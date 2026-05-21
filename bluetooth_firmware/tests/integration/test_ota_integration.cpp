/**
 * @file test_ota_integration.cpp
 * @brief OTA firmware update integration tests
 */
#include <gtest/gtest.h>
#include "app/OtaManager.hpp"
#include "common/Logger.hpp"
#include <numeric>

using namespace bt;
using namespace bt::app;

// CRC-32 helper (must match OtaManager's internal implementation)
static uint32_t compute_crc32(const uint8_t *data, uint32_t len) {
    static constexpr uint32_t POLY = 0xEDB88320UL;
    uint32_t crc = ~0U;
    for (uint32_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 1U) ? ((crc >> 1U) ^ POLY) : (crc >> 1U);
        }
    }
    return ~crc;
}

class OtaIntegTest : public ::testing::Test {
protected:
    OtaManager ota;
    static constexpr ConnHandle CONN = 0x0001U;
};

TEST_F(OtaIntegTest, IdleInitially) {
    EXPECT_EQ(ota.state(), OtaState::IDLE);
}

TEST_F(OtaIntegTest, StartAndReceiveSingleChunk) {
    const uint8_t fw[] = {0x01, 0x02, 0x03, 0x04};
    const uint32_t crc = compute_crc32(fw, sizeof(fw));

    bool completed = false;
    ota.on_complete([&completed](bool ok, const std::string &) {
        completed = ok;
    });

    EXPECT_EQ(ota.start_ota(CONN, sizeof(fw), crc), BtError::OK);
    EXPECT_EQ(ota.write_chunk(fw, sizeof(fw)), BtError::OK);
    EXPECT_EQ(ota.state(), OtaState::COMPLETE);
    EXPECT_TRUE(completed);
}

TEST_F(OtaIntegTest, ChunkedTransfer) {
    const uint8_t fw[64] = {};  // 64 zero bytes
    const uint32_t crc = compute_crc32(fw, sizeof(fw));

    ota.start_ota(CONN, 64U, crc);

    // Transfer in 16-byte chunks
    for (int i = 0; i < 4; ++i) {
        const BtError err = ota.write_chunk(fw + i * 16, 16U);
        EXPECT_EQ(err, BtError::OK) << "Chunk " << i << " failed";
    }
    EXPECT_EQ(ota.state(), OtaState::COMPLETE);
}

TEST_F(OtaIntegTest, BadCrcFails) {
    const uint8_t fw[] = {0xDE, 0xAD};
    ota.start_ota(CONN, sizeof(fw), 0xDEADBEEFU);  // Wrong CRC

    ota.write_chunk(fw, sizeof(fw));
    EXPECT_EQ(ota.state(), OtaState::ERROR);
}

TEST_F(OtaIntegTest, AbortMidTransfer) {
    const uint8_t fw[100] = {};
    ota.start_ota(CONN, sizeof(fw), 0);
    ota.write_chunk(fw, 10U);  // Partial

    bool abort_cb = false;
    ota.on_complete([&abort_cb](bool ok, const std::string &) { abort_cb = !ok; });
    EXPECT_EQ(ota.abort_ota(), BtError::OK);
    EXPECT_EQ(ota.state(), OtaState::IDLE);
    EXPECT_TRUE(abort_cb);
}

TEST_F(OtaIntegTest, OverflowRejected) {
    const uint8_t fw[4] = {1, 2, 3, 4};
    ota.start_ota(CONN, 2U, 0);  // Only expecting 2 bytes
    EXPECT_NE(ota.write_chunk(fw, 4U), BtError::OK);
}

TEST_F(OtaIntegTest, ZeroSizeRejected) {
    EXPECT_NE(ota.start_ota(CONN, 0U, 0), BtError::OK);
}
