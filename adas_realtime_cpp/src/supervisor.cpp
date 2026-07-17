#include "adas/supervisor.hpp"

#include <algorithm>
#include <cmath>

namespace adas {

AdasSupervisor::AdasSupervisor(AdasConfiguration config) noexcept
    : config_(config), acc_(config.limits), lcc_(config.limits), mpc_lcc_(config.limits),
            configuration_valid_(std::isfinite(config.cruise_speed_mps) && config.cruise_speed_mps >= 0.0 &&
                                                     config.limits.max_acceleration_mps2 > 0.0 && config.limits.max_deceleration_mps2 < 0.0 &&
                                                     config.limits.max_steering_angle_rad > 0.0 && config.limits.max_steering_rate_radps > 0.0 &&
                                                     config.minimum_lane_confidence >= 0.0 && config.minimum_lane_confidence <= 1.0 &&
                                                     config.minimum_lead_confidence >= 0.0 && config.minimum_lead_confidence <= 1.0 &&
                                                     config.max_frame_age.count() > 0 && config.maximum_speed_mps > 0.0 &&
                                                     config.maximum_lane_offset_m > 0.0 && config.maximum_heading_error_rad > 0.0) {}

bool AdasSupervisor::fresh(const SensorFrame& frame, TimePoint now) const noexcept {
    return frame.vehicle.valid && frame.timestamp <= now && now - frame.timestamp <= config_.max_frame_age;
}

bool AdasSupervisor::plausible(const SensorFrame& frame) const noexcept {
    const auto& vehicle = frame.vehicle;
    const bool vehicle_ok = std::isfinite(vehicle.speed_mps) && std::isfinite(vehicle.acceleration_mps2) &&
        std::isfinite(vehicle.yaw_rate_radps) && std::isfinite(vehicle.steering_angle_rad) &&
        std::isfinite(vehicle.lane_offset_m) && std::isfinite(vehicle.heading_error_rad) &&
        vehicle.speed_mps >= 0.0 && vehicle.speed_mps <= config_.maximum_speed_mps &&
        std::abs(vehicle.lane_offset_m) <= config_.maximum_lane_offset_m &&
        std::abs(vehicle.heading_error_rad) <= config_.maximum_heading_error_rad;
    const bool lead_ok = !frame.lead.valid ||
        (std::isfinite(frame.lead.longitudinal_distance_m) && std::isfinite(frame.lead.relative_speed_mps) &&
         frame.lead.longitudinal_distance_m > 0.0 && frame.lead.confidence >= 0.0 && frame.lead.confidence <= 1.0);
    const bool lane_ok = !frame.lane.valid ||
        (std::isfinite(frame.lane.lateral_offset_m) && std::isfinite(frame.lane.heading_error_rad) &&
         frame.lane.confidence >= 0.0 && frame.lane.confidence <= 1.0);
    return vehicle_ok && lead_ok && lane_ok;
}

double AdasSupervisor::aeb_deceleration(const VehicleState&, const LeadObject& lead) const noexcept {
    if (!lead.valid || lead.confidence < config_.minimum_lead_confidence || lead.longitudinal_distance_m <= 0.0) {
        return config_.limits.max_acceleration_mps2;
    }
    const double closing_speed = std::max(-lead.relative_speed_mps, 0.0);
    if (closing_speed < 0.1) return config_.limits.max_acceleration_mps2;
    const double ttc_s = lead.longitudinal_distance_m / closing_speed;
    const double braking_distance = (closing_speed * closing_speed) / (2.0 * std::max(-config_.limits.max_deceleration_mps2, 0.1));
    if (ttc_s < 1.5 || lead.longitudinal_distance_m < braking_distance + 2.0) return config_.limits.max_deceleration_mps2;
    if (ttc_s < 2.5) return std::max(-4.0, config_.limits.max_deceleration_mps2);
    return 0.0;
}

ActuatorCommand AdasSupervisor::step(const SensorFrame& frame, TimePoint now, double dt_s) noexcept {
    ActuatorCommand out{};
    out.timestamp = now;
    if (!configuration_valid_) {
        out.faults |= Fault::ConfigurationInvalid;
        out.longitudinal_mode = ControlMode::Fault;
        out.lateral_mode = ControlMode::Fault;
        return out;
    }
    if (!plausible(frame)) {
        out.faults |= Fault::FrameInvalid;
        out.longitudinal_mode = ControlMode::Standby;
        out.lateral_mode = ControlMode::Standby;
        return out;
    }
    if (!fresh(frame, now) || dt_s <= 0.0 || dt_s > 0.1) {
        out.faults |= Fault::FrameStale;
        out.longitudinal_mode = ControlMode::Standby;
        out.lateral_mode = ControlMode::Standby;
        return out;
    }
    if (frame.vehicle.driver_override) {
        out.faults |= Fault::DriverOverride;
        out.longitudinal_mode = ControlMode::Standby;
        out.lateral_mode = ControlMode::Standby;
        return out;
    }

    const auto& ego = frame.vehicle;
    if (frame.lead.valid && frame.lead.confidence >= config_.minimum_lead_confidence) {
        if (!range_filter_.update(frame.lead.longitudinal_distance_m, frame.lead.relative_speed_mps, dt_s)) {
            out.faults |= Fault::EstimatorRejectedMeasurement;
        }
    } else {
        out.faults |= Fault::LeadUnavailable;
    }

    if (ego.brake_available) {
        LeadObject filtered_lead = frame.lead;
        if (range_filter_.initialized() && frame.lead.valid) {
            filtered_lead.longitudinal_distance_m = range_filter_.range_m();
            filtered_lead.relative_speed_mps = range_filter_.range_rate_mps();
        }
        const double acc_request = acc_.compute(ego, filtered_lead, config_.cruise_speed_mps, dt_s);
        const double emergency_request = aeb_deceleration(ego, filtered_lead);
        out.requested_acceleration_mps2 = std::min(acc_request, emergency_request);
        out.aeb_request = emergency_request < 0.0;
        out.longitudinal_mode = ControlMode::Active;
    } else {
        out.faults |= Fault::BrakeUnavailable;
        out.longitudinal_mode = ControlMode::Fault;
    }

    if (ego.steering_available && frame.lane.valid && frame.lane.confidence >= config_.minimum_lane_confidence) {
        out.requested_steering_angle_rad = config_.use_mpc_lateral
            ? mpc_lcc_.compute(ego, frame.lane, dt_s)
            : lcc_.compute(ego, frame.lane, dt_s);
        out.lateral_mode = ControlMode::Active;
    } else {
        out.faults |= ego.steering_available ? Fault::LaneUnavailable : Fault::SteeringUnavailable;
        out.lateral_mode = ControlMode::Degraded;
    }

    out.requested_acceleration_mps2 = std::clamp(out.requested_acceleration_mps2, config_.limits.max_deceleration_mps2, config_.limits.max_acceleration_mps2);
    out.requested_steering_angle_rad = std::clamp(out.requested_steering_angle_rad, -config_.limits.max_steering_angle_rad, config_.limits.max_steering_angle_rad);
    return out;
}

}  // namespace adas
