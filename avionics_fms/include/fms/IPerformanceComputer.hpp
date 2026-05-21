/**
 * @file IPerformanceComputer.hpp
 * @brief Performance Computer Interface
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms {

struct ClimbProfile { double v2_kt; double v_climb_kt; double mach_climb; };
struct CruiseProfile { double mach; double fl; double step_fl; };
struct DescentProfile { double top_of_descent_nm; double fpa_deg; double vapp_kt; };

class IPerformanceComputer {
public:
    virtual ~IPerformanceComputer() = default;

    virtual FmsError init()     = 0;
    virtual void     shutdown() = 0;

    virtual void update(const NavState &nav, const FuelState &fuel,
                        const FlightPlan &fp) = 0;

    virtual const PerformanceData &get_perf_data() const = 0;
    virtual SystemStatus           get_status()    const = 0;
};

}  // namespace fms
