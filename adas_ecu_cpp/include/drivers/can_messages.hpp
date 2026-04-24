/**
 * @file    can_messages.hpp
 * @brief   CAN message/signal codec: pack & unpack all ADAS ECU bus messages.
 *
 * Each struct represents one CAN message.
 * Encode() → builds raw CanFrame bytes from physical signal values.
 * Decode() → unpacks raw bytes into physical signal values.
 *
 * Signal encoding follows DBC conventions:
 *   Physical = (raw * factor) + offset
 *   Raw      = (physical - offset) / factor
 *
 * All byte ordering in this file is Intel (little-endian) unless noted.
 *
 * ┌─────────┬────────┬──────────────────────────────────────────┬──────┐
 * │ MSG ID  │ Cycle  │ Description                              │  DLC │
 * ├─────────┼────────┼──────────────────────────────────────────┼──────┤
 * │ 0x100   │  10ms  │ VehicleSpeed                             │   8  │
 * │ 0x101   │  10ms  │ SteeringAngle                            │   8  │
 * │ 0x102   │  10ms  │ WheelSpeeds                              │   8  │
 * │ 0x200   │  20ms  │ RadarObject (forward)                    │   8  │
 * │ 0x201   │  20ms  │ CameraLane                               │   8  │
 * │ 0x202   │  20ms  │ BSD_Radar (left/right)                   │   8  │
 * │ 0x203   │  50ms  │ UltrasonicSensors (parking)              │   8  │
 * │ 0x300   │  20ms  │ ACC_Status     (ECU → bus)               │   8  │
 * │ 0x301   │  20ms  │ ACC_Control    (ECU → bus)               │   8  │
 * │ 0x302   │  20ms  │ LKA_Status     (ECU → bus)               │   8  │
 * │ 0x303   │  20ms  │ LKA_TorqueCmd  (ECU → bus)               │   8  │
 * │ 0x304   │  20ms  │ BSD_Status     (ECU → bus)               │   8  │
 * │ 0x305   │  50ms  │ Park_Status    (ECU → bus)               │   8  │
 * │ 0x306   │  20ms  │ HHA_Status     (ECU → bus)               │   8  │
 * │ 0x400   │  20ms  │ DriverInputs   (BCM → ADAS ECU)          │   8  │
 * │ 0x401   │  20ms  │ GearShifter    (TCU → ADAS ECU)          │   8  │
 * │ 0x500   │ 100ms  │ LDW_Warning    (ECU → HMI)               │   3  │
 * └─────────┴────────┴──────────────────────────────────────────┴──────┘
 */

#pragma once
#include "hal/hal_types.hpp"
#include "drivers/can_driver.hpp"

namespace messages {

using namespace drivers;

// ═══════════════════════════════════════════════════════════════════════════════
// INPUT MESSAGES (received by ADAS ECU)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * @struct MsgVehicleSpeed  ID=0x100  Cycle=10ms
 * @brief  Vehicle speed from ABS/Brake controller.
 *
 * Signal layout:
 *   Byte 0-1:  VehicleSpeed_raw  [0..65535] factor=0.01 offset=0  unit=km/h
 *   Byte 2:    SpeedValid        [0/1]
 *   Byte 3:    Direction         [0=fwd, 1=rev]
 */
struct MsgVehicleSpeed {
    static constexpr uint32_t ID    = 0x100u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 10u;   // ms

    // Physical values (populated by Decode)
    float    speed_kph    = 0.0f;   ///< [0..655.35] km/h
    bool     valid        = false;
    bool     reverse      = false;

    void decode(const CanFrame& f) {
        uint16_t raw = static_cast<uint16_t>((f.data[1] << 8u) | f.data[0]);
        speed_kph    = raw * 0.01f;
        valid        = (f.data[2] & 0x01u) != 0u;
        reverse      = (f.data[3] & 0x01u) != 0u;
    }
};

/**
 * @struct MsgSteeringAngle  ID=0x101  Cycle=10ms
 * @brief  Steering wheel angle from EPS controller.
 *
 *   Byte 0-1:  Angle_raw  signed int16  factor=0.1  offset=0  unit=deg
 *              Positive = left turn
 *   Byte 2:    AngularRate_raw  int8  factor=1  offset=0  unit=deg/s
 *   Byte 3-bit0: Valid
 */
struct MsgSteeringAngle {
    static constexpr uint32_t ID    = 0x101u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 10u;

