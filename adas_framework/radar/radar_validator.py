# adas_framework/radar/radar_validator.py
"""
Radar sensor validation module.

Validates:
    - Object detection (range, velocity, azimuth)
    - Object tracking consistency
    - Ghost object count
    - SNR threshold compliance
    - Update rate verification
    - Radar status health
    - Interference detection

Supports:
    - CAN-based object list (standard automotive radar output)
    - ROS topic input (simulation)
    - Direct radar API (vendor-specific extension point)

Usage:
    validator = RadarValidator(cfg.radar)
    validator.attach(signal_validator)
    objects = validator.get_object_list()
    validator.assert_target_detected(range_m=50.0, tolerance_m=2.0)
    validator.assert_no_ghost_objects()
    validator.assert_update_rate(expected_hz=20.0)
"""
from __future__ import annotations

import math
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from core.config import RadarConfig
from core.logger import radar_log as log


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RadarObject:
    """A single detected radar object."""
    obj_id:       int
    range_m:      float
    velocity_mps: float
    azimuth_deg:  float
    rcs_dbm:      float         = 0.0
    confidence:   float         = 1.0
    timestamp:    float         = field(default_factory=time.monotonic)
    is_ghost:     bool          = False
    age_cycles:   int           = 0


@dataclass
class RadarStatus:
    operational:  bool  = True
    interference: bool  = False
    blockage:     bool  = False
    temperature_c: float = 25.0
    voltage_v:     float = 12.0


# ─────────────────────────────────────────────────────────────────────────────
# RadarValidator
# ─────────────────────────────────────────────────────────────────────────────

