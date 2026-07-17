"""
ISO 15765-2 (ISO-TP) transport layer.

Two implementations share the same abstract base:

``MockIsoTpConnection``
    In-process simulation. Transparently used by :class:`~core.uds_client.MockUDSEngine`
    — callers never interact with it directly in mock mode.

``RealIsoTpConnection``
    Wraps *can-isotp* ``NotifierBasedCanStack`` over a live
    :class:`~core.vector_interface.RealVectorInterface` bus.  Falls back to a
    minimal manual single-frame implementation when *can-isotp* is absent
    (payloads ≤ 7 bytes only).

Factory
-------
::

    cfg  = IsoTpConfig(tx_id=0x7E0, rx_id=0x7E8)
    conn = build_isotp_connection(cfg, iface, mock=True)
    conn.open()
    raw_response = conn.send_and_recv(b"\\x10\\x03")   # DiagnosticSessionControl extended
    conn.close()

Timing defaults (ISO 14229-1):
    P2  server response timeout = 50 ms  (P2_DEFAULT)
    P2* extended response timeout = 5000 ms
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from .vector_interface import VectorInterfaceBase


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class IsoTpConfig:
    """ISO-TP addressing and timing parameters."""

    tx_id: int        = 0x7E0     # Tester → ECU physical CAN ID
    rx_id: int        = 0x7E8     # ECU → Tester response CAN ID
    func_id: int      = 0x7DF     # Functional (broadcast) CAN ID
    padding_byte: int = 0xAA      # CAN frame padding (some ECUs require 0xCC or 0xFF)
    stmin: int        = 0         # Separation time min [ms] between consecutive frames
    blocksize: int    = 0         # ISO-TP block size (0 = unlimited)
    p2_timeout_ms: int      = 150      # Default P2 server response timeout
    p2_star_timeout_ms: int = 5_000   # P2* extended response timeout


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class IsoTpConnectionBase(ABC):
    """Minimal transport interface consumed by :class:`~core.uds_client.UDSClient`."""

    @abstractmethod
    def open(self) -> None:
        """Initialise the transport channel."""

    @abstractmethod
    def close(self) -> None:
        """Release the transport channel."""

    @abstractmethod
    def send_and_recv(self, payload: bytes) -> bytes:
        """
        Send a UDS payload and return the raw response bytes.

        Handles ISO-TP segmentation/reassembly transparently.

        Raises:
            TimeoutError: No response within P2/P2* timeout.
        """

    def __enter__(self) -> "IsoTpConnectionBase":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------

class MockIsoTpConnection(IsoTpConnectionBase):
    """
    In-process ISO-TP stub — no CAN traffic generated.

    [MOCK/SIMULATED]

    Used internally by :class:`~core.uds_client.MockUDSEngine`.
    In mock mode the UDS client never calls ``send_and_recv``; instead
    it short-circuits directly to the mock response engine.  This class
    exists only as a concrete no-op so the fixture wiring still works.
    """

    def open(self) -> None:
        logger.debug("[MOCK] IsoTpConnection opened (simulated)")

    def close(self) -> None:
        logger.debug("[MOCK] IsoTpConnection closed")

    def send_and_recv(self, payload: bytes) -> bytes:
        # The UDSClient mock-path never calls this.
        raise NotImplementedError("MockIsoTpConnection.send_and_recv should never be called directly.")


# ---------------------------------------------------------------------------
# Real hardware implementation
# ---------------------------------------------------------------------------

class RealIsoTpConnection(IsoTpConnectionBase):
    """
    ISO-TP connection over a live CAN bus.

    Prefers the *can-isotp* library (``pip install can-isotp``).
    Falls back to a minimal manual framing path for single-frame payloads
    (≤ 7 bytes) when the library is unavailable.
    """

    def __init__(self, config: IsoTpConfig, interface: "VectorInterfaceBase") -> None:
        self._cfg = config
        self._iface = interface
        self._stack = None

    def open(self) -> None:
        try:
            import isotp  # type: ignore[import]
            self._use_lib = True
            addr = isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=self._cfg.tx_id,
                rxid=self._cfg.rx_id,
            )
            self._stack = isotp.CanStack(
                bus=self._iface._bus,   # expose underlying python-can bus
                address=addr,
                params={"blocksize": self._cfg.blocksize, "stmin": self._cfg.stmin},
            )
        except ImportError:
            logger.warning(
                "can-isotp not installed; falling back to manual single-frame ISO-TP. "
                "Install via: pip install can-isotp"
            )
            self._use_lib = False

    def close(self) -> None:
        self._stack = None

    def send_and_recv(self, payload: bytes) -> bytes:
        if self._use_lib and self._stack is not None:
            return self._send_via_lib(payload)
        return self._send_manual_sf(payload)

    # -- Private helpers -----------------------------------------------------

    def _send_via_lib(self, payload: bytes) -> bytes:
        """Use the can-isotp library stack."""
        assert self._stack is not None
        self._stack.send(payload)
        deadline = time.monotonic() + self._cfg.p2_timeout_ms / 1000.0
        while time.monotonic() < deadline:
            self._stack.process()
            if self._stack.available():
                return self._stack.recv()
            time.sleep(0.001)
        raise TimeoutError(
            f"No ISO-TP response within {self._cfg.p2_timeout_ms} ms "
            f"(TX=0x{self._cfg.tx_id:X} RX=0x{self._cfg.rx_id:X})"
        )

    def _send_manual_sf(self, payload: bytes) -> bytes:
        """Minimal single-frame ISO-TP (≤ 7 bytes payload only)."""
        if len(payload) > 7:
            raise NotImplementedError(
                "Manual ISO-TP path only supports single-frame payloads (≤ 7 bytes). "
                "Install can-isotp for multi-frame support."
            )
        from .vector_interface import CANFrame
        frame_bytes = bytes([len(payload)]) + payload
        frame_bytes = frame_bytes.ljust(8, bytes([self._cfg.padding_byte]))
        self._iface.send(CANFrame(arbitration_id=self._cfg.tx_id, data=frame_bytes))

        deadline = time.monotonic() + self._cfg.p2_timeout_ms / 1000.0
        while time.monotonic() < deadline:
            rx = self._iface.recv(timeout=0.01)
            if rx and rx.arbitration_id == self._cfg.rx_id:
                pci = rx.data[0]
                frame_type = (pci & 0xF0) >> 4
                if frame_type == 0x0:  # Single Frame
                    length = pci & 0x0F
                    return bytes(rx.data[1: 1 + length])
            time.sleep(0.001)
        raise TimeoutError(f"No ISO-TP response within {self._cfg.p2_timeout_ms} ms")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_isotp_connection(
    config: IsoTpConfig,
    interface: "VectorInterfaceBase",
    mock: bool = True,
) -> IsoTpConnectionBase:
    """
    Return the appropriate ISO-TP connection.

    Args:
        config:    ISO-TP addressing config.
        interface: Underlying CAN interface.
        mock:      If True, return a no-op mock; else real ISO-TP.
    """
    if mock:
        return MockIsoTpConnection()
    return RealIsoTpConnection(config, interface)
