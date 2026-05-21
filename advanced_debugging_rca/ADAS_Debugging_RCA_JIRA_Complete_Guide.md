 # ADAS Validation — Debugging, Root Cause Analysis & JIRA Bug Reporting
## Complete Professional Reference for Automotive Test Engineers

> **Document Classification:** Technical Reference — Validation Engineering
> **Applicable Tools:** CANoe 17.x, vTestStudio, dSPACE SCALEXIO, python-can, JIRA Software
> **Standards Referenced:** ISO 26262, ISO 14229 (UDS), ISO 15765 (CAN transport layer), AUTOSAR
> **Audience:** ADAS validation engineers, HIL engineers, integration test engineers

---

## Table of Contents

1. [Debugging Philosophy in Automotive Testing](#1-debugging-philosophy-in-automotive-testing)
2. [The Five-Layer Debugging Model](#2-the-five-layer-debugging-model)
3. [Reproducing a Defect — Step by Step](#3-reproducing-a-defect--step-by-step)
4. [CANoe Trace Analysis — Deep Dive](#4-canoe-trace-analysis--deep-dive)
5. [Signal-Level Debugging Techniques](#5-signal-level-debugging-techniques)
6. [UDS Diagnostic Debugging (Services 0x19, 0x22, 0x27, 0x2E)](#6-uds-diagnostic-debugging)
7. [State Machine Debugging](#7-state-machine-debugging)
8. [Timing and Latency Debugging](#8-timing-and-latency-debugging)
9. [CAN Bus Electrical Debugging](#9-can-bus-electrical-debugging)
10. [Root Cause Analysis Methods](#10-root-cause-analysis-methods)
    - 10.1 5-Why Analysis
    - 10.2 Fishbone (Ishikawa) Diagram
    - 10.3 Fault Tree Analysis
    - 10.4 Is/Is-Not Analysis
11. [Feature-Specific RCA Playbooks](#11-feature-specific-rca-playbooks)
    - 11.1 BSD — Missed Warning
    - 11.2 ACC — Unexpected Deceleration
    - 11.3 LKA — Torque Not Applied
    - 11.4 FCW — False Positive Warning
    - 11.5 DMS — Drowsiness Not Detected
    - 11.6 PDC — Wrong Zone Reported
12. [CAPL Debugging Scripts Library](#12-capl-debugging-scripts-library)
13. [Python Debugging and Log Analysis Scripts](#13-python-debugging-and-log-analysis-scripts)
14. [JIRA Bug Reporting — Complete Guide](#14-jira-bug-reporting--complete-guide)
    - 14.1 JIRA Project Setup for ADAS Testing
    - 14.2 Defect Severity and Priority Definitions
    - 14.3 Full JIRA Ticket Template — Every Field Explained
    - 14.4 Writing Good vs Bad Bug Titles
    - 14.5 Steps to Reproduce — Professional Formatting
    - 14.6 Attaching Evidence — What and How
    - 14.7 JIRA Workflow States
    - 14.8 Linking Tickets (Defect ↔ Requirement ↔ Test Case)   
    - 14.9 Writing Defect Comments During Investigation
    - 14.10 Closing a Defect After Fix Verification
15. [Real ADAS Bug Examples with Full JIRA Tickets](#15-real-adas-bug-examples-with-full-jira-tickets)
16. [Root Cause Report Template](#16-root-cause-report-template)
17. [Bug Triage Process](#17-bug-triage-process)
18. [Defect Metrics and Trends](#18-defect-metrics-and-trends)

---

  ## 1. Debugging Philosophy in Automotive Testing

### 1.1 The Core Principle: Evidence Before Conclusion

In automotive ECU testing, the single most costly mistake is declaring a root cause before
sufficient evidence is gathered. A common trap: a test case fails, the engineer notices a CAN
signal is missing, assumes "ECU SW bug," and raises a P1 defect — only to discover 2 days later
the CAN terminator was unplugged.

**Golden rule:** Eliminate the test environment before blaming the DUT (Device Under Test).

```
FAILURE OBSERVED
       │
       ▼
Is the test environment healthy?
   ├── CAN bus: correct termination, no error frames, all nodes present?
   ├── ECU powered correctly: voltage 13.0–14.5 V, KL15 applied?
   ├── SW version matches test plan?
   ├── DBC/ARXML database version matches SW build?
   └── No active pre-existing DTCs from prior test?

If ANY of the above is NO → fix the environment first, then re-run
If ALL are YES → proceed to ECU behaviour analysis
```

### 1.2 Reproducibility Is Everything

A bug that cannot be reproduced cannot be fixed. Before raising a JIRA ticket:

| Reproducibility | Action |
|----------------|--------|
| 100% (every run) | Raise immediately — clear steps to reproduce |
| Intermittent (>50% of runs) | Run at least 5 times, document success/fail ratio |
| Rare (<50%) | Investigate environmental triggers; document pattern |
| Not reproducible after 10 attempts | Log as "Cannot Reproduce" with all context; keep open |

### 1.3 The 3Cs Rule for Every Defect

Every defect must answer three questions clearly:

```
CONDITION:  Under exactly what conditions does this occur?
            (speed, gear, signal values, SW version, temperature)

CONSEQUENCE: What exactly is wrong?
             (signal value, missing output, wrong timing, unexpected DTC)

CONTRAST:   What SHOULD happen instead?
            (reference: SRS requirement ID, expected value, timing spec)
```

---

## 2. The Five-Layer Debugging Model

Work from the bottom of the stack upward. Do not jump to layer 3 before confirming layers 1 and 2.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5 — FEATURE LOGIC                                        │
│  ECU application: state machine, algorithm, threshold behaviour  │
│  Tools: XCP/A2L, internal SW logs, state signal monitoring      │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4 — ACTUATOR / OUTPUT                                    │
│  ECU output: CAN messages, LIN frames, I/O pin levels           │
│  Tools: CANoe Trace, oscilloscope on output pins                │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3 — ECU INPUT PROCESSING                                 │
│  Does the ECU receive and parse inputs correctly?               │
│  Tools: UDS 0x22 read DID (if inputs stored), XCP read          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2 — COMMUNICATION                                        │
│  Are signals present, correctly encoded, at correct cycle time? │
│  Tools: CANoe Statistics, Trace, DBC signal decode              │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1 — PHYSICAL / ELECTRICAL                                │
│  Power supply, wiring, termination, connector integrity          │
│  Tools: Multimeter, oscilloscope, impedance measurement         │
└─────────────────────────────────────────────────────────────────┘
```

**Debugging decision at each layer:**
```
Layer 1 CHECK: Voltage = 13.5 V ✓; Bus impedance = 60 Ω ✓; No loose wires ✓ → proceed
Layer 2 CHECK: Message 0x300 present every 20 ms ✓; decoded value correct ✓ → proceed
Layer 3 CHECK: XCP read acc_target_dist_cm = expected value ✓ → proceed
Layer 4 CHECK: 0x502 ACC_Status = 2 as expected ✓; 0x500 ThrottleRequest = 0 ← ANOMALY
                                                           ↑ Found at layer 4
Layer 5 INVESTIGATE: Why does Status=Active but Throttle=0?
                     → Check internal throttle command via XCP
                     → acc_ctrl_throttle_pct = 0 when it should be 30%
                     → ECU logic bug: throttle command not sent when no lead vehicle detected
                       but RadarFwd_ObjectValid flag = 0 (object valid flag not set by test)
                     → Root cause: test setup missing RadarFwd_ObjectValid = 1 for "no target" case
```

---

## 3. Reproducing a Defect — Step by Step

### 3.1 Minimum Required Information to Begin Reproduction

Before touching the bench, collect:

```
□ Exact SW build version (0x22 F1 89 response)
□ Exact DBC/database version used during failure
□ CANoe measurement log (.blf) from the failing run
□ DTC snapshot at time of failure (UDS 0x19 02 0F)
□ Test case ID and exact step at which failure occurred
□ Environmental conditions (voltage, temperature if relevant)
□ Exact CAN frames / signal values at time of failure
□ Screenshot or write-log from the failed run
```

### 3.2 Reproduction Procedure

```
STEP 1 — Restore exact configuration
  - Flash the same SW build that was failing
  - Load the same DBC version
  - Set PSU to 13.5 V (or match the voltage at time of failure)
  - Clear all DTCs: UDS 14 FF FF FF

STEP 2 — Replay the failure scenario
  - If .blf log exists: use CANoe Replay block to feed exact signals
  - If not: manually re-enter the preconditions from the test case

STEP 3 — Open the .blf from the failing run
  - Load it in CANoe as reference
  - Align timestamps from first common event (e.g., KL15 = ON)
  - Open both Graphics windows side by side: reference vs live

STEP 4 — Execute step-by-step
  - Proceed through test case steps one at a time
  - At each step, compare live signals against reference .blf
  - Mark the exact step and timestamp where divergence occurs

STEP 5 — Isolate the divergence point
  - At what exact moment do live and reference traces diverge?
  - Which signal deviates first?
  - That signal is the starting point of root cause analysis
```

### 3.3 Reproduction Rate Documentation

```
Run #1: FAIL — <brief what happened>
Run #2: FAIL
Run #3: PASS — <note any difference in conditions>
Run #4: FAIL
Run #5: FAIL

Reproducibility: 4/5 = 80%
Pattern observed: Passes when [condition X] — this is a clue to the root cause
```

---

## 4. CANoe Trace Analysis — Deep Dive

### 4.1 Trace Window Setup for ADAS Debugging

```
1. Open Trace window: View → Trace
2. Apply filter — only show relevant IDs:
   Filter → Message IDs: 0x200, 0x300, 0x3A0, 0x3B0, 0x410, 0x500-0x510
3. Enable symbolic display:
   Right-click column header → Add Column → "Signal Name" + "Signal Value"
4. Enable absolute and delta timestamps:
   Right-click timestamp column → "Absolute + Relative"
5. Go to failure timestamp: Ctrl+G → enter time in ms
6. Use trigger marker: Edit → Trigger → "Set trigger on message 0x3A0, bit BSD_Left_WarningActive changes to 0"
```

### 4.2 Reading the Trace — What to Look For

**Normal healthy trace pattern:**
```
Time(ms)   ID     Dir  DLC  B0    B1    B2    B3    Signal
---------------------------------------------------------------------
1000.000  0x200  Rx   8   D0    1F    00    00    VehicleSpeed = 81.44
1000.010  0x300  Rx   8   2C    01    FF    7F    RadarRear_L = 300cm
1000.015  0x3A0  Tx   8   01    01    02    00    BSD_L_Obj=1, BSD_L_Warn=1
1010.000  0x200  Rx   8   D0    1F    00    00    VehicleSpeed = 81.44  (10ms cycle ✓)
1010.010  0x300  Rx   8   2C    01    FF    7F    (20ms cycle on this message ✓)
```

**Anomaly patterns and what they mean:**

```
ANOMALY 1: Message gap — missing cycle
  1000.000  0x3B0  Rx   8   2C 01 ...   OK
  1020.000  0x3B0  Rx   8   2C 01 ...   OK
  [gap]
  1060.000  0x3B0  Rx   8   2C 01 ...   ← 40 ms gap instead of 20 ms
  MEANING: CAN node temporarily stopped transmitting (bus-off recovery, SW overload, power glitch)

ANOMALY 2: Unchanged signal value when it should change
  500ms: BSD_Left_WarningActive = 0
  600ms: Radar_Rear_Left_Distance changed from 0x7FFF to 300 cm ← input arrived
  700ms: BSD_Left_WarningActive = 0   ← should be 1 by now
  800ms: BSD_Left_WarningActive = 0   ← still not reacting
  MEANING: ECU received input but did not process it → state machine, DTC suppression, or logic bug

ANOMALY 3: Signal value spikes / glitches
  10.5ms: VehicleSpeed = 80.0 km/h
  10.6ms: VehicleSpeed = 0.0 km/h   ← single-frame glitch
  10.7ms: VehicleSpeed = 80.0 km/h
  MEANING: CAN encoding error OR spurious message injection OR test setup issue

ANOMALY 4: Incorrect signal encoding
  RadarFwd_Distance = 65535 cm (0xFFFF) continuously even with target present
  MEANING: Factor/offset mismatch in DBC vs actual encoding; or test setup sending wrong raw value

ANOMALY 5: Wrong message direction
  ACC_TorqueRequest appears as Rx (received) instead of Tx (transmitted)
  MEANING: DBC has wrong node assignment; or another node is overriding the ECU output
```

### 4.3 Using the Statistics Window

```
CANoe → Statistics window → CAN → Message Statistics

Columns to check:
  Message ID | Name       | Count | Avg Cycle | Min Cycle | Max Cycle | Last Rx
  ------------------------------------------------------------------------------------
  0x200      | VehicleSpd | 5000  | 10.01 ms  | 9.85 ms   | 10.20 ms  | 00:01:23.456
  0x300      | RadarFwd   | 2498  | 20.02 ms  | 19.90 ms  | 25.60 ms  | ← MAX too high!

If any message has:
  - Max cycle > 2× nominal → CAN overload or node bug
  - Count = 0 → message never received → node offline, wrong channel, wrong DBC
  - Count far lower than expected → messages being dropped (bus error, wrong channel)
```

### 4.4 Graphics Window — Correlated Multi-Signal View

```
Create a correlated view to see input-to-output relationship:

Panel layout:
  Row 1: Radar_Rear_Left_Distance    (input — cm)
  Row 2: BSD_Left_ObjectDetected     (ECU intermediate — 0/1)
  Row 3: TurnSignal_Left             (driver input — 0/1)
  Row 4: BSD_Left_WarningActive      (ECU output — 0/1)
  Row 5: BSD_AlertEscalation         (ECU output — 0/1)

Usage:
  - Place Cursor 1 at: Radar distance crosses 350 cm threshold
  - Place Cursor 2 at: BSD_Left_WarningActive → 1
  - Delta = response latency

  If BSD_Left_WarningActive never rises to 1 even though:
    • Radar distance IS within zone (< 350 cm)
    • BSD_Left_ObjectDetected IS = 1
    → The warning output stage is broken (output not being sent even though detection is correct)
    → Different layer: detection logic OK, output logic bug
```

---

## 5. Signal-Level Debugging Techniques

### 5.1 Signal Plausibility Checks

For every ECU input signal, ask:

```
1. Is the signal PRESENT?          (check message arrival in Statistics)
2. Is the value in VALID RANGE?    (compare to DBC min/max)
3. Is the ENCODING correct?        (manual decode: raw → physical via factor/offset)
4. Is the CYCLE TIME correct?      (compare to DBC cycle time)
5. Does it CHANGE when it should?  (inject a known value, verify it changes)
6. Is the value PLAUSIBLE?         (cross-correlate with related signals)
```

**Cross-correlation plausibility example — Wheel Speed vs Vehicle Speed:**
```
At 80 km/h:
  VehicleSpeed (0x200) = 80.0 km/h ✓
  WheelSpeed_FL (0x201 B0-B1) should also ≈ 80.0 km/h ± 2% (normal slip)

If WheelSpeed_FL = 0 km/h while VehicleSpeed = 80 km/h:
  → Wheel speed sensor fault or encoding mismatch
  → ECU may set DTC C1103 (WSS FL implausible)
  → ACC may disable due to implausible WSS

If VehicleSpeed = 0 while WheelSpeed_FL = 80 km/h:
  → BCM is not sending VehicleSpeed (gateway fault)
  → ADAS ECU receives no valid speed → all features disable
```

### 5.2 Manual Signal Decode — Working Example

**Scenario:** `BSD_Left_WarningActive` should be 1 (active), but you see raw byte 0x3A0[B1] = 0x03.

```
Raw byte B1 = 0x03 = binary 0000 0011

Signal map (from DBC):
  bit0 = BSD_Left_WarningActive
  bit1 = BSD_Right_WarningActive
  bit2 = BSD_AlertEscalation
  bit3–7 = reserved

Decode:
  bit0 = 1 → BSD_Left_WarningActive  = 1  ✓
  bit1 = 1 → BSD_Right_WarningActive = 1  ← BOTH sides warning!
  bit2 = 0 → BSD_AlertEscalation     = 0

Is both sides warning correct? If only left target was injected → RIGHT warning is WRONG
→ Potential: ECU mirroring left detection to right; OR right sensor also sees target
→ Investigate: check right radar input for spurious target
```

### 5.3 CAPL: Automated Signal Plausibility Monitor

```c
// Continuous plausibility monitoring — run throughout all test sessions
variables {
  float speed_prev = 0;
  msTimer tPlausCheck;
}

on start {
  setTimer(tPlausCheck, 100);  // check every 100 ms
}

on timer tPlausCheck {
  float v_vehicle = $VehicleSpeed / 100.0;
  float v_wfl     = $WheelSpeed_FL / 100.0;
  float v_wfr     = $WheelSpeed_FR / 100.0;

  // Vehicle speed plausibility vs wheel speed
  if (v_vehicle > 5.0) {  // only check when moving
    if (abs(v_vehicle - v_wfl) > 5.0) {
      write("[PLAUSIBILITY FAIL @%d ms] VehicleSpeed=%.1f vs WheelSpeed_FL=%.1f — delta > 5 km/h",
            timeNow()/100000, v_vehicle, v_wfl);
    }
    if (abs(v_vehicle - v_wfr) > 5.0) {
      write("[PLAUSIBILITY FAIL @%d ms] VehicleSpeed=%.1f vs WheelSpeed_FR=%.1f — delta > 5 km/h",
            timeNow()/100000, v_vehicle, v_wfr);
    }
  }

  // Acceleration plausibility (max physically possible ≈ 10 m/s² = 36 km/h per second)
  float delta_speed = v_vehicle - speed_prev;
  if (abs(delta_speed) > 3.6) {  // > 1 m/s change per 100 ms = > 10 m/s²
    write("[PLAUSIBILITY WARN @%d ms] Unrealistic acceleration: %.1f km/h in 100 ms",
          timeNow()/100000, delta_speed);
  }
  speed_prev = v_vehicle;

  setTimer(tPlausCheck, 100);
}

on message 0x3A0 {  // BSD output — monitor for unexpected simultaneous warnings
  int l_warn = this.byte(1) & 0x01;
  int r_warn = (this.byte(1) >> 1) & 0x01;
  if (l_warn && r_warn) {
    write("[WARN @%d ms] BSD: BOTH sides warning simultaneously — verify radar inputs",
          timeNow()/100000);
  }
}
```

---

## 6. UDS Diagnostic Debugging

### 6.1 Essential UDS Services for Debugging

| Service | Hex | Purpose | When to Use |
|---------|-----|---------|-------------|
| DiagnosticSessionControl | 0x10 | Open Extended/Programming session | Before any diagnostic command |
| SecurityAccess | 0x27 | Unlock ECU for sensitive operations | Before writing data |
| ReadDataByIdentifier | 0x22 | Read ECU internal data (SW version, calibration, status) | At every test start; during RCA |
| WriteDataByIdentifier | 0x2E | Write configuration data | Variant coding; calibration |
| ReadDTCInformation | 0x19 | Read Diagnostic Trouble Codes | After any failure; start of day |
| ClearDiagnosticInfo | 0x14 | Clear all DTCs | Between test cases; after fix |
| RoutineControl | 0x31 | Start/stop ECU routines (calibration, EOL, diagnostics) | Sensor alignment; self-test |
| ReadMemoryByAddress | 0x23 | Read raw ECU memory | Deep debugging when A2L unavailable |
| ECUReset | 0x11 | Hard/soft reset ECU | After flash; after fault injection |
| CommunicationControl | 0x28 | Disable/enable CAN messages | Isolate ECU from network for testing |
| InputOutputControlByIdentifier | 0x2F | Force ECU outputs to known values | Actuator testing; output debugging |

### 6.2 Complete Debugging UDS Session — CAPL Script

```c
// Full diagnostic debugging session — run on key 'D'
on key 'D' {
  dword dtcCode;
  byte  dtcStatus;
  int   i;

  write("========================================");
  write("DIAGNOSTIC DEBUGGING SESSION START");
  write("========================================");

  // Step 1: Open Extended Diagnostic Session
  diagRequest ADAS_ECU.DiagnosticSessionControl_extendedDiagnosticSession req_sess;
  diagSendRequest(req_sess);
  testWaitForEvent(diagResponse ADAS_ECU.DiagnosticSessionControl_extendedDiagnosticSession, 500);
  write("[1] Extended session: %s",
        lastDiagResponse.isPositiveResponse() ? "OK" : "FAILED");

  // Step 2: Read SW Version
  diagRequest ADAS_ECU.ReadDataByIdentifier_F189 req_swver;
  diagSendRequest(req_swver);
  testWaitForEvent(diagResponse ADAS_ECU.ReadDataByIdentifier_F189, 500);
  write("[2] SW Version: %s", diagGetParameterRaw(lastDiagResponse, "F189_SwVersion"));

  // Step 3: Read ECU Configuration / Variant Coding
  diagRequest ADAS_ECU.ReadDataByIdentifier_F180 req_variant;
  diagSendRequest(req_variant);
  testWaitForEvent(diagResponse ADAS_ECU.ReadDataByIdentifier_F180, 500);
  write("[3] Variant Coding DID F180: Raw=%s",
        diagGetParameterRaw(lastDiagResponse, "F180_VariantCode"));

  // Step 4: Read all DTCs
  diagRequest ADAS_ECU.ReadDTCInformation_reportDTCByStatusMask req_dtc;
  req_dtc.DTCStatusMask = 0x0F;
  diagSendRequest(req_dtc);
  testWaitForEvent(diagResponse ADAS_ECU.ReadDTCInformation_reportDTCByStatusMask, 1000);
  write("[4] Active DTCs: %d found", lastDiagResponse.numberOfDTCs);
  for (i = 0; i < lastDiagResponse.numberOfDTCs; i++) {
    write("    DTC[%d]: %06X  Status: 0x%02X  [%s]",
          i,
          lastDiagResponse.DTC[i].DTCNumber,
          lastDiagResponse.DTC[i].StatusByte,
          (lastDiagResponse.DTC[i].StatusByte & 0x08) ? "CONFIRMED" : "PENDING");
  }

  // Step 5: Read ECU internal status DIDs
  diagRequest ADAS_ECU.ReadDataByIdentifier_D100 req_status;  // custom DID: ADAS feature status
  diagSendRequest(req_status);
  testWaitForEvent(diagResponse ADAS_ECU.ReadDataByIdentifier_D100, 500);
  write("[5] ADAS Feature Status DID D100: %s",
        diagGetParameterRaw(lastDiagResponse, "D100_FeatureStatus"));

  write("========================================");
  write("DIAGNOSTIC DEBUGGING SESSION END");
  write("========================================");
}
```

### 6.3 Reading Freeze Frame Data for RCA

When a DTC is set, the ECU captures a snapshot of the vehicle state at the time of failure.
This is invaluable for RCA of intermittent bugs.

```
UDS Request: 19 04 [DTC 3 bytes] 01  → ReadDTCSnapshotRecord

Example: DTC C1501 (BSD Left Radar No Comm) freeze frame
  Request:  19 04 C1 50 01 01
  Response: 59 04 C1 50 01 01 [freeze frame data]

Typical freeze frame content:
  Byte 0–1: VehicleSpeed at time of DTC set        (e.g., 0x1F40 = 8000 → 80.0 km/h)
  Byte 2:   GearPosition                           (e.g., 0x03 = Drive)
  Byte 3:   IgnitionStatus                         (e.g., 0x01 = KL15 ON)
  Byte 4:   SupplyVoltage_V × 10                   (e.g., 0x87 = 135 = 13.5 V)
  Byte 5–6: Odometer_km                            (e.g., 0x4E20 = 20000 km)
  Byte 7:   AmbientTemp_degC + 40 offset           (e.g., 0x4C = 76 - 40 = 36°C)

RCA use of freeze frame:
  - Speed = 80 km/h → DTC not triggered at low speed (not a cold-start issue)
  - Gear = Drive → ECU was active, not in park/shutdown
  - Voltage = 13.5 V → no undervoltage trigger
  - Temp = 36°C → possible thermal issue? Check if DTC recurs at lower temperature
```

### 6.4 Using 0x2F (InputOutputControl) for Actuator Debugging

When an ECU output seems wrong, use 0x2F to force a known value and verify the physical
actuation path is working.

```
Example: PDC buzzer not beeping. Is it an ECU logic issue or buzzer circuit issue?

Step 1: Force buzzer ON via 0x2F
  Request: 2F [DID_Buzzer] 03 [control value = fast beep = 0x03]
  Response: 6F [DID_Buzzer] 03 → ECU confirms control accepted

Step 2: Listen physically — does buzzer beep?
  YES → buzzer hardware and wiring are fine → bug is in PDC logic
  NO  → buzzer circuit fault (wiring, fuse, buzzer hardware) → DTC C1820 confirmed

Step 3: Return control to ECU
  Request: 2F [DID_Buzzer] 00  → shortTermAdjustment, return control to ECU
```

---

## 7. State Machine Debugging

### 7.1 Reconstructing State from CAN Signals

Many ADAS ECUs expose their internal state via a status signal on CAN. But sometimes
only lower-level signals are available, and the state must be inferred.

**ACC State Reconstruction without ACC_Status signal:**

```
Inferred State | Evidence
---------------|--------------------------------------------------
OFF (0)        | ThrottleRequest = 0 AND BrakeRequest = 0 AND
               | no ACC output messages for > 500 ms
STANDBY (1)    | ACC_DisplaySpeed non-zero AND ThrottleRequest = 0
               | AND no lead vehicle handling (no BrakeRequest variation)
ACTIVE (2)     | ThrottleRequest changes dynamically with speed error
               | BrakeRequest rises when lead vehicle injected
OVERRIDE (3)   | ThrottleRequest drops to 0 immediately after BrakeSwitch = 1
               | AND ACC_DisplaySpeed remains non-zero (not cancelled)
```

### 7.2 CAPL State Machine Logger

```c
// Log every state transition for any feature — parametric
variables {
  int bsd_state_prev    = -1;
  int acc_state_prev    = -1;
  int lka_state_prev    = -1;
  int fcw_status_prev   = -1;
  int dms_drowsy_prev   = -1;
}

// BSD system status
on message 0x3A0 {
  int st = this.byte(2) & 0x03;
  if (st != bsd_state_prev) {
    write("[BSD STATE @%d ms] %d → %d  (%s)",
          timeNow()/100000, bsd_state_prev, st,
          st==0?"OFF": st==1?"STANDBY": st==2?"ACTIVE":"UNKNOWN");
    bsd_state_prev = st;
  }
}

// ACC status
on message 0x502 {
  int st = this.byte(0) & 0x07;
  if (st != acc_state_prev) {
    write("[ACC STATE @%d ms] %d → %d  (%s → %s)",
          timeNow()/100000, acc_state_prev, st,
          acc_state_prev==0?"OFF": acc_state_prev==1?"STANDBY":
          acc_state_prev==2?"ACTIVE": acc_state_prev==3?"OVERRIDE":"INIT",
          st==0?"OFF": st==1?"STANDBY": st==2?"ACTIVE": st==3?"OVERRIDE":"?");
    acc_state_prev = st;
  }
}

// LKA status
on message 0x503 {
  int st = this.byte(2) & 0x03;
  if (st != lka_state_prev) {
    write("[LKA STATE @%d ms] %d → %d  (%s)",
          timeNow()/100000, lka_state_prev, st,
          st==0?"OFF": st==1?"STANDBY": st==2?"ACTIVE":"WARNING");
    lka_state_prev = st;
  }
}

// DMS drowsiness level
on message 0x520 {
  int lv = this.byte(0) & 0x03;
  if (lv != dms_drowsy_prev) {
    write("[DMS DROWSY @%d ms] Level: %d → %d  (%s)",
          timeNow()/100000, dms_drowsy_prev, lv,
          lv==0?"ALERT": lv==1?"MILD": lv==2?"MODERATE":"SEVERE");
    dms_drowsy_prev = lv;
  }
}
```

### 7.3 Forbidden State Transitions

Some state transitions are architecturally forbidden. If they occur, it indicates a serious ECU
logic bug that must be escalated as P1.

| Feature | Forbidden Transition | Why It Is Dangerous |
|---------|---------------------|---------------------|
| ACC | ACTIVE → ACTIVE with ThrottleRequest > 80% when BrakeSwitch = 1 | Throttle engaged while braking = runaway |
| LKA | any state → ACTIVE without LKA_Enable = 1 | Unauthorised torque application |
| AEB | any state → BRAKING without FCW_TTC_ms < 1200 | Phantom braking at high speed |
| APA | MANEUVERING → DONE without all USS clear | Collision not detected during manoeuvre |
| DMS | SEVERE drowsiness → no warning | Safety critical non-response |

---

## 8. Timing and Latency Debugging

### 8.1 Understanding Timing Requirements

Every ADAS feature has response latency requirements defined in the SRS:

| Feature | Requirement | Source |
|---------|-------------|--------|
| BSD warning activation | ≤ 300 ms from target entry to warning | SRS-BSD-004 |
| FCW visual warning | ≤ 200 ms from TTC threshold crossing | SRS-FCW-007 |
| FCW haptic warning | ≤ 100 ms after visual warning | SRS-FCW-008 |
| ACC deceleration onset | ≤ 300 ms from target cut-in | SRS-ACC-012 |
| LKA torque onset | ≤ 150 ms from lane offset threshold | SRS-LKA-003 |
| AEB full brake | ≤ 400 ms from obstacle classification | SRS-AEB-001 |
| DMS drowsiness alert | ≤ 2000 ms from sustained eye closure > 80% | SRS-DMS-005 |
| PDC beep rate change | ≤ 100 ms from zone threshold crossing | SRS-PDC-002 |

### 8.2 Latency Measurement Script — Full Suite

```c
// Latency measurement for all ADAS features
variables {
  dword t_BSD_input   = 0;
  dword t_BSD_output  = 0;
  dword t_FCW_input   = 0;
  dword t_FCW_visual  = 0;
  dword t_FCW_haptic  = 0;
  dword t_ACC_cutIn   = 0;
  dword t_ACC_brake   = 0;
  dword t_LKA_offset  = 0;
  dword t_LKA_torque  = 0;

  // Requirements (ms)
  int REQ_BSD  = 300;
  int REQ_FCW_VIS = 200;
  int REQ_FCW_HAP = 100;  // after visual
  int REQ_ACC  = 300;
  int REQ_LKA  = 150;
}

// ── BSD latency ──────────────────────────────────────────────
on message 0x3B0 {  // Rear radar
  int dist_left = (this.byte(0) << 8) | this.byte(1);
  if (dist_left < 350 && dist_left > 0 && t_BSD_input == 0) {
    t_BSD_input = timeNow() / 100000;
  }
}

on signal BSD_Left_WarningActive {
  if (this == 1 && t_BSD_input > 0 && t_BSD_output == 0) {
    t_BSD_output = timeNow() / 100000;
    dword latency = t_BSD_output - t_BSD_input;
    write("[LATENCY BSD] Input→Warning: %d ms  Req: ≤%d ms  [%s]",
          latency, REQ_BSD, latency <= REQ_BSD ? "PASS" : "FAIL");
    t_BSD_input  = 0;
    t_BSD_output = 0;
  }
}

// ── FCW latency ──────────────────────────────────────────────
on signal FCW_TTC_ms {
  // Visual warning threshold: 3000 ms TTC
  if (this <= 3000 && this > 0 && t_FCW_input == 0) {
    t_FCW_input = timeNow() / 100000;
  }
}

on signal FCW_VisualWarning {
  if (this == 1 && t_FCW_input > 0 && t_FCW_visual == 0) {
    t_FCW_visual = timeNow() / 100000;
    dword lat = t_FCW_visual - t_FCW_input;
    write("[LATENCY FCW Visual] TTC≤3s → VisualWarn: %d ms  Req: ≤%d ms  [%s]",
          lat, REQ_FCW_VIS, lat <= REQ_FCW_VIS ? "PASS" : "FAIL");
  }
}

on signal FCW_HapticWarning {
  if (this == 1 && t_FCW_visual > 0 && t_FCW_haptic == 0) {
    t_FCW_haptic = timeNow() / 100000;
    dword lat = t_FCW_haptic - t_FCW_visual;
    write("[LATENCY FCW Haptic] Visual→Haptic: %d ms  Req: ≤%d ms  [%s]",
          lat, REQ_FCW_HAP, lat <= REQ_FCW_HAP ? "PASS" : "FAIL");
    // reset
    t_FCW_input  = 0;
    t_FCW_visual = 0;
    t_FCW_haptic = 0;
  }
}

// ── LKA latency ──────────────────────────────────────────────
on signal LaneOffset_cm {
  if (abs(this) >= 30 && t_LKA_offset == 0) {
    t_LKA_offset = timeNow() / 100000;
  }
}

on signal LKA_TorqueRequest_Nm {
  if (abs(this) > 50 && t_LKA_offset > 0 && t_LKA_torque == 0) {
    t_LKA_torque = timeNow() / 100000;
    dword lat = t_LKA_torque - t_LKA_offset;
    write("[LATENCY LKA] Offset≥30cm → Torque>0.5Nm: %d ms  Req: ≤%d ms  [%s]",
          lat, REQ_LKA, lat <= REQ_LKA ? "PASS" : "FAIL");
    t_LKA_offset = 0;
    t_LKA_torque = 0;
  }
}
```

### 8.3 Common Timing Failure Root Causes

| Symptom | Likely Root Cause | How to Confirm |
|---------|------------------|---------------|
| Latency consistently > spec by fixed amount (e.g., always +50 ms) | SW debounce timer set too long | Check XCP: debounce_time_ms parameter |
| Latency varies randomly ±50 ms | CAN scheduling jitter; ECU task overload | Check task cycle in XCP; measure CAN message timestamps |
| Latency within spec but warning disappears too quickly | Hysteresis timeout too short | Check hold_timer_ms in XCP |
| Latency doubles on second occurrence | First-event flag not cleared | State machine bug: first-event latch not reset |
| No output at all — but ECU is in correct state | Output task not running | Check ECU task schedule via XCP; escalate |

---

## 9. CAN Bus Electrical Debugging

### 9.1 Physical Layer Checks (with Multimeter and Oscilloscope)

**Multimeter checks (ignition ON, no measurement running):**

```
Measurement          | Probe Placement          | Expected     | Fail Indication
---------------------|--------------------------|--------------|------------------
CANH voltage         | CANH to chassis GND      | 2.5–3.5 V    | < 1.5 V = short to GND
                     |                          |              | > 4.5 V = short to VBAT
CANL voltage         | CANL to chassis GND      | 1.5–2.5 V    | Same interpretation
CANH-CANL diff       | CANH to CANL             | 1.0–3.0 V    | < 0.5 V = bus dominant stuck
Bus impedance        | CANH to CANL, ECU off    | 55–65 Ω      | > 70 Ω = terminator missing
                     |                          |              | < 40 Ω = extra termination / short
GND continuity       | ECU chassis GND to bench | < 0.5 Ω      | > 1 Ω = poor GND connection
Supply voltage       | ECU pin 12V to GND       | 12.5–14.5 V  | < 9 V = undervoltage → DTC
```

**Oscilloscope checks (CAN traffic active):**
```
Channel 1: CANH (yellow)
Channel 2: CANL (blue)
Math: CH1 - CH2 (differential — eliminates common-mode noise)

Normal differential signal:
  Dominant bit:  CANH - CANL ≈ +2.0 V
  Recessive bit: CANH - CANL ≈ 0 V

Problems visible on scope:
  Ringing after dominant → short cable stubs, missing termination
  Long dominant stretches → error frame, bus-off condition
  Asymmetric rise/fall → cable impedance mismatch
  DC offset on both lines → common-mode interference (EMC susceptibility)
```

### 9.2 CAN Error Frame Analysis in CANoe

```
CANoe → Trace → enable "Error Frames" display

Error Frame Types:
  Bit Error:    A node transmitted a dominant but read back a recessive → wiring/short
  Stuff Error:  Six consecutive same bits (stuffing rule violation) → electrical noise
  Form Error:   Fixed bit field wrong (EOF, ACK delimiter) → timing/bitrate mismatch
  CRC Error:    Checksum mismatch → data corruption, bitrate mismatch, noise
  ACK Error:    No node acknowledged a frame → receiver offline or no termination

Error counter interpretation:
  TEC (Transmit Error Counter) > 127 → node enters Error Passive
  TEC > 255 → node enters Bus Off (stops transmitting entirely)
  REC (Receive Error Counter) > 127 → node enters Error Passive (still receives)
```

**CAPL: Monitor error frames and alert engineer:**
```c
on errorFrame {
  write("[CAN ERROR FRAME @%d ms] Channel: %d  Type: %s",
        timeNow()/100000,
        this.msgChannel,
        (this.errorFrameType == 1) ? "Bit Error" :
        (this.errorFrameType == 2) ? "Stuff Error" :
        (this.errorFrameType == 3) ? "Form Error" :
        (this.errorFrameType == 4) ? "CRC Error"  :
        (this.errorFrameType == 5) ? "ACK Error"  : "Unknown");
  // If error rate high → trigger alert
}

variables { int errorCount = 0; }
on errorFrame {
  errorCount++;
  if (errorCount % 10 == 0) {
    write("[ALERT] %d CAN error frames observed — investigate physical layer!", errorCount);
  }
}
```

---

## 10. Root Cause Analysis Methods

### 10.1 The 5-Why Method

Start from the observable symptom and ask "Why?" five times. Stop when you reach something
that cannot be questioned further (a root cause that is actionable).

**Example — BSD Warning Not Activating:**

```
SYMPTOM: BSD_Left_WarningActive stays 0 even with target at 300 cm

Why 1: Why is BSD_Left_WarningActive = 0?
        → Because BSD_Left_ObjectDetected = 0 (ECU did not detect the object)

Why 2: Why is BSD_Left_ObjectDetected = 0?
        → Because the ECU is in STANDBY state (BSD_SystemStatus = 1, not 2)

Why 3: Why is BSD in STANDBY instead of ACTIVE?
        → Because VehicleSpeed = 18 km/h (below 20 km/h activation threshold)

Why 4: Why is VehicleSpeed = 18 km/h?
        → Because the test injected speed = 18 km/h; precondition says ≥ 20 km/h was set

Why 5: Why was speed set to 18 km/h if precondition requires 20 km/h?
        → CAN encoding error in CAPL script: setVehicleSpeed(80) was writing
          raw = 80 instead of raw = 80 × 100 = 8000 → actual speed = 0.80 km/h
          (another node was keeping speed at 18 km/h from a previous test)

ROOT CAUSE: Test setup defect — CAPL setVehicleSpeed function had a missing ×100 factor.
             Previous test residual speed value was being used.
CORRECTIVE ACTION: Fix encoding formula; always clear speed to 0 in teardown between TCs.
CLASSIFICATION: Test environment defect — NOT an ECU software bug.
```

### 10.2 Fishbone (Ishikawa) Diagram

Used when the root cause is not immediately obvious. Categorise potential causes:

```
                         EFFECT: FCW Warning Not Triggering at TTC 2.5s
                                              │
          ┌───────────────────────────────────┼────────────────────────────┐
          │                                   │                            │
    SENSOR/INPUT                         ECU LOGIC                   OUTPUT/ACTUATOR
    ──────────────                       ──────────                   ──────────────
    Radar signal missing                 TTC calculation wrong        Warning signal not sent
    Wrong distance encoding              Sensitivity not set          Cluster not receiving
    ObjectValid flag = 0                 SW not handling zero RCS     Warning suppressed by DTC
    Radar blocked DTC                    Speed input wrong            Mode not active
          │                                   │                            │
    COMMUNICATION                       CONFIGURATION                ENVIRONMENT
    ─────────────                        ─────────────               ───────────
    CAN frame delayed                    DBC version mismatch        Speed < min activation
    Message cycle too long               FCW_Sensitivity = 0         Wrong gear position
    ID conflict                          Variant coding: FCW=0        Bench voltage too low
    Bus load > 70%                       Feature disabled in coding   Temperature fault
```

**Working through the fishbone:**
```
1. Check each branch systematically
2. Mark each cause as:
   CONFIRMED (evidence found) | EXCLUDED (evidence rules it out) | UNKNOWN (needs investigation)
3. Confirmed causes that trace to a single point = root cause
4. Multiple confirmed causes = complex failure (rare, document all)
```

### 10.3 Fault Tree Analysis (FTA) — Mini Version

Used for safety-critical failures. Start from the top-level unsafe event and work down.

```
TOP EVENT: AEB fires on empty road (false positive)
                       │
                    [OR gate]
          ┌────────────────────────┐
          │                        │
   Forward radar                Camera fusion
   ghost target                 misclassification
          │                        │
       [OR gate]                [OR gate]
    ┌───────┐               ┌──────────┐
 Radar FW   Metal         Camera lens  Poor lighting
 defect     reflection     dirty       condition
```

**FTA output:** Every leaf node is a basic event (hardware fault, software condition, external factor).
These become individual test cases or validation requirements.

### 10.4 Is/Is-Not Analysis

Highly effective for intermittent bugs. Define exactly what the fault IS and IS NOT:

```
┌─────────────────────┬──────────────────────────┬─────────────────────────────┐
│ Dimension           │ IS (failure present)      │ IS NOT (failure absent)     │
├─────────────────────┼──────────────────────────┼─────────────────────────────┤
│ Feature             │ BSD left side             │ BSD right side              │
│ Speed range         │ 60–90 km/h               │ 20–59 km/h or > 90 km/h     │
│ SW version          │ v2.3.1                    │ v2.3.0 (worked correctly)   │
│ Time of day         │ Any                       │ No pattern                  │
│ Bench vs vehicle    │ Both                      │ Neither — consistent        │
│ Target distance     │ 250–300 cm                │ < 200 cm or > 400 cm        │
│ DTC present?        │ C1501 sometimes pending   │ Not confirmed               │
│ Reproduced by?      │ Engineer A and B          │ Not unique to one person    │
└─────────────────────┴──────────────────────────┴─────────────────────────────┘

INSIGHT from Is/Is-Not:
  - Only at 250–300 cm: boundary zone — likely hysteresis bug in object-in-zone detection
  - Only v2.3.1: regression since v2.3.0 — look at git diff / change log for v2.3.1
  - Only 60–90 km/h: speed-dependent filter change? Check if new speed-dependent zone was added
→ HYPOTHESIS: v2.3.1 introduced a speed-dependent radar zone reduction that shrinks the BSD
  detection zone at high speed, pushing the 300 cm target OUTSIDE the active zone.
```

---

## 11. Feature-Specific RCA Playbooks

### 11.1 BSD — Missed Warning (False Negative)

```
SYMPTOM: Target in blind zone, but no mirror warning

DIAGNOSTIC FLOW:
┌── Step 1: Check BSD_SystemStatus ──────────────────────────────────────────┐
│   = 0 (OFF)?   → Why is BSD OFF?                                            │
│     ├── No BSD_Enable flag? → Test setup issue                             │
│     ├── Active DTC? → Read 0x19; C1501/C1502 = radar lost                  │
│     └── Speed < threshold? → Check VehicleSpeed encoding                   │
│                                                                              │
│   = 1 (STANDBY)? → BSD active but feature not engaged                      │
│     ├── Speed just below threshold? → BVA test: try exact threshold speed  │
│     └── Gear not in D? → Check GearPosition signal                         │
│                                                                              │
│   = 2 (ACTIVE)? → Feature should work; investigate detection layer         │
└─────────────────────────────────────────────────────────────────────────────┘

┌── Step 2: Check BSD_Left_ObjectDetected ────────────────────────────────────┐
│   = 0?  → ECU didn't detect object                                          │
│     ├── Radar input actually present? Check 0x3B0 in trace                 │
│     ├── Distance within zone? Zone boundary may have changed in new SW      │
│     ├── Relative speed of target? Some zones exclude stationary objects     │
│     └── Object classification? Some implementations require object class    │
│                                                                              │
│   = 1?  → Object detected, warning not asserted — output layer bug         │
└─────────────────────────────────────────────────────────────────────────────┘

┌── Step 3: Check warning output ─────────────────────────────────────────────┐
│   BSD_Left_ObjectDetected = 1 but BSD_Left_WarningActive = 0               │
│     ├── Is there an active DTC suppressing the output?                      │
│     ├── Is LightControl node (mirror indicator) offline? Check mirror CAN  │
│     └── Output inhibited by some other condition? (night mode, rain, etc.) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 ACC — Unexpected Deceleration (Phantom Braking)

```
SYMPTOM: ACC decelerates with no lead vehicle present

DIAGNOSTIC FLOW:
1. Check RadarFwd_ObjectValid at time of phantom braking
   = 1 → ECU thinks there IS a valid object → radar false detection
   = 0 → ECU internally computed a target without valid sensor input → algorithm bug

2. Read RadarFwd_Distance and RadarFwd_RelSpeed at braking onset
   Distance approaching 0? → Stationary ghost target (metal bridge, gantry)
   RelSpeed = 0 always? → Stationary target: check if filter for stationary objects is active

3. Check BrakeRequest_mbar value
   Very low (< 50 mbar)? → Mild deceleration; may be natural follow distance control
   High (> 200 mbar)?   → Active emergency braking → P1 safety issue

4. Check FreezeFrame if DTC set
   Was there a DTC at time of braking? C1302 (fusion mismatch)?

5. Cross-check camera data (if available)
   Camera says object present? → Sensor fusion false positive
   Camera says no object? → Radar ghost target; camera overriding correctly or fusion not working

ROOT CAUSE CATEGORIES:
  A. Radar ghost target (physical environment) → filter parameter needs adjustment
  B. Sensor fusion not rejecting stationary ghost → SWRS SRS-FCW fusion algorithm defect
  C. Test environment issue → another CAN node injecting object data
```

### 11.3 LKA — Torque Not Applied

```
SYMPTOM: LKA active, LaneOffset > threshold, but LKA_TorqueRequest = 0

INVESTIGATION:
1. Is LKA_Status = 2 (active)?
   NO → Feature not active:
     - LKA_Enable = 0? (HMI/driver setting)
     - LaneQuality < minimum? (camera degraded)
     - Speed < 60 km/h? (activation threshold)
     - TurnSignal active? (intentional LC suppression)

2. Is LaneOffset_cm correctly received?
   Check 0x350 raw decode vs physical value. DBC mismatch?

3. Is LKA_TorqueRequest_Nm exactly 0 or just low?
   Low (< 10 cm × 100 = 0.1 Nm)? → Gain too low; calibration parameter
   Exactly 0? → Output blocked

4. Is EPS receiving the torque request?
   Send 0x2F to force LKA_TorqueRequest → does EPS respond?
   If YES → ECU output is blocked before CAN send
   If NO → EPS rejects request (LKA not in EPS permission mode)

5. Check EPS status signal
   EPS_LKA_Ready bit = 0? → EPS in manual mode; LKA handshake not completed
```

### 11.4 FCW — False Positive Warning

```
SYMPTOM: FCW visual warning triggers on clear road

DIAGNOSTIC FLOW:
1. Capture RadarFwd_Distance and RadarFwd_ObjectValid at false trigger time
   ObjectValid = 0 but warning fires? → ECU using invalid object → logic bug
   ObjectValid = 1 but no real object? → Radar ghost target

2. Calculate TTC manually from trace data
   TTC = distance_cm / (relative_speed_cm_per_s)
   If TTC calculation from trace ≠ FCW_TTC_ms from ECU → TTC calculation bug

3. Sensitivity setting
   FCW_Sensitivity = 3 (high)? → Lower sensitivity reduces false positives
   If default is 3 and SRS says default = 2 → calibration defect

4. Environmental correlation
   Does false positive occur only near:
     - Metal bridges / gantries? → Stationary ghost target
     - Road work barriers? → High RCS objects
     - Tunnels? → Multipath reflection
   → If YES: environmental rejection filter needs tuning; raise as calibration CR

5. Object classification
   Is the radar classifying the object correctly? (class = vehicle vs infrastructure)
   If class = 0 (unknown) and ECU uses unknown as "potential target" → classification filter bug
```

### 11.5 DMS — Drowsiness Not Detected

```
SYMPTOM: Eye closure held at 85% for 2.5 s, but no drowsiness alert

INVESTIGATION:
1. Verify camera input is received
   Is DMS_FaceDetected = 1 during the test?
   NO → Camera not detecting face → physical camera issue or DMS_FaceDetected signal error

2. Verify EyeClosure_pct is correctly encoded and received by ECU
   XCP read: dms_eye_closure_filtered
   Is filtered value ≠ raw input? → Filter time constant too long (EMA/IIR filter)
   If filtered value never reaches 80% → filter coefficient (alpha) too low; calibration

3. Check timing accumulator
   XCP read: dms_drowsiness_score
   Is score incrementing? If it increments but DrowsinessLevel never changes →
   threshold for level change too high; calibration or SW bug

4. Check speed condition
   DMS usually only active above certain speed or when ACC engaged
   VehicleSpeed < DMS activation speed? → No alert expected

5. Check DMS_DrowsinessLevel signal
   Level = 2 but no audio warning? → Audio output chain fault
   Level = 0 even with score high? → Threshold or reset condition bug
```

### 11.6 PDC — Wrong Zone Reported

```
SYMPTOM: PDC reports CRITICAL (zone 4) when USS distance = 100 cm (should be zone 2)

INVESTIGATION:
1. Verify USS raw distance received correctly
   Is 0x3F1 byte value = 0x64 (100 cm)? YES → input is correct
   Is PDC_Rear_Zone = 4? → ECU is reading zone wrong

2. Check zone boundary configuration (via XCP or calibration data)
   XCP read: pdc_zone_boundaries[4]  (should be: 20, 50, 100, 150 cm for zones 4,3,2,1)
   If boundaries are: {20, 40, 80, 120} → boundaries misconfigured; wrong calibration

3. Check if different sensors have different zones
   All 4 rear sensors at 100 cm = zone 4? → boundary config issue
   Only one sensor triggers zone 4 → individual sensor offset calibration error

4. LIN sensor raw reading vs PDC processed value
   Is LIN frame for that sensor reporting same value as what appears in CAN 0x3F1?
   If LIN says 100 cm but CAN says 40 cm → ECU misreading LIN response
   (LIN data byte order wrong; or different sensor protocol version)
```

---

## 12. CAPL Debugging Scripts Library

### 12.1 Master Debugging Node — Attach to Any Test Session

```c
/*
 * ADAS_Debug_Master.can
 * Purpose: Comprehensive real-time debug logger for all ADAS features
 * Usage:   Include in any CANoe simulation node
 * Output:  CANoe Write window + optional log file
 */

variables {
  // State tracking
  int bsd_state_prev   = -1;
  int acc_state_prev   = -1;
  int lka_state_prev   = -1;
  int fcw_status_prev  = -1;
  int pdc_zone_prev    = -1;

  // Latency tracking
  dword t_stimulus[10];
  dword t_response[10];

  // Counters
  int can_error_count  = 0;
  int bsd_warnings     = 0;
  int fcw_warnings     = 0;

  // File output
  dword debugFile;
  msTimer tHeartbeat;
}

on start {
  debugFile = openFileWrite("debug_session.txt", 0);
  write("[INIT] Debug master started at %s", getLocalTimeString());
  setTimer(tHeartbeat, 5000);
}

on timer tHeartbeat {
  write("[HEARTBEAT] BSD_warns=%d  FCW_warns=%d  CAN_errors=%d  Timestamp=%d ms",
        bsd_warnings, fcw_warnings, can_error_count, timeNow()/100000);
  setTimer(tHeartbeat, 5000);
}

// ── DTC Change Monitor ────────────────────────────────────────────
// Runs UDS 0x19 read automatically every 30 seconds
msTimer tDTC_Poll;
on start { setTimer(tDTC_Poll, 30000); }
on timer tDTC_Poll {
  diagRequest ADAS_ECU.ReadDTCInformation_reportDTCByStatusMask req;
  req.DTCStatusMask = 0x0F;
  diagSendRequest(req);
  setTimer(tDTC_Poll, 30000);
}
on diagResponse ADAS_ECU.ReadDTCInformation_reportDTCByStatusMask {
  if (this.numberOfDTCs > 0) {
    int i;
    write("[AUTO-DTC POLL @%d ms] %d DTC(s) active:", timeNow()/100000, this.numberOfDTCs);
    for (i = 0; i < this.numberOfDTCs; i++) {
      write("  DTC %06X  Status 0x%02X", this.DTC[i].DTCNumber, this.DTC[i].StatusByte);
    }
  }
}

// ── CAN Error Frame Counter ───────────────────────────────────────
on errorFrame {
  can_error_count++;
  if (can_error_count <= 5 || can_error_count % 20 == 0) {
    write("[CAN_ERR #%d @%d ms] ch=%d", can_error_count, timeNow()/100000, this.msgChannel);
  }
}

// ── Feature State Change Logger ───────────────────────────────────
on message 0x3A0 {
  int st = this.byte(2) & 0x03;
  int lw = this.byte(1) & 0x01;
  int rw = (this.byte(1) >> 1) & 0x01;
  if (st != bsd_state_prev) {
    write("[BSD@%d ms] State: %d→%d | L_warn=%d R_warn=%d",
          timeNow()/100000, bsd_state_prev, st, lw, rw);
    bsd_state_prev = st;
  }
  if (lw || rw) bsd_warnings++;
}

on message 0x502 {
  int st = this.byte(0);
  if (st != acc_state_prev) {
    write("[ACC@%d ms] State: %d→%d  Speed_display=%d km/h",
          timeNow()/100000, acc_state_prev, st,
          ((this.byte(1) << 8) | this.byte(2)) / 10);
    acc_state_prev = st;
  }
}

on message 0x510 {
  int vis  = this.byte(0) & 0x01;
  int aud  = (this.byte(0) >> 1) & 0x01;
  int hap  = (this.byte(0) >> 2) & 0x01;
  int ttc  = (this.byte(1) << 8) | this.byte(2);
  int st   = this.byte(3);
  if (st != fcw_status_prev) {
    write("[FCW@%d ms] Status: %d→%d | Visual=%d Audio=%d Haptic=%d TTC=%d ms",
          timeNow()/100000, fcw_status_prev, st, vis, aud, hap, ttc);
    fcw_status_prev = st;
    if (vis || aud || hap) fcw_warnings++;
  }
}

on message 0x530 {
  int zone_r = this.byte(1);
  if (zone_r != pdc_zone_prev) {
    char* zone_name;
    zone_name = zone_r==0?"CLEAR": zone_r==1?"FAR": zone_r==2?"MID":
                zone_r==3?"NEAR": zone_r==4?"CRITICAL":"?";
    write("[PDC@%d ms] Rear zone: %d→%d (%s)  Beep=%d",
          timeNow()/100000, pdc_zone_prev, zone_r, zone_name, this.byte(2));
    pdc_zone_prev = zone_r;
  }
}

on stop {
  write("[STOP] Session summary: BSD_warnings=%d FCW_warnings=%d CAN_errors=%d",
        bsd_warnings, fcw_warnings, can_error_count);
  closeFile(debugFile);
}
```

### 12.2 Message Injection Verification Script

```c
// Verify that your injected messages are actually being received correctly by ECU
// Critical: confirms test setup is injecting what you think it's injecting

on key 'v' {
  write("=== INJECTION VERIFICATION ===");

  // Verify VehicleSpeed injection
  float speed = $VehicleSpeed / 100.0;
  write("VehicleSpeed received by ECU: %.2f km/h  (raw: %d)",
        speed, $VehicleSpeed);

  // Verify Radar forward
  int dist = $RadarFwd_Distance;
  float relspd = $RadarFwd_RelSpeed / 10.0;
  write("RadarFwd: distance=%d cm, relSpeed=%.1f km/h, valid=%d",
        dist, relspd, $RadarFwd_ObjectValid);

  // Verify gear
  write("GearPosition: %d (0=P,1=R,2=N,3=D)", $GearPosition);

  // Verify lane
  write("LaneOffset: %d cm, LaneQuality: %d", $LaneOffset_cm, $LaneQuality);

  // Verify brake
  write("BrakeSwitch: %d, BrakeRequest_mbar: %d",
        $BrakeSwitch, $BrakeRequest_mbar);

  write("=== ECU OUTPUT STATUS ===");
  write("BSD: L_obj=%d R_obj=%d L_warn=%d R_warn=%d Status=%d",
        $BSD_Left_ObjectDetected, $BSD_Right_ObjectDetected,
        $BSD_Left_WarningActive, $BSD_Right_WarningActive, $BSD_SystemStatus);
  write("ACC: Status=%d Throttle=%d%% Brake=%d mbar",
        $ACC_Status, $ThrottleRequest, $BrakeRequest_mbar);
  write("LKA: Status=%d Torque=%d (×0.01 Nm)",
        $LKA_Status, $LKA_TorqueRequest_Nm);
  write("FCW: Visual=%d Audio=%d Haptic=%d TTC=%d ms",
        $FCW_VisualWarning, $FCW_AudioWarning, $FCW_HapticWarning, $FCW_TTC_ms);
}
```

---

## 13. Python Debugging and Log Analysis Scripts

### 13.1 Parse BLF Log File for Feature Analysis

```python
"""
blf_analyzer.py
Parse a CANoe .blf measurement log and extract ADAS signal events.
Requirements: pip install python-can
"""
import can
from datetime import datetime, timedelta

def analyze_blf(filepath: str, feature: str = "BSD"):
    """Extract relevant events from a BLF file for a specific feature."""

    # Signal configuration per feature
    FEATURES = {
        "BSD": {
            "input_ids":  [0x3B0],         # Rear radar
            "output_ids": [0x3A0],          # BSD ECU output
            "desc": "Blind Spot Detection"
        },
        "ACC": {
            "input_ids":  [0x300, 0x200, 0x210, 0x410],
            "output_ids": [0x500, 0x501, 0x502],
            "desc": "Adaptive Cruise Control"
        },
        "FCW": {
            "input_ids":  [0x300, 0x200, 0x440],
            "output_ids": [0x510],
            "desc": "Forward Collision Warning"
        },
        "PDC": {
            "input_ids":  [0x3F1, 0x210, 0x200],
            "output_ids": [0x530],
            "desc": "Parking Distance Control"
        }
    }

    cfg = FEATURES.get(feature)
    if not cfg:
        print(f"Unknown feature '{feature}'. Choose: {list(FEATURES.keys())}")
        return

    all_ids = set(cfg["input_ids"] + cfg["output_ids"])
    events = []
    base_time = None

    print(f"\nAnalysing BLF: {filepath}")
    print(f"Feature: {cfg['desc']}")
    print(f"Watching IDs: {[hex(x) for x in all_ids]}")
    print("-" * 70)

    with can.BLFReader(filepath) as reader:
        for msg in reader:
            if base_time is None:
                base_time = msg.timestamp
            rel_ms = (msg.timestamp - base_time) * 1000

            if msg.arbitration_id in all_ids:
                direction = "IN " if msg.arbitration_id in cfg["input_ids"] else "OUT"
                data_hex = " ".join(f"{b:02X}" for b in msg.data)
                events.append({
                    "time_ms": rel_ms,
                    "id": msg.arbitration_id,
                    "dir": direction,
                    "data": msg.data,
                    "data_hex": data_hex
                })

    print(f"Total relevant frames captured: {len(events)}")
    print()

    # Decode and report events
    for ev in events[:200]:  # limit output to first 200
        decode = decode_frame(ev["id"], ev["data"], feature)
        print(f"[{ev['time_ms']:10.1f} ms] {ev['dir']} 0x{ev['id']:03X}: {ev['data_hex']}  → {decode}")

    return events


def decode_frame(msg_id: int, data: bytes, feature: str) -> str:
    """Decode known ADAS message frames to human-readable form."""
    d = list(data)
    try:
        if msg_id == 0x200:
            speed = ((d[0] << 8) | d[1]) / 100.0
            return f"VehicleSpeed = {speed:.1f} km/h"

        elif msg_id == 0x3B0:
            l_dist = (d[0] << 8) | d[1]
            r_dist = (d[2] << 8) | d[3]
            return (f"Radar_Rear: L={l_dist if l_dist < 0x7FFF else 'NONE'} cm  "
                    f"R={r_dist if r_dist < 0x7FFF else 'NONE'} cm")

        elif msg_id == 0x3A0:
            l_obj  = d[0] & 0x01
            r_obj  = (d[0] >> 1) & 0x01
            l_warn = d[1] & 0x01
            r_warn = (d[1] >> 1) & 0x01
            status = d[2] & 0x03
            st_str = ["OFF","STANDBY","ACTIVE","?"][status]
            return (f"BSD: L_obj={l_obj} R_obj={r_obj} "
                    f"L_warn={l_warn} R_warn={r_warn} Status={st_str}")

        elif msg_id == 0x300:
            dist = (d[0] << 8) | d[1]
            rel  = int.from_bytes(bytes([d[2], d[3]]), 'big', signed=True) / 10.0
            valid = d[4] & 0x01
            return f"RadarFwd: dist={dist} cm  relSpeed={rel:.1f} km/h  valid={valid}"

        elif msg_id == 0x510:
            vis = d[0] & 0x01
            aud = (d[0] >> 1) & 0x01
            hap = (d[0] >> 2) & 0x01
            ttc = (d[1] << 8) | d[2]
            return f"FCW: Visual={vis} Audio={aud} Haptic={hap} TTC={ttc} ms"

        elif msg_id == 0x502:
            st = d[0] & 0x07
            spd = ((d[1] << 8) | d[2]) / 10.0
            st_str = ["OFF","STANDBY","ACTIVE","OVERRIDE"][min(st,3)]
            return f"ACC: Status={st_str} DisplaySpeed={spd:.1f} km/h"

        elif msg_id == 0x530:
            fz = d[0] & 0x07
            rz = d[1] & 0x07
            br = d[2]
            zones = ["CLEAR","FAR","MID","NEAR","CRITICAL"]
            return (f"PDC: Front={zones[min(fz,4)]} Rear={zones[min(rz,4)]} "
                    f"Beep={br}")

    except (IndexError, ValueError):
        return "decode error"
    return f"raw: {' '.join(f'{b:02X}' for b in data)}"


if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "test_log.blf"
    feature  = sys.argv[2] if len(sys.argv) > 2 else "BSD"
    analyze_blf(filepath, feature)
```

### 13.2 Latency Analyser from BLF

```python
"""
latency_checker.py
Automatically measure input-to-output latency from a BLF file.
"""
import can

REQUIREMENTS = {
    "BSD":  {"input_id": 0x3B0, "output_id": 0x3A0, "max_ms": 300},
    "FCW":  {"input_id": 0x300, "output_id": 0x510, "max_ms": 200},
    "ACC":  {"input_id": 0x300, "output_id": 0x501, "max_ms": 300},
    "PDC":  {"input_id": 0x3F1, "output_id": 0x530, "max_ms": 100},
}

def check_latency(filepath: str, feature: str):
    cfg = REQUIREMENTS[feature]
    input_t  = None
    results  = []

    with can.BLFReader(filepath) as reader:
        base = None
        for msg in reader:
            if base is None:
                base = msg.timestamp
            t_ms = (msg.timestamp - base) * 1000

            # Detect input trigger (threshold crossing)
            if msg.arbitration_id == cfg["input_id"] and input_t is None:
                if _is_trigger(msg, feature):
                    input_t = t_ms

            # Detect output trigger
            if msg.arbitration_id == cfg["output_id"] and input_t is not None:
                if _is_output(msg, feature):
                    latency = t_ms - input_t
                    status = "PASS" if latency <= cfg["max_ms"] else "FAIL"
                    results.append((input_t, latency, status))
                    input_t = None  # reset for next event

    print(f"\nLatency Analysis — {feature}")
    print(f"Requirement: ≤ {cfg['max_ms']} ms")
    print(f"{'#':<4} {'Trigger(ms)':<14} {'Latency(ms)':<14} {'Result'}")
    print("-" * 45)
    passes = 0
    for i, (t, lat, st) in enumerate(results, 1):
        print(f"{i:<4} {t:<14.1f} {lat:<14.1f} {st}")
        if st == "PASS":
            passes += 1

    if results:
        avg = sum(r[1] for r in results) / len(results)
        mx  = max(r[1] for r in results)
        print(f"\nSummary: {passes}/{len(results)} PASS  |  Avg={avg:.1f} ms  Max={mx:.1f} ms")
    else:
        print("No latency events found in log.")


def _is_trigger(msg, feature):
    d = list(msg.data)
    if feature == "BSD":
        l_dist = (d[0] << 8) | d[1]
        return 0 < l_dist < 350
    if feature == "FCW":
        dist = (d[0] << 8) | d[1]
        return dist < 5560
    if feature == "ACC":
        dist = (d[0] << 8) | d[1]
        return dist < 5000
    if feature == "PDC":
        return d[0] < 150
    return False

def _is_output(msg, feature):
    d = list(msg.data)
    if feature == "BSD":
        return (d[1] & 0x01) == 1  # BSD_Left_WarningActive
    if feature == "FCW":
        return (d[0] & 0x01) == 1  # FCW_VisualWarning
    if feature == "ACC":
        brake = (d[0] << 8) | d[1]
        return brake > 0
    if feature == "PDC":
        return (d[1] & 0x07) >= 2  # zone ≥ MID
    return False


if __name__ == "__main__":
    import sys
    check_latency(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "BSD")
```

---

## 14. JIRA Bug Reporting — Complete Guide

### 14.1 JIRA Project Setup for ADAS Testing

**Recommended JIRA Project Configuration:**

```
Project Type: Software (Scrum or Kanban)
Issue Types:
  Bug          → Defects found during testing
  Task         → Test execution tasks
  Story        → Feature test coverage items
  Epic         → Per-feature test campaigns (BSD Epic, ACC Epic, etc.)
  Improvement  → Calibration change requests

Custom Fields to Add:
  ECU SW Version         (text)
  DBC Version            (text)
  Bench ID               (single-select: ADAS-Bench-01, 02, 03)
  ADAS Feature           (single-select: BSD, ACC, LKA, LDW, FCW, BCW, DMS, PDC, APA)
  Requirement ID         (text link to DOORS)
  Test Case ID           (text)
  DTC Codes              (text)
  Reproducibility        (single-select: 100%/Intermittent/>50%/<50%/NotReproduced)
  Safety Relevant        (yes/no)
  ASIL Level             (single-select: QM, A, B, C, D)
  Measurement Log        (text: filename/path)
  Root Cause Category    (single-select: SW Logic/Calibration/Test Setup/Communication/HW)

Components (create one per feature):
  BSD, ACC, LKA, LDW, FCW, BCW, DMS, PDC, APA, Diagnostics, Platform, Communication

Labels (for filtering):
  regression, new-feature, safety-critical, confirmed, intermittent,
  needs-triage, pending-fix, fix-verified
```

### 14.2 Defect Severity and Priority Definitions

**Severity** = impact on the product (how bad is the bug):

| Severity | Criteria | ADAS Examples |
|----------|---------|---------------|
| **S1 — Critical** | Safety-critical failure; vehicle may injure occupants or others | AEB fires on empty road; LKA applies full lock steering unexpectedly |
| **S2 — Major** | Core feature non-functional; no workaround | ACC never activates; BSD shows no warnings in any condition |
| **S3 — Minor** | Feature functional but behaves incorrectly in specific conditions | BSD warning 50 ms late; PDC beep rate wrong at 100 cm |
| **S4 — Cosmetic** | HMI/display issue; does not affect function | Cluster displays "km/h" instead of "mph" in US variant |

**Priority** = urgency of fix (when should it be fixed):

| Priority | Criteria | Typical Response Time |
|----------|---------|----------------------|
| **P1 — Immediate** | Safety risk; production gate blocker | Fix within 24–48 hours; escalate to program manager |
| **P2 — High** | Functional regression; sprint blocker | Fix within current sprint (1–2 weeks) |
| **P3 — Medium** | Functional deviation; workaround exists | Fix in next sprint |
| **P4 — Low** | Cosmetic; enhancement | Fix in backlog; schedule as capacity allows |

**Severity vs Priority Matrix:**

```
              PRIORITY
              P1      P2      P3      P4
SEVERITY S1 │ ████   ████    ░░░░    ░░░░
         S2 │ ████   ████    ████    ░░░░
         S3 │ ░░░░   ████    ████    ████
         S4 │ ░░░░   ░░░░    ████    ████

████ = common combination
░░░░ = unusual — explain in comments if you use this combination

Note: A Safety-critical bug (S1) with a known workaround may be P2
      A Minor bug (S3) that blocks a release gate may be P1
```

### 14.3 Full JIRA Ticket Template — Every Field Explained

```
╔══════════════════════════════════════════════════════════════════════╗
║ JIRA BUG TICKET — COMPLETE FIELD GUIDE                              ║
╚══════════════════════════════════════════════════════════════════════╝

FIELD: Summary (Title)                                   [REQUIRED]
────────────────────────────────────────────────────────────────────
Format:  [FEATURE] [component]: [observable symptom] [in what condition]
Example: [BSD] [Warning Output]: Left mirror warning not activated
         with target at 300 cm at 80 km/h

Rules:
  ✓ Start with feature code in square brackets
  ✓ One sentence; 60–80 characters
  ✓ Describe WHAT IS WRONG, not WHY
  ✗ Do NOT write: "Bug in BSD" (too vague)
  ✗ Do NOT write: "BSD warning timing issue" (not enough context)
  ✗ Do NOT write: "Fix BSD" (describes action, not the defect)

FIELD: Issue Type                                        [REQUIRED]
────────────────────────────────────────────────────────────────────
Select: Bug

FIELD: Priority                                          [REQUIRED]
────────────────────────────────────────────────────────────────────
Select based on priority definitions above.
If safety-relevant: default to P1 until assessed in triage.

FIELD: Severity                                          [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Select: S1 / S2 / S3 / S4

FIELD: ADAS Feature                                      [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Select from: BSD / ACC / LKA / LDW / FCW / BCW / DMS / PDC / APA

FIELD: Component/s                                       [REQUIRED]
────────────────────────────────────────────────────────────────────
Select the relevant JIRA project component (same as feature)

FIELD: ECU SW Version                                    [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: v2.3.1_build_4512
Find via: UDS 0x22 F1 89 at start of test

FIELD: DBC Version                                       [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: ADAS_ECU_v1.4.dbc (date: 2026-03-15)

FIELD: Bench ID                                          [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: ADAS-HIL-Bench-02

FIELD: Reproducibility                                   [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: 5/5 (100%)  or  3/10 (intermittent)

FIELD: Test Case ID                                      [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: TC-BSD-001

FIELD: Requirement ID                                    [OPTIONAL — Custom Field]
────────────────────────────────────────────────────────────────────
Example: SRS-BSD-004

FIELD: DTC Codes                                         [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: C1501 (CONFIRMED, status 0x2F)  or  None

FIELD: Safety Relevant                                   [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Select: Yes / No
If Yes → ASIL Level must also be filled

FIELD: Measurement Log                                   [REQUIRED — Custom Field]
────────────────────────────────────────────────────────────────────
Example: //server/ADAS_Logs/2026-05-04_BSD_v2.3.1_bench02.blf

FIELD: Description                                       [REQUIRED]
────────────────────────────────────────────────────────────────────
See Section 14.5 for formatting.

FIELD: Attachments                                       [REQUIRED]
────────────────────────────────────────────────────────────────────
See Section 14.6 for what to attach.

FIELD: Linked Issues                                     [OPTIONAL]
────────────────────────────────────────────────────────────────────
Link to:
  - Test case JIRA ticket: "is tested by" TC-BSD-001
  - Requirement ticket: "relates to" SRS-BSD-004
  - Duplicate: "duplicates" JIRA-XXXX
  - Caused by: "is caused by" JIRA-XXXX (if known)
  - Blocked by: "is blocked by" JIRA-XXXX (if fix pending)
```

### 14.4 Writing Good vs Bad Bug Titles

```
BAD TITLES — what NOT to write:
─────────────────────────────────────────────────────────────────
✗ "Bug in BSD"
✗ "LKA doesn't work"
✗ "Test case failed"
✗ "ACC problem at high speed"
✗ "Wrong output from ECU"
✗ "Fix the warning"
✗ "ADAS issues found today"

GOOD TITLES — clear, specific, actionable:
─────────────────────────────────────────────────────────────────
✓ "[BSD] Left mirror warning not activated with target at 280 cm and 80 km/h"
✓ "[ACC] Unexpected deceleration (BrakeRequest > 200 mbar) with no lead vehicle at 100 km/h"
✓ "[LKA] Corrective torque not applied when LaneOffset exceeds +40 cm at 80 km/h"
✓ "[FCW] Visual warning fires at TTC 3.8 s — 800 ms early vs 3.0 s threshold"
✓ "[DMS] Drowsiness alert not triggered after 2.5 s at 85% eye closure with face detected"
✓ "[PDC] Rear zone reported as CRITICAL (4) when USS distance = 100 cm (expected: MID)"
✓ "[APA] APA_Status stuck at SCANNING after valid parking space detected at 5 km/h"

TITLE ANATOMY:
  [FEATURE]  [Component or signal that is wrong]:  [What is observed]
             [in what condition / at what value / compared to what expected]
```

### 14.5 Steps to Reproduce — Professional Formatting

The Steps to Reproduce section is the most important part of the bug report. A developer must
be able to reproduce the failure from your steps alone — without asking you anything.

**Template:**
```
*Environment*
- ECU SW Version:   v2.3.1_build_4512
- DBC Version:      ADAS_ECU_v1.4.dbc
- Bench:            ADAS-HIL-Bench-02
- CANoe Version:    17.0 SP4
- Measurement log:  //server/logs/2026-05-04_BSD_bench02.blf

*Preconditions*
1. ECU flashed with v2.3.1_build_4512 and verified via UDS 0x22 F1 89
2. All DTCs cleared: UDS 14 FF FF FF — confirmed 0 DTCs after clear
3. BSD_Enable = 1 (set via CANoe IG on message 0x3A0)
4. GearPosition = D (Drive): CAN 0x210 B0 = 0x03
5. TurnSignal = OFF (both): CAN 0x220 B0 = 0x00

*Steps*
Step 1: Set VehicleSpeed = 80 km/h
        CAN 0x200: [0xD0, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        Verify: VehicleSpeed signal in Graphics window = 80 km/h

Step 2: Wait 500 ms for ECU to stabilise in ACTIVE state
        Verify: BSD_SystemStatus (0x3A0 B2) = 0x02 (ACTIVE)

Step 3: Set Radar_Rear_Left_Distance = 280 cm (within BSD detection zone)
        CAN 0x3B0: [0x18, 0x01, 0xFF, 0x7F, 0x00, 0x00, 0x00, 0x00]
        (0x0118 = 280 cm; B2-B3 = 0x7FFF = no right target)
        Verify: message visible in CANoe Trace with correct decode

Step 4: Wait 500 ms for ECU processing (spec requirement: ≤ 300 ms)

*Observed Result*
- BSD_Left_ObjectDetected (0x3A0 B0 bit0) = 0  ← should be 1
- BSD_Left_WarningActive  (0x3A0 B1 bit0) = 0  ← should be 1
- BSD_SystemStatus remains 2 (ACTIVE) — feature is running but not detecting
- No DTC set

*Expected Result*
Per SRS-BSD-004:
"The BSD system shall detect a valid target in the left blind zone
 and assert BSD_Left_ObjectDetected = 1 and BSD_Left_WarningActive = 1
 within 300 ms of the target entering the defined detection zone,
 when vehicle speed ≥ 20 km/h and no suppression condition is active."

*Reproducibility*
5/5 runs: FAIL (100% reproducible)

*Additional Context*
Same test passed with SW v2.3.0_build_4470.
The test case was last passing on 2026-04-28 with the previous build.
The detection zone for LEFT side appears to have changed between builds.
RIGHT side BSD (with right radar target) works correctly in same session.
```

### 14.6 Attaching Evidence — What and How

**Mandatory attachments for every bug:**

```
1. CANoe Measurement Log (.blf)
   - Contains full raw CAN trace from test session
   - Naming: YYYY-MM-DD_<feature>_<SW-build>_<bench>.blf
   - Store on: shared drive, then paste path in Measurement Log field

2. CANoe Screenshot (PNG)
   - Trace window at the exact failure timestamp
   - Graphics window showing input and output signals correlated
   - Annotate with red arrows/circles pointing to the anomaly
   - How: CANoe → File → Print Window → save PNG; drag into JIRA

3. DTC Snapshot
   - Run UDS 0x19 02 0F; copy response bytes + interpretation
   - Paste directly into Description as a code block

4. CAPL Write Log (if applicable)
   - Copy CAPL write output that shows signal values at failure time
   - Paste as code block in JIRA description

5. Video recording (for intermittent bugs)
   - Record bench screen + CANoe Trace + physical ECU during failure
   - Use OBS Studio or Windows screen recorder
   - Upload to JIRA as .mp4 attachment
```

**Optional but valuable:**
```
6. Comparison with previous passing build
   - Screenshot from v2.3.0 (passing) vs v2.3.1 (failing)
   - Side-by-side comparison makes the defect obvious to developers

7. Oscilloscope trace (for electrical/timing bugs)
   - Export as CSV or screenshot
   - Annotate the exact measurement values

8. XCP variable log
   - If internal ECU variables were captured
   - Export from CANoe XCP window or INCA as CSV
```

**How to attach in JIRA:**
```
Drag-and-drop files directly onto the JIRA ticket comment box
OR
Click the "paperclip" icon in the ticket toolbar → Browse files
Limit: most JIRA instances allow up to 25 MB per attachment; use .zip for large .blf files
```

### 14.7 JIRA Workflow States

```
OPEN
  │
  │  Assigned by test lead to developer during triage
  ▼
IN PROGRESS (Developer)
  │
  │  Developer analyses, codes the fix, raises PR
  ▼
IN REVIEW (Code Review)
  │
  │  Code review passed; build created with fix
  ▼
READY FOR VERIFICATION (new build delivered)
  │
  │  Test engineer re-runs test case on new build
  ▼
  ├── Fix confirmed → VERIFIED
  │       │
  │       └── Closed by test lead → CLOSED
  │
  └── Fix not effective OR new defect introduced
          │
          └── REOPENED (add comment: "Fix not verified, see comment #N")
                │
                └── Returns to IN PROGRESS
```

**State transition rules:**
```
OPEN → IN PROGRESS:          Developer assigned + acknowledged
IN PROGRESS → IN REVIEW:     Fix committed + PR linked in JIRA
IN REVIEW → RTF_VERIFY:      PR merged + build available; comment with build ID
RTF_VERIFY → VERIFIED:       Test engineer re-ran TC → PASS on new build
RTF_VERIFY → REOPENED:       Fix failed; comment added explaining why
VERIFIED → CLOSED:           Test lead confirms; closes ticket
ANY_STATE → WONT_FIX:        Program decision; must be approved by test lead + PM
ANY_STATE → DUPLICATE:       Link to original ticket; close this one
```

### 14.8 Linking Tickets

```
In JIRA ticket → "Link" button → choose link type:

Link Type        | When to Use                                    | Direction
─────────────────|────────────────────────────────────────────────|──────────
is caused by     | This bug is caused by another JIRA ticket       | Bug → Root
duplicates       | Same bug reported twice                         | Newer → Older
blocks           | This bug prevents another ticket from closing   | Bug → Task
is blocked by    | Fix waiting on another ticket                   | Bug → Dependency
relates to       | Associated requirement or test case             | Bug → Req
is tested by     | The TC that caught this bug                     | Bug → TC
clones           | Copy of a bug for another variant/bench         | New → Original

Examples:
  ADAS-1234 "BSD warning late" is caused by ADAS-1198 "Radar cycle time change"
  ADAS-1234 "BSD warning late" is tested by TC-BSD-001 (test case ticket)
  ADAS-1234 "BSD warning late" relates to SRS-BSD-004 (requirement ticket)
  ADAS-1234 duplicates ADAS-1199 (same bug reported by different engineer)
```

### 14.9 Writing Defect Comments During Investigation

**Good comment practice:**

```
COMMENT 1 — Initial investigation (by test engineer, day of filing):
────────────────────────────────────────────────────────────────────────────
Confirmed reproducible: 5/5 runs fail with exact steps above.

Additional observation: Tested with v2.3.0 (previous build) — BSD works correctly.
See attached comparison screenshot (v230_passing_vs_v231_failing.png).

Testing right-side BSD in same session: TC-BSD-002 PASSES.
This isolates the defect to the LEFT side detection logic in v2.3.1.

DTC status: No DTC set — ECU does not self-detect this as a failure.
XCP read: bsd_left_object_detected_internal = 0 even with radar at 280 cm.
          bsd_zone_left_boundary_cm = 250 (was 350 in v2.3.0 — CHANGED!)
→ Hypothesis: Detection zone left boundary was changed from 350 cm to 250 cm
  between v2.3.0 and v2.3.1, causing the 280 cm target to be OUTSIDE the zone.

Assigning to: [Developer Name] for investigation of zone boundary change.
────────────────────────────────────────────────────────────────────────────

COMMENT 2 — Developer response (by developer):
────────────────────────────────────────────────────────────────────────────
Confirmed. In v2.3.1, a calibration parameter change was merged for the
right-side zone (SRS-BSD-012). However, the parameter array index for
left vs right was swapped in the merge (git commit a3f8c12):

  pdc_zone_boundary[LEFT]  was set to 250 (should remain 350)
  pdc_zone_boundary[RIGHT] was set to 350 (should be 250 per SRS-BSD-012)

Fix: swap the array indices. PR raised: PR-4521.
New build with fix: v2.3.2_build_4601 — available for re-test.
────────────────────────────────────────────────────────────────────────────

COMMENT 3 — Fix verification (by test engineer):
────────────────────────────────────────────────────────────────────────────
Re-tested on v2.3.2_build_4601 on ADAS-HIL-Bench-02.

TC-BSD-001: PASS — BSD_Left_WarningActive = 1 at 280 cm within 210 ms
TC-BSD-002: PASS — Right side unaffected
TC-BSD-003: PASS — No warning below speed threshold

XCP confirmed: bsd_zone_left_boundary_cm = 350 (restored to correct value)

Regression impact: Re-ran TC-BSD-001 through TC-BSD-004 — all PASS.
Recommend CLOSING this ticket.
────────────────────────────────────────────────────────────────────────────
```

### 14.10 Closing a Defect After Fix Verification

**Before clicking "Verify" / "Close" in JIRA:**

```
Verification Checklist:
  [ ] Re-ran the exact failing test case (same preconditions, same bench)
  [ ] Test case PASSES on new build
  [ ] Re-ran at least 3 runs to confirm stability
  [ ] Regression tests for the affected feature also pass
  [ ] DTC snapshot: no unexpected DTCs on new build
  [ ] XCP confirmed parameter fix (if applicable)
  [ ] Measurement log from passing run saved and archived
  [ ] Comment added with: build version, pass result, date, engineer name

Fill in JIRA "Resolution" field:
  Fixed            → Normal closure after confirmed fix
  Won't Fix        → Business decision (requires approval)
  Cannot Reproduce → After 10+ attempts without success
  Duplicate        → Link to original; close this one
  By Design        → Behaviour is correct; test case was wrong (requires SRS reference)

Fixed-in version: update the "Fix Version" field with the build that fixed it
Close the ticket
```

---

## 15. Real ADAS Bug Examples with Full JIRA Tickets

### Bug #1 — BSD False Positive (Safety Critical)

```
JIRA ID:       ADAS-1156
Summary:       [BSD] Right mirror warning activated at 120 km/h with no vehicle in blind spot
Priority:      P1
Severity:      S1 — Safety Critical
Safety:        Yes — ASIL A
Feature:       BSD
SW Version:    v3.1.0_build_5010
Reproducibility: 3/5 (intermittent — occurs at specific speeds)
DTC Codes:     None

DESCRIPTION
Environment:
  Bench: ADAS-HIL-Bench-01
  CAN log: //server/logs/2026-05-01_BSD_false_positive.blf

Preconditions:
  1. VehicleSpeed = 120 km/h
  2. No right rear radar target: 0x3B0 B2-B3 = 0x7FFF
  3. BSD_Enable = 1, Gear = D

Steps:
  1. Set VehicleSpeed = 120 km/h (CAN 0x200: [0xD0, 0x2E, ...])
  2. Radar right target = 0x7FFF (no object)
  3. Wait 2 seconds

Observed: BSD_Right_WarningActive = 1 (WRONG — no target present)
          BSD_Right_ObjectDetected = 1 (WRONG — no target was injected)
          Duration: 350–600 ms, then clears

Expected: Both signals = 0 (no target, no warning)

Reproducibility: Occurs 3 of 5 times at exactly 120 km/h. Does NOT occur at 80 or 100 km/h.

XCP: bsd_right_obj_detected_raw = 1 at the moment of false warning
     bsd_right_radar_distance_cm = 312 during false detection
     (no target was injected — distance 312 cm appeared from nowhere)

HYPOTHESIS: At 120 km/h, the ego speed calculation used in the Doppler compensation
for stationary-object rejection may be producing a ghost object at the detection zone
boundary. This is a speed-dependent sensor fusion bug.

Attachments:
  - BSD_false_positive_trace_120kmh.png
  - 2026-05-01_BSD_v3.1.0_bench01.blf
```

---

### Bug #2 — ACC Timing Regression (Major)

```
JIRA ID:       ADAS-1187
Summary:       [ACC] BrakeRequest response latency 485 ms — exceeds 300 ms requirement
               on lead vehicle cut-in at 100 km/h
Priority:      P2
Severity:      S2 — Major
Safety:        Yes — ASIL B
Feature:       ACC
SW Version:    v3.2.0_build_5110
Reproducibility: 5/5 (100%)
DTC Codes:     None
Requirement:   SRS-ACC-012 ("BrakeRequest within 300 ms of target cut-in")

DESCRIPTION
Environment:
  Bench: ADAS-HIL-Bench-02

Preconditions:
  1. VehicleSpeed = 100 km/h
  2. ACC active (set speed = 100 km/h, gap = 2)
  3. No lead vehicle

Steps:
  1. ACC active at 100 km/h (TC-ACC-002 precondition)
  2. Inject lead vehicle at 20 m, relative speed = -30 km/h

Observed:
  Time of RadarFwd_Distance < 5000 cm: t = 10450 ms
  Time of BrakeRequest_mbar > 0:       t = 10935 ms
  LATENCY = 485 ms  ← EXCEEDS 300 ms requirement

  Note: v3.1.0 measured latency: 187 ms (was passing)
  v3.2.0 introduced a new radar pre-processing filter — likely adds ~200 ms delay

Expected:
  BrakeRequest onset within 300 ms (SRS-ACC-012)

Latency measurement run 5 times:
  Run 1: 485 ms FAIL
  Run 2: 492 ms FAIL
  Run 3: 479 ms FAIL
  Run 4: 488 ms FAIL
  Run 5: 483 ms FAIL
  Average: 485 ms — consistently over requirement by 185 ms

XCP: acc_radar_prefilter_delay_ms = 200 (new parameter in v3.2.0, not in v3.1.0)
     This appears to be the source of the additional latency.

Attachments:
  - ACC_latency_comparison_v310_vs_v320.png
  - 2026-05-04_ACC_latency_v3.2.0_bench02.blf
```

---

### Bug #3 — LKA State Machine Bug (Minor/Major)

```
JIRA ID:       ADAS-1199
Summary:       [LKA] LKA_Status transitions directly from STANDBY (1) to WARNING (3)
               without passing through ACTIVE (2) on first activation
Priority:      P2
Severity:      S3 — Minor (no torque applied in wrong state — safe but incorrect)
Safety:        No
Feature:       LKA
SW Version:    v3.2.0_build_5110
Reproducibility: 10/10 (100% — on first activation after each ignition cycle)
DTC Codes:     None
Requirement:   SRS-LKA-001

DESCRIPTION
Preconditions:
  Fresh ignition cycle (ECU reset), LKA_Enable = 1, Speed = 80 km/h, LaneQuality = 12

Steps:
  1. Start measurement (fresh after ECU reset / ignition ON)
  2. Set VehicleSpeed = 80 km/h
  3. Enable LKA: CAN 0x430 B0 = 0x01
  4. Set LaneOffset = 0 cm, LaneQuality = 12

Observed (first activation):
  t=0 ms:    LKA_Status = 0 (OFF)
  t=105 ms:  LKA_Status = 1 (STANDBY)
  t=210 ms:  LKA_Status = 3 (WARNING) ← skipped state 2!
  t=850 ms:  LKA_Status = 2 (ACTIVE) ← eventually reaches active

Expected:
  OFF → STANDBY → ACTIVE (no skipping to WARNING on first activation)
  WARNING state should only appear when LaneQuality is LOW

Subsequent activations (second time onwards): CORRECT (OFF → STANDBY → ACTIVE)
This is a first-time initialisation state machine bug.

XCP at t=210 ms: lka_lane_quality_init_flag = 0 (initialisation flag not set)
                 lka_quality_last_known = 0 (default value = 0, interpreted as LOW quality)
ROOT CAUSE HYPOTHESIS:
  On first activation, lka_quality_last_known defaults to 0 (lowest quality)
  causing an immediate transition to WARNING before the first camera frame is processed.
  Subsequent activations use the last known quality = 12 (correct).

Attachments:
  - LKA_state_machine_first_activation_trace.png
  - 2026-05-04_LKA_SM_v3.2.0_bench02.blf
```

---

## 16. Root Cause Report Template

Use this for all P1/P2 defects after fix verification.

```markdown
# ROOT CAUSE ANALYSIS REPORT

**JIRA ID:**         ADAS-1187
**Title:**           ACC BrakeRequest latency 485 ms exceeds 300 ms requirement
**Date of Failure:** 2026-05-03
**Date of Report:**  2026-05-05
**Author:**          [Test Engineer Name]
**Reviewed by:**     [Test Lead / Safety Manager]

---

## 1. FAILURE DESCRIPTION

| Field | Value |
|-------|-------|
| Feature | ACC |
| SW Version | v3.2.0_build_5110 |
| Severity | S2 Major |
| Safety | ASIL B |
| Requirement | SRS-ACC-012: BrakeRequest ≤ 300 ms after cut-in |

**Observed:** BrakeRequest onset latency = 485 ms (average of 5 runs)
**Expected:** ≤ 300 ms per SRS-ACC-012

---

## 2. TIMELINE

| Date/Time | Event |
|-----------|-------|
| 2026-04-28 | v3.2.0 delivered to test team |
| 2026-05-03 | TC-ACC-002 executed — FAIL; latency 485 ms |
| 2026-05-03 | JIRA ADAS-1187 raised, P2 |
| 2026-05-04 | Developer analysis: new pre-filter found |
| 2026-05-05 | Fix proposed: reduce prefilter delay |
| 2026-05-06 | v3.2.1_build_5125 delivered with fix |
| 2026-05-06 | Fix verified: latency = 198 ms (PASS) |

---

## 3. ROOT CAUSE ANALYSIS

### 3.1 Five-Why

```
Why 1: Why was latency 485 ms?
  → New radar pre-processing filter added in v3.2.0 adds ~200 ms delay before
    radar data is passed to ACC algorithm.

Why 2: Why was the 200 ms filter added?
  → Radar engineering team added a median filter to reduce noise on noisy test track.

Why 3: Why was the 200 ms chosen?
  → Empirically tuned for noise reduction without SRS timing impact analysis.

Why 4: Why was the SRS timing requirement not checked?
  → The parameter change (acc_radar_prefilter_delay_ms) was classified as a
    calibration change, not a SW change — calibration changes bypassed the
    formal impact analysis checklist.

Why 5: Why does the calibration change process not require timing impact analysis?
  → The calibration change process predates SRS-ACC-012. The process was not updated
    when the 300 ms requirement was added to the SRS.

ROOT CAUSE: Process gap — calibration parameter changes that affect timing
            are not subject to SRS timing requirement impact analysis.
```

### 3.2 Is/Is-Not Summary

| Dimension | Is | Is Not |
|-----------|----|----|
| SW build | v3.2.0 | v3.1.0 |
| Speed | Any | Speed-specific |
| Feature | ACC | All other features |
| Parameter | acc_radar_prefilter_delay_ms | All other parameters |

---

## 4. CORRECTIVE ACTION

| # | Action | Owner | Due | Status |
|---|--------|-------|-----|--------|
| 1 | Reduce acc_radar_prefilter_delay_ms from 200 ms to 20 ms | SW Dev | 2026-05-05 | DONE |
| 2 | Add SRS timing requirement check to calibration change checklist | Process Owner | 2026-05-15 | IN PROGRESS |
| 3 | Backlog: review all calibration parameters for timing SRS conflicts | Test Lead | 2026-05-30 | OPEN |

---

## 5. VERIFICATION

**Fix build:** v3.2.1_build_5125
**Latency after fix:**
  Run 1: 198 ms PASS
  Run 2: 201 ms PASS
  Run 3: 195 ms PASS
  Average: 198 ms — within 300 ms requirement

**Regression:** TC-ACC-001 through TC-ACC-004 all PASS on v3.2.1

---

## 6. LESSONS LEARNED

1. Calibration changes with timing impact must be reviewed against SRS timing requirements
2. Any new filter with latency > 50 ms should trigger an automatic SRS timing check
3. Pre-filter parameters should be explicitly listed in the SW change impact analysis

---

**Sign-off**
Test Engineer: _________________    Date: __________
Test Lead:     _________________    Date: __________
Safety Manager (ASIL B): _________  Date: __________
```

---

## 17. Bug Triage Process

### 17.1 Weekly Triage Meeting — Agenda and Rules

```
PARTICIPANTS:  Test lead, senior test engineers, SW development lead, PM
FREQUENCY:     Weekly (or 2× per week near release)
DURATION:      60 minutes maximum
INPUT:         New defects raised since last triage + overdue P1/P2

AGENDA:
  1. New defects review (5 min each):
     - Test engineer presents: what failed, steps, evidence
     - Team agrees: severity, priority, component, owner
     - Decision: Fix / Won't Fix / Needs Info / Duplicate

  2. P1/P2 status (2 min each):
     - Developer gives 2-sentence status: current analysis, ETA
     - Test lead notes any change to risk assessment

  3. Metrics review (5 min):
     - Total open: [N]  P1: [N]  P2: [N]  P3: [N]
     - Defects closed since last triage: [N]
     - Trend: increasing / stable / decreasing

  4. Release gate status:
     - Any P1 open? → Cannot release until resolved
     - P2 count vs release criteria

TRIAGE DECISION RULES:
  ✓ Test engineer presents evidence before severity is debated
  ✓ Developer cannot close a ticket without test engineer verification
  ✓ P1 bugs: developer must acknowledge within 4 hours
  ✓ "Won't Fix" requires PM + test lead sign-off
  ✓ "By Design" requires SRS reference — cannot be assumed
```

### 17.2 Triage Decision Matrix

```
Is the failure reproducible?
  NO (after 10 attempts)  → Set to "Cannot Reproduce"; assign monitoring action
  YES →

Is it a test setup issue?
  YES → Close as "Invalid"; fix test procedure; re-execute
  NO →

Is it a known/duplicate?
  YES → Link to original; close as "Duplicate"
  NO →

Is safety relevant?
  YES → P1 immediately; notify safety manager; do not wait for triage meeting
  NO →

Score Severity (1–4) × Priority (1–4):
  Score ≥ 6 → P1/P2: assign to sprint immediately
  Score 4–5 → P3: add to sprint backlog
  Score ≤ 3 → P4: add to product backlog
```

---

## 18. Defect Metrics and Trends

### 18.1 Defect Density Tracking

```
Defect Density = Number of defects / KLOC (1000 lines of code changed)

Typical target: < 0.5 defects/KLOC for production-quality ADAS SW

Track per sprint:
  Sprint   | KLOC_changed | Defects_found | Density | Trend
  ---------|--------------|---------------|---------|--------
  Sprint 1 | 12.4         | 18            | 1.45    | baseline
  Sprint 2 | 8.1          | 10            | 1.23    | ↓ improving
  Sprint 3 | 15.2         | 19            | 1.25    | → stable
  Sprint 4 | 9.8          | 6             | 0.61    | ↓ improving
```

### 18.2 Defect Age Tracking

```
Defect Age = Date CLOSED - Date OPENED (days)

Target: P1 ≤ 3 days; P2 ≤ 10 days; P3 ≤ 30 days

If P2 defect is open > 14 days without progress → escalate to PM
If P1 defect is open > 2 days → escalate to program manager daily

Track in JIRA dashboard:
  JQL for old P2 defects: project = ADAS AND priority = P2
                           AND status != Closed AND created < -14d
```

### 18.3 Defect Distribution Chart — What to Analyse

```
By Feature:
  Which feature has the most defects?
  → Focus testing and developer attention there

By Root Cause Category:
  SW Logic: 40%    Calibration: 30%    Test Setup: 20%    HW: 10%
  → High "Test Setup" % = test process improvement needed
  → High "Calibration" % = calibration governance process gap

By Severity:
  S1: 5%    S2: 30%    S3: 55%    S4: 10%
  → S1 > 5% = safety process concern; escalate

By Detection Phase:
  Unit test: 10%    Integration test: 45%    System test: 35%    Field: 10%
  → High field detection % = test coverage gap; add more test cases
  → Target: 0% field detection for S1/S2 defects
```

### 18.4 JIRA Dashboard Configuration

```
Create a JIRA dashboard with these gadgets:

1. "Defect Summary" — Pie chart
   JQL: project = ADAS AND issuetype = Bug AND status != Closed
   Group by: Priority

2. "Open P1/P2" — Issue List
   JQL: project = ADAS AND priority in (P1, P2) AND status != Closed
   Columns: Summary, Assignee, Created, Days open

3. "Defects by Feature" — Bar chart
   JQL: project = ADAS AND issuetype = Bug
   Group by: Component

4. "Fix Verification Queue" — Issue List
   JQL: project = ADAS AND status = "Ready for Verification"
   Columns: Summary, Fix Version, Assignee(test)

5. "Weekly Trend" — Created vs Resolved chart
   Ascending trend of "resolved" = good (team is fixing faster than finding)
   Descending trend of "resolved" = risk (backlog growing)
```
