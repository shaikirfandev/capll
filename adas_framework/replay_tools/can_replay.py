# adas_framework/replay_tools/can_replay.py
"""
CAN Log Replay Module — ADAS Enterprise Framework.

Supports:
    - Vector BLF file replay (via python-can BLF reader)
    - ASC text log replay
    - PCAP (Wireshark) Ethernet replay via scapy
    - Real-time speed control (0.5×, 1×, 2×, 4×, etc.)
    - Timestamp-accurate replay with drift correction
    - Frame filter: replay only specific CAN IDs
    - Loop mode for endurance testing

Usage:
    replayer = CANReplayer(can_bus, log_file="capture.blf")
    replayer.add_filter(include_ids=[0x120, 0x150])
    replayer.replay(speed=1.0, loop=False)

    # Or use context manager for controlled replay in tests:
    with CANReplayer.play(can_bus, "test_scenario.asc") as r:
        time.sleep(r.duration_s)
        assert signals.get("ACC_Status") == 2
"""
from __future__ import annotations

import contextlib
import os
import struct
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterator, List, Optional, Set

from core.logger import get_logger

log = get_logger("can_replay")


# ─────────────────────────────────────────────────────────────────────────────
# Frame record (normalised)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LogFrame:
    timestamp: float   # seconds from log start
    can_id:    int
    data:      bytes
    is_fd:     bool = False
    channel:   int  = 1


# ─────────────────────────────────────────────────────────────────────────────
# Log readers
# ─────────────────────────────────────────────────────────────────────────────

class _BLFReader:
    """Read frames from a Vector BLF log via python-can."""
    def __init__(self, path: str):
        self._path = path

    def frames(self) -> Iterator[LogFrame]:
        try:
            import can
            with can.BLFReader(self._path) as reader:
                first_ts = None
                for msg in reader:
                    if first_ts is None:
                        first_ts = msg.timestamp
                    yield LogFrame(
                        timestamp = msg.timestamp - first_ts,
                        can_id    = msg.arbitration_id,
                        data      = bytes(msg.data),
                        is_fd     = msg.is_fd,
                        channel   = getattr(msg, 'channel', 1) or 1,
                    )
        except ImportError:
            log.warning("python-can not available — BLF reader disabled")

    def duration(self) -> float:
        frames = list(self.frames())
        return frames[-1].timestamp if frames else 0.0


class _ASCReader:
    """Read frames from a Vector ASC text log."""
    def __init__(self, path: str):
        self._path = path

    def frames(self) -> Iterator[LogFrame]:
        first_ts = None
        with open(self._path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("//") or line.startswith("date"):
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                try:
                    ts  = float(parts[0])
                    # can_id is hex in ASC
                    raw_id = parts[2]
                    can_id = int(raw_id, 16)
                    dlc    = int(parts[4])
                    data   = bytes(int(b, 16) for b in parts[5:5+dlc])
                    if first_ts is None:
                        first_ts = ts
                    yield LogFrame(
                        timestamp = ts - first_ts,
                        can_id    = can_id,
                        data      = data,
                    )
                except (ValueError, IndexError):
                    continue


# ─────────────────────────────────────────────────────────────────────────────
# CANReplayer
# ─────────────────────────────────────────────────────────────────────────────

class CANReplayer:
    """High-fidelity CAN log replay engine."""

    def __init__(self, can_bus, log_file: str):
        self._bus       = can_bus
        self._log_file  = log_file
        self._reader    = self._create_reader(log_file)
        self._include_ids: Optional[Set[int]] = None
        self._exclude_ids: Set[int]           = set()
        self._speed: float = 1.0
        self._stop_event   = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._current_ts: float = 0.0
        self._frames_sent:  int = 0
        self._frames_skipped: int = 0

    def _create_reader(self, path: str):
        ext = Path(path).suffix.lower()
        if ext == ".blf":
            return _BLFReader(path)
        elif ext in (".asc", ".log"):
            return _ASCReader(path)
        else:
            raise ValueError(f"Unsupported log format: {ext}")

    # ── Filter configuration ──────────────────────────────────────────────────

    def add_filter(self, include_ids: List[int] = None,
                   exclude_ids: List[int] = None):
        if include_ids is not None:
            self._include_ids = set(include_ids)
        if exclude_ids:
            self._exclude_ids.update(exclude_ids)

    def _should_replay(self, frame: LogFrame) -> bool:
        if frame.can_id in self._exclude_ids:
            return False
        if self._include_ids is not None:
            return frame.can_id in self._include_ids
        return True

    # ── Replay execution ──────────────────────────────────────────────────────

    def replay(self, speed: float = 1.0, loop: bool = False):
        """Block until replay complete (or stopped)."""
        self._speed = speed
        self._stop_event.clear()

        while True:
            self._play_once()
            if self._stop_event.is_set() or not loop:
                break
            log.info("Replay loop restarting...")

        log.info(
            f"Replay complete | sent={self._frames_sent} "
            f"skipped={self._frames_skipped}"
        )

    def _play_once(self):
        """Single-pass replay."""
        start_wall = time.monotonic()
        last_log_ts = 0.0

        for frame in self._reader.frames():
            if self._stop_event.is_set():
                break

            if not self._should_replay(frame):
                self._frames_skipped += 1
                continue

            # Timing: wait for the right wall-clock moment
            target_wall = start_wall + (frame.timestamp / self._speed)
            now = time.monotonic()
            wait = target_wall - now
            if wait > 0:
                time.sleep(wait)

            # Send
            self._bus.send(frame.can_id, frame.data)
            self._frames_sent += 1
            self._current_ts = frame.timestamp
            last_log_ts = frame.timestamp

    def replay_async(self, speed: float = 1.0, loop: bool = False
                     ) -> threading.Thread:
        """Start replay in a background thread, return thread."""
        self._thread = threading.Thread(
            target=self.replay,
            kwargs={"speed": speed, "loop": loop},
            daemon=True,
            name="CANReplay",
        )
        self._thread.start()
        return self._thread

    def stop(self):
        """Stop a running replay."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    @property
    def current_time_s(self) -> float:
        return self._current_ts

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Convenience context manager ───────────────────────────────────────────

    @classmethod
    @contextlib.contextmanager
    def play(cls, can_bus, log_file: str,
             speed: float = 1.0,
             include_ids: List[int] = None) -> Generator["CANReplayer", None, None]:
        """
        Context manager: starts async replay, yields replayer, stops on exit.

        Usage:
            with CANReplayer.play(bus, "capture.blf", speed=2.0) as r:
                time.sleep(5.0)
                assert signals.get("ACC_Status") == 2
        """
        replayer = cls(can_bus, log_file)
        if include_ids:
            replayer.add_filter(include_ids=include_ids)
        replayer.replay_async(speed=speed)
        try:
            yield replayer
        finally:
            replayer.stop()

    # ── Log analysis (without replaying) ─────────────────────────────────────

    def analyze(self) -> dict:
        """
        Pre-scan the log file and return statistics.
        Useful for validating a log before replay.
        """
        frames_by_id: dict = {}
        total = 0
        for frame in self._reader.frames():
            total += 1
            if frame.can_id not in frames_by_id:
                frames_by_id[frame.can_id] = 0
            frames_by_id[frame.can_id] += 1

        return {
            "total_frames":  total,
            "unique_ids":    len(frames_by_id),
            "id_frame_count": frames_by_id,
        }
