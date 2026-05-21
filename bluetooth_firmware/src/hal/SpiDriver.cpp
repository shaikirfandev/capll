/**
 * @file SpiDriver.cpp  GpioDriver.cpp  PowerManager.cpp
 * @brief Simulated HAL drivers
 */

// ── SpiDriver ─────────────────────────────────────────────────────────────────
#include "hal/SpiDriver.hpp"
#include "common/Logger.hpp"
#include <cstring>
#include <mutex>

static constexpr const char *SPI_TAG = "SpiDriver";

namespace bt::hal {

struct SpiDriver::Impl {
    SpiConfig config{};
    bool      initialised{false};
    mutable std::mutex mtx;
};

SpiDriver::SpiDriver()  : impl_(std::make_unique<Impl>()) {}
SpiDriver::~SpiDriver() { deinit(); }

bool SpiDriver::init(const SpiConfig &cfg) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->config      = cfg;
    impl_->initialised = true;
    BT_LOG_INFO(SPI_TAG, "SPI init freq={}Hz mode={}", cfg.freq_hz, static_cast<int>(cfg.mode));
    return true;
}

void SpiDriver::deinit() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->initialised = false;
}

int32_t SpiDriver::transfer(const uint8_t *tx, uint8_t *rx, uint16_t len) {
    if (!impl_->initialised) { return -1; }
    // Simulation: echo TX to RX (loopback)
    if (rx && tx) { std::memcpy(rx, tx, len); }
    return static_cast<int32_t>(len);
}

int32_t SpiDriver::write(const uint8_t *data, uint16_t len) {
    return transfer(data, nullptr, len);
}

int32_t SpiDriver::read(uint8_t *buf, uint16_t len) {
    if (!buf) { return -1; }
    std::memset(buf, 0xFFU, len);  // Bus idle = high
    return static_cast<int32_t>(len);
}

bool SpiDriver::set_freq(uint32_t hz) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->config.freq_hz = hz;
    return true;
}

}  // namespace bt::hal
