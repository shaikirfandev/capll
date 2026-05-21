/**
 * @file    acc_ecu.cpp
 * @brief   Adaptive Cruise Control — Full ECU Simulation
 * @details Implements ACC with radar-based lead vehicle tracking,
 *          PID speed controller, safe following distance enforcement,
 *          and cut-in/cut-out scenario handling.
 *
 * Compile: g++ -std=c++17 -Wall -Wextra -O2 acc_ecu.cpp -o acc_ecu
 */

#include <cstdint>
#include <cstddef>
#include <cmath>
#include <cassert>
#include <array>
#include <algorithm>
#include <iostream>
#include <iomanip>

// ============================================================================
// TYPES
// ============================================================================

enum class AccState : uint8_t {
    INACTIVE       = 0U,
    SPEED_CONTROL  = 1U,   // No lead vehicle — maintaining set speed
    FOLLOWING      = 2U,   // Lead vehicle detected — following at safe distance
    BRAKING        = 3U,   // Active braking to close gap or emergency
    OVERRIDE       = 4U,   // Driver pedal override
    FAULT          = 5U,
};

struct RadarObject {
    bool    valid            = false;
    float   distanceM        = 999.0F;  // Distance to target (m)
    float   relativeSpeedMps = 0.0F;    // Relative speed: negative = closing
    float   azimuthDeg       = 0.0F;    // Lateral angle
    uint8_t objectId         = 0U;
};

struct AccInputs {
    float       vehicleSpeedMps   = 0.0F;   // Ego vehicle speed
    float       setSpeedMps       = 0.0F;   // Driver-set cruise speed
    float       setTimeGapS       = 2.0F;   // Following time gap (default: 2.0s)
    RadarObject leadVehicle       = {};     // Closest in-path radar object
    float       brakeInput        = 0.0F;   // Driver brake pedal [0..1]
    float       accelInput        = 0.0F;   // Driver accelerator [0..1]
    bool        accEnableSwitch   = false;
    bool        radarFaultActive  = false;
    uint32_t    timestamp_ms      = 0U;
};

struct AccOutputs {
    float       targetAccelMps2   = 0.0F;  // Commanded acceleration (+) or deceleration (-)
    float       throttleRequest   = 0.0F;  // [0..1] to engine/motor
    float       brakeRequest      = 0.0F;  // [0..1] to brake system
    AccState    state             = AccState::INACTIVE;
    const char* stateString       = "INACTIVE";
    float       targetSpeed       = 0.0F;  // Internal target speed for display
    float       actualGapM        = 999.0F;
    float       desiredGapM       = 999.0F;
};

// ============================================================================
// SAFE FOLLOWING DISTANCE CALCULATOR
// ============================================================================

class SafeDistanceCalculator {
public:
    static constexpr float MIN_GAP_M          = 5.0F;   // Absolute minimum gap
    static constexpr float DEFAULT_TIME_GAP_S = 2.0F;   // 2-second rule

    /**
     * Calculate minimum safe following distance.
     * Based on: time-gap model + stopping distance difference.
     *
     * @param egoSpeedMps  Ego vehicle speed
     * @param timeGapS     Desired time headway (2s default, driver selectable)
     * @return             Desired gap in metres
     */
    static float computeDesiredGap(float egoSpeedMps, float timeGapS) noexcept {
        // Time-gap model: gap = v * t_gap
        float timeGapModel = egoSpeedMps * timeGapS;

        // Minimum stopping distance buffer (2m at standstill)
        return std::max(MIN_GAP_M, timeGapModel);
    }

    /**
     * Compute required deceleration to reach safe gap.
     * Uses simple kinematic model.
     */
    static float computeGapError(float currentGapM, float desiredGapM,
                                  float relSpeedMps) noexcept {
        float gapError    = currentGapM - desiredGapM;   // + = too far, - = too close
        // Add velocity term: if closing fast, need to react early
        float closingTerm = relSpeedMps * 0.5F;          // relSpeed negative = closing
        return gapError + closingTerm;
    }
};

// ============================================================================
// PID CONTROLLER (reused from LKA module — same pattern)
// ============================================================================

