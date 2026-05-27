# Module 01 — Automotive Cybersecurity Fundamentals

> Level: Beginner → Intermediate | Est. study time: 6 hours

---

## 1.1 What is Automotive Cybersecurity?

Automotive cybersecurity is the discipline of protecting vehicle electronic systems,
software, communication networks, and data against unauthorized access, manipulation,
destruction, or disclosure — while maintaining safe vehicle operation.

Unlike traditional IT security, automotive cybersecurity must operate under:
- **Real-time constraints** (hard deadlines, microsecond response)
- **Functional safety co-existence** (ISO 26262 — cyber exploits must not cause ASIL violations)
- **Long product lifetimes** (15–20 years vs 3–5 years in IT)
- **Supply chain complexity** (OEM → Tier1 → Tier2 → semiconductor)
- **Physical safety** (compromised brakes, steering = risk to human life)

---

## 1.2 The CIA Triad in Automotive Context

| Property | IT Definition | Automotive Example |
|----------|--------------|-------------------|
| **Confidentiality** | Data not disclosed to unauthorized parties | Protect calibration data, encryption keys, PII, proprietary DBC content |
| **Integrity** | Data not tampered with | CAN message counters/CRC, firmware hash validation, OTA signature |
| **Availability** | System accessible when needed | AEB must respond in <600ms; DoS on CAN bus is safety-critical |

**Additional automotive properties:**
- **Authenticity** — Is this ECU message genuinely from the claimed sender? (SecOC)
- **Non-repudiation** — Audit log of who flashed what firmware, when
- **Safety** — Cybersecurity failures must not cause ISO 26262 ASIL violations

---

## 1.3 Threat vs Vulnerability vs Risk

```
THREAT:      An actor or event that could exploit a weakness
              e.g. "Attacker injects fake ACC messages on CAN"

VULNERABILITY: A weakness that could be exploited
              e.g. "CAN bus has no message authentication"

RISK:        Probability × Impact of exploitation
              e.g. Risk(ACC injection) = HIGH probability × CRITICAL safety impact
                                       = CRITICAL RISK
```

**ISO 21434 terminology:**
- **Asset**: Something of value (e.g., firmware signing key, UDS session)
- **Damage scenario**: What harm could result (e.g., vehicle crash, data breach)
- **Threat scenario**: How the damage could be achieved
- **Attack path**: The specific technical steps to reach the asset
- **Attack feasibility**: How hard is the attack (time, skill, resources, opportunity)
- **Risk level**: CRITICAL / HIGH / MEDIUM / LOW / NEGLIGIBLE

---

## 1.4 Attack Surface of a Modern Vehicle

```
┌─────────────────────────────────────────────────────────────┐
│                    VEHICLE ATTACK SURFACE                   │
├─────────────────────────────────────────────────────────────┤
│  PHYSICAL        │  SHORT RANGE      │  LONG RANGE          │
│                  │                   │                       │
│  OBD-II port     │  Bluetooth        │  Cellular (4G/5G)    │
│  JTAG/SWD debug  │  Wi-Fi            │  V2X (C-V2X/DSRC)   │
│  USB ports       │  NFC/RFID keyfob  │  OTA update          │
│  SD card slots   │  UWB (UWB keyless)│  Cloud backend API   │
│  Charging port   │  Dedicated ShorT  │  Mobile app          │
│  Infotainment    │  Range Devices    │  Remote diagnostics  │
│  CAN bus access  │  (DSRC 5.9GHz)   │  V2I / V2N           │
└─────────────────────────────────────────────────────────────┘
```

**Attack entry points ranked by ease of exploitation:**
1. OBD-II physical access (highest, no auth on older vehicles)
2. Infotainment web browser / app store
3. Bluetooth pairing vulnerabilities
4. OTA update mechanism (if unsigned)
5. Mobile companion app API
6. V2X messages (spoofable if not authenticated)
7. Charging station interface (ISO 15118)

---

## 1.5 Vehicle E/E Architecture Evolution

