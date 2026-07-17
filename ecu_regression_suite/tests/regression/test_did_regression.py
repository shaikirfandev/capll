"""
DID regression tests — compare current DID values/lengths against baseline.

These tests read every DID in the matrix and compare the response against the
stored baseline.  Any difference (value changed, length changed, NRC changed,
previously-passing DID now failing) is flagged as a regression.

Regression classifications:
- REGRESSION: DID was readable in baseline, now returns NRC or different value.
- VALUE_CHANGE: Both runs passed, but the returned value differs.
- LENGTH_CHANGE: Response data length changed between runs.
- NEW_DID: DID not present in baseline (new in this SW version).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.regression]


def _enter_for_did(client: UDSClient, sessions: list, sec_level: int) -> None:
    target = "extended" if "extended" in sessions else sessions[0] if sessions else "default"
    mapping = {"default": SessionType.DEFAULT, "programming": SessionType.PROGRAMMING}
    r = client.change_session(mapping.get(target, SessionType.EXTENDED))
    assert r.positive, f"Could not enter {target} session"
    if sec_level > 0 and client.security_level < sec_level:
        algo = get_algorithm("xor_placeholder")
        perform_security_access(client, level=sec_level, algorithm=algo)


def test_did_regression(
    uds_client: UDSClient,
    result_collector: RunResult,
    baseline_loader: Optional[RunResult],
    did_entry: Dict[str, Any],
) -> None:
    """
    Regression check: read a DID and compare with baseline.

    If no baseline exists, this test simply records the current value as
    a "new baseline candidate" and passes (first-run behaviour).
    """
    did_id_str  = did_entry["id"]
    did_int     = int(did_id_str, 16)
    sessions    = did_entry.get("sessions", ["default"])
    sec_level   = did_entry.get("security_level", 0)
    exp_length  = did_entry.get("length", 1)

    test_id  = f"did/{did_id_str}-read"
    baseline_record: Optional[TestRecord] = None
    if baseline_loader:
        baseline_record = baseline_loader.records.get(test_id)

    record = TestRecord(
        test_id=test_id,
        category="did",
        service_id="0x22",
        did_id=did_id_str,
        session=sessions[0] if sessions else "default",
    )

    try:
        _enter_for_did(uds_client, sessions, sec_level)
        resp = uds_client.read_did(did_int)

        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        if baseline_record is None:
            # First run / no baseline — just verify the DID is readable
            assert resp.positive, (
                f"DID {did_id_str} is not readable (no baseline to compare): {resp.nrc_name}"
            )
            record.status = "pass"
            return

        # ── Baseline comparison ────────────────────────────────────────────────
        was_passing = baseline_record.status == "pass"
        now_passing = resp.positive

        if was_passing and not now_passing:
            msg = (
                f"REGRESSION: DID {did_id_str} was readable in baseline "
                f"(v{baseline_loader.version if baseline_loader else '?'}) "
                f"but now returns NRC {resp.nrc_name}"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        if not was_passing and now_passing:
            # Improvement — pass but flag for review
            record.status = "pass"
            record.extra["improvement"] = (
                f"DID {did_id_str} previously failing ({baseline_record.status}), "
                f"now passing — verify intentional"
            )
            return

        assert resp.positive, (
            f"DID {did_id_str} still failing (was failing in baseline too): {resp.nrc_name}"
        )

        # Both pass: compare values
        current_val = resp.data.hex().upper()
        baseline_val = baseline_record.actual_value or ""

        # Length regression
        value_bytes = resp.data[2:]
        if len(value_bytes) != exp_length:
            msg = (
                f"LENGTH REGRESSION: DID {did_id_str} — "
                f"expected {exp_length} bytes, got {len(value_bytes)}"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        # Value regression: flag if value changed for DIDs that should be stable
        static_did_prefixes = ("0xF1", "0xF0")  # ISO/OBD DIDs are typically static
        is_static = any(did_id_str.upper().startswith(p.upper()) for p in static_did_prefixes)
        if is_static and current_val != baseline_val:
            msg = (
                f"VALUE REGRESSION: Static DID {did_id_str} value changed — "
                f"baseline: {baseline_val}, current: {current_val}"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        record.status = "pass"
        if current_val != baseline_val:
            record.extra["value_changed"] = True
            record.extra["baseline_val"] = baseline_val
            record.extra["current_val"]  = current_val

    except AssertionError as exc:
        if record.status not in ("fail",):
            record.status = "fail"
            record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
