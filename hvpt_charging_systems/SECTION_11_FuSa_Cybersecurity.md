# SECTION 11 — FUNCTIONAL SAFETY & CYBERSECURITY
## ISO 26262, ISO 21434 — Complete Engineer Reference

---

## 11.1 ISO 26262 FUNCTIONAL SAFETY

### 11.1.1 ASIL Level Definitions

```
AUTOMOTIVE SAFETY INTEGRITY LEVELS (ASIL):
══════════════════════════════════════════════════════════════
ASIL levels determined by three factors:
  S = Severity     (how bad is the injury?)
  E = Exposure     (how often is hazard encountered?)
  C = Controllability (can driver mitigate?)

SEVERITY (S):
  S0 = No injuries
  S1 = Light-moderate injuries (survivable)
  S2 = Severe life-threatening injuries
  S3 = Life-threatening / fatal injuries

EXPOSURE (E):
  E0 = Incredible (almost never)
  E1 = Very low probability (< once per year per vehicle)
  E2 = Low probability (few times per year)
  E3 = Medium probability (monthly)
  E4 = High probability (daily / very common)

CONTROLLABILITY (C):
  C0 = Controllable in general
  C1 = Simply controllable (> 99% can avoid)
  C2 = Normally controllable (> 90% can avoid)
  C3 = Difficult to control or uncontrollable

ASIL DETERMINATION TABLE:
  S \ E×C  │ E1,C1 │ E1,C2 │ E1,C3 │ E2,C2 │ E2,C3 │ E3,C3 │ E4,C3
  ─────────┼───────┼───────┼───────┼───────┼───────┼───────┼──────
  S1       │  QM   │  QM   │  QM   │  QM   │  A    │  B    │  C
  S2       │  QM   │  QM   │  A    │  B    │  C    │  C    │  D
  S3       │  QM   │  A    │  B    │  C    │  C    │  D    │  D

  QM = Quality Management (no specific ISO 26262 requirements)
  ASIL A = Lowest (moderate requirements)
  ASIL B = Medium requirements
  ASIL C = High requirements
  ASIL D = Highest (strictest requirements, e.g., airbags, HV isolation)

EV POWERTRAIN ASIL EXAMPLES:
  Item                    │ ASIL │ Hazard
  ────────────────────────┼──────┼─────────────────────────
  HV isolation monitoring │  D   │ Electric shock to occupant
  Contactor welding detect│  D   │ Unintended propulsion
  Torque limit override   │  C   │ Uncontrolled acceleration
  Thermal runaway detect  │  D   │ Battery fire
  Regen braking torque    │  C   │ Loss of braking
  BMS SoC accuracy        │  B   │ Range anxiety / stranding
  OBC fault detection     │  B   │ Fire from overcharge
```

### 11.1.2 Safety Lifecycle

```
ISO 26262 V-MODEL SAFETY LIFECYCLE:
══════════════════════════════════════════════════════════════

Part 3: Concept Phase
  ├── Item Definition
  │     - What is the item? (e.g., BMS)
  │     - Boundaries, interfaces, relevant items
  │
  ├── Hazard Analysis and Risk Assessment (HARA)
  │     - Enumerate hazardous events
  │     - Assign S, E, C → ASIL
  │     - Define Safety Goals
  │
  └── Functional Safety Concept
        - Safety Goals → Functional Safety Requirements

Part 4: Product Development (System Level)
  ├── Technical Safety Concept
  │     - Functional → Technical Safety Requirements
  │     - Allocate to hardware/software
  │
  ├── System Design
  │     - Architecture, FMEA, FTA
  │     - Safe states definition
  │     - Independence requirements
  │
  └── System Integration & Testing

Part 5: Hardware Development
  └── HW design, PMHF metrics, FMEDA

Part 6: Software Development
  └── SW unit design, coding guidelines, testing

Part 7: Production, Operation, Maintenance
```

### 11.1.3 HARA Example — BMS

