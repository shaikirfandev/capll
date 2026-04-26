"""
python_can_bus_monitor.py
========================
Automotive CAN bus monitoring using python-can library.

Features:
- Connect to real CAN hardware (PEAK, Kvaser, Vector) or virtual bus
- Monitor and filter messages
- Decode signals using cantools (DBC parsing)
- Detect message timeouts
- Log to CSV
- Calculate bus load

Requirements:
    pip install python-can cantools
"""

import can
import cantools
import csv
import time
import threading
from datetime import datetime
from collections import defaultdict
from typing import Optional


# ─────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────
BUS_INTERFACE  = "virtual"        # "pcan", "kvaser", "vector", "socketcan", "virtual"
BUS_CHANNEL    = "test"           # e.g., "PCAN_USBBUS1", "vcan0", "0"
BUS_BITRATE    = 500_000          # 500 kbps
DBC_FILE       = "powertrain.dbc" # Optional – set to None to skip signal decoding
LOG_FILE       = "can_monitor.csv"
MONITOR_DURATION = 30             # seconds (0 = run until Ctrl+C)


# ─────────────────────────────────────────────────────────
# Bus Load Tracker
# ─────────────────────────────────────────────────────────
class BusLoadTracker:
    """Approximate CAN bus load measurement."""

    BITS_PER_FRAME_APPROX = 130  # Standard 8-byte CAN frame ≈ 130 bits

    def __init__(self, bitrate: int = 500_000):
        self.bitrate = bitrate
        self.frame_count = 0
        self.window_start = time.time()
        self.lock = threading.Lock()

    def record_frame(self):
        with self.lock:
            self.frame_count += 1

    def get_load_percent(self) -> float:
        with self.lock:
            elapsed = time.time() - self.window_start
            if elapsed == 0:
                return 0.0
            bits_used = self.frame_count * self.BITS_PER_FRAME_APPROX
            load = (bits_used / (self.bitrate * elapsed)) * 100.0
            # Reset window
            self.frame_count = 0
            self.window_start = time.time()
            return min(load, 100.0)


