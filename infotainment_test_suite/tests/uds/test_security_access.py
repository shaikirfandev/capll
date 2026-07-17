"""
Security Access (0x27) tests.

Covers seed/key handshake, correct key acceptance, wrong key rejection,
lockout after N attempts, and security-denied in wrong session.

Markers: ``uds``, ``security``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSResponse, UDSClientBase, MockUDSClient,
)
from core.security_access import (
    NullAlgorithm, XorPlaceholderAlgorithm,
    get_algorithm, perform_security_access,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _level(sessions_config: dict) -> int:
    return int(sessions_config.get("security_access", {}).get("level_1", {}).get("request_level", 0x01))


def _algo(sessions_config: dict):
    name = sessions_config.get("security_access", {}).get("level_1", {}).get("algorithm", "xor_placeholder")
    return get_algorithm(name)


# ===========================================================================
@pytest.mark.uds
@pytest.mark.security
@pytest.mark.smoke
def test_request_seed_in_extended_session(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify RequestSeed (0x27 odd sub-fn) returns a non-zero seed in extended session.

    Arrange: ECU in extended diagnostic session.
    Act:     security_access_request_seed(level=0x01).
    Assert:  Positive response; seed bytes are non-zero.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    level = _level(sessions_config)

    resp: UDSResponse = uds_client.security_access_request_seed(level)

    assert resp.positive, f"RequestSeed rejected: NRC={resp.nrc_name}"
    assert resp.service_id == ServiceID.SECURITY_ACCESS
    # Seed starts at byte index 1 (byte 0 = level echo)
    seed = resp.data[1:] if len(resp.data) > 1 else b""
    assert any(b != 0 for b in seed), "ECU returned an all-zero seed — suspicious"


@pytest.mark.uds
@pytest.mark.security
@pytest.mark.smoke
def test_correct_key_grants_access(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify the correct derived key unlocks security access.

    Arrange: ECU in extended session.
    Act:     perform_security_access() with configured algorithm.
    Assert:  Returns True (positive SendKey response).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    granted = perform_security_access(uds_client, _level(sessions_config), _algo(sessions_config))
    assert granted, "Security access should be granted with correct key"


@pytest.mark.uds
@pytest.mark.security
@pytest.mark.negative
@pytest.mark.regression
def test_wrong_key_returns_nrc_invalid_key(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify an incorrect key returns NRC 0x35 (InvalidKey).

    Arrange: ECU in extended session; stub SendKey to return NRC 0x35.
    Act:     Send a deliberately wrong key.
    Assert:  Response is negative with NRC InvalidKey.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    level = _level(sessions_config)

    # Request seed first
    seed_resp = uds_client.security_access_request_seed(level)
    assert seed_resp.positive, "RequestSeed must succeed before SendKey"

    # Stub the SendKey response to return NRC 0x35
    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.SECURITY_ACCESS, NRC.INVALID_KEY)

    wrong_key = bytes([0x00, 0x00, 0x00, 0x00])
    key_resp = uds_client.security_access_send_key(level, wrong_key)

    assert not key_resp.positive, "Wrong key should produce negative response"
    assert key_resp.nrc == NRC.INVALID_KEY, (
        f"Expected NRC 0x35 (InvalidKey) but got {key_resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.security
@pytest.mark.negative
@pytest.mark.regression
def test_seed_request_in_default_session_denied(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify RequestSeed in default session returns NRC 0x7F (service not supported in session).

    Arrange: ECU in default session; stub to return NRC 0x7F.
    Act:     security_access_request_seed() without entering extended session.
    Assert:  Negative response with NRC serviceNotSupportedInActiveSession.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    level = _level(sessions_config)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(
            ServiceID.SECURITY_ACCESS,
            NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION,
        )

    resp = uds_client.security_access_request_seed(level)

    assert not resp.positive, "RequestSeed should be denied in default session"
    assert resp.nrc in (
        NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION,
        NRC.CONDITIONS_NOT_CORRECT,
    ), f"Expected NRC 0x7F or 0x22 but got {resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.security
@pytest.mark.negative
@pytest.mark.regression
def test_lockout_after_exceeded_attempts(
    uds_client: UDSClientBase,
    sessions_config: dict,
) -> None:
    """
    Verify the ECU returns NRC 0x36 (ExceededNumberOfAttempts) after max failed keys.

    Arrange: ECU in extended session; stub third SendKey to return NRC 0x36.
    Act:     Send wrong key until lockout.
    Assert:  Final response carries NRC 0x36.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    level       = _level(sessions_config)
    max_attempts = int(
        sessions_config.get("security_access", {})
        .get("level_1", {}).get("max_attempts", 3)
    )

    # Request seed once
    seed_resp = uds_client.security_access_request_seed(level)
    assert seed_resp.positive

    wrong_key = bytes([0x00, 0x00, 0x00, 0x00])
    last_resp  = None

    for attempt in range(max_attempts):
        if attempt == max_attempts - 1 and isinstance(uds_client, MockUDSClient):
            uds_client.inject_nrc(ServiceID.SECURITY_ACCESS, NRC.EXCEEDED_NUMBER_OF_ATTEMPTS)
        elif isinstance(uds_client, MockUDSClient):
            uds_client.inject_nrc(ServiceID.SECURITY_ACCESS, NRC.INVALID_KEY)
        last_resp = uds_client.security_access_send_key(level, wrong_key)

    assert last_resp is not None
    assert not last_resp.positive, "Final attempt should be rejected"
    assert last_resp.nrc == NRC.EXCEEDED_NUMBER_OF_ATTEMPTS, (
        f"Expected NRC 0x36 on lockout but got {last_resp.nrc_name}"
    )
