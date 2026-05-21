/**
 * @file test_tcu_integration.cpp
 * @brief Integration tests: full OTA sequence, telematics, config, reporting.
 *
 * These tests run in simulation mode (no real hardware needed).
 * Tests that need vcan0 are skipped if the interface is not present.
 */

#include <gtest/gtest.h>
#include "core/Framework.h"
#include "can/CANManager.h"
#include "diagnostics/UDSClient.h"
#include "telematics/TelematicsSDKAdapter.h"
#include "firmware/CRCValidator.h"
#include "validation/TestEngine.h"
#include "validation/FaultInjector.h"
#include "reporting/ReportGenerator.h"
#include "config/ConfigManager.h"
#include "logging/Logger.h"

#include <filesystem>
#include <fstream>
#include <thread>
#include <chrono>

using namespace tcu;

// ============================================================
// Fixture
// ============================================================

class TCUIntegrationTest : public ::testing::Test {
protected:
    std::string tmp_dir;
    std::shared_ptr<can::CANManager>                can_mgr;
    std::shared_ptr<diagnostics::UDSClient>         uds_client;
    std::shared_ptr<telematics::TelematicsSDKAdapter> sdk;
    bool vcan_available = false;

    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir        = "/tmp/tcu_test_logs";
        lc.enable_console = false;
        tcu::logging::Logger::init(lc);

        tmp_dir = "/tmp/tcu_integ_" + std::to_string(getpid());
        std::filesystem::create_directories(tmp_dir);

        vcan_available = (system("ip link show vcan0 > /dev/null 2>&1") == 0);

        // CAN Manager
        can::CANConfig cc;
        cc.interface     = "vcan0";
        cc.loopback      = true;
        cc.rx_timeout_ms = 100;
        can_mgr = std::make_shared<can::CANManager>(cc);

        // UDS Client
        diagnostics::ISOTPConfig istp;
        istp.tx_id         = 0x7E0;
        istp.rx_id         = 0x7E8;
        istp.p2_timeout_ms = 200;
        uds_client = std::make_shared<diagnostics::UDSClient>(can_mgr, istp);

        // Telematics SDK (simulation mode)
        telematics::SDKConfig sdk_cfg;
        sdk_cfg.simulation_mode = true;
        sdk = std::make_shared<telematics::TelematicsSDKAdapter>(sdk_cfg);
    }

    void TearDown() override {
        std::filesystem::remove_all(tmp_dir);
    }

    std::string write_temp_file(const std::string& name, const std::string& content) {
        std::string path = tmp_dir + "/" + name;
        std::ofstream f(path);
        f << content;
        return path;
    }
};

// ============================================================
// Config integration
// ============================================================

TEST_F(TCUIntegrationTest, ConfigLoadAndModuleInit) {
    auto cfg_path = write_temp_file("default.json", R"({
        "can": { "interface": "vcan0", "enable_fd": false },
        "uds": { "tx_id": 2016, "rx_id": 2024, "p2_timeout_ms": 500 },
        "telematics": { "simulation_mode": true, "server_url": "mqtt://localhost:1883" },
        "engine": { "parallel": false, "stop_on_first_fail": false }
    })");

    config::ConfigManager cfg;
    ASSERT_TRUE(cfg.load(cfg_path));

    EXPECT_EQ(cfg.get<std::string>("can.interface", ""), "vcan0");
    EXPECT_EQ(cfg.get<int>("uds.tx_id", 0), 2016);
    EXPECT_TRUE(cfg.get<bool>("telematics.simulation_mode", false));
}

// ============================================================
// Telematics simulation flow
// ============================================================

