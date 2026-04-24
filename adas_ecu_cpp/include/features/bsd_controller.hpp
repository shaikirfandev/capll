/**
 * @file    bsd_controller.hpp
 * @brief   Blind Spot Detection controller.
 *
 * Monitors left and right blind zones via dedicated radar sensors.
 * Warns driver with mirror LEDs (steady → flashing when turn signal active).
 * Issues audio chime when turn signal activated with object in blind zone.
 *
 * Active above BSD_MIN_SPEED_KPH.
 * Suppressed when vehicle is reversing.
 *
 * LED states:
 *   No object   → LED off
 *   Object only → LED steady
 *   Object + turn signal → LED flashing + chime
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"
#include "features/sensor_fusion.hpp"

namespace features {

class BsdController {
public:
    static constexpr float  MIN_SPEED_KPH   = 12.0f;
    static constexpr float  MAX_DIST_M      = 6.0f;    ///< BSD detection range

    static BsdController& instance() {
        static BsdController inst;
        return inst;
    }

    void tick(const VehicleState&    vehicle,
              const BlindZoneModel&  blind_zone,
              const messages::MsgDriverInputs& driver);

    void getBSDStatusMsg(messages::MsgBSDStatus& status) const;

    bool isWarnLeft()  const { return warn_left_; }
    bool isWarnRight() const { return warn_right_; }

private:
    BsdController() = default;

    using LedState = messages::MsgBSDStatus::LedState;

    bool        warn_left_  = false;
    bool        warn_right_ = false;
    LedState    led_left_   = LedState::OFF;
    LedState    led_right_  = LedState::OFF;
    bool        chime_      = false;
};

} // namespace features
