# Scenarios 11–15 — Fuel Gauge, Range & EV SOC
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 11 — Fuel Gauge Drops Rapidly From Full to Half Tank Then Stabilises

> **Interviewer:** "After filling the tank to 100%, the fuel gauge drops to approximately 50% within 5 minutes of driving, then correctly tracks the remaining fuel. What is causing the initial rapid drop?"

**Background:**
This is a known pattern caused by fuel slosh and float settling. When the tank is completely full, the fuel sender float is at its mechanical maximum. As the car moves, fuel settles to the back of the tank and the float drops → false low reading → gauge drops.

**Investigation Path:**

**Step 1 — Confirm it stabilises at 50% and matches reality:**
- After 5 minutes: fuel gauge stays at 50%
- Top up tank again → does gauge return to 100%?
- If yes: the 50% reading after 5 min represents actual remaining fuel (perhaps only half was ever added)
- If no: after re-fill it shows 80% → genuine gauge overshoot issue

**Step 2 — Sender signal capture:**
```capl
variables {
  float gFuelSender_last = 0.0;
  float gFuelGauge_last  = 0.0;
  long  tLast_ms         = 0;
}

on signal FuelLevelSensor::FuelSender_Ohm {
  float sender = this.value;
  float gauge  = getValue(Cluster::FuelGauge_Display_Pct);
  long  now    = timeNow() / 10;
  long  dt     = now - tLast_ms;

  float senderDelta = sender - gFuelSender_last;
  float gaugeDelta  = gauge  - gFuelGauge_last;

  write("[%d ms] Sender=%.1fΩ (Δ%.1f)  Gauge=%.1f%% (Δ%.1f%%)",
        now, sender, senderDelta, gauge, gaugeDelta);

  // Flag rapid drops
  if (gaugeDelta < -5.0) {
    write("WARNING — Fuel gauge dropped %.1f%% in %d ms — check sender signal", gaugeDelta, dt);
  }

  gFuelSender_last = sender;
  gFuelGauge_last  = gauge;
  tLast_ms         = now;
}
```

**Step 3 — Sender resistance range:**
```
Typical fuel sender:
  Empty:  250 Ω
  Full:   30 Ω
BCM reads resistance → converts to percentage → sends CAN signal to cluster
```
If BCM sender calibration table has no entry for > 95% full (because full sender is at mechanical limits and physically variable), BCM maps anything between 30–40Ω to "full" but 40–60Ω to "50–80%" → sudden apparent drop when sender settles from bang-full to slightly-below-full.

**Step 4 — Damping filter:**
The cluster applies a damping filter to prevent the gauge from dropping on every corner.
Standard max drop rate: gauge must not fall more than 2% per minute when speed > 10 km/h.
If this filter was removed from a recent SW build → raw sender drops appear on gauge immediately.

**Test Cases:**
```
TC_FUEL_001: Sender signal = 30Ω (full) → gauge shows 100%
TC_FUEL_002: Sender signal steps from 30Ω to 40Ω (8% drop in sender) → gauge must not drop > 2% in first 60s
TC_FUEL_003: Sender steady at 140Ω (half tank) → gauge stable at 50% ±2% for 5 minutes
TC_FUEL_004: Sender drops 10% in 1 second (slosh simulation) → gauge must not mirror this drop
TC_FUEL_005: Engine off, parked → gauge must not move (sender + car stationary)
TC_FUEL_006: Fuel level at reserve → warning lamp on at spec threshold (typically 10–12 litres remaining)
```

**Root Cause Summary:**
Fuel gauge damping filter was accidentally disabled in a cluster SW update when refactoring the signal processing module. The raw fuel sender resistance (which varies with fuel slosh during initial driving) was directly displayed without smoothing. Sender variance from 32Ω (overfull at fill station) to 45Ω (settling after 2 km of driving) appears as a 30% gauge drop. Fix: restore the rate-limiting filter (max 2% gauge change per minute while vehicle is moving).

---

## Scenario 12 — Distance to Empty Shows 999 km Permanently

> **Interviewer:** "The Distance to Empty (DTE) display on the cluster shows 999 km regardless of actual fuel level. Even with only 5 litres of fuel, it still shows 999 km. How do you investigate?"

**Background:**
DTE is calculated either by the cluster or by the BCM/ECM: `DTE = fuel_remaining_litres × current_fuel_economy_km/l`. A permanent maximum value means either the input data is wrong (fuel level maxed out) or the calculation is outputting its cap value (typically 999 km as maximum display).

