/**
 * @file    hha_controller.hpp
 * @brief   Hill Hold Assist controller.
 *
 * Prevents vehicle from rolling back on uphill starts by holding brakes
 * briefly after driver releases brake pedal.
 *
 * Activation conditions:
 *   - Road gradient ≥ HHA_MIN_GRADIENT_PCT (estimated from wheel speed model)
 *   - Vehicle stopped (speed < 1 km/h)
 *   - Gear = DRIVE or REVERSE (not Park/Neutral)
 *   - Brake pedal was applied
 *
 * Hold sequence:
 *   1. HOLDING: brakes held for up to MAX_HOLD_MS while driver transitions to throttle
 *   2. RELEASING: gradual brake release over RELEASE_RAMP_MS
 *   3. Returns to READY state
 *
 * State machine:
 *   OFF → READY (gradient detected) → HOLDING (stopped, brake released)
 *       → RELEASING → READY
 *
 * Runs every 20ms.
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"
#include "features/sensor_fusion.hpp"

namespace features {

class HhaController {
public:
    static constexpr float    MIN_GRADIENT_PCT = 2.0f;    ///< Min uphill grade
    static constexpr uint32_t MAX_HOLD_MS      = 3000u;   ///< Max brake hold time
    static constexpr uint32_t RELEASE_RAMP_MS  = 500u;    ///< Gradual release ramp
    static constexpr float    STOP_SPEED_KPH   = 1.0f;    ///< "Stopped" threshold

    using State = messages::MsgHHAStatus::State;

    static HhaController& instance() {
        static HhaController inst;
        return inst;
    }

    void tick(const VehicleState& vehicle);

    void getHHAStatusMsg(messages::MsgHHAStatus& status) const;

    State   getState()         const { return state_; }
    float   getBrakeHoldPct()  const { return brake_hold_pct_; }

private:
    HhaController() = default;

    bool isHoldConditionMet(const VehicleState& v) const;

    State       state_           = State::OFF;
    float       brake_hold_pct_  = 0.0f;     ///< 0–100% brake hold command
    uint32_t    hold_start_tick_ = 0u;
    uint32_t    hold_elapsed_ms_ = 0u;
    float       gradient_estim_  = 0.0f;
    bool        brake_was_pressed_ = false;
};

} // namespace features
