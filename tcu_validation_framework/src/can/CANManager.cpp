/**
 * @file CANManager.cpp
 * @brief SocketCAN-based CAN Manager implementation.
 *
 * Uses Linux SocketCAN API:
 *   - socket(PF_CAN, SOCK_RAW, CAN_RAW) for classic CAN
 *   - socket(PF_CAN, SOCK_RAW, CAN_RAW) + setsockopt CAN_RAW_FD_FRAMES for CAN-FD
 *   - Rx loop uses select() for timeout + graceful thread stop
 */

#include "can/CANManager.h"
#include "logging/Logger.h"

#include <algorithm>
#include <cerrno>
#include <cstring>
#include <stdexcept>
#include <chrono>

// Linux SocketCAN headers
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/select.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <linux/can/error.h>

namespace tcu::can {

static auto s_log = tcu::logging::Logger::get("can");

// ============================================================
// Construction / Destruction
// ============================================================

CANManager::CANManager(const CANConfig& cfg)
    : m_cfg(cfg)
{}

CANManager::~CANManager() {
    if (m_running) { stop(); }
    if (m_socket_fd >= 0) { close(); }
}

// ============================================================
// Open / Close
// ============================================================

bool CANManager::open() {
    if (m_socket_fd >= 0) {
        s_log->warn("Socket already open on {}", m_cfg.interface);
        return true;
    }

    // Create CAN raw socket
    m_socket_fd = ::socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (m_socket_fd < 0) {
        s_log->error("socket() failed: {}", strerror(errno));
        return false;
    }

    // Enable CAN-FD if requested
    if (m_cfg.enable_fd) {
        int enable = 1;
        if (::setsockopt(m_socket_fd, SOL_CAN_RAW, CAN_RAW_FD_FRAMES,
                         &enable, sizeof(enable)) < 0) {
            s_log->warn("CAN-FD not supported on {}: {}", m_cfg.interface, strerror(errno));
        }
    }

    // Enable loopback if requested
    int loopback = m_cfg.loopback ? 1 : 0;
    ::setsockopt(m_socket_fd, SOL_CAN_RAW, CAN_RAW_LOOPBACK,
                 &loopback, sizeof(loopback));

    // Enable error frames
    can_err_mask_t err_mask = CAN_ERR_MASK;
    ::setsockopt(m_socket_fd, SOL_CAN_RAW, CAN_RAW_ERR_FILTER,
                 &err_mask, sizeof(err_mask));

    // Bind to interface
    struct ifreq ifr{};
    ::strncpy(ifr.ifr_name, m_cfg.interface.c_str(), IFNAMSIZ - 1);
    if (::ioctl(m_socket_fd, SIOCGIFINDEX, &ifr) < 0) {
        s_log->error("Interface '{}' not found: {}", m_cfg.interface, strerror(errno));
        ::close(m_socket_fd);
        m_socket_fd = -1;
        return false;
    }

    struct sockaddr_can addr{};
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (::bind(m_socket_fd,
               reinterpret_cast<struct sockaddr*>(&addr),
               sizeof(addr)) < 0) {
        s_log->error("bind() failed on {}: {}", m_cfg.interface, strerror(errno));
        ::close(m_socket_fd);
        m_socket_fd = -1;
        return false;
    }

    s_log->info("CAN socket opened: {} (fd={}, FD={})",
                m_cfg.interface, m_socket_fd, m_cfg.enable_fd ? "yes" : "no");
    return true;
}

void CANManager::close() {
    if (m_socket_fd >= 0) {
        ::close(m_socket_fd);
        m_socket_fd = -1;
        s_log->info("CAN socket closed: {}", m_cfg.interface);
    }
}

// ============================================================
// Start / Stop Rx Thread
// ============================================================

bool CANManager::start() {
    if (m_socket_fd < 0) {
        s_log->error("start() called before open()");
        return false;
    }
    if (m_running.exchange(true)) {
        s_log->warn("Rx thread already running");
        return true;
    }
    m_rx_thread = std::thread(&CANManager::rx_thread_fn, this);
    s_log->info("CAN Rx thread started on {}", m_cfg.interface);
    return true;
}

void CANManager::stop() {
    if (!m_running.exchange(false)) { return; }
    if (m_rx_thread.joinable()) {
        m_rx_thread.join();
    }
    s_log->info("CAN Rx thread stopped: {}", m_cfg.interface);
}

// ============================================================
// Transmit
// ============================================================

bool CANManager::transmit(const CANFrame& frame) {
    std::lock_guard<std::mutex> lock(m_tx_mutex);

    if (m_socket_fd < 0) {
        s_log->error("transmit() on closed socket");
        return false;
    }

    ssize_t nbytes = 0;

    if (frame.is_fd) {
        struct canfd_frame fd_frame{};
        fd_frame.can_id = frame.id | (frame.is_extended ? CAN_EFF_FLAG : 0U);
        fd_frame.len    = std::min(static_cast<uint8_t>(CAN_FD_MAX_DLEN), frame.dlc);
        ::memcpy(fd_frame.data, frame.data, fd_frame.len);
        nbytes = ::write(m_socket_fd, &fd_frame, sizeof(fd_frame));
    } else {
        struct can_frame raw{};
        raw.can_id  = frame.id | (frame.is_extended ? CAN_EFF_FLAG : 0U);
        raw.can_id |= frame.is_remote ? CAN_RTR_FLAG : 0U;
        raw.can_dlc = std::min(static_cast<uint8_t>(8U), frame.dlc);
        ::memcpy(raw.data, frame.data, raw.can_dlc);
        nbytes = ::write(m_socket_fd, &raw, sizeof(raw));
    }

    if (nbytes < 0) {
        s_log->error("CAN Tx error on {}: {}", m_cfg.interface, strerror(errno));
        std::lock_guard<std::mutex> sl(m_stats_mutex);
        ++m_stats.tx_errors;
        return false;
    }

    std::lock_guard<std::mutex> sl(m_stats_mutex);
    ++m_stats.tx_frames;
    return true;
}

bool CANManager::transmit(uint32_t id, const uint8_t* data, uint8_t dlc, bool extended) {
    CANFrame f;
    f.id          = id;
    f.dlc         = dlc;
    f.is_extended = extended;
    if (data && dlc > 0) {
        ::memcpy(f.data, data, std::min(static_cast<size_t>(dlc), sizeof(f.data)));
    }
    return transmit(f);
}

// ============================================================
// Filters
// ============================================================

bool CANManager::set_filters(const std::vector<std::pair<uint32_t, uint32_t>>& id_mask_pairs) {
    std::vector<struct can_filter> filters;
    filters.reserve(id_mask_pairs.size());
    for (const auto& [id, mask] : id_mask_pairs) {
        filters.push_back({id, mask});
    }
    int rc = ::setsockopt(m_socket_fd, SOL_CAN_RAW, CAN_RAW_FILTER,
                          filters.data(),
                          static_cast<socklen_t>(sizeof(struct can_filter) * filters.size()));
    if (rc < 0) {
        s_log->error("set_filters() failed: {}", strerror(errno));
        return false;
    }
    s_log->debug("Applied {} CAN filters", filters.size());
    return true;
}

// ============================================================
// Callback management
// ============================================================

CallbackHandle CANManager::register_rx_callback(RxCallback cb) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    auto handle = m_next_handle.fetch_add(1);
    m_rx_callbacks[handle] = std::move(cb);
    return handle;
}

