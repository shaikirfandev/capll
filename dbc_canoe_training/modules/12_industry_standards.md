# Module 12 — Industry Standards for CAN/DBC Engineering

> **Level**: Advanced  
> **Duration**: ~3 hours  
> **Goal**: Understand the standards that govern DBC creation, signal safety, and automotive network development.

---

## 12.1 ISO 11898 — CAN Standard Family

### Standard Overview

| Standard | Title | Scope |
|----------|-------|-------|
| ISO 11898-1:2015 | Data link layer and physical signaling | CAN frame structure, bit stuffing, error handling, CAN FD |
| ISO 11898-2:2016 | HS-CAN physical layer | Electrical spec: differential signaling, 120Ω termination, up to 1 Mbps |
| ISO 11898-3:2006 | LS-CAN fault-tolerant physical layer | Single-wire fault tolerance, up to 125 Kbps (LIN alternative) |
| ISO 11898-4:2004 | Time-triggered CAN (TTCAN) | Synchronized time-slot based transmission (rarely used) |
| ISO 11898-6:2013 | CAN Selective Wake-up | Wake-up filter functionality |

### Key Electrical Parameters (ISO 11898-2)

```
Parameter           Value
──────────────────────────────────────
Dominant voltage    CAN_H ≥ 2.75V, CAN_L ≤ 2.25V (differential ≥ 1.5V)
Recessive voltage   CAN_H = CAN_L ≈ 2.5V (differential ≈ 0V)
Termination         120Ω at each bus end
Max cable length    40m @ 1 Mbps, 500m @ 125 Kbps
Max nodes           Up to 112 (standard HS transceivers)
Common bitrates     125K, 250K, 500K, 1000K bps
```

### ISO 11898-1 DBC Relevance

```
DBC files encode the ISO 11898-1 data link layer content:
  ✓ Frame ID (11 or 29 bit)
  ✓ DLC (0–8 for CAN 2.0, 0–15 for CAN FD)
  ✓ Signal bit positions and byte order
  ✓ Extended frame bit (IDE)
  
NOT in DBC (handled by hardware/driver):
  ✗ Bit timing / baud rate (set in CANoe hardware config)
  ✗ CRC polynomial (hardware layer)
  ✗ ACK mechanism (hardware)
  ✗ Termination values (physical installation)
```

---

## 12.2 AUTOSAR Communication Stack

### Stack Architecture

```
        ┌─────────────────────────────────┐
        │        Application Layer         │
        │   SWC ──── RTE ──── SWC         │
        ├─────────────────────────────────┤
        │        COM Module                │
        │  I-Signal → I-Signal-I-PDU       │
        │  Encoding: Factor, Offset, Type  │
        │  Init value, Timeout, E2E        │
        ├─────────────────────────────────┤
        │        PDU Router               │
        │  Routes I-PDUs between buses    │
        ├─────────────────────────────────┤
        │    CanIf / FrIf / EthIf         │
        ├─────────────────────────────────┤
        │  CAN / FlexRay / Ethernet HW    │
        └─────────────────────────────────┘
```

### AUTOSAR vs DBC Terminology Mapping

| AUTOSAR Term | DBC Equivalent | Notes |
|---|---|---|
| SystemSignal | SG_ | Top-level signal definition |
| ComSignal | SG_ with COM config | Signal with COM attributes |
| I-Signal | SG_ | Internal signal in COM module |
| ISignalIPdu | BO_ | PDU (message) container |
| Frame | BO_ | CAN frame with ID and DLC |
| ISignal_ComSignalLength | SG_ length | Bit length |
| ISignal_BitPosition | SG_ start_bit | Position in PDU |
| ComSignalEndianness | @1 / @0 | Intel / Motorola |
| InitValue | BA_ GenSigStartValue | Initial / default value |
| ComSignalFactor | factor | Scaling factor |
| ComSignalOffset | offset | Scaling offset |

### AUTOSAR COM Code Generation

