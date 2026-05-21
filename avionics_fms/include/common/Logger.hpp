/**
 * @file Logger.hpp
 * @brief Avionics-grade logger — circular buffer NVM backing, DO-178C safe
 *
 * Thread-safe. NVM backing for post-flight analysis (similar to DFDR data).
 * Log levels mapped to ARINC 429 SSM status for avionics integration.
 */
#pragma once
#include <cstdint>
#include <cstddef>
#include <string_view>

namespace fms {

enum class LogLevel : uint8_t {
    TRACE   = 0U,
    DEBUG   = 1U,
    INFO    = 2U,
    NOTICE  = 3U,  // Normal but significant
    WARN    = 4U,
    ERROR   = 5U,
    CRITICAL = 6U,  // System fault — always logged to NVM
    OFF     = 7U,
};

class Logger {
public:
    static Logger &get();

    void init(const char *log_file, LogLevel min_level = LogLevel::INFO);
    void shutdown();
    void set_level(LogLevel level);

    void log(LogLevel level, const char *subsystem,
             const char *fmt, ...) __attribute__((format(printf, 4, 5)));

    /** Flush NVM buffer — call before power-down */
    void flush_nvm();

private:
    Logger() = default;
    ~Logger() = default;
    Logger(const Logger &) = delete;
    Logger &operator=(const Logger &) = delete;

    struct Impl;
    Impl *impl_{nullptr};
};

// ── Convenience macros ────────────────────────────────────────────────────────
#define FMS_LOG_DEBUG(SYS, fmt, ...)   ::fms::Logger::get().log(::fms::LogLevel::DEBUG,  SYS, fmt, ##__VA_ARGS__)
#define FMS_LOG_INFO(SYS, fmt, ...)    ::fms::Logger::get().log(::fms::LogLevel::INFO,   SYS, fmt, ##__VA_ARGS__)
#define FMS_LOG_NOTICE(SYS, fmt, ...)  ::fms::Logger::get().log(::fms::LogLevel::NOTICE, SYS, fmt, ##__VA_ARGS__)
#define FMS_LOG_WARN(SYS, fmt, ...)    ::fms::Logger::get().log(::fms::LogLevel::WARN,   SYS, fmt, ##__VA_ARGS__)
#define FMS_LOG_ERROR(SYS, fmt, ...)   ::fms::Logger::get().log(::fms::LogLevel::ERROR,  SYS, fmt, ##__VA_ARGS__)
#define FMS_LOG_CRITICAL(SYS, fmt, ...) ::fms::Logger::get().log(::fms::LogLevel::CRITICAL, SYS, fmt, ##__VA_ARGS__)

}  // namespace fms
