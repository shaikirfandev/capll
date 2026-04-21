# Instrument Cluster Fundamentals — Marelli / LTTS Cluster Lead

> **Role Target:** Cluster Lead, L&T Technology Services → Marelli, Bangalore
> **Scope:** Instrument Cluster (IC) validation, CAN-based signal verification,
>            OEM cluster feature testing, gauge/telltale/display/NVM behaviour

---

## 1. Instrument Cluster Overview

An Instrument Cluster (IC) is the electronic display unit facing the driver that communicates vehicle status. It is one of the most visible safety-critical HMI (Human-Machine Interface) components in a vehicle.

### 1.1 Types of Clusters

| Type | Description | OEM Examples |
|---|---|---|
| Analog/Hybrid | Physical gauges + small TFT for trip/warning | Entry-level ICE vehicles |
| Semi-digital | Partial digital gauges + central display | Toyota, Maruti |
| Full Digital | All-TFT configurable display | BMW iDrive, VW MIB3, Mercedes MBUX |
| Head-Up Display (HUD) | Projected on windshield | Porsche, Audi |

### 1.2 Key Cluster Features to Validate

| Feature Category | Examples |
|---|---|
| Gauges | Speedometer, Tachometer, Fuel, Engine Temp, Boost |
| Telltales | MIL, SRS, ABS, EPB, TPMS, Seatbelt, Battery, EV-mode |
| Driver Information System (DIS/DIC) | Odometer, Trip A/B, Fuel Range, Avg Speed |
| Warning Messages | Priority-managed warning pop-ups |
| Chimes / Alerts | Seatbelt chime, overspeed beep, EV warning |
| Power Mode Behaviour | Cluster behaviour at KL15 ON/OFF, crank, wake |
| CAN Timeout Behaviour | Display fallback on signal loss |
| NVM (Non-Volatile Memory) | Odometer retention, trip save across ignition cycles |
| Illumination | Backlight brightness, day/night mode |
| International / Localisation | km/h vs mph, left/right hand drive |

---

## 2. CAN Signal Architecture for Instrument Cluster

### 2.1 Typical Network Topology

```
Instrument Cluster
    │
    ├── High-Speed CAN (500 kbps) — Powertrain Bus
    │       ECU: Engine ECU, TCU, ABS, EPS
    │       Messages: Speed, RPM, Gear, Fault data
    │
    ├── Low-Speed CAN / LIN — Body Bus
    │       ECU: BCM, HVAC, Lighting
    │       Messages: Door status, Ignition, Illumination
    │
    ├── MOST / Ethernet (luxury) — Infotainment Bus
    │       Connected to HMI stack, navigation
    │
    └── K-Line (legacy) — OBD/Diagnostic
```

### 2.2 Key CAN Messages for Cluster Validation

| Message Name | ID (example) | Source ECU | Signals |
|---|---|---|---|
| `VehicleSpeed` | 0x3B3 | ABS / ESC | `VehicleSpeed` [km/h × 0.01], `SpeedValid` |
| `EngineStatus` | 0x316 | ECM | `EngineRPM` [rpm × 0.25], `Throttle`, `EngineFault` |
| `FuelLevel` | 0x34A | BCM/FuelSensor | `FuelLevel_pct` [0-100], `LowFuelWarning` |
| `TCU_Info` | 0x3B4 | TCU | `CurrentGear`, `GearDisplayRequest` |
| `ABS_Status` | 0x3A5 | ABS | `ABS_Active`, `EBD_Active`, `ABS_Fault` |
| `SRS_Status` | 0x3A6 | Airbag ECU | `SRS_Fault`, `OccupantDetect` |
| `BCM_Status` | 0x3A0 | BCM | `DoorOpen`, `SeatbeltUnfastened`, `Handbrake` |
| `TPMS_Status` | 0x3C0 | TPMS ECU | `TyrePressure[4]`, `TyreWarn` |
| `BMS_SOC` | 0x3A2 | BMS | `SOC_pct`, `ChargingStatus` (EV/HEV) |
| `ClimateStatus` | 0x4A0 | HVAC | `TargetTemp`, `FanSpeed` |

### 2.3 Signal Definition (DBC Format Understanding)

