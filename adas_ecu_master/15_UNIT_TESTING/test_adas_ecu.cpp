/**
 * @file    test_adas_ecu.cpp
 * @brief   Unit tests for ADAS ECU components using Google Test
 * @details Tests: PidController, StaticRingBuffer, LKA state machine,
 *          CAN signal decode, ACC gap calculator
 *
 * Build:
 *   # Install gtest (macOS): brew install googletest
 *   g++ -std=c++17 -Wall -Wextra test_adas_ecu.cpp \
 *       -lgtest -lgtest_main -pthread -o test_adas_ecu
 *   ./test_adas_ecu
 *
 * Cross-compile for ECU (native unit test on host — recommended):
 *   arm-none-eabi-g++ cannot easily link gtest.
 *   Recommended: run all unit tests on host (x86), HIL tests on target.
 */

#include <gtest/gtest.h>
#include <cstdint>
#include <cstddef>
#include <cmath>
#include <array>

// ============================================================================
// COMPONENT UNDER TEST: StaticRingBuffer
// ============================================================================

template <typename T, std::size_t N>
class StaticRingBuffer {
    static_assert(N > 0U && (N & (N-1U)) == 0U, "N must be power of 2");
public:
    bool push(const T& val) noexcept {
        if (full()) { return false; }
        buf_[head_ & (N-1U)] = val;
        ++head_;
        return true;
    }
    bool pop(T& out) noexcept {
        if (empty()) { return false; }
        out = buf_[tail_ & (N-1U)];
        ++tail_;
        return true;
    }
    bool empty() const noexcept { return head_ == tail_; }
    bool full()  const noexcept { return (head_ - tail_) == N; }
    std::size_t size() const noexcept { return head_ - tail_; }

private:
    T           buf_[N] = {};
    std::size_t head_   = 0U;
    std::size_t tail_   = 0U;
};

// ============================================================================
// COMPONENT UNDER TEST: PidController
// ============================================================================

class PidController {
public:
    struct Params { float kp, ki, kd, outMin, outMax, integralClamp; };
    explicit PidController(Params p) noexcept : p_(p) {}

    float compute(float error, float dt_s) noexcept {
        if (dt_s <= 0.0F) { return 0.0F; }
        integral_ += error * dt_s;
        integral_  = std::max(-p_.integralClamp, std::min(p_.integralClamp, integral_));
        float deriv = (error - prevErr_) / dt_s;
        prevErr_    = error;
        return std::max(p_.outMin, std::min(p_.outMax, p_.kp*error + p_.ki*integral_ + p_.kd*deriv));
    }
    void reset() noexcept { integral_ = 0.0F; prevErr_ = 0.0F; }
    float getIntegral() const noexcept { return integral_; }

private:
    Params p_;
    float  integral_  = 0.0F;
    float  prevErr_   = 0.0F;
};

// ============================================================================
// COMPONENT UNDER TEST: CAN Signal Decoder
// ============================================================================

static float decodeCanSignalIntel(const uint8_t* data, uint8_t startBit,
                                   uint8_t bitLen, float factor, float offset) {
    uint64_t raw = 0U;
    for (uint8_t i = 0U; i < bitLen; ++i) {
        uint8_t bp  = startBit + i;
        uint8_t bi  = static_cast<uint8_t>(bp % 8U);
        uint8_t byt = static_cast<uint8_t>(bp / 8U);
        if (byt < 8U && ((data[byt] >> bi) & 0x01U)) {
            raw |= (static_cast<uint64_t>(1U) << i);
        }
    }
    return static_cast<float>(raw) * factor + offset;
}

// ============================================================================
// COMPONENT UNDER TEST: Safe Distance Calculator
// ============================================================================

static float computeDesiredGap(float speedMps, float timeGapS) {
    return std::max(5.0F, speedMps * timeGapS);
}

// ============================================================================
// TEST SUITE 1: StaticRingBuffer
// ============================================================================

class RingBufferTest : public ::testing::Test {
protected:
    StaticRingBuffer<int, 4> buf;
};

TEST_F(RingBufferTest, InitiallyEmpty) {
    EXPECT_TRUE(buf.empty());
    EXPECT_FALSE(buf.full());
    EXPECT_EQ(buf.size(), 0U);
}

TEST_F(RingBufferTest, PushAndPop) {
    EXPECT_TRUE(buf.push(42));
    EXPECT_FALSE(buf.empty());
    EXPECT_EQ(buf.size(), 1U);

    int val = 0;
    EXPECT_TRUE(buf.pop(val));
    EXPECT_EQ(val, 42);
    EXPECT_TRUE(buf.empty());
}

TEST_F(RingBufferTest, FIFO_Order) {
    buf.push(1);
    buf.push(2);
    buf.push(3);

    int v;
    buf.pop(v); EXPECT_EQ(v, 1);
    buf.pop(v); EXPECT_EQ(v, 2);
    buf.pop(v); EXPECT_EQ(v, 3);
}

TEST_F(RingBufferTest, FullRejectsNewItems) {
    EXPECT_TRUE(buf.push(1));
    EXPECT_TRUE(buf.push(2));
    EXPECT_TRUE(buf.push(3));
    EXPECT_TRUE(buf.push(4));
    EXPECT_TRUE(buf.full());
    EXPECT_FALSE(buf.push(5));  // Must reject — buffer full
}

TEST_F(RingBufferTest, PopFromEmptyReturnsFalse) {
    int v;
    EXPECT_FALSE(buf.pop(v));
}

