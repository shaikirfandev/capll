# BYD Sealion 7 — Hardware Architecture
## ECUs | Sensors | Compute | Battery | Power Electronics

---

## 1. Major ECU Inventory

### Powertrain Domain

| ECU | Full Name | Key Functions | Protocol |
|-----|-----------|---------------|----------|
| **VCU** | Vehicle Control Unit | Torque arbitration, drive mode, regeneration, energy management | CAN FD (master) |
| **BMS** | Battery Management System | Cell monitoring, SOC/SOH, thermal management, contactor control | CAN FD |
| **MCU-F** | Motor Controller Unit (Front) | 3-phase PWM inverter, torque control, field weakening | CAN FD |
| **MCU-R** | Motor Controller Unit (Rear) | AWD torque distribution, traction control | CAN FD |
| **OBC** | On-Board Charger | AC→DC rectification, CC/CV charging | CAN FD |
| **DC-DC** | DC-DC Converter | HV→12V (typically 14V, ~3–3.5 kW) | CAN |

### 8-in-1 Module Integration (e-Platform 3.0)

BYD integrates the following into one mechanical assembly:
```
┌──────────────────────────────────────────────┐
│             8-in-1 Power Assembly            │
│  Motor | MCU | Reducer | PDU | DC-DC |       │
│  OBC | VCU | BMS (battery side interface)    │
└──────────────────────────────────────────────┘
```
Advantages: reduced wiring harness length, lower system weight (~30% mass reduction vs individual units), shared coolant circuit.

### Chassis Domain

| ECU | Function | ASIL | Protocol |
|-----|----------|------|----------|
| **ESP/ESC** | Electronic Stability Control + ABS | ASIL C | CAN FD |
| **EPS** | Electric Power Steering (torque overlay for LKA) | ASIL D | CAN FD |
| **EPB** | Electronic Parking Brake | ASIL B | CAN |
| **iBooster / BBW** | Brake-by-Wire (blended regen/friction brake) | ASIL D | CAN FD |

> **iBooster importance:** Brake-by-wire decouples pedal from caliper — enables smooth regenerative braking blend without pedal pulsation. Safety-critical: dual-channel redundancy, ASIL D.

### ADAS Domain

| ECU | Function | Compute | Protocol |
|-----|----------|---------|----------|
| **DiPilot DCU** | ADAS Domain Controller (perception + planning + control) | Multi-core SoC + AI accelerator | Ethernet 1000BASE-T1 |
| **Front Radar ECU** | Front long-range radar processing | Integrated DSP | Ethernet |
| **Corner Radar ECUs ×4** | Blind spot / cross-traffic radar | Integrated DSP | Ethernet / CAN FD |
| **Camera ISP ECUs** | Image signal processing (may be integrated into DCU) | FPGA/ISP | MIPI CSI-2 / Ethernet |

### Body Domain

| ECU | Function | Protocol |
|-----|----------|----------|
| **BCM** | Central body control (lighting, windows, doors, CAN master to LIN slaves) | CAN + LIN master |
| **PEPS** | Passive Entry / Passive Start (BLE key fob, NFC) | CAN + BLE radio |
| **HVAC** | Climate control, heat pump coordination | CAN |
| **SRS** | Airbag ECU (crash sensing, pyro fire) | CAN |

### Infotainment / HMI Domain

| ECU | Function | Protocol |
|-----|----------|----------|
| **DiLink Head Unit** | Central infotainment head unit (Android-based) | Ethernet, USB 3.0, CAN |
| **Instrument Cluster ECU** | Digital cluster rendering | Ethernet / CAN |
| **TCU** | Telematics Control Unit (4G LTE, WiFi, Bluetooth) | Ethernet to GW, 4G to cloud |
| **V2X Unit** (market dependent) | Vehicle-to-Infrastructure communication | DSRC / C-V2X |

---

## 2. Sensor Suite

### ADAS Sensors

| Sensor | Qty | Technology | Range | Field of View | Use |
|--------|-----|-----------|-------|---------------|-----|
| Front long-range radar | 1 | 77 GHz FMCW | 200+ m | 20° | ACC, AEB |
| Corner/short-range radar | 4 | 77 GHz FMCW | 80 m | 150° | BSD, RCTA, FCTA |
| Front wide-angle camera | 1 | CMOS, 8 MP | 150 m | 120° | Lane detection, signs, AEB |
| Front narrow camera | 1 | CMOS | 200 m | 30° | Long-range forward object |
| Rear camera | 1 | CMOS, 5 MP | 15 m | 130° | Reverse assist, parking |
| Side cameras ×2 | 2 | CMOS | 10 m | 180° | Surround view, lane change |
| Ultrasonic sensors | 12 | Piezoelectric, 40 kHz | 5 m | Hemispherical | Parking, APA |

**Note:** Higher-end DiPilot+ variants may include LiDAR (supplier: Hesai / RoboSense) for city-driving autonomy. Base Sealion 7 uses camera + radar only.

### Non-ADAS Sensors

| Sensor | Function |
|--------|----------|
| IMU (Inertial Measurement Unit) | 6-DOF acceleration + gyroscope for stability control, sensor fusion |
| GNSS (GPS + BeiDou + GLONASS) | Positioning for navigation and ADAS HD-map correlation |
| Wheel speed sensors ×4 | ABS, traction control, vehicle speed |
| Steering angle sensor | EPS, ESC reference |
| Yaw rate sensor | ESP, ADAS lane-keeping |
| Battery temperature sensors (~100 pt) | BMS thermal monitoring per cell group |
| Isolation monitoring sensor | HV ground fault detection |
| Pressure sensors (TPMS) ×4 | Tire pressure monitoring |

---

## 3. Compute Hardware

