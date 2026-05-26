# SECTION 2 — AUTOMOTIVE SYSTEMS ENGINEERING PROCESS
## V-Model Lifecycle, Requirements Engineering, JAMA, DOORS

---

## 2.1 AUTOMOTIVE V-MODEL LIFECYCLE

### 2.1.1 V-Model Overview

```
AUTOMOTIVE V-MODEL DEVELOPMENT PROCESS:
═════════════════════════════════════════════════════════════════════

LEFT SIDE (Development)                    RIGHT SIDE (Verification)
─────────────────────────────              ────────────────────────────────
Vehicle Feature Requirements  ─────────────► System Validation Testing
         │                    (Acceptance)                 │
         ▼                                                  │
System Requirements Spec  ──────────────► System Integration Testing
         │                  (Integration)                   │
         ▼                                                  │
Software/HW Architecture  ──────────────► Component Integration Testing
         │                                                  │
         ▼                                                  │
SW Module Specifications  ──────────────► Unit/Module Testing
         │                                                  │
         ▼                                                  │
    ────────────────────────────────────────────────────────
               CODE IMPLEMENTATION (Bottom of V)
    ────────────────────────────────────────────────────────

VERIFICATION activities: Did we build it right?
VALIDATION activities: Did we build the right thing?
```

### 2.1.2 V-Model Phases Explained

| Phase | Owner | Inputs | Outputs | Tools |
|-------|-------|--------|---------|-------|
| Vehicle Feature Requirements | Product Management | Customer needs, market analysis | VFR documents | JAMA, Confluence |
| System Requirements Spec | Systems Engineering | VFR | SysRS, ICD | DOORS, JAMA |
| Software Architecture | Software Architects | SysRS | SW architecture doc | Enterprise Architect |
| Module Design | SW Developers | Architecture | Low-level design | Polarion, DOORS |
| Implementation | SW Developers | Design | Source code | IDE, compilers |
| Unit Testing | SW Dev/Test | Module specs | Test results | Unit test framework |
| Component Integration | Integration Eng | Architecture | Integration test results | CANoe, HIL |
| System Integration Testing | Systems/Test Eng | SysRS | SIT results | CANoe, HIL, Real Vehicle |
| System Validation | Validation Eng | VFR | Validation evidence | Vehicle test, CANoe |

---

## 2.2 REQUIREMENT ELICITATION

### 2.2.1 Sources of Requirements

```
REQUIREMENT SOURCES (EV Powertrain project):
───────────────────────────────────────────────────────────────
1. Customer/Market Requests:
   - Range requirements (e.g., 500 km WLTP)
   - Charging speed requirements (0→80% < 30 min)
   - Performance requirements (0–100 km/h < 4.5s)
   - Feature requests (V2G, thermal preconditioning)

2. Standards and Regulations:
   - ISO 15118 — EV charging communication
   - IEC 61851 — Charging equipment
   - UNECE R100 — EV safety
   - FMVSS 305 — Crash energy storage systems

3. OEM System-Level Architecture:
   - HV voltage range (400V vs 800V platform)
   - Packaging constraints
   - Connector standards

4. Supplier/Component Constraints:
   - BMS cell chemistry limits
   - Inverter switching frequency
   - Motor thermal capability

5. Heritage / Carry-over:
   - Previous platform requirements
   - Known issues from previous generation
```

### 2.2.2 Requirement Writing Guidelines (INCOSE / EARS)

**Good Requirement Characteristics (SMART):**
- **Specific** — Unambiguous, single sentence
- **Measurable** — Quantifiable with acceptance criteria
- **Achievable** — Technically feasible
- **Relevant** — Traceable to vehicle need
- **Testable** — Can be verified by a test

**EARS (Easy Approach to Requirements Syntax):**
```
Ubiquitous:     The [system] shall [function].
Event-driven:   WHEN [event], the [system] shall [function].
State-driven:   WHILE [state], the [system] shall [function].
Conditional:    IF [condition], THEN the [system] shall [function].
Optional:       WHERE [feature included], the [system] shall [function].
```

---

## 2.3 VEHICLE FEATURE REQUIREMENTS (VFR) — EXAMPLES

