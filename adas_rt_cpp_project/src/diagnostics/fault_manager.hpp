#pragma once
/**
 * @file fault_manager.hpp
 * @brief Automotive DTC-style fault management system.
 *
 * AUTOMOTIVE CONTEXT
 * ──────────────────
 * In production ADAS ECUs, faults are stored as Diagnostic Trouble Codes (DTCs)
 * following ISO 14229 (UDS) and ISO 15765 conventions.
 * Each DTC has:
 *   • A code (e.g. P0001 = powertrain code 0001)
 *   • A status byte (active, pending, confirmed, test-not-complete …)
 *   • Freeze frame data (sensor snapshot at time of first occurrence)
 *   • An occurrence counter
 *
 * THIS MODULE (SIMPLIFIED)
 * ─────────────────────────
 * • FaultCode enum maps to project-specific 16-bit DTC IDs.
 * • FaultStatus tracks the lifecycle: PENDING → ACTIVE → CONFIRMED → HEALED.
 * • FaultManager broadcasts fault events over CAN (ID 0x400).
 * • SafeStateHandler is called when a FATAL fault occurs.
 */

#include <array>
#include <cstdint>
#include <functional>
#include <mutex>
#include <string>
#include <unordered_map>

namespace adas {
namespace diag {

// ─── DTC codes ────────────────────────────────────────────────────────────────

enum class FaultCode : uint16_t {
    NONE                      = 0x0000,
    CAMERA_SIGNAL_LOST        = 0x0101,
    RADAR_SIGNAL_LOST         = 0x0102,
    LIDAR_SIGNAL_LOST         = 0x0103,
    EKF_DIVERGENCE            = 0x0201,
    PLANNING_TIMEOUT          = 0x0301,
    CONTROL_ACTUATOR_FAULT    = 0x0401,
    CAN_TX_TIMEOUT            = 0x0501,
    CAN_RX_TIMEOUT            = 0x0502,
    CPU_OVERLOAD              = 0x0601,
    MEMORY_CORRUPTION         = 0x0602,
    WATCHDOG_TIMEOUT          = 0x0603,
    RT_DEADLINE_MISS_CRITICAL = 0x0701,
};

const char* faultCodeToString(FaultCode code);

// ─── Fault lifecycle ──────────────────────────────────────────────────────────

enum class FaultStatus : uint8_t {
    INACTIVE   = 0x00,   ///< No fault active
    PENDING    = 0x01,   ///< Fault condition detected, awaiting confirmation
    ACTIVE     = 0x02,   ///< Confirmed fault
    HEALED     = 0x03,   ///< Was active, now gone; retained until cleared
};

struct FaultRecord {
    FaultCode   code;
    FaultStatus status;
    uint32_t    occurrence_count;
    uint64_t    first_occurrence_us;
    uint64_t    last_occurrence_us;
    char        context[64];   ///< Freeze-frame description
};

// ─── Fault manager ────────────────────────────────────────────────────────────

using SafeStateCallback = std::function<void(FaultCode)>;

/**
 * @class FaultManager
 * @brief Tracks active faults and triggers safe-state actions.
 *
 * Usage:
 * @code
 *   auto& fm = FaultManager::instance();
 *   fm.registerSafeStateCallback([](FaultCode c) {
 *       // engage parking brake, disable actuators
 *   });
 *   fm.reportFault(FaultCode::RADAR_SIGNAL_LOST, "No frames in 100ms");
 *   fm.healFault(FaultCode::RADAR_SIGNAL_LOST);
 * @endcode
 */
class FaultManager {
public:
    static FaultManager& instance();

    FaultManager(const FaultManager&)            = delete;
    FaultManager& operator=(const FaultManager&) = delete;

    /// Register callback to be invoked when a FATAL fault is detected
    void registerSafeStateCallback(SafeStateCallback cb);

    /**
     * @brief Report a fault condition.
     * @param code     DTC code
     * @param context  Human-readable context (freeze-frame)
     */
    void reportFault(FaultCode code, const char* context = "");

    /// Mark a fault as healed (status transitions to HEALED)
    void healFault(FaultCode code);

    /// Clear all healed/inactive faults (UDS service 14)
    void clearFaults();

    /// Get all active/healed fault records
    std::vector<FaultRecord> getActiveFaults() const;

    /// Returns true if any ACTIVE faults exist
    bool hasActiveFaults() const;

    /// Print all faults to stdout (for debug)
    void dump() const;

private:
    FaultManager() = default;

    // Fatal faults → safe state (unrecoverable)
    static bool isFatal(FaultCode code);

    mutable std::mutex                           mutex_;
    std::unordered_map<uint16_t, FaultRecord>   records_;
    SafeStateCallback                            safe_state_cb_;
};

}  // namespace diag
}  // namespace adas
