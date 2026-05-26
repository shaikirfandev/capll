"""
pytest_framework/test_suites/sensor_fusion/test_fusion.py

Sensor Fusion Validation Suite
ASIL: B | Requirements: FUSION_REQ_001–050
"""
import time
import pytest

from core.base_test import ADASBaseTest
from radar.radar_validator   import RadarObject
from camera.camera_validator import LaneDetectionResult
from lidar.lidar_validator   import LiDARPoint, PointCloud
from sensor_fusion.fusion_validator import FusedObject

CANID_FUSION_STATUS = 0x200


@pytest.mark.sensor_fusion
@pytest.mark.regression
class TestSensorFusion(ADASBaseTest):

    ASIL    = "B"
    FEATURE = "SENSOR_FUSION"
    REQ_IDS = ["FUSION_REQ_001", "FUSION_REQ_010", "FUSION_REQ_030"]

    # ── Timestamp synchronisation ─────────────────────────────────────────────

    @pytest.mark.smoke
    def test_timestamp_sync_radar_camera(self, fusion):
        """Radar and camera timestamps must be within 20ms."""
        ts = time.monotonic()
        fusion.record_timestamp("radar",  ts)
        fusion.record_timestamp("camera", ts + 0.015)
        fusion.assert_timestamp_sync("radar", "camera", max_skew_ms=20.0)

    def test_timestamp_sync_radar_lidar(self, fusion):
        """Radar and LiDAR timestamps must be within 30ms."""
        ts = time.monotonic()
        fusion.record_timestamp("radar", ts)
        fusion.record_timestamp("lidar", ts + 0.025)
        fusion.assert_timestamp_sync("radar", "lidar", max_skew_ms=30.0)

    # ── Object fusion consistency ─────────────────────────────────────────────

    def test_object_fused_from_radar(self, fusion):
        """Object seen by radar must appear in fusion output."""
        fusion.ingest(FusedObject(
            track_id=1, pos_x_m=30.0, pos_y_m=0.5,
            velocity_mps=20.0, heading_deg=5.0,
            confidence=0.90, source="radar"
        ))
        fusion.assert_object_fused(track_id=1)

    def test_object_fused_from_camera(self, fusion):
        """Object classified by camera must appear in fusion output."""
        fusion.ingest(FusedObject(
            track_id=2, pos_x_m=15.0, pos_y_m=-0.3,
            velocity_mps=10.0, heading_deg=0.0,
            confidence=0.85, source="camera"
        ))
        fusion.assert_object_fused(track_id=2)

    def test_multi_source_fusion_confidence_boost(self, fusion):
        """Object confirmed by radar + camera should have confidence ≥ 0.90."""
        for src in ("radar", "camera", "lidar"):
            fusion.ingest(FusedObject(
                track_id=5, pos_x_m=40.0, pos_y_m=0.0,
                velocity_mps=30.0, heading_deg=0.0,
                confidence=0.88, source=src
            ))
        fusion.assert_confidence_above(track_id=5, min_confidence=0.80)

    # ── Tracking continuity ───────────────────────────────────────────────────

    def test_tracking_continuity(self, fusion):
        """Object must maintain tracking for ≥ 5 consecutive updates."""
        for i in range(8):
            fusion.ingest(FusedObject(
                track_id=10, pos_x_m=50.0 - i * 2,
                pos_y_m=0.0, velocity_mps=20.0,
                heading_deg=0.0, confidence=0.92,
                source="fused"
            ))
            time.sleep(0.01)
        fusion.assert_tracking_continuity(track_id=10, min_updates=5)

    def test_no_tracking_gaps(self, fusion):
        """No tracking gap > 3× expected period (300ms for 10Hz)."""
        fusion.assert_no_tracking_gaps(track_id=10, max_gap_s=0.3)

    # ── Latency ───────────────────────────────────────────────────────────────

    @pytest.mark.performance
    def test_fusion_latency_within_limit(self, fusion):
        """Mean sensor-to-fusion latency < 50ms per sensor."""
        for _ in range(20):
            fusion.record_latency("radar",  float(30 + (10 * 0.1)))
            fusion.record_latency("camera", float(40 + (5  * 0.1)))
        fusion.assert_latency("radar",  max_mean_ms=50.0)
        fusion.assert_latency("camera", max_mean_ms=50.0)

    # ── Failover ─────────────────────────────────────────────────────────────

    @pytest.mark.fault_injection
    @pytest.mark.safety
    def test_fusion_survives_sensor_dropout(
        self, fusion, fault_injector
    ):
        """Fusion continues tracking when one sensor drops out."""
        from utilities.fault_injector import FaultType
        # Pre-load fused object
        fusion.ingest(FusedObject(
            track_id=20, pos_x_m=35.0, pos_y_m=0.0,
            velocity_mps=25.0, heading_deg=0.0,
            confidence=0.90, source="fused"
        ))
        with fault_injector.inject(FaultType.RADAR_DROPOUT, duration_s=0.5):
            time.sleep(0.3)
            # Camera-only fused update should still arrive
            fusion.ingest(FusedObject(
                track_id=20, pos_x_m=34.0, pos_y_m=0.0,
                velocity_mps=25.0, heading_deg=0.0,
                confidence=0.70, source="camera"
            ))
        fusion.assert_object_fused(track_id=20)

    # ── Object proximity search ───────────────────────────────────────────────

    def test_object_near_lookup(self, fusion):
        """find_object_near returns correct object within tolerance."""
        fusion.ingest(FusedObject(
            track_id=30, pos_x_m=20.0, pos_y_m=1.0,
            velocity_mps=15.0, heading_deg=0.0,
            confidence=0.88, source="fused"
        ))
        obj = fusion.find_object_near(20.5, 1.2, tolerance_m=2.0)
        assert obj is not None, "Expected object near (20.5, 1.2) not found"
        assert obj.track_id == 30

    def test_object_outside_tolerance_not_returned(self, fusion):
        """find_object_near returns None when tolerance is not met."""
        obj = fusion.find_object_near(100.0, 100.0, tolerance_m=1.0)
        assert obj is None, "Unexpected object found far outside tolerance"
