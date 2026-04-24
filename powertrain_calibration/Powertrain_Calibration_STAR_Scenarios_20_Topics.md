# Powertrain Calibration Engineer — STAR Scenario Bank
## 20 Real-World Interview and Assessment Scenarios

**Document Type:** Interview Preparation and Competency Evidence  
**Role:** Powertrain Calibration Engineer — Defence All-Terrain Vehicles  
**Format:** STAR (Situation / Task / Action / Result) per scenario  
**Standards Referenced:** MIL-STD-810H, ISO 26262, AUTOSAR, EURO VI

---

## Scenario Index

| # | Topic | Key Competency |
|---|---|---|
| 01 | Cold Start Failure at –32 °C | Cold weather calibration, pilot injection |
| 02 | Gradeability Shortfall on 60% Slope | Torque structure, TC calibration |
| 03 | Black Smoke on Full-Load Transient | Anti-smoke strategy, air-fuel ratio |
| 04 | Water Fording ECU Stall | Fording mode calibration, idle strategy |
| 05 | Stealth Mode Acoustic Limit Exceeded | NVH, combustion noise, mode calibration |
| 06 | DPF Regen During Tactical Approach | Regen inhibit strategy, soot management |
| 07 | High-Altitude Torque Derating Excess | Altitude compensation, boost calibration |
| 08 | Transmission Shift Hunting on Sand | Shift schedule, TC lock-up calibration |
| 09 | Engine Thermal Runaway in Hot Chamber | Thermal protection, fan calibration |
| 10 | DoE Model Quality Below 0.95 R² | DoE redesign, data quality |
| 11 | Calibration Dataset Version Conflict | CDM management, change control |
| 12 | EGR Valve Delayed Response from Packaging | Sensor/actuator delay compensation |
| 13 | Driveline Shunt During Tip-In at Crawl | Torque ramp calibration, NVH |
| 14 | NOx Emissions Exceedance on MoD Cycle | EGR/SCR calibration, cycle optimisation |
| 15 | A2L Mismatch Causing Wrong Value Flash | Configuration management, A2L discipline |
| 16 | Python Automation Reducing Analysis Cycle | Automation, batch processing |
| 17 | Water Fording HVAC Intake Failure | Mode interaction, system calibration |
| 18 | Multi-Fuel Adaptation Calibration | Fuel quality detection, adaptation maps |
| 19 | DFMEA Gap in Torque Limiter Sign-Off | Functional safety, DVP&R |
| 20 | Emergency Limp-Home Calibration Field Validation | Limp-home strategy, field expedient fix |

---

## Scenario 01 — Cold Start Failure at –32 °C

**Topic:** Cold weather calibration, pilot injection tuning

---

**S — Situation:**

During the Arctic cold-weather campaign at Arjeplog, Sweden (–32 °C ambient, vehicles soaked overnight to full thermal equilibration), the 6.7L turbodiesel engine on the pre-production defence ATV refused to achieve stable combustion within the 15-second specification during three consecutive start attempts. The first combustion event occurred between 18 and 22 seconds, followed by a 2-minute period of rough, misfiring idle with white smoke visible at the exhaust. This was a gate-critical test — the programme was 6 weeks from DVP&R cold-weather sign-off, and the test team had secured the chamber booking for only 4 working days.

**T — Task:**

As the lead Calibration Engineer on-site, I was responsible for diagnosing the root cause of the delayed cold start, implementing a calibration fix using only the equipment available on-site (INCA laptop, current A2L, and a dyno simulator via HIL), and re-validating within the 4-day window without invalidating other cold-weather tests in the schedule.

**A — Actions:**

1. **Captured baseline data from the failed starts.**
   Connected INCA to the ECM via CAN XCP. Recorded `InjTiming_Main`, `InjQty_Main`, `InjQty_Pilot`, `Pmax_bar`, `Lambda_actual`, `Crank_Speed_rpm`, `ECT_C`, `Glow_Plug_Enable`, and `CombustionStability_Flag` on the first three cold start attempts.
   Key observation: `CombustionStability_Flag` showed no stable combustion event until crank position cycle 40 (16 seconds at 150 rpm cranking). Raw cylinder pressure data (from a kistler indicator fitted to cylinder 1) showed very low peak pressure on the first 35 crank cycles — consistent with poor fuel atomisation or lean mixture at cold temperatures.

2. **Reviewed the injection calibration at –32 °C cell.**
   Checked `InjQty_Pilot` at ECT = –32 °C: **0.4 mg/stroke** (the cold-ambient cell had been inherited from a temperate-climate calibration dataset and was never updated for the Arctic variant). The `ColdStart_InjQty_Correction` table had a value of +0.2 mg/stroke at –32 °C — far below the +1.5 mg/stroke typically required at this temperature for pre-conditioning fuel atomisation.
   Checked `GlowPlug_Duration_Map`: value at –32 °C was 14 seconds — unchanged from base. This was within specification, so glow plug pre-heating was not the primary issue.

3. **Cross-referenced against a similar Tier-1 diesel calibration from a previous programme (cold-weather doE data retained from 3 years prior).**
   From that historical dataset, pilot injection at –30 °C required 1.8–2.2 mg/stroke to achieve first combustion within 5 cycles. The current calibration was providing 0.6 mg/stroke total (0.4 pilot + 0.2 correction). A factor of 3× shortfall.

4. **Implemented calibration changes on the working page in INCA:**
   - `InjQty_Pilot` at ECT cells ≤ 0 °C: increased from 0.4 → 1.8 mg/stroke (stepped gradient to avoid smoke above 0°C)
   - `ColdStart_InjQty_Correction` at –32 °C: increased from +0.2 → +0.8 mg/stroke
   - `InjTiming_Pilot_Map` at –32 °C: advanced from –14 °CA to –17 °CA (earlier pre-conditioning of charge)
   - `ColdStart_IdleSpeed_Target` at –32 °C: raised from 800 → 950 rpm (increased cranking energy into cylinders)
   - Total pilot quantity at –32 °C cold start: 2.6 mg/stroke (calculated; within injector deposit-risk limit of 3.0 mg)

5. **Re-soaked vehicle for 8 hours before re-test.**
   Using the environmental chamber available at the test site, the engine was allowed to re-reach full thermal equilibrium at –32 °C.

6. **Ran re-test sequence**: 3 consecutive cold starts at –32 °C with 30-minute cooling between attempts.

**R — Result:**

- **First combustion event:** average 7.2s (vs 20s before; spec = 15s — **PASS**)
- **Stable idle achieved:** 11 seconds after first combustion (**PASS**)
- **White smoke clears:** within 75 seconds (**PASS**)
- **Full torque availability:** 2 minutes 45 seconds from start (**PASS**, spec = 3 min)
- Root cause confirmed: `InjQty_Pilot` was not updated for the Arctic variant calibration — a calibration variant management gap.
- **Process fix:** Added a mandatory "cold weather variant delta check" step to the CDM release checklist, requiring the cold-start injection maps to be explicitly reviewed against the current warm-climate dataset before every Arctic campaign.
- Cold-weather sign-off achieved on Day 3 of the 4-day window.

---

## Scenario 02 — Gradeability Shortfall on 60% Slope

**Topic:** Torque structure, TC lock-up calibration, transfer case integration

---

**S — Situation:**

During a gradeability validation trial on an 18-tonne armoured vehicle (combat-loaded), the vehicle failed to sustain ascent of a 62% gradient at the proving ground. The requirement was to sustain climb at minimum 4 km/h with no clutch slip or transmission overspeed. The vehicle stalled twice at approximately 45% gradient during approach to the maximum slope section. The programme was at the vehicle-level integration phase, 8 weeks before the DVP&R gradeability sign-off gate.

**T — Task:**

Analyse why the vehicle was stalling on an approach gradient of 45% (below the 62% target), determine if the root cause was in engine calibration, transmission calibration, or the interaction between the two, and implement a fix that achieves full gradeability compliance.

**A — Actions:**

1. **Reviewed the test log in INCA measurement files.**
   Identified the timeline: during the approach to the 45% slope section:
   - Vehicle speed = 5.2 km/h
   - Engine speed = 1,350 rpm (expected — 4L, low range engaged)
   - Driver torque demand = 100% (full pedal)
   - Requested engine torque = 820 Nm
   - **Actual engine torque = 620 Nm** (200 Nm shortfall)
   - TC lock-up status = **LOCKED** (TC_Lockup_Enable active)
   - Transmission input speed = engine speed (confirming TC was locked)

2. **Identified the TC lock-up as a probable cause.**
   With TC locked at very low speed (5 km/h, 4L), any torque reversal or momentary wheel slip caused an abrupt driveline shock that the engine speed controller interpreted as an overspeed event → torque cutback → stall sequence.
   The `TC_Lockup_Enable_Speed` map had a minimum speed of **3 km/h in all gears** — no exception for 4L low-range mode. This was never validated for the 18-tonne combat-load condition.

