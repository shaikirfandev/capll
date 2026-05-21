/**
 * @file BluetoothController.cpp
 * @brief Simulated Bluetooth Controller — production-quality HCI stub
 *
 * In production this layer wraps the vendor HCI transport (e.g. Qualcomm QCA6391
 * UART H4, NXP KW45 SDIO, TI CC2652 SPI). For simulation and unit testing,
 * this implementation uses an internal state machine and queued callbacks.
 *
 * Singleton pattern: only one controller instance per process (matches hardware).
 */

#include "bt/BluetoothController.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <atomic>
#include <thread>
#include <queue>
#include <condition_variable>
#include <chrono>
#include <cassert>
#include <cstring>
#include <algorithm>

static constexpr const char *TAG = "BluetoothController";

namespace bt {

// ─────────────────────────────────────────────────────────────────────────────
// Internal implementation structure
// ─────────────────────────────────────────────────────────────────────────────
struct BluetoothController::Impl {
    std::atomic<bool>          initialised{false};
    BtMode                     mode{BtMode::BLE_ONLY};
    PowerState                 power_state{PowerState::OFF};
    BdAddr                     public_addr{0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    BdAddr                     random_addr{};
    std::string                device_name{"BT_FW_v2.1"};
    int8_t                     tx_power_dbm{0};

    // Advertising state
    std::atomic<bool>          advertising{false};
    AdvParams                  adv_params{};
    AdvData                    adv_data{};
    AdvData                    scan_rsp{};

    // Scanning state
    std::atomic<bool>          scanning{false};

    // Registered callbacks
    HciEventCb                 event_cb{};
    HciAclDataCb               acl_cb{};

    // Connection tracking (sim: up to 8 simultaneous)
    static constexpr uint8_t MAX_CONNS = 8U;
    struct ConnEntry {
        ConnHandle handle{INVALID_CONN_HANDLE};
        BdAddr     peer_addr{};
        bool       active{false};
        int8_t     rssi{-70};
    };
    std::array<ConnEntry, MAX_CONNS> connections{};
    ConnHandle next_handle{0x0001U};

    // Mutex protecting all state (except atomics)
    mutable std::mutex mtx;

    // Background "event pump" thread — simulates async HCI events
    std::thread        event_thread;
    std::atomic<bool>  event_thread_running{false};

    // Event queue for simulate_* helpers used in tests
    struct SimEvent {
        std::function<void()> fn;
    };
    std::queue<SimEvent>       pending_events;
    std::condition_variable    event_cv;
    std::mutex                 event_q_mtx;
};

// ─────────────────────────────────────────────────────────────────────────────
// Singleton
// ─────────────────────────────────────────────────────────────────────────────
BluetoothController &BluetoothController::instance() {
    static BluetoothController controller;
    return controller;
}

BluetoothController::BluetoothController()
    : impl_(std::make_unique<Impl>()) {}

BluetoothController::~BluetoothController() {
    shutdown();
}

// ─────────────────────────────────────────────────────────────────────────────
// Lifecycle
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::initialise(BtMode mode) {
    std::lock_guard<std::mutex> lock(impl_->mtx);

    if (impl_->initialised.load()) {
        BT_LOG_WARN(TAG, "Already initialised — call reset() first");
        return BtError::ERR_INVALID_STATE;
    }

    BT_LOG_INFO(TAG, "Initialising Bluetooth controller, mode={}",
                static_cast<int>(mode));

    impl_->mode        = mode;
    impl_->power_state = PowerState::ACTIVE;
    impl_->initialised.store(true);

    // Start event pump thread
    impl_->event_thread_running.store(true);
    impl_->event_thread = std::thread([this]() {
        while (impl_->event_thread_running.load()) {
            std::unique_lock<std::mutex> q_lock(impl_->event_q_mtx);
            impl_->event_cv.wait_for(q_lock, std::chrono::milliseconds(50),
                [this] { return !impl_->pending_events.empty() ||
                                !impl_->event_thread_running.load(); });
            while (!impl_->pending_events.empty()) {
                auto ev = std::move(impl_->pending_events.front());
                impl_->pending_events.pop();
                q_lock.unlock();
                if (ev.fn) { ev.fn(); }
                q_lock.lock();
            }
        }
    });

    BT_LOG_INFO(TAG, "Controller initialised, device addr={}",
                format_bdaddr(impl_->public_addr));
    return BtError::OK;
}

BtError BluetoothController::reset() {
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        BT_LOG_INFO(TAG, "HCI Reset");
        impl_->advertising.store(false);
        impl_->scanning.store(false);
        for (auto &c : impl_->connections) {
            c.active = false;
            c.handle = INVALID_CONN_HANDLE;
        }
        impl_->next_handle = 0x0001U;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(20));  // Simulate reset delay
    return BtError::OK;
}

void BluetoothController::shutdown() {
    if (!impl_->initialised.load()) { return; }

    BT_LOG_INFO(TAG, "Shutting down controller");

    impl_->event_thread_running.store(false);
    impl_->event_cv.notify_all();
    if (impl_->event_thread.joinable()) {
        impl_->event_thread.join();
    }

    impl_->advertising.store(false);
    impl_->scanning.store(false);
    impl_->power_state = PowerState::OFF;
    impl_->initialised.store(false);
}

// ─────────────────────────────────────────────────────────────────────────────
// Identity
// ─────────────────────────────────────────────────────────────────────────────
BdAddr BluetoothController::get_public_address() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->public_addr;
}