CallbackHandle CANManager::register_error_callback(ErrorCallback cb) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    auto handle = m_next_handle.fetch_add(1);
    m_err_callbacks[handle] = std::move(cb);
    return handle;
}

void CANManager::unregister_callback(CallbackHandle handle) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    m_rx_callbacks.erase(handle);
    m_err_callbacks.erase(handle);
}

// ============================================================
// Statistics
// ============================================================

CANStats CANManager::statistics() const {
    std::lock_guard<std::mutex> lock(m_stats_mutex);
    return m_stats;
}

void CANManager::reset_statistics() {
    std::lock_guard<std::mutex> lock(m_stats_mutex);
    m_stats = {};
}

bool CANManager::is_running() const noexcept {
    return m_running.load();
}

const std::string& CANManager::interface_name() const noexcept {
    return m_cfg.interface;
}

// ============================================================
// Rx Thread
// ============================================================

void CANManager::rx_thread_fn() {
    s_log->debug("Rx thread running (fd={})", m_socket_fd);

    while (m_running.load()) {
        fd_set rdfs;
        FD_ZERO(&rdfs);
        FD_SET(m_socket_fd, &rdfs);

        struct timeval tv{};
        tv.tv_sec  = m_cfg.rx_timeout_ms / 1000;
        tv.tv_usec = (m_cfg.rx_timeout_ms % 1000) * 1000;

        int ret = ::select(m_socket_fd + 1, &rdfs, nullptr, nullptr, &tv);
        if (ret < 0) {
            if (errno == EINTR) { continue; }
            s_log->error("select() error: {}", strerror(errno));
            break;
        }
        if (ret == 0) { continue; }  // timeout — check m_running

        if (!FD_ISSET(m_socket_fd, &rdfs)) { continue; }

        if (m_cfg.enable_fd) {
            struct canfd_frame fd_frame{};
            ssize_t nbytes = ::read(m_socket_fd, &fd_frame, sizeof(fd_frame));
            if (nbytes > 0) {
                auto frame = build_fd_frame(fd_frame);
                // Get µs timestamp from kernel
                frame.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
                dispatch_frame(frame);
                std::lock_guard<std::mutex> sl(m_stats_mutex);
                ++m_stats.rx_frames;
            }
        } else {
            struct can_frame raw{};
            ssize_t nbytes = ::read(m_socket_fd, &raw, sizeof(raw));
            if (nbytes > 0) {
                if (raw.can_id & CAN_ERR_FLAG) {
                    // Error frame
                    CANError err;
                    err.error_class  = raw.can_id & CAN_ERR_MASK;
                    err.description  = "CAN error frame received";
                    err.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
                        std::chrono::system_clock::now().time_since_epoch()).count();
                    dispatch_error(err);
                    std::lock_guard<std::mutex> sl(m_stats_mutex);
                    ++m_stats.rx_errors;
                    if (raw.can_id & CAN_ERR_BUSOFF) { ++m_stats.bus_off_events; }
                } else {
                    auto frame = build_frame(raw);
                    frame.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
                        std::chrono::system_clock::now().time_since_epoch()).count();
                    dispatch_frame(frame);
                    std::lock_guard<std::mutex> sl(m_stats_mutex);
                    ++m_stats.rx_frames;
                }
            }
        }
    }

    s_log->debug("Rx thread exited");
}

