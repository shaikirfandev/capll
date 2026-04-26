#!/usr/bin/env python3
"""Section 6: HIL test orchestration example with mocked lab instruments."""

from dataclasses import dataclass
from typing import List


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class MockPowerSupply:
    def __init__(self) -> None:
        self.voltage_v = 0.0
        self.enabled = False

    def set_voltage(self, voltage_v: float) -> None:
        self.voltage_v = voltage_v

    def output_on(self) -> None:
        self.enabled = True

    def output_off(self) -> None:
        self.enabled = False


class MockEcuBenchModel:
    def __init__(self) -> None:
        self.boot_time_ms = 820
        self.current_profile_a = [0.8, 3.5, 5.2, 2.1, 1.0]
        self.heartbeat_period_ms = 100
        self.first_heartbeat_ms = 900


class HilOrchestrator:
    def __init__(self) -> None:
        self.psu = MockPowerSupply()
        self.ecu = MockEcuBenchModel()

    def run_startup_sequence(self) -> List[CheckResult]:
        results: List[CheckResult] = []

        self.psu.set_voltage(13.5)
        self.psu.output_on()

        results.append(CheckResult(
            name="Power rail set to nominal",
            passed=13.0 <= self.psu.voltage_v <= 14.5,
            details=f"voltage={self.psu.voltage_v:.2f}V",
        ))

        inrush = max(self.ecu.current_profile_a)
        results.append(CheckResult(
            name="Inrush current below limit",
            passed=inrush <= 8.0,
            details=f"inrush={inrush:.2f}A, limit=8.00A",
        ))

        results.append(CheckResult(
            name="ECU boot time within target",
            passed=self.ecu.boot_time_ms <= 1500,
            details=f"boot_time={self.ecu.boot_time_ms}ms, limit=1500ms",
        ))

        results.append(CheckResult(
            name="Heartbeat starts on time",
            passed=self.ecu.first_heartbeat_ms <= 1000,
            details=f"first_heartbeat={self.ecu.first_heartbeat_ms}ms, limit=1000ms",
        ))

        results.append(CheckResult(
            name="Heartbeat period check",
            passed=80 <= self.ecu.heartbeat_period_ms <= 120,
            details=f"period={self.ecu.heartbeat_period_ms}ms",
        ))

        self.psu.output_off()
        return results


def main() -> None:
    orchestrator = HilOrchestrator()
    results = orchestrator.run_startup_sequence()

    print("=== HIL Startup Orchestration Report ===")
    passed = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        passed += int(r.passed)
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
