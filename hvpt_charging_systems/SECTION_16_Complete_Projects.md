# SECTION 16 — COMPLETE END-TO-END PROJECTS
## 5 Production-Grade EV Powertrain Projects with Full Source Code

---

## PROJECT 1: EV Battery State Monitor with CAN + Python Dashboard

### Architecture

```
PROJECT FOLDER STRUCTURE:
ev_battery_monitor/
├── README.md
├── requirements.txt
├── config/
│   ├── settings.yaml           # CAN interface config
│   └── signals.yaml            # Signals to monitor
├── src/
│   ├── __init__.py
│   ├── can_reader.py           # CAN bus reader thread
│   ├── signal_decoder.py       # DBC-based decoder
│   ├── data_logger.py          # CSV/SQLite logging
│   └── dashboard.py            # Tkinter live dashboard
├── dbc/
│   └── EV_BMS.dbc              # BMS DBC file (example)
├── tests/
│   ├── test_decoder.py
│   └── test_logger.py
└── run.py                      # Entry point
```

### requirements.txt
```
python-can==4.3.1
cantools==39.4.4
pyyaml==6.0.1
pandas==2.1.0
matplotlib==3.8.0
```

### config/settings.yaml
```yaml
can:
  interface: pcan          # pcan / socketcan / vector
  channel: PCAN_USBBUS1
  bitrate: 500000

logging:
  csv_path: logs/bms_data.csv
  log_interval_ms: 100

dashboard:
  update_interval_ms: 200
  window_title: "EV Battery Monitor"
```

### config/signals.yaml
```yaml
signals:
  - name: BMS_SoC
    message_id: 0x310
    message_name: BMS_Status
    unit: "%"
    min: 0
    max: 100
    warn_low: 10
    warn_high: 95
    color: "#00FF88"

  - name: BMS_PackVoltage
    message_id: 0x310
    message_name: BMS_Status
    unit: "V"
    min: 280
    max: 420
    warn_low: 300
    warn_high: 415
    color: "#88AAFF"

  - name: BMS_PackCurrent
    message_id: 0x310
    message_name: BMS_Status
    unit: "A"
    min: -300
    max: 300
    warn_low: -290
    warn_high: 290
    color: "#FFAA44"

  - name: BMS_MaxCellTemp
    message_id: 0x311
    message_name: BMS_Thermal
    unit: "°C"
    min: -30
    max: 80
    warn_low: -10
    warn_high: 55
    color: "#FF6688"
```

### src/can_reader.py
```python
"""
CAN Bus Reader with Thread-Safe Callback Architecture
Supports: PCAN, SocketCAN, Vector interfaces
"""
import can
import threading
import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CANReader:
    """Thread-safe CAN bus message reader with callback dispatch."""

    def __init__(self, interface: str, channel: str, bitrate: int):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[can.Bus] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[int, List[Callable]] = {}
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Open CAN bus connection."""
        try:
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.interface,
                bitrate=self.bitrate
            )
            self._running = True
            self._thread = threading.Thread(
                target=self._receive_loop,
                name="CAN_RxThread",
                daemon=True
            )
            self._thread.start()
            logger.info(f"CAN connected: {self.interface}:{self.channel} @{self.bitrate}")
            return True
        except Exception as e:
            logger.error(f"CAN connect failed: {e}")
            return False

    def disconnect(self):
        """Close CAN bus connection."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.bus:
            self.bus.shutdown()
        logger.info("CAN disconnected")

    def register_callback(self, arb_id: int, callback: Callable):
        """Register callback for specific CAN ID. Thread-safe."""
        with self._lock:
            if arb_id not in self._callbacks:
                self._callbacks[arb_id] = []
            self._callbacks[arb_id].append(callback)

    def register_catch_all(self, callback: Callable):
        """Register callback for ALL messages (use ID -1)."""
        self.register_callback(-1, callback)

    def _receive_loop(self):
        """Background receive thread. Dispatches to registered callbacks."""
        while self._running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None:
                    continue

                with self._lock:
                    # Dispatch to specific ID callbacks
                    cbs = list(self._callbacks.get(msg.arbitration_id, []))
                    # Dispatch to catch-all callbacks
                    cbs += list(self._callbacks.get(-1, []))

                for cb in cbs:
                    try:
                        cb(msg)
                    except Exception as e:
                        logger.warning(f"Callback error for {msg.arbitration_id:#x}: {e}")

            except Exception as e:
                if self._running:
                    logger.error(f"CAN receive error: {e}")
```

### src/signal_decoder.py
```python
"""
DBC-based CAN signal decoder with signal cache.
"""
import cantools
import logging
from typing import Dict, Any, Optional
import can

logger = logging.getLogger(__name__)


class SignalDecoder:
    """Decodes CAN messages using DBC file."""

    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        self._cache: Dict[int, Any] = {}  # Latest decoded values per ID
        logger.info(f"DBC loaded: {dbc_path}, {len(self.db.messages)} messages")

    def decode(self, msg: can.Message) -> Optional[Dict[str, float]]:
        """Decode a CAN message. Returns dict of signal_name→value or None."""
        try:
            msg_def = self.db.get_message_by_frame_id(msg.arbitration_id)
            decoded = msg_def.decode(bytes(msg.data), decode_choices=False)
            # Cache latest values
            self._cache[msg.arbitration_id] = decoded
            return decoded
        except (KeyError, cantools.database.errors.DecodeError):
            return None

    def get_signal_value(self, signal_name: str) -> Optional[float]:
        """Get latest cached value for a signal by name."""
        for decoded in self._cache.values():
            if signal_name in decoded:
                return decoded[signal_name]
        return None

    def get_message_name(self, arb_id: int) -> str:
        """Get message name from CAN ID."""
        try:
            return self.db.get_message_by_frame_id(arb_id).name
        except KeyError:
            return f"0x{arb_id:03X}"
```

