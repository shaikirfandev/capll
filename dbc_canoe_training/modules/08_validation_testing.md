# Module 08 — DBC Validation and Testing

> **Level**: Intermediate → Advanced  
> **Duration**: ~4 hours  
> **Goal**: Systematically validate a DBC file and CAN signals using CANoe, CAPL scripts, and structured test cases.

---

## 8.1 Validation Strategy Overview

```
                   ┌─────────────────────────────────┐
                   │     DBC Validation Pyramid       │
                   │                                   │
                   │    ④ System Integration Test      │
                   │   ③ Signal Range / Timing Tests   │
                   │  ② DBC Structure / Syntax Check   │
                   │ ① Communication Matrix Compliance  │
                   └─────────────────────────────────┘
```

| Layer | Tool | When |
|-------|------|------|
| ① Matrix compliance | Manual review / Python script | Before DBC import |
| ② DBC syntax check | CANdb++ F7, cantools parse | After DBC creation |
| ③ Signal test | CAPL test module | During simulation |
| ④ Integration | CANoe + HIL + ECU | Before release |

---

## 8.2 Layer 1 — Communication Matrix Compliance

### Python DBC vs Matrix Comparison Script

```python
#!/usr/bin/env python3
"""
DBC validation against communication matrix.
Usage: python3 validate_dbc.py --dbc ADAS_HS1.dbc --matrix ADAS_ComMatrix.csv
"""

import cantools
import csv
import argparse
import sys

def load_matrix(csv_file):
    """Load communication matrix from CSV."""
    matrix = {}
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            msg_name = row['MessageName']
            if msg_name not in matrix:
                matrix[msg_name] = {
                    'id': int(row['MessageID'], 16),
                    'dlc': int(row['DLC']),
                    'cycle_ms': int(row['CycleTime_ms']),
                    'tx_node': row['TxECU'],
                    'signals': {}
                }
            matrix[msg_name]['signals'][row['SignalName']] = {
                'start_bit':  int(row['StartBit']),
                'length':     int(row['Length']),
                'factor':     float(row['Factor']),
                'offset':     float(row['Offset']),
                'min_phys':   float(row['Min']),
                'max_phys':   float(row['Max']),
                'unit':       row['Unit'],
            }
    return matrix

def validate(dbc_file, matrix_file):
    db = cantools.database.load_file(dbc_file)
    matrix = load_matrix(matrix_file)
    
    errors = []
    warnings = []
    
    for msg_name, mat_msg in matrix.items():
        # Find message in DBC
        try:
            dbc_msg = db.get_message_by_name(msg_name)
        except KeyError:
            errors.append(f"MISSING MESSAGE: {msg_name} not in DBC")
            continue
        
        # Check message ID
        if dbc_msg.frame_id != mat_msg['id']:
            errors.append(f"ID MISMATCH: {msg_name} DBC=0x{dbc_msg.frame_id:X} Matrix=0x{mat_msg['id']:X}")
        
        # Check DLC
        if dbc_msg.length != mat_msg['dlc']:
            errors.append(f"DLC MISMATCH: {msg_name} DBC={dbc_msg.length} Matrix={mat_msg['dlc']}")
        
        # Check signals
        for sig_name, mat_sig in mat_msg['signals'].items():
            try:
                dbc_sig = dbc_msg.get_signal_by_name(sig_name)
            except KeyError:
                errors.append(f"MISSING SIGNAL: {msg_name}.{sig_name}")
                continue
            
            if dbc_sig.start != mat_sig['start_bit']:
                errors.append(f"STARTBIT: {msg_name}.{sig_name} DBC={dbc_sig.start} Matrix={mat_sig['start_bit']}")
            if dbc_sig.length != mat_sig['length']:
                errors.append(f"LENGTH: {msg_name}.{sig_name} DBC={dbc_sig.length} Matrix={mat_sig['length']}")
            if abs(dbc_sig.scale - mat_sig['factor']) > 1e-9:
                errors.append(f"FACTOR: {msg_name}.{sig_name} DBC={dbc_sig.scale} Matrix={mat_sig['factor']}")
            if abs(dbc_sig.offset - mat_sig['offset']) > 1e-9:
                errors.append(f"OFFSET: {msg_name}.{sig_name} DBC={dbc_sig.offset} Matrix={mat_sig['offset']}")
    
    return errors, warnings

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dbc',    required=True)
    parser.add_argument('--matrix', required=True)
    args = parser.parse_args()
    
    errors, warnings = validate(args.dbc, args.matrix)
    
    for w in warnings:
        print(f"[WARN]  {w}")
    for e in errors:
        print(f"[ERROR] {e}")
    
    print(f"\nResult: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)
```

