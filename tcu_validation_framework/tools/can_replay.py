#!/usr/bin/env python3
"""
can_replay.py — Replay CAN messages from a candump log file.

Usage:
    python3 tools/can_replay.py --file logs/candump.log --interface vcan0
    python3 tools/can_replay.py --file logs/candump.log --interface vcan0 --speed 2.0 --loop

Log format supported:
    (timestamp) channel  ID#DATA
    e.g.: (1700000000.123456) vcan0 123#DEADBEEF

Author: TCU Validation Framework
"""

import argparse
import re
import socket
import struct
import sys
import time
from pathlib import Path
from typing import Optional


# ============================================================
# CAN socket helpers (SocketCAN raw)
# ============================================================

CAN_FRAME_FMT = "=IB3x8s"   # can_id, can_dlc, pad, data
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)

CAN_EFF_FLAG = 0x80000000
CAN_RTR_FLAG = 0x40000000
CAN_ERR_FLAG = 0x20000000
CAN_SFF_MASK = 0x000007FF
CAN_EFF_MASK = 0x1FFFFFFF


def open_can_socket(interface: str) -> socket.socket:
    """Open a raw CAN socket bound to the given interface."""
    try:
        sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        sock.bind((interface,))
        return sock
    except OSError as exc:
        sys.exit(f"Error opening CAN socket on {interface}: {exc}")


def send_can_frame(sock: socket.socket, can_id: int, data: bytes) -> None:
    """Pack and send a standard CAN frame."""
    dlc = min(len(data), 8)
    padded = data[:dlc].ljust(8, b"\x00")
    frame = struct.pack(CAN_FRAME_FMT, can_id, dlc, padded)
    sock.send(frame)


# ============================================================
# Log parsing
# ============================================================

# Candump format: (timestamp) channel ID#DATA
LOG_RE = re.compile(
    r"^\((\d+\.\d+)\)\s+\S+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)"
)


def parse_log_file(path: Path):
    """Yield (timestamp, can_id, data_bytes) tuples from a candump log."""
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = LOG_RE.match(line)
            if not m:
                continue
            ts    = float(m.group(1))
            raw_id = int(m.group(2), 16)
            data   = bytes.fromhex(m.group(3)) if m.group(3) else b""
            yield ts, raw_id, data


# ============================================================
# Replay logic
# ============================================================

def replay(log_file: Path,
           interface: str,
           speed: float = 1.0,
           loop: bool = False,
           verbose: bool = False) -> None:

    sock   = open_can_socket(interface)
    passes = 0

    try:
        while True:
            messages = list(parse_log_file(log_file))
            if not messages:
                print("No messages found in log file.")
                return

            passes += 1
            print(f"[Pass {passes}] Replaying {len(messages)} messages on {interface} "
                  f"(speed={speed}x)")

            first_ts: Optional[float] = None
            replay_start = time.time()

            for ts, can_id, data in messages:
                if first_ts is None:
                    first_ts = ts

                # Time relative to first message
                relative_ts   = ts - first_ts
                target_wall   = replay_start + (relative_ts / speed)
                now           = time.time()
                sleep_time    = target_wall - now

                if sleep_time > 0:
                    time.sleep(sleep_time)

                send_can_frame(sock, can_id, data)

                if verbose:
                    print(f"  tx {can_id:08X}#{data.hex().upper()}")

            elapsed = time.time() - replay_start
            print(f"  Done in {elapsed:.2f}s")

            if not loop:
                break

    except KeyboardInterrupt:
        print("\nReplay interrupted by user.")
    finally:
        sock.close()


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay CAN messages from a candump log file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--file",      required=True, type=Path,
                        help="Path to candump log file")
    parser.add_argument("--interface", default="vcan0",
                        help="CAN interface to replay on")
    parser.add_argument("--speed",     type=float, default=1.0,
                        help="Replay speed multiplier (e.g. 2.0 = 2× faster)")
    parser.add_argument("--loop",      action="store_true",
                        help="Loop replay indefinitely")
    parser.add_argument("--verbose",   action="store_true",
                        help="Print each transmitted frame")

    args = parser.parse_args()

    if not args.file.exists():
        sys.exit(f"Log file not found: {args.file}")

    if args.speed <= 0:
        sys.exit("Speed must be > 0")

    replay(args.file, args.interface, args.speed, args.loop, args.verbose)


if __name__ == "__main__":
    main()