### src/data_logger.py
```python
"""
CSV logger for CAN signal data with periodic flush.
"""
import csv
import os
import time
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DataLogger:
    """Periodic CSV logger for signal data."""

    def __init__(self, csv_path: str, signal_names: list, interval_ms: int = 100):
        self.csv_path = csv_path
        self.signal_names = signal_names
        self.interval_s = interval_ms / 1000.0
        self._current = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        self._init_csv()

    def _init_csv(self):
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp'] + self.signal_names)

    def update(self, signal_name: str, value: float):
        """Update current value for a signal."""
        with self._lock:
            self._current[signal_name] = value

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._log_loop, name="LoggerThread", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _log_loop(self):
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            while self._running:
                time.sleep(self.interval_s)
                with self._lock:
                    row = [time.time()] + [
                        self._current.get(s, '') for s in self.signal_names
                    ]
                writer.writerow(row)
                f.flush()
```

### src/dashboard.py
```python
"""
Live Tkinter dashboard for BMS signal monitoring.
Dark theme with color-coded signal cards.
"""
import tkinter as tk
import threading
import time
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

BG = "#1A1A2E"
CARD_BG = "#16213E"
TEXT_FG = "#E0E0E0"
LABEL_FG = "#888888"
WARN_COLOR = "#FF6600"
FAULT_COLOR = "#FF2244"


class SignalCard(tk.Frame):
    """Individual signal display card."""

    def __init__(self, parent, signal_config: dict):
        super().__init__(parent, bg=CARD_BG, padx=10, pady=8,
                         highlightbackground="#333", highlightthickness=1)
        self.config = signal_config
        self.normal_color = signal_config.get('color', '#FFFFFF')

        self.name_label = tk.Label(
            self, text=signal_config['name'],
            bg=CARD_BG, fg=LABEL_FG, font=("Consolas", 10)
        )
        self.name_label.pack()

        self.value_label = tk.Label(
            self, text="---",
            bg=CARD_BG, fg=self.normal_color, font=("Consolas", 28, "bold")
        )
        self.value_label.pack()

        self.unit_label = tk.Label(
            self, text=signal_config.get('unit', ''),
            bg=CARD_BG, fg=LABEL_FG, font=("Consolas", 10)
        )
        self.unit_label.pack()

    def update_value(self, value: float):
        """Update displayed value with color coding."""
        unit = self.config.get('unit', '')
        self.value_label.config(text=f"{value:.1f}")

        warn_low = self.config.get('warn_low')
        warn_high = self.config.get('warn_high')
        if warn_low is not None and value <= warn_low:
            color = WARN_COLOR
        elif warn_high is not None and value >= warn_high:
            color = FAULT_COLOR
        else:
            color = self.normal_color

        self.value_label.config(fg=color)


class Dashboard:
    """Main dashboard window."""

    def __init__(self, title: str, signals_config: list, update_interval_ms: int = 200):
        self.signals_config = signals_config
        self.update_interval_ms = update_interval_ms
        self._values: Dict[str, float] = {}
        self._lock = threading.Lock()

        self.root = tk.Tk()
        self.root.title(title)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self._cards: Dict[str, SignalCard] = {}
        self._build_ui()

    def _build_ui(self):
        # Title bar
        tk.Label(
            self.root,
            text="EV BATTERY MONITOR",
            bg=BG, fg="#00FFAA",
            font=("Consolas", 14, "bold")
        ).grid(row=0, column=0, columnspan=4, pady=(10, 5))

        # Status bar
        self.status_var = tk.StringVar(value="CAN: Connecting...")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=BG, fg=LABEL_FG, font=("Consolas", 9)
        ).grid(row=1, column=0, columnspan=4)

        # Signal cards in grid
        cols = 4
        for i, sig in enumerate(self.signals_config):
            row = 2 + i // cols
            col = i % cols
            card = SignalCard(self.root, sig)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self._cards[sig['name']] = card

        for c in range(cols):
            self.root.columnconfigure(c, weight=1)

    def update_signal(self, name: str, value: float):
        """Thread-safe signal value update."""
        with self._lock:
            self._values[name] = value

    def set_status(self, text: str):
        """Update status bar text."""
        self.status_var.set(text)

    def _poll_updates(self):
        """Periodic UI update from main thread."""
        with self._lock:
            values = dict(self._values)

        for name, value in values.items():
            if name in self._cards:
                self._cards[name].update_value(value)

        self.root.after(self.update_interval_ms, self._poll_updates)

    def run(self):
        """Start dashboard (blocking, must run on main thread)."""
        self.root.after(self.update_interval_ms, self._poll_updates)
        self.root.mainloop()
```

### run.py
```python
"""
EV Battery Monitor — Entry Point
"""
import yaml
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from can_reader import CANReader
from signal_decoder import SignalDecoder
from data_logger import DataLogger
from dashboard import Dashboard

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s: %(message)s')

def main():
    with open('config/settings.yaml') as f:
        settings = yaml.safe_load(f)
    with open('config/signals.yaml') as f:
        signals_cfg = yaml.safe_load(f)['signals']

    # Initialize components
    decoder = SignalDecoder('dbc/EV_BMS.dbc')
    signal_names = [s['name'] for s in signals_cfg]
    logger_csv = DataLogger(
        settings['logging']['csv_path'],
        signal_names,
        settings['logging']['log_interval_ms']
    )
    dashboard = Dashboard(
        settings['dashboard']['window_title'],
        signals_cfg,
        settings['dashboard']['update_interval_ms']
    )

    # CAN reader
    can_cfg = settings['can']
    reader = CANReader(can_cfg['interface'], can_cfg['channel'], can_cfg['bitrate'])

    def on_message(msg):
        decoded = decoder.decode(msg)
        if decoded:
            for name, value in decoded.items():
                logger_csv.update(name, value)
                dashboard.update_signal(name, value)

    reader.register_catch_all(on_message)

    if reader.connect():
        dashboard.set_status(f"CAN: Connected ({can_cfg['channel']})")
    else:
        dashboard.set_status("CAN: DISCONNECTED — Check hardware!")

    logger_csv.start()
    dashboard.run()  # Blocking main thread

    logger_csv.stop()
    reader.disconnect()


if __name__ == '__main__':
    main()
```

