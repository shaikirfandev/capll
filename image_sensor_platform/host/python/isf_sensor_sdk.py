"""
isf_sensor_sdk.py
=================
Python host SDK for the Industrial Image Sensor Firmware Platform.

Provides:
  - SensorDevice     : USB/UART/Ethernet connection management
  - SensorControl    : Register read/write, gain/exposure/FPS control
  - FrameCapture     : Frame acquisition, pixel format decoding
  - DiagnosticsClient: DTC reading, health monitoring, trace log streaming
  - FirmwareUpdater  : OTA firmware update with CRC verification

Typical usage:
    from isf_sensor_sdk import SensorDevice, SensorControl, FrameCapture

    with SensorDevice.open_usb(vid=0x1234, pid=0x0001) as dev:
        ctrl = SensorControl(dev)
        ctrl.configure(width=1920, height=1080, fps=30, gain_x100=150, exposure_us=5000)
        ctrl.start()
        with FrameCapture(dev) as cap:
            for frame in cap.stream(count=10):
                print(f"Frame {frame.sequence}: {frame.width}x{frame.height} "
                      f"ts={frame.timestamp_us}")
        ctrl.stop()

Copyright (c) 2026 Industrial Vision Systems.
"""

from __future__ import annotations

import struct
import time
import threading
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Optional, Iterator, Callable

import numpy as np  # type: ignore

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Protocol constants (must match firmware host_comm_protocol.h)
# ─────────────────────────────────────────────────────────────────────────────
_PROTO_MAGIC       = 0xISF1
_CMD_REG_READ      = 0x01
_CMD_REG_WRITE     = 0x02
_CMD_CONFIGURE     = 0x10
_CMD_START         = 0x11
_CMD_STOP          = 0x12
_CMD_GET_STATS     = 0x20
_CMD_GET_DTC       = 0x21
_CMD_CLEAR_DTC     = 0x22
_CMD_FW_UPDATE     = 0x30
_CMD_FRAME_REQ     = 0x40
_CMD_GET_CAPS      = 0x50

_RESP_OK           = 0x00
_RESP_ERR          = 0x01
_RESP_NAK          = 0x02

_FRAME_HEADER_MAGIC = b'\xDE\xAD\xBE\xEF'
_FRAME_HEADER_FMT   = '<4sIIIIHBBHHhHH'  # 36 bytes
_FRAME_HEADER_SIZE  = struct.calcsize(_FRAME_HEADER_FMT)

# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────
class PixelFormat(IntEnum):
    RAW8   = 0x00
    RAW10  = 0x01
    RAW12  = 0x02
    RAW16  = 0x04
    YUV422 = 0x10
    RGB888 = 0x20
    MONO8  = 0x30

class HdrMode(IntEnum):
    DISABLED = 0
    TWO_FRAME = 1
    DOL = 3

# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SensorConfig:
    """Configuration request to send to the firmware."""
    width:        int = 1920
    height:       int = 1080
    fps:          int = 30
    pixel_format: PixelFormat = PixelFormat.RAW12
    gain_x100:    int = 100       # 100 = 1×
    exposure_us:  int = 10000
    hdr_mode:     HdrMode = HdrMode.DISABLED
    test_pattern: bool = False
    test_pattern_id: int = 0


@dataclass
class FrameData:
    """Decoded frame from the sensor."""
    sequence:     int
    timestamp_us: int
    width:        int
    height:       int
    pixel_format: PixelFormat
    gain_x100:    int
    exposure_us:  int
    temperature_c_x10: int
    ecc_errors:   int
    crc_errors:   int
    flags:        int
    pixels:       np.ndarray   # Shape: (height, width) or (height, width, channels)

    @property
    def temperature_c(self) -> float:
        return self.temperature_c_x10 / 10.0

    @property
    def gain(self) -> float:
        return self.gain_x100 / 100.0


