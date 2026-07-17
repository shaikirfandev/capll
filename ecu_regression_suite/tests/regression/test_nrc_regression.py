"""
NRC regression tests — verify NRC behavior is consistent with baseline.

If a previously-expected NRC changes (e.g. a new SW version starts returning
a different NRC for the same negative scenario), this test flags it as a regression.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, ServiceID, SessionType

from tests.nrc_matrix.test_nrc_responses import _trigger_nrc_scenario


pytestmark = [pytest.mark.regression]

_SESSION_MAP = {
    "default":     SessionType.DEFAULT,
    "extended":    SessionType.EXTENDED,
    "programming": SessionType.PROGRAMMING,
}


def test_nrc_regression(
    uds_client: UDSClient,
    result_collector: RunResult,
    baseline_loader: Optional[RunResult],
    nrc_scenario: Dict[str, Any],
) -> None:
    """
    NRC regression: verify each negative-response scenario still produces
    the same NRC as in the baseline.

    Regressions:
    - NRC changed from expected (different error code → potential behavior change).
    - Previously negative response now returns positive (NRC scenario no longer triggered).
    """
    scenario_name = nrc_scenario["scenario"]
    expected_nrc  = int(nrc_scenario["expected_nrc"], 16)
    setup_session = nrc_scenario.get("setup_session", "default")
    setup_security = int(nrc_scenario.get("setup_security", 0))

    test_id = f"nrc/{scenario_name}"
    baseline_record: Optional[TestRecord] = None
    if baseline_loader:
        baseline_record = baseline_loader.records.get(test_id)

    record = TestRecord(
        test_id=test_id,
        category="nrc",
        service_id=nrc_scenario.get("service_id"),
        session=setup_session,
        nrc_code=nrc_scenario["expected_nrc"],
        extra={"expected_nrc": nrc_scenario["expected_nrc"]},
    )

    try:
        r = uds_client.change_session(_SESSION_MAP.get(setup_session, SessionType.DEFAULT))
        assert r.positive

        is_security_test = "security" in scenario_name.lower() or "key" in scenario_name.lower()
        if setup_security > 0 and not is_security_test:
            algo = get_algorithm("xor_placeholder")
            perform_security_access(uds_client, level=setup_security, algorithm=algo)

        resp = _trigger_nrc_scenario(uds_client, nrc_scenario)
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        if baseline_record is None:
            # No baseline — verify NRC is correct per YAML spec
            assert not resp.positive, (
                f"Expected NRC 0x{expected_nrc:02X} but got POSITIVE response"
            )
            assert resp.nrc == expected_nrc, (
                f"NRC mismatch: expected 0x{expected_nrc:02X}, got 0x{resp.nrc:02X}"
            )
            record.status = "pass"
            return

        # ── Baseline comparison ────────────────────────────────────────────────
        was_failing   = baseline_record.status == "pass"   # "pass" means NRC was correctly received
        base_nrc_str  = baseline_record.actual_nrc or f"0x{expected_nrc:02X}"
        curr_nrc_str  = f"0x{resp.nrc:02X}" if resp.nrc else "positive"

        if was_failing and resp.positive:
            msg = (
                f"NRC REGRESSION: Scenario '{scenario_name}' previously returned NRC "
                f"{base_nrc_str} but now returns POSITIVE — NRC no longer triggered"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        if base_nrc_str != curr_nrc_str:
            msg = (
                f"NRC CHANGE: Scenario '{scenario_name}' NRC changed "
                f"from {base_nrc_str} (baseline) to {curr_nrc_str} (current)"
            )
            # NRC change is a soft regression (report but allow override in accepted-changes config)
            record.extra["nrc_changed"] = True
            record.extra["baseline_nrc"] = base_nrc_str
            record.extra["current_nrc"]  = curr_nrc_str

        assert not resp.positive, (
            f"Expected NRC 0x{expected_nrc:02X} but got POSITIVE response"
        )
        assert resp.nrc == expected_nrc, (
            f"NRC mismatch: expected 0x{expected_nrc:02X}, got 0x{resp.nrc:02X} ({resp.nrc_name})"
        )
        record.status = "pass"

    except AssertionError as exc:
        if record.status not in ("fail",):
            record.status = "fail"
            record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
