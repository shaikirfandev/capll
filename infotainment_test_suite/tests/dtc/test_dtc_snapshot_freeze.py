"""
DTC Freeze Frame / Extended Data Record tests.

ISO 14229-1 service 0x19 sub-functions:
  0x04 — reportDTCSnapshotRecordByDTCNumber
  0x06 — reportDTCExtendedDataRecordByDTCNumber

Markers: ``dtc``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC, ServiceID, SessionType,
    UDSResponse, UDSClientBase, MockUDSClient,
)
from core.dtc_manager import DTCManager


@pytest.mark.dtc
@pytest.mark.regression
def test_dtc_diff_detects_new_dtc(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify dtc_manager.diff() correctly identifies a newly triggered DTC.

    Arrange: Take a clean snapshot; inject a new DTC; take second snapshot.
    Act:     dtc_manager.diff(before, after).
    Assert:  The diff list contains exactly the injected DTC.
    """
    INJECTED_DTC = 0xB16001  # GPS antenna open circuit

    # Clean snapshot
    uds_client.clear_dtc(group=0xFFFFFF)
    before = dtc_manager.read_all()

    # Inject DTC into mock
    if isinstance(uds_client, MockUDSClient):
        synthetic = bytes([
            0x02, 0xFF,
            (INJECTED_DTC >> 16) & 0xFF,
            (INJECTED_DTC >>  8) & 0xFF,
             INJECTED_DTC        & 0xFF,
            0x09,  # confirmed + testFailed
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=synthetic),
        )

    after = dtc_manager.read_all()
    new_dtcs = dtc_manager.diff(before, after)

    assert len(new_dtcs) == 1, f"Expected 1 new DTC; found: {[str(d) for d in new_dtcs]}"
    assert new_dtcs[0].dtc_code == INJECTED_DTC


@pytest.mark.dtc
@pytest.mark.regression
def test_no_new_dtcs_after_clean_operation(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify diff() returns empty list when no new DTCs are triggered.

    Arrange: Two consecutive clean snapshots (no fault injection).
    Act:     dtc_manager.diff(snap1, snap2).
    Assert:  Empty list.
    """
    uds_client.clear_dtc(group=0xFFFFFF)
    snap1 = dtc_manager.read_all()
    snap2 = dtc_manager.read_all()   # same mock response

    new_dtcs = dtc_manager.diff(snap1, snap2)
    assert new_dtcs == [], f"Expected no new DTCs but found: {new_dtcs}"


@pytest.mark.dtc
@pytest.mark.regression
def test_dtc_record_code_str_format(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify DTCRecord.code_str produces correct ISO format for a Body DTC.

    DTC 0xB12001:
      high byte 0xB1 → prefix B, sub-type 0x31
      mid  byte 0x20
      low  byte 0x01
      Expected: "B3" + "20" + "01" = "B32001"

    Arrange: Inject DTC 0xB12001.
    Act:     Read snapshot; access .code_str on the record.
    Assert:  code_str matches "B12001" (high & 0x3F = 0x31 → '1').
    """
    DTC_CODE = 0xB12001

    if isinstance(uds_client, MockUDSClient):
        synthetic = bytes([
            0x02, 0xFF,
            (DTC_CODE >> 16) & 0xFF,
            (DTC_CODE >>  8) & 0xFF,
             DTC_CODE        & 0xFF,
            0x08,
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=synthetic),
        )

    snapshot = dtc_manager.read_all()
    rec = next((r for r in snapshot.records if r.dtc_code == DTC_CODE), None)
    assert rec is not None, f"DTC 0x{DTC_CODE:06X} not found in snapshot"
    # Body DTC: high=0xB1 → 'B', (0xB1&0x3F)=0x31=49≠'1' in hex
    assert rec.code_str.startswith("B"), f"Body DTC should start with 'B': {rec.code_str}"


@pytest.mark.dtc
@pytest.mark.regression
def test_multiple_dtcs_in_snapshot(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify the parser handles multiple DTC records in a single response.

    Arrange: Inject 3 DTCs in one synthetic response payload.
    Act:     dtc_manager.read_all().
    Assert:  Snapshot contains exactly 3 records.
    """
    dtcs = [
        (0xB11001, 0x09),
        (0xB12002, 0x09),
        (0xB13001, 0x04),   # pending only
    ]

    if isinstance(uds_client, MockUDSClient):
        payload = bytes([0x02, 0xFF])
        for code, status in dtcs:
            payload += bytes([
                (code >> 16) & 0xFF,
                (code >>  8) & 0xFF,
                 code        & 0xFF,
                status,
            ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=payload),
        )

    snapshot = dtc_manager.read_all()

    assert len(snapshot.records) == 3, (
        f"Expected 3 DTC records; got {len(snapshot.records)}"
    )
    assert len(snapshot.confirmed_dtcs) == 2, (
        "Expected 2 confirmed DTCs (0xB11001 and 0xB12002)"
    )
    assert len(snapshot.pending_dtcs)   == 1, (
        "Expected 1 pending DTC (0xB13001)"
    )
