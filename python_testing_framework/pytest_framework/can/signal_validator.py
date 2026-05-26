"""
pytest_framework/can/signal_validator.py

Enterprise ADAS Framework – CAN Signal Validation Engine
=========================================================
Subscribes to CANInterface, decodes signals via DBC,
provides assertion helpers and value history tracking.
Thread-safe; designed for use inside pytest fixtures.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.logger import get_logger

log = get_logger("signal_validator")


@dataclass
class SignalSample:
    timestamp: float
    value:     Any


@dataclass
class SignalSpec:
    """Min/max/timeout constraints for a signal."""
    name:       str
    min_val:    Optional[float] = None
    max_val:    Optional[float] = None
    timeout_s:  float           = 1.0
    unit:       str             = ""
    scaling:    float           = 1.0
    offset:     float           = 0.0


class SignalValidator:
    """
    Listens to a CANInterface and maintains a rolling history
    of decoded signal values.

    Usage:
        sv = SignalValidator(can_bus, history_depth=200)
        sv.start()
        val = sv.get("ACC_Status")
        sv.assert_received("ACC_Status", timeout_s=2.0)
    """

    def __init__(
        self,
        can_bus: Any,
        history_depth: int = 500,
        decode_fn: Optional[Callable] = None,
    ) -> None:
        self._bus          = can_bus
        self._depth        = history_depth
        self._decode_fn    = decode_fn or (lambda f: can_bus.decode(f))
        self._history:  Dict[str, deque] = {}
        self._lock      = threading.RLock()
        self._running   = False
        self._thread:   Optional[threading.Thread] = None
        self._specs:    Dict[str, SignalSpec] = {}
        self._callbacks: Dict[str, List[Callable]] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(
            target=self._poll_loop, daemon=True, name="signal-poll"
        )
        self._thread.start()
        log.info("[SignalValidator] started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("[SignalValidator] stopped")

    def __enter__(self) -> "SignalValidator":
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()

    # ── Signal access ─────────────────────────────────────────────────────────

    def update(self, name: str, value: Any) -> None:
        """Inject a signal value directly (simulation / test stub)."""
        with self._lock:
            if name not in self._history:
                self._history[name] = deque(maxlen=self._depth)
            sample = SignalSample(timestamp=time.monotonic(), value=value)
            self._history[name].append(sample)
        for cb in self._callbacks.get(name, []):
            try:
                cb(name, value)
            except Exception as exc:
                log.warning(f"[SignalValidator] callback error: {exc!r}")

    def get(self, name: str) -> Optional[Any]:
        """Return the most recent value for a signal, or None."""
        with self._lock:
            h = self._history.get(name)
            if h:
                return h[-1].value
        return None

    def get_history(self, name: str) -> List[SignalSample]:
        with self._lock:
            return list(self._history.get(name, []))

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return {k: v[-1].value for k, v in self._history.items() if v}

    # ── Spec registration ─────────────────────────────────────────────────────

    def register_spec(self, spec: SignalSpec) -> None:
        self._specs[spec.name] = spec

    def on_change(self, name: str, callback: Callable[[str, Any], None]) -> None:
        self._callbacks.setdefault(name, []).append(callback)

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_received(
        self, name: str, timeout_s: float = 2.0
    ) -> Any:
        """Block until signal arrives or timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            val = self.get(name)
            if val is not None:
                return val
            time.sleep(0.02)
        raise AssertionError(
            f"Signal '{name}' not received within {timeout_s}s"
        )

    def assert_value(
        self, name: str, expected: Any, tolerance: float = 0.0
    ) -> None:
        val = self.get(name)
        assert val is not None, f"Signal '{name}' has no value"
        if tolerance > 0:
            assert abs(float(val) - float(expected)) <= tolerance, (
                f"Signal '{name}' = {val}, expected {expected} ±{tolerance}"
            )
        else:
            assert val == expected, (
                f"Signal '{name}' = {val!r}, expected {expected!r}"
            )

    def assert_in_range(
        self, name: str, low: float, high: float
    ) -> None:
        val = self.get(name)
        assert val is not None, f"Signal '{name}' has no value"
        fval = float(val)
        assert low <= fval <= high, (
            f"Signal '{name}' = {fval} outside [{low}, {high}]"
        )

    def assert_stable(
        self, name: str, duration_s: float = 0.5,
        tolerance: float = 0.05
    ) -> None:
        """Assert signal stays within tolerance% of initial value for duration_s."""
        initial = self.get(name)
        assert initial is not None, f"Signal '{name}' has no value"
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            cur = self.get(name)
            if cur is None:
                continue
            if abs(float(cur) - float(initial)) > tolerance * abs(float(initial) + 1e-9):
                raise AssertionError(
                    f"Signal '{name}' not stable: started={initial}, drifted to={cur}"
                )
            time.sleep(0.02)

    def assert_changed_within(
        self, name: str, timeout_s: float = 1.0
    ) -> Any:
        """Assert a signal changes value within timeout_s."""
        initial = self.get(name)
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            cur = self.get(name)
            if cur != initial:
                return cur
            time.sleep(0.02)
        raise AssertionError(
            f"Signal '{name}' did not change from {initial!r} within {timeout_s}s"
        )

    def assert_within_spec(self, name: str) -> None:
        """Assert against a registered SignalSpec."""
        spec = self._specs.get(name)
        assert spec, f"No spec registered for '{name}'"
        val = self.get(name)
        assert val is not None, f"Signal '{name}' has no value"
        fval = float(val) * spec.scaling + spec.offset
        if spec.min_val is not None:
            assert fval >= spec.min_val, (
                f"{name}={fval:.4f} below min {spec.min_val} {spec.unit}"
            )
        if spec.max_val is not None:
            assert fval <= spec.max_val, (
                f"{name}={fval:.4f} above max {spec.max_val} {spec.unit}"
            )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while self._running:
            try:
                frame = self._bus.receive(timeout_s=0.05)
                if frame is None:
                    continue
                signals = self._decode_fn(frame)
                for name, value in signals.items():
                    self.update(name, value)
            except Exception as exc:
                log.debug(f"[SignalValidator] poll error: {exc!r}")
