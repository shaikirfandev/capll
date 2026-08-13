# 04 Requirements Engineering — ASPICE, Traceability, Decomposition, Interfaces, Timing, Reviews, Validation, and Requirement-Based Testing

This document is a detailed training reference for automotive engineers working on system, software, integration, validation, and process compliance activities.
It expands Sections **15 through 22** of an automotive requirements engineering curriculum and is written to be used in OEM, Tier-1, and engineering services environments.

The focus is practical: how requirements are written, decomposed, reviewed, traced, implemented, verified, validated, and transformed into test assets that survive ASPICE and safety audits.

---

## Table of Contents

1. [15. Requirements + ASPICE](#15-requirements--aspice)
1. [16. Requirements Traceability](#16-requirements-traceability)
1. [17. Requirements Decomposition](#17-requirements-decomposition)
1. [18. Interface Requirements](#18-interface-requirements)
1. [19. Timing Requirements](#19-timing-requirements)
1. [20. Requirements Review](#20-requirements-review)
1. [21. Requirements Validation](#21-requirements-validation)
1. [22. Requirement-Based Testing](#22-requirement-based-testing)

---

## 15. REQUIREMENTS + ASPICE

In Automotive SPICE, requirements engineering is not an isolated documentation activity.
It is the backbone that connects customer intent to engineering realization and objective evidence.
Every downstream design, code module, calibration item, interface definition, and test case should be traceable back to an approved requirement baseline.

### 15.1 Why ASPICE cares so much about requirements

- Requirements are the contractual agreement between customer intent and engineering implementation.
- Weak requirements create unstable architecture, uncontrolled derived requirements, and expensive integration defects.
- Safety and cybersecurity goals cannot be demonstrated without clear, verifiable technical requirements.
- ASPICE assessors look for objective evidence that requirements are complete, consistent, feasible, testable, and traced.
- A mature organization manages requirements as baselined work products, not as ad-hoc text files or meeting notes.

### 15.2 End-to-end ASPICE process relationship

Requirements flow across the V-cycle.
The left side creates and refines requirements and architecture.
The right side proves that the resulting product satisfies those requirements.

```text
Customer Needs / SYS.1
        ↓
System Requirements / SYS.2
        ↓
System Architecture / SYS.3
        ↓
Software Requirements / SWE.1
        ↓
Software Architecture / SWE.2
        ↓
Detailed Design + Unit Construction / SWE.3, SWE.4
        ↓
Unit Verification / SWE.5
        ↓
Software Integration + Test / SWE.6
        ↓
System Integration + Verification / SYS.4
        ↓
System Qualification + Validation / SYS.5, SYS.6
```

| ASPICE Process | Main RE Concern | Typical Inputs | Typical Outputs | Why it matters to RE |
|---|---|---|---|---|
| SYS.1 | Capture stakeholder needs | OEM feature request, legal needs, safety goals, use cases | Stakeholder requirements specification | Defines the intent that later requirements must preserve |
| SYS.2 | Analyze system requirements | Stakeholder requirements, item definition, assumptions | System requirements specification, external interface requirements | Creates the technical baseline for system behavior |
| SYS.3 | Architect the system | System requirements, constraints, platform strategy | System architectural design, allocation decisions | Shows where each requirement is realized |
| SYS.4 | Integrate and verify the system | System architecture, test specification, integrated elements | System integration records, verification results | Confirms the assembled system meets system requirements |
| SYS.5 | System qualify | Qualified system, qualification criteria | Qualification reports, release evidence | Demonstrates readiness in representative conditions |
| SYS.6 | Validate system | User scenarios, operational concept, stakeholder needs | Validation reports, acceptance evidence | Shows the product solves the intended real-world problem |
| SWE.1 | Analyze software requirements | System requirements allocation, ICDs, safety/security constraints | Software requirements specification | Translates system intent into software behavior |
| SWE.2 | Architect software | Software requirements, platform constraints, AUTOSAR strategy | Software architecture design | Allocates software requirements to components and interfaces |
| SWE.3 | Detailed software design and unit construction | Architecture, software requirements | Detailed design, code, unit design records | Implements requirement intent with enough detail for unit development |
| SWE.4 | Software unit verification | Detailed design, unit implementation, unit test spec | Unit verification results | Checks the smallest implementation units against design/requirement intent |
| SWE.5 | Software integration and integration test | Software components, integration strategy | Integration results, interface verification records | Proves software elements work together and respect interfaces |
| SWE.6 | Software qualification test | Integrated software, software requirements | Software qualification results | Demonstrates software fulfills software requirements before full system test |

### SYS.1 Stakeholder Requirements Definition

- Captures what the customer, regulators, service teams, and users expect from the vehicle function.
- Outputs are often feature-oriented, operational, and user-centric rather than implementation-centric.
- Requirements engineers translate market language into controlled engineering terminology.
- Typical examples include customer visible behavior, environmental conditions, regulatory triggers, and diagnostic expectations.
- A defect here propagates through the entire development chain because everything downstream assumes the stakeholder intent is correct.

### SYS.2 System Requirements Analysis

- Transforms stakeholder intent into precise technical system requirements.
- Adds measurable values, modes, state conditions, failure behavior, interfaces, performance limits, and verification criteria.
- Requires analysis of normal operation, degraded operation, start-up, shutdown, and diagnostic states.
- System requirements should be atomic, uniquely identified, versioned, and linked to their origin.
- SYS.2 is the most visible RE process in many ASPICE assessments because it shows whether engineering understands the problem.

### SYS.3 System Architectural Design

- Allocates system requirements to subsystems, ECUs, sensors, actuators, communication buses, and manual driver interactions.
- Creates logical and physical architecture views.
- Documents interfaces, responsibilities, redundancy concepts, and resource constraints.
- Introduces derived requirements when architectural decisions reveal new needs.
- Provides the traceability bridge from requirements to implementation domains.

### SYS.4 System Integration and Integration Test

- Combines hardware and software elements according to an integration strategy.
- Verifies that interfaces, states, timing, and feature interactions work at system level.
- Uses requirement-based tests, interface tests, fault injection, and regression tests.
- Closes verification evidence against SYS.2 requirements.
- Common outputs are integration logs, defect reports, pass/fail reports, and updated traceability records.

### SYS.5 System Qualification Test

- Runs the complete system against qualification criteria in representative environments.
- Often includes vehicle-level tests, climatic conditions, EMC, power mode behavior, and operational scenarios.
- The goal is to confirm that the engineered system is release-ready against its technical requirement set.
- Qualification is still verification-oriented because the reference remains the documented specification.
- Evidence is especially important for release gates and customer audits.

### SYS.6 System Validation

- Checks fitness for intended use in realistic customer scenarios.
- Asks whether the correct product was built, not only whether it meets technical specifications.
- Typical validation environments include proving grounds, fleet trials, user acceptance programs, and scenario replay.
- Stakeholder expectations, misuse cases, and operational context are essential inputs.
- Validation closes the loop to SYS.1, not only to SYS.2.

### SWE.1 Software Requirements Analysis

- Derives software-facing behavior from allocated system requirements.
- Defines algorithm behavior, state machines, diagnostics, timing, interfaces, non-functional behavior, and failure handling.
- Clarifies what is done in software versus hardware or network layers.
- Typical concerns are computational limits, memory constraints, scheduling assumptions, and platform APIs.
- SWE.1 outputs must be testable and architecturally allocatable.

### SWE.2 Software Architectural Design

- Maps software requirements to components, runnables, services, tasks, and communication paths.
- Defines interfaces between software components and external Basic Software or middleware services.
- Creates an architecture that supports timing, safety partitioning, freedom from interference, and maintainability.
- Shows where diagnostic behavior, mode management, error handling, and data ownership reside.
- Architecture is the critical traceability layer between requirements and source code.

### SWE.3 Software Detailed Design and Unit Construction

- Breaks architecture into unit-level logic, APIs, state tables, algorithms, and code constructs.
- Design decisions must still preserve software requirement intent.
- Detailed design often introduces local derived requirements such as parameter ranges or overflow handling.
- Construction evidence includes code, design descriptions, and static analysis results.
- Poor detailed design often creates hidden requirements that should have been documented explicitly.

### SWE.4 Software Unit Verification

- Verifies each unit against the detailed design and applicable software requirements.
- Typical techniques include unit tests, static analysis, boundary analysis, data/control flow coverage, and interface stubs.
- Even if unit tests are design-based, there should still be traceability to higher-level requirements where relevant.
- Results feed confidence into later integration stages.
- Weak unit verification shifts expensive defect detection to integration and vehicle test.

### SWE.5 Software Integration and Integration Test

- Builds up interacting software elements and verifies interfaces, tasking, timing, and shared data behavior.
- Focuses on what cannot be demonstrated at isolated unit level.
- Typical concerns are queue overflow, signal freshness, service discovery, initialization order, and error propagation.
- Traceability should connect integration tests to software requirements and interface requirements.
- This process is where architectural assumptions are frequently proven right or wrong.

### SWE.6 Software Qualification Test

- Executes software-level verification against the approved software requirements specification.
- Usually performed in a controlled target or representative environment before full system integration evidence is claimed.
- Typical assets include software qualification test specifications, automated scripts, logs, and reports.
- Demonstrates that the integrated software product satisfies SWE.1.
- Strong SWE.6 evidence reduces surprises during SYS.4 and SYS.5.

### 15.3 Requirements analysis in ASPICE context

- Requirements analysis means examining inputs, resolving ambiguity, making assumptions explicit, and converting intent into measurable technical statements.
- The analyst checks feasibility, safety impact, security impact, legal constraints, and interface consequences before baselining the requirement.
- Analysis includes identifying operating modes, trigger conditions, state transitions, boundary values, and fault reactions.
- Good analysis results in requirements that are atomic, unique, consistent, prioritized, and verifiable.
- ASPICE does not reward beautifully written prose if the requirement cannot be traced, implemented, or verified.

### 15.4 System architecture and requirements

- System architecture is the answer to the question: where will each system requirement be realized?
- A single vehicle function is often distributed across sensors, multiple ECUs, communication buses, actuators, HMIs, and backend systems.
- Architecture introduces allocation decisions such as which ECU hosts a fusion algorithm or which node owns a telltale output.
- Architectural decomposition frequently reveals derived requirements for interfaces, timing, power modes, diagnostics, and safe states.
- If architecture is weak, traceability becomes superficial because the links do not explain implementation responsibility.

### 15.5 Software architecture and requirements

- Software architecture refines allocated system behavior into components, services, tasks, and data/control interfaces.
- It defines how requirements are distributed to software components and how those components communicate.
- It should reveal ownership of state, fault handling, resource management, and scheduling constraints.
- In AUTOSAR-based projects, software architecture also clarifies the relationship among application software components, CDDs, BSW services, and RTE communication.
- Good software architecture allows each software requirement to be mapped to one or more architectural elements without guesswork.

### 15.6 Bidirectional traceability in ASPICE

- Forward traceability links a requirement to downstream realization and verification artifacts.
- Backward traceability links a design, code change, or test case back to an approved requirement source.
- Bidirectional traceability is necessary for change impact analysis, defect triage, release audits, and safety assessments.
- An ASPICE assessor expects evidence that links are maintained and used, not just generated once and forgotten.
- Good bidirectional traceability can answer both “what implements this requirement?” and “why does this artifact exist?”

### 15.7 Verification in ASPICE

- Verification asks whether specified work products or product elements conform to specified requirements.
- Verification happens at multiple levels: requirements review, architecture review, unit verification, software qualification, system integration verification, and system qualification.
- A requirement is only verifiable if it includes measurable criteria, operating conditions, and expected results.
- Verification evidence is objective: review records, simulation logs, automated test reports, calibration traces, measurements, screenshots, and sign-offs.
- Good verification planning is created early; waiting until integration to think about verification usually exposes missing requirement detail.

### 15.8 Validation in ASPICE

- Validation asks whether the final product fulfills the intended use in the real operational context.
- Validation often uses end-user scenarios, proving ground cases, fleet learning, and representative environmental conditions.
- A technically correct system can still fail validation if it annoys the driver, misses usage context, or creates unacceptable false positives.
- Validation evidence often combines qualitative judgment with quantitative measures such as comfort, nuisance rate, takeover quality, and scenario coverage.
- Validation is strongly linked to stakeholder requirements, customer clinics, legal use cases, and operational design domain definitions.

### 15.9 Typical ASPICE work products relevant to requirements engineering

| Work Product | Typical Owner | Contains | Used by |
|---|---|---|---|
| Stakeholder Requirements Specification (StRS) | Product owner / system engineer | Customer intent, use cases, user scenarios, external expectations | SYS.2, validation planning |
| System Requirements Specification (SyRS) | System requirements engineer | Functional, non-functional, interface, safety, security, timing requirements | SYS.3, SYS.4, SWE.1 |
| System Architectural Design | System architect | Subsystem structure, interfaces, allocations, deployment | SYS.4, SWE.1, supplier allocation |
| Interface Control Document (ICD) | System / network architect | Signal definitions, services, IDs, timing, error handling | Integration teams, test teams, suppliers |
| Software Requirements Specification (SwRS) | Software requirements engineer | Algorithm behavior, states, diagnostics, interfaces, timing, resource constraints | SWE.2, SWE.6 |
| Software Architectural Design (SwAD) | Software architect | Components, runnables, tasks, ports, dependencies | SWE.3, SWE.5 |
| Traceability Matrix | Configuration / requirements manager | Links among reqs, design, code, tests, defects | All engineering and audit functions |
| Verification Specification | Test architect | Methods, environments, expected results, pass criteria | Unit, integration, qualification teams |
| Validation Plan | System validation lead | Real-world scenarios, acceptance criteria, user context | SYS.6 |
| Review Records | Moderator / author / reviewers | Findings, actions, decisions, status | Process evidence, continuous improvement |

### 15.10 Example work product snippets

Example system requirement entry:

```text
ID: SYS-FCW-042
Title: FCW visual and audible warning timing
Requirement: The Forward Collision Warning system shall issue a visual warning in the cluster and an audible chime within 300 ms after TTC falls below 2.2 s while vehicle speed is between 20 km/h and 160 km/h and the system is not in degraded mode.
Rationale: Provide timely driver warning for collision avoidance.
Verification Method: System integration test + vehicle test.
Source: STK-ADAS-011, HARA-FCW-03.
Safety relevance: ASIL B.
```

Example interface control entry:

```text
Signal Name: FCW_WarnReq
Bus: CAN FD Powertrain Safety Bus
Frame ID: 0x18FF52A1
Sender: ADAS Domain Controller
Receiver: Instrument Cluster, Chassis Supervisor
Cycle Time: 20 ms
Timeout: 100 ms
Initial Value: 0x0 (No warning)
Invalid Value: 0x3 (Signal invalid)
Fault Behavior: Receiver shall treat timeout or invalid value as warning unavailable and store diagnostic event.
```

Example verification specification entry:

```text
Test ID: SYS-TC-FCW-017
Objective: Verify warning is issued within 300 ms after TTC threshold crossing.
Input Stimulus: Replay scenario SCN_FCW_URBAN_STOP_05 with TTC ramp from 3.0 s to 1.8 s.
Measurement: TTC threshold timestamp, cluster telltale timestamp, chime timestamp.
Pass Criteria: Visual and audible warning timestamps shall be ≤ 300 ms after threshold crossing.
```

### 15.11 What good ASPICE evidence looks like

- A clear requirement hierarchy from stakeholder to system to software to test.
- Approved baselines with revision history and change rationale.
- Architecture elements explicitly allocated to requirements.
- Verification methods identified for each requirement.
- Evidence that orphan or obsolete requirements are detected and resolved.
- Evidence that reviews are performed and findings are closed.
- Evidence that validation is planned against intended use, not just lab tests.

### 15.12 Common RE failures seen in ASPICE assessments

- System requirements copied directly from marketing text without measurable criteria.
- Software requirements that restate implementation decisions without behavior or acceptance criteria.
- Architecture documents that show blocks but not allocation of requirements.
- Test cases that exist but are not linked to the requirement baseline.
- Derived requirements implemented in code but never formally documented.
- Interfaces defined in DBC or AUTOSAR files but not linked back to system/software requirements.
- Validation confused with verification, causing missing customer-use evidence.

---

## 16. REQUIREMENTS TRACEABILITY

Traceability is the ability to follow the life of a requirement forward and backward through specification, design, implementation, verification, validation, release, and change management.
In automotive programs, traceability is essential because functions are distributed across ECUs, suppliers, buses, and test levels.

### 16.1 Forward traceability

- Forward traceability follows a source requirement into its derived artifacts.
- Example: Vehicle warning requirement → system requirement → cluster software requirement → display component → test case → test report.
- It proves that approved intent has been implemented and verified.
- It is heavily used during implementation planning, coverage analysis, and release readiness reviews.
- Forward gaps usually reveal missing implementation or missing verification.

### 16.2 Backward traceability

- Backward traceability follows an artifact back to its reason for existence.
- Example: A diagnostic service implementation in the TCU must trace back to a system requirement, legal requirement, or service requirement.
- It prevents gold-plating, hidden scope, and undocumented behavior.
- It is crucial during audits and change impact analysis because engineers must justify why code, signals, tests, or calibration parameters exist.
- Backward gaps usually reveal unauthorized implementation or undocumented derived requirements.

### 16.3 Bidirectional traceability

- Bidirectional traceability means links are navigable in both directions and remain meaningful across baselines.
- It is not enough to export a static spreadsheet once; links must be maintained as requirements evolve.
- A mature project can query any requirement and immediately show allocated architecture, implemented components, and verification evidence.
- Likewise it can pick any code component, interface, or test and identify the parent requirement and approval history.
- Bidirectional traceability is fundamental for safety cases, supplier collaboration, and change impact analysis.

### 16.4 What traceability completeness means

- Every approved requirement should have a parent source unless it is explicitly marked as derived.
- Every system and software requirement should have an allocation target or owner.
- Every implementable requirement should have at least one verification method and planned verification artifact.
- Every delivered design element or code module should have at least one backward link to an approved requirement.
- Every closed defect that changes behavior should update traceability if it adds or modifies requirement intent.

### 16.5 Common traceability defects

| Defect Type | What it means | Typical Root Cause | Risk |
|---|---|---|---|
| Orphan requirement | Requirement has no parent or no downstream links | Late addition, poor baseline control, missing analysis | Unclear necessity or no implementation/test coverage |
| Orphan test | Test case has no linked requirement | Test team created exploratory case but never traced it | Coverage reporting becomes misleading |
| Missing implementation | Requirement has no design/code allocation | Planning gap, rejected feature, ownership confusion | Requirement may ship unimplemented |
| Missing verification | Requirement has no verification case or result | Requirement written after test design, unclear measurability | Cannot claim compliance or release confidence |
| Obsolete trace link | Link points to outdated requirement version or retired artifact | Weak change management | False sense of coverage |
| Many-to-many confusion | Too many uncontrolled links with no rationale | Bulk linking without engineering review | Traceability becomes noisy and unusable |

### 16.6 Practical traceability chain in automotive

A realistic chain often looks like this:

```text
Vehicle Feature Requirement
    ↓ derives to
System Requirement
    ↓ allocated to
Subsystem / ECU Requirement
    ↓ refined into
Software Requirement
    ↓ allocated to
Software Architecture Component
    ↓ realized by
Code Module / Runnable / Service / Calibration
    ↓ verified by
Unit Test / Integration Test / SIL / HIL / Vehicle Test
    ↓ evidenced by
Logs / Reports / Reviews / Release Note
```

### 16.7 How to detect incomplete traceability

- Run reports for requirements with no child links.
- Run reports for software components with no parent requirements.
- Run reports for tests with no linked requirement or retired requirement.
- Compare requirement counts by baseline to test coverage counts.
- Check that rejected, deferred, and variant-specific requirements are explicitly marked rather than silently unlinked.
- Review derived requirements separately because they legitimately may not trace to customer wording but must trace to architectural rationale.

### 16.8 Realistic traceability matrix

| Vehicle Req | System Req | Subsystem/ECU Req | Software Req | Arch/Code Element | Verification Artifact | Status | Typical Gap Check |
|---|---|---|---|---|---|---|---|
| VEH-ADAS-001 | SYS-FCW-042 | ECU-ADAS-017 | SWR-FCW-021 | Cmp_FCWManager / Rbl_FCW_20ms | SYS-TC-FCW-017, HIL-TC-FCW-004 | Covered | Check timing log attached |
| VEH-ADAS-001 | SYS-FCW-043 | ECU-CLU-011 | SWR-CLU-055 | Cmp_WarningRenderer | SYS-TC-FCW-018 | Covered | Check cluster display evidence |
| VEH-ADAS-002 | SYS-AEB-010 | ECU-ADAS-022 | SWR-AEB-003 | Cmp_AEBDecision | SIL-TC-AEB-001, HIL-TC-AEB-009 | Covered | Check TTC threshold calibration |
| VEH-ADAS-002 | SYS-AEB-012 | ECU-ESC-008 | SWR-ESC-041 | BrakeReqGateway | INT-TC-AEB-ESC-003 | Covered | Check bus interface alignment |
| VEH-ADAS-003 | SYS-LKA-030 | ECU-EPS-005 | SWR-EPS-012 | TorqueAssistService | HIL-TC-LKA-005 | Covered | Check torque saturation limits |
| VEH-ADAS-004 | SYS-BSD-019 | ECU-ADAS-030 | SWR-BSD-015 | Cmp_BSDZoneMonitor | SIL-TC-BSD-006 | Covered | Check lane geometry assumptions |
| VEH-TCU-001 | SYS-TCU-004 | ECU-TCU-002 | SWR-TCU-008 | ECallManager | SYS-TC-ECALL-002 | Covered | Check crash event source |
| VEH-TCU-001 | SYS-TCU-007 | ECU-BACKEND-001 | SWR-CLOUD-014 | EmergencyPayloadService | INT-TC-ECALL-API-001 | Covered | Check backend ACK handling |
| VEH-TCU-002 | SYS-OTA-011 | ECU-TCU-014 | SWR-OTA-044 | DownloadResumeController | INT-TC-OTA-007 | Covered | Check resume CRC verification |
| VEH-TCU-003 | SYS-DIAG-021 | ECU-TCU-019 | SWR-DOIP-005 | DoIPSessionHandler | INT-TC-DOIP-003 | Covered | Check routing activation timeout |
| VEH-TCU-004 | SYS-CYB-032 | ECU-TCU-024 | SWR-AUTH-010 | RemoteCommandAuth | SEC-TC-RCMD-004 | Covered | Check certificate expiry path |
| VEH-CLU-001 | SYS-CLU-005 | ECU-CLU-003 | SWR-CLU-012 | SpeedDisplayService | HIL-TC-SPD-001 | Covered | Check scaling and rounding |
| VEH-CLU-002 | SYS-CLU-011 | ECU-CLU-007 | SWR-CLU-025 | TelltalePriorityManager | HIL-TC-TELL-004 | Covered | Check arbitration logic |
| VEH-CLU-003 | SYS-CLU-017 | ECU-CLU-014 | SWR-CLU-039 | BrightnessController | HIL-TC-DIM-003 | Covered | Check lux sensor fallback |
| VEH-CLU-004 | SYS-CLU-022 | ECU-CLU-018 | SWR-CLU-061 | BootSequenceManager | SYS-TC-BOOT-002 | Covered | Check 2 s boot target |
| VEH-ADAS-005 | SYS-ADAS-055 | ECU-ADAS-042 | SWR-ADAS-087 | SensorHealthMonitor | SIL-TC-DEG-005 | Covered | Check degraded mode entry |
| VEH-ADAS-006 | SYS-RCTA-012 | ECU-ADAS-051 | SWR-RCTA-006 | RearCrossTrafficFusion | HIL-TC-RCTA-003 | Covered | Check reverse gear dependency |
| VEH-TCU-005 | SYS-NET-013 | ECU-TCU-031 | SWR-MODEM-018 | BearerSelectionManager | INT-TC-NET-006 | Covered | Check fallback hysteresis |
| VEH-TCU-006 | SYS-GNSS-006 | ECU-TCU-034 | SWR-GNSS-009 | PositionMonitor | SIL-TC-GNSS-002 | Covered | Check reacquisition timer |
| VEH-CLU-005 | SYS-CLU-031 | ECU-CLU-028 | SWR-CLU-072 | OdometerNvMService | INT-TC-ODO-002 | Covered | Check retained value after reset |
| VEH-ADAS-007 | SYS-ACC-027 | ECU-ADAS-060 | SWR-ACC-032 | StopGoController | HIL-TC-ACC-010 | Covered | Check resume delay |
| VEH-ADAS-008 | SYS-PA-014 | ECU-ADAS-066 | SWR-PA-005 | ObstacleStopManager | HIL-TC-PA-004 | Covered | Check obstacle distance source |
| VEH-TCU-007 | SYS-PWR-009 | ECU-TCU-040 | SWR-BAT-011 | LowBackupBatteryMonitor | INT-TC-BAT-002 | Covered | Check threshold tolerance |
| VEH-CLU-006 | SYS-CLU-041 | ECU-CLU-035 | SWR-CLU-081 | SeatbeltChimeManager | HIL-TC-SB-003 | Covered | Check timing and cancel rule |
| VEH-ADAS-009 | SYS-ICD-004 | ECU-ADAS-071 | SWR-COM-022 | CanIf_FcwOutput | INT-TC-CAN-011 | Covered | Check sender/receiver timeout |
| VEH-TCU-008 | SYS-ICD-022 | ECU-TCU-045 | SWR-UDS-016 | DiagnosticSessionManager | INT-TC-UDS-005 | Covered | Check NRC behavior |
| VEH-ADAS-010 | SYS-AEB-018 | ECU-ADAS-075 | SWR-AEB-014 | FalsePositiveSuppressor | VEH-TC-AEB-012 | Partially Covered | Missing night-rain scenario |
| VEH-TCU-009 | SYS-OTA-019 | ECU-TCU-052 | SWR-OTA-063 | PackageVerifier | --- | Missing Verification | Test case not yet linked |
| VEH-CLU-007 | SYS-CLU-048 | ECU-CLU-041 | --- | --- | --- | Missing Implementation | Requirement approved without allocation |
| VEH-ADAS-011 | --- | --- | --- | --- | --- | Orphan Requirement | Parent feature request missing |

### 16.9 Interpreting the matrix

- Rows marked Covered show a healthy forward path from vehicle requirement to verification evidence.
- Partially Covered indicates that some verification exists but scenario completeness is missing.
- Missing Verification indicates implementation may exist but objective evidence is absent.
- Missing Implementation indicates the requirement was accepted but no architecture or software allocation has been made.
- Orphan Requirement indicates the requirement cannot be justified or decomposed correctly because its source or linkage is missing.

### 16.10 Traceability queries every project should be able to answer

- Which approved system requirements have no test case?
- Which automated regression tests verify safety-related requirements?
- Which software components are affected if SYS-AEB-010 changes TTC threshold logic?
- Which vehicle tests prove that a cluster telltale is shown under communication timeout?
- Which requirements are implemented by a supplier and which remain OEM responsibility?
- Which derived requirements were introduced by architecture after the latest baseline?

### 16.11 Good traceability practices

- Use stable unique identifiers and avoid reusing deleted IDs.
- Link requirements at the right granularity; atomic requirements should map to targeted verification assets.
- Document link semantics such as derives-from, satisfies, verifies, allocates-to, or refines.
- Baseline the matrix together with requirements and test specifications.
- Review traceability quality during milestone reviews, not only before audits.
- Automate link checking but still perform engineering review because automated links can be noisy or wrong.

---

## 17. REQUIREMENTS DECOMPOSITION

Automotive products are built by decomposition.
A vehicle-level intent becomes system-level technical behavior, then subsystem behavior, then ECU-level responsibilities, then software requirements, then component-level details.
Good decomposition preserves intent while increasing precision.

### 17.1 Typical decomposition chain

```text
Vehicle Requirement
    ↓
System Requirement
    ↓
Subsystem Requirement
    ↓
ECU Requirement
    ↓
Software Requirement
    ↓
Component Requirement
```

### 17.2 Key decomposition concepts

| Concept | Meaning | Typical Question |
|---|---|---|
| Allocation | Assigning a requirement to the element that will realize it | Which subsystem or ECU owns this behavior? |
| Decomposition | Breaking a broad requirement into smaller technical requirements | What lower-level statements are needed to realize this? |
| Derived requirement | A new requirement created because the chosen solution needs it | What new constraint appears because of architecture or implementation? |
| Interface requirement | A requirement defining how elements exchange data or control | What exactly is sent, when, by whom, and what happens on fault? |
| Responsibility assignment | Clarifying ownership for creation, implementation, verification, and release | Who is accountable for this requirement and its evidence? |

### 17.3 Rules for healthy decomposition

- Do not simply copy the parent text and rename the level; each level should add the detail needed by that engineering discipline.
- Preserve intent; lower-level requirements may be more specific, but they must not silently change behavior.
- Separate functional behavior from interface, timing, diagnostic, safety, and environmental details when needed.
- Create derived requirements explicitly rather than hiding them in architecture diagrams or code comments.
- Assign an owner and verification method at the level where the requirement becomes implementable.

### 17.4 Worked ADAS example: Automatic Emergency Braking

| Level | Example ID | Example requirement |
|---|---|---|
| Vehicle | VEH-AEB-001 | The vehicle shall reduce the severity of frontal collisions by automatically braking when a forward collision is imminent and the driver does not react in time. |
| System | SYS-AEB-010 | The AEB system shall request partial braking within 200 ms after TTC falls below 1.5 s while vehicle speed is between 10 km/h and 160 km/h and brake pedal is not pressed. |
| Subsystem | SUB-ADAS-004 | The ADAS sensing and decision subsystem shall compute TTC every 20 ms using fused radar and camera object tracks. |
| ECU | ECU-ADAS-022 | The ADAS domain controller shall publish AEB_BrakeRequest with 0.1 m/s² resolution on CAN FD every 10 ms. |
| Software | SWR-AEB-003 | The AEB decision module shall set BrakeStage = PARTIAL when TTC < 1.5 s for two consecutive cycles and driver brake demand < 10%. |
| Component | CMP-AEB-017 | Component AebDecision_Filter shall debounce TTC threshold crossings across two 20 ms samples before raising PARTIAL_BRAKE request. |

### 17.5 Why each level is different in the AEB example

- The vehicle level describes the customer-facing objective.
- The system level adds measurable trigger conditions and response expectations.
- The subsystem level introduces sensing and computational responsibilities.
- The ECU level defines deployment and communication ownership.
- The software level defines algorithmic state behavior.
- The component level defines detailed logic suitable for direct implementation and unit verification.

### 17.6 Derived requirements in AEB decomposition

- Because the AEB decision depends on fused objects, a derived requirement may be created for object timestamp freshness.
- Because brake requests are sent on CAN FD, a derived requirement may define counter and CRC behavior for message integrity.
- Because false positives are safety critical, a derived requirement may define suppression under stationary-object filtering conditions.
- Because the function is ASIL-relevant, a derived requirement may define monitoring for sensor plausibility and degraded mode entry.
- Because the function must be testable, a derived requirement may define diagnostic support for injecting TTC or object lists in HIL mode.

### 17.7 Interface requirements created by decomposition

- AEB request to ESC ECU.
- AEB warning request to cluster and infotainment chime controller.
- Radar and camera object list interfaces into the fusion subsystem.
- Mode management interface for feature enable/disable states.
- Diagnostic interfaces for freeze frame and DTC reporting.

### 17.8 Responsibility assignment example for an ADAS feature

| Artifact / Decision | Primary Owner | Support Owner | Typical Evidence |
|---|---|---|---|
| Vehicle requirement baseline | OEM feature owner | System engineer | Approved feature specification |
| System requirement decomposition | System requirements engineer | Safety engineer, architect | SyRS baseline, review minutes |
| ADAS algorithm allocation | System architect | ADAS tech lead | System architecture document |
| ECU interface definition | Network architect | ADAS ECU owner, ESC owner | ICD, DBC, ARXML |
| Software requirement authoring | Software requirements engineer | Algorithm lead | SwRS baseline |
| Component design | Software architect / developer | Test engineer | SwAD, design notes |
| Verification planning | Test architect | System and software leads | Verification specification |
| Validation scenario acceptance | Validation lead | Feature owner | Validation plan, proving ground reports |

### 17.9 Second ADAS example: Lane Keeping Assist decomposition

| Level | Example ID | Requirement |
|---|---|---|
| Vehicle | VEH-LKA-001 | The vehicle shall assist the driver in keeping the vehicle within the lane during highway driving. |
| System | SYS-LKA-030 | The LKA system shall provide steering assist torque between 60 km/h and 130 km/h when lane markings are valid and driver hands are detected on the steering wheel. |
| Subsystem | SUB-LKA-008 | The perception subsystem shall provide lane model confidence and curvature every 40 ms. |
| ECU | ECU-EPS-005 | The EPS ECU shall accept signed steering assist torque requests from the ADAS controller over CAN FD every 10 ms. |
| Software | SWR-LKA-019 | The LKA controller shall clamp requested torque to ±2.5 Nm and ramp out torque within 100 ms when hands-off is detected. |
| Component | CMP-LKA-031 | The torque arbitration component shall prioritize driver override torque over ADAS assist torque within one control cycle. |

### 17.10 Decomposition of non-functional requirements

- Performance requirements decompose into task execution time, bus latency budget, sensor freshness, and HMI update delay.
- Safety requirements decompose into diagnostics, fault detection, fault reaction, safe state, and independence constraints.
- Security requirements decompose into authentication, authorization, secure boot, integrity protection, logging, and key lifecycle requirements.
- Availability requirements decompose into startup behavior, fallback behavior, reset strategy, watchdog interaction, and communication recovery.
- Maintainability requirements decompose into diagnostics, serviceability, calibration access, and software update support.

### 17.11 Decomposition checklist

- Is the parent requirement fully represented by the child set?
- Do the children add necessary technical detail rather than duplicate wording?
- Are interfaces, timing, diagnostics, and degraded behavior addressed?
- Are derived requirements explicitly tagged and justified?
- Is responsibility assigned to a concrete subsystem, ECU, or component?
- Can each child requirement be verified at its level?
- Are lower-level assumptions compatible with parent-level constraints?

### 17.12 Common decomposition mistakes

- Skipping subsystem or ECU level and jumping directly from system requirement to code.
- Creating children that are design choices but not behavioral requirements.
- Splitting one atomic parent into overlapping children that cause contradictory implementations.
- Failing to create interface requirements when the function crosses ECU boundaries.
- Forgetting that failure behavior also needs decomposition, not only nominal behavior.

---

## 18. INTERFACE REQUIREMENTS

Many automotive integration problems are not algorithm defects but interface defects.
A function can be logically correct and still fail in the vehicle because a signal times out, a counter is misinterpreted, scaling is inconsistent, endianness is wrong, a CRC is not checked, or fault behavior is undefined.

### 18.1 What every interface requirement should define

- Signal or service name.
- Sender and receiver.
- Protocol or bus.
- Cycle time or event condition.
- Timeout and freshness expectation.
- Initial value and invalid value.
- Range, scaling, offset, and encoding.
- CRC and sequence counter behavior if applicable.
- Endianness or byte order.
- Fault behavior at sender and receiver side.

### 18.2 Generic interface requirement template

```text
The <sender> shall transmit <signal/service> to <receiver> over <bus/protocol> every <cycle time> or on <event>.
The signal shall use <encoding>, <range>, <scaling>, <endianness>, initial value <value>, invalid value <value>, timeout <value>, CRC <rule>, counter <rule>.
Upon timeout, invalid value, CRC failure, or counter discontinuity, the receiver shall <fault behavior>.
```

### 18.3 CAN requirement example — FCW warning request

| Attribute | Value |
|---|---|
| Requirement ID | IFC-CAN-001 |
| Signal / Service | FCW_WarnReq |
| Bus / Protocol | CAN |
| Sender | ADAS Domain Controller |
| Receiver | Instrument Cluster |
| Cycle time / Event | 20 ms periodic |
| Timeout | 100 ms |
| Initial value | 0x0 = No warning |
| Invalid value | 0x3 = Invalid |
| Range | 0..3 |
| Scaling | Enumerated, no scaling |
| Encoding | 2-bit enum |
| CRC | Not used at signal level; frame protected by CAN CRC |
| Counter | 4-bit rolling counter in frame payload |
| Endianness | Intel (little endian) |
| Fault behavior | If timeout or invalid value occurs, cluster shall remove FCW indication within 100 ms, log communication fault, and inhibit audible alert. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.4 CAN FD requirement example — AEB brake request

| Attribute | Value |
|---|---|
| Requirement ID | IFC-CANFD-002 |
| Signal / Service | AEB_BrakeReq |
| Bus / Protocol | CAN FD |
| Sender | ADAS Domain Controller |
| Receiver | ESC ECU |
| Cycle time / Event | 10 ms periodic |
| Timeout | 30 ms |
| Initial value | 0.0 m/s² |
| Invalid value | 0xFFF = Signal invalid |
| Range | 0.0..8.0 m/s² |
| Scaling | 0.01 m/s² per bit |
| Encoding | Unsigned 12-bit |
| CRC | 8-bit application CRC in payload |
| Counter | 4-bit rolling counter increments every frame |
| Endianness | Motorola (big endian) |
| Fault behavior | ESC shall ignore request with invalid CRC or stale counter and enter fallback deceleration = 0; DTC shall be stored after 3 consecutive failures. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.5 LIN requirement example — mirror fold command

| Attribute | Value |
|---|---|
| Requirement ID | IFC-LIN-003 |
| Signal / Service | MirrorFoldCmd |
| Bus / Protocol | LIN |
| Sender | Body Control Module |
| Receiver | Door ECU |
| Cycle time / Event | 50 ms periodic while command active |
| Timeout | 200 ms |
| Initial value | 0x0 = No action |
| Invalid value | 0x3 = Invalid |
| Range | 0..3 |
| Scaling | Enumerated, no scaling |
| Encoding | 2-bit enum |
| CRC | LIN classic checksum |
| Counter | Not used |
| Endianness | Little endian |
| Fault behavior | Door ECU shall stop mirror motor, keep current mirror position, and set local communication fault status if command times out. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.6 Automotive Ethernet requirement example — camera video stream

| Attribute | Value |
|---|---|
| Requirement ID | IFC-ETH-004 |
| Signal / Service | FrontCameraVideoStream |
| Bus / Protocol | 1000BASE-T1 Ethernet |
| Sender | Front Camera ECU |
| Receiver | ADAS Domain Controller |
| Cycle time / Event | 33.3 ms frame period at 30 fps |
| Timeout | 100 ms without valid frame |
| Initial value | No frame until stream start complete |
| Invalid value | Frame marked invalid in metadata flag |
| Range | 1280x720 YUV422 frames |
| Scaling | Pixel data raw; metadata fields as specified in ICD |
| Encoding | RTP payload over UDP |
| CRC | Ethernet FCS + stream payload checksum in metadata |
| Counter | 32-bit frame sequence counter |
| Endianness | Network byte order (big endian) |
| Fault behavior | Receiver shall declare camera unavailable after 100 ms without valid frame sequence, trigger degraded mode, and suppress camera-dependent ADAS functions. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.7 SOME/IP requirement example — vehicle localization service

| Attribute | Value |
|---|---|
| Requirement ID | IFC-SOMEIP-005 |
| Signal / Service | LocalizationPoseService.CurrentPose |
| Bus / Protocol | Automotive Ethernet / SOME-IP |
| Sender | Localization ECU |
| Receiver | ADAS Domain Controller |
| Cycle time / Event | 20 ms event group notification |
| Timeout | 80 ms |
| Initial value | Position validity = false |
| Invalid value | Validity flag = false or covariance > threshold |
| Range | Latitude, longitude, heading, velocity within defined struct bounds |
| Scaling | Double precision SI units |
| Encoding | SOME/IP serialized struct |
| CRC | Transport integrity by Ethernet FCS; no application CRC |
| Counter | 64-bit timestamp + 16-bit service update counter |
| Endianness | Big endian network order |
| Fault behavior | Receiver shall ignore stale pose, freeze previous trajectory planning input for max 60 ms, then transition to minimal-risk behavior if no valid update returns. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.8 DoIP requirement example — remote diagnostic activation

| Attribute | Value |
|---|---|
| Requirement ID | IFC-DOIP-006 |
| Signal / Service | DoIPRoutingActivationRequest |
| Bus / Protocol | DoIP over Ethernet |
| Sender | External Diagnostic Tester |
| Receiver | TCU / DoIP Gateway |
| Cycle time / Event | Event-triggered |
| Timeout | 2 s response timeout |
| Initial value | No session active |
| Invalid value | Unsupported activation type or malformed payload |
| Range | Payload length and fields as ISO 13400 profile |
| Scaling | Not applicable |
| Encoding | DoIP payload format |
| CRC | Ethernet FCS only |
| Counter | TCP sequence handled by stack; no application counter |
| Endianness | Big endian |
| Fault behavior | Gateway shall reject malformed request with standard negative response, not open routing path, and log security event on repeated failures. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.9 UDS requirement example — radar alignment routine control

| Attribute | Value |
|---|---|
| Requirement ID | IFC-UDS-007 |
| Signal / Service | UDS 0x31 RoutineControl RadarAlignment |
| Bus / Protocol | CAN / UDS |
| Sender | Diagnostic Tester |
| Receiver | ADAS ECU |
| Cycle time / Event | Event-triggered diagnostic request/response |
| Timeout | P2 = 50 ms, P2* = 5 s |
| Initial value | Routine idle |
| Invalid value | Unsupported sub-function or wrong session/security level |
| Range | Routine results 0..100% alignment status |
| Scaling | 1% per bit |
| Encoding | UDS service payload |
| CRC | CAN frame CRC only |
| Counter | Not used |
| Endianness | Big endian service payload |
| Fault behavior | ECU shall return NRC 0x22, 0x24, or 0x33 as applicable and shall not modify alignment status on invalid request. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.10 Sensor interface requirement example — IMU over SPI

| Attribute | Value |
|---|---|
| Requirement ID | IFC-SENSOR-008 |
| Signal / Service | YawRateSensorSample |
| Bus / Protocol | SPI |
| Sender | IMU Sensor |
| Receiver | ADAS Domain Controller |
| Cycle time / Event | 5 ms sample period |
| Timeout | 15 ms |
| Initial value | 0 deg/s with validity false until self-test pass |
| Invalid value | All-ones register value or sensor status invalid |
| Range | -250..250 deg/s |
| Scaling | 0.01 deg/s per bit |
| Encoding | Signed 16-bit two's complement |
| CRC | 8-bit SPI frame CRC |
| Counter | 8-bit sample counter |
| Endianness | Big endian register order |
| Fault behavior | Receiver shall discard sample on CRC or counter fault, raise IMU plausibility monitor, and transition to sensor degraded mode after 3 consecutive failures. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.11 Sensor interface requirement example — camera over MIPI CSI-2

| Attribute | Value |
|---|---|
| Requirement ID | IFC-SENSOR-009 |
| Signal / Service | LaneCameraRawFrames |
| Bus / Protocol | MIPI CSI-2 |
| Sender | Lane Camera Sensor |
| Receiver | Camera ECU SoC |
| Cycle time / Event | 40 ms frame period at 25 fps |
| Timeout | 120 ms |
| Initial value | Black-frame suppression until auto-exposure ready |
| Invalid value | Frame error flag set or exposure metadata invalid |
| Range | 1920x1080 RAW10 pixels |
| Scaling | Raw sensor values, no engineering scaling |
| Encoding | CSI-2 RAW10 packets |
| CRC | CSI-2 packet CRC/ECC |
| Counter | Frame counter in metadata |
| Endianness | Bit-packed sensor format as specified by sensor vendor |
| Fault behavior | Camera ECU shall drop invalid frames, flag perception unavailable, and command controlled function degradation after timeout. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.12 Actuator interface requirement example — electronic throttle PWM command

| Attribute | Value |
|---|---|
| Requirement ID | IFC-ACT-010 |
| Signal / Service | ThrottleMotorDutyCmd |
| Bus / Protocol | PWM |
| Sender | Powertrain Control Module |
| Receiver | Electronic Throttle Actuator |
| Cycle time / Event | 2 ms PWM update |
| Timeout | 10 ms watchdog in actuator driver |
| Initial value | 0% duty at ignition on |
| Invalid value | Duty < 5% or > 95% considered out of valid electrical range |
| Range | 5%..95% duty |
| Scaling | 0.1% duty per step |
| Encoding | Hardware PWM duty cycle |
| CRC | Not applicable |
| Counter | Not applicable |
| Endianness | Not applicable |
| Fault behavior | Actuator driver shall enter limp-home spring return on missing valid PWM updates and report fault to PCM. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.13 ECU-to-ECU interface requirement example — steering torque request

| Attribute | Value |
|---|---|
| Requirement ID | IFC-ECU-011 |
| Signal / Service | LKA_TorqueReq |
| Bus / Protocol | CAN FD |
| Sender | ADAS Domain Controller |
| Receiver | EPS ECU |
| Cycle time / Event | 10 ms periodic |
| Timeout | 30 ms |
| Initial value | 0.0 Nm |
| Invalid value | 0x7FFF = Invalid |
| Range | -3.0..3.0 Nm |
| Scaling | 0.01 Nm per bit |
| Encoding | Signed 16-bit two's complement |
| CRC | 16-bit application CRC across torque, mode, counter |
| Counter | 4-bit rolling counter |
| Endianness | Motorola big endian |
| Fault behavior | EPS shall ramp requested assist torque to zero within 50 ms on timeout, invalid value, CRC failure, or counter discontinuity. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.14 ECU-to-ECU interface requirement example — cluster telltale status

| Attribute | Value |
|---|---|
| Requirement ID | IFC-ECU-012 |
| Signal / Service | AEB_TelltaleStatus |
| Bus / Protocol | CAN |
| Sender | Instrument Cluster |
| Receiver | ADAS Domain Controller |
| Cycle time / Event | 100 ms periodic |
| Timeout | 300 ms |
| Initial value | 0x0 = Off |
| Invalid value | 0x3 = Invalid |
| Range | 0..3 |
| Scaling | Enumerated |
| Encoding | 2-bit enum |
| CRC | CAN frame CRC only |
| Counter | No application counter |
| Endianness | Little endian |
| Fault behavior | ADAS controller shall log HMI acknowledgment loss if the telltale status is invalid or not refreshed within timeout. |

- Review note: sender and receiver behavior must be defined separately if either side has safety responsibility.
- Review note: timeout should be justified from cycle time, network jitter, and system reaction budget.
- Review note: initial and invalid values must not accidentally trigger the controlled function.

### 18.15 Interface requirement review questions

- Is the sender unambiguously identified?
- Is every intended receiver listed?
- Are cycle time and timeout consistent with system timing requirements?
- Are scaling and engineering units defined?
- Is byte order defined for multi-byte signals?
- Are CRC and counter semantics documented where needed?
- Is degraded or fail-safe receiver behavior defined?
- Does the interface support diagnostics and service modes if required?
- Are startup and shutdown conditions defined?
- Is bus load or bandwidth impact understood?

---

## 19. TIMING REQUIREMENTS

Timing defects are among the hardest automotive defects to find late because the system may appear logically correct yet still fail due to scheduling, synchronization, latency, overload, or timeout interactions.
Good timing requirements make dynamic behavior explicit and measurable.

### 19.1 Core timing terms

| Term | Meaning | Automotive example |
|---|---|---|
| Response time | Elapsed time from trigger to completed response | Time from FCW TTC threshold crossing to cluster warning display |
| Latency | Delay between source data/event and availability at destination | Delay from radar measurement timestamp to fused object delivery |
| Cycle time | Periodic execution or transmission interval | 10 ms control task or 20 ms CAN signal period |
| Timeout | Maximum tolerated interval without expected event/data | Receiver declares signal stale after 100 ms |
| Jitter | Variation around expected periodicity or response time | Task expected every 10 ms but varies between 9.5 and 10.8 ms |
| Deadline | Latest acceptable completion time | Brake request must be issued before 200 ms after trigger |
| Execution time | CPU time required by software element | Lane model update runnable executes in 2.4 ms worst case |
| Fault reaction time | Time from fault detection to safe or degraded response | Sensor timeout to feature disable within 150 ms |
| FTTI | Fault Tolerant Time Interval | Maximum time from hazardous fault occurrence until safety measure must control risk |
| Watchdog timeout | Maximum allowed absence of life indication before reset/fault action | Supervised task must kick watchdog within 50 ms |

### 19.2 Response time

- Response time is typically defined from an observable trigger to an observable effect.
- The trigger must be precise: threshold crossing, message arrival, driver action, ignition state, or diagnostic request.
- The endpoint must be precise: actuator command sent, telltale displayed, DTC set, or backend acknowledgment received.
- Response time often includes sensing, communication, scheduling, application logic, and output actuation.
- If the trigger or endpoint is vague, test engineers will measure different things and claim contradictory results.

Example:

```text
Requirement: The FCW system shall display a visual warning within 300 ms after TTC falls below 2.2 s.
Trigger timestamp: First sample in which TTC < 2.2 s and validity = true.
End timestamp: First cluster frame in which FCW warning icon state = active.
```

### 19.3 Latency

- Latency usually applies to data transport or processing pipelines.
- A sensor sample may be timestamped at measurement, preprocessed, transmitted, fused, and then consumed by a control algorithm.
- Latency matters because stale data can produce unsafe control decisions even if software execution itself is fast.
- Freshness should be defined together with latency and timeout requirements.
- Timestamp propagation is often essential for measuring true end-to-end latency.

### 19.4 Cycle time

- Cycle time defines how often a periodic activity is expected to occur.
- Examples include task activation rate, network transmission period, polling interval, and backend heartbeat interval.
- Cycle time directly influences CPU load, network load, freshness, and response capability.
- A requirement should clarify whether a value is nominal, maximum, minimum, or tolerance band.
- Cycle times must be consistent across related elements: producer task, communication stack, receiver task, and monitor timeout.

### 19.5 Timeout

- Timeout is a fault-detection requirement.
- A timeout too short creates nuisance faults under normal jitter and startup transitions.
- A timeout too long delays fault reaction and can violate safety goals or user expectations.
- Timeout must be based on cycle time, jitter, startup behavior, and fault reaction budget.
- Timeout behavior must specify what happens after expiration: inhibit feature, keep last value for grace period, substitute fallback value, log DTC, or reset channel.

### 19.6 Jitter

- Jitter is the variation around an expected time point or period.
- It matters in control systems, synchronized displays, sensor fusion, and communication supervision.
- A 10 ms task with ±2 ms jitter may be acceptable for diagnostics but not for torque control.
- Requirements should distinguish one-time outliers from worst-case continuous jitter.
- Jitter often needs to be specified for both sender and receiver timing behavior.

### 19.7 Deadline

- A deadline is the latest time by which a result must be available or an action must occur.
- Unlike generic response time, a deadline is often tied to acceptability or safety.
- Missing a deadline can mean the function is considered failed even if the result eventually arrives.
- Deadlines are common in AEB, telltale rendering, torque arbitration, watchdog kicking, and diagnostic acknowledgments.
- Deadlines should be testable with timestamped evidence.

### 19.8 Execution time

- Execution time is the processing time consumed by a software element on its execution platform.
- Requirements may reference average, worst-case, or percentile execution time depending on the safety/performance need.
- Execution time must consider caches, interrupts, concurrent load, and representative compiler optimization settings.
- A software element can meet functional behavior and still cause timing failure if execution time breaks system schedulability.
- Execution time budgets should be allocated from higher-level response budgets.

### 19.9 Fault reaction time

- Fault reaction time measures how fast the system moves from fault detection to a defined safe or degraded response.
- Example: if front camera frames stop arriving, the lane keeping assist shall be disabled and driver informed within 150 ms.
- It is different from fault detection time; together they contribute to FTTI consumption.
- Requirements must define the detection event and the required reaction endpoint.
- Safety-related fault reaction times should trace to hazard analysis assumptions.

### 19.10 FTTI

- FTTI is the maximum time available from occurrence of a hazardous fault until the system must control the risk sufficiently.
- FTTI is usually established during safety analysis and then allocated across detection, communication, decision, and actuation steps.
- If total fault detection plus reaction exceeds FTTI, the safety concept is not viable.
- Requirements engineers should avoid quoting FTTI as a generic performance number; it is a safety-derived timing budget.
- Lower-level requirements must consume only their allocated share of the FTTI budget.

### 19.11 Watchdog timeout

- A watchdog timeout supervises software or hardware health by expecting periodic alive indications or timely task completion.
- Requirements should define who kicks the watchdog, at what rate, under what conditions, and what happens if the kick is missed.
- Windowed watchdogs may specify both minimum and maximum kick times.
- A reset reaction may be acceptable in one ECU state but dangerous in another, so context matters.
- Watchdog requirements should align with startup, shutdown, bootloader, and diagnostic session behavior.

### 19.12 Example timing budgets

| Function | Trigger | Budget Element | Allocated Time |
|---|---|---|---|
| FCW warning | TTC threshold crossing | Sensor freshness + fusion update | 80 ms |
| FCW warning | TTC threshold crossing | Decision logic task scheduling + execution | 40 ms |
| FCW warning | TTC threshold crossing | CAN transmission to cluster | 20 ms |
| FCW warning | TTC threshold crossing | Cluster rendering delay | 160 ms |
| AEB brake request | TTC threshold crossing | Object list freshness | 50 ms |
| AEB brake request | TTC threshold crossing | AEB decision execution | 30 ms |
| AEB brake request | TTC threshold crossing | CAN FD transmission to ESC | 10 ms |
| AEB brake request | TTC threshold crossing | ESC acceptance and actuation start | 110 ms |
| Cluster telltale | CAN signal reception | Application decoding | 20 ms |
| Cluster telltale | CAN signal reception | Graphics scheduling and render | 180 ms |
| eCall initiation | Crash trigger | Crash event debounce | 100 ms |
| eCall initiation | Crash trigger | Cellular session establishment | 2 s |

### 19.13 Example timing requirements

- The ADAS controller shall publish AEB_BrakeReq within 10 ms after the end of the cycle in which TTC < 1.5 s is confirmed.
- The cluster shall illuminate the seatbelt telltale within 200 ms after SeatbeltStatus changes from Buckled to Unbuckled while ignition state = RUN.
- The TCU shall respond to a DoIP routing activation request within 2 s under nominal network conditions.
- The lane model processing runnable shall complete within 4 ms worst case on the target SoC at 85% CPU background load.
- Upon front camera timeout, LKA shall transition to unavailable state and remove steering torque request within 150 ms.

### 19.14 Timing requirement anti-patterns

- “The system shall respond quickly.”
- “The ECU shall have low latency.”
- “The function shall not delay the driver.”
- “Warnings shall be shown immediately.”
- These statements are unusable because trigger, endpoint, and measurable values are missing.

### 19.15 Timing review questions

- What exact event starts the timer?
- What exact event stops the timer?
- Is the timing value maximum, minimum, or nominal?
- Is jitter tolerated and bounded?
- Is timeout derived from cycle time and network behavior?
- Is degraded mode timing defined separately?
- Does the allocated timing fit within safety budgets such as FTTI?

---

## 20. REQUIREMENTS REVIEW

Professional requirement reviews prevent defects from escaping into architecture, code, and test where they become much more expensive to fix.
A strong review is disciplined, evidence-based, and defect-oriented.

### 20.1 Purpose of a requirement review

- Detect ambiguity before implementation starts.
- Find missing conditions, boundaries, and failure behaviors.
- Confirm technical feasibility and consistency with architecture constraints.
- Ensure the requirement is testable and traceable.
- Identify safety, security, interface, and timing implications early.

### 20.2 Typical review roles

| Role | Primary contribution |
|---|---|
| Author | Explains intent and proposed requirement text |
| Moderator | Enforces review method and defect capture |
| System architect | Checks allocation, interfaces, and consistency with architecture |
| Software architect / lead | Checks implementability and software impact |
| Test engineer | Checks measurability and verification strategy |
| Safety engineer | Checks safety assumptions, safe state, and FTTI-related implications |
| Cybersecurity engineer | Checks authentication, integrity, access control, and abuse cases |
| Calibration / vehicle engineer | Checks operating ranges and realistic usage conditions |

### 20.3 Review defect categories

- Ambiguity: multiple interpretations are possible.
- Omission: a required condition, boundary, or mode is missing.
- Contradiction: the requirement conflicts with another requirement or interface definition.
- Non-testability: pass/fail cannot be objectively assessed.
- Incorrect units or scaling: values are dimensionally unclear or inconsistent.
- Unrealistic feasibility: platform or bus constraints make the value implausible.
- Safety gap: hazardous failure behavior or fault reaction not addressed.
- Security gap: misuse, spoofing, integrity, or authentication concern not addressed.

### 20.4 How to review for ambiguity

- Flag words like quickly, correctly, sufficient, appropriate, optimized, user-friendly, robust, immediate, and minimal.
- Check whether pronouns or vague subjects like “the system” hide ownership.
- Check whether conditions are implicitly assumed rather than stated.
- Ask whether two engineers would implement the same behavior independently.
- If not, the requirement is ambiguous.

### 20.5 How to review for missing conditions

- Look for operating mode dependencies such as ignition state, speed range, gear state, network availability, or environmental validity.
- Check startup, shutdown, diagnostic session, and degraded mode behavior.
- Check whether the requirement applies under manual override or driver intervention.
- Check whether variant coding or market conditions affect applicability.
- Check whether preconditions for valid sensor input are defined.

### 20.6 How to review for missing failure behavior

- Ask what should happen if input data is invalid, stale, or contradictory.
- Ask what happens on bus timeout, reset, low voltage, or sensor degradation.
- Ask whether the function should fail silent, fail operational, or transition to a safe state.
- Ask whether the driver or technician should be informed.
- Ask whether a DTC, event memory, or backend report is required.

### 20.7 How to review for incorrect units and missing boundaries

- Verify engineering units are explicit: km/h, m/s², Nm, %, ms, °C, V.
- Check scaling, offset, and representation for interface values.
- Look for missing minimum and maximum values.
- Check inclusivity/exclusivity of thresholds such as <, ≤, >, ≥.
- Confirm boundary tolerances and rounding rules where display or conversion is involved.

### 20.8 How to review for missing timing

- If a behavior is time-sensitive, ask whether response time, cycle time, timeout, or deadline is needed.
- Check whether timing is realistic for the platform and bus architecture.
- Check whether timeout and fault reaction time align with safety needs.
- Ensure start and end measurement points are clear.
- Make sure the intended timing can be measured in the target environment.

### 20.9 How to review for contradictions

- Compare the requirement with parent requirements and sibling requirements.
- Compare with DBC, ICD, ARXML, and architecture assumptions.
- Check for conflicting thresholds across variants or markets.
- Check whether one requirement says the feature shall inhibit itself while another says it shall remain available in the same state.
- Contradictions are especially common when multiple teams own adjacent interfaces.

### 20.10 How to review for testability

- Can a specific stimulus be applied?
- Can the expected result be observed objectively?
- Are pass/fail criteria measurable?
- Does the requirement define applicable environment and preconditions?
- Can verification be assigned to a clear test level?

### 20.11 How to review safety implications

- Determine whether failure of the requirement contributes to a hazardous event.
- Check for safe state, degraded mode, or warning strategy.
- Check whether diagnostic coverage or reaction time constraints are needed.
- Check consistency with HARA, FSC, TSC, and safety requirements.
- Check whether latent fault handling or monitoring requirements are missing.

### 20.12 How to review security implications

- Could the behavior be abused if an attacker injects messages or unauthorized commands?
- Is authenticity or integrity protection needed?
- Does remote activation require authentication, authorization, rate limiting, or logging?
- Does the requirement leak sensitive data or allow unsafe diagnostics in drive state?
- Are secure failure behaviors defined when trust cannot be established?

### 20.13 Requirements review checklist

| Category | Checklist question |
|---|---|
| Clarity | Is the subject/owner explicit? |
| Clarity | Is every ambiguous term removed or quantified? |
| Completeness | Are preconditions stated? |
| Completeness | Are operating modes stated? |
| Completeness | Are startup and shutdown behaviors covered? |
| Completeness | Are degraded and fault states covered? |
| Boundaries | Are min/max limits stated? |
| Boundaries | Are thresholds inclusive/exclusive as intended? |
| Units | Are engineering units explicit? |
| Units | Are scaling and offsets defined where applicable? |
| Timing | Is response time, timeout, cycle time, or deadline needed? |
| Timing | Are measurement start/end points defined? |
| Interfaces | Are sender, receiver, and protocol defined? |
| Interfaces | Are invalid value and timeout reactions defined? |
| Consistency | Does it conflict with parent or sibling requirements? |
| Consistency | Does it align with ICD/DBC/ARXML definitions? |
| Verification | Is there an objective verification method? |
| Verification | Can pass/fail be measured? |
| Safety | Is safe state or safe reaction defined if needed? |
| Safety | Is fault reaction time or FTTI impact addressed if relevant? |
| Security | Are misuse and unauthorized access concerns considered? |
| Security | Is integrity/authentication needed? |
| Traceability | Does it have a valid parent or derived rationale? |
| Traceability | Is downstream allocation expected and feasible? |
| Ownership | Is implementation owner clear? |
| Ownership | Is verification owner clear? |
| Variants | Is market/variant applicability defined? |
| Diagnostics | Are DTC/reporting/service behaviors needed? |
| Environmental | Are temperature, voltage, network, or sensor assumptions needed? |
| Usability | Could the behavior confuse or annoy the driver? |

### 20.14 Review example

Bad requirement:

```text
The cluster shall quickly show the collision warning when required.
```

Review findings:
- Ambiguous: “quickly” is undefined.
- Ambiguous: “when required” is undefined.
- Missing trigger condition: which signal or event activates the warning?
- Missing timing: no response time or deadline.
- Missing fault behavior: what if the warning request signal is invalid or times out?
- Missing operating conditions: is the behavior valid in startup, transport mode, or display-test mode?

Improved requirement:

```text
The instrument cluster shall display the FCW warning icon within 200 ms after reception of FCW_WarnReq = Active from the ADAS controller while ignition state = RUN and display self-test mode = inactive.
If FCW_WarnReq is invalid or not received for 100 ms, the cluster shall remove the FCW warning icon and store communication fault event CLU_COMM_FCW_01.
```

### 20.15 Good review outputs

- Defect list with severity and owner.
- Updated requirement text or change requests.
- Rationale for accepted assumptions.
- Link updates if derived requirements were created.
- Evidence that review findings were closed before baseline approval.

---

## 21. REQUIREMENTS VALIDATION

Validation and verification are often confused.
Automotive engineers must distinguish them clearly because they answer different questions and use different evidence.

### 21.1 The four concepts that are commonly mixed up

| Concept | Main Question | Object under examination | Typical evidence |
|---|---|---|---|
| Requirement validation | Did we specify the right requirement? | The requirement statement itself | Stakeholder review, use-case review, scenario walkthrough, expert judgment |
| Requirement verification | Is the requirement statement well-formed and compliant with rules? | The requirement statement itself | Checklist review, quality rule checks, peer review findings |
| System verification | Did the built system meet the specified technical requirements? | Implemented system | Requirement-based tests, measurements, analysis, inspections |
| System validation | Does the built system satisfy intended use in real context? | Implemented system in operational context | Vehicle trials, user acceptance, proving ground scenarios, fleet evidence |

### 21.2 Requirement verification vs requirement validation

- Requirement verification is about quality of the requirement statement.
- Requirement validation is about correctness of the requirement intent relative to stakeholder need.
- A requirement can be verified as well-written yet still be invalid because it specifies the wrong threshold or wrong user behavior.
- Example: “The system shall warn at TTC < 2.2 s” may be grammatically perfect, but validation may show that drivers need 2.8 s in certain vehicle classes.
- Therefore both activities are necessary and complementary.

### 21.3 System verification vs system validation

- System verification checks conformance to the approved technical specification.
- System validation checks fitness for intended use in real operational scenarios.
- A system may pass verification and still fail validation if nuisance behavior is unacceptable or if driver understanding is poor.
- Example: an FCW function may consistently warn within 300 ms as specified, yet validation may show too many false warnings in urban traffic.
- Validation is especially critical for ADAS, HMIs, comfort functions, and connected services where human interaction matters.

### 21.4 Automotive examples

**Example A — Requirement verification**

- Requirement text: “The cluster shall display low fuel warning below 8 liters.”
- Review checks whether units, threshold, mode conditions, and testability are clear.
- Finding: missing hysteresis and missing sensor fault behavior.

**Example B — Requirement validation**

- Vehicle clinics and field analysis may show that 8 liters is too late for customer expectation in certain markets.
- Stakeholders decide the right threshold is 10 liters with range prediction support.
- The original requirement was well-written but not the right one.

**Example C — System verification**

- On HIL and vehicle test, engineers prove the low-fuel warning appears below 10 liters within 500 ms and clears above 12 liters.
- This confirms the built cluster behavior matches the revised specification.

**Example D — System validation**

- In real customer journeys, users confirm the warning provides enough time to refuel and is understandable.
- This demonstrates the feature meets intended use.

### 21.5 Requirement validation methods

- Scenario walkthroughs with domain experts.
- Use-case simulation and customer journey review.
- Benchmark comparison with target competitors or previous vehicle generation.
- Safety and misuse-case review.
- Service and maintenance workflow review.
- Prototype or mock-up evaluation for HMI-heavy features.

### 21.6 Signs that a requirement has not been validated

- Frequent changes late in vehicle test because the specified behavior annoys users.
- A technically correct requirement produces false positives or false negatives in real traffic.
- Service teams report that diagnostic behavior is unusable in workshops.
- Regional or legal operating realities were not considered.
- The driver interaction was never reviewed outside the engineering team.

### 21.7 Clear mental model

```text
Requirement Verification = Is the requirement written correctly?
Requirement Validation   = Is it the correct requirement to satisfy stakeholder intent?
System Verification      = Did we build the system according to the specified requirements?
System Validation        = Did we build the right system for real use?
```

### 21.8 Validation pitfalls

- Using only lab pass/fail tests and calling that validation.
- Assuming customer intent is fully captured by the first feature concept.
- Ignoring misuse, environment, and human behavior.
- Treating validation as a final phase rather than a recurring learning activity.
- Not feeding validation results back into requirement updates and traceability.

---

## 22. REQUIREMENT-BASED TESTING

Requirement-based testing means every planned test is intentionally derived from one or more approved requirements, with clear expected results and traceability.
In automotive programs, requirement-based testing provides coverage visibility, audit evidence, regression control, and change impact support.

### 22.1 Why requirement-based testing matters

- It proves that tests are aligned with approved behavior rather than with tester assumptions.
- It exposes weak or untestable requirements early because test design becomes impossible.
- It enables coverage reporting at vehicle, system, software, and component levels.
- It supports selective regression when a requirement changes.
- It is essential for ASPICE, ISO 26262, and supplier acceptance evidence.

### 22.2 Converting a requirement into a test

- Identify the exact requirement statement and any parent/child links.
- Extract trigger, preconditions, expected behavior, timing, limits, and failure reactions.
- Determine the most appropriate test level and environment.
- Choose the test design technique: positive, negative, boundary, robustness, timing, fault injection, safety, or regression.
- Define objective pass/fail criteria and evidence to collect.

### 22.3 Test design categories

| Category | Purpose | Example |
|---|---|---|
| Positive test | Prove nominal behavior under valid conditions | Verify AEB warning appears when TTC threshold is crossed |
| Negative test | Prove behavior does not occur under excluded conditions | Verify AEB does not trigger when driver brake pedal is already pressed |
| Boundary test | Check threshold edges and inclusivity/exclusivity | Verify cluster low fuel warning exactly at 10.0 L and 10.1 L |
| Robustness test | Check resilience under noise, intermittent input, or abnormal but plausible conditions | Verify TCU resumes OTA download after network interruption |
| Timing test | Measure response times, latency, and deadlines | Verify FCW warning within 300 ms |
| Fault injection test | Inject invalid, stale, or corrupt data | Inject CAN counter fault and verify receiver degrades gracefully |
| Safety test | Demonstrate safe state or safety mechanism | Verify LKA torque ramps to zero on camera timeout |
| Regression test | Protect behavior after changes | Re-run previously passed requirement tests after software update |

### 22.4 Requirement-to-test transformation example

Requirement:

```text
SYS-CLU-011: The cluster shall illuminate the seatbelt telltale within 200 ms after SeatbeltStatus changes from Buckled to Unbuckled while ignition state = RUN.
```

Derived tests:
- Positive: Unbuckle during RUN and measure telltale response time.
- Negative: Change SeatbeltStatus while ignition = OFF and verify telltale does not illuminate.
- Boundary: Toggle status exactly at state transition from ACC to RUN and verify defined behavior.
- Fault injection: Send invalid SeatbeltStatus and verify cluster enters fallback or logs fault as specified.
- Regression: Re-run after cluster graphics stack update.

### 22.5 Requirement sets used for the example test catalog

ADAS requirement set:
| Requirement ID | Title | Requirement summary |
|---|---|---|
| ADAS-SYS-REQ-001 | FCW warning timing | Issue visual and audible FCW warning within 300 ms when TTC < 2.2 s and system valid. |
| ADAS-SYS-REQ-002 | AEB partial braking | Request partial braking when TTC < 1.5 s for two consecutive cycles and driver brake demand < 10%. |
| ADAS-SYS-REQ-003 | AEB low-speed inhibit | Do not trigger AEB braking below 5 km/h. |
| ADAS-SYS-REQ-004 | ACC stop-and-go resume | Resume following within 1.0 s after lead vehicle moves when ACC remains active and driver hold condition is false. |
| ADAS-SYS-REQ-005 | LKA assist speed window | Provide LKA steering assist only between 60 km/h and 130 km/h with valid lane model and hands-on detected. |
| ADAS-SYS-REQ-006 | Blind spot warning | Generate blind spot warning when a target is present in adjacent lane zone for more than 200 ms. |
| ADAS-SYS-REQ-007 | Rear cross traffic alert | Warn during reverse when cross-traffic target closing speed exceeds threshold and rear visibility zone is occupied. |
| ADAS-SYS-REQ-008 | Parking obstacle stop | Request stop when obstacle distance becomes less than or equal to 0.50 m during automated parking maneuver. |
| ADAS-SYS-REQ-009 | Sensor degraded mode | Enter degraded mode and inhibit dependent functions within 150 ms after front camera timeout > 100 ms. |
| ADAS-SYS-REQ-010 | Hands-on monitoring | Ramp out LKA torque within 100 ms after hands-off state persists for 1.5 s. |

TCU requirement set:
| Requirement ID | Title | Requirement summary |
|---|---|---|
| TCU-SYS-REQ-001 | eCall initiation | Start emergency call session within 5 s after confirmed crash event if cellular service is available. |
| TCU-SYS-REQ-002 | GNSS reacquisition | Restore valid GNSS position within 30 s after tunnel exit under open-sky conditions. |
| TCU-SYS-REQ-003 | OTA resume download | Resume interrupted OTA package download from last verified chunk within 60 s after network restoration. |
| TCU-SYS-REQ-004 | Network bearer fallback | Switch from 5G/LTE to lower available bearer within 10 s after radio link loss while preserving telematics session state when possible. |
| TCU-SYS-REQ-005 | Remote unlock security | Accept remote door unlock command only when message signature, freshness token, and vehicle state authorization are valid. |
| TCU-SYS-REQ-006 | Periodic status upload | Upload vehicle health status every 60 s while ignition = RUN and backend session active. |
| TCU-SYS-REQ-007 | DoIP readiness | Accept DoIP routing activation within 2 s after Ethernet link-up and ignition state = SERVICE or RUN. |
| TCU-SYS-REQ-008 | Backup battery low warning | Report telematics backup battery low event within 10 s after measured voltage falls below threshold for 5 s. |
| TCU-SYS-REQ-009 | Roaming restriction | Block non-emergency data sessions when roaming is disabled by configuration, except approved regulatory services. |
| TCU-SYS-REQ-010 | Secure remote command audit | Store authenticated audit log entry within 1 s for every accepted remote control command. |

Cluster requirement set:
| Requirement ID | Title | Requirement summary |
|---|---|---|
| CLU-SYS-REQ-001 | Speed display accuracy | Display vehicle speed within ±1 km/h of validated vehicle speed input from 20 km/h to 180 km/h. |
| CLU-SYS-REQ-002 | Seatbelt telltale timing | Illuminate seatbelt telltale within 200 ms after SeatbeltStatus changes to Unbuckled while ignition = RUN. |
| CLU-SYS-REQ-003 | Low fuel warning threshold | Show low fuel warning when filtered fuel level falls below 10.0 L and clear it only when fuel level exceeds 12.0 L. |
| CLU-SYS-REQ-004 | Warning priority arbitration | Display highest-priority active warning according to priority table without suppressing legally mandatory telltales. |
| CLU-SYS-REQ-005 | Boot readiness | Reach normal operation display state within 2.0 s after KL15 = ON. |
| CLU-SYS-REQ-006 | Auto dimming | Adjust display brightness within 500 ms after ambient light class changes under auto-brightness mode. |
| CLU-SYS-REQ-007 | Gear position fallback | Display gear position as “--” within 300 ms when transmission gear signal becomes invalid or timed out. |
| CLU-SYS-REQ-008 | Odometer retention | Retain odometer value across ignition cycles and resets with maximum loss of 0.1 km. |
| CLU-SYS-REQ-009 | Turn indicator synchronization | Flash turn indicator telltale synchronized with body controller command at 1.5 Hz ± 0.1 Hz. |
| CLU-SYS-REQ-010 | Seatbelt chime coordination | Generate seatbelt audible chime and telltale according to buckle status, speed threshold, and timeout rules. |

### 22.6 Large requirement-based test catalog

The following catalog provides **120 requirement-based test examples** across ADAS, TCU, and Cluster domains.
Each example is intentionally traceable, concrete, and audit-friendly.

#### RBT-ADAS-001 — FCW warning timing — Positive test

- Requirement ID: ADAS-SYS-REQ-001
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: FCW warning timing.
- Preconditions: Vehicle speed = 60 km/h, FCW enabled, sensors valid, cluster reachable.
- Test stimulus: Decrease TTC from 2.6 s to below 2.2 s using replay scenario.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: TTC threshold timestamp, warning icon timestamp, chime timestamp.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-001 → RBT-ADAS-001 → execution report / regression suite entry.

#### RBT-ADAS-002 — FCW warning timing — Negative test

- Requirement ID: ADAS-SYS-REQ-001
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: FCW warning timing.
- Preconditions: Vehicle speed = 60 km/h, FCW enabled, sensors valid, cluster reachable.
- Test stimulus: Driver warning already acknowledged mute active.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: TTC threshold timestamp, warning icon timestamp, chime timestamp.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-001 → RBT-ADAS-002 → execution report / regression suite entry.

#### RBT-ADAS-003 — FCW warning timing — Boundary test

- Requirement ID: ADAS-SYS-REQ-001
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: FCW warning timing.
- Preconditions: Vehicle speed = 60 km/h, FCW enabled, sensors valid, cluster reachable.
- Test stimulus: TTC values = 2.21 s, 2.20 s, 2.19 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: TTC threshold timestamp, warning icon timestamp, chime timestamp.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-001 → RBT-ADAS-003 → execution report / regression suite entry.

#### RBT-ADAS-004 — FCW warning timing — Robustness test

- Requirement ID: ADAS-SYS-REQ-001
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: FCW warning timing.
- Preconditions: Vehicle speed = 60 km/h, FCW enabled, sensors valid, cluster reachable.
- Test stimulus: Delay cluster CAN reception by 120 ms or inject invalid warning signal.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: TTC threshold timestamp, warning icon timestamp, chime timestamp.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-001 → RBT-ADAS-004 → execution report / regression suite entry.

#### RBT-ADAS-005 — AEB partial braking — Positive test

- Requirement ID: ADAS-SYS-REQ-002
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: AEB partial braking.
- Preconditions: Vehicle speed = 50 km/h, brake pedal demand = 0%, target vehicle decelerates.
- Test stimulus: Force TTC below 1.5 s for two consecutive control cycles.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: BrakeStage output, brake request value, time to request.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-002 → RBT-ADAS-005 → execution report / regression suite entry.

#### RBT-ADAS-006 — AEB partial braking — Negative test

- Requirement ID: ADAS-SYS-REQ-002
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: AEB partial braking.
- Preconditions: Vehicle speed = 50 km/h, brake pedal demand = 0%, target vehicle decelerates.
- Test stimulus: Driver brake demand set to 15% during threshold crossing.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: BrakeStage output, brake request value, time to request.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-002 → RBT-ADAS-006 → execution report / regression suite entry.

#### RBT-ADAS-007 — AEB partial braking — Boundary test

- Requirement ID: ADAS-SYS-REQ-002
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: AEB partial braking.
- Preconditions: Vehicle speed = 50 km/h, brake pedal demand = 0%, target vehicle decelerates.
- Test stimulus: TTC = 1.51 s, 1.50 s, 1.49 s and one-cycle/two-cycle persistence.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: BrakeStage output, brake request value, time to request.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-002 → RBT-ADAS-007 → execution report / regression suite entry.

#### RBT-ADAS-008 — AEB partial braking — Robustness test

- Requirement ID: ADAS-SYS-REQ-002
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: AEB partial braking.
- Preconditions: Vehicle speed = 50 km/h, brake pedal demand = 0%, target vehicle decelerates.
- Test stimulus: Inject single-cycle TTC glitch, CAN FD counter error on brake request, or stale object list.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: BrakeStage output, brake request value, time to request.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-002 → RBT-ADAS-008 → execution report / regression suite entry.

#### RBT-ADAS-009 — AEB low-speed inhibit — Positive test

- Requirement ID: ADAS-SYS-REQ-003
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: AEB low-speed inhibit.
- Preconditions: AEB enabled, target object present, driver inactive.
- Test stimulus: Reduce ego speed toward 5 km/h while maintaining low TTC.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Brake request presence or absence and inhibit flag.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-003 → RBT-ADAS-009 → execution report / regression suite entry.

#### RBT-ADAS-010 — AEB low-speed inhibit — Negative test

- Requirement ID: ADAS-SYS-REQ-003
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: AEB low-speed inhibit.
- Preconditions: AEB enabled, target object present, driver inactive.
- Test stimulus: Set ego speed = 4 km/h and force TTC below threshold.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Brake request presence or absence and inhibit flag.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-003 → RBT-ADAS-010 → execution report / regression suite entry.

#### RBT-ADAS-011 — AEB low-speed inhibit — Boundary test

- Requirement ID: ADAS-SYS-REQ-003
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: AEB low-speed inhibit.
- Preconditions: AEB enabled, target object present, driver inactive.
- Test stimulus: Ego speed = 4.9, 5.0, 5.1 km/h.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Brake request presence or absence and inhibit flag.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-003 → RBT-ADAS-011 → execution report / regression suite entry.

#### RBT-ADAS-012 — AEB low-speed inhibit — Robustness test

- Requirement ID: ADAS-SYS-REQ-003
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: AEB low-speed inhibit.
- Preconditions: AEB enabled, target object present, driver inactive.
- Test stimulus: Inject noisy wheel speed around threshold or missing speed signal.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Brake request presence or absence and inhibit flag.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-003 → RBT-ADAS-012 → execution report / regression suite entry.

#### RBT-ADAS-013 — ACC stop-and-go resume — Positive test

- Requirement ID: ADAS-SYS-REQ-004
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: ACC stop-and-go resume.
- Preconditions: ACC active in stop-and-go, lead vehicle stopped ahead, hold condition false.
- Test stimulus: Move lead vehicle after standstill.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to resume command and requested acceleration.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-004 → RBT-ADAS-013 → execution report / regression suite entry.

#### RBT-ADAS-014 — ACC stop-and-go resume — Negative test

- Requirement ID: ADAS-SYS-REQ-004
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: ACC stop-and-go resume.
- Preconditions: ACC active in stop-and-go, lead vehicle stopped ahead, hold condition false.
- Test stimulus: Driver door open or seatbelt unbuckled inhibit active.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to resume command and requested acceleration.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-004 → RBT-ADAS-014 → execution report / regression suite entry.

#### RBT-ADAS-015 — ACC stop-and-go resume — Boundary test

- Requirement ID: ADAS-SYS-REQ-004
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: ACC stop-and-go resume.
- Preconditions: ACC active in stop-and-go, lead vehicle stopped ahead, hold condition false.
- Test stimulus: Lead vehicle movement just below and above resume trigger distance/speed.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to resume command and requested acceleration.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-004 → RBT-ADAS-015 → execution report / regression suite entry.

#### RBT-ADAS-016 — ACC stop-and-go resume — Robustness test

- Requirement ID: ADAS-SYS-REQ-004
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: ACC stop-and-go resume.
- Preconditions: ACC active in stop-and-go, lead vehicle stopped ahead, hold condition false.
- Test stimulus: Interrupt radar track for 200 ms during resume or delay drivetrain acceptance.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to resume command and requested acceleration.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-004 → RBT-ADAS-016 → execution report / regression suite entry.

#### RBT-ADAS-017 — LKA assist speed window — Positive test

- Requirement ID: ADAS-SYS-REQ-005
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: LKA assist speed window.
- Preconditions: Valid lane model, hands-on true, no EPS fault.
- Test stimulus: Sweep vehicle speed across operational window.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Torque request enable state and requested torque.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-005 → RBT-ADAS-017 → execution report / regression suite entry.

#### RBT-ADAS-018 — LKA assist speed window — Negative test

- Requirement ID: ADAS-SYS-REQ-005
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: LKA assist speed window.
- Preconditions: Valid lane model, hands-on true, no EPS fault.
- Test stimulus: Hands-on false or lane model invalid while within speed window.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Torque request enable state and requested torque.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-005 → RBT-ADAS-018 → execution report / regression suite entry.

#### RBT-ADAS-019 — LKA assist speed window — Boundary test

- Requirement ID: ADAS-SYS-REQ-005
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: LKA assist speed window.
- Preconditions: Valid lane model, hands-on true, no EPS fault.
- Test stimulus: Speeds = 59, 60, 130, 131 km/h.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Torque request enable state and requested torque.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-005 → RBT-ADAS-019 → execution report / regression suite entry.

#### RBT-ADAS-020 — LKA assist speed window — Robustness test

- Requirement ID: ADAS-SYS-REQ-005
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: LKA assist speed window.
- Preconditions: Valid lane model, hands-on true, no EPS fault.
- Test stimulus: Inject camera frame timeout or invalid lane confidence.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Torque request enable state and requested torque.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-005 → RBT-ADAS-020 → execution report / regression suite entry.

#### RBT-ADAS-021 — Blind spot warning — Positive test

- Requirement ID: ADAS-SYS-REQ-006
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Blind spot warning.
- Preconditions: Adjacent lane target enters blind spot zone, indicators off.
- Test stimulus: Maintain target in blind spot zone for more than 200 ms.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Warning lamp activation time and zone occupancy status.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-006 → RBT-ADAS-021 → execution report / regression suite entry.

#### RBT-ADAS-022 — Blind spot warning — Negative test

- Requirement ID: ADAS-SYS-REQ-006
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Blind spot warning.
- Preconditions: Adjacent lane target enters blind spot zone, indicators off.
- Test stimulus: Target present for less than 200 ms only.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Warning lamp activation time and zone occupancy status.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-006 → RBT-ADAS-022 → execution report / regression suite entry.

#### RBT-ADAS-023 — Blind spot warning — Boundary test

- Requirement ID: ADAS-SYS-REQ-006
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Blind spot warning.
- Preconditions: Adjacent lane target enters blind spot zone, indicators off.
- Test stimulus: Occupancy duration = 199, 200, 201 ms.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Warning lamp activation time and zone occupancy status.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-006 → RBT-ADAS-023 → execution report / regression suite entry.

#### RBT-ADAS-024 — Blind spot warning — Robustness test

- Requirement ID: ADAS-SYS-REQ-006
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Blind spot warning.
- Preconditions: Adjacent lane target enters blind spot zone, indicators off.
- Test stimulus: Inject intermittent target tracking loss or invalid lane assignment.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Warning lamp activation time and zone occupancy status.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-006 → RBT-ADAS-024 → execution report / regression suite entry.

#### RBT-ADAS-025 — Rear cross traffic alert — Positive test

- Requirement ID: ADAS-SYS-REQ-007
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Rear cross traffic alert.
- Preconditions: Reverse gear active, rear sensors valid, lateral target approaching.
- Test stimulus: Replay cross-traffic target with closing speed above threshold.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Alert request timing and classification state.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-007 → RBT-ADAS-025 → execution report / regression suite entry.

#### RBT-ADAS-026 — Rear cross traffic alert — Negative test

- Requirement ID: ADAS-SYS-REQ-007
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Rear cross traffic alert.
- Preconditions: Reverse gear active, rear sensors valid, lateral target approaching.
- Test stimulus: Reverse gear inactive with same target motion.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Alert request timing and classification state.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-007 → RBT-ADAS-026 → execution report / regression suite entry.

#### RBT-ADAS-027 — Rear cross traffic alert — Boundary test

- Requirement ID: ADAS-SYS-REQ-007
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Rear cross traffic alert.
- Preconditions: Reverse gear active, rear sensors valid, lateral target approaching.
- Test stimulus: Closing speed just below/at/above threshold.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Alert request timing and classification state.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-007 → RBT-ADAS-027 → execution report / regression suite entry.

#### RBT-ADAS-028 — Rear cross traffic alert — Robustness test

- Requirement ID: ADAS-SYS-REQ-007
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Rear cross traffic alert.
- Preconditions: Reverse gear active, rear sensors valid, lateral target approaching.
- Test stimulus: Inject rear radar timeout or spurious static object reflections.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Alert request timing and classification state.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-007 → RBT-ADAS-028 → execution report / regression suite entry.

#### RBT-ADAS-029 — Parking obstacle stop — Positive test

- Requirement ID: ADAS-SYS-REQ-008
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Parking obstacle stop.
- Preconditions: Automated parking maneuver active, obstacle sensor chain healthy.
- Test stimulus: Decrease obstacle distance to 0.50 m or less.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Stop request timing, final speed, distance estimate.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-008 → RBT-ADAS-029 → execution report / regression suite entry.

#### RBT-ADAS-030 — Parking obstacle stop — Negative test

- Requirement ID: ADAS-SYS-REQ-008
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Parking obstacle stop.
- Preconditions: Automated parking maneuver active, obstacle sensor chain healthy.
- Test stimulus: Manual parking mode active instead of automated mode.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Stop request timing, final speed, distance estimate.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-008 → RBT-ADAS-030 → execution report / regression suite entry.

#### RBT-ADAS-031 — Parking obstacle stop — Boundary test

- Requirement ID: ADAS-SYS-REQ-008
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Parking obstacle stop.
- Preconditions: Automated parking maneuver active, obstacle sensor chain healthy.
- Test stimulus: Obstacle distance = 0.51, 0.50, 0.49 m.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Stop request timing, final speed, distance estimate.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-008 → RBT-ADAS-031 → execution report / regression suite entry.

#### RBT-ADAS-032 — Parking obstacle stop — Robustness test

- Requirement ID: ADAS-SYS-REQ-008
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Parking obstacle stop.
- Preconditions: Automated parking maneuver active, obstacle sensor chain healthy.
- Test stimulus: Inject ultrasonic sensor dropout on one corner or conflicting sensor readings.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Stop request timing, final speed, distance estimate.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-008 → RBT-ADAS-032 → execution report / regression suite entry.

#### RBT-ADAS-033 — Sensor degraded mode — Positive test

- Requirement ID: ADAS-SYS-REQ-009
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Sensor degraded mode.
- Preconditions: ADAS functions active, front camera delivering valid frames.
- Test stimulus: Stop front camera frames for more than 100 ms.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Degraded mode flag, function inhibition timing, driver warning.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-009 → RBT-ADAS-033 → execution report / regression suite entry.

#### RBT-ADAS-034 — Sensor degraded mode — Negative test

- Requirement ID: ADAS-SYS-REQ-009
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Sensor degraded mode.
- Preconditions: ADAS functions active, front camera delivering valid frames.
- Test stimulus: Frame gap shorter than declared timeout.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Degraded mode flag, function inhibition timing, driver warning.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-009 → RBT-ADAS-034 → execution report / regression suite entry.

#### RBT-ADAS-035 — Sensor degraded mode — Boundary test

- Requirement ID: ADAS-SYS-REQ-009
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Sensor degraded mode.
- Preconditions: ADAS functions active, front camera delivering valid frames.
- Test stimulus: Gap = 99, 100, 101 ms.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Degraded mode flag, function inhibition timing, driver warning.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-009 → RBT-ADAS-035 → execution report / regression suite entry.

#### RBT-ADAS-036 — Sensor degraded mode — Robustness test

- Requirement ID: ADAS-SYS-REQ-009
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Sensor degraded mode.
- Preconditions: ADAS functions active, front camera delivering valid frames.
- Test stimulus: Alternate valid/invalid frames or corrupt frame counters.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Degraded mode flag, function inhibition timing, driver warning.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-009 → RBT-ADAS-036 → execution report / regression suite entry.

#### RBT-ADAS-037 — Hands-on monitoring — Positive test

- Requirement ID: ADAS-SYS-REQ-010
- Domain: ADAS
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Hands-on monitoring.
- Preconditions: LKA active, steering torque assist active, hands-on initially true.
- Test stimulus: Force hands-off state and maintain it for 1.5 s.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Timer progression and torque ramp-out completion time.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-010 → RBT-ADAS-037 → execution report / regression suite entry.

#### RBT-ADAS-038 — Hands-on monitoring — Negative test

- Requirement ID: ADAS-SYS-REQ-010
- Domain: ADAS
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Hands-on monitoring.
- Preconditions: LKA active, steering torque assist active, hands-on initially true.
- Test stimulus: Hands-off duration shorter than required persistence.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Timer progression and torque ramp-out completion time.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-010 → RBT-ADAS-038 → execution report / regression suite entry.

#### RBT-ADAS-039 — Hands-on monitoring — Boundary test

- Requirement ID: ADAS-SYS-REQ-010
- Domain: ADAS
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Hands-on monitoring.
- Preconditions: LKA active, steering torque assist active, hands-on initially true.
- Test stimulus: Hands-off duration = 1.49, 1.50, 1.51 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Timer progression and torque ramp-out completion time.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-010 → RBT-ADAS-039 → execution report / regression suite entry.

#### RBT-ADAS-040 — Hands-on monitoring — Robustness test

- Requirement ID: ADAS-SYS-REQ-010
- Domain: ADAS
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Hands-on monitoring.
- Preconditions: LKA active, steering torque assist active, hands-on initially true.
- Test stimulus: Inject intermittent hands-on glitches or steering sensor invalidity.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Timer progression and torque ramp-out completion time.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: ADAS-SYS-REQ-010 → RBT-ADAS-040 → execution report / regression suite entry.

#### RBT-TCU-001 — eCall initiation — Positive test

- Requirement ID: TCU-SYS-REQ-001
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: eCall initiation.
- Preconditions: Crash detection source available, SIM provisioned, cellular network present.
- Test stimulus: Inject confirmed crash trigger.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to emergency call session start and payload transmission state.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-001 → RBT-TCU-001 → execution report / regression suite entry.

#### RBT-TCU-002 — eCall initiation — Negative test

- Requirement ID: TCU-SYS-REQ-001
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: eCall initiation.
- Preconditions: Crash detection source available, SIM provisioned, cellular network present.
- Test stimulus: No confirmed crash; only pre-crash warning available.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to emergency call session start and payload transmission state.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-001 → RBT-TCU-002 → execution report / regression suite entry.

#### RBT-TCU-003 — eCall initiation — Boundary test

- Requirement ID: TCU-SYS-REQ-001
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: eCall initiation.
- Preconditions: Crash detection source available, SIM provisioned, cellular network present.
- Test stimulus: Crash confirmation debounce at exact threshold timing.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to emergency call session start and payload transmission state.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-001 → RBT-TCU-003 → execution report / regression suite entry.

#### RBT-TCU-004 — eCall initiation — Robustness test

- Requirement ID: TCU-SYS-REQ-001
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: eCall initiation.
- Preconditions: Crash detection source available, SIM provisioned, cellular network present.
- Test stimulus: Drop network during session setup or invalidate GPS payload on first attempt.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to emergency call session start and payload transmission state.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-001 → RBT-TCU-004 → execution report / regression suite entry.

#### RBT-TCU-005 — GNSS reacquisition — Positive test

- Requirement ID: TCU-SYS-REQ-002
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: GNSS reacquisition.
- Preconditions: Vehicle exits tunnel, GNSS receiver previously lost fix.
- Test stimulus: Provide open-sky satellite visibility after tunnel exit.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to valid position and reported HDOP/confidence.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-002 → RBT-TCU-005 → execution report / regression suite entry.

#### RBT-TCU-006 — GNSS reacquisition — Negative test

- Requirement ID: TCU-SYS-REQ-002
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: GNSS reacquisition.
- Preconditions: Vehicle exits tunnel, GNSS receiver previously lost fix.
- Test stimulus: Remain under covered parking with no sky visibility.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to valid position and reported HDOP/confidence.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-002 → RBT-TCU-006 → execution report / regression suite entry.

#### RBT-TCU-007 — GNSS reacquisition — Boundary test

- Requirement ID: TCU-SYS-REQ-002
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: GNSS reacquisition.
- Preconditions: Vehicle exits tunnel, GNSS receiver previously lost fix.
- Test stimulus: Reacquisition at 29, 30, 31 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to valid position and reported HDOP/confidence.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-002 → RBT-TCU-007 → execution report / regression suite entry.

#### RBT-TCU-008 — GNSS reacquisition — Robustness test

- Requirement ID: TCU-SYS-REQ-002
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: GNSS reacquisition.
- Preconditions: Vehicle exits tunnel, GNSS receiver previously lost fix.
- Test stimulus: Inject intermittent satellite visibility or stale ephemeris.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to valid position and reported HDOP/confidence.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-002 → RBT-TCU-008 → execution report / regression suite entry.

#### RBT-TCU-009 — OTA resume download — Positive test

- Requirement ID: TCU-SYS-REQ-003
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: OTA resume download.
- Preconditions: OTA campaign active, package partially downloaded and verified up to last chunk.
- Test stimulus: Restore network after interruption.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to resume, resumed byte offset, integrity status.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-003 → RBT-TCU-009 → execution report / regression suite entry.

#### RBT-TCU-010 — OTA resume download — Negative test

- Requirement ID: TCU-SYS-REQ-003
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: OTA resume download.
- Preconditions: OTA campaign active, package partially downloaded and verified up to last chunk.
- Test stimulus: Package signature invalid before resume.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to resume, resumed byte offset, integrity status.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-003 → RBT-TCU-010 → execution report / regression suite entry.

#### RBT-TCU-011 — OTA resume download — Boundary test

- Requirement ID: TCU-SYS-REQ-003
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: OTA resume download.
- Preconditions: OTA campaign active, package partially downloaded and verified up to last chunk.
- Test stimulus: Interruption near chunk boundary and exactly at chunk boundary.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to resume, resumed byte offset, integrity status.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-003 → RBT-TCU-011 → execution report / regression suite entry.

#### RBT-TCU-012 — OTA resume download — Robustness test

- Requirement ID: TCU-SYS-REQ-003
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: OTA resume download.
- Preconditions: OTA campaign active, package partially downloaded and verified up to last chunk.
- Test stimulus: Inject packet loss, server 503, or CRC mismatch on resumed chunk.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to resume, resumed byte offset, integrity status.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-003 → RBT-TCU-012 → execution report / regression suite entry.

#### RBT-TCU-013 — Network bearer fallback — Positive test

- Requirement ID: TCU-SYS-REQ-004
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Network bearer fallback.
- Preconditions: Telematics data session active over 5G/LTE.
- Test stimulus: Force current radio bearer loss while alternative bearer is available.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to fallback and session continuity status.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-004 → RBT-TCU-013 → execution report / regression suite entry.

#### RBT-TCU-014 — Network bearer fallback — Negative test

- Requirement ID: TCU-SYS-REQ-004
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Network bearer fallback.
- Preconditions: Telematics data session active over 5G/LTE.
- Test stimulus: All bearers unavailable.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to fallback and session continuity status.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-004 → RBT-TCU-014 → execution report / regression suite entry.

#### RBT-TCU-015 — Network bearer fallback — Boundary test

- Requirement ID: TCU-SYS-REQ-004
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Network bearer fallback.
- Preconditions: Telematics data session active over 5G/LTE.
- Test stimulus: Fallback completion at 9.9, 10.0, 10.1 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to fallback and session continuity status.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-004 → RBT-TCU-015 → execution report / regression suite entry.

#### RBT-TCU-016 — Network bearer fallback — Robustness test

- Requirement ID: TCU-SYS-REQ-004
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Network bearer fallback.
- Preconditions: Telematics data session active over 5G/LTE.
- Test stimulus: Oscillate radio availability to test hysteresis and flap suppression.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to fallback and session continuity status.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-004 → RBT-TCU-016 → execution report / regression suite entry.

#### RBT-TCU-017 — Remote unlock security — Positive test

- Requirement ID: TCU-SYS-REQ-005
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Remote unlock security.
- Preconditions: Vehicle locked, backend command path active, vehicle stationary.
- Test stimulus: Send remote unlock command with valid credentials.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Authorization result, door unlock action, audit log.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-005 → RBT-TCU-017 → execution report / regression suite entry.

#### RBT-TCU-018 — Remote unlock security — Negative test

- Requirement ID: TCU-SYS-REQ-005
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Remote unlock security.
- Preconditions: Vehicle locked, backend command path active, vehicle stationary.
- Test stimulus: Replay old freshness token or invalid signature.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Authorization result, door unlock action, audit log.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-005 → RBT-TCU-018 → execution report / regression suite entry.

#### RBT-TCU-019 — Remote unlock security — Boundary test

- Requirement ID: TCU-SYS-REQ-005
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Remote unlock security.
- Preconditions: Vehicle locked, backend command path active, vehicle stationary.
- Test stimulus: Freshness token near expiry threshold.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Authorization result, door unlock action, audit log.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-005 → RBT-TCU-019 → execution report / regression suite entry.

#### RBT-TCU-020 — Remote unlock security — Robustness test

- Requirement ID: TCU-SYS-REQ-005
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Remote unlock security.
- Preconditions: Vehicle locked, backend command path active, vehicle stationary.
- Test stimulus: Inject delayed signed packets, duplicate commands, or backend timestamp skew.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Authorization result, door unlock action, audit log.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-005 → RBT-TCU-020 → execution report / regression suite entry.

#### RBT-TCU-021 — Periodic status upload — Positive test

- Requirement ID: TCU-SYS-REQ-006
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Periodic status upload.
- Preconditions: Ignition = RUN, backend session active, signal source values valid.
- Test stimulus: Maintain RUN state for several upload periods.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Upload period, payload completeness, backend acknowledgment.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-006 → RBT-TCU-021 → execution report / regression suite entry.

#### RBT-TCU-022 — Periodic status upload — Negative test

- Requirement ID: TCU-SYS-REQ-006
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Periodic status upload.
- Preconditions: Ignition = RUN, backend session active, signal source values valid.
- Test stimulus: Ignition switched to OFF before next period.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Upload period, payload completeness, backend acknowledgment.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-006 → RBT-TCU-022 → execution report / regression suite entry.

#### RBT-TCU-023 — Periodic status upload — Boundary test

- Requirement ID: TCU-SYS-REQ-006
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Periodic status upload.
- Preconditions: Ignition = RUN, backend session active, signal source values valid.
- Test stimulus: Upload interval at 59, 60, 61 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Upload period, payload completeness, backend acknowledgment.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-006 → RBT-TCU-023 → execution report / regression suite entry.

#### RBT-TCU-024 — Periodic status upload — Robustness test

- Requirement ID: TCU-SYS-REQ-006
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Periodic status upload.
- Preconditions: Ignition = RUN, backend session active, signal source values valid.
- Test stimulus: Inject temporary backend timeout or missing vehicle signal field.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Upload period, payload completeness, backend acknowledgment.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-006 → RBT-TCU-024 → execution report / regression suite entry.

#### RBT-TCU-025 — DoIP readiness — Positive test

- Requirement ID: TCU-SYS-REQ-007
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: DoIP readiness.
- Preconditions: Ethernet cable/link connected, ignition entering SERVICE or RUN.
- Test stimulus: Establish link-up then send routing activation.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time until request accepted and session state created.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-007 → RBT-TCU-025 → execution report / regression suite entry.

#### RBT-TCU-026 — DoIP readiness — Negative test

- Requirement ID: TCU-SYS-REQ-007
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: DoIP readiness.
- Preconditions: Ethernet cable/link connected, ignition entering SERVICE or RUN.
- Test stimulus: Ignition = OFF or unsupported activation type.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time until request accepted and session state created.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-007 → RBT-TCU-026 → execution report / regression suite entry.

#### RBT-TCU-027 — DoIP readiness — Boundary test

- Requirement ID: TCU-SYS-REQ-007
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: DoIP readiness.
- Preconditions: Ethernet cable/link connected, ignition entering SERVICE or RUN.
- Test stimulus: Acceptance at 1.9, 2.0, 2.1 s after link-up.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time until request accepted and session state created.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-007 → RBT-TCU-027 → execution report / regression suite entry.

#### RBT-TCU-028 — DoIP readiness — Robustness test

- Requirement ID: TCU-SYS-REQ-007
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: DoIP readiness.
- Preconditions: Ethernet cable/link connected, ignition entering SERVICE or RUN.
- Test stimulus: Inject malformed DoIP payload or delayed DHCP/configuration.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time until request accepted and session state created.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-007 → RBT-TCU-028 → execution report / regression suite entry.

#### RBT-TCU-029 — Backup battery low warning — Positive test

- Requirement ID: TCU-SYS-REQ-008
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Backup battery low warning.
- Preconditions: Backup battery nominal at start, monitoring active.
- Test stimulus: Reduce measured backup battery voltage below threshold for 5 s.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Event reporting time and DTC state.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-008 → RBT-TCU-029 → execution report / regression suite entry.

#### RBT-TCU-030 — Backup battery low warning — Negative test

- Requirement ID: TCU-SYS-REQ-008
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Backup battery low warning.
- Preconditions: Backup battery nominal at start, monitoring active.
- Test stimulus: Voltage dip shorter than 5 s.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Event reporting time and DTC state.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-008 → RBT-TCU-030 → execution report / regression suite entry.

#### RBT-TCU-031 — Backup battery low warning — Boundary test

- Requirement ID: TCU-SYS-REQ-008
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Backup battery low warning.
- Preconditions: Backup battery nominal at start, monitoring active.
- Test stimulus: Duration = 4.9, 5.0, 5.1 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Event reporting time and DTC state.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-008 → RBT-TCU-031 → execution report / regression suite entry.

#### RBT-TCU-032 — Backup battery low warning — Robustness test

- Requirement ID: TCU-SYS-REQ-008
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Backup battery low warning.
- Preconditions: Backup battery nominal at start, monitoring active.
- Test stimulus: Inject noisy ADC measurements around threshold.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Event reporting time and DTC state.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-008 → RBT-TCU-032 → execution report / regression suite entry.

#### RBT-TCU-033 — Roaming restriction — Positive test

- Requirement ID: TCU-SYS-REQ-009
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Roaming restriction.
- Preconditions: Vehicle enters roaming network, roaming-disabled config active.
- Test stimulus: Attempt non-emergency backend data session.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Session block result and exception handling.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-009 → RBT-TCU-033 → execution report / regression suite entry.

#### RBT-TCU-034 — Roaming restriction — Negative test

- Requirement ID: TCU-SYS-REQ-009
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Roaming restriction.
- Preconditions: Vehicle enters roaming network, roaming-disabled config active.
- Test stimulus: Emergency regulatory service request under same config.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Session block result and exception handling.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-009 → RBT-TCU-034 → execution report / regression suite entry.

#### RBT-TCU-035 — Roaming restriction — Boundary test

- Requirement ID: TCU-SYS-REQ-009
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Roaming restriction.
- Preconditions: Vehicle enters roaming network, roaming-disabled config active.
- Test stimulus: Transition exactly when PLMN changes.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Session block result and exception handling.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-009 → RBT-TCU-035 → execution report / regression suite entry.

#### RBT-TCU-036 — Roaming restriction — Robustness test

- Requirement ID: TCU-SYS-REQ-009
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Roaming restriction.
- Preconditions: Vehicle enters roaming network, roaming-disabled config active.
- Test stimulus: Inject inconsistent roaming flags from modem and network stack.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Session block result and exception handling.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-009 → RBT-TCU-036 → execution report / regression suite entry.

#### RBT-TCU-037 — Secure remote command audit — Positive test

- Requirement ID: TCU-SYS-REQ-010
- Domain: TCU
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Secure remote command audit.
- Preconditions: Remote command channel enabled, secure storage available.
- Test stimulus: Send authenticated remote command accepted by vehicle.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to audit record persistence and log contents.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-010 → RBT-TCU-037 → execution report / regression suite entry.

#### RBT-TCU-038 — Secure remote command audit — Negative test

- Requirement ID: TCU-SYS-REQ-010
- Domain: TCU
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Secure remote command audit.
- Preconditions: Remote command channel enabled, secure storage available.
- Test stimulus: Rejected command should not be logged as accepted.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to audit record persistence and log contents.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-010 → RBT-TCU-038 → execution report / regression suite entry.

#### RBT-TCU-039 — Secure remote command audit — Boundary test

- Requirement ID: TCU-SYS-REQ-010
- Domain: TCU
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Secure remote command audit.
- Preconditions: Remote command channel enabled, secure storage available.
- Test stimulus: Storage nearly full during command acceptance.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to audit record persistence and log contents.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-010 → RBT-TCU-039 → execution report / regression suite entry.

#### RBT-TCU-040 — Secure remote command audit — Robustness test

- Requirement ID: TCU-SYS-REQ-010
- Domain: TCU
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Secure remote command audit.
- Preconditions: Remote command channel enabled, secure storage available.
- Test stimulus: Inject storage write delay or reset immediately after command acceptance.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to audit record persistence and log contents.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: TCU-SYS-REQ-010 → RBT-TCU-040 → execution report / regression suite entry.

#### RBT-CLU-001 — Speed display accuracy — Positive test

- Requirement ID: CLU-SYS-REQ-001
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Speed display accuracy.
- Preconditions: Cluster normal mode active, validated vehicle speed input available.
- Test stimulus: Sweep vehicle speed through operating range using simulator or vehicle.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Displayed speed versus reference speed.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-001 → RBT-CLU-001 → execution report / regression suite entry.

#### RBT-CLU-002 — Speed display accuracy — Negative test

- Requirement ID: CLU-SYS-REQ-001
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Speed display accuracy.
- Preconditions: Cluster normal mode active, validated vehicle speed input available.
- Test stimulus: Input validity false.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Displayed speed versus reference speed.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-001 → RBT-CLU-002 → execution report / regression suite entry.

#### RBT-CLU-003 — Speed display accuracy — Boundary test

- Requirement ID: CLU-SYS-REQ-001
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Speed display accuracy.
- Preconditions: Cluster normal mode active, validated vehicle speed input available.
- Test stimulus: Speeds = 19.9, 20.0, 180.0, 180.1 km/h where applicable.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Displayed speed versus reference speed.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-001 → RBT-CLU-003 → execution report / regression suite entry.

#### RBT-CLU-004 — Speed display accuracy — Robustness test

- Requirement ID: CLU-SYS-REQ-001
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Speed display accuracy.
- Preconditions: Cluster normal mode active, validated vehicle speed input available.
- Test stimulus: Inject scaling mismatch or stale speed input.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Displayed speed versus reference speed.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-001 → RBT-CLU-004 → execution report / regression suite entry.

#### RBT-CLU-005 — Seatbelt telltale timing — Positive test

- Requirement ID: CLU-SYS-REQ-002
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Seatbelt telltale timing.
- Preconditions: Ignition = RUN, seatbelt initially buckled, cluster healthy.
- Test stimulus: Change seatbelt status to Unbuckled.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to telltale illumination and any chime trigger.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-002 → RBT-CLU-005 → execution report / regression suite entry.

#### RBT-CLU-006 — Seatbelt telltale timing — Negative test

- Requirement ID: CLU-SYS-REQ-002
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Seatbelt telltale timing.
- Preconditions: Ignition = RUN, seatbelt initially buckled, cluster healthy.
- Test stimulus: Ignition = OFF while status changes.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to telltale illumination and any chime trigger.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-002 → RBT-CLU-006 → execution report / regression suite entry.

#### RBT-CLU-007 — Seatbelt telltale timing — Boundary test

- Requirement ID: CLU-SYS-REQ-002
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Seatbelt telltale timing.
- Preconditions: Ignition = RUN, seatbelt initially buckled, cluster healthy.
- Test stimulus: Response at 199, 200, 201 ms.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to telltale illumination and any chime trigger.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-002 → RBT-CLU-007 → execution report / regression suite entry.

#### RBT-CLU-008 — Seatbelt telltale timing — Robustness test

- Requirement ID: CLU-SYS-REQ-002
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Seatbelt telltale timing.
- Preconditions: Ignition = RUN, seatbelt initially buckled, cluster healthy.
- Test stimulus: Inject invalid seatbelt signal or timeout.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to telltale illumination and any chime trigger.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-002 → RBT-CLU-008 → execution report / regression suite entry.

#### RBT-CLU-009 — Low fuel warning threshold — Positive test

- Requirement ID: CLU-SYS-REQ-003
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Low fuel warning threshold.
- Preconditions: Fuel level source valid, cluster normal mode active.
- Test stimulus: Ramp filtered fuel level downward then upward.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Warning set/clear points and hysteresis.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-003 → RBT-CLU-009 → execution report / regression suite entry.

#### RBT-CLU-010 — Low fuel warning threshold — Negative test

- Requirement ID: CLU-SYS-REQ-003
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Low fuel warning threshold.
- Preconditions: Fuel level source valid, cluster normal mode active.
- Test stimulus: Fuel sensor invalidity active.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Warning set/clear points and hysteresis.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-003 → RBT-CLU-010 → execution report / regression suite entry.

#### RBT-CLU-011 — Low fuel warning threshold — Boundary test

- Requirement ID: CLU-SYS-REQ-003
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Low fuel warning threshold.
- Preconditions: Fuel level source valid, cluster normal mode active.
- Test stimulus: Fuel level = 9.9, 10.0, 10.1, 11.9, 12.0, 12.1 L.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Warning set/clear points and hysteresis.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-003 → RBT-CLU-011 → execution report / regression suite entry.

#### RBT-CLU-012 — Low fuel warning threshold — Robustness test

- Requirement ID: CLU-SYS-REQ-003
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Low fuel warning threshold.
- Preconditions: Fuel level source valid, cluster normal mode active.
- Test stimulus: Inject noisy fuel level around threshold or lost CAN updates.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Warning set/clear points and hysteresis.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-003 → RBT-CLU-012 → execution report / regression suite entry.

#### RBT-CLU-013 — Warning priority arbitration — Positive test

- Requirement ID: CLU-SYS-REQ-004
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Warning priority arbitration.
- Preconditions: Multiple warning sources available to cluster.
- Test stimulus: Activate warnings of different priorities simultaneously.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Displayed order, coexistence, and mandatory telltale persistence.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-004 → RBT-CLU-013 → execution report / regression suite entry.

#### RBT-CLU-014 — Warning priority arbitration — Negative test

- Requirement ID: CLU-SYS-REQ-004
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Warning priority arbitration.
- Preconditions: Multiple warning sources available to cluster.
- Test stimulus: Lower-priority warning should not mask mandatory safety telltale.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Displayed order, coexistence, and mandatory telltale persistence.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-004 → RBT-CLU-014 → execution report / regression suite entry.

#### RBT-CLU-015 — Warning priority arbitration — Boundary test

- Requirement ID: CLU-SYS-REQ-004
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Warning priority arbitration.
- Preconditions: Multiple warning sources available to cluster.
- Test stimulus: Simultaneous activation within same render cycle.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Displayed order, coexistence, and mandatory telltale persistence.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-004 → RBT-CLU-015 → execution report / regression suite entry.

#### RBT-CLU-016 — Warning priority arbitration — Robustness test

- Requirement ID: CLU-SYS-REQ-004
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Warning priority arbitration.
- Preconditions: Multiple warning sources available to cluster.
- Test stimulus: Inject rapid warning churn or conflicting source states.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Displayed order, coexistence, and mandatory telltale persistence.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-004 → RBT-CLU-016 → execution report / regression suite entry.

#### RBT-CLU-017 — Boot readiness — Positive test

- Requirement ID: CLU-SYS-REQ-005
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Boot readiness.
- Preconditions: KL15 off, cluster fully powered down.
- Test stimulus: Switch KL15 to ON.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to normal operation display state and animation end.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-005 → RBT-CLU-017 → execution report / regression suite entry.

#### RBT-CLU-018 — Boot readiness — Negative test

- Requirement ID: CLU-SYS-REQ-005
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Boot readiness.
- Preconditions: KL15 off, cluster fully powered down.
- Test stimulus: Voltage brownout during boot.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to normal operation display state and animation end.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-005 → RBT-CLU-018 → execution report / regression suite entry.

#### RBT-CLU-019 — Boot readiness — Boundary test

- Requirement ID: CLU-SYS-REQ-005
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Boot readiness.
- Preconditions: KL15 off, cluster fully powered down.
- Test stimulus: Boot time at 1.9, 2.0, 2.1 s.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to normal operation display state and animation end.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-005 → RBT-CLU-019 → execution report / regression suite entry.

#### RBT-CLU-020 — Boot readiness — Robustness test

- Requirement ID: CLU-SYS-REQ-005
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Boot readiness.
- Preconditions: KL15 off, cluster fully powered down.
- Test stimulus: Inject delayed CAN wake messages or graphics service restart.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to normal operation display state and animation end.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-005 → RBT-CLU-020 → execution report / regression suite entry.

#### RBT-CLU-021 — Auto dimming — Positive test

- Requirement ID: CLU-SYS-REQ-006
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Auto dimming.
- Preconditions: Auto-brightness mode active, ambient light sensor valid.
- Test stimulus: Change ambient light class from day to tunnel/night and back.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to new brightness target and final level.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-006 → RBT-CLU-021 → execution report / regression suite entry.

#### RBT-CLU-022 — Auto dimming — Negative test

- Requirement ID: CLU-SYS-REQ-006
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Auto dimming.
- Preconditions: Auto-brightness mode active, ambient light sensor valid.
- Test stimulus: Manual brightness mode selected.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to new brightness target and final level.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-006 → RBT-CLU-022 → execution report / regression suite entry.

#### RBT-CLU-023 — Auto dimming — Boundary test

- Requirement ID: CLU-SYS-REQ-006
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Auto dimming.
- Preconditions: Auto-brightness mode active, ambient light sensor valid.
- Test stimulus: Class transition exactly at lux threshold.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to new brightness target and final level.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-006 → RBT-CLU-023 → execution report / regression suite entry.

#### RBT-CLU-024 — Auto dimming — Robustness test

- Requirement ID: CLU-SYS-REQ-006
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Auto dimming.
- Preconditions: Auto-brightness mode active, ambient light sensor valid.
- Test stimulus: Inject stuck ambient light value or sensor timeout.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to new brightness target and final level.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-006 → RBT-CLU-024 → execution report / regression suite entry.

#### RBT-CLU-025 — Gear position fallback — Positive test

- Requirement ID: CLU-SYS-REQ-007
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Gear position fallback.
- Preconditions: Gear position displayed normally, transmission signal valid.
- Test stimulus: Invalidate or timeout gear position signal.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Time to fallback display “--”.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-007 → RBT-CLU-025 → execution report / regression suite entry.

#### RBT-CLU-026 — Gear position fallback — Negative test

- Requirement ID: CLU-SYS-REQ-007
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Gear position fallback.
- Preconditions: Gear position displayed normally, transmission signal valid.
- Test stimulus: Brief invalid pulse shorter than debounce rule.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Time to fallback display “--”.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-007 → RBT-CLU-026 → execution report / regression suite entry.

#### RBT-CLU-027 — Gear position fallback — Boundary test

- Requirement ID: CLU-SYS-REQ-007
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Gear position fallback.
- Preconditions: Gear position displayed normally, transmission signal valid.
- Test stimulus: Timeout = 299, 300, 301 ms.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Time to fallback display “--”.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-007 → RBT-CLU-027 → execution report / regression suite entry.

#### RBT-CLU-028 — Gear position fallback — Robustness test

- Requirement ID: CLU-SYS-REQ-007
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Gear position fallback.
- Preconditions: Gear position displayed normally, transmission signal valid.
- Test stimulus: Inject alternating valid/invalid gear values.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Time to fallback display “--”.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-007 → RBT-CLU-028 → execution report / regression suite entry.

#### RBT-CLU-029 — Odometer retention — Positive test

- Requirement ID: CLU-SYS-REQ-008
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Odometer retention.
- Preconditions: Known odometer value stored, cluster in normal operation.
- Test stimulus: Perform ignition cycle or reset sequence.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Value before and after reset, persistence delay.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-008 → RBT-CLU-029 → execution report / regression suite entry.

#### RBT-CLU-030 — Odometer retention — Negative test

- Requirement ID: CLU-SYS-REQ-008
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Odometer retention.
- Preconditions: Known odometer value stored, cluster in normal operation.
- Test stimulus: Power removed before commit precondition satisfied if defined.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Value before and after reset, persistence delay.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-008 → RBT-CLU-030 → execution report / regression suite entry.

#### RBT-CLU-031 — Odometer retention — Boundary test

- Requirement ID: CLU-SYS-REQ-008
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Odometer retention.
- Preconditions: Known odometer value stored, cluster in normal operation.
- Test stimulus: Reset just before and just after periodic NVM save point.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Value before and after reset, persistence delay.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-008 → RBT-CLU-031 → execution report / regression suite entry.

#### RBT-CLU-032 — Odometer retention — Robustness test

- Requirement ID: CLU-SYS-REQ-008
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Odometer retention.
- Preconditions: Known odometer value stored, cluster in normal operation.
- Test stimulus: Inject NVM write failure or unexpected reset during commit.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Value before and after reset, persistence delay.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-008 → RBT-CLU-032 → execution report / regression suite entry.

#### RBT-CLU-033 — Turn indicator synchronization — Positive test

- Requirement ID: CLU-SYS-REQ-009
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Turn indicator synchronization.
- Preconditions: Body controller command available, cluster active.
- Test stimulus: Activate left or right turn signal command.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Telltale flash frequency and phase relation.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-009 → RBT-CLU-033 → execution report / regression suite entry.

#### RBT-CLU-034 — Turn indicator synchronization — Negative test

- Requirement ID: CLU-SYS-REQ-009
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Turn indicator synchronization.
- Preconditions: Body controller command available, cluster active.
- Test stimulus: No command active.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Telltale flash frequency and phase relation.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-009 → RBT-CLU-034 → execution report / regression suite entry.

#### RBT-CLU-035 — Turn indicator synchronization — Boundary test

- Requirement ID: CLU-SYS-REQ-009
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Turn indicator synchronization.
- Preconditions: Body controller command available, cluster active.
- Test stimulus: Frequency at 1.4, 1.5, 1.6 Hz.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Telltale flash frequency and phase relation.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-009 → RBT-CLU-035 → execution report / regression suite entry.

#### RBT-CLU-036 — Turn indicator synchronization — Robustness test

- Requirement ID: CLU-SYS-REQ-009
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Turn indicator synchronization.
- Preconditions: Body controller command available, cluster active.
- Test stimulus: Inject missing command cycles or BCM timing jitter.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Telltale flash frequency and phase relation.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-009 → RBT-CLU-036 → execution report / regression suite entry.

#### RBT-CLU-037 — Seatbelt chime coordination — Positive test

- Requirement ID: CLU-SYS-REQ-010
- Domain: Cluster
- Test classification: positive functional
- Objective: Verify nominal behavior when all preconditions are satisfied. Requirement focus: Seatbelt chime coordination.
- Preconditions: Ignition = RUN, speed threshold behavior enabled, audio path healthy.
- Test stimulus: Create buckle/unbuckle and speed conditions that should trigger chime.
- Procedure outline: Apply valid triggering conditions exactly as required.
- Measurements / observations: Chime start, duration, repetition, and coordination with telltale.
- Expected result: The system shall perform the specified nominal behavior within the required limits.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-010 → RBT-CLU-037 → execution report / regression suite entry.

#### RBT-CLU-038 — Seatbelt chime coordination — Negative test

- Requirement ID: CLU-SYS-REQ-010
- Domain: Cluster
- Test classification: negative / inhibition
- Objective: Verify the behavior does not occur when an exclusion condition is present. Requirement focus: Seatbelt chime coordination.
- Preconditions: Ignition = RUN, speed threshold behavior enabled, audio path healthy.
- Test stimulus: Vehicle speed below activation threshold.
- Procedure outline: Apply near-nominal conditions while holding one exclusion or inhibit condition active.
- Measurements / observations: Chime start, duration, repetition, and coordination with telltale.
- Expected result: The system shall suppress or block the behavior exactly as required and shall not create unintended side effects.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-010 → RBT-CLU-038 → execution report / regression suite entry.

#### RBT-CLU-039 — Seatbelt chime coordination — Boundary test

- Requirement ID: CLU-SYS-REQ-010
- Domain: Cluster
- Test classification: boundary
- Objective: Verify threshold behavior at, below, and above the defined limits. Requirement focus: Seatbelt chime coordination.
- Preconditions: Ignition = RUN, speed threshold behavior enabled, audio path healthy.
- Test stimulus: Speed exactly at activation threshold and timeout cancellation point.
- Procedure outline: Sweep values around the relevant thresholds and capture transitions precisely.
- Measurements / observations: Chime start, duration, repetition, and coordination with telltale.
- Expected result: The system shall switch behavior only at the specified thresholds with correct hysteresis or inclusivity.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-010 → RBT-CLU-039 → execution report / regression suite entry.

#### RBT-CLU-040 — Seatbelt chime coordination — Robustness test

- Requirement ID: CLU-SYS-REQ-010
- Domain: Cluster
- Test classification: robustness / timing / fault injection
- Objective: Verify resilience under timing disturbance, invalid data, or transient faults. Requirement focus: Seatbelt chime coordination.
- Preconditions: Ignition = RUN, speed threshold behavior enabled, audio path healthy.
- Test stimulus: Inject audio amplifier unavailable or repeated buckle glitches.
- Procedure outline: Inject stale, invalid, delayed, intermittent, or corrupted stimuli while monitoring fault reaction.
- Measurements / observations: Chime start, duration, repetition, and coordination with telltale.
- Expected result: The system shall transition to the specified degraded, fault, or recovery behavior within the required time.
- Pass criteria: All measured values, states, and logs shall satisfy the linked requirement and any stated timing or fault-handling constraints.
- Evidence to collect: Time-stamped logs, bus traces, screenshots or HMI capture, diagnostic records, and final test verdict.
- Traceability: CLU-SYS-REQ-010 → RBT-CLU-040 → execution report / regression suite entry.

### 22.7 Coverage summary of the 120 examples

| Domain | Requirements covered | Tests per requirement | Total example tests |
|---|---|---|---|
| ADAS | 10 | 4 | 40 |
| TCU | 10 | 4 | 40 |
| Cluster | 10 | 4 | 40 |
| Total | 30 | 4 | 120 |

### 22.8 Final guidance for engineers

- Write requirements so that a test engineer can derive stimulus, expected result, and pass/fail criteria without guessing.
- Do not wait until test implementation to discover missing timing, boundaries, or failure behavior.
- Use bidirectional traceability so every requirement has verification evidence and every test has a reason to exist.
- Treat interface and timing requirements with the same rigor as functional behavior, because many vehicle defects arise there.
- Review and validate requirements early; the cheapest defect is the one removed before architecture and implementation begin.

