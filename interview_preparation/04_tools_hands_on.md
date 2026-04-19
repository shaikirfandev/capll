# Tools & Hands-On Scenarios — What Interviewers Will Ask You to Demonstrate

> Many interviews include a practical round: "Show me how you would do X in CANoe" or
> "Walk me through a CAPL script". This file prepares you for those scenarios.

---

## 1. CANoe — Practical Scenarios

### Scenario 1: "Show me how you would monitor CAN traffic and find a specific signal"

**Your walkthrough:**
```
Step 1: Open CANoe → Load the DBC file for the project
  "I start by loading the CAN database (.dbc file) so CANoe can decode raw CAN
   frames into meaningful signal names and values."

Step 2: Open Trace window → Start measurement
  "The Trace window shows every CAN frame on the bus in real-time —
   ID, DLC, data bytes, timestamp, and cycle time."

Step 3: Filter for the specific message
  "If I'm looking for VehicleSpeed, I filter the trace by message ID — say 0x200.
   I can also use the Graphics window to plot the signal value over time."

Step 4: Add signal to Graphics window
  "I drag VehicleSpeed_kmh from the database to the Graphics panel.
   Now I can see the real-time value as a graph — useful for spotting sudden changes,
   glitches, or missing frames."

Step 5: Check cycle time
  "In the Statistics window, I verify the message cycle time. If VehicleSpeed
   should arrive every 20ms and I see 40ms gaps, that indicates a timeout issue."
```

### Scenario 2: "How would you simulate a CAN bus-off fault?"

**Your walkthrough:**
```
Method 1: Using CANoe Fault Injection (IG block)
  "I use the Interaction Generator (IG) to inject bus errors:
   - Set up a disturbance node in the Simulation Setup
   - Configure it to inject dominant bits during the CRC field
   - This forces Error Frames → TEC increments → Bus-Off when TEC > 255"

Method 2: Using CAPL + CANoe hardware (VN-series)
  "Using CANoe's fault injection panel:
   1. Go to Simulation Setup → Right-click CAN channel → Add Disturbance
   2. Set: 'Corrupt CRC of messages with ID=0x200'
   3. Start measurement → observe Error Frames accumulating
   4. When TEC > 255 → node goes Bus-Off"

What I verify after bus-off:
  1. Other ECUs log a timeout DTC for the missing messages
  2. The bus-off node recovers within spec time (≤ 1 second typically)
  3. After recovery, the node resumes normal transmission
  4. No data corruption on resumed messages
```

### Scenario 3: "How do you use UDS diagnostics in CANoe?"

**Your walkthrough:**
```
Step 1: Load diagnostic configuration
  "I load the ODX/PDX diagnostic database into CANoe → this maps UDS services
   to human-readable names (ReadDTCInformation, SecurityAccess, etc.)"

Step 2: Open Diagnostic Console
  "In the Diagnostic Console, I can:
   - Send any UDS service with click (or type raw hex)
   - See response decoded: positive response or NRC with meaning"

Step 3: Example — Read DTCs
  "I select ReadDTCInformation → subFunction 0x02 → statusMask 0xFF
   → Send. The response shows all stored DTCs with status bytes."

Step 4: Example — Security Access + Write
  "For protected operations:
   1. Switch to Extended Session (0x10 03) → green response ✓
   2. SecurityAccess → RequestSeed → I get 4-byte seed
   3. I enter the computed key → Send → Access granted
   4. Now I can WriteDataByIdentifier (0x2E) with the calibration value"

If asked to automate: "I write this in CAPL using diagRequest/diagResponse handlers
so it runs automatically without manual clicks."
```

---

## 2. CAPL — Code Walkthrough Scenarios

### Scenario 4: "Write a CAPL script to check if VehicleSpeed is within valid range"

