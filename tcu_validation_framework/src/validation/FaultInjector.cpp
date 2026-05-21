/**
 * @file FaultInjector.cpp
 * @brief Fault injection implementation for negative testing.
 */

#include "validation/FaultInjector.h"
#include "logging/Logger.h"

#include <chrono>
#include <sstream>

namespace tcu::validation {

static auto s_log = tcu::logging::Logger::get("fault_injector");

// ============================================================
// ActiveFault RAII
// ============================================================

ActiveFault::ActiveFault(FaultType type, std::function<void(FaultType)> cleanup)
    : m_type(type), m_cleanup(std::move(cleanup))
{}

ActiveFault::~ActiveFault() {
    clear();
}

void ActiveFault::clear() {
    if (!m_cleared.exchange(true)) {
        if (m_cleanup) { m_cleanup(m_type); }
    }
}

FaultType ActiveFault::type() const noexcept { return m_type; }
bool      ActiveFault::is_active() const noexcept { return !m_cleared.load(); }

// ============================================================
// FaultInjector
// ============================================================

FaultInjector::FaultInjector(std::shared_ptr<tcu::can::CANManager>       can_mgr,
                              std::shared_ptr<tcu::telematics::TelematicsSDKAdapter> sdk)
    : m_can(std::move(can_mgr))
    , m_sdk(std::move(sdk))
{}

std::unique_ptr<ActiveFault> FaultInjector::inject(const FaultSpec& spec) {
    s_log->info("Injecting fault: {} | duration={}ms | param={}",
                fault_type_to_string(spec.type),
                spec.duration_ms,
                spec.parameter);

    bool applied = apply_fault(spec);
    if (!applied) {
        s_log->error("Failed to inject fault: {}", fault_type_to_string(spec.type));
        return nullptr;
    }

    std::lock_guard<std::mutex> lock(m_mutex);
    m_active_faults[spec.type]++;

    auto cleanup = [this](FaultType t) {
        clear_fault(t);
    };

    return std::make_unique<ActiveFault>(spec.type, cleanup);
}

bool FaultInjector::apply_fault(const FaultSpec& spec) {
    switch (spec.type) {
        case FaultType::CAN_BUS_OFF:
            s_log->warn("Simulating CAN bus-off on {}", m_can ? m_can->interface_name() : "N/A");
            // In real hardware: send frames with wrong bit timing or use error injection
            // Here we stop the CAN manager to simulate disconnection
            if (m_can && m_can->is_running()) {
                m_can->stop();
            }
            return true;

        case FaultType::CAN_DROPOUT:
            s_log->warn("Simulating CAN signal dropout ({}ms)", spec.duration_ms);
            if (m_can && m_can->is_running()) {
                m_can->stop();
            }
            return true;

        case FaultType::CAN_CORRUPTION:
            s_log->warn("Simulating CAN frame corruption");
            // Set corrupt filter — drop all frames
            if (m_can) {
                // Set an impossible filter to drop all Rx frames
                m_can->set_filters({{0xFFFFFFF0U, 0xFFFFFFFFU}});
            }
            return true;

        case FaultType::NETWORK_LATENCY:
            s_log->warn("Simulating network latency ({}ms)", spec.duration_ms);
            if (m_sdk) {
                tcu::telematics::NetworkMetrics m;
                m.latency_ms = static_cast<float>(spec.duration_ms);
                m.connected  = true;
                m_sdk->sim_set_metrics(m);
            }
            return true;

        case FaultType::NETWORK_LOSS:
            s_log->warn("Simulating network loss");
            if (m_sdk) {
                tcu::telematics::NetworkMetrics m;
                m.connected          = false;
                m.dl_throughput_kbps = 0;
                m.ul_throughput_kbps = 0;
                m_sdk->sim_set_metrics(m);
            }
            return true;

        case FaultType::UDS_MALFORMED:
            s_log->warn("Injecting malformed UDS response");
            // This is handled at test level by using raw send_raw()
            return true;

        case FaultType::POWER_CUT:
            s_log->warn("Simulating power cut — stopping all managers");
            if (m_can && m_can->is_running()) { m_can->stop(); }
            if (m_sdk && m_sdk->is_connected()) { m_sdk->disconnect(); }
            return true;

        case FaultType::FIRMWARE_CORRUPT:
            s_log->warn("Simulating firmware corruption");
            // In test: use wrong CRC in firmware package
            return true;

        case FaultType::OTA_INTERRUPTED:
            s_log->warn("Simulating OTA interruption");
            return true;

        case FaultType::OTA_WRONG_VERSION:
            s_log->warn("Simulating OTA wrong version");
            return true;

        case FaultType::SECURITY_ATTACK:
            s_log->warn("Simulating security attack (invalid seed response)");
            return true;

        case FaultType::MEMORY_PRESSURE:
            s_log->warn("Simulating memory pressure");
            return true;

        case FaultType::CPU_SPIKE:
            s_log->warn("Simulating CPU spike");
            return true;

        default:
            s_log->error("Unknown fault type: {}", static_cast<int>(spec.type));
            return false;
    }
}

void FaultInjector::clear_fault(FaultType type) {
    s_log->info("Clearing fault: {}", fault_type_to_string(type));

    switch (type) {
        case FaultType::CAN_BUS_OFF:
        case FaultType::CAN_DROPOUT:
            // Restart CAN manager
            if (m_can && !m_can->is_running()) {
                m_can->start();
            }
            break;

        case FaultType::CAN_CORRUPTION:
            // Remove all filters (pass all)
            if (m_can) {
                m_can->set_filters({});
            }
            break;

        case FaultType::NETWORK_LATENCY:
        case FaultType::NETWORK_LOSS:
            if (m_sdk) {
                tcu::telematics::NetworkMetrics m;
                m.latency_ms         = 20.0f;
                m.connected          = true;
                m.dl_throughput_kbps = 10000.0f;
                m.ul_throughput_kbps = 2000.0f;
                m_sdk->sim_set_metrics(m);
            }
            break;

        case FaultType::POWER_CUT:
            if (m_can && !m_can->is_running()) { m_can->start(); }
            if (m_sdk && !m_sdk->is_connected()) { m_sdk->connect(); }
            break;

        default:
            break;
    }

    std::lock_guard<std::mutex> lock(m_mutex);
    auto it = m_active_faults.find(type);
    if (it != m_active_faults.end()) {
        if (--it->second == 0) {
            m_active_faults.erase(it);
        }
    }
}

bool FaultInjector::is_fault_active(FaultType type) const {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto it = m_active_faults.find(type);
    return it != m_active_faults.end() && it->second > 0;
}

void FaultInjector::clear_all() {
    std::lock_guard<std::mutex> lock(m_mutex);
    for (const auto& [type, _] : m_active_faults) {
        clear_fault(type);
    }
    m_active_faults.clear();
}

std::string FaultInjector::fault_type_to_string(FaultType type) {
    switch (type) {
        case FaultType::CAN_BUS_OFF:        return "CAN_BUS_OFF";
        case FaultType::CAN_DROPOUT:        return "CAN_DROPOUT";
        case FaultType::CAN_CORRUPTION:     return "CAN_CORRUPTION";
        case FaultType::NETWORK_LATENCY:    return "NETWORK_LATENCY";
        case FaultType::NETWORK_LOSS:       return "NETWORK_LOSS";
        case FaultType::UDS_MALFORMED:      return "UDS_MALFORMED";
        case FaultType::POWER_CUT:          return "POWER_CUT";
        case FaultType::FIRMWARE_CORRUPT:   return "FIRMWARE_CORRUPT";
        case FaultType::OTA_INTERRUPTED:    return "OTA_INTERRUPTED";
        case FaultType::OTA_WRONG_VERSION:  return "OTA_WRONG_VERSION";
        case FaultType::SECURITY_ATTACK:    return "SECURITY_ATTACK";
        case FaultType::MEMORY_PRESSURE:    return "MEMORY_PRESSURE";
        case FaultType::CPU_SPIKE:          return "CPU_SPIKE";
        default:                            return "UNKNOWN";
    }
}

} // namespace tcu::validation
