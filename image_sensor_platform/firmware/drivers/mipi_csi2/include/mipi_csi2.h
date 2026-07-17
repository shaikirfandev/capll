/**
 * @file    mipi_csi2.h
 * @brief   MIPI CSI-2 receiver driver interface.
 *
 * Implements the full CSI-2 spec (v3.0 compatible):
 *   - D-PHY and C-PHY support
 *   - 1/2/4 data lanes
 *   - Up to 2.5 Gbps per lane (D-PHY)
 *   - Long Packet: Image data, Embedded data
 *   - Short Packet: Frame Start, Frame End, Line Start, Line End
 *   - Virtual Channel multiplexing (VC0–VC3)
 *   - Data Type routing (RAW8/10/12/14/16, YUV422, RGB888)
 *   - Continuous and Non-Continuous clock modes
 *   - Error detection: ECC, CRC, SOT leader errors
 *   - Hardware-assisted DMA to frame buffer pool
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef MIPI_CSI2_H
#define MIPI_CSI2_H

#include "platform_types.h"
#include "hal_dma.h"

/* ─────────────────────────────────────────────────────────────────────────── */
/* CSI-2 Constants                                                             */
/* ─────────────────────────────────────────────────────────────────────────── */
#define CSI2_MAX_LANES              4U
#define CSI2_MAX_VIRTUAL_CHANNELS   4U
#define CSI2_MAX_DATA_TYPES         8U
#define CSI2_FRAME_BUFFER_POOL_SIZE 4U  /**< Minimum 3 for triple-buffering */

/** @brief CSI-2 Data Type codes (MIPI CSI-2 v3.0 Table 11). */
#define CSI2_DT_FRAME_START     0x00U
#define CSI2_DT_FRAME_END       0x01U
#define CSI2_DT_LINE_START      0x02U
#define CSI2_DT_LINE_END        0x03U
#define CSI2_DT_GENERIC_SHORT1  0x08U
#define CSI2_DT_YUV420_8BIT     0x18U
#define CSI2_DT_YUV422_8BIT     0x1EU
#define CSI2_DT_RGB888          0x24U
#define CSI2_DT_RAW8            0x2AU
#define CSI2_DT_RAW10           0x2BU
#define CSI2_DT_RAW12           0x2CU
#define CSI2_DT_RAW14           0x2DU
#define CSI2_DT_RAW16           0x2EU
#define CSI2_DT_EMBEDDED        0x12U

/* ─────────────────────────────────────────────────────────────────────────── */
/* Types                                                                       */
/* ─────────────────────────────────────────────────────────────────────────── */

typedef enum {
    CSI2_PHY_DPHY = 0,
    CSI2_PHY_CPHY,
} csi2_phy_type_t;

typedef enum {
    CSI2_CLK_CONTINUOUS = 0,
    CSI2_CLK_NON_CONTINUOUS,
} csi2_clock_mode_t;

/** @brief Frame buffer descriptor — must be cache-line aligned. */
typedef struct ISF_ALIGNED(HAL_DMA_CACHE_LINE_BYTES) {
    void               *data;           /**< Virtual address of frame data */
    u64                 phys_addr;      /**< Physical address for DMA */
    u32                 capacity_bytes;
    u32                 used_bytes;     /**< Filled by driver when frame complete */
    u32                 width;
    u32                 height;
    u8                  pixel_format;   /**< CSI2_DT_xxx */
    u8                  virtual_channel;
    u32                 sequence;       /**< Monotonically increasing frame counter */
    isf_timestamp_us_t  timestamp_us;  /**< Hardware timestamp at frame-start SOF */
    bool                valid;
    u16                 ecc_errors;
    u16                 crc_errors;
} csi2_frame_buffer_t;

/** @brief CSI-2 receiver hardware configuration. */
typedef struct {
    u8              num_lanes;
    u32             data_rate_mbps;     /**< Per-lane data rate */
    csi2_phy_type_t phy_type;
    csi2_clock_mode_t clock_mode;
    bool            embedded_data_enable;   /**< Capture embedded metadata lines */
    u8              active_virtual_channels; /**< Bitmask: bit0=VC0 … bit3=VC3 */

    /** @brief Frame buffer pool — must be pre-allocated by caller.
     *  Pool size >= 3 for zero-copy double/triple buffering. */
    csi2_frame_buffer_t *frame_pool;
    u8                   frame_pool_size;

    /** @brief Frame completion callback (ISR context — keep it short). */
    void (*frame_ready_cb)(csi2_frame_buffer_t *frame, void *ctx);
    void *frame_ready_ctx;

    /** @brief Error callback. */
    void (*error_cb)(u32 error_flags, void *ctx);
    void *error_ctx;

    reg_addr_t  base_addr;  /**< CSI-2 controller MMIO base */
    u8          dma_channel;
} csi2_config_t;

