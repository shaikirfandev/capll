"""
robot_framework/libraries/SensorLibrary.py

Robot Framework keyword library for sensor-level validation:
Radar, Camera, LiDAR and Sensor Fusion.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pytest_framework"))

from robot.api import logger
from robot.api.deco import keyword, library

from radar.radar_validator   import RadarValidator, RadarObject
from camera.camera_validator import CameraValidator
from lidar.lidar_validator   import LiDARValidator
from sensor_fusion.fusion_validator import FusionValidator, FusedObject
from simulators.vehicle_simulator   import RadarSimulator

ROBOT_LIBRARY_SCOPE = "SUITE"


@library(scope="SUITE", auto_keywords=False)
class SensorLibrary:
    """
    Robot Framework library for ADAS sensor validation.

    Usage:
        Library    ../libraries/SensorLibrary.py
    """

    def __init__(self) -> None:
        self._radar:  RadarValidator  | None = None
        self._camera: CameraValidator | None = None
        self._lidar:  LiDARValidator  | None = None
        self._fusion: FusionValidator | None = None
        self._radar_sim: RadarSimulator | None = None

    @keyword("Initialize Sensor Library")
    def initialize_sensor_library(
        self, lidar_host: str = "127.0.0.1", lidar_port: int = 2368
    ) -> None:
        """Initialize all sensor validators."""
        from core.config import RadarConfig, CameraConfig, LiDARConfig
        self._radar  = RadarValidator(RadarConfig())
        self._camera = CameraValidator(source=0, cfg=CameraConfig())
        self._lidar  = LiDARValidator(host=lidar_host, port=int(lidar_port))
        self._fusion = FusionValidator(expected_sources=["radar", "camera", "lidar"])
        self._radar_sim = RadarSimulator(self._radar)
        logger.info("SensorLibrary initialized")

    @keyword("Teardown Sensor Library")
    def teardown_sensor_library(self) -> None:
        """Release sensor resources."""
        if self._radar_sim:
            self._radar_sim.stop()
        if self._camera:
            self._camera.release()
        if self._lidar:
            self._lidar.disconnect()

    # ── Radar ─────────────────────────────────────────────────────────────────

    @keyword("Inject Radar Object")
    def inject_radar_object(
        self,
        obj_id:       int   = 1,
        range_m:      float = 30.0,
        velocity_mps: float = 0.0,
        azimuth_deg:  float = 0.0,
        confidence:   float = 0.90,
    ) -> None:
        """
        Inject a synthetic radar object.

        Example:
            Inject Radar Object    obj_id=1    range_m=30    velocity_mps=-5
        """
        self._radar.ingest_object(RadarObject(
            obj_id       = int(obj_id),
            range_m      = float(range_m),
            velocity_mps = float(velocity_mps),
            azimuth_deg  = float(azimuth_deg),
            confidence   = float(confidence),
        ))
        logger.info(
            f"Radar object {obj_id} injected at {range_m}m, {velocity_mps}m/s"
        )

    @keyword("Radar Should Detect Target")
    def radar_should_detect_target(
        self,
        range_m:       float,
        velocity_mps:  float,
        azimuth_deg:   float = 0.0,
        range_tol_m:   float = 2.0,
        vel_tol_mps:   float = 1.0,
    ) -> None:
        """Assert radar detects object within tolerance."""
        self._radar.assert_target_detected(
            range_m      = float(range_m),
            velocity_mps = float(velocity_mps),
            azimuth_deg  = float(azimuth_deg),
            range_tol    = float(range_tol_m),
            vel_tol      = float(vel_tol_mps),
        )
        logger.info(f"Radar target at {range_m}m/{velocity_mps}m/s detected ✓")

    @keyword("Radar Should Have No Ghost Objects")
    def radar_should_have_no_ghost_objects(
        self, max_stationary_velocity_mps: float = 0.3
    ) -> None:
        """Assert no ghost (false) stationary objects present."""
        self._radar.assert_no_ghost_objects(float(max_stationary_velocity_mps))

    @keyword("Radar Update Rate Should Be At Least")
    def radar_update_rate_should_be_at_least(self, min_hz: float = 10.0) -> None:
        """Assert radar update rate ≥ min_hz."""
        self._radar.assert_update_rate(min_hz=float(min_hz))

    # ── Camera ────────────────────────────────────────────────────────────────

    @keyword("Camera Should Detect Lane")
    def camera_should_detect_lane(self) -> None:
        """Assert camera module detects at least one lane line."""
        self._camera.assert_lane_detected()
        logger.info("Lane detection confirmed ✓")

    @keyword("Camera Image Quality Should Meet Spec")
    def camera_image_quality_should_meet_spec(
        self,
        min_brightness: float = 30.0,
        max_blur:       float = 100.0,
        min_fps:        float = 25.0,
    ) -> None:
        """Assert camera image quality metrics within spec."""
        self._camera.assert_image_quality(
            min_brightness = float(min_brightness),
            max_blur_score = float(max_blur),
        )
        self._camera.assert_fps(min_fps=float(min_fps))
        logger.info("Camera image quality within spec ✓")

    # ── LiDAR ─────────────────────────────────────────────────────────────────

    @keyword("LiDAR Should Detect Obstacle")
    def lidar_should_detect_obstacle(
        self,
        pos_x_m:   float,
        pos_y_m:   float,
        pos_z_m:   float = 0.0,
        radius_m:  float = 1.0,
    ) -> None:
        """Assert LiDAR latest cloud contains obstacle at position."""
        self._lidar.assert_obstacle_detected(
            pos_x_m  = float(pos_x_m),
            pos_y_m  = float(pos_y_m),
            pos_z_m  = float(pos_z_m),
            radius_m = float(radius_m),
        )
        logger.info(f"LiDAR obstacle at ({pos_x_m}, {pos_y_m}) detected ✓")

    @keyword("LiDAR Should Have Minimum Points")
    def lidar_should_have_minimum_points(self, min_points: int = 100) -> None:
        """Assert LiDAR cloud has at least min_points."""
        self._lidar.assert_point_count(min_count=int(min_points))

    # ── Sensor Fusion ─────────────────────────────────────────────────────────

    @keyword("Inject Fused Object")
    def inject_fused_object(
        self,
        track_id:     int   = 1,
        pos_x_m:      float = 30.0,
        pos_y_m:      float = 0.0,
        velocity_mps: float = 20.0,
        confidence:   float = 0.90,
        source:       str   = "fused",
    ) -> None:
        """
        Inject a synthetic fused object into FusionValidator.

        Example:
            Inject Fused Object    track_id=1    pos_x_m=30    velocity_mps=20
        """
        self._fusion.ingest(FusedObject(
            track_id     = int(track_id),
            pos_x_m      = float(pos_x_m),
            pos_y_m      = float(pos_y_m),
            velocity_mps = float(velocity_mps),
            heading_deg  = 0.0,
            confidence   = float(confidence),
            source       = source,
        ))

    @keyword("Fusion Timestamps Should Be Synced")
    def fusion_timestamps_should_be_synced(
        self, sensor_a: str, sensor_b: str, max_skew_ms: float = 20.0
    ) -> None:
        """Assert fusion input timestamps aligned within tolerance."""
        self._fusion.assert_timestamp_sync(sensor_a, sensor_b, float(max_skew_ms))
        logger.info(
            f"Fusion timestamp skew {sensor_a}↔{sensor_b} ≤ {max_skew_ms}ms ✓"
        )

    @keyword("Fusion Should Track Object")
    def fusion_should_track_object(self, track_id: int) -> None:
        """Assert fusion output contains given track_id."""
        self._fusion.assert_object_fused(int(track_id))
        logger.info(f"Fusion tracking object {track_id} ✓")

    @keyword("Fusion Latency Should Be Under")
    def fusion_latency_should_be_under(
        self, sensor_name: str, max_mean_ms: float = 50.0
    ) -> None:
        """Assert fusion pipeline latency within limit."""
        self._fusion.assert_latency(sensor_name, float(max_mean_ms))
        logger.info(f"Fusion {sensor_name} latency ≤ {max_mean_ms}ms ✓")
