# 08 — Requirements Engineering Projects, Capstone, and Mastery

This document is a **large-scale automotive requirements engineering workbook** intended for engineers who want to practice complete end-to-end decomposition from stakeholder needs to release evidence.

It covers Sections **35 through 39** in a single integrated training asset and intentionally uses large, repetitive engineering structures so the learner can recognize the chain across many domains.

---

## Table of Contents

- 35.1 Adaptive Cruise Control (ACC)
- 35.2 Automatic Emergency Braking (AEB)
- 35.3 Lane Keeping Assist (LKA)
- 35.4 ADAS Domain Controller (ADC)
- 35.5 Telematics Control Unit (TCU)
- 35.6 eCall System (ECALL)
- 35.7 Over-the-Air Update System (OTA)
- 35.8 Digital Instrument Cluster (CLUSTER)
- 35.9 Vehicle Gateway (GATEWAY)
- 35.10 Zonal Architecture (ZONAL)
- 36 Requirements Engineering Capstone
- 37 Requirements + Functional Safety + Testing Master Chain
- 38 Final Competency Matrix
- 39 Final Learning Outcome

---

## 35. COMPLETE END-TO-END REQUIREMENTS PROJECTS

Each project below follows the same end-to-end chain:

```text
Stakeholder Requirements
→ Vehicle Requirements
→ System Requirements
→ HARA
→ Safety Requirements
→ Architecture
→ Subsystem Requirements
→ Software Requirements
→ Hardware Requirements
→ Interface Requirements
→ Test Requirements
→ Verification
→ Validation
→ Traceability
→ Change Management
→ Release
```

- The examples are educational but realistic enough to support workshop and interview preparation.
- HARA ratings are illustrative and must always be re-evaluated in real programs with OEM method and item boundaries.
- The repeated structure is intentional: it teaches how the same discipline scales across ADAS, telematics, HMI, connectivity, and E/E architecture.

## 35.1 Adaptive Cruise Control (ACC)

### 35.1.1 Project context

- **Domain**: longitudinal ADAS control.
- **Goal**: maintain driver-selected speed and time gap to a lead vehicle.
- **Primary sensing / input context**: front radar, front camera, ego motion signals.
- **Primary actuation / output context**: powertrain torque and brake coordinator.
- **Human-machine interaction**: cluster, chime, steering-wheel switches.
- **Network context**: CAN and Automotive Ethernet.
- **Operational design domain summary**: controlled-access roads and marked roads within defined speed range.

### 35.1.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-ACC-001 | OEM Product / Feature Planning | The vehicle shall provide Adaptive Cruise Control behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-ACC-002 | Safety Office | The ACC function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-ACC-003 | Regulatory / Homologation | The ACC function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-ACC-004 | HMI / Brand | The ACC function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-ACC-005 | Service / After Sales | The ACC function shall expose diagnosable faults for alignment, blockage, timeout, actuator-denied diagnosis. | Enables maintainability |
| SH-ACC-006 | Cybersecurity | The ACC function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-ACC-007 | Manufacturing | The ACC item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-ACC-008 | Validation | The ACC item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.1.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-ACC-001 | The vehicle shall make Adaptive Cruise Control available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-ACC-002 | The vehicle shall communicate Adaptive Cruise Control states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-ACC-003 | The vehicle shall preserve driver authority and safe handback behavior for Adaptive Cruise Control. | Critical for controllability |
| VEH-ACC-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Adaptive Cruise Control. | Supports safety and service |
| VEH-ACC-005 | The vehicle shall support variant and market configuration of Adaptive Cruise Control without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-ACC-006 | The vehicle shall store event and health information relevant to Adaptive Cruise Control according to legal and privacy rules. | Supports field learning |

### 35.1.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-ACC-001 | The system shall process front radar, front camera, ego motion signals using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-ACC-002 | The system shall deliver maintain driver-selected speed and time gap to a lead vehicle while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-ACC-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-ACC-004 | The system shall monitor output-path acknowledgement or feedback from powertrain torque and brake coordinator. | Closed-loop supervision |
| SYS-ACC-005 | The system shall inform cluster, chime, steering-wheel switches about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-ACC-006 | The system shall inhibit activation or transition to degraded mode when fails to decelerate for a slower or cut-in lead vehicle cannot be mitigated safely. | Activation gating |
| SYS-ACC-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for alignment, blockage, timeout, actuator-denied diagnosis. | Serviceability |
| SYS-ACC-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-ACC-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-ACC-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.1.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-ACC-001 | Nominal use within controlled-access roads and marked roads within defined speed range | fails to decelerate for a slower or cut-in lead vehicle | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-ACC-002 | Nominal use within controlled-access roads and marked roads within defined speed range | accelerates or maintains speed when braking is needed | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-ACC-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-ACC-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-ACC-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL C |

### 35.1.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-ACC-001 | Prevent hazardous loss of intended Adaptive Cruise Control support or service when it is required. | ASIL C |
| SG-ACC-002 | Prevent hazardous false or unintended behavior related to Adaptive Cruise Control. | ASIL C |
| SG-ACC-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Adaptive Cruise Control. | ASIL C |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-ACC-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Adaptive Cruise Control according to the safety concept. | SG-ACC-003 |
| FSR-ACC-002 | The item shall monitor acknowledgement or feedback on the powertrain torque and brake coordinator path where relevant and transition to safe state on loss of confidence. | SG-ACC-001 |
| FSR-ACC-003 | The item shall bound or suppress accelerates or maintains speed when braking is needed using confidence, plausibility, and arbitration checks. | SG-ACC-002 |
| FSR-ACC-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via cluster, chime, steering-wheel switches. | SG-ACC-001 |
| FSR-ACC-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-ACC-003 |

### 35.1.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests front radar, front camera, ego motion signals, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to maintain driver-selected speed and time gap to a lead vehicle. |
| Output / actuation layer | Routes requests or actions through powertrain torque and brake coordinator with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through cluster, chime, steering-wheel switches. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over CAN and Automotive Ethernet. |

### 35.1.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-ACC-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-ACC-002 | Core logic subsystem shall implement the behavior to maintain driver-selected speed and time gap to a lead vehicle. | Feature application |
| SUB-ACC-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Adaptive Cruise Control. | Application state machine |
| SUB-ACC-004 | Diagnostics subsystem shall detect and classify faults related to alignment, blockage, timeout, actuator-denied diagnosis. | Diagnostic manager |
| SUB-ACC-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-ACC-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-ACC-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-ACC-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.1.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-ACC-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-ACC-002 | The software shall implement the state machine for Adaptive Cruise Control with explicit transitions and inhibition reasons. | Behavior control |
| SWR-ACC-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-ACC-004 | The software shall manage degraded behavior such that the system will deactivate or degrade to safe speed-control / warning behavior. | Safe degradation |
| SWR-ACC-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-ACC-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-ACC-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-ACC-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-ACC-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-ACC-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.1.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-ACC-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-ACC-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-ACC-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-ACC-004 | The hardware shall support reliable interfacing to front radar, front camera, ego motion signals and powertrain torque and brake coordinator as applicable. | I/O integrity |
| HWR-ACC-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-ACC-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.1.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-ACC-001 | Input sensor/status interface | CAN and Automotive Ethernet | Define units, timestamps, validity, freshness, and failure behavior for front radar, front camera, ego motion signals. |
| IF-ACC-002 | Vehicle-state interface | CAN and Automotive Ethernet | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-ACC-003 | Output/actuation interface | CAN and Automotive Ethernet | Define request format, acknowledgement, counters, and fail-safe behavior for powertrain torque and brake coordinator. |
| IF-ACC-004 | HMI interface | CAN and Automotive Ethernet | Define state, warning, message IDs, and update timing for cluster, chime, steering-wheel switches. |
| IF-ACC-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-ACC-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-ACC-007 | Logging / telemetry interface | CAN and Automotive Ethernet | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-ACC-008 | Update / security interface | CAN and Automotive Ethernet | Define software identity, package trust, and protected service access as applicable. |

### 35.1.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-ACC-001 | Requirement-based SIL tests shall verify nominal behavior for Adaptive Cruise Control. | Functional verification |
| TST-ACC-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-ACC-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-ACC-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-ACC-005 | Environmental and power-condition tests shall verify that Adaptive Cruise Control responds safely under disturbances. | Environmental confidence |
| TST-ACC-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-ACC-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-ACC-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-ACC-009 | Vehicle tests shall verify customer-visible behavior and integration with cluster, chime, steering-wheel switches. | Vehicle-level verification |
| TST-ACC-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.1.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.1.14 Validation

- Validate that Adaptive Cruise Control provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through cluster, chime, steering-wheel switches is correct and timely.
- Validate that degraded behavior (deactivate or degrade to safe speed-control / warning behavior) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.1.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-ACC-001 → VEH-ACC-001 |
| Vehicle requirement | System requirement | VEH-ACC-003 → SYS-ACC-004 / SYS-ACC-006 |
| Hazard | Safety goal / FSR | HE-ACC-001 → SG-ACC-001 → FSR-ACC-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-ACC-003 → SUB-ACC-001 → SWR-ACC-001 / HWR-ACC-004 |
| Requirement | Test | SYS-ACC-007 → TST-ACC-006 |
| Change request | Regression scope | CR-ACC-X → impacted IF/SWR/TST links |

### 35.1.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.1.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Adaptive Cruise Control is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.2 Automatic Emergency Braking (AEB)

### 35.2.1 Project context

- **Domain**: collision mitigation.
- **Goal**: warn and autonomously brake for imminent frontal collisions.
- **Primary sensing / input context**: front radar, front camera, ego motion and friction estimate.
- **Primary actuation / output context**: brake system with ESC/ABS coordination.
- **Human-machine interaction**: cluster, chime, warning indicators.
- **Network context**: CAN and Automotive Ethernet.
- **Operational design domain summary**: vehicle, pedestrian, and cyclist scenarios inside approved operating envelope.

### 35.2.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-AEB-001 | OEM Product / Feature Planning | The vehicle shall provide Automatic Emergency Braking behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-AEB-002 | Safety Office | The AEB function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-AEB-003 | Regulatory / Homologation | The AEB function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-AEB-004 | HMI / Brand | The AEB function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-AEB-005 | Service / After Sales | The AEB function shall expose diagnosable faults for object confidence, brake-path acknowledgement, sensor blockage, false-trigger investigation. | Enables maintainability |
| SH-AEB-006 | Cybersecurity | The AEB function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-AEB-007 | Manufacturing | The AEB item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-AEB-008 | Validation | The AEB item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.2.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-AEB-001 | The vehicle shall make Automatic Emergency Braking available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-AEB-002 | The vehicle shall communicate Automatic Emergency Braking states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-AEB-003 | The vehicle shall preserve driver authority and safe handback behavior for Automatic Emergency Braking. | Critical for controllability |
| VEH-AEB-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Automatic Emergency Braking. | Supports safety and service |
| VEH-AEB-005 | The vehicle shall support variant and market configuration of Automatic Emergency Braking without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-AEB-006 | The vehicle shall store event and health information relevant to Automatic Emergency Braking according to legal and privacy rules. | Supports field learning |

### 35.2.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-AEB-001 | The system shall process front radar, front camera, ego motion and friction estimate using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-AEB-002 | The system shall deliver warn and autonomously brake for imminent frontal collisions while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-AEB-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-AEB-004 | The system shall monitor output-path acknowledgement or feedback from brake system with ESC/ABS coordination. | Closed-loop supervision |
| SYS-AEB-005 | The system shall inform cluster, chime, warning indicators about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-AEB-006 | The system shall inhibit activation or transition to degraded mode when fails to trigger braking for an imminent frontal collision cannot be mitigated safely. | Activation gating |
| SYS-AEB-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for object confidence, brake-path acknowledgement, sensor blockage, false-trigger investigation. | Serviceability |
| SYS-AEB-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-AEB-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-AEB-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.2.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-AEB-001 | Nominal use within vehicle, pedestrian, and cyclist scenarios inside approved operating envelope | fails to trigger braking for an imminent frontal collision | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-AEB-002 | Nominal use within vehicle, pedestrian, and cyclist scenarios inside approved operating envelope | triggers hard braking with no valid obstacle | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL D |
| HE-AEB-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-AEB-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-AEB-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL D |

### 35.2.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-AEB-001 | Prevent hazardous loss of intended Automatic Emergency Braking support or service when it is required. | ASIL C |
| SG-AEB-002 | Prevent hazardous false or unintended behavior related to Automatic Emergency Braking. | ASIL D |
| SG-AEB-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Automatic Emergency Braking. | ASIL D |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-AEB-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Automatic Emergency Braking according to the safety concept. | SG-AEB-003 |
| FSR-AEB-002 | The item shall monitor acknowledgement or feedback on the brake system with ESC/ABS coordination path where relevant and transition to safe state on loss of confidence. | SG-AEB-001 |
| FSR-AEB-003 | The item shall bound or suppress triggers hard braking with no valid obstacle using confidence, plausibility, and arbitration checks. | SG-AEB-002 |
| FSR-AEB-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via cluster, chime, warning indicators. | SG-AEB-001 |
| FSR-AEB-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-AEB-003 |

### 35.2.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests front radar, front camera, ego motion and friction estimate, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to warn and autonomously brake for imminent frontal collisions. |
| Output / actuation layer | Routes requests or actions through brake system with ESC/ABS coordination with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through cluster, chime, warning indicators. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over CAN and Automotive Ethernet. |

### 35.2.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-AEB-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-AEB-002 | Core logic subsystem shall implement the behavior to warn and autonomously brake for imminent frontal collisions. | Feature application |
| SUB-AEB-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Automatic Emergency Braking. | Application state machine |
| SUB-AEB-004 | Diagnostics subsystem shall detect and classify faults related to object confidence, brake-path acknowledgement, sensor blockage, false-trigger investigation. | Diagnostic manager |
| SUB-AEB-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-AEB-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-AEB-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-AEB-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.2.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-AEB-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-AEB-002 | The software shall implement the state machine for Automatic Emergency Braking with explicit transitions and inhibition reasons. | Behavior control |
| SWR-AEB-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-AEB-004 | The software shall manage degraded behavior such that the system will inhibit braking or degrade to warning-only mode when confidence is insufficient. | Safe degradation |
| SWR-AEB-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-AEB-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-AEB-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-AEB-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-AEB-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-AEB-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.2.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-AEB-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-AEB-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-AEB-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-AEB-004 | The hardware shall support reliable interfacing to front radar, front camera, ego motion and friction estimate and brake system with ESC/ABS coordination as applicable. | I/O integrity |
| HWR-AEB-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-AEB-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.2.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-AEB-001 | Input sensor/status interface | CAN and Automotive Ethernet | Define units, timestamps, validity, freshness, and failure behavior for front radar, front camera, ego motion and friction estimate. |
| IF-AEB-002 | Vehicle-state interface | CAN and Automotive Ethernet | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-AEB-003 | Output/actuation interface | CAN and Automotive Ethernet | Define request format, acknowledgement, counters, and fail-safe behavior for brake system with ESC/ABS coordination. |
| IF-AEB-004 | HMI interface | CAN and Automotive Ethernet | Define state, warning, message IDs, and update timing for cluster, chime, warning indicators. |
| IF-AEB-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-AEB-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-AEB-007 | Logging / telemetry interface | CAN and Automotive Ethernet | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-AEB-008 | Update / security interface | CAN and Automotive Ethernet | Define software identity, package trust, and protected service access as applicable. |

### 35.2.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-AEB-001 | Requirement-based SIL tests shall verify nominal behavior for Automatic Emergency Braking. | Functional verification |
| TST-AEB-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-AEB-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-AEB-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-AEB-005 | Environmental and power-condition tests shall verify that Automatic Emergency Braking responds safely under disturbances. | Environmental confidence |
| TST-AEB-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-AEB-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-AEB-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-AEB-009 | Vehicle tests shall verify customer-visible behavior and integration with cluster, chime, warning indicators. | Vehicle-level verification |
| TST-AEB-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.2.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.2.14 Validation

- Validate that Automatic Emergency Braking provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through cluster, chime, warning indicators is correct and timely.
- Validate that degraded behavior (inhibit braking or degrade to warning-only mode when confidence is insufficient) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.2.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-AEB-001 → VEH-AEB-001 |
| Vehicle requirement | System requirement | VEH-AEB-003 → SYS-AEB-004 / SYS-AEB-006 |
| Hazard | Safety goal / FSR | HE-AEB-001 → SG-AEB-001 → FSR-AEB-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-AEB-003 → SUB-AEB-001 → SWR-AEB-001 / HWR-AEB-004 |
| Requirement | Test | SYS-AEB-007 → TST-AEB-006 |
| Change request | Regression scope | CR-AEB-X → impacted IF/SWR/TST links |

### 35.2.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.2.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Automatic Emergency Braking is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.3 Lane Keeping Assist (LKA)

### 35.3.1 Project context

- **Domain**: lateral ADAS control.
- **Goal**: apply corrective steering support to keep the vehicle in lane.
- **Primary sensing / input context**: front camera lane model, steering angle, yaw rate, wheel speeds.
- **Primary actuation / output context**: electric power steering.
- **Human-machine interaction**: cluster status icon, limitation message, warning tone.
- **Network context**: CAN and Automotive Ethernet.
- **Operational design domain summary**: roads with detectable lane boundaries inside defined speed and curvature limits.

### 35.3.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-LKA-001 | OEM Product / Feature Planning | The vehicle shall provide Lane Keeping Assist behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-LKA-002 | Safety Office | The LKA function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-LKA-003 | Regulatory / Homologation | The LKA function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-LKA-004 | HMI / Brand | The LKA function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-LKA-005 | Service / After Sales | The LKA function shall expose diagnosable faults for camera alignment, lane confidence, steering feedback, torque monitoring. | Enables maintainability |
| SH-LKA-006 | Cybersecurity | The LKA function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-LKA-007 | Manufacturing | The LKA item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-LKA-008 | Validation | The LKA item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.3.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-LKA-001 | The vehicle shall make Lane Keeping Assist available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-LKA-002 | The vehicle shall communicate Lane Keeping Assist states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-LKA-003 | The vehicle shall preserve driver authority and safe handback behavior for Lane Keeping Assist. | Critical for controllability |
| VEH-LKA-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Lane Keeping Assist. | Supports safety and service |
| VEH-LKA-005 | The vehicle shall support variant and market configuration of Lane Keeping Assist without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-LKA-006 | The vehicle shall store event and health information relevant to Lane Keeping Assist according to legal and privacy rules. | Supports field learning |

### 35.3.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-LKA-001 | The system shall process front camera lane model, steering angle, yaw rate, wheel speeds using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-LKA-002 | The system shall deliver apply corrective steering support to keep the vehicle in lane while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-LKA-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-LKA-004 | The system shall monitor output-path acknowledgement or feedback from electric power steering. | Closed-loop supervision |
| SYS-LKA-005 | The system shall inform cluster status icon, limitation message, warning tone about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-LKA-006 | The system shall inhibit activation or transition to degraded mode when fails to provide corrective support during unintended lane departure cannot be mitigated safely. | Activation gating |
| SYS-LKA-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for camera alignment, lane confidence, steering feedback, torque monitoring. | Serviceability |
| SYS-LKA-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-LKA-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-LKA-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.3.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-LKA-001 | Nominal use within roads with detectable lane boundaries inside defined speed and curvature limits | fails to provide corrective support during unintended lane departure | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-LKA-002 | Nominal use within roads with detectable lane boundaries inside defined speed and curvature limits | applies unintended steering torque | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-LKA-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-LKA-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-LKA-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL C |

### 35.3.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-LKA-001 | Prevent hazardous loss of intended Lane Keeping Assist support or service when it is required. | ASIL C |
| SG-LKA-002 | Prevent hazardous false or unintended behavior related to Lane Keeping Assist. | ASIL C |
| SG-LKA-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Lane Keeping Assist. | ASIL C |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-LKA-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Lane Keeping Assist according to the safety concept. | SG-LKA-003 |
| FSR-LKA-002 | The item shall monitor acknowledgement or feedback on the electric power steering path where relevant and transition to safe state on loss of confidence. | SG-LKA-001 |
| FSR-LKA-003 | The item shall bound or suppress applies unintended steering torque using confidence, plausibility, and arbitration checks. | SG-LKA-002 |
| FSR-LKA-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via cluster status icon, limitation message, warning tone. | SG-LKA-001 |
| FSR-LKA-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-LKA-003 |

### 35.3.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests front camera lane model, steering angle, yaw rate, wheel speeds, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to apply corrective steering support to keep the vehicle in lane. |
| Output / actuation layer | Routes requests or actions through electric power steering with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through cluster status icon, limitation message, warning tone. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over CAN and Automotive Ethernet. |

### 35.3.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-LKA-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-LKA-002 | Core logic subsystem shall implement the behavior to apply corrective steering support to keep the vehicle in lane. | Feature application |
| SUB-LKA-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Lane Keeping Assist. | Application state machine |
| SUB-LKA-004 | Diagnostics subsystem shall detect and classify faults related to camera alignment, lane confidence, steering feedback, torque monitoring. | Diagnostic manager |
| SUB-LKA-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-LKA-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-LKA-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-LKA-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.3.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-LKA-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-LKA-002 | The software shall implement the state machine for Lane Keeping Assist with explicit transitions and inhibition reasons. | Behavior control |
| SWR-LKA-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-LKA-004 | The software shall manage degraded behavior such that the system will cancel torque and inform the driver when lane confidence or EPS health is insufficient. | Safe degradation |
| SWR-LKA-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-LKA-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-LKA-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-LKA-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-LKA-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-LKA-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.3.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-LKA-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-LKA-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-LKA-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-LKA-004 | The hardware shall support reliable interfacing to front camera lane model, steering angle, yaw rate, wheel speeds and electric power steering as applicable. | I/O integrity |
| HWR-LKA-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-LKA-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.3.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-LKA-001 | Input sensor/status interface | CAN and Automotive Ethernet | Define units, timestamps, validity, freshness, and failure behavior for front camera lane model, steering angle, yaw rate, wheel speeds. |
| IF-LKA-002 | Vehicle-state interface | CAN and Automotive Ethernet | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-LKA-003 | Output/actuation interface | CAN and Automotive Ethernet | Define request format, acknowledgement, counters, and fail-safe behavior for electric power steering. |
| IF-LKA-004 | HMI interface | CAN and Automotive Ethernet | Define state, warning, message IDs, and update timing for cluster status icon, limitation message, warning tone. |
| IF-LKA-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-LKA-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-LKA-007 | Logging / telemetry interface | CAN and Automotive Ethernet | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-LKA-008 | Update / security interface | CAN and Automotive Ethernet | Define software identity, package trust, and protected service access as applicable. |

### 35.3.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-LKA-001 | Requirement-based SIL tests shall verify nominal behavior for Lane Keeping Assist. | Functional verification |
| TST-LKA-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-LKA-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-LKA-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-LKA-005 | Environmental and power-condition tests shall verify that Lane Keeping Assist responds safely under disturbances. | Environmental confidence |
| TST-LKA-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-LKA-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-LKA-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-LKA-009 | Vehicle tests shall verify customer-visible behavior and integration with cluster status icon, limitation message, warning tone. | Vehicle-level verification |
| TST-LKA-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.3.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.3.14 Validation

- Validate that Lane Keeping Assist provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through cluster status icon, limitation message, warning tone is correct and timely.
- Validate that degraded behavior (cancel torque and inform the driver when lane confidence or EPS health is insufficient) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.3.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-LKA-001 → VEH-LKA-001 |
| Vehicle requirement | System requirement | VEH-LKA-003 → SYS-LKA-004 / SYS-LKA-006 |
| Hazard | Safety goal / FSR | HE-LKA-001 → SG-LKA-001 → FSR-LKA-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-LKA-003 → SUB-LKA-001 → SWR-LKA-001 / HWR-LKA-004 |
| Requirement | Test | SYS-LKA-007 → TST-LKA-006 |
| Change request | Regression scope | CR-LKA-X → impacted IF/SWR/TST links |

