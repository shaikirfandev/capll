/**
 * @file SensorFusion.cpp
 * @brief Simplified 10-state EKF (position/velocity/bias)
 */
#include "SensorFusion.hpp"
#include <cmath>

namespace fms::sensors {

static constexpr double R_EARTH = 6371000.0;

Matrix10 SensorFusion::identity() noexcept {
    Matrix10 m{};
    for (int i = 0; i < EKF_STATES; ++i) m[i][i] = 1.0;
    return m;
}

fms::FmsError SensorFusion::init() noexcept {
    P_ = identity();
    for (int i = 0; i < EKF_STATES; ++i) P_[i][i] = 100.0;  // high initial uncertainty
    initialized_ = false;
    state_ = {};
    return fms::FmsError::OK;
}

void SensorFusion::predict(const InsRaw& ins) noexcept {
    if (!ins.valid) return;
    // Simple propagation
    const double dt = 0.1;  // 10 Hz
    state_.lat_deg    += (ins.vel_north_ms * dt) / R_EARTH * (180.0 / M_PI);
    state_.lon_deg    += (ins.vel_east_ms * dt) /
                         (R_EARTH * std::cos(state_.lat_deg * M_PI / 180.0)) * (180.0 / M_PI);
    state_.vel_north_ms = ins.vel_north_ms;
    state_.vel_east_ms  = ins.vel_east_ms;
    state_.vel_down_ms  = ins.vel_down_ms;

    // Grow covariance
    for (int i = 0; i < 2; ++i)  P_[i][i] += 0.1;    // position grows
    for (int i = 3; i < 6; ++i)  P_[i][i] += 0.01;   // velocity grows
}

void SensorFusion::update_gps(const GpsRaw& gps) noexcept {
    // RAIM: require >=5 sats and hdop < 2.0
    if (!gps.valid || gps.num_satellites < 5U || gps.hdop >= 2.0) return;

    // Measurement noise
    const double R_pos = 1.5 * 1.5;   // (1.5 m)^2
    const double R_vel = 0.1 * 0.1;

    // Innovation (measurement residual)
    const double lat_scale = R_EARTH * (M_PI / 180.0);
    const double lon_scale = R_EARTH * std::cos(state_.lat_deg * M_PI / 180.0) * (M_PI / 180.0);

    const double dy_lat = (gps.lat_deg - state_.lat_deg) * lat_scale;
    const double dy_lon = (gps.lon_deg - state_.lon_deg) * lon_scale;
    const double dy_vn  = gps.vel_north_ms - state_.vel_north_ms;
    const double dy_ve  = gps.vel_east_ms  - state_.vel_east_ms;

    // Kalman gain K = P*H' / (H*P*H' + R)  — simplified scalar per axis
    const double K_lat = P_[0][0] / (P_[0][0] + R_pos);
    const double K_lon = P_[1][1] / (P_[1][1] + R_pos);
    const double K_vn  = P_[3][3] / (P_[3][3] + R_vel);
    const double K_ve  = P_[4][4] / (P_[4][4] + R_vel);

    // Update state
    state_.lat_deg      += K_lat * dy_lat / lat_scale;
    state_.lon_deg      += K_lon * dy_lon / lon_scale;
    state_.vel_north_ms += K_vn  * dy_vn;
    state_.vel_east_ms  += K_ve  * dy_ve;

    // Update covariance (Joseph form simplified)
    P_[0][0] *= (1.0 - K_lat);
    P_[1][1] *= (1.0 - K_lon);
    P_[3][3] *= (1.0 - K_vn);
    P_[4][4] *= (1.0 - K_ve);

    // ANP from position covariance (2σ)
    const double horiz_m = 2.0 * std::sqrt(P_[0][0] + P_[1][1]);
    state_.anp_nm = static_cast<float>(horiz_m / 1852.0);
    state_.alt_m  = static_cast<float>(gps.alt_wgs84_m);
    state_.valid  = true;
}

void SensorFusion::update(const GpsRaw& gps, const InsRaw& ins, const AdcRaw& adc) noexcept {
    if (!initialized_ && ins.valid) {
        // Seed EKF from GPS if available, else use a default position
        state_.lat_deg = gps.valid ? gps.lat_deg : 51.4775;
        state_.lon_deg = gps.valid ? gps.lon_deg : -0.4614;
        state_.alt_m   = static_cast<float>(adc.pressure_alt_ft * 0.3048f);
        initialized_   = true;
        state_.valid   = true;
    }
    predict(ins);
    update_gps(gps);
}

}  // namespace fms::sensors
