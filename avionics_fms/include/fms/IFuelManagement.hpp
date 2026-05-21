/**
 * @file IFuelManagement.hpp
 * @brief Fuel Management System Interface
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms {

class IFuelManagement {
public:
    virtual ~IFuelManagement() = default;

    virtual FmsError init()     = 0;
    virtual void     shutdown() = 0;

    virtual void update(const PerformanceData &perf, const NavState &nav) = 0;

    virtual const FuelState &get_fuel_state() const = 0;
    virtual SystemStatus     get_status() const = 0;
};

}  // namespace fms
