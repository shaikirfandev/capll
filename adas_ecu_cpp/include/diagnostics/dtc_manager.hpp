/**
 * @file    dtc_manager.hpp
 * @brief   Diagnostic Trouble Code manager — AUTOSAR-aligned fault storage.
 *
 * Implements a subset of AUTOSAR Dem (Diagnostic Event Manager):
 *  - Fixed-size DTC table (no heap)
 *  - Each DTC has: event ID, status (active/pending/stored), occurrence count
 *  - Supports UDS 0x19 ReadDTCInformation via getDTCList()
 *  - Supports UDS 0x14 ClearDiagnosticInformation via clearAll()
 *  - NVM simulation: dtc_table_ would be stored to FLASH on real target
 *
 * DTC naming follows AUTOSAR convention: U/B/C/P prefix
 *   U = Network communication
 *   B = Body
 *   C = Chassis
 *   P = Powertrain/ADAS
 */

#pragma once
#include "hal/hal_types.hpp"

namespace diagnostics {

// ── DTC Codes used in ADAS ECU ────────────────────────────────────────────────
enum class DtcId : uint32_t {
    // Radar
    RADAR_COMM_LOSS         = 0xU0001,   ///< No CAN message from radar >500ms
    RADAR_SIGNAL_INVALID    = 0xU0002,   ///< Radar valid bit = 0 for >2s
    // Camera
    CAMERA_COMM_LOSS        = 0xU0010,
    CAMERA_BLOCKAGE         = 0xU0011,   ///< Camera reports blockage
    // ACC
    ACC_INTERNAL_FAULT      = 0xP1001,
    ACC_SPEED_SENSOR_FAULT  = 0xP1002,
    // LKA
    LKA_EPS_COMM_LOSS       = 0xP1010,
    LKA_TORQUE_STUCK        = 0xP1011,
    // BSD
    BSD_LEFT_RADAR_FAULT    = 0xP1020,
    BSD_RIGHT_RADAR_FAULT   = 0xP1021,
    // Parking
    PARK_SENSOR_FL_FAULT    = 0xP1030,
    PARK_SENSOR_FR_FAULT    = 0xP1031,
    PARK_SENSOR_RL_FAULT    = 0xP1032,
    PARK_SENSOR_RR_FAULT    = 0xP1033,
    // HHA
    HHA_GRADIENT_FAULT      = 0xP1040,
    // ECU
    ECU_VOLTAGE_LOW         = 0xB0001,
    ECU_VOLTAGE_HIGH        = 0xB0002,
    ECU_OVERTEMPERATURE     = 0xB0003,
    ECU_INTERNAL_ERROR      = 0xB0099,
    // Scheduler
    TASK_OVERRUN            = 0xU0100,
};

// ── DTC Status byte (ISO 14229 aligned) ──────────────────────────────────────
struct DtcStatus {
    bool test_failed            : 1;  ///< bit 0: currently failing
    bool test_failed_this_cycle : 1;  ///< bit 1: failed in this cycle
    bool pending                : 1;  ///< bit 2: approaching trip threshold
    bool confirmed              : 1;  ///< bit 3: confirmed after N failures
    bool test_not_completed     : 1;  ///< bit 4: test not run yet this cycle
    bool test_failed_since_clear: 1;  ///< bit 5: failed after last clear
    bool                        : 2;  ///< bits 6-7: reserved

    DtcStatus() : test_failed(false), test_failed_this_cycle(false),
                  pending(false), confirmed(false), test_not_completed(true),
                  test_failed_since_clear(false) {}

    uint8_t toByte() const {
        return (uint8_t)(test_failed            << 0u |
                         test_failed_this_cycle << 1u |
                         pending                << 2u |
                         confirmed              << 3u |
                         test_not_completed     << 4u |
                         test_failed_since_clear<< 5u);
    }
};

// ── DTC Entry ────────────────────────────────────────────────────────────────

struct DtcEntry {
    DtcId       id              = static_cast<DtcId>(0);
    DtcStatus   status;
    uint8_t     occurrence      = 0u;   ///< Number of times confirmed
    uint8_t     fail_counter    = 0u;   ///< Consecutive failure count
    uint8_t     pass_counter    = 0u;   ///< Consecutive pass count
    uint32_t    first_tick      = 0u;   ///< Tick when first reported
    uint32_t    last_tick       = 0u;   ///< Tick when last active
    bool        used            = false;///< Entry slot in use

    // Trip thresholds (AUTOSAR Dem configurable per DTC)
    static constexpr uint8_t FAIL_TRIP_THRESHOLD = 3u;
    static constexpr uint8_t PASS_TRIP_THRESHOLD = 3u;
};

// ── DTC Manager ──────────────────────────────────────────────────────────────

class DtcManager {
public:
    static constexpr uint8_t MAX_DTCS = 32u;

    static DtcManager& instance() {
        static DtcManager inst;
        return inst;
    }

    /**
     * @brief Report a fault event. Call every cycle while fault condition holds.
     *        DTC becomes 'confirmed' after FAIL_TRIP_THRESHOLD consecutive calls.
     */
    void reportFault(DtcId id);

    /**
     * @brief Report that a fault condition has cleared. Starts healing.
     */
    void reportPassed(DtcId id);

    /**
     * @brief Clear all stored DTCs (UDS 0x14 service handler).
     */
    void clearAll();

    /**
     * @brief Get count of currently confirmed DTCs.
     */
    uint8_t confirmedCount() const;

    /**
     * @brief Get count of currently active (test_failed) DTCs.
     */
    uint8_t activeCount() const;

    /**
     * @brief Returns true if a specific DTC is currently confirmed.
     */
    bool isConfirmed(DtcId id) const;

    /**
     * @brief Fill a caller-provided buffer with confirmed DTC IDs.
     * @param out     Buffer to receive IDs
     * @param max     Max entries in buffer
     * @return        Number of DTCs written
     */
    uint8_t getConfirmedDTCs(DtcId* out, uint8_t max) const;

    /**
     * @brief Diagnostic cycle end — update status bits.
     *        Call once per 100ms diagnostic cycle.
     */
    void endOfCycle();

private:
    DtcManager() = default;

    DtcEntry* find(DtcId id);
    DtcEntry* allocate(DtcId id);

    DtcEntry table_[MAX_DTCS];
};

} // namespace diagnostics
