#pragma once
/**
 * @file logger.hpp
 * @brief Thread-safe, real-time-friendly structured logger.
 *
 * DESIGN
 * ──────
 * • Lock-free SPSC queue from the RT thread to a dedicated logging thread.
 *   RT threads never block; they drop the message if the queue is full.
 * • Log thread writes to stdout and/or a file using line-buffered I/O.
 * • Supports structured fields (JSON output for Kibana/Splunk ingestion).
 *
 * LOG LEVELS
 * ──────────
 *   TRACE   – Per-cycle algorithm values (high frequency, disabled in release)
 *   DEBUG   – Diagnostic events (object detection, EKF innovations)
 *   INFO    – Normal system events (startup, mode changes)
 *   WARNING – Non-fatal anomalies (missed deadline, CAN Rx timeout)
 *   ERROR   – Recoverable faults (sensor dropout, EKF divergence)
 *   FATAL   – Unrecoverable faults (stack overflow, watchdog) → triggers safe state
 *
 * USAGE
 * ─────
 * @code
 *   auto& log = adas::diag::Logger::instance();
 *   log.setLevel(adas::diag::LogLevel::DEBUG);
 *   ADAS_LOG_INFO("FUSION", "Track {} confirmed at ({:.2f},{:.2f})", id, px, py);
 *   ADAS_LOG_ERROR("CAN", "Tx timeout on ID {:03X}", 0x200);
 * @endcode
 */

#include <array>
#include <atomic>
#include <cstdint>
#include <functional>
#include <string>
#include <thread>

namespace adas {
namespace diag {

// ─── Log level ────────────────────────────────────────────────────────────────

enum class LogLevel : uint8_t {
    TRACE   = 0,
    DEBUG   = 1,
    INFO    = 2,
    WARNING = 3,
    ERROR   = 4,
    FATAL   = 5,
};

const char* logLevelToString(LogLevel level);

// ─── Log entry ────────────────────────────────────────────────────────────────

struct LogEntry {
    LogLevel level;
    uint64_t timestamp_us;
    char     module[16];
    char     message[192];   ///< Fixed-size to avoid heap in RT path
};

static_assert(sizeof(LogEntry) <= 256, "LogEntry must fit in cache line pairs");

// ─── Logger ───────────────────────────────────────────────────────────────────

/**
 * @class Logger
 * @brief Singleton structured logger with lock-free RT ingestion.
 */
class Logger {
public:
    static Logger& instance();

    // Non-copyable singleton
    Logger(const Logger&)            = delete;
    Logger& operator=(const Logger&) = delete;

    void setLevel(LogLevel level);
    void setOutputFile(const std::string& path);

    /**
     * @brief Enqueue a log message (lock-free, from any thread).
     *        If the ring buffer is full, the message is silently dropped.
     * @param level   Severity level
     * @param module  Module name (max 15 chars)
     * @param msg     Already-formatted message string
     */
    void log(LogLevel level, const char* module, const char* msg);

    void start();
    void stop();

private:
    Logger();
    ~Logger();

    void flushLoop();

    // Lock-free SPSC ring buffer (capacity = 1024 entries)
    static constexpr std::size_t kCapacity = 1024;
    static constexpr std::size_t kMask     = kCapacity - 1;

    alignas(64) std::atomic<uint64_t> head_{0};
    alignas(64) std::atomic<uint64_t> tail_{0};
    alignas(64) std::array<LogEntry, kCapacity> ring_{};

    LogLevel             min_level_{LogLevel::INFO};
    std::string          output_file_;
    std::thread          flush_thread_;
    std::atomic<bool>    running_{false};
};

}  // namespace diag
}  // namespace adas

// ─── Convenience macros ───────────────────────────────────────────────────────

#define ADAS_LOG(level, module, ...)                                    \
    do {                                                                 \
        char _msg_buf[192];                                              \
        snprintf(_msg_buf, sizeof(_msg_buf), __VA_ARGS__);              \
        adas::diag::Logger::instance().log(level, module, _msg_buf);   \
    } while(0)

#define ADAS_LOG_TRACE(mod, ...)   ADAS_LOG(adas::diag::LogLevel::TRACE,   mod, __VA_ARGS__)
#define ADAS_LOG_DEBUG(mod, ...)   ADAS_LOG(adas::diag::LogLevel::DEBUG,   mod, __VA_ARGS__)
#define ADAS_LOG_INFO(mod, ...)    ADAS_LOG(adas::diag::LogLevel::INFO,    mod, __VA_ARGS__)
#define ADAS_LOG_WARN(mod, ...)    ADAS_LOG(adas::diag::LogLevel::WARNING, mod, __VA_ARGS__)
#define ADAS_LOG_ERROR(mod, ...)   ADAS_LOG(adas::diag::LogLevel::ERROR,   mod, __VA_ARGS__)
#define ADAS_LOG_FATAL(mod, ...)   ADAS_LOG(adas::diag::LogLevel::FATAL,   mod, __VA_ARGS__)
