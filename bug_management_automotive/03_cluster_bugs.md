# Instrument Cluster — Bug Reproduction, Reporting, Resolving & Diagnostics

> **Domain**: Instrument Cluster ECU (IC / KOMBI)
> **Sub-systems**: Speedometer · Tachometer · Tell-tales (warning lamps) · Fuel gauge · UI renderer · CAN signal decoding · NVM · UDS diagnostics
> **Tools**: CANoe · CANalyzer · dSPACE HIL · CAPL · Lauterbach Trace32 · UDS ISO 14229

---

## 1. Bug Categories in Instrument Cluster

| Category | Description | Example |
|---------|-------------|---------|
| Wrong Gauge Value | Gauge shows incorrect physical value | Speedometer reads 2× actual speed |
| Tell-tale Wrong State | Warning lamp ON when should be OFF or vice versa | CEL flickering; ABS lamp missing |
| Boot / Startup Failure | Cluster does not initialize correctly after power-on | Black screen; stuck at OEM logo after OTA |
| Gauge Sweep Missing | Power-on sweep animation absent or incomplete | Speedometer does not sweep to max on ignition ON |
| CAN Signal Loss / Timeout | Cluster not reacting to missing CAN messages | Speed stays at 0 when CAN bus off |
| NVM Corruption | Stored data (odometer, calibration) lost or wrong | Odometer resets to 0 after battery disconnect |
| Pixel / Rendering Error | Display pixels stuck, wrong color, wrong font | White horizontal line across screen; wrong icon |
| DTC Handling Bug | Cluster does not display/clear warning for DTC correctly | MIL ON but no UDS DTC stored |
| Brightness / Theme Error | Incorrect brightness adaptation or theme switching | Day mode active at night; display too dim |
| CAN Arbitration Bug | Two nodes sending same message ID causing data corruption | Speedometer oscillating between 0 and real speed |

---

## 2. Bug Scenario 1 — Speedometer Shows Double the Actual Speed

### Bug Description
**Title:** Speedometer displays exactly 2× actual vehicle speed (e.g., vehicle at 60 km/h → gauge shows 120 km/h)  
**Severity:** P1 — Safety critical; false speed information  
**Reported by:** Test driver during validation of SW v3.1 integration  
**Frequency:** 100% reproducible upon first drive  

### Reproduction Steps
```
Environment:
  Vehicle: OEM Sedan Platform A
  Cluster SW: v3.1.0 (just updated from v3.0.5)
  CAN bus: Powertrain CAN, 500 kbit/s

Steps:
  1. Start vehicle; wait for cluster to fully boot
  2. Drive at known constant speed (GPS verified: 60 km/h)
  3. Observe cluster speedometer
  4. Result: Speedometer needle points to 120 km/h
  5. At 80 km/h → gauge shows 160 km/h
  6. GPS speed vs display speed ratio = exactly 2.0
  → Factor-of-2 error suggests DBC signal scaling regression
```

### CANoe Signal Analysis
```capl
// CAPL script: Monitor VehicleSpeed CAN signal and compute displayed vs raw
variables {
  message 0x200 msg_VehicleSpeed;   // Powertrain CAN message
  float rawSignalValue;
  float scaledValue_v30;
  float scaledValue_v31;
}

on message 0x200 {
  // Extract raw 16-bit signal from bytes 0–1 (big-endian, unsigned)
  rawSignalValue = (this.byte(0) << 8) | this.byte(1);
  
  // DBC v3.0 scaling: factor=0.01, offset=0 → speed_kmh = raw * 0.01
  scaledValue_v30 = rawSignalValue * 0.01;
  
  // DBC v3.1 INCORRECT scaling: factor=0.02, offset=0 → 2× the actual value
  scaledValue_v31 = rawSignalValue * 0.02;
  
  write("Raw: %.0f  |  v3.0 decode: %.1f km/h  |  v3.1 decode: %.1f km/h",
        rawSignalValue, scaledValue_v30, scaledValue_v31);
}
```

