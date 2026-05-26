"""
pytest_framework/core/retry.py

Enterprise ADAS Framework – Retry & Flaky Test Utilities
==========================================================
  @retry         — decorator for transient flaky hardware calls
  @flaky         — marks a test as known-flaky (ASIL-aware)
  wait_for       — polling helper with timeout
  FlakyTracker   — session-scoped flakiness ledger (feeds ai_analytics)
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, Optional, Tuple, Type

import pytest

from core.logger import get_logger

log = get_logger("retry")


# ── @retry ────────────────────────────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    delay_s: float = 0.5,
    backoff: float = 1.5,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_name: str = "retry",
):
    """
    Retry decorator for hardware / CAN / UDS calls that may transiently fail.

    Args:
        max_attempts: Total attempts (including first try).
        delay_s:      Initial delay between retries.
        backoff:      Multiplier applied to delay after each failure.
        exceptions:   Exception types to catch and retry on.
        logger_name:  Logger to use for retry messages.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _log   = get_logger(logger_name)
            delay  = delay_s
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        _log.warning(
                            f"[retry] {fn.__qualname__} attempt {attempt}/{max_attempts} "
                            f"failed: {exc!r} — retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        _log.error(
                            f"[retry] {fn.__qualname__} exhausted {max_attempts} attempts"
                        )
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ── @flaky ────────────────────────────────────────────────────────────────────

def flaky(
    max_runs: int = 3,
    min_passes: int = 1,
    reason: str = "Known flaky test",
):
    """
    Re-run a test up to max_runs times; pass if it passes min_passes times.
    ASIL C/D tests MUST NOT use this decorator — enforced at collection time
    (conftest.py checks for @flaky on ASIL C/D classes).
    """
    def decorator(fn: Callable) -> Callable:
        fn._flaky        = True           # type: ignore[attr-defined]
        fn._flaky_runs   = max_runs       # type: ignore[attr-defined]
        fn._flaky_passes = min_passes     # type: ignore[attr-defined]
        fn._flaky_reason = reason         # type: ignore[attr-defined]

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            passes = 0
            last_exc: Optional[Exception] = None
            for run in range(1, max_runs + 1):
                try:
                    result = fn(*args, **kwargs)
                    passes += 1
                    log.debug(f"[flaky] {fn.__qualname__} run {run} PASSED ({passes}/{min_passes})")
                    if passes >= min_passes:
                        return result
                except Exception as exc:
                    last_exc = exc
                    log.warning(f"[flaky] {fn.__qualname__} run {run} FAILED: {exc!r}")
            pytest.fail(
                f"[flaky] {fn.__qualname__} passed only {passes}/{min_passes} "
                f"required runs (last error: {last_exc!r})"
            )
        return wrapper
    return decorator


# ── wait_for ──────────────────────────────────────────────────────────────────

def wait_for(
    condition: Callable[[], bool],
    timeout_s: float = 5.0,
    poll_interval_s: float = 0.05,
    description: str = "condition",
) -> float:
    """
    Poll condition() until True or timeout.

    Returns:
        Elapsed seconds when condition became True.

    Raises:
        TimeoutError: If condition not met within timeout_s.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if condition():
            elapsed = timeout_s - (deadline - time.monotonic())
            log.debug(f"[wait_for] '{description}' met in {elapsed:.3f}s")
            return elapsed
        time.sleep(poll_interval_s)
    raise TimeoutError(
        f"[wait_for] '{description}' not met within {timeout_s}s"
    )


# ── FlakyTracker ──────────────────────────────────────────────────────────────

class FlakyTracker:
    """
    Lightweight session-scoped flakiness ledger.
    Collects pass/fail history per test node-id.
    Results are consumed by ai_analytics/flaky_detector.py.
    """
    def __init__(self) -> None:
        self._records: dict[str, list[bool]] = {}

    def record(self, node_id: str, passed: bool) -> None:
        self._records.setdefault(node_id, []).append(passed)

    def is_flaky(self, node_id: str, threshold: float = 0.2) -> bool:
        runs = self._records.get(node_id, [])
        if len(runs) < 3:
            return False
        fail_rate = runs.count(False) / len(runs)
        return threshold < fail_rate < (1.0 - threshold)

    def all_records(self) -> dict[str, list[bool]]:
        return dict(self._records)

    def summary(self) -> dict[str, Any]:
        out = {}
        for nid, runs in self._records.items():
            out[nid] = {
                "runs":      len(runs),
                "passes":    runs.count(True),
                "failures":  runs.count(False),
                "flaky":     self.is_flaky(nid),
            }
        return out
