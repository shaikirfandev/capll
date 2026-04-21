# RTOS, ISO 26262 & SOTIF for ADAS in C/C++

> **Coverage:** Real-Time Scheduling, Sensor Timing, ISO 26262 ASIL B/D for ADAS,
>               ISO 21448 (SOTIF), Functional Safety Mechanisms, Hardware Monitors

---

## 1. ADAS Real-Time Task Architecture

```
Scheduling overview (Deadline-Monotonic):
┌─────────────────────────────────────────────────────┐
│  Period  │  Deadline │  Task                        │
│  10 ms   │  10 ms    │  Radar raw processing        │
│  20 ms   │  20 ms    │  Camera object detection     │
│  20 ms   │  20 ms    │  Sensor fusion + tracking    │
│  20 ms   │  20 ms    │  FCW / AEB decision          │
│  50 ms   │  50 ms    │  ACC / LKA control output    │
│ 100 ms   │ 100 ms    │  LDW / TSR processing        │
│ 100 ms   │ 100 ms    │  Diagnostic health monitor   │
│ 500 ms   │ 500 ms    │  NVM / DTC reporting         │
└─────────────────────────────────────────────────────┘
```

---

## 2. FreeRTOS Task Setup for ADAS

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "timers.h"

/* Task handles */
static TaskHandle_t h_radar_task    = NULL;
static TaskHandle_t h_fusion_task   = NULL;
static TaskHandle_t h_fcw_task      = NULL;
static TaskHandle_t h_acc_task      = NULL;
static TaskHandle_t h_diag_task     = NULL;

/* Queues */
static QueueHandle_t q_radar_output = NULL;   /* RadarFrame → fusion */
static QueueHandle_t q_fused_objects = NULL;  /* FusedObjects → FCW/ACC */

/* Semaphores */
static SemaphoreHandle_t sem_radar_frame_ready   = NULL;
static SemaphoreHandle_t sem_camera_frame_ready  = NULL;

/* Stack sizes (words = 4 bytes on ARM) */
#define RADAR_TASK_STACK   512U   /* 2 KB */
#define FUSION_TASK_STACK  1024U  /* 4 KB — larger for Kalman operations */
#define FCW_TASK_STACK     512U
#define ACC_TASK_STACK     512U
#define DIAG_TASK_STACK    256U

/* Task priorities (higher = more urgent) */
#define PRIORITY_RADAR    6U
#define PRIORITY_FUSION   5U
#define PRIORITY_FCW      5U
#define PRIORITY_ACC      4U
#define PRIORITY_DIAG     2U

void adas_create_tasks(void)
{
    /* Queues */
    q_radar_output   = xQueueCreate(4U, sizeof(RadarFrame_t));
    q_fused_objects  = xQueueCreate(2U, sizeof(FusedObjectList_t));

    /* Semaphores */
    sem_radar_frame_ready  = xSemaphoreCreateBinary();
    sem_camera_frame_ready = xSemaphoreCreateBinary();

    /* Create tasks */
    xTaskCreate(radar_processing_task, "RADAR",  RADAR_TASK_STACK,  NULL, PRIORITY_RADAR,  &h_radar_task);
    xTaskCreate(fusion_task,           "FUSION", FUSION_TASK_STACK, NULL, PRIORITY_FUSION, &h_fusion_task);
    xTaskCreate(fcw_aeb_task,          "FCW",    FCW_TASK_STACK,    NULL, PRIORITY_FCW,    &h_fcw_task);
    xTaskCreate(acc_lka_task,          "ACC",    ACC_TASK_STACK,    NULL, PRIORITY_ACC,    &h_acc_task);
    xTaskCreate(diagnostic_task,       "DIAG",   DIAG_TASK_STACK,   NULL, PRIORITY_DIAG,   &h_diag_task);

    vTaskStartScheduler();
}