### CANoe Trace Output
```
Time(s)  ID     DLC  Data                Description
0.001    0x200   8   46 58 00 00 ...     VehicleSpeed raw=0x4658=18008
  v3.0 decode: 180.08 km/h   [WRONG — GPS 90 km/h → factor 0.01 also wrong here]

// Corrected: this vehicle uses factor=0.01, offset=0
// At 90 km/h GPS:
//   Expected raw = 90 / 0.01 = 9000 = 0x2328
//   Actual raw = 0x2328 ✓   Using v3.0: 0x2328 × 0.01 = 90 km/h ✓
//                           Using v3.1: 0x2328 × 0.02 = 180 km/h ✗ (2×)
```

### DBC File Root Cause
```
# DBC v3.0 (correct):
SG_ VehicleSpeed_kmh : 0|16@1+ (0.01,0) [0|327.67] "km/h" Vector__XXX

# DBC v3.1 (WRONG — accidentally changed during signal database refactor):
SG_ VehicleSpeed_kmh : 0|16@1+ (0.02,0) [0|655.35] "km/h" Vector__XXX

Root Cause: During DBC v3.1 refactor task (JIRA KOMBI-442), an engineer updated
the signal factor from 0.01 to 0.02. The intent was to double the max range for
a different signal (OdometerHighRes) on a neighboring line — wrong line was edited.
The incorrect DBC was committed, reviewed, and approved without signal-level validation.
```

### Fix
```
1. Revert VehicleSpeed_kmh factor to 0.01 in DBC v3.1
2. Recompile cluster SW with corrected DBC
3. Add automated DBC signal regression check:
   - Script compares each signal factor/offset between DBC versions
   - Fails CI pipeline if safety-critical signal (speed, fuel, temp) factor changes by > 5%
   - Required human approval for any such change even if within threshold
```

### Verification
```capl
// Post-fix verification: drive at 5 known speeds (GPS reference)
// 20, 40, 60, 80, 100 km/h
// Acceptance: |cluster_display – GPS_speed| ≤ 1.0 km/h at each point
```

### Bug Report (JIRA)
```
Summary: [Cluster][Speedometer] 2× speed shown — DBC v3.1 signal factor regression

Severity: P1 — Safety Critical
Root Cause: DBC VehicleSpeed_kmh factor changed from 0.01 to 0.02 in v3.1 refactor
Fix: Revert factor; add DBC regression diff script to CI gate
Verification: 5-point speed sweep test pass required before release
```

### Recurring Bug Pattern
```
This class of bug (wrong gauge value due to DBC factor/offset) can recur whenever:
  - A new DBC version is integrated
  - A new CAN signal database tool is used
  - Platform sharing introdu  ces a different DBC for a different variant

Detection checklist on EVERY DBC version change:
  □ Run DBC diff: compare factor, offset, startBit, length for every signal
  □ Flag: any safety signal (speed, fuel level, engine temp) change → manual review
  □ Execute automated gauge accuracy test (simulated CAN input, optical readout check)
  □ Never skip cluster signal validation even for "minor" DBC updates

If speedometer error recurs after fix:
  Step 1: Identify current DBC version in software build
  Step 2: diff against last known-good DBC
  Step 3: Focus on VehicleSpeed signal attributes: factor, offset, startBit, byteOrder
  Step 4: Rerun CAPL log above with actual bus capture to confirm raw vs displayed
```

---

## 3. Bug Scenario 2 — Check Engine Tell-tale Flickers ON/OFF

### Bug Description
**Title:** MIL (Malfunction Indicator Lamp / Check Engine Light) flickers ON for ~500 ms then OFF repeatedly at 1–2 Hz  
**Severity:** P2 — Customer-visible false alarm; may cause dealer visits  
**Frequency:** Reproducible when two calibration ECUs present on the same CAN bus (development lab condition)

### Reproduction Steps
```
Environment:
  CAN bus: Body CAN, 250 kbit/s
  ECUs on bus: Cluster, ECM (Engine Control Module), CAL-Tool ECU (development calibration ECU)

Steps:
  1. Start vehicle in lab with calibration ECU (ETAS INCA) connected
  2. Power ON ignition
  3. Observe cluster: MIL (amber CEL icon) flickers at ~1.5 Hz
  4. Disconnect calibration ECU from CAN
  5. MIL immediately settles to proper state (OFF, no fault)
  → Calibration ECU causes conflict
```

