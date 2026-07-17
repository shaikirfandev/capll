"""
Tests for ClearDiagnosticInformation (0x14).

Validates:
- 0x14 succeeds in extended session.
- 0x14 is rejected in default session (NRC 0x7F).
- Group-of-DTC parameter 0xFFFFFF (all DTCs) is accepted.
"""
from __future__ import annotations

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.dtc, pytest.mark.regression]


def test_clear_dtc_extended_session(
    uds_client: UDSClient,
    result_collector: RunResult,
) -> None:
    """
    0x14 — ClearDTC must succeed in extended session with group 0xFFFFFF.
    """
    record = TestRecord(
        test_id="service/0x14-clear_dtc",
        category="service",
        service_id="0x14",
        session="extended",
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive

        resp = uds_client.clear_dtc(0xFF_FF_FF)
        record.actual_value = resp.data.hex().upper() if resp.positive else ""
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"ClearDTC in extended session returned unexpected NRC {resp.nrc_name}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_clear_dtc_default_session_rejected(uds_client: UDSClient) -> None:
    """
    0x14 — ClearDTC must return NRC 0x7F (serviceNotSupportedInActiveSession) in default session.
    """
    r = uds_client.change_session(SessionType.DEFAULT)
    assert r.positive

    resp = uds_client.clear_dtc(0xFF_FF_FF)
    assert not resp.positive, "ClearDTC unexpectedly succeeded in default session"
    assert resp.nrc == 0x7F, (
        f"Expected NRC 0x7F, got 0x{resp.nrc:02X} ({resp.nrc_name})"
    )
