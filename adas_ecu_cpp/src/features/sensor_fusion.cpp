/**
 * @file    sensor_fusion.cpp
 * @brief   Sensor fusion world model implementation.
 */

#include "features/sensor_fusion.hpp"
#include <cmath>

namespace features {

void SensorFusion::update(
    const messages::MsgRadarObject&   radar,
    const messages::MsgCameraLane&    camera,
    const messages::MsgBSDRadar&      bsd,
    const messages::MsgUltrasonic&    ultrasonic,
    const messages::MsgVehicleSpeed&  speed,
    const messages::MsgSteeringAngle& steer,
    const messages::MsgDriverInputs&  driver,
    const messages::MsgGearShifter&   gear
) {
    // ── Vehicle state ──────────────────────────────────────────────────────────
    vehicle_state_.speed_kph        = speed.speed_kph;
    vehicle_state_.is_reversing     = speed.reverse;
    vehicle_state_.steer_angle_deg  = steer.angle_deg;
    vehicle_state_.steer_rate_dps   = steer.rate_deg_s;
    vehicle_state_.brake_pct        = driver.brake_pct;
    vehicle_state_.accel_pct        = driver.accel_pct;
    vehicle_state_.turn_left        = driver.turn_left;
    vehicle_state_.turn_right       = driver.turn_right;
    vehicle_state_.gear             = gear.pos;
    vehicle_state_.speed_valid      = speed.valid;
    vehicle_state_.hill_gradient    = estimateGradient(speed);

    // ── Front target (radar + camera fusion) ──────────────────────────────────
    fuseFrontTarget(radar, camera);

    // ── Lane model ────────────────────────────────────────────────────────────
    lane_model_.left_offset_m    = camera.left_offset_m;
    lane_model_.right_offset_m   = camera.right_offset_m;
    lane_model_.left_quality     = camera.left_quality;
    lane_model_.right_quality    = camera.right_quality;
    lane_model_.ldw_left         = camera.ldw_left_active;
    lane_model_.ldw_right        = camera.ldw_right_active;
    lane_model_.valid            = (camera.left_quality >= 1u || camera.right_quality >= 1u);

    // ── Blind zone ────────────────────────────────────────────────────────────
    blind_zone_.left_occupied  = bsd.left_detected;
    blind_zone_.right_occupied = bsd.right_detected;
    blind_zone_.left_dist_m    = bsd.left_dist_m;
    blind_zone_.right_dist_m   = bsd.right_dist_m;
    blind_zone_.valid          = true;

    // ── Parking model ─────────────────────────────────────────────────────────
    parking_model_.fl_cm  = ultrasonic.fl_cm;
    parking_model_.fr_cm  = ultrasonic.fr_cm;
    parking_model_.rl_cm  = ultrasonic.rl_cm;
    parking_model_.rr_cm  = ultrasonic.rr_cm;
    parking_model_.valid  = (ultrasonic.fl_valid || ultrasonic.rr_valid);
}

// ── Private: fuse front target ────────────────────────────────────────────────

void SensorFusion::fuseFrontTarget(
    const messages::MsgRadarObject& r,
    const messages::MsgCameraLane&  c)
{
    UNUSED(c);  // Camera used for type confirmation in full implementation

    if (!r.valid) {
        // No radar contact — clear/far state
        front_target_.valid        = false;
        front_target_.distance_m   = 150.0f;
        front_target_.rel_velocity_mps = 0.0f;
        front_target_.ttc_s        = 99.0f;
        front_target_.type         = messages::MsgRadarObject::ObjectType::NONE;
        return;
    }

    front_target_.valid             = true;
    front_target_.distance_m        = r.distance_m;
    front_target_.rel_velocity_mps  = r.rel_velocity_mps;
    front_target_.ttc_s             = r.ttc_s;
    front_target_.type              = r.type;

    // Camera confirmation: if left+right offsets ~= 0 AND radar valid → camera confirms
    // (simplified — real system uses camera bounding box matching)
    front_target_.camera_confirms =
        (std::fabsf(c.left_offset_m) < 0.05f && c.left_quality >= 2u);
}

// ── Private: gradient estimation ─────────────────────────────────────────────

float SensorFusion::estimateGradient(const messages::MsgVehicleSpeed& v) {
    // Simple gradient estimation from speed rate of change
    // (real system uses a longitudinal accelerometer on the IMU)
    // Δv / Δt ≈ a(m/s²) → if no throttle/brake, a ≈ g * sin(grade)
    // g * sin(grade) ≈ g * grade(rad) ≈ 9.81 * grade_fraction
    // grade_pct = (a/9.81) * 100
    // Here we do a simple LPF on the estimated slope

    float delta_v_kph = v.speed_kph - speed_prev_;
    speed_prev_       = v.speed_kph;

    // At 20ms cycle: acceleration ≈ (delta_v_kph / 3.6) / 0.02 m/s²
    float accel_mps2  = (delta_v_kph / 3.6f) / 0.02f;

    // Gradient estimate (%)
    float grad_estim  = (accel_mps2 / 9.81f) * 100.0f;

    // Low-pass filter: α = 0.05 (heavily filtered for stability)
    static constexpr float ALPHA = 0.05f;
    gradient_lpf_ = ALPHA * grad_estim + (1.0f - ALPHA) * gradient_lpf_;

    return gradient_lpf_;
}

} // namespace features
