/**
 * @file test_event_bus.cpp
 */
#include <gtest/gtest.h>
#include "bt/EventBus.hpp"
#include <atomic>
#include <chrono>
#include <thread>

using namespace bt;
using namespace std::chrono_literals;

class EventBusTest : public ::testing::Test {
protected:
    EventBus bus;
};

TEST_F(EventBusTest, SubscribeAndReceiveSync) {
    std::atomic<int> count{0};
    bus.subscribe([&count](const BtEvent &) { count++; });

    bus.publish(EvtError{BtError::ERR_HW_FAILURE});
    EXPECT_EQ(count.load(), 1);
}

TEST_F(EventBusTest, MultipleSubscribers) {
    std::atomic<int> c1{0}, c2{0};
    bus.subscribe([&c1](const BtEvent &) { c1++; });
    bus.subscribe([&c2](const BtEvent &) { c2++; });

    bus.publish(EvtConnected{0x0001, {}});
    EXPECT_EQ(c1.load(), 1);
    EXPECT_EQ(c2.load(), 1);
}

TEST_F(EventBusTest, UnsubscribeStopsDelivery) {
    std::atomic<int> count{0};
    auto id = bus.subscribe([&count](const BtEvent &) { count++; });

    bus.publish(EvtConnected{0x0001, {}});
    bus.unsubscribe(id);
    bus.publish(EvtDisconnected{0x0001, 0x13});

    EXPECT_EQ(count.load(), 1);  // Only first event received
}

TEST_F(EventBusTest, AsyncPublishDelivered) {
    std::atomic<int> count{0};
    bus.subscribe([&count](const BtEvent &) { count++; });

    bus.publish_async(EvtPairingComplete{0x0001, true, {}});

    // Give async thread time to dispatch
    for (int i = 0; i < 50 && count.load() == 0; ++i) {
        std::this_thread::sleep_for(10ms);
    }
    EXPECT_EQ(count.load(), 1);
}

TEST_F(EventBusTest, StressPublish) {
    std::atomic<uint32_t> count{0};
    bus.subscribe([&count](const BtEvent &) { count++; });

    constexpr uint32_t N = 1000U;
    for (uint32_t i = 0; i < N; ++i) {
        bus.publish(EvtError{BtError::OK});
    }
    EXPECT_EQ(count.load(), N);
}