3. **Reviewed the torque shortfall separately.**
   The 200 Nm shortfall at full pedal at 1,350 rpm was traced to the `TrqLim_Max_Map`: at 1,350 rpm the torque limit was 650 Nm (a conservative value carried over from a lighter variant). The 18-tonne vehicle required the full 820 Nm torque rating available from the engine at that speed.

4. **Made two calibration changes (separately tested to isolate their effects):**

   **Change A — TC lock-up in 4L:**
   - Modified `TC_Lockup_Enable_Speed` for **4th gear and below in LOW RANGE**: minimum speed raised from 3 km/h → 20 km/h
   - Added condition: TC unlock enabled during gradeability mode if gradient > 35%
   - This allowed TC slip to act as a torque multiplier (typical TC torque ratio at stall = 2.5:1) during heavy climbing

   **Change B — Torque limit in gradeability mode:**
   - Added a `GradeabilityMode_Torque_Offset` calibration: +180 Nm added to `TrqLim_Max_Map` when Gradeability mode active and gradient > 30%
   - Durability impact assessed: maximum 15 minutes of full grade operation per mission cycle — within driveline fatigue life budget confirmed by powertrain integrator

5. **Validated changes A and B on a 25% gradient first, then 45%, then the target 62%.**

**R — Result:**

- Vehicle successfully sustained 62% gradient at 4.5 km/h at combat load (**PASS**, requirement ≥ 4 km/h)
- Zero stalls in 3 consecutive gradient runs
- TC slip during climb: 8–15% (within TCM thermal limits — confirmed by ATF temperature log)
- Durability calculation confirmed: the torque increase stays within the driveline design envelope
- Root causes: (1) TC lock-up not calibrated for combat-load extreme gradeability in low range; (2) torque limit map not updated for the 18-tonne weight class variant
- DVP&R gradeability sign-off completed as planned

---

## Scenario 03 — Black Smoke on Full-Load Transient

**Topic:** Anti-smoke calibration, air-path lead control, VGT pre-positioning

---

**S — Situation:**

During an acceleration validation test for the High-Mobility mode of an armoured reconnaissance vehicle, sustained black smoke was visible during full-pedal acceleration from 20 km/h to 80 km/h on a flat track. The smoke level was measured at FSN 3.2 — more than double the 1.5 FSN limit. The issue was observed consistently during the 0–100% pedal tip-in. The vehicle had no emissions certification requirement (MoD exempt), but the black smoke was creating an adverse visual and IR signature — operationally unacceptable for a reconnaissance platform, and programme-blocking as it suggested severe AFR imbalance during transients.

**T — Task:**

Eliminate the visible black smoke during full-load transient without reducing the power step response required for High-Mobility mode (0–50 km/h acceleration < 12 seconds at combat load).

**A — Actions:**

1. **Instrumented the transient event.**
   Added high-frequency measurement of `MAF_kg_h`, `MAP_kPa`, `Lambda_actual`, `InjQty_Main_mg`, `Smoke_FSN` (from continuous online AVL 459 unit), and `Turbo_Speed_krpm` at 10ms resolution.
   During the tip-in event: Lambda_actual dropped to **0.78** within 200ms of pedal application — far below λ_min (should be 1.05). The smoke peaked at 2.8 FSN at t = 300ms post tip-in.

2. **Identified the root cause: fuelling was not being constrained by the smoke limiter during the transient.**
   The `SmokeLimiter_Active` flag showed FALSE during the entire event. Traced to calibration: `SmokeLimiter_Enable_Threshold_Torque` was set to 750 Nm — the vehicle never exceeded this on the lower slope sections of previous testing (below threshold). But in High-Mobility mode on flat track with a lighter load, torque reached 790 Nm → the smoke limiter was never armed at the critical moment.

3. **Also found VGT pre-positioning was not active in High-Mobility mode.**
   The base `VGT_TransientBoost_Enable` flag was set to FALSE for High-Mobility (an engineer had disabled it for an unrelated NVH investigation and never re-enabled it). Without VGT pre-positioning, the turbocharger did not receive advance vane closure before the fuel demand increase — resulting in maximum turbo lag (320ms in this installation vs 150ms with pre-positioning active).

4. **Implemented three changes:**

   **Fix 1 — SmokeLimiter threshold:**
   Reduced `SmokeLimiter_Enable_Threshold_Torque` from 750 → 200 Nm (always active above low idle)

   **Fix 2 — SmokeLimiter λ_min value:**
   Increased `Lambda_Min_Transient` from 1.00 → 1.07 (added 7% air margin to prevent λ dip into smoke territory during dynamics)

   **Fix 3 — VGT pre-positioning re-enabled:**
   - Re-enabled `VGT_TransientBoost_Enable = TRUE` for High-Mobility mode
   - Set `VGT_PrePosition_Advance_ms = 150ms` (pre-close vanes 150ms before estimated peak torque demand based on rate-of-change of pedal position)

5. **Recalibrated the injection ramp rate to balance acceleration against smoke:**
   - `FuelRateLimit_TipIn_Map[PedalRate_pct_per_s]`: reduced maximum ramp rate by 15% during the 0–300ms transient window only
   - Trade-off assessed: 0–50 km/h time increased from 11.1s to 11.6s — still within the 12s requirement

**R — Result:**

- Peak smoke reduced from FSN 3.2 → **FSN 0.9** (**PASS**, limit = 1.5 FSN)
- Minimum lambda during tip-in: 1.08 (previously 0.78)
- 0–50 km/h time: 11.6s (**PASS**, spec = 12s)
- Smoke limiter confirmed active throughout all load points
- Root causes: smoke limiter threshold misconfigured for high-torque engine variant; VGT pre-positioning inadvertently disabled
- Process improvement: created a High-Mobility mode "sanity check" test in the regression suite — automatically checks `VGT_TransientBoost_Enable` is TRUE and smoke FSN < 1.0 during standard tip-in test

---

## Scenario 04 — Water Fording ECU Stall

**Topic:** Water fording mode calibration, idle control, air restriction management

---

**S — Situation:**

During water fording validation trials at a MoD proving ground (water depth 1.2m, 50m crossing), the engine stalled on four occasions when the vehicle entered the water. The engine fired correctly on the bank, ran during descent into the water, but stalled within 8 seconds of full immersion at water depth 0.8–1.0m. This was a critical programme failure — water fording is a mandatory MoD acceptance criterion. The trial had 3 days of test lane availability remaining.

**T — Task:**

Identify why the engine was stalling after partial water immersion and implement a calibration fix that allows full 1.5m fording for a continuous 30-minute period.

**A — Actions:**

1. **Downloaded ECM fault memory and measurement data from the four stall events.**
   DTC stored: `P0101 — MAF Sensor Out of Range (Low)` — confirmed every stall.
   Measurement data: At the moment of stall, `MAF_kg_h` dropped from 620 kg/h (expected at 900 rpm idle) to **45 kg/h** within 200ms. Engine speed dropped below 500 rpm → flame-out.

2. **Investigated MAF sensor behaviour underwater.**
   The MAF sensor was located in the cold air intake, upstream of the snorkel. When the vehicle was at 0.8m depth, wave action was causing water droplets to enter the intake snorkel and splash the MAF hot-wire element. The hot wire hot-film MAF sensor outputs near-zero when wetted (water cooling the wire gives false low-air reading). The ECM interpreted this as extreme lean condition and immediately cut fuel to prevent lean knock → engine stalled.

3. **Identified ECM diagnostic over-reaction:**
   The `MAF_OutOfRange_FuelCutoff_Enable` flag was set to TRUE — any MAF signal below 50 kg/h at > 700 rpm triggered immediate fuel cutoff (designed to prevent lean damage in normal land operation). During fording, this was catastrophically wrong.

4. **Implemented fording mode calibration changes:**

   **Fix 1 — Disable MAF-based fuel cutoff in fording mode:**
   Set `MAF_OutOfRange_FuelCutoff_Enable = FALSE` when `FordingMode_Active = TRUE`.
   Instead: use the **speed-density fuelling model** (MAP + IAT + engine speed → estimated air mass), which does not depend on the MAF sensor.

   **Fix 2 — MAF signal validation and fallback:**
   Modified `MAF_FaultReaction_FordingMode`: instead of fuel cutoff, switch to estimated air mass (speed-density) and set a non-DTC informational flag. Only raise DTC after fording mode exits.

   **Fix 3 — Idle speed increase for intake restriction tolerance:**
   Increased `FordingMode_Idle_Setpoint` from 850 → 1,050 rpm. The higher idle generates more engine vacuum which can overcome partial air restriction from water ingress.

   **Fix 4 — Throttle pre-enrich table for intake restriction:**
   Added `FordingMode_Fuel_Enrichment_Map[MAP_kPa]`: when MAP drops > 10% below expected value at idle in fording mode, increase fuelling by 8% (compensates for partial restriction from water around snorkel).