```
BO_ 955 VehicleSpeed: 8 ABS
 SG_ VehicleSpeed M : 0|16@1+ (0.01,0) [0|655.35] "km/h" Vector__XXX
 SG_ SpeedValid : 16|1@1+ (1,0) [0|1] "" Vector__XXX
 SG_ SpeedDirection : 17|2@1+ (1,0) [0|3] "" Vector__XXX

/*
 Decoding: VehicleSpeed_raw = 0x0BB8 = 3000
 Physical = 3000 × 0.01 = 30.00 km/h
*/
```

---

## 3. Telltale (Warning Lamp) Validation

### 3.1 Telltale Priority Levels (ISO 2575)

| Priority | Colour | Examples | Action |
|---|---|---|---|
| P1 — Red / Critical | Red | MIL (solid), SRS, ABS+EBD, Oil Pressure, Overheat | Stop vehicle immediately |
| P2 — Yellow / Warning | Amber | TPMS, Engine Fault, Battery, Low Fuel | Service required |
| P3 — Green / Info | Green | Turn Indicator, High Beam, ACC active | Information only |
| P4 — Blue / Info | Blue | High Beam indicator | Information only |

### 3.2 Telltale Test Design Checklist

```
For each telltale, validate:

1. ACTIVATION
   ✓ Correct CAN signal bit/value triggers telltale ON
   ✓ Correct activation timing (immediate vs debounced)
   ✓ No false activation on adjacent bit patterns

2. DE-ACTIVATION
   ✓ Correct CAN signal clears telltale
   ✓ Latching behaviour (stays on until cleared by service)

3. PRIORITY
   ✓ Higher-priority telltale suppresses lower (when space limited)
   ✓ Multiple simultaneous telltales ranked correctly

4. SELF-CHECK (Bulb Check)
   ✓ All telltales illuminate for 2–3s at KL15 ON
   ✓ All extinguish at bulb check timeout

5. CAN TIMEOUT
   ✓ Signal provider fails → telltale enters default state (usually ON)

6. NVM
   ✓ Fault confirmed DTCs re-displayed after ignition cycle

7. LOCALISATION
   ✓ Icon matches market (AU, EU, IN, US cluster variants differ)
```

### 3.3 CAPL Script — Telltale Functional Test

```capl
/*--- Automated Telltale Test: ABSFault Telltale ---*/
variables {
    message 0x3A5 ABS_Status_msg;
    msTimer telltaleCheckTimer;
    int testResult;
}

on start {
    testResult = -1;
    write("=== ABS Fault Telltale Test START ===");

    /* Step 1: Ensure clean state */
    ABS_Status_msg.ABS_Fault = 0;
    ABS_Status_msg.ABS_Active = 0;
    output(ABS_Status_msg);
    setTimer(telltaleCheckTimer, 500);  /* Wait 500ms for cluster to settle */
}

on timer telltaleCheckTimer {
    /* Step 2: Inject ABS fault signal */
    ABS_Status_msg.ABS_Fault = 1;
    output(ABS_Status_msg);
    write("ABS_Fault CAN signal injected = 1");

    /* Step 3: Wait for telltale to activate */
    setTimer(telltaleCheckTimer, 200);
}

/* Read back cluster telltale feedback on diagnostic response */
on message 0x726 {   /* Cluster UDS response ID */
    if (this.byte(2) == 0x01) {  /* ABS telltale active */
        write("PASS: ABS Telltale activated correctly");
        testResult = 0;
    } else {
        write("FAIL: ABS Telltale NOT activated");
        testResult = 1;
    }
}
```

---

## 4. Gauge Validation

### 4.1 Speedometer Accuracy Test

```
Test procedure:
1. Inject VehicleSpeed at 0, 10, 20, 30, 40, 60, 80, 100, 120, 140, 160, 200 km/h
2. Measure displayed value via camera inspection or diagnostics
3. Compare against tolerance: ±3 km/h or ±2% (whichever is greater) — EU Regulation 39

OEM-specific: Many OEMs mandate cluster shows speed HIGHER than GPS by 0–+5 km/h
(OEM never under-reads — liability) → confirm this in OEM SRS.
```

### 4.2 Tachometer

