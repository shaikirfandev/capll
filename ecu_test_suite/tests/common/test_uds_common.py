"""
Common UDS service tests — reusable across all ECU domains.

These tests verify the generic UDS stack behaviour that every domain ECU
must support (ISO 14229-1 mandatory services).  They are collected alongside
each domain suite when the CLI invokes pytest on both directories.

Markers:  ``uds``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC,
    ServiceID,
    SessionType,
    ResetType,
    CommControlType,
    UDSResponse,
    UDSClientBase,
    MockUDSClient,
)


# ===========================================================================
# Test: TesterPresent in default session
# ===========================================================================
@pytest.mark.uds
@pytest.mark.smoke
def test_tester_present_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify TesterPresent (0x3E) is accepted in the default session.

    Arrange: ECU is in default diagnostic session.
    Act:     Send TesterPresent with suppress_response=False.
    Assert:  ECU returns a positive response (0x7E 0x00).
    """
    # Arrange — ensure we are in the default session
    uds_client.diagnostic_session_control(SessionType.DEFAULT)

    # Act
    response: UDSResponse = uds_client.tester_present(suppress_response=False)

    # Assert
    assert response.positive, (
        f"TesterPresent should succeed in default session; got NRC={response.nrc_name}"
    )
    assert response.service_id == ServiceID.TESTER_PRESENT


# ===========================================================================
# Test: Full session transition cycle
# ===========================================================================
@pytest.mark.uds
@pytest.mark.regression
def test_session_transitions_full_cycle(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU correctly transitions through all three sessions.

    Arrange: Start in default session.
    Act:     Transition default → extended → programming → default.
    Assert:  Each DiagnosticSessionControl returns a positive response.
    """
    # Default → Extended
    resp = uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    assert resp.positive, f"Default→Extended failed: NRC={resp.nrc_name}"

    # Extended → Programming
    resp = uds_client.diagnostic_session_control(SessionType.PROGRAMMING)
    assert resp.positive, f"Extended→Programming failed: NRC={resp.nrc_name}"

    # Programming → Default
    resp = uds_client.diagnostic_session_control(SessionType.DEFAULT)
    assert resp.positive, f"Programming→Default failed: NRC={resp.nrc_name}"


# ===========================================================================
# Test: Hard reset returns ECU to default session
# ===========================================================================
@pytest.mark.uds
@pytest.mark.smoke
def test_hard_reset_returns_to_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify that after a hard reset the ECU accepts default session requests.

    Arrange: ECU is in extended diagnostic session.
    Act:     Issue ECUReset (hard reset), then request default session.
    Assert:  Both responses are positive.
    """
    # Arrange — put ECU into extended session
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    # Act — hard reset
    reset_resp = uds_client.ecu_reset(ResetType.HARD_RESET)
    assert reset_resp.positive, f"ECUReset failed: NRC={reset_resp.nrc_name}"

    # Act — re-enter default session (simulates ECU boot completing)
    default_resp = uds_client.diagnostic_session_control(SessionType.DEFAULT)
    assert default_resp.positive, (
        f"Default session after reset failed: NRC={default_resp.nrc_name}"
    )


# ===========================================================================
# Test: Negative response for out-of-range DID
# ===========================================================================
@pytest.mark.uds
@pytest.mark.regression
def test_negative_response_for_invalid_did(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU returns NRC 0x31 (RequestOutOfRange) for an undefined DID.

    Arrange: Stub the mock client to return NRC 0x31 for DID 0x0000.
    Act:     Read an unallocated DID.
    Assert:  Response is negative with NRC requestOutOfRange.

    .. note::
        On real hardware this test will pass only if 0x0000 is genuinely
        not allocated in the ECU's DID table.  Adjust the DID as needed.
    """
    invalid_did = 0x0000

    # Arrange — pre-load a negative response stub (mock mode)
    if isinstance(uds_client, MockUDSClient):
        uds_client.stub_response(
            ServiceID.READ_DATA_BY_IDENTIFIER,
            UDSResponse(
                service_id = ServiceID.READ_DATA_BY_IDENTIFIER,
                positive   = False,
                nrc        = NRC.REQUEST_OUT_OF_RANGE,
            ),
        )

    # Act
    response = uds_client.read_data_by_identifier(invalid_did)

    # Assert
    assert not response.positive, "Expected negative response for invalid DID"
    assert response.nrc == NRC.REQUEST_OUT_OF_RANGE, (
        f"Expected NRC 0x31 (requestOutOfRange) but got {response.nrc_name}"
    )


# ===========================================================================
# Test: CommunicationControl — disable then re-enable normal messages
# ===========================================================================
@pytest.mark.uds
@pytest.mark.regression
def test_communication_control_disable_and_restore(uds_client: UDSClientBase) -> None:
    """
    Verify CommunicationControl (0x28) disable/enable round-trip.

    Arrange: ECU is in extended diagnostic session.
    Act:     Disable Tx messages, then re-enable all.
    Assert:  Both CommunicationControl requests return positive responses.
    """
    # Arrange
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    # Act — disable TX
    disable_resp = uds_client.communication_control(
        CommControlType.DISABLE_RX_ENABLE_TX,
        comm_type=0x01,   # normalCommunicationMessages
    )
    assert disable_resp.positive, (
        f"CommunicationControl disable failed: NRC={disable_resp.nrc_name}"
    )

    # Act — re-enable all
    enable_resp = uds_client.communication_control(
        CommControlType.ENABLE_RX_AND_TX,
        comm_type=0x01,
    )
    assert enable_resp.positive, (
        f"CommunicationControl re-enable failed: NRC={enable_resp.nrc_name}"
    )


# ===========================================================================
# Test: Clear DTC returns positive when no faults present
# ===========================================================================
@pytest.mark.uds
@pytest.mark.dtc
@pytest.mark.smoke
def test_clear_dtc_with_no_active_faults(
    uds_client: UDSClientBase,
    dtc_manager,
) -> None:
    """
    Verify ClearDiagnosticInformation (0x14) succeeds on a clean ECU.

    Arrange: ECU DTC memory is clear.
    Act:     Issue clear DTC for all groups (0xFFFFFF).
    Assert:  Positive response and subsequent read returns no DTCs.
    """
    # Act — clear
    clear_resp = uds_client.clear_dtc(group=0xFFFFFF)
    assert clear_resp.positive, (
        f"ClearDTC failed on clean ECU: NRC={clear_resp.nrc_name}"
    )

    # Assert — re-read confirms empty
    snapshot = dtc_manager.read_all()
    assert len(snapshot.confirmed_dtcs) == 0, (
        f"Expected no confirmed DTCs after clear; found: "
        f"{[str(d) for d in snapshot.confirmed_dtcs]}"
    )


# ===========================================================================
# Test: Soft reset is accepted in extended session
# ===========================================================================
@pytest.mark.uds
@pytest.mark.regression
def test_soft_reset_in_extended_session(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU accepts a soft reset while in extended diagnostic session.

    Arrange: Transition to extended diagnostic session.
    Act:     Issue ECUReset with type 0x03 (softReset).
    Assert:  Positive response received.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.ecu_reset(ResetType.SOFT_RESET)
    assert resp.positive, f"Soft reset in extended session failed: NRC={resp.nrc_name}"