/* Radar Processing Task — 10ms period */
void radar_processing_task(void* pvParameters)
{
    TickType_t last_wake = xTaskGetTickCount();
    RadarFrame_t frame;

    for (;;) {
        /* Wait for DMA completion semaphore (from ISR) */
        if (xSemaphoreTake(sem_radar_frame_ready, pdMS_TO_TICKS(15U)) == pdTRUE) {
            parse_radar_dma_buffer(&frame);
            xQueueOverwrite(q_radar_output, &frame);   /* Always deliver latest */
        } else {
            /* Radar timeout — report DTC */
            Dem_SetEventStatus(DEM_EVENT_RADAR_TIMEOUT, DEM_EVENT_STATUS_FAILED);
        }

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(10U));
    }
}

/* Sensor Fusion Task — 20ms period */
void fusion_task(void* pvParameters)
{
    TickType_t last_wake = xTaskGetTickCount();
    RadarFrame_t    radar_frame;
    FusedObjectList_t fused;

    for (;;) {
        /* Get latest radar frame (non-blocking — use previous if none) */
        xQueuePeek(q_radar_output, &radar_frame, 0U);

        run_fusion_and_tracking(&radar_frame, &fused);

        xQueueOverwrite(q_fused_objects, &fused);

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(20U));
    }
}

/* FCW/AEB Task — 20ms period, safety-critical */
void fcw_aeb_task(void* pvParameters)
{
    TickType_t last_wake = xTaskGetTickCount();
    FusedObjectList_t objects;

    for (;;) {
        if (xQueuePeek(q_fused_objects, &objects, pdMS_TO_TICKS(25U)) == pdTRUE) {
            fcw_run_logic(&objects);
            aeb_run_logic(&objects);
        } else {
            /* No fusion output — safe state: inhibit any active brake */
            aeb_cancel_intervention();
            Dem_SetEventStatus(DEM_EVENT_FUSION_TIMEOUT, DEM_EVENT_STATUS_FAILED);
        }

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(20U));
    }
}
```

---

## 3. Interrupt-Driven Sensor Acquisition

```c
/* Radar SPI DMA complete ISR */
void DMA1_Stream0_IRQHandler(void)
{
    BaseType_t higher_prio_woken = pdFALSE;

    if (DMA1->LISR & DMA_LISR_TCIF0) {
        DMA1->LIFCR = DMA_LIFCR_CTCIF0;    /* Clear flag */
        xSemaphoreGiveFromISR(sem_radar_frame_ready, &higher_prio_woken);
    }

    portYIELD_FROM_ISR(higher_prio_woken);
}

/* Camera VSYNC ISR — marks end of frame */
void EXTI9_5_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;

    if (EXTI->PR & EXTI_PR_PR8) {
        EXTI->PR = EXTI_PR_PR8;
        xSemaphoreGiveFromISR(sem_camera_frame_ready, &woken);
    }

    portYIELD_FROM_ISR(woken);
}

/* Watchdog periodic refresh — must be called from a task that is alive */
void watchdog_task(void* pvParameters)
{
    for (;;) {
        IWDG->KR = 0xAAAAU;      /* Kick watchdog */
        vTaskDelay(pdMS_TO_TICKS(50U));
    }
}
```

---

## 4. ISO 26262 ADAS Safety Architecture

### ASIL Classification for ADAS Functions

| ADAS Function | Hazard | ASIL | Reasoning |
|---|---|---|---|
| AEB (Auto Emergency Braking) | Unintended braking at speed | ASIL D | Life-threatening, no driver override time |
| FCW activation | False alarm — driver distraction | ASIL B | Driver can override |
| LKA steering intervention | Unintended steer to oncoming | ASIL D | High speed, no time to react |
| ACC speed control | Speed too high | ASIL B | Driver can brake |
| LDW warning | Nuisance alert | QM | No safety-critical outcome |
| Sensor self-diagnosis | Missed fault | ASIL B | Must detect sensor failure |

### Safety Mechanism — Independent Monitor

```c
/* AEB Safety Monitor — diverse implementation (ASIL D decomposed to 2×ASIL B) */

/* Primary path: main ADAS ECU (Cortex-A72, QNX) */
static float primary_ttc_s   = 99.0f;
static bool  primary_aeb_cmd = false;

