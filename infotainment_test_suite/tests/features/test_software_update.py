"""
OTA / Software Update feature tests.

Markers: ``ota``, ``smoke``, ``regression``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import SessionType, RoutineControlType, UDSClientBase
from core.security_access import get_algorithm, perform_security_access

def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)

@pytest.mark.ota
@pytest.mark.smoke
def test_read_software_version_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read software_version DID; verify non-empty payload."""
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("software_version"))
    assert resp.positive, f"SW version DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4

@pytest.mark.ota
@pytest.mark.smoke
def test_read_boot_software_version_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read bootloader version DID; verify non-empty payload."""
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("boot_software_version"))
    assert resp.positive, f"Boot SW version DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4

@pytest.mark.ota
@pytest.mark.regression
def test_read_ota_update_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read OTA update status DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("ota_update_status"))
    assert resp.positive, f"OTA status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06)

@pytest.mark.ota
@pytest.mark.regression
def test_software_checksum_verify_routine(uds_client: UDSClientBase, routine: Callable[[str], int], sessions_config: dict) -> None:
    """Run software checksum verification routine in programming session."""
    uds_client.diagnostic_session_control(SessionType.PROGRAMMING)
    _unlock(uds_client, sessions_config)
    resp = uds_client.routine_control(RoutineControlType.START, routine("software_checksum_verify"))
    assert resp.positive, f"SW checksum routine failed: NRC={resp.nrc_name}"

@pytest.mark.ota
@pytest.mark.regression
def test_programming_session_accepts_uds_services(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Verify standard DIDs remain readable during programming session."""
    uds_client.diagnostic_session_control(SessionType.PROGRAMMING)
    resp = uds_client.read_data_by_identifier(did("software_version"))
    assert resp.positive, f"SW version RDBI in programming session failed: NRC={resp.nrc_name}"
