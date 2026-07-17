"""
Audio Amplifier feature tests.

Markers: ``audio``, ``smoke``, ``regression``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import SessionType, RoutineControlType, UDSClientBase
from core.security_access import get_algorithm, perform_security_access
from core.dtc_manager import DTCManager

def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)

@pytest.mark.audio
@pytest.mark.smoke
def test_read_audio_amp_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read audio amplifier status DID; verify valid enum state."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("audio_amp_status"))
    assert resp.positive, f"Audio amp status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.audio
@pytest.mark.smoke
def test_read_audio_volume_level_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read audio volume level DID; verify value 0–100."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("audio_volume_level"))
    assert resp.positive, f"Volume DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] <= 100, f"Volume level {resp.data[2]} > 100"

@pytest.mark.audio
@pytest.mark.regression
def test_write_audio_volume_level(uds_client: UDSClientBase, did: Callable[[str], int], sessions_config: dict) -> None:
    """Write volume to 0x32 (50 %); verify positive WDBI."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.write_data_by_identifier(did("audio_volume_level"), bytes([0x32]))
    assert resp.positive, f"Volume WDBI failed: NRC={resp.nrc_name}"

@pytest.mark.audio
@pytest.mark.regression
def test_read_mute_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read mute state DID; verify value 0x00 or 0x01."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("mute_state"))
    assert resp.positive, f"Mute state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01)

@pytest.mark.audio
@pytest.mark.regression
def test_audio_self_test_routine(uds_client: UDSClientBase, routine: Callable[[str], int], sessions_config: dict) -> None:
    """Start audio self-test routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)
    resp = uds_client.routine_control(RoutineControlType.START, routine("audio_self_test"))
    assert resp.positive, f"Audio self-test failed: NRC={resp.nrc_name}"

@pytest.mark.audio
@pytest.mark.dtc
@pytest.mark.regression
def test_no_audio_amp_over_temp_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify audio amp over-temperature DTC absent on healthy ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("audio_amp_over_temperature")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0