### 35.3.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.3.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Lane Keeping Assist is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.4 ADAS Domain Controller (ADC)

### 35.4.1 Project context

- **Domain**: centralized ADAS compute platform.
- **Goal**: host multiple ADAS applications with shared services and isolation.
- **Primary sensing / input context**: multiple cameras, radars, chassis signals, optional lidar.
- **Primary actuation / output context**: hosted feature outputs toward braking, steering, and HMI paths.
- **Human-machine interaction**: domain-level status propagated to cluster and service tools.
- **Network context**: TSN Ethernet, CAN, DoIP.
- **Operational design domain summary**: vehicle-specific ADAS operating domains defined by hosted functions.

### 35.4.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-ADC-001 | OEM Product / Feature Planning | The vehicle shall provide ADAS Domain Controller behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-ADC-002 | Safety Office | The ADC function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-ADC-003 | Regulatory / Homologation | The ADC function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-ADC-004 | HMI / Brand | The ADC function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-ADC-005 | Service / After Sales | The ADC function shall expose diagnosable faults for platform telemetry, partition health, storage/update diagnosis. | Enables maintainability |
| SH-ADC-006 | Cybersecurity | The ADC function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-ADC-007 | Manufacturing | The ADC item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-ADC-008 | Validation | The ADC item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.4.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-ADC-001 | The vehicle shall make ADAS Domain Controller available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-ADC-002 | The vehicle shall communicate ADAS Domain Controller states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-ADC-003 | The vehicle shall preserve driver authority and safe handback behavior for ADAS Domain Controller. | Critical for controllability |
| VEH-ADC-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for ADAS Domain Controller. | Supports safety and service |
| VEH-ADC-005 | The vehicle shall support variant and market configuration of ADAS Domain Controller without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-ADC-006 | The vehicle shall store event and health information relevant to ADAS Domain Controller according to legal and privacy rules. | Supports field learning |

### 35.4.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-ADC-001 | The system shall process multiple cameras, radars, chassis signals, optional lidar using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-ADC-002 | The system shall deliver host multiple ADAS applications with shared services and isolation while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-ADC-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-ADC-004 | The system shall monitor output-path acknowledgement or feedback from hosted feature outputs toward braking, steering, and HMI paths. | Closed-loop supervision |
| SYS-ADC-005 | The system shall inform domain-level status propagated to cluster and service tools about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-ADC-006 | The system shall inhibit activation or transition to degraded mode when platform overload or partition interference delays safety-critical functions cannot be mitigated safely. | Activation gating |
| SYS-ADC-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for platform telemetry, partition health, storage/update diagnosis. | Serviceability |
| SYS-ADC-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-ADC-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-ADC-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.4.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-ADC-001 | Nominal use within vehicle-specific ADAS operating domains defined by hosted functions | platform overload or partition interference delays safety-critical functions | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-ADC-002 | Nominal use within vehicle-specific ADAS operating domains defined by hosted functions | corrupted or unauthorized software executes on the platform | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL D |
| HE-ADC-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-ADC-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-ADC-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL D |

### 35.4.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-ADC-001 | Prevent hazardous loss of intended ADAS Domain Controller support or service when it is required. | ASIL C |
| SG-ADC-002 | Prevent hazardous false or unintended behavior related to ADAS Domain Controller. | ASIL D |
| SG-ADC-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for ADAS Domain Controller. | ASIL D |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-ADC-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade ADAS Domain Controller according to the safety concept. | SG-ADC-003 |
| FSR-ADC-002 | The item shall monitor acknowledgement or feedback on the hosted feature outputs toward braking, steering, and HMI paths path where relevant and transition to safe state on loss of confidence. | SG-ADC-001 |
| FSR-ADC-003 | The item shall bound or suppress corrupted or unauthorized software executes on the platform using confidence, plausibility, and arbitration checks. | SG-ADC-002 |
| FSR-ADC-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via domain-level status propagated to cluster and service tools. | SG-ADC-001 |
| FSR-ADC-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-ADC-003 |

### 35.4.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests multiple cameras, radars, chassis signals, optional lidar, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to host multiple ADAS applications with shared services and isolation. |
| Output / actuation layer | Routes requests or actions through hosted feature outputs toward braking, steering, and HMI paths with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through domain-level status propagated to cluster and service tools. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over TSN Ethernet, CAN, DoIP. |

### 35.4.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-ADC-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-ADC-002 | Core logic subsystem shall implement the behavior to host multiple ADAS applications with shared services and isolation. | Feature application |
| SUB-ADC-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for ADAS Domain Controller. | Application state machine |
| SUB-ADC-004 | Diagnostics subsystem shall detect and classify faults related to platform telemetry, partition health, storage/update diagnosis. | Diagnostic manager |
| SUB-ADC-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-ADC-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-ADC-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-ADC-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.4.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-ADC-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-ADC-002 | The software shall implement the state machine for ADAS Domain Controller with explicit transitions and inhibition reasons. | Behavior control |
| SWR-ADC-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-ADC-004 | The software shall manage degraded behavior such that the system will degrade hosted features by priority and maintain safe partition isolation. | Safe degradation |
| SWR-ADC-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-ADC-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-ADC-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-ADC-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-ADC-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-ADC-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.4.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-ADC-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-ADC-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-ADC-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-ADC-004 | The hardware shall support reliable interfacing to multiple cameras, radars, chassis signals, optional lidar and hosted feature outputs toward braking, steering, and HMI paths as applicable. | I/O integrity |
| HWR-ADC-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-ADC-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.4.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-ADC-001 | Input sensor/status interface | TSN Ethernet, CAN, DoIP | Define units, timestamps, validity, freshness, and failure behavior for multiple cameras, radars, chassis signals, optional lidar. |
| IF-ADC-002 | Vehicle-state interface | TSN Ethernet, CAN, DoIP | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-ADC-003 | Output/actuation interface | TSN Ethernet, CAN, DoIP | Define request format, acknowledgement, counters, and fail-safe behavior for hosted feature outputs toward braking, steering, and HMI paths. |
| IF-ADC-004 | HMI interface | TSN Ethernet, CAN, DoIP | Define state, warning, message IDs, and update timing for domain-level status propagated to cluster and service tools. |
| IF-ADC-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-ADC-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-ADC-007 | Logging / telemetry interface | TSN Ethernet, CAN, DoIP | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-ADC-008 | Update / security interface | TSN Ethernet, CAN, DoIP | Define software identity, package trust, and protected service access as applicable. |

### 35.4.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-ADC-001 | Requirement-based SIL tests shall verify nominal behavior for ADAS Domain Controller. | Functional verification |
| TST-ADC-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-ADC-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-ADC-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-ADC-005 | Environmental and power-condition tests shall verify that ADAS Domain Controller responds safely under disturbances. | Environmental confidence |
| TST-ADC-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-ADC-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-ADC-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-ADC-009 | Vehicle tests shall verify customer-visible behavior and integration with domain-level status propagated to cluster and service tools. | Vehicle-level verification |
| TST-ADC-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.4.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.4.14 Validation

- Validate that ADAS Domain Controller provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through domain-level status propagated to cluster and service tools is correct and timely.
- Validate that degraded behavior (degrade hosted features by priority and maintain safe partition isolation) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.4.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-ADC-001 → VEH-ADC-001 |
| Vehicle requirement | System requirement | VEH-ADC-003 → SYS-ADC-004 / SYS-ADC-006 |
| Hazard | Safety goal / FSR | HE-ADC-001 → SG-ADC-001 → FSR-ADC-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-ADC-003 → SUB-ADC-001 → SWR-ADC-001 / HWR-ADC-004 |
| Requirement | Test | SYS-ADC-007 → TST-ADC-006 |
| Change request | Regression scope | CR-ADC-X → impacted IF/SWR/TST links |

### 35.4.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.4.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- ADAS Domain Controller is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.5 Telematics Control Unit (TCU)

### 35.5.1 Project context

- **Domain**: connectivity and remote services.
- **Goal**: connect the vehicle securely to backend, diagnostics, and update services.
- **Primary sensing / input context**: modem state, GNSS, vehicle power state, gateway data.
- **Primary actuation / output context**: remote session permissions, wake control, data transfer channels.
- **Human-machine interaction**: connected-service status and limited alerts.
- **Network context**: cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP.
- **Operational design domain summary**: parked and driving connectivity use cases subject to policy and consent.

### 35.5.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-TCU-001 | OEM Product / Feature Planning | The vehicle shall provide Telematics Control Unit behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-TCU-002 | Safety Office | The TCU function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-TCU-003 | Regulatory / Homologation | The TCU function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-TCU-004 | HMI / Brand | The TCU function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-TCU-005 | Service / After Sales | The TCU function shall expose diagnosable faults for modem, certificate, wakeup, provisioning, and bus-load diagnosis. | Enables maintainability |
| SH-TCU-006 | Cybersecurity | The TCU function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-TCU-007 | Manufacturing | The TCU item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-TCU-008 | Validation | The TCU item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.5.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-TCU-001 | The vehicle shall make Telematics Control Unit available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-TCU-002 | The vehicle shall communicate Telematics Control Unit states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-TCU-003 | The vehicle shall preserve driver authority and safe handback behavior for Telematics Control Unit. | Critical for controllability |
| VEH-TCU-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Telematics Control Unit. | Supports safety and service |
| VEH-TCU-005 | The vehicle shall support variant and market configuration of Telematics Control Unit without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-TCU-006 | The vehicle shall store event and health information relevant to Telematics Control Unit according to legal and privacy rules. | Supports field learning |

### 35.5.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-TCU-001 | The system shall process modem state, GNSS, vehicle power state, gateway data using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-TCU-002 | The system shall deliver connect the vehicle securely to backend, diagnostics, and update services while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-TCU-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-TCU-004 | The system shall monitor output-path acknowledgement or feedback from remote session permissions, wake control, data transfer channels. | Closed-loop supervision |
| SYS-TCU-005 | The system shall inform connected-service status and limited alerts about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-TCU-006 | The system shall inhibit activation or transition to degraded mode when forwards unsafe or unauthorized remote traffic into the vehicle cannot be mitigated safely. | Activation gating |
| SYS-TCU-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for modem, certificate, wakeup, provisioning, and bus-load diagnosis. | Serviceability |
| SYS-TCU-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-TCU-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-TCU-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.5.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-TCU-001 | Nominal use within parked and driving connectivity use cases subject to policy and consent | forwards unsafe or unauthorized remote traffic into the vehicle | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-TCU-002 | Nominal use within parked and driving connectivity use cases subject to policy and consent | causes excessive wakeups and battery drain | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-TCU-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-TCU-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-TCU-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL C |

### 35.5.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-TCU-001 | Prevent hazardous loss of intended Telematics Control Unit support or service when it is required. | ASIL C |
| SG-TCU-002 | Prevent hazardous false or unintended behavior related to Telematics Control Unit. | ASIL C |
| SG-TCU-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Telematics Control Unit. | ASIL C |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-TCU-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Telematics Control Unit according to the safety concept. | SG-TCU-003 |
| FSR-TCU-002 | The item shall monitor acknowledgement or feedback on the remote session permissions, wake control, data transfer channels path where relevant and transition to safe state on loss of confidence. | SG-TCU-001 |
| FSR-TCU-003 | The item shall bound or suppress causes excessive wakeups and battery drain using confidence, plausibility, and arbitration checks. | SG-TCU-002 |
| FSR-TCU-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via connected-service status and limited alerts. | SG-TCU-001 |
| FSR-TCU-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-TCU-003 |

### 35.5.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests modem state, GNSS, vehicle power state, gateway data, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to connect the vehicle securely to backend, diagnostics, and update services. |
| Output / actuation layer | Routes requests or actions through remote session permissions, wake control, data transfer channels with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through connected-service status and limited alerts. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP. |

### 35.5.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-TCU-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-TCU-002 | Core logic subsystem shall implement the behavior to connect the vehicle securely to backend, diagnostics, and update services. | Feature application |
| SUB-TCU-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Telematics Control Unit. | Application state machine |
| SUB-TCU-004 | Diagnostics subsystem shall detect and classify faults related to modem, certificate, wakeup, provisioning, and bus-load diagnosis. | Diagnostic manager |
| SUB-TCU-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-TCU-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-TCU-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-TCU-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.5.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-TCU-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-TCU-002 | The software shall implement the state machine for Telematics Control Unit with explicit transitions and inhibition reasons. | Behavior control |
| SWR-TCU-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-TCU-004 | The software shall manage degraded behavior such that the system will block remote actions, back off wakeups, and preserve safe vehicle state. | Safe degradation |
| SWR-TCU-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-TCU-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-TCU-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-TCU-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-TCU-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-TCU-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.5.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-TCU-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-TCU-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-TCU-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-TCU-004 | The hardware shall support reliable interfacing to modem state, GNSS, vehicle power state, gateway data and remote session permissions, wake control, data transfer channels as applicable. | I/O integrity |
| HWR-TCU-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-TCU-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.5.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-TCU-001 | Input sensor/status interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Define units, timestamps, validity, freshness, and failure behavior for modem state, GNSS, vehicle power state, gateway data. |
| IF-TCU-002 | Vehicle-state interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-TCU-003 | Output/actuation interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Define request format, acknowledgement, counters, and fail-safe behavior for remote session permissions, wake control, data transfer channels. |
| IF-TCU-004 | HMI interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Define state, warning, message IDs, and update timing for connected-service status and limited alerts. |
| IF-TCU-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-TCU-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-TCU-007 | Logging / telemetry interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-TCU-008 | Update / security interface | cellular, Wi-Fi/Bluetooth where applicable, CAN, Ethernet, DoIP | Define software identity, package trust, and protected service access as applicable. |

### 35.5.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-TCU-001 | Requirement-based SIL tests shall verify nominal behavior for Telematics Control Unit. | Functional verification |
| TST-TCU-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-TCU-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-TCU-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-TCU-005 | Environmental and power-condition tests shall verify that Telematics Control Unit responds safely under disturbances. | Environmental confidence |
| TST-TCU-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-TCU-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-TCU-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-TCU-009 | Vehicle tests shall verify customer-visible behavior and integration with connected-service status and limited alerts. | Vehicle-level verification |
| TST-TCU-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.5.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.5.14 Validation

- Validate that Telematics Control Unit provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through connected-service status and limited alerts is correct and timely.
- Validate that degraded behavior (block remote actions, back off wakeups, and preserve safe vehicle state) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.5.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-TCU-001 → VEH-TCU-001 |
| Vehicle requirement | System requirement | VEH-TCU-003 → SYS-TCU-004 / SYS-TCU-006 |
| Hazard | Safety goal / FSR | HE-TCU-001 → SG-TCU-001 → FSR-TCU-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-TCU-003 → SUB-TCU-001 → SWR-TCU-001 / HWR-TCU-004 |
| Requirement | Test | SYS-TCU-007 → TST-TCU-006 |
| Change request | Regression scope | CR-TCU-X → impacted IF/SWR/TST links |

### 35.5.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.5.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Telematics Control Unit is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.6 eCall System (ECALL)

### 35.6.1 Project context

- **Domain**: emergency call service.
- **Goal**: place an emergency call and transmit minimum data after a qualifying crash or SOS trigger.
- **Primary sensing / input context**: crash trigger, GNSS, modem status, backup battery, SOS switch.
- **Primary actuation / output context**: cellular emergency session and cabin audio routing.
- **Human-machine interaction**: SOS lamp, call status, fault status.
- **Network context**: cellular plus internal vehicle interfaces.
- **Operational design domain summary**: qualifying crash events and manual emergency requests.

### 35.6.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-ECALL-001 | OEM Product / Feature Planning | The vehicle shall provide eCall System behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-ECALL-002 | Safety Office | The ECALL function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-ECALL-003 | Regulatory / Homologation | The ECALL function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-ECALL-004 | HMI / Brand | The ECALL function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-ECALL-005 | Service / After Sales | The ECALL function shall expose diagnosable faults for backup battery, audio path, GNSS, modem, switch diagnosis. | Enables maintainability |
| SH-ECALL-006 | Cybersecurity | The ECALL function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-ECALL-007 | Manufacturing | The ECALL item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-ECALL-008 | Validation | The ECALL item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.6.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-ECALL-001 | The vehicle shall make eCall System available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-ECALL-002 | The vehicle shall communicate eCall System states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-ECALL-003 | The vehicle shall preserve driver authority and safe handback behavior for eCall System. | Critical for controllability |
| VEH-ECALL-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for eCall System. | Supports safety and service |
| VEH-ECALL-005 | The vehicle shall support variant and market configuration of eCall System without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-ECALL-006 | The vehicle shall store event and health information relevant to eCall System according to legal and privacy rules. | Supports field learning |

### 35.6.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-ECALL-001 | The system shall process crash trigger, GNSS, modem status, backup battery, SOS switch using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-ECALL-002 | The system shall deliver place an emergency call and transmit minimum data after a qualifying crash or SOS trigger while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-ECALL-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-ECALL-004 | The system shall monitor output-path acknowledgement or feedback from cellular emergency session and cabin audio routing. | Closed-loop supervision |
| SYS-ECALL-005 | The system shall inform SOS lamp, call status, fault status about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-ECALL-006 | The system shall inhibit activation or transition to degraded mode when fails to place emergency call after a qualifying crash cannot be mitigated safely. | Activation gating |
| SYS-ECALL-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for backup battery, audio path, GNSS, modem, switch diagnosis. | Serviceability |
| SYS-ECALL-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-ECALL-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-ECALL-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.6.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-ECALL-001 | Nominal use within qualifying crash events and manual emergency requests | fails to place emergency call after a qualifying crash | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-ECALL-002 | Nominal use within qualifying crash events and manual emergency requests | places a false emergency call | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-ECALL-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-ECALL-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-ECALL-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL C |

### 35.6.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-ECALL-001 | Prevent hazardous loss of intended eCall System support or service when it is required. | ASIL C |
| SG-ECALL-002 | Prevent hazardous false or unintended behavior related to eCall System. | ASIL C |
| SG-ECALL-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for eCall System. | ASIL C |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-ECALL-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade eCall System according to the safety concept. | SG-ECALL-003 |
| FSR-ECALL-002 | The item shall monitor acknowledgement or feedback on the cellular emergency session and cabin audio routing path where relevant and transition to safe state on loss of confidence. | SG-ECALL-001 |
| FSR-ECALL-003 | The item shall bound or suppress places a false emergency call using confidence, plausibility, and arbitration checks. | SG-ECALL-002 |
| FSR-ECALL-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via SOS lamp, call status, fault status. | SG-ECALL-001 |
| FSR-ECALL-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-ECALL-003 |

### 35.6.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests crash trigger, GNSS, modem status, backup battery, SOS switch, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to place an emergency call and transmit minimum data after a qualifying crash or SOS trigger. |
| Output / actuation layer | Routes requests or actions through cellular emergency session and cabin audio routing with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through SOS lamp, call status, fault status. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over cellular plus internal vehicle interfaces. |

### 35.6.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-ECALL-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-ECALL-002 | Core logic subsystem shall implement the behavior to place an emergency call and transmit minimum data after a qualifying crash or SOS trigger. | Feature application |
| SUB-ECALL-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for eCall System. | Application state machine |
| SUB-ECALL-004 | Diagnostics subsystem shall detect and classify faults related to backup battery, audio path, GNSS, modem, switch diagnosis. | Diagnostic manager |
| SUB-ECALL-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-ECALL-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-ECALL-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-ECALL-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.6.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-ECALL-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-ECALL-002 | The software shall implement the state machine for eCall System with explicit transitions and inhibition reasons. | Behavior control |
| SWR-ECALL-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-ECALL-004 | The software shall manage degraded behavior such that the system will retry according to law, report unavailability, preserve emergency power path. | Safe degradation |
| SWR-ECALL-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-ECALL-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-ECALL-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-ECALL-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-ECALL-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-ECALL-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.6.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-ECALL-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-ECALL-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-ECALL-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-ECALL-004 | The hardware shall support reliable interfacing to crash trigger, GNSS, modem status, backup battery, SOS switch and cellular emergency session and cabin audio routing as applicable. | I/O integrity |
| HWR-ECALL-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-ECALL-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.6.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-ECALL-001 | Input sensor/status interface | cellular plus internal vehicle interfaces | Define units, timestamps, validity, freshness, and failure behavior for crash trigger, GNSS, modem status, backup battery, SOS switch. |
| IF-ECALL-002 | Vehicle-state interface | cellular plus internal vehicle interfaces | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-ECALL-003 | Output/actuation interface | cellular plus internal vehicle interfaces | Define request format, acknowledgement, counters, and fail-safe behavior for cellular emergency session and cabin audio routing. |
| IF-ECALL-004 | HMI interface | cellular plus internal vehicle interfaces | Define state, warning, message IDs, and update timing for SOS lamp, call status, fault status. |
| IF-ECALL-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-ECALL-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-ECALL-007 | Logging / telemetry interface | cellular plus internal vehicle interfaces | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-ECALL-008 | Update / security interface | cellular plus internal vehicle interfaces | Define software identity, package trust, and protected service access as applicable. |

### 35.6.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-ECALL-001 | Requirement-based SIL tests shall verify nominal behavior for eCall System. | Functional verification |
| TST-ECALL-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-ECALL-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-ECALL-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-ECALL-005 | Environmental and power-condition tests shall verify that eCall System responds safely under disturbances. | Environmental confidence |
| TST-ECALL-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-ECALL-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-ECALL-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-ECALL-009 | Vehicle tests shall verify customer-visible behavior and integration with SOS lamp, call status, fault status. | Vehicle-level verification |
| TST-ECALL-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.6.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.6.14 Validation

- Validate that eCall System provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through SOS lamp, call status, fault status is correct and timely.
- Validate that degraded behavior (retry according to law, report unavailability, preserve emergency power path) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.6.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-ECALL-001 → VEH-ECALL-001 |
| Vehicle requirement | System requirement | VEH-ECALL-003 → SYS-ECALL-004 / SYS-ECALL-006 |
| Hazard | Safety goal / FSR | HE-ECALL-001 → SG-ECALL-001 → FSR-ECALL-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-ECALL-003 → SUB-ECALL-001 → SWR-ECALL-001 / HWR-ECALL-004 |
| Requirement | Test | SYS-ECALL-007 → TST-ECALL-006 |
| Change request | Regression scope | CR-ECALL-X → impacted IF/SWR/TST links |

### 35.6.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.6.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- eCall System is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.7 Over-the-Air Update System (OTA)

### 35.7.1 Project context

- **Domain**: software lifecycle management.
- **Goal**: securely download, stage, validate, activate, and roll back software packages.
- **Primary sensing / input context**: vehicle preconditions, storage health, package signatures, ECU health status.
- **Primary actuation / output context**: package staging, ECU flashing, rollback, user notifications.
- **Human-machine interaction**: campaign status, consent, progress, result messaging.
- **Network context**: backend TLS/IP, DoIP, CAN, Ethernet.
- **Operational design domain summary**: approved parked or otherwise safe update conditions.

### 35.7.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-OTA-001 | OEM Product / Feature Planning | The vehicle shall provide Over-the-Air Update System behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-OTA-002 | Safety Office | The OTA function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-OTA-003 | Regulatory / Homologation | The OTA function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-OTA-004 | HMI / Brand | The OTA function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-OTA-005 | Service / After Sales | The OTA function shall expose diagnosable faults for campaign history, package integrity, recovery path diagnosis. | Enables maintainability |
| SH-OTA-006 | Cybersecurity | The OTA function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-OTA-007 | Manufacturing | The OTA item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-OTA-008 | Validation | The OTA item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.7.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-OTA-001 | The vehicle shall make Over-the-Air Update System available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-OTA-002 | The vehicle shall communicate Over-the-Air Update System states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-OTA-003 | The vehicle shall preserve driver authority and safe handback behavior for Over-the-Air Update System. | Critical for controllability |
| VEH-OTA-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Over-the-Air Update System. | Supports safety and service |
| VEH-OTA-005 | The vehicle shall support variant and market configuration of Over-the-Air Update System without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-OTA-006 | The vehicle shall store event and health information relevant to Over-the-Air Update System according to legal and privacy rules. | Supports field learning |

