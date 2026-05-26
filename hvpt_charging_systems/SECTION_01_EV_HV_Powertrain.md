# SECTION 1 — EV HIGH VOLTAGE POWERTRAIN FUNDAMENTALS
## Complete Theory, Architecture & System Integration Guide

---

## 1.1 EV ARCHITECTURE OVERVIEW

### 1.1.1 What is an Electric Vehicle?

An Electric Vehicle (EV) replaces the Internal Combustion Engine (ICE) with an electric drive system. Power is stored electrochemically in a High Voltage (HV) battery pack and converted to mechanical motion via an inverter and electric motor.

### 1.1.2 EV System Architecture Diagram (Text Representation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EV HIGH VOLTAGE POWERTRAIN                        │
│                                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │  HV      │    │ Inverter │    │  Traction│    │   Reduction  │  │
│  │ Battery  │───▶│  (PE)    │───▶│  Motor   │───▶│    Gear /    │  │
│  │  Pack    │    │          │    │  (EM)    │    │  Drivetrain  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────┘  │
│       │                │                                              │
│       │          ┌──────────┐                                        │
│       │          │  DC-DC   │───▶ 12V LV Battery / LV Bus           │
│       │          │ Converter│                                        │
│       │          └──────────┘                                        │
│       │                                                               │
│  ┌────▼─────┐    ┌──────────┐    ┌──────────┐                       │
│  │  BMS     │    │   OBC    │    │  PDU     │                       │
│  │ (Battery │    │ (On-Board│    │ (Power   │                       │
│  │  Mgmt)   │    │ Charger) │    │  Distrib)│                       │
│  └──────────┘    └──────────┘    └──────────┘                       │
│                                                                       │
│  CONTROL NETWORK (CAN/LIN/ETHERNET):                                 │
│  VCU ◄──► BMS ◄──► MCU ◄──► Inverter ◄──► OBC ◄──► EVSE           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.1.3 HV Powertrain ECU Network

| ECU | Full Name | Primary Function |
|-----|-----------|-----------------|
| VCU | Vehicle Control Unit | Master controller, torque requests, mode management |
| BMS | Battery Management System | Cell monitoring, SoC/SoH, protection, balancing |
| MCU | Motor Control Unit | Vector control, torque/speed regulation |
| OBC | On-Board Charger | AC→DC conversion for AC charging |
| DC-DC | DC-DC Converter Controller | HV to 12V step-down conversion |
| PDU | Power Distribution Unit | HV bus switching, precharge, contactors |
| TCU | Thermal Control Unit | Battery and motor thermal management |
| EVCC | EV Communication Controller | ISO 15118 charging communication |
| GW | Gateway | Network routing, signal bridging |

---

## 1.2 HV BATTERY SYSTEM

### 1.2.1 Battery Pack Architecture

```
HV Battery Pack
├── Module 1 (e.g., 12 cells in series × 2 parallel = 12S2P)
│   ├── Cell 1.1, Cell 1.2 (parallel pair)
│   ├── Cell 2.1, Cell 2.2
│   └── ...
├── Module 2
├── Module N
├── BMS (Main)
│   ├── Cell Voltage Monitoring ICs (e.g., TI BQ79606)
│   ├── Temperature Sensors (NTC thermistors)
│   ├── Current Sensor (Hall effect / shunt)
│   └── Isolation Monitor
├── Main Positive Contactor (HV+)
├── Main Negative Contactor (HV-)
├── Precharge Contactor + Resistor
├── Manual Service Disconnect (MSD)
└── HV Connector (CCS / CHAdeMO / GB/T)
```

### 1.2.2 Battery Pack Specifications (Typical EV)

| Parameter | Value Range |
|-----------|-------------|
| Nominal Voltage | 300V – 800V |
| Capacity | 40 kWh – 120 kWh |
| Cell Chemistry | NMC, LFP, NCA |
| Cell Voltage (nominal) | 3.2V (LFP) / 3.6V (NMC) |
| Pack Voltage (max) | 4.2V × N_series |
| Max Continuous Current | 200A – 600A |
| Peak Current (30s) | 500A – 1200A |
| Operating Temperature | −20°C to +55°C |
| BMS Communication | CAN 2.0B, CAN FD |

### 1.2.3 Cell Chemistries Compared

| Property | NMC | LFP | NCA |
|----------|-----|-----|-----|
| Energy Density | High | Medium | Very High |
| Cycle Life | 1000–2000 | 2000–6000 | 500–1500 |
| Thermal Stability | Medium | Excellent | Low |
| Cost | Medium | Low | High |
| Applications | Most EVs | Budget EVs, trucks | High-perf EVs |

### 1.2.4 State of Charge (SoC) Calculation Methods

