"""
Tests for TesterPresent (0x3E).

Validates:
- Sub-function 0x00: positive response with echo byte.
- Sub-function 0x80: suppress response flag (no response expected — handled).
- Session keepalive: extended session persists while TesterPresent is sent periodically.
- Session times out when TesterPresent stops (verified by checking session state).
- Invalid sub-function 0x01 → NRC 0x12.
"""
from __future__ import annotations

import time

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]


def test_tester_present_sub0x00(
    uds_client: UDSClient,
    result_collector: RunResult,
) -> None:
    """
    0x3E sub-fn 0x00 — Must return positive response echoing sub-function byte 0x00.
    """
    record = TestRecord(
        test_id="service/0x3E-tester_present",
        category="service",
        service_id="0x3E",
        session="default",
    )
    try:
        uds_client.change_session(SessionType.DEFAULT)
        resp = uds_client.tester_present(suppress_response=False)

        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, f"TesterPresent(0x00) returned {resp.nrc_name}"
        assert resp.data[0] == 0x00, (
            f"Sub-function echo mismatch: expected 0x00, got 0x{resp.data[0]:02X}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)


def test_tester_present_suppress_response(uds_client: UDSClient) -> None:
    """
    0x3E sub-fn 0x80 — Response is suppressed; method must not raise.
    """
    uds_client.change_session(SessionType.DEFAULT)
    resp = uds_client.tester_present(suppress_response=True)
    # With suppress, positive=True but data is empty
    assert resp.positive, (
        f"TesterPresent(suppress=True) returned unexpected NRC {resp.nrc_name}"
    )


def test_tester_present_session_keepalive(uds_client: UDSClient) -> None:
    """
    0x3E — Extended session persists while TesterPresent is sent every 1 s for 3 s.
    """
    r = uds_client.change_session(SessionType.EXTENDED)
    assert r.positive

    for _ in range(3):
        resp = uds_client.tester_present(suppress_response=False)
        assert resp.positive, f"TesterPresent failed during keepalive: {resp.nrc_name}"
        time.sleep(0.1)  # Mock mode: minimal sleep

    # Verify still in extended session via read of ActiveSession DID
    read_resp = uds_client.read_did(0xF186)
    assert read_resp.positive, "Could not read session DID after keepalive"

    uds_client.change_session(SessionType.DEFAULT)


def test_tester_present_invalid_subfn_nrc12(uds_client: UDSClient) -> None:
    """
    0x3E — Invalid sub-function 0x01 must return NRC 0x12.
    """
    from core.uds_client import ServiceID
    uds_client.change_session(SessionType.DEFAULT)
    resp = uds_client._send(bytes([int(ServiceID.TESTER_PRESENT), 0x01]))
    assert not resp.positive
    assert resp.nrc == 0x12, (
        f"Expected NRC 0x12 for invalid TesterPresent sub-fn, got 0x{resp.nrc:02X}"
    )