```capl
/*
 * Interview scenario: Signal range validation
 * Checks VehicleSpeed_kmh stays within 0–260 km/h
 * Logs failure if out of range
 */
variables {
  int testResult = 1;   // 1=PASS, 0=FAIL
  int sampleCount = 0;
  int failCount = 0;
}

on message 0x200 {    // VehicleSpeed message
  float speed;
  
  // Decode: 16-bit signal, bytes 0-1, factor=0.01, offset=0
  speed = ((this.byte(0) << 8) | this.byte(1)) * 0.01;
  sampleCount++;
  
  if (speed < 0.0 || speed > 260.0) {
    write("FAIL: VehicleSpeed = %.2f km/h — OUT OF RANGE [0..260]", speed);
    testResult = 0;
    failCount++;
  }
}

on stopMeasurement {
  write("=== Test Result ===");
  write("Samples: %d | Failures: %d | Result: %s",
        sampleCount, failCount, testResult ? "PASS" : "FAIL");
}
```

**How to explain it:**
"This script monitors every VehicleSpeed message on CAN ID 0x200. It decodes the raw bytes using the DBC factor of 0.01 and checks if the value is within the valid range of 0 to 260 km/h. If any sample goes out of range, it logs a failure. At the end of the measurement, it prints a summary."

---

### Scenario 5: "Write a CAPL script to simulate a CAN message timeout"

```capl
/*
 * Interview scenario: Timeout injection
 * Sends EngineRPM normally for 10s, then STOPS to simulate timeout
 * Verifies: receiving ECU sets default value and logs DTC
 */
variables {
  message 0x180 msg_EngineRPM;
  msTimer tSendCycle;
  msTimer tStopAfter;
  int sending = 1;
}

on start {
  // Normal: send EngineRPM every 10ms
  msg_EngineRPM.dlc = 8;
  msg_EngineRPM.byte(0) = 0x1F;   // RPM raw = 0x1F40 = 8000 → 800 RPM (factor 0.1)
  msg_EngineRPM.byte(1) = 0x40;
  setTimer(tSendCycle, 10);
  setTimer(tStopAfter, 10000);    // Stop after 10 seconds
  write("Phase 1: Sending EngineRPM every 10ms...");
}

on timer tSendCycle {
  if (sending) {
    output(msg_EngineRPM);
  }
  setTimer(tSendCycle, 10);
}

on timer tStopAfter {
  sending = 0;
  write("Phase 2: TIMEOUT — stopped sending EngineRPM. Monitoring ECU reaction...");
  // Now verify: receiving ECU should detect timeout within 50ms
  // and set RPM to default value (typically 0 or 0xFFFF)
}
```

---

### Scenario 6: "Write a CAPL script for UDS DTC read automation"

```capl
/*
 * Automated DTC reader
 * 1. Enter Extended Session
 * 2. Read all confirmed DTCs
 * 3. Print each DTC code and status
 */
variables {
  byte dtcData[256];
}

on start {
  // Step 1: Switch to Extended Session
  diagRequest ECU.DiagnosticSessionControl_ExtendedDiagnosticSession req;
  diagSendRequest(req);
}

on diagResponse ECU.DiagnosticSessionControl_ExtendedDiagnosticSession {
  if (diagGetLastResponseCode(this) < 0) {
    write("Extended session active — reading DTCs...");
    
    // Step 2: Read confirmed DTCs
    diagRequest ECU.ReadDTCInformation_reportDTCByStatusMask dtcReq;
    diagSetParameter(dtcReq, "DTCStatusMask", 0x08);  // confirmed
    diagSendRequest(dtcReq);
  } else {
    write("Session switch FAILED: NRC=0x%02X", diagGetLastResponseCode(this));
  }
}

on diagResponse ECU.ReadDTCInformation_reportDTCByStatusMask {
  int len, numDTCs, i;
  
  len = diagGetParameterRaw(this, "DTCAndStatusRecord", dtcData, 256);
  numDTCs = len / 4;
  
  write("=== %d Confirmed DTC(s) ===", numDTCs);
  for (i = 0; i < numDTCs; i++) {
    write("  DTC: %02X%02X%02X | Status: 0x%02X",
          dtcData[i*4], dtcData[i*4+1], dtcData[i*4+2], dtcData[i*4+3]);
  }
}
```