```
Signal: EngineRPM = RPM_raw × 0.25
Range: 0–8000 RPM (petrol), 0–5000 RPM (diesel)
Redline: at 6500 RPM — validate red-zone colour change

Test: Inject EngineRPM from 0→8000 in 250 RPM steps
Check: Needle position accuracy ±2%
Check: Redline marker starts at correct RPM
Check: Over-speed behaviour at RPM > max_scale
```

### 4.3 Fuel Gauge — Non-linear OEM Mapping

```
Fuel gauge is NOT linear. OEM applies a custom curve:
  - 0–10 Litre: Reads Empty faster (reserve protection)
  - 10–35 Litre: Normal linear range
  - 35–40 Litre: Reads Full more slowly (tank shape compensation)

Validation CAPL: Ramp FuelLevel_pct from 100→0 at 1% steps, 200ms intervals
Verify: Needle movement matches OEM fuel gauge mapping document
Verify: Low Fuel Warning telltale activates at correct Reserve point
```

---

## 5. NVM (Non-Volatile Memory) Validation

### 5.1 Odometer — Safety-Critical NVM

```
ISO 16844: Odometer must be protected against tampering and rollback.

VALIDATION TEST SEQUENCE:
1. Record current odometer value: X km
2. Inject VehicleSpeed = 100 km/h for 60 seconds → distance += 1.666 km
3. Perform ignition OFF (KL15 = 0) → wait 5 seconds
4. Ignition ON (KL15 = 1)
5. Read odometer → expect X + 1.666 km (±0.1 km tolerance)
6. Perform battery disconnect (KL30 = 0) → reconnect
7. Read odometer → must NOT rollback

Tools: UDS 0x22 ReadDataByIdentifier (DID 0xF400 often = odometer)
CAPL: Use Diagnostics.SendRequest() or Udm_Request() for UDS reads
```

### 5.2 Trip Meter Validation

```
Tests:
- Trip A/B reset via stalk/button → verify reset to 0.0 km
- Trip memory survives KL15 cycle
- Trip A/B are independent
- Display rolls over at 9999.9 km → 0.0 km (trip only, not odo)
```

---

## 6. Cluster Power Mode & KL15 Behaviour

### 6.1 Power Mode Sequence

```
KL30 ON (battery)
   → Cluster wakes from sleep
   → Internal self-test (NVM checksum, RAM test)
   → Wait for KL15

KL15 ON (ignition)
   → Bulb check (all telltales ON for 2–3s)
   → Welcome animation
   → CAN buses active
   → Start receiving VehicleSpeed, RPM etc.

Engine Crank
   → RPM goes from 0 → idle (~800 RPM)
   → MIL may momentarily activate then clear (normal)

KL15 OFF (ignition off)
   → After-run behaviour (cooling fan, DPF regen)
   → Cluster saves NVM (odo, trip)
   → Sleep animation / fade out
   → Cluster enters low-power sleep (<2mA quiescent allowed)

KL30 OFF
   → Full power remove — no resume needed
```

---

## 7. CAN Timeout / Fallback Display Validation

### 7.1 Strategy Types

| Strategy | Cluster Behaviour on Signal Timeout |
|---|---|
| Last Value Hold | Display last known value for N seconds |
| Substitute Value | Display a default (e.g., "–.–" or 0) |
| Telltale ON | Light a warning lamp (e.g., CAN network fault) |
| Error Message | Show "SERVICE REQUIRED" in DIS |

### 7.2 CAPL — CAN Timeout Injection Test

```capl
on start {
    write("=== CAN Timeout Test: VehicleSpeed ===");
    /* Inject speed at 60 km/h */
    message 0x3B3 vspd;
    vspd.VehicleSpeed = 6000;  /* raw = 60 km/h */
    output(vspd);
    setTimer(activeTimer, 2000);
}

msTimer activeTimer;
msTimer faultTimer;

on timer activeTimer {
    /* Stop sending speed message — simulate ECU fault */
    write("VehicleSpeed transmission STOPPED — timeout test begins");
    /* Do NOT call output(vspd) → cluster should see timeout */
    setTimer(faultTimer, 3000);  /* Observe after 3s */
}

on timer faultTimer {
    /* Read cluster response — confirm fallback */
    write("Verify cluster shows '--' or 0 km/h on speedometer");
    write("Verify CAN_NetworkFault telltale activated");
    /* If cluster has DiagnosticDataRequest DID, read it here */
}
```