@dataclass
class DiagnosticEvent:
    dtc_code: int
    status:   int   # 0=clear,1=pending,2=confirmed,3=aged
    occurrence_count: int
    first_occurrence_us: int
    last_occurrence_us: int

    STATUS_NAMES = {0: "Clear", 1: "Pending", 2: "Confirmed", 3: "Aged"}

    @property
    def status_name(self) -> str:
        return self.STATUS_NAMES.get(self.status, "Unknown")


@dataclass
class SensorCapabilities:
    modes: list
    min_gain_x100: int
    max_gain_x100: int
    min_exposure_us: int
    max_exposure_us: int
    has_hdr: bool
    has_trigger: bool
    has_temperature: bool


@dataclass
class RuntimeStats:
    frames_captured:    int
    frames_dropped:     int
    ecc_errors:         int
    crc_errors:         int
    current_fps_x10:    int
    current_gain_x100:  int
    current_exposure_us: int
    temperature_c_x10:  int

    @property
    def fps(self) -> float:
        return self.current_fps_x10 / 10.0

    @property
    def temperature_c(self) -> float:
        return self.temperature_c_x10 / 10.0

    @property
    def drop_rate(self) -> float:
        total = self.frames_captured + self.frames_dropped
        return self.frames_dropped / total if total > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Transport layer
# ─────────────────────────────────────────────────────────────────────────────
class _Transport:
    """Abstract transport — USB, UART, or TCP."""
    def send(self, data: bytes) -> None: raise NotImplementedError
    def recv(self, n: int, timeout: float = 2.0) -> bytes: raise NotImplementedError
    def close(self) -> None: raise NotImplementedError


class _UsbTransport(_Transport):
    def __init__(self, vid: int, pid: int, timeout: float = 2.0):
        try:
            import usb.core  # type: ignore
            self._dev = usb.core.find(idVendor=vid, idProduct=pid)
            if self._dev is None:
                raise ConnectionError(f"USB device {vid:04X}:{pid:04X} not found")
            self._dev.set_configuration()
            self._ep_out = self._dev[0][(0, 0)][0]
            self._ep_in  = self._dev[0][(0, 0)][1]
            self._timeout_ms = int(timeout * 1000)
            logger.info(f"USB connected: {vid:04X}:{pid:04X}")
        except ImportError:
            raise RuntimeError("pyusb not installed: pip install pyusb")

    def send(self, data: bytes) -> None:
        self._dev.write(self._ep_out, data, timeout=self._timeout_ms)

    def recv(self, n: int, timeout: float = 2.0) -> bytes:
        return bytes(self._dev.read(self._ep_in, n, timeout=int(timeout * 1000)))

    def close(self) -> None:
        pass  # pyusb handles cleanup


class _UartTransport(_Transport):
    def __init__(self, port: str, baudrate: int = 921600, timeout: float = 2.0):
        import serial  # type: ignore
        self._ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        logger.info(f"UART connected: {port} @ {baudrate}")

    def send(self, data: bytes) -> None:
        self._ser.write(data)

    def recv(self, n: int, timeout: float = 2.0) -> bytes:
        self._ser.timeout = timeout
        return self._ser.read(n)

    def close(self) -> None:
        self._ser.close()


class _TcpTransport(_Transport):
    def __init__(self, host: str, port: int, timeout: float = 2.0):
        import socket
        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._sock.settimeout(timeout)
        logger.info(f"TCP connected: {host}:{port}")

    def send(self, data: bytes) -> None:
        self._sock.sendall(data)

    def recv(self, n: int, timeout: float = 2.0) -> bytes:
        self._sock.settimeout(timeout)
        buf = b''
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed by remote")
            buf += chunk
        return buf

    def close(self) -> None:
        self._sock.close()