**Method 1 — Coulomb Counting:**
$$SoC(t) = SoC(t_0) - \frac{1}{Q_{nom}} \int_{t_0}^{t} I(\tau) d\tau$$

Where:
- $Q_{nom}$ = nominal battery capacity (Ah)
- $I(\tau)$ = current (positive = discharge, negative = charge)

**Method 2 — OCV (Open Circuit Voltage) Lookup:**
- SoC estimated from Open Circuit Voltage vs SoC curve (OCV-SoC curve)
- Accurate at rest, inaccurate during load

**Method 3 — Kalman Filter (Extended/Unscented):**
- Combines model prediction with measurement correction
- Most accurate — used in OEM BMS systems

### 1.2.5 State of Health (SoH) Calculation

$$SoH = \frac{Q_{current}}{Q_{original}} \times 100\%$$

SoH < 80% → End of automotive life (second-life or recycling threshold)

### 1.2.6 BMS Protection Functions

| Function | Threshold Example | Reaction |
|----------|-------------------|----------|
| Overvoltage Cell | > 4.25V | Open contactors, DTC set |
| Undervoltage Cell | < 2.8V | Open contactors, DTC set |
| Overcurrent Charge | > C/2 rate | Derate, then disconnect |
| Overcurrent Discharge | > 3C rate | Derate, then disconnect |
| Overtemperature | > 55°C | Derate, cooling activation |
| Undertemperature | < −10°C | Charge inhibit |
| Isolation Fault | < 100 Ω/V | Disconnect, warning lamp |

---

## 1.3 BATTERY MANAGEMENT SYSTEM (BMS)

### 1.3.1 BMS Architecture

```
┌─────────────────────────────────────────────────────┐
│                    BMS ARCHITECTURE                  │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              BMS MASTER ECU                  │   │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  │   │
│  │  │  SoC/SoH │  │ Contactor │  │ Thermal  │  │   │
│  │  │Algorithm │  │  Control  │  │  Mgmt    │  │   │
│  │  └──────────┘  └───────────┘  └──────────┘  │   │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  │   │
│  │  │  Safety  │  │ Balancing │  │  CAN/LIN │  │   │
│  │  │  Monitor │  │  Control  │  │  Driver  │  │   │
│  │  └──────────┘  └───────────┘  └──────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│         │ isoSPI / CAN                               │
│  ┌──────▼────────────────────────────────────────┐  │
│  │         CELL MONITORING ICs (CMICs)           │  │
│  │  CMIC_1  CMIC_2  CMIC_3  ...  CMIC_N         │  │
│  │  (each monitors 12–18 cells)                  │  │
│  └───────────────────────────────────────────────┘  │
│         │ Physical connections                        │
│  ┌──────▼───────────────────────────────────────┐   │
│  │         BATTERY CELLS                        │   │
│  │  V_cell1  V_cell2  ...  V_cellN              │   │
│  │  T_sensor1  ...  T_sensorN                   │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 1.3.2 Key BMS CAN Signals

```
Message: BMS_Status (0x310, 10ms cyclic)
├── Signal: BMS_SoC            [0..100%,  resolution 0.5%]
├── Signal: BMS_SoH            [0..100%,  resolution 0.5%]
├── Signal: BMS_PackVoltage    [0..1000V, resolution 0.1V]
├── Signal: BMS_PackCurrent    [−600..600A, resolution 0.1A]
├── Signal: BMS_MaxCellTemp    [−40..120°C, resolution 0.5°C]
├── Signal: BMS_MinCellTemp    [−40..120°C, resolution 0.5°C]
├── Signal: BMS_MaxCellVolt    [0..5000mV, resolution 1mV]
├── Signal: BMS_MinCellVolt    [0..5000mV, resolution 1mV]
├── Signal: BMS_ContactorState [enum: OPEN/PRECHARGE/CLOSED]
├── Signal: BMS_IsolationStatus[enum: OK/WARNING/FAULT]
└── Signal: BMS_FaultCode      [bitmap, 16-bit]

Message: BMS_Limits (0x311, 100ms cyclic)
├── Signal: BMS_MaxChargePower  [0..350kW, resolution 0.1kW]
├── Signal: BMS_MaxDischargePower [0..500kW]
├── Signal: BMS_MaxChargeVoltage [0..1000V]
├── Signal: BMS_MaxChargeCurrent [0..600A]
└── Signal: BMS_TargetVoltage  [0..1000V]
```

### 1.3.3 Contactor Control Sequence

```
PRECHARGE SEQUENCE (Power-On):
─────────────────────────────────────────────────────
Step 1: VCU requests HV_ON
Step 2: BMS checks isolation (IMD measurement)
Step 3: BMS closes Precharge contactor + Negative contactor
Step 4: Precharge resistor limits inrush current
Step 5: BMS monitors DC link voltage rise
Step 6: When V_dclink ≥ 95% × V_battery → Close Main Positive
Step 7: Open Precharge contactor
Step 8: BMS reports CONTACTOR_CLOSED to VCU
Step 9: VCU enables MCU/Inverter

