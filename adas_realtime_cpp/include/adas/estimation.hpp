#pragma once

#include "adas/types.hpp"

namespace adas {

// Two-state discrete Kalman filter: x = [range_m, range_rate_mps].
// Suitable for a radar/camera track after sensor-specific validation.
class RangeKalmanFilter {
public:
    void reset(double range_m, double range_rate_mps) noexcept;
    bool update(double measured_range_m, double measured_range_rate_m, double dt_s) noexcept;
    [[nodiscard]] double range_m() const noexcept { return x_[0]; }
    [[nodiscard]] double range_rate_mps() const noexcept { return x_[1]; }
    [[nodiscard]] bool initialized() const noexcept { return initialized_; }

private:
    double x_[2]{};
    double p_[2][2]{{25.0, 0.0}, {0.0, 9.0}};
    bool initialized_{};
};

}  // namespace adas
