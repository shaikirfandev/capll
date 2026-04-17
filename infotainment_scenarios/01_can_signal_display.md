# Scenarios 1–5 — CAN Signal & Cluster Display
## Infotainment Test Validation — Scenario-Based Interview Prep

---

## Scenario 1 — Odometer Jumps Backward After Ignition Cycle

> **Interviewer:** "A customer reports their odometer shows 45,230 km, they park the car, restart it the next day, and it shows 45,180 km — 50 km less than before. How do you investigate?"

**Background:**
Odometer data is stored in NVM (Non-Volatile Memory) in the cluster ECU. It is written periodically (every X km or every ignition OFF). A backward jump means either a corrupt NVM write or the cluster loaded an old backup instead of the latest value.

**Investigation Path:**

**Step 1 — Reproduce the issue:**
- Check if the rollback is always 50 km — consistent delta suggests a specific NVM slot issue
- Check if it only happens after a cold soak (temperature-dependent NVM write failure)

**Step 2 — NVM write timing:**
- The cluster writes odometer to NVM every 1 km (or on ignition OFF)
- If ignition OFF is abrupt (battery disconnect / crash) before the final write completes → NVM holds the last good value, which may be 50 km old
- Test: Drive exactly 50 km → cut power abruptly → restart → does odometer roll back?

**Step 3 — NVM backup slots:**
- Most clusters use two NVM slots + a checksum for redundancy
- If slot 1 checksum fails, system falls back to slot 2 (the older backup)
- Corrupt slot 1 = rollback to slot 2 age (could be 50 km difference)

**Step 4 — UDS diagnostic read:**
```
0x22 0xF1A0 → Odometer current value (manufacturer-specific DID)
0x22 0xF1A1 → NVM slot 1 odometer
0x22 0xF1A2 → NVM slot 2 odometer (backup)
Compare slot 1 vs slot 2 — is the gap 50 km?
```

**Step 5 — DTCs:**
```
0x19 02 08 → confirmed DTCs
Look for: B1010 (NVM write failure), B1011 (NVM checksum error)
```

**CAPL Script — Monitor odometer NVM write events:**
```capl
variables {
  dword gOdoLastValue = 0;
  dword gOdoCurrent  = 0;
}

on signal Cluster::Odometer_km {
  gOdoCurrent = (dword)this.value;
  if (gOdoCurrent < gOdoLastValue) {
    write("FAIL — Odometer DECREASED: was %d km, now %d km (delta=%d km)",
          gOdoLastValue, gOdoCurrent, gOdoLastValue - gOdoCurrent);
  } else {
    gOdoLastValue = gOdoCurrent;
    write("Odometer: %d km (+%d km)", gOdoCurrent, gOdoCurrent - gOdoLastValue);
  }
}
```

**Test Cases:**
```
TC_ODO_001: Drive 5 km → ignition OFF normally → restart → odometer shows correct +5 km
TC_ODO_002: Drive 5 km → cut power abruptly (simulate KL30 loss) → restart → odometer check
TC_ODO_003: Drive 50 km → normal shutdown → read UDS 0x22 NVM slot 1 and slot 2 → both equal
TC_ODO_004: 50 ignition cycles over 2 hours → odometer must not roll back at any cycle
TC_ODO_005: After battery disconnect (30 min) → odometer must retain value within 1 km
```

**Root Cause Summary:**
Most likely — NVM slot redundancy logic reads slot 2 (backup) instead of slot 1 (latest) when slot 1 checksum fails. The checksum failure may be caused by a power glitch during the write window. SW fix: increase NVM write frequency (every 0.1 km) or improve checksum algorithm.

---

## Scenario 2 — Warning Icon Stays ON After Fault is Cleared

> **Interviewer:** "The engine temperature warning icon stays illuminated on the cluster even after the engine has cooled down to normal temperature and the DTC has been cleared. What is the fault?"

**Background:**
Warning icons should extinguish when: (a) the fault condition is no longer present AND (b) the DTC is cleared or healed. If it stays on after both conditions are met, the cluster display logic has a bug.

**Investigation Path:**

**Step 1 — Confirm fault is actually gone:**
```
UDS 0x22 0x1001 → Engine coolant temperature → should read normal (< 95°C)
UDS 0x19 02 08  → Should return 0 DTCs (confirmed)
```