/** @brief CSI-2 error flags (reported via error_cb). */
typedef enum {
    CSI2_ERR_SOT_LEADER     = ISF_BIT(0),
    CSI2_ERR_SOT_SYNC       = ISF_BIT(1),
    CSI2_ERR_ECC_SINGLE     = ISF_BIT(2),  /**< Corrected — data valid */
    CSI2_ERR_ECC_DOUBLE     = ISF_BIT(3),  /**< Uncorrectable — data invalid */
    CSI2_ERR_CRC            = ISF_BIT(4),
    CSI2_ERR_DATA_OVERFLOW  = ISF_BIT(5),
    CSI2_ERR_LINE_LEN       = ISF_BIT(6),
    CSI2_ERR_LINE_COUNT     = ISF_BIT(7),
    CSI2_ERR_FIFO_OVERFLOW  = ISF_BIT(8),
} csi2_error_flag_t;

/** @brief Opaque CSI-2 handle. */
typedef struct csi2_context_s *csi2_handle_t;

/** @brief Run-time statistics. */
typedef struct {
    u64 frames_captured;
    u64 frames_dropped;
    u32 ecc_single_errors;
    u32 ecc_double_errors;
    u32 crc_errors;
    u32 sot_errors;
    u32 fifo_overflows;
    u32 line_length_errors;
    u64 bytes_received;
    u32 current_fps_x10;
} csi2_stats_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* API                                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */

/**
 * @brief   Initialise CSI-2 receiver.
 * @note    Configures D-PHY PLL, lane timing, FIFO depths, and DMA descriptors.
 *          Does NOT start frame capture — call csi2_start() after sensor stream begins.
 */
isf_status_t csi2_init(const csi2_config_t *config, csi2_handle_t *out_handle);

/**
 * @brief   Apply new configuration without full re-initialisation.
 *          CSI-2 must be stopped before calling.
 */
isf_status_t csi2_reconfigure(csi2_handle_t handle, const csi2_config_t *config);

/** @brief Enable frame capture (start accepting lanes from sensor). */
isf_status_t csi2_start(csi2_handle_t handle);

/** @brief Disable frame capture (gracefully wait for current frame to complete). */
isf_status_t csi2_stop(csi2_handle_t handle);

/**
 * @brief   Dequeue the next completed frame buffer (blocking).
 * @param   timeout_ms   0 = poll, UINT32_MAX = block indefinitely.
 * @return  ISF_OK and sets *out_frame, or ISF_ERR_TIMEOUT.
 */
isf_status_t csi2_dequeue_frame(csi2_handle_t handle,
                                 csi2_frame_buffer_t **out_frame,
                                 u32 timeout_ms);

/**
 * @brief   Return a frame buffer to the free pool after the application is done.
 * @note    Must be called for every frame obtained via dequeue or callback to
 *          avoid buffer starvation.
 */
isf_status_t csi2_return_frame(csi2_handle_t handle, csi2_frame_buffer_t *frame);

/** @brief Read current statistics. */
isf_status_t csi2_get_stats(csi2_handle_t handle, csi2_stats_t *out_stats);

/** @brief Reset all counters. */
isf_status_t csi2_reset_stats(csi2_handle_t handle);

/** @brief DPHY PLL calibration — call at startup and after temperature change > 15°C. */
isf_status_t csi2_calibrate_phy(csi2_handle_t handle);

/**
 * @brief   Set D-PHY lane settling time (HS-SETTLE override).
 *          Default is auto-calculated from data rate; override if needed.
 */
isf_status_t csi2_set_settle_time_ns(csi2_handle_t handle, u16 settle_ns);

/** @brief De-initialise and release all resources. */
isf_status_t csi2_deinit(csi2_handle_t handle);

/** @brief Dump MIPI CSI-2 status registers to the debug logger. */
void csi2_dump_registers(csi2_handle_t handle);

#endif /* MIPI_CSI2_H */
