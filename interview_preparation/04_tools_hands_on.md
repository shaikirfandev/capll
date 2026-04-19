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

### What is ECU Flashing? (Simple explanation)

> **Think of it like this:**
> Your phone has an operating system (Android/iOS). When you do a software update,
> your phone downloads new code and replaces the old code inside. After the update,
> your phone works the same — but with new features or bug fixes.
>
> **ECU flashing is exactly the same thing — but for the car's computer (ECU).**
> The ECU is a small computer inside the car that controls things like the engine,
> brakes, airbags, or ADAS features. When engineers write new software and want to
> put it into the ECU, that process is called **flashing**.
>
> "Flash" = the type of memory inside the ECU (Flash memory — like a USB stick).
> Writing new code to that memory = **flashing the ECU**.

---

### Why do we flash an ECU?

```
Reason 1: Bug fix
  Old software had a bug → engineers fix the code → flash the new code to ECU
  Example: "ACC was braking too hard at 80 km/h" → SW fix → re-flash ECU → re-test

Reason 2: New feature added
  New ADAS feature developed → flash new SW → test it

Reason 3: Calibration update
  Radar sensitivity changed → new calibration values → flash → re-validate

Reason 4: Production line
  A brand new ECU comes from the factory with NO software.
  The assembly line flashes the software during car manufacturing.
```

---

### Scenario 9: "Walk me through how you flash an ECU"

#### Method 1: UDS Flashing via CANoe (most common in ADAS / Cluster testing)

**Simple version:**
> You connect a laptop (running CANoe) to the car via a special cable (CAN interface).
> CANoe sends a sequence of special messages to the ECU saying:
> "Hey ECU — wake up, let me write new code to you."
> The ECU says "OK" — and CANoe uploads the new software byte by byte.

**Detailed step-by-step:**

```
Step 1: Open Programming Session (0x10 02)
  What it means: You knock on the ECU's door and say
                 "I want to enter programming mode"
  ECU responds:  "OK, programming mode active" (positive response 0x50 02)

  Why needed:    Normal session (default) does NOT allow flashing.
                 You must switch to programming session first.
                 (Just like: you can't install apps on a phone without unlocking it)

──────────────────────────────────────────────────────────────

Step 2: Security Access — Request Seed (0x27 01)
  What it means: You ask the ECU "Give me a challenge (seed)"
  ECU responds:  Sends back a random 4-byte number — e.g., 0xA3 B7 22 F1

  Why needed:    The ECU doesn't let just ANYONE flash it.
                 It's like a password challenge.
                 (Just like: a bank ATM asks for your PIN before any transaction)

──────────────────────────────────────────────────────────────

Step 3: Security Access — Send Key (0x27 02)
  What it means: You take the seed, apply a secret algorithm (e.g., XOR, CRC)
                 and send back the computed "key"
  ECU checks:    "Is this the right key for the seed I sent?"
  ECU responds:  "Yes — access granted" (positive response 0x67 02)

  Why needed:    Confirms you are an authorised programmer, not a random person
                 (Just like: you enter your PIN → bank gives you access)

──────────────────────────────────────────────────────────────

Step 4: Disable Normal Communication (0x28 03)
  What it means: Stop all normal CAN messages during flashing
  ECU responds:  "OK, I will stop sending my normal messages"

  Why needed:    During flashing, the ECU is busy receiving new code.
                 If it's also trying to respond to other CAN messages,
                 it might get confused or corrupt the flash.
                 (Just like: "Do Not Disturb" mode on your phone during a big update)

──────────────────────────────────────────────────────────────

Step 5: Turn Off DTC Storage (0x85 02)
  What it means: Tell the ECU "don't log any fault codes during flashing"
  ECU responds:  "OK, DTC storage off"

  Why needed:    During flashing, some sensors might be disconnected or in odd states.
                 We don't want fake DTCs to be stored because of the flash process itself.

──────────────────────────────────────────────────────────────

Step 6: Erase Flash Memory (0x31 FF 00)
  What it means: "Erase the current software from memory"
  ECU responds:  "Erase complete" (can take 2–10 seconds)

  Why needed:    You can't write new code on top of old code in flash memory.
                 You must erase first — like formatting a USB stick before copying new files.
                 (Just like: "Factory Reset" before installing a fresh OS on a PC)

──────────────────────────────────────────────────────────────

Step 7: Request Download (0x34)
  What it means: "I want to send you a file. It's X bytes long. Here's the memory address."
  ECU responds:  "OK, I'm ready. Send me 128 bytes at a time (block size)"

  Why needed:    The ECU needs to know HOW MUCH data is coming and WHERE to store it.
                 (Just like: before copying a file to a USB stick, Windows checks
                 there's enough free space)

──────────────────────────────────────────────────────────────

Step 8: Transfer Data (0x36) — repeated many times
  What it means: Send the actual software file in small chunks
                 Block 1: 0x36 01 [128 bytes of software data]
                 Block 2: 0x36 02 [next 128 bytes]
                 Block 3: 0x36 03 [next 128 bytes]
                 ... continues until all data is sent

  ECU responds:  After each block: "Block received OK, send next"

  Why needed:    CAN bus can only send 8 bytes per frame.
                 So a 512 KB firmware file has to be split into thousands of small
                 chunks and sent one by one.
                 (Just like: emailing a large file as many smaller attachments)

──────────────────────────────────────────────────────────────

Step 9: Transfer Exit (0x37)
  What it means: "I finished sending all the data"
  ECU responds:  "All data received"

  Why needed:    Tells the ECU the transfer is complete.
                 ECU can now start verifying the data integrity.

──────────────────────────────────────────────────────────────

Step 10: Checksum Verification (0x31 FF 01)
  What it means: "Verify that the data I sent is correct — run a checksum check"
  ECU calculates: CRC or checksum of the received data
  ECU responds:  "Checksum PASS" or "Checksum FAIL"

  Why needed:    What if a byte got corrupted during transfer?
                 This step catches any data errors.
                 (Just like: after downloading a file, you check its MD5 hash
                 to make sure it downloaded correctly)

──────────────────────────────────────────────────────────────

Step 11: ECU Reset (0x11 01)
  What it means: "Restart yourself with the new software"
  ECU responds:  Reboots — starts running new code

  Why needed:    New software only becomes active after a reset.
                 (Just like: after a Windows update, you must restart the PC)

──────────────────────────────────────────────────────────────

Step 12: Verify SW Version (0x22 F1 95)
  What it means: "Read your current software version number"
  ECU responds:  "SW version: v2.5.0"

  Why needed:    Confirm the flash was successful — the ECU is running
                 the new software version we intended.

──────────────────────────────────────────────────────────────

Step 13: Read DTCs (0x19 02 0F)
  What it means: "Do you have any fault codes after the flash?"
  ECU responds:  List of active DTCs (should be zero after a clean flash)

  Why needed:    If the new software has a bug or something is misconfigured,
                 DTCs will appear immediately. This is the smoke test.
```

**The full flashing sequence at a glance:**

```
0x10 02  → Enter Programming Session
0x27 01  → Request Seed (security challenge)
0x27 02  → Send Key (security answer)
0x28 03  → Disable normal communication
0x85 02  → Disable DTC storage
0x31 FF00→ Erase flash memory
0x34     → Request download (tell ECU: file size + memory address)
0x36 01  → Transfer data block 1
0x36 02  → Transfer data block 2
  ...      (repeat until all blocks sent)
0x37     → Transfer exit
0x31 FF01→ Verify checksum
0x11 01  → ECU reset
0x22 F195→ Read SW version (confirm success)
0x19 02 0F→ Read DTCs (should be clean)
```

