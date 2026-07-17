"""
Vector VN hardware interface abstraction.

Two concrete implementations behind a common base:

``MockVectorInterface``   — fully in-process, no hardware needed (CI/offline).
``RealVectorInterface``   — wraps *python-can* ``vector`` backend.

Use :func:`build_vector_interface` to get the right one.
All mock activity is tagged **[MOCK]** in log output.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class VectorChannelConfig:
    """Parameters for a single Vector hardware channel."""
    channel:    int  = 1
    bitrate:    int  = 500_000
    fd_bitrate: int  = 2_000_000
    can_fd:     bool = False
    app_name:   str  = "InfotainmentTestSuite"


@dataclass
class CANFrame:
    """Minimal CAN / CAN-FD frame."""
    arbitration_id:  int
    data:            bytes
    is_fd:           bool  = False
    is_remote_frame: bool  = False
    timestamp:       float = 0.0

    def __str__(self) -> str:
        return f"CANFrame(id=0x{self.arbitration_id:X} data={self.data.hex(' ').upper()})"


class VectorInterfaceBase(ABC):
    """Abstract base — all Vector interface implementations conform to this."""

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def send(self, frame: CANFrame) -> None: ...

    @abstractmethod
    def recv(self, timeout: float = 1.0) -> Optional[CANFrame]: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    def __enter__(self) -> "VectorInterfaceBase":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()


class MockVectorInterface(VectorInterfaceBase):
    """
    Simulated Vector interface.  No hardware required.
    A positive UDS response is auto-generated for every transmitted frame.
    """

    _POS_RESPONSE_OFFSET = 0x40

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config    = config
        self._connected = False
        self._rx_queue: list[CANFrame] = []

    def connect(self) -> None:
        self._connected = True
        logger.info(
            "[MOCK] Connected — ch={} bitrate={} CAN-FD={}",
            self._config.channel, self._config.bitrate, self._config.can_fd,
        )

    def disconnect(self) -> None:
        self._connected = False
        logger.info("[MOCK] Disconnected")

    def is_connected(self) -> bool:
        return self._connected

    def send(self, frame: CANFrame) -> None:
        if not self._connected:
            raise RuntimeError("MockVectorInterface: not connected")
        logger.debug("[MOCK] TX  {}", frame)
        self._inject_response(frame)

    def recv(self, timeout: float = 1.0) -> Optional[CANFrame]:
        if self._rx_queue:
            f = self._rx_queue.pop(0)
            logger.debug("[MOCK] RX  {}", f)
            return f
        return None

    def inject_frame(self, frame: CANFrame) -> None:
        """Test helper — push a frame into the RX queue."""
        self._rx_queue.append(frame)

    def _inject_response(self, req: CANFrame) -> None:
        if not req.data:
            return
        pos_sid  = req.data[0] + self._POS_RESPONSE_OFFSET
        resp_data = bytes([pos_sid]) + req.data[1:2] + b"\x00\x00\x00\x00"
        self._rx_queue.append(
            CANFrame(arbitration_id=req.arbitration_id + 0x08, data=resp_data)
        )


class RealVectorInterface(VectorInterfaceBase):
    """Real Vector VN device backed by python-can ``vector`` backend."""

    def __init__(self, config: VectorChannelConfig) -> None:
        self._config = config
        self._bus    = None  # type: ignore[assignment]

    def connect(self) -> None:
        try:
            import can  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("pip install python-can[vector]") from exc

        kw: dict = dict(
            interface = "vector",
            channel   = self._config.channel - 1,  # python-can: 0-based
            bitrate   = self._config.bitrate,
            app_name  = self._config.app_name,
        )
        if self._config.can_fd:
            kw.update(fd=True, data_bitrate=self._config.fd_bitrate)
        self._bus = can.Bus(**kw)
        logger.info("Connected  ch={} bitrate={}", self._config.channel, self._config.bitrate)

    def disconnect(self) -> None:
        if self._bus is not None:
            self._bus.shutdown()
            self._bus = None
        logger.info("Disconnected")

    def is_connected(self) -> bool:
        return self._bus is not None

    def send(self, frame: CANFrame) -> None:
        import can  # type: ignore[import]
        self._bus.send(can.Message(
            arbitration_id  = frame.arbitration_id,
            data            = frame.data,
            is_fd           = frame.is_fd,
            is_remote_frame = frame.is_remote_frame,
            is_extended_id  = False,
        ))
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


def build_vector_interface(
    config: VectorChannelConfig,
    mock: bool = False,
) -> VectorInterfaceBase:
    """Factory — returns mock or real interface based on *mock* flag or env var."""
    env_mock = os.environ.get("MOCK_HARDWARE", "1").lower() in ("1", "true", "yes")
    if mock or env_mock:
        logger.warning("[MOCK] Hardware mock mode ACTIVE — no Vector device required")
        return MockVectorInterface(config)
    return RealVectorInterface(config)
