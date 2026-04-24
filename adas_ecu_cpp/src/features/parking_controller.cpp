/**
 * @file    parking_controller.cpp
 * @brief   Parking assistance controller.
 */

#include "features/parking_controller.hpp"

namespace features {

// Threshold table: index → upper bound in cm
// Zone 0 = clear (>200), Zone 8 = critical (<20 → auto-brake)
static const uint16_t ZONE_UPPER[9] = {200, 150, 100, 75, 50, 35, 25, 20, 0};

uint8_t ParkingController::distToZone(uint16_t dist_cm) {
    for (uint8_t z = 0u; z < 8u; z++) {
        if (dist_cm >= ZONE_UPPER[z]) return z;
    }
    return 8u;  // Critical
}

void ParkingController::tick(const VehicleState& vehicle,
                              const ParkingModel& sensors,
                              const messages::MsgDriverInputs& driver)
{
    using Gear = messages::MsgGearShifter::Gear;

    switch (state_) {
        case State::OFF:
            zone_fl_ = zone_fr_ = zone_rl_ = zone_rr_ = 0u;
            auto_brake_ = false;

            // Auto-activate in reverse at low speed
            if (vehicle.gear == Gear::REVERSE && vehicle.speed_kph < MAX_SPEED_KPH) {
                state_ = State::ACTIVE;
            }
            // Manual activation via button
            if (driver.park_btn) {
                manually_activated_ = true;
                state_ = State::ACTIVE;
            }
            break;

        case State::ACTIVE: {
            // Deactivate conditions
            if (vehicle.speed_kph >= MAX_SPEED_KPH) {
                // Mute at higher speeds
                state_ = State::MUTED;
                break;
            }
            if (driver.park_btn && manually_activated_) {
                // Toggle off
                manually_activated_ = false;
                state_ = State::OFF;
                break;
            }
            if (vehicle.gear != Gear::REVERSE && !manually_activated_) {
                state_ = State::OFF;
                break;
            }

            if (!sensors.valid) break;

            // Compute proximity zones
            zone_fl_ = distToZone(sensors.fl_cm);
            zone_fr_ = distToZone(sensors.fr_cm);
            zone_rl_ = distToZone(sensors.rl_cm);
            zone_rr_ = distToZone(sensors.rr_cm);

            // Auto-brake: any rear sensor under critical threshold
            if (vehicle.is_reversing) {
                auto_brake_ = (sensors.rl_cm < AUTO_BRAKE_THRESHOLD_CM ||
                               sensors.rr_cm < AUTO_BRAKE_THRESHOLD_CM);
            } else {
                // Forward parking check
                auto_brake_ = (sensors.fl_cm < AUTO_BRAKE_THRESHOLD_CM ||
                               sensors.fr_cm < AUTO_BRAKE_THRESHOLD_CM);
            }
            break;
        }

        case State::MUTED:
            auto_brake_ = false;
            if (vehicle.speed_kph < MAX_SPEED_KPH * 0.8f) {
                state_ = State::ACTIVE;
            }
            break;

        case State::FAULT:
            auto_brake_ = false;
            break;
    }
}

void ParkingController::getParkStatusMsg(messages::MsgParkStatus& status) const {
    status.state     = state_;
    status.zone_fl   = zone_fl_;
    status.zone_fr   = zone_fr_;
    status.zone_rl   = zone_rl_;
    status.zone_rr   = zone_rr_;
    status.brake_cmd = auto_brake_;
}

} // namespace features
