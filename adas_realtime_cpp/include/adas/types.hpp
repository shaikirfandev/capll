#pragma once

// ============================================================
// adas/types.hpp — Shared ADAS data model
// Production C++20. No dynamic allocation; all types trivially copyable
// or standard-layout for zero-overhead transport boundaries.
// All SI units: m, m/s, m/s², rad, rad/s, N, Nm, kg.
// ============================================================

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace adas {

using TimePoint = std::chrono::steady_clock::time_point;
constexpr double kGravityMps2 = 9.80665;

enum class DriveDirection : std::uint8_t { Forward, Reverse };
enum class ControlMode : std::uint8_t { Disabled, Standby, Active, Degraded, Fault };

enum class Fault : std::uint32_t {
    None = 0U,
    ConfigurationInvalid = 1U << 0U,
    FrameStale = 1U << 1U,
    FrameInvalid = 1U << 2U,
    DriverOverride = 1U << 3U,
    BrakeUnavailable = 1U << 4U,
    SteeringUnavailable = 1U << 5U,
    LeadUnavailable = 1U << 6U,
    LaneUnavailable = 1U << 7U,
    EstimatorRejectedMeasurement = 1U << 8U,
    DeadlineMiss = 1U << 9U,
    GatewayWriteFailure = 1U << 10U,
};

constexpr Fault operator|(Fault left, Fault right) noexcept {
    return static_cast<Fault>(static_cast<std::uint32_t>(left) | static_cast<std::uint32_t>(right));
}

constexpr Fault& operator|=(Fault& left, Fault right) noexcept {
    left = left | right;
    return left;
}

constexpr bool has_fault(Fault value, Fault test) noexcept {
    return (static_cast<std::uint32_t>(value) & static_cast<std::uint32_t>(test)) != 0U;
}

struct VehicleState {
    TimePoint timestamp{};
    double speed_mps{};
    double acceleration_mps2{};
    double yaw_rate_radps{};
    double steering_angle_rad{};
    double lane_offset_m{};        // Positive: vehicle is right of lane centre.
    double heading_error_rad{};    // Positive: vehicle heading points right of lane direction.
    bool driver_override{};
    bool brake_available{true};
    bool steering_available{true};
    bool valid{};
};

struct LeadObject {
    double longitudinal_distance_m{std::numeric_limits<double>::infinity()};
    double relative_speed_mps{};  // Lead minus ego; negative while closing.
    double confidence{};          // [0, 1]
    bool valid{};
};

struct LaneModel {
    double lateral_offset_m{};
    double heading_error_rad{};
    double confidence{};          // [0, 1]
    bool valid{};
};

struct SensorFrame {
    TimePoint timestamp{};
    VehicleState vehicle{};
    LeadObject lead{};
    LaneModel lane{};
};

struct ActuatorCommand {
    TimePoint timestamp{};
    double requested_acceleration_mps2{};
    double requested_steering_angle_rad{};
    bool aeb_request{};
    ControlMode longitudinal_mode{ControlMode::Disabled};
    ControlMode lateral_mode{ControlMode::Disabled};
    Fault faults{Fault::None};
};

struct Limits {
    double max_acceleration_mps2{2.0};
    double max_deceleration_mps2{-8.0};
    double max_steering_angle_rad{0.55};
    double max_steering_rate_radps{0.35};
};

struct CycleHealth {
    std::uint64_t cycle_count{};
    std::uint64_t deadline_miss_count{};
    std::chrono::microseconds worst_execution_time{};
    Fault faults{Fault::None};
};

// ── Vehicle dynamics state (bicycle model + longitudinal) ──────────────────
struct VehicleDynamics {
    // Longitudinal
    double speed_mps{};
    double acceleration_mps2{};
    double jerk_mps3{};
    // Lateral — SAE sign convention (right-hand vehicle frame)
    double yaw_rate_radps{};
    double side_slip_rad{};
    double lateral_acceleration_mps2{};
    // Road geometry
    double road_curvature_invm{};  // Curvature κ = 1/R; positive = turning left
    double road_grade_rad{};       // Positive = uphill
    // Tyre
    double front_tyre_slip_rad{};
    double rear_tyre_slip_rad{};
    bool valid{};
};

// ── IMU raw measurement ────────────────────────────────────────────────────
struct ImuMeasurement {
    TimePoint timestamp{};
    // Body-frame linear accelerations (include gravity projection)
    double ax_mps2{};
    double ay_mps2{};
    double az_mps2{};
    // Body-frame angular rates
    double gx_radps{};
    double gy_radps{};
    double gz_radps{};
    bool valid{};
};

// ── Object track from a single sensor ─────────────────────────────────────
struct ObjectTrack {
    std::uint32_t track_id{};         // Sensor-assigned track ID
    double longitudinal_m{};          // Range along ego heading
    double lateral_m{};               // Positive = left of ego
    double longitudinal_rate_mps{};   // Positive = moving away
    double lateral_rate_mps{};
    double rcs_dbsm{};                // Radar cross section (radar only)
    double confidence{};
    bool valid{};
};

// ── Multi-object sensor fusion output ─────────────────────────────────────
struct FusedObjectList {
    static constexpr std::size_t kMaxObjects = 16U;
    std::array<ObjectTrack, kMaxObjects> objects{};
    std::uint8_t object_count{};
    TimePoint timestamp{};
};

// ── EKF ego state estimate ─────────────────────────────────────────────────
// State vector: [x_m, y_m, heading_rad, speed_mps, yaw_rate_radps]
struct EgoStateEstimate {
    double x_m{};
    double y_m{};
    double heading_rad{};
    double speed_mps{};
    double yaw_rate_radps{};
    double speed_variance{};
    double position_variance_m2{};
    TimePoint timestamp{};
    bool valid{};
};

// ── Diagnostic trouble code ────────────────────────────────────────────────
enum class DtcStatus : std::uint8_t { Clear, Pending, Confirmed, Aged };

struct DiagnosticEvent {
    std::uint32_t dtc_code{};         // 3-byte DTC (e.g. U0100 = 0x00U0100)
    DtcStatus status{DtcStatus::Clear};
    std::uint8_t occurrence_counter{};
    TimePoint first_occurrence{};
    TimePoint last_occurrence{};
};

// ── Actuator feedback ──────────────────────────────────────────────────────
struct ActuatorFeedback {
    TimePoint timestamp{};
    double actual_acceleration_mps2{};
    double actual_steering_angle_rad{};
    bool brake_active{};
    bool ebs_active{};                // Electronic brake system engaged
    bool valid{};
};

// ── Calibration record ────────────────────────────────────────────────────
struct CalibrationRecord {
    std::uint32_t schema_version{1U};
    double time_gap_s{1.8};
    double standstill_gap_m{5.0};
    double cruise_speed_mps{27.78};
    double mpc_lateral_cost_q{8.0};
    double mpc_heading_cost_r{3.0};
    // Kalman noise tuning
    double kf_process_noise_range{0.25};
    double kf_process_noise_rate{1.0};
    double kf_meas_variance_range{2.25};
    double kf_meas_variance_rate{0.64};
};

}  // namespace adas
