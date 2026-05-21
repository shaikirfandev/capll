/**
 * @file main.cpp
 * @brief Bluetooth Firmware — Application Entry Point
 *
 * Bootstrap sequence for a production-representative BT stack on a
 * simulated automotive-grade embedded target (Qualcomm QCC5171 / TI CC2642R).
 *
 * Production mapping:
 *   BluetoothController  →  HCI UART to BT SoC
 *   UartDriver           →  LPUART0 DMA at 3 Mbaud (QCC5171 HCI)
 *   SpiDriver            →  DSPI0 for audio codec SPI config
 *   GpioDriver           →  nRF GPIO for BT_RESET, BT_WAKE
 *   PowerManager         →  PMIC (DA9210) I2C control
 *   EventBus             →  IPC dispatcher shared with RTOS tasks
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <cstdlib>

// Common
#include "common/Logger.hpp"

// BT stack
#include "bt/BluetoothController.hpp"
#include "bt/EventBus.hpp"
#include "bt/ConnectionStateMachine.hpp"
#include "bt/GattServer.hpp"
#include "bt/BleAdvertiser.hpp"
#include "bt/PairingManager.hpp"
#include "bt/SecurityManager.hpp"
#include "bt/BleScanner.hpp"
#include "bt/profiles/A2dpSimulator.hpp"
#include "bt/profiles/HfpSimulator.hpp"

// HAL
#include "hal/UartDriver.hpp"
#include "hal/SpiDriver.hpp"
#include "hal/GpioDriver.hpp"
#include "hal/PowerManager.hpp"

// RTOS
#include "rtos/StdThreadTask.hpp"
#include "rtos/StdMutex.hpp"
#include "rtos/StdQueue.hpp"
#include "rtos/StdSemaphore.hpp"

// App
#include "app/ConnectionManager.hpp"
#include "app/OtaManager.hpp"
#include "app/DiagnosticsModule.hpp"

using namespace std::chrono_literals;
static constexpr const char *MAIN_TAG = "Main";

// ── GATT UUIDs ────────────────────────────────────────────────────────────────
static constexpr bt::Uuid16 SVC_DEVICE_INFO   {0x180AU};
static constexpr bt::Uuid16 CHAR_FW_REVISION  {0x2A26U};
static constexpr bt::Uuid16 SVC_BATTERY       {0x180FU};
static constexpr bt::Uuid16 CHAR_BATTERY_LEVEL{0x2A19U};
static constexpr bt::Uuid16 SVC_HRM           {0x180DU};
static constexpr bt::Uuid16 CHAR_HRM_MEAS     {0x2A37U};

// ── Demo scenario ─────────────────────────────────────────────────────────────
static void run_demo(bt::app::ConnectionManager &conn_mgr,
                     bt::app::OtaManager        &ota_mgr,
                     bt::app::DiagnosticsModule &diag,
                     bt::BleScanner             &scanner,
                     bt::GattServer             &gatt,
                     bt::PairingManager         &pairing) {

    BT_LOG_INFO(MAIN_TAG, "--- Demo scenario starting ---");

    // 1. Start advertising
    BT_LOG_INFO(MAIN_TAG, "Step 1: Start advertising");
    conn_mgr.start_advertising();

    // 2. Register connection callbacks
    conn_mgr.on_connected([&diag, &pairing](bt::ConnHandle h, const bt::BdAddr &addr) {
        BT_LOG_INFO(MAIN_TAG, ">> CONNECTED handle=0x{:04X} peer={}", h, bt::format_bdaddr(addr));
        diag.record_event("ConnMgr", "Connected to " + bt::format_bdaddr(addr));
        // Auto-initiate pairing for new connections
        pairing.initiate_pairing(h, bt::PairingMethod::NUMERIC_COMPARISON);
    });

    conn_mgr.on_disconnected([&diag](bt::ConnHandle h, uint8_t reason) {
        BT_LOG_INFO(MAIN_TAG, ">> DISCONNECTED handle=0x{:04X} reason=0x{:02X}", h, reason);
        diag.record_event("ConnMgr", "Disconnected handle=" + std::to_string(h));
    });

    // 3. OTA setup
    BT_LOG_INFO(MAIN_TAG, "Step 2: Configure OTA callbacks");
    ota_mgr.on_progress([](uint32_t rx, uint32_t total) {
        const uint8_t pct = static_cast<uint8_t>((rx * 100U) / total);
        BT_LOG_INFO(MAIN_TAG, "  OTA progress: {}% ({}/{})", pct, rx, total);
    });
    ota_mgr.on_complete([&diag](bool ok, const std::string &msg) {
        BT_LOG_INFO(MAIN_TAG, "  OTA complete: ok={} msg={}", ok, msg);
        diag.record_event("OTA", msg);
    });

    // 4. Simulate an OTA transfer
    BT_LOG_INFO(MAIN_TAG, "Step 3: Simulate OTA firmware update");
    const uint8_t fake_fw[16] = {0xDE, 0xAD, 0xBE, 0xEF,
                                  0xCA, 0xFE, 0xBA, 0xBE,
                                  0x01, 0x02, 0x03, 0x04,
                                  0x05, 0x06, 0x07, 0x08};
    // Pre-compute expected CRC
    uint32_t expected_crc = 0;
    for (const uint8_t b : fake_fw) {
        expected_crc ^= b;  // Simplified for demo
    }
    ota_mgr.start_ota(0x0001U, 16U, 0U);  // CRC=0 since simplified hash
    ota_mgr.write_chunk(fake_fw, 16U);

    // 5. GATT notify simulation
    BT_LOG_INFO(MAIN_TAG, "Step 4: Simulate GATT Battery Level notification");
    const uint8_t battery_level = 87U;
    gatt.set_value(0x0020U, &battery_level, 1U);  // Hypothetical handle
    gatt.notify(0x0001U, 0x0020U, &battery_level, 1U);

    // 6. BLE scan for 1 second
    BT_LOG_INFO(MAIN_TAG, "Step 5: BLE scan for nearby devices (1s)");
    scanner.set_scan_callback([&diag](const bt::BdAddr &addr, int8_t rssi,
                                       const bt::AdvData &/*data*/) {
        BT_LOG_INFO(MAIN_TAG, "  Scan result: {} RSSI={}dBm",
                    bt::format_bdaddr(addr), rssi);
        diag.record_event("Scanner", "Found " + bt::format_bdaddr(addr));
    });
    scanner.set_rssi_filter(-80);
    scanner.start_scan();
    std::this_thread::sleep_for(1s);
    scanner.stop_scan();

    // 7. Print diagnostics report
    BT_LOG_INFO(MAIN_TAG, "Step 6: Diagnostics report\n{}", diag.generate_report());

    BT_LOG_INFO(MAIN_TAG, "--- Demo scenario complete ---");
}

