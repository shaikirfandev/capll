/**
 * @file Logger.hpp
 * @brief FMS logger — lightweight, no dynamic allocation
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include <cstdarg>

namespace fms {

enum class LogLevel : uint8_t {
    TRACE = 0, DEBUG, INFO, NOTICE, WARN, ERROR, CRITICAL, OFF
};

class Logger {
public:
    static Logger& get();
    FmsError init(const char* log_file, LogLevel min_level) noexcept;
    void log(LogLevel level, const char* subsys, const char* msg) noexcept;
    [[nodiscard]] LogLevel min_level() const noexcept { return min_level_; }
private:
    Logger() = default;
    LogLevel min_level_{LogLevel::INFO};
};

}  // namespace fms

#define FMS_LOG(lvl, subsys, msg) \
    fms::Logger::get().log(fms::LogLevel::lvl, subsys, msg)
#define FMS_LOG_INFO(s, m)  FMS_LOG(INFO,  s, m)
#define FMS_LOG_WARN(s, m)  FMS_LOG(WARN,  s, m)
#define FMS_LOG_ERROR(s, m) FMS_LOG(ERROR, s, m)
#define FMS_LOG_DEBUG(s, m) FMS_LOG(DEBUG, s, m)
#define FMS_LOG_CRIT(s, m)  FMS_LOG(CRITICAL, s, m)