    float   angle_deg     = 0.0f;   ///< [-3276.8..+3276.7] deg
    float   rate_deg_s    = 0.0f;   ///< deg/s
    bool    valid         = false;

    void decode(const CanFrame& f) {
        int16_t raw_angle  = static_cast<int16_t>((f.data[1] << 8u) | f.data[0]);
        int8_t  raw_rate   = static_cast<int8_t>(f.data[2]);
        angle_deg          = raw_angle * 0.1f;
        rate_deg_s         = static_cast<float>(raw_rate);
        valid              = (f.data[3] & 0x01u) != 0u;
    }
};

/**
 * @struct MsgWheelSpeeds  ID=0x102  Cycle=10ms
 * @brief  Individual wheel speeds from ABS.
 *
 *   Byte 0-1: FL_raw  uint16  factor=0.01  unit=km/h
 *   Byte 2-3: FR_raw  uint16  factor=0.01  unit=km/h
 *   Byte 4-5: RL_raw  uint16  factor=0.01  unit=km/h
 *   Byte 6-7: RR_raw  uint16  factor=0.01  unit=km/h
 */
struct MsgWheelSpeeds {
    static constexpr uint32_t ID    = 0x102u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 10u;

    float   fl_kph = 0.0f;
    float   fr_kph = 0.0f;
    float   rl_kph = 0.0f;
    float   rr_kph = 0.0f;

    void decode(const CanFrame& f) {
        auto raw = [&](int i) { return static_cast<uint16_t>((f.data[i+1] << 8u) | f.data[i]); };
        fl_kph = raw(0) * 0.01f;
        fr_kph = raw(2) * 0.01f;
        rl_kph = raw(4) * 0.01f;
        rr_kph = raw(6) * 0.01f;
    }
};

/**
 * @struct MsgRadarObject  ID=0x200  Cycle=20ms
 * @brief  Forward-looking radar primary target from radar module.
 *
 *   Byte 0-1: Distance_raw  uint16  factor=0.01  offset=0   unit=m  [0..655.35]
 *   Byte 2-3: RelVelocity_raw int16  factor=0.01  offset=0  unit=m/s [-327..327]
 *   Byte 4:   ObjectValid  [0/1]
 *   Byte 5:   ObjectType   [0=none,1=car,2=truck,3=moto,4=ped]
 *   Byte 6:   TTC_raw  uint8  factor=0.1   unit=s  [0..25.5s]
 */
struct MsgRadarObject {
    static constexpr uint32_t ID    = 0x200u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    enum class ObjectType : uint8_t {
        NONE        = 0,
        CAR         = 1,
        TRUCK       = 2,
        MOTORCYCLE  = 3,
        PEDESTRIAN  = 4,
    };

    float       distance_m      = 0.0f;
    float       rel_velocity_mps= 0.0f;   ///< negative = closing
    float       ttc_s           = 0.0f;   ///< time-to-collision
    bool        valid           = false;
    ObjectType  type            = ObjectType::NONE;

    void decode(const CanFrame& f) {
        uint16_t raw_dist = static_cast<uint16_t>((f.data[1] << 8u) | f.data[0]);
        int16_t  raw_vel  = static_cast<int16_t>((f.data[3] << 8u) | f.data[2]);
        distance_m        = raw_dist * 0.01f;
        rel_velocity_mps  = raw_vel  * 0.01f;
        valid             = (f.data[4] & 0x01u) != 0u;
        type              = static_cast<ObjectType>(f.data[5] & 0x07u);
        ttc_s             = f.data[6] * 0.1f;
    }
};

/**
 * @struct MsgCameraLane  ID=0x201  Cycle=20ms
 * @brief  Lane detection data from front camera.
 *
 *   Byte 0:   LeftQuality   [0..3]  3=clear
 *   Byte 1:   RightQuality  [0..3]
 *   Byte 2-3: LeftOffset_raw  int16  factor=0.001  unit=m  (depart positive=right)
 *   Byte 4-5: RightOffset_raw int16  factor=0.001  unit=m
 *   Byte 6:   LDW_LeftActive  [0/1]
 *   Byte 7:   LDW_RightActive [0/1]
 */
struct MsgCameraLane {
    static constexpr uint32_t ID    = 0x201u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    float   left_offset_m   = 0.0f;  ///< positive = drifting right of left lane
    float   right_offset_m  = 0.0f;
    uint8_t left_quality    = 0u;    ///< 0=none, 1=weak, 2=good, 3=very good
    uint8_t right_quality   = 0u;
    bool    ldw_left_active = false;
    bool    ldw_right_active= false;

