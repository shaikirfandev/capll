from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType


@pytest.mark.regression
@pytest.mark.aeb
def test_aeb_yaml_scenarios(scenario_loader, aeb_controller) -> None:
    """Test ID: AEB_SCN_001
Requirement: AEB shall support YAML-driven scenario validation.
Objective: Verify scenario-based intervention levels."""
    scenarios = scenario_loader.load("aeb_scenarios.yaml")
    for scenario in scenarios:
        level = aeb_controller.update(
            ego_speed=scenario.data["ego_speed_kph"] / 3.6,
            target_distance=scenario.data["target_distance_m"],
            target_speed=scenario.data["target_speed_kph"] / 3.6,
            target_type=TargetType[scenario.data["target_type"]],
        )
        assert level is InterventionLevel[scenario.data["expected_level"]]
    assert len(scenarios) >= 3