/* Monitor path: safety monitor MCU (Cortex-M7, FreeRTOS) */
static float  monitor_ttc_s   = 99.0f;
static bool   monitor_aeb_cmd = false;

/* Comparison via dedicated safety bus (internal CAN between ECUs) */
#define AEB_TTC_MISMATCH_THRESHOLD_S 0.3f

void safety_monitor_10ms(void)
{
    float ttc_diff = fabsf(primary_ttc_s - monitor_ttc_s);

    if (ttc_diff > AEB_TTC_MISMATCH_THRESHOLD_S) {
        /* Paths disagree — enter safe state */
        Dem_SetEventStatus(DEM_EVENT_AEB_MONITOR_MISMATCH, DEM_EVENT_STATUS_FAILED);
        aeb_force_safe_state();
        return;
    }

    /* Both paths must agree to allow AEB intervention */
    if (primary_aeb_cmd && monitor_aeb_cmd) {
        aeb_allow_braking();
    }
}
```

---

## 5. ISO 21448 (SOTIF) — Operating Scenarios

```
SOTIF addresses failures in absence of faults — performance limitations.

┌──────────────────────────────────────────────────────┐
│  ISO 26262 Domain          │  ISO 21448 (SOTIF) Domain│
│  (Random hardware faults,  │  (Insufficient spec,     │
│   systematic errors)       │   sensor limitations,    │
│                            │   corner cases)          │
├────────────────────────────┼──────────────────────────┤
│ Radar HW failure           │ Radar blinded by rain    │
│ Camera CPU hang            │ Camera in bright sunlight│
│ CRC error on CAN frame     │ Wrong object class (CNN) │
│ Sensor supply voltage drop │ Pedestrian in dark coat  │
└────────────────────────────┴──────────────────────────┘
```

```c
/* SOTIF degradation monitor — check sensor quality flags */
typedef struct {
    uint8_t radar_degraded;    /* 0=OK, 1=partial, 2=fully degraded */
    uint8_t camera_degraded;
    uint8_t lidar_degraded;
    uint8_t fusion_confidence; /* 0–100 */
} SensorHealthStatus_t;

/* Performance limitation detection */
void check_sensor_performance(SensorHealthStatus_t* health)
{
    if (health == NULL) return;

    /* Radar: low number of valid targets in clear weather = possible blockage */
    if (get_radar_valid_target_count() < 2U && is_weather_clear()) {
        health->radar_degraded = 2U; /* Fully degraded */
        Dem_SetEventStatus(DEM_EVENT_RADAR_BLOCKAGE, DEM_EVENT_STATUS_FAILED);
    }

    /* Camera: low image brightness = night / tunnel */
    if (get_camera_mean_luminance() < 15U) {
        health->camera_degraded = 1U; /* Partial */
    }

    /* Camera: overexposure = direct sun / headlights */
    if (get_camera_saturation_pixels_pct() > 40U) {
        health->camera_degraded = 2U;
    }

    /* Degrade system behaviour based on sensor health */
    if (health->radar_degraded == 2U || health->camera_degraded == 2U) {
        /* SOTIF safe action: increase TTC threshold, reduce max speed */
        set_fcw_ttc_threshold(FCW_TTC_ALERT_S + 0.5f);
        set_acc_max_speed(80.0f / 3.6f);   /* Limit to 80 km/h */
        trigger_driver_attention_request();
    }
}
```

---

## 6. Functional Safety Mechanisms for ADAS

### Mechanism 1 — Plausibility Check (Radar vs Camera)

```c
/* Cross-sensor plausibility: radar range vs camera estimated distance */
#define PLAUSIBILITY_TOLERANCE_PCT 30.0f

bool check_object_plausibility(float radar_range_m, float camera_dist_m)
{
    if (camera_dist_m < 0.1f) return true;  /* Camera not estimating — skip */

    float ratio = (radar_range_m - camera_dist_m) / camera_dist_m * 100.0f;
    if (ratio < 0.0f) ratio = -ratio;

    if (ratio > PLAUSIBILITY_TOLERANCE_PCT) {
        Dem_SetEventStatus(DEM_EVENT_OBJECT_PLAUSIBILITY_FAIL, DEM_EVENT_STATUS_FAILED);
        return false;
    }
    return true;
}
```

### Mechanism 2 — Ego Motion Plausibility

```c
/* Cross-check: CAN speed vs IMU integrated speed */
static float s_imu_integrated_speed_ms = 0.0f;

