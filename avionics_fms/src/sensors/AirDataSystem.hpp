/**
 * @file AirDataSystem.hpp
 */
#pragma once
#include "sensors/IAirDataSystem.hpp"
#include "sensors/SensorTypes.hpp"

namespace fms::sensors {

class AirDataSystem : public IAirDataSystem {
public:
    fms::FmsError  init()   noexcept override;
    void           deinit() noexcept override {}
    fms::FmsError  update() noexcept override;
    [[nodiscard]] const AdcRaw&     get_data()   const noexcept override { return data_; }
    [[nodiscard]] fms::SystemStatus get_status() const noexcept override { return status_; }

private:
    AdcRaw              data_{};
    fms::SystemStatus   status_{fms::SystemStatus::NORMAL};
    float sim_alt_ft_{0.0f};
    float sim_cas_kt_{0.0f};
};

}  // namespace fms::sensors
