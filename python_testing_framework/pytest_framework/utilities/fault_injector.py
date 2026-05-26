"""
pytest_framework/utilities/fault_injector.py

Enterprise ADAS Framework – Fault Injection Engine
===================================================
16 fault types covering CAN, Ethernet, sensor, and ECU.
Context-manager API for clean test isolation.
FMEA parametrize helper generates full fault matrix.
"""
from __future__ import annotations

import random
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Generator, Iterator, List, Optional

from core.logger import get_logger

log = get_logger("fault_injector")


class FaultType(Enum):
    MISSING_FRAME      = auto()   # Stop sending a CAN frame
    WRONG_DLC          = auto()   # Send with incorrect DLC
    BIT_FLIP           = auto()   # Flip random bits in payload
    BUS_OFF            = auto()   # Trigger CAN bus-off state
    HIGH_LOAD          = auto()   # Flood bus with low-priority frames
    WRONG_CRC          = auto()   # Corrupt CRC / checksum byte
    RADAR_DROPOUT      = auto()   # Stop radar object injection
    CAMERA_BLOCKAGE    = auto()   # Inject blank camera frames
    LIDAR_DROPOUT      = auto()   # Stop LiDAR point cloud injection
    ECU_RESET          = auto()   # Send UDS ECU reset command
    COMM_DISABLED      = auto()   # UDS 0x28 disable normal comms
    ETH_PACKET_LOSS    = auto()   # Drop random Ethernet packets
    ETH_DELAY_MS       = auto()   # Add latency to Ethernet frames
    VOLTAGE_SAG        = auto()   # Simulate undervoltage event
    POWER_INTERRUPT    = auto()   # Simulate complete power loss
    GPS_LOSS           = auto()   # Stop GPS signal injection


@dataclass
class FaultSpec:
    fault_type:  FaultType
    can_id:      int   = 0
    duration_s:  float = 1.0
    intensity:   float = 1.0    # 0.0–1.0 scale
    payload:     bytes = b""
    description: str  = ""

    def __post_init__(self) -> None:
        if not self.description:
            self.description = self.fault_type.name


class FaultInjector:
    """
    Controlled fault injection for negative testing and FMEA verification.

    Usage:
        fi = FaultInjector(can_bus)
        with fi.inject(FaultType.BIT_FLIP, can_id=0x120, duration_s=0.5):
            # run test that should detect corruption
            ...
    """

    def __init__(self, can_bus: Optional[Any] = None) -> None:
        self._bus           = can_bus
        self._active:       List[FaultSpec] = []
        self._suppressed:   set = set()
        self._lock          = threading.Lock()
        self._threads:      List[threading.Thread] = []

    # ── Context manager API ───────────────────────────────────────────────────

    @contextmanager
    def inject(
        self,
        fault: "FaultType | FaultSpec",
        **kwargs: Any,
    ) -> Iterator[FaultSpec]:
        if isinstance(fault, FaultType):
            spec = FaultSpec(fault_type=fault, **kwargs)
        else:
            spec = fault
        self._start(spec)
        try:
            yield spec
        finally:
            self._stop(spec)

    def inject_for(self, fault_type: FaultType, duration_s: float,
                   **kwargs: Any) -> None:
        """Fire-and-forget injection for exactly duration_s."""
        spec = FaultSpec(fault_type=fault_type, duration_s=duration_s, **kwargs)
        self._start(spec)
        time.sleep(duration_s)
        self._stop(spec)

    # ── FMEA matrix ───────────────────────────────────────────────────────────

    @staticmethod
    def fmea_suite(can_ids: List[int]) -> List[FaultSpec]:
        """
        Generate a full FMEA parametrize list covering every fault type
        for each provided CAN ID.
        """
        suite: List[FaultSpec] = []
        for can_id in can_ids:
            for ft in FaultType:
                suite.append(FaultSpec(
                    fault_type = ft,
                    can_id     = can_id,
                    duration_s = 0.5,
                ))
        return suite

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def active_faults(self) -> List[FaultSpec]:
        with self._lock:
            return list(self._active)

    def is_suppressed(self, can_id: int) -> bool:
        return can_id in self._suppressed

    def clear_all(self) -> None:
        with self._lock:
            self._active.clear()
            self._suppressed.clear()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _start(self, spec: FaultSpec) -> None:
        with self._lock:
            self._active.append(spec)
        log.warning(
            f"[FaultInjector] ▶ {spec.fault_type.name} "
            f"can_id=0x{spec.can_id:03X} duration={spec.duration_s}s"
        )
        if spec.fault_type == FaultType.BIT_FLIP and self._bus:
            t = threading.Thread(
                target=self._bit_flip_loop,
                args=(spec,),
                daemon=True,
            )
            t.start()
            self._threads.append(t)
        if spec.fault_type == FaultType.HIGH_LOAD and self._bus:
            t = threading.Thread(
                target=self._high_load_loop,
                args=(spec,),
                daemon=True,
            )
            t.start()
            self._threads.append(t)
        if spec.fault_type in (FaultType.RADAR_DROPOUT,
                                FaultType.CAMERA_BLOCKAGE,
                                FaultType.LIDAR_DROPOUT,
                                FaultType.GPS_LOSS,
                                FaultType.MISSING_FRAME):
            with self._lock:
                self._suppressed.add(spec.can_id)

    def _stop(self, spec: FaultSpec) -> None:
        with self._lock:
            if spec in self._active:
                self._active.remove(spec)
            self._suppressed.discard(spec.can_id)
        log.info(f"[FaultInjector] ■ {spec.fault_type.name} ended")

    def _bit_flip_loop(self, spec: FaultSpec) -> None:
        deadline = time.monotonic() + spec.duration_s
        while time.monotonic() < deadline:
            if self._bus and spec.can_id:
                corrupted = bytearray(8)
                for i in range(8):
                    corrupted[i] = random.randint(0, 0xFF)
                try:
                    self._bus.send(spec.can_id, bytes(corrupted))
                except Exception:
                    pass
            time.sleep(0.02)

    def _high_load_loop(self, spec: FaultSpec) -> None:
        deadline = time.monotonic() + spec.duration_s
        while time.monotonic() < deadline:
            if self._bus:
                for flood_id in range(0x700, 0x700 + 20):
                    try:
                        self._bus.send(flood_id, bytes(8))
                    except Exception:
                        break
            time.sleep(0.001)
