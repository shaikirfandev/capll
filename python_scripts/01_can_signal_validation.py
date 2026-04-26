#!/usr/bin/env python3
"""Section 1: CAN signal validation automation example."""

from dataclasses import dataclass
from typing import List


@dataclass
class CANFrame:
    timestamp_ms: int
    can_id: int
    data: bytes


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def decode_speed_kph(frame: CANFrame) -> float:
    # Example: speed in first two bytes, scale 0.01 kph/bit
    raw = (frame.data[0] << 8) | frame.data[1]
    return raw * 0.01


def decode_rpm(frame: CANFrame) -> float:
    # Example: RPM in bytes 2-3, scale 0.25 rpm/bit
    raw = (frame.data[2] << 8) | frame.data[3]
    return raw * 0.25


def check_cycle_time(frames: List[CANFrame], max_cycle_ms: int) -> CheckResult:
    deltas = [frames[i].timestamp_ms - frames[i - 1].timestamp_ms for i in range(1, len(frames))]
    worst = max(deltas)
    passed = worst <= max_cycle_ms
    return CheckResult(
        name="CAN cycle time",
        passed=passed,
        details=f"worst={worst}ms, limit={max_cycle_ms}ms",
    )


def check_signal_ranges(frames: List[CANFrame]) -> List[CheckResult]:
    results: List[CheckResult] = []
    for i, frame in enumerate(frames):
        speed = decode_speed_kph(frame)
        rpm = decode_rpm(frame)

        speed_ok = 0.0 <= speed <= 250.0
        rpm_ok = 0.0 <= rpm <= 8000.0

        results.append(CheckResult(
            name=f"Frame {i} speed range",
            passed=speed_ok,
            details=f"speed={speed:.2f} kph",
        ))
        results.append(CheckResult(
            name=f"Frame {i} rpm range",
            passed=rpm_ok,
            details=f"rpm={rpm:.2f}",
        ))
    return results


def run_test() -> List[CheckResult]:
    # Synthetic capture for demonstration.
    capture = [
        CANFrame(0, 0x120, bytes([0x13, 0x88, 0x2E, 0xE0, 0, 0, 0, 0])),   # 50.00kph, 3000rpm
        CANFrame(10, 0x120, bytes([0x13, 0x92, 0x2F, 0x10, 0, 0, 0, 0])),  # 50.10kph, 3012rpm
        CANFrame(20, 0x120, bytes([0x13, 0x9C, 0x2F, 0x40, 0, 0, 0, 0])),  # 50.20kph, 3024rpm
        CANFrame(30, 0x120, bytes([0x13, 0xA6, 0x2F, 0x70, 0, 0, 0, 0])),  # 50.30kph, 3036rpm
    ]

    results = [check_cycle_time(capture, max_cycle_ms=20)]
    results.extend(check_signal_ranges(capture))
    return results


def print_report(results: List[CheckResult]) -> None:
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print("=== CAN Signal Validation Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{total} checks passed")


if __name__ == "__main__":
    report = run_test()
    print_report(report)
