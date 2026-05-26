# adas_framework/core/base_test.py
"""
Base test class for all ADAS test cases.

Provides:
    - Structured test metadata (ASIL level, feature, requirement ID)
    - Automatic log context injection
    - Assertion helpers with rich diagnostic messages
    - Timing measurement utilities
    - Signal snapshot / diff for pre/post comparisons
    - ISO 26262 ASIL enforcement (ASIL C/D blocks @flaky)

Usage:
    class TestACC(ADASBaseTest):
        ASIL  = "ASIL-B"
        FEATURE = "ACC"
        REQ_IDS = ["ACC-SYS-001", "ACC-SYS-002"]

        def test_speed_hold(self, can_bus, signals):
            with self.measure("speed_stabilize"):
                ...
            self.assert_signal_in_range(signals.get("ACC_SetSpeed"), 80, 130)
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Optional

import pytest

from core.logger import get_logger

log = get_logger("base_test")


class ADASBaseTest:
    """
    Base class for all ADAS automated test cases.

    Class attributes (override per test class):
        ASIL    : str — "QM" | "ASIL-A" | "ASIL-B" | "ASIL-C" | "ASIL-D"
        FEATURE : str — ADAS feature name (e.g. "ACC", "AEB")
        REQ_IDS : list[str] — Linked system requirement IDs (for RTM)
        DTC_IDS : list[str] — Expected DTC codes to monitor during test
    """
    ASIL:    str       = "QM"
    FEATURE: str       = "GENERIC"
    REQ_IDS: list[str] = []
    DTC_IDS: list[str] = []

    _timings: dict = {}

    # ── Setup / teardown ──────────────────────────────────────────────────────

    def setup_method(self, method):
        test_name = f"{self.__class__.__name__}::{method.__name__}"
        log.info(
            f"▶ START {test_name}",
            extra={
                "feature": self.FEATURE,
                "asil": self.ASIL,
                "req_ids": self.REQ_IDS,
            }
        )
        self._test_name = test_name
        self._start_ts = time.monotonic()
        self._timings = {}
        self._pre_signals: dict = {}

    def teardown_method(self, method):
        elapsed = time.monotonic() - self._start_ts
        log.info(f"◀ END   {self._test_name}  ({elapsed:.3f}s)")

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_signal_in_range(
        self, value: Any, low: float, high: float,
        signal_name: str = "signal", unit: str = ""
    ):
        """Assert numeric value is within [low, high]."""
        assert value is not None, \
            f"{signal_name}: no data received"
        fval = float(value)
        assert low <= fval <= high, (
            f"{signal_name} = {fval:.4f}{unit} is outside "
            f"expected range [{low}{unit} … {high}{unit}]"
        )

    def assert_signal_equals(
        self, value: Any, expected: Any,
        signal_name: str = "signal", tolerance: float = 0.0
    ):
        """Assert signal equals expected value, optionally within tolerance."""
        assert value is not None, f"{signal_name}: no data received"
        if tolerance > 0:
            assert abs(float(value) - float(expected)) <= tolerance, (
                f"{signal_name} = {value} ≠ {expected} "
                f"(tolerance ±{tolerance})"
            )
        else:
            assert value == expected, f"{signal_name} = {value!r} ≠ {expected!r}"

    def assert_response_time(
        self, elapsed_s: float, max_s: float, label: str = "response"
    ):
        """Assert that an operation completed within max_s."""
        assert elapsed_s <= max_s, (
            f"{label} took {elapsed_s*1000:.1f}ms — "
            f"exceeds limit of {max_s*1000:.0f}ms"
        )

    def assert_no_active_faults(self, signals: dict, fault_signal: str = "FaultActive"):
        """Assert that the fault signal is 0 / not active."""
        val = signals.get(fault_signal, 0)
        assert val == 0, \
            f"Active fault detected: {fault_signal}={val}"

    def assert_state(self, current: Any, expected: Any, state_name: str = "state"):
        """Assert ECU/system state equals expected."""
        assert current == expected, (
            f"{state_name}: expected {expected!r}, got {current!r}"
        )

    # ── Timing context manager ────────────────────────────────────────────────

    @contextmanager
    def measure(self, label: str):
        """
        Context manager to measure execution time of a block.
        Result stored in self._timings[label].

        Usage:
            with self.measure("acc_engage"):
                send_acc_enable()
                wait_for_acc_active()
            self.assert_response_time(self._timings["acc_engage"], max_s=0.5)
        """
        t0 = time.monotonic()
        yield
        elapsed = time.monotonic() - t0
        self._timings[label] = elapsed
        log.debug(f"  ⏱ {label}: {elapsed*1000:.2f}ms")

    # ── Signal snapshot ───────────────────────────────────────────────────────

    def snapshot(self, signals: dict, *keys: str) -> dict:
        """Capture a snapshot of selected signal values."""
        snap = {k: signals.get(k) for k in keys}
        self._pre_signals = snap
        return snap

    def assert_signal_changed(self, before: Any, after: Any, signal_name: str):
        """Assert that a signal value changed between snapshot and now."""
        assert before != after, \
            f"{signal_name} did not change (remained {before!r})"

    def assert_signal_increased(self, before: float, after: float, signal_name: str):
        """Assert signal value increased."""
        assert float(after) > float(before), \
            f"{signal_name} did not increase: {before} → {after}"

    def assert_signal_decreased(self, before: float, after: float, signal_name: str):
        """Assert signal value decreased."""
        assert float(after) < float(before), \
            f"{signal_name} did not decrease: {before} → {after}"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def wait_for_signal(
        self, get_fn, predicate, timeout_s: float = 5.0,
        poll_s: float = 0.05, label: str = "signal"
    ) -> Any:
        """
        Poll until predicate(value) is True or timeout.

        Usage:
            val = self.wait_for_signal(
                lambda: signals.get("AEB_State"), lambda v: v == 3, timeout_s=2.0
            )
        """
        import time as _time
        deadline = _time.monotonic() + timeout_s
        while _time.monotonic() < deadline:
            val = get_fn()
            if predicate(val):
                return val
            _time.sleep(poll_s)
        raise TimeoutError(
            f"Timeout waiting for {label} condition after {timeout_s}s "
            f"(last value: {get_fn()!r})"
        )

    @property
    def is_safety_critical(self) -> bool:
        return self.ASIL in ("ASIL-C", "ASIL-D")
