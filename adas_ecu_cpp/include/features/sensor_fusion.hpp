/**
 * @file    sensor_fusion.hpp
 * @brief   Sensor fusion module — combines radar + camera + ultrasonic data
 *          into a unified environment model used by all ADAS features.
 *
 * Design pattern: "world model" singleton — all feature controllers
 * read from this, never directly from raw CAN messages.
 *
 * Runs at 20ms (50 Hz) — fastest sensor cycle in the system.
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_messages.hpp"

namespace features {

/**
 * @struct FrontTarget
 * @brief  Fused forward object from radar + optional camera confirmation.
 */
struct FrontTarget {
    float   distance_m      = 150.0f;   ///< [0..200] m — default far/clear
    float   rel_velocity_mps= 0.0f;     ///< negative = closing
    float   ttc_s           = 99.0f;    ///< time-to-collision
    bool    valid           = false;
    bool    camera_confirms = false;    ///< camera has detected same object
    messages::MsgRadarObject::ObjectType type
        = messages::MsgRadarObject::ObjectType::NONE;
};

/**
 * @struct LaneModel
 * @brief  Current lane boundary and deviation data from camera.
 */
struct LaneModel {
    float   left_offset_m   = 0.0f;    ///< lateral distance to left lane marking
    float   right_offset_m  = 0.0f;
    uint8_t left_quality    = 0u;      ///< 0=none 3=best
    uint8_t right_quality   = 0u;
    bool    ldw_left        = false;   ///< camera reports LDW event
    bool    ldw_right       = false;
    bool    valid           = false;
};

/**
 * @struct BlindZoneModel
 * @brief  Left and right blind zone occupancy (BSD radar).
 */
struct BlindZoneModel {
    bool    left_occupied   = false;
    bool    right_occupied  = false;
    float   left_dist_m     = 99.0f;
    float   right_dist_m    = 99.0f;
    bool    valid           = false;
};

/**
 * @struct ParkingModel
 * @brief  Proximity data from 4 ultrasonic sensors.
 */
struct ParkingModel {
    uint16_t fl_cm  = 300u;
    uint16_t fr_cm  = 300u;
    uint16_t rl_cm  = 300u;
    uint16_t rr_cm  = 300u;
    bool     valid  = false;

    uint16_t minRear()  const { return (rl_cm < rr_cm) ? rl_cm : rr_cm; }
    uint16_t minFront() const { return (fl_cm < fr_cm) ? fl_cm : fr_cm; }
};

/**
 * @struct VehicleState
 * @brief  Current vehicle motion state, fused from ABS + EPS + TCU.
 */
struct VehicleState {
    float   speed_kph       = 0.0f;
    float   steer_angle_deg = 0.0f;
    float   steer_rate_dps  = 0.0f;
    float   brake_pct       = 0.0f;
    float   accel_pct       = 0.0f;
    float   hill_gradient   = 0.0f;     ///< %, estimated from wheel speed delta
    bool    is_reversing    = false;
    bool    turn_left       = false;
    bool    turn_right      = false;
    messages::MsgGearShifter::Gear gear
        = messages::MsgGearShifter::Gear::PARK;
    bool    speed_valid     = false;
};

/**
 * @class SensorFusion
 * @brief Singleton world model — populated each 20ms cycle.
 *
 * Usage:
 *   SensorFusion& sf = SensorFusion::instance();
 *   sf.update(radar_msg, camera_msg, bsd_msg, ultrasonic_msg,
 *             speed_msg, steer_msg, driver_msg, gear_msg);
 *   float dist = sf.frontTarget().distance_m;
 */
class SensorFusion {
public:
    static SensorFusion& instance() {
        static SensorFusion inst;
        return inst;
    }

    /**
     * @brief Update world model from latest decoded CAN messages.
     *        Call once per 20ms control cycle.
     */
    void update(
        const messages::MsgRadarObject&   radar,
        const messages::MsgCameraLane&    camera,
        const messages::MsgBSDRadar&      bsd,
        const messages::MsgUltrasonic&    ultrasonic,
        const messages::MsgVehicleSpeed&  speed,
        const messages::MsgSteeringAngle& steer,
        const messages::MsgDriverInputs&  driver,
        const messages::MsgGearShifter&   gear
    );

    // ── Read accessors (const — features should not modify world model) ───────
    const FrontTarget&    frontTarget()   const { return front_target_; }
    const LaneModel&      laneModel()     const { return lane_model_; }
    const BlindZoneModel& blindZone()     const { return blind_zone_; }
    const ParkingModel&   parkingModel()  const { return parking_model_; }
    const VehicleState&   vehicleState()  const { return vehicle_state_; }

private:
    SensorFusion() = default;

    void fuseFrontTarget(const messages::MsgRadarObject& r,
                         const messages::MsgCameraLane&  c);
    float estimateGradient(const messages::MsgVehicleSpeed& v);

    FrontTarget    front_target_;
    LaneModel      lane_model_;
    BlindZoneModel blind_zone_;
    ParkingModel   parking_model_;
    VehicleState   vehicle_state_;

    // For gradient estimation (low-pass filtered)
    float speed_prev_    = 0.0f;
    float gradient_lpf_  = 0.0f;
};

} // namespace features
