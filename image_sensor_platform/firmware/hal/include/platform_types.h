/**
 * @file    platform_types.h
 * @brief   Fundamental platform-agnostic type definitions for the image sensor firmware.
 *
 * MISRA C:2012 compliant. All types are explicitly sized.
 * No stdlib dependencies — suitable for bare-metal targets.
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 * @standard   MISRA C:2012, CERT C
 */

#ifndef PLATFORM_TYPES_H
#define PLATFORM_TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ─────────────────────────────────────────────────────────────────────────── */
/* Compiler and platform detection                                             */
/* ─────────────────────────────────────────────────────────────────────────── */
#if defined(__ARM_ARCH)
#   define PLATFORM_ARM     1
#   define PLATFORM_ENDIAN_LITTLE 1
#elif defined(__x86_64__) || defined(_M_X64)
#   define PLATFORM_X86_64  1
#   define PLATFORM_ENDIAN_LITTLE 1
#endif

#if defined(__GNUC__) || defined(__clang__)
#   define ISF_PACKED        __attribute__((packed))
#   define ISF_ALIGNED(n)    __attribute__((aligned(n)))
#   define ISF_INLINE        static inline __attribute__((always_inline))
#   define ISF_NORETURN      __attribute__((noreturn))
#   define ISF_WEAK          __attribute__((weak))
#   define ISF_SECTION(s)    __attribute__((section(s)))
#elif defined(_MSC_VER)
#   define ISF_PACKED
#   define ISF_ALIGNED(n)    __declspec(align(n))
#   define ISF_INLINE        static __forceinline
#   define ISF_NORETURN      __declspec(noreturn)
#   define ISF_WEAK
#   define ISF_SECTION(s)
#endif

/* ─────────────────────────────────────────────────────────────────────────── */
/* Explicit-width integer types (already in stdint.h — aliases for clarity)   */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef uint8_t     u8;
typedef uint16_t    u16;
typedef uint32_t    u32;
typedef uint64_t    u64;
typedef int8_t      s8;
typedef int16_t     s16;
typedef int32_t     s32;
typedef int64_t     s64;
typedef float       f32;
typedef double      f64;

/* Register address type — wide enough for 64-bit SoC memory maps */
typedef uint64_t    reg_addr_t;
typedef uint32_t    reg_val_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Return / status codes                                                       */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef enum {
    ISF_OK                  =  0,   /**< Operation succeeded */
    ISF_ERR_GENERIC         = -1,   /**< Unclassified error */
    ISF_ERR_INVALID_ARG     = -2,   /**< Null or out-of-range argument */
    ISF_ERR_NOT_INITIALIZED = -3,   /**< Module not initialised */
    ISF_ERR_TIMEOUT         = -4,   /**< Operation timed out */
    ISF_ERR_BUSY            = -5,   /**< Resource busy */
    ISF_ERR_NO_MEM          = -6,   /**< Memory allocation failure */
    ISF_ERR_NOT_SUPPORTED   = -7,   /**< Feature not supported on this platform */
    ISF_ERR_IO              = -8,   /**< I/O bus error */
    ISF_ERR_CRC             = -9,   /**< CRC / checksum failure */
    ISF_ERR_OVERFLOW        = -10,  /**< Buffer or arithmetic overflow */
    ISF_ERR_UNDERFLOW       = -11,  /**< Buffer underflow */
    ISF_ERR_NOT_FOUND       = -12,  /**< Device or resource not found */
    ISF_ERR_PERMISSION      = -13,  /**< Access permission denied */
    ISF_ERR_RESET_REQUIRED  = -14,  /**< Hardware requires reset */
    ISF_ERR_CALIBRATION     = -15,  /**< Sensor calibration error */
} isf_status_t;

/** @brief Evaluate and return on non-OK status — reduces boilerplate. */
#define ISF_RETURN_IF_ERR(expr)   do { isf_status_t _s = (expr); if (_s != ISF_OK) { return _s; } } while (0)

/** @brief Null-pointer guard. */
#define ISF_CHECK_PTR(p)          do { if ((p) == NULL) { return ISF_ERR_INVALID_ARG; } } while (0)

