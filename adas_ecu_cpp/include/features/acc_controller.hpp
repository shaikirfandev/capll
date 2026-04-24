/**
 * @file    acc_controller.hpp
 * @brief   Adaptive Cruise Control — longitudinal control state machine.
 *
 * Algorithm overview:
 *  1. Speed control mode: PID controller targeting set_speed
 *  2. Following mode: maintain time-gap to lead vehicle
 *  3. Emergency brake: if TTC < threshold, override with full deceleration
 *
 * State machine:
 *
 *      ┌─────────┐  set button   ┌──────────┐  radar valid  ┌─────────┐
 *      │  OFF    │ ─────────────>│ STANDBY  │ ─────────────>│ ACTIVE  │
 *      └─────────┘               └──────────┘               └────┬────┘
 *           ▲                         ▲                           │
 *           │ ignition off            │ cancel / brake            │ cancel/brake/
 *           │                         │ speed < min               │ fault
 *           │              ┌──────────┴───────┐                   │
 *           └──────────────│    OVERRIDDEN    │<──────────────────┘
 *                          └──────────────────┘
 *
 * Runs every 20ms.
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"
#include "features/sensor_fusion.hpp"

namespace features {

class AccController {
public:
    // ── Configuration constants ───────────────────────────────────────────────
    static constexpr float  MIN_SPEED_KPH       = 30.0f;   ///< Min ACC activation speed
    static constexpr float  MAX_SPEED_KPH       = 180.0f;  ///< Max set speed
    static constexpr float  MAX_DECEL_MPS2      = -4.5f;   ///< Max normal decel demand
    static constexpr float  EMERGENCY_DECEL_MPS2= -8.0f;   ///< AEB decel demand
    static constexpr float  MAX_ACCEL_MPS2      = +2.0f;   ///< Max acceleration demand
    static constexpr float  TTC_AEB_THRESHOLD_S = 1.5f;    ///< TTC for AEB trigger
    static constexpr float  TTC_WARN_THRESHOLD_S= 2.5f;    ///< TTC for decel start
    static constexpr float  MIN_FOLLOW_DIST_M   = 5.0f;    ///< Absolute min following distance
    static constexpr float  TIME_GAP_S          = 2.0f;    ///< Default following time gap

    // ── Feature state ─────────────────────────────────────────────────────────
    using State = messages::MsgACCStatus::State;

    static AccController& instance() {
        static AccController inst;
        return inst;
    }

    /**
     * @brief  Main control cycle. Call every 20ms.
     */
    void tick(const VehicleState& vehicle,
              const FrontTarget&  target,
              const messages::MsgDriverInputs& driver);

    /**
     * @brief  Populate CAN output messages from current state.
     */
    void getStatusMsg(messages::MsgACCStatus&  status) const;
    void getControlMsg(messages::MsgACCControl& ctrl)  const;

    State   getState()    const { return state_; }
    float   getSetSpeed() const { return set_speed_kph_; }
    bool    isAEBActive() const { return aeb_active_; }

private:
    AccController() = default;

    // ── State machine transitions ─────────────────────────────────────────────
    void handleOff(const messages::MsgDriverInputs& d, const VehicleState& v);
    void handleStandby(const messages::MsgDriverInputs& d, const VehicleState& v,
                       const FrontTarget& t);
    void handleActive(const messages::MsgDriverInputs& d, const VehicleState& v,
                      const FrontTarget& t);
    void handleOverride(const messages::MsgDriverInputs& d, const VehicleState& v);

    // ── Control algorithms ────────────────────────────────────────────────────

    /**
     * @brief Speed-hold PID controller.
     * @param current_kph  Current vehicle speed
     * @param target_kph   Desired speed
     * @return Acceleration demand in m/s²
     */
    float speedPidControl(float current_kph, float target_kph);

    /**
     * @brief Calculate following gap demand.
     * @param current_kph  Vehicle speed
     * @param target       Forward target data
     * @return Required deceleration/acceleration m/s²
     */
    float followingControl(float current_kph, const FrontTarget& target);

    /**
     * @brief Clamp acceleration demand to safe limits.
     * @param demand  Raw PID output
     * @return Clamped demand
     */
    float clampDemand(float demand) const;

    // ── PID state ─────────────────────────────────────────────────────────────
    struct PidState {
        float kp = 0.3f;
        float ki = 0.05f;
        float kd = 0.1f;
        float integral   = 0.0f;
        float prev_error = 0.0f;
    } pid_;

    // ── Output state ──────────────────────────────────────────────────────────
    State   state_               = State::OFF;
    float   set_speed_kph_       = 0.0f;
    float   accel_demand_mps2_   = 0.0f;
    float   brake_req_pct_       = 0.0f;
    float   throttle_req_pct_    = 0.0f;
    bool    aeb_active_          = false;
    uint8_t error_code_          = 0u;
    uint8_t gap_level_           = 3u;
};

} // namespace features
