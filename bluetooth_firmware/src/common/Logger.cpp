/**
 * @file Logger.cpp
 * @brief Automotive-grade spdlog-backed logger implementation
 */

#include "common/Logger.hpp"
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/pattern_formatter.h>
#include <mutex>
#include <vector>
#include <cassert>

namespace bt {

// ─────────────────────────────────────────────────────────────────────────────
// Pimpl
// ─────────────────────────────────────────────────────────────────────────────
struct Logger::Impl {
    std::shared_ptr<spdlog::logger>  logger;
    std::mutex                       init_mutex;
    bool                             initialised{false};
    Level                            level{Level::DEBUG};
};

// ─────────────────────────────────────────────────────────────────────────────
// Singleton
// ─────────────────────────────────────────────────────────────────────────────
Logger &Logger::get() {
    static Logger instance;
    return instance;
}

Logger::Logger() : impl_(std::make_unique<Impl>()) {}

Logger::~Logger() {
    if (impl_ && impl_->logger) {
        impl_->logger->flush();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Initialisation
// ─────────────────────────────────────────────────────────────────────────────
void Logger::init(std::string_view log_file, Level level) {
    std::lock_guard<std::mutex> lock(impl_->init_mutex);
    if (impl_->initialised) { return; }

    std::vector<spdlog::sink_ptr> sinks;

    // Console sink (coloured output)
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_pattern("[%H:%M:%S.%e] [%^%l%$] [BT] %v");
    sinks.push_back(console_sink);

    // Rotating file sink — 10 MB per file, 5 files max
    try {
        constexpr std::size_t MAX_SIZE  = 10U * 1024U * 1024U;  // 10 MB
        constexpr std::size_t MAX_FILES = 5U;
        auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
            std::string(log_file), MAX_SIZE, MAX_FILES, /*rotate_on_open=*/false);
        file_sink->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] [BT] [%t] %v");
        sinks.push_back(file_sink);
    } catch (const std::exception &ex) {
        // File logging unavailable (e.g. no write permission) — continue with console only
        console_sink->warn("Logger: Failed to open log file '{}': {}", log_file, ex.what());
    }

    impl_->logger = std::make_shared<spdlog::logger>("bt_firmware", sinks.begin(), sinks.end());
    impl_->logger->set_level(static_cast<spdlog::level::level_enum>(static_cast<int>(level)));
    impl_->logger->flush_on(spdlog::level::warn);  // Auto-flush on WARN+

    spdlog::register_logger(impl_->logger);
    spdlog::set_default_logger(impl_->logger);

    impl_->level       = level;
    impl_->initialised = true;

    impl_->logger->info("========================================");
    impl_->logger->info("Bluetooth Firmware Logger Initialised");
    impl_->logger->info("Log file : {}", log_file);
    impl_->logger->info("Log level: {}", spdlog::level::to_string_view(
                            static_cast<spdlog::level::level_enum>(static_cast<int>(level))));
    impl_->logger->info("========================================");
}

void Logger::set_level(Level level) {
    impl_->level = level;
    if (impl_->logger) {
        impl_->logger->set_level(
            static_cast<spdlog::level::level_enum>(static_cast<int>(level)));
    }
}

Logger::Level Logger::get_level() const { return impl_->level; }

void Logger::flush() {
    if (impl_->logger) { impl_->logger->flush(); }
}

std::shared_ptr<spdlog::logger> Logger::raw() { return impl_->logger; }

// ─────────────────────────────────────────────────────────────────────────────
// Lazy init helper — ensure logger exists even if init() was never called
// ─────────────────────────────────────────────────────────────────────────────
static void ensure_init() {
    static bool done = false;
    if (!done) {
        bt::Logger::get().init("bt_firmware.log", bt::Logger::Level::DEBUG);
        done = true;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Template implementations (explicit instantiations avoid link errors)
// ─────────────────────────────────────────────────────────────────────────────
template<typename... Args>
void Logger::trace(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->trace(fmt::runtime(fmt), std::forward<Args>(args)...);
}

template<typename... Args>
void Logger::debug(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->debug(fmt::runtime(fmt), std::forward<Args>(args)...);
}

template<typename... Args>
void Logger::info(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->info(fmt::runtime(fmt), std::forward<Args>(args)...);
}

template<typename... Args>
void Logger::warn(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->warn(fmt::runtime(fmt), std::forward<Args>(args)...);
}

template<typename... Args>
void Logger::error(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->error(fmt::runtime(fmt), std::forward<Args>(args)...);
}

template<typename... Args>
void Logger::critical(std::string_view fmt, Args &&...args) {
    ensure_init();
    impl_->logger->critical(fmt::runtime(fmt), std::forward<Args>(args)...);
    impl_->logger->flush();  // Always flush on critical
}

// Explicit instantiations for zero-arg variants (most common for simple messages)
template void Logger::info(std::string_view);
template void Logger::debug(std::string_view);
template void Logger::warn(std::string_view);
template void Logger::error(std::string_view);
template void Logger::critical(std::string_view);

}  // namespace bt