---

## 3. dSPACE HIL + CANoe — Interview Walkthrough

### Scenario 7: "Explain how you set up a HIL test for ADAS"

**Your walkthrough:**
```
"The HIL setup at BYD consisted of:

Hardware:
  - dSPACE SCALEXIO real-time processor
  - VT Studio for signal routing and I/O configuration
  - ADAS ECU connected via CAN and Ethernet interfaces
  - Vector VN5640 interface card — bridges dSPACE CAN channels to CANoe

Setup steps:
  1. Load the ADAS ECU plant model (Simulink model compiled for dSPACE)
  2. Map ECU CAN inputs to dSPACE CAN channels (e.g., RadarObject → CAN1, CameraLane → CAN2)
  3. Configure sensor simulation: inject radar targets with distance, velocity, RCS
  4. Configure vehicle model: speed, yaw rate, steering angle
  5. Connect CANoe to the same CAN bus via VN interface — CANoe monitors all traffic in real-time

Test execution:
  1. Define driving scenario in dSPACE (e.g., 'follow lead vehicle at 80 km/h, 40m gap')
  2. Start real-time execution
  3. Inject target cut-in at 20m → verify ACC braking response
  4. Log all CAN signals (input + output) for post-test analysis

Result analysis:
  - Was ACC braking within spec? (deceleration ≤ 4.0 m/s²)
  - Was the response time < 500ms?
  - Were any DTCs logged unexpectedly?"
```

---

### Scenario 7b: "How exactly do you use CANoe alongside dSPACE HIL?"

**Your walkthrough — CANoe role in HIL:**

```
"CANoe runs in parallel with dSPACE during HIL testing. dSPACE handles the real-time
plant model (vehicle physics, sensor simulation), while CANoe handles:

  1. CAN bus monitoring — real-time trace of all ECU messages
  2. CAPL-based signal injection — supplement or override dSPACE signals
  3. Diagnostic console — read/clear DTCs without stopping the HIL run
  4. Logging — .blf file capturing every frame for post-test analysis
  5. Pass/fail evaluation — CAPL scripts assert expected signal values
  6. Fault injection — stop specific messages to test ECU error handling

The two tools connect via a shared CAN bus — dSPACE writes sensor data,
ECU responds on the bus, CANoe reads everything."
```

**Step-by-step CANoe setup for ADAS HIL:**

```
Step 1: Hardware connection
  CANoe (VN5640 interface) → connected to same CAN channel as ECU and dSPACE
  Channel assignment in CANoe: CAN 1 = ADAS bus (250kbps or 500kbps)

Step 2: Load DBC file
  File → Databases → Add → select project .dbc
  Now all signals on the ADAS bus are named and decoded in the Trace window

Step 3: Configure Trace window
  Filter: show only relevant message IDs (e.g., 0x300 Radar, 0x320 Camera, 0x500 ACC output)
  Columns: ID, Name, Data (decoded), Cycle time, DLC

Step 4: Configure Graphics window
  Add signals:
    - RadarTarget_Distance   (dSPACE output → ECU input)
    - VehicleSpeed           (dSPACE output → ECU input)
    - ACC_BrakeRequest_mbar  (ECU output — what we verify)
    - LKA_TorqueRequest_Nm   (ECU output — what we verify)
    - AEB_Active             (ECU output — critical safety signal)
  Set Y-axis limits per signal for clear visualisation

Step 5: Load CAPL evaluation script
  Simulation Setup → Add CAPL node → assign validation script
  The script monitors ECU outputs and logs PASS/FAIL automatically

Step 6: Configure Logging
  Measurement → Logging → New configuration
  File format: .blf (Binary Logging Format — all channels)
  Trigger: start on measurement start, split file every 500MB
  Naming: ADAS_HIL_<feature>_<date>_<run>.blf

Step 7: Open Diagnostic Console
  Load ODX/PDX file into CANoe diagnostic config
  During test: use Diagnostic Console to:
    - Read active DTCs mid-run (0x19 01)
    - Clear DTCs between test cases (0x14 FF FF FF)
    - Read ECU SW version (0x22 F189/F195)

Step 8: Start measurement
  Press F9 (Start) → CANoe begins logging
  dSPACE scenario runs in parallel
  Watch Graphics window for ECU response curves
  CAPL script logs PASS/FAIL in Write window
```