### VFR-001: DC Fast Charging Performance

```
Document: Vehicle Feature Requirements
Feature:  DC Fast Charging
ID:       VFR-EV-CHG-001

Title: DC Fast Charging Time Requirement

Requirement:
WHEN the vehicle is connected to a CCS-compliant DC fast charger
AND the ambient temperature is between 0°C and 40°C
AND the battery SoC is below 20%,
THEN the vehicle shall achieve charging from 20% SoC to 80% SoC
     within 30 minutes at a charger output of 150 kW or greater.

Priority: Must Have
Source: Customer Requirement CR-2025-447
Standard: IEC 62196-3, ISO 15118-2
Acceptance Criteria:
  - Test at 0°C, 23°C, 40°C ambient
  - Charger rated ≥ 150 kW
  - Measured from charger start signal to BMS_SoC = 80%
  - Time ≤ 30 minutes in all conditions

Status: Approved
Owner: Systems Engineering — EV Powertrain
Revision: 1.2
```

### VFR-002: Regenerative Braking Energy Recovery

```
ID: VFR-EV-REGEN-001

Title: Regenerative Braking Minimum Recovery

Requirement:
WHILE the vehicle is in DRIVE mode
AND vehicle speed is between 15 km/h and 120 km/h
AND the BMS_SoC is below 95%,
THEN the regenerative braking system shall recover
     a minimum of 70% of the kinetic energy during normal deceleration
     (defined as deceleration rate ≤ 0.2g).

Priority: Must Have
Source: OEM Fuel Economy Strategy
Standard: WLTP measurement protocol
```

### VFR-003: Cold Weather Charging

```
ID: VFR-EV-THERM-001

Title: Battery Pre-Heating for Cold Temperature Charging

Requirement:
WHEN the battery temperature is below 5°C
AND a scheduled charging session is programmed,
THEN the vehicle shall automatically pre-heat the battery pack
     to a minimum temperature of 15°C before initiating charging,
     without user intervention required.

Priority: Should Have
Source: Customer satisfaction survey (cold climate markets)
```

---

## 2.4 SYSTEM REQUIREMENTS SPECIFICATION (SysRS) — EXAMPLES

### SysRS-BMS-001: Cell Voltage Monitoring

```
Document: System Requirements Specification — Battery Management System
ID: SysRS-BMS-001

Title: Cell Voltage Monitoring Accuracy

Requirement:
The BMS shall measure individual cell voltages with an accuracy of
±5 mV across the operating temperature range of −40°C to +85°C
(electronic operating temperature range).

Derived From: VFR-EV-BAT-002
Component: Battery Management System
Interface: Cell Monitoring ICs (isoSPI interface)
Verification Method: Test
Acceptance Criteria:
  - Apply reference voltage at BMS input terminals
  - Measure BMS reported voltage
  - Error ≤ ±5 mV at 0°C, 25°C, 85°C, −40°C
  - Over cell range: 2.5V – 4.35V

Status: Released
Revision: 2.0
```

### SysRS-INV-001: Torque Response Time

```
ID: SysRS-INV-001

Title: Torque Response Time

Requirement:
WHEN the VCU transmits a torque request step change of 100 Nm,
THEN the inverter shall achieve 90% of the requested torque
     within 50 ms from receipt of the CAN torque request message.

Derived From: VFR-EV-PERF-001 (0–100 km/h performance)
Verification Method: Test (HIL + Vehicle)
Acceptance Criteria:
  - Step change from 0 Nm to 100 Nm torque request
  - Motor speed: 1000 RPM, 3000 RPM, 6000 RPM test points
  - 90% torque achieved ≤ 50 ms
  - Measured by resolver and current sensor
```

### SysRS-VCU-001: Precharge Sequence Timing

```
ID: SysRS-VCU-001

Title: HV Precharge Sequence Timeout

Requirement:
The VCU shall initiate the HV precharge sequence within 200 ms of
receiving the IGNITION_ON signal.
The precharge sequence shall complete within 3 seconds.
IF the precharge does not complete within 3 seconds,
THEN the VCU shall abort the precharge, set DTC P0AF0,
     and transition to FAULT state.

Derived From: Safety Goal SG-003
Verification Method: Test
```

