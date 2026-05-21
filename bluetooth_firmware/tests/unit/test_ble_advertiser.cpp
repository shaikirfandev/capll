/**
 * @file test_ble_advertiser.cpp
 * @brief BleAdvertiser tests using mock controller
 */
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "bt/BleAdvertiser.hpp"
#include "mocks/MockBtController.hpp"

using namespace bt;
using namespace bt::mocks;
using ::testing::Return;
using ::testing::_;
using ::testing::Invoke;

class BleAdvTest : public ::testing::Test {
protected:
    MockBtController ctrl;
    std::unique_ptr<BleAdvertiser> adv;

    void SetUp() override {
        adv = std::make_unique<BleAdvertiser>(&ctrl);
    }
};

TEST_F(BleAdvTest, StartAdvertisingCallsController) {
    EXPECT_CALL(ctrl, start_advertising(_, _, _))
        .WillOnce(Return(BtError::OK));

    AdvParams params{};
    params.interval_min_ms = 100U;
    params.interval_max_ms = 150U;
    AdvData adv_data{}, scan_rsp{};

    EXPECT_EQ(adv->start(params, adv_data, scan_rsp), BtError::OK);
    EXPECT_TRUE(adv->is_advertising());
}

TEST_F(BleAdvTest, StopAdvertisingCallsController) {
    EXPECT_CALL(ctrl, start_advertising(_, _, _)).WillOnce(Return(BtError::OK));
    EXPECT_CALL(ctrl, stop_advertising()).WillOnce(Return(BtError::OK));

    AdvParams params{};
    params.interval_min_ms = 100U;
    params.interval_max_ms = 150U;
    AdvData adv_data{}, scan_rsp{};

    adv->start(params, adv_data, scan_rsp);
    EXPECT_EQ(adv->stop(), BtError::OK);
    EXPECT_FALSE(adv->is_advertising());
}

TEST_F(BleAdvTest, InvalidIntervalRejected) {
    AdvParams params{};
    params.interval_min_ms = 200U;  // min > max → invalid
    params.interval_max_ms = 100U;
    AdvData adv_data{}, scan_rsp{};

    // Controller should NOT be called
    EXPECT_CALL(ctrl, start_advertising(_, _, _)).Times(0);

    const BtError err = adv->start(params, adv_data, scan_rsp);
    EXPECT_NE(err, BtError::OK);
}

TEST_F(BleAdvTest, DoubleStartReturnsBusy) {
    EXPECT_CALL(ctrl, start_advertising(_, _, _)).WillOnce(Return(BtError::OK));

    AdvParams p{};
    p.interval_min_ms = 100; p.interval_max_ms = 150;
    AdvData d{}, s{};
    adv->start(p, d, s);

    // Second start without stop should return ERR_INVALID_STATE or similar
    EXPECT_CALL(ctrl, start_advertising(_, _, _)).Times(0);
    const BtError err = adv->start(p, d, s);
    EXPECT_NE(err, BtError::OK);
}
