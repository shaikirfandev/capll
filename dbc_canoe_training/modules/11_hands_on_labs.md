# Module 11 — Hands-On Labs

> **Level**: Beginner → Advanced  
> **Duration**: ~6 hours total (all labs)  
> **Goal**: Practical exercises for creating DBC files, decoding raw frames, setting up CANoe simulation, writing CAPL, and running regression tests.

---

## Lab Prerequisites

```
Software required:
  ✓ Vector CANdb++ (standalone or via CANoe)
  ✓ Vector CANoe 10.0+ (student edition acceptable)
  ✓ Python 3.8+ with: pip install cantools python-can
  ✓ Text editor (VS Code recommended)

Files provided (in resources/ folder):
  ✓ sample_system_spec_matrix.md  — input specification
  ✓ vehicle_network.dbc           — reference DBC
  ✓ capl_validation.can           — validation scripts
  ✓ cheat_sheet.md                — quick reference
```

---

## LAB 1 — Create DBC from System Specification Matrix

**Objective**: Convert a system spec matrix to a valid DBC file manually.  
**Time**: ~90 minutes  
**Level**: Beginner

### Input: System Spec Matrix (Excerpt)

Use `resources/sample_system_spec_matrix.md` as input. For this lab, use the following 3-message subset:

| Message | ID | DLC | Cycle | Tx |
|---------|----|-----|-------|----|
| BrakePressure | 0x180 | 4 | 5ms | ABS_ECU |
| AccelPedal | 0x190 | 2 | 10ms | ECM |
| SpeedDisplay | 0x3A0 | 3 | 100ms | IPC |

| Message | Signal | Start | Len | Type | Factor | Offset | Min | Max | Unit | Receivers |
|---------|--------|-------|-----|------|--------|--------|-----|-----|------|-----------|
| BrakePressure | FrontBrake_Bar | 0 | 16 | U | 0.1 | 0 | 0 | 200 | bar | AEB_ECU,ECM |
| BrakePressure | RearBrake_Bar | 16 | 16 | U | 0.1 | 0 | 0 | 200 | bar | AEB_ECU,ECM |
| AccelPedal | AccelPos_Pct | 0 | 8 | U | 0.4 | 0 | 0 | 100 | % | AEB_ECU,IPC |
| AccelPedal | Kickdown | 8 | 1 | U | 1 | 0 | 0 | 1 | — | IPC |
| SpeedDisplay | DisplaySpeed | 0 | 12 | U | 0.1 | 0 | 0 | 409.5 | km/h | CGW |
| SpeedDisplay | SpeedUnit | 12 | 2 | U | 1 | 0 | 0 | 1 | — | CGW |
| SpeedDisplay | Speed_Valid | 14 | 1 | U | 1 | 0 | 0 | 1 | — | CGW |

### Steps

**Step 1: Set up DBC header**
```
VERSION ""

NS_ :
  NS_DESC_
  CM_
  BA_DEF_
  BA_DEF_DEF_
  BA_
  VAL_

BS_:

BU_: ABS_ECU ECM IPC AEB_ECU CGW Vector__XXX
```

**Step 2: Add messages and signals**

Convert each ID: 0x180=384, 0x190=400, 0x3A0=928

```
BO_ 384 BrakePressure: 4 ABS_ECU
 SG_ FrontBrake_Bar : 0|16@1+ (0.1,0) [0|200] "bar" AEB_ECU,ECM
 SG_ RearBrake_Bar  : 16|16@1+ (0.1,0) [0|200] "bar" AEB_ECU,ECM

BO_ 400 AccelPedal: 2 ECM
 SG_ AccelPos_Pct : 0|8@1+ (0.4,0) [0|100] "%" AEB_ECU,IPC
 SG_ Kickdown     : 8|1@1+ (1,0) [0|1] "" IPC

BO_ 928 SpeedDisplay: 3 IPC
 SG_ DisplaySpeed : 0|12@1+ (0.1,0) [0|409.5] "km/h" CGW
 SG_ SpeedUnit    : 12|2@1+ (1,0) [0|1] "" CGW
 SG_ Speed_Valid  : 14|1@1+ (1,0) [0|1] "" CGW
```

**Step 3: Add VAL_ entries**
```
VAL_ 928 SpeedDisplay SpeedUnit 0 "km/h" 1 "mph" ;
```

