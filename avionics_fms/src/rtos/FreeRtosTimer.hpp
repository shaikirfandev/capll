/**
 * @file FreeRtosTimer.hpp
 */
#pragma once
#include "rtos/IRtosInterfaces.hpp"
#include <thread>
#include <atomic>

namespace fms::rtos {

class FreeRtosTimer : public IRtosTimer {
public:
    ~FreeRtosTimer() override { stop(); }

    FmsError create(const char*, uint32_t period_ms, bool periodic, TimerCb cb) noexcept override {
        period_ms_ = period_ms; periodic_ = periodic; cb_ = cb;
        return FmsError::OK;
    }

    bool start() noexcept override {
        if (active_.load()) return false;
        active_.store(true);
        thread_ = std::thread([this] {
            do {
                std::this_thread::sleep_for(std::chrono::milliseconds(period_ms_));
                if (active_.load() && cb_) cb_();
            } while (active_.load() && periodic_);
            active_.store(false);
        });
        return true;
    }

    bool stop() noexcept override {
        active_.store(false);
        if (thread_.joinable()) thread_.join();
        return true;
    }

    bool reset() noexcept override { stop(); return start(); }
    bool is_active() const noexcept override { return active_.load(); }

private:
    uint32_t period_ms_{0};
    bool periodic_{false};
    TimerCb cb_;
    std::atomic<bool> active_{false};
    std::thread thread_;
};

}  // namespace fms::rtos
