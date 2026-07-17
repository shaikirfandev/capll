"""
ReadDTCInformation (0x19) tests.

Covers reading all DTCs by status mask, confirmed-only, pending-only,
count verification, and snapshot data format.

Markers: ``dtc``, ``smoke``, ``regression``
"""
from __future__ import annotations

import pytest

from core.uds_client import NRC, ServiceID, SessionType, UDSClientBase, MockUDSClient, UDSResponse
from core.dtc_manager import DTCManager, DTCSnapshot


@pytest.mark.dtc
@pytest.mark.smoke
def test_read_all_dtcs_status_mask_ff(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    ReadDTCInformation sub-fn 0x02 with mask 0xFF returns a valid snapshot.

    Arrange: Clear DTCs first.
    Act:     dtc_manager.read_all(0xFF).
    Assert:  Positive inner response; snapshot has zero confirmed DTCs on clean ECU.
    """
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot: DTCSnapshot = dtc_manager.read_all(status_mask=0xFF)

    assert isinstance(snapshot, DTCSnapshot), "Expected DTCSnapshot object"
    assert len(snapshot.confirmed_dtcs) == 0, (
        f"Expected 0 confirmed DTCs after clear; found: "
        f"{[str(d) for d in snapshot.confirmed_dtcs]}"
    )


@pytest.mark.dtc
@pytest.mark.regression
def test_read_confirmed_dtcs_only(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    ReadDTCInformation with mask 0x08 (confirmedDTC bit only).

    Arrange: Clear DTCs.
    Act:     dtc_manager.read_confirmed().
    Assert:  Snapshot records list is empty on clean ECU.
    """
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_confirmed()

    assert len(snapshot.confirmed_dtcs) == 0, (
        f"Expected 0 confirmed DTCs; got: {[str(d) for d in snapshot.confirmed_dtcs]}"
    )


@pytest.mark.dtc
@pytest.mark.regression
def test_read_pending_dtcs_only(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    ReadDTCInformation with mask 0x04 (pendingDTC bit only).

    Arrange: Clear DTCs.
    Act:     dtc_manager.read_pending().
    Assert:  Snapshot records list is empty on clean ECU.
    """
    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_pending()

    assert len(snapshot.pending_dtcs) == 0, (
        f"Expected 0 pending DTCs; got: {[str(d) for d in snapshot.pending_dtcs]}"
    )


@pytest.mark.dtc
@pytest.mark.regression
def test_dtc_snapshot_after_injected_fault(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Inject a synthetic fault DTC into the mock and verify it appears in the snapshot.

    This test validates that the DTC parsing logic correctly decodes records
    from a ReadDTCInformation response.

    Arrange: Stub read_dtc to return one confirmed BT module DTC.
    Act:     dtc_manager.read_all().
    Assert:  Snapshot contains the injected DTC code and it is confirmed.
    """
    BT_MODULE_DTC    = 0xB13001   # from infotainment_dtcs.yaml
    CONFIRMED_STATUS = 0x09       # testFailed(0x01) + confirmedDTC(0x08)

    if isinstance(uds_client, MockUDSClient):
        synthetic = bytes([
            0x02, 0xFF,    # sub-fn + availability mask
            (BT_MODULE_DTC >> 16) & 0xFF,
            (BT_MODULE_DTC >>  8) & 0xFF,
             BT_MODULE_DTC        & 0xFF,
            CONFIRMED_STATUS,
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=synthetic),
        )

    snapshot = dtc_manager.read_all()

    dtc_codes = {r.dtc_code for r in snapshot.records}
    assert BT_MODULE_DTC in dtc_codes, (
        f"Expected BT module DTC 0x{BT_MODULE_DTC:06X} in snapshot; "
        f"found: {[hex(c) for c in dtc_codes]}"
    )
    bt_rec = next(r for r in snapshot.records if r.dtc_code == BT_MODULE_DTC)
    assert bt_rec.is_confirmed, "Injected DTC should be confirmed"


@pytest.mark.dtc
@pytest.mark.regression
def test_dtc_status_bit_decoding(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify the status bit decoder identifies the correct named bits.

    Arrange: Inject a DTC with status byte 0x0F (bits 0-3 all set).
    Act:     Read snapshot; check active_bits() on the record.
    Assert:  "testFailed", "pendingDTC", "confirmedDTC" are all in active_bits.
    """
    DTC_CODE = 0xB12001
    STATUS   = 0x0F   # bits 0,1,2,3

    if isinstance(uds_client, MockUDSClient):
        synthetic = bytes([
            0x02, 0xFF,
            (DTC_CODE >> 16) & 0xFF,
            (DTC_CODE >>  8) & 0xFF,
             DTC_CODE        & 0xFF,
            STATUS,
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            UDSResponse(ServiceID.READ_DTC_INFORMATION, positive=True, data=synthetic),
        )

    snapshot = dtc_manager.read_all()

    matching = [r for r in snapshot.records if r.dtc_code == DTC_CODE]
    assert len(matching) == 1, f"Expected DTC 0x{DTC_CODE:06X} in snapshot"
    bits = matching[0].active_bits()
    assert "testFailed"   in bits
    assert "pendingDTC"   in bits
    assert "confirmedDTC" in bits