void update_imu_speed(float accel_ms2, float dt_s)
{
    s_imu_integrated_speed_ms += accel_ms2 * dt_s;
    /* Clamp drift */
    if (s_imu_integrated_speed_ms < 0.0f) s_imu_integrated_speed_ms = 0.0f;
}

bool plausibility_ego_speed(float can_speed_ms)
{
    float diff = fabsf(can_speed_ms - s_imu_integrated_speed_ms);
    return diff < 5.0f;   /* Max 5 m/s difference allowed */
}
```

### Mechanism 3 — Brake Command Supervision

```c
/* AEB output supervision — brake pressure must respond within 100ms */
static uint32_t s_brake_cmd_ts_ms  = 0U;
static bool     s_brake_cmd_active = false;

void aeb_request_braking(float decel_ms2, uint32_t now_ms)
{
    s_brake_cmd_active = true;
    s_brake_cmd_ts_ms  = now_ms;
    send_brake_request_can(decel_ms2);
}

void supervise_brake_response(float actual_decel_ms2, uint32_t now_ms)
{
    if (!s_brake_cmd_active) return;

    uint32_t elapsed = now_ms - s_brake_cmd_ts_ms;

    if (elapsed > 100U && actual_decel_ms2 < 0.5f) {
        /* Braking not achieved within 100 ms — actuator failure */
        Dem_SetEventStatus(DEM_EVENT_AEB_ACTUATOR_FAIL, DEM_EVENT_STATUS_FAILED);
        s_brake_cmd_active = false;
    }

    if (actual_decel_ms2 >= 0.5f) {
        s_brake_cmd_active = false;   /* Confirmed */
    }
}
```

---

## 7. Memory Protection Unit (MPU) — ADAS Safety Regions

```c
/* ARM Cortex-M7 MPU configuration for ADAS safety partitioning */
#include "core_cm7.h"

void configure_mpu_adas(void)
{
    MPU->CTRL = 0U;   /* Disable MPU during configuration */

    /* Region 0: Radar DMA buffer — read-only for application tasks */
    MPU->RNR  = 0U;
    MPU->RBAR = 0x20000000U;   /* DMA buffer base address */
    MPU->RASR = MPU_RASR_ENABLE_Msk |
                (0x10U << MPU_RASR_SIZE_Pos) |   /* 128KB */
                (0x03U << MPU_RASR_AP_Pos)   |   /* Full access from priv, read-only from unpriv */
                (0x01U << MPU_RASR_TEX_Pos)  |   /* Normal memory */
                MPU_RASR_C_Msk | MPU_RASR_B_Msk;

    /* Region 1: FCW/AEB output registers — only FCW task can write */
    MPU->RNR  = 1U;
    MPU->RBAR = 0x20020000U;
    MPU->RASR = MPU_RASR_ENABLE_Msk |
                (0x0DU << MPU_RASR_SIZE_Pos) |   /* 32KB */
                (0x01U << MPU_RASR_AP_Pos);       /* Priv R/W, Unpriv no access */

    /* Region 2: Safety monitor area — read-only (monitor writes from M4 core) */
    MPU->RNR  = 2U;
    MPU->RBAR = 0x10000000U;   /* SRAM1 shared with safety MCU via AXI */
    MPU->RASR = MPU_RASR_ENABLE_Msk |
                (0x11U << MPU_RASR_SIZE_Pos) |   /* 256KB */
                (0x06U << MPU_RASR_AP_Pos);       /* Priv R/W, Unpriv read-only */

    MPU->CTRL = MPU_CTRL_ENABLE_Msk | MPU_CTRL_PRIVDEFENA_Msk;
    __DSB();
    __ISB();
}

