/**
 * @file InertialNavSystem.cpp
 * @brief Strapdown INS with Schuler oscillation and RLG drift simulation
 */
#include "InertialNavSystem.hpp"
#include <cmath>
#include <chrono>

using namespace std::chrono;

namespace fms::sensors {

static constexpr double SCHULER_PERIOD_S = 84.38 * 60.0;
static constexpr double DRIFT_NM_PER_S   = 0.8 / 3600.0;
static constexpr double NM_TO_DEG        = 1.0 / 60.0;

fms::FmsError InertialNavSystem::init(const fms::Position3D &ref) noexcept {
    ref_pos_    = ref;
    aligned_    = false;
    elapsed_s_  = 0.0;
    start_time_ = steady_clock::now();
    // seed InsRaw with initial attitude; position is tracked in ref_pos_
    data_.true_heading_deg = 270.0;
    data_.pitch_deg        = 2.5;
    data_.roll_deg         = 0.0;
    data_.aligned          = false;
    data_.valid            = false;
    status_                = fms::SystemStatus::NORMAL;
    return fms::FmsError::OK;
}

fms::FmsError InertialNavSystem::update() noexcept {
    elapsed_s_ = duration_cast<duration<double>>(
        steady_clock::now() - start_time_).count();

    // Alignment phase (2 s simulation)
    if (!aligned_ && elapsed_s_ >= 2.0) {
        aligned_    = true;
        data_.valid = true;
    }
    if (!aligned_) return fms::FmsError::OK;

    // Drift: RLG 0.8 nm/hr, modulated by Schuler oscillation
    double drift_nm = DRIFT_NM_PER_S * elapsed_s_ *
                      std::sin(2.0 * M_PI * elapsed_s_ / SCHULER_PERIOD_S);

    // Update position estimate (stored in ref_pos_)
    ref_pos_.lat_deg += drift_nm * NM_TO_DEG;
    ref_pos_.lon_deg += (drift_nm * NM_TO_DEG) /
                        std::cos(ref_pos_.lat_deg * M_PI / 180.0);

    // Simulate westbound cruise attitude & velocity
    data_.vel_north_ms    = -10.0;
    data_.vel_east_ms     = -220.0;
    data_.vel_down_ms     =   0.0;
    data_.roll_deg        =   0.0;
    data_.pitch_deg       =   2.5;
    data_.true_heading_deg = 270.0;
    data_.accel_x_ms2     =   0.0;
    data_.accel_y_ms2     =   0.0;
    data_.accel_z_ms2     =  -9.81;
    return fms::FmsError::OK;
}

}  // namespace fms::sensors