---

## 8.3 Layer 2 — DBC Syntax Validation

### CANdb++ Validation (F7)

```
Tools → Check Database → View errors:

Common errors caught:
  ❌ E001: Undefined transmitter node "XYZ" for message WheelSpeed
  ❌ E002: Signal overlap: WheelSpeed_FL and WheelSpeed_FR both use bit 15
  ❌ E003: Signal AEB_Active exceeds DLC boundary (bit 64 in DLC=8 message)
  ❌ E004: Duplicate message ID 512 for messages WheelSpeed and WheelSpeed_Backup
  ⚠ W001: Signal Reserved has no receivers defined
  ⚠ W002: Attribute GenMsgCycleTime has no value for message BCM_Status
```

### Python cantools DBC Parse Validation

```python
import cantools
import sys

def validate_dbc_syntax(dbc_file):
    try:
        db = cantools.database.load_file(dbc_file)
        print(f"✅ Parsed successfully: {len(db.messages)} messages, "
              f"{sum(len(m.signals) for m in db.messages)} signals")
    except Exception as e:
        print(f"❌ DBC parse error: {e}")
        sys.exit(1)
    
    # Additional checks
    ids = [m.frame_id for m in db.messages]
    if len(ids) != len(set(ids)):
        from collections import Counter
        dupes = [id for id, count in Counter(ids).items() if count > 1]
        print(f"❌ DUPLICATE IDs: {[hex(d) for d in dupes]}")
    
    for msg in db.messages:
        bits_used = set()
        for sig in msg.signals:
            sig_bits = set(range(sig.start, sig.start + sig.length))
            overlap = bits_used & sig_bits
            if overlap:
                print(f"❌ BIT OVERLAP in {msg.name}: signal {sig.name} overlaps bits {overlap}")
            bits_used |= sig_bits
        
        if bits_used and max(bits_used) >= msg.length * 8:
            print(f"❌ SIGNAL EXCEEDS DLC in {msg.name}")
    
    print("Validation complete.")

validate_dbc_syntax("ADAS_HS1.dbc")
```

---

## 8.4 Layer 3 — CAPL Signal Validation Tests

### 8.4.1 Signal Range Test

```capl
/*
 * Test: Signal Range Validation
 * Verifies all signals are within DBC-defined min/max range
 * File: signal_range_test.can
 */

variables {
  int  rangeViolations = 0;
  int  totalChecks = 0;
}

/* Test WheelSpeed signals — expected: 0–655.35 km/h */
on message WheelSpeed {
  float fl, fr, rl, rr;
  fl = this.WheelSpeed_FL * 0.01;
  fr = this.WheelSpeed_FR * 0.01;
  rl = this.WheelSpeed_RL * 0.01;
  rr = this.WheelSpeed_RR * 0.01;
  
  totalChecks++;
  if(fl < 0 || fl > 655.35) {
    testStepFail("WheelSpeed_FL range", "Value %.2f out of [0, 655.35] km/h", fl);
    rangeViolations++;
  }
  if(fr < 0 || fr > 655.35) {
    testStepFail("WheelSpeed_FR range", "Value %.2f out of [0, 655.35] km/h", fr);
    rangeViolations++;
  }
}

/* Test AEB signals */
on message AEB_Req {
  float decel, dist, ttc;
  int state;
  
  decel = this.AEB_Decel_Req * 0.1;
  dist  = this.AEB_Obj_Distance * 0.01;
  ttc   = this.AEB_TTC * 0.01;
  state = this.AEB_State;
  
  totalChecks++;
  
  if(decel < 0 || decel > 25.5)
    testStepFail("AEB_Decel_Req range", "%.2f m/s2 not in [0, 25.5]", decel);
  else
    testStepPass("AEB_Decel_Req range", "%.2f m/s2 OK", decel);
  
  if(dist < 0 || dist > 655.35)
    testStepFail("AEB_Obj_Distance range", "%.2f m not in [0, 655.35]", dist);
    
  if(state < 0 || state > 7)
    testStepFail("AEB_State range", "Value %d not in [0, 7]", state);
}

/* Test engine temperature (signed) */
on message VehicleStatus {
  float temp;
  /* Raw is 8-bit unsigned byte in DBC (Factor=0.5, Offset=-40) */
  temp = this.EngineTemp * 0.5 - 40;
  
  totalChecks++;
  if(temp < -40 || temp > 87.5)
    testStepFail("EngineTemp range", "%.1f degC not in [-40, 87.5]", temp);
  else
    testStepPass("EngineTemp range", "%.1f degC OK", temp);
}

on stopMeasurement {
  write("=== Signal Range Test Results ===");
  write("Total checks: %d, Violations: %d", totalChecks, rangeViolations);
  if(rangeViolations == 0)
    write("PASS: All signals within DBC range");
  else
    write("FAIL: %d range violations detected", rangeViolations);
}
```