PRECHARGE VOLTAGE PROFILE:
V_dclink(t) = V_batt × (1 - e^(-t/RC))
Where R = precharge resistor, C = inverter capacitance
```

---

## 1.4 INVERTER ARCHITECTURE

### 1.4.1 Inverter Function

The inverter converts DC power from the HV battery to 3-phase AC power for the traction motor. It is the heart of the electric drivetrain.

```
INVERTER INTERNAL ARCHITECTURE:
┌───────────────────────────────────────────────────────────┐
│                      INVERTER                             │
│                                                           │
│  DC Bus (+/-)  ──┐                                       │
│                  │   ┌────────────────────────────────┐  │
│               ┌──▼───▼──┐                              │  │
│               │  DC Link │  C_dclink (e.g. 1500µF)    │  │
│               │Capacitor │                              │  │
│               └──────────┘                              │  │
│                    │                                     │  │
│   ┌────────────────┼────────────────────────────────┐  │  │
│   │     6-IGBT/SiC MOSFET BRIDGE (3-phase)          │  │  │
│   │  ┌──────┐  ┌──────┐  ┌──────┐                  │  │  │
│   │  │ U_Hi │  │ V_Hi │  │ W_Hi │  (Upper switches) │  │  │
│   │  └──────┘  └──────┘  └──────┘                  │  │  │
│   │  ┌──────┐  ┌──────┐  ┌──────┐                  │  │  │
│   │  │ U_Lo │  │ V_Lo │  │ W_Lo │  (Lower switches) │  │  │
│   │  └──────┘  └──────┘  └──────┘                  │  │  │
│   └────────────────────────────────────────────────┘  │  │
│                    │                                     │  │
│          3-phase AC output (U, V, W) → Motor            │  │
│                                                           │
│  GATE DRIVER BOARD ──► PWM signals from MCU              │
│  CURRENT SENSORS (3 × shunt/Hall)                        │
│  TEMPERATURE SENSORS (IGBT/SiC junction)                 │
│  RESOLVER/ENCODER interface (rotor position)             │
└───────────────────────────────────────────────────────────┘
```

### 1.4.2 Vector Control (Field Oriented Control — FOC)

```
FOC CONTROL LOOP:
                    ┌────────────────────────────────────┐
Torque Request ────▶│ Torque-to-Current Mapping (Id, Iq)│
                    └──────────────┬─────────────────────┘
                                   │
             ┌─────────────────────▼──────────────────────┐
             │   Current Controllers (PI — d and q axis)  │
             └─────────────────────┬──────────────────────┘
                                   │
             ┌─────────────────────▼──────────────────────┐
             │   Inverse Park Transform (dq → αβ)         │
             └─────────────────────┬──────────────────────┘
                                   │
             ┌─────────────────────▼──────────────────────┐
             │   Space Vector Modulation (SVM/SVPWM)      │
             └─────────────────────┬──────────────────────┘
                                   │
                              Gate Pulses ──► IGBT/SiC
                                   │
                              Motor Phase Currents
                                   │
             ┌─────────────────────▼──────────────────────┐
             │   Clarke + Park Transform (αβ → dq)        │
             │   + Rotor Position from Resolver/Encoder   │
             └─────────────────────────────────────────────┘
                                   │ (feedback)
                                   └──────────────────────┐
                                                          │
```

### 1.4.3 Key Inverter CAN Signals

```
Message: INV_Status (0x410, 5ms cyclic)
├── INV_ActualTorque     [−500..500 Nm, 0.1 Nm resolution]
├── INV_ActualSpeed      [−20000..20000 RPM, 1 RPM resolution]
├── INV_DCLinkVoltage    [0..1000V, 0.1V resolution]
├── INV_DCLinkCurrent    [−600..600A, 0.1A resolution]
├── INV_PhaseCurrentU    [−1000..1000A, 0.1A]
├── INV_ModuleTemp       [−40..200°C, 0.5°C]
├── INV_MotorTemp        [−40..200°C, 0.5°C]
├── INV_State            [INIT/ENABLE/FAULT/ACTIVE]
└── INV_FaultCode        [16-bit bitmap]