---

## PROJECT 2: Automated BMS UDS Diagnostic Test Suite

### Project Structure
```
bms_uds_test_suite/
├── README.md
├── requirements.txt
├── conftest.py             # Pytest fixtures
├── config/
│   └── ecu_config.yaml     # ECU addresses, DID list
├── tests/
│   ├── test_sessions.py    # Session management tests
│   ├── test_dids.py        # DID read/write tests
│   ├── test_dtcs.py        # DTC lifecycle tests
│   └── test_security.py    # Security access tests
└── reports/                # Auto-generated HTML reports
```

### conftest.py
```python
"""
Pytest fixtures for BMS UDS test suite.
"""
import pytest
import yaml
import can
import isotp
import udsoncan

CONFIG_PATH = 'config/ecu_config.yaml'


@pytest.fixture(scope='session')
def ecu_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope='session')
def can_bus(ecu_config):
    """Session-scoped CAN bus connection."""
    bus = can.interface.Bus(
        channel=ecu_config['can']['channel'],
        bustype=ecu_config['can']['interface'],
        bitrate=ecu_config['can']['bitrate']
    )
    yield bus
    bus.shutdown()


@pytest.fixture(scope='function')
def uds_client(can_bus, ecu_config):
    """Function-scoped UDS client (fresh session per test)."""
    bms_cfg = ecu_config['ecus']['BMS']
    addr = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        txid=bms_cfg['tx_id'],
        rxid=bms_cfg['rx_id']
    )
    conn = udsoncan.connections.PythonIsoTpConnection(can_bus, addr)
    conn.open()

    with udsoncan.client.Client(conn, request_timeout=2.0) as client:
        yield client

    conn.close()
```

### tests/test_dtcs.py
```python
"""
BMS DTC Lifecycle Test Cases.
Tests: clear DTCs, force fault conditions, verify DTC creation.
"""
import pytest
import udsoncan
import time


class TestDTCLifecycle:

    def test_clear_dtcs_in_extended_session(self, uds_client):
        """TC-DTC-001: Verify DTCs can be cleared in Extended session."""
        uds_client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
        response = uds_client.clear_dtc(group=0xFFFFFF)
        assert response.positive, f"ClearDTC failed: {response}"

    def test_no_dtcs_after_clear(self, uds_client):
        """TC-DTC-002: After ClearDTC, no DTCs should be present."""
        uds_client.change_session(0x03)
        uds_client.clear_dtc(group=0xFFFFFF)
        time.sleep(0.5)

        dtcs = uds_client.get_dtc_by_status_mask(0xFF)
        assert len(dtcs.dtcs) == 0, f"Expected 0 DTCs, found {len(dtcs.dtcs)}"

    def test_read_dtc_count(self, uds_client):
        """TC-DTC-003: Read DTC count service should succeed."""
        response = uds_client.get_number_of_dtc_by_status_mask(0x09)  # confirmed + active
        assert response.positive
        count = response.service_data.dtc_count
        assert isinstance(count, int) and count >= 0

    @pytest.mark.parametrize("status_mask,description", [
        (0x01, "testFailed"),
        (0x08, "confirmedDTC"),
        (0x0F, "testFailed+confirmed"),
        (0xFF, "all statuses"),
    ])
    def test_dtc_read_by_status_mask(self, uds_client, status_mask, description):
        """TC-DTC-004: ReadDTCByStatusMask with various masks should succeed."""
        response = uds_client.get_dtc_by_status_mask(status_mask)
        assert response.positive, f"Failed for mask {status_mask:#x} ({description})"
```

### tests/test_dids.py
```python
"""
BMS DID read/write test cases.
"""
import pytest
import yaml


with open('config/ecu_config.yaml') as f:
    _cfg = yaml.safe_load(f)
DID_LIST = _cfg.get('dids', {})


class TestBMSDIDs:

    @pytest.mark.parametrize("did_hex,description", [
        (0xF190, "VIN"),
        (0xF121, "BMS_SoH"),
        (0xF180, "SW_Version"),
        (0xF182, "ECU_ManufacturingDate"),
        (0xF18C, "ECU_SerialNumber"),
        (0xF101, "BMS_SoC"),
        (0xF110, "BMS_PackVoltage"),
        (0xF111, "BMS_PackCurrent"),
    ])
    def test_did_readable(self, uds_client, did_hex, description):
        """Verify DID is readable in Default session."""
        response = uds_client.read_data_by_identifier(did_hex)
        assert response.positive, \
            f"DID {did_hex:#06x} ({description}) failed: {response.code_name}"
        assert len(response.service_data.values[did_hex]) > 0

    def test_vin_format(self, uds_client):
        """TC-DID-001: VIN (0xF190) must be exactly 17 ASCII characters."""
        response = uds_client.read_data_by_identifier(0xF190)
        assert response.positive
        vin_bytes = response.service_data.values[0xF190]
        assert len(vin_bytes) == 17, f"VIN length {len(vin_bytes)} != 17"
        vin_str = bytes(vin_bytes).decode('ascii', errors='replace')
        assert vin_str.isalnum(), f"VIN contains non-alphanumeric: {vin_str}"

    def test_soc_range(self, uds_client):
        """TC-DID-002: BMS_SoC (0xF101) must be in range [0, 100]."""
        response = uds_client.read_data_by_identifier(0xF101)
        assert response.positive
        raw = response.service_data.values[0xF101]
        soc = int.from_bytes(raw[:2], 'big') * 0.5  # scale 0.5 per DBC
        assert 0.0 <= soc <= 100.0, f"SoC out of range: {soc}%"
```

