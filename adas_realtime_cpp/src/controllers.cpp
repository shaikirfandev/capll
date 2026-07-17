#include "adas/controllers.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace adas {

PidController::PidController(double kp, double ki, double kd, double min_output, double max_output) noexcept
    : kp_(kp), ki_(ki), kd_(kd), min_(min_output), max_(max_output) {}

void PidController::reset() noexcept { integral_ = 0.0; previous_error_ = 0.0; first_ = true; }

double PidController::update(double setpoint, double measurement, double dt_s) noexcept {
    if (dt_s <= 0.0 || !std::isfinite(dt_s)) return 0.0;
    const double error = setpoint - measurement;
    const double derivative = first_ ? 0.0 : (error - previous_error_) / dt_s;
    const double candidate = std::clamp(integral_ + error * dt_s, min_ / std::max(ki_, 1e-9), max_ / std::max(ki_, 1e-9));
    const double unsaturated = kp_ * error + ki_ * candidate + kd_ * derivative;
    const double output = std::clamp(unsaturated, min_, max_);
    if (output == unsaturated || (error * (unsaturated - output) < 0.0)) integral_ = candidate;
    previous_error_ = error;
    first_ = false;
    return output;
}

double AdaptiveCruiseControl::compute(const VehicleState& ego, const LeadObject& lead, double set_speed_mps, double dt_s) noexcept {
    double desired_speed = set_speed_mps;
    if (lead.valid) {
        const double desired_gap = standstill_distance_m_ + time_gap_s_ * std::max(ego.speed_mps, 0.0);
        const double gap_error = lead.longitudinal_distance_m - desired_gap;
        desired_speed = std::min(desired_speed, ego.speed_mps + 0.45 * gap_error + 0.65 * lead.relative_speed_mps);
    }
    return std::clamp(speed_pid_.update(desired_speed, ego.speed_mps, dt_s), limits_.max_deceleration_mps2, limits_.max_acceleration_mps2);
}

double LaneCenteringController::compute(const VehicleState& ego, const LaneModel& lane, double dt_s) noexcept {
    const double lookahead_error = lane.lateral_offset_m + std::max(ego.speed_mps, 2.0) * 0.45 * lane.heading_error_rad;
    const double raw = lateral_pid_.update(0.0, lookahead_error, dt_s);
    const double max_step = limits_.max_steering_rate_radps * dt_s;
    previous_command_ += std::clamp(raw - previous_command_, -max_step, max_step);
    return std::clamp(previous_command_, -limits_.max_steering_angle_rad, limits_.max_steering_angle_rad);
}

double MpcLaneCenteringController::compute(const VehicleState& ego, const LaneModel& lane, double dt_s) noexcept {
    if (!std::isfinite(dt_s) || dt_s <= 0.0) return previous_command_;
    constexpr int kCandidateCount = 5;
    constexpr double kRateScales[kCandidateCount] = {-1.0, -0.5, 0.0, 0.5, 1.0};
    const double max_step = limits_.max_steering_rate_radps * dt_s;
    const double speed = std::max(ego.speed_mps, 1.0);
    double best_command = previous_command_;
    double best_cost = std::numeric_limits<double>::infinity();

    for (const double scale : kRateScales) {
        const double candidate = std::clamp(previous_command_ + scale * max_step,
                                            -limits_.max_steering_angle_rad, limits_.max_steering_angle_rad);
        double lateral_error = lane.lateral_offset_m;
        double heading_error = lane.heading_error_rad;
        double cost = 0.2 * candidate * candidate + 2.0 * (candidate - previous_command_) * (candidate - previous_command_);
        for (int step = 0; step < kPredictionHorizon; ++step) {
            heading_error += (speed / kWheelbaseM) * candidate * dt_s;
            lateral_error += speed * heading_error * dt_s;
            cost += 8.0 * lateral_error * lateral_error + 3.0 * heading_error * heading_error;
        }
        if (cost < best_cost) {
            best_cost = cost;
            best_command = candidate;
        }
    }
    previous_command_ = best_command;
    return previous_command_;
}

}  // namespace adas
