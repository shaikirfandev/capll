/**
 * @file logger.cpp
 * @brief Thread-safe logger implementation.
 */

#include "logger.hpp"

#include <chrono>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>

namespace adas {
namespace diag {

const char* logLevelToString(LogLevel level) {
    switch (level) {
        case LogLevel::TRACE:   return "TRACE";
        case LogLevel::DEBUG:   return "DEBUG";
        case LogLevel::INFO:    return "INFO ";
        case LogLevel::WARNING: return "WARN ";
        case LogLevel::ERROR:   return "ERROR";
        case LogLevel::FATAL:   return "FATAL";
        default:                return "?????";
    }
}

static uint64_t nowUs() {
    using namespace std::chrono;
    return duration_cast<microseconds>(
        steady_clock::now().time_since_epoch()).count();
}

// ─── Singleton ────────────────────────────────────────────────────────────────

Logger& Logger::instance() {
    static Logger inst;
    return inst;
}

Logger::Logger() = default;

Logger::~Logger() { stop(); }

void Logger::setLevel(LogLevel level) {
    min_level_ = level;
}

void Logger::setOutputFile(const std::string& path) {
    output_file_ = path;
}

// ─── RT-safe log() ───────────────────────────────────────────────────────────

void Logger::log(LogLevel level, const char* module, const char* msg) {
    if (level < min_level_) return;

    const uint64_t tail = tail_.load(std::memory_order_relaxed);
    const uint64_t next = tail + 1;

    // Drop if full (never block in RT path)
    if (next - head_.load(std::memory_order_acquire) > kCapacity) {
        return;
    }

    LogEntry& entry    = ring_[tail & kMask];
    entry.level        = level;
    entry.timestamp_us = nowUs();
    std::strncpy(entry.module,  module, sizeof(entry.module)  - 1);
    std::strncpy(entry.message, msg,    sizeof(entry.message) - 1);
    entry.module[sizeof(entry.module) - 1]   = '\0';
    entry.message[sizeof(entry.message) - 1] = '\0';

    tail_.store(next, std::memory_order_release);
}

// ─── Flush loop (non-RT background thread) ───────────────────────────────────

void Logger::start() {
    if (running_.exchange(true)) return;
    flush_thread_ = std::thread([this] { flushLoop(); });
}

void Logger::stop() {
    running_.store(false);
    if (flush_thread_.joinable()) flush_thread_.join();
}

void Logger::flushLoop() {
    std::ofstream file;
    if (!output_file_.empty()) {
        file.open(output_file_, std::ios::app);
    }

    while (running_.load(std::memory_order_relaxed)) {
        const uint64_t head = head_.load(std::memory_order_relaxed);
        const uint64_t tail = tail_.load(std::memory_order_acquire);

        for (uint64_t i = head; i != tail; ++i) {
            const LogEntry& e = ring_[i & kMask];

            // Format: [TIMESTAMP_US] [LEVEL] [MODULE] message
            char line[256];
            snprintf(line, sizeof(line), "[%12llu] [%s] [%-10s] %s\n",
                     static_cast<unsigned long long>(e.timestamp_us),
                     logLevelToString(e.level),
                     e.module,
                     e.message);

            std::fputs(line, stdout);
            if (file.is_open()) {
                file << line;
            }

            // FATAL → flush immediately
            if (e.level == LogLevel::FATAL) {
                std::fflush(stdout);
                if (file.is_open()) file.flush();
            }
        }
        head_.store(tail, std::memory_order_release);

        // Sleep 1 ms between flushes (non-RT thread, can sleep)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

}  // namespace diag
}  // namespace adas
