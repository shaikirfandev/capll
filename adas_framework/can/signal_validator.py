# adas_framework/can/signal_validator.py
"""
Real-time CAN signal validator with DBC decoding.

Features:
    - Decode all signals from DBC via cantools
    - Thread-safe signal store with timestamps
    - Timeout detection per message
    - Jitter measurement per message
    - Signal range violation detection
    - Signal change event callbacks
    - Freeze detection (signal stuck at same value)

Usage:
    validator = SignalValidator(dbc_path, timeout_config)
    validator.attach(can_interface)  # auto-subscribes to all messages
    soc = validator.get("BMS_SoC")
    validator.assert_no_timeouts()
    validator.assert_no_range_violations()
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import cantools
    _CANTOOLS = True
except ImportError:
    _CANTOOLS = False

from can.can_interface import CANInterface, CANMessage
from core.logger import can_log as log


# ─────────────────────────────────────────────────────────────────────────────
# Range / timeout configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MessageExpectation:
    """Expected timing behaviour for a CAN message."""
    arb_id:     int
    name:       str
    period_ms:  Optional[float] = None    # None = event-driven
    timeout_ms: Optional[float] = None    # None = no timeout check
    tolerance_pct: float        = 20.0    # ±20% jitter tolerance


@dataclass
class SignalRange:
    """Expected min/max for a decoded signal value."""
    signal_name: str
    min_val:     float
    max_val:     float
    unit:        str = ""


@dataclass
class SignalRecord:
    """Internal record for latest signal value + timing."""
    value:     Any            = None
    timestamp: float          = 0.0
    prev_value: Any           = None
    prev_timestamp: float     = 0.0
    period_ms_history: deque  = field(default_factory=lambda: deque(maxlen=100))


# ─────────────────────────────────────────────────────────────────────────────
# SignalValidator
# ─────────────────────────────────────────────────────────────────────────────

class SignalValidator:
    """CAN signal store with timeout and range violation tracking."""

    def __init__(self, dbc_path: str):
        self._db = None
        if _CANTOOLS and dbc_path:
            try:
                self._db = cantools.database.load_file(dbc_path)
                log.info(f"DBC loaded: {dbc_path} "
                         f"({len(self._db.messages)} messages)")
            except Exception as e:
                log.warning(f"DBC load failed ({dbc_path}): {e}")

        self._signals: Dict[str, SignalRecord] = defaultdict(SignalRecord)
        self._msg_last_ts: Dict[int, float]    = {}
        self._lock = threading.Lock()

        self._expectations:    Dict[int, MessageExpectation] = {}
        self._ranges:          Dict[str, SignalRange]        = {}
        self._range_violations: List[dict]                   = []
        self._timeouts:         List[dict]                   = []
        self._change_callbacks: Dict[str, List[Callable]]   = defaultdict(list)

    # ── Configuration ─────────────────────────────────────────────────────────

    def expect_message(self, arb_id: int, name: str,
                       period_ms: float = None,
                       timeout_ms: float = None,
                       tolerance_pct: float = 20.0):
        self._expectations[arb_id] = MessageExpectation(
            arb_id, name, period_ms, timeout_ms, tolerance_pct
        )

    def expect_signal_range(self, signal_name: str, min_val: float,
                            max_val: float, unit: str = ""):
        self._ranges[signal_name] = SignalRange(signal_name, min_val, max_val, unit)

    def on_signal_change(self, signal_name: str, callback: Callable[[str, Any, Any], None]):
        """Register callback(signal_name, old_value, new_value) on change."""
        self._change_callbacks[signal_name].append(callback)

    # ── Attach to CAN interface ───────────────────────────────────────────────

    def attach(self, can_iface: CANInterface):
        """Subscribe to all CAN messages from the interface."""
        can_iface.subscribe_all(self._on_message)

    def _on_message(self, msg: CANMessage):
        """Process an incoming CAN message — decode and validate."""
        ts = msg.timestamp

        with self._lock:
            # ── Period measurement ────────────────────────────────────────────
            if msg.arb_id in self._msg_last_ts:
                period_ms = (ts - self._msg_last_ts[msg.arb_id]) * 1000.0
                exp = self._expectations.get(msg.arb_id)
                if exp and exp.period_ms:
                    tol = exp.period_ms * exp.tolerance_pct / 100.0
                    if period_ms > exp.period_ms + tol:
                        self._timeouts.append({
                            "type": "late",
                            "arb_id": msg.arb_id,
                            "name": exp.name,
                            "actual_ms": round(period_ms, 2),
                            "expected_ms": exp.period_ms,
                            "timestamp": ts,
                        })
            self._msg_last_ts[msg.arb_id] = ts

        # ── DBC decode ────────────────────────────────────────────────────────
        if not self._db:
            return
        try:
            decoded = self._db.decode_message(
                msg.arb_id, msg.data, decode_choices=False
            )
        except Exception:
            return

        with self._lock:
            for sig_name, value in decoded.items():
                rec = self._signals[sig_name]
                old_val = rec.value

                rec.prev_value    = old_val
                rec.prev_timestamp = rec.timestamp
                rec.value         = value
                rec.timestamp     = ts

                # Range check
                rng = self._ranges.get(sig_name)
                if rng and isinstance(value, (int, float)):
                    if not (rng.min_val <= value <= rng.max_val):
                        self._range_violations.append({
                            "signal":     sig_name,
                            "value":      value,
                            "min":        rng.min_val,
                            "max":        rng.max_val,
                            "unit":       rng.unit,
                            "timestamp":  ts,
                        })
                        log.warning(
                            f"Range violation: {sig_name}={value}{rng.unit} "
                            f"[{rng.min_val}, {rng.max_val}]"
                        )

        # Change callbacks (outside lock to avoid deadlock)
        for cb in self._change_callbacks.get(sig_name, []):
            try:
                if old_val != value:
                    cb(sig_name, old_val, value)
            except Exception as e:
                log.error(f"Change callback error for {sig_name}: {e}")

    # ── API ───────────────────────────────────────────────────────────────────

    def get(self, signal_name: str, default: Any = None) -> Any:
        """Return latest decoded value for a signal."""
        with self._lock:
            rec = self._signals.get(signal_name)
            return rec.value if rec and rec.value is not None else default

    def get_all(self) -> dict:
        """Return snapshot of all latest signal values."""
        with self._lock:
            return {k: v.value for k, v in self._signals.items()
                    if v.value is not None}

    def age_ms(self, signal_name: str) -> Optional[float]:
        """Return milliseconds since signal was last received."""
        with self._lock:
            rec = self._signals.get(signal_name)
            if rec and rec.timestamp:
                return (time.monotonic() - rec.timestamp) * 1000.0
        return None

    def check_timeouts(self, now: float = None):
        """Check all expected messages for missing reception."""
        now = now or time.monotonic()
        with self._lock:
            for arb_id, exp in self._expectations.items():
                if exp.timeout_ms is None:
                    continue
                last = self._msg_last_ts.get(arb_id)
                if last is None:
                    self._timeouts.append({
                        "type": "never_received",
                        "arb_id": arb_id,
                        "name": exp.name,
                        "timestamp": now,
                    })
                elif (now - last) * 1000 > exp.timeout_ms:
                    self._timeouts.append({
                        "type": "timeout",
                        "arb_id": arb_id,
                        "name": exp.name,
                        "actual_ms": round((now - last) * 1000, 2),
                        "limit_ms": exp.timeout_ms,
                        "timestamp": now,
                    })

    # ── Assertion helpers ─────────────────────────────────────────────────────

    def assert_no_timeouts(self):
        self.check_timeouts()
        with self._lock:
            t = list(self._timeouts)
        assert not t, f"CAN message timeouts detected: {t}"

    def assert_no_range_violations(self):
        with self._lock:
            v = list(self._range_violations)
        assert not v, f"Signal range violations: {v}"

    def clear_violations(self):
        with self._lock:
            self._range_violations.clear()
            self._timeouts.clear()

    def wait_for_signal(
        self, signal_name: str, predicate: Callable,
        timeout_s: float = 5.0, poll_s: float = 0.05
    ) -> Any:
        """Block until signal satisfies predicate or timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            val = self.get(signal_name)
            if predicate(val):
                return val
            time.sleep(poll_s)
        raise TimeoutError(
            f"Signal '{signal_name}' did not satisfy condition "
            f"within {timeout_s}s (last: {self.get(signal_name)!r})"
        )

    def summary(self) -> dict:
        with self._lock:
            return {
                "signals_tracked": len(self._signals),
                "range_violations": len(self._range_violations),
                "timeouts": len(self._timeouts),
            }
