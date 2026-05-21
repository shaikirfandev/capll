/**
 * @file AirDataSystem.cpp
 * @brief ISA atmosphere model — pitot-static simulation
 */
#include "AirDataSystem.hpp"
#include <cmath>

namespace fms::sensors {

// ISA constants
static constexpr float SEA_LEVEL_PRESSURE_PA = 101325.0f;
static constexpr float SEA_LEVEL_TEMP_K      = 288.15f;
static constexpr float LAPSE_RATE            = 0.0065f;   // K/m
static constexpr float g                     = 9.80665f;
static constexpr float R                     = 287.05f;

static float pressure_to_alt_ft(float p_pa) {
    // Barometric formula (troposphere)
    float T = SEA_LEVEL_TEMP_K * std::pow(p_pa / SEA_LEVEL_PRESSURE_PA,
                                           R * LAPSE_RATE / g);
    float alt_m = (SEA_LEVEL_TEMP_K - T) / LAPSE_RATE;
    return alt_m * 3.28084f;
}

fms::FmsError AirDataSystem::init() noexcept {
    sim_alt_ft_ = 0.0f;
    sim_cas_kt_ = 0.0f;
    data_       = {};
    status_     = fms::SystemStatus::NORMAL;
    return fms::FmsError::OK;
}

fms::FmsError AirDataSystem::update() noexcept {
    // Simulate climb to FL350
    sim_alt_ft_ += 100.0f;
    if (sim_alt_ft_ > 35000.0f) sim_alt_ft_ = 35000.0f;

    sim_cas_kt_ += 1.0f;
    if (sim_cas_kt_ > 280.0f) sim_cas_kt_ = 280.0f;

    const float alt_m = sim_alt_ft_ / 3.28084f;
    const float T     = SEA_LEVEL_TEMP_K - LAPSE_RATE * alt_m;
    const float p     = SEA_LEVEL_PRESSURE_PA *
                        std::pow(T / SEA_LEVEL_TEMP_K, g / (R * LAPSE_RATE));
    const float rho   = p / (R * T);
    const float rho0  = SEA_LEVEL_PRESSURE_PA / (R * SEA_LEVEL_TEMP_K);
    const float sigma = rho / rho0;

    const float cas = sim_cas_kt_ * 0.514444f;  // m/s
    const float tas_ms = cas / std::sqrt(sigma);

    data_.valid            = true;
    data_.pressure_alt_ft  = sim_alt_ft_;
    data_.cas_kt           = sim_cas_kt_;
    data_.tas_kt           = tas_ms / 0.514444f;
    data_.mach             = tas_ms / std::sqrt(1.4f * R * T);
    data_.sat_c            = T - 273.15f;
    data_.isa_deviation_c  = data_.sat_c - (15.0f - 1.98f * (sim_alt_ft_ / 1000.0f));
    (void)pressure_to_alt_ft(p);  // Exercise formula
    return fms::FmsError::OK;
}

}  // namespace fms::sensors