### CANoe CAN Bus Capture Analysis
```capl
// CAPL: detect message ID collision (two nodes sending same ID)
variables {
  dword lastSenderId_0x500;
  int   frameRxCount_0x500;
}

on message 0x500 {
  frameRxCount_0x500++;
  
  // Check source address byte (byte 7) or node identifier bit
  if (this.byte(7) != lastSenderId_0x500 && frameRxCount_0x500 > 1) {
    write("ID CONFLICT: CAN ID 0x500 sent by TWO different nodes!");
    write("  Previous node byte7=0x%02X | New node byte7=0x%02X",
          lastSenderId_0x500, this.byte(7));
  }
  lastSenderId_0x500 = this.byte(7);
}
```

### CAN Trace Finding
```
Time(ms)  ID    DLC  Data                       TX Node (Network symbol)
 0.000    0x500   8  00 00 00 00 00 00 00 AA   ECM          → MIL_Request=0 (OFF)
 0.667    0x500   8  00 00 02 00 00 00 00 CC   CAL_ECU      → MIL_Request=1 (ON)
 1.334    0x500   8  00 00 00 00 00 00 00 AA   ECM          → MIL_Request=0 (OFF)
 2.001    0x500   8  00 00 02 00 00 00 00 CC   CAL_ECU      → MIL_Request=1 (ON)

Analysis:
  - CAN ID 0x500 = LampControl_Status message (defined in DBC)
  - ECM sends it every 667 ms (MIL_Request=0, correct)
  - CAL_ECU (ETAS INCA calibration tool) ALSO sends ID 0x500 every 667 ms
    with a stale/test value that has MIL_Request=1
  - Cluster receives both → bouncing between ON and OFF at alternating cycle
```

### Root Cause
Using ETAS INCA calibration tool with an outdated configuration file (`inca_config_v1.2.a2l`) that includes a TX segment for CAN ID 0x500. In production, only the ECM should send 0x500. The calibration ECU sends a stale MIL value left in the INCA workspace from a previous testing session.

### Fix
1. **Immediate**: Remove TX access to CAN ID 0x500 from calibration tool INCA configuration.
2. **Process fix**: INCA A2L configurations must be reviewed before connecting to any vehicle CAN bus — prohibition on enabling TX for body control messages.
3. **Cluster-side protection**: Implement AUTOSAR ComSignalGroup sender constraint — cluster accepts MIL_Request from ECM Node ID only (node address check using NM node identifier).

### Recurring Bug Pattern
```
Tell-tale flickering recur after fix:

Scenario A — New calibration tool/ECU on same bus:
  Immediate check: disconnect any external tool from Body CAN; observe if flicker stops
  If YES: new tool has conflicting TX config → review its A2L/ARXML transmit map
  
Scenario B — Flicker occurs even with no external tools:
  Check for new ECU added to Body CAN in latest build (did DBC add a new node?)
  Run CAPL ID collision script above → identify second transmitter for 0x500
  Compare CAN Matrix (Excel/ARXML) with actual bus capture for all nodes transmitting 0x500
  
Scenario C — Intermittent flicker (not periodic):
  Could be CAN bus off recovery → brief burst of stale frames
  Check: Bus Error Counter increasing? (CANoe → Statistics → BusErrorCount)
  Could be EMC interference on Body CAN causing dominant bit stuffing errors
  → EMC-hardened shielded cable test; add bus termination check
```

---

## 4. Bug Scenario 3 — Cluster Does Not Boot After OTA Update

### Bug Description
**Title:** Instrument cluster shows OEM logo then goes black — ECU never completes boot  
**Severity:** P1 — Safety critical; all telltales and gauges absent  
**Frequency:** Reproducible after applying OTA v5.0 to v5.1 on specific hardware variant (HW variant ID=0x03)

### Reproduction Steps
```
Steps:
  1. Cluster on v5.0 (confirmed by UDS 0x22 F195 read)
  2. Apply OTA package cluster_v5.1.pkg via telematics OTA channel
  3. Cluster reboots post-update
  4. OEM logo visible ~2 s, then black screen
  5. CAN: no NM frames from Cluster ECU after t=3 s
  6. UDS: no response to 0x3E TesterPresent or functional addressing
```

