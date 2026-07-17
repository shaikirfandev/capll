"""
Tests for UDS CommunicationControl (service 0x28).

Validates:
- Enable/disable Rx and Tx in extended session.
- All supported control types (0x00–0x03) return positive responses.
- CommunicationControl in default session returns NRC 0x7F.
- Invalid control type returns NRC 0x12.
"""
from __future__ import annotations

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]

_CTRL_TYPES = [
    pytest.param(0x00, 0x01, "enable_rx_and_tx",     id="0x00-enable_rx_tx"),
    pytest.param(0x01, 0x01, "enable_rx_disable_tx", id="0x01-enable_rx_disable_tx"),
    pytest.param(0x02, 0x01, "disable_rx_enable_tx", id="0x02-disable_rx_enable_tx"),
    pytest.param(0x03, 0x01, "disable_rx_and_tx",    id="0x03-disable_rx_tx"),
]


@pytest.mark.parametrize("ctrl_type,comm_type,name", _CTRL_TYPES)
def test_communication_control_extended_session(
    uds_client: UDSClient,
    result_collector: RunResult,
    ctrl_type: int,
    comm_type: int,
    name: str,
) -> None:
    """
    0x28 — All control types must be accepted in extended session.
    """
    record = TestRecord(
        test_id=f"service/0x28-{name}",
        category="service",
        service_id="0x28",
        session="extended",
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive

        resp = uds_client.communication_control(ctrl_type, comm_type)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"CommunicationControl(ctrl=0x{ctrl_type:02X}) returned {resp.nrc_name}"
        )

        # Re-enable Rx/Tx after disabling to not disrupt subsequent tests
        if ctrl_type != 0x00:
            uds_client.communication_control(0x00, comm_type)

        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_communication_control_default_session_nrc7f(uds_client: UDSClient) -> None:
    """
    0x28 — Not available in default session → expect NRC 0x7F.
    """
    uds_client.change_session(SessionType.DEFAULT)
    resp = uds_client.communication_control(0x00, 0x01)
    assert not resp.positive
    assert resp.nrc == 0x7F, (
        f"Expected NRC 0x7F in default session, got 0x{resp.nrc:02X} ({resp.nrc_name})"
    )


def test_communication_control_invalid_type_nrc12(uds_client: UDSClient) -> None:
    """
    0x28 — Invalid control type 0x0A must return NRC 0x12.
    """
    uds_client.change_session(SessionType.EXTENDED)
    resp = uds_client.communication_control(0x0A, 0x01)
    assert not resp.positive
    assert resp.nrc == 0x12, (
        f"Expected NRC 0x12, got 0x{resp.nrc:02X} ({resp.nrc_name})"
    )
    uds_client.change_session(SessionType.DEFAULT)
