# Automotive Requirements Engineering Fundamentals and Writing Guide

> A detailed educational reference for automotive engineers working on ADAS, TCU, Cluster, Gateway, diagnostics, safety, and cybersecurity related projects.

---

## Table of Contents

1. [Requirements Engineering Fundamentals](#1-requirements-engineering-fundamentals)
2. [Requirements Engineering Lifecycle](#2-requirements-engineering-lifecycle)
3. [Requirements Elicitation](#3-requirements-elicitation)
4. [Requirement Classification](#4-requirement-classification)
5. [Good Requirement Characteristics](#5-good-requirement-characteristics)
6. [Requirement Writing](#6-requirement-writing)
7. [Requirement Patterns](#7-requirement-patterns)

---

# 1. REQUIREMENTS ENGINEERING FUNDAMENTALS

## 1.1 What is a requirement?

A **requirement** is a mandatory statement of needed behavior, quality, limit, interface, or condition that a product must satisfy.

In automotive engineering, a requirement describes what a vehicle function, ECU, software item, hardware element, or service must do so that engineers can design, implement, verify, validate, and maintain it.

A requirement should answer one or more of these questions:

- What shall the system do?
- Under what condition shall it do it?
- How fast, how often, how accurately, or how reliably shall it do it?
- What shall it never do?
- What information shall it send, receive, store, or display?
- What legal, safety, or security constraints shall it satisfy?

### Beginner examples

**ADAS**

> When time-to-collision falls below the warning threshold for a valid ego-lane target, the ADAS ECU shall request a forward collision warning.

**TCU**

> When the restraint control module reports a deployment-level crash event, the TCU shall initiate the emergency call procedure.

**Cluster**

> When the low fuel warning request is TRUE, the cluster shall activate the amber low fuel telltale.

---

## 1.2 Why requirements matter

Requirements matter because modern vehicles are distributed systems with many ECUs, sensors, actuators, buses, gateways, cloud services, and diagnostics paths.

A single customer-visible behavior often depends on many contributors.

### Example: ADAS warning path

A forward collision warning may involve:

- camera and radar sensing
- perception and fusion logic
- decision logic in the ADAS ECU
- gateway signal routing
- cluster warning presentation
- audio chime request
- diagnostics fault supervision
- safety mechanisms and fallback behavior

If the requirement is vague, each team makes different assumptions.

### Requirements are the alignment backbone

Requirements align:

- OEM and supplier expectations
- system, software, and hardware teams
- design and verification teams
- safety, security, service, and manufacturing stakeholders
- feature intent and vehicle-level validation

### Business and engineering impact

Good requirements reduce:

- rework
- ambiguity
- requirement churn
- integration defects
- late change cost
- escaped defects into vehicle test or field operation

---

## 1.3 Requirement versus related terms

| Term | Meaning | Example | Why it is different |
|---|---|---|---|
| Requirement | Mandatory obligation on the product | The gateway shall route OBD requests to the addressed subnet. | Defines what must be satisfied. |
| Specification | Structured collection of requirements and supporting context | Cluster software requirements specification | A specification contains many requirements. |
| Design | Chosen technical solution | Use a watchdog-serviced task every 20 ms. | Design explains how to satisfy a requirement. |
| Test case | Procedure to verify a requirement | Inject warning request and measure telltale latency. | Test proves requirement fulfillment. |
| Feature | Customer-visible capability | Lane departure warning | A feature decomposes into many requirements. |
| Constraint | Mandatory limitation or rule | The TCU shall use TLS 1.3 for backend communication. | Restricts implementation or operating conditions. |

### Requirement vs specification

A requirement is one controlled statement.
A specification is the organized container of many controlled statements.

### Requirement vs design

**Requirement**

> When brake failure warning request is TRUE, the cluster shall activate the red brake telltale within 100 ms.

**Design**

> The telltale logic shall be implemented in the `WarningManager` state machine with a dedicated high-priority render queue.

### Requirement vs test case

**Requirement**

> After a failed backend session establishment attempt, the TCU shall retry after 30 s ±2 s while ignition remains ON.

**Test case**

1. Force backend authentication failure.
2. Observe retry attempts for 90 s.
3. Confirm retries occur at 30 s ±2 s.

### Requirement vs feature

**Feature**: remote vehicle status in mobile application.

Possible requirements:

- The TCU shall transmit door lock state to the backend on change of state.
- The backend payload shall include VIN and timestamp.
- The TCU shall retry upload after network recovery.

### Requirement vs constraint

Examples of valid automotive constraints:

- The cluster shall comply with market-specific telltale color rules.
- The gateway shall not exceed 70% average CPU utilization in nominal routing mode.
- The TCU shall verify OTA package authenticity before installation.

---

## 1.4 Requirement types used in automotive programs

| Type | Meaning | Automotive example |
|---|---|---|
| Functional | What the system shall do. | The cluster shall display the gear position received from the transmission controller. |
| Non-functional | How well the system shall operate. | The ADAS ECU shall complete one fusion cycle within 40 ms. |
| System | Vehicle or feature-level obligations. | The eCall system shall establish an emergency call after crash detection. |
| Software | Obligations allocated to software items or components. | The TCU connectivity manager shall persist the last successful APN profile. |
| Hardware | Obligations allocated to electronics, sensors, or physical interfaces. | The radar sensor shall detect passenger vehicles up to 180 m under nominal conditions. |
| Safety | Risk-reduction behavior from HARA or safety concept. | The AEB function shall inhibit unintended brake requests when no valid collision-path target exists. |
| Security | Cybersecurity protections from TARA or cybersecurity concept. | The gateway shall reject unauthenticated extended diagnostic session requests. |
| Interface | Signals, protocols, units, timing, and ownership across boundaries. | The cluster shall decode `VehSpd` from CAN message `0x180` with scale 0.01 km/h per bit. |
| Performance | Latency, accuracy, throughput, load, memory, availability. | The TCU shall establish a TLS backend session within 5 s in nominal LTE coverage. |
| Diagnostic | Fault detection, DTCs, freeze frames, service behavior. | The gateway shall store a DTC when CAN channel 2 remains bus-off for longer than 100 ms. |
| Regulatory | Legal or homologation obligations. | The cluster telltales shall comply with applicable regulatory color and visibility requirements. |
| Environmental | Operating conditions and robustness limits. | The ECU shall operate over the specified automotive temperature range. |
| Manufacturing | Production programming, traceability, end-of-line support. | The cluster shall support a manufacturing bulb-test routine. |
| Service | Aftersales diagnosis, replacement, and field maintenance support. | The TCU shall support readout of modem firmware version via a diagnostic data identifier. |

## 1.5 Consequences of poor requirements

Poor requirements create real product risk.

### Incorrect implementation

If a requirement says “show the warning quickly”, one team may implement 100 ms and another 500 ms.

### Ambiguous behavior

If a requirement says “warn when collision is likely”, nobody knows whether the trigger is TTC, range-rate, driver intent, or a fused risk score.

### Safety failures

If AEB safety requirements do not clearly define invalid target handling, the system may brake unexpectedly or fail to brake when needed.

### Integration failures

If interface requirements do not define bus, message, scaling, timeout, and ownership, gateway and cluster teams may implement incompatible interpretations.

### Test gaps

If a requirement is not measurable, testers cannot produce a binary pass/fail verdict.

### Cost escalation

A defect found at requirement review is cheap.
A defect found during vehicle integration is expensive.
A defect found after SOP can lead to service campaigns or recalls.

### Requirement churn

Weak elicitation and poor wording cause repeated late clarification.
This destabilizes code, calibration, test, and safety evidence.

### Vehicle-level defects and recalls

Examples include:

- telltales not visible when they must be visible
- eCall not transmitting correct data after crash
- gateway routing stale warning data
- OTA update recovery behavior incomplete
- ADAS nuisance warnings causing customer dissatisfaction or safety concerns

---

## 1.6 ADAS, TCU, and Cluster context

### ADAS

Requirements usually cover:

- operational design domain
- target classes
- activation conditions
- warning and intervention timing
- safe fallback during sensor blockage or invalid input
- HMI interaction with cluster and chime systems

### TCU

Requirements usually cover:

- network registration and retry behavior
- eCall/bCall triggers
- backend communication and certificates
- sleep/wake and low-power behavior
- OTA security and recovery
- diagnostics and service observability

### Cluster

Requirements usually cover:

- telltale logic and priority rules
- startup and shutdown behavior
- signal decoding and substitution
- unit coding and market variants
- buzzer and popup interaction
- regulatory display obligations

---

## 1.7 Requirement thinking checklist

When reading or writing a requirement, ask:

1. Who needs this behavior?
2. What triggers it?
3. What exact response is required?
4. What timing, range, accuracy, or tolerance applies?
5. In which vehicle modes, states, and variants does it apply?
6. How will it be verified?
7. What happens when data is invalid, delayed, or missing?
8. Which higher-level source, hazard, or interface drives it?

---

# 2. REQUIREMENTS ENGINEERING LIFECYCLE

Requirements engineering is a controlled lifecycle rather than a one-time writing task.

```text
Stakeholder Need -> Elicitation -> Analysis -> Specification -> Review -> Baseline
-> Architecture -> Decomposition -> Implementation -> Verification -> Validation
-> Change Management -> Maintenance
```

## 2.1 Stakeholder Need

Define the business, user, safety, and regulatory problem to solve.

### Inputs

- market needs
- OEM feature intent
- regulatory and safety goals

### Activities

- capture user and business outcomes
- define scope and assumptions
- separate needs from proposed solutions

### Outputs

- need statements
- feature scope
- initial assumptions

### Roles

- product manager
- OEM feature owner
- systems engineer

### Work products

- feature concept note
- stakeholder need list

### Reviews

- scope review
- concept review

### Tools

- feature templates
- interview notes

### Common failures

- solution bias too early
- missing stakeholders
- unclear scope

### Metrics

- stakeholder coverage
- open assumptions count

### Automotive example

For LDW, the OEM need may state that the vehicle shall help the driver avoid unintentional lane departure on highways without excessive nuisance alerts.

---

## 2.2 Elicitation

Collect raw expectations, scenarios, constraints, and source material.

### Inputs

- stakeholder needs
- legacy specs
- vehicle and field data

### Activities

- interviews and workshops
- scenario capture
- collect source documents

### Outputs

- candidate requirements
- glossary
- issue list

### Roles

- requirements engineer
- domain experts
- customer representatives

### Work products

- workshop minutes
- source matrix

### Reviews

- elicitation playback
- source completeness review

### Tools

- DOORS candidate module
- use case templates

### Common failures

- only happy path captured
- service and manufacturing ignored
- vague terms left unexplored

### Metrics

- source coverage
- scenario coverage

### Automotive example

A TCU workshop may reveal the hidden need to store the last valid GNSS position if live position is unavailable during eCall.

---

## 2.3 Analysis

Interpret collected information and remove conflicts and ambiguity.

### Inputs

- candidate requirements
- source documents
- interface and safety inputs

### Activities

- classify requirements
- resolve conflicts
- identify derived needs

### Outputs

- analyzed requirements
- conflict log
- derived requirement candidates

### Roles

- system engineer
- architect
- safety engineer

### Work products

- analysis record
- classification matrix

### Reviews

- cross-functional analysis review

### Tools

- issue tracker
- trace matrix

### Common failures

- contradictions not resolved
- multiple obligations in one sentence
- modes ignored

### Metrics

- defects found in analysis
- open conflicts

### Automotive example

Cluster analysis often reveals that one vague “show warning” request is really several requirements for telltale, popup, priority, and timeout behavior.

---

## 2.4 Specification

Write controlled, clear, testable requirements.

### Inputs

- analyzed requirements
- style guide
- glossary

### Activities

- write shall statements
- add identifiers and attributes
- link sources and parent requirements

### Outputs

- SyRS/SwRS/HwRS modules
- traceable requirement set

### Roles

- requirements author
- system or software engineer

### Work products

- specification module
- authoring checklist

### Reviews

- peer review
- domain review

### Tools

- DOORS/Polarion/Jama
- quality checklists

### Common failures

- using should instead of shall
- missing units
- design hidden in requirement text

### Metrics

- authoring defect density
- attribute completeness

### Automotive example

A well-written TCU retry requirement explicitly states trigger, timing tolerance, operating condition, and stop condition.

---

## 2.5 Review

Detect wording and technical defects before baseline.

### Inputs

- draft requirements
- review checklist
- source material

### Activities

- peer review
- technical walkthrough
- traceability and consistency check

### Outputs

- review comments
- approved corrections

### Roles

- author
- reviewers
- moderator

### Work products

- review record
- defect log

### Reviews

- formal review or walkthrough

### Tools

- ALM review workflow
- diff tools

### Common failures

- grammar-only reviews
- missing tester or safety reviewer
- unresolved ambiguity accepted

### Metrics

- review defects per 100 requirements
- comment closure time

### Automotive example

A review may catch that one cluster requirement says popup lasts 5 s while another says warnings persist until acknowledged.

---

## 2.6 Baseline

Freeze an approved requirement version.

### Inputs

- reviewed requirements
- approval evidence
- config rules

### Activities

- assign baseline version
- freeze content
- communicate authoritative set

### Outputs

- approved baseline
- release note

### Roles

- configuration manager
- requirements owner
- project lead

### Work products

- baseline package
- approval record

### Reviews

- baseline readiness review

### Tools

- ALM baseline features
- config management tools

### Common failures

- baselining with major open issues
- teams using uncontrolled copies

### Metrics

- post-baseline volatility
- downstream alignment rate

### Automotive example

A system baseline at milestone A allows software and test teams to work against a stable contractual reference.

---

## 2.7 Architecture

Allocate responsibilities and define structure.

### Inputs

- baselined system requirements
- platform constraints
- safety and cybersecurity concepts

### Activities

- allocate to ECUs and subsystems
- define interfaces and timing budgets
- raise architecture-derived requirements

### Outputs

- allocation matrix
- ICD updates
- derived requirements

### Roles

- system architect
- network architect
- software architect

### Work products

- architecture description
- interface control document

### Reviews

- architecture review
- timing review

### Tools

- SysML/UML tools
- network databases

### Common failures

- unclear ownership
- diagnostic path forgotten
- interface assumptions not controlled

### Metrics

- allocation coverage
- unresolved interface count

### Automotive example

An FCW path may allocate sensing to ADAS ECU, routing to gateway, and display to cluster, generating derived interface requirements.

---

## 2.8 Decomposition

Split higher-level requirements into implementable lower-level requirements.

### Inputs

- allocated system requirements
- architecture decisions
- timing budgets

### Activities

- derive ECU/HW/SW requirements
- preserve parent intent
- establish parent-child traceability

### Outputs

- lower-level requirements
- decomposition rationale

### Roles

- system engineer
- subsystem leads
- software requirements engineer

### Work products

- SwRS/HwRS modules
- trace links

### Reviews

- decomposition review
- trace review

### Tools

- hierarchy views
- allocation reports

### Common failures

- copying parent text verbatim
- orphan low-level requirements
- unclear child ownership

### Metrics

- parent coverage
- orphan requirement count

### Automotive example

“Warn driver of collision risk” may decompose into target validity, TTC logic, HMI request, routing, and diagnostic monitoring requirements.

---

## 2.9 Implementation

Realize requirements in code, configuration, hardware, and calibration.

### Inputs

- baselined low-level requirements
- design artifacts
- coding constraints

### Activities

- implement code and config
- raise clarifications
- maintain links where required

### Outputs

- software, calibration, config, hardware outputs

### Roles

- developers
- calibration engineers
- integrators

### Work products

- source code
- AUTOSAR config
- CAN database changes

### Reviews

- code review
- implementation trace review

### Tools

- IDE
- compilers
- version control

### Common failures

- developers silently fixing requirement gaps in code
- hidden derived behavior

### Metrics

- clarification requests
- requirement-related code defects

### Automotive example

If eSIM activation failure behavior was never specified, implementation must raise a requirement gap rather than bury a guess in code.

---

## 2.10 Verification

Show that implementation satisfies each requirement.

### Inputs

- requirements with verification intent
- implemented product
- test environment definitions

### Activities

- derive tests
- execute bench/SIL/HIL/analysis
- record pass/fail evidence

### Outputs

- test cases
- coverage reports
- verification evidence

### Roles

- test engineer
- integration engineer
- analyst

### Work products

- unit tests
- HIL procedures
- reports

### Reviews

- test readiness review
- coverage review

### Tools

- test management tools
- CAN tools
- HIL benches

### Common failures

- subjective pass criteria
- negative scenarios omitted
- multiple obligations per requirement complicate tests

### Metrics

- requirement coverage
- pass/fail rate

### Automotive example

A cluster telltale latency requirement can be verified by timestamping input signal reception and display activation.

---

## 2.11 Validation

Check whether the right product was built for the real use case.

### Inputs

- stakeholder needs
- verified system
- vehicle scenarios

### Activities

- vehicle-level scenario assessment
- usability and nuisance evaluation
- acceptance review

### Outputs

- validation report
- acceptance feedback
- change requests

### Roles

- validation team
- feature owner
- OEM acceptance team

### Work products

- vehicle test report
- scenario verdict log

### Reviews

- acceptance review
- field trial review

### Tools

- proving grounds
- data loggers

### Common failures

- verification confused with validation
- real driving scenarios missing

### Metrics

- scenario acceptance rate
- nuisance issue rate

### Automotive example

An ADAS warning function may verify in HIL yet fail validation because drivers consider it overly intrusive in dense urban traffic.

---

## 2.12 Change Management

Control modifications after baseline.

### Inputs

- change requests
- defects
- regulatory updates
- field issues

### Activities

- impact analysis
- approve/reject/defer
- update linked artifacts

### Outputs

- change decisions
- updated requirements
- audit trail

### Roles

- change board
- requirements owner
- project manager

### Work products

- impact analysis
- change record

### Reviews

- change board review

### Tools

- issue tracker
- traceability reports

### Common failures

- text changed without impact analysis
- tests not updated
- variant scope forgotten

### Metrics

- change turnaround time
- post-baseline volatility

### Automotive example

A new OTA logging rule may affect TCU requirements, backend payloads, service diagnostics, and compliance evidence.

---

## 2.13 Maintenance

Keep the requirement repository healthy over the product lifecycle.

### Inputs

- released baselines
- field lessons
- platform reuse decisions

### Activities

- retire obsolete text
- improve patterns
- maintain trace links

### Outputs

- current repository
- reuse guidelines
- lessons learned

### Roles

- requirements custodian
- quality manager
- configuration manager

### Work products

- repository health report
- pattern library

### Reviews

- periodic repository review

### Tools

- ALM dashboards
- reuse libraries

### Common failures

- dead requirements retained forever
- legacy copy-paste without context review

### Metrics

- obsolete count
- reuse rate

### Automotive example

A cluster platform reused across regions should remove obsolete market-specific wording before the next program copies it.

---

## 2.14 Lifecycle summary

| Stage | Main question | Typical exit criterion |
|---|---|---|
| Stakeholder Need | What problem must be solved? | Scope and user/business intent are understood. |
| Elicitation | What raw expectations and sources exist? | Sources and scenarios are captured. |
| Analysis | What do the source statements really mean? | Major ambiguity and conflict are resolved or logged. |
| Specification | How do we express the obligations clearly? | Controlled requirement set exists. |
| Review | Is the text good enough to trust? | Major review defects are closed. |
| Baseline | Which version is authoritative? | Approved baseline is frozen. |
| Architecture | Where is each responsibility allocated? | Ownership and interfaces are defined. |
| Decomposition | How is high-level intent split into lower-level obligations? | Implementable child requirements exist. |
| Implementation | How is the requirement realized? | Code/configuration/hardware exists. |
| Verification | Did we build it according to requirements? | Objective evidence exists. |
| Validation | Did we build the right thing for the user and context? | Stakeholder intent is accepted in scenario testing. |
| Change Management | How are updates controlled? | Approved changes are consistently propagated. |
| Maintenance | How is long-term repository quality preserved? | Current, reusable, auditable requirement set remains healthy. |

---

# 3. REQUIREMENTS ELICITATION

## 3.1 What elicitation means

Elicitation is the disciplined discovery of needs, expectations, constraints, scenarios, and hidden assumptions.

It is more than collecting statements.
It includes questioning, clarifying, challenging vague wording, and translating domain language into engineering-ready input.

## 3.2 Main sources of requirements

| Source | What it contributes | Example |
|---|---|---|
| Customer / driver | user value and usability expectations | Driver expects FCW warnings to be timely and understandable. |
| OEM feature definition | authoritative program intent and brand behavior | OEM defines activation speed and warning modality for LDW. |
| Regulatory documents | legal obligations and compliance constraints | Cluster telltale behavior and eCall obligations are regulation driven. |
| Safety analyses | hazards, safety goals, and safe-state needs | AEB shall suppress unintended braking under defined faults. |
| Security analyses | threats, attack paths, and mitigation needs | TCU shall authenticate OTA packages. |
| System requirements | parent obligations for lower-level decomposition | Vehicle-level warning timing drives ECU and HMI requirements. |
| Stakeholder interviews | tacit knowledge and practical operational needs | Service engineers may need readout of last modem error cause. |
| Workshops | cross-functional alignment and conflict resolution | ADAS, gateway, cluster, and safety teams align on warning path behavior. |
| Vehicle use cases | normal mission scenarios | Highway drive, urban stop-and-go, reversing, towing, crash event. |
| Operational scenarios | detailed state/event sequences | TCU loses LTE in tunnel and reconnects after exit. |
| Existing system analysis | legacy behavior and field issues | Repeated reconnect storms reveal need for backoff rules. |
| Legacy requirements | reuse candidates from related programs | Prior gateway routing requirements may be reusable with context review. |
| Interface specifications | signals, protocols, units, message timing | CAN scale and timeout rules between chassis ECU and cluster. |
| Supplier specifications | capabilities and constraints from lower-tier suppliers | Radar supplier provides detection range and confidence semantics. |
| Diagnostics specifications | DTC, UDS, freeze-frame, service expectations | TCU shall expose SIM state through a data identifier. |
| Manufacturing and service concepts | end-of-line, flashing, replacement, field maintenance | Cluster shall support bulb test and pixel test in manufacturing mode. |

## 3.3 Interviews

### Good practice

- prepare focused questions
- ask for thresholds and failure cases
- challenge vague words such as quickly or safe

### Automotive example

A TCU backend architect may reveal that wake-up storms must be rate-limited to protect servers.

## 3.4 Workshops

### Good practice

- map actors, signals, modes, and exceptions
- resolve terminology conflicts live
- capture decisions and open issues

### Automotive example

A workshop between ADAS, brake, cluster, and safety teams can define FCW-to-AEB escalation rules.

## 3.5 Observation

### Good practice

- watch real service or user workflow
- compare procedure vs real practice
- note timing and context details

### Automotive example

Observing workshop diagnosis often exposes missing requirements for readable status and fault isolation.

## 3.6 Scenario analysis

### Good practice

- write preconditions, trigger, flow, alternatives, failures
- include degraded cases
- convert scenarios into requirement candidates

### Automotive example

A charging scenario may reveal cluster behavior needed during cable connect, active charge, interruption, and charge complete.

## 3.7 Use cases

### Good practice

- focus on actor goal and success criteria
- identify alternative flows
- treat use cases as input, not final requirements

### Automotive example

Use case: driver receives blind-spot warning while initiating a lane change.

## 3.8 Functional decomposition

### Good practice

- split a feature into sensing, logic, HMI, diagnostics, safety, and service functions
- derive questions for each block

### Automotive example

Remote vehicle status decomposes into acquisition, timestamping, caching, encryption, upload, retry, and backend acknowledgment.

## 3.9 Domain analysis

### Good practice

- study platform norms and existing patterns
- understand standards and recurring failure modes

### Automotive example

Lane departure warning on one platform often reveals reusable activation and suppression patterns.

## 3.10 Prototyping

### Good practice

- use mock-ups to surface unstated expectations
- capture learned behavior as explicit requirements

### Automotive example

A warning popup prototype may show that text alone is insufficient without a telltale.

## 3.11 Existing-system analysis

### Good practice

- review current logs, complaints, and known defects
- separate useful legacy behavior from accidental behavior

### Automotive example

Field data may show the TCU needs exponential retry backoff after repeated attach failures.

## 3.12 Failure analysis

### Good practice

- ask what can go wrong
- define detection, DTC, degrade, and recovery needs

### Automotive example

Camera blockage analysis leads to suppression, unavailable indication, and recovery requirements.

## 3.13 HARA-driven elicitation

### Good practice

- start from hazardous events and safety goals
- derive required monitors and safe-state behavior

### Automotive example

For AEB, HARA may require explicit inhibition of braking on certain corrupted target inputs.

## 3.14 Realistic elicitation examples

### ADAS example

Raw statement:

> The system should warn the driver before a likely collision.

Questions that must be asked:

- Which target classes are in scope?
- Which speeds and road types are in scope?
- What defines likely?
- What warning modalities are mandatory?
- What happens if sensor confidence is low?

### TCU example

Raw statement:

> In a severe crash the vehicle must call emergency services.

Questions that must be asked:

- What input defines severe crash?
- What happens if voice setup fails?
- What happens if GNSS is unavailable?
- What data must be transmitted before call setup?
- What service diagnostics are needed?

### Cluster example

Raw statement:

> Show the low fuel warning at the right time.

Questions that must be asked:

- What is the exact threshold?
- Is hysteresis required?
- Does the warning include telltale, text, or both?
- What happens when the fuel signal is invalid?
- Do markets or variants differ?

---

# 4. REQUIREMENT CLASSIFICATION

Classification helps determine ownership, review path, decomposition, and verification strategy.

## 4.1 By abstraction level

| Level | Purpose | Example |
|---|---|---|
| Stakeholder | user or business need | The vehicle shall help the driver avoid unintentional lane departure. |
| Vehicle | vehicle-level feature behavior | The vehicle shall warn the driver within 300 ms when LDW criteria are met. |
| System | function or item responsibility | The LDW system shall evaluate lane departure above 60 km/h. |
| Subsystem | logical subsystem obligation | The perception subsystem shall provide lane confidence every 40 ms. |
| ECU | concrete controller obligation | The ADAS ECU shall issue `LDW_Request` when departure criteria are met. |
| Hardware | physical element obligation | The camera shall provide lane model timestamps. |
| Software | software-item or component obligation | The LDW manager shall suppress warnings while turn indicator is active. |
| Component | module-level detail where needed | The indicator debounce component shall filter input for 50 ms. |

## 4.2 By behavior class

| Class | Focus | Example |
|---|---|---|
| Functional | what happens | When reverse gear is engaged, the cluster shall request reverse camera display. |
| Performance | how well | The TCU shall complete backend session setup within 5 s. |
| Timing | when or how often | The ADAS ECU shall transmit warning messages every 20 ms ±1 ms. |
| Interface | data exchange and semantics | The gateway shall forward `SOC` using the defined scaling and timeout rules. |
| Diagnostic | fault visibility and service behavior | The cluster shall store a DTC on missing speed input timeout. |
| Safety | risk reduction and safe state | The steering assist controller shall stop torque requests after plausibility fault. |
| Security | attack resistance and trust | The TCU shall verify update package signature before installation. |
| Reliability | repeatable correct operation over time | The restart manager shall tolerate one transient restart failure and retry. |
| Availability | readiness and uptime | The emergency call path shall be ready within 12 s after ignition ON. |
| Maintainability | service and repair friendliness | The TCU shall expose modem state through diagnostic DID. |

## 4.3 By source

| Source class | Meaning | Example |
|---|---|---|
| Customer | end-user or fleet expectation | Remote door status shall be available in the mobile app. |
| OEM | program or brand-defined behavior | Warning priority shall follow OEM HMI policy. |
| Regulatory | legal obligation | Mandatory telltales shall satisfy applicable market regulations. |
| Safety | derived from hazard and safety concept | AEB shall inhibit unintended braking on invalid target input. |
| Security | derived from threat analysis | Gateway shall deny unauthenticated extended diagnostic access. |
| Architecture | created by allocation and design structure | Gateway shall provide timeout substitution because source and sink ECUs are in different domains. |
| Interface | driven by another system boundary | Cluster shall decode vehicle speed using the defined signal scaling. |
| Derived | required to realize, verify, or safely support a parent requirement | ADAS ECU shall provide warning validity status in addition to warning request. |
| Design constraint | mandatory platform or solution limit | TCU shall use the OEM secure boot chain on the selected SoC. |

## 4.4 Derived requirements in depth

A **derived requirement** is created because a parent requirement cannot be fully realized, integrated, verified, or safely operated without additional lower-level obligations.

Derived requirements typically come from:

- architecture allocation
- interface realization
- timing budget distribution
- safety mechanism needs
- diagnostics and service visibility
- security and compliance constraints
- verification observability needs

### Derived requirement example: ADAS warning path

Parent requirement:

> The vehicle shall warn the driver of imminent frontal collision.

Necessary derived requirements may include:

- The ADAS ECU shall transmit `FCW_Request` and `FCW_Severity` every 20 ms.
- The gateway shall route the FCW message to the cluster domain within one routing cycle.
- The cluster shall display the visual FCW warning when `FCW_Request` is TRUE.

### Derived requirement example: TCU diagnostics

Parent requirement:

> The TCU shall establish a backend session automatically after ignition ON.

Derived requirements may include:

- The TCU shall store a DTC when session establishment fails continuously for more than 120 s.
- The TCU shall expose the last failure cause category via diagnostics.
- The TCU shall persist the last successful connection timestamp.

### Good handling of derived requirements

- record the parent link
- document derivation rationale
- review with affected stakeholders
- baseline the new requirement
- verify it like any other requirement

### Bad handling of derived requirements

- hiding them only in code or architecture diagrams
- labeling design preference as “derived requirement” without source rationale
- implementing them without customer visibility when contractual scope changes
- failing to link them to tests

---

# 5. GOOD REQUIREMENT CHARACTERISTICS

A strong requirement is usable by authors, reviewers, implementers, testers, auditors, and maintainers.

## 5.1 Correct

A good requirement is **correct** when it matches the true intended need.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The cluster shall display the seatbelt telltale when any door is open. | Door-open and seatbelt logic are different functions. | The cluster shall display the seatbelt telltale when the seatbelt reminder request is TRUE. | The trigger matches the real function source. |

### Review questions

- Does the statement satisfy the correct criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.2 Complete

A good requirement is **complete** when it contains enough information to implement and verify.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The TCU shall reconnect to the backend after connection loss. | No retry interval, operating condition, or end condition is defined. | When backend connection loss is detected while ignition is ON, the TCU shall retry every 30 s ±2 s until connection is restored or ignition is switched OFF. | Trigger, condition, timing, and termination are explicit. |

### Review questions

- Does the statement satisfy the complete criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.3 Consistent

A good requirement is **consistent** when it does not conflict with other approved statements.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The cluster shall display the FCW popup for 8 s. | Another approved requirement says warnings persist until acknowledged or request clears. | When FCW request is active, the cluster shall display the popup until the request becomes FALSE or the driver acknowledges it. | The behavior aligns with the common warning persistence policy. |

### Review questions

- Does the statement satisfy the consistent criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.4 Unambiguous

A good requirement is **unambiguous** when it has only one reasonable interpretation.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The ADAS ECU shall warn the driver when a collision is likely. | Likely is subjective. | When the calibrated FCW criteria are fulfilled for a valid ego-lane target, the ADAS ECU shall request a forward collision warning. | The trigger is tied to defined criteria rather than opinion. |

### Review questions

- Does the statement satisfy the unambiguous criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.5 Verifiable

A good requirement is **verifiable** when it supports objective pass/fail determination.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The gateway shall route charging status efficiently. | Efficiently is not measurable. | The gateway shall forward `ChargeStatus` to the cluster within one routing cycle with no message loss in nominal operation. | The tester can measure timing and loss. |

### Review questions

- Does the statement satisfy the verifiable criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.6 Feasible

A good requirement is **feasible** when it is realistically achievable.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The cluster shall boot and render all graphics within 10 ms. | This is likely impossible on the selected platform. | The cluster shall render vehicle speed and mandatory telltales within 800 ms after ignition ON under nominal supply conditions. | The target is realistic and scoped. |

### Review questions

- Does the statement satisfy the feasible criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.7 Necessary

A good requirement is **necessary** when it provides real value or compliance.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The TCU shall log every successful DNS resolution event for ten years. | No stakeholder, service, or compliance need is shown. | The TCU shall log backend connection failures with timestamp and failure cause for service diagnosis. | The behavior is justified and useful. |

### Review questions

- Does the statement satisfy the necessary criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.8 Traceable

A good requirement is **traceable** when it can be linked backward and forward.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The gateway shall reject unauthorized diagnostics. | Valid idea, but source and parent linkage may be missing. | Derived from cybersecurity requirement CYB-045, the gateway shall reject extended diagnostic session requests that fail secure authentication. | Source rationale is preserved. |

### Review questions

- Does the statement satisfy the traceable criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.9 Atomic

A good requirement is **atomic** when it contains one main obligation.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| When crash severity is high, the TCU shall start eCall, store the crash record, notify the backend, and display a cluster message. | Many separate obligations are packed into one sentence. | Separate requirements shall define eCall initiation, crash record storage, backend notification, and cluster notification. | Each child behavior can be allocated and tested independently. |

### Review questions

- Does the statement satisfy the atomic criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.10 Singular

A good requirement is **singular** when it keeps mandatory and optional behavior separate.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The cluster shall show the low fuel warning and maybe a text if needed. | Optionality and obligation are mixed. | When low fuel criteria are met, the cluster shall activate the amber low fuel telltale. Where low fuel popup feature is enabled, the cluster shall display the popup for 5 s. | Mandatory and variant-specific behavior are separated. |

### Review questions

- Does the statement satisfy the singular criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.11 Modifiable

A good requirement is **modifiable** when it is easy to update without side effects.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The TCU shall send door status, hood status, trunk status, charging status, and tire pressure status every 30 s. | Any one payload change forces a large statement rewrite. | Separate requirements or a controlled interface table shall define each signal group. | Change impact becomes local instead of global. |

### Review questions

- Does the statement satisfy the modifiable criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.12 Understandable

A good requirement is **understandable** when it is readable by cross-functional reviewers.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| The SWC shall assert HMI_EVT_47 upon ST3->ST4 transition when QF=1. | Internal jargon blocks review. | When charging state transitions from cable connected to charging active and payment authorization is valid, the cluster shall display the charging active icon. | The same intent is readable to system, test, and service teams. |

### Review questions

- Does the statement satisfy the understandable criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.13 Prioritized

A good requirement is **prioritized** when it has known business or safety importance.

| Bad Requirement | Problem | Improved Requirement | Why It Is Better |
|---|---|---|---|
| All requirements are critical. | If everything is critical, planning and triage are meaningless. | The brake failure telltale requirement shall be classified as safety-critical because it supports mandatory warning presentation. | Priority helps release and change decisions. |

### Review questions

- Does the statement satisfy the prioritized criterion?
- Would implementation teams invent missing detail?
- Would a tester or reviewer interpret it the same way?

## 5.14 Practical quality checklist

- Is the source known?
- Is the statement in approved project style?
- Is the requirement atomic and singular?
- Are trigger, response, timing, units, and state clear?
- Is variant applicability explicit?
- Can verification produce an objective result?
- Has invalid, degraded, and recovery behavior been considered where relevant?
- Are parent, child, and test trace links defined?

---

# 6. REQUIREMENT WRITING

Professional requirement writing converts engineering intent into precise, reviewable, testable text.

## 6.1 Core sentence anatomy

A strong requirement usually contains:

- subject
- modal verb
- trigger or condition
- required response
- timing, quantity, range, or constraint where needed

Generic form:

```text
When <trigger>, the <subject> shall <response> within <time> under <conditions>.
```

## 6.2 Shall, should, may, must

| Word | Typical meaning | Recommended use |
|---|---|---|
| Shall | mandatory requirement | default for binding product requirements |
| Should | recommendation or goal | avoid in mandatory requirement sets unless intentionally non-binding |
| May | permission or option | use carefully for allowed or optional behavior |
| Must | strong obligation, often external/legal wording | often reserved for regulatory or process text |

### Shall

Use **shall** for mandatory, verifiable product behavior.

**Weak**: The cluster should show the warning fast.

**Strong**: When brake failure warning request is TRUE, the cluster shall activate the red brake telltale within 100 ms.

### Should

Use **should** for recommendations, preferred practices, or concept guidance.

### May

Use **may** for permission or optional capability.

### Must

Use **must** mainly when quoting regulations or external obligations, then translate into controlled requirement style where appropriate.

## 6.3 Conditions, triggers, and states

Useful condition words:

- when
- while
- if
- upon
- where
- under

Examples:

- When ignition transitions from OFF to ON, the TCU shall start modem initialization.
- While reverse gear is engaged, the cluster shall request reverse-camera display.
- If backend certificate validation fails, the TCU shall terminate the session attempt.
- Where remote climate feature is enabled, the TCU shall accept valid preconditioning commands.

## 6.4 Response wording

Prefer observable verbs:

- display
- transmit
- store
- request
- clear
- reject
- inhibit
- activate
- deactivate
- retry
- respond

Avoid vague verbs unless heavily qualified:

- handle
- manage
- process
- optimize
- ensure
- support

Weak:

> The TCU shall handle modem failures.

Strong:

> When modem restart fails three consecutive times, the TCU shall store a DTC, inhibit backend session establishment, and report telematics unavailable status to the vehicle network.

## 6.5 Constraints

Constraints express mandatory limits.

Weak:

> The software shall use low memory.

Strong:

> The cluster graphics application shall not exceed 120 MB of RAM consumption in nominal operation with the full telltale set enabled.

## 6.6 Timing

Timing requirements cover:

- deadlines
- periods
- timeouts
- debounce windows
- startup time
- retry intervals
- persistence duration
- jitter

Weak:

> The cluster shall show the warning immediately.

Strong:

> When `BrakeWarnReq` becomes TRUE, the cluster shall activate the red brake telltale within 100 ms.

## 6.7 Quantification

Replace vague adjectives with measurable quantities.

| Weak | Strong |
|---|---|
| The TCU shall keep logs for a long time. | The TCU shall retain the last 50 backend connection failure records in non-volatile memory. |
| The radar shall detect distant targets. | The radar shall detect passenger vehicle targets at distances up to 180 m under nominal conditions. |
| The cluster shall dim smoothly. | The cluster shall support brightness adjustment in steps no greater than 2% of full scale. |

## 6.8 Tolerances

Examples:

- The gateway shall forward the message every 20 ms ±1 ms.
- The TCU real-time clock drift shall not exceed ±2 s over 24 h without network time synchronization.
- The cluster popup shall remain visible for 5 s ±0.5 s.

## 6.9 Weak vs strong examples

| Weak wording | Strong wording |
|---|---|
| The system shall warn the driver if a crash may happen. | When calibrated FCW criteria are fulfilled for a valid ego-lane target, the ADAS ECU shall request a forward collision warning. |
| The TCU shall reconnect after losing the network. | When backend connection loss is detected while ignition is ON, the TCU shall attempt session re-establishment every 30 s ±2 s until the connection is restored or ignition is switched OFF. |
| Important warnings shall have high priority. | The cluster shall present the red brake failure warning above all non-safety informational popups and shall not suppress the red brake telltale while the request is active. |
| The gateway shall detect communication problems. | The gateway shall set CAN2 bus-off fault status when the CAN controller reports bus-off continuously for longer than 100 ms. |
| The TCU shall install only valid updates. | Before starting OTA installation, the TCU shall verify the update package signature using the OEM-trusted public key set and shall reject the installation if verification fails. |

## 6.10 Authoring rules of thumb

- One sentence, one main obligation.
- Prefer active voice.
- State units explicitly.
- Define abbreviations in a glossary.
- Avoid “and/or”.
- Avoid “etc.” and “as necessary”.
- Separate requirement text from rationale and notes.
- Keep solution detail out unless it is an intentional constraint.

---

# 7. REQUIREMENT PATTERNS

Patterns reduce ambiguity and help authors write consistently.

## 7.1 Functional pattern

```text
When <trigger or condition>, the <subject> shall <response>.
```

## 7.2 Timing pattern

```text
When <trigger>, the <subject> shall <response> within <time>.
```

or

```text
The <subject> shall <response> every <period> ± <tolerance> while <state>.
```

## 7.3 Performance pattern

```text
The <subject> shall <perform action> with <capacity / latency / accuracy / resource limit> under <conditions>.
```

## 7.4 Safety pattern

```text
When <hazard or fault condition> occurs, the <subject> shall <prevent / detect / mitigate / transition to safe state> within <time>.
```

## 7.5 Diagnostic pattern

```text
When <fault condition> is present for <time>, the <subject> shall store or report <diagnostic information>.
```

## 7.6 Communication pattern

```text
The <subject> shall transmit or receive <signal/message> on <interface> with <format/rate/rules>.
```

## 7.7 Fault handling pattern

```text
If <fault> is detected, the <subject> shall <fault response> and shall <report or inhibit behavior>.
```

## 7.8 Degradation pattern

```text
While <degraded condition> exists, the <subject> shall <reduced behavior> and shall <indicate limitation>.
```

## 7.9 Recovery pattern

```text
When <recovery condition> is met, the <subject> shall <restore or resume behavior> within <time>.
```

## 7.10 Example library

The following library contains more than 100 automotive requirement-writing examples across ADAS, TCU, Cluster, Gateway, and related systems.

## 7.11 Functional examples

### Example 001 — Functional: AEB warning request

- Domain: ADAS
- Pattern family: Functional
- Intent: Warn on valid imminent frontal collision
- Weak wording: `The system shall warn the driver about collision.`
- Preferred requirement:

```text
When time-to-collision falls below the forward warning threshold for a valid ego-lane vehicle target, the ADAS ECU shall set `FCW_Request` to TRUE.
```

- Verification idea: Stimulate TTC threshold crossing in SIL and observe output signal transition.
- Why it is stronger: Avoids vague words like likely and identifies the source ECU output.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 002 — Functional: Lane departure suppression

- Domain: ADAS
- Pattern family: Functional
- Intent: Suppress nuisance warnings during intentional lane changes
- Weak wording: `The system shall not annoy the driver during lane changes.`
- Preferred requirement:

```text
While the turn indicator is active on the side of the predicted lane departure, the ADAS ECU shall suppress lane departure warning requests.
```

- Verification idea: Simulate departure with indicator active and verify no request.
- Why it is stronger: State-based functional suppression is explicit.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 003 — Functional: eCall initiation

- Domain: TCU
- Pattern family: Functional
- Intent: Start emergency procedure after severe crash
- Weak wording: `The telematics unit shall call for help after crash.`
- Preferred requirement:

```text
When the restraint control module publishes a deployment-level crash event, the TCU shall initiate the eCall procedure.
```

- Verification idea: Inject crash event on the vehicle network and verify eCall state transition.
- Why it is stronger: Names the trigger source and expected response.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 004 — Functional: Heartbeat start

- Domain: TCU
- Pattern family: Functional
- Intent: Start keepalive after successful session establishment
- Weak wording: `The TCU shall send heartbeats when connected.`
- Preferred requirement:

```text
When backend session establishment completes successfully, the TCU shall start periodic heartbeat transmission.
```

- Verification idea: Complete session setup and verify heartbeat starts.
- Why it is stronger: Separates connection success from subsequent behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 005 — Functional: Low fuel telltale

- Domain: Cluster
- Pattern family: Functional
- Intent: Notify the driver about low fuel
- Weak wording: `The cluster shall show low fuel.`
- Preferred requirement:

```text
When low fuel warning criteria are fulfilled, the cluster shall activate the amber low fuel telltale.
```

- Verification idea: Drive simulated fuel below threshold and verify telltale.
- Why it is stronger: Makes the output and trigger precise.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 006 — Functional: Incoming call banner

- Domain: Cluster
- Pattern family: Functional
- Intent: Display incoming call status
- Weak wording: `The cluster shall indicate phone calls.`
- Preferred requirement:

```text
When the infotainment system requests an incoming call notification, the cluster shall display the incoming call banner.
```

- Verification idea: Inject call request and observe banner presentation.
- Why it is stronger: Clear user-visible response requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 007 — Functional: Diagnostic routing

- Domain: Gateway
- Pattern family: Functional
- Intent: Route external tester requests to target subnet
- Weak wording: `The gateway shall send diagnostics where needed.`
- Preferred requirement:

```text
When a valid OBD diagnostic request is received on the external diagnostic connector, the gateway shall route the request to the addressed vehicle subnet.
```

- Verification idea: Send diagnostic request and inspect routed traffic.
- Why it is stronger: Specifies gateway function boundary.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 008 — Functional: Wake propagation

- Domain: Gateway
- Pattern family: Functional
- Intent: Wake connected domains at ignition on
- Weak wording: `The gateway shall wake other networks.`
- Preferred requirement:

```text
When KL15 transitions from OFF to ON, the gateway shall propagate the configured wake-up event to connected network domains.
```

- Verification idea: Toggle ignition and verify wake-up traffic.
- Why it is stronger: Defines a specific event and action.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 009 — Functional: Remote lock request

- Domain: Body
- Pattern family: Functional
- Intent: Translate remote command into door lock action
- Weak wording: `The car shall lock from the app.`
- Preferred requirement:

```text
When a valid remote lock command is received from the TCU, the body control module shall request door locking.
```

- Verification idea: Inject command and verify BCM lock request.
- Why it is stronger: Connects telematics feature to body ECU behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Body integration.

### Example 010 — Functional: Washer warning icon

- Domain: Cluster
- Pattern family: Functional
- Intent: Display washer-fluid low indication
- Weak wording: `The cluster shall inform the driver about washer fluid.`
- Preferred requirement:

```text
When washer fluid low request is TRUE, the cluster shall display the washer fluid warning icon.
```

- Verification idea: Toggle request and verify icon.
- Why it is stronger: Observable HMI output.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 011 — Functional: Hands-on reminder

- Domain: ADAS
- Pattern family: Functional
- Intent: Request reminder after prolonged hands-off condition
- Weak wording: `The system shall remind the driver to hold the wheel.`
- Preferred requirement:

```text
When the hands-off timer exceeds the calibrated threshold during active lane centering, the ADAS ECU shall request a hands-on reminder.
```

- Verification idea: Let timer expire and verify request.
- Why it is stronger: Links reminder to operating state and calibrated threshold.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 012 — Functional: Roaming state report

- Domain: TCU
- Pattern family: Functional
- Intent: Update backend when modem roaming changes
- Weak wording: `The TCU shall report roaming.`
- Preferred requirement:

```text
When cellular roaming status changes, the TCU shall update the reported roaming state to the backend.
```

- Verification idea: Change roaming indication in modem simulation and verify payload update.
- Why it is stronger: Defines a clean state-change trigger.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

## 7.12 Timing examples

### Example 013 — Timing: Brake telltale latency

- Domain: Cluster
- Pattern family: Timing
- Intent: Warn driver quickly about brake failure
- Weak wording: `The warning shall appear immediately.`
- Preferred requirement:

```text
When `BrakeWarnReq` becomes TRUE, the cluster shall activate the red brake telltale within 100 ms.
```

- Verification idea: Timestamp input signal and telltale activation on the bench.
- Why it is stronger: Replaces subjective immediacy with a measurable deadline.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 014 — Timing: Retry interval

- Domain: TCU
- Pattern family: Timing
- Intent: Retry backend connection at a defined cadence
- Weak wording: `The TCU shall retry later.`
- Preferred requirement:

```text
After a failed backend session establishment attempt, the TCU shall start the next retry after 30 s ±2 s while ignition remains ON.
```

- Verification idea: Force repeated failures and measure retry intervals.
- Why it is stronger: Specifies interval and operating condition.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 015 — Timing: Routing cycle latency

- Domain: Gateway
- Pattern family: Timing
- Intent: Forward a message within budget
- Weak wording: `The gateway shall forward charging status quickly.`
- Preferred requirement:

```text
The gateway shall forward message `SOC_Status` to the cluster domain within one routing cycle after reception on the source bus.
```

- Verification idea: Measure ingress-to-egress delay using bus traces.
- Why it is stronger: Good timing budget statement at interface boundary.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 016 — Timing: Warning issuance delay

- Domain: ADAS
- Pattern family: Timing
- Intent: Issue LDW request within timing budget
- Weak wording: `The ADAS ECU shall react fast.`
- Preferred requirement:

```text
When lane departure warning criteria become TRUE, the ADAS ECU shall request the warning within 150 ms.
```

- Verification idea: Drive criteria transition and measure output latency.
- Why it is stronger: Connects reaction speed to explicit trigger.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 017 — Timing: GNSS freshness timeout

- Domain: TCU
- Pattern family: Timing
- Intent: Mark stale location data after timeout
- Weak wording: `Old GNSS data shall not be used for too long.`
- Preferred requirement:

```text
If no valid GNSS position update is received for 5 s while location reporting is active, the TCU shall mark live position as stale.
```

- Verification idea: Block GNSS feed and measure stale-flag assertion time.
- Why it is stronger: Defines timeout and state context.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 018 — Timing: Popup duration

- Domain: Cluster
- Pattern family: Timing
- Intent: Persist low fuel popup for fixed duration
- Weak wording: `The popup shall stay for some seconds.`
- Preferred requirement:

```text
When low fuel warning is first activated, the cluster shall display the low fuel popup for 5 s ±0.5 s.
```

- Verification idea: Trigger low fuel condition and measure popup persistence.
- Why it is stronger: Adds measurable duration and tolerance.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 019 — Timing: Watchdog refresh period

- Domain: Gateway
- Pattern family: Timing
- Intent: Service watchdog periodically
- Weak wording: `The gateway shall keep the watchdog alive.`
- Preferred requirement:

```text
The gateway application shall refresh the software watchdog every 20 ms ±5 ms while the main loop is healthy.
```

- Verification idea: Observe refresh intervals under nominal run mode.
- Why it is stronger: Periodic timing with operational condition.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 020 — Timing: Blockage debounce

- Domain: ADAS
- Pattern family: Timing
- Intent: Debounce blockage detection
- Weak wording: `The system shall not set blockage too quickly.`
- Preferred requirement:

```text
When camera blockage confidence exceeds threshold continuously for 500 ms, the ADAS ECU shall set `CameraBlocked` to TRUE.
```

- Verification idea: Force blockage confidence high and verify debounce timing.
- Why it is stronger: Converts intent into a precise debounce rule.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 021 — Timing: Emergency path boot time

- Domain: TCU
- Pattern family: Timing
- Intent: Make emergency path ready soon after power on
- Weak wording: `The emergency function shall be ready soon.`
- Preferred requirement:

```text
After KL15 ON, the TCU shall make the emergency call path ready within 12 s under nominal supply and network conditions.
```

- Verification idea: Cold boot TCU and measure readiness indicator.
- Why it is stronger: Useful readiness requirement for a critical feature.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 022 — Timing: Bulb-check completion

- Domain: Cluster
- Pattern family: Timing
- Intent: Complete startup telltale check in time
- Weak wording: `The bulb check shall not take long.`
- Preferred requirement:

```text
Upon ignition ON, the cluster shall complete mandatory telltale bulb check within 3 s.
```

- Verification idea: Cycle ignition and verify self-test timing.
- Why it is stronger: Crisp startup deadline.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 023 — Timing: Bus-off detection time

- Domain: Gateway
- Pattern family: Timing
- Intent: Raise fault after persistent bus-off
- Weak wording: `The gateway shall detect bus-off quickly.`
- Preferred requirement:

```text
When the CAN controller reports bus-off continuously for more than 100 ms, the gateway shall set the CAN bus-off fault status.
```

- Verification idea: Inject bus-off and measure detection time.
- Why it is stronger: Adds persistence threshold and fault response.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 024 — Timing: Fusion cycle period

- Domain: ADAS
- Pattern family: Timing
- Intent: Run fusion at fixed cadence
- Weak wording: `Fusion shall run periodically.`
- Preferred requirement:

```text
The object fusion manager shall execute once every 40 ms ±2 ms while ADAS operating mode is ACTIVE.
```

- Verification idea: Measure task activation intervals in HIL.
- Why it is stronger: Explicit period and tolerance improve schedulability review.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

## 7.13 Performance examples

### Example 025 — Performance: Object tracking capacity

- Domain: ADAS
- Pattern family: Performance
- Intent: Track many simultaneous objects
- Weak wording: `The fusion function shall handle many objects.`
- Preferred requirement:

```text
The ADAS object fusion function shall track at least 64 simultaneous valid objects per cycle under nominal operating conditions.
```

- Verification idea: Inject 64-object scenario and confirm no dropped tracks.
- Why it is stronger: Defines quantitative capacity.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 026 — Performance: Session setup latency

- Domain: TCU
- Pattern family: Performance
- Intent: Connect to backend with acceptable delay
- Weak wording: `The TCU shall connect quickly.`
- Preferred requirement:

```text
The TCU shall establish a TLS-protected backend session within 5 s in nominal LTE coverage.
```

- Verification idea: Measure session setup time with radio simulation.
- Why it is stronger: Performance target is measurable and scoped.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 027 — Performance: Startup render time

- Domain: Cluster
- Pattern family: Performance
- Intent: Show essential info promptly after ignition on
- Weak wording: `The cluster shall boot fast.`
- Preferred requirement:

```text
The cluster shall render vehicle speed and legally required telltales within 800 ms after KL15 ON under nominal supply voltage.
```

- Verification idea: Cold boot and measure first valid rendering.
- Why it is stronger: Performance expectation focuses on essential content.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 028 — Performance: CPU load budget

- Domain: Gateway
- Pattern family: Performance
- Intent: Stay within platform compute budget
- Weak wording: `The gateway shall use low CPU.`
- Preferred requirement:

```text
The gateway software shall not exceed 70% average CPU utilization during nominal routing with all configured network channels active.
```

- Verification idea: Run stress traffic and measure CPU load.
- Why it is stronger: Turns a vague efficiency goal into a usable budget.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 029 — Performance: Log retention capacity

- Domain: TCU
- Pattern family: Performance
- Intent: Store sufficient failure history
- Weak wording: `The TCU shall keep enough logs.`
- Preferred requirement:

```text
The TCU shall retain at least 50 backend connection failure records in non-volatile memory.
```

- Verification idea: Trigger more than 50 failures and verify retention behavior.
- Why it is stronger: Quantified capacity requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 030 — Performance: Brightness range

- Domain: Cluster
- Pattern family: Performance
- Intent: Support full day/night readability range
- Weak wording: `The display shall be bright enough.`
- Preferred requirement:

```text
The cluster display shall support luminance adjustment from 10 cd/m² to 800 cd/m².
```

- Verification idea: Measure luminance at minimum and maximum settings.
- Why it is stronger: Directly measurable display performance.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 031 — Performance: Lane model accuracy

- Domain: ADAS
- Pattern family: Performance
- Intent: Meet lane estimation accuracy target
- Weak wording: `Lane estimation shall be accurate.`
- Preferred requirement:

```text
The camera lane model output shall provide lane boundary lateral position with RMS error not exceeding 0.25 m within the supported ODD.
```

- Verification idea: Compare estimated lane geometry against reference data.
- Why it is stronger: Accuracy requirement becomes testable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 032 — Performance: Diagnostic throughput

- Domain: Gateway
- Pattern family: Performance
- Intent: Route several sessions concurrently
- Weak wording: `The gateway shall handle multiple diagnostics.`
- Preferred requirement:

```text
The gateway shall support concurrent routing of at least four diagnostic request-response sessions without loss of session separation.
```

- Verification idea: Run concurrent diagnostic sessions and verify routing integrity.
- Why it is stronger: Quantifies throughput and concurrency.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 033 — Performance: RTC drift

- Domain: TCU
- Pattern family: Performance
- Intent: Maintain acceptable clock accuracy
- Weak wording: `The clock shall stay accurate.`
- Preferred requirement:

```text
Without network time synchronization, the TCU real-time clock drift shall not exceed ±2 s over 24 h at 25°C.
```

- Verification idea: Measure drift in a controlled environment.
- Why it is stronger: Performance requirement with explicit condition.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 034 — Performance: Animation refresh rate

- Domain: Cluster
- Pattern family: Performance
- Intent: Maintain visible turn-indicator smoothness
- Weak wording: `The indicator animation shall look smooth.`
- Preferred requirement:

```text
The cluster shall update the turn indicator animation at a minimum refresh rate of 20 Hz while the indicator request is active.
```

- Verification idea: Measure animation frame timing.
- Why it is stronger: Converts perception goal into measurable refresh rate.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 035 — Performance: Decision cycle capacity

- Domain: ADAS
- Pattern family: Performance
- Intent: Process all enabled functions within cycle budget
- Weak wording: `The ECU shall not overload.`
- Preferred requirement:

```text
The ADAS ECU shall process warning decision logic for all configured ADAS functions within the 40 ms control cycle.
```

- Verification idea: Stress enabled feature set and verify cycle completion.
- Why it is stronger: Good aggregate computational performance statement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 036 — Performance: Remote command response

- Domain: Body
- Pattern family: Performance
- Intent: Acknowledge remote lock command promptly
- Weak wording: `The BCM shall respond quickly.`
- Preferred requirement:

```text
The body control module shall acknowledge a valid remote lock request within 200 ms after command reception from the TCU.
```

- Verification idea: Send command and timestamp acknowledgment.
- Why it is stronger: Performance target on cross-ECU command path.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Body integration.

## 7.14 Safety examples

### Example 037 — Safety: Unintended braking inhibition

- Domain: ADAS
- Pattern family: Safety
- Intent: Prevent false AEB at very low speed without valid target
- Weak wording: `The system shall not brake unnecessarily.`
- Preferred requirement:

```text
When ego vehicle speed is below 3 km/h and no collision-path target is valid, the ADAS ECU shall inhibit autonomous emergency braking requests.
```

- Verification idea: Simulate low-speed non-target conditions and verify no brake request.
- Why it is stronger: Safety constraint is explicit and verifiable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 038 — Safety: LDW unavailable indication

- Domain: ADAS
- Pattern family: Safety
- Intent: Suppress LDW when lane input is not trustworthy
- Weak wording: `The system shall be safe if lane input fails.`
- Preferred requirement:

```text
When lane model validity is FALSE for longer than the fault tolerant time interval, the ADAS ECU shall suppress lane departure warnings and shall request feature unavailable indication.
```

- Verification idea: Invalidate lane model and observe suppression plus indication.
- Why it is stronger: Defines degraded safe behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 039 — Safety: OTA installation inhibition

- Domain: TCU
- Pattern family: Safety
- Intent: Prevent installation of unauthenticated software
- Weak wording: `Invalid updates shall not be installed.`
- Preferred requirement:

```text
If OTA package signature verification fails, the TCU shall inhibit installation of the package.
```

- Verification idea: Inject invalid signature and verify installation does not start.
- Why it is stronger: Security-driven safety gate.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 040 — Safety: Red warning priority

- Domain: Cluster
- Pattern family: Safety
- Intent: Protect visibility of critical brake warning
- Weak wording: `Important warnings shall stay visible.`
- Preferred requirement:

```text
When red brake failure warning request is active, the cluster shall present the red brake telltale independent of infotainment popup state.
```

- Verification idea: Overlay warning with popup traffic and verify visibility.
- Why it is stronger: Expresses priority rule for safety-critical HMI.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 041 — Safety: Authenticated diagnostics

- Domain: Gateway
- Pattern family: Safety
- Intent: Prevent unsafe unauthorized diagnostic access
- Weak wording: `The gateway shall be secure.`
- Preferred requirement:

```text
The gateway shall deny transition to extended diagnostic session when secure authentication has not succeeded.
```

- Verification idea: Attempt session without authentication and verify denial.
- Why it is stronger: Specific boundary-control requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 042 — Safety: Steering assist cutoff

- Domain: ADAS
- Pattern family: Safety
- Intent: Stop torque output after plausibility fault
- Weak wording: `The controller shall stop if steering input is bad.`
- Preferred requirement:

```text
When steering torque sensor plausibility becomes FALSE, the lane centering controller shall stop issuing steering assist torque requests within 100 ms.
```

- Verification idea: Inject plausibility fault and measure torque request removal.
- Why it is stronger: Hazard mitigation with timing bound.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 043 — Safety: Emergency fallback position

- Domain: TCU
- Pattern family: Safety
- Intent: Send last valid position if live GNSS unavailable
- Weak wording: `The system shall try another position source if GNSS fails.`
- Preferred requirement:

```text
When live GNSS position is unavailable during eCall initiation, the TCU shall transmit the last valid stored position if its age does not exceed the configured maximum age.
```

- Verification idea: Block GNSS and verify fallback payload behavior.
- Why it is stronger: Safety behavior with bounded fallback data validity.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 044 — Safety: Speed substitute display

- Domain: Cluster
- Pattern family: Safety
- Intent: Avoid misleading speed display on invalid input
- Weak wording: `The cluster shall handle invalid speed safely.`
- Preferred requirement:

```text
When vehicle speed input is invalid, the cluster shall suppress numerical speed update and shall activate the defined substitute indication.
```

- Verification idea: Invalidate speed signal and verify substitute behavior.
- Why it is stronger: Protects driver from misleading information.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 045 — Safety: Domain isolation on segmentation fault

- Domain: Gateway
- Pattern family: Safety
- Intent: Preserve safety concept under network fault
- Weak wording: `The gateway shall isolate problems.`
- Preferred requirement:

```text
When a network segmentation fault is detected between powertrain and chassis domains, the gateway shall maintain isolation of the affected domain according to the safety concept.
```

- Verification idea: Inject segmentation fault and verify controlled isolation.
- Why it is stronger: Links behavior to safety concept.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 046 — Safety: Confidence-gated braking

- Domain: ADAS
- Pattern family: Safety
- Intent: Issue AEB only for sufficiently trusted targets
- Weak wording: `The system shall brake only for valid targets.`
- Preferred requirement:

```text
The AEB function shall issue brake requests only for targets whose classification and trajectory confidence meet the safety-approved validity criteria.
```

- Verification idea: Vary target confidence and verify brake request gating.
- Why it is stronger: Explicit acceptance gate for hazardous output.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 047 — Safety: Low-voltage write protection

- Domain: TCU
- Pattern family: Safety
- Intent: Avoid NVM corruption during brownout
- Weak wording: `The TCU shall protect memory at low voltage.`
- Preferred requirement:

```text
When supply voltage falls below the non-volatile write protection threshold, the TCU shall stop non-essential memory writes.
```

- Verification idea: Lower supply voltage and observe write suppression.
- Why it is stronger: Safety and integrity behavior is bounded.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 048 — Safety: Acknowledge lockout

- Domain: Cluster
- Pattern family: Safety
- Intent: Do not allow driver to hide critical active warning
- Weak wording: `The user shall not dismiss critical warnings too early.`
- Preferred requirement:

```text
The cluster shall not allow driver acknowledgement to suppress a legally mandated red telltale while the corresponding warning request remains active.
```

- Verification idea: Attempt acknowledgement and verify telltale persists.
- Why it is stronger: Maintains mandatory warning persistence.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

## 7.15 Diagnostic examples

### Example 049 — Diagnostic: CAN2 bus-off DTC

- Domain: Gateway
- Pattern family: Diagnostic
- Intent: Store a fault when bus-off persists
- Weak wording: `The gateway shall indicate bus-off faults.`
- Preferred requirement:

```text
When CAN channel 2 remains in bus-off state for longer than 100 ms, the gateway shall store DTC `GW_CAN2_BusOff`.
```

- Verification idea: Inject bus-off and read DTC memory.
- Why it is stronger: Ties detection to a concrete service artifact.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 050 — Diagnostic: Backend failure DTC

- Domain: TCU
- Pattern family: Diagnostic
- Intent: Make long-lasting session failure service-visible
- Weak wording: `The TCU shall log backend problems.`
- Preferred requirement:

```text
When backend session establishment fails continuously for more than 120 s while ignition is ON, the TCU shall store a backend communication DTC.
```

- Verification idea: Block backend and observe DTC setting after threshold.
- Why it is stronger: Persistent fault becomes diagnosable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 051 — Diagnostic: Speed signal timeout DTC

- Domain: Cluster
- Pattern family: Diagnostic
- Intent: Detect missing speed input
- Weak wording: `The cluster shall diagnose lost speed messages.`
- Preferred requirement:

```text
When `VehSpd` is unavailable for longer than 300 ms while ignition is ON, the cluster shall store a vehicle speed signal timeout DTC.
```

- Verification idea: Suppress source signal and read DTC.
- Why it is stronger: Classic timeout-to-DTC behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 052 — Diagnostic: Camera blockage fault entry

- Domain: ADAS
- Pattern family: Diagnostic
- Intent: Store prolonged blockage as service fault
- Weak wording: `The system shall log camera blockage.`
- Preferred requirement:

```text
When camera blockage status remains TRUE for longer than 2 s, the ADAS ECU shall store a camera blockage fault entry.
```

- Verification idea: Force blockage and inspect diagnostic memory.
- Why it is stronger: Adds persistence and explicit output.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 053 — Diagnostic: Freeze-frame capture

- Domain: TCU
- Pattern family: Diagnostic
- Intent: Store relevant context with modem failure DTC
- Weak wording: `The fault memory shall save useful data.`
- Preferred requirement:

```text
When the TCU stores a modem registration failure DTC, it shall capture ignition state, RSSI class, PLMN, and retry counter as freeze-frame data.
```

- Verification idea: Trigger failure and inspect freeze-frame payload.
- Why it is stronger: Defines exactly what support teams need.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 054 — Diagnostic: Software version DID

- Domain: Gateway
- Pattern family: Diagnostic
- Intent: Respond to a software-version readout request
- Weak wording: `The gateway shall report its software version.`
- Preferred requirement:

```text
Upon reception of a UDS ReadDataByIdentifier request for the software version DID, the gateway shall respond with the configured software version string.
```

- Verification idea: Send UDS 0x22 request and inspect response.
- Why it is stronger: Precise service-readout behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 055 — Diagnostic: Manufacturing bulb test

- Domain: Cluster
- Pattern family: Diagnostic
- Intent: Support production and service telltale check
- Weak wording: `The cluster shall have a test mode.`
- Preferred requirement:

```text
When manufacturing diagnostic mode is active and the bulb-test routine is requested, the cluster shall illuminate all telltales for the configured test duration.
```

- Verification idea: Enter mode and trigger routine.
- Why it is stronger: Clear manufacturing diagnostic behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 056 — Diagnostic: AEB event memory

- Domain: ADAS
- Pattern family: Diagnostic
- Intent: Store intervention context for analysis
- Weak wording: `AEB events shall be logged.`
- Preferred requirement:

```text
When an AEB intervention is executed, the ADAS ECU shall store an event memory record containing target type, ego speed, and intervention timestamp.
```

- Verification idea: Trigger intervention and inspect event record.
- Why it is stronger: Defines useful post-event diagnostic evidence.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 057 — Diagnostic: SIM state DID

- Domain: TCU
- Pattern family: Diagnostic
- Intent: Expose SIM status for service
- Weak wording: `The SIM state shall be readable.`
- Preferred requirement:

```text
The TCU shall support diagnostic readout of the current SIM state via the designated data identifier.
```

- Verification idea: Send DID read request and verify returned state.
- Why it is stronger: Improves field diagnostics.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 058 — Diagnostic: DTC clear behavior

- Domain: Gateway
- Pattern family: Diagnostic
- Intent: Clear faults on valid service request
- Weak wording: `The gateway shall clear diagnostics when requested.`
- Preferred requirement:

```text
Upon successful execution of UDS ClearDiagnosticInformation, the gateway shall clear DTCs that satisfy the configured clear conditions.
```

- Verification idea: Write DTCs, send 0x14, and verify clear behavior.
- Why it is stronger: Leaves no ambiguity about service action.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 059 — Diagnostic: Buzzer fault monitoring

- Domain: Cluster
- Pattern family: Diagnostic
- Intent: Detect buzzer circuit fault during active request
- Weak wording: `The cluster shall know if the buzzer fails.`
- Preferred requirement:

```text
When buzzer output feedback indicates open circuit continuously for more than 100 ms during an active buzzer request, the cluster shall store a buzzer circuit fault.
```

- Verification idea: Inject open circuit and inspect DTC.
- Why it is stronger: Diagnostic behavior tied to measurable feedback.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 060 — Diagnostic: Calibration status DID

- Domain: ADAS
- Pattern family: Diagnostic
- Intent: Expose invalid calibration to service tool
- Weak wording: `Service shall know when calibration is invalid.`
- Preferred requirement:

```text
When ADAS calibration status is INVALID, the ECU shall report the status via the defined diagnostic data identifier.
```

- Verification idea: Set calibration invalid and read DID.
- Why it is stronger: Makes readiness state diagnosable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

## 7.16 Communication examples

### Example 061 — Communication: Battery status forwarding

- Domain: Gateway
- Pattern family: Communication
- Intent: Map a source signal to the target network correctly
- Weak wording: `The gateway shall send battery status to the cluster.`
- Preferred requirement:

```text
The gateway shall forward signal `BattStat` from CAN chassis message `0x3A0` to CAN body message `0x511` using the same update event semantics as the source signal.
```

- Verification idea: Trace source and destination buses.
- Why it is stronger: Specifies routing semantics rather than just intent.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 062 — Communication: Speed decoding

- Domain: Cluster
- Pattern family: Communication
- Intent: Decode vehicle speed using correct scaling
- Weak wording: `The cluster shall receive speed.`
- Preferred requirement:

```text
The cluster shall decode signal `VehSpd` from CAN message `0x180` as an unsigned value with scale 0.01 km/h per bit.
```

- Verification idea: Inject known payloads and verify displayed speed.
- Why it is stronger: Encoding and units are explicit.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 063 — Communication: VIN in status payload

- Domain: TCU
- Pattern family: Communication
- Intent: Always include vehicle identity in backend status upload
- Weak wording: `The payload shall identify the vehicle.`
- Preferred requirement:

```text
The TCU shall include the VIN field in every backend vehicle-status payload.
```

- Verification idea: Inspect transmitted payloads.
- Why it is stronger: Simple but clear communication content rule.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 064 — Communication: Sensor timestamp reception

- Domain: ADAS
- Pattern family: Communication
- Intent: Use Ethernet timestamps from perception source
- Weak wording: `The ECU shall consider packet timing.`
- Preferred requirement:

```text
The ADAS ECU shall receive object-list timestamps from the perception sensor over Automotive Ethernet and shall use the received timestamps for fusion age calculation.
```

- Verification idea: Inject timestamped packets and inspect age calculation input.
- Why it is stronger: Defines both receipt and semantic use.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 065 — Communication: Diagnostic client addressing

- Domain: Gateway
- Pattern family: Communication
- Intent: Keep session separation across routing
- Weak wording: `The gateway shall keep diagnostic sessions separate.`
- Preferred requirement:

```text
The gateway shall preserve diagnostic client addressing information when routing UDS traffic between the external tester and internal ECU targets.
```

- Verification idea: Run multi-client diagnostic test.
- Why it is stronger: Communication correctness under concurrency.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 066 — Communication: MQTT keepalive

- Domain: TCU
- Pattern family: Communication
- Intent: Maintain broker session using configured keepalive
- Weak wording: `The TCU shall keep the session alive.`
- Preferred requirement:

```text
The TCU shall transmit MQTT keepalive messages at the configured broker keepalive interval while the session is connected.
```

- Verification idea: Observe keepalive timing on an active session.
- Why it is stronger: Protocol rule becomes testable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 067 — Communication: Warning timeout interpretation

- Domain: Cluster
- Pattern family: Communication
- Intent: Default missing warning request to FALSE after timeout
- Weak wording: `The cluster shall know when warning messages stop.`
- Preferred requirement:

```text
If `FCW_Request` is not updated within the configured timeout period, the cluster shall treat the request as FALSE.
```

- Verification idea: Stop signal updates and observe timeout behavior.
- Why it is stronger: Defines timeout semantics at the consumer side.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 068 — Communication: SOME/IP service offer

- Domain: Gateway
- Pattern family: Communication
- Intent: Offer service on Ethernet backbone in operational mode
- Weak wording: `The gateway shall advertise its service.`
- Preferred requirement:

```text
When the vehicle network enters operational mode, the gateway shall offer the configured SOME/IP diagnostic translation service on the Ethernet backbone.
```

- Verification idea: Enter operational mode and inspect service-discovery traffic.
- Why it is stronger: Specific communication behavior in service-oriented architecture.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 069 — Communication: eCall MSD encoding

- Domain: TCU
- Pattern family: Communication
- Intent: Encode emergency data in required format
- Weak wording: `The TCU shall send emergency data correctly.`
- Preferred requirement:

```text
The TCU shall encode the minimum set of emergency data according to the applicable eCall data format specification.
```

- Verification idea: Capture encoded MSD and compare against format rules.
- Why it is stronger: Protocol format requirement driven by standard.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 070 — Communication: Warning signal period

- Domain: ADAS
- Pattern family: Communication
- Intent: Transmit active warning messages at fixed rate
- Weak wording: `The ADAS ECU shall keep sending warnings.`
- Preferred requirement:

```text
While `FCW_Request` is TRUE, the ADAS ECU shall transmit the FCW warning message every 20 ms ±1 ms.
```

- Verification idea: Observe transmit period on the bus.
- Why it is stronger: Combines state condition with interface timing.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 071 — Communication: Unit coding reception

- Domain: Cluster
- Pattern family: Communication
- Intent: Apply market coding updates to displayed values
- Weak wording: `The cluster shall support unit coding.`
- Preferred requirement:

```text
Upon reception of a market coding update, the cluster shall apply the configured distance unit to displayed trip values.
```

- Verification idea: Send coding update and verify display units.
- Why it is stronger: Configuration update behavior is explicit.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 072 — Communication: Checksum-based packet drop

- Domain: Gateway
- Pattern family: Communication
- Intent: Discard corrupted Ethernet diagnostic packets
- Weak wording: `The gateway shall protect packet integrity.`
- Preferred requirement:

```text
The gateway shall discard incoming Ethernet diagnostic packets whose transport checksum validation fails.
```

- Verification idea: Inject invalid-checksum packets and verify discard.
- Why it is stronger: Communication integrity rule with clear pass/fail.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

## 7.17 Fault handling examples

### Example 073 — Fault handling: Modem restart sequence

- Domain: TCU
- Pattern family: Fault handling
- Intent: Recover from modem initialization failure
- Weak wording: `The TCU shall recover from modem errors.`
- Preferred requirement:

```text
If modem initialization fails, the TCU shall perform a modem restart and shall record the restart attempt count.
```

- Verification idea: Force init failure and observe restart plus count update.
- Why it is stronger: Explicit action and observability.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 074 — Fault handling: Lost speed input response

- Domain: Cluster
- Pattern family: Fault handling
- Intent: Switch safely when speed input becomes invalid
- Weak wording: `The cluster shall handle lost speed input.`
- Preferred requirement:

```text
If vehicle speed input becomes invalid, the cluster shall freeze the displayed speed for no longer than 300 ms and shall then switch to substitute indication.
```

- Verification idea: Invalidate input and observe display progression.
- Why it is stronger: Avoids undefined transition behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 075 — Fault handling: Routing table integrity fault

- Domain: Gateway
- Pattern family: Fault handling
- Intent: Enter safe mode on corrupted route table
- Weak wording: `The gateway shall do something safe if routing data is bad.`
- Preferred requirement:

```text
If routing table integrity verification fails at startup, the gateway shall inhibit normal routing and shall enter diagnostic-safe mode.
```

- Verification idea: Corrupt table image and verify safe mode.
- Why it is stronger: Startup fault containment.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 076 — Fault handling: Camera stream loss

- Domain: ADAS
- Pattern family: Fault handling
- Intent: Inhibit LDW when camera frames stop arriving
- Weak wording: `The system shall react to lost camera stream.`
- Preferred requirement:

```text
If camera frame reception is lost for longer than 100 ms, the ADAS ECU shall inhibit lane departure warning output.
```

- Verification idea: Stop frame stream and verify output inhibition.
- Why it is stronger: Specific fault response protects against stale perception.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 077 — Fault handling: Certificate validation error

- Domain: TCU
- Pattern family: Fault handling
- Intent: Terminate session and log cause
- Weak wording: `The TCU shall react to certificate problems.`
- Preferred requirement:

```text
If backend certificate validation fails, the TCU shall terminate the session attempt and shall store the validation error class.
```

- Verification idea: Inject invalid certificate chain and inspect behavior.
- Why it is stronger: Security fault handling with diagnostic visibility.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 078 — Fault handling: Missing warning icon asset

- Domain: Cluster
- Pattern family: Fault handling
- Intent: Fall back to text when icon load fails
- Weak wording: `The cluster shall still show something if the icon is missing.`
- Preferred requirement:

```text
If a warning icon asset fails to load during startup, the cluster shall activate the fallback text-based warning presentation.
```

- Verification idea: Corrupt asset and verify fallback presentation.
- Why it is stronger: Prevents HMI silence on graphics fault.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 079 — Fault handling: Time-sync source loss

- Domain: Gateway
- Pattern family: Fault handling
- Intent: Continue nominal routing but flag invalid time state
- Weak wording: `The gateway shall handle clock issues.`
- Preferred requirement:

```text
If the gateway loses a valid time synchronization source, it shall continue routing nominal traffic and shall flag time-synchronization invalid status.
```

- Verification idea: Remove time source and inspect fault status.
- Why it is stronger: Fault is localized instead of overreacting.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 080 — Fault handling: Radar misalignment fault

- Domain: ADAS
- Pattern family: Fault handling
- Intent: Suppress AEB when radar self-check indicates misalignment
- Weak wording: `The system shall not use bad radar alignment.`
- Preferred requirement:

```text
If radar self-check indicates sensor misalignment, the ADAS ECU shall suppress AEB intervention requests.
```

- Verification idea: Inject misalignment fault and verify suppression.
- Why it is stronger: Fault response is directly tied to hazardous output.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 081 — Fault handling: Diagnostic storage full

- Domain: TCU
- Pattern family: Fault handling
- Intent: Apply overwrite policy while preserving locked records
- Weak wording: `The TCU shall cope with full fault memory.`
- Preferred requirement:

```text
If non-volatile diagnostic storage becomes full, the TCU shall overwrite the oldest non-locked event record and shall preserve all locked legal records.
```

- Verification idea: Fill memory and observe overwrite policy.
- Why it is stronger: Precise and maintainable storage fault behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 082 — Fault handling: Buzzer feedback failure

- Domain: Cluster
- Pattern family: Fault handling
- Intent: Keep visual warning active when buzzer fails
- Weak wording: `The cluster shall still warn if buzzer is broken.`
- Preferred requirement:

```text
If buzzer feedback indicates failure during an active red warning request, the cluster shall log the fault and shall keep the visual warning active.
```

- Verification idea: Inject buzzer failure and verify visual warning persists.
- Why it is stronger: Maintains minimum warning channel.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 083 — Fault handling: Unauthorized remote command

- Domain: Gateway
- Pattern family: Fault handling
- Intent: Reject command and increment event counter
- Weak wording: `The gateway shall reject bad remote commands.`
- Preferred requirement:

```text
If an unauthorized remote command is received from the telematics domain, the gateway shall reject the command and shall increment the security event counter.
```

- Verification idea: Send unauthorized command and inspect reject plus counter.
- Why it is stronger: Good combined containment and observability.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 084 — Fault handling: Localization quality fault

- Domain: ADAS
- Pattern family: Fault handling
- Intent: Disable map-assisted speed adaptation on poor localization
- Weak wording: `The system shall react when localization is poor.`
- Preferred requirement:

```text
If localization quality drops below the minimum threshold required for map-assisted speed adaptation, the ADAS ECU shall disable map-assisted speed adjustments.
```

- Verification idea: Reduce localization quality and verify feature disable.
- Why it is stronger: Fault response is scoped to affected behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

## 7.18 Degradation examples

### Example 085 — Degradation: Camera blocked mode

- Domain: ADAS
- Pattern family: Degradation
- Intent: Provide temporary unavailability instead of invalid warnings
- Weak wording: `The system shall degrade gracefully if the camera is blocked.`
- Preferred requirement:

```text
While camera blockage status is TRUE, the ADAS ECU shall suppress lane departure warning and shall indicate feature temporarily unavailable.
```

- Verification idea: Force blockage and verify suppression plus indication.
- Why it is stronger: Classic graceful degradation example.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 086 — Degradation: Weak coverage queueing

- Domain: TCU
- Pattern family: Degradation
- Intent: Queue non-critical uploads in poor cellular conditions
- Weak wording: `The TCU shall do less when coverage is weak.`
- Preferred requirement:

```text
While cellular signal quality remains below the backend transmission threshold, the TCU shall queue non-critical telemetry for deferred upload.
```

- Verification idea: Simulate weak coverage and inspect queueing behavior.
- Why it is stronger: Maintains service with reduced capability.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 087 — Degradation: Low-voltage dimming mode

- Domain: Cluster
- Pattern family: Degradation
- Intent: Reduce brightness to protect low-power operation
- Weak wording: `The cluster shall save power at low voltage.`
- Preferred requirement:

```text
While vehicle supply voltage is below the low-voltage display threshold, the cluster shall reduce display brightness to the defined low-power level.
```

- Verification idea: Lower supply and verify degraded brightness mode.
- Why it is stronger: Explicit degraded operating mode.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 088 — Degradation: Single-channel failover

- Domain: Gateway
- Pattern family: Degradation
- Intent: Continue service on one Ethernet channel
- Weak wording: `The gateway shall keep working if one channel fails.`
- Preferred requirement:

```text
While one redundant Ethernet channel is unavailable, the gateway shall continue service operation on the remaining channel and shall indicate reduced redundancy.
```

- Verification idea: Disable one channel and verify continued service.
- Why it is stronger: Availability-oriented degraded mode.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 089 — Degradation: Partial object-set operation

- Domain: ADAS
- Pattern family: Degradation
- Intent: Operate FCW with reduced sensor envelope
- Weak wording: `The system shall still work somewhat if long-range radar is unavailable.`
- Preferred requirement:

```text
While radar long-range mode is unavailable, the ADAS ECU shall continue FCW processing using short-range object inputs only within the supported reduced-speed envelope.
```

- Verification idea: Disable long-range mode and verify reduced-scope behavior.
- Why it is stronger: Good example of bounded partial functionality.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 090 — Degradation: Offline command restriction

- Domain: TCU
- Pattern family: Degradation
- Intent: Block remote actuation but keep critical services
- Weak wording: `The TCU shall degrade sensibly if backend is down.`
- Preferred requirement:

```text
While backend connection is unavailable, the TCU shall reject remote actuation commands and shall continue local emergency-call readiness.
```

- Verification idea: Drop backend and verify offline restrictions.
- Why it is stronger: Separates critical from non-critical telematics services.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 091 — Degradation: Temperature display suppression

- Domain: Cluster
- Pattern family: Degradation
- Intent: Suppress only invalid outside-temperature value
- Weak wording: `The cluster shall degrade if ambient temperature input is bad.`
- Preferred requirement:

```text
While ambient temperature input is invalid, the cluster shall suppress outside-temperature numerical display and shall retain all unrelated display functions.
```

- Verification idea: Invalidate temperature input and observe scoped suppression.
- Why it is stronger: Localized degradation avoids collateral behavior loss.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 092 — Degradation: Overload shedding

- Domain: Gateway
- Pattern family: Degradation
- Intent: Defer low-priority infotainment traffic under overload
- Weak wording: `The gateway shall reduce traffic under overload.`
- Preferred requirement:

```text
While network load exceeds the overload threshold, the gateway shall defer transmission of configured low-priority infotainment messages.
```

- Verification idea: Create overload and inspect message shedding.
- Why it is stronger: Explicit overload-management degradation.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 093 — Degradation: Driver-monitoring unavailable mode

- Domain: ADAS
- Pattern family: Degradation
- Intent: Limit lane centering support duration without DMS
- Weak wording: `The system shall be more careful if driver monitoring is unavailable.`
- Preferred requirement:

```text
While driver-monitoring camera status is unavailable, the lane centering function shall limit maximum automated steering support duration to the configured degraded threshold.
```

- Verification idea: Disable monitoring camera and observe limited support time.
- Why it is stronger: Clear degraded safety envelope.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 094 — Degradation: Reduced-accuracy location

- Domain: TCU
- Pattern family: Degradation
- Intent: Mark poor GNSS data as degraded
- Weak wording: `The TCU shall indicate bad location quality.`
- Preferred requirement:

```text
While live GNSS accuracy is worse than the configured limit, the TCU shall mark transmitted location data as reduced accuracy.
```

- Verification idea: Degrade GNSS accuracy and inspect validity flags.
- Why it is stronger: Communicates degraded semantics to backend consumers.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 095 — Degradation: Reduced-animation mode

- Domain: Cluster
- Pattern family: Degradation
- Intent: Lower HMI graphics cost under high load
- Weak wording: `The cluster shall use simpler graphics if busy.`
- Preferred requirement:

```text
While graphics resource load exceeds the configured threshold, the cluster shall switch warning animations to reduced frame mode.
```

- Verification idea: Induce high load and verify animation fallback.
- Why it is stronger: Graceful performance degradation.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 096 — Degradation: Diagnostic-only degraded mode

- Domain: Gateway
- Pattern family: Degradation
- Intent: Keep service access while main routing is inhibited
- Weak wording: `The gateway shall stay diagnosable when degraded.`
- Preferred requirement:

```text
While the main application routing service is inhibited by a recoverable internal fault, the gateway shall keep basic diagnostic access available.
```

- Verification idea: Inject recoverable fault and verify diagnostic-only mode.
- Why it is stronger: Useful field-service degradation requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

## 7.19 Recovery examples

### Example 097 — Recovery: Camera unblocked recovery

- Domain: ADAS
- Pattern family: Recovery
- Intent: Restore LDW after stable recovery from blockage
- Weak wording: `The system shall recover when the camera is okay again.`
- Preferred requirement:

```text
When camera blockage status returns to FALSE for 1 s continuously, the ADAS ECU shall restore lane departure warning availability within 200 ms.
```

- Verification idea: Clear blockage and measure feature recovery timing.
- Why it is stronger: Recovery includes debounce and response time.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 098 — Recovery: Queued telemetry flush

- Domain: TCU
- Pattern family: Recovery
- Intent: Upload stored non-critical data after reconnection
- Weak wording: `The TCU shall send queued data after reconnect.`
- Preferred requirement:

```text
When backend connectivity is re-established, the TCU shall transmit queued telemetry in chronological order.
```

- Verification idea: Reconnect backend and inspect queued uploads.
- Why it is stronger: Recovery rule preserves data order.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 099 — Recovery: Speed display recovery

- Domain: Cluster
- Pattern family: Recovery
- Intent: Restore normal display quickly after valid speed returns
- Weak wording: `The cluster shall show speed again when the signal returns.`
- Preferred requirement:

```text
When valid vehicle speed input resumes after a timeout, the cluster shall restore numerical speed display within 100 ms.
```

- Verification idea: Restore signal and measure display recovery.
- Why it is stronger: Explicit exit from substitute mode.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 100 — Recovery: Redundant link restoration

- Domain: Gateway
- Pattern family: Recovery
- Intent: Return to dual-channel mode after link recovery
- Weak wording: `The gateway shall recover redundancy when possible.`
- Preferred requirement:

```text
When the failed redundant Ethernet channel becomes healthy, the gateway shall restore dual-channel operation within 2 s.
```

- Verification idea: Recover link and verify redundancy restoration.
- Why it is stronger: Clear recovery timing.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 101 — Recovery: Modem restart recovery

- Domain: TCU
- Pattern family: Recovery
- Intent: Resume registration after successful restart
- Weak wording: `The TCU shall continue after modem restart.`
- Preferred requirement:

```text
After a successful modem restart, the TCU shall re-enter network registration state within 5 s.
```

- Verification idea: Force restart and measure registration-state entry.
- Why it is stronger: Useful recovery readiness statement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 102 — Recovery: Localization recovery

- Domain: ADAS
- Pattern family: Recovery
- Intent: Re-enable map-assisted feature after stable good localization
- Weak wording: `The system shall turn map-assisted mode back on when localization is okay.`
- Preferred requirement:

```text
When localization quality returns above the minimum threshold for 500 ms, the ADAS ECU shall re-enable map-assisted speed adaptation.
```

- Verification idea: Restore localization and verify feature return.
- Why it is stronger: Recovery includes hysteresis against oscillation.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 103 — Recovery: Graphics fallback exit

- Domain: Cluster
- Pattern family: Recovery
- Intent: Use icon again on next activation after asset recovery
- Weak wording: `The cluster shall recover from icon faults.`
- Preferred requirement:

```text
When the required warning icon asset becomes available after a prior load failure, the cluster shall replace fallback text presentation with icon presentation at the next warning activation.
```

- Verification idea: Recover asset and verify next activation uses icon.
- Why it is stronger: Keeps transition behavior stable and predictable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 104 — Recovery: Bus-off recovery

- Domain: Gateway
- Pattern family: Recovery
- Intent: Resume channel routing after bus controller recovery
- Weak wording: `The gateway shall continue after bus-off recovery.`
- Preferred requirement:

```text
After CAN channel 2 recovers from bus-off and completes controller restart, the gateway shall resume routing on channel 2 within 500 ms.
```

- Verification idea: Recover channel and measure routing resumption.
- Why it is stronger: Specific communication recovery requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 105 — Recovery: GNSS live position restoration

- Domain: TCU
- Pattern family: Recovery
- Intent: Resume live location reporting when GNSS is valid again
- Weak wording: `The TCU shall use GNSS again after recovery.`
- Preferred requirement:

```text
When live GNSS position validity returns to TRUE, the TCU shall resume reporting live position in the next backend location payload.
```

- Verification idea: Restore GNSS and inspect subsequent payload.
- Why it is stronger: Simple but complete recovery rule.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 106 — Recovery: Warning-path recovery

- Domain: ADAS
- Pattern family: Recovery
- Intent: Resume active warning transmission when cluster path returns
- Weak wording: `The ADAS ECU shall send warnings again after communication recovery.`
- Preferred requirement:

```text
When the cluster communication path returns to available state, the ADAS ECU shall resume transmission of active warning requests in the next scheduled message period.
```

- Verification idea: Restore path and inspect resumed traffic.
- Why it is stronger: Ties recovery to periodic message schedule.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 107 — Recovery: Low-voltage exit

- Domain: Cluster
- Pattern family: Recovery
- Intent: Return to nominal brightness after supply recovery
- Weak wording: `The cluster shall go back to normal after voltage recovers.`
- Preferred requirement:

```text
When supply voltage rises above the low-voltage recovery threshold for 2 s continuously, the cluster shall restore nominal brightness control.
```

- Verification idea: Raise voltage and measure brightness recovery.
- Why it is stronger: Recovery threshold plus dwell time prevents oscillation.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 108 — Recovery: Security lockout expiry

- Domain: Gateway
- Pattern family: Recovery
- Intent: Allow a new authenticated attempt after temporary lockout
- Weak wording: `The gateway shall unlock later.`
- Preferred requirement:

```text
When the security lockout timer expires, the gateway shall permit a new authenticated diagnostic session attempt.
```

- Verification idea: Wait for timer expiry and verify session can be retried.
- Why it is stronger: Defines recovery from temporary protective state.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

## 7.20 Mixed examples

### Example 109 — Mixed: BSD indicator request

- Domain: ADAS
- Pattern family: Mixed
- Intent: Request blind-spot indication when adjacent-zone occupancy persists
- Weak wording: `The system shall tell the driver about blind-spot vehicles.`
- Preferred requirement:

```text
When a valid adjacent-lane object remains within the blind-spot warning zone for the calibrated persistence time, the ADAS ECU shall request the blind-spot indicator.
```

- Verification idea: Replay adjacent-lane scenario and verify indicator request.
- Why it is stronger: Functional plus timing nuance in one strong statement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 110 — Mixed: Wake-on-call handling

- Domain: TCU
- Pattern family: Mixed
- Intent: Wake telematics unit on incoming emergency callback
- Weak wording: `The TCU shall wake up for important calls.`
- Preferred requirement:

```text
When an authenticated emergency callback request is received during sleep mode, the TCU shall wake and enable the emergency voice path within the configured wake-up time budget.
```

- Verification idea: Inject callback while sleeping and measure wake path readiness.
- Why it is stronger: Good multi-condition telematics requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 111 — Mixed: Charge-complete message

- Domain: Cluster
- Pattern family: Mixed
- Intent: Display charge complete popup at end of charging session
- Weak wording: `The cluster shall show charge complete.`
- Preferred requirement:

```text
When charging session state transitions from ACTIVE to COMPLETE, the cluster shall display the charge complete popup for 5 s ±0.5 s.
```

- Verification idea: Simulate end-of-charge transition and measure popup persistence.
- Why it is stronger: Tightly written HMI notification requirement.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 112 — Mixed: DoIP tester access control

- Domain: Gateway
- Pattern family: Mixed
- Intent: Allow DoIP routing only in permitted power mode
- Weak wording: `The gateway shall control DoIP access.`
- Preferred requirement:

```text
While vehicle power mode is OFF, the gateway shall reject external DoIP diagnostic session establishment unless the approved service wake condition is active.
```

- Verification idea: Attempt DoIP access in OFF mode with and without wake condition.
- Why it is stronger: Combines mode condition with security/service rule.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 113 — Mixed: Driver inattentive escalation

- Domain: ADAS
- Pattern family: Mixed
- Intent: Escalate warning if reminder is ignored
- Weak wording: `The system shall escalate if the driver ignores warnings.`
- Preferred requirement:

```text
When driver hands-off reminder remains active for longer than the escalation threshold during lane centering, the ADAS ECU shall request the escalated warning level.
```

- Verification idea: Ignore initial reminder and verify escalated request.
- Why it is stronger: Good escalation pattern.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 114 — Mixed: OTA rollback trigger

- Domain: TCU
- Pattern family: Mixed
- Intent: Rollback after failed post-install health check
- Weak wording: `The TCU shall recover from bad updates.`
- Preferred requirement:

```text
If post-install health check fails after OTA activation, the TCU shall initiate rollback to the previous valid software image.
```

- Verification idea: Inject failed health check and verify rollback start.
- Why it is stronger: Strong fault-handling and recovery combination.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 115 — Mixed: Priority arbitration

- Domain: Cluster
- Pattern family: Mixed
- Intent: Suppress non-critical popup behind critical warning
- Weak wording: `The cluster shall prioritize important warnings.`
- Preferred requirement:

```text
When a red brake warning request is active, the cluster shall suppress display of incoming low-priority infotainment popups.
```

- Verification idea: Inject simultaneous requests and verify arbitration.
- Why it is stronger: Priority becomes concrete and testable.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 116 — Mixed: Signal timeout substitution

- Domain: Gateway
- Pattern family: Mixed
- Intent: Send substitute value when source signal times out
- Weak wording: `The gateway shall handle timed-out source signals.`
- Preferred requirement:

```text
When the source `GearPos` signal exceeds its timeout threshold, the gateway shall transmit the configured substitute value to the consumer network.
```

- Verification idea: Stop source updates and inspect egress substitute value.
- Why it is stronger: Good interface plus fault-handling example.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

### Example 117 — Mixed: AEB chime request

- Domain: ADAS
- Pattern family: Mixed
- Intent: Add acoustic request during escalation phase
- Weak wording: `The system shall ask for a chime when needed.`
- Preferred requirement:

```text
When FCW escalation level becomes HIGH, the ADAS ECU shall request the forward collision acoustic warning.
```

- Verification idea: Drive escalation logic and verify chime request output.
- Why it is stronger: Functional output tied to explicit severity state.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for ADAS integration.

### Example 118 — Mixed: Certificate-expiry warning

- Domain: TCU
- Pattern family: Mixed
- Intent: Raise service-visible warning before backend certificate expires
- Weak wording: `The TCU shall manage certificates proactively.`
- Preferred requirement:

```text
When the active backend certificate remaining validity falls below the configured warning threshold, the TCU shall store a certificate-expiry warning event.
```

- Verification idea: Inject near-expiry certificate and verify event storage.
- Why it is stronger: Security maintenance requirement with diagnostic value.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for TCU integration.

### Example 119 — Mixed: Language update handling

- Domain: Cluster
- Pattern family: Mixed
- Intent: Apply updated language to future text warnings
- Weak wording: `The cluster shall support language changes.`
- Preferred requirement:

```text
When the active HMI language coding is updated, the cluster shall present subsequent warning text using the updated language selection.
```

- Verification idea: Update coding and trigger warning text.
- Why it is stronger: Clear post-configuration behavior.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Cluster integration.

### Example 120 — Mixed: Wake reason storage

- Domain: Gateway
- Pattern family: Mixed
- Intent: Record cause of wake event for service analysis
- Weak wording: `The gateway shall know why it woke up.`
- Preferred requirement:

```text
When the gateway exits sleep mode, it shall store the wake-source category in diagnostic event memory.
```

- Verification idea: Wake from multiple sources and inspect stored category.
- Why it is stronger: Supports serviceability and root-cause analysis.
- Review focus: Confirm trigger, subject, observable response, and any timing or fault assumptions are fully controlled for Gateway integration.

## 7.20 Pattern selection quick guide

| If you need to express... | Prefer pattern |
|---|---|
| event-driven behavior | Functional |
| deadline, period, timeout, or debounce | Timing |
| capacity, latency, accuracy, or resource limit | Performance |
| safe-state or hazard mitigation | Safety |
| DTC, freeze frame, or service readout | Diagnostic |
| signal, message, protocol, or encoding rule | Communication |
| explicit response to detected failure | Fault handling |
| reduced but still useful service | Degradation |
| return from degraded or fault state | Recovery |

## 7.21 Final reminders for automotive authors

- Patterns help, but engineering judgment is still required.
- Numbers should come from analysis, safety, architecture, regulation, or validated calibration assumptions.
- Keep implementation detail out unless it is an intentional constraint.
- Always capture derived requirements explicitly instead of hiding them in design or code.
- Always ask how a tester, integrator, or service engineer will observe the required behavior.
- Always review nominal, fault, degraded, and recovery behavior as a connected set.

---

## Closing note

Strong requirements engineering improves architecture quality, software quality, test coverage, safety confidence, cybersecurity robustness, integration speed, and customer trust. In automotive programs, better requirement text is not paperwork quality alone; it is product quality.
