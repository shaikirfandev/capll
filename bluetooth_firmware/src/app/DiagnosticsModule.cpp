/**
 * @file DiagnosticsModule.cpp
 * @brief Health monitoring and telemetry diagnostics
 */
#include "app/DiagnosticsModule.hpp"
#include "common/Logger.hpp"
#include <sstream>
#include <iomanip>
#include <chrono>
#include <mutex>
#include <deque>

static constexpr const char *TAG = "Diagnostics";

namespace bt::app {

struct DiagnosticsModule::Impl {
    BtHealthStats stats{};
    std::deque<std::string> event_log;  // Rolling window of last 100 events
    mutable std::mutex mtx;
    static constexpr uint32_t MAX_LOG_ENTRIES = 100U;
};

DiagnosticsModule::DiagnosticsModule() : impl_(std::make_unique<Impl>()) {}
DiagnosticsModule::~DiagnosticsModule() = default;

const BtHealthStats &DiagnosticsModule::get_stats() const {
    return impl_->stats;  // Lock-free read of atomics; stats struct may need atomic members in production
}

void DiagnosticsModule::reset_stats() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->stats = BtHealthStats{};
    impl_->event_log.clear();
    BT_LOG_INFO(TAG, "Stats reset");
}

std::string DiagnosticsModule::generate_report() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    const auto &s = impl_->stats;
    std::ostringstream oss;
    oss << "=== Bluetooth Diagnostics Report ===\n"
        << "  TX bytes          : " << s.tx_bytes << "\n"
        << "  RX bytes          : " << s.rx_bytes << "\n"
        << "  Connections       : " << s.conn_count << "\n"
        << "  Disconnections    : " << s.disconn_count << "\n"
        << "  Pairing failures  : " << s.pairing_failures << "\n"
        << "  HCI errors        : " << s.hci_errors << "\n"
        << "  OTA attempts      : " << s.ota_attempts << "\n"
        << "  OTA success       : " << s.ota_success << "\n"
        << "  Last RSSI         : " << static_cast<int>(s.last_rssi) << " dBm\n"
        << "  Avg conn interval : " << std::fixed << std::setprecision(1)
                                    << s.avg_conn_interval_ms << " ms\n"
        << "=== Last " << impl_->event_log.size() << " Events ===\n";
    for (const auto &entry : impl_->event_log) {
        oss << "  " << entry << "\n";
    }
    return oss.str();
}

void DiagnosticsModule::record_event(std::string_view component, std::string_view event) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->event_log.size() >= Impl::MAX_LOG_ENTRIES) {
        impl_->event_log.pop_front();
    }
    impl_->event_log.emplace_back(std::string("[") + std::string(component) + "] " +
                                   std::string(event));
    BT_LOG_DEBUG(TAG, "[{}] {}", component, event);
}

}  // namespace bt::app
