/**
 * @file IGuidanceComputer.hpp
 * @brief Guidance Computer Interface — LNAV/VNAV outputs for autopilot
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms {

class IGuidanceComputer {
public:
    virtual ~IGuidanceComputer() = default;

    virtual FmsError init()     = 0;
    virtual void     shutdown() = 0;

    virtual void update(const NavState &nav, const FlightPlan &fp,
                        const PerformanceData &perf) = 0;

    virtual const LateralGuidance  &get_lateral_guidance()  const = 0;
    virtual const VerticalGuidance &get_vertical_guidance() const = 0;
    virtual FmsMode                 get_fms_mode()          const = 0;

    virtual void     set_lnav_mode(LnavMode mode) = 0;
    virtual void     set_vnav_mode(VnavMode mode) = 0;
    virtual FmsError execute_missed_approach()    = 0;
    virtual FmsError direct_to(const char *ident) = 0;

    virtual SystemStatus get_status() const = 0;
};

}  // namespace fms
