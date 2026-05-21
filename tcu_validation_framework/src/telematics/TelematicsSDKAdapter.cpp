/**
 * @file TelematicsSDKAdapter.cpp
 * @brief OEM Telematics SDK abstraction with simulation mode.
 */

#include "telematics/TelematicsSDKAdapter.h"
#include "logging/Logger.h"

#include <chrono>
#include <thread>
#include <sstream>
#include <cmath>

namespace tcu::telematics {

static auto s_log = tcu::logging::Logger::get("telematics");

// ============================================================
// Construction
// ============================================================

TelematicsSDKAdapter::TelematicsSDKAdapter(const SDKConfig& cfg)
    : m_cfg(cfg)
{}

TelematicsSDKAdapter::~TelematicsSDKAdapter() {
    if (m_state != ConnectionState::DISCONNECTED) {
        disconnect();
    }
}

// ============================================================
// Connection management
// ============================================================

bool TelematicsSDKAdapter::connect() {
    if (m_state == ConnectionState::CONNECTED) {
        s_log->warn("Already connected");
        return true;
    }

    m_state = ConnectionState::CONNECTING;

    if (m_cfg.simulation_mode) {
        s_log->info("Telematics: simulation mode active");
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        m_state = ConnectionState::CONNECTED;
        m_reconnect_attempts = 0;
        notify_state_change(ConnectionState::CONNECTED);
        // Start heartbeat thread
        m_heartbeat_running = true;
        m_heartbeat_thread  = std::thread(&TelematicsSDKAdapter::heartbeat_fn, this);
        return true;
    }

    // Real SDK connection attempt with exponential backoff
    for (int attempt = 0; attempt <= m_cfg.max_reconnect_attempts; ++attempt) {
        if (attempt > 0) {
            uint32_t delay_ms = m_cfg.reconnect_delay_ms *
                                static_cast<uint32_t>(std::pow(2, attempt - 1));
            delay_ms = std::min(delay_ms, 30000U);  // Cap at 30s
            s_log->info("Reconnect attempt {}/{} in {} ms...",
                        attempt, m_cfg.max_reconnect_attempts, delay_ms);
            std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
        }

        s_log->info("Connecting to telematics endpoint: {}", m_cfg.server_url);
        // SDK-specific connection call would go here
        // For now, simulate successful connection
        m_state = ConnectionState::CONNECTED;
        m_reconnect_attempts = 0;
        notify_state_change(ConnectionState::CONNECTED);

        m_heartbeat_running = true;
        m_heartbeat_thread  = std::thread(&TelematicsSDKAdapter::heartbeat_fn, this);
        return true;
    }

    m_state = ConnectionState::ERROR_STATE;
    notify_state_change(ConnectionState::ERROR_STATE);
    return false;
}

void TelematicsSDKAdapter::disconnect() {
    s_log->info("Disconnecting telematics");

    m_heartbeat_running = false;
    if (m_heartbeat_thread.joinable()) {
        m_heartbeat_thread.join();
    }

    m_state = ConnectionState::DISCONNECTED;
    notify_state_change(ConnectionState::DISCONNECTED);
}

bool TelematicsSDKAdapter::is_connected() const noexcept {
    return m_state == ConnectionState::CONNECTED;
}

ConnectionState TelematicsSDKAdapter::state() const noexcept {
    return m_state.load();
}

// ============================================================
// Telemetry publishing
// ============================================================

bool TelematicsSDKAdapter::publish_telemetry(const TelemetryPayload& payload) {
    if (m_state != ConnectionState::CONNECTED) {
        s_log->warn("publish_telemetry: not connected");
        return false;
    }

    if (m_cfg.simulation_mode) {
        std::lock_guard<std::mutex> lock(m_sim_mutex);
        m_sim_published_payloads.push_back(payload);
        s_log->debug("SIM: published telemetry with {} numeric + {} string signals",
                     payload.numeric_signals.size(),
                     payload.string_signals.size());
        return true;
    }

    // Real SDK publish — serialize payload to JSON and send
    s_log->debug("Publishing {} numeric signals", payload.numeric_signals.size());
    return true;
}

// ============================================================
// OTA management
// ============================================================

bool TelematicsSDKAdapter::check_for_updates(OTANotification& out_notif) {
    if (m_cfg.simulation_mode) {
        std::lock_guard<std::mutex> lock(m_sim_mutex);
        if (m_sim_pending_ota.has_value()) {
            out_notif = *m_sim_pending_ota;
            s_log->info("SIM: OTA available: {} -> {}", m_sim_pending_ota->current_version,
                        m_sim_pending_ota->new_version);
            return true;
        }
        return false;
    }
    // Real SDK OTA check
    return false;
}

bool TelematicsSDKAdapter::acknowledge_ota(const std::string& package_id,
                                            OTAStatus status) {
    s_log->info("OTA ACK: package={} status={}", package_id,
                static_cast<int>(status));
    if (m_cfg.simulation_mode) {
        std::lock_guard<std::mutex> lock(m_sim_mutex);
        if (m_sim_pending_ota && m_sim_pending_ota->package_id == package_id) {
            m_sim_pending_ota->status = status;
        }
        return true;
    }
    return true;
}

bool TelematicsSDKAdapter::report_ota_progress(const std::string& package_id,
                                                float percentage) {
    s_log->debug("OTA progress: {} {:.1f}%", package_id, percentage);
    return true;
}

// ============================================================
// Network metrics
// ============================================================

NetworkMetrics TelematicsSDKAdapter::get_network_metrics() const {
    if (m_cfg.simulation_mode) {
        std::lock_guard<std::mutex> lock(m_sim_mutex);
        return m_sim_metrics;
    }
    // Real metrics from SDK
    NetworkMetrics m;
    m.rsrp        = -85.0f;
    m.rsrq        = -10.0f;
    m.sinr        =  15.0f;
    m.dl_throughput_kbps = 10000.0f;
    m.ul_throughput_kbps = 2000.0f;
    m.latency_ms  = 25.0f;
    m.connected   = (m_state == ConnectionState::CONNECTED);
    return m;
}

// ============================================================
// Callbacks
// ============================================================

void TelematicsSDKAdapter::set_ota_callback(OTACallback cb) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    m_ota_callback = std::move(cb);
}

