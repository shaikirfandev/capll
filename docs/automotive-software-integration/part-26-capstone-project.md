# Part 26 — Capstone Project: Multi-Domain Automotive Vehicle Software Integration

---

## Project Title
**Multi-Domain Automotive Vehicle Software Integration**

---

## Objective

Integrate the complete software stack of a modern passenger vehicle across all major domains:
- ADAS Domain Controller (ADC)
- Central Gateway ECU
- Digital Instrument Cluster ECU
- Infotainment (IVI) ECU
- Telematics Control Unit (TCU)
- Body ECU
- Powertrain ECU

Demonstrate the complete integration journey from requirement to release.

---

## Vehicle Architecture Overview

```
+--------------------------------------------------------------------+
|                        VEHICLE                                     |
|                                                                    |
|  ADAS DOMAIN          INFOTAINMENT         TELEMATICS              |
|  +----------+         +-----------+        +--------+              |
|  | ADAS DC  |---ETH---| IVI ECU   |        |  TCU   |--LTE/5G---→Cloud |
|  | Orin/SoC |         | AAOS/Qcom |        +--------+              |
|  +----------+         +-----------+            |                   |
|      |                     |                   |                   |
|  +---------+           +---------+             |                   |
|  |Cluster  |           |  Body   |             |                   |
|  |  ECU    |           |  ECU    |             |                   |
|  +---------+           +---------+             |                   |
|      |                     |                   |                   |
|  +-------------------------------------------+---+                |
|  |       CENTRAL GATEWAY ECU (NXP S32G)           |               |
|  +--------------------------------------+----------+               |
|       |            |           |        |                          |
|    CAN FD         CAN        CAN FD   Ethernet                    |
|  (ADAS/Brake)  (Powertrain)(Body/LIN) (Backbone)                  |
|                                                                    |
+--------------------------------------------------------------------+
```

---

## Network Topology

```
Ethernet Backbone (1000BASE-T1):
  Central Gateway ←→ ADAS DC
  Central Gateway ←→ Cluster ECU
  Central Gateway ←→ IVI ECU
  Central Gateway ←→ TCU

CAN FD Bus 1 (2 Mbps, ADAS):
  Central Gateway ←→ Brake ECU
  Central Gateway ←→ EPS ECU
  Central Gateway ←→ ADAS DC (actuator interface)

CAN Bus 2 (500 kbps, Powertrain):
  Central Gateway ←→ Engine ECU
  Central Gateway ←→ Transmission ECU
  Central Gateway ←→ ABS/ESC ECU

CAN FD Bus 3 (1 Mbps, Body/Chassis):
  Central Gateway ←→ Body ECU
  Body ECU ←→ (LIN clusters: door modules, seat ECUs, mirror ECUs)

Camera Bus (100BASE-T1 per camera):
  ADAS DC ←→ Front Camera
  ADAS DC ←→ Rear Camera
  ADAS DC ←→ Left/Right Camera × 2

Radar (100BASE-T1):
  ADAS DC ←→ Front Radar
  ADAS DC ←→ 4× Corner Radar (CAN FD sub-network)
```

---

## ECU List and Software Baseline

| ECU | HW Platform | OS | AUTOSAR Type | SW Version |
|---|---|---|---|---|
| ADAS DC | Qualcomm Snapdragon Ride Gen2 | Linux PREEMPT_RT | Adaptive | v1.3.0 |
| Central Gateway | NXP S32G2 | FreeRTOS + Linux | Classic + Adaptive | v4.2.0 |
| Cluster ECU | Renesas R-Car H3 | Linux | Adaptive | v2.1.0 |
| IVI ECU | Qualcomm SA8295P | Android Automotive 13 | Adaptive | v3.0.1 |
| TCU | NXP i.MX8M Plus | Linux | Custom | v1.5.0 |
| Body ECU | NXP S32K3 | AUTOSAR OS | Classic | v2.0.1 |
| Engine ECU | Renesas RH850/U2A | AUTOSAR OS | Classic | v5.1.0 |

---

## Phase 1 — Requirement Analysis

### Key Integration Requirements

| Req ID | Requirement | Source | ASIL |
|---|---|---|---|
| INT-001 | AEB shall trigger within 150ms of confirmed threat | Safety Req | ASIL-C |
| INT-002 | VehicleSpeed shall be available on Ethernet backbone within 20ms of CAN reception | System Req | QM |
| INT-003 | Cluster shall display telltales within 1 second of ignition on | Display Req | ASIL-B |
| INT-004 | IVI shall show vehicle speed within 200ms | IVI Req | QM |
| INT-005 | OTA update success rate shall be ≥ 98% | OTA Req | QM |
| INT-006 | UDS DiagnosticSessionControl shall respond within 50ms | Diag Req | QM |

