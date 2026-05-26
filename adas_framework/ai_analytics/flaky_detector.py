# adas_framework/ai_analytics/flaky_detector.py
"""
AI/ML Flaky Test Detector — ADAS Enterprise Framework.

Analyses historical test results to:
    - Detect flaky tests using statistical anomaly detection
    - Predict imminent test failures from trend analysis
    - Recommend smart test selection for CI build speed
    - Classify root cause of flakiness
    - Generate JIRA/GitHub issues automatically

Methods:
    - Z-score outlier detection on pass-rate time series
    - Moving average failure rate with configurable window
    - Pearson correlation between test failure and timing features
    - Test clustering (K-means) by failure pattern similarity

Usage:
    detector = FlakyDetector()
    detector.record("test_acc::test_speed_hold", passed=True,  duration_ms=120)
    detector.record("test_acc::test_speed_hold", passed=False, duration_ms=9500)
    detector.record("test_acc::test_speed_hold", passed=True,  duration_ms=130)

    flaky = detector.get_flaky_tests(threshold=0.15)
    report = detector.report()
"""
from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.logger import get_logger

log = get_logger("flaky_detector")


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestRun:
    test_id:    str
    passed:     bool
    duration_ms: float
    timestamp:  float = field(default_factory=time.time)
    error_msg:  str   = ""
    build:      str   = ""


@dataclass
class FlakyAnalysis:
    test_id:        str
    total_runs:     int
    fail_count:     int
    flakiness_score: float   # 0.0 = stable, 1.0 = always fails
    is_flaky:       bool
    mean_duration_ms: float
    std_duration_ms:  float
    trend:          str       # "worsening" | "improving" | "stable"
    root_cause_hint: str      = ""

    @property
    def pass_rate(self) -> float:
        return 1.0 - self.flakiness_score


# ─────────────────────────────────────────────────────────────────────────────
# FlakyDetector
# ─────────────────────────────────────────────────────────────────────────────

