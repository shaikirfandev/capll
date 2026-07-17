#include "power_manager.h"
#include "logger.h"
#include <thread>

namespace firmware {

PowerManager::PowerManager()
    : current_state_(PowerState::S0),
      previous_state_(PowerState::S0),
      recovery_success_count_(0),
      recovery_total_count_(0) {
}

Status PowerManager::set_power_state(PowerState state) {
    LOG_INFO("PowerManager", "Setting power state to S" + std::to_string(static_cast<int>(state)));
    
    previous_state_ = current_state_;
    last_state_change_ = std::chrono::high_resolution_clock::now();
    
    Status result = transition_to_state(state);
    
    if (result == Status::SUCCESS) {
        PowerMetrics metric;
        metric.previous_state = previous_state_;
        metric.current_state = state;
        metric.state_change_time = last_state_change_;
        metric.transition_time_ms = 0;
        metric.transition_successful = true;
        power_events_.push_back(metric);
    }
    
    return result;
}

PowerState PowerManager::get_power_state() const {
    return current_state_;
}

Status PowerManager::suspend() {
    LOG_INFO("PowerManager", "Suspending system to S3");
    return set_power_state(PowerState::S3);
}

Status PowerManager::resume() {
    LOG_INFO("PowerManager", "Resuming from suspend state");
    return set_power_state(PowerState::S0);
}

Status PowerManager::hibernate() {
    LOG_INFO("PowerManager", "Entering hibernation S4");
    return set_power_state(PowerState::S4);
}

Status PowerManager::wake_on_lan() {
    LOG_INFO("PowerManager", "Waking system via LAN");
    
    if (current_state_ != PowerState::S3 && current_state_ != PowerState::S4) {
        LOG_WARNING("PowerManager", "System not in sleep state, cannot wake");
        return Status::INVALID_PARAM;
    }
    
    return resume();
}

Status PowerManager::power_loss_recovery() {
    LOG_INFO("PowerManager", "Executing power loss recovery");
    recovery_total_count_++;
    
    // Simulate recovery
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    recovery_success_count_++;
    return Status::SUCCESS;
}

PowerMetrics PowerManager::get_power_metrics() const {
    if (power_events_.empty()) {
        PowerMetrics metric;
        metric.current_state = current_state_;
        metric.transition_time_ms = 0;
        metric.wake_latency_ms = 0;
        metric.transition_successful = true;
        return metric;
    }
    
    return power_events_.back();
}

uint32 PowerManager::get_state_transition_time(PowerState from, PowerState to) const {
    for (const auto& event : power_events_) {
        if (event.previous_state == from && event.current_state == to) {
            return event.transition_time_ms;
        }
    }
    return 0;
}

uint32 PowerManager::get_wake_latency() const {
    uint32 total = 0;
    for (const auto& event : power_events_) {
        total += event.wake_latency_ms;
    }
    return total / (power_events_.empty() ? 1 : power_events_.size());
}

uint32 PowerManager::get_recovery_success_rate() const {
    if (recovery_total_count_ == 0) return 0;
    return (recovery_success_count_ * 100) / recovery_total_count_;
}

std::vector<PowerMetrics> PowerManager::get_power_event_log() const {
    return power_events_;
}

Status PowerManager::transition_to_state(PowerState state) {
    if (state == current_state_) {
        return Status::SUCCESS;
    }
    
    // Validate transition
    switch (state) {
        case PowerState::S0:  // Working
            // Can transition from any state
            break;
        case PowerState::S1:  // Light sleep
            if (current_state_ != PowerState::S0) return Status::INVALID_PARAM;
            break;
        case PowerState::S3:  // Deep sleep
            if (current_state_ != PowerState::S0 && current_state_ != PowerState::S1) 
                return Status::INVALID_PARAM;
            break;
        case PowerState::S4:  // Hibernation
            if (current_state_ != PowerState::S0) return Status::INVALID_PARAM;
            break;
        case PowerState::S5:  // Soft off
            // Can transition from any state
            break;
        case PowerState::S6:  // Hard off
            // Can transition from any state
            break;
        default:
            return Status::INVALID_PARAM;
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    current_state_ = state;
    
    LOG_INFO("PowerManager", "Successfully transitioned to S" + std::to_string(static_cast<int>(state)));
    
    return Status::SUCCESS;
}

} // namespace firmware
