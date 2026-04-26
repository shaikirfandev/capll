#!/usr/bin/env python3
"""Section 2: LIN schedule and frame timing validation example."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LinScheduleSlot:
    frame_id: int
    period_ms: int


@dataclass
class LinMeasurement:
    frame_id: int
    timestamps_ms: List[int]


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def validate_lin_schedule(
    schedule: List[LinScheduleSlot],
    measurements: Dict[int, LinMeasurement],
    jitter_tolerance_ms: int,
) -> List[CheckResult]:
    results: List[CheckResult] = []

    for slot in schedule:
        meas = measurements.get(slot.frame_id)
        if not meas or len(meas.timestamps_ms) < 2:
            results.append(CheckResult(
                name=f"Frame 0x{slot.frame_id:02X} availability",
                passed=False,
                details="Frame missing or insufficient samples",
            ))
            continue

        deltas = [
            meas.timestamps_ms[i] - meas.timestamps_ms[i - 1]
            for i in range(1, len(meas.timestamps_ms))
        ]
        worst_jitter = max(abs(delta - slot.period_ms) for delta in deltas)
        passed = worst_jitter <= jitter_tolerance_ms

        results.append(CheckResult(
            name=f"Frame 0x{slot.frame_id:02X} schedule timing",
            passed=passed,
            details=f"period={slot.period_ms}ms, worst_jitter={worst_jitter}ms",
        ))

    return results


def main() -> None:
    schedule = [
        LinScheduleSlot(frame_id=0x10, period_ms=20),
        LinScheduleSlot(frame_id=0x11, period_ms=40),
        LinScheduleSlot(frame_id=0x12, period_ms=100),
    ]

    measurements = {
        0x10: LinMeasurement(0x10, [0, 20, 40, 60, 80]),
        0x11: LinMeasurement(0x11, [0, 41, 80, 120, 160]),
        0x12: LinMeasurement(0x12, [0, 100, 200, 299, 400]),
    }

    results = validate_lin_schedule(schedule, measurements, jitter_tolerance_ms=3)

    print("=== LIN Schedule Validation Report ===")
    passed = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        passed += int(r.passed)
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
