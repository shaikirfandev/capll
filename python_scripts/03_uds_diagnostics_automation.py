#!/usr/bin/env python3
"""Section 3: UDS diagnostics automation example (simulation)."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class MockEcuUdsServer:
    def __init__(self) -> None:
        self.session = 0x01  # default session
        self.seed = 0x1234
        self.security_unlocked = False
        self.dids: Dict[int, bytes] = {
            0xF190: b"VIN_DEMO_123456789",
            0xF187: b"SW_1.4.2",
            0xF1A0: b"\x00\x00",
        }

    def _negative_response(self, sid: int, nrc: int) -> bytes:
        return bytes([0x7F, sid, nrc])

    def handle_request(self, request: bytes) -> bytes:
        if not request:
            return self._negative_response(0x00, 0x13)  # incorrect message length

        sid = request[0]

        if sid == 0x10:  # Diagnostic Session Control
            if len(request) != 2:
                return self._negative_response(sid, 0x13)
            requested_session = request[1]
            if requested_session not in (0x01, 0x02, 0x03):
                return self._negative_response(sid, 0x12)
            self.session = requested_session
            return bytes([0x50, requested_session, 0x00, 0x32, 0x00, 0x32])

        if sid == 0x22:  # ReadDataByIdentifier
            if len(request) != 3:
                return self._negative_response(sid, 0x13)
            did = (request[1] << 8) | request[2]
            data = self.dids.get(did)
            if data is None:
                return self._negative_response(sid, 0x31)  # request out of range
            return bytes([0x62, request[1], request[2]]) + data

        if sid == 0x27:  # SecurityAccess
            if len(request) < 2:
                return self._negative_response(sid, 0x13)
            sub = request[1]
            if sub == 0x01:  # request seed
                return bytes([0x67, 0x01, (self.seed >> 8) & 0xFF, self.seed & 0xFF])
            if sub == 0x02:  # send key
                if len(request) != 4:
                    return self._negative_response(sid, 0x13)
                key = (request[2] << 8) | request[3]
                expected_key = self.seed ^ 0xABCD
                if key == expected_key:
                    self.security_unlocked = True
                    return bytes([0x67, 0x02])
                return self._negative_response(sid, 0x35)  # invalid key
            return self._negative_response(sid, 0x12)

        if sid == 0x2E:  # WriteDataByIdentifier
            if len(request) < 4:
                return self._negative_response(sid, 0x13)
            if self.session != 0x03:
                return self._negative_response(sid, 0x7E)  # service not supported in active session
            if not self.security_unlocked:
                return self._negative_response(sid, 0x33)  # security access denied
            did = (request[1] << 8) | request[2]
            payload = request[3:]
            self.dids[did] = payload
            return bytes([0x6E, request[1], request[2]])

        return self._negative_response(sid, 0x11)  # service not supported


def is_positive(response: bytes, request_sid: int) -> bool:
    return len(response) > 0 and response[0] == (request_sid + 0x40)


def run_uds_test_sequence() -> List[CheckResult]:
    ecu = MockEcuUdsServer()
    results: List[CheckResult] = []

    # 1) Enter extended diagnostic session
    resp = ecu.handle_request(bytes([0x10, 0x03]))
    results.append(CheckResult(
        name="Enter extended session",
        passed=is_positive(resp, 0x10),
        details=resp.hex(" "),
    ))

    # 2) Read VIN DID
    resp = ecu.handle_request(bytes([0x22, 0xF1, 0x90]))
    vin_ok = is_positive(resp, 0x22) and b"VIN_" in resp
    results.append(CheckResult(
        name="Read VIN (DID F190)",
        passed=vin_ok,
        details=resp.hex(" "),
    ))

    # 3) Security access: request seed
    seed_resp = ecu.handle_request(bytes([0x27, 0x01]))
    seed_ok = is_positive(seed_resp, 0x27) and len(seed_resp) == 4
    results.append(CheckResult(
        name="Request security seed",
        passed=seed_ok,
        details=seed_resp.hex(" "),
    ))

    # 4) Security access: send key
    seed = (seed_resp[2] << 8) | seed_resp[3]
    key = seed ^ 0xABCD
    key_resp = ecu.handle_request(bytes([0x27, 0x02, (key >> 8) & 0xFF, key & 0xFF]))
    results.append(CheckResult(
        name="Unlock security level",
        passed=is_positive(key_resp, 0x27),
        details=key_resp.hex(" "),
    ))

    # 5) Write calibration DID
    write_resp = ecu.handle_request(bytes([0x2E, 0xF1, 0xA0, 0x12, 0x34]))
    results.append(CheckResult(
        name="Write DID F1A0",
        passed=is_positive(write_resp, 0x2E),
        details=write_resp.hex(" "),
    ))

    # 6) Read calibration DID back
    read_back = ecu.handle_request(bytes([0x22, 0xF1, 0xA0]))
    read_ok = is_positive(read_back, 0x22) and read_back[-2:] == bytes([0x12, 0x34])
    results.append(CheckResult(
        name="Read back DID F1A0",
        passed=read_ok,
        details=read_back.hex(" "),
    ))

    # 7) Negative response check: unknown DID
    neg_resp = ecu.handle_request(bytes([0x22, 0xFA, 0x00]))
    nrc_ok = len(neg_resp) == 3 and neg_resp[0] == 0x7F and neg_resp[2] == 0x31
    results.append(CheckResult(
        name="Negative response for unknown DID",
        passed=nrc_ok,
        details=neg_resp.hex(" "),
    ))

    return results


def print_report(results: List[CheckResult]) -> None:
    print("=== UDS Diagnostics Automation Report ===")
    passed = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        passed += int(result.passed)
        print(f"[{status}] {result.name}: {result.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    print_report(run_uds_test_sequence())
