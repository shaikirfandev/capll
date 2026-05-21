/**
 * @file Logger.cpp
 */
#include "Logger.hpp"
#include <cstdio>
#include <ctime>
#include <chrono>

namespace fms {

static const char* level_str(LogLevel l) {
    switch (l) {
        case LogLevel::TRACE:    return "TRACE";
        case LogLevel::DEBUG:    return "DEBUG";
        case LogLevel::INFO:     return "INFO ";
        case LogLevel::NOTICE:   return "NOTCE";
        case LogLevel::WARN:     return "WARN ";
        case LogLevel::ERROR:    return "ERROR";
        case LogLevel::CRITICAL: return "CRIT ";
        default:                 return "OFF  ";
    }
}

Logger& Logger::get() {
    static Logger instance;
    return instance;
}

FmsError Logger::init(const char* /*log_file*/, LogLevel min_level) noexcept {
    min_level_ = min_level;
    return FmsError::OK;
}

void Logger::log(LogLevel level, const char* subsys, const char* msg) noexcept {
    if (level < min_level_) return;
    auto now = std::chrono::steady_clock::now().time_since_epoch();
    auto ms  = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
    std::printf("[%lld ms][%s][%s] %s\n",
                static_cast<long long>(ms), level_str(level), subsys, msg);
}

}  // namespace fms