**CAPL Script — HIL ADAS Evaluation (used alongside dSPACE)**

```capl
/*
 * HIL ADAS Evaluation Script
 * Runs alongside dSPACE — monitors ECU outputs and logs PASS/FAIL
 * Covers: ACC braking latency, LKA torque response, AEB trigger
 */
variables {
  // ── ACC evaluation ──────────────────────────────────────────────
  dword tDistanceCrossed = 0;     // when radar distance < 2000cm
  int   aebExpected      = 0;
  int   aebVerified      = 0;

  // ── LKA evaluation ──────────────────────────────────────────────
  dword tLaneDriftStart  = 0;
  int   lkaTorqueSeen    = 0;

  // ── Counters ─────────────────────────────────────────────────────
  int   passTotal = 0;
  int   failTotal = 0;
}

/* ── Monitor radar distance (dSPACE injects 0x300) ── */
on message 0x300 {
  int dist = (this.byte(0) << 8) | this.byte(1);   // cm

  // threshold: < 2000cm (20m) → ACC should decelerate
  if (dist < 2000 && dist > 0 && tDistanceCrossed == 0) {
    tDistanceCrossed = timeNow() / 100000;          // ms
    write("[HIL-ACC] Distance threshold crossed at %d ms", tDistanceCrossed);
  }

  // threshold: < 600cm (6m) → AEB should fire
  if (dist < 600 && dist > 0 && !aebExpected) {
    aebExpected = 1;
    write("[HIL-AEB] Critical zone entered (%d cm) — AEB expected within 150ms", dist);
  }
}

/* ── Monitor ACC brake output (ECU writes 0x501) ── */
on message 0x501 {
  int brake = (this.byte(0) << 8) | this.byte(1);   // mbar

  if (tDistanceCrossed > 0 && brake > 500) {
    dword latency = (timeNow() / 100000) - tDistanceCrossed;
    if (latency <= 500) {
      write("[HIL-ACC] PASS: BrakeRequest = %d mbar | latency = %d ms ✓", brake, latency);
      passTotal++;
    } else {
      write("[HIL-ACC] FAIL: BrakeRequest latency = %d ms > 500ms spec!", latency);
      failTotal++;
    }
    tDistanceCrossed = 0;   // reset for next event
  }
}

/* ── Monitor AEB activation (ECU writes 0x502 bit0) ── */
on message 0x502 {
  if ((this.byte(0) & 0x01) && aebExpected && !aebVerified) {
    write("[HIL-AEB] PASS: AEB activated ✓");
    aebVerified = 1;
    passTotal++;
  }
}

/* ── Monitor LKA lane data (dSPACE injects 0x320) ── */
on message 0x320 {
  int offset = (this.byte(0) << 8) | this.byte(1);   // mm, signed

  // signed 16-bit decode
  if (offset > 32767) offset -= 65536;

  if (offset < -150 && tLaneDriftStart == 0) {
    tLaneDriftStart = timeNow() / 100000;
    write("[HIL-LKA] Drift threshold (-150mm) crossed @ %d ms", tLaneDriftStart);
  }
}

/* ── Monitor LKA torque output (ECU writes 0x510) ── */
on message 0x510 {
  int torque = (this.byte(0) << 8) | this.byte(1);
  if (torque > 32767) torque -= 65536;   // signed

  if (tLaneDriftStart > 0 && torque > 20 && !lkaTorqueSeen) {
    dword latency = (timeNow() / 100000) - tLaneDriftStart;
    if (latency <= 100) {
      write("[HIL-LKA] PASS: Correction torque = %d (×0.1Nm) | latency = %d ms ✓",
            torque, latency);
      passTotal++;
    } else {
      write("[HIL-LKA] FAIL: LKA torque latency = %d ms > 100ms!", latency);
      failTotal++;
    }
    lkaTorqueSeen = 1;
  }
}

/* ── End of test summary ── */
on stopMeasurement {
  write("╔══════════════════════════════════════╗");
  write("║  HIL ADAS TEST SUMMARY               ║");
  write("║  PASS: %-3d  FAIL: %-3d               ║", passTotal, failTotal);
  write("║  RESULT: %-26s ║",
        (failTotal == 0) ? "OVERALL PASS ✓" : "OVERALL FAIL ✗ — review log");
  write("╚══════════════════════════════════════╝");
}
```