### 35.7.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-OTA-001 | The system shall process vehicle preconditions, storage health, package signatures, ECU health status using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-OTA-002 | The system shall deliver securely download, stage, validate, activate, and roll back software packages while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-OTA-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-OTA-004 | The system shall monitor output-path acknowledgement or feedback from package staging, ECU flashing, rollback, user notifications. | Closed-loop supervision |
| SYS-OTA-005 | The system shall inform campaign status, consent, progress, result messaging about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-OTA-006 | The system shall inhibit activation or transition to degraded mode when activates corrupted or incompatible software cannot be mitigated safely. | Activation gating |
| SYS-OTA-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for campaign history, package integrity, recovery path diagnosis. | Serviceability |
| SYS-OTA-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-OTA-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-OTA-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.7.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-OTA-001 | Nominal use within approved parked or otherwise safe update conditions | activates corrupted or incompatible software | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-OTA-002 | Nominal use within approved parked or otherwise safe update conditions | renders the vehicle unusable after interrupted update | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-OTA-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-OTA-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-OTA-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL D |

### 35.7.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-OTA-001 | Prevent hazardous loss of intended Over-the-Air Update System support or service when it is required. | ASIL C |
| SG-OTA-002 | Prevent hazardous false or unintended behavior related to Over-the-Air Update System. | ASIL C |
| SG-OTA-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Over-the-Air Update System. | ASIL D |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-OTA-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Over-the-Air Update System according to the safety concept. | SG-OTA-003 |
| FSR-OTA-002 | The item shall monitor acknowledgement or feedback on the package staging, ECU flashing, rollback, user notifications path where relevant and transition to safe state on loss of confidence. | SG-OTA-001 |
| FSR-OTA-003 | The item shall bound or suppress renders the vehicle unusable after interrupted update using confidence, plausibility, and arbitration checks. | SG-OTA-002 |
| FSR-OTA-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via campaign status, consent, progress, result messaging. | SG-OTA-001 |
| FSR-OTA-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-OTA-003 |

### 35.7.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests vehicle preconditions, storage health, package signatures, ECU health status, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to securely download, stage, validate, activate, and roll back software packages. |
| Output / actuation layer | Routes requests or actions through package staging, ECU flashing, rollback, user notifications with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through campaign status, consent, progress, result messaging. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over backend TLS/IP, DoIP, CAN, Ethernet. |

### 35.7.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-OTA-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-OTA-002 | Core logic subsystem shall implement the behavior to securely download, stage, validate, activate, and roll back software packages. | Feature application |
| SUB-OTA-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Over-the-Air Update System. | Application state machine |
| SUB-OTA-004 | Diagnostics subsystem shall detect and classify faults related to campaign history, package integrity, recovery path diagnosis. | Diagnostic manager |
| SUB-OTA-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-OTA-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-OTA-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-OTA-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.7.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-OTA-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-OTA-002 | The software shall implement the state machine for Over-the-Air Update System with explicit transitions and inhibition reasons. | Behavior control |
| SWR-OTA-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-OTA-004 | The software shall manage degraded behavior such that the system will prevent activation, roll back, and preserve last known good software. | Safe degradation |
| SWR-OTA-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-OTA-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-OTA-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-OTA-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-OTA-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-OTA-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.7.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-OTA-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-OTA-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-OTA-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-OTA-004 | The hardware shall support reliable interfacing to vehicle preconditions, storage health, package signatures, ECU health status and package staging, ECU flashing, rollback, user notifications as applicable. | I/O integrity |
| HWR-OTA-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-OTA-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.7.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-OTA-001 | Input sensor/status interface | backend TLS/IP, DoIP, CAN, Ethernet | Define units, timestamps, validity, freshness, and failure behavior for vehicle preconditions, storage health, package signatures, ECU health status. |
| IF-OTA-002 | Vehicle-state interface | backend TLS/IP, DoIP, CAN, Ethernet | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-OTA-003 | Output/actuation interface | backend TLS/IP, DoIP, CAN, Ethernet | Define request format, acknowledgement, counters, and fail-safe behavior for package staging, ECU flashing, rollback, user notifications. |
| IF-OTA-004 | HMI interface | backend TLS/IP, DoIP, CAN, Ethernet | Define state, warning, message IDs, and update timing for campaign status, consent, progress, result messaging. |
| IF-OTA-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-OTA-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-OTA-007 | Logging / telemetry interface | backend TLS/IP, DoIP, CAN, Ethernet | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-OTA-008 | Update / security interface | backend TLS/IP, DoIP, CAN, Ethernet | Define software identity, package trust, and protected service access as applicable. |

### 35.7.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-OTA-001 | Requirement-based SIL tests shall verify nominal behavior for Over-the-Air Update System. | Functional verification |
| TST-OTA-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-OTA-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-OTA-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-OTA-005 | Environmental and power-condition tests shall verify that Over-the-Air Update System responds safely under disturbances. | Environmental confidence |
| TST-OTA-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-OTA-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-OTA-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-OTA-009 | Vehicle tests shall verify customer-visible behavior and integration with campaign status, consent, progress, result messaging. | Vehicle-level verification |
| TST-OTA-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.7.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.7.14 Validation

- Validate that Over-the-Air Update System provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through campaign status, consent, progress, result messaging is correct and timely.
- Validate that degraded behavior (prevent activation, roll back, and preserve last known good software) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.7.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-OTA-001 → VEH-OTA-001 |
| Vehicle requirement | System requirement | VEH-OTA-003 → SYS-OTA-004 / SYS-OTA-006 |
| Hazard | Safety goal / FSR | HE-OTA-001 → SG-OTA-001 → FSR-OTA-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-OTA-003 → SUB-OTA-001 → SWR-OTA-001 / HWR-OTA-004 |
| Requirement | Test | SYS-OTA-007 → TST-OTA-006 |
| Change request | Regression scope | CR-OTA-X → impacted IF/SWR/TST links |

### 35.7.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.7.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Over-the-Air Update System is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.8 Digital Instrument Cluster (CLUSTER)

### 35.8.1 Project context

- **Domain**: driver information and warning presentation.
- **Goal**: display accurate, prioritized vehicle status, telltales, and ADAS information.
- **Primary sensing / input context**: vehicle status messages, warnings, ADAS states, ambient light.
- **Primary actuation / output context**: display panel, telltale rendering, backlight, chime coordination.
- **Human-machine interaction**: speedometer, telltales, warnings, menus, ADAS graphics.
- **Network context**: CAN, Ethernet, internal display interfaces.
- **Operational design domain summary**: all customer driving states with day/night and fault conditions.

### 35.8.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-CLUSTER-001 | OEM Product / Feature Planning | The vehicle shall provide Digital Instrument Cluster behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-CLUSTER-002 | Safety Office | The CLUSTER function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-CLUSTER-003 | Regulatory / Homologation | The CLUSTER function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-CLUSTER-004 | HMI / Brand | The CLUSTER function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-CLUSTER-005 | Service / After Sales | The CLUSTER function shall expose diagnosable faults for display pipeline, pixel test, reset, configuration diagnosis. | Enables maintainability |
| SH-CLUSTER-006 | Cybersecurity | The CLUSTER function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-CLUSTER-007 | Manufacturing | The CLUSTER item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-CLUSTER-008 | Validation | The CLUSTER item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.8.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-CLUSTER-001 | The vehicle shall make Digital Instrument Cluster available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-CLUSTER-002 | The vehicle shall communicate Digital Instrument Cluster states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-CLUSTER-003 | The vehicle shall preserve driver authority and safe handback behavior for Digital Instrument Cluster. | Critical for controllability |
| VEH-CLUSTER-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Digital Instrument Cluster. | Supports safety and service |
| VEH-CLUSTER-005 | The vehicle shall support variant and market configuration of Digital Instrument Cluster without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-CLUSTER-006 | The vehicle shall store event and health information relevant to Digital Instrument Cluster according to legal and privacy rules. | Supports field learning |

### 35.8.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-CLUSTER-001 | The system shall process vehicle status messages, warnings, ADAS states, ambient light using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-CLUSTER-002 | The system shall deliver display accurate, prioritized vehicle status, telltales, and ADAS information while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-CLUSTER-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-CLUSTER-004 | The system shall monitor output-path acknowledgement or feedback from display panel, telltale rendering, backlight, chime coordination. | Closed-loop supervision |
| SYS-CLUSTER-005 | The system shall inform speedometer, telltales, warnings, menus, ADAS graphics about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-CLUSTER-006 | The system shall inhibit activation or transition to degraded mode when fails to display critical warning or accurate speed cannot be mitigated safely. | Activation gating |
| SYS-CLUSTER-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for display pipeline, pixel test, reset, configuration diagnosis. | Serviceability |
| SYS-CLUSTER-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-CLUSTER-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-CLUSTER-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.8.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-CLUSTER-001 | Nominal use within all customer driving states with day/night and fault conditions | fails to display critical warning or accurate speed | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-CLUSTER-002 | Nominal use within all customer driving states with day/night and fault conditions | shows misleading ADAS or warning status | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL C |
| HE-CLUSTER-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-CLUSTER-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-CLUSTER-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL C |

### 35.8.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-CLUSTER-001 | Prevent hazardous loss of intended Digital Instrument Cluster support or service when it is required. | ASIL C |
| SG-CLUSTER-002 | Prevent hazardous false or unintended behavior related to Digital Instrument Cluster. | ASIL C |
| SG-CLUSTER-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Digital Instrument Cluster. | ASIL C |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-CLUSTER-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Digital Instrument Cluster according to the safety concept. | SG-CLUSTER-003 |
| FSR-CLUSTER-002 | The item shall monitor acknowledgement or feedback on the display panel, telltale rendering, backlight, chime coordination path where relevant and transition to safe state on loss of confidence. | SG-CLUSTER-001 |
| FSR-CLUSTER-003 | The item shall bound or suppress shows misleading ADAS or warning status using confidence, plausibility, and arbitration checks. | SG-CLUSTER-002 |
| FSR-CLUSTER-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via speedometer, telltales, warnings, menus, ADAS graphics. | SG-CLUSTER-001 |
| FSR-CLUSTER-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-CLUSTER-003 |

### 35.8.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests vehicle status messages, warnings, ADAS states, ambient light, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to display accurate, prioritized vehicle status, telltales, and ADAS information. |
| Output / actuation layer | Routes requests or actions through display panel, telltale rendering, backlight, chime coordination with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through speedometer, telltales, warnings, menus, ADAS graphics. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over CAN, Ethernet, internal display interfaces. |

### 35.8.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-CLUSTER-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-CLUSTER-002 | Core logic subsystem shall implement the behavior to display accurate, prioritized vehicle status, telltales, and ADAS information. | Feature application |
| SUB-CLUSTER-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Digital Instrument Cluster. | Application state machine |
| SUB-CLUSTER-004 | Diagnostics subsystem shall detect and classify faults related to display pipeline, pixel test, reset, configuration diagnosis. | Diagnostic manager |
| SUB-CLUSTER-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-CLUSTER-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-CLUSTER-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-CLUSTER-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.8.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-CLUSTER-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-CLUSTER-002 | The software shall implement the state machine for Digital Instrument Cluster with explicit transitions and inhibition reasons. | Behavior control |
| SWR-CLUSTER-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-CLUSTER-004 | The software shall manage degraded behavior such that the system will switch to fallback view and preserve mandatory telltales. | Safe degradation |
| SWR-CLUSTER-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-CLUSTER-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-CLUSTER-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-CLUSTER-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-CLUSTER-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-CLUSTER-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.8.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-CLUSTER-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-CLUSTER-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-CLUSTER-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-CLUSTER-004 | The hardware shall support reliable interfacing to vehicle status messages, warnings, ADAS states, ambient light and display panel, telltale rendering, backlight, chime coordination as applicable. | I/O integrity |
| HWR-CLUSTER-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-CLUSTER-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.8.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-CLUSTER-001 | Input sensor/status interface | CAN, Ethernet, internal display interfaces | Define units, timestamps, validity, freshness, and failure behavior for vehicle status messages, warnings, ADAS states, ambient light. |
| IF-CLUSTER-002 | Vehicle-state interface | CAN, Ethernet, internal display interfaces | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-CLUSTER-003 | Output/actuation interface | CAN, Ethernet, internal display interfaces | Define request format, acknowledgement, counters, and fail-safe behavior for display panel, telltale rendering, backlight, chime coordination. |
| IF-CLUSTER-004 | HMI interface | CAN, Ethernet, internal display interfaces | Define state, warning, message IDs, and update timing for speedometer, telltales, warnings, menus, ADAS graphics. |
| IF-CLUSTER-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-CLUSTER-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-CLUSTER-007 | Logging / telemetry interface | CAN, Ethernet, internal display interfaces | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-CLUSTER-008 | Update / security interface | CAN, Ethernet, internal display interfaces | Define software identity, package trust, and protected service access as applicable. |

### 35.8.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-CLUSTER-001 | Requirement-based SIL tests shall verify nominal behavior for Digital Instrument Cluster. | Functional verification |
| TST-CLUSTER-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-CLUSTER-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-CLUSTER-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-CLUSTER-005 | Environmental and power-condition tests shall verify that Digital Instrument Cluster responds safely under disturbances. | Environmental confidence |
| TST-CLUSTER-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-CLUSTER-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-CLUSTER-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-CLUSTER-009 | Vehicle tests shall verify customer-visible behavior and integration with speedometer, telltales, warnings, menus, ADAS graphics. | Vehicle-level verification |
| TST-CLUSTER-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.8.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.8.14 Validation

- Validate that Digital Instrument Cluster provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through speedometer, telltales, warnings, menus, ADAS graphics is correct and timely.
- Validate that degraded behavior (switch to fallback view and preserve mandatory telltales) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.8.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-CLUSTER-001 → VEH-CLUSTER-001 |
| Vehicle requirement | System requirement | VEH-CLUSTER-003 → SYS-CLUSTER-004 / SYS-CLUSTER-006 |
| Hazard | Safety goal / FSR | HE-CLUSTER-001 → SG-CLUSTER-001 → FSR-CLUSTER-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-CLUSTER-003 → SUB-CLUSTER-001 → SWR-CLUSTER-001 / HWR-CLUSTER-004 |
| Requirement | Test | SYS-CLUSTER-007 → TST-CLUSTER-006 |
| Change request | Regression scope | CR-CLUSTER-X → impacted IF/SWR/TST links |

### 35.8.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.8.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Digital Instrument Cluster is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.9 Vehicle Gateway (GATEWAY)

### 35.9.1 Project context

- **Domain**: cross-domain communication and security enforcement.
- **Goal**: route, filter, secure, and diagnose traffic between vehicle domains and external services.
- **Primary sensing / input context**: network load, frame health, policy state, vehicle state.
- **Primary actuation / output context**: message routing, rate limiting, domain isolation, secure diagnostics.
- **Human-machine interaction**: mostly service-facing; limited driver-facing if required.
- **Network context**: CAN, CAN FD, LIN, Ethernet, DoIP.
- **Operational design domain summary**: all vehicle network states including sleep, wake, service, update, driving.

### 35.9.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-GATEWAY-001 | OEM Product / Feature Planning | The vehicle shall provide Vehicle Gateway behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-GATEWAY-002 | Safety Office | The GATEWAY function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-GATEWAY-003 | Regulatory / Homologation | The GATEWAY function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-GATEWAY-004 | HMI / Brand | The GATEWAY function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-GATEWAY-005 | Service / After Sales | The GATEWAY function shall expose diagnosable faults for routing, topology, error-counter, policy diagnosis. | Enables maintainability |
| SH-GATEWAY-006 | Cybersecurity | The GATEWAY function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-GATEWAY-007 | Manufacturing | The GATEWAY item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-GATEWAY-008 | Validation | The GATEWAY item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.9.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-GATEWAY-001 | The vehicle shall make Vehicle Gateway available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-GATEWAY-002 | The vehicle shall communicate Vehicle Gateway states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-GATEWAY-003 | The vehicle shall preserve driver authority and safe handback behavior for Vehicle Gateway. | Critical for controllability |
| VEH-GATEWAY-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Vehicle Gateway. | Supports safety and service |
| VEH-GATEWAY-005 | The vehicle shall support variant and market configuration of Vehicle Gateway without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-GATEWAY-006 | The vehicle shall store event and health information relevant to Vehicle Gateway according to legal and privacy rules. | Supports field learning |

### 35.9.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-GATEWAY-001 | The system shall process network load, frame health, policy state, vehicle state using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-GATEWAY-002 | The system shall deliver route, filter, secure, and diagnose traffic between vehicle domains and external services while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-GATEWAY-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-GATEWAY-004 | The system shall monitor output-path acknowledgement or feedback from message routing, rate limiting, domain isolation, secure diagnostics. | Closed-loop supervision |
| SYS-GATEWAY-005 | The system shall inform mostly service-facing; limited driver-facing if required about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-GATEWAY-006 | The system shall inhibit activation or transition to degraded mode when drops, delays, or misroutes safety-critical traffic cannot be mitigated safely. | Activation gating |
| SYS-GATEWAY-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for routing, topology, error-counter, policy diagnosis. | Serviceability |
| SYS-GATEWAY-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-GATEWAY-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-GATEWAY-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.9.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-GATEWAY-001 | Nominal use within all vehicle network states including sleep, wake, service, update, driving | drops, delays, or misroutes safety-critical traffic | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-GATEWAY-002 | Nominal use within all vehicle network states including sleep, wake, service, update, driving | allows unauthorized traffic into protected domains | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL D |
| HE-GATEWAY-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-GATEWAY-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-GATEWAY-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL D |

### 35.9.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-GATEWAY-001 | Prevent hazardous loss of intended Vehicle Gateway support or service when it is required. | ASIL C |
| SG-GATEWAY-002 | Prevent hazardous false or unintended behavior related to Vehicle Gateway. | ASIL D |
| SG-GATEWAY-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Vehicle Gateway. | ASIL D |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-GATEWAY-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Vehicle Gateway according to the safety concept. | SG-GATEWAY-003 |
| FSR-GATEWAY-002 | The item shall monitor acknowledgement or feedback on the message routing, rate limiting, domain isolation, secure diagnostics path where relevant and transition to safe state on loss of confidence. | SG-GATEWAY-001 |
| FSR-GATEWAY-003 | The item shall bound or suppress allows unauthorized traffic into protected domains using confidence, plausibility, and arbitration checks. | SG-GATEWAY-002 |
| FSR-GATEWAY-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via mostly service-facing; limited driver-facing if required. | SG-GATEWAY-001 |
| FSR-GATEWAY-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-GATEWAY-003 |

### 35.9.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests network load, frame health, policy state, vehicle state, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to route, filter, secure, and diagnose traffic between vehicle domains and external services. |
| Output / actuation layer | Routes requests or actions through message routing, rate limiting, domain isolation, secure diagnostics with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through mostly service-facing; limited driver-facing if required. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over CAN, CAN FD, LIN, Ethernet, DoIP. |

### 35.9.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-GATEWAY-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-GATEWAY-002 | Core logic subsystem shall implement the behavior to route, filter, secure, and diagnose traffic between vehicle domains and external services. | Feature application |
| SUB-GATEWAY-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Vehicle Gateway. | Application state machine |
| SUB-GATEWAY-004 | Diagnostics subsystem shall detect and classify faults related to routing, topology, error-counter, policy diagnosis. | Diagnostic manager |
| SUB-GATEWAY-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-GATEWAY-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-GATEWAY-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-GATEWAY-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.9.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-GATEWAY-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-GATEWAY-002 | The software shall implement the state machine for Vehicle Gateway with explicit transitions and inhibition reasons. | Behavior control |
| SWR-GATEWAY-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-GATEWAY-004 | The software shall manage degraded behavior such that the system will prioritize critical traffic and isolate failing segments. | Safe degradation |
| SWR-GATEWAY-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-GATEWAY-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-GATEWAY-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-GATEWAY-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-GATEWAY-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-GATEWAY-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.9.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-GATEWAY-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-GATEWAY-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-GATEWAY-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-GATEWAY-004 | The hardware shall support reliable interfacing to network load, frame health, policy state, vehicle state and message routing, rate limiting, domain isolation, secure diagnostics as applicable. | I/O integrity |
| HWR-GATEWAY-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-GATEWAY-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.9.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-GATEWAY-001 | Input sensor/status interface | CAN, CAN FD, LIN, Ethernet, DoIP | Define units, timestamps, validity, freshness, and failure behavior for network load, frame health, policy state, vehicle state. |
| IF-GATEWAY-002 | Vehicle-state interface | CAN, CAN FD, LIN, Ethernet, DoIP | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-GATEWAY-003 | Output/actuation interface | CAN, CAN FD, LIN, Ethernet, DoIP | Define request format, acknowledgement, counters, and fail-safe behavior for message routing, rate limiting, domain isolation, secure diagnostics. |
| IF-GATEWAY-004 | HMI interface | CAN, CAN FD, LIN, Ethernet, DoIP | Define state, warning, message IDs, and update timing for mostly service-facing; limited driver-facing if required. |
| IF-GATEWAY-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-GATEWAY-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-GATEWAY-007 | Logging / telemetry interface | CAN, CAN FD, LIN, Ethernet, DoIP | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-GATEWAY-008 | Update / security interface | CAN, CAN FD, LIN, Ethernet, DoIP | Define software identity, package trust, and protected service access as applicable. |

### 35.9.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-GATEWAY-001 | Requirement-based SIL tests shall verify nominal behavior for Vehicle Gateway. | Functional verification |
| TST-GATEWAY-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-GATEWAY-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-GATEWAY-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-GATEWAY-005 | Environmental and power-condition tests shall verify that Vehicle Gateway responds safely under disturbances. | Environmental confidence |
| TST-GATEWAY-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-GATEWAY-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-GATEWAY-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-GATEWAY-009 | Vehicle tests shall verify customer-visible behavior and integration with mostly service-facing; limited driver-facing if required. | Vehicle-level verification |
| TST-GATEWAY-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.9.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.9.14 Validation

- Validate that Vehicle Gateway provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through mostly service-facing; limited driver-facing if required is correct and timely.
- Validate that degraded behavior (prioritize critical traffic and isolate failing segments) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.9.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-GATEWAY-001 → VEH-GATEWAY-001 |
| Vehicle requirement | System requirement | VEH-GATEWAY-003 → SYS-GATEWAY-004 / SYS-GATEWAY-006 |
| Hazard | Safety goal / FSR | HE-GATEWAY-001 → SG-GATEWAY-001 → FSR-GATEWAY-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-GATEWAY-003 → SUB-GATEWAY-001 → SWR-GATEWAY-001 / HWR-GATEWAY-004 |
| Requirement | Test | SYS-GATEWAY-007 → TST-GATEWAY-006 |
| Change request | Regression scope | CR-GATEWAY-X → impacted IF/SWR/TST links |

### 35.9.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.9.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Vehicle Gateway is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 35.10 Zonal Architecture (ZONAL)

### 35.10.1 Project context

- **Domain**: distributed E/E architecture.
- **Goal**: organize vehicle electronics by physical zones with backbone networking and central compute.
- **Primary sensing / input context**: distributed zone I/O, backbone health, power-state coordination, service maps.
- **Primary actuation / output context**: local zone outputs, power switching, service abstractions, backbone communication.
- **Human-machine interaction**: indirect through hosted vehicle functions.
- **Network context**: Automotive Ethernet/TSN, local buses, service APIs.
- **Operational design domain summary**: vehicle-wide electrical and communication operation across all programs and variants.

### 35.10.2 Stakeholder requirements

