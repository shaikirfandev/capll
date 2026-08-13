from __future__ import annotations

import pytest

from sensors.camera import CameraDetection
from sensors.lidar import LidarDetection
from sensors.radar import RadarDetection
from sensors.sensor_fusion import SensorFusion


@pytest.mark.unit
class TestSensorFusionUnit:
    def test_new_track_is_created_on_first_update(self) -> None:
        """Test ID: SF_UNIT_001
Requirement: Fusion shall create tracks for new objects.
Objective: Verify first observation initializes a track."""
        fusion = SensorFusion()
        track = fusion.update_track(1, 40.0, -5.0, 0.2, 0.9, "radar", timestamp=1.0)
        assert track.object_id == 1
        assert track.distance_m == pytest.approx(40.0)

    def test_predict_advances_track_state(self) -> None:
        """Test ID: SF_UNIT_002
Requirement: Fusion shall predict track motion between measurements.
Objective: Verify Kalman prediction step."""
        fusion = SensorFusion()
        fusion.update_track(1, 40.0, -5.0, 0.2, 0.9, "radar", timestamp=1.0)
        predicted = fusion.predict(1, dt=0.5)
        assert predicted[0, 0] == pytest.approx(37.5)

    def test_update_blends_measurement_with_prediction(self) -> None:
        """Test ID: SF_UNIT_003
Requirement: Fusion shall smooth measurements.
Objective: Verify update step uses measurement and prediction."""
        fusion = SensorFusion()
        fusion.update_track(1, 50.0, -5.0, 0.0, 0.9, "radar", timestamp=1.0)
        track = fusion.update_track(1, 48.0, -4.0, 0.1, 0.8, "camera", timestamp=1.1)
        assert 48.0 <= track.distance_m <= 50.0
        assert any("camera" in source for source in track.sources)

    def test_camera_radar_fusion_combines_sources(self) -> None:
        """Test ID: SF_UNIT_004
Requirement: Fusion shall combine camera and radar detections.
Objective: Verify multi-sensor fusion output."""
        fusion = SensorFusion()
        camera = [CameraDetection(object_id=1, distance_m=49.0, lateral_offset_m=0.1, relative_speed_mps=-4.0, confidence=0.8)]
        radar = [RadarDetection(object_id=1, distance_m=50.0, relative_speed_mps=-5.0, azimuth_deg=0.0, confidence=0.9)]
        tracks = fusion.fuse(camera_detections=camera, radar_detections=radar, timestamp=2.0)
        assert len(tracks) == 1
        assert tracks[0].distance_m == pytest.approx(49.574, rel=1e-3)

    def test_lidar_can_join_existing_track(self) -> None:
        """Test ID: SF_UNIT_005
Requirement: Fusion shall ingest lidar measurements.
Objective: Verify lidar contribution to fused track."""
        fusion = SensorFusion()
        lidar = [LidarDetection(object_id=7, distance_m=12.0, lateral_offset_m=-0.2, confidence=0.7)]
        tracks = fusion.fuse(lidar_detections=lidar, timestamp=3.0)
        assert tracks[0].lateral_offset_m == pytest.approx(-0.2)

    def test_track_management_keeps_multiple_objects(self) -> None:
        """Test ID: SF_UNIT_006
Requirement: Fusion shall manage multiple concurrent tracks.
Objective: Verify multi-object storage."""
        fusion = SensorFusion()
        fusion.update_track(1, 20.0, -1.0, 0.0, 0.9, "radar", timestamp=1.0)
        fusion.update_track(2, 25.0, -2.0, 0.5, 0.9, "camera", timestamp=1.0)
        assert set(fusion.tracks) == {1, 2}

    def test_stale_tracks_are_removed(self) -> None:
        """Test ID: SF_UNIT_007
Requirement: Fusion shall remove stale tracks.
Objective: Verify timeout-based track deletion."""
        fusion = SensorFusion(track_timeout_s=0.2)
        fusion.update_track(1, 20.0, -1.0, 0.0, 0.9, "radar", timestamp=1.0)
        fusion.remove_stale_tracks(timestamp=1.3)
        assert fusion.tracks == {}

    def test_sensor_timeout_detection(self) -> None:
        """Test ID: SF_UNIT_008
Requirement: Fusion shall monitor sensor freshness.
Objective: Verify sensor timeout detection."""
        fusion = SensorFusion(track_timeout_s=0.5)
        fusion.update_track(1, 20.0, -1.0, 0.0, 0.9, "camera", timestamp=1.0)
        assert fusion.is_sensor_timed_out("camera", now=1.6) is True

    def test_sensor_not_timed_out_when_recent(self) -> None:
        """Test ID: SF_UNIT_009
Requirement: Fusion shall not report recent sensors as stale.
Objective: Verify freshness logic."""
        fusion = SensorFusion(track_timeout_s=0.5)
        fusion.update_track(1, 20.0, -1.0, 0.0, 0.9, "radar", timestamp=1.0)
        assert fusion.is_sensor_timed_out("radar", now=1.3) is False

    def test_confidence_is_clamped(self) -> None:
        """Test ID: SF_UNIT_010
Requirement: Fusion confidence shall remain normalized.
Objective: Verify confidence clamping."""
        fusion = SensorFusion()
        track = fusion.update_track(1, 10.0, 0.0, 0.0, 2.5, "camera", timestamp=1.0)
        assert track.confidence == 1.0
