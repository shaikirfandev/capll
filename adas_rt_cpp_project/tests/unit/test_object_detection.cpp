/**
 * @file test_object_detection.cpp
 * @brief Unit tests for ObjectDetector pipeline.
 */

#include <gtest/gtest.h>
#include "../../src/adas/perception/object_detection.hpp"

using namespace adas::perception;

// ─── Test fixture ─────────────────────────────────────────────────────────────

class ObjectDetectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        CameraIntrinsics intr{718.8f, 718.8f, 607.5f, 185.2f};
        ExtrinsicTransform cam_ext{1.5f, 0.f, 1.2f, 0.f, 0.f, 0.f};
        ExtrinsicTransform rad_ext{2.5f, 0.f, 0.5f, 0.f, 0.f, 0.f};
        detector_.configure(intr, cam_ext, rad_ext);
    }

    ObjectDetector detector_;
};

// ─── Camera detection tests ───────────────────────────────────────────────────

TEST_F(ObjectDetectorTest, EmptyCameraFrameReturnsNoObjects) {
    SensorFrame frame{};
    frame.type         = SensorType::CAMERA;
    frame.timestamp_us = 1000;
    auto objects = detector_.process(frame);
    EXPECT_TRUE(objects.empty());
}

TEST_F(ObjectDetectorTest, LowConfidenceCameraDetectionFiltered) {
    SensorFrame frame{};
    frame.type         = SensorType::CAMERA;
    frame.timestamp_us = 1000;

    CameraDetection det{};
    det.u = 320; det.v = 240;
    det.width = 80; det.height = 60;
    det.depth_m = 20.f;
    det.confidence = 0.10f;   // below kMinConfidenceCamera=0.40
    det.cls = ObjectClass::VEHICLE;
    frame.camera_dets.push_back(det);

    auto objects = detector_.process(frame);
    EXPECT_TRUE(objects.empty()) << "Low confidence detection should be filtered";
}

TEST_F(ObjectDetectorTest, ValidCameraDetectionProjectedCorrectly) {
    SensorFrame frame{};
    frame.type         = SensorType::CAMERA;
    frame.timestamp_us = 5000;

    CameraDetection det{};
    det.u           = 607.5f;   // principal point (cx) → object at image centre
    det.v           = 185.2f;   // cy
    det.width       = 80.f;
    det.height      = 60.f;
    det.depth_m     = 30.f;
    det.confidence  = 0.85f;
    det.cls         = ObjectClass::VEHICLE;
    frame.camera_dets.push_back(det);

    auto objects = detector_.process(frame);
    ASSERT_EQ(objects.size(), 1u);

    const auto& obj = objects[0];
    EXPECT_EQ(obj.source, SensorType::CAMERA);
    EXPECT_EQ(obj.cls,    ObjectClass::VEHICLE);
    EXPECT_NEAR(obj.confidence, 0.85f, 1e-4f);
    EXPECT_GT(obj.x, 0.f) << "Object should be in front of ego (positive X)";
    EXPECT_EQ(obj.timestamp_us, 5000u);
}

// ─── Radar detection tests ────────────────────────────────────────────────────

TEST_F(ObjectDetectorTest, RadarDetectionConvertedToEgoFrame) {
    SensorFrame frame{};
    frame.type         = SensorType::RADAR;
    frame.timestamp_us = 2000;

    RadarDetection det{};
    det.range_m        = 50.f;
    det.azimuth_rad    = 0.f;   // straight ahead
    det.elevation_rad  = 0.f;
    det.range_rate_mps = -10.f; // approaching at 10 m/s
    det.rcs_dbsm       = 15.f;
    frame.radar_dets.push_back(det);

    auto objects = detector_.process(frame);
    ASSERT_EQ(objects.size(), 1u);

    const auto& obj = objects[0];
    EXPECT_EQ(obj.source, SensorType::RADAR);
    EXPECT_NEAR(obj.x, 52.5f, 1.0f)  // 50m range + 2.5m radar offset
        << "Radar object should be ~52.5m ahead";
    EXPECT_GT(obj.vx, 0.f) << "Approaching target → positive vx toward ego";
}

TEST_F(ObjectDetectorTest, RadarOutOfRangeDetectionFiltered) {
    SensorFrame frame{};
    frame.type         = SensorType::RADAR;
    frame.timestamp_us = 3000;

    RadarDetection det{};
    det.range_m       = 250.f;  // > 200 m limit
    det.azimuth_rad   = 0.f;
    det.elevation_rad = 0.f;
    frame.radar_dets.push_back(det);

    auto objects = detector_.process(frame);
    EXPECT_TRUE(objects.empty()) << "Out-of-range radar target should be filtered";
}

// ─── Multiple detections ──────────────────────────────────────────────────────

TEST_F(ObjectDetectorTest, MultipleRadarDetectionsGetUniqueIDs) {
    SensorFrame frame{};
    frame.type         = SensorType::RADAR;
    frame.timestamp_us = 4000;

    for (int i = 0; i < 5; ++i) {
        RadarDetection det{};
        det.range_m       = 20.f + i * 10.f;
        det.azimuth_rad   = 0.f;
        det.elevation_rad = 0.f;
        frame.radar_dets.push_back(det);
    }

    auto objects = detector_.process(frame);
    ASSERT_EQ(objects.size(), 5u);

    for (size_t i = 0; i < objects.size(); ++i) {
        for (size_t j = i + 1; j < objects.size(); ++j) {
            EXPECT_NE(objects[i].id, objects[j].id)
                << "All objects must have unique IDs";
        }
    }
}

// ─── Reset test ───────────────────────────────────────────────────────────────

TEST_F(ObjectDetectorTest, ResetClearsIDCounter) {
    SensorFrame frame{};
    frame.type         = SensorType::RADAR;
    frame.timestamp_us = 6000;
    RadarDetection det{};
    det.range_m = 30.f;
    frame.radar_dets.push_back(det);

    detector_.process(frame);  // ID counter advances
    detector_.reset();

    auto objects = detector_.process(frame);
    ASSERT_FALSE(objects.empty());
    EXPECT_EQ(objects[0].id, 0u) << "After reset, IDs restart from 0";
}
