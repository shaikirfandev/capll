/**
 * @file    sensor_api.h
 * @brief   Sensor Abstraction Layer (SAL) — unified API across all sensor models.
 *
 * Architecture:
 *
 *   Application
 *       ↓
 *   sensor_api.h   (this file — platform-independent interface)
 *       ↓
 *   sensor_driver.c  (per-sensor implementation registered at runtime)
 *       ↓
 *   hal_i2c / hal_mipi_csi2  (platform HAL)
 *
 * Supported sensor families: Sony IMX, OmniVision OV, ON Semi AR,
 *   Aptina, FLIR Lepton, onsemi Python, Basler daA series.
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef SENSOR_API_H
#define SENSOR_API_H

#include "platform_types.h"
#include "hal_i2c.h"

/* ─────────────────────────────────────────────────────────────────────────── */
/* Limits                                                                      */
/* ─────────────────────────────────────────────────────────────────────────── */
#define SENSOR_MAX_REGISTERED       8U
#define SENSOR_MAX_RESOLUTION_MODES 16U
#define SENSOR_MAX_NAME_LEN         32U
#define SENSOR_MAX_MODEL_ID_LEN     16U
#define SENSOR_EEPROM_MAX_BYTES     4096U

/* ─────────────────────────────────────────────────────────────────────────── */
/* Enumerations                                                                */
/* ─────────────────────────────────────────────────────────────────────────── */

/** @brief Pixel format codes (follow V4L2 FOURCC conventions). */
typedef enum {
    SENSOR_PIXFMT_RAW8       = 0x00,
    SENSOR_PIXFMT_RAW10      = 0x01,
    SENSOR_PIXFMT_RAW12      = 0x02,
    SENSOR_PIXFMT_RAW14      = 0x03,
    SENSOR_PIXFMT_RAW16      = 0x04,
    SENSOR_PIXFMT_YUV422     = 0x10,
    SENSOR_PIXFMT_YUV420     = 0x11,
    SENSOR_PIXFMT_RGB888     = 0x20,
    SENSOR_PIXFMT_RGB565     = 0x21,
    SENSOR_PIXFMT_MONO8      = 0x30,
    SENSOR_PIXFMT_MONO16     = 0x31,
    SENSOR_PIXFMT_IR10       = 0x40,   /**< Thermal IR, 10-bit */
} sensor_pixel_format_t;

/** @brief HDR exposure modes. */
typedef enum {
    SENSOR_HDR_DISABLED = 0,
    SENSOR_HDR_2FRAME,          /**< 2-frame short+long exposure */
    SENSOR_HDR_3FRAME,          /**< 3-frame HDR */
    SENSOR_HDR_DOL,             /**< Digital Overlap (Sony DOL-HDR) */
    SENSOR_HDR_STAGGER,         /**< Stagger HDR (e.g. AR0820) */
} sensor_hdr_mode_t;

/** @brief Sensor power state. */
typedef enum {
    SENSOR_POWER_OFF     = 0,
    SENSOR_POWER_STANDBY = 1,
    SENSOR_POWER_ACTIVE  = 2,
} sensor_power_state_t;

/** @brief Trigger source. */
typedef enum {
    SENSOR_TRIG_FREERUN = 0,        /**< Continuous free-running */
    SENSOR_TRIG_HARDWARE,           /**< External hardware trigger */
    SENSOR_TRIG_SOFTWARE,           /**< Software trigger command */
    SENSOR_TRIG_HARDWARE_BURST,     /**< Triggered burst of N frames */
} sensor_trigger_mode_t;

/** @brief Mirror/flip. */
typedef enum {
    SENSOR_FLIP_NONE    = 0x00,
    SENSOR_FLIP_H       = 0x01,
    SENSOR_FLIP_V       = 0x02,
    SENSOR_FLIP_HV      = 0x03,
} sensor_flip_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Data structures                                                             */
/* ─────────────────────────────────────────────────────────────────────────── */

/** @brief Region of interest. */
typedef struct {
    u16 x;
    u16 y;
    u16 width;
    u16 height;
} sensor_roi_t;

