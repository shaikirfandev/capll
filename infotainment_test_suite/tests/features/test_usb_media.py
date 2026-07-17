"""
USB / Media playback feature tests.

Markers: ``usb_media``, ``smoke``, ``regression``, ``dtc``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import NRC, ServiceID, SessionType, UDSClientBase, MockUDSClient, UDSResponse
from core.dtc_manager import DTCManager

@pytest.mark.usb_media
@pytest.mark.smoke
def test_read_usb_port1_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read USB port 1 status DID; verify value in valid enum range."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("usb_port1_status"))
    assert resp.positive, f"USB port1 DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04), f"Invalid USB1 state: 0x{resp.data[2]:02X}"

@pytest.mark.usb_media
@pytest.mark.smoke
def test_read_usb_port2_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read USB port 2 status DID; verify response is positive."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("usb_port2_status"))
    assert resp.positive, f"USB port2 DID failed: NRC={resp.nrc_name}"

@pytest.mark.usb_media
@pytest.mark.regression
def test_read_media_playback_state_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read media_playback_state DID; verify value in {idle, playing, paused, stopped, error}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("media_playback_state"))
    assert resp.positive, f"Media playback state DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02, 0x03, 0x04)

@pytest.mark.usb_media
@pytest.mark.dtc
@pytest.mark.regression
def test_no_usb_overcurrent_dtc_on_clean_ecu(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify USB port 1 overcurrent DTC is absent after clear."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot  = dtc_manager.read_all()
    code      = dtc_code("usb_port1_overcurrent")
    faults    = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0, f"USB overcurrent DTC 0x{code:06X} unexpectedly set"

@pytest.mark.usb_media
@pytest.mark.regression
def test_usb_hub_fault_dtc_absent(uds_client: UDSClientBase, dtc_manager: DTCManager, dtc_code: Callable[[str], int]) -> None:
    """Verify USB hub not-responding DTC is absent on a healthy ECU."""
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()
    code     = dtc_code("usb_hub_not_responding")
    faults   = [r for r in snapshot.confirmed_dtcs if r.dtc_code == code]
    assert len(faults) == 0, f"USB hub DTC 0x{code:06X} unexpectedly set"
