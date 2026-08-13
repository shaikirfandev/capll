from __future__ import annotations

import math
from enum import Enum, auto


class TargetType(Enum):
    VEHICLE = auto()
    PEDESTRIAN = auto()
    CYCLIST = auto()


class InterventionLevel(Enum):
    NONE = auto()
    WARNING = auto()
    PREFILL = auto()
    PARTIAL_BRAKE = auto()
    FULL_BRAKE = auto()


class AEBController:
    def __init__(self) -> None:
        self.ttc_warning = 2.7
        self.ttc_prefill = 2.0
        self.ttc_partial = 1.6
        self.ttc_full = 1.2
        self._level = InterventionLevel.NONE
        self._active = False
        self._last_ttc = math.inf

    def compute_ttc(self, ego_speed: float, target_distance: float, target_speed: float) -> float:
        closing_speed = ego_speed - target_speed
        if target_distance <= 0.0 or closing_speed <= 0.05:
            return math.inf
        return target_distance / closing_speed

    def update(self, ego_speed: float, target_distance: float, target_speed: float, target_type: TargetType) -> InterventionLevel:
        self._last_ttc = self.compute_ttc(ego_speed, target_distance, target_speed)
        type_bias = {
            TargetType.VEHICLE: 0.0,
            TargetType.PEDESTRIAN: 0.3,
            TargetType.CYCLIST: 0.2,
        }[target_type]
        effective_ttc = self._last_ttc - type_bias
        if ego_speed < 0.5 or target_distance > 150.0 or math.isinf(self._last_ttc):
            self._level = InterventionLevel.NONE
        elif effective_ttc <= self.ttc_full:
            self._level = InterventionLevel.FULL_BRAKE
        elif effective_ttc <= self.ttc_partial:
            self._level = InterventionLevel.PARTIAL_BRAKE
        elif effective_ttc <= self.ttc_prefill:
            self._level = InterventionLevel.PREFILL
        elif effective_ttc <= self.ttc_warning:
            self._level = InterventionLevel.WARNING
        else:
            self._level = InterventionLevel.NONE
        self._active = self._level is not InterventionLevel.NONE
        return self._level

    def get_intervention_level(self) -> InterventionLevel:
        return self._level

    def is_active(self) -> bool:
        return self._active

    @property
    def last_ttc(self) -> float:
        return self._last_ttc
