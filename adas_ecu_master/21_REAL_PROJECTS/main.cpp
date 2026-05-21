/**
 * @file    main.cpp
 * @brief   Mini ADAS ECU — Integrates LKA + LDA + ACC in a single simulation
 * @compile g++ -std=c++17 -Wall -Wextra main.cpp -o adas_ecu_demo
 */

#include <cstdint>
#include <cstdio>
#include <cmath>
#include <algorithm>

// ============================================================================
// SHARED TYPES
// ============================================================================

struct VehicleState {
    float speedKph;
    float laneOffsetM;
    float headingAngleDeg;
    float epsDriverTorqueNm;
    float radarRangeM;
    float radarRelSpeedMps;
    float radarAzimuthDeg;
    uint8_t laneQuality;       // 0-3
    bool  indicatorActive;
    bool  aebActive;
};

// ============================================================================
// MINIMAL LKA CONTROLLER
// ============================================================================

enum class LkaState : uint8_t { STANDBY=0, MONITORING=1, CORRECTING=2, OVERRIDE=3, FAULT=4 };

struct LkaResult {
    LkaState state;
    float    torqueRequestNm;
    bool     active;
};

class LkaController {
    LkaState  state_     = LkaState::STANDBY;
    float     integralE_ = 0.0F;
    float     prevErr_   = 0.0F;
    int       overrideCnt_ = 0;

    static constexpr float KP = 0.8F, KI = 0.15F, KD = 0.05F;
    static constexpr float DT = 0.01F;
    static constexpr float MAX_TORQUE = 3.0F;
    static constexpr float OVERRIDE_TORQUE = 2.5F;
    static constexpr int   OVERRIDE_HOLD_CYCLES = 300; // 3s at 10ms

public:
    LkaResult update(const VehicleState& v) noexcept {
        LkaResult r{};
        r.state = state_;

        const bool canActivate = (v.speedKph >= 60.0F) && (v.laneQuality >= 2U)
                               && !v.indicatorActive && !v.aebActive;
        const bool driverOverride = (std::abs(v.epsDriverTorqueNm) > OVERRIDE_TORQUE);

        switch (state_) {
            case LkaState::STANDBY:
                if (canActivate) state_ = LkaState::MONITORING;
                break;
            case LkaState::MONITORING:
                if (!canActivate) { state_ = LkaState::STANDBY; break; }
                if (driverOverride) { state_ = LkaState::OVERRIDE; overrideCnt_ = OVERRIDE_HOLD_CYCLES; break; }
                if (std::abs(v.laneOffsetM) > 0.15F) state_ = LkaState::CORRECTING;
                break;
            case LkaState::CORRECTING:
                if (!canActivate) { state_ = LkaState::STANDBY; integralE_ = 0.0F; break; }
                if (driverOverride) { state_ = LkaState::OVERRIDE; overrideCnt_ = OVERRIDE_HOLD_CYCLES; integralE_ = 0.0F; break; }
                if (std::abs(v.laneOffsetM) < 0.08F) state_ = LkaState::MONITORING;
                break;
            case LkaState::OVERRIDE:
                if (overrideCnt_ > 0) { --overrideCnt_; }
                else { state_ = canActivate ? LkaState::MONITORING : LkaState::STANDBY; }
                break;
            case LkaState::FAULT:
                break;
        }

        r.state = state_;
        r.active = (state_ == LkaState::CORRECTING);

        if (state_ == LkaState::CORRECTING) {
            const float err = -v.laneOffsetM;
            integralE_ = std::max(-5.0F, std::min(5.0F, integralE_ + err * DT));
            const float dErr = (err - prevErr_) / DT;
            prevErr_ = err;
            float out = KP*err + KI*integralE_ + KD*dErr;
            r.torqueRequestNm = std::max(-MAX_TORQUE, std::min(MAX_TORQUE, out));
        } else {
            integralE_ = 0.0F;
            prevErr_ = 0.0F;
        }
        return r;
    }
};

// ============================================================================
// MINIMAL LDA STATE MACHINE
// ============================================================================

enum class LdaAlertLevel : uint8_t { NONE=0, VISUAL=1, HAPTIC=2, AUDIBLE=3 };

struct LdaResult {
    LdaAlertLevel alertLevel;
    float         tlcSeconds;
};

