/**
 * @file    hal_dma.h
 * @brief   DMA controller HAL — zero-copy frame transfers.
 *
 * Supports:
 *   - Memory-to-memory, peripheral-to-memory, memory-to-peripheral
 *   - Scatter-gather (chained descriptors) for multi-plane frames
 *   - Double-buffering for continuous streaming
 *   - Cache coherency management (invalidate/clean before/after transfer)
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef HAL_DMA_H
#define HAL_DMA_H

#include "platform_types.h"

/* ─────────────────────────────────────────────────────────────────────────── */
/* Constants                                                                   */
/* ─────────────────────────────────────────────────────────────────────────── */
#define HAL_DMA_MAX_CHANNELS        16U
#define HAL_DMA_MAX_SG_DESCRIPTORS  64U
#define HAL_DMA_CACHE_LINE_BYTES    64U

/* ─────────────────────────────────────────────────────────────────────────── */
/* Types                                                                       */
/* ─────────────────────────────────────────────────────────────────────────── */

typedef enum {
    HAL_DMA_DIR_MEM_TO_MEM = 0,
    HAL_DMA_DIR_PERIPH_TO_MEM,
    HAL_DMA_DIR_MEM_TO_PERIPH,
} hal_dma_direction_t;

typedef enum {
    HAL_DMA_WIDTH_8BIT  = 0,
    HAL_DMA_WIDTH_16BIT = 1,
    HAL_DMA_WIDTH_32BIT = 2,
    HAL_DMA_WIDTH_64BIT = 3,
} hal_dma_width_t;

typedef enum {
    HAL_DMA_BURST_1  = 0,
    HAL_DMA_BURST_4  = 1,
    HAL_DMA_BURST_8  = 2,
    HAL_DMA_BURST_16 = 3,
} hal_dma_burst_t;

/** @brief Scatter-gather descriptor — maps to HW descriptor layout. */
typedef struct ISF_PACKED ISF_ALIGNED(HAL_DMA_CACHE_LINE_BYTES) {
    u64 src_addr;
    u64 dst_addr;
    u32 byte_count;
    u32 ctrl;       /**< HW-specific control bits */
    u64 next_desc;  /**< Physical address of next descriptor or 0 for last */
} hal_dma_descriptor_t;

/** @brief DMA channel handle. */
typedef struct hal_dma_channel_s *hal_dma_channel_t;

/** @brief Completion callback invoked from ISR context. */
typedef void (*hal_dma_complete_cb_t)(hal_dma_channel_t ch, isf_status_t status, void *user_ctx);

/** @brief DMA channel configuration. */
typedef struct {
    u8                  channel_index;
    hal_dma_direction_t direction;
    hal_dma_width_t     data_width;
    hal_dma_burst_t     burst_size;
    bool                circular_mode;      /**< Auto-reload descriptor on completion */
    bool                double_buffer;      /**< Ping-pong between two destination buffers */
    u32                 priority;           /**< 0 = low, 3 = very high */
    hal_dma_complete_cb_t complete_cb;
    void               *user_ctx;
} hal_dma_config_t;

/** @brief Transfer request for a single contiguous transfer. */
typedef struct {
    void  *src;
    void  *dst;
    u32    byte_count;
} hal_dma_transfer_t;

/** @brief Statistics. */
typedef struct {
    u64 bytes_transferred;
    u32 transfer_count;
    u32 error_count;
    u32 fifo_error_count;
    u32 direct_mode_error_count;
} hal_dma_stats_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* API                                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */

isf_status_t hal_dma_init(const hal_dma_config_t *config, hal_dma_channel_t *out_ch);
isf_status_t hal_dma_deinit(hal_dma_channel_t ch);

/**
 * @brief   Start a simple memory or peripheral DMA transfer.
 * @note    Non-blocking. Completion notified via callback.
 */
isf_status_t hal_dma_start(hal_dma_channel_t ch, const hal_dma_transfer_t *xfer);

/**
 * @brief   Start scatter-gather transfer using pre-built descriptor chain.
 * @param   descriptors  Array of descriptors (must be physically contiguous and cache-aligned).
 * @param   count        Number of descriptors.
 */
isf_status_t hal_dma_start_sg(hal_dma_channel_t ch,
                               hal_dma_descriptor_t *descriptors,
                               u8 count);

/**
 * @brief   Block until transfer completes (or timeout).
 */
isf_status_t hal_dma_wait(hal_dma_channel_t ch, u32 timeout_ms);

/**
 * @brief   Abort an in-progress transfer. Safe to call from any context.
 */
isf_status_t hal_dma_abort(hal_dma_channel_t ch);

/**
 * @brief   Return bytes remaining in current transfer.
 */
u32 hal_dma_get_remaining(hal_dma_channel_t ch);

/**
 * @brief   Flush D-cache lines for a DMA buffer (before starting DMA write from peripheral).
 *          Must be called before starting a P->M transfer so CPU sees fresh data.
 */
void hal_dma_cache_invalidate(void *addr, u32 byte_count);

/**
 * @brief   Clean D-cache lines (before M->P DMA — ensure CPU writes are visible to peripheral).
 */
void hal_dma_cache_clean(const void *addr, u32 byte_count);

isf_status_t hal_dma_get_stats(hal_dma_channel_t ch, hal_dma_stats_t *out_stats);

#endif /* HAL_DMA_H */