```
HARA TABLE: BMS (Battery Management System)
═══════════════════════════════════════════════════════════════════════════════

Item: Battery Management System
Operating Situation: Vehicle in motion, highway driving at 120 km/h

ID    │ Hazardous Event              │ S  │ E  │ C  │ ASIL │ Safety Goal
──────┼──────────────────────────────┼────┼────┼────┼──────┼──────────────────
HE-01 │ BMS fails to open contactors │ S3 │ E4 │ C3 │  D   │ SG-01: BMS shall
      │ during thermal runaway       │    │    │    │      │ open main contactors
      │                              │    │    │    │      │ within 500ms of
      │                              │    │    │    │      │ thermal runaway
──────┼──────────────────────────────┼────┼────┼────┼──────┼──────────────────
HE-02 │ BMS allows overcharge        │ S2 │ E3 │ C3 │  C   │ SG-02: BMS shall
      │ beyond 4.25V/cell            │    │    │    │      │ limit charging
      │ → fire risk                  │    │    │    │      │ voltage to max
      │                              │    │    │    │      │ allowed cell voltage
──────┼──────────────────────────────┼────┼────┼────┼──────┼──────────────────
HE-03 │ HV contactors close          │ S3 │ E2 │ C2 │  B   │ SG-03: BMS shall
      │ unexpectedly during          │    │    │    │      │ not close contactors
      │ maintenance/service          │    │    │    │      │ without valid VCU
      │                              │    │    │    │      │ ignition signal
──────┼──────────────────────────────┼────┼────┼────┼──────┼──────────────────
HE-04 │ Isolation fault undetected   │ S3 │ E3 │ C3 │  D   │ SG-04: BMS shall
      │ → HV shock to occupant       │    │    │    │      │ detect isolation
      │ during service               │    │    │    │      │ resistance < 100 Ω/V
      │                              │    │    │    │      │ and open contactors
──────┼──────────────────────────────┼────┼────┼────┼──────┼──────────────────
HE-05 │ Incorrect SoC causes         │ S1 │ E4 │ C2 │  A   │ SG-05: BMS_SoC
      │ unexpected vehicle stop      │    │    │    │      │ accuracy ±5% under
      │                              │    │    │    │      │ all operating conditions
```

### 11.1.4 Functional Safety Requirements

```
SAFETY GOALS → FUNCTIONAL SAFETY REQUIREMENTS:

Safety Goal SG-01: Open contactors within 500ms of thermal runaway

FSR-BMS-001:
  The BMS shall monitor individual cell temperatures at minimum 10ms cycle time.
  The BMS shall detect thermal runaway condition when:
    - Any cell temperature rate of change > 5°C/s
    - OR any cell temperature > 80°C
  The BMS shall open main positive and negative contactors within 500ms.
  ASIL-D requirement.

Safety Mechanism: SW1 — Independent temperature monitoring watchdog
  - SW1 runs on separate CPU core at ASIL-D
  - Checks temperature rate of change every 10ms
  - Independently commands contactor open via dedicated hardware path
  - Diagnostic coverage ≥ 99% (ASIL-D FMEDA requirement)

FSR-BMS-002:
  The BMS shall implement HV isolation monitoring with:
    - Measurement frequency ≥ 1 Hz
    - Minimum detectable resistance: 100 Ω/V × system voltage
    - For 400V system: minimum detection = 40 kΩ
    - For 800V system: minimum detection = 80 kΩ
  Upon isolation fault: BMS shall open contactors within 100ms.
  ASIL-D requirement.

Safety Mechanism: SW2 — Isolation monitoring via IMD (Isolation Monitoring Device)
  - Hardware IMD (e.g., Bender ISOMETER) provides physical output
  - BMS reads IMD output AND calculates own isolation measurement
  - Both must agree (redundant monitoring)
  - Any disagreement → fault detection → safe state
```

### 11.1.5 FMEA Example

```
FMEA: BMS Contactor Control Function

System: BMS Main Positive Contactor Driver
Function: Open/Close main positive contactor on command

ID    │ Failure Mode      │ Effect            │ S │ O │ D │ RPN │ Mitigation
──────┼───────────────────┼───────────────────┼───┼───┼───┼─────┼───────────────
FM-01 │ Driver stuck-on   │ Contactor remains │ 9 │ 3 │ 4 │ 108 │ Current feedback
      │ (hardware fault)  │ closed in fault   │   │   │   │     │ + redundant drive
      │                   │ → HV always on    │   │   │   │     │ path
──────┼───────────────────┼───────────────────┼───┼───┼───┼─────┼───────────────
FM-02 │ Driver stuck-off  │ HV bus never      │ 3 │ 2 │ 5 │  30 │ Startup self-test
      │ (open circuit)    │ energized         │   │   │   │     │ (close/open check)
──────┼───────────────────┼───────────────────┼───┼───┼───┼─────┼───────────────
FM-03 │ SW command wrong  │ Close instead of  │ 9 │ 2 │ 5 │  90 │ Redundant SW
      │ polarity          │ open on fault cmd │   │   │   │     │ with vote logic
──────┼───────────────────┼───────────────────┼───┼───┼───┼─────┼───────────────
FM-04 │ Coil driver OV    │ Contactor weld    │ 8 │ 2 │ 4 │  64 │ Voltage monitor
      │ (overvoltage)     │ (permanently on)  │   │   │   │     │ on coil driver

S = Severity (1-10), O = Occurrence (1-10), D = Detection (1-10)
RPN = Risk Priority Number = S × O × D (higher = more critical)
```

