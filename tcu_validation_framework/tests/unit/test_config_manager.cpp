/**
 * @file test_config_manager.cpp
 * @brief Unit tests for ConfigManager.
 */

#include <gtest/gtest.h>
#include "config/ConfigManager.h"
#include "logging/Logger.h"

#include <fstream>
#include <filesystem>
#include <cstdlib>

using namespace tcu::config;

// ============================================================
// Fixture
// ============================================================

class ConfigManagerTest : public ::testing::Test {
protected:
    std::string tmp_dir;

    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir       = "/tmp/tcu_test_logs";
        lc.enable_console= false;
        tcu::logging::Logger::init(lc);

        tmp_dir = "/tmp/tcu_cfg_test_" + std::to_string(getpid());
        std::filesystem::create_directories(tmp_dir);
    }

    void TearDown() override {
        std::filesystem::remove_all(tmp_dir);
    }

    std::string write_json(const std::string& name, const std::string& content) {
        std::string path = tmp_dir + "/" + name;
        std::ofstream f(path);
        f << content;
        return path;
    }

    ConfigManager make_fresh() {
        return ConfigManager{};
    }
};

// ============================================================
// Load tests
// ============================================================

TEST_F(ConfigManagerTest, LoadValidJsonSucceeds) {
    auto path = write_json("valid.json", R"({ "key": "value" })");
    ConfigManager cfg;
    EXPECT_TRUE(cfg.load(path));
}

TEST_F(ConfigManagerTest, LoadNonExistentFileFails) {
    ConfigManager cfg;
    EXPECT_FALSE(cfg.load("/tmp/does_not_exist_12345.json"));
}

TEST_F(ConfigManagerTest, LoadInvalidJsonFails) {
    auto path = write_json("bad.json", "{ invalid json !!!");
    ConfigManager cfg;
    EXPECT_FALSE(cfg.load(path));
}

TEST_F(ConfigManagerTest, LoadedFilesTracked) {
    auto p1 = write_json("a.json", R"({"x": 1})");
    auto p2 = write_json("b.json", R"({"y": 2})");
    ConfigManager cfg;
    cfg.load(p1);
    cfg.load_overlay(p2);
    EXPECT_EQ(cfg.loaded_files().size(), 2U);
}

// ============================================================
// get<T>() tests
// ============================================================

TEST_F(ConfigManagerTest, GetStringValue) {
    auto path = write_json("cfg.json", R"({ "can": { "interface": "vcan0" } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_EQ(cfg.get<std::string>("can.interface", "default"), "vcan0");
}

TEST_F(ConfigManagerTest, GetIntValue) {
    auto path = write_json("cfg.json", R"({ "uds": { "p2_timeout_ms": 1500 } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_EQ(cfg.get<int>("uds.p2_timeout_ms", 0), 1500);
}

TEST_F(ConfigManagerTest, GetBoolValueTrue) {
    auto path = write_json("cfg.json", R"({ "telematics": { "simulation_mode": true } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_TRUE(cfg.get<bool>("telematics.simulation_mode", false));
}

TEST_F(ConfigManagerTest, GetBoolValueFalse) {
    auto path = write_json("cfg.json", R"({ "telematics": { "simulation_mode": false } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_FALSE(cfg.get<bool>("telematics.simulation_mode", true));
}

TEST_F(ConfigManagerTest, GetDoubleValue) {
    auto path = write_json("cfg.json", R"({ "network": { "timeout": 3.14 } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_NEAR(cfg.get<double>("network.timeout", 0.0), 3.14, 0.001);
}

TEST_F(ConfigManagerTest, GetMissingKeyReturnsDefault) {
    auto path = write_json("cfg.json", R"({ "key": "val" })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_EQ(cfg.get<std::string>("missing.nested.key", "fallback"), "fallback");
}

// ============================================================
// set() tests
// ============================================================

TEST_F(ConfigManagerTest, SetStringThenGet) {
    ConfigManager cfg;
    cfg.set_string("new.key", "hello");
    EXPECT_EQ(cfg.get<std::string>("new.key", ""), "hello");
}

TEST_F(ConfigManagerTest, SetBoolThenGet) {
    ConfigManager cfg;
    cfg.set_bool("feature.enabled", true);
    EXPECT_TRUE(cfg.get<bool>("feature.enabled", false));
}

TEST_F(ConfigManagerTest, SetIntThenGet) {
    ConfigManager cfg;
    cfg.set_int("limits.max_retries", 5);
    EXPECT_EQ(cfg.get<int64_t>("limits.max_retries", 0), 5);
}

// ============================================================
// has() / remove() tests
// ============================================================

TEST_F(ConfigManagerTest, HasExistingKey) {
    auto path = write_json("cfg.json", R"({ "a": { "b": 1 } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    EXPECT_TRUE(cfg.has("a.b"));
}

TEST_F(ConfigManagerTest, HasMissingKeyReturnsFalse) {
    ConfigManager cfg;
    EXPECT_FALSE(cfg.has("nonexistent.key"));
}

TEST_F(ConfigManagerTest, RemoveExistingKey) {
    ConfigManager cfg;
    cfg.set_string("temp.key", "value");
    EXPECT_TRUE(cfg.has("temp.key"));
    cfg.remove("temp.key");
    EXPECT_FALSE(cfg.has("temp.key"));
}

// ============================================================
// Overlay merge tests
// ============================================================

TEST_F(ConfigManagerTest, OverlayOverridesValue) {
    auto base    = write_json("base.json",    R"({ "can": { "interface": "can0", "bitrate": 500000 } })");
    auto overlay = write_json("overlay.json", R"({ "can": { "interface": "vcan0" } })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(base));
    ASSERT_TRUE(cfg.load_overlay(overlay));
    // Overlaid value wins
    EXPECT_EQ(cfg.get<std::string>("can.interface", ""), "vcan0");
    // Non-overlaid value preserved
    EXPECT_EQ(cfg.get<int>("can.bitrate", 0), 500000);
}

// ============================================================
// dump()
// ============================================================

TEST_F(ConfigManagerTest, DumpReturnsPrettyJson) {
    auto path = write_json("cfg.json", R"({ "a": 1 })");
    ConfigManager cfg;
    ASSERT_TRUE(cfg.load(path));
    std::string d = cfg.dump();
    EXPECT_NE(d.find("\"a\""), std::string::npos);
    EXPECT_NE(d.find("1"), std::string::npos);
}

// ============================================================
// Global singleton
// ============================================================

TEST_F(ConfigManagerTest, GlobalConfigReturnsSameInstance) {
    auto& a = ConfigManager::global_config();
    auto& b = ConfigManager::global_config();
    EXPECT_EQ(&a, &b);
}
