/**
 * @file GpsReceiver.cpp
 * @brief EGLL->KSFO westbound GPS simulation with RAIM
 */
#include "GpsReceiver.hpp"

namespace fms::sensors {

fms::FmsError GpsReceiver::init() noexcept {
    data_    = {};
    sim_lon_ = -0.4614;
    rng_.seed(42U);
    status_  = fms::SystemStatus::NORMAL;
    return fms::FmsError::OK;
}

fms::FmsError GpsReceiver::update() noexcept {
    // Advance westbound
    sim_lon_ -= 0.05;
    if (sim_lon_ < -180.0) sim_lon_ = -180.0;

    data_.valid          = true;
    data_.lat_deg        = 51.4775 + noise_(rng_);
    data_.lon_deg        = sim_lon_ + noise_(rng_);
    data_.alt_wgs84_m    = 10668.0 + noise_(rng_) * 10.0;
    data_.vel_north_ms   = -10.0 + noise_(rng_) * 0.1;
    data_.vel_east_ms    = -220.0 + noise_(rng_) * 0.1;
    data_.vel_down_ms    = 0.0;
    data_.hdop           = 0.9;
    data_.vdop           = 1.2;
    data_.num_satellites = 9U;
    data_.fix_quality    = 2U;  // 3D fix
    return fms::FmsError::OK;
}

bool GpsReceiver::is_raim_ok() const noexcept {
    return (data_.num_satellites >= MIN_SATS_FOR_RAIM) && (data_.hdop < 2.0);
}

}  // namespace fms::sensors
