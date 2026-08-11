from __future__ import annotations

import pytest

from adas.acc import ACCState
from vehicle.vehicle_state import VehicleState


@pytest.mark.system
@pytest.mark.acc
class TestACCSystem:
    def test_highway_cruise_holds_state_active(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_SYS_001
Requirement: ACC system shall sustain highway cruise.
Objective: Verify nominal cruise state."""
        acc_controller.activate()
        for _ in range(10):
            accel = acc_controller.update(33.33, None, None)
            vehicle_state.apply_acceleration(accel, 0.1)
        assert acc_controller.get_state() is ACCState.ACTIVE

    def test_following_mode_enters_braking(self, acc_controller) -> None:
        """Test ID: ACC_SYS_002
Requirement: ACC system shall maintain following distance.
Objective: Verify braking state in system flow."""
        acc_controller.activate()
        acc_controller.update(30.0, 18.0, 22.0)
        assert acc_controller.get_state() is ACCState.BRAKING

    def test_target_loss_recovers_to_active(self, acc_controller) -> None:
        """Test ID: ACC_SYS_003
Requirement: ACC system shall recover from target cut-out.
Objective: Verify cut-out sequence."""
        acc_controller.activate()
        acc_controller.update(30.0, 18.0, 22.0)
        acc_controller.update(28.0, None, None)
        assert acc_controller.get_state() is ACCState.ACTIVE

    def test_driver_override_in_system_flow(self, acc_controller) -> None:
        """Test ID: ACC_SYS_004
Requirement: ACC system shall hand control to driver override.
Objective: Verify override state in system context."""
        acc_controller.activate()
        acc_controller.update(28.0, None, None, brake_pressed=True)
        assert acc_controller.get_state() is ACCState.OVERRIDE

    def test_deactivation_clears_command(self, acc_controller) -> None:
        """Test ID: ACC_SYS_005
Requirement: ACC system shall clear command on deactivation.
Objective: Verify shutdown behavior."""
        acc_controller.activate()
        acc_controller.update(20.0, None, None)
        acc_controller.deactivate()
        assert acc_controller.compute_acceleration() == 0.0