---

## 2.5 ECU REQUIREMENT DOCUMENT — EXAMPLE

### ECU Requirement: BMS Communication

```
Document: ECU Requirements — BMS
ID: ECU-BMS-CAN-001

Title: BMS CAN Transmission Rate — Status Message

Requirement:
The BMS shall transmit the BMS_Status CAN message (ID: 0x310)
at a cyclic rate of 10 ms ± 1 ms under all operating conditions
when the CAN network is in Normal Communication mode.

Rationale: VCU requires current battery status at 10ms for
           torque control loop stability.

Verification Method: Test + Measurement (CANoe timing measurement)
Acceptance Criteria:
  - Record 1000 consecutive BMS_Status messages
  - Calculate mean period: 10 ms ± 0.5 ms
  - Maximum jitter: ±1 ms
  - No message missing for > 50 ms (detected as timeout)

Related: AUTOSAR COM module configuration, OS task assignment
```

---

## 2.6 REQUIREMENT TRACEABILITY MATRIX (RTM)

```
REQUIREMENT TRACEABILITY MATRIX — EV Charging System
═══════════════════════════════════════════════════════════════════════════════════
VFR ID          │ SysRS ID       │ SW/HW Req ID  │ Test Case ID   │ Result
───────────────────────────────────────────────────────────────────────────────────
VFR-EV-CHG-001  │ SysRS-OBC-001  │ ECU-OBC-001   │ TC-CHG-001     │ PASS
(DC Fast Charge │ SysRS-BMS-005  │ ECU-BMS-005   │ TC-CHG-002     │ PASS
 timing)        │ SysRS-EVCC-001 │ ECU-EVCC-001  │ TC-CHG-003     │ PASS
                │                │               │ TC-CHG-004     │ IN REVIEW
───────────────────────────────────────────────────────────────────────────────────
VFR-EV-REGEN-001│ SysRS-MCU-003  │ ECU-MCU-003   │ TC-REGEN-001   │ PASS
(Regen braking) │ SysRS-VCU-005  │ ECU-VCU-010   │ TC-REGEN-002   │ FAIL
                │                │               │ TC-REGEN-003   │ PASS
───────────────────────────────────────────────────────────────────────────────────
VFR-EV-THERM-001│ SysRS-TCU-001  │ ECU-TCU-001   │ TC-THERM-001   │ NOT RUN
(Cold charging) │ SysRS-BMS-010  │ ECU-BMS-010   │ TC-THERM-002   │ NOT RUN
═══════════════════════════════════════════════════════════════════════════════════
Coverage: 8/10 test cases executed, 6 PASS, 1 FAIL, 1 IN REVIEW
```

---

## 2.7 INTERFACE CONTROL DOCUMENT (ICD)

### 2.7.1 ICD Purpose

The ICD defines ALL interfaces between two systems or ECUs:
- Physical connections (connectors, pinout)
- Communication interfaces (CAN messages, signals)
- Power interfaces (voltage levels, current limits)
- Environmental interfaces (temperature range)
- Mechanical interfaces (mounting, dimensions)

### 2.7.2 ICD Example — VCU to BMS Interface