**Step 2 — Check CAN signal:**
- Is `EngineTemp_Warning_Active` CAN signal still = 1?
- If yes: the ECM is still broadcasting the warning flag even though temperature is normal
- ECM may have a hysteresis issue: warning sets at 115°C, should clear at 105°C — does it clear?

**Step 3 — Separate the signal from the display:**
```capl
// Monitor warning flag from ECM
on signal ECM::EngineOvertemp_Warning_Active {
  write("ECM OverTemp Warning Flag = %d", this.value);
}

// Monitor what cluster receives
on signal Cluster::Telltale_EngineTemp_State {
  write("Cluster EngineTemp Icon State = %d (0=OFF, 1=ON, 2=BLINK)", this.value);
}
```

If ECM flag = 0 but cluster icon = 1 → cluster is not clearing the display on signal deactivation → cluster SW bug (missing `if signal == 0 → clear icon` handler).

**Step 4 — NVM latch check:**
Some warning icons are latched in NVM and require a specific command to clear:
- Try UDS `0x2E 0x5100 0x00` (clear warning latch DID — manufacturer specific)
- Or: full cluster reset via `0x11 01` (ECU reset)

**Step 5 — Ignition cycle test:**
- Does the icon clear after ignition OFF → ON cycle?
- If yes: the cluster correctly re-evaluates on boot but fails to update during runtime

**Test Cases:**
```
TC_WARN_001: Inject engine temp = 120°C → icon ON → reduce to 90°C → icon OFF within 2s
TC_WARN_002: Inject engine temp = 120°C → clear DTC 0x14 → icon must still show until temp reduces
TC_WARN_003: Inject engine temp = 120°C → reduce to 90°C → icon OFF → inject again → icon ON again (no latch)
TC_WARN_004: Inject engine temp → clear → ignition cycle → icon must be OFF on restart
TC_WARN_005: All 15 warning icons — each must extinguish within 2 seconds of fault removal
```

**Root Cause Summary:**
Two possible causes: (1) ECM hysteresis bug — warning flag not de-asserted correctly. (2) Cluster rendering bug — flag goes to 0 on CAN but cluster icon not updated until next full refresh cycle. Check cluster refresh rate — if it only updates icon state every 500ms and the signal de-asserts between refresh cycles, icon stays on until next refresh.

---

## Scenario 3 — Gear Display Shows Wrong Gear in Automatic Transmission

> **Interviewer:** "The cluster gear indicator shows 'N' (Neutral) while the car is clearly in 'D' (Drive) and moving. How do you debug this?"

**Background:**
The gear display reads from a CAN signal typically sent by the TCM (Transmission Control Module). Mismatch between physical gear and displayed gear means either wrong signal, wrong decoding, or wrong source.

**Investigation Path:**

**Step 1 — Confirm physical gear via OBD-II:**
```
UDS 0x01 0x0A (Mode 1, PID 0x0A — not standard for gear, but manufacturer-specific)
Or: UDS 0x22 [TCM DID for current gear] → confirm TCM reports Drive (D)
```

**Step 2 — Check CAN message:**
```capl
on message TCM::GearStatus_BC {
  write("TCM Gear: Actual=%d  Target=%d  Mode=%d",
        this.TCM_CurrentGear,
        this.TCM_TargetGear,
        this.TCM_ShiftMode);
}
```
- Is `TCM_CurrentGear` showing Drive (e.g., value = 3) or Neutral (value = 1)?
- If TCM sends Drive but cluster shows Neutral → cluster decoding is wrong

**Step 3 — Signal decoding check:**
Gear signal is often encoded:
```
0x00 = Park
0x01 = Reverse
0x02 = Neutral
0x03 = Drive
0x04 = Sport
0x05 = Low
```
If cluster DBC has old encoding (0x03 = Neutral instead of 0x03 = Drive) → wrong label shown.

**Step 4 — Multiplexed signal check:**
Gear info may be inside a multiplexed message. If cluster reads wrong Mux ID, it reads from the wrong signal slot.

**Step 5 — Simultaneous signals test:**
Some vehicles send gear from both TCM (primary) and BCM (backup). If BCM signal shows Neutral (e.g., ignition cold start default) and cluster is using BCM instead of TCM → displays N.

