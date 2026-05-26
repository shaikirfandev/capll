# SECTION 7 — PYTHON AUTOMOTIVE TEST AUTOMATION
## Complete Framework for EV Powertrain Testing

---

## 7.1 PYTHON FRAMEWORK OVERVIEW

### 7.1.1 Framework Architecture

```
PYTHON AUTOMOTIVE TEST FRAMEWORK ARCHITECTURE:
═════════════════════════════════════════════════════════════════════

ev_test_framework/
├── config/
│   ├── vehicle_config.yaml          ← Vehicle/ECU configuration
│   ├── test_config.yaml             ← Test parameters
│   └── can_channels.yaml            ← Hardware channel mapping
├── core/
│   ├── can_interface.py             ← python-can wrapper
│   ├── dbc_handler.py               ← cantools DBC parser
│   ├── uds_client.py                ← UDS diagnostics client
│   ├── signal_monitor.py            ← Real-time signal monitoring
│   └── test_runner.py               ← Test execution engine
├── tests/
│   ├── battery/
│   │   ├── test_bms_communication.py
│   │   ├── test_charging_sequence.py
│   │   └── test_thermal_limits.py
│   ├── inverter/
│   │   └── test_inverter_control.py
│   ├── charging/
│   │   └── test_ac_dc_charging.py
│   └── uds/
│       └── test_dtc_validation.py
├── utilities/
│   ├── logger.py                    ← Logging framework
│   ├── report_generator.py          ← HTML/Excel reports
│   ├── signal_validator.py          ← Signal range checking
│   └── can_log_analyzer.py          ← .blf/.asc file analysis
├── dashboards/
│   └── battery_monitor.py           ← Real-time tkinter dashboard
├── requirements.txt
├── conftest.py                      ← pytest fixtures
└── run_tests.py                     ← Main test executor
```

### 7.1.2 Required Packages

```python
# requirements.txt
python-can==4.3.1          # CAN bus interface
cantools==39.4.4           # DBC parsing and encoding/decoding
udsoncan==1.22.0           # UDS (ISO 14229) diagnostics
pyserial==3.5              # Serial communication
pandas==2.1.0              # Data analysis
openpyxl==3.1.2            # Excel reports
pytest==7.4.0              # Test framework
pytest-html==3.2.0         # HTML test reports
jinja2==3.1.2              # Report templating
matplotlib==3.7.2          # Signal plotting
numpy==1.24.3              # Numerical processing
pyyaml==6.0.1              # Config file parsing
rich==13.5.2               # Console output formatting
```

---

## 7.2 CAN INTERFACE MODULE