---

#### Method 2: USB Flash (Infotainment Head Unit)

```
Simple version:
  The infotainment screen is basically a tablet inside the car.
  You copy the new software onto a USB stick — plug it into the car —
  the screen detects it and installs it automatically.

Step by step:
  1. Get the firmware file (.zip or .bin) from the SW team
  2. Copy it to a USB stick (FAT32 formatted, must be in the root folder)
  3. Insert USB into the infotainment USB port
  4. On screen: "Update detected → Install? YES/NO" → tap YES
  5. Progress bar appears — takes 5–15 minutes
  6. Head unit reboots automatically
  7. Check: Settings → System Info → SW version = new version ✓

What can go wrong:
  - USB not FAT32 formatted → HU won't detect it
  - Wrong file name (HU looks for a specific filename like update.zip)
  - Power cut during update → partial flash → HU bricked (needs workshop recovery)
```

---

#### Method 3: ADB Flash (Android-based Head Unit)

```
Simple version:
  Some infotainment systems run Android (like AAOS — Android Automotive OS).
  ADB (Android Debug Bridge) is a developer tool — like a direct command line
  into the Android system inside the HU.

Step by step:
  1. Connect USB cable: laptop → HU USB developer port
  2. Open terminal on laptop

  3. Check connection:
     adb devices
     → Should show: "HU_SERIAL_NUMBER  device"

  4. Reboot into bootloader (flash mode):
     adb reboot bootloader

  5. Flash the system partition:
     fastboot flash system system.img

  6. Flash the boot partition:
     fastboot flash boot boot.img

  7. Reboot:
     fastboot reboot

  8. Verify new version:
     adb shell getprop ro.build.version.incremental
     → Should print: "v2.5.0_20260419"

  9. Check logs for errors:
     adb logcat | grep -i "error\|crash\|fatal"
```

---

#### Post-Flash Checklist (ALL methods)

```
After every flash — always check these before signing off:

  □ SW version correct?
      UDS: 0x22 F1 95 → read version
      ADB: adb shell getprop ro.build.version.incremental

  □ Zero DTCs after flash?
      UDS: 0x19 02 0F → should return "0 DTCs"
      If DTCs present: note them, clear (0x14 FF FF FF), recheck

  □ Basic functionality (smoke test):
      ADAS: does ACC activate? LKA respond?
      Infotainment: does the screen boot? Media play? GPS lock?
      Cluster: do all warning lamps extinguish on IGN ON?

  □ NVM/calibration preserved?
      Check odometer reading (should not reset to 0)
      Check stored user settings (language, units, paired phones)
      Check ECU variant coding (0x22 F1 20) — should match HW variant

  □ Re-run relevant regression tests
      Any test that was FAIL before this build → re-run → verify PASS
```

---

#### Interview one-liner to summarise it:

> "ECU flashing is the process of writing new software into the ECU's flash memory.
> For CAN-connected ECUs like ADAS and cluster, I use UDS-based flashing via CANoe —
> the sequence is: programming session → security access → erase → download →
> transfer data in blocks → checksum verify → reset → confirm SW version.
> For infotainment, I use USB package update or ADB fastboot depending on the HU type.
> After every flash I always check: SW version, DTC count, basic function smoke test,
> and NVM integrity."

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

---

## 7. Full Script Examples — CAPL & Python

### CAPL Script: Complete UDS Diagnostic Sequence (ODX Symbolic)

> Full workflow — session switch → security access → read SW version → read DTCs → print report

```capl
/*
 * Full UDS Diagnostic Sequence — ODX Symbolic version
 * ──────────────────────────────────────────────────
 * Step 1: Enter Extended Diagnostic Session
 * Step 2: Security Access (Seed → Key)
 * Step 3: Read SW version (DID F195)
 * Step 4: Read all confirmed DTCs (0x19 02 08)
 * Step 5: Print summary report
 *
 * Requires: ODX/PDX loaded in CANoe, ECU node named "ECU"
 */

variables {
  char  swVersion[32];
  byte  dtcRaw[256];
  int   dtcCount   = 0;
  int   stepNumber = 0;

  // Security key algorithm: Simple XOR with 0xCA (replace with real algo)
  dword seed       = 0;
  dword key        = 0;
}

/* ════════════════════════════════════════════════════
   STEP 1 — Enter Extended Diagnostic Session
   ════════════════════════════════════════════════════ */
on start {
  diagRequest ECU.DiagnosticSessionControl_extendedDiagnosticSession req;
  stepNumber = 1;
  write("[DIAG] ── Step 1: Requesting Extended Session...");
  diagSendRequest(req);
}

on diagResponse ECU.DiagnosticSessionControl_extendedDiagnosticSession {
  if (diagGetLastResponseCode(this) < 0) {
    write("[DIAG] ✓ Extended Session active");

    /* ── Step 2: Request Seed ── */
    diagRequest ECU.SecurityAccess_requestSeed seedReq;
    stepNumber = 2;
    write("[DIAG] ── Step 2: Requesting Security Seed...");
    diagSendRequest(seedReq);
  } else {
    write("[DIAG] ✗ Session switch FAILED — NRC: 0x%02X",
          diagGetLastResponseCode(this));
  }
}

/* ════════════════════════════════════════════════════
   STEP 2a — Receive Seed
   ════════════════════════════════════════════════════ */
on diagResponse ECU.SecurityAccess_requestSeed {
  if (diagGetLastResponseCode(this) < 0) {
    // Extract seed (4 bytes) and compute key
    seed  = (dword)diagGetParameter(this, "SecurityAccessDataRecord");
    key   = seed ^ 0xCAFEBABE;   // ← Replace with your project's real algorithm

    write("[DIAG] ✓ Seed received: 0x%08X  →  Computed key: 0x%08X", seed, key);

    /* ── Step 2b: Send Key ── */
    diagRequest ECU.SecurityAccess_sendKey keyReq;
    diagSetParameter(keyReq, "SecurityAccessDataRecord", key);
    stepNumber = 3;
    write("[DIAG] ── Step 2b: Sending Security Key...");
    diagSendRequest(keyReq);
  } else {
    write("[DIAG] ✗ Seed request FAILED — NRC: 0x%02X",
          diagGetLastResponseCode(this));
  }
}

/* ════════════════════════════════════════════════════
   STEP 2b — Key accepted → Read SW Version
   ════════════════════════════════════════════════════ */
on diagResponse ECU.SecurityAccess_sendKey {
  if (diagGetLastResponseCode(this) < 0) {
    write("[DIAG] ✓ Security Access GRANTED");

    /* ── Step 3: Read SW Version (DID F195) ── */
    diagRequest ECU.ReadDataByIdentifier req;
    diagSetParameter(req, "DataIdentifier", 0xF195);
    stepNumber = 4;
    write("[DIAG] ── Step 3: Reading SW Version (DID 0xF195)...");
    diagSendRequest(req);
  } else {
    write("[DIAG] ✗ Key REJECTED — NRC: 0x%02X.  Wrong algorithm?",
          diagGetLastResponseCode(this));
  }
}

/* ════════════════════════════════════════════════════
   STEP 3 — Receive SW Version → Read DTCs
   ════════════════════════════════════════════════════ */
on diagResponse ECU.ReadDataByIdentifier {
  if (diagGetLastResponseCode(this) < 0) {
    diagGetParameterString(this, "ECU_SoftwareVersionNumber", swVersion, 32);
    write("[DIAG] ✓ SW Version: %s", swVersion);

    /* ── Step 4: Read confirmed DTCs ── */
    diagRequest ECU.ReadDTCInformation_reportDTCByStatusMask dtcReq;
    diagSetParameter(dtcReq, "DTCStatusMask", 0x08);   // 0x08 = confirmed
    stepNumber = 5;
    write("[DIAG] ── Step 4: Reading confirmed DTCs (mask 0x08)...");
    diagSendRequest(dtcReq);
  } else {
    write("[DIAG] ✗ ReadDataByIdentifier FAILED — NRC: 0x%02X",
          diagGetLastResponseCode(this));
  }
}

/* ════════════════════════════════════════════════════
   STEP 4 — Receive DTC list → Print Report
   ════════════════════════════════════════════════════ */
on diagResponse ECU.ReadDTCInformation_reportDTCByStatusMask {
  int len, i;
  byte h, m, l, s;

  if (diagGetLastResponseCode(this) < 0) {
    len      = diagGetParameterRaw(this, "DTCAndStatusRecord", dtcRaw, 256);
    dtcCount = len / 4;

    write("╔══════════════════════════════════════════════╗");
    write("║  UDS DIAGNOSTIC REPORT                       ║");
    write("║  ECU SW Version : %-26s ║", swVersion);
    write("║  Confirmed DTCs : %-3d                        ║", dtcCount);
    write("╠══════════════════════════════════════════════╣");

    if (dtcCount == 0) {
      write("║  No DTCs — ECU is CLEAN ✓                    ║");
    } else {
      for (i = 0; i < dtcCount; i++) {
        h = dtcRaw[i*4];
        m = dtcRaw[i*4 + 1];
        l = dtcRaw[i*4 + 2];
        s = dtcRaw[i*4 + 3];
        write("║  DTC[%02d]: %02X %02X %02X  Status: 0x%02X           ║",
              i+1, h, m, l, s);
      }
    }

    write("╚══════════════════════════════════════════════╝");
  } else {
    write("[DIAG] ✗ ReadDTCInformation FAILED — NRC: 0x%02X",
          diagGetLastResponseCode(this));
  }
}
```

