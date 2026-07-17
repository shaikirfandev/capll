"""
Data-driven WriteDataByIdentifier (0x2E) tests.

Covers two scenarios, each data-driven from YAML matrices:

1. ``writable_did`` — Write → read-back round-trip verification.
2. ``readonly_did`` — Attempt write, expect NRC 0x31 (requestOutOfRange).

Both scenarios are parametrised automatically via ``pytest_generate_tests``.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]


def _enter_extended_with_security(client: UDSClient, sec_level: int) -> None:
    r = client.change_session(SessionType.EXTENDED)
    assert r.positive, f"Could not enter extended session: {r.nrc_name}"
    if sec_level > 0:
        algo = get_algorithm("xor_placeholder")
        perform_security_access(client, level=sec_level, algorithm=algo)


def test_write_did_round_trip(
    uds_client: UDSClient,
    result_collector: RunResult,
    writable_did: Dict[str, Any],
) -> None:
    """
    0x2E / 0x22 — Write test value → read back → verify value matches.

    Uses ``write_test_value`` from the YAML matrix if present, otherwise
    falls back to ``mock_value``.
    """
    did_id_str   = writable_did["id"]
    did_int      = int(did_id_str, 16)
    did_name     = writable_did.get("name", did_id_str)
    sec_level    = writable_did.get("security_level", 0)
    exp_length   = writable_did.get("length", 1)
    data_type    = writable_did.get("data_type", "hex")

    # Determine write value
    write_val_str = writable_did.get("write_test_value") or writable_did.get("mock_value", "00")
    if data_type == "ascii":
        write_bytes = str(write_val_str).encode("ascii")[:exp_length].ljust(exp_length, b" ")
    else:
        write_bytes = bytes.fromhex(str(write_val_str).replace(" ", ""))

    record = TestRecord(
        test_id=f"did/{did_id_str}-write",
        category="did",
        service_id="0x2E",
        did_id=did_id_str,
        session="extended",
    )
    try:
        _enter_extended_with_security(uds_client, sec_level)

        write_resp = uds_client.write_did(did_int, write_bytes)
        record.actual_value = write_resp.data.hex().upper() if write_resp.positive else None
        record.actual_nrc   = f"0x{write_resp.nrc:02X}" if write_resp.nrc else None
        record.elapsed_ms   = write_resp.elapsed_ms

        assert write_resp.positive, (
            f"WriteDID {did_id_str} ({did_name}) returned {write_resp.nrc_name}"
        )

        # Read back and verify
        read_resp = uds_client.read_did(did_int)
        assert read_resp.positive, (
            f"ReadDID {did_id_str} after write returned {read_resp.nrc_name}"
        )
        readback_data = read_resp.data[2:]   # strip DID echo bytes
        assert readback_data == write_bytes, (
            f"DID {did_id_str} read-back mismatch: "
            f"wrote {write_bytes.hex().upper()}, read {readback_data.hex().upper()}"
        )
        record.extra["roundtrip_ok"] = True
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_write_readonly_did_rejected(
    uds_client: UDSClient,
    result_collector: RunResult,
    readonly_did: Dict[str, Any],
) -> None:
    """
    0x2E — Attempt to write any read-only DID; expect NRC 0x31 (requestOutOfRange).
    """
    did_id_str = readonly_did["id"]
    did_int    = int(did_id_str, 16)
    exp_length = readonly_did.get("length", 1)
    dummy_data = bytes(exp_length)

    record = TestRecord(
        test_id=f"did/{did_id_str}-write-rejected",
        category="did",
        service_id="0x2E",
        did_id=did_id_str,
        session="extended",
        extra={"expected_nrc": "0x31"},
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive

        # Try to get security (best effort; even if denied, write should still be rejected)
        try:
            algo = get_algorithm("xor_placeholder")
            perform_security_access(uds_client, level=1, algorithm=algo)
        except Exception:  # noqa: BLE001
            pass

        resp = uds_client.write_did(did_int, dummy_data)
        record.actual_nrc = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms = resp.elapsed_ms

        assert not resp.positive, (
            f"Write to read-only DID {did_id_str} unexpectedly succeeded"
        )
        assert resp.nrc == 0x31, (
            f"Expected NRC 0x31 (requestOutOfRange) for read-only DID {did_id_str}, "
            f"got 0x{resp.nrc:02X} ({resp.nrc_name})"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
