#pragma once

#include "adas/types.hpp"

namespace adas {

class PidController {
public:
    PidController(double kp, double ki, double kd, double min_output, double max_output) noexcept;
    double update(double setpoint, double measurement, double dt_s) noexcept;
    void reset() noexcept;

private:
    double kp_, ki_, kd_, min_, max_;
    double integral_{};
    double previous_error_{};
    bool first_{true};
};

class AdaptiveCruiseControl {
public:
    explicit AdaptiveCruiseControl(Limits limits) noexcept : limits_(limits), speed_pid_(0.8, 0.18, 0.04, limits.max_deceleration_mps2, limits.max_acceleration_mps2) {}
    double compute(const VehicleState& ego, const LeadObject& lead, double set_speed_mps, double dt_s) noexcept;

private:
    Limits limits_;
    PidController speed_pid_;
    double time_gap_s_{1.8};
    double standstill_distance_m_{5.0};
};

class LaneCenteringController {
public:
    explicit LaneCenteringController(Limits limits) noexcept : limits_(limits), lateral_pid_(0.38, 0.02, 0.08, -limits.max_steering_angle_rad, limits.max_steering_angle_rad) {}
    double compute(const VehicleState& ego, const LaneModel& lane, double dt_s) noexcept;

private:
    Limits limits_;
    PidController lateral_pid_;
    double previous_command_{};
};

// Fixed-cost finite-control-set MPC for the kinematic bicycle model. It uses a
// fixed candidate set and horizon, so run time and memory are bounded.
class MpcLaneCenteringController {
public:
    explicit MpcLaneCenteringController(Limits limits) noexcept : limits_(limits) {}
    double compute(const VehicleState& ego, const LaneModel& lane, double dt_s) noexcept;

private:
    Limits limits_;
    double previous_command_{};
    static constexpr double kWheelbaseM = 2.8;
    static constexpr int kPredictionHorizon = 12;
};

}  // namespace adas
