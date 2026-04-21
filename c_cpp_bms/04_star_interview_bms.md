# STAR Interview Scenarios — BMS C/C++ Engineering

> **Domain:** Battery Management System (BMS) — EV / HEV
> **Format:** Situation → Task → Action → Result
> **Topics:** SoC accuracy, protection response time, memory safety, UDS, ISO 26262

---

## STAR Scenario 1 — SoC Drift at Low Temperature

### Situation
During winter validation testing of an EV BMS (60 Ah NMC pack), our Coulomb-counting SoC showed **±8% error** after 4-hour drives at −10 °C. Customers would see unexpected low-battery warnings, causing range anxiety.

### Task
Reduce SoC error to < ±3% across −20 °C to +45 °C, without hardware changes, within a 6-week sprint.

### Action

**Root cause analysis:**
- Coulombic efficiency (η) was hardcoded at 0.99 regardless of temperature
- At −10 °C, η drops to ~0.85 due to lithium plating risk on graphite anode
- Current sensor offset drifted ±0.3 A at cold temperatures

**Fix 1 — Temperature-dependent η:**
```cpp
float get_coulombic_efficiency(float temp_c, float /*current_a*/)
{
    /* Empirical polynomial fit from characterisation data */
    /* At 25°C: η=0.990, at 0°C: η=0.940, at -10°C: η=0.880 */
    if (temp_c >= 25.0f) return 0.990f;
    if (temp_c >= 10.0f) return 0.975f - 0.001f * (25.0f - temp_c);
    if (temp_c >=  0.0f) return 0.960f - 0.002f * (10.0f - temp_c);
    return 0.880f + 0.004f * temp_c;   /* Linear below 0°C */
}
```

**Fix 2 — OCV correction at extended rest:**
```cpp
void soc_apply_ocv_correction(float current_a, float cell_ocv_v, float dt_since_last_s)
{
    /* Only correct when |I| < 0.5A for > 120 seconds (relaxed state) */
    if (fabsf(current_a) < 0.5f && dt_since_last_s > 120.0f) {
        float soc_from_ocv = soc_from_ocv_table(cell_ocv_v);
        float error = soc_from_ocv - g_soc_fraction;

        /* Gentle correction — limit to 1% per correction event */
        float correction = clampf(error, -0.01f, 0.01f);
        g_soc_fraction += correction;
        log_soc_correction(correction);
    }
}
```

**Fix 3 — Current sensor offset calibration on startup:**
```cpp
void current_sensor_calibrate_offset(void)
{
    /* At startup with contactors open, true current = 0A */
    /* Sample 100ms, compute mean offset */
    int32_t sum_ma = 0L;
    for (uint8_t i = 0U; i < 100U; ++i) {
        sum_ma += read_current_sensor_raw_ma();
        vTaskDelay(pdMS_TO_TICKS(1U));
    }
    g_current_offset_ma = (int32_t)(sum_ma / 100L);
}
```

### Result
- SoC error reduced from **±8%** to **±2.1%** across temperature range
- Zero customer complaints in next winter test cycle (10 vehicles, 3000 km)
- OCV correction prevented Coulomb counting drift accumulation up to 95% accuracy over 8-hour trips
- Temperature-dependent η accepted into BMS calibration dataset for production

---

## STAR Scenario 2 — OV2 Response Time Failure (ISO 26262)

### Situation
During HIL testing, ASIL B requirement stated: *OV2 (cell > 4250 mV) must open contactors within 2ms*. Our measurement showed reaction time of **8ms** — 4× too slow. Certification was at risk.

### Task
Identify and fix the bottleneck so OV2 → contactor open latency was < 2ms end-to-end.

### Action

**Instrumented the OV2 path with GPIO toggling:**
```c
/* Measurement points: */
/* T0: DMA_ISR fires (AFE conversion complete) */
/* T1: Cell Monitor semaphore taken */
/* T2: OV2 condition detected */
/* T3: Event group set */
/* T4: Contactor task unblocks */
/* T5: GPIO contactor open command */

void DMA2_Stream3_IRQHandler(void) {
    GPIO_PROBE_SET(PROBE_T0);       /* T0 */
    xSemaphoreGiveFromISR(sem_afe_ready, &hp_woken);
    portYIELD_FROM_ISR(hp_woken);
}
```

**Latency breakdown discovered:**

| Segment | Before Fix | Root Cause |
|---|---|---|
| DMA ISR → Cell Monitor unblock | 0.2ms | Context switch OK |
| Voltage decode (PEC + all 96 cells) | 4.3ms | Scanning all cells before checking worst |
| Event → Contactor task unblock | 0.5ms | Normal OS latency |
| Contactor task to GPIO | 3.0ms | Task was at P3, contactor at P3 (same) |
| **Total** | **8.0ms** | — |

