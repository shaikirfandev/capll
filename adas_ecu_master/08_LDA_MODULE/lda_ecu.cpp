/**
 * @file    lda_ecu.cpp
 * @brief   Lane Departure Assist — Alert-only (no steering intervention)
 * @standard ISO 17361 LDWS, MISRA C++:2008
 * @asil    ASIL B
 * @compile g++ -std=c++17 -Wall -Wextra lda_ecu.cpp -o lda_ecu
 */

#include <cstdint>
#include <cmath>
#include <cstdio>
#include <algorithm>

// ============================================================================
// TYPES
// ============================================================================

enum class LdaState : uint8_t {
    POWER_OFF       = 0U,
    INITIALISING    = 1U,
    MONITORING      = 2U,   // Armed, TLC computed, no alert
    WARNING         = 3U,   // Visual alert: LED on departing side
    HAPTIC_ALERT    = 4U,   // Seat/wheel vibration
    CRITICAL_ALERT  = 5U,   // Audible + haptic
    SUPPRESSED      = 6U,   // Indicator ON / speed < min / camera lost
};

struct LdaInputs {
    float   vehicleSpeedKph;
    float   laneOffsetM;         // Positive = right of centre
    float   headingAngleDeg;     // Positive = drifting right
    float   laneWidthM;          // Detected lane width [m], ~3.5m typical
    uint8_t laneQuality;         // 0=LOST, 1=LOW, 2=MED, 3=HIGH
    bool    leftMarkerDetected;
    bool    rightMarkerDetected;
    bool    indicatorActive;     // Turn signal ON
    bool    lkaActive;           // LKA is controlling steering
    bool    aebActive;           // AEB braking
};

struct LdaOutputs {
    LdaState state;
    bool     warningVisualLeft;
    bool     warningVisualRight;
    bool     warningHaptic;
    bool     warningAudible;
    float    tlcSeconds;         // Computed TLC for diagnostics
};

// ============================================================================
// CONSTANTS — Calibration (would be in NvM in production)
// ============================================================================

static constexpr float MIN_SPEED_KPH           = 60.0F;
static constexpr float TLC_WARNING_S           = 3.0F;
static constexpr float TLC_HAPTIC_S            = 1.5F;
static constexpr float TLC_CRITICAL_S          = 0.8F;
static constexpr float TLC_CLEAR_HYSTERESIS_S  = 4.0F;  // Hysteresis to clear alert
static constexpr float MIN_LANE_QUALITY        = 2.0F;  // 0=LOST..3=HIGH; require ≥ MEDIUM
static constexpr float HALF_LANE_WIDTH_DEFAULT = 1.75F; // 3.5m / 2
static constexpr float VEHICLE_HALF_WIDTH_M    = 0.95F; // 1.9m wide vehicle / 2

// ============================================================================
// TLC COMPUTATION
// ============================================================================

/**
 * Compute lateral gap from vehicle edge to lane marking.
 * @param laneOffsetM  Lateral offset from lane centre (positive = right)
 * @param halfLaneW    Half lane width in metres
 * @return Gap from right vehicle edge to right marking (positive = gap remaining)
 *         Returns gap to the nearer marking (side of departure).
 */
static float computeLateralGap(float laneOffsetM, float halfLaneW) noexcept {
    // Gap to right marking = halfLane - offset - vehicleHalfWidth
    const float gapRight = halfLaneW - laneOffsetM - VEHICLE_HALF_WIDTH_M;
    // Gap to left marking  = halfLane + offset - vehicleHalfWidth
    const float gapLeft  = halfLaneW + laneOffsetM - VEHICLE_HALF_WIDTH_M;
    // Return minimum (closer to departure)
    return std::min(gapLeft, gapRight);
}

/**
 * Compute lateral velocity from heading angle and vehicle speed.
 * lateral_velocity = speed × sin(heading_angle)
 */
static float computeLateralVelocity(float speedKph, float headingAngleDeg) noexcept {
    const float speedMs = speedKph / 3.6F;
    const float headingRad = headingAngleDeg * (3.14159265F / 180.0F);
    return speedMs * std::sin(headingRad);
}

/**
 * Compute Time-To-Line-Crossing.
 * Returns a large value (99.0F) if lateral velocity is near zero or moving away.
 */
static float computeTLC(float laneOffsetM, float headingAngleDeg,
                         float speedKph, float halfLaneW) noexcept {
    const float lateralGapM  = computeLateralGap(laneOffsetM, halfLaneW);
    const float lateralVelMs = std::abs(computeLateralVelocity(speedKph, headingAngleDeg));

    if (lateralGapM <= 0.0F) {
        return 0.0F;  // Already crossed
    }
    if (lateralVelMs < 0.005F) {  // < 5mm/s — not drifting
        return 99.0F;
    }
    return lateralGapM / lateralVelMs;
}