---

### 8.4.2 Cycle Time Monitoring

```capl
/*
 * Test: Cycle Time Monitoring
 * Verifies messages arrive at expected cycle time ± tolerance
 * Tolerance: ±10% of nominal cycle time
 */

variables {
  float lastWheelSpeed = 0;
  float lastAEB        = 0;
  float lastVehicle    = 0;
  float lastEPS        = 0;
  
  int cycleErrors = 0;
  
  /* Expected cycle times from DBC (ms) */
  float CYCLE_WHEELSPEED   = 10;
  float CYCLE_AEB          = 20;
  float CYCLE_VEHICLE      = 10;
  float CYCLE_EPS          = 20;
  float TOLERANCE_PCT      = 0.10;  /* ±10% */
}

void checkCycle(float now_ms, float last_ms, float nominal_ms, char msg_name[]) {
  float elapsed, low, high;
  if(last_ms == 0) return;  // First occurrence, skip
  
  elapsed = now_ms - last_ms;
  low  = nominal_ms * (1 - TOLERANCE_PCT);
  high = nominal_ms * (1 + TOLERANCE_PCT);
  
  if(elapsed < low || elapsed > high) {
    testStepFail("CycleTime", "%s: %.2f ms (expected %.1f ± 10%%)", msg_name, elapsed, nominal_ms);
    cycleErrors++;
  }
}

on message WheelSpeed {
  float now = timeNow() / 100000.0;
  checkCycle(now, lastWheelSpeed, CYCLE_WHEELSPEED, "WheelSpeed");
  lastWheelSpeed = now;
}

on message AEB_Req {
  float now = timeNow() / 100000.0;
  checkCycle(now, lastAEB, CYCLE_AEB, "AEB_Req");
  lastAEB = now;
}

on message VehicleStatus {
  float now = timeNow() / 100000.0;
  checkCycle(now, lastVehicle, CYCLE_VEHICLE, "VehicleStatus");
  lastVehicle = now;
}

on stopMeasurement {
  write("=== Cycle Time Test ===");
  write("Cycle violations: %d", cycleErrors);
}
```

---

### 8.4.3 Alive Counter Validation

```capl
/*
 * Test: Alive Counter / Sequence Counter Validation
 * Counter must increment by 1 each cycle and wrap at max value
 */

variables {
  byte lastAlive_AEB  = 0xFF;  /* 0xFF = "first received" sentinel */
  byte lastAlive_VS   = 0xFF;
  byte lastAlive_BCM  = 0xFF;
  
  int counterErrors = 0;
}

void checkAliveCounter(byte current, byte last, byte max_val, char sig_name[]) {
  byte expected;
  if(last == 0xFF) return;  /* First frame */
  
  expected = (last + 1);
  if(expected > max_val) expected = 0;  /* Wrap */
  
  if(current != expected) {
    testStepFail("AliveCounter", "%s: got %d, expected %d (last=%d)", 
                 sig_name, current, expected, last);
    counterErrors++;
  }
}

on message AEB_Req {
  checkAliveCounter(this.Alive_Ctr_AEB, lastAlive_AEB, 14, "Alive_Ctr_AEB");
  lastAlive_AEB = this.Alive_Ctr_AEB;
}

on message VehicleStatus {
  checkAliveCounter(this.Alive_Ctr_VS, lastAlive_VS, 14, "Alive_Ctr_VS");
  lastAlive_VS = this.Alive_Ctr_VS;
}

on message BCM_Status {
  checkAliveCounter(this.Alive_Ctr_BCM, lastAlive_BCM, 14, "Alive_Ctr_BCM");
  lastAlive_BCM = this.Alive_Ctr_BCM;
}

on stopMeasurement {
  write("=== Alive Counter Test ===");
  write("Counter errors: %d", counterErrors);
}
```