Message: VCU_TorqueRequest (0x100, 5ms cyclic)
├── VCU_TorqueRequest    [−500..500 Nm]
├── VCU_SpeedLimit       [0..20000 RPM]
├── VCU_DriveMode        [ECO/NORMAL/SPORT/REGEN]
└── VCU_EnableDrive      [0=Disable, 1=Enable]
```

---

## 1.5 ELECTRIC TRACTION MOTOR

### 1.5.1 Motor Types in EVs

| Motor Type | Advantages | Disadvantages | Usage |
|-----------|-----------|---------------|-------|
| PMSM (Permanent Magnet Synchronous) | High efficiency, high torque density | Expensive (rare earth magnets) | Most modern EVs |
| IPMSM (Interior PM) | Field weakening capability, robust | Complex control | Tesla, Nissan Leaf |
| Induction Motor (IM) | Low cost, no magnets | Lower efficiency at part load | Tesla Model S (rear) |
| WRSM (Wound Rotor Synchronous) | No rare earth magnets, adjustable flux | Slip rings needed | Renault Zoe |
| SRM (Switched Reluctance) | Very robust, no magnets | High torque ripple, noise | Research stage |

### 1.5.2 Motor Characteristics

```
MOTOR OPERATING REGIONS:
                 Torque (Nm)
                     │
     Max Torque ─────┤████████████████│
                     │                │ ← Constant Power region
                     │                │   (Field Weakening)
                     │                │
                     └────────────────┴──────────── Speed (RPM)
                     0          Base Speed    Max Speed
                          ↑                      ↑
                     Constant Torque        Constant Power
```

### 1.5.3 Motor Parameters (Typical 100kW PMSM)

| Parameter | Value |
|-----------|-------|
| Rated Power | 100 kW |
| Peak Power (30s) | 200 kW |
| Rated Torque | 250 Nm |
| Peak Torque | 500 Nm |
| Max Speed | 15,000 RPM |
| Efficiency (peak) | 97.5% |
| Stator Resistance | 0.012 Ω |
| d-axis Inductance | 0.3 mH |
| q-axis Inductance | 0.6 mH |

---

## 1.6 ON-BOARD CHARGER (OBC)

### 1.6.1 OBC Architecture

```
AC INPUT ──► EMI Filter ──► PFC Stage ──► DC/DC Isolated Stage ──► HV DC OUT
              (passive)   (Boost PFC)   (LLC / Phase-shift FB)

PFC Stage: Converts AC to stable ~400V DC (power factor correction)
DC/DC Stage: Isolated conversion to target battery voltage
                                                                        
OBC CONTROL:
VCU/EVCC ──► CAN ──► OBC Controller ──► Gate Drivers ──► Power Stage
         charging targets
         (V_target, I_limit)
```

### 1.6.2 AC Charging Standards

| Standard | Connector | Max Power | Phases |
|----------|-----------|-----------|--------|
| SAE J1772 Level 1 | J1772 | 1.9 kW | 1-phase |
| SAE J1772 Level 2 | J1772 | 19.2 kW | 1-phase |
| IEC 62196 Type 2 | Mennekes | 22 kW | 3-phase |
| GB/T 20234.2 | Chinese AC | 7.4 kW | 1-phase |

### 1.6.3 OBC CAN Signals

```
Message: OBC_Status (0x620, 100ms)
├── OBC_State        [IDLE/INIT/PRECHARGE/CHARGE/FAULT/DONE]
├── OBC_OutputVoltage [0..1000V, 0.1V]
├── OBC_OutputCurrent [0..100A, 0.1A]
├── OBC_OutputPower  [0..22000W, 1W]
├── OBC_Temperature  [−40..120°C]
├── OBC_Fault        [bitmap]
└── OBC_InputACVoltage [0..300V, 0.1V]

