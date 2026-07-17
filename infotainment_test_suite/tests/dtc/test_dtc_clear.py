"""
ClearDiagnosticInformation (0x14) tests.

Covers clearing all DTC groups, per-group clear, and verifying the
DTC list is empty after a successful clear.

Markers: ``dtc``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSClientBase, MockUDSClient,
)
from core.dtc_manager import DTCManager


@pytest.mark.dtc
@pytest.mark.smoke
def test_clear_all_dtcs(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify ClearDiagnosticInformation(0xFFFFFF) succeeds and DTC list is empty.

    Arrange: ECU in extended session.
    Act:     clear_dtc(group=0xFFFFFF); read_all().
    Assert:  ClearDTC positive; 0 confirmed DTCs after clear.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    clear_resp = uds_client.clear_dtc(group=0xFFFFFF)

    assert clear_resp.positive, f"ClearDTC failed: NRC={clear_resp.nrc_name}"

    snapshot = dtc_manager.read_all()
    assert len(snapshot.confirmed_dtcs) == 0, (
        f"Expected 0 confirmed DTCs after clear; found: "
        f"{[str(d) for d in snapshot.confirmed_dtcs]}"
    )


@pytest.mark.dtc
@pytest.mark.regression
def test_clear_body_system_dtc_group(
    uds_client: UDSClientBase,
) -> None:
    """
    Clear only the Body system DTC group (0xB00000–0xBFFFFF range → group 0xFF00).

    ISO 14229 allows OEM-specific group IDs.  This test uses the common
    "Body/B-code" group if defined, otherwise falls back to 0xFFFFFF.

    Arrange: Extended session.
    Act:     clear_dtc(group=0xFF00).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    resp = uds_client.clear_dtc(group=0xFF00)

    assert resp.positive, f"ClearDTC body-group failed: NRC={resp.nrc_name}"


@pytest.mark.dtc
@pytest.mark.regression
def test_clear_dtc_and_re_read_is_empty(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Full round-trip: inject DTC → verify present → clear → verify absent.

    Arrange: Inject a synthetic confirmed DTC; read to confirm presence.
    Act:     ClearDTC; re-read.
    Assert:  DTC is absent after clear.
    """
    from core.uds_client import UDSResponse

    FAKE_DTC     = 0xB15003
    CONFIRMED_ST = 0x09

    # Inject the DTC
    if isinstance(uds_client, MockUDSClient):
        synthetic = bytes([
            0x02, 0xFF,
            (FAKE_DTC >> 16) & 0xFF,
            (FAKE_DTC >>  8) & 0xFF,
             FAKE_DTC        & 0xFF,
            CONFIRMED_ST,
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=synthetic),
        )

    snap_before = dtc_manager.read_all()
    assert FAKE_DTC in snap_before.codes(), "Injected DTC should appear in first snapshot"

    # Clear and verify
    uds_client.clear_dtc(group=0xFFFFFF)
    snap_after = dtc_manager.read_all()

    assert FAKE_DTC not in snap_after.codes(), (
        f"DTC 0x{FAKE_DTC:06X} should be absent after clear"
    )


@pytest.mark.dtc
@pytest.mark.negative
@pytest.mark.regression
def test_clear_dtc_without_extended_session_denied(
    uds_client: UDSClientBase,
) -> None:
    """
    Verify ClearDTC in default session returns NRC conditionsNotCorrect.

    Arrange: Default session; stub NRC 0x22.
    Act:     clear_dtc() in default session.
    Assert:  Negative response with NRC 0x22.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)

    if isinstance(uds_client, MockUDSClient):
        uds_client.inject_nrc(ServiceID.CLEAR_DTC_INFORMATION, NRC.CONDITIONS_NOT_CORRECT)

    resp = uds_client.clear_dtc(group=0xFFFFFF)

    assert not resp.positive, "ClearDTC in default session should be denied"
    assert resp.nrc in (NRC.CONDITIONS_NOT_CORRECT, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION), (
        f"Expected NRC 0x22/0x7F, got {resp.nrc_name}"
    )