```
Tool: EB Tresos Studio, Vector DaVinci Configurator, ETAS ISOLAR
Process:
  1. Import DBC → convert to ARXML
  2. Configure COM module in ARXML
  3. Code generator creates:
     - CAN_Com_Cfg.c / .h (signal tables)
     - Com_Cbk.c (signal callback hooks)
     - Can_PBcfg.c (CAN controller configuration)
  
Generated code example:
  Com_SendSignal(SIGNAL_AEB_DECEL_REQ, &rawValue);
  Com_ReceiveSignal(SIGNAL_WHEEL_SPEED_FL, &rawValue);
```

---

## 12.3 ISO 14229 — UDS Diagnostics

### Relevance to DBC

UDS (Unified Diagnostic Services) runs over CAN — the DBC must include diagnostic message definitions:

```
Standard diagnostic message IDs:
  0x7DF    OBD2 Functional Request (broadcast)
  0x7E0–0x7E7  ECU-specific diagnostic request (tester → ECU)
  0x7E8–0x7EF  ECU-specific diagnostic response (ECU → tester)
  0x18DA00F1   Extended (29-bit) physical request
  0x18DAF100   Extended (29-bit) physical response

DBC for diagnostic messages:
BO_ 2015 DiagRequest: 8 Tester
 SG_ DiagData : 0|64@1+ (1,0) [0|0] "" AEB_ECU

BO_ 2024 DiagResponse: 8 AEB_ECU
 SG_ DiagData : 0|64@1+ (1,0) [0|0] "" Tester
```

### ISO 15765-2 Transport Protocol (ISO-TP)

```
UDS uses ISO-TP (ISO 15765-2) for multi-frame messages:
  Single Frame (SF):   DLC ≤ 7 bytes of data
  First Frame (FF):    Start of multi-frame (>7 bytes)
  Consecutive Frame (CF): Continuation
  Flow Control (FC):   Receiver controls flow

DBC represents ISO-TP at the CAN frame level
Higher-level UDS PDUs are described in CDD/ODX files
(CANdelaStudio, CANoe Diagnostics module)
```

---

## 12.4 ISO 26262 — Functional Safety

### ASIL Levels and CAN Signal Requirements

| ASIL | Description | CAN Signal Requirements |
|------|-------------|------------------------|
| QM | Quality Management | No safety requirement |
| ASIL-A | Lowest safety | Basic range check |
| ASIL-B | Low-medium | Alive counter, CRC, range check |
| ASIL-C | Medium | E2E Profile 01/02, signal timeout |
| ASIL-D | Highest | Full E2E, redundancy, independent monitoring |

### Typical ASIL Assignments in ADAS

| Signal | ASIL | E2E Required |
|--------|------|-------------|
| WheelSpeed | B | Yes (E2E P01) |
| AEB_Active (request) | B | Yes (E2E P01) |
| SteeringAngle | B | Yes |
| EngineSpeed | A | Recommended |
| VehicleSpeed display | QM | No |
| BCM Door status | QM | No |
| Infotainment signals | QM | No |

### DBC Attributes for Safety

```
BA_DEF_ BO_ "ASIL" ENUM "QM","A","B","C","D";
BA_DEF_ BO_ "SafetyClass" ENUM "NONE","IMPORTANT","CRITICAL";
BA_DEF_ BO_ "FaultReactionTime_ms" INT 0 1000;

/* Assign ASIL levels */
BA_ "ASIL"                  BO_ 512  "B";    /* WheelSpeed */
BA_ "ASIL"                  BO_ 580  "B";    /* AEB_Req */
BA_ "ASIL"                  BO_ 896  "B";    /* EPS_Status */
BA_ "ASIL"                  BO_ 768  "A";    /* VehicleStatus */
BA_ "ASIL"                  BO_ 848  "QM";   /* IPC_Display */
BA_ "ASIL"                  BO_ 1056 "QM";   /* BCM_Status */

BA_ "FaultReactionTime_ms"  BO_ 512  30;    /* 3× cycle time */
BA_ "FaultReactionTime_ms"  BO_ 580  60;    /* 3× cycle time */
```