```
INTERFACE CONTROL DOCUMENT
Interface:    VCU ↔ BMS
Document ID:  ICD-VCU-BMS-001
Version:      3.1
Date:         2026-01-15

═══════════════════════════════════════════════════════════
SECTION 1: PHYSICAL INTERFACE
═══════════════════════════════════════════════════════════
Connector (VCU side): MQS Connector, 32-pin, Part# ABC-12345
Connector (BMS side): MQS Connector, 32-pin, Part# ABC-12346

Pin Assignment (CAN interface):
  Pin 12: CAN2_H (Powertrain CAN High)  — 2.5V nominal
  Pin 13: CAN2_L (Powertrain CAN Low)   — 2.5V nominal
  Pin 11: CAN2_GND                      — 0V
  
  Pin 14: CAN3_H (Diagnostics CAN High)
  Pin 15: CAN3_L (Diagnostics CAN Low)

═══════════════════════════════════════════════════════════
SECTION 2: CAN INTERFACE DEFINITION
═══════════════════════════════════════════════════════════
Network:    Powertrain CAN (CAN2)
Baud Rate:  500 kbit/s
BRS (FD):   2 Mbit/s (when CAN FD enabled)
Termination: 120Ω at VCU, 120Ω at PDU (network ends)

MESSAGES — VCU → BMS (VCU is sender):
┌──────────────────────────────────────────────────────────┐
│ Message: VCU_Command                                      │
│ ID:      0x100 (11-bit)                                  │
│ DLC:     8 bytes                                         │
│ Cycle:   10 ms                                           │
│ Signals:                                                 │
│  ├── VCU_HV_Enable     [Bit 0,     Length 2]  Enum       │
│  │     0=OFF, 1=ON, 2=PRECHARGE, 3=FAULT_RQST           │
│  ├── VCU_ChgEnable     [Bit 2,     Length 1]  Bool       │
│  ├── VCU_MaxChgCurrent [Byte 2–3,  Length 16] 0.1A/bit  │
│  ├── VCU_TargetVoltage [Byte 4–5,  Length 16] 0.1V/bit  │
│  └── VCU_DrvMode       [Byte 1,bit4 Length 3] Enum       │
│        0=ECO, 1=NORMAL, 2=SPORT, 3=REGEN_MAX             │
└──────────────────────────────────────────────────────────┘

MESSAGES — BMS → VCU (BMS is sender):
┌──────────────────────────────────────────────────────────┐
│ Message: BMS_Status                                       │
│ ID:      0x310 (11-bit)                                  │
│ DLC:     8 bytes                                         │
│ Cycle:   10 ms                                           │
│ Signals: [see Section 1.2.3 for full signal list]        │
└──────────────────────────────────────────────────────────┘
│ Message: BMS_CellData                                     │
│ ID:      0x311 (11-bit)                                  │
│ DLC:     8 bytes                                         │
│ Cycle:   100 ms                                          │
│ Signals:                                                 │
│  ├── BMS_MaxCellVoltage [Bytes 0–1] 1mV/bit, offset 0   │
│  ├── BMS_MinCellVoltage [Bytes 2–3] 1mV/bit, offset 0   │
│  ├── BMS_MaxCellTemp    [Byte 4]    1°C/bit, offset -40  │
│  ├── BMS_MinCellTemp    [Byte 5]    1°C/bit, offset -40  │
│  ├── BMS_AvgCellVolt    [Bytes 6–7] 1mV/bit, offset 0   │

═══════════════════════════════════════════════════════════
SECTION 3: TIMING REQUIREMENTS
═══════════════════════════════════════════════════════════
BMS_Status cyclic period:     10 ms ± 1 ms
BMS timeout detection (VCU):  50 ms (5 missing messages)
VCU_Command cyclic period:    10 ms ± 1 ms
BMS timeout (VCU command):    50 ms
```

---

## 2.8 JAMA WORKFLOW (Requirements Management)

### 2.8.1 JAMA Concepts

| Term | Definition |
|------|-----------|
| Item | Any requirement, test case, feature, or risk |
| Item Type | Category: Feature, Story, System Req, Test Case, Risk |
| Project | Container for a product or system |
| Set | Organized collection of items |
| Review | Formal review process for approving items |
| Relationship | Links between items (derives, refines, satisfies, verifies) |
| Baseline | Snapshot of approved requirements |

### 2.8.2 JAMA Workflow — EV Feature Development

```
JAMA WORKFLOW:
──────────────────────────────────────────────────────────────
STEP 1: Create Feature
  Product Manager creates Feature item in JAMA:
  Type: Feature
  Title: "DC Fast Charging — CCS Combo 2"
  Description: [Customer need description]
  Priority: Must Have
  Release: Program_MY2027

STEP 2: Decompose to System Requirements
  Systems Engineer creates SysRS items:
  Type: System Requirement
  Derived From: [link to Feature]
  Items: SysRS-OBC-001, SysRS-BMS-005, SysRS-EVCC-001, ...

STEP 3: Software/Hardware Requirements
  ECU Owner creates ECU requirements:
  Derived From: [link to SysRS item]

STEP 4: Test Case Creation
  Test Engineer creates Test Case items:
  Type: Test Case
  Verifies: [link to SysRS item]
  Test Steps, Expected Results, Pass/Fail Criteria

STEP 5: Review
  Requirements Review meeting
  Status changes: DRAFT → IN_REVIEW → APPROVED
  
STEP 6: Baseline
  Approved set → Baseline created for release
  Baseline ID: BL-MY2027-CHG-001

STEP 7: Change Management
  Any change → Change Request → Impact Analysis → Approval
  Version control: all changes tracked with justification
```

