/**
 * @file Framework.h
 * @brief Core Framework — singleton lifecycle manager for the TCU Validation Platform
 *
 * Manages startup, shutdown, module registration, and the global watchdog.
 * All modules register themselves here on init and deregister on teardown.
 *
 * Thread-safety: All public methods are thread-safe via internal mutex.
 */

#pragma once

#include <atomic>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace tcu {

/**
 * @brief Framework initialisation configuration.
 */
struct FrameworkConfig {
    std::string instance_name{"tcu_validator"};  ///< Unique instance identifier
    std::string log_dir{"logs"};                 ///< Log output directory
    std::string config_path{"configs/default.json"}; ///< Primary config file
    bool        enable_watchdog{true};           ///< Global watchdog enable
    uint32_t    watchdog_timeout_ms{30000};      ///< Watchdog timeout (ms)
};

/**
 * @brief Module lifecycle callbacks registered by each subsystem.
 */
struct ModuleCallbacks {
    std::function<bool()>      init;      ///< Initialise module; returns false on failure
    std::function<void()>      shutdown;  ///< Graceful shutdown
    std::function<std::string()> health;  ///< Return health status string
};

/**
 * @brief Global framework state.
 */
enum class FrameworkState : uint8_t {
    UNINITIALIZED = 0,
    INITIALIZING,
    RUNNING,
    SHUTTING_DOWN,
    FAULT
};

/**
 * @brief Core framework singleton — entry point for all subsystems.
 *
 * Usage:
 * @code
 *   auto& fw = Framework::instance();
 *   fw.initialize(cfg);
 *   fw.register_module("can", {init_fn, shutdown_fn, health_fn});
 *   fw.start();
 *   // ... run ...
 *   fw.shutdown();
 * @endcode
 */
class Framework {
public:
    Framework(const Framework&)            = delete;
    Framework& operator=(const Framework&) = delete;
    Framework(Framework&&)                 = delete;
    Framework& operator=(Framework&&)      = delete;

    /**
     * @brief Singleton access.
     */
    static Framework& instance();

    /**
     * @brief Initialise the framework with the given configuration.
     * @return true on success
     */
    bool initialize(const FrameworkConfig& cfg);

    /**
     * @brief Register a module for lifecycle management.
     * @param name   Unique module name
     * @param cbs    Lifecycle callbacks
     */
    void register_module(const std::string& name, ModuleCallbacks cbs);

    /**
     * @brief Start all registered modules in registration order.
     * @return true if all modules started successfully
     */
    bool start();

    /**
     * @brief Gracefully shutdown all modules in reverse registration order.
     */
    void shutdown();

    /**
     * @brief Query framework state.
     */
    FrameworkState state() const noexcept;

    /**
     * @brief Query per-module health.
     * @return Map of {module_name → health_string}
     */
    std::unordered_map<std::string, std::string> health_report() const;

    /**
     * @brief Get framework version string.
     */
    static const char* version() noexcept;

    /**
     * @brief Block the calling thread until shutdown is requested.
     */
    void wait_for_shutdown();

    /**
     * @brief Request a framework shutdown from any thread (signal-safe wrapper).
     */
    void request_shutdown();

private:
    Framework() = default;
    ~Framework() = default;

    mutable std::mutex                              m_mutex;
    FrameworkConfig                                 m_config;
    std::atomic<FrameworkState>                     m_state{FrameworkState::UNINITIALIZED};
    std::vector<std::string>                        m_module_order;
    std::unordered_map<std::string, ModuleCallbacks> m_modules;
    std::atomic<bool>                               m_shutdown_requested{false};
};

} // namespace tcu
