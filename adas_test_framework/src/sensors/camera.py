from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CameraDetection:
    object_id: int
    distance_m: float
    lateral_offset_m: float
    relative_speed_mps: float
    confidence: float = 1.0
    lane_offset_m: float = 0.0
    timestamp: float = 0.0