void CANManager::dispatch_frame(const CANFrame& frame) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    for (auto& [handle, cb] : m_rx_callbacks) {
        if (cb) { cb(frame); }
    }
}

void CANManager::dispatch_error(const CANError& error) {
    std::lock_guard<std::mutex> lock(m_cb_mutex);
    for (auto& [handle, cb] : m_err_callbacks) {
        if (cb) { cb(error); }
    }
}

CANFrame CANManager::build_frame(const struct can_frame& raw) const {
    CANFrame f;
    f.is_extended = (raw.can_id & CAN_EFF_FLAG) != 0;
    f.is_remote   = (raw.can_id & CAN_RTR_FLAG) != 0;
    f.id          = raw.can_id & (f.is_extended ? CAN_EFF_MASK : CAN_SFF_MASK);
    f.dlc         = raw.can_dlc;
    f.is_fd       = false;
    ::memcpy(f.data, raw.data, std::min(static_cast<int>(raw.can_dlc), 8));
    return f;
}

CANFrame CANManager::build_fd_frame(const struct canfd_frame& raw) const {
    CANFrame f;
    f.is_extended = (raw.can_id & CAN_EFF_FLAG) != 0;
    f.id          = raw.can_id & (f.is_extended ? CAN_EFF_MASK : CAN_SFF_MASK);
    f.dlc         = raw.len;
    f.is_fd       = true;
    ::memcpy(f.data, raw.data, std::min(static_cast<int>(raw.len), 64));
    return f;
}

} // namespace tcu::can