### 2.8.3 Requirement Status States (JAMA)

```
DRAFT → IN_REVIEW → APPROVED → RELEASED → OBSOLETE
                       │
                  REJECTED → REWORK → DRAFT
```

---

## 2.9 DOORS WORKFLOW (IBM DOORS)

### 2.9.1 DOORS Structure

```
DOORS DATABASE STRUCTURE:
──────────────────────────────────────
Project: EV_Powertrain_MY2027
├── Folder: Vehicle Features
│   └── Module: VFR_EV_Powertrain (formal module)
├── Folder: System Requirements
│   ├── Module: SysRS_BMS
│   ├── Module: SysRS_Inverter
│   ├── Module: SysRS_OBC
│   └── Module: SysRS_VCU
├── Folder: ECU Requirements
│   ├── Module: ECU_BMS
│   ├── Module: ECU_MCU
│   └── Module: ECU_OBC
├── Folder: Test Cases
│   ├── Module: TC_Charging
│   ├── Module: TC_Battery
│   └── Module: TC_Powertrain
└── Folder: Traceability
    └── Module: RTM_Overview
```

### 2.9.2 DOORS DXL Scripting (Common)

```dxl
// DXL Script: Export requirements to Excel
Module m = edit("\\EV_Powertrain_MY2027\\SysRS_BMS", false)
Object o
string id, req, status
for o in m do {
    id     = o."Object ID" ""
    req    = o."Object Text" ""
    status = o."Status" ""
    print id "\t" req "\t" status "\n"
}
close(m)
```

---

## 2.10 FUNCTIONAL REQUIREMENTS vs NON-FUNCTIONAL

### 2.10.1 Functional Requirements

Describe WHAT the system does (behavior):

```
FR-001: The BMS shall transmit cell voltage data every 10 ms.
FR-002: The VCU shall issue a torque request within 20 ms of receiving
        an accelerator pedal signal change.
FR-003: The OBC shall initiate charging within 5 seconds of receiving
        a valid pilot signal from the EVSE.
```

### 2.10.2 Non-Functional Requirements

Describe HOW WELL the system does it (quality):

```
NFR-001 (Performance): BMS_SoC estimation shall have an accuracy
                        of ±3% across all operating conditions.

NFR-002 (Reliability):  The BMS shall have a MTBF of > 100,000 hours
                         in normal automotive operating conditions.

NFR-003 (Safety):       In the event of any single-point hardware fault,
                         the BMS shall open the main contactors within 100 ms.

NFR-004 (Availability): The EV charging system shall be available for
                         use within 2 seconds of key-on event.

NFR-005 (Maintainability): All DTC codes shall be accessible via
                            standard UDS diagnostic interface (ISO 14229).
```

---

## 2.11 ACCEPTANCE CRITERIA EXAMPLES

### 2.11.1 Acceptance Criteria Format

```
Feature: Battery State of Charge Display
ID: AC-HMI-SOC-001

Given: Vehicle is in READY or DRIVE state
And:   BMS is transmitting BMS_Status message
When:  BMS_SoC signal value changes by ≥ 1%
Then:  Instrument cluster shall update SoC display within 500 ms
And:   Displayed value shall match BMS_SoC ± 1%
And:   If BMS_SoC ≤ 10%, low battery warning shall illuminate

Test Method: HIL test with CAN signal injection
Pass Criteria: All AND conditions met in ≥ 99/100 test repetitions
```

---

## 2.12 V-MODEL TESTING LEVELS

### 2.12.1 Software Unit Testing (SWUT)

