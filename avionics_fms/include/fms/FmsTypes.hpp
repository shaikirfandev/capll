/**
 * @file FmsTypes.hpp
 * @brief Core type definitions for the Flight Management System
 *
 * DO-178C DAL-B compliance — all types are statically sized, no dynamic
 * allocation in safety-critical paths.
 *
 * Standards: RTCA DO-178C, ARINC 702A, EUROCAE ED-75D
 * Aircraft: Transport Category (Boeing 737 / Airbus A320 class)
 */
#pragma once

#include <cstdint>
#include <cmath>
#include <array>
#include <string_view>

namespace fms {

// ── Version ────────────────────────────────────────────────────────────────────
static constexpr uint8_t FMS_SW_VERSION_MAJOR = 3U;
static constexpr uint8_t FMS_SW_VERSION_MINOR = 2U;
static constexpr uint8_t FMS_SW_VERSION_PATCH = 1U;

// ── Physical Constants ────────────────────────────────────────────────────────
namespace constants {
    static constexpr double EARTH_RADIUS_M      = 6371000.0;   // WGS-84 mean radius
    static constexpr double EARTH_RADIUS_NM     = 3440.065;    // Nautical miles
    static constexpr double GRAVITY_MS2         = 9.80665;     // Standard gravity
    static constexpr double NM_TO_M             = 1852.0;      // 1 NM in metres
    static constexpr double FT_TO_M             = 0.3048;      // 1 ft in metres
    static constexpr double KT_TO_MS            = 0.514444;    // 1 kt in m/s
    static constexpr double DEG_TO_RAD          = 3.14159265358979323846 / 180.0;
    static constexpr double RAD_TO_DEG          = 180.0 / 3.14159265358979323846;
    static constexpr double ISA_SEA_LEVEL_TEMP  = 288.15;      // K
    static constexpr double ISA_SEA_LEVEL_PRESS = 101325.0;    // Pa
    static constexpr double ISA_LAPSE_RATE      = 0.0065;      // K/m
    static constexpr double SPEED_OF_SOUND_SL   = 340.29;      // m/s at sea level
    static constexpr double PI                  = 3.14159265358979323846;
}

// ── Error Codes ───────────────────────────────────────────────────────────────
enum class FmsError : uint32_t {
    OK                    = 0x0000U,
    ERR_INVALID_PARAM     = 0x0001U,
    ERR_NULL_POINTER      = 0x0002U,
    ERR_BUFFER_OVERFLOW   = 0x0003U,
    ERR_NOT_INITIALISED   = 0x0004U,
    ERR_SENSOR_FAILED     = 0x0010U,
    ERR_GPS_UNAVAILABLE   = 0x0011U,
    ERR_INS_DEGRADED      = 0x0012U,
    ERR_ADC_FAILED        = 0x0013U,
    ERR_NAV_DEGRADED      = 0x0020U,
    ERR_FP_INVALID        = 0x0021U,
    ERR_WAYPOINT_LIMIT    = 0x0022U,
    ERR_PROCEDURE_NOT_FOUND = 0x0023U,
    ERR_COMMS_TIMEOUT     = 0x0030U,
    ERR_ARINC_PARITY      = 0x0031U,
    ERR_CAN_BUS_OFF       = 0x0032U,
    ERR_SAFETY_LIMIT      = 0x0040U,
    ERR_WATCHDOG_TIMEOUT  = 0x0041U,
    ERR_MEMORY_CORRUPTION = 0x0042U,
    ERR_CHECKSUM_FAIL     = 0x0043U,
    ERR_NOT_FOUND         = 0x0050U,
    ERR_BUFFER_FULL       = 0x0051U,
    ERR_FAULT_LATCHED     = 0x0052U,
    ERR_UNKNOWN           = 0xFFFFU,
};

// ── Geographic Position ────────────────────────────────────────────────────────
struct LatLon {
    double lat_deg{0.0};   // Latitude  [-90, +90]  degrees
    double lon_deg{0.0};   // Longitude [-180, +180] degrees
};

struct Position3D {
    double lat_deg{0.0};   // Degrees
    double lon_deg{0.0};   // Degrees
    double alt_ft{0.0};    // Altitude in feet MSL
};

struct Velocity3D {
    double north_ms{0.0};  // North component m/s
    double east_ms{0.0};   // East  component m/s
    double down_ms{0.0};   // Down  component m/s (positive = descending)
};

// ── Attitude ──────────────────────────────────────────────────────────────────
struct Attitude {
    double pitch_deg{0.0};    // Nose-up positive
    double roll_deg{0.0};     // Right wing down positive
    double yaw_deg{0.0};      // True heading [0, 360)
    double track_deg{0.0};    // Track over ground [0, 360)
};

// ── System Health ─────────────────────────────────────────────────────────────
enum class SystemStatus : uint8_t {
    NORMAL      = 0U,
    ADVISORY    = 1U,   // Monitor — no crew action required
    CAUTION     = 2U,   // Abnormal — crew action may be required
    WARNING     = 3U,   // Emergency — immediate crew action required
    FAILED      = 4U,
};

// ── Navigation State ──────────────────────────────────────────────────────────
enum class NavMode : uint8_t {
    INERTIAL   = 0U,   // INS only (DRFIT)
    GPS_AIDED  = 1U,   // GPS/INS blended
    GPS_ONLY   = 2U,   // GPS primary (degraded)
    VOR_DME    = 3U,   // Radio nav
    DEAD_RECK  = 4U,   // Dead reckoning (all sensors failed)
};

struct NavState {
    Position3D position;
    Velocity3D velocity;
    Attitude   attitude;
    NavMode    mode{NavMode::GPS_AIDED};
    double     ground_speed_kt{0.0};
    double     tas_kt{0.0};    // True Airspeed
    double     cas_kt{0.0};    // Calibrated Airspeed
    double     mach{0.0};      // Mach number
    double     wind_dir_deg{0.0};
    double     wind_speed_kt{0.0};
    double     track_angle_error_deg{0.0};  // XTE source
    double     rnp_nm{0.1};    // Required Navigation Performance
    double     anp_nm{0.05};   // Actual Navigation Performance
    uint64_t   timestamp_us{0};
    SystemStatus status{SystemStatus::NORMAL};
};

// ── Waypoint ──────────────────────────────────────────────────────────────────
enum class WaypointType : uint8_t {
    AIRPORT      = 0U,
    VOR          = 1U,
    NDB          = 2U,
    INTERSECTION = 3U,
    USER_DEFINED = 4U,
    RUNWAY       = 5U,
    IAF          = 6U,   // Initial Approach Fix
    FAF          = 7U,   // Final Approach Fix
    MAP          = 8U,   // Missed Approach Point
    TOC          = 9U,   // Top of Climb
    TOD          = 10U,  // Top of Descent
    PSEUDO       = 11U,  // Computed T-P
};

enum class AltitudeConstraint : uint8_t {
    NONE    = 0U,
    AT      = 1U,  // Exactly at
    AT_OR_ABOVE = 2U,
    AT_OR_BELOW = 3U,
    BETWEEN = 4U,
};

enum class SpeedConstraint : uint8_t {
    NONE    = 0U,
    AT      = 1U,
    AT_OR_ABOVE = 2U,
    AT_OR_BELOW = 3U,
};

static constexpr uint8_t IDENT_LEN = 8U;
static constexpr uint8_t MAX_WAYPOINTS = 128U;

struct Waypoint {
    char         ident[IDENT_LEN]{};
    LatLon       position;
    WaypointType type{WaypointType::INTERSECTION};

