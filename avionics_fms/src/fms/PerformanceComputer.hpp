/**
 * @file PerformanceComputer.hpp
 */
#pragma once
#include "fms/IPerformanceComputer.hpp"
#include "fms/FmsTypes.hpp"

namespace fms {

class PerformanceComputer : public IPerformanceComputer {
public:
    FmsError init() noexcept override;
    void     shutdown() noexcept override {}
    void     update(const NavState& nav, const FuelState& fuel,
                    const FlightPlan& fp) noexcept override;
    [[nodiscard]] const PerformanceData& get_perf_data() const noexcept override { return perf_; }
    [[nodiscard]] SystemStatus           get_status()    const noexcept override { return status_; }

private:
    PerformanceData perf_{};
    SystemStatus    status_{SystemStatus::NORMAL};
};

}  // namespace fms