**Step 4: Add attributes**
```
BA_DEF_ BO_ "GenMsgCycleTime" INT 0 10000;
BA_DEF_DEF_ "GenMsgCycleTime" 0;

BA_ "GenMsgCycleTime" BO_ 384 5;
BA_ "GenMsgCycleTime" BO_ 400 10;
BA_ "GenMsgCycleTime" BO_ 928 100;
```

**Step 5: Add comments**
```
CM_ BO_ 384 "Hydraulic brake pressure — ASIL-B — 5ms";
CM_ BO_ 400 "Accelerator pedal position — ASIL-A — 10ms";
CM_ BO_ 928 "Speed display data for IPC — QM — 100ms";
```

### Verification

```python
import cantools
db = cantools.database.load_file("lab1_output.dbc")
for msg in db.messages:
    print(f"ID: 0x{msg.frame_id:X}  Name: {msg.name}  Signals: {len(msg.signals)}")
for sig in db.get_message_by_name("AccelPedal").signals:
    print(f"  {sig.name}: start={sig.start}, len={sig.length}, factor={sig.scale}")
```

**Expected output:**
```
ID: 0x180  Name: BrakePressure  Signals: 2
ID: 0x190  Name: AccelPedal     Signals: 2
ID: 0x3A0  Name: SpeedDisplay   Signals: 3
  AccelPos_Pct: start=0, len=8, factor=0.4
  Kickdown: start=8, len=1, factor=1.0
```

---

## LAB 2 — Decode Raw CAN Frames

**Objective**: Decode raw CAN data frames using the vehicle_network.dbc.  
**Time**: ~45 minutes  
**Level**: Beginner

### Exercise 2A: Manual Decoding

Given frame: `ID=0x244 DLC=8 Data: 01 1E 00 10 00 05 FF 00`

Refer to module 04 AEB_Req signal layout:
```
Data bytes (hex → binary):
Byte 0: 0x01 = 0000_0001
Byte 1: 0x1E = 0001_1110
Byte 2: 0x00 = 0000_0000
Byte 3: 0x10 = 0001_0000
Byte 4: 0x00 = 0000_0000
Byte 5: 0x05 = 0000_0101
Byte 6: 0xFF = 1111_1111
Byte 7: 0x00 = 0000_0000

Decode each signal:
AEB_Active    (bit 0,  len=1) = byte0 bit0 = 1      → physical = 1 × 1 + 0 = 1 (ACTIVE)
AEB_State     (bit 1,  len=3) = byte0 bits 1-3 = 0b000 = 0 → OFF? 
  Wait: byte0=0x01=0b00000001, bits 1-3 = 000 = 0 → AEB_State = 0 (OFF)
AEB_Decel_Req (bit 4,  len=8) = byte0 bits 4-7 (0b0000) + byte1 bits 0-3 (0b1110) = 0b0001_1110 = 30
  Physical = 30 × 0.1 = 3.0 m/s²
AEB_Obj_Distance (bit 12, len=16) = byte1 bits 4-7 (0b0001) + byte2 (0b0000_0000) + byte3 bits 0-3 (0b0000)
  = 0x0010 = 16 → Physical = 16 × 0.01 = 0.16 m  ← very close!
AEB_TTC       (bit 28, len=8) = byte3 bits 4-7 (0b0001) + byte4 bits 0-3 (0b0000) = 0x00... 
  Need bits 28-35: bit28=bit4 of byte3, ..., bit35=bit3 of byte4
  byte3=0x10=0b0001_0000: bits28-31 = bits4-7 = 0001
  byte4=0x00=0b0000_0000: bits32-35 = bits0-3 = 0000
  Raw = 0b0000_0001 = wait, Intel: start=28 means bit28 is LSB
  Raw bits28-35 = byte3[4..7] byte4[0..3] → raw = 0b(byte3>>4 | byte4<<4 in context)
  Simpler: raw bytes 28-35 bit range in data = 0x00 → TTC = 0 × 0.01 = 0.00 s
Alive_Ctr_AEB (bit 36, len=4) = nibble at bits 36-39 = byte4 bits4-7 = 0x00 >> 4 = 0
CRC_AEB       (bit 40, len=8) = byte5 = 0x05
```

### Exercise 2B: Python Decoding