class LdaController {
    static constexpr float MIN_SPEED = 60.0F;
    static constexpr float TLC_VIS = 3.0F, TLC_HAP = 1.5F, TLC_AUD = 0.8F;

public:
    LdaResult update(const VehicleState& v) noexcept {
        LdaResult r{};
        if (v.speedKph < MIN_SPEED || v.laneQuality < 2U || v.indicatorActive) {
            r.alertLevel = LdaAlertLevel::NONE;
            r.tlcSeconds = 99.0F;
            return r;
        }

        const float halfLane = 1.75F;
        const float gapM = halfLane - std::abs(v.laneOffsetM) - 0.95F;
        const float speedMs = v.speedKph / 3.6F;
        const float latVel = std::abs(speedMs * std::sin(v.headingAngleDeg * 3.14159265F / 180.0F));
        const float tlc = (latVel > 0.005F) ? (gapM / latVel) : 99.0F;

        r.tlcSeconds = tlc;
        if      (tlc < TLC_AUD) r.alertLevel = LdaAlertLevel::AUDIBLE;
        else if (tlc < TLC_HAP) r.alertLevel = LdaAlertLevel::HAPTIC;
        else if (tlc < TLC_VIS) r.alertLevel = LdaAlertLevel::VISUAL;
        else                    r.alertLevel = LdaAlertLevel::NONE;

        return r;
    }
};

// ============================================================================
// MINIMAL ACC CONTROLLER
// ============================================================================

enum class AccState : uint8_t { OFF=0, SPEED_CONTROL=1, FOLLOWING=2, OVERRIDE=3 };

struct AccResult {
    AccState state;
    float    throttlePercent;
    float    brakePercent;
};

class AccController {
    AccState state_     = AccState::OFF;
    float    speedInt_  = 0.0F;
    float    gapInt_    = 0.0F;
    float    setSpeedKph_ = 100.0F;

    static constexpr float DT         = 0.05F;
    static constexpr float TIME_GAP   = 1.5F;
    static constexpr float MIN_GAP_M  = 5.0F;
    static constexpr float KP_SPD = 0.2F, KI_SPD = 0.05F;
    static constexpr float KP_GAP = 0.3F, KI_GAP = 0.04F;

public:
    AccResult update(const VehicleState& v) noexcept {
        AccResult r{};

        // Simple activation
        if (v.speedKph < 20.0F) { state_ = AccState::OFF; return r; }
        if (state_ == AccState::OFF) state_ = AccState::SPEED_CONTROL;

        const bool hasTarget = (v.radarRangeM > 0.0F && v.radarRangeM < 150.0F
                               && std::abs(v.radarAzimuthDeg) < 5.0F);
        const float desiredGap = std::max(MIN_GAP_M, v.speedKph / 3.6F * TIME_GAP);

        if (hasTarget) {
            state_ = AccState::FOLLOWING;
            const float gapErr = v.radarRangeM - desiredGap;
            gapInt_ = std::max(-10.0F, std::min(10.0F, gapInt_ + gapErr * DT));
            float cmd = KP_GAP * gapErr + KI_GAP * gapInt_;
            speedInt_ = 0.0F;
            r.throttlePercent = std::max(0.0F, std::min(100.0F, cmd * 10.0F));
            r.brakePercent    = std::max(0.0F, std::min(100.0F, -cmd * 5.0F));
        } else {
            state_ = AccState::SPEED_CONTROL;
            const float speedErr = setSpeedKph_ - v.speedKph;
            speedInt_ = std::max(-20.0F, std::min(20.0F, speedInt_ + speedErr * DT));
            float cmd = KP_SPD * speedErr + KI_SPD * speedInt_;
            gapInt_ = 0.0F;
            r.throttlePercent = std::max(0.0F, std::min(100.0F, cmd * 5.0F));
            r.brakePercent    = 0.0F;
        }

        r.state = state_;
        return r;
    }
};

// ============================================================================
// DIAGNOSTICS MANAGER — DTC Log
// ============================================================================

struct DtcEntry {
    uint32_t dtcCode;
    uint8_t  status;   // 0=no fault, 1=pending, 2=confirmed
    uint32_t occurrences;
};

class DiagnosticsManager {
    DtcEntry dtcs_[8U]{};
    uint8_t  count_ = 0U;

public:
    void reportFault(uint32_t code) noexcept {
        for (uint8_t i = 0U; i < count_; ++i) {
            if (dtcs_[i].dtcCode == code) {
                ++dtcs_[i].occurrences;
                if (dtcs_[i].occurrences >= 3U) dtcs_[i].status = 2U;
                return;
            }
        }
        if (count_ < 8U) {
            dtcs_[count_++] = DtcEntry{code, 1U, 1U};
        }
    }

    void printDtcLog() const noexcept {
        std::printf("\n=== DTC Log (%u entries) ===\n", count_);
        for (uint8_t i = 0U; i < count_; ++i) {
            std::printf("  DTC 0x%05X  status=%s  occurrences=%u\n",
                        dtcs_[i].dtcCode,
                        (dtcs_[i].status == 2U) ? "CONFIRMED" : "PENDING",
                        dtcs_[i].occurrences);
        }
    }
};