BtError BluetoothController::set_random_address(const BdAddr &addr) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->random_addr = addr;
    BT_LOG_DEBUG(TAG, "Random addr set to {}", format_bdaddr(addr));
    return BtError::OK;
}

BtError BluetoothController::set_device_name(std::string_view name) {
    if (name.empty() || name.size() > 248U) {
        return BtError::ERR_INVALID_PARAM;
    }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->device_name = std::string(name);
    BT_LOG_INFO(TAG, "Device name set to '{}'", impl_->device_name);
    return BtError::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// HCI transport (simulated)
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::send_hci_command(uint16_t opcode,
                                               const uint8_t *params,
                                               uint8_t len) {
    if (!impl_->initialised.load()) { return BtError::ERR_INVALID_STATE; }
    BT_LOG_DEBUG(TAG, "HCI cmd opcode=0x{:04X} param_len={}", opcode, len);
    (void)params;
    // Simulate Command Complete event asynchronously
    if (impl_->event_cb) {
        std::array<uint8_t, 6> cc_event{
            0x0EU, 0x04U,         // HCI Event: Command Complete
            0x01U,                 // Num HCI commands
            static_cast<uint8_t>(opcode & 0xFFU),
            static_cast<uint8_t>((opcode >> 8U) & 0xFFU),
            0x00U                  // Status: success
        };
        {
            std::lock_guard<std::mutex> q_lock(impl_->event_q_mtx);
            impl_->pending_events.push({[this, cc_event]() {
                if (impl_->event_cb) {
                    impl_->event_cb(cc_event.data(),
                                   static_cast<uint16_t>(cc_event.size()));
                }
            }});
        }
        impl_->event_cv.notify_one();
    }
    return BtError::OK;
}

BtError BluetoothController::send_acl_data(ConnHandle handle,
                                             const uint8_t *data,
                                             uint16_t len) {
    if (!impl_->initialised.load()) { return BtError::ERR_INVALID_STATE; }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    bool found = false;
    for (const auto &c : impl_->connections) {
        if (c.active && c.handle == handle) { found = true; break; }
    }
    if (!found) {
        BT_LOG_WARN(TAG, "send_acl_data: handle 0x{:04X} not connected", handle);
        return BtError::ERR_NOT_CONNECTED;
    }
    BT_LOG_DEBUG(TAG, "ACL TX handle=0x{:04X} len={}", handle, len);
    (void)data;
    return BtError::OK;
}

void BluetoothController::register_event_callback(HciEventCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->event_cb = std::move(cb);
}

void BluetoothController::register_acl_callback(HciAclDataCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->acl_cb = std::move(cb);
}

// ─────────────────────────────────────────────────────────────────────────────
// BLE operations
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::start_advertising(const AdvParams &params,
                                                const AdvData   &adv_data,
                                                const AdvData   &scan_rsp) {
    if (!impl_->initialised.load()) { return BtError::ERR_INVALID_STATE; }
    if (impl_->advertising.load()) {
        BT_LOG_WARN(TAG, "Already advertising");
        return BtError::ERR_INVALID_STATE;
    }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->adv_params  = params;
    impl_->adv_data    = adv_data;
    impl_->scan_rsp    = scan_rsp;
    impl_->advertising.store(true);
    BT_LOG_INFO(TAG, "Advertising started interval=[{}-{}]ms type={}",
                params.interval_min_ms, params.interval_max_ms,
                static_cast<int>(params.type));
    return BtError::OK;
}

BtError BluetoothController::stop_advertising() {
    if (!impl_->advertising.load()) {
        return BtError::ERR_INVALID_STATE;
    }
    impl_->advertising.store(false);
    BT_LOG_INFO(TAG, "Advertising stopped");
    return BtError::OK;
}

BtError BluetoothController::start_scan(uint16_t window_ms,
                                          uint16_t interval_ms,
                                          bool     active_scan,
                                          bool     filter_duplicates) {
    if (!impl_->initialised.load()) { return BtError::ERR_INVALID_STATE; }
    impl_->scanning.store(true);
    BT_LOG_INFO(TAG, "Scan started window={}ms interval={}ms active={} dedup={}",
                window_ms, interval_ms, active_scan, filter_duplicates);
    return BtError::OK;
}

BtError BluetoothController::stop_scan() {
    impl_->scanning.store(false);
    BT_LOG_INFO(TAG, "Scan stopped");
    return BtError::OK;
}

BtError BluetoothController::create_ble_connection(const BdAddr &peer_addr,
                                                     bool peer_is_random) {
    if (!impl_->initialised.load()) { return BtError::ERR_INVALID_STATE; }
    BT_LOG_INFO(TAG, "Initiating BLE connection to {} (random={})",
                format_bdaddr(peer_addr), peer_is_random);

    // Simulate async LE Connection Complete event after 50ms
    {
        std::lock_guard<std::mutex> q_lock(impl_->event_q_mtx);
        impl_->pending_events.push({[this, peer_addr]() {
            std::lock_guard<std::mutex> lock(impl_->mtx);
            // Find free slot
            for (auto &c : impl_->connections) {
                if (!c.active) {
                    c.handle    = impl_->next_handle++;
                    c.peer_addr = peer_addr;
                    c.active    = true;
                    c.rssi      = -65;
                    BT_LOG_INFO(TAG, "LE Connected: handle=0x{:04X} peer={}",
                                c.handle, format_bdaddr(peer_addr));
                    // Deliver LE Connection Complete event to upper stack
                    if (impl_->event_cb) {
                        std::array<uint8_t, 19> le_conn{};
                        le_conn[0] = 0x3EU;  // LE Meta
                        le_conn[1] = 17U;    // length
                        le_conn[2] = 0x01U;  // LE Connection Complete subevent
                        le_conn[3] = 0x00U;  // Status: success
                        le_conn[4] = static_cast<uint8_t>(c.handle & 0xFFU);
                        le_conn[5] = static_cast<uint8_t>((c.handle >> 8U) & 0xFFU);
                        // ... (remaining fields: role, addr type, addr, interval, latency, timeout, accuracy)
                        impl_->event_cb(le_conn.data(),
                                       static_cast<uint16_t>(le_conn.size()));
                    }
                    return;
                }
            }
            BT_LOG_ERROR(TAG, "No free connection slot!");
        }});
    }
    impl_->event_cv.notify_one();
    return BtError::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// Classic BT
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::set_connectable(bool enable) {
    BT_LOG_INFO(TAG, "Connectable = {}", enable);
    return BtError::OK;
}

BtError BluetoothController::set_discoverable(bool enable, uint16_t timeout_sec) {
    BT_LOG_INFO(TAG, "Discoverable = {} timeout={}s", enable, timeout_sec);
    return BtError::OK;
}

BtError BluetoothController::start_inquiry(uint8_t duration_s, uint8_t max_responses) {
    BT_LOG_INFO(TAG, "Inquiry started duration={}s max_rsp={}", duration_s, max_responses);
    return BtError::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// Connection management
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::disconnect(ConnHandle handle, uint8_t reason) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    for (auto &c : impl_->connections) {
        if (c.active && c.handle == handle) {
            BT_LOG_INFO(TAG, "Disconnecting handle=0x{:04X} reason=0x{:02X}",
                        handle, reason);
            c.active = false;
            c.handle = INVALID_CONN_HANDLE;
            // Fire Disconnection Complete event
            if (impl_->event_cb) {
                std::array<uint8_t, 6> dc_event{
                    0x05U, 0x04U,  // Disconnection Complete
                    0x00U,          // Status: success
                    static_cast<uint8_t>(handle & 0xFFU),
                    static_cast<uint8_t>((handle >> 8U) & 0xFFU),
                    reason
                };
                impl_->event_cb(dc_event.data(),
                               static_cast<uint16_t>(dc_event.size()));
            }
            return BtError::OK;
        }
    }
    return BtError::ERR_NOT_CONNECTED;
}

BtError BluetoothController::update_conn_params(ConnHandle handle,
                                                  uint16_t interval_min_ms,
                                                  uint16_t interval_max_ms,
                                                  uint16_t latency,
                                                  uint16_t supervision_timeout_ms) {
    BT_LOG_DEBUG(TAG, "Conn param update hdl=0x{:04X} int=[{}-{}]ms lat={} STO={}ms",
                 handle, interval_min_ms, interval_max_ms, latency, supervision_timeout_ms);
    return BtError::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// Power management
// ─────────────────────────────────────────────────────────────────────────────
BtError BluetoothController::set_power_state(PowerState state) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_INFO(TAG, "Power state: {} -> {}",
                static_cast<int>(impl_->power_state), static_cast<int>(state));
    impl_->power_state = state;
    return BtError::OK;
}

PowerState BluetoothController::get_power_state() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->power_state;
}

BtError BluetoothController::set_tx_power(int8_t dbm) {
    if (dbm < -40 || dbm > 20) { return BtError::ERR_INVALID_PARAM; }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->tx_power_dbm = dbm;
    BT_LOG_INFO(TAG, "TX power set to {} dBm", dbm);
    return BtError::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// Diagnostics
// ─────────────────────────────────────────────────────────────────────────────
int8_t BluetoothController::get_rssi(ConnHandle handle) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    for (const auto &c : impl_->connections) {
        if (c.active && c.handle == handle) { return c.rssi; }
    }
    return 0;
}

IBluetoothController::ControllerVersion BluetoothController::get_version() const {
    return ControllerVersion{
        .hci_version    = 0x0CU,   // BT 5.3
        .hci_revision   = 0x0001U,
        .lmp_version    = 0x0CU,
        .manufacturer_id= 0x000FU, // Broadcom/Cypress (sim)
        .lmp_subversion = 0x4208U
    };
}

}  // namespace bt
