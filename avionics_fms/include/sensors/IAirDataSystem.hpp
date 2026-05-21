/**
 * @file IAirDataSystem.hpp
 * @brief Air Data Computer interface (ADS-B, pitot-static, TAT probe)
 */
#pragma once
#include "sensors/SensorTypes.hpp"
#include "fms/FmsTypes.hpp"

namespace fms::sensors {
class IAirDataSystem {
public:
    virtual ~IAirDataSystem() = default;
    virtual fms::FmsError init()       = 0;
    virtual void          deinit()     = 0;
    virtual fms::FmsError update()     = 0;  // Called at 50Hz
    virtual const AdcRaw &get_data() const = 0;
    virtual fms::SystemStatus get_status() const = 0;
};
}
