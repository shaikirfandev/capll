#ifndef FIRMWARE_POWER_MANAGER_H
#define FIRMWARE_POWER_MANAGER_H

#include "types.h"
#include <chrono>

namespace firmware {

class PowerManager {
public:
    PowerManager();

    // Power state transitions
    Status set_power_state(PowerState state);
    PowerState get_power_state() const;

    // Power operations
    Status suspend();
    Status resume();
    Status hibernate();
    Status wake_on_lan();
    Status power_loss_recovery();

    // Measurements
    PowerMetrics get_power_metrics() const;
    uint32 get_state_transition_time(PowerState from, PowerState to) const;
    uint32 get_wake_latency() const;
    uint32 get_recovery_success_rate() const;

    // Power events
    std::vector<PowerMetrics> get_power_event_log() const;

private:
    PowerState current_state_;
    PowerState previous_state_;
    std::chrono::high_resolution_clock::time_point last_state_change_;
    std::vector<PowerMetrics> power_events_;
    uint32 recovery_success_count_;
    uint32 recovery_total_count_;

    Status transition_to_state(PowerState state);
};

} // namespace firmware

#endif // FIRMWARE_POWER_MANAGER_H
