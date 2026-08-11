from __future__ import annotations

import pytest


@pytest.mark.regression
@pytest.mark.acc
@pytest.mark.parametrize("scenario_file", ["acc_scenarios.yaml"])
def test_acc_yaml_scenarios(scenario_file: str, scenario_loader, acc_controller) -> None:
    """Test ID: ACC_SCN_001
Requirement: ACC shall support YAML-driven scenario validation.
Objective: Verify configured scenarios execute deterministically."""
    scenarios = scenario_loader.load(scenario_file)
    for scenario in scenarios:
        acc_controller.deactivate()
        acc_controller.set_speed(scenario.data["set_speed_kph"])
        acc_controller.activate()
        lead = scenario.data.get("lead_vehicle")
        if "time_gap_s" in scenario.data:
            nearest = min(acc_controller.time_gap_settings, key=lambda gap: abs(gap - scenario.data["time_gap_s"]))
            acc_controller.set_time_gap(nearest)
        accel = acc_controller.update(
            vehicle_speed=scenario.data["ego_speed_kph"] / 3.6,
            lead_vehicle_distance=None if lead is None else lead["distance_m"],
            lead_vehicle_speed=None if lead is None else lead["speed_kph"] / 3.6,
        )
        assert acc_controller.get_state().name == scenario.data["expected_state"]
        if "expected_accel" in scenario.data:
            assert accel == pytest.approx(scenario.data["expected_accel"], abs=1.0)
    assert len(scenarios) >= 2
