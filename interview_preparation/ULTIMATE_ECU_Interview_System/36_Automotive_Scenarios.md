# Automotive Scenario-Based Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Scenario-based questions are the **most common differentiator** in senior automotive interviews. Instead of textbook questions, interviewers at Bosch, Continental, Harman, Aptiv, and KPIT present real-world ECU failures and ask you to diagnose, fix, and prevent them. This file covers classic automotive scenarios with full root-cause analysis and production-grade solutions.

**Key scenario categories:**
- CAN bus failures (bus-off, overload, signal corruption)
- ECU startup failures (watchdog reset, NvM corruption, power brownout)
- Communication timeouts (CAN, LIN, Ethernet, MQTT)
- Software-hardware interaction issues (DMA, cache, interrupt handling)
- Production field failures (fleet-scale, hard to reproduce)
- Safety scenarios (ASIL violations, MPU faults, watchdog misses)

---

## CAN BUS SCENARIOS

---

### Scenario 1: ECU goes bus-off every morning at 7AM in customer fleet.

**What they're testing:** Understanding of CAN error recovery, ECU network dependency, bus-off state machine.

**Your expert answer:**

"This is a fascinating time-based failure. The 7AM pattern is the key clue — it suggests:

1. Temperature-related (cold morning, soldering issues, connector oxidation)
2. Multiple ECUs powering up simultaneously (ignition ON at 7AM commute)
3. Transceiver startup sequence creating dominant bit glitch

**Root cause analysis:**
```
CAN Bus-Off Trigger Chain:

When ignition is turned ON:
  T=0ms:   BCM (Body Control Module) powers on, CAN transceiver enabled
  T=0ms:   Instrument cluster powers on simultaneously
  T=2ms:   Both ECUs start transmitting their power-on status messages
  
  CAN Arbitration Issue:
  BCM sends 0x100 (priority bits: 0 0001 0000 0000)
  Cluster sends 0x100 simultaneously (SAME CAN ID! — configuration error)
  
  Two ECUs transmitting same CAN ID simultaneously:
  → Neither wins arbitration (same ID, same priority)
  → Both transmit simultaneously → dominant bit collision
  → Both see their own bit error
  → TEC (Transmit Error Counter) increments by 8 per error
  → After 16 errors: TEC > 127 → Error Passive state  
  → After 24 errors: TEC > 255 → Bus-Off state
  → Bus-Off recovery: 128 × 11 recessive bits before re-joining
  
Why only at 7AM?
  Hot soak (parked 8+ hours overnight) → ECU resets
  Both BCM and cluster have warm-restart recovery path that avoids collision
  Only cold-boot (full power-off overnight) triggers the race condition
```

**Diagnosis steps:**
```bash
# 1. Capture CAN traffic during ignition ON (Vector CANalyzer or python-can)
# candump -t a -L logfile.asc can0 &

# 2. Filter for errors
candump can0 | grep -i "error\|BUSOFF"

# 3. Check TEC/REC counters
ip -details link show can0
# Output: can state BUS-OFF txerr XX rxerr XX

# 4. Analyse: which CAN ID appears from two different nodes simultaneously?
# Look for same CAN ID but different DLC or data — same ID from two sources
```

**Fix:**
```
1. Assign unique CAN IDs to each ECU — audit entire network DBC file
2. Add startup delay jitter (BCM: 0ms, Cluster: 50ms randomised)
3. Implement bus-off recovery with exponential backoff (not immediate retry):
```

