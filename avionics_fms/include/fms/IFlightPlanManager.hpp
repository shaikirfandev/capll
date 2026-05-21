/**
 * @file IFlightPlanManager.hpp
 * @brief Flight Plan Manager Interface
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms {

class IFlightPlanManager {
public:
    virtual ~IFlightPlanManager() = default;

    virtual FmsError init(const char *navdb_path) = 0;
    virtual void     shutdown() = 0;

    virtual FmsError activate() = 0;
    virtual void     set_origin(const char *icao) = 0;
    virtual void     set_destination(const char *icao) = 0;
    virtual FmsError insert_waypoint(uint8_t idx, const Waypoint &wpt) = 0;
    virtual FmsError delete_waypoint(uint8_t idx) = 0;
    virtual FmsError sequence_next_waypoint() = 0;
    virtual FmsError direct_to(const char *ident) = 0;
    virtual bool     find_waypoint(const char *ident, Waypoint &out) const = 0;

    virtual const FlightPlan &get_active_fp() const = 0;

    virtual SystemStatus get_status() const = 0;
};

}  // namespace fms