### Traditional Domain Architecture (Pre-2020)

```
  ┌──────────────────────────────────────────────────────────────┐
  │                    CENTRAL GATEWAY ECU                      │
  │                   (CAN gateway / router)                    │
  └────┬──────────────┬──────────────┬──────────────┬───────────┘
       │              │              │              │
  ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐   ┌────▼────┐
  │POWERTRAIN│  │CHASSIS &   │  │INFOTAIN-│   │ADAS /   │
  │ DOMAIN  │  │SAFETY      │  │MENT     │   │SAFETY   │
  │         │  │DOMAIN      │  │DOMAIN   │   │DOMAIN   │
  │ECM/TCM  │  │ABS/ESP/EPS │  │HU/ICE   │   │ADAS ECU │
  │BMS(EV)  │  │BCM/PEPS    │  │Cluster  │   │Cameras  │
  │         │  │Airbag      │  │OTA      │   │Radar    │
  └─────────┘  └────────────┘  └─────────┘   └─────────┘
```

### Modern Zonal Architecture (2022+, SDV)

```
  ┌────────────────────────────────────────────────────────────────┐
  │               VEHICLE COMPUTE PLATFORM (VCP)                  │
  │         High-Performance Central Computer (HPC)               │
  │   Automotive Ethernet backbone (1Gbps/10Gbps TSN)            │
  └────┬──────────────┬──────────────┬──────────────┬────────────┘
       │              │              │              │
  ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐   ┌────▼────┐
  │ ZONE A  │  │  ZONE B    │  │ ZONE C  │   │ ZONE D  │
  │Front-L  │  │Front-R     │  │Rear-L   │   │Rear-R   │
  │Zonal ECU│  │Zonal ECU   │  │Zonal ECU│   │Zonal ECU│
  │(Actuator│  │(Actuator   │  │(Actuator│   │(Actuator│
  │nodes)   │  │nodes)      │  │nodes)   │   │nodes)   │
  └─────────┘  └────────────┘  └─────────┘   └─────────┘
  
  SDV Advantages for Security:
  - Centralized security monitoring (VCP is the trust anchor)
  - Zonal isolation (compromised zone cannot cascade easily)
  - Software updates via OTA to VCP, pushed to zones
  - Hardware Security Module (HSM) in VCP
```

---

## 1.6 Key ECU Types and Their Security Relevance

| ECU | Function | Security Relevance | ASIL |
|-----|----------|--------------------|------|
| **Gateway (GW)** | Routes messages between domains/busses | Firewall, message filtering, SecOC gateway | ASIL B |
| **BCM** (Body Control) | Door locks, windows, lights | Keyless entry, remote unlock attacks | ASIL A |
| **TCU** (Telematics) | 4G/5G, GPS, OTA | Highest external attack surface | QM–A |
| **ADAS ECU** | Camera/Radar/LiDAR fusion | Perception spoofing, AEB safety | ASIL C/D |
| **ECM** (Engine Control) | Engine management | Torque manipulation, emissions defeat | ASIL C/D |
| **EPS** (Electric Power Steering) | Steering control | Safety-critical, steering takeover | ASIL D |
| **ABS/ESC** | Braking | Safety-critical, brake manipulation | ASIL D |
| **Cluster/IPC** | Driver display | Spoofed warnings, distraction | ASIL B |
| **OBD-II Server** | Diagnostics entry | Attack vector for all ECUs | QM |

---

## 1.7 Software Defined Vehicle (SDV) Security Implications

SDV shifts from hardware-dedicated functions to software on high-performance compute:

```
Traditional:   100+ ECUs → Each function has dedicated MCU
SDV:           5–10 zones + 1-3 HPC platforms → Software containers run functions

SDV Security Challenges:
┌─────────────────────────────────────────────────┐
│ 1. Hypervisor security (Type-1, e.g. QNX, XEN) │
│ 2. Container isolation (Docker/Podman on Linux)  │
│ 3. POSIX OS attack surface (Linux kernel vulns)  │
│ 4. Inter-VM communication channels              │
│ 5. Shared memory exploitation                   │
│ 6. App store / 3rd party app trust              │
│ 7. Remote code execution via OTA                │
│ 8. Supply chain software compromise             │
└─────────────────────────────────────────────────┘
```

