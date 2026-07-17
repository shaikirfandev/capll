"""
Tests for UDS ECUReset (service 0x11).

Validates:
- Hard reset (0x01), soft reset (0x03), key-off/on (0x02) — positive responses.
- Post-reset state: ECU returns to default session.
- Invalid reset type returns NRC 0x12 (subFunctionNotSupported).
"""
from __future__ import annotations

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, ResetType, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]

_RESET_PARAMS = [
    pytest.param(ResetType.HARD_RESET,  "hard_reset",  id="0x01-hard_reset"),
    pytest.param(ResetType.SOFT_RESET,  "soft_reset",  id="0x03-soft_reset"),
    pytest.param(ResetType.KEY_OFF_ON,  "key_off_on",  id="0x02-key_off_on"),
]


@pytest.mark.parametrize("reset_type,reset_name", _RESET_PARAMS)
def test_ecu_reset_positive(
    uds_client: UDSClient,
    result_collector: RunResult,
    reset_type: int,
    reset_name: str,
) -> None:
    """
    0x11 — All supported reset types must return a positive response.
    """
    record = TestRecord(
        test_id=f"service/0x11-{reset_name}",
        category="service",
        service_id="0x11",
        session="default",
        elapsed_ms=0.0,
    )
    try:
        resp = uds_client.ecu_reset(reset_type)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"ECUReset({reset_name}) returned unexpected NRC {resp.nrc_name}"
        )
        assert len(resp.data) >= 1, "Positive response must contain at least reset-type echo"
        assert resp.data[0] == reset_type, (
            f"Reset-type byte mismatch in response: "
            f"expected 0x{reset_type:02X}, got 0x{resp.data[0]:02X}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)


def test_ecu_reset_returns_to_default_session(uds_client: UDSClient) -> None:
    """
    0x11 — After a hard reset, the ECU must be in the default session.
    """
    # Enter extended first
    r = uds_client.change_session(SessionType.EXTENDED)
    assert r.positive

    # Perform hard reset
    r = uds_client.ecu_reset(ResetType.HARD_RESET)
    assert r.positive

    # Verify default session is now active (read ActiveDiagnosticSession DID 0xF186)
    r = uds_client.read_did(0xF186)
    assert r.positive, f"Could not read DID 0xF186 after reset: {r.nrc_name}"
    # Default session = 0x01; data is [DID_high, DID_low, value]
    assert r.data[2] == 0x01, (
        f"Expected default session (0x01) after reset, got 0x{r.data[2]:02X}"
    )


def test_ecu_reset_invalid_type_nrc(uds_client: UDSClient) -> None:
    """
    0x11 — Unsupported reset type 0x05 must return NRC 0x12.
    """
    from core.uds_client import ServiceID
    resp = uds_client._send(bytes([int(ServiceID.ECU_RESET), 0x05]))
    assert not resp.positive, "Expected negative response for unsupported reset type 0x05"
    assert resp.nrc == 0x12, (
        f"Expected NRC 0x12 (subFunctionNotSupported), got 0x{resp.nrc:02X}"
    )
    uds_client.change_session(SessionType.DEFAULT)