class PidController {
public:
    struct Params {
        float kp, ki, kd;
        float outputMin, outputMax;
        float integralClamp;
    };

    explicit PidController(Params p) noexcept : p_(p) {}

    float compute(float error, float dt_s) noexcept {
        if (dt_s <= 0.0F) { return 0.0F; }
        integral_  += error * dt_s;
        integral_   = std::clamp(integral_, -p_.integralClamp, p_.integralClamp);
        float deriv = (error - prevErr_) / dt_s;
        prevErr_    = error;
        return std::clamp(p_.kp*error + p_.ki*integral_ + p_.kd*deriv,
                          p_.outputMin, p_.outputMax);
    }
    void reset() noexcept { integral_ = 0.0F; prevErr_ = 0.0F; }

private:
    Params p_;
    float  integral_ = 0.0F;
    float  prevErr_  = 0.0F;
};

// ============================================================================
// ACC STATE MACHINE
// ============================================================================

class AccStateMachine {
public:
    static constexpr float MIN_SPEED_MPS       = 5.0F;    // 18 km/h
    static constexpr float LEAD_DETECT_RANGE_M = 150.0F;  // Lead vehicle detection range
    static constexpr float LEAD_LOST_RANGE_M   = 160.0F;  // Hysteresis

    AccState process(const AccInputs& in) noexcept {
        switch (state_) {
        case AccState::INACTIVE:       return processInactive(in);
        case AccState::SPEED_CONTROL:  return processSpeedControl(in);
        case AccState::FOLLOWING:      return processFollowing(in);
        case AccState::BRAKING:        return processBraking(in);
        case AccState::OVERRIDE:       return processOverride(in);
        case AccState::FAULT:          return processFault(in);
        }
        return state_;
    }

    AccState getState() const noexcept { return state_; }

private:
    AccState state_ = AccState::INACTIVE;

    bool hasLeadVehicle(const AccInputs& in) const noexcept {
        return in.leadVehicle.valid
            && in.leadVehicle.distanceM < LEAD_DETECT_RANGE_M
            && std::abs(in.leadVehicle.azimuthDeg) < 5.0F;  // In-path check
    }

    AccState processInactive(const AccInputs& in) noexcept {
        if (in.accEnableSwitch && !in.radarFaultActive
            && in.vehicleSpeedMps >= MIN_SPEED_MPS
            && in.brakeInput < 0.05F) {
            state_ = hasLeadVehicle(in) ? AccState::FOLLOWING : AccState::SPEED_CONTROL;
        }
        return state_;
    }

    AccState processSpeedControl(const AccInputs& in) noexcept {
        if (!in.accEnableSwitch || in.radarFaultActive) {
            state_ = AccState::INACTIVE; return state_;
        }
        if (in.brakeInput > 0.1F || in.accelInput > 0.5F) {
            state_ = AccState::OVERRIDE; return state_;
        }
        if (hasLeadVehicle(in)) {
            state_ = AccState::FOLLOWING;
        }
        return state_;
    }

    AccState processFollowing(const AccInputs& in) noexcept {
        if (!in.accEnableSwitch || in.radarFaultActive) {
            state_ = AccState::INACTIVE; return state_;
        }
        if (in.brakeInput > 0.1F) {
            state_ = AccState::OVERRIDE; return state_;
        }
        if (!hasLeadVehicle(in)) {
            state_ = AccState::SPEED_CONTROL; return state_;
        }
        // Emergency braking: gap < 0.5 * desired
        float desired = SafeDistanceCalculator::computeDesiredGap(
            in.vehicleSpeedMps, in.setTimeGapS);
        if (in.leadVehicle.distanceM < desired * 0.5F) {
            state_ = AccState::BRAKING;
        }
        return state_;
    }

    AccState processBraking(const AccInputs& in) noexcept {
        if (!in.accEnableSwitch) { state_ = AccState::INACTIVE; return state_; }
        if (in.brakeInput > 0.3F) { state_ = AccState::OVERRIDE; return state_; }
        float desired = SafeDistanceCalculator::computeDesiredGap(
            in.vehicleSpeedMps, in.setTimeGapS);
        // Exit braking when gap is restored
        if (in.leadVehicle.distanceM > desired * 0.9F) {
            state_ = AccState::FOLLOWING;
        }
        return state_;
    }