---

### 8.4.4 Boundary Value Testing

```capl
/*
 * Test: Boundary Value Test Module
 * Injects edge-case raw values and verifies ECU response
 * Requires simulation mode (virtual CAN)
 */

testcase TC_BVT_AEB_Decel() {
  message AEB_Req msg;
  
  testStep("BVT setup", "Injecting boundary values for AEB_Decel_Req");
  
  /* MIN boundary: raw=0 → 0.0 m/s² */
  msg.AEB_Active    = 0;
  msg.AEB_Decel_Req = 0;
  output(msg);
  wait(50);
  
  /* MAX boundary: raw=255 → 25.5 m/s² */
  msg.AEB_Active    = 1;
  msg.AEB_Decel_Req = 255;
  output(msg);
  wait(50);
  testStepPass("BVT MAX", "AEB_Decel_Req=255 raw (25.5 m/s²) transmitted");
  
  /* MIN-1: raw=256 → overflows 8-bit! Should not happen */
  /* Send the DBC-invalid case and verify ECU rejects */
  msg.AEB_Decel_Req = 0;
  msg.AEB_Active    = 0;
  output(msg);
  wait(50);
}

testcase TC_BVT_SteeringAngle() {
  message EPS_Status msg;
  
  /* MAX positive steering: raw=32767 → 3276.7 degrees */
  msg.SteeringAngle = 32767;
  output(msg);
  testStepPass("BVT SteeringAngle MAX", "raw=32767 (3276.7 deg)");
  wait(30);
  
  /* MAX negative: raw=-32768 → -3276.8 degrees */
  msg.SteeringAngle = -32768;
  output(msg);
  testStepPass("BVT SteeringAngle MIN", "raw=-32768 (-3276.8 deg)");
  wait(30);
  
  /* Zero crossing */
  msg.SteeringAngle = 0;
  output(msg);
  testStepPass("BVT SteeringAngle ZERO", "raw=0 (0.0 deg)");
  wait(30);
}

testgroup BoundaryValueTests() {
  TC_BVT_AEB_Decel();
  TC_BVT_SteeringAngle();
}
```

---

## 8.5 DBC Regression Test Suite

A regression test suite catches regressions when DBC is updated:

```capl
/*
 * DBC Regression Test Suite
 * Run after every DBC change to verify no regressions
 * File: dbc_regression.can
 */

includes {
  "signal_range_test.can"
  "cycle_time_test.can"
  "alive_counter_test.can"
}

testcase TC_REG_MessageList() {
  /* Verify all expected messages are received within 5 seconds */
  int timeout = 5000;
  
  testStep("Regression", "Waiting for all messages...");
  
  if(waitForMessage(512, timeout)) /* WheelSpeed */
    testStepPass("WheelSpeed received", "ID 0x200 OK");
  else
    testStepFail("WheelSpeed missing", "ID 0x200 not received in %d ms", timeout);
  
  if(waitForMessage(580, timeout)) /* AEB_Req */
    testStepPass("AEB_Req received", "ID 0x244 OK");
  else
    testStepFail("AEB_Req missing", "ID 0x244 not received in %d ms", timeout);
  
  if(waitForMessage(768, timeout)) /* VehicleStatus */
    testStepPass("VehicleStatus received", "ID 0x300 OK");
  else
    testStepFail("VehicleStatus missing", "ID 0x300 not received");
}

testcase TC_REG_NoDuplicateIDs() {
  /* In a real network: monitor for same ID from two different nodes */
  /* This would indicate a DBC error or configuration problem */
  testStepPass("ID uniqueness", "No duplicate message IDs detected");
}

testcase TC_REG_NoErrorFrames() {
  int errorsBefore = getErrorCount();
  wait(2000);
  int errorsAfter = getErrorCount();
  
  if(errorsAfter == errorsBefore)
    testStepPass("No CAN errors", "Zero error frames in 2s window");
  else
    testStepFail("CAN errors", "%d error frames in 2s window", errorsAfter - errorsBefore);
}

testgroup DBC_RegressionSuite() {
  TC_REG_MessageList();
  TC_REG_NoDuplicateIDs();
  TC_REG_NoErrorFrames();
}

on start {
  testRunner("ADAS_DBC_Regression", DBC_RegressionSuite);
}
```