/** @brief Resolution and timing mode descriptor. */
typedef struct {
    u16                  width;
    u16                  height;
    sensor_pixel_format_t pixel_format;
    u8                   mipi_lanes;        /**< 1, 2, or 4 CSI-2 data lanes */
    u32                  mipi_data_rate_mbps;
    u16                  frame_rate_max;    /**< Maximum FPS at this mode */
    u16                  frame_rate_min;
    bool                 hdr_capable;
    u32                  hdr_modes_mask;    /**< Bitmask of sensor_hdr_mode_t */
    u8                   binning_h;         /**< Horizontal binning factor */
    u8                   binning_v;
} sensor_mode_desc_t;

/** @brief Sensor identification. */
typedef struct {
    char name[SENSOR_MAX_NAME_LEN];
    char model_id[SENSOR_MAX_MODEL_ID_LEN];
    u16  chip_id;
    u8   revision;
    u32  pixel_array_width;
    u32  pixel_array_height;
    u8   i2c_addr;                         /**< Default 7-bit I2C address */
    bool auto_detect;                      /**< Probe by chip-id register */
    u16  chip_id_reg;
    u16  chip_id_expected;
} sensor_identity_t;

/** @brief Sensor configuration request (what the caller wants). */
typedef struct {
    u16                  width;
    u16                  height;
    sensor_pixel_format_t pixel_format;
    u16                  frame_rate;       /**< Requested FPS */
    sensor_hdr_mode_t    hdr_mode;
    sensor_roi_t         roi;              /**< Active window within array */
    bool                 use_full_array;   /**< If true, ignore roi */
    u16                  exposure_us;      /**< Coarse exposure in µs */
    u16                  gain_x100;        /**< Analogue gain × 100 (100 = 1×) */
    u16                  digital_gain_x100;
    sensor_trigger_mode_t trigger_mode;
    sensor_flip_t        flip;
    bool                 test_pattern;     /**< Enable sensor built-in test pattern */
    u8                   test_pattern_id;
} sensor_config_t;

/** @brief Sensor capabilities reported by the driver. */
typedef struct {
    u8               mode_count;
    sensor_mode_desc_t modes[SENSOR_MAX_RESOLUTION_MODES];
    u16              min_exposure_us;
    u32              max_exposure_us;
    u16              min_gain_x100;
    u16              max_gain_x100;
    u16              min_digital_gain_x100;
    u16              max_digital_gain_x100;
    bool             has_hardware_trigger;
    bool             has_master_slave;
    bool             has_embedded_metadata;
    bool             has_optical_black_rows;
    bool             has_temperature_sensor;
    bool             has_eeprom;
    u16              eeprom_size_bytes;
} sensor_capabilities_t;

/** @brief Real-time statistics from the sensor. */
typedef struct {
    u32              frame_count;
    u32              frame_drop_count;
    u32              crc_error_count;
    u32              overflow_count;
    u16              current_gain_x100;
    u32              current_exposure_us;
    s16              temperature_c_x10;    /**< Temperature × 10, e.g. 253 = 25.3 °C */
    u16              current_frame_rate_x10;
    isf_timestamp_us_t last_frame_timestamp;
} sensor_runtime_stats_t;

