# Scenarios 21–25 — Diagnostics, DTCs & EOL Testing
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 21 — Cluster ECU Not Detected by Scan Tool in Default Session

> **Interviewer:** "A technician cannot communicate with the cluster ECU using a standard OBD-II scan tool. The tool shows 'No Response' for the cluster. The cluster is clearly ON and the display is functioning. What do you investigate?"

**Background:**
The cluster is working (physical evidence from display). The OBD-II scan tool cannot communicate. This is a diagnostic access issue, not a cluster hardware failure.

**Investigation Path:**

**Step 1 — Confirm the physical communication channel:**
A standard OBD-II tool communicates on:
- ISO 15765-4 (CAN): Functional address 0x7DF, or physical address (cluster-specific)
- ISO 14229 (UDS): layers on top of CAN
Check: is the cluster's diagnostic CAN address in the scan tool's vehicle database?

**Step 2 — CAN bus check:**
```capl
// Monitor all diagnostic CAN traffic to see if cluster responds at all
on message * {
  if (this.id == 0x7DF) {
    write("Functional UDS request received: 0x%X", this.id);
  }
  if (this.id >= 0x700 && this.id <= 0x7FF) {
    write("Diagnostic response: ID=0x%X  Data=[%02X %02X %02X %02X %02X %02X %02X %02X]",
          this.id,
          this.byte(0), this.byte(1), this.byte(2), this.byte(3),
          this.byte(4), this.byte(5), this.byte(6), this.byte(7));
  }
}
```
- Is the cluster sending any response at all? If NO response: either the cluster isn't receiving, or cluster SW diagnostic handler is not running.

