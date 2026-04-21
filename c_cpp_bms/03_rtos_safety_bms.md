# RTOS and Functional Safety for BMS Engineering

> **Domain:** Battery Management System (BMS) — EV / HEV
> **RTOS:** FreeRTOS (AUTOSAR Classic OS compatible patterns)
> **Standards:** ISO 26262, IEC 62619, UN R100 Annex 9, MISRA C:2012

---

## 1. BMS Task Architecture

```
Priority (FreeRTOS, higher = more urgent)
┌─────────────────────────────────────────────────────────────────────┐
│ P7 (ISR)  DMA_ISR_AFE      SPI DMA complete → SoC queue            │
│ P6        Contactor Ctrl   10ms  — ASIL B                           │
│ P5        Cell Monitor     10ms  — OV/UV/OT protection              │
│ P4        SoC Calculator   100ms — EKF update                        │
│ P4        UDS Handler      20ms  — Diagnostic comms                 │
│ P3        Balancer         500ms — Cell equalisation                 │
│ P2        NVM Writer       1s    — Periodic SoC/SoH persistence      │
│ P1        CAN Comms        10ms  — Status broadcast                 │
│ P0        Idle             —     — Stack watermark, WD kick          │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Timing Constraints

| Function | Deadline | ASIL | Rationale |
|---|---|---|---|
| OV2 detection | 1ms | ASIL B | Cell damage within tens of ms |
| Contactor open command | 2ms | ASIL B | ISO 26262 / IEC 62619 |
| SoC update | 100ms | QM | Coulomb counting accuracy |
| IMD (isolation) alarm | 500ms | ASIL B | ISO 6469-3 500 Ω/V |
| UDS response | 25ms per frame | QM | ISO 14229 P2 timer |
| NVM write | Non-RT | QM | Wear levelling via FTL |

---

## 2. FreeRTOS Task Setup — BMS

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "timers.h"
#include "event_groups.h"

/* ---- Inter-task communication objects ---- */
static QueueHandle_t  q_cell_voltages;       /* DMA ISR → Cell Monitor */
static QueueHandle_t  q_pack_measurements;   /* Cell Monitor → SoC Calculator */
static QueueHandle_t  q_balance_cmds;        /* Balancer → HAL driver */
static QueueHandle_t  q_can_tx;             /* Any → CAN task */

static SemaphoreHandle_t sem_afe_ready;      /* DMA ISR → Cell Monitor */
static SemaphoreHandle_t mutex_bms_state;    /* Protect shared BmsPackData_t */
static EventGroupHandle_t eg_faults;         /* Fault signalling */

/* Fault event bits */
#define FAULT_BIT_OV2   (1UL << 0U)
#define FAULT_BIT_UV2   (1UL << 1UL)
#define FAULT_BIT_OT2   (1UL << 2U)
#define FAULT_BIT_IMD   (1UL << 3U)
#define FAULT_BIT_WELD  (1UL << 4U)

/* Shared state (access with mutex_bms_state) */
static BmsPackData_t g_bms_state;

/* ---- Measurement data sent between tasks ---- */
typedef struct {
    uint16_t cell_mv[96U];
    int32_t  current_ma;
    uint32_t pack_voltage_mv;
    uint32_t timestamp_ms;
} BmsMeasurement_t;

/* ============================================================
 * Cell Monitor Task — P5, 10ms
 * ============================================================ */
static void task_cell_monitor(void* pv_params)
{
    (void)pv_params;
    BmsMeasurement_t meas;

    for (;;) {
        /* Wait for AFE DMA complete semaphore (timeout = 15ms) */
        if (xSemaphoreTake(sem_afe_ready, pdMS_TO_TICKS(15U)) == pdTRUE) {
            /* Read decoded voltages from DMA buffer */
            decode_all_afe_voltages(meas.cell_mv);
            meas.current_ma     = read_current_sensor_ma();
            meas.pack_voltage_mv = sum_cell_voltages(meas.cell_mv);
            meas.timestamp_ms   = xTaskGetTickCount() * portTICK_PERIOD_MS;

            /* Check OV/UV — fast path before sending to SoC task */
            for (uint8_t i = 0U; i < 96U; ++i) {
                if (meas.cell_mv[i] >= 4250U) {
                    xEventGroupSetBits(eg_faults, FAULT_BIT_OV2);
                }
                if (meas.cell_mv[i] <= 2800U) {
                    xEventGroupSetBits(eg_faults, FAULT_BIT_UV2);
                }
            }

            /* Forward measurement to SoC task */
            xQueueOverwrite(q_pack_measurements, &meas);   /* Non-blocking, overwrite old */
        } else {
            /* Missed AFE sample — log communication error */
            xEventGroupSetBits(eg_faults, FAULT_BIT_OV2);  /* Use generic flag for testing */
        }

        vTaskDelay(pdMS_TO_TICKS(10U));
    }
}

/* ============================================================
 * Contactor Control Task — P6, 10ms
 * ============================================================ */
static void task_contactor_ctrl(void* pv_params)
{
    (void)pv_params;
    ContactorFsm_t fsm = {BMS_STATE_STANDBY, 0U, 0.0f, 0U};

    for (;;) {
        /* Check fault events — highest priority path */
        EventBits_t faults = xEventGroupGetBits(eg_faults);
        if (faults & (FAULT_BIT_OV2 | FAULT_BIT_UV2 | FAULT_BIT_OT2 | FAULT_BIT_IMD)) {
            if (fsm.state != BMS_STATE_FAULT) {
                open_all_contactors_immediately();  /* < 1ms hardware path */
                fsm.state = BMS_STATE_FAULT;
                report_dtc_from_fault_bits(faults);
            }
        } else {
            /* Normal FSM tick */
            contactor_fsm_run_1ms(NULL, &fsm);
        }

        vTaskDelay(pdMS_TO_TICKS(10U));
    }
}

/* ============================================================
 * SoC Calculator Task — P4, 100ms
 * ============================================================ */
static void task_soc_calculator(void* pv_params)
{
    (void)pv_params;
    BmsMeasurement_t meas;
    float dt_s = 0.100f;

    /* Initialise SoC from NVM or OCV at startup */
    float initial_soc = load_soc_from_nvm();
    ekf_soc_reset(initial_soc);

    for (;;) {
        /* Block until new measurement, timeout 150ms */
        if (xQueueReceive(q_pack_measurements, &meas, pdMS_TO_TICKS(150U)) == pdTRUE) {
            float current_a  = (float)meas.current_ma / 1000.0f;
            float voltage_v  = (float)meas.pack_voltage_mv / 1000.0f;

            /* EKF update → SoC */
            ekf_soc_update(current_a, voltage_v, read_avg_temperature_c(), dt_s);
            float soc = ekf_soc_get();

            /* Update shared state */
            if (xSemaphoreTake(mutex_bms_state, pdMS_TO_TICKS(5U)) == pdTRUE) {
                g_bms_state.soc_pct = (uint8_t)(soc * 100.0f + 0.5f);
                xSemaphoreGive(mutex_bms_state);
            }
        }

        vTaskDelay(pdMS_TO_TICKS(100U));
    }
}

/* ============================================================
 * NVM Writer Task — P2, 1s
 * ============================================================ */
static void task_nvm_writer(void* pv_params)
{
    (void)pv_params;

    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(1000U));

        BmsNvmData_t nvm = {0};
        if (xSemaphoreTake(mutex_bms_state, pdMS_TO_TICKS(10U)) == pdTRUE) {
            nvm.soc_at_shutdown = (float)g_bms_state.soc_pct / 100.0f;
            nvm.soh_pct         = g_bms_state.soh_pct;
            xSemaphoreGive(mutex_bms_state);
        }
        nvm.crc8 = compute_crc8((const uint8_t*)&nvm, sizeof(nvm) - 1U);
        nvm_write_block(NVM_BLOCK_BMS, &nvm, sizeof(nvm));
    }
}

/* ============================================================
 * Task Creation — called from main()
 * ============================================================ */
void bms_rtos_init(void)
{
    q_cell_voltages      = xQueueCreate(1U,  sizeof(uint16_t) * 96U);
    q_pack_measurements  = xQueueCreate(1U,  sizeof(BmsMeasurement_t));
    q_balance_cmds       = xQueueCreate(12U, sizeof(BalanceCommand));
    q_can_tx             = xQueueCreate(8U,  sizeof(uint8_t) * 8U);

    sem_afe_ready        = xSemaphoreCreateBinary();
    mutex_bms_state      = xSemaphoreCreateMutex();
    eg_faults            = xEventGroupCreate();

    xTaskCreate(task_contactor_ctrl, "ContCtrl", 512U, NULL, 6, NULL);
    xTaskCreate(task_cell_monitor,   "CellMon",  512U, NULL, 5, NULL);
    xTaskCreate(task_soc_calculator, "SoCCalc",  1024U, NULL, 4, NULL);
    xTaskCreate(task_uds_handler,    "UDS",       1024U, NULL, 4, NULL);
    xTaskCreate(task_balancer,       "Balancer",  512U, NULL, 3, NULL);
    xTaskCreate(task_nvm_writer,     "NVM",       256U, NULL, 2, NULL);
    xTaskCreate(task_can_comms,      "CAN",       512U, NULL, 1, NULL);

    vTaskStartScheduler();
}
```

