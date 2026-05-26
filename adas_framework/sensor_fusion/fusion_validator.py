# adas_framework/sensor_fusion/fusion_validator.py
"""
Sensor Fusion validation module.

Validates:
    - Timestamp synchronization between radar / camera / LiDAR
    - Object fusion consistency (same physical object → same track ID)
    - Fused object position accuracy
    - Sensor latency per channel
    - Tracking continuity (no spurious drops)
    - Failover behaviour (sensor degradation → graceful degrade)

Usage:
    fusion = FusionValidator(cfg)
    fusion.ingest_radar_objects(radar_list)
    fusion.ingest_camera_objects(camera_list)
    fusion.assert_timestamp_sync(max_skew_ms=10.0)
    fusion.assert_object_fused(range_m=50.0)
    fusion.assert_tracking_continuity(track_id=5, min_cycles=20)
"""
from __future__ import annotations

import math
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.logger import fusion_log as log


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FusedObject:
    """An object produced by the sensor fusion algorithm."""
    track_id:     int
    pos_x_m:      float
    pos_y_m:      float
    velocity_mps: float
    heading_deg:  float
    confidence:   float
    source:       str       # "radar", "camera", "lidar", "fused"
    timestamp:    float = field(default_factory=time.monotonic)


@dataclass
class SensorTimestamp:
    """Timestamp record from a specific sensor channel."""
    sensor:    str      # "radar", "camera", "lidar"
    timestamp: float
    seq:       int = 0


# ─────────────────────────────────────────────────────────────────────────────
# FusionValidator
# ─────────────────────────────────────────────────────────────────────────────

