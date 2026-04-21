# C Fundamentals for ADAS Engineering

> **Domain:** Advanced Driver Assistance Systems
> **Systems:** Camera, Radar, LiDAR, Ultrasonic, Sensor Fusion, Path Planning, V2X
> **Standards:** ISO 26262, ISO 21448 (SOTIF), MISRA C:2012, AUTOSAR Classic

---

## 1. Why C in ADAS?

| Layer | Language | Reason |
|---|---|---|
| MCAL / BSW Drivers | C | Direct hardware access, AUTOSAR mandated |
| Sensor raw data acquisition | C | ISR timing, DMA control, zero overhead |
| Safety monitors (ASIL D) | C | Deterministic, no hidden costs |
| Signal processing (DSP) | C + CMSIS | Optimised intrinsics, SIMD |
| Application logic (fusion) | C++ | OOP, templates, STL (Adaptive) |

---

## 2. Data Types — ADAS Signal Representation

```c
#include <stdint.h>     /* MISRA: use fixed-width types everywhere */
#include <stdbool.h>

/* Sensor measurement types */
typedef uint16_t  radar_range_cm_t;       /* 0–65535 cm (655.35 m) */
typedef int16_t   radar_velocity_cms_t;   /* -32768 to +32767 cm/s */
typedef uint8_t   radar_confidence_t;     /* 0–100 % */
typedef uint16_t  lidar_range_mm_t;       /* millimetre resolution */
typedef uint16_t  camera_pixel_t;         /* 16-bit depth or disparity */
typedef int32_t   position_mm_t;          /* signed world coordinates */
typedef float     angle_rad_t;            /* MISRA: float OK for physical angles */

/* Radar target structure */
typedef struct {
    radar_range_cm_t    range_cm;
    radar_velocity_cms_t radial_vel_cms;
    int16_t             azimuth_mdeg;    /* milli-degrees: -18000 to +18000 */
    int16_t             elevation_mdeg;
    radar_confidence_t  confidence_pct;
    uint8_t             target_id;
    uint8_t             is_valid;
} RadarTarget_t;

/* LiDAR point */
typedef struct {
    int32_t x_mm;    /* lateral */
    int32_t y_mm;    /* longitudinal */
    int32_t z_mm;    /* vertical */
    uint8_t intensity;
    uint8_t ring_id;
} LidarPoint_t;

/* Camera bounding box */
typedef struct {
    uint16_t x_left;
    uint16_t y_top;
    uint16_t width;
    uint16_t height;
    uint8_t  class_id;    /* 0=car, 1=truck, 2=pedestrian, 3=cyclist */
    uint8_t  confidence;  /* 0–100 */
} CameraObject_t;
```

---

## 3. Pointers — ADAS Buffer and DMA Patterns

```c
/* Read-only sensor buffer — const correctness */
void process_radar_frame(const RadarTarget_t* targets, uint8_t count) {
    if (targets == NULL || count == 0U) return;  /* MISRA: null check */

    for (uint8_t i = 0U; i < count; ++i) {
        if (targets[i].is_valid && targets[i].range_cm < 5000U) {
            classify_target(&targets[i]);
        }
    }
}

/* Double-pointer: update output array from processing */
typedef struct { float x; float y; float vx; float vy; } FusedObject_t;

uint8_t fuse_sensors(
    const RadarTarget_t*  radar,  uint8_t  n_radar,
    const CameraObject_t* camera, uint8_t  n_camera,
    FusedObject_t*        output, uint8_t  max_output)
{
    uint8_t count = 0U;
    for (uint8_t r = 0U; r < n_radar && count < max_output; ++r) {
        if (!radar[r].is_valid) continue;
        output[count].x  = (float)radar[r].range_cm * 0.01f;
        output[count].vx = (float)radar[r].radial_vel_cms * 0.01f;
        output[count].y  = 0.0f;
        output[count].vy = 0.0f;
        ++count;
    }
    return count;
}

/* Function pointer — sensor driver callback table */
typedef void (*SensorCb_t)(const uint8_t* data, uint16_t length);

typedef struct {
    uint8_t    sensor_id;
    SensorCb_t on_data_ready;
    SensorCb_t on_error;
} SensorDriver_t;

static void radar_data_cb(const uint8_t* data, uint16_t len);
static void camera_data_cb(const uint8_t* data, uint16_t len);

static const SensorDriver_t g_sensor_drivers[] = {
    {0U, radar_data_cb,  NULL},
    {1U, camera_data_cb, NULL},
};
```