| ID | Source | Requirement | Rationale |
|---|---|---|---|
| SH-ZONAL-001 | OEM Product / Feature Planning | The vehicle shall provide Zonal Architecture behavior that delivers clear customer value in the intended operating domain. | Defines business and user intent |
| SH-ZONAL-002 | Safety Office | The ZONAL function shall avoid hazardous behavior and degrade safely when required inputs or outputs are not trustworthy. | Establishes safety intent |
| SH-ZONAL-003 | Regulatory / Homologation | The ZONAL function shall satisfy applicable legal, market, and rating-program obligations. | Ensures compliance |
| SH-ZONAL-004 | HMI / Brand | The ZONAL function shall provide understandable driver information, warnings, and status states. | Ensures usability |
| SH-ZONAL-005 | Service / After Sales | The ZONAL function shall expose diagnosable faults for topology-aware fault isolation, commissioning, coding, update diagnosis. | Enables maintainability |
| SH-ZONAL-006 | Cybersecurity | The ZONAL function shall reject unauthorized commands, corrupted data, and untrusted software or configuration. | Protects safety and trust |
| SH-ZONAL-007 | Manufacturing | The ZONAL item shall support end-of-line test, coding, calibration, and traceable configuration. | Supports industrialization |
| SH-ZONAL-008 | Validation | The ZONAL item shall be verifiable in simulation, HIL, vehicle, and field-oriented validation campaigns. | Supports evidence generation |

### 35.10.3 Vehicle requirements

| ID | Vehicle requirement | Why it matters |
|---|---|---|
| VEH-ZONAL-001 | The vehicle shall make Zonal Architecture available only within the defined operating domain and system-health preconditions. | Prevents misleading availability |
| VEH-ZONAL-002 | The vehicle shall communicate Zonal Architecture states such as Standby, Available, Active, Limited, Override, and Fault to the driver or service path as appropriate. | Improves transparency |
| VEH-ZONAL-003 | The vehicle shall preserve driver authority and safe handback behavior for Zonal Architecture. | Critical for controllability |
| VEH-ZONAL-004 | The vehicle shall support diagnosable degraded behavior rather than silent performance loss for Zonal Architecture. | Supports safety and service |
| VEH-ZONAL-005 | The vehicle shall support variant and market configuration of Zonal Architecture without uncontrolled behavior change. | Supports portfolio reuse |
| VEH-ZONAL-006 | The vehicle shall store event and health information relevant to Zonal Architecture according to legal and privacy rules. | Supports field learning |

### 35.10.4 System requirements

| ID | System requirement | Engineering purpose |
|---|---|---|
| SYS-ZONAL-001 | The system shall process distributed zone I/O, backbone health, power-state coordination, service maps using synchronized timestamps and input-quality evaluation. | Data coherence |
| SYS-ZONAL-002 | The system shall deliver organize vehicle electronics by physical zones with backbone networking and central compute while respecting safety, timing, and comfort constraints. | Core feature behavior |
| SYS-ZONAL-003 | The system shall monitor input freshness, range, plausibility, and communication health on all safety-relevant interfaces. | Fault detection |
| SYS-ZONAL-004 | The system shall monitor output-path acknowledgement or feedback from local zone outputs, power switching, service abstractions, backbone communication. | Closed-loop supervision |
| SYS-ZONAL-005 | The system shall inform indirect through hosted vehicle functions about state changes, limitations, and fault conditions within allocated latency. | HMI timeliness |
| SYS-ZONAL-006 | The system shall inhibit activation or transition to degraded mode when loses or delays critical service traffic due to zonal controller or backbone failure cannot be mitigated safely. | Activation gating |
| SYS-ZONAL-007 | The system shall provide platform diagnostics, event logging, and freeze-frame support for topology-aware fault isolation, commissioning, coding, update diagnosis. | Serviceability |
| SYS-ZONAL-008 | The system shall support secure configuration, software identity, and protected calibration where relevant. | Configuration trust |
| SYS-ZONAL-009 | The system shall maintain deterministic execution and data-flow behavior under worst-case normal load. | Real-time behavior |
| SYS-ZONAL-010 | The system shall support change impact analysis through traceable requirement, interface, and test identifiers. | Lifecycle control |

### 35.10.5 HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| HE-ZONAL-001 | Nominal use within vehicle-wide electrical and communication operation across all programs and variants | loses or delays critical service traffic due to zonal controller or backbone failure | Collision, loss of intended function, or delayed response causing harm | S3 | E4 | C2 | ASIL C |
| HE-ZONAL-002 | Nominal use within vehicle-wide electrical and communication operation across all programs and variants | maps a service to the wrong physical endpoint or unsafe power state | Unexpected vehicle behavior or misleading status | S3 | E4 | C3 | ASIL D |
| HE-ZONAL-003 | Sensor degraded or blocked | Function remains active with undetected invalid input | Unsafe output or unsafe assumption by driver/system | S3 | E3 | C3 | ASIL C |
| HE-ZONAL-004 | Communication or output-path fault | Function continues despite missing acknowledgement or stale interface data | Loss of controllability or missing intervention | S2 | E3 | C2 | ASIL B |
| HE-ZONAL-005 | Software/configuration/update anomaly | Unapproved, corrupted, or incompatible behavior becomes active | System behaves outside safety concept | S3 | E2 | C3 | ASIL D |

### 35.10.6 Safety requirements

#### Safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| SG-ZONAL-001 | Prevent hazardous loss of intended Zonal Architecture support or service when it is required. | ASIL C |
| SG-ZONAL-002 | Prevent hazardous false or unintended behavior related to Zonal Architecture. | ASIL D |
| SG-ZONAL-003 | Prevent operation with undetected critical faults in inputs, outputs, timing, or trusted configuration for Zonal Architecture. | ASIL D |

#### Functional safety requirements

| ID | Functional safety requirement | Linked safety goal |
|---|---|---|
| FSR-ZONAL-001 | The item shall detect invalid or stale safety-relevant input data and inhibit or degrade Zonal Architecture according to the safety concept. | SG-ZONAL-003 |
| FSR-ZONAL-002 | The item shall monitor acknowledgement or feedback on the local zone outputs, power switching, service abstractions, backbone communication path where relevant and transition to safe state on loss of confidence. | SG-ZONAL-001 |
| FSR-ZONAL-003 | The item shall bound or suppress maps a service to the wrong physical endpoint or unsafe power state using confidence, plausibility, and arbitration checks. | SG-ZONAL-002 |
| FSR-ZONAL-004 | The item shall inform the driver or service path about limitation and fault conditions in a timely manner via indirect through hosted vehicle functions. | SG-ZONAL-001 |
| FSR-ZONAL-005 | The item shall authenticate trusted software/configuration and prevent unsafe activation after update or configuration error. | SG-ZONAL-003 |

### 35.10.7 Architecture

| Block | Role in the item |
|---|---|
| Input / sensing layer | Ingests distributed zone I/O, backbone health, power-state coordination, service maps, validates quality, timestamps, and availability. |
| Decision / service logic | Implements the core logic required to organize vehicle electronics by physical zones with backbone networking and central compute. |
| Output / actuation layer | Routes requests or actions through local zone outputs, power switching, service abstractions, backbone communication with acknowledgement handling. |
| HMI / information layer | Controls driver or operator feedback through indirect through hosted vehicle functions. |
| Platform services | Provides diagnostics, NVM, timing, cybersecurity, update, and trace support over Automotive Ethernet/TSN, local buses, service APIs. |

### 35.10.8 Subsystem requirements

| ID | Subsystem requirement | Typical owner |
|---|---|---|
| SUB-ZONAL-001 | Input manager shall normalize, range-check, timestamp, and qualify all incoming data. | System / platform input layer |
| SUB-ZONAL-002 | Core logic subsystem shall implement the behavior to organize vehicle electronics by physical zones with backbone networking and central compute. | Feature application |
| SUB-ZONAL-003 | State-management subsystem shall govern standby, available, active, limited, override, and fault states for Zonal Architecture. | Application state machine |
| SUB-ZONAL-004 | Diagnostics subsystem shall detect and classify faults related to topology-aware fault isolation, commissioning, coding, update diagnosis. | Diagnostic manager |
| SUB-ZONAL-005 | Timing supervision subsystem shall detect deadline miss and overload conditions. | Execution manager |
| SUB-ZONAL-006 | Configuration subsystem shall handle variant coding, calibration identity, and baseline compatibility. | Configuration service |
| SUB-ZONAL-007 | Event logging subsystem shall capture key transitions, inhibition reasons, and freeze-frame context. | Logging service |
| SUB-ZONAL-008 | Security subsystem shall protect trusted software, configuration, and service access. | Platform security |

### 35.10.9 Software requirements

| ID | Software requirement | Focus |
|---|---|---|
| SWR-ZONAL-001 | The software shall validate all external inputs before using them in safety-relevant logic. | Input robustness |
| SWR-ZONAL-002 | The software shall implement the state machine for Zonal Architecture with explicit transitions and inhibition reasons. | Behavior control |
| SWR-ZONAL-003 | The software shall supervise message freshness, alive counters, CRC/checksum where defined, and timestamp coherence. | Interface integrity |
| SWR-ZONAL-004 | The software shall manage degraded behavior such that the system will fall back to predefined degraded-zone operation and preserve critical paths. | Safe degradation |
| SWR-ZONAL-005 | The software shall expose diagnostic monitors and DTC maturation/healing rules for each significant fault path. | Diagnostics |
| SWR-ZONAL-006 | The software shall provide calibration hooks with range checks and release traceability. | Calibration control |
| SWR-ZONAL-007 | The software shall maintain deterministic execution within allocated cycle-time budgets under worst-case supported load. | Timing |
| SWR-ZONAL-008 | The software shall support controlled restart behavior and preserve safe initialization state after reset. | Safe startup/restart |
| SWR-ZONAL-009 | The software shall support secure update, trusted boot assumptions, or software identity checks as relevant to the item. | Trusted execution |
| SWR-ZONAL-010 | The software shall provide traceable event codes and reason codes for activation, inhibition, and fault transitions. | Observability |

### 35.10.10 Hardware requirements

| ID | Hardware requirement | Focus |
|---|---|---|
| HWR-ZONAL-001 | The hardware shall support the required compute, memory, and communication throughput with margin. | Performance margin |
| HWR-ZONAL-002 | The hardware shall provide watchdog, reset supervision, and fault reporting suitable for the item criticality. | Safety mechanisms |
| HWR-ZONAL-003 | The hardware shall tolerate vehicle power conditions, voltage variation, and required environmental stresses. | Automotive robustness |
| HWR-ZONAL-004 | The hardware shall support reliable interfacing to distributed zone I/O, backbone health, power-state coordination, service maps and local zone outputs, power switching, service abstractions, backbone communication as applicable. | I/O integrity |
| HWR-ZONAL-005 | The hardware shall support diagnostic observability for supply, interface, memory, and thermal faults. | Serviceability |
| HWR-ZONAL-006 | The hardware shall support trusted storage or equivalent protection for software identity and configuration data where required. | Security foundation |

### 35.10.11 Interface requirements

| ID | Interface | Direction / medium | Contract highlights |
|---|---|---|---|
| IF-ZONAL-001 | Input sensor/status interface | Automotive Ethernet/TSN, local buses, service APIs | Define units, timestamps, validity, freshness, and failure behavior for distributed zone I/O, backbone health, power-state coordination, service maps. |
| IF-ZONAL-002 | Vehicle-state interface | Automotive Ethernet/TSN, local buses, service APIs | Provide ego state, power mode, and gating conditions with synchronized timestamps. |
| IF-ZONAL-003 | Output/actuation interface | Automotive Ethernet/TSN, local buses, service APIs | Define request format, acknowledgement, counters, and fail-safe behavior for local zone outputs, power switching, service abstractions, backbone communication. |
| IF-ZONAL-004 | HMI interface | Automotive Ethernet/TSN, local buses, service APIs | Define state, warning, message IDs, and update timing for indirect through hosted vehicle functions. |
| IF-ZONAL-005 | Diagnostic interface | UDS / DoIP / service APIs | Define DTCs, freeze frames, routines, DID data, and access conditions. |
| IF-ZONAL-006 | Configuration interface | NVM / secure service | Define variant coding, calibration versions, compatibility, and checksums. |
| IF-ZONAL-007 | Logging / telemetry interface | Automotive Ethernet/TSN, local buses, service APIs | Define event triggers, privacy rules, rate limits, and upload or service-read paths. |
| IF-ZONAL-008 | Update / security interface | Automotive Ethernet/TSN, local buses, service APIs | Define software identity, package trust, and protected service access as applicable. |

### 35.10.12 Test requirements

| ID | Test requirement | Purpose |
|---|---|---|
| TST-ZONAL-001 | Requirement-based SIL tests shall verify nominal behavior for Zonal Architecture. | Functional verification |
| TST-ZONAL-002 | Boundary tests shall verify operating-domain limits, mode transitions, and invalid-input handling. | Boundary robustness |
| TST-ZONAL-003 | Fault-injection tests shall verify stale data, timeout, corruption, and monitor response. | Safety robustness |
| TST-ZONAL-004 | HIL tests shall verify network timing, acknowledgements, and integration behavior. | System integration |
| TST-ZONAL-005 | Environmental and power-condition tests shall verify that Zonal Architecture responds safely under disturbances. | Environmental confidence |
| TST-ZONAL-006 | Diagnostic tests shall verify DTC setting, healing, freeze frames, and service routines. | Service readiness |
| TST-ZONAL-007 | Configuration tests shall verify variant coding and calibration compatibility. | Product-line control |
| TST-ZONAL-008 | Security tests shall verify unauthorized commands, software, or configuration are rejected. | Cybersecurity |
| TST-ZONAL-009 | Vehicle tests shall verify customer-visible behavior and integration with indirect through hosted vehicle functions. | Vehicle-level verification |
| TST-ZONAL-010 | Regression tests shall execute for every release candidate and relevant change request. | Change control |

### 35.10.13 Verification

- Static verification: requirement review, safety review, architecture review, interface review, traceability review.
- Dynamic verification: SIL for algorithms or logic, HIL for timing and interface realism, system benches for startup and diagnostics.
- Robustness verification: fault injection, overload tests, resets, power disturbance, communication faults, invalid configuration handling.
- Configuration verification: baseline IDs, calibration identities, variant combinations, package integrity, diagnostic ID consistency.
- Closure verification: all deviations dispositioned and linked to approved release baseline.

### 35.10.14 Validation

- Validate that Zonal Architecture provides the expected customer or operational value in realistic scenarios.
- Validate that driver/operator understanding through indirect through hosted vehicle functions is correct and timely.
- Validate that degraded behavior (fall back to predefined degraded-zone operation and preserve critical paths) is understandable and acceptable.
- Validate service workflows using real diagnostic tools and representative faults.
- Validate regional, legal, and fleet-operational expectations where applicable.

### 35.10.15 Traceability

| Upstream | Downstream | Trace example |
|---|---|---|
| Stakeholder need | Vehicle requirement | SH-ZONAL-001 → VEH-ZONAL-001 |
| Vehicle requirement | System requirement | VEH-ZONAL-003 → SYS-ZONAL-004 / SYS-ZONAL-006 |
| Hazard | Safety goal / FSR | HE-ZONAL-001 → SG-ZONAL-001 → FSR-ZONAL-002 |
| System requirement | Subsystem / SW / HW requirement | SYS-ZONAL-003 → SUB-ZONAL-001 → SWR-ZONAL-001 / HWR-ZONAL-004 |
| Requirement | Test | SYS-ZONAL-007 → TST-ZONAL-006 |
| Change request | Regression scope | CR-ZONAL-X → impacted IF/SWR/TST links |

### 35.10.16 Change management

1. Capture the proposed change with source, rationale, affected baselines, and urgency.
2. Perform impact analysis across requirements, hazards, safety goals, architecture, interfaces, diagnostics, tests, and release milestones.
3. Classify the change as functional, safety, interface, quality, regulatory, cybersecurity, or manufacturability driven.
4. Approve through the appropriate working group, CCB, or safety board.
5. Update linked artifacts and preserve bidirectional traceability to the change record.
6. Execute targeted verification and regression based on impact, not guesswork.
7. Re-baseline the package and record residual risk, deviation, or release note impact.

### 35.10.17 Release

- Approved requirement baseline and review history
- Approved HARA and safety requirement set
- Architecture, interface, and configuration baseline frozen or deviation-approved
- Requirement-to-test traceability with coverage evidence
- Diagnostic package and service documentation ready
- Open-issue review with risk acceptance where needed
- Calibration / variant / software identity package approved
- Post-release monitoring plan defined

**Engineering lesson**

- Zonal Architecture is not just a feature; it is a chain of assumptions, safety obligations, interfaces, and evidence.
- When the chain is weak at the top, teams compensate with late debugging and excessive retest cost.
- When the chain is explicit, release decisions become evidence-based rather than opinion-based.

---

## 36. REQUIREMENTS ENGINEERING CAPSTONE

### 36.1 Project title

**Production ADAS ECU Requirements Engineering**

This capstone simulates a realistic production program in which the learner must convert an imperfect OEM package into a disciplined engineering baseline for a centralized ADAS ECU hosting ACC, AEB, and LKA.

### 36.2 Fictional OEM requirement package

| OEM ID | Raw OEM requirement |
|---|---|
| OEM-ADAS-001 | The vehicle shall provide Highway Assist composed of ACC + LKA + AEB support on divided roads up to 130 km/h. |
| OEM-ADAS-002 | The ADAS ECU shall integrate front camera and front radar delivered by separate suppliers. |
| OEM-ADAS-003 | ADAS warning and status information shall be displayed in the digital cluster and center display. |
| OEM-ADAS-004 | Brake override shall always immediately return longitudinal control to the driver. |
| OEM-ADAS-005 | Steering assistance shall be suppressed when the driver intentionally changes lane. |
| OEM-ADAS-006 | System start-up after ignition on shall feel immediate to the customer. |
| OEM-ADAS-007 | The ECU shall support OTA updates and post-update rollback. |
| OEM-ADAS-008 | The ECU shall comply with ISO 26262 and target ASIL D for the emergency braking path. |
| OEM-ADAS-009 | False emergency braking must be avoided. |
| OEM-ADAS-010 | The ECU shall record enough data to debug field issues but must respect privacy rules. |
| OEM-ADAS-011 | The ECU shall support vehicle variants with and without surround camera package. |
| OEM-ADAS-012 | The ECU shall fit on the corporate Ethernet backbone and vehicle gateway architecture. |
| OEM-ADAS-013 | The ECU shall present diagnostic information useful to dealers and backend analytics. |
| OEM-ADAS-014 | The system shall remain safe if a sensor becomes blocked or communication is lost. |
| OEM-ADAS-015 | The project SOP date is fixed and reuse is preferred over custom development. |

### 36.3 What the learner must do

1. Analyze stakeholder needs and classify them into product, safety, architecture, service, validation, and lifecycle concerns.
2. Identify ambiguous, conflicting, missing, or non-measurable statements.
3. Create a clean system-requirement set with measurable timing, diagnostics, interface, and degraded-mode behavior.
4. Perform HARA and derive safety goals.
5. Create FSRs and indicate likely TSR decomposition directions.
6. Decompose the system into perception, decision/control, platform, diagnostics, HMI, logging, and update partitions.
7. Define interfaces to sensors, actuators, HMI, gateway, and OTA paths.
8. Define timing budgets, diagnostics, startup, and recovery behavior.
9. Create traceability linking OEM need to requirement to hazard to test to release evidence.
10. Create requirement-based test cases and fault-injection tests.
11. Build verification and validation strategies.
12. Manage requirement changes and resolve conflicting objectives.
13. Prepare the release evidence package expected for SOP readiness.

### 36.4 Ambiguity analysis of the OEM package

| OEM ID | Ambiguity or issue | Why it matters |
|---|---|---|
| OEM-ADAS-001 | “Highway Assist” is not decomposed into exact ODD, state model, and takeover assumptions. | Architecture and validation cannot scope coverage correctly. |
| OEM-ADAS-003 | Display ownership between cluster and center display is unclear. | HMI timing, fallback, and interface contracts remain undefined. |
| OEM-ADAS-006 | “Feel immediate” is subjective. | A measurable startup requirement is needed. |
| OEM-ADAS-008 | ASIL D path is named but item boundaries and safety mechanisms are unspecified. | Safety work products risk becoming vague. |
| OEM-ADAS-009 | “Must be avoided” is not measurable. | False positive metrics and confidence criteria are required. |
| OEM-ADAS-010 | “Enough data” conflicts with privacy and storage constraints. | Logging classes and retention must be defined. |
| OEM-ADAS-011 | Variant impact is named but not bounded. | Compute, interfaces, and test scope can explode late. |
| OEM-ADAS-014 | “Remain safe” is too generic. | Specific degraded modes, warnings, and inhibitions are needed. |
| OEM-ADAS-015 | Reuse preference can conflict with performance or safety timing. | A gap analysis and decision criteria are necessary. |

### 36.5 Expert solution — consolidated stakeholder needs

| Need category | Clean stakeholder need | Implications |
|---|---|---|
| Product | Provide useful and trustworthy highway assistance with understandable activation, limitation, and handback behavior. | ODD, HMI, nuisance behavior, startup timing |
| Safety | Ensure emergency braking path and steering support degrade safely and remain controllable. | HARA, safety goals, monitors, inhibition, feedback |
| Integration | Integrate radar, camera, brake, EPS, gateway, cluster, diagnostics, and OTA paths coherently. | ICD quality, timing budgets, network governance |
| Lifecycle | Support secure update, rollback, field logging, diagnostics, and variant management under control. | Configuration, privacy, service, release evidence |
| Program | Exploit reuse where justified but do not violate timing, safety, or SOP targets. | Trade studies, gap analysis, staged decisions |

### 36.6 Expert solution — cleaned system requirements

| ID | System requirement | Purpose |
|---|---|---|
| CAP-SYS-001 | The ADAS ECU shall support ACC, AEB, and LKA within a defined highway ODD covering divided roads, detectable lane boundaries, healthy front radar, healthy front camera, and ego speed from 30 km/h to 130 km/h unless feature-specific limits are tighter. | Defines scope and ODD |
| CAP-SYS-002 | The ECU shall provide warning-function readiness within 2.5 s after ignition-on and assistance readiness within 5.0 s after ignition-on when required dependencies are healthy. | Makes startup measurable |
| CAP-SYS-003 | The ECU shall disengage longitudinal control within 100 ms of valid brake override. | Protects driver authority |
| CAP-SYS-004 | The ECU shall cancel steering support within 100 ms of valid turn-indicator intent or driver torque override threshold. | Protects intended maneuver |
| CAP-SYS-005 | The AEB trigger path shall execute with effective 20 ms cycle time and detect stale perception or actuation feedback within 40 ms. | Supports ASIL D timing |
| CAP-SYS-006 | The ECU shall inhibit activation or transition to degraded mode when critical sensor blockage, timeout, or actuation unavailability is present. | Defines safe gating |
| CAP-SYS-007 | The ECU shall provide HMI state outputs AVAILABLE, ACTIVE, SUPPRESSED, LIMITED, and FAULT to the cluster within 50 ms of state change. | Clarifies HMI ownership |
| CAP-SYS-008 | The ECU shall support authenticated OTA updates with compatibility checks, A/B image handling, and rollback on failed health checks. | Lifecycle safety |
| CAP-SYS-009 | The ECU shall record synchronized event snapshots for safety and debug use subject to privacy policy and retention rules. | Debugability with privacy discipline |
| CAP-SYS-010 | The ECU shall support variant coding for optional sensor packages without uncontrolled safety-behavior change. | Variant governance |
| CAP-SYS-011 | The ECU shall expose DTCs, freeze frames, health counters, software versions, and calibration identifiers via workshop and approved backend paths. | Diagnostics visibility |
| CAP-SYS-012 | The ECU shall segregate ASIL-relevant feature execution from QM logging and analytics by time and memory isolation. | Freedom from interference |

### 36.7 Expert solution — HARA

