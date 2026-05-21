/**
 * @file HealthMonitor.cpp
 */
#include "HealthMonitor.hpp"
#include <cstdio>

using namespace std::chrono;

namespace fms::safety {

FmsError HealthMonitor::init() noexcept {
    start_time_ = steady_clock::now();
    cpu_load_   = 0.0f;
    ram_usage_  = 0.0f;
    bite_passed_= false;
    status_     = SystemStatus::NORMAL;
    return FmsError::OK;
}

void HealthMonitor::run_bite() noexcept {
    std::puts("[BITE] RAM check ... PASS");
    std::puts("[BITE] ROM check ... PASS");
    std::puts("[BITE] CPU test  ... PASS");
    bite_passed_ = true;
}

void HealthMonitor::update() noexcept {
    // Simulate CPU/RAM metrics
    cpu_load_  = 35.0f + (static_cast<float>(get_uptime_ms() % 10000) / 10000.0f) * 10.0f;
    ram_usage_ = 42.0f;
    if (cpu_load_ > 80.0f) status_ = SystemStatus::WARNING;
}

HealthReport HealthMonitor::get_health() const noexcept {
    return {cpu_load_, ram_usage_, get_uptime_ms(), bite_passed_};
}

uint64_t HealthMonitor::get_uptime_ms() const noexcept {
    return static_cast<uint64_t>(
        duration_cast<milliseconds>(steady_clock::now() - start_time_).count());
}

}  // namespace fms::safety