```python
# core/can_interface.py
"""
CAN Interface wrapper for python-can.
Supports Vector VN16xx, PEAK PCAN, Kvaser, and virtual interfaces.
"""

import can
import cantools
import threading
import time
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CANInterface:
    """
    Unified CAN interface supporting multiple hardware backends.
    Thread-safe message transmission and reception.
    """

    def __init__(self, channel: str, bustype: str = 'vector',
                 bitrate: int = 500000, dbc_path: Optional[str] = None,
                 fd_enabled: bool = False, data_bitrate: int = 2000000):
        """
        Initialize CAN interface.
        
        Args:
            channel:      Hardware channel (e.g., 'PCAN_USBBUS1', 'can0')
            bustype:      'vector', 'pcan', 'socketcan', 'virtual'
            bitrate:      Nominal CAN bitrate (bps)
            dbc_path:     Path to DBC file for signal decoding
            fd_enabled:   Enable CAN FD
            data_bitrate: Data phase bitrate for CAN FD
        """
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.fd_enabled = fd_enabled
        self.data_bitrate = data_bitrate
        
        self._bus = None
        self._db = None
        self._callbacks: Dict[int, list] = {}  # msg_id -> [callbacks]
        self._listener_thread = None
        self._running = False
        self._lock = threading.Lock()
        
        if dbc_path:
            self.load_dbc(dbc_path)
    
    def load_dbc(self, dbc_path: str):
        """Load DBC file for message encoding/decoding."""
        self._db = cantools.database.load_file(dbc_path)
        logger.info(f"DBC loaded: {dbc_path} ({len(self._db.messages)} messages)")
    
    def connect(self) -> bool:
        """
        Open CAN interface connection.
        Returns True on success.
        """
        try:
            kwargs = {
                'channel': self.channel,
                'bustype': self.bustype,
                'bitrate': self.bitrate,
            }
            if self.fd_enabled:
                kwargs['fd'] = True
                kwargs['data_bitrate'] = self.data_bitrate
            
            self._bus = can.interface.Bus(**kwargs)
            self._running = True
            
            # Start listener thread
            self._listener_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True,
                name=f"CAN-Listener-{self.channel}"
            )
            self._listener_thread.start()
            logger.info(f"CAN connected: {self.bustype}/{self.channel} @ {self.bitrate}bps")
            return True
            
        except Exception as e:
            logger.error(f"CAN connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close CAN interface."""
        self._running = False
        if self._bus:
            self._bus.shutdown()
        logger.info("CAN disconnected")
    
    def _receive_loop(self):
        """Background thread for receiving CAN messages."""
        while self._running:
            try:
                msg = self._bus.recv(timeout=0.1)
                if msg is not None:
                    self._dispatch_message(msg)
            except Exception as e:
                if self._running:
                    logger.error(f"CAN receive error: {e}")
    
    def _dispatch_message(self, msg: can.Message):
        """Dispatch received message to registered callbacks."""
        callbacks = self._callbacks.get(msg.arbitration_id, [])
        for callback in callbacks:
            try:
                callback(msg)
            except Exception as e:
                logger.error(f"Callback error for ID {msg.arbitration_id:#x}: {e}")
    
    def register_callback(self, msg_id: int, callback: Callable):
        """Register a callback for a specific message ID."""
        if msg_id not in self._callbacks:
            self._callbacks[msg_id] = []
        self._callbacks[msg_id].append(callback)
    
    def send_message(self, msg_id: int, data: bytes, 
                     is_extended_id: bool = False) -> bool:
        """
        Send a raw CAN message.
        
        Args:
            msg_id:           CAN message identifier
            data:             Message payload bytes
            is_extended_id:   True for 29-bit ID
        Returns:
            True if sent successfully
        """
        try:
            msg = can.Message(
                arbitration_id=msg_id,
                data=data,
                is_extended_id=is_extended_id
            )
            with self._lock:
                self._bus.send(msg)
            return True
        except Exception as e:
            logger.error(f"Send failed ID {msg_id:#x}: {e}")
            return False
    
    def send_signal(self, message_name: str, signals: dict) -> bool:
        """
        Send a CAN message with named signals using DBC encoding.
        
        Args:
            message_name: Message name as defined in DBC
            signals:      Dict of {signal_name: physical_value}
        
        Example:
            can.send_signal('VCU_Command', {
                'VCU_HV_Enable': 1,
                'VCU_DriveMode': 2
            })
        """
        if not self._db:
            raise RuntimeError("No DBC loaded. Call load_dbc() first.")
        
        try:
            msg_def = self._db.get_message_by_name(message_name)
            data = msg_def.encode(signals)
            return self.send_message(msg_def.frame_id, data)
        except Exception as e:
            logger.error(f"Signal send failed '{message_name}': {e}")
            return False
    
    def decode_message(self, msg: can.Message) -> Optional[dict]:
        """
        Decode a received CAN message using DBC.
        Returns dict of {signal_name: physical_value} or None.
        """
        if not self._db:
            return None
        try:
            msg_def = self._db.get_message_by_frame_id(msg.arbitration_id)
            return msg_def.decode(msg.data)
        except Exception:
            return None
    
    def wait_for_message(self, msg_id: int, timeout: float = 5.0) -> Optional[can.Message]:
        """
        Wait for a specific message to appear on the bus.
        Returns the message or None if timeout expires.
        """
        received = threading.Event()
        result = [None]
        
        def handler(msg):
            result[0] = msg
            received.set()
        
        self.register_callback(msg_id, handler)
        received.wait(timeout=timeout)
        self._callbacks[msg_id].remove(handler)
        
        return result[0]
    
    def wait_for_signal(self, message_name: str, signal_name: str,
                        expected_value: Any, timeout: float = 10.0,
                        tolerance: float = 0.0) -> bool:
        """
        Wait until a specific signal reaches the expected value.
        
        Args:
            message_name:   CAN message name
            signal_name:    Signal name
            expected_value: Target value
            timeout:        Maximum wait time (seconds)
            tolerance:      Acceptable deviation (for numeric values)
        Returns:
            True if value reached, False if timeout
        """
        if not self._db:
            raise RuntimeError("No DBC loaded")
        
        msg_def = self._db.get_message_by_name(message_name)
        received = threading.Event()
        
        def handler(msg):
            try:
                decoded = msg_def.decode(msg.data)
                actual = decoded.get(signal_name)
                if actual is not None:
                    if tolerance > 0:
                        if abs(actual - expected_value) <= tolerance:
                            received.set()
                    else:
                        if actual == expected_value:
                            received.set()
            except Exception:
                pass
        
        self.register_callback(msg_def.frame_id, handler)
        result = received.wait(timeout=timeout)
        self._callbacks[msg_def.frame_id].remove(handler)
        
        return result
```