---

## PROJECT 3: CAN Bus Log Analyzer

### Project Structure
```
can_log_analyzer/
├── README.md
├── requirements.txt
├── analyzer.py         # Main entry point
├── parsers/
│   ├── blf_parser.py   # .blf file parser
│   └── asc_parser.py   # .asc file parser
├── analyzers/
│   ├── timing.py       # Message timing analysis
│   ├── bus_load.py     # Bus load calculator
│   └── signal_plot.py  # Signal plotting
└── reports/
    └── report_template.html
```

### analyzer.py
```python
"""
CAN Bus Log Analyzer
Usage: python analyzer.py --log test.blf --dbc EV_BMS.dbc --output report.html
"""
import argparse
import can
import cantools
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime


def parse_blf(blf_path: str, db) -> pd.DataFrame:
    """Parse .blf log file into DataFrame with decoded signals."""
    records = []
    with can.LogReader(blf_path) as reader:
        for msg in reader:
            try:
                msg_def = db.get_message_by_frame_id(msg.arbitration_id)
                decoded = msg_def.decode(bytes(msg.data), decode_choices=False)
                for sig, val in decoded.items():
                    records.append({
                        'timestamp': msg.timestamp,
                        'can_id': msg.arbitration_id,
                        'message': msg_def.name,
                        'signal': sig,
                        'value': float(val)
                    })
            except (KeyError, Exception):
                pass
    return pd.DataFrame(records)


def calculate_bus_load(blf_path: str, bitrate: int = 500000,
                       window_s: float = 1.0) -> pd.DataFrame:
    """Calculate CAN bus load over time windows."""
    records = []
    with can.LogReader(blf_path) as reader:
        for msg in reader:
            # Each CAN frame = 47 bits overhead + 8 × DLC bits (approx)
            bits = 47 + 8 * (msg.dlc or 0)
            records.append({'timestamp': msg.timestamp, 'bits': bits})

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df['window'] = (df['timestamp'] / window_s).astype(int) * window_s
    load = df.groupby('window').agg(total_bits=('bits', 'sum')).reset_index()
    load['load_percent'] = (load['total_bits'] / (bitrate * window_s)) * 100
    return load


def analyze_message_timing(df: pd.DataFrame, message_name: str) -> dict:
    """Analyze cycle time statistics for a specific message."""
    msg_df = df[df['message'] == message_name].drop_duplicates('timestamp')
    if len(msg_df) < 2:
        return {}

    timestamps = sorted(msg_df['timestamp'].unique())
    periods_ms = [1000 * (timestamps[i+1] - timestamps[i])
                  for i in range(len(timestamps)-1)]

    return {
        'message': message_name,
        'count': len(timestamps),
        'mean_period_ms': sum(periods_ms) / len(periods_ms),
        'max_period_ms': max(periods_ms),
        'min_period_ms': min(periods_ms),
        'jitter_ms': max(periods_ms) - min(periods_ms),
    }


def plot_signal(df: pd.DataFrame, signal_name: str, output_path: str):
    """Plot signal over time and save as PNG."""
    sig_df = df[df['signal'] == signal_name].sort_values('timestamp')
    if sig_df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    t0 = sig_df['timestamp'].iloc[0]
    ax.plot(sig_df['timestamp'] - t0, sig_df['value'],
            color='#00AAFF', linewidth=0.8)
    ax.set_title(f"Signal: {signal_name}", color='white')
    ax.set_xlabel("Time [s]", color='white')
    ax.set_ylabel(signal_name, color='white')
    ax.set_facecolor('#1A1A2E')
    fig.patch.set_facecolor('#1A1A2E')
    ax.tick_params(colors='white')
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='CAN Bus Log Analyzer')
    parser.add_argument('--log', required=True, help='.blf or .asc log file')
    parser.add_argument('--dbc', required=True, help='DBC file path')
    parser.add_argument('--output', default='reports/analysis.html',
                        help='Output HTML report path')
    parser.add_argument('--bitrate', type=int, default=500000)
    args = parser.parse_args()

    print(f"Loading DBC: {args.dbc}")
    db = cantools.database.load_file(args.dbc)

    print(f"Parsing log: {args.log}")
    df = parse_blf(args.log, db)
    print(f"  Decoded {len(df)} signal samples from {df['message'].nunique()} messages")

    bus_load = calculate_bus_load(args.log, args.bitrate)
    max_load = bus_load['load_percent'].max() if not bus_load.empty else 0

    # Timing analysis for key messages
    timing_results = []
    for msg_name in df['message'].unique():
        stats = analyze_message_timing(df, msg_name)
        if stats:
            timing_results.append(stats)

    # Generate HTML report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<title>CAN Log Analysis</title>
<style>
  body {{ background: #1A1A2E; color: #E0E0E0; font-family: Consolas, monospace; padding: 20px; }}
  h1 {{ color: #00FFAA; }}
  h2 {{ color: #88AAFF; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
  th {{ background: #16213E; color: #00FFAA; padding: 8px; text-align: left; }}
  td {{ padding: 6px; border-bottom: 1px solid #333; }}
  tr:hover {{ background: #16213E; }}
  .warn {{ color: #FF6600; font-weight: bold; }}
  .pass {{ color: #00FF88; }}
</style>
</head>
<body>
<h1>CAN Bus Log Analysis Report</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>Log file: {args.log}</p>
<p>DBC file: {args.dbc}</p>

<h2>Bus Load Summary</h2>
<p>Peak bus load: <span class="{'warn' if max_load > 60 else 'pass'}">{max_load:.1f}%</span>
   (limit: 60%)</p>

<h2>Message Timing Analysis</h2>
<table>
<tr><th>Message</th><th>Count</th><th>Mean Period (ms)</th>
    <th>Max Period (ms)</th><th>Min Period (ms)</th><th>Jitter (ms)</th></tr>
""")
        for r in sorted(timing_results, key=lambda x: x['message']):
            jitter_class = 'warn' if r['jitter_ms'] > 5 else 'pass'
            f.write(f"""<tr>
  <td>{r['message']}</td>
  <td>{r['count']}</td>
  <td>{r['mean_period_ms']:.2f}</td>
  <td class="{'warn' if r['max_period_ms'] > r['mean_period_ms']*1.5 else ''}">{r['max_period_ms']:.2f}</td>
  <td>{r['min_period_ms']:.2f}</td>
  <td class="{jitter_class}">{r['jitter_ms']:.2f}</td>
</tr>""")
        f.write("</table></body></html>")

    print(f"Report saved: {args.output}")


if __name__ == '__main__':
    main()
```

