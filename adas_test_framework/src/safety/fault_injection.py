from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Iterator, Optional

from communication.can_interface import CANInterface


class FaultType(Enum):
    SENSOR_TIMEOUT = auto()
    SIGNAL_CORRUPTION = auto()
    STUCK_AT = auto()
    CAN_SUPPRESSION = auto()


@dataclass(slots=True)
class FaultEvent:
    fault_type: FaultType
    target: str
    value: object | None = None


class FaultInjector:
    def __init__(self, can_interface: Optional[CANInterface] = None) -> None:
        self.can_interface = can_interface
        self._sensor_timeouts: set[str] = set()
        self._signal_corruption: dict[str, Callable[[object], object]] = {}
        self._stuck_values: dict[str, object] = {}
        self._active_faults: list[FaultEvent] = []

    def inject_sensor_timeout(self, sensor_name: str) -> FaultEvent:
        self._sensor_timeouts.add(sensor_name)
        event = FaultEvent(FaultType.SENSOR_TIMEOUT, sensor_name)
        self._active_faults.append(event)
        return event

    def inject_signal_corruption(self, signal_name: str, corruption: Callable[[object], object] | object) -> FaultEvent:
        transform = corruption if callable(corruption) else lambda _value, replacement=corruption: replacement
        self._signal_corruption[signal_name] = transform
        event = FaultEvent(FaultType.SIGNAL_CORRUPTION, signal_name)
        self._active_faults.append(event)
        return event

    def inject_stuck_at(self, signal_name: str, value: object) -> FaultEvent:
        self._stuck_values[signal_name] = value
        event = FaultEvent(FaultType.STUCK_AT, signal_name, value)
        self._active_faults.append(event)
        return event

    def suppress_can_id(self, arbitration_id: int) -> FaultEvent:
        if self.can_interface is None:
            raise ValueError("CAN interface required for CAN suppression")
        self.can_interface.suppress(arbitration_id)
        event = FaultEvent(FaultType.CAN_SUPPRESSION, hex(arbitration_id))
        self._active_faults.append(event)
        return event

    def clear_fault(self, target: str) -> None:
        self._sensor_timeouts.discard(target)
        self._signal_corruption.pop(target, None)
        self._stuck_values.pop(target, None)
        self._active_faults = [event for event in self._active_faults if event.target != target]
        if self.can_interface and target.startswith("0x"):
            self.can_interface.restore(int(target, 16))

    def clear_all(self) -> None:
        for event in list(self._active_faults):
            self.clear_fault(event.target)

    def apply_faults(self, signals: dict[str, object]) -> dict[str, object]:
        mutated = dict(signals)
        for signal_name, value in self._stuck_values.items():
            mutated[signal_name] = value
        for signal_name, transform in self._signal_corruption.items():
            if signal_name in mutated:
                mutated[signal_name] = transform(mutated[signal_name])
        return mutated

    def is_sensor_timed_out(self, sensor_name: str) -> bool:
        return sensor_name in self._sensor_timeouts

    @contextmanager
    def sensor_timeout(self, sensor_name: str) -> Iterator[FaultEvent]:
        event = self.inject_sensor_timeout(sensor_name)
        try:
            yield event
        finally:
            self.clear_fault(sensor_name)

    @property
    def active_faults(self) -> list[FaultEvent]:
        return list(self._active_faults)
