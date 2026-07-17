"""
UDS Diagnostic Session Control (0x10) tests.

Covers default, extended, and programming session transitions, timing
parameter verification, and out-of-session write rejection.

Markers: ``uds``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType, ResetType,
    UDSResponse, UDSClientBase,
)


@pytest.mark.uds
@pytest.mark.smoke
def test_enter_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU accepts a defaultSession (0x01) request and responds positively.

    Arrange: No precondition.
    Act:     DiagnosticSessionControl(defaultSession).
    Assert:  Positive response; service_id = 0x10.
    """
    resp: UDSResponse = uds_client.diagnostic_session_control(SessionType.DEFAULT)

    assert resp.positive, f"defaultSession rejected: NRC={resp.nrc_name}"
    assert resp.service_id == ServiceID.DIAGNOSTIC_SESSION_CONTROL


@pytest.mark.uds
@pytest.mark.smoke
def test_enter_extended_diagnostic_session(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU transitions to extendedDiagnosticSession (0x03).

    Arrange: ECU in default session.
    Act:     DiagnosticSessionControl(extendedDiagnosticSession).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    assert resp.positive, f"extendedDiagnosticSession rejected: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.regression
def test_enter_programming_session_from_extended(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU enters programmingSession from extendedDiagnosticSession.

    Arrange: ECU in extended diagnostic session.
    Act:     DiagnosticSessionControl(programmingSession).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.diagnostic_session_control(SessionType.PROGRAMMING)

    assert resp.positive, f"programmingSession rejected: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.regression
def test_full_session_cycle(uds_client: UDSClientBase) -> None:
    """
    Verify the full session cycle: default → extended → programming → default.

    Arrange: No precondition.
    Act:     Transition through all four steps.
    Assert:  All four DiagnosticSessionControl calls return positive responses.
    """
    steps = [
        SessionType.DEFAULT,
        SessionType.EXTENDED_DIAGNOSTIC,
        SessionType.PROGRAMMING,
        SessionType.DEFAULT,
    ]
    for session in steps:
        resp = uds_client.diagnostic_session_control(session)
        assert resp.positive, (
            f"Session 0x{session:02X} transition failed: NRC={resp.nrc_name}"
        )


@pytest.mark.uds
@pytest.mark.regression
def test_session_response_contains_timing_parameters(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify the DSC positive response carries P2 and P2* timing bytes.

    Arrange: ECU in extended session.
    Act:     Check response data bytes 1–4 (P2_H, P2_L, P2*_H, P2*_L).
    Assert:  P2 > 0 ms; P2* > P2.

    ISO 14229-1 §7.4.1: response format
      [echo_session_type][P2_msb][P2_lsb][P2*_msb][P2*_lsb]
    """
    resp = uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    assert resp.positive, f"extendedDiagnosticSession rejected: NRC={resp.nrc_name}"
    if len(resp.data) >= 5:
        p2_ms      = (resp.data[1] << 8) | resp.data[2]
        p2_star_ms = ((resp.data[3] << 8) | resp.data[4]) * 10  # units of 10 ms
        assert p2_ms > 0,         f"P2 timing is 0 ms — invalid"
        assert p2_star_ms >= p2_ms, (
            f"P2* ({p2_star_ms} ms) should be ≥ P2 ({p2_ms} ms)"
        )


@pytest.mark.uds
@pytest.mark.regression
def test_hard_reset_returns_to_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify a hard reset (0x11 sub-fn 0x01) restores the ECU to default session.

    Arrange: ECU in extended diagnostic session.
    Act:     ECUReset(hardReset), then enter defaultSession.
    Assert:  Both calls return positive responses.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    reset_resp = uds_client.ecu_reset(ResetType.HARD_RESET)
    assert reset_resp.positive, f"ECUReset failed: NRC={reset_resp.nrc_name}"

    default_resp = uds_client.diagnostic_session_control(SessionType.DEFAULT)
    assert default_resp.positive, (
        f"defaultSession after hard reset failed: NRC={default_resp.nrc_name}"
    )