    double       alt_constraint_ft{0.0};
    double       alt_constraint2_ft{0.0};  // Upper bound for BETWEEN
    AltitudeConstraint alt_type{AltitudeConstraint::NONE};

    double       spd_constraint_kt{0.0};
    SpeedConstraint spd_type{SpeedConstraint::NONE};

    double       mag_variation_deg{0.0};
    double       elevation_ft{0.0};
    uint16_t     frequency_khz{0U};  // VOR/NDB frequency

    // Computed by FMS
    double       dist_to_go_nm{0.0};
    double       ete_sec{0.0};
    double       eta_utc_sec{0.0};
    double       planned_fuel_kg{0.0};
    double       outbound_course_deg{0.0};
};

// ── Flight Plan ───────────────────────────────────────────────────────────────
enum class FlightPlanState : uint8_t {
    EMPTY        = 0U,
    INCOMPLETE   = 1U,
    COMPLETE     = 2U,
    ACTIVE       = 3U,
    MODIFIED     = 4U,  // Temporary revision pending
    ALTERNATE    = 5U,
};

struct FlightPlan {
    char   origin_icao[5]{};      // Departure airport
    char   dest_icao[5]{};        // Destination airport
    char   alt_icao[5]{};         // Alternate airport
    char   callsign[8]{};
    uint8_t wpt_count{0U};
    Waypoint waypoints[MAX_WAYPOINTS]{};
    uint8_t  active_wpt_idx{0U};
    FlightPlanState state{FlightPlanState::EMPTY};

