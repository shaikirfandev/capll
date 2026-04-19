# Python Automotive Testing Interview Q&A — 50 Questions
## python-can | cantools | udsoncan | isotp | pytest | CI/CD

---

## Section 1: python-can Fundamentals

**Q1: How do you open a CAN bus and send a message in python-can?**
```python
import can
bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
msg = can.Message(arbitration_id=0x123, data=[0x01, 0x02, 0x03], is_extended_id=False)
bus.send(msg)
bus.shutdown()
```

**Q2: How do you receive messages with a listener pattern?**
```python
import can

class MyListener(can.Listener):
    def on_message_received(self, msg):
        print(f"ID=0x{msg.arbitration_id:03X} data={msg.data.hex()}")

bus = can.Bus(channel='virtual', bustype='virtual')
notifier = can.Notifier(bus, [MyListener()])
# Messages delivered asynchronously to on_message_received
```

**Q3: What is the virtual bus in python-can and when do you use it?**
> `bustype='virtual'` creates an in-process virtual CAN bus — no hardware needed. Useful for unit testing without physical CAN hardware. Two Bus instances with the same channel on virtual bus exchange messages between each other.

**Q4: How do you use a filter in python-can?**
```python
bus.set_filters([
    {"can_id": 0x100, "can_mask": 0x7FF, "extended": False},  # Exact match
    {"can_id": 0x200, "can_mask": 0x700, "extended": False},  # Range 0x200–0x2FF
])
```

**Q5: How do you log CAN traffic to an ASC file?**
```python
import can
bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
logger = can.Logger('trace.asc')
notifier = can.Notifier(bus, [logger])
# ... record traffic ...
notifier.stop()
bus.shutdown()
```

---

## Section 2: cantools — DBC Signal Decoding

**Q6: How do you decode a CAN message using a DBC file?**
```python
import cantools, can

db = cantools.database.load_file('engine.dbc')
bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)

msg = bus.recv()
decoded = db.decode_message(msg.arbitration_id, msg.data)
print(decoded)  # {'EngineSpeed': 1500.0, 'EngineTemp': 90.0}
```

**Q7: How do you encode and send a DBC-defined message?**
```python
db = cantools.database.load_file('engine.dbc')
msg_def = db.get_message_by_name('EngineCommand')

data = msg_def.encode({'TargetSpeed': 2000.0, 'TorqueLimit': 80.0})
can_msg = can.Message(arbitration_id=msg_def.frame_id, data=data)
bus.send(can_msg)
```

**Q8: How do you read signal min/max limits from a DBC?**
```python
msg = db.get_message_by_name('EngineStatus')
for signal in msg.signals:
    print(f"{signal.name}: min={signal.minimum}, max={signal.maximum}, unit={signal.unit}")
```

---

## Section 3: UDS Diagnostics (udsoncan / isotp)

**Q9: How do you send a UDS ReadDataByIdentifier request?**
```python
import isotp, udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import udsoncan.configs

tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits,
                         rxid=0x7E8, txid=0x7E0)
stack = isotp.CanStack(bus, address=tp_addr)
conn = PythonIsoTpConnection(stack)

with Client(conn, request_timeout=2) as client:
    response = client.read_data_by_identifier(udsoncan.DataIdentifier(0xF190))
    print(response.service_data.values[0xF190])  # VIN
```

**Q10: How do you perform Security Access with udsoncan?**
```python
def my_key_function(level, seed, params):
    # Custom seed-key algorithm
    return bytes([s ^ 0xFF for s in seed])

with Client(conn, request_timeout=2) as client:
    client.unlock_security_access(0x01)  # Level 1 — calls key function internally
```

**Q11: What is ISO-TP (ISO 15765-2) and why is it needed?**
> CAN frames carry max 8 bytes. UDS messages can be much longer (VIN=17 bytes, ECU software data=thousands of bytes). ISO-TP provides segmentation and reassembly: Single Frame (SF), First Frame (FF), Consecutive Frames (CF), and Flow Control (FC). The `isotp` Python library handles this transparently.