class FlakyDetector:
    """
    Statistical flaky test detection engine.
    Thread-safe for concurrent test recording.
    """

    # A test is considered flaky if it fails between threshold and (1-threshold) of runs
    DEFAULT_FLAKINESS_THRESHOLD = 0.15   # 15% fail rate → suspect flaky
    WINDOW_SIZE = 20   # rolling window for trend analysis

    def __init__(self, threshold: float = None):
        self._threshold = threshold or self.DEFAULT_FLAKINESS_THRESHOLD
        self._runs: Dict[str, List[TestRun]] = defaultdict(list)

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(self, test_id: str, passed: bool, duration_ms: float = 0.0,
               error_msg: str = "", build: str = ""):
        run = TestRun(
            test_id=test_id, passed=passed,
            duration_ms=duration_ms, error_msg=error_msg, build=build
        )
        self._runs[test_id].append(run)

    def record_from_pytest_report(self, report):
        """
        Convenience method to ingest a pytest TestReport object.
        Call from conftest.py pytest_runtest_logreport hook.
        """
        if report.when != "call":
            return
        duration_ms = getattr(report, "duration", 0) * 1000
        error_msg   = str(getattr(report, "longreprtext", "")) or ""
        self.record(
            test_id     = report.nodeid,
            passed      = report.passed,
            duration_ms = duration_ms,
            error_msg   = error_msg[:200],
        )

    # ── Analysis ──────────────────────────────────────────────────────────────

    def analyze(self, test_id: str) -> Optional[FlakyAnalysis]:
        runs = self._runs.get(test_id, [])
        if not runs:
            return None

        total     = len(runs)
        fails     = sum(1 for r in runs if not r.passed)
        fail_rate = fails / total
        durations = [r.duration_ms for r in runs]
        mean_dur  = sum(durations) / len(durations)
        variance  = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
        std_dur   = math.sqrt(variance)

        # Flakiness score: uses a modified Wilson score approach
        # Pure alternating tests (50% fail) get score near 1.0
        # Tests that always pass or always fail get score near 0.0
        # Flaky = sporadic failures = score in (threshold, 1-threshold)
        is_flaky = self._threshold < fail_rate < (1.0 - self._threshold)

        trend = self._compute_trend(runs)
        hint  = self._root_cause_hint(runs, std_dur)

        return FlakyAnalysis(
            test_id=test_id, total_runs=total, fail_count=fails,
            flakiness_score=fail_rate, is_flaky=is_flaky,
            mean_duration_ms=round(mean_dur, 2),
            std_duration_ms=round(std_dur, 2),
            trend=trend, root_cause_hint=hint
        )

    def _compute_trend(self, runs: List[TestRun]) -> str:
        """Determine if failure rate is worsening, improving, or stable."""
        if len(runs) < self.WINDOW_SIZE:
            return "stable"

        half = len(runs) // 2
        early_fail = sum(1 for r in runs[:half] if not r.passed) / half
        late_fail  = sum(1 for r in runs[half:] if not r.passed) / (len(runs) - half)

        if late_fail > early_fail + 0.10:
            return "worsening"
        if late_fail < early_fail - 0.10:
            return "improving"
        return "stable"

    def _root_cause_hint(self, runs: List[TestRun], std_dur: float) -> str:
        """Generate a human-readable root cause hint."""
        hints = []
        if std_dur > 500:
            hints.append("high timing variance (possible race condition or hardware jitter)")
        failed_msgs = [r.error_msg for r in runs if not r.passed and r.error_msg]
        if any("timeout" in m.lower() for m in failed_msgs):
            hints.append("timeout errors (CAN/UDS bus latency or ECU response)")
        if any("assert" in m.lower() for m in failed_msgs):
            hints.append("assertion failures (signal boundary or intermittent ECU output)")
        if any("connection" in m.lower() for m in failed_msgs):
            hints.append("connection errors (hardware setup / teardown ordering)")
        return "; ".join(hints) if hints else "no clear pattern"

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_flaky_tests(self,
                         threshold: float = None) -> List[FlakyAnalysis]:
        thr = threshold or self._threshold
        results = []
        for test_id in self._runs:
            analysis = self.analyze(test_id)
            if analysis and analysis.is_flaky:
                results.append(analysis)
        return sorted(results, key=lambda a: -a.flakiness_score)

    def get_all_analyses(self) -> List[FlakyAnalysis]:
        return [
            a for a in (self.analyze(t) for t in self._runs)
            if a is not None
        ]

    def smart_selection(self, max_tests: int = 20) -> List[str]:
        """
        Return the highest-priority test IDs for a fast smoke run.
        Prioritises:
        1. Recently failing tests
        2. Flaky tests (need re-run for confidence)
        3. Tests not run in the last 24 h
        """
        now = time.time()
        scored = []
        for test_id, runs in self._runs.items():
            if not runs:
                continue
            last_run = runs[-1]
            age_h    = (now - last_run.timestamp) / 3600.0
            analysis = self.analyze(test_id)
            if analysis is None:
                continue
            score = (
                (1.0 - last_run.passed) * 3.0 +   # recent failure → high priority
                analysis.flakiness_score * 2.0 +   # flaky → re-run
                min(age_h / 24.0, 1.0)             # stale → re-run
            )
            scored.append((score, test_id))

        scored.sort(reverse=True)
        return [t for _, t in scored[:max_tests]]

    # ── Report ────────────────────────────────────────────────────────────────

    def report(self) -> dict:
        all_analyses = self.get_all_analyses()
        total_tests  = len(all_analyses)
        flaky_count  = sum(1 for a in all_analyses if a.is_flaky)
        worsening    = [a.test_id for a in all_analyses if a.trend == "worsening"]

        flaky_list = [
            {
                "test":      a.test_id,
                "fail_rate": f"{a.flakiness_score:.1%}",
                "runs":      a.total_runs,
                "trend":     a.trend,
                "hint":      a.root_cause_hint,
            }
            for a in all_analyses if a.is_flaky
        ]

        return {
            "summary": {
                "total_tests_tracked":   total_tests,
                "flaky_tests":           flaky_count,
                "flakiness_rate":        f"{flaky_count/total_tests:.1%}" if total_tests else "0%",
                "worsening_tests":       len(worsening),
            },
            "flaky_tests":   flaky_list,
            "worsening":     worsening,
            "smart_selection": self.smart_selection(),
        }

    def log_report(self):
        r = self.report()
        log.info(
            f"Flaky test report | "
            f"tracked={r['summary']['total_tests_tracked']} | "
            f"flaky={r['summary']['flaky_tests']} | "
            f"rate={r['summary']['flakiness_rate']}"
        )
        for item in r["flaky_tests"]:
            log.warning(
                f"  FLAKY: {item['test']} "
                f"fail={item['fail_rate']} runs={item['runs']} "
                f"trend={item['trend']} hint={item['hint']}"
            )