---

### Python Script: Complete UDS Diagnostic Sequence (Raw CAN via python-can + udsoncan)

> Same workflow in Python — useful for CI pipelines, automated nightly tests, or when no CANoe licence is available.

**Libraries needed:**
```bash
pip install python-can udsoncan
```

```python
"""
Full UDS Diagnostic Sequence — Python version
──────────────────────────────────────────────
Connects to a real CAN interface (e.g., Vector XL, PEAK PCAN, or SocketCAN).
Performs:
  Step 1 : Enter Extended Diagnostic Session
  Step 2 : Security Access  (Seed → Key)
  Step 3 : Read SW Version  (DID 0xF195)
  Step 4 : Read confirmed DTCs  (0x19 02 08)
  Step 5 : Print report + save to CSV

Install : pip install python-can udsoncan
"""

import can
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client    import Client
from udsoncan           import configs, services
import isotp
import csv
import datetime
import sys

# ─────────────────────────────────────────────────────────────
# 1. Configuration
# ─────────────────────────────────────────────────────────────
CAN_INTERFACE  = "vector"          # "pcan" | "socketcan" | "vector" | "kvaser"
CAN_CHANNEL    = "PCAN_USBBUS1"    # e.g. "can0" for SocketCAN
CAN_BITRATE    = 500000            # 500 kbps

ECU_TX_ID      = 0x7E0             # Tester → ECU (physical request)
ECU_RX_ID      = 0x7E8             # ECU → Tester (response)

OUTPUT_CSV     = "dtc_report.csv"


def compute_key(seed: int) -> int:
    """
    Security key algorithm — replace with your project's real formula.
    Example here: XOR with fixed secret.
    """
    return seed ^ 0xCAFEBABE


# ─────────────────────────────────────────────────────────────
# 2. CAN + ISO-TP transport layer setup
# ─────────────────────────────────────────────────────────────
bus = can.Bus(
    interface=CAN_INTERFACE,
    channel=CAN_CHANNEL,
    bitrate=CAN_BITRATE,
)

tp_addr = isotp.Address(
    isotp.AddressingMode.Normal_11bits,
    txid=ECU_TX_ID,
    rxid=ECU_RX_ID,
)

stack = isotp.CanStack(bus=bus, address=tp_addr)
conn  = PythonIsoTpConnection(stack)

# udsoncan client config
client_config = configs.default_client_config.copy()
client_config["security_algo"]      = compute_key          # hook our key function
client_config["security_algo_extra_args"] = {}
client_config["request_timeout"]    = 2.0
client_config["p2_timeout"]         = 1.0


# ─────────────────────────────────────────────────────────────
# 3. Main diagnostic sequence
# ─────────────────────────────────────────────────────────────
def run_diagnostics():
    dtc_results  = []
    sw_version   = "UNKNOWN"

    with Client(conn, config=client_config) as client:

        # ── Step 1: Extended Diagnostic Session ──────────────
        print("[DIAG] Step 1: Entering Extended Diagnostic Session...")
        resp = client.change_session(
            services.DiagnosticSessionControl.Session.extendedDiagnosticSession
        )
        if not resp.positive:
            print(f"[DIAG] ✗ Session switch FAILED — NRC: {resp.code_name}")
            sys.exit(1)
        print("[DIAG] ✓ Extended Session active")

        # ── Step 2: Security Access ───────────────────────────
        print("[DIAG] Step 2: Requesting security access...")
        client.unlock_security_access(level=0x01)   # level 0x01 → subfunction 0x01/0x02
        print("[DIAG] ✓ Security Access granted")

        # ── Step 3: Read SW Version (DID 0xF195) ─────────────
        print("[DIAG] Step 3: Reading SW Version (DID 0xF195)...")
        resp = client.read_data_by_identifier(
            [udsoncan.DataIdentifier(0xF195)]
        )
        if resp.positive:
            raw_val = resp.service_data.values.get(0xF195, b"")
            sw_version = raw_val.decode("ascii", errors="replace").strip()
            print(f"[DIAG] ✓ SW Version: {sw_version}")
        else:
            print(f"[DIAG] ✗ ReadDataByIdentifier FAILED — NRC: {resp.code_name}")

        # ── Step 4: Read Confirmed DTCs (status mask 0x08) ───
        print("[DIAG] Step 4: Reading confirmed DTCs (mask 0x08)...")
        resp = client.get_dtc_by_status_mask(status_mask=0x08)

        if resp.positive:
            dtcs = resp.service_data.dtcs
            print(f"[DIAG] ✓ {len(dtcs)} confirmed DTC(s) found")
            for dtc in dtcs:
                dtc_results.append({
                    "dtc_id":     f"{dtc.id:06X}",
                    "status":     f"0x{dtc.status.byte:02X}",
                    "severity":   str(dtc.severity),
                    "functional_unit": str(dtc.functional_unit),
                })
        else:
            print(f"[DIAG] ✗ ReadDTCInformation FAILED — NRC: {resp.code_name}")

    return sw_version, dtc_results


# ─────────────────────────────────────────────────────────────
# 4. Print report + save CSV
# ─────────────────────────────────────────────────────────────
def print_report(sw_version: str, dtcs: list):
    border = "═" * 50
    print(f"\n╔{border}╗")
    print(f"║  UDS DIAGNOSTIC REPORT{' ' * 27}║")
    print(f"║  Date       : {datetime.datetime.now():%Y-%m-%d %H:%M:%S}{' ' * 12}║")
    print(f"║  SW Version : {sw_version:<35}║")
    print(f"║  DTCs Found : {len(dtcs):<35}║")
    print(f"╠{border}╣")

    if not dtcs:
        print(f"║  No DTCs — ECU is CLEAN ✓{' ' * 24}║")
    else:
        print(f"║  {'#':<4} {'DTC ID':<10} {'Status':<10} {'Severity':<15}║")
        print(f"╠{border}╣")
        for i, d in enumerate(dtcs, 1):
            print(f"║  {i:<4} {d['dtc_id']:<10} {d['status']:<10} {d['severity']:<15}║")

    print(f"╚{border}╝\n")


def save_csv(sw_version: str, dtcs: list, filename: str):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["dtc_id", "status", "severity", "functional_unit"]
        )
        writer.writeheader()
        writer.writerows(dtcs)
    print(f"[CSV] Report saved → {filename}")


# ─────────────────────────────────────────────────────────────
# 5. Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        sw, dtc_list = run_diagnostics()
        print_report(sw, dtc_list)
        save_csv(sw, dtc_list, OUTPUT_CSV)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        bus.shutdown()
```

