from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType
from sensors.camera import CameraDetection
from sensors.radar import RadarDetection
from sensors.sensor_fusion import SensorFusion


@pytest.mark.safety
class TestDegradation:
    def test_fusion_degrades_without_camera(self) -> None:
        """Test ID: DEG_001
Requirement: System shall degrade gracefully on camera loss.
Objective: Verify radar-only fallback."""
        fusion = SensorFusion()
        tracks = fusion.fuse(radar_detections=[RadarDetection(1, 20.0, -2.0)], timestamp=1.0)
        assert len(tracks) == 1

    def test_fusion_degrades_without_radar(self) -> None:
        """Test ID: DEG_002
Requirement: System shall degrade gracefully on radar loss.
Objective: Verify camera-only fallback."""
        fusion = SensorFusion()
        tracks = fusion.fuse(camera_detections=[CameraDetection(1, 20.0, 0.2, -1.0)], timestamp=1.0)
        assert len(tracks) == 1

    def test_lka_warns_when_low_speed_prevents_active(self, lka_controller) -> None:
        """Test ID: DEG_003
Requirement: LKA shall degrade to warning-only when active assist unavailable.
Objective: Verify low-speed degraded mode."""
        lka_controller.update(0.35, 0.2, 7.0)
        assert lka_controller.get_warning_level().name == "WARNING"

    def test_aeb_non_intervention_when_stationary(self, aeb_controller) -> None:
        """Test ID: DEG_004
Requirement: AEB shall degrade to inactive at standstill.
Objective: Verify stationary degraded mode."""
        assert aeb_controller.update(0.0, 3.0, 0.0, TargetType.PEDESTRIAN) is InterventionLevel.NONE

    def test_fault_injector_corruption_can_be_cleared(self, fault_injector) -> None:
        """Test ID: DEG_005
Requirement: Degradation utilities shall restore nominal signal path.
Objective: Verify fault cleanup."""
        fault_injector.inject_signal_corruption("speed", 0)
        fault_injector.clear_fault("speed")
        assert fault_injector.apply_faults({"speed": 30})["speed"] == 30
