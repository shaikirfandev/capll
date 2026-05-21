/**
 * @file test_stress.cpp
 * @brief Stress and soak tests: concurrent sessions, throughput, memory stability.
 */

#include <gtest/gtest.h>
#include "telematics/TelematicsSDKAdapter.h"
#include "validation/TestEngine.h"
#include "config/ConfigManager.h"
#include "logging/Logger.h"

#include <atomic>
#include <chrono>
#include <thread>
#include <vector>

using namespace tcu;

// ============================================================
// Fixture
// ============================================================

class StressTest : public ::testing::Test {
protected:
    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir        = "/tmp/tcu_test_logs";
        lc.enable_console = false;
        tcu::logging::Logger::init(lc);
    }
};

// ============================================================
// Telemetry publish throughput
// ============================================================

TEST_F(StressTest, TelemetryPublishThroughput_1000Messages) {
    telematics::SDKConfig cfg;
    cfg.simulation_mode = true;
    telematics::TelematicsSDKAdapter sdk(cfg);
    ASSERT_TRUE(sdk.connect());

    constexpr int N = 1000;
    auto t0 = std::chrono::steady_clock::now();

    for (int i = 0; i < N; ++i) {
        telematics::TelemetryPayload p;
        p.device_id = "STRESS-001";
        p.numeric_signals["seq"]       = static_cast<double>(i);
        p.numeric_signals["speed_kmh"] = static_cast<double>(i % 200);
        p.numeric_signals["battery_v"] = 12.0 + (i % 10) * 0.01;
        EXPECT_TRUE(sdk.publish_telemetry(p));
    }

    auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t0).count();

    EXPECT_EQ(sdk.sim_get_published().size(), static_cast<size_t>(N));

    double rate = N * 1000.0 / elapsed_ms;
    EXPECT_GT(rate, 100.0)  // Minimum 100 msg/sec
        << "Publish rate too low: " << rate << " msg/sec";

    auto log = tcu::logging::Logger::get("stress");
    log->info("Telemetry throughput: {} msg in {} ms ({:.0f} msg/sec)",
              N, elapsed_ms, rate);
}

// ============================================================
// Concurrent publish from multiple threads
// ============================================================

TEST_F(StressTest, ConcurrentTelemetryPublish_8Threads_500Messages) {
    telematics::SDKConfig cfg;
    cfg.simulation_mode = true;
    telematics::TelematicsSDKAdapter sdk(cfg);
    ASSERT_TRUE(sdk.connect());

    constexpr int NUM_THREADS = 8;
    constexpr int MSGS_PER_THREAD = 500;
    std::atomic<int> success_count{0};
    std::atomic<int> fail_count{0};

    std::vector<std::thread> threads;
    for (int t = 0; t < NUM_THREADS; ++t) {
        threads.emplace_back([&sdk, &success_count, &fail_count, t] {
            for (int i = 0; i < MSGS_PER_THREAD; ++i) {
                telematics::TelemetryPayload p;
                p.device_id = "STRESS-T" + std::to_string(t);
                p.numeric_signals["thread"]  = static_cast<double>(t);
                p.numeric_signals["message"] = static_cast<double>(i);
                if (sdk.publish_telemetry(p)) {
                    ++success_count;
                } else {
                    ++fail_count;
                }
            }
        });
    }

    for (auto& th : threads) { th.join(); }

    int total = NUM_THREADS * MSGS_PER_THREAD;
    EXPECT_EQ(success_count.load(), total);
    EXPECT_EQ(fail_count.load(), 0);
    auto log = tcu::logging::Logger::get("stress");
    log->info("Concurrent publish: {} threads × {} = {} messages, failures={}",
              NUM_THREADS, MSGS_PER_THREAD, total, fail_count.load());
}

// ============================================================
// TestEngine throughput
// ============================================================