---

## Phase 2 — Architecture and Interface Definition

### SOME/IP Service Definitions

| Service | Provider | Consumer | Event Period |
|---|---|---|---|
| VehicleStateService | Central Gateway | Cluster, IVI, TCU | 10ms |
| ObjectListService | ADAS DC | Cluster (ADAS viz) | 30ms (33Hz) |
| ClimateService | Body ECU | IVI | 100ms |
| LocationService | TCU | IVI (navigation), ADAS | 100ms |

### CAN FD Interface (ADAS domain)

| Signal | Source | Consumer | Message ID | Period |
|---|---|---|---|---|
| AEB_BrakeRequest | ADAS DC | Brake ECU | 0x300 | 5ms |
| LKA_SteeringTorque | ADAS DC | EPS ECU | 0x310 | 5ms |
| BrakeStatus_Feedback | Brake ECU | ADAS DC | 0x400 | 5ms |

---

## Phase 3 — Development

Each ECU team develops their software components. Integration team:
- Defines and baselines ICD
- Creates CANoe simulation for unavailable ECUs
- Sets up development bench with CAN/Ethernet analyzers

---

## Phase 4 — Configuration

### AUTOSAR Classic (Body ECU example)
1. Configure CanIf: 3 CAN FD HW objects (ADAS, Body CAN, Diag)
2. Configure COM: VehicleSpeed, DoorStatus, WindowControl signals
3. Configure PduR: routing from CAN Bus 3 to Ethernet via gateway SOME/IP
4. Configure Dcm: UDS services, DID list, security access
5. Configure Dem: DTC list (50 DTCs for body functions)
6. Configure NvM: 10 NvM blocks (window positions, user preferences, DTC status)
7. Generate code with DaVinci Configurator Pro → rebuild

### Adaptive AUTOSAR (ADAS DC example)
1. Define service manifests: ObjectListService, ADCStateService
2. Configure ara::com SOME/IP binding
3. Configure Execution Manager: process start order, restart policy
4. Build with CMake cross-compiler for ARM target

---

## Phase 5 — Build

CI/CD Pipeline (GitHub Actions):
- Every commit triggers: static analysis → unit test → cross-compile → package
- Integration baseline built every Friday: all ECU SW compiled and packaged

---

## Phase 6 — ECU Flashing and Bring-Up

### Flash Order
1. Body ECU (simplest, verify basic CAN first)
2. Engine ECU (verify powertrain CAN signals)
3. Central Gateway (verify bridging of CAN to Ethernet)
4. Cluster ECU (verify SOME/IP VehicleStateService received)
5. IVI ECU (verify Android Automotive + VHAL integration)
6. TCU (verify cellular + MQTT telemetry)
7. ADAS DC (verify all sensors, then actuators)

### Bring-Up Verification per ECU
```
[ ] ECU boots (no reset loop)
[ ] DTC count at startup = 0 (or only expected startup DTCs)
[ ] CAN/Ethernet communication active
[ ] Basic functional test passes
[ ] Security access verified
```

---

## Phase 7 — Network Integration (Bench)

### Verification Sequence

**Step 1: CAN Powertrain**
- Inject EngineSpeed (0x0C8) from Engine ECU simulator
- Verify Gateway receives and translates to VehicleStateService SOME/IP event
- Verify Cluster shows RPM on display

**Step 2: CAN FD ADAS**
- Inject AEB trigger from ADAS DC (0x300)
- Verify Brake ECU receives and simulates braking
- Measure latency: ADAS trigger → CAN FD → Brake ECU: < 5ms

**Step 3: Ethernet SOME/IP**
- Cluster subscribes to ObjectListService
- ADAS DC publishes object list (simulated)
- Verify cluster displays ADAS objects

**Step 4: DoIP Diagnostics**
- Connect laptop via DoIP (Ethernet)
- Read VIN from all ECUs via 0x22 0xF190
- Clear DTCs on all ECUs

---

## Phase 8 — Software Integration Testing (SIL/Bench)

### Test Execution (subset)

| Test ID | Description | Expected | Result |
|---|---|---|---|
| SIT-001 | VehicleSpeed on CAN → SOME/IP latency | < 20ms | 12ms PASS |
| SIT-002 | AEB brake command latency | < 5ms | 3ms PASS |
| SIT-003 | Cluster telltale at startup | < 1s | 480ms PASS |
| SIT-004 | IVI VehicleSpeed display | < 200ms | 85ms PASS |
| SIT-005 | DTC set on sensor disconnection | Within 200ms | PASS |
| SIT-006 | MQTT telemetry published | Every 10s | PASS |
| SIT-007 | OTA download and install | < 30 min for 50MB | 22 min PASS |

---

## Phase 9 — HIL Integration