    void decode(const CanFrame& f) {
        left_quality   = f.data[0] & 0x03u;
        right_quality  = f.data[1] & 0x03u;
        int16_t lo     = static_cast<int16_t>((f.data[3] << 8u) | f.data[2]);
        int16_t ro     = static_cast<int16_t>((f.data[5] << 8u) | f.data[4]);
        left_offset_m  = lo * 0.001f;
        right_offset_m = ro * 0.001f;
        ldw_left_active  = (f.data[6] & 0x01u) != 0u;
        ldw_right_active = (f.data[7] & 0x01u) != 0u;
    }
};

/**
 * @struct MsgBSDRadar  ID=0x202  Cycle=20ms
 * @brief  Left/Right blind-spot radar detections.
 *
 *   Byte 0:   LeftDetected   [0/1]
 *   Byte 1:   RightDetected  [0/1]
 *   Byte 2:   LeftDist_raw   uint8  factor=0.1  unit=m  [0..25.5]
 *   Byte 3:   RightDist_raw  uint8  factor=0.1  unit=m
 *   Byte 4:   LeftRelVel_raw  int8  factor=0.5  unit=m/s
 *   Byte 5:   RightRelVel_raw int8  factor=0.5  unit=m/s
 */
struct MsgBSDRadar {
    static constexpr uint32_t ID    = 0x202u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    bool    left_detected   = false;
    bool    right_detected  = false;
    float   left_dist_m     = 0.0f;
    float   right_dist_m    = 0.0f;
    float   left_rel_vel    = 0.0f;
    float   right_rel_vel   = 0.0f;

    void decode(const CanFrame& f) {
        left_detected  = (f.data[0] & 0x01u) != 0u;
        right_detected = (f.data[1] & 0x01u) != 0u;
        left_dist_m    = f.data[2] * 0.1f;
        right_dist_m   = f.data[3] * 0.1f;
        left_rel_vel   = static_cast<int8_t>(f.data[4]) * 0.5f;
        right_rel_vel  = static_cast<int8_t>(f.data[5]) * 0.5f;
    }
};

/**
 * @struct MsgUltrasonic  ID=0x203  Cycle=50ms
 * @brief  4 ultrasonic sensor distances (parking assistance).
 *
 *   Byte 0: FL_raw  uint8  factor=2  unit=cm  [0..510]
 *   Byte 1: FR_raw  uint8  factor=2  unit=cm
 *   Byte 2: RL_raw  uint8  factor=2  unit=cm
 *   Byte 3: RR_raw  uint8  factor=2  unit=cm
 *   Byte 4: ValidFlags  [bit0=FL, bit1=FR, bit2=RL, bit3=RR]
 */
struct MsgUltrasonic {
    static constexpr uint32_t ID    = 0x203u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 50u;

    uint16_t fl_cm = 0u;
    uint16_t fr_cm = 0u;
    uint16_t rl_cm = 0u;
    uint16_t rr_cm = 0u;
    bool     fl_valid = false;
    bool     fr_valid = false;
    bool     rl_valid = false;
    bool     rr_valid = false;

