from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LidarDetection:
    object_id: int
    distance_m: float
    lateral_offset_m: float
    height_m: float = 1.5
    confidence: float = 1.0
    timestamp: float = 0.0