**Fix 1 — Fast OV2 hardware path (parallel to SW):**
Already had HW comparator on AFE GPIO — enabled it to directly drive relay control logic.

**Fix 2 — Priority inversion fix:**
```c
/* Cell monitor → P5, Contactor task → P6 (higher priority) */
xTaskCreate(task_cell_monitor,   "CellMon",   512U, NULL, 5, NULL);
xTaskCreate(task_contactor_ctrl, "ContCtrl",  512U, NULL, 6, NULL);
```

**Fix 3 — Scan highest-risk cells first (skip full decode):**
```c
void fast_check_ov2(const uint8_t* spi_raw)
{
    /* Check only the 8 cells from highest-temperature module first */
    uint8_t hot_module = get_hottest_module_idx();
    for (uint8_t c = 0U; c < 8U; ++c) {
        uint16_t v_mv = decode_single_cell(spi_raw, hot_module, c);
        if (v_mv >= 4250U) {
            xEventGroupSetBitsFromISR(eg_faults, FAULT_BIT_OV2, &hp_woken);
            return;   /* Abort scan — already faulted */
        }
    }
}
```

### Result
- OV2 → contactor open latency reduced from **8ms to 1.4ms**
- Well within ASIL B 2ms requirement
- Hardware comparator path added as independent channel (ASIL B dual-channel)
- ISO 26262 Part 4 FMEA updated; certification review passed

---

## STAR Scenario 3 — Memory Corruption in NVM SoC Write

### Situation
After a CAN bus disturbance during driving, the BMS restarted and initialised SoC at 100% instead of the actual 42% saved to NVM. Investigation revealed the NVM block was corrupted — the CRC was being overwritten with stale data from a freed object.

### Task
Identify the use-after-free bug in the NVM write path and harden the NVM write against corruption.

### Action

**Root cause — object pool pattern misused:**
```c
/* BUGGY CODE — simplified */
BmsNvmData_t* get_nvm_buffer(void) {
    return &s_nvm_pool[s_pool_idx++ % NVM_POOL_SIZE];
}

void task_nvm_writer(void* p) {
    for (;;) {
        BmsNvmData_t* buf = get_nvm_buffer();
        fill_from_state(buf);
        buf->crc8 = compute_crc8((uint8_t*)buf, sizeof(*buf) - 1);  /* CRC computed here */

        /* ... later, async path ... */
        NvM_WriteBlock(NVM_BMS, buf);   /* BUG: buffer recycled before DMA write completes */
    }
}
```

**Fix — static double-buffer with write-completion flag:**
```c
static BmsNvmData_t s_nvm_buf[2U];
static volatile uint8_t s_write_buf_idx = 0U;
static volatile bool s_nvm_write_pending = false;

void task_nvm_writer(void* p)
{
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(1000U));

        /* Skip if previous write still pending */
        if (s_nvm_write_pending) continue;

        uint8_t idx = s_write_buf_idx;
        BmsNvmData_t* buf = &s_nvm_buf[idx];

        if (xSemaphoreTake(mutex_bms_state, pdMS_TO_TICKS(10U)) == pdTRUE) {
            buf->soc_at_shutdown = (float)g_bms_state.soc_pct / 100.0f;
            buf->soh_pct         = g_bms_state.soh_pct;
            xSemaphoreGive(mutex_bms_state);
        }

        buf->crc8 = compute_crc8((uint8_t*)buf, sizeof(*buf) - 1U);
        s_nvm_write_pending = true;
        NvM_WriteBlock(NVM_BMS, buf);   /* Async — completion handled by callback */
    }
}

/* NvM write-complete callback */
void NvM_JobFinishedCallback_BMS(void)
{
    s_write_buf_idx    = (s_write_buf_idx + 1U) % 2U;   /* Swap buffer */
    s_nvm_write_pending = false;
}
```

**Added NVM validation on read:**
```c
bool nvm_load_bms(BmsNvmData_t* out)
{
    if (NvM_ReadBlock(NVM_BMS, out) != E_OK) return false;
    uint8_t expected_crc = compute_crc8((uint8_t*)out, sizeof(*out) - 1U);
    if (out->crc8 != expected_crc) {
        report_dtc(DTC_NVM_CRC_FAIL, NULL, 0U);
        return false;
    }
    if (out->soc_at_shutdown < 0.0f || out->soc_at_shutdown > 1.0f) return false;
    return true;
}
```

### Result
- Root cause confirmed as use-after-free via static analysis (Polyspace Code Prover)
- Double-buffer + completion callback eliminated race condition
- NVM CRC validation prevented incorrect SoC restore in all 6 subsequent power-cycle tests
- Added to safety checklist: all async buffer handles must use ownership tracking

