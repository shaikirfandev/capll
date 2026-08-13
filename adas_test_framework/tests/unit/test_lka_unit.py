from __future__ import annotations

import pytest

from adas.lka import LKAController, LKAWarningLevel


@pytest.mark.unit
@pytest.mark.lka
class TestLKAUnit:
    def test_no_departure_inside_nominal_lane(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_001
Requirement: LKA shall not warn in nominal lane position.
Objective: Verify neutral lane behavior."""
        torque = lka_controller.update(lane_offset_m=0.05, lateral_speed_mps=0.0, vehicle_speed_mps=20.0)
        assert torque < 0.5
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE

    def test_warning_near_threshold(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_002
Requirement: LKA shall warn near departure threshold.
Objective: Verify early warning behavior."""
        lka_controller.update(lane_offset_m=0.26, lateral_speed_mps=0.1, vehicle_speed_mps=20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    def test_active_when_departing_outward(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_003
Requirement: LKA shall actively intervene during lane departure.
Objective: Verify ACTIVE warning level."""
        torque = lka_controller.update(lane_offset_m=0.35, lateral_speed_mps=0.2, vehicle_speed_mps=22.0)
        assert lka_controller.is_departing() is True
        assert lka_controller.get_warning_level() is LKAWarningLevel.ACTIVE
        assert torque < 0.0

    def test_torque_direction_pushes_back_to_lane_center(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_004
Requirement: LKA steering torque shall oppose lane departure.
Objective: Verify torque sign for positive offset."""
        torque = lka_controller.compute_steering_torque(lane_offset_m=0.3, lateral_speed_mps=0.1, vehicle_speed_mps=25.0)
        assert torque < 0.0

    def test_torque_saturates_at_limits(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_005
Requirement: LKA torque shall stay within calibrated bounds.
Objective: Verify steering torque saturation."""
        torque = lka_controller.compute_steering_torque(lane_offset_m=3.0, lateral_speed_mps=2.0, vehicle_speed_mps=40.0)
        assert torque == pytest.approx(-3.0)

    def test_low_speed_limits_active_intervention(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_006
Requirement: LKA shall avoid active intervention at low speed.
Objective: Verify low-speed mode handling."""
        lka_controller.update(lane_offset_m=0.35, lateral_speed_mps=0.2, vehicle_speed_mps=8.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    @pytest.mark.parametrize("offset", [0.3, -0.3, 0.45, -0.45])
    def test_lane_departure_detection_sign_agnostic(self, lka_controller: LKAController, offset: float) -> None:
        """Test ID: LKA_UNIT_007
Requirement: LKA shall detect departures to either side.
Objective: Verify symmetric threshold detection."""
        lka_controller.update(lane_offset_m=offset, lateral_speed_mps=0.2 if offset > 0 else -0.2, vehicle_speed_mps=18.0)
        assert lka_controller.is_departing() is True

    def test_curved_road_centered_vehicle_does_not_trigger(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_008
Requirement: LKA shall tolerate curved roads when centered.
Objective: Verify lateral-speed-only case stays inactive."""
        lka_controller.update(lane_offset_m=0.02, lateral_speed_mps=0.4, vehicle_speed_mps=25.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE

    def test_negative_offset_generates_positive_torque(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_009
Requirement: LKA torque shall oppose negative lane offsets.
Objective: Verify torque sign for left departures."""
        torque = lka_controller.compute_steering_torque(lane_offset_m=-0.3, lateral_speed_mps=-0.1, vehicle_speed_mps=25.0)
        assert torque > 0.0

    def test_warning_clears_after_recenter(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_010
Requirement: LKA warning shall clear after recovery.
Objective: Verify hysteresis-free recovery."""
        lka_controller.update(lane_offset_m=0.35, lateral_speed_mps=0.2, vehicle_speed_mps=20.0)
        lka_controller.update(lane_offset_m=0.01, lateral_speed_mps=-0.1, vehicle_speed_mps=20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE

    def test_threshold_exact_value_can_activate(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_011
Requirement: LKA shall treat threshold crossings deterministically.
Objective: Verify exact threshold behavior."""
        lka_controller.update(lane_offset_m=0.3, lateral_speed_mps=0.05, vehicle_speed_mps=20.0)
        assert lka_controller.get_warning_level() in (LKAWarningLevel.WARNING, LKAWarningLevel.ACTIVE)

    def test_torque_scales_with_speed(self, lka_controller: LKAController) -> None:
        """Test ID: LKA_UNIT_012
Requirement: LKA torque shall scale with vehicle speed.
Objective: Verify higher speed raises correction authority."""
        low_speed = abs(lka_controller.compute_steering_torque(lane_offset_m=0.2, lateral_speed_mps=0.0, vehicle_speed_mps=10.0))
        high_speed = abs(lka_controller.compute_steering_torque(lane_offset_m=0.2, lateral_speed_mps=0.0, vehicle_speed_mps=25.0))
        assert high_speed > low_speed
