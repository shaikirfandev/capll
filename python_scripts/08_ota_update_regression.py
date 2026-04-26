#!/usr/bin/env python3
"""Section 8: OTA update regression automation example."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


@dataclass
class UpdatePackage:
    version: str
    payload: bytes
    checksum: int
    post_flash_pass: bool = True


class MockOtaEcu:
    def __init__(self) -> None:
        self.software_version = "1.0.0"
        self.previous_version = self.software_version
        self.active_partition = "A"

    @staticmethod
    def calc_checksum(payload: bytes) -> int:
        return sum(payload) % 65536

    def install_update(
        self,
        pkg: UpdatePackage,
        battery_voltage_v: float,
        soc_percent: int,
        network_ok: bool,
    ) -> Tuple[bool, str]:
        if battery_voltage_v < 12.0:
            return False, "Precheck failed: battery voltage too low"
        if soc_percent < 30:
            return False, "Precheck failed: SOC too low"
        if not network_ok:
            return False, "Precheck failed: network unavailable"

        expected = self.calc_checksum(pkg.payload)
        if expected != pkg.checksum:
            return False, "Checksum mismatch"

        # Flash attempt.
        self.previous_version = self.software_version
        self.software_version = pkg.version
        self.active_partition = "B" if self.active_partition == "A" else "A"

        if not pkg.post_flash_pass:
            # Rollback strategy.
            self.software_version = self.previous_version
            self.active_partition = "A" if self.active_partition == "B" else "B"
            return False, "Post-flash validation failed -> rollback complete"

        return True, "Update successful"


def run_ota_regression_suite() -> List[CheckResult]:
    ecu = MockOtaEcu()
    results: List[CheckResult] = []

    # Case 1: Happy path update.
    payload_ok = b"ECU_IMAGE_V1_1_0"
    pkg_ok = UpdatePackage(
        version="1.1.0",
        payload=payload_ok,
        checksum=MockOtaEcu.calc_checksum(payload_ok),
    )
    ok, msg = ecu.install_update(pkg_ok, battery_voltage_v=12.6, soc_percent=80, network_ok=True)
    results.append(CheckResult(
        name="OTA happy path",
        passed=ok and ecu.software_version == "1.1.0",
        details=msg,
    ))

    # Case 2: Checksum mismatch should be rejected.
    payload_bad = b"ECU_IMAGE_V1_2_0"
    pkg_bad_checksum = UpdatePackage(
        version="1.2.0",
        payload=payload_bad,
        checksum=1234,
    )
    ok, msg = ecu.install_update(pkg_bad_checksum, battery_voltage_v=12.6, soc_percent=80, network_ok=True)
    results.append(CheckResult(
        name="Reject bad checksum",
        passed=(not ok) and ecu.software_version == "1.1.0",
        details=msg,
    ))

    # Case 3: Low battery blocks update.
    ok, msg = ecu.install_update(pkg_ok, battery_voltage_v=11.5, soc_percent=80, network_ok=True)
    results.append(CheckResult(
        name="Block low-voltage update",
        passed=not ok,
        details=msg,
    ))

    # Case 4: Post-flash failure triggers rollback.
    payload_v120 = b"ECU_IMAGE_V1_2_0"
    pkg_post_fail = UpdatePackage(
        version="1.2.0",
        payload=payload_v120,
        checksum=MockOtaEcu.calc_checksum(payload_v120),
        post_flash_pass=False,
    )
    ok, msg = ecu.install_update(pkg_post_fail, battery_voltage_v=12.8, soc_percent=70, network_ok=True)
    results.append(CheckResult(
        name="Rollback on post-flash failure",
        passed=(not ok) and ecu.software_version == "1.1.0",
        details=msg,
    ))

    return results


def main() -> None:
    results = run_ota_regression_suite()
    passed = sum(1 for r in results if r.passed)

    print("=== OTA Regression Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