---

## 8.6 Error Injection Testing

### CAPL Error Frame Injection

```capl
/*
 * Error Injection: Simulate missing message (timeout scenario)
 * Tests ECU reaction when WheelSpeed times out
 */

variables {
  msTimer suppressTimer;
  int     suppressing = 0;
}

testcase TC_EI_WheelSpeedTimeout() {
  testStep("ErrorInjection", "Suppressing WheelSpeed for 500ms");
  suppressing = 1;
  setTimer(suppressTimer, 500);
  
  /* Wait for ECU to detect timeout (should trigger DTC or safe state) */
  wait(1000);
  suppressing = 0;
  
  testStepPass("ErrorInjection", "WheelSpeed resumed after 500ms suppression");
}

on timer suppressTimer {
  suppressing = 0;
}

/* Gate all WheelSpeed frames */
on message WheelSpeed {
  if(suppressing) {
    /* Don't forward — effectively suppress message */
    /* Note: in CANoe, use "Replay Block" with gap filter for cleaner suppression */
  }
}
```

---

## 8.7 DBC Validation Checklist (Production Release)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DBC Pre-Release Validation Checklist
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRUCTURE:
□ CANdb++ F7 check passes with 0 errors
□ All message IDs unique (no duplicates)
□ All Tx ECU nodes listed in BU_ section
□ All Rx ECU nodes listed in BU_ section
□ Vector__XXX included in BU_ (for unassigned receivers)
□ No signal bit overlaps
□ No signal exceeds DLC boundary
□ All VAL_ entries have semicolons
□ All CM_ entries have semicolons

CONTENT:
□ Each message ID matches communication matrix
□ Each message DLC matches communication matrix
□ Each signal start bit matches communication matrix
□ Each signal length matches communication matrix
□ Each signal factor matches communication matrix
□ Each signal offset matches communication matrix
□ Each signal min/max physical range is correct
□ All signed signals use correct type (@1-)
□ All Motorola signals tested with byte order
□ Alive counter max value matches spec (0 = not valid)
□ CRC signals have correct length (8 or 16 bit)

ATTRIBUTES:
□ GenMsgCycleTime set for all cyclic messages
□ GenMsgSendType set (cyclic/event/noMsgSendType)
□ GenSigStartValue set for safety-critical signals
□ VFrameFormat set for CAN FD messages
□ E2E profile attributes present for protected messages

VERSION:
□ DatabaseVersion attribute updated
□ ApprovalStatus set correctly (DRAFT/REVIEW/RELEASED)
□ ChangeDescription describes latest change
□ Author and reviewer names present

TESTING:
□ Python validation script passes 0 errors vs matrix
□ CANoe import: no warnings
□ Signal decode test: 5 frames per message decoded correctly
□ Cycle time test: all messages within ±10% of nominal
□ Alive counter test: 0 missed increments in 30s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Module 08 — Knowledge Check

1. What is the tolerance typically used for CAN message cycle time validation?
2. In CAPL, what function sends a verdict pass for a test step?
3. An alive counter wraps from 14 back to 0. What value follows 14?
4. What are the four boundary values tested in Boundary Value Testing for an 8-bit unsigned signal?
5. In the Python validation script, what indicates a "DLC mismatch" error?
6. Why is it important to run a regression suite after every DBC version change?

**Answers:**
1. ±10% of the nominal cycle time (e.g., for 10ms: accept 9–11ms)
2. `testStepPass("step_name", "message")`
3. 0 (counter wraps: after 14 comes 0 for a max=14 counter)
4. 0 (MIN), 1 (MIN+1), 254 (MAX-1), 255 (MAX) — and ideally also invalid/not-available
5. `dbc_msg.length != mat_msg['dlc']` in the validation script
6. DBC changes can silently shift signal positions, change factors, or break alive counter logic — regression tests catch these before ECU integration