---

## 4. Structures — ADAS Object Model

```c
/* Kinematics in ego-vehicle coordinate system */
typedef struct {
    float x_m;        /* longitudinal distance [m] */
    float y_m;        /* lateral distance [m] */
    float vx_ms;      /* longitudinal velocity [m/s] */
    float vy_ms;      /* lateral velocity [m/s] */
    float ax_ms2;     /* longitudinal acceleration [m/s²] */
    float heading_rad;
    float heading_rate_rads; /* yaw rate */
} Kinematics_t;

/* Object classification */
typedef enum {
    OBJ_CLASS_UNKNOWN    = 0U,
    OBJ_CLASS_CAR        = 1U,
    OBJ_CLASS_TRUCK      = 2U,
    OBJ_CLASS_PEDESTRIAN = 3U,
    OBJ_CLASS_CYCLIST    = 4U,
    OBJ_CLASS_MOTORCYCLE = 5U,
    OBJ_CLASS_ANIMAL     = 6U,
    OBJ_CLASS_STATIC     = 7U
} ObjectClass_t;

/* Fused tracked object */
typedef struct {
    uint8_t       id;
    ObjectClass_t class_type;
    Kinematics_t  kinematics;
    float         existence_probability;  /* 0.0–1.0 */
    float         ttc_s;                  /* Time-To-Collision [s] */
    float         thw_s;                  /* Time Headway [s] */
    uint8_t       is_in_path;
    uint8_t       sensor_source_mask;     /* bit0=radar, bit1=camera, bit2=lidar */
    uint32_t      timestamp_ms;
} TrackedObject_t;

/* Ego vehicle state */
typedef struct {
    float speed_ms;          /* vehicle speed [m/s] */
    float acceleration_ms2;  /* longitudinal acceleration [m/s²] */
    float yaw_rate_rads;     /* yaw rate [rad/s] */
    float steering_angle_rad;
    float lateral_acceleration_ms2;
    uint8_t gear;
    uint8_t brake_active;
    uint8_t hazard_lights;
} EgoState_t;
```

---

## 5. Bit Manipulation — CAN Signal Decoding for ADAS

