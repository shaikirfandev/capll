# Scenarios 1–5 — Speedometer, Tachometer & Odometer
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 1 — Speedometer Reads Correctly at Low Speed but Drifts High Above 100 km/h

> **Interviewer:** "The speedometer is accurate between 0–100 km/h but progressively overreads above 100 km/h — at 160 km/h actual speed, the cluster shows 172 km/h. What is the fault?"

**Background:**
A non-linear error that grows with speed suggests a scaling issue — either a wrong factor, a lookup table error, or a non-linearity in the wheel speed sensor signal processing.

**Investigation Path:**

**Step 1 — Confirm error profile:**
Test at 60, 80, 100, 120, 140, 160 km/h using GPS reference:
```
60 km/h  → cluster shows 61  → error = +1.7%  (within EU +10% spec)
100 km/h → cluster shows 101 → error = +1.0%
120 km/h → cluster shows 126 → error = +5.0%
160 km/h → cluster shows 172 → error = +7.5%  (non-linear — grows with speed)
```
Non-linear error → not a simple offset → either lookup table or polynomial scaling

**Step 2 — Check CAN signal encoding:**
The `VehicleSpeed` signal is often encoded as:
- Linear: `speed_kmh = raw × factor + offset`
- Lookup table: cluster interpolates from a calibration table

If a lookup table is used, a wrong entry at the high-speed end causes overread only at high speed.

**Step 3 — CAN raw vs display comparison:**
```capl
on signal ABS::VehicleSpeed_raw {
  float can_speed = this.value * 0.01;    // factor: 0.01 km/h per bit
  float displayed = getValue(Cluster::Speedometer_Display_kmh);
  float error_pct = (displayed - can_speed) / can_speed * 100.0;

  write("CAN=%.1f km/h  Display=%.1f km/h  Error=%.2f%%",
        can_speed, displayed, error_pct);

  if (error_pct > 5.0) {
    write("WARNING — Error exceeds 5%% at %.1f km/h — non-linear scaling suspected", can_speed);
  }
}
```

**Step 4 — Segment the lookup table:**
Request the cluster lookup table calibration data via UDS:
```
UDS 0x22 0xF210 → SpeedCalibration_LUT (manufacturer-specific DID)
Compare LUT entries at high speed range vs spec
```

**Step 5 — Test all speeds systematically:**
```capl
variables {
  message ABS_Speed_BC msgSpd;
  msTimer tmrSweep;
  int gSpeedTable[12] = {0,20,40,60,80,100,110,120,130,140,150,160};
  int gIdx = 0;
  int gPass = 0, gFail = 0;
}

on start { setTimer(tmrSweep, 500); }

on timer tmrSweep {
  if (gIdx >= elcount(gSpeedTable)) {
    write("=== Speed Accuracy: PASS=%d FAIL=%d ===", gPass, gFail);
    stop(); return;
  }

  int setSpeed = gSpeedTable[gIdx];
  msgSpd.VehicleSpeed_raw = (word)(setSpeed * 100);  // 0.01 km/h/bit
  output(msgSpd);
  delay(400);

  float displayed = getValue(Cluster::Speedometer_Display_kmh);
  float error     = displayed - (float)setSpeed;
  // EU spec: +0 to +10% of actual speed
  float maxAllowed = (float)setSpeed * 0.10;

  if (error >= 0.0 && error <= maxAllowed) {
    write("PASS [%3d km/h] Display=%.1f  Error=+%.1f km/h (%.1f%%)",
          setSpeed, displayed, error, error/setSpeed*100);
    gPass++;
  } else {
    write("FAIL [%3d km/h] Display=%.1f  Error=%.1f km/h (%.1f%%) *** OUT OF SPEC",
          setSpeed, displayed, error, error/setSpeed*100);
    gFail++;
  }

  gIdx++;
  setTimer(tmrSweep, 800);
}
```

**Test Cases:**
```
TC_SPD_001: 30 km/h CAN input → cluster displays 30–33 km/h (0 to +10%)
TC_SPD_002: 100 km/h CAN input → cluster displays 100–110 km/h
TC_SPD_003: 160 km/h CAN input → cluster displays 160–176 km/h
TC_SPD_004: Speed signal absent (timeout) → cluster shows 0 km/h or last valid with timeout indicator
TC_SPD_005: Speed transitions 0→160→0 in 2s → cluster tracks within 200ms lag
TC_SPD_006: Speed at exactly 0 → no negative display, no flicker around zero
```

