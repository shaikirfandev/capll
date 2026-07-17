"""
Vector VN hardware interface abstraction.

Provides a hardware-agnostic base class and two concrete implementations:

  ``MockVectorInterface``
      Simulates a Vector device for offline development and CI.  All mock
      activity is clearly tagged with **[MOCK]** in log output.

  ``RealVectorInterface``
      Wraps *python-can* with the ``vector`` backend.  Requires the Vector
      XL Driver Library (``xlwrap.dll`` / ``libxl.so``) and a connected
      VN1610 / VN1630 / CANcaseXL device.

Factory
-------
Use :func:`build_vector_interface` to obtain the right implementation::

    iface = build_vector_interface(config, mock=False)
    iface.connect()
    # ... use iface ...
    iface.disconnect()

Switching to mock mode without code changes::

    MOCK_HARDWARE=1 python -m cli.main
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class VectorChannelConfig:
    """Parameters for a single Vector hardware channel."""

    channel: int   = 1          # 1-based channel number shown in Vector Hardware Config
    bitrate: int   = 500_000    # CAN bitrate in bps (classic CAN)
    fd_bitrate: int = 2_000_000 # CAN-FD data-phase bitrate in bps
    can_fd: bool   = False      # Enable CAN-FD frame format
    app_name: str  = "ECU_Test_Suite"


@dataclass
class CANFrame:
    """Minimal CAN / CAN-FD frame representation."""

    arbitration_id:   int
    data:             bytes
    is_fd:            bool  = False
    is_remote_frame:  bool  = False
    timestamp:        float = 0.0

    def __str__(self) -> str:
        return (
            f"CANFrame(id=0x{self.arbitration_id:X}, "
            f"data={self.data.hex(' ').upper()}, fd={self.is_fd})"
        )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class VectorInterfaceBase(ABC):
    """Abstract base class — all Vector interface implementations conform to this."""

    @abstractmethod
    def connect(self) -> None:
        """Open the hardware channel and start the CAN stack."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the hardware channel and release the driver handle."""

    @abstractmethod
    def send(self, frame: CANFrame) -> None:
        """Transmit a single CAN / CAN-FD frame."""

    @abstractmethod
    def recv(self, timeout: float = 1.0) -> Optional[CANFrame]:
        """
        Receive a single CAN frame, blocking up to *timeout* seconds.

        Returns ``None`` if no frame arrives within the timeout window.
        """

    @abstractmethod
    def is_connected(self) -> bool:
        """Return ``True`` if the channel is currently open."""

    # Context-manager support
    def __enter__(self) -> "VectorInterfaceBase":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------
class MockVectorInterface(VectorInterfaceBase):
    """
    Simulated Vector interface for offline development and CI.

    On every :meth:`send` call a plausible positive UDS response
    (SID + 0x40) is pushed into an internal RX queue so that the ISO-TP
    and UDS layers above see a responding ECU.

    .. note::
        All log messages are prefixed with **[MOCK]**.
    """

    _POS_RESPONSE_OFFSET: int = 0x40

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config    = config
        self._connected = False
        self._rx_queue: list[CANFrame] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def connect(self) -> None:
        self._connected = True
        logger.info(
            "[MOCK] Connected — ch={} bitrate={} CAN-FD={}",
            self._config.channel,
            self._config.bitrate,
            self._config.can_fd,
        )

    def disconnect(self) -> None:
        self._connected = False
        logger.info("[MOCK] Disconnected")

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Frame I/O
    # ------------------------------------------------------------------
    def send(self, frame: CANFrame) -> None:
        if not self._connected:
            raise RuntimeError("MockVectorInterface: not connected — call connect() first")
        logger.debug("[MOCK] TX  {}", frame)
        self._inject_mock_response(frame)

    def recv(self, timeout: float = 1.0) -> Optional[CANFrame]:
        if self._rx_queue:
            frame = self._rx_queue.pop(0)
            logger.debug("[MOCK] RX  {}", frame)
            return frame
        return None

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def inject_frame(self, frame: CANFrame) -> None:
        """Manually push a frame into the RX queue (for test stubbing)."""
        self._rx_queue.append(frame)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _inject_mock_response(self, request: CANFrame) -> None:
        """Synthesise a positive UDS response for the request frame."""
        if not request.data:
            return
        service_id    = request.data[0]
        positive_sid  = service_id + self._POS_RESPONSE_OFFSET
        # Echo sub-function byte + pad to 6 bytes total
        resp_payload  = bytes([positive_sid]) + request.data[1:2] + b"\x00\x00\x00\x00"
        response = CANFrame(
            arbitration_id = request.arbitration_id + 0x08,  # conventional ECU reply offset
            data           = resp_payload,
        )
        self._rx_queue.append(response)


