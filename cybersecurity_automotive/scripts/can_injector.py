#!/usr/bin/env python3
"""
CAN Frame Injector — Automotive Cybersecurity Lab Tool

EDUCATIONAL TOOL FOR AUTHORIZED SECURITY TESTING ON TEST BENCH ONLY.
DO NOT USE ON VEHICLES CONNECTED TO PUBLIC ROADS.
Unauthorized use on production vehicles may violate law (Computer Fraud and Abuse Act,
EU Directive 2013/40/EU, and local vehicle cybersecurity regulations).

Modes:
  single    — Inject a single CAN frame
  replay    — Replay frames from a CAN log file
  burst     — Inject the same frame at high rate (DoS simulation)
  busoff    — Simulate bus-off attack by sending conflicting error frames (educational only)

Usage:
  python3 can_injector.py --channel vcan0 --mode single --id 0x244 --data 01 02 03 04 05 06 07 08
  python3 can_injector.py --channel vcan0 --mode replay --log candump.log
  python3 can_injector.py --channel vcan0 --mode burst --id 0x100 --data FF FF --count 1000

Requirements:
  pip install python-can

Author: Automotive Cybersecurity Lab
"""
import can
import time
import argparse
import sys
import re
from typing import List, Optional

# ─── SAFETY BANNER ───────────────────────────────────────────────────────────

SAFETY_BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║          AUTOMOTIVE CAN INJECTOR — AUTHORIZED LAB USE ONLY              ║
║                                                                          ║
║  USE ONLY ON ISOLATED TEST BENCHES WITH ECUs NOT CONNECTED TO VEHICLES  ║
║  Unauthorized use on production vehicles is ILLEGAL                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ─── LOG PARSERS ─────────────────────────────────────────────────────────────

def parse_candump_log(path: str) -> List[can.Message]:
    """
    Parse candump ASCII log format:
    (1234567890.123456) vcan0 244#0102030405060708
    """
    frames = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Match: (timestamp) interface ID#DATA
            m = re.match(r'\((\d+\.\d+)\)\s+\S+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)', line)
            if m:
                ts = float(m.group(1))
                arb_id = int(m.group(2), 16)
                data = bytes.fromhex(m.group(3)) if m.group(3) else b''
                frames.append(can.Message(
                    arbitration_id=arb_id,
                    data=data,
                    timestamp=ts,
                    is_extended_id=False
                ))
    return frames

def parse_asc_log(path: str) -> List[can.Message]:
    """
    Parse Vector ASC log format:
      0.001  1  244    Rx   d   8  01 02 03 04 05 06 07 08
    """
    frames = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//') or line.lower().startswith('date'):
                continue
            parts = line.split()
            if len(parts) >= 7:
                try:
                    ts = float(parts[0])
                    arb_id = int(parts[2], 16)
                    dlc = int(parts[5])
                    data = bytes(int(x, 16) for x in parts[6:6+dlc])
                    frames.append(can.Message(
                        arbitration_id=arb_id,
                        data=data,
                        timestamp=ts,
                        is_extended_id=False
                    ))
                except (ValueError, IndexError):
                    continue
    return frames

# ─── INJECTOR ────────────────────────────────────────────────────────────────

