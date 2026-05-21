/**
 * @file fault_manager.cpp
 * @brief DTC fault management implementation.
 */

#include "fault_manager.hpp"
#include "logger.hpp"

#include <chrono>
#include <cstdio>
#include <iostream>

namespace adas {
namespace diag {

static uint64_t nowUs() {
    using namespace std::chrono;
    return duration_cast<microseconds>(
        steady_clock::now().time_since_epoch()).count();
}

const char* faultCodeToString(FaultCode code) {
    switch (code) {
        case FaultCode::NONE:                       return "NONE";
        case FaultCode::CAMERA_SIGNAL_LOST:         return "CAMERA_SIGNAL_LOST";
        case FaultCode::RADAR_SIGNAL_LOST:          return "RADAR_SIGNAL_LOST";
        case FaultCode::LIDAR_SIGNAL_LOST:          return "LIDAR_SIGNAL_LOST";
        case FaultCode::EKF_DIVERGENCE:             return "EKF_DIVERGENCE";
        case FaultCode::PLANNING_TIMEOUT:           return "PLANNING_TIMEOUT";
        case FaultCode::CONTROL_ACTUATOR_FAULT:     return "CONTROL_ACTUATOR_FAULT";
        case FaultCode::CAN_TX_TIMEOUT:             return "CAN_TX_TIMEOUT";
        case FaultCode::CAN_RX_TIMEOUT:             return "CAN_RX_TIMEOUT";
        case FaultCode::CPU_OVERLOAD:               return "CPU_OVERLOAD";
        case FaultCode::MEMORY_CORRUPTION:          return "MEMORY_CORRUPTION";
        case FaultCode::WATCHDOG_TIMEOUT:           return "WATCHDOG_TIMEOUT";
        case FaultCode::RT_DEADLINE_MISS_CRITICAL:  return "RT_DEADLINE_MISS_CRITICAL";
        default:                                    return "UNKNOWN";
    }
}

bool FaultManager::isFatal(FaultCode code) {
    return code == FaultCode::MEMORY_CORRUPTION ||
           code == FaultCode::WATCHDOG_TIMEOUT  ||
           code == FaultCode::CONTROL_ACTUATOR_FAULT;
}

// ─── Singleton ────────────────────────────────────────────────────────────────

FaultManager& FaultManager::instance() {
    static FaultManager fm;
    return fm;
}

void FaultManager::registerSafeStateCallback(SafeStateCallback cb) {
    std::lock_guard<std::mutex> lock(mutex_);
    safe_state_cb_ = std::move(cb);
}

// ─── Report ───────────────────────────────────────────────────────────────────

void FaultManager::reportFault(FaultCode code, const char* context) {
    const uint64_t now = nowUs();
    const uint16_t key = static_cast<uint16_t>(code);

    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = records_.find(key);

        if (it == records_.end()) {
            // New fault: PENDING → ACTIVE on first report
            FaultRecord rec{};
            rec.code                 = code;
            rec.status               = FaultStatus::ACTIVE;
            rec.occurrence_count     = 1;
            rec.first_occurrence_us  = now;
            rec.last_occurrence_us   = now;
            std::snprintf(rec.context, sizeof(rec.context), "%s", context);
            records_[key] = rec;
        } else {
            auto& rec            = it->second;
            rec.status           = FaultStatus::ACTIVE;
            rec.last_occurrence_us = now;
            ++rec.occurrence_count;
        }
    }

    ADAS_LOG_ERROR("FAULT_MGR", "DTC %04X (%s): %s",
                   static_cast<unsigned>(code),
                   faultCodeToString(code),
                   context);

    if (isFatal(code)) {
        ADAS_LOG_FATAL("FAULT_MGR", "FATAL fault %04X → triggering safe state",
                       static_cast<unsigned>(code));
        SafeStateCallback cb;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            cb = safe_state_cb_;
        }
        if (cb) cb(code);
    }
}

void FaultManager::healFault(FaultCode code) {
    const uint16_t key = static_cast<uint16_t>(code);
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = records_.find(key);
        if (it != records_.end() && it->second.status == FaultStatus::ACTIVE) {
            it->second.status = FaultStatus::HEALED;
        }
    }
    ADAS_LOG_INFO("FAULT_MGR", "DTC %04X (%s) HEALED",
                  static_cast<unsigned>(code),
                  faultCodeToString(code));
}

void FaultManager::clearFaults() {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto it = records_.begin(); it != records_.end(); ) {
        if (it->second.status == FaultStatus::HEALED ||
            it->second.status == FaultStatus::INACTIVE) {
            it = records_.erase(it);
        } else {
            ++it;
        }
    }
}

std::vector<FaultRecord> FaultManager::getActiveFaults() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<FaultRecord> out;
    for (const auto& [key, rec] : records_) {
        if (rec.status == FaultStatus::ACTIVE ||
            rec.status == FaultStatus::HEALED) {
            out.push_back(rec);
        }
    }
    return out;
}

bool FaultManager::hasActiveFaults() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& [key, rec] : records_) {
        if (rec.status == FaultStatus::ACTIVE) return true;
    }
    return false;
}

void FaultManager::dump() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::printf("┌─────── Active Fault Records ───────────────────────────────┐\n");
    for (const auto& [key, rec] : records_) {
        const char* status_str = "";
        switch (rec.status) {
            case FaultStatus::ACTIVE:   status_str = "ACTIVE";   break;
            case FaultStatus::HEALED:   status_str = "HEALED";   break;
            case FaultStatus::PENDING:  status_str = "PENDING";  break;
            case FaultStatus::INACTIVE: status_str = "INACTIVE"; break;
        }
        std::printf("│ DTC %04X %-30s [%s] x%u\n",
                    key,
                    faultCodeToString(rec.code),
                    status_str,
                    rec.occurrence_count);
    }
    std::printf("└───────────────────────────────────────────────────────────┘\n");
}

}  // namespace diag
}  // namespace adas