### DiPilot Domain Controller (ADAS DCU)

| Component | Specification |
|-----------|---------------|
| Main SoC | Multi-core ARM Cortex-A + AI NPU (estimated: BYD-customized or Horizon Robotics Journey 5 / NVIDIA Orin class) |
| AI performance | ~50–128 TOPS (variant dependent) |
| Memory | LPDDR5 8–16 GB |
| Storage | eMMC 5.1 / UFS 3.1, 32-64 GB |
| OS | Linux / QNX on safety partition |
| GPU | Integrated in SoC for perception rendering |
| Functional safety | ISO 26262 ASIL B/D partitioning |

### Head Unit (DiLink)

| Component | Specification |
|-----------|---------------|
| SoC | Qualcomm Snapdragon 8155 (automotive grade) |
| CPU | Octa-core Kryo 585, up to 2.84 GHz |
| GPU | Adreno 640 |
| RAM | 8 GB LPDDR5 |
| Storage | 128 GB UFS 2.1 |
| OS | Android Automotive OS (BYD DiLink customization) |

### Cluster ECU

| Component | Specification |
|-----------|---------------|
| SoC | NXP i.MX 8 or similar |
| Display driver | GPU-driven digital instrument cluster |
| OS | Linux / AUTOSAR Adaptive |

---

## 4. Battery Technology — Blade Battery

### Cell Chemistry

| Attribute | Value |
|-----------|-------|
| Chemistry | **LFP (Lithium Iron Phosphate)** — LiFeO₄ |
| Cell format | **Blade cell** — ultra-thin prismatic (long rectangular) |
| Cell arrangement | Cell-to-Pack (CTP) — no module casing |
| Capacity (Sealion 7 LR) | ~82.56 kWh usable |
| Nominal voltage | ~3.2 V/cell |
| Energy density | ~150 Wh/kg (pack level, improved vs conventional LFP) |
| Cycle life | >3000 cycles to 80% SOH |

### Why Blade Battery?

```
Traditional LFP:        Blade Battery:

[Cell] → [Module] →     [Blade Cell — directly spans pack width]
         [Pack]         [Cell IS the structural element]
                        [No module casing = +20% energy density]
```

**Safety advantage — Nail penetration test:**
- Conventional NMC: Surface temp → 500°C (thermal runaway)
- Blade LFP: Surface temp → < 60°C (no thermal runaway)

### BMS Architecture

```
Cell stack (100S × nP configuration for ~82 kWh)
     │
  [Cell Supervision Circuits (CSC) — one per group]
     │ SPI/CAN
  [BMS Master ECU]
     │ CAN FD
  [VCU] ←→ [Contactor control] ←→ [HV bus]

BMS functions:
- Voltage monitoring per cell (resolution: 1 mV)
- Temperature monitoring per group (NTC sensors)
- SOC estimation (Kalman filter + ampere-hour integration)
- SOH estimation (capacity fade tracking)
- Cell balancing (passive, up to 100 mA)
- Contactor pre-charge logic
- SPI communication to CSCs
- Thermal management coordination with PTC / heat pump
```

---

## 5. Power Electronics

### Motor Specifications

| Variant | Front Motor | Rear Motor | Combined |
|---------|-------------|-----------|---------|
| RWD | — | 230 kW, 360 Nm | 230 kW |
| AWD | 160 kW, 310 Nm | 230 kW, 360 Nm | 390 kW |
| Motor type | **PMSM** (Permanent Magnet Synchronous Motor) | PMSM | — |

**PMSM advantages:**
- High torque density
- Efficient field weakening for high speed
- Precise torque response (< 10 ms) via FOC (Field-Oriented Control)

### Inverter

| Parameter | Value |
|-----------|-------|
| Topology | 3-phase IGBT / SiC MOSFET bridge |
| Switching frequency | 10–20 kHz (SiC enables higher) |
| Current | Up to 600+ Arms |
| Control algorithm | FOC (Field-Oriented Control) with MTPA (Maximum Torque Per Ampere) |
| Efficiency | > 97% peak |

**SiC (Silicon Carbide) advantage in BYD's newer platforms:**
- Lower switching losses → better efficiency at high temperature
- 3× faster switching than IGBT → smaller filter inductors
- Enables 800V architecture energy

### On-Board Charger (OBC)

| Parameter | Value |
|-----------|-------|
| AC input | Single-phase or 3-phase (market dependent) |
| AC charging power | Up to 11 kW (3-phase) |
| DC fast charge | CCS2 / CHAdeMO / GB/T, up to 150 kW |
| Efficiency | ~94% AC→DC |
| Isolation | Galvanic isolation (transformer-based topology) |

### DC-DC Converter

| Parameter | Value |
|-----------|-------|
| Input | HV bus (300–450 V) |
| Output | 12–14.5 V LV bus |
| Power | 3–3.5 kW continuous |
| Topology | Isolated full-bridge DC-DC |

### Thermal Management System

```
Coolant loop architecture:
┌──────── Battery thermal loop ──────────────────────┐
│  Battery pack ←→ Chiller/PTC ←→ Heat pump          │
└────────────────────────────────────────────────────┘

┌──────── Motor/Electronics thermal loop ─────────────┐
│  Motor + Inverter + OBC ←→ Radiator (front)         │
└─────────────────────────────────────────────────────┘

Heat Pump system:
- Refrigerant loop drives both cabin heating and battery pre-conditioning
- COP (Coefficient of Performance) > 2 at 0°C → 50%+ better than PTC alone
- Battery pre-conditioning: BMS requests heat when fast charge is scheduled

Operating temperature limits:
  Battery optimal: 15–35°C
  Battery max: 60°C (BMS cutback above 45°C)
  Motor: -40°C to +150°C (with derating above 120°C)
```