### HIL Setup
- dSPACE SCALEXIO HIL with all 7 ECUs connected
- Vehicle dynamics model (longitudinal, lateral)
- Sensor simulation: camera video replay, radar object injection
- CAN/Ethernet network configured per network topology

### HIL Test Categories
- 200 functional tests (all features)
- 50 fault injection tests (sensor failures, CAN errors)
- 10 endurance tests (8+ hours each)
- 30 latency/timing tests
- 20 OTA update tests

### HIL Result: 487/510 passed (95.5%)
- 23 failures: 18 defects found; 5 test spec issues corrected
- P1 defect: 2 (resolved within sprint)

---

## Phase 10 — Vehicle Integration

### Test Vehicle
- Pre-production vehicle with all ECUs installed
- Closed-course track for ADAS validation
- Test instruments: data logger, 4× high-speed cameras

### Vehicle Test Highlights

| Test | Conditions | Result |
|---|---|---|
| AEB at 50 km/h | Static target | Avoided, latency 98ms |
| ACC following | 80 km/h, lead vehicle decelerates | Maintained 50m gap |
| LKA lane centering | Highway 100 km/h | ±0.15m from center |
| Cluster boot telltale | Cold start -10°C | 620ms (within 1s req) |
| OTA update in vehicle | Parked, LTE signal | 28 minutes, success |
| eCall simulation | Manual trigger | MSD sent within 5s |

---

## Phase 11 — Diagnostics Validation

```
[ ] All 120 ECU DTCs verified (set conditions, clear, read)
[ ] Security access for all ECUs (seed/key algorithm verified)
[ ] DoIP routing to all 7 ECUs via Central Gateway
[ ] All DIDs readable (VIN, SW version, hardware variant)
[ ] Programming session and flashing verified via OBD port
[ ] OBD Mode 03 (emissions DTCs) verified for Engine/Transmission ECUs
```

---

## Phase 12 — Cybersecurity Review

- Penetration test on TCU (external network interface)
- TARA updated: OTA path, diagnostic interface, IVI external connectivity
- SecOC verified on AEB/LKA CAN FD messages
- Secure boot verified on all ECUs
- Certificate expiry management process documented

---

## Phase 13 — Functional Safety Review

- ASIL-C verification for AEB: fault injection tests (camera loss, radar loss, brake ECU error)
- E2E protection on AEB brake request (CAN FD 0x300): CRC + counter verified
- FTTI test: camera signal loss → AEB-vision disabled within 150ms
- Cluster safety telltale (ASIL-B): Qt Safe Renderer verified independent of main display

---

## Phase 14 — Release

### Release Package

```
Integration Baseline: FINAL_2025_W38
  adas_dc_v1.3.0.hex        SHA256: a1b2c3...
  gateway_v4.2.0.hex         SHA256: d4e5f6...
  cluster_v2.1.0.hex         SHA256: g7h8i9...
  ivi_v3.0.1.img             SHA256: j0k1l2...
  tcu_v1.5.0.tar.gz          SHA256: m3n4o5...
  body_v2.0.1.hex            SHA256: p6q7r8...
  engine_v5.1.0.hex          SHA256: s9t0u1...
  build_manifest.json
  release_notes_v2025_W38.pdf
  hil_test_report_final.pdf
  vehicle_test_report_final.pdf
  safety_review_signoff.pdf
  security_review_signoff.pdf
```

---

## Phase 15 — OTA Deployment

### Campaign Plan
- Stage 1: 100 internal fleet vehicles → monitor 2 weeks
- Stage 2: 1,000 vehicles → monitor 1 week
- Stage 3: Full fleet rollout

### Monitoring KPIs
- OTA success rate: target ≥ 98%
- Post-update DTC count: target ≤ 2 new DTCs per vehicle
- eCall availability: target 100% in Stage 1
- ADAS feature availability: target 100% post-update

---

## Capstone Learnings

| Topic | Key Integration Lesson |
|---|---|
| ADAS | End-to-end latency budget must be measured, not assumed |
| Gateway | VLAN routing and SOME/IP bridging are common sources of failure |
| Cluster | Boot time optimization requires early/late boot split |
| IVI | VHAL backend initialization order is critical for fast startup |
| TCU | MQTT reconnection strategy is essential for field reliability |
| OTA | A/B partitions + staged rollout are non-negotiable for safety |
| Diagnostics | DTC configuration testing should start in Phase 10, not Phase 15 |
| Security | Secure boot must be tested with fault injection from day 1 |
| Safety | FTTI testing belongs in HIL, not just in vehicle |

---

*This concludes the Automotive Software Integration Reference Document.*

*Return to [README](README.md) | Start from [Part 1 — Fundamentals](part-01-fundamentals.md)*
