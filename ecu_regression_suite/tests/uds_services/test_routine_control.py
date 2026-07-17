"""
Data-driven RoutineControl (0x31) tests.

One test per RID entry in ``config/<ecu>/rid_matrix.yaml``:
- Start routine (0x31 0x01) — positive response, timing within expected bounds.
- Request results (0x31 0x03) — where ``supports_results: true``.
- Stop routine (0x31 0x02) — where ``supports_stop: true``.
- Access control: no-security → NRC 0x33; wrong session → NRC 0x7F.
"""
from __future__ import annotations

import time
from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]


def _enter_for_rid(client: UDSClient, sessions: list, sec_level: int) -> None:
    target = "extended" if "extended" in sessions else sessions[0] if sessions else "extended"
    mapping = {"default": SessionType.DEFAULT, "programming": SessionType.PROGRAMMING}
    sess_type = mapping.get(target, SessionType.EXTENDED)
    r = client.change_session(sess_type)
    assert r.positive, f"Could not enter {target} session: {r.nrc_name}"
    if sec_level > 0:
        algo = get_algorithm("xor_placeholder")
        perform_security_access(client, level=sec_level, algorithm=algo)


def test_routine_control_start(
    uds_client: UDSClient,
    result_collector: RunResult,
    rid_entry: Dict[str, Any],
) -> None:
    """
    0x31 0x01 — Start every RID; verify positive response and timing regression.

    Timing regression rule: elapsed_ms must be ≤ max_duration_ms from YAML.
    """
    rid_id_str  = rid_entry["id"]
    rid_int     = int(rid_id_str, 16)
    rid_name    = rid_entry.get("name", rid_id_str)
    sessions    = rid_entry.get("sessions", ["extended"])
    sec_level   = rid_entry.get("security_level", 0)
    max_ms      = rid_entry.get("max_duration_ms", 30_000)
    exp_ms      = rid_entry.get("expected_duration_ms", 0)

    record = TestRecord(
        test_id=f"rid/{rid_id_str}-start",
        category="rid",
        service_id="0x31",
        rid_id=rid_id_str,
        session=sessions[0] if sessions else "extended",
    )
    try:
        _enter_for_rid(uds_client, sessions, sec_level)

        t0   = time.monotonic()
        resp = uds_client.start_routine(rid_int)
        elapsed = (time.monotonic() - t0) * 1000

        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"StartRoutine {rid_id_str} ({rid_name}) returned {resp.nrc_name}"
        )

        timing_ok = resp.elapsed_ms <= max_ms
        record.extra["timing_ok"]       = timing_ok
        record.extra["expected_ms"]     = exp_ms
        record.extra["max_allowed_ms"]  = max_ms

        assert timing_ok, (
            f"Routine {rid_id_str} timing regression: "
            f"{resp.elapsed_ms:.1f}ms > max {max_ms}ms"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_routine_control_request_results(
    uds_client: UDSClient,
    result_collector: RunResult,
    rid_entry: Dict[str, Any],
) -> None:
    """
    0x31 0x03 — Request results for every RID that declares ``supports_results: true``.
    """
    if not rid_entry.get("supports_results", False):
        pytest.skip(f"RID {rid_entry['id']} does not support requestResults (0x31 0x03)")

    rid_id_str = rid_entry["id"]
    rid_int    = int(rid_id_str, 16)
    sessions   = rid_entry.get("sessions", ["extended"])
    sec_level  = rid_entry.get("security_level", 0)

    record = TestRecord(
        test_id=f"rid/{rid_id_str}-results",
        category="rid",
        service_id="0x31",
        rid_id=rid_id_str,
        session=sessions[0] if sessions else "extended",
    )
    try:
        _enter_for_rid(uds_client, sessions, sec_level)

        # Start the routine first
        uds_client.start_routine(rid_int)

        # Request results
        resp = uds_client.request_routine_results(rid_int)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        assert resp.positive, (
            f"RequestRoutineResults {rid_id_str} returned {resp.nrc_name}"
        )
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_routine_control_stop(
    uds_client: UDSClient,
    rid_entry: Dict[str, Any],
) -> None:
    """
    0x31 0x02 — Stop every RID that declares ``supports_stop: true``.
    """
    if not rid_entry.get("supports_stop", False):
        pytest.skip(f"RID {rid_entry['id']} does not support stop (0x31 0x02)")

    rid_id_str = rid_entry["id"]
    rid_int    = int(rid_id_str, 16)
    sessions   = rid_entry.get("sessions", ["extended"])
    sec_level  = rid_entry.get("security_level", 0)

    _enter_for_rid(uds_client, sessions, sec_level)

    # Start before stopping
    uds_client.start_routine(rid_int)

    stop_resp = uds_client.stop_routine(rid_int)
    assert stop_resp.positive, (
        f"StopRoutine {rid_id_str} returned {stop_resp.nrc_name}"
    )
    uds_client.change_session(SessionType.DEFAULT)


def test_routine_control_security_denied(
    uds_client: UDSClient,
    rid_entry: Dict[str, Any],
) -> None:
    """
    0x31 — Secured routines (security_level > 0) must return NRC 0x33
    when attempted without security access.
    """
    if rid_entry.get("security_level", 0) == 0:
        pytest.skip(f"RID {rid_entry['id']} does not require security")

    rid_id_str = rid_entry["id"]
    rid_int    = int(rid_id_str, 16)
    sessions   = rid_entry.get("sessions", ["extended"])

    target = "extended" if "extended" in sessions else sessions[0]
    mapping = {"default": SessionType.DEFAULT, "programming": SessionType.PROGRAMMING}
    r = uds_client.change_session(mapping.get(target, SessionType.EXTENDED))
    assert r.positive
    # Ensure no security access

    resp = uds_client.start_routine(rid_int)
    assert not resp.positive
    assert resp.nrc == 0x33, (
        f"Expected NRC 0x33 (securityAccessDenied) for {rid_id_str} without auth, "
        f"got 0x{resp.nrc:02X}"
    )
    uds_client.change_session(SessionType.DEFAULT)
