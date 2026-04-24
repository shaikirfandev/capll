# Powertrain Calibration Engineer — Defence All-Terrain Vehicles
## Comprehensive Learning and Reference Guide

**Document Type:** Engineering Learning Reference  
**Domain:** Powertrain Calibration — Defence Ground Vehicles  
**Standards References:** MIL-STD-810H, MIL-STD-461G, ISO 26262, AUTOSAR, EURO VI / Tier 4 emissions  
**Target Reader:** Graduate to Senior Calibration Engineer  
**Tools Covered:** ETAS INCA, MDA, CDM Studio, Vector vCDM, CANape, MATLAB/Simulink, Python

---

## Table of Contents

1. [Role Overview and Context](#1-role-overview-and-context)
2. [Powertrain Architecture for Defence Vehicles](#2-powertrain-architecture-for-defence-vehicles)
3. [Engine Calibration Fundamentals](#3-engine-calibration-fundamentals)
4. [Transmission Calibration](#4-transmission-calibration)
5. [Multi-Mode Calibration Strategies](#5-multi-mode-calibration-strategies)
6. [Thermal Management and Packaging Calibration](#6-thermal-management-and-packaging-calibration)
7. [NVH and Vibration Considerations in Calibration](#7-nvh-and-vibration-considerations-in-calibration)
8. [Design of Experiments (DoE) for Powertrain Calibration](#8-design-of-experiments-doe-for-powertrain-calibration)
9. [Model-Based Calibration Workflow](#9-model-based-calibration-workflow)
10. [Environmental Extremes Calibration Campaigns](#10-environmental-extremes-calibration-campaigns)
11. [Emissions Calibration and Military Exemptions](#11-emissions-calibration-and-military-exemptions)
12. [Calibration Data Management](#12-calibration-data-management)
13. [HIL / SIL / Dyno Calibration Methods](#13-hil--sil--dyno-calibration-methods)
14. [Python and MATLAB Automation](#14-python-and-matlab-automation)
15. [Functional Safety and DFMEA for Calibration](#15-functional-safety-and-dfmea-for-calibration)
16. [Calibration Release Management](#16-calibration-release-management)
17. [Key Performance Metrics and Sign-Off Criteria](#17-key-performance-metrics-and-sign-off-criteria)
18. [Glossary](#18-glossary)

---

## 1. Role Overview and Context

### 1.1 What a Powertrain Calibration Engineer Does

A Powertrain Calibration Engineer translates hardware capability into real-world behaviour by populating, tuning, and validating the lookup tables, control parameters, and strategy switches that reside inside the Engine Control Module (ECM) and Transmission Control Module (TCM). Every torque request, every gear shift, every cooling fan activation, and every emission control event is governed by a calibration value.

In a defence vehicle context, this work extends far beyond a commercial truck or passenger car:

- The vehicle must operate from **–32 °C** Arctic conditions to **+55 °C** desert ambient
- It must ford water up to **1.5 metres** deep without hydrostatic lock or ECU flooding
- It must climb **60% gradients** at full combat load without clutch slip or thermal runaway
- It must operate in **stealth / silent mode** with strict acoustic and thermal emission constraints
- It must survive the vibration, shock, and EMI environments defined by **MIL-STD-810H** and **MIL-STD-461G**

The calibration engineer is the final authority on whether the powertrain delivers these capabilities. A poorly calibrated engine can strand a vehicle in a river crossing. A mistimed shift can shed a track on a steep descent. The stakes are operationally critical.

### 1.2 The Calibration Engineer in the Vehicle Development Lifecycle

```
Programme Phase        Calibration Activities
─────────────────────────────────────────────────────────────────────
Concept (SOP-36m)     Define calibration strategy, identify DoE matrix,
                       resource hardware requirements (dyno, HIL rigs)

Base Vehicle (SOP-24m) Base engine maps, transmission preliminary calibration,
                        SIL/HIL bring-up, dyno base runs

Integration (SOP-12m)  Vehicle-level integration, extreme terrain validation
                        begins, thermal and NVH assessment

Validation (SOP-6m)    Environmental chamber campaigns (cold/hot/altitude),
                        final emissions run, gradeability confirmation

Homologation / SOQ     Calibration dataset freeze, release notes, sign-off
                        evidence package, CDM archive
```

### 1.3 Key Interfaces

| Stakeholder | Interface Topic |
|---|---|
| Controls Engineers | Strategy logic, diagnostic thresholds, torque model |
| Powertrain Integrators | Sub-system boundary conditions, can-AM routing |
| Test Engineers | Test procedure definition, data review, sign-off |
| Emissions Team | Emissions targets, EGR/SCR/DPF calibration ownership |
| Thermal Engineers | Cooling map inputs, thermal protection limits |
| NVH Engineers | Combustion noise acceptance thresholds |
| Systems Engineers | Requirements traceability, DFMEA calibration items |
| Customer (MoD / OEM) | Acceptance criteria, operational envelope definition |

---

## 2. Powertrain Architecture for Defence Vehicles

### 2.1 Typical Defence Powertrain Layout

```
                    ┌──────────────────────────────────────────────┐
                    │            POWERTRAIN OVERVIEW               │
                    │                                              │
     Fuel System ──►│  Diesel / Hybrid Engine  ──┐               │
     Air System  ──►│  (Multi-cylinder, turbo)   │               │
     EGR System  ──►│                            ▼               │
                    │   ECM ◄──────────────► Torque coupler       │
                    │   (Engine Control)     (torque converter /  │
                    │                         wet clutch pack)     │
                    │                            │               │
                    │   TCM ◄───────────────►  Gearbox           │
                    │   (Transmission Ctrl)   (Automatic 6+1R /  │
                    │                           Hydrostatic range) │
                    │                            │               │
                    │                    Transfer case            │
                    │                  (2wd / 4wd / lock)        │
                    │                            │               │
                    │                    Front/ Rear Axle         │
                    │                  (diff lock, axle ratio)   │
                    └──────────────────────────────────────────────┘
```

### 2.2 Engine Types in Defence Vehicles

| Engine Type | Example | Calibration Challenges |
|---|---|---|
| Turbocharged Diesel (V6/V8) | Detroit 6.7L, MTU 8V199 | EGR, DPF regen under combat cycle, altitude boost |
| Multi-fuel capable | NATO multi-fuel engine | Varying cetane/octane, calorific value adaptation |
| Hybrid (diesel-electric) | BAE HybriDrive | EV mode transitions, ICE-on thresholds, battery SoC management |
| Gas turbine (legacy) | T55-GA-714A (helicopter crossover) | Very different thermal response, no cylinder-based ignition |

### 2.3 Transmission Types

| Type | Characteristics | Calibration Focus |
|---|---|---|
| Allison 3000/4000 series | 6-speed automatic with TC | Shift scheduling, TC lock-up map, adaptive learning |
| Renk HSWL 106 | Hydrostatic-mechanical | Steering radius control, drive range calibration |
| ZF 7HP / 8HP | 7/8-speed wet clutch | Pressure ramp calibration, shift quality NVH |
| Transfer case (high-low) | BorgWarner, Tremec | Range Select calibration, mode change logic |

### 2.4 Sensor and Actuator Inventory for Calibration

Understanding what the ECM sees and commands is fundamental to calibration.

**Key sensors:**
- MAP (manifold absolute pressure) — boost control feedback
- MAF (mass air flow) — air-fuel ratio base calculation
- ECT (engine coolant temperature) — warm-up enrichment, cooling fan activation
- IAT (intake air temperature) — charge density correction, derating
- EGT (exhaust gas temperature) — DPF regen triggering, turbine protection
- Crank/cam position — injection timing, misfire detection
- Oxygen (lambda) sensor — closed-loop AFR control
- Fuel rail pressure — common rail pressure closed-loop

**Key actuators:**
- Fuel injectors (pilot, main, post injection events)
- VGT (Variable Geometry Turbocharger) vane position
- EGR valve position
- Throttle (air mass control for idle, deceleration)
- Wastegate (boost limiting)
- Cooling fan (speed-controlled or on/off)
- DPF regeneration burner or post-injection

---

## 3. Engine Calibration Fundamentals

### 3.1 Torque Structure and Air-Fuel Ratio

The ECM controls engine torque through a **torque-based control structure**:

```
Driver demand (accelerator pedal position)
        │
        ▼
  Desired torque (Nm) ◄── mode limits (stealth, crawl, max power)
        │
        ▼
  Air path model: MAF / MAP → estimated volumetric efficiency
        │
        ▼
  Fuelling: injected mass (mg/stroke) = Torque_desired / (BMEP_factor × η_combustion)
        │
Injection events per cycle:
  ├── Pilot injection  : reduces combustion noise (NVH calibration)
  ├── Pre-injection    : reduces HC emissions at cold start
  ├── Main injection   : primary torque generation
  └── Post injection   : DPF regeneration oxidation
```

**Key calibration maps in the torque structure:**

| Map Name | Axes | Purpose |
|---|---|---|
| `TrqLim_Max_Map` | Engine speed × coolant temp | Maximum torque limit |
| `TrqLim_Derating_Alt` | Altitude (hPa) | Derating at high altitude |
| `TrqLim_Derating_IAT` | Intake air temp | Thermal protection |
| `Fuel_Main_Map` | Engine speed × desired torque | Main injection quantity (mg/stroke) |
| `Fuel_Pilot_Map` | Engine speed × coolant temp | Pilot injection quantity |
| `InjTiming_Main_Map` | Engine speed × torque | Main injection timing (°CA BTDC) |
| `InjTiming_Pilot_Map` | Engine speed × coolant temp | Pilot timing offset |
| `Lambda_Target_Map` | Engine speed × load | Target air–fuel ratio (λ) |
| `EGR_Rate_Map` | Engine speed × load | EGR mass flow rate % |
| `VGT_Position_Map` | Engine speed × load | VGT vane opening % |
| `Boost_Pressure_Target` | Engine speed × desired torque | Turbocharger boost setpoint |

### 3.2 Injection Timing Calibration

Injection timing is the most sensitive calibration parameter for balancing:
- **Torque output** (advance → more torque, but more NOx, peak cylinder pressure)
- **Emissions** (retard → less NOx, but more fuel consumption, smoke)
- **Combustion noise** (pilot injection offset reduces pressure rise rate = dP/dθ)
- **Piston/bearing durability** (peak cylinder pressure Pmax must not exceed design limit)

```
Calibration process for InjTiming_Main_Map:

Step 1: DoE sweep — vary injection timing from -20° to +2° BTDC at each
        (speed, load) operating point on dyno. Record:
        - Torque (Nm), BSFC (g/kWh), Pmax (bar), NOx (g/kWh), Smoke (FSN)

Step 2: Build response surface models for each response variable

Step 3: Apply multi-objective optimisation:
        Minimise BSFC + NOx while keeping Pmax < Pmax_limit and
        Smoke < FSN_limit

Step 4: Extract optimal timing angle per (speed, load) cell

Step 5: Apply smoothing filter to prevent step changes between cells
        (ensures smooth drivability)
```

### 3.3 Air–Fuel Ratio Calibration

For diesel engines, the target is excess air (λ > 1) to avoid smoke. For cold start and transient events, the control is more nuanced:

| Operating Condition | λ Target | Reason |
|---|---|---|
| Warm idle | 2.5 – 4.0 | Clean combustion, low smoke |
| Part load cruise | 1.8 – 2.5 | Fuel efficiency |
| Full load peak torque | 1.15 – 1.30 | Maximum air utilisation |
| Cold start (< 5 °C) | Enrichment mode | Combustion stability, HC reduction |
| Water fording | Enrichment mode | Prevent stall if air intake restricted |
| DPF regen (post-injection) | Rich spike | HC load for oxidation catalyst |

### 3.4 Cold Start Calibration

Cold start calibration in defence vehicles must function at **–32 °C** — a condition that severely affects:
- Fuel viscosity and atomisation (poor spray breakup below –20°C)
- Battery cranking capability (reduced CCA at low temperature)
- Glow plug pre-heat duration
- Initial injection quantity (more fuel needed for first combustion)
- Idle speed target during warm-up

**Cold start calibration map suite:**

```
Maps adjusted for cold start:
  ColdStart_GlowPlug_Duration_Map   [ECT → glow plug on-time (s)]
  ColdStart_InjQty_Correction       [ECT → additional fuel mass (mg/stroke)]
  ColdStart_IdleSpeed_Target        [ECT → idle speed setpoint (rpm)]
  ColdStart_ExhaustTemp_Target      [ECT → fast idle duration until exhaust warm]
  ColdStart_Pilot_Qty               [ECT → increased pilot injection for NVH]
  ColdStart_Lambda_Override         [ECT × time → lambda relaxation map]
```

**–32 °C validation criteria:**
- Engine starts within 15 seconds of cranking
- Idle speed stabilises within 30 seconds
- No misfire DTC within the first 60 seconds
- Acceptable white smoke (unburned HC) within 90 seconds
- Full torque available within 3 minutes (after warm-up hold)

### 3.5 Transient Response Calibration

Defence vehicles demand rapid torque delivery for obstacle clearance, sudden acceleration on inclines, and emergency manoeuvres.

The key challenge for a turbocharged diesel is **turbo lag** — the delay between fuel demand increase and boosted air delivery. This causes:
1. Rich combustion spike → black smoke
2. Torque tracking error → vehicle hesitates

**Anti-smoke / torque management strategy:**

```
When: driver demand increases rapidly (dPedalPos/dt > threshold)

Without calibration:
  Fuel injected immediately → λ drops below 1.0 → black smoke

With correct calibration:
  1. FuelRateLimit_Map: restrict injection rate increase until
     estimated boost pressure has risen sufficiently
     (uses predictive VGT pre-positioning)

  2. TransientBoost: advance VGT vane toward closed position
     to accelerate turbo spool-up

  3. SmokeLimiter: lambda-based clamp on injection quantity
     ensures λ never drops below λ_min (typically 1.05)

Result: torque follows demand without visible smoke
        typical lag compensation: 150–300ms for full load step
```

---

## 4. Transmission Calibration

### 4.1 Shift Scheduling

The gear shift schedule determines **when** the transmission changes gear, governed by:
- Vehicle speed
- Accelerator pedal position (driver demand)
- Road gradient (estimated from longitudinal acceleration and torque balance)
- Drive mode (road, off-road, crawl, tow)
- Transmission fluid temperature

**Shift schedule map structure:**

```
Upshift line:    Vehicle_Speed_Upshift[Gear][PedalPos] = threshold speed (km/h)
Downshift line:  Vehicle_Speed_Downshift[Gear][PedalPos] = threshold speed (km/h)

Hysteresis band: Upshift_speed - Downshift_speed > Hysteresis_min
  (prevents hunting between gears)

Calibration objective:
  1. Match shift points to engine optimal efficiency corridor (BSFC island)
  2. Avoid shift in the middle of a corner or gradient (gradient hold logic)
  3. Ensure downshift is available early enough for engine braking on descent
  4. Stealth mode: delay shifts to avoid acoustic signature during deceleration
```

### 4.2 Torque Converter Lock-Up Calibration

The torque converter (TC) operates in two states:
- **Slip mode:** impeller and turbine have speed difference — efficient for vehicle launch, isolates torsional vibration
- **Lock-up mode:** clutch engages — eliminates slip losses, improves fuel economy

**Lock-up calibration maps:**

| Map | Axes | Calibration Goal |
|---|---|---|
| `TC_Lockup_Enable_Speed` | Gear × pedal position | Minimum speed for lock-up engagement |
| `TC_Lockup_Slip_Target` | Engine speed × torque | Controlled micro-slip for NVH isolation |
| `TC_Lockup_Disengage` | Deceleration rate | Disengage before stall or harsh manoeuvre |
| `TC_Lockup_Temp_Limit` | Trans fluid temperature | Unlock if fluid overheating |

**Off-road consideration:** TC lock-up must be **disabled** during rock crawl and water fording — locked TC during low-speed torque reversals causes driveline shock and potential damage.

### 4.3 Clutch Pressure Calibration (Wet Clutch Transmissions)

For ZF or Allison units with wet clutch packs, clutch pressure ramp calibration determines shift quality:

```
Clutch engagement sequence:
  1. Pre-fill phase:  fill clutch oil volume rapidly (calibrate: fill_time, fill_pressure)
  2. Torque phase:    ramp pressure to transfer torque from old clutch to new
  3. Overlap phase:   brief period where both clutches partially engaged (calibrate ramp rate)
  4. End-phase:       snap to full pressure (calibrate end pressure)

Shift quality metric:
  - Jerk (da/dt) must be < 3 m/s³ for comfort (road mode)
  - For off-road mode: allow harder shifts (jerk < 8 m/s³) for speed
  - Shift duration: target 200–400ms for highway shift, 100–200ms for sport mode
```

### 4.4 Gradient Detection and Hill-Hold Calibration

Defence vehicles operate on gradients up to 60%. The TCM must:
- Detect gradient from longitudinal acceleration (corrected for pitch from IMU)
- Hold the current gear (inhibit upshift) when above gradient threshold
- Enable hill-start assist (HSA) which holds brake pressure during driver transition from brake to accelerator

```
Gradient detection calibration:
  GradEst = (a_longitudinal - a_wheel_accel) / g
  GradientHold_Threshold_Map[vehicle_speed][gradient] → gear_hold_flag
  DownhillShift_Threshold_Map[gradient] → forced_downshift_command
```

### 4.5 Transfer Case and Axle Lock Calibration

Defence vehicles have multiple drive modes managed by the TCM or a dedicated transfer case control module:

| Mode | Driveline Config | Calibration Action |
|---|---|---|
| 2H (2WD High) | Rear axle only | Standard shift map |
| 4H (4WD High) | All axles, centre diff free | Modify shift schedule (higher gear hold speed) |
| 4L (4WD Low) | All axles, low range | Full torque at very low speed, crawl ratio active |
| 4L + Axle Lock | All axles, all diffs locked | Maximum torque, minimum traction loss — no speed limit |
| Water Fording | 4L + fan shutdown + sealing | Max torque headroom, cool-down after exit |

---

## 5. Multi-Mode Calibration Strategies

### 5.1 Mode Architecture

Defence vehicles require calibration datasets that switch between operational modes. This is implemented as a **Mode Signal** passed from the vehicle Mission Computer (or driver switch) to the ECM/TCM:

```
Mode Signal (5-bit):
  0x01  ROAD_NORMAL
  0x02  ROAD_SPORT
  0x03  OFFROAD_SAND
  0x04  OFFROAD_MUD
  0x05  OFFROAD_ROCK_CRAWL
  0x06  WATER_FORDING
  0x07  STEALTH_SILENT
  0x08  RECOVERY_MODE
  0x09  HIGH_MOBILITY (max speed)
  0x0A  COLD_WEATHER
  0x0B  HOT_AMBIENT
  0x0C  HIGH_ALTITUDE
  0x0D  TOWING_HEAVY
  0x0E  EMERGENCY_LIMP_HOME
```

### 5.2 Road Normal Mode

**Objective:** Balanced performance, fuel economy, low emissions  
**Calibration characteristics:**
- Full shift schedule active — aggressive upshifts for fuel economy
- TC lock-up engaged from 2nd gear above 25 km/h
- EGR fully active — all emission maps operative
- Cooling fan: duty-cycle speed control (variable speed)
- Driver pedal map: linear 1:1 torque request

### 5.3 Off-Road Sand Mode

**Objective:** Maximum traction on loose sand — prevent bogging  
**Calibration changes from Road Normal:**
- Throttle pedal map: **reduced initial response** (prevents wheel spin on soft surface)
- Upshift points: **raised** (keep engine in higher torque band in lower gears)
- TC lock-up: **disabled below 40 km/h** (slip needed for traction modulation)
- Traction control: more aggressive intervention threshold
- Fan speed: **increased proactively** (sand intake thermal risk)
- Injection timing: slight advance for responsiveness at low load

### 5.4 Off-Road Mud Mode

**Objective:** Maximum low-speed torque, clean recovery from stuck  
**Calibration changes:**
- Pedal map: **step-response** torque curve (immediate torque at first pedal touch)
- Gear hold: **inhibit 5th and 6th gear** — maximum available gear = 4th
- TC lock-up: fully disabled in crawl speed range
- EGR: **partially reduced** — combustion stability with intermittent load spikes
- Engine idle: raised to **950 rpm** (ready for sudden torque demands)
- Torque limit: unlocked to **maximum available** (sacrifice durability forecast for mission)

### 5.5 Water Fording Mode

**Objective:** Maintain powertrain operation during 1.5m water immersion for up to 30 minutes  

This is one of the most safety-critical calibration modes. Failure = vehicle stranded in water = crew risk.

```
Water Fording calibration checklist:

Pre-immersion (triggered when fording mode selected):
  ✓ Engine speed: raise minimum idle to 900 rpm (prevents stall if water enters)
  ✓ Engine fan: DISABLE or set to low duty (fan blades must not cavitate in water)
  ✓ Alternator: increase charge voltage (compensate for bilge pump load)
  ✓ Exhaust backpressure: monitor — water ingress raises backpressure
  ✓ Throttle pedal: slight pre-enrichment (water in intake = air restriction)
  ✓ Diagnostic masks: disable false air-filter restriction DTCs

During immersion:
  ✓ Continuous coolant temp monitoring — engine cannot overheat (no cooling fan)
  ✓ If ECT > 105°C: override mode and increase fan speed emergency
  ✓ EGR valve: CLOSE (prevent water ingress via EGR circuit)
  ✓ EVAP system: purge valve closed (water in vapour canister)
  ✓ Transmission: inhibit gear changes above 2nd gear
  ✓ Axle breathers: ECM monitors pressure sensor if fitted

Post-immersion (exit fording mode):
  ✓ Fan speed: ramp to maximum for 3 minutes (rapid cool-down)
  ✓ Post-fording DTC check: auto-clear known false DTCs
  ✓ Brake drying cycles: automatic application sequence
  ✓ Return to 4H or selected mode
```

### 5.6 Stealth / Silent Mode

**Objective:** Minimise vehicle acoustic and thermal signature below defined thresholds  
Acoustic: < 72 dB(A) at 10m  
Thermal: exhaust outlet temperature below threshold (IR signature reduction)

```
Stealth mode calibration changes:

Engine:
  - Reduce idle speed to minimum stable (typically 550–600 rpm)
  - Disable combustion noise optimisation (allow more retarded timing)
  - Engine fan: pulse-width modulated low duty cycle
  - Restrict max torque to 60% of rated (less engine noise at high load)
  - EGR: maximise (reduces combustion temperature and noise)
  - Post-injection events: DISABLED (no exhaust burner noise)

Transmission:
  - Shift points: higher speed thresholds (stay in higher gear longer at low speed)
  - Gear changes: softer ramp rates (reduce mechanical clunk)
  - TC lock-up: always locked above 15 km/h (eliminates slip noise)
  - Differential locks: engage earlier (prevent tyre scrub noise from slip)

Ancillaries:
  - Air-conditioning: DISABLED
  - Auxiliary power: battery-only if available (electric ancillary mode)
  - Exhaust brake: DISABLED (flap operation creates noise)
```

### 5.7 High-Mobility Mode

**Objective:** Maximum speed, maximum acceleration for close support or pursuit  
- All torque limiters relaxed to maximum hardware limits
- Pedal map: step function — no ramp delay
- Shift schedule: maximum performance mode (holds gears longer through corners)
- TC lock-up: continuous lock in all gears ≥ 2
- EGR: disabled at full load (airflow priority)
- Cooling: maximum continuous fan duty
- Durability monitoring: active life-consumption counter (informs maintenance)

---

## 6. Thermal Management and Packaging Calibration

### 6.1 Why Packaging Affects Calibration

In a defence vehicle, the powertrain is compressed into a hull with strict armour, crew space, and ammunition storage requirements. The resulting packaging creates:

- **Thermal hotspots:** exhaust manifold within 50mm of wiring harness
- **Restricted cooling airflow:** limited hood opening area forces CAC (charge air cooler) limitation
- **Vibration transmission:** engine mounts tuned for isolation can introduce resonance in sensor harnesses
- **Sensor accuracy degradation:** MAP sensors mounted near vibrating structures show 2–5% reading error
- **Restricted actuator response:** EGR valve with a long pipe run has a 200ms additional delay vs bench spec

### 6.2 Thermal Protection Calibration

```
Under-hood thermal management maps:

Fan_Speed_Map[ECT][IAT] → fan duty cycle %
  - Hysteresis: fan switches ON at 95°C, switches OFF at 88°C
  - IAT correction: if IAT > 45°C, add +5% duty at all ECT cells
  - Emergency: if ECT > 108°C, force fan to 100%

Derating_Thermal_Map[IAT][ECT] → torque derating %
  - Below threshold: 0% derating (full torque available)
  - IAT > 50°C: 5% derating per 5°C step
  - IAT > 70°C: engine protection shutdown warning
  - ECT > 110°C: 15% derating + operator warning DTC

Cooler_Efficiency_Correction:
  - In packaging-constrained vehicles, measure actual coolant delta-T across radiator
  - If measured efficiency < spec: tighten ECT fan actuation by –5°C to compensate
  - Document as a packaging calibration note in the A2L calibration record
```

### 6.3 Exhaust Gas Temperature Management

EGT at turbine inlet must not exceed material limits:

| Component | Max continuous EGT | Max transient EGT |
|---|---|---|
| Turbocharger turbine | 750 °C | 820 °C (30s) |
| DPF substrate | 680 °C nominal | 900 °C (regen) |
| DOC inlet | 580 °C | 720 °C |

**EGT protection calibration:**
```
EGT_Protection_Map[Engine_Speed][Load] → active_protection_action
  Protection actions (in order of escalation):
  1. Retard injection timing 2° (reduces EGT by ~15°C per 2°)
  2. Increase fuel post-injection (provides cooling via HC oxidation)
  3. Open EGR valve (reduces combustion temperature)
  4. Limit fuelling (derating)
  5. Engine torque cap + DTC (P0546 - EGT sensor high)
```

### 6.4 Charge Air Cooler Limitation

In some defence packaging, the charge air cooler (CAC) cannot reject enough heat under sustained high-load conditions. This shows up as:

- IAT rising progressively under sustained high load
- Knock tendency (for spark-ignition multi-fuel variants)
- ECM derating triggering prematurely

**Calibration response:**
- Set `CAC_Efficiency_Derating_Map` to reduce boost target by 2–5% when IAT > 40°C
- This reduces turbo work, reducing heat input to CAC
- Trade-off: slight torque reduction — document as packaging performance deviation
- Co-ordinate with thermal engineer to update the thermal model

---

## 7. NVH and Vibration Considerations in Calibration

### 7.1 Combustion Noise and the Pilot Injection Role

Diesel combustion noise is characterised by the **rate of pressure rise (dP/dθ in bar/°CA)**. A steep rise causes the characteristic "clatter" sound. The pilot injection pre-conditions the charge before the main injection, creating a pilot combustion event that warms the cylinder and reduces the main injection ignition delay.

**Pilot injection calibration targets:**
- dP/dθ target: ≤ 8 bar/°CA at idle, ≤ 12 bar/°CA at full load
- Pilot quantity: typically 0.5–2.0 mg/stroke (larger = more pre-heating, slower pressure rise)
- Pilot timing: 10–20 °CA before main injection
- Cold start: increase pilot quantity by 50% until ECT > 40°C

### 7.2 Structural Resonance and Sensor Errors

When the engine fires at a frequency that coincides with a structural resonance of the vehicle chassis or a sensor bracket, the sensor output can show noise spikes:

```
Example: MAP sensor mounted on intake manifold bracket

Engine firing frequency at idle (4-cylinder, 750 rpm):
  f_firing = (N × n) / (2 × 60) = (4 × 750) / 120 = 25 Hz

If the bracket resonance is at 22–28 Hz:
  MAP signal shows ±5 kPa oscillation at idle
  ECM interprets as load oscillation → unstable idle fuelling

Calibration response:
  Option A: Add MAP signal filtering (increase LP filter time constant from 5ms to 20ms)
            Risk: slower transient response for boost control
  Option B: Adjust idle speed to 680 rpm to shift firing frequency to 22.7 Hz
            (below bracket resonance)
  Option C: Hardware fix: change bracket natural frequency (with NVH engineer)
```

### 7.3 Driveline Torsional Vibration

Transfer of torque reversal through a driveline with compliance elements (universal joints, rubber couplings) can excite torsional modes — felt as a "shunt" or "clonk" during tip-in / tip-out.

**Calibration mitigations:**
- `TorqueRequest_RampRate_TipIn` — limit rate of torque increase during sharp pedal application
- `TorqueRequest_RampRate_TipOut` — limit rate of torque removal during pedal release
- `DriveshaftTorque_Oscillation_Filter` — ECM inertia compensation torque superimposed to damp oscillation

---

## 8. Design of Experiments (DoE) for Powertrain Calibration

### 8.1 Why DoE Instead of One-Factor-at-a-Time (OFAT)

In a traditional OFAT calibration, the engineer sweeps one parameter while holding all others constant. This misses interaction effects — the combination of injection timing and EGR rate influences NOx in a non-linear way that no single sweep reveals.

DoE uses a **statistical design matrix** to explore the parameter space efficiently:

```
Example: NOx and BSFC response to injection timing and EGR rate

OFAT approach:
  - Sweep timing: 72 test points (at constant EGR)
  - Sweep EGR:    72 test points (at constant timing)
  - Total:        144 points, no interaction data

DoE approach (face-centred Central Composite Design):
  - 2 factors × 5 levels = 13 unique design points
  - Captures main effects AND interactions
  - Fits quadratic response surface model
  - Total: 13 points + 3 centre-point repeats = 16 tests
  - 89% reduction in test time
```

### 8.2 Common DoE Designs for Engine Calibration

| Design Type | Use Case | Number of Points |
|---|---|---|
| Full Factorial | 2–3 factors, small range | 2^k or 3^k (can be large) |
| Fractional Factorial | Screening: identify which factors matter | 2^(k-p) |
| Central Composite Design (CCD) | Response surface modelling, 2–6 factors | 2^k + 2k + centre pts |
| D-optimal | Irregular operating region, constrained | Optimised per region shape |
| Latin Hypercube Sampling (LHS) | Computer simulation (SIL/HIL) | User-defined N |
| Space-filling DoE | Full engine map exploration | Poisson disc / LHS |

### 8.3 DoE Test Matrix Example — EGR and Boost Optimisation

```
Factor definitions:
  x1 = EGR_Rate           range: [0%, 30%]
  x2 = VGT_Position       range: [20%, 80% closed]
  x3 = InjTiming_Main     range: [-18°, -2° BTDC]

Responses measured:
  y1 = NOx (g/kWh)
  y2 = BSFC (g/kWh)
  y3 = Pmax (bar)
  y4 = EGT (°C)
  y5 = Smoke (FSN)

Design: Face-centred CCD for 3 factors
  Design matrix (17 runs + 3 centre replicates = 20 total):

  Run   EGR%   VGT%   Timing°  | NOx    BSFC    Pmax
  ────────────────────────────────────────────────────
   1    0      20     -18       |  4.2   220     145
   2    30     20     -18       |  1.8   235     132
   3    0      80     -18       |  3.9   228     138
   4    30     80     -18       |  2.1   240     126
   5    0      20      -2       |  5.1   212     162
   6    30     20      -2       |  2.5   225     148
   7    0      80      -2       |  4.8   218     155
   8    30     80      -2       |  2.2   232     140
   [star points and centre replicates...]

Model fitted (for NOx example):
  NOx = β0 + β1·EGR + β2·VGT + β3·Timing
        + β12·EGR·VGT + β13·EGR·Timing + β23·VGT·Timing
        + β11·EGR² + β22·VGT² + β33·Timing²

  R² = 0.97 (97% variance explained by model)
  Best operating point found at EGR=28%, VGT=65%, Timing=-8° BTDC:
  NOx = 2.1 g/kWh (–47% vs baseline), BSFC = 228 g/kWh (+3.6%)
```

### 8.4 Statistical Confidence Requirements

All response surface models used for calibration decisions must meet minimum quality gates:

| Quality Gate | Minimum Requirement | Tool |
|---|---|---|
| Coefficient of determination R² | ≥ 0.95 | MATLAB, ETAS ASCMO, MBC Toolbox |
| Root Mean Square Error (RMSE) | < 5% of response range | Same |
| Lack-of-fit test | p-value > 0.05 (no significant lack of fit) | ANOVA |
| Prediction accuracy on validation set | ≤ 7% error on holdout points | Cross-validation |
| Outlier check | Cook's distance < 1 for all design points | Regression diagnostics |

---

## 9. Model-Based Calibration Workflow

### 9.1 End-to-End MBC Process

```
Stage 1: Design Space Definition
  └─ Define speed/load operating points from customer duty cycle
  └─ Define factor ranges and constraints (hardware limits, emissions)
  └─ Design DoE matrix (CCD/D-optimal/LHS)

Stage 2: Data Collection
  └─ Execute DoE on engine dyno (automated sweep via INCA/ATI Vision)
  └─ Data quality checks: outlier flagging, repeatability assessment
  └─ Output: structured measurement dataset (.mdf file)

Stage 3: Model Fitting (MATLAB MBC Toolbox or ETAS ASCMO)
  └─ Import DoE data
  └─ Select model type: polynomial, RBF, Gaussian Process
  └─ Assess model quality: R², RMSE, LOF test
  └─ Iterate design if quality insufficient

Stage 4: Optimisation
  └─ Define objective function: minimise(BSFC) subject to NOx < limit,
       Pmax < limit, EGT < limit, Smoke < FSN_limit
  └─ Multi-objective Pareto front generation
  └─ Select optimal operating point from Pareto front per customer priority

Stage 5: Calibration Table Generation
  └─ Extract optimal values per (speed, load) operating point
  └─ Apply table smoothing (ensure no step changes)
  └─ Generate A2L-compatible calibration files (.hex or .cdf)
  └─ Import into INCA / CDM Studio for ECM download

Stage 6: Validation
  └─ Drive cycle validation on dyno and/or vehicle
  └─ Confirm model predictions match real-world measurements
  └─ Document evidence: R² values, model diagnostics, validation plots
```

### 9.2 ETAS INCA Calibration Workflow

INCA (Integrated Calibration and Acquisition) is the primary tool for live ECM calibration and measurement:

```
INCA workflow:
1. Create project → select device (ECM hardware)
2. Import A2L file (describes all calibration parameters and addresses)
3. Connect to ECM via XCP or CCP over CAN/ETH
4. Open Working Page of calibration data (leaves Reference Page intact = safe fallback)
5. Select maps to edit: navigate Map Browser → double-click table
6. Edit individual cells or apply offset/scaling to selected region
7. Measure response in real time using measurement variables on time channel
8. Save to Working Page → promote to Reference Page when validated
9. Export calibration to .hex (Intel HEX) or .cdf (Calibration Data Format)
10. Hand off .cdf file to CDM Studio / vCDM for version management
```

---

## 10. Environmental Extremes Calibration Campaigns

### 10.1 Cold Weather Campaign (–32 °C)

**Location:** Arctic test track (Arjeplog, Sweden) or MoD cold chamber  
**Objective:** Cold start, warm-up, and sustained operation at minimum temperature

**Pre-campaign preparation:**
- Freeze vehicle overnight to –32 °C (8-hour soak minimum for full thermal equilibrium)
- Battery pre-condition: some programmes use external battery heater to exclude battery from first test to isolate engine calibration
- Instrumentation: add thermocouples to intake manifold, injector body, fuel rail, gearbox oil

**Test procedures:**
```
Test 1: Raw Cold Start at –32 °C
  - Soak 8 hours minimum
  - Without pre-heat: crank and record:
    Crank_to_First_Combustion_time (target < 5s)
    Crank_to_Stable_Idle_time (target < 15s)
    Time_to_50%_Torque_Available (target < 3 min)
    HC/CO emissions during warm-up

Test 2: Cold Crawl Performance
  - Start engine, allow 60s warm-up
  - 10% gradient, 4L, 500kg extra load
  - Verify no stall, gradeability ≥ spec

Test 3: Transmission Cold Shift Quality
  - ATF (automatic transmission fluid) at –32 °C has very high viscosity
  - Verify shift point adaptation: TCM defers lock-up until ATF > 0 °C
  - Verify shift smoothness (no harsh shifts from high viscosity clutch fill)

Test 4: Cold Idle Stability
  - 30 minutes at idle in –32 °C ambient
  - No engine stall, idle speed within ±50 rpm of target
  - Battery charge maintained
```

**Common cold-weather calibration issues and fixes:**

| Issue | Root Cause | Calibration Fix |
|---|---|---|
| White smoke for > 5 min | Pilot injection quantity too small at cold ECT | Increase `ColdStart_Pilot_Qty` table by 0.5 mg/stroke below 10°C |
| Rough idle at –20 °C | Injection timing too retarded — poor ignition at cold | Advance `InjTiming_Main` by 2° for ECT < 0°C cells |
| Transmission harsh shift | Clutch fill time not extended for high-viscosity ATF | Increase `ClutchFill_Time_Low_Temp` correction by 50ms at –30°C |
| Battery drain during extended crank | Alternator not activated until engine running | Enable `Starter_Alternator_Enable` calibration flag for cold-start assistance |

### 10.2 High-Temperature Campaign (+55 °C Ambient)

**Location:** Middle East test site or MoD hot chamber  
**Objective:** Sustained performance under maximum thermal stress

**Test focus areas:**
- Under-hood temperatures: verify no wiring insulation damage (wire spec typically 125°C or 150°C)
- Coolant temperature: validate cooling fan calibration maintains ECT < 100°C during full-load gradeability
- Inter-cooler outlet temperature: must stay below IAT_limit (typically 65°C) under sustained boost
- Fuel temperature: diesel fuel above 70°C causes vapour lock — verify fuel return cooling

**Thermal derating validation:**
```
Test procedure:
1. Soak vehicle at +55°C for 4 hours (full thermal equilibrium)
2. Select High-Mobility mode
3. Full load acceleration to maximum speed
4. Log: ECT, IAT, EGT, Fan_Duty, Torque_Actual vs Torque_Request
5. Acceptance criterion:
   - Torque_Actual / Torque_Request > 92% (max 8% thermal derating allowed)
   - ECT must not exceed 105°C at any point
   - No coolant overheating DTC during 30-minute sustained high-load cycle
```

### 10.3 High-Altitude Campaign (4,500 m ASL)

**Location:** Bolivian Andes, Ethiopian Highlands, or altitude chamber  
**Objective:** Verify performance and power delivery at reduced atmospheric pressure

At 4,500m ASL, atmospheric pressure is approximately **57 kPa** (vs 101.3 kPa sea level). This means:
- Air density reduced by 43%
- Turbocharger must work harder to achieve same boost ratio
- Maximum achievable boost is compressor map limited
- Engine torque will derate unless calibration accounts for ambient pressure

**Altitude calibration maps:**

```
TrqLim_Derating_Alt_Map[BPsens_kPa] → torque_derating_%

  kPa    Derating
  101.3  0%        (sea level)
  90.0   3%
  80.0   7%
  70.0   12%
  57.0   25%       (4,500m)

  Note: derating is graceful — operator receives a dash warning
  but vehicle remains operable (mission-critical requirement)

VGT_Position_Alt_Correction[BPsens_kPa] → VGT_position_offset_%
  At altitude, advance VGT toward closed to increase boost ratio
  Limit: compressor surge boundary must not be crossed
  (use turbocharger compressor map to define surge limit)
```

---

## 11. Emissions Calibration and Military Exemptions

### 11.1 Civilian vs Military Emissions Context

Civilian vehicles must comply with legislated emission standards (Euro VI, EPA Tier 4 Final). Military vehicles in many jurisdictions have legal exemptions from these standards, but:

- **Export-controlled sales** may require compliance with destination country legislation
- **Multi-purpose platforms** (those used domestically in peacetime on public roads) must comply with civil standards
- **MoD sustainability policies** increasingly align with civilian standards as a programme requirement even where legally exempt

The calibration engineer must know which standard applies to each market variant of the vehicle.

### 11.2 Emissions Control System Overview for Diesel Powertrain

```
Intake side:
  EGR (Exhaust Gas Recirculation): reduces NOx by diluting charge with inert exhaust gas
  Throttle: used on diesels to create EGR delta-P at low load

Fuel side:
  Injection pressure: common rail 1,600–2,500 bar (affects soot formation)
  Pilot injection: reduces HC/CO at cold start
  Post injection: HC loading for catalyst regeneration

Aftertreatment:
  DOC (Diesel Oxidation Catalyst): oxidises CO and HC, produces NO₂ for DPF regen
  DPF (Diesel Particle Filter): traps soot, requires periodic regeneration
  SCR (Selective Catalytic Reduction): converts NOx using AdBlue (urea)
  ASC (Ammonia Slip Catalyst): prevents excess NH₃ from SCR
```

### 11.3 DPF Regeneration Calibration

Soot accumulation in the DPF is estimated by the ECM using a soot load model (grams of soot per litre of DPF volume). When soot load exceeds threshold, active regeneration is initiated:

```
DPF Regeneration calibration parameters:

  DPF_SootLoad_Regen_Threshold: 8 g/L (trigger active regen)
  DPF_SootLoad_Warning_Threshold: 10 g/L (operator dashboard warning)
  DPF_SootLoad_Forced_Regen: 12 g/L (vehicle limits speed to complete regen)

During active regen (raises DPF temp to 550–650°C to oxidise soot):
  PostInjection_Qty_Regen_Map[EGT][Engine_Speed] → post-injection quantity
  DOC_LightOff_Temp_Check: if DOC > 250°C → suppress post-injection (prevent uncontrolled exotherm)
  Regen_Duration_Map[SootLoad] → estimated regen time (minutes)

Defence-specific calibration requirement:
  Inhibit DPF regen during:
    - Water fording mode (exhaust temp management constraint)
    - Stealth mode (post-injection creates exhaust smoke/flame — IR signature)
    - Rock crawl (intermittent load profile cannot sustain regen temp)

  Post-inhibit strategy:
    - Store regen debt (time since last regen)
    - Force regen at next available opportunity (road mode at steady speed)
    - If regen debt > 2× normal interval: DTC + operator warning
```

---

## 12. Calibration Data Management

### 12.1 CDM Toolchain

Calibration datasets live in structured files linked to specific hardware and software versions. The toolchain is:

```
INCA (live calibration) → export .cdf / .hex
         │
         ▼
CDM Studio / Vector vCDM (version control, variant management)
         │
         ▼
Release package: .hex + .cdf + release notes + A2L reference
         │
         ▼
ECU flash (via ETAS, CANdela, or vehicle diagnostics)
```

### 12.2 A2L File and ASAP2 Standard

The A2L file (ASAP2 format) is the **data dictionary** that maps calibration parameter names to ECM memory addresses. Every calibration map has:
- Parameter name (e.g., `InjTiming_Main_Map`)
- Memory address in the ECM
- Data type (uint8, int16, float32)
- Physical conversion formula (factor, offset)
- Axis references (X-axis = engine speed, Y-axis = load)
- Min/max limits
- Function group

**A2L discipline:** The A2L must exactly match the software binary. If the software is re-compiled without updating the A2L, the calibration tool writes to the wrong memory address — potentially writing a value into an unrelated variable. This is a critical safety-relevant configuration management item.

### 12.3 Variant Management

Defence vehicles typically have multiple hardware variants:
- Different engine displacements (6.7L vs 8.1L)
- Different transmission ratios (desert vs arctic final drive)
- Different emission aftertreatment (EU market vs exempt)
- Different altitude ratings (sea level vs high-altitude)

Each variant requires a distinct **calibration variant** (sometimes called a "dataset"):

```
vCDM variant structure:

  Vehicle_Programme_001
  ├── HW_Rev_A
  │   ├── SW_Baseline_010
  │   │   ├── CAL_Variant_EU_SeaLevel_Standard
  │   │   ├── CAL_Variant_EU_HighAlt_4500m
  │   │   ├── CAL_Variant_Exempt_Desert_55degC
  │   │   └── CAL_Variant_Exempt_Arctic_Neg32degC
  │   └── SW_Baseline_011
  │       └── [updated calibrations for SW baseline 011]
  └── HW_Rev_B
      └── [pending calibration for new hardware rev]
```

### 12.4 Change Management

Every calibration change must be:
1. **Motivated** — documented reason (test failure, DoE result, customer request)
2. **Reviewed** — peer review by second calibration engineer
3. **Impact-assessed** — what else could this change affect? (emissions, performance, durability)
4. **Tested** — minimum confirmation test before release
5. **Archived** — old dataset retained, change delta visible in CDM diff tool

---

## 13. HIL / SIL / Dyno Calibration Methods

### 13.1 Calibration Hierarchy

```
SIL (Software-in-the-Loop)
  • Fastest iteration: run simulation in < real time
  • No hardware needed: test calibration concepts before dyno booking
  • Use: strategy exploration, DoE pre-screening, MBC model validation
  • Tool: MATLAB/Simulink with GT-Power engine model

HIL (Hardware-in-the-Loop)
  • Real ECM + simulated engine/transmission/vehicle
  • Can inject fault codes, test boundary conditions safely
  • Use: validation of calibration strategy logic, NRC verification
  • Tool: dSPACE SCALEXIO + INCA + ControlDesk

Engine Dyno
  • Real engine + instrumented test cell
  • Highest fidelity for combustion calibration (injection timing, EGR)
  • Full DoE execution: automated sweep using ATI Vision / INCA ORION
  • Use: base engine maps, MBC data collection, emissions measurements

Powertrain (PT) Dyno
  • Engine + transmission + transfer case + axles on multi-axle dynamometer
  • Full drivetrain response calibration
  • Use: shift quality, TC lock-up, gradeability, transmission thermal

Full Vehicle
  • Final integration validation
  • Cannot isolate subsystems but gives holistic performance assessment
  • Use: ride quality, NVH in vehicle, thermal in vehicle environment
  • Use for: environmental chamber campaigns, terrain trials
```

### 13.2 Automated Dyno Sweep (INCA ORION)

The INCA ORION automation framework allows a pre-programmed calibration sweep without engineer intervention:

```python
# Conceptual INCA ORION sequence (Python API pseudocode)
# Real implementation uses INCA COM automation API

doe_matrix = load_doe_csv("EGR_VGT_Timing_CCD_17points.csv")

for i, run in enumerate(doe_matrix):
    # Set calibration values via XCP
    inca.set_calibration("EGR_Rate_Setpoint", run["EGR_pct"])
    inca.set_calibration("VGT_Position_Setpoint", run["VGT_pct"])
    inca.set_calibration("InjTiming_Offset", run["Timing_deg"])

    # Set dyno operating point
    dyno.set_speed_torque(run["Engine_speed_rpm"], run["Load_Nm"])
    wait_stable(seconds=30)   # wait for thermal stability

    # Record measurement
    sample = inca.measure_snapshot(
        variables=["NOx_gkwh", "BSFC_gkwh", "Pmax_bar", "EGT_C", "Smoke_FSN"],
        duration=10,
        average=True
    )
    doe_matrix.loc[i, "NOx"]  = sample["NOx_gkwh"]
    doe_matrix.loc[i, "BSFC"] = sample["BSFC_gkwh"]
    doe_matrix.loc[i, "Pmax"] = sample["Pmax_bar"]
    doe_matrix.loc[i, "EGT"]  = sample["EGT_C"]
    doe_matrix.loc[i, "Smoke"]= sample["Smoke_FSN"]

    print(f"Run {i+1}/{len(doe_matrix)} complete: NOx={sample['NOx_gkwh']:.2f}")

doe_matrix.to_csv("DoE_Results_Run_001.csv")
print("DoE sweep complete")
```

---

## 14. Python and MATLAB Automation

### 14.1 Python Post-Processing — Calibration Data Analysis

```python
"""
powertrain_cal_analyser.py
--------------------------
Automated post-processing for engine calibration data.
Reads MDF4 measurement files from INCA, extracts key channels,
computes performance metrics, and flags anomalies.

Dependencies: asammdf, pandas, scipy, matplotlib
Install:      pip install asammdf pandas scipy matplotlib
"""

import asammdf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Channel definitions (match your A2L / measurement setup) ──────
CHANNELS = {
    "engine_speed":     "Engine_Speed_rpm",
    "engine_torque":    "Engine_Torque_Nm",
    "fuel_rate":        "Fuel_Consumption_gkwh",
    "nox":              "NOx_Sensor_gkwh",
    "egt":              "EGT_Turbine_Inlet_C",
    "egr_rate":         "EGR_Rate_pct",
    "boost_pressure":   "MAP_kPa",
    "coolant_temp":     "ECT_C",
    "pedal_position":   "PedalPos_pct",
    "turbo_speed":      "Turbo_Speed_krpm",
    "smoke":            "Smoke_FSN",
    "pmax":             "Pmax_bar",
}

# ── Acceptance limits (project-specific — adjust per spec sheet) ──
LIMITS = {
    "nox_max_gkwh":      4.5,
    "smoke_max_fsn":     1.5,
    "egt_max_C":         780.0,
    "pmax_max_bar":      185.0,
    "fuel_rate_warn_gkwh": 250.0,
    "coolant_max_C":     102.0,
}


@dataclass
class RunResult:
    """Analysis result for one calibration test run."""
    run_id:        str
    duration_s:    float
    mean_values:   Dict[str, float] = field(default_factory=dict)
    max_values:    Dict[str, float] = field(default_factory=dict)
    violations:    List[str]       = field(default_factory=list)
    passed:        bool            = True


class CalibrationAnalyser:
    """
    Reads INCA MDF4 measurement files and produces automated analysis.

    Usage:
        a = CalibrationAnalyser()
        a.load_mdf("run_001_high_load.mf4")
        result = a.analyse()
        a.plot_time_history()
        a.export_report("run_001_report.csv")
    """

    def __init__(self):
        self.mdf:    Optional[asammdf.MDF] = None
        self.data:   Optional[pd.DataFrame] = None
        self.result: Optional[RunResult] = None

    def load_mdf(self, filepath: str):
        """Load an MDF4 file and extract all defined channels."""
        print(f"Loading: {filepath}")
        self.mdf = asammdf.MDF(filepath)

        series_dict = {}
        for key, channel_name in CHANNELS.items():
            try:
                sig = self.mdf.get(channel_name)
                # Resample to 10ms uniform grid
                sig_resampled = sig.interp(
                    new_samples=np.arange(sig.timestamps[0],
                                          sig.timestamps[-1], 0.01)
                )
                series_dict[key] = pd.Series(
                    sig_resampled.samples,
                    index=sig_resampled.timestamps,
                    name=key
                )
            except Exception as e:
                print(f"  [WARN] Channel '{channel_name}' not found: {e}")

        self.data = pd.DataFrame(series_dict)
        print(f"  Loaded {len(self.data)} samples, "
              f"duration={self.data.index[-1]:.1f}s")

    def analyse(self) -> RunResult:
        """Run automated analysis and limit checking."""
        if self.data is None:
            raise RuntimeError("No data loaded — call load_mdf() first")

        run_id = Path(self.mdf.name).stem if self.mdf else "unknown"
        result = RunResult(
            run_id=run_id,
            duration_s=float(self.data.index[-1])
        )

        # Compute mean and max for each channel
        for key in self.data.columns:
            result.mean_values[key] = float(self.data[key].mean())
            result.max_values[key]  = float(self.data[key].max())

        # Check limits
        checks = [
            ("nox",          "nox_max_gkwh",        "max"),
            ("smoke",        "smoke_max_fsn",        "max"),
            ("egt",          "egt_max_C",            "max"),
            ("pmax",         "pmax_max_bar",         "max"),
            ("coolant_temp", "coolant_max_C",        "max"),
            ("fuel_rate",    "fuel_rate_warn_gkwh",  "mean"),
        ]

        for channel, limit_key, stat in checks:
            if channel not in self.data.columns:
                continue
            limit_val = LIMITS.get(limit_key, float("inf"))
            actual    = result.max_values[channel] if stat == "max" \
                        else result.mean_values[channel]
            if actual > limit_val:
                result.violations.append(
                    f"{channel} {stat}={actual:.2f} exceeds limit {limit_val:.2f}"
                )
                result.passed = False

        # Smoke-NOx trade-off check: both cannot be simultaneously high
        if ("nox" in self.data.columns and "smoke" in self.data.columns):
            nox_high   = self.data["nox"]   > LIMITS["nox_max_gkwh"] * 0.9
            smoke_high = self.data["smoke"] > LIMITS["smoke_max_fsn"] * 0.9
            both_high  = (nox_high & smoke_high).sum()
            if both_high > 50:  # > 500ms both high
                result.violations.append(
                    f"NOx and Smoke simultaneously near limit for {both_high*10}ms"
                    f" — calibration operating point sub-optimal"
                )

        self.result = result
        return result

    def compute_bsfc_map(self, speed_bins: int = 10,
                          load_bins:  int = 10) -> pd.DataFrame:
        """
        Build a 2D BSFC map from measured data.
        Useful for verifying fuel economy calibration against target map.
        """
        if self.data is None:
            raise RuntimeError("No data loaded")

        df = self.data[["engine_speed", "engine_torque", "fuel_rate"]].copy()
        df = df.dropna()

        speed_edges = np.linspace(df["engine_speed"].min(),
                                  df["engine_speed"].max(), speed_bins + 1)
        load_edges  = np.linspace(df["engine_torque"].min(),
                                  df["engine_torque"].max(), load_bins + 1)

        bsfc_map = np.full((load_bins, speed_bins), np.nan)

        for i in range(load_bins):
            for j in range(speed_bins):
                mask = (
                    (df["engine_speed"]  >= speed_edges[j]) &
                    (df["engine_speed"]  <  speed_edges[j+1]) &
                    (df["engine_torque"] >= load_edges[i]) &
                    (df["engine_torque"] <  load_edges[i+1])
                )
                if mask.sum() >= 5:
                    bsfc_map[i, j] = df.loc[mask, "fuel_rate"].mean()

        speed_centres = (speed_edges[:-1] + speed_edges[1:]) / 2
        load_centres  = (load_edges[:-1]  + load_edges[1:])  / 2

        return pd.DataFrame(bsfc_map,
                            index=load_centres.round(0),
                            columns=speed_centres.round(0))

    def detect_anomalies(self, window_s: float = 1.0,
                          sigma_threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect outlier samples (sensor glitches, calibration instability)
        using rolling z-score method.

        Returns DataFrame of anomaly timestamps and magnitudes.
        """
        if self.data is None:
            raise RuntimeError("No data loaded")

        window_pts = max(1, int(window_s / 0.01))  # 10ms sample rate
        anomalies  = []

        for col in self.data.columns:
            series = self.data[col].dropna()
            if len(series) < window_pts * 3:
                continue

            rolling_mean = series.rolling(window_pts, center=True).mean()
            rolling_std  = series.rolling(window_pts, center=True).std()
            z_score      = (series - rolling_mean) / (rolling_std + 1e-9)

            outlier_mask = z_score.abs() > sigma_threshold
            for ts, val in series[outlier_mask].items():
                anomalies.append({
                    "timestamp_s": ts,
                    "channel":     col,
                    "value":       val,
                    "z_score":     float(z_score[ts]),
                    "rolling_mean": float(rolling_mean[ts])
                })

        return pd.DataFrame(anomalies).sort_values("timestamp_s")

    def plot_time_history(self, channels: Optional[List[str]] = None,
                           save_path: Optional[str] = None):
        """Plot selected channels over time."""
        if self.data is None:
            raise RuntimeError("No data loaded")

        channels = channels or list(self.data.columns)[:6]
        fig, axes = plt.subplots(len(channels), 1,
                                  figsize=(16, 3 * len(channels)), sharex=True)
        if len(channels) == 1:
            axes = [axes]

        for ax, ch in zip(axes, channels):
            if ch not in self.data.columns:
                continue
            ax.plot(self.data.index, self.data[ch], linewidth=0.8)
            ax.set_ylabel(ch, fontsize=9)
            ax.grid(True, alpha=0.3)

            # Overlay limits
            limit_map = {
                "nox":          ("nox_max_gkwh",   "r--"),
                "egt":          ("egt_max_C",       "r--"),
                "pmax":         ("pmax_max_bar",    "r--"),
                "coolant_temp": ("coolant_max_C",   "orange"),
            }
            if ch in limit_map:
                limit_key, style = limit_map[ch]
                ax.axhline(LIMITS[limit_key], linestyle=style.replace("--", ""),
                           color=style[0], linewidth=1.0, alpha=0.7,
                           label=f"Limit={LIMITS[limit_key]}")
                ax.legend(fontsize=8)

        axes[-1].set_xlabel("Time (s)")
        plt.suptitle(f"Calibration Run: {self.result.run_id if self.result else '?'}")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"Plot saved: {save_path}")
        plt.show()

    def export_report(self, output_csv: str):
        """Export analysis summary to CSV."""
        if self.result is None:
            self.analyse()

        rows = []
        for key in self.result.mean_values:
            rows.append({
                "channel":    key,
                "mean":       round(self.result.mean_values.get(key, 0), 3),
                "max":        round(self.result.max_values.get(key, 0), 3),
                "violations": "; ".join(
                    [v for v in self.result.violations if key in v]
                )
            })

        pd.DataFrame(rows).to_csv(output_csv, index=False)
        print(f"Report exported: {output_csv}")
        print(f"Overall: {'PASS' if self.result.passed else 'FAIL'}")
        if self.result.violations:
            for v in self.result.violations:
                print(f"  [VIOLATION] {v}")


# ── Batch analysis across multiple test runs ──────────────────────
def batch_analysis(run_directory: str, output_dir: str = "reports"):
    """
    Process all MDF4 files in a directory.
    Produces per-run CSV reports and a summary comparison.
    """
    from pathlib import Path
    import os

    Path(output_dir).mkdir(exist_ok=True)
    mdf_files = list(Path(run_directory).glob("*.mf4"))
    print(f"Found {len(mdf_files)} MDF4 files in {run_directory}")

    summary_rows = []
    for mdf_file in mdf_files:
        a = CalibrationAnalyser()
        a.load_mdf(str(mdf_file))
        result = a.analyse()
        anomalies = a.detect_anomalies()

        a.export_report(f"{output_dir}/{result.run_id}_report.csv")

        summary_rows.append({
            "run_id":       result.run_id,
            "duration_s":  result.duration_s,
            "mean_NOx":    result.mean_values.get("nox", np.nan),
            "max_EGT":     result.max_values.get("egt", np.nan),
            "mean_BSFC":   result.mean_values.get("fuel_rate", np.nan),
            "anomalies":   len(anomalies),
            "violations":  len(result.violations),
            "passed":      result.passed,
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(f"{output_dir}/batch_summary.csv", index=False)
    print(f"\nBatch complete. Summary: {output_dir}/batch_summary.csv")
    print(f"Pass rate: {summary['passed'].mean()*100:.0f}% "
          f"({summary['passed'].sum()}/{len(summary)})")
    return summary


if __name__ == "__main__":
    # Single run analysis
    a = CalibrationAnalyser()
    a.load_mdf("engine_doe_run_007.mf4")
    result = a.analyse()
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")

    bsfc_map = a.compute_bsfc_map()
    print("\nBSFC Map (g/kWh):")
    print(bsfc_map.to_string())

    anomalies = a.detect_anomalies()
    if not anomalies.empty:
        print(f"\n{len(anomalies)} anomalies detected:")
        print(anomalies.to_string(index=False))

    a.plot_time_history(
        channels=["engine_speed", "engine_torque", "nox", "egt", "boost_pressure"],
        save_path="run_007_time_history.png"
    )
    a.export_report("run_007_report.csv")
```

### 14.2 MATLAB MBC Toolbox — Response Surface Modelling

```matlab
% mbc_fit_and_optimise.m
% ─────────────────────────────────────────────────────────────────
% Fits response surface models to DoE data and finds optimal
% calibration values for injection timing and EGR rate.
%
% Input:  DoE results CSV (from Python batch analysis)
% Output: Optimal calibration map + model quality report
%
% Tool:   MATLAB R2024a, Model-Based Calibration Toolbox
% ─────────────────────────────────────────────────────────────────

%% Load DoE data
data = readtable('DoE_Results_Run_001.csv');

% Variables
EGR     = data.EGR_pct;
VGT     = data.VGT_pct;
Timing  = data.Timing_deg;

NOx     = data.NOx_gkwh;
BSFC    = data.BSFC_gkwh;
Pmax    = data.Pmax_bar;
EGT     = data.EGT_C;
Smoke   = data.Smoke_FSN;

%% Fit polynomial response surface models
fprintf('Fitting response surface models...\n');

X_coded = [EGR, VGT, Timing, EGR.*VGT, EGR.*Timing, VGT.*Timing, ...
           EGR.^2, VGT.^2, Timing.^2];

% Fit NOx model
mdl_NOx   = fitlm(X_coded, NOx,   'linear', 'RobustOpts','off');
mdl_BSFC  = fitlm(X_coded, BSFC,  'linear');
mdl_Pmax  = fitlm(X_coded, Pmax,  'linear');
mdl_EGT   = fitlm(X_coded, EGT,   'linear');
mdl_Smoke = fitlm(X_coded, Smoke, 'linear');

fprintf('Model R² values:\n');
fprintf('  NOx:   %.4f\n', mdl_NOx.Rsquared.Ordinary);
fprintf('  BSFC:  %.4f\n', mdl_BSFC.Rsquared.Ordinary);
fprintf('  Pmax:  %.4f\n', mdl_Pmax.Rsquared.Ordinary);
fprintf('  EGT:   %.4f\n', mdl_EGT.Rsquared.Ordinary);
fprintf('  Smoke: %.4f\n', mdl_Smoke.Rsquared.Ordinary);

%% Optimisation: minimise BSFC subject to emissions and structural limits
fprintf('\nRunning optimisation...\n');

% Design variable bounds
lb = [0,  20, -18];   % [EGR%, VGT%, Timing°]
ub = [30, 80, -2];    % upper bounds

% Constraints
function [c, ceq] = nonlinear_constraints(x, mdl_NOx, mdl_BSFC, ...
                                           mdl_Pmax, mdl_EGT, mdl_Smoke)
    x_coded = encode_x(x);

    NOx_pred   = predict(mdl_NOx,   x_coded);
    Pmax_pred  = predict(mdl_Pmax,  x_coded);
    EGT_pred   = predict(mdl_EGT,   x_coded);
    Smoke_pred = predict(mdl_Smoke, x_coded);

    % Inequality constraints (c ≤ 0 means feasible)
    c = [NOx_pred   - 3.5;    % NOx ≤ 3.5 g/kWh
         Pmax_pred  - 180;    % Pmax ≤ 180 bar
         EGT_pred   - 760;    % EGT ≤ 760°C
         Smoke_pred - 1.2];   % Smoke ≤ 1.2 FSN
    ceq = [];                  % no equality constraints
end

obj_fn = @(x) predict(mdl_BSFC, encode_x(x));
con_fn = @(x) nonlinear_constraints(x, mdl_NOx, mdl_BSFC, mdl_Pmax, ...
                                        mdl_EGT, mdl_Smoke);

% fmincon optimisation
opts = optimoptions('fmincon', 'Algorithm','sqp', ...
                    'Display','iter', 'MaxIterations',500);
x0   = [15, 50, -10];  % starting point
[x_opt, BSFC_opt, exitflag] = fmincon(obj_fn, x0, [], [], [], [], ...
                                        lb, ub, con_fn, opts);

fprintf('\nOptimal calibration point:\n');
fprintf('  EGR_Rate    = %.1f %%\n',  x_opt(1));
fprintf('  VGT_Position= %.1f %%\n',  x_opt(2));
fprintf('  Inj_Timing  = %.1f ° BTDC\n', x_opt(3));
fprintf('  Predicted BSFC = %.1f g/kWh\n', BSFC_opt);
fprintf('  Predicted NOx  = %.2f g/kWh\n', predict(mdl_NOx, encode_x(x_opt)));
fprintf('  Predicted Pmax = %.1f bar\n',   predict(mdl_Pmax, encode_x(x_opt)));

%% Generate 2D response surface plots
figure('Name','BSFC Response Surface vs EGR and Timing');
[EGR_grid, Timing_grid] = meshgrid(linspace(0,30,40), linspace(-18,-2,40));
VGT_fixed = 50;  % hold VGT at optimum

BSFC_grid = zeros(size(EGR_grid));
for i = 1:numel(EGR_grid)
    x_pt = [EGR_grid(i), VGT_fixed, Timing_grid(i)];
    BSFC_grid(i) = predict(mdl_BSFC, encode_x(x_pt));
end

surf(EGR_grid, Timing_grid, BSFC_grid, 'EdgeAlpha', 0.2);
xlabel('EGR Rate (%)'); ylabel('Injection Timing (° BTDC)');
zlabel('BSFC (g/kWh)'); title('BSFC Response Surface');
colorbar; hold on;
plot3(x_opt(1), x_opt(3), BSFC_opt, 'r*', 'MarkerSize', 15, ...
     'DisplayName', 'Optimum');
legend; saveas(gcf, 'BSFC_response_surface.png');

%% Helper function
function x_coded = encode_x(x)
    x_coded = [x, x(1)*x(2), x(1)*x(3), x(2)*x(3), ...
                x(1)^2, x(2)^2, x(3)^2];
end
```

---

## 15. Functional Safety and DFMEA for Calibration

### 15.1 Calibration-Related Functional Safety Items

Under ISO 26262, calibration data is considered part of the software development process. The following items have direct functional safety implications:

| Calibration Item | Safety Goal | Potential Violation | ASIL |
|---|---|---|---|
| Max torque limit map | Prevent driveline overload | Wrong torque limit → driveline failure | B |
| Derating maps | Prevent thermal damage causing loss of control | Missing derating → ECU/diesel thermal runaway | C |
| Shift inhibit at water fording | Prevent transmission engagement that causes jolt | Wrong mode signal → gear shift in water = stall | C |
| Idle speed calibration | Prevent engine stall in critical conditions | Idle too low → stall on incline = loss of braking | B |
| Fuel cutoff threshold | Prevent runaway | Fuel cutoff threshold too high → cannot stop engine | D |
| DPF regen inhibit | Prevent exhaust fire | Regen enabled in fording → exhaust fire | C |

### 15.2 DFMEA Participation

The calibration engineer participates in the Powertrain DFMEA by:
1. Identifying which calibration parameters can violate safety goals
2. Defining calibration limits (A2L min/max) as the first line of defence
3. Confirming that ECM range checks (limits) are implemented in software
4. Reviewing that calibration review/approval process is defined in the control plan
5. Sign-off that calibration data is verified before each ECM flash in production

### 15.3 Calibration Validation vs. Verification

| Activity | Definition | Owner | Evidence |
|---|---|---|---|
| Calibration Verification | Confirms calibration parameters are within design limits (A2L min/max) | CDM tool automated check | CDM limit check report |
| Calibration Validation | Confirms calibrated ECM delivers required system behaviour | Calibration engineer | Test report, dyno data, environmental sign-off |
| Design Verification (DVP&R) | Confirms the calibration strategy as a whole meets requirements | Lead Calibration Engineer | DVP matrix with pass/fail evidence |

---

## 16. Calibration Release Management

### 16.1 Calibration Release Plan

```
Milestone           Calibration Deliverable        Who Approves
──────────────────────────────────────────────────────────────────
PT SOP – 24w        Base calibration (dyno-only)   Lead Cal Eng
Vehicle Integration  Integration calibration         Cal + PT Integration
Env Chamber (Cold)  Cold weather dataset             Cal + Test Lead
Env Chamber (Hot)   Hot/altitude dataset             Cal + Test Lead
DVP&R gate           Full validation dataset         Systems + Cal Lead
SOQ / SOP           Production release dataset      Programme Manager
```

### 16.2 Release Package Contents

Each calibration release must include:
1. **Calibration file** (.hex / .cdf referenced to specific SW binary hash)
2. **A2L file version** used for the release
3. **Differences vs previous release** (change delta from CDM diff report)
4. **Confirmation tests** completed (minimum smoke test + gradeability check)
5. **Known limitations** (if any parameters are interim or placeholder)
6. **Sign-off evidence** (environmental test data for environmental releases)
7. **Linked JIRA/DOORS IDs** for requirements traceability

### 16.3 Configuration Management Rules

- **One A2L file per ECM software binary** — never mix A2L versions
- **Working page = development; reference page = released** — never release from working page without promotion
- **All calibration changes require peer review** before ECM flash on a gate campaign
- **Emergency calibration changes** (field fix during test campaign): allowed with single verbal approval + mandatory post-hoc peer review submission within 24 hours

---

## 17. Key Performance Metrics and Sign-Off Criteria

### 17.1 Performance Targets (Representative — Adjust to Programme Spec)

| Performance Parameter | Target | Test Method |
|---|---|---|
| Gradeability at full load | ≥ 60% gradient sustained | Gradeability ramp at test track |
| Cold start time at –32 °C | < 15s to first combustion | Controlled soak + timed start |
| Full torque availability at –32 °C | < 3 min after start | Torque measurement at output shaft |
| Max speed (road, unladen) | ≥ 110 km/h | GPS run on flat road |
| 0–50 km/h acceleration time | < 12s (combat load) | Stopwatch + GPS |
| Fuel economy (road normal) | ≤ 28 L/100km | Drive cycle measurement |
| NOx (if emission regulated) | < 3.5 g/kWh | Modal analysis on dyno |
| Smoke (FSN) | < 1.5 (all conditions) | AVL 415 smoke meter |
| ECT peak at full load | < 105 °C | Thermocouple/ECM log |
| DPF regen inhibit during fording | Zero regen events | DTC log + aftertreatment monitor |
| Shift quality jerk (road mode) | < 3 m/s³ | Accelerometer on floor |
| Stealth mode acoustic level | < 72 dB(A) at 10m | ISO 362 exterior noise method |

### 17.2 Sign-Off Evidence Checklist

```
For each calibration release, confirm:

□ Base performance (gradeability, acceleration) PASS
□ Cold start at –32 °C: pass/fail + log attached
□ Hot ambient at +55 °C: thermal derating within spec: pass/fail + log
□ Altitude at 4,500m: torque derating within spec: pass/fail + log
□ Water fording: no DTC, no stall, fan correctly disabled: pass/fail
□ Stealth mode: acoustic measurement < 72 dB(A): pass/fail + test report
□ NOx / Smoke: within limits or exemption applied: confirmed
□ DPF regen inhibit: confirmed by DTC log
□ Shift quality: jerk measurement < spec: pass/fail + measurement
□ CDM limit check: no out-of-limit parameters: CDM report attached
□ Peer review: reviewer sign-off on calibration change delta
□ Regression: no regressions confirmed vs previous baseline
```

---

## 18. Glossary

| Term | Definition |
|---|---|
| A2L | ASAP2 parameter description file — maps calibration names to ECM memory |
| ASAP2 | Association for Standardization of Automation and Measuring Systems — format 2 |
| BSFC | Brake-Specific Fuel Consumption — fuel mass per unit energy output (g/kWh) |
| CCA | Cold Cranking Amps — battery capability at low temperature |
| CDM | Calibration Data Management — tools and processes for managing calibration datasets |
| CDF | Calibration Data Format — file format for exchanging calibration parameters |
| CCP | CAN Calibration Protocol — predecessor to XCP |
| DoE | Design of Experiments — structured statistical test planning |
| DOC | Diesel Oxidation Catalyst — oxidises CO and HC |
| DPF | Diesel Particulate Filter — captures soot from exhaust |
| EGR | Exhaust Gas Recirculation — returns exhaust gas to intake to reduce NOx |
| EGT | Exhaust Gas Temperature |
| ECT | Engine Coolant Temperature |
| ECM | Engine Control Module |
| FSN | Filter Smoke Number — particulate smoke measurement unit |
| INCA | Integrated Calibration and Acquisition — ETAS calibration tool |
| IAT | Intake Air Temperature |
| LHS | Latin Hypercube Sampling — space-filling DoE design method |
| MAP | Manifold Absolute Pressure |
| MAF | Mass Air Flow |
| MBC | Model-Based Calibration — using statistical models to speed up calibration |
| MDF | Measurement Data Format — standard ASAM format for measurement data |
| NVH | Noise, Vibration, Harshness |
| SCR | Selective Catalytic Reduction — converts NOx using urea |
| TC | Torque Converter |
| TCM | Transmission Control Module |
| VGT | Variable Geometry Turbocharger |
| XCP | Universal Calibration Protocol — modern ECM communication for calibration |
| λ | Lambda — ratio of actual air-fuel ratio to stoichiometric |

---

## Document Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-04-24 | Powertrain Calibration Lead | Initial release |

---

*This document is a comprehensive learning reference. Specific values (temperatures, pressures, timing angles) are representative of a typical defence diesel powertrain. Programme-specific targets must be taken from the vehicle's Design Input Requirements specification.*
