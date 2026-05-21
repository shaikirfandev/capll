/**
 * @file ConfigManager.cpp
 * @brief JSON config with dot-path navigation, env var overrides, hot reload.
 */

#include "config/ConfigManager.h"
#include "logging/Logger.h"

#include <fstream>
#include <regex>
#include <sstream>
#include <filesystem>
#include <stdexcept>

namespace tcu::config {

static auto s_log = tcu::logging::Logger::get("config");

// ============================================================
// Singleton
// ============================================================

ConfigManager& ConfigManager::global_config() {
    static ConfigManager s_instance;
    return s_instance;
}

// ============================================================
// Load / Save
// ============================================================

bool ConfigManager::load(const std::string& path) {
    std::lock_guard<std::mutex> lock(m_mutex);

    std::ifstream f(path);
    if (!f.is_open()) {
        s_log->error("Cannot open config: {}", path);
        return false;
    }

    try {
        m_root = nlohmann::json::parse(f, nullptr, /*exceptions=*/true,
                                        /*ignore_comments=*/true);
        m_loaded_paths.push_back(path);
        s_log->info("Config loaded: {}", path);
    } catch (const nlohmann::json::parse_error& ex) {
        s_log->error("JSON parse error in {}: {}", path, ex.what());
        return false;
    }

    apply_env_overrides();
    return true;
}

bool ConfigManager::load_overlay(const std::string& path) {
    std::lock_guard<std::mutex> lock(m_mutex);

    std::ifstream f(path);
    if (!f.is_open()) {
        s_log->warn("Overlay config not found (skipping): {}", path);
        return false;
    }

    try {
        auto overlay = nlohmann::json::parse(f, nullptr, true, true);
        merge(m_root, overlay);
        m_loaded_paths.push_back(path);
        s_log->info("Config overlay merged: {}", path);
    } catch (const nlohmann::json::parse_error& ex) {
        s_log->error("Overlay parse error {}: {}", path, ex.what());
        return false;
    }

    apply_env_overrides();
    return true;
}

bool ConfigManager::load_profile(const std::string& profile_name,
                                  const std::string& config_dir) {
    std::string profile_path = config_dir + "/" + profile_name + ".json";
    return load_overlay(profile_path);
}

bool ConfigManager::save(const std::string& path) const {
    std::lock_guard<std::mutex> lock(m_mutex);
    std::ofstream f(path);
    if (!f.is_open()) { return false; }
    f << m_root.dump(2);
    s_log->info("Config saved: {}", path);
    return true;
}

// ============================================================
// Dot-path access implementation
// ============================================================

nlohmann::json* ConfigManager::navigate(const std::string& dot_path,
                                         bool create_missing) {
    // Split "a.b.c" → ["a", "b", "c"]
    std::vector<std::string> keys;
    std::istringstream ss(dot_path);
    std::string token;
    while (std::getline(ss, token, '.')) {
        if (!token.empty()) { keys.push_back(token); }
    }

    nlohmann::json* node = &m_root;
    for (const auto& k : keys) {
        if (!node->is_object()) { return nullptr; }
        auto it = node->find(k);
        if (it == node->end()) {
            if (!create_missing) { return nullptr; }
            (*node)[k] = nlohmann::json::object();
            node = &(*node)[k];
        } else {
            node = &(*it);
        }
    }
    return node;
}

const nlohmann::json* ConfigManager::navigate(const std::string& dot_path) const {
    std::vector<std::string> keys;
    std::istringstream ss(dot_path);
    std::string token;
    while (std::getline(ss, token, '.')) {
        if (!token.empty()) { keys.push_back(token); }
    }

    const nlohmann::json* node = &m_root;
    for (const auto& k : keys) {
        if (!node->is_object()) { return nullptr; }
        auto it = node->find(k);
        if (it == node->end()) { return nullptr; }
        node = &(*it);
    }
    return node;
}

bool ConfigManager::has(const std::string& dot_path) const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return navigate(dot_path) != nullptr;
}

void ConfigManager::remove(const std::string& dot_path) {
    std::lock_guard<std::mutex> lock(m_mutex);
    // Find parent
    auto last_dot = dot_path.rfind('.');
    if (last_dot == std::string::npos) {
        m_root.erase(dot_path);
        return;
    }
    std::string parent_path = dot_path.substr(0, last_dot);
    std::string key         = dot_path.substr(last_dot + 1);
    auto* parent = navigate(parent_path);
    if (parent && parent->is_object()) {
        parent->erase(key);
    }
}

