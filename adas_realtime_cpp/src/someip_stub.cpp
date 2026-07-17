// ============================================================
// adas/someip_stub.cpp — SOME/IP stub (host simulation)
// ============================================================

#include "adas/someip_stub.hpp"

namespace adas {

bool SomeIpAdasServiceStub::notify_status(const AdasStatusEvent& event) noexcept {
    last_event_ = event;
    return true;
}

void SomeIpAdasServiceStub::on_set_cruise_speed(std::function<bool(double)> handler) noexcept {
    cruise_speed_handler_ = std::move(handler);
}

void SomeIpAdasServiceStub::on_set_enabled(std::function<bool(bool)> handler) noexcept {
    enabled_handler_ = std::move(handler);
}

bool SomeIpAdasServiceStub::simulate_set_cruise_speed(double speed_mps) noexcept {
    if (cruise_speed_handler_) return cruise_speed_handler_(speed_mps);
    return false;
}

bool SomeIpAdasServiceStub::simulate_set_enabled(bool enabled) noexcept {
    if (enabled_handler_) return enabled_handler_(enabled);
    return false;
}

}  // namespace adas