// ============================================================================
// LDA STATE MACHINE
// ============================================================================

class LdaStateMachine {
public:
    LdaStateMachine() noexcept : state_(LdaState::POWER_OFF) {}

    void update(const LdaInputs& in, LdaOutputs& out) noexcept {
        // Compute TLC regardless of state
        const float halfLane = (in.laneWidthM > 1.0F) ? (in.laneWidthM / 2.0F) : HALF_LANE_WIDTH_DEFAULT;
        const float tlc = computeTLC(in.laneOffsetM, in.headingAngleDeg, in.vehicleSpeedKph, halfLane);

        // Determine if any suppression condition is active
        const bool suppressed = in.indicatorActive
                             || in.lkaActive
                             || in.aebActive
                             || (in.vehicleSpeedKph < MIN_SPEED_KPH)
                             || (static_cast<float>(in.laneQuality) < MIN_LANE_QUALITY)
                             || (!in.leftMarkerDetected && !in.rightMarkerDetected);

        // Ignition-off → immediate POWER_OFF
        if (in.vehicleSpeedKph < 0.1F && state_ != LdaState::INITIALISING) {
            if (state_ != LdaState::POWER_OFF) {
                state_ = LdaState::POWER_OFF;
            }
        }

        // Main state transitions
        switch (state_) {
            case LdaState::POWER_OFF:
                if (in.vehicleSpeedKph > 0.5F) {
                    state_ = LdaState::INITIALISING;
                }
                break;

            case LdaState::INITIALISING:
                if (in.laneQuality >= 2U && in.vehicleSpeedKph >= MIN_SPEED_KPH) {
                    state_ = LdaState::MONITORING;
                }
                break;

            case LdaState::MONITORING:
                if (suppressed) {
                    state_ = LdaState::SUPPRESSED;
                } else if (tlc < TLC_CRITICAL_S) {
                    state_ = LdaState::CRITICAL_ALERT;
                } else if (tlc < TLC_HAPTIC_S) {
                    state_ = LdaState::HAPTIC_ALERT;
                } else if (tlc < TLC_WARNING_S) {
                    state_ = LdaState::WARNING;
                }
                break;

            case LdaState::WARNING:
                if (suppressed || tlc > TLC_CLEAR_HYSTERESIS_S) {
                    state_ = suppressed ? LdaState::SUPPRESSED : LdaState::MONITORING;
                } else if (tlc < TLC_HAPTIC_S) {
                    state_ = LdaState::HAPTIC_ALERT;
                }
                break;

            case LdaState::HAPTIC_ALERT:
                if (suppressed || tlc > TLC_CLEAR_HYSTERESIS_S) {
                    state_ = suppressed ? LdaState::SUPPRESSED : LdaState::MONITORING;
                } else if (tlc < TLC_CRITICAL_S) {
                    state_ = LdaState::CRITICAL_ALERT;
                } else if (tlc >= TLC_HAPTIC_S) {
                    state_ = LdaState::WARNING;
                }
                break;

            case LdaState::CRITICAL_ALERT:
                if (suppressed || tlc > TLC_CLEAR_HYSTERESIS_S) {
                    state_ = suppressed ? LdaState::SUPPRESSED : LdaState::MONITORING;
                } else if (tlc >= TLC_HAPTIC_S) {
                    state_ = LdaState::HAPTIC_ALERT;
                }
                break;

            case LdaState::SUPPRESSED:
                if (!suppressed && in.vehicleSpeedKph >= MIN_SPEED_KPH) {
                    state_ = LdaState::MONITORING;
                }
                break;

            default:
                state_ = LdaState::MONITORING;
                break;
        }

        // Compute which side is departing (for directional visual alert)
        const bool driftingRight = (in.laneOffsetM > 0.0F) || (in.headingAngleDeg > 0.0F);

        // Set outputs
        out.state            = state_;
        out.tlcSeconds       = tlc;
        out.warningVisualLeft  = false;
        out.warningVisualRight = false;
        out.warningHaptic      = false;
        out.warningAudible     = false;

        switch (state_) {
            case LdaState::CRITICAL_ALERT:
                out.warningAudible = true;
                out.warningHaptic  = true;
                if (driftingRight) { out.warningVisualRight = true; }
                else               { out.warningVisualLeft  = true; }
                break;
            case LdaState::HAPTIC_ALERT:
                out.warningHaptic  = true;
                if (driftingRight) { out.warningVisualRight = true; }
                else               { out.warningVisualLeft  = true; }
                break;
            case LdaState::WARNING:
                if (driftingRight) { out.warningVisualRight = true; }
                else               { out.warningVisualLeft  = true; }
                break;
            default:
                break;
        }
    }

