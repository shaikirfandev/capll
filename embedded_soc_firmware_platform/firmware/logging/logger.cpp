#include "logger.h"
#include <iostream>
#include <iomanip>

namespace firmware {

Logger& Logger::getInstance() {
    static Logger instance;
    return instance;
}

Logger::Logger()
    : format_(LogFormat::JSON),
      min_log_level_(LogLevel::DEBUG),
      error_count_(0),
      warning_count_(0) {
}

void Logger::initialize(const std::string& log_file, LogFormat format) {
    std::lock_guard<std::mutex> lock(log_mutex_);
    log_file_.open(log_file, std::ios::app);
    format_ = format;
}

void Logger::log(LogLevel level, const std::string& component, const std::string& message) {
    std::lock_guard<std::mutex> lock(log_mutex_);
    
    if (level < min_log_level_) return;

    if (level == LogLevel::ERROR) error_count_++;
    if (level == LogLevel::WARNING) warning_count_++;

    write_log(level, component, message);
}

void Logger::write_log(LogLevel level, const std::string& component, const std::string& message) {
    std::string timestamp = get_timestamp();
    std::string level_str = level_to_string(level);

    if (format_ == LogFormat::JSON) {
        json log_entry;
        log_entry["timestamp"] = timestamp;
        log_entry["level"] = level_str;
        log_entry["component"] = component;
        log_entry["message"] = message;
        logs_json_.push_back(log_entry);
        
        if (log_file_.is_open()) {
            log_file_ << log_entry.dump() << std::endl;
        }
    } else if (format_ == LogFormat::TEXT) {
        std::string log_text = "[" + timestamp + "] [" + level_str + "] [" + component + "] " + message;
        logs_text_.push_back(log_text);
        
        if (log_file_.is_open()) {
            log_file_ << log_text << std::endl;
        }
    }

    std::cout << "LOG: " << level_str << " [" << component << "] " << message << std::endl;
}

void Logger::log_event(EventType event, const std::string& component, const std::string& details) {
    std::string event_name;
    switch (event) {
        case EventType::BOOT_START: event_name = "BOOT_START"; break;
        case EventType::BOOT_PHASE_ENTRY: event_name = "BOOT_PHASE_ENTRY"; break;
        case EventType::BOOT_PHASE_EXIT: event_name = "BOOT_PHASE_EXIT"; break;
        case EventType::POWER_STATE_CHANGE: event_name = "POWER_STATE_CHANGE"; break;
        case EventType::MEMORY_INIT: event_name = "MEMORY_INIT"; break;
        case EventType::SECURITY_CHECK: event_name = "SECURITY_CHECK"; break;
        case EventType::DEVICE_ENUMERATION: event_name = "DEVICE_ENUMERATION"; break;
        case EventType::ERROR_DETECTED: event_name = "ERROR_DETECTED"; break;
        case EventType::RECOVERY_START: event_name = "RECOVERY_START"; break;
        case EventType::SYSTEM_SHUTDOWN: event_name = "SYSTEM_SHUTDOWN"; break;
        case EventType::HEALTH_STATUS: event_name = "HEALTH_STATUS"; break;
    }
    
    log(LogLevel::INFO, component, event_name + ": " + details);
}

void Logger::log_security_event(const SecurityEvent& event) {
    json log_entry;
    log_entry["type"] = "SECURITY_EVENT";
    log_entry["event_type"] = event.event_type;
    log_entry["description"] = event.description;
    log_entry["timestamp"] = get_timestamp();
    log_entry["result"] = (event.result == Status::SUCCESS ? "SUCCESS" : "FAILURE");
    log_entry["details"] = event.details;
    
    logs_json_.push_back(log_entry);
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.dump() << std::endl;
    }
}

void Logger::log_boot_metrics(const BootMetrics& metrics) {
    json log_entry;
    log_entry["type"] = "BOOT_METRICS";
    log_entry["total_boot_time_ms"] = metrics.total_boot_time_ms;
    log_entry["sec_phase_time_ms"] = metrics.sec_phase_time_ms;
    log_entry["pei_phase_time_ms"] = metrics.pei_phase_time_ms;
    log_entry["dxe_phase_time_ms"] = metrics.dxe_phase_time_ms;
    log_entry["bds_phase_time_ms"] = metrics.bds_phase_time_ms;
    log_entry["os_load_time_ms"] = metrics.os_load_time_ms;
    log_entry["boot_successful"] = metrics.boot_successful;
    
    logs_json_.push_back(log_entry);
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.dump() << std::endl;
    }
}

void Logger::log_power_metrics(const PowerMetrics& metrics) {
    json log_entry;
    log_entry["type"] = "POWER_METRICS";
    log_entry["transition_time_ms"] = metrics.transition_time_ms;
    log_entry["wake_latency_ms"] = metrics.wake_latency_ms;
    log_entry["transition_successful"] = metrics.transition_successful;
    
    logs_json_.push_back(log_entry);
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.dump() << std::endl;
    }
}

void Logger::log_health_status(const HealthStatus& status) {
    json log_entry;
    log_entry["type"] = "HEALTH_STATUS";
    log_entry["cpu_temp_c"] = status.cpu_temp_c;
    log_entry["memory_usage_percent"] = status.memory_usage_percent;
    log_entry["pcie_devices_healthy"] = status.pcie_devices_healthy;
    log_entry["usb_devices_healthy"] = status.usb_devices_healthy;
    log_entry["security_status_ok"] = status.security_status_ok;
    log_entry["overall_status"] = status.overall_status;
    
    logs_json_.push_back(log_entry);
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.dump() << std::endl;
    }
}

void Logger::log_device_enumeration(const std::string& subsystem, const std::vector<DeviceInfo>& devices) {
    json log_entry;
    log_entry["type"] = "DEVICE_ENUMERATION";
    log_entry["subsystem"] = subsystem;
    log_entry["device_count"] = devices.size();
    
    json devices_array = json::array();
    for (const auto& dev : devices) {
        json dev_entry;
        dev_entry["vendor_id"] = dev.vendor_id;
        dev_entry["device_id"] = dev.device_id;
        dev_entry["name"] = dev.name;
        devices_array.push_back(dev_entry);
    }
    log_entry["devices"] = devices_array;
    
    logs_json_.push_back(log_entry);
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.dump() << std::endl;
    }
}

std::vector<std::string> Logger::get_logs() const {
    std::lock_guard<std::mutex> lock(log_mutex_);
    return logs_text_;
}

json Logger::get_logs_json() const {
    std::lock_guard<std::mutex> lock(log_mutex_);
    return logs_json_;
}

void Logger::flush_to_file() {
    std::lock_guard<std::mutex> lock(log_mutex_);
    if (log_file_.is_open()) {
        log_file_.flush();
    }
}

void Logger::set_log_level(LogLevel level) {
    std::lock_guard<std::mutex> lock(log_mutex_);
    min_log_level_ = level;
}

uint32 Logger::get_error_count() const {
    std::lock_guard<std::mutex> lock(log_mutex_);
    return error_count_;
}

uint32 Logger::get_warning_count() const {
    std::lock_guard<std::mutex> lock(log_mutex_);
    return warning_count_;
}

std::string Logger::level_to_string(LogLevel level) const {
    switch (level) {
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO: return "INFO";
        case LogLevel::WARNING: return "WARNING";
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::CRITICAL: return "CRITICAL";
        default: return "UNKNOWN";
    }
}

std::string Logger::get_timestamp() const {
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
    
    std::ostringstream oss;
    oss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S") 
        << '.' << std::setfill('0') << std::setw(3) << ms.count();
    return oss.str();
}

} // namespace firmware
