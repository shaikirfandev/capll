#pragma once

// ============================================================
// adas/vehicle_dynamics.hpp — Vehicle dynamics model utilities
//
// Implements:
//   1. KinematicBicycleModel  — constant-curvature prediction step used by MPC
//   2. VehicleMotionControl   — longitudinal PID + jerk filter + lateral MPC wrapper
//
// Model assumptions (valid for normal driving conditions):
//   - Front-wheel steer, rigid axles, no tyre slip below 100 km/h.
//   - Road grade treated as a bias on the longitudinal acceleration demand.
//   - At speeds below 1 m/s the heading integration is frozen to prevent
//     numerical blow-up due to division by near-zero speed.
//
// Production extensions needed before series use:
//   - Add Pacejka magic-formula tyre model.
//   - Calibrate Cf/Cr (cornering stiffness) per tyre compound.
//   - Couple brake blending and drivetrain delay model.
//   - Validate with chassis-dynamometer and flat-track test data.
// ============================================================

#include "adas/types.hpp"

namespace adas {

// ──────────────────────────────────────────────────────────────────────────────
// Kinematic bicycle prediction step.
// Inputs : current state x=[x_m,y_m,\psi,v], steering delta, dt_s.
// Outputs: next state.  No allocation.  Branchless for speed and speed safety.
// ──────────────────────────────────────────────────────────────────────────────
struct BicycleState {
    double x_m{};
    double y_m{};
    double heading_rad{};
    double speed_mps{};
};

struct BicycleParameters {
    double wheelbase_m{2.80};
    double cog_to_front_m{1.30};  // Distance from CoG to front axle
    double max_steering_rad{0.55};
    double max_speed_mps{70.0};
};

/// @brief Advance kinematic bicycle state by dt_s seconds.
/// @note  noexcept – safe to call from real-time control thread.
[[nodiscard]] BicycleState bicycle_step(const BicycleState& state,
                                         double steering_rad,
                                         double acceleration_mps2,
                                         double dt_s,
                                         const BicycleParameters& params) noexcept;

// ──────────────────────────────────────────────────────────────────────────────
// Road-grade-aware vehicle motion controller.
//
// Combines:
//   - Longitudinal: speed-error PID → acceleration demand → jerk filter.
//   - Lateral     : MPC-FCS (see controllers.hpp) called through supervisor.
//
// The jerk filter limits da/dt to ±kMaxJerkMps3. This prevents passenger
// discomfort and protects the brake hardware from square-wave torque requests.
// ──────────────────────────────────────────────────────────────────────────────
class VehicleMotionController {
public:
    explicit VehicleMotionController(Limits limits) noexcept;

    /// @brief Compute acceleration demand for desired speed, considering grade.
    /// @param desired_speed_mps  Target longitudinal speed (m/s).
    /// @param current_speed_mps  Filtered speed from CAN (m/s).
    /// @param road_grade_rad     Positive = uphill (rad).
    /// @param dt_s               Control period (s).
    /// @return Clamped jerk-filtered acceleration demand (m/s²).
    [[nodiscard]] double compute_longitudinal(double desired_speed_mps,
                                               double current_speed_mps,
                                               double road_grade_rad,
                                               double dt_s) noexcept;

    void reset() noexcept;

    [[nodiscard]] double previous_acceleration() const noexcept { return previous_accel_; }

private:
    static constexpr double kMaxJerkMps3 = 3.0;  // Comfort limit per ISO 15622
    static constexpr double kGrade = 9.80665;

    Limits limits_;
    double integral_{};
    double previous_error_{};
    double previous_accel_{};
    bool first_{true};
};

}  // namespace adas