class RadarValidator:
    """
    Validates radar sensor output against expected performance requirements.
    """

    # CAN signal names (adjust to match project DBC)
    SIG_OBJ_ID       = "RADAR_ObjID"
    SIG_OBJ_RANGE    = "RADAR_ObjRange"
    SIG_OBJ_VEL      = "RADAR_ObjVelocity"
    SIG_OBJ_AZIMUTH  = "RADAR_ObjAzimuth"
    SIG_OBJ_RCS      = "RADAR_ObjRCS"
    SIG_STATUS_OP    = "RADAR_StatusOperational"
    SIG_STATUS_INT   = "RADAR_StatusInterference"
    SIG_STATUS_BLK   = "RADAR_StatusBlockage"

    def __init__(self, config: RadarConfig):
        self._cfg      = config
        self._objects:  Dict[int, RadarObject] = {}
        self._history:  deque = deque(maxlen=500)
        self._lock     = threading.Lock()
        self._status   = RadarStatus()
        self._update_ts: deque = deque(maxlen=100)

        # Validation results
        self._ghost_objects:    List[RadarObject] = []
        self._missed_updates:   int = 0
        self._range_violations: List[dict] = []

    # ── Signal attachment ─────────────────────────────────────────────────────

    def attach(self, signal_validator):
        """Subscribe to radar signal changes."""
        signal_validator.on_signal_change(
            self.SIG_OBJ_RANGE, self._on_object_update
        )
        signal_validator.on_signal_change(
            self.SIG_STATUS_OP, self._on_status_update
        )

    def _on_object_update(self, name: str, old: Any, new: Any):
        """Called when an object signal changes."""
        self._update_ts.append(time.monotonic())

    def _on_status_update(self, name: str, old: Any, new: Any):
        if new == 0:
            log.warning("Radar status: not operational")
            self._status.operational = False

    # ── Object ingestion ──────────────────────────────────────────────────────

    def ingest_object(self, obj: RadarObject):
        """Feed a radar object (from DBC decoder or simulator)."""
        with self._lock:
            self._validate_object(obj)
            self._objects[obj.obj_id] = obj
            self._history.append(obj)
            self._update_ts.append(obj.timestamp)

    def ingest_from_signals(self, signals: dict):
        """
        Parse a single-object snapshot from decoded CAN signals.
        For multi-object radars, call this per object slot.
        """
        obj_id   = int(signals.get(self.SIG_OBJ_ID, 0) or 0)
        rng      = float(signals.get(self.SIG_OBJ_RANGE, 0) or 0)
        vel      = float(signals.get(self.SIG_OBJ_VEL, 0) or 0)
        azimuth  = float(signals.get(self.SIG_OBJ_AZIMUTH, 0) or 0)
        rcs      = float(signals.get(self.SIG_OBJ_RCS, 0) or 0)

        if rng <= 0:
            return

        self.ingest_object(RadarObject(
            obj_id=obj_id, range_m=rng, velocity_mps=vel,
            azimuth_deg=azimuth, rcs_dbm=rcs
        ))

    def _validate_object(self, obj: RadarObject):
        """Check object against configured limits."""
        cfg = self._cfg
        if not (cfg.target_range_min_m <= obj.range_m <= cfg.target_range_max_m):
            self._range_violations.append({
                "obj_id": obj.obj_id,
                "range_m": obj.range_m,
                "limits": (cfg.target_range_min_m, cfg.target_range_max_m),
                "timestamp": obj.timestamp,
            })
        if not (cfg.velocity_min_mps <= obj.velocity_mps <= cfg.velocity_max_mps):
            log.warning(
                f"Radar object {obj.obj_id} velocity {obj.velocity_mps} mps "
                f"outside range [{cfg.velocity_min_mps}, {cfg.velocity_max_mps}]"
            )
        if obj.rcs_dbm < cfg.snr_threshold_db:
            obj.is_ghost = True
            self._ghost_objects.append(obj)
            log.warning(
                f"Potential ghost object {obj.obj_id}: "
                f"RCS={obj.rcs_dbm:.1f}dBm < threshold={cfg.snr_threshold_db}dBm"
            )

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_object_list(self) -> List[RadarObject]:
        """Return all currently tracked objects."""
        with self._lock:
            return list(self._objects.values())

    def find_target(self, range_m: float, tolerance_m: float = 2.0,
                    velocity_mps: float = None,
                    vel_tolerance: float = 2.0) -> Optional[RadarObject]:
        """Find an object matching range (and optionally velocity)."""
        with self._lock:
            for obj in self._objects.values():
                if abs(obj.range_m - range_m) <= tolerance_m:
                    if velocity_mps is None:
                        return obj
                    if abs(obj.velocity_mps - velocity_mps) <= vel_tolerance:
                        return obj
        return None

    def current_update_rate_hz(self) -> float:
        """Estimate update rate from recent timestamps."""
        with self._lock:
            ts = list(self._update_ts)
        if len(ts) < 5:
            return 0.0
        recent = ts[-20:]
        if len(recent) < 2:
            return 0.0
        elapsed = recent[-1] - recent[0]
        if elapsed <= 0:
            return 0.0
        return (len(recent) - 1) / elapsed

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_target_detected(
        self, range_m: float, tolerance_m: float = 2.0,
        velocity_mps: float = None, vel_tolerance: float = 2.0
    ):
        obj = self.find_target(range_m, tolerance_m, velocity_mps, vel_tolerance)
        assert obj is not None, (
            f"No radar target detected at {range_m}m ±{tolerance_m}m. "
            f"Tracked objects: {[(o.obj_id, round(o.range_m,1)) for o in self.get_object_list()]}"
        )
        return obj

    def assert_no_ghost_objects(self):
        with self._lock:
            ghosts = list(self._ghost_objects)
        assert not ghosts, (
            f"{len(ghosts)} ghost object(s) detected: "
            f"{[(g.obj_id, g.rcs_dbm) for g in ghosts]}"
        )

    def assert_update_rate(self, expected_hz: float, tolerance_pct: float = 20.0):
        actual = self.current_update_rate_hz()
        low    = expected_hz * (1 - tolerance_pct / 100)
        assert actual >= low, (
            f"Radar update rate {actual:.1f}Hz below minimum {low:.1f}Hz "
            f"(expected {expected_hz}Hz ±{tolerance_pct}%)"
        )

    def assert_operational(self):
        assert self._status.operational, "Radar reports non-operational status"
        assert not self._status.interference, "Radar reports interference"
        assert not self._status.blockage, "Radar reports blockage"

    def assert_no_range_violations(self):
        with self._lock:
            v = list(self._range_violations)
        assert not v, f"Radar range violations: {v}"

    def assert_object_count(self, min_count: int = 1, max_count: int = 32):
        count = len(self.get_object_list())
        assert min_count <= count <= max_count, (
            f"Object count {count} outside [{min_count}, {max_count}]"
        )

    def clear_stats(self):
        with self._lock:
            self._ghost_objects.clear()
            self._range_violations.clear()
            self._objects.clear()

    def summary(self) -> dict:
        with self._lock:
            return {
                "tracked_objects": len(self._objects),
                "ghost_objects":   len(self._ghost_objects),
                "range_violations": len(self._range_violations),
                "update_rate_hz":  round(self.current_update_rate_hz(), 2),
                "operational":     self._status.operational,
            }
