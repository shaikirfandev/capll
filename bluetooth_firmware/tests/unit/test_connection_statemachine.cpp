/**
 * @file test_connection_statemachine.cpp
 * @brief FSM transition tests
 */
#include <gtest/gtest.h>
#include "bt/ConnectionStateMachine.hpp"

using namespace bt;

class CsmTest : public ::testing::Test {
protected:
    ConnectionStateMachine csm;
};

TEST_F(CsmTest, InitialStateIsIdle) {
    EXPECT_EQ(csm.current_state(), ConnState::IDLE);
}

TEST_F(CsmTest, IdleToAdvertising) {
    EXPECT_EQ(csm.process_event(ConnEvent::START_ADV), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::ADVERTISING);
}

TEST_F(CsmTest, AdvertisingToConnected) {
    csm.process_event(ConnEvent::START_ADV);
    EXPECT_EQ(csm.process_event(ConnEvent::CONNECTED), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::CONNECTED);
}

TEST_F(CsmTest, ConnectedToPairing) {
    csm.process_event(ConnEvent::START_ADV);
    csm.process_event(ConnEvent::CONNECTED);
    EXPECT_EQ(csm.process_event(ConnEvent::PAIR_START), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::PAIRING);
}

TEST_F(CsmTest, PairingToPaired) {
    csm.process_event(ConnEvent::START_ADV);
    csm.process_event(ConnEvent::CONNECTED);
    csm.process_event(ConnEvent::PAIR_START);
    EXPECT_EQ(csm.process_event(ConnEvent::PAIR_COMPLETE), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::PAIRED);
}

TEST_F(CsmTest, DisconnectFromConnected) {
    csm.process_event(ConnEvent::START_ADV);
    csm.process_event(ConnEvent::CONNECTED);
    csm.process_event(ConnEvent::DISCONNECT_REQ);
    EXPECT_EQ(csm.current_state(), ConnState::DISCONNECTING);
    csm.process_event(ConnEvent::DISCONNECTED);
    EXPECT_EQ(csm.current_state(), ConnState::IDLE);
}

TEST_F(CsmTest, IllegalTransitionReturnsError) {
    // Cannot CONNECT from IDLE without advertising first
    EXPECT_NE(csm.process_event(ConnEvent::CONNECTED), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::ERROR);
}

TEST_F(CsmTest, ErrorRecovery) {
    csm.process_event(ConnEvent::CONNECTED);  // illegal → ERROR
    EXPECT_EQ(csm.current_state(), ConnState::ERROR);
    EXPECT_EQ(csm.process_event(ConnEvent::DISCONNECT_REQ), BtError::OK);
    EXPECT_EQ(csm.current_state(), ConnState::IDLE);
}

TEST_F(CsmTest, CanTransitionCheck) {
    EXPECT_TRUE(csm.can_transition(ConnEvent::START_ADV));
    EXPECT_FALSE(csm.can_transition(ConnEvent::CONNECTED));
}