---

## PROJECT 4: CAPL BMS Full Simulation Node

### battery_ecu_simulation.can
```c
/*
 * battery_ecu_simulation.can
 * Complete BMS Simulation Node for CANoe
 * Simulates: SoC, Voltages, Currents, Temperatures, Faults, Precharge
 *
 * Author: EV Test Team
 * Standard: ISO 11898, vehicle DBC v2.3
 */

includes
{
}

variables
{
  // ── Timers ───────────────────────────────────────────────────────────
  msTimer tmrBMSStatus;      // 10ms cyclic
  msTimer tmrBMSThermal;     // 100ms cyclic
  msTimer tmrBMSFault;       // 50ms cyclic
  msTimer tmrPrecharge;      // 1ms resolution for precharge
  msTimer tmrFaultMonitor;   // 100ms fault monitoring

  // ── State Machine ───────────────────────────────────────────────────
  int    bmsState;           // 0=INIT,1=IDLE,2=READY,3=PRECHARGE,4=ACTIVE,5=FAULT,6=CHARGE
  const int BMS_INIT      = 0;
  const int BMS_IDLE      = 1;
  const int BMS_READY     = 2;
  const int BMS_PRECHARGE = 3;
  const int BMS_ACTIVE    = 4;
  const int BMS_FAULT     = 5;
  const int BMS_CHARGE    = 6;

  // ── Battery Parameters ───────────────────────────────────────────────
  float  soc;                // State of Charge [%]
  float  packVoltage;        // Pack voltage [V]
  float  packCurrent;        // Pack current [A] (positive=discharge)
  float  maxCellVoltage;     // Highest cell voltage [V]
  float  minCellVoltage;     // Lowest cell voltage [V]
  float  packTemp;           // Pack temperature [°C]
  float  maxCellTemp;        // Max cell temperature [°C]
  float  minCellTemp;        // Min cell temperature [°C]
  float  isolationResistance;// HV isolation resistance [kΩ]
  float  soh;                // State of Health [%]

  // ── Limits ───────────────────────────────────────────────────────────
  float  chargePowerLimit;   // Max charge power [kW]
  float  dischargePowerLimit;// Max discharge power [kW]
  float  maxChargeCurrent;   // Max charge current [A]
  float  maxDischargeCurrent;// Max discharge current [A]

  // ── Fault Flags ──────────────────────────────────────────────────────
  int    faultOverVoltage;
  int    faultUnderVoltage;
  int    faultOverTemp;
  int    faultIsolation;
  int    faultContactorWeld;
  int    faultCANTimeout;
  int    faultPrechargeTimeout;

  // ── Simulation Config ────────────────────────────────────────────────
  float  simCurrentLoad;     // External current load for SoC simulation
  float  capacity_Ah;        // Battery capacity [Ah]
  float  nominalVoltage;     // Nominal pack voltage [V]
  int    cellCountSeries;    // Cells in series
  int    cellCountParallel;  // Cells in parallel

  // ── Precharge tracking ───────────────────────────────────────────────
  float  dcLinkVoltage;      // DC link voltage [V]
  int    prechargeTimeMs;    // Precharge elapsed time
  const int PRECHARGE_TIMEOUT_MS = 5000;  // 5 second timeout
}

/*──────────────────────────────────────────────────────────────────────
  INITIALIZATION
──────────────────────────────────────────────────────────────────────*/
on preStart
{
  // Initialize battery parameters
  soc               = 75.0;        // Start at 75% SoC
  packVoltage       = 396.0;       // [V]
  packCurrent       = 0.0;         // [A]
  maxCellVoltage    = 3.960;       // [V]
  minCellVoltage    = 3.950;       // [V]
  packTemp          = 25.0;        // [°C]
  maxCellTemp       = 25.0;        // [°C]
  minCellTemp       = 24.5;        // [°C]
  isolationResistance = 5000.0;    // [kΩ] — healthy
  soh               = 95.0;        // [%]

  // Limits (can be commanded by VCU)
  chargePowerLimit      = 50.0;    // [kW]
  dischargePowerLimit   = 100.0;   // [kW]
  maxChargeCurrent      = 100.0;   // [A]
  maxDischargeCurrent   = 250.0;   // [A]

  // Fault flags all clear
  faultOverVoltage        = 0;
  faultUnderVoltage       = 0;
  faultOverTemp           = 0;
  faultIsolation          = 0;
  faultContactorWeld      = 0;
  faultCANTimeout         = 0;
  faultPrechargeTimeout   = 0;

  // Simulation parameters
  simCurrentLoad    = 0.0;
  capacity_Ah       = 60.0;
  nominalVoltage    = 400.0;
  cellCountSeries   = 100;
  cellCountParallel = 3;
  dcLinkVoltage     = 0.0;
  prechargeTimeMs   = 0;

  bmsState = BMS_INIT;
}

on start
{
  // Start cyclic timers
  setTimer(tmrBMSStatus,    10);   // 10ms
  setTimer(tmrBMSThermal,   100);  // 100ms
  setTimer(tmrBMSFault,     50);   // 50ms
  setTimer(tmrFaultMonitor, 100);  // 100ms

  bmsState = BMS_IDLE;
  write("[BMS_SIM] Battery ECU Simulation STARTED. State=IDLE, SoC=%.1f%%", soc);
}

/*──────────────────────────────────────────────────────────────────────
  10ms CYCLIC — BMS_Status Message (0x310)
──────────────────────────────────────────────────────────────────────*/
on timer tmrBMSStatus
{
  message BMS_Status bmsMsg;

  // Update SoC via Coulomb counting simulation
  if (bmsState == BMS_ACTIVE && simCurrentLoad != 0.0) {
    // SoC decrement: ΔSoC = (I × Δt) / (3600 × Ah)
    float deltaSoc = (simCurrentLoad * 0.010) / (3600.0 * capacity_Ah) * 100.0;
    soc -= deltaSoc;
    if (soc < 0.0) soc = 0.0;
    if (soc > 100.0) soc = 100.0;
  }

  // Calculate pack voltage from SoC (simplified linear model)
  // SoC 0%→20%: 300-350V, 20%→80%: 350-410V, 80%→100%: 410-420V
  if (soc < 20.0)
    packVoltage = 300.0 + (soc / 20.0) * 50.0;
  else if (soc < 80.0)
    packVoltage = 350.0 + ((soc - 20.0) / 60.0) * 60.0;
  else
    packVoltage = 410.0 + ((soc - 80.0) / 20.0) * 10.0;

  maxCellVoltage = packVoltage / cellCountSeries;
  minCellVoltage = maxCellVoltage - 0.010;  // 10mV imbalance

  // Populate CAN message
  bmsMsg.BMS_SoC             = (word)(soc * 2.0);       // scale 0.5, raw = SoC/0.5
  bmsMsg.BMS_PackVoltage     = (word)(packVoltage * 10.0); // scale 0.1
  bmsMsg.BMS_PackCurrent     = (int)(packCurrent * 10.0);  // scale 0.1, signed
  bmsMsg.BMS_MaxCellVoltage  = (word)(maxCellVoltage * 1000.0); // scale 0.001 [mV]
  bmsMsg.BMS_MinCellVoltage  = (word)(minCellVoltage * 1000.0);
  bmsMsg.BMS_State           = bmsState;
  bmsMsg.BMS_FaultCode       = getFaultCode();

  output(bmsMsg);
  setTimer(tmrBMSStatus, 10);
}

/*──────────────────────────────────────────────────────────────────────
  100ms CYCLIC — BMS_Thermal, BMS_Limits
──────────────────────────────────────────────────────────────────────*/
on timer tmrBMSThermal
{
  message BMS_Thermal thermalMsg;
  message BMS_Limits  limitsMsg;

  // Temperature model: increase during high current
  if (packCurrent > 100.0) {
    maxCellTemp += 0.2;  // Rising during high discharge
    minCellTemp += 0.15;
  } else if (packCurrent < -50.0) {
    maxCellTemp += 0.1;  // Slight rise during fast charge
  } else {
    // Cooling towards ambient
    if (maxCellTemp > 25.0) maxCellTemp -= 0.05;
    if (minCellTemp > 24.0) minCellTemp -= 0.03;
  }

  thermalMsg.BMS_MaxCellTemp  = (byte)(maxCellTemp + 40.0); // offset -40°C
  thermalMsg.BMS_MinCellTemp  = (byte)(minCellTemp + 40.0);
  thermalMsg.BMS_PackTemp     = (byte)(packTemp + 40.0);
  thermalMsg.BMS_CoolantTemp  = (byte)(22.0 + 40.0);
  output(thermalMsg);

  // Derate limits at high temperature
  if (maxCellTemp > 50.0) {
    dischargePowerLimit = 100.0 * (1.0 - (maxCellTemp - 50.0) / 30.0);
    if (dischargePowerLimit < 10.0) dischargePowerLimit = 10.0;
  } else {
    dischargePowerLimit = 100.0;
  }

  // Derate limits at low SoC
  if (soc < 10.0) {
    dischargePowerLimit *= (soc / 10.0);
    if (dischargePowerLimit < 5.0) dischargePowerLimit = 5.0;
  }

  limitsMsg.BMS_MaxChargeCurrent    = (word)(maxChargeCurrent * 10.0);
  limitsMsg.BMS_MaxDischargeCurrent = (word)(maxDischargeCurrent * 10.0);
  limitsMsg.BMS_ChargePowerLimit    = (word)(chargePowerLimit * 10.0);
  limitsMsg.BMS_DischargePowerLimit = (word)(dischargePowerLimit * 10.0);
  limitsMsg.BMS_SoH                 = (byte)(soh * 2.0);
  limitsMsg.BMS_IsolationResistance = (word)(isolationResistance);
  output(limitsMsg);

  setTimer(tmrBMSThermal, 100);
}

/*──────────────────────────────────────────────────────────────────────
  50ms CYCLIC — Fault Detection
──────────────────────────────────────────────────────────────────────*/
on timer tmrFaultMonitor
{
  // Over-voltage check
  if (maxCellVoltage > 4.25) {
    if (!faultOverVoltage) {
      faultOverVoltage = 1;
      write("[BMS_SIM] FAULT: Cell Overvoltage! Max=%.3fV", maxCellVoltage);
      OpenContactors();
    }
  } else if (maxCellVoltage < 4.20) {
    faultOverVoltage = 0;  // Hysteresis clear
  }

  // Under-voltage check
  if (minCellVoltage < 2.80) {
    if (!faultUnderVoltage) {
      faultUnderVoltage = 1;
      write("[BMS_SIM] FAULT: Cell Undervoltage! Min=%.3fV", minCellVoltage);
      OpenContactors();
    }
  } else if (minCellVoltage > 2.90) {
    faultUnderVoltage = 0;
  }

  // Over-temperature check
  if (maxCellTemp > 60.0) {
    if (!faultOverTemp) {
      faultOverTemp = 1;
      write("[BMS_SIM] FAULT: Over Temperature! T=%.1f°C", maxCellTemp);
      OpenContactors();
    }
  } else if (maxCellTemp < 55.0) {
    faultOverTemp = 0;
  }

  // Isolation fault check
  if (isolationResistance < 100.0) {  // 100 kΩ threshold
    if (!faultIsolation) {
      faultIsolation = 1;
      write("[BMS_SIM] FAULT: Isolation fault! R=%.0f kΩ", isolationResistance);
      OpenContactors();
    }
  } else if (isolationResistance > 200.0) {
    faultIsolation = 0;
  }

  // Update BMS state based on faults
  if (faultOverVoltage || faultUnderVoltage || faultOverTemp || faultIsolation) {
    bmsState = BMS_FAULT;
  }

  setTimer(tmrFaultMonitor, 100);
}

/*──────────────────────────────────────────────────────────────────────
  VCU COMMAND HANDLER
──────────────────────────────────────────────────────────────────────*/
on message VCU_Command
{
  int hvEnable = this.VCU_HV_Enable;
  int chargeEnable = this.VCU_ChargeEnable;

  if (bmsState == BMS_FAULT) {
    write("[BMS_SIM] VCU command ignored — BMS in FAULT state");
    return;
  }

  if (hvEnable == 1 && bmsState == BMS_IDLE) {
    write("[BMS_SIM] HV Enable command received — starting precharge");
    bmsState = BMS_PRECHARGE;
    dcLinkVoltage = 0.0;
    prechargeTimeMs = 0;
    setTimer(tmrPrecharge, 1);
  }

  if (hvEnable == 0 && (bmsState == BMS_ACTIVE || bmsState == BMS_READY)) {
    write("[BMS_SIM] HV Disable command received — opening contactors");
    OpenContactors();
    bmsState = BMS_IDLE;
  }

  if (chargeEnable == 1 && bmsState == BMS_ACTIVE) {
    bmsState = BMS_CHARGE;
    packCurrent = -20.0;  // Charging: negative current
    write("[BMS_SIM] Charge enabled — entering CHARGE state");
  }
}

/*──────────────────────────────────────────────────────────────────────
  PRECHARGE STATE MACHINE (1ms resolution)
──────────────────────────────────────────────────────────────────────*/
on timer tmrPrecharge
{
  if (bmsState != BMS_PRECHARGE) return;

  prechargeTimeMs++;

  // RC charging model: V(t) = V_batt × (1 - e^(-t/tau))
  // tau = R × C = 100Ω × 1000μF = 100ms
  float tau = 100.0;  // ms
  dcLinkVoltage = packVoltage * (1.0 - exp(-(float)prechargeTimeMs / tau));

  // Check if precharge complete (≥ 95% of pack voltage)
  if (dcLinkVoltage >= packVoltage * 0.95) {
    write("[BMS_SIM] Precharge complete. VDClink=%.1fV in %dms",
          dcLinkVoltage, prechargeTimeMs);
    bmsState = BMS_ACTIVE;
    packCurrent = simCurrentLoad;
    return;  // Don't restart timer
  }

  // Precharge timeout check
  if (prechargeTimeMs >= PRECHARGE_TIMEOUT_MS) {
    faultPrechargeTimeout = 1;
    bmsState = BMS_FAULT;
    write("[BMS_SIM] FAULT: Precharge timeout after %dms. VDClink=%.1fV",
          prechargeTimeMs, dcLinkVoltage);
    return;
  }

  setTimer(tmrPrecharge, 1);
}

/*──────────────────────────────────────────────────────────────────────
  HELPER FUNCTIONS
──────────────────────────────────────────────────────────────────────*/
int getFaultCode()
{
  int code = 0;
  if (faultOverVoltage)        code |= 0x01;
  if (faultUnderVoltage)       code |= 0x02;
  if (faultOverTemp)           code |= 0x04;
  if (faultIsolation)          code |= 0x08;
  if (faultContactorWeld)      code |= 0x10;
  if (faultCANTimeout)         code |= 0x20;
  if (faultPrechargeTimeout)   code |= 0x40;
  return code;
}

void OpenContactors()
{
  // Signal hardware contactor open command
  message BMS_ContactorCommand contCmd;
  contCmd.BMS_MainPosCmd   = 0;
  contCmd.BMS_MainNegCmd   = 0;
  contCmd.BMS_PrechargeCmd = 0;
  output(contCmd);
  packCurrent = 0.0;
  write("[BMS_SIM] Contactors OPENED");
}

/*──────────────────────────────────────────────────────────────────────
  FAULT INJECTION API (for test automation)
──────────────────────────────────────────────────────────────────────*/
on sysvar::FaultInjection::BMS_InjectOverVoltage
{
  if (@this == 1) {
    maxCellVoltage = 4.30;  // Force overvoltage
    write("[BMS_SIM] FAULT INJECTED: Overvoltage (%.3fV)", maxCellVoltage);
  }
}

on sysvar::FaultInjection::BMS_InjectIsolationFault
{
  if (@this == 1) {
    isolationResistance = 30.0;  // Force isolation fault (below 100 kΩ)
    write("[BMS_SIM] FAULT INJECTED: Isolation R=%.0f kΩ", isolationResistance);
  } else {
    isolationResistance = 5000.0;
    faultIsolation = 0;
    write("[BMS_SIM] Isolation fault CLEARED");
  }
}

on sysvar::FaultInjection::BMS_InjectOverTemp
{
  if (@this == 1) {
    maxCellTemp = 65.0;
    write("[BMS_SIM] FAULT INJECTED: Over Temperature (%.1f°C)", maxCellTemp);
  } else {
    maxCellTemp = 25.0;
    faultOverTemp = 0;
    write("[BMS_SIM] Temperature fault CLEARED");
  }
}

on sysvar::FaultInjection::BMS_SetCurrentLoad
{
  simCurrentLoad = (float)@this;
  if (bmsState == BMS_ACTIVE) {
    packCurrent = simCurrentLoad;
    write("[BMS_SIM] Current load set to %.1f A", simCurrentLoad);
  }
}
```