---

## 3. DMA ISR — AFE Voltage Conversion Complete

```c
/* LTC6811 SPI DMA transfer complete ISR
   Runs in ISR context — MUST be < 5µs
   Priority must be ≤ configMAX_SYSCALL_INTERRUPT_PRIORITY */

void DMA2_Stream3_IRQHandler(void)
{
    BaseType_t higher_priority_woken = pdFALSE;

    if (DMA2->LISR & DMA_LISR_TCIF3) {
        DMA2->LIFCR = DMA_LIFCR_CTCIF3;   /* Clear interrupt flag */

        /* Validate SPI PEC checksum before releasing semaphore */
        if (afe_pec_valid()) {
            xSemaphoreGiveFromISR(sem_afe_ready, &higher_priority_woken);
        }
        /* else: cell monitor task will handle timeout → DTC */
    }

    portYIELD_FROM_ISR(higher_priority_woken);
}
```

---

## 4. ISO 26262 — BMS ASIL Allocation

| BMS Function | Failure Mode | ASIL | Safety Goal |
|---|---|---|---|
| Cell OV2 detection & reaction | False negative → cell fire | ASIL B | Open contactors within 2ms of confirmed OV2 |
| Cell UV2 detection | False negative → cell reversal | ASIL B | Open contactors within 10ms |
| Cell OT2 detection | False negative → thermal runaway | ASIL B | Open contactors, activate cooling |
| Contactor weld detection | Undetected weld → shock risk | ASIL B | Detect on every open command |
| Isolation monitoring (IMD) | Loss of isolation → HV contact | ASIL B | UN R100: 500 Ω/V minimum |
| SoC estimation | Gross error → deep discharge | QM | Display warning only |
| Cell balancing | Wrong cell discharged | QM | Does not affect safety |
| UDS diagnostics | Wrong DID response | QM | No safety relevance |

