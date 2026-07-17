"""
Tests for InputOutputControlByIdentifier (0x2F).

Covers IO-controllable DIDs declared with ``io_controllable: true`` in the matrix.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]

# IO control parameter values (ISO 14229-1 §11.7)
_RETURN_CONTROL_TO_ECU = 0x00
_RESET_TO_DEFAULT      = 0x01
_FREEZE_CURRENT_STATE  = 0x02
_SHORT_TERM_ADJUSTMENT = 0x03


def test_io_control_freeze_and_restore(
    uds_client: UDSClient,
    result_collector: RunResult,
    io_did: Dict[str, Any],
) -> None:
    """
    0x2F — Freeze current IO state, then return control to ECU.
    """
    did_id_str = io_did["id"]
    did_int    = int(did_id_str, 16)
    sec_level  = io_did.get("security_level", 0)

    record = TestRecord(
        test_id=f"io/{did_id_str}-freeze",
        category="did",
        service_id="0x2F",
        did_id=did_id_str,
        session="extended",
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive
        if sec_level > 0:
            algo = get_algorithm("xor_placeholder")
            perform_security_access(uds_client, level=sec_level, algorithm=algo)

        # Freeze current state
        resp = uds_client.io_control(did_int, _FREEZE_CURRENT_STATE)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"IOControl(freeze) for {did_id_str} returned {resp.nrc_name}"
        )

        # Return control to ECU
        restore = uds_client.io_control(did_int, _RETURN_CONTROL_TO_ECU)
        assert restore.positive, (
            f"IOControl(returnToECU) for {did_id_str} returned {restore.nrc_name}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_io_control_reset_to_default(
    uds_client: UDSClient,
    io_did: Dict[str, Any],
) -> None:
    """
    0x2F — Reset IO to default value.
    """
    did_id_str = io_did["id"]
    did_int    = int(did_id_str, 16)
    sec_level  = io_did.get("security_level", 0)

    r = uds_client.change_session(SessionType.EXTENDED)
    assert r.positive
    if sec_level > 0:
        algo = get_algorithm("xor_placeholder")
        perform_security_access(uds_client, level=sec_level, algorithm=algo)

    resp = uds_client.io_control(did_int, _RESET_TO_DEFAULT)
    assert resp.positive, (
        f"IOControl(resetToDefault) for {did_id_str} returned {resp.nrc_name}"
    )
    uds_client.change_session(SessionType.DEFAULT)


def test_io_control_non_controllable_did_rejected(uds_client: UDSClient) -> None:
    """
    0x2F — Attempt to control a non-io-controllable DID (VIN 0xF190) must return NRC 0x31.
    """
    uds_client.change_session(SessionType.EXTENDED)
    resp = uds_client.io_control(0xF190, _FREEZE_CURRENT_STATE)
    assert not resp.positive
    assert resp.nrc == 0x31, (
        f"Expected NRC 0x31 for non-IO DID 0xF190, got 0x{resp.nrc:02X}"
    )
    uds_client.change_session(SessionType.DEFAULT)
