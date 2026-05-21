/**
 * @file NavigationEngine.hpp
 */
#pragma once
#include "fms/INavigationEngine.hpp"
#include "fms/FmsTypes.hpp"

namespace fms {

class NavigationEngine : public INavigationEngine {
public:
    FmsError init(LatLon ref) noexcept override;
    void     shutdown() noexcept override {}
    void     update_gps(double lat, double lon, double alt_m,
                        double vel_n, double vel_e,
                        uint8_t sats, float hdop) noexcept override;
    void     update_adc(float tas, float cas, float mach,
                        float press_alt, float isa_dev) noexcept override;
    void     set_rnp_requirement(float rnp_nm) noexcept override;
    [[nodiscard]] bool            is_rnp_satisfied() const noexcept override;
    [[nodiscard]] const NavState& get_nav_state()   const noexcept override { return state_; }
    [[nodiscard]] double compute_bearing_deg(const Position3D& from,
                                              const Position3D& to) const noexcept override;
    [[nodiscard]] double compute_distance_nm(const Position3D& from,
                                              const Position3D& to) const noexcept override;
    [[nodiscard]] double compute_xte_nm(const Position3D& from,
                                         const Position3D& to,
                                         const Position3D& pos) const noexcept override;
    [[nodiscard]] SystemStatus get_status() const noexcept override { return state_.status; }

private:
    NavState state_{};
};

}  // namespace fms