    void decode(const CanFrame& f) {
        fl_cm    = static_cast<uint16_t>(f.data[0]) * 2u;
        fr_cm    = static_cast<uint16_t>(f.data[1]) * 2u;
        rl_cm    = static_cast<uint16_t>(f.data[2]) * 2u;
        rr_cm    = static_cast<uint16_t>(f.data[3]) * 2u;
        fl_valid = (f.data[4] & BIT(0)) != 0u;
        fr_valid = (f.data[4] & BIT(1)) != 0u;
        rl_valid = (f.data[4] & BIT(2)) != 0u;
        rr_valid = (f.data[4] & BIT(3)) != 0u;
    }
};

/**
 * @struct MsgDriverInputs  ID=0x400  Cycle=20ms
 * @brief  Driver switch/button states from BCM.
 *
 *   Byte 0 bit0: ACC_SetButton
 *   Byte 0 bit1: ACC_CancelButton
 *   Byte 0 bit2: ACC_ResumeButton
 *   Byte 0 bit3: LKA_ToggleButton
 *   Byte 0 bit4: ParkAssistButton
 *   Byte 1:      ACC_SetSpeed_raw  uint8  factor=1  unit=km/h
 *   Byte 2 bit0: TurnSignalLeft
 *   Byte 2 bit1: TurnSignalRight
 *   Byte 3:      BrakePedalPct    uint8  factor=0.4  unit=%  [0..100]
 *   Byte 4:      AccelPedalPct    uint8  factor=0.4  unit=%  [0..100]
 */
struct MsgDriverInputs {
    static constexpr uint32_t ID    = 0x400u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    bool    acc_set         = false;
    bool    acc_cancel      = false;
    bool    acc_resume      = false;
    bool    lka_toggle      = false;
    bool    park_btn        = false;
    uint8_t acc_set_speed   = 0u;      ///< km/h
    bool    turn_left       = false;
    bool    turn_right      = false;
    float   brake_pct       = 0.0f;
    float   accel_pct       = 0.0f;

    void decode(const CanFrame& f) {
        acc_set       = (f.data[0] & BIT(0)) != 0u;
        acc_cancel    = (f.data[0] & BIT(1)) != 0u;
        acc_resume    = (f.data[0] & BIT(2)) != 0u;
        lka_toggle    = (f.data[0] & BIT(3)) != 0u;
        park_btn      = (f.data[0] & BIT(4)) != 0u;
        acc_set_speed = f.data[1];
        turn_left     = (f.data[2] & BIT(0)) != 0u;
        turn_right    = (f.data[2] & BIT(1)) != 0u;
        brake_pct     = f.data[3] * 0.4f;
        accel_pct     = f.data[4] * 0.4f;
    }
};

/**
 * @struct MsgGearShifter  ID=0x401  Cycle=20ms
 * @brief  Current gear position from TCU.
 *
 *   Byte 0: GearPos  [0=P, 1=R, 2=N, 3=D, 4=S, 5=L]
 *   Byte 1: Valid
 */
struct MsgGearShifter {
    static constexpr uint32_t ID    = 0x401u;
    static constexpr uint8_t  DLC   = 4u;
    static constexpr uint32_t CYCLE = 20u;

    enum class Gear : uint8_t {
        PARK    = 0,
        REVERSE = 1,
        NEUTRAL = 2,
        DRIVE   = 3,
        SPORT   = 4,
        LOW     = 5,
    };

    Gear    pos   = Gear::PARK;
    bool    valid = false;

    void decode(const CanFrame& f) {
        pos   = static_cast<Gear>(f.data[0] & 0x07u);
        valid = (f.data[1] & 0x01u) != 0u;
    }
};

// ═══════════════════════════════════════════════════════════════════════════════
// OUTPUT MESSAGES (transmitted by ADAS ECU)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * @struct MsgACCStatus  ID=0x300  Cycle=20ms
 * @brief  ACC system status output from ADAS ECU to HMI and gateway.
 *
 *   Byte 0:   ACC_Sts     [0=OFF, 1=STANDBY, 2=ACTIVE, 3=OVERRIDE, 255=FAULT]
 *   Byte 1:   ACC_SetSpd  uint8 factor=1  unit=km/h
 *   Byte 2:   ACC_Gap     [1..5] following gap level
 *   Byte 3:   ACC_ErrCode uint8
 */
struct MsgACCStatus {
    static constexpr uint32_t ID    = 0x300u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    enum class State : uint8_t {
        OFF      = 0,
        STANDBY  = 1,
        ACTIVE   = 2,
        OVERRIDE = 3,
        FAULT    = 255,
    };