class FusionValidator:
    """Validates sensor fusion output quality and consistency."""

    LATENCY_WINDOW = 50  # samples

    def __init__(self):
        self._lock     = threading.Lock()
        self._fused:   Dict[int, List[FusedObject]] = defaultdict(list)
        self._latest:  Dict[int, FusedObject]       = {}
        self._ts_log:  Dict[str, deque]             = {
            "radar":  deque(maxlen=200),
            "camera": deque(maxlen=200),
            "lidar":  deque(maxlen=200),
            "fusion": deque(maxlen=200),
        }
        self._tracking_gaps: List[dict] = []
        self._latencies:     Dict[str, List[float]] = defaultdict(list)
        self._failover_log:  List[dict] = []

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, obj: FusedObject):
        """Feed a fused or single-sensor object."""
        with self._lock:
            prev = self._latest.get(obj.track_id)
            self._fused[obj.track_id].append(obj)
            self._latest[obj.track_id] = obj
            self._ts_log[obj.source].append(obj.timestamp)

            # Continuity check
            if prev is not None:
                gap_ms = (obj.timestamp - prev.timestamp) * 1000.0
                expected_ms = 50.0  # 20Hz
                if gap_ms > expected_ms * 3:
                    self._tracking_gaps.append({
                        "track_id": obj.track_id,
                        "gap_ms":   round(gap_ms, 2),
                        "ts":       obj.timestamp,
                    })
                    log.warning(
                        f"Tracking gap on ID {obj.track_id}: "
                        f"{gap_ms:.1f}ms (expected ≤ {expected_ms*3:.0f}ms)"
                    )

    def record_timestamp(self, sensor: str, ts: float = None, seq: int = 0):
        """Record a sensor frame timestamp for synchronization analysis."""
        ts = ts or time.monotonic()
        with self._lock:
            if sensor in self._ts_log:
                self._ts_log[sensor].append(ts)

    def record_latency(self, sensor: str, latency_ms: float):
        """Record measured sensor-to-fusion latency."""
        with self._lock:
            self._latencies[sensor].append(latency_ms)

    # ── Timestamp synchronization ─────────────────────────────────────────────

    def timestamp_skew_ms(self, sensor_a: str, sensor_b: str) -> float:
        """
        Calculate the mean timestamp skew between two sensor channels.
        Positive = sensor_a is ahead of sensor_b.
        """
        with self._lock:
            ts_a = list(self._ts_log.get(sensor_a, []))
            ts_b = list(self._ts_log.get(sensor_b, []))

        if not ts_a or not ts_b:
            return float("nan")

        # Compare latest N timestamps
        n = min(len(ts_a), len(ts_b), 20)
        skews = [ts_a[-n+i] - ts_b[-n+i] for i in range(n)]
        return sum(skews) / len(skews) * 1000.0  # ms

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_latest(self, track_id: int) -> Optional[FusedObject]:
        with self._lock:
            return self._latest.get(track_id)

    def get_all_tracks(self) -> List[FusedObject]:
        with self._lock:
            return list(self._latest.values())

    def find_object_near(self, x_m: float, y_m: float,
                          tolerance_m: float = 3.0) -> Optional[FusedObject]:
        """Find the nearest tracked object to a given position."""
        with self._lock:
            objs = list(self._latest.values())
        best = None
        best_dist = float("inf")
        for obj in objs:
            dist = math.hypot(obj.pos_x_m - x_m, obj.pos_y_m - y_m)
            if dist < tolerance_m and dist < best_dist:
                best_dist = dist
                best = obj
        return best

    def latency_stats(self, sensor: str) -> dict:
        with self._lock:
            lats = list(self._latencies.get(sensor, []))
        if not lats:
            return {"mean_ms": 0, "max_ms": 0, "min_ms": 0, "p95_ms": 0}
        return {
            "mean_ms": round(sum(lats) / len(lats), 2),
            "max_ms":  round(max(lats), 2),
            "min_ms":  round(min(lats), 2),
            "p95_ms":  round(sorted(lats)[int(len(lats) * 0.95)], 2),
        }

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_timestamp_sync(
        self, sensor_a: str = "radar", sensor_b: str = "camera",
        max_skew_ms: float = 10.0
    ):
        skew = self.timestamp_skew_ms(sensor_a, sensor_b)
        if math.isnan(skew):
            raise AssertionError(
                f"Cannot compute skew — insufficient data for "
                f"{sensor_a} or {sensor_b}"
            )
        assert abs(skew) <= max_skew_ms, (
            f"Timestamp skew {sensor_a}↔{sensor_b}: "
            f"{skew:.2f}ms exceeds limit {max_skew_ms}ms"
        )

    def assert_object_fused(
        self, range_m: float, tolerance_m: float = 3.0
    ):
        """Assert a fused object exists at approximately (range_m, 0)."""
        obj = self.find_object_near(range_m, 0.0, tolerance_m)
        assert obj is not None, (
            f"No fused object found at range {range_m}m ±{tolerance_m}m. "
            f"Active tracks: "
            f"{[(o.track_id, round(o.pos_x_m,1)) for o in self.get_all_tracks()]}"
        )
        return obj

    def assert_tracking_continuity(
        self, track_id: int, min_cycles: int = 20
    ):
        with self._lock:
            history = list(self._fused.get(track_id, []))
        assert len(history) >= min_cycles, (
            f"Track {track_id} has only {len(history)} cycles "
            f"(minimum required: {min_cycles})"
        )
        # Check for gaps
        gaps_for_track = [
            g for g in self._tracking_gaps if g["track_id"] == track_id
        ]
        assert not gaps_for_track, (
            f"Track {track_id} had {len(gaps_for_track)} tracking gap(s): "
            f"{gaps_for_track}"
        )

    def assert_latency(self, sensor: str, max_latency_ms: float):
        stats = self.latency_stats(sensor)
        assert stats["p95_ms"] <= max_latency_ms, (
            f"{sensor} p95 latency {stats['p95_ms']}ms exceeds "
            f"limit {max_latency_ms}ms (max={stats['max_ms']}ms)"
        )

    def assert_no_tracking_gaps(self):
        with self._lock:
            gaps = list(self._tracking_gaps)
        assert not gaps, f"Tracking gaps detected: {gaps}"

    def summary(self) -> dict:
        with self._lock:
            return {
                "active_tracks":    len(self._latest),
                "tracking_gaps":    len(self._tracking_gaps),
                "radar_updates":    len(self._ts_log["radar"]),
                "camera_updates":   len(self._ts_log["camera"]),
                "lidar_updates":    len(self._ts_log["lidar"]),
            }