**Investigation Path:**

**Step 1 — Check the inputs to the DTE calculation:**
```capl
on key 'd' {
  float fuelLevel_pct = getValue(BCM::FuelLevel_Pct);
  float fuelLevel_L   = getValue(BCM::FuelLevel_Litres);
  float economy_kmpl  = getValue(ECM::FuelEconomy_kmpl);
  float dte_ecm       = getValue(ECM::DTE_km);
  float dte_cluster   = getValue(Cluster::DTE_Display_km);

  write("=== DTE Debug ===");
  write("Fuel Level: %.0f%% = %.1f litres", fuelLevel_pct, fuelLevel_L);
  write("Current Economy: %.1f km/litre", economy_kmpl);
  write("ECM calculates DTE: %.0f km", dte_ecm);
  write("Cluster displays DTE: %.0f km", dte_cluster);
  write("Calculated DTE: %.0f km", fuelLevel_L * economy_kmpl);

  if (dte_cluster == 999.0 && dte_ecm < 500.0) {
    write("FAIL: ECM sends %.0f km but cluster caps/ignores at 999 km", dte_ecm);
  } else if (dte_ecm == 999.0) {
    write("FAIL: ECM itself sending max value — inputs to ECM calculation are wrong");
  }
}
```

**Step 2 — Economy initialisation:**
At vehicle handover (new vehicle, first start), the rolling average fuel economy has no history.
Default value: some implementations default to `99.9 km/l` (max) until real economy data is accumulated.
`DTE = 10 litres × 99.9 km/l = 999 km` → displayed immediately from factory until real data builds up.

**Step 3 — Stuck signal:**
The `FuelEconomy_kmpl` signal may be stuck at its maximum (99.9) due to:
- ECM not yet receiving load data (cold start, idling only)
- Signal initialised to max and never updated (fuel injector data not feeding economy calculation)

**Step 4 — DTE display cap:**
If DTE calculation returns > 999 → cluster caps at 999 and shows "---" or "999".
If the cap logic has a bug (caps at 999.0 and displays exactly 999.0 instead of "---"): the cap itself is the bug.

**Test Cases:**
```
TC_DTE_001: Fuel = 10L, economy injected as 10 km/L → DTE shows 100 km ±10 km
TC_DTE_002: Fuel = 50L, economy = 15 km/L → DTE shows 750 km ±20 km
TC_DTE_003: Fuel = 3L (reserve) → DTE shows ≤ 45 km (critical range warning)
TC_DTE_004: DTE > 999 km → cluster shows "---" not "999" (no false reassurance)
TC_DTE_005: Economy history cleared (trip reset) → DTE gracefully re-estimates, not 999 km
TC_DTE_006: DTE accuracy: drive until empty → DTE at 0 km must correspond to actual empty ±15%
```

**Root Cause Summary:**
New vehicles from the factory have no fuel economy history. The ECM defaults the rolling average economy to 99.9 km/litre (max value) until at least 50 km of real drive data is accumulated. With 10 litres in the tank at handover: `10 × 99.9 = 999 km` → displays as 999 km. Fix: cluster must display "---" when economy average confidence is below minimum threshold (< 50 km of data), instead of showing a numerically calculated but unreliable DTE.

---

## Scenario 13 — EV State of Charge Drops 5% Instantly on Motor Start

> **Interviewer:** "On an electric vehicle, the SOC is at 80% when the car is parked. The driver gets in, starts the drive mode, and the SOC instantly jumps from 80% to 75%. It then decreases normally. What is happening?"

**Background:**
A 5% instant SOC drop on drive mode activation is a known calibration artefact in BMS (Battery Management System) systems. The parked SOC and the dynamic SOC are calculated differently.

**Investigation Path:**

**Step 1 — Two SOC calculation modes:**
```
Parked/resting SOC:   Calculated from Open Circuit Voltage (OCV)
                      Accurate, stable, but only valid when battery is at rest (no current)

Dynamic/driving SOC:  Calculated from Coulomb counting (integrating current over time)
                      Real-time, but drifts over time and is reset to OCV on next rest period
```
The instant drop = difference between resting OCV-based SOC and the starting point of the Coulomb counter.

**Step 2 — BMS initialisation sequence:**
```
1. Car parked (8 hours) → BMS measures OCV → calculates SOC = 80%
2. Driver starts → BMS switches from OCV mode to Coulomb counting mode
3. Coulomb counter initialised at 80% ← should use OCV as starting point!
4. If Coulomb counter is initialised 5% lower than OCV → instant apparent drop
```

