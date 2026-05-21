/**
 * @file vehicle_controller.cpp
 * @brief Longitudinal PID + Stanley lateral controller implementation.
 */

#include "vehicle_controller.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>

namespace adas {
namespace control {

VehicleController::VehicleController() = default;

void VehicleController::configure(float Kp, float Ki, float Kd,
                                   float stanley_k, float max_steer_rad) {
    Kp_            = Kp;
    Ki_            = Ki;
    Kd_            = Kd;
    stanley_k_     = stanley_k;
    max_steer_rad_ = max_steer_rad;
}

void VehicleController::reset() {
    integral_    = 0.f;
    prev_error_  = 0.f;
    prev_ts_us_  = 0;
}

// ─── Main compute() ───────────────────────────────────────────────────────────

ControlCommand VehicleController::compute(
    const planning::EgoState&              ego,
    const std::vector<planning::Waypoint>& trajectory,
    uint64_t timestamp_us)
{
    ControlCommand cmd{};
    cmd.timestamp_us = timestamp_us;

    if (trajectory.empty()) {
        // Safety: if no trajectory, hold brakes
        cmd.brake   = 0.5f;
        cmd.throttle = 0.f;
        cmd.steer_rad = 0.f;
        return cmd;
    }

    // ── Compute dt ────────────────────────────────────────────────────────────
    float dt_s = 0.05f;
    if (prev_ts_us_ > 0) {
        dt_s = static_cast<float>(timestamp_us - prev_ts_us_) * 1e-6f;
        dt_s = std::clamp(dt_s, 0.005f, 0.5f);
    }
    prev_ts_us_ = timestamp_us;

    // ── Longitudinal PID ─────────────────────────────────────────────────────
    // Look at the first waypoint's desired speed (nearest horizon)
    const float target_speed = trajectory.front().speed_mps;
    const float speed_error  = target_speed - ego.speed_mps;
    const float throttle     = computeThrottle(speed_error, dt_s);

    if (throttle >= 0.f) {
        cmd.throttle = std::min(1.0f, throttle);
        cmd.brake    = 0.f;
    } else {
        cmd.throttle = 0.f;
        cmd.brake    = std::min(1.0f, -throttle);
    }

    // ── Stanley lateral control ──────────────────────────────────────────────
    // Find nearest waypoint on trajectory (look-ahead ~1 s)
    const auto& target_wp = trajectory[std::min<size_t>(5, trajectory.size()-1)];
    cmd.steer_rad = computeSteer(ego, target_wp);

    return cmd;
}

// ─── PID longitudinal ────────────────────────────────────────────────────────

float VehicleController::computeThrottle(float speed_error, float dt_s) {
    // Anti-windup: only integrate when not saturated
    integral_ += speed_error * dt_s;
    integral_  = std::clamp(integral_, -max_integral_, max_integral_);

    const float derivative = (speed_error - prev_error_) / dt_s;
    prev_error_ = speed_error;

    return Kp_ * speed_error + Ki_ * integral_ + Kd_ * derivative;
}

// ─── Stanley lateral ──────────────────────────────────────────────────────────

float VehicleController::computeSteer(const planning::EgoState&  ego,
                                       const planning::Waypoint& target) const {
    // ① Heading error: angle from ego heading to target heading
    float heading_error = target.heading_rad - ego.heading_rad;
    // Normalise to [-π, π]
    while (heading_error >  M_PIf32) heading_error -= 2.f * M_PIf32;
    while (heading_error < -M_PIf32) heading_error += 2.f * M_PIf32;

    // ② Cross-track error: signed lateral distance to target waypoint
    const float dx    = target.x - ego.x;
    const float dy    = target.y - ego.y;
    const float e_cte = -std::sin(ego.heading_rad) * dx
                       + std::cos(ego.heading_rad) * dy;

    // ③ Stanley formula
    const float v_safe = std::max(ego.speed_mps, 0.5f);  // prevent div by 0
    const float steer  = heading_error
                        + std::atan2(stanley_k_ * e_cte, v_safe);

    return std::clamp(steer, -max_steer_rad_, max_steer_rad_);
}

}  // namespace control
}  // namespace adas
