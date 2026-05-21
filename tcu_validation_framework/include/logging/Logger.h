/**
 * @file Logger.h
 * @brief Multi-level, thread-safe logging system built on spdlog.
 *
 * Features:
 *   - Console + rotating file sinks
 *   - Binary (compact) log sink for post-analysis
 *   - Module-scoped loggers (each module gets its own named logger)
 *   - Crash-safe: flush-on-every-write option for debug builds
 *   - Timestamp synchronisation (UTC, µs precision)
 */

#pragma once

#include <memory>
#include <string>
#include <mutex>
#include <unordered_map>

// Forward declaration to avoid including spdlog in every TU
namespace spdlog { class logger; }

namespace tcu::logging {

enum class LogLevel : uint8_t {
    TRACE = 0,
    DEBUG,
    INFO,
    WARN,
    ERROR,
    CRITICAL,
    OFF,
};

/**
 * @brief Logger configuration.
 */
struct LogConfig {
    std::string log_dir{"logs"};                  ///< Output directory
    std::string base_filename{"tcu_validator"};   ///< Base log file name
    size_t      max_file_size_mb{10};             ///< Rotate when file exceeds this
    size_t      max_files{10};                    ///< Max rotated files to keep
    LogLevel    console_level{LogLevel::INFO};    ///< Minimum level for console output
    LogLevel    file_level{LogLevel::DEBUG};      ///< Minimum level for file output
    bool        flush_on_write{false};            ///< Flush after every write (slow but safe)
    bool        enable_binary_log{false};         ///< Enable compact binary log
    std::string pattern{"%Y-%m-%d %H:%M:%S.%e [%^%l%$] [%n] %v"}; ///< spdlog pattern
};

/**
 * @brief Central logger registry.
 *
 * Usage:
 * @code
 *   Logger::init(cfg);
 *   auto log = Logger::get("can");
 *   log->info("CAN socket opened on {}", iface);
 *   log->error("Failed to transmit frame: {}", strerror(errno));
 * @endcode
 */
class Logger {
public:
    Logger(const Logger&)            = delete;
    Logger& operator=(const Logger&) = delete;

    /**
     * @brief Initialise the logging system (call once at startup).
     */
    static bool init(const LogConfig& cfg);

    /**
     * @brief Shutdown the logging system and flush all sinks.
     */
    static void shutdown();

    /**
     * @brief Get or create a named module logger.
     */
    static std::shared_ptr<spdlog::logger> get(const std::string& name);

    /**
     * @brief Set log level for all loggers.
     */
    static void set_level(LogLevel level);

    /**
     * @brief Flush all loggers immediately.
     */
    static void flush_all();

    /**
     * @brief Returns true if logging system has been initialised.
     */
    static bool is_initialized() noexcept;

private:
    Logger() = default;

    static std::mutex                                                  s_mutex;
    static std::unordered_map<std::string, std::shared_ptr<spdlog::logger>> s_loggers;
    static LogConfig                                                   s_config;
    static bool                                                        s_initialized;
};

/**
 * @brief RAII helper for timing blocks.
 *
 * Usage:
 * @code
 *   {
 *       ScopedTimer t("Flash operation", Logger::get("firmware"));
 *       // ... flash ...
 *   } // logs "Flash operation took 3241 ms"
 * @endcode
 */
class ScopedTimer {
public:
    explicit ScopedTimer(std::string name, std::shared_ptr<spdlog::logger> logger);
    ~ScopedTimer();
private:
    std::string                        m_name;
    std::shared_ptr<spdlog::logger>    m_logger;
    std::chrono::steady_clock::time_point m_start;
};

} // namespace tcu::logging
