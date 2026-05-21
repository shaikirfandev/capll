/**
 * @file Watchdog.cpp
 */
#include "Watchdog.hpp"

using namespace std::chrono;

namespace fms::safety {

FmsError Watchdog::init(uint32_t timeout_ms) noexcept {
    timeout_ms_ = timeout_ms;
    last_kick_  = steady_clock::now();
    return FmsError::OK;
}

void Watchdog::kick() noexcept {
    last_kick_ = steady_clock::now();
}

bool Watchdog::is_expired() const noexcept {
    auto elapsed = duration_cast<milliseconds>(steady_clock::now() - last_kick_).count();
    return elapsed > static_cast<int64_t>(timeout_ms_);
}

SystemStatus Watchdog::get_status() const noexcept {
    return is_expired() ? SystemStatus::FAILED : SystemStatus::NORMAL;
}

}  // namespace fms::safety