Message: VCU_ChargingControl (0x200, 100ms)
├── VCU_ChargeEnable     [0/1]
├── VCU_TargetVoltage    [0..1000V]
├── VCU_MaxCurrent       [0..100A]
└── VCU_ChargingMode     [AC_L1/AC_L2/AC_L3/DCFC]
```

---

## 1.7 DC-DC CONVERTER

### 1.7.1 Function

Converts HV battery voltage (300–800V) down to 12V–14.5V to:
- Power the 12V LV network
- Charge the 12V auxiliary battery
- Supply all LV ECUs, lights, actuators

### 1.7.2 Key Parameters

| Parameter | Typical Value |
|-----------|-------------|
| Input Voltage | 250–800V HV |
| Output Voltage | 12.5–14.8V |
| Output Current | 50–200A |
| Output Power | 1.5–3.5 kW |
| Efficiency | > 94% |
| Communication | CAN |

### 1.7.3 DC-DC CAN Signals

```
Message: DCDC_Status (0x630, 100ms)
├── DCDC_OutputVoltage [10..16V]
├── DCDC_OutputCurrent [0..200A]
├── DCDC_Temperature   [−40..120°C]
├── DCDC_State         [OFF/STANDBY/ACTIVE/FAULT]
└── DCDC_Fault         [bitmap]
```

---

## 1.8 VEHICLE CONTROL UNIT (VCU)

### 1.8.1 VCU — Master Orchestrator Role

The VCU is the highest-level ECU in the EV powertrain. It:
- Receives driver inputs (accelerator pedal, brake, gear selector)
- Manages vehicle operating states (READY/DRIVE/REGEN/CHARGE/SLEEP)
- Issues torque requests to MCU/Inverter
- Manages HV system power-on/power-off sequences
- Communicates with all powertrain ECUs
- Monitors fault status from all ECUs
- Implements drive modes (ECO/NORMAL/SPORT)
- Controls regenerative braking magnitude

### 1.8.2 VCU State Machine

```
                        ┌─────────┐
                        │  OFF    │◄──── Key Off / HV Fault
                        └────┬────┘
                             │ Key On
                        ┌────▼────┐
                        │ STANDBY │
                        └────┬────┘
                             │ Precharge OK + BMS Ready
                        ┌────▼────┐
                        │  READY  │◄──── Vehicle powered, HV on
                        └────┬────┘
                             │ D/R selected + Throttle
               ┌─────────────┼─────────────┐
          ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
          │  DRIVE  │  │  REGEN  │  │  SPORT  │
          └─────────┘  └─────────┘  └─────────┘
                             │ Charge gun inserted
                        ┌────▼────┐
                        │  CHARGE │
                        └─────────┘
                             │ Emergency / Crash
                        ┌────▼────┐
                        │  CRASH/ │
                        │ FAILSAFE│
                        └─────────┘
```

### 1.8.3 VCU Torque Management

```
TORQUE REQUEST LOGIC:
1. Read Accelerator Pedal Position (APP): 0–100%
2. Apply pedal map: APP → Torque_raw (from characteristic curve)
3. Apply drive mode modifier:
   ECO:    Torque_mod = Torque_raw × 0.70
   NORMAL: Torque_mod = Torque_raw × 1.00
   SPORT:  Torque_mod = Torque_raw × 1.30 (up to motor limit)
4. Apply BMS power limit:
   Torque_limit = (BMS_MaxDischargePower / INV_ActualSpeed) × 9549
5. Final torque = MIN(Torque_mod, Torque_limit, Motor_MaxTorque)
6. Send VCU_TorqueRequest to MCU via CAN
```

---

## 1.9 MOTOR CONTROL UNIT (MCU)

### 1.9.1 MCU Functions

- Receives torque/speed requests from VCU
- Executes Field Oriented Control (FOC) algorithm
- Controls gate drivers for inverter IGBTs/SiC MOSFETs
- Monitors phase currents, rotor position, temperatures
- Implements torque limiters and protection functions
- Implements field weakening for above base-speed operation
- Communicates with VCU, BMS, and inverter hardware

### 1.9.2 MCU CAN Interface

```
MCU receives:
├── VCU_TorqueRequest (0x100, 5ms)
└── BMS_Limits (0x311, 100ms)

MCU transmits:
├── MCU_Status (0x410, 5ms)
│   ├── MCU_ActualTorque
│   ├── MCU_ActualSpeed
│   └── MCU_State
└── MCU_Temperature (0x411, 100ms)
    ├── MCU_InverterTemp
    └── MCU_MotorTemp
```

---

## 1.10 POWER DISTRIBUTION UNIT (PDU)

### 1.10.1 PDU Architecture

```
HV BATTERY (+)
      │
      ├──► Manual Service Disconnect (MSD) — Emergency disconnect
      │
      ├──► Main (+) Contactor ─────────────────────────┐
      │                                                 │
      ├──► Precharge Contactor + Precharge Resistor ───┤
      │                                                 │
      └──► Fuses/Circuit Breakers for each HV load:    │
           ├── Inverter / Motor   ◄──────────────────  │
           ├── OBC                                      │
           ├── DC-DC Converter                         │
           └── HVAC Compressor                         │
                                                        │
