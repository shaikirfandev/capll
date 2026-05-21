/**
 * @file GpsReceiver.hpp
 */
#pragma once
#include "sensors/IGpsReceiver.hpp"
#include "sensors/SensorTypes.hpp"
#include <random>

namespace fms::sensors {

class GpsReceiver : public IGpsReceiver {
public:
    fms::FmsError init() noexcept override;
    void          deinit() noexcept override {}
    fms::FmsError update() noexcept override;
    [[nodiscard]] const GpsRaw&       get_data()   const noexcept override { return data_; }
    [[nodiscard]] bool                has_fix()    const noexcept override { return data_.valid; }
    [[nodiscard]] fms::SystemStatus   get_status() const noexcept override { return status_; }

    // Non-virtual helper exposed to SensorFusion
    [[nodiscard]] bool is_raim_ok() const noexcept;

private:
    GpsRaw   data_{};
    fms::SystemStatus status_{fms::SystemStatus::NORMAL};
    double   sim_lon_{-0.4614};
    std::mt19937 rng_;
    std::normal_distribution<double> noise_{0.0, 1.5e-5};  // ~1.5 m in degrees
    static constexpr uint8_t MIN_SATS_FOR_RAIM = 5U;
};

}  // namespace fms::sensors
