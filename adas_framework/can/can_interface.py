# adas_framework/can/can_interface.py
"""
Thread-safe CAN bus abstraction layer.

Supports:
    - Classic CAN 2.0B (ISO 11898)
    - CAN FD (ISO 11898-7)
    - Virtual bus (testing without hardware)
    - python-can backend (PCAN, Vector, SocketCAN, kvaser, virtual)
    - Async reception via asyncio
    - Periodic message transmission
    - Message filtering

Usage:
    bus = CANInterface.create(cfg.can)
    bus.start()
    bus.send(0x310, b'\\x00' * 8)
    msg = bus.recv(timeout=0.1)
    bus.subscribe(0x310, callback)
    bus.stop()
"""
from __future__ import annotations

import asyncio
import struct
import threading
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional

try:
    import can
    from can import Message, Bus, PeriodicTask
    _CAN_AVAILABLE = True
except ImportError:
    _CAN_AVAILABLE = False

from core.config import CANConfig
from core.logger import can_log as log


class CANMessage:
    """Lightweight CAN message container (hardware-independent)."""

    __slots__ = ("arb_id", "data", "timestamp", "is_fd", "is_error")

    def __init__(self, arb_id: int, data: bytes,
                 timestamp: float = 0.0,
                 is_fd: bool = False,
                 is_error: bool = False):
        self.arb_id    = arb_id
        self.data      = data
        self.timestamp = timestamp or time.monotonic()
        self.is_fd     = is_fd
        self.is_error  = is_error

    def __repr__(self):
        return (f"CANMessage(id={self.arb_id:#05x}, "
                f"data={self.data.hex(' ')}, ts={self.timestamp:.6f})")


class PeriodicSender:
    """Sends a CAN message at a fixed interval in a background thread."""

    def __init__(self, bus_send_fn: Callable, arb_id: int,
                 data: bytes, period_s: float):
        self._send   = bus_send_fn
        self.arb_id  = arb_id
        self.data    = data
        self.period  = period_s
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            self._send(self.arb_id, self.data)
            time.sleep(self.period)

    def update_data(self, data: bytes):
        self.data = data

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)


