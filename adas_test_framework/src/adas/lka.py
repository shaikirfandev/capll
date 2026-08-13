from __future__ import annotations

from enum import Enum, auto


class LKAWarningLevel(Enum):
    NONE = auto()
    WARNING = auto()
    ACTIVE = auto()


class LKAController:
    def __init__(self, lane_departure_threshold_m: float = 0.3) -> None:
        self.lane_departure_threshold_m = lane_departure_threshold_m
        self._warning_level = LKAWarningLevel.NONE
        self._last_torque = 0.0
        self._departing = False

    def update(self, lane_offset_m: float, lateral_speed_mps: float, vehicle_speed_mps: float) -> float:
        self._departing = abs(lane_offset_m) >= self.lane_departure_threshold_m and lane_offset_m * lateral_speed_mps >= 0.0
        if abs(lane_offset_m) < self.lane_departure_threshold_m * 0.8:
            self._warning_level = LKAWarningLevel.NONE
        elif self._departing and vehicle_speed_mps >= 12.0:
            self._warning_level = LKAWarningLevel.ACTIVE
        else:
            self._warning_level = LKAWarningLevel.WARNING
        self._last_torque = self.compute_steering_torque(lane_offset_m, lateral_speed_mps, vehicle_speed_mps)
        return self._last_torque

    def compute_steering_torque(self, lane_offset_m: float = 0.0, lateral_speed_mps: float = 0.0, vehicle_speed_mps: float = 0.0) -> float:
        speed_factor = min(1.0, max(0.2, vehicle_speed_mps / 25.0))
        torque = -(3.0 * lane_offset_m + 0.8 * lateral_speed_mps) * speed_factor
        return max(-3.0, min(3.0, torque))

    def is_departing(self) -> bool:
        return self._departing

    def get_warning_level(self) -> LKAWarningLevel:
        return self._warning_level