| Hazard ID | Operational situation | Malfunctioning behavior | Potential harm | S | E | C | Example ASIL |
|---|---|---|---|---|---|---|---|
| CAP-HE-001 | Highway closing speed behind slower vehicle | AEB/ACC path fails to decelerate when required | Rear-end collision with severe injury potential | S3 | E4 | C3 | ASIL D |
| CAP-HE-002 | Clear road at highway speed | AEB triggers false emergency braking | Rear impact or instability due to unexpected braking | S2 | E4 | C2 | ASIL C |
| CAP-HE-003 | Unintended lane departure | LKA fails to provide corrective support or timely warning | Lane departure and side collision | S3 | E4 | C2 | ASIL C |
| CAP-HE-004 | Intentional lane change | LKA resists driver maneuver | Driver surprise and unsafe trajectory | S2 | E4 | C2 | ASIL B |
| CAP-HE-005 | Sensor blocked or stale | Function remains active with undetected invalid perception | Incorrect control decision | S3 | E3 | C3 | ASIL D |
| CAP-HE-006 | OTA activation | Corrupted safety software image becomes active | Loss or corruption of ADAS safety behavior | S3 | E2 | C3 | ASIL D |
| CAP-HE-007 | High compute load | QM analytics delays safety-critical loop | Late intervention or missed handback | S3 | E3 | C3 | ASIL D |

### 36.8 Expert solution — safety goals

| ID | Safety goal | ASIL |
|---|---|---|
| CAP-SG-001 | Prevent failure to provide required emergency braking within the defined ODD. | ASIL D |
| CAP-SG-002 | Prevent hazardous false emergency braking. | ASIL C |
| CAP-SG-003 | Prevent unintended or inappropriate steering support. | ASIL D |
| CAP-SG-004 | Prevent operation with undetected critical sensor, communication, timing, or actuation faults. | ASIL D |
| CAP-SG-005 | Prevent activation of unauthorized or corrupted ADAS software/configuration. | ASIL D |
| CAP-SG-006 | Prevent mixed-criticality interference from violating safety timing. | ASIL D |

### 36.9 Expert solution — functional safety requirements

| ID | Functional safety requirement | Derived from |
|---|---|---|
| CAP-FSR-001 | Detect stale or invalid perception data used by the AEB path within 40 ms and inhibit autonomous braking if confidence cannot be restored. | CAP-SG-001, CAP-SG-004 |
| CAP-FSR-002 | Verify brake-path acknowledgement and observed deceleration response after emergency brake request. | CAP-SG-001 |
| CAP-FSR-003 | Cancel steering support within 100 ms of valid lane-change intent or driver torque override. | CAP-SG-003 |
| CAP-FSR-004 | Inhibit function activation on critical sensor blockage, timeout, or actuation unavailability and inform the driver. | CAP-SG-004 |
| CAP-FSR-005 | Protect ASIL partitions from QM logging/analytics interference by time and memory isolation. | CAP-SG-006 |
| CAP-FSR-006 | Authenticate software images and integrity-check configuration before execution, with rollback on failed health checks. | CAP-SG-005 |
| CAP-FSR-007 | Monitor loop deadline violations and command feature-specific safe state on overrun. | CAP-SG-006 |
| CAP-FSR-008 | Bound false braking through validated collision confidence, plausibility, and object persistence criteria. | CAP-SG-002 |

### 36.10 Expert solution — architecture decomposition

- Perception partition: sensor ingest, object/lane fusion, quality flags, timestamp supervision.
- Decision/control partition: ACC, AEB, and LKA state machines, arbitration, trigger logic, handback logic.
- Platform partition: timing supervision, diagnostics, NVM, logging, startup, watchdog, secure configuration.
- HMI partition: state reporting, warnings, limitation messages, event reason-code mapping.
- OTA/security partition: image trust, package compatibility, staged activation, rollback, certificate support.

### 36.11 Expert solution — key interfaces

| Interface ID | Producer → Consumer | Main contents | Timing / contract |
|---|---|---|---|
| CAP-IF-001 | Front radar → ADAS ECU | Tracked objects, quality, status, timestamps | 20 ms, freshness monitored within 40 ms |
| CAP-IF-002 | Front camera → ADAS ECU | Lane model, objects, blockage status, timestamps | 20 ms, freshness monitored within 40 ms |
| CAP-IF-003 | Brake system → ADAS ECU | Availability, acknowledgement, achieved decel, faults | 10 ms, acknowledgement path supervised |
| CAP-IF-004 | EPS → ADAS ECU | Availability, actual torque, steering feedback, faults | 10 ms, cancellation contract <= 100 ms |
| CAP-IF-005 | ADAS ECU → Cluster | Feature states, warnings, limitation and fault IDs | 50 ms on state change |
| CAP-IF-006 | Gateway → ADAS ECU | Vehicle speed, yaw, turn signal, power mode, network policy | 10–20 ms with timestamps |
| CAP-IF-007 | TCU / OTA manager → ADAS ECU | Manifest, package metadata, install trigger, result reporting | Event driven, authenticated |
| CAP-IF-008 | Service tool ↔ ADAS ECU | UDS/DoIP DTCs, freeze frames, DID reads, routines | On request with state gating |

### 36.12 Expert solution — timing budget example

| Path | Example budget | Why it matters |
|---|---|---|
| Sensor ingest to validated perception availability | 20 ms | Protects AEB/LKA decision quality |
| AEB decision path | 10 ms | Supports rapid intervention |
| Brake request output serialization | 10 ms | Preserves total braking latency budget |
| Brake feedback supervision | 50 ms | Detects actuation failure |
| LKA lane model to torque request | 20 ms | Supports stable lateral support |
| Brake override to ACC disengage | 100 ms max | Preserves driver authority |
| Turn intent or driver torque override to LKA cancel | 100 ms max | Prevents resistance to intended maneuver |
| State change to cluster indication | 50 ms | Maintains clear user feedback |

### 36.13 Expert solution — diagnostics strategy

| Diagnostic area | Example requirement | Expected evidence |
|---|---|---|
| Sensor health | Detect blockage, timeout, misalignment, implausibility, timestamp drift. | DTC, limitation state, freeze frame |
| Actuation path | Detect brake/EPS refusal, timeout, or implausible feedback. | DTC, inhibition reason, safe-state log |
| Platform health | Detect watchdog, deadline miss, memory ECC, partition overload. | Reset reason, counters, platform DTCs |
| Communication | Detect missing counters, CRC mismatch, bus or Ethernet errors. | Communication health and DTCs |
| Update health | Record manifest validation, install outcome, rollback reason. | Campaign history, signed result |
| Service support | Expose versions, calibrations, last disengagement causes, event counters. | DIDs, routines, service manual alignment |

### 36.14 Expert solution — traceability chain

```text
OEM Need
  ↓
Stakeholder Need
  ↓
Vehicle / Item Requirement
  ↓
System Requirement
  ↘
   HARA → Safety Goal → FSR → TSR Theme
  ↓
Architecture Allocation
  ↓
Subsystem / SW / HW / Interface Requirement
  ↓
Test Requirement → Test Case → Result
  ↓
Release Evidence
```

| Example upstream item | Example downstream chain |
|---|---|
| OEM-ADAS-004 | CAP-SYS-003 → brake-override logic → HIL timing test → release evidence for driver authority |
| OEM-ADAS-008 | CAP-HE-001 → CAP-SG-001 → CAP-FSR-001/002 → ASIL D verification campaign |
| OEM-ADAS-007 | CAP-SYS-008 → update trust and rollback requirements → package integrity test → operational signoff |
| OEM-ADAS-010 | CAP-SYS-009 → logging/privacy rules → retention tests → legal approval |
| OEM-ADAS-014 | CAP-SYS-006 → sensor-fault FSRs → fault-injection tests → degraded-mode validation |

### 36.15 Expert solution — requirement-based test cases

| Test case | Linked requirement | Intent | Level |
|---|---|---|---|
| CAP-TC-001 | CAP-SYS-002 | Verify startup readiness timing with healthy dependencies. | HIL / vehicle |
| CAP-TC-002 | CAP-SYS-003 | Verify brake override disengages longitudinal control within 100 ms. | HIL |
| CAP-TC-003 | CAP-FSR-001 | Inject stale radar/camera timestamps and verify AEB inhibition. | SIL/HIL fault injection |
| CAP-TC-004 | CAP-FSR-002 | Force brake acknowledgement failure and verify intervention-failed handling. | HIL |
| CAP-TC-005 | CAP-SYS-004 | Verify turn-indicator intent and driver torque override cancel LKA within 100 ms. | HIL / vehicle |
| CAP-TC-006 | CAP-SYS-007 | Verify cluster state transitions AVAILABLE, ACTIVE, LIMITED, FAULT. | Integration |
| CAP-TC-007 | CAP-SYS-008 | Perform corrupted OTA package attempt and verify rejection/rollback. | System |
| CAP-TC-008 | CAP-SYS-009 | Verify event snapshots are synchronized and privacy-compliant. | System |
| CAP-TC-009 | CAP-SYS-011 | Verify DTCs, freeze frames, versions, and identifiers are accessible. | Service integration |
| CAP-TC-010 | CAP-FSR-005, CAP-FSR-007 | Stress QM logging and verify ASIL loops maintain deadlines. | Platform/HIL |

### 36.16 Expert solution — fault-injection tests

| Fault ID | Injected fault | Expected safe behavior |
|---|---|---|
| FI-001 | Stale radar object stream | AEB/ACC inhibit or degrade and log reason |
| FI-002 | Implausible lane-model jump | LKA safe-off with limitation indication |
| FI-003 | Brake acknowledgement missing | Intervention failure detected and logged |
| FI-004 | EPS feedback stuck value | LKA support cancelled on monitor trip |
| FI-005 | QM partition CPU starvation attempt | ASIL loop protection and timing-monitor action |
| FI-006 | Corrupted OTA manifest | Update rejected before activation |
| FI-007 | Turn-signal message loss | Driver torque override remains effective; state logic handles missing intent signal safely |
| FI-008 | NVM checksum mismatch on startup | Safe initialization and feature inhibition until integrity restored |

### 36.17 Expert solution — verification strategy

- Review-driven verification: requirement, architecture, interface, safety, and traceability reviews.
- Model/SIL verification: scenario replay, edge-case coverage, numerical and state-machine checks.
- Platform verification: startup, partitioning, watchdog, diagnostics, and update infrastructure checks.
- HIL verification: realistic network timing, actuator acknowledgements, and fault-monitor behavior.
- Vehicle verification: proving-ground and road behavior, state displays, and integration realism.
- Release verification: regression completeness, defect review, configuration freeze, and evidence integrity.

### 36.18 Expert solution — validation strategy

- Customer validation confirms trust, low nuisance behavior, and understandable handback.
- Operational validation confirms ODD boundaries across realistic traffic, weather, and road conditions.
- Service validation confirms DTC usefulness, diagnosis speed, and update-recovery workflows.
- Privacy/legal validation confirms the logging package follows data governance rules.
- Fleet validation confirms false-trigger rates, limitation rates, and update success rates at population scale.

### 36.19 Expert solution — handling conflicts

| Conflict | Resolution principle |
|---|---|
| Safety vs comfort | Safety goals are non-negotiable; comfort is tuned inside the safe envelope. |
| Logging depth vs privacy/storage | Define event classes, retention windows, and access rights explicitly. |
| Reuse vs performance | Reuse is acceptable only after gap analysis against timing, safety, and integration requirements. |
| Availability vs false positives | Use explicit activation gating, confidence thresholds, and scenario-based validation metrics. |
| OTA flexibility vs release safety | Remote updates require strict trust chain, health checks, and rollback evidence. |

### 36.20 Expert solution — release evidence package

| Evidence element | Minimum content |
|---|---|
| Requirement baseline | Approved stakeholder, system, interface, diagnostics, and variant requirement package |
| Safety evidence | Approved HARA, safety goals, FSR set, safety verification summary, residual risk record |
| Architecture evidence | Item definition, block diagrams, partitioning rationale, timing budgets, ICD baseline |
| Test evidence | Requirement coverage, HIL/SIL/system reports, fault injection reports, regression summary |
| Validation evidence | Vehicle and fleet acceptance summaries with unresolved-risk disposition |
| Configuration evidence | Software versions, calibration IDs, variant matrix, package checksums, release notes |
| Service evidence | DTC list, DID list, routines, workshop procedures, event-log interpretation guidance |
| Operational evidence | Monitoring KPIs, rollback criteria, incident-response process, post-launch analytics plan |

### 36.21 Capstone success criteria

- The learner identifies ambiguity rather than polishing ambiguous text.
- The learner writes measurable requirements rather than vague design wishes.
- The learner builds a visible safety chain rather than only naming ASIL labels.
- The learner defines interfaces with timing and ownership rather than only naming buses.
- The learner creates tests from requirements rather than from implementation guesses.
- The learner finishes with release evidence, not only with requirement tables.

---

## 37. REQUIREMENTS + FUNCTIONAL SAFETY + TESTING MASTER CHAIN

### 37.1 The chain

```text
STAKEHOLDER NEED
→ REQUIREMENT
→ SYSTEM ANALYSIS
→ HARA
→ SAFETY GOAL
→ FSR
→ TSR
→ SYSTEM REQUIREMENT
→ ARCHITECTURE
→ SW/HW REQUIREMENT
→ IMPLEMENTATION
→ VERIFICATION
→ FAULT INJECTION
→ HIL/SIL
→ SYSTEM VALIDATION
→ VEHICLE VALIDATION
→ SAFETY CASE
→ RELEASE
```

### 37.2 Why every arrow exists

| Arrow | Why it exists |
|---|---|
| Stakeholder Need → Requirement | Engineering cannot safely design or test vague intent; needs must become explicit, reviewable statements. |
| Requirement → System Analysis | Written text must be checked for feasibility, completeness, dependencies, and assumptions. |
| System Analysis → HARA | Hazards can only be assessed once functions, contexts, and boundaries are understood. |
| HARA → Safety Goal | Hazards must be turned into high-level safety intent that the item is obligated to satisfy. |
| Safety Goal → FSR | High-level safety intent is too abstract for engineering allocation; FSRs make it actionable. |
| FSR → TSR | Functional safety obligations need technical realization in architecture, interfaces, timing, and mechanisms. |
| TSR → System Requirement | Safety must be integrated into the main engineering baseline, not kept in a separate universe. |
| System Requirement → Architecture | Requirements say what must happen; architecture says where responsibilities live and how they interact. |
| Architecture → SW/HW Requirement | Allocated blocks need implementable software, hardware, interface, and diagnostic requirements. |
| SW/HW Requirement → Implementation | Implementation is the physical and software realization of the allocated requirement set. |
| Implementation → Verification | Built artifacts must be checked against the requirements that justified them. |
| Verification → Fault Injection | Normal testing alone does not prove the safety concept handles failures correctly. |
| Fault Injection → HIL/SIL | Faults need realistic dynamic environments to expose interaction effects before vehicle risk is accepted. |
| HIL/SIL → System Validation | Lab success does not guarantee user or vehicle-level suitability in realistic use. |
| System Validation → Vehicle Validation | Only the full vehicle reveals final timing, human factors, noise, and dynamics interactions. |
| Vehicle Validation → Safety Case | Results, analyses, and requirements must be organized into a justified argument about acceptable residual risk. |
| Safety Case → Release | Release decisions should be evidence-driven, not intuition-driven. |

### 37.3 Why the chain fails in weak programs

- Teams jump directly from OEM wish-lists to software tasks, leaving system assumptions unowned.
- HARA is treated as paperwork after architecture is frozen, so safety goals do not shape design.
- Interfaces are named but not contracted, causing expensive integration churn.
- Diagnostics and degraded modes are treated as implementation leftovers rather than requirements.
- Testing emphasizes nominal behavior and underinvests in fault injection and operational validation.
- Release decisions rely on schedule pressure rather than traceable evidence sufficiency.

### 37.4 Master-chain reinforcement rules

1. Every low-level artifact must have an upstream reason to exist.
2. Every critical upstream requirement must have a downstream implementation and test path.
3. Every safety claim must have evidence and assumptions explicitly named.
4. Every interface must be testable independently of the rest of the design where practical.
5. Every change must identify which arrows in the chain are affected.

---

## 38. FINAL COMPETENCY MATRIX

### 38.1 Level definitions

| Level | Description |
|---|---|
| Beginner | Follows templates and contributes correctly with close guidance. |
| Engineer | Owns bounded scope independently and produces reviewed work products. |
| Senior | Owns complex scope end to end, anticipates gaps, and mentors others. |
| Lead | Directs cross-team decisions, governance, and release-quality alignment. |
| Architect | Defines platform patterns, strategy, and scalable assurance frameworks. |

### 38.2 Matrix overview

| Skill | Beginner | Engineer | Senior | Lead | Architect |
|---|---|---|---|---|---|
| Requirement Elicitation | Captures direct stakeholder statements and asks basic clarifying questions. | Plans elicitation sessions and extracts scenarios and constraints for a subsystem. | Surfaces latent needs from safety, service, manufacturing, and validation stakeholders. | Builds cross-team elicitation strategy and closes scope gaps systematically. | Defines enterprise intake patterns, scenario libraries, and governance. |
| Requirement Analysis | Checks ambiguity, missing units, and obvious conflicts. | Performs feasibility and dependency analysis for bounded scope. | Runs cross-discipline impact analysis spanning safety, architecture, and validation. | Directs conflict resolution and decision logging across teams. | Defines large-scale analysis methods and review gates for platforms. |
| Requirement Writing | Writes simple atomic requirements with approved patterns. | Writes measurable subsystem and system requirements with triggers and tolerances. | Produces coherent requirement sets anticipating test, safety, and variant impacts. | Defines writing standards, examples, and review criteria for teams and suppliers. | Creates reusable authoring taxonomies and organizational patterns. |
| Traceability | Maintains basic parent-child and test links. | Ensures bidirectional traceability across stakeholder, system, SW/HW, interface, and tests. | Uses traceability to drive completeness and impact analysis. | Implements dashboards for missing links, orphan tests, and baseline drift. | Defines digital-thread trace models spanning platforms and compliance evidence. |
| HARA | Participates in workshops and understands S/E/C concepts. | Documents hazards, situations, malfunctioning behavior, and ASIL rationale. | Challenges item boundaries and ensures HARA outputs drive architecture and tests. | Facilitates cross-functional HARA consistency and escalation. | Defines reusable hazard patterns and enterprise scenario catalogs. |
| ISO 26262 | Knows key terms such as item, ASIL, safety goal, and FSR. | Supports item definition, FSC/TSC artifacts, and requirement allocation. | Drives safety concept maturation and supplier alignment. | Owns safety planning and evidence integration across programs. | Defines platform safety patterns and reusable safety mechanisms. |
| ASPICE | Understands SYS.2/SWE.1 expectations and follows process. | Produces compliant baselines, reviews, and traceability. | Improves product quality using ASPICE intent rather than checklist-only thinking. | Coordinates assessment readiness, tailoring, and supplier process closure. | Shapes organization-wide process architecture and evidence automation. |
| Test Strategy | Links requirements to straightforward tests. | Builds requirement-based test sets across SIL/HIL/system levels. | Creates risk-based verification strategy including degraded and misuse scenarios. | Balances evidence sufficiency, cost, and release timing across teams. | Defines enterprise validation architecture and evidence reuse patterns. |
| Fault Injection | Understands why faults are injected. | Designs subsystem-level campaigns for timeouts, stale data, and monitor trips. | Uses injected results to challenge safety assumptions and diagnostic coverage. | Integrates fault-injection evidence into release and safety-case decisions. | Defines reusable fault models and campaign libraries across platforms. |
| System Architecture | Reads architecture diagrams and allocations. | Defines subsystem decomposition, interfaces, and timing budgets. | Optimizes architecture for safety, performance, and serviceability. | Leads trade studies and cross-domain integration decisions. | Creates reference architectures and platform evolution roadmaps. |
| Safety Case | Understands that claims require evidence. | Contributes reviewed requirement, test, and analysis evidence. | Builds coherent argument threads from hazards to validation results. | Owns safety-case completeness and review readiness. | Defines reusable argument patterns and evidence taxonomies. |
| Stakeholder Management | Communicates status and questions clearly to local team. | Coordinates clarifications with system, safety, SW, test, and customer representatives. | Negotiates conflicting priorities with evidence-based trade-offs. | Manages executive, supplier, and milestone expectations. | Shapes long-term alignment between strategy, standards, and engineering organizations. |
| Change Management | Understands baselines and approved changes. | Performs impact analysis and updates linked artifacts. | Drives change boards for subsystem scope and evidence closure. | Owns release governance, deviation handling, and configuration control. | Defines scalable change-control frameworks and product-line baseline strategy. |

### 38.3 Detailed competency expectations

#### Requirement Elicitation

**Definition**: Discovering explicit and latent needs from OEMs, suppliers, users, standards, service, and validation stakeholders.

- **Beginner**: Captures direct stakeholder statements and asks basic clarifying questions.
- **Engineer**: Plans elicitation sessions and extracts scenarios and constraints for a subsystem.
- **Senior**: Surfaces latent needs from safety, service, manufacturing, and validation stakeholders.
- **Lead**: Builds cross-team elicitation strategy and closes scope gaps systematically.
- **Architect**: Defines enterprise intake patterns, scenario libraries, and governance.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Requirement Analysis

**Definition**: Checking feasibility, completeness, conflicts, assumptions, and downstream impacts.

- **Beginner**: Checks ambiguity, missing units, and obvious conflicts.
- **Engineer**: Performs feasibility and dependency analysis for bounded scope.
- **Senior**: Runs cross-discipline impact analysis spanning safety, architecture, and validation.
- **Lead**: Directs conflict resolution and decision logging across teams.
- **Architect**: Defines large-scale analysis methods and review gates for platforms.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Requirement Writing

**Definition**: Producing atomic, testable, unambiguous, implementation-appropriate requirements.

- **Beginner**: Writes simple atomic requirements with approved patterns.
- **Engineer**: Writes measurable subsystem and system requirements with triggers and tolerances.
- **Senior**: Produces coherent requirement sets anticipating test, safety, and variant impacts.
- **Lead**: Defines writing standards, examples, and review criteria for teams and suppliers.
- **Architect**: Creates reusable authoring taxonomies and organizational patterns.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Traceability

**Definition**: Maintaining verifiable links from stakeholder intent to release evidence.

- **Beginner**: Maintains basic parent-child and test links.
- **Engineer**: Ensures bidirectional traceability across stakeholder, system, SW/HW, interface, and tests.
- **Senior**: Uses traceability to drive completeness and impact analysis.
- **Lead**: Implements dashboards for missing links, orphan tests, and baseline drift.
- **Architect**: Defines digital-thread trace models spanning platforms and compliance evidence.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### HARA

**Definition**: Identifying hazards, operational situations, malfunctioning behavior, and ASIL classification.

- **Beginner**: Participates in workshops and understands S/E/C concepts.
- **Engineer**: Documents hazards, situations, malfunctioning behavior, and ASIL rationale.
- **Senior**: Challenges item boundaries and ensures HARA outputs drive architecture and tests.
- **Lead**: Facilitates cross-functional HARA consistency and escalation.
- **Architect**: Defines reusable hazard patterns and enterprise scenario catalogs.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### ISO 26262

**Definition**: Applying item definition, safety goals, FSRs, TSRs, safety mechanisms, and evidence.

- **Beginner**: Knows key terms such as item, ASIL, safety goal, and FSR.
- **Engineer**: Supports item definition, FSC/TSC artifacts, and requirement allocation.
- **Senior**: Drives safety concept maturation and supplier alignment.
- **Lead**: Owns safety planning and evidence integration across programs.
- **Architect**: Defines platform safety patterns and reusable safety mechanisms.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### ASPICE

**Definition**: Applying SYS.2, SYS.3, SWE.1, verification, change, and configuration expectations.

- **Beginner**: Understands SYS.2/SWE.1 expectations and follows process.
- **Engineer**: Produces compliant baselines, reviews, and traceability.
- **Senior**: Improves product quality using ASPICE intent rather than checklist-only thinking.
- **Lead**: Coordinates assessment readiness, tailoring, and supplier process closure.
- **Architect**: Shapes organization-wide process architecture and evidence automation.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Test Strategy

**Definition**: Planning unit, integration, SIL, HIL, vehicle, robustness, and release verification.

