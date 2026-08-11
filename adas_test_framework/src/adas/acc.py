from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ACCState(Enum):
    OFF = auto()
    STANDBY = auto()
    ACTIVE = auto()
    BRAKING = auto()
    OVERRIDE = auto()


@dataclass
class ACCController:
    min_speed_kph: float = 30.0
    max_speed_kph: float = 180.0
    time_gap_settings: list[float] = field(default_factory=lambda: [1.0, 1.3, 1.6, 2.0])
    kp: float = 0.35
    ki: float = 0.08
    kd: float = 0.04
    gap_gain: float = 0.12
    _state: ACCState = ACCState.OFF
    _set_speed_kph: float = 30.0
    _selected_gap_index: int = 2
    _integral_error: float = 0.0
    _previous_error: float = 0.0
    _last_acceleration: float = 0.0
    _target_acquired: bool = False
    _driver_override: bool = False

    def activate(self) -> ACCState:
        if not self.min_speed_kph <= self._set_speed_kph <= self.max_speed_kph:
            raise ValueError("Set speed out of ACC operating range")
        self._state = ACCState.STANDBY
        self._driver_override = False
        return self._state

    def deactivate(self) -> ACCState:
        self._state = ACCState.OFF
        self._integral_error = 0.0
        self._previous_error = 0.0
        self._last_acceleration = 0.0
        self._target_acquired = False
        self._driver_override = False
        return self._state

    def set_speed(self, kph: float) -> None:
        if not self.min_speed_kph <= kph <= self.max_speed_kph:
            raise ValueError(f"ACC set speed must be within {self.min_speed_kph}-{self.max_speed_kph} kph")
        self._set_speed_kph = float(kph)

    def set_time_gap(self, time_gap_s: float) -> float:
        if time_gap_s not in self.time_gap_settings:
            raise ValueError("Unsupported time gap setting")
        self._selected_gap_index = self.time_gap_settings.index(time_gap_s)
        return time_gap_s

    @property
    def selected_time_gap(self) -> float:
        return self.time_gap_settings[self._selected_gap_index]

    @property
    def driver_override_detected(self) -> bool:
        return self._driver_override

    def update(
        self,
        vehicle_speed: float,
        lead_vehicle_distance: Optional[float],
        lead_vehicle_speed: Optional[float],
        brake_pressed: bool = False,
        throttle_override: bool = False,
        dt: float = 0.1,
    ) -> float:
        if self._state == ACCState.OFF:
            self._last_acceleration = 0.0
            return self._last_acceleration
        if brake_pressed or throttle_override:
            self._driver_override = True
            self._state = ACCState.OVERRIDE
            self._last_acceleration = 0.0
            return self._last_acceleration
        self._driver_override = False
        speed_kph = vehicle_speed * 3.6
        if speed_kph < self.min_speed_kph:
            self._state = ACCState.STANDBY
            self._last_acceleration = 0.0
            return self._last_acceleration
        set_speed_mps = self._set_speed_kph / 3.6
        target_speed = set_speed_mps
        desired_distance = max(5.0, self.selected_time_gap * max(vehicle_speed, 0.1))
        self._target_acquired = lead_vehicle_distance is not None and lead_vehicle_speed is not None
        if self._target_acquired:
            assert lead_vehicle_distance is not None and lead_vehicle_speed is not None
            distance_error = lead_vehicle_distance - desired_distance
            relative_speed = lead_vehicle_speed - vehicle_speed
            if distance_error < 0.0 or relative_speed < -1.0:
                self._state = ACCState.BRAKING
                target_speed = min(set_speed_mps, max(0.0, lead_vehicle_speed + distance_error * self.gap_gain))
            else:
                self._state = ACCState.ACTIVE
                target_speed = min(set_speed_mps, lead_vehicle_speed + max(distance_error, 0.0) * 0.05)
        else:
            self._state = ACCState.ACTIVE
        self._last_acceleration = self._pid_control(target_speed - vehicle_speed, dt)
        if self._state == ACCState.BRAKING:
            distance_error = (lead_vehicle_distance or 0.0) - desired_distance
            self._last_acceleration -= max(0.0, -distance_error) * self.gap_gain
        self._last_acceleration = max(-3.5, min(2.0, self._last_acceleration))
        return self._last_acceleration

    def _pid_control(self, error: float, dt: float) -> float:
        self._integral_error += error * dt
        derivative = (error - self._previous_error) / dt if dt > 0 else 0.0
        self._previous_error = error
        return self.kp * error + self.ki * self._integral_error + self.kd * derivative

    def get_state(self) -> ACCState:
        return self._state

    def get_set_speed(self) -> float:
        return self._set_speed_kph

    def compute_acceleration(self) -> float:
        return self._last_acceleration
