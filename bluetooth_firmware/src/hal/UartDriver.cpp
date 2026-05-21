/**
 * @file UartDriver.cpp
 * @brief Simulated UART driver using std::queue + mutex
 *
 * Simulates UART H4 transport for Bluetooth HCI.
 * Production replacement: STM32H7 USART DMA driver or
 * Infineon TC397 ASCLIN UART driver.
 */
#include "hal/UartDriver.hpp"
#include "common/Logger.hpp"
#include <algorithm>
#include <condition_variable>
#include <queue>

static constexpr const char *TAG = "UartDriver";

namespace bt::hal {

struct UartDriver::Impl {
    UartConfig  config{};
    bool        initialised{false};
    UartRxCb    rx_cb;
    // Simulated byte queues
    std::queue<uint8_t>  tx_queue;
    std::queue<uint8_t>  rx_queue;  // Injected by test/simulation
    std::mutex           mtx;
    std::condition_variable rx_cv;
};

UartDriver::UartDriver() : impl_(std::make_unique<Impl>()) {}
UartDriver::~UartDriver() { deinit(); }

bool UartDriver::init(const UartConfig &cfg) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->config      = cfg;
    impl_->initialised = true;
    BT_LOG_INFO(TAG, "UART init baud={} flow_ctrl={}", cfg.baud_rate, cfg.flow_control);
    return true;
}

void UartDriver::deinit() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->initialised = false;
    BT_LOG_DEBUG(TAG, "UART deinit");
}

int32_t UartDriver::send(const uint8_t *data, uint16_t len) {
    if (!impl_->initialised) { return -1; }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    for (uint16_t i = 0; i < len; ++i) {
        impl_->tx_queue.push(data[i]);
    }
    BT_LOG_DEBUG(TAG, "UART TX {} bytes", len);
    return static_cast<int32_t>(len);
}

int32_t UartDriver::receive(uint8_t *buf, uint16_t max_len, uint32_t timeout_ms) {
    using namespace std::chrono;
    const auto deadline = steady_clock::now() + milliseconds(timeout_ms);
    uint16_t received = 0;
    while (received < max_len) {
        std::unique_lock<std::mutex> lock(impl_->mtx);
        if (impl_->rx_queue.empty()) {
            if (!impl_->rx_cv.wait_until(lock, deadline,
                    [this] { return !impl_->rx_queue.empty(); })) {
                break;  // Timeout
            }
        }
        buf[received++] = impl_->rx_queue.front();
        impl_->rx_queue.pop();
    }
    return static_cast<int32_t>(received);
}

void UartDriver::set_rx_callback(UartRxCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->rx_cb = std::move(cb);
}

bool UartDriver::set_baud_rate(uint32_t baud) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->config.baud_rate = baud;
    BT_LOG_INFO(TAG, "Baud rate changed to {}", baud);
    return true;
}

void UartDriver::flush() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    while (!impl_->tx_queue.empty()) { impl_->tx_queue.pop(); }
}

// Test helper — inject bytes into the RX side
void UartDriver::inject_rx(const uint8_t *data, uint16_t len) {
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        for (uint16_t i = 0; i < len; ++i) {
            impl_->rx_queue.push(data[i]);
        }
    }
    impl_->rx_cv.notify_all();
    // If callback registered, invoke it
    if (impl_->rx_cb) {
        impl_->rx_cb(data, len);
    }
}

}  // namespace bt::hal
