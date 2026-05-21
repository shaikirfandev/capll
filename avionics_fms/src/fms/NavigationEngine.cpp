/**
 * @file NavigationEngine.cpp
 * @brief Haversine navigation, RNP monitoring
 * @req SRS-NAV-001..SRS-NAV-005
 */
#include "NavigationEngine.hpp"
#include <cmath>
#include <cstring>

namespace fms {

static constexpr double R_NM = 3440.065;  // Earth radius in nautical miles
static constexpr double DEG2RAD = M_PI / 180.0;

FmsError NavigationEngine::init(LatLon ref) noexcept {
    state_ = {};
    state_.position.lat_deg = ref.lat_deg;
    state_.position.lon_deg = ref.lon_deg;
    state_.rnp_nm    = 2.0f;
    state_.anp_nm    = 99.0f;
    state_.mode      = NavMode::DEAD_RECK;
    state_.status    = SystemStatus::NORMAL;
    return FmsError::OK;
}

void NavigationEngine::update_gps(double lat, double lon, double alt_m,
                                   double vel_n, double vel_e,
                                   uint8_t sats, float hdop) noexcept {
    state_.position.lat_deg = lat;
    state_.position.lon_deg = lon;
    state_.position.alt_ft  = static_cast<float>(alt_m * 3.28084);
    state_.velocity.north_ms = vel_n;
    state_.velocity.east_ms  = vel_e;

    // ANP proportional to HDOP and satellite count
    const float base_anp = 0.01f * hdop;
    const float sat_factor = (sats >= 8U) ? 1.0f : (2.0f / static_cast<float>(sats));
    state_.anp_nm = base_anp * sat_factor;

    if (sats >= 4U && hdop < 3.0f) {
        state_.mode = NavMode::GPS_AIDED;
    }

    // Ground speed from velocity components
    const double gs_ms = std::sqrt(vel_n * vel_n + vel_e * vel_e);
    state_.ground_speed_kt = static_cast<float>(gs_ms * 1.94384);  // m/s → kt

    if (!is_rnp_satisfied()) {
        state_.status = SystemStatus::WARNING;
    } else {
        state_.status = SystemStatus::NORMAL;
    }
}

void NavigationEngine::update_adc(float tas, float cas, float mach,
                                   float press_alt, float /*isa_dev*/) noexcept {
    state_.tas_kt         = tas;
    state_.cas_kt         = cas;
    state_.mach           = mach;
    state_.position.alt_ft = press_alt;
}

void NavigationEngine::set_rnp_requirement(float rnp_nm) noexcept {
    state_.rnp_nm = rnp_nm;
}

bool NavigationEngine::is_rnp_satisfied() const noexcept {
    return state_.anp_nm <= state_.rnp_nm;
}

double NavigationEngine::compute_bearing_deg(const Position3D& from,
                                              const Position3D& to) const noexcept {
    const double lat1 = from.lat_deg * DEG2RAD;
    const double lat2 = to.lat_deg   * DEG2RAD;
    const double dlon = (to.lon_deg - from.lon_deg) * DEG2RAD;

    const double y = std::sin(dlon) * std::cos(lat2);
    const double x = std::cos(lat1) * std::sin(lat2) -
                     std::sin(lat1) * std::cos(lat2) * std::cos(dlon);
    double brg = std::atan2(y, x) / DEG2RAD;
    if (brg < 0.0) brg += 360.0;
    return brg;
}

double NavigationEngine::compute_distance_nm(const Position3D& from,
                                              const Position3D& to) const noexcept {
    const double lat1 = from.lat_deg * DEG2RAD;
    const double lat2 = to.lat_deg   * DEG2RAD;
    const double dlat = lat2 - lat1;
    const double dlon = (to.lon_deg - from.lon_deg) * DEG2RAD;

    const double a = std::sin(dlat / 2) * std::sin(dlat / 2) +
                     std::cos(lat1) * std::cos(lat2) *
                     std::sin(dlon / 2) * std::sin(dlon / 2);
    return 2.0 * R_NM * std::asin(std::sqrt(a));
}

double NavigationEngine::compute_xte_nm(const Position3D& from,
                                         const Position3D& to,
                                         const Position3D& pos) const noexcept {
    const double d13 = compute_distance_nm(from, pos) / R_NM;
    const double brg13 = compute_bearing_deg(from, pos)  * DEG2RAD;
    const double brg12 = compute_bearing_deg(from, to)   * DEG2RAD;
    return std::asin(std::sin(d13) * std::sin(brg13 - brg12)) * R_NM;
}

}  // namespace fms