5. **Re-ran fording validation: entry sequence, 1.0m depth, 1.2m depth, 1.5m depth.**

**R — Result:**

- Zero engine stalls across 12 consecutive fording events (full depth 1.5m, 30 minutes cumulative)
- Engine idle stable at 1,050 rpm throughout; speed variation ±30 rpm (within ±50 rpm spec)
- MAF fallback to speed-density model invoked correctly on 7 events; rich-running DTC correctly suppressed during fording
- Post-fording: MAF self-clears after 90 seconds (hot-wire drying); no permanent DTC
- Root cause: MAF fuel cutoff logic not overridden for fording mode — a missing mode exclusion in the calibration strategy
- DVP&R fording requirement signed off on Day 3 of the trial

---

## Scenario 05 — Stealth Mode Acoustic Limit Exceeded

**Topic:** Stealth mode combustion noise, pilot injection NVH optimisation, idle speed calibration

---

**S — Situation:**

During acoustic signature testing for stealth mode compliance on a Special Operations wheeled vehicle, the pass-by noise measurement at 10m recorded **78 dB(A)** — 6 dB above the 72 dB(A) MoD contract requirement. The vehicle was in stealth mode (silent approach), stationary idle, no ancillaries active. The dominant noise source identified by the acoustic team was combustion noise from the diesel engine — not tyre, transmission, or wind noise. The test was conducted at an MoD acoustic range with repeatable conditions. Failure to meet this requirement would trigger a contract penalty clause.

**T — Task:**

Reduce the in-vehicle diesel combustion noise signature to below 72 dB(A) at 10m in stationary idle stealth mode, without increasing fuel consumption or exhaust temperature beyond allowable limits for the stealth thermal signature constraint.

**A — Actions:**

1. **Measured cylinder pressure and computed dP/dθ (pressure rise rate).**
   Using kistler piezo-electric pressure transducer on cylinder 1: `dP/dθ_max = 14.2 bar/°CA` at idle in stealth mode.
   Literature and internal benchmarks indicate dP/dθ < 8 bar/°CA is required for low-noise diesel combustion. The stealth mode calibration had not specifically addressed combustion noise — it had only reduced engine speed slightly (750 → 650 rpm).

2. **Analysed the current pilot injection calibration in stealth mode.**
   At the stealth mode idle condition: `InjQty_Pilot = 0.5 mg/stroke`, `InjTiming_Pilot = –14 °CA before main injection`.
   This was identical to road-normal mode — the stealth mode had not modified pilot injection parameters.

3. **Developed a pilot injection optimisation strategy specifically for stealth mode:**

   **Action A — Increase pilot quantity:** Swept pilot quantity from 0.5 → 2.0 mg/stroke in 0.25 mg steps at idle, measuring dP/dθ and dB(A) at each step.
   Result: at 1.5 mg/stroke, dP/dθ dropped to 7.8 bar/°CA; further increase to 2.0 provided marginal additional benefit with smoke risk.

   **Action B — Retard main injection timing in stealth mode:** Applied –3° retard on `InjTiming_Main_Map` specifically for stealth idle cell. Retarded main injection reduces the peak pressure rise rate further but increases BSFC and EGT.
   Checked EGT at retarded timing: +28°C increase — within the 50°C budget allowed for stealth EGT constraint.

   **Action C — Add second pilot injection (split pilot):** Configured a secondary pilot event at –25 °CA before main, with 0.3 mg/stroke — this further pre-warms the charge gradually, reducing ignition delay of the main injection.

   **Action D — Reduce idle speed to 580 rpm:** Engine combustion frequency at 580 rpm = 19.3 Hz (4-cylinder) — placed below the dominant panel resonance of the hull at 22 Hz. Validated that 580 rpm provided stable combustion with the increased pilot quantity. Previously 650 rpm was creating a hull resonance amplification of +3 dB.

4. **Measured acoustic result with each change applied cumulatively.**

**R — Result:**

- Final noise measured: **68.5 dB(A) at 10m** — 3.5 dB below the 72 dB(A) limit (**PASS**)
- dP/dθ reduced from 14.2 → 7.2 bar/°CA
- BSFC increase at stealth idle: +6 g/kWh (acceptable — idle fuel consumption is a minor mission contributor)
- EGT increase: +24°C (within +50°C allowed thermal budget)
- Smoke: FSN 0.6 (well below limit)
- Contract requirement met; acoustic test signed off by independent acoustic assessor

---

## Scenario 06 — DPF Regeneration During Tactical Approach

**Topic:** DPF regeneration inhibit strategy, soot management, post-inhibit recovery

---

**S — Situation:**

During a tactical field trial, the vehicle's DPF automatic regeneration unexpectedly initiated while the vehicle was conducting a slow-speed approach under stealth conditions. The regen event raised EGT from 380°C to 620°C and caused visible exhaust smoke from the post-injection hydrocarbon loading. Both the thermal signature (IR spike) and the visual exhaust smoke violated the tactical concealment requirement. The regeneration ran for 22 minutes. The situation was raised by the commanding officer as a programme-blocking observation — an uncontrolled regen during real operations could compromise mission security.

**T — Task:**

Implement a calibration strategy that unconditionally inhibits DPF regeneration in stealth mode and any tactical mode, while managing soot accumulation so the DPF does not become blocked during extended operations without road mode recovery opportunities.

**A — Actions:**

1. **Analysed why regen initiated in stealth mode.**
   The `DPF_Regen_Inhibit_SteathMode` flag existed in the calibration but was set to `0` (disabled inhibit = regen allowed). Initial review showed the flag had been set during a calibration session 3 revisions prior but was then overwritten during an automated table copy from the road-mode calibration variant. The CDM diff log confirmed the overwrite — a variant management gap.

2. **Set `DPF_Regen_Inhibit_StealthMode = 1` (inhibit) for all tactical modes:** stealth, rock crawl, water fording, sand, mud, and a new `TacticalApproach` mode added at customer request.

3. **Assessed soot accumulation risk during extended inhibit.**
   Typical combat sortie duty cycle: 4 hours, 60% tactical mode. At normal soot load rate with EGR-heavy calibration, soot accumulation = approximately 1.5 g/L per hour of low-load operation. Maximum inhibit without soot overload = approximately 3 hours before approaching warning threshold (8 g/L).
   At 4-hour sortie: potential soot load at end = 6 g/L — below warning, above normal regen trigger (4 g/L).

4. **Implemented post-tactical forced regen strategy:**
   Created a new `PostTacticalRegen_Required` flag:
   - If tactical mode has been active for cumulative > 90 minutes: set flag = TRUE
   - On next road mode entry at speed > 60 km/h: initiate forced passive regen using elevated EGT (no post-injection — uses elevated baseline combustion temperature and oxidation catalyst)
   - If road mode not available within 30 minutes of flag setting: initiate active regen (standard post-injection) but only if vehicle not in ANY inhibit mode

5. **Added operator HMI warning:**
   Created DTC `P2463_INFO — DPF_PostTactical_Regen_Recommended`: informs vehicle crew/commander that a maintenance drive cycle activity is required after tactical operations. Not a fault, not a restriction — information only.

6. **Validated the full scenario**: simulated 4-hour tactical cycle, confirmed:
   - Zero regen events during tactical inhibit period
   - Post-tactical auto-regen triggered correctly within first 15 minutes of road mode
   - Soot model consistent with measured DPF differential pressure sensor throughout

**R — Result:**

- Zero uncontrolled regen events in 6 subsequent tactical field trial days (**PASS**)
- Soot load never exceeded 8 g/L (warning threshold) during any simulated mission profile
- Post-tactical regen confirmed successful in all 12 test cycles
- DPF differential pressure remained < 25 kPa throughout (within DPF lifetime pressure limit)
- Customer signed off the solution; DPF regen inhibit added to tactics manual as standard procedure

---

## Scenario 07 — High-Altitude Torque Derating Excess at 4,500m

**Topic:** Altitude compensation calibration, boost scheduling, compressor surge avoidance

---

**S — Situation:**

During high-altitude validation at 4,200m ASL in South America, the vehicle demonstrated acceptable performance at 3,000m (–12% torque vs sea level, within the –15% limit) but at 4,200m the measured torque shortfall reached **–38%** versus sea level — more than double the allowed –25% derating. Gradeability at 4,200m was 41% instead of the required 60%. The programme had contracted to operate in an Andean theatre of operations where altitudes above 4,000m are routine. The customer witness was present for the trial.

**T — Task:**

Understand why the altitude derating was disproportionately large at high altitude (above 4,000m), implement a calibration fix, and demonstrate the required performance within the 5-day trial window.

**A — Actions:**

1. **Measured boost pressure at 4,200m and compared to model predictions.**
   At 4,200m, atmospheric pressure = 60.5 kPa.
   Measured `MAP_kPa` at full load = 158 kPa (absolute). Expected from turbo map = 175 kPa.
   Shortfall in boost = 17 kPa — this translated directly to the torque shortfall via the air density reduction.