    AccState processOverride(const AccInputs& in) noexcept {
        if (!in.accEnableSwitch) { state_ = AccState::INACTIVE; return state_; }
        if (in.brakeInput < 0.05F && in.accelInput < 0.05F) {
            state_ = hasLeadVehicle(in) ? AccState::FOLLOWING : AccState::SPEED_CONTROL;
        }
        return state_;
    }

    AccState processFault(const AccInputs& in) noexcept {
        (void)in; return state_;
    }
};

// ============================================================================
// ACC CONTROLLER
// ============================================================================

class AccController {
public:
    AccController()
        : speedPid_(PidController::Params{1.2F, 0.1F, 0.08F, -3.5F, 2.0F, 5.0F}),
          gapPid_(  PidController::Params{0.5F, 0.05F, 0.1F, -4.0F, 2.0F, 8.0F}) {}

    AccOutputs process(const AccInputs& in) noexcept {
        AccOutputs out{};
        uint32_t dt_ms = (lastTs_ == 0U) ? 20U : (in.timestamp_ms - lastTs_);
        lastTs_ = in.timestamp_ms;
        float dt_s = static_cast<float>(dt_ms) / 1000.0F;

        AccState state = sm_.process(in);
        out.state      = state;

        switch (state) {
        case AccState::INACTIVE:
            speedPid_.reset();
            gapPid_.reset();
            out.stateString = "INACTIVE";
            break;

        case AccState::SPEED_CONTROL: {
            float speedError  = in.setSpeedMps - in.vehicleSpeedMps;
            float accelCmd    = speedPid_.compute(speedError, dt_s);
            out.targetAccelMps2 = accelCmd;
            out.targetSpeed     = in.setSpeedMps;
            mapAccelToActuators(accelCmd, out);
            out.stateString = "SPEED_CTRL";
            break;
        }

        case AccState::FOLLOWING: {
            float desired     = SafeDistanceCalculator::computeDesiredGap(
                                    in.vehicleSpeedMps, in.setTimeGapS);
            float gapError    = SafeDistanceCalculator::computeGapError(
                                    in.leadVehicle.distanceM, desired,
                                    in.leadVehicle.relativeSpeedMps);
            float accelCmd    = gapPid_.compute(gapError, dt_s);

            // Never exceed set speed when following
            float setErr      = in.setSpeedMps - in.vehicleSpeedMps;
            accelCmd          = std::min(accelCmd, speedPid_.compute(setErr, dt_s));
            accelCmd          = std::clamp(accelCmd, -3.5F, 1.5F);

            out.targetAccelMps2 = accelCmd;
            out.desiredGapM     = desired;
            out.actualGapM      = in.leadVehicle.distanceM;
            out.targetSpeed     = in.setSpeedMps;
            mapAccelToActuators(accelCmd, out);
            out.stateString = "FOLLOWING";
            break;
        }

        case AccState::BRAKING: {
            // Maximum deceleration (within comfort zone: -3.5 m/s²)
            float desired  = SafeDistanceCalculator::computeDesiredGap(
                                 in.vehicleSpeedMps, in.setTimeGapS);
            float gapError = SafeDistanceCalculator::computeGapError(
                                 in.leadVehicle.distanceM, desired,
                                 in.leadVehicle.relativeSpeedMps);
            float accelCmd = std::clamp(gapPid_.compute(gapError, dt_s), -4.0F, 0.0F);
            out.targetAccelMps2 = accelCmd;
            out.actualGapM      = in.leadVehicle.distanceM;
            out.desiredGapM     = desired;
            mapAccelToActuators(accelCmd, out);
            out.stateString = "BRAKING";
            break;
        }

        case AccState::OVERRIDE:
            speedPid_.reset();
            gapPid_.reset();
            out.stateString = "OVERRIDE";
            break;

        case AccState::FAULT:
            speedPid_.reset();
            gapPid_.reset();
            out.stateString = "FAULT";
            break;
        }

        return out;
    }

private:
    static void mapAccelToActuators(float accelMps2, AccOutputs& out) noexcept {
        if (accelMps2 > 0.0F) {
            out.throttleRequest = std::min(1.0F, accelMps2 / 2.0F);
            out.brakeRequest    = 0.0F;
        } else {
            out.throttleRequest = 0.0F;
            out.brakeRequest    = std::min(1.0F, -accelMps2 / 4.0F);
        }
    }

