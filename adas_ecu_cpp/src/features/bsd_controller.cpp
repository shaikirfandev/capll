/**
 * @file    bsd_controller.cpp
 * @brief   BSD controller implementation.
 */

#include "features/bsd_controller.hpp"

namespace features {

void BsdController::tick(const VehicleState& vehicle,
                          const BlindZoneModel& blind_zone,
                          const messages::MsgDriverInputs& driver)
{
    warn_left_  = false;
    warn_right_ = false;
    led_left_   = LedState::OFF;
    led_right_  = LedState::OFF;
    chime_      = false;

    // BSD inactive below minimum speed or while reversing
    if (vehicle.speed_kph < MIN_SPEED_KPH || vehicle.is_reversing) return;
    if (!blind_zone.valid) return;

    // ── Left blind zone ───────────────────────────────────────────────────────
    if (blind_zone.left_occupied && blind_zone.left_dist_m <= MAX_DIST_M) {
        warn_left_ = true;
        if (driver.turn_left) {
            // Driver signalling to merge into occupied zone → flash LED + chime
            led_left_ = LedState::FLASH;
            chime_    = true;
        } else {
            led_left_ = LedState::STEADY;
        }
    }

    // ── Right blind zone ──────────────────────────────────────────────────────
    if (blind_zone.right_occupied && blind_zone.right_dist_m <= MAX_DIST_M) {
        warn_right_ = true;
        if (driver.turn_right) {
            led_right_ = LedState::FLASH;
            chime_     = true;
        } else {
            led_right_ = LedState::STEADY;
        }
    }
}

void BsdController::getBSDStatusMsg(messages::MsgBSDStatus& status) const {
    status.warn_left  = warn_left_;
    status.warn_right = warn_right_;
    status.led_left   = led_left_;
    status.led_right  = led_right_;
    status.chime      = chime_;
}

} // namespace features