2. **Examined the VGT calibration at altitude.**
   The `VGT_Position_Alt_Correction` map (which should close the VGT vanes at altitude to increase boost ratio) had values that only extended to **80 kPa altitude** in the lookup table axis. Above 80 kPa input (i.e., below 80 kPa ambient = above ~2,000m) the table returned the **last defined value** (flat extrapolation) — the calibration was never extended to the 60 kPa range.

3. **Extended the VGT altitude correction table to 55 kPa (beyond the max required altitude of 4,500m = 57 kPa).**
   Used the turbocharger compressor map to compute the maximum VGT closure angle at 60 kPa before entering the surge region. Added a 10% margin from the surge boundary.
   Extended `VGT_Position_Alt_Correction` table: at 60 kPa, added +22% VGT closure correction (close vanes more to maintain boost ratio).

4. **Re-checked surge risk.**
   At the extended VGT closure, measured compressor outlet pressure ratio = 2.9:1. From the compressor map (provided by turbo supplier), surge boundary at this speed was at pressure ratio = 3.1:1. Margin = 6.9% — documented as within acceptable range with a note to re-check under engine transient conditions.

5. **Also optimised `Boost_Pressure_Target` at altitude:**
   At 60 kPa ambient, the original boost target was 250 kPa absolute (2.5 bar) — appropriate for sea level. Added an altitude-based target increase to 265 kPa at 60 kPa ambient to compensate for the lower density air (more boost mass needed for same torque).

6. **Road-mapped with turbocharger supplier:** confirmed extended VGT range is within actuator mechanical limit (motor current spec).

**R — Result:**

- Torque at 4,200m with updated calibration: sea-level minus **22%** (**PASS**, spec ≤ –25%)
- Gradeability at 4,200m: 56% (spec = 60% — marginally below; agreed with customer that 56% is acceptable based on revised operational altitude cap in the theatre of 4,000m)
- No compressor surge observed in 6 hours of full-altitude testing
- Root cause: VGT altitude correction table axis not extended to the required altitude range — a calibration coverage gap
- Turbo supplier informed — corrected compressor map coverage document updated

---

## Scenario 08 — Transmission Shift Hunting on Sand

**Topic:** Shift schedule calibration, hysteresis tuning, TC calibration for loose terrain

---

**S — Situation:**

During sand dune testing in UAE conditions (+45 °C ambient), the vehicle exhibited continuous gear hunting between 3rd and 4th gear during low-speed dune climbing at approximately 25 km/h. The transmission cycled between 3rd and 4th gear approximately every 4–6 seconds, causing progressive momentum loss, increasing the risk of the vehicle becoming stuck on the face of the dune. After 3 minutes of hunting, the vehicle lost enough momentum to slip back. Gear hunting on soft terrain is a known operationally unacceptable condition.

**T — Task:**

Eliminate gear hunting in sand mode during dune climbing at 20–30 km/h without reducing fuel economy or responsiveness in road mode.

**A — Actions:**

1. **Analysed the shift pattern from TCM log.**
   Upshift to 4th triggered at: vehicle speed 27 km/h, pedal position 78%. Within 1.5s, momentum loss from the dune face dropped speed to 23 km/h → downshift to 3rd triggered at: vehicle speed 23 km/h, pedal position 82%. In 3rd, engine torque increased, speed rose to 27 km/h → upshift repeated. Classic hunting pattern.
   Hysteresis band: upshift at 27 km/h, downshift at 23 km/h = 4 km/h band. Motor calibration spec required > 6 km/h hysteresis to prevent hunting.

2. **Found calibration error: sand mode shift hysteresis was using the road-mode values.**
   The `ShiftHysteresis_SandMode` calibration table was mapped to the road-mode table by a global pointer — sand mode was not overriding the shift hysteresis values. This was a strategy implementation oversight.

3. **Separated the sand mode shift tables:**
   Created independent `Upshift_3to4_SandMode_Speed` and `Downshift_4to3_SandMode_Speed` lookups.

   **Adjusted values for sand mode:**
   - Upshift 3→4: raised threshold from 27 km/h → **35 km/h** (hold 3rd gear longer)
   - Downshift 4→3: lowered threshold from 23 km/h → **18 km/h** (allow more speed loss before downshifting)
   - Effective hysteresis band: 17 km/h (vs 4 km/h previously)

4. **Added gradient-hold logic for sand mode:**
   If `GradientEst > 15%` AND `SandMode_Active`: inhibit upshift beyond 3rd gear entirely below 30 km/h. Forces the driver to manually select 4th if required.

5. **Also softened TC lock-up in sand mode (secondary fix):**
   With the previous lock-up calibration, TC locked in 3rd gear above 20 km/h. Any deceleration from dune resistance caused an abrupt engine deceleration event (locked TC = direct coupling) which the shift logic interpreted as a vehicle deceleration → triggered downshift. Raised TC lock-up minimum speed in sand mode from 20 → 40 km/h.

**R — Result:**

- Zero gear hunting events in 45 minutes of continuous dune testing (previously hunting every 4–6 seconds)
- Vehicle successfully climbed the test dune face uninterrupted in 6/6 attempts (**PASS**)
- Road mode shift schedule completely unchanged (verified with road mode regression)
- Root cause: sand mode shift tables were incorrectly pointing to road mode values — a calibration table mapping error compounded by insufficient hysteresis for soft-terrain dynamics

---

## Scenario 09 — Engine Thermal Runaway in Hot Chamber at +55 °C

**Topic:** Thermal protection calibration, cooling fan duty map, derating cascade

---

**S — Situation:**

During a 4-hour hot-ambient soak and performance test in the Millbrook environmental test chamber (+55 °C chamber temperature), the engine coolant temperature progressively climbed from 92 °C (normal operating) to 112 °C over 45 minutes of sustained 80% load operation, triggering an emergency engine shutdown via the ECM protection pathway. The shutdown occurred during the middle of a continuous-load gradeability endurance run — a gate test. The vehicle's cooling system specification was designed to maintain ECT < 105 °C at 55 °C ambient under 100% continuous load.

**T — Task:**

Determine why the cooling fan calibration was insufficient to maintain ECT < 105 °C, implement a fix, and re-run the 4-hour endurance test without ECT exceedance.

**A — Actions:**

1. **Reviewed ECM logs: cooling fan duty cycle during the overtemperature event.**
   `Fan_Duty_pct` was logging at 72% during the period when ECT climbed from 100 → 112 °C. At 72%, the cooling fan was in the upper range but not at maximum (100%). The `Fan_Speed_Map[ECT][IAT]` should have saturated fan duty to 100% well before ECT reached 108 °C.

2. **Examined the fan duty map in detail.**
   `Fan_Speed_Map` at ECT = 105 °C, IAT = 55 °C: **72%**. The map was never extended to the ECT × IAT combination of [105°C, 55°C] — the table had been calibrated on bench with a maximum IAT of 40 °C. At IAT = 55 °C, the fan controller read the row for IAT = 40 °C (nearest neighbour, no interpolation available in this ECM version for this map) → clamp at 72%.

3. **Root cause confirmed: IAT axis in the fan map did not cover +55 °C.**
   The calibration was designed for a 40 °C maximum ambient vehicle (different programme origin). No one had extended the IAT axis to +55 °C when the dataset was ported to the defence programme.

4. **Extended the fan map:**
   Added IAT axis breakpoints at 45, 50, 55, 60 °C to the `Fan_Speed_Map`.
   Set fan duty at [ECT ≥ 100 °C, IAT ≥ 45 °C] = **100%** (maximum).
   Set fan duty at [ECT = 95 °C, IAT = 55 °C] = **85%** (proactive early response).
   Added `FanPreemptive_HighAmbient_Flag`: if IAT > 48 °C and vehicle has been running > 10 minutes: force fan to minimum 60% regardless of ECT (prevents thermal soaking under high ambient before ECT responds).

5. **Verified the fix on a bench thermal model (Simulink cooling circuit model) before re-running the chamber.**
   Simulation with new fan map: predicted ECT peak at +55 °C / 100% load = 101.4 °C. Chamber re-test scheduled for next available slot.

6. **Re-ran the 4-hour chamber endurance test.**

**R — Result:**

- ECT peak during 4-hour 55 °C chamber test: **102.8 °C** (spec < 105 °C — **PASS**)
- Fan duty reached 100% at minute 8 and held through the endurance run
- Zero emergency shutdowns, zero coolant overtemperature DTCs
- Root cause: fan duty map IAT axis truncated — missing high-ambient calibration range from programme porting
- Lesson learned: all maps with temperature or ambient-condition axes must have the axis coverage explicitly checked against the new programme's environmental envelope during calibration portability review

---

## Scenario 10 — DoE Model Quality Below 0.95 R²

**Topic:** DoE design quality, data outlier removal, re-design and re-test

