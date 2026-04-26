#!/usr/bin/env python3
"""Section 7: ADAS scenario automation example (AEB + LDW)."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


@dataclass
class ScenarioSample:
    t_ms: int
    ego_speed_mps: float
    target_speed_mps: float
    target_distance_m: float
    lane_offset_m: float


def compute_ttc(distance_m: float, relative_speed_mps: float) -> float:
    if relative_speed_mps <= 0:
        return float("inf")
    return distance_m / relative_speed_mps


def evaluate_aeb(samples: List[ScenarioSample], trigger_ttc_s: float) -> Optional[ScenarioSample]:
    for sample in samples:
        rel_speed = max(sample.ego_speed_mps - sample.target_speed_mps, 0.0)
        ttc = compute_ttc(sample.target_distance_m, rel_speed)
        if ttc <= trigger_ttc_s:
            return sample
    return None


def evaluate_ldw(samples: List[ScenarioSample], offset_threshold_m: float, hold_ms: int) -> Optional[int]:
    above_threshold_start = None
    for s in samples:
        if abs(s.lane_offset_m) > offset_threshold_m:
            if above_threshold_start is None:
                above_threshold_start = s.t_ms
            if s.t_ms - above_threshold_start >= hold_ms:
                return s.t_ms
        else:
            above_threshold_start = None
    return None


def run_adas_tests() -> List[CheckResult]:
    results: List[CheckResult] = []

    # AEB scenario: ego approaches slower target vehicle.
    aeb_samples = [
        ScenarioSample(0, 22.0, 10.0, 55.0, 0.05),
        ScenarioSample(200, 22.0, 10.0, 50.0, 0.03),
        ScenarioSample(400, 22.0, 10.0, 45.0, 0.02),
        ScenarioSample(600, 22.0, 10.0, 35.0, 0.04),
        ScenarioSample(800, 22.0, 10.0, 25.0, 0.01),
        ScenarioSample(1000, 22.0, 10.0, 16.0, 0.00),
    ]
    trigger = evaluate_aeb(aeb_samples, trigger_ttc_s=1.5)

    results.append(CheckResult(
        name="AEB trigger present",
        passed=trigger is not None,
        details=f"trigger_time={None if trigger is None else trigger.t_ms}ms",
    ))

    if trigger is not None:
        rel_speed = trigger.ego_speed_mps - trigger.target_speed_mps
        ttc = compute_ttc(trigger.target_distance_m, rel_speed)
        results.append(CheckResult(
            name="AEB trigger TTC threshold",
            passed=ttc <= 1.5,
            details=f"ttc={ttc:.2f}s",
        ))
        results.append(CheckResult(
            name="AEB trigger before collision",
            passed=trigger.target_distance_m > 0,
            details=f"distance_at_trigger={trigger.target_distance_m:.2f}m",
        ))

    # LDW scenario: sustained lane departure.
    ldw_samples = [
        ScenarioSample(0, 15.0, 15.0, 999.0, 0.10),
        ScenarioSample(200, 15.0, 15.0, 999.0, 0.30),
        ScenarioSample(400, 15.0, 15.0, 999.0, 0.75),
        ScenarioSample(700, 15.0, 15.0, 999.0, 0.82),
        ScenarioSample(1000, 15.0, 15.0, 999.0, 0.88),
    ]
    ldw_trigger_ms = evaluate_ldw(ldw_samples, offset_threshold_m=0.7, hold_ms=500)
    results.append(CheckResult(
        name="LDW trigger present",
        passed=ldw_trigger_ms is not None,
        details=f"trigger_time={ldw_trigger_ms}",
    ))

    # False positive check: centered lane should not trigger.
    centered_lane_samples = [
        ScenarioSample(i * 200, 20.0, 20.0, 999.0, 0.15) for i in range(8)
    ]
    no_false_trigger = evaluate_ldw(centered_lane_samples, 0.7, 500) is None
    results.append(CheckResult(
        name="No LDW false trigger on centered lane",
        passed=no_false_trigger,
        details="offset stayed within +/-0.15m",
    ))

    return results


def main() -> None:
    results = run_adas_tests()
    passed = sum(1 for r in results if r.passed)

    print("=== ADAS Scenario Validation Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