**Root Cause Summary:**
The cluster speed display uses a lookup table for conversion. The high-speed portion of the table (>100 km/h) was calibrated with a factor of `0.0112` instead of `0.01` km/h per bit — a 12% over-factor applied only above 100 km/h due to a table entry error introduced during a platform portover from a different vehicle programme.

---

## Scenario 2 — RPM Needle Oscillates ±200 RPM at Idle

> **Interviewer:** "At idle (850 RPM), the tachometer needle continuously oscillates between 650–1050 RPM with a visible shaking motion. It's smooth at higher RPM. Customer reports it feels like the engine is hunting. How do you investigate?"

**Background:**
If the engine is genuinely hunting (unstable idle speed): ECM issue, not cluster. If only the needle oscillates but the ECM reports stable RPM: cluster damping/filtering issue.

**Investigation Path:**

**Step 1 — Separate ECM RPM from cluster display:**
```capl
variables {
  float gRPM_CAN_min   = 99999.0;
  float gRPM_CAN_max   = 0.0;
  float gRPM_Disp_min  = 99999.0;
  float gRPM_Disp_max  = 0.0;
  dword gSamplesCount  = 0;
}

on signal ECM::Engine_RPM {
  float rpm = this.value;
  if (rpm < gRPM_CAN_min)  gRPM_CAN_min  = rpm;
  if (rpm > gRPM_CAN_max)  gRPM_CAN_max  = rpm;
  gSamplesCount++;
}

on signal Cluster::Tachometer_Display_RPM {
  float disp = this.value;
  if (disp < gRPM_Disp_min) gRPM_Disp_min = disp;
  if (disp > gRPM_Disp_max) gRPM_Disp_max = disp;
}

// After 10 seconds at idle
on key 'r' {
  float can_range  = gRPM_CAN_max  - gRPM_CAN_min;
  float disp_range = gRPM_Disp_max - gRPM_Disp_min;
  write("CAN RPM range at idle:     %.0f–%.0f  (spread=%.0f RPM)", gRPM_CAN_min, gRPM_CAN_max, can_range);
  write("Cluster display range:     %.0f–%.0f  (spread=%.0f RPM)", gRPM_Disp_min, gRPM_Disp_max, disp_range);

  if (can_range < 50 && disp_range > 300) {
    write("RESULT: ECM RPM is stable — cluster DAMPING FAULT (display oscillates more than signal)");
  } else if (can_range > 300) {
    write("RESULT: ECM RPM is genuinely unstable — engine idle quality issue, NOT cluster");
  }
}
```

**Step 2 — Check cluster needle damping parameter:**
Cluster needle movement is damped to prevent mechanical wear and to smooth visual jitter.
Damping is configured as an exponential moving average:
```
displayed_rpm = α × new_rpm + (1 - α) × displayed_rpm
α = 0.05 (heavy damping) → smooth but lagging
α = 0.8  (light damping)  → fast but oscillates with noise
```
If α was incorrectly set to 0.8 in a SW update, any ±10 RPM noise in the CAN signal would produce ±200 RPM visual oscillation due to stepped needle movement at low RPM.

**Step 3 — RPM signal noise check:**
At idle, cylinder firing causes real RPM pulses. A 4-cylinder engine at 850 RPM fires every 35ms — potential CAN signal noise.
Check: is the ECM sending RPM as instantaneous crankshaft speed (noisy) or as engine average RPM (smooth)?
Fix: ECM should send 100ms average RPM, not instantaneous.

**Test Cases:**
```
TC_RPM_001: Stable CAN RPM 850 → cluster needle must not oscillate more than ±25 RPM visually
TC_RPM_002: RPM step 800→2000 → needle reaches 2000 within 300ms (damping must not lag excessively)
TC_RPM_003: RPM signal jitter ±50 RPM at 5Hz → cluster shows smooth needle, not tracking every jitter
TC_RPM_004: RPM 0 → ignition on → needle sweeps from 0 to max and returns before engine start
TC_RPM_005: RPM ramp from 0 to 6000 at 100 RPM/100ms → needle tracks linearly
TC_RPM_006: RPM exceeds red line (6500) → needle must not exceed physical stop
```

