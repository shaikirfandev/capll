/**
 * @file    lka_controller.cpp
 * @brief   LKA + LDW controller implementation.
 */

#include "features/lka_controller.hpp"
#include <cmath>
#include <algorithm>

namespace features {

void LkaController::tick(const VehicleState& vehicle,
                          const LaneModel&    lane,
                          const messages::MsgDriverInputs& driver)
{
    ldw_active_ = false;
    ldw_left_   = false;
    ldw_right_  = false;

    // ── LDW evaluation (runs regardless of LKA state) ─────────────────────────
    bool speed_ok      = vehicle.speed_kph >= MIN_SPEED_KPH;
    bool no_indicator  = !driver.turn_left && !driver.turn_right;
    bool lane_visible  = lane.left_quality >= min_lane_quality_ ||
                         lane.right_quality >= min_lane_quality_;

    if (speed_ok && no_indicator && lane_visible) {
        if (std::fabsf(lane.left_offset_m)  > WARN_THRESHOLD_M && lane.left_quality  >= 1u) {
            ldw_left_   = true;
            ldw_active_ = true;
        }
        if (std::fabsf(lane.right_offset_m) > WARN_THRESHOLD_M && lane.right_quality >= 1u) {
            ldw_right_  = true;
            ldw_active_ = true;
        }
    }

    // ── LKA state machine ─────────────────────────────────────────────────────
    switch (lka_state_) {
        case LKAState::OFF:
            torque_cmd_nm_ = 0.0f;
            if (driver.lka_toggle) {
                lka_state_ = LKAState::READY;
            }
            break;

        case LKAState::READY:
            torque_cmd_nm_ = 0.0f;
            if (!driver.lka_toggle) {
                lka_state_ = LKAState::OFF;
                break;
            }
            if (!speed_ok || !lane_visible) break;

            // Move to PREPARING if offset is growing toward threshold
            if (std::fabsf(lane.left_offset_m)  > INTERVENE_THRESH_M * 0.8f ||
                std::fabsf(lane.right_offset_m) > INTERVENE_THRESH_M * 0.8f) {
                lka_state_ = LKAState::PREPARING;
            }
            break;

        case LKAState::PREPARING:
            torque_cmd_nm_ = 0.0f;
            if (!speed_ok || !lane_visible || !driver.lka_toggle) {
                lka_state_ = LKAState::READY;
                break;
            }
            // Suppress if driver is intentionally changing lane
            if (driver.turn_left || driver.turn_right) {
                lka_state_ = LKAState::READY;
                break;
            }
            if (std::fabsf(lane.left_offset_m)  > INTERVENE_THRESH_M ||
                std::fabsf(lane.right_offset_m) > INTERVENE_THRESH_M) {
                lka_state_ = LKAState::INTERVENING;
            } else {
                lka_state_ = LKAState::READY;
            }
            break;

        case LKAState::INTERVENING: {
            if (!speed_ok || !lane_visible || !driver.lka_toggle ||
                driver.turn_left || driver.turn_right) {
                torque_cmd_nm_ = 0.0f;
                lka_state_     = LKAState::READY;
                break;
            }

            // Determine which side needs correction
            float offset = 0.0f;
            if      (std::fabsf(lane.left_offset_m)  > INTERVENE_THRESH_M) {
                offset     = lane.left_offset_m;    // positive = drifting right
                warn_side_ = WarnSide::RIGHT;
            } else if (std::fabsf(lane.right_offset_m) > INTERVENE_THRESH_M) {
                offset     = -lane.right_offset_m;  // negate for left correction
                warn_side_ = WarnSide::LEFT;
            } else {
                // No longer departed
                torque_cmd_nm_ = 0.0f;
                lka_state_     = LKAState::READY;
                warn_side_     = WarnSide::NONE;
                break;
            }

            // Rate of change of offset (approx 20ms cycle)
            float rate = (offset - prev_offset_) / 0.02f;

            torque_cmd_nm_ = computeTorque(offset, rate);
            prev_offset_   = offset;
            break;
        }

        case LKAState::FAULT:
            torque_cmd_nm_ = 0.0f;
            break;
    }

    // Clamp final torque output
    torque_cmd_nm_ = std::max(-MAX_TORQUE_NM, std::min(torque_cmd_nm_, MAX_TORQUE_NM));
}

float LkaController::computeTorque(float offset_m, float rate_mps) {
    // PD controller: corrective torque proportional to offset + derivative
    // Negative offset (vehicle drifting right) → positive torque (steer left)
    float torque = -(KP * offset_m + KD * rate_mps);
    return torque;
}

void LkaController::getLKAStatusMsg(messages::MsgLKAStatus& status) const {
    status.state      = lka_state_;
    status.warn_side  = warn_side_;
    status.error_code = 0u;
}

void LkaController::getLKATorqueMsg(messages::MsgLKATorqueCmd& torque) const {
    torque.torque_nm = torque_cmd_nm_;
    torque.valid     = (lka_state_ == LKAState::INTERVENING);
}

void LkaController::getLDWMsg(messages::MsgLDWWarning& ldw) const {
    ldw.audio = ldw_active_;
    ldw.vis_l = ldw_left_;
    ldw.vis_r = ldw_right_;
}

} // namespace features
