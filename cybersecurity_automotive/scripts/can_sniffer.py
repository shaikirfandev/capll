#!/usr/bin/env python3
"""
CAN Sniffer with DBC Decoding and Anomaly Detection
Automotive Cybersecurity Lab Tool

Usage:
  python3 can_sniffer.py --channel vcan0 --dbc vehicle.dbc
  python3 can_sniffer.py --channel PCAN --bitrate 500000 --ids 0x244,0x100

Requirements:
  pip install python-can cantools colorama

Author: Automotive Cybersecurity Lab
"""
import can
import cantools
import time
import argparse
import json
import sys
import signal
from collections import defaultdict
from typing import Optional
from datetime import datetime

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False

# ─── ANOMALY DETECTION RULES ──────────────────────────────────────────────────

class AnomalyRule:
    """Base class for CAN anomaly detection rules"""
    def check(self, msg: can.Message, stats: dict) -> Optional[str]:
        return None

class CycleTimeAnomalyRule(AnomalyRule):
    """Detect messages arriving too fast (possible injection/flood)"""
    def __init__(self, tolerance: float = 0.5):
        self.last_time = {}
        self.expected_cycles = {}  # Learned from first N messages
        self.learn_count = defaultdict(int)
        self.cycle_sum = defaultdict(float)
        self.tolerance = tolerance  # 50% deviation triggers alert

    def check(self, msg: can.Message, stats: dict) -> Optional[str]:
        now = msg.timestamp
        mid = msg.arbitration_id

        if mid in self.last_time:
            gap = now - self.last_time[mid]

            # Learning phase: first 20 messages
            if self.learn_count[mid] < 20:
                self.cycle_sum[mid] += gap
                self.learn_count[mid] += 1
                self.expected_cycles[mid] = self.cycle_sum[mid] / self.learn_count[mid]
            else:
                expected = self.expected_cycles.get(mid, 0)
                if expected > 0 and gap < expected * self.tolerance:
                    return f"CYCLE_TIME_ANOMALY: ID=0x{mid:03X} gap={gap*1000:.1f}ms expected={expected*1000:.1f}ms"

        self.last_time[mid] = now
        return None

class DLCWhitelistRule(AnomalyRule):
    """Detect messages with unexpected DLC (could be injection bypass)"""
    def __init__(self, whitelist: dict):
        # whitelist: {message_id: expected_dlc}
        self.whitelist = whitelist

    def check(self, msg: can.Message, stats: dict) -> Optional[str]:
        if msg.arbitration_id in self.whitelist:
            expected_dlc = self.whitelist[msg.arbitration_id]
            if msg.dlc != expected_dlc:
                return (f"DLC_ANOMALY: ID=0x{msg.arbitration_id:03X} "
                        f"DLC={msg.dlc} expected={expected_dlc}")
        return None

class BusLoadRule(AnomalyRule):
    """Alert if bus load exceeds threshold (possible DoS)"""
    def __init__(self, threshold_percent: float = 70.0, window_sec: float = 1.0):
        self.window_start = time.time()
        self.frame_count = 0
        self.threshold = threshold_percent
        self.window_sec = window_sec
        # CAN 500Kbps: ~7000 frames/sec theoretical max (8-byte frames ~71 bits each)
        self.max_frames = 7000 * window_sec

    def check(self, msg: can.Message, stats: dict) -> Optional[str]:
        self.frame_count += 1
        elapsed = time.time() - self.window_start

        if elapsed >= self.window_sec:
            load = (self.frame_count / self.max_frames) * 100
            result = None
            if load > self.threshold:
                result = f"HIGH_BUS_LOAD: {load:.1f}% in last {elapsed:.1f}s ({self.frame_count} frames)"
            self.frame_count = 0
            self.window_start = time.time()
            return result
        return None

class IDWhitelistRule(AnomalyRule):
    """Alert on message IDs not in the known whitelist"""
    def __init__(self, whitelist: set):
        self.whitelist = whitelist
        self.already_alerted = set()

    def check(self, msg: can.Message, stats: dict) -> Optional[str]:
        mid = msg.arbitration_id
        if self.whitelist and mid not in self.whitelist and mid not in self.already_alerted:
            self.already_alerted.add(mid)
            return f"UNKNOWN_ID: 0x{mid:03X} (not in whitelist)"
        return None

# ─── SNIFFER ─────────────────────────────────────────────────────────────────

