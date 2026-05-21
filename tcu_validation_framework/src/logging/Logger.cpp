/**
 * @file Logger.cpp
 * @brief spdlog-based logging subsystem — rotating file + console sinks.
 */

#include "logging/Logger.h"

#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/ansicolor_sink.h>
#include <spdlog/sinks/null_sink.h>
#include <spdlog/async.h>
#include <spdlog/async_logger.h>

#include <filesystem>
#include <stdexcept>

namespace tcu::logging {

// ============================================================
// Static state
// ============================================================

static bool                                            s_initialised = false;
static LogConfig                                       s_config;
static std::vector<spdlog::sink_ptr>                  s_sinks;
static std::unordered_map<std::string, std::shared_ptr<spdlog::logger>> s_loggers;
static std::mutex                                      s_mutex;

// ============================================================
// Init
// ============================================================

bool Logger::init(const LogConfig& cfg) {
    std::lock_guard<std::mutex> lock(s_mutex);
    if (s_initialised) { return true; }

    s_config = cfg;

    try {
        // Ensure log directory exists
        std::filesystem::create_directories(cfg.log_dir);

        // Rotating file sink
        auto file_path = cfg.log_dir + "/" + cfg.base_filename + ".log";
        auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
            file_path,
            cfg.max_file_size_bytes,
            cfg.max_files);

        file_sink->set_level(spdlog::level::trace);
        file_sink->set_pattern("[%Y-%m-%dT%H:%M:%S.%e] [%n] [%l] %v");

        s_sinks.push_back(file_sink);

        // Console colour sink
        if (cfg.enable_console) {
            auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
            console_sink->set_level(cfg.console_level);
            console_sink->set_pattern("[%H:%M:%S.%e] [%^%l%$] [%n] %v");
            s_sinks.push_back(console_sink);
        }

        // Initialise thread pool for async logging
        spdlog::init_thread_pool(8192, 1);

        s_initialised = true;
        auto root = get("root");
        root->info("Logging initialised: dir={} files={}x{}MB",
                   cfg.log_dir, cfg.max_files,
                   cfg.max_file_size_bytes / (1024 * 1024));
        return true;

    } catch (const spdlog::spdlog_ex& ex) {
        fprintf(stderr, "[Logger] init failed: %s\n", ex.what());
        return false;
    }
}

void Logger::shutdown() {
    std::lock_guard<std::mutex> lock(s_mutex);
    spdlog::shutdown();
    s_loggers.clear();
    s_sinks.clear();
    s_initialised = false;
}

void Logger::flush_all() {
    std::lock_guard<std::mutex> lock(s_mutex);
    for (auto& [name, logger] : s_loggers) {
        logger->flush();
    }
}

// ============================================================
// Named logger factory
// ============================================================

std::shared_ptr<spdlog::logger> Logger::get(const std::string& name) {
    std::lock_guard<std::mutex> lock(s_mutex);

    auto it = s_loggers.find(name);
    if (it != s_loggers.end()) {
        return it->second;
    }

    // Create new async logger with shared sinks
    std::shared_ptr<spdlog::logger> logger;

    if (s_initialised && !s_sinks.empty()) {
        logger = std::make_shared<spdlog::async_logger>(
            name, s_sinks.begin(), s_sinks.end(),
            spdlog::thread_pool(),
            spdlog::async_overflow_policy::block);
    } else {
        // Fallback: null sink (used before init)
        auto null_sink = std::make_shared<spdlog::sinks::null_sink_mt>();
        logger = std::make_shared<spdlog::logger>(name, null_sink);
    }

    logger->set_level(s_config.global_level);
    spdlog::register_logger(logger);
    s_loggers[name] = logger;
    return logger;
}

void Logger::set_level(const std::string& name, spdlog::level::level_enum level) {
    auto logger = get(name);
    logger->set_level(level);
}

void Logger::set_global_level(spdlog::level::level_enum level) {
    std::lock_guard<std::mutex> lock(s_mutex);
    s_config.global_level = level;
    for (auto& [name, logger] : s_loggers) {
        logger->set_level(level);
    }
    spdlog::set_level(level);
}

// ============================================================
// ScopedTimer
// ============================================================

ScopedTimer::ScopedTimer(std::shared_ptr<spdlog::logger> logger,
                         std::string label,
                         spdlog::level::level_enum level)
    : m_logger(std::move(logger))
    , m_label(std::move(label))
    , m_level(level)
    , m_start(std::chrono::steady_clock::now())
{}

ScopedTimer::~ScopedTimer() {
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - m_start).count();
    m_logger->log(m_level, "[TIMER] {} took {:.3f} ms", m_label, elapsed / 1000.0);
}

} // namespace tcu::logging
