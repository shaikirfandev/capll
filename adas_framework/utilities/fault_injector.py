# adas_framework/utilities/fault_injector.py
"""
Fault Injection Module — ADAS Enterprise Framework.

Enables controlled failure injection for negative testing and FMEA verification.

Fault categories:
    1. CAN faults      — bit error, bus-off, missing message, wrong DLC
    2. Sensor faults   — radar disconnect, camera block, LiDAR dropout
    3. ECU faults      — hard reset, flash corruption, memory fault
    4. Network faults  — Ethernet packet loss, delay, reorder
    5. Power faults    — voltage sag, supply interrupt (HIL only)
    6. GPS faults      — signal loss, NTRIP spoofing

Usage:
    injector = FaultInjector(can_bus, cfg)

    # Inject a single missing CAN frame
    with injector.inject(FaultType.MISSING_FRAME, can_id=0x120, duration_s=2.0):
        # test assertions here
        time.sleep(1.0)

    # Parametrize multiple faults
    for fault in injector.suite():
        with fault:
            assert_system_survives(fault)
"""
from __future__ import annotations

import random
import time
import threading
import contextlib
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generator, List, Optional, Callable

from core.logger import get_logger

log = get_logger("fault_injector")


# ─────────────────────────────────────────────────────────────────────────────
# Fault type catalogue
# ─────────────────────────────────────────────────────────────────────────────

class FaultType(Enum):
    # CAN faults
    MISSING_FRAME       = auto()   # Stop sending a periodic frame
    WRONG_DLC           = auto()   # Send frame with wrong data length
    BIT_FLIP            = auto()   # Corrupt data bytes randomly
    BUS_OFF             = auto()   # Simulate CAN bus-off condition
    HIGH_LOAD           = auto()   # Flood bus with high-load frames
    WRONG_CRC           = auto()   # Corrupt E2E CRC byte

    # Sensor faults
    RADAR_DROPOUT       = auto()   # Stop all radar object messages
    CAMERA_BLOCKAGE     = auto()   # Inject all-black camera frames
    LIDAR_DROPOUT       = auto()   # Stop LiDAR point cloud output

    # ECU faults
    ECU_RESET           = auto()   # Send UDS 0x11 hard reset
    COMM_DISABLED       = auto()   # Send UDS 0x28 communication disable

    # Network faults
    ETH_PACKET_LOSS     = auto()   # Drop % of Ethernet packets (HIL only)
    ETH_DELAY_MS        = auto()   # Add artificial latency

    # Power faults (HIL only)
    VOLTAGE_SAG         = auto()   # Drop supply voltage
    POWER_INTERRUPT     = auto()   # Brief power loss


@dataclass
class FaultSpec:
    """Specification for a single fault injection."""
    fault_type:  FaultType
    can_id:      Optional[int]    = None
    duration_s:  float            = 2.0
    intensity:   float            = 1.0    # 0.0–1.0 (for probabilistic faults)
    payload:     Optional[bytes]  = None
    description: str              = ""


# ─────────────────────────────────────────────────────────────────────────────
# FaultInjector
# ─────────────────────────────────────────────────────────────────────────────