# ─────────────────────────────────────────────────────────────────────────────
# SensorDevice — connection lifecycle
# ─────────────────────────────────────────────────────────────────────────────
class SensorDevice:
    """Manages the physical connection to the sensor firmware."""

    def __init__(self, transport: _Transport):
        self._transport = transport
        self._seq = 0
        self._lock = threading.Lock()

    @classmethod
    def open_usb(cls, vid: int = 0x1234, pid: int = 0x0001) -> "SensorDevice":
        return cls(_UsbTransport(vid, pid))

    @classmethod
    def open_uart(cls, port: str, baudrate: int = 921600) -> "SensorDevice":
        return cls(_UartTransport(port, baudrate))

    @classmethod
    def open_tcp(cls, host: str = "192.168.1.100", port: int = 5000) -> "SensorDevice":
        return cls(_TcpTransport(host, port))

    def __enter__(self) -> "SensorDevice":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

    def _build_command(self, cmd_id: int, payload: bytes = b'') -> bytes:
        """Build a framed command packet: [MAGIC:2][SEQ:2][CMD:1][LEN:2][PAYLOAD:N][CRC:2]"""
        with self._lock:
            seq = self._seq
            self._seq = (self._seq + 1) & 0xFFFF
        frame = struct.pack('<HHBH', _PROTO_MAGIC, seq, cmd_id, len(payload)) + payload
        crc = _crc16(frame)
        return frame + struct.pack('<H', crc)

    def send_command(self, cmd_id: int, payload: bytes = b'', timeout: float = 2.0) -> bytes:
        """Send a command and return the response payload."""
        pkt = self._build_command(cmd_id, payload)
        with self._lock:
            self._transport.send(pkt)
            # Read response header: [MAGIC:2][SEQ:2][STATUS:1][LEN:2]
            hdr = self._transport.recv(7, timeout=timeout)
            magic, seq, status, resp_len = struct.unpack('<HHBH', hdr)
            if magic != _PROTO_MAGIC:
                raise IOError(f"Bad response magic: 0x{magic:04X}")
            if status == _RESP_ERR:
                raise RuntimeError("Firmware returned error response")
            resp_payload = self._transport.recv(resp_len + 2, timeout=timeout)  # +2 for CRC
            return resp_payload[:-2]  # Strip CRC


def _crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
        crc &= 0xFFFF
    return crc


# ─────────────────────────────────────────────────────────────────────────────
# SensorControl
# ─────────────────────────────────────────────────────────────────────────────
class SensorControl:
    """Configure and control the image sensor."""

    def __init__(self, device: SensorDevice):
        self._dev = device

    def configure(self, **kwargs) -> None:
        """Configure sensor. Keyword args map to SensorConfig fields."""
        cfg = SensorConfig(**kwargs)
        payload = struct.pack(
            '<HHHBBHHBBBB',
            cfg.width, cfg.height, cfg.fps,
            int(cfg.pixel_format), int(cfg.hdr_mode),
            cfg.gain_x100, cfg.exposure_us,
            int(cfg.test_pattern), cfg.test_pattern_id, 0, 0
        )
        self._dev.send_command(_CMD_CONFIGURE, payload)
        logger.info(f"Configured: {cfg.width}x{cfg.height}@{cfg.fps}fps "
                    f"gain={cfg.gain_x100/100:.2f}x exp={cfg.exposure_us}us")

    def start(self) -> None:
        self._dev.send_command(_CMD_START)
        logger.info("Sensor streaming started")

    def stop(self) -> None:
        self._dev.send_command(_CMD_STOP)
        logger.info("Sensor streaming stopped")

    def set_gain(self, gain_x100: int) -> None:
        self._dev.send_command(_CMD_REG_WRITE,
                               struct.pack('<HH', 0x0204, gain_x100))

    def set_exposure(self, exposure_us: int) -> None:
        self._dev.send_command(_CMD_REG_WRITE,
                               struct.pack('<HI', 0x0202, exposure_us))

    def read_register(self, reg_addr: int) -> int:
        resp = self._dev.send_command(_CMD_REG_READ, struct.pack('<H', reg_addr))
        return struct.unpack('<H', resp[:2])[0]

    def write_register(self, reg_addr: int, value: int) -> None:
        self._dev.send_command(_CMD_REG_WRITE, struct.pack('<HH', reg_addr, value))

    def get_stats(self) -> RuntimeStats:
        resp = self._dev.send_command(_CMD_GET_STATS)
        f = struct.unpack('<QQIIIHIh', resp[:38])
        return RuntimeStats(
            frames_captured=f[0], frames_dropped=f[1],
            ecc_errors=f[2], crc_errors=f[3], current_fps_x10=f[4],
            current_gain_x100=f[5], current_exposure_us=f[6],
            temperature_c_x10=f[7]
        )

    def get_capabilities(self) -> SensorCapabilities:
        resp = self._dev.send_command(_CMD_GET_CAPS)
        mode_count = resp[0]
        modes = []
        offset = 1
        for _ in range(mode_count):
            w, h, fps_max, fmt, lanes = struct.unpack_from('<HHHBB', resp, offset)
            modes.append({'width': w, 'height': h, 'fps_max': fps_max,
                          'format': PixelFormat(fmt), 'lanes': lanes})
            offset += 8
        min_gain, max_gain, min_exp, max_exp, flags = struct.unpack_from('<HHIII', resp, offset)
        return SensorCapabilities(
            modes=modes, min_gain_x100=min_gain, max_gain_x100=max_gain,
            min_exposure_us=min_exp, max_exposure_us=max_exp,
            has_hdr=bool(flags & 0x01), has_trigger=bool(flags & 0x02),
            has_temperature=bool(flags & 0x04)
        )