- **Beginner**: Links requirements to straightforward tests.
- **Engineer**: Builds requirement-based test sets across SIL/HIL/system levels.
- **Senior**: Creates risk-based verification strategy including degraded and misuse scenarios.
- **Lead**: Balances evidence sufficiency, cost, and release timing across teams.
- **Architect**: Defines enterprise validation architecture and evidence reuse patterns.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Fault Injection

**Definition**: Designing and interpreting fault campaigns for sensors, timing, communication, and actuation.

- **Beginner**: Understands why faults are injected.
- **Engineer**: Designs subsystem-level campaigns for timeouts, stale data, and monitor trips.
- **Senior**: Uses injected results to challenge safety assumptions and diagnostic coverage.
- **Lead**: Integrates fault-injection evidence into release and safety-case decisions.
- **Architect**: Defines reusable fault models and campaign libraries across platforms.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### System Architecture

**Definition**: Structuring functions, interfaces, allocations, timing, and degradation concepts.

- **Beginner**: Reads architecture diagrams and allocations.
- **Engineer**: Defines subsystem decomposition, interfaces, and timing budgets.
- **Senior**: Optimizes architecture for safety, performance, and serviceability.
- **Lead**: Leads trade studies and cross-domain integration decisions.
- **Architect**: Creates reference architectures and platform evolution roadmaps.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Safety Case

**Definition**: Assembling evidence and structured argument that residual risk is acceptable.

- **Beginner**: Understands that claims require evidence.
- **Engineer**: Contributes reviewed requirement, test, and analysis evidence.
- **Senior**: Builds coherent argument threads from hazards to validation results.
- **Lead**: Owns safety-case completeness and review readiness.
- **Architect**: Defines reusable argument patterns and evidence taxonomies.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Stakeholder Management

**Definition**: Negotiating scope, resolving ambiguity, and aligning OEM/Tier-1/domain teams.

- **Beginner**: Communicates status and questions clearly to local team.
- **Engineer**: Coordinates clarifications with system, safety, SW, test, and customer representatives.
- **Senior**: Negotiates conflicting priorities with evidence-based trade-offs.
- **Lead**: Manages executive, supplier, and milestone expectations.
- **Architect**: Shapes long-term alignment between strategy, standards, and engineering organizations.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

#### Change Management

**Definition**: Baseline control, impact analysis, deviation handling, and release governance.

- **Beginner**: Understands baselines and approved changes.
- **Engineer**: Performs impact analysis and updates linked artifacts.
- **Senior**: Drives change boards for subsystem scope and evidence closure.
- **Lead**: Owns release governance, deviation handling, and configuration control.
- **Architect**: Defines scalable change-control frameworks and product-line baseline strategy.

**How this skill becomes visible in real work**

- The engineer can explain why each work product exists, not only how to fill the template.
- The engineer can challenge ambiguity before implementation consumes it.
- The engineer can connect the skill to safety, testing, and release consequences.
- The engineer can mentor others using examples, reviews, and decision rationale.

### 38.4 Interpreting progression from Beginner to Architect

- Growth is not only about knowing more terminology; it is about handling more ambiguity, more cross-team coupling, and more release consequence.
- Senior engineers prevent problems that Engineers might only discover later.
- Leads and Architects optimize the system around evidence, governance, reuse, and strategic consistency.
- Competency should be evaluated through reviewed deliverables and release outcomes, not training attendance alone.

---

## 39. FINAL LEARNING OUTCOME

### 39.1 Complete learner profile

By the end of this material, the learner is prepared to operate as a combined:

- **Senior Automotive Requirements Engineer**
- **Functional Safety Engineer**
- **Safety Validation Strategist**

with practical literacy across **ADAS**, **Telematics**, **Instrument Cluster/HMI**, and **Vehicle E/E Architecture** including gateway and zonal platforms.

### 39.2 Capabilities and expected competencies

- Translate ambiguous stakeholder requests into measurable, auditable requirement baselines.
- Decompose needs through vehicle, system, subsystem, software, hardware, interface, and test layers.
- Run requirement reviews that detect ambiguity, hidden assumptions, and solution bias early.
- Perform or strongly support HARA and derive safety goals and practical safety requirements.
- Define interfaces with timing, ownership, validity, diagnostics, and degraded-mode expectations.
- Create verification strategies spanning review, SIL, HIL, vehicle, fault injection, and service evidence.
- Create validation strategies spanning customer value, legal interpretation, service readiness, and fleet robustness.
- Manage change with disciplined impact analysis and baseline control.
- Prepare release evidence packages that support rational production decisions.
- Bridge requirements, architecture, safety, software, hardware, test, and service teams using shared engineering logic.

### 39.3 Detailed final competency table

| Area | Final expected competence |
|---|---|
| Requirement elicitation | Can independently lead workshops and extract operational scenarios, constraints, and acceptance criteria. |
| Requirement analysis | Can uncover conflicts, missing ODD boundaries, unbounded timing, and unspecified diagnostics. |
| Requirement writing | Can produce atomic, measurable requirements suitable for system, SW, HW, interface, safety, and test use. |
| Safety engineering | Can connect hazards to safety goals, FSRs, monitors, inhibitions, and evidence. |
| Architecture thinking | Can decompose functions across ECUs, partitions, networks, and services while preserving timing and safety intent. |
| Testing mindset | Can derive requirement-based and fault-injection tests from engineering intent rather than implementation convenience. |
| Serviceability | Can ensure DTCs, freeze frames, service routines, and field logs are actually usable by workshops and analytics teams. |
| Lifecycle discipline | Can manage versions, variants, updates, rollback evidence, and release governance under pressure. |
| Cross-functional leadership | Can negotiate trade-offs among safety, comfort, cost, reuse, schedule, privacy, and manufacturability. |
| Release readiness | Can judge whether the chain from requirement to evidence is strong enough for responsible release. |

### 39.4 Final professional identity

- You can own the **front end** of engineering: stakeholder understanding, ambiguity removal, and requirement creation.
- You can own the **middle** of engineering: architecture allocation, interface definition, diagnostics, and decomposition.
- You can influence the **back end** of engineering: test strategy, validation, release evidence, and field feedback loops.
- You can bridge the silos between requirements, safety, architecture, software, hardware, service, and testing.
- You act not merely as a requirement author, but as a guardian of engineering intent from concept to release.

### 39.5 Final statement

A mature automotive requirements engineer does more than write sentences. The mature engineer protects the chain from need to release. They know why the product exists, how it can fail, how the design is structured, how the evidence is built, and how the organization can release it responsibly. That integrated capability is the final learning outcome of this guide.

---

## Appendix A — Reusable requirement review checklist

1. Is the subject explicit?
2. Is the trigger explicit?
3. Is the required response measurable?
4. Are units, tolerances, and limits present?
5. Is timing/freshness specified where relevant?
6. Is degraded behavior defined?
7. Is diagnostic behavior defined?
8. Is the requirement testable?
9. Is the requirement traceable?
10. Is the requirement free of hidden design bias?

## Appendix B — Reusable verification checklist

1. Requirement review complete
2. Interface review complete
3. Safety review complete
4. Traceability report generated
5. SIL results reviewed
6. HIL results reviewed
7. Fault injection reviewed
8. Open defects dispositioned
9. Configuration baseline frozen
10. Release note draft prepared

## Appendix C — Reusable validation checklist

1. Customer scenarios covered
2. ODD boundary scenarios covered
3. Service workflows rehearsed
4. Legal interpretation confirmed
5. Fleet monitoring KPIs defined
6. Regional variant differences validated
7. Driver/operator HMI understanding validated
8. Degraded modes validated
9. Update/recovery behavior validated
10. Warranty/field feedback path prepared

## Appendix D — Adaptive Cruise Control micro-lessons

- ACC-ML-01: Start from stakeholder scenarios before debating implementation.
- ACC-ML-02: Write operating-domain assumptions explicitly.
- ACC-ML-03: State timing expectations before integration begins.
- ACC-ML-04: Define diagnostics as requirements, not as optional extras.
- ACC-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- ACC-ML-06: Safety requirements must live inside the main engineering baseline.
- ACC-ML-07: Degraded behavior must be designed, reviewed, and validated.
- ACC-ML-08: Fault injection reveals whether monitors really work.
- ACC-ML-09: Service and update workflows are part of product quality.
- ACC-ML-10: A release is only as strong as its traceability and evidence closure.
- ACC-ML-11: Calibration changes can have requirement-level consequences.
- ACC-ML-12: Version and variant identity must be visible in tools and logs.
- ACC-ML-13: Review comments are valuable when they remove ambiguity early.
- ACC-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- ACC-ML-15: Requirement IDs should be stable across the project lifecycle.
- ACC-ML-16: A clear safe state is better than an unexplained limitation.
- ACC-ML-17: Event logs should be understandable to both developers and service engineers.
- ACC-ML-18: Tests should be derived before late implementation bias narrows imagination.
- ACC-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- ACC-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Automatic Emergency Braking micro-lessons

- AEB-ML-01: Start from stakeholder scenarios before debating implementation.
- AEB-ML-02: Write operating-domain assumptions explicitly.
- AEB-ML-03: State timing expectations before integration begins.
- AEB-ML-04: Define diagnostics as requirements, not as optional extras.
- AEB-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- AEB-ML-06: Safety requirements must live inside the main engineering baseline.
- AEB-ML-07: Degraded behavior must be designed, reviewed, and validated.
- AEB-ML-08: Fault injection reveals whether monitors really work.
- AEB-ML-09: Service and update workflows are part of product quality.
- AEB-ML-10: A release is only as strong as its traceability and evidence closure.
- AEB-ML-11: Calibration changes can have requirement-level consequences.
- AEB-ML-12: Version and variant identity must be visible in tools and logs.
- AEB-ML-13: Review comments are valuable when they remove ambiguity early.
- AEB-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- AEB-ML-15: Requirement IDs should be stable across the project lifecycle.
- AEB-ML-16: A clear safe state is better than an unexplained limitation.
- AEB-ML-17: Event logs should be understandable to both developers and service engineers.
- AEB-ML-18: Tests should be derived before late implementation bias narrows imagination.
- AEB-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- AEB-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Lane Keeping Assist micro-lessons

- LKA-ML-01: Start from stakeholder scenarios before debating implementation.
- LKA-ML-02: Write operating-domain assumptions explicitly.
- LKA-ML-03: State timing expectations before integration begins.
- LKA-ML-04: Define diagnostics as requirements, not as optional extras.
- LKA-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- LKA-ML-06: Safety requirements must live inside the main engineering baseline.
- LKA-ML-07: Degraded behavior must be designed, reviewed, and validated.
- LKA-ML-08: Fault injection reveals whether monitors really work.
- LKA-ML-09: Service and update workflows are part of product quality.
- LKA-ML-10: A release is only as strong as its traceability and evidence closure.
- LKA-ML-11: Calibration changes can have requirement-level consequences.
- LKA-ML-12: Version and variant identity must be visible in tools and logs.
- LKA-ML-13: Review comments are valuable when they remove ambiguity early.
- LKA-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- LKA-ML-15: Requirement IDs should be stable across the project lifecycle.
- LKA-ML-16: A clear safe state is better than an unexplained limitation.
- LKA-ML-17: Event logs should be understandable to both developers and service engineers.
- LKA-ML-18: Tests should be derived before late implementation bias narrows imagination.
- LKA-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- LKA-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — ADAS Domain Controller micro-lessons

- ADC-ML-01: Start from stakeholder scenarios before debating implementation.
- ADC-ML-02: Write operating-domain assumptions explicitly.
- ADC-ML-03: State timing expectations before integration begins.
- ADC-ML-04: Define diagnostics as requirements, not as optional extras.
- ADC-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- ADC-ML-06: Safety requirements must live inside the main engineering baseline.
- ADC-ML-07: Degraded behavior must be designed, reviewed, and validated.
- ADC-ML-08: Fault injection reveals whether monitors really work.
- ADC-ML-09: Service and update workflows are part of product quality.
- ADC-ML-10: A release is only as strong as its traceability and evidence closure.
- ADC-ML-11: Calibration changes can have requirement-level consequences.
- ADC-ML-12: Version and variant identity must be visible in tools and logs.
- ADC-ML-13: Review comments are valuable when they remove ambiguity early.
- ADC-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- ADC-ML-15: Requirement IDs should be stable across the project lifecycle.
- ADC-ML-16: A clear safe state is better than an unexplained limitation.
- ADC-ML-17: Event logs should be understandable to both developers and service engineers.
- ADC-ML-18: Tests should be derived before late implementation bias narrows imagination.
- ADC-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- ADC-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Telematics Control Unit micro-lessons

- TCU-ML-01: Start from stakeholder scenarios before debating implementation.
- TCU-ML-02: Write operating-domain assumptions explicitly.
- TCU-ML-03: State timing expectations before integration begins.
- TCU-ML-04: Define diagnostics as requirements, not as optional extras.
- TCU-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- TCU-ML-06: Safety requirements must live inside the main engineering baseline.
- TCU-ML-07: Degraded behavior must be designed, reviewed, and validated.
- TCU-ML-08: Fault injection reveals whether monitors really work.
- TCU-ML-09: Service and update workflows are part of product quality.
- TCU-ML-10: A release is only as strong as its traceability and evidence closure.
- TCU-ML-11: Calibration changes can have requirement-level consequences.
- TCU-ML-12: Version and variant identity must be visible in tools and logs.
- TCU-ML-13: Review comments are valuable when they remove ambiguity early.
- TCU-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- TCU-ML-15: Requirement IDs should be stable across the project lifecycle.
- TCU-ML-16: A clear safe state is better than an unexplained limitation.
- TCU-ML-17: Event logs should be understandable to both developers and service engineers.
- TCU-ML-18: Tests should be derived before late implementation bias narrows imagination.
- TCU-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- TCU-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — eCall System micro-lessons

- ECALL-ML-01: Start from stakeholder scenarios before debating implementation.
- ECALL-ML-02: Write operating-domain assumptions explicitly.
- ECALL-ML-03: State timing expectations before integration begins.
- ECALL-ML-04: Define diagnostics as requirements, not as optional extras.
- ECALL-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- ECALL-ML-06: Safety requirements must live inside the main engineering baseline.
- ECALL-ML-07: Degraded behavior must be designed, reviewed, and validated.
- ECALL-ML-08: Fault injection reveals whether monitors really work.
- ECALL-ML-09: Service and update workflows are part of product quality.
- ECALL-ML-10: A release is only as strong as its traceability and evidence closure.
- ECALL-ML-11: Calibration changes can have requirement-level consequences.
- ECALL-ML-12: Version and variant identity must be visible in tools and logs.
- ECALL-ML-13: Review comments are valuable when they remove ambiguity early.
- ECALL-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- ECALL-ML-15: Requirement IDs should be stable across the project lifecycle.
- ECALL-ML-16: A clear safe state is better than an unexplained limitation.
- ECALL-ML-17: Event logs should be understandable to both developers and service engineers.
- ECALL-ML-18: Tests should be derived before late implementation bias narrows imagination.
- ECALL-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- ECALL-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Over-the-Air Update System micro-lessons

- OTA-ML-01: Start from stakeholder scenarios before debating implementation.
- OTA-ML-02: Write operating-domain assumptions explicitly.
- OTA-ML-03: State timing expectations before integration begins.
- OTA-ML-04: Define diagnostics as requirements, not as optional extras.
- OTA-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- OTA-ML-06: Safety requirements must live inside the main engineering baseline.
- OTA-ML-07: Degraded behavior must be designed, reviewed, and validated.
- OTA-ML-08: Fault injection reveals whether monitors really work.
- OTA-ML-09: Service and update workflows are part of product quality.
- OTA-ML-10: A release is only as strong as its traceability and evidence closure.
- OTA-ML-11: Calibration changes can have requirement-level consequences.
- OTA-ML-12: Version and variant identity must be visible in tools and logs.
- OTA-ML-13: Review comments are valuable when they remove ambiguity early.
- OTA-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- OTA-ML-15: Requirement IDs should be stable across the project lifecycle.
- OTA-ML-16: A clear safe state is better than an unexplained limitation.
- OTA-ML-17: Event logs should be understandable to both developers and service engineers.
- OTA-ML-18: Tests should be derived before late implementation bias narrows imagination.
- OTA-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- OTA-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Digital Instrument Cluster micro-lessons

- CLUSTER-ML-01: Start from stakeholder scenarios before debating implementation.
- CLUSTER-ML-02: Write operating-domain assumptions explicitly.
- CLUSTER-ML-03: State timing expectations before integration begins.
- CLUSTER-ML-04: Define diagnostics as requirements, not as optional extras.
- CLUSTER-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- CLUSTER-ML-06: Safety requirements must live inside the main engineering baseline.
- CLUSTER-ML-07: Degraded behavior must be designed, reviewed, and validated.
- CLUSTER-ML-08: Fault injection reveals whether monitors really work.
- CLUSTER-ML-09: Service and update workflows are part of product quality.
- CLUSTER-ML-10: A release is only as strong as its traceability and evidence closure.
- CLUSTER-ML-11: Calibration changes can have requirement-level consequences.
- CLUSTER-ML-12: Version and variant identity must be visible in tools and logs.
- CLUSTER-ML-13: Review comments are valuable when they remove ambiguity early.
- CLUSTER-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- CLUSTER-ML-15: Requirement IDs should be stable across the project lifecycle.
- CLUSTER-ML-16: A clear safe state is better than an unexplained limitation.
- CLUSTER-ML-17: Event logs should be understandable to both developers and service engineers.
- CLUSTER-ML-18: Tests should be derived before late implementation bias narrows imagination.
- CLUSTER-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- CLUSTER-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Vehicle Gateway micro-lessons

- GATEWAY-ML-01: Start from stakeholder scenarios before debating implementation.
- GATEWAY-ML-02: Write operating-domain assumptions explicitly.
- GATEWAY-ML-03: State timing expectations before integration begins.
- GATEWAY-ML-04: Define diagnostics as requirements, not as optional extras.
- GATEWAY-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- GATEWAY-ML-06: Safety requirements must live inside the main engineering baseline.
- GATEWAY-ML-07: Degraded behavior must be designed, reviewed, and validated.
- GATEWAY-ML-08: Fault injection reveals whether monitors really work.
- GATEWAY-ML-09: Service and update workflows are part of product quality.
- GATEWAY-ML-10: A release is only as strong as its traceability and evidence closure.
- GATEWAY-ML-11: Calibration changes can have requirement-level consequences.
- GATEWAY-ML-12: Version and variant identity must be visible in tools and logs.
- GATEWAY-ML-13: Review comments are valuable when they remove ambiguity early.
- GATEWAY-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- GATEWAY-ML-15: Requirement IDs should be stable across the project lifecycle.
- GATEWAY-ML-16: A clear safe state is better than an unexplained limitation.
- GATEWAY-ML-17: Event logs should be understandable to both developers and service engineers.
- GATEWAY-ML-18: Tests should be derived before late implementation bias narrows imagination.
- GATEWAY-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- GATEWAY-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix D — Zonal Architecture micro-lessons

- ZONAL-ML-01: Start from stakeholder scenarios before debating implementation.
- ZONAL-ML-02: Write operating-domain assumptions explicitly.
- ZONAL-ML-03: State timing expectations before integration begins.
- ZONAL-ML-04: Define diagnostics as requirements, not as optional extras.
- ZONAL-ML-05: Every interface needs ownership, units, timing, validity, and fault handling.
- ZONAL-ML-06: Safety requirements must live inside the main engineering baseline.
- ZONAL-ML-07: Degraded behavior must be designed, reviewed, and validated.
- ZONAL-ML-08: Fault injection reveals whether monitors really work.
- ZONAL-ML-09: Service and update workflows are part of product quality.
- ZONAL-ML-10: A release is only as strong as its traceability and evidence closure.
- ZONAL-ML-11: Calibration changes can have requirement-level consequences.
- ZONAL-ML-12: Version and variant identity must be visible in tools and logs.
- ZONAL-ML-13: Review comments are valuable when they remove ambiguity early.
- ZONAL-ML-14: Supplier contracts improve when interface assumptions are frozen explicitly.
- ZONAL-ML-15: Requirement IDs should be stable across the project lifecycle.
- ZONAL-ML-16: A clear safe state is better than an unexplained limitation.
- ZONAL-ML-17: Event logs should be understandable to both developers and service engineers.
- ZONAL-ML-18: Tests should be derived before late implementation bias narrows imagination.
- ZONAL-ML-19: A good HARA depends on realistic situations, not generic fear statements.
- ZONAL-ML-20: Change control is part of engineering quality, not only project administration.

## Appendix E — Adaptive Cruise Control self-study prompts

1. How would you refine the ODD for Adaptive Cruise Control?
2. Which interface for Adaptive Cruise Control is most likely to cause integration defects and why?
3. What degraded mode for Adaptive Cruise Control would be safest but still acceptable to the customer?
4. Which HARA assumption for Adaptive Cruise Control would you challenge first in a real workshop?
5. Which diagnostic artifact for Adaptive Cruise Control would matter most to a service technician?
6. Which requirement for Adaptive Cruise Control is most likely to change late in the program?
7. What evidence would you demand before approving release of Adaptive Cruise Control?
8. How would OTA or configuration changes affect Adaptive Cruise Control?
9. Which validation scenario would best expose customer dissatisfaction with Adaptive Cruise Control?
10. What would a strong traceability dashboard for Adaptive Cruise Control show?

## Appendix E — Automatic Emergency Braking self-study prompts

1. How would you refine the ODD for Automatic Emergency Braking?
2. Which interface for Automatic Emergency Braking is most likely to cause integration defects and why?
3. What degraded mode for Automatic Emergency Braking would be safest but still acceptable to the customer?
4. Which HARA assumption for Automatic Emergency Braking would you challenge first in a real workshop?
5. Which diagnostic artifact for Automatic Emergency Braking would matter most to a service technician?
6. Which requirement for Automatic Emergency Braking is most likely to change late in the program?
7. What evidence would you demand before approving release of Automatic Emergency Braking?
8. How would OTA or configuration changes affect Automatic Emergency Braking?
9. Which validation scenario would best expose customer dissatisfaction with Automatic Emergency Braking?
10. What would a strong traceability dashboard for Automatic Emergency Braking show?

## Appendix E — Lane Keeping Assist self-study prompts

1. How would you refine the ODD for Lane Keeping Assist?
2. Which interface for Lane Keeping Assist is most likely to cause integration defects and why?
3. What degraded mode for Lane Keeping Assist would be safest but still acceptable to the customer?
4. Which HARA assumption for Lane Keeping Assist would you challenge first in a real workshop?
5. Which diagnostic artifact for Lane Keeping Assist would matter most to a service technician?
6. Which requirement for Lane Keeping Assist is most likely to change late in the program?
7. What evidence would you demand before approving release of Lane Keeping Assist?
8. How would OTA or configuration changes affect Lane Keeping Assist?
9. Which validation scenario would best expose customer dissatisfaction with Lane Keeping Assist?
10. What would a strong traceability dashboard for Lane Keeping Assist show?

## Appendix E — ADAS Domain Controller self-study prompts

1. How would you refine the ODD for ADAS Domain Controller?
2. Which interface for ADAS Domain Controller is most likely to cause integration defects and why?
3. What degraded mode for ADAS Domain Controller would be safest but still acceptable to the customer?
4. Which HARA assumption for ADAS Domain Controller would you challenge first in a real workshop?
5. Which diagnostic artifact for ADAS Domain Controller would matter most to a service technician?
6. Which requirement for ADAS Domain Controller is most likely to change late in the program?
7. What evidence would you demand before approving release of ADAS Domain Controller?
8. How would OTA or configuration changes affect ADAS Domain Controller?
9. Which validation scenario would best expose customer dissatisfaction with ADAS Domain Controller?
10. What would a strong traceability dashboard for ADAS Domain Controller show?

## Appendix E — Telematics Control Unit self-study prompts

