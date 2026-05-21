/**
 * @file CANManager.h
 * @brief SocketCAN-based CAN Manager — thread-safe Tx/Rx with filtering & DBC support.
 *
 * Architecture:
 *   - A dedicated Rx thread runs continuously, pushing received frames to
 *     registered callbacks.
 *   - Tx is protected by a mutex (thread-safe from any calling thread).
 *   - Filters are applied at the kernel level (setsockopt SO_CAN_FILTER) for
 *     maximum efficiency.
 *
 * Supports: CAN 2.0A (11-bit), CAN 2.0B (29-bit), CAN-FD.
 */

#pragma once

#include <atomic>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include <linux/can.h>
#include <linux/can/raw.h>

namespace tcu::can {

/** @brief Maximum CAN FD payload size */
static constexpr size_t CAN_FD_MAX_DLEN = 64U;

/**
 * @brief Unified CAN frame (supports classic CAN and CAN-FD).
 */
struct CANFrame {
    uint32_t id{0};           ///< CAN ID (masked; bit 31 = extended frame flag)
    uint8_t  dlc{0};          ///< Data length code (0–8 for classic, 0–64 for FD)
    uint8_t  data[CAN_FD_MAX_DLEN]{};
    bool     is_extended{false}; ///< 29-bit extended frame
    bool     is_fd{false};       ///< CAN-FD frame
    bool     is_remote{false};   ///< Remote Transmission Request
    int64_t  timestamp_us{0};    ///< µs since epoch (filled on Rx)
};

/**
 * @brief CAN hardware / vcan interface statistics.
 */
struct CANStats {
    uint64_t tx_frames{0};
    uint64_t rx_frames{0};
    uint64_t tx_errors{0};
    uint64_t rx_errors{0};
    uint64_t rx_overflows{0};
    uint64_t bus_off_events{0};
};

/**
 * @brief CAN bus error event.
 */
struct CANError {
    uint32_t error_class{0};   ///< CAN_ERR_* flags from linux/can/error.h
    std::string description;
    int64_t  timestamp_us{0};
};

using RxCallback    = std::function<void(const CANFrame&)>;
using ErrorCallback = std::function<void(const CANError&)>;
using CallbackHandle = uint32_t;

/**
 * @brief CAN interface configuration.
 */
struct CANConfig {
    std::string interface{"vcan0"};   ///< SocketCAN interface name
    bool        enable_fd{false};     ///< Enable CAN-FD
    bool        loopback{false};      ///< Enable loopback (testing)
    uint32_t    rx_timeout_ms{1000};  ///< Rx select() timeout
    size_t      rx_queue_depth{1024}; ///< Internal Rx queue depth
};

/**
 * @brief Thread-safe CAN Manager using SocketCAN.
 *
 * Lifecycle:
 *   open() → register_rx_callback() → start() → [Tx/Rx] → stop() → close()
 */
class CANManager {
public:
    explicit CANManager(const CANConfig& cfg);
    ~CANManager();

    CANManager(const CANManager&)            = delete;
    CANManager& operator=(const CANManager&) = delete;

    /**
     * @brief Open the CAN socket and bind to the configured interface.
     * @return true on success
     */
    bool open();

    /**
     * @brief Close the socket and release resources.
     */
    void close();

    /**
     * @brief Start the Rx listener thread.
     */
    bool start();

    /**
     * @brief Stop the Rx listener thread gracefully.
     */
    void stop();

    /**
     * @brief Transmit a CAN frame (thread-safe).
     * @param frame  Frame to transmit
     * @return true on success
     */
    bool transmit(const CANFrame& frame);

    /**
     * @brief Transmit raw bytes as a CAN frame (helper).
     */
    bool transmit(uint32_t id, const uint8_t* data, uint8_t dlc, bool extended = false);

    /**
     * @brief Apply kernel-level CAN ID filters.
     * Replaces any previously set filters.
     * @param id_mask_pairs  Vector of {can_id, can_mask} pairs
     */
    bool set_filters(const std::vector<std::pair<uint32_t, uint32_t>>& id_mask_pairs);

    /**
     * @brief Register a callback invoked for every received frame.
     * @return Handle used to unregister the callback
     */
    CallbackHandle register_rx_callback(RxCallback cb);

    /**
     * @brief Register a callback invoked on CAN bus errors.
     */
    CallbackHandle register_error_callback(ErrorCallback cb);

    /**
     * @brief Unregister a previously registered callback.
     */
    void unregister_callback(CallbackHandle handle);

    /**
     * @brief Retrieve current interface statistics.
     */
    CANStats statistics() const;

    /**
     * @brief Reset statistics counters.
     */
    void reset_statistics();

    /**
     * @brief Returns true if the socket is open and the Rx thread is running.
     */
    bool is_running() const noexcept;

    /**
     * @brief Get configured interface name.
     */
    const std::string& interface_name() const noexcept;

private:
    void rx_thread_fn();
    void dispatch_frame(const CANFrame& frame);
    void dispatch_error(const CANError& error);
    CANFrame build_frame(const struct can_frame& raw) const;
    CANFrame build_fd_frame(const struct canfd_frame& raw) const;

    CANConfig                                   m_cfg;
    int                                         m_socket_fd{-1};
    std::atomic<bool>                           m_running{false};
    std::thread                                 m_rx_thread;
    mutable std::mutex                          m_tx_mutex;
    mutable std::mutex                          m_cb_mutex;
    std::unordered_map<CallbackHandle, RxCallback>    m_rx_callbacks;
    std::unordered_map<CallbackHandle, ErrorCallback> m_err_callbacks;
    std::atomic<CallbackHandle>                 m_next_handle{1};
    mutable std::mutex                          m_stats_mutex;
    CANStats                                    m_stats{};
};

} // namespace tcu::can
