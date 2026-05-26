"""
pytest_framework/sensor_fusion/fusion_validator.py

Enterprise ADAS Framework – Multi-Sensor Fusion Validation
============================================================
Validates: object fusion consistency, timestamp synchronisation,
tracking continuity, latency, and failover behaviour.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from core.logger import get_logger

log = get_logger("fusion_validator")


@dataclass
class FusedObject:
    track_id:    int
    pos_x_m:    float
    pos_y_m:    float
    velocity_mps: float
    heading_deg:  float
    confidence:  float
    source:      str    # "radar" | "camera" | "lidar" | "fused"
    timestamp:   float  = field(default_factory=time.monotonic)


class FusionValidator:
    """
    Validates multi-sensor fusion outputs.

    Usage:
        fv = FusionValidator(expected_sources=["radar","camera"])
        fv.ingest(FusedObject(...))
        fv.assert_object_fused(track_id=10)
        fv.assert_timestamp_sync("radar", "camera", max_skew_ms=20.0)
    """

    def __init__(
        self,
        expected_sources: Optional[List[str]] = None,
        tracking_period_s: float = 0.1,
    ) -> None:
        self._sources   = expected_sources or ["radar", "camera", "lidar"]
        self._period    = tracking_period_s
        self._objects:  List[FusedObject] = []
        self._ts_map:   Dict[str, float]  = {}   # sensor → last timestamp
        self._latencies: Dict[str, List[float]] = {}
        self._track_ids: Dict[int, List[float]] = {}  # id → update timestamps
        self._lock      = threading.Lock()

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, obj: FusedObject) -> None:
        with self._lock:
            self._objects.append(obj)
            self._track_ids.setdefault(obj.track_id, []).append(obj.timestamp)

    def record_timestamp(self, sensor: str, ts: float) -> None:
        with self._lock:
            self._ts_map[sensor] = ts

    def record_latency(self, sensor: str, latency_ms: float) -> None:
        with self._lock:
            self._latencies.setdefault(sensor, []).append(latency_ms)

    def clear(self) -> None:
        with self._lock:
            self._objects.clear()
            self._track_ids.clear()
            self._ts_map.clear()
            self._latencies.clear()

    # ── Queries ───────────────────────────────────────────────────────────────

    def find_object_near(
        self, x_m: float, y_m: float, tolerance_m: float = 3.0
    ) -> Optional[FusedObject]:
        with self._lock:
            for obj in reversed(self._objects):
                dist = ((obj.pos_x_m - x_m)**2 + (obj.pos_y_m - y_m)**2) ** 0.5
                if dist <= tolerance_m:
                    return obj
        return None

    def timestamp_skew_ms(self, sensor_a: str, sensor_b: str) -> float:
        with self._lock:
            ta = self._ts_map.get(sensor_a, 0.0)
            tb = self._ts_map.get(sensor_b, 0.0)
        return abs(ta - tb) * 1000.0

    def latency_stats(self, sensor: str) -> dict:
        lats = self._latencies.get(sensor, [])
        if not lats:
            return {"min": 0, "max": 0, "mean": 0, "count": 0}
        return {
            "min":   min(lats),
            "max":   max(lats),
            "mean":  sum(lats) / len(lats),
            "count": len(lats),
        }

    def tracking_gaps(
        self, track_id: int, max_gap_s: Optional[float] = None
    ) -> List[float]:
        limit = max_gap_s or (self._period * 3)
        ts_list = self._track_ids.get(track_id, [])
        return [
            ts_list[i+1] - ts_list[i]
            for i in range(len(ts_list) - 1)
            if ts_list[i+1] - ts_list[i] > limit
        ]

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_timestamp_sync(
        self, sensor_a: str, sensor_b: str,
        max_skew_ms: float = 20.0,
    ) -> None:
        skew = self.timestamp_skew_ms(sensor_a, sensor_b)
        assert skew <= max_skew_ms, (
            f"Timestamp skew {sensor_a}↔{sensor_b}: {skew:.1f}ms > {max_skew_ms}ms"
        )

    def assert_object_fused(
        self, track_id: int, min_sources: int = 1
    ) -> FusedObject:
        with self._lock:
            matches = [o for o in self._objects if o.track_id == track_id]
        assert matches, f"Track ID {track_id} not present in fusion output"
        sources = {o.source for o in matches}
        assert len(sources) >= min_sources, (
            f"Track {track_id} seen from only {sources} — need ≥ {min_sources} sources"
        )
        return matches[-1]

    def assert_tracking_continuity(
        self, track_id: int, min_updates: int = 5
    ) -> None:
        ts = self._track_ids.get(track_id, [])
        assert len(ts) >= min_updates, (
            f"Track {track_id} has only {len(ts)} updates, need ≥ {min_updates}"
        )

    def assert_latency(
        self, sensor: str, max_mean_ms: float, max_p99_ms: float = 0.0
    ) -> None:
        stats = self.latency_stats(sensor)
        assert stats["count"] > 0, f"No latency data for sensor '{sensor}'"
        assert stats["mean"] <= max_mean_ms, (
            f"{sensor} mean latency {stats['mean']:.1f}ms > {max_mean_ms}ms"
        )
        if max_p99_ms > 0:
            lats = sorted(self._latencies.get(sensor, []))
            p99  = lats[int(len(lats) * 0.99)] if lats else 0.0
            assert p99 <= max_p99_ms, (
                f"{sensor} p99 latency {p99:.1f}ms > {max_p99_ms}ms"
            )

    def assert_no_tracking_gaps(
        self, track_id: int, max_gap_s: Optional[float] = None
    ) -> None:
        gaps = self.tracking_gaps(track_id, max_gap_s)
        assert not gaps, (
            f"Track {track_id} has {len(gaps)} tracking gaps: "
            f"{[f'{g*1000:.0f}ms' for g in gaps]}"
        )

    def assert_confidence_above(
        self, track_id: int, min_confidence: float = 0.8
    ) -> None:
        with self._lock:
            obj = next(
                (o for o in reversed(self._objects) if o.track_id == track_id), None
            )
        assert obj is not None, f"Track {track_id} not found"
        assert obj.confidence >= min_confidence, (
            f"Track {track_id} confidence {obj.confidence:.2f} < {min_confidence}"
        )

    def assert_fusion_sources_present(
        self, required: Optional[List[str]] = None
    ) -> None:
        needed = required or self._sources
        with self._lock:
            seen = {o.source for o in self._objects}
        missing = set(needed) - seen
        assert not missing, (
            f"Fusion missing data from: {missing} "
            f"(seen: {seen})"
        )