**CANoe windows to open during an ADAS HIL session:**

| Window | Purpose | Key setting |
|--------|---------|-------------|
| Trace | Real-time frame monitor | Filter: ADAS bus only; decoded signal names |
| Graphics | Signal waveform plot | Add: radar distance, brake pressure, torque request, AEB_Active |
| Write | CAPL PASS/FAIL log | Auto-scrolls during test — save after run |
| Statistics | Cycle time & bus load | Flag: messages missing their cycle time |
| Diagnostic Console | Live DTC read/clear | Load ODX; read 0x19 02 0F after each scenario |
| Data Replay | Replay vehicle CAN log on HIL | Compare HIL result vs real vehicle capture |

---

### Scenario 8: "How do you handle a test that passes on HIL but fails in vehicle?"

**Your answer:**
```
"This happens when the HIL model doesn't perfectly match real-world conditions. My approach:

1. Compare environments:
   - Does the HIL model include the exact sensor noise profile from the real sensor?
   - Is the CAN load realistic? (HIL might have less bus load than a real vehicle)
   - Is EMC noise simulated? (Real vehicle has electromagnetic interference)

2. Capture vehicle CAN log:
   - Record the exact CAN signals during the vehicle failure
   - Play back the vehicle CAN log on HIL → does it reproduce?
   - If YES: the ECU code can be debugged on HIL
   - If NO: the HIL model is missing something

3. Refine HIL model:
   - Add the missing condition (e.g., sensor noise, bus load, CAN error frames)
   - Re-run test on refined HIL model → verify it now fails → confirms we caught the gap

At BMW, I had this exact situation with ACC — radar target detection worked on HIL but failed 
in vehicle at specific angles. The issue was that the HIL model didn't simulate radar 
multipath reflections from road barriers."
```

---

## 4. ECU Flashing — Interview Walkthrough

### Scenario 9: "Walk me through how you flash an ECU"

**Your walkthrough:**
```
"I've flashed ECUs using three methods:

Method 1: UDS-based flashing via CANoe (ADAS, Cluster)
  - Sequence: 0x10 02 → 0x27 → 0x28 → 0x85 02 → 0x31 FF00 → 0x34 → 0x36... → 0x37 → 0x11
  - I load the hex file into CANoe's flash tool (vFlash or ODX-based flasher)
  - After flash: read back SW version (0x22 F195) to confirm

Method 2: USB flash (Infotainment HU)
  - Copy firmware image to USB stick
  - Insert into HU USB port → HU detects update package
  - Follow on-screen prompts → HU restarts with new SW

Method 3: ADB flash (Infotainment / Android-based HU)
  - Connect via USB → adb reboot bootloader → fastboot flash system system.img
  - Or: adb sideload update.zip
  - After flash: adb shell getprop ro.build.version.incremental → verify version

Post-flash checklist (all methods):
  □ Verify SW version matches expected
  □ Read DTCs — no critical DTCs after flash
  □ Basic functional check (smoke test)
  □ NVM integrity check — odometer, calibration data preserved"
```