**CAPL Automated Test:**
```capl
variables {
  message GearShift_Req msgGear;
  int testGears[5] = {0, 1, 2, 3, 4};   // P, R, N, D, S
  char gearLabels[5][2] = {"P","R","N","D","S"};
  int gIdx = 0;
  msTimer tmrGear;
  int gPass = 0, gFail = 0;
}

on start { setTimer(tmrGear, 1000); }

on timer tmrGear {
  if (gIdx >= 5) {
    write("=== Gear Display: PASS=%d FAIL=%d ===", gPass, gFail);
    stop(); return;
  }
  msgGear.GearPosition = testGears[gIdx];
  output(msgGear);
  delay(500);

  int displayed = getValue(Cluster::DisplayedGear);
  if (displayed == testGears[gIdx]) {
    write("PASS — Gear %s displayed correctly", gearLabels[gIdx]);
    gPass++;
  } else {
    write("FAIL — Gear %s: sent=%d displayed=%d", gearLabels[gIdx], testGears[gIdx], displayed);
    gFail++;
  }
  gIdx++;
  setTimer(tmrGear, 800);
}
```

**Test Cases:**
```
TC_GEAR_001: TCM sends P (0x00) → cluster displays 'P'
TC_GEAR_002: TCM sends R (0x01) → cluster displays 'R' + reverse camera activates
TC_GEAR_003: TCM sends N (0x02) → cluster displays 'N'
TC_GEAR_004: TCM sends D (0x03) → cluster displays 'D'
TC_GEAR_005: Rapid shift P→R→N→D in 1s each → cluster keeps up with no lag > 500ms
TC_GEAR_006: TCM CAN message timeout (stop sending) → cluster shows last valid gear or '--'
```

**Root Cause Summary:**
Most likely a DBC update mismatch after a TCM SW change — TCM changed gear encoding values but cluster DBC was not updated. Always ensure cluster and TCM DBC files are versioned together and validated jointly after any TCM SW release.

---

## Scenario 4 — Battery Voltage Shows 0V on Driver Information Display

> **Interviewer:** "The Driver Information Display shows battery voltage as 0.0V but all electrical systems are working fine. How do you approach this?"

**Background:**
Battery voltage is typically measured by the BCM (Body Control Module) or BMS (Battery Management System) and transmitted over CAN to the cluster/IVI for display.

**Investigation Path:**

**Step 1 — Confirm actual battery voltage is fine:**
- Multimeter on battery terminals → should read 12.5–14.5V (engine running)
- Vehicle clearly powering normally → hardware battery is fine

**Step 2 — Check CAN signal:**
```capl
on message BCM::BatteryStatus_BC {
  write("BCM Battery: Voltage=%.2fV  Current=%.1fA  SOC=%d%%",
        this.Batt_Voltage_V,
        this.Batt_Current_A,
        this.Batt_SOC_Pct);
}
```
- If `Batt_Voltage_V` = 0.0 on CAN → BCM is sending 0 (signal stuck at default/init value)
- If `Batt_Voltage_V` = 12.8 on CAN but display shows 0 → cluster signal decoding error

**Step 3 — Signal scaling:**
Voltage often encoded as: `physical = raw × 0.1V`
If raw = 128 → physical = 12.8V correct
If scaling changed to `raw × 0.001V` → 128 × 0.001 = 0.128V → rounds to 0.0 on display

**Step 4 — DTC check on BCM:**
```
UDS 0x19 02 08 on BCM → is there a voltage sensor DTC?
B2200 = Battery voltage sensor fault → BCM transmitting default 0V
```

**Step 5 — Signal timeout / substitute value:**
Some systems: if voltage sensor fails DTC → BCM sends 0.0V as substitute value
Display shows 0.0V correctly representing "sensor fault"
Fix: show '---' instead of '0.0V' when sensor DTC is present

**Test Cases:**
```
TC_BATT_001: BCM sends 12.5V → cluster displays 12.5V (±0.1V tolerance)
TC_BATT_002: BCM sends 14.2V (charging) → cluster shows 14.2V
TC_BATT_003: BCM sends 11.8V (low) → cluster shows 11.8V + low battery warning icon
TC_BATT_004: BCM CAN message timeout → cluster shows '---' or last valid (not '0.0V')
TC_BATT_005: BCM sends 0.0V explicitly → cluster shows '---' or fault indicator (not 0.0V as valid)
```

