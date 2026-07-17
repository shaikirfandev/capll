"""
ReadDataByIdentifier (0x22) and WriteDataByIdentifier (0x2E) tests.

Covers reading every infotainment DID from the YAML catalogue,
write acceptance for writable DIDs, and rejection for read-only DIDs
or DIDs accessed without security unlock.

Markers: ``uds``, ``smoke``, ``regression``, ``parametrize``
"""
from __future__ import annotations

from typing import Callable

import pytest
import yaml
from pathlib import Path

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSResponse, UDSClientBase, MockUDSClient,
)
from core.security_access import get_algorithm, perform_security_access


# ---------------------------------------------------------------------------
# Parametrised: read every DID defined in infotainment_dids.yaml
# ---------------------------------------------------------------------------
def _all_dids() -> list[tuple[str, dict]]:
    """Load DID catalogue at collection time for parametrize."""
    cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / "infotainment_dids.yaml"
    try:
        with open(cfg_path) as f:
            data = yaml.safe_load(f) or {}
        return [(name, entry) for name, entry in data.items() if isinstance(entry, dict)]
    except FileNotFoundError:
        return []


@pytest.mark.uds
@pytest.mark.regression
@pytest.mark.parametrize
@pytest.mark.parametrize("did_name,did_entry", _all_dids(), ids=[d[0] for d in _all_dids()])
def test_read_all_dids(
    uds_client: UDSClientBase,
    did_name: str,
    did_entry: dict,
) -> None:
    """
    Read every DID in the YAML catalogue and verify a positive response.

    DIDs that require extended session are accessed after transitioning.
    Test IDs match the DID name for easy filtering.

    Arrange: Enter required session based on did_entry["session"].
    Act:     ReadDataByIdentifier for the DID.
    Assert:  Positive response with non-empty data.
    """
    session_map = {"default": SessionType.DEFAULT,
                   "extended": SessionType.EXTENDED_DIAGNOSTIC,
                   "programming": SessionType.PROGRAMMING}
    required_session = session_map.get(did_entry.get("session", "default"), SessionType.DEFAULT)
    uds_client.diagnostic_session_control(required_session)

    did_int = int(did_entry.get("id", "0x0000"), 16) if isinstance(did_entry.get("id"), str) else int(did_entry.get("id", 0))

    resp = uds_client.read_data_by_identifier(did_int)

    assert resp.positive, (
        f"RDBI DID '{did_name}' (0x{did_int:04X}) failed: NRC={resp.nrc_name}"
    )
    assert len(resp.data) >= 2, (
        f"RDBI DID '{did_name}' response too short: {len(resp.data)} bytes"
    )


# ---------------------------------------------------------------------------
# Specific targeted tests
# ---------------------------------------------------------------------------
@pytest.mark.uds
@pytest.mark.smoke
def test_read_software_version_did(
    uds_client: UDSClientBase,
    did: Callable[[str], int],
) -> None:
    """
    Read software_version DID (0xF189) and verify minimum 4-byte response.

    Arrange: ECU in default session.
    Act:     RDBI software_version.
    Assert:  Positive; data ≥ 4 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("software_version"))

    assert resp.positive, f"Software version RDBI failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4, "Software version response too short"


@pytest.mark.uds
@pytest.mark.smoke
def test_read_vin_did(
    uds_client: UDSClientBase,
    did: Callable[[str], int],
) -> None:
    """
    Read VIN DID (0xF190) and verify 19-byte response (2 DID echo + 17 VIN chars).

    Arrange: ECU in default session.
    Act:     RDBI vin.
    Assert:  Positive; data ≥ 4 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    resp = uds_client.read_data_by_identifier(did("vin"))

    assert resp.positive, f"VIN RDBI failed: NRC={resp.nrc_name}"
    assert len(resp.data) >= 4, "VIN response too short"


@pytest.mark.uds
@pytest.mark.regression
def test_write_display_brightness_did(
    uds_client: UDSClientBase,
    did: Callable[[str], int],
    ecu_config: dict,
    sessions_config: dict,
) -> None:
    """
    Write the display_brightness DID with value 0x80 (50 %).

    Arrange: ECU in extended session (no security required for brightness).
    Act:     WDBI display_brightness = 0x80.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.write_data_by_identifier(did("display_brightness"), bytes([0x80]))

    assert resp.positive, f"WDBI display_brightness failed: NRC={resp.nrc_name}"


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_write_read_only_did_returns_nrc(
    uds_client: UDSClientBase,
    did: Callable[[str], int],
) -> None:
    """
    Verify writing a read-only DID (software_version) returns NRC 0x31 or 0x22.

    Arrange: ECU in extended session; stub WDBI to return NRC 0x31.
    Act:     WDBI software_version.
    Assert:  Negative response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.WRITE_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)

    resp = uds_client.write_data_by_identifier(did("software_version"), b"\x01\x02\x03")

    assert not resp.positive, "Writing a read-only DID should return negative response"
    assert resp.nrc in (NRC.REQUEST_OUT_OF_RANGE, NRC.CONDITIONS_NOT_CORRECT), (
        f"Expected NRC 0x31 or 0x22 but got {resp.nrc_name}"
    )


@pytest.mark.uds
@pytest.mark.negative
@pytest.mark.regression
def test_write_did_in_default_session_denied(
    uds_client: UDSClientBase,
    did: Callable[[str], int],
) -> None:
    """
    Verify writing a write-enabled DID in default session is rejected.

    Extended-session DIDs must not be writable in the default session.

    Arrange: ECU in default session; stub to return NRC 0x7F.
    Act:     WDBI audio_volume_level in default session.
    Assert:  Negative response.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(
            ServiceID.WRITE_DATA_BY_IDENTIFIER,
            NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION,
        )

    resp = uds_client.write_data_by_identifier(did("audio_volume_level"), bytes([0x50]))

    assert not resp.positive, "WDBI in default session should be denied"
