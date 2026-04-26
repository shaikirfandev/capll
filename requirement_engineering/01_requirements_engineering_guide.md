# Requirements Engineering in Automotive — Complete Guide

---

## Table of Contents

1. [What is Requirements Engineering in Automotive?](#1-what-is-requirements-engineering-in-automotive)
2. [Requirement Hierarchy: Stakeholder → System → SW → HW](#2-requirement-hierarchy)
3. [Requirement Types](#3-requirement-types)
4. [EARS Notation — 5 Patterns with Automotive Examples](#4-ears-notation)
5. [Writing Good Requirements: SMART Criteria](#5-writing-good-requirements)
6. [Common Requirement Anti-patterns](#6-common-requirement-anti-patterns)
7. [Requirements Traceability](#7-requirements-traceability)
8. [Tools Overview](#8-tools-overview)
9. [Change Impact Analysis](#9-change-impact-analysis)
10. [Requirement Reviews](#10-requirement-reviews)
11. [Interface Control Document (ICD)](#11-interface-control-document-icd)
12. [5 STAR Scenarios](#12-5-star-scenarios)
13. [15 Interview Q&A](#13-15-interview-qa)

---

## 1. What is Requirements Engineering in Automotive?

Requirements Engineering (RE) is the disciplined process of **eliciting, documenting, analysing, validating, and managing requirements** throughout the product lifecycle.

In automotive, RE is mandated by:

| Standard | Requirement Process |
|----------|-------------------|
| **ASPICE** | SYS.2 (System Requirements), SWE.1 (SW Requirements) |
| **ISO 26262** | Safety requirements for ASIL-classified items |
| **ISO 21434** | Cybersecurity requirements |
| **AUTOSAR** | Software component interface requirements |

### Why RE is Critical in Automotive

- A poorly written requirement discovered in testing costs **100×** more to fix than at requirements phase
- Ambiguous safety requirements can trigger recalls (e.g., misunderstood activation threshold for AEB)
- Multi-ECU systems require precise interface requirements to avoid integration failures
- Tier 1 suppliers deliver software to OEMs — traceability is audited and contractually required

---

## 2. Requirement Hierarchy

Automotive requirements follow a strict top-down derivation chain:

```
┌────────────────────────────────────────────────────────────────┐
│  STAKEHOLDER REQUIREMENTS (StRS)                               │
│  Source: OEM, regulators (UNECE, NHTSA), end customer          │
│  Example: "The vehicle shall alert the driver when a           │
│           forward collision is imminent."                       │
└──────────────────────────┬─────────────────────────────────────┘
                           │ derives
┌──────────────────────────▼─────────────────────────────────────┐
│  SYSTEM REQUIREMENTS (SyRS)                                    │
│  Source: System architect, safety engineer                     │
│  Example: "The FCW system shall issue a visual and audible     │
│            alert within 500 ms of detecting TTC < 2.5 s."     │
└──────────┬────────────────────────────────┬────────────────────┘
           │ allocates to SW                 │ allocates to HW
┌──────────▼──────────────┐      ┌──────────▼──────────────────┐
│  SW REQUIREMENTS (SwRS) │      │  HW REQUIREMENTS (HwRS)     │
│  ASPICE SWE.1           │      │  Sensor spec, ECU power     │
│  Example: FCW Algorithm │      │  Example: Radar min range   │
│  shall output alert     │      │  = 0.5 m, max range = 200 m │
│  signal on CAN ID 0x3A0 │      │                             │
└──────────┬──────────────┘      └─────────────────────────────┘
           │ derived into
┌──────────▼──────────────────────────────────────────────────────┐
│  SW MODULE / COMPONENT REQUIREMENTS                             │
│  Example: FCW_AlertManager shall set AlertActive = TRUE         │
│           when FCW_Risk_Level > THRESHOLD_HIGH for > 200 ms     │
└──────────┬──────────────────────────────────────────────────────┘
           │ verified by
┌──────────▼──────────────────────────────────────────────────────┐
│  TEST CASES                                                     │
│  Unit test, Integration test, HIL test, Vehicle test            │
└─────────────────────────────────────────────────────────────────┘
```

### Key ASPICE Processes

- **SYS.2**: System Requirements Analysis — allocated, consistent, complete, unambiguous
- **SWE.1**: SW Requirements Analysis — derives from SYS requirements
- **SWE.4**: SW Unit Verification — traces to SWE.3 (detailed design) and SWE.1
- **SYS.4**: System Integration & Verification Test — traces to SYS.2

---

## 3. Requirement Types

### 3.1 Functional Requirements

Define **what** the system shall do — observable behaviour.

> "The AEB system shall apply maximum braking when TTC falls below 1.5 seconds and the driver has not responded."

### 3.2 Non-Functional Requirements (Quality Requirements)

Define **how well** the system performs — performance, reliability, usability.

> "The FCW algorithm shall process radar data within 10 ms cycle time."
> "The ECU shall have a boot time of less than 500 ms."

### 3.3 Safety Requirements (Functional Safety — ISO 26262)

Derived from Hazard Analysis and Risk Assessment (HARA). Classified by ASIL (A–D).

> "[ASIL C] The AEB system shall not activate unintentionally while the vehicle is stationary."

Safety requirements must always state:
- ASIL level
- Safe state
- Fault tolerance time interval (FTTI)

### 3.4 Interface Requirements

Define the **signals, protocols, and connections** between components or ECUs.

> "The AEB ECU shall receive vehicle speed on CAN bus via signal VehicleSpeed_kph on message ID 0x100, DLC 8, at 10 ms cycle rate."

ICDs (Interface Control Documents) capture these formally.

### 3.5 Performance Requirements

Response time, throughput, computational load, memory usage.

> "The object fusion algorithm shall process up to 64 simultaneous tracked objects within one 20 ms cycle."

### 3.6 Environmental Requirements

Operating conditions: temperature, vibration, EMC, IP rating.

> "The ECU shall operate correctly within an ambient temperature range of −40°C to +85°C."
> "The ECU shall comply with CISPR 25 Class 5 for electromagnetic emissions."

---

## 4. EARS Notation

**EARS (Easy Approach to Requirements Syntax)** was developed to reduce requirement ambiguity by providing structured templates.

Reference: *Mavin, A., Wilkinson, P., et al. (2009). Easy Approach to Requirements Syntax (EARS).*

### Pattern 1 — Ubiquitous (Always Active)

**Template**: `The <system> shall <action>.`

Used for requirements that apply at all times, with no trigger condition.

**Automotive Examples**:
- "The Gateway ECU shall forward all CAN messages from the powertrain bus to the diagnostic bus."
- "The instrument cluster shall display the current vehicle speed in km/h."
- "The ECU software shall store all diagnostic trouble codes (DTCs) in non-volatile memory."

---

### Pattern 2 — Event-Driven

**Template**: `When <trigger>, the <system> shall <action>.`

Used when the requirement is triggered by a discrete event or signal change.

**Automotive Examples**:
- "When the ignition is switched ON, the BCM shall initialise all body control outputs within 200 ms."
- "When vehicle speed exceeds 180 km/h, the ECU shall limit throttle input to 80% of maximum."
- "When a DTC is set, the ECU shall illuminate the malfunction indicator lamp (MIL) within one drive cycle."
- "When SeatbeltFastened transitions from TRUE to FALSE while speed > 5 km/h, the BCM shall trigger the seatbelt reminder chime."

---

### Pattern 3 — State-Driven

**Template**: `While <state>, the <system> shall <action>.`

Used when the requirement applies continuously during a specific system state.

**Automotive Examples**:
- "While the AEB system is in ACTIVE state, the FCW algorithm shall evaluate TTC every 20 ms."
- "While the vehicle is in REVERSE gear, the parking camera system shall display the rear-view image on the HMI screen."
- "While battery State of Charge (SoC) is below 15%, the BMS shall inhibit high-power loads above 5 kW."
- "While engine coolant temperature exceeds 110°C, the ECU shall activate the cooling fan at maximum duty cycle."

---

### Pattern 4 — Optional Feature

**Template**: `Where <feature is included>, the <system> shall <action>.`

Used for requirements that apply only when an optional feature or configuration is present.

**Automotive Examples**:
- "Where the vehicle is equipped with adaptive cruise control (ACC), the ECU shall maintain the set following distance in Stop-and-Go traffic."
- "Where night vision capability is installed, the camera ECU shall process IR sensor data at 30 fps."
- "Where the vehicle variant includes a panoramic sunroof, the BCM shall prevent sunroof operation when ambient temperature exceeds 75°C at the glass sensor."

---

### Pattern 5 — Unwanted Behaviour

**Template**: `If <precondition/trigger>, the <system> shall <safety action>.`

Used to specify how the system shall handle unwanted, erroneous, or hazardous conditions.

**Automotive Examples**:
- "If the radar sensor fails self-test during boot, the AEB ECU shall set DTC P1A00 and disable the AEB function."
- "If CAN communication to the brake ECU is lost for more than 100 ms, the ADAS controller shall revert to driver-only mode and issue a driver warning."
- "If SoC exceeds 98% during regenerative braking, the BMS shall immediately reduce regenerative braking torque to zero."
- "If the steering angle sensor reports values outside ±540° range, the EPAS ECU shall set a fault and apply a default assistive torque of 0 Nm."

---

## 5. Writing Good Requirements: SMART Criteria

| SMART Letter | Attribute | Poor Example | Good Example |
|---|---|---|---|
| **S** — Specific | One behaviour per requirement | "The system shall handle braking well" | "The AEB system shall engage full braking when TTC < 1.2 s" |
| **M** — Measurable | Quantified, no vague adjectives | "Response shall be fast" | "Response time shall not exceed 100 ms" |
| **A** — Achievable | Technically feasible within constraints | "Battery shall last 1 year on a single charge" | "Low-power mode current draw shall not exceed 2 mA" |
| **R** — Relevant | Traceable to a higher-level need | Requirement with no parent | Each SW req traces to a SYS req or safety goal |
| **T** — Testable | Can be verified with defined test method | "User-friendly display" | "Speedometer shall be readable from 1 m at 200 lux ambient lighting" |

### Additional Quality Attributes

- **Unambiguous**: Only one interpretation possible — avoid "appropriate", "sufficient", "if necessary"
- **Complete**: No TBDs in a baselined requirement
- **Consistent**: No contradictions with other requirements in the same module
- **Traceable**: Linked to parent requirement and to test case(s)
- **Atomic**: Each requirement addresses exactly one condition/behaviour
- **Non-prescriptive**: States WHAT, not HOW (avoid specifying implementation unless truly constrained)

---

## 6. Common Requirement Anti-patterns

### Anti-pattern 1: Ambiguous / Vague Language

| Bad | Problem | Better |
|-----|---------|--------|
| "The system shall respond quickly" | "Quickly" is undefined | "The system shall respond within 50 ms" |
| "The ECU shall be reliable" | No measurable target | "The ECU shall achieve MTBF > 100,000 hours" |
| "Appropriate warnings shall be given" | "Appropriate" is subjective | "A visual icon and audible chime (80 dB ± 3 dB) shall activate" |
| "The system shall handle errors gracefully" | Unmeasurable | "On sensor failure, DTC shall be set within 1 drive cycle" |

### Anti-pattern 2: Untestable Requirements

These cannot be verified by any test:
- "The software shall be maintainable."
- "The algorithm shall be efficient."
- "The system shall behave correctly under all conditions."

**Fix**: Add a test method and acceptance criteria: "Code complexity (McCabe) per function shall not exceed 15."

### Anti-pattern 3: Compound Requirements

Requirements containing AND / OR linking two separate behaviours:

> Bad: "The FCW system shall alert the driver AND the AEB shall brake simultaneously when TTC < 1 s."

**Fix**: Split into:
1. "When TTC < 1 s, the FCW system shall activate the visual and audible alert."
2. "When TTC < 1 s, the AEB system shall apply autonomous braking."

### Anti-pattern 4: Implementation Requirements (How instead of What)

> Bad: "The AEB controller shall use a Kalman filter to estimate object velocity."

This prescribes the algorithm. Unless it is a genuine design constraint, write:
> Better: "The AEB controller shall estimate relative object velocity with an accuracy of ±0.5 m/s."

### Anti-pattern 5: TBD / TBC in Baselined Requirements

"The maximum braking deceleration shall be TBD."

This is a major ASPICE finding. TBDs must be resolved before baselining.

### Anti-pattern 6: Passive Voice Without Subject

> Bad: "Warnings shall be displayed."
> Good: "The instrument cluster HMI shall display the FCW warning icon."

The system subject must always be clearly named.

---

## 7. Requirements Traceability

### Forward Traceability

From higher-level requirement → derived requirement → test case.
Used to ensure every requirement is verified.

### Backward Traceability

From test case → requirement → stakeholder need.
Used to ensure every test has a reason (no orphan tests) and every requirement has coverage.

### Traceability Matrix Example — AEB Feature

The following is a simplified traceability matrix for an Automatic Emergency Braking (AEB) feature:

| Stakeholder Req | System Req | SW Req | Module Req | Test Case |
|---|---|---|---|---|
| STK-001: Vehicle shall avoid front collision automatically | SYS-AEB-001: AEB shall engage braking when TTC ≤ 1.5 s | SWE-AEB-001: FCW_Algo shall output Risk_Level > HIGH when TTC ≤ 1.5 s | MOD-AEB-001: FCW_Algo.computeRisk() shall return HIGH for TTC ≤ 1.5 s | TC-AEB-001: Unit test — verify computeRisk() returns HIGH at TTC = 1.4 s |
| STK-001 | SYS-AEB-001 | SWE-AEB-002: AlertManager shall command MaxBraking when Risk_Level = HIGH | MOD-AEB-002: AlertManager.applyBraking() shall output BrakeCmd = MAX within 20 ms | TC-AEB-002: HIL test — inject Risk_Level = HIGH, verify BrakeCmd = MAX within 20 ms |
| STK-001 | SYS-AEB-002: AEB shall not activate at speeds < 5 km/h | SWE-AEB-003: AEB function shall be inhibited when VehicleSpeed < 5 km/h | MOD-AEB-003: AEB_Supervisor.isEnabled() returns FALSE when speed < 5 km/h | TC-AEB-003: HIL test — verify no braking command at 3 km/h with object at 0.5 m |
| STK-002: Driver shall be warned before AEB activation | SYS-AEB-003: FCW visual alert within 500 ms of TTC < 2.5 s | SWE-AEB-004: HMI_Manager shall assert FCW_Icon_Active within 500 ms of TTC < 2.5 s | MOD-AEB-004: HMI_Manager.showFCWAlert() latency ≤ 500 ms | TC-AEB-004: HIL test — measure CAN signal FCW_Alert_Active timestamp vs TTC threshold crossing |

### Traceability Coverage Metrics

- **Requirement Coverage**: % of requirements with at least one linked test case (target: 100%)
- **Test Traceability**: % of test cases linked to at least one requirement (target: 100%)
- **Safety Req Coverage**: All ASIL B/C/D requirements must have multiple independent test methods

---

## 8. Tools Overview

### 8.1 IBM DOORS Classic

DOORS (Dynamic Object-Oriented Requirements System) is the industry standard for automotive requirements management.

**Module Structure**:
```
Project
└── Module (Formal Module)
    ├── Section
    │   ├── Requirement Object (row)
    │   │   ├── Object ID (auto-generated)
    │   │   ├── Object Text (requirement text)
    │   │   ├── Attributes (ASIL, Status, Owner, Review_Status)
    │   │   └── Links → (to other modules)
    └── Link Module (stores directional links between objects)
```

**Key Attributes**:
- **Object Identifier (ID)**: e.g., FCW-SW-0042
- **Object Text**: The requirement statement
- **ASIL**: Enum [QM, A, B, C, D]
- **Verification Method**: Enum [Analysis, Inspection, Test, Demonstration]
- **Status**: Enum [Draft, In Review, Approved, Obsolete]
- **Allocated To**: Link to SW component

**DOORS Views**:
- **Standard View**: Table with all attributes
- **Links View**: Shows upstream/downstream links
- **Explorer View**: Module tree navigation

**Baselines**:
- A snapshot of a module at a point in time (e.g., "SYS_AEB_v1.2_baseline_2025-06-01")
- Required before a system integration test milestone
- Changes after baseline managed via Change Proposals

**Change Sets** (DOORS Next):
- Branching mechanism — work in parallel without affecting the baseline
- Merge change sets after review and approval

---

### 8.2 IBM DOORS Next (DOORS NG)

The modern, web-based successor to DOORS Classic.

**Key Features**:
- Browser-based interface (no client install)
- Module view + artifact view
- ReqIF import/export (standard format for OEM↔Tier1 exchange)
- Integrated review workflows
- Read/write access via REST API (OSLC)
- Link types: refines, traces, satisfies, verifies, derives

**Typical Workflow**:
1. OEM exports StRS in ReqIF format
2. Tier 1 imports into DOORS Next project
3. System engineers create SYS module, link to StRS with "refines" link
4. SW engineers create SWE module, link to SYS with "derives" link
5. Test engineers create test spec, link with "verifies" link
6. Baseline created at project milestone
7. Coverage reports generated for ASPICE audit

---

### 8.3 JIRA with Requirements Plugin (Xray / R4J)

For agile automotive projects, JIRA manages requirements through a hierarchy:

```
Epic (Feature level — e.g., AEB Feature)
└── Story (System-level behaviour — e.g., AEB Alert)
    ├── Task (SW implementation task)
    └── Test (Xray Test linked to Story)
        └── Test Execution (Test Run result)
```

**Requirement Plugins**:
- **R4J (Requirements for Jira)**: Adds formal requirements management; parents/children, change notification
- **Xray**: Adds test types (Manual, Automated, BDD), test plans, coverage reports
- **Jira Product Discovery**: For stakeholder requirement capture at product level

**Traceability in Jira**:
- Epic → Story (requirement) → Test (test case) → Bug (defect when test fails)
- Traceability report: generated via Xray coverage matrix

---

### 8.4 Polarion ALM

Siemens Polarion is widely used in Tier 1 automotive for combined requirements + test management.

**Work Item Types**:
- **Requirement**: Functional, non-functional, safety requirement
- **Test Case**: Manual or automated test specification
- **Defect**: Bug tracked through lifecycle
- **Risk**: Risk register item linked to requirement

**Document Model**:
- **Requirement Specification**: Document containing requirement work items
- **Test Specification**: Document containing test case work items
- **Project Plan**: Work packages and milestones

**Linking in Polarion**:
- "verifies" link: Test Case → Requirement
- "derives" link: SW Requirement → System Requirement
- "implements" link: Task → Requirement

**Polarion Reports**:
- Test coverage report (requirements with no test)
- Open defects by severity / component
- Baseline comparison report (what changed)

---

### 8.5 Enterprise Architect for SysML/UML Requirements

Sparx Enterprise Architect (EA) is used for:
- SysML Requirement Diagrams (visual blocks showing requirements and relationships)
- Use case diagrams (stakeholder needs)
- Block Definition Diagrams (system architecture with requirement allocation)
- Sequence diagrams (interface requirements)

**Requirement block in SysML**:
```
«requirement»
FCW Alert Timing
id = SYS-FCW-003
text = "The FCW system shall issue a visual alert within 500 ms of TTC falling below 2.5 s"
ASIL = B
```

**SysML Relationships**:
- `«derive»`: Higher-level req → lower-level req
- `«refine»`: Adds detail to a requirement
- `«verify»`: Test case verifies requirement
- `«satisfy»`: Design element satisfies requirement

---

## 9. Change Impact Analysis

When a requirement changes, a structured impact analysis must be performed.

### Ripple Effect Chain

```
Stakeholder Req changes
    └── Which System Requirements derive from it? → Re-review SYS reqs
        └── Which SW Requirements derive from those? → Re-review SWE reqs
            └── Which design elements implement those SW reqs? → Re-review design
                └── Which test cases verify those reqs? → Replan and re-execute tests
                    └── Which test results are now invalid? → Mark as stale
```

### Change Impact Analysis Template

| Field | Content |
|-------|---------|
| Change Reference | CR-2025-0147 |
| Changed Requirement | SYS-AEB-001 — TTC threshold changed from 1.5 s to 1.2 s |
| Reason for Change | OEM OTA update — regulatory change UNECE R152 |
| Impacted SYS Reqs | SYS-AEB-001, SYS-AEB-002 |
| Impacted SW Reqs | SWE-AEB-001, SWE-AEB-002, SWE-AEB-005 |
| Impacted Design | FCW_Algorithm.c — TTC_THRESHOLD constant |
| Impacted Tests | TC-AEB-001, TC-AEB-002, TC-AEB-007 (all need re-run) |
| Re-test Scope | HIL regression — AEB activation tests (3 test cases) |
| Safety Impact | ASIL B requirement — safety analysis update required |
| Effort Estimate | 3 days SW change + 1 day HIL test |

### ASPICE Requirement for Change Management

ASPICE SUP.10 requires:
- All changes documented with rationale
- Impact analysis performed
- Change requests reviewed and approved before implementation
- Affected work products re-verified after change

---

## 10. Requirement Reviews

### Formal Review Process (IEEE 1028 / ASPICE VER.1)

**Roles**:
- **Author**: Requirements engineer who wrote the requirements
- **Moderator**: Facilitates the review (independent)
- **Reviewer**: Domain expert (safety engineer, SW architect, test engineer)
- **Scribe**: Records findings

**Review Types**:
1. **Walkthrough**: Author presents, informal, early draft
2. **Technical Review**: Peer checking, moderate formality
3. **Inspection (Fagan)**: Most formal — entry criteria, defect log, exit criteria, metrics

### Review Checklist — Requirements Module

**Completeness**
- [ ] All requirements have status "Approved" (no Draft or TBD in baselined module)
- [ ] All acronyms are defined in the glossary section
- [ ] Every ASIL-classified requirement has an ASIL attribute set
- [ ] All interface requirements reference the signal name, message ID, and protocol

**Correctness**
- [ ] Each requirement uses SHALL for mandatory, SHOULD for recommended
- [ ] No ambiguous words: "fast", "appropriate", "good", "user-friendly", "sufficient"
- [ ] All numeric values include units (ms, km/h, °C, V, A)
- [ ] No compound requirements (single AND/OR connecting two distinct behaviours)

**Traceability**
- [ ] Every requirement has at least one upstream link
- [ ] Every requirement has at least one downstream link (design or test)
- [ ] No orphan requirements (no parent)

**Testability**
- [ ] Every requirement has a Verification Method attribute set (Test/Analysis/Inspection/Demo)
- [ ] Quantified acceptance criteria are present for all measurable requirements

### Common Review Findings (Top 10)

1. Missing measurement units (e.g., "response within 100" — 100 what?)
2. Use of "TBD" or "TBC" in a requirement text
3. Compound requirements joined with AND
4. No ASIL attribute on a safety-relevant requirement
5. Ambiguous trigger conditions ("if needed", "when appropriate")
6. No upstream link (orphan requirement)
7. No verification method defined
8. Implementation language ("shall use CAN FD" instead of "shall transmit at > 1 Mbit/s")
9. Contradictory requirements (two reqs specify different timeout values)
10. Too broad scope ("The system shall handle all failure modes") — needs decomposition

---

## 11. Interface Control Document (ICD)

### What is an ICD?

An Interface Control Document formally defines all **signals, messages, and protocols** exchanged between two or more systems or ECUs. It is the contract between development teams.

### Why ICDs Are Critical in Multi-ECU Systems

- In a modern vehicle, 70–100 ECUs communicate over CAN, CAN FD, LIN, Ethernet, and FlexRay
- Without a precise ICD, engineers make assumptions about signal scaling, endianness, or timeout behaviour
- Integration failures traced to ICD ambiguity can delay programs by weeks

### ICD Content

| Section | Content |
|---------|---------|
| Document scope | Which two systems/ECUs does this ICD cover |
| System overview diagram | Block diagram showing ECU-to-ECU connection |
| Communication protocol | CAN / CAN FD / LIN / Ethernet; baud rate; topology |
| Message table | Message name, Message ID (hex), DLC, Cycle time, Sender ECU, Receiver ECU |
| Signal table | Signal name, Start bit, Length (bits), Factor, Offset, Min, Max, Unit, Initial value, Invalid value |
| Error handling | Timeout behaviour, missing message detection, substitute values |
| Security | Encryption/authentication requirements (ISO 21434) |
| Versioning | Document version, linked DBC/ARXML version |

### ICD Signal Table Example (AEB system)

| Signal Name | Message ID | Start Bit | Bits | Factor | Offset | Min | Max | Unit | Sender |
|---|---|---|---|---|---|---|---|---|---|
| VehicleSpeed | 0x100 | 0 | 16 | 0.01 | 0 | 0 | 655.35 | km/h | BCM |
| AEB_BrakeCmd | 0x3A0 | 0 | 8 | 1 | 0 | 0 | 100 | % | AEB ECU |
| FCW_Alert_Active | 0x3A0 | 8 | 1 | 1 | 0 | 0 | 1 | boolean | AEB ECU |
| TTC_Estimate | 0x3A1 | 0 | 16 | 0.001 | 0 | 0 | 65.535 | s | AEB ECU |

---

## 12. Five STAR Scenarios

---

### STAR 1: Catching an Ambiguous Safety Requirement That Would Have Caused a Recall

**Situation**: During ASPICE Level 2 assessment preparation for an ASIL B AEB system, I was reviewing the safety requirements module in DOORS.

**Task**: Conduct a formal inspection of all 47 SW safety requirements before baseline sign-off.

**Action**:
I created a review checklist aligned to ISO 26262-6 and went through each requirement. I found this requirement:

> "If the AEB system detects an imminent collision, the system shall engage emergency braking."

The word "imminent" had no quantitative definition anywhere in the module. Different engineers had different interpretations: the algorithm engineer assumed TTC < 1.5 s; the test engineer had written HIL test cases based on TTC < 2.0 s; no calibration constant existed in the software.

I escalated this as a Critical Review Finding. I requested a cross-functional meeting with the safety engineer, system architect, and calibration engineer. We agreed on:

> "If TTC falls below 1.5 s and relative velocity exceeds 5 km/h, the AEB ECU shall apply autonomous braking at ≥ 80% of maximum deceleration within 150 ms."

I updated the requirement, got it approved, and the HIL test cases were rewritten. The calibration value was formally captured as a system parameter in the ICD.

**Result**: The ambiguity was caught 8 weeks before vehicle integration testing. The test lead estimated this would have caused 20+ days of re-testing and possible field issues if it had reached production. The ASPICE assessor cited this finding resolution as an example of process maturity.

---

### STAR 2: Managing Requirement Changes Mid-Sprint on a Cluster ECU Project

**Situation**: Mid-sprint in a 2-week agile cycle, the OEM issued a change request: the speedometer display refresh rate needed to change from 100 ms to 50 ms due to a new driver perception study. This was a supplier contractual obligation.

**Task**: Assess impact, update requirements, and determine whether the sprint commitment could be maintained.

**Action**:
I immediately performed a change impact analysis in JIRA:
1. Identified 3 SW requirements in the Cluster display module affected
2. Found 2 test cases in Xray that would need updated expected values
3. Confirmed with the SW architect that the change required modifying one scheduler task period — 1 day effort
4. Confirmed with hardware team that the CAN message cycle time was already 50 ms — no HW change needed
5. Called a sprint planning review with the PO and tech lead — we re-pointed the story and accepted the change

I updated the DOORS module with the new requirement, created a change proposal in DOORS, linked it to the OEM change request number, and updated the Xray test cases with new timing acceptance criteria.

**Result**: Sprint delivery was maintained with a 1-day slip. The change was fully traced in DOORS and passed the OEM change management audit.

---

### STAR 3: Building a Traceability Matrix from Scratch in DOORS

**Situation**: Joining a new project that was 6 months in but had no formal traceability — requirements were in Word documents and test cases in Excel.

**Task**: Establish full ASPICE-compliant traceability from SYS reqs to SW reqs to test cases within 4 weeks.

**Action**:
1. Imported all Word-based system requirements into a new DOORS Formal Module (SYS requirements) using File → Import Word Document. Assigned IDs and attributes to each object.
2. Created a SW Requirements module; for each SW requirement, created a "derives from" link to the corresponding SYS requirement.
3. Imported test cases from Excel into DOORS using DOORS DXL script — mapped columns (ID, Title, Steps, Expected Result) to DOORS attributes.
4. For each test case, created a "verifies" link to the SW requirement.
5. Generated a traceability report in DOORS using a DXL script to export a matrix to Excel — rows = requirements, columns = test cases, cells = linked/not linked.
6. Identified 23 SW requirements with no test coverage — created a gap list and assigned to the test engineer.

**Result**: Full traceability achieved in 3.5 weeks. Coverage reached 97% (3 deprecated requirements excluded). ASPICE external assessor rated SWE.1 and SWE.5 at Level 2 with no major findings on traceability.

---

### STAR 4: Writing EARS Requirements for an AEB Feature

**Situation**: A new AEB feature was being scoped for a program starting in Q3. The system requirements were in bullet-point form with no syntax discipline — unprovable, ambiguous, and unmappable to test.

**Task**: Rewrite 15 system requirements for AEB using EARS notation, validated against ISO 26262 and ASPICE SYS.2 criteria.

**Action**:
I ran a workshop with the safety engineer, system architect, and test lead. We took each bullet and reformulated using the 5 EARS patterns:

| Original | EARS Pattern | Rewritten |
|---|---|---|
| "AEB should work at highway speeds" | State-driven | "While vehicle speed is between 30 km/h and 200 km/h, the AEB system shall remain in ACTIVE_READY state." |
| "Alert driver before braking" | Event-driven | "When FCW_Risk_Level transitions to HIGH, the FCW system shall activate the visual and audible alert within 200 ms." |
| "System should handle sensor faults" | Unwanted behaviour | "If the radar sensor fails self-check at boot, the AEB ECU shall set DTC P1A00 and transition to DEGRADED mode." |
| "Night vision option available" | Optional feature | "Where the vehicle is equipped with the night vision package, the IR camera shall provide object data to the AEB fusion module." |
| "Store all event logs" | Ubiquitous | "The AEB ECU shall log all AEB activation events with timestamp and trigger parameters in non-volatile memory." |

All 15 requirements were approved in the ASPICE SYS.2 review. The test engineer said test design time was reduced by 40% compared to previous projects because acceptance criteria were already embedded in the requirement text.

**Result**: Zero ambiguity findings in the OEM requirement review. Traceability from each requirement to at least 2 test cases achieved at the time of module baseline.

---

### STAR 5: Conducting a Requirement Review and Finding 10 Issues

**Situation**: As the requirements team lead, I was assigned to chair the formal inspection of the SW requirements module for a new LIN body control function (door lock/unlock). The module had 35 requirements authored by a junior engineer.

**Task**: Conduct the formal inspection, log all findings, and ensure defects were resolved before baseline.

**Action**:
I sent the module to 4 reviewers 3 days in advance with a review checklist. In the 90-minute inspection meeting:

| # | Finding ID | Requirement | Issue Type | Severity |
|---|---|---|---|---|
| 1 | RVW-001 | REQ-DL-003 | Missing unit: "unlock within 200" — 200 ms or cycles? | Major |
| 2 | RVW-002 | REQ-DL-007 | Compound: "shall lock doors AND disable interior lights" | Major |
| 3 | RVW-003 | REQ-DL-009 | Ambiguous: "all doors shall be secured appropriately" | Major |
| 4 | RVW-004 | REQ-DL-011 | No upstream SYS link — orphan requirement | Major |
| 5 | RVW-005 | REQ-DL-015 | TBD in text: "timeout = TBD" | Critical |
| 6 | RVW-006 | REQ-DL-018 | Implementation req: "shall use LIN frame ID 0x1C" — functional requirement? | Minor |
| 7 | RVW-007 | REQ-DL-020 | No Verification Method attribute set | Minor |
| 8 | RVW-008 | REQ-DL-022 | Passive voice: "warnings shall be displayed" — by which system? | Major |
| 9 | RVW-009 | REQ-DL-028 | Safety req with no ASIL attribute | Critical |
| 10 | RVW-010 | REQ-DL-033 | Contradicts REQ-DL-005: two different timeout values (50 ms vs 100 ms) | Critical |

I logged all findings in a Review Action Item tracker in Polarion, assigned each to the author with due dates. All 10 were resolved within 5 business days. The module was re-inspected (brief 30-minute spot check) and baselined.

**Result**: Baseline approved. Requirement defect density: 0.29 defects/requirement — within the acceptable threshold of < 0.5 for SW requirements modules. Junior engineer received structured feedback and improved significantly on the next module.

---

## 13. 15 Interview Q&A

---

**Q1. What is the difference between a system requirement and a software requirement?**

A system requirement (SyRS) describes the observable behaviour of the complete system (multiple ECUs, sensors, actuators) allocated from stakeholder needs. A software requirement (SwRS) is derived from the system requirement and is allocated specifically to a software component to implement. For example: "The AEB system shall activate braking when TTC < 1.5 s" is a system requirement. "The AEB_Supervisor module shall output BrakeCmd = MAX when TTC < 1.5 s" is a software requirement derived from it.

---

**Q2. What is EARS notation and why do you use it?**

EARS (Easy Approach to Requirements Syntax) provides five structured templates for writing requirements:
1. Ubiquitous (The system shall...)
2. Event-driven (When event, the system shall...)
3. State-driven (While state, the system shall...)
4. Optional feature (Where feature, the system shall...)
5. Unwanted behaviour (If condition, the system shall...)

I use EARS because it forces authors to explicitly define triggers, states, and conditions — eliminating the most common sources of requirement ambiguity. It also makes test case derivation straightforward because the triggering condition is already stated.

---

**Q3. How do you maintain traceability from stakeholder requirements to test cases?**

I establish a full chain: Stakeholder Req → System Req → SW Req → Module/Component Req → Test Case.
In DOORS, I use link modules with directional link types (derives, verifies). Each object at one level has an explicit link to its parent. For test coverage I generate a traceability matrix report — requirements in rows, test cases in columns — to identify gaps. Coverage is reported as a metric: % of requirements with verified test cases. In ASPICE reviews, I export this matrix for the assessor as evidence for VER.1 and SWE.5.

---

**Q4. What happens when a requirement changes? Walk me through the process.**

1. A change request (CR) is raised in the change management tool (JIRA or DOORS Change Proposal)
2. I perform change impact analysis: identify all downstream requirements, design items, and test cases linked to the changed requirement
3. Present the impact assessment to the change control board (CCB) for approval
4. After approval: update the requirement in DOORS, update the version/status
5. Notify all affected engineers (SW, test, safety)
6. Re-baseline the module after all linked items are updated
7. Trigger re-testing for all test cases linked to the changed requirement
8. Record the change rationale in the requirement's history attribute

---

**Q5. What is ReqIF and when do you use it?**

ReqIF (Requirements Interchange Format) is an OMG standard XML-based format for exchanging requirements between different tools (e.g., OEM uses DOORS, Tier 1 uses Polarion). When an OEM issues a system requirements module, they export it as .reqif file. The Tier 1 imports it into their tool, establishes traceability to their SW requirements, and may later export their SW requirements back. ReqIF preserves attribute names, data types, and link types. This avoids copying requirements manually and prevents version mismatch between OEM and Tier 1 documents.

---

**Q6. How do you handle a TBD in a safety requirement?**

A TBD in a safety requirement is a Critical finding — it cannot be baselined. I follow these steps:
1. Flag immediately as a blocking issue in the review
2. Identify who is responsible for resolving the TBD (usually the safety engineer or system architect)
3. Raise a formal action item with a due date
4. Freeze the requirement in "Draft" status — it cannot be used in design or test until resolved
5. If the TBD cannot be resolved before a project milestone, escalate to the project manager — the milestone should not proceed without it
I have never allowed a TBD to go into a baselined module.

---

**Q7. Explain the difference between forward and backward traceability.**

Forward traceability: starting from a higher-level requirement and following all derived lower-level requirements and test cases downstream. Used to check that all requirements are implemented and verified.

Backward traceability: starting from a test case and tracing back up to the requirement and ultimately the stakeholder need. Used to ensure no test cases exist without a requirement (orphan tests) and every test is justified.

Both directions are needed for ASPICE compliance. If forward traceability is missing, requirements are not tested. If backward traceability is missing, there may be tests with no justification (wasted effort or untraceable test coverage).

---

**Q8. What is an Interface Control Document and why is it critical?**

An ICD formally specifies all signals, messages, and communication parameters exchanged between two ECUs or systems. It defines: message ID, signal bit position, scaling factor, offset, unit, valid range, cycle time, sender, and receiver. It is critical because in multi-ECU systems (where AEB ECU communicates with BCM, HMI, and brake ECU), each team develops independently. Without a precise ICD, teams make assumptions about signal layout or timeout values that only fail at integration — at which point the cost to fix is much higher. The ICD is versioned and linked to the DBC file used in CANoe.

---

**Q9. How do you write a testable requirement?**

A requirement is testable if:
1. It has a quantitative acceptance criterion (e.g., "within 100 ms", "≥ 80%", "≤ −40°C")
2. The subject is unambiguous (one specific system or component)
3. The trigger is precisely defined (EARS pattern)
4. The verification method is stated (Test, Analysis, Inspection, Demonstration)

I also cross-check by asking: "Can I write a specific test case step and expected result that would directly verify this requirement with a pass/fail outcome?" If not, the requirement needs revision.

---

**Q10. What is the ASPICE SWE.1 process?**

ASPICE SWE.1 (Software Requirements Analysis) requires the supplier to:
1. Develop SW requirements from the system requirements (SYS.2 output)
2. Ensure SW requirements are consistent, complete, testable, and unambiguous
3. Allocate SW requirements to SW components
4. Establish bidirectional traceability to SYS requirements
5. Obtain agreement from affected parties on SW requirements
6. Place SW requirements under version control and baseline them

Evidence for ASPICE SWE.1 at Level 2: a baselined SW requirements module in DOORS/Polarion with bidirectional links to SYS requirements, a review record, and a change history.

---

**Q11. Describe how you have used IBM DOORS in a project.**

In my previous program (ADAS AEB development for a Tier 1 supplier), DOORS was the central requirements management tool. I used DOORS Classic:
- Managed a formal module of 120 SW requirements for the AEB algorithm
- Created custom attributes: ASIL, SW_Component, Verification_Method, Review_Status
- Wrote DXL scripts to auto-generate a weekly traceability coverage report exported to Excel
- Managed 5 baselines across the development lifecycle (concept, system design, SW design, integration test, production)
- Handled 3 change proposals following OEM requirement changes — performed impact analysis and updated all linked objects

---

**Q12. What is the difference between validation and verification in requirements context?**

Verification: "Are we building the product right?" — checking that the implementation conforms to the requirement as specified. Example: HIL test verifying AEB braking command is issued within 150 ms.

Validation: "Are we building the right product?" — checking that the requirements actually fulfil the stakeholder need. Example: vehicle-level test confirming that AEB with 1.5 s TTC threshold actually prevents collisions in the real-world test scenario intended by the OEM.

In requirements engineering, validation happens during requirement reviews (is this requirement what the customer actually needs?) and verification happens during system/SW testing.

---

**Q13. How do you handle conflicting requirements from two stakeholders?**

1. Document both requirements explicitly with their sources
2. Quantify the conflict (e.g., OEM A requires TTC threshold = 1.5 s, OEM B requires 1.2 s for a dual-customer platform)
3. Raise a Change Request / Technical Query (TQ) to both stakeholders
4. Facilitate a decision meeting with the system architect and project manager
5. If a common value is agreed, update both and document the decision rationale
6. If the platform must support both variants, use a variant management approach: two requirement variants linked to different vehicle configurations (tagged with "Variant A" / "Variant B" attributes in DOORS)

---

**Q14. What makes a requirement "non-functional" and can you give automotive examples?**

Non-functional requirements specify quality attributes — how the system performs rather than what it does. They constrain the design but don't describe specific behaviour.

Automotive examples:
- **Performance**: "The radar object fusion algorithm shall complete processing within 20 ms cycle time."
- **Reliability**: "The AEB ECU shall achieve an MTBF of ≥ 10,000 operating hours."
- **Safety (ISO 26262)**: "The AEB function shall achieve ASIL B hardware requirements at the item level."
- **Environmental**: "The ECU shall comply with IEC 60068-2-6 vibration test profile for underhood mounting."
- **Memory**: "The SW image shall not exceed 512 KB of program flash."
- **Security**: "All UDS diagnostic services above 0x10 01 shall require an authenticated session."

---

**Q15. If you had to set up a requirements management process for a new project from scratch, what would you do in the first two weeks?**

Week 1:
- Define the requirement hierarchy (StRS → SyRS → SwRS → Component Req)
- Set up the DOORS / Polarion project structure: one module per level, link types defined
- Define module attributes: ID scheme, ASIL, Status, Owner, Verification Method, Review Status
- Create a requirements style guide aligned to EARS and SMART criteria
- Import or enter any existing requirements from Word/Excel documents
- Establish access control: who can write, who can only read

Week 2:
- Conduct a kickoff requirements workshop with system architects, safety engineers, and SW leads
- Define the traceability strategy: what links are mandatory at each level
- Create the first draft of the ICD template
- Set up a DXL/Python script to generate weekly coverage reports
- Schedule recurring requirement review meetings (every 2 weeks)
- Define baseline milestones aligned to the project plan

By end of week 2, the requirement management infrastructure is in place and the team can begin authoring with consistent standards and tooling.

---

*Guide compiled for automotive engineers targeting ASPICE Level 2/3 and ISO 26262 compliant projects.*
*Last updated: April 2026*
