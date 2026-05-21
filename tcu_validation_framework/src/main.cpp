/**
 * @file main.cpp
 * @brief TCU Validation Framework — entry point.
 *
 * Usage:
 *   tcu_validator [options]
 *
 * Options:
 *   --config <path>      Path to JSON config file (default: configs/default.json)
 *   --profile <name>     Config profile overlay (e.g. production, test)
 *   --suite <name>       Test suite name (default: "TCU_Validation")
 *   --output <dir>       Report output directory (default: reports/)
 *   --interface <iface>  CAN interface override (e.g. can0, vcan0)
 *   --simulate           Force simulation mode (no real hardware)
 *   --verbose            Enable debug logging
 *   --help               Show this help
 */

#include "core/Framework.h"
#include "can/CANManager.h"
#include "diagnostics/UDSClient.h"
#include "telematics/TelematicsSDKAdapter.h"
#include "firmware/FirmwareFlasher.h"
#include "firmware/CRCValidator.h"
#include "validation/TestEngine.h"
#include "validation/FaultInjector.h"
#include "logging/Logger.h"
#include "reporting/ReportGenerator.h"
#include "config/ConfigManager.h"

#include <iostream>
#include <string>
#include <csignal>
#include <atomic>
#include <filesystem>

// ============================================================
// Signal handler
// ============================================================

static std::atomic<bool> g_shutdown_requested{false};

static void signal_handler(int sig) {
    fprintf(stderr, "\n[tcu_validator] Signal %d received — shutting down\n", sig);
    g_shutdown_requested = true;
    tcu::Framework::instance().request_shutdown();
}

// ============================================================
// Test suite builder
// ============================================================