**Root Cause Summary:**
Cluster SW update changed the needle damping coefficient α from `0.15` to `0.72` — possibly a copy-paste error from a sports variant calibration. At idle RPM, combined with the ECM sending instantaneous (not averaged) RPM, the high α value allows every 10 RPM crankshaft fluctuation to translate into a visible needle jump. Fix: restore α = 0.15 for the standard powertrain variant.

---

## Scenario 3 — Odometer Value Differs Between Cluster and Service Tool Read

> **Interviewer:** "A technician reads the odometer on the cluster display: 45,230 km. They then read the odometer via a UDS 0x22 request on the cluster ECU: it returns 44,980 km. A 250 km difference. Which is correct and why is there a discrepancy?"

**Background:**
Two odometer values existing simultaneously usually means the cluster has two separate odometer counters — one for display (live) and one stored in NVM (committed). The NVM write may lag behind the live counter.

**Investigation Path:**

**Step 1 — Understand the odometer architecture:**
```
Live counter (RAM):   incremented as vehicle moves, real-time, lost on power off
NVM counter:          written periodically (every 5 km or on ignition OFF)
Display shows:        live RAM counter
UDS 0x22 returns:    NVM counter (last committed value)
```
If vehicle drove 250 km without the NVM being written → live = 45,230, NVM = 44,980.

**Step 2 — When is NVM written?:**
Check cluster SW spec:
- Triggered on ignition OFF → if the last 250 km were driven with no ignition OFF (long continuous trip) + this was the first read after a power cut: NVM never got the latest value.
- Triggered every 5 km → 250 km gap = NVM hasn't been written in 50 cycles = impossible unless NVM write is failing.

**Step 3 — Check for NVM write failure DTC:**
```
UDS 0x19 02 08 on cluster: look for B1010 or B1011 (NVM write error)
If DTC present → NVM write has been failing silently → NVM reading 250 km behind
```

**Step 4 — Verify which value is legally correct:**
EU Regulation: the odometer displayed to the driver must be the accurate mileage.
The display showing the live counter is correct. The NVM UDS value is the backup.
If NVM differs by > spec tolerance (typically ≤ 10 km): NVM write fault.

**CAPL — Monitor NVM Write Events:**
```capl
variables {
  dword gOdo_NVM_last   = 0;
  dword gOdo_Live_last  = 0;
  dword gNVM_write_count = 0;
}

on signal Cluster::Odometer_Live_km {
  dword live = (dword)this.value;
  if (live != gOdo_Live_last) {
    gOdo_Live_last = live;
  }
}

on signal Cluster::Odometer_NVM_Written {
  // This signal pulses each time an NVM write completes
  if (this.value == 1) {
    gNVM_write_count++;
    dword delta = gOdo_Live_last - gOdo_NVM_last;
    write("[NVM Write #%d] Live=%d  NVM written  Delta before write=%d km",
          gNVM_write_count, gOdo_Live_last, delta);

    if (delta > 10) {
      write("WARNING — NVM write lag %d km (spec ≤10 km)", delta);
    }
    gOdo_NVM_last = gOdo_Live_last;
  }
}

// On ignition cycle, verify NVM was written before power off
on signal PowerSupply::KL15_Active {
  if (this.value == 0) {
    dword finalDelta = gOdo_Live_last - gOdo_NVM_last;
    if (finalDelta > 1) {
      write("FAIL — IGN OFF with %d km un-committed to NVM (expected ≤1 km)", finalDelta);
    } else {
      write("PASS — IGN OFF: NVM committed within 1 km of live odometer");
    }
  }
}
```

**Test Cases:**
```
TC_ODO_001: Drive 100 km → ignition OFF → UDS 0x22 reads odo within 1 km of display
TC_ODO_002: Drive 5 km without ignition OFF → UDS read → within 5 km of display
TC_ODO_003: 500 km continuous drive (no IGN OFF) → NVM updated every 5 km per spec
TC_ODO_004: Battery disconnect mid-drive → restore power → UDS odo = display odo ±5 km
TC_ODO_005: Odometer must not roll forward during vehicle off (no phantom accumulation)
TC_ODO_006: NVM write failure DTC → cluster must alert technician, not silently diverge
```

