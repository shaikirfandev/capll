/**
 * @file test_arinc429.cpp
 * @brief Unit tests for ARINC 429 BNR encoding — @req SRS-COM-001..008
 */
#include <gtest/gtest.h>
#include "comms/Arinc429Driver.hpp"

class Arinc429Test : public ::testing::Test {
protected:
    void SetUp() override {
        ASSERT_EQ(drv_.init(0U, 100U), fms::FmsError::OK);
    }
    fms::comms::Arinc429Driver drv_;
};

/// @req SRS-COM-001: BNR encode/decode roundtrip for altitude 35000 ft
TEST_F(Arinc429Test, BnrRoundtripAlt35000) {
    using namespace fms::comms;
    uint32_t word = Arinc429Driver::encode_bnr(
        label::ALTITUDE_CORRECTED, 0U, 35000.0, 1.0, 18U, Arinc429Ssm::NORMAL_OP);
    double decoded = Arinc429Driver::decode_bnr(word >> 10U & 0x3FFFFU, 1.0, 18U);
    EXPECT_NEAR(decoded, 35000.0, 1.0);
}

/// @req SRS-COM-002: BNR encode/decode roundtrip for negative altitude
TEST_F(Arinc429Test, BnrRoundtripNegAlt) {
    using namespace fms::comms;
    uint32_t word = Arinc429Driver::encode_bnr(
        label::ALTITUDE_CORRECTED, 0U, -500.0, 1.0, 18U, Arinc429Ssm::NORMAL_OP);
    double decoded = Arinc429Driver::decode_bnr(word >> 10U & 0x3FFFFU, 1.0, 18U);
    EXPECT_NEAR(decoded, -500.0, 2.0);
}

/// @req SRS-COM-003: BNR roundtrip airspeed 280 kt
TEST_F(Arinc429Test, BnrRoundtripAirspeed) {
    using namespace fms::comms;
    uint32_t word = Arinc429Driver::encode_bnr(
        label::AIRSPEED_IAS, 0U, 280.0, 0.25, 16U, Arinc429Ssm::NORMAL_OP);
    double decoded = Arinc429Driver::decode_bnr(word >> 10U & 0x1FFFFU, 0.25, 16U);
    EXPECT_NEAR(decoded, 280.0, 1.0);
}

/// @req SRS-COM-004: RX callback fires on transmit (loopback)
TEST_F(Arinc429Test, RxCallbackFires) {
    using namespace fms::comms;
    double received = -1.0;
    drv_.set_rx_callback(
        static_cast<uint8_t>(label::ALTITUDE_CORRECTED),
        [&](const Arinc429Frame& f) {
            received = Arinc429Driver::decode_bnr(f.data_bits, 1.0, 18U);
        });
    uint32_t word = Arinc429Driver::encode_bnr(
        label::ALTITUDE_CORRECTED, 0U, 10000.0, 1.0, 18U, Arinc429Ssm::NORMAL_OP);
    drv_.transmit_raw(word);
    EXPECT_NEAR(received, 10000.0, 5.0);
}

/// @req SRS-COM-005: SSM field NORMAL_OP in encoded word
TEST_F(Arinc429Test, SsmNormalOp) {
    using namespace fms::comms;
    uint32_t word = Arinc429Driver::encode_bnr(
        label::ALTITUDE_CORRECTED, 0U, 35000.0, 1.0, 18U, Arinc429Ssm::NORMAL_OP);
    uint8_t ssm = static_cast<uint8_t>((word >> 29U) & 0x3U);
    EXPECT_EQ(ssm, static_cast<uint8_t>(Arinc429Ssm::NORMAL_OP));
}

/// @req SRS-COM-006: driver status is NORMAL after init
TEST_F(Arinc429Test, StatusNormalAfterInit) {
    EXPECT_EQ(drv_.get_status(), fms::SystemStatus::NORMAL);
}
