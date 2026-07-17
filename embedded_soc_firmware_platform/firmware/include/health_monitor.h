#ifndef FIRMWARE_HEALTH_MONITOR_H
#define FIRMWARE_HEALTH_MONITOR_H

#include "types.h"
#include <vector>
#include <map>

namespace firmware {

class HealthMonitor {
public:
    HealthMonitor();

    // Monitoring operations
    void update_cpu_temperature(int32 temp_c);
    void update_memory_usage(uint32 percent);
    void update_device_health(const std::string& subsystem, bool healthy);
    void record_security_event(const std::string& event);
    void record_power_state_change(PowerState state);

    // Health queries
    HealthStatus get_current_health() const;
    int32 get_cpu_temperature() const;
    uint32 get_memory_usage() const;
    bool is_subsystem_healthy(const std::string& subsystem) const;

    // Health history
    std::vector<HealthStatus> get_health_history() const;
    std::vector<std::string> get_security_events() const;
    std::vector<std::string> get_power_events() const;

    // Health reports
    std::string generate_health_report() const;
    std::vector<std::string> get_warnings() const;
    std::vector<std::string> get_critical_alerts() const;

    // Thresholds
    void set_temperature_thresholds(const TemperatureThresholds& thresholds);
    TemperatureThresholds get_temperature_thresholds() const;

private:
    HealthStatus current_health_;
    std::vector<HealthStatus> health_history_;
    std::vector<std::string> security_events_;
    std::vector<std::string> power_events_;
    std::map<std::string, bool> subsystem_health_;
    TemperatureThresholds temp_thresholds_;

    void check_thresholds();
};

} // namespace firmware

#endif // FIRMWARE_HEALTH_MONITOR_H
