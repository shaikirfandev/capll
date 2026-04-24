/**
 * @file    hha_controller.cpp
 * @brief   Hill Hold Assist controller implementation.
 */

#include "features/hha_controller.hpp"
#include "hal/hal_timer.hpp"
#include <algorithm>

namespace features {

void HhaController::tick(const VehicleState& vehicle) {
    using Gear = messages::MsgGearShifter::Gear;

    switch (state_) {
        case State::OFF:
            brake_hold_pct_ = 0.0f;
            // Only activate if road gradient ≥ minimum threshold
            if (std::fabsf(vehicle.hill_gradient) >= MIN_GRADIENT_PCT) {
                state_ = State::READY;
                gradient_estim_ = vehicle.hill_gradient;
            }
            break;

        case State::READY:
            brake_hold_pct_ = 0.0f;
            gradient_estim_ = vehicle.hill_gradient;

            // Return to OFF on flat road
            if (std::fabsf(vehicle.hill_gradient) < MIN_GRADIENT_PCT * 0.5f) {
                state_ = State::OFF;
                break;
            }

            // Track brake pedal
            if (vehicle.brake_pct > 5.0f) {
                brake_was_pressed_ = true;
            }

            // Activate when: stopped + brake released after being pressed + gradient
            if (brake_was_pressed_
                && vehicle.brake_pct < 2.0f
                && vehicle.speed_kph  < STOP_SPEED_KPH
                && (vehicle.gear == Gear::DRIVE || vehicle.gear == Gear::REVERSE)) {
                hold_start_tick_   = hal::Timer::getTick();
                hold_elapsed_ms_   = 0u;
                brake_hold_pct_    = 80.0f;  // Initial hold level
                brake_was_pressed_ = false;
                state_             = State::HOLDING;
            }
            break;

        case State::HOLDING: {
            hold_elapsed_ms_ = hal::Timer::getTick() - hold_start_tick_;

            // Release conditions:
            // 1. Driver applies throttle (accelerating away)
            // 2. Max hold time exceeded
            bool throttle_applied = vehicle.accel_pct > 10.0f;
            bool time_expired     = hold_elapsed_ms_ >= MAX_HOLD_MS;

            if (throttle_applied || time_expired) {
                state_ = State::RELEASING;
                break;
            }

            // Maintain hold pressure
            brake_hold_pct_ = 80.0f;
            break;
        }

        case State::RELEASING: {
            // Ramp brake hold from 80% → 0% over RELEASE_RAMP_MS
            uint32_t elapsed = hal::Timer::getTick() - hold_start_tick_;
            uint32_t release_elapsed = elapsed - hold_elapsed_ms_;

            if (release_elapsed >= RELEASE_RAMP_MS) {
                brake_hold_pct_ = 0.0f;
                state_          = State::READY;
            } else {
                float ratio     = 1.0f - (static_cast<float>(release_elapsed)
                                          / static_cast<float>(RELEASE_RAMP_MS));
                brake_hold_pct_ = 80.0f * ratio;
            }
            break;
        }

        case State::FAULT:
            brake_hold_pct_ = 0.0f;
            break;
    }
}

void HhaController::getHHAStatusMsg(messages::MsgHHAStatus& status) const {
    status.state         = state_;
    status.hold_duration = static_cast<uint16_t>(hold_elapsed_ms_);
    status.gradient_pct  = gradient_estim_;
}

} // namespace features