HV BATTERY (−) ◄────────────────────────── Main (−) Contactor
```

### 1.10.2 PDU CAN Signals

```
Message: PDU_Status (0x320, 50ms)
├── PDU_MainPosContactorState  [OPEN/CLOSED/FAULT]
├── PDU_MainNegContactorState  [OPEN/CLOSED/FAULT]
├── PDU_PrechargeState         [OPEN/CLOSED/FAULT]
├── PDU_HV_Voltage             [0..1000V]
├── PDU_HV_Current             [−600..600A]
├── PDU_IsolationOK            [0=FAULT, 1=OK]
└── PDU_FuseStatus             [bitmap, per-fuse]
```

---

## 1.11 CHARGING PORT & CHARGING SYSTEM

### 1.11.1 Charging Inlet Types

| Standard | Region | Connector | AC/DC |
|----------|--------|-----------|-------|
| CCS Combo 1 | USA, Korea | SAE J1772 + DC pins | Both |
| CCS Combo 2 | Europe | Mennekes + DC pins | Both |
| CHAdeMO | Japan | Separate DC connector | DC only |
| GB/T 20234 | China | Chinese standard | Both |
| Tesla NACS | USA (now CCS expanding) | NACS | Both |
| MCS | Trucks | Megawatt Charging | DC |

### 1.11.2 AC Charging Sequence (IEC 61851 / SAE J1772)

```
AC CHARGING SEQUENCE:
═══════════════════════════════════════════════════════

1. CABLE PLUG-IN:
   - EVSE detects cable insertion (CP line pull-down)
   - State A (12V on CP) → State B (9V = vehicle connected)

2. EVSE READY SIGNAL:
   - EVSE applies PWM on CP line (1 kHz)
   - PWM duty cycle → available current encoding:
     10% = 6A, 25% = 16A, 50% = 32A, 80% = 63A

3. VEHICLE READY:
   - Vehicle (EVCC) reads CP PWM duty → know max available current
   - Vehicle pulls CP to State C (6V = charging)
   - EVSE energizes AC output

4. CHARGING:
   - OBC converts AC → DC
   - BMS accepts charge current
   - VCU monitors all parameters

5. CHARGE COMPLETE / STOP:
   - BMS reports SoC = 100% or user stops
   - VCU signals OBC to stop
   - CP returns to State B, then A
   - EVSE de-energizes

PROXIMITY PILOT (PP):
- Resistor in cable connector indicates max current rating
- 100Ω = 63A, 220Ω = 32A, 330Ω = 20A, 1.5kΩ = 13A
```

### 1.11.3 DC Fast Charging Sequence (CCS — ISO 15118)

```
DC FAST CHARGING SEQUENCE (CCS Combo):
═══════════════════════════════════════════════════════

1. PHYSICAL CONNECTION:
   - CCS cable inserted (AC + DC + CP + PP pins)
   - CP state transitions (same as AC — State B)

2. HIGH-LEVEL COMMUNICATION (HLC) — ISO 15118:
   [Vehicle ←→ EVSE over PLC (Power Line Communication)]

   EVSE_SpendHello →
   ← Vehicle_SpendHello
   
   TLS Handshake (optional for security) →
   ←
   
   ServiceDiscovery_Req →
   ← ServiceDiscovery_Res (charge services available)
   
   ChargeParameterDiscovery_Req →
   ← ChargeParameterDiscovery_Res
   (EVSE tells vehicle: Max Voltage=1000V, Max Current=500A)
   
   Cable_Check_Req →
   ← Cable_Check_Res (isolation check OK)
   
   PreCharge_Req (target V = battery V) →
   ← PreCharge_Res (EVSE output voltage = battery V)
   
   PowerDelivery_Req (ChargeProgress=START) →
   ← PowerDelivery_Res (EVSE starts charging)

3. ACTIVE CHARGING (CurrentDemand loop):
   Every 250ms:
   CurrentDemand_Req (EV_Target_Voltage, EV_Max_Current) →
   ← CurrentDemand_Res (EVSE_Present_Voltage, EVSE_Present_Current)

4. CHARGE COMPLETE:
   CurrentDemand_Req (charging_complete=TRUE) →
   ← CurrentDemand_Res
   
   PowerDelivery_Req (ChargeProgress=STOP) →
   ← PowerDelivery_Res
   
   WeldingDetection_Req →
   ← WeldingDetection_Res (contactors not welded = OK)
   
   SessionStop_Req →
   ← SessionStop_Res

5. CABLE UNPLUG
```

---

## 1.12 REGENERATIVE BRAKING

### 1.12.1 Regen Braking Concept

```
REGENERATIVE BRAKING POWER FLOW:
────────────────────────────────────────────────────
During deceleration:
  Wheels slow down → Motor acts as GENERATOR
  Mechanical Energy → Electrical Energy (3-phase AC)
  Inverter rectifies AC → DC (motoring control reversed)
  DC current flows back INTO the HV battery
  BMS limits regen current based on SoC and temperature
────────────────────────────────────────────────────

Regen torque = negative torque applied by MCU
VCU calculates regen torque from:
  - Brake pedal position
  - Vehicle speed (regen effectiveness at speed)
  - BMS_MaxChargePower limit
  - Regen mode setting (0-paddles, 1-2-3-max)