### Diagnostics — UDS Diagnostic Pre/Post OTA
```capl
// Before OTA: Read SW version
diagRequest ECU_Cluster.ReadDataByIdentifier_F195 swVersionReq;
on diagResponse ECU_Cluster.ReadDataByIdentifier_F195 {
  byte version[8];
  diagGetParameter(this, "DataRecord", version, elcount(version));
  write("Cluster SW Version: %02X %02X %02X %02X %02X",
        version[0], version[1], version[2], version[3], version[4]);
  // Output: 05 00 00 00 03  → v5.0.0.0 HW=0x03
}

// After OTA attempt: Try to read SW version
// If no response after 5 retries → ECU boot failure confirmed
on timer tester_ping {
  static int retryCount;
  retryCount++;
  if (retryCount > 5) {
    write("ERROR: Cluster not responding after OTA — BOOT FAILURE");
    cancelTimer(tester_ping);
  }
  diagSendRequest(swVersionReq);
  setTimer(tester_ping, 1000);
}
```

### Lauterbach Trace32 Debug (JTAG)
```
Connect Trace32 to cluster JTAG debug port

Command:
  HALT   (stop CPU at failure point)
  Register.View
  
Output at failure:
  PC = 0x08014A00  (inside NVM_Init() function)
  LR = 0x08014992  (called from ECU_Init → NVM_Init)
  
Memory view:
  0x20001000: NVM_CRC_STORED   = 0xA3C2  
  0x20001002: NVM_CRC_COMPUTED = 0x0000  (computed CRC = 0 → NVM data all 0xFF after erase)
  
Source:
  if (NVM_CRC_STORED != NVM_CRC_COMPUTED) {
    NVM_SetDefaultValues();   
    while(1);  // ← CPU stuck in infinite loop — "error halt" behaviour (wrong implementation)
  }
```

### Root Cause
OTA v5.1 changed the NVM (Non-Volatile Memory) layout — new calibration fields were added, shifting the start address of existing data by 16 bytes. The OTA process erased NVM before flashing the new application. After flashing, NVM_Init() computes a CRC over the new (empty) NVM area and finds it does not match the stored CRC (which was written by v5.0 to a now-different address). The code incorrectly enters a `while(1)` halt instead of gracefully applying factory defaults.

### Fix
```c
// Before (wrong — hard halt on NVM CRC failure):
if (NVM_CRC_STORED != NVM_CRC_COMPUTED) {
    NVM_SetDefaultValues();
    while(1);  // system halt
}

// After (correct — apply defaults and continue):
if (NVM_CRC_STORED != NVM_CRC_COMPUTED) {
    NVM_SetDefaultValues();    // reset to factory defaults
    NVM_WriteAll();            // write defaults to NVM immediately
    ECU_LOG("NVM CRC fail: defaults applied, continuing boot");
    // Do NOT halt — graceful recovery
}
```

### Recurring Pattern Protocol
```
Cluster boot failure can recur after ANY future OTA that changes NVM layout:

Prevention:
  □ OTA package MUST include NVM migration script (v5.0→v5.1 field mapping)
  □ NVM_Init() must NEVER call while(1) on CRC failure in production code
  □ NVM layout changes require full OTA regression test on ALL hardware variants
  
If cluster black screen occurs after any future OTA:
  Step 1: UDS 0x27 security access → 0x31 routine 0xFF00 (NVM reset routine)
          If cluster responds → trigger factory NVM reset → cluster re-boots
  Step 2: If no UDS response → JTAG Trace32 → confirm stuck in NVM_Init
  Step 3: Identify: was NVM layout changed in this update? (check release notes)
  Step 4: Force-flash full firmware via bootloader (UDS 0x34/0x36/0x37 sequence)
  
Remote recovery path:
  If vehicle has operational TCU:
    TCU can deliver "NVM factory defaults" special OTA package
    This clears NVM and re-applies defaults without erasing application code
    Cluster re-boots with factory NVM → boot succeeds → then normal OTA re-applied
```

---

## 5. Bug Scenario 4 — Low Fuel Warning Missing at 10 L

### Bug Description
**Title:** Low fuel tell-tale (amber fuel pump icon) does not illuminate when fuel level reaches 10 L (threshold)  
**Severity:** P2 — Feature defect; customer may run out of fuel  
**Frequency:** Consistent in lab; 3 field complaints

