"""
Voice Recognition feature tests.

Markers: ``voice``, ``smoke``, ``regression``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import SessionType, RoutineControlType, UDSClientBase
from core.dtc_manager import DTCManager

@pytest.mark.voice
@pytest.mark.smoke
def test_read_voice_recognition_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read VR engine state DID; verify value in {0x00..0x03}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("voice_recognition_state"))
    assert resp.positive, f"VR state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.voice
@pytest.mark.smoke
def test_read_microphone_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read microphone hardware status DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("microphone_status"))
    assert resp.positive, f"Microphone status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.voice
@pytest.mark.regression
def test_voice_recognition_self_test_routine(uds_client: UDSClientBase, routine: Callable[[str], int]) -> None:
    """Run VR self-test routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.routine_control(RoutineControlType.START, routine("voice_recognition_self_test"))
    assert resp.positive, f"VR self-test failed: NRC={resp.nrc_name}"

@pytest.mark.voice
@pytest.mark.dtc
@pytest.mark.regression
def test_no_microphone_open_circuit_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify microphone open-circuit DTC absent after clear."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("microphone_open_circuit")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0, f"Mic open-circuit DTC 0x{code:06X} unexpectedly set"