---

## 11.2 ISO 21434 AUTOMOTIVE CYBERSECURITY

### 11.2.1 Cybersecurity Overview

```
ISO 21434 SCOPE:
  Applies to E/E systems in road vehicles throughout lifecycle
  (concept, development, production, operation, maintenance, decommissioning)

KEY CONCEPTS:
  TARA — Threat Analysis and Risk Assessment
  Cybersecurity Goal — top-level security objective
  CAL — Cybersecurity Assurance Level (1–4, like ASIL)
  Attack feasibility — effort needed to mount attack
  
AUTOMOTIVE ATTACK VECTORS:
  Physical     │ OBD port, USB, SD card, debug interface
  Short-range  │ Bluetooth, WiFi, NFC, DSRC (V2X)
  Long-range   │ Cellular (4G/5G), over-the-air (OTA) updates
  Supply chain │ Malicious supplier firmware/hardware
  
KEY STANDARDS ECOSYSTEM:
  ISO 21434      — Main cybersecurity standard for vehicles
  UNECE WP.29 R155 — Cybersecurity regulation (mandatory in EU, Japan, etc.)
  SAE J3061      — Precursor to ISO 21434
  ISO/SAE 21434   — Combined standard
```

### 11.2.2 TARA — Threat Analysis and Risk Assessment

```
TARA METHODOLOGY:

STEP 1: ITEM DEFINITION
  What is the item: e.g., OBC (Onboard Charger)
  Interfaces: CAN (internal), ISO 15118 PLC (external EVSE)
  Data flows: Charge commands, billing data, SW updates

STEP 2: ASSET IDENTIFICATION
  Assets are things of value that can be compromised:
  ┌──────────────────────────────────────────────────────────────┐
  │ Asset           │ Property│ Impact if Compromised            │
  ├─────────────────┼─────────┼──────────────────────────────────┤
  │ Charge control  │ Integrity│ Battery damage, fire            │
  │ Charge limit    │ Integrity│ Overcharge, cell damage         │
  │ Billing data    │ Confidentiality│ Privacy breach, fraud    │
  │ SW update path  │ Integrity│ Malicious firmware injection    │
  │ User location   │ Confidentiality│ User tracking            │
  │ OBC availability│ Availability│ Denial of service to user   │
  └──────────────────────────────────────────────────────────────┘

STEP 3: THREAT SCENARIOS
  Threat scenario: What bad thing could happen?
  
  TS-001: Malicious EVSE sends crafted ISO 15118 messages
          → Injects incorrect current demand → battery damage
  
  TS-002: Attacker gains access to CAN bus via OBD port
          → Sends fake VCU_ChargeCurrentLimit = 0xFFFF
          → OBC charges at maximum → overcharge → fire
  
  TS-003: MITM attack on ISO 15118 TLS session
          → Modifies charge parameters
          → Vehicle charged with incorrect voltage
  
  TS-004: OTA update man-in-the-middle
          → Malicious firmware installed on BMS
          → BMS bypasses safety monitoring

STEP 4: ATTACK FEASIBILITY (LIKELIHOOD)
  Factors: Time, expertise, knowledge, window of opportunity, equipment
  
  Low (< 1 week, public info):          feasibility = HIGH
  Medium (weeks, restricted info):       feasibility = MEDIUM
  High (months, expert team, funded):    feasibility = LOW

STEP 5: IMPACT ASSESSMENT
  S = Safety impact (death/injury)
  F = Financial impact
  O = Operational impact  
  P = Privacy impact

STEP 6: RISK VALUE
  Risk = Impact × Likelihood
  CAL 4 = highest risk, requires strongest cybersecurity measures

TARA TABLE EXAMPLE:
  TS-001 │ Battery damage via malicious EVSE  │ S:High F:High │ Feasibility: Medium │ CAL 3
  TS-003 │ TLS MITM on ISO 15118             │ F:Med  O:Med  │ Feasibility: Low    │ CAL 2
  TS-004 │ OTA firmware injection            │ S:High        │ Feasibility: Low    │ CAL 4
```