```c
/* Extract ADAS status bits from CAN frame */
#define ADAS_STATUS_FCW_ACTIVE_BIT      (0U)   /* bit 0 */
#define ADAS_STATUS_AEB_ACTIVE_BIT      (1U)   /* bit 1 */
#define ADAS_STATUS_LDW_ACTIVE_BIT      (2U)   /* bit 2 */
#define ADAS_STATUS_LKA_ACTIVE_BIT      (3U)   /* bit 3 */
#define ADAS_STATUS_ACC_ACTIVE_BIT      (4U)   /* bit 4 */
#define ADAS_STATUS_BSM_LEFT_BIT        (5U)   /* bit 5 */
#define ADAS_STATUS_BSM_RIGHT_BIT       (6U)   /* bit 6 */
#define ADAS_STATUS_SYSTEM_FAULT_BIT    (7U)   /* bit 7 */

#define BIT_SET(byte, bit)    (((byte) >> (bit)) & 0x01U)
#define BIT_MASK(bit)         (1U << (bit))

typedef struct {
    uint8_t fcw_active   : 1;
    uint8_t aeb_active   : 1;
    uint8_t ldw_active   : 1;
    uint8_t lka_active   : 1;
    uint8_t acc_active   : 1;
    uint8_t bsm_left     : 1;
    uint8_t bsm_right    : 1;
    uint8_t system_fault : 1;
} AdasStatusBits_t;

void decode_adas_status(uint8_t raw_byte, AdasStatusBits_t* status) {
    if (status == NULL) return;
    status->fcw_active   = BIT_SET(raw_byte, ADAS_STATUS_FCW_ACTIVE_BIT);
    status->aeb_active   = BIT_SET(raw_byte, ADAS_STATUS_AEB_ACTIVE_BIT);
    status->ldw_active   = BIT_SET(raw_byte, ADAS_STATUS_LDW_ACTIVE_BIT);
    status->lka_active   = BIT_SET(raw_byte, ADAS_STATUS_LKA_ACTIVE_BIT);
    status->acc_active   = BIT_SET(raw_byte, ADAS_STATUS_ACC_ACTIVE_BIT);
    status->bsm_left     = BIT_SET(raw_byte, ADAS_STATUS_BSM_LEFT_BIT);
    status->bsm_right    = BIT_SET(raw_byte, ADAS_STATUS_BSM_RIGHT_BIT);
    status->system_fault = BIT_SET(raw_byte, ADAS_STATUS_SYSTEM_FAULT_BIT);
}

/* Pack 12-bit radar range into CAN frame (big-endian)            */
/* Range 0–4095 cm, offset 0, factor 1                            */
void encode_radar_range(uint8_t* frame, uint16_t range_cm) {
    frame[0] = (uint8_t)((range_cm >> 4U) & 0xFFU);         /* bits 11–4 */
    frame[1] = (uint8_t)((range_cm & 0x0FU) << 4U);         /* bits 3–0 in upper nibble */
}

uint16_t decode_radar_range(const uint8_t* frame) {
    return (uint16_t)(((uint16_t)frame[0] << 4U) | ((frame[1] >> 4U) & 0x0FU));
}
```

---

## 6. Arrays & Buffers — Sensor Data Pipelines

```c
#define MAX_RADAR_TARGETS    64U
#define MAX_LIDAR_POINTS   4096U
#define MAX_TRACKED_OBJECTS  32U
#define FRAME_HISTORY_SIZE    5U

/* Static allocation — no malloc in AUTOSAR Classic */
static RadarTarget_t   s_radar_targets[MAX_RADAR_TARGETS];
static LidarPoint_t    s_lidar_points[MAX_LIDAR_POINTS];
static TrackedObject_t s_tracked_objects[MAX_TRACKED_OBJECTS];

/* Ring buffer for object history (for trajectory prediction) */
typedef struct {
    Kinematics_t frames[FRAME_HISTORY_SIZE];
    uint8_t      head;
    uint8_t      count;
} KinematicsHistory_t;

void history_push(KinematicsHistory_t* h, const Kinematics_t* k) {
    if (h == NULL || k == NULL) return;
    h->frames[h->head] = *k;
    h->head = (h->head + 1U) % FRAME_HISTORY_SIZE;
    if (h->count < FRAME_HISTORY_SIZE) h->count++;
}

const Kinematics_t* history_get(const KinematicsHistory_t* h, uint8_t age) {
    /* age=0 → latest, age=1 → one frame back */
    if (h == NULL || age >= h->count) return NULL;
    uint8_t idx = (uint8_t)((h->head + FRAME_HISTORY_SIZE - 1U - age) % FRAME_HISTORY_SIZE);
    return &h->frames[idx];
}

/* 2D array — occupancy grid (80×80 cells, each cell = 25cm) */
#define GRID_ROWS 80U
#define GRID_COLS 80U
static uint8_t s_occupancy_grid[GRID_ROWS][GRID_COLS];  /* 0=free, 255=occupied */

void grid_mark_object(float obj_x_m, float obj_y_m) {
    /* Ego at grid centre (40,40) */
    int16_t col = (int16_t)(40.0f + obj_y_m / 0.25f);
    int16_t row = (int16_t)(40.0f - obj_x_m / 0.25f);
    if (col >= 0 && col < (int16_t)GRID_COLS &&
        row >= 0 && row < (int16_t)GRID_ROWS) {
        s_occupancy_grid[row][col] = 255U;
    }
}
```