**Output example:**
```
[DIAG] Step 1: Entering Extended Diagnostic Session...
[DIAG] ✓ Extended Session active
[DIAG] Step 2: Requesting security access...
[DIAG] ✓ Security Access granted
[DIAG] Step 3: Reading SW Version (DID 0xF195)...
[DIAG] ✓ SW Version: v2.5.0_20260419
[DIAG] Step 4: Reading confirmed DTCs (mask 0x08)...
[DIAG] ✓ 2 confirmed DTC(s) found

╔══════════════════════════════════════════════════╗
║  UDS DIAGNOSTIC REPORT                           ║
║  Date       : 2026-04-19 14:32:07                ║
║  SW Version : v2.5.0_20260419                    ║
║  DTCs Found : 2                                  ║
╠══════════════════════════════════════════════════╣
║  #    DTC ID     Status     Severity            ║
╠══════════════════════════════════════════════════╣
║  1    C0200A     0x08       warning             ║
║  2    B1003F     0x08       warning             ║
╚══════════════════════════════════════════════════╝

[CSV] Report saved → dtc_report.csv
```

**Key library mapping (Python ↔ CAPL):**

| CAPL (CANoe) | Python (udsoncan) |
|---|---|
| `diagRequest ECU.DiagnosticSessionControl_extendedDiagnosticSession` | `client.change_session(Session.extendedDiagnosticSession)` |
| `diagRequest ECU.SecurityAccess_requestSeed` | `client.unlock_security_access(level=0x01)` |
| `diagRequest ECU.ReadDataByIdentifier` | `client.read_data_by_identifier([DataIdentifier(0xF195)])` |
| `diagRequest ECU.ReadDTCInformation_reportDTCByStatusMask` | `client.get_dtc_by_status_mask(status_mask=0x08)` |
| `diagGetLastResponseCode(this) < 0` | `resp.positive == True` |
| `diagGetParameterRaw(this, "DTCAndStatusRecord", buf, 256)` | `resp.service_data.dtcs` |
| `write("...")` | `print("...")` |

> **Interview tip:** "In my BYD project, I used CAPL for real-time in-loop testing inside CANoe,
> and Python scripts for nightly regression runs on the CI server — same diagnostic logic,
> different execution environments."

---

## 8. ECU Flashing Scripts — CAPL & Python (Full UDS Sequence)

> These scripts implement the complete 13-step UDS flash sequence from Scenario 9.
> They read a binary firmware file and transfer it block by block to the ECU.

---

### CAPL Script: Full UDS ECU Flashing (Raw CAN — no ODX needed)

> CAPL does not have native file I/O for binary files, so the firmware is stored as
> a byte array (simulating a loaded `.hex` / `.bin`). In real projects, the firmware
> is pre-loaded into a CAPL byte buffer by a wrapper or test environment.