class FaultInjector:
    """Controls all fault injection operations."""

    def __init__(self, can_bus, cfg=None):
        self._can       = can_bus
        self._cfg       = cfg
        self._active    : List[FaultSpec] = []
        self._lock      = threading.Lock()
        self._suppressed: set = set()   # CAN IDs suppressed

    # ── Context manager injection ─────────────────────────────────────────────

    @contextlib.contextmanager
    def inject(self, spec_or_type, **kwargs) -> Generator[FaultSpec, None, None]:
        """
        Context manager for a single fault injection.

        Usage:
            with injector.inject(FaultType.MISSING_FRAME, can_id=0x120) as fault:
                ...assertions...
        """
        if isinstance(spec_or_type, FaultType):
            spec = FaultSpec(fault_type=spec_or_type, **kwargs)
        else:
            spec = spec_or_type

        self._start_fault(spec)
        try:
            yield spec
        finally:
            self._stop_fault(spec)

    # ── Fault start / stop ────────────────────────────────────────────────────

    def _start_fault(self, spec: FaultSpec):
        log.warning(f"[FAULT START] {spec.fault_type.name} | CAN_ID={spec.can_id:#05x if spec.can_id else 'N/A'}")
        with self._lock:
            self._active.append(spec)

        ft = spec.fault_type

        if ft == FaultType.MISSING_FRAME and spec.can_id:
            self._suppressed.add(spec.can_id)
            self._start_suppression(spec.can_id)

        elif ft == FaultType.BIT_FLIP and spec.can_id:
            self._start_bit_flip(spec)

        elif ft == FaultType.WRONG_DLC and spec.can_id:
            self._send_wrong_dlc(spec.can_id)

        elif ft == FaultType.HIGH_LOAD:
            self._start_high_load(spec)

        elif ft == FaultType.WRONG_CRC and spec.can_id:
            self._inject_wrong_crc(spec.can_id)

        elif ft == FaultType.ECU_RESET:
            self._ecu_reset()

        elif ft == FaultType.COMM_DISABLED:
            self._comm_disable()

    def _stop_fault(self, spec: FaultSpec):
        with self._lock:
            if spec in self._active:
                self._active.remove(spec)

        ft = spec.fault_type
        if ft == FaultType.MISSING_FRAME and spec.can_id:
            self._suppressed.discard(spec.can_id)
            log.info(f"[FAULT END] Frame suppression removed for {spec.can_id:#05x}")

        elif ft == FaultType.COMM_DISABLED:
            self._comm_enable()

        log.info(f"[FAULT END] {spec.fault_type.name}")

    # ── CAN fault implementations ─────────────────────────────────────────────

    def _start_suppression(self, can_id: int):
        """Block outgoing frames for this CAN ID."""
        # In a real implementation, this hooks into the CAN tx filter
        # For test environments: stop the periodic sender if one exists
        if hasattr(self._can, '_periodic_senders'):
            sender = self._can._periodic_senders.get(can_id)
            if sender:
                sender.stop()
                log.debug(f"Stopped periodic sender for {can_id:#05x}")

    def _start_bit_flip(self, spec: FaultSpec):
        """Spawn a thread that sends corrupted frames periodically."""
        def _corruptor():
            end = time.monotonic() + spec.duration_s
            while time.monotonic() < end:
                data = list(spec.payload or bytes(8))
                idx = random.randint(0, len(data) - 1)
                bit = 1 << random.randint(0, 7)
                data[idx] ^= bit
                self._can.send(spec.can_id, bytes(data))
                time.sleep(0.020)  # 50 Hz

        t = threading.Thread(target=_corruptor, daemon=True, name="BitFlip")
        t.start()

    def _send_wrong_dlc(self, can_id: int):
        """Send a frame with too-short payload."""
        self._can.send(can_id, bytes([0xDE]))  # only 1 byte

    def _start_high_load(self, spec: FaultSpec):
        """Flood the bus at 80% load."""
        def _flood():
            end = time.monotonic() + spec.duration_s
            while time.monotonic() < end:
                for fake_id in range(0x500, 0x540):
                    self._can.send(fake_id, bytes(8))
                time.sleep(0.001)

        t = threading.Thread(target=_flood, daemon=True, name="HighLoad")
        t.start()

    def _inject_wrong_crc(self, can_id: int):
        """Send a frame with corrupted E2E CRC byte."""
        data = bytes([0x00] * 7 + [0xFF])  # last byte = corrupted CRC
        self._can.send(can_id, data)

    # ── ECU fault implementations ─────────────────────────────────────────────

    def _ecu_reset(self):
        """Send UDS hard reset if UDS client is available."""
        if hasattr(self._can, '_uds_client'):
            self._can._uds_client.sync_change_session(0x03)
            self._can._uds_client._raw_request(bytes([0x11, 0x01]))
        else:
            log.warning("UDS client not attached — ECU reset via CAN not available")

    def _comm_disable(self):
        """Disable ECU communication via UDS 0x28."""
        if hasattr(self._can, '_uds_client'):
            self._can._uds_client._raw_request(bytes([0x28, 0x01, 0x01]))

    def _comm_enable(self):
        if hasattr(self._can, '_uds_client'):
            self._can._uds_client._raw_request(bytes([0x28, 0x00, 0x01]))

    # ── Fault suite generation ────────────────────────────────────────────────

    def suite(self, can_ids: List[int] = None) -> List[FaultSpec]:
        """
        Generate a parametrized fault suite for all common fault types.
        Useful for FMEA coverage loops.
        """
        ids = can_ids or [0x120, 0x150, 0x160]
        specs = []
        for can_id in ids:
            specs.append(FaultSpec(FaultType.MISSING_FRAME, can_id=can_id,
                                   duration_s=3.0,
                                   description=f"Missing frame {can_id:#05x}"))
            specs.append(FaultSpec(FaultType.BIT_FLIP, can_id=can_id,
                                   duration_s=2.0, payload=bytes(8),
                                   description=f"Bit flip {can_id:#05x}"))
            specs.append(FaultSpec(FaultType.WRONG_DLC, can_id=can_id,
                                   description=f"Wrong DLC {can_id:#05x}"))
            specs.append(FaultSpec(FaultType.WRONG_CRC, can_id=can_id,
                                   description=f"Wrong CRC {can_id:#05x}"))
        return specs

    # ── Active state ──────────────────────────────────────────────────────────

    @property
    def active_faults(self) -> List[FaultSpec]:
        with self._lock:
            return list(self._active)

    def is_suppressed(self, can_id: int) -> bool:
        return can_id in self._suppressed

    def clear_all(self):
        with self._lock:
            self._active.clear()
        self._suppressed.clear()
