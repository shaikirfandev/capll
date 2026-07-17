"""
Display / HMI feature tests.

Markers: ``display``, ``smoke``, ``regression``, ``io_control``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import NRC, ServiceID, SessionType, RoutineControlType, UDSClientBase, MockUDSClient
from core.security_access import get_algorithm, perform_security_access
from core.dtc_manager import DTCManager

def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)

@pytest.mark.display
@pytest.mark.smoke
def test_read_hmi_sleep_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read HMI power/sleep state DID; verify value in {0x00..0x03}."""
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("hmi_sleep_state"))
    assert resp.positive, f"HMI sleep state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.display
@pytest.mark.smoke
def test_read_display_brightness_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read display brightness DID (0x3020); verify 1-byte value 0–255."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("display_brightness"))
    assert resp.positive, f"Display brightness RDBI failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 3

@pytest.mark.display
@pytest.mark.regression
def test_write_display_brightness_50_percent(uds_client: UDSClientBase, did: Callable[[str], int], sessions_config: dict) -> None:
    """Write display_brightness to 0x80 (≈50 %); verify positive WDBI."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.write_data_by_identifier(did("display_brightness"), bytes([0x80]))
    assert resp.positive, f"Display brightness WDBI failed: NRC={resp.nrc_name}"

@pytest.mark.display
@pytest.mark.regression
def test_read_touch_screen_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read touch screen status DID; verify valid state value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("touch_screen_status"))
    assert resp.positive, f"Touch screen status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.display
@pytest.mark.regression
def test_display_self_test_routine(uds_client: UDSClientBase, routine: Callable[[str], int], sessions_config: dict) -> None:
    """Start display self-test routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)
    resp = uds_client.routine_control(RoutineControlType.START, routine("display_self_test"))
    assert resp.positive, f"Display self-test failed: NRC={resp.nrc_name}"

@pytest.mark.display
@pytest.mark.dtc
@pytest.mark.regression
def test_no_display_panel_comm_fault_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify display panel communication DTC absent on healthy HU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("display_panel_comm_failure")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0