// ── Main ─────────────────────────────────────────────────────────────────────
int main() {
    // ── Logger init ──────────────────────────────────────────────────────────
    bt::Logger::get().init("bt_firmware.log");
    BT_LOG_INFO(MAIN_TAG, "Bluetooth Firmware v2.1.0 starting");

    // ── HAL layer ────────────────────────────────────────────────────────────
    bt::hal::UartDriver    uart;
    bt::hal::SpiDriver     spi;
    bt::hal::GpioDriver    gpio;
    bt::hal::PowerManager  power;

    bt::hal::UartConfig uart_cfg{};
    uart_cfg.baud_rate  = 3000000U;
    uart_cfg.data_bits  = 8U;
    uart_cfg.stop_bits  = bt::hal::UartStopBit::ONE;
    uart_cfg.parity     = bt::hal::UartParity::NONE;
    uart_cfg.flow_ctrl  = true;
    uart.init(uart_cfg);

    bt::hal::SpiConfig spi_cfg{};
    spi_cfg.freq_hz = 8000000U;
    spi_cfg.mode    = bt::hal::SpiMode::MODE_0;
    spi.init(spi_cfg);

    // BT_RESET pin = GPIO 4, BT_WAKE = GPIO 5
    gpio.configure(4U, bt::hal::GpioDirn::OUTPUT, bt::hal::GpioPull::NONE);
    gpio.configure(5U, bt::hal::GpioDirn::OUTPUT, bt::hal::GpioPull::NONE);
    gpio.write(4U, true);  // Deassert reset

    // ── BT Stack layer ──────────────────────────────────────────────────────
    auto &controller = bt::BluetoothController::instance();
    controller.initialise(bt::BtMode::BLE_ONLY);
    controller.set_device_name("BT-Firmware-Demo");

    const auto pub_addr = controller.get_public_address();
    BT_LOG_INFO(MAIN_TAG, "BT Public Address: {}", bt::format_bdaddr(pub_addr));

    bt::EventBus              event_bus;
    bt::GattServer            gatt_server;
    bt::PairingManager        pairing_mgr;
    bt::SecurityManager       security_mgr;
    bt::BleAdvertiser         advertiser(&controller);
    bt::BleScanner            scanner(&controller);
    bt::ConnectionStateMachine csm;

    // ── Register GATT Services ───────────────────────────────────────────────
    // Device Information Service
    bt::GattServiceDef dev_info_svc{};
    dev_info_svc.uuid16  = SVC_DEVICE_INFO;
    dev_info_svc.primary = true;
    dev_info_svc.chars.push_back({CHAR_FW_REVISION,
        bt::GattProp::READ,
        bt::GattPerm::READ,
        {0x32, 0x2E, 0x31, 0x2E, 0x30}});  // "2.1.0" ASCII
    gatt_server.add_service(dev_info_svc);

    // Battery Service
    bt::GattServiceDef battery_svc{};
    battery_svc.uuid16  = SVC_BATTERY;
    battery_svc.primary = true;
    battery_svc.chars.push_back({CHAR_BATTERY_LEVEL,
        static_cast<bt::GattProp>(
            static_cast<uint8_t>(bt::GattProp::READ) |
            static_cast<uint8_t>(bt::GattProp::NOTIFY)),
        bt::GattPerm::READ,
        {0x64U}});  // 100%
    gatt_server.add_service(battery_svc);

    // ── App layer ────────────────────────────────────────────────────────────
    bt::app::ConnectionManager conn_mgr(&controller);
    bt::app::OtaManager        ota_mgr;
    bt::app::DiagnosticsModule diag;

    // ── Subscribe EventBus for diagnostic counters ───────────────────────────
    event_bus.subscribe([&diag](const bt::BtEvent &evt) {
        std::visit([&diag](const auto &e) {
            using T = std::decay_t<decltype(e)>;
            if constexpr (std::is_same_v<T, bt::EvtError>) {
                diag.record_event("EventBus", "Error: " + bt::bt_error_str(e.error));
            }
        }, evt);
    });

    // ── Profiles ─────────────────────────────────────────────────────────────
    bt::profiles::A2dpSimulator a2dp;
    bt::profiles::HfpSimulator  hfp;
    hfp.set_at_callback([](const std::string &resp) {
        BT_LOG_DEBUG(MAIN_TAG, "HFP AT response: {}", resp);
    });

    // ── Run demo scenario ─────────────────────────────────────────────────────
    run_demo(conn_mgr, ota_mgr, diag, scanner, gatt_server, pairing_mgr);

    // ── Shutdown ──────────────────────────────────────────────────────────────
    BT_LOG_INFO(MAIN_TAG, "Shutting down Bluetooth stack...");
    conn_mgr.stop_advertising();
    controller.shutdown();
    power.power_down_radio();

    BT_LOG_INFO(MAIN_TAG, "Shutdown complete. Goodbye.");
    return EXIT_SUCCESS;
}
