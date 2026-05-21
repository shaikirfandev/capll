/**
 * @file PowerManager.cpp
 * @brief Power state machine for BT radio power management
 *
 * Manages transitions: ACTIVE → LOW_POWER → SNIFF → BLE_CONN_LP → SLEEP → OFF
 * Production: maps to vendor-specific HCI VS commands for Qualcomm/TI chips.
 */
#include "hal/PowerManager.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <chrono>

static constexpr const char *TAG = "PowerManager";

namespace bt::hal {

struct PowerManager::Impl {
    bt::PowerState state{bt::PowerState::ACTIVE};
    float          voltages[4]{3.3F, 1.8F, 3.3F, 4.1F};  // VCC_MAIN/RF/IO/VBAT
    bool           charging{false};
    uint8_t        battery_pct{80U};
    mutable std::mutex mtx;
};

PowerManager::PowerManager()  : impl_(std::make_unique<Impl>()) {}
PowerManager::~PowerManager() = default;

void PowerManager::enter_sleep() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_INFO(TAG, "Entering sleep mode");
    impl_->state = bt::PowerState::SLEEP;
}

void PowerManager::wake_up() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_INFO(TAG, "Wake up from sleep");
    impl_->state = bt::PowerState::ACTIVE;
}

float PowerManager::get_voltage(SysVoltageRail rail) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->voltages[static_cast<uint8_t>(rail) % 4U];
}

bool PowerManager::is_charging() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->charging;
}

uint8_t PowerManager::battery_percent() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->battery_pct;
}

void PowerManager::power_down_radio() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_INFO(TAG, "Radio powered DOWN");
    impl_->state = bt::PowerState::OFF;
}

void PowerManager::power_up_radio() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_INFO(TAG, "Radio powered UP");
    impl_->state = bt::PowerState::ACTIVE;
}

}  // namespace bt::hal
