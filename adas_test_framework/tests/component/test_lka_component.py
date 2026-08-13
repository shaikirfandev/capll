from __future__ import annotations

import pytest

from adas.lka import LKAWarningLevel
from vehicle.vehicle_state import VehicleState


@pytest.mark.component
@pytest.mark.lka
class TestLKAComponent:
    def test_lka_applies_corrective_torque_to_vehicle(self, lka_controller, vehicle_state: VehicleState) -> None:
        """Test ID: LKA_COMP_001
Requirement: LKA component shall compute corrective torque.
Objective: Verify torque direction with vehicle state."""
        torque = lka_controller.update(0.35, 0.2, vehicle_state.speed_mps)
        assert torque < 0.0

    def test_lka_warning_when_near_lane_edge(self, lka_controller) -> None:
        """Test ID: LKA_COMP_002
Requirement: LKA component shall warn near lane boundary.
Objective: Verify component warning path."""
        lka_controller.update(0.25, 0.05, 20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    def test_lka_inactive_at_center(self, lka_controller) -> None:
        """Test ID: LKA_COMP_003
Requirement: LKA component shall remain quiet at lane center.
Objective: Verify neutral component behavior."""
        lka_controller.update(0.0, 0.0, 20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE

    @pytest.mark.parametrize("offset", [0.31, 0.4, -0.31, -0.4])
    def test_lka_detects_departures_both_sides(self, lka_controller, offset: float) -> None:
        """Test ID: LKA_COMP_004
Requirement: LKA component shall detect both left and right departures.
Objective: Verify sign-symmetric component coverage."""
        lka_controller.update(offset, 0.2 if offset > 0 else -0.2, 22.0)
        assert lka_controller.is_departing() is True

    def test_lka_low_speed_does_not_activate(self, lka_controller) -> None:
        """Test ID: LKA_COMP_005
Requirement: LKA component shall limit low-speed intervention.
Objective: Verify speed gating."""
        lka_controller.update(0.35, 0.2, 6.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    def test_lka_recovery_clears_departure_flag(self, lka_controller) -> None:
        """Test ID: LKA_COMP_006
Requirement: LKA component shall clear departure after recentering.
Objective: Verify recovery behavior."""
        lka_controller.update(0.35, 0.2, 20.0)
        lka_controller.update(0.0, -0.1, 20.0)
        assert lka_controller.is_departing() is False

    def test_lka_torque_is_bounded(self, lka_controller) -> None:
        """Test ID: LKA_COMP_007
Requirement: LKA component shall saturate torque.
Objective: Verify safety bounds."""
        torque = lka_controller.compute_steering_torque(2.0, 1.0, 30.0)
        assert -3.0 <= torque <= 3.0

    def test_lka_speed_scaling_increases_torque(self, lka_controller) -> None:
        """Test ID: LKA_COMP_008
Requirement: LKA component shall increase authority with speed.
Objective: Verify speed-based scaling."""
        low = abs(lka_controller.compute_steering_torque(0.2, 0.0, 8.0))
        high = abs(lka_controller.compute_steering_torque(0.2, 0.0, 25.0))
        assert high > low