TEST_F(RingBufferTest, WrapAround) {
    buf.push(1); buf.push(2); buf.push(3); buf.push(4);  // full
    int v;
    buf.pop(v);  // remove 1 → space
    EXPECT_TRUE(buf.push(5));  // wraps around
    buf.pop(v); EXPECT_EQ(v, 2);
    buf.pop(v); EXPECT_EQ(v, 3);
    buf.pop(v); EXPECT_EQ(v, 4);
    buf.pop(v); EXPECT_EQ(v, 5);
    EXPECT_TRUE(buf.empty());
}

// ============================================================================
// TEST SUITE 2: PID Controller
// ============================================================================

class PidTest : public ::testing::Test {
protected:
    PidController::Params params{1.0F, 0.1F, 0.05F, -5.0F, 5.0F, 10.0F};
    PidController pid{params};
};

TEST_F(PidTest, ZeroErrorProducesZeroOutput) {
    float out = pid.compute(0.0F, 0.01F);
    EXPECT_NEAR(out, 0.0F, 1e-5F);
}

TEST_F(PidTest, PositiveErrorProducesPositiveOutput) {
    float out = pid.compute(1.0F, 0.01F);
    EXPECT_GT(out, 0.0F);
}

TEST_F(PidTest, NegativeErrorProducesNegativeOutput) {
    float out = pid.compute(-1.0F, 0.01F);
    EXPECT_LT(out, 0.0F);
}

TEST_F(PidTest, OutputClampsAtMax) {
    // Large error should clamp to max
    for (int i = 0; i < 100; ++i) {
        pid.compute(100.0F, 0.01F);
    }
    float out = pid.compute(100.0F, 0.01F);
    EXPECT_LE(out, 5.0F + 1e-5F);
}

TEST_F(PidTest, OutputClampsAtMin) {
    for (int i = 0; i < 100; ++i) {
        pid.compute(-100.0F, 0.01F);
    }
    float out = pid.compute(-100.0F, 0.01F);
    EXPECT_GE(out, -5.0F - 1e-5F);
}

TEST_F(PidTest, ResetClearsIntegral) {
    pid.compute(5.0F, 0.01F);
    pid.compute(5.0F, 0.01F);
    EXPECT_NE(pid.getIntegral(), 0.0F);
    pid.reset();
    EXPECT_NEAR(pid.getIntegral(), 0.0F, 1e-6F);
}

TEST_F(PidTest, ZeroDtReturnsZero) {
    // dt_s = 0 must be handled safely (no division by zero)
    float out = pid.compute(5.0F, 0.0F);
    EXPECT_NEAR(out, 0.0F, 1e-5F);
}

TEST_F(PidTest, IntegralClampPreventsWindup) {
    // Drive integral to clamp
    for (int i = 0; i < 1000; ++i) {
        pid.compute(100.0F, 0.1F);
    }
    EXPECT_LE(std::abs(pid.getIntegral()), 10.0F + 1e-5F);
}

// ============================================================================
// TEST SUITE 3: CAN Signal Decode
// ============================================================================

TEST(CanDecode, VehicleSpeed_KnownValue) {
    // VehicleSpeed: startBit=0, 16 bits, Intel, factor=0.01, offset=0
    // Speed = 80 km/h → raw = 80 / 0.01 = 8000 = 0x1F40
    uint8_t data[8] = {0x40, 0x1F, 0, 0, 0, 0, 0, 0};  // little-endian 8000
    float speed = decodeCanSignalIntel(data, 0U, 16U, 0.01F, 0.0F);
    EXPECT_NEAR(speed, 80.0F, 0.01F);
}

TEST(CanDecode, ZeroFrame) {
    uint8_t data[8] = {};
    float speed = decodeCanSignalIntel(data, 0U, 16U, 0.01F, 0.0F);
    EXPECT_NEAR(speed, 0.0F, 1e-5F);
}

TEST(CanDecode, SingleBitSignal) {
    uint8_t data[8] = {};
    data[2U] = 0x01U;  // bit 16 set
    float val = decodeCanSignalIntel(data, 16U, 1U, 1.0F, 0.0F);
    EXPECT_NEAR(val, 1.0F, 1e-5F);
}

TEST(CanDecode, SingleBitSignalClear) {
    uint8_t data[8] = {0xFF, 0xFF, 0xFE, 0xFF, 0, 0, 0, 0};  // bit 16 = 0
    float val = decodeCanSignalIntel(data, 16U, 1U, 1.0F, 0.0F);
    EXPECT_NEAR(val, 0.0F, 1e-5F);
}

// ============================================================================
// TEST SUITE 4: Safe Distance Calculator
// ============================================================================

TEST(SafeDistance, NormalHighway) {
    // 120 km/h = 33.3 m/s, 2s gap → 66.6m
    float gap = computeDesiredGap(33.33F, 2.0F);
    EXPECT_NEAR(gap, 66.67F, 0.1F);
}

TEST(SafeDistance, LowSpeedMinimum) {
    // 1 m/s, 2s → 2m, but minimum is 5m
    float gap = computeDesiredGap(1.0F, 2.0F);
    EXPECT_GE(gap, 5.0F);
}

TEST(SafeDistance, StandstillMinimum) {
    float gap = computeDesiredGap(0.0F, 2.0F);
    EXPECT_GE(gap, 5.0F);
}

TEST(SafeDistance, LargerTimeGapMeansLargerGap) {
    float gap_2s = computeDesiredGap(30.0F, 2.0F);
    float gap_3s = computeDesiredGap(30.0F, 3.0F);
    EXPECT_GT(gap_3s, gap_2s);
}

// ============================================================================
// MAIN — gtest main provided by -lgtest_main, or write own:
// ============================================================================
// int main(int argc, char** argv) {
//     testing::InitGoogleTest(&argc, argv);
//     return RUN_ALL_TESTS();
// }