**Step 3 — ISO TP (Transport Protocol) error:**
Cluster diagnostic is on a separate high-speed CAN bus (not the OBD-II port's default LS-CAN).
Gateway ECU (GW) bridges OBD-II port → diagnostic CAN bus.
If GW is not routing diagnostic requests to the cluster CAN: cluster never sees the request → no response.

**Step 4 — ECU address check:**
The cluster diagnostic request address (e.g., 0x720) must be listed in:
- The scan tool database (if using manufacturer-specific mode)
- The gateway routing table (if the request is bridged by GW)

**Step 5 — Diagnostic session suppression:**
During normal vehicle operation, some ECUs suppress diagnostic communication until a specific condition is met:
- Vehicle speed = 0
- KL15 = ON for minimum 5 seconds
- No active drive mode
Test: ensure all conditions are met before connecting scan tool.

**Test Cases:**
```
TC_DIAG_001: UDS 0x10 01 sent to cluster physical address → cluster responds with 0x50 01 within 50ms
TC_DIAG_002: Functional request 0x7DF 0x10 01 → cluster responds on its physical response address
TC_DIAG_003: UDS 0x7E (TesterPresent) every 2s → cluster remains in active session
TC_DIAG_004: UDS request while driving > 60 km/h → cluster must still respond (no speed lockout unless spec'd)
TC_DIAG_005: 10 back-to-back service requests → all answered without timeout or NRC 0x21 (busy)
TC_DIAG_006: Gateway routing: OBD-II port request → GW routes to cluster CAN → cluster responds
```

**Root Cause Summary:**
The cluster was on the body CAN bus (HS-CAN3) at 500 kbps. The OBD-II port is connected to powertrain HS-CAN1 at 500 kbps. The gateway ECU routing table had an entry for the cluster address (0x720) routing to HS-CAN3, but a recent gateway SW update reset the routing table to defaults (cluster address removed from table). Requests reached the gateway but were not forwarded to HS-CAN3 → cluster never received them. Fix: restore routing table entry in gateway SW.

---

## Scenario 22 — U0100 DTC Appears Every Ignition Cycle and Auto-Clears

> **Interviewer:** "A U0100 DTC (Lost Communication with ECM/PCM) appears on the cluster every ignition cycle, stays for 10–15 seconds, then self-clears. The engine runs normally. No drivability symptoms. What is happening?"

**Background:**
U0100 appearing only at startup and self-clearing suggests the ECM takes longer to become active on CAN than the cluster's communication timeout allows.

**Investigation Path:**

**Step 1 — Measure ECM CAN start-up timing:**
```capl
variables {
  dword tKL15_ON     = 0;
  dword tECM_First   = 0;
  dword tU0100_Set   = 0;
  dword tU0100_Clear = 0;
  int   gECM_Seen    = 0;
}

on sysvar SysVar::KL15_State {
  if (@SysVar::KL15_State == 1 && tKL15_ON == 0) {
    tKL15_ON = timeNow() / 10;
    write("[%d ms] KL15 ON — waiting for ECM...", tKL15_ON);
  }
}

on message ECM::EngineData_BC {
  if (!gECM_Seen) {
    gECM_Seen = 1;
    tECM_First = timeNow() / 10;
    write("[%d ms] ECM first message — delay from KL15 = %d ms",
          tECM_First, tECM_First - tKL15_ON);
  }
}

on signal Cluster::DTC_U0100_Active {
  if (this.value == 1 && tU0100_Set == 0) {
    tU0100_Set = timeNow() / 10;
    write("[%d ms] U0100 SET — ECM comm timeout", tU0100_Set);
  }
  if (this.value == 0 && tU0100_Set > 0) {
    tU0100_Clear = timeNow() / 10;
    write("[%d ms] U0100 CLEARED — ECM communication restored  (was active for %d ms)",
          tU0100_Clear, tU0100_Clear - tU0100_Set);
  }
}
```

**Step 2 — Expected finding:**
- KL15 ON: t=0ms
- Cluster timeout threshold: 500ms (typical — cluster expects ECM within 500ms)
- ECM first message: t=800ms (ECM boot takes 800ms at cold start)
- Result: at 500ms cluster sets U0100, at 800ms ECM appears → U0100 healed → self-clears

**Step 3 — Solutions:**
Option A: Increase cluster timeout threshold from 500ms to 1200ms (matches ECM boot time)
Option B: Change cluster timeout detection to use a "gradual warm-up" approach — only set DTC if ECM is absent for > 3 full ignition cycles (not just 500ms)
Option C: ECM SW optimised to send first CAN message earlier during boot (before full init)

**Step 4 — Threshold calibration test:**
```capl
// Inject simulated ECM message delay to find cluster timeout threshold
variables {
  message ECM_EngineData_BC msgECM;
  msTimer tmrECMDelay;
  int gDelayMs = 100;
}

on start {
  write("Finding cluster U0100 timeout threshold...");
  simulateKL15_ON();
  startTimer(tmrECMDelay, gDelayMs);
}

on timer tmrECMDelay {
  // Send first ECM message after delay
  output(msgECM);
  // Then check if U0100 was set
  delay(200);
  int dtc = getValue(Cluster::DTC_U0100_Active);
  write("Delay=%d ms → U0100=%d (0=no fault 1=fault)", gDelayMs, dtc);

  if (dtc == 0) {
    gDelayMs += 100;
    simulateKL15_OFF();
    delay(2000);
    simulateKL15_ON();
    setTimer(tmrECMDelay, gDelayMs);
  } else {
    write("THRESHOLD FOUND: U0100 sets at %d ms ECM absence", gDelayMs);
    write("ECM boot time must be shorter than %d ms to avoid U0100", gDelayMs);
    stop();
  }
}
```

**Test Cases:**
```
TC_U0100_001: ECM appears within 400ms of KL15 → no U0100 DTC at any point
TC_U0100_002: ECM absent for 2000ms → U0100 confirmed DTC set
TC_U0100_003: ECM comes back after 2000ms absence → U0100 heals in next drive cycle
TC_U0100_004: U0100 from startup self-clears → must not remain as confirmed DTC after clear
TC_U0100_005: 50 cold start ignition cycles → U0100 must never appear if ECM within spec boot time
TC_U0100_006: Genuine ECM fault (disconnect) → U0100 set AND engine warning lamp activates
```

**Root Cause Summary:**
Cold ECM boot takes 750ms at −20°C (battery cold cranking, bosch injector calibration check). Cluster timeout is 500ms. At temperatures below 0°C, the U0100 appears every start. Spec revised: cluster timeout increased to 1200ms to accommodate cold ECM boot time, with a note that timeout does not apply during extended crank (engine not yet started).

---

## Scenario 23 — EOL Backlight Test Fails on 3% of Production Units

> **Interviewer:** "The End-of-Line backlight brightness test — which measures cluster backlight output in candela and compares against a spec of 350–450 cd/m² — is failing on 3% of produced units. How do you investigate a production variation issue?"

**Background:**
3% failure rate on a production EOL test means either: (a) the test limit is too tight, (b) there is a component variation issue, or (c) the test setup itself has errors.

**Investigation Path:**

**Step 1 — Distribution plot:**
Collect all passing and failing measurements and plot distribution.
```
Results from 1000 units:
  Mean: 412 cd/m²
  Std dev: 18 cd/m²
  Range: 335–490 cd/m²
  Spec: 350–450 cd/m²

Units failing BELOW 350: 1.5% → 30 units (genuine dim LEDs)
Units failing ABOVE 450: 1.5% → 30 units (genuine bright LEDs / test jig issue)
```
Normal distribution within ±3σ. The spec window (100 cd/m²) is narrower than the natural process variation (±3σ = ±54 cd/m²). This is a Cpk (process capability) issue.

**Step 2 — Cp and Cpk calculation:**
```
Cp = (USL - LSL) / (6σ) = (450 - 350) / (6 × 18) = 100/108 = 0.93
Cpk = min((USL - mean) / (3σ), (mean - LSL) / (3σ))
    = min((450-412)/54, (412-350)/54)
    = min(0.70, 1.15) = 0.70

Cpk < 1.33 is not capable → 3% process failure rate expected
```
The process is not capable to the current specification.

**Step 3 — Root cause of variation:**
LED binning variation: LED brightness varies ±15% between bins (groups sorted by luminosity).
If the cluster supplier is using mixed LED bins instead of a consistent bin → natural variation.
Fix: tighten LED bin selection or adjust PWM duty cycle during EOL to normalise output.

**Step 4 — EOL calibration instead of test-only:**
Instead of rejecting 3%, implement an EOL calibration step:
1. Measure actual backlight output
2. Adjust PWM duty cycle to bring output within spec
3. Store calibration value in cluster NVM via UDS 0x2E

**CAPL EOL Backlight Calibration Script:**
```capl
/*
 * EOL Backlight Calibration
 * UDS: Writes backlight PWM correction factor to NVM
 * Target: 400 cd/m² ± 10%
 */

variables {
  diagRequest Cluster.DiagnosticSessionControl  reqSession;
  diagRequest Cluster.SecurityAccess_Seed       reqSeed;
  diagRequest Cluster.SecurityAccess_Key        reqKey;
  diagRequest Cluster.WriteDataByIdentifier     reqWrite;

  float TARGET_BRIGHTNESS = 400.0;   // target cd/m²
  float TOLERANCE_PCT     = 10.0;    // ±10%
}

float measureActualBrightness() {
  // Read brightness from photometer via GPIB/USB (hardware instrument)
  // Returns actual measured value in cd/m²
  // Placeholder — actual implementation reads measurement equipment
  return 385.0;   // example measured value
}

word calculatePWM_Correction(float measuredBrightness) {
  // PWM correction: linear scale factor
  // Base PWM = 2000 (resolution: 0–4095)
  // Correction = base × (target / measured)
  float scale = TARGET_BRIGHTNESS / measuredBrightness;
  return (word)(2000.0 * scale);
}

on start {
  float measured = measureActualBrightness();
  write("Measured backlight: %.1f cd/m²  Target: %.1f cd/m²", measured, TARGET_BRIGHTNESS);

  float lower = TARGET_BRIGHTNESS * (1.0 - TOLERANCE_PCT / 100.0);
  float upper = TARGET_BRIGHTNESS * (1.0 + TOLERANCE_PCT / 100.0);

  if (measured >= lower && measured <= upper) {
    write("PASS — Within spec (%.0f–%.0f cd/m²), no calibration needed", lower, upper);
    stop(); return;
  }

  write("Calibrating: entering extended session...");
  diagSetParameter(reqSession, "DiagnosticSessionType", 0x03);
  diagSendRequest(reqSession);
}

on diagResponse Cluster.DiagnosticSessionControl {
  diagSetParameter(reqSeed, "securityAccessType", 0x01);
  diagSendRequest(reqSeed);
}

on diagResponse Cluster.SecurityAccess_Seed {
  dword seed = diagGetRespPrimitiveLong(this, "securitySeed");
  dword key  = seed ^ 0x5A3C9F1E;   // EOL key algorithm
  diagSetParameter(reqKey, "securityAccessType", 0x02);
  diagSetParameter(reqKey, "securityKey", key);
  diagSendRequest(reqKey);
}

on diagResponse Cluster.SecurityAccess_Key {
  float measured  = measureActualBrightness();
  word  pwmCorr   = calculatePWM_Correction(measured);
  write("Writing PWM correction = %d (for measured %.1f cd/m²)", pwmCorr, measured);
  diagSetParameter(reqWrite, "dataIdentifier", 0xF250);   // Backlight cal DID
  diagSetParameter(reqWrite, "BacklightPWM_Cal", pwmCorr);
  diagSendRequest(reqWrite);
}

on diagResponse Cluster.WriteDataByIdentifier {
  if (diagGetRespCode(this) == 0x6E) {
    float remeasured = measureActualBrightness();
    write("Post-cal brightness: %.1f cd/m²", remeasured);
    write (remeasured >= 360 && remeasured <= 440 ? "EOL CAL PASS" : "EOL CAL FAIL");
  }
}
```

**Test Cases:**
```
TC_EOL_BL_001: Unit at 380 cd (below spec 350–450) → calibration adjusts → post-cal 400 ±10
TC_EOL_BL_002: Unit at 460 cd (above spec) → calibration reduces → post-cal within spec
TC_EOL_BL_003: Calibration value stored in NVM → survives 10 ignition cycles
TC_EOL_BL_004: Calibration value out of range (PWM > 4000) → EOL reject flag raised
TC_EOL_BL_005: Post-calibration brightness measured 3× → all readings consistent ±2%
TC_EOL_BL_006: Calibration process time < 30 seconds (production line takt requirement)
```

**Root Cause Summary:**
LED binning mixing across supplier batches caused ±20% brightness variation. Combined with a tight spec (±12.5% around 400 cd/m²), natural process variation exceeded the specification window (Cpk = 0.70). Implemented EOL calibration instead of reject-only. Failure rate: 3% → 0.1% (residual failures from units where measured brightness was outside the PWM correction range).

---

## Scenario 24 — UDS ReadDTCInformation Returns Wrong Snapshot Data

> **Interviewer:** "When reading a DTC freeze frame using UDS service 0x19 subfunction 0x04, the snapshot data (vehicle speed, engine RPM at fault time) shows zeros for all parameters even though the DTC was clearly set while driving. How do you investigate?"

**Background:**
DTC snapshot (freeze frame) should capture the vehicle operating conditions at the moment the DTC was confirmed. Zeros mean either the data was not captured, was captured as zeros, or the snapshot NVM was cleared.

**Investigation Path:**

**Step 1 — Verify the DTC and snapshot linkage:**
```capl
variables {
  diagRequest Cluster.ReadDTCInfo_SnapshotData reqSnap;
}

on start {
  // Request snapshot for fault code 0xB2001 (example cluster DTC)
  diagSetParameter(reqSnap, "subfunction",          0x04);   // Read snapshot
  diagSetParameter(reqSnap, "DTCMaskRecord",        0xB2001);
  diagSetParameter(reqSnap, "DTCSnapshotRecordNum", 0xFF);   // All records
  diagSendRequest(reqSnap);
}

on diagResponse Cluster.ReadDTCInfo_SnapshotData {
  long dtc_code  = diagGetRespPrimitiveLong(this, "DTC");
  byte snap_id   = diagGetRespPrimitiveByte(this, "SnapshotRecordNumber");
  word veh_speed = diagGetRespPrimitiveWord(this, "SnapshotData_VehicleSpeed_kmh");
  word eng_rpm   = diagGetRespPrimitiveWord(this, "SnapshotData_EngineRPM");
  byte coolant   = diagGetRespPrimitiveByte(this, "SnapshotData_CoolantTemp_degC");

  write("DTC 0x%06X  Snapshot#%d:", dtc_code, snap_id);
  write("  Vehicle Speed: %d km/h", veh_speed);
  write("  Engine RPM:    %d", eng_rpm);
  write("  Coolant Temp:  %d°C", coolant);

  if (veh_speed == 0 && eng_rpm == 0) {
    write("SUSPECT — All zeros: snapshot may not have been populated at fault time");
  }
}
```

**Step 2 — Snapshot capture timing:**
DTC snapshot must be captured at the first DTC confirmation event (2nd occurrence for confirmed DTC).
If the snapshot is captured at DTC storage (before re-confirm), the data may be from a parked/off state.

**Step 3 — Snapshot data sources:**
The cluster snapshot DID must read live input signals at the moment of fault:
- `VehicleSpeed` from CAN (ABS message)
- `EngineRPM` from CAN (ECM message)
At fault time, if these CAN signals are not yet active (e.g., fault happens during startup before CAN signals initialised), the snapshot captures 0 (default init value).

**Step 4 — NVM write sequence:**
Some implementations write the DTC to NVM before filling all snapshot fields.
If the NVM write occurs before the live data is copied into the snapshot buffer → snapshot is partially zeros.

**Test Cases:**
```
TC_SNAP_001: Inject fault while driving at 80 km/h, 2000 RPM → snapshot shows ~80 km/h, ~2000 RPM
TC_SNAP_002: Inject fault at ignition ON (speed=0, RPM=0) → snapshot shows 0,0 (correct for that condition)
TC_SNAP_003: Multiple faults in one drive → each has independent snapshot with its own data
TC_SNAP_004: DTC cleared → snapshot also cleared → 0x19 04 returns no data for cleared DTC
TC_SNAP_005: Snapshot survives battery disconnect → data intact after power cycle
TC_SNAP_006: Snapshot format matches ISO 15031-5 OBD-II freeze frame requirements
```

**Root Cause Summary:**
The cluster snapshot capture was triggered at DTC pending state (first occurrence) rather than DTC confirmed state. At first occurrence, the fault happens during the first 500ms of startup when `VehicleSpeed` and `EngineRPM` CAN signals have not yet been received and their internal registers hold init value of 0. Fix: snapshot must be captured at DTC confirmed state (second occurrence within a drive cycle), by which time all CAN inputs are live.

---

## Scenario 25 — Cluster Fails EOL All-Pixel Test on Specific Zone

> **Interviewer:** "The EOL all-pixel (All-Segment Display) test illuminates every pixel of the cluster display to check for dead pixels. The test passes on 95% of units but fails on 5% with dead pixels in the same specific zone: bottom-left corner, 100×50 pixel area. This precise zone pattern indicates a systematic cause. What do you investigate?"

**Background:**
A consistent failure zone across 5% of units points to a manufacturing or assembly issue — not random LED failure. The bottom-left corner is most likely a specific display connector pin range or a specific pixel driver IC.

**Investigation Path:**

**Step 1 — Map the failing zone to hardware:**
```
Display: 1280×480 pixels
Failing zone: x=0–100, y=430–480 (bottom-left)
Total failing pixels: 100×50 = 5000 pixels out of 614,400

The bottom-left corner maps to:
  - Column driver IC #1 (drives columns 0–127)
  - Row driver IC #6 (drives rows 431–480)
  - Flexible PCB connector: Pin group 3 (source lines 0–50)
```

**Step 2 — Connector damage during assembly:**
The bottom-left flexible PCB connector is at risk during the screen-to-housing assembly step.
If the assembly fixture is slightly misaligned → the flex connector folds against the housing edge → driver pins micro-cracked.
Examine 5 failing units: do the dead pixel zones all start at exactly x=0? → Confirms left-edge connector.

**Step 3 — Correlation with specific assembly shift or fixture:**
Pull production records for failing unit serial numbers.
If all failures come from: the same assembly line, same shift, or same date range → confirms a specific tooling, fixture, or operator procedure issue.

**Step 4 — Supplier batch tracking:**
Check if all 5% failures come from the same incoming component batch.
If failures correlate with a specific batch of display modules → supplier quality issue (display module pre-damaged).

**Step 5 — CAPL EOL pixel test script:**
```capl
/*
 * EOL All-Pixel Validation
 * Tests each display zone independently using photometer grid readings
 * Identifies specific failing zones with pixel coordinates
 */

variables {
  diagRequest Cluster.WriteMemoryAddr  reqPixelTest;
  diagRequest Cluster.ReadDataByID     reqZoneResult;

  int ZONE_COLS = 10;    // divide display into 10 column zones
  int ZONE_ROWS = 4;     // divide display into 4 row zones
  int gFailedZones[10][4];  // failed zone map
  int gTotalFails = 0;
}

testcase TC_EOL_ALLPIXEL() {
  // Activate all-pixel mode via UDS
  diagSetParameter(reqPixelTest, "memoryAddress", 0x00500000);
  diagSetParameter(reqPixelTest, "memorySize",    0x01);
  diagSetParameter(reqPixelTest, "dataRecord",    0xFF);  // 0xFF = all pixels ON
  diagSendRequest(reqPixelTest);
  testWaitForTimeout(500);  // allow display to settle

  // Read zone pass/fail bitmap from cluster
  diagSetParameter(reqZoneResult, "dataIdentifier", 0xF380);  // EOL zone result DID
  diagSendRequest(reqZoneResult);
  testWaitForResponse(reqZoneResult, 1000);

  // Parse zone bitmap
  long zoneBitmap = diagGetRespPrimitiveLong(reqZoneResult, "PixelZoneFaultMap");
  int zoneIdx = 0;

  for (int col = 0; col < ZONE_COLS; col++) {
    for (int row = 0; row < ZONE_ROWS; row++) {
      int bit = (zoneBitmap >> zoneIdx) & 0x01;
      if (bit == 1) {
        int x_start = col * 128;
        int y_start = row * 120;
        write("FAIL — Dead pixels in zone col=%d row=%d (x=%d–%d y=%d–%d)",
              col, row, x_start, x_start+127, y_start, y_start+119);
        gFailedZones[col][row] = 1;
        gTotalFails++;
      }
      zoneIdx++;
    }
  }

  if (gTotalFails == 0) {
    testStepPass("TC_ALLPIXEL", "All display zones: 0 dead pixel zones");
  } else {
    testStepFail("TC_ALLPIXEL",
      "Dead pixel zones detected: " + (string)gTotalFails + " out of 40 zones");
  }

  // Turn off all-pixel mode
  diagSetParameter(reqPixelTest, "dataRecord", 0x00);
  diagSendRequest(reqPixelTest);
}
```

**Test Cases:**
```
TC_PIX_001: All-pixel ON → photometer grid reading → every zone within ±10% of mean brightness
TC_PIX_002: Specific zone dead pixels > 5 in a 10×10 area → zone flagged as FAIL
TC_PIX_003: All rows illuminated independently → confirms row drivers functioning
TC_PIX_004: All columns illuminated independently → confirms column drivers functioning
TC_PIX_005: All-pixel test repeatable: same result on 3 consecutive runs
TC_PIX_006: EOL test time < 10 seconds (takt requirement)
```

**Root Cause Summary:**
Assembly jig support bracket on Line 2 was 1.5mm too high — causing a micro-bend in the flexible connector during the display-to-housing assembly step. The micro-bend stressed the driver line traces connected to the bottom-left pixel zone. Under thermal cycling (EOL hot test), these traces developed micro-cracks → dead pixels. Fix: jig height corrected. All 5% affected units (already built) inspected: those with dead pixels replaced display. Line 2 adjusted; subsequent production: 0% EOL pixel failure.

---
*File: 08_diagnostics_dtc.md | Scenarios 21–25 | April 2026*