```capl
/*
 * UDS ECU Flash Script — CAPL (Raw CAN, no ODX)
 * ══════════════════════════════════════════════
 * Implements full ISO 14229 flash sequence:
 *   0x10 02 → Programming Session
 *   0x27 01/02 → Security Access (Seed/Key)
 *   0x28 03 → Disable Comm
 *   0x85 02 → Disable DTC storage
 *   0x31 FF 00 → Erase Flash
 *   0x34 → Request Download
 *   0x36 xx → Transfer Data (looped)
 *   0x37 → Transfer Exit
 *   0x31 FF 01 → Checksum Verify
 *   0x11 01 → ECU Reset
 *   0x22 F1 95 → Read SW Version
 *   0x19 02 0F → Read DTCs
 *
 * CAN IDs: Tester→ECU = 0x7E0 | ECU→Tester = 0x7E8
 */

variables {
  message 0x7E0 req;          // tester request frame
  msTimer tTimeout;           // response timeout guard

  // ── Flash state machine ──────────────────────────────
  int  flashStep    = 0;      // current step (0 = idle)
  int  blockIndex   = 1;      // 0x36 block sequence counter (1..255)
  int  fwOffset     = 0;      // byte offset into fwData[]
  int  fwTotalBytes = 0;      // total firmware size in bytes
  int  blockSize    = 128;    // negotiated max block size (bytes per 0x36)

  // ── Simulated firmware buffer (replace with real data load) ──
  // In real use: load from file or receive via test framework.
  // Here: 384 bytes of dummy data (3 blocks × 128 bytes).
  byte fwData[384];

  // ── Result flags ─────────────────────────────────────
  char newSwVersion[32];
  int  flashResult = 0;   // 1 = success
}

/* ════════════════════════════════════════════════════════════
   HELPERS
   ════════════════════════════════════════════════════════════ */
void sendRaw(byte b0, byte b1, byte b2, byte b3,
             byte b4, byte b5, byte b6, byte b7) {
  req.dlc     = 8;
  req.byte(0) = b0;
  req.byte(1) = b1;
  req.byte(2) = b2;
  req.byte(3) = b3;
  req.byte(4) = b4;
  req.byte(5) = b5;
  req.byte(6) = b6;
  req.byte(7) = b7;
  output(req);
  setTimer(tTimeout, 5000);   // 5s timeout per step
}

/* ════════════════════════════════════════════════════════════
   START — initialise firmware buffer and begin sequence
   ════════════════════════════════════════════════════════════ */
on start {
  int i;
  // Fill dummy firmware with pattern 0x00..0xFF repeating
  fwTotalBytes = 384;
  for (i = 0; i < fwTotalBytes; i++) fwData[i] = (byte)(i & 0xFF);

  write("╔══════════════════════════════════════════╗");
  write("║  ECU FLASH START                         ║");
  write("║  Firmware size : %d bytes              ║", fwTotalBytes);
  write("╚══════════════════════════════════════════╝");

  // Step 1: Enter Programming Session (0x10 02)
  flashStep = 1;
  write("[FLASH] Step 1 → Programming Session (0x10 02)");
  sendRaw(0x02, 0x10, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00);
}

/* ════════════════════════════════════════════════════════════
   RECEIVE — all ECU responses arrive on 0x7E8
   ════════════════════════════════════════════════════════════ */
on message 0x7E8 {
  byte sid = this.byte(1);
  byte sub = this.byte(2);
  byte nrc = this.byte(3);
  int  i;
  byte blk[8];
  int  remaining, chunkLen;
  dword seed, key;

  cancelTimer(tTimeout);

  // ── Negative Response ──────────────────────────────────────
  if (sid == 0x7F) {
    write("[FLASH] ✗ NEGATIVE RESPONSE at step %d — SID:0x%02X NRC:0x%02X",
          flashStep, sub, nrc);
    write("        NRC meaning: %s", nrcToString(nrc));
    return;
  }

  // ── Step 1 response: 0x50 02 — Programming Session active ──
  if (sid == 0x50 && flashStep == 1) {
    write("[FLASH] ✓ Step 1 PASS — Programming Session active");

    // Step 2: Request Seed (0x27 01)
    flashStep = 2;
    write("[FLASH] Step 2 → Request Seed (0x27 01)");
    sendRaw(0x02, 0x27, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00);
  }

  // ── Step 2 response: 0x67 01 + 4-byte seed ─────────────────
  else if (sid == 0x67 && sub == 0x01 && flashStep == 2) {
    seed = ((dword)this.byte(2) << 24) | ((dword)this.byte(3) << 16) |
           ((dword)this.byte(4) <<  8) |  (dword)this.byte(5);
    key  = seed ^ 0xCAFEBABE;   // ← Replace with project algorithm
    write("[FLASH] ✓ Step 2a — Seed: 0x%08X → Key: 0x%08X", seed, key);

    // Step 3: Send Key (0x27 02)
    flashStep = 3;
    write("[FLASH] Step 3 → Send Key (0x27 02)");
    sendRaw(0x06, 0x27, 0x02,
            (byte)(key >> 24), (byte)(key >> 16),
            (byte)(key >>  8), (byte)(key),
            0x00);
  }

  // ── Step 3 response: 0x67 02 — Key accepted ────────────────
  else if (sid == 0x67 && sub == 0x02 && flashStep == 3) {
    write("[FLASH] ✓ Step 3 PASS — Security Access granted");

    // Step 4: Disable Normal Communication (0x28 03)
    flashStep = 4;
    write("[FLASH] Step 4 → Disable Communication (0x28 03)");
    sendRaw(0x02, 0x28, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00);
  }

  // ── Step 4 response: 0x68 ──────────────────────────────────
  else if (sid == 0x68 && flashStep == 4) {
    write("[FLASH] ✓ Step 4 PASS — Communication disabled");

    // Step 5: Disable DTC Storage (0x85 02)
    flashStep = 5;
    write("[FLASH] Step 5 → Disable DTC Storage (0x85 02)");
    sendRaw(0x02, 0x85, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00);
  }

  // ── Step 5 response: 0xC5 ──────────────────────────────────
  else if (sid == 0xC5 && flashStep == 5) {
    write("[FLASH] ✓ Step 5 PASS — DTC storage disabled");

    // Step 6: Erase Flash (0x31 01 FF 00)
    flashStep = 6;
    write("[FLASH] Step 6 → Erase Flash (0x31 01 FF 00) — may take up to 10s...");
    sendRaw(0x04, 0x31, 0x01, 0xFF, 0x00, 0x00, 0x00, 0x00);
    setTimer(tTimeout, 15000);   // erase can take longer
  }

  // ── Step 6 response: 0x71 01 FF 00 — Erase complete ────────
  else if (sid == 0x71 && flashStep == 6) {
    write("[FLASH] ✓ Step 6 PASS — Flash erased");

    // Step 7: Request Download (0x34)
    // Byte layout: 0x34 | dataFormatId | addrAndLenFormat | memAddr(4) | memSize(4)
    // addrAndLenFormat = 0x44 → 4-byte address, 4-byte size
    // Memory address: 0x08000000 (example — adjust for target ECU)
    flashStep = 7;
    write("[FLASH] Step 7 → Request Download (0x34) — addr=0x08000000 size=%d", fwTotalBytes);
    req.dlc     = 8;
    req.byte(0) = 0x0A;   // PCI: 10 payload bytes → use multi-frame in real ISO-TP
    req.byte(1) = 0x34;   // Service ID
    req.byte(2) = 0x00;   // dataFormatIdentifier (no compression)
    req.byte(3) = 0x44;   // addrAndLenFormat: 4+4 bytes
    req.byte(4) = 0x08;   // memory address byte 1 (0x08000000)
    req.byte(5) = 0x00;
    req.byte(6) = 0x00;
    req.byte(7) = 0x00;
    output(req);
    // Note: Real impl needs ISO-TP multi-frame; simplified here for concept.
    setTimer(tTimeout, 5000);
  }

  // ── Step 7 response: 0x74 — Download accepted, block size given ──
  else if (sid == 0x74 && flashStep == 7) {
    // Byte 2 = lengthFormatId, Bytes 3-4 = maxBlockSize
    blockSize = (this.byte(3) << 8) | this.byte(4);
    if (blockSize == 0) blockSize = 128;   // fallback
    write("[FLASH] ✓ Step 7 PASS — ECU ready, maxBlockSize = %d bytes", blockSize);

    // Step 8: Transfer Data — first block
    flashStep  = 8;
    blockIndex = 1;
    fwOffset   = 0;
    write("[FLASH] Step 8 → Transfer Data (0x36) — sending %d blocks...",
          (fwTotalBytes + blockSize - 1) / blockSize);
    sendNextBlock();
  }

  // ── Step 8 response: 0x76 xx — Block received ──────────────
  else if (sid == 0x76 && flashStep == 8) {
    fwOffset += blockSize;
    write("[FLASH]   Block %d ✓ (%d / %d bytes transferred)",
          blockIndex, fwOffset > fwTotalBytes ? fwTotalBytes : fwOffset, fwTotalBytes);
    blockIndex++;

    if (fwOffset < fwTotalBytes) {
      sendNextBlock();   // send next block
    } else {
      write("[FLASH] ✓ Step 8 PASS — All data transferred");

      // Step 9: Transfer Exit (0x37)
      flashStep = 9;
      write("[FLASH] Step 9 → Transfer Exit (0x37)");
      sendRaw(0x01, 0x37, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
    }
  }

  // ── Step 9 response: 0x77 — Transfer complete ──────────────
  else if (sid == 0x77 && flashStep == 9) {
    write("[FLASH] ✓ Step 9 PASS — Transfer exit confirmed");

    // Step 10: Checksum Verify (0x31 01 FF 01)
    flashStep = 10;
    write("[FLASH] Step 10 → Checksum Verify (0x31 01 FF 01)");
    sendRaw(0x04, 0x31, 0x01, 0xFF, 0x01, 0x00, 0x00, 0x00);
  }

  // ── Step 10 response: 0x71 01 FF 01 — Checksum OK ──────────
  else if (sid == 0x71 && flashStep == 10) {
    if (this.byte(4) == 0x00) {   // result byte 0x00 = PASS
      write("[FLASH] ✓ Step 10 PASS — Checksum verified OK");
    } else {
      write("[FLASH] ✗ Step 10 FAIL — Checksum ERROR (result=0x%02X)", this.byte(4));
      return;
    }

    // Step 11: ECU Reset (0x11 01)
    flashStep = 11;
    write("[FLASH] Step 11 → ECU Reset (0x11 01)");
    sendRaw(0x02, 0x11, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00);
  }

  // ── Step 11 response: 0x51 01 — Reset acknowledged ─────────
  else if (sid == 0x51 && flashStep == 11) {
    write("[FLASH] ✓ Step 11 PASS — ECU rebooting...");
    write("[FLASH]   Waiting 3 seconds for ECU boot...");
    flashStep = 12;
    setTimer(tTimeout, 3000);   // wait for ECU to boot up
  }

  // ── Step 12: After reset — Read SW Version (0x22 F1 95) ─────
  else if (sid == 0x62 && flashStep == 12) {
    // 0x62 = positive response to 0x22
    int len, i;
    for (i = 0; i < 16 && this.byte(4 + i) != 0x00; i++)
      newSwVersion[i] = this.byte(4 + i);
    newSwVersion[i] = 0x00;
    write("[FLASH] ✓ Step 12 PASS — New SW Version: %s", newSwVersion);

    // Step 13: Read DTCs (0x19 02 0F)
    flashStep = 13;
    write("[FLASH] Step 13 → Read DTCs after flash (0x19 02 0F)");
    sendRaw(0x03, 0x19, 0x02, 0x0F, 0x00, 0x00, 0x00, 0x00);
  }

  // ── Step 13: DTC response (0x59 02) ─────────────────────────
  else if (sid == 0x59 && flashStep == 13) {
    int numDTCs = (this.dlc - 4) / 4;
    if (numDTCs == 0) {
      write("[FLASH] ✓ Step 13 PASS — 0 DTCs after flash ✓");
      flashResult = 1;
    } else {
      write("[FLASH] ⚠ Step 13 WARNING — %d DTC(s) found after flash!", numDTCs);
    }
    printFlashSummary();
  }
}

/* ════════════════════════════════════════════════════════════
   SEND NEXT DATA BLOCK (0x36)
   ════════════════════════════════════════════════════════════ */
void sendNextBlock() {
  int i, remaining, chunkLen;

  remaining = fwTotalBytes - fwOffset;
  chunkLen  = (remaining < blockSize) ? remaining : blockSize;

  // For interview/demo: send first 6 bytes of the block (simplified single CAN frame)
  // Real implementation requires ISO-TP multi-frame for chunks > 6 bytes.
  req.dlc     = 8;
  req.byte(0) = (byte)(chunkLen + 2);   // PCI length
  req.byte(1) = 0x36;                    // TransferData
  req.byte(2) = (byte)(blockIndex & 0xFF);  // block sequence counter
  // Bytes 3-7: first 5 bytes of this block chunk
  for (i = 0; i < 5 && i < chunkLen; i++)
    req.byte(3 + i) = fwData[fwOffset + i];

  output(req);
  setTimer(tTimeout, 2000);
}

/* ════════════════════════════════════════════════════════════
   TIMEOUT — no response from ECU
   ════════════════════════════════════════════════════════════ */
on timer tTimeout {
  if (flashStep == 12) {
    // Boot wait complete — now read SW version
    write("[FLASH] ECU boot wait done → reading SW version (0x22 F1 95)");
    sendRaw(0x03, 0x22, 0xF1, 0x95, 0x00, 0x00, 0x00, 0x00);
  } else {
    write("[FLASH] ✗ TIMEOUT at step %d — no ECU response within limit", flashStep);
    printFlashSummary();
  }
}

/* ════════════════════════════════════════════════════════════
   FINAL SUMMARY
   ════════════════════════════════════════════════════════════ */
void printFlashSummary() {
  write("╔══════════════════════════════════════════════╗");
  write("║  ECU FLASH SUMMARY                           ║");
  write("║  Steps completed : %-3d / 13                 ║", flashStep);
  write("║  New SW Version  : %-26s ║", newSwVersion);
  write("║  Result          : %-26s ║",
        flashResult ? "SUCCESS ✓" : "FAILED ✗ — check log");
  write("╚══════════════════════════════════════════════╝");
}

/* ════════════════════════════════════════════════════════════
   NRC HELPER — translate NRC byte to readable string
   ════════════════════════════════════════════════════════════ */
char nrcToString(byte nrc)[] {
  switch(nrc) {
    case 0x10: return "generalReject";
    case 0x11: return "serviceNotSupported";
    case 0x12: return "subFunctionNotSupported";
    case 0x13: return "incorrectMessageLengthOrInvalidFormat";
    case 0x22: return "conditionsNotCorrect";
    case 0x24: return "requestSequenceError";
    case 0x25: return "noResponseFromSubnetComponent";
    case 0x31: return "requestOutOfRange";
    case 0x33: return "securityAccessDenied";
    case 0x35: return "invalidKey";
    case 0x36: return "exceededNumberOfAttempts";
    case 0x37: return "requiredTimeDelayNotExpired";
    case 0x70: return "uploadDownloadNotAccepted";
    case 0x71: return "transferDataSuspended";
    case 0x72: return "generalProgrammingFailure";
    case 0x73: return "wrongBlockSequenceCounter";
    case 0x78: return "requestCorrectlyReceivedResponsePending";
    default:   return "unknownNRC";
  }
}
```