---

## 12.5 ASPICE — Software Process Improvement

### What ASPICE Means for DBC Work

ASPICE (Automotive SPICE) is a process framework for automotive software development (based on ISO/IEC 15504). Most OEM projects require ASPICE CL2 or CL3.

### Key Work Products for DBC Engineering

```
Process: SYS.3 System Architecture Design
  Work product: System Architecture Documentation
  DBC content: Network topology diagram, bus selection rationale, 
               message allocation per domain

Process: SWE.2 Software Architecture
  Work product: Software Architecture Specification
  DBC content: DBC file (v-controlled), AUTOSAR ARXML (if applicable),
               communication matrix, signal ASIL assignments

Process: SWE.5 Software Integration Testing
  Work product: Software Integration Test Specification + Results
  DBC content: CANoe test plan (CAPL test modules),
               test results (pass/fail HTML reports)
               
Process: SWE.6 Software Qualification Testing
  Work product: Qualification Test Results
  DBC content: System-level bus capture evidence, regression test report
```

### ASPICE CL2 Checklist for DBC

```
At ASPICE Capability Level 2:
□ DBC under version control (Git/SVN) with baseline identification
□ Communication matrix traceable to system requirements
□ Peer review evidence (review minutes with reviewer sign-off)
□ Change request process (ECR with before/after documented)
□ Test plan with test cases per signal
□ Test results linked to test cases
□ Known defects logged and tracked
□ DBC release clearly labeled BASELINE/DRAFT/APPROVED/RELEASED
```

---

## 12.6 SAE J1939 — Heavy Vehicle CAN Protocol

### J1939 vs CAN/DBC Differences

| Feature | Classical CAN + DBC | SAE J1939 |
|---------|--------------------|-----------| 
| Frame type | 11-bit or 29-bit | Always 29-bit extended |
| ID structure | Free allocation | Structured: Priority+DP+PGN+SA |
| Signal naming | Project-specific | SPN (Suspect Parameter Numbers) |
| DLC | 0–8 bytes | Typically 8 bytes |
| Multi-frame | ISO-TP (diagnostics only) | J1939-21 Transport Protocol (TP) |
| Higher layer | None standard | J1939-71 (vehicle application layer) |

### J1939 29-bit ID Breakdown

```
Bits 28-26: Priority (0–7)
Bit 25:     Reserved (0)
Bit 24:     Data Page (0 or 1)
Bits 23-8:  PGN (16 bits) — Parameter Group Number
Bits 7-0:   Source Address (0–253, 254=null, 255=global)

Example: Engine Speed message
  Priority = 3 (011b)
  Reserved = 0
  DP = 0
  PGN = 61444 (0xF004) = EEC1 (Electronic Engine Controller 1)
  SA = 0 (Engine #1)
  
  29-bit ID = 0x0CF00400
  
In DBC:
  BO_ 2566844416 EEC1: 8 Engine
     (0x0CF00400 + 0x80000000 = 2566844416)
   SG_ EngineSpeed : 24|16@1+ (0.125,0) [0|8031.875] "rpm" ...
   SG_ DriverDemandEngTorque : 8|8@1+ (1,-125) [-125|125] "%" ...
```

---

## 12.7 OEM-Specific Naming Standards

### BMW Naming Convention

```
Messages:   [FunctionGroup]_[Function]_[SubFunction]
            Example: ENG_EngineControl_TorqueRequest

Signals:    [PhysicalQuantity][_Direction][_Unit]
            Example: EngTorque_Req_Nm, WhlSpd_FL_kph

ID Ranges:  0x0–0xFF:    Priority broadcast
            0x100–0x3FF: Powertrain
            0x400–0x5FF: Chassis
            0x600–0x7EF: Body/Comfort
```

### Volkswagen Group Naming Convention

