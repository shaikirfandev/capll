# adas_framework/core/retry.py
"""
Retry and flaky-test handling for the ADAS framework.

Provides:
    @retry(max_attempts=3, delay_s=1.0, exceptions=(AssertionError,))
    @flaky(max_runs=5, min_passes=3)
    RetryContext — runtime retry loop with exponential back-off
    FlakyTracker — session-level tracker for identifying flaky tests

ISO 26262 Note:
    Safety-critical tests (ASIL C/D) should NOT use @flaky — a genuine
    failure must surface immediately. Use @retry only for known transient
    infra issues (e.g., CAN bus connect timeout).
"""
from __future__ import annotations

import asyncio
import functools
import time
from typing import Callable, Tuple, Type

from core.logger import get_logger

log = get_logger("retry")


# ─────────────────────────────────────────────────────────────────────────────
# @retry decorator
# ─────────────────────────────────────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    delay_s: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable | None = None,
):
    """
    Retry a test function on failure with exponential back-off.

    Args:
        max_attempts: Total number of attempts (including first).
        delay_s:      Initial delay between retries in seconds.
        backoff:      Multiplier applied to delay on each retry.
        exceptions:   Exception types that trigger a retry.
        on_retry:     Optional callback(attempt, exc) called on each retry.

    Example:
        @retry(max_attempts=3, delay_s=0.5, exceptions=(TimeoutError,))
        def test_ecu_responds():
            ...
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                wait = delay_s
                last_exc = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        last_exc = exc
                        if attempt == max_attempts:
                            break
                        log.warning(
                            f"[RETRY] {func.__name__} attempt {attempt}/{max_attempts} "
                            f"failed: {exc}. Retrying in {wait:.1f}s..."
                        )
                        if on_retry:
                            on_retry(attempt, exc)
                        await asyncio.sleep(wait)
                        wait *= backoff
                raise last_exc
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                wait = delay_s
                last_exc = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as exc:
                        last_exc = exc
                        if attempt == max_attempts:
                            break
                        log.warning(
                            f"[RETRY] {func.__name__} attempt {attempt}/{max_attempts} "
                            f"failed: {exc}. Retrying in {wait:.1f}s..."
                        )
                        if on_retry:
                            on_retry(attempt, exc)
                        time.sleep(wait)
                        wait *= backoff
                raise last_exc
            return sync_wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# @flaky decorator
# ─────────────────────────────────────────────────────────────────────────────

def flaky(max_runs: int = 5, min_passes: int = 3):
    """
    Mark a test as flaky — run it up to max_runs times and pass if it
    succeeds at least min_passes times.

    ⚠ DO NOT use for ASIL C/D safety tests. Only use for known
       infrastructure-level intermittencies (network, timing).

    Example:
        @flaky(max_runs=5, min_passes=3)
        def test_camera_latency():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            passes = 0
            failures = []
            for run in range(1, max_runs + 1):
                try:
                    func(*args, **kwargs)
                    passes += 1
                    log.debug(f"[FLAKY] {func.__name__} run {run}: PASS ({passes}/{min_passes})")
                    if passes >= min_passes:
                        return
                except Exception as exc:
                    failures.append(str(exc))
                    log.debug(f"[FLAKY] {func.__name__} run {run}: FAIL — {exc}")

            raise AssertionError(
                f"Flaky test '{func.__name__}' passed {passes}/{max_runs} runs "
                f"(required {min_passes}). Failures: {failures}"
            )
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# RetryContext — use inside a test body
# ─────────────────────────────────────────────────────────────────────────────

class RetryContext:
    """
    In-test retry loop with configurable back-off.

    Usage:
        with RetryContext(max_attempts=5, delay_s=0.2) as ctx:
            while ctx.should_retry():
                try:
                    result = read_sensor()
                    ctx.succeed()
                except SensorTimeout:
                    ctx.record_failure()
    """

    def __init__(self, max_attempts: int = 3, delay_s: float = 0.5,
                 backoff: float = 1.5):
        self.max_attempts = max_attempts
        self.delay_s = delay_s
        self.backoff = backoff
        self._attempt = 0
        self._succeeded = False
        self._last_exc: Exception | None = None
        self._wait = delay_s

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def should_retry(self) -> bool:
        if self._succeeded:
            return False
        if self._attempt >= self.max_attempts:
            if self._last_exc:
                raise self._last_exc
            return False
        self._attempt += 1
        return True

    def record_failure(self, exc: Exception | None = None):
        self._last_exc = exc
        if self._attempt < self.max_attempts:
            time.sleep(self._wait)
            self._wait *= self.backoff

    def succeed(self):
        self._succeeded = True


# ─────────────────────────────────────────────────────────────────────────────
# Session-level flaky tracker (used by conftest to build report)
# ─────────────────────────────────────────────────────────────────────────────

class FlakyTracker:
    """Tracks test pass/fail history across a session for flakiness analysis."""

    def __init__(self):
        self._history: dict[str, list[bool]] = {}

    def record(self, test_id: str, passed: bool):
        self._history.setdefault(test_id, []).append(passed)

    def is_flaky(self, test_id: str, threshold: float = 0.3) -> bool:
        """A test is flaky if its failure rate is between threshold and 1.0."""
        runs = self._history.get(test_id, [])
        if len(runs) < 2:
            return False
        fail_rate = runs.count(False) / len(runs)
        return 0 < fail_rate < 1.0

    def flaky_tests(self) -> list[dict]:
        results = []
        for test_id, runs in self._history.items():
            if len(runs) < 2:
                continue
            fail_rate = runs.count(False) / len(runs)
            if 0 < fail_rate < 1.0:
                results.append({
                    "test_id": test_id,
                    "runs": len(runs),
                    "passes": runs.count(True),
                    "failures": runs.count(False),
                    "fail_rate_pct": round(fail_rate * 100, 1),
                })
        return sorted(results, key=lambda x: x["fail_rate_pct"], reverse=True)

    def summary(self) -> str:
        flaky = self.flaky_tests()
        if not flaky:
            return "No flaky tests detected."
        lines = [f"Flaky tests detected ({len(flaky)}):"]
        for t in flaky:
            lines.append(
                f"  {t['test_id']:<60} "
                f"{t['passes']}P/{t['failures']}F  "
                f"({t['fail_rate_pct']}% fail)"
            )
        return "\n".join(lines)
