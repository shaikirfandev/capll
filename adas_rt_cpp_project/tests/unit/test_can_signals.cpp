/**
 * @file test_can_signals.cpp
 * @brief Unit tests for CAN signal encode/decode and SimHal.
 */

#include <gtest/gtest.h>
#include "../../src/hil_sil/can_bus_sim.hpp"

using namespace adas::hil;

// ─── Signal encoding round-trip ───────────────────────────────────────────────

TEST(CanSignalTest, EncodeDecodeEgoSpeed_RoundTrip) {
    CanFrame frame{};
    const float original = 27.78f;   // 100 km/h in m/s
    encodeSignal(frame, signals::EGO_SPEED, original);

    const float decoded = decodeSignal(frame, signals::EGO_SPEED);
    EXPECT_NEAR(decoded, original, signals::EGO_SPEED.scale)
        << "Decoded speed should match original within 1 LSB";
}

TEST(CanSignalTest, EncodeDecodeSteeringAngle_Signed) {
    CanFrame frame{};
    const float original = -0.35f;   // -20 degrees steering left
    encodeSignal(frame, signals::STEER_ANGLE, original);

    const float decoded = decodeSignal(frame, signals::STEER_ANGLE);
    EXPECT_NEAR(decoded, original, signals::STEER_ANGLE.scale * 2.f)
        << "Signed steering angle decode should preserve sign and magnitude";
}

TEST(CanSignalTest, MultipleSignalsInSameFrame) {
    CanFrame frame{};
    encodeSignal(frame, signals::THROTTLE,    0.75f);
    encodeSignal(frame, signals::BRAKE,       0.00f);
    encodeSignal(frame, signals::STEER_ANGLE, 0.12f);

    EXPECT_NEAR(decodeSignal(frame, signals::THROTTLE),    0.75f, 0.01f);
    EXPECT_NEAR(decodeSignal(frame, signals::BRAKE),       0.00f, 0.01f);
    EXPECT_NEAR(decodeSignal(frame, signals::STEER_ANGLE), 0.12f, 0.02f);
}

// ─── SimHal tests ─────────────────────────────────────────────────────────────

class SimHalTest : public ::testing::Test {
protected:
    void SetUp() override {
        hal_.open();
    }
    void TearDown() override {
        hal_.close();
    }
    SimHal hal_;
};

TEST_F(SimHalTest, TxFrameAppearsInTxLog) {
    CanFrame frame{};
    frame.id  = 0x200;
    frame.dlc = 4;
    hal_.txCan(frame);

    auto log = hal_.drainTxLog();
    ASSERT_EQ(log.size(), 1u);
    EXPECT_EQ(log[0].id, 0x200u);
}

TEST_F(SimHalTest, TxFrameEchoedToRxCallback) {
    bool callback_called = false;
    uint32_t received_id = 0;

    hal_.registerCanRxCallback([&](const CanFrame& f) {
        callback_called = true;
        received_id     = f.id;
    });

    CanFrame frame{};
    frame.id  = 0x100;
    frame.dlc = 2;
    hal_.txCan(frame);

    EXPECT_TRUE(callback_called)   << "RX callback must be called on Tx";
    EXPECT_EQ(received_id, 0x100u) << "Received ID must match transmitted ID";
}

TEST_F(SimHalTest, InjectFrameTriggersRxCallback) {
    int rx_count = 0;
    hal_.registerCanRxCallback([&](const CanFrame&) { ++rx_count; });

    CanFrame f1{}, f2{};
    f1.id = 0x300;
    f2.id = 0x400;
    hal_.injectFrame(f1);
    hal_.injectFrame(f2);

    EXPECT_EQ(rx_count, 2) << "Two injected frames should produce 2 RX callbacks";
}

TEST_F(SimHalTest, DrainTxLogClearsBuffer) {
    CanFrame frame{};
    frame.id = 0x500;
    hal_.txCan(frame);
    hal_.txCan(frame);

    auto first_drain  = hal_.drainTxLog();
    auto second_drain = hal_.drainTxLog();

    EXPECT_EQ(first_drain.size(),  2u) << "First drain should return 2 frames";
    EXPECT_EQ(second_drain.size(), 0u) << "Second drain should return empty";
}

TEST_F(SimHalTest, IsSimulationReturnsTrue) {
    EXPECT_TRUE(hal_.isSimulation());
}
