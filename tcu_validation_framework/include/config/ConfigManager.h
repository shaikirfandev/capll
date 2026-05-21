/**
 * @file ConfigManager.h
 * @brief JSON/YAML configuration manager with environment profile support.
 *
 * Supports:
 *   - Loading from JSON files (primary format)
 *   - Environment variable overrides (TCU_CFG_<KEY>=<value>)
 *   - Multiple named profiles (default, production, test, hil)
 *   - Type-safe access with defaults
 *   - Dynamic reload without restart
 */

#pragma once

#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <optional>

// Forward-declare nlohmann::json to avoid including in all TUs
namespace nlohmann { class json; }

namespace tcu::config {

/**
 * @brief Configuration manager.
 *
 * Usage:
 * @code
 *   ConfigManager cfg;
 *   cfg.load("configs/default.json");
 *   cfg.load_profile("production");  // overlays configs/production.json
 *   auto iface = cfg.get<std::string>("can.interface", "vcan0");
 *   auto timeout = cfg.get<uint32_t>("uds.p2_timeout_ms", 50);
 * @endcode
 */
class ConfigManager {
public:
    ConfigManager();
    ~ConfigManager();

    ConfigManager(const ConfigManager&)            = delete;
    ConfigManager& operator=(const ConfigManager&) = delete;

    /**
     * @brief Load a JSON configuration file.
     * If a config is already loaded, values are merged (file keys override existing).
     */
    bool load(const std::string& file_path);

    /**
     * @brief Load a named profile (loads configs/<profile>.json).
     */
    bool load_profile(const std::string& profile_name,
                      const std::string& config_dir = "configs");

    /**
     * @brief Apply environment variable overrides.
     * Scans process environment for TCU_CFG_* variables.
     * e.g. TCU_CFG_CAN_INTERFACE=can0 → sets can.interface = "can0"
     */
    void apply_env_overrides();

    /**
     * @brief Reload configuration from the same file path (hot reload).
     */
    bool reload();

    /**
     * @brief Get a typed configuration value.
     * @param key      Dot-separated key path (e.g. "can.interface")
     * @param default_val Returned if key not found
     */
    template<typename T>
    T get(const std::string& key, const T& default_val = T{}) const;

    /**
     * @brief Get an optional value — nullopt if key not found.
     */
    template<typename T>
    std::optional<T> get_optional(const std::string& key) const;

    /**
     * @brief Set a value programmatically (does not write to file).
     */
    template<typename T>
    void set(const std::string& key, const T& value);

    /**
     * @brief Check if a key exists.
     */
    bool has(const std::string& key) const;

    /**
     * @brief Get entire configuration as JSON string.
     */
    std::string dump(int indent = 2) const;

    /**
     * @brief Register a callback for configuration changes (hot reload).
     */
    using ChangeCallback = std::function<void(const std::string& key)>;
    void on_change(ChangeCallback cb);

private:
    nlohmann::json* navigate(const std::string& key, bool create = false);
    const nlohmann::json* navigate(const std::string& key) const;

    mutable std::mutex                   m_mutex;
    std::unique_ptr<nlohmann::json>      m_data;
    std::string                          m_last_file_path;
    std::vector<ChangeCallback>          m_change_callbacks;
};

// ============================================================
// Global singleton accessor
// ============================================================

/**
 * @brief Global configuration singleton.
 */
ConfigManager& global_config();

} // namespace tcu::config
