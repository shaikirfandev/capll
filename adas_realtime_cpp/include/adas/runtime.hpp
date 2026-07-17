#pragma once

#include "adas/interfaces.hpp"
#include "adas/supervisor.hpp"

#include <chrono>

namespace adas {

// OS-neutral execution shell. A QNX/AUTOSAR adapter invokes run_cycle() from its
// configured 20 ms runnable/thread; the algorithm remains transport-independent.
class ControlRuntime final {
public:
    ControlRuntime(AdasSupervisor& supervisor, IVehicleGateway& gateway, std::chrono::microseconds deadline) noexcept;
    [[nodiscard]] bool run_cycle(TimePoint now, double dt_s) noexcept;
    [[nodiscard]] CycleHealth health() const noexcept { return health_; }

private:
    AdasSupervisor& supervisor_;
    IVehicleGateway& gateway_;
    std::chrono::microseconds deadline_;
    CycleHealth health_{};
};

}  // namespace adas
