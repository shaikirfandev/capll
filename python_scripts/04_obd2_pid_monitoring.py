#!/usr/bin/env python3
"""Section 4: OBD-II PID monitoring and validation example."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class MockObdInterface:
    """Simple OBD-II adapter simulation."""

    def __init__(self) -> None:
        self.pid_data: Dict[int, bytes] = {
            0x0C: bytes([0x2E, 0xE0]),  # Engine RPM
            0x0D: bytes([0x50]),        # Vehicle speed
            0x05: bytes([0x78]),        # Coolant temp
            0x11: bytes([0x66]),        # Throttle position
        }

    def request_mode01_pid(self, pid: int) -> bytes:
        payload = self.pid_data.get(pid)
        if payload is None:
            raise ValueError(f"PID 0x{pid:02X} not supported")
        # Positive response format: 0x41 <PID> <payload>
        return bytes([0x41, pid]) + payload


def decode_engine_rpm(response: bytes) -> float:
    a, b = response[2], response[3]
    return ((a * 256) + b) / 4.0


def decode_vehicle_speed(response: bytes) -> int:
    return response[2]


def decode_coolant_temp(response: bytes) -> int:
    return response[2] - 40


def decode_throttle_pct(response: bytes) -> float:
    return (response[2] * 100.0) / 255.0


def run_obd_test() -> List[CheckResult]:
    obd = MockObdInterface()
    results: List[CheckResult] = []

    rpm_resp = obd.request_mode01_pid(0x0C)
    rpm = decode_engine_rpm(rpm_resp)
    results.append(CheckResult(
        name="Engine RPM in valid range",
        passed=600 <= rpm <= 5000,
        details=f"rpm={rpm:.1f}",
    ))

    speed_resp = obd.request_mode01_pid(0x0D)
    speed = decode_vehicle_speed(speed_resp)
    results.append(CheckResult(
        name="Vehicle speed in valid range",
        passed=0 <= speed <= 180,
        details=f"speed={speed} km/h",
    ))

    coolant_resp = obd.request_mode01_pid(0x05)
    coolant = decode_coolant_temp(coolant_resp)
    results.append(CheckResult(
        name="Coolant temp in valid range",
        passed=70 <= coolant <= 110,
        details=f"coolant={coolant} C",
    ))

    throttle_resp = obd.request_mode01_pid(0x11)
    throttle = decode_throttle_pct(throttle_resp)
    results.append(CheckResult(
        name="Throttle position in valid range",
        passed=0.0 <= throttle <= 100.0,
        details=f"throttle={throttle:.1f}%",
    ))

    # Cross-check example: high speed should not coincide with idle rpm in this scenario.
    correlation_ok = not (speed > 80 and rpm < 900)
    results.append(CheckResult(
        name="RPM-speed plausibility check",
        passed=correlation_ok,
        details=f"rpm={rpm:.1f}, speed={speed}",
    ))

    return results


def main() -> None:
    results = run_obd_test()
    passed = sum(1 for r in results if r.passed)

    print("=== OBD-II Monitoring Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
