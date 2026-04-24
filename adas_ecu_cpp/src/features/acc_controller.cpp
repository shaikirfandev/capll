/**
 * @file    acc_controller.cpp
 * @brief   ACC state machine + longitudinal control algorithms.
 *
 * Core algorithms:
 *
 * 1) Speed PID:
 *    error = target_speed - current_speed
 *    demand = Kp*e + Ki*∫e*dt + Kd*(de/dt)
 *
 * 2) Gap control:
 *    desired_dist = speed_mps * TIME_GAP_S   (+ MIN_FOLLOW_DIST)
 *    gap_error = actual_dist - desired_dist
 *    demand = gap_error * K_gap
 *
 * 3) AEB override:
 *    if TTC < AEB_THRESHOLD → demand = EMERGENCY_DECEL (full braking)
 */

#include "features/acc_controller.hpp"
#include "hal/hal_timer.hpp"
#include <cmath>
#include <algorithm>

namespace features {

// ──  Main tick ─────────────────────────────────────────────────────────────────

void AccController::tick(const VehicleState& vehicle,
                          const FrontTarget&  target,
                          const messages::MsgDriverInputs& driver)
{
    // ── AEB check runs in ALL states ──────────────────────────────────────────
    aeb_active_ = false;
    if (target.valid && target.ttc_s < TTC_AEB_THRESHOLD_S && vehicle.speed_kph > 5.0f) {
        aeb_active_          = true;
        accel_demand_mps2_   = EMERGENCY_DECEL_MPS2;
        brake_req_pct_       = 100.0f;
        throttle_req_pct_    = 0.0f;
        // Force FAULT state — driver must reset after AEB
        state_               = State::FAULT;
        error_code_          = 0x10;  // AEB triggered
        return;
    }

    // ── State machine ─────────────────────────────────────────────────────────
    switch (state_) {
        case State::OFF:      handleOff(driver, vehicle);           break;
        case State::STANDBY:  handleStandby(driver, vehicle, target); break;
        case State::ACTIVE:   handleActive(driver, vehicle, target);  break;
        case State::OVERRIDE: handleOverride(driver, vehicle);      break;
        case State::FAULT:
            // Latch — requires ignition cycle to clear
            accel_demand_mps2_ = 0.0f;
            brake_req_pct_     = 0.0f;
            throttle_req_pct_  = 0.0f;
            break;
    }
}

// ── OFF state handler ─────────────────────────────────────────────────────────

void AccController::handleOff(const messages::MsgDriverInputs& d,
                               const VehicleState& v) {
    accel_demand_mps2_ = 0.0f;
    brake_req_pct_     = 0.0f;
    throttle_req_pct_  = 0.0f;

    // Transition to STANDBY when ACC set pressed at valid speed
    if (d.acc_set && v.speed_kph >= MIN_SPEED_KPH && v.speed_valid) {
        set_speed_kph_ = static_cast<float>(d.acc_set_speed);
        // Clamp set speed to limits
        set_speed_kph_ = std::max(MIN_SPEED_KPH, std::min(set_speed_kph_, MAX_SPEED_KPH));
        // Reset PID integrator
        pid_.integral   = 0.0f;
        pid_.prev_error = 0.0f;
        state_          = State::STANDBY;
        error_code_     = 0u;
    }
}

// ── STANDBY state handler ─────────────────────────────────────────────────────

void AccController::handleStandby(const messages::MsgDriverInputs& d,
                                   const VehicleState& v,
                                   const FrontTarget&  t) {
    accel_demand_mps2_ = 0.0f;
    brake_req_pct_     = 0.0f;
    throttle_req_pct_  = 0.0f;

    if (d.acc_cancel) { state_ = State::OFF; return; }

    // Speed dropped below minimum — stay in standby (don't go to OFF)
    if (!v.speed_valid || v.speed_kph < MIN_SPEED_KPH) return;

    // Radar must be valid to go ACTIVE (or no target = open road)
    bool road_clear = !t.valid || t.distance_m > MIN_FOLLOW_DIST_M;
    if (road_clear || t.valid) {
        state_ = State::ACTIVE;
    }
}

// ── ACTIVE state handler ──────────────────────────────────────────────────────

void AccController::handleActive(const messages::MsgDriverInputs& d,
                                  const VehicleState& v,
                                  const FrontTarget&  t)
{
    // ── Cancel conditions ─────────────────────────────────────────────────────
    if (d.acc_cancel) {
        state_ = State::OFF;
        accel_demand_mps2_ = 0.0f; brake_req_pct_ = 0.0f;
        return;
    }
    if (d.brake_pct > 15.0f) {
        state_ = State::OVERRIDE;
        return;
    }
    if (!v.speed_valid || v.speed_kph < MIN_SPEED_KPH) {
        state_ = State::STANDBY;
        return;
    }

    // ── Update set speed on new set button press ──────────────────────────────
    if (d.acc_set && d.acc_set_speed > 0u) {
        set_speed_kph_ = std::max(MIN_SPEED_KPH,
                         std::min(static_cast<float>(d.acc_set_speed), MAX_SPEED_KPH));
        pid_.integral = 0.0f;   // Reset I on set speed change
    }

    // ── Control demand calculation ────────────────────────────────────────────
    float demand = 0.0f;

    if (t.valid && t.distance_m < (v.speed_kph / 3.6f) * TIME_GAP_S * 2.0f) {
        // Following mode: object within gap zone
        demand = followingControl(v.speed_kph, t);
    } else {
        // Speed hold mode: no relevant target, maintain set speed
        demand = speedPidControl(v.speed_kph, set_speed_kph_);
    }

    demand = clampDemand(demand);

    accel_demand_mps2_ = demand;

    // Convert demand to brake/throttle percentages for CAN output
    if (demand < -0.2f) {
        // Deceleration: map [-4.5..0] m/s² to [0..100]%
        brake_req_pct_    = std::min(100.0f, (-demand / 4.5f) * 100.0f);
        throttle_req_pct_ = 0.0f;
    } else if (demand > 0.2f) {
        // Acceleration: map [0..+2] m/s² to [0..50]% throttle
        throttle_req_pct_ = std::min(50.0f, (demand / 2.0f) * 50.0f);
        brake_req_pct_    = 0.0f;
    } else {
        // Coasting / neutral zone
        brake_req_pct_    = 0.0f;
        throttle_req_pct_ = 0.0f;
    }
}

// ── OVERRIDE state handler ────────────────────────────────────────────────────

void AccController::handleOverride(const messages::MsgDriverInputs& d,
                                    const VehicleState& v) {
    // Driver is braking — output nothing, wait for driver to release
    accel_demand_mps2_ = 0.0f;
    brake_req_pct_     = 0.0f;
    throttle_req_pct_  = 0.0f;

    if (d.brake_pct < 5.0f && d.acc_resume && v.speed_kph >= MIN_SPEED_KPH) {
        // Resume after override
        pid_.integral   = 0.0f;
        pid_.prev_error = 0.0f;
        state_          = State::ACTIVE;
    } else if (d.acc_cancel) {
        state_ = State::OFF;
    }
}

// ── Speed PID ─────────────────────────────────────────────────────────────────

float AccController::speedPidControl(float current_kph, float target_kph) {
    // Convert to m/s for SI unit computation
    float current_mps = current_kph / 3.6f;
    float target_mps  = target_kph  / 3.6f;

    float error = target_mps - current_mps;

    // Integral with anti-windup clamp
    pid_.integral += error * 0.02f;  // dt = 20ms
    const float INTEGRAL_MAX = 2.0f;
    if (pid_.integral >  INTEGRAL_MAX) pid_.integral =  INTEGRAL_MAX;
    if (pid_.integral < -INTEGRAL_MAX) pid_.integral = -INTEGRAL_MAX;

    // Derivative
    float derivative = (error - pid_.prev_error) / 0.02f;
    pid_.prev_error  = error;

    return pid_.kp * error + pid_.ki * pid_.integral + pid_.kd * derivative;
}

// ── Gap / following control ───────────────────────────────────────────────────

float AccController::followingControl(float current_kph, const FrontTarget& target) {
    float current_mps   = current_kph / 3.6f;
    float desired_dist  = current_mps * TIME_GAP_S + MIN_FOLLOW_DIST_M;
    float gap_error     = target.distance_m - desired_dist;

    // Simple proportional gap controller + closing rate feed-forward
    static constexpr float K_GAP  = 0.3f;   // proportional to distance error
    static constexpr float K_CLOS = 0.6f;   // proportional to closing rate

    float demand = K_GAP * gap_error + K_CLOS * target.rel_velocity_mps;

    // Emergency decel if TTC < warning threshold
    if (target.ttc_s < TTC_WARN_THRESHOLD_S) {
        demand = std::min(demand, MAX_DECEL_MPS2 * 0.7f);
    }

    return demand;
}

// ── Demand clamp ──────────────────────────────────────────────────────────────

float AccController::clampDemand(float demand) const {
    if (demand < MAX_DECEL_MPS2)  demand = MAX_DECEL_MPS2;
    if (demand > MAX_ACCEL_MPS2)  demand = MAX_ACCEL_MPS2;
    return demand;
}

// ── CAN message population ────────────────────────────────────────────────────

void AccController::getStatusMsg(messages::MsgACCStatus& status) const {
    status.state      = state_;
    status.set_speed  = static_cast<uint8_t>(set_speed_kph_);
    status.gap_level  = gap_level_;
    status.error_code = error_code_;
}

void AccController::getControlMsg(messages::MsgACCControl& ctrl) const {
    ctrl.accel_demand_mps2  = accel_demand_mps2_;
    ctrl.brake_req_pct      = brake_req_pct_;
    ctrl.throttle_req_pct   = throttle_req_pct_;
    ctrl.emergency_brake    = aeb_active_;
}

} // namespace features
