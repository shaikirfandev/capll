from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType


@pytest.mark.system
@pytest.mark.aeb
class TestAEBSystem:
    def test_vehicle_warning_system_case(self, aeb_controller) -> None:
        """Test ID: AEB_SYS_001
Requirement: AEB system shall issue vehicle warning before braking.
Objective: Verify warning stage in system flow."""
        assert aeb_controller.update(20.0, 18.0, 13.0, TargetType.VEHICLE) is InterventionLevel.WARNING

    def test_vehicle_full_brake_system_case(self, aeb_controller) -> None:
        """Test ID: AEB_SYS_002
Requirement: AEB system shall full-brake for severe closing TTC.
Objective: Verify emergency stop behavior."""
        assert aeb_controller.update(25.0, 10.0, 15.0, TargetType.VEHICLE) is InterventionLevel.FULL_BRAKE

    def test_pedestrian_system_case(self, aeb_controller) -> None:
        """Test ID: AEB_SYS_003
Requirement: AEB system shall protect pedestrians.
Objective: Verify pedestrian escalation."""
        assert aeb_controller.update(12.0, 8.0, 0.0, TargetType.PEDESTRIAN) in (InterventionLevel.PARTIAL_BRAKE, InterventionLevel.FULL_BRAKE)

    def test_cyclist_system_case(self, aeb_controller) -> None:
        """Test ID: AEB_SYS_004
Requirement: AEB system shall protect cyclists.
Objective: Verify cyclist response."""
        assert aeb_controller.update(15.0, 12.0, 2.0, TargetType.CYCLIST) is not InterventionLevel.NONE

    def test_far_target_no_intervention(self, aeb_controller) -> None:
        """Test ID: AEB_SYS_005
Requirement: AEB system shall avoid far-target false positives.
Objective: Verify non-intervention case."""
        assert aeb_controller.update(25.0, 160.0, 0.0, TargetType.VEHICLE) is InterventionLevel.NONE