---

## 7.3 DBC HANDLER MODULE

```python
# core/dbc_handler.py
"""
DBC file parser and signal encoding/decoding utilities.
"""

import cantools
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class DBCHandler:
    """
    Manages DBC database loading, signal lookup, and encoding/decoding.
    Supports multiple DBC files for multi-network vehicles.
    """

    def __init__(self):
        self._databases: Dict[str, cantools.database.Database] = {}
        self._all_messages = {}  # id -> message across all DBs

    def load_dbc(self, network_name: str, dbc_path: str):
        """Load a DBC file and associate with a network name."""
        db = cantools.database.load_file(dbc_path)
        self._databases[network_name] = db
        
        for msg in db.messages:
            self._all_messages[msg.frame_id] = msg
        
        logger.info(f"Loaded DBC '{network_name}': {dbc_path} "
                    f"({len(db.messages)} messages, "
                    f"{sum(len(m.signals) for m in db.messages)} signals)")

    def get_signal_info(self, message_name: str, signal_name: str) -> dict:
        """Get metadata about a specific signal."""
        for db in self._databases.values():
            try:
                msg = db.get_message_by_name(message_name)
                sig = msg.get_signal_by_name(signal_name)
                return {
                    'name': sig.name,
                    'start': sig.start,
                    'length': sig.length,
                    'byte_order': sig.byte_order,
                    'is_signed': sig.is_signed,
                    'scale': sig.scale,
                    'offset': sig.offset,
                    'minimum': sig.minimum,
                    'maximum': sig.maximum,
                    'unit': sig.unit,
                    'choices': sig.choices
                }
            except KeyError:
                continue
        return {}

    def encode(self, message_name: str, signals: dict) -> bytes:
        """Encode signals into CAN frame bytes."""
        for db in self._databases.values():
            try:
                msg = db.get_message_by_name(message_name)
                return msg.encode(signals)
            except KeyError:
                continue
        raise ValueError(f"Message '{message_name}' not found in any DBC")

    def decode(self, msg_id: int, data: bytes) -> Optional[dict]:
        """Decode CAN frame bytes into signal dictionary."""
        msg_def = self._all_messages.get(msg_id)
        if msg_def:
            try:
                return msg_def.decode(data)
            except Exception as e:
                logger.debug(f"Decode error ID {msg_id:#x}: {e}")
        return None

    def get_all_signals(self, message_name: str) -> List[str]:
        """List all signals in a message."""
        for db in self._databases.values():
            try:
                msg = db.get_message_by_name(message_name)
                return [sig.name for sig in msg.signals]
            except KeyError:
                continue
        return []

    def validate_signal_range(self, message_name: str, 
                               signal_name: str, value: Any) -> bool:
        """Check if a signal value is within defined min/max range."""
        info = self.get_signal_info(message_name, signal_name)
        if not info:
            return True  # Cannot validate without info
        
        min_val = info.get('minimum')
        max_val = info.get('maximum')
        
        if min_val is not None and value < min_val:
            logger.warning(f"{signal_name} = {value} < minimum {min_val}")
            return False
        if max_val is not None and value > max_val:
            logger.warning(f"{signal_name} = {value} > maximum {max_val}")
            return False
        return True
```

---

## 7.4 UDS CLIENT MODULE