---

## PROJECT 5: Python CAN Regression Test Framework

### Project Structure
```
ev_regression_framework/
├── README.md
├── requirements.txt
├── run_regression.py           # Main runner
├── config/
│   ├── test_config.yaml        # Test suite configuration
│   └── ecu_addresses.yaml      # ECU CAN IDs
├── test_suites/
│   ├── bms_suite.py            # BMS test suite
│   ├── charging_suite.py       # Charging test suite
│   └── network_suite.py        # Network health suite
├── framework/
│   ├── can_client.py           # CAN interface wrapper
│   ├── uds_helper.py           # UDS helper functions
│   └── report_generator.py     # HTML + Excel reports
└── reports/
    └── .gitkeep
```

### run_regression.py
```python
"""
EV Regression Test Framework — Main Runner
Usage: python run_regression.py --suite bms --report html
"""
import argparse
import pytest
import sys
import os
from datetime import datetime
from framework.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description='EV Regression Test Framework')
    parser.add_argument('--suite', choices=['bms', 'charging', 'network', 'all'],
                        default='all', help='Test suite to run')
    parser.add_argument('--report', choices=['html', 'excel', 'both'],
                        default='html', help='Report format')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('reports', exist_ok=True)

    # Select test suite paths
    suite_map = {
        'bms':      ['test_suites/bms_suite.py'],
        'charging': ['test_suites/charging_suite.py'],
        'network':  ['test_suites/network_suite.py'],
        'all':      ['test_suites/']
    }

    pytest_args = suite_map[args.suite]
    html_path = f'reports/regression_{args.suite}_{timestamp}.html'
    pytest_args += [
        f'--html={html_path}',
        '--self-contained-html',
        '-v' if args.verbose else '-q',
        '--tb=short'
    ]

    print(f"Running suite: {args.suite}")
    print(f"Report: {html_path}")
    print("=" * 60)

    exit_code = pytest.main(pytest_args)

    print("=" * 60)
    if exit_code == 0:
        print(f"RESULT: PASS — Report: {html_path}")
    else:
        print(f"RESULT: FAIL (code={exit_code}) — Report: {html_path}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
```

