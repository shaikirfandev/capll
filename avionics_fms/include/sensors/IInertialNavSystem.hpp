/**
 * @file IInertialNavSystem.hpp
 * @brief Inertial Navigation System interface (IRS/AHRS)
 */
#pragma once
#include "sensors/SensorTypes.hpp"
#include "fms/FmsTypes.hpp"

namespace fms::sensors {
class IInertialNavSystem {
public:
    virtual ~IInertialNavSystem() = default;
    virtual fms::FmsError init(const fms::Position3D &ref_pos) = 0;
    virtual void          deinit() = 0;
    virtual fms::FmsError update() = 0;  // Called at 50Hz
    virtual const InsRaw &get_data() const = 0;
    virtual bool          is_aligned() const = 0;
    virtual double        get_drift_rate_nm_hr() const = 0;
    virtual fms::SystemStatus get_status() const = 0;
};
}