class CANSniffer:
    def __init__(self, channel: str, bustype: str, bitrate: int, db=None,
                 filter_ids: list = None, anomaly_rules: list = None,
                 log_file: str = None):
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.db = db
        self.filter_ids = set(filter_ids) if filter_ids else None
        self.anomaly_rules = anomaly_rules or []
        self.log_file = open(log_file, 'w') if log_file else None

        self.stats = defaultdict(lambda: {"count": 0, "last_data": None, "last_time": 0})
        self.alerts = []
        self.total_frames = 0
        self.start_time = time.time()

    def _print_color(self, color_code: str, msg: str):
        if COLOR:
            print(f"{color_code}{msg}{Style.RESET_ALL}")
        else:
            print(msg)

    def _format_frame(self, msg: can.Message) -> str:
        ts = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S.%f")[:-3]
        data_hex = " ".join(f"{b:02X}" for b in msg.data)
        line = f"[{ts}] 0x{msg.arbitration_id:03X} DLC={msg.dlc} [{data_hex}]"

        if self.db:
            try:
                decoded = self.db.decode_message(msg.arbitration_id, msg.data)
                signals = ", ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                                   for k, v in decoded.items())
                line += f" | {signals}"
            except (KeyError, Exception):
                pass

        return line

    def _log_alert(self, alert_msg: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        full = f"[{ts}] *** ALERT: {alert_msg}"
        self._print_color(Fore.RED if COLOR else "", full)
        self.alerts.append({"timestamp": ts, "message": alert_msg})
        if self.log_file:
            self.log_file.write(f"ALERT|{ts}|{alert_msg}\n")

    def sniff(self, duration: float = None):
        """Main sniff loop"""
        bus_kwargs = {"bustype": self.bustype}
        if self.bitrate and self.bustype in ("socketcan", "pcan"):
            pass  # bitrate set via OS for socketcan; PCAN auto-detects
        if self.bustype == "pcan":
            bus_kwargs["bitrate"] = self.bitrate

        with can.interface.Bus(self.channel, **bus_kwargs) as bus:
            print(f"[CAN Sniffer] Listening on {self.channel} ({self.bustype})")
            print(f"[CAN Sniffer] DBC: {'Loaded' if self.db else 'None'}")
            print(f"[CAN Sniffer] Anomaly rules: {len(self.anomaly_rules)}")
            print("─" * 80)

            timeout = time.time() + duration if duration else None

            try:
                while True:
                    if timeout and time.time() > timeout:
                        break

                    msg = bus.recv(timeout=0.5)
                    if msg is None:
                        continue

                    self.total_frames += 1

                    # Apply ID filter
                    if self.filter_ids and msg.arbitration_id not in self.filter_ids:
                        continue

                    # Update stats
                    mid = msg.arbitration_id
                    self.stats[mid]["count"] += 1
                    self.stats[mid]["last_data"] = msg.data.hex()
                    self.stats[mid]["last_time"] = msg.timestamp

                    # Print frame
                    line = self._format_frame(msg)
                    print(line)
                    if self.log_file:
                        self.log_file.write(f"FRAME|{line}\n")

                    # Run anomaly rules
                    for rule in self.anomaly_rules:
                        alert = rule.check(msg, self.stats)
                        if alert:
                            self._log_alert(alert)

            except KeyboardInterrupt:
                pass
            finally:
                self._print_summary()
                if self.log_file:
                    self.log_file.close()

    def _print_summary(self):
        elapsed = time.time() - self.start_time
        print("\n" + "─" * 80)
        print(f"[SUMMARY] Duration: {elapsed:.1f}s | Total frames: {self.total_frames}")
        print(f"[SUMMARY] Unique message IDs: {len(self.stats)}")
        print(f"[SUMMARY] Alerts triggered: {len(self.alerts)}")
        print("\n[MESSAGE STATISTICS]")
        print(f"{'ID':>8}  {'Count':>8}  {'Rate/s':>8}  {'Last Data'}")
        print("─" * 60)
        for mid, stat in sorted(self.stats.items()):
            rate = stat["count"] / elapsed if elapsed > 0 else 0
            print(f"0x{mid:03X}    {stat['count']:>8}  {rate:>8.1f}  {stat['last_data']}")

# ─── ARGUMENT PARSING ────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Automotive CAN Security Sniffer")
    p.add_argument("--channel", default="vcan0",
                   help="CAN interface: vcan0, can0, PCAN_USBBUS1 (default: vcan0)")
    p.add_argument("--bustype", default="socketcan",
                   choices=["socketcan", "pcan", "kvaser", "vector", "ixxat"],
                   help="python-can bus type (default: socketcan)")
    p.add_argument("--bitrate", type=int, default=500000,
                   help="CAN bitrate in bps (default: 500000)")
    p.add_argument("--dbc", help="DBC file path for signal decoding")
    p.add_argument("--ids", help="Comma-separated hex IDs to filter (e.g., 0x244,0x100)")
    p.add_argument("--whitelist", help="Comma-separated hex IDs for whitelist rule")
    p.add_argument("--duration", type=float, help="Capture duration in seconds")
    p.add_argument("--log", help="Log file path (optional)")
    p.add_argument("--bus-load-threshold", type=float, default=70.0,
                   help="Bus load alert threshold %% (default: 70)")
    return p.parse_args()


def main():
    args = parse_args()

    # Load DBC
    db = None
    if args.dbc:
        try:
            db = cantools.database.load_file(args.dbc)
            print(f"[DBC] Loaded {args.dbc}: {len(db.messages)} messages")
        except Exception as e:
            print(f"[DBC] Warning: could not load {args.dbc}: {e}")

    # Build ID filter
    filter_ids = None
    if args.ids:
        filter_ids = [int(x.strip(), 16) for x in args.ids.split(",")]

    # Build whitelist
    whitelist = set()
    if args.whitelist:
        whitelist = {int(x.strip(), 16) for x in args.whitelist.split(",")}
    elif db:
        whitelist = {msg.frame_id for msg in db.messages}

    # Build DLC whitelist from DBC
    dlc_whitelist = {}
    if db:
        for msg in db.messages:
            dlc_whitelist[msg.frame_id] = msg.length

    # Anomaly rules
    rules = [
        CycleTimeAnomalyRule(tolerance=0.5),
        DLCWhitelistRule(dlc_whitelist),
        BusLoadRule(threshold_percent=args.bus_load_threshold),
    ]
    if whitelist:
        rules.append(IDWhitelistRule(whitelist))

    # Run sniffer
    sniffer = CANSniffer(
        channel=args.channel,
        bustype=args.bustype,
        bitrate=args.bitrate,
        db=db,
        filter_ids=filter_ids,
        anomaly_rules=rules,
        log_file=args.log
    )
    sniffer.sniff(duration=args.duration)


if __name__ == "__main__":
    main()