TEST_F(TCUIntegrationTest, TelematicsConnectAndPublish) {
    ASSERT_TRUE(sdk->connect());
    EXPECT_TRUE(sdk->is_connected());

    telematics::TelemetryPayload payload;
    payload.device_id = "TCU-TEST-001";
    payload.numeric_signals["battery_v"]    = 12.5;
    payload.numeric_signals["speed_kmh"]    = 0.0;
    payload.numeric_signals["gps_lat"]      = 52.52;
    payload.numeric_signals["gps_lon"]      = 13.405;
    payload.string_signals["vin"]           = "WBATESTVIN000001";
    payload.string_signals["fw_version"]    = "1.0.0";

    EXPECT_TRUE(sdk->publish_telemetry(payload));

    auto& published = sdk->sim_get_published();
    ASSERT_EQ(published.size(), 1U);
    EXPECT_EQ(published[0].device_id, "TCU-TEST-001");
    EXPECT_NEAR(published[0].numeric_signals.at("battery_v"), 12.5, 0.01);
}

TEST_F(TCUIntegrationTest, OTANotificationDetectedAndAcknowledged) {
    ASSERT_TRUE(sdk->connect());

    // Inject OTA
    telematics::OTANotification notif;
    notif.package_id      = "TCU-FW-2.0.0";
    notif.current_version = "1.5.0";
    notif.new_version     = "2.0.0";
    notif.package_size    = 1024 * 512;  // 512 KB
    notif.checksum_sha256 = "deadbeef";
    sdk->sim_inject_ota(notif);

    telematics::OTANotification detected;
    EXPECT_TRUE(sdk->check_for_updates(detected));
    EXPECT_EQ(detected.package_id,  "TCU-FW-2.0.0");
    EXPECT_EQ(detected.new_version, "2.0.0");

    // Acknowledge
    EXPECT_TRUE(sdk->acknowledge_ota(detected.package_id,
                                      telematics::OTAStatus::DOWNLOAD_STARTED));
    EXPECT_TRUE(sdk->report_ota_progress(detected.package_id, 50.0f));
    EXPECT_TRUE(sdk->acknowledge_ota(detected.package_id,
                                      telematics::OTAStatus::INSTALL_SUCCESS));
}

TEST_F(TCUIntegrationTest, NetworkMetricsAvailable) {
    ASSERT_TRUE(sdk->connect());

    telematics::NetworkMetrics good;
    good.rsrp             = -85.0f;
    good.rsrq             = -10.0f;
    good.sinr             =  15.0f;
    good.dl_throughput_kbps = 10000.0f;
    good.latency_ms       =  20.0f;
    good.connected        = true;
    sdk->sim_set_metrics(good);

    auto m = sdk->get_network_metrics();
    EXPECT_TRUE(m.connected);
    EXPECT_NEAR(m.rsrp,       -85.0f,  0.1f);
    EXPECT_NEAR(m.latency_ms,  20.0f,  0.1f);
    EXPECT_GT(m.dl_throughput_kbps, 0.0f);
}

// ============================================================
// Fault injection integration
// ============================================================

TEST_F(TCUIntegrationTest, FaultInjectionNetworkLossAndRecovery) {
    ASSERT_TRUE(sdk->connect());

    auto injector = std::make_shared<validation::FaultInjector>(can_mgr, sdk);

    validation::FaultSpec spec;
    spec.type        = validation::FaultType::NETWORK_LOSS;
    spec.duration_ms = 0;  // Manual clear

    auto fault = injector->inject(spec);
    ASSERT_NE(fault, nullptr);
    EXPECT_TRUE(fault->is_active());

    auto metrics_during = sdk->get_network_metrics();
    EXPECT_FALSE(metrics_during.connected);

    // Clear fault (RAII)
    fault.reset();

    auto metrics_after = sdk->get_network_metrics();
    EXPECT_TRUE(metrics_after.connected);
}

TEST_F(TCUIntegrationTest, MultipleFaultsClearedByReset) {
    ASSERT_TRUE(sdk->connect());
    auto injector = std::make_shared<validation::FaultInjector>(can_mgr, sdk);

    auto f1 = injector->inject({validation::FaultType::NETWORK_LOSS, 0});
    EXPECT_TRUE(f1 && f1->is_active());

    injector->clear_all();
    EXPECT_FALSE(injector->is_fault_active(validation::FaultType::NETWORK_LOSS));
}

// ============================================================
// TestEngine + Reporting integration
// ============================================================

