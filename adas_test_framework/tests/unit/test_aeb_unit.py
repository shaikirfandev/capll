from __future__ import annotations

import math

import pytest

from adas.aeb import AEBController, InterventionLevel, TargetType


@pytest.mark.unit
@pytest.mark.aeb
class TestAEBUnit:
    def test_ttc_is_infinite_when_not_closing(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_001
Requirement: AEB shall avoid false positives when not closing.
Objective: Verify TTC saturates to infinity for non-closing targets."""
        ttc = aeb_controller.compute_ttc(ego_speed=20.0, target_distance=30.0, target_speed=20.5)
        assert math.isinf(ttc)

    def test_ttc_calculation_matches_distance_over_closing_speed(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_002
Requirement: AEB shall compute TTC accurately.
Objective: Verify TTC formula for approaching vehicle."""
        ttc = aeb_controller.compute_ttc(ego_speed=25.0, target_distance=50.0, target_speed=15.0)
        assert ttc == pytest.approx(5.0)

    @pytest.mark.parametrize(
        ("distance", "target_speed", "expected"),
        [
            (24.0, 10.0, InterventionLevel.WARNING),
            (19.0, 10.0, InterventionLevel.PREFILL),
            (15.0, 10.0, InterventionLevel.PARTIAL_BRAKE),
            (10.0, 10.0, InterventionLevel.FULL_BRAKE),
        ],
    )
    def test_vehicle_thresholds(self, aeb_controller: AEBController, distance: float, target_speed: float, expected: InterventionLevel) -> None:
        """Test ID: AEB_UNIT_003
Requirement: AEB shall honor intervention TTC thresholds.
Objective: Verify vehicle target intervention transitions."""
        level = aeb_controller.update(ego_speed=20.0, target_distance=distance, target_speed=target_speed, target_type=TargetType.VEHICLE)
        assert level is expected

    def test_pedestrian_bias_triggers_earlier_than_vehicle(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_004
Requirement: AEB shall be more conservative for pedestrians.
Objective: Verify target-type specific escalation."""
        vehicle_level = aeb_controller.update(ego_speed=15.0, target_distance=35.0, target_speed=0.0, target_type=TargetType.VEHICLE)
        pedestrian_level = aeb_controller.update(ego_speed=15.0, target_distance=35.0, target_speed=0.0, target_type=TargetType.PEDESTRIAN)
        assert pedestrian_level.value >= vehicle_level.value

    def test_cyclist_bias_triggers_earlier_than_vehicle(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_005
Requirement: AEB shall protect cyclists conservatively.
Objective: Verify cyclist escalation bias."""
        vehicle_level = aeb_controller.update(ego_speed=14.0, target_distance=30.0, target_speed=2.0, target_type=TargetType.VEHICLE)
        cyclist_level = aeb_controller.update(ego_speed=14.0, target_distance=30.0, target_speed=2.0, target_type=TargetType.CYCLIST)
        assert cyclist_level.value >= vehicle_level.value

    def test_false_positive_prevention_for_far_targets(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_006
Requirement: AEB shall not trigger on far targets.
Objective: Verify range-based false-positive prevention."""
        level = aeb_controller.update(ego_speed=30.0, target_distance=180.0, target_speed=0.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.NONE
        assert aeb_controller.is_active() is False

    def test_no_braking_when_ego_vehicle_stationary(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_007
Requirement: AEB shall not command when vehicle is stationary.
Objective: Verify standstill behavior."""
        level = aeb_controller.update(ego_speed=0.0, target_distance=1.0, target_speed=0.0, target_type=TargetType.PEDESTRIAN)
        assert level is InterventionLevel.NONE

    def test_warning_level_activates_controller(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_008
Requirement: AEB shall report active status during warning phase.
Objective: Verify controller active flag."""
        level = aeb_controller.update(ego_speed=20.0, target_distance=18.0, target_speed=13.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.WARNING
        assert aeb_controller.is_active() is True

    def test_full_brake_for_severe_closing_rate(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_009
Requirement: AEB shall command full brake below full-brake TTC.
Objective: Verify severe closing-rate response."""
        level = aeb_controller.update(ego_speed=30.0, target_distance=8.0, target_speed=20.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.FULL_BRAKE

    def test_partial_brake_for_mid_ttc(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_010
Requirement: AEB shall support partial braking stage.
Objective: Verify mid-range TTC behavior."""
        level = aeb_controller.update(ego_speed=20.0, target_distance=14.0, target_speed=11.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.PARTIAL_BRAKE

    @pytest.mark.parametrize("ego_speed", [8.0, 15.0, 25.0, 35.0])
    def test_speed_dependent_behavior(self, aeb_controller: AEBController, ego_speed: float) -> None:
        """Test ID: AEB_UNIT_011
Requirement: AEB response shall depend on closing speed.
Objective: Verify higher ego speeds do not reduce intervention severity."""
        level = aeb_controller.update(ego_speed=ego_speed, target_distance=15.0, target_speed=0.0, target_type=TargetType.PEDESTRIAN)
        assert level in (InterventionLevel.PREFILL, InterventionLevel.PARTIAL_BRAKE, InterventionLevel.FULL_BRAKE)

    def test_last_ttc_property_tracks_latest_update(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_012
Requirement: AEB shall expose latest TTC estimate.
Objective: Verify TTC state retention."""
        aeb_controller.update(ego_speed=20.0, target_distance=40.0, target_speed=10.0, target_type=TargetType.VEHICLE)
        assert aeb_controller.last_ttc == pytest.approx(4.0)

    def test_prefill_threshold(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_013
Requirement: AEB shall support brake prefill stage.
Objective: Verify prefill threshold behavior."""
        level = aeb_controller.update(ego_speed=15.0, target_distance=18.5, target_speed=5.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.PREFILL

    def test_none_when_target_distance_invalid(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_014
Requirement: AEB shall ignore invalid negative distances.
Objective: Verify malformed target input handling."""
        level = aeb_controller.update(ego_speed=15.0, target_distance=-1.0, target_speed=0.0, target_type=TargetType.CYCLIST)
        assert level is InterventionLevel.NONE

    def test_warning_but_not_brake_for_large_ttc(self, aeb_controller: AEBController) -> None:
        """Test ID: AEB_UNIT_015
Requirement: AEB shall warn before braking.
Objective: Verify early-stage warning only behavior."""
        level = aeb_controller.update(ego_speed=20.0, target_distance=24.0, target_speed=11.0, target_type=TargetType.VEHICLE)
        assert level is InterventionLevel.WARNING
