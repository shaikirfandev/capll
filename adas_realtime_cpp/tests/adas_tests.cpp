#include "adas/runtime.hpp"
#include "adas/spsc_queue.hpp"
#include "adas/supervisor.hpp"
#include "adas/vehicle_gateway.hpp"

#include <cassert>
#include <chrono>
#include <cmath>
#include <iostream>

int main() {
    using namespace std::chrono;
    adas::AdasSupervisor supervisor;
    const auto now = steady_clock::now();
    adas::SensorFrame nominal{now, {now, 20.0, 0.0, 0.0, 0.0, 0.20, 0.02, false, true, true, true}, {45.0, -2.0, 0.9, true}, {0.20, 0.02, 0.9, true}};
    const auto command = supervisor.step(nominal, now, 0.02);
    assert(command.longitudinal_mode == adas::ControlMode::Active);
    assert(command.lateral_mode == adas::ControlMode::Active);
    assert(command.requested_acceleration_mps2 > 0.0);
    assert(std::abs(command.requested_steering_angle_rad) <= 0.55);

    auto collision = nominal;
    collision.lead = {8.0, -12.0, 0.95, true};
    const auto emergency = supervisor.step(collision, now + 20ms, 0.02);
    assert(emergency.aeb_request);
    assert(emergency.requested_acceleration_mps2 <= -4.0);

    auto stale = nominal;
    stale.timestamp = now - 200ms;
    const auto fallback = supervisor.step(stale, now, 0.02);
    assert(fallback.longitudinal_mode == adas::ControlMode::Standby);
    assert(adas::has_fault(fallback.faults, adas::Fault::FrameStale));

    auto invalid = nominal;
    invalid.vehicle.speed_mps = -1.0;
    const auto rejected = supervisor.step(invalid, now, 0.02);
    assert(rejected.longitudinal_mode == adas::ControlMode::Standby);
    assert(adas::has_fault(rejected.faults, adas::Fault::FrameInvalid));

    adas::SpscQueue<int, 4> queue;
    assert(queue.try_push(7));
    assert(queue.try_push(11));
    assert(queue.try_pop().value() == 7);
    assert(queue.try_pop().value() == 11);
    assert(!queue.try_pop().has_value());

    adas::InMemoryVehicleGateway gateway;
    adas::ControlRuntime runtime(supervisor, gateway, 10ms);
    gateway.publish(nominal);
    assert(runtime.run_cycle(now, 0.02));
    assert(runtime.health().cycle_count == 1U);
    assert(gateway.last_command().has_value());
    std::cout << "All ADAS core tests passed\n";
}