```python
import cantools

db = cantools.database.load_file("resources/vehicle_network.dbc")
msg = db.get_message_by_name("AEB_Req")

# Raw CAN frame bytes
raw_data = bytes([0x01, 0x1E, 0x00, 0x10, 0x00, 0x05, 0xFF, 0x00])

decoded = msg.decode(raw_data)
print("Decoded signals:")
for name, value in decoded.items():
    print(f"  {name:25s} = {value}")
```

**Expected output (approximate):**
```
  AEB_Active              = 1
  AEB_State               = 0
  AEB_Decel_Req           = 3.0
  AEB_Obj_Distance        = 0.16
  AEB_TTC                 = 0.0
  Alive_Ctr_AEB           = 0
  CRC_AEB                 = 5
  Reserved_AEB            = 255
```

### Exercise 2C: Encode a Physical Value to Raw

```python
# Encode: AEB_Decel_Req = 7.5 m/s²
msg = db.get_message_by_name("AEB_Req")
data = msg.encode({
    'AEB_Active':       1,
    'AEB_State':        3,     # ACTIVE
    'AEB_Decel_Req':    7.5,
    'AEB_Obj_Distance': 25.0,
    'AEB_TTC':          1.5,
    'Alive_Ctr_AEB':    5,
    'CRC_AEB':          0,     # would be calculated by E2E
    'Reserved_AEB':     0
})
print("Encoded bytes:", data.hex())
```

---

## LAB 3 — CANoe Simulation Setup

**Objective**: Configure CANoe to simulate the ADAS Safety Bus.  
**Time**: ~60 minutes  
**Level**: Intermediate

### Step-by-Step Setup

```
1. Open CANoe → File → New → CAN
   - Select "Empty configuration"
   - File → Save As: ADAS_Simulation.cfg

2. Add hardware:
   - File → Hardware → Virtual CAN Channel 1
   - Bitrate: 500000
   - OK

3. Add database:
   - Measurement Setup window → right-click CAN Network → Properties
   - Databases → Add → select resources/vehicle_network.dbc
   - OK

4. Add IL node:
   - Measurement Setup → Add Node → "CANoe node"
   - Type: IL (Interaction Layer)
   - Name: Vehicle_IL
   - Database: vehicle_network.dbc
   - Bus: CAN 1

5. Add CAPL simulation node:
   - Add Node → CAPL
   - Name: AEB_Simulation
   - CAPL file: create new → AEB_Sim.can (see Lab 4)
   - Bus: CAN 1

6. Open Analysis windows:
   - View → Trace (enable Symbolic mode)
   - View → Graphics → add AEB_Decel_Req, AEB_Obj_Distance, WheelSpeed_FL
   - View → Statistics

7. Start measurement:
   - Press F9 (or green Play button)
   - Verify Trace window shows decoded messages
   - Verify Graphics shows signal waveforms

8. Check Statistics:
   - Bus Load should be ~6-7%
   - Error count should be 0
```

---

## LAB 4 — CAPL Signal Validation Script

**Objective**: Write and run a CAPL test module for signal validation.  
**Time**: ~60 minutes  
**Level**: Intermediate

### Lab 4A: Basic Signal Monitoring

Create file `lab4_monitor.can`:

```capl
variables {
  msTimer cycleWatchdog;
  int     wdResets = 0;
}

on start {
  write("=== ADAS Signal Monitor Started ===");
  setTimer(cycleWatchdog, 100);  // Watchdog: check every 100ms
}

on message WheelSpeed {
  float fl = this.WheelSpeed_FL * 0.01;
  float fr = this.WheelSpeed_FR * 0.01;
  
  if(fl < 0 || fl > 300)
    write("RANGE VIOLATION: WheelSpeed_FL = %.2f km/h", fl);
    
  if(fr < 0 || fr > 300)
    write("RANGE VIOLATION: WheelSpeed_FR = %.2f km/h", fr);
}

on message AEB_Req {
  float decel = this.AEB_Decel_Req * 0.1;
  int   state = this.AEB_State;
  
  if(this.AEB_Active == 1 && decel == 0.0)
    write("WARNING: AEB_Active=1 but Decel=0 — inconsistency");
    
  if(state > 6)
    write("INVALID: AEB_State = %d (max valid = 6)", state);
}

on timer cycleWatchdog {
  write("[%f] Watchdog OK — measurement running", timeNow()/100000.0);
  setTimer(cycleWatchdog, 5000);  // Recheck every 5 seconds
}
```

### Lab 4B: Full Regression Test Suite

Create file `lab4_regression.can`:

```capl
/*
 * ADAS DBC Regression Test Suite
 * Runs automatically on measurement start
 */

variables {
  int allMsgsReceived = 0;
  byte msgFlags = 0;  // Bitfield: bit0=WheelSpeed, bit1=AEB_Req, bit2=VehicleStatus
  
  msTimer startupWait;
  int testsFailed = 0;
  int testsPassed = 0;
}

void logPass(char testName[]) {
  testStepPass(testName, "PASS");
  testsPassed++;
  write("[PASS] %s", testName);
}

void logFail(char testName[], char reason[]) {
  testStepFail(testName, reason);
  testsFailed++;
  write("[FAIL] %s: %s", testName, reason);
}

on start {
  setTimer(startupWait, 3000);  // Wait 3s for messages to arrive
}

on message WheelSpeed   { msgFlags = msgFlags | 0x01; }
on message AEB_Req      { msgFlags = msgFlags | 0x02; }
on message VehicleStatus { msgFlags = msgFlags | 0x04; }
on message EPS_Status   { msgFlags = msgFlags | 0x08; }
on message IPC_Display  { msgFlags = msgFlags | 0x10; }
on message BCM_Status   { msgFlags = msgFlags | 0x20; }

on timer startupWait {
  /* Check all messages received */
  if(msgFlags & 0x01) logPass("WheelSpeed_Present");
  else logFail("WheelSpeed_Present", "Message 0x200 not received in 3 seconds");
  
  if(msgFlags & 0x02) logPass("AEB_Req_Present");
  else logFail("AEB_Req_Present", "Message 0x244 not received in 3 seconds");
  
  if(msgFlags & 0x04) logPass("VehicleStatus_Present");
  else logFail("VehicleStatus_Present", "Message 0x300 not received");
  
  if(msgFlags & 0x08) logPass("EPS_Status_Present");
  else logFail("EPS_Status_Present", "Message 0x380 not received");
  
  if(msgFlags & 0x10) logPass("IPC_Display_Present");
  else logFail("IPC_Display_Present", "Message 0x350 not received");
  
  if(msgFlags & 0x20) logPass("BCM_Status_Present");
  else logFail("BCM_Status_Present", "Message 0x420 not received");
}

on stopMeasurement {
  write("===========================");
  write("REGRESSION SUITE COMPLETE");
  write("  Passed: %d", testsPassed);
  write("  Failed: %d", testsFailed);
  write("===========================");
}
```

---

## LAB 5 — Multiplexed Message Implementation

**Objective**: Create a multiplexed DBC message and verify decoding.  
**Time**: ~45 minutes  
**Level**: Advanced

### Scenario

Create a diagnostic status message that carries different sensor data based on a MUX selector:
- Mux 0: Radar sensor data (distance, speed, angle)
- Mux 1: Camera data (lane offset, width)
- Mux 2: Fusion output (object class, confidence)

### DBC Creation

```
BO_ 1024 ADAS_SensorMux: 8 AEB_ECU
 SG_ SensorMux     M : 0|4@1+  (1,0) [0|2]     ""    CGW
 SG_ Sensor_Status   : 4|4@1+  (1,0) [0|15]    ""    CGW
 
 SG_ Radar_Dist    m0 : 8|16@1+ (0.01,0)  [0|655.35] "m"   CGW
 SG_ Radar_Speed   m0 : 24|12@1- (0.1,0)  [-204.8|204.7] "m/s" CGW
 SG_ Radar_Angle   m0 : 36|10@1- (0.1,0)  [-51.2|51.1] "deg" CGW
 
 SG_ Cam_LaneOffset m1 : 8|12@1- (0.01,0) [-20.48|20.47] "m" CGW
 SG_ Cam_LaneWidth  m1 : 20|10@1+ (0.01,0) [0|10.23] "m" CGW
 
 SG_ Fusion_Class   m2 : 8|4@1+  (1,0) [0|7] "" CGW
 SG_ Fusion_Conf    m2 : 12|7@1+ (1,0) [0|100] "%" CGW

VAL_ 1024 ADAS_SensorMux SensorMux  0 "RADAR" 1 "CAMERA" 2 "FUSION" 3 "NOT_AVAIL" ;
VAL_ 1024 ADAS_SensorMux Fusion_Class 0 "UNKNOWN" 1 "CAR" 2 "TRUCK" 3 "PEDESTRIAN" 4 "CYCLIST" ;
```