/** @brief Opaque sensor handle. */
typedef struct sensor_context_s *sensor_handle_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Driver registration structure (filled by each sensor driver module)        */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct {
    sensor_identity_t   identity;

    /** @brief Called once per sensor instance. Allocates context and resets HW. */
    isf_status_t (*probe)(hal_i2c_bus_t bus, sensor_handle_t *out_handle);

    /** @brief Apply full configuration. Called before streaming. */
    isf_status_t (*configure)(sensor_handle_t handle, const sensor_config_t *cfg);

    /** @brief Start streaming (release sensor from standby). */
    isf_status_t (*start_streaming)(sensor_handle_t handle);

    /** @brief Stop streaming (puts sensor in standby). */
    isf_status_t (*stop_streaming)(sensor_handle_t handle);

    /** @brief Set analogue gain. gain_x100: 100 = 1×, 200 = 2×. */
    isf_status_t (*set_gain)(sensor_handle_t handle, u16 gain_x100);

    /** @brief Set integration (exposure) time in microseconds. */
    isf_status_t (*set_exposure)(sensor_handle_t handle, u32 exposure_us);

    /** @brief Set frame rate. Adjusts blanking lines. */
    isf_status_t (*set_frame_rate)(sensor_handle_t handle, u16 fps);

    /** @brief Enable/disable HDR mode. */
    isf_status_t (*set_hdr_mode)(sensor_handle_t handle, sensor_hdr_mode_t mode);

    /** @brief Set ROI within the pixel array. */
    isf_status_t (*set_roi)(sensor_handle_t handle, const sensor_roi_t *roi);

    /** @brief Send a software trigger (for SENSOR_TRIG_SOFTWARE). */
    isf_status_t (*trigger)(sensor_handle_t handle);

    /** @brief Read temperature from embedded sensor. Returns °C × 10. */
    isf_status_t (*read_temperature)(sensor_handle_t handle, s16 *out_temp_x10);

    /** @brief Power control. */
    isf_status_t (*set_power_state)(sensor_handle_t handle, sensor_power_state_t state);

    /** @brief Read EEPROM (calibration data, lens shading tables). */
    isf_status_t (*read_eeprom)(sensor_handle_t handle, u16 offset, u8 *buf, u16 len);

    /** @brief Read runtime statistics. */
    isf_status_t (*get_stats)(sensor_handle_t handle, sensor_runtime_stats_t *out_stats);

    /** @brief Read sensor capabilities. */
    isf_status_t (*get_caps)(sensor_handle_t handle, sensor_capabilities_t *out_caps);

    /** @brief Release all resources. */
    isf_status_t (*remove)(sensor_handle_t handle);

} sensor_driver_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Sensor Manager API                                                          */
/* ─────────────────────────────────────────────────────────────────────────── */

/**
 * @brief   Register a sensor driver in the global driver table.
 *          Called by each sensor module's __init or constructor.
 */
isf_status_t sensor_register_driver(const sensor_driver_t *driver);

/**
 * @brief   Probe all I2C buses and all registered drivers.
 *          Returns handles for sensors found.
 * @param   out_handles  Array of handles (size SENSOR_MAX_REGISTERED).
 * @param   out_count    Number of sensors found.
 */
isf_status_t sensor_discover(hal_i2c_bus_t *buses,
                              u8 bus_count,
                              sensor_handle_t *out_handles,
                              u8 *out_count);

/** @brief Open a specific sensor by name and I2C address. */
isf_status_t sensor_open(hal_i2c_bus_t bus,
                          const char *sensor_name,
                          u8 i2c_addr,
                          sensor_handle_t *out_handle);

/** @brief Close sensor (stop streaming, release handle). */
isf_status_t sensor_close(sensor_handle_t handle);

/** @brief Configure sensor with the given settings. */
isf_status_t sensor_configure(sensor_handle_t handle, const sensor_config_t *cfg);

/** @brief Start frame capture. */
isf_status_t sensor_start(sensor_handle_t handle);

/** @brief Stop frame capture. */
isf_status_t sensor_stop(sensor_handle_t handle);

/* Convenience wrappers that delegate to driver function pointers */
isf_status_t sensor_set_gain(sensor_handle_t handle, u16 gain_x100);
isf_status_t sensor_set_exposure(sensor_handle_t handle, u32 exposure_us);
isf_status_t sensor_set_frame_rate(sensor_handle_t handle, u16 fps);
isf_status_t sensor_set_hdr(sensor_handle_t handle, sensor_hdr_mode_t mode);
isf_status_t sensor_set_roi(sensor_handle_t handle, const sensor_roi_t *roi);
isf_status_t sensor_trigger(sensor_handle_t handle);
isf_status_t sensor_get_stats(sensor_handle_t handle, sensor_runtime_stats_t *out);
isf_status_t sensor_get_caps(sensor_handle_t handle, sensor_capabilities_t *out);
isf_status_t sensor_read_temperature(sensor_handle_t handle, s16 *out_temp_x10);
isf_status_t sensor_read_eeprom(sensor_handle_t handle, u16 offset, u8 *buf, u16 len);

/** @brief Dump a human-readable summary of sensor state to the logger. */
void sensor_dump_info(sensor_handle_t handle);

#endif /* SENSOR_API_H */
