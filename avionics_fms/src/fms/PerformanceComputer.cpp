/**
 * @file PerformanceComputer.cpp
 */
#include "PerformanceComputer.hpp"

namespace fms {

FmsError PerformanceComputer::init() noexcept {
    perf_.tow_kg              = 70000.0;
    perf_.cruise_mach         = 0.78;
    perf_.long_range_mach     = 0.74;
    perf_.fuel_flow_cruise_kghr = 2400.0;
    perf_.fuel_flow_climb_kghr  = 3200.0;
    perf_.opt_cruise_alt_ft   = 35000.0;
    status_                   = SystemStatus::NORMAL;
    return FmsError::OK;
}

void PerformanceComputer::update(const NavState& nav, const FuelState& fuel,
                                  const FlightPlan&) noexcept {
    // Update TOW with fuel burn
    perf_.tow_kg = 41413.0 + fuel.total_fuel_kg;

    // Optimum altitude increases as weight decreases
    perf_.opt_cruise_alt_ft = 35000.0 + (70000.0 - perf_.tow_kg) * 0.2;
    if (perf_.opt_cruise_alt_ft > 41000.0) perf_.opt_cruise_alt_ft = 41000.0;

    (void)nav;
}

}  // namespace fms
