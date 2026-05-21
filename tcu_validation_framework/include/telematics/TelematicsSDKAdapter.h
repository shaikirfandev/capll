/**
 * @file TelematicsSDKAdapter.h
 * @brief Telematics SDK Adapter — abstracts the OEM telematics SDK behind a clean interface.
 *
 * Provides:
 *   - SDK initialisation and teardown
 *   - Authenticated session management (mutual TLS / token-based)
 *   - Telemetry data upload
 *   - OTA command reception (via MQTT)
 *   - Network status monitoring
 *   - Simulated SDK mode for testing without real hardware
 */

#pragma once

#include <atomic>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace tcu::telematics {

// ============================================================
// Types
// ============================================================

enum class ConnectionState : uint8_t {
    DISCONNECTED = 0,
    CONNECTING,
    CONNECTED,
    AUTHENTICATED,
    ERROR,
};

inline const char* to_string(ConnectionState s) noexcept {
    switch (s) {
        case ConnectionState::DISCONNECTED:   return "DISCONNECTED";
        case ConnectionState::CONNECTING:     return "CONNECTING";
        case ConnectionState::CONNECTED:      return "CONNECTED";
        case ConnectionState::AUTHENTICATED:  return "AUTHENTICATED";
        case ConnectionState::ERROR:          return "ERROR";
        default:                              return "UNKNOWN";
    }
}

/**
 * @brief Telemetry data payload.
 */
struct TelemetryPayload {
    std::string                                  vehicle_id;
    int64_t                                      timestamp_ms{0};   ///< UTC ms
    std::unordered_map<std::string, double>      numeric_signals;   ///< key → value
    std::unordered_map<std::string, std::string> string_signals;    ///< key → value
    std::string                                  topic_override;    ///< Optional MQTT topic
};

/**
 * @brief OTA notification received from backend.
 */
struct OTANotification {
    std::string  campaign_id;
    std::string  package_id;
    std::string  package_url;
    std::string  package_version;
    uint32_t     package_size_bytes{0};
    std::string  package_hash_sha256;
    std::string  package_signature;
    std::string  target_ecu;
};

/**
 * @brief Network quality metrics.
 */
struct NetworkMetrics {
    int32_t  rsrp_dbm{-999};       ///< Reference Signal Received Power
    int32_t  rsrq_db{-999};        ///< Reference Signal Received Quality
    int32_t  sinr_db{-999};        ///< Signal-to-Interference-Noise Ratio
    uint32_t throughput_kbps{0};   ///< Estimated downlink throughput
    uint32_t latency_ms{0};        ///< Round-trip latency to backend
    uint8_t  signal_bars{0};       ///< 0–5 signal bar equivalent
    std::string plmn;              ///< Current PLMN (MCC+MNC)
    std::string rat;               ///< Radio access technology ("LTE", "5G-NSA")
};

/**
 * @brief SDK configuration.
 */
struct SDKConfig {
    std::string  server_url;                    ///< Backend URL (HTTPS/MQTT)
    uint16_t     server_port{8883};             ///< MQTT/HTTPS port
    std::string  client_cert_path;              ///< mTLS client certificate PEM
    std::string  client_key_path;               ///< mTLS client private key PEM
    std::string  ca_cert_path;                  ///< CA certificate PEM (pinning)
    std::string  vehicle_id;                    ///< VIN or unique vehicle identifier
    std::string  auth_token;                    ///< Bearer token (alternative to mTLS)
    uint32_t     keepalive_interval_s{60};      ///< MQTT keepalive interval
    uint32_t     reconnect_backoff_max_s{300};  ///< Max reconnect backoff
    bool         simulation_mode{false};        ///< Use simulated SDK (no real network)
    bool         verify_server_cert{true};      ///< Enforce TLS certificate validation
};

using ConnectionStateCallback = std::function<void(ConnectionState)>;
using OTANotificationCallback = std::function<void(const OTANotification&)>;
using TelemetryAckCallback    = std::function<void(bool success, const std::string& msg_id)>;

// ============================================================
// Adapter interface
// ============================================================

/**
 * @brief Telematics SDK Adapter.
 *
 * Wraps the vendor SDK behind a stable interface for unit testing and portability.
 */
class TelematicsSDKAdapter {
public:
    explicit TelematicsSDKAdapter(const SDKConfig& cfg);
    ~TelematicsSDKAdapter();

    TelematicsSDKAdapter(const TelematicsSDKAdapter&)            = delete;
    TelematicsSDKAdapter& operator=(const TelematicsSDKAdapter&) = delete;

    // --------------------------------------------------------
    // Lifecycle
    // --------------------------------------------------------

    /** @brief Initialise the SDK (load config, prepare TLS context). */
    bool initialize();

    /** @brief Connect to the backend. Non-blocking; state updates via callback. */
    bool connect();

    /** @brief Disconnect gracefully. */
    void disconnect();

    /** @brief Get current connection state. */
    ConnectionState connection_state() const noexcept;

    // --------------------------------------------------------
    // Telemetry
    // --------------------------------------------------------

    /**
     * @brief Upload a telemetry payload.
     * @param payload  Data to upload
     * @param async    If true, enqueue and return immediately
     * @return Message ID (empty on failure)
     */
    std::string upload_telemetry(const TelemetryPayload& payload, bool async = true);

    /**
     * @brief Flush the telemetry queue (blocks until empty or timeout).
     */
    bool flush_telemetry(uint32_t timeout_ms = 10000);

    // --------------------------------------------------------
    // OTA
    // --------------------------------------------------------

    /** @brief Register callback for incoming OTA notifications. */
    void set_ota_callback(OTANotificationCallback cb);

    /** @brief Publish OTA result to backend. */
    bool report_ota_result(const std::string& campaign_id,
                           bool success, const std::string& details);

    // --------------------------------------------------------
    // Network monitoring
    // --------------------------------------------------------

    /** @brief Get latest network quality metrics. */
    NetworkMetrics network_metrics() const;

    /** @brief Register callback for connection state changes. */
    void set_connection_state_callback(ConnectionStateCallback cb);

    // --------------------------------------------------------
    // Simulation helpers (simulation_mode = true)
    // --------------------------------------------------------

    /** @brief Inject a simulated OTA notification (test use only). */
    void sim_inject_ota(const OTANotification& notification);

    /** @brief Simulate a connection drop (test use only). */
    void sim_drop_connection();

    /** @brief Simulate network metrics (test use only). */
    void sim_set_network_metrics(const NetworkMetrics& m);

private:
    void reconnect_thread_fn();
    void set_state(ConnectionState new_state);

    SDKConfig                      m_cfg;
    std::atomic<ConnectionState>   m_state{ConnectionState::DISCONNECTED};
    ConnectionStateCallback        m_state_cb;
    OTANotificationCallback        m_ota_cb;
    mutable std::mutex             m_metrics_mutex;
    NetworkMetrics                 m_metrics;
    std::atomic<bool>              m_stop_reconnect{false};
    std::thread                    m_reconnect_thread;
};

} // namespace tcu::telematics
