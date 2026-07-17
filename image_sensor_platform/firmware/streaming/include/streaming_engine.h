/**
 * @file    streaming_engine.h
 * @brief   Zero-copy frame streaming engine with triple-buffering and pipeline monitoring.
 *
 * Pipeline:
 *
 *   [CSI-2 DMA] → [Free Queue] → [Capture Queue] → [App Queue] → [Return Queue]
 *                                     ↕
 *                              [Frame Metadata Attachment]
 *                                     ↕
 *                              [Drop Detection / Stats]
 *
 * Buffer ownership rules (MUST be followed to guarantee zero-copy):
 *   1. DMA controller fills buffers from the FREE pool.
 *   2. On frame complete, buffer moves to CAPTURE queue (ISR context).
 *   3. Streaming task moves it to APP queue with metadata attached.
 *   4. Application calls stream_dequeue_frame().
 *   5. Application calls stream_return_frame() when done → returns to FREE pool.
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef STREAMING_ENGINE_H
#define STREAMING_ENGINE_H

#include "platform_types.h"
#include "mipi_csi2.h"

/* ─────────────────────────────────────────────────────────────────────────── */
/* Constants                                                                   */
/* ─────────────────────────────────────────────────────────────────────────── */
#define STREAM_MAX_PIPELINES        4U
#define STREAM_QUEUE_DEPTH          8U
#define STREAM_MAX_METADATA_BYTES   256U

/* ─────────────────────────────────────────────────────────────────────────── */
/* Frame metadata (attached at capture time, transmitted alongside image data) */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct ISF_PACKED {
    u32                 sequence;          /**< Frame sequence number (from CSI-2) */
    isf_timestamp_us_t  timestamp_sof_us;  /**< Start-of-Frame hardware timestamp */
    isf_timestamp_us_t  timestamp_eof_us;  /**< End-of-Frame hardware timestamp */
    isf_timestamp_us_t  timestamp_host_us; /**< Enqueue time on host */
    u32                 width;
    u32                 height;
    u8                  pixel_format;
    u8                  virtual_channel;
    u16                 exposure_us;
    u16                 gain_x100;
    s16                 temperature_c_x10;
    u8                  pipeline_id;
    u8                  flags;             /**< Bitmask: FRAME_FLAG_DROPPED, etc. */
    u16                 ecc_errors;
    u16                 crc_errors;
    u8                  _pad[2];
} frame_metadata_t;

ISF_STATIC_ASSERT(sizeof(frame_metadata_t) == 52U, "frame_metadata_t must be 52 bytes");

#define FRAME_FLAG_DROPPED   0x01U
#define FRAME_FLAG_CORRUPTED 0x02U
#define FRAME_FLAG_FIRST     0x04U
#define FRAME_FLAG_TEST_PAT  0x08U

/** @brief Complete application-visible frame (image + metadata). */
typedef struct {
    csi2_frame_buffer_t *buffer;    /**< Image data (zero-copy — do not modify) */
    frame_metadata_t     meta;
} stream_frame_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Pipeline statistics                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct {
    u64 frames_captured;
    u64 frames_dropped;
    u64 frames_delivered;
    u64 frames_returned;
    u32 queue_high_watermark;   /**< Max simultaneous frames in APP queue */
    u32 free_pool_low_watermark;
    u32 buffer_starvation_count;
    u64 bytes_streamed;
    u32 avg_latency_us;         /**< Average SOF → dequeue latency */
    u32 max_latency_us;
    u32 current_fps_x10;
} stream_pipeline_stats_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Configuration                                                               */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct {
    u8                   pipeline_id;
    csi2_handle_t        csi2_handle;
    u32                  width;
    u32                  height;
    u8                   pixel_format;
    u8                   virtual_channel;
    u32                  frame_size_bytes;  /**< width × height × bpp/8, aligned */

    /** @brief Memory pool for frame data. Caller allocates; engine manages. */
    void                *frame_memory_pool;
    u32                  frame_memory_size;

    /** @brief Frame-ready callback (optional, called from worker task context). */
    void (*on_frame_ready)(const stream_frame_t *frame, void *ctx);
    void *on_frame_ready_ctx;

    /** @brief Drop callback. */
    void (*on_frame_drop)(u32 sequence, void *ctx);
    void *on_frame_drop_ctx;
} stream_pipeline_config_t;

/** @brief Opaque pipeline handle. */
typedef struct stream_pipeline_s *stream_pipeline_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* API                                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */

/**
 * @brief   Create and initialise a streaming pipeline.
 * @note    Allocates buffer descriptors from frame_memory_pool.
 *          Minimum pool size = frame_size_bytes × (STREAM_QUEUE_DEPTH + 1).
 */
isf_status_t stream_pipeline_create(const stream_pipeline_config_t *config,
                                     stream_pipeline_t *out_pipeline);

/** @brief Destroy pipeline and return all memory to caller. */
isf_status_t stream_pipeline_destroy(stream_pipeline_t pipeline);

/** @brief Start streaming (enables CSI-2 DMA and begins frame capture). */
isf_status_t stream_start(stream_pipeline_t pipeline);

/** @brief Stop streaming gracefully (drains in-flight frames). */
isf_status_t stream_stop(stream_pipeline_t pipeline);

/**
 * @brief   Dequeue next available frame from the APP queue.
 * @param   timeout_ms  0 = non-blocking poll; UINT32_MAX = block forever.
 * @return  ISF_OK with frame, ISF_ERR_TIMEOUT, or ISF_ERR_GENERIC on pipeline error.
 * @note    Caller MUST call stream_return_frame() when done with the frame.
 */
isf_status_t stream_dequeue_frame(stream_pipeline_t pipeline,
                                   stream_frame_t *out_frame,
                                   u32 timeout_ms);

/**
 * @brief   Return a frame buffer to the free pool.
 * @note    MUST be called for every successfully dequeued frame.
 *          Failure to return frames causes buffer starvation and drops.
 */
isf_status_t stream_return_frame(stream_pipeline_t pipeline,
                                  const stream_frame_t *frame);

/** @brief Read pipeline statistics. */
isf_status_t stream_get_stats(stream_pipeline_t pipeline,
                               stream_pipeline_stats_t *out_stats);

/** @brief Reset statistics counters. */
isf_status_t stream_reset_stats(stream_pipeline_t pipeline);

/** @brief Flush all queued frames back to the free pool. */
isf_status_t stream_flush(stream_pipeline_t pipeline);

/**
 * @brief   Worker task entry point.
 *          For RTOS: run this function in a dedicated task at high priority.
 *          For Linux: maps to a kernel thread or IRQ-bottom-half.
 */
void stream_worker_task(void *pipeline_ptr);

#endif /* STREAMING_ENGINE_H */
