from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Callable, Deque, Dict, Iterable, Optional


@dataclass(slots=True)
class CANFrame:
    arbitration_id: int
    data: bytes
    timestamp: float = field(default_factory=time.monotonic)
    is_fd: bool = False


class CANInterface:
    """Deterministic mock CAN interface suitable for CI and pytest."""

    def __init__(self, channel: str = "virtual", bitrate: int = 500_000, loopback: bool = True) -> None:
        self.channel = channel
        self.bitrate = bitrate
        self.loopback = loopback
        self._rx_queue: Deque[CANFrame] = deque()
        self._tx_history: list[CANFrame] = []
        self._callbacks: Dict[int, list[Callable[[CANFrame], None]]] = {}
        self._suppressed_ids: set[int] = set()
        self._lock = Lock()

    def send(self, arbitration_id: int, data: bytes | bytearray | Iterable[int]) -> CANFrame:
        payload = bytes(data)
        if len(payload) > 8:
            raise ValueError("Classic CAN payload must be 8 bytes or less")
        frame = CANFrame(arbitration_id=arbitration_id, data=payload)
        with self._lock:
            if arbitration_id in self._suppressed_ids:
                return frame
            self._tx_history.append(frame)
            if self.loopback:
                self._rx_queue.append(frame)
        for callback in self._callbacks.get(arbitration_id, []):
            callback(frame)
        return frame

    def inject_frame(self, arbitration_id: int, data: bytes | bytearray | Iterable[int]) -> CANFrame:
        frame = CANFrame(arbitration_id=arbitration_id, data=bytes(data))
        with self._lock:
            self._rx_queue.append(frame)
        return frame

    def recv(self, arbitration_id: Optional[int] = None, timeout: float = 0.0) -> Optional[CANFrame]:
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                if arbitration_id is None and self._rx_queue:
                    return self._rx_queue.popleft()
                if arbitration_id is not None:
                    for index, frame in enumerate(self._rx_queue):
                        if frame.arbitration_id == arbitration_id:
                            del self._rx_queue[index]
                            return frame
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.001)

    def register_callback(self, arbitration_id: int, callback: Callable[[CANFrame], None]) -> None:
        self._callbacks.setdefault(arbitration_id, []).append(callback)

    def suppress(self, arbitration_id: int) -> None:
        self._suppressed_ids.add(arbitration_id)

    def restore(self, arbitration_id: int) -> None:
        self._suppressed_ids.discard(arbitration_id)

    def clear(self) -> None:
        with self._lock:
            self._rx_queue.clear()
            self._tx_history.clear()

    @property
    def tx_history(self) -> list[CANFrame]:
        return list(self._tx_history)
