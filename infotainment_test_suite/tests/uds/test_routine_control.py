"""
Routine Control (0x31) tests.

Covers start/stop/request-results for infotainment routines,
security requirement enforcement, and result status byte validation.

Markers: ``uds``, ``smoke``, ``regression``
"""
from __future__ import annotations

from typing import Callable

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType, RoutineControlType,
    UDSResponse, UDSClientBase, MockUDSClient,
)
from core.security_access import get_algorithm, perform_security_access


def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config.get("security_access", {}).get("level_1", {}).get("algorithm", "xor_placeholder"))
    level = int(sessions_config.get("security_access", {}).get("level_1", {}).get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)


@pytest.mark.uds
@pytest.mark.smoke
def test_display_self_test_start(
    uds_client: UDSClientBase,
    routine: Callable[[str], int],
    sessions_config: dict,
) -> None:
    """
    Start the display self-test routine and verify positive response.

    Arrange: Extended session + security unlock.
    Act:     RoutineControl(startRoutine, display_self_test).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)

    resp = uds_client.routine_control(
        RoutineControlType.START, routine("display_self_test")
    )

    assert resp.positive, f"display_self_test start failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.regression
def test_display_self_test_request_results(
    uds_client: UDSClientBase,
    routine: Callable[[str], int],
    sessions_config: dict,
) -> None:
    """
    Request the results of the display self-test and verify status byte.

    Arrange: Start routine, then request results.
    Act:     RoutineControl(requestRoutineResults, display_self_test).
    Assert:  Positive response; status byte = 0x00 (pass).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)
    rid = routine("display_self_test")

    uds_client.routine_control(RoutineControlType.START, rid)
    resp = uds_client.routine_control(RoutineControlType.REQUEST_RESULT, rid)

    assert resp.positive, f"display_self_test result request failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 4:
        assert resp.data[3] == 0x00, (
            f"display_self_test status 0x{resp.data[3]:02X} != expected 0x00"
        )


@pytest.mark.uds
@pytest.mark.regression
def test_factory_reset_routine(
    uds_client: UDSClientBase,
    routine: Callable[[str], int],
    sessions_config: dict,
) -> None:
    """
    Execute the factory reset routine in programming session.

    .. warning::
        On real hardware this resets all user settings.
        Run only on a bench ECU.

    Arrange: Programming session + security unlock.
    Act:     RoutineControl(startRoutine, factory_reset).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.PROGRAMMING)
    _unlock(uds_client, sessions_config)

    resp = uds_client.routine_control(
        RoutineControlType.START, routine("factory_reset")
    )

    assert resp.positive, f"factory_reset routine failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.regression
def test_bluetooth_self_test_routine(
    uds_client: UDSClientBase,
    routine: Callable[[str], int],
    sessions_config: dict,
) -> None:
    """
    Run the BT module self-test routine (no security needed per YAML).

    Arrange: Extended session.
    Act:     RoutineControl(startRoutine, bluetooth_self_test).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.routine_control(
        RoutineControlType.START, routine("bluetooth_self_test")
    )
    assert resp.positive, f"bluetooth_self_test failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_routine_without_security_denied(
    uds_client: UDSClientBase,
    routine: Callable[[str], int],
) -> None:
    """
    Verify a security-required routine is rejected without security access.

    Arrange: Extended session; NO security unlock; stub to return NRC 0x33.
    Act:     RoutineControl(startRoutine, display_self_test).
    Assert:  Negative response with NRC securityAccessDenied.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.ROUTINE_CONTROL, NRC.SECURITY_ACCESS_DENIED)

    resp = uds_client.routine_control(
        RoutineControlType.START, routine("display_self_test")
    )

    assert not resp.positive, "Routine should be rejected without security access"
    assert resp.nrc in (NRC.SECURITY_ACCESS_DENIED, NRC.CONDITIONS_NOT_CORRECT), (
        f"Expected NRC 0x33 or 0x22 but got {resp.nrc_name}"
    )