---

## 5. Defect Reporting — JIRA Walkthrough

### Scenario 10: "How do you write a good bug report?"

**Your walkthrough:**
```
"A complete bug report contains:

Title: [Domain][Feature] Brief description (e.g., '[ADAS][ParkAssist] False obstacle 
       detection on metal bollard at 5 km/h')

Severity: P1 (blocker), P2 (major), P3 (minor), P4 (cosmetic)

Environment:
  - ECU SW version: v2.4.1
  - HW variant: 0x03
  - Tool: CANoe 16.0 SP2 + dSPACE SCALEXIO
  - DBC version: v3.1

Preconditions:
  - Vehicle in Park mode
  - Parking Assist feature enabled

Steps to Reproduce:
  1. Set vehicle speed to 5 km/h via CAN signal injection
  2. Place metal bollard target at 1.5m distance
  3. Observe parking warning
  4. Expected: No warning (bollard is not in parking path)
  5. Actual: Warning activates with distance = 1.5m displayed

Root Cause (if known): Material-type filter disabled below 15 km/h

Attachments:
  - CAN trace (.blf file)
  - Screenshot of CANoe Graphics showing signal values
  - CAPL log with signal decode

Linked Requirements: REQ-PARK-042 in DOORS

Key principles:
  1. Always include the EXACT steps — anyone should be able to reproduce
  2. Always attach CAN logs — developers need raw data
  3. Clearly separate Expected vs Actual behavior
  4. Mention if it's a regression (was it working in a previous version?)"
```

---

## Tool Proficiency Self-Assessment (Prepare for "Rate yourself" questions)

| Tool | Your Level | How to Describe |
|------|-----------|----------------|
| CANoe | 8/10 | "I use it daily — trace, graphics, diagnostic console, CAPL scripting, IG, simulation setup" |
| CANalyzer | 7/10 | "Used for monitoring and logging — less scripting than CANoe but comfortable" |
| CAPL | 8/10 | "Written 50+ scripts — signal validation, fault injection, UDS automation, report generation" |
| dSPACE | 7/10 | "Set up HIL scenarios, configured sensor models, ran real-time tests with VT Studio" |
| JIRA | 8/10 | "Full defect lifecycle — create, triage, track, close. Custom filters by sprint/component" |
| DOORS | 7/10 | "Requirement tracing, test case linking, traceability matrix generation" |
| ADB | 6/10 | "Basic usage — logcat, dumpsys, install, shell, flashing. Used for Infotainment HU testing" |
| Python | 5/10 | "Basic scripting — log parsing, test data generation. Currently improving" |
| UDS diagnostics | 8/10 | "All core services. Can diagnose using raw hex or CANoe diagnostic console" |

> **Tip**: Never say 10/10 for anything — it invites tough follow-up questions.
> Never say below 5/10 — for tools on your CV, show working proficiency.

---

## 6. CAPL Diagnostic Syntax — Deep Explanation

### "What does `on diagResponse ECU.ReadDTCInformation_reportDTCByStatusMask` mean?"

This is a common interview question when you write or explain Scenario 6. Break it down part by part:

```
on diagResponse   ECU   .   ReadDTCInformation_reportDTCByStatusMask
│                 │              │
│                 │              └─ Service name + subfunction name
│                 │                 (auto-generated from the diagnostic database)
│                 │
│                 └─ The ECU node name as configured in CANoe's
│                    diagnostic setup (ODX / .cdd file)
│
└─ CAPL predefined event keyword — fires when a diagnostic
   response frame is received from that ECU
```

| Part | Type | Where it comes from |
|------|------|---------------------|
| `on diagResponse` | CAPL predefined event keyword | Built into CAPL — fires when a diagnostic response arrives |
| `ECU` | Diagnostic node name | Defined in your CANoe diagnostic configuration (ODX/PDX or `.cdd` file) — the name you gave the ECU under test |
| `ReadDTCInformation_reportDTCByStatusMask` | Service + subfunction name | Auto-generated from the diagnostic database — `ReadDTCInformation` = UDS service `0x19`, `reportDTCByStatusMask` = subfunction `0x02` |

