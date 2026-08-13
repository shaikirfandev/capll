from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BlindSpotObject:
    object_id: int
    longitudinal_m: float
    lateral_m: float
    relative_speed_mps: float = 0.0


class BSDController:
    def __init__(self) -> None:
        self._left_detected = False
        self._right_detected = False

    def update(self, objects: list[BlindSpotObject]) -> tuple[bool, bool]:
        self._left_detected = any(0.0 <= obj.longitudinal_m <= 10.0 and 1.0 <= obj.lateral_m <= 4.0 for obj in objects)
        self._right_detected = any(0.0 <= obj.longitudinal_m <= 10.0 and -4.0 <= obj.lateral_m <= -1.0 for obj in objects)
        return self._left_detected, self._right_detected

    def left_active(self) -> bool:
        return self._left_detected

    def right_active(self) -> bool:
        return self._right_detected
