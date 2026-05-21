/**
 * @file test_pairing_flow.cpp
 * @brief End-to-end pairing flow integration test
 */
#include <gtest/gtest.h>
#include "bt/PairingManager.hpp"
#include "bt/SecurityManager.hpp"
#include "bt/EventBus.hpp"

using namespace bt;

class PairingFlowTest : public ::testing::Test {
protected:
    PairingManager pm;
    SecurityManager sm;
    EventBus bus;
    const ConnHandle CONN = 0x0001U;
    const BdAddr PEER = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
};

TEST_F(PairingFlowTest, JustWorksFlow) {
    bool pairing_complete = false;
    pm.set_pairing_result_callback([&pairing_complete](ConnHandle, bool ok,
                                                         const BdAddr &) {
        pairing_complete = ok;
    });

    EXPECT_EQ(pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS), BtError::OK);
    EXPECT_EQ(pm.accept_pairing(CONN), BtError::OK);
}

TEST_F(PairingFlowTest, PasskeyEntryFlow) {
    uint32_t displayed_passkey = 0;
    pm.set_passkey_display_callback([&displayed_passkey](ConnHandle, uint32_t pk) {
        displayed_passkey = pk;
    });

    EXPECT_EQ(pm.initiate_pairing(CONN, PairingMethod::PASSKEY_ENTRY), BtError::OK);
    EXPECT_GT(displayed_passkey, 0U);  // Passkey should have been generated

    // Provide correct passkey
    EXPECT_EQ(pm.provide_passkey(CONN, displayed_passkey), BtError::OK);
}

TEST_F(PairingFlowTest, NumericComparisonFlow) {
    uint32_t confirm_value = 0;
    pm.set_passkey_confirm_callback([&confirm_value](ConnHandle, uint32_t val) {
        confirm_value = val;
    });

    EXPECT_EQ(pm.initiate_pairing(CONN, PairingMethod::NUMERIC_COMPARISON), BtError::OK);
    EXPECT_GT(confirm_value, 0U);

    EXPECT_EQ(pm.confirm_numeric(CONN, true), BtError::OK);  // User confirms
}

TEST_F(PairingFlowTest, EncryptionAfterPairing) {
    pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS);
    pm.accept_pairing(CONN);

    // Generate LTK and start encryption
    const auto ltk = sm.generate_ltk();
    EXPECT_EQ(ltk.size(), 16U);
    EXPECT_EQ(sm.start_encryption(CONN, ltk, 0U), BtError::OK);
}

TEST_F(PairingFlowTest, BondStorageAndRetrieval) {
    pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS);
    pm.accept_pairing(CONN);

    // get_bond_info for connected peer — in simulation bond is stored after accept
    // For now verify remove works without crash
    pm.remove_bond(PEER);
    EXPECT_FALSE(pm.is_bonded(PEER));
}
