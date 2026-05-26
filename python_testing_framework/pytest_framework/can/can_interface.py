"""
pytest_framework/can/can_interface.py

Enterprise ADAS Framework – CAN / CAN FD Bus Interface
=======================================================
Thread-safe abstraction over python-can.
Supports: PCAN, Vector XL, SocketCAN, Kvaser, IXXAT, virtual (CI).
Auto-loads DBC via cantools for signal decoding.
"""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.logger import get_logger

log = get_logger("can_interface")

try:
    import can
    import cantools
    _HAS_CAN = True
except ImportError:
    _HAS_CAN = False
    log.warning("python-can / cantools not installed — using virtual stub")


@dataclass
class CANFrame:
    """Normalised CAN / CAN FD frame."""
    timestamp: float
    can_id:    int
    data:      bytes
    is_fd:     bool = False
    is_remote: bool = False
    channel:   str  = ""
    dlc:       int  = field(init=False)

    def __post_init__(self) -> None:
        self.dlc = len(self.data)

    def __repr__(self) -> str:
        return (f"CANFrame(0x{self.can_id:03X}, "
                f"[{self.data.hex(' ')}], "
                f"{'FD' if self.is_fd else 'CAN'})")


class CANInterface:
    """
    Thread-safe CAN / CAN FD bus wrapper.

    Usage:
        with CANInterface(channel="PCAN_USBBUS1", interface="pcan") as bus:
            bus.send(0x120, bytes([0x02, 0x64]))
            frame = bus.receive(timeout_s=0.5)
    """

    def __init__(
        self,
        channel:    str = "virtual",
        interface:  str = "virtual",
        bitrate:    int = 500_000,
        fd_bitrate: int = 2_000_000,
        fd_enabled: bool = False,
        dbc_path:   str  = "",
    ) -> None:
        self._channel    = channel
        self._interface  = interface
        self._bitrate    = bitrate
        self._fd_bitrate = fd_bitrate
        self._fd         = fd_enabled
        self._dbc_path   = dbc_path
        self._bus: Optional[Any] = None
        self._db:  Optional[Any] = None
        self._rx_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._rx_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._tx_count = 0
        self._rx_count = 0

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "CANInterface":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.disconnect()

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self) -> None:
        if not _HAS_CAN:
            log.info("[CAN] python-can absent — virtual stub active")
            return
        kwargs: Dict[str, Any] = dict(
            channel=self._channel,
            interface=self._interface,
            bitrate=self._bitrate,
        )
        if self._fd:
            kwargs["fd"] = True
            kwargs["data_bitrate"] = self._fd_bitrate
        try:
            self._bus = can.Bus(**kwargs)
        except Exception as exc:
            log.error(f"[CAN] Bus open failed: {exc!r}")
            raise
        if self._dbc_path:
            try:
                self._db = cantools.database.load_file(self._dbc_path)
                log.info(f"[CAN] DBC loaded: {self._dbc_path}")
            except Exception as exc:
                log.warning(f"[CAN] DBC load failed: {exc!r}")
        self._start_rx_thread()
        log.info(f"[CAN] Connected: {self._interface}/{self._channel} "
                 f"{'FD' if self._fd else 'Classic'} @ {self._bitrate}")

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=2.0)
        if self._bus:
            try:
                self._bus.shutdown()
            except Exception:
                pass
        log.info(f"[CAN] Disconnected (tx={self._tx_count}, rx={self._rx_count})")

    # ── TX ────────────────────────────────────────────────────────────────────

    def send(
        self, can_id: int, data: bytes | list[int],
        is_fd: bool = False, is_remote: bool = False
    ) -> None:
        payload = bytes(data) if not isinstance(data, bytes) else data
        with self._lock:
            if self._bus is None:
                log.debug(f"[CAN stub] TX 0x{can_id:03X} [{payload.hex(' ')}]")
                self._tx_count += 1
                return
            msg = can.Message(
                arbitration_id=can_id,
                data=payload,
                is_fd=is_fd,
                is_remote_frame=is_remote,
                is_extended_id=can_id > 0x7FF,
            )
            try:
                self._bus.send(msg)
                self._tx_count += 1
            except can.CanError as exc:
                log.error(f"[CAN] TX error on 0x{can_id:03X}: {exc!r}")
                raise

    def send_periodic(
        self, can_id: int, data: bytes | list[int], period_s: float
    ) -> Any:
        """Start a periodic transmit task. Returns the task handle."""
        if self._bus is None:
            return None
        msg = can.Message(arbitration_id=can_id, data=bytes(data), is_fd=self._fd)
        return self._bus.send_periodic(msg, period_s)

    # ── RX ────────────────────────────────────────────────────────────────────

    def receive(self, timeout_s: float = 0.5) -> Optional[CANFrame]:
        try:
            return self._rx_queue.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def receive_all(self, timeout_s: float = 0.1) -> List[CANFrame]:
        deadline = time.monotonic() + timeout_s
        frames: List[CANFrame] = []
        while time.monotonic() < deadline:
            try:
                frames.append(self._rx_queue.get_nowait())
            except queue.Empty:
                break
        return frames

    def wait_for_id(
        self, can_id: int, timeout_s: float = 2.0
    ) -> Optional[CANFrame]:
        """Block until a frame with can_id arrives or timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            frame = self.receive(timeout_s=0.02)
            if frame and frame.can_id == can_id:
                return frame
        return None

    # ── Signal decoding ───────────────────────────────────────────────────────

    def decode(self, frame: CANFrame) -> Dict[str, Any]:
        """Decode CAN frame signals using loaded DBC. Returns {} if no DBC."""
        if self._db is None:
            return {}
        try:
            msg = self._db.get_message_by_frame_id(frame.can_id)
            return msg.decode(frame.data, decode_choices=False)
        except Exception:
            return {}

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def tx_count(self) -> int:
        return self._tx_count

    @property
    def rx_count(self) -> int:
        return self._rx_count

    def flush_rx(self) -> None:
        while not self._rx_queue.empty():
            self._rx_queue.get_nowait()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _start_rx_thread(self) -> None:
        self._rx_thread = threading.Thread(
            target=self._rx_loop, daemon=True, name="can-rx"
        )
        self._rx_thread.start()

    def _rx_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw = self._bus.recv(timeout=0.02)
                if raw is None:
                    continue
                frame = CANFrame(
                    timestamp=raw.timestamp,
                    can_id=raw.arbitration_id,
                    data=bytes(raw.data),
                    is_fd=raw.is_fd,
                    is_remote=raw.is_remote_frame,
                )
                self._rx_count += 1
                try:
                    self._rx_queue.put_nowait(frame)
                except queue.Full:
                    self._rx_queue.get_nowait()  # drop oldest
                    self._rx_queue.put_nowait(frame)
            except Exception:
                pass
