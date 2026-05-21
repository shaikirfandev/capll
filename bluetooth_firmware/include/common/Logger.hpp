/**
 * @file Logger.hpp
 * @brief Automotive-grade logging abstraction backed by spdlog
 *
 * Provides a thread-safe singleton logger with automotive component tagging,
 * log level control, and multi-sink support (console + rotating file).
 *
 * Usage:
 *   bt::Logger::get().info("[BT][ADV] Advertising started, addr={}", addr_str);
 *   BT_LOG_INFO("BleAdvertiser", "started interval={}ms", params.interval_min_ms);
 */

#pragma once

#include <memory>
#include <string>
#include <string_view>

// Forward-declare spdlog to avoid pulling full header into every TU
namespace spdlog { class logger; }

namespace bt {

/**
 * @class Logger
 * @brief Singleton logger for the Bluetooth firmware stack
 *
 * Backed by spdlog with:
 *  - Console sink (coloured, for development)
 *  - Rotating file sink (bt_firmware.log, 10MB x 5 files)
 *  - Automotive format: [HH:MM:SS.mmm] [LEVEL] [COMPONENT] message
 */
class Logger {
public:
    enum class Level : int {
        TRACE    = 0,
        DEBUG    = 1,
        INFO     = 2,
        WARN     = 3,
        ERR      = 4,
        CRITICAL = 5,
        OFF      = 6,
    };

    // Singleton access
    static Logger &get();

    // Non-copyable, non-movable
    Logger(const Logger &) = delete;
    Logger &operator=(const Logger &) = delete;
    Logger(Logger &&)      = delete;
    Logger &operator=(Logger &&) = delete;

    /**
     * @brief Initialise logger with console + file sinks.
     * @param log_file  Path to rotating log file (e.g. "/var/log/bt_firmware.log")
     * @param level     Initial log level
     */
    void init(std::string_view log_file = "bt_firmware.log",
              Level level = Level::DEBUG);

    void set_level(Level level);
    Level get_level() const;
    void flush();

    // ── Core log methods ─────────────────────────────────────────────────────
    template<typename... Args>
    void trace(std::string_view fmt, Args &&...args);

    template<typename... Args>
    void debug(std::string_view fmt, Args &&...args);

    template<typename... Args>
    void info(std::string_view fmt, Args &&...args);

    template<typename... Args>
    void warn(std::string_view fmt, Args &&...args);

    template<typename... Args>
    void error(std::string_view fmt, Args &&...args);

    template<typename... Args>
    void critical(std::string_view fmt, Args &&...args);

    /// Raw access to underlying spdlog logger (for spdlog-specific features)
    std::shared_ptr<spdlog::logger> raw();

private:
    Logger();
    ~Logger();

    struct Impl;
    std::unique_ptr<Impl> impl_;
};

// ── Convenience macros ────────────────────────────────────────────────────────
// Format: [COMPONENT] message
// These are not function-like — they log with component tag prepended.
#define BT_LOG_TRACE(comp, fmt, ...)    bt::Logger::get().trace("[{}] " fmt, comp, ##__VA_ARGS__)
#define BT_LOG_DEBUG(comp, fmt, ...)    bt::Logger::get().debug("[{}] " fmt, comp, ##__VA_ARGS__)
#define BT_LOG_INFO(comp, fmt, ...)     bt::Logger::get().info("[{}] " fmt, comp, ##__VA_ARGS__)
#define BT_LOG_WARN(comp, fmt, ...)     bt::Logger::get().warn("[{}] " fmt, comp, ##__VA_ARGS__)
#define BT_LOG_ERROR(comp, fmt, ...)    bt::Logger::get().error("[{}] " fmt, comp, ##__VA_ARGS__)
#define BT_LOG_CRITICAL(comp, fmt, ...) bt::Logger::get().critical("[{}] " fmt, comp, ##__VA_ARGS__)

}  // namespace bt