    State   state       = State::OFF;
    uint8_t set_speed   = 0u;
    uint8_t gap_level   = 3u;   ///< 1=close .. 5=far
    uint8_t error_code  = 0u;

    void encode(CanFrame& f) const {
        f.id          = ID;
        f.dlc         = DLC;
        f.data[0]     = static_cast<uint8_t>(state);
        f.data[1]     = set_speed;
        f.data[2]     = gap_level;
        f.data[3]     = error_code;
        // bytes 4-7 reserved = 0
    }
};

/**
 * @struct MsgACCControl  ID=0x301  Cycle=20ms
 * @brief  ACC longitudinal control demand to brake/throttle controllers.
 *
 *   Byte 0-1: AccelDemand_raw  int16  factor=0.001  unit=m/s²  [-8..+4]
 *   Byte 2:   BrakeReq_raw  uint8  factor=0.4  unit=%  [0..100]
 *   Byte 3:   ThrottleReq_raw  uint8  factor=0.4  unit=%
 *   Byte 4:   EmergencyBrake  [0/1]  (AEB command)
 */
struct MsgACCControl {
    static constexpr uint32_t ID    = 0x301u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    float   accel_demand_mps2   = 0.0f; ///< [-8..+4] m/s²
    float   brake_req_pct       = 0.0f;
    float   throttle_req_pct    = 0.0f;
    bool    emergency_brake     = false;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        int16_t accel_raw = static_cast<int16_t>(accel_demand_mps2 / 0.001f);
        f.data[0] = static_cast<uint8_t>(accel_raw & 0xFFu);
        f.data[1] = static_cast<uint8_t>((accel_raw >> 8u) & 0xFFu);
        f.data[2] = static_cast<uint8_t>(brake_req_pct    / 0.4f);
        f.data[3] = static_cast<uint8_t>(throttle_req_pct / 0.4f);
        f.data[4] = emergency_brake ? 0x01u : 0x00u;
    }
};

/**
 * @struct MsgLKAStatus  ID=0x302  Cycle=20ms
 *   Byte 0: LKA_Sts   [0=OFF, 1=READY, 2=PREPARING, 3=INTERVENING, 255=FAULT]
 *   Byte 1: LKA_SideWarn  [0=none, 1=left, 2=right]
 */
struct MsgLKAStatus {
    static constexpr uint32_t ID    = 0x302u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    enum class State : uint8_t {
        OFF          = 0,
        READY        = 1,
        PREPARING    = 2,
        INTERVENING  = 3,
        FAULT        = 255,
    };
    enum class WarnSide : uint8_t { NONE=0, LEFT=1, RIGHT=2 };

    State    state    = State::OFF;
    WarnSide warn_side= WarnSide::NONE;
    uint8_t  error_code = 0u;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        f.data[0] = static_cast<uint8_t>(state);
        f.data[1] = static_cast<uint8_t>(warn_side);
        f.data[2] = error_code;
    }
};

/**
 * @struct MsgLKATorqueCmd  ID=0x303  Cycle=20ms
 *   Byte 0-1: TorqueOverride_raw  int16  factor=0.01  unit=Nm  [-5..+5]
 *   Byte 2:   TorqueValid [0/1]
 */
struct MsgLKATorqueCmd {
    static constexpr uint32_t ID    = 0x303u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    float   torque_nm   = 0.0f;
    bool    valid       = false;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        int16_t raw = static_cast<int16_t>(torque_nm / 0.01f);
        f.data[0] = static_cast<uint8_t>(raw & 0xFFu);
        f.data[1] = static_cast<uint8_t>((raw >> 8u) & 0xFFu);
        f.data[2] = valid ? 0x01u : 0x00u;
    }
};

/**
 * @struct MsgBSDStatus  ID=0x304  Cycle=20ms
 *   Byte 0: BSD_Warn_L  [0/1]
 *   Byte 1: BSD_Warn_R  [0/1]
 *   Byte 2: BSD_LED_L   [0=off,1=steady,2=flash]
 *   Byte 3: BSD_LED_R
 *   Byte 4: BSD_Chime   [0/1]
 */
