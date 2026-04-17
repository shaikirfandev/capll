# Scenarios 26–30 — Startup, Shutdown, NVM & Stress
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 26 — Cluster Gauge Sweep Animation Plays Twice on Every Cold Start

> **Interviewer:** "The gauge sweep animation (needle theatre) plays normally once during cold start. On certain cold morning starts it plays twice — the needles sweep up, return to zero, then sweep up again before finally settling at live data. What causes a double sweep?"

**Background:**
Gauge sweep is a deliberate animation played once after ignition ON. A double sweep means the animation trigger condition fires twice. This could be a software init sequence issue, or a KL15 bounce (brief power loss and restoration giving two start events).

**Investigation Path:**

**Step 1 — KL15 signal analysis:**
```capl
variables {
  int   gKL15_transitions = 0;
  dword tKL15_ON_first    = 0;
  dword tKL15_ON_last     = 0;
}

on signal PowerSupply::KL15_Active {
  int state = (int)this.value;
  gKL15_transitions++;
  dword now = timeNow() / 10;
  write("[%d ms] KL15 transition #%d → %d", now, gKL15_transitions, state);

  if (state == 1) {
    if (tKL15_ON_first == 0) {
      tKL15_ON_first = now;
    } else {
      tKL15_ON_last = now;
      write("SECOND KL15 ON event at %d ms (delta=%d ms from first) — possible bounce!",
            now, now - tKL15_ON_first);
    }
  }
}

on signal Cluster::GaugeSweep_Active {
  write("[%d ms] Gauge sweep: %d (1=playing)", timeNow()/10, (int)this.value);
}
```

**Step 2 — KL15 bounce on cold morning:**
At low temperatures:
- Ignition switch contact resistance increases (dirty/cold contacts)
- Brief interruption in KL15 (10–50ms) during key turn
- Cluster software treats 50ms KL15 loss + recover as a full ignition cycle → plays sweep again

**Step 3 — Debounce threshold:**
Cluster should debounce KL15:
- A KL15 loss shorter than 200ms should NOT trigger a new ignition cycle
- If debounce threshold = 50ms: a 60ms bounce at −15°C triggers double sweep
- Fix: increase KL15 debounce to 300ms

**Step 4 — ECM confirmation:**
The cluster could require ECM confirmation of ignition state instead of relying solely on KL15 voltage:
```capl
// More robust: check both KL15 AND ECM ignition status signal
on signal ECM::IgnitionStatus {
  // 0=off 1=accessory 2=run 3=crank
  if (this.value == 2 && getValue(PowerSupply::KL15_Active) == 1) {
    write("Confirmed ignition RUN — safe to play gauge sweep");
  }
}
```

**Test Cases:**
```
TC_SWEEP_001: Cold start (−20°C) → gauge sweep plays exactly once
TC_SWEEP_002: Warm start → gauge sweep plays exactly once
TC_SWEEP_003: KL15 bounce 30ms → sweep plays once (bounce ignored below 200ms debounce)
TC_SWEEP_004: KL15 bounce 400ms → second ignition cycle acknowledged → sweep plays twice (correct response to genuine second cycle)
TC_SWEEP_005: Gauge sweep must complete before live ECM data is displayed (no data-sweep mix)
TC_SWEEP_006: 100 cold start cycles at −20°C → double sweep count = 0
```

**Root Cause Summary:**
At −15°C and below, the ignition barrel KL15 contact experienced a 65ms bounce as the copper contacts cooled and contracted slightly between the ON detent and full ON position. The cluster's KL15 debounce was set to 50ms — just shorter than the 65ms bounce. Increasing the debounce to 200ms eliminated the double sweep without perceptibly delaying normal ignition response.

---

## Scenario 27 — Cluster NVM Corruption After Battery Disconnect During Drive

> **Interviewer:** "A vehicle's battery was disconnected while driving (maintenance error). When reconnected, the cluster shows: odometer reset to 0, all user settings (brightnes, language) lost, and trip computer cleared. This is partially expected after power loss, but is it all correct behaviour?"

**Background:**
Some data loss after unexpected power removal is expected. The question is: which data should be preserved (must be in NVM with proper write completion) and which data can be lost (acceptable to lose on power cut).

**Investigation Path:**

