#pragma once

// ============================================================
// adas/someip_stub.hpp — SOME/IP service stub (host-side simulation)
//
// In production, replace this with generated ara::com proxies
// (Adaptive AUTOSAR) or vsomeip-based client (QNX / Linux).
//
// This stub models the ADAS function announcement service:
//   Service ID  : 0x0A01  (ADAS Control)
//   Instance ID : 0x0001
//   Methods     : SetCruiseSpeed (0x0001), SetEnabled (0x0002)
//   Events      : ControlStatus (0x8001)
//
// Thread safety: not thread-safe. All calls must originate from
// the same thread (the integration/gateway layer).
// ============================================================

#include "adas/types.hpp"

#include <cstdint>
#include <functional>
#include <optional>

namespace adas {

// ControlStatus event payload sent from ADAS to consumer ECUs
struct AdasStatusEvent {
    std::uint64_t timestamp_us{};
    float requested_acceleration_mps2{};
    float requested_steering_angle_rad{};
    std::uint8_t longitudinal_mode{};  // maps to ControlMode
    std::uint8_t lateral_mode{};
    std::uint32_t faults{};
    bool aeb_active{};
};

/// @brief Interface that a real vsomeip/ara::com adapter implements.
class ISomeIpAdasService {
public:
    virtual ~ISomeIpAdasService() = default;

    /// @brief Send a ControlStatus event notification to all subscribers.
    virtual bool notify_status(const AdasStatusEvent& event) noexcept = 0;

    /// @brief Register handler for SetCruiseSpeed method request.
    /// @param handler Called with target speed (m/s). Returns true on accept.
    virtual void on_set_cruise_speed(std::function<bool(double)> handler) noexcept = 0;

    /// @brief Register handler for SetEnabled method request.
    virtual void on_set_enabled(std::function<bool(bool)> handler) noexcept = 0;
};

/// @brief In-process stub used for host SIL and unit tests.
class SomeIpAdasServiceStub final : public ISomeIpAdasService {
public:
    bool notify_status(const AdasStatusEvent& event) noexcept override;
    void on_set_cruise_speed(std::function<bool(double)> handler) noexcept override;
    void on_set_enabled(std::function<bool(bool)> handler) noexcept override;

    // Test accessors
    [[nodiscard]] std::optional<AdasStatusEvent> last_event() const noexcept { return last_event_; }
    bool simulate_set_cruise_speed(double speed_mps) noexcept;
    bool simulate_set_enabled(bool enabled) noexcept;

private:
    std::optional<AdasStatusEvent> last_event_;
    std::function<bool(double)> cruise_speed_handler_;
    std::function<bool(bool)> enabled_handler_;
};

}  // namespace adas
