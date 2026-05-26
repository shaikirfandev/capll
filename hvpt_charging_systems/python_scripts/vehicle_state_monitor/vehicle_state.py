"""
vehicle_state_monitor/vehicle_state.py
Vehicle Power State & Transition Monitor.

Monitors:
    - KL15 (ignition) state from CAN
    - VCU operating mode
    - Charging state
    - Power mode transitions with timestamps
    - Unexpected transition detection
    - CSV logging of all transitions

Usage:
    python vehicle_state.py --dbc EV_Powertrain.dbc --channel PCAN_USBBUS1
    python vehicle_state.py --dbc EV_Powertrain.dbc --channel test --interface virtual --duration 60
"""
import argparse
import can
import cantools
import csv
import threading
import time
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# STATE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

VCU_MODE_NAMES = {
    0: "OFF",
    1: "ACCESSORY",
    2: "READY",
    3: "ACTIVE",
    4: "CHARGING",
    5: "SLEEP",
    6: "FAULT",
}

CHARGING_STATE_NAMES = {
    0: "NOT_CHARGING",
    1: "AC_CHARGING",
    2: "DC_CHARGING",
    3: "CHARGING_COMPLETE",
    4: "CHARGING_FAULT",
}

# Valid power mode transitions (any not in this list is flagged as unexpected)
VALID_TRANSITIONS = {
    ("OFF",       "ACCESSORY"),
    ("ACCESSORY", "READY"),
    ("ACCESSORY", "OFF"),
    ("READY",     "ACTIVE"),
    ("READY",     "CHARGING"),
    ("READY",     "OFF"),
    ("ACTIVE",    "READY"),
    ("ACTIVE",    "FAULT"),
    ("ACTIVE",    "SLEEP"),
    ("CHARGING",  "READY"),
    ("CHARGING",  "CHARGING_FAULT"),
    ("SLEEP",     "READY"),
    ("SLEEP",     "OFF"),
    ("FAULT",     "OFF"),
}


@dataclass
class VehicleStateSnapshot:
    """Current vehicle state."""
    timestamp: float = 0.0
    vcu_mode: int = 0
    vcu_mode_name: str = "OFF"
    charge_state: int = 0
    charge_state_name: str = "NOT_CHARGING"
    kl15: int = 0
    soc: float = 0.0
    fault_active: int = 0
    fault_code: int = 0


@dataclass
class TransitionEvent:
    """Logged state transition."""
    timestamp: str
    elapsed_s: float
    from_state: str
    to_state: str
    trigger: str   # which signal caused transition
    expected: bool
    soc: float