1. How would you refine the ODD for Telematics Control Unit?
2. Which interface for Telematics Control Unit is most likely to cause integration defects and why?
3. What degraded mode for Telematics Control Unit would be safest but still acceptable to the customer?
4. Which HARA assumption for Telematics Control Unit would you challenge first in a real workshop?
5. Which diagnostic artifact for Telematics Control Unit would matter most to a service technician?
6. Which requirement for Telematics Control Unit is most likely to change late in the program?
7. What evidence would you demand before approving release of Telematics Control Unit?
8. How would OTA or configuration changes affect Telematics Control Unit?
9. Which validation scenario would best expose customer dissatisfaction with Telematics Control Unit?
10. What would a strong traceability dashboard for Telematics Control Unit show?

## Appendix E — eCall System self-study prompts

1. How would you refine the ODD for eCall System?
2. Which interface for eCall System is most likely to cause integration defects and why?
3. What degraded mode for eCall System would be safest but still acceptable to the customer?
4. Which HARA assumption for eCall System would you challenge first in a real workshop?
5. Which diagnostic artifact for eCall System would matter most to a service technician?
6. Which requirement for eCall System is most likely to change late in the program?
7. What evidence would you demand before approving release of eCall System?
8. How would OTA or configuration changes affect eCall System?
9. Which validation scenario would best expose customer dissatisfaction with eCall System?
10. What would a strong traceability dashboard for eCall System show?

## Appendix E — Over-the-Air Update System self-study prompts

1. How would you refine the ODD for Over-the-Air Update System?
2. Which interface for Over-the-Air Update System is most likely to cause integration defects and why?
3. What degraded mode for Over-the-Air Update System would be safest but still acceptable to the customer?
4. Which HARA assumption for Over-the-Air Update System would you challenge first in a real workshop?
5. Which diagnostic artifact for Over-the-Air Update System would matter most to a service technician?
6. Which requirement for Over-the-Air Update System is most likely to change late in the program?
7. What evidence would you demand before approving release of Over-the-Air Update System?
8. How would OTA or configuration changes affect Over-the-Air Update System?
9. Which validation scenario would best expose customer dissatisfaction with Over-the-Air Update System?
10. What would a strong traceability dashboard for Over-the-Air Update System show?

## Appendix E — Digital Instrument Cluster self-study prompts

1. How would you refine the ODD for Digital Instrument Cluster?
2. Which interface for Digital Instrument Cluster is most likely to cause integration defects and why?
3. What degraded mode for Digital Instrument Cluster would be safest but still acceptable to the customer?
4. Which HARA assumption for Digital Instrument Cluster would you challenge first in a real workshop?
5. Which diagnostic artifact for Digital Instrument Cluster would matter most to a service technician?
6. Which requirement for Digital Instrument Cluster is most likely to change late in the program?
7. What evidence would you demand before approving release of Digital Instrument Cluster?
8. How would OTA or configuration changes affect Digital Instrument Cluster?
9. Which validation scenario would best expose customer dissatisfaction with Digital Instrument Cluster?
10. What would a strong traceability dashboard for Digital Instrument Cluster show?

## Appendix E — Vehicle Gateway self-study prompts

1. How would you refine the ODD for Vehicle Gateway?
2. Which interface for Vehicle Gateway is most likely to cause integration defects and why?
3. What degraded mode for Vehicle Gateway would be safest but still acceptable to the customer?
4. Which HARA assumption for Vehicle Gateway would you challenge first in a real workshop?
5. Which diagnostic artifact for Vehicle Gateway would matter most to a service technician?
6. Which requirement for Vehicle Gateway is most likely to change late in the program?
7. What evidence would you demand before approving release of Vehicle Gateway?
8. How would OTA or configuration changes affect Vehicle Gateway?
9. Which validation scenario would best expose customer dissatisfaction with Vehicle Gateway?
10. What would a strong traceability dashboard for Vehicle Gateway show?

## Appendix E — Zonal Architecture self-study prompts

1. How would you refine the ODD for Zonal Architecture?
2. Which interface for Zonal Architecture is most likely to cause integration defects and why?
3. What degraded mode for Zonal Architecture would be safest but still acceptable to the customer?
4. Which HARA assumption for Zonal Architecture would you challenge first in a real workshop?
5. Which diagnostic artifact for Zonal Architecture would matter most to a service technician?
6. Which requirement for Zonal Architecture is most likely to change late in the program?
7. What evidence would you demand before approving release of Zonal Architecture?
8. How would OTA or configuration changes affect Zonal Architecture?
9. Which validation scenario would best expose customer dissatisfaction with Zonal Architecture?
10. What would a strong traceability dashboard for Zonal Architecture show?

## Appendix F — Adaptive Cruise Control review questions

1. (ACC) What is the clearest stakeholder value statement for this item?
2. (ACC) Which requirement should define the operating domain?
3. (ACC) Which input quality criterion is most safety-critical?
4. (ACC) Which output acknowledgement is necessary to trust actuation or presentation?
5. (ACC) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (ACC) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (ACC) Which interface signal needs a freshness requirement and why?
8. (ACC) Which diagnostic monitor would you implement first?
9. (ACC) What must be visible to the driver versus only to service tools?
10. (ACC) Which requirement most strongly affects customer trust?
11. (ACC) Which hazard depends most heavily on realistic operational situations?
12. (ACC) Where could configuration mistakes create hazardous behavior?
13. (ACC) Which test must exist before the first vehicle is available?
14. (ACC) Which fault-injection case best challenges the safety concept?
15. (ACC) What evidence would convince you the release is ready?
16. (ACC) What should be traced to the change request if a late interface update occurs?
17. (ACC) Which part of the architecture deserves the strongest isolation or supervision?
18. (ACC) How would you prove that degraded behavior is understandable to the user?
19. (ACC) What workshop symptom should correspond to the main fault path?
20. (ACC) Which calibration parameter could silently change customer perception?
21. (ACC) How would you check that requirement wording is not implementation-biased?
22. (ACC) Which non-functional requirement is easiest to forget for this item?
23. (ACC) What post-launch KPI would you monitor for field quality?
24. (ACC) Which release artifact is most likely to be incomplete in a rushed program?
25. (ACC) What would you ask the OEM before freezing the baseline?

## Appendix F — Automatic Emergency Braking review questions

1. (AEB) What is the clearest stakeholder value statement for this item?
2. (AEB) Which requirement should define the operating domain?
3. (AEB) Which input quality criterion is most safety-critical?
4. (AEB) Which output acknowledgement is necessary to trust actuation or presentation?
5. (AEB) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (AEB) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (AEB) Which interface signal needs a freshness requirement and why?
8. (AEB) Which diagnostic monitor would you implement first?
9. (AEB) What must be visible to the driver versus only to service tools?
10. (AEB) Which requirement most strongly affects customer trust?
11. (AEB) Which hazard depends most heavily on realistic operational situations?
12. (AEB) Where could configuration mistakes create hazardous behavior?
13. (AEB) Which test must exist before the first vehicle is available?
14. (AEB) Which fault-injection case best challenges the safety concept?
15. (AEB) What evidence would convince you the release is ready?
16. (AEB) What should be traced to the change request if a late interface update occurs?
17. (AEB) Which part of the architecture deserves the strongest isolation or supervision?
18. (AEB) How would you prove that degraded behavior is understandable to the user?
19. (AEB) What workshop symptom should correspond to the main fault path?
20. (AEB) Which calibration parameter could silently change customer perception?
21. (AEB) How would you check that requirement wording is not implementation-biased?
22. (AEB) Which non-functional requirement is easiest to forget for this item?
23. (AEB) What post-launch KPI would you monitor for field quality?
24. (AEB) Which release artifact is most likely to be incomplete in a rushed program?
25. (AEB) What would you ask the OEM before freezing the baseline?

## Appendix F — Lane Keeping Assist review questions

1. (LKA) What is the clearest stakeholder value statement for this item?
2. (LKA) Which requirement should define the operating domain?
3. (LKA) Which input quality criterion is most safety-critical?
4. (LKA) Which output acknowledgement is necessary to trust actuation or presentation?
5. (LKA) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (LKA) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (LKA) Which interface signal needs a freshness requirement and why?
8. (LKA) Which diagnostic monitor would you implement first?
9. (LKA) What must be visible to the driver versus only to service tools?
10. (LKA) Which requirement most strongly affects customer trust?
11. (LKA) Which hazard depends most heavily on realistic operational situations?
12. (LKA) Where could configuration mistakes create hazardous behavior?
13. (LKA) Which test must exist before the first vehicle is available?
14. (LKA) Which fault-injection case best challenges the safety concept?
15. (LKA) What evidence would convince you the release is ready?
16. (LKA) What should be traced to the change request if a late interface update occurs?
17. (LKA) Which part of the architecture deserves the strongest isolation or supervision?
18. (LKA) How would you prove that degraded behavior is understandable to the user?
19. (LKA) What workshop symptom should correspond to the main fault path?
20. (LKA) Which calibration parameter could silently change customer perception?
21. (LKA) How would you check that requirement wording is not implementation-biased?
22. (LKA) Which non-functional requirement is easiest to forget for this item?
23. (LKA) What post-launch KPI would you monitor for field quality?
24. (LKA) Which release artifact is most likely to be incomplete in a rushed program?
25. (LKA) What would you ask the OEM before freezing the baseline?

## Appendix F — ADAS Domain Controller review questions

1. (ADC) What is the clearest stakeholder value statement for this item?
2. (ADC) Which requirement should define the operating domain?
3. (ADC) Which input quality criterion is most safety-critical?
4. (ADC) Which output acknowledgement is necessary to trust actuation or presentation?
5. (ADC) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (ADC) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (ADC) Which interface signal needs a freshness requirement and why?
8. (ADC) Which diagnostic monitor would you implement first?
9. (ADC) What must be visible to the driver versus only to service tools?
10. (ADC) Which requirement most strongly affects customer trust?
11. (ADC) Which hazard depends most heavily on realistic operational situations?
12. (ADC) Where could configuration mistakes create hazardous behavior?
13. (ADC) Which test must exist before the first vehicle is available?
14. (ADC) Which fault-injection case best challenges the safety concept?
15. (ADC) What evidence would convince you the release is ready?
16. (ADC) What should be traced to the change request if a late interface update occurs?
17. (ADC) Which part of the architecture deserves the strongest isolation or supervision?
18. (ADC) How would you prove that degraded behavior is understandable to the user?
19. (ADC) What workshop symptom should correspond to the main fault path?
20. (ADC) Which calibration parameter could silently change customer perception?
21. (ADC) How would you check that requirement wording is not implementation-biased?
22. (ADC) Which non-functional requirement is easiest to forget for this item?
23. (ADC) What post-launch KPI would you monitor for field quality?
24. (ADC) Which release artifact is most likely to be incomplete in a rushed program?
25. (ADC) What would you ask the OEM before freezing the baseline?

## Appendix F — Telematics Control Unit review questions

1. (TCU) What is the clearest stakeholder value statement for this item?
2. (TCU) Which requirement should define the operating domain?
3. (TCU) Which input quality criterion is most safety-critical?
4. (TCU) Which output acknowledgement is necessary to trust actuation or presentation?
5. (TCU) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (TCU) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (TCU) Which interface signal needs a freshness requirement and why?
8. (TCU) Which diagnostic monitor would you implement first?
9. (TCU) What must be visible to the driver versus only to service tools?
10. (TCU) Which requirement most strongly affects customer trust?
11. (TCU) Which hazard depends most heavily on realistic operational situations?
12. (TCU) Where could configuration mistakes create hazardous behavior?
13. (TCU) Which test must exist before the first vehicle is available?
14. (TCU) Which fault-injection case best challenges the safety concept?
15. (TCU) What evidence would convince you the release is ready?
16. (TCU) What should be traced to the change request if a late interface update occurs?
17. (TCU) Which part of the architecture deserves the strongest isolation or supervision?
18. (TCU) How would you prove that degraded behavior is understandable to the user?
19. (TCU) What workshop symptom should correspond to the main fault path?
20. (TCU) Which calibration parameter could silently change customer perception?
21. (TCU) How would you check that requirement wording is not implementation-biased?
22. (TCU) Which non-functional requirement is easiest to forget for this item?
23. (TCU) What post-launch KPI would you monitor for field quality?
24. (TCU) Which release artifact is most likely to be incomplete in a rushed program?
25. (TCU) What would you ask the OEM before freezing the baseline?

## Appendix F — eCall System review questions

1. (ECALL) What is the clearest stakeholder value statement for this item?
2. (ECALL) Which requirement should define the operating domain?
3. (ECALL) Which input quality criterion is most safety-critical?
4. (ECALL) Which output acknowledgement is necessary to trust actuation or presentation?
5. (ECALL) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (ECALL) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (ECALL) Which interface signal needs a freshness requirement and why?
8. (ECALL) Which diagnostic monitor would you implement first?
9. (ECALL) What must be visible to the driver versus only to service tools?
10. (ECALL) Which requirement most strongly affects customer trust?
11. (ECALL) Which hazard depends most heavily on realistic operational situations?
12. (ECALL) Where could configuration mistakes create hazardous behavior?
13. (ECALL) Which test must exist before the first vehicle is available?
14. (ECALL) Which fault-injection case best challenges the safety concept?
15. (ECALL) What evidence would convince you the release is ready?
16. (ECALL) What should be traced to the change request if a late interface update occurs?
17. (ECALL) Which part of the architecture deserves the strongest isolation or supervision?
18. (ECALL) How would you prove that degraded behavior is understandable to the user?
19. (ECALL) What workshop symptom should correspond to the main fault path?
20. (ECALL) Which calibration parameter could silently change customer perception?
21. (ECALL) How would you check that requirement wording is not implementation-biased?
22. (ECALL) Which non-functional requirement is easiest to forget for this item?
23. (ECALL) What post-launch KPI would you monitor for field quality?
24. (ECALL) Which release artifact is most likely to be incomplete in a rushed program?
25. (ECALL) What would you ask the OEM before freezing the baseline?

## Appendix F — Over-the-Air Update System review questions

1. (OTA) What is the clearest stakeholder value statement for this item?
2. (OTA) Which requirement should define the operating domain?
3. (OTA) Which input quality criterion is most safety-critical?
4. (OTA) Which output acknowledgement is necessary to trust actuation or presentation?
5. (OTA) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (OTA) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (OTA) Which interface signal needs a freshness requirement and why?
8. (OTA) Which diagnostic monitor would you implement first?
9. (OTA) What must be visible to the driver versus only to service tools?
10. (OTA) Which requirement most strongly affects customer trust?
11. (OTA) Which hazard depends most heavily on realistic operational situations?
12. (OTA) Where could configuration mistakes create hazardous behavior?
13. (OTA) Which test must exist before the first vehicle is available?
14. (OTA) Which fault-injection case best challenges the safety concept?
15. (OTA) What evidence would convince you the release is ready?
16. (OTA) What should be traced to the change request if a late interface update occurs?
17. (OTA) Which part of the architecture deserves the strongest isolation or supervision?
18. (OTA) How would you prove that degraded behavior is understandable to the user?
19. (OTA) What workshop symptom should correspond to the main fault path?
20. (OTA) Which calibration parameter could silently change customer perception?
21. (OTA) How would you check that requirement wording is not implementation-biased?
22. (OTA) Which non-functional requirement is easiest to forget for this item?
23. (OTA) What post-launch KPI would you monitor for field quality?
24. (OTA) Which release artifact is most likely to be incomplete in a rushed program?
25. (OTA) What would you ask the OEM before freezing the baseline?

## Appendix F — Digital Instrument Cluster review questions

1. (CLUSTER) What is the clearest stakeholder value statement for this item?
2. (CLUSTER) Which requirement should define the operating domain?
3. (CLUSTER) Which input quality criterion is most safety-critical?
4. (CLUSTER) Which output acknowledgement is necessary to trust actuation or presentation?
5. (CLUSTER) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (CLUSTER) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (CLUSTER) Which interface signal needs a freshness requirement and why?
8. (CLUSTER) Which diagnostic monitor would you implement first?
9. (CLUSTER) What must be visible to the driver versus only to service tools?
10. (CLUSTER) Which requirement most strongly affects customer trust?
11. (CLUSTER) Which hazard depends most heavily on realistic operational situations?
12. (CLUSTER) Where could configuration mistakes create hazardous behavior?
13. (CLUSTER) Which test must exist before the first vehicle is available?
14. (CLUSTER) Which fault-injection case best challenges the safety concept?
15. (CLUSTER) What evidence would convince you the release is ready?
16. (CLUSTER) What should be traced to the change request if a late interface update occurs?
17. (CLUSTER) Which part of the architecture deserves the strongest isolation or supervision?
18. (CLUSTER) How would you prove that degraded behavior is understandable to the user?
19. (CLUSTER) What workshop symptom should correspond to the main fault path?
20. (CLUSTER) Which calibration parameter could silently change customer perception?
21. (CLUSTER) How would you check that requirement wording is not implementation-biased?
22. (CLUSTER) Which non-functional requirement is easiest to forget for this item?
23. (CLUSTER) What post-launch KPI would you monitor for field quality?
24. (CLUSTER) Which release artifact is most likely to be incomplete in a rushed program?
25. (CLUSTER) What would you ask the OEM before freezing the baseline?

## Appendix F — Vehicle Gateway review questions

1. (GATEWAY) What is the clearest stakeholder value statement for this item?
2. (GATEWAY) Which requirement should define the operating domain?
3. (GATEWAY) Which input quality criterion is most safety-critical?
4. (GATEWAY) Which output acknowledgement is necessary to trust actuation or presentation?
5. (GATEWAY) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (GATEWAY) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (GATEWAY) Which interface signal needs a freshness requirement and why?
8. (GATEWAY) Which diagnostic monitor would you implement first?
9. (GATEWAY) What must be visible to the driver versus only to service tools?
10. (GATEWAY) Which requirement most strongly affects customer trust?
11. (GATEWAY) Which hazard depends most heavily on realistic operational situations?
12. (GATEWAY) Where could configuration mistakes create hazardous behavior?
13. (GATEWAY) Which test must exist before the first vehicle is available?
14. (GATEWAY) Which fault-injection case best challenges the safety concept?
15. (GATEWAY) What evidence would convince you the release is ready?
16. (GATEWAY) What should be traced to the change request if a late interface update occurs?
17. (GATEWAY) Which part of the architecture deserves the strongest isolation or supervision?
18. (GATEWAY) How would you prove that degraded behavior is understandable to the user?
19. (GATEWAY) What workshop symptom should correspond to the main fault path?
20. (GATEWAY) Which calibration parameter could silently change customer perception?
21. (GATEWAY) How would you check that requirement wording is not implementation-biased?
22. (GATEWAY) Which non-functional requirement is easiest to forget for this item?
23. (GATEWAY) What post-launch KPI would you monitor for field quality?
24. (GATEWAY) Which release artifact is most likely to be incomplete in a rushed program?
25. (GATEWAY) What would you ask the OEM before freezing the baseline?

## Appendix F — Zonal Architecture review questions

1. (ZONAL) What is the clearest stakeholder value statement for this item?
2. (ZONAL) Which requirement should define the operating domain?
3. (ZONAL) Which input quality criterion is most safety-critical?
4. (ZONAL) Which output acknowledgement is necessary to trust actuation or presentation?
5. (ZONAL) What is the safest degraded mode if the primary sensor becomes unavailable?
6. (ZONAL) Which ambiguity would most likely survive until vehicle test if not addressed early?
7. (ZONAL) Which interface signal needs a freshness requirement and why?
8. (ZONAL) Which diagnostic monitor would you implement first?
9. (ZONAL) What must be visible to the driver versus only to service tools?
10. (ZONAL) Which requirement most strongly affects customer trust?
11. (ZONAL) Which hazard depends most heavily on realistic operational situations?
12. (ZONAL) Where could configuration mistakes create hazardous behavior?
13. (ZONAL) Which test must exist before the first vehicle is available?
14. (ZONAL) Which fault-injection case best challenges the safety concept?
15. (ZONAL) What evidence would convince you the release is ready?
16. (ZONAL) What should be traced to the change request if a late interface update occurs?
17. (ZONAL) Which part of the architecture deserves the strongest isolation or supervision?
18. (ZONAL) How would you prove that degraded behavior is understandable to the user?
19. (ZONAL) What workshop symptom should correspond to the main fault path?
20. (ZONAL) Which calibration parameter could silently change customer perception?
21. (ZONAL) How would you check that requirement wording is not implementation-biased?
22. (ZONAL) Which non-functional requirement is easiest to forget for this item?
23. (ZONAL) What post-launch KPI would you monitor for field quality?
24. (ZONAL) Which release artifact is most likely to be incomplete in a rushed program?
25. (ZONAL) What would you ask the OEM before freezing the baseline?

## Appendix G — Adaptive Cruise Control evidence checklist

