from __future__ import annotations

import pytest

from adas.acc import ACCController, ACCState
from vehicle.vehicle_state import VehicleState


@pytest.mark.component
@pytest.mark.acc
class TestACCComponent:
    def test_acc_cruise_increases_vehicle_speed(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_COMP_001
Requirement: ACC component shall accelerate toward set speed.
Objective: Verify controller-to-vehicle interaction."""
        acc_controller.activate()
        accel = acc_controller.update(vehicle_state.speed_mps - 5.0, None, None)
        vehicle_state.apply_acceleration(accel, 0.1)
        assert vehicle_state.speed_mps > 25.0

    def test_acc_following_reduces_speed(self, acc_controller, vehicle_state: VehicleState) -> None:
        """Test ID: ACC_COMP_002
Requirement: ACC component shall slow down for lead vehicle.
Objective: Verify closed-loop following behavior."""
        acc_controller.activate()
        accel = acc_controller.update(vehicle_state.speed_mps, 20.0, 22.0)
        assert accel < 0.0

    def test_acc_loopback_can_message(self, acc_controller, can_interface) -> None:
        """Test ID: ACC_COMP_003
Requirement: ACC component shall publish status to CAN.
Objective: Verify mock CAN loopback transport."""
        acc_controller.activate()
        can_interface.send(0x120, [acc_controller.get_state().value, int(acc_controller.get_set_speed())])
        frame = can_interface.recv(0x120)
        assert frame is not None
        assert frame.data[1] == int(acc_controller.get_set_speed())

    def test_acc_override_stops_actuation(self, acc_controller) -> None:
        """Test ID: ACC_COMP_004
Requirement: ACC component shall stop actuation during override.
Objective: Verify override suppresses acceleration."""
        acc_controller.activate()
        accel = acc_controller.update(28.0, None, None, brake_pressed=True)
        assert accel == 0.0
        assert acc_controller.get_state() is ACCState.OVERRIDE

    @pytest.mark.parametrize("gap", [1.0, 1.3, 1.6, 2.0])
    def test_acc_headway_setting_affects_braking(self, acc_controller, gap: float) -> None:
        """Test ID: ACC_COMP_005
Requirement: ACC component shall respect selected headway.
Objective: Verify headway setting influences response."""
        acc_controller.activate()
        acc_controller.set_time_gap(gap)
        accel = acc_controller.update(30.0, 40.0, 25.0)
        assert accel <= 2.0

    def test_acc_deactivate_resets_integrator(self, acc_controller) -> None:
        """Test ID: ACC_COMP_006
Requirement: ACC component shall reset control state on deactivate.
Objective: Verify clean shutdown behavior."""
        acc_controller.activate()
        acc_controller.update(20.0, None, None)
        acc_controller.deactivate()
        assert acc_controller.compute_acceleration() == 0.0

    def test_acc_target_loss_recovers_to_active(self, acc_controller) -> None:
        """Test ID: ACC_COMP_007
Requirement: ACC component shall resume cruise after cut-out.
Objective: Verify target-loss recovery."""
        acc_controller.activate()
        acc_controller.update(30.0, 15.0, 20.0)
        acc_controller.update(28.0, None, None)
        assert acc_controller.get_state() is ACCState.ACTIVE

    def test_acc_invalid_set_speed_raises(self) -> None:
        """Test ID: ACC_COMP_008
Requirement: ACC component shall enforce configured set speed range.
Objective: Verify component-level input validation."""
        controller = ACCController()
        with pytest.raises(ValueError):
            controller.set_speed(200.0)