### framework/report_generator.py
```python
"""
Excel + HTML report generator for regression results.
"""
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from datetime import datetime
from typing import List, Dict


PASS_FILL = PatternFill(start_color="00AA44", end_color="00AA44", fill_type="solid")
FAIL_FILL = PatternFill(start_color="CC2233", end_color="CC2233", fill_type="solid")
WARN_FILL = PatternFill(start_color="FF8800", end_color="FF8800", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1A2244", end_color="1A2244", fill_type="solid")
WHITE_FONT = Font(color="FFFFFF", bold=True)


class ReportGenerator:
    """Generates Excel test reports with color-coded verdicts."""

    def __init__(self, project: str = "EV Powertrain"):
        self.project = project
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "Test Results"
        self._write_header()
        self._row = 3

    def _write_header(self):
        headers = ['TC ID', 'Test Name', 'Suite', 'Status',
                   'Duration (s)', 'Timestamp', 'Notes']
        self.ws.merge_cells('A1:G1')
        title_cell = self.ws['A1']
        title_cell.value = f"{self.project} — Regression Test Report"
        title_cell.font = Font(size=14, bold=True, color="FFFFFF")
        title_cell.fill = HEADER_FILL
        title_cell.alignment = Alignment(horizontal='center')

        for col, header in enumerate(headers, 1):
            cell = self.ws.cell(row=2, column=col, value=header)
            cell.font = WHITE_FONT
            cell.fill = HEADER_FILL

        # Column widths
        widths = [15, 40, 20, 10, 15, 22, 40]
        for col, width in enumerate(widths, 1):
            self.ws.column_dimensions[
                openpyxl.utils.get_column_letter(col)
            ].width = width

    def add_result(self, tc_id: str, name: str, suite: str,
                   status: str, duration: float = 0.0, notes: str = ""):
        row = self._row
        values = [tc_id, name, suite, status.upper(),
                  f"{duration:.2f}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notes]

        for col, val in enumerate(values, 1):
            self.ws.cell(row=row, column=col, value=val)

        status_cell = self.ws.cell(row=row, column=4)
        if status.upper() == 'PASS':
            status_cell.fill = PASS_FILL
            status_cell.font = WHITE_FONT
        elif status.upper() == 'FAIL':
            status_cell.fill = FAIL_FILL
            status_cell.font = WHITE_FONT
        else:
            status_cell.fill = WARN_FILL

        self._row += 1

    def save(self, path: str):
        self.wb.save(path)
        print(f"Excel report saved: {path}")
```

---

## SECTION 16 SUMMARY

| Project | Technology | Purpose |
|---------|-----------|---------|
| EV Battery Monitor | Python + Tkinter + python-can | Live CAN dashboard |
| BMS UDS Test Suite | Python + pytest + udsoncan | Automated diagnostics testing |
| CAN Log Analyzer | Python + pandas + matplotlib | Offline log analysis + HTML report |
| CAPL BMS Simulation | CAPL + CANoe | Complete BMS restbus simulation |
| Regression Framework | Python + pytest + openpyxl | Full regression test runner |

**All projects include:**
- Professional project structure with config files
- Thread-safe architecture where concurrent I/O is used
- Error handling at system boundaries
- Configuration-driven design (YAML)
- Automated report generation

---

*Training program complete. See README.md for full section index.*
