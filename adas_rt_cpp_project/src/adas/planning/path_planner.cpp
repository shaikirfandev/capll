/**
 * @file path_planner.cpp
 * @brief Behavior + trajectory planning implementation.
 */

#include "path_planner.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>

namespace adas {
namespace planning {

PathPlanner::PathPlanner() = default;

void PathPlanner::configure(float cruise_speed_mps, float lane_width_m) {
    cruise_speed_mps_ = cruise_speed_mps;
    lane_width_m_     = lane_width_m;
}

// ─── Top-level plan() ─────────────────────────────────────────────────────────

std::vector<Waypoint> PathPlanner::plan(
    const EgoState& ego,
    const std::vector<perception::TrackedObject>& objects,
    float /*dt_s*/)
{
    last_decision_ = selectBehavior(ego, objects);

    switch (last_decision_.state) {
        case BehaviorState::EMERGENCY_BRAKE:
            return generateAEBTrajectory(ego);

        case BehaviorState::FOLLOW: {
            // Find the lead vehicle track
            for (const auto& obj : objects) {
                if (obj.track_id == last_decision_.lead_track_id) {
                    return generateFollowTrajectory(ego, obj,
                                                    last_decision_.target_speed_mps);
                }
            }
            [[fallthrough]];  // lead track lost – fall back to cruise
        }

        case BehaviorState::CRUISE:
        default:
            return generateCruiseTrajectory(ego, last_decision_.target_speed_mps);
    }
}

// ─── Behavior selection ───────────────────────────────────────────────────────

BehaviorDecision PathPlanner::selectBehavior(
    const EgoState& ego,
    const std::vector<perception::TrackedObject>& objects) const
{
    BehaviorDecision decision{};
    decision.state            = BehaviorState::CRUISE;
    decision.target_speed_mps = cruise_speed_mps_;

    // Find closest confirmed obstacle in the forward corridor
    // (simplified: objects within ±1 lane width ahead)
    const float half_lane = lane_width_m_ * 0.5f;

    float   min_range   = std::numeric_limits<float>::max();
    const perception::TrackedObject* lead_obj = nullptr;

    for (const auto& obj : objects) {
        if (!obj.is_confirmed) continue;
        if (obj.px < 0.5f)    continue;           // ignore objects behind ego
        if (std::abs(obj.py) > half_lane) continue;  // ignore adjacent lanes

        const float range = obj.px;
        if (range < min_range) {
            min_range = range;
            lead_obj  = &obj;
        }
    }

    if (lead_obj == nullptr) {
        return decision;  // CRUISE
    }

    // Relative speed (positive when approaching)
    const float rel_speed = ego.speed_mps - lead_obj->vx;
    const float ttc = (rel_speed > 0.1f) ? (min_range / rel_speed)
                                          : std::numeric_limits<float>::max();

    if (ttc < kMinTTC_AEB && min_range < 30.0f) {
        decision.state            = BehaviorState::EMERGENCY_BRAKE;
        decision.lead_track_id    = lead_obj->track_id;
        decision.target_speed_mps = 0.0f;
    } else {
        decision.state            = BehaviorState::FOLLOW;
        decision.lead_track_id    = lead_obj->track_id;
        decision.desired_ttc_s    = kMinTTC_Follow;
        // ACC target speed: lead speed but not exceeding cruise
        decision.target_speed_mps = std::min(lead_obj->vx, cruise_speed_mps_);
    }
    return decision;
}

// ─── Trajectory generators ────────────────────────────────────────────────────

std::vector<Waypoint> PathPlanner::generateCruiseTrajectory(
    const EgoState& ego,
    float target_speed_mps) const
{
    std::vector<Waypoint> traj;
    traj.reserve(kNumWaypoints);

    const float T  = kPlanHorizon_s;
    const float dt = T / kNumWaypoints;

    // JMT: s0=0, v0=ego.speed, a0=ego.accel → s1=v_target*T, v1=v_target, a1=0
    const float s1 = target_speed_mps * T;
    const auto  c  = solveJMT(0.f, ego.speed_mps, ego.accel_mps2,
                               s1, target_speed_mps, 0.f, T);

    for (int i = 1; i <= kNumWaypoints; ++i) {
        const float t = i * dt;
        const float s = evalJMT(c, t);
        const float v = evalJMT_d1(c, t);

        Waypoint wp{};
        wp.x           = ego.x + s * std::cos(ego.heading_rad);
        wp.y           = ego.y + s * std::sin(ego.heading_rad);
        wp.heading_rad = ego.heading_rad;
        wp.speed_mps   = std::max(0.f, v);
        wp.curvature   = 0.f;
        wp.timestamp_s = t;
        traj.push_back(wp);
    }
    return traj;
}

std::vector<Waypoint> PathPlanner::generateFollowTrajectory(
    const EgoState& ego,
    const perception::TrackedObject& lead,
    float target_speed_mps) const
{
    // Desired gap = time_headway * ego_speed + standstill_distance
    const float desired_gap = kMinTTC_Follow * ego.speed_mps + 5.0f;
    const float actual_gap  = lead.px;
    const float gap_error   = actual_gap - desired_gap;

    // Adjust target speed proportionally to gap error (simple P controller)
    float adjusted_speed = target_speed_mps + 0.3f * gap_error;
    adjusted_speed = std::clamp(adjusted_speed, 0.f, cruise_speed_mps_);

    return generateCruiseTrajectory(ego, adjusted_speed);
}

std::vector<Waypoint> PathPlanner::generateAEBTrajectory(const EgoState& ego) const {
    std::vector<Waypoint> traj;
    traj.reserve(kNumWaypoints);

    // Linear deceleration to 0
    const float v0 = ego.speed_mps;
    const float t_stop = v0 / kMaxDecel_mps2;

    for (int i = 1; i <= kNumWaypoints; ++i) {
        const float t  = kPlanHorizon_s * i / kNumWaypoints;
        const float tt = std::min(t, t_stop);
        const float v  = std::max(0.f, v0 - kMaxDecel_mps2 * tt);
        const float s  = v0 * tt - 0.5f * kMaxDecel_mps2 * tt * tt;

        Waypoint wp{};
        wp.x           = ego.x + s * std::cos(ego.heading_rad);
        wp.y           = ego.y + s * std::sin(ego.heading_rad);
        wp.heading_rad = ego.heading_rad;
        wp.speed_mps   = v;
        wp.curvature   = 0.f;
        wp.timestamp_s = t;
        traj.push_back(wp);
    }
    return traj;
}

// ─── 5th-order JMT polynomial ─────────────────────────────────────────────────
// Solve linear system for coefficients [c3, c4, c5]:
//   [T³   T⁴    T⁵  ] [c3]   [s1 - s0 - v0*T - 0.5*a0*T²        ]
//   [3T²  4T³   5T⁴ ] [c4] = [v1 - v0 - a0*T                     ]
//   [6T   12T²  20T³] [c5]   [a1 - a0                             ]

std::array<float,6> PathPlanner::solveJMT(
    float s0, float v0, float a0,
    float s1, float v1, float a1,
    float T) const
{
    const float T2 = T*T,  T3 = T2*T,  T4 = T3*T,  T5 = T4*T;

    const float b0 = s1 - s0 - v0*T - 0.5f*a0*T2;
    const float b1 = v1 - v0 - a0*T;
    const float b2 = a1 - a0;

    // Cramer's rule on the 3×3 subsystem
    const float det = T3*(4.f*T3*20.f*T3 - 5.f*T4*12.f*T2)
                    - T4*(3.f*T2*20.f*T3 - 5.f*T4*6.f*T)
                    + T5*(3.f*T2*12.f*T2 - 4.f*T3*6.f*T);
    // Use simplified closed-form (from Werling 2010):
    const float a00=T3, a01=T4, a02=T5;
    const float a10=3.f*T2, a11=4.f*T3, a12=5.f*T4;
    const float a20=6.f*T, a21=12.f*T2, a22=20.f*T3;

    const float D = a00*(a11*a22-a12*a21)
                  - a01*(a10*a22-a12*a20)
                  + a02*(a10*a21-a11*a20);

    const float c3 = (b0*(a11*a22-a12*a21)
                    - a01*(b1*a22-a12*b2)
                    + a02*(b1*a21-a11*b2)) / D;
    const float c4 = (a00*(b1*a22-a12*b2)
                    - b0*(a10*a22-a12*a20)
                    + a02*(a10*b2-b1*a20)) / D;
    const float c5 = (a00*(a11*b2-b1*a21)
                    - a01*(a10*b2-b1*a20)
                    + b0*(a10*a21-a11*a20)) / D;

    return {s0, v0, 0.5f*a0, c3, c4, c5};
}

float PathPlanner::evalJMT(const std::array<float,6>& c, float t) const {
    return c[0] + c[1]*t + c[2]*t*t + c[3]*t*t*t
                + c[4]*t*t*t*t + c[5]*t*t*t*t*t;
}

float PathPlanner::evalJMT_d1(const std::array<float,6>& c, float t) const {
    return c[1] + 2.f*c[2]*t + 3.f*c[3]*t*t
                + 4.f*c[4]*t*t*t + 5.f*c[5]*t*t*t*t;
}

}  // namespace planning
}  // namespace adas
