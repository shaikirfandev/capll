"""
ISO-TP (ISO 15765-2) transport layer.

``MockIsoTpConnection``   — in-process simulation, auto-responds with positive UDS frames.
``RealIsoTpConnection``   — uses can-isotp NotifierBasedCanStack.

Use :func:`build_isotp_connection` factory.
"""
from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class IsoTpConfig:
    tx_id:   int  = 0x730
    rx_id:   int  = 0x738
    func_id: int  = 0x7DF
    addressing_mode: str = "normal"
    tx_padding: int = 0xAA
    stmin:      int = 0
    blocksize:  int = 0


class IsoTpConnectionBase(ABC):
    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def send(self, data: bytes) -> None: ...

    @abstractmethod
    def wait_frame(self, timeout: float = 2.0) -> bytes: ...

    @abstractmethod
    def empty_rxqueue(self) -> None: ...

    @abstractmethod
    def empty_txqueue(self) -> None: ...

    def __enter__(self) -> "IsoTpConnectionBase":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class MockIsoTpConnection(IsoTpConnectionBase):
    """Simulated ISO-TP connection — no socket or hardware required."""

    def __init__(self, config: IsoTpConfig) -> None:
        self._config    = config
        self._rx_buffer: list[bytes] = []
        self._is_open   = False

    def open(self) -> None:
        self._is_open = True
        logger.info("[MOCK] ISO-TP open  TX=0x{:X}  RX=0x{:X}", self._config.tx_id, self._config.rx_id)

    def close(self) -> None:
        self._is_open = False
        logger.info("[MOCK] ISO-TP closed")

    def send(self, data: bytes) -> None:
        logger.debug("[MOCK] ISO-TP SEND: {}", data.hex(" ").upper())
        if data:
            self._rx_buffer.append(bytes([data[0] + 0x40]) + data[1:2] + b"\x00\x00\x00\x00")

    def wait_frame(self, timeout: float = 2.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._rx_buffer:
                frame = self._rx_buffer.pop(0)
                logger.debug("[MOCK] ISO-TP RECV: {}", frame.hex(" ").upper())
                return frame
            time.sleep(0.001)
        raise TimeoutError(f"[MOCK] No frame within {timeout}s")

    def empty_rxqueue(self) -> None:
        self._rx_buffer.clear()

    def empty_txqueue(self) -> None:
        pass

    def inject_response(self, data: bytes) -> None:
        """Pre-load a specific response for testing negative paths."""
        self._rx_buffer.insert(0, data)


class RealIsoTpConnection(IsoTpConnectionBase):
    """Real ISO-TP via can-isotp NotifierBasedCanStack."""

    def __init__(self, config: IsoTpConfig, bus: object) -> None:
        self._config = config
        self._bus    = bus
        self._stack  = None

    def open(self) -> None:
        try:
            import isotp  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("pip install can-isotp") from exc

        address = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=self._config.tx_id,
            rxid=self._config.rx_id,
        )
        self._stack = isotp.NotifierBasedCanStack(
            bus     = self._bus,   # type: ignore[arg-type]
            address = address,
            params  = dict(
                stmin      = self._config.stmin,
                blocksize  = self._config.blocksize,
                tx_padding = self._config.tx_padding,
            ),
        )
        self._stack.start()
        logger.info("ISO-TP open  TX=0x{:X}  RX=0x{:X}", self._config.tx_id, self._config.rx_id)

    def close(self) -> None:
        if self._stack is not None:
            self._stack.stop()
            self._stack = None
        logger.info("ISO-TP closed")

    def send(self, data: bytes) -> None:
        self._stack.send(data)  # type: ignore[union-attr]
        logger.debug("ISO-TP SEND: {}", data.hex(" ").upper())

    def wait_frame(self, timeout: float = 2.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._stack.available():  # type: ignore[union-attr]
                f = self._stack.recv()   # type: ignore[union-attr]
                logger.debug("ISO-TP RECV: {}", f.hex(" ").upper())
                return f
            time.sleep(0.001)
        raise TimeoutError(f"No frame within {timeout}s")

    def empty_rxqueue(self) -> None:
        while self._stack and self._stack.available():
            self._stack.recv()

    def empty_txqueue(self) -> None:
        pass


def build_isotp_connection(
    config: IsoTpConfig,
    bus: Optional[object] = None,
    mock: bool = False,
) -> IsoTpConnectionBase:
    env_mock = os.environ.get("MOCK_HARDWARE", "1").lower() in ("1", "true", "yes")
    if mock or env_mock:
        return MockIsoTpConnection(config)
    if bus is None:
        raise ValueError("A live can.BusABC is required for RealIsoTpConnection")
    return RealIsoTpConnection(config, bus)
