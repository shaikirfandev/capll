"""
network_health_monitor/network_health.py
CAN Network Health Monitor — Bus load, message timing, error frame detection.

Usage:
    python network_health.py --dbc EV_BMS.dbc --channel PCAN_USBBUS1 --duration 60

Outputs:
    - Real-time console report every 5s
    - Final HTML summary report
"""
import can
import cantools
import argparse
import time
import threading
import statistics
from collections import defaultdict
from datetime import datetime


class NetworkHealthMonitor:
    """Monitors CAN bus health metrics in real time."""

    def __init__(self, db: cantools.db.Database, bitrate: int = 500000):
        self.db = db
        self.bitrate = bitrate
        self._lock = threading.Lock()

        # Message tracking
        self._msg_timestamps = defaultdict(list)  # arb_id -> [timestamps]
        self._msg_counts = defaultdict(int)
        self._error_count = 0
        self._bus_off = False

        # Bus load (1s windows)
        self._window_bits = 0
        self._bus_load_history = []

        # Expected periods (from DBC or config)
        self._expected_periods: dict = {}  # arb_id -> period_ms

    def set_expected_period(self, arb_id: int, period_ms: float):
        """Set expected cycle time for a message (for timing violation detection)."""
        self._expected_periods[arb_id] = period_ms

    def process_message(self, msg: can.Message):
        """Process a received CAN message and update statistics."""
        with self._lock:
            arb_id = msg.arbitration_id
            ts = msg.timestamp
            self._msg_timestamps[arb_id].append(ts)
            self._msg_counts[arb_id] += 1

            # Keep only last 200 timestamps per message
            if len(self._msg_timestamps[arb_id]) > 200:
                self._msg_timestamps[arb_id] = self._msg_timestamps[arb_id][-200:]

            # Bus load bit counting
            bits = 47 + 8 * (msg.dlc or 0)
            self._window_bits += bits

    def process_error_frame(self):
        with self._lock:
            self._error_count += 1

    def update_bus_load(self):
        """Call every 1 second to record bus load window."""
        with self._lock:
            load = (self._window_bits / self.bitrate) * 100.0
            self._bus_load_history.append(load)
            self._window_bits = 0

    def get_message_stats(self, arb_id: int) -> dict:
        """Get timing statistics for a message ID."""
        with self._lock:
            timestamps = self._msg_timestamps.get(arb_id, [])

        if len(timestamps) < 2:
            return {'count': len(timestamps), 'mean_period_ms': None,
                    'max_period_ms': None, 'min_period_ms': None,
                    'jitter_ms': None, 'stdev_ms': None}

        periods_ms = [(timestamps[i+1] - timestamps[i]) * 1000
                      for i in range(len(timestamps) - 1)]
        return {
            'count': len(timestamps),
            'mean_period_ms': statistics.mean(periods_ms),
            'max_period_ms': max(periods_ms),
            'min_period_ms': min(periods_ms),
            'jitter_ms': max(periods_ms) - min(periods_ms),
            'stdev_ms': statistics.stdev(periods_ms) if len(periods_ms) > 1 else 0
        }

    def get_bus_load_stats(self) -> dict:
        with self._lock:
            h = list(self._bus_load_history)
        if not h:
            return {'current': 0, 'peak': 0, 'mean': 0}
        return {
            'current': h[-1] if h else 0,
            'peak': max(h),
            'mean': statistics.mean(h)
        }

    def get_timing_violations(self, tolerance_pct: float = 20.0) -> list:
        """Return list of messages with timing violations."""
        violations = []
        for arb_id, expected in self._expected_periods.items():
            stats = self.get_message_stats(arb_id)
            if stats['max_period_ms'] is None:
                continue
            threshold = expected * (1 + tolerance_pct / 100.0)
            if stats['max_period_ms'] > threshold:
                try:
                    msg_name = self.db.get_message_by_frame_id(arb_id).name
                except KeyError:
                    msg_name = f"0x{arb_id:03X}"
                violations.append({
                    'message': msg_name,
                    'arb_id': arb_id,
                    'expected_ms': expected,
                    'max_period_ms': stats['max_period_ms'],
                    'tolerance_ms': threshold
                })
        return violations

    def print_report(self):
        """Print current health summary to console."""
        load = self.get_bus_load_stats()
        violations = self.get_timing_violations()

        print("\n" + "═" * 65)
        print(f"  NETWORK HEALTH — {datetime.now().strftime('%H:%M:%S')}")
        print("═" * 65)
        print(f"  Bus Load:  Current={load['current']:.1f}%  "
              f"Peak={load['peak']:.1f}%  Mean={load['mean']:.1f}%  "
              f"(limit: 60%)")
        print(f"  Error Frames: {self._error_count}")
        print()
        print(f"  {'Message':<20} {'Count':>7} {'Mean(ms)':>10} "
              f"{'Max(ms)':>9} {'Jitter(ms)':>12}")
        print("-" * 65)

        for arb_id in sorted(self._msg_timestamps.keys()):
            stats = self.get_message_stats(arb_id)
            try:
                name = self.db.get_message_by_frame_id(arb_id).name[:20]
            except KeyError:
                name = f"0x{arb_id:03X}"

            if stats['mean_period_ms']:
                print(f"  {name:<20} {stats['count']:>7} "
                      f"{stats['mean_period_ms']:>9.2f}ms "
                      f"{stats['max_period_ms']:>8.2f}ms "
                      f"{stats['jitter_ms']:>11.2f}ms")

        if violations:
            print()
            print(f"  *** TIMING VIOLATIONS: {len(violations)} ***")
            for v in violations:
                print(f"    {v['message']}: max={v['max_period_ms']:.1f}ms "
                      f"(expected≤{v['tolerance_ms']:.1f}ms)")

        print("═" * 65)