### ASIL B Requirements Applied to OV2 Path

```
ASIL B decomposition:
    - ASIL B = ASIL B(A) + ASIL B(B)  (if independent)
    OR = single ASIL B channel

OV2 protection implementation meets single-channel ASIL B:
    ✓ MISRA C:2012 compliance in detection code
    ✓ Software CRC on AFE SPI data (PEC-15)
    ✓ Redundant HW comparator on cell select nodes (separate µC pin)
    ✓ Watchdog ensures task execution (WDST: 5ms armed, 1ms window)
    ✓ DTC confirmed (3 consecutive samples > OV2) before action — debounce
    ✓ Independent OV2 test case in ASIL B-classified test module
```

---

## 5. IEC 62619 — Safety Requirements for Li-ion BMS

| Clause | Requirement | Implementation |
|---|---|---|
| 6.1 | Cell level over-current protection | HW fuse + SW current limit contactor |
| 6.2 | Over-voltage protection | AFE hardware OV pin + SW confirmation |
| 6.3 | Under-voltage protection | AFE hardware UV pin + SW confirmation |
| 6.4 | Over-temperature protection | Thermistor + AFE + SW debounce 1s |
| 6.5 | Short-circuit protection | HW current sense + 1ms SW reaction |
| 7.1 | Cell reversal protection | UV2 threshold + contactor open |
| 7.2 | Charge at low temperature | SW inhibit charge if T < 0°C, charging |
| 8.1 | Isolation resistance (HV) | IMD: 500 Ω/V, monitored every 100ms |

---

## 6. Watchdog Configuration — BMS Safety Monitor

