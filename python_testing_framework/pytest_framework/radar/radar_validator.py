"""
pytest_framework/radar/radar_validator.py

Enterprise ADAS Framework – Radar Object Validation
=====================================================
Thread-safe radar object ingestion, tracking, and assertion.
Supports real radar via CAN signal feed or simulated objects.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.logger import get_logger

log = get_logger("radar_validator")


@dataclass
class RadarObject:
    obj_id:      int
    range_m:     float
    velocity_mps: float
    azimuth_deg:  float
    rcs_dbm:      float
    confidence:   float = 1.0
    is_ghost:     bool  = False
    timestamp:    float = field(default_factory=time.monotonic)


@dataclass
class RadarStatus:
    operational:  bool  = True
    update_rate_hz: float = 0.0
    object_count: int   = 0
    last_update:  float = 0.0


class RadarValidator:
    """
    Validates radar outputs for ADAS features.

    Usage:
        rv = RadarValidator(cfg.radar)
        rv.ingest_object(RadarObject(...))
        rv.assert_target_detected(range_m=50.0, tolerance_m=5.0)
    """

    def __init__(self, cfg: Optional[object] = None) -> None:
        self._cfg         = cfg
        self._objects:    List[RadarObject] = []
        self._timestamps: deque = deque(maxlen=50)
        self._lock        = threading.Lock()
        self._status      = RadarStatus()

        if cfg:
            self._range_min  = getattr(cfg, "range_min_m",  0.5)
            self._range_max  = getattr(cfg, "range_max_m",  250.0)
            self._vel_min    = getattr(cfg, "velocity_min_mps", -80.0)
            self._vel_max    = getattr(cfg, "velocity_max_mps",  80.0)
            self._snr_thresh = getattr(cfg, "snr_threshold_db", 5.0)
            self._expected_hz = getattr(cfg, "update_rate_hz",  20.0)
        else:
            self._range_min   = 0.5
            self._range_max   = 250.0
            self._vel_min     = -80.0
            self._vel_max     =  80.0
            self._snr_thresh  = 5.0
            self._expected_hz = 20.0

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest_object(self, obj: RadarObject) -> None:
        obj.is_ghost = self._detect_ghost(obj)
        with self._lock:
            self._objects.append(obj)
            self._timestamps.append(time.monotonic())
            self._status.object_count = len(self._objects)
            self._status.last_update  = time.monotonic()

    def ingest_from_signals(self, signals: Dict[str, float]) -> None:
        obj = RadarObject(
            obj_id      = int(signals.get("Radar_ObjID", 0)),
            range_m     = float(signals.get("Radar_Range_m", 0)),
            velocity_mps = float(signals.get("Radar_Velocity_mps", 0)),
            azimuth_deg  = float(signals.get("Radar_Azimuth_deg", 0)),
            rcs_dbm      = float(signals.get("Radar_RCS_dBm", 0)),
            confidence   = float(signals.get("Radar_Confidence", 1.0)),
        )
        self.ingest_object(obj)

    def clear(self) -> None:
        with self._lock:
            self._objects.clear()
            self._timestamps.clear()

    # ── Queries ───────────────────────────────────────────────────────────────

    def find_target(
        self, range_m: float, tolerance_m: float = 5.0
    ) -> Optional[RadarObject]:
        with self._lock:
            for obj in reversed(self._objects):
                if abs(obj.range_m - range_m) <= tolerance_m:
                    return obj
        return None

    def current_update_rate_hz(self) -> float:
        with self._lock:
            ts = list(self._timestamps)
        if len(ts) < 2:
            return 0.0
        intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
        avg_interval = sum(intervals) / len(intervals)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    def ghost_objects(self) -> List[RadarObject]:
        with self._lock:
            return [o for o in self._objects if o.is_ghost]

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_target_detected(
        self, range_m: float, tolerance_m: float = 5.0,
        timeout_s: float = 2.0
    ) -> RadarObject:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            obj = self.find_target(range_m, tolerance_m)
            if obj:
                return obj
            time.sleep(0.05)
        raise AssertionError(
            f"No radar target detected at {range_m}m ±{tolerance_m}m "
            f"within {timeout_s}s"
        )

    def assert_no_ghost_objects(self) -> None:
        ghosts = self.ghost_objects()
        assert not ghosts, (
            f"Ghost radar objects detected: "
            f"{[(o.obj_id, o.range_m, o.rcs_dbm) for o in ghosts]}"
        )

    def assert_update_rate(
        self, min_hz: Optional[float] = None, max_hz: Optional[float] = None
    ) -> None:
        rate = self.current_update_rate_hz()
        expected = self._expected_hz
        _min = min_hz if min_hz is not None else expected * 0.8
        _max = max_hz if max_hz is not None else expected * 1.2
        assert _min <= rate <= _max, (
            f"Radar update rate {rate:.1f}Hz outside [{_min:.1f}, {_max:.1f}]Hz"
        )

    def assert_operational(self) -> None:
        assert self._status.operational, "Radar not operational"
        assert self._status.last_update > 0, "Radar never produced an update"

    def assert_no_range_violations(self) -> None:
        with self._lock:
            bad = [
                o for o in self._objects
                if not (self._range_min <= o.range_m <= self._range_max)
            ]
        assert not bad, (
            f"Radar objects outside range spec [{self._range_min}m, {self._range_max}m]: "
            f"{[(o.obj_id, o.range_m) for o in bad]}"
        )

    def assert_object_count(self, min_count: int, max_count: int) -> None:
        with self._lock:
            count = len(self._objects)
        assert min_count <= count <= max_count, (
            f"Radar object count {count} outside [{min_count}, {max_count}]"
        )

    def assert_velocity_in_range(
        self, obj_id: int, min_mps: float, max_mps: float
    ) -> None:
        with self._lock:
            matches = [o for o in self._objects if o.obj_id == obj_id]
        assert matches, f"No radar object with ID {obj_id}"
        obj = matches[-1]
        assert min_mps <= obj.velocity_mps <= max_mps, (
            f"Radar obj {obj_id} velocity {obj.velocity_mps:.2f}m/s "
            f"outside [{min_mps}, {max_mps}]"
        )

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        with self._lock:
            return {
                "object_count":    len(self._objects),
                "ghost_count":     len(self.ghost_objects()),
                "update_rate_hz":  self.current_update_rate_hz(),
                "operational":     self._status.operational,
            }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _detect_ghost(self, obj: RadarObject) -> bool:
        return obj.rcs_dbm < self._snr_thresh and obj.confidence < 0.5