class VehicleStateMonitor:
    """Monitors vehicle state machine and logs transitions."""

    def __init__(self, db: cantools.db.Database, log_path: str = 'reports/state_log.csv'):
        self._db = db
        self._log_path = log_path
        self._lock = threading.Lock()
        self._signals: dict = {}
        self._prev_state = VehicleStateSnapshot()
        self._transitions: list = []
        self._start_time = time.time()
        self._running = True
        self._unexpected_count = 0
        os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)

    def feed(self, msg: can.Message):
        """Process a received CAN message."""
        try:
            decoded = self._db.decode_message(
                msg.arbitration_id, msg.data, decode_choices=False
            )
            with self._lock:
                self._signals.update(decoded)
        except Exception:
            pass

    def _build_snapshot(self) -> VehicleStateSnapshot:
        s = self._signals
        vcu_mode = int(s.get('VCU_PowerMode', 0))
        charge_state = int(s.get('VCU_ChargeState', 0))
        return VehicleStateSnapshot(
            timestamp=time.time(),
            vcu_mode=vcu_mode,
            vcu_mode_name=VCU_MODE_NAMES.get(vcu_mode, f"UNKNOWN({vcu_mode})"),
            charge_state=charge_state,
            charge_state_name=CHARGING_STATE_NAMES.get(charge_state, f"UNKNOWN({charge_state})"),
            kl15=int(s.get('VCU_KL15', 0)),
            soc=float(s.get('BMS_SoC', 0.0)),
            fault_active=int(s.get('VCU_FaultActive', 0)),
            fault_code=int(s.get('VCU_FaultCode', 0)),
        )

    def check_transitions(self):
        """Compare current state to previous and log any transitions."""
        current = self._build_snapshot()
        prev = self._prev_state

        if current.vcu_mode_name != prev.vcu_mode_name:
            transition = (prev.vcu_mode_name, current.vcu_mode_name)
            expected = transition in VALID_TRANSITIONS
            if not expected:
                self._unexpected_count += 1

            event = TransitionEvent(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                elapsed_s=round(time.time() - self._start_time, 3),
                from_state=prev.vcu_mode_name,
                to_state=current.vcu_mode_name,
                trigger='VCU_PowerMode',
                expected=expected,
                soc=current.soc,
            )
            self._transitions.append(event)
            self._log_event(event)
            self._print_event(event)

        self._prev_state = current

    def _log_event(self, event: TransitionEvent):
        """Append transition to CSV log."""
        write_header = not os.path.exists(self._log_path) or os.path.getsize(self._log_path) == 0
        with open(self._log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['Timestamp', 'Elapsed(s)', 'From', 'To',
                                  'Trigger', 'Expected', 'SoC(%)'])
            writer.writerow([
                event.timestamp, event.elapsed_s,
                event.from_state, event.to_state,
                event.trigger,
                'YES' if event.expected else 'NO',
                f"{event.soc:.1f}"
            ])

    def _print_event(self, event: TransitionEvent):
        marker = "  " if event.expected else "  *** UNEXPECTED *** "
        print(f"[{event.timestamp}] +{event.elapsed_s:8.3f}s  "
              f"{event.from_state:12} → {event.to_state:12}  "
              f"SoC={event.soc:.1f}%{marker}")

    def print_summary(self):
        """Print monitoring session summary."""
        elapsed = time.time() - self._start_time
        print("\n" + "═" * 65)
        print(f"  VEHICLE STATE MONITOR — SUMMARY")
        print("═" * 65)
        print(f"  Duration:             {elapsed:.1f}s")
        print(f"  Total transitions:    {len(self._transitions)}")
        print(f"  Unexpected:           {self._unexpected_count}")
        print(f"  Log file:             {self._log_path}")
        current = self._build_snapshot()
        print(f"  Final state:          {current.vcu_mode_name}")
        print(f"  Final SoC:            {current.soc:.1f}%")
        print("═" * 65)


def run_monitor(args):
    db = cantools.database.load_file(args.dbc)
    os.makedirs('reports', exist_ok=True)
    log_path = f"reports/state_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    monitor = VehicleStateMonitor(db, log_path)

    bus = can.interface.Bus(
        channel=args.channel, bustype=args.interface, bitrate=args.bitrate
    )

    print(f"[StateMonitor] Monitoring {args.channel} | duration={args.duration}s")
    print(f"[StateMonitor] Log: {log_path}\n")
    print(f"{'Timestamp':26} {'Elapsed':>10}  {'From':12} → {'To':12}  {'SoC':6}")
    print("-" * 75)

    start = time.time()
    last_check = start

    try:
        while (time.time() - start) < args.duration:
            msg = bus.recv(timeout=0.05)
            if msg and not msg.is_error_frame:
                monitor.feed(msg)

            if time.time() - last_check >= 0.1:   # Check state at 10Hz
                monitor.check_transitions()
                last_check = time.time()

    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()

    monitor.print_summary()


def main():
    parser = argparse.ArgumentParser(description='Vehicle State Monitor')
    parser.add_argument('--dbc',       required=True)
    parser.add_argument('--channel',   default='PCAN_USBBUS1')
    parser.add_argument('--interface', default='pcan')
    parser.add_argument('--bitrate',   type=int, default=500000)
    parser.add_argument('--duration',  type=int, default=3600,
                        help='Monitoring duration in seconds (default: 1 hour)')
    args = parser.parse_args()
    run_monitor(args)


if __name__ == '__main__':
    main()