# ---------------------------------------------------------------------------
# Real Vector implementation
# ---------------------------------------------------------------------------
class RealVectorInterface(VectorInterfaceBase):
    """
    Real Vector VN hardware interface backed by *python-can* ``vector`` backend.

    Prerequisites
    -------------
    - Vector XL Driver Library installed on the host PC.
    - ``pip install python-can[vector]``
    - VN device appears in **Vector Hardware Config** at the selected channel.

    .. warning::
        ``channel`` is **1-based** in this class (matching Vector Hardware Config)
        but *python-can* uses a **0-based** index internally — the conversion is
        handled automatically.
    """

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config = config
        self._bus    = None  # type: ignore[assignment]

    def connect(self) -> None:
        try:
            import can  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "python-can is not installed.  Run: pip install python-can[vector]"
            ) from exc

        bus_kwargs: dict = {
            "interface": "vector",
            "channel":   self._config.channel - 1,  # python-can: 0-based
            "bitrate":   self._config.bitrate,
            "app_name":  self._config.app_name,
        }
        if self._config.can_fd:
            bus_kwargs.update(fd=True, data_bitrate=self._config.fd_bitrate)

        self._bus = can.Bus(**bus_kwargs)
        logger.info(
            "Connected — ch={} bitrate={} CAN-FD={}",
            self._config.channel,
            self._config.bitrate,
            self._config.can_fd,
        )

    def disconnect(self) -> None:
        if self._bus is not None:
            self._bus.shutdown()
            self._bus = None
        logger.info("Disconnected from Vector hardware")

    def is_connected(self) -> bool:
        return self._bus is not None

    def send(self, frame: CANFrame) -> None:
        import can  # type: ignore[import]

        msg = can.Message(
            arbitration_id = frame.arbitration_id,
            data           = frame.data,
            is_fd          = frame.is_fd,
            is_remote_frame= frame.is_remote_frame,
            is_extended_id = False,
        )
        self._bus.send(msg)
        logger.debug("TX  {}", frame)

    def recv(self, timeout: float = 1.0) -> Optional[CANFrame]:
        msg = self._bus.recv(timeout=timeout)
        if msg is None:
            return None
        return CANFrame(
            arbitration_id  = msg.arbitration_id,
            data            = bytes(msg.data),
            is_fd           = getattr(msg, "is_fd", False),
            is_remote_frame = msg.is_remote_frame,
            timestamp       = msg.timestamp,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def build_vector_interface(
    config: VectorChannelConfig,
    mock: bool = False,
) -> VectorInterfaceBase:
    """
    Return a :class:`MockVectorInterface` or :class:`RealVectorInterface`.

    Mock mode is forced when the environment variable ``MOCK_HARDWARE`` is
    set to ``1``, ``true``, or ``yes`` (case-insensitive).

    Args:
        config: Channel parameters.
        mock:   Explicitly request mock mode (overrides env var default).
    """
    env_mock = os.environ.get("MOCK_HARDWARE", "0").lower() in ("1", "true", "yes")
    if mock or env_mock:
        logger.warning(
            "[MOCK] Hardware mock mode ACTIVE — no real Vector device required"
        )
        return MockVectorInterface(config)
    return RealVectorInterface(config)
