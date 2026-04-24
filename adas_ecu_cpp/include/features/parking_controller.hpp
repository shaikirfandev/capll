/**
 * @file    parking_controller.hpp
 * @brief   Parking Assistance System controller.
 *
 * Uses 4 ultrasonic sensors (FL, FR, RL, RR) to compute proximity zones
 * and drive HMI display zones + audio tone zones.
 *
 * Zone definitions (distance thresholds in cm):
 *   Zone 0: >200cm  — clear (no display)
 *   Zone 1: 150–200 — far
 *   Zone 2: 100–150
 *   Zone 3:  75–100
 *   Zone 4:  50–75
 *   Zone 5:  35–50
 *   Zone 6:  25–35  — close
 *   Zone 7:  20–25  — critical
 *   Zone 8:  <20cm  — AUTO BRAKE triggered
 *
 * Activates automatically in reverse gear if speed <10 km/h.
 * Or manually via Park Assist button (forward parking also).
 *
 * Auto-brake command issued to braking system when any rear sensor < 20cm.
 *
 * Runs every 50ms.
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"
#include "features/sensor_fusion.hpp"

namespace features {

class ParkingController {
public:
    static constexpr float    MAX_SPEED_KPH           = 10.0f;
    static constexpr uint16_t AUTO_BRAKE_THRESHOLD_CM  = 20u;
    static constexpr uint16_t ZONE_THRESHOLDS_CM[]
        = {200u, 150u, 100u, 75u, 50u, 35u, 25u, 20u};

    using State = messages::MsgParkStatus::State;

    static ParkingController& instance() {
        static ParkingController inst;
        return inst;
    }

    void tick(const VehicleState&  vehicle,
              const ParkingModel&  sensors,
              const messages::MsgDriverInputs& driver);

    void getParkStatusMsg(messages::MsgParkStatus& status) const;

    State   getState() const { return state_; }
    bool    isAutoBrakeActive() const { return auto_brake_; }

private:
    ParkingController() = default;

    /** Map sensor distance (cm) to zone number 0–8 */
    static uint8_t distToZone(uint16_t dist_cm);

    State   state_      = State::OFF;
    uint8_t zone_fl_    = 0u;
    uint8_t zone_fr_    = 0u;
    uint8_t zone_rl_    = 0u;
    uint8_t zone_rr_    = 0u;
    bool    auto_brake_ = false;
    bool    manually_activated_ = false;
};

} // namespace features