**SDV Security Stack:**
```
┌─────────────────────────────────┐
│    Applications (ADAS, IVI)     │  ← App isolation, signing
├─────────────────────────────────┤
│    Middleware (AUTOSAR Adaptive │  ← SecOC, TLS, mTLS
│    / ROS2 / SOME/IP)            │
├─────────────────────────────────┤
│    OS (Linux / QNX / Android)   │  ← Kernel hardening, SELinux
├─────────────────────────────────┤
│    Hypervisor (Type-1)          │  ← VM isolation
├─────────────────────────────────┤
│    Hardware (SoC + HSM/TPM)     │  ← Root of Trust
└─────────────────────────────────┘
```

---

## 1.8 Secure Development Lifecycle (SDL) for Automotive

```
ISO 21434 Cybersecurity Engineering Lifecycle:

  CONCEPT         DEVELOPMENT       PRODUCTION      POST-PRODUCTION
  ─────────────   ───────────────   ─────────────   ───────────────
  Item definition Security goals    Security         Vulnerability
  Cybersecurity   Threat analysis   testing          monitoring
  case init       TARA              Penetration      Incident
  Risk assessment Architecture      testing          response
  Security goals  design reviews    Cyber FMEA       OTA patches
                  Secure coding     Release gate     SBOM updates
                  Static analysis                    EoL decommission
                  Code review
                  Unit/integration
```

**Phases and Key Activities:**

| Phase | Key Output | Standard Reference |
|-------|-----------|-------------------|
| Concept | Cybersecurity case, item definition | ISO 21434 §9 |
| Product Development | TARA, security architecture, secure code | ISO 21434 §10, §11 |
| Integration & Testing | Pentest report, cyber FMEA | ISO 21434 §12 |
| Validation | Security validation report | ISO 21434 §13 |
| Production | CSMS (Cybersecurity Management System) | UNECE R155 |
| Post-Production | VSOC, incident response, OTA patches | ISO 21434 §14 |

---

## 1.9 Key Security Definitions

| Term | Definition |
|------|-----------|
| **Attack feasibility** | How easy is the attack (time, expertise, equipment, knowledge) |
| **Damage scenario** | Description of harm caused if attack succeeds |
| **Cybersecurity goal** | High-level security requirement tied to a damage scenario |
| **Cybersecurity claim** | Statement that a countermeasure sufficiently addresses a risk |
| **CSMS** | Cybersecurity Management System — company-level process for managing cyber risks |
| **VSOC** | Vehicle Security Operations Centre — real-time monitoring of fleet cyber events |
| **SecOC** | Secure Onboard Communication — AUTOSAR module for CAN message authentication |
| **HSM** | Hardware Security Module — dedicated crypto processor in MCU |
| **RoT** | Root of Trust — hardware anchor for all cryptographic operations |
| **SBOM** | Software Bill of Materials — inventory of all software components + versions |
| **TARA** | Threat Analysis and Risk Assessment — ISO 21434 mandated process |

---

## 1.10 Summary — Module 01

```
KEY TAKEAWAYS:

✓ Automotive cybersecurity ≠ IT security: real-time + safety + 20yr lifetime
✓ CIA Triad extended with Authenticity and Safety in vehicles
✓ Attack surface spans physical, short-range, and long-range vectors
✓ Architecture evolved: Domain → Zonal → SDV (more software = more attack surface)
✓ ISO 21434 mandates cybersecurity throughout the entire vehicle lifecycle
✓ HSM/TPM = hardware root of trust for all security mechanisms
✓ Gateway ECU is the most critical security boundary
✓ SDV introduces cloud/container risks but enables better centralized defense
```

**Next Module**: [02 — Automotive Networks & Security](02_networks_security.md)