---

## STAR Scenario 4 — CAN Timeout Cascade Causing UDS Session Drop

### Situation
During UDS end-of-line (EOL) programming, the BMS would intermittently drop from extended diagnostic session (0x03) back to default session mid-operation. This caused the EOL tester to fail and required a manual reset — adding ~3 minutes per vehicle on the production line.

### Task
Identify why the UDS session was timing out and fix it without modifying the EOL tester's CAN sequence.

### Action

**Analysis — Session timeout mechanism:**
```c
/* UDS Session timer (ISO 14229-1: S3 timer = 5000ms) */
static uint32_t g_uds_session_last_activity_ms = 0U;
#define UDS_S3_TIMEOUT_MS   5000U

void uds_check_session_timeout(void)
{
    uint32_t elapsed = get_system_tick_ms() - g_uds_session_last_activity_ms;
    if (elapsed > UDS_S3_TIMEOUT_MS && g_uds_session != UDS_SESSION_DEFAULT) {
        uds_transition_to_default();
    }
}

/* Called on every received UDS frame */
void uds_refresh_session_timer(void) {
    g_uds_session_last_activity_ms = get_system_tick_ms();
}
```

**Root cause — CAN RX queue overrun causing dropped TesterPresent frames:**
```
EOL tester sends:  0x3E 0x80  (TesterPresent, suppressPositiveResponse)
Rate: every 2000ms (within S3=5000ms, correct)

BUT: BMS CAN RX task priority = P1 (same as CAN TX)
     NVM task at P2 holds mutex_bms_state for up to 800ms during flash write
     → CAN RX task starved for 800ms
     → RX FIFO overrun
     → 4 consecutive TesterPresent frames dropped
     → 4 × 2000ms = 8000ms > S3=5000ms → session dropped
```

**Fix — Raise CAN RX priority and preempt NVM during CAN traffic:**
```c
/* CAN RX task at P4 — cannot be blocked by NVM (P2) */
xTaskCreate(task_can_rx, "CAN_RX", 512U, NULL, 4, NULL);

/* NVM: check if UDS session active before long operations */
void task_nvm_writer(void* p) {
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(1000U));

        /* Delay NVM write if UDS session is active */
        uint8_t retries = 10U;
        while (uds_is_non_default_session() && retries-- > 0U) {
            vTaskDelay(pdMS_TO_TICKS(100U));
        }
        nvm_do_write();
    }
}
```

**Added TesterPresent frame counter for monitoring:**
```c
uint32_t g_tester_present_received = 0UL;
uint32_t g_tester_present_suppressed = 0UL;
```

### Result
- EOL session drop eliminated on production line (0 failures in next 500 vehicles)
- CAN RX priority restructure prevented queue overrun even during NVM writes
- CAPL test was added in CANoe to replay the scenario: confirmed fix held under 50 repeated EOL cycles
- NVM write extended by 300ms in worst case — acceptable for production volume

---

## STAR Scenario 5 — MISRA C Compliance Drive Before Audit

### Situation
Three months before an ISO 26262 Part 6 audit, static analysis (LDRA) reported **1,847 MISRA C:2012 violations** in the BMS firmware. Many were in safety-relevant paths (OV/UV protection, contactor FSM). Compliance was a hard gate for production sign-off.

### Task
As lead embedded software engineer, eliminate all MISRA Required + Mandatory violations in safety-relevant modules, and reduce Advisory violations by > 70%, within 10 weeks.

### Action

**Triage — Categorise violations by severity and safety relevance:**
```
Category          Count    Plan
Mandatory          12      Fix 100% — day 1
Required (ASIL B) 218      Fix 100% — 8 weeks
Required (QM)     401      Fix 100% — 10 weeks
Advisory           1216    Fix > 70%
Total              1847
```

**Common fixes applied:**