**Step 3 — CAN trace:**
```capl
on signal BMS::SOC_Pct {
  float soc = this.value;
  write("[SOC] %.1f%%  Source=%d (0=OCV 1=Coulomb)",
        soc, getValue(BMS::SOC_CalculationMode));
}

on signal VehiclePowerMode::DriveMode_Active {
  if (this.value == 1) {
    write("[DRIVE START] SOC at drive start = %.1f%%", getValue(BMS::SOC_Pct));
  }
}
```

**Step 4 — Temperature correction:**
BMS applies a temperature derating: at low temperatures, usable capacity is reduced.
If car is parked at 20°C (no derating) but the first drive starts at 5°C (cabin temperature differential):
- Available capacity at 5°C < capacity at 20°C
- SOC recalculated for temperature derating → apparent drop

**Test Cases:**
```
TC_EV_SOC_001: Park 8 hours → start drive → SOC change on mode switch ≤ 1%
TC_EV_SOC_002: Park 8 hours at −10°C → start drive → SOC adjustment expected (spec defines max delta)
TC_EV_SOC_003: SOC at full charge (100%) → start drive → no jump above 100% or below 98%
TC_EV_SOC_004: SOC decreases monotonically during constant speed driving (no random jumps)
TC_EV_SOC_005: Regenerative braking → SOC increases at rate proportional to regen power
TC_EV_SOC_006: SOC reaches 0% → vehicle enters limp mode → cluster shows "Range: 0 km" warning
```

**Root Cause Summary:**
BMS Coulomb counter initialisation algorithm used an SOC lookup table indexed by both temperature and OCV. There was a 1°C temperature rounding error at the table boundary (19.5°C rounded to 20°C vs 19°C) that caused the Coulomb counter to initialise 5% lower than the OCV-based SOC. Fix: correct the temperature boundary handling in the SOC initialisation table lookup.

---

## Scenario 14 — EV Range Estimate Changes Drastically When Heating is Switched On

> **Interviewer:** "An EV shows 200 km range estimate. The driver switches on cabin heating → range instantly drops to 120 km. The actual impact of heating is approximately 20% but the display shows a 40% drop. Why does the range estimate over-react?"

**Investigation Path:**

**Step 1 — Range calculation inputs:**
```
Range = available_energy_kWh / projected_consumption_kWh_per_km

When heating ON:
  - Projected consumption increases → range decreases
  - The size of the decrease depends on: projected heating power and driving profile
```

**Step 2 — Instantaneous vs history-based consumption:**
```capl
on signal BMS::RangeEstimate_km {
  float range = this.value;
  float heat  = getValue(HVAC::HeatingPower_kW);
  float drive = getValue(DriveSystem::DriveConsumption_kW_per_km);

  write("Range=%.0f km  Heating=%.1fkW  Drive=%.2fkW/km", range, heat, drive);
}
```
If the range model uses instantaneous heating power (e.g., 6kW peak at startup) instead of steady-state heating power (1.5kW after pre-heat): the projected energy budget is 4× overestimated → range drops 4× more than reality.

**Step 3 — History window:**
Range estimation should be based on average consumption over the last 30–50 km.
If the averaging window is reset when HVAC state changes → the algorithm starts fresh with only the high-startup-power data → overestimates heating impact.

**Step 4 — BMS energy budget split:**
```
Available energy:      50 kWh
Driving reserve:       40 kWh (range-giving)
HVAC reserve:          10 kWh (committed)

With heating OFF: Range = 40 kWh / 0.2 kWh/km = 200 km
With heating ON (correct): HVAC takes ~5 kWh for 200 km trip → Drive reserve = 35 kWh → range = 175 km
With heating ON (bug): HVAC instantaneous power 6kW projected × full trip time → reserves 20 kWh → range = 100 km
```

**Step 5 — Fix specification:**
Use steady-state heating efficiency (post warm-up) not peak heating power for range projection.
Apply a 30-km rolling average to all auxiliary loads for range calculation.

**Test Cases:**
```
TC_RANGE_001: Heating OFF → range stable at computed value
TC_RANGE_002: Heating ON → range drops by ≤ 25% (spec allows up to 25% at extreme cold)
TC_RANGE_003: Heating OFF again → range recovers to within 5% of pre-heating estimate
TC_RANGE_004: Rapid HVAC on/off cycling → range display does not oscillate more than ±5% per cycle
TC_RANGE_005: Seat heaters ON (1kW) → range impact ≤ 5%
TC_RANGE_006: Range accuracy validation: predicted range at 100% SOC vs actual range driven ≤ ±15% error
```

