#pragma once
/**
 * @file vehicle_controller.hpp
 * @brief Longitudinal (PID speed) + Lateral (Stanley) vehicle controller.
 *
 * LONGITUDINAL CONTROL
 * ─────────────────────
 *   Classic PID on speed error:
 *     u_lon = Kp*e + Ki*∫e dt + Kd*(de/dt)
 *   Output: throttle ∈ [0,1] and brake ∈ [0,1] (mutually exclusive)
 *
 * LATERAL CONTROL  (Stanley method)
 * ────────────────────────────────────
 *   δ = ψ_e + arctan(k * e_cte / v)
 *   where  ψ_e  = heading error
 *          e_cte = cross-track error to nearest waypoint
 *          k     = gain constant
 *          v     = speed
 *
 * OUTPUT
 * ──────
 *   ControlCommand { throttle, brake, steer_rad }  → sent to CAN bus
 */

#include "path_planner.hpp"

#include <cstdint>

namespace adas {
namespace control {

struct ControlCommand {
    float throttle;       ///< [0.0 – 1.0]
    float brake;          ///< [0.0 – 1.0]
    float steer_rad;      ///< steering angle [rad], positive = left turn
    uint64_t timestamp_us;
};

class VehicleController {
public:
    VehicleController();
    ~VehicleController() = default;

    VehicleController(const VehicleController&)            = delete;
    VehicleController& operator=(const VehicleController&) = delete;

    /// Configure PID gains and Stanley gain
    void configure(float Kp, float Ki, float Kd, float stanley_k,
                   float max_steer_rad = 0.6109f);  // ~35 deg

    /**
     * @brief Compute control commands from current state + planned trajectory.
     * @param ego         Current vehicle state
     * @param trajectory  Trajectory from PathPlanner
     * @param timestamp_us Current time [µs]
     * @return Control command (throttle, brake, steer)
     */
    ControlCommand compute(const planning::EgoState&         ego,
                           const std::vector<planning::Waypoint>& trajectory,
                           uint64_t timestamp_us);

    /// Reset integrator (useful on mode switches / SIL test reset)
    void reset();

private:
    float computeThrottle(float speed_error, float dt_s);
    float computeSteer(const planning::EgoState& ego,
                       const planning::Waypoint&  target) const;

    // PID state
    float integral_{0.f};
    float prev_error_{0.f};
    uint64_t prev_ts_us_{0};

    // Config
    float Kp_{1.0f}, Ki_{0.05f}, Kd_{0.1f};
    float stanley_k_{0.5f};
    float max_steer_rad_{0.6109f};
    float max_integral_{5.0f};   ///< anti-windup clamp [m/s * s]
};

}  // namespace control
}  // namespace adas
