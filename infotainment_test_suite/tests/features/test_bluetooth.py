"""
Bluetooth feature tests.

Markers: ``bluetooth``, ``smoke``, ``regression``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import NRC, ServiceID, SessionType, UDSClientBase, MockUDSClient, UDSResponse
from core.security_access import get_algorithm, perform_security_access
from core.dtc_manager import DTCManager

def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)

@pytest.mark.bluetooth
@pytest.mark.smoke
def test_read_bluetooth_module_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read bluetooth_module_status DID in extended session; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("bluetooth_module_status"))
    assert resp.positive, f"BT status DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 2

@pytest.mark.bluetooth
@pytest.mark.smoke
def test_read_bluetooth_pairing_count_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read bluetooth_pairing_count DID and verify value is in 0–8 range."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("bluetooth_pairing_count"))
    assert resp.positive, f"BT pairing count DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        count = resp.data[2]
        assert count <= 8, f"BT pairing count {count} > 8 (spec maximum)"

@pytest.mark.bluetooth
@pytest.mark.regression
def test_read_bluetooth_a2dp_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read A2DP streaming state DID; verify value in {0x00, 0x01, 0x02}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("bluetooth_a2dp_state"))
    assert resp.positive, f"A2DP state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02), f"Invalid A2DP state: 0x{resp.data[2]:02X}"

@pytest.mark.bluetooth
@pytest.mark.regression
def test_read_bluetooth_hfp_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read HFP call state DID; verify value in {0x00..0x03}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("bluetooth_hfp_state"))
    assert resp.positive, f"HFP state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03), f"Invalid HFP state: 0x{resp.data[2]:02X}"

@pytest.mark.bluetooth
@pytest.mark.dtc
@pytest.mark.regression
def test_no_bluetooth_module_dtc_on_healthy_ecu(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify BT module not-detected DTC is absent after DTC clear."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    bt_code  = dtc_code("bluetooth_module_not_detected")
    bt_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == bt_code]
    assert len(bt_faults) == 0, f"BT module DTC 0x{bt_code:06X} unexpectedly confirmed"