# ─────────────────────────────────────────────────────────────────────────────
# FrameCapture
# ─────────────────────────────────────────────────────────────────────────────
class FrameCapture:
    """Acquire frames from the streaming pipeline."""

    def __init__(self, device: SensorDevice):
        self._dev = device
        self._active = False

    def __enter__(self) -> "FrameCapture":
        self._active = True
        return self

    def __exit__(self, *_) -> None:
        self._active = False

    def capture_one(self, timeout: float = 5.0) -> FrameData:
        """Request and receive a single frame."""
        self._dev.send_command(_CMD_FRAME_REQ)
        # Receive frame header
        raw_hdr = self._dev._transport.recv(_FRAME_HEADER_SIZE, timeout=timeout)
        fields = struct.unpack(_FRAME_HEADER_FMT, raw_hdr)
        magic, seq, ts_us, width, height, gain, pix_fmt, vc, exp, ecc, temp, crc_err, flags = fields
        assert fields[0] == _FRAME_HEADER_MAGIC, "Bad frame magic"

        # Calculate expected pixel data size
        bpp_map = {
            PixelFormat.RAW8:  1,  PixelFormat.RAW10: 2, PixelFormat.RAW12: 2,
            PixelFormat.RAW16: 2,  PixelFormat.YUV422: 2, PixelFormat.RGB888: 3,
            PixelFormat.MONO8: 1,
        }
        bpp = bpp_map.get(PixelFormat(pix_fmt), 2)
        data_size = int(width) * int(height) * bpp
        raw_pixels = self._dev._transport.recv(data_size, timeout=timeout)

        # Convert to numpy array
        if bpp == 2:
            pixels = np.frombuffer(raw_pixels, dtype=np.uint16).reshape(height, width)
        elif bpp == 3:
            pixels = np.frombuffer(raw_pixels, dtype=np.uint8).reshape(height, width, 3)
        else:
            pixels = np.frombuffer(raw_pixels, dtype=np.uint8).reshape(height, width)

        return FrameData(
            sequence=seq, timestamp_us=ts_us,
            width=width, height=height,
            pixel_format=PixelFormat(pix_fmt),
            gain_x100=gain, exposure_us=exp,
            temperature_c_x10=temp,
            ecc_errors=ecc, crc_errors=crc_err, flags=flags,
            pixels=pixels
        )

    def stream(self, count: int = -1, timeout: float = 5.0) -> Iterator[FrameData]:
        """Generator that yields frames. count=-1 streams indefinitely."""
        captured = 0
        while self._active and (count < 0 or captured < count):
            try:
                frame = self.capture_one(timeout=timeout)
                yield frame
                captured += 1
            except TimeoutError:
                logger.warning("Frame timeout — sensor may have stopped")
                break

    def save_raw(self, frame: FrameData, path: Path) -> None:
        """Save raw pixel data and metadata to .npy + .json files."""
        import json
        np.save(str(path.with_suffix('.npy')), frame.pixels)
        meta = {
            'sequence': frame.sequence, 'timestamp_us': frame.timestamp_us,
            'width': frame.width, 'height': frame.height,
            'pixel_format': frame.pixel_format.name,
            'gain': frame.gain, 'exposure_us': frame.exposure_us,
            'temperature_c': frame.temperature_c,
            'ecc_errors': frame.ecc_errors, 'crc_errors': frame.crc_errors,
        }
        path.with_suffix('.json').write_text(json.dumps(meta, indent=2))
        logger.info(f"Saved frame {frame.sequence} to {path}")