class CANInterface:
    """
    Hardware-agnostic CAN bus interface.

    Thread-safe: recv/send can be called from any thread.
    """

    def __init__(self, config: CANConfig):
        self._cfg      = config
        self._bus      = None
        self._lock     = threading.Lock()
        self._running  = False
        self._rx_thread: Optional[threading.Thread] = None
        self._subscribers: Dict[int, List[Callable]] = defaultdict(list)
        self._wildcard_subs: List[Callable] = []
        self._periodic_senders: List[PeriodicSender] = []

        # Latest decoded message per arb_id (for polling)
        self._latest: Dict[int, CANMessage] = {}
        self._latest_lock = threading.Lock()

        # Error stats
        self.error_count = 0
        self.rx_count    = 0
        self.tx_count    = 0

    @classmethod
    def create(cls, config: CANConfig) -> "CANInterface":
        return cls(config)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if not _CAN_AVAILABLE:
            log.warning("python-can not available — using virtual null bus")
            self._bus = _NullBus()
        else:
            kwargs = dict(
                channel=self._cfg.channel,
                bustype=self._cfg.interface,
                bitrate=self._cfg.bitrate,
            )
            if self._cfg.fd_enabled:
                kwargs["fd"] = True
                kwargs["data_bitrate"] = self._cfg.fd_bitrate
            self._bus = can.interface.Bus(**kwargs)

        self._running = True
        self._rx_thread = threading.Thread(
            target=self._rx_loop, name="CAN-RX", daemon=True
        )
        self._rx_thread.start()
        log.info(
            f"CAN started — {self._cfg.interface}:{self._cfg.channel} "
            f"@ {self._cfg.bitrate//1000}kbps"
        )

    def stop(self):
        self._running = False
        for ps in self._periodic_senders:
            ps.stop()
        if self._rx_thread:
            self._rx_thread.join(timeout=2.0)
        if self._bus and hasattr(self._bus, "shutdown"):
            self._bus.shutdown()
        log.info("CAN stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ── Send ──────────────────────────────────────────────────────────────────

    def send(self, arb_id: int, data: bytes, is_fd: bool = False):
        """Send a single CAN frame. Thread-safe."""
        with self._lock:
            if _CAN_AVAILABLE and isinstance(self._bus, can.BusABC):
                msg = can.Message(
                    arbitration_id=arb_id,
                    data=data,
                    is_fd=is_fd,
                    is_extended_id=False,
                )
                self._bus.send(msg)
            self.tx_count += 1

    def send_periodic(self, arb_id: int, data: bytes,
                      period_s: float) -> PeriodicSender:
        """Start a periodic CAN frame sender. Returns handle to update data."""
        ps = PeriodicSender(self.send, arb_id, data, period_s)
        ps.start()
        self._periodic_senders.append(ps)
        return ps

    # ── Receive ───────────────────────────────────────────────────────────────

    def recv(self, timeout: float = 0.1) -> Optional[CANMessage]:
        """
        Blocking receive (for simple polling).
        Returns None on timeout.
        """
        if not self._bus:
            return None
        if _CAN_AVAILABLE and isinstance(self._bus, can.BusABC):
            raw = self._bus.recv(timeout=timeout)
            if raw:
                return CANMessage(
                    raw.arbitration_id,
                    bytes(raw.data),
                    raw.timestamp or time.monotonic(),
                    is_fd=getattr(raw, "is_fd", False),
                    is_error=raw.is_error_frame,
                )
        return None

    def latest(self, arb_id: int) -> Optional[CANMessage]:
        """Return the most recently received message for an arb_id."""
        with self._latest_lock:
            return self._latest.get(arb_id)

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def subscribe(self, arb_id: int, callback: Callable[[CANMessage], None]):
        """Register callback for a specific arb_id."""
        self._subscribers[arb_id].append(callback)

    def subscribe_all(self, callback: Callable[[CANMessage], None]):
        """Register callback for every received message."""
        self._wildcard_subs.append(callback)

    def unsubscribe(self, arb_id: int, callback: Callable):
        subs = self._subscribers.get(arb_id, [])
        if callback in subs:
            subs.remove(callback)

    # ── RX loop ───────────────────────────────────────────────────────────────

    def _rx_loop(self):
        while self._running:
            try:
                if _CAN_AVAILABLE and isinstance(self._bus, can.BusABC):
                    raw = self._bus.recv(timeout=self._cfg.timeout_s)
                    if raw is None:
                        continue
                    msg = CANMessage(
                        raw.arbitration_id,
                        bytes(raw.data),
                        raw.timestamp or time.monotonic(),
                        is_fd=getattr(raw, "is_fd", False),
                        is_error=raw.is_error_frame,
                    )
                    if msg.is_error:
                        self.error_count += 1
                        log.warning(f"CAN error frame on {self._cfg.channel}")
                        continue

                    self.rx_count += 1

                    with self._latest_lock:
                        self._latest[msg.arb_id] = msg

                    # Dispatch callbacks
                    for cb in self._subscribers.get(msg.arb_id, []):
                        try:
                            cb(msg)
                        except Exception as e:
                            log.error(f"Subscriber callback error: {e}")
                    for cb in self._wildcard_subs:
                        try:
                            cb(msg)
                        except Exception as e:
                            log.error(f"Wildcard subscriber error: {e}")

            except Exception as e:
                if self._running:
                    log.error(f"RX loop error: {e}")
                    self.error_count += 1

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "rx_count":    self.rx_count,
            "tx_count":    self.tx_count,
            "error_count": self.error_count,
            "channel":     self._cfg.channel,
        }


class _NullBus:
    """Null CAN bus for headless unit testing."""

    def recv(self, timeout=0.1):
        time.sleep(timeout)
        return None

    def send(self, msg):
        pass

    def shutdown(self):
        pass
