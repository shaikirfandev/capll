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

## 3. dSPACE HIL — Interview Walkthrough

### Scenario 7: "Explain how you set up a HIL test for ADAS"

**Your walkthrough:**
```
"The HIL setup at BYD consisted of:

Hardware:
  - dSPACE SCALEXIO real-time processor
  - VT Studio for signal routing and I/O configuration
  - ADAS ECU connected via CAN and Ethernet interfaces

Setup steps:
  1. Load the ADAS ECU plant model (Simulink model compiled for dSPACE)
  2. Map ECU CAN inputs to dSPACE CAN channels (e.g., RadarObject → CAN1, CameraLane → CAN2)
  3. Configure sensor simulation: inject radar targets with distance, velocity, RCS
  4. Configure vehicle model: speed, yaw rate, steering angle

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