### 11.2.3 Cybersecurity Goals and Requirements

```
CYBERSECURITY GOAL (from TARA):
CG-OBC-001: The OBC shall be protected against unauthorized 
            modification of charge parameters via ISO 15118 interface.

CYBERSECURITY REQUIREMENTS (from CG):
CR-OBC-001: The OBC shall validate the authenticity of all ISO 15118
            messages using TLS 1.3 with ECDSA P-256 certificates.

CR-OBC-002: The OBC shall verify the SECC certificate chain against
            a trusted root CA before accepting charge parameters.

CR-OBC-003: The OBC shall implement input validation on all received
            numeric parameters (current, voltage limits) against
            physical plausibility limits before applying.

CR-OBC-004: The OBC shall log all failed authentication attempts
            and generate DTC on repeated failures (> 3).

SECURE COMMUNICATION IMPLEMENTATION:
  ISO 15118-2 with TLS:
    - TLS 1.2 minimum (TLS 1.3 recommended)
    - Certificate: X.509 v3 ECDSA P-256
    - EVCC certificate issued by OEM PKI
    - SECC certificate issued by eMobility operator PKI
    - Certificate revocation via OCSP
    
SECURE DIAGNOSTICS:
  UDS Security Access (27 service):
    - Seed must be unpredictable (use TRNG — True Random Number Generator)
    - Key algorithm complexity ≥ 128-bit effective security
    - Failed attempt counter stored in NVM
    - Lockout after 3 failures (minimum 10-minute delay)
    - Programming session only in vehicle at rest (speed = 0)
```

### 11.2.4 Security Testing in EV Context

```
CYBERSECURITY TEST CASES FOR EV POWERTRAIN:

TC-SEC-001: UDS Brute Force Protection
  Precondition: Extended session, BMS ECU
  
  Step 1: Send 27 01 (request seed)
  Step 2: Send wrong key: 27 02 FF FF FF FF
  Step 3: Repeat wrong key 3 times
  Step 4: Verify lockout behavior
  
  Expected:
    - After 3 wrong keys: NRC 0x36 (ExceededNumberOfAttempts)
    - ECU locked for ≥ 10 minutes
    - NRC 0x37 (RequiredTimeDelayNotExpired) for all subsequent attempts

TC-SEC-002: CAN Injection Protection (OBD access)
  Precondition: Physical OBD access
  
  Step 1: Inject fake VCU_Command message with VCU_HV_Enable = 1
          from different CAN address (0x7FF instead of 0x100)
  Step 2: Monitor BMS response
  
  Expected:
    - BMS verifies message sender (if message authentication implemented)
    - Without MAC: BMS should have functional plausibility checks
    - BMS should not respond to out-of-context HV enable during standby
  
  Note: CAN injection is a known weakness. AUTOSAR SecOC (Secure Onboard
        Communication) adds MACs (Message Authentication Codes) to CAN frames.

TC-SEC-003: OTA Update Integrity Verification
  Precondition: OTA update mechanism available
  
  Step 1: Prepare valid firmware with correct signature
  Step 2: Modify firmware binary (corrupt 1 byte)
  Step 3: Attempt OTA update with corrupted firmware
  
  Expected:
    - ECU verifies cryptographic signature (RSA-2048 or ECDSA-P256)
    - ECU rejects corrupted firmware
    - DTC set: 0x0F0001 (OTA_Integrity_Failure)
    - ECU remains on previous valid firmware

TC-SEC-004: ISO 15118 TLS Certificate Validation
  Step 1: Connect to vehicle with expired SECC certificate
  Step 2: Monitor EVCC behavior
  
  Expected:
    - EVCC checks certificate validity period
    - EVCC rejects expired certificate
    - TLS handshake fails
    - Charging session does not start
    - Alert logged in DTC or secure event log

AUTOSAR SecOC OVERVIEW:
  CAN messages can include a Message Authentication Code (MAC):
  
  Normal CAN frame:
    [ID][Data 8 bytes]
  
  SecOC frame:
    [ID][Data 4-6 bytes][FreshnessBits 2-4 bits][MAC 24-28 bits]
  
  MAC calculation:
    MAC = CMAC-AES-128(Key, FreshnessValue || MessageID || Data)
  
  Protection:
    - Replay attack prevention (freshness counter)
    - Authentication (only nodes with key can create valid MAC)
    - Integrity (any data modification invalidates MAC)
```