# ─────────────────────────────────────────────────────────
# Message Timeout Monitor
# ─────────────────────────────────────────────────────────
class TimeoutMonitor:
    """Monitor expected periodic messages for timeouts."""

    def __init__(self):
        # {msg_id: (expected_cycle_ms, last_seen_time)}
        self._monitored: dict[int, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def register(self, msg_id: int, cycle_ms: float):
        """Register a message ID with its expected cycle time."""
        with self._lock:
            self._monitored[msg_id] = (cycle_ms, time.time())

    def message_received(self, msg_id: int):
        """Update last-seen timestamp for a message."""
        with self._lock:
            if msg_id in self._monitored:
                cycle_ms, _ = self._monitored[msg_id]
                self._monitored[msg_id] = (cycle_ms, time.time())

    def check_timeouts(self) -> list[int]:
        """Return list of message IDs that have timed out."""
        now = time.time()
        timed_out = []
        with self._lock:
            for msg_id, (cycle_ms, last_seen) in self._monitored.items():
                timeout_s = (cycle_ms * 1.5) / 1000.0  # 150% of cycle = timeout
                if (now - last_seen) > timeout_s:
                    timed_out.append(msg_id)
        return timed_out


# ─────────────────────────────────────────────────────────
# Signal Decoder (using cantools + DBC)
# ─────────────────────────────────────────────────────────
def load_database(dbc_path: Optional[str]) -> Optional[cantools.database.Database]:
    if dbc_path is None:
        return None
    try:
        db = cantools.database.load_file(dbc_path)
        print(f"[INFO] DBC loaded: {dbc_path} ({len(db.messages)} messages)")
        return db
    except FileNotFoundError:
        print(f"[WARN] DBC file not found: {dbc_path} – running without signal decoding")
        return None


def decode_message(db: Optional[cantools.database.Database],
                   msg: can.Message) -> Optional[dict]:
    """Decode CAN message signals using DBC database. Returns None if unknown."""
    if db is None:
        return None
    try:
        db_msg = db.get_message_by_frame_id(msg.arbitration_id)
        return db_msg.decode(msg.data, decode_choices=True)
    except (KeyError, cantools.database.errors.DecodeError):
        return None


# ─────────────────────────────────────────────────────────
# CSV Logger
# ─────────────────────────────────────────────────────────
class CSVLogger:
    def __init__(self, filepath: str):
        self._file = open(filepath, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["Timestamp", "ID_Hex", "DLC", "Data_Hex", "Signals"])
        print(f"[INFO] Logging to: {filepath}")

    def log(self, msg: can.Message, signals: Optional[dict]):
        ts  = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S.%f")[:-3]
        id_ = f"0x{msg.arbitration_id:03X}"
        dlc = msg.dlc
        data_hex = msg.data.hex().upper()
        sig_str  = str(signals) if signals else ""
        self._writer.writerow([ts, id_, dlc, data_hex, sig_str])

    def close(self):
        self._file.close()


# ─────────────────────────────────────────────────────────
# Main Monitor
# ─────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  python-can Bus Monitor")
    print(f"  Interface : {BUS_INTERFACE} | Channel: {BUS_CHANNEL}")
    print(f"  Bitrate   : {BUS_BITRATE // 1000} kbps")
    print("=" * 55)

    # Load DBC
    db = load_database(DBC_FILE)

    # Setup bus
    try:
        bus = can.interface.Bus(
            bustype=BUS_INTERFACE,
            channel=BUS_CHANNEL,
            bitrate=BUS_BITRATE
        )
    except can.CanInitializationError as e:
        print(f"[ERROR] Failed to connect to CAN bus: {e}")
        return

    # Helpers
    bus_load  = BusLoadTracker(BUS_BITRATE)
    timeout_monitor = TimeoutMonitor()
    csv_logger = CSVLogger(LOG_FILE)

    # Register expected periodic messages (ID → cycle_ms)
    timeout_monitor.register(0x100, 10.0)   # EngineData @ 10ms
    timeout_monitor.register(0x200, 20.0)   # VehicleData @ 20ms
    timeout_monitor.register(0x300, 100.0)  # TransmissionData @ 100ms

    msg_counts: dict[int, int] = defaultdict(int)
    start_time = time.time()

    print(f"[INFO] Monitoring bus... (duration={MONITOR_DURATION}s, 0=forever)\n")

    try:
        while True:
            # Duration check
            if MONITOR_DURATION > 0 and (time.time() - start_time) > MONITOR_DURATION:
                break

            # Receive with 100ms timeout
            msg = bus.recv(timeout=0.1)
            if msg is None:
                # Check timeouts during quiet periods
                timed_out = timeout_monitor.check_timeouts()
                for tid in timed_out:
                    print(f"[TIMEOUT] Message 0x{tid:03X} not received within expected period!")
                continue

            # Update trackers
            bus_load.record_frame()
            timeout_monitor.message_received(msg.arbitration_id)
            msg_counts[msg.arbitration_id] += 1

            # Decode
            signals = decode_message(db, msg)

            # Print to console (every 100th message to reduce noise)
            if msg_counts[msg.arbitration_id] % 100 == 1:
                sig_str = f" | {signals}" if signals else ""
                print(f"[RX] {datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S.%f')[:-3]} "
                      f"ID=0x{msg.arbitration_id:03X} DLC={msg.dlc} "
                      f"Data={msg.data.hex().upper()}{sig_str}")

            # Log
            csv_logger.log(msg, signals)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        bus.shutdown()
        csv_logger.close()

        # Final statistics
        elapsed = time.time() - start_time
        total_msgs = sum(msg_counts.values())
        print("\n" + "=" * 55)
        print("  MONITOR STATISTICS")
        print("=" * 55)
        print(f"  Duration      : {elapsed:.1f}s")
        print(f"  Total Messages: {total_msgs}")
        print(f"  Avg Rate      : {total_msgs / elapsed:.1f} msg/s")
        print(f"  Unique IDs    : {len(msg_counts)}")
        print("\n  Top 5 IDs by count:")
        for mid, cnt in sorted(msg_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    0x{mid:03X} : {cnt} messages  ({cnt/elapsed:.1f} Hz)")
        print("=" * 55)


if __name__ == "__main__":
    main()
