#pragma once

#include "adas/controllers.hpp"
#include "adas/estimation.hpp"

namespace adas {

struct AdasConfiguration {
    Limits limits{};
    double cruise_speed_mps{27.78};
    double minimum_lane_confidence{0.60};
    double minimum_lead_confidence{0.55};
    std::chrono::milliseconds max_frame_age{100};
    double maximum_speed_mps{70.0};
    double maximum_lane_offset_m{3.0};
    double maximum_heading_error_rad{0.8};
    bool use_mpc_lateral{true};
};

// Safety envelope: validates freshness and availability, gives driver input priority,
// and limits every actuator request before it crosses the vehicle boundary.
class AdasSupervisor {
public:
    explicit AdasSupervisor(AdasConfiguration config = {}) noexcept;
    ActuatorCommand step(const SensorFrame& frame, TimePoint now, double dt_s) noexcept;
    [[nodiscard]] bool configuration_valid() const noexcept { return configuration_valid_; }

private:
    [[nodiscard]] bool fresh(const SensorFrame& frame, TimePoint now) const noexcept;
    [[nodiscard]] bool plausible(const SensorFrame& frame) const noexcept;
    [[nodiscard]] double aeb_deceleration(const VehicleState& ego, const LeadObject& lead) const noexcept;
    AdasConfiguration config_;
    AdaptiveCruiseControl acc_;
    LaneCenteringController lcc_;
    MpcLaneCenteringController mpc_lcc_;
    RangeKalmanFilter range_filter_;
    bool configuration_valid_{};
};

}  // namespace adas
