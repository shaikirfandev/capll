# Scenarios 6–10 — Warning Icons & Telltale Logic
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 6 — Check Engine Light Stays ON After ECM Confirms No Active Fault

> **Interviewer:** "The MIL (Malfunction Indicator Lamp / Check Engine Light) is illuminated on the cluster. You clear all DTCs with a scan tool and confirm zero active faults on the ECM. The MIL stays ON. What is happening?"

**Background:**
The MIL has specific OBD-II-mandated persistence rules. Clearing DTCs does not immediately extinguish the MIL — the ECM diagnostic monitors must run and confirm no fault across the required number of drive cycles.

**Investigation Path:**

**Step 1 — OBD-II MIL persistence rules (ISO 15031-6):**
```
After DTC clear (0x14):
  1. DTC removed from confirmed list ✓
  2. Monitor status = "not yet run since clear"
  3. MIL remains ON until:
     a. The monitor runs AND returns PASS in the same drive cycle, OR
     b. 3 consecutive drive cycles with no fault detected (for non-continuous monitors)
```
This is not a bug — this is legal compliance.

**Step 2 — Distinguish OBD-II MIL from manufacturer warning lamp:**
Some vehicles have both:
- `MIL_OBD` — amber engine icon, follows OBD-II healing rules
- `EngineWarning_OEM` — separate OEM warning, may have different rules
Confirm which icon is staying on.

**Step 3 — Monitor readiness check:**
```capl
// Check OBD-II monitor readiness status
// Mode 0x01 PID 0x41 = Monitor Status Since DTCs Cleared
on diagResponse ECM.ReadData_Mode01 {
  byte monitorStatus = diagGetRespPrimitiveByte(this, "MonitorStatusByte");
  // Bit 5: MIL status (1 = MIL commanded ON)
  // Bits 0-4: monitor readiness flags (0 = complete, 1 = not complete)

  write("OBD Monitor Status Byte: 0x%02X", monitorStatus);
  if (monitorStatus & 0x20) {
    write("MIL commanded ON by ECM — monitor not yet confirmed clean");
  } else {
    write("MIL commanded OFF — display issue if cluster still shows MIL");
  }
}
```

**Step 4 — If ECM commands MIL=OFF but cluster still shows it:**
This is a cluster rendering bug. Cluster receiving `MIL_State=0` but not updating the icon.
Check: debounce timer in cluster (if cluster requires MIL=0 for 500ms before clearing icon).

**Step 5 — Drive cycle completion:**
Request ECM to force complete monitored drive cycle:
```
UDS Mode 0x06 → On-Board Monitoring Test Results
All monitors must show PASS flag before MIL clears
```

**Test Cases:**
```
TC_MIL_001: Inject ECM MIL request = 1 → MIL illuminates within 1 second
TC_MIL_002: De-assert MIL request → MIL clears after next passing monitor run (1–3 drive cycles)
TC_MIL_003: MIL request = 0 for 1 second → cluster clears MIL icon within 1 second
TC_MIL_004: MIL blink request (severe fault) → MIL blinks at 2 Hz
TC_MIL_005: 3 drive cycles with no fault → MIL clears (OBD-II healing confirmed)
TC_MIL_006: MIL and Battery warning ON simultaneously → both icons visible, no suppression
```