    AccStateMachine sm_;
    PidController   speedPid_;
    PidController   gapPid_;
    uint32_t        lastTs_ = 0U;
};

// ============================================================================
// SCENARIO SIMULATOR
// ============================================================================

struct Scenario {
    const char* name;
    float       egoSpeedMps;
    float       setSpeedMps;
    float       leadDistM;
    float       leadRelSpeedMps;   // Negative = closing
    bool        leadPresent;
    float       driverBrake;
};

int main() {
    std::cout << "=== ACC ECU Simulation ===\n\n";
    std::cout << std::fixed << std::setprecision(2);

    AccController acc;

    // Test scenarios
    const std::array<Scenario, 5> scenarios = {{
        {"Free road, set 33 m/s (120 km/h)",    28.0F, 33.0F, 999.F,  0.0F, false, 0.0F},
        {"Lead at 50m, same speed",             33.0F, 33.0F, 50.0F,  0.0F, true,  0.0F},
        {"Lead cutting in at 30m, 5 m/s slower",33.0F, 33.0F, 30.0F, -5.0F, true,  0.0F},
        {"Emergency: lead at 15m, closing fast", 33.0F, 33.0F, 15.0F,-10.0F, true,  0.0F},
        {"Driver brakes — override",             25.0F, 33.0F, 50.0F,  0.0F, true,  0.7F},
    }};

    for (const auto& scen : scenarios) {
        std::cout << "\n--- Scenario: " << scen.name << " ---\n";
        std::cout << std::setw(8) << "t(s)"
                  << std::setw(12) << "Ego(m/s)"
                  << std::setw(12) << "Gap(m)"
                  << std::setw(14) << "DesGap(m)"
                  << std::setw(10) << "Accel"
                  << std::setw(10) << "Throttle"
                  << std::setw(10) << "Brake"
                  << std::setw(14) << "State\n";
        std::cout << std::string(90, '-') << "\n";

        float egoSpeed = scen.egoSpeedMps;
        float gapM     = scen.leadDistM;

        for (int step = 0; step < 20; ++step) {
            AccInputs in{};
            in.timestamp_ms    = static_cast<uint32_t>(step * 200U);
            in.vehicleSpeedMps = egoSpeed;
            in.setSpeedMps     = scen.setSpeedMps;
            in.setTimeGapS     = 2.0F;
            in.accEnableSwitch = true;
            in.brakeInput      = scen.driverBrake;

            if (scen.leadPresent) {
                in.leadVehicle.valid            = true;
                in.leadVehicle.distanceM        = gapM;
                in.leadVehicle.relativeSpeedMps = scen.leadRelSpeedMps;
                in.leadVehicle.azimuthDeg       = 0.0F;
            }

            AccOutputs out = acc.process(in);

            // Update simulation state
            egoSpeed += out.targetAccelMps2 * 0.2F;
            egoSpeed  = std::max(0.0F, egoSpeed);
            if (scen.leadPresent) {
                gapM -= (scen.leadRelSpeedMps * 0.2F);  // Closing
                gapM  = std::max(2.0F, gapM);
            }

            std::cout << std::setw(8)  << (step * 0.2F)
                      << std::setw(12) << egoSpeed
                      << std::setw(12) << (scen.leadPresent ? gapM : 999.0F)
                      << std::setw(14) << out.desiredGapM
                      << std::setw(10) << out.targetAccelMps2
                      << std::setw(10) << out.throttleRequest
                      << std::setw(10) << out.brakeRequest
                      << std::setw(14) << out.stateString << "\n";
        }
        acc = AccController{};  // Reset for next scenario
    }

    return 0;
}
