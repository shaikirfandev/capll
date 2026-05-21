/**
 * @file InertialNavSystem.hpp
 */
#pragma once
#include "sensors/IInertialNavSystem.hpp"
#include "sensors/SensorTypes.hpp"
#include <chrono>

namespace fms::sensors {

class InertialNavSystem : public IInertialNavSystem {
public:
    fms::FmsError init(const fms::Position3D &ref_pos) noexcept override;
    void          deinit() noexcept override {}
    fms::FmsError update() noexcept override;
    [[nodiscard]] const InsRaw&   get_data()           const noexcept override { return data_; }
    [[nodiscard]] bool            is_aligned()          const noexcept override { return aligned_; }
    [[nodiscard]] double          get_drift_rate_nm_hr() const noexcept override { return 0.8; }
    [[nodiscard]] fms::SystemStatus get_status()        const noexcept override { return status_; }

private:
    InsRaw   data_{};
    bool     aligned_{false};
    fms::SystemStatus status_{fms::SystemStatus::NORMAL};
    fms::Position3D ref_pos_{};
    std::chrono::steady_clock::time_point start_time_;
    double elapsed_s_{0.0};
};

}  // namespace fms::sensors
