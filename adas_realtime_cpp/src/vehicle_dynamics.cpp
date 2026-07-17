// ============================================================
// adas/vehicle_dynamics.cpp — Vehicle dynamics implementation
// ============================================================

#include "adas/vehicle_dynamics.hpp"

#include <algorithm>
#include <cmath>

namespace adas {

// ──────────────────────────────────────────────────────────────────────────────
// Kinematic bicycle model — constant-curvature Runge–Kutta 4th order step.
//
// Equations:
//   ψ̇ = v · tan(δ) / L
//   ẋ = v · cos(ψ)
//   ẏ = v · sin(ψ)
//   v̇ = a_demand
//
// For a real-time 20 ms control cycle the Euler approximation is acceptable
// provided the speed is not very low. RK4 is used here for accuracy in
// open-loop MPC prediction.
// ──────────────────────────────────────────────────────────────────────────────
[[nodiscard]] BicycleState bicycle_step(const BicycleState& state,
                                         double steering_rad,
                                         double acceleration_mps2,
                                         double dt_s,
                                         const BicycleParameters& params) noexcept {
    const double delta = std::clamp(steering_rad, -params.max_steering_rad, params.max_steering_rad);
    const double v = std::clamp(state.speed_mps, 0.0, params.max_speed_mps);

    // At very low speed the kinematic model degenerates — freeze heading.
    const double psi_dot = (v >= 0.5) ? (v * std::tan(delta) / params.wheelbase_m) : 0.0;

    // RK4 integration (position only; speed updated with Euler on acceleration)
    auto deriv = [&](double psi, double speed) {
        return std::make_pair(speed * std::cos(psi), speed * std::sin(psi));
    };

    const auto [dx1, dy1] = deriv(state.heading_rad, v);
    const auto [dx2, dy2] = deriv(state.heading_rad + 0.5 * dt_s * psi_dot, v + 0.5 * dt_s * acceleration_mps2);
    const auto [dx3, dy3] = deriv(state.heading_rad + 0.5 * dt_s * psi_dot, v + 0.5 * dt_s * acceleration_mps2);
    const auto [dx4, dy4] = deriv(state.heading_rad + dt_s * psi_dot, v + dt_s * acceleration_mps2);

    BicycleState next;
    next.x_m        = state.x_m + (dt_s / 6.0) * (dx1 + 2.0 * dx2 + 2.0 * dx3 + dx4);
    next.y_m        = state.y_m + (dt_s / 6.0) * (dy1 + 2.0 * dy2 + 2.0 * dy3 + dy4);
    next.heading_rad = state.heading_rad + dt_s * psi_dot;
    next.speed_mps  = std::clamp(v + dt_s * acceleration_mps2, 0.0, params.max_speed_mps);
    return next;
}

// ──────────────────────────────────────────────────────────────────────────────
// VehicleMotionController — speed PID with grade compensation and jerk filter
// ──────────────────────────────────────────────────────────────────────────────
VehicleMotionController::VehicleMotionController(Limits limits) noexcept : limits_(limits) {}

void VehicleMotionController::reset() noexcept {
    integral_ = 0.0;
    previous_error_ = 0.0;
    previous_accel_ = 0.0;
    first_ = true;
}

double VehicleMotionController::compute_longitudinal(double desired_speed_mps,
                                                      double current_speed_mps,
                                                      double road_grade_rad,
                                                      double dt_s) noexcept {
    if (dt_s <= 0.0 || !std::isfinite(dt_s)) return previous_accel_;

    const double error = desired_speed_mps - current_speed_mps;

    // Grade feed-forward: on a grade θ, gravity adds g·sin(θ) opposing motion.
    const double grade_ff = kGrade * std::sin(road_grade_rad);

    // Integral with anti-windup clamping
    constexpr double kKp = 0.9, kKi = 0.20, kKd = 0.05;
    const double derivative = first_ ? 0.0 : (error - previous_error_) / dt_s;
    const double integral_candidate = integral_ + error * dt_s;
    const double raw = kKp * error + kKi * integral_candidate + kKd * derivative + grade_ff;
    const double clamped = std::clamp(raw, limits_.max_deceleration_mps2, limits_.max_acceleration_mps2);

    // Only accumulate integral if not saturated, or error is reducing saturation.
    if (clamped == raw || (error * (raw - clamped) < 0.0)) integral_ = integral_candidate;
    previous_error_ = error;
    first_ = false;

    // Jerk filter: limit da/dt
    const double max_delta = kMaxJerkMps3 * dt_s;
    const double jerk_filtered = std::clamp(clamped, previous_accel_ - max_delta, previous_accel_ + max_delta);
    previous_accel_ = std::clamp(jerk_filtered, limits_.max_deceleration_mps2, limits_.max_acceleration_mps2);
    return previous_accel_;
}

}  // namespace adas
