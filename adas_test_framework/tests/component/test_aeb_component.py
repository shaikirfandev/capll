from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType
from adas.fcw import FCWController


@pytest.mark.component
@pytest.mark.aeb
class TestAEBComponent:
    def test_aeb_warning_can_precede_braking(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_001
Requirement: AEB component shall warn before braking.
Objective: Verify warning-stage output."""
        level = aeb_controller.update(20.0, 24.0, 11.0, TargetType.VEHICLE)
        assert level is InterventionLevel.WARNING

    def test_aeb_full_brake_for_pedestrian(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_002
Requirement: AEB component shall escalate on pedestrian threat.
Objective: Verify pedestrian full-brake case."""
        level = aeb_controller.update(18.0, 8.0, 0.0, TargetType.PEDESTRIAN)
        assert level is InterventionLevel.FULL_BRAKE

    def test_aeb_and_fcw_alignment(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_003
Requirement: FCW warning shall align with early AEB phases.
Objective: Verify FCW/AEB consistency."""
        fcw = FCWController()
        fcw_active = fcw.update(20.0, 17.0, 13.0)
        level = aeb_controller.update(20.0, 17.0, 13.0, TargetType.VEHICLE)
        assert fcw_active is True
        assert level is InterventionLevel.WARNING

    def test_aeb_inactive_for_far_vehicle(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_004
Requirement: AEB component shall ignore far targets.
Objective: Verify distance gating."""
        level = aeb_controller.update(25.0, 120.0, 0.0, TargetType.VEHICLE)
        assert level is InterventionLevel.NONE

    @pytest.mark.parametrize("target_type", [TargetType.VEHICLE, TargetType.PEDESTRIAN, TargetType.CYCLIST])
    def test_aeb_supports_all_target_types(self, aeb_controller, target_type) -> None:
        """Test ID: AEB_COMP_005
Requirement: AEB component shall support calibrated target classes.
Objective: Verify all target-type pathways execute."""
        level = aeb_controller.update(15.0, 20.0, 5.0, target_type)
        assert level in set(InterventionLevel)

    def test_aeb_seed_false_positive_case(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_006
Requirement: AEB component shall not trigger on receding targets.
Objective: Verify negative closing speed behavior."""
        level = aeb_controller.update(10.0, 12.0, 15.0, TargetType.CYCLIST)
        assert level is InterventionLevel.NONE

    def test_aeb_reports_latest_ttc(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_007
Requirement: AEB component shall provide latest TTC to observers.
Objective: Verify observability of internal estimate."""
        aeb_controller.update(12.0, 24.0, 6.0, TargetType.VEHICLE)
        assert aeb_controller.last_ttc == pytest.approx(4.0)

    def test_aeb_active_flag_tracks_intervention(self, aeb_controller) -> None:
        """Test ID: AEB_COMP_008
Requirement: AEB component shall expose active status.
Objective: Verify active flag transitions."""
        aeb_controller.update(20.0, 18.0, 10.0, TargetType.VEHICLE)
        assert aeb_controller.is_active() is True
