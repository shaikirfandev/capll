/**
 * @file test_bt_stack_integration.cpp
 * @brief Full BT stack integration test: init → advertise → scan → GATT
 */
#include <gtest/gtest.h>
#include "bt/BluetoothController.hpp"
#include "bt/EventBus.hpp"
#include "bt/GattServer.hpp"
#include "bt/BleAdvertiser.hpp"
#include "bt/BleScanner.hpp"
#include "bt/PairingManager.hpp"
#include "common/Logger.hpp"
#include <chrono>
#include <thread>
#include <atomic>

using namespace bt;
using namespace std::chrono_literals;

class BtStackIntegration : public ::testing::Test {
protected:
    void SetUp() override {
        Logger::get().init("");  // No file output in tests
        auto &ctrl = BluetoothController::instance();
        ctrl.initialise(BtMode::DUAL_MODE);
        ctrl.set_device_name("IntegTest");
    }

    void TearDown() override {
        BluetoothController::instance().shutdown();
    }
};

TEST_F(BtStackIntegration, InitialisesAndGetAddress) {
    auto &ctrl = BluetoothController::instance();
    const BdAddr addr = ctrl.get_public_address();
    // Address should not be all-zero in simulation
    const bool all_zero = std::all_of(addr.begin(), addr.end(), [](uint8_t b){ return b == 0; });
    EXPECT_FALSE(all_zero);
}

TEST_F(BtStackIntegration, AdvertiserStartStop) {
    auto &ctrl = BluetoothController::instance();
    BleAdvertiser adv(&ctrl);

    AdvParams params{};
    params.interval_min_ms = 100U;
    params.interval_max_ms = 150U;
    AdvData adv_data{}, scan_rsp{};

    EXPECT_EQ(adv.start(params, adv_data, scan_rsp), BtError::OK);
    EXPECT_TRUE(adv.is_advertising());
    EXPECT_EQ(adv.stop(), BtError::OK);
    EXPECT_FALSE(adv.is_advertising());
}

TEST_F(BtStackIntegration, ScannerReceivesSimulatedResults) {
    auto &ctrl = BluetoothController::instance();
    BleScanner scanner(&ctrl);

    std::atomic<int> result_count{0};
    scanner.set_scan_callback([&result_count](const BdAddr &, int8_t, const AdvData &) {
        result_count++;
    });
    scanner.set_rssi_filter(-100);  // Accept all
    scanner.start_scan();

    std::this_thread::sleep_for(700ms);  // Wait for 2+ simulated results (300ms each)
    scanner.stop_scan();

    EXPECT_GE(result_count.load(), 1);
}

TEST_F(BtStackIntegration, GattServiceRegistration) {
    GattServer gatt;
    GattServiceDef svc{};
    svc.uuid16  = Uuid16{0x180AU};
    svc.primary = true;
    svc.chars.push_back({Uuid16{0x2A26U}, GattProp::READ, GattPerm::READ,
                          {0x32, 0x2E, 0x31}});

    EXPECT_EQ(gatt.add_service(svc), BtError::OK);
    const auto val = gatt.get_value(0x0002U);
    EXPECT_FALSE(val.empty());
}

TEST_F(BtStackIntegration, EventBusPublishReceive) {
    EventBus bus;
    std::atomic<int> evts{0};

    bus.subscribe([&evts](const BtEvent &ev) {
        if (std::holds_alternative<EvtConnected>(ev)) { evts++; }
    });

    bus.publish(EvtConnected{0x0001, {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}});
    EXPECT_EQ(evts.load(), 1);
}
