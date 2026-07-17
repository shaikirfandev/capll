"""
Navigation / GPS feature tests.

Markers: ``navigation``, ``smoke``, ``regression``, ``dtc``
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

@pytest.mark.navigation
@pytest.mark.smoke
def test_read_gps_fix_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read GPS fix status DID; verify value in {0x00..0x03}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("gps_fix_status"))
    assert resp.positive, f"GPS fix DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03)

@pytest.mark.navigation
@pytest.mark.smoke
def test_read_map_db_version_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read navigation map DB version DID; verify non-empty response."""
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("map_db_version"))
    assert resp.positive, f"Map DB version DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4

@pytest.mark.navigation
@pytest.mark.regression
def test_read_navigation_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read navigation engine state DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("navigation_state"))
    assert resp.positive, f"Navigation state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04)

@pytest.mark.navigation
@pytest.mark.regression
def test_gps_self_test_routine(uds_client: UDSClientBase, routine: Callable[[str], int], sessions_config: dict) -> None:
    """Execute GPS self-test routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.routine_control(RoutineControlType.START, routine("gps_self_test"))
    assert resp.positive, f"GPS self-test routine failed: NRC={resp.nrc_name}"

@pytest.mark.navigation
@pytest.mark.dtc
@pytest.mark.regression
def test_no_gps_antenna_open_circuit_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify GPS antenna open-circuit DTC absent on healthy ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("gps_antenna_open_circuit")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0, f"GPS antenna DTC 0x{code:06X} unexpectedly set"
