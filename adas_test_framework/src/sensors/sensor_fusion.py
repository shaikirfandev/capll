from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np

from sensors.camera import CameraDetection
from sensors.lidar import LidarDetection
from sensors.radar import RadarDetection


@dataclass(slots=True)
class FusedTrack:
    object_id: int
    distance_m: float
    relative_speed_mps: float
    lateral_offset_m: float
    confidence: float
    sources: set[str] = field(default_factory=set)
    timestamp: float = field(default_factory=time.monotonic)


class SensorFusion:
    """Simple constant-velocity Kalman fusion for camera/radar/lidar tracks."""

    def __init__(self, track_timeout_s: float = 0.5) -> None:
        self.track_timeout_s = track_timeout_s
        self._states: dict[int, np.ndarray] = {}
        self._covariances: dict[int, np.ndarray] = {}
        self._tracks: dict[int, FusedTrack] = {}
        self._sensor_timestamps: dict[str, float] = {}
        self._q = np.diag([0.3, 0.2])
        self._r = np.diag([0.7, 0.4])

    def predict(self, object_id: int, dt: float) -> np.ndarray:
        state = self._states[object_id]
        transition = np.array([[1.0, dt], [0.0, 1.0]])
        self._states[object_id] = transition @ state
        self._covariances[object_id] = transition @ self._covariances[object_id] @ transition.T + self._q
        return self._states[object_id].copy()

    def update_track(self, object_id: int, distance_m: float, velocity_mps: float, lateral_offset_m: float, confidence: float, source: str, timestamp: Optional[float] = None) -> FusedTrack:
        timestamp = time.monotonic() if timestamp is None else timestamp
        measurement = np.array([[distance_m], [velocity_mps]])
        if object_id not in self._states:
            self._states[object_id] = measurement.copy()
            self._covariances[object_id] = np.eye(2)
        else:
            self.predict(object_id, max(timestamp - self._tracks[object_id].timestamp, 0.01))
            covariance = self._covariances[object_id]
            innovation = measurement - self._states[object_id]
            innovation_cov = covariance + self._r
            gain = covariance @ np.linalg.inv(innovation_cov)
            self._states[object_id] = self._states[object_id] + gain @ innovation
            self._covariances[object_id] = (np.eye(2) - gain) @ covariance
        track = self._tracks.get(object_id)
        smoothed_lateral = lateral_offset_m if track is None else (track.lateral_offset_m * 0.4 + lateral_offset_m * 0.6)
        merged_sources = set() if track is None else set(track.sources)
        merged_sources.add(source)
        fused = FusedTrack(
            object_id=object_id,
            distance_m=float(self._states[object_id][0, 0]),
            relative_speed_mps=float(self._states[object_id][1, 0]),
            lateral_offset_m=smoothed_lateral,
            confidence=min(1.0, max(0.0, confidence)),
            sources=merged_sources,
            timestamp=timestamp,
        )
        self._tracks[object_id] = fused
        self._sensor_timestamps[source] = timestamp
        return fused

    def fuse(
        self,
        camera_detections: Optional[Iterable[CameraDetection]] = None,
        radar_detections: Optional[Iterable[RadarDetection]] = None,
        lidar_detections: Optional[Iterable[LidarDetection]] = None,
        timestamp: Optional[float] = None,
    ) -> list[FusedTrack]:
        timestamp = time.monotonic() if timestamp is None else timestamp
        camera_map = {item.object_id: item for item in camera_detections or []}
        radar_map = {item.object_id: item for item in radar_detections or []}
        lidar_map = {item.object_id: item for item in lidar_detections or []}
        track_ids = set(camera_map) | set(radar_map) | set(lidar_map)
        fused_tracks: list[FusedTrack] = []
        for object_id in track_ids:
            camera = camera_map.get(object_id)
            radar = radar_map.get(object_id)
            lidar = lidar_map.get(object_id)
            weights = []
            distances = []
            velocities = []
            laterals = []
            if camera:
                weights.append(camera.confidence)
                distances.append(camera.distance_m)
                velocities.append(camera.relative_speed_mps)
                laterals.append(camera.lateral_offset_m)
            if radar:
                weights.append(radar.confidence * 1.2)
                distances.append(radar.distance_m)
                velocities.append(radar.relative_speed_mps)
                laterals.append(math.tan(math.radians(radar.azimuth_deg)) * radar.distance_m)
            if lidar:
                weights.append(lidar.confidence * 1.1)
                distances.append(lidar.distance_m)
                velocities.append(0.0 if radar is None else radar.relative_speed_mps)
                laterals.append(lidar.lateral_offset_m)
            total_weight = sum(weights) or 1.0
            fused_distance = sum(value * weight for value, weight in zip(distances, weights)) / total_weight
            fused_velocity = sum(value * weight for value, weight in zip(velocities, weights)) / total_weight
            fused_lateral = sum(value * weight for value, weight in zip(laterals, weights)) / total_weight
            fused_confidence = min(1.0, total_weight / max(len(weights), 1))
            source = "+".join(sorted(name for name, present in (("camera", camera), ("radar", radar), ("lidar", lidar)) if present))
            fused_tracks.append(self.update_track(object_id, fused_distance, fused_velocity, fused_lateral, fused_confidence, source, timestamp))
        self.remove_stale_tracks(timestamp)
        return fused_tracks

    def remove_stale_tracks(self, timestamp: Optional[float] = None) -> None:
        timestamp = time.monotonic() if timestamp is None else timestamp
        stale = [track_id for track_id, track in self._tracks.items() if timestamp - track.timestamp > self.track_timeout_s]
        for track_id in stale:
            self._tracks.pop(track_id, None)
            self._states.pop(track_id, None)
            self._covariances.pop(track_id, None)

    def is_sensor_timed_out(self, sensor_name: str, timeout_s: Optional[float] = None, now: Optional[float] = None) -> bool:
        if sensor_name not in self._sensor_timestamps:
            return True
        timeout = self.track_timeout_s if timeout_s is None else timeout_s
        current = time.monotonic() if now is None else now
        return current - self._sensor_timestamps[sensor_name] > timeout

    @property
    def tracks(self) -> dict[int, FusedTrack]:
        return dict(self._tracks)
