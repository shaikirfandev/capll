# BYD Sealion 7 — Vehicle Architecture Overview
## Platform | E/E Architecture | Communication Protocols

---

## 1. Platform Overview

### e-Platform 3.0

The BYD Sealion 7 is built on **BYD e-Platform 3.0**, BYD's third-generation purpose-built EV architecture announced in January 2021.

| Attribute | Specification |
|-----------|---------------|
| Platform | BYD e-Platform 3.0 |
| Architecture type | Skateboard chassis (flat floor) |
| Battery integration | Cell-to-Pack (CTP) — Blade Battery |
| Powertrain | Front, Rear, or AWD motor configurations |
| Voltage architecture | **800V capable** high-voltage system (nominal ~400V on base variants) |
| Charging | AC Type 2 up to 11 kW + DC CCS2 up to 150 kW |

**Chassis architecture:**
- Skateboard platform: battery pack integrated as structural element of floor
- High-strength steel + aluminum alloy mixed body structure
- Multi-link independent rear suspension; MacPherson strut front
- Front crash structure integrates battery protection beams

**Key e-Platform 3.0 innovations:**
1. **8-in-1 powertrain module** — motor, motor controller (inverter), reducer, PDU, DC-DC, OBC, VCU, BMS integrated
2. **Blade Battery as structural member** — increases torsional rigidity, eliminates battery module casing
3. **High-voltage architecture** — reduces cable weight, enables faster charging

---

## 2. E/E Architecture

### Domain-Based Architecture

The BYD Sealion 7 uses a **Domain-Based E/E architecture** (transitioning elements of Zonal).

```
┌─────────────────────────────────────────────────────────┐
│                    DOMAIN CONTROLLER                    │
│                   (Central Gateway ECU)                 │
└──────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │
  ┌────┴──┐  ┌───┴───┐  ┌───┴───┐  ┌───┴──────────────┐
  │ADAS   │  │Power- │  │Body   │  │Infotainment      │
  │Domain │  │train  │  │Domain │  │Domain            │
  │Controller│Domain │  │Controller│  │Controller        │
  └────┬──┘  └───┬───┘  └───┬───┘  └───┬──────────────┘
       │          │          │          │
  Cameras    VCU/BMS/MCU  Body ECUs  Head Unit
  Radar       Inverter    Doors/Lights  Cluster
  Ultrasonic  Thermal     HVAC        TCU
```

**Domain breakdown:**

| Domain | Responsible ECU | Protocols used |
|--------|----------------|----------------|
| ADAS / Active Safety | ADAS Domain Controller | Ethernet 100BASE-T1, CAN FD |
| Powertrain | VCU (Vehicle Control Unit) | CAN FD, Isolated CAN |
| Body/Comfort | Body Control Module (BCM) | CAN, LIN |
| Infotainment/HMI | Central Head Unit | Ethernet, LVDS, CAN |
| Chassis | EPS ECU, ABS/ESP ECU | CAN FD |
| Connectivity | TCU (Telematics Control Unit) | 4G LTE, Ethernet to GW |

---

## 3. Communication Protocol Stack

```
┌──────────────────────────────────────────────────────────┐
│           Application Layer (UDS, SOME/IP, XCP)          │
├──────────────────────────────────────────────────────────┤
│           Transport Layer (ISO 15765-2, UDP/TCP)         │
├──────────────────────────────────────────────────────────┤
│      Network Layer (IPv4/IPv6 for Ethernet nodes)        │
├──────────────────────────────────────────────────────────┤
│   Data Link: CAN FD | CAN 2.0B | LIN 2.2A | 100BASE-T1  │
├──────────────────────────────────────────────────────────┤
│         Physical Layer (ISO 11898, BroadR-Reach)         │
└──────────────────────────────────────────────────────────┘
```

### Protocol Usage by Domain

| Protocol | Speed | Where Used |
|----------|-------|------------|
| **CAN 2.0B** | 500 kbit/s | Body, LIN master, legacy sensors |
| **CAN FD** | 2–5 Mbit/s | Powertrain (VCU↔BMS↔MCU), chassis (ESP↔EPS↔ABS) |
| **LIN 2.2A** | 19.2 kbit/s | Seat control, mirrors, window lift, interior lighting |
| **100BASE-T1 Ethernet** | 100 Mbit/s | ADAS sensor data, camera streams (compressed) |
| **1000BASE-T1 Ethernet** | 1 Gbit/s | ADAS domain controller internal, infotainment backbone |
| **USB 3.0** | 5 Gbit/s | OTA update, map data loading, Android head unit peripherals |