```

### 1.12.2 Regen Braking Limits

```
Regen_TorqueLimit = MIN(
    Motor_MaxRegenTorque,           // mechanical limit
    BMS_MaxChargePower / ω_motor,   // battery limit
    Wheel_TractionLimit,            // tire limit (no lock-up)
    Driver_RegenSetting             // user preference
)
```

---

## 1.13 THERMAL MANAGEMENT SYSTEM

### 1.13.1 Thermal Architecture

```
THERMAL MANAGEMENT OVERVIEW:
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ┌──────────┐     ┌────────────┐     ┌────────────┐ │
│  │  Battery │     │  Inverter  │     │   Motor    │ │
│  │  Cooling │     │  Cooling   │     │  Cooling   │ │
│  └────┬─────┘     └─────┬──────┘     └─────┬──────┘ │
│       │                 │                   │        │
│       └────────────┬────┘───────────────────┘        │
│                    │                                  │
│              ┌─────▼──────┐                          │
│              │  Coolant   │                          │
│              │  Pump      │                          │
│              └─────┬──────┘                          │
│                    │                                  │
│              ┌─────▼──────┐                          │
│              │  Radiator  │ ◄── Fan control          │
│              │  + Chiller │                          │
│              └────────────┘                          │
│                                                      │
│  HEAT PUMP (optional in premium EVs):                │
│  - Cabin heating using refrigerant                   │
│  - More efficient than resistive heating             │
└──────────────────────────────────────────────────────┘
```

### 1.13.2 Battery Thermal Strategy

| Battery Temp | Strategy |
|-------------|---------|
| < 0°C | Charge inhibit, pre-heating via PTC or heat pump |
| 0°C – 15°C | Reduced charge rate (Li plating risk) |
| 15°C – 35°C | Normal operation, cooling optional |
| 35°C – 45°C | Active cooling engaged |
| > 45°C | Charge/discharge derating |
| > 55°C | Emergency shutdown |

---

## 1.14 HV SAFETY CONCEPTS

### 1.14.1 Isolation Monitoring Device (IMD)

```
IMD PRINCIPLE:
The IMD continuously measures the insulation resistance between:
- HV+ and chassis ground
- HV− and chassis ground

Normal Operation: R_isolation > 100 Ω/V_nominal
  Example: 400V system → R_iso > 40 kΩ

Fault Condition: R_isolation < threshold
  → IMD triggers warning (yellow) at 100–500 Ω/V
  → IMD triggers fault (red, disconnect) at < 100 Ω/V

IMD uses measurement injection method:
  Injects low-level AC/DC test signal on HV bus
  Measures return current through chassis
  Calculates R_isolation = V_test / I_return
```

### 1.14.2 HV Interlock System

```
HV INTERLOCK LOOP:
─────────────────────────────────────────────────────
All HV connectors are wired in series in an interlock loop:
  PDU_Interlock ──► Inverter_Interlock ──► Motor_Interlock
  ──► OBC_Interlock ──► DCDC_Interlock ──► BMS_Interlock
                                                    │
                                             12V return
─────────────────────────────────────────────────────
If any connector is removed/opened:
  → Loop resistance changes
  → BCM/VCU detects open loop
  → Immediately opens main contactors
  → Prevents HV exposure
```

### 1.14.3 Manual Service Disconnect (MSD)

- Physical plug that breaks the battery mid-point
- Reduces effective voltage by half (e.g., 800V → 400V) during service
- Location: Typically accessible from trunk/underbody
- Orange color coding (universal HV identifier)

### 1.14.4 HV Wiring Color Code

| Color | Meaning |
|-------|---------|
| Orange | HV cables (universal automotive) |
| Blue | Coolant/thermal |
| Green | Low-voltage ground |
| Red | Low-voltage positive |
| Yellow | Caution markers |

---

## 1.15 FAULT HANDLING & DIAGNOSTIC TROUBLE CODES (DTCs)

### 1.15.1 Fault Severity Levels

| Level | Name | Action |
|-------|------|--------|
| 0 | Info | Log only |
| 1 | Warning | MIL lamp, reduce performance |
| 2 | Recoverable | Power reduction, continue degraded |
| 3 | Non-recoverable | Shut down component, limp mode |
| 4 | Safety Critical | Immediate HV shutdown, stop vehicle |

### 1.15.2 Example DTCs — EV Powertrain

| DTC Code | Description | Severity | Action |
|---------|-------------|---------|--------|
| P0A00 | Motor Control Module Fault | Level 3 | MCU shutdown |
| P0A0F | Motor Overtemperature | Level 3 | Derate, then shutdown |
| P0A80 | Battery Capacity Degradation | Level 2 | Warning lamp |
| P0AE0 | Isolation Fault — HV Bus | Level 4 | Immediate contactors open |
| P0AF0 | Battery Contactor Fault | Level 4 | Emergency shutdown |
| P1E00 | Charging Communication Fault | Level 2 | Charging stop |
| P0C00 | HV Interlock Fault | Level 4 | Contactors open |

### 1.15.3 Fault Flow Architecture

```
ECU detects fault condition
        │
        ▼
