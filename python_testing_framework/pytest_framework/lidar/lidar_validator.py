"""
pytest_framework/lidar/lidar_validator.py

Enterprise ADAS Framework – LiDAR Point Cloud Validation
=========================================================
UDP listener for Velodyne/Ouster/HESAI point cloud packets.
Validates: point count, range, update rate, obstacle detection.
Headless stub when no LiDAR hardware available.
"""
from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

from core.logger import get_logger

log = get_logger("lidar_validator")

try:
    import numpy as np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False


@dataclass
class LiDARPoint:
    x:         float
    y:         float
    z:         float
    intensity: float = 0.0

    @property
    def range_m(self) -> float:
        if _HAS_NP:
            import numpy as np
            return float(np.sqrt(self.x**2 + self.y**2 + self.z**2))
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5


@dataclass
class PointCloud:
    points:    List[LiDARPoint] = field(default_factory=list)
    timestamp: float            = field(default_factory=time.monotonic)

    @property
    def count(self) -> int:
        return len(self.points)

    def max_range_m(self) -> float:
        if not self.points:
            return 0.0
        return max(p.range_m for p in self.points)

    def min_range_m(self) -> float:
        if not self.points:
            return 0.0
        return min(p.range_m for p in self.points)


class LiDARValidator:
    """
    UDP-based LiDAR point cloud validator.

    Usage:
        with LiDARValidator(host="127.0.0.1", port=2368) as lidar:
            cloud = lidar.get_latest_cloud(timeout_s=2.0)
            lidar.assert_point_count(cloud, min_points=500)
    """

    VELODYNE_PACKET_SIZE = 1206  # bytes per Velodyne UDP data packet

    def __init__(
        self,
        host:   str   = "127.0.0.1",
        port:   int   = 2368,
        cfg:    Optional[object] = None,
    ) -> None:
        self._host      = host
        self._port      = port
        self._cfg       = cfg
        self._sock:     Optional[socket.socket] = None
        self._lock      = threading.Lock()
        self._latest:   Optional[PointCloud] = None
        self._thread:   Optional[threading.Thread] = None
        self._stop      = threading.Event()
        self._update_ts: List[float] = []

        if cfg:
            self._max_range_m  = getattr(cfg, "range_max_m",  100.0)
            self._min_points   = getattr(cfg, "min_points",   1000)
            self._expected_hz  = getattr(cfg, "update_rate_hz", 10.0)
        else:
            self._max_range_m  = 100.0
            self._min_points   = 1000
            self._expected_hz  = 10.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> "LiDARValidator":
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self._host, self._port))
            self._sock.settimeout(0.5)
            self._thread = threading.Thread(
                target=self._rx_loop, daemon=True, name="lidar-rx"
            )
            self._thread.start()
            log.info(f"[LiDAR] listening on {self._host}:{self._port}")
        except OSError:
            log.warning("[LiDAR] UDP bind failed — using stub mode")
        return self

    def disconnect(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._sock:
            self._sock.close()
        log.info("[LiDAR] disconnected")

    def __enter__(self) -> "LiDARValidator":
        return self.connect()

    def __exit__(self, *_: object) -> None:
        self.disconnect()

    # ── Point cloud access ────────────────────────────────────────────────────

    def ingest_cloud(self, cloud: PointCloud) -> None:
        """Inject a point cloud directly (simulation / stub)."""
        with self._lock:
            self._latest = cloud
            self._update_ts.append(time.monotonic())
            if len(self._update_ts) > 50:
                self._update_ts = self._update_ts[-50:]

    def get_latest_cloud(self, timeout_s: float = 2.0) -> Optional[PointCloud]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._lock:
                if self._latest is not None:
                    return self._latest
            time.sleep(0.05)
        return None

    def current_update_rate_hz(self) -> float:
        with self._lock:
            ts = list(self._update_ts)
        if len(ts) < 2:
            return 0.0
        intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
        avg = sum(intervals) / len(intervals)
        return 1.0 / avg if avg > 0 else 0.0

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_point_count(
        self, cloud: PointCloud,
        min_points: Optional[int] = None,
    ) -> None:
        min_p = min_points or self._min_points
        assert cloud is not None, "LiDAR: no point cloud received"
        assert cloud.count >= min_p, (
            f"LiDAR: only {cloud.count} points, expected ≥ {min_p}"
        )

    def assert_max_range(
        self, cloud: PointCloud, max_m: Optional[float] = None
    ) -> None:
        limit = max_m or self._max_range_m
        assert cloud is not None, "LiDAR: no point cloud received"
        bad = [p for p in cloud.points if p.range_m > limit]
        assert not bad, (
            f"LiDAR: {len(bad)} points exceed range limit {limit}m "
            f"(max={max(p.range_m for p in bad):.1f}m)"
        )

    def assert_update_rate(
        self, min_hz: Optional[float] = None, max_hz: Optional[float] = None
    ) -> None:
        rate  = self.current_update_rate_hz()
        _min  = min_hz if min_hz is not None else self._expected_hz * 0.8
        _max  = max_hz if max_hz is not None else self._expected_hz * 1.2
        assert _min <= rate <= _max, (
            f"LiDAR update rate {rate:.1f}Hz outside [{_min:.1f}, {_max:.1f}]Hz"
        )

    def assert_obstacle_detected(
        self, x_m: float, y_m: float,
        radius_m: float = 2.0,
        cloud: Optional[PointCloud] = None,
    ) -> None:
        c = cloud or self.get_latest_cloud()
        assert c is not None, "LiDAR: no point cloud available"
        hits = [
            p for p in c.points
            if ((p.x - x_m)**2 + (p.y - y_m)**2) <= radius_m**2
        ]
        assert hits, (
            f"LiDAR: no obstacle detected at ({x_m:.1f}m, {y_m:.1f}m) "
            f"±{radius_m}m"
        )

    def assert_no_spurious_points(
        self, cloud: PointCloud, min_range_m: float = 0.1
    ) -> None:
        noise = [p for p in cloud.points if p.range_m < min_range_m]
        assert not noise, (
            f"LiDAR: {len(noise)} spurious points within {min_range_m}m of sensor"
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _rx_loop(self) -> None:
        buf: List[bytes] = []
        while not self._stop.is_set():
            try:
                data, _ = self._sock.recvfrom(65535)
                if len(data) == self.VELODYNE_PACKET_SIZE:
                    points = self._parse_velodyne_packet(data)
                    buf.extend(points)
                    if len(buf) >= self._min_points:
                        cloud = PointCloud(points=list(buf))
                        self.ingest_cloud(cloud)
                        buf.clear()
            except socket.timeout:
                pass
            except Exception as exc:
                log.debug(f"[LiDAR] rx error: {exc!r}")

    @staticmethod
    def _parse_velodyne_packet(data: bytes) -> List[LiDARPoint]:
        """Simplified Velodyne VLP-16 packet parser."""
        points: List[LiDARPoint] = []
        BLOCKS = 12
        for b in range(BLOCKS):
            offset = 100 + b * 100
            if offset + 100 > len(data):
                break
            azimuth = struct.unpack_from("<H", data, offset + 2)[0] / 100.0
            import math
            for ch in range(16):
                d_offset = offset + 4 + ch * 3
                dist_raw = struct.unpack_from("<H", data, d_offset)[0]
                intensity = data[d_offset + 2]
                if dist_raw == 0:
                    continue
                dist_m = dist_raw * 0.002
                vert_angle = (-15 + ch * 2) * math.pi / 180.0
                az_rad = math.radians(azimuth)
                r_xy   = dist_m * math.cos(vert_angle)
                x = r_xy * math.sin(az_rad)
                y = r_xy * math.cos(az_rad)
                z = dist_m * math.sin(vert_angle)
                points.append(LiDARPoint(x=x, y=y, z=z, intensity=intensity))
        return points