---

### Python Script: Full UDS ECU Flashing (python-can + udsoncan)

> Reads a real `.bin` firmware file from disk and flashes it block by block.
> Handles multi-frame ISO-TP automatically via the `isotp` library.

**Libraries needed:**
```bash
pip install python-can udsoncan isotp
```

```python
"""
UDS ECU Flash Script — Python (python-can + udsoncan)
══════════════════════════════════════════════════════
Full ISO 14229 flash sequence:
  Step 1 : Programming Session  (0x10 02)
  Step 2 : Security Access      (0x27 01/02)
  Step 3 : Disable Comm         (0x28 03)
  Step 4 : Disable DTC Storage  (0x85 02)
  Step 5 : Erase Flash          (0x31 01 FF 00)
  Step 6 : Request Download     (0x34)
  Step 7 : Transfer Data        (0x36 — looped)
  Step 8 : Transfer Exit        (0x37)
  Step 9 : Checksum Verify      (0x31 01 FF 01)
  Step 10: ECU Reset            (0x11 01)
  Step 11: Read SW Version      (0x22 F1 95)
  Step 12: Read DTCs            (0x19 02 0F)

Usage:
  python uds_flash.py firmware.bin

Install:
  pip install python-can udsoncan isotp
"""

import can
import isotp
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client      import Client
from udsoncan             import configs, services, MemoryLocation, DataFormatIdentifier
import sys
import time
import os

# ─────────────────────────────────────────────────────────────
# 1. Configuration — adjust for your project
# ─────────────────────────────────────────────────────────────
CAN_INTERFACE   = "vector"          # "pcan" | "socketcan" | "vector" | "kvaser"
CAN_CHANNEL     = "PCAN_USBBUS1"    # "can0" for SocketCAN
CAN_BITRATE     = 500_000           # 500 kbps

ECU_TX_ID       = 0x7E0             # Tester → ECU
ECU_RX_ID       = 0x7E8             # ECU → Tester

FLASH_MEM_ADDR  = 0x08000000        # ECU flash start address
BLOCK_SIZE      = 128               # bytes per transfer block (ECU may negotiate higher)
SECURITY_LEVEL  = 0x01              # programming security level

FIRMWARE_FILE   = sys.argv[1] if len(sys.argv) > 1 else "firmware.bin"


# ─────────────────────────────────────────────────────────────
# 2. Security key algorithm
# ─────────────────────────────────────────────────────────────
def compute_key(seed: int, params: dict) -> int:
    """Replace with your project's real seed→key algorithm."""
    return seed ^ 0xCAFEBABE


# ─────────────────────────────────────────────────────────────
# 3. CAN + ISO-TP transport setup
# ─────────────────────────────────────────────────────────────
def create_client() -> Client:
    bus = can.Bus(interface=CAN_INTERFACE, channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
    tp_addr = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        txid=ECU_TX_ID,
        rxid=ECU_RX_ID,
    )
    stack = isotp.CanStack(bus=bus, address=tp_addr)
    conn  = PythonIsoTpConnection(stack)

    cfg = configs.default_client_config.copy()
    cfg["security_algo"]           = compute_key
    cfg["security_algo_extra_args"] = {}
    cfg["request_timeout"]         = 10.0   # longer for flash operations
    cfg["p2_timeout"]              = 5.0

    return Client(conn, config=cfg), bus


# ─────────────────────────────────────────────────────────────
# 4. Flash helper: load firmware
# ─────────────────────────────────────────────────────────────
def load_firmware(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Firmware file not found: {path}")
    with open(path, "rb") as f:
        data = f.read()
    print(f"[FLASH] Firmware loaded: {path} ({len(data):,} bytes)")
    return data


# ─────────────────────────────────────────────────────────────
# 5. Main flash sequence
# ─────────────────────────────────────────────────────────────
def flash_ecu(firmware: bytes):
    client, bus = create_client()

    try:
        with client:

            # ── Step 1: Programming Session ──────────────────────
            print("\n[FLASH] ━━━ Step 1: Enter Programming Session (0x10 02) ━━━")
            resp = client.change_session(
                services.DiagnosticSessionControl.Session.programmingSession
            )
            _check(resp, "Programming Session")

            # ── Step 2: Security Access ───────────────────────────
            print("[FLASH] ━━━ Step 2: Security Access (0x27 01/02) ━━━")
            client.unlock_security_access(level=SECURITY_LEVEL)
            print("[FLASH] ✓ Security Access granted")

            # ── Step 3: Disable Normal Communication ─────────────
            print("[FLASH] ━━━ Step 3: Disable Communication (0x28 03) ━━━")
            resp = client.communication_control(
                control_type=services.CommunicationControl.ControlType.disableRxAndTx,
                communication_type=services.CommunicationControl.CommunicationType(
                    subnet=0xF, nm_msg=False, app_msg=True
                )
            )
            _check(resp, "Disable Communication")

            # ── Step 4: Disable DTC Storage ───────────────────────
            print("[FLASH] ━━━ Step 4: Disable DTC Storage (0x85 02) ━━━")
            resp = client.control_dtc_setting(
                setting_type=services.ControlDTCSetting.SettingType.off
            )
            _check(resp, "Disable DTC Storage")

            # ── Step 5: Erase Flash ───────────────────────────────
            print("[FLASH] ━━━ Step 5: Erase Flash (0x31 01 FF 00) ━━━")
            print("[FLASH]   Erasing... (may take up to 10 seconds)")
            resp = client.start_routine(
                routine_id=0xFF00,
                # memory address + size as routine option record
                routine_option_record=bytes([
                    (FLASH_MEM_ADDR >> 24) & 0xFF,
                    (FLASH_MEM_ADDR >> 16) & 0xFF,
                    (FLASH_MEM_ADDR >>  8) & 0xFF,
                     FLASH_MEM_ADDR        & 0xFF,
                    (len(firmware) >> 24) & 0xFF,
                    (len(firmware) >> 16) & 0xFF,
                    (len(firmware) >>  8) & 0xFF,
                     len(firmware)        & 0xFF,
                ])
            )
            _check(resp, "Erase Flash")
            print("[FLASH] ✓ Flash erased")

            # ── Step 6: Request Download (0x34) ──────────────────
            print("[FLASH] ━━━ Step 6: Request Download (0x34) ━━━")
            mem_location = MemoryLocation(
                address=FLASH_MEM_ADDR,
                length=len(firmware),
                address_format=32,   # 4-byte address
                length_format=32,    # 4-byte length
            )
            resp = client.request_download(
                memory_location=mem_location,
                dfi=DataFormatIdentifier(compression_method=0, encrypting_method=0),
            )
            _check(resp, "Request Download")
            # ECU may return a max block size — use it
            if hasattr(resp.service_data, 'max_length'):
                negotiated = resp.service_data.max_length
                if negotiated and negotiated > 0:
                    global BLOCK_SIZE
                    BLOCK_SIZE = negotiated
            print(f"[FLASH] ✓ Download accepted — block size: {BLOCK_SIZE} bytes")

            # ── Step 7: Transfer Data (0x36) — loop ──────────────
            print(f"[FLASH] ━━━ Step 7: Transfer Data (0x36) ━━━")
            total_blocks = (len(firmware) + BLOCK_SIZE - 1) // BLOCK_SIZE
            print(f"[FLASH]   Sending {len(firmware):,} bytes in {total_blocks} blocks...")

            for block_num in range(total_blocks):
                offset     = block_num * BLOCK_SIZE
                chunk      = firmware[offset : offset + BLOCK_SIZE]
                sequence   = (block_num + 1) & 0xFF   # wraps at 255

                resp = client.transfer_data(sequence_number=sequence, data=chunk)
                _check(resp, f"TransferData block {sequence}")

                # Progress bar
                pct = int((block_num + 1) / total_blocks * 40)
                bar = "█" * pct + "░" * (40 - pct)
                print(f"\r[FLASH]   [{bar}] {block_num+1}/{total_blocks}", end="", flush=True)

            print()   # newline after progress bar
            print("[FLASH] ✓ All blocks transferred")

            # ── Step 8: Transfer Exit (0x37) ─────────────────────
            print("[FLASH] ━━━ Step 8: Transfer Exit (0x37) ━━━")
            resp = client.request_transfer_exit()
            _check(resp, "Transfer Exit")

            # ── Step 9: Checksum Verify (0x31 01 FF 01) ──────────
            print("[FLASH] ━━━ Step 9: Checksum Verify (0x31 01 FF 01) ━━━")
            resp = client.start_routine(routine_id=0xFF01)
            _check(resp, "Checksum Verification")
            result_byte = resp.service_data.routine_status_record[0] \
                          if resp.service_data.routine_status_record else 0x00
            if result_byte != 0x00:
                raise RuntimeError(f"Checksum FAILED — result byte: 0x{result_byte:02X}")
            print("[FLASH] ✓ Checksum verified — data integrity confirmed")

            # ── Step 10: ECU Reset (0x11 01) ─────────────────────
            print("[FLASH] ━━━ Step 10: ECU Reset (0x11 01) ━━━")
            resp = client.ecu_reset(
                reset_type=services.ECUReset.ResetType.hardReset
            )
            _check(resp, "ECU Reset")
            print("[FLASH] ✓ ECU reset initiated — waiting 5s for boot...")
            time.sleep(5)

            # ── Step 11: Read SW Version (0x22 F1 95) ────────────
            print("[FLASH] ━━━ Step 11: Read SW Version (0x22 F1 95) ━━━")
            # After reset ECU is back in default session
            resp = client.read_data_by_identifier(
                [udsoncan.DataIdentifier(0xF195)]
            )
            sw_version = "UNKNOWN"
            if resp.positive:
                raw = resp.service_data.values.get(0xF195, b"")
                sw_version = raw.decode("ascii", errors="replace").strip()
            print(f"[FLASH] ✓ New SW Version: {sw_version}")

            # ── Step 12: Read DTCs (0x19 02 0F) ──────────────────
            print("[FLASH] ━━━ Step 12: Read DTCs after flash (0x19 02 0F) ━━━")
            resp = client.get_dtc_by_status_mask(status_mask=0x0F)
            dtc_count = 0
            if resp.positive:
                dtc_count = len(resp.service_data.dtcs)
            status = "CLEAN ✓" if dtc_count == 0 else f"⚠ {dtc_count} DTC(s) found!"
            print(f"[FLASH] ✓ Post-flash DTC check: {status}")

            # ── Final Report ──────────────────────────────────────
            print_summary(sw_version, dtc_count, len(firmware), total_blocks)

    finally:
        bus.shutdown()


# ─────────────────────────────────────────────────────────────
# 6. Helper: check response, raise on negative
# ─────────────────────────────────────────────────────────────
def _check(resp, label: str):
    if not resp.positive:
        raise RuntimeError(f"[FLASH] ✗ {label} FAILED — NRC: {resp.code_name}")
    print(f"[FLASH] ✓ {label} — OK")


# ─────────────────────────────────────────────────────────────
# 7. Print final summary
# ─────────────────────────────────────────────────────────────
def print_summary(sw_version, dtc_count, fw_size, total_blocks):
    border = "═" * 52
    result = "FLASH SUCCESS ✓" if dtc_count == 0 else "FLASH DONE — CHECK DTCs"
    print(f"\n╔{border}╗")
    print(f"║  ECU FLASH COMPLETE                                  ║")
    print(f"║  Firmware size  : {fw_size:>8,} bytes                    ║")
    print(f"║  Blocks sent    : {total_blocks:>8}                          ║")
    print(f"║  New SW Version : {sw_version:<33}║")
    print(f"║  Post-flash DTCs: {dtc_count:<33}║")
    print(f"║  Result         : {result:<33}║")
    print(f"╚{border}╝\n")


# ─────────────────────────────────────────────────────────────
# 8. Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        fw = load_firmware(FIRMWARE_FILE)
        flash_ecu(fw)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[FLASH] Aborted by user.")
        sys.exit(1)
```