/* ─────────────────────────────────────────────────────────────────────────── */
/* Bit manipulation macros (MISRA C:2012 Dir 4.9 — use inline functions       */
/* wherever possible; these are compile-time helpers only)                    */
/* ─────────────────────────────────────────────────────────────────────────── */
#define ISF_BIT(n)              (1UL << (n))
#define ISF_BITMASK(msb, lsb)   (((1UL << ((msb) - (lsb) + 1U)) - 1U) << (lsb))
#define ISF_FIELD_GET(reg, msb, lsb) (((reg) >> (lsb)) & ((1UL << ((msb) - (lsb) + 1U)) - 1U))
#define ISF_FIELD_SET(reg, val, msb, lsb) \
    (((reg) & ~ISF_BITMASK(msb, lsb)) | (((val) << (lsb)) & ISF_BITMASK(msb, lsb)))

/* ─────────────────────────────────────────────────────────────────────────── */
/* Memory barrier and volatile access (critical for DMA / MMIO)              */
/* ─────────────────────────────────────────────────────────────────────────── */
#if defined(PLATFORM_ARM)
#   define ISF_DMB()    __asm__ volatile ("dmb sy" ::: "memory")
#   define ISF_DSB()    __asm__ volatile ("dsb sy" ::: "memory")
#   define ISF_ISB()    __asm__ volatile ("isb"    ::: "memory")
#else
#   define ISF_DMB()    __asm__ volatile ("" ::: "memory")
#   define ISF_DSB()    __asm__ volatile ("" ::: "memory")
#   define ISF_ISB()    __asm__ volatile ("" ::: "memory")
#endif

/** @brief Volatile register read — prevents compiler from optimising away. */
ISF_INLINE u32 mmio_read32(reg_addr_t addr) {
    return *((volatile u32 *)(uintptr_t)addr);
}

/** @brief Volatile register write. */
ISF_INLINE void mmio_write32(reg_addr_t addr, u32 val) {
    *((volatile u32 *)(uintptr_t)addr) = val;
    ISF_DSB();
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Utility macros                                                              */
/* ─────────────────────────────────────────────────────────────────────────── */
#define ISF_ARRAY_SIZE(arr)     (sizeof(arr) / sizeof((arr)[0]))
#define ISF_MIN(a, b)           ((a) < (b) ? (a) : (b))
#define ISF_MAX(a, b)           ((a) > (b) ? (a) : (b))
#define ISF_CLAMP(val, lo, hi)  (ISF_MIN(ISF_MAX((val), (lo)), (hi)))
#define ISF_ALIGN_UP(val, align) (((val) + (align) - 1U) & ~((align) - 1U))
#define ISF_UNUSED(x)           ((void)(x))

/** @brief Compile-time assertion — no runtime cost. */
#define ISF_STATIC_ASSERT(cond, msg) _Static_assert(cond, msg)

/* ─────────────────────────────────────────────────────────────────────────── */
/* Timestamp type — monotonic microseconds                                    */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef u64 isf_timestamp_us_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Version structure                                                           */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct {
    u8  major;
    u8  minor;
    u16 patch;
    u32 build;      /**< CI build number */
    char label[16]; /**< e.g. "release", "debug" */
} isf_version_t;

#define ISF_FW_VERSION { .major = 2, .minor = 0, .patch = 0, .build = 0, .label = "release" }

/* ─────────────────────────────────────────────────────────────────────────── */
/* Compile-time size assertions                                                */
/* ─────────────────────────────────────────────────────────────────────────── */
ISF_STATIC_ASSERT(sizeof(u8)  == 1U, "u8 must be 1 byte");
ISF_STATIC_ASSERT(sizeof(u16) == 2U, "u16 must be 2 bytes");
ISF_STATIC_ASSERT(sizeof(u32) == 4U, "u32 must be 4 bytes");
ISF_STATIC_ASSERT(sizeof(u64) == 8U, "u64 must be 8 bytes");

#endif /* PLATFORM_TYPES_H */
