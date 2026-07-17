"""
Tests for UDS DiagnosticSessionControl (service 0x10).

Validates:
- All three sessions (default, extended, programming) can be entered.
- Positive response contains correct session byte, P2, and P2* timing values.
- Session transitions: default→extended, extended→programming, back to default.
- P2 and P2* timing parameters are within expected bounds from sessions_security.yaml.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]

_SESSION_PARAMS = [
    pytest.param(SessionType.DEFAULT,     "default",     id="0x01-default"),
    pytest.param(SessionType.EXTENDED,    "extended",    id="0x03-extended"),
    pytest.param(SessionType.PROGRAMMING, "programming", id="0x02-programming"),
]


@pytest.mark.parametrize("session_type,session_name", _SESSION_PARAMS)
def test_session_control_positive(
    uds_client: UDSClient,
    result_collector: RunResult,
    sessions_config: Dict[str, Any],
    session_type: int,
    session_name: str,
) -> None:
    """
    0x10 — Positive path: every session must be reachable and return correct timing.
    """
    # Always start from default before changing session
    uds_client.change_session(SessionType.DEFAULT)

    resp = uds_client.change_session(session_type)

    record = TestRecord(
        test_id=f"service/0x10-session_{session_name}",
        category="service",
        service_id="0x10",
        session=session_name,
        actual_value=resp.data.hex().upper() if resp.positive else None,
        actual_nrc=f"0x{resp.nrc:02X}" if resp.nrc else None,
        elapsed_ms=resp.elapsed_ms,
    )

    try:
        assert resp.positive, (
            f"DiagnosticSessionControl({session_name}) returned NRC {resp.nrc_name}"
        )

        # Response layout: [session_byte, P2_high, P2_low, P2S_high, P2S_low]
        assert len(resp.data) >= 5, (
            f"Response too short: expected ≥5 bytes, got {len(resp.data)}"
        )
        assert resp.data[0] == session_type, (
            f"Session byte mismatch: expected 0x{session_type:02X}, got 0x{resp.data[0]:02X}"
        )

        # Validate P2 timing from YAML config
        p2_resp_ms    = int.from_bytes(resp.data[1:3], "big")
        p2_star_x10ms = int.from_bytes(resp.data[3:5], "big")
        p2_star_ms    = p2_star_x10ms * 10

        sess_cfg = sessions_config.get("sessions", {}).get(session_name, {})
        expected_p2   = sess_cfg.get("p2_ms", 50)
        expected_p2s  = sess_cfg.get("p2_star_ms", 5000)

        assert p2_resp_ms == expected_p2, (
            f"P2 mismatch: expected {expected_p2} ms, got {p2_resp_ms} ms"
        )
        assert p2_star_ms == expected_p2s, (
            f"P2* mismatch: expected {expected_p2s} ms, got {p2_star_ms} ms"
        )

        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_session_control_timing_within_bounds(
    uds_client: UDSClient,
    sessions_config: Dict[str, Any],
) -> None:
    """
    0x10 — Response latency for DiagnosticSessionControl must be < P2 server timeout.
    """
    uds_client.change_session(SessionType.DEFAULT)
    resp = uds_client.change_session(SessionType.EXTENDED)
    assert resp.positive
    p2_limit = sessions_config.get("sessions", {}).get("extended", {}).get("p2_ms", 150)
    # Add 20% tolerance for transport overhead
    assert resp.elapsed_ms < p2_limit * 1.2, (
        f"Response time {resp.elapsed_ms:.1f}ms exceeded P2 limit "
        f"({p2_limit}ms + 20% tolerance)"
    )
    uds_client.change_session(SessionType.DEFAULT)


def test_session_transition_chain(uds_client: UDSClient) -> None:
    """
    0x10 — Verify session transitions: default → extended → programming → default.
    """
    transitions = [
        (SessionType.DEFAULT,     "default"),
        (SessionType.EXTENDED,    "extended"),
        (SessionType.PROGRAMMING, "programming"),
        (SessionType.DEFAULT,     "default"),
    ]
    for session_type, name in transitions:
        resp = uds_client.change_session(session_type)
        assert resp.positive, (
            f"Could not transition to {name} session: {resp.nrc_name}"
        )


def test_session_control_invalid_session_nrc(uds_client: UDSClient) -> None:
    """
    0x10 — Invalid session sub-function 0xAA must return NRC 0x12 (subFunctionNotSupported).
    """
    from core.uds_client import ServiceID
    # Build a raw payload with unsupported session type
    raw_resp = uds_client._send(bytes([int(ServiceID.DIAGNOSTIC_SESSION_CONTROL), 0xAA]))
    assert not raw_resp.positive, "Expected a negative response for session 0xAA"
    assert raw_resp.nrc == 0x12, (
        f"Expected NRC 0x12 (subFunctionNotSupported), got 0x{raw_resp.nrc:02X}"
    )
    uds_client.change_session(SessionType.DEFAULT)
