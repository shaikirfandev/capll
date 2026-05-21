/**
 * @file aircraft_config.hpp
 * @brief Compile-time B737-800 aircraft constants — DO-178C DAL-B
 * @req SRS-PERF-010
 */
#pragma once
#include <cstdint>

namespace fms::config {

// ── B737-800 Aircraft Limits ─────────────────────────────────────────────────
inline constexpr float MTOW_KG            = 78016.0f;   ///< Max Take-Off Weight
inline constexpr float MLW_KG             = 66360.0f;   ///< Max Landing Weight
inline constexpr float MZFW_KG            = 62732.0f;   ///< Max Zero Fuel Weight
inline constexpr float MAX_FUEL_KG        = 26020.0f;   ///< Max fuel capacity
inline constexpr float VMO_KT             = 340.0f;     ///< Max Operating Speed
inline constexpr float MMO                = 0.82f;      ///< Max Operating Mach
inline constexpr float CRUISE_MACH        = 0.78f;      ///< Typical cruise Mach
inline constexpr float LONG_RANGE_MACH    = 0.74f;      ///< LRC Mach
inline constexpr float MAX_ALT_FT         = 41000.0f;   ///< Maximum altitude
inline constexpr float CEILING_FT         = 41000.0f;   ///< Service ceiling

// ── Fuel ─────────────────────────────────────────────────────────────────────
inline constexpr float FUEL_FLOW_CRUISE_KGHR = 2400.0f; ///< Per engine cruise
inline constexpr float FUEL_FLOW_CLIMB_KGHR  = 3600.0f; ///< Per engine climb
inline constexpr float FUEL_RESERVE_KG       = 1500.0f; ///< Minimum reserve
inline constexpr float FUEL_IMBALANCE_KG     = 200.0f;  ///< Imbalance warning

// ── Performance ──────────────────────────────────────────────────────────────
inline constexpr float V2_MIN_KT           = 148.0f;    ///< Min V2 (clean, MTOW)
inline constexpr float VAPP_MIN_KT         = 138.0f;    ///< Min VAPP
inline constexpr float VFE_FLAP5_KT        = 230.0f;    ///< Max speed flap 5
inline constexpr float VFE_FLAP30_KT       = 175.0f;    ///< Max speed flap 30
inline constexpr float VS_MAX_FPM          = 3000.0f;   ///< Max vertical speed
inline constexpr float ROLL_LIMIT_DEG      = 25.0f;     ///< Max LNAV bank

// ── Navigation ───────────────────────────────────────────────────────────────
inline constexpr float RNP_EN_ROUTE_NM     = 2.0f;      ///< En-route RNP
inline constexpr float RNP_APPROACH_NM     = 0.1f;      ///< Approach RNP
inline constexpr float RNP_OCEANIC_NM      = 4.0f;      ///< Oceanic RNP
inline constexpr uint8_t MIN_GPS_SATS      = 5U;        ///< RAIM minimum
inline constexpr float MAX_HDOP            = 2.0f;      ///< RAIM HDOP limit

// ── ARINC 429 ────────────────────────────────────────────────────────────────
inline constexpr uint32_t ARINC429_BAUD_LO = 12500U;    ///< Low speed (12.5 kbps)
inline constexpr uint32_t ARINC429_BAUD_HI = 100000U;   ///< High speed (100 kbps)

// ── Safety ───────────────────────────────────────────────────────────────────
inline constexpr uint32_t WATCHDOG_TIMEOUT_MS = 500U;   ///< Watchdog kick interval
inline constexpr uint32_t MAX_FAULT_RECORDS   = 64U;    ///< Static fault table size

}  // namespace fms::config
