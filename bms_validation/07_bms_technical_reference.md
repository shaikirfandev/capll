# BMS Validation — Technical Reference Guide

> **Domain:** Battery Management System (BMS) — Validation Engineering
> **Covers:** Architecture, Algorithms, Protocols, Thresholds, Test Strategy, ISO Standards

---

## Table of Contents

1. [Cell Chemistry & Parameter Reference](#1-cell-chemistry--parameter-reference)
2. [BMS State Machine Reference](#2-bms-state-machine-reference)
3. [SoC / SoH / SoP Algorithms](#3-soc--soh--sop-algorithms)
4. [Cell Balancing Methods](#4-cell-balancing-methods)
5. [Contactor Logic & Precharge](#5-contactor-logic--precharge)
6. [Isolation Monitoring (IMD)](#6-isolation-monitoring-imd)
7. [Thermal Management](#7-thermal-management)
8. [CAN Signal Architecture](#8-can-signal-architecture)
9. [UDS Service Reference](#9-uds-service-reference)
10. [DTC Reference Table](#10-dtc-reference-table)
11. [ISO Standards Reference](#11-iso-standards-reference)
12. [Test Coverage Matrix](#12-test-coverage-matrix)
13. [Interview Q&A — BMS Deep Dive](#13-interview-qa--bms-deep-dive)

---

## 1. Cell Chemistry & Parameter Reference

### Lithium-Ion (NMC / NCA) — Common in BEV

| Parameter | Value | Notes |
|---|---|---|
| Nominal Voltage | 3.60–3.70 V | Per cell |
| Max Charge Voltage | 4.20–4.25 V | OV2 threshold |
| Min Discharge Voltage | 2.50–3.00 V | UV2 threshold |
| Typical Capacity | 3–100 Ah | Depends on format (cylindrical/prismatic/pouch) |
| Max Charge Temp | 45°C | C-rate dependent |
| Max Discharge Temp | 60°C | Pulse power |
| Min Charge Temp | 0°C (standard) | 10°C for fast charge |
| Min Discharge Temp | -20°C | |
| Cycle Life | 500–2000 cycles | To 80% SoH |
| Coulombic Efficiency | 99.5% (at 25°C) | Drops to ~85% at -20°C |

### LFP (LiFePO₄) — Common in PHEV, Stationary

| Parameter | Value |
|---|---|
| Nominal Voltage | 3.20–3.30 V |
| Max Charge Voltage | 3.60–3.65 V |
| Min Discharge Voltage | 2.50 V |
| Cycle Life | 2000–5000 cycles |
| Thermal Runaway Temp | > 270°C (safer than NMC) |

### OCV-SoC Curve (NMC, 25°C)

| SoC (%) | OCV (V) |
|---|---|
| 100 | 4.18 |
| 90  | 4.08 |
| 80  | 3.98 |
| 70  | 3.88 |
| 60  | 3.80 |
| 50  | 3.73 |
| 40  | 3.68 |
| 30  | 3.62 |
| 20  | 3.55 |
| 10  | 3.42 |
| 0   | 3.00 |

> **Key Note:** OCV curves shift with temperature. At -20°C, OCV for 50% SoC may be ~3.58 V instead of 3.73 V — if BMS uses a 25°C-only table, SoC will be overestimated in cold conditions.

---

## 2. BMS State Machine Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                     BMS TOP-LEVEL STATE MACHINE                  │
│                                                                   │
│  POWER_OFF ──────────────── KL30 ON ────────────► INIT          │
│                                                     │             │
│                               POST complete  ◄──────┘             │
│                                    │                              │
│                               ┌────▼───────────────────────┐      │
│                               │          IDLE               │      │
│                               │  (HV bus disconnected)      │      │
│                               └────┬───────────────────────┘      │
│                                    │ HV_Request                   │
│                               ┌────▼───────────────────────┐      │
│                               │       PRECHARGE             │      │
│                               │  Main- ON + Precharge ON    │      │
│                               │  V_dclink rising...         │      │
│                               └────┬──────────┬────────────┘      │
│                                    │ 95% ratio  Timeout           │
│                               ┌────▼─────┐  ┌──▼──────────┐      │
│                               │ HV_READY │  │    FAULT     │      │
│                               │ Normal   │  │  All open    │      │
│                               │ operation│  └─────────────┘      │
│                               └────┬─────┘                       │
│                                    │ HV_Off OR Fault              │
│                               ┌────▼───────────────────────┐      │
│                               │         HV_OFF              │      │
│                               │  Open Main+ then Main-      │      │
│                               └─────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed BMS Operating Sub-States

| State | HV Bus | Balancing | Charging | Description |
|---|---|---|---|---|
| INIT | OFF | OFF | OFF | Boot, POST, NVM read |
| IDLE | OFF | ON (if delta > threshold) | OFF | Ready to accept HV request |
| PRECHARGE | Partial | OFF | OFF | Charging DC link |
| HV_READY | ON | ON | OFF | Normal discharge/regen |
| CHARGING | ON | ON | ON | External charger connected |
| FAULT | OFF | OFF | OFF | Protection fault active |
| SLEEP | OFF | OFF | OFF | Deep sleep, wake on CAN |

---

## 3. SoC / SoH / SoP Algorithms

### SoC — State of Charge

**Method 1: Coulomb Counting**

$$\text{SoC}(t) = \text{SoC}(t_0) + \frac{1}{Q_{nom}} \int_{t_0}^{t} \eta(\text{T}) \cdot I(\tau) \, d\tau$$

| Symbol | Description |
|---|---|
| $Q_{nom}$ | Nominal capacity at 25°C [Ah] |
| $\eta(T)$ | Coulombic efficiency (temperature-dependent, 0.85–0.99) |
| $I(\tau)$ | Pack current [A] (positive = discharge) |

**Method 2: OCV Method (rest state)**

Read OCV after ≥ 2 hours rest → Look up SoC from temperature-indexed OCV table.

**Method 3: Extended Kalman Filter (EKF)**

Combines Coulomb Counting (prediction) with OCV measurement (correction):

```
State vector:  x = [SoC, V_rc1, V_rc2]   (SoC + RC circuit states)
Process model: x(k+1) = f(x(k), I(k))
Observation:   V_terminal = g(x(k)) + noise

Predict:  x̂(k+1|k) = f(x̂(k), I(k))
         P(k+1|k) = F·P(k)·Fᵀ + Q

Update:   K = P(k+1|k)·Hᵀ·(H·P(k+1|k)·Hᵀ + R)⁻¹
         x̂(k+1) = x̂(k+1|k) + K·(V_meas - g(x̂(k+1|k)))
         P(k+1) = (I - K·H)·P(k+1|k)
```

### SoH — State of Health

$$\text{SoH} = \frac{Q_{actual}}{Q_{initial}} \times 100\%$$

Calculated via full reference discharge (CC discharge at 0.2C from 100% to cutoff voltage).

**EoL (End of Life) criterion:** SoH < 80% (capacity retention)

### SoP — State of Power

Maximum available power at current SoC and temperature:

$$P_{max,discharge} = V_{OCV}(SoC) \cdot I_{max,discharge}(T, SoC)$$

Transmitted to VCU via CAN: `Max_Discharge_Power`, `Max_Charge_Power` [W]

---

## 4. Cell Balancing Methods

### Passive Balancing

```
┌─────┐   S₁    R₁(100Ω)
│Cell │───/  ───┤>├──┐
└─────┘              │
                     GND

When S₁ closed: I_bleed = V_cell / R_bleed ≈ 4.2V / 100Ω = 42 mA
Energy dissipated as heat.
```

| Pros | Cons |
|---|---|
| Simple, low cost | Energy wasted as heat |
| No EMI concerns | Slow balancing |
| Low BOM | Thermal design challenge |

**Activation:** V_max - V_min > 10 mV
**Target:** All cells at V_min + 2 mV
**Suspension:** During discharge > 0.5C (thermal risk)

### Active Balancing (Inductor-Based)

```
         L1            L2
Cell_H ──┤├──M₁──┬──M₂──┤├── Cell_L
                 │
              Shared
              Node
```

Energy transferred from high-SoC cell to low-SoC cell.
Efficiency: 85–95%.

---

## 5. Contactor Logic & Precharge

### Precharge Calculation

| Parameter | Formula | Example |
|---|---|---|
| Time constant | $\tau = R_{pc} \times C_{dclink}$ | 40Ω × 3000µF = 120 ms |
| Time to 95% | $t_{95\%} = 3\tau$ | 360 ms |
| Peak inrush (with R) | $I_{peak} = V_{batt} / R_{pc}$ | 400V / 40Ω = 10 A |
| Peak inrush (no R) | $I_{peak} = V_{batt} / R_{int}$ | 400V / 0.1Ω = 4000 A |

### Precharge State Machine Timing

```
t=0 ms:   Main- CLOSED
t=5 ms:   Precharge CLOSED
t=5→365ms: V_dclink rises to 95%: 380V
t=365ms:  Main+ CLOSED
t=365ms:  Inrush measured (< 50 A required)
t=415ms:  Precharge OPEN
t=615ms:  HV READY
```

### Contactor Weld Detection

After precharge open command:
1. Wait 200 ms
2. Measure current through precharge path
3. If I > 0.5 A → weld detected → DTC P0A3A

---

## 6. Isolation Monitoring (IMD)

### Standard Requirements

| Standard | Requirement |
|---|---|
| ISO 6469-3 | R_iso ≥ 500 Ω/V × V_nominal during operation |
| UN R100 | Isolation resistance monitoring mandatory for EV |
| IEC 62196 | Isolation check before connector energisation |

### Measurement Principle

The IMD injects a low-frequency measurement signal and measures response:

$$R_{iso} = \frac{V_{inj} \times R_{k}}{V_{meas}} - R_{k}$$

Where $R_k$ is the known internal coupling resistance.

### Threshold Levels (example at 400V pack)

| Level | R_iso (Ω) | R_iso (Ω/V at 400V) | BMS Action |
|---|---|---|---|
| NORMAL | > 200 kΩ | > 500 | None |
| WARN | 80–200 kΩ | 200–500 | DTC + Driver Warning |
| CRITICAL | 40–80 kΩ | 100–200 | 50% Charge Limit |
| EMERGENCY | < 40 kΩ | < 100 | Immediate HV Off |

### IMD Test (Startup POST)

1. IMD injection: apply test signal below safety threshold
2. Verify measurement circuit responds correctly
3. Verify threshold-crossing detection at each level
4. Duration: < 200 ms added to startup time

---

## 7. Thermal Management

### Cooling System Architecture

```
┌────────────────────────────────────────────────────┐
│                 BATTERY PACK                        │
│  [Module 1] [Module 2] ... [Module N]               │
│      │           │               │                  │
│  ────┴───────────┴───────────────┴────              │
│                Cooling Plate                        │
│                (liquid channels)                    │
└──────────────────┬─────────────────────────────────┘
                   │
            ┌──────▼──────┐
            │ Coolant Pump │ (PWM controlled 0–100%)
            └──────┬───────┘
                   │
            ┌──────▼──────┐
            │    Chiller   │ (A/C compressor driven)
            └─────────────┘
```

### Thermal Control Zones

| Zone | Temp Range | Cooling | Heater | Power |
|---|---|---|---|---|
| COLD | T < 0°C | OFF | ON | Charge limited to 0.5C |
| NORMAL | 0–35°C | 20% | OFF | 100% |
| WARM | 35–40°C | 50% | OFF | 100% |
| HOT_L1 | 40–45°C | 80% | OFF | 80% |
| HOT_L2 | 45–50°C | 100% | OFF | 50% |
| CRITICAL | > 50°C | 100% | OFF | 0% + DTC |

### Cell Temperature Gradient Management

BMS must monitor **per-cell** or **per-module** maximum temperature, not just average.
A high-resistance cell (aging, micro-short) can be 5–10°C hotter than module average.

---

## 8. CAN Signal Architecture

### BMS CAN Message Map

| ID (hex) | Message Name | Direction | Cycle | DLC | Key Signals |
|---|---|---|---|---|---|
| 0x3A0 | BMS_Status | BMS→VCU | 10 ms | 8 | SoC, SoH, BMS_State, Fault_Level |
| 0x3A1 | BMS_Voltage | BMS→VCU | 50 ms | 8 | Pack_V, Max_Cell_V, Min_Cell_V, Delta_mV |
| 0x3A2 | BMS_Current | BMS→VCU | 10 ms | 4 | Pack_Current, Direction |
| 0x3A3 | BMS_Temperature | BMS→VCU | 100 ms | 8 | Max_T, Min_T, Avg_T |
| 0x3A4 | BMS_Limits | BMS→VCU | 50 ms | 8 | Max_Chg_Power, Max_Disch_Power |
| 0x3A5 | BMS_CellBalance | BMS→VCU | 200 ms | 8 | Balance_Active, Cell_Delta |
| 0x3A6 | BMS_ContStatus | BMS→VCU | 10 ms | 4 | CTR_State, VDcLink, MainPlus, MainMinus |
| 0x4A0 | VCU_HVRequest | VCU→BMS | 10 ms | 4 | HV_Request, Crash_Signal, Charge_Enable |
| 0x600 | CHG_Control | Charger→BMS | 100 ms | 8 | Chg_Voltage, Chg_Current, Chg_Status |

### Signal Encoding Examples

```
BMS_Status (0x3A0):
  Byte 0:    SoC [0..200] → physical = raw × 0.5 %   (0–100%)
  Byte 1:    SoH [0..200] → physical = raw × 0.5 %
  Byte 2:    BMS_State [0..7]
  Byte 3:    Fault_Level [0..3]  (0=None, 1=Warn, 2=Critical, 3=Emergency)
  Byte 4:    Active_DTC_Count [0..255]
  Byte 5:    Balance_Active [0..1]
  Byte 6-7:  Checksum (CRC-8)

BMS_Voltage (0x3A1):
  Byte 0-1:  Pack_Voltage      [0..65535] → raw × 0.1 V  (0–6553.5 V)
  Byte 2-3:  Max_Cell_Voltage  [0..65535] → raw × 0.001 V (0–65.535 V)
  Byte 4-5:  Min_Cell_Voltage  [0..65535] → raw × 0.001 V
  Byte 6-7:  Cell_Delta_mV     [0..65535] mV
```

---

## 9. UDS Service Reference

### Session Types

| Session | SID | Sub-function | Access |
|---|---|---|---|
| Default | 0x10 | 0x01 | Always available |
| Extended | 0x10 | 0x03 | Read live data, clear DTCs |
| Programming | 0x10 | 0x02 | Flash, calibration write |

### Complete BMS UDS Service Matrix

| SID | Service | BMS Support | Session Required | Security |
|---|---|---|---|---|
| 0x10 | DiagnosticSessionControl | ✓ | Any | None |
| 0x11 | ECUReset (Hard/Soft/Key off) | ✓ | Extended | Level 1 |
| 0x14 | ClearDiagnosticInformation | ✓ | Extended | None |
| 0x19 | ReadDTCInformation | ✓ | Any | None |
| 0x22 | ReadDataByIdentifier | ✓ | Any | None |
| 0x27 | SecurityAccess | ✓ | Extended | — |
| 0x28 | CommunicationControl | ✓ | Extended | Level 1 |
| 0x2E | WriteDataByIdentifier | ✓ | Extended/Prog | Level 1 |
| 0x2F | InputOutputControlByIdentifier | ✓ | Extended | Level 1 |
| 0x31 | RoutineControl | ✓ | Extended | Level 1 |
| 0x34 | RequestDownload | ✗ | — | — |
| 0x35 | RequestUpload | ✗ | — | — |
| 0x3E | TesterPresent | ✓ | Any | None |
| 0x85 | ControlDTCSetting | ✓ | Extended | None |

### ReadDTC Sub-Functions Used for BMS

| Sub-fn | Code | Usage |
|---|---|---|
| reportNumberOf DTCByStatusMask | 0x01 | Count active DTCs |
| reportDTCByStatusMask | 0x02 | Read all DTCs with status |
| reportDTCSnapshotByDTCNumber | 0x04 | Freeze frame for specific DTC |
| reportSupportedDTC | 0x0A | Get full DTC list |

### Security Algorithm (Example — BMS Level 1)

```python
seed = received_from_ecu          # 4-byte big-endian
key  = ((seed ^ 0xA53CF069) << 1 | (seed ^ 0xA53CF069) >> 31) & 0xFFFFFFFF
```

---

## 10. DTC Reference Table

| DTC Code | SAE Format | Description | Severity | Fault Counter | Reaction |
|---|---|---|---|---|---|
| P0A0D | High Voltage Battery Cell Voltage High Warning | Cell OV Level 1 | Warning | 2 × 10ms | 20% Derate |
| P0A0E | High Voltage Battery Cell Voltage High Critical | Cell OV Level 2 | Critical | 2 × 10ms | Contactor Open |
| P0A0F | High Voltage Battery Cell Voltage Low | Cell UV | Critical | 2 × 10ms | Contactor Open |
| P0A10 | HV Battery OV Hardware SM Failure | Safety mechanism POST fail | Safety | Immediate | Limp mode |
| P0A1A | High Voltage Battery Temperature High Warning | OT Level 1 | Warning | 10 × 10ms | Cooling + 50% Derate |
| P0A1B | High Voltage Battery Temperature High Critical | OT Level 2 | Critical | 5 × 10ms | Contactor Open |
| P0A1C | High Voltage Battery Temperature Sensor | Sensor OC/SC | Diagnostic | Immediate | Assume max temp |
| P0A2D | High Voltage Battery SoC Out of Range | SoC invalid | Diagnostic | 1 × 1s | Limit power |
| P0A3A | High Voltage Battery Contactor Weld | Weld detected | Safety | Immediate | HV isolation |
| P0A3B | High Voltage Battery Precharge Failure | Timeout | Critical | After timeout | HV blocked |
| P1A00 | High Voltage Battery Emergency Overtemp | OT Emergency | Emergency | Immediate | Shutdown |
| P1B00 | High Voltage Battery Isolation Resistance Low Warn | R_iso warning | Warning | 3 × 100ms | Driver lamp |
| P1B01 | High Voltage Battery Isolation Resistance Low Critical | R_iso critical | Critical | 2 × 100ms | 50% charge |
| P1B02 | High Voltage Battery Isolation Resistance Emergency | R_iso emergency | Emergency | Immediate | HV Off |
| P1C00 | High Voltage Battery CAN Communication Timeout | VCU timeout | Diagnostic | 3 × 100ms | Limp mode |
| P1D00 | High Voltage Battery IMD Self-Test Failure | IMD POST fail | Safety | Immediate | Limp mode |

### DTC Status Byte Meaning (ISO 14229)

| Bit | Name | Description |
|---|---|---|
| 0 | testFailed | Test failed in current drive cycle |
| 3 | confirmedDTC | Failed at least twice |
| 4 | testNotCompletedSinceLastClear | Not yet tested after clear |
| 5 | testFailedSinceLastClear | Failed since last clear |
| 6 | testNotCompletedThisMonitoringCycle | Not yet exercised this cycle |
| 7 | warningIndicatorRequested | MIL / warning lamp requested |

---

## 11. ISO Standards Reference

| Standard | Scope | BMS Relevance |
|---|---|---|
| **ISO 26262** | Functional Safety (ASIL A-D) | BMS ASIL B: OV protection, contactor control |
| **ISO 6469-3** | Safety of EVs — Electrical requirements | Isolation resistance ≥ 500 Ω/V |
| **ISO 14229** | UDS (Unified Diagnostic Services) | Diagnostics, DTC, programming |
| **ISO 15765-2** | CAN ISOTP | UDS transport layer |
| **IEC 62619** | Safety requirements for Li cells | Cell qualification, abuse testing |
| **UN Regulation R100** | EV safety | HV isolation, protection against shock |
| **UNECE R134** | Hydrogen & Fuel Cell (reference) | — |
| **SAE J1939** | Heavy truck CAN protocol | Some commercial EV BMS use J1939 |
| **CHAdeMO / CCS** | DC charging protocols | BMS communication with DC charger |

### ISO 26262 BMS ASIL Assignment (Typical)

| Function | ASIL | Reason |
|---|---|---|
| Over-voltage protection (HW path) | ASIL B | Fire risk |
| Over-voltage protection (SW path) | ASIL B | Fire risk |
| Isolation monitoring | ASIL B | Electric shock risk |
| Contactor control (open on fault) | ASIL B | Fire / shock risk |
| SoC estimation | QM | No safety-critical direct harm |
| Cell balancing | QM | Secondary effect |
| CAN communication | QM | Degraded mode acceptable |

---

## 12. Test Coverage Matrix

| Function | Unit Test | Integration Test | HIL Test | EOL Test |
|---|---|---|---|---|
| Cell OV detection | ✓ | ✓ | ✓ | — |
| Cell UV detection | ✓ | ✓ | ✓ | — |
| Temperature protection | ✓ | ✓ | ✓ | — |
| SoC accuracy | ✓ | ✓ | ✓ | ✓ |
| SoH calculation | ✓ | — | ✓ | — |
| Passive balancing | ✓ | ✓ | ✓ | — |
| Active balancing | ✓ | ✓ | ✓ | — |
| Precharge sequence | ✓ | ✓ | ✓ | ✓ |
| Contactor weld detection | ✓ | ✓ | ✓ | ✓ |
| Emergency HV off | ✓ | ✓ | ✓ | — |
| Isolation monitoring | ✓ | ✓ | ✓ | ✓ |
| UDS ReadDID | — | ✓ | ✓ | — |
| UDS WriteDID | — | ✓ | ✓ | ✓ |
| DTC storage & read | ✓ | ✓ | ✓ | — |
| EOL sequence | — | — | ✓ | ✓ |
| Safety mechanism POST | ✓ | ✓ | ✓ | — |
| CAN signal timing | — | ✓ | ✓ | — |
| Thermal management | ✓ | ✓ | ✓ | — |

---

## 13. Interview Q&A — BMS Deep Dive

**Q: What is the difference between SoC and SoH?**

SoC is *how full the battery is right now* (0–100%), updated continuously.
SoH is *how healthy the battery is compared to new* — measured by comparing current max capacity to the original rated capacity. When SoH drops below 80%, the pack is at EoL.

---

**Q: Why is ISOTP needed for UDS on CAN?**

Standard CAN frames carry max 8 bytes. UDS responses (e.g. reading 96 cell voltages) can be 200+ bytes. ISO 15765-2 (ISOTP) handles multi-frame segmentation and reassembly: First Frame, Consecutive Frames, and Flow Control.

---

**Q: What happens if the precharge resistor fails open?**

- Precharge contactor closes but V_dclink never rises
- Precharge timeout fires after 2 s
- DTC P0A3B logged
- Main+ contactor never closes
- Vehicle cannot enter HV_READY

---

**Q: Why does cell balancing pause above 0.5C discharge?**

Passive balancing dissipates energy as heat *inside* the bleed resistor, which is physically close to the cell. At high discharge rates, cells are already warm. Adding balancing heat could push temperatures above OT1/OT2 thresholds. Balancing is therefore suspended when pack current exceeds a safe threshold.

---

**Q: Describe the EKF correction step in SoC estimation.**

The EKF uses the measured terminal voltage as an observation. By comparing V_measured to V_predicted (from the battery equivalent circuit model at the predicted SoC), the EKF computes a correction: `ΔSoC = K × (V_meas - V_predicted)`. The Kalman gain K weights how much to trust the measurement vs. the prediction, based on their respective noise variances.

---

**Q: What is debounce in fault detection and why is it needed?**

Debounce requires a fault condition to persist for N consecutive scan cycles before triggering a fault reaction. Without debounce, momentary sensor noise, transient voltage spikes during switching, or measurement quantization errors would cause spurious shutdowns. For OV2, 2 consecutive 10 ms samples (20 ms) is typical.

---

**Q: How does UDS Security Access protect BMS write operations?**

1. Tester opens extended session
2. Tester sends 0x27 0x01 (request seed)
3. ECU generates a random seed and sends it
4. Tester applies secret algorithm (XOR + rotate, or CMAC)
5. Tester sends 0x27 0x02 + computed key
6. ECU verifies key — if correct, unlocks write access for the session
7. If key wrong 3 times, ECU locks for a delay period (anti-brute-force)

---

**Q: What is the minimum isolation resistance for a 400V EV pack per ISO 6469-3?**

$$R_{iso,min} = 500 \, \Omega/V \times 400 \, V = 200 \, k\Omega$$

---

**Q: What is ASIL B and how does it apply to BMS?**

ASIL (Automotive Safety Integrity Level) B is the second most stringent level. For BMS:
- Hardware OV safety mechanism must have ≥ 90% Diagnostic Coverage (DC)
- Two independent protection paths required (SW + HW comparator)
- POST (Power-On Self-Test) required to test the HW path at every startup
- Single-point fault metric (SPFM) ≥ 90%

---

*Document Version: 1.0 | BMS Validation Team | 2026-04-19*