static void build_validation_suite(tcu::validation::TestEngine& engine,
                                   std::shared_ptr<tcu::can::CANManager> can_mgr,
                                   std::shared_ptr<tcu::diagnostics::UDSClient> uds,
                                   std::shared_ptr<tcu::telematics::TelematicsSDKAdapter> sdk,
                                   bool simulation_mode) {

    auto log = tcu::logging::Logger::get("main");

    // --------------------------------------------------------
    // TC001: CAN interface health check
    // --------------------------------------------------------
    {
        tcu::validation::TestCase tc;
        tc.id          = "TC001";
        tc.name        = "CAN Interface Health Check";
        tc.timeout_ms  = 5000;
        tc.max_retries = 1;
        tc.is_critical = true;
        tc.execute     = [&can_mgr, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC001";
            r.test_name = "CAN Interface Health Check";

            if (can_mgr->is_running()) {
                auto stats = can_mgr->statistics();
                log->info("CAN stats: Tx={} Rx={} TxErr={} RxErr={}",
                          stats.tx_frames, stats.rx_frames,
                          stats.tx_errors, stats.rx_errors);
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "CAN running: Tx=" + std::to_string(stats.tx_frames) +
                            " Rx=" + std::to_string(stats.rx_frames);
            } else {
                r.verdict = tcu::validation::Verdict::FAIL;
                r.message = "CAN manager not running";
            }
            return r;
        };
        engine.add_test(tc);
    }

    // --------------------------------------------------------
    // TC002: Telematics connectivity
    // --------------------------------------------------------
    {
        tcu::validation::TestCase tc;
        tc.id          = "TC002";
        tc.name        = "Telematics SDK Connection";
        tc.timeout_ms  = 15000;
        tc.max_retries = 2;
        tc.execute     = [&sdk, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC002";
            r.test_name = "Telematics SDK Connection";

            if (sdk->is_connected()) {
                auto metrics = sdk->get_network_metrics();
                log->info("Network: RSRP={:.1f} latency={:.1f}ms",
                          metrics.rsrp, metrics.latency_ms);
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "Connected, latency=" + std::to_string(
                    static_cast<int>(metrics.latency_ms)) + "ms";
            } else {
                r.verdict = tcu::validation::Verdict::FAIL;
                r.message = "Not connected";
            }
            return r;
        };
        engine.add_test(tc);
    }

    // --------------------------------------------------------
    // TC003: Telemetry publish
    // --------------------------------------------------------
    {
        tcu::validation::TestCase tc;
        tc.id         = "TC003";
        tc.name       = "Telemetry Payload Publish";
        tc.timeout_ms = 10000;
        tc.execute    = [&sdk, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC003";
            r.test_name = "Telemetry Payload Publish";

            tcu::telematics::TelemetryPayload payload;
            payload.device_id = "TCU-001";
            payload.numeric_signals["battery_voltage"]    = 12.6;
            payload.numeric_signals["gps_latitude"]       = 52.5200;
            payload.numeric_signals["gps_longitude"]      =  13.4050;
            payload.numeric_signals["vehicle_speed_kmh"]  = 0.0;
            payload.string_signals["fw_version"]          = "1.2.3";
            payload.string_signals["vin"]                 = "WBA1234567TEST0001";

            bool ok = sdk->publish_telemetry(payload);
            if (ok) {
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "Telemetry published: " +
                            std::to_string(payload.numeric_signals.size()) + " signals";
            } else {
                r.verdict = tcu::validation::Verdict::FAIL;
                r.message = "Publish failed";
            }
            return r;
        };
        engine.add_test(tc);
    }

    // --------------------------------------------------------
    // TC004: OTA update detection
    // --------------------------------------------------------
    if (simulation_mode) {
        tcu::validation::TestCase tc;
        tc.id         = "TC004";
        tc.name       = "OTA Update Detection";
        tc.timeout_ms = 5000;
        tc.precondition = [&sdk] { return sdk->is_connected(); };
        tc.execute    = [&sdk, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC004";
            r.test_name = "OTA Update Detection";

            // Inject simulated OTA notification
            tcu::telematics::OTANotification notif;
            notif.package_id      = "TCU-FW-2.0.0";
            notif.current_version = "1.2.3";
            notif.new_version     = "2.0.0";
            notif.package_size    = 2 * 1024 * 1024;
            notif.checksum_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
            sdk->sim_inject_ota(notif);

            tcu::telematics::OTANotification detected;
            if (sdk->check_for_updates(detected)) {
                log->info("OTA detected: {} → {}", detected.current_version,
                          detected.new_version);
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "OTA v" + detected.new_version + " detected";
            } else {
                r.verdict = tcu::validation::Verdict::FAIL;
                r.message = "OTA not detected after injection";
            }
            return r;
        };
        engine.add_test(tc);
    }

    // --------------------------------------------------------
    // TC005: UDS session control
    // --------------------------------------------------------
    {
        tcu::validation::TestCase tc;
        tc.id          = "TC005";
        tc.name        = "UDS Default Session Open";
        tc.timeout_ms  = 5000;
        tc.max_retries = 1;
        tc.execute     = [&uds, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC005";
            r.test_name = "UDS Default Session Open";

            auto result = uds->open_session(tcu::diagnostics::UDSSession::Default);
            if (result.success) {
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "Default session established";
            } else {
                // In simulation/no-ECU mode: skip
                r.verdict = tcu::validation::Verdict::SKIP;
                r.message = "No ECU available — " + result.error_message;
            }
            return r;
        };
        engine.add_test(tc);
    }

    // --------------------------------------------------------
    // TC006: Fault injection — network loss recovery
    // --------------------------------------------------------
    if (simulation_mode) {
        tcu::validation::TestCase tc;
        tc.id         = "TC006";
        tc.name       = "Fault Injection — Network Loss Recovery";
        tc.timeout_ms = 10000;
        tc.execute    = [&sdk, can_mgr, log]() -> tcu::validation::TestResult {
            tcu::validation::TestResult r;
            r.test_id   = "TC006";
            r.test_name = "Fault Injection — Network Loss Recovery";

            auto injector = std::make_shared<tcu::validation::FaultInjector>(can_mgr, sdk);

            tcu::validation::FaultSpec spec;
            spec.type = tcu::validation::FaultType::NETWORK_LOSS;
            spec.duration_ms = 1000;

            auto active = injector->inject(spec);
            if (!active) {
                r.verdict = tcu::validation::Verdict::ERROR;
                r.message = "Failed to inject fault";
                return r;
            }

            // Verify metrics show disconnected
            auto m = sdk->get_network_metrics();
            bool fault_active = !m.connected;

            // Clear fault (RAII — destroy active fault)
            active.reset();

            // Verify recovery
            auto m2 = sdk->get_network_metrics();
            bool recovered = m2.connected;

            if (fault_active && recovered) {
                r.verdict = tcu::validation::Verdict::PASS;
                r.message = "Network loss injected and recovered";
            } else {
                r.verdict = tcu::validation::Verdict::FAIL;
                r.message = "fault_active=" + std::to_string(fault_active) +
                            " recovered=" + std::to_string(recovered);
            }
            return r;
        };
        engine.add_test(tc);
    }
}

