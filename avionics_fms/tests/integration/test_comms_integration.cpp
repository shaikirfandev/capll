/**
 * @file test_comms_integration.cpp
 * @brief Communications bus integration — @req SRS-INT-020..025
 */
#include <gtest/gtest.h>
#include "comms/Arinc429Driver.hpp"
#include "comms/Arinc664Driver.hpp"
#include "comms/CanAerospaceDriver.hpp"

class CommsIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        ASSERT_EQ(arinc_.init(0U, 100U), fms::FmsError::OK);
        ASSERT_EQ(afdx_.init(100U, 1000000U), fms::FmsError::OK);
        ASSERT_EQ(can_.init(0x10U, 1U), fms::FmsError::OK);
    }
    fms::comms::Arinc429Driver    arinc_;
    fms::comms::Arinc664Driver    afdx_;
    fms::comms::CanAerospaceDriver can_;
};

/// @req SRS-INT-020: ARINC 429 loopback — transmit altitude, receive matches
TEST_F(CommsIntegrationTest, Arinc429Loopback) {
    using namespace fms::comms;
    double received = -1.0;
    arinc_.set_rx_callback(
        static_cast<uint8_t>(label::ALTITUDE_CORRECTED),
        [&](const Arinc429Frame& f) {
            received = Arinc429Driver::decode_bnr(f.data_bits, 1.0, 18U);
        });
    uint32_t word = Arinc429Driver::encode_bnr(
        label::ALTITUDE_CORRECTED, 0U, 35000.0, 1.0, 18U, Arinc429Ssm::NORMAL_OP);
    EXPECT_EQ(arinc_.transmit_raw(word), fms::FmsError::OK);
    EXPECT_NEAR(received, 35000.0, 5.0);
}

/// @req SRS-INT-021: AFDX transmit succeeds and networks healthy
TEST_F(CommsIntegrationTest, AfdxTransmit) {
    fms::comms::AfdxFrame frame{};
    frame.vl_id = 100U;
    frame.seq_num   = 1U;
    frame.payload_len = 4U;
    frame.payload[0] = 0xDE; frame.payload[1] = 0xAD;
    frame.payload[2] = 0xBE; frame.payload[3] = 0xEF;
    EXPECT_TRUE(afdx_.transmit(frame));
}

/// @req SRS-INT-022: CANaerospace transmit succeeds
TEST_F(CommsIntegrationTest, CanAeroTransmit) {
    fms::comms::CanAeroMessage msg{};
    msg.message_id = 0x100U;
    msg.node_id    = 0x10U;
    msg.data_type  = static_cast<uint8_t>(fms::comms::CanAeroDataType::FLOAT);
    uint32_t alt_bits = 0U; float alt = 35000.0f; std::memcpy(&alt_bits, &alt, 4);
    msg.data = alt_bits;
    EXPECT_TRUE(can_.transmit(msg));
}

/// @req SRS-INT-023: CANaerospace RX callback fires on transmit (loopback)
TEST_F(CommsIntegrationTest, CanAeroLoopback) {
    float received = -1.0f;
    can_.set_rx_callback(0x100U, [&](const fms::comms::CanAeroMessage& m) {
        std::memcpy(&received, &m.data, sizeof(float));
    });
    fms::comms::CanAeroMessage msg{};
    msg.message_id = 0x100U;
    msg.node_id    = 0x10U;
    msg.data_type  = static_cast<uint8_t>(fms::comms::CanAeroDataType::FLOAT);
    uint32_t alt_bits = 0U; float alt = 35000.0f; std::memcpy(&alt_bits, &alt, 4);
    msg.data = alt_bits;
    can_.transmit(msg);
    EXPECT_NEAR(received, 35000.0f, 1.0f);
}

/// @req SRS-INT-024: ARINC 429 status NORMAL after successful operations
TEST_F(CommsIntegrationTest, Arinc429StatusNormal) {
    EXPECT_EQ(arinc_.get_status(), fms::SystemStatus::NORMAL);
}