```
Messages:   [SystemCode]_[Sender]_[Function]_[Index]
            Example: CAN01_ESP_Fahrdynamik_01

Signals:    German or English, underscore separated
            Example: ESP_Bremsdruck_VA (front axle brake pressure)
```

### Generic OEM Best Practice

```
Message naming:
  PascalCase, underscore between sections
  Example: AEB_BrakeRequest, ECM_EngineStatus_01

Signal naming:
  PascalCase or CamelCase with underscore separators
  Direction suffix for wheel channels: _FL, _FR, _RL, _RR
  Unit suffix when ambiguous: _Pct, _Deg, _Bar, _Nm
  E2E signals: Alive_Ctr_[MsgName], CRC_[MsgName]
  Not available value: signal_NA (comment in CM_)
```

---

## 12.8 CAN FD and Automotive Ethernet Coexistence

### When to Use Each Protocol

| Protocol | Best For | Bandwidth |
|----------|---------|-----------|
| CAN 2.0A (11-bit) | Safety-critical, short cycle | ≤1 Mbps |
| CAN 2.0B (29-bit) | J1939 heavy vehicle | ≤1 Mbps |
| CAN FD | ADAS sensor data (>8 byte frames) | ≤8 Mbps data phase |
| FlexRay | X-by-wire, deterministic ASIL-D | 10 Mbps/ch |
| LIN | Comfort actuators (switches, seats) | 20 Kbps |
| 100BASE-T1 | ADAS camera/radar, over-air updates | 100 Mbps |
| 1000BASE-T1 | Backbone Ethernet, infotainment | 1 Gbps |

### Zonal Architecture Trend (2024+)

```
Traditional Domain Architecture:     Modern Zonal Architecture:
                                      
  ADAS ECU                             Zone Controller (Front)
  Powertrain ECU   → Multiple           → CAN FD (local sensors)
  Body ECU           CAN buses          → 100BASE-T1 (to Vehicle Backbone)
  Infotainment ECU                      
                                       Zone Controller (Rear)
                                        → CAN FD + LIN
                                        
                                       Central Vehicle Computer (CVC)
                                        → 1000BASE-T1 backbone
                                        
DBC files still needed for CAN FD segments in zonal architecture
SOME/IP / DDS for Ethernet segments (different tooling)
```

---

## 12.9 Standards Interaction Summary

```
Signal lifecycle through standards:

Vehicle requirement (FMEA / ISO 26262 HARA)
    │
    ▼
ASPICE SYS.3 ──► System Architecture Doc
    │              (Network topology, ASIL assignment)
    ▼
ASPICE SWE.2 ──► DBC file (ISO 11898-1 compliant)
    │              (Communication matrix, signal encoding)
    ▼
AUTOSAR COM ──► Generated C code (signal handlers)
    │              (Factor, offset applied in software)
    ▼
ISO 26262 ──── E2E protection in DBC + firmware
    │              (CRC + alive counter per ASIL level)
    ▼
ISO 14229 ──── UDS diagnostic frames in DBC
                  (0x7E0/0x7E8 + transport protocol)
```

---

## Module 12 — Knowledge Check

1. Which ISO standard defines the CAN electrical layer (voltage levels, termination)?
2. In AUTOSAR, what is the name of the module that handles CAN signal encoding?
3. What ASIL level typically requires E2E protection with alive counter and CRC?
4. What is a PGN in SAE J1939?
5. At ASPICE CL2, what evidence is needed to demonstrate DBC version control?
6. What is the data phase bitrate range for CAN FD?

**Answers:**
1. ISO 11898-2 (HS-CAN physical layer)
2. COM Module (Communication Service Module)
3. ASIL-B (and higher: C, D)
4. Parameter Group Number — a 16-bit identifier in the J1939 29-bit CAN ID that identifies the application-layer data group (equivalent to message type)
5. DBC files under version control (Git/SVN), baseline identification, change history with ECR references, review evidence
6. Up to 8 Mbps (with 64-byte payload per frame)
