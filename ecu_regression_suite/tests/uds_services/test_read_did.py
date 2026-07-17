"""
Data-driven ReadDataByIdentifier (0x22) tests.

One test per DID entry in ``config/<ecu>/did_matrix.yaml`` — generated
automatically via ``pytest_generate_tests`` in conftest.py.

Each test:
1. Enters the required session.
2. Performs security access if ``security_level > 0``.
3. Reads the DID.
4. Validates: positive response, correct data length, correct data type/format,
   value within range (where declared in YAML).
5. Records the result in ``result_collector`` for baseline diffing.
"""
from __future__ import annotations

import re
from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]


def _session_type(session_name: str) -> int:
    return {"default": SessionType.DEFAULT, "programming": SessionType.PROGRAMMING}.get(
        session_name, SessionType.EXTENDED
    )


def _enter_session_with_auth(
    client: UDSClient,
    sessions: list,
    security_level: int,
    algo_name: str = "xor_placeholder",
) -> None:
    """Enter the highest-priority allowed session and unlock security if needed."""
    target = "extended" if "extended" in sessions else sessions[0] if sessions else "default"
    r = client.change_session(_session_type(target))
    assert r.positive, f"Could not enter {target} session: {r.nrc_name}"

    if security_level > 0 and client.security_level < security_level:
        algo = get_algorithm(algo_name)
        perform_security_access(client, level=security_level, algorithm=algo)


def test_read_did(
    uds_client: UDSClient,
    result_collector: RunResult,
    did_entry: Dict[str, Any],
) -> None:
    """
    0x22 ReadDataByIdentifier — one test per DID in the matrix.

    Validates:
    - Positive response received.
    - Response data length matches ``length`` in YAML.
    - For ``ascii`` type: value matches ``expected_format`` regex (if declared).
    - For ``uint8/uint16/uint32``: value within ``value_range`` (if declared).
    """
    did_id_str  = did_entry["id"]
    did_int     = int(did_id_str, 16)
    did_name    = did_entry.get("name", did_id_str)
    sessions    = did_entry.get("sessions", ["default"])
    sec_level   = did_entry.get("security_level", 0)
    exp_length  = did_entry.get("length", 1)
    data_type   = did_entry.get("data_type", "hex")

    record = TestRecord(
        test_id=f"did/{did_id_str}-read",
        category="did",
        service_id="0x22",
        did_id=did_id_str,
        session=sessions[0] if sessions else "default",
    )

    try:
        _enter_session_with_auth(uds_client, sessions, sec_level)

        resp = uds_client.read_did(did_int)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"ReadDID {did_id_str} ({did_name}) returned {resp.nrc_name}"
        )

        # Response data: [DID_high, DID_low, ...value_bytes...]
        value_bytes = resp.data[2:]
        record.extra["length_ok"] = (len(value_bytes) == exp_length)

        assert len(value_bytes) == exp_length, (
            f"DID {did_id_str} length mismatch: expected {exp_length} bytes, "
            f"got {len(value_bytes)}"
        )

        # Type-specific validation
        if data_type == "ascii":
            text = value_bytes.decode("ascii", errors="replace").rstrip("\x00")
            fmt = did_entry.get("expected_format")
            if fmt:
                record.extra["format_ok"] = bool(re.fullmatch(fmt, text))
                assert re.fullmatch(fmt, text), (
                    f"DID {did_id_str} ASCII value '{text}' does not match pattern '{fmt}'"
                )

        elif data_type in ("uint8", "uint16", "uint32"):
            int_val = int.from_bytes(value_bytes, "big")
            vrange = did_entry.get("value_range")
            if vrange:
                lo, hi = vrange
                assert lo <= int_val <= hi, (
                    f"DID {did_id_str} value {int_val} out of range [{lo}, {hi}]"
                )

        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