---

## Section 4: pytest for Automotive Testing

**Q12: How do you structure automotive tests with pytest?**
```python
# test_engine_speed.py
import pytest, can, cantools

@pytest.fixture(scope='session')
def can_bus():
    bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
    yield bus
    bus.shutdown()

@pytest.fixture(scope='session')
def db():
    return cantools.database.load_file('engine.dbc')

def test_engine_speed_in_range(can_bus, db):
    msg = can_bus.recv(timeout=1.0)
    decoded = db.decode_message(msg.arbitration_id, msg.data)
    assert 'EngineSpeed' in decoded
    assert 600 <= decoded['EngineSpeed'] <= 1000
```

**Q13: How do you parametrize a test across multiple speed setpoints?**
```python
@pytest.mark.parametrize("setpoint,expected_min,expected_max", [
    (1000, 950, 1050),
    (2000, 1900, 2100),
    (3000, 2850, 3150),
])
def test_speed_tracking(can_bus, db, setpoint, expected_min, expected_max):
    # Send setpoint via CAN
    # Read back actual speed and verify in range
    pass
```

**Q14: How do you skip a test if hardware is not available?**
```python
import can, pytest

def is_can_available():
    try:
        bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
        bus.shutdown()
        return True
    except:
        return False

@pytest.mark.skipif(not is_can_available(), reason="CAN hardware not found")
def test_live_engine_speed(can_bus):
    pass
```

---

## Section 5: Signal Validation Patterns

**Q15: How do you validate a signal over time (not just one snapshot)?**
```python
import time, can, cantools

def read_signal_for_duration(bus, db, msg_name, signal_name, duration_s):
    values = []
    deadline = time.time() + duration_s
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg:
            try:
                decoded = db.decode_message(msg.arbitration_id, msg.data)
                if signal_name in decoded:
                    values.append(decoded[signal_name])
            except:
                pass
    return values

values = read_signal_for_duration(bus, db, 'EngineStatus', 'EngineSpeed', 5.0)
assert len(values) > 0, "No messages received"
assert all(600 <= v <= 1000 for v in values), f"Out-of-range values: {values}"
```

**Q16: How do you detect a message cycle time violation?**
```python
def check_cycle_time(bus, arb_id, expected_ms, tolerance_pct=10, count=20):
    timestamps = []
    while len(timestamps) < count:
        msg = bus.recv(timeout=1.0)
        if msg and msg.arbitration_id == arb_id:
            timestamps.append(msg.timestamp)
    
    intervals = [(timestamps[i+1] - timestamps[i]) * 1000 
                 for i in range(len(timestamps)-1)]
    tolerance = expected_ms * tolerance_pct / 100
    violations = [t for t in intervals 
                  if abs(t - expected_ms) > tolerance]
    return violations  # Empty list = pass
```

---

## Section 6: General Interview Questions

**Q17: What is the GIL and how does it affect CAN receive threading?**
> Python's Global Interpreter Lock (GIL) means only one thread runs Python bytecode at a time. For CAN receive, use `can.Notifier` (launches a background thread with callbacks) or asyncio-based approaches. For CPU-intensive processing, use `multiprocessing` to bypass the GIL.

**Q18: How do you handle bitrate mismatch detection in python-can?**
> python-can doesn't auto-detect bitrate. If bitrate is wrong, `bus.recv()` may never return or return garbage. Validate with a known working message first, or use a CAN analyzer to verify bus activity before starting tests.

**Q19: How do you generate a test report from pytest results?**
```bash
pytest --html=report.html --self-contained-html
pytest --junitxml=junit_results.xml   # For Jenkins/CI
```

**Q20: What is Vector's CANoe Python API and how does it differ from python-can?**
> CANoe's Python API (via COM interface or CANoe Python) runs within CANoe's environment — full access to CANoe's database, panels, and measurement setup. python-can is a standalone library working directly with hardware. CANoe Python is better for integrated testing; python-can is better for CI pipelines without a CANoe license on every machine.