### Python Verification

```python
import cantools

db = cantools.database.load_file("lab5_mux.dbc")
msg = db.get_message_by_name("ADAS_SensorMux")

# Decode Mux=0 (Radar) frame
radar_data = bytes([0x00, 0x27, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00])
print("Radar decode:", msg.decode(radar_data, decode_choices=True))

# Decode Mux=1 (Camera) frame
cam_data    = bytes([0x01, 0x00, 0x80, 0x10, 0x00, 0x00, 0x00, 0x00])
print("Camera decode:", msg.decode(cam_data, decode_choices=True))
```

---

## LAB 6 — Full Regression Test Suite

**Objective**: Build and run a complete DBC regression test comparing two DBC versions.  
**Time**: ~60 minutes  
**Level**: Advanced

### Scenario

DBC was updated from v1.0 to v1.1. Run regression to find changes.

### Regression Script

```python
#!/usr/bin/env python3
"""
DBC Regression Comparison Tool
Usage: python3 lab6_regression.py v1.0.dbc v1.1.dbc
"""

import cantools
import sys

def compare_dbc(old_file, new_file):
    old = cantools.database.load_file(old_file)
    new = cantools.database.load_file(new_file)
    
    old_msgs = {m.name: m for m in old.messages}
    new_msgs = {m.name: m for m in new.messages}
    
    regressions = []
    additions = []
    removals = []
    
    # Check removed messages
    for name in old_msgs:
        if name not in new_msgs:
            removals.append(f"REMOVED MESSAGE: {name} (ID=0x{old_msgs[name].frame_id:X})")
    
    # Check added messages
    for name in new_msgs:
        if name not in old_msgs:
            additions.append(f"NEW MESSAGE: {name} (ID=0x{new_msgs[name].frame_id:X})")
    
    # Check modified messages
    for name in old_msgs:
        if name not in new_msgs:
            continue
        old_msg = old_msgs[name]
        new_msg = new_msgs[name]
        
        if old_msg.frame_id != new_msg.frame_id:
            regressions.append(f"ID CHANGE {name}: 0x{old_msg.frame_id:X} → 0x{new_msg.frame_id:X}")
        if old_msg.length != new_msg.length:
            regressions.append(f"DLC CHANGE {name}: {old_msg.length} → {new_msg.length}")
        
        old_sigs = {s.name: s for s in old_msg.signals}
        new_sigs = {s.name: s for s in new_msg.signals}
        
        for sig_name in old_sigs:
            if sig_name not in new_sigs:
                regressions.append(f"REMOVED SIGNAL {name}.{sig_name}")
            else:
                o, n = old_sigs[sig_name], new_sigs[sig_name]
                if o.start != n.start:
                    regressions.append(f"STARTBIT {name}.{sig_name}: {o.start} → {n.start}")
                if o.length != n.length:
                    regressions.append(f"LENGTH {name}.{sig_name}: {o.length} → {n.length}")
                if abs(o.scale - n.scale) > 1e-9:
                    regressions.append(f"FACTOR {name}.{sig_name}: {o.scale} → {n.scale}")
                if abs(o.offset - n.offset) > 1e-9:
                    regressions.append(f"OFFSET {name}.{sig_name}: {o.offset} → {n.offset}")
    
    print(f"\nDBC REGRESSION REPORT: {old_file} vs {new_file}")
    print("=" * 60)
    
    if regressions:
        print(f"\n❌ REGRESSIONS ({len(regressions)}):")
        for r in regressions:
            print(f"  {r}")
    else:
        print("\n✅ No regressions found")
    
    if removals:
        print(f"\n⚠  REMOVED ({len(removals)}):")
        for r in removals: print(f"  {r}")
    
    if additions:
        print(f"\n✅ ADDED ({len(additions)}):")
        for a in additions: print(f"  {a}")
    
    return len(regressions) == 0

if __name__ == "__main__":
    ok = compare_dbc(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
```

---

## Lab Summary and Checklist

```
□ Lab 1: Created 3-message DBC from spec matrix ✓
□ Lab 2: Decoded raw AEB frame manually and with Python ✓
□ Lab 3: Configured CANoe with DBC, IL, and CAPL node ✓
□ Lab 4: Wrote CAPL range + cycle time + regression tests ✓
□ Lab 5: Created multiplexed DBC message for sensor data ✓
□ Lab 6: Built Python DBC regression comparison tool ✓
```