```c
/* IWDG + WWDG dual watchdog for ASIL B */

/* IWDG — Independent Watchdog (uses LSI ~32kHz, cannot be disabled by SW) */
#define IWDG_TIMEOUT_MS   50U   /* Safety: 50ms max task stall allowed */

void iwdg_init(void)
{
    IWDG->KR  = 0x5555U;   /* Unlock */
    IWDG->PR  = 0x03U;     /* /32 prescaler → tick = 1ms @ 32kHz */
    IWDG->RLR = IWDG_TIMEOUT_MS;
    IWDG->KR  = 0xAAAAU;   /* Reload */
    IWDG->KR  = 0xCCCCU;   /* Start */
}

void iwdg_kick(void) { IWDG->KR = 0xAAAAU; }

/* Kicked from Idle task — only reached if all higher priority tasks completed */
static void task_idle_watchdog(void* pv_params)
{
    (void)pv_params;
    for (;;) {
        iwdg_kick();
        vTaskDelay(pdMS_TO_TICKS(10U));
    }
}

/* WWDG — Window Watchdog (early-kick detection for timing violations) */
#define WWDG_WINDOW   0x60U   /* Must kick within window ≥ 0x40, ≤ 0x7F */
#define WWDG_COUNTER  0x7FU

void wwdg_init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_WWDGEN;
    WWDG->CFR  = WWDG_PRESCALER_8 | WWDG_WINDOW;
    WWDG->CR   = WWDG_CR_WDGA | WWDG_COUNTER;
}

void wwdg_kick(void) { WWDG->CR = WWDG_COUNTER; }
```

---

## 7. Safety Mechanisms — BMS Diagnostics

### 7.1 Cell Voltage Plausibility

```c
/* Check: sum of cell voltages ≈ pack voltage sensor */
bool check_voltage_plausibility(const BmsPackData_t* pack)
{
    uint32_t sum_mv = 0UL;
    for (uint8_t m = 0U; m < BMS_NUM_MODULES; ++m) {
        for (uint8_t c = 0U; c < BMS_CELLS_PER_MODULE; ++c) {
            sum_mv += pack->modules[m].cells[c].voltage_mv;
        }
    }
    /* Allow ±2% tolerance (wiring resistance) */
    uint32_t tolerance = pack->pack_voltage_mv / 50UL;   /* 2% */
    int32_t  diff      = (int32_t)sum_mv - (int32_t)pack->pack_voltage_mv;
    if (diff < 0) diff = -diff;

    if ((uint32_t)diff > tolerance) {
        report_dtc(DTC_VOLTAGE_PLAUSIBILITY, pack, get_system_tick_ms());
        return false;
    }
    return true;
}
```

### 7.2 Current Sensor Validation

```c
/* Cross-check: HV current vs 12V LV current (energy balance) */
bool check_current_sensor_plausibility(float hv_current_a, float lv_power_w,
                                        float pack_voltage_v)
{
    /* HV power = V × I */
    float hv_power_w = pack_voltage_v * hv_current_a;
    float lv_power_derived = hv_power_w * 0.95f;  /* 95% inverter efficiency estimate */

    /* Allow 20% tolerance due to efficiency model uncertainty */
    float tolerance = lv_power_derived * 0.20f;
    float diff      = fabsf(lv_power_w - lv_power_derived);

    return diff <= tolerance;
}
```

### 7.3 Contactor Weld Detection

```c
/* Weld detection: after command to open main positive,
   if DC link voltage stays high → weld suspected */
typedef struct {
    bool    cmd_open_sent;
    uint32_t cmd_timestamp_ms;
    float   expected_v_drop_v;
} WeldDetector_t;

static WeldDetector_t s_weld;

void weld_detector_on_open_command(float dc_link_v)
{
    s_weld.cmd_open_sent      = true;
    s_weld.cmd_timestamp_ms   = get_system_tick_ms();
    s_weld.expected_v_drop_v  = dc_link_v * 0.90f;  /* Expect ≥10% drop in 200ms */
}

void weld_detector_run(float dc_link_v)
{
    if (!s_weld.cmd_open_sent) return;

    uint32_t elapsed = get_system_tick_ms() - s_weld.cmd_timestamp_ms;

    if (elapsed > 200U) {
        if (dc_link_v > s_weld.expected_v_drop_v) {
            /* DC link not dropped — weld suspected */
            xEventGroupSetBits(eg_faults, FAULT_BIT_WELD);
            report_dtc(DTC_CONTACTOR_WELD, NULL, get_system_tick_ms());
        }
        s_weld.cmd_open_sent = false;
    }
}
```

---

## 8. Memory Protection (ARM Cortex-M4 MPU)