**Root Cause Summary:**
In this case, the MIL was staying on because the cluster had a 1-second debounce gate before clearing the icon (to prevent flicker during early drive cycle). But combined with the OBD-II drive cycle requirement, the total persistence exceeded the customer's expectation. The cluster SW was updated to immediately clear the MIL icon the moment the ECM signals `MIL_Request=0`, separating the OBD-II drive cycle logic (ECM's responsibility) from the icon display logic (cluster's responsibility).

---

## Scenario 7 — Oil Pressure Warning Flickering at Idle

> **Interviewer:** "The low oil pressure warning lamp flickers on and off rapidly at idle. At higher RPM (>1500) it is solid OFF. At idle it flickers. Is this a sensor problem, an oil pressure problem, or a cluster problem?"

**Background:**
Oil pressure at idle is genuinely lower than at higher RPM — this is normal physics. The question is whether the pressure is briefly dipping below the warning threshold at idle.

**Investigation Path:**

**Step 1 — Is the oil pressure actually borderline at idle?:**
Oil pressure warning threshold: typically 0.5–0.8 bar
Idle oil pressure: typically 1.5–2.5 bar (normal)
If actual idle pressure is 0.6 bar → engine may have worn oil pump or wrong viscosity oil → genuine warning

**Step 2 — Sensor vs cluster:**
Check oil pressure sensor output directly:
```capl
variables {
  float gOilPressure_min = 99.0;
  float gOilPressure_max = 0.0;
  int   gFlickerCount    = 0;
  int   gLastWarnState   = 0;
}

on signal ECM::OilPressure_Warning_Active {
  int current = (int)this.value;
  if (current != gLastWarnState) {
    gFlickerCount++;
    write("[Flicker #%d] Oil Warning changed: %d → %d  at time=%d ms",
          gFlickerCount, gLastWarnState, current, timeNow()/10);
    gLastWarnState = current;
  }
}

on signal ECM::OilPressure_bar {
  float p = this.value;
  if (p < gOilPressure_min) gOilPressure_min = p;
  if (p > gOilPressure_max) gOilPressure_max = p;
}

on key 'o' {
  write("Oil pressure range: %.2f–%.2f bar  Flicker events: %d",
        gOilPressure_min, gOilPressure_max, gFlickerCount);
}
```

**Step 3 — Threshold hysteresis check:**
Warning threshold with hysteresis:
- Warning ON:  pressure < 0.7 bar
- Warning OFF: pressure > 0.9 bar (0.2 bar hysteresis)
If hysteresis is missing (both thresholds at 0.7 bar), a pressure oscillating around 0.7 bar causes rapid warning ON/OFF = flicker.

**Step 4 — Cluster debounce:**
Even if ECM sends rapid ON/OFF, cluster should debounce the oil warning:
- Warning ON: require ECM flag = 1 for minimum 200ms before illuminating
- Warning OFF: require ECM flag = 0 for minimum 500ms before extinguishing
If cluster has no debounce → every ECM ON/OFF transition appears as a flicker.

**Test Cases:**
```
TC_OIL_001: Oil pressure = 3.0 bar → warning icon OFF
TC_OIL_002: Oil pressure = 0.3 bar for 500ms → warning icon ON within 1 second
TC_OIL_003: Oil pressure oscillates 0.6↔0.8 bar at 2Hz → warning icon must not flicker (debounced)
TC_OIL_004: Warning ON → oil pressure restored → icon OFF after 1s stable good pressure
TC_OIL_005: Oil pressure missing (sensor fail) → cluster shows pressure warning + sensor fault indicator
TC_OIL_006: Oil pressure warning at cold start (< 5s run time) → behaviour per spec (may suppress brief cold-start warning)
```

**Root Cause Summary:**
The ECM oil pressure warning signal lacked hysteresis — it was toggling between 0 and 1 as actual idle oil pressure fluctuated around the single threshold of 0.7 bar due to minor oil pump pulsation. At higher RPM, pressure was well above threshold → no flicker. Fix: add 0.2 bar hysteresis in ECM warning generation. Additionally, cluster SW updated to debounce warning icon with 300ms ON-delay and 500ms OFF-delay.

---

## Scenario 8 — Seatbelt Warning Does Not Extinguish When Seatbelt Buckled

> **Interviewer:** "After buckling the seatbelt the warning chime stops but the seatbelt warning icon on the cluster stays illuminated. How do you investigate this split behaviour — chime stops but icon stays?"

**Background:**
The chime stopping confirms the BCM received the buckled signal. The icon staying on means the cluster is not receiving or processing the buckled signal for icon control.

**Investigation Path:**

**Step 1 — Two separate paths in BCM:**
```
BCM receives: SeatbeltBuckled_Driver = 1

BCM output A: Chime_Off_Cmd → Chime controller (LIN) → chime stops ✓ (working)
BCM output B: SeatbeltWarning_Icon_Req → CAN → Cluster → Icon display ✗ (failing)
```
Both paths start from the same BCM sensor input. If chime works but icon doesn't: BCM → Cluster CAN path is the issue.

**Step 2 — CAN trace:**
```capl
on message BCM::SeatbeltStatus_BC {
  write("BCM Seatbelt: Driver=%d  Passenger=%d  Icon_Req=%d",
        this.SB_Driver_Buckled,
        this.SB_Passenger_Buckled,
        this.SB_Warning_Icon_Request);
}

on signal Cluster::Telltale_Seatbelt_State {
  write("Cluster Seatbelt Icon: %d (0=OFF 1=ON)", this.value);
}
```
- Does BCM send `SB_Warning_Icon_Request = 0` when buckled?
- If BCM sends 0 but cluster icon stays ON → cluster not updating icon

**Step 3 — Message filter check:**
Some cluster implementations filter safety-critical icon messages through a message authentication mechanism. If the CRC or counter in the seatbelt status message is wrong, the cluster rejects the message and keeps the last valid state.
Check: is there a rolling counter or CRC in the BCM seatbelt message?

**Step 4 — Icon latch logic:**
Some OEMs latch the seatbelt warning ON until a speed condition is met (e.g., speed has been > 20 km/h for 2 seconds). If the vehicle never reached 20 km/h: icon may be intentionally latched.
This would be a specification misunderstanding — verify the latch condition with the product spec.

**Test Cases:**
```
TC_SB_001: Buckle driver seatbelt → icon OFF within 2 seconds
TC_SB_002: Unbuckle at 0 km/h → icon ON → buckle → icon OFF
TC_SB_003: Unbuckle at 30 km/h → chime AND icon both active → buckle → both clear within 2s
TC_SB_004: BCM seatbelt message timeout → cluster keeps last valid state (no false clear)
TC_SB_005: Passenger seatbelt icon independently controlled from driver icon
TC_SB_006: Rear passenger seatbelt icons (if equipped) function independently
```

**Root Cause Summary:**
BCM seatbelt message upgraded to E2E (End-to-End) protection (CRC + rolling counter) in the latest SW release. The cluster was not updated to handle E2E validation — it rejects all E2E-protected messages and keeps the last valid (un-E2E) state. Since the chime controller was on LIN (not CAN) and not subject to E2E, it still functioned. Fix: update cluster to validate E2E CRC/counter in seatbelt message, or roll back BCM E2E protection on non-safety messages.

---

## Scenario 9 — TPMS Warning Does Not Illuminate in Cold Weather

> **Interviewer:** "A customer in Norway reports that their TPMS (Tyre Pressure Monitoring System) warning never activates in winter — even when tyre pressure is clearly low (1.5 vs 2.0 bar specified). The same car triggers the warning in summer. What is failing?"

**Background:**
Tyre pressure is temperature-dependent. The ideal gas law: `P ∝ T`. At −20°C versus +20°C, tyre pressure naturally drops by ~14% without any leak. TPMS must account for this temperature compensation.

**Investigation Path:**

**Step 1 — Temperature compensation calculation:**
```
PV = nRT
If T drops from 293K (+20°C) to 253K (−20°C):
  Pressure drops proportionally: 2.0 × (253/293) = 1.73 bar even with no leak

Warning threshold: 1.8 bar (25% below standard 2.4 bar — EU regulation)
At −20°C, 2.4 bar cold spec → 2.4 × (253/293) = 2.07 bar is normal
If threshold is fixed at 1.8 bar and actual pressure at −20°C = 2.07 bar → no warning (correct!)
```
This scenario shows the warning NOT triggering is correct behaviour if pressure is genuinely at spec.

**Step 2 — But if there IS a real under-inflation:**
Customer says 1.5 bar. At −20°C the threshold (temperature-compensated) should be:
- Reference pressure: 2.4 bar at 20°C
- At −20°C: warn if below 2.07 bar (25% warning threshold)
- 1.5 bar << 2.07 bar → warning SHOULD trigger

**Step 3 — Direct TPMS sensor data:**
```capl
on message TPMS::TyrePressure_BC {
  write("TPMS: FL=%.2fbar  FR=%.2fbar  RL=%.2fbar  RR=%.2fbar  Temp=%.0f°C",
        this.TPMS_FL_Pressure_bar,
        this.TPMS_FR_Pressure_bar,
        this.TPMS_RL_Pressure_bar,
        this.TPMS_RR_Pressure_bar,
        this.TPMS_AmbientTemp_degC);

  // Check: is cluster receiving the warning request?
  write("TPMS_Warning_Request: %d", this.TPMS_WarningReq);
}
```

**Step 4 — Sensor battery failure in cold:**
Direct TPMS sensors contain small batteries rated for −10°C to +85°C. At −20°C:
- Battery voltage drops below minimum operating → sensor stops transmitting
- Cluster receives no TPMS data → cannot detect under-inflation
- Cluster should show a different warning: "TPMS system unavailable" (not misrepresent as OK)

**Step 5 — Check cluster TPMS fallback:**
If TPMS sensor data absent (timeout): cluster must show TPMS fault lamp (not remain silent)

**Test Cases:**
```
TC_TPMS_001: All tyres at specified pressure → no warning
TC_TPMS_002: One tyre 25% below spec → TPMS warning on within 10 minutes of driving
TC_TPMS_003: TPMS sensor timeout (battery dead simulation) → cluster shows TPMS fault icon
TC_TPMS_004: Pressure low at ignition on → warning visible within 60 seconds
TC_TPMS_005: Re-inflation to spec → warning clears after driving 5 min (sensor relearns)
TC_TPMS_006: Temperature −25°C chamber test → TPMS sensor transmits correctly
```

**Root Cause Summary:**
At −20°C the TPMS sensor battery was failing to power the RF transmitter. The sensor hardware requires a battery rated to −40°C for Nordic market variants. The cluster correctly showed no warning because it received no data. The issue is a component selection failure — the standard battery was shipped to the Nordic market without the cold-rated battery variant. Fix: supplier change to −40°C rated battery + cluster update to show "TPMS Sensor Lost" warning on extended timeout.

---

## Scenario 10 — Battery Charge Warning Activates and Deactivates Randomly

> **Interviewer:** "The battery/alternator warning lamp flickers on and off intermittently — approximately once every 5–10 minutes. The vehicle is running fine and battery voltage seems stable. How do you diagnose the intermittent?"

**Background:**
Intermittent warnings are the hardest to investigate because they are difficult to catch at the right moment. The strategy is to set up continuous logging and capture the event automatically.

**Investigation Path:**

**Step 1 — Long-duration automated capture:**
```capl
variables {
  int   gBattWarnState    = 0;
  int   gTransitionCount  = 0;
  dword gLastTransition   = 0;
  float gVoltage_at_warn  = 0.0;
  float gVoltage_min      = 99.0;
  float gVoltage_max      = 0.0;
}

on signal BCM::Battery_Voltage_V {
  float v = this.value;
  if (v < gVoltage_min) gVoltage_min = v;
  if (v > gVoltage_max) gVoltage_max = v;
}

on signal BCM::BatteryCharge_Warning_Active {
  int current = (int)this.value;

  if (current != gBattWarnState) {
    gTransitionCount++;
    dword now = timeNow() / 10;
    dword delta_ms = now - gLastTransition;

    float voltage = getValue(BCM::Battery_Voltage_V);
    if (current == 1) gVoltage_at_warn = voltage;

    write("[BATT WARN %s] #%d  t=%d ms  delta=%d ms  Voltage=%.2fV",
          current ? "ON " : "OFF",
          gTransitionCount, now, delta_ms, voltage);

    gBattWarnState   = current;
    gLastTransition  = now;
  }
}

on stopMeasurement {
  write("=== Battery Warning Summary ===");
  write("Total transitions: %d", gTransitionCount);
  write("Voltage range observed: %.2f–%.2f V", gVoltage_min, gVoltage_max);
  write("Voltage at warn events: %.2f V", gVoltage_at_warn);
  write("If transitions happen at fixed interval → check software timer bug");
  write("If transitions correlate with low voltage → real charging fault");
}
```

**Step 2 — Correlate with other signals:**
- Does the warning correlate with a specific load (cooling fan on, AC compressor)?
- Does it correlate with a specific CAN message that appears just before each event?
- Is there a pattern: always every 5 minutes → suggests a software timer firing

**Step 3 — Software timer investigation:**
Some cluster or BCM implementations have a "battery check" timer that runs every 5 minutes.
If this timer reads a stale/cached voltage value instead of current, it may see an old low-voltage reading and trigger the warning briefly.

**Step 4 — Alternator field duty cycle:**
At borderline load, alternator field duty cycle fluctuates between 95–100%.
Brief rotor saturation → alternator output drops for 50–100ms → voltage dips to 11.8V → warning triggers → recovers.
Check: oscilloscope on alternator L-terminal.

**Test Cases:**
```
TC_BATT_WARN_001: Battery voltage 14.1V → no warning icon
TC_BATT_WARN_002: Battery voltage 11.7V for 500ms → warning ON within 1 second
TC_BATT_WARN_003: Battery voltage 11.7V → returns to 13.8V → warning clears within 2 seconds
TC_BATT_WARN_004: Voltage fluctuates 13.5↔13.8V (normal range) → no warning flickering
TC_BATT_WARN_005: CAN voltage missing (sensor fault) → cluster shows warning + sensor code
TC_BATT_WARN_006: 2-hour continuous drive → if no genuine fault → zero warning events
```

**Root Cause Summary:**
BCM battery monitoring function ran on a 5-minute timer and used a 10-sample moving average. One of the 10 samples was being corrupted by a hardware A/D converter glitch when the AC compressor clutch engaged. The corrupted sample pulled the average below the 12.0V threshold momentarily → BCM transmitted warning → cluster illuminated → next timer cycle average was correct → BCM cleared warning. Fix: exclude samples taken within 200ms of AC compressor clutch engagement, which causes known A/D noise.

---
*File: 05_warning_telltales.md | Scenarios 6–10 | April 2026*
