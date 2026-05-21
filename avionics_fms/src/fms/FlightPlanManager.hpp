/**
 * @file FlightPlanManager.hpp
 */
#pragma once
#include "fms/IFlightPlanManager.hpp"
#include "fms/FmsTypes.hpp"

namespace fms {

class FlightPlanManager : public IFlightPlanManager {
public:
    FmsError init(const char* navdb_path) noexcept override;
    void     shutdown() noexcept override {}
    FmsError activate() noexcept override;
    void     set_origin(const char* icao) noexcept override;
    void     set_destination(const char* icao) noexcept override;
    FmsError insert_waypoint(uint8_t idx, const Waypoint& wpt) noexcept override;
    FmsError delete_waypoint(uint8_t idx) noexcept override;
    FmsError sequence_next_waypoint() noexcept override;
    FmsError direct_to(const char* ident) noexcept override;
    bool     find_waypoint(const char* ident, Waypoint& out) const noexcept override;
    [[nodiscard]] const FlightPlan& get_active_fp() const noexcept override { return fp_; }
    [[nodiscard]] SystemStatus      get_status()    const noexcept override { return status_; }

private:
    FlightPlan fp_{};
    SystemStatus status_{SystemStatus::NORMAL};

    struct NavDbEntry { char ident[8]; double lat; double lon; WaypointType type; };
    static const NavDbEntry NAV_DB[];
    static constexpr std::size_t NAV_DB_SIZE = 12U;
};

}  // namespace fms
