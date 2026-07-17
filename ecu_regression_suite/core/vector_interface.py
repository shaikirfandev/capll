"""
Vector CAN/CAN-FD hardware interface with simulated mock mode.

Two concrete implementations share the same abstract base:

``MockVectorInterface``
    No hardware required.  All transmitted frames are logged with the
    **[MOCK]** prefix.  An internal RX queue allows tests to inject
    synthetic ECU responses via :meth:`inject_frame`.

``RealVectorInterface``
    Wraps *python-can* with the ``vector`` backend.  Requires the Vector
    XL Driver Library and a connected USB CAN device (VN1610, VN1630,
    CANcaseXL, etc.).

Factory
-------
::

    cfg  = VectorChannelConfig(channel=1, bitrate=500_000, mock=True)
    iface = build_vector_interface(cfg)
    iface.connect()

Assumption: 500 kbps classic CAN (ISO 14229 default). Change ``bitrate``
and set ``can_fd=True`` for CAN-FD nodes.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class VectorChannelConfig:
    """Parameters for a single Vector hardware channel."""

    channel: int      = 1            # 1-based channel number in Vector Hardware Config
    bitrate: int      = 500_000      # CAN bus bitrate in bps (classic CAN)
    fd_bitrate: int   = 2_000_000    # CAN-FD data-phase bitrate in bps
    can_fd: bool      = False        # Enable CAN-FD frame format
    app_name: str     = "ECURegressionSuite"
    mock: bool        = True         # True = simulated, False = real Vector hardware
    rx_queue_depth: int = 256        # Internal mock RX queue size


@dataclass
class CANFrame:
    """Minimal CAN / CAN-FD frame."""

    arbitration_id: int
    data: bytes
    is_fd: bool   = False
    timestamp: float = field(default_factory=time.monotonic)

    def __str__(self) -> str:
        return (
            f"CANFrame(id=0x{self.arbitration_id:03X} "
            f"data={self.data.hex(' ').upper()} fd={self.is_fd})"
        )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class VectorInterfaceBase(ABC):
    """Hardware-agnostic CAN interface contract."""

    @abstractmethod
    def connect(self) -> None:
        """Open the hardware channel."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the hardware channel."""

    @abstractmethod
    def send(self, frame: CANFrame) -> None:
        """Transmit a single CAN frame."""

    @abstractmethod
    def recv(self, timeout: float = 0.1) -> Optional[CANFrame]:
        """Receive a single frame; returns None on timeout."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the channel is open."""

    def __enter__(self) -> "VectorInterfaceBase":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------

class MockVectorInterface(VectorInterfaceBase):
    """
    Simulated Vector interface for CI / offline use.

    [MOCK/SIMULATED — no real hardware accessed]

    Tests inject synthetic ECU responses via :meth:`inject_frame`.
    The :class:`~core.uds_client.MockUDSEngine` uses this internally.
    """

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config = config
        self._connected = False
        self._rx_queue: Deque[CANFrame] = deque(maxlen=config.rx_queue_depth)

    # -- Lifecycle -----------------------------------------------------------

    def connect(self) -> None:
        self._connected = True
        logger.info("[MOCK] VectorInterface connected (simulated channel {})", self._config.channel)

    def disconnect(self) -> None:
        self._connected = False
        self._rx_queue.clear()
        logger.info("[MOCK] VectorInterface disconnected")

    def is_connected(self) -> bool:
        return self._connected

    # -- I/O -----------------------------------------------------------------

    def send(self, frame: CANFrame) -> None:
        if not self._connected:
            raise RuntimeError("VectorInterface not connected.")
        logger.debug("[MOCK] CAN TX  {}", frame)

    def recv(self, timeout: float = 0.1) -> Optional[CANFrame]:
        if not self._connected:
            raise RuntimeError("VectorInterface not connected.")
        if self._rx_queue:
            return self._rx_queue.popleft()
        time.sleep(min(timeout, 0.005))
        return None

    # -- Test helpers --------------------------------------------------------

    def inject_frame(self, arb_id: int, data: bytes) -> None:
        """Inject a synthetic ECU response frame into the RX queue."""
        if not self._config.mock:
            raise RuntimeError("inject_frame is only available in mock mode.")
        self._rx_queue.append(CANFrame(arbitration_id=arb_id, data=data))

    def clear_rx_queue(self) -> None:
        """Discard all pending mock frames."""
        self._rx_queue.clear()


# ---------------------------------------------------------------------------
# Real hardware implementation
# ---------------------------------------------------------------------------

class RealVectorInterface(VectorInterfaceBase):
    """
    Real Vector USB CAN interface via *python-can* (vector backend).

    Requires:
    - Vector XL Driver Library installed on the host machine.
    - ``pip install python-can[vector]``
    - A connected VN1610 / VN1630 / CANalyzer USB device.
    """

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config = config
        self._bus = None
        self._connected = False

    def connect(self) -> None:
        try:
            import can  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "python-can is required for hardware mode. "
                "Run: pip install python-can[vector]"
            ) from exc

        self._bus = can.interface.Bus(
            interface="vector",
            channel=self._config.channel - 1,   # python-can uses 0-based
            bitrate=self._config.bitrate,
            fd=self._config.can_fd,
            data_bitrate=self._config.fd_bitrate if self._config.can_fd else None,
            app_name=self._config.app_name,
        )
        self._connected = True
        logger.info(
            "VectorInterface connected: channel={} bitrate={} fd={}",
            self._config.channel,
            self._config.bitrate,
            self._config.can_fd,
        )

    def disconnect(self) -> None:
        if self._bus is not None:
            self._bus.shutdown()
            self._bus = None
        self._connected = False
        logger.info("VectorInterface disconnected")

    def is_connected(self) -> bool:
        return self._connected

    def send(self, frame: CANFrame) -> None:
        if not self._connected:
            raise RuntimeError("VectorInterface not connected.")
        import can  # type: ignore[import]
        msg = can.Message(
            arbitration_id=frame.arbitration_id,
            data=list(frame.data),
            is_extended_id=False,
            is_fd=frame.is_fd,
        )
        self._bus.send(msg, timeout=1.0)
        logger.debug("CAN TX  {}", frame)

    def recv(self, timeout: float = 0.1) -> Optional[CANFrame]:
        if not self._connected:
            raise RuntimeError("VectorInterface not connected.")
        msg = self._bus.recv(timeout=timeout)
        if msg is None:
            return None
        return CANFrame(
            arbitration_id=msg.arbitration_id,
            data=bytes(msg.data),
            is_fd=msg.is_fd,
            timestamp=msg.timestamp or time.monotonic(),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_vector_interface(config: VectorChannelConfig) -> VectorInterfaceBase:
    """
    Return the appropriate VectorInterface implementation.

    Args:
        config: Channel configuration.  Set ``config.mock=True`` for offline use.

    Returns:
        :class:`MockVectorInterface` when ``config.mock`` is True, else
        :class:`RealVectorInterface`.
    """
    if config.mock:
        return MockVectorInterface(config)
    return RealVectorInterface(config)
