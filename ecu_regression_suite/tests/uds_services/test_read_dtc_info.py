"""
Tests for ReadDTCInformation (0x19).

Validates all documented sub-functions:
- 0x02 reportDTCByStatusMask
- 0x04 reportDTCSnapshotRecordByDTCNumber
- 0x06 reportDTCExtendedDataRecordByDTCNumber
- 0x0A reportSupportedDTC

All sub-functions are tested in extended session.
"""
from __future__ import annotations

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.dtc, pytest.mark.regression]

_DTC_SUB_FNS = [
    pytest.param(0x02, "reportDTCByStatusMask",     id="0x02-by_status_mask"),
    pytest.param(0x04, "reportDTCSnapshotRecord",   id="0x04-snapshot"),
    pytest.param(0x06, "reportDTCExtendedData",     id="0x06-extended_data"),
    pytest.param(0x0A, "reportSupportedDTC",        id="0x0A-supported_dtc"),
]


@pytest.mark.parametrize("sub_fn,sub_name", _DTC_SUB_FNS)
def test_read_dtc_subfunctions(
    uds_client: UDSClient,
    result_collector: RunResult,
    sub_fn: int,
    sub_name: str,
) -> None:
    """
    0x19 — All supported sub-functions must return a positive response.
    """
    record = TestRecord(
        test_id=f"service/0x19-{sub_name}",
        category="service",
        service_id="0x19",
        session="extended",
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive

        if sub_fn == 0x02:
            resp = uds_client.read_dtc_by_status_mask(0xFF)
        elif sub_fn == 0x04:
            resp = uds_client.read_dtc_snapshot(0x000001)  # dummy DTC
        elif sub_fn == 0x06:
            resp = uds_client.read_dtc_extended_data(0x000001)
        elif sub_fn == 0x0A:
            resp = uds_client.read_dtc_supported_dtc(0xFF)
        else:
            pytest.skip(f"Sub-function 0x{sub_fn:02X} not covered")
            return

        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"ReadDTCInformation sub-fn 0x{sub_fn:02X} ({sub_name}) returned {resp.nrc_name}"
        )
        # Response must echo the sub-function byte
        assert resp.data[0] == sub_fn, (
            f"Sub-function echo mismatch: expected 0x{sub_fn:02X}, got 0x{resp.data[0]:02X}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_read_dtc_invalid_subfn_nrc12(uds_client: UDSClient) -> None:
    """
    0x19 — Unsupported sub-function 0x99 must return NRC 0x12.
    """
    from core.uds_client import ServiceID
    uds_client.change_session(SessionType.EXTENDED)
    resp = uds_client._send(bytes([int(ServiceID.READ_DTC_INFORMATION), 0x99]))
    assert not resp.positive
    assert resp.nrc == 0x12, (
        f"Expected NRC 0x12, got 0x{resp.nrc:02X}"
    )
    uds_client.change_session(SessionType.DEFAULT)