**How the name is constructed from UDS:**

```
UDS Service  0x19  →  ReadDTCInformation
Sub-function 0x02  →  reportDTCByStatusMask

Combined:  ReadDTCInformation_reportDTCByStatusMask
```

**If your ECU has a different name** (e.g., `EngineECU`), the exact same handler becomes:

```capl
on diagResponse EngineECU.ReadDTCInformation_reportDTCByStatusMask {
```

**Where to find these names in CANoe:**
> Open Diagnostic Console → expand the ECU node in the service tree → every service and subfunction shown there matches exactly the identifier you use in CAPL.

**More examples of the same pattern:**

```capl
on diagResponse ECU.DiagnosticSessionControl_defaultSession        // 0x10 01
on diagResponse ECU.DiagnosticSessionControl_extendedDiagnosticSession  // 0x10 03
on diagResponse ECU.SecurityAccess_requestSeed                     // 0x27 01
on diagResponse ECU.SecurityAccess_sendKey                         // 0x27 02
on diagResponse ECU.ReadDataByIdentifier                           // 0x22 (no subfunction)
on diagResponse ECU.WriteDataByIdentifier                          // 0x2E
on diagResponse ECU.RoutineControl_startRoutine                    // 0x31 01
on diagResponse ECU.RoutineControl_requestRoutineResults           // 0x31 03
on diagResponse ECU.ECUReset_hardReset                             // 0x11 01
```

**Key rule:** If a UDS service has subfunctions (like 0x19, 0x27, 0x31), the name is `ServiceName_subfunctionName`. If it has no subfunctions (like 0x22, 0x2E), it's just `ServiceName`.

---

### Alternative: Without ODX — Direct UDS Hex Codes (Raw CAN)

When no ODX/diagnostic database is loaded, you cannot use `diagRequest`/`diagResponse`. Instead, you manually construct UDS byte frames and send them as raw CAN messages on the physical CAN ID.

**How UDS over CAN works (ISO 15765-2 Single Frame):**

```
Byte 0: PCI (Protocol Control Info) — 0x0N where N = payload length
Byte 1: UDS Service ID
Byte 2+: Parameters / subfunction / data
```

**Example: Read all confirmed DTCs — raw UDS CAN frames**

