from __future__ import annotations

import math


class FCWController:
    def __init__(self, warning_ttc_s: float = 2.5) -> None:
        self.warning_ttc_s = warning_ttc_s
        self._warning_active = False
        self._last_ttc = math.inf

    def update(self, ego_speed_mps: float, target_distance_m: float, target_speed_mps: float) -> bool:
        closing_speed = ego_speed_mps - target_speed_mps
        self._last_ttc = math.inf if closing_speed <= 0.05 else target_distance_m / closing_speed
        self._warning_active = 0.0 < self._last_ttc <= self.warning_ttc_s
        return self._warning_active

    def is_warning_active(self) -> bool:
        return self._warning_active

    @property
    def last_ttc(self) -> float:
        return self._last_ttc