struct MsgBSDStatus {
    static constexpr uint32_t ID    = 0x304u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    enum class LedState : uint8_t { OFF=0, STEADY=1, FLASH=2 };

    bool        warn_left   = false;
    bool        warn_right  = false;
    LedState    led_left    = LedState::OFF;
    LedState    led_right   = LedState::OFF;
    bool        chime       = false;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        f.data[0] = warn_left  ? 0x01u : 0x00u;
        f.data[1] = warn_right ? 0x01u : 0x00u;
        f.data[2] = static_cast<uint8_t>(led_left);
        f.data[3] = static_cast<uint8_t>(led_right);
        f.data[4] = chime ? 0x01u : 0x00u;
    }
};

/**
 * @struct MsgParkStatus  ID=0x305  Cycle=50ms
 *   Byte 0: Park_Sts    [0=OFF, 1=ACTIVE, 2=MUTED, 255=FAULT]
 *   Byte 1: ZoneFL      [0..8]
 *   Byte 2: ZoneFR      [0..8]
 *   Byte 3: ZoneRL      [0..8]
 *   Byte 4: ZoneRR      [0..8]
 *   Byte 5: BrakeCmdActive [0/1] — ECU commanding auto-brake
 */
struct MsgParkStatus {
    static constexpr uint32_t ID    = 0x305u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 50u;

    enum class State : uint8_t { OFF=0, ACTIVE=1, MUTED=2, FAULT=255 };

    State   state   = State::OFF;
    uint8_t zone_fl = 0u;
    uint8_t zone_fr = 0u;
    uint8_t zone_rl = 0u;
    uint8_t zone_rr = 0u;
    bool    brake_cmd = false;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        f.data[0] = static_cast<uint8_t>(state);
        f.data[1] = zone_fl;
        f.data[2] = zone_fr;
        f.data[3] = zone_rl;
        f.data[4] = zone_rr;
        f.data[5] = brake_cmd ? 0x01u : 0x00u;
    }
};

/**
 * @struct MsgHHAStatus  ID=0x306  Cycle=20ms
 *   Byte 0: HHA_Sts    [0=OFF, 1=READY, 2=HOLDING, 3=RELEASING, 255=FAULT]
 *   Byte 1-2: HoldDuration_raw uint16 factor=1 unit=ms
 *   Byte 3: GradientPct_raw uint8 factor=0.5 unit=%
 */
struct MsgHHAStatus {
    static constexpr uint32_t ID    = 0x306u;
    static constexpr uint8_t  DLC   = 8u;
    static constexpr uint32_t CYCLE = 20u;

    enum class State : uint8_t { OFF=0, READY=1, HOLDING=2, RELEASING=3, FAULT=255 };

    State    state         = State::OFF;
    uint16_t hold_duration = 0u;   ///< ms
    float    gradient_pct  = 0.0f;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        f.data[0] = static_cast<uint8_t>(state);
        f.data[1] = static_cast<uint8_t>(hold_duration & 0xFFu);
        f.data[2] = static_cast<uint8_t>((hold_duration >> 8u) & 0xFFu);
        f.data[3] = static_cast<uint8_t>(gradient_pct / 0.5f);
    }
};

/**
 * @struct MsgLDWWarning  ID=0x500  Cycle=100ms
 *   Byte 0: AudioWarning [0/1]
 *   Byte 1: VisualLeft   [0/1]
 *   Byte 2: VisualRight  [0/1]
 */
struct MsgLDWWarning {
    static constexpr uint32_t ID    = 0x500u;
    static constexpr uint8_t  DLC   = 3u;
    static constexpr uint32_t CYCLE = 100u;

    bool audio  = false;
    bool vis_l  = false;
    bool vis_r  = false;

    void encode(CanFrame& f) const {
        f.id = ID; f.dlc = DLC;
        f.data[0] = audio ? 0x01u : 0x00u;
        f.data[1] = vis_l ? 0x01u : 0x00u;
        f.data[2] = vis_r ? 0x01u : 0x00u;
    }
};

} // namespace messages
