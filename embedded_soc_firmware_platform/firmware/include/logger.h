#ifndef FIRMWARE_LOGGER_H
#define FIRMWARE_LOGGER_H

#include "types.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <mutex>
#include <vector>
#include <nlohmann/json.hpp>

namespace firmware {

using json = nlohmann::json;

enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    CRITICAL = 4,
};

enum class LogFormat {
    TEXT,
    JSON,
    CSV,
};

class Logger {
public:
    static Logger& getInstance();

    // Initialize logger
    void initialize(const std::string& log_file, LogFormat format = LogFormat::JSON);

    // Logging methods
    void log(LogLevel level, const std::string& component, const std::string& message);
    void log_event(EventType event, const std::string& component, const std::string& details);
    void log_security_event(const SecurityEvent& event);
    void log_boot_metrics(const BootMetrics& metrics);
    void log_power_metrics(const PowerMetrics& metrics);
    void log_health_status(const HealthStatus& status);
    void log_device_enumeration(const std::string& subsystem, const std::vector<DeviceInfo>& devices);

    // Get logs
    std::vector<std::string> get_logs() const;
    json get_logs_json() const;

    // Flush to file
    void flush_to_file();

    // Set log level
    void set_log_level(LogLevel level);

    // Statistics
    uint32 get_error_count() const;
    uint32 get_warning_count() const;

private:
    Logger();
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    void write_log(LogLevel level, const std::string& component, const std::string& message);
    std::string level_to_string(LogLevel level) const;
    std::string get_timestamp() const;

    mutable std::mutex log_mutex_;
    std::vector<std::string> logs_text_;
    std::vector<json> logs_json_;
    std::ofstream log_file_;
    LogFormat format_;
    LogLevel min_log_level_;
    uint32 error_count_;
    uint32 warning_count_;
};

// Convenience macros
#define LOG_DEBUG(component, msg) Logger::getInstance().log(LogLevel::DEBUG, component, msg)
#define LOG_INFO(component, msg) Logger::getInstance().log(LogLevel::INFO, component, msg)
#define LOG_WARNING(component, msg) Logger::getInstance().log(LogLevel::WARNING, component, msg)
#define LOG_ERROR(component, msg) Logger::getInstance().log(LogLevel::ERROR, component, msg)
#define LOG_CRITICAL(component, msg) Logger::getInstance().log(LogLevel::CRITICAL, component, msg)

} // namespace firmware

#endif // FIRMWARE_LOGGER_H