**Root Cause Summary:**
If BCM sends 0.0V: BCM voltage sensor DTC — sensor circuit fault or BCM calibration issue.
If CAN shows correct voltage but display shows 0: cluster DBC scaling mismatch after SW update.
If CAN message missing: BCM not initialised yet during early boot — display shows init value (0) and never updates.

---

## Scenario 5 — Trip Computer Resets Unexpectedly

> **Interviewer:** "Customers report their trip computer (average fuel consumption, distance, time) resets to zero randomly — not just on a new trip. How do you investigate?"

**Background:**
Trip computer data is stored in cluster NVM and reset either by: user action (hold trip button), new ignition cycle (if configured), or NVM fault. Random reset means an unintended trigger.

**Investigation Path:**

**Step 1 — Identify reset pattern:**
- Does it correlate with a specific driver action? (phone call, media interaction, speed bump?)
- Does it happen at a specific distance or time interval?
- Does it happen across all vehicles or only one specific build variant?

**Step 2 — CAN message monitor:**
Some IVI systems send a "Trip Reset" CAN message that the cluster obeys.
Check if any CAN message with a trip reset flag is being asserted:
```capl
on message * {
  // Scan all messages for trip-reset-related signals
  if (this.TripReset_Req == 1) {
    write("TRIP RESET message received! ID=0x%X  time=%d ms", this.id, timeNow()/10);
  }
}
```

**Step 3 — Steering wheel button ghost presses:**
Some vehicles: LIN-connected steering wheel buttons send trip reset on long press.
If LIN signal has noise (resistor ageing, connector oxidation) → phantom button press → trip reset.
Test: disconnect steering wheel LIN module → does random reset stop?

**Step 4 — Power supply glitch:**
A momentary voltage dip (< 9V spike from heavy load: AC compressor, starter relay) can cause the cluster to briefly reset.
Monitor supply voltage on oscilloscope during suspected reset events.

**Step 5 — SW race condition:**
In multithreaded cluster SW: if two threads simultaneously access the NVM trip register (one reading, one writing ignition-cycle data), a corrupted write can reset values.
This type of bug appears randomly and is hard to reproduce.

**CAPL Test — Simulate conditions that may trigger reset:**
```capl
variables {
  message SteeringWheel_LIN  msgSW;
  message BCM_PowerStatus_BC msgPower;
  msTimer tmrStress;
  int gCycle = 0;
}

on start {
  // Read initial trip distance
  float tripDist = getValue(Cluster::Trip_A_Distance_km);
  write("Initial Trip A = %.1f km — starting stress test", tripDist);
  setTimer(tmrStress, 1000);
}

on timer tmrStress {
  gCycle++;
  // Simulate various stressors
  switch(gCycle % 4) {
    case 0: // AC compressor load spike
      msgPower.BattVoltage = 110;  // 11.0V dip
      output(msgPower);
      delay(50);
      msgPower.BattVoltage = 138;  // back to 13.8V
      output(msgPower);
      break;
    case 1: // Steering wheel button noise
      msgSW.HornButton = 1;
      output(msgSW);
      delay(20);
      msgSW.HornButton = 0;
      output(msgSW);
      break;
    case 2: // Multiple ignition cycles
      // simulate cluster re-init signal
      break;
  }

  float tripNow = getValue(Cluster::Trip_A_Distance_km);
  if (tripNow == 0) {
    write("FAIL [Cycle %d] Trip computer RESET to 0!", gCycle);
  }

  if (gCycle < 100) setTimer(tmrStress, 500);
  else write("Stress test complete — no reset detected");
}
```

**Test Cases:**
```
TC_TRIP_001: Long press trip button for exactly 3s → trip resets (correct intentional reset)
TC_TRIP_002: Short press trip button (< 1s) → trip does NOT reset (unintended reset guard)
TC_TRIP_003: 50 ignition cycles without pressing trip button → trip value preserved
TC_TRIP_004: Simulate 11.0V supply dip for 50ms → trip value preserved
TC_TRIP_005: Simulate steering wheel LIN disconnect/reconnect 10 times → trip not reset
TC_TRIP_006: After battery disconnect (30 min) → trip resets to 0 is acceptable (document in spec)
```

**Root Cause Summary:**
Most common: LIN noise causing phantom steering wheel button long press → triggers intentional reset path. Second most common: voltage dip during ignition cycling causing cluster to execute cold boot (not warm restart), which initialises trip registers.

---
*File: 01_can_signal_display.md | Scenarios 1–5 | April 2026*
