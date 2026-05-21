#pragma once
/**
 * @file path_planner.hpp
 * @brief Trajectory / path planning for ADAS (ACC + Emergency Braking + Lane Keep)
 *
 * PLANNING HIERARCHY
 * ──────────────────
 *   Mission  →  Route planner (not here, uses HD map)
 *   Behavior →  Decision: follow, change lane, brake, stop
 *   Motion   →  THIS MODULE: generates a smooth trajectory (5th-order polynomial)
 *
 * TRAJECTORY REPRESENTATION
 * ─────────────────────────
 *   • A sequence of Waypoints in ego-vehicle Frenet frame (s, d, t)
 *     converted to Cartesian for the controller.
 *   • Polynomials are optimised for minimum jerk over a 3 s horizon.
 *
 * REAL-TIME CONSTRAINT
 * ────────────────────
 *   Target: < 2 ms / cycle at 20 Hz.  No dynamic allocation in hot path.
 */

#include "sensor_fusion.hpp"  // for TrackedObject

#include <array>
#include <cstdint>
#include <vector>

namespace adas {
namespace planning {

// ─── Waypoint ─────────────────────────────────────────────────────────────────

struct Waypoint {
    float x, y;          ///< ego-frame Cartesian [m]
    float heading_rad;   ///< desired heading [rad]
    float speed_mps;     ///< desired speed at this point [m/s]
    float curvature;     ///< 1/R [1/m]
    float timestamp_s;   ///< relative time from now
};

// ─── Driving decision ─────────────────────────────────────────────────────────

enum class BehaviorState : uint8_t {
    CRUISE          = 0,  ///< no obstacles, maintain cruise speed
    FOLLOW          = 1,  ///< ACC following mode
    EMERGENCY_BRAKE = 2,  ///< AEB triggered
    LANE_CHANGE_L   = 3,
    LANE_CHANGE_R   = 4,
    STOP            = 5,
};

struct BehaviorDecision {
    BehaviorState state;
    float         target_speed_mps;
    float         desired_ttc_s;       ///< Time-To-Collision target
    uint32_t      lead_track_id;       ///< ID of lead vehicle (0 if none)
};

// ─── Planner inputs ───────────────────────────────────────────────────────────

struct EgoState {
    float x, y;           ///< position in global/map frame [m]
    float heading_rad;    ///< yaw [rad]
    float speed_mps;      ///< longitudinal speed [m/s]
    float accel_mps2;     ///< longitudinal acceleration [m/s²]
    float yaw_rate_rads;  ///< yaw rate [rad/s]
};

// ─── PathPlanner class ────────────────────────────────────────────────────────

/**
 * @class PathPlanner
 * @brief Behavior decision + minimum-jerk polynomial trajectory generator.
 *
 * Usage:
 * @code
 *   PathPlanner planner;
 *   planner.configure(cruise_speed_mps, lane_width_m);
 *   auto trajectory = planner.plan(ego_state, tracked_objects, dt_s);
 * @endcode
 */
class PathPlanner {
public:
    PathPlanner();
    ~PathPlanner() = default;

    PathPlanner(const PathPlanner&)            = delete;
    PathPlanner& operator=(const PathPlanner&) = delete;

    void configure(float cruise_speed_mps, float lane_width_m = 3.7f);

    /**
     * @brief Compute a trajectory for the next 3 seconds.
     * @param ego       Current ego-vehicle state
     * @param objects   Tracked objects from SensorFusion
     * @param dt_s      Time step [s] (used for ACC gap calculation)
     * @return          Trajectory as a vector of Waypoints
     */
    std::vector<Waypoint> plan(const EgoState& ego,
                               const std::vector<perception::TrackedObject>& objects,
                               float dt_s);

    /// Accessor: last behavior decision (for logging/telemetry)
    BehaviorDecision lastDecision() const { return last_decision_; }

private:
    // ── Behavior selection ───────────────────────────────────────────────────
    BehaviorDecision selectBehavior(
        const EgoState& ego,
        const std::vector<perception::TrackedObject>& objects) const;

    // ── Trajectory generation ────────────────────────────────────────────────

    /// Generate ACC following trajectory (polynomial speed profile)
    std::vector<Waypoint> generateFollowTrajectory(
        const EgoState& ego,
        const perception::TrackedObject& lead,
        float target_speed_mps) const;

    /// Generate cruise/straight-line trajectory
    std::vector<Waypoint> generateCruiseTrajectory(
        const EgoState& ego,
        float target_speed_mps) const;

    /// Generate emergency brake trajectory (linear decel to 0)
    std::vector<Waypoint> generateAEBTrajectory(const EgoState& ego) const;

    // ── 5th-order polynomial solver ──────────────────────────────────────────
    /**
     * @brief Solve 5th-order Jerk-minimising (JMT) polynomial.
     *
     * Boundary conditions: s(0)=s0, s'(0)=v0, s''(0)=a0
     *                      s(T)=s1, s'(T)=v1, s''(T)=a1
     * @return Coefficients [c0..c5] of s(t) = c0 + c1*t + ... + c5*t^5
     */
    std::array<float,6> solveJMT(float s0, float v0, float a0,
                                  float s1, float v1, float a1,
                                  float T) const;

    float evalJMT(const std::array<float,6>& c, float t) const;
    float evalJMT_d1(const std::array<float,6>& c, float t) const;  // velocity

    // ── AEB logic ────────────────────────────────────────────────────────────
    bool aebTriggered(const EgoState& ego,
                      const perception::TrackedObject& lead) const;

    // ── Configuration ────────────────────────────────────────────────────────
    float cruise_speed_mps_{33.33f};  ///< 120 km/h default
    float lane_width_m_{3.7f};
    static constexpr float kMinTTC_AEB       = 1.5f;   ///< AEB trigger [s]
    static constexpr float kMinTTC_Follow    = 2.5f;   ///< ACC headway [s]
    static constexpr float kPlanHorizon_s    = 3.0f;
    static constexpr int   kNumWaypoints     = 30;
    static constexpr float kMaxDecel_mps2    = 8.0f;   ///< AEB decel [m/s²]
    static constexpr float kMaxAccel_mps2    = 2.5f;   ///< Comfort accel

    BehaviorDecision last_decision_{};
};

}  // namespace planning
}  // namespace adas
