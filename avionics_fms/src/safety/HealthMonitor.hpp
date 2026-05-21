/**
 * @file HealthMonitor.hpp
 */
#pragma once
#include "safety/IHealthMonitor.hpp"
#include <chrono>

namespace fms::safety {

class HealthMonitor : public IHealthMonitor {
public:
    FmsError init() noexcept override;
    void     shutdown() noexcept override {}
    void     run_bite() noexcept override;
    void     update() noexcept override;
    [[nodiscard]] HealthReport get_health()      const noexcept override;
    [[nodiscard]] float        get_cpu_load_pct()const noexcept override { return cpu_load_; }
    [[nodiscard]] float        get_ram_usage_pct()const noexcept override { return ram_usage_; }
    [[nodiscard]] uint64_t     get_uptime_ms()   const noexcept override;
    [[nodiscard]] SystemStatus get_status()      const noexcept override { return status_; }

private:
    SystemStatus status_{SystemStatus::NORMAL};
    float cpu_load_{0.0f};
    float ram_usage_{0.0f};
    bool  bite_passed_{false};
    std::chrono::steady_clock::time_point start_time_;
};

}  // namespace fms::safety
