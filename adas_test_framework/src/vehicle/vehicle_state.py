from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class VehicleState:
    speed_mps: float
    yaw_rate: float
    acceleration: float = 0.0
    lane_offset: float = 0.0
    gear: str = "D"
    indicators: dict[str, bool] = field(default_factory=lambda: {"left": False, "right": False})
    brake_pressure: float = 0.0

    @property
    def speed_kph(self) -> float:
        return self.speed_mps * 3.6

    def apply_acceleration(self, acceleration_mps2: float, dt: float) -> None:
        self.acceleration = acceleration_mps2
        self.speed_mps = max(0.0, self.speed_mps + acceleration_mps2 * dt)

    def steer(self, lane_offset: float, yaw_rate: float) -> None:
        self.lane_offset = lane_offset
        self.yaw_rate = yaw_rate
