/**
 * @file FuelManagement.hpp
 */
#pragma once
#include "fms/IFuelManagement.hpp"
#include "fms/FmsTypes.hpp"

namespace fms {

class FuelManagement : public IFuelManagement {
public:
    FmsError init() noexcept override;
    void     shutdown() noexcept override {}
    void     update(const PerformanceData& perf, const NavState& nav) noexcept override;
    [[nodiscard]] const FuelState& get_fuel_state() const noexcept override { return state_; }
    [[nodiscard]] SystemStatus     get_status()     const noexcept override { return status_; }

private:
    FuelState    state_{};
    SystemStatus status_{SystemStatus::NORMAL};
    static constexpr double INITIAL_FUEL_KG = 18000.0;
    static constexpr double IMBALANCE_WARN  = 200.0;
    static constexpr double LOW_FUEL_WARN   = 1500.0;
    static constexpr float MIN_FOR_GO_ARD  = 800.0f;
    static constexpr double DT_HR           = 50.0 / 3600000.0;  // 50 ms in hours
};

}  // namespace fms