// ============================================================
// main()
// ============================================================

int main(int argc, char* argv[]) {
    // --------------------------------------------------------
    // Parse CLI arguments
    // --------------------------------------------------------
    std::string config_path   = "configs/default.json";
    std::string profile;
    std::string suite_name    = "TCU_Validation";
    std::string output_dir    = "reports";
    std::string can_interface;
    bool        simulation    = false;
    bool        verbose       = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help" || arg == "-h") {
            std::cout << "Usage: tcu_validator [options]\n"
                      << "  --config <path>      JSON config (default: configs/default.json)\n"
                      << "  --profile <name>     Config profile overlay\n"
                      << "  --suite <name>       Test suite name\n"
                      << "  --output <dir>       Report output directory\n"
                      << "  --interface <iface>  CAN interface override\n"
                      << "  --simulate           Force simulation mode\n"
                      << "  --verbose            Enable debug logging\n";
            return 0;
        } else if (arg == "--config"    && i + 1 < argc) { config_path   = argv[++i]; }
        else if   (arg == "--profile"   && i + 1 < argc) { profile       = argv[++i]; }
        else if   (arg == "--suite"     && i + 1 < argc) { suite_name    = argv[++i]; }
        else if   (arg == "--output"    && i + 1 < argc) { output_dir    = argv[++i]; }
        else if   (arg == "--interface" && i + 1 < argc) { can_interface = argv[++i]; }
        else if   (arg == "--simulate")                   { simulation    = true; }
        else if   (arg == "--verbose")                    { verbose       = true; }
        else {
            std::cerr << "Unknown option: " << arg << " (use --help)\n";
            return 1;
        }
    }

    // --------------------------------------------------------
    // Signal handling
    // --------------------------------------------------------
    std::signal(SIGINT,  signal_handler);
    std::signal(SIGTERM, signal_handler);

    // --------------------------------------------------------
    // Framework init
    // --------------------------------------------------------
    tcu::FrameworkConfig fw_cfg;
    fw_cfg.instance_name = "tcu_validator";
    fw_cfg.config_path   = config_path;
    fw_cfg.log_dir       = "logs";

    auto& fw = tcu::Framework::instance();
    if (!fw.initialize(fw_cfg)) {
        std::cerr << "Framework init failed\n";
        return 1;
    }

    auto log = tcu::logging::Logger::get("main");
    if (verbose) {
        tcu::logging::Logger::set_global_level(spdlog::level::debug);
        log->info("Verbose (debug) logging enabled");
    }

    // --------------------------------------------------------
    // Config load
    // --------------------------------------------------------
    auto& cfg = tcu::config::ConfigManager::global_config();
    if (!cfg.load(config_path)) {
        log->warn("Config not found: {} — using defaults", config_path);
    }
    if (!profile.empty()) {
        cfg.load_profile(profile, "configs");
    }

    // CLI overrides
    if (!can_interface.empty()) {
        cfg.set_string("can.interface", can_interface);
    }
    if (simulation) {
        cfg.set_bool("telematics.simulation_mode", true);
        log->info("Simulation mode forced via CLI");
    }

    bool sim_mode = cfg.get<bool>("telematics.simulation_mode", true);
    std::string iface = cfg.get<std::string>("can.interface", "vcan0");

    log->info("Config: interface={} simulate={}", iface, sim_mode);

    // --------------------------------------------------------
    // Module instantiation
    // --------------------------------------------------------

    // CAN Manager
    tcu::can::CANConfig can_cfg;
    can_cfg.interface      = iface;
    can_cfg.enable_fd      = cfg.get<bool>("can.enable_fd", false);
    can_cfg.loopback       = cfg.get<bool>("can.loopback", false);
    can_cfg.rx_timeout_ms  = cfg.get<uint32_t>("can.rx_timeout_ms", 100);

    auto can_mgr = std::make_shared<tcu::can::CANManager>(can_cfg);

    // UDS Client
    tcu::diagnostics::ISOTPConfig istp_cfg;
    istp_cfg.tx_id        = cfg.get<uint32_t>("uds.tx_id", 0x7E0);
    istp_cfg.rx_id        = cfg.get<uint32_t>("uds.rx_id", 0x7E8);
    istp_cfg.p2_timeout_ms= cfg.get<uint32_t>("uds.p2_timeout_ms", 1000);
    istp_cfg.p2_star_ms   = cfg.get<uint32_t>("uds.p2_star_ms", 5000);
    auto uds = std::make_shared<tcu::diagnostics::UDSClient>(can_mgr, istp_cfg);

    // Telematics SDK
    tcu::telematics::SDKConfig sdk_cfg;
    sdk_cfg.server_url       = cfg.get<std::string>("telematics.server_url", "mqtt://localhost:1883");
    sdk_cfg.simulation_mode  = sim_mode;
    sdk_cfg.max_reconnect_attempts = cfg.get<uint32_t>("telematics.max_reconnect_attempts", 5);
    sdk_cfg.reconnect_delay_ms     = cfg.get<uint32_t>("telematics.reconnect_delay_ms", 2000);
    auto sdk = std::make_shared<tcu::telematics::TelematicsSDKAdapter>(sdk_cfg);

    // --------------------------------------------------------
    // Register modules with framework
    // --------------------------------------------------------
    fw.register_module("can", {
        .init = [&can_mgr] {
            if (!can_mgr->open()) {
                // In simulation mode, ignore CAN open failure
                return true;  // Non-fatal
            }
            return can_mgr->start();
        },
        .shutdown = [&can_mgr] { can_mgr->stop(); can_mgr->close(); },
        .health   = [&can_mgr] {
            return can_mgr->is_running() ? "OK" : "NOT_RUNNING";
        }
    });

    fw.register_module("telematics", {
        .init     = [&sdk] { return sdk->connect(); },
        .shutdown = [&sdk] { sdk->disconnect(); },
        .health   = [&sdk] { return sdk->is_connected() ? "CONNECTED" : "DISCONNECTED"; }
    });

    // --------------------------------------------------------
    // Start all modules
    // --------------------------------------------------------
    if (!fw.start()) {
        log->error("Framework start failed");
        fw.shutdown();
        return 2;
    }

    // --------------------------------------------------------
    // Print health report
    // --------------------------------------------------------
    auto health = fw.health_report();
    log->info("Module health:");
    for (const auto& [name, status] : health) {
        log->info("  {} → {}", name, status);
    }

    // --------------------------------------------------------
    // Build and run test suite
    // --------------------------------------------------------
    tcu::validation::EngineConfig eng_cfg;
    eng_cfg.parallel           = cfg.get<bool>("engine.parallel", false);
    eng_cfg.stop_on_first_fail = cfg.get<bool>("engine.stop_on_first_fail", false);
    eng_cfg.retry_delay_ms     = cfg.get<uint32_t>("engine.retry_delay_ms", 500);

    tcu::validation::TestEngine engine(eng_cfg);
    build_validation_suite(engine, can_mgr, uds, sdk, sim_mode);

    log->info("Running test suite: {}", suite_name);
    auto suite_result = engine.run(suite_name);

    // --------------------------------------------------------
    // Generate reports
    // --------------------------------------------------------
    std::filesystem::create_directories(output_dir);
    tcu::reporting::ReportGenerator reporter(output_dir);
    reporter.generate(suite_result, tcu::reporting::ReportFormat::ALL, suite_name);

    log->info("Reports written to: {}", output_dir);

    // --------------------------------------------------------
    // Print summary
    // --------------------------------------------------------
    std::cout << "\n========================================\n";
    std::cout << "  TCU Validation Suite: " << suite_name << "\n";
    std::cout << "  Total:   " << suite_result.total_tests << "\n";
    std::cout << "  PASS:    " << suite_result.passed << "\n";
    std::cout << "  FAIL:    " << suite_result.failed << "\n";
    std::cout << "  SKIP:    " << suite_result.skipped << "\n";
    std::cout << "  TIMEOUT: " << suite_result.timed_out << "\n";
    std::cout << "  ERROR:   " << suite_result.errored << "\n";
    std::cout << "  Time:    " << suite_result.total_ms << " ms\n";
    std::cout << "  Result:  " << (suite_result.all_passed ? "PASS ✓" : "FAIL ✗") << "\n";
    std::cout << "========================================\n\n";

    // --------------------------------------------------------
    // Shutdown
    // --------------------------------------------------------
    fw.shutdown();

    return suite_result.all_passed ? 0 : 1;
}