// ============================================================
// Environment variable overrides
// ============================================================

void ConfigManager::apply_env_overrides() {
    // Scan environment for TCU_CFG_* variables
    // TCU_CFG_CAN_INTERFACE=vcan0 → sets config key "can.interface"
    extern char** environ;
    if (environ == nullptr) { return; }

    for (char** ep = environ; *ep != nullptr; ++ep) {
        std::string entry(*ep);
        static const std::string PREFIX = "TCU_CFG_";
        if (entry.rfind(PREFIX, 0) != 0) { continue; }

        auto eq_pos = entry.find('=');
        if (eq_pos == std::string::npos) { continue; }

        // Convert TCU_CFG_CAN_INTERFACE → can.interface (lower case, _ → . for top-level, keep sub-structure)
        std::string raw_key = entry.substr(PREFIX.size(), eq_pos - PREFIX.size());
        std::string value   = entry.substr(eq_pos + 1);

        // Simple rule: first underscore becomes a dot, rest stay
        // TCU_CFG_CAN_INTERFACE → can.interface
        std::string dot_key;
        bool first_sep = true;
        for (char c : raw_key) {
            if (c == '_' && first_sep) {
                dot_key += '.';
                first_sep = false;
            } else {
                dot_key += static_cast<char>(std::tolower(c));
            }
        }

        set_string(dot_key, value);
        s_log->debug("ENV override: {}={}", dot_key, value);
    }
}

// ============================================================
// Typed set helpers
// ============================================================

void ConfigManager::set_string(const std::string& dot_path, const std::string& value) {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto* node = navigate(dot_path, true);
    if (node) { *node = value; }
}

void ConfigManager::set_bool(const std::string& dot_path, bool value) {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto* node = navigate(dot_path, true);
    if (node) { *node = value; }
}

void ConfigManager::set_int(const std::string& dot_path, int64_t value) {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto* node = navigate(dot_path, true);
    if (node) { *node = value; }
}

void ConfigManager::set_double(const std::string& dot_path, double value) {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto* node = navigate(dot_path, true);
    if (node) { *node = value; }
}

// ============================================================
// Hot reload
// ============================================================

void ConfigManager::enable_hot_reload(bool enabled, uint32_t interval_ms) {
    m_hot_reload_enabled  = enabled;
    m_hot_reload_interval = interval_ms;

    if (enabled && !m_reload_thread_running) {
        m_reload_thread_running = true;
        m_reload_thread = std::thread(&ConfigManager::hot_reload_fn, this);
        s_log->info("Config hot reload enabled (interval={}ms)", interval_ms);
    } else if (!enabled && m_reload_thread_running) {
        m_reload_thread_running = false;
        if (m_reload_thread.joinable()) { m_reload_thread.join(); }
    }
}

void ConfigManager::hot_reload_fn() {
    while (m_reload_thread_running.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(m_hot_reload_interval));
        if (!m_reload_thread_running) { break; }

        // Check mtime of loaded files
        for (const auto& path : m_loaded_paths) {
            try {
                auto mtime = std::filesystem::last_write_time(path);
                auto& last = m_file_mtimes[path];
                if (mtime != last) {
                    last = mtime;
                    s_log->info("Config changed — hot reloading: {}", path);
                    load(path);
                    if (m_reload_callback) { m_reload_callback(); }
                }
            } catch (...) {
                // File may not exist yet
            }
        }
    }
}

void ConfigManager::set_reload_callback(std::function<void()> cb) {
    m_reload_callback = std::move(cb);
}

// ============================================================
// Utilities
// ============================================================

std::string ConfigManager::dump() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_root.dump(2);
}

const std::vector<std::string>& ConfigManager::loaded_files() const {
    return m_loaded_paths;
}

void ConfigManager::merge(nlohmann::json& base, const nlohmann::json& overlay) {
    if (!overlay.is_object()) { base = overlay; return; }
    for (const auto& [key, val] : overlay.items()) {
        if (base.contains(key) && base[key].is_object() && val.is_object()) {
            merge(base[key], val);
        } else {
            base[key] = val;
        }
    }
}

} // namespace tcu::config