**Example terminal output:**
```
[FLASH] Firmware loaded: firmware.bin (524,288 bytes)

[FLASH] ━━━ Step 1: Enter Programming Session (0x10 02) ━━━
[FLASH] ✓ Programming Session — OK
[FLASH] ━━━ Step 2: Security Access (0x27 01/02) ━━━
[FLASH] ✓ Security Access granted
[FLASH] ━━━ Step 3: Disable Communication (0x28 03) ━━━
[FLASH] ✓ Disable Communication — OK
[FLASH] ━━━ Step 4: Disable DTC Storage (0x85 02) ━━━
[FLASH] ✓ Disable DTC Storage — OK
[FLASH] ━━━ Step 5: Erase Flash (0x31 01 FF 00) ━━━
[FLASH]   Erasing... (may take up to 10 seconds)
[FLASH] ✓ Flash erased
[FLASH] ━━━ Step 6: Request Download (0x34) ━━━
[FLASH] ✓ Download accepted — block size: 256 bytes
[FLASH] ━━━ Step 7: Transfer Data (0x36) ━━━
[FLASH]   Sending 524,288 bytes in 2048 blocks...
[FLASH]   [████████████████████████████████████████] 2048/2048
[FLASH] ✓ All blocks transferred
[FLASH] ━━━ Step 8: Transfer Exit (0x37) ━━━
[FLASH] ✓ Transfer Exit — OK
[FLASH] ━━━ Step 9: Checksum Verify (0x31 01 FF 01) ━━━
[FLASH] ✓ Checksum verified — data integrity confirmed
[FLASH] ━━━ Step 10: ECU Reset (0x11 01) ━━━
[FLASH] ✓ ECU reset initiated — waiting 5s for boot...
[FLASH] ━━━ Step 11: Read SW Version (0x22 F1 95) ━━━
[FLASH] ✓ New SW Version: v2.5.0_20260419
[FLASH] ━━━ Step 12: Read DTCs after flash (0x19 02 0F) ━━━
[FLASH] ✓ Post-flash DTC check: CLEAN ✓

╔════════════════════════════════════════════════════╗
║  ECU FLASH COMPLETE                                  ║
║  Firmware size  :  524,288 bytes                    ║
║  Blocks sent    :     2048                          ║
║  New SW Version : v2.5.0_20260419                   ║
║  Post-flash DTCs: 0                                 ║
║  Result         : FLASH SUCCESS ✓                   ║
╚════════════════════════════════════════════════════╝
```

