/**
 * @file GuidanceComputer.cpp
 * @req SRS-GUID-001..SRS-GUID-004
 */
#include "GuidanceComputer.hpp"
#include "NavigationEngine.hpp"
#include <cmath>
#include <cstring>
#include <algorithm>

namespace fms {

static constexpr float MAX_BANK_DEG    = 25.0f;
static constexpr float XTE_TO_BANK_KP  = 3.0f;   // deg/nm

FmsError GuidanceComputer::init() noexcept {
    mode_   = {};
    lat_    = {};
    vert_   = {};
    status_ = SystemStatus::NORMAL;
    return FmsError::OK;
}

void GuidanceComputer::set_lnav_mode(LnavMode m) noexcept { mode_.lnav = m; }
void GuidanceComputer::set_vnav_mode(VnavMode m) noexcept { mode_.vnav = m; }

float GuidanceComputer::bank_from_xte(float xte_nm) const noexcept {
    float cmd = xte_nm * XTE_TO_BANK_KP;
    return std::max(-MAX_BANK_DEG, std::min(MAX_BANK_DEG, cmd));
}

void GuidanceComputer::update_lnav(const NavState& nav, const FlightPlan& fp) noexcept {
    if (fp.wpt_count < 2U || fp.active_wpt_idx >= fp.wpt_count) return;
    const uint8_t prev_idx = (fp.active_wpt_idx > 0) ? fp.active_wpt_idx - 1 : 0;
    const auto& from_ll = fp.waypoints[prev_idx].position;
    const auto& to_ll   = fp.waypoints[fp.active_wpt_idx].position;
    const Position3D from{from_ll.lat_deg, from_ll.lon_deg, 0.0};
    const Position3D to{to_ll.lat_deg, to_ll.lon_deg, 0.0};

    // Use static helpers directly (no nav_eng instance needed)
    NavigationEngine nav_eng;
    nav_eng.init(LatLon{nav.position.lat_deg, nav.position.lon_deg});

    const double xte = nav_eng.compute_xte_nm(from, to, nav.position);
    lat_.xte_nm      = xte;
    lat_.roll_cmd_deg = static_cast<double>(bank_from_xte(static_cast<float>(xte)));
}

void GuidanceComputer::update_vnav(const NavState& nav, const FlightPlan& fp,
                                    const PerformanceData& perf) noexcept {
    if (mode_.vnav != VnavMode::VNAV_PTH && mode_.vnav != VnavMode::VNAV_SPD) return;
    if (fp.wpt_count < 2U || fp.active_wpt_idx >= fp.wpt_count) return;
    const auto& target_wpt = fp.waypoints[fp.active_wpt_idx];

    // Use waypoint constraint if set, otherwise optimum cruise altitude
    const double target_alt = (target_wpt.alt_constraint_ft > 0.0)
                               ? target_wpt.alt_constraint_ft
                               : perf.opt_cruise_alt_ft;

    const float alt_error = static_cast<float>(target_alt) - static_cast<float>(nav.position.alt_ft);
    const float vs_cmd    = std::max(-3000.0f, std::min(3000.0f, alt_error * 0.5f));
    vert_.vs_cmd_fpm  = static_cast<double>(vs_cmd);
    vert_.in_descent  = vs_cmd < 0.0f;
}

void GuidanceComputer::update(const NavState& nav, const FlightPlan& fp,
                               const PerformanceData& perf) noexcept {
    if (fp.state != FlightPlanState::ACTIVE) return;

    if (mode_.lnav == LnavMode::LNAV || mode_.lnav == LnavMode::APPROACH) {
        update_lnav(nav, fp);
    }
    if (mode_.vnav == VnavMode::VNAV_PTH || mode_.vnav == VnavMode::VNAV_SPD) {
        update_vnav(nav, fp, perf);
    }
}

FmsError GuidanceComputer::execute_missed_approach() noexcept {
    mode_.lnav = LnavMode::HDG_SEL;
    mode_.vnav = VnavMode::ALT_HOLD;
    return FmsError::OK;
}

FmsError GuidanceComputer::direct_to(const char* ident) noexcept {
    std::strncpy(direct_to_ident_, ident, sizeof(direct_to_ident_) - 1);
    mode_.lnav = LnavMode::LNAV;
    return FmsError::OK;
}

}  // namespace fms
