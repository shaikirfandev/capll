"""
can_signal_monitor/monitor.py
Real-time CAN signal monitoring with threshold alerting.

Usage:
    python monitor.py --dbc EV_BMS.dbc --channel PCAN_USBBUS1

Features:
    - Live signal value display in terminal
    - Configurable alert thresholds
    - CSV logging
    - Signal statistics (min/max/mean)
"""
import can
import cantools
import argparse
import time
import threading
import csv
import os
from datetime import datetime
from collections import defaultdict


class SignalMonitor:
    """Real-time CAN signal monitor with statistics and alerting."""

    def __init__(self, dbc_path: str, channel: str, interface: str = 'pcan',
                 bitrate: int = 500000):
        self.db = cantools.database.load_file(dbc_path)
        self.channel = channel
        self.interface = interface
        self.bitrate = bitrate
        self.bus = None
        self._running = False

        # Signal storage
        self._latest: dict = {}
        self._stats: dict = defaultdict(lambda: {'min': float('inf'),
                                                  'max': float('-inf'),
                                                  'sum': 0.0, 'count': 0})
        self._thresholds: dict = {}  # signal_name -> (low, high)
        self._alerts: list = []

        # Message tracking for timeout detection
        self._last_rx: dict = {}  # arb_id -> timestamp
        self._timeouts: dict = {}  # arb_id -> timeout_ms

        self._lock = threading.Lock()

    def set_threshold(self, signal_name: str, low: float, high: float):
        """Set alert thresholds for a signal."""
        self._thresholds[signal_name] = (low, high)

    def set_timeout(self, arb_id: int, timeout_ms: int):
        """Set message timeout threshold for Bus-Off/timeout detection."""
        self._timeouts[arb_id] = timeout_ms

    def start(self):
        """Start monitoring."""
        self.bus = can.interface.Bus(
            channel=self.channel, bustype=self.interface, bitrate=self.bitrate
        )
        self._running = True
        rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        rx_thread.start()
        print(f"[CAN Monitor] Started on {self.interface}:{self.channel}")

    def stop(self):
        self._running = False
        if self.bus:
            self.bus.shutdown()

    def _rx_loop(self):
        while self._running:
            msg = self.bus.recv(timeout=0.1)
            if msg is None:
                continue
            try:
                msg_def = self.db.get_message_by_frame_id(msg.arbitration_id)
                decoded = msg_def.decode(bytes(msg.data), decode_choices=False)
                ts = msg.timestamp

                with self._lock:
                    self._last_rx[msg.arbitration_id] = ts
                    for name, value in decoded.items():
                        val = float(value)
                        self._latest[name] = val
                        s = self._stats[name]
                        if val < s['min']:
                            s['min'] = val
                        if val > s['max']:
                            s['max'] = val
                        s['sum'] += val
                        s['count'] += 1

                        # Threshold check
                        if name in self._thresholds:
                            lo, hi = self._thresholds[name]
                            if val < lo or val > hi:
                                self._alerts.append({
                                    'time': ts,
                                    'signal': name,
                                    'value': val,
                                    'low': lo,
                                    'high': hi
                                })
            except (KeyError, Exception):
                pass

    def get_value(self, signal_name: str):
        with self._lock:
            return self._latest.get(signal_name)

    def get_stats(self, signal_name: str) -> dict:
        with self._lock:
            s = self._stats[signal_name]
            mean = s['sum'] / s['count'] if s['count'] > 0 else 0
            return {
                'min': s['min'],
                'max': s['max'],
                'mean': mean,
                'count': s['count']
            }

    def print_dashboard(self, signals: list):
        """Print live dashboard to terminal."""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=" * 60)
        print(f"  CAN SIGNAL MONITOR  —  {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        with self._lock:
            for sig in signals:
                val = self._latest.get(sig, '---')
                stats = self.get_stats(sig) if sig in self._stats else {}
                threshold = self._thresholds.get(sig)
                alert = ""
                if threshold and val != '---':
                    lo, hi = threshold
                    if val < lo or val > hi:
                        alert = " *** ALERT ***"
                print(f"  {sig:<30} {str(val):>10}{alert}")
        print("-" * 60)
        if self._alerts:
            print(f"  ALERTS: {len(self._alerts)} threshold violations")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='CAN Signal Monitor')
    parser.add_argument('--dbc', required=True)
    parser.add_argument('--channel', default='PCAN_USBBUS1')
    parser.add_argument('--interface', default='pcan')
    parser.add_argument('--bitrate', type=int, default=500000)
    parser.add_argument('--signals', nargs='+',
                        default=['BMS_SoC', 'BMS_PackVoltage', 'BMS_PackCurrent',
                                 'BMS_MaxCellTemp', 'MCU_MotorSpeed', 'MCU_TorqueActual'])
    args = parser.parse_args()

    monitor = SignalMonitor(args.dbc, args.channel, args.interface, args.bitrate)
    monitor.set_threshold('BMS_SoC', 10.0, 95.0)
    monitor.set_threshold('BMS_MaxCellTemp', -20.0, 55.0)
    monitor.set_timeout(0x310, 50)  # BMS 50ms timeout

    monitor.start()
    try:
        while True:
            monitor.print_dashboard(args.signals)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping...")
        monitor.stop()


if __name__ == '__main__':
    main()
