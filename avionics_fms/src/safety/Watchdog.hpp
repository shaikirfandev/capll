/**
 * @file Watchdog.hpp / Watchdog.cpp — DAL-A watchdog
 * @req SRS-SAFE-003
 */
#pragma once
#include "safety/IWatchdog.hpp"
#include <chrono>
#include <atomic>

namespace fms::safety {

class Watchdog : public IWatchdog {
public:
    FmsError init(uint32_t timeout_ms) noexcept override;
    void     shutdown() noexcept override {}
    void     kick() noexcept override;
    [[nodiscard]] bool         is_expired()  const noexcept override;
    [[nodiscard]] uint32_t     timeout_ms()  const noexcept override { return timeout_ms_; }
    [[nodiscard]] SystemStatus get_status()  const noexcept override;

private:
    uint32_t timeout_ms_{500};
    std::chrono::steady_clock::time_point last_kick_;
};

}  // namespace fms::safety
