/**
 * @file    isf_logger.h
 * @brief   Structured, zero-heap logging subsystem.
 *
 * Features:
 *   - Compile-time log level filtering (dead code at O2 for disabled levels)
 *   - Binary ring-buffer backend (fast, no printf in ISR paths)
 *   - ASCII sink adapter (UART, SWO, SEGGER RTT)
 *   - Host-side log decoder (Python script reads binary ring via USB/UART)
 *   - Timestamp in microseconds from monotonic clock
 *   - Module ID for per-subsystem filtering
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef ISF_LOGGER_H
#define ISF_LOGGER_H

#include "platform_types.h"
#include <stdarg.h>

/* ─────────────────────────────────────────────────────────────────────────── */
/* Configuration (override via CMake defines)                                  */
/* ─────────────────────────────────────────────────────────────────────────── */
#ifndef ISF_LOG_LEVEL
#   define ISF_LOG_LEVEL  ISF_LOG_LEVEL_DEBUG
#endif

#ifndef ISF_LOG_RING_SIZE_BYTES
#   define ISF_LOG_RING_SIZE_BYTES  (8192U)
#endif

#ifndef ISF_LOG_MAX_MESSAGE_BYTES
#   define ISF_LOG_MAX_MESSAGE_BYTES (128U)
#endif

/* ─────────────────────────────────────────────────────────────────────────── */
/* Log levels                                                                  */
/* ─────────────────────────────────────────────────────────────────────────── */
#define ISF_LOG_LEVEL_TRACE   0
#define ISF_LOG_LEVEL_DEBUG   1
#define ISF_LOG_LEVEL_INFO    2
#define ISF_LOG_LEVEL_WARN    3
#define ISF_LOG_LEVEL_ERROR   4
#define ISF_LOG_LEVEL_FATAL   5
#define ISF_LOG_LEVEL_NONE    6

/* ─────────────────────────────────────────────────────────────────────────── */
/* Module IDs (extend as needed)                                               */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef enum {
    ISF_MOD_HAL       = 0x01,
    ISF_MOD_I2C       = 0x02,
    ISF_MOD_SPI       = 0x03,
    ISF_MOD_DMA       = 0x04,
    ISF_MOD_CSI2      = 0x05,
    ISF_MOD_SENSOR    = 0x06,
    ISF_MOD_STREAM    = 0x07,
    ISF_MOD_DIAG      = 0x08,
    ISF_MOD_BOOT      = 0x09,
    ISF_MOD_APP       = 0x0A,
    ISF_MOD_SYNC      = 0x0B,
} isf_module_id_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Binary log record (fixed-size, cache-friendly)                              */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct ISF_PACKED {
    u64  timestamp_us;
    u32  arg1;
    u32  arg2;
    u16  msg_id;       /**< Pre-registered message ID (for binary mode) */
    u8   level;
    u8   module_id;
} isf_log_record_t;

ISF_STATIC_ASSERT(sizeof(isf_log_record_t) == 20U, "log record must be 20 bytes");

/* ─────────────────────────────────────────────────────────────────────────── */
/* Sink callback type                                                          */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef void (*isf_log_sink_fn_t)(const char *str, u16 len);

/* ─────────────────────────────────────────────────────────────────────────── */
/* API                                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */

/** @brief Initialise the logger. Call before any log macro. */
isf_status_t isf_log_init(isf_log_sink_fn_t ascii_sink);

/** @brief Register a custom output sink (e.g., USB CDC, Ethernet syslog). */
void isf_log_set_sink(isf_log_sink_fn_t sink);

/** @brief Set runtime log level (0 = trace, 5 = fatal). */
void isf_log_set_level(u8 level);

/** @brief Core logging function — do not call directly; use macros below. */
void isf_log_write(u8 level, u8 module, const char *file, u32 line,
                   const char *fmt, ...);

/** @brief Dump the binary ring buffer to the ASCII sink (for post-mortem). */
void isf_log_dump_ring(void);

/* ─────────────────────────────────────────────────────────────────────────── */
/* Convenience macros — compile out below configured level                    */
/* ─────────────────────────────────────────────────────────────────────────── */
#define ISF_LOG_MODULE  ISF_MOD_APP   /* Override per .c file before including */

#if ISF_LOG_LEVEL <= ISF_LOG_LEVEL_TRACE
#   define ISF_LOG_TRACE(fmt, ...) isf_log_write(ISF_LOG_LEVEL_TRACE, ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
#else
#   define ISF_LOG_TRACE(fmt, ...) ((void)0)
#endif

#if ISF_LOG_LEVEL <= ISF_LOG_LEVEL_DEBUG
#   define ISF_LOG_DEBUG(fmt, ...) isf_log_write(ISF_LOG_LEVEL_DEBUG, ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
#else
#   define ISF_LOG_DEBUG(fmt, ...) ((void)0)
#endif

#if ISF_LOG_LEVEL <= ISF_LOG_LEVEL_INFO
#   define ISF_LOG_INFO(fmt, ...)  isf_log_write(ISF_LOG_LEVEL_INFO,  ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
#else
#   define ISF_LOG_INFO(fmt, ...) ((void)0)
#endif

#if ISF_LOG_LEVEL <= ISF_LOG_LEVEL_WARN
#   define ISF_LOG_WARN(fmt, ...)  isf_log_write(ISF_LOG_LEVEL_WARN,  ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
#else
#   define ISF_LOG_WARN(fmt, ...) ((void)0)
#endif

#if ISF_LOG_LEVEL <= ISF_LOG_LEVEL_ERROR
#   define ISF_LOG_ERR(fmt, ...)   isf_log_write(ISF_LOG_LEVEL_ERROR, ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
#else
#   define ISF_LOG_ERR(fmt, ...) ((void)0)
#endif

#define ISF_LOG_FATAL(fmt, ...)    isf_log_write(ISF_LOG_LEVEL_FATAL, ISF_LOG_MODULE, __FILE__, __LINE__, fmt, ##__VA_ARGS__)

/* ─────────────────────────────────────────────────────────────────────────── */
/* Assertion with optional log                                                 */
/* ─────────────────────────────────────────────────────────────────────────── */
#define ISF_ASSERT(cond)   do { if (!(cond)) { ISF_LOG_FATAL("Assertion failed: %s", #cond); while(1){} } } while(0)

#endif /* ISF_LOGGER_H */