---

## 8. OEM Standards Commonly Applied

| Standard | Application to Cluster |
|---|---|
| ISO 2575 | Symbols for vehicle controls, telltale icons |
| ISO 4513 | Visibility of instrument cluster from driver position |
| UN ECE Reg 39 | Speedometer accuracy requirements |
| ISO 16844 | Tachometers and odometers (road vehicle instrumentation) |
| ISO 11992 | Vehicle bus networks |
| OEM-specific SRS | Every customer (Marelli OEM: FCA, Renault, Honda etc.) has own SRS document |

---

## 9. Common Defects in Cluster Validation

| Defect | Root Cause | Detection Method |
|---|---|---|
| Speed flicker at 0 km/h | Missing SpeedValid flag handling | Trace analysis |
| Odometer rollback after KL30 | NVM write order bug | Power cycle sequence test |
| Fuel needle stuck at E | Signal scaling mismatch (DBC vs physical) | DBC audit + injection |
| MIL latches after fault cleared | Cluster latching logic error | Fault clear + drive cycle test |
| Telltale missing at bulb check | Wrong display layer priority | Self-check validation |
| Chime not playing | Missing prerequisite CAN signal (ignition valid) | Trace dependency analysis |
| Gear display shows P when in N | DBC mismatch → signal overlap | Enumerations audit in DBC |
| Backlight doesn't dim | Illumination signal not received | Body bus verification |

---

---

## 10. Cluster Variant Management

### 10.1 Common Variants for a Single Platform

| Variant Axis | Options | CAN Implication |
|---|---|---|
| Unit system | km/h vs mph (US/UK markets) | Speed signal same — cluster renders in mph |
| Steering hand | LHD vs RHD | No CAN impact — display mirror is HW-based |
| Language | 30+ OEM market languages | DIS strings loaded from NVM at first KL15 |
| Fuel type | Petrol / Diesel / EV / HEV | Different gauge sets displayed |
| Trim level | Base / Mid / Top | DIS feature set varies — different SW builds |
| Region | EU / NAM / APAC | Regulatory warning icons differ (ISO 2575 vs SAE J1048) |

### 10.2 Variant Test Strategy

```
METHOD 1 — Parameterised CAPL:
  - A single CAPL test script parametrised via environment variable "market"
  - Speedometer expected values change based on market (km/h or mph)
  - Fuel economy: L/100km (EU) vs MPG (US) vs km/L (Japan)

METHOD 2 — Multiple DBC + config files:
  - variant_eu.cfg / variant_us.cfg — loaded at startup
  - Different CAN IDs for TPMS in NAM vs EU (OEM-specific)

VALIDATION APPROACH FOR EACH VARIANT:
  1. Load correct SW build + DBC for that market
  2. Run the full regression suite
  3. Verify unit labels, decimal places, and localisation strings
  4. Check regulatory telltale icons match ISO 2575 (EU) or SAE J1048 (US)
```

### 10.3 Localisation Test Points

```
- Speed display: "120 km/h" vs "74 mph" — check rounding, no decimal on speed
- Fuel economy: "7.5 L/100km" vs "31 MPG" — both from same signal, different formula
  Formula: MPG = 235.214 / (L_per_100km)
- Temperature: °C vs °F: °F = (°C × 9/5) + 32
- Distance (trip): km to 1dp decimal, miles to 1dp decimal
- DIS language: cluster loads language pack from NVM on first boot (or via UDS write)
- Max speedometer scale: EU typically 260 km/h, US 160 mph (scale ring changes)
```

---

## 11. EV / HEV Specific Cluster Signals

### 11.1 EV-Unique Displays (replacing ICE gauges)

| Display | Signal Source | Replaces |
|---|---|---|
| State of Charge (SOC %) | BMS on CAN | Fuel gauge |
| Power meter (kW in/out) | BMS / VCU | Tachometer (often overlaid) |
| Range estimate (km) | VCU | Fuel range in DIS |
| Charging status | BMS / ChargeCtrl | Fuel pump telltale |
| Regen indicator | VCU | None — EV-specific |
| Ready indicator ("READY") | VCU | MIL position | 