    LdaState getState() const noexcept { return state_; }

private:
    LdaState state_;
};

// ============================================================================
// HELPERS
// ============================================================================

static const char* stateToStr(LdaState s) noexcept {
    switch (s) {
        case LdaState::POWER_OFF:       return "POWER_OFF";
        case LdaState::INITIALISING:    return "INITIALISING";
        case LdaState::MONITORING:      return "MONITORING";
        case LdaState::WARNING:         return "WARNING";
        case LdaState::HAPTIC_ALERT:    return "HAPTIC_ALERT";
        case LdaState::CRITICAL_ALERT:  return "CRITICAL_ALERT";
        case LdaState::SUPPRESSED:      return "SUPPRESSED";
        default:                        return "UNKNOWN";
    }
}

// ============================================================================
// MAIN — Simulation
// ============================================================================

int main() {
    std::printf("=== LDA Module Simulation ===\n");
    std::printf("%-6s %-18s %-6s %-6s %-6s %-5s %-5s %-5s\n",
                "t[s]", "State", "TLC[s]", "Offset", "Head", "Vis", "Hap", "Aud");
    std::printf("%-6s %-18s %-6s %-6s %-6s %-5s %-5s %-5s\n",
                "------", "------------------", "------", "------", "------", "-----", "-----", "-----");

    LdaStateMachine lda{};
    LdaInputs  in{};
    LdaOutputs out{};

    // Base state: driving at 100 km/h, centred in lane
    in.vehicleSpeedKph     = 100.0F;
    in.laneWidthM          = 3.5F;
    in.laneQuality         = 3U;   // HIGH
    in.leftMarkerDetected  = true;
    in.rightMarkerDetected = true;

    constexpr float DT_S     = 0.05F;   // 50ms cycle
    constexpr int   CYCLES   = 600;     // 30 seconds

    for (int cycle = 0; cycle < CYCLES; ++cycle) {
        const float tSec = static_cast<float>(cycle) * DT_S;

        // Scenario: gradual right drift from t=5s to t=15s
        if (tSec >= 5.0F && tSec < 15.0F) {
            in.laneOffsetM    = (tSec - 5.0F) * 0.04F;   // 0 → 0.4m drift
            in.headingAngleDeg = (tSec - 5.0F) * 0.2F;   // 0 → 2.0 deg heading
        }
        // Driver corrects at t=15s
        else if (tSec >= 15.0F && tSec < 16.0F) {
            in.laneOffsetM    = 0.4F - (tSec - 15.0F) * 0.4F;
            in.headingAngleDeg = 2.0F - (tSec - 15.0F) * 2.0F;
        }
        // Turn indicator at t=20s (intentional lane change)
        else if (tSec >= 20.0F && tSec < 22.0F) {
            in.indicatorActive = true;
            in.laneOffsetM     = (tSec - 20.0F) * 0.15F;  // Actual lane change
            in.headingAngleDeg = (tSec - 20.0F) * 1.5F;
        }
        else if (tSec >= 22.0F && tSec < 24.0F) {
            in.indicatorActive = false;
            in.laneOffsetM     = 0.0F;
            in.headingAngleDeg = 0.0F;
        }
        // t=25s: camera goes LOST briefly (rain simulation)
        else if (tSec >= 25.0F && tSec < 27.0F) {
            in.laneQuality = 0U;  // LOST
            in.leftMarkerDetected  = false;
            in.rightMarkerDetected = false;
        }
        else if (tSec >= 27.0F) {
            in.laneQuality = 3U;
            in.leftMarkerDetected  = true;
            in.rightMarkerDetected = true;
        }
        else {
            in.laneOffsetM     = 0.0F;
            in.headingAngleDeg = 0.0F;
        }

        lda.update(in, out);

        // Print only state changes or at 1s intervals
        if (cycle % 20 == 0 || out.warningAudible || out.warningHaptic) {
            std::printf("%-6.1f %-18s %-6.2f %-6.2f %-6.1f %-5s %-5s %-5s\n",
                        tSec,
                        stateToStr(out.state),
                        out.tlcSeconds > 98.0F ? 99.0F : out.tlcSeconds,
                        in.laneOffsetM,
                        in.headingAngleDeg,
                        (out.warningVisualLeft || out.warningVisualRight) ? "YES" : "no",
                        out.warningHaptic ? "YES" : "no",
                        out.warningAudible ? "YES" : "no");
        }
    }

    std::printf("\n=== LDA Simulation Complete ===\n");
    std::printf("Note: TLC=99 means vehicle is not drifting (lateral velocity near zero)\n");
    return 0;
}