### Steps
```
Steps:
  1. Set fuel level to 11 L via HIL fuel simulator
  2. Slowly reduce simulated fuel level: 11 → 10.5 → 10.0 → 9.5 L
  3. Observe: low fuel telltale ABSENT at 10.0 L and 9.5 L
  4. Telltale illuminates only at 6.5 L
  5. Expected: illuminate at ≤ 10.0 L
```

### CANoe / CAPL — Fuel Level Signal Analysis
```capl
// CAPL: decode and monitor fuel signal
on message 0x180 {  // Body CAN FuelLevel message
  float raw = (this.byte(0) << 2) | (this.byte(1) >> 6);  // 10-bit signal [0..1023]
  float fuel_liters = raw * 0.05;   // per DBC: factor=0.05, offset=0, unit=L
  
  if (fuel_liters <= 10.0) {
    write("WARN: Fuel ≤ 10L (%.1f L) — Low fuel telltale SHOULD be ON", fuel_liters);
  }
  
  write("FuelLevel: raw=%d  decoded=%.2f L", (int)raw, fuel_liters);
}

// Output observed:
// FuelLevel: raw=200  decoded=10.00 L  (SHOULD trigger: no trigger seen)
// FuelLevel: raw=128  decoded=6.40 L   (trigger seen here)

// Diagnosis: Cluster threshold comparison uses integer math:
// int comparison: if (fuel_raw <= 128) → trigger
// Expected: if (fuel_raw <= 200) → trigger (10.0 L / 0.05 = 200)
// Bug: threshold value in NVM was hardcoded as 128 during calibration (=6.4 L)
```

### Root Cause
Cluster NVM calibration data block `NVM_LowFuelThreshold_raw` was written as 0x80 (128) instead of 0xC8 (200) during ECU calibration at end-of-line. This is a calibration data entry error, not a software bug.

### Fix
```
EOL calibration tool: set NVM_LowFuelThreshold_raw = 200 (0xC8) 
Equivalent to: 200 × 0.05 = 10.0 L ✓

For already-shipped ECUs:
  UDS 0x2E — WriteDataByIdentifier with DID 0xF190 (LowFuelThreshold)
  Send: 0x2E F1 90 00 C8  → writes 200 as threshold
  
Verification: Step fuel from 11 → 9 L via CAN; confirm telltale at exactly 10 L transition
```

---

## 6. Cluster Diagnostic Commands Reference

### UDS Commands for Cluster ECU

| Function | UDS Service | Example |
|----------|------------|---------|
| Read SW version | 0x22 F195 | `22 F1 95` → returns version string |
| Read HW variant | 0x22 F191 | `22 F1 91` → returns HW ID |
| Read active DTCs | 0x19 02 09 | Returns all confirmed emission DTCs |
| Read all DTCs | 0x19 02 FF | All status masks |
| Clear DTCs | 0x14 FF FF FF | Clears all stored DTCs |
| ECU reset (soft) | 0x11 01 | Software reset |
| ECU reset (hard) | 0x11 03 | Hardware (key-off simulation) reset |
| Write threshold | 0x2E XXXX | Write calibration DID |
| Request download | 0x34 | Begin flash sequence |

### CAPL Template: Cluster CAN Signal Monitor
```capl
variables {
  msTimer tPollTimer;
}

on start {
  setTimer(tPollTimer, 100);  // poll every 100 ms
}

on timer tPollTimer {
  setTimer(tPollTimer, 100);
  output(msg_poll);  // trigger display refresh
}

on message 0x200 { /* VehicleSpeed — see Scenario 1 */ }
on message 0x180 { /* FuelLevel — see Scenario 4 */ }
on message 0x500 { /* LampControl_Status — see Scenario 2 */ }
```

### Performance Reference

| Parameter | Target | Fail Threshold |
|-----------|--------|---------------|
| Boot time (ign-ON to gauge sweep done) | ≤ 4 s | > 8 s |
| CAN signal → display update latency | ≤ 100 ms | > 300 ms |
| Tell-tale activation latency (DTC set → lamp ON) | ≤ 500 ms | > 2 s |
| Gauge accuracy (speed) | ±1 km/h | > ±3 km/h |
| Odometer accuracy | ±0.5% | > ±1% |
| NVM write time (key-off) | ≤ 200 ms | > 500 ms |