```
Level: Module/Function level
Tools: Google Test, Unity, LDRA TBrun
Input: SW Module Specification
Test: Individual functions, branches, statements
Coverage: Line, branch, MC/DC (for ASIL B/D)

Example:
  Function: calculate_SoC(float current, float prev_SoC)
  Test Cases:
    - Normal current (positive = discharge): SoC decreases
    - Negative current (charge): SoC increases
    - Zero current: SoC unchanged
    - Overflow: SoC clamps at 100%
    - Underflow: SoC clamps at 0%
```

### 2.12.2 Software Integration Testing (SIT)

```
Level: Multiple modules integrated
Tools: SIL (Software In the Loop), CANoe with simulation
Input: SW Architecture
Test: Module interactions, CAN communication, state machines
```

### 2.12.3 Hardware-in-the-Loop (HIL) Testing

```
Level: ECU hardware connected to simulated vehicle
Tools: dSPACE, National Instruments, ETAS LABCAR
Input: System Requirements, Integration requirements
Test: Full ECU behavior with realistic signals and timing
Environment: Temperature chambers, battery simulators

Typical HIL setup for BMS:
  Real BMS ECU ← CAN bus → HIL simulator
  HIL simulates: cell voltages, temperatures, current sensor
  HIL simulates: VCU, MCU, Inverter CAN messages
  Test cases run automatically via CANoe test module
```

### 2.12.4 Vehicle Validation Testing (VVT)

```
Level: Complete vehicle
Tools: CANoe with vehicle adapter, ETAS INCA, XCP logging
Input: Vehicle Feature Requirements
Test: End-to-end vehicle behavior
Environment: Proving ground, climatic chambers, real roads

Key validation activities:
  - Charging validation (real EVSE/charger stations)
  - Performance validation (acceleration, range)
  - Thermal validation (hot weather, cold weather)
  - Safety validation (crash, interlock)
  - Regulatory homologation testing
```

---

## 2.13 RELEASE MANAGEMENT

### 2.13.1 Software Release Process

```
RELEASE GATE CRITERIA:
──────────────────────────────────────────────────
Gate 1: Development Complete
  ✓ All planned features implemented
  ✓ Unit test coverage ≥ 80% (ASIL-B: MC/DC)
  ✓ Static analysis clean (MISRA-C compliant)

Gate 2: Integration Complete
  ✓ All SIT test cases executed
  ✓ No open critical/major defects
  ✓ CAN communication verified (all messages/signals)

Gate 3: HIL Testing Complete
  ✓ All HIL test cases passed
  ✓ Requirements coverage ≥ 95%
  ✓ Performance metrics verified

Gate 4: Vehicle Validation
  ✓ All vehicle feature requirements verified
  ✓ No open S1/S2 (critical/high) bugs
  ✓ Homologation tests passed

Gate 5: Production Release
  ✓ Safety documentation complete (ISO 26262)
  ✓ PPAP/APQP approved (Tier-1 supplier)
  ✓ Customer sign-off
```

### 2.13.2 Release Artifacts

| Artifact | Description |
|---------|-------------|
| Software Release Note | SW version, changes, known issues |
| Test Report | All test results with evidence |
| Requirements Coverage Report | RTM showing coverage % |
| DTC List | All diagnostic codes for release |
| Calibration Data | Parameter values for production |
| DBC File | CAN database for released version |
| ARXML | AUTOSAR system description |
| Safety Case | ISO 26262 safety evidence |

---

## SECTION 2 SUMMARY

The Automotive V-Model provides a disciplined approach to:
1. **Requirement Management**: VFR → SysRS → ECU Requirements with full traceability
2. **Interface Definition**: ICD documents ensure no ambiguity between ECU owners
3. **Testing Coverage**: Every requirement has a test case, measured via RTM
4. **Release Gates**: Quality cannot be bypassed — each gate must be cleared
5. **Tools**: JAMA for agile requirement management, DOORS for formal requirement control

Key documents to know:
- **VFR**: Customer-facing feature requirements
- **SysRS**: Technical system requirements
- **ICD**: Interface definition between systems
- **RTM**: Traceability from feature to test result

---

*Next: Section 3 — Automotive Communication Networks*
