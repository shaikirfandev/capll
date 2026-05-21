/**
 * @file RfcommSimulator.cpp
 * @brief RFCOMM frame simulation for SPP (Serial Port Profile)
 *
 * Simulates RFCOMM multiplexer over L2CAP PSM 0x0003.
 * Used in Classic Bluetooth SPP for legacy OBD-II diagnostic tools
 * and automotive key fob pairing.
 */
#include "bt/RfcommSimulator.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <queue>

static constexpr const char *TAG   = "RFCOMM";
static constexpr uint16_t RFCOMM_PSM = 0x0003U;

namespace bt {

struct RfcommSimulator::Impl {
    std::queue<std::vector<uint8_t>> rx_queue;
    mutable std::mutex mtx;
    bool mux_open{false};
};

RfcommSimulator::RfcommSimulator() : impl_(std::make_unique<Impl>()) {}
RfcommSimulator::~RfcommSimulator() = default;

BtError RfcommSimulator::open_mux(ConnHandle conn) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->mux_open) { return BtError::ERR_ALREADY_CONNECTED; }
    impl_->mux_open = true;
    BT_LOG_INFO(TAG, "RFCOMM MUX opened conn=0x{:04X}", conn);
    return BtError::OK;
}

BtError RfcommSimulator::open_dlci(uint8_t dlci) {
    BT_LOG_INFO(TAG, "RFCOMM DLCI={} opened", dlci);
    return BtError::OK;
}

BtError RfcommSimulator::send(uint8_t dlci, const uint8_t *data, uint16_t len) {
    (void)dlci;
    BT_LOG_DEBUG(TAG, "RFCOMM TX dlci={} len={}", dlci, len);
    (void)data;
    return BtError::OK;
}

void RfcommSimulator::inject_rx(const uint8_t *data, uint16_t len) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->rx_queue.emplace(data, data + len);
}

std::optional<std::vector<uint8_t>> RfcommSimulator::receive() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->rx_queue.empty()) { return std::nullopt; }
    auto v = impl_->rx_queue.front();
    impl_->rx_queue.pop();
    return v;
}

}  // namespace bt
