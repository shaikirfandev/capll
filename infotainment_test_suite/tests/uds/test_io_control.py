"""
IO Control by Identifier (0x2F) tests.

Covers forcing display backlight, audio mute, and speaker test tone,
plus the return-control-to-ECU sub-function and security enforcement.

Markers: ``uds``, ``io_control``, ``smoke``, ``regression``
"""
from __future__ import annotations

from typing import Callable

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSResponse, UDSClientBase, MockUDSClient,
)
from core.security_access import get_algorithm, perform_security_access


def _int(s: object) -> int:
    if isinstance(s, int):
        return s
    return int(str(s).replace("0x", "").replace("0X", ""), 16)


def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)


@pytest.mark.uds
@pytest.mark.io_control
@pytest.mark.smoke
def test_force_display_backlight_on(
    uds_client: UDSClientBase,
    ecu_config: dict,
    sessions_config: dict,
) -> None:
    """
    Force display backlight to maximum via IOControl.

    Arrange: Extended session + security unlock.
    Act:     IOControlByIdentifier(display_backlight DID, shortTermAdjustment → 0xFF).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)

    io_cfg = ecu_config.get("io_control", {}).get("display_backlight", {})
    did    = _int(io_cfg.get("did", "0x3020"))
    option = bytes.fromhex(str(io_cfg.get("control_on", "0x0300FF")).replace("0x", "").zfill(6))

    resp = uds_client.io_control_by_identifier(did, option)

    assert resp.positive, f"IOControl backlight ON failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.io_control
@pytest.mark.smoke
def test_force_display_backlight_off(
    uds_client: UDSClientBase,
    ecu_config: dict,
    sessions_config: dict,
) -> None:
    """
    Force display backlight OFF and then return control to ECU.

    Arrange: Extended session + security unlock.
    Act:     IOControl → backlight 0x00; then returnControlToECU.
    Assert:  Both calls positive.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)

    io_cfg   = ecu_config.get("io_control", {}).get("display_backlight", {})
    did      = _int(io_cfg.get("did", "0x3020"))
    off_opt  = bytes.fromhex(str(io_cfg.get("control_off", "0x030000")).replace("0x", "").zfill(6))
    ret_opt  = bytes.fromhex(str(io_cfg.get("return_ctrl", "0x0000")).replace("0x", "").zfill(4))

    off_resp = uds_client.io_control_by_identifier(did, off_opt)
    assert off_resp.positive, f"IOControl backlight OFF failed: NRC={off_resp.nrc_name}"

    ret_resp = uds_client.io_control_by_identifier(did, ret_opt)
    assert ret_resp.positive, f"ReturnControlToECU failed: NRC={ret_resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.io_control
@pytest.mark.regression
def test_force_audio_mute(
    uds_client: UDSClientBase,
    ecu_config: dict,
    sessions_config: dict,
) -> None:
    """
    Force audio mute via IOControl and verify positive response.

    Arrange: Extended session + security unlock.
    Act:     IOControl mute → active (0x01).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)

    io_cfg = ecu_config.get("io_control", {}).get("audio_mute", {})
    did    = _int(io_cfg.get("did", "0x3032"))
    option = bytes.fromhex(str(io_cfg.get("control_on", "0x030001")).replace("0x", "").zfill(6))

    resp = uds_client.io_control_by_identifier(did, option)
    assert resp.positive, f"IOControl audio mute failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.io_control
@pytest.mark.regression
def test_speaker_test_tone_start_stop(
    uds_client: UDSClientBase,
    ecu_config: dict,
    sessions_config: dict,
) -> None:
    """
    Start and then stop the speaker test-tone IOControl sequence.

    Arrange: Extended session + security unlock.
    Act:     IOControl test tone ON; IOControl test tone OFF.
    Assert:  Both calls positive.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)

    io_cfg  = ecu_config.get("io_control", {}).get("speaker_test_tone", {})
    did     = _int(io_cfg.get("did", "0x3033"))
    on_opt  = bytes.fromhex(str(io_cfg.get("control_on",  "0x030001")).replace("0x", "").zfill(6))
    off_opt = bytes.fromhex(str(io_cfg.get("control_off", "0x030000")).replace("0x", "").zfill(6))

    on_resp  = uds_client.io_control_by_identifier(did, on_opt)
    assert on_resp.positive, f"Speaker test tone ON failed: NRC={on_resp.nrc_name}"

    off_resp = uds_client.io_control_by_identifier(did, off_opt)
    assert off_resp.positive, f"Speaker test tone OFF failed: NRC={off_resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.io_control
@pytest.mark.negative
@pytest.mark.regression
def test_io_control_without_security_denied(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Verify IOControl without security access returns NRC 0x33.

    Arrange: Extended session; NO security unlock; stub NRC 0x33.
    Act:     IOControl display_backlight ON.
    Assert:  Negative response with NRC securityAccessDenied.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(
            ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER,
            NRC.SECURITY_ACCESS_DENIED,
        )

    io_cfg = ecu_config.get("io_control", {}).get("display_backlight", {})
    did    = _int(io_cfg.get("did", "0x3020"))
    option = bytes([0x03, 0x00, 0xFF])

    resp = uds_client.io_control_by_identifier(did, option)

    assert not resp.positive, "IOControl without security access should be denied"
    assert resp.nrc in (NRC.SECURITY_ACCESS_DENIED, NRC.CONDITIONS_NOT_CORRECT), (
        f"Expected NRC 0x33/0x22, got {resp.nrc_name}"
    )
