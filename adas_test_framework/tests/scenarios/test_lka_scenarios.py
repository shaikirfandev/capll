from __future__ import annotations

import pytest

from adas.lka import LKAWarningLevel


@pytest.mark.regression
@pytest.mark.lka
def test_lka_yaml_scenarios(scenario_loader, lka_controller) -> None:
    """Test ID: LKA_SCN_001
Requirement: LKA shall support YAML-driven scenario validation.
Objective: Verify scenario-based warning levels."""
    scenarios = scenario_loader.load("lka_scenarios.yaml")
    for scenario in scenarios:
        lka_controller.update(
            lane_offset_m=scenario.data["lane_offset_m"],
            lateral_speed_mps=scenario.data["lateral_speed_mps"],
            vehicle_speed_mps=scenario.data["vehicle_speed_kph"] / 3.6,
        )
        assert lka_controller.get_warning_level() is LKAWarningLevel[scenario.data["expected_level"]]
    assert len(scenarios) >= 3
