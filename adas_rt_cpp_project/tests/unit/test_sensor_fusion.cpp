/**
 * @file test_sensor_fusion.cpp
 * @brief Unit tests for EKF sensor fusion (SensorFusion class).
 */

#include <gtest/gtest.h>
#include "../../src/adas/perception/sensor_fusion.hpp"
#include "../../src/adas/perception/object_detection.hpp"

using namespace adas::perception;

class SensorFusionTest : public ::testing::Test {
protected:
    void SetUp() override {
        fusion_.setNoiseParams(0.5f, 0.3f, 1.0f);
        fusion_.reset();
    }

    SensorFusion fusion_;
};

// ─── Track init ───────────────────────────────────────────────────────────────

TEST_F(SensorFusionTest, NewDetectionCreatesTrack) {
    DetectedObject det{};
    det.id           = 0;
    det.source       = SensorType::CAMERA;
    det.cls          = ObjectClass::VEHICLE;
    det.confidence   = 0.9f;
    det.x = 30.f; det.y = 0.f;
    det.vx = 0.f; det.vy = 0.f;
    det.timestamp_us = 0;

    auto tracks = fusion_.update({det}, 1'000'000);
    EXPECT_EQ(tracks.size(), 1u);
    EXPECT_NEAR(tracks[0].px, 30.f, 1.f);
    EXPECT_NEAR(tracks[0].py, 0.f,  1.f);
}

// ─── Track confirmation ───────────────────────────────────────────────────────

TEST_F(SensorFusionTest, TrackConfirmedAfterThreeHits) {
    DetectedObject det{};
    det.id           = 0;
    det.source       = SensorType::CAMERA;
    det.cls          = ObjectClass::VEHICLE;
    det.confidence   = 0.9f;
    det.x = 30.f; det.y = 0.f;
    det.timestamp_us = 0;

    // First update
    auto tracks = fusion_.update({det}, 1'000'000);
    EXPECT_FALSE(tracks.empty());
    EXPECT_FALSE(tracks[0].is_confirmed) << "Should not be confirmed on first hit";

    // Second update
    det.x = 29.0f;
    tracks = fusion_.update({det}, 1'020'000);
    EXPECT_FALSE(tracks.empty());
    EXPECT_FALSE(tracks[0].is_confirmed) << "Not yet confirmed on second hit";

    // Third update
    det.x = 28.0f;
    tracks = fusion_.update({det}, 1'040'000);
    EXPECT_FALSE(tracks.empty());
    EXPECT_TRUE(tracks[0].is_confirmed) << "Should be confirmed after 3 hits";
}

// ─── Track deletion after misses ──────────────────────────────────────────────

TEST_F(SensorFusionTest, TrackDeletedAfterMaxMisses) {
    DetectedObject det{};
    det.id           = 0;
    det.source       = SensorType::CAMERA;
    det.cls          = ObjectClass::VEHICLE;
    det.confidence   = 0.9f;
    det.x = 30.f; det.y = 0.f;
    det.timestamp_us = 0;

    // Init track
    fusion_.update({det}, 1'000'000);

    // Send 6 empty updates (kMaxMisses = 5)
    for (int i = 0; i < 6; ++i) {
        auto tracks = fusion_.update({}, static_cast<uint64_t>(1'020'000 + i * 20'000));
        if (i >= 5 && tracks.empty()) {
            SUCCEED() << "Track correctly pruned after " << i+1 << " misses";
            return;
        }
    }
    FAIL() << "Track should have been pruned after kMaxMisses frames";
}

// ─── EKF prediction ───────────────────────────────────────────────────────────

TEST_F(SensorFusionTest, KalmanPredictionProducesReasonablePosition) {
    // Object at 50m, moving toward ego at 15 m/s
    DetectedObject det{};
    det.source = SensorType::RADAR;
    det.cls    = ObjectClass::VEHICLE;
    det.confidence = 0.7f;
    det.x = 50.f; det.y = 0.f;
    det.vx = -15.f; det.vy = 0.f;   // approaching

    // 3 updates to confirm track
    for (int i = 0; i < 3; ++i) {
        det.x -= 0.3f;   // small motion between frames
        fusion_.update({det}, static_cast<uint64_t>(1'000'000 + i * 20'000));
    }

    // One update with no detection: EKF should predict forward
    auto tracks = fusion_.update({}, 1'060'000);
    ASSERT_FALSE(tracks.empty());

    // After prediction, position should have moved slightly toward ego
    // (x decreasing because vx is negative)
    // We just check it's within plausible range
    EXPECT_GT(tracks[0].px, 45.f) << "EKF predicted position seems unreasonably low";
    EXPECT_LT(tracks[0].px, 55.f) << "EKF predicted position seems too high";
}

// ─── Multiple objects ─────────────────────────────────────────────────────────

TEST_F(SensorFusionTest, TwoObjectsTrackedIndependently) {
    DetectedObject obj1{}, obj2{};
    obj1.source = obj2.source = SensorType::CAMERA;
    obj1.cls    = obj2.cls    = ObjectClass::VEHICLE;
    obj1.confidence = obj2.confidence = 0.9f;
    obj1.x = 30.f; obj1.y = -2.f;   // right lane
    obj2.x = 50.f; obj2.y =  2.f;   // left lane

    for (int i = 0; i < 4; ++i) {
        fusion_.update({obj1, obj2}, static_cast<uint64_t>(i * 20'000));
    }

    auto tracks = fusion_.getTracks();
    EXPECT_EQ(tracks.size(), 2u) << "Should have exactly 2 independent tracks";

    // Verify they are spatially separated
    EXPECT_NE(tracks[0].track_id, tracks[1].track_id);
    const float gap = std::abs(tracks[0].px - tracks[1].px);
    EXPECT_GT(gap, 10.f) << "Tracks should remain spatially separate";
}

// ─── Reset ────────────────────────────────────────────────────────────────────

TEST_F(SensorFusionTest, ResetClearsAllTracks) {
    DetectedObject det{};
    det.source = SensorType::CAMERA;
    det.confidence = 0.9f;
    det.x = 30.f; det.y = 0.f;

    fusion_.update({det}, 1'000'000);
    fusion_.reset();

    auto tracks = fusion_.getTracks();
    EXPECT_TRUE(tracks.empty()) << "All tracks must be cleared after reset()";
}