**UDS Flash step mapping — CAPL vs Python:**

| Step | UDS Hex | CAPL (raw CAN) | Python (udsoncan) |
|------|---------|----------------|-------------------|
| Programming Session | `0x10 02` | `sendRaw(0x02, 0x10, 0x02, ...)` | `client.change_session(programmingSession)` |
| Request Seed | `0x27 01` | `sendRaw(0x02, 0x27, 0x01, ...)` | `client.unlock_security_access(level=0x01)` |
| Disable Comm | `0x28 03` | `sendRaw(0x02, 0x28, 0x03, ...)` | `client.communication_control(disableRxAndTx)` |
| Disable DTC | `0x85 02` | `sendRaw(0x02, 0x85, 0x02, ...)` | `client.control_dtc_setting(off)` |
| Erase Flash | `0x31 01 FF 00` | `sendRaw(0x04, 0x31, 0x01, 0xFF, 0x00, ...)` | `client.start_routine(0xFF00, ...)` |
| Request Download | `0x34` | `sendRaw + manual bytes` | `client.request_download(memory_location, dfi)` |
| Transfer Data | `0x36 xx [data]` | `output(req)` in loop | `client.transfer_data(sequence_number, data)` |
| Transfer Exit | `0x37` | `sendRaw(0x01, 0x37, ...)` | `client.request_transfer_exit()` |
| Checksum Verify | `0x31 01 FF 01` | `sendRaw(0x04, 0x31, 0x01, 0xFF, 0x01, ...)` | `client.start_routine(0xFF01)` |
| ECU Reset | `0x11 01` | `sendRaw(0x02, 0x11, 0x01, ...)` | `client.ecu_reset(hardReset)` |
| Read SW Version | `0x22 F1 95` | `sendRaw(0x03, 0x22, 0xF1, 0x95, ...)` | `client.read_data_by_identifier([0xF195])` |
| Read DTCs | `0x19 02 0F` | `sendRaw(0x03, 0x19, 0x02, 0x0F, ...)` | `client.get_dtc_by_status_mask(0x0F)` |

> **Interview tip:** "In the CAPL script I handle the state machine with `flashStep` variable and
> respond to each 0x7E8 frame at the right step. In Python, `udsoncan` handles ISO-TP framing
> automatically — so multi-frame transfer of large blocks (>7 bytes) works out of the box,
> which is critical for the 0x36 data transfer loop."