```c
/* Bus-off recovery with exponential backoff */
static uint32_t s_busoff_count    = 0U;
static uint32_t s_recovery_delay_ms = 100U;

void can_busoff_handler(void) {
    s_busoff_count++;
    
    /* Set DTC */
    DEM_SetDTC(DTC_CAN_BUS_OFF);
    
    /* Exponential backoff: 100ms, 200ms, 400ms ... max 30s */
    uint32_t delay = s_recovery_delay_ms;
    s_recovery_delay_ms = MIN(s_recovery_delay_ms * 2U, 30000U);
    
    /* Wait, then attempt re-init */
    osDelay(delay);
    CAN_Init();  /* Re-initialise CAN controller */
    
    if (s_busoff_count > 10U) {
        /* Persistent bus-off: enter limp-home mode */
        System_EnterLimpHome(REASON_CAN_BUS_OFF);
    }
}

void can_busoff_reset_counter(void) {
    /* Call after 30 minutes of clean operation */
    s_busoff_count = 0U;
    s_recovery_delay_ms = 100U;
}
```

**Production Insight:** This exact scenario was found during Hyundai Kona Electric ECU integration testing. The BCM and instrument cluster both used 0x100 as their startup heartbeat ID. The bug only appeared in cold-start conditions. Fix: BCM assigned 0x100, cluster assigned 0x101, with a 30ms startup delay for the cluster. Fleet vehicles in production retrofit via OTA configuration update."

---

### Scenario 2: CAN signal shows wrong value intermittently — only under high temperature (>80°C under-hood).

**Your expert answer:**

"Temperature-dependent signal corruption is almost always a hardware issue manifesting as software symptoms.

**Hypothesis tree:**
```
Temperature > 80°C →
  Option A: Transceiver timing margins violated (SN65HVD230)
            → Bit timing sample point shifts
            → Intermittent bit errors, CRC failures
  
  Option B: Oscillator frequency drift (crystal at 16 MHz drifts ±50ppm)
            → CAN bit timing calculated for 16 MHz, but actual 15.999 MHz
            → At 1 Mbps, 1 bit = 1μs. 50ppm drift = 50ns error
            → If accumulated at field edges: sample point missed
  
  Option C: PCB trace impedance change (FR4 loses stiffness, solder cold joint)
            → Signal reflections → bit corruption on long bus runs
  
  Option D: Connector oxidation at elevated temp cycling
            → Intermittent resistance increase on CAN_H or CAN_L line
```

**Software-level evidence collection:**
```c
/* Log CAN error counters before corruption occurs */
void periodic_can_health_log(void) {  /* Call every 1 second */
    uint32_t tec = CAN1->ESR & CAN_ESR_TEC;  /* Transmit Error Counter */
    uint32_t rec = (CAN1->ESR & CAN_ESR_REC) >> 24;
    uint8_t  err_flag = CAN1->ESR & 0x07U;  /* LEC: Last Error Code */
    
    /* LEC values: 0=none, 1=stuff, 2=form, 3=ack, 4=bit_dom, 5=bit_rec, 6=crc */
    if (tec > 10U || rec > 10U) {
        log_warn("CAN health: TEC=%u, REC=%u, LEC=%u, temp=%d°C",
                 tec, rec, err_flag, temperature_sensor_read());
    }
}
```

**Diagnosis with Vector CANoe + temperature logging:**
```
CANoe + K-factor (temperature thermocouple) capture:
  Overlay: CAN error frame count vs temperature
  Observation: Error rate increases steeply at 82°C
  Conclusion: Component at thermal limit
  
Oscilloscope (differential probe on CAN_H/CAN_L at >80°C):
  Measure eye diagram at hot condition
  If eye is closing → signal integrity problem (Option A, C, or D)
  
Crystal stability test (spectrum analyser):
  Measure clock output at 25°C and 85°C
  If frequency drift > ±25ppm at rated bitrate → Option B
```

**Resolution:** Component-level fix (hardware), but software mitigation:
```c
/* Reduce CAN bitrate in thermal protection mode */
void thermal_protection_handler(int temp_c) {
    if (temp_c > 85 && g_can_bitrate == 1000000U) {
        /* Drop to 500kbps — twice the timing margin */
        CAN_ChangeBitrate(500000U);
        DEM_SetDTC(DTC_THERMAL_DERATING);
        log_warn("Thermal: CAN bitrate derated to 500kbps at %d°C", temp_c);
    }
}
```

---