/* MPU Fault Handler — safety reaction */
void MemManage_Handler(void)
{
    /* Log fault address */
    uint32_t fault_addr = SCB->MMFAR;
    (void)fault_addr;

    /* Safety reaction: disable AEB output, set fault DTC */
    disable_aeb_output();
    Dem_SetEventStatus(DEM_EVENT_MPU_VIOLATION, DEM_EVENT_STATUS_FAILED);

    /* Trigger soft reset via watchdog */
    for (;;) { /* Let watchdog expire */ }
}
```

---

## 8. Timing Analysis — WCET for Safety Functions

```c
/*
 * Worst-Case Execution Time (WCET) analysis for FCW decision function
 * Tool: Rapita RVS or TASKING Static Analyzer
 *
 * Measured on Cortex-A53 @ 1.2 GHz:
 *   fcw_run_logic():         280 µs typical, 410 µs WCET
 *   fusion update (20 tgts): 850 µs typical, 1.2 ms WCET
 *   Kalman update (1 target): 45 µs typical,  65 µs WCET
 *
 * Budget check:
 *   Task period = 20 ms
 *   WCET total fusion + FCW = 1.2 ms + 0.41 ms = 1.61 ms
 *   Utilisation = 1.61 / 20 = 8% — SAFE ✓
 */

/* Cycle counter for WCET measurement (Cortex-A) */
static inline uint32_t read_cycle_counter(void) {
#if defined(__ARM_ARCH_7A__) || defined(__ARM_ARCH_8A__)
    uint32_t cycles;
    __asm volatile("MRC p15, 0, %0, c9, c13, 0" : "=r"(cycles));
    return cycles;
#else
    return 0U;
#endif
}

void measure_fcw_wcet(void)
{
    uint32_t t_start = read_cycle_counter();
    fcw_run_logic(&g_fused_objects);
    uint32_t t_end   = read_cycle_counter();

    uint32_t cycles = t_end - t_start;
    uint32_t us     = cycles / 1200U;  /* 1.2 GHz */

    if (us > 500U) {
        /* WCET exceeded — report to safety monitor */
        Dem_SetEventStatus(DEM_EVENT_WCET_EXCEEDED, DEM_EVENT_STATUS_FAILED);
    }
}
```

---

## 9. AUTOSAR Adaptive — ADAS Service-Oriented Architecture

```cpp
/* AUTOSAR Adaptive: ADAS uses ara::com for inter-process communication */

/* Service: ObjectDetection — publishes fused object list */
namespace adas {
namespace services {

struct TrackedObject {
    uint8_t id;
    float   x_m, y_m;
    float   vx_ms, vy_ms;
    float   ttc_s;
    uint8_t class_id;
};

struct ObjectList {
    std::array<TrackedObject, 32> objects;
    uint8_t  count;
    uint64_t timestamp_ns;
};

} // namespace services
} // namespace adas

/* Fusion ECU (Publisher) */
class FusionService : public ara::com::sample::skeleton::ObjectDetectionSkeleton {
public:
    void publish_object_list(const adas::services::ObjectList& list) {
        ObjectList.Send(list);     /* ara::com Event Send */
    }
};

/* FCW ECU (Subscriber) */
class FcwService {
public:
    void init(void) {
        auto handles = ara::com::sample::proxy::ObjectDetectionProxy::FindService(
            ara::com::InstanceIdentifier{"FUSION_1"});
        if (!handles.empty()) {
            proxy_ = std::make_unique<ara::com::sample::proxy::ObjectDetectionProxy>(handles[0]);
            proxy_->ObjectList.Subscribe(1U);
            proxy_->ObjectList.SetReceiveHandler([this](){ on_objects_received(); });
        }
    }

private:
    void on_objects_received(void) {
        auto sample = proxy_->ObjectList.GetNewSamples(1U);
        if (!sample.empty()) {
            run_fcw_logic(*sample[0]);
        }
    }
    std::unique_ptr<ara::com::sample::proxy::ObjectDetectionProxy> proxy_;
};
```

---

*File: 03_rtos_safety_adas.md | c_cpp_adas learning series*
