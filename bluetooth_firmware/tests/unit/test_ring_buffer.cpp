/**
 * @file test_ring_buffer.cpp
 * @brief Unit tests for lock-free SPSC RingBuffer
 */
#include <gtest/gtest.h>
#include "common/RingBuffer.hpp"
#include <thread>
#include <vector>
#include <numeric>

using namespace bt;

// ── Basic functionality ────────────────────────────────────────────────────────
TEST(RingBuffer, StartsEmpty) {
    RingBuffer<uint8_t, 8> rb;
    EXPECT_TRUE(rb.empty());
    EXPECT_FALSE(rb.full());
    EXPECT_EQ(rb.size(), 0U);
}

TEST(RingBuffer, PushPop) {
    RingBuffer<uint8_t, 8> rb;
    EXPECT_TRUE(rb.push(42U));
    EXPECT_FALSE(rb.empty());
    EXPECT_EQ(rb.size(), 1U);

    uint8_t val = 0;
    EXPECT_TRUE(rb.pop(val));
    EXPECT_EQ(val, 42U);
    EXPECT_TRUE(rb.empty());
}

TEST(RingBuffer, FillAndEmpty) {
    RingBuffer<uint32_t, 4> rb;  // capacity = 4
    for (uint32_t i = 0; i < 4; ++i) { EXPECT_TRUE(rb.push(i)); }
    EXPECT_TRUE(rb.full());
    EXPECT_FALSE(rb.push(99));  // overflow → rejected

    for (uint32_t i = 0; i < 4; ++i) {
        uint32_t v = 0; rb.pop(v);
        EXPECT_EQ(v, i);
    }
    EXPECT_TRUE(rb.empty());
}

TEST(RingBuffer, WrapAround) {
    RingBuffer<uint8_t, 4> rb;
    // Fill 3, drain 3, fill 3 again — exercises wrap-around
    rb.push(1); rb.push(2); rb.push(3);
    uint8_t v; rb.pop(v); rb.pop(v); rb.pop(v);
    EXPECT_TRUE(rb.push(4));
    EXPECT_TRUE(rb.push(5));
    rb.pop(v); EXPECT_EQ(v, 4U);
    rb.pop(v); EXPECT_EQ(v, 5U);
}

// ── SPSC concurrent stress test ───────────────────────────────────────────────
TEST(RingBuffer, SpscConcurrent) {
    RingBuffer<uint32_t, 256> rb;
    constexpr uint32_t ITEMS = 10000U;

    std::thread producer([&]() {
        for (uint32_t i = 0; i < ITEMS; ++i) {
            while (!rb.push(i)) { std::this_thread::yield(); }
        }
    });

    std::vector<uint32_t> received;
    received.reserve(ITEMS);
    while (received.size() < ITEMS) {
        uint32_t v;
        if (rb.pop(v)) { received.push_back(v); }
        else { std::this_thread::yield(); }
    }

    producer.join();
    ASSERT_EQ(received.size(), ITEMS);
    // Check sequence integrity
    for (uint32_t i = 0; i < ITEMS; ++i) {
        EXPECT_EQ(received[i], i) << "Mismatch at index " << i;
    }
}
