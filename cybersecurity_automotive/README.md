# Automotive Cybersecurity — Master Learning Program
### Enterprise-Grade Training | Beginner → Expert | 19 Modules

> Aligned with ISO/SAE 21434 · UNECE R155/R156 · AUTOSAR Security · ISO 26262

---

## Program Overview

This program trains engineers from zero to production-ready across every domain of
automotive cybersecurity — embedded security, network attacks, ECU hardening, OTA
security, EV charging, penetration testing, AUTOSAR, and ADAS security.

**Target roles**: Embedded Engineer · Automotive Cybersecurity Engineer · Vehicle
Pentest Engineer · ADAS Security Engineer · SOC Analyst · ECU Integration Engineer

---

## Module Index

| # | Module | Level | Key Topics |
|---|--------|-------|-----------|
| [01](modules/01_fundamentals.md) | Automotive Cybersecurity Fundamentals | Beginner | CIA Triad, E/E Architecture, SDV, Attack Surface |
| [02](modules/02_networks_security.md) | Automotive Networks & Security | Beginner–Intermediate | CAN/LIN/Ethernet, SOME/IP, DoIP, Protocol Attacks |
| [03](modules/03_threat_modeling.md) | Threat Modeling & TARA | Intermediate | STRIDE, DREAD, Attack Trees, ISO 21434 TARA |
| [04](modules/04_ecu_security.md) | ECU Security & Hardening | Intermediate–Advanced | Secure Boot, HSM, TPM, JTAG, Glitch Attacks |
| [05](modules/05_can_hacking.md) | CAN Bus Hacking & Defense | Intermediate | Sniffing, Injection, Replay, DBC Analysis |
| [06](modules/06_uds_diagnostics.md) | UDS & Diagnostic Security | Intermediate | Services, Seed-Key, Flashing Security, Exploitation |
| [07](modules/07_ethernet_adas_security.md) | Ethernet & ADAS Security | Advanced | SOME/IP, TSN, Sensor Spoofing, Perception Attacks |
| [08](modules/08_ota_connected_security.md) | OTA & Connected Vehicle Security | Advanced | OTA Architecture, Cloud, TLS, API Attacks |
| [09](modules/09_ev_charging_security.md) | EV & Charging Security | Intermediate–Advanced | BMS, ISO 15118, OCPP, Charging Attacks |
| [10](modules/10_autosar_security.md) | AUTOSAR Security | Advanced | SecOC, Crypto Stack, Secure Diagnostics |
| [11](modules/11_penetration_testing.md) | Vehicle Penetration Testing | Advanced | Methodology, ECU Exploit, Firmware Analysis |
| [12](modules/12_secure_coding.md) | Secure Coding for Automotive | All Levels | MISRA C, Buffer Overflows, Race Conditions |
| [13](modules/13_soc_incident_response.md) | Automotive SOC & Incident Response | Advanced | SIEM, IDS, Fleet Monitoring, IR Playbooks |
| [14](modules/14_compliance_standards.md) | Compliance & Standards | All Levels | ISO 21434, UNECE R155, R156, ASPICE |
| [15](modules/15_real_world_attacks.md) | Real-World Automotive Attacks | All Levels | Jeep Hack, Tesla, Key Fob, CAN Injection |
| [16](modules/16_hands_on_labs.md) | Hands-On Labs | All Levels | 12 Practical Labs with Scripts & Solutions |
| [17](modules/17_edge_cases.md) | Edge Cases & Failure Scenarios | Advanced | 22 Failure Modes, Root Cause, Mitigation |
| [18](modules/18_interview_prep.md) | Interview Preparation | All Levels | 300 Q&A — OEM, Pentest, AUTOSAR, ISO 21434 |
| [19](modules/19_career_roadmap.md) | Career Roadmap | All Levels | 5 Career Paths, Certifications, Projects |

---

## Supporting Materials

| File | Description |
|------|-------------|
| [templates/tara_template.md](templates/tara_template.md) | ISO 21434 TARA worksheet template |
| [templates/threat_model_template.md](templates/threat_model_template.md) | STRIDE/DREAD threat model template |
| [templates/pentest_checklist.md](templates/pentest_checklist.md) | Vehicle penetration testing checklist |
| [templates/ecu_security_checklist.md](templates/ecu_security_checklist.md) | ECU security hardening checklist |
| [scripts/can_sniffer.py](scripts/can_sniffer.py) | Python CAN bus sniffer + DBC decoder |
| [scripts/uds_fuzzer.py](scripts/uds_fuzzer.py) | UDS service fuzzer + seed-key tester |
| [scripts/can_injector.py](scripts/can_injector.py) | CAN frame injector + replay tool |
| [scripts/firmware_analyzer.py](scripts/firmware_analyzer.py) | Firmware extraction & entropy analyzer |
| [capl/can_security_monitor.can](capl/can_security_monitor.can) | CAPL: CAN security monitoring + IDS |
| [capl/uds_security_tests.can](capl/uds_security_tests.can) | CAPL: UDS security test automation |

---

## Quick Start by Role

### Embedded Security Engineer
`01 → 04 → 10 → 12 → 14 → 17`

### Vehicle Penetration Tester
`01 → 02 → 05 → 06 → 11 → 15 → 16`

### ADAS Security Engineer
`01 → 02 → 07 → 03 → 08 → 17`

### SOC / Incident Response Analyst
`01 → 13 → 14 → 15 → 17 → 18`

### Automotive Test / Validation Engineer
`01 → 02 → 05 → 06 → 16 → 18`

### ECU Integration Engineer
`01 → 04 → 10 → 06 → 12 → 14`

---

## Standards Alignment

| Standard | Modules |
|----------|---------|
| ISO/SAE 21434:2021 | 03, 04, 08, 14 |
| UNECE WP.29 R155/R156 | 08, 14 |
| AUTOSAR Classic/Adaptive | 10, 12 |
| ISO 26262 (functional safety ↔ cyber) | 04, 14 |
| ASPICE SYS/SWE | 03, 12, 14 |
| NIST CSF | 13, 14 |
| SAE J3061 | 03, 14 |
| IEC 62443 | 04, 13, 14 |

---

## Lab Environment Requirements

```
Hardware (optional, labs also run in SIL mode):
  - CAN adapter: PCAN-USB / Vector VN1610 / Kvaser Leaf
  - Raspberry Pi 4 (ECU simulator)
  - OBD-II Dongle

Software (all open-source labs):
  - Python 3.10+, python-can, scapy, udsoncan
  - Wireshark / BUSMASTER / SavvyCAN / Kayak
  - Ghidra / Radare2 / Binwalk
  - SocketCAN (Linux) / Virtual CAN (vcan0)
  - Docker (for isolated lab environments)
```

---

*Program Version: 2.0 | Last Updated: 2026 | Aligned: ISO/SAE 21434:2021*
