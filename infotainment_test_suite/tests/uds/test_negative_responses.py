"""
Negative Response Code (NRC) tests.

Verifies the ECU (via mock stubs) returns the correct NRC for each
invalid request scenario defined in ISO 14229-1, Annex A.

Markers: ``uds``, ``negative``, ``regression``
"""
from __future__ import annotations

from typing import Callable

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSResponse, UDSClientBase, MockUDSClient,
)


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_service_not_supported(uds_client: UDSClientBase) -> None:
    """
    NRC 0x11 — serviceNotSupported for an unsupported service.

    Arrange: Stub any call to return NRC 0x11.
    Act:     RDBI with an invalid DID that triggers the stub.
    Assert:  Negative response with NRC 0x11.
    """
    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.READ_DATA_BY_IDENTIFIER, NRC.SERVICE_NOT_SUPPORTED)

    resp = uds_client.read_data_by_identifier(0xFFFF)

    assert not resp.positive
    assert resp.nrc == NRC.SERVICE_NOT_SUPPORTED, (
        f"Expected NRC 0x11, got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_incorrect_message_length(uds_client: UDSClientBase) -> None:
    """
    NRC 0x13 — incorrectMessageLengthOrInvalidFormat.

    Arrange: Stub WDBI to return NRC 0x13 (malformed write).
    Act:     WDBI with 0 data bytes.
    Assert:  Negative response with NRC 0x13.
    """
    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.WRITE_DATA_BY_IDENTIFIER, NRC.INCORRECT_MESSAGE_LENGTH)

    resp = uds_client.write_data_by_identifier(0x3020, b"")

    assert not resp.positive
    assert resp.nrc == NRC.INCORRECT_MESSAGE_LENGTH, (
        f"Expected NRC 0x13, got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_conditions_not_correct(uds_client: UDSClientBase) -> None:
    """
    NRC 0x22 — conditionsNotCorrect (e.g. routine requested in wrong state).

    Arrange: Default session; stub RoutineControl to return NRC 0x22.
    Act:     RC startRoutine in default session.
    Assert:  Negative response with NRC 0x22.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.ROUTINE_CONTROL, NRC.CONDITIONS_NOT_CORRECT)

    resp = uds_client.routine_control(0x01, 0x0301)

    assert not resp.positive
    assert resp.nrc == NRC.CONDITIONS_NOT_CORRECT, (
        f"Expected NRC 0x22, got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_request_out_of_range_invalid_did(
    uds_client: UDSClientBase,
) -> None:
    """
    NRC 0x31 — requestOutOfRange for an unallocated DID.

    Arrange: Stub RDBI for DID 0x0000 to return NRC 0x31.
    Act:     RDBI 0x0000.
    Assert:  Negative response with NRC 0x31.
    """
    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.READ_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)

    resp = uds_client.read_data_by_identifier(0x0000)

    assert not resp.positive
    assert resp.nrc == NRC.REQUEST_OUT_OF_RANGE, (
        f"Expected NRC 0x31, got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_security_access_denied(uds_client: UDSClientBase) -> None:
    """
    NRC 0x33 — securityAccessDenied for a protected routine without unlock.

    Arrange: Extended session; no security access; stub NRC 0x33.
    Act:     RoutineControl startRoutine.
    Assert:  Negative response with NRC 0x33.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.ROUTINE_CONTROL, NRC.SECURITY_ACCESS_DENIED)

    resp = uds_client.routine_control(0x01, 0x0303)

    assert not resp.positive
    assert resp.nrc == NRC.SECURITY_ACCESS_DENIED, (
        f"Expected NRC 0x33, got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_nrc_service_not_supported_in_active_session(uds_client: UDSClientBase) -> None:
    """
    NRC 0x7F — serviceNotSupportedInActiveSession.

    Arrange: Default session; stub SecurityAccess to return NRC 0x7F.
    Act:     RequestSeed in default session.
    Assert:  Negative response with NRC 0x7F.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(
            ServiceID.SECURITY_ACCESS,
            NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION,
        )

    resp = uds_client.security_access_request_seed(0x01)

    assert not resp.positive
    assert resp.nrc == NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION, (
        f"Expected NRC 0x7F, got {resp.nrc_name}"
    )
