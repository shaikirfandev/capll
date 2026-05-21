/**
 * @file GuidanceComputer.hpp
 */
#pragma once
#include "fms/IGuidanceComputer.hpp"
#include "fms/FmsTypes.hpp"

namespace fms {

class GuidanceComputer : public IGuidanceComputer {
public:
    FmsError init() noexcept override;
    void shutdown() noexcept override {}
    void update(const NavState& nav, const FlightPlan& fp,
                const PerformanceData& perf) noexcept override;
    void     set_lnav_mode(LnavMode mode) noexcept override;
    void     set_vnav_mode(VnavMode mode) noexcept override;
    FmsError execute_missed_approach() noexcept override;
    FmsError direct_to(const char* ident) noexcept override;
    [[nodiscard]] FmsMode    get_fms_mode() const noexcept override { return mode_; }
    [[nodiscard]] SystemStatus get_status() const noexcept override { return status_; }
    [[nodiscard]] const LateralGuidance&  get_lateral_guidance()  const noexcept override { return lat_; }
    [[nodiscard]] const VerticalGuidance& get_vertical_guidance() const noexcept override { return vert_; }

    // Test helpers
    [[nodiscard]] float get_roll_cmd_deg() const noexcept { return static_cast<float>(lat_.roll_cmd_deg); }
    [[nodiscard]] float get_vs_cmd_fpm()   const noexcept { return static_cast<float>(vert_.vs_cmd_fpm); }

private:
    FmsMode         mode_{};
    LateralGuidance lat_{};
    VerticalGuidance vert_{};
    SystemStatus    status_{SystemStatus::NORMAL};
    char            direct_to_ident_[8]{};

    float bank_from_xte(float xte_nm) const noexcept;
    void  update_lnav(const NavState& nav, const FlightPlan& fp) noexcept;
    void  update_vnav(const NavState& nav, const FlightPlan& fp,
                      const PerformanceData& perf) noexcept;
};

}  // namespace fms