### CAN FD vs CAN — Why BYD chose CAN FD for powertrain:
- BMS ↔ VCU requires high-rate cell data (100+ cells × voltage + temp)
- CAN FD 64-byte payload reduces frame count by 8×
- Faster fault propagation for safety-critical torque commands

---

## 4. Topology Diagram

```
Central Gateway
├── Powertrain CAN FD bus
│   ├── VCU (Vehicle Control Unit)
│   ├── BMS (Battery Management System)
│   ├── MCU Front (Motor Controller Unit)
│   ├── MCU Rear (AWD variant)
│   ├── OBC (On-Board Charger)
│   ├── DC-DC Converter ECU
│   └── TPMS module
│
├── Chassis CAN FD bus
│   ├── ESP/ABS ECU (Electronic Stability Program)
│   ├── EPS ECU (Electric Power Steering)
│   ├── EPB (Electronic Parking Brake)
│   └── CDC (Continuous Damping Control, if fitted)
│
├── Body CAN bus
│   ├── BCM (Body Control Module)
│   ├── Instrument Cluster ECU
│   ├── PEPS (Passive Entry/Start module)
│   ├── AC/HVAC controller
│   └── LIN sub-masters → mirrors, seats, windows
│
├── Automotive Ethernet (100/1000BASE-T1)
│   ├── ADAS Domain Controller (DiPilot DCU)
│   │   ├── Front camera (LVDS → Ethernet)
│   │   ├── Rear camera
│   │   ├── Side cameras × 2
│   │   ├── Front radar
│   │   ├── Corner radars × 4
│   │   └── Ultrasonic sensors × 12
│   └── Central Head Unit (DiLink)
│       └── TCU (Telematics, 4G/WiFi/BT)
│
└── Diagnostics (ISO 13400 DoIP over Ethernet)
    └── OBD-II port → DoIP gateway
```

---

## 5. Gateway Architecture

The **Central Gateway (CGW)** is the network backbone:

- **Protocol translation:** CAN FD ↔ Ethernet ↔ CAN ↔ LIN bridging
- **Routing:** Signal routing and PDU transformation between domains
- **Firewall:** Cyber-security firewall — blocks unauthorized cross-domain messages
- **Diagnostics:** DoIP routing activation, UDS gateway (ISO 14229-2 multi-ECU routing)
- **Time sync:** IEEE 802.1AS (gPTP) master for Ethernet nodes; CAN time sync for CAN nodes

---

## 6. High-Voltage Architecture

```
Battery Pack (HV)
     │
    [HV Junction Box]
     ├── [Main contactor +/-]
     ├── [Pre-charge circuit]
     ├── [Manual Service Disconnect (MSD)]
     │
     ├── → OBC (AC charging, galvanically isolated)
     ├── → DC Fast Charge port (CCS2 / GB/T)
     ├── → Inverter (Front/Rear motor drive)
     ├── → DC-DC converter → 12V LV system
     ├── → PTC heater (battery/cabin warming)
     └── → AC compressor (heat pump)
```

**Safety:**
- Isolation monitoring: > 500 Ω/V (FMVSS 305, GB/T 18384)
- Crash deactivation: ISOSense / pyrotechnic contactor opening
- Ground fault detection in BMS

---

## 7. Key Standards Compliance

| Standard | Area | Compliance |
|----------|------|------------|
| ISO 26262 | Functional Safety | ASIL B (general), ASIL D (AEB, EPS critical paths) |
| ISO 21434 | Cybersecurity | TARA conducted, SecOC on critical CAN FD messages |
| ISO 13400 | DoIP diagnostics | DoIP over Ethernet gateway |
| ISO 14229 | UDS diagnostics | Services 0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x31, 0x34-36, 0x3E, 0x85 |
| GB/T 18384 | EV safety (China) | Full compliance |
| UN R155 | Cybersecurity CSMS | Compliant for EU market |
| UN R156 | Software updates | OTA SUMS compliant |
| NCAP ADAS | Euro NCAP 2023 | 5-star safety rating |
