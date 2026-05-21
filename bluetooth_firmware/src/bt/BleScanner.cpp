/**
 * @file BleScanner.cpp  AttProtocol.cpp  L2capManager.cpp  GattClient.cpp
 * @note Each class has its own .cpp — combined here for brevity in this file
 */

#include "bt/BleScanner.hpp"
#include "bt/IBluetoothController.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <thread>
#include <chrono>
#include <random>

static constexpr const char *TAG = "BleScanner";

namespace bt {

struct BleScanner::Impl {
    IBluetoothController *controller{nullptr};
    std::atomic<bool>     scanning{false};
    ScanResultCb          scan_cb;
    int8_t                rssi_filter{-127};  // no filter by default
    mutable std::mutex    mtx;

    // Simulation: background thread fires fake scan results
    std::thread           sim_thread;
    std::atomic<bool>     sim_running{false};

    void run_sim() {
        std::mt19937 rng{42U};
        std::uniform_int_distribution<int> rssi_dist(-90, -40);
        static const BdAddr fake_addrs[] = {
            {0x01,0x23,0x45,0x67,0x89,0xABU},
            {0xAA,0xBB,0xCC,0xDD,0xEE,0xFFU},
            {0x11,0x22,0x33,0x44,0x55,0x66U},
        };
        uint32_t idx = 0;
        while (sim_running.load() && scanning.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(300));
            if (!scanning.load()) break;
            EvtBleAdv result{};
            result.peer_addr = fake_addrs[idx % 3U];
            result.rssi      = static_cast<int8_t>(rssi_dist(rng));
            result.type      = AdvType::ADV_IND;
            // Minimal adv data: Flags
            result.adv_data  = {0x02, 0x01, 0x06};
            idx++;
            std::lock_guard<std::mutex> lock(mtx);
            if (scan_cb && result.rssi >= rssi_filter) {
                scan_cb(result);
            }
        }
    }
};

BleScanner::BleScanner(IBluetoothController *controller)
    : impl_(std::make_unique<Impl>()) {
    impl_->controller = controller;
}

BleScanner::~BleScanner() {
    if (impl_->scanning.load()) { (void)stop_scan(); }
    impl_->sim_running.store(false);
    if (impl_->sim_thread.joinable()) { impl_->sim_thread.join(); }
}

BtError BleScanner::start_scan(uint16_t window_ms, uint16_t interval_ms,
                                 bool active, bool filter_dup) {
    if (impl_->scanning.load()) {
        return BtError::ERR_INVALID_STATE;
    }
    BtError err = impl_->controller->start_scan(window_ms, interval_ms, active, filter_dup);
    if (err != BtError::OK) return err;
    impl_->scanning.store(true);
    impl_->sim_running.store(true);
    impl_->sim_thread = std::thread(&Impl::run_sim, impl_.get());
    BT_LOG_INFO(TAG, "Scan started window={}ms interval={}ms", window_ms, interval_ms);
    return BtError::OK;
}

BtError BleScanner::stop_scan() {
    impl_->scanning.store(false);
    impl_->sim_running.store(false);
    if (impl_->sim_thread.joinable()) { impl_->sim_thread.join(); }
    impl_->controller->stop_scan();
    BT_LOG_INFO(TAG, "Scan stopped");
    return BtError::OK;
}

void BleScanner::set_scan_callback(ScanResultCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->scan_cb = std::move(cb);
}

bool BleScanner::is_scanning() const { return impl_->scanning.load(); }

BtError BleScanner::set_rssi_filter(int8_t min_rssi) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->rssi_filter = min_rssi;
    return BtError::OK;
}

}  // namespace bt
