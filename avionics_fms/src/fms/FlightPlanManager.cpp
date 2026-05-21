/**
 * @file FlightPlanManager.cpp
 * @req SRS-FPM-001..SRS-FPM-020
 */
#include "FlightPlanManager.hpp"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace fms {

const FlightPlanManager::NavDbEntry FlightPlanManager::NAV_DB[] = {
    {"EGLL",  51.4775, -0.4614,  WaypointType::AIRPORT},
    {"KSFO",  37.6213,-122.3790, WaypointType::AIRPORT},
    {"KLAX",  33.9425,-118.4081, WaypointType::AIRPORT},
    {"EDDF",  50.0333,   8.5706, WaypointType::AIRPORT},
    {"LAM",   51.6458,   0.1522, WaypointType::VOR},
    {"OCK",   51.3050,  -0.4472, WaypointType::VOR},
    {"WOBUN", 53.1667,  -1.5833, WaypointType::INTERSECTION},
    {"MALOT", 54.9167,  -7.2500, WaypointType::INTERSECTION},
    {"SUNOT", 57.0833, -13.5000, WaypointType::INTERSECTION},
    {"MIMKU", 59.8333, -24.0000, WaypointType::INTERSECTION},
    {"SFO",   37.6195,-122.3748, WaypointType::VOR},
    {"KSFO",  37.6213,-122.3790, WaypointType::AIRPORT},
};

FmsError FlightPlanManager::init(const char* /*navdb_path*/) noexcept {
    fp_ = {};
    status_ = SystemStatus::NORMAL;
    return FmsError::OK;
}

FmsError FlightPlanManager::activate() noexcept {
    if (fp_.wpt_count < 2U) return FmsError::ERR_FP_INVALID;
    fp_.state = FlightPlanState::ACTIVE;
    fp_.active_wpt_idx = 1U;
    return FmsError::OK;
}

void FlightPlanManager::set_origin(const char* icao) noexcept {
    std::strncpy(fp_.origin_icao, icao, sizeof(fp_.origin_icao) - 1);
}

void FlightPlanManager::set_destination(const char* icao) noexcept {
    std::strncpy(fp_.dest_icao, icao, sizeof(fp_.dest_icao) - 1);
}

FmsError FlightPlanManager::insert_waypoint(uint8_t idx, const Waypoint& wpt) noexcept {
    if (fp_.wpt_count >= MAX_WAYPOINTS) return FmsError::ERR_BUFFER_OVERFLOW;
    if (idx > fp_.wpt_count) return FmsError::ERR_INVALID_PARAM;
    for (uint8_t i = fp_.wpt_count; i > idx; --i) {
        fp_.waypoints[i] = fp_.waypoints[i - 1];
    }
    fp_.waypoints[idx] = wpt;
    fp_.wpt_count++;
    return FmsError::OK;
}

FmsError FlightPlanManager::delete_waypoint(uint8_t idx) noexcept {
    if (idx >= fp_.wpt_count) return FmsError::ERR_INVALID_PARAM;
    for (uint8_t i = idx; i < fp_.wpt_count - 1; ++i) {
        fp_.waypoints[i] = fp_.waypoints[i + 1];
    }
    fp_.waypoints[fp_.wpt_count - 1] = {};
    fp_.wpt_count--;
    return FmsError::OK;
}

FmsError FlightPlanManager::sequence_next_waypoint() noexcept {
    if (fp_.active_wpt_idx + 1 < fp_.wpt_count) {
        fp_.active_wpt_idx++;
    }
    return FmsError::OK;
}

FmsError FlightPlanManager::direct_to(const char* ident) noexcept {
    for (uint8_t i = 0; i < fp_.wpt_count; ++i) {
        if (std::strncmp(fp_.waypoints[i].ident, ident, 8) == 0) {
            fp_.active_wpt_idx = i;
            return FmsError::OK;
        }
    }
    // Find in nav-db and add
    Waypoint wpt{};
    if (!find_waypoint(ident, wpt)) return FmsError::ERR_PROCEDURE_NOT_FOUND;
    fp_.active_wpt_idx = fp_.wpt_count;
    return insert_waypoint(fp_.wpt_count, wpt);
}

bool FlightPlanManager::find_waypoint(const char* ident, Waypoint& out) const noexcept {
    for (std::size_t i = 0; i < NAV_DB_SIZE; ++i) {
        if (std::strncmp(NAV_DB[i].ident, ident, 8) == 0) {
            std::strncpy(out.ident, NAV_DB[i].ident, 8);
            out.position.lat_deg = NAV_DB[i].lat;
            out.position.lon_deg = NAV_DB[i].lon;
            out.type     = NAV_DB[i].type;
            return true;
        }
    }
    return false;
}

}  // namespace fms