Fault confirmed after debounce (e.g., 3 consecutive cycles, 50ms)
        │
        ▼
DTC stored in fault memory (Non-Volatile)
        │
        ▼
Fault reported via CAN signal (FaultCode bitmap)
        │
        ▼
VCU receives fault ──► Determines reaction level
        │
        ├── Level 1: Set MIL lamp
        ├── Level 2: Derate torque/power
        ├── Level 3: Shutdown subsystem
        └── Level 4: Open contactors + safe state
```

---

## 1.16 VEHICLE POWER MANAGEMENT STATES

### 1.16.1 Power State Machine

```
VEHICLE POWER STATES:
──────────────────────────────────────────────────────────
STATE       │ HV Status │ 12V   │ ECUs Active       │ Notes
──────────────────────────────────────────────────────────
DEEP_SLEEP  │ OFF        │ OFF   │ None (only wake   │ Max power save
            │           │       │ detector ICs)     │
──────────────────────────────────────────────────────────
SLEEP       │ OFF        │ Standby│ BCM, Wakeup ECUs │ Key out, locked
──────────────────────────────────────────────────────────
ACCESSORY   │ OFF        │ ON    │ BCM, IVI, BMS     │ Key Acc position
──────────────────────────────────────────────────────────
IGNITION_ON │ Precharging│ ON   │ All ECUs          │ Key On (not start)
──────────────────────────────────────────────────────────
READY       │ ON, HV+    │ ON    │ All + Drive-ready │ Ready to drive
──────────────────────────────────────────────────────────
DRIVE       │ ON         │ ON    │ All               │ Driving
──────────────────────────────────────────────────────────
CHARGING    │ ON (charge)│ ON    │ BMS, OBC, VCU     │ Plugged in
──────────────────────────────────────────────────────────
FAULT       │ OFF/Limited│ ON    │ Safety ECUs       │ Degraded
──────────────────────────────────────────────────────────
```

### 1.16.2 Wakeup Hierarchy

```
WAKEUP TRIGGERS:
Physical:  Key insertion / Smart key proximity → BCM wakeup
CAN:       BCM sends wakeup frame to all ECUs on CAN bus
KL.15:     Ignition line triggers hardware wakeup
Remote:    Telematics module → schedules charging/preconditioning
Timer:     User-programmed departure time → pre-conditioning
```

---

## 1.17 ENERGY FLOW ARCHITECTURE

### 1.17.1 Energy Flow Diagram

```
ENERGY FLOW — DRIVING MODE:
═══════════════════════════════════════════════════════════

Battery ──(DC HV)──► PDU ──(DC HV)──► Inverter ──(3-phase AC)──► Motor ──► Wheels

                                  │
                            (DC HV)
                                  │
                             DC-DC Converter ──(12V DC)──► LV Bus ──► ECUs, Lights
                                  │
                             HVAC Compressor (HV driven)

ENERGY FLOW — REGENERATION MODE:

Wheels ──(decelerating)──► Motor ──(3-phase AC generated)──► Inverter ──(DC)──► Battery

ENERGY FLOW — AC CHARGING:

Grid AC ──► EVSE/Wallbox ──► Charging Cable ──► OBC ──(DC)──► PDU ──► Battery
                                                       │
                                               DC-DC active ──► LV Bus

ENERGY FLOW — DC FAST CHARGING:

Grid AC ──► External Charger ──► DC ──► Charging Cable ──► PDU ──► Battery
                                              (bypasses OBC)
```

---

## SECTION 1 SUMMARY

| System | Key Function | Primary CAN Message |
|--------|-------------|---------------------|
| HV Battery + BMS | Energy storage, protection | BMS_Status (0x310) |
| Inverter + MCU | DC→AC conversion, motor control | INV_Status (0x410) |
| Electric Motor | Converts electrical to mechanical | (via Inverter) |
| OBC | AC charging conversion | OBC_Status (0x620) |
| DC-DC Converter | HV to 12V supply | DCDC_Status (0x630) |
| VCU | Master orchestrator | VCU_TorqueRequest (0x100) |
| PDU | HV switching, safety | PDU_Status (0x320) |
| Thermal System | Temperature management | TCU_Status (0x510) |

---

*Next: Section 2 — Automotive Systems Engineering Process*