```python
# core/uds_client.py
"""
UDS (ISO 14229) diagnostics client for automotive ECU testing.
"""

import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan import services
import isotp
import can
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class UDSClient:
    """
    UDS diagnostic client for EV ECU testing.
    Supports session management, DID read/write, DTC operations.
    """

    def __init__(self, can_interface: can.Bus, request_id: int, 
                 response_id: int, padding_byte: int = 0x00):
        """
        Initialize UDS client.
        
        Args:
            can_interface: python-can bus object
            request_id:    CAN ID for diagnostic requests (e.g., 0x741 for OBC)
            response_id:   CAN ID for diagnostic responses (e.g., 0x749)
            padding_byte:  ISO-TP padding byte
        """
        self.request_id = request_id
        self.response_id = response_id
        self._client = None
        
        # Setup ISO-TP transport
        self._isotp_addr = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=request_id,
            rxid=response_id
        )
        self._conn = PythonIsoTpConnection(
            bus=can_interface,
            address=self._isotp_addr,
            params={'tx_padding': padding_byte}
        )
        
        # UDS client configuration
        self._config = udsoncan.configs.default_client_config.copy()
        self._config['request_timeout'] = 2.0
        self._config['p2_timeout'] = 1.0

    def connect(self):
        """Open UDS client connection."""
        self._conn.open()
        self._client = Client(self._conn, config=self._config)
        logger.info(f"UDS connected: Req={self.request_id:#x} Resp={self.response_id:#x}")

    def disconnect(self):
        """Close UDS client."""
        if self._conn:
            self._conn.close()
        logger.info("UDS disconnected")

    def change_session(self, session: int) -> bool:
        """
        Change diagnostic session (0x10 service).
        session: 0x01=Default, 0x02=Programming, 0x03=Extended
        """
        try:
            self._client.change_session(session)
            logger.info(f"Session changed to {session:#x}")
            return True
        except Exception as e:
            logger.error(f"Session change failed: {e}")
            return False

    def ecu_reset(self, reset_type: int = 0x01) -> bool:
        """
        ECU reset (0x11 service).
        reset_type: 0x01=HardReset, 0x02=KeyOffOnReset, 0x03=SoftReset
        """
        try:
            self._client.ecu_reset(reset_type)
            logger.info(f"ECU reset sent (type={reset_type:#x})")
            return True
        except Exception as e:
            logger.error(f"ECU reset failed: {e}")
            return False

    def read_data_by_id(self, did: int) -> Optional[bytes]:
        """
        Read data by DID (0x22 service).
        Returns raw bytes or None.
        
        Example:
            vin = uds.read_data_by_id(0xF190)
        """
        try:
            response = self._client.read_data_by_identifier(did)
            data = response.service_data.values[did]
            logger.debug(f"ReadDID {did:#x}: {data.hex()}")
            return bytes(data)
        except Exception as e:
            logger.error(f"ReadDID {did:#x} failed: {e}")
            return None

    def write_data_by_id(self, did: int, data: bytes) -> bool:
        """
        Write data by DID (0x2E service).
        Returns True on success.
        """
        try:
            self._client.write_data_by_identifier(did, data)
            logger.info(f"WriteDID {did:#x}: {data.hex()}")
            return True
        except Exception as e:
            logger.error(f"WriteDID {did:#x} failed: {e}")
            return False

    def read_dtc_by_status(self, status_mask: int = 0xFF) -> List[dict]:
        """
        Read DTCs by status mask (0x19 02 service).
        Returns list of DTC dicts.
        """
        try:
            response = self._client.get_dtc_by_status_mask(status_mask)
            dtcs = []
            for entry in response.service_data.dtcs:
                dtcs.append({
                    'dtc': entry.id,
                    'dtc_hex': f"{entry.id:#08x}",
                    'status': entry.status.get_byte_value(),
                    'test_failed': entry.status.test_failed,
                    'confirmed': entry.status.confirmed_dtc,
                })
            logger.info(f"Read {len(dtcs)} DTCs")
            return dtcs
        except Exception as e:
            logger.error(f"ReadDTC failed: {e}")
            return []

    def clear_dtc(self, group: int = 0xFFFFFF) -> bool:
        """
        Clear diagnostic information (0x14 service).
        group: 0xFFFFFF = clear all DTCs
        """
        try:
            self._client.clear_dtc(group)
            logger.info("DTCs cleared")
            return True
        except Exception as e:
            logger.error(f"ClearDTC failed: {e}")
            return False

    def security_access(self, level: int, seed_to_key_func) -> bool:
        """
        Security access (0x27 service).
        
        Args:
            level:            Security level (e.g., 0x01, 0x03)
            seed_to_key_func: Function(seed_bytes) -> key_bytes
        
        Returns True if access granted.
        """
        try:
            # Step 1: Request seed
            response = self._client.request_seed(level)
            seed = response.service_data.seed
            logger.debug(f"Security seed: {seed.hex()}")
            
            # Step 2: Calculate key
            key = seed_to_key_func(seed)
            
            # Step 3: Send key
            self._client.send_key(level + 1, key)
            logger.info(f"Security access granted (level={level:#x})")
            return True
        except Exception as e:
            logger.error(f"Security access failed: {e}")
            return False

    def tester_present(self) -> bool:
        """Send Tester Present (0x3E) to keep session alive."""
        try:
            self._client.tester_present()
            return True
        except Exception as e:
            logger.error(f"Tester Present failed: {e}")
            return False
```