---

## 7. Control Flow — ADAS State Machine

```c
/* FCW (Forward Collision Warning) state machine */
typedef enum {
    FCW_STATE_INACTIVE   = 0U,  /* No threat */
    FCW_STATE_ALERT      = 1U,  /* Visual + audio warning */
    FCW_STATE_CRITICAL   = 2U,  /* Pre-fill brakes */
    FCW_STATE_FAULT      = 3U
} FcwState_t;

static FcwState_t s_fcw_state = FCW_STATE_INACTIVE;

/* TTC thresholds */
#define FCW_TTC_ALERT_S    2.5f
#define FCW_TTC_CRITICAL_S 1.5f
#define FCW_MIN_SPEED_MS   2.8f  /* ~10 km/h */

void fcw_state_machine_20ms(const TrackedObject_t* lead_obj,
                             const EgoState_t*       ego)
{
    if (lead_obj == NULL || ego == NULL) {
        s_fcw_state = FCW_STATE_FAULT;
        return;
    }

    float ttc = lead_obj->ttc_s;
    float ego_speed = ego->speed_ms;

    switch (s_fcw_state) {
        case FCW_STATE_INACTIVE:
            if (ego_speed > FCW_MIN_SPEED_MS &&
                lead_obj->is_in_path &&
                ttc < FCW_TTC_ALERT_S &&
                ttc > 0.0f) {
                s_fcw_state = FCW_STATE_ALERT;
                trigger_fcw_warning_visual();
                trigger_fcw_warning_audio();
            }
            break;

        case FCW_STATE_ALERT:
            if (ttc < FCW_TTC_CRITICAL_S && ttc > 0.0f) {
                s_fcw_state = FCW_STATE_CRITICAL;
                trigger_brake_prefill();
            } else if (ttc >= FCW_TTC_ALERT_S || !lead_obj->is_in_path) {
                s_fcw_state = FCW_STATE_INACTIVE;
                cancel_fcw_warnings();
            }
            break;

        case FCW_STATE_CRITICAL:
            if (ttc >= FCW_TTC_ALERT_S || !lead_obj->is_in_path) {
                s_fcw_state = FCW_STATE_INACTIVE;
                release_brake_prefill();
            }
            break;

        case FCW_STATE_FAULT:
        default:
            /* Safe state — no active warnings */
            break;
    }
}
```

---

## 8. Math Functions — TTC, THW, Lateral Distance

```c
#include <math.h>

/* Time-To-Collision calculation */
float calculate_ttc(float rel_distance_m, float rel_velocity_ms) {
    /* rel_velocity > 0 means approaching */
    if (rel_velocity_ms <= 0.0f) return 99.0f;  /* Not approaching */
    return rel_distance_m / rel_velocity_ms;
}

/* Time-Headway */
float calculate_thw(float distance_m, float ego_speed_ms) {
    if (ego_speed_ms < 0.1f) return 99.0f;
    return distance_m / ego_speed_ms;
}

/* Lateral distance to lane marking */
float lateral_distance_to_line(
    float obj_x, float obj_y,   /* object position */
    float line_a, float line_b, float line_c)  /* ax + by + c = 0 */
{
    float denom = sqrtf(line_a * line_a + line_b * line_b);
    if (denom < 1e-6f) return 0.0f;
    return fabsf(line_a * obj_x + line_b * obj_y + line_c) / denom;
}

/* Simple path prediction — constant velocity model */
void predict_position(const Kinematics_t* current, float dt_s,
                      float* pred_x, float* pred_y) {
    if (current == NULL || pred_x == NULL || pred_y == NULL) return;
    *pred_x = current->x_m  + current->vx_ms * dt_s
            + 0.5f * current->ax_ms2 * dt_s * dt_s;
    *pred_y = current->y_m  + current->vy_ms * dt_s;
}

/* Euclidean distance between two positions */
float euclidean_dist(float x1, float y1, float x2, float y2) {
    float dx = x2 - x1;
    float dy = y2 - y1;
    return sqrtf(dx * dx + dy * dy);
}
```

