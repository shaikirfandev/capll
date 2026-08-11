from __future__ import annotations

import pytest

from adas.lka import LKAWarningLevel


@pytest.mark.system
@pytest.mark.lka
class TestLKASystem:
    def test_centered_lane_system_case(self, lka_controller) -> None:
        """Test ID: LKA_SYS_001
Requirement: LKA system shall remain idle near lane center.
Objective: Verify nominal cruise behavior."""
        lka_controller.update(0.05, 0.0, 20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE

    def test_warning_zone_system_case(self, lka_controller) -> None:
        """Test ID: LKA_SYS_002
Requirement: LKA system shall warn before departure.
Objective: Verify warning stage."""
        lka_controller.update(0.25, 0.05, 20.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    def test_active_departure_system_case(self, lka_controller) -> None:
        """Test ID: LKA_SYS_003
Requirement: LKA system shall intervene during lane departure.
Objective: Verify active assistance stage."""
        lka_controller.update(0.35, 0.2, 22.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.ACTIVE

    def test_low_speed_limits_activation(self, lka_controller) -> None:
        """Test ID: LKA_SYS_004
Requirement: LKA system shall limit low-speed activation.
Objective: Verify low-speed system gating."""
        lka_controller.update(0.35, 0.2, 8.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.WARNING

    def test_recovery_clears_warning(self, lka_controller) -> None:
        """Test ID: LKA_SYS_005
Requirement: LKA system shall clear warnings after recentering.
Objective: Verify recovery flow."""
        lka_controller.update(0.35, 0.2, 22.0)
        lka_controller.update(0.0, -0.1, 22.0)
        assert lka_controller.get_warning_level() is LKAWarningLevel.NONE