## ECU STARTUP SCENARIOS

---

### Scenario 3: ECU resets randomly every few days in fleet. DTC shows watchdog reset.

**Your expert answer:**

"Watchdog resets after random intervals (not systematic) typically indicate one of:
1. Task starvation (high-priority task running too long)
2. Interrupt storm (ISR running too often, task scheduler never runs)
3. Genuine hang (deadlock)

**Diagnosis approach:**
```c
/* Step 1: Identify which task failed to kick watchdog */
/* Add timestamp to each WDG token refresh */
typedef struct {
    uint32_t last_kick_ms;
    uint32_t kick_timeout_ms;
    const char *task_name;
    bool alive;
} WdgToken_t;

/* In watchdog supervisor — log the culprit before reset */
void check_watchdog_tokens(void) {
    uint32_t now = osKernelGetTickCount();
    
    for (int i = 0; i < WDG_TASK_COUNT; i++) {
        uint32_t elapsed = now - s_tokens[i].last_kick_ms;
        if (elapsed > s_tokens[i].kick_timeout_ms) {
            /* This task didn't kick in time — log BEFORE watchdog fires */
            log_fatal("WDG: Task '%s' missed kick! Elapsed=%ums, Timeout=%ums",
                      s_tokens[i].task_name, elapsed, s_tokens[i].kick_timeout_ms);
            log_fatal("WDG: Stack watermark: %u words",
                      uxTaskGetStackHighWaterMark(s_tokens[i].handle));
            /* Save to NvM so we can read after reset */
            NvM_WriteBlock(NVM_BLOCK_WDG_FAULT_LOG, &s_fault_log);
        }
    }
}
```

**Reading the fault log after reset:**
```c
/* On ECU startup, check reset reason and fault log */
void startup_check_reset_reason(void) {
    uint32_t rsr = RCC->RSR;  /* STM32 Reset Status Register */
    
    if (rsr & RCC_RSR_IWDG1RSTF) {
        /* Independent Watchdog reset */
        WdgFaultLog_t log;
        NvM_ReadBlock(NVM_BLOCK_WDG_FAULT_LOG, &log);
        
        log_warn("BOOT: WDG reset detected! Last fault: task='%s' at %ums ago",
                 log.task_name, log.elapsed_ms);
        DEM_SetDTC(DTC_WATCHDOG_RESET);
    }
    
    RCC->RSR |= RCC_RSR_RMVF;  /* Clear reset flags */
}
```

**Common root causes found in production:**
```
1. CAN receive callback doing slow NvM write in ISR context:
   ISR → Com_RxIndication → App_Callback → NvM_WriteBlock (SLOW!)
   NvM write takes 5ms → ISR blocked for 5ms → 10ms task misses 5 WDG kicks
   
   Fix: never call blocking operations in ISR or callbacks
   Use flag/queue: set flag in callback, do NvM write in task context

2. Deadlock: CAN task holds mutex, diagnostic task tries to acquire same mutex
   CAN task then calls diagnostic function that tries same mutex → deadlock
   
   Fix: audit all mutex acquisition paths, use std::scoped_lock for multiple mutexes
   
3. Interrupt storm: broken sensor generating 50,000 interrupts/second
   CPU 100% in ISR → tasks never run → WDG never kicked
   
   Fix: GPIO debounce filter, ISR rate limiter (disable IRQ if too frequent)
```

---

## PRODUCTION INSIGHT SCENARIOS

---

### Scenario 4: OTA update fails on 0.1% of fleet (500 vehicles out of 500,000). All other vehicles succeed.

**Your expert answer:**

"0.1% failure rate suggests a specific hardware configuration or boundary condition. I'd approach this as:

**Step 1 — Fleet correlation analysis:**
```python
# Correlate failing VINs with hardware attributes
failing_vins = ['VIN001', 'VIN034', ...]

for vin in failing_vins:
    ecu_data = get_ecu_data(vin)
    print(f"{vin}: HW={ecu_data['hw_version']}, "
          f"flash_size={ecu_data['flash_kb']}KB, "
          f"carrier={ecu_data['sim_carrier']}, "
          f"signal_dbm={ecu_data['last_rssi']}")

# Output pattern:
# All failing: HW=v1.1, flash_size=1024KB (vs 2048KB in passing units)
# All failing: carrier=MVNOx (specific MVNO with different MTU)
```

**Step 2 — Identify root cause (flash size):**
```
OTA package: 900KB
flash_size=2048KB: ota_download → /tmp/ota.bin (512KB available) → SUCCESS  
flash_size=1024KB: ota_download → /tmp/ota.bin (128KB available!) → PARTIAL WRITE

First 128KB downloaded → SHA256 check → MISMATCH → OTA marked failed
No error logged clearly (file write succeeded but was truncated silently!)
```

**Step 3 — The carrier MTU issue (secondary):**
```
MVNOx uses IP MTU 576 (some MVNOs use smaller MTU)
HTTPS client uses TCP MSS based on MTU
576 byte MTU → 536 byte TCP payload
OTA download buffer = 4096 bytes → fragmented into 8 TCP segments
If any segment has >200ms RTT → TCP timeout → download abort

Fix: retry with exponential backoff, resume via HTTP Range header
```

**Fix:**
```c
/* Check available storage BEFORE starting download */
OTAResult ota_pre_flight_check(size_t expected_pkg_size) {
    struct statvfs fs;
    if (statvfs("/tmp", &fs) != 0) return OTA_ERR_STORAGE_CHECK;
    
    size_t avail_bytes = fs.f_bsize * fs.f_bavail;
    
    if (avail_bytes < expected_pkg_size * 2U) {  /* Need 2× for safety margin */
        log_error("OTA: Insufficient storage. Available=%zu, Required=%zu",
                  avail_bytes, expected_pkg_size * 2U);
        DEM_SetDTC(DTC_OTA_STORAGE_INSUFFICIENT);
        return OTA_ERR_INSUFFICIENT_STORAGE;
    }
    return OTA_OK;
}
```

**Production Insight (Harman, BMW OTA project):** The 0.1% failure was exactly this pattern — low-storage trim-level vehicles had 1GB eMMC vs 8GB on high-trim. The fix was a pre-flight storage check, OTA server reporting available storage requirement in manifest, and server-side vehicle segmentation to only offer OTA when storage check passes."

---

## CHEAT SHEET — Automotive Scenarios

```
CAN bus-off diagnosis:
  Check: ip -details link show canX (txerr/rxerr counters)
  Tools: candump -l (log) | Vector CANalyzer error frame analysis
  CAN ESR register: TEC, REC, LEC (Last Error Code 0-6)
  Root causes: duplicate CAN IDs, EMI, oscillator drift, bus termination

Watchdog reset diagnosis:
  Save fault log to NvM before reset (non-volatile!)
  Read reset reason register on boot (RCC->RSR on STM32)
  Track each task's last kick time + task name
  Root causes: deadlock, interrupt storm, ISR blocking, task starvation

Field intermittent failure strategy:
  5 questions: When? Which units? What conditions? What changed? What's different?
  Correlate with: temperature, mileage, firmware version, hardware revision
  Add telemetry first — log before debugging
  
OTA failure analysis:
  Pre-flight: check storage space, signal strength, battery voltage
  During download: SHA256 streaming verify
  Post-download: full SHA256 + certificate signature check
  Resume: HTTP Range header for poor connectivity
  Fleet segmentation: validate on 1% before 100% rollout

Key numbers to remember:
  CAN bus-off: TEC > 255 (or 256 in some controllers)
  CAN error passive: TEC > 127 or REC > 127
  Bus-off recovery: 128 × 11 recessive bits
  ISO 14229 P2 timeout: 50ms default
  ISO 14229 P2* timeout: 5000ms extended
  UDS SecurityAccess seed-key delay: 10s after 3 failed attempts
```