---

**S — Situation:**

During the model-based calibration phase for EGR and VGT optimisation on a new 8-cylinder turbodiesel, the response surface model for NOx fitted from 18-run CCD DoE data produced R² = 0.72 — well below the 0.95 R² quality gate. Using a model of this quality for calibration would produce unreliable optimal values. The risk was that the NOx map derived from a poor model could have prediction errors of ±30%, potentially causing emissions exceedances on a customer-witnessed drive cycle 3 weeks later.

**T — Task:**

Diagnose why the model quality was poor, recover valid model data, rebuild the model to meet the R² ≥ 0.95 gate, and deliver calibration tables in time for the drive cycle test.

**A — Actions:**

1. **Residual analysis on the initial 18-run dataset.**
   Plotted Cook's Distance for all 18 design points. Runs 4, 11, and 16 had Cook's Distance > 1 — confirmed as high-leverage outliers. Reviewed raw data from those runs: run 4 had a step transient in engine coolant temperature during the measurement window (thermostat opening event — the measurement was not taken at steady state). Run 11: operator noted ECM DTC P0401 (EGR flow below threshold) during measurement — EGR was partially stuck during that run. Run 16: MAF sensor showed erratic oscillation (±20%) — suspected condensation event in test cell.

2. **Removed 3 outlier runs from the dataset:** residual dataset = 15 runs.
   Re-fitted the quadratic RSM with 15 points. New R² = 0.88 — improved but still below gate.

3. **Augmented the DoE design with 5 additional targeted points.**
   Identified regions of the design space with highest model uncertainty (using CDF confidence intervals): the VGT 20–30% range at high EGR rate had only 1 data point after outlier removal — insufficient for quadratic curvature estimation.
   Added 5 additional dyno runs targeting this region (took 6 hours of additional dyno time — approved by test lead given the downstream risk).

4. **Re-fitted model with augmented 20-run dataset (15 original + 5 new).**
   R² = 0.97, RMSE = 0.14 g/kWh on NOx (response range = 2.8 g/kWh → 5% RMSE/range).
   Lack-of-fit test p-value = 0.18 (> 0.05 — no significant lack of fit).
   Quality gate: **PASS**.

5. **Root cause documented:** Measurement stability criteria were not defined in the DoE test plan. The data collection script was capturing a 10-second average, but some runs had not stabilised before the window — steady-state criterion (ECT stability ±0.5 °C for 30 seconds, MAF stability ±2% for 20 seconds) was not checked before measurement was triggered.

6. **Implemented automated stability gate in the INCA ORION sweep script** for all future DoE campaigns.

**R — Result:**

- Final NOx model: R² = 0.97, meeting the 0.95 gate (**PASS**)
- Optimal calibration tables derived with ≥ 95% statistical confidence
- Drive cycle test completed with NOx measurement 11% below the target limit
- Process improvement: mandatory steady-state check function (`wait_stable()`) added to the DoE automation script — prevents future outliers from thermal transients or sensor faults

---

## Scenario 11 — Calibration Dataset Version Conflict

**Topic:** CDM management, A2L version control, calibration dataset integrity

---

**S — Situation:**

During final system testing, the test team reported that the vehicle was exhibiting maximum torque 12% below specification following an overnight ECM flash. The vehicle had been flashed with what was believed to be the latest validated calibration dataset. Gradeability on the 50% slope was below the DVP&R requirement. Programme management escalated immediately as this was a gate test 2 weeks before DVP&R closure.

**T — Task:**

Identify why the ECM was producing less than specified torque after the overnight flash, determine if the calibration or the software was at fault, and restore correct calibration immediately.

**A — Actions:**

1. **Connected INCA and read the A2L-decoded torque limit map from the ECM.**
   `TrqLim_Max_Map` read back from ECM: maximum cell value = 680 Nm. Expected: 780 Nm.
   The map was clearly holding a lower value than the validated dataset.

2. **Checked the flash log and CDM record.**
   The flash had used `CAL_Dataset_v4.6.cdf` — the correct latest validated version per the release log.
   However, cross-checking the CDM diff tool: `CAL_Dataset_v4.6.cdf` was linked to **SW_Baseline_009**. The ECM had been flashed with **SW_Baseline_010** the previous week (new software release). The A2L file for SW_010 had a different `TrqLim_Max_Map` memory address — the calibration file v4.6 written to SW_010 had written the torque limit value into a non-matching address.

3. **The written values went to an unrelated map (`ColdStart_InjQty_Correction`)**, and the `TrqLim_Max_Map` in SW_010 retained its default compile-time value of 680 Nm — hence the torque shortfall.

4. **Immediate action:** Re-flashed ECM with `CAL_Dataset_v4.7.cdf` — the version created for SW_Baseline_010. Verified by reading back the torque map via INCA: 780 Nm confirmed. Repeatable gate test run immediately — performance nominal.

5. **Root cause:** The release process allowed a calibration file linked to SW_009 to be applied to an ECM running SW_010. The CDM Studio release workflow did not enforce matching of SW baseline to calibration baseline before flash authorisation.

6. **Process fix implemented:**
   Added a mandatory SW baseline / calibration baseline compatibility check to the CDM flash workflow:
   - CDM Studio export script now reads the ECM software version (from UDS 0x22 F189) before flash
   - Compares against the SW baseline flag in the .cdf metadata
   - If mismatch: flash rejected with error `CAL_SW_MISMATCH — abort`
   - Override allowed only with Lead Calibration Engineer counter-signature

**R — Result:**

- Vehicle restored to correct calibration within 1.5 hours of incident report
- Gate test repeated: performance nominal, gradeability **PASS**
- Root cause fully closed; CDM workflow updated across all 3 active programmes
- No further cross-version flash incidents in subsequent 14 months

---

## Scenario 12 — EGR Valve Delayed Response from Packaging

**Topic:** Actuator lag compensation, packaging-driven calibration adjustment

---

**S — Situation:**

After installation of the EGR system into the hull-integrated packaging of the armoured vehicle (significantly longer EGR pipe run = 680mm vs the 250mm dyno bench installation), steady-state EGR-based NOx reduction was meeting targets, but during transient load increases NOx spiked to 6.2 g/kWh (limit = 4.5 g/kWh) before settling. The spike lasted 400–600ms per tip-in event. The transient NOx spike had not been seen during engine dyno calibration (short pipe) and appeared only after vehicle integration.

**T — Task:**

Identify why transient NOx spikes were occurring in the vehicle that were absent on the dyno, and implement a vehicle-specific calibration correction that eliminates the transient excess without degrading steady-state.

**A — Actions:**

1. **Measured EGR valve response time in the vehicle vs bench.**
   On bench (250mm pipe): command to actual EGR flow response = 110ms delay.
   In vehicle (680mm pipe + two additional bends): command to actual EGR flow response = **310ms delay**.
   The longer pipe adds 200ms of additional pneumatic lag (gas transit time + pressure equalisation).

2. **Identified the ECM's dynamic EGR control strategy.**
   The `EGR_Ctrl_LeadTime_ms` parameter (feed-forward advance on EGR during load transients) was set to 110ms — matched to the dyno installation. In the vehicle with 200ms additional lag, the EGR valve was opening 200ms too late relative to the fuel increase → N 200ms window of low EGR → NOx spike.

3. **Increased `EGR_Ctrl_LeadTime_ms` from 110 → 320ms.**
   This advanced the EGR valve opening command by 320ms ahead of the predicted load increase (based on the rate-of-change of pedal position signal).

4. **Validated the transient EGR response timing:**
   With 320ms lead time: EGR flow was established 15ms before the fuel mass increase — eliminating the lean NOx window. Transient NOx spike reduced from 6.2 → 3.8 g/kWh.

5. **Documented as a packaging-driven calibration note** in the release documentation:
   - Vehicle EGR transport delay = 310ms (bench = 110ms)
   - `EGR_Ctrl_LeadTime_ms` set to vehicle-specific value 320ms
   - This value must NOT be shared back to the bench calibration dataset
   - Added a calibration variant flag: `Packaging_EGR_Delay_Extended = TRUE` to indicate the vehicle-specific setting

**R — Result:**

- Transient NOx peak reduced from 6.2 → 3.8 g/kWh (**PASS**, limit = 4.5 g/kWh)
- Steady-state NOx unchanged (EGR steady-state maps not modified)
- No impact on smoke during transient (confirmed — smoke remained < FSN 0.8)
- Lesson: packaging changes that increase actuator transport delays of > 50ms require a dedicated recalibration of feed-forward lead times — this must be a checklist item during vehicle integration change review

---

## Scenario 13 — Driveline Shunt During Tip-In at Rock Crawl Speed

**Topic:** Torque ramp calibration, driveline NVH, low-speed torsional control

---

**S — Situation:**

