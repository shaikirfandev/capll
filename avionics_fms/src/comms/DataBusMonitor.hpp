/**
 * @file DataBusMonitor.hpp
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include <chrono>

namespace fms::comms {

class DataBusMonitor {
public:
    FmsError init() noexcept;
    void     update() noexcept;
    void     mark_arinc429_active() noexcept;
    void     mark_afdx_active()     noexcept;
    void     mark_can_active()      noexcept;
    [[nodiscard]] bool is_arinc429_healthy() const noexcept;
    [[nodiscard]] bool is_afdx_healthy()     const noexcept;
    [[nodiscard]] bool is_can_healthy()      const noexcept;
    [[nodiscard]] SystemStatus get_status()  const noexcept;

private:
    using Clock     = std::chrono::steady_clock;
    using TimePoint = Clock::time_point;
    static constexpr uint32_t TIMEOUT_MS = 1000U;

    TimePoint last_arinc429_{};
    TimePoint last_afdx_{};
    TimePoint last_can_{};
    SystemStatus status_{SystemStatus::NORMAL};
};

}  // namespace fms::comms