**Step 1 — Data classification:**
```
MUST SURVIVE power cut:                    ACCEPTABLE to lose on power cut:
  Odometer (legal mileage record)            Trip computer
  VIN / vehicle identification               Instantaneous fuel economy
  ECU serial number                          Short-term user preferences
  Calibration data                           Menu cursor position
  DTC history

If odometer is lost: this is a regulatory compliance failure
If trip computer is lost: this is acceptable (user preference data)
```

**Step 2 — NVM write strategy for odometer:**
Correct implementation:
- Odometer in EEPROM (byte-level writable, survives power cut)
- Written every 1 km AND on every ignition OFF
- Checksummed: if checksum fails on next boot → rollback to last valid backup
- Two copies: primary + backup (different NVM addresses)

**Step 3 — Investigate the reset to 0:**
```capl
on start {
  // After reconnecting battery, read all NVM-backed odometer data
  dword odo_display   = getValue(Cluster::Odometer_Display_km);
  dword odo_nvm       = readNVM(0x0100);   // NVM address for primary odometer
  dword odo_backup    = readNVM(0x0200);   // NVM backup
  byte  odo_checksum  = readNVM(0x0104);
  byte  calc_checksum = calculateChecksum(odo_nvm);

  write("Display ODO:   %d km", odo_display);
  write("NVM Primary:   %d km  Checksum=%02X (calculated=%02X) %s",
        odo_nvm, odo_checksum, calc_checksum,
        (odo_checksum == calc_checksum) ? "✓VALID" : "✗CORRUPTED");
  write("NVM Backup:    %d km", odo_backup);

  if (odo_nvm == 0 && odo_backup == 0) {
    write("FAIL — Both NVM copies are 0 — incomplete NVM initialisation or corruption");
  } else if (odo_display == 0 && odo_nvm > 0) {
    write("FAIL — ODO display reads 0 but NVM had valid data — display not reading NVM on boot");
  }
}
```

**Step 4 — Failure mode analysis:**
If both primary AND backup NVM = 0:
1. The battery was disconnected during an NVM write → partially written → checksum fails → primary invalidated
2. Fallback to backup → but backup was ALSO being written at that exact time (rare but possible if both updated simultaneously) → backup also invalid
3. Both invalid → system initialises odometer to 0 (default) → reset appearance

Fix: stagger primary and backup NVM writes by minimum 5 seconds.

**Test Cases:**
```
TC_NVM_001: Battery disconnect at any point during drive → odometer recovers to within 5 km on restart
TC_NVM_002: Battery disconnect during ignition OFF NVM write → primary invalid → backup used → odo within 10 km
TC_NVM_003: Both NVM copies corrupted → cluster shows 'NVM Error' and retains last readable value, not 0
TC_NVM_004: Battery reconnect → language/brightness settings lost is acceptable
TC_NVM_005: Battery reconnect → VIN, variant coding, ECU serial number intact
TC_NVM_006: 100 random power cut cycles → odometer never resets to 0
```

**Root Cause Summary:**
The primary and backup odometer NVM writes were staggered by only 50ms. During a power cut, both writes were in-flight simultaneously (a 50ms window where both are being written). Power cut corrupted both. Fix: stagger to 30 seconds minimum. Also added a third NVM copy written only on ignition OFF (not every km) as a "last known good" fallback for extreme cases.

---

## Scenario 28 — Cluster Display Brightness Cycles Between Max and Min Every 2 Seconds

> **Interviewer:** "The cluster display brightness cycles from maximum to minimum and back, every 2 seconds, continuously. The auto-brightness setting is ON. No button is being pressed. How do you debug an oscillating auto-brightness?"

**Background:**
Oscillating brightness is a closed-loop control issue — the auto-brightness control loop is unstable. This is a classic control system problem: the feedback gain is too high, causing the system to overshoot and oscillate.

**Investigation Path:**

**Step 1 — Confirm auto-brightness is the cause:**
Disable auto-brightness → does oscillation stop?
If yes: the auto-brightness control loop is the issue.
If no: hardware PWM driver fault or ambient light sensor fault.

