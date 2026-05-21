/**
 * @file FaultManager.cpp
 * @req SRS-SAFE-001, SRS-SAFE-002
 */
#include "FaultManager.hpp"
#include <cstring>
#include <algorithm>

namespace fms::safety {

fms::FmsError FaultManager::init() noexcept {
    std::unique_lock lk(mtx_);
    table_.fill({});
    count_ = 0;
    return fms::FmsError::OK;
}

void FaultManager::shutdown() noexcept {
    std::unique_lock lk(mtx_);
    table_.fill({});
    count_ = 0;
}

FaultRecord* FaultManager::find_record(FaultId id) noexcept {
    for (auto& r : table_) {
        if (r.state != FaultState::INACTIVE && r.id == id) return &r;
    }
    return nullptr;
}

const FaultRecord* FaultManager::find_record(FaultId id) const noexcept {
    for (const auto& r : table_) {
        if (r.state != FaultState::INACTIVE && r.id == id) return &r;
    }
    return nullptr;
}

fms::FmsError FaultManager::report_fault(FaultId id, FaultSeverity sev,
                                      const char* desc) noexcept {
    FaultRecord* existing = nullptr;
    FaultRecord* free_slot = nullptr;
    FaultCallback cb_copy;
    FaultRecord rec_copy;

    {
        std::unique_lock lk(mtx_);
        for (auto& r : table_) {
            if (r.state != FaultState::INACTIVE && r.id == id) {
                existing = &r; break;
            }
            if (r.state == FaultState::INACTIVE && !free_slot) free_slot = &r;
        }

        if (existing) {
            existing->occurrence_count++;
            if (sev > existing->severity) existing->severity = sev;
        } else {
            if (!free_slot) return fms::FmsError::ERR_BUFFER_FULL;
            free_slot->id              = id;
            free_slot->severity        = sev;
            free_slot->state           = FaultState::ACTIVE;
            free_slot->occurrence_count = 1;
            std::strncpy(free_slot->description, desc, sizeof(free_slot->description) - 1);
            count_++;
        }

        // CRITICAL → LATCHED immediately
        FaultRecord* rec = existing ? existing : free_slot;
        if (rec->severity == FaultSeverity::CRITICAL) rec->state = FaultState::LATCHED;

        cb_copy  = callback_;
        rec_copy = *rec;
    }
    // Invoke callback outside lock
    if (cb_copy) cb_copy(rec_copy);
    return fms::FmsError::OK;
}

fms::FmsError FaultManager::clear_fault(FaultId id) noexcept {
    std::unique_lock lk(mtx_);
    FaultRecord* rec = find_record(id);
    if (!rec) return fms::FmsError::ERR_NOT_FOUND;
    if (rec->state == FaultState::LATCHED) return fms::FmsError::ERR_FAULT_LATCHED;
    rec->state = FaultState::INACTIVE;
    if (count_ > 0) --count_;
    return fms::FmsError::OK;
}

bool FaultManager::is_fault_active(FaultId id) const noexcept {
    std::unique_lock lk(mtx_);
    const auto* rec = find_record(id);
    return rec && (rec->state != FaultState::INACTIVE);
}

uint32_t FaultManager::get_active_fault_count() const noexcept {
    std::unique_lock lk(mtx_);
    return count_;
}

fms::SystemStatus FaultManager::get_worst_status() const noexcept {
    std::unique_lock lk(mtx_);
    fms::SystemStatus worst = fms::SystemStatus::NORMAL;
    for (const auto& r : table_) {
        if (r.state == FaultState::INACTIVE) continue;
        fms::SystemStatus s = fms::SystemStatus::NORMAL;
        switch (r.severity) {
            case FaultSeverity::WARNING:  s = fms::SystemStatus::WARNING;  break;
            case FaultSeverity::CAUTION:  s = fms::SystemStatus::CAUTION;  break;
            case FaultSeverity::CRITICAL: s = fms::SystemStatus::FAILED;   break;
            default: break;
        }
        if (s > worst) worst = s;
    }
    return worst;
}

void FaultManager::set_fault_callback(FaultCallback cb) noexcept {
    std::unique_lock lk(mtx_);
    callback_ = std::move(cb);
}

}  // namespace fms::safety
