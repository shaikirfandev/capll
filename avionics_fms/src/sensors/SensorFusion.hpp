/**
 * @file SensorFusion.hpp
 * @brief 10-state Extended Kalman Filter
 */
#pragma once
#include "sensors/SensorTypes.hpp"
#include "fms/FmsTypes.hpp"
#include <array>

namespace fms::sensors {

static constexpr int EKF_STATES = 10;
using Matrix10 = std::array<std::array<double, EKF_STATES>, EKF_STATES>;

struct FusedState {
    double lat_deg{};
    double lon_deg{};
    float  alt_m{};
    double vel_north_ms{};
    double vel_east_ms{};
    double vel_down_ms{};
    float  anp_nm{1.0f};
    bool   valid{false};
};

class SensorFusion {
public:
    FmsError init() noexcept;
    void update(const GpsRaw& gps, const InsRaw& ins, const AdcRaw& adc) noexcept;
    [[nodiscard]] const FusedState& get_state() const noexcept { return state_; }

private:
    FusedState state_{};
    Matrix10 P_{};  // Covariance
    bool initialized_{false};
    void predict(const InsRaw& ins) noexcept;
    void update_gps(const GpsRaw& gps) noexcept;
    static Matrix10 identity() noexcept;
};

}  // namespace fms::sensors