TEST_F(StressTest, TestEngineThroughput_200Tests) {
    validation::EngineConfig eng_cfg;
    eng_cfg.parallel = false;
    validation::TestEngine engine(eng_cfg);

    constexpr int N = 200;
    for (int i = 0; i < N; ++i) {
        validation::TestCase tc;
        tc.id   = "ST" + std::to_string(i);
        tc.name = "StressTest " + std::to_string(i);
        int id  = i;
        tc.execute = [id] {
            validation::TestResult r;
            r.test_id = "ST" + std::to_string(id);
            r.verdict = (id % 10 != 9)
                        ? validation::Verdict::PASS
                        : validation::Verdict::FAIL;  // Every 10th fails
            return r;
        };
        engine.add_test(tc);
    }

    auto t0 = std::chrono::steady_clock::now();
    auto result = engine.run("Stress_200");
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t0).count();

    EXPECT_EQ(result.total_tests, static_cast<uint32_t>(N));
    EXPECT_EQ(result.passed, static_cast<uint32_t>(N - N / 10));
    EXPECT_EQ(result.failed, static_cast<uint32_t>(N / 10));
    EXPECT_LT(elapsed, 30000) << "200 no-op tests should complete in < 30s";

    auto log = tcu::logging::Logger::get("stress");
    log->info("TestEngine: {} tests in {} ms ({:.0f} tests/sec)",
              N, elapsed, N * 1000.0 / elapsed);
}

// ============================================================
// TestEngine parallel throughput
// ============================================================

TEST_F(StressTest, TestEngineParallel_100Tests) {
    validation::EngineConfig eng_cfg;
    eng_cfg.parallel = true;
    validation::TestEngine engine(eng_cfg);

    constexpr int N = 100;
    for (int i = 0; i < N; ++i) {
        validation::TestCase tc;
        tc.id      = "PAR" + std::to_string(i);
        tc.name    = "Parallel " + std::to_string(i);
        tc.execute = [] {
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
            validation::TestResult r;
            r.verdict = validation::Verdict::PASS;
            return r;
        };
        engine.add_test(tc);
    }

    auto t0     = std::chrono::steady_clock::now();
    auto result = engine.run("Parallel_100");
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t0).count();

    EXPECT_EQ(result.passed, static_cast<uint32_t>(N));
    // Parallel should be significantly faster than 100 × 5ms = 500ms
    EXPECT_LT(elapsed, 400L) << "Parallel 100×5ms tests should complete in < 400ms";

    auto log = tcu::logging::Logger::get("stress");
    log->info("Parallel TestEngine: {} tests in {} ms", N, elapsed);
}

// ============================================================
// Config under load (many concurrent reads)
// ============================================================

TEST_F(StressTest, ConfigConcurrentReads) {
    config::ConfigManager cfg;
    cfg.set_string("can.interface",  "vcan0");
    cfg.set_int("uds.p2_timeout_ms", 1000);
    cfg.set_bool("sim.enabled",      true);
    cfg.set_double("limits.voltage", 12.5);

    constexpr int READERS = 10;
    constexpr int READS   = 1000;
    std::atomic<int> ok_count{0};

    std::vector<std::thread> threads;
    for (int t = 0; t < READERS; ++t) {
        threads.emplace_back([&cfg, &ok_count] {
            for (int i = 0; i < READS; ++i) {
                auto v = cfg.get<std::string>("can.interface", "");
                if (v == "vcan0") { ++ok_count; }
            }
        });
    }
    for (auto& th : threads) { th.join(); }

    EXPECT_EQ(ok_count.load(), READERS * READS);
}

// ============================================================
// Memory stability — repeated connect/disconnect cycles
// ============================================================

TEST_F(StressTest, TelematicsConnectDisconnect_50Cycles) {
    constexpr int CYCLES = 50;
    for (int i = 0; i < CYCLES; ++i) {
        telematics::SDKConfig cfg;
        cfg.simulation_mode = true;
        telematics::TelematicsSDKAdapter sdk(cfg);
        ASSERT_TRUE(sdk.connect())    << "cycle " << i;
        EXPECT_TRUE(sdk.is_connected());
        sdk.disconnect();
        EXPECT_FALSE(sdk.is_connected());
    }
}

// ============================================================
// Rapid OTA inject/check cycles
// ============================================================

TEST_F(StressTest, OTA_RapidInjectAndCheck_100Cycles) {
    telematics::SDKConfig cfg;
    cfg.simulation_mode = true;
    telematics::TelematicsSDKAdapter sdk(cfg);
    ASSERT_TRUE(sdk.connect());

    constexpr int CYCLES = 100;
    int found = 0;

    for (int i = 0; i < CYCLES; ++i) {
        telematics::OTANotification notif;
        notif.package_id      = "PKG-" + std::to_string(i);
        notif.current_version = "1.0." + std::to_string(i);
        notif.new_version     = "2.0." + std::to_string(i);
        sdk.sim_inject_ota(notif);

        telematics::OTANotification detected;
        if (sdk.check_for_updates(detected)) {
            EXPECT_EQ(detected.package_id, notif.package_id);
            ++found;
        }
    }

    EXPECT_EQ(found, CYCLES);
}