---

## 9. Memory — Safe Access Patterns for ADAS

```c
#include <string.h>

/* Safe memcopy — always check bounds */
void safe_copy_radar_targets(RadarTarget_t* dst, const RadarTarget_t* src,
                              uint8_t count, uint8_t dst_capacity) {
    if (dst == NULL || src == NULL) return;
    uint8_t copy_count = (count < dst_capacity) ? count : dst_capacity;
    memcpy(dst, src, (size_t)copy_count * sizeof(RadarTarget_t));
}

/* Zero initialise sensor buffers at cycle start */
void clear_sensor_buffers(void) {
    memset(s_radar_targets,   0, sizeof(s_radar_targets));
    memset(s_lidar_points,    0, sizeof(s_lidar_points));
    memset(s_occupancy_grid,  0, sizeof(s_occupancy_grid));
}

/* Volatile for DMA-filled sensor buffer — prevent compiler reordering */
volatile uint8_t g_radar_dma_buffer[256U];
volatile bool    g_radar_dma_ready = false;

void radar_dma_complete_isr(void) {
    g_radar_dma_ready = true;     /* Signal to processing task */
}

void radar_processing_task(void) {
    if (g_radar_dma_ready) {
        g_radar_dma_ready = false;
        /* Copy volatile buffer to local non-volatile for processing */
        uint8_t local_buf[256U];
        for (uint16_t i = 0U; i < 256U; ++i) {
            local_buf[i] = g_radar_dma_buffer[i];
        }
        parse_radar_frame(local_buf, sizeof(local_buf));
    }
}
```

---

## 10. MISRA C:2012 — Top Rules for ADAS C Code

| Rule | Requirement | ADAS Context |
|---|---|---|
| Dir 4.1 | No runtime errors (arithmetic overflow) | Velocity, TTC calculations |
| Dir 4.7 | Check return values of functions | Sensor API calls |
| Rule 1.3 | No undefined behaviour | Pointer arithmetic |
| Rule 10.1 | Operands of essentially Boolean type | `is_valid` flag operations |
| Rule 10.3 | No implicit type conversion | float→uint conversions in CAN encoding |
| Rule 11.3 | No cast between pointer-to-object types | Sensor data buffer access |
| Rule 12.1 | Operator precedence — use parentheses | Bit-field expressions |
| Rule 14.4 | Boolean controlling conditions only | `if (is_valid)` not `if (value)` |
| Rule 15.5 | Single point of exit per function | Return from safety monitors |
| Rule 17.1 | No `<stdarg.h>` variadic | No printf-style in production |
| Rule 21.3 | No `malloc`/`free` | All buffers static |
| Rule 21.6 | No standard I/O | No `printf` in embedded ADAS |

---

## 11. Practical Exercises

### Exercise 1 — TTC Monitor
Implement a function that scans all `n` tracked objects and returns the minimum TTC among objects where `is_in_path == 1` and `ttc_s > 0`.

### Exercise 2 — Occupancy Grid Update
Write `void update_occupancy_grid(const LidarPoint_t* pts, uint16_t n)` that marks all LiDAR points within ±10 m lateral and 0–50 m longitudinal as occupied (255) in `s_occupancy_grid`.

### Exercise 3 — Radar-Camera Association
Write `uint8_t associate_radar_camera(const RadarTarget_t* r, const CameraObject_t* c, uint8_t n_cam)` that returns the index of the camera object whose bounding box centre best aligns with the radar target's azimuth angle.

---

*File: 01_c_fundamentals_adas.md | c_cpp_adas learning series*
