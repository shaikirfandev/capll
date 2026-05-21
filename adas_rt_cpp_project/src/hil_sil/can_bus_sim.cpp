/**
 * @file can_bus_sim.cpp
 * @brief SimHal and signal encoding/decoding implementation.
 */

#include "can_bus_sim.hpp"

#include <cassert>
#include <cstring>
#include <stdexcept>

#ifdef ADAS_USE_SOCKETCAN
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace adas {
namespace hil {

// ─── Signal encode/decode ─────────────────────────────────────────────────────

void encodeSignal(CanFrame& frame, const CanSignal& sig, float physical_value) {
    const float raw_f   = (physical_value - sig.offset) / sig.scale;
    const uint64_t mask = (1ULL << sig.length) - 1ULL;

    uint64_t raw;
    if (sig.is_signed) {
        const int64_t raw_signed = static_cast<int64_t>(raw_f);
        raw = static_cast<uint64_t>(raw_signed) & mask;
    } else {
        raw = static_cast<uint64_t>(raw_f) & mask;
    }

    // Pack into frame.data (little-endian byte order)
    uint64_t data64;
    std::memcpy(&data64, frame.data, 8);

    // Clear the bits at start_bit..start_bit+length-1, then set
    const uint64_t shifted_mask = mask << sig.start_bit;
    data64 = (data64 & ~shifted_mask) | ((raw << sig.start_bit) & shifted_mask);

    std::memcpy(frame.data, &data64, 8);
    frame.dlc = std::max(frame.dlc, static_cast<uint8_t>((sig.start_bit + sig.length + 7) / 8));
}

float decodeSignal(const CanFrame& frame, const CanSignal& sig) {
    uint64_t data64;
    std::memcpy(&data64, frame.data, 8);

    const uint64_t mask = (1ULL << sig.length) - 1ULL;
    const uint64_t raw  = (data64 >> sig.start_bit) & mask;

    float physical;
    if (sig.is_signed) {
        // Sign-extend
        const bool negative = (raw >> (sig.length - 1)) & 1;
        const int64_t signed_raw = negative
            ? static_cast<int64_t>(raw | (~mask))
            : static_cast<int64_t>(raw);
        physical = static_cast<float>(signed_raw) * sig.scale + sig.offset;
    } else {
        physical = static_cast<float>(raw) * sig.scale + sig.offset;
    }
    return physical;
}

// ─── SimHal ───────────────────────────────────────────────────────────────────

SimHal::SimHal() = default;

SimHal::~SimHal() { close(); }

bool SimHal::open() {
    std::lock_guard<std::mutex> lock(mutex_);
    open_ = true;
    return true;
}

void SimHal::close() {
    std::lock_guard<std::mutex> lock(mutex_);
    open_ = false;
}

bool SimHal::txCan(const CanFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!open_) return false;

    // Log the transmitted frame (for test assertion)
    tx_log_.push_back(frame);

    // Echo to all RX callbacks (simulates loopback on shared bus)
    for (const auto& cb : rx_callbacks_) {
        cb(frame);
    }
    return true;
}

void SimHal::registerCanRxCallback(CanRxCallback cb) {
    std::lock_guard<std::mutex> lock(mutex_);
    rx_callbacks_.push_back(std::move(cb));
}

void SimHal::registerGpsCallback(GpsCallback cb) {
    std::lock_guard<std::mutex> lock(mutex_);
    gps_callback_ = std::move(cb);
}

void SimHal::registerImuCallback(ImuCallback cb) {
    std::lock_guard<std::mutex> lock(mutex_);
    imu_callback_ = std::move(cb);
}

void SimHal::injectFrame(const CanFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& cb : rx_callbacks_) {
        cb(frame);
    }
}

void SimHal::injectGps(const GpsPosition& gps) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (gps_callback_) gps_callback_(gps);
}

void SimHal::injectImu(const ImuData& imu) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (imu_callback_) imu_callback_(imu);
}

std::vector<CanFrame> SimHal::drainTxLog() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<CanFrame> out = std::move(tx_log_);
    tx_log_.clear();
    return out;
}

// ─── SocketCanHal ─────────────────────────────────────────────────────────────

#ifdef ADAS_USE_SOCKETCAN

SocketCanHal::SocketCanHal(const char* interface_name)
    : iface_name_(interface_name) {}

SocketCanHal::~SocketCanHal() { close(); }

bool SocketCanHal::open() {
    sock_fd_ = ::socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock_fd_ < 0) return false;

    struct ifreq ifr{};
    std::strncpy(ifr.ifr_name, iface_name_, IFNAMSIZ - 1);
    if (::ioctl(sock_fd_, SIOCGIFINDEX, &ifr) < 0) {
        ::close(sock_fd_);
        sock_fd_ = -1;
        return false;
    }

    struct sockaddr_can addr{};
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (::bind(sock_fd_, reinterpret_cast<struct sockaddr*>(&addr), sizeof(addr)) < 0) {
        ::close(sock_fd_);
        sock_fd_ = -1;
        return false;
    }

    rx_stop_.store(false);
    rx_thread_ = std::thread([this] { rxThreadLoop(); });
    return true;
}

void SocketCanHal::close() {
    rx_stop_.store(true);
    if (sock_fd_ >= 0) {
        ::close(sock_fd_);
        sock_fd_ = -1;
    }
    if (rx_thread_.joinable()) rx_thread_.join();
}

bool SocketCanHal::txCan(const CanFrame& frame) {
    struct can_frame cf{};
    cf.can_id  = frame.is_extended ? (frame.id | CAN_EFF_FLAG) : frame.id;
    cf.can_dlc = frame.dlc;
    std::memcpy(cf.data, frame.data, frame.dlc);
    return ::write(sock_fd_, &cf, sizeof(cf)) == sizeof(cf);
}

void SocketCanHal::registerCanRxCallback(CanRxCallback cb) {
    std::lock_guard<std::mutex> lock(cb_mutex_);
    rx_callbacks_.push_back(std::move(cb));
}

void SocketCanHal::registerGpsCallback(GpsCallback cb)  { gps_cb_ = std::move(cb); }
void SocketCanHal::registerImuCallback(ImuCallback cb)   { imu_cb_ = std::move(cb); }

void SocketCanHal::rxThreadLoop() {
    while (!rx_stop_.load()) {
        struct can_frame cf{};
        const ssize_t n = ::read(sock_fd_, &cf, sizeof(cf));
        if (n < 0) break;

        CanFrame frame{};
        frame.id          = cf.can_id & CAN_EFF_MASK;
        frame.is_extended = (cf.can_id & CAN_EFF_FLAG) != 0;
        frame.dlc         = cf.can_dlc;
        std::memcpy(frame.data, cf.data, cf.can_dlc);
        frame.timestamp_us = 0;  // could use SO_TIMESTAMP

        std::lock_guard<std::mutex> lock(cb_mutex_);
        for (const auto& cb : rx_callbacks_) {
            cb(frame);
        }
    }
}

#endif  // ADAS_USE_SOCKETCAN

}  // namespace hil
}  // namespace adas