**Root Cause Summary:**
The cluster NVM write was configured to trigger only on ignition OFF (not every 5 km). The customer had been on a long road trip (250+ km, one engine-off at destination). A subsequent power supply interruption (loose battery terminal) occurred before the ignition-OFF NVM write completed. Result: live counter had 45,230 km (in volatile RAM, lost) but the last NVM commit had 44,980 km. The display shows the NVM value after power loss — so both the display and UDS would show the same 44,980 km after the power event. The 250 km is genuinely lost from the odometer.

---

## Scenario 4 — Gear Indicator Displays P (Park) While Car Is Rolling

> **Interviewer:** "PRND display on the cluster shows 'P' while the vehicle is clearly moving at 30 km/h. The car is in Drive. How is this possible and what test do you write to catch it?"

**Background:**
Displaying 'P' while moving is a safety issue — it may cause a driver to believe the car is in Park and attempt to exit. This must be resolved urgently.

**Investigation Path:**

**Step 1 — Identify all sources of gear signal:**
```
Primary:    TCM → GearPosition_BC (0x3A0)          10ms cycle
Backup:     BCM → GearStatus_Backup_BC (0x3A1)     500ms event-driven
Cluster reads primary first, falls back to backup on primary timeout.
```

**Step 2 — Timeout fallback issue:**
If the primary TCM gear message (0x3A0) has a timeout, the cluster falls back to BCM backup.
If BCM backup signal has a default/init value of P (Park = 0x00): cluster shows P while car is moving.

**Step 3 — Reproduce with CAN error injection:**
```capl
variables {
  message TCM_GearStatus_BC  msgTCM;
  message BCM_GearBackup_BC  msgBCM;
  msTimer tmrTest;
}

on start {
  // Set BCM backup to default Park
  msgBCM.GearPosition = 0x00;   // P = Park
  output(msgBCM);

  // Start sending car in Drive at 30 km/h
  message ABS_Speed_BC msgSpd;
  msgSpd.VehicleSpeed_raw = 3000;   // 30 km/h at 0.01 factor
  output(msgSpd);

  msgTCM.GearPosition = 0x03;   // Drive
  output(msgTCM);

  write("Phase 1: Normal — TCM sending Drive at 30 km/h");
  setTimer(tmrTest, 3000);
}

on timer tmrTest {
  // Phase 2: Stop TCM gear message — simulate timeout
  write("Phase 2: Stopping TCM gear message — cluster should NOT show P while moving!");

  // Stop outputting TCM message (set to deactivated)
  stopOutput(msgTCM);

  delay(1000);   // wait for cluster's timeout window

  int gearShown = getValue(Cluster::DisplayedGear);
  float speed   = getValue(Cluster::Speedometer_Display_kmh);

  write("After TCM timeout: Speed=%.1f km/h  Cluster shows gear=%d (0=P 3=D)", speed, gearShown);

  if (gearShown == 0 && speed > 5.0) {
    write("FAIL — SAFETY: Cluster shows PARK (P) while vehicle moving at %.1f km/h!", speed);
  } else if (gearShown == 3) {
    write("PASS — Cluster holds last valid gear (Drive) on TCM timeout");
  } else if (gearShown == 0xFF || gearShown == 7) {
    write("PASS — Cluster shows invalid/dash symbol on TCM timeout (not defaulting to Park)");
  }
}
```

**Step 4 — Safe fallback spec:**
The correct behaviour on TCM timeout while moving (speed > 5 km/h):
- Do NOT show Park
- Hold last valid gear for up to 2 seconds
- After 2 seconds: show '--' or 'F' (fault) indicator

**Test Cases:**
```
TC_GEAR_001: TCM sends D → cluster shows D
TC_GEAR_002: TCM sends P → vehicle speed 0 → cluster shows P (correct)
TC_GEAR_003: TCM timeout → vehicle speed > 5 km/h → cluster must NOT show P
TC_GEAR_004: TCM timeout → vehicle speed > 5 km/h → cluster shows last valid gear for 2s then '--'
TC_GEAR_005: TCM sending P while vehicle speed > 5 km/h (contradictory) → cluster shows warning
TC_GEAR_006: Rapid P→R→N→D→R (1 per 500ms) → cluster tracks every change within 200ms
```