    double total_dist_nm{0.0};
    double total_fuel_kg{0.0};
    double total_time_min{0.0};
    double cost_index{0.0};      // CI: 0=min fuel, 999=min time
    double cruise_alt_ft{35000.0};
    double step_climb_alt_ft{0.0};
};

// ── Performance ───────────────────────────────────────────────────────────────
struct PerformanceData {
    double zfw_kg{0.0};        // Zero Fuel Weight
    double fuel_on_board_kg{0.0};
    double tow_kg{0.0};        // Take-Off Weight
    double mlw_kg{0.0};        // Max Landing Weight
    double mtow_kg{78016.0};   // Boeing 737-800 MTOW
    double cruise_mach{0.78};
    double long_range_mach{0.74};
    double vmo_kt{340.0};      // Max Operating Speed
    double mmo{0.82};          // Max Mach
    double green_dot_kt{200.0}; // Best L/D speed (clean)
    double max_alt_ft{41000.0};
    double opt_cruise_alt_ft{35000.0};
    double fuel_flow_cruise_kghr{2400.0};  // Per engine
    double fuel_flow_climb_kghr{3200.0};
    double specific_range{0.0};  // nm/kg
};

// ── FMS Mode ──────────────────────────────────────────────────────────────────
enum class LnavMode : uint8_t {
    STANDBY  = 0U,
    HDG_SEL  = 1U,   // Heading Select
    TRK_SEL  = 2U,   // Track Select
    LNAV     = 3U,   // FMS Lateral Navigation
    VOR_LOC  = 4U,   // VOR/Localiser tracking
    APPROACH = 5U,
};

enum class VnavMode : uint8_t {
    STANDBY  = 0U,
    ALT_HOLD = 1U,
    ALT_SEL  = 2U,   // Altitude Select (climb/descend to)
    VNAV_PTH = 3U,   // VNAV Path
    VNAV_SPD = 4U,   // VNAV Speed
    GS       = 5U,   // Glideslope
    FPA      = 6U,   // Flight Path Angle
};

struct FmsMode {
    LnavMode lnav{LnavMode::STANDBY};
    VnavMode vnav{VnavMode::STANDBY};
    bool     at_active{false};   // Autothrottle engaged
    bool     ap_engaged{false};  // Autopilot engaged
};

// ── Guidance Outputs ──────────────────────────────────────────────────────────
struct LateralGuidance {
    double  roll_cmd_deg{0.0};    // Commanded roll angle
    double  bank_angle_deg{0.0};  // Actual bank
    double  xte_nm{0.0};          // Cross-track error (positive = right of track)
    double  dtk_deg{0.0};         // Desired track
    double  track_error_deg{0.0}; // Track angle error
    double  turn_rate_dps{0.0};   // Demanded turn rate
    uint8_t next_wpt_idx{0U};
};

struct VerticalGuidance {
    double vs_cmd_fpm{0.0};       // Commanded vertical speed
    double alt_error_ft{0.0};     // Altitude error
    double vnav_path_deg{0.0};    // VNAV path angle
    double target_alt_ft{0.0};    // Target altitude
    double target_spd_kt{0.0};    // Target speed
    double target_mach{0.0};
    double thrust_rating{0.0};   // [0.0, 1.0]
    double vdev_ft{0.0};          // Vertical deviation from path
    bool   in_descent{false};
};

// ── Fuel State ────────────────────────────────────────────────────────────────
struct FuelState {
    double  total_fuel_kg{0.0};
    double  left_wing_kg{0.0};
    double  right_wing_kg{0.0};
    double  centre_tank_kg{0.0};
    double  fuel_flow_kghr{0.0};   // Total actual
    double  fuel_used_kg{0.0};
    double  endurance_hr{0.0};
    double  extra_fuel_kg{0.0};    // Fuel above min required
    bool    imbalance_warn{false};
    bool    low_fuel_warn{false};
};

// ── System Health (enum defined above) ────────────────────────────────────────

struct SubsystemHealth {
    SystemStatus navigation{SystemStatus::NORMAL};
    SystemStatus guidance{SystemStatus::NORMAL};
    SystemStatus sensors{SystemStatus::NORMAL};
    SystemStatus comms{SystemStatus::NORMAL};
    SystemStatus power{SystemStatus::NORMAL};
    SystemStatus memory{SystemStatus::NORMAL};
};

}  // namespace fms