**Root Cause Summary:**
The range model incorrectly used the HVAC instantaneous current draw (measured 0–10 seconds after switching on, during compressor/heater element ramp-up: 5–6 kW) for projecting energy cost over the entire journey. Steady-state heating power is 1.2–1.8 kW. The model over-penalised the range by 3–4×. Fix: ignore HVAC power samples in the first 30 seconds after HVAC mode change, use the 30–120 second average instead.

---

## Scenario 15 — Fuel Economy Display Does Not Update After Long Stop-Start Section

> **Interviewer:** "A driver drives 20 km at 120 km/h on a motorway (excellent economy: 5 L/100km). They then enter city traffic for 1 hour with extensive stop-start (poor economy: 15 L/100km). The trip computer economy display only gradually changes over the next 30 minutes — showing 8 L/100km for a long time even though actual consumption is 15 L/100km. How do you explain this?"

**Background:**
This is an averaging window length issue, not a bug — the moving average is correctly weighted over the distance driven, but the window is too long (or distance-based rather than time-based), making it slow to respond.

**Investigation Path:**

**Step 1 — Average economy calculation type:**
```
Option A: Distance-weighted rolling average (last 50 km)
  After 20 km motorway + 5 km city: motorway still dominates (20/25 = 80% of data)
  Economy display = 80% × 5 + 20% × 15 = 7 L/100km → slow to change ← this is the behaviour

Option B: Time-weighted rolling average (last 30 minutes)
  After 30 min city: city data = 100% of recent window → shows 15 L/100km much faster

Option C: Instantaneous economy (current 5s average)
  Shows current second-by-second consumption → too volatile but responsive
```

**Step 2 — Check window type:**
```capl
on key 'e' {
  float avgEconomy   = getValue(Cluster::AvgFuelEconomy_L100km);
  float instEconomy  = getValue(ECM::InstFuelEconomy_L100km);
  float totalFuel_L  = getValue(Cluster::TripFuelUsed_L);
  float totalDist_km = getValue(Cluster::Trip_Distance_km);
  float calcEconomy  = (totalDist_km > 0) ? (totalFuel_L / totalDist_km * 100.0) : 0.0;

  write("Displayed Avg Economy: %.1f L/100km", avgEconomy);
  write("Instantaneous Economy: %.1f L/100km", instEconomy);
  write("Trip-total calculation: %.1f L/100km (%.1fL / %.1fkm)",
        calcEconomy, totalFuel_L, totalDist_km);
  write("If displayed ≈ trip-total → uses full-trip average (not rolling)");
  write("If displayed ≈ recent average → uses rolling window of some size");
}
```

**Step 3 — User expectation vs spec:**
Most customers expect the average economy to reflect recent driving conditions.
The spec likely says: "trip average economy" = total fuel used / total distance driven.
Trip average IS mathematically slow to change when history is long. This is correct behaviour.
However: many competitors show "last 30 km average" which changes faster.
Product decision: is this a spec issue or a product quality issue?

**Step 4 — Proposed improvement:**
Show both: "Trip Average" (full trip) and "Last 30 km Average" simultaneously, or allow user to select the window.

**Test Cases:**
```
TC_ECON_001: Drive 10 km at constant 120 km/h → avg economy settles within ±0.5 L/100km of actual
TC_ECON_002: Economy display updates at least once every 500m driven (not once per minute)
TC_ECON_003: Trip reset → economy display resets and re-builds from next 1 km of data
TC_ECON_004: Zero distance (vehicles stationary) → economy shows 0 or '---' (no divide-by-zero)
TC_ECON_005: Switch from motorway to city → within 10 km, display reflects reality within ±3 L/100km
TC_ECON_006: Economy in L/100km, mpg, km/L — all market variants display correctly with correct unit
```

**Root Cause Summary:**
This is correct behaviour for a trip-total average economy calculation — the display correctly shows the cumulative average for the entire trip. The customer expectation does not match the product specification. Improvement recommendation filed: add a "Recent 30 km" average alongside the trip average to improve perceived responsiveness. This was accepted as a product improvement for the next programme.

---
*File: 06_fuel_range_ev.md | Scenarios 11–15 | April 2026*