### 11.2 CAN Signals for BMS/EV Cluster Validation

```
BMS → Cluster (example, OEM-specific IDs):

0x3A2  BMS_Status (10ms cycle)
  SOC_pct       [0|16@1+] (0.5, 0)   — 0.5% resolution
  SOH_pct       [16|8@1+] (1, 0)     — battery health
  BatteryVoltage [24|12@1+] (0.1, 0) — pack voltage
  BatteryTemp   [36|8@1+] (1, -40)   — offset -40°C

0x3A3  VCU_Status (10ms cycle)
  DriveRange_km  [0|16@1+] (1, 0)     — GOM (Guess-O-Meter)
  ChargingState  [16|4@1+] (1, 0)
      0 = Not charging
      1 = AC charging
      2 = DC fast charge
      3 = Regen active
  ReadySignal    [20|1@1+] (1, 0)     — Cluster shows READY lamp
```

### 11.3 EV Cluster Validation Points

```
1. SOC gauge:
   - Inject SOC = 0, 10, 20 ... 100% → verify gauge matches
   - Low battery warning at OEM threshold (typically 10% or 15%)
   - Empty warning at 5% (OEM-specific)
   - Gauge rate of change: gauge must not jump — filter/smoothing validation

2. Charging screen:
   - AC charge = slow fill animation
   - DC fast charge = faster fill animation + kW display
   - Full charged = 100% + "CHARGED" message

3. READY lamp:
   - VCU sends ReadySignal=1 → green READY lamp on cluster
   - Appears only after HV pre-charge complete (safety requirement)
   - Validated via CAPL: inject ReadySignal=0,1,0 and verify telltale

4. Range display:
   - GOM (range km) decreases as injected SOC decreases
   - Compare displayed range vs (SOC × battery_capacity / avg_consumption)
   - "--" shown when range data unavailable (signal timeout)
```

---

## 12. Cluster Validation Interview Q&A — Domain Knowledge

| Question | Answer |
|---|---|
| What is the bulb check sequence? | At KL15 ON, cluster activates all telltales for ~2–3 seconds to verify display elements function |
| Why is the speedometer calibrated to always over-read? | EU Reg 39 forbids under-reading (dangerous) — permitted over-read is ≤10% + 4 km/h |
| What is NVM in cluster context? | Flash memory storing odometer, trip counters, DTC data, calibration tables — must survive power loss |
| How does the cluster receive gear position? | From TCU via CAN — `CurrentGear` signal in TCU message (0=P, 1=R, 2=N, 3=D, 4-8 = gears) |
| What is a timeout fallback? | How cluster displays signal data when CAN message is no longer received within expected cycle time |
| What is ASIL B relevance to cluster? | Speedometer is an ASIL B function — must not show misleading speed under any fault |
| What is a DID? | Data Identifier — used in UDS ReadDataByIdentifier (0x22) to read specific ECU data |
| What is a DTC? | Diagnostic Trouble Code — fault code stored in ECU NVM readable via UDS 0x19 service |
| How do you validate odometer accuracy? | Inject known speed × time, compare CAN-calculated km vs cluster-displayed km |
| What is a MIL? | Malfunction Indicator Lamp — the "check engine" amber telltale required by OBD legislation |
| What causes a MIL to remain latched? | ECU stores DTC that requires a drive cycle to clear — cluster reads DTC presence from ECM |
| What is TPMS? | Tyre Pressure Monitoring System — required by EU Reg. 661/2009 since 2014 |
| What are P-codes and B-codes? | Powertrain and Body OBD DTCs — P0xxx = generic, P1xxx = OEM specific |
| What is KL15 vs KL30? | KL30 = battery (always on). KL15 = ignition-switched power (controlled by ignition key) |
| What is cluster self-test / IGN-on test? | Sequence where cluster sweeps all gauges, lights all telltales, plays chime — verifies hardware |

---

*File: 01_instrument_cluster_fundamentals.md | marelli_cluster_lead series*
