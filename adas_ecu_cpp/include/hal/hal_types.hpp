/**
 * @file    hal_types.hpp
 * @brief   Base embedded type definitions — replaces stdlib for bare-metal targets.
 *          On simulation build (Linux/macOS) these map to standard types.
 *
 * In real embedded firmware, stdint.h is provided by the ARM GCC toolchain.
 * These typedefs are the ONLY integer types used throughout the ADAS ECU codebase —
 * never use raw int/long/float in automotive embedded code.
 */

#pragma once

// ── Integer types ──────────────────────────────────────────────────────────────
#include <cstdint>          // uint8_t, int16_t, uint32_t, etc.
#include <cstddef>          // size_t, nullptr_t
#include <cstring>          // memset, memcpy (used in CAN frame struct initialisation)
#include <cassert>

// ── Embedded-safe boolean ─────────────────────────────────────────────────────
using bool_t  = bool;

// ── Status / return codes used across all modules ────────────────────────────
enum class Status : uint8_t {
    OK              = 0x00,
    ERROR           = 0x01,
    TIMEOUT         = 0x02,
    INVALID_PARAM   = 0x03,
    NOT_READY       = 0x04,
    OVERFLOW        = 0x05,
    FAULT           = 0xFF,
};

// ── ECU run mode ──────────────────────────────────────────────────────────────
enum class EcuMode : uint8_t {
    BOOT            = 0x00,
    INITIALISING    = 0x01,
    NORMAL          = 0x02,
    DEGRADED        = 0x03,     // ≥1 feature disabled due to fault
    LIMP_HOME       = 0x04,     // Basic vehicle ops only
    SLEEP           = 0x05,
    FAULT           = 0xFF,
};

// ── Tick type  (1 tick = 1ms, 32-bit wraps every ~49 days) ───────────────────
using TickType_t = uint32_t;

// ── Compile-time helpers ──────────────────────────────────────────────────────
#define ARRAY_SIZE(arr)     (sizeof(arr) / sizeof((arr)[0]))
#define BIT(n)              (1u << (n))
#define UNUSED(x)           (static_cast<void>(x))

// ── Memory qualifiers — map to real qualifiers on embedded target ─────────────
#ifdef EMBEDDED_TARGET
    #define FLASH_CONST     __attribute__((section(".rodata"))) const
    #define RAM_FUNC        __attribute__((section(".ramfunc")))
    #define PACKED          __attribute__((packed))
#else
    #define FLASH_CONST     const
    #define RAM_FUNC
    #define PACKED
#endif

// ── Physical unit aliases (for readability) ───────────────────────────────────
using Millimetres_t     = int32_t;
using Centimetres_t     = int16_t;
using Metres_t          = float;
using Kph_t             = float;       // km/h
using Mps_t             = float;       // m/s
using Nm_t              = float;       // Newton-metres (torque)
using Percent_t         = float;       // 0.0–100.0
using Degrees_t         = float;
using Millivolts_t      = int32_t;
using Milliamps_t       = int32_t;
