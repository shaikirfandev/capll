#include "health_monitor.h"
#include "logger.h"

namespace firmware {

HealthMonitor::HealthMonitor() {
    current_health_.cpu_temp_c = 45;
    current_health_.memory_usage_percent = 50;
    current_health_.pcie_devices_healthy = 1;
    current_health_.usb_devices_healthy = 1;
    current_health_.security_status_ok = 1;
    current_health_.overall_status = "OK";
    
    temp_thresholds_.warning_temp_c = 80;
    temp_thresholds_.critical_temp_c = 95;
    temp_thresholds_.shutdown_temp_c = 105;
}

void HealthMonitor::update_cpu_temperature(int32 temp_c) {
    current_health_.cpu_temp_c = temp_c;
    health_history_.push_back(current_health_);
    
    LOG_DEBUG("HealthMonitor", "CPU temperature updated: " + std::to_string(temp_c) + "C");
    
    check_thresholds();
}

void HealthMonitor::update_memory_usage(uint32 percent) {
    current_health_.memory_usage_percent = percent;
    
    LOG_DEBUG("HealthMonitor", "Memory usage updated: " + std::to_string(percent) + "%");
}

void HealthMonitor::update_device_health(const std::string& subsystem, bool healthy) {
    subsystem_health_[subsystem] = healthy;
    
    LOG_DEBUG("HealthMonitor", "Device health updated - " + subsystem + ": " + 
              (healthy ? "HEALTHY" : "UNHEALTHY"));
    
    if (subsystem == "pcie") {
        current_health_.pcie_devices_healthy = healthy ? 1 : 0;
    } else if (subsystem == "usb") {
        current_health_.usb_devices_healthy = healthy ? 1 : 0;
    }
}

void HealthMonitor::record_security_event(const std::string& event) {
    security_events_.push_back(event);
    
    LOG_INFO("HealthMonitor", "Security event recorded: " + event);
}

void HealthMonitor::record_power_state_change(PowerState state) {
    power_events_.push_back("S" + std::to_string(static_cast<int>(state)));
    
    LOG_DEBUG("HealthMonitor", "Power state change recorded: S" + std::to_string(static_cast<int>(state)));
}

HealthStatus HealthMonitor::get_current_health() const {
    return current_health_;
}

int32 HealthMonitor::get_cpu_temperature() const {
    return current_health_.cpu_temp_c;
}

uint32 HealthMonitor::get_memory_usage() const {
    return current_health_.memory_usage_percent;
}

bool HealthMonitor::is_subsystem_healthy(const std::string& subsystem) const {
    if (subsystem_health_.find(subsystem) != subsystem_health_.end()) {
        return subsystem_health_.at(subsystem);
    }
    return true;
}

std::vector<HealthStatus> HealthMonitor::get_health_history() const {
    return health_history_;
}

std::vector<std::string> HealthMonitor::get_security_events() const {
    return security_events_;
}

std::vector<std::string> HealthMonitor::get_power_events() const {
    return power_events_;
}

std::string HealthMonitor::generate_health_report() const {
    std::string report = "=== System Health Report ===\n";
    report += "CPU Temperature: " + std::to_string(current_health_.cpu_temp_c) + "C\n";
    report += "Memory Usage: " + std::to_string(current_health_.memory_usage_percent) + "%\n";
    report += "PCIe Devices Health: " + std::string(current_health_.pcie_devices_healthy ? "HEALTHY" : "UNHEALTHY") + "\n";
    report += "USB Devices Health: " + std::string(current_health_.usb_devices_healthy ? "HEALTHY" : "UNHEALTHY") + "\n";
    report += "Security Status: " + std::string(current_health_.security_status_ok ? "OK" : "COMPROMISED") + "\n";
    report += "Overall Status: " + current_health_.overall_status + "\n";
    report += "=== End Report ===\n";
    return report;
}

std::vector<std::string> HealthMonitor::get_warnings() const {
    std::vector<std::string> warnings;
    
    if (current_health_.cpu_temp_c > temp_thresholds_.warning_temp_c) {
        warnings.push_back("CPU temperature exceeds warning threshold: " + 
                          std::to_string(current_health_.cpu_temp_c) + "C");
    }
    
    if (current_health_.memory_usage_percent > 90) {
        warnings.push_back("Memory usage is high: " + std::to_string(current_health_.memory_usage_percent) + "%");
    }
    
    if (!current_health_.pcie_devices_healthy) {
        warnings.push_back("PCIe subsystem unhealthy");
    }
    
    if (!current_health_.usb_devices_healthy) {
        warnings.push_back("USB subsystem unhealthy");
    }
    
    return warnings;
}

std::vector<std::string> HealthMonitor::get_critical_alerts() const {
    std::vector<std::string> alerts;
    
    if (current_health_.cpu_temp_c > temp_thresholds_.critical_temp_c) {
        alerts.push_back("CRITICAL: CPU temperature critically high: " + 
                        std::to_string(current_health_.cpu_temp_c) + "C");
    }
    
    if (current_health_.cpu_temp_c > temp_thresholds_.shutdown_temp_c) {
        alerts.push_back("CRITICAL: CPU temperature exceeds shutdown threshold - initiating shutdown!");
    }
    
    if (!current_health_.security_status_ok) {
        alerts.push_back("CRITICAL: Security compromise detected");
    }
    
    return alerts;
}

void HealthMonitor::set_temperature_thresholds(const TemperatureThresholds& thresholds) {
    temp_thresholds_ = thresholds;
    
    LOG_INFO("HealthMonitor", "Temperature thresholds updated - Warning: " + 
             std::to_string(thresholds.warning_temp_c) + "C, Critical: " + 
             std::to_string(thresholds.critical_temp_c) + "C");
}

TemperatureThresholds HealthMonitor::get_temperature_thresholds() const {
    return temp_thresholds_;
}

void HealthMonitor::check_thresholds() {
    if (current_health_.cpu_temp_c > temp_thresholds_.critical_temp_c) {
        current_health_.overall_status = "CRITICAL";
        LOG_CRITICAL("HealthMonitor", "CRITICAL: CPU temperature " + 
                     std::to_string(current_health_.cpu_temp_c) + "C exceeds critical threshold");
    } else if (current_health_.cpu_temp_c > temp_thresholds_.warning_temp_c) {
        current_health_.overall_status = "WARNING";
        LOG_WARNING("HealthMonitor", "WARNING: CPU temperature " + 
                    std::to_string(current_health_.cpu_temp_c) + "C exceeds warning threshold");
    } else {
        current_health_.overall_status = "OK";
    }
}

} // namespace firmware