During trials of the rock-crawl mode at 0–3 km/h with all axles locked, test drivers consistently reported a severe "clonk" and jerk sensation when applying throttle from a brief idle (simulating wheel obstacle negotiation). The vibration was severe enough to cause crew head movement — assessed as potentially NVH-risk and incompatible with the delicate sensor equipment mounted in the hull. ACM analysis of the IMU data showed longitudinal acceleration jerk of 18 m/s³ — the allowable limit was 8 m/s³ for crew and 5 m/s³ for sensitive equipment.

**T — Task:**

Reduce the longitudinal jerk during throttle tip-in in rock crawl mode to below 5 m/s³ while retaining the immediate torque response required for obstacle clearance.

**A — Actions:**

1. **Identified the jerk source: torque reversal.**
   The driveline in 4L all-axle-lock has near-zero compliance once all diffs are locked — the full driveline torsional stiffness acts directly. When torque demand jumped from 0 (idle overrun state) to 400 Nm (first pedal touch), the gear mesh backlash and rubber coupling in the transmission output shaft absorbed the torque step as a single impact event — hence the clonk.

2. **Measured the rate of torque increase on tip-in via INCA:**
   `TorqueRequest_RampRate_TipIn` in rock crawl mode = **unlimited** (a placeholder of 9999 Nm/s inherited from a default dataset). The torque went from 0 to 400 Nm in < 40ms — approximately 10,000 Nm/s ramp rate.

3. **Determined the acceptable ramp rate:**
   At 5 m/s³ jerk limit and vehicle mass 18,000 kg: max jerk rate = 5 × 18,000 = 90,000 N·m total. With final drive ratio 35:1 and tyre radius 0.45m, this equates to approximately 1,160 Nm/s at the transmission output — or approximately 33 Nm/s at the engine output shaft. Applied a safety margin of 50%: target ramp rate = 50 Nm/s.

4. **Set `TorqueRequest_RampRate_TipIn_CrawlMode = 50 Nm/s` (vs unlimited previously).**

5. **Protected obstacle clearance:** confirmed that at 50 Nm/s ramp rate, full torque (450 Nm) is available within 9 seconds from idle — acceptable for slow rock crawl where the driver is managing each wheel contact point individually.

6. **Also added `Backlash_Preload_Torque = 15 Nm`:** a continuous low-torque preload prevents the driveline from going to zero backlash/reversal during idle in crawl mode — keeping the gear mesh loaded and eliminating the clonk from mesh engagement.

**R — Result:**

- Measured jerk on test: peak 4.1 m/s³ (**PASS** for sensitive equipment limit of 5 m/s³)
- Clonk eliminated — no audible impact reported by test drivers in 3 hours of rock crawl testing
- Torque delivery profile: smooth ramp, no step; obstacle negotiation capability unaffected
- Jerk reduced from 18 → 4.1 m/s³ (77% reduction)

---

## Scenario 14 — NOx Emissions Exceedance on MoD Certification Cycle

**Topic:** EGR calibration, SCR dosing, cycle-specific calibration optimisation

---

**S — Situation:**

During a formal emissions measurement on the MoD-specific duty cycle (representative of operating pattern: 40% low load urban, 30% sustained gradient, 30% high-speed transit), the vehicle produced NOx = **5.2 g/kWh** against a contractual limit of 4.0 g/kWh (programme-specific target, not legally mandated but commercially binding). The exceedance was consistently in the sustained gradient phase of the cycle, where EGR operation was limited by the calibration. The test was witnessed and the result was reported as non-compliant.

**T — Task:**

Reduce cycle-average NOx to below 4.0 g/kWh on the MoD duty cycle without exceeding the 1.5 FSN smoke limit or reducing the gradeability performance.

**A — Actions:**

1. **Modal NOx analysis across the duty cycle.**
   Used Python to parse the MDF4 PEMS (Portable Emissions Measurement System) data file and correlate NOx against engine speed/load operating point. Identified: 78% of the NOx exceedance occurred in the 1,200–1,600 rpm, 60–80% load region — the sustained gradient phase.

2. **Examined EGR calibration in the affected region.**
   `EGR_Rate_Map` at 1,400 rpm, 70% load = 8%. Competitor benchmark for similar engine at this condition: 18–22%. The EGR rate had been reduced in this region during an earlier calibration session to prevent smoke during high-gradient operation (safety calibration applied without re-checking NOx impact).

3. **Re-evaluated smoke risk at increased EGR.**
   Ran a targeted mini-DoE on the dyno: at 1,400 rpm, 70% load, swept EGR from 8% to 25% in steps of 4%, measuring NOx, Smoke, BSFC, and EGT.
   Result: EGR 18% gave NOx = 3.2 g/kWh, Smoke = 0.9 FSN (below 1.5 limit), BSFC +2.8% (acceptable).

4. **Increased EGR in the gradient operating region:**
   `EGR_Rate_Map` at 1,200–1,600 rpm, 60–85% load band: increased from 8–12% → 16–20%.
   Applied the change to road normal, gradient, and high-mobility modes only (not stealth — EGR in stealth already maximised for noise).

5. **SCR dosing check:**
   The SCR AdBlue dosing map was confirmed to be at the boundary of the dosing rate — the SCR was not underperforming, it was the engine-out NOx that was too high. No SCR change required.

6. **Re-run the MoD duty cycle** with updated EGR map.

**R — Result:**

- Cycle-average NOx: **3.6 g/kWh** (**PASS**, limit = 4.0 g/kWh)
- Smoke: FSN 1.1 across the cycle (under 1.5 limit — **PASS**)
- Gradeability unchanged (confirmed with post-change gradeability test)
- BSFC change: +1.9% on the MoD cycle (accepted by programme — within 2% fuel economy margin)
- Emissions contract requirement met; customer signed off formal test report

---

## Scenario 15 — A2L Mismatch Causing Incorrect Value Flash

**Topic:** A2L configuration management, ECM data integrity, calibration safety process

---

**S — Situation:**

Following a minor software patch (SW v1.5.1 → v1.5.2, a single-function bug fix in the CAN gateway), an ECM was re-flashed with a calibration dataset using the A2L file from v1.5.1 without updating the A2L to v1.5.2. The software patch had relocated the `TrqLim_Max_Map` internal table by 64 bytes due to a struct size change in the gateway module. During the next test session, the vehicle exhibited severe erratic engine behaviour — uncontrolled torque surges and a DTC storm. The test was abandoned.

**T — Task:**

Restore the ECM to correct known-good calibration, determine the full impact of the A2L mismatch write, document which values were corrupted, and prevent recurrence.

**A — Actions:**

1. **Immediate safe-state: engine was not re-started** until the calibration was characterised. Safety risk assessment: worst case — corrupted torque limit could allow engine overspeed. Decision: do not power ECM until safe calibration is restored.

2. **Read entire ECM calibration via INCA using the v1.5.2 A2L** and compared all maps to the intended calibration dataset (golden reference stored in CDM).
   Identified 3 maps that were corrupted (received values intended for a different address):
   - `TrqLim_Max_Map`: received values from `Fan_Speed_Map` (wrong physical values = fan duty percentages interpreted as Nm torque = up to 780 Nm at all cells — erratic)
   - `Fan_Speed_Map`: received `TrqLim_Max_Map` values (temperatures interpreted as fan duties)
   - `ColdStart_InjQty_Correction`: received data from an unrelated calibration section (random garbage values)

3. **Re-flashed ECM with correct v1.5.2 A2L and the latest validated calibration dataset.**
   Confirmed all three corrupted maps now match golden reference.

4. **Reviewed all A2L change notes between v1.5.1 and v1.5.2:**
   Identified 4 map address changes resulting from the gateway struct resize. Created an A2L delta report documenting all address changes.

5. **Immediate short-term process fix:**
   Added a step in the CDM flash procedure: before any flash, compare the A2L SW version tag (embedded in the A2L header) against the SW version read from the ECM via UDS DID 0x22 F189. Block flash if mismatch.

6. **Long-term fix:**
   Worked with SW team to embed A2L version hash into the ECM software binary. At flash time, INCA extracts the hash and verifies against the A2L being used. Mismatch = flash aborted automatically, no human decision required.

**R — Result:**

- ECM restored to correct calibration; vehicle functioned correctly on first re-test
- No hardware damage (corrupt values were outside hardware actuator limits, so safety monitors had cut response before damage occurred — protection system worked as designed)
- Root cause: A2L version not updated following SW patch — a process gap
- 0 further A2L mismatch events in 18 months following automated A2L compatibility enforcement

---

## Scenario 16 — Python Automation Reducing Analysis Cycle Time by 40%

**Topic:** Calibration data automation, batch MDF processing, anomaly detection

---

**S — Situation:**

The programme was running 6 calibration test sessions per week on 3 separate test rigs (engine dyno, PT dyno, HIL bench). Each session generated 3–8 MDF4 measurement files averaging 2.5 GB each. Manual post-processing by calibration engineers was consuming 12–15 hours per week (2 engineers × 6–7.5 hours each) — extracting key metrics, plotting signals, checking against limits, and writing test summaries. This was delaying calibration outcome decisions by 2–5 days and was identified as a programme bottleneck.

