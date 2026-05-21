/**
 * @file Framework.cpp
 * @brief Core Framework implementation.
 */

#include "core/Framework.h"
#include "logging/Logger.h"

#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <iostream>

namespace tcu {

// ============================================================
// Static storage
// ============================================================

static std::condition_variable s_shutdown_cv;
static std::mutex               s_shutdown_mutex;

// ============================================================
// Singleton
// ============================================================

Framework& Framework::instance() {
    static Framework s_instance;
    return s_instance;
}

// ============================================================
// Public API
// ============================================================

bool Framework::initialize(const FrameworkConfig& cfg) {
    std::lock_guard<std::mutex> lock(m_mutex);

    if (m_state != FrameworkState::UNINITIALIZED) {
        std::cerr << "[Framework] Already initialised — ignoring duplicate call\n";
        return false;
    }

    m_state  = FrameworkState::INITIALIZING;
    m_config = cfg;

    // Initialise logging first so all subsequent code can log
    tcu::logging::LogConfig log_cfg;
    log_cfg.log_dir   = cfg.log_dir;
    log_cfg.base_filename = cfg.instance_name;
    if (!tcu::logging::Logger::init(log_cfg)) {
        std::cerr << "[Framework] Logger init failed\n";
        m_state = FrameworkState::FAULT;
        return false;
    }

    auto log = tcu::logging::Logger::get("framework");
    log->info("TCU Validation Framework v{} starting", version());
    log->info("Instance: {}, Config: {}", cfg.instance_name, cfg.config_path);

    return true;
}

void Framework::register_module(const std::string& name, ModuleCallbacks cbs) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_module_order.push_back(name);
    m_modules[name] = std::move(cbs);
    tcu::logging::Logger::get("framework")->debug("Module registered: {}", name);
}

bool Framework::start() {
    auto log = tcu::logging::Logger::get("framework");

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_state != FrameworkState::INITIALIZING) {
            log->error("start() called in wrong state: {}",
                       static_cast<int>(m_state.load()));
            return false;
        }
    }

    log->info("Starting {} registered modules...", m_module_order.size());

    for (const auto& name : m_module_order) {
        auto& cbs = m_modules[name];
        log->info("  → Starting module: {}", name);
        if (cbs.init && !cbs.init()) {
            log->error("Module '{}' failed to initialise — aborting start", name);
            m_state = FrameworkState::FAULT;
            return false;
        }
    }

    m_state = FrameworkState::RUNNING;
    log->info("All modules started. Framework RUNNING.");
    return true;
}

void Framework::shutdown() {
    auto log = tcu::logging::Logger::get("framework");

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_state == FrameworkState::SHUTTING_DOWN ||
            m_state == FrameworkState::UNINITIALIZED) {
            return;
        }
        m_state = FrameworkState::SHUTTING_DOWN;
    }

    log->info("Shutting down framework ({} modules)...", m_module_order.size());

    // Shutdown in reverse registration order
    for (auto it = m_module_order.rbegin(); it != m_module_order.rend(); ++it) {
        auto& cbs = m_modules[*it];
        log->info("  ← Stopping module: {}", *it);
        if (cbs.shutdown) {
            cbs.shutdown();
        }
    }

    log->info("Framework shutdown complete.");
    tcu::logging::Logger::flush_all();

    m_shutdown_requested = true;
    s_shutdown_cv.notify_all();
}

FrameworkState Framework::state() const noexcept {
    return m_state.load();
}

std::unordered_map<std::string, std::string> Framework::health_report() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    std::unordered_map<std::string, std::string> report;
    for (const auto& [name, cbs] : m_modules) {
        report[name] = cbs.health ? cbs.health() : "OK";
    }
    return report;
}

const char* Framework::version() noexcept {
    return "2.0.0";
}

void Framework::wait_for_shutdown() {
    std::unique_lock<std::mutex> lock(s_shutdown_mutex);
    s_shutdown_cv.wait(lock, [this] { return m_shutdown_requested.load(); });
}

void Framework::request_shutdown() {
    m_shutdown_requested = true;
    s_shutdown_cv.notify_all();
    // Trigger full shutdown on next event loop cycle
    shutdown();
}

} // namespace tcu