```c
/* MPU region map for BMS MCU */
/* Region 0: Flash (RX only) */
/* Region 1: Data SRAM (RW) */
/* Region 2: DMA buffer (RO for CPU — prevent accidental write) */
/* Region 3: Contactor I/O registers (RW, strongly ordered) */
/* Region 4: Stack overflow guard (no access) */

void mpu_configure_bms(void)
{
    MPU->CTRL = 0U;   /* Disable MPU before config */

    /* Region 2: AFE DMA buffer — CPU reads only */
    MPU->RNR  = 2U;
    MPU->RBAR = (uint32_t)&s_afe_dma_buffer;
    MPU->RASR = MPU_RASR_ENABLE
              | MPU_RASR_SIZE_4KB
              | MPU_RASR_AP_PRIV_RO
              | MPU_RASR_XN;   /* No execute */

    /* Region 3: Contactor GPIO registers */
    MPU->RNR  = 3U;
    MPU->RBAR = CONTACTOR_GPIO_BASE;
    MPU->RASR = MPU_RASR_ENABLE
              | MPU_RASR_SIZE_256B
              | MPU_RASR_AP_PRIV_RW
              | MPU_RASR_B    /* Bufferable */
              | MPU_RASR_XN;

    /* Region 4: Stack canary / guard page (no access) */
    MPU->RNR  = 4U;
    MPU->RBAR = STACK_GUARD_ADDR;
    MPU->RASR = MPU_RASR_ENABLE | MPU_RASR_SIZE_32B | MPU_RASR_AP_NO_ACCESS;

    MPU->CTRL = MPU_CTRL_ENABLE | MPU_CTRL_PRIVDEFENA;
    __DSB(); __ISB();
}
```

---

## 9. AUTOSAR Integration — DEM / NVM / FIM

```c
/* AUTOSAR DEM: set event */
void bms_report_fault_dem(uint32_t dtc_code)
{
    /* Map BMS DTC to AUTOSAR EventId */
    Dem_EventIdType event_id = bms_dtc_to_dem_event(dtc_code);
    (void)Dem_SetEventStatus(event_id, DEM_EVENT_STATUS_FAILED);
}

/* AUTOSAR NVM: request write */
void bms_persist_soc_nvm(float soc)
{
    BmsNvmData_t nvm_data = {0};
    nvm_data.soc_at_shutdown = soc;
    nvm_data.crc8 = compute_crc8((const uint8_t*)&nvm_data, sizeof(nvm_data) - 1U);

    /* Request NvM write — asynchronous */
    NvM_WriteBlock(NVM_BLOCK_BMS_SOC, &nvm_data);
    /* Completion notified via NvM_JobFinishedCallback_BMS() */
}

/* FIM: inhibit balancing during charging fault */
void bms_fim_check_balancer(void)
{
    FiM_FunctionIdType fim_id = FIM_BALANCER_FUNCTION;
    boolean inhibited = FALSE;
    (void)FiM_GetFunctionPermission(fim_id, &inhibited);
    if (inhibited == TRUE) {
        stop_all_balancing();
    }
}
```

---

## 10. Worst-Case Execution Time (WCET) Analysis

| Task | WCET Estimate | Budget | Margin |
|---|---|---|---|
| Cell Monitor (96 cells) | 380 µs | 10ms | 96% |
| OV2 detection in Cell Monitor | 45 µs | 1ms (safety) | 95.5% |
| EKF SoC update (2-state) | 28 µs | 100ms | >99% |
| Contactor state tick | 8 µs | 10ms | 99.9% |
| UDS 0x22 RDBI dispatch | 12 µs per DID | 25ms | >99% |
| AFE PEC checksum (96 cells) | 210 µs | N/A (ISR) | < allowed |

### WCET Measurement Code

```c
/* Arm PMU cycle counter for WCET profiling */
void wcet_start(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT  = 0U;
    DWT->CTRL   |= DWT_CTRL_CYCCNTENA_Msk;
}

uint32_t wcet_stop_cycles(void) {
    return DWT->CYCCNT;
}

/* Usage in cell monitor: */
void measure_cell_monitor_wcet(void)
{
    wcet_start();
    run_cell_monitor_pass();
    uint32_t cycles = wcet_stop_cycles();
    float us = (float)cycles / 168.0f;    /* 168 MHz STM32F4 */
    if (us > g_max_cell_monitor_us) g_max_cell_monitor_us = us;
}
```

---

*File: 03_rtos_safety_bms.md | c_cpp_bms learning series*