// ============================================================================
// MAIN LOOP
// ============================================================================

static const char* lkaStateStr(LkaState s) noexcept {
    switch(s) {
        case LkaState::STANDBY:    return "STBY";
        case LkaState::MONITORING: return "MON ";
        case LkaState::CORRECTING: return "CORR";
        case LkaState::OVERRIDE:   return "OVR ";
        case LkaState::FAULT:      return "FALT";
        default:                   return "?   ";
    }
}

static const char* accStateStr(AccState s) noexcept {
    switch(s) {
        case AccState::OFF:           return "OFF ";
        case AccState::SPEED_CONTROL: return "SPD ";
        case AccState::FOLLOWING:     return "FOLL";
        case AccState::OVERRIDE:      return "OVR ";
        default:                      return "?   ";
    }
}

int main() {
    std::printf("=== Mini ADAS ECU Integration Demo ===\n");
    std::printf("%-6s %-5s %-5s %-7s %-7s %-7s %-5s %-5s %-6s\n",
                "t[s]","LKA","ACC","Torq[Nm]","Offset","Gap[m]","Throt","Brake","TLC[s]");
    std::printf("-------------------------------------------------------------------\n");

    LkaController      lka{};
    LdaController      lda{};
    AccController      acc{};
    DiagnosticsManager diag{};

    VehicleState v{};
    v.speedKph   = 0.0F;
    v.laneQuality = 3U;
    v.radarRangeM = 0.0F;

    constexpr float DT   = 0.01F;   // 10ms main loop
    constexpr int   STEPS = 3000;   // 30 seconds

    for (int step = 0; step < STEPS; ++step) {
        const float t = static_cast<float>(step) * DT;

        // --- Simulate driving scenario ---
        // 0-5s: accelerate to 100 km/h
        if (t < 5.0F) {
            v.speedKph = t * 20.0F;  // 0 → 100
        } else {
            v.speedKph = 100.0F;
        }

        // 3-8s: slight right drift
        if (t >= 3.0F && t < 8.0F) {
            v.laneOffsetM     = (t - 3.0F) * 0.06F;  // 0 → 0.3m
            v.headingAngleDeg = (t - 3.0F) * 0.3F;
        } else if (t >= 8.0F && t < 9.0F) {
            v.laneOffsetM    = 0.3F - (t - 8.0F) * 0.3F;
            v.headingAngleDeg = 1.5F - (t - 8.0F) * 1.5F;
        } else if (t >= 9.0F) {
            v.laneOffsetM     = 0.0F;
            v.headingAngleDeg = 0.0F;
        }

        // 10-15s: lead vehicle appears at 80m, closes to 30m
        if (t >= 10.0F && t < 15.0F) {
            v.radarRangeM     = 80.0F - (t - 10.0F) * 10.0F;  // 80 → 30m
            v.radarAzimuthDeg = 1.0F;
            v.radarRelSpeedMps = -10.0F;
        } else if (t >= 15.0F && t < 25.0F) {
            v.radarRangeM     = 30.0F;
            v.radarAzimuthDeg = 1.0F;
            v.radarRelSpeedMps = 0.0F;
        } else if (t >= 25.0F) {
            v.radarRangeM = 0.0F;  // Lead vehicle gone
        }

        // 20-21s: driver override (brakes)
        v.epsDriverTorqueNm = (t >= 20.0F && t < 21.0F) ? 3.5F : 0.0F;

        // --- Run controllers (all at 10ms) ---
        const LkaResult lkaR = lka.update(v);
        const LdaResult ldaR = lda.update(v);

        // ACC runs at 50ms (every 5 cycles)
        AccResult accR{};
        if (step % 5 == 0) {
            accR = acc.update(v);
        }

        // Fault injection: camera LOST between t=17-18s
        if (t >= 17.0F && t < 18.0F) {
            v.laneQuality = 0U;
            diag.reportFault(0xC1101U);  // DTC: Camera signal lost
        } else if (t >= 18.0F) {
            v.laneQuality = 3U;
        }

        // Print summary at 1s intervals
        if (step % 100 == 0) {
            std::printf("%-6.1f %-5s %-5s %-7.2f %-7.2f %-7.1f %-5.1f %-5.1f %-6.2f\n",
                        t,
                        lkaStateStr(lkaR.state),
                        accStateStr(accR.state),
                        lkaR.torqueRequestNm,
                        v.laneOffsetM,
                        v.radarRangeM,
                        accR.throttlePercent,
                        accR.brakePercent,
                        ldaR.tlcSeconds > 50.0F ? 99.0F : ldaR.tlcSeconds);
        }
    }

    diag.printDtcLog();
    std::printf("\n=== Mini ADAS ECU Demo Complete ===\n");
    return 0;
}
