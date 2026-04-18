# BYD Sealion 7 — Technical Architecture Documentation
## Senior Automotive Systems Architect Reference Guide

---

## Overview

This folder contains a comprehensive, deep-technical breakdown of the **BYD Sealion 7** electric vehicle from an automotive systems architecture perspective. Content is structured for automotive engineers, ECU software developers, ADAS validation specialists, and system designers.

---

## Document Index

| File | Contents |
|------|----------|
| [01_vehicle_architecture_overview.md](01_vehicle_architecture_overview.md) | Platform (e-Platform 3.0), E/E Architecture (domain-based), full topology diagram, protocol stack, high-voltage architecture, standards compliance |
| [02_hardware_architecture.md](02_hardware_architecture.md) | All ECUs (VCU/BMS/MCU/DCU/BCM/Cluster/TCU), sensor suite (cameras/radar/ultrasonic/IMU/GPS), compute hardware (Snapdragon 8155, DiPilot DCU SoC), Blade Battery chemistry, BMS architecture, motor specs, inverter/OBC/DC-DC, thermal management |
| [03_software_architecture.md](03_software_architecture.md) | OS per domain (QNX/Linux/AUTOSAR CP/Android Auto OS), AUTOSAR BSW stack, ADAS software stack (perception→fusion→planning→control), DiLink infotainment, OTA architecture (UDS FOTA), cybersecurity (SecOC/HSM/ECDSA), ISO 26262 ASIL assignments |
| [04_adas_autonomous_features.md](04_adas_autonomous_features.md) | SAE L2+ DiPilot feature matrix (20+ features), AEB decision chain with TTC math, LKA MPC controller, ACC stop-and-go logic, sensor fusion (EKF + IMM), critical edge cases, graceful degradation, APA and DMS details |
| [05_connectivity_performance_infotainment.md](05_connectivity_performance_infotainment.md) | Telematics stack (4G/WiFi/BT/NFC), BYD App remote functions, V2X (C-V2X), voice assistant NLU pipeline, RWD/AWD performance specs, regenerative braking strategy, display configurations, HMI principles, Android Auto/CarPlay |
| [06_testing_validation_competitive.md](06_testing_validation_competitive.md) | HIL/SIL/MIL setup details, ADAS HIL test scenarios, UDS service list, key DIDs, 3 real-world debugging case studies (false AEB, cold range, LKA oscillation), competitive matrix vs Tesla Model Y / Ioniq 5 / XPeng G6, L3 roadmap, SDV future scope |

---

## Key Technical Highlights

### Platform
- **BYD e-Platform 3.0** — skateboard chassis, Cell-to-Pack Blade Battery (LFP)
- **8-in-1 power module** — VCU + MCU + OBC + DC-DC + BMS interface integrated

### Protocols
- **CAN FD** (2–5 Mbit/s) — powertrain + chassis domain
- **100/1000BASE-T1 Ethernet** — ADAS domain + infotainment backbone
- **LIN 2.2A** — body comfort actuators
- **DoIP (ISO 13400)** — diagnostic access via Ethernet gateway

### Safety
- **ASIL D** on AEB, EPS (LKA), battery contactor control
- **ISO 21434** TARA + SecOC on safety-critical CAN FD messages
- **ISO 26262** functional safety decomposition across all ADAS paths

### Battery
- **Blade LFP technology** — nail penetration: < 60°C surface temp vs 500°C for NMC
- SOC estimation via dual Kalman filter + Ah integration

### ADAS
- **Dual-channel sensor agreement** required for AEB activation (radar + camera)
- **Extended Kalman Filter** + **IMM** for multi-model object tracking
- **Graceful degradation** per sensor fault type

---

## Quick Reference: Common Diagnostic DIDs

| DID | Hex | Description |
|-----|-----|-------------|
| VIN | 0xF190 | Vehicle Identification Number |
| BMS SOC | 0x0201 | Battery state of charge |
| Motor Torque | 0x0301 | Current motor output |
| Vehicle Speed | 0x0101 | Wheel-based speed |
| ADAS SW Version | 0x0501 | DiPilot algorithm version |
| Cell Voltages | 0x0210 | All cell voltage array |
| Cell Temperatures | 0x0220 | All temperature sensor array |

---

## Applicable Standards

| Standard | Domain |
|----------|--------|
| ISO 26262:2018 | Functional Safety (ASIL A–D) |
| ISO/SAE 21434:2021 | Cybersecurity Engineering |
| ISO 21448 (SOTIF) | Safety of Intended Function |
| ISO 14229 (UDS) | Unified Diagnostic Services |
| ISO 13400 (DoIP) | Diagnostics over IP |
| ISO 15765-2 (ISO-TP) | CAN Transport Protocol |
| SAE J1939 | Heavy vehicle (not directly applicable but knowledge reference) |
| AUTOSAR 4.x | ECU software standard |
| UN R155 / R156 | CSMS + SUMS regulatory |
| Euro NCAP 2023 | Safety rating framework |
| IEEE 802.1AS (gPTP) | Ethernet time synchronization |
| SAE J3016 | Autonomy level taxonomy (L0–L5) |

---

*Content prepared as a senior automotive systems architecture reference. Data represents publicly available technical information supplemented with industry-standard practices. Specific proprietary BYD implementation details may differ.*