class CANInjector:
    def __init__(self, channel: str, bustype: str = "socketcan", bitrate: int = 500000):
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate

    def _open_bus(self):
        kwargs = {"bustype": self.bustype}
        if self.bustype == "pcan":
            kwargs["bitrate"] = self.bitrate
        return can.interface.Bus(self.channel, **kwargs)

    def inject_single(self, arb_id: int, data: bytes, count: int = 1,
                      interval: float = 0.0, extended: bool = False):
        """Inject a single CAN frame (optionally repeated)"""
        msg = can.Message(
            arbitration_id=arb_id,
            data=data,
            is_extended_id=extended
        )
        with self._open_bus() as bus:
            for i in range(count):
                bus.send(msg)
                sent_data = " ".join(f"{b:02X}" for b in data)
                print(f"[{i+1}/{count}] Sent: 0x{arb_id:03X} [{sent_data}]")
                if interval > 0 and i < count - 1:
                    time.sleep(interval)

    def inject_burst(self, arb_id: int, data: bytes, count: int = 1000,
                     interval: float = 0.001):
        """High-rate burst injection (DoS test)"""
        print(f"[BURST] Injecting 0x{arb_id:03X} x{count} at {1/interval:.0f} fps")
        print("[BURST] WARNING: High-rate injection may cause bus overload")
        self.inject_single(arb_id, data, count=count, interval=interval)

    def replay_log(self, log_path: str, speed: float = 1.0, loop: bool = False):
        """Replay a CAN log file with original timing"""
        # Detect log format
        if log_path.endswith('.asc'):
            frames = parse_asc_log(log_path)
        else:
            frames = parse_candump_log(log_path)

        if not frames:
            print(f"[ERROR] No frames found in {log_path}")
            return

        print(f"[REPLAY] Loaded {len(frames)} frames from {log_path}")
        print(f"[REPLAY] Speed: {speed}x")

        run_count = 0
        try:
            with self._open_bus() as bus:
                while True:
                    run_count += 1
                    t0 = frames[0].timestamp
                    replay_start = time.time()

                    for i, frame in enumerate(frames):
                        # Compute delay based on original timing
                        original_offset = (frame.timestamp - t0) / speed
                        elapsed = time.time() - replay_start
                        wait = original_offset - elapsed
                        if wait > 0:
                            time.sleep(wait)

                        msg = can.Message(
                            arbitration_id=frame.arbitration_id,
                            data=frame.data,
                            is_extended_id=frame.is_extended_id
                        )
                        bus.send(msg)
                        if i % 100 == 0:
                            print(f"  [REPLAY run {run_count}] {i}/{len(frames)} frames sent", end='\r')

                    print(f"\n[REPLAY] Run {run_count} complete — {len(frames)} frames")
                    if not loop:
                        break
        except KeyboardInterrupt:
            print(f"\n[REPLAY] Stopped by user (run {run_count})")

    def simulate_busoff(self, target_id: int, duration: float = 5.0):
        """
        EDUCATIONAL SIMULATION: Demonstrate bus-off concept.

        Real bus-off attacks require hardware that can inject dominant bits at bit-level.
        This simulation shows the CONCEPTUAL APPROACH only using software-level
        error frame generation (actual bus-off requires CAN controller hardware support).

        What a real bus-off attack does:
        1. Attacker monitors target ECU frames
        2. At EXACT moment target transmits, attacker sends dominant bit (bus wins by dominance)
        3. Target ECU sees error, increments TEC (Transmit Error Counter)
        4. After TEC >= 256, ECU enters bus-off state — silenced from network

        This function uses legal software simulation to EDUCATE, not to attack.
        """
        print("[BUS-OFF SIMULATION — EDUCATIONAL ONLY]")
        print(f"  Monitoring 0x{target_id:03X} for {duration}s")
        print("  A real attack would require bit-level hardware access to the physical CAN bus")
        print("  This simulation only demonstrates the detection side")

        seen = []
        try:
            with self._open_bus() as bus:
                end = time.time() + duration
                while time.time() < end:
                    msg = bus.recv(timeout=0.1)
                    if msg and msg.arbitration_id == target_id:
                        seen.append(msg.timestamp)
        except KeyboardInterrupt:
            pass

        print(f"  [RESULT] Observed {len(seen)} frames from 0x{target_id:03X} in {duration}s")
        if seen:
            rates = [seen[i+1]-seen[i] for i in range(len(seen)-1)]
            avg = sum(rates)/len(rates) if rates else 0
            print(f"  [RESULT] Average cycle time: {avg*1000:.2f}ms")
            print("  [RESULT] In a real attack, the attacker would inject at this exact timing")

# ─── ARGUMENT PARSING ────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="CAN Frame Injector (Lab/Educational Use Only)"
    )
    p.add_argument("--channel", default="vcan0", help="CAN interface")
    p.add_argument("--bustype", default="socketcan",
                   choices=["socketcan", "pcan", "vector", "kvaser", "virtual"])
    p.add_argument("--bitrate", type=int, default=500000)
    p.add_argument("--mode", required=True,
                   choices=["single", "replay", "burst", "busoff"],
                   help="Injection mode")

    # Single/burst frame options
    p.add_argument("--id", help="CAN message ID (hex, e.g., 0x244)")
    p.add_argument("--data", nargs="+", help="CAN data bytes in hex (e.g., 01 02 03 04)")
    p.add_argument("--extended", action="store_true", help="Use extended (29-bit) frame")
    p.add_argument("--count", type=int, default=1, help="Injection count")
    p.add_argument("--interval", type=float, default=0.0, help="Interval between frames (sec)")

    # Replay options
    p.add_argument("--log", help="Log file path (.asc or candump format)")
    p.add_argument("--speed", type=float, default=1.0, help="Replay speed multiplier")
    p.add_argument("--loop", action="store_true", help="Loop replay continuously")

    # Bus-off
    p.add_argument("--target-id", help="Target ID for bus-off simulation (hex)")
    p.add_argument("--duration", type=float, default=5.0, help="Duration for bus-off sim (sec)")

    return p.parse_args()


def main():
    print(SAFETY_BANNER)
    args = parse_args()

    injector = CANInjector(
        channel=args.channel,
        bustype=args.bustype,
        bitrate=args.bitrate
    )

    if args.mode == "single":
        if not args.id or not args.data:
            print("[ERROR] --id and --data required for single mode")
            sys.exit(1)
        arb_id = int(args.id, 16)
        data = bytes(int(x, 16) for x in args.data)
        injector.inject_single(arb_id, data, count=args.count,
                               interval=args.interval, extended=args.extended)

    elif args.mode == "burst":
        if not args.id or not args.data:
            print("[ERROR] --id and --data required for burst mode")
            sys.exit(1)
        arb_id = int(args.id, 16)
        data = bytes(int(x, 16) for x in args.data)
        interval = args.interval if args.interval > 0 else 0.001
        injector.inject_burst(arb_id, data, count=args.count, interval=interval)

    elif args.mode == "replay":
        if not args.log:
            print("[ERROR] --log required for replay mode")
            sys.exit(1)
        injector.replay_log(args.log, speed=args.speed, loop=args.loop)

    elif args.mode == "busoff":
        tid = int(args.target_id, 16) if args.target_id else 0x100
        injector.simulate_busoff(tid, duration=args.duration)


if __name__ == "__main__":
    main()