---

## 7.5 PYTEST TEST EXAMPLES

```python
# tests/battery/test_bms_communication.py
"""
BMS CAN Communication Validation Tests
Requirement coverage: SysRS-BMS-001 through SysRS-BMS-015
"""

import pytest
import time
from typing import Generator
from core.can_interface import CANInterface
from core.uds_client import UDSClient
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def can_bus() -> Generator[CANInterface, None, None]:
    """Setup CAN interface for all tests in this module."""
    bus = CANInterface(
        channel='PCAN_USBBUS1',
        bustype='pcan',
        bitrate=500000,
        dbc_path='config/EV_Powertrain.dbc'
    )
    assert bus.connect(), "CAN interface connection failed"
    yield bus
    bus.disconnect()

@pytest.fixture(scope='module')
def uds_bms(can_bus) -> Generator[UDSClient, None, None]:
    """Setup UDS client for BMS (request=0x741, response=0x749)."""
    client = UDSClient(
        can_interface=can_bus._bus,
        request_id=0x741,
        response_id=0x749
    )
    client.connect()
    yield client
    client.disconnect()


# ═══════════════════════════════════════════════════════════════
# TEST CASES
# ═══════════════════════════════════════════════════════════════

class TestBMSMessageTransmission:
    """Tests for BMS CAN message transmission behavior."""

    @pytest.mark.parametrize("message_name,expected_period_ms,tolerance_ms", [
        ("BMS_Status",  10,  1),    # SysRS-BMS-001
        ("BMS_Limits",  100, 5),    # SysRS-BMS-002
        ("BMS_CellData", 100, 5),   # SysRS-BMS-003
    ])
    def test_message_period(self, can_bus, message_name, 
                             expected_period_ms, tolerance_ms):
        """Verify BMS message cyclic transmission period."""
        msg_id = can_bus._db.get_message_by_name(message_name).frame_id
        timestamps = []
        
        def capture(msg):
            timestamps.append(time.monotonic())
        
        can_bus.register_callback(msg_id, capture)
        time.sleep(2.0)  # Collect for 2 seconds
        can_bus._callbacks[msg_id].remove(capture)
        
        assert len(timestamps) >= 10, \
            f"{message_name}: Not enough messages received ({len(timestamps)})"
        
        periods_ms = [
            (timestamps[i+1] - timestamps[i]) * 1000 
            for i in range(len(timestamps)-1)
        ]
        mean_period = sum(periods_ms) / len(periods_ms)
        max_period = max(periods_ms)
        
        assert abs(mean_period - expected_period_ms) <= tolerance_ms, \
            f"{message_name}: Mean period {mean_period:.2f}ms, " \
            f"expected {expected_period_ms}±{tolerance_ms}ms"
        
        assert max_period <= expected_period_ms * 5, \
            f"{message_name}: Max period spike {max_period:.2f}ms detected"

    def test_bms_soc_range(self, can_bus):
        """Verify BMS_SoC signal within valid range [0-100%]."""
        msg = can_bus.wait_for_message(
            can_bus._db.get_message_by_name('BMS_Status').frame_id,
            timeout=2.0
        )
        assert msg is not None, "BMS_Status message not received"
        
        decoded = can_bus.decode_message(msg)
        soc = decoded['BMS_SoC']
        
        assert 0.0 <= soc <= 100.0, \
            f"BMS_SoC = {soc}% — OUT OF VALID RANGE [0-100%]"

    def test_bms_pack_voltage_range(self, can_bus):
        """Verify BMS_PackVoltage within expected range [280-420V]."""
        msg = can_bus.wait_for_message(
            can_bus._db.get_message_by_name('BMS_Status').frame_id,
            timeout=2.0
        )
        decoded = can_bus.decode_message(msg)
        voltage = decoded['BMS_PackVoltage']
        
        assert 280.0 <= voltage <= 420.0, \
            f"BMS_PackVoltage = {voltage}V — OUTSIDE RANGE [280-420V]"


class TestBMSDiagnostics:
    """Tests for BMS UDS diagnostic services."""

    def test_default_session(self, uds_bms):
        """Verify BMS accepts Default Diagnostic Session."""
        result = uds_bms.change_session(0x01)
        assert result, "BMS did not accept Default Session (0x10 0x01)"

    def test_extended_session(self, uds_bms):
        """Verify BMS accepts Extended Diagnostic Session."""
        result = uds_bms.change_session(0x03)
        assert result, "BMS did not accept Extended Session (0x10 0x03)"
        uds_bms.change_session(0x01)  # Return to default

    def test_read_vin(self, uds_bms):
        """Verify BMS can provide VIN (DID 0xF190)."""
        data = uds_bms.read_data_by_id(0xF190)
        assert data is not None, "ReadDID 0xF190 (VIN) failed"
        assert len(data) == 17, f"VIN length {len(data)} != 17"
        # Check ASCII printable characters
        assert all(32 <= b <= 126 for b in data), "VIN contains non-ASCII bytes"

    def test_read_bms_software_version(self, uds_bms):
        """Verify BMS SW version DID readable."""
        data = uds_bms.read_data_by_id(0xF188)  # ECU SW version
        assert data is not None, "ReadDID 0xF188 (SW version) failed"
        assert len(data) >= 4, f"SW version too short: {len(data)} bytes"

    def test_read_dtc_empty(self, uds_bms):
        """Verify no DTCs present in clean state."""
        # Clear DTCs first
        uds_bms.clear_dtc(0xFFFFFF)
        time.sleep(0.5)
        
        # Read DTCs
        dtcs = uds_bms.read_dtc_by_status(0xFF)
        
        confirmed = [d for d in dtcs if d['confirmed']]
        assert len(confirmed) == 0, \
            f"Unexpected confirmed DTCs after clear: {confirmed}"


class TestBMSFaultHandling:
    """Tests for BMS fault detection and DTC setting."""

    @pytest.mark.parametrize("fault_name,expected_dtc", [
        ("cell_overvoltage",   0x0A0001),
        ("cell_undervoltage",  0x0A0002),
        ("overtemperature",    0x0A0003),
        ("isolation_fault",    0x0A0010),
    ])
    def test_fault_dtc_set(self, can_bus, uds_bms, fault_name, expected_dtc):
        """Verify correct DTC is set when fault condition occurs."""
        # This test requires fault injection capability
        # In real test: fault injection via CAPL simulation or hardware fault sim
        pytest.skip(f"Fault injection infrastructure required for {fault_name}")
```