**Step 2 — Ambient light sensor reading:**
```capl
on signal BCM::AmbientLight_lux {
  float lux = this.value;
  float pwm = getValue(Cluster::Backlight_PWM_Pct);
  write("[%d ms] Ambient=%.0f lux → Backlight=%.0f%%", timeNow()/10, lux, pwm);
}
```
- Is the ambient lux reading oscillating? → sensor issue (e.g., cluster's backlight leaking onto the ambient sensor → as brightness increases, sensor sees more light, reduces brightness, sensor sees less light, increases brightness → oscillation)
- Is lux stable but brightness oscillating? → control algorithm issue

**Step 3 — Feedback loop analysis:**
Physical cause of oscillation: cluster backlight visible to the ambient light sensor.
```
Brightness HIGH → backlight light leaks to sensor → sensor reads HIGH lux → target brightness = LOW
Brightness LOW  → less leak → sensor reads LOW lux → target brightness = HIGH
Repeat at the response delay cycle time
```
Period of oscillation = 2× the control loop update delay.

**Step 4 — Control algorithm fix:**
```
Option A: Add low-pass filter on ambient sensor reading (rolling average over last 5s)
Option B: Add deadband: only update brightness if ambient lux changes by ± 50 lux
          (prevents chasing minor variations)
Option C: One-way filter: brightness can increase quickly but can only DECREASE slowly
          (rate limiter: max decrease rate = 2% per second)
```

**CAPL Stability Test:**
```capl
variables {
  float gBrightness_prev  = 0.0;
  int   gOscillations     = 0;
  int   gDirection_prev   = 0;    // 1=increasing -1=decreasing
}

on signal Cluster::Backlight_PWM_Pct {
  float b = this.value;
  float delta = b - gBrightness_prev;

  int direction = (delta > 0.5) ? 1 : (delta < -0.5) ? -1 : 0;

  // Count direction reversals
  if (direction != 0 && direction != gDirection_prev && gDirection_prev != 0) {
    gOscillations++;
    write("Direction reversal #%d at %.0f%% (was %.0f%%)  Δ=%.1f%%",
          gOscillations, b, gBrightness_prev, delta);
  }

  if (gDirection_prev != 0)
    gDirection_prev = direction;
  gBrightness_prev = b;
}

// After 60 seconds of measurement
on key 's' {
  write("Brightness oscillation reversals in 60s: %d", gOscillations);
  write(gOscillations < 5 ? "PASS — Stable brightness control"
                          : "FAIL — Unstable oscillating brightness control");
}
```

**Test Cases:**
```
TC_BRIGHT_001: Constant ambient light → backlight stable at one value for 60 seconds (≤ 5 oscillations)
TC_BRIGHT_002: Ambient changes from dark to bright → brightness adjusts smoothly over 5–10 seconds
TC_BRIGHT_003: Cover ambient sensor (simulate night) → brightness reduces to minimum within 30 seconds
TC_BRIGHT_004: Remove cover (simulate day) → brightness increases within 10 seconds
TC_BRIGHT_005: Auto-brightness off → manual brightness set to 50% → stays at 50% indefinitely
TC_BRIGHT_006: Brightness change rate: must not change faster than 5% per second in auto mode
```

**Root Cause Summary:**
Ambient light sensor was positioned adjacent to the cluster (behind the instrument panel surround) but the cluster backlight leakage illuminated the sensor's field of view. The auto-brightness update interval (2 Hz) combined with the leakage feedback loop created a 2-second oscillation cycle. Fix: (1) add physical light trap around ambient sensor, (2) add 10-lux deadband to brightness control, (3) rate-limit brightness decrease to 2% per second to prevent visible oscillation even if minor feedback is present.

---

## Scenario 29 — Cluster Reboots When High-Load Features Are Activated Simultaneously

> **Interviewer:** "When a driver activates navigation, full-brightness display, maximum fan speed, and makes a phone call all within a few seconds, the cluster occasionally reboots (black screen for 2 seconds). How do you investigate a simultaneous load crash?"

**Background:**
Multiple high-load features together can:
1. Cause a supply voltage dip that triggers the cluster's undervoltage reset
2. Cause CPU overload in the cluster (if cluster renders ADAS overlays during nav + media)
3. Cause a CAN bus congestion spike that triggers watchdog

**Investigation Path:**

**Step 1 — Supply voltage monitoring:**
```capl
variables {
  float gVoltage_min = 99.0;
  dword tCrash       = 0;
}

on signal BCM::SupplyVoltage_V {
  float v = this.value;
  if (v < gVoltage_min) gVoltage_min = v;

  if (v < 9.5) {
    tCrash = timeNow() / 10;
    write("[%d ms] UNDERVOLTAGE: %.2fV — cluster reset likely!", tCrash, v);
  }
}

on signal Cluster::ClusterPowerState {
  if (this.value == 0 && tCrash > 0 && (timeNow()/10 - tCrash) < 500) {
    write("CONFIRMED: Cluster reset occurred %d ms after undervoltage event", timeNow()/10 - tCrash);
  }
}
```

**Step 2 — Simultaneous load current draw:**
```
Navigation (GPU active):           +1.5A @12V = 18W
Full brightness:                   +0.8A @12V = 9.6W
Fan motor speed increase:          +3.0A @12V = 36W  ← large jump
Phone call (Bluetooth TX power):   +0.2A @12V = 2.4W
Total instantaneous spike:         +5.5A = 66W

Wiring harness gauge: if harness is 0.75mm² (rated 8.75A), total load margin is very small.
Combined with battery at slightly low charge → voltage dip when fan motor starts.
```

**Step 3 — Cluster undervoltage threshold:**
Cluster reset threshold: typically 9.0–9.5V for 50ms
If voltage dips to 9.2V for 60ms when all loads activate: cluster resets.

**Step 4 — Sequence of activation:**
The fan speed increase is the key trigger. Fan motor inrush current is 3× steady-state.
If fan goes from 1 to maximum directly (no ramp): inrush = 9A for 200ms.
If this occurs while other loads are already drawing: total = 14A → voltage drop across harness resistance = 14A × 0.15Ω = 2.1V → 14.2 − 2.1 = 12.1V (fine) OR 12.0 − 2.1 = 9.9V at marginal battery → below cluster reset threshold.

**Step 5 — Fix options:**
1. Fan motor soft-start ramp (0→max over 2 seconds instead of instant) — reduces inrush
2. Load shedding: if battery below 12V, cap fan to 70% during initial 3 seconds
3. Cluster reset threshold: review if 9.5V is appropriate or can be lowered to 8.5V

**Test Cases:**
```
TC_STRESS_001: Activate all high-load features within 2 seconds → cluster must not reset
TC_STRESS_002: Monitor supply voltage during stress activation → must not drop below 10V
TC_STRESS_003: Fan from 1→maximum instantly → voltage dip < 1.5V (harness validation)
TC_STRESS_004: Battery at 11.8V (weak battery), activate all loads → cluster stable
TC_STRESS_005: 50 activation cycles → 0 cluster reboots
TC_STRESS_006: Cluster reset (if it occurs) → time to return to operational state < 5 seconds
```

**Root Cause Summary:**
Fan motor drives directly to maximum from a CAN command with no soft-start ramp. At 6°C ambient temperature with a two-year-old battery (internal resistance increased), the combined inrush caused a 180ms voltage dip to 9.1V → below the cluster's 9.5V/50ms undervoltage reset threshold. Fix: (1) implement fan motor soft-start ramp from current speed to target over 1.5 seconds, (2) lower cluster undervoltage reset threshold from 9.5V to 8.5V (still within cluster hardware spec) to provide more margin.

---

## Scenario 30 — Cluster Shows Stale Data for 3 Seconds After Ignition ON

> **Interviewer:** "When the ignition is turned on, the cluster shows yesterday's trip computer data, last saved GPS position, and previous session's audio source for approximately 3 seconds before the display updates. Customers notice the old data briefly and find it confusing. How do you validate and fix this?"

**Background:**
The cluster boots and immediately renders the last NVM-saved state before receiving live CAN data. The 3-second window is the time between cluster OS boot completion and all CAN subsystems providing fresh data.

**Investigation Path:**

**Step 1 — Boot timeline analysis:**
```capl
variables {
  dword tKL15_ON        = 0;
  dword tFirstValidData = 0;
  dword tLastStaleData  = 0;
  int   gLiveDataReceived = 0;
}

on sysvar SysVar::KL15_State {
  if (@SysVar::KL15_State == 1) {
    tKL15_ON = timeNow() / 10;
    write("[%d ms] KL15 ON — cluster boot started", tKL15_ON);
  }
}

on signal ECM::EngineRPM {
  if (!gLiveDataReceived) {
    gLiveDataReceived = 1;
    tFirstValidData = timeNow() / 10;
    write("[%d ms] FIRST valid ECM data received — %d ms after KL15",
          tFirstValidData, tFirstValidData - tKL15_ON);
  }
}

on signal Cluster::TripComputer_Displayed {
  // Check if displayed data matches current session or previous
  float displayedFuel = getValue(Cluster::Trip_FuelUsed_L);
  if (displayedFuel > 0 && !gLiveDataReceived) {
    tLastStaleData = timeNow() / 10;
    write("[%d ms] Stale trip data still displayed (%d ms after KL15)",
          tLastStaleData, tLastStaleData - tKL15_ON);
  }
}
```

**Step 2 — Solution: show placeholder until data is live:**
Valid approaches for the 3-second gap:
1. **Splash screen**: show OEM logo / animation for 3 seconds, hiding all data displays
2. **Data-valid flag**: cluster only renders data when `DataValid_Flag = 1` received from each source ECU
3. **Animated transition**: fade in cluster data when first valid signals received (smooth appearance)
4. **Blank fields**: show "---" in all data fields until first valid data received for each signal

**Step 3 — Per-signal data-valid flags:**
Many modern CAN signals include an `Init_Indicator` bit:
```capl
on message ECM::EngineData_BC {
  byte init  = this.ECM_Init_Complete;   // 0=initialising 1=data valid
  float rpm  = this.Engine_RPM;

  if (init == 1) {
    write("ECM data VALID — RPM=%.0f", rpm);
    // cluster can now display RPM from ECM
  } else {
    write("ECM still initialising — show placeholder for RPM field");
  }
}
```

**Step 4 — Comprehensive startup display validation:**
```capl
variables {
  dword tKL15 = 0;
  // Track when each data source goes valid
  int gECM_valid     = 0;
  int gABS_valid     = 0;
  int gBCM_valid     = 0;
  int gTCM_valid     = 0;
  int gAll_valid     = 0;
}

on sysvar SysVar::KL15_State {
  if (@SysVar::KL15_State == 1) tKL15 = timeNow() / 10;
}

on signal ECM::ECM_Init_Complete { if (this.value == 1 && !gECM_valid) { gECM_valid = 1; write("[%d ms] ECM ready", timeNow()/10 - tKL15); } checkAllValid(); }
on signal ABS::ABS_Init_Complete { if (this.value == 1 && !gABS_valid) { gABS_valid = 1; write("[%d ms] ABS ready", timeNow()/10 - tKL15); } checkAllValid(); }
on signal BCM::BCM_Init_Complete { if (this.value == 1 && !gBCM_valid) { gBCM_valid = 1; write("[%d ms] BCM ready", timeNow()/10 - tKL15); } checkAllValid(); }
on signal TCM::TCM_Init_Complete { if (this.value == 1 && !gTCM_valid) { gTCM_valid = 1; write("[%d ms] TCM ready", timeNow()/10 - tKL15); } checkAllValid(); }

void checkAllValid() {
  if (gECM_valid && gABS_valid && gBCM_valid && gTCM_valid && !gAll_valid) {
    gAll_valid = 1;
    dword allReadyTime = timeNow()/10 - tKL15;
    write("ALL subsystems valid at %d ms — cluster can now display live data", allReadyTime);
    if (allReadyTime <= 3000) {
      write("PASS — All data valid within 3 seconds of KL15");
    } else {
      write("FAIL — Data ready time %d ms exceeds 3 second target", allReadyTime);
    }
  }
}
```

**Test Cases:**
```
TC_STALE_001: KL15 ON → cluster must not show previous session trip data after 3 seconds
TC_STALE_002: KL15 ON → all gauge fields show placeholder ('---' or animation) until ECM data valid
TC_STALE_003: Navigation last position → must show current position (new GPS fix) within 60 seconds
TC_STALE_004: Audio source from previous session not pre-selected on new session (user must select)
TC_STALE_005: 0–3 seconds after KL15: no numerically misleading data displayed (either placeholder or live)
TC_STALE_006: All init-valid flags from all ECUs declared within 3000ms of KL15 ON
```

**Root Cause Summary:**
The cluster rendered whatever was in its NVM immediately on boot (to show "something" quickly) without waiting for ECU valid flags. This was intentional for fast visual appearance but the spec never defined how long stale data was acceptable to display. The fix adds a maximum stale-display window: after 500ms of KL15, if live ECM data has not arrived, all data fields switch to placeholder symbols. When ECM/ABS/BCM all send their `Init_Complete = 1` signal, the placeholders are replaced atomically with the first live data — ensuring no brief flash of stale values.

---
*File: 09_startup_shutdown_stress.md | Scenarios 26–30 | April 2026*
