"""
Tester Present (0x3E) tests.

Covers session keep-alive behaviour, suppress-response flag,
and the frame-logger fixture demonstrating raw transaction capture.

Markers: ``uds``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import NRC, ServiceID, SessionType, UDSClientBase, MockUDSClient


@pytest.mark.uds
@pytest.mark.smoke
def test_tester_present_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify TesterPresent is accepted in default session (suppress=False).

    Arrange: ECU in default session.
    Act:     tester_present(suppress=False).
    Assert:  Positive response; service_id = 0x3E.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.tester_present(suppress=False)

    assert resp.positive, f"TesterPresent rejected: NRC={resp.nrc_name}"
    assert resp.service_id == ServiceID.TESTER_PRESENT


@pytest.mark.uds
@pytest.mark.smoke
def test_tester_present_suppress_response(uds_client: UDSClientBase) -> None:
    """
    Verify TesterPresent with suppress-response (0x80 sub-fn) is accepted.

    Arrange: ECU in extended session.
    Act:     tester_present(suppress=True).
    Assert:  Positive (no-response is indicated by the positive flag in mock mode).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.tester_present(suppress=True)

    assert resp.positive, f"TesterPresent (suppress) rejected: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.regression
def test_multiple_tester_present_keep_session_alive(uds_client: UDSClientBase) -> None:
    """
    Send 5 consecutive TesterPresent messages and verify all succeed.

    This simulates a test harness keeping the session alive across a
    long-running operation.

    Arrange: ECU in extended session.
    Act:     Send 5 × tester_present(suppress=True).
    Assert:  All 5 return positive.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    for i in range(5):
        resp = uds_client.tester_present(suppress=True)
        assert resp.positive, (
            f"TesterPresent #{i+1} failed: NRC={resp.nrc_name}"
        )


@pytest.mark.uds
@pytest.mark.regression
def test_frame_logger_captures_tester_present_transaction(
    uds_client: UDSClientBase,
    frame_logger: list,
) -> None:
    """
    Verify the frame_logger fixture captures the TesterPresent transaction.

    Arrange: Clear transaction log (done by frame_logger fixture).
    Act:     tester_present(suppress=False).
    Assert:  frame_logger contains exactly one entry with service="TesterPresent".
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    # frame_logger was cleared in fixture setup; DSC above added 1 transaction
    prior_count = len(frame_logger)

    resp = uds_client.tester_present(suppress=False)
    assert resp.positive

    # frame_logger is the same object as uds_client.transaction_log
    assert len(frame_logger) > prior_count, "frame_logger should have at least one new entry"
    last = frame_logger[-1]
    assert last["service"] == "TesterPresent", (
        f"Expected last logged service 'TesterPresent' but got '{last['service']}'"
    )