---

## 7.6 BATTERY MONITORING DASHBOARD

```python
# dashboards/battery_monitor.py
"""
Real-time battery monitoring dashboard using tkinter.
Displays live BMS signals from CAN bus.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from core.can_interface import CANInterface


class BatteryDashboard:
    """Real-time battery monitoring GUI."""

    def __init__(self, can_bus: CANInterface):
        self.can_bus = can_bus
        self.root = tk.Tk()
        self.root.title("EV Battery Monitor — Live")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a2e')
        
        # Signal values
        self.soc = tk.StringVar(value="--")
        self.soh = tk.StringVar(value="--")
        self.voltage = tk.StringVar(value="--")
        self.current = tk.StringVar(value="--")
        self.max_temp = tk.StringVar(value="--")
        self.contactor = tk.StringVar(value="--")
        self.fault_code = tk.StringVar(value="0x0000")
        self.power = tk.StringVar(value="--")
        
        self._build_ui()
        self._register_callbacks()

    def _build_ui(self):
        """Build dashboard UI."""
        style = ttk.Style()
        style.configure('Card.TFrame', background='#16213e', relief='raised')
        
        # Title
        title = tk.Label(self.root, text="EV BATTERY MANAGEMENT SYSTEM",
                        font=('Helvetica', 16, 'bold'),
                        fg='#00d2ff', bg='#1a1a2e')
        title.pack(pady=10)
        
        # Main frame
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # SoC bar
        self._create_signal_card(main, "State of Charge", self.soc, "%", 0, 0, "#00d2ff")
        self._create_signal_card(main, "State of Health", self.soh, "%", 0, 1, "#00b894")
        self._create_signal_card(main, "Pack Voltage", self.voltage, "V", 1, 0, "#fdcb6e")
        self._create_signal_card(main, "Pack Current", self.current, "A", 1, 1, "#e17055")
        self._create_signal_card(main, "Max Cell Temp", self.max_temp, "°C", 2, 0, "#d63031")
        self._create_signal_card(main, "Output Power", self.power, "kW", 2, 1, "#6c5ce7")
        
        # Status bar
        status = tk.Frame(self.root, bg='#16213e')
        status.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(status, text="CONTACTOR:", fg='white', bg='#16213e').pack(side=tk.LEFT)
        tk.Label(status, textvariable=self.contactor, fg='#00d2ff', 
                bg='#16213e', font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        
        tk.Label(status, text="FAULT CODE:", fg='white', bg='#16213e').pack(side=tk.LEFT, padx=20)
        tk.Label(status, textvariable=self.fault_code, fg='#ff6b6b',
                bg='#16213e', font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)

    def _create_signal_card(self, parent, label, var, unit, row, col, color):
        """Create a signal display card."""
        frame = tk.Frame(parent, bg='#16213e', relief='raised', bd=2)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew', ipadx=15, ipady=10)
        parent.columnconfigure(col, weight=1)
        
        tk.Label(frame, text=label, fg='#aaa', bg='#16213e', 
                font=('Helvetica', 10)).pack()
        
        val_frame = tk.Frame(frame, bg='#16213e')
        val_frame.pack()
        
        tk.Label(val_frame, textvariable=var, fg=color, bg='#16213e',
                font=('Helvetica', 28, 'bold')).pack(side=tk.LEFT)
        tk.Label(val_frame, text=f" {unit}", fg='#aaa', bg='#16213e',
                font=('Helvetica', 14)).pack(side=tk.LEFT, pady=10)

    def _register_callbacks(self):
        """Register CAN callbacks to update dashboard."""
        db = self.can_bus._db
        if not db:
            return
        
        try:
            msg_id = db.get_message_by_name('BMS_Status').frame_id
            self.can_bus.register_callback(msg_id, self._on_bms_status)
        except Exception as e:
            print(f"Callback registration failed: {e}")

    def _on_bms_status(self, msg):
        """Handle BMS_Status message."""
        decoded = self.can_bus.decode_message(msg)
        if decoded:
            self.soc.set(f"{decoded.get('BMS_SoC', 0):.1f}")
            self.soh.set(f"{decoded.get('BMS_SoH', 0):.1f}")
            self.voltage.set(f"{decoded.get('BMS_PackVoltage', 0):.1f}")
            current = decoded.get('BMS_PackCurrent', 0)
            self.current.set(f"{current:.1f}")
            self.max_temp.set(f"{decoded.get('BMS_MaxCellTemp', 0):.1f}")
            power = decoded.get('BMS_PackVoltage', 0) * abs(current) / 1000.0
            self.power.set(f"{power:.1f}")
            
            contactor_map = {0: 'OPEN', 1: 'PRECHARGE', 2: 'CLOSED', 3: 'FAULT'}
            self.contactor.set(contactor_map.get(decoded.get('BMS_ContactorState', 0), '?'))
            
            fault = decoded.get('BMS_FaultCode', 0)
            self.fault_code.set(f"0x{int(fault):04X}")

    def run(self):
        """Start the dashboard."""
        self.root.mainloop()


if __name__ == '__main__':
    # Example usage
    bus = CANInterface(
        channel='virtual',
        bustype='virtual',
        bitrate=500000,
        dbc_path='config/EV_Powertrain.dbc'
    )
    bus.connect()
    
    dashboard = BatteryDashboard(bus)
    dashboard.run()
```

