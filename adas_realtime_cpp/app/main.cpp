#include "adas/runtime.hpp"
#include "adas/supervisor.hpp"
#include "adas/vehicle_gateway.hpp"

#include <chrono>
#include <iostream>
#include <thread>

int main() {
    using namespace std::chrono;
    adas::AdasSupervisor supervisor;
    adas::InMemoryVehicleGateway gateway;
    adas::ControlRuntime runtime(supervisor, gateway, 5ms);
    constexpr auto period = 20ms;  // 50 Hz control task.

    auto next_release = steady_clock::now();
    for (int cycle = 0; cycle < 10; ++cycle) {
        next_release += period;
        const auto now = steady_clock::now();
        gateway.publish({now, {now, 22.0, 0.0, 0.0, 0.0, 0.12, 0.01, false, true, true, true}, {30.0, -6.0, 0.9, true}, {0.12, 0.01, 0.9, true}});
        if (runtime.run_cycle(now, duration<double>(period).count())) {
            if (const auto command = gateway.last_command()) {
                std::cout << "cycle=" << cycle << " accel=" << command->requested_acceleration_mps2
                          << " steering=" << command->requested_steering_angle_rad << " aeb=" << command->aeb_request << '\n';
            }
        }
        std::this_thread::sleep_until(next_release);
    }
}