**Root Cause Summary:**
Cluster timeout fallback logic reads BCM backup gear signal which initialises to Park (0x00) at ECU power-on and is only updated when the BCM sends an event-driven update. The BCM sends gear update only when gear changes — so the backup value stays as the initial P value from BCM boot. Fix: cluster must hold last valid TCM gear on timeout; the backup signal should only be used if the last known speed was 0 km/h (truly parked condition).

---

## Scenario 5 — Trip Computer Average Speed Shows 0 km/h Despite Driving

> **Interviewer:** "The trip computer displays Average Speed as 0.0 km/h even after driving 50 km over 45 minutes. How do you debug this calculation failure?"

**Background:**
Average speed = total distance / total time. If average speed = 0, either total distance = 0, total time = 0, or there is a divide-by-zero guard returning 0.

**Investigation Path:**

**Step 1 — Individual component check:**
```capl
on key 'c' {
  // Read all trip computer components from cluster
  float tripDist  = getValue(Cluster::Trip_A_Distance_km);
  float tripTime  = getValue(Cluster::Trip_A_Time_min);
  float avgSpeed  = getValue(Cluster::Trip_A_AvgSpeed_kmh);
  float calcSpeed = (tripTime > 0) ? (tripDist / (tripTime / 60.0)) : 0.0;

  write("Trip A:  Distance=%.1f km  Time=%.0f min  Display AvgSpeed=%.1f km/h",
        tripDist, tripTime, avgSpeed);
  write("Calculated AvgSpeed = %.1f km/h", calcSpeed);

  if (avgSpeed == 0.0 && calcSpeed > 0.0) {
    write("FAIL — Calculated=%.1f km/h but display shows 0 — calculation display bug", calcSpeed);
  } else if (tripTime == 0.0) {
    write("FAIL — Trip time = 0 → timer not incrementing → time counter bug");
  } else if (tripDist == 0.0) {
    write("FAIL — Trip distance = 0 → distance counter not incrementing");
  }
}
```

**Step 2 — Units mismatch:**
Average speed formula checks:
- If trip time is stored in seconds but code divides distance by minutes: result is 60× wrong (not 0)
- If distance is in metres but treated as km: result is 1000× too small (could display as 0.0 if rounded)

**Step 3 — Integer overflow / truncation:**
If average speed is computed as integer arithmetic:
```
avg_speed = (int)(distance_m / time_s * 3.6)
If distance_m = 50000, time_s = 2700:
  50000 / 2700 = 18 (integer division) × 3.6 = 64.8 → rounds to 64 ← correct
BUT:
  If distance_m is stored as uint16 and wraps after 65535m (65.5km): resets to 0 → avg = 0
```

**Step 4 — Stopped time inclusion:**
Average speed may exclude time the vehicle was stationary (traffic lights).
If the implementation excludes ALL time where speed < 5 km/h, but the first 5 km was in slow traffic:
`time_moving = total_time - stopped_time` = very small → average looks wrong

**Test Cases:**
```
TC_AVG_001: Drive 60 km in exactly 60 min at constant speed → avg speed = 60.0 ±1.0 km/h
TC_AVG_002: Drive 30 km, stop 10 min, drive 30 km in 30 min → avg speed based on spec (includes or excludes stops)
TC_AVG_003: Reset trip → drive 1 km → avg speed visible and plausible within 1 km
TC_AVG_004: Very long trip (200 km, 3 hours) → overflow check: avg speed correct, no reset to 0
TC_AVG_005: All trip fields reset to 0 when trip button held → avg speed shows 0.0 after reset
TC_AVG_006: Avg speed in km/h and mph (market variant) → correct unit display with unit label
```

**Root Cause Summary:**
Trip distance counter is stored as `uint16_t` in kilometres × 10 (one decimal place). Maximum value = 65535 → 6553.5 km before overflow. After a 6554 km trip without reset, the distance counter wrapped to 0 → average speed = 0./trip_time × ... This is a data type specification defect — the field should be `uint32_t` to support trips up to 429,496 km.

---
*File: 01_speed_rpm_display.md | Scenarios 1–5 | April 2026*
