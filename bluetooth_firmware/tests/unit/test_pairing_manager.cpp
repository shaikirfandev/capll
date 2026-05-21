/**
 * @file test_pairing_manager.cpp
 */
#include <gtest/gtest.h>
#include "bt/PairingManager.hpp"

using namespace bt;

class PairingTest : public ::testing::Test {
protected:
    PairingManager pm;
    const ConnHandle CONN = 0x0001U;
    const BdAddr     PEER = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
};

TEST_F(PairingTest, InitiatePairingOk) {
    EXPECT_EQ(pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS), BtError::OK);
}

TEST_F(PairingTest, NotBondedBeforePairing) {
    EXPECT_FALSE(pm.is_bonded(PEER));
}

TEST_F(PairingTest, AcceptAndComplete) {
    pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS);
    EXPECT_EQ(pm.accept_pairing(CONN), BtError::OK);
}

TEST_F(PairingTest, RemoveBond) {
    pm.initiate_pairing(CONN, PairingMethod::JUST_WORKS);
    pm.accept_pairing(CONN);
    // After simulated completion bond should exist — then remove
    pm.remove_all_bonds();
    EXPECT_FALSE(pm.is_bonded(PEER));
}

TEST_F(PairingTest, RejectPairing) {
    pm.initiate_pairing(CONN, PairingMethod::PASSKEY_ENTRY);
    EXPECT_EQ(pm.reject_pairing(CONN), BtError::OK);
}
