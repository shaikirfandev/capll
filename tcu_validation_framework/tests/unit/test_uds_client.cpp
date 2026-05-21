/**
 * @file test_uds_client.cpp
 * @brief Unit tests for UDSClient using mock CAN manager.
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include "diagnostics/UDSClient.h"
#include "can/CANManager.h"
#include "logging/Logger.h"

#include <atomic>

using namespace tcu::diagnostics;
using namespace tcu::can;
using namespace testing;

// ============================================================
// Mock CAN Manager
// We can't mock CANManager directly as it uses a real socket,
// but we can test the UDSClient construction and config API.
// ============================================================

class UDSClientTest : public ::testing::Test {
protected:
    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir       = "/tmp/tcu_test_logs";
        lc.enable_console= false;
        tcu::logging::Logger::init(lc);
    }

    ISOTPConfig make_istp_config() {
        ISOTPConfig cfg;
        cfg.tx_id          = 0x7E0;
        cfg.rx_id          = 0x7E8;
        cfg.p2_timeout_ms  = 500;
        cfg.p2_star_ms     = 5000;
        cfg.p3_timeout_ms  = 1000;
        cfg.st_min_ms      = 5;
        return cfg;
    }
};

// ============================================================
// ISOTPConfig tests
// ============================================================

TEST_F(UDSClientTest, ISOTPConfigDefaults) {
    ISOTPConfig cfg;
    EXPECT_EQ(cfg.tx_id,         0x7E0U);
    EXPECT_EQ(cfg.rx_id,         0x7E8U);
    EXPECT_EQ(cfg.p2_timeout_ms, 1000U);
    EXPECT_EQ(cfg.p2_star_ms,    5000U);
}

TEST_F(UDSClientTest, ISOTPConfigCustom) {
    auto cfg = make_istp_config();
    EXPECT_EQ(cfg.tx_id,        0x7E0U);
    EXPECT_EQ(cfg.rx_id,        0x7E8U);
    EXPECT_EQ(cfg.p2_timeout_ms, 500U);
}

// ============================================================
// UDSService enum values
// ============================================================

TEST_F(UDSClientTest, UDSServiceEnumValues) {
    EXPECT_EQ(static_cast<uint8_t>(UDSService::DiagnosticSessionControl), 0x10);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::ECUReset),                 0x11);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::ClearDTC),                 0x14);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::ReadDTC),                  0x19);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::ReadDataById),             0x22);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::WriteDataById),            0x2E);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::RoutineControl),           0x31);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::RequestDownload),          0x34);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::TransferData),             0x36);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::RequestTransferExit),      0x37);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::SecurityAccess),           0x27);
    EXPECT_EQ(static_cast<uint8_t>(UDSService::TesterPresent),            0x3E);
}

// ============================================================
// UDSSession enum
// ============================================================

TEST_F(UDSClientTest, UDSSessionEnumValues) {
    EXPECT_EQ(static_cast<uint8_t>(UDSSession::Default),     0x01);
    EXPECT_EQ(static_cast<uint8_t>(UDSSession::Programming), 0x02);
    EXPECT_EQ(static_cast<uint8_t>(UDSSession::Extended),    0x03);
}

// ============================================================
// NRC enum
// ============================================================

TEST_F(UDSClientTest, NRCEnumValues) {
    EXPECT_EQ(static_cast<uint8_t>(NRC::ServiceNotSupported),               0x11);
    EXPECT_EQ(static_cast<uint8_t>(NRC::SubFunctionNotSupported),           0x12);
    EXPECT_EQ(static_cast<uint8_t>(NRC::IncorrectMessageLengthOrFormat),    0x13);
    EXPECT_EQ(static_cast<uint8_t>(NRC::ConditionsNotCorrect),              0x22);
    EXPECT_EQ(static_cast<uint8_t>(NRC::RequestOutOfRange),                 0x31);
    EXPECT_EQ(static_cast<uint8_t>(NRC::SecurityAccessDenied),              0x33);
    EXPECT_EQ(static_cast<uint8_t>(NRC::InvalidKey),                        0x35);
    EXPECT_EQ(static_cast<uint8_t>(NRC::ResponsePending),                   0x78);
}

// ============================================================
// UDSResult
// ============================================================

TEST_F(UDSClientTest, UDSResultDefaultIsUnsuccessful) {
    UDSResult r;
    EXPECT_FALSE(r.success);
    EXPECT_TRUE(r.payload.empty());
    EXPECT_TRUE(r.error_message.empty());
}

TEST_F(UDSClientTest, UDSResultSuccessConstruct) {
    UDSResult r;
    r.success    = true;
    r.service_id = 0x10;
    r.payload    = {0x50, 0x01};
    EXPECT_TRUE(r.success);
    EXPECT_EQ(r.payload.size(), 2U);
}

// ============================================================
// DTCRecord
// ============================================================

TEST_F(UDSClientTest, DTCRecordDefaultValues) {
    DTCRecord rec;
    EXPECT_EQ(rec.dtc_id, 0U);
    EXPECT_EQ(rec.status_byte, 0U);
    EXPECT_TRUE(rec.status_text.empty());
    EXPECT_TRUE(rec.freeze_frame_data.empty());
}

// ============================================================
// set/get ISTP config
// ============================================================

TEST_F(UDSClientTest, SetISOTPConfigReflectsBack) {
    CANConfig cc;
    cc.interface = "vcan0";
    auto can_mgr = std::make_shared<CANManager>(cc);
    UDSClient client(can_mgr, make_istp_config());

    ISOTPConfig new_cfg;
    new_cfg.tx_id = 0x600;
    new_cfg.rx_id = 0x601;
    client.set_istp_config(new_cfg);
    EXPECT_EQ(client.istp_config().tx_id, 0x600U);
    EXPECT_EQ(client.istp_config().rx_id, 0x601U);
}

// ============================================================
// Timeout behaviour (no real ECU — expect timeout result)
// ============================================================

TEST_F(UDSClientTest, OpenSessionTimeoutWithNoECU) {
    CANConfig cc;
    cc.interface = "vcan0";
    auto can_mgr = std::make_shared<CANManager>(cc);

    ISOTPConfig istp = make_istp_config();
    istp.p2_timeout_ms = 100;  // Short timeout for test speed

    UDSClient client(can_mgr, istp);
    // CAN is not open — transmit will fail, result should be failure
    auto result = client.open_session(UDSSession::Default);
    EXPECT_FALSE(result.success);
}
