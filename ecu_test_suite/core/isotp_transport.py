"""
ISO-TP (ISO 15765-2) transport layer setup.

Provides two connection implementations:

``MockIsoTpConnection``
    Fully in-process simulation — no sockets, no hardware.  A positive
    UDS response is auto-generated for every ``send()`` call.

``RealIsoTpConnection``
    Uses *can-isotp* ``NotifierBasedCanStack`` over a live ``can.BusABC``
    instance (obtained from :class:`~core.vector_interface.RealVectorInterface`).

Both expose the same ``IsoTpConnectionBase`` interface which is compatible
with *udsoncan*'s ``Client``.

Factory
-------
::

    conn = build_isotp_connection(config, bus=can_bus, mock=False)
    conn.open()
    # ... pass to uds_client ...
    conn.close()
"""
from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
@dataclass
class IsoTpConfig:
    """ISO-TP addressing and flow-control parameters."""

    tx_id:    int = 0x7DF   # Physical request CAN ID  (tester → ECU)
    rx_id:    int = 0x7E8   # Physical response CAN ID (ECU → tester)
    func_id:  int = 0x7DF   # Functional (broadcast) request CAN ID
    addressing_mode: str = "normal"  # "normal" | "extended" | "mixed"
    tx_padding: int = 0xAA  # Padding byte for CAN-FD frames
    stmin:      int = 0     # Separation time minimum [ms]; 0 = no delay
    blocksize:  int = 0     # Block size; 0 = unlimited


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class IsoTpConnectionBase(ABC):
    """
    Minimal connection interface expected by *udsoncan* ``Client``.

    Callers may also use it as a context manager::

        with build_isotp_connection(...) as conn:
            client = build_uds_client(conn)
    """

    @abstractmethod
    def open(self) -> None:
        """Open the transport channel."""

    @abstractmethod
    def close(self) -> None:
        """Close the transport channel."""

    @abstractmethod
    def send(self, data: bytes) -> None:
        """Send a diagnostic payload (already segmented by ISO-TP)."""

    @abstractmethod
    def wait_frame(self, timeout: float = 2.0) -> bytes:
        """
        Block until a complete ISO-TP PDU is received.

        Raises:
            TimeoutError: If no PDU arrives within *timeout* seconds.
        """

    @abstractmethod
    def empty_rxqueue(self) -> None:
        """Discard all pending inbound PDUs."""

    @abstractmethod
    def empty_txqueue(self) -> None:
        """Discard all pending outbound PDUs (no-op on most stacks)."""

    # Context manager support
    def __enter__(self) -> "IsoTpConnectionBase":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Mock connection
