#!/usr/bin/env python3
"""Section 5: DTC lifecycle automation example."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DtcStatus:
    code: str
    pending: bool = False
    confirmed: bool = False
    fault_count: int = 0
    heal_counter: int = 0


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class DtcManager:
    def __init__(self) -> None:
        self.records: Dict[str, DtcStatus] = {}

    def _get(self, code: str) -> DtcStatus:
        if code not in self.records:
            self.records[code] = DtcStatus(code=code)
        return self.records[code]

    def report_fault(self, code: str) -> None:
        rec = self._get(code)
        rec.fault_count += 1
        rec.pending = True
        rec.heal_counter = 0
        if rec.fault_count >= 2:
            rec.confirmed = True

    def report_pass_cycle(self, code: str) -> None:
        rec = self._get(code)
        rec.heal_counter += 1

        # Example healing policy
        if rec.heal_counter >= 3:
            rec.pending = False
        if rec.heal_counter >= 5:
            rec.confirmed = False
            rec.fault_count = 0

    def clear_dtc(self, code: str) -> None:
        rec = self._get(code)
        rec.pending = False
        rec.confirmed = False
        rec.fault_count = 0
        rec.heal_counter = 0


def run_dtc_lifecycle_test() -> List[CheckResult]:
    manager = DtcManager()
    code = "P0301"
    results: List[CheckResult] = []

    manager.report_fault(code)  # first detection
    rec = manager.records[code]
    results.append(CheckResult(
        name="After first fault detection -> pending set",
        passed=rec.pending and not rec.confirmed,
        details=f"pending={rec.pending}, confirmed={rec.confirmed}, fault_count={rec.fault_count}",
    ))

    manager.report_fault(code)  # second detection
    rec = manager.records[code]
    results.append(CheckResult(
        name="After second fault detection -> confirmed set",
        passed=rec.pending and rec.confirmed,
        details=f"pending={rec.pending}, confirmed={rec.confirmed}, fault_count={rec.fault_count}",
    ))

    for _ in range(3):
        manager.report_pass_cycle(code)
    rec = manager.records[code]
    results.append(CheckResult(
        name="After 3 pass cycles -> pending cleared",
        passed=not rec.pending and rec.confirmed,
        details=f"pending={rec.pending}, confirmed={rec.confirmed}, heal_counter={rec.heal_counter}",
    ))

    for _ in range(2):
        manager.report_pass_cycle(code)
    rec = manager.records[code]
    results.append(CheckResult(
        name="After 5 pass cycles -> confirmed cleared",
        passed=(not rec.pending) and (not rec.confirmed),
        details=f"pending={rec.pending}, confirmed={rec.confirmed}, heal_counter={rec.heal_counter}",
    ))

    manager.report_fault(code)
    manager.clear_dtc(code)
    rec = manager.records[code]
    results.append(CheckResult(
        name="Manual clear DTC resets status",
        passed=(not rec.pending) and (not rec.confirmed) and rec.fault_count == 0,
        details=f"pending={rec.pending}, confirmed={rec.confirmed}, fault_count={rec.fault_count}",
    ))

    return results


def main() -> None:
    results = run_dtc_lifecycle_test()
    passed = sum(1 for r in results if r.passed)

    print("=== DTC Lifecycle Test Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