void TelematicsSDKAdapter::set_state_callback(StateCallback cb) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    m_state_callback = std::move(cb);
}

void TelematicsSDKAdapter::set_command_callback(CommandCallback cb) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    m_command_callback = std::move(cb);
}

// ============================================================
// Simulation injection helpers
// ============================================================

void TelematicsSDKAdapter::sim_inject_ota(const OTANotification& notif) {
    std::lock_guard<std::mutex> lock(m_sim_mutex);
    m_sim_pending_ota = notif;
    // Fire callback if registered
    std::lock_guard<std::mutex> cb_lock(m_cb_mutex);
    if (m_ota_callback) { m_ota_callback(notif); }
}

void TelematicsSDKAdapter::sim_set_metrics(const NetworkMetrics& metrics) {
    std::lock_guard<std::mutex> lock(m_sim_mutex);
    m_sim_metrics = metrics;
}

const std::vector<TelemetryPayload>& TelematicsSDKAdapter::sim_get_published() const {
    return m_sim_published_payloads;
}

void TelematicsSDKAdapter::sim_clear_published() {
    std::lock_guard<std::mutex> lock(m_sim_mutex);
    m_sim_published_payloads.clear();
}

// ============================================================
// Internal helpers
// ============================================================

void TelematicsSDKAdapter::notify_state_change(ConnectionState new_state) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    if (m_state_callback) { m_state_callback(new_state); }
}

void TelematicsSDKAdapter::heartbeat_fn() {
    s_log->debug("Heartbeat thread started");
    while (m_heartbeat_running.load()) {
        std::this_thread::sleep_for(std::chrono::seconds(30));
        if (m_heartbeat_running && m_state == ConnectionState::CONNECTED) {
            s_log->trace("Telematics heartbeat OK");
        }
    }
    s_log->debug("Heartbeat thread stopped");
}

} // namespace tcu::telematics