# ---------------------------------------------------------------------------
class MockIsoTpConnection(IsoTpConnectionBase):
    """
    Simulated ISO-TP connection — no socket or CAN bus required.

    Behaviour
    ---------
    * :meth:`send` logs the payload and enqueues a positive UDS response.
    * :meth:`wait_frame` dequeues and returns the next response.
    * :meth:`inject_response` lets tests pre-load specific raw responses.

    All log lines are prefixed with **[MOCK]**.
    """

    def __init__(self, config: IsoTpConfig) -> None:
        self._config    = config
        self._rx_buffer: list[bytes] = []
        self._is_open   = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def open(self) -> None:
        self._is_open = True
        logger.info(
            "[MOCK] ISO-TP open  TX=0x{:X}  RX=0x{:X}",
            self._config.tx_id,
            self._config.rx_id,
        )

    def close(self) -> None:
        self._is_open = False
        logger.info("[MOCK] ISO-TP closed")

    # ------------------------------------------------------------------
    # Data transfer
    # ------------------------------------------------------------------
    def send(self, data: bytes) -> None:
        logger.debug("[MOCK] ISO-TP SEND: {}", data.hex(" ").upper())
        self._auto_respond(data)

    def wait_frame(self, timeout: float = 2.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._rx_buffer:
                frame = self._rx_buffer.pop(0)
                logger.debug("[MOCK] ISO-TP RECV: {}", frame.hex(" ").upper())
                return frame
            time.sleep(0.001)
        raise TimeoutError(
            f"[MOCK] No ISO-TP frame available within {timeout}s"
        )

    def empty_rxqueue(self) -> None:
        self._rx_buffer.clear()

    def empty_txqueue(self) -> None:
        pass  # no outbound queue in mock mode

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------
    def inject_response(self, data: bytes) -> None:
        """Pre-load a specific raw response for the next :meth:`wait_frame`."""
        self._rx_buffer.append(data)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _auto_respond(self, request: bytes) -> None:
        """Generate a minimal positive UDS response for *request*."""
        if not request:
            return
        sid      = request[0]
        pos_sid  = sid + 0x40
        response = bytes([pos_sid]) + request[1:2] + b"\x00\x00\x00\x00"
        self._rx_buffer.append(response)


# ---------------------------------------------------------------------------
# Real ISO-TP connection
# ---------------------------------------------------------------------------
class RealIsoTpConnection(IsoTpConnectionBase):
    """
    Real ISO-TP connection using *can-isotp* ``NotifierBasedCanStack``.

    Prerequisites
    -------------
    * ``pip install can-isotp``
    * A connected ``can.BusABC`` instance (from :class:`~core.vector_interface.RealVectorInterface`).

    Args:
        config: ISO-TP addressing and flow-control parameters.
        bus:    An open *python-can* ``BusABC`` instance.
    """

    def __init__(self, config: IsoTpConfig, bus: object) -> None:
        self._config = config
        self._bus    = bus
        self._stack  = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def open(self) -> None:
        try:
            import isotp  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "can-isotp not installed.  Run: pip install can-isotp"
            ) from exc

        address_mode_map = {
            "normal":   "isotp.AddressingMode.Normal_11bits",
            "extended": "isotp.AddressingMode.Extended_11bits",
            "mixed":    "isotp.AddressingMode.Mixed_11bits_SID",
        }

        address = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=self._config.tx_id,
            rxid=self._config.rx_id,
        )
        params = {
            "stmin":      self._config.stmin,
            "blocksize":  self._config.blocksize,
            "tx_padding": self._config.tx_padding,
        }
        self._stack = isotp.NotifierBasedCanStack(
            bus     = self._bus,  # type: ignore[arg-type]
            address = address,
            params  = params,
        )
        self._stack.start()
        logger.info(
            "ISO-TP open  TX=0x{:X}  RX=0x{:X}",
            self._config.tx_id,
            self._config.rx_id,
        )

    def close(self) -> None:
        if self._stack is not None:
            self._stack.stop()
            self._stack = None
        logger.info("ISO-TP closed")

    # ------------------------------------------------------------------
    # Data transfer
    # ------------------------------------------------------------------
    def send(self, data: bytes) -> None:
        self._stack.send(data)  # type: ignore[union-attr]
        logger.debug("ISO-TP SEND: {}", data.hex(" ").upper())

    def wait_frame(self, timeout: float = 2.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._stack.available():  # type: ignore[union-attr]
                frame = self._stack.recv()  # type: ignore[union-attr]
                logger.debug("ISO-TP RECV: {}", frame.hex(" ").upper())
                return frame
            time.sleep(0.001)
        raise TimeoutError(f"No ISO-TP frame received within {timeout}s")

    def empty_rxqueue(self) -> None:
        while self._stack and self._stack.available():
            self._stack.recv()

    def empty_txqueue(self) -> None:
        pass  # NotifierBasedCanStack manages its own TX queue


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def build_isotp_connection(
    config: IsoTpConfig,
    bus: Optional[object] = None,
    mock: bool = False,
) -> IsoTpConnectionBase:
    """
    Return a :class:`MockIsoTpConnection` or :class:`RealIsoTpConnection`.

    Mock mode is forced when ``MOCK_HARDWARE`` env var is truthy.

    Args:
        config: ISO-TP parameters.
        bus:    Open ``can.BusABC`` (required when ``mock=False``).
        mock:   Explicitly request mock mode.
    """
    env_mock = os.environ.get("MOCK_HARDWARE", "0").lower() in ("1", "true", "yes")
    if mock or env_mock:
        return MockIsoTpConnection(config)
    if bus is None:
        raise ValueError(
            "A live can.BusABC instance is required for RealIsoTpConnection"
        )
    return RealIsoTpConnection(config, bus)