def run_monitor(args):
    """Main monitoring loop."""
    db = cantools.database.load_file(args.dbc)
    monitor = NetworkHealthMonitor(db, args.bitrate)

    # Set expected periods for key messages (adjust per project)
    monitor.set_expected_period(0x310, 10.0)   # BMS 10ms
    monitor.set_expected_period(0x100, 10.0)   # VCU 10ms
    monitor.set_expected_period(0x200, 5.0)    # MCU 5ms
    monitor.set_expected_period(0x400, 100.0)  # OBC 100ms

    bus = can.interface.Bus(
        channel=args.channel, bustype=args.interface, bitrate=args.bitrate
    )

    start_time = time.time()
    last_report = start_time
    last_bus_load = start_time

    print(f"[NetHealth] Monitoring {args.channel} for {args.duration}s...")

    try:
        while (time.time() - start_time) < args.duration:
            msg = bus.recv(timeout=0.05)
            if msg:
                if msg.is_error_frame:
                    monitor.process_error_frame()
                else:
                    monitor.process_message(msg)

            now = time.time()
            if now - last_bus_load >= 1.0:
                monitor.update_bus_load()
                last_bus_load = now

            if now - last_report >= args.interval:
                monitor.print_report()
                last_report = now

    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()

    print("\n[NetHealth] Final summary:")
    monitor.print_report()


def main():
    parser = argparse.ArgumentParser(description='CAN Network Health Monitor')
    parser.add_argument('--dbc', required=True)
    parser.add_argument('--channel', default='PCAN_USBBUS1')
    parser.add_argument('--interface', default='pcan')
    parser.add_argument('--bitrate', type=int, default=500000)
    parser.add_argument('--duration', type=int, default=300,
                        help='Monitoring duration in seconds')
    parser.add_argument('--interval', type=int, default=5,
                        help='Report interval in seconds')
    args = parser.parse_args()

    run_monitor(args)


if __name__ == '__main__':
    main()
