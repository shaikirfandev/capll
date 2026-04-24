/**
 * @file    lka_controller.hpp
 * @brief   Lane Keeping Assist + Lane Departure Warning controller.
 *
 * LKA: Applies steering torque overlay to keep vehicle within lane.
 * LDW: Issues audio/visual warning when lane marking is crossed.
 *
 * State machine (LKA):
 *   OFF → READY (≥60 km/h, lane visible) → PREPARING (offset growing) → INTERVENING
 *
 * Torque model: proportional to lateral offset with speed scaling.
 *   Torque = Kp * offset_error + Kd * rate_of_change
 *   Clamped to ±MAX_TORQUE_NM
 *
 * LDW triggers when:
 *   - Lane offset > WARN_THRESHOLD_M
 *   - No turn indicator active
 *   - Speed > MIN_SPEED_KPH
 *   - Lane quality ≥ 1
 *
 * Runs every 20ms.
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"
#include "features/sensor_fusion.hpp"

namespace features {

class LkaController {
public:
    static constexpr float  MIN_SPEED_KPH       = 60.0f;
    static constexpr float  MAX_TORQUE_NM        = 5.0f;
    static constexpr float  WARN_THRESHOLD_M     = 0.27f;   ///< LDW alert offset
    static constexpr float  INTERVENE_THRESH_M   = 0.22f;   ///< LKA starts intervening
    static constexpr float  KP                   = 8.0f;    ///< Proportional gain
    static constexpr float  KD                   = 1.5f;    ///< Derivative gain

    using LKAState   = messages::MsgLKAStatus::State;
    using WarnSide   = messages::MsgLKAStatus::WarnSide;

    static LkaController& instance() {
        static LkaController inst;
        return inst;
    }

    void tick(const VehicleState& vehicle,
              const LaneModel&    lane,
              const messages::MsgDriverInputs& driver);

    void getLKAStatusMsg(messages::MsgLKAStatus&   status) const;
    void getLKATorqueMsg(messages::MsgLKATorqueCmd& torque) const;
    void getLDWMsg       (messages::MsgLDWWarning&  ldw)    const;

    LKAState getState()     const { return lka_state_; }
    float    getTorque()    const { return torque_cmd_nm_; }
    bool     isLDWActive()  const { return ldw_active_; }

private:
    LkaController() = default;

    float computeTorque(float offset_m, float rate_mps);

    LKAState    lka_state_      = LKAState::OFF;
    WarnSide    warn_side_      = WarnSide::NONE;
    float       torque_cmd_nm_  = 0.0f;
    bool        ldw_active_     = false;
    bool        ldw_left_       = false;
    bool        ldw_right_      = false;
    float       prev_offset_    = 0.0f;
    uint8_t     min_lane_quality_ = 1u;
};

} // namespace features