---

## 7.7 REPORT GENERATOR

```python
# utilities/report_generator.py
"""
HTML and Excel test report generator for automotive test results.
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class TestReportGenerator:
    """Generates professional test reports in HTML and Excel format."""

    def __init__(self, project_name: str, vehicle_id: str, sw_version: str):
        self.project_name = project_name
        self.vehicle_id = vehicle_id
        self.sw_version = sw_version
        self.test_results = []
        self.start_time = datetime.now()

    def add_result(self, test_id: str, test_name: str, 
                   verdict: str, details: str = "",
                   requirement_id: str = "", 
                   execution_time: float = 0.0):
        """Add a test result entry."""
        self.test_results.append({
            'test_id': test_id,
            'test_name': test_name,
            'verdict': verdict.upper(),
            'details': details,
            'requirement_id': requirement_id,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        })

    def generate_excel(self, output_path: str):
        """Generate Excel test report."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Results"
        
        # Colors
        green = PatternFill("solid", fgColor="00C851")
        red   = PatternFill("solid", fgColor="FF4444")
        gray  = PatternFill("solid", fgColor="AAAAAA")
        blue  = PatternFill("solid", fgColor="0070C0")
        
        # Header
        ws.merge_cells('A1:G1')
        ws['A1'] = f"TEST REPORT — {self.project_name}"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = blue
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Metadata
        meta = [
            ('Vehicle ID:', self.vehicle_id),
            ('SW Version:', self.sw_version),
            ('Test Date:', self.start_time.strftime('%Y-%m-%d %H:%M:%S')),
            ('Total Tests:', len(self.test_results)),
            ('PASS:', sum(1 for r in self.test_results if r['verdict'] == 'PASS')),
            ('FAIL:', sum(1 for r in self.test_results if r['verdict'] == 'FAIL')),
        ]
        for i, (k, v) in enumerate(meta, start=2):
            ws[f'A{i}'] = k
            ws[f'B{i}'] = str(v)
        
        # Column headers
        headers = ['Test ID', 'Test Name', 'Verdict', 
                   'Details', 'Req. ID', 'Time (s)', 'Timestamp']
        header_row = len(meta) + 3
        for col, h in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col, value=h)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = blue
            ws.column_dimensions[get_column_letter(col)].width = 20
        
        # Results
        for row_offset, result in enumerate(self.test_results, start=1):
            row = header_row + row_offset
            ws.cell(row=row, column=1, value=result['test_id'])
            ws.cell(row=row, column=2, value=result['test_name'])
            
            verdict_cell = ws.cell(row=row, column=3, value=result['verdict'])
            if result['verdict'] == 'PASS':
                verdict_cell.fill = green
            elif result['verdict'] == 'FAIL':
                verdict_cell.fill = red
            else:
                verdict_cell.fill = gray
            
            ws.cell(row=row, column=4, value=result['details'])
            ws.cell(row=row, column=5, value=result['requirement_id'])
            ws.cell(row=row, column=6, value=result['execution_time'])
            ws.cell(row=row, column=7, value=result['timestamp'])
        
        wb.save(output_path)
        logger.info(f"Excel report saved: {output_path}")

    def generate_summary(self) -> dict:
        """Return test execution summary statistics."""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['verdict'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['verdict'] == 'FAIL')
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': total - passed - failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'duration': (datetime.now() - self.start_time).total_seconds()
        }
```

---

## SECTION 7 SUMMARY

The Python Automotive Test Framework provides:

| Component | Capability |
|-----------|-----------|
| `CANInterface` | Thread-safe CAN Tx/Rx with signal decode |
| `DBCHandler` | Multi-DBC signal encode/decode/validate |
| `UDSClient` | Full ISO 14229 diagnostic operations |
| pytest tests | Parametrized, fixture-based test cases |
| BMS Dashboard | Real-time tkinter GUI monitoring |
| Report Generator | HTML + Excel test reports with color coding |

Key libraries: `python-can` (bus), `cantools` (DBC), `udsoncan` (UDS), `pytest` (test framework), `pandas`+`openpyxl` (reports)

---

*Next: Section 8 — UDS Diagnostics Complete Training*
