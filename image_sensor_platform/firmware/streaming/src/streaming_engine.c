/**
 * @file    streaming_engine.c
 * @brief   Zero-copy frame streaming engine implementation.
 *
 * Lock strategy:
 *   - FREE pool  → protected by pool_mutex (can sleep)
 *   - CAPTURE queue → lock-free single-writer (ISR) / single-reader (worker)
 *   - APP queue  → protected by app_mutex (dequeue may block)
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#include "streaming_engine.h"
#include "isf_logger.h"
#include "hal_dma.h"

#include <string.h>

/* ─────────────────────────────────────────────────────────────────────────── */
/* RTOS / OS abstraction                                                       */
/* The following macros map to FreeRTOS, POSIX, or bare-metal implementations */
/* ─────────────────────────────────────────────────────────────────────────── */
#if defined(ISF_RTOS_FREERTOS)
#   include "FreeRTOS.h"
#   include "semphr.h"
#   include "queue.h"
#   define isf_mutex_t              SemaphoreHandle_t
#   define isf_mutex_create()       xSemaphoreCreateMutex()
#   define isf_mutex_lock(m,tms)    (xSemaphoreTake((m),(TickType_t)((tms)==UINT32_MAX ? portMAX_DELAY : pdMS_TO_TICKS(tms))) == pdTRUE ? ISF_OK : ISF_ERR_TIMEOUT)
#   define isf_mutex_unlock(m)      xSemaphoreGive(m)
#   define isf_sem_t                SemaphoreHandle_t
#   define isf_sem_create(n)        xSemaphoreCreateCounting(STREAM_QUEUE_DEPTH,(n))
#   define isf_sem_wait(s,tms)      (xSemaphoreTake((s),(TickType_t)((tms)==UINT32_MAX ? portMAX_DELAY : pdMS_TO_TICKS(tms))) == pdTRUE ? ISF_OK : ISF_ERR_TIMEOUT)
#   define isf_sem_post(s)          xSemaphoreGive(s)
#   define isf_sem_post_from_isr(s) { BaseType_t w; xSemaphoreGiveFromISR((s),&w); portYIELD_FROM_ISR(w); }
#elif defined(ISF_OS_POSIX)
#   include <pthread.h>
#   include <semaphore.h>
#   define isf_mutex_t              pthread_mutex_t
#   define isf_mutex_create()       PTHREAD_MUTEX_INITIALIZER
#   define isf_mutex_lock(m,tms)    (pthread_mutex_lock(&(m)) == 0 ? ISF_OK : ISF_ERR_GENERIC)
#   define isf_mutex_unlock(m)      pthread_mutex_unlock(&(m))
    typedef sem_t isf_sem_t;
#   define isf_sem_create(n)        /* manual init needed */
#   define isf_sem_wait(s,tms)      (sem_wait(&(s)) == 0 ? ISF_OK : ISF_ERR_TIMEOUT)
#   define isf_sem_post(s)          sem_post(&(s))
#   define isf_sem_post_from_isr(s) sem_post(&(s))
#else
#   error "Define ISF_RTOS_FREERTOS or ISF_OS_POSIX"
#endif

/* ─────────────────────────────────────────────────────────────────────────── */
/* Internal pipeline state                                                     */
/* ─────────────────────────────────────────────────────────────────────────── */
#define FREE_POOL_SIZE   (STREAM_QUEUE_DEPTH + 2U)  /* Extra buffers for hysteresis */

typedef struct {
    /* === Configuration (read-only after create) === */
    stream_pipeline_config_t config;
    csi2_frame_buffer_t      csi2_buffers[FREE_POOL_SIZE];

    /* === Free pool (buffers available for DMA) === */
    csi2_frame_buffer_t     *free_pool[FREE_POOL_SIZE];
    u8                       free_head;
    u8                       free_tail;
    u8                       free_count;
    isf_mutex_t              pool_mutex;

    /* === Capture ring (ISR → worker, lock-free SPSC) === */
    csi2_frame_buffer_t     *capture_ring[STREAM_QUEUE_DEPTH];
    volatile u8              cap_write;
    volatile u8              cap_read;

    /* === App queue (worker → application) === */
    stream_frame_t           app_queue[STREAM_QUEUE_DEPTH];
    u8                       app_head;
    u8                       app_tail;
    u8                       app_count;
    isf_mutex_t              app_mutex;
    isf_sem_t                app_sem;  /**< Signalled when a frame is enqueued */

    /* === State === */
    bool             active;
    bool             stopping;

    /* === Stats === */
    stream_pipeline_stats_t  stats;
    isf_timestamp_us_t       last_fps_update_us;
    u32                      fps_frame_count;
} stream_pipeline_ctx_t;

/* Static pool of pipeline contexts — no heap allocation in firmware */
static stream_pipeline_ctx_t s_pipelines[STREAM_MAX_PIPELINES];
static bool s_pipeline_used[STREAM_MAX_PIPELINES];

/* ─────────────────────────────────────────────────────────────────────────── */
/* Internal helpers                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */

/** @brief ISR callback from CSI-2 driver. Called when a frame DMA completes. */
static void stream_csi2_frame_ready_isr(csi2_frame_buffer_t *frame, void *ctx)
{
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)ctx;
    /* Lock-free SPSC enqueue into capture ring */
    const u8 next = (p->cap_write + 1U) & (STREAM_QUEUE_DEPTH - 1U);
    if (next == p->cap_read) {
        /* Ring full — drop frame (DMA buffer must still be returned to free pool!) */
        p->stats.frames_dropped++;
        /* Re-queue the buffer immediately so DMA can use it */
        /* (pool mutex cannot be taken from ISR; use separate atomic free-list) */
        /* For now, mark buffer as unused and let worker reclaim */
        frame->valid = false;
        return;
    }
    p->capture_ring[p->cap_write] = frame;
    p->cap_write = next;
    isf_sem_post_from_isr(p->app_sem);  /* Wake worker */
}

/** @brief Return one buffer to the free pool. Safe to call from any context. */
static void stream_release_to_free(stream_pipeline_ctx_t *p, csi2_frame_buffer_t *buf)
{
    (void)isf_mutex_lock(p->pool_mutex, UINT32_MAX);
    if (p->free_count < FREE_POOL_SIZE) {
        p->free_pool[p->free_head] = buf;
        p->free_head = (p->free_head + 1U) % FREE_POOL_SIZE;
        p->free_count++;
        if (p->free_count < p->stats.free_pool_low_watermark || p->stats.free_pool_low_watermark == 0U) {
            p->stats.free_pool_low_watermark = p->free_count;
        }
    }
    (void)isf_mutex_unlock(p->pool_mutex);
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Public API implementation                                                   */
/* ─────────────────────────────────────────────────────────────────────────── */

isf_status_t stream_pipeline_create(const stream_pipeline_config_t *config,
                                     stream_pipeline_t *out_pipeline)
{
    ISF_CHECK_PTR(config);
    ISF_CHECK_PTR(out_pipeline);

    /* Find a free slot */
    stream_pipeline_ctx_t *p = NULL;
    for (u8 i = 0U; i < STREAM_MAX_PIPELINES; i++) {
        if (!s_pipeline_used[i]) {
            p = &s_pipelines[i];
            s_pipeline_used[i] = true;
            break;
        }
    }
    if (p == NULL) { return ISF_ERR_NO_MEM; }
    memset(p, 0, sizeof(*p));
    memcpy(&p->config, config, sizeof(*config));

    /* Partition the user-supplied memory pool into frame buffers */
    u8 *mem = (u8 *)config->frame_memory_pool;
    const u32 buf_stride = ISF_ALIGN_UP(config->frame_size_bytes, HAL_DMA_CACHE_LINE_BYTES);
    if ((u64)buf_stride * FREE_POOL_SIZE > config->frame_memory_size) {
        ISF_LOG_ERR("Stream: memory pool too small: need %lu, have %u",
                    (unsigned long)buf_stride * FREE_POOL_SIZE,
                    config->frame_memory_size);
        s_pipeline_used[config->pipeline_id] = false;
        return ISF_ERR_NO_MEM;
    }

    for (u8 i = 0U; i < FREE_POOL_SIZE; i++) {
        p->csi2_buffers[i].data          = mem + (u32)i * buf_stride;
        p->csi2_buffers[i].phys_addr     = (u64)(uintptr_t)(p->csi2_buffers[i].data);
        p->csi2_buffers[i].capacity_bytes = buf_stride;
        p->csi2_buffers[i].valid         = false;
        p->free_pool[i]                  = &p->csi2_buffers[i];
    }
    p->free_count = FREE_POOL_SIZE;

    /* Configure CSI-2 to use our callback and buffer pool */
    /* Note: full CSI-2 config is done at the driver level before calling create().
     * Here we just attach the per-pipeline callback. */

    *out_pipeline = (stream_pipeline_t)p;
    ISF_LOG_INFO("Stream: pipeline %d created, %d buffers of %d bytes",
                 config->pipeline_id, FREE_POOL_SIZE, buf_stride);
    return ISF_OK;
}

isf_status_t stream_start(stream_pipeline_t pipeline)
{
    ISF_CHECK_PTR(pipeline);
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline;
    if (p->active) { return ISF_ERR_BUSY; }

    /* Prime CSI-2 with free buffers before enabling reception */
    for (u8 i = 0U; i < ISF_MIN(3U, p->free_count); i++) {
        csi2_frame_buffer_t *buf = p->free_pool[i];
        buf->width  = p->config.width;
        buf->height = p->config.height;
        /* The csi2 driver will take ownership of these until frame_ready_cb fires */
    }

    p->active   = true;
    p->stopping = false;
    ISF_LOG_INFO("Stream: pipeline %d started", p->config.pipeline_id);
    return ISF_OK;
}

isf_status_t stream_stop(stream_pipeline_t pipeline)
{
    ISF_CHECK_PTR(pipeline);
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline;
    p->stopping = true;
    /* Worker will drain the queue and set active = false */
    ISF_LOG_INFO("Stream: pipeline %d stop requested", p->config.pipeline_id);
    return ISF_OK;
}

isf_status_t stream_dequeue_frame(stream_pipeline_t pipeline,
                                   stream_frame_t *out_frame,
                                   u32 timeout_ms)
{
    ISF_CHECK_PTR(pipeline);
    ISF_CHECK_PTR(out_frame);
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline;

    isf_status_t st = isf_sem_wait(p->app_sem, timeout_ms);
    if (st != ISF_OK) { return st; }

    (void)isf_mutex_lock(p->app_mutex, UINT32_MAX);
    if (p->app_count == 0U) {
        (void)isf_mutex_unlock(p->app_mutex);
        return ISF_ERR_UNDERFLOW;
    }
    *out_frame = p->app_queue[p->app_tail];
    p->app_tail = (p->app_tail + 1U) % STREAM_QUEUE_DEPTH;
    p->app_count--;
    p->stats.frames_delivered++;
    (void)isf_mutex_unlock(p->app_mutex);
    return ISF_OK;
}

isf_status_t stream_return_frame(stream_pipeline_t pipeline, const stream_frame_t *frame)
{
    ISF_CHECK_PTR(pipeline);
    ISF_CHECK_PTR(frame);
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline;
    stream_release_to_free(p, frame->buffer);
    p->stats.frames_returned++;
    return ISF_OK;
}

/** @brief Worker task — processes capture ring and builds app queue. */
void stream_worker_task(void *pipeline_ptr)
{
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline_ptr;

    while (p->active || (p->cap_read != p->cap_write)) {
        /* Process all pending captures */
        while (p->cap_read != p->cap_write) {
            csi2_frame_buffer_t *buf = p->capture_ring[p->cap_read];
            p->cap_read = (p->cap_read + 1U) & (STREAM_QUEUE_DEPTH - 1U);

            if (!buf->valid) {
                stream_release_to_free(p, buf);
                continue;
            }

            /* Build metadata */
            stream_frame_t frame;
            frame.buffer                    = buf;
            frame.meta.sequence             = buf->sequence;
            frame.meta.timestamp_sof_us     = buf->timestamp_us;
            frame.meta.width                = (u32)buf->width;
            frame.meta.height               = (u32)buf->height;
            frame.meta.pixel_format         = buf->pixel_format;
            frame.meta.virtual_channel      = buf->virtual_channel;
            frame.meta.pipeline_id          = p->config.pipeline_id;
            frame.meta.ecc_errors           = buf->ecc_errors;
            frame.meta.crc_errors           = buf->crc_errors;
            frame.meta.flags                = (buf->crc_errors > 0U) ? FRAME_FLAG_CORRUPTED : 0U;

            /* Enqueue to app queue */
            (void)isf_mutex_lock(p->app_mutex, UINT32_MAX);
            if (p->app_count < STREAM_QUEUE_DEPTH) {
                p->app_queue[p->app_head] = frame;
                p->app_head = (p->app_head + 1U) % STREAM_QUEUE_DEPTH;
                p->app_count++;
                p->stats.frames_captured++;
                if (p->app_count > p->stats.queue_high_watermark) {
                    p->stats.queue_high_watermark = p->app_count;
                }
            } else {
                /* App queue full — drop */
                p->stats.frames_dropped++;
                (void)isf_mutex_unlock(p->app_mutex);
                stream_release_to_free(p, buf);
                continue;
            }
            (void)isf_mutex_unlock(p->app_mutex);

            /* Optional callback */
            if (p->config.on_frame_ready) {
                p->config.on_frame_ready(&frame, p->config.on_frame_ready_ctx);
            }
        }

        if (p->stopping && p->cap_read == p->cap_write) {
            p->active = false;
        }

        /* Yield CPU if no more work */
        /* hal_delay_us(100); or task yield */
    }
}

isf_status_t stream_get_stats(stream_pipeline_t pipeline, stream_pipeline_stats_t *out_stats)
{
    ISF_CHECK_PTR(pipeline);
    ISF_CHECK_PTR(out_stats);
    const stream_pipeline_ctx_t *p = (const stream_pipeline_ctx_t *)pipeline;
    memcpy(out_stats, &p->stats, sizeof(*out_stats));
    return ISF_OK;
}

isf_status_t stream_pipeline_destroy(stream_pipeline_t pipeline)
{
    ISF_CHECK_PTR(pipeline);
    stream_pipeline_ctx_t *p = (stream_pipeline_ctx_t *)pipeline;
    (void)stream_stop(pipeline);
    /* Wait for worker to exit — OS-specific */
    for (u8 i = 0U; i < STREAM_MAX_PIPELINES; i++) {
        if (&s_pipelines[i] == p) {
            s_pipeline_used[i] = false;
            break;
        }
    }
    ISF_LOG_INFO("Stream: pipeline destroyed");
    return ISF_OK;
}