**T — Task:**

Design and implement a Python automation framework that processes all weekly MDF4 files overnight, produces per-run analysis reports, flags limit violations, and generates a weekly comparison dashboard — targeting a 40% reduction in engineer analysis time.

**A — Actions:**

1. **Mapped the current manual process** (5 steps, times measured):
   - Open MDF in INCA MDA: 8 min/file
   - Extract 15 key channels and compute means/maxes: 25 min/file
   - Check against test spec limits: 10 min/file
   - Generate plot PDF: 15 min/file
   - Write session summary in JIRA: 20 min/file
   Total: ~78 min/file × 30 files/week = 39 hours/week → absorbed by 2 engineers = 19.5 h/engineer

2. **Developed the automation framework** (Python, 3 weeks development, iterative with engineer feedback):

   Core components:
   - `CalibrationAnalyser` class (asammdf + pandas): load MDF, extract channels, compute statistics
   - `LimitChecker`: validate all channels against JSON-defined limits (per test type)
   - `AnomalyDetector`: rolling z-score outlier detection across all channels
   - `BSFCMapBuilder`: calculate 2D BSFC map from each steady-state run
   - `ReportGenerator`: auto-generate HTML + PDF report (matplotlib + Jinja2 template)
   - `JiraUploader`: POST report to JIRA issue via REST API, attach PDF
   - `WeeklyDashboard`: compare all 30 runs in a merged trend chart (NOx, BSFC, EGT, Smoke over time)

3. **Set up nightly automated batch run:**
   - Cron job at 23:00 scans the shared NAS drive for new MDF4 files
   - Processes all new files using `batch_analysis()` function
   - Sends email summary at 06:00 with PASS/FAIL count and violation summary
   - Engineers arrive in the morning to a complete analysis — they review outputs rather than generating them

4. **Iterative refinement over 4 weeks:**
   - Engineers reported 3 cases where automated outlier detection flagged a valid measurement as anomaly (thermal soak plateau) → added `exclude_windows` config feature
   - Added custom steady-state window detection (not just time-based but stability-criterion based)
   - Integrated with CDM Studio API to auto-tag run results against the calibration dataset version

**R — Result:**

- **Analysis time reduced from 78 min/file → 4 min/file** (engineer review of auto-generated report only)
- Weekly saving: 39 hours manual → 4 hours review = **35 hours saved per week** (90% reduction in raw processing time vs the 40% target)
- Anomaly detection caught a sensor drift issue (EGT thermocouple reading +45°C offset for 3 consecutive days) that would likely have been missed in manual review — preventing 6 calibration decisions from being based on wrong EGT data
- Framework adopted by 2 other programmes within the company → shared maintenance model
- Presented at internal engineering excellence forum; commended by Head of Powertrain Engineering

---

## Scenario 17 — Water Fording HVAC Intake Failure During Immersion

**Topic:** HVAC system calibration, mode interaction, crew compartment sealing

---

**S — Situation:**

During a fording trial at 1.2m water depth, crew reported that the vehicle interior was flooding through the HVAC (air conditioning / heating) system air intake ducts. Water entered the below-floor ductwork and began pooling in the crew compartment footwell. The HVAC system had a mechanical flap that was supposed to close on fording-mode selection, but it was found open during the immersion event. Additionally, the cabin pressure balance was lost causing water seepage around door seals. This was a safety and capability issue — crew compartment ingress of water could damage electronics and endanger crew.

**T — Task:**

Identify why the HVAC intake flap was not closing in fording mode and implement a calibration and control strategy fix to ensure the crew compartment remains sealed during fording.

**A — Actions:**

1. **Reviewed the HVAC control module (BCCM) CAN message log.**
   In fording mode, the ECM broadcasts a `FordingMode_Active = TRUE` signal on the vehicle CAN. The BCCM should respond by closing the intake flap via a relay command.
   Log review: `FordingMode_Active` was being transmitted correctly. However, the BCCM was not responding — `HVAC_IntakeFlap_Cmd` remained at `OPEN`.

2. **Investigated BCCM software version.**
   BCCM SW v2.1 included the fording mode intake flap response. The BCCM on the test vehicle had **SW v1.9** (older version from initial vehicle build, not yet updated in the integration phase). v1.9 did not parse the `FordingMode_Active` CAN signal — the signal was added in v2.0.

3. **Immediate interim calibration workaround (while BCCM SW was updated):**
   Modified the ECM to transmit the fording mode intent 60 seconds before vehicle entry into water (user activates fording mode on the bank before entry). Added a `HVAC_Shutdown_PreFording_Cmd` direct relay signal routed through the ECM — bypassing the BCCM and directly opening the relay for the intake flap motor. This ensured flap closure regardless of BCCM SW version.

4. **Coordinated with BCCM SW team:** BCCM SW v2.1 applied to the vehicle within 2 days.

5. **Added cabin overpressure calibration:**
   With the intake flap closed during fording, the interior air supply stops. To prevent negative pressure (which draws in water around seals), implemented `HVAC_FordingMode_RecircOnly = TRUE`: HVAC switches to full recirculation (internal air only), with the fan maintaining slight positive pressure in the cabin. Calibrated fan duty during fording: 35% (enough for positive pressure without overloading the battery).

6. **Validated** by repeating the 1.2m fording trial with updated BCCM SW v2.1 and new cabin overpressure calibration.

**R — Result:**

- Zero water ingress through HVAC during 1.2m fording trial (8 consecutive crossings)
- Cabin pressure maintained at +15 Pa relative to exterior (measured by cabin differential pressure sensor) — confirmed adequate seal
- Root cause: BCCM SW version gap (fording mode CAN signal not parsed); compounded by insufficient integration test coverage of BCCM-ECM interface in fording mode
- Test coverage gap addressed: added BCCM fording mode response check to the integration smoke test suite

---

## Scenario 18 — Multi-Fuel Adaptation Calibration

**Topic:** Multi-fuel capability, calorific value adaptation, fuel quality detection

---

**S — Situation:**

A defence vehicle programme required NATO multi-fuel capability (JP-8 aviation fuel, AVTUR, standard diesel, and locally sourced diesel of variable cetane quality). During trials with JP-8 fuel (cetane number ~45 vs standard diesel ~52), the vehicle exhibited:
- Extended white smoke during cold start
- 8% reduction in full-load peak torque
- Reduced combustion stability at idle (±80 rpm idle speed oscillation)
These were not unexpected physically, but no adaptation strategy existed in the ECM calibration — the engine behaved the same regardless of fuel type.

**T — Task:**

Develop and implement a multi-fuel adaptation calibration strategy that enables satisfactory operation across all NATO fuel types without requiring separate flash for each fuel type.

**A — Actions:**

1. **Characterised the differences between the four fuel types on the engine dyno.**
   Key parameters measured at the same injection quantity and timing:
   - Net calorific value (NCV): diesel = 43.0 MJ/kg, JP-8 = 43.2 MJ/kg, low-cetane diesel = 41.9 MJ/kg
   - Cetane number: standard diesel 52, JP-8 45, AVTUR 40, low-cetane 40–44
   - Viscosity: JP-8 lower viscosity — spray pattern changes slightly, earlier evaporation
   - Density: JP-8 lower than diesel — same volume injected = less mass injected

2. **Developed two fuel quality adaptation signals:**

   **Signal 1 — Fuel density adaptation:**
   The fuel rail pressure model uses assumed fuel density (0.835 g/cm³ for diesel). JP-8 density = 0.800 g/cm³.
   If density is not corrected: injected fuel mass overestimated by ~4.2% → rich mixture.
   Added `FuelDensity_Adaptation_Factor` calibrated as follows:
   - Default: 0.835
   - Detected via: a combustion model observer comparing expected vs actual torque response
   - After 3 minutes of operation: adaptation converges to estimated actual fuel density
   - Range: 0.780–0.860 g/cm³ (covers all NATO fuels)

   **Signal 2 — Cetane number estimation:**
   Low cetane = longer ignition delay. Detectable as: longer time from injection to first pressure rise (from crank sensor data analysis implemented in the ECM algorithm).
   Added `IgnDelay_Feedback_deg` observable from crank-speed derivative pattern.
   When IgnDelay_Feedback > threshold: ECM applies `PilotAdv_LowCetane_Correction` = +3° advance on pilot injection (earlier pilot = more pre-heat time = compensates for longer ignition delay of low-cetane fuel).

3. **Calibrated the adaptation convergence time:**
   After fuelling with a different fuel type: target for full adaptation = 10 minutes of engine operation. During adaptation, BSFC and smoke may be slightly elevated (acceptable — documented in operator manual as "10-minute quality period").

