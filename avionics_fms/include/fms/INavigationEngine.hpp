/**
 * @file INavigationEngine.hpp
 * @brief Navigation Engine Interface — DO-178C DAL-B
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms {

class INavigationEngine {
public:
    virtual ~INavigationEngine() = default;

    virtual FmsError init(LatLon ref) = 0;
    virtual void     shutdown() = 0;

    virtual void     update_gps(double lat, double lon, double alt_m,
                                 double vel_n, double vel_e,
                                 uint8_t sats, float hdop) = 0;
    virtual void     update_adc(float tas_kt, float cas_kt, float mach,
                                 float press_alt_ft, float isa_dev_c) = 0;
    virtual void     set_rnp_requirement(float rnp_nm) = 0;
    virtual bool     is_rnp_satisfied() const = 0;
    virtual const NavState& get_nav_state() const = 0;

    virtual double compute_bearing_deg(const Position3D& from,
                                        const Position3D& to) const = 0;
    virtual double compute_distance_nm(const Position3D& from,
                                        const Position3D& to) const = 0;
    virtual double compute_xte_nm(const Position3D& from, const Position3D& to,
                                   const Position3D& pos) const = 0;

    virtual SystemStatus get_status() const = 0;
};

}  // namespace fms