- (ACC-EV-01) Stakeholder requirements reviewed and approved
- (ACC-EV-02) Vehicle requirements baselined
- (ACC-EV-03) System requirements reviewed for ambiguity and measurability
- (ACC-EV-04) HARA workshop minutes stored
- (ACC-EV-05) Safety goals approved
- (ACC-EV-06) FSRs linked to hazards
- (ACC-EV-07) Architecture allocation reviewed
- (ACC-EV-08) Subsystem requirements allocated to owners
- (ACC-EV-09) Software requirements reviewed
- (ACC-EV-10) Hardware requirements reviewed
- (ACC-EV-11) Interface contracts signed by affected teams
- (ACC-EV-12) Diagnostic list reviewed by service engineering
- (ACC-EV-13) Requirement-based test specification approved
- (ACC-EV-14) Fault-injection campaign defined
- (ACC-EV-15) SIL results archived
- (ACC-EV-16) HIL results archived
- (ACC-EV-17) Vehicle validation results archived
- (ACC-EV-18) Traceability report generated
- (ACC-EV-19) Open issues dispositioned
- (ACC-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Automatic Emergency Braking evidence checklist

- (AEB-EV-01) Stakeholder requirements reviewed and approved
- (AEB-EV-02) Vehicle requirements baselined
- (AEB-EV-03) System requirements reviewed for ambiguity and measurability
- (AEB-EV-04) HARA workshop minutes stored
- (AEB-EV-05) Safety goals approved
- (AEB-EV-06) FSRs linked to hazards
- (AEB-EV-07) Architecture allocation reviewed
- (AEB-EV-08) Subsystem requirements allocated to owners
- (AEB-EV-09) Software requirements reviewed
- (AEB-EV-10) Hardware requirements reviewed
- (AEB-EV-11) Interface contracts signed by affected teams
- (AEB-EV-12) Diagnostic list reviewed by service engineering
- (AEB-EV-13) Requirement-based test specification approved
- (AEB-EV-14) Fault-injection campaign defined
- (AEB-EV-15) SIL results archived
- (AEB-EV-16) HIL results archived
- (AEB-EV-17) Vehicle validation results archived
- (AEB-EV-18) Traceability report generated
- (AEB-EV-19) Open issues dispositioned
- (AEB-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Lane Keeping Assist evidence checklist

- (LKA-EV-01) Stakeholder requirements reviewed and approved
- (LKA-EV-02) Vehicle requirements baselined
- (LKA-EV-03) System requirements reviewed for ambiguity and measurability
- (LKA-EV-04) HARA workshop minutes stored
- (LKA-EV-05) Safety goals approved
- (LKA-EV-06) FSRs linked to hazards
- (LKA-EV-07) Architecture allocation reviewed
- (LKA-EV-08) Subsystem requirements allocated to owners
- (LKA-EV-09) Software requirements reviewed
- (LKA-EV-10) Hardware requirements reviewed
- (LKA-EV-11) Interface contracts signed by affected teams
- (LKA-EV-12) Diagnostic list reviewed by service engineering
- (LKA-EV-13) Requirement-based test specification approved
- (LKA-EV-14) Fault-injection campaign defined
- (LKA-EV-15) SIL results archived
- (LKA-EV-16) HIL results archived
- (LKA-EV-17) Vehicle validation results archived
- (LKA-EV-18) Traceability report generated
- (LKA-EV-19) Open issues dispositioned
- (LKA-EV-20) Release notes and baseline identifiers prepared

## Appendix G — ADAS Domain Controller evidence checklist

- (ADC-EV-01) Stakeholder requirements reviewed and approved
- (ADC-EV-02) Vehicle requirements baselined
- (ADC-EV-03) System requirements reviewed for ambiguity and measurability
- (ADC-EV-04) HARA workshop minutes stored
- (ADC-EV-05) Safety goals approved
- (ADC-EV-06) FSRs linked to hazards
- (ADC-EV-07) Architecture allocation reviewed
- (ADC-EV-08) Subsystem requirements allocated to owners
- (ADC-EV-09) Software requirements reviewed
- (ADC-EV-10) Hardware requirements reviewed
- (ADC-EV-11) Interface contracts signed by affected teams
- (ADC-EV-12) Diagnostic list reviewed by service engineering
- (ADC-EV-13) Requirement-based test specification approved
- (ADC-EV-14) Fault-injection campaign defined
- (ADC-EV-15) SIL results archived
- (ADC-EV-16) HIL results archived
- (ADC-EV-17) Vehicle validation results archived
- (ADC-EV-18) Traceability report generated
- (ADC-EV-19) Open issues dispositioned
- (ADC-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Telematics Control Unit evidence checklist

- (TCU-EV-01) Stakeholder requirements reviewed and approved
- (TCU-EV-02) Vehicle requirements baselined
- (TCU-EV-03) System requirements reviewed for ambiguity and measurability
- (TCU-EV-04) HARA workshop minutes stored
- (TCU-EV-05) Safety goals approved
- (TCU-EV-06) FSRs linked to hazards
- (TCU-EV-07) Architecture allocation reviewed
- (TCU-EV-08) Subsystem requirements allocated to owners
- (TCU-EV-09) Software requirements reviewed
- (TCU-EV-10) Hardware requirements reviewed
- (TCU-EV-11) Interface contracts signed by affected teams
- (TCU-EV-12) Diagnostic list reviewed by service engineering
- (TCU-EV-13) Requirement-based test specification approved
- (TCU-EV-14) Fault-injection campaign defined
- (TCU-EV-15) SIL results archived
- (TCU-EV-16) HIL results archived
- (TCU-EV-17) Vehicle validation results archived
- (TCU-EV-18) Traceability report generated
- (TCU-EV-19) Open issues dispositioned
- (TCU-EV-20) Release notes and baseline identifiers prepared

## Appendix G — eCall System evidence checklist

- (ECALL-EV-01) Stakeholder requirements reviewed and approved
- (ECALL-EV-02) Vehicle requirements baselined
- (ECALL-EV-03) System requirements reviewed for ambiguity and measurability
- (ECALL-EV-04) HARA workshop minutes stored
- (ECALL-EV-05) Safety goals approved
- (ECALL-EV-06) FSRs linked to hazards
- (ECALL-EV-07) Architecture allocation reviewed
- (ECALL-EV-08) Subsystem requirements allocated to owners
- (ECALL-EV-09) Software requirements reviewed
- (ECALL-EV-10) Hardware requirements reviewed
- (ECALL-EV-11) Interface contracts signed by affected teams
- (ECALL-EV-12) Diagnostic list reviewed by service engineering
- (ECALL-EV-13) Requirement-based test specification approved
- (ECALL-EV-14) Fault-injection campaign defined
- (ECALL-EV-15) SIL results archived
- (ECALL-EV-16) HIL results archived
- (ECALL-EV-17) Vehicle validation results archived
- (ECALL-EV-18) Traceability report generated
- (ECALL-EV-19) Open issues dispositioned
- (ECALL-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Over-the-Air Update System evidence checklist

- (OTA-EV-01) Stakeholder requirements reviewed and approved
- (OTA-EV-02) Vehicle requirements baselined
- (OTA-EV-03) System requirements reviewed for ambiguity and measurability
- (OTA-EV-04) HARA workshop minutes stored
- (OTA-EV-05) Safety goals approved
- (OTA-EV-06) FSRs linked to hazards
- (OTA-EV-07) Architecture allocation reviewed
- (OTA-EV-08) Subsystem requirements allocated to owners
- (OTA-EV-09) Software requirements reviewed
- (OTA-EV-10) Hardware requirements reviewed
- (OTA-EV-11) Interface contracts signed by affected teams
- (OTA-EV-12) Diagnostic list reviewed by service engineering
- (OTA-EV-13) Requirement-based test specification approved
- (OTA-EV-14) Fault-injection campaign defined
- (OTA-EV-15) SIL results archived
- (OTA-EV-16) HIL results archived
- (OTA-EV-17) Vehicle validation results archived
- (OTA-EV-18) Traceability report generated
- (OTA-EV-19) Open issues dispositioned
- (OTA-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Digital Instrument Cluster evidence checklist

- (CLUSTER-EV-01) Stakeholder requirements reviewed and approved
- (CLUSTER-EV-02) Vehicle requirements baselined
- (CLUSTER-EV-03) System requirements reviewed for ambiguity and measurability
- (CLUSTER-EV-04) HARA workshop minutes stored
- (CLUSTER-EV-05) Safety goals approved
- (CLUSTER-EV-06) FSRs linked to hazards
- (CLUSTER-EV-07) Architecture allocation reviewed
- (CLUSTER-EV-08) Subsystem requirements allocated to owners
- (CLUSTER-EV-09) Software requirements reviewed
- (CLUSTER-EV-10) Hardware requirements reviewed
- (CLUSTER-EV-11) Interface contracts signed by affected teams
- (CLUSTER-EV-12) Diagnostic list reviewed by service engineering
- (CLUSTER-EV-13) Requirement-based test specification approved
- (CLUSTER-EV-14) Fault-injection campaign defined
- (CLUSTER-EV-15) SIL results archived
- (CLUSTER-EV-16) HIL results archived
- (CLUSTER-EV-17) Vehicle validation results archived
- (CLUSTER-EV-18) Traceability report generated
- (CLUSTER-EV-19) Open issues dispositioned
- (CLUSTER-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Vehicle Gateway evidence checklist

- (GATEWAY-EV-01) Stakeholder requirements reviewed and approved
- (GATEWAY-EV-02) Vehicle requirements baselined
- (GATEWAY-EV-03) System requirements reviewed for ambiguity and measurability
- (GATEWAY-EV-04) HARA workshop minutes stored
- (GATEWAY-EV-05) Safety goals approved
- (GATEWAY-EV-06) FSRs linked to hazards
- (GATEWAY-EV-07) Architecture allocation reviewed
- (GATEWAY-EV-08) Subsystem requirements allocated to owners
- (GATEWAY-EV-09) Software requirements reviewed
- (GATEWAY-EV-10) Hardware requirements reviewed
- (GATEWAY-EV-11) Interface contracts signed by affected teams
- (GATEWAY-EV-12) Diagnostic list reviewed by service engineering
- (GATEWAY-EV-13) Requirement-based test specification approved
- (GATEWAY-EV-14) Fault-injection campaign defined
- (GATEWAY-EV-15) SIL results archived
- (GATEWAY-EV-16) HIL results archived
- (GATEWAY-EV-17) Vehicle validation results archived
- (GATEWAY-EV-18) Traceability report generated
- (GATEWAY-EV-19) Open issues dispositioned
- (GATEWAY-EV-20) Release notes and baseline identifiers prepared

## Appendix G — Zonal Architecture evidence checklist

- (ZONAL-EV-01) Stakeholder requirements reviewed and approved
- (ZONAL-EV-02) Vehicle requirements baselined
- (ZONAL-EV-03) System requirements reviewed for ambiguity and measurability
- (ZONAL-EV-04) HARA workshop minutes stored
- (ZONAL-EV-05) Safety goals approved
- (ZONAL-EV-06) FSRs linked to hazards
- (ZONAL-EV-07) Architecture allocation reviewed
- (ZONAL-EV-08) Subsystem requirements allocated to owners
- (ZONAL-EV-09) Software requirements reviewed
- (ZONAL-EV-10) Hardware requirements reviewed
- (ZONAL-EV-11) Interface contracts signed by affected teams
- (ZONAL-EV-12) Diagnostic list reviewed by service engineering
- (ZONAL-EV-13) Requirement-based test specification approved
- (ZONAL-EV-14) Fault-injection campaign defined
- (ZONAL-EV-15) SIL results archived
- (ZONAL-EV-16) HIL results archived
- (ZONAL-EV-17) Vehicle validation results archived
- (ZONAL-EV-18) Traceability report generated
- (ZONAL-EV-19) Open issues dispositioned
- (ZONAL-EV-20) Release notes and baseline identifiers prepared

## Appendix H — Automotive requirements engineering glossary

- **Acceptance criteria**: Conditions that must be met for a requirement or feature to be considered satisfied.
- **Actuation path**: The chain from software decision to physical actuator response, including acknowledgement and monitoring.
- **Alive counter**: A rolling value used to detect stale, repeated, or missing network messages.
- **ASIL**: Automotive Safety Integrity Level from ISO 26262 used to classify safety rigor.
- **Assumption**: A statement accepted as true for engineering decisions until proven otherwise or replaced by a requirement.
- **Baseline**: A formally approved version of a set of work products subject to change control.
- **Boundary condition**: A limit case at the edge of allowed operation where defects frequently appear.
- **Calibration**: Data used to tune behavior without recompiling core software.
- **CCB**: Change Control Board that approves or rejects proposed changes.
- **Completeness**: A quality attribute of requirements meaning all necessary information is present.
- **Configuration item**: A managed artifact such as software, calibration, document, or hardware definition.
- **Controllability**: In HARA, the estimated ability of a person to avoid harm from malfunctioning behavior.
- **CRC**: Cyclic redundancy check used to detect data corruption.
- **Cut-in**: A vehicle entering the ego lane ahead, commonly relevant to ACC and AEB.
- **Debounce**: Filtering logic used to reject transient input noise or spurious state changes.
- **Degradation strategy**: Predefined safe behavior used when full function cannot be maintained.
- **Derived requirement**: A requirement created from analysis of higher-level requirements, architecture, or constraints.
- **Diagnostic coverage**: The fraction of relevant faults detected by safety or diagnostic mechanisms.
- **DID**: Data Identifier used in UDS diagnostics for reading specific data items.
- **DTC**: Diagnostic Trouble Code used to identify and service faults.
- **E2E protection**: End-to-end communication protection such as counters, CRC, and sequence checks.
- **ECC**: Error correction code used to detect/correct memory corruption.
- **EOL**: End of line manufacturing stage where plant checks and coding are performed.
- **Exposure**: In HARA, the estimated probability of the operational situation occurring.
- **Fault injection**: Intentional insertion of faults to test monitors, safe states, and robustness.
- **Fault tolerant time interval**: Maximum time between a fault and the point where unsafe behavior may occur.
- **FFI**: Freedom from interference between elements of different criticality.
- **Field issue**: A defect or behavior discovered after deployment in customer or fleet use.
- **Freeze frame**: Snapshot data stored with a DTC to preserve fault context.
- **Freshness**: A timing property that indicates whether data arrived recently enough to be valid.
- **FSR**: Functional Safety Requirement derived from a safety goal.
- **Gateway**: An ECU or service that routes and filters communication between networks or domains.
- **HARA**: Hazard Analysis and Risk Assessment used to derive safety goals.
- **Health check**: Verification performed after update or startup to confirm the system is fit for operation.
- **HIL**: Hardware-in-the-loop test environment integrating real hardware with simulated plant or surrounding ECUs.
- **Homologation**: Regulatory approval process required to sell a vehicle or function in a market.
- **ICD**: Interface Control Document defining interface ownership and data contracts.
- **Implementation bias**: Requirement wording that embeds one chosen design instead of the needed behavior.
- **Inhibition**: Blocking activation or output when preconditions are not satisfied.
- **Integrity**: Confidence that data or software is correct and uncorrupted.
- **Item definition**: ISO 26262 description of the function, boundaries, assumptions, and interfaces being analyzed.
- **Jerk**: Rate of change of acceleration, important for comfort and stability.
- **Latency**: Time delay between cause and effect along a path.
- **Limited mode**: A degraded but still partially available operational state.
- **Monitor**: Mechanism that detects faults, timing anomalies, or implausible behavior.
- **Nuisance behavior**: Technically allowed but customer-annoying behavior such as false warnings or unnecessary interventions.
- **ODD**: Operational Design Domain defining where a function is intended to operate.
- **Orphan requirement**: A requirement without valid upstream rationale or downstream implementation/test link.
- **Partitioning**: Separating software or hardware resources to contain faults and interference.
- **Plausibility check**: A comparison used to detect unreasonable or inconsistent values.
- **Post-launch monitoring**: Collection and review of field data after release to detect emerging issues.
- **Priority arbitration**: Logic that decides which message, feature, or request wins when several compete.
- **QM**: Quality Managed classification for non-ASIL functions in ISO 26262.
- **Regression test**: Re-run test used to ensure a change did not break existing behavior.
- **Release evidence**: The collected proof used to justify a controlled product release.
- **Residual risk**: The risk remaining after safety measures are applied.
- **Requirement anti-pattern**: Common bad practice such as vague verbs, missing units, or multiple behaviors in one requirement.
- **Rollback**: Restoring a previous known-good software image or configuration after update failure.
- **Scenario**: A concrete operational story used for elicitation, HARA, testing, or validation.
- **Sequence counter**: An incrementing field used to detect loss, duplication, or reordering of messages.
- **Service routine**: A diagnostic procedure invoked through service tools.
- **SIL**: Software-in-the-loop testing environment using software and simulation.
- **Safety case**: Structured argument supported by evidence that a system is acceptably safe.
- **Safety goal**: Top-level safety objective derived from HARA.
- **Stakeholder requirement**: A need or expectation expressed by a stakeholder at a high level.
- **State machine**: A model defining modes, transitions, triggers, and outputs.
- **Supervision**: Continuous checking of expected behavior, health, or timing.
- **Timeout**: Condition where expected data or acknowledgement does not arrive in time.
- **Traceability**: Ability to follow relationships among needs, requirements, design, tests, and release evidence.
- **TSR**: Technical Safety Requirement allocated to architecture elements.
- **UDS**: Unified Diagnostic Services used for automotive diagnostics.
- **Variant coding**: Configuration mechanism that enables or disables product-line features.
- **Validation**: Confirmation that the correct product was built for real user and operational needs.
- **Verification**: Confirmation that the product was built correctly against specified requirements.
- **Watchdog**: Mechanism that detects runaway or stalled execution and triggers recovery.

## Appendix I — Final mastery flashcards

- Flashcard 1: **Q:** Why are stakeholder requirements insufficient on their own? **A:** Because they rarely contain measurable timing, diagnostics, safety, interface, and degraded-mode details.
- Flashcard 2: **Q:** Why must HARA be connected to realistic operational situations? **A:** Because safety classification depends on context, not abstract malfunction alone.
- Flashcard 3: **Q:** Why are interfaces so often project risks? **A:** Because hidden assumptions about timing, ownership, and validity cause late integration defects.
- Flashcard 4: **Q:** Why is fault injection essential? **A:** Because nominal tests do not prove that monitors and safe states actually work.
- Flashcard 5: **Q:** Why is traceability important at release? **A:** Because it proves that critical requirements were implemented and verified in the released baseline.
- Flashcard 6: **Q:** Why can calibration be a requirements concern? **A:** Because calibration changes can alter customer-visible and safety-relevant behavior.
- Flashcard 7: **Q:** Why does a safety case matter? **A:** Because it organizes evidence and assumptions into a release-decision argument.
- Flashcard 8: **Q:** Why should diagnostics be designed early? **A:** Because serviceability and fault evidence shape architecture, data retention, and interface needs.
- Flashcard 9: **Q:** Why is validation different from verification? **A:** Verification checks conformance to requirements; validation checks fitness for real intended use.
- Flashcard 10: **Q:** Why do good requirements reduce cost? **A:** Because ambiguity found early is dramatically cheaper than defects found late in integration or field use.

## Appendix J — Requirement smell catalog

1. Uses vague verbs such as support, optimize, minimize, maximize, or handle without measurable criteria.
2. Combines multiple unrelated behaviors into one long sentence.
3. Hides trigger conditions or assumes them implicitly.
4. Omits units, tolerances, or timing budgets.
5. Describes a design choice without stating the actual need.
6. Uses words like fast, robust, intuitive, safe, immediate, or reliable without measurable evidence criteria.
7. Never states degraded behavior or fault response.
8. Assumes interface ownership instead of specifying it.
9. Omits diagnostic behavior, logging, or service visibility.
10. Cannot be linked to a test case with an objective pass/fail result.
11. Contradicts another requirement or redefines the same behavior differently.
12. Fails to name state or mode dependencies.
13. Ignores startup, shutdown, restart, or update behavior.
14. Cannot be traced back to a stakeholder need or hazard.
15. Is written so narrowly that it prevents platform reuse without reason.
16. Is written so broadly that implementation teams interpret it differently.
17. Assumes perfect inputs and ignores sensor or communication quality.
18. Describes customer messaging but not who owns the HMI interface.
19. Describes safety intent but omits detection and safe-state expectations.
20. Lists test methods inside the requirement instead of the required behavior itself.

## Appendix K — Adaptive Cruise Control typical pitfalls

- (ACC-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (ACC-PIT-02) Underestimating interface timing and freshness constraints.
- (ACC-PIT-03) Postponing degraded-mode design until integration test.
- (ACC-PIT-04) Relying on calibration to hide requirement ambiguity.
- (ACC-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (ACC-PIT-06) Forgetting update, restart, and power-state behavior.
- (ACC-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (ACC-PIT-08) Failing to align HMI expectations with actual feature states.
- (ACC-PIT-09) Under-specifying variant behavior and product-line constraints.
- (ACC-PIT-10) Approving release without verifying traceability completeness.
- (ACC-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (ACC-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Automatic Emergency Braking typical pitfalls

- (AEB-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (AEB-PIT-02) Underestimating interface timing and freshness constraints.
- (AEB-PIT-03) Postponing degraded-mode design until integration test.
- (AEB-PIT-04) Relying on calibration to hide requirement ambiguity.
- (AEB-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (AEB-PIT-06) Forgetting update, restart, and power-state behavior.
- (AEB-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (AEB-PIT-08) Failing to align HMI expectations with actual feature states.
- (AEB-PIT-09) Under-specifying variant behavior and product-line constraints.
- (AEB-PIT-10) Approving release without verifying traceability completeness.
- (AEB-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (AEB-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Lane Keeping Assist typical pitfalls

- (LKA-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (LKA-PIT-02) Underestimating interface timing and freshness constraints.
- (LKA-PIT-03) Postponing degraded-mode design until integration test.
- (LKA-PIT-04) Relying on calibration to hide requirement ambiguity.
- (LKA-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (LKA-PIT-06) Forgetting update, restart, and power-state behavior.
- (LKA-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (LKA-PIT-08) Failing to align HMI expectations with actual feature states.
- (LKA-PIT-09) Under-specifying variant behavior and product-line constraints.
- (LKA-PIT-10) Approving release without verifying traceability completeness.
- (LKA-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (LKA-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — ADAS Domain Controller typical pitfalls

- (ADC-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (ADC-PIT-02) Underestimating interface timing and freshness constraints.
- (ADC-PIT-03) Postponing degraded-mode design until integration test.
- (ADC-PIT-04) Relying on calibration to hide requirement ambiguity.
- (ADC-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (ADC-PIT-06) Forgetting update, restart, and power-state behavior.
- (ADC-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (ADC-PIT-08) Failing to align HMI expectations with actual feature states.
- (ADC-PIT-09) Under-specifying variant behavior and product-line constraints.
- (ADC-PIT-10) Approving release without verifying traceability completeness.
- (ADC-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (ADC-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Telematics Control Unit typical pitfalls

- (TCU-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (TCU-PIT-02) Underestimating interface timing and freshness constraints.
- (TCU-PIT-03) Postponing degraded-mode design until integration test.
- (TCU-PIT-04) Relying on calibration to hide requirement ambiguity.
- (TCU-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (TCU-PIT-06) Forgetting update, restart, and power-state behavior.
- (TCU-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (TCU-PIT-08) Failing to align HMI expectations with actual feature states.
- (TCU-PIT-09) Under-specifying variant behavior and product-line constraints.
- (TCU-PIT-10) Approving release without verifying traceability completeness.
- (TCU-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (TCU-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — eCall System typical pitfalls

- (ECALL-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (ECALL-PIT-02) Underestimating interface timing and freshness constraints.
- (ECALL-PIT-03) Postponing degraded-mode design until integration test.
- (ECALL-PIT-04) Relying on calibration to hide requirement ambiguity.
- (ECALL-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (ECALL-PIT-06) Forgetting update, restart, and power-state behavior.
- (ECALL-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (ECALL-PIT-08) Failing to align HMI expectations with actual feature states.
- (ECALL-PIT-09) Under-specifying variant behavior and product-line constraints.
- (ECALL-PIT-10) Approving release without verifying traceability completeness.
- (ECALL-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (ECALL-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Over-the-Air Update System typical pitfalls

- (OTA-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (OTA-PIT-02) Underestimating interface timing and freshness constraints.
- (OTA-PIT-03) Postponing degraded-mode design until integration test.
- (OTA-PIT-04) Relying on calibration to hide requirement ambiguity.
- (OTA-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (OTA-PIT-06) Forgetting update, restart, and power-state behavior.
- (OTA-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (OTA-PIT-08) Failing to align HMI expectations with actual feature states.
- (OTA-PIT-09) Under-specifying variant behavior and product-line constraints.
- (OTA-PIT-10) Approving release without verifying traceability completeness.
- (OTA-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (OTA-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Digital Instrument Cluster typical pitfalls

- (CLUSTER-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (CLUSTER-PIT-02) Underestimating interface timing and freshness constraints.
- (CLUSTER-PIT-03) Postponing degraded-mode design until integration test.
- (CLUSTER-PIT-04) Relying on calibration to hide requirement ambiguity.
- (CLUSTER-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (CLUSTER-PIT-06) Forgetting update, restart, and power-state behavior.
- (CLUSTER-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (CLUSTER-PIT-08) Failing to align HMI expectations with actual feature states.
- (CLUSTER-PIT-09) Under-specifying variant behavior and product-line constraints.
- (CLUSTER-PIT-10) Approving release without verifying traceability completeness.
- (CLUSTER-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (CLUSTER-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Vehicle Gateway typical pitfalls

- (GATEWAY-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (GATEWAY-PIT-02) Underestimating interface timing and freshness constraints.
- (GATEWAY-PIT-03) Postponing degraded-mode design until integration test.
- (GATEWAY-PIT-04) Relying on calibration to hide requirement ambiguity.
- (GATEWAY-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (GATEWAY-PIT-06) Forgetting update, restart, and power-state behavior.
- (GATEWAY-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (GATEWAY-PIT-08) Failing to align HMI expectations with actual feature states.
- (GATEWAY-PIT-09) Under-specifying variant behavior and product-line constraints.
- (GATEWAY-PIT-10) Approving release without verifying traceability completeness.
- (GATEWAY-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (GATEWAY-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

## Appendix K — Zonal Architecture typical pitfalls

- (ZONAL-PIT-01) Treating the feature description as if it were already a requirement baseline.
- (ZONAL-PIT-02) Underestimating interface timing and freshness constraints.
- (ZONAL-PIT-03) Postponing degraded-mode design until integration test.
- (ZONAL-PIT-04) Relying on calibration to hide requirement ambiguity.
- (ZONAL-PIT-05) Assuming service diagnostics can be added late with no architectural cost.
- (ZONAL-PIT-06) Forgetting update, restart, and power-state behavior.
- (ZONAL-PIT-07) Testing only nominal scenarios and missing monitor coverage gaps.
- (ZONAL-PIT-08) Failing to align HMI expectations with actual feature states.
- (ZONAL-PIT-09) Under-specifying variant behavior and product-line constraints.
- (ZONAL-PIT-10) Approving release without verifying traceability completeness.
- (ZONAL-PIT-11) Ignoring manufacturing and commissioning constraints until SOP pressure is high.
- (ZONAL-PIT-12) Recording logs that are rich for developers but unusable for workshops or field operations.

