/**
 * @file test_can_manager.cpp
 * @brief Unit tests for CANManager using mock socket interface.
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include "can/CANManager.h"
#include "logging/Logger.h"

#include <atomic>
#include <chrono>
#include <thread>

using namespace tcu::can;
using namespace testing;

// ============================================================
// Test fixture
// ============================================================

class CANManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        tcu::logging::LogConfig cfg;
        cfg.log_dir       = "/tmp/tcu_test_logs";
        cfg.enable_console = false;
        tcu::logging::Logger::init(cfg);
    }

    void TearDown() override {
        tcu::logging::Logger::flush_all();
    }

    CANConfig make_vcan_config() {
        CANConfig cfg;
        cfg.interface     = "vcan0";
        cfg.enable_fd     = false;
        cfg.loopback      = true;
        cfg.rx_timeout_ms = 100;
        return cfg;
    }
};

// ============================================================
// Construction tests
// ============================================================

TEST_F(CANManagerTest, ConstructionDoesNotThrow) {
    EXPECT_NO_THROW({
        CANManager mgr(make_vcan_config());
    });
}

TEST_F(CANManagerTest, InitialStateNotRunning) {
    CANManager mgr(make_vcan_config());
    EXPECT_FALSE(mgr.is_running());
}

TEST_F(CANManagerTest, InterfaceNameReturned) {
    CANManager mgr(make_vcan_config());
    EXPECT_EQ(mgr.interface_name(), "vcan0");
}

// ============================================================
// Statistics tests
// ============================================================

TEST_F(CANManagerTest, InitialStatisticsAreZero) {
    CANManager mgr(make_vcan_config());
    auto stats = mgr.statistics();
    EXPECT_EQ(stats.tx_frames,     0UL);
    EXPECT_EQ(stats.rx_frames,     0UL);
    EXPECT_EQ(stats.tx_errors,     0UL);
    EXPECT_EQ(stats.rx_errors,     0UL);
    EXPECT_EQ(stats.bus_off_events,0UL);
}

TEST_F(CANManagerTest, ResetStatisticsClearsAll) {
    CANManager mgr(make_vcan_config());
    mgr.reset_statistics();
    auto stats = mgr.statistics();
    EXPECT_EQ(stats.tx_frames, 0UL);
    EXPECT_EQ(stats.rx_frames, 0UL);
}

// ============================================================
// Callback registration
// ============================================================

TEST_F(CANManagerTest, RegisterRxCallbackReturnsHandle) {
    CANManager mgr(make_vcan_config());
    bool called = false;
    auto handle = mgr.register_rx_callback([&called](const CANFrame&) {
        called = true;
    });
    EXPECT_GE(handle, 0);
}

TEST_F(CANManagerTest, UnregisterCallbackDoesNotThrow) {
    CANManager mgr(make_vcan_config());
    auto h = mgr.register_rx_callback([](const CANFrame&){});
    EXPECT_NO_THROW(mgr.unregister_callback(h));
}

TEST_F(CANManagerTest, MultipleCallbacksCanBeRegistered) {
    CANManager mgr(make_vcan_config());
    auto h1 = mgr.register_rx_callback([](const CANFrame&){});
    auto h2 = mgr.register_rx_callback([](const CANFrame&){});
    auto h3 = mgr.register_error_callback([](const CANError&){});
    EXPECT_NE(h1, h2);
    EXPECT_NE(h2, h3);
}

// ============================================================
// CANFrame construction
// ============================================================

TEST_F(CANManagerTest, CANFrameDefaultValues) {
    CANFrame f;
    EXPECT_EQ(f.id, 0U);
    EXPECT_EQ(f.dlc, 0U);
    EXPECT_FALSE(f.is_extended);
    EXPECT_FALSE(f.is_remote);
    EXPECT_FALSE(f.is_fd);
}

TEST_F(CANManagerTest, CANFrameSetData) {
    CANFrame f;
    f.id  = 0x123;
    f.dlc = 4;
    f.data[0] = 0xDE;
    f.data[1] = 0xAD;
    f.data[2] = 0xBE;
    f.data[3] = 0xEF;
    EXPECT_EQ(f.id,     0x123U);
    EXPECT_EQ(f.dlc,    4U);
    EXPECT_EQ(f.data[0], 0xDE);
    EXPECT_EQ(f.data[3], 0xEF);
}

// ============================================================
// vcan0 integration tests (conditional)
// ============================================================

class CANManagerVcanTest : public CANManagerTest {
protected:
    bool vcan_available = false;

    void SetUp() override {
        CANManagerTest::SetUp();
        // Check if vcan0 exists
        vcan_available = (system("ip link show vcan0 > /dev/null 2>&1") == 0);
    }
};

TEST_F(CANManagerVcanTest, OpenSucceedsOnVcan0) {
    if (!vcan_available) { GTEST_SKIP() << "vcan0 not available"; }

    CANManager mgr(make_vcan_config());
    EXPECT_TRUE(mgr.open());
    mgr.close();
}

TEST_F(CANManagerVcanTest, StartAndStopRxThread) {
    if (!vcan_available) { GTEST_SKIP() << "vcan0 not available"; }

    CANManager mgr(make_vcan_config());
    ASSERT_TRUE(mgr.open());
    EXPECT_TRUE(mgr.start());
    EXPECT_TRUE(mgr.is_running());
    mgr.stop();
    EXPECT_FALSE(mgr.is_running());
    mgr.close();
}

TEST_F(CANManagerVcanTest, LoopbackTransmitReceive) {
    if (!vcan_available) { GTEST_SKIP() << "vcan0 not available"; }

    CANConfig cfg = make_vcan_config();
    cfg.loopback = true;
    CANManager mgr(cfg);
    ASSERT_TRUE(mgr.open());
    ASSERT_TRUE(mgr.start());

    std::atomic<bool> received{false};
    std::atomic<uint32_t> rx_id{0};

    mgr.register_rx_callback([&](const CANFrame& f) {
        rx_id    = f.id;
        received = true;
    });

    // Transmit a frame
    uint8_t data[] = {0x01, 0x02, 0x03};
    EXPECT_TRUE(mgr.transmit(0x456, data, 3));

    // Wait up to 500ms for Rx
    auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(500);
    while (!received && std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    mgr.stop();
    mgr.close();

    EXPECT_TRUE(received.load());
    EXPECT_EQ(rx_id.load(), 0x456U);
}
