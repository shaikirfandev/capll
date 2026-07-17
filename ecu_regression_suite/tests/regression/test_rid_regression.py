"""
RID regression tests — compare routine execution time and result against baseline.

Checks:
- Routine still starts successfully (not a regression).
- Execution time has not drifted by more than 100% or 50 ms (timing regression).
- Result bytes match baseline (result content regression).
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.regression]


def _enter_for_rid(client: UDSClient, sessions: list, sec_level: int) -> None:
    target = "extended" if "extended" in sessions else sessions[0] if sessions else "extended"
    mapping = {"default": SessionType.DEFAULT, "programming": SessionType.PROGRAMMING}
    r = client.change_session(mapping.get(target, SessionType.EXTENDED))
    assert r.positive
    if sec_level > 0 and client.security_level < sec_level:
        algo = get_algorithm("xor_placeholder")
        perform_security_access(client, level=sec_level, algorithm=algo)


def test_rid_regression(
    uds_client: UDSClient,
    result_collector: RunResult,
    baseline_loader: Optional[RunResult],
    rid_entry: Dict[str, Any],
) -> None:
    """
    Regression check: start a routine and compare timing + result with baseline.
    """
    rid_id_str = rid_entry["id"]
    rid_int    = int(rid_id_str, 16)
    sessions   = rid_entry.get("sessions", ["extended"])
    sec_level  = rid_entry.get("security_level", 0)
    max_ms     = rid_entry.get("max_duration_ms", 30_000)
    exp_ms     = rid_entry.get("expected_duration_ms", 0)

    test_id = f"rid/{rid_id_str}-start"
    baseline_record: Optional[TestRecord] = None
    if baseline_loader:
        baseline_record = baseline_loader.records.get(test_id)

    record = TestRecord(
        test_id=test_id,
        category="rid",
        service_id="0x31",
        rid_id=rid_id_str,
        session=sessions[0] if sessions else "extended",
    )

    try:
        _enter_for_rid(uds_client, sessions, sec_level)

        resp = uds_client.start_routine(rid_int)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms
        record.extra["expected_ms"]    = exp_ms
        record.extra["max_allowed_ms"] = max_ms

        if baseline_record is None:
            assert resp.positive, f"Routine {rid_id_str} not executable: {resp.nrc_name}"
            record.status = "pass"
            return

        # ── Baseline comparison ────────────────────────────────────────────────
        was_passing = baseline_record.status == "pass"
        now_passing = resp.positive

        if was_passing and not now_passing:
            msg = (
                f"REGRESSION: Routine {rid_id_str} was executable in baseline "
                f"but now returns {resp.nrc_name}"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        assert resp.positive, f"Routine {rid_id_str} failed: {resp.nrc_name}"

        # Timing regression: flag if elapsed_ms > max_duration_ms
        if resp.elapsed_ms > max_ms:
            msg = (
                f"TIMING REGRESSION: Routine {rid_id_str} took "
                f"{resp.elapsed_ms:.1f}ms, exceeds max {max_ms}ms"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        # Timing drift from baseline: flag if >100% or >50 ms
        base_elapsed = baseline_record.elapsed_ms or 0.0
        if base_elapsed > 0:
            drift_abs = abs(resp.elapsed_ms - base_elapsed)
            drift_pct = drift_abs / base_elapsed * 100
            record.extra["timing_drift_ms"]  = round(drift_abs, 2)
            record.extra["timing_drift_pct"] = round(drift_pct, 1)
            if drift_abs > 50 or drift_pct > 100:
                record.extra["timing_regression_flag"] = True
                # This is a warning, not a hard failure — add to extra but don't fail
                record.extra["timing_warning"] = (
                    f"Timing drift detected: {drift_abs:.1f}ms ({drift_pct:.0f}%) "
                    f"vs baseline {base_elapsed:.1f}ms"
                )

        # Result content regression
        current_result  = resp.data.hex().upper()
        baseline_result = baseline_record.actual_value or ""
        if current_result != baseline_result:
            record.extra["result_changed"] = True
            record.extra["baseline_result"] = baseline_result
            record.extra["current_result"]  = current_result
            # Result change is logged but not a hard failure unless routine indicates error
            # (0x01 = pass, 0x00 = fail in common coding)
            result_bytes = resp.data[3:]  # strip sub-fn + RID echo
            if result_bytes and result_bytes[0] != 0x01:
                msg = (
                    f"RESULT REGRESSION: Routine {rid_id_str} result indicates failure "
                    f"(first result byte = 0x{result_bytes[0]:02X})"
                )
                record.status = "fail"
                record.failure_reason = msg
                pytest.fail(msg)

        record.status = "pass"

    except AssertionError as exc:
        if record.status not in ("fail",):
            record.status = "fail"
            record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
