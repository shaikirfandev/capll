/**
 * @file DataBusMonitor.cpp
 */
#include "DataBusMonitor.hpp"
#include <chrono>

using namespace std::chrono;

namespace fms::comms {

FmsError DataBusMonitor::init() noexcept {
    const auto now = Clock::now();
    last_arinc429_ = now;
    last_afdx_     = now;
    last_can_      = now;
    status_        = SystemStatus::NORMAL;
    return FmsError::OK;
}

void DataBusMonitor::mark_arinc429_active() noexcept { last_arinc429_ = Clock::now(); }
void DataBusMonitor::mark_afdx_active()     noexcept { last_afdx_     = Clock::now(); }
void DataBusMonitor::mark_can_active()      noexcept { last_can_      = Clock::now(); }

static bool check_timeout(std::chrono::steady_clock::time_point tp, uint32_t ms) noexcept {
    auto elapsed = duration_cast<milliseconds>(std::chrono::steady_clock::now() - tp).count();
    return elapsed < static_cast<long long>(ms);
}

bool DataBusMonitor::is_arinc429_healthy() const noexcept { return check_timeout(last_arinc429_, TIMEOUT_MS); }
bool DataBusMonitor::is_afdx_healthy()     const noexcept { return check_timeout(last_afdx_,     TIMEOUT_MS); }
bool DataBusMonitor::is_can_healthy()      const noexcept { return check_timeout(last_can_,      TIMEOUT_MS); }

void DataBusMonitor::update() noexcept {
    status_ = (!is_arinc429_healthy() || !is_afdx_healthy())
              ? SystemStatus::WARNING : SystemStatus::NORMAL;
}

SystemStatus DataBusMonitor::get_status() const noexcept { return status_; }

}  // namespace fms::comms
