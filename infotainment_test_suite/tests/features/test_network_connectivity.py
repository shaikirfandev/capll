"""
Network Connectivity (Wi-Fi / Hotspot) feature tests.

Markers: ``network``, ``smoke``, ``regression``, ``dtc``
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

@pytest.mark.network
@pytest.mark.smoke
def test_read_wifi_module_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read Wi-Fi module status DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("wifi_module_status"))
    assert resp.positive, f"Wi-Fi status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04)

@pytest.mark.network
@pytest.mark.smoke
def test_read_wifi_ssid_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read Wi-Fi SSID DID; verify response is positive and non-empty."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("wifi_ssid"))
    assert resp.positive, f"Wi-Fi SSID DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 2

@pytest.mark.network
@pytest.mark.regression
def test_read_hotspot_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read mobile hotspot enable/disable DID; verify value 0x00 or 0x01."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("hotspot_status"))
    assert resp.positive, f"Hotspot status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01)

@pytest.mark.network
@pytest.mark.regression
def test_connectivity_self_test_routine(uds_client: UDSClientBase, routine: Callable[[str], int]) -> None:
    """Run Wi-Fi RF loop-back self-test routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.routine_control(RoutineControlType.START, routine("connectivity_self_test"))
    assert resp.positive, f"Connectivity self-test failed: NRC={resp.nrc_name}"

@pytest.mark.network
@pytest.mark.dtc
@pytest.mark.regression
def test_no_wifi_module_not_detected_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify Wi-Fi module not-detected DTC absent on healthy ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("wifi_module_not_detected")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0, f"Wi-Fi module DTC 0x{code:06X} unexpectedly set"
