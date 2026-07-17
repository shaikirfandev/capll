"""
Radio / Tuner feature tests.

Markers: ``radio``, ``smoke``, ``regression``
"""
from __future__ import annotations
from typing import Callable
import pytest
from core.uds_client import SessionType, UDSClientBase
from core.security_access import get_algorithm, perform_security_access

def _unlock(uds_client, sessions_config):
    algo  = get_algorithm(sessions_config["security_access"]["level_1"].get("algorithm", "xor_placeholder"))
    level = int(sessions_config["security_access"]["level_1"].get("request_level", 0x01))
    perform_security_access(uds_client, level, algo)

@pytest.mark.radio
@pytest.mark.smoke
def test_read_tuner_band_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read active tuner band DID; verify value in {0x00=AM, 0x01=FM, 0x02=DAB}."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("tuner_band"))
    assert resp.positive, f"Tuner band DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02), f"Unknown tuner band: 0x{resp.data[2]:02X}"

@pytest.mark.radio
@pytest.mark.smoke
def test_read_fm_frequency_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read FM frequency DID; verify at least 4 data bytes."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("fm_frequency"))
    assert resp.positive, f"FM frequency DID failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4, "FM frequency response too short"

@pytest.mark.radio
@pytest.mark.regression
def test_read_dab_service_status_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read DAB service status DID; verify valid enum value."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("dab_service_status"))
    assert resp.positive, f"DAB status DID failed: NRC={resp.nrc_name}"
    if len(resp.data) >= 3:
        assert resp.data[2] in (0x00, 0x01, 0x02)

@pytest.mark.radio
@pytest.mark.regression
def test_read_signal_strength_did(uds_client: UDSClientBase, did: Callable[[str], int]) -> None:
    """Read RF signal strength DID; verify response is positive."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.read_data_by_identifier(did("signal_strength"))
    assert resp.positive, f"Signal strength DID failed: NRC={resp.nrc_name}"

@pytest.mark.radio
@pytest.mark.regression
def test_write_tuner_band_switch_fm(uds_client: UDSClientBase, did: Callable[[str], int], sessions_config: dict) -> None:
    """Switch active tuner band to FM (0x01) via WDBI; verify positive response."""
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    _unlock(uds_client, sessions_config)
    resp = uds_client.write_data_by_identifier(did("tuner_band"), bytes([0x01]))
    assert resp.positive, f"Tuner band WDBI failed: NRC={resp.nrc_name}"
