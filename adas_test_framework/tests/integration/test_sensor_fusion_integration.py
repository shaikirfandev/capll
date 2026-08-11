from __future__ import annotations

import pytest

from sensors.camera import CameraDetection
from sensors.lidar import LidarDetection
from sensors.radar import RadarDetection
from sensors.sensor_fusion import SensorFusion


@pytest.mark.integration
class TestSensorFusionIntegration:
    def test_fusion_integrates_all_three_sensors(self) -> None:
        """Test ID: SF_INT_001
Requirement: Fusion integration shall support camera, radar, and lidar.
Objective: Verify tri-sensor fused track."""
        fusion = SensorFusion()
        tracks = fusion.fuse(
            [CameraDetection(1, 30.0, 0.1, -3.0, 0.8)],
            [RadarDetection(1, 31.0, -4.0, 0.0, 0.9)],
            [LidarDetection(1, 29.5, 0.05, confidence=0.85)],
            timestamp=1.0,
        )
        assert len(tracks) == 1
        assert tracks[0].distance_m == pytest.approx(30.2176, rel=1e-3)

    def test_fusion_maintains_track_between_updates(self) -> None:
        """Test ID: SF_INT_002
Requirement: Fusion integration shall maintain persistent tracks.
Objective: Verify object continuity."""
        fusion = SensorFusion()
        fusion.fuse(radar_detections=[RadarDetection(4, 40.0, -2.0, confidence=0.9)], timestamp=1.0)
        fusion.fuse(radar_detections=[RadarDetection(4, 39.0, -2.0, confidence=0.9)], timestamp=1.1)
        assert 4 in fusion.tracks

    def test_fusion_timeout_removes_track(self) -> None:
        """Test ID: SF_INT_003
Requirement: Fusion integration shall remove stale tracks.
Objective: Verify lifecycle cleanup."""
        fusion = SensorFusion(track_timeout_s=0.2)
        fusion.fuse(camera_detections=[CameraDetection(1, 10.0, 0.0, 0.0)], timestamp=1.0)
        fusion.remove_stale_tracks(timestamp=1.3)
        assert fusion.tracks == {}

    def test_fusion_camera_timeout_detected(self) -> None:
        """Test ID: SF_INT_004
Requirement: Fusion integration shall monitor sensor freshness.
Objective: Verify camera timeout path."""
        fusion = SensorFusion(track_timeout_s=0.5)
        fusion.fuse(camera_detections=[CameraDetection(1, 10.0, 0.0, 0.0)], timestamp=1.0)
        assert fusion.is_sensor_timed_out("camera", now=1.6) is True

    def test_fusion_radar_and_lidar_without_camera(self) -> None:
        """Test ID: SF_INT_005
Requirement: Fusion integration shall degrade gracefully without camera.
Objective: Verify radar/lidar-only fusion."""
        fusion = SensorFusion()
        tracks = fusion.fuse(
            radar_detections=[RadarDetection(2, 50.0, -5.0, confidence=0.8)],
            lidar_detections=[LidarDetection(2, 49.5, -0.2, confidence=0.9)],
            timestamp=1.0,
        )
        assert len(tracks) == 1
        assert tracks[0].confidence > 0.8

    def test_fusion_merges_source_labels(self) -> None:
        """Test ID: SF_INT_006
Requirement: Fusion integration shall retain sensor provenance.
Objective: Verify source labeling."""
        fusion = SensorFusion()
        tracks = fusion.fuse(
            camera_detections=[CameraDetection(3, 25.0, 0.1, -1.0)],
            radar_detections=[RadarDetection(3, 26.0, -2.0)],
            timestamp=1.0,
        )
        assert "camera+radar" in tracks[0].sources