4. **Cold start penalty for low-cetane fuel:**
   Added `GlowPlug_LowCetane_Extension_s`: if last run's cetane estimate < 46, extend glow plug pre-heat by 5 seconds on next cold start.

**R — Result:**

- JP-8 cold start: white smoke cleared within 120 seconds (vs 4+ minutes without adaptation)
- Full-load torque on JP-8 with adaptation: –3.1% vs diesel (vs –8% without) — within the –5% NATO multi-fuel tolerance
- Idle stability on AVTUR: ±22 rpm (vs ±80 rpm without adaptation) — PASS
- All four NATO fuels demonstrated acceptable operation within the adaptation window
- Customer signed off multi-fuel capability requirement; capability documented in the vehicle technical manual

---

## Scenario 19 — DFMEA Gap in Torque Limiter Calibration Sign-Off

**Topic:** Functional safety, DFMEA participation, calibration limit review

---

**S — Situation:**

During a customer-led functional safety audit (ISO 26262 compliance review) of the powertrain DFMEA package, the auditor identified that the `TrqLim_Max_Map` calibration parameter had no confirmed A2L minimum/maximum limit enforcement — the A2L physical minimum and maximum were both set to `0` (effectively unlimited). This meant a calibration engineer could flash a torque value of 9999 Nm into the ECM with no software check to prevent it. The safety goal "Prevent driveline overload leading to loss of control" was mapped to this parameter as a first-line protection element. The finding was raised as a critical DFMEA gap with a severity level of 9 (potential for vehicle loss of control).

**T — Task:**

Close the DFMEA finding by implementing and evidencing quantitative A2L limits on the `TrqLim_Max_Map` and all other safety-relevant calibration parameters, and deliver the closure evidence within 15 working days.

**A — Actions:**

1. **Identified all safety-relevant calibration parameters from the DFMEA.**
   Worked with the Systems Safety Engineer to collect all DFMEA lines where the mitigation referenced "calibration range limit" as a prevention measure. Identified 23 calibration parameters across the ECM and TCM.

2. **For each parameter, sourced the hardware design limit:**
   `TrqLim_Max_Map`:
   - Driveline designer: maximum torque without guaranteed failure = 950 Nm (over-peak)
   - Maximum torque for the 18,000-cycle fatigue life = 820 Nm
   - Current calibration maximum value: 780 Nm
   - Therefore safe A2L maximum = 820 Nm (fatigue limit — more conservative than over-peak)
   - A2L minimum = 0 Nm (engine must be able to output zero torque for E-stop)

3. **Set physical limits in the A2L for all 23 parameters** using INCA A2L Editor:
   Each parameter's `PHYS_UPPERLIMT` and `PHYS_LOWERLIMIT` set to hardware-validated bounds. Any attempt to write outside these bounds via INCA would generate an immediate warning and require manual override with engineer acknowledgement.

4. **For the 5 ASIL C/D parameters**, implemented additional software range check in the ECM software (coordinated with SW engineer):
   Added a startup self-test that reads the calibration values and confirms they are within the design-intent bounds. If any value exceeds bounds at startup: ECM enters limp-home mode and sets a safety-relevant DTC.

5. **Created a Calibration Limit Rationale Document** for each of the 23 parameters:
   - Parameter name, A2L limits set, rationale (hardware limit, safety goal, standard)
   - Reviewed and signed by Lead Calibration Engineer + Systems Safety Engineer
   - Archived in DOORS with traceability to DFMEA line number

6. **Re-ran the DFMEA with the audit team to formally close each finding.**

**R — Result:**

- All 23 DFMEA calibration limit findings closed within 12 working days (3 days ahead of deadline)
- A2L limits confirmed in INCA — demonstrated to auditor live on screen
- Software startup range check demonstrated: deliberately flashing an out-of-range value confirmed DTC and limp-home response as designed
- Audit finding formally closed; ISO 26262 compliance document updated
- Process improvement: added "A2L limit completeness check" as a mandatory item in the programme's DFMEA template — ensuring every calibration parameter referenced in the DFMEA has documented, validated limits before design freeze

---

## Scenario 20 — Emergency Limp-Home Calibration During Field Validation Trial

**Topic:** Limp-home strategy calibration, field expedient fix, remote calibration deployment

---

**S — Situation:**

During a remote field validation trial in a desert test location (no workshop facilities, 300km from the nearest service depot), the EGR cooler developed an internal leak causing coolant contamination of the EGR gas path. A DTC was set: `P0401 — EGR Flow Insufficient / Cooler Contamination Suspected`. The ECM correctly detected the fault and entered limp-home mode, restricting engine torque to 45% and disabling EGR. The vehicle was operational but severely underpowered — unable to meet the performance requirements of the day's scheduled trials. The programme had 3 days of remote trial time remaining before the team relocated. No replacement EGR cooler was available.

**T — Task:**

Implement a remote calibration update (via laptop + CAN interface) that allows the vehicle to complete the remaining trial objectives at acceptable performance while operating with the EGR system permanently disabled, managing the NOx and thermal consequences, and not causing further hardware damage.

**A — Actions:**

1. **Assessed the hardware damage and ongoing risk.**
   EGR cooler leak: coolant was entering the EGR system but the volume was low (no white smoke from exhaust — coolant not reaching cylinders). EGR valve confirmed jammed partially open by coolant residue (visual inspection). Decision: override EGR control entirely — physically close EGR valve passivation (wire-tied closed), calibration change to not command EGR.

2. **Modified calibration for EGR-disabled operation:**

   **Change 1 — Disable EGR:**
   Set `EGR_Enable_Override = DISABLED` in ECM working page via INCA. This removed all EGR commands and cleared the `P0401` root DTC (cooler now bypassed by design).

   **Change 2 — NOx consequence management:**
   With no EGR: expect NOx + 80–120% vs baseline. For a MoD-exempt programme on a remote desert trial: NOx increase is acceptable. Documented as a field deviation in the programme log.

   **Change 3 — EGT management:**
   Without EGR: combustion temperatures increase — estimated EGT rise of +60–80°C. Re-checked `EGT_Protection_Map`: at anticipated EGT level (+65°C), the protection would derate torque at 15%. Pre-emptively relaxed the EGT derating threshold by +50°C to allow the engine to run at the higher EGT without triggering derating (justified: trial of maximum 3 days, then EGR cooler replaced before any further running).
   Added a trial time limit: flag `EGT_FieldDeviation_Active = TRUE` — automatically expires in 72 hours and resets all protection thresholds.

   **Change 4 — Remove limp-home torque restriction:**
   With EGR intentionally disabled and documented, the `P0401 limp-home torque limit` was no longer appropriate. Set `LimpHome_TrqLimit_EGR_Fault = FALSE` in the calibration override table. Full torque restored.

3. **Deployed the field calibration change via INCA laptop + USB-CAN interface** at the trial site (no workshop needed — only ECM access via diagnostic connector). All changes on Working Page only — Reference Page protected. Total time to deploy: 35 minutes.

4. **Ran a quick validation test:** gradeability on a 30% gradient, acceleration run, 30-minute sustained high load. Confirmed:
   - Full torque available
   - EGT peaked at 730°C (within the relaxed threshold, below turbo limit of 780°C)
   - No further DTCs set
   - No further coolant loss (EGR valve physically locked closed)

**R — Result:**

- Remaining 3 trial days completed successfully at full performance
- Gradeability: PASS on all scheduled test slopes
- EGT remained < 735°C throughout — no thermal damage
- NOx increase: estimated +90% vs baseline — documented as MoD-exempt field deviation, no programme impact
- EGR cooler replaced at programme depot; standard calibration restored; no permanent engine damage
- Lesson documented: "Emergency limp-home calibration procedure" added to the powertrain trial team handbook — enabling future field fixes to be executed consistently, with a standard approval chain and automatic time-limiting mechanism built into the ECM calibration strategy

---

## STAR Scenario Index by Competency

| Competency Area | Scenarios |
|---|---|
| Cold weather / environmental extremes | 01, 09 |
| Gradeability and driveline | 02, 13 |
| Combustion and emissions | 03, 14 |
| Water fording mode | 04, 17 |
| Acoustic / stealth mode | 05 |
| DPF / aftertreatment | 06 |
| Altitude calibration | 07 |
| Transmission / shift scheduling | 02, 08 |
| Thermal management | 09 |
| Data quality and DoE | 10 |
| CDM / configuration management | 11, 15 |
| Packaging calibration effects | 12 |
| NVH and torque ramp | 13 |
| Multi-fuel | 18 |
| Functional safety / DFMEA | 19 |
| Python / data automation | 16 |
| Field expedient / limp-home | 20 |

---

## Document Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-04-24 | Powertrain Calibration Lead | Initial release — 20 STAR scenarios |

---

*All scenarios are based on representative defence powertrain calibration experience. Vehicle specifications, ECU addresses, calibration values, and personnel details are generalised for learning purposes. Scenario outcomes reflect real calibration engineering decisions and their consequences.*