```c
/* MISRA Rule 10.4: Both operands of an operator must have same essential type */
/* BEFORE (violation): */
uint8_t mask = (1 << cell_idx);                /* 'cell_idx' is int, shift is int, then truncated to uint8 */

/* AFTER: */
uint8_t mask = (uint8_t)(1U << (uint8_t)cell_idx);   /* Explicit cast and unsigned operator */

/* MISRA Rule 15.5: A function shall have a single point of exit */
/* BEFORE (multiple returns): */
bool check_ov(uint16_t v) {
    if (v == 0U) return false;          /* Early return */
    if (v > 5000U) return false;        /* Early return */
    return v >= BMS_OV2_THRESHOLD_MV;
}

/* AFTER: */
bool check_ov(uint16_t v) {
    bool result = false;
    if (v > 0U && v <= 5000U) {
        result = (v >= BMS_OV2_THRESHOLD_MV);
    }
    return result;
}

/* MISRA Rule 14.4: The controlling expression of an if statement shall be essentially Boolean */
/* BEFORE: */
if (error_count) { ... }     /* integer used as Boolean */

/* AFTER: */
if (error_count != 0U) { ... }

/* MISRA Rule 17.7: Result of a function with non-void return type must be used */
/* BEFORE: */
xSemaphoreTake(mutex, pdMS_TO_TICKS(10U));   /* Return ignored */

/* AFTER: */
if (xSemaphoreTake(mutex, pdMS_TO_TICKS(10U)) != pdTRUE) {
    /* Handle failure */
    log_mutex_timeout();
}
```

**Process improvements:**
- Added MISRA checker to CI pipeline (LDRA + Jenkins) — violations blocked PR merge
- Created BMS MISRA deviation record for justified exceptions (3 deviations documented)
- 2-hour MISRA workshop for the team → common patterns understood by all

### Result
- Mandatory: **12/12 fixed** (100%)
- Required (ASIL B): **218/218 fixed** (100%)
- Required (QM): **401/401 fixed** (100%)
- Advisory: reduced by **78%** (949 of 1216 fixed)
- ISO 26262 Part 6 audit **passed with zero critical findings**
- CI pipeline now maintains < 50 advisory violations per release

---

## Quick-Reference Q&A Table

| Question | Answer |
|---|---|
| What's Coulombic efficiency and why does it vary? | η = Ah_out / Ah_in. < 1.0 because some charge is lost to side reactions (SEI formation, Li plating at low T). NMC: 0.98 at 25°C, 0.87 at −10°C |
| How does an EKF differ from a Luenberger observer for SoC? | EKF handles nonlinear OCV-SoC curve via linearisation (Jacobian). Luenberger observer assumes linear system. EKF adapts covariance online; Luenberger gain is fixed. |
| What is the Thevenin equivalent model? | R0 (ohmic) in series with R1||C1 (RC pair for polarisation). Two-state EKF: [SoC, V_RC]. More states → more accuracy, more CPU cost. |
| Why use double-buffering for NVM writes? | Async DMA writes continue after the function returns. Double buffer prevents use-after-free where the CPU fills buffer n+1 before DMA of buffer n completes. |
| Define ASIL B for OV2 protection | Probability of failure to detect OV2 within 2ms < 10⁻⁷ /h (ASIL B requirement). Achieved via: SW channel + HW comparator + PEC checksum + watchdog. |
| What is IEC 62619? | Safety standard for secondary lithium cells in stationary/vehicle applications. Specifies OV/UV/OT/OC/short-circuit requirements and test procedures for BMS. |
| How do you verify contactor weld? | After open command: measure DC link voltage decay. If Vlink > 90% of Vbat after 200ms → weld suspected → DTC → prevent HV reconnect. |
| What's S3 timer in UDS? | Session timeout (ISO 14229-1). Default: 5000ms. If no TesterPresent received within S3, ECU drops to default session. |
| Why PEC-15 in AFE communication? | PEC (Packet Error Code) is a 15-bit CRC on SPI data from LTC6811 AFE. Detects single and most multi-bit errors in cell voltage readings before they are used in protection logic. |
| How do you measure WCET on an embedded target? | Use ARM DWT cycle counter (DWT->CYCCNT). Run worst-case input, record max cycles. Convert: µs = cycles / clock_MHz. Must measure on target hardware, not simulator. |
| What is cell balancing? | Passive: discharge highest cells through resistors until equal to minimum cell. Active: transfer charge from high to low cells. Passive simpler but wastes energy as heat. |
| What is IMD? | Insulation Monitoring Device. Measures resistance between HV bus and chassis. ISO 6469-3: min 500 Ω/V. At 400V pack: > 200 kΩ required. Detects HV leakage to chassis. |
| What's Chi-squared gate for EKF? | Innovation gate: if (y_err² / S) > χ²_threshold, reject measurement as outlier. Prevents corrupted voltage sensor from corrupting SoC estimate. |
| Difference between SoC and SoH? | SoC = current energy vs current capacity (0–100%). SoH = current capacity vs original capacity (100% = new, 80% = EOL). SoC changes cycle-to-cycle, SoH degrades over months. |
| How do you handle a negative SoC result? | Clamp to 0%, set DTC (SoC_UNDERFLOW), apply OCV correction at next rest opportunity. Never allow SoC to go below 0 in production — it breaks Coulomb counting reset. |

---

*File: 04_star_interview_bms.md | c_cpp_bms learning series*
