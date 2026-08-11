from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RadarDetection:
    object_id: int
    distance_m: float
    relative_speed_mps: float
    azimuth_deg: float = 0.0
    confidence: float = 1.0
    timestamp: float = 0.0
