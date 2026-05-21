/**
 * @file FuelManagement.cpp
 */
#include "FuelManagement.hpp"
#include <cmath>

namespace fms {

FmsError FuelManagement::init() noexcept {
    state_.total_fuel_kg   = INITIAL_FUEL_KG;
    state_.left_wing_kg    = INITIAL_FUEL_KG / 2.0;
    state_.right_wing_kg   = INITIAL_FUEL_KG / 2.0;
    state_.fuel_used_kg    = 0.0;
    state_.imbalance_warn  = false;
    state_.low_fuel_warn   = false;
    status_ = SystemStatus::NORMAL;
    return FmsError::OK;
}

void FuelManagement::update(const PerformanceData& perf, const NavState&) noexcept {
    const double burn = perf.fuel_flow_cruise_kghr * DT_HR;
    state_.left_wing_kg  -= burn / 2.0;
    state_.right_wing_kg -= burn / 2.0;
    if (state_.left_wing_kg  < 0.0) state_.left_wing_kg  = 0.0;
    if (state_.right_wing_kg < 0.0) state_.right_wing_kg = 0.0;
    state_.total_fuel_kg  = state_.left_wing_kg + state_.right_wing_kg;
    state_.fuel_used_kg  += burn;

    state_.imbalance_warn = std::fabs(state_.left_wing_kg - state_.right_wing_kg) > IMBALANCE_WARN;
    state_.low_fuel_warn  = state_.total_fuel_kg < LOW_FUEL_WARN;

    if (state_.low_fuel_warn) status_ = SystemStatus::WARNING;
}

}  // namespace fms