TEST_F(TCUIntegrationTest, FullSuiteWithReportGeneration) {
    validation::EngineConfig eng_cfg;
    eng_cfg.parallel           = false;
    eng_cfg.stop_on_first_fail = false;
    validation::TestEngine engine(eng_cfg);

    // TC1: Telematics connection
    {
        validation::TestCase tc;
        tc.id         = "IT001";
        tc.name       = "Telematics Connection";
        tc.timeout_ms = 5000;
        tc.execute    = [this]() {
            validation::TestResult r;
            r.test_id   = "IT001";
            r.test_name = "Telematics Connection";
            bool ok = sdk->connect();
            r.verdict = ok ? validation::Verdict::PASS : validation::Verdict::FAIL;
            return r;
        };
        engine.add_test(tc);
    }

    // TC2: Telemetry publish
    {
        validation::TestCase tc;
        tc.id         = "IT002";
        tc.name       = "Telemetry Publish";
        tc.timeout_ms = 5000;
        tc.precondition = [this] { return sdk->is_connected(); };
        tc.execute    = [this]() {
            telematics::TelemetryPayload p;
            p.device_id = "IT-TEST";
            p.numeric_signals["v"] = 12.0;
            validation::TestResult r;
            r.test_id   = "IT002";
            r.test_name = "Telemetry Publish";
            r.verdict   = sdk->publish_telemetry(p)
                          ? validation::Verdict::PASS
                          : validation::Verdict::FAIL;
            return r;
        };
        engine.add_test(tc);
    }

    auto suite = engine.run("Integration_Suite");

    // Generate all report formats
    reporting::ReportGenerator reporter(tmp_dir);
    EXPECT_TRUE(reporter.generate(suite, reporting::ReportFormat::ALL, "integration"));

    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/integration.html"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/integration.json"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/integration.csv"));

    EXPECT_EQ(suite.total_tests, 2U);
    EXPECT_GE(suite.passed, 1U);  // At minimum IT001 should pass
}

// ============================================================
// CRC32 validation
// ============================================================

TEST_F(TCUIntegrationTest, CRC32KnownVector) {
    // CRC-32 of "123456789" = 0xCBF43926
    const uint8_t data[] = {'1','2','3','4','5','6','7','8','9'};
    uint32_t crc = firmware::CRCValidator::crc32(data, sizeof(data));
    EXPECT_EQ(crc, 0xCBF43926U);
}

TEST_F(TCUIntegrationTest, CRC32EmptyData) {
    uint32_t crc = firmware::CRCValidator::crc32(nullptr, 0);
    EXPECT_EQ(crc, 0x00000000U);
}

TEST_F(TCUIntegrationTest, CRC32FileVerification) {
    // Write known data to temp file
    std::string path = tmp_dir + "/test.bin";
    const uint8_t data[] = {'1','2','3','4','5','6','7','8','9'};
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char*>(data), sizeof(data));
    f.close();

    EXPECT_TRUE(firmware::CRCValidator::verify_file_crc32(path, 0xCBF43926U));
    EXPECT_FALSE(firmware::CRCValidator::verify_file_crc32(path, 0x12345678U));
}

// ============================================================
// vcan0 CAN integration test (skipped if not available)
// ============================================================

TEST_F(TCUIntegrationTest, CANOpenAndSendOnVcan0) {
    if (!vcan_available) { GTEST_SKIP() << "vcan0 not available"; }

    ASSERT_TRUE(can_mgr->open());
    ASSERT_TRUE(can_mgr->start());

    std::atomic<bool> rx_ok{false};
    can_mgr->register_rx_callback([&](const can::CANFrame& f) {
        if (f.id == 0x789) { rx_ok = true; }
    });

    uint8_t data[] = {0xAA, 0xBB, 0xCC};
    EXPECT_TRUE(can_mgr->transmit(0x789, data, 3));

    auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(500);
    while (!rx_ok && std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    can_mgr->stop();
    can_mgr->close();

    EXPECT_TRUE(rx_ok.load());
}
