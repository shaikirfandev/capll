"""
pytest_framework/core/base_test.py

Enterprise ADAS Framework – Base Test Class
============================================
Provides:
  - ASIL / feature / requirement metadata
  - Structured setup/teardown logging
  - pytest-native assertion helpers
  - Timing measurement context manager
  - Signal snapshot & diff utilities
  - ISO 26262 ASIL enforcement hooks
  - Allure step integration
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

import pytest

from core.logger import get_logger

log = get_logger("base_test")

# Optional allure import – silently absent in lean CI images
try:
    import allure
    _ALLURE = True
except ImportError:
    _ALLURE = False


class ADASBaseTest:
    """
    Base class for all ADAS automated test cases.

    Override class attributes per feature:
        ASIL     : "QM" | "A" | "B" | "C" | "D"
        FEATURE  : ADAS feature name  (e.g. "ACC", "AEB")
        REQ_IDS  : Linked system requirement IDs (DOORS / Polarion RTM)
        DTC_IDS  : DTC codes to monitor during the test
    """
    ASIL:    str       = "QM"
    FEATURE: str       = "GENERIC"
    REQ_IDS: list[str] = []
    DTC_IDS: list[str] = []

    _timings:      dict = {}
    _pre_signals:  dict = {}
    _test_name:    str  = ""
    _start_ts:     float = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def setup_method(self, method: Any) -> None:
        self._test_name = f"{self.__class__.__name__}::{method.__name__}"
        self._start_ts  = time.monotonic()
        self._timings   = {}
        self._pre_signals = {}
        log.info(
            f"▶ START {self._test_name}",
            extra={"feature": self.FEATURE, "asil": self.ASIL,
                   "req_ids": self.REQ_IDS},
        )
        if _ALLURE:
            allure.dynamic.label("asil",    self.ASIL)
            allure.dynamic.label("feature", self.FEATURE)
            for r in self.REQ_IDS:
                allure.dynamic.link(r, name=r)

    def teardown_method(self, method: Any) -> None:
        elapsed = time.monotonic() - self._start_ts
        log.info(f"◀ END   {self._test_name}  ({elapsed:.3f}s)")

    # ── Timing ────────────────────────────────────────────────────────────────

    @contextmanager
    def measure(self, label: str) -> Generator[None, None, None]:
        """Context manager that records elapsed time into self._timings."""
        t0 = time.monotonic()
        yield
        self._timings[label] = (time.monotonic() - t0) * 1000  # ms
        log.debug(f"⏱  {label} = {self._timings[label]:.1f}ms")

    def assert_response_time(
        self, label: str, max_ms: float
    ) -> None:
        elapsed = self._timings.get(label)
        assert elapsed is not None, f"No timing recorded for '{label}'"
        assert elapsed <= max_ms, (
            f"{label} took {elapsed:.1f}ms — exceeds limit {max_ms:.0f}ms"
        )

    # ── Signal assertions ─────────────────────────────────────────────────────

    @staticmethod
    def assert_in_range(
        value: Any, low: float, high: float, label: str = "value"
    ) -> None:
        """Assert low <= float(value) <= high."""
        assert value is not None, f"{label}: no data received"
        fval = float(value)
        assert low <= fval <= high, (
            f"{label} = {fval:.4f} outside expected range [{low}, {high}]"
        )

    @staticmethod
    def assert_approx(
        value: Any, expected: float, abs_tol: float = 0.0,
        rel_tol: float = 1e-6, label: str = "value"
    ) -> None:
        """Assert value ≈ expected within tolerance using pytest.approx."""
        assert value is not None, f"{label}: no data received"
        assert float(value) == pytest.approx(expected, abs=abs_tol, rel=rel_tol), (
            f"{label} = {value} ≠ {expected} (abs_tol={abs_tol}, rel_tol={rel_tol})"
        )

    @staticmethod
    def assert_bit_set(value: int, bit: int, label: str = "value") -> None:
        assert (int(value) >> bit) & 1, f"{label} bit {bit} not set (value=0x{value:X})"

    @staticmethod
    def assert_bit_clear(value: int, bit: int, label: str = "value") -> None:
        assert not ((int(value) >> bit) & 1), \
            f"{label} bit {bit} unexpectedly set (value=0x{value:X})"

    @staticmethod
    def assert_no_active_faults(signals: dict, fault_signal: str = "FaultActive") -> None:
        val = signals.get(fault_signal, 0)
        assert int(val) == 0, f"Active fault: {fault_signal}={val}"

    # ── Snapshot helpers ──────────────────────────────────────────────────────

    def snapshot(self, signals: dict, keys: list[str]) -> None:
        """Capture pre-condition signal values for later diff."""
        self._pre_signals = {k: signals.get(k) for k in keys}

    def assert_changed(self, signals: dict, key: str) -> None:
        """Assert a signal changed since snapshot()."""
        before = self._pre_signals.get(key)
        after  = signals.get(key)
        assert before != after, (
            f"{key} did not change: before={before}, after={after}"
        )

    def assert_unchanged(self, signals: dict, key: str) -> None:
        """Assert a signal did NOT change since snapshot()."""
        before = self._pre_signals.get(key)
        after  = signals.get(key)
        assert before == after, (
            f"{key} unexpectedly changed: {before} → {after}"
        )

    # ── ASIL enforcement ──────────────────────────────────────────────────────

    def skip_if_no_hil(self, hil_enabled: bool, reason: str = "") -> None:
        if not hil_enabled:
            pytest.skip(reason or "HIL bench not available — skipping hardware test")

    def xfail_asil_d_without_hil(self, hil_enabled: bool) -> None:
        if self.ASIL == "D" and not hil_enabled:
            pytest.xfail("ASIL D test requires HIL bench for full validation")