# ─────────────────────────────────────────────────────────────────────────────
# DiagnosticsClient
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosticsClient:
    """Read DTCs, health data, and trace logs."""

    def __init__(self, device: SensorDevice):
        self._dev = device

    def get_dtcs(self) -> list[DiagnosticEvent]:
        resp = self._dev.send_command(_CMD_GET_DTC)
        if not resp:
            return []
        count = resp[0]
        events = []
        offset = 1
        for _ in range(count):
            code, status, occ, first_ts, last_ts = struct.unpack_from('<IBIQQ', resp, offset)
            events.append(DiagnosticEvent(dtc_code=code, status=status,
                                           occurrence_count=occ,
                                           first_occurrence_us=first_ts,
                                           last_occurrence_us=last_ts))
            offset += 22
        return events

    def clear_dtcs(self) -> None:
        self._dev.send_command(_CMD_CLEAR_DTC)
        logger.info("DTCs cleared")

    def print_dtc_report(self) -> None:
        dtcs = self.get_dtcs()
        if not dtcs:
            print("No active DTCs")
            return
        print(f"{'DTC Code':<12} {'Status':<12} {'Occurrences':<13} {'First Seen'}")
        print('-' * 65)
        for d in dtcs:
            first = time.strftime('%H:%M:%S', time.gmtime(d.first_occurrence_us / 1e6))
            print(f"0x{d.dtc_code:08X}  {d.status_name:<12} {d.occurrence_count:<13} {first}")


# ─────────────────────────────────────────────────────────────────────────────
# FirmwareUpdater
# ─────────────────────────────────────────────────────────────────────────────
class FirmwareUpdater:
    """OTA firmware update with integrity verification."""

    CHUNK_SIZE = 512  # Bytes per transfer

    def __init__(self, device: SensorDevice):
        self._dev = device

    def update(self, firmware_path: Path,
               progress_cb: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Update firmware from a binary file.
        The firmware image must be signed (last 256 bytes = signature).
        """
        import hashlib
        fw_data = firmware_path.read_bytes()
        fw_size  = len(fw_data)
        fw_sha256 = hashlib.sha256(fw_data).digest()

        logger.info(f"Starting firmware update: {fw_size} bytes from {firmware_path}")

        # Start update session
        header = struct.pack('<II32s', fw_size, self.CHUNK_SIZE, fw_sha256)
        self._dev.send_command(_CMD_FW_UPDATE, b'\x01' + header)

        # Transfer data in chunks
        offset = 0
        chunk_idx = 0
        total_chunks = (fw_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE

        while offset < fw_size:
            chunk = fw_data[offset:offset + self.CHUNK_SIZE]
            payload = struct.pack('<HH', chunk_idx, len(chunk)) + chunk
            self._dev.send_command(_CMD_FW_UPDATE, b'\x02' + payload, timeout=10.0)
            offset += len(chunk)
            chunk_idx += 1
            if progress_cb:
                progress_cb(offset, fw_size)

        # Finalize and verify
        self._dev.send_command(_CMD_FW_UPDATE, b'\x03', timeout=30.0)  # Verify+install
        logger.info("Firmware update completed successfully")