```capl
/*
 * UDS Diagnostic WITHOUT ODX — direct hex codes
 * Target ECU physical request ID : 0x7E0
 * Target ECU physical response ID: 0x7E8
 *
 * Sequence:
 *   1. Enter Extended Diagnostic Session  → 0x10 03
 *   2. Read DTC by Status Mask            → 0x19 02 08
 *   3. Parse raw response bytes manually
 */

variables {
  message 0x7E0 udsReq;       // Physical request  CAN ID
  msTimer tWaitForResp;
  int step = 0;
}

/* ── Step 1: Start measurement → send Extended Session request ── */
on start {
  step = 1;

  udsReq.dlc = 8;
  udsReq.byte(0) = 0x02;   // PCI: Single Frame, 2 payload bytes
  udsReq.byte(1) = 0x10;   // Service ID: DiagnosticSessionControl
  udsReq.byte(2) = 0x03;   // SubFunction: extendedDiagnosticSession
  udsReq.byte(3) = 0x00;   // padding
  udsReq.byte(4) = 0x00;
  udsReq.byte(5) = 0x00;
  udsReq.byte(6) = 0x00;
  udsReq.byte(7) = 0x00;

  output(udsReq);
  write("[UDS TX] 0x7E0 → DiagnosticSessionControl extendedSession (0x10 03)");
  setTimer(tWaitForResp, 500);   // timeout guard
}

/* ── Receive all frames on the ECU response ID ── */
on message 0x7E8 {
  byte sid    = this.byte(1);   // Service ID in response = request SID + 0x40
  byte nrc    = this.byte(2);   // NRC if SID == 0x7F
  int  i, numDTCs;
  byte dtcHigh, dtcMid, dtcLow, status;

  /* ── Negative Response ── */
  if (sid == 0x7F) {
    write("[UDS RX] NEGATIVE RESPONSE — Request SID: 0x%02X  NRC: 0x%02X", nrc, this.byte(3));
    return;
  }

  /* ── Positive response: Extended Session (0x50 03) ── */
  if (sid == 0x50 && step == 1) {
    cancelTimer(tWaitForResp);
    write("[UDS RX] Extended Session active ✓");

    // Step 2: Send ReadDTCInformation — reportDTCByStatusMask
    step = 2;
    udsReq.byte(0) = 0x03;   // PCI: 3 payload bytes
    udsReq.byte(1) = 0x19;   // Service ID: ReadDTCInformation
    udsReq.byte(2) = 0x02;   // SubFunction: reportDTCByStatusMask
    udsReq.byte(3) = 0x08;   // StatusMask:  0x08 = confirmed DTC
    udsReq.byte(4) = 0x00;
    udsReq.byte(5) = 0x00;
    udsReq.byte(6) = 0x00;
    udsReq.byte(7) = 0x00;

    output(udsReq);
    write("[UDS TX] 0x7E0 → ReadDTCInformation reportDTCByStatusMask (0x19 02 08)");
    setTimer(tWaitForResp, 500);
  }

  /* ── Positive response: ReadDTCInformation (0x59 02) ── */
  if (sid == 0x59 && step == 2) {
    cancelTimer(tWaitForResp);

    // Byte 0 = PCI, Byte 1 = 0x59, Byte 2 = 0x02 (subfunction echo),
    // Byte 3 = DTCStatusAvailabilityMask
    // Byte 4 onwards: [DTC high][DTC mid][DTC low][Status] × N
    numDTCs = (this.dlc - 4) / 4;
    write("[UDS RX] ReadDTCInformation ✓ — %d confirmed DTC(s)", numDTCs);

    for (i = 0; i < numDTCs; i++) {
      dtcHigh = this.byte(4 + i*4);
      dtcMid  = this.byte(5 + i*4);
      dtcLow  = this.byte(6 + i*4);
      status  = this.byte(7 + i*4);
      write("  DTC[%d]: %02X %02X %02X  Status: 0x%02X", i+1, dtcHigh, dtcMid, dtcLow, status);
    }
  }
}

/* ── Timeout guard ── */
on timer tWaitForResp {
  write("[UDS] TIMEOUT — no response from ECU (step %d)", step);
}
```

---

### ODX Symbolic vs Raw UDS — Side-by-Side Comparison

| Aspect | ODX Symbolic (with database) | Raw UDS Hex (no database) |
|--------|------------------------------|---------------------------|
| **Requires** | ODX / PDX / `.cdd` file loaded in CANoe | No database needed |
| **Send request** | `diagRequest ECU.ReadDTCInformation_reportDTCByStatusMask` | `udsReq.byte(1) = 0x19; udsReq.byte(2) = 0x02; ...` |
| **Receive event** | `on diagResponse ECU.ReadDTCInformation_reportDTCByStatusMask` | `on message 0x7E8` → check `this.byte(1) == 0x59` |
| **Response decode** | `diagGetParameterRaw()` — auto-named fields | Manual byte indexing (`this.byte(4)`, `this.byte(5)`, ...) |
| **Portability** | Tied to the specific ODX database version | Works on any ECU with UDS — no config file needed |
| **Readability** | High — service names are self-documenting | Lower — must know UDS spec to read the code |
| **When to use** | Production test automation with full ODX | Quick debugging, bench tests, unknown ECU, no database available |

> **Interview tip:** Mention both approaches — "I prefer ODX symbolic for production scripts because it's readable and maintainable. But I also know how to write raw UDS hex scripts for bench debugging when no database is available."
