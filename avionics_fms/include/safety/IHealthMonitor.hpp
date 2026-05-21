/**
 * @file IHealthMonitor.hpp
 * @brief Built-In Test Equipment (BITE) and health monitoring interface
 * @req SRS-SAFE-004
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include <cstdint>

namespace fms::safety {

struct HealthReport {
    float    cpu_load_pct;
    float    ram_usage_pct;
    uint64_t uptime_ms;
    bool     bite_passed;
};

class IHealthMonitor {
public:
    virtual ~IHealthMonitor() = default;
    virtual FmsError init() noexcept = 0;
    virtual void     shutdown() noexcept = 0;
    virtual void     run_bite() noexcept = 0;
    virtual void     update() noexcept = 0;
    [[nodiscard]] virtual HealthReport get_health() const noexcept = 0;
    [[nodiscard]] virtual float        get_cpu_load_pct() const noexcept = 0;
    [[nodiscard]] virtual float        get_ram_usage_pct() const noexcept = 0;
    [[nodiscard]] virtual uint64_t     get_uptime_ms() const noexcept = 0;
    [[nodiscard]] virtual SystemStatus get_status() const noexcept = 0;
};

}  // namespace fms::safety
