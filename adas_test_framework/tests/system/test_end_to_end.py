from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType
from sensors.camera import CameraDetection
from sensors.radar import RadarDetection
from sensors.sensor_fusion import SensorFusion
from vehicle.vehicle_state import VehicleState


@pytest.mark.system
class TestEndToEnd:
    def test_acc_and_vehicle_state_end_to_end(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: E2E_001
Requirement: End-to-end flow shall support ACC cruise.
Objective: Verify controller, vehicle, and timing interplay."""
        acc_controller.activate()
        for _ in range(5):
            vehicle_state.apply_acceleration(acc_controller.update(vehicle_state.speed_mps - 3.0, None, None), 0.1)
        assert vehicle_state.speed_mps > 30.0

    def test_aeb_and_fusion_end_to_end(self, aeb_controller) -> None:
        """Test ID: E2E_002
Requirement: End-to-end flow shall support fusion-informed AEB.
Objective: Verify fused target can drive AEB."""
        fusion = SensorFusion()
        track = fusion.fuse(
            camera_detections=[CameraDetection(1, 12.0, 0.0, -8.0, 0.9)],
            radar_detections=[RadarDetection(1, 11.5, -8.0, 0.0, 0.9)],
            timestamp=1.0,
        )[0]
        level = aeb_controller.update(25.0, track.distance_m, 17.0, TargetType.VEHICLE)
        assert level in (InterventionLevel.PREFILL, InterventionLevel.PARTIAL_BRAKE, InterventionLevel.FULL_BRAKE)

    def test_lka_and_vehicle_state_end_to_end(self, lka_controller, vehicle_state: VehicleState) -> None:
        """Test ID: E2E_003
Requirement: End-to-end flow shall support lane assistance.
Objective: Verify steering correction chain."""
        torque = lka_controller.update(0.35, 0.2, vehicle_state.speed_mps)
        vehicle_state.steer(lane_offset=0.2, yaw_rate=torque * 0.1)
        assert vehicle_state.yaw_rate < 0.0

    def test_diagnostics_end_to_end(self, uds_client) -> None:
        """Test ID: E2E_004
Requirement: End-to-end flow shall support diagnostics.
Objective: Verify DTC lifecycle through UDS client."""
        uds_client.server.dtc_manager.set_dtc(0x123456, description="camera timeout")
        assert len(uds_client.read_dtc_information()) == 1
        uds_client.clear_diagnostic_information()
        assert uds_client.read_dtc_information() == []

    def test_fault_injection_end_to_end(self, fault_injector, can_interface) -> None:
        """Test ID: E2E_005
Requirement: End-to-end flow shall support fault injection.
Objective: Verify injected CAN suppression affects transport."""
        fault_injector.suppress_can_id(0x123)
        can_interface.send(0x123, [1, 2, 3])
        assert can_interface.recv(0x123) is None
