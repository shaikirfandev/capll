"""
CarPlay / Android Auto projection feature tests.

Markers: ``projection``, ``smoke``, ``regression``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import SessionType, RoutineControlType, UDSClientBase
from core.dtc_manager import DTCManager

@pytest.mark.projection
@pytest.mark.smoke
def test_read_carplay_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read CarPlay session state DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("carplay_status"))
    assert resp.positive, f"CarPlay status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04)

@pytest.mark.projection
@pytest.mark.smoke
def test_read_android_auto_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read Android Auto session state DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("android_auto_status"))
    assert resp.positive, f"Android Auto status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04)

@pytest.mark.projection
@pytest.mark.regression
def test_projection_session_start_routine(uds_client: UDSClientBase, routine: Callable[[str], int]) -> None:
    """Start wired projection session routine; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.routine_control(RoutineControlType.START, routine("projection_session_start"))
    assert resp.positive, f"Projection session start failed: NRC={resp.nrc_name}"

@pytest.mark.projection
@pytest.mark.dtc
@pytest.mark.regression
def test_no_carplay_auth_fault_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify CarPlay MFi auth failure DTC absent on clean ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("carplay_auth_failure")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0

@pytest.mark.projection
@pytest.mark.dtc
@pytest.mark.regression
def test_no_android_auto_proxy_fault_dtc(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify Android Auto proxy fault DTC absent on healthy ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("android_auto_proxy_fault")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0
