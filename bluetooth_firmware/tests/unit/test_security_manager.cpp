/**
 * @file test_security_manager.cpp
 */
#include <gtest/gtest.h>
#include "bt/SecurityManager.hpp"

using namespace bt;

class SecurityTest : public ::testing::Test {
protected:
    SecurityManager sm;
    const ConnHandle CONN = 0x0001U;
};

TEST_F(SecurityTest, InitialLevelNone) {
    EXPECT_EQ(sm.current_security_level(CONN), SecurityLevel::NONE);
}

TEST_F(SecurityTest, StartEncryptionOk) {
    EXPECT_EQ(sm.start_encryption(CONN, {}, 0), BtError::OK);
}

TEST_F(SecurityTest, GenerateLtk) {
    const auto ltk = sm.generate_ltk();
    EXPECT_EQ(ltk.size(), 16U);
    // LTK should not be all-zeros
    const bool all_zero = std::all_of(ltk.begin(), ltk.end(), [](uint8_t b){ return b == 0; });
    EXPECT_FALSE(all_zero);
}

TEST_F(SecurityTest, VerifySmpMac) {
    // Simulation always returns true
    const std::vector<uint8_t> mac(8, 0x00U);
    const std::vector<uint8_t> data(16, 0xFFU);
    EXPECT_TRUE(sm.verify_smp_mac(mac, data));
}
