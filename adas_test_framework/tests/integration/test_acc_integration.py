from __future__ import annotations

import pytest

from adas.acc import ACCState
from vehicle.vehicle_state import VehicleState


@pytest.mark.integration
@pytest.mark.acc
class TestACCIntegration:
    def test_acc_vehicle_closed_loop_reaches_active(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_INT_001
Requirement: ACC integration shall sustain active cruise.
Objective: Verify closed-loop state progression."""
        acc_controller.activate()
        for _ in range(5):
            accel = acc_controller.update(vehicle_state.speed_mps, None, None)
            vehicle_state.apply_acceleration(accel, 0.1)
        assert acc_controller.get_state() is ACCState.ACTIVE

    def test_acc_integration_slows_for_lead_vehicle(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_INT_002
Requirement: ACC integration shall react to lead vehicle.
Objective: Verify braking integration path."""
        acc_controller.activate()
        accel = acc_controller.update(vehicle_state.speed_mps, 18.0, 22.0)
        vehicle_state.apply_acceleration(accel, 0.1)
        assert vehicle_state.acceleration < 0.0

    def test_acc_can_trace_contains_command(self, acc_controller, can_interface) -> None:
        """Test ID: ACC_INT_003
Requirement: ACC integration shall publish command frames.
Objective: Verify CAN traceability."""
        acc_controller.activate()
        accel = acc_controller.update(28.0, None, None)
        can_interface.send(0x120, [int((accel + 10) * 10)])
        assert len(can_interface.tx_history) == 1

    def test_acc_integration_resumes_after_target_loss(self, acc_controller) -> None:
        """Test ID: ACC_INT_004
Requirement: ACC integration shall resume cruise after target cut-out.
Objective: Verify recovery sequence."""
        acc_controller.activate()
        acc_controller.update(30.0, 18.0, 20.0)
        acc_controller.update(28.0, None, None)
        assert acc_controller.get_state() is ACCState.ACTIVE

    def test_acc_integration_handles_override(self, acc_controller) -> None:
        """Test ID: ACC_INT_005
Requirement: ACC integration shall respect driver override.
Objective: Verify override sequence."""
        acc_controller.activate()
        acc_controller.update(30.0, None, None, throttle_override=True)
        assert acc_controller.get_state() is ACCState.OVERRIDE

    def test_acc_integration_speed_clamps_to_nonnegative(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_INT_006
Requirement: ACC integration shall avoid negative vehicle speed.
Objective: Verify vehicle model safety clamp."""
        acc_controller.activate()
        vehicle_state.apply_acceleration(-100.0, 1.0)
        assert vehicle_state.speed_mps >= 0.0
