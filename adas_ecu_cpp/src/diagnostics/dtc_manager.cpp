/**
 * @file    dtc_manager.cpp
 * @brief   DTC manager implementation.
 */

#include "diagnostics/dtc_manager.hpp"
#include "hal/hal_timer.hpp"
#include <cstdio>

namespace diagnostics {

// ── Internal helpers ──────────────────────────────────────────────────────────

DtcEntry* DtcManager::find(DtcId id) {
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (table_[i].used && table_[i].id == id) return &table_[i];
    }
    return nullptr;
}

DtcEntry* DtcManager::allocate(DtcId id) {
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (!table_[i].used) {
            table_[i]            = DtcEntry{};
            table_[i].id         = id;
            table_[i].used       = true;
            table_[i].first_tick = hal::Timer::getTick();
            return &table_[i];
        }
    }
    return nullptr;  // Table full
}

// ── Public API ────────────────────────────────────────────────────────────────

void DtcManager::reportFault(DtcId id) {
    DtcEntry* entry = find(id);
    if (!entry) {
        entry = allocate(id);
        if (!entry) {
            // DTC table full — can't store (log for debug)
#ifdef SIMULATION_BUILD
            std::printf("[DTC] WARNING: table full, cannot store DTC 0x%06X\n",
                        static_cast<uint32_t>(id));
#endif
            return;
        }
    }

    entry->status.test_failed            = true;
    entry->status.test_failed_this_cycle = true;
    entry->status.test_not_completed     = false;
    entry->last_tick                     = hal::Timer::getTick();
    entry->pass_counter                  = 0u;  // Reset healing counter

    entry->fail_counter++;
    if (entry->fail_counter >= DtcEntry::FAIL_TRIP_THRESHOLD) {
        // Confirmed after N consecutive failures
        if (!entry->status.confirmed) {
            entry->occurrence++;
            entry->status.confirmed          = true;
            entry->status.test_failed_since_clear = true;
#ifdef SIMULATION_BUILD
            std::printf("[DTC] CONFIRMED: 0x%06X (occurrence #%u)\n",
                        static_cast<uint32_t>(id), entry->occurrence);
#endif
        }
    } else if (!entry->status.confirmed) {
        entry->status.pending = true;
    }
}

void DtcManager::reportPassed(DtcId id) {
    DtcEntry* entry = find(id);
    if (!entry) return;

    entry->status.test_failed            = false;
    entry->status.test_failed_this_cycle = false;
    entry->fail_counter                  = 0u;

    entry->pass_counter++;
    if (entry->pass_counter >= DtcEntry::PASS_TRIP_THRESHOLD) {
        entry->status.pending  = false;
        // Note: confirmed stays set — DTC remains stored until ClearDTC
        // test_failed = false marks it as healed but still in memory
    }
}

void DtcManager::clearAll() {
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        table_[i] = DtcEntry{};   // Reset to default-constructed state
    }
#ifdef SIMULATION_BUILD
    std::printf("[DTC] All DTCs cleared\n");
#endif
}

void DtcManager::endOfCycle() {
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (table_[i].used) {
            // Clear this-cycle flag ready for next cycle
            table_[i].status.test_failed_this_cycle = false;
        }
    }
}

uint8_t DtcManager::confirmedCount() const {
    uint8_t count = 0u;
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (table_[i].used && table_[i].status.confirmed) count++;
    }
    return count;
}

uint8_t DtcManager::activeCount() const {
    uint8_t count = 0u;
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (table_[i].used && table_[i].status.test_failed) count++;
    }
    return count;
}

bool DtcManager::isConfirmed(DtcId id) const {
    for (uint8_t i = 0; i < MAX_DTCS; i++) {
        if (table_[i].used && table_[i].id == id && table_[i].status.confirmed) {
            return true;
        }
    }
    return false;
}

uint8_t DtcManager::getConfirmedDTCs(DtcId* out, uint8_t max) const {
    uint8_t count = 0u;
    for (uint8_t i = 0; i < MAX_DTCS && count < max; i++) {
        if (table_[i].used && table_[i].status.confirmed) {
            out[count++] = table_[i].id;
        }
    }
    return count;
}

} // namespace diagnostics