---

## 11.3 SAFE STATE DEFINITION

```
EV POWERTRAIN SAFE STATES:
══════════════════════════════════════════════════════════════

Safe State 1: HV Isolation Safe State
  Trigger: Isolation fault detected by IMD
  Actions:
    - Open main positive contactor
    - Open main negative contactor
    - Set BMS_Status = FAULT
    - Set BMS_FaultCode bit 4 (isolation fault)
    - Illuminate MIL (malfunction indicator lamp)
    - Log DTC 0x0D0002 (isolation fault)
  Vehicle behavior: Immediate propulsion disable, limp home on 12V

Safe State 2: Thermal Runaway Safe State
  Trigger: Cell temperature rate > 5°C/s OR T > 80°C
  Actions (within 500ms):
    - Open all HV contactors
    - Command cooling system maximum
    - Activate battery fire detection
    - Send emergency CAN message to BCM (body control module)
    - Trigger visible/audible alarm
  Vehicle behavior: Full propulsion disable, fire warning

Safe State 3: Contactor Weld Safe State
  Trigger: Contactor feedback doesn't match command
  Actions:
    - Open redundant parallel contactor path
    - Isolate DC bus via pyrofuse (irreversible)
    - Set persistent DTC (requires workshop reset)
  Vehicle behavior: Drive disabled until repaired

Safe State 4: Communication Loss Safe State (BMS timeout)
  Trigger: VCU stops receiving BMS_Status for > 50ms
  Actions:
    - VCU commands 0 torque
    - VCU commands 0 charge current
    - Set DTC (communication timeout)
  Vehicle behavior: Gradual torque ramp-down, limp mode
  Recovery: Resume when BMS messages return

SAFE STATE TESTING:
  For each safe state: inject trigger condition
  Verify correct action sequence and timing
  Verify DTC set, correct signal values on CAN
```

---

## 11.4 ISO 26262 VERIFICATION & VALIDATION

```
V&V ACTIVITIES PER ISO 26262:

PART 8 — Supporting Processes:
  Verification    = Did we build it right?
  Validation      = Did we build the right thing?

SAFETY VALIDATION PLAN:
  For each Safety Goal, define:
  1. How do we validate compliance?
  2. What evidence is required?
  3. What pass/fail criteria?

EXAMPLE — Safety Goal SG-01 Validation:
  Goal: Open contactors within 500ms of thermal runaway
  
  Test setup:
    - HIL with battery thermal model
    - Inject thermal runaway: cell temp rate = 6°C/s
    - Measure time from trigger to contactor open signal
  
  Evidence required:
    - Test report showing response time < 500ms
    - Formal review by safety assessor
    - FMEDA showing diagnostic coverage ≥ 99%
    - Code coverage ≥ 100% MC/DC for safety function

CODING GUIDELINES (ISO 26262 Part 6):
  ASIL-B and above must follow:
  - Defensive programming
  - No dynamic memory allocation in safety functions
  - No recursion in safety functions
  - Stack depth analysis
  - Compiler warnings treated as errors
  - MISRA C compliance (Part 6, Table 1)
  - MC/DC code coverage (branch + condition)
```

---

## SECTION 11 SUMMARY

| Standard | Application | Key EV Topics |
|----------|-------------|---------------|
| ISO 26262 | Functional Safety | ASIL D for HV isolation, contactors, thermal |
| ISO 21434 | Cybersecurity | TARA, CAN SecOC, OTA security |
| IEC 61508 | Base safety standard | Foundation for ISO 26262 |
| UNECE R155 | Cybersecurity regulation | Mandatory in EU since 2022 |

ASIL-D items in EV: HV isolation monitoring, contactor welding detection, thermal runaway detection.
CAL-4 cybersecurity: OTA firmware update, ISO 15118 communication.

---

*Next: Section 12 — OEM Case Studies*
