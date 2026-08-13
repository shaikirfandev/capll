# Automotive Requirements Engineering — System, ADAS, Telematics, Cluster, Safety, HARA, and SOTIF

This document is a detailed educational reference for automotive engineers writing, analysing, tracing, and verifying requirements for modern distributed vehicle systems. It focuses on **Sections 8 through 14** and emphasises professional requirement style, traceability, safety integration, and realistic engineering examples.

---

## Table of Contents

- [Section 8: AUTOMOTIVE SYSTEM REQUIREMENTS](#section-8-automotive-system-requirements)
- [Section 9: ADAS REQUIREMENTS ENGINEERING](#section-9-adas-requirements-engineering)
- [Section 10: TELEMATICS REQUIREMENTS ENGINEERING](#section-10-telematics-requirements-engineering)
- [Section 11: INSTRUMENT CLUSTER REQUIREMENTS](#section-11-instrument-cluster-requirements)
- [Section 12: REQUIREMENTS + FUNCTIONAL SAFETY](#section-12-requirements-functional-safety)
- [Section 13: REQUIREMENTS + HARA](#section-13-requirements-hara)
- [Section 14: REQUIREMENTS + SOTIF](#section-14-requirements-sotif)

---

## Document Conventions

| Convention | Meaning |
|---|---|
| `REQ-...` | Requirement identifier |
| `SG-...` | Safety goal identifier |
| `FSR-...` | Functional safety requirement |
| `TSR-...` | Technical safety requirement |
| `SwRS-...` | Software requirement |
| `HwRS-...` | Hardware requirement |
| `TC-...` | Test requirement or verification case |

### Requirement Writing Rules Used in This Document

- Each requirement states one externally verifiable behaviour.
- Quantitative limits are used wherever timing, performance, or thresholds matter.
- Safety-related behaviour explicitly references safe state, warning, inhibition, or fallback behaviour.
- Interface requirements identify source, destination, message, signal, data age, and fault handling expectation.
- Failure requirements describe detection, reaction, notification, logging, and recovery.

### Typical Traceability Chain

```text
Stakeholder Need
  -> Item Definition
    -> HARA / SOTIF Analysis
      -> Safety Goal / Performance Limitation
        -> Functional Safety Requirement / SOTIF Requirement
          -> Technical Safety Requirement
            -> System Requirement
              -> Software Requirement + Hardware Requirement
                -> Unit / Integration / HIL / Vehicle Test Requirement
```

## Section 8: AUTOMOTIVE SYSTEM REQUIREMENTS

Modern vehicles are distributed systems. Requirements must be tailored to the function and risk profile of each ECU class. The following subsections provide example requirement sets for commonly used automotive electronic systems.

### 8.1 Requirement Categories Used for Each ECU Type

| Category | Purpose | Typical Evidence |
|---|---|---|
| Functional | What the ECU shall do | System test, HIL, vehicle test |
| Performance | How well it shall do it | Benchmark, profiling, timing analysis |
| Interface | What it exchanges and over which channel | ICD review, bus trace, conformance test |
| Diagnostic | How faults are detected and reported | Fault injection, UDS test |
| Safety | How hazards are prevented or controlled | Safety analysis, HIL fault campaign |
| Security | How assets are protected | Pen-test, secure boot validation |
| Timing | When actions shall happen | Timing measurement, trace |
| Failure-handling | How degraded or failed operation is handled | Negative test, recovery test |

### 8.1 Generic ECU

The Generic ECU is responsible for **execute a bounded control or monitoring function**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.1.1 Functional requirements

- **REQ-ECU-FUNC-01**: The Generic ECU shall execute a bounded control or monitoring function whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-ECU-FUNC-02**: The Generic ECU shall process sensor inputs, network signals, and diagnostics and produce actuator commands and status signals according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-ECU-FUNC-03**: The Generic ECU shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-ECU-FUNC-04**: The Generic ECU shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.1.2 Performance requirements

- **REQ-ECU-PERF-01**: The Generic ECU shall complete its main application cycle within 10 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-ECU-PERF-02**: The Generic ECU shall reach application-ready state within 300 ms after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-ECU-PERF-03**: The Generic ECU shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-ECU-PERF-04**: The Generic ECU shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.1.3 Interface requirements

- **REQ-ECU-INTF-01**: The Generic ECU shall exchange operational data over CAN or LIN using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-ECU-INTF-02**: The Generic ECU shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-ECU-INTF-03**: The Generic ECU shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 50 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-ECU-INTF-04**: The Generic ECU shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.1.4 Diagnostic requirements

- **REQ-ECU-DIAG-01**: The Generic ECU shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-ECU-DIAG-02**: The Generic ECU shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-ECU-DIAG-03**: The Generic ECU shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-ECU-DIAG-04**: The Generic ECU shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.1.5 Safety requirements

- **REQ-ECU-SAFE-01**: If a fault can lead to hazardous behaviour, the Generic ECU shall place outputs in a non-hazardous state within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-ECU-SAFE-02**: The Generic ECU shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-ECU-SAFE-03**: The Generic ECU shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-ECU-SAFE-04**: The Generic ECU shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.1.6 Security requirements

- **REQ-ECU-SEC-01**: The Generic ECU shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-ECU-SEC-02**: The Generic ECU shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-ECU-SEC-03**: The Generic ECU shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-ECU-SEC-04**: The Generic ECU shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.1.7 Timing requirements

- **REQ-ECU-TIME-01**: The Generic ECU shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-ECU-TIME-02**: The Generic ECU shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-ECU-TIME-03**: The Generic ECU shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-ECU-TIME-04**: The Generic ECU shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.1.8 Failure-handling requirements

- **REQ-ECU-FAIL-01**: If a required input becomes unavailable, the Generic ECU shall enter substitute values or function inhibition and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-ECU-FAIL-02**: If an unrecoverable internal error is detected, the Generic ECU shall issue network fault status before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-ECU-FAIL-03**: The Generic ECU shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-ECU-FAIL-04**: After recovery from a transient fault, the Generic ECU shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.2 ADAS ECU

The ADAS ECU is responsible for **process perception and generate driver assistance decisions**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.2.1 Functional requirements

- **REQ-ADAS-FUNC-01**: The ADAS ECU shall process perception and generate driver assistance decisions whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-ADAS-FUNC-02**: The ADAS ECU shall process radar, camera, ultrasonic, vehicle dynamics, and map inputs and produce warnings, braking requests, and steering torque requests according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-ADAS-FUNC-03**: The ADAS ECU shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-ADAS-FUNC-04**: The ADAS ECU shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.2.2 Performance requirements

- **REQ-ADAS-PERF-01**: The ADAS ECU shall complete its main application cycle within 20 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-ADAS-PERF-02**: The ADAS ECU shall reach application-ready state within 800 ms after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-ADAS-PERF-03**: The ADAS ECU shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-ADAS-PERF-04**: The ADAS ECU shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.2.3 Interface requirements

- **REQ-ADAS-INTF-01**: The ADAS ECU shall exchange operational data over CAN FD and automotive Ethernet using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-ADAS-INTF-02**: The ADAS ECU shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-ADAS-INTF-03**: The ADAS ECU shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 40 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-ADAS-INTF-04**: The ADAS ECU shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.2.4 Diagnostic requirements

- **REQ-ADAS-DIAG-01**: The ADAS ECU shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-ADAS-DIAG-02**: The ADAS ECU shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-ADAS-DIAG-03**: The ADAS ECU shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-ADAS-DIAG-04**: The ADAS ECU shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.2.5 Safety requirements

- **REQ-ADAS-SAFE-01**: If a fault can lead to hazardous behaviour, the ADAS ECU shall suppress automatic intervention and inform the driver within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-ADAS-SAFE-02**: The ADAS ECU shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-ADAS-SAFE-03**: The ADAS ECU shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-ADAS-SAFE-04**: The ADAS ECU shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.2.6 Security requirements

- **REQ-ADAS-SEC-01**: The ADAS ECU shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-ADAS-SEC-02**: The ADAS ECU shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-ADAS-SEC-03**: The ADAS ECU shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-ADAS-SEC-04**: The ADAS ECU shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.2.7 Timing requirements

- **REQ-ADAS-TIME-01**: The ADAS ECU shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-ADAS-TIME-02**: The ADAS ECU shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-ADAS-TIME-03**: The ADAS ECU shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-ADAS-TIME-04**: The ADAS ECU shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.2.8 Failure-handling requirements

- **REQ-ADAS-FAIL-01**: If a required input becomes unavailable, the ADAS ECU shall enter reduced authority or reduced availability and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-ADAS-FAIL-02**: If an unrecoverable internal error is detected, the ADAS ECU shall issue ADAS unavailable message before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-ADAS-FAIL-03**: The ADAS ECU shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-ADAS-FAIL-04**: After recovery from a transient fault, the ADAS ECU shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.3 Telematics Control Unit (TCU)

The Telematics Control Unit (TCU) is responsible for **provide off-board connectivity, emergency calling, and remote services**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.3.1 Functional requirements

- **REQ-TCU-FUNC-01**: The Telematics Control Unit (TCU) shall provide off-board connectivity, emergency calling, and remote services whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-TCU-FUNC-02**: The Telematics Control Unit (TCU) shall process cellular status, GNSS, vehicle bus data, and remote commands and produce cloud messages, call sessions, and remote command results according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-TCU-FUNC-03**: The Telematics Control Unit (TCU) shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-TCU-FUNC-04**: The Telematics Control Unit (TCU) shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.3.2 Performance requirements

- **REQ-TCU-PERF-01**: The Telematics Control Unit (TCU) shall complete its main application cycle within 100 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-TCU-PERF-02**: The Telematics Control Unit (TCU) shall reach application-ready state within 5 s after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-TCU-PERF-03**: The Telematics Control Unit (TCU) shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-TCU-PERF-04**: The Telematics Control Unit (TCU) shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.3.3 Interface requirements

- **REQ-TCU-INTF-01**: The Telematics Control Unit (TCU) shall exchange operational data over CAN, Ethernet, Bluetooth, and modem links using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-TCU-INTF-02**: The Telematics Control Unit (TCU) shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-TCU-INTF-03**: The Telematics Control Unit (TCU) shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 500 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-TCU-INTF-04**: The Telematics Control Unit (TCU) shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.3.4 Diagnostic requirements

- **REQ-TCU-DIAG-01**: The Telematics Control Unit (TCU) shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-TCU-DIAG-02**: The Telematics Control Unit (TCU) shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-TCU-DIAG-03**: The Telematics Control Unit (TCU) shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-TCU-DIAG-04**: The Telematics Control Unit (TCU) shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.3.5 Safety requirements

- **REQ-TCU-SAFE-01**: If a fault can lead to hazardous behaviour, the Telematics Control Unit (TCU) shall maintain emergency capability and stop non-essential exchange within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-TCU-SAFE-02**: The Telematics Control Unit (TCU) shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-TCU-SAFE-03**: The Telematics Control Unit (TCU) shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-TCU-SAFE-04**: The Telematics Control Unit (TCU) shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.3.6 Security requirements

- **REQ-TCU-SEC-01**: The Telematics Control Unit (TCU) shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-TCU-SEC-02**: The Telematics Control Unit (TCU) shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-TCU-SEC-03**: The Telematics Control Unit (TCU) shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-TCU-SEC-04**: The Telematics Control Unit (TCU) shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.3.7 Timing requirements

- **REQ-TCU-TIME-01**: The Telematics Control Unit (TCU) shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-TCU-TIME-02**: The Telematics Control Unit (TCU) shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-TCU-TIME-03**: The Telematics Control Unit (TCU) shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-TCU-TIME-04**: The Telematics Control Unit (TCU) shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.3.8 Failure-handling requirements

- **REQ-TCU-FAIL-01**: If a required input becomes unavailable, the Telematics Control Unit (TCU) shall enter store-and-forward operation and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-TCU-FAIL-02**: If an unrecoverable internal error is detected, the Telematics Control Unit (TCU) shall issue service unavailable indication before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-TCU-FAIL-03**: The Telematics Control Unit (TCU) shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-TCU-FAIL-04**: After recovery from a transient fault, the Telematics Control Unit (TCU) shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.4 Instrument Cluster

The Instrument Cluster is responsible for **display legally required driving information and warnings**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.4.1 Functional requirements

- **REQ-CLSTR-FUNC-01**: The Instrument Cluster shall display legally required driving information and warnings whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-CLSTR-FUNC-02**: The Instrument Cluster shall process vehicle speed, tell-tales, ADAS messages, and dimming inputs and produce displayed symbols, chimes, and messages according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-CLSTR-FUNC-03**: The Instrument Cluster shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-CLSTR-FUNC-04**: The Instrument Cluster shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.4.2 Performance requirements

- **REQ-CLSTR-PERF-01**: The Instrument Cluster shall complete its main application cycle within 20 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-CLSTR-PERF-02**: The Instrument Cluster shall reach application-ready state within 2 s after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-CLSTR-PERF-03**: The Instrument Cluster shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-CLSTR-PERF-04**: The Instrument Cluster shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.4.3 Interface requirements

- **REQ-CLSTR-INTF-01**: The Instrument Cluster shall exchange operational data over CAN or Ethernet display backbone using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-CLSTR-INTF-02**: The Instrument Cluster shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-CLSTR-INTF-03**: The Instrument Cluster shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 100 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-CLSTR-INTF-04**: The Instrument Cluster shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.4.4 Diagnostic requirements

- **REQ-CLSTR-DIAG-01**: The Instrument Cluster shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-CLSTR-DIAG-02**: The Instrument Cluster shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-CLSTR-DIAG-03**: The Instrument Cluster shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-CLSTR-DIAG-04**: The Instrument Cluster shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.4.5 Safety requirements

- **REQ-CLSTR-SAFE-01**: If a fault can lead to hazardous behaviour, the Instrument Cluster shall display safe fallback information within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-CLSTR-SAFE-02**: The Instrument Cluster shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-CLSTR-SAFE-03**: The Instrument Cluster shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-CLSTR-SAFE-04**: The Instrument Cluster shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.4.6 Security requirements

- **REQ-CLSTR-SEC-01**: The Instrument Cluster shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-CLSTR-SEC-02**: The Instrument Cluster shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-CLSTR-SEC-03**: The Instrument Cluster shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-CLSTR-SEC-04**: The Instrument Cluster shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.4.7 Timing requirements

- **REQ-CLSTR-TIME-01**: The Instrument Cluster shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-CLSTR-TIME-02**: The Instrument Cluster shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-CLSTR-TIME-03**: The Instrument Cluster shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-CLSTR-TIME-04**: The Instrument Cluster shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.4.8 Failure-handling requirements

- **REQ-CLSTR-FAIL-01**: If a required input becomes unavailable, the Instrument Cluster shall enter simplified display mode and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-CLSTR-FAIL-02**: If an unrecoverable internal error is detected, the Instrument Cluster shall issue cluster malfunction indication before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-CLSTR-FAIL-03**: The Instrument Cluster shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-CLSTR-FAIL-04**: After recovery from a transient fault, the Instrument Cluster shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.5 Gateway ECU

The Gateway ECU is responsible for **route, filter, firewall, and supervise network communication**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.5.1 Functional requirements

- **REQ-GTW-FUNC-01**: The Gateway ECU shall route, filter, firewall, and supervise network communication whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-GTW-FUNC-02**: The Gateway ECU shall process messages from powertrain, chassis, body, telematics, and ADAS domains and produce forwarded, translated, or blocked traffic according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-GTW-FUNC-03**: The Gateway ECU shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-GTW-FUNC-04**: The Gateway ECU shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.5.2 Performance requirements

- **REQ-GTW-PERF-01**: The Gateway ECU shall complete its main application cycle within 5 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-GTW-PERF-02**: The Gateway ECU shall reach application-ready state within 500 ms after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-GTW-PERF-03**: The Gateway ECU shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-GTW-PERF-04**: The Gateway ECU shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.5.3 Interface requirements

- **REQ-GTW-INTF-01**: The Gateway ECU shall exchange operational data over multiple CAN/CAN FD/LIN/Ethernet segments using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-GTW-INTF-02**: The Gateway ECU shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-GTW-INTF-03**: The Gateway ECU shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 20 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-GTW-INTF-04**: The Gateway ECU shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.5.4 Diagnostic requirements

- **REQ-GTW-DIAG-01**: The Gateway ECU shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-GTW-DIAG-02**: The Gateway ECU shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-GTW-DIAG-03**: The Gateway ECU shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-GTW-DIAG-04**: The Gateway ECU shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.5.5 Safety requirements

- **REQ-GTW-SAFE-01**: If a fault can lead to hazardous behaviour, the Gateway ECU shall block unauthorised traffic while preserving safety communication within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-GTW-SAFE-02**: The Gateway ECU shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-GTW-SAFE-03**: The Gateway ECU shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-GTW-SAFE-04**: The Gateway ECU shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.5.6 Security requirements

- **REQ-GTW-SEC-01**: The Gateway ECU shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-GTW-SEC-02**: The Gateway ECU shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-GTW-SEC-03**: The Gateway ECU shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-GTW-SEC-04**: The Gateway ECU shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.5.7 Timing requirements

- **REQ-GTW-TIME-01**: The Gateway ECU shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-GTW-TIME-02**: The Gateway ECU shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-GTW-TIME-03**: The Gateway ECU shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-GTW-TIME-04**: The Gateway ECU shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.5.8 Failure-handling requirements

- **REQ-GTW-FAIL-01**: If a required input becomes unavailable, the Gateway ECU shall enter priority-based routing with traffic shedding and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-GTW-FAIL-02**: If an unrecoverable internal error is detected, the Gateway ECU shall issue network degradation status before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-GTW-FAIL-03**: The Gateway ECU shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-GTW-FAIL-04**: After recovery from a transient fault, the Gateway ECU shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.6 Domain Controller

The Domain Controller is responsible for **consolidate multiple functions and coordinate software services**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.6.1 Functional requirements

- **REQ-DOM-FUNC-01**: The Domain Controller shall consolidate multiple functions and coordinate software services whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-DOM-FUNC-02**: The Domain Controller shall process sensor data, service requests, and subordinate node status and produce domain control commands and coordinated decisions according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-DOM-FUNC-03**: The Domain Controller shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-DOM-FUNC-04**: The Domain Controller shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.6.2 Performance requirements

- **REQ-DOM-PERF-01**: The Domain Controller shall complete its main application cycle within 10 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-DOM-PERF-02**: The Domain Controller shall reach application-ready state within 1.5 s after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-DOM-PERF-03**: The Domain Controller shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-DOM-PERF-04**: The Domain Controller shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.6.3 Interface requirements

- **REQ-DOM-INTF-01**: The Domain Controller shall exchange operational data over CAN FD and service-oriented Ethernet using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-DOM-INTF-02**: The Domain Controller shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-DOM-INTF-03**: The Domain Controller shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 30 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-DOM-INTF-04**: The Domain Controller shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.6.4 Diagnostic requirements

- **REQ-DOM-DIAG-01**: The Domain Controller shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-DOM-DIAG-02**: The Domain Controller shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-DOM-DIAG-03**: The Domain Controller shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-DOM-DIAG-04**: The Domain Controller shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.6.5 Safety requirements

- **REQ-DOM-SAFE-01**: If a fault can lead to hazardous behaviour, the Domain Controller shall disable affected domain functions and maintain minimum essential operation within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-DOM-SAFE-02**: The Domain Controller shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-DOM-SAFE-03**: The Domain Controller shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-DOM-SAFE-04**: The Domain Controller shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.6.6 Security requirements

- **REQ-DOM-SEC-01**: The Domain Controller shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-DOM-SEC-02**: The Domain Controller shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-DOM-SEC-03**: The Domain Controller shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-DOM-SEC-04**: The Domain Controller shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.6.7 Timing requirements

- **REQ-DOM-TIME-01**: The Domain Controller shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-DOM-TIME-02**: The Domain Controller shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-DOM-TIME-03**: The Domain Controller shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-DOM-TIME-04**: The Domain Controller shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.6.8 Failure-handling requirements

- **REQ-DOM-FAIL-01**: If a required input becomes unavailable, the Domain Controller shall enter function isolation with graceful quality reduction and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-DOM-FAIL-02**: If an unrecoverable internal error is detected, the Domain Controller shall issue domain degradation message before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-DOM-FAIL-03**: The Domain Controller shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-DOM-FAIL-04**: After recovery from a transient fault, the Domain Controller shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.7 Sensor ECU

The Sensor ECU is responsible for **acquire, condition, and publish validated measurements**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.7.1 Functional requirements

- **REQ-SNSR-FUNC-01**: The Sensor ECU shall acquire, condition, and publish validated measurements whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-SNSR-FUNC-02**: The Sensor ECU shall process raw transducer signals, supply monitoring, and time base and produce validated measurements, confidence values, and health status according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-SNSR-FUNC-03**: The Sensor ECU shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-SNSR-FUNC-04**: The Sensor ECU shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.7.2 Performance requirements

- **REQ-SNSR-PERF-01**: The Sensor ECU shall complete its main application cycle within 10 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-SNSR-PERF-02**: The Sensor ECU shall reach application-ready state within 200 ms after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-SNSR-PERF-03**: The Sensor ECU shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-SNSR-PERF-04**: The Sensor ECU shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.7.3 Interface requirements

- **REQ-SNSR-INTF-01**: The Sensor ECU shall exchange operational data over SENT, SPI, CAN, or Ethernet using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-SNSR-INTF-02**: The Sensor ECU shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-SNSR-INTF-03**: The Sensor ECU shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 20 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-SNSR-INTF-04**: The Sensor ECU shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.7.4 Diagnostic requirements

- **REQ-SNSR-DIAG-01**: The Sensor ECU shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-SNSR-DIAG-02**: The Sensor ECU shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-SNSR-DIAG-03**: The Sensor ECU shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-SNSR-DIAG-04**: The Sensor ECU shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.7.5 Safety requirements

- **REQ-SNSR-SAFE-01**: If a fault can lead to hazardous behaviour, the Sensor ECU shall invalidate the measurement and publish a fault status within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-SNSR-SAFE-02**: The Sensor ECU shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-SNSR-SAFE-03**: The Sensor ECU shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-SNSR-SAFE-04**: The Sensor ECU shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.7.6 Security requirements

- **REQ-SNSR-SEC-01**: The Sensor ECU shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-SNSR-SEC-02**: The Sensor ECU shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-SNSR-SEC-03**: The Sensor ECU shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-SNSR-SEC-04**: The Sensor ECU shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.7.7 Timing requirements

- **REQ-SNSR-TIME-01**: The Sensor ECU shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-SNSR-TIME-02**: The Sensor ECU shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-SNSR-TIME-03**: The Sensor ECU shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-SNSR-TIME-04**: The Sensor ECU shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.7.8 Failure-handling requirements

- **REQ-SNSR-FAIL-01**: If a required input becomes unavailable, the Sensor ECU shall enter confidence-reduced publication or output suppression and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-SNSR-FAIL-02**: If an unrecoverable internal error is detected, the Sensor ECU shall issue sensor fault flag before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-SNSR-FAIL-03**: The Sensor ECU shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-SNSR-FAIL-04**: After recovery from a transient fault, the Sensor ECU shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.8 Actuator ECU

The Actuator ECU is responsible for **convert validated control demands into physical actuation**. The examples below show a balanced requirement set covering functionality, quality, diagnostics, safety, security, timing, and recovery.

#### 8.8.1 Functional requirements

- **REQ-ACT-FUNC-01**: The Actuator ECU shall convert validated control demands into physical actuation whenever the relevant vehicle operating mode is active.
  - *Rationale*: Defines the primary mission of the controller.
  - *Verification*: System integration test in nominal operating modes.

- **REQ-ACT-FUNC-02**: The Actuator ECU shall process command requests, feedback sensors, power-stage status, and diagnostics and produce motor, valve, lamp, relay, or brake actuation according to the allocated feature logic.
  - *Rationale*: Captures end-to-end transformation of inputs into outputs.
  - *Verification*: HIL test with representative input sweeps.

- **REQ-ACT-FUNC-03**: The Actuator ECU shall support startup, run, shutdown, and diagnostic operating states with deterministic state transitions.
  - *Rationale*: Prevents undefined modes and integration ambiguity.
  - *Verification*: State machine test across all transitions.

- **REQ-ACT-FUNC-04**: The Actuator ECU shall preserve configurable parameters and restore the last valid calibration set after a power cycle.
  - *Rationale*: Ensures continuity after ignition cycles and service events.
  - *Verification*: Power interruption test with NVM read-back.

#### 8.8.2 Performance requirements

- **REQ-ACT-PERF-01**: The Actuator ECU shall complete its main application cycle within 5 ms under worst-case load.
  - *Rationale*: Bounds response time and scheduler utilisation.
  - *Verification*: Execution-time measurement with worst-case stimuli.

- **REQ-ACT-PERF-02**: The Actuator ECU shall reach application-ready state within 250 ms after valid power-on.
  - *Rationale*: Supports vehicle startup expectations.
  - *Verification*: Boot-time measurement over voltage and temperature corners.

- **REQ-ACT-PERF-03**: The Actuator ECU shall maintain average CPU utilisation below 80% and peak utilisation below 90% during worst-case scenarios.
  - *Rationale*: Retains timing margin for diagnostics and recovery tasks.
  - *Verification*: Profiling during stress scenarios.

- **REQ-ACT-PERF-04**: The Actuator ECU shall retain at least 20% communication and memory margin after integration of all released functions.
  - *Rationale*: Prevents latent integration failures caused by exhausted resources.
  - *Verification*: Resource analysis and runtime measurement.

#### 8.8.3 Interface requirements

- **REQ-ACT-INTF-01**: The Actuator ECU shall exchange operational data over PWM, CAN, and local feedback interfaces using interfaces defined in the approved ICD.
  - *Rationale*: Locks behaviour to controlled interface definitions.
  - *Verification*: ICD review plus network conformance test.

- **REQ-ACT-INTF-02**: The Actuator ECU shall reject messages whose identifier, payload length, counter, or CRC does not match the configured interface definition.
  - *Rationale*: Prevents silent corruption and interface misuse.
  - *Verification*: Bus fault injection with malformed frames.

- **REQ-ACT-INTF-03**: The Actuator ECU shall time-stamp received safety-relevant inputs and mark them invalid when data age exceeds 20 ms.
  - *Rationale*: Allows downstream logic to detect stale information.
  - *Verification*: Signal staleness test using delayed or frozen frames.

- **REQ-ACT-INTF-04**: The Actuator ECU shall provide a diagnostic communication interface for identification, status, DTCs, and software version information.
  - *Rationale*: Supports manufacturing, service, and field analysis.
  - *Verification*: UDS diagnostic session conformance test.

#### 8.8.4 Diagnostic requirements

- **REQ-ACT-DIAG-01**: The Actuator ECU shall monitor internal memory, processor, communication, and I/O health and classify detected faults as transient, confirmed, or permanent.
  - *Rationale*: Supports consistent diagnostic maturation.
  - *Verification*: Diagnostic monitor unit and integration test.

- **REQ-ACT-DIAG-02**: The Actuator ECU shall store confirmed DTCs together with freeze-frame data and occurrence counters in non-volatile memory.
  - *Rationale*: Preserves evidence for service and warranty investigations.
  - *Verification*: Fault injection followed by UDS readout after reset.

- **REQ-ACT-DIAG-03**: The Actuator ECU shall support diagnostic services for DTC read, DTC clear, routine control, data identifier read, and ECU reset subject to session permissions.
  - *Rationale*: Defines minimum serviceability expectations.
  - *Verification*: ISO 14229 service test campaign.

- **REQ-ACT-DIAG-04**: The Actuator ECU shall execute power-on self-tests and periodic runtime monitors for all safety-relevant elements allocated to diagnostics.
  - *Rationale*: Ensures diagnostic coverage is implemented in operation and at startup.
  - *Verification*: Self-test coverage analysis and monitored execution trace.

#### 8.8.5 Safety requirements

- **REQ-ACT-SAFE-01**: If a fault can lead to hazardous behaviour, the Actuator ECU shall remove hazardous drive energy and move to safe position within the allocated fault-tolerant time interval.
  - *Rationale*: Primary safety containment rule.
  - *Verification*: Fault injection with reaction-time measurement.

- **REQ-ACT-SAFE-02**: The Actuator ECU shall provide explicit health status for safety-relevant outputs so that dependent systems can detect degraded integrity.
  - *Rationale*: Avoids unsafe use of invalid information.
  - *Verification*: Interface-level safety mechanism test.

- **REQ-ACT-SAFE-03**: The Actuator ECU shall inhibit unsafe function activation when any prerequisite safety condition is not met.
  - *Rationale*: Prevents unsafe entry into automatic or assisted modes.
  - *Verification*: Precondition violation test across activation paths.

- **REQ-ACT-SAFE-04**: The Actuator ECU shall log safety-relevant fault transitions and operating context needed for post-event analysis.
  - *Rationale*: Supports field safety investigations.
  - *Verification*: Event memory verification and trace review.

#### 8.8.6 Security requirements

- **REQ-ACT-SEC-01**: The Actuator ECU shall verify software authenticity and integrity during boot before executing application software.
  - *Rationale*: Implements secure boot as a baseline cybersecurity control.
  - *Verification*: Cryptographic boot-chain validation test.

- **REQ-ACT-SEC-02**: The Actuator ECU shall restrict security-relevant services to authenticated and authorised entities.
  - *Rationale*: Prevents unauthorised control and configuration changes.
  - *Verification*: Access control and penetration test.

- **REQ-ACT-SEC-03**: The Actuator ECU shall protect security credentials from readout, downgrade, and replay attacks.
  - *Rationale*: Preserves trust anchors across lifecycle states.
  - *Verification*: Security review and negative diagnostic access test.

- **REQ-ACT-SEC-04**: The Actuator ECU shall record and rate-limit repeated invalid security requests.
  - *Rationale*: Supports detection of attack attempts and brute-force resistance.
  - *Verification*: Cybersecurity robustness test.

#### 8.8.7 Timing requirements

- **REQ-ACT-TIME-01**: The Actuator ECU shall respond to wake-up, enable, or cancel commands within one application cycle plus communication latency.
  - *Rationale*: Ensures predictable temporal behaviour visible at vehicle level.
  - *Verification*: End-to-end latency measurement.

- **REQ-ACT-TIME-02**: The Actuator ECU shall refresh safety-relevant outputs at a periodicity consistent with the allocated FTTI and interface budget.
  - *Rationale*: Aligns timing with safety analysis assumptions.
  - *Verification*: Schedule analysis and runtime timestamp trace.

- **REQ-ACT-TIME-03**: The Actuator ECU shall service the hardware watchdog within the configured window during all valid operating states.
  - *Rationale*: Detects deadlock or severe timing failure.
  - *Verification*: Watchdog window monitoring and stall injection.

- **REQ-ACT-TIME-04**: The Actuator ECU shall detect loss of its time base or task overrun and transition to the defined fallback mode.
  - *Rationale*: Prevents uncontrolled execution after scheduler corruption.
  - *Verification*: OS fault injection and timing overrun test.

#### 8.8.8 Failure-handling requirements

- **REQ-ACT-FAIL-01**: If a required input becomes unavailable, the Actuator ECU shall enter reduced authority or limp-home actuation and indicate the degraded status externally.
  - *Rationale*: Provides deterministic fallback when prerequisites are lost.
  - *Verification*: Missing-input test with external status observation.

- **REQ-ACT-FAIL-02**: If an unrecoverable internal error is detected, the Actuator ECU shall issue actuator fault status before or during the transition to safe state where technically feasible.
  - *Rationale*: Improves diagnosability and user awareness.
  - *Verification*: Internal fault injection with HMI and network observation.

- **REQ-ACT-FAIL-03**: The Actuator ECU shall attempt controlled recovery only after the root cause monitor indicates that restart conditions are valid.
  - *Rationale*: Avoids oscillation between fault and restart states.
  - *Verification*: Recovery logic test with persistent and intermittent faults.

- **REQ-ACT-FAIL-04**: After recovery from a transient fault, the Actuator ECU shall revalidate all safety-relevant inputs and outputs before resuming full function.
  - *Rationale*: Prevents unsafe resumption after partial recovery.
  - *Verification*: Reset-and-resume integration test.

### 8.10 Cross-System Requirement Review Checklist

- Is every externally visible function tied to a state or trigger?
- Are all timing values measurable and allocated to a responsible component?
- Are missing data, stale data, invalid data, and contradictory data all handled explicitly?
- Do interface requirements identify source ECU, destination ECU, signal name, cycle time, timeout, and fault reaction?
- Are DTC storage, diagnostic permissions, and freeze-frame content defined?
- Do safety requirements identify safe state, warning strategy, and fallback conditions?
- Do cybersecurity requirements cover secure boot, diagnostics authentication, update protection, and event logging?
- Is degraded behaviour safe, bounded, and visible to the driver or supervisory controller?

## Section 9: ADAS REQUIREMENTS ENGINEERING

ADAS requirements need a stronger emphasis on perception validity, timing, human-machine interaction, and graceful degradation than many conventional ECUs.

### 9.1 ADAS Requirement Pattern

```text
When <trigger condition> and <all activation conditions are valid>,
the <ADAS feature> shall <issue warning / control request / intervention>
within <timing budget>, unless <driver override or higher-priority inhibit condition> applies.
```

### 9.2 Adaptive Cruise Control (ACC)

```text
OFF -> STANDBY -> ACTIVE_SPEED_CONTROL -> ACTIVE_DISTANCE_CONTROL -> HOLD/RESUME
  ^         |             |                       |                  |
  |         +--fault------+-----------------------+--------cancel----+
  +-----------------------------driver off / ignition off------------+
```

#### 9.2.2 Activation

- **REQ-ACC-ACTIVA-01**: The ACC system shall activate only in valid speed and health conditions; reject activation on invalid brake, speed, or perception inputs.
  - *Rationale*: Defines expected ACC behaviour for activation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-ACTIVA-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to activation.
  - *Rationale*: Defines expected ACC behaviour for activation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-ACTIVA-03**: The ACC system shall expose activation status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for activation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.3 Deactivation

- **REQ-ACC-DEACTI-01**: The ACC system shall cancel on driver cancel, brake override, ignition off, or confirmed critical fault.
  - *Rationale*: Defines expected ACC behaviour for deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DEACTI-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to deactivation.
  - *Rationale*: Defines expected ACC behaviour for deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DEACTI-03**: The ACC system shall expose deactivation status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.4 Speed control

- **REQ-ACC-SPEEDC-01**: The ACC system shall regulate toward set speed with bounded acceleration and jerk.
  - *Rationale*: Defines expected ACC behaviour for speed control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-SPEEDC-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to speed control.
  - *Rationale*: Defines expected ACC behaviour for speed control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-SPEEDC-03**: The ACC system shall expose speed control status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for speed control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.5 Distance control

- **REQ-ACC-DISTAN-01**: The ACC system shall maintain selected time gap to in-path lead target.
  - *Rationale*: Defines expected ACC behaviour for distance control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DISTAN-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to distance control.
  - *Rationale*: Defines expected ACC behaviour for distance control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DISTAN-03**: The ACC system shall expose distance control status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for distance control.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.6 Target detection

- **REQ-ACC-TARGET-01**: The ACC system shall select the closest valid in-path target using confidence and lane assignment.
  - *Rationale*: Defines expected ACC behaviour for target detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-TARGET-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to target detection.
  - *Rationale*: Defines expected ACC behaviour for target detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-TARGET-03**: The ACC system shall expose target detection status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for target detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.7 Target loss

- **REQ-ACC-TARGET-01**: The ACC system shall fall back from distance mode to speed mode or cancel if loss is suspicious.
  - *Rationale*: Defines expected ACC behaviour for target loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-TARGET-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to target loss.
  - *Rationale*: Defines expected ACC behaviour for target loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-TARGET-03**: The ACC system shall expose target loss status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for target loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.8 Driver override

- **REQ-ACC-DRIVER-01**: The ACC system shall yield to accelerator or brake override according to feature concept.
  - *Rationale*: Defines expected ACC behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DRIVER-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to driver override.
  - *Rationale*: Defines expected ACC behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DRIVER-03**: The ACC system shall expose driver override status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.9 Brake intervention

- **REQ-ACC-BRAKEI-01**: The ACC system shall request service braking if torque reduction alone is insufficient.
  - *Rationale*: Defines expected ACC behaviour for brake intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-BRAKEI-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to brake intervention.
  - *Rationale*: Defines expected ACC behaviour for brake intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-BRAKEI-03**: The ACC system shall expose brake intervention status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for brake intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.10 Sensor failure

- **REQ-ACC-SENSOR-01**: The ACC system shall disable or degrade feature on radar/camera failure.
  - *Rationale*: Defines expected ACC behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-SENSOR-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to sensor failure.
  - *Rationale*: Defines expected ACC behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-SENSOR-03**: The ACC system shall expose sensor failure status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.11 Communication failure

- **REQ-ACC-COMMUN-01**: The ACC system shall cancel on loss of speed, brake, powertrain, or brake-ack signals.
  - *Rationale*: Defines expected ACC behaviour for communication failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-COMMUN-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to communication failure.
  - *Rationale*: Defines expected ACC behaviour for communication failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-COMMUN-03**: The ACC system shall expose communication failure status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for communication failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.12 Degraded operation

- **REQ-ACC-DEGRAD-01**: The ACC system shall reduce speed range or function scope when perception confidence is degraded.
  - *Rationale*: Defines expected ACC behaviour for degraded operation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DEGRAD-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to degraded operation.
  - *Rationale*: Defines expected ACC behaviour for degraded operation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DEGRAD-03**: The ACC system shall expose degraded operation status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for degraded operation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.2.13 Driver warning

- **REQ-ACC-DRIVER-01**: The ACC system shall show set speed, gap, active state, degraded state, and takeover expectations.
  - *Rationale*: Defines expected ACC behaviour for driver warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DRIVER-02**: The ACC system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to driver warning.
  - *Rationale*: Defines expected ACC behaviour for driver warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-ACC-DRIVER-03**: The ACC system shall expose driver warning status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected ACC behaviour for driver warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

### 9.3 Automatic Emergency Braking (AEB)

#### 9.3.2 Object detection

- **REQ-AEB-OBJECT-01**: The AEB system shall detect and track vehicles, pedestrians, and cyclists within the validated ODD.
  - *Rationale*: Defines expected AEB behaviour for object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-OBJECT-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to object detection.
  - *Rationale*: Defines expected AEB behaviour for object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-OBJECT-03**: The AEB system shall expose object detection status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.3 Collision prediction

- **REQ-AEB-COLLIS-01**: The AEB system shall compute collision metrics every cycle using host, target, and road-condition inputs.
  - *Rationale*: Defines expected AEB behaviour for collision prediction.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-COLLIS-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to collision prediction.
  - *Rationale*: Defines expected AEB behaviour for collision prediction.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-COLLIS-03**: The AEB system shall expose collision prediction status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for collision prediction.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.4 Warning

- **REQ-AEB-WARNIN-01**: The AEB system shall issue FCW before emergency braking where time permits.
  - *Rationale*: Defines expected AEB behaviour for warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-WARNIN-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to warning.
  - *Rationale*: Defines expected AEB behaviour for warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-WARNIN-03**: The AEB system shall expose warning status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for warning.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.5 Pre-braking

- **REQ-AEB-PREBRA-01**: The AEB system shall request pressure pre-fill or pre-brake phase before full intervention.
  - *Rationale*: Defines expected AEB behaviour for pre-braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-PREBRA-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to pre-braking.
  - *Rationale*: Defines expected AEB behaviour for pre-braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-PREBRA-03**: The AEB system shall expose pre-braking status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for pre-braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.6 Emergency braking

- **REQ-AEB-EMERGE-01**: The AEB system shall request emergency braking within the allocated budget when the emergency threshold is crossed.
  - *Rationale*: Defines expected AEB behaviour for emergency braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-EMERGE-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to emergency braking.
  - *Rationale*: Defines expected AEB behaviour for emergency braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-EMERGE-03**: The AEB system shall expose emergency braking status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for emergency braking.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.7 Driver override

- **REQ-AEB-DRIVER-01**: The AEB system shall allow valid driver braking dominance and scenario-dependent steering avoidance.
  - *Rationale*: Defines expected AEB behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-DRIVER-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to driver override.
  - *Rationale*: Defines expected AEB behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-DRIVER-03**: The AEB system shall expose driver override status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.8 Sensor failure

- **REQ-AEB-SENSOR-01**: The AEB system shall disable or downgrade AEB according to approved sensor-availability matrix.
  - *Rationale*: Defines expected AEB behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-SENSOR-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to sensor failure.
  - *Rationale*: Defines expected AEB behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-SENSOR-03**: The AEB system shall expose sensor failure status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.9 False object detection

- **REQ-AEB-FALSEO-01**: The AEB system shall suppress emergency braking on overhead infrastructure and low-confidence clutter.
  - *Rationale*: Defines expected AEB behaviour for false object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-FALSEO-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to false object detection.
  - *Rationale*: Defines expected AEB behaviour for false object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-FALSEO-03**: The AEB system shall expose false object detection status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for false object detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.10 Communication loss

- **REQ-AEB-COMMUN-01**: The AEB system shall detect lost brake-path acknowledgement or critical motion-signal loss.
  - *Rationale*: Defines expected AEB behaviour for communication loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-COMMUN-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to communication loss.
  - *Rationale*: Defines expected AEB behaviour for communication loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-COMMUN-03**: The AEB system shall expose communication loss status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for communication loss.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.3.11 Safe-state transition

- **REQ-AEB-SAFEST-01**: The AEB system shall latch unavailable state and restore manual responsibility explicitly.
  - *Rationale*: Defines expected AEB behaviour for safe-state transition.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-SAFEST-02**: The AEB system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to safe-state transition.
  - *Rationale*: Defines expected AEB behaviour for safe-state transition.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-AEB-SAFEST-03**: The AEB system shall expose safe-state transition status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected AEB behaviour for safe-state transition.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

### 9.4 Lane Keeping Assist (LKA)

#### 9.4.2 Lane detection

- **REQ-LKA-LANEDE-01**: The LKA system shall compute lane boundaries and confidence every cycle.
  - *Rationale*: Defines expected LKA behaviour for lane detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-LANEDE-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to lane detection.
  - *Rationale*: Defines expected LKA behaviour for lane detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-LANEDE-03**: The LKA system shall expose lane detection status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for lane detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.3 Lane departure

- **REQ-LKA-LANEDE-01**: The LKA system shall detect unintentional departure while suppressing intentional lane changes.
  - *Rationale*: Defines expected LKA behaviour for lane departure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-LANEDE-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to lane departure.
  - *Rationale*: Defines expected LKA behaviour for lane departure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-LANEDE-03**: The LKA system shall expose lane departure status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for lane departure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.4 Steering intervention

- **REQ-LKA-STEERI-01**: The LKA system shall request corrective torque within comfort and controllability limits.
  - *Rationale*: Defines expected LKA behaviour for steering intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-STEERI-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to steering intervention.
  - *Rationale*: Defines expected LKA behaviour for steering intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-STEERI-03**: The LKA system shall expose steering intervention status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for steering intervention.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.5 Driver hands-on detection

- **REQ-LKA-DRIVER-01**: The LKA system shall require valid supervision state where the concept assumes shared control.
  - *Rationale*: Defines expected LKA behaviour for driver hands-on detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-DRIVER-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to driver hands-on detection.
  - *Rationale*: Defines expected LKA behaviour for driver hands-on detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-DRIVER-03**: The LKA system shall expose driver hands-on detection status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for driver hands-on detection.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.6 System activation/deactivation

- **REQ-LKA-SYSTEM-01**: The LKA system shall enter active mode only when lane, speed, steering, and health preconditions are valid.
  - *Rationale*: Defines expected LKA behaviour for system activation/deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-SYSTEM-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to system activation/deactivation.
  - *Rationale*: Defines expected LKA behaviour for system activation/deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-SYSTEM-03**: The LKA system shall expose system activation/deactivation status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for system activation/deactivation.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.7 Sensor failure

- **REQ-LKA-SENSOR-01**: The LKA system shall cancel intervention on camera, steering-angle, or yaw-rate invalidity.
  - *Rationale*: Defines expected LKA behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-SENSOR-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to sensor failure.
  - *Rationale*: Defines expected LKA behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-SENSOR-03**: The LKA system shall expose sensor failure status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for sensor failure.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

#### 9.4.8 Driver override

- **REQ-LKA-DRIVER-01**: The LKA system shall release torque promptly when driver counter-steer exceeds threshold.
  - *Rationale*: Defines expected LKA behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-DRIVER-02**: The LKA system shall detect invalid prerequisites, conflicting driver actions, and input-quality violations relevant to driver override.
  - *Rationale*: Defines expected LKA behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

- **REQ-LKA-DRIVER-03**: The LKA system shall expose driver override status, faults, and fallback behaviour to diagnostics and HMI where applicable.
  - *Rationale*: Defines expected LKA behaviour for driver override.
  - *Verification*: Scenario-based simulation, HIL, and vehicle test.

### 9.5 Additional ADAS Feature Requirement Examples

#### 9.5.1 Forward Collision Warning (FCW)

- **REQ-FORWARDC-01**: The Forward Collision Warning (FCW) feature shall warn the driver when predicted time-to-collision falls below the threshold.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-FORWARDC-02**: The Forward Collision Warning (FCW) feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-FORWARDC-03**: The Forward Collision Warning (FCW) feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-FORWARDC-04**: The Forward Collision Warning (FCW) feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-FORWARDC-05**: The Forward Collision Warning (FCW) feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.2 Lane Departure Alert (LDA)

- **REQ-LANEDEPA-01**: The Lane Departure Alert (LDA) feature shall warn before lane crossing when intervention is unavailable or not configured.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-LANEDEPA-02**: The Lane Departure Alert (LDA) feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-LANEDEPA-03**: The Lane Departure Alert (LDA) feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-LANEDEPA-04**: The Lane Departure Alert (LDA) feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-LANEDEPA-05**: The Lane Departure Alert (LDA) feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.3 Blind Spot Detection (BSD)

- **REQ-BLINDSPO-01**: The Blind Spot Detection (BSD) feature shall detect relevant objects in adjacent blind zones and warn on lane-change intent.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-BLINDSPO-02**: The Blind Spot Detection (BSD) feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-BLINDSPO-03**: The Blind Spot Detection (BSD) feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-BLINDSPO-04**: The Blind Spot Detection (BSD) feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-BLINDSPO-05**: The Blind Spot Detection (BSD) feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.4 Rear Cross Traffic Alert (RCTA)

- **REQ-REARCROS-01**: The Rear Cross Traffic Alert (RCTA) feature shall monitor cross traffic while reverse gear is active.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-REARCROS-02**: The Rear Cross Traffic Alert (RCTA) feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-REARCROS-03**: The Rear Cross Traffic Alert (RCTA) feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-REARCROS-04**: The Rear Cross Traffic Alert (RCTA) feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-REARCROS-05**: The Rear Cross Traffic Alert (RCTA) feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.5 Traffic Sign Recognition (TSR)

- **REQ-TRAFFICS-01**: The Traffic Sign Recognition (TSR) feature shall detect, classify, and age out recognised signs while managing ambiguity.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICS-02**: The Traffic Sign Recognition (TSR) feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICS-03**: The Traffic Sign Recognition (TSR) feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICS-04**: The Traffic Sign Recognition (TSR) feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICS-05**: The Traffic Sign Recognition (TSR) feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.6 Parking Assist

- **REQ-PARKINGA-01**: The Parking Assist feature shall guide or control parking manoeuvres only with a valid slot and obstacle model.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-PARKINGA-02**: The Parking Assist feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-PARKINGA-03**: The Parking Assist feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-PARKINGA-04**: The Parking Assist feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-PARKINGA-05**: The Parking Assist feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.7 Highway Assist

- **REQ-HIGHWAYA-01**: The Highway Assist feature shall combine longitudinal and lateral control only within the approved highway ODD.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-HIGHWAYA-02**: The Highway Assist feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-HIGHWAYA-03**: The Highway Assist feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-HIGHWAYA-04**: The Highway Assist feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-HIGHWAYA-05**: The Highway Assist feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.8 Traffic Jam Assist

- **REQ-TRAFFICJ-01**: The Traffic Jam Assist feature shall support low-speed stop-and-go traffic with explicit takeover management.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICJ-02**: The Traffic Jam Assist feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICJ-03**: The Traffic Jam Assist feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICJ-04**: The Traffic Jam Assist feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-TRAFFICJ-05**: The Traffic Jam Assist feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

#### 9.5.9 Driver Monitoring

- **REQ-DRIVERMO-01**: The Driver Monitoring feature shall estimate driver attention and publish supervision status for dependent ADAS features.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-DRIVERMO-02**: The Driver Monitoring feature shall define explicit activation, deactivation, and degraded-operation rules.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-DRIVERMO-03**: The Driver Monitoring feature shall communicate active, degraded, unavailable, and urgent states to the driver.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-DRIVERMO-04**: The Driver Monitoring feature shall detect sensor or communication loss affecting its validated function envelope.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

- **REQ-DRIVERMO-05**: The Driver Monitoring feature shall record relevant diagnostic and event data for field analysis and calibration feedback.
  - *Rationale*: Representative system-level requirement for the feature.
  - *Verification*: System test, scenario simulation, and HIL as applicable.

### 9.6 ADAS Requirement Review Questions

- What is the minimum sensor set required for nominal operation and for degraded operation?
- Which driver overrides are allowed, and in what order of priority?
- How are perception confidence and uncertainty exposed to control logic?
- What happens when the feature loses authority but the hazard remains present?
- Which HMI messages are advisory, cautionary, urgent, or takeover related?
- Does every activation condition have an explicit deactivation and recovery rule?

## Section 10: TELEMATICS REQUIREMENTS ENGINEERING

Telematics requirements combine automotive real-time expectations with off-board networking behaviour.

### 10.1 TCU

- **REQ-TCU-01**: The TCU function shall initialise cellular, GNSS, bus, security, and storage services in a controlled sequence.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-TCU-02**: The TCU function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-TCU-03**: The TCU function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-TCU-04**: The TCU function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.2 Cellular connectivity

- **REQ-CELLULAR-01**: The Cellular connectivity function shall establish packet-data service and handle registration loss using bounded retry logic.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CELLULAR-02**: The Cellular connectivity function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CELLULAR-03**: The Cellular connectivity function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CELLULAR-04**: The Cellular connectivity function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.3 GNSS

- **REQ-GNSS-01**: The GNSS function shall publish position, time, velocity, and fix quality with validity status.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-GNSS-02**: The GNSS function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-GNSS-03**: The GNSS function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-GNSS-04**: The GNSS function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.4 Bluetooth

- **REQ-BLUETOOT-01**: The Bluetooth function shall pair only with authenticated devices and clear incomplete sessions on timeout.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BLUETOOT-02**: The Bluetooth function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BLUETOOT-03**: The Bluetooth function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BLUETOOT-04**: The Bluetooth function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.5 Wi-Fi

- **REQ-WIFI-01**: The Wi-Fi function shall provide authenticated service sessions for approved production use cases.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-WIFI-02**: The Wi-Fi function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-WIFI-03**: The Wi-Fi function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-WIFI-04**: The Wi-Fi function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.6 CAN communication

- **REQ-CANCOMMU-01**: The CAN communication function shall validate telematics-relevant signals for source, freshness, counter, and CRC.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CANCOMMU-02**: The CAN communication function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CANCOMMU-03**: The CAN communication function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CANCOMMU-04**: The CAN communication function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.7 Ethernet

- **REQ-ETHERNET-01**: The Ethernet function shall establish authenticated service-oriented communication and monitor link state.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ETHERNET-02**: The Ethernet function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ETHERNET-03**: The Ethernet function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ETHERNET-04**: The Ethernet function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.8 Cloud communication

- **REQ-CLOUDCOM-01**: The Cloud communication function shall use mutually authenticated TLS and schema-validated messages.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CLOUDCOM-02**: The Cloud communication function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CLOUDCOM-03**: The Cloud communication function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-CLOUDCOM-04**: The Cloud communication function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.9 eCall

- **REQ-ECALL-01**: The eCall function shall start emergency communication within the legal time budget after confirmed trigger.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ECALL-02**: The eCall function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ECALL-03**: The eCall function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-ECALL-04**: The eCall function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.10 bCall

- **REQ-BCALL-01**: The bCall function shall support manual breakdown-call initiation without interfering with eCall.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BCALL-02**: The bCall function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BCALL-03**: The bCall function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-BCALL-04**: The bCall function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.11 Remote diagnostics

- **REQ-REMOTEDI-01**: The Remote diagnostics function shall allow only authenticated, authorised, and policy-permitted remote diagnostic sessions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTEDI-02**: The Remote diagnostics function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTEDI-03**: The Remote diagnostics function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTEDI-04**: The Remote diagnostics function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.12 Remote commands

- **REQ-REMOTECO-01**: The Remote commands function shall execute commands only after authenticity, freshness, authorisation, and vehicle-precondition checks.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTECO-02**: The Remote commands function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTECO-03**: The Remote commands function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-REMOTECO-04**: The Remote commands function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.13 OTA

- **REQ-OTA-01**: The OTA function shall verify package authenticity, compatibility, and recoverability before installation.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-OTA-02**: The OTA function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-OTA-03**: The OTA function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-OTA-04**: The OTA function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.14 Vehicle data collection

- **REQ-VEHICLED-01**: The Vehicle data collection function shall collect only approved signals and protect integrity, privacy, and retention rules.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-VEHICLED-02**: The Vehicle data collection function shall define behaviour for connection establishment, timeout, retry, authentication failure, and message validation failure.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-VEHICLED-03**: The Vehicle data collection function shall protect data integrity across network loss, ECU restart, power loss, and backend unavailability.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

- **REQ-VEHICLED-04**: The Vehicle data collection function shall provide deterministic status for vehicle unavailable, backend unavailable, success, partial success, and failed execution conditions.
  - *Rationale*: Representative telematics requirement pattern.
  - *Verification*: End-to-end connectivity test, fault injection, and backend integration test.

### 10.15 Cross-Cutting Failure and Recovery Matrix

| Situation | Typical Requirement Intent |
|---|---|
| Connection establishment | Define prerequisites, timeout, retry policy, and acknowledgement. |
| Network loss | Switch to buffer mode, preserve critical services, and expose degraded status. |
| Timeout | Abort or retry within bounded time and return deterministic error status. |
| Retry | Use bounded retry counts or exponential backoff; prevent duplicate actuation. |
| Authentication failure | Reject the session, log the event, and rate-limit repeated failures. |
| Message validation failure | Discard invalid payloads and preserve an audit trail. |
| Data integrity failure | Request retransmission or stop execution until integrity is restored. |
| Power loss | Protect persistent state and maintain bootable recovery path. |
| ECU restart | Resume or roll back using checkpointed state. |
| Backend unavailable | Queue non-urgent work and preserve emergency services. |
| Vehicle unavailable | Return not-executed status without guessing or forcing execution. |

## Section 11: INSTRUMENT CLUSTER REQUIREMENTS

The instrument cluster is a safety-relevant HMI ECU because it communicates mandatory vehicle status, warnings, and ADAS availability to the driver.

### 11.1 Vehicle speed

- **REQ-IC-01-01**: The instrument cluster shall display and manage vehicle speed according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-01-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to vehicle speed.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-01-03**: The instrument cluster shall enter the defined fallback or unavailable state when vehicle speed data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-01-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when vehicle speed is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.2 RPM

- **REQ-IC-02-01**: The instrument cluster shall display and manage rpm according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-02-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to rpm.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-02-03**: The instrument cluster shall enter the defined fallback or unavailable state when rpm data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-02-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when rpm is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.3 Fuel level

- **REQ-IC-03-01**: The instrument cluster shall display and manage fuel level according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-03-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to fuel level.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-03-03**: The instrument cluster shall enter the defined fallback or unavailable state when fuel level data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-03-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when fuel level is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.4 Temperature

- **REQ-IC-04-01**: The instrument cluster shall display and manage temperature according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-04-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to temperature.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-04-03**: The instrument cluster shall enter the defined fallback or unavailable state when temperature data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-04-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when temperature is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.5 Warning lamps

- **REQ-IC-05-01**: The instrument cluster shall display and manage warning lamps according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-05-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to warning lamps.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-05-03**: The instrument cluster shall enter the defined fallback or unavailable state when warning lamps data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-05-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when warning lamps is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.6 Tell-tales

- **REQ-IC-06-01**: The instrument cluster shall display and manage tell-tales according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-06-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to tell-tales.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-06-03**: The instrument cluster shall enter the defined fallback or unavailable state when tell-tales data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-06-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when tell-tales is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.7 ADAS notifications

- **REQ-IC-07-01**: The instrument cluster shall display and manage adas notifications according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-07-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to adas notifications.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-07-03**: The instrument cluster shall enter the defined fallback or unavailable state when adas notifications data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-07-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when adas notifications is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.8 Driver messages

- **REQ-IC-08-01**: The instrument cluster shall display and manage driver messages according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-08-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to driver messages.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-08-03**: The instrument cluster shall enter the defined fallback or unavailable state when driver messages data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-08-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when driver messages is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.9 Display brightness

- **REQ-IC-09-01**: The instrument cluster shall display and manage display brightness according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-09-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to display brightness.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-09-03**: The instrument cluster shall enter the defined fallback or unavailable state when display brightness data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-09-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when display brightness is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.10 Display failure

- **REQ-IC-10-01**: The instrument cluster shall display and manage display failure according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-10-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to display failure.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-10-03**: The instrument cluster shall enter the defined fallback or unavailable state when display failure data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-10-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when display failure is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.11 Communication loss

- **REQ-IC-11-01**: The instrument cluster shall display and manage communication loss according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-11-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to communication loss.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-11-03**: The instrument cluster shall enter the defined fallback or unavailable state when communication loss data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-11-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when communication loss is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.12 Incorrect signal

- **REQ-IC-12-01**: The instrument cluster shall display and manage incorrect signal according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-12-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to incorrect signal.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-12-03**: The instrument cluster shall enter the defined fallback or unavailable state when incorrect signal data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-12-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when incorrect signal is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.13 Frozen display

- **REQ-IC-13-01**: The instrument cluster shall display and manage frozen display according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-13-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to frozen display.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-13-03**: The instrument cluster shall enter the defined fallback or unavailable state when frozen display data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-13-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when frozen display is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.14 Boot

- **REQ-IC-14-01**: The instrument cluster shall display and manage boot according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-14-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to boot.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-14-03**: The instrument cluster shall enter the defined fallback or unavailable state when boot data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-14-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when boot is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.15 Shutdown

- **REQ-IC-15-01**: The instrument cluster shall display and manage shutdown according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-15-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to shutdown.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-15-03**: The instrument cluster shall enter the defined fallback or unavailable state when shutdown data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-15-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when shutdown is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.16 Diagnostic mode

- **REQ-IC-16-01**: The instrument cluster shall display and manage diagnostic mode according to the approved HMI specification and source-signal definition.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-16-02**: The instrument cluster shall apply timing, range, plausibility, and freshness checks relevant to diagnostic mode.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-16-03**: The instrument cluster shall enter the defined fallback or unavailable state when diagnostic mode data or rendering becomes invalid.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

- **REQ-IC-16-04**: The instrument cluster shall log diagnostic evidence and preserve warning priority when diagnostic mode is affected by faults or degraded communication.
  - *Rationale*: Representative cluster requirement pattern covering correctness, timing, safety, and diagnostics.
  - *Verification*: Signal replay, display timing measurement, and fault injection.

### 11.17 Instrument Cluster Timing and Safety Notes

- Speed display, critical tell-tales, and red warnings should have an explicitly budgeted end-to-end latency.
- Cluster requirements should identify what happens when the input signal is stale, invalid, contradictory, or frozen.
- If a warning cannot be rendered, the vehicle architecture should define whether a fallback lamp path or redundant HMI path exists.
- Watchdog and render-heartbeat monitoring are often necessary because a syntactically healthy ECU can still present a frozen image.

## Section 12: REQUIREMENTS + FUNCTIONAL SAFETY

Functional safety requirements are derived from hazard analysis and then decomposed through the architecture until they become implementable and testable.

### 12.1 Safety Traceability Flow

```text
HARA -> Hazard -> Safety Goal -> FSR -> TSR -> System Requirement -> SwRS -> HwRS -> Test Requirement
```

### 12.2 What Must Be Traced for Every Safety Requirement

- Originating item and hazardous event
- ASIL classification and rationale
- Allocated functional safety requirement
- Allocated technical safety requirement and architectural element
- Derived system, software, and hardware requirements
- Verification method, acceptance criteria, and evidence location
- Dependencies on interfaces, calibration, watchdogs, diagnostics, or supervision mechanisms
- Status across change requests, releases, and baselines

### 12.3 Sample Safety Traceability Matrix Structure

| Level | Example Content |
|---|---|
| HARA | Hazardous event: unintended ACC acceleration toward slower lead vehicle |
| Safety Goal | Prevent unintended sustained longitudinal acceleration that can create rear-end collision risk |
| FSR | Detect invalid target selection and inhibit propulsion request |
| TSR | Implement target plausibility monitor and safe torque arbitration |
| System Requirement | ACC controller shall cancel active control on target plausibility failure |
| Software Requirement | Target manager shall invalidate lead target on multi-cycle inconsistency |
| Hardware Requirement | Radar interface shall provide CRC, alive counter, and health status |
| Test Requirement | Inject target-ID corruption and verify ACC cancel within 100 ms |

### 12.4 Example 01

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: host vehicle follows a slower vehicle on highway
- **Malfunctioning Behaviour**: wrong-target acceleration
- **Hazard**: rear-end collision with slower lead vehicle
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by wrong-target acceleration.
- **FSR**: The ACC longitudinal control shall detect wrong-target acceleration and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control wrong-target acceleration.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for wrong-target acceleration within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with wrong-target acceleration and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of wrong-target acceleration.
- **Test Requirement**: Inject or simulate wrong-target acceleration in the situation 'host vehicle follows a slower vehicle on highway' and verify that the hazard 'rear-end collision with slower lead vehicle' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 01 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.5 Example 02

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: highway following with valid lead vehicle
- **Malfunctioning Behaviour**: failure to brake for slower lead vehicle
- **Hazard**: rear-end collision due to insufficient deceleration
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by failure to brake for slower lead vehicle.
- **FSR**: The ACC longitudinal control shall detect failure to brake for slower lead vehicle and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control failure to brake for slower lead vehicle.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for failure to brake for slower lead vehicle within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with failure to brake for slower lead vehicle and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of failure to brake for slower lead vehicle.
- **Test Requirement**: Inject or simulate failure to brake for slower lead vehicle in the situation 'highway following with valid lead vehicle' and verify that the hazard 'rear-end collision due to insufficient deceleration' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 02 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.6 Example 03

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: driver presses brake during active ACC
- **Malfunctioning Behaviour**: no cancel on brake input
- **Hazard**: loss of driver authority and potential collision
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no cancel on brake input.
- **FSR**: The ACC longitudinal control shall detect no cancel on brake input and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no cancel on brake input.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for no cancel on brake input within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with no cancel on brake input and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no cancel on brake input.
- **Test Requirement**: Inject or simulate no cancel on brake input in the situation 'driver presses brake during active ACC' and verify that the hazard 'loss of driver authority and potential collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 03 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.7 Example 04

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: open highway with no relevant lead object
- **Malfunctioning Behaviour**: unintended braking due to false target
- **Hazard**: rear-impact risk from following traffic
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by unintended braking due to false target.
- **FSR**: The ACC longitudinal control shall detect unintended braking due to false target and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control unintended braking due to false target.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for unintended braking due to false target within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with unintended braking due to false target and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of unintended braking due to false target.
- **Test Requirement**: Inject or simulate unintended braking due to false target in the situation 'open highway with no relevant lead object' and verify that the hazard 'rear-impact risk from following traffic' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 04 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.8 Example 05

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: communication recovers after network outage
- **Malfunctioning Behaviour**: uncontrolled resume after communication recovery
- **Hazard**: unexpected acceleration or braking surprises the driver
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by uncontrolled resume after communication recovery.
- **FSR**: The ACC longitudinal control shall detect uncontrolled resume after communication recovery and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control uncontrolled resume after communication recovery.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for uncontrolled resume after communication recovery within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with uncontrolled resume after communication recovery and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of uncontrolled resume after communication recovery.
- **Test Requirement**: Inject or simulate uncontrolled resume after communication recovery in the situation 'communication recovers after network outage' and verify that the hazard 'unexpected acceleration or braking surprises the driver' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 05 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.9 Example 06

- **Item / Function**: ACC longitudinal control
- **Operational Situation**: stop-and-go traffic at low speed
- **Malfunctioning Behaviour**: automatic resume with seat-belt or readiness precondition violated
- **Hazard**: unexpected vehicle motion without valid driver readiness
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by automatic resume with seat-belt or readiness precondition violated.
- **FSR**: The ACC longitudinal control shall detect automatic resume with seat-belt or readiness precondition violated and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control automatic resume with seat-belt or readiness precondition violated.
- **System Requirement**: The ACC longitudinal control shall execute the defined fault reaction for automatic resume with seat-belt or readiness precondition violated within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to ACC longitudinal control shall monitor the relevant inputs, state transitions, and outputs associated with automatic resume with seat-belt or readiness precondition violated and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to ACC longitudinal control shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of automatic resume with seat-belt or readiness precondition violated.
- **Test Requirement**: Inject or simulate automatic resume with seat-belt or readiness precondition violated in the situation 'stop-and-go traffic at low speed' and verify that the hazard 'unexpected vehicle motion without valid driver readiness' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 06 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.10 Example 07

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: approach to stationary or slow-moving obstacle
- **Malfunctioning Behaviour**: late intervention due to stale object list
- **Hazard**: delayed braking leading to collision or increased impact speed
- **Classification**: Derived and validated in HARA -> **ASIL D**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by late intervention due to stale object list.
- **FSR**: The AEB collision mitigation shall detect late intervention due to stale object list and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control late intervention due to stale object list.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for late intervention due to stale object list within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with late intervention due to stale object list and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of late intervention due to stale object list.
- **Test Requirement**: Inject or simulate late intervention due to stale object list in the situation 'approach to stationary or slow-moving obstacle' and verify that the hazard 'delayed braking leading to collision or increased impact speed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 07 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.11 Example 08

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: vehicle closes rapidly on obstacle
- **Malfunctioning Behaviour**: no braking on confirmed collision path
- **Hazard**: severe frontal collision
- **Classification**: Derived and validated in HARA -> **ASIL D**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no braking on confirmed collision path.
- **FSR**: The AEB collision mitigation shall detect no braking on confirmed collision path and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no braking on confirmed collision path.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for no braking on confirmed collision path within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with no braking on confirmed collision path and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no braking on confirmed collision path.
- **Test Requirement**: Inject or simulate no braking on confirmed collision path in the situation 'vehicle closes rapidly on obstacle' and verify that the hazard 'severe frontal collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 08 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.12 Example 09

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: vehicle passes under an overhead sign
- **Malfunctioning Behaviour**: false emergency braking for overhead infrastructure
- **Hazard**: unexpected harsh braking causing rear impact or loss of control
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by false emergency braking for overhead infrastructure.
- **FSR**: The AEB collision mitigation shall detect false emergency braking for overhead infrastructure and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control false emergency braking for overhead infrastructure.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for false emergency braking for overhead infrastructure within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with false emergency braking for overhead infrastructure and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of false emergency braking for overhead infrastructure.
- **Test Requirement**: Inject or simulate false emergency braking for overhead infrastructure in the situation 'vehicle passes under an overhead sign' and verify that the hazard 'unexpected harsh braking causing rear impact or loss of control' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 09 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.13 Example 10

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: obstacle disappears after avoidance or stop
- **Malfunctioning Behaviour**: failure to release braking after hazard resolved
- **Hazard**: unexpected stop in unsafe location or rear-end risk
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by failure to release braking after hazard resolved.
- **FSR**: The AEB collision mitigation shall detect failure to release braking after hazard resolved and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control failure to release braking after hazard resolved.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for failure to release braking after hazard resolved within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with failure to release braking after hazard resolved and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of failure to release braking after hazard resolved.
- **Test Requirement**: Inject or simulate failure to release braking after hazard resolved in the situation 'obstacle disappears after avoidance or stop' and verify that the hazard 'unexpected stop in unsafe location or rear-end risk' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 10 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.14 Example 11

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: AEB decides to brake but the brake path fails
- **Malfunctioning Behaviour**: brake path communication loss
- **Hazard**: no mitigation despite imminent collision
- **Classification**: Derived and validated in HARA -> **ASIL D**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by brake path communication loss.
- **FSR**: The AEB collision mitigation shall detect brake path communication loss and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control brake path communication loss.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for brake path communication loss within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with brake path communication loss and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of brake path communication loss.
- **Test Requirement**: Inject or simulate brake path communication loss in the situation 'AEB decides to brake but the brake path fails' and verify that the hazard 'no mitigation despite imminent collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 11 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.15 Example 12

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: camera fails during drive while radar remains healthy
- **Malfunctioning Behaviour**: undefined degraded mode selection
- **Hazard**: inconsistent driver expectation and missed mitigation
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by undefined degraded mode selection.
- **FSR**: The AEB collision mitigation shall detect undefined degraded mode selection and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control undefined degraded mode selection.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for undefined degraded mode selection within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with undefined degraded mode selection and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of undefined degraded mode selection.
- **Test Requirement**: Inject or simulate undefined degraded mode selection in the situation 'camera fails during drive while radar remains healthy' and verify that the hazard 'inconsistent driver expectation and missed mitigation' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 12 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.16 Example 13

- **Item / Function**: AEB collision mitigation
- **Operational Situation**: sensor fault disables AEB while driving
- **Malfunctioning Behaviour**: loss of braking capability not shown to driver
- **Hazard**: driver overestimates available protection
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by loss of braking capability not shown to driver.
- **FSR**: The AEB collision mitigation shall detect loss of braking capability not shown to driver and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control loss of braking capability not shown to driver.
- **System Requirement**: The AEB collision mitigation shall execute the defined fault reaction for loss of braking capability not shown to driver within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB collision mitigation shall monitor the relevant inputs, state transitions, and outputs associated with loss of braking capability not shown to driver and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB collision mitigation shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of loss of braking capability not shown to driver.
- **Test Requirement**: Inject or simulate loss of braking capability not shown to driver in the situation 'sensor fault disables AEB while driving' and verify that the hazard 'driver overestimates available protection' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 13 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.17 Example 14

- **Item / Function**: AEB and FCW combined feature
- **Operational Situation**: perception degradation removes braking capability but warning remains
- **Malfunctioning Behaviour**: FCW-only degraded mode not indicated
- **Hazard**: overtrust in residual function
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by FCW-only degraded mode not indicated.
- **FSR**: The AEB and FCW combined feature shall detect FCW-only degraded mode not indicated and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control FCW-only degraded mode not indicated.
- **System Requirement**: The AEB and FCW combined feature shall execute the defined fault reaction for FCW-only degraded mode not indicated within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to AEB and FCW combined feature shall monitor the relevant inputs, state transitions, and outputs associated with FCW-only degraded mode not indicated and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to AEB and FCW combined feature shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of FCW-only degraded mode not indicated.
- **Test Requirement**: Inject or simulate FCW-only degraded mode not indicated in the situation 'perception degradation removes braking capability but warning remains' and verify that the hazard 'overtrust in residual function' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 14 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.18 Example 15

- **Item / Function**: LKA lateral support
- **Operational Situation**: vehicle cruises on marked highway lane
- **Malfunctioning Behaviour**: wrong-direction steering torque
- **Hazard**: side-swipe or road departure hazard
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by wrong-direction steering torque.
- **FSR**: The LKA lateral support shall detect wrong-direction steering torque and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control wrong-direction steering torque.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for wrong-direction steering torque within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with wrong-direction steering torque and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of wrong-direction steering torque.
- **Test Requirement**: Inject or simulate wrong-direction steering torque in the situation 'vehicle cruises on marked highway lane' and verify that the hazard 'side-swipe or road departure hazard' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 15 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.19 Example 16

- **Item / Function**: LKA lateral support
- **Operational Situation**: driver drifts out of lane without indicator
- **Malfunctioning Behaviour**: no intervention during unintentional departure
- **Hazard**: road departure or side collision
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no intervention during unintentional departure.
- **FSR**: The LKA lateral support shall detect no intervention during unintentional departure and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no intervention during unintentional departure.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for no intervention during unintentional departure within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with no intervention during unintentional departure and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no intervention during unintentional departure.
- **Test Requirement**: Inject or simulate no intervention during unintentional departure in the situation 'driver drifts out of lane without indicator' and verify that the hazard 'road departure or side collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 16 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.20 Example 17

- **Item / Function**: LKA lateral support
- **Operational Situation**: driver intentionally steers against assistance
- **Malfunctioning Behaviour**: no release on driver override
- **Hazard**: driver fight and possible lane instability
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no release on driver override.
- **FSR**: The LKA lateral support shall detect no release on driver override and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no release on driver override.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for no release on driver override within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with no release on driver override and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no release on driver override.
- **Test Requirement**: Inject or simulate no release on driver override in the situation 'driver intentionally steers against assistance' and verify that the hazard 'driver fight and possible lane instability' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 17 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.21 Example 18

- **Item / Function**: LKA lateral support
- **Operational Situation**: poor lane markings in rain
- **Malfunctioning Behaviour**: intervention with invalid lane confidence
- **Hazard**: unexpected steering on uncertain scene
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by intervention with invalid lane confidence.
- **FSR**: The LKA lateral support shall detect intervention with invalid lane confidence and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control intervention with invalid lane confidence.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for intervention with invalid lane confidence within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with intervention with invalid lane confidence and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of intervention with invalid lane confidence.
- **Test Requirement**: Inject or simulate intervention with invalid lane confidence in the situation 'poor lane markings in rain' and verify that the hazard 'unexpected steering on uncertain scene' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 18 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.22 Example 19

- **Item / Function**: LKA lateral support
- **Operational Situation**: urban manoeuvring below operating speed
- **Malfunctioning Behaviour**: unintended activation at low speed
- **Hazard**: unexpected steering during low-speed manoeuvres
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by unintended activation at low speed.
- **FSR**: The LKA lateral support shall detect unintended activation at low speed and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control unintended activation at low speed.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for unintended activation at low speed within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with unintended activation at low speed and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of unintended activation at low speed.
- **Test Requirement**: Inject or simulate unintended activation at low speed in the situation 'urban manoeuvring below operating speed' and verify that the hazard 'unexpected steering during low-speed manoeuvres' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 19 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.23 Example 20

- **Item / Function**: LKA lateral support
- **Operational Situation**: EPS authority becomes degraded during operation
- **Malfunctioning Behaviour**: warning-only fallback not entered
- **Hazard**: insufficient or inconsistent lane correction
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by warning-only fallback not entered.
- **FSR**: The LKA lateral support shall detect warning-only fallback not entered and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control warning-only fallback not entered.
- **System Requirement**: The LKA lateral support shall execute the defined fault reaction for warning-only fallback not entered within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to LKA lateral support shall monitor the relevant inputs, state transitions, and outputs associated with warning-only fallback not entered and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to LKA lateral support shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of warning-only fallback not entered.
- **Test Requirement**: Inject or simulate warning-only fallback not entered in the situation 'EPS authority becomes degraded during operation' and verify that the hazard 'insufficient or inconsistent lane correction' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 20 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.24 Example 21

- **Item / Function**: FCW warning function
- **Operational Situation**: approach to slower lead vehicle
- **Malfunctioning Behaviour**: warning not issued
- **Hazard**: driver loses reaction time leading to collision
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by warning not issued.
- **FSR**: The FCW warning function shall detect warning not issued and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control warning not issued.
- **System Requirement**: The FCW warning function shall execute the defined fault reaction for warning not issued within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to FCW warning function shall monitor the relevant inputs, state transitions, and outputs associated with warning not issued and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to FCW warning function shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of warning not issued.
- **Test Requirement**: Inject or simulate warning not issued in the situation 'approach to slower lead vehicle' and verify that the hazard 'driver loses reaction time leading to collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 21 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.25 Example 22

- **Item / Function**: Blind Spot Detection
- **Operational Situation**: host vehicle prepares lane change
- **Malfunctioning Behaviour**: missed vehicle in blind spot
- **Hazard**: lane change into occupied lane causing side collision
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by missed vehicle in blind spot.
- **FSR**: The Blind Spot Detection shall detect missed vehicle in blind spot and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control missed vehicle in blind spot.
- **System Requirement**: The Blind Spot Detection shall execute the defined fault reaction for missed vehicle in blind spot within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Blind Spot Detection shall monitor the relevant inputs, state transitions, and outputs associated with missed vehicle in blind spot and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Blind Spot Detection shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of missed vehicle in blind spot.
- **Test Requirement**: Inject or simulate missed vehicle in blind spot in the situation 'host vehicle prepares lane change' and verify that the hazard 'lane change into occupied lane causing side collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 22 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.26 Example 23

- **Item / Function**: Blind Spot Detection
- **Operational Situation**: vehicle travels near roadside barrier
- **Malfunctioning Behaviour**: false warning due to roadside infrastructure
- **Hazard**: driver hesitation or unnecessary manoeuvre
- **Classification**: Derived and validated in HARA -> **ASIL A**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by false warning due to roadside infrastructure.
- **FSR**: The Blind Spot Detection shall detect false warning due to roadside infrastructure and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control false warning due to roadside infrastructure.
- **System Requirement**: The Blind Spot Detection shall execute the defined fault reaction for false warning due to roadside infrastructure within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Blind Spot Detection shall monitor the relevant inputs, state transitions, and outputs associated with false warning due to roadside infrastructure and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Blind Spot Detection shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of false warning due to roadside infrastructure.
- **Test Requirement**: Inject or simulate false warning due to roadside infrastructure in the situation 'vehicle travels near roadside barrier' and verify that the hazard 'driver hesitation or unnecessary manoeuvre' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 23 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.27 Example 24

- **Item / Function**: Rear Cross Traffic Alert
- **Operational Situation**: vehicle reverses from parking spot
- **Malfunctioning Behaviour**: warning shown on wrong side
- **Hazard**: driver checks wrong way and collision risk increases
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by warning shown on wrong side.
- **FSR**: The Rear Cross Traffic Alert shall detect warning shown on wrong side and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control warning shown on wrong side.
- **System Requirement**: The Rear Cross Traffic Alert shall execute the defined fault reaction for warning shown on wrong side within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Rear Cross Traffic Alert shall monitor the relevant inputs, state transitions, and outputs associated with warning shown on wrong side and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Rear Cross Traffic Alert shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of warning shown on wrong side.
- **Test Requirement**: Inject or simulate warning shown on wrong side in the situation 'vehicle reverses from parking spot' and verify that the hazard 'driver checks wrong way and collision risk increases' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 24 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.28 Example 25

- **Item / Function**: Automated parking assist
- **Operational Situation**: automated parking manoeuvre in confined space
- **Malfunctioning Behaviour**: steers into obstacle
- **Hazard**: low-speed collision with object or pedestrian
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by steers into obstacle.
- **FSR**: The Automated parking assist shall detect steers into obstacle and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control steers into obstacle.
- **System Requirement**: The Automated parking assist shall execute the defined fault reaction for steers into obstacle within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Automated parking assist shall monitor the relevant inputs, state transitions, and outputs associated with steers into obstacle and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Automated parking assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of steers into obstacle.
- **Test Requirement**: Inject or simulate steers into obstacle in the situation 'automated parking manoeuvre in confined space' and verify that the hazard 'low-speed collision with object or pedestrian' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 25 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.29 Example 26

- **Item / Function**: Automated parking assist
- **Operational Situation**: slow manoeuvre near wall
- **Malfunctioning Behaviour**: no stop on ultrasonic timeout
- **Hazard**: low-speed collision
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no stop on ultrasonic timeout.
- **FSR**: The Automated parking assist shall detect no stop on ultrasonic timeout and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no stop on ultrasonic timeout.
- **System Requirement**: The Automated parking assist shall execute the defined fault reaction for no stop on ultrasonic timeout within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Automated parking assist shall monitor the relevant inputs, state transitions, and outputs associated with no stop on ultrasonic timeout and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Automated parking assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no stop on ultrasonic timeout.
- **Test Requirement**: Inject or simulate no stop on ultrasonic timeout in the situation 'slow manoeuvre near wall' and verify that the hazard 'low-speed collision' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 26 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.30 Example 27

- **Item / Function**: Automated parking assist
- **Operational Situation**: trailer attached to vehicle
- **Malfunctioning Behaviour**: feature operates with invalid vehicle geometry assumptions
- **Hazard**: incorrect path and collision risk
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by feature operates with invalid vehicle geometry assumptions.
- **FSR**: The Automated parking assist shall detect feature operates with invalid vehicle geometry assumptions and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control feature operates with invalid vehicle geometry assumptions.
- **System Requirement**: The Automated parking assist shall execute the defined fault reaction for feature operates with invalid vehicle geometry assumptions within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Automated parking assist shall monitor the relevant inputs, state transitions, and outputs associated with feature operates with invalid vehicle geometry assumptions and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Automated parking assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of feature operates with invalid vehicle geometry assumptions.
- **Test Requirement**: Inject or simulate feature operates with invalid vehicle geometry assumptions in the situation 'trailer attached to vehicle' and verify that the hazard 'incorrect path and collision risk' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 27 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.31 Example 28

- **Item / Function**: Automated parking assist
- **Operational Situation**: obstacle temporarily blocks planned path
- **Malfunctioning Behaviour**: automatic resume after interruption without driver consent
- **Hazard**: driver surprise and collision risk
- **Classification**: Derived and validated in HARA -> **ASIL A**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by automatic resume after interruption without driver consent.
- **FSR**: The Automated parking assist shall detect automatic resume after interruption without driver consent and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control automatic resume after interruption without driver consent.
- **System Requirement**: The Automated parking assist shall execute the defined fault reaction for automatic resume after interruption without driver consent within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Automated parking assist shall monitor the relevant inputs, state transitions, and outputs associated with automatic resume after interruption without driver consent and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Automated parking assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of automatic resume after interruption without driver consent.
- **Test Requirement**: Inject or simulate automatic resume after interruption without driver consent in the situation 'obstacle temporarily blocks planned path' and verify that the hazard 'driver surprise and collision risk' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 28 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.32 Example 29

- **Item / Function**: Highway Assist
- **Operational Situation**: combined lateral and longitudinal assistance active
- **Malfunctioning Behaviour**: no takeover request on supervision loss
- **Hazard**: loss of safe human fallback for automation
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no takeover request on supervision loss.
- **FSR**: The Highway Assist shall detect no takeover request on supervision loss and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no takeover request on supervision loss.
- **System Requirement**: The Highway Assist shall execute the defined fault reaction for no takeover request on supervision loss within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Highway Assist shall monitor the relevant inputs, state transitions, and outputs associated with no takeover request on supervision loss and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Highway Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no takeover request on supervision loss.
- **Test Requirement**: Inject or simulate no takeover request on supervision loss in the situation 'combined lateral and longitudinal assistance active' and verify that the hazard 'loss of safe human fallback for automation' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 29 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.33 Example 30

- **Item / Function**: Highway Assist
- **Operational Situation**: vehicle enters unsupported road type after map mismatch
- **Malfunctioning Behaviour**: ODD exit not detected
- **Hazard**: unsupported automation behaviour
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by ODD exit not detected.
- **FSR**: The Highway Assist shall detect ODD exit not detected and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control ODD exit not detected.
- **System Requirement**: The Highway Assist shall execute the defined fault reaction for ODD exit not detected within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Highway Assist shall monitor the relevant inputs, state transitions, and outputs associated with ODD exit not detected and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Highway Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of ODD exit not detected.
- **Test Requirement**: Inject or simulate ODD exit not detected in the situation 'vehicle enters unsupported road type after map mismatch' and verify that the hazard 'unsupported automation behaviour' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 30 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.34 Example 31

- **Item / Function**: Highway Assist
- **Operational Situation**: position uncertainty rises during active assistance
- **Malfunctioning Behaviour**: localisation degradation not handled
- **Hazard**: automation continues outside validated localisation quality
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by localisation degradation not handled.
- **FSR**: The Highway Assist shall detect localisation degradation not handled and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control localisation degradation not handled.
- **System Requirement**: The Highway Assist shall execute the defined fault reaction for localisation degradation not handled within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Highway Assist shall monitor the relevant inputs, state transitions, and outputs associated with localisation degradation not handled and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Highway Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of localisation degradation not handled.
- **Test Requirement**: Inject or simulate localisation degradation not handled in the situation 'position uncertainty rises during active assistance' and verify that the hazard 'automation continues outside validated localisation quality' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 31 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.35 Example 32

- **Item / Function**: Highway Assist
- **Operational Situation**: driver ignores repeated takeover requests
- **Malfunctioning Behaviour**: no escalation to next safety strategy
- **Hazard**: prolonged unsupported automation
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by no escalation to next safety strategy.
- **FSR**: The Highway Assist shall detect no escalation to next safety strategy and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control no escalation to next safety strategy.
- **System Requirement**: The Highway Assist shall execute the defined fault reaction for no escalation to next safety strategy within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Highway Assist shall monitor the relevant inputs, state transitions, and outputs associated with no escalation to next safety strategy and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Highway Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of no escalation to next safety strategy.
- **Test Requirement**: Inject or simulate no escalation to next safety strategy in the situation 'driver ignores repeated takeover requests' and verify that the hazard 'prolonged unsupported automation' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 32 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.36 Example 33

- **Item / Function**: Traffic Jam Assist
- **Operational Situation**: stop-and-go traffic with active assist
- **Malfunctioning Behaviour**: silent drop of lateral control
- **Hazard**: driver assumes assistance remains and drifts out of lane
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by silent drop of lateral control.
- **FSR**: The Traffic Jam Assist shall detect silent drop of lateral control and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control silent drop of lateral control.
- **System Requirement**: The Traffic Jam Assist shall execute the defined fault reaction for silent drop of lateral control within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Traffic Jam Assist shall monitor the relevant inputs, state transitions, and outputs associated with silent drop of lateral control and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Traffic Jam Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of silent drop of lateral control.
- **Test Requirement**: Inject or simulate silent drop of lateral control in the situation 'stop-and-go traffic with active assist' and verify that the hazard 'driver assumes assistance remains and drifts out of lane' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 33 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.37 Example 34

- **Item / Function**: Traffic Jam Assist
- **Operational Situation**: stop-and-go standstill
- **Malfunctioning Behaviour**: unintended resume into obstacle
- **Hazard**: low-speed collision with stopped object
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by unintended resume into obstacle.
- **FSR**: The Traffic Jam Assist shall detect unintended resume into obstacle and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control unintended resume into obstacle.
- **System Requirement**: The Traffic Jam Assist shall execute the defined fault reaction for unintended resume into obstacle within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Traffic Jam Assist shall monitor the relevant inputs, state transitions, and outputs associated with unintended resume into obstacle and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Traffic Jam Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of unintended resume into obstacle.
- **Test Requirement**: Inject or simulate unintended resume into obstacle in the situation 'stop-and-go standstill' and verify that the hazard 'low-speed collision with stopped object' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 34 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.38 Example 35

- **Item / Function**: Traffic Jam Assist
- **Operational Situation**: vehicle held at standstill with active assistance
- **Malfunctioning Behaviour**: loss of hold capability without warning
- **Hazard**: unexpected roll or movement surprise
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by loss of hold capability without warning.
- **FSR**: The Traffic Jam Assist shall detect loss of hold capability without warning and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control loss of hold capability without warning.
- **System Requirement**: The Traffic Jam Assist shall execute the defined fault reaction for loss of hold capability without warning within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Traffic Jam Assist shall monitor the relevant inputs, state transitions, and outputs associated with loss of hold capability without warning and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Traffic Jam Assist shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of loss of hold capability without warning.
- **Test Requirement**: Inject or simulate loss of hold capability without warning in the situation 'vehicle held at standstill with active assistance' and verify that the hazard 'unexpected roll or movement surprise' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 35 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.39 Example 36

- **Item / Function**: Driver Monitoring
- **Operational Situation**: Level-2 assistance active
- **Malfunctioning Behaviour**: failure to detect no-driver or incapacitated-driver condition
- **Hazard**: no capable fallback driver for active support features
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by failure to detect no-driver or incapacitated-driver condition.
- **FSR**: The Driver Monitoring shall detect failure to detect no-driver or incapacitated-driver condition and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control failure to detect no-driver or incapacitated-driver condition.
- **System Requirement**: The Driver Monitoring shall execute the defined fault reaction for failure to detect no-driver or incapacitated-driver condition within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Driver Monitoring shall monitor the relevant inputs, state transitions, and outputs associated with failure to detect no-driver or incapacitated-driver condition and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Driver Monitoring shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of failure to detect no-driver or incapacitated-driver condition.
- **Test Requirement**: Inject or simulate failure to detect no-driver or incapacitated-driver condition in the situation 'Level-2 assistance active' and verify that the hazard 'no capable fallback driver for active support features' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 36 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.40 Example 37

- **Item / Function**: Driver Monitoring
- **Operational Situation**: direct low-angle sun enters the cabin camera
- **Malfunctioning Behaviour**: camera saturation not detected
- **Hazard**: dependent assist feature trusts invalid supervision signal
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by camera saturation not detected.
- **FSR**: The Driver Monitoring shall detect camera saturation not detected and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control camera saturation not detected.
- **System Requirement**: The Driver Monitoring shall execute the defined fault reaction for camera saturation not detected within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Driver Monitoring shall monitor the relevant inputs, state transitions, and outputs associated with camera saturation not detected and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Driver Monitoring shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of camera saturation not detected.
- **Test Requirement**: Inject or simulate camera saturation not detected in the situation 'direct low-angle sun enters the cabin camera' and verify that the hazard 'dependent assist feature trusts invalid supervision signal' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 37 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.41 Example 38

- **Item / Function**: Driver Monitoring
- **Operational Situation**: driver wears dark sunglasses and face is partially occluded
- **Malfunctioning Behaviour**: false attentive classification under poor observability
- **Hazard**: ADAS may fail to request takeover when needed
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by false attentive classification under poor observability.
- **FSR**: The Driver Monitoring shall detect false attentive classification under poor observability and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control false attentive classification under poor observability.
- **System Requirement**: The Driver Monitoring shall execute the defined fault reaction for false attentive classification under poor observability within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Driver Monitoring shall monitor the relevant inputs, state transitions, and outputs associated with false attentive classification under poor observability and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Driver Monitoring shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of false attentive classification under poor observability.
- **Test Requirement**: Inject or simulate false attentive classification under poor observability in the situation 'driver wears dark sunglasses and face is partially occluded' and verify that the hazard 'ADAS may fail to request takeover when needed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 38 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.42 Example 39

- **Item / Function**: Driver Monitoring with Highway Assist consumer
- **Operational Situation**: shared-control assistance active
- **Malfunctioning Behaviour**: stale supervision status reused after timeout
- **Hazard**: assistance continues without current driver state
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by stale supervision status reused after timeout.
- **FSR**: The Driver Monitoring with Highway Assist consumer shall detect stale supervision status reused after timeout and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control stale supervision status reused after timeout.
- **System Requirement**: The Driver Monitoring with Highway Assist consumer shall execute the defined fault reaction for stale supervision status reused after timeout within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Driver Monitoring with Highway Assist consumer shall monitor the relevant inputs, state transitions, and outputs associated with stale supervision status reused after timeout and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Driver Monitoring with Highway Assist consumer shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of stale supervision status reused after timeout.
- **Test Requirement**: Inject or simulate stale supervision status reused after timeout in the situation 'shared-control assistance active' and verify that the hazard 'assistance continues without current driver state' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 39 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.43 Example 40

- **Item / Function**: Telematics eCall
- **Operational Situation**: crash event with valid trigger
- **Malfunctioning Behaviour**: eCall not initiated
- **Hazard**: delayed emergency response for injured occupants
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by eCall not initiated.
- **FSR**: The Telematics eCall shall detect eCall not initiated and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control eCall not initiated.
- **System Requirement**: The Telematics eCall shall execute the defined fault reaction for eCall not initiated within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Telematics eCall shall monitor the relevant inputs, state transitions, and outputs associated with eCall not initiated and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Telematics eCall shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of eCall not initiated.
- **Test Requirement**: Inject or simulate eCall not initiated in the situation 'crash event with valid trigger' and verify that the hazard 'delayed emergency response for injured occupants' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 40 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.44 Example 41

- **Item / Function**: Telematics eCall
- **Operational Situation**: post-crash emergency communication
- **Malfunctioning Behaviour**: wrong or stale location transmitted
- **Hazard**: emergency responders may be misdirected
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by wrong or stale location transmitted.
- **FSR**: The Telematics eCall shall detect wrong or stale location transmitted and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control wrong or stale location transmitted.
- **System Requirement**: The Telematics eCall shall execute the defined fault reaction for wrong or stale location transmitted within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Telematics eCall shall monitor the relevant inputs, state transitions, and outputs associated with wrong or stale location transmitted and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Telematics eCall shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of wrong or stale location transmitted.
- **Test Requirement**: Inject or simulate wrong or stale location transmitted in the situation 'post-crash emergency communication' and verify that the hazard 'emergency responders may be misdirected' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 41 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.45 Example 42

- **Item / Function**: Telematics remote command
- **Operational Situation**: vehicle parked and connected
- **Malfunctioning Behaviour**: remote unlock executed without authorisation
- **Hazard**: security breach and potential theft
- **Classification**: Derived and validated in HARA -> **ASIL QM**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by remote unlock executed without authorisation.
- **FSR**: The Telematics remote command shall detect remote unlock executed without authorisation and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control remote unlock executed without authorisation.
- **System Requirement**: The Telematics remote command shall execute the defined fault reaction for remote unlock executed without authorisation within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Telematics remote command shall monitor the relevant inputs, state transitions, and outputs associated with remote unlock executed without authorisation and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Telematics remote command shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of remote unlock executed without authorisation.
- **Test Requirement**: Inject or simulate remote unlock executed without authorisation in the situation 'vehicle parked and connected' and verify that the hazard 'security breach and potential theft' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 42 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.46 Example 43

- **Item / Function**: Telematics OTA
- **Operational Situation**: software update installation in parked vehicle
- **Malfunctioning Behaviour**: power loss leaves ECU unbootable
- **Hazard**: loss of vehicle function after update
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by power loss leaves ECU unbootable.
- **FSR**: The Telematics OTA shall detect power loss leaves ECU unbootable and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control power loss leaves ECU unbootable.
- **System Requirement**: The Telematics OTA shall execute the defined fault reaction for power loss leaves ECU unbootable within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Telematics OTA shall monitor the relevant inputs, state transitions, and outputs associated with power loss leaves ECU unbootable and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Telematics OTA shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of power loss leaves ECU unbootable.
- **Test Requirement**: Inject or simulate power loss leaves ECU unbootable in the situation 'software update installation in parked vehicle' and verify that the hazard 'loss of vehicle function after update' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 43 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.47 Example 44

- **Item / Function**: Telematics emergency and breakdown call
- **Operational Situation**: breakdown call active when crash trigger occurs
- **Malfunctioning Behaviour**: resource arbitration keeps eCall from pre-empting
- **Hazard**: emergency response delayed
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by resource arbitration keeps eCall from pre-empting.
- **FSR**: The Telematics emergency and breakdown call shall detect resource arbitration keeps eCall from pre-empting and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control resource arbitration keeps eCall from pre-empting.
- **System Requirement**: The Telematics emergency and breakdown call shall execute the defined fault reaction for resource arbitration keeps eCall from pre-empting within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Telematics emergency and breakdown call shall monitor the relevant inputs, state transitions, and outputs associated with resource arbitration keeps eCall from pre-empting and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Telematics emergency and breakdown call shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of resource arbitration keeps eCall from pre-empting.
- **Test Requirement**: Inject or simulate resource arbitration keeps eCall from pre-empting in the situation 'breakdown call active when crash trigger occurs' and verify that the hazard 'emergency response delayed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 44 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.48 Example 45

- **Item / Function**: Remote diagnostics
- **Operational Situation**: backend requests high-rate polling while driving
- **Malfunctioning Behaviour**: diagnostic traffic overloads in-vehicle bus
- **Hazard**: safety-relevant control traffic may be delayed
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by diagnostic traffic overloads in-vehicle bus.
- **FSR**: The Remote diagnostics shall detect diagnostic traffic overloads in-vehicle bus and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control diagnostic traffic overloads in-vehicle bus.
- **System Requirement**: The Remote diagnostics shall execute the defined fault reaction for diagnostic traffic overloads in-vehicle bus within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Remote diagnostics shall monitor the relevant inputs, state transitions, and outputs associated with diagnostic traffic overloads in-vehicle bus and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Remote diagnostics shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of diagnostic traffic overloads in-vehicle bus.
- **Test Requirement**: Inject or simulate diagnostic traffic overloads in-vehicle bus in the situation 'backend requests high-rate polling while driving' and verify that the hazard 'safety-relevant control traffic may be delayed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 45 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.49 Example 46

- **Item / Function**: Vehicle data collection
- **Operational Situation**: backend starts a data-collection campaign
- **Malfunctioning Behaviour**: campaign integrity not verified
- **Hazard**: privacy or safety data policy violation
- **Classification**: Derived and validated in HARA -> **ASIL QM**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by campaign integrity not verified.
- **FSR**: The Vehicle data collection shall detect campaign integrity not verified and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control campaign integrity not verified.
- **System Requirement**: The Vehicle data collection shall execute the defined fault reaction for campaign integrity not verified within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Vehicle data collection shall monitor the relevant inputs, state transitions, and outputs associated with campaign integrity not verified and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Vehicle data collection shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of campaign integrity not verified.
- **Test Requirement**: Inject or simulate campaign integrity not verified in the situation 'backend starts a data-collection campaign' and verify that the hazard 'privacy or safety data policy violation' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 46 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.50 Example 47

- **Item / Function**: Instrument Cluster
- **Operational Situation**: brake system reports critical fault during driving
- **Malfunctioning Behaviour**: cluster fails to show high-priority warning
- **Hazard**: driver is unaware of major braking system impairment
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by cluster fails to show high-priority warning.
- **FSR**: The Instrument Cluster shall detect cluster fails to show high-priority warning and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control cluster fails to show high-priority warning.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for cluster fails to show high-priority warning within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with cluster fails to show high-priority warning and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of cluster fails to show high-priority warning.
- **Test Requirement**: Inject or simulate cluster fails to show high-priority warning in the situation 'brake system reports critical fault during driving' and verify that the hazard 'driver is unaware of major braking system impairment' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 47 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.51 Example 48

- **Item / Function**: Instrument Cluster
- **Operational Situation**: speed source communication is lost in motion
- **Malfunctioning Behaviour**: stale speed remains displayed
- **Hazard**: driver is misled about actual speed
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by stale speed remains displayed.
- **FSR**: The Instrument Cluster shall detect stale speed remains displayed and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control stale speed remains displayed.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for stale speed remains displayed within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with stale speed remains displayed and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of stale speed remains displayed.
- **Test Requirement**: Inject or simulate stale speed remains displayed in the situation 'speed source communication is lost in motion' and verify that the hazard 'driver is misled about actual speed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 48 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.52 Example 49

- **Item / Function**: Instrument Cluster
- **Operational Situation**: highway-assist takeover request is active
- **Malfunctioning Behaviour**: frozen display hides takeover warning
- **Hazard**: driver misses takeover and automation assumptions fail
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by frozen display hides takeover warning.
- **FSR**: The Instrument Cluster shall detect frozen display hides takeover warning and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control frozen display hides takeover warning.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for frozen display hides takeover warning within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with frozen display hides takeover warning and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of frozen display hides takeover warning.
- **Test Requirement**: Inject or simulate frozen display hides takeover warning in the situation 'highway-assist takeover request is active' and verify that the hazard 'driver misses takeover and automation assumptions fail' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 49 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.53 Example 50

- **Item / Function**: Instrument Cluster
- **Operational Situation**: night drive with ambient light transitions
- **Malfunctioning Behaviour**: brightness control hides critical warning
- **Hazard**: driver misses urgent warning
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by brightness control hides critical warning.
- **FSR**: The Instrument Cluster shall detect brightness control hides critical warning and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control brightness control hides critical warning.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for brightness control hides critical warning within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with brightness control hides critical warning and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of brightness control hides critical warning.
- **Test Requirement**: Inject or simulate brightness control hides critical warning in the situation 'night drive with ambient light transitions' and verify that the hazard 'driver misses urgent warning' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 50 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.54 Example 51

- **Item / Function**: Instrument Cluster
- **Operational Situation**: service session active with diagnostic overlay
- **Malfunctioning Behaviour**: diagnostic mode masks critical warning
- **Hazard**: driver misses safety-critical information
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by diagnostic mode masks critical warning.
- **FSR**: The Instrument Cluster shall detect diagnostic mode masks critical warning and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control diagnostic mode masks critical warning.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for diagnostic mode masks critical warning within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with diagnostic mode masks critical warning and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of diagnostic mode masks critical warning.
- **Test Requirement**: Inject or simulate diagnostic mode masks critical warning in the situation 'service session active with diagnostic overlay' and verify that the hazard 'driver misses safety-critical information' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 51 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.55 Example 52

- **Item / Function**: Instrument Cluster
- **Operational Situation**: market variant coding updated incorrectly
- **Malfunctioning Behaviour**: wrong units displayed
- **Hazard**: driver misinterprets legal speed
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by wrong units displayed.
- **FSR**: The Instrument Cluster shall detect wrong units displayed and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control wrong units displayed.
- **System Requirement**: The Instrument Cluster shall execute the defined fault reaction for wrong units displayed within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Instrument Cluster shall monitor the relevant inputs, state transitions, and outputs associated with wrong units displayed and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Instrument Cluster shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of wrong units displayed.
- **Test Requirement**: Inject or simulate wrong units displayed in the situation 'market variant coding updated incorrectly' and verify that the hazard 'driver misinterprets legal speed' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 52 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.56 Example 53

- **Item / Function**: Gateway ECU
- **Operational Situation**: gateway routes brake-status signal between domains
- **Malfunctioning Behaviour**: corrupted or wrongly mapped message forwarded
- **Hazard**: dependent ADAS function uses wrong brake status
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by corrupted or wrongly mapped message forwarded.
- **FSR**: The Gateway ECU shall detect corrupted or wrongly mapped message forwarded and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control corrupted or wrongly mapped message forwarded.
- **System Requirement**: The Gateway ECU shall execute the defined fault reaction for corrupted or wrongly mapped message forwarded within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Gateway ECU shall monitor the relevant inputs, state transitions, and outputs associated with corrupted or wrongly mapped message forwarded and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Gateway ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of corrupted or wrongly mapped message forwarded.
- **Test Requirement**: Inject or simulate corrupted or wrongly mapped message forwarded in the situation 'gateway routes brake-status signal between domains' and verify that the hazard 'dependent ADAS function uses wrong brake status' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 53 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.57 Example 54

- **Item / Function**: Gateway ECU
- **Operational Situation**: high network load from infotainment traffic
- **Malfunctioning Behaviour**: safety message delayed behind non-essential traffic
- **Hazard**: dependent safety function reacts too late
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by safety message delayed behind non-essential traffic.
- **FSR**: The Gateway ECU shall detect safety message delayed behind non-essential traffic and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control safety message delayed behind non-essential traffic.
- **System Requirement**: The Gateway ECU shall execute the defined fault reaction for safety message delayed behind non-essential traffic within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Gateway ECU shall monitor the relevant inputs, state transitions, and outputs associated with safety message delayed behind non-essential traffic and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Gateway ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of safety message delayed behind non-essential traffic.
- **Test Requirement**: Inject or simulate safety message delayed behind non-essential traffic in the situation 'high network load from infotainment traffic' and verify that the hazard 'dependent safety function reacts too late' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 54 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.58 Example 55

- **Item / Function**: Gateway ECU
- **Operational Situation**: external tester connected while driving
- **Malfunctioning Behaviour**: unauthorised diagnostic routing allowed
- **Hazard**: potential disturbance or misuse of safety functions
- **Classification**: Derived and validated in HARA -> **ASIL QM**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by unauthorised diagnostic routing allowed.
- **FSR**: The Gateway ECU shall detect unauthorised diagnostic routing allowed and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control unauthorised diagnostic routing allowed.
- **System Requirement**: The Gateway ECU shall execute the defined fault reaction for unauthorised diagnostic routing allowed within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Gateway ECU shall monitor the relevant inputs, state transitions, and outputs associated with unauthorised diagnostic routing allowed and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Gateway ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of unauthorised diagnostic routing allowed.
- **Test Requirement**: Inject or simulate unauthorised diagnostic routing allowed in the situation 'external tester connected while driving' and verify that the hazard 'potential disturbance or misuse of safety functions' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 55 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.59 Example 56

- **Item / Function**: Gateway ECU
- **Operational Situation**: signal translation between networks
- **Malfunctioning Behaviour**: left/right semantic mapping swapped
- **Hazard**: ADAS intent logic misinterprets lane-change intent
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by left/right semantic mapping swapped.
- **FSR**: The Gateway ECU shall detect left/right semantic mapping swapped and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control left/right semantic mapping swapped.
- **System Requirement**: The Gateway ECU shall execute the defined fault reaction for left/right semantic mapping swapped within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Gateway ECU shall monitor the relevant inputs, state transitions, and outputs associated with left/right semantic mapping swapped and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Gateway ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of left/right semantic mapping swapped.
- **Test Requirement**: Inject or simulate left/right semantic mapping swapped in the situation 'signal translation between networks' and verify that the hazard 'ADAS intent logic misinterprets lane-change intent' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 56 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.60 Example 57

- **Item / Function**: Gateway ECU
- **Operational Situation**: multiple domains depend on synchronised timestamps
- **Malfunctioning Behaviour**: time-sync failure invalidates timestamped data
- **Hazard**: sensor fusion combines temporally inconsistent data
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by time-sync failure invalidates timestamped data.
- **FSR**: The Gateway ECU shall detect time-sync failure invalidates timestamped data and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control time-sync failure invalidates timestamped data.
- **System Requirement**: The Gateway ECU shall execute the defined fault reaction for time-sync failure invalidates timestamped data within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Gateway ECU shall monitor the relevant inputs, state transitions, and outputs associated with time-sync failure invalidates timestamped data and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Gateway ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of time-sync failure invalidates timestamped data.
- **Test Requirement**: Inject or simulate time-sync failure invalidates timestamped data in the situation 'multiple domains depend on synchronised timestamps' and verify that the hazard 'sensor fusion combines temporally inconsistent data' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 57 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.61 Example 58

- **Item / Function**: Sensor ECU
- **Operational Situation**: wheel speed or steering angle drifts due to partial fault
- **Malfunctioning Behaviour**: plausible-but-wrong value published
- **Hazard**: dependent control uses incorrect dynamics data
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by plausible-but-wrong value published.
- **FSR**: The Sensor ECU shall detect plausible-but-wrong value published and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control plausible-but-wrong value published.
- **System Requirement**: The Sensor ECU shall execute the defined fault reaction for plausible-but-wrong value published within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Sensor ECU shall monitor the relevant inputs, state transitions, and outputs associated with plausible-but-wrong value published and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Sensor ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of plausible-but-wrong value published.
- **Test Requirement**: Inject or simulate plausible-but-wrong value published in the situation 'wheel speed or steering angle drifts due to partial fault' and verify that the hazard 'dependent control uses incorrect dynamics data' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 58 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.62 Example 59

- **Item / Function**: Sensor ECU
- **Operational Situation**: power-up after service event
- **Malfunctioning Behaviour**: boot with corrupted calibration
- **Hazard**: incorrect output propagates into control decisions
- **Classification**: Derived and validated in HARA -> **ASIL C**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by boot with corrupted calibration.
- **FSR**: The Sensor ECU shall detect boot with corrupted calibration and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control boot with corrupted calibration.
- **System Requirement**: The Sensor ECU shall execute the defined fault reaction for boot with corrupted calibration within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Sensor ECU shall monitor the relevant inputs, state transitions, and outputs associated with boot with corrupted calibration and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Sensor ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of boot with corrupted calibration.
- **Test Requirement**: Inject or simulate boot with corrupted calibration in the situation 'power-up after service event' and verify that the hazard 'incorrect output propagates into control decisions' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 59 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.63 Example 60

- **Item / Function**: Sensor ECU
- **Operational Situation**: intermittent connector issue during drive
- **Malfunctioning Behaviour**: measurement dropout not reported
- **Hazard**: consumer ECU trusts unavailable or reconstructed data
- **Classification**: Derived and validated in HARA -> **ASIL B**
- **Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by measurement dropout not reported.
- **FSR**: The Sensor ECU shall detect measurement dropout not reported and transition to the defined safe or degraded state appropriate to the operational situation.
- **TSR**: The allocated architecture shall implement monitoring, plausibility checks, integrity protection, and supervised fallback paths needed to control measurement dropout not reported.
- **System Requirement**: The Sensor ECU shall execute the defined fault reaction for measurement dropout not reported within the allocated time budget and shall inform dependent systems or the driver where required.
- **Software Requirement**: The software assigned to Sensor ECU shall monitor the relevant inputs, state transitions, and outputs associated with measurement dropout not reported and shall trigger the specified fallback behaviour.
- **Hardware Requirement**: The hardware platform and interfaces assigned to Sensor ECU shall provide the diagnostics, integrity protection, and actuation or communication controls needed to support detection and mitigation of measurement dropout not reported.
- **Test Requirement**: Inject or simulate measurement dropout not reported in the situation 'intermittent connector issue during drive' and verify that the hazard 'consumer ECU trusts unavailable or reconstructed data' is prevented or mitigated according to the safety concept.
- **Traceability Note**: Link Example 60 to the item definition, HARA entry, safety goal, FSR, TSR, system architecture, software component, hardware element, and verification report.

### 12.64 Practical Safety Requirement Writing Guidance

- State the hazardous consequence that is being prevented or controlled.
- Define the detection mechanism and the reaction time, not just the reaction.
- Separate nominal functionality from safety monitoring and fault reaction where doing so improves verification clarity.
- Avoid “safe” as an undefined adjective; specify what the safe state is.
- Trace every safety mechanism to a verification case that proves both detection and reaction.
- When degraded operation is allowed, bound it explicitly by speed, ODD, authority, and HMI indication.

## Section 13: REQUIREMENTS + HARA

HARA turns operational situations and malfunctioning behaviour into actionable requirements. The examples below show how HARA output guides safety goals and then produces derived requirements.

### 13.1 ACC wrong-target acceleration

- **Operational Situation**: highway following behind slower vehicle
- **Malfunctioning Behaviour**: ACC selects non-relevant object and accelerates
- **Hazardous Event**: rear-end collision risk increases
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by ACC selects non-relevant object and accelerates.
- **Derived Requirement Chain**:
  - FSR: Detect ACC selects non-relevant object and accelerates and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control ACC selects non-relevant object and accelerates.
  - System Requirement: The assigned function shall react to ACC selects non-relevant object and accelerates within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'highway following behind slower vehicle'.

### 13.2 ACC no cancel on brake

- **Operational Situation**: driver presses brake during active ACC
- **Malfunctioning Behaviour**: ACC continues to command torque
- **Hazardous Event**: driver authority is reduced in an urgent situation
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by ACC continues to command torque.
- **Derived Requirement Chain**:
  - FSR: Detect ACC continues to command torque and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control ACC continues to command torque.
  - System Requirement: The assigned function shall react to ACC continues to command torque within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'driver presses brake during active ACC'.

### 13.3 ACC no gap control due to lost speed signal

- **Operational Situation**: cruise following active in moderate traffic
- **Malfunctioning Behaviour**: host speed input times out but control continues
- **Hazardous Event**: gap estimation becomes unsafe
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by host speed input times out but control continues.
- **Derived Requirement Chain**:
  - FSR: Detect host speed input times out but control continues and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control host speed input times out but control continues.
  - System Requirement: The assigned function shall react to host speed input times out but control continues within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'cruise following active in moderate traffic'.

### 13.4 AEB missed stationary vehicle

- **Operational Situation**: approach to stopped queue
- **Malfunctioning Behaviour**: perception fails to classify stationary lead vehicle
- **Hazardous Event**: high-severity frontal collision
- **Severity / Exposure / Controllability**: S3 / E4 / C3 -> **ASIL D**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by perception fails to classify stationary lead vehicle.
- **Derived Requirement Chain**:
  - FSR: Detect perception fails to classify stationary lead vehicle and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control perception fails to classify stationary lead vehicle.
  - System Requirement: The assigned function shall react to perception fails to classify stationary lead vehicle within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'approach to stopped queue'.

### 13.5 AEB false brake on bridge

- **Operational Situation**: vehicle passes beneath overhead bridge
- **Malfunctioning Behaviour**: bridge is classified as obstacle
- **Hazardous Event**: unexpected harsh braking causes rear-impact risk
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by bridge is classified as obstacle.
- **Derived Requirement Chain**:
  - FSR: Detect bridge is classified as obstacle and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control bridge is classified as obstacle.
  - System Requirement: The assigned function shall react to bridge is classified as obstacle within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'vehicle passes beneath overhead bridge'.

### 13.6 AEB no warning before unavailable

- **Operational Situation**: AEB sensor fails while driving
- **Malfunctioning Behaviour**: function becomes unavailable without HMI indication
- **Hazardous Event**: driver overestimates protection
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by function becomes unavailable without HMI indication.
- **Derived Requirement Chain**:
  - FSR: Detect function becomes unavailable without HMI indication and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control function becomes unavailable without HMI indication.
  - System Requirement: The assigned function shall react to function becomes unavailable without HMI indication within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'AEB sensor fails while driving'.

### 13.7 LKA wrong-direction torque

- **Operational Situation**: vehicle drifts toward left lane line
- **Malfunctioning Behaviour**: LKA commands torque in the wrong direction
- **Hazardous Event**: lane departure or side collision
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by LKA commands torque in the wrong direction.
- **Derived Requirement Chain**:
  - FSR: Detect LKA commands torque in the wrong direction and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control LKA commands torque in the wrong direction.
  - System Requirement: The assigned function shall react to LKA commands torque in the wrong direction within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'vehicle drifts toward left lane line'.

### 13.8 LKA no override release

- **Operational Situation**: driver counters LKA intervention
- **Malfunctioning Behaviour**: system continues steering torque
- **Hazardous Event**: driver fights system and loses controllability margin
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by system continues steering torque.
- **Derived Requirement Chain**:
  - FSR: Detect system continues steering torque and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control system continues steering torque.
  - System Requirement: The assigned function shall react to system continues steering torque within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'driver counters LKA intervention'.

### 13.9 LKA active with no lanes

- **Operational Situation**: faded lane markings in rain
- **Malfunctioning Behaviour**: intervention remains enabled despite low confidence
- **Hazardous Event**: unexpected steering on uncertain scene
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by intervention remains enabled despite low confidence.
- **Derived Requirement Chain**:
  - FSR: Detect intervention remains enabled despite low confidence and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control intervention remains enabled despite low confidence.
  - System Requirement: The assigned function shall react to intervention remains enabled despite low confidence within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'faded lane markings in rain'.

### 13.10 FCW no alert

- **Operational Situation**: closing on slower vehicle
- **Malfunctioning Behaviour**: threshold crossed but FCW remains silent
- **Hazardous Event**: driver loses reaction time
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by threshold crossed but FCW remains silent.
- **Derived Requirement Chain**:
  - FSR: Detect threshold crossed but FCW remains silent and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control threshold crossed but FCW remains silent.
  - System Requirement: The assigned function shall react to threshold crossed but FCW remains silent within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'closing on slower vehicle'.

### 13.11 BSD missed adjacent motorcycle

- **Operational Situation**: lane change preparation
- **Malfunctioning Behaviour**: blind-spot object is not detected
- **Hazardous Event**: side collision risk
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by blind-spot object is not detected.
- **Derived Requirement Chain**:
  - FSR: Detect blind-spot object is not detected and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control blind-spot object is not detected.
  - System Requirement: The assigned function shall react to blind-spot object is not detected within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'lane change preparation'.

### 13.12 RCTA wrong-side warning

- **Operational Situation**: reverse out of parking slot
- **Malfunctioning Behaviour**: threat side is reversed
- **Hazardous Event**: driver checks wrong side and collision risk rises
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by threat side is reversed.
- **Derived Requirement Chain**:
  - FSR: Detect threat side is reversed and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control threat side is reversed.
  - System Requirement: The assigned function shall react to threat side is reversed within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'reverse out of parking slot'.

### 13.13 Parking assist obstacle timeout

- **Operational Situation**: automated parking near wall
- **Malfunctioning Behaviour**: close-range sensor times out but movement continues
- **Hazardous Event**: low-speed collision
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by close-range sensor times out but movement continues.
- **Derived Requirement Chain**:
  - FSR: Detect close-range sensor times out but movement continues and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control close-range sensor times out but movement continues.
  - System Requirement: The assigned function shall react to close-range sensor times out but movement continues within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'automated parking near wall'.

### 13.14 Highway assist no takeover on DMS loss

- **Operational Situation**: combined control active on highway
- **Malfunctioning Behaviour**: driver supervision becomes unavailable but no takeover is requested
- **Hazardous Event**: active assistance continues without supported fallback driver
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by driver supervision becomes unavailable but no takeover is requested.
- **Derived Requirement Chain**:
  - FSR: Detect driver supervision becomes unavailable but no takeover is requested and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control driver supervision becomes unavailable but no takeover is requested.
  - System Requirement: The assigned function shall react to driver supervision becomes unavailable but no takeover is requested within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'combined control active on highway'.

### 13.15 Traffic jam assist silent lateral loss

- **Operational Situation**: stop-and-go automation active
- **Malfunctioning Behaviour**: lateral support ends without HMI update
- **Hazardous Event**: driver assumes steering support persists
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by lateral support ends without HMI update.
- **Derived Requirement Chain**:
  - FSR: Detect lateral support ends without HMI update and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control lateral support ends without HMI update.
  - System Requirement: The assigned function shall react to lateral support ends without HMI update within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'stop-and-go automation active'.

### 13.16 Driver monitoring stale state

- **Operational Situation**: shared-control assistance active
- **Malfunctioning Behaviour**: old attentive status persists after timeout
- **Hazardous Event**: automation uses stale supervision assumption
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by old attentive status persists after timeout.
- **Derived Requirement Chain**:
  - FSR: Detect old attentive status persists after timeout and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control old attentive status persists after timeout.
  - System Requirement: The assigned function shall react to old attentive status persists after timeout within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'shared-control assistance active'.

### 13.17 TCU eCall not initiated

- **Operational Situation**: crash event occurs
- **Malfunctioning Behaviour**: crash trigger is received but no eCall starts
- **Hazardous Event**: emergency response is delayed
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by crash trigger is received but no eCall starts.
- **Derived Requirement Chain**:
  - FSR: Detect crash trigger is received but no eCall starts and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control crash trigger is received but no eCall starts.
  - System Requirement: The assigned function shall react to crash trigger is received but no eCall starts within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'crash event occurs'.

### 13.18 TCU stale GNSS in eCall

- **Operational Situation**: post-crash MSD transmission
- **Malfunctioning Behaviour**: old location is transmitted as current
- **Hazardous Event**: responder location may be wrong
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by old location is transmitted as current.
- **Derived Requirement Chain**:
  - FSR: Detect old location is transmitted as current and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control old location is transmitted as current.
  - System Requirement: The assigned function shall react to old location is transmitted as current within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'post-crash MSD transmission'.

### 13.19 Remote unlock replay

- **Operational Situation**: vehicle parked and connected
- **Malfunctioning Behaviour**: replayed command opens vehicle
- **Hazardous Event**: security compromise and theft risk
- **Severity / Exposure / Controllability**: S0 / E4 / C3 -> **ASIL QM**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by replayed command opens vehicle.
- **Derived Requirement Chain**:
  - FSR: Detect replayed command opens vehicle and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control replayed command opens vehicle.
  - System Requirement: The assigned function shall react to replayed command opens vehicle within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'vehicle parked and connected'.

### 13.20 OTA interrupted install

- **Operational Situation**: safety ECU update in parked vehicle
- **Malfunctioning Behaviour**: power is lost during installation
- **Hazardous Event**: ECU may become unbootable
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by power is lost during installation.
- **Derived Requirement Chain**:
  - FSR: Detect power is lost during installation and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control power is lost during installation.
  - System Requirement: The assigned function shall react to power is lost during installation within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'safety ECU update in parked vehicle'.

### 13.21 Cluster stale speed display

- **Operational Situation**: speed source times out in motion
- **Malfunctioning Behaviour**: last speed remains displayed as valid
- **Hazardous Event**: driver misreads actual speed
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by last speed remains displayed as valid.
- **Derived Requirement Chain**:
  - FSR: Detect last speed remains displayed as valid and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control last speed remains displayed as valid.
  - System Requirement: The assigned function shall react to last speed remains displayed as valid within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'speed source times out in motion'.

### 13.22 Cluster frozen display during takeover

- **Operational Situation**: takeover request active
- **Malfunctioning Behaviour**: render task freezes
- **Hazardous Event**: critical HMI message is hidden
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by render task freezes.
- **Derived Requirement Chain**:
  - FSR: Detect render task freezes and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control render task freezes.
  - System Requirement: The assigned function shall react to render task freezes within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'takeover request active'.

### 13.23 Gateway corrupts brake signal

- **Operational Situation**: gateway routes brake status
- **Malfunctioning Behaviour**: payload or mapping becomes corrupted
- **Hazardous Event**: ADAS decisions rely on wrong brake state
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by payload or mapping becomes corrupted.
- **Derived Requirement Chain**:
  - FSR: Detect payload or mapping becomes corrupted and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control payload or mapping becomes corrupted.
  - System Requirement: The assigned function shall react to payload or mapping becomes corrupted within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'gateway routes brake status'.

### 13.24 Gateway congestion starves safety traffic

- **Operational Situation**: infotainment traffic flood on network
- **Malfunctioning Behaviour**: safety messages are delayed behind low-priority traffic
- **Hazardous Event**: safety functions react late
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by safety messages are delayed behind low-priority traffic.
- **Derived Requirement Chain**:
  - FSR: Detect safety messages are delayed behind low-priority traffic and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control safety messages are delayed behind low-priority traffic.
  - System Requirement: The assigned function shall react to safety messages are delayed behind low-priority traffic within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'infotainment traffic flood on network'.

### 13.25 Domain controller service isolation failure

- **Operational Situation**: one application faults in a consolidated controller
- **Malfunctioning Behaviour**: entire controller restarts and unrelated function is lost
- **Hazardous Event**: simultaneous loss of multiple functions
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by entire controller restarts and unrelated function is lost.
- **Derived Requirement Chain**:
  - FSR: Detect entire controller restarts and unrelated function is lost and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control entire controller restarts and unrelated function is lost.
  - System Requirement: The assigned function shall react to entire controller restarts and unrelated function is lost within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'one application faults in a consolidated controller'.

### 13.26 Sensor ECU drift undetected

- **Operational Situation**: wheel-speed or steering-angle sensor drifts
- **Malfunctioning Behaviour**: value remains in range but is wrong
- **Hazardous Event**: dependent control uses incorrect dynamics state
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by value remains in range but is wrong.
- **Derived Requirement Chain**:
  - FSR: Detect value remains in range but is wrong and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control value remains in range but is wrong.
  - System Requirement: The assigned function shall react to value remains in range but is wrong within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'wheel-speed or steering-angle sensor drifts'.

### 13.27 Actuator command timeout persists

- **Operational Situation**: command source is lost
- **Malfunctioning Behaviour**: actuator holds last value indefinitely
- **Hazardous Event**: sustained hazardous actuation
- **Severity / Exposure / Controllability**: S3 / E4 / C3 -> **ASIL D**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by actuator holds last value indefinitely.
- **Derived Requirement Chain**:
  - FSR: Detect actuator holds last value indefinitely and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control actuator holds last value indefinitely.
  - System Requirement: The assigned function shall react to actuator holds last value indefinitely within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'command source is lost'.

### 13.28 Actuator out-of-range command accepted

- **Operational Situation**: distributed actuation interface active
- **Malfunctioning Behaviour**: invalid excessive command is executed
- **Hazardous Event**: excessive physical actuation
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by invalid excessive command is executed.
- **Derived Requirement Chain**:
  - FSR: Detect invalid excessive command is executed and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control invalid excessive command is executed.
  - System Requirement: The assigned function shall react to invalid excessive command is executed within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'distributed actuation interface active'.

### 13.29 TSR conflicting signs unresolved

- **Operational Situation**: temporary roadwork sign conflicts with map or permanent sign
- **Malfunctioning Behaviour**: system silently chooses the wrong sign
- **Hazardous Event**: driver receives misleading speed advice
- **Severity / Exposure / Controllability**: S1 / E4 / C2 -> **ASIL A**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by system silently chooses the wrong sign.
- **Derived Requirement Chain**:
  - FSR: Detect system silently chooses the wrong sign and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control system silently chooses the wrong sign.
  - System Requirement: The assigned function shall react to system silently chooses the wrong sign within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'temporary roadwork sign conflicts with map or permanent sign'.

### 13.30 Highway assist ODD exit undetected

- **Operational Situation**: vehicle leaves divided highway
- **Malfunctioning Behaviour**: feature remains active outside its ODD
- **Hazardous Event**: unsupported automation behaviour
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by feature remains active outside its ODD.
- **Derived Requirement Chain**:
  - FSR: Detect feature remains active outside its ODD and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control feature remains active outside its ODD.
  - System Requirement: The assigned function shall react to feature remains active outside its ODD within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'vehicle leaves divided highway'.

### 13.31 Traffic jam assist auto-resume on wrong target

- **Operational Situation**: stop-and-go standstill
- **Malfunctioning Behaviour**: feature resumes on false lead target
- **Hazardous Event**: low-speed collision
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by feature resumes on false lead target.
- **Derived Requirement Chain**:
  - FSR: Detect feature resumes on false lead target and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control feature resumes on false lead target.
  - System Requirement: The assigned function shall react to feature resumes on false lead target within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'stop-and-go standstill'.

### 13.32 eCall backup power unavailable

- **Operational Situation**: crash disconnects main power
- **Malfunctioning Behaviour**: backup energy path is missing or failed
- **Hazardous Event**: emergency call cannot complete
- **Severity / Exposure / Controllability**: S3 / E4 / C2 -> **ASIL C**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by backup energy path is missing or failed.
- **Derived Requirement Chain**:
  - FSR: Detect backup energy path is missing or failed and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control backup energy path is missing or failed.
  - System Requirement: The assigned function shall react to backup energy path is missing or failed within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'crash disconnects main power'.

### 13.33 Cluster warning obscured by overlay

- **Operational Situation**: diagnostic or infotainment overlay active
- **Malfunctioning Behaviour**: critical warning is not visible
- **Hazardous Event**: driver misses urgent warning
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by critical warning is not visible.
- **Derived Requirement Chain**:
  - FSR: Detect critical warning is not visible and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control critical warning is not visible.
  - System Requirement: The assigned function shall react to critical warning is not visible within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'diagnostic or infotainment overlay active'.

### 13.34 Gateway restricted diagnostics while driving

- **Operational Situation**: vehicle in motion with external tester connected
- **Malfunctioning Behaviour**: gateway forwards prohibited diagnostic services
- **Hazardous Event**: potential disturbance to safety ECUs
- **Severity / Exposure / Controllability**: S0 / E4 / C3 -> **ASIL QM**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by gateway forwards prohibited diagnostic services.
- **Derived Requirement Chain**:
  - FSR: Detect gateway forwards prohibited diagnostic services and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control gateway forwards prohibited diagnostic services.
  - System Requirement: The assigned function shall react to gateway forwards prohibited diagnostic services within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'vehicle in motion with external tester connected'.

### 13.35 Parking assist unsupported trailer mode

- **Operational Situation**: trailer attached to vehicle
- **Malfunctioning Behaviour**: parking automation still allowed
- **Hazardous Event**: vehicle geometry assumption invalid leading to collision risk
- **Severity / Exposure / Controllability**: S2 / E4 / C2 -> **ASIL B**
- **Derived Safety Goal**: Prevent or adequately mitigate hazardous behaviour caused by parking automation still allowed.
- **Derived Requirement Chain**:
  - FSR: Detect parking automation still allowed and initiate the defined safe, degraded, or warning response.
  - TSR: Implement the monitoring, integrity checks, supervision logic, and protected interfaces needed to control parking automation still allowed.
  - System Requirement: The assigned function shall react to parking automation still allowed within the time budget assumed by HARA.
  - Verification Requirement: Create simulation, HIL, and/or vehicle tests reproducing the situation 'trailer attached to vehicle'.

### 13.36 HARA-to-Requirement Review Prompts

- Did the hazardous event combine operating situation and malfunctioning behaviour?
- Is the derived safety goal phrased as a vehicle-level harm prevention objective?
- Are FSRs function-oriented while TSRs are architecture-oriented?
- Does the chain allocate at least one verification method for every derived requirement?
- If the ASIL is reduced by decomposition, is the rationale recorded and traceable?

## Section 14: REQUIREMENTS + SOTIF

SOTIF (Safety of the Intended Functionality, ISO 21448) addresses hazards arising **without a fault** when the intended function is limited, the environment is unusual, or perception/control performance is insufficient.

### 14.1 How SOTIF Requirements Are Created

Identify the intended function and the operational design domain (ODD).
Identify functional insufficiencies, performance limitations, and triggering conditions.
Define detection, limitation, warning, fallback, or ODD-restriction requirements.
Verify through scenario-based simulation, dataset replay, proving-ground tests, and field observation.
Feed discovered unknown scenarios back into requirements, datasets, and validation plans.

### 14.2 SOTIF Requirement Families

| Family | Typical Concern | Example Countermeasure Requirement |
|---|---|---|
| Sensor limitations | Weather, glare, contamination, occlusion | Detect reduced sensing quality and restrict feature availability |
| Perception limitations | Misclassification, missed detections, wrong fusion | Bound intervention to validated confidence and context |
| Environmental conditions | Construction zones, snow, tunnels, low sun | Detect ODD reduction and degrade or hand over |
| Edge cases | Rare objects, odd trajectories, uncommon infrastructure | Use conservative handling or explicit ambiguity state |
| Triggering conditions | Known corner cases that provoke insufficiency | Create monitors, warnings, or inhibit rules |
| Unknown scenarios | Not yet represented in design/validation set | Log, shadow-evaluate, and continuously update requirement catalogue |
| Performance limitations | Range, latency, classification quality, localization uncertainty | Specify measurable boundaries and actions on exceedance |

### 14.3 Sensor limitations

- **REQ-SOTIF-SNS-01**: The feature set shall monitor camera occlusion, radar blockage, ultrasonic contamination, and GNSS degradation indicators relevant to each feature.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-SNS-02**: The requirements for sensor limitations shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-SNS-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when sensor limitations exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-SNS-04**: Validation evidence for sensor limitations shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-SNS-05**: New findings about sensor limitations from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.4 Perception limitations

- **REQ-SOTIF-PRC-01**: The feature set shall publish confidence, uncertainty, and ambiguity information for intervention-relevant objects and lanes.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PRC-02**: The requirements for perception limitations shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PRC-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when perception limitations exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PRC-04**: Validation evidence for perception limitations shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PRC-05**: New findings about perception limitations from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.5 Environmental conditions

- **REQ-SOTIF-ENV-01**: The feature set shall declare the environmental conditions under which validated performance is claimed and supervise ODD exit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-ENV-02**: The requirements for environmental conditions shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-ENV-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when environmental conditions exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-ENV-04**: Validation evidence for environmental conditions shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-ENV-05**: New findings about environmental conditions from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.6 Edge cases

- **REQ-SOTIF-EDG-01**: The feature set shall include rare but plausible objects, trajectories, and infrastructure patterns in the scenario catalogue.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-EDG-02**: The requirements for edge cases shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-EDG-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when edge cases exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-EDG-04**: Validation evidence for edge cases shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-EDG-05**: New findings about edge cases from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.7 Triggering conditions

- **REQ-SOTIF-TRG-01**: The feature set shall document known triggering conditions as explicit inhibitors, degraders, or caution states.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-TRG-02**: The requirements for triggering conditions shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-TRG-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when triggering conditions exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-TRG-04**: Validation evidence for triggering conditions shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-TRG-05**: New findings about triggering conditions from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.8 Unknown scenarios

- **REQ-SOTIF-UNK-01**: The feature set shall discover, assess, and feed back unknown unsafe scenarios found after design-time analysis.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-UNK-02**: The requirements for unknown scenarios shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-UNK-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when unknown scenarios exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-UNK-04**: Validation evidence for unknown scenarios shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-UNK-05**: New findings about unknown scenarios from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.9 Performance limitations

- **REQ-SOTIF-PER-01**: The feature set shall state quantitative performance limits and define behaviour when those limits are exceeded.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PER-02**: The requirements for performance limitations shall distinguish between detectable online limitations and limitations that require ODD restriction or user guidance.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PER-03**: The system shall degrade, inhibit, warn, or request takeover according to the validated strategy when performance limitations exceed the approved limit.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PER-04**: Validation evidence for performance limitations shall include scenario-based simulation, replay, proving-ground cases, and documented acceptance criteria.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

- **REQ-SOTIF-PER-05**: New findings about performance limitations from field data or safety analysis shall be converted into traceable requirement updates where safety-relevant.
  - *Rationale*: Representative SOTIF requirement pattern.
  - *Verification*: Scenario-based validation, evidence review, and change-traceability audit.

### 14.10 ADAS-Focused SOTIF Scenario Examples

| Feature | Scenario | SOTIF Concern | Example Requirement Intent |
|---|---|---|---|
| ACC | Low sun directly behind lead vehicle | Target detection confidence drops despite no hardware fault | Reduce maximum speed support, keep driver informed, and cancel distance mode if target confidence falls below threshold. |
| ACC | Sharp cut-in by motorcycle | Object appears late with unstable classification | Use conservative gap policy and inhibit aggressive resume until track stabilises. |
| AEB | Pedestrian partially occluded by parked van | Late perception of emerging VRU | Use occlusion-aware collision prediction and escalate warning earlier where validated. |
| AEB | Metal plate reflection on wet road | False obstacle candidate from reflection | Require multi-cue confirmation before emergency braking unless immediate close-range evidence exists. |
| LKA | Construction zone with temporary yellow lane markings | Nominal lane model may follow obsolete white lines | Prioritise temporary-lane cues or degrade to warning-only when ambiguity persists. |
| LKA | Road edge without lane markings | Lane boundary estimate may drift toward curb or shoulder | Restrict torque intervention when road-edge confidence alone is below validated threshold. |
| BSD | Fast-approaching motorcycle in adjacent lane | Short dwell time challenges track continuity | Specify minimum detection and warning timing for high relative-speed objects. |
| RCTA | Parking lot with diagonal traffic aisle | Cross-traffic geometry differs from typical model | Extend scenario model or inhibit when geometry confidence is insufficient. |
| TSR | Temporary paper sign in work zone | Sign appearance differs from training set | Introduce ambiguity state or rely on map/cluster ambiguity handling. |
| Driver Monitoring | Driver wears mask, hat, and sunglasses at dusk | Facial-feature visibility is strongly reduced without camera fault | Output uncertain supervision state and trigger stronger confirmation strategy. |
| Highway Assist | Lane splits near toll area | Path selection ambiguity increases even though sensors are healthy | Trigger ODD exit or takeover request when route confidence falls below limit. |
| Parking Assist | Low curb hidden by snow | Obstacle model under-represents low obstacle | Require conservative speed and driver brake responsibility under snow-coverage uncertainty. |

### 14.11 Practical SOTIF Requirement Patterns

- When sensing confidence for a function falls below the validated threshold, the system shall degrade or disable the intervention that depends on that confidence.
- If the environment indicates departure from the validated ODD, the system shall inform the driver and transition to the defined fallback mode.
- Where perception ambiguity exists between multiple scene interpretations, the system shall choose the validated conservative action or request driver takeover.
- The feature shall log unresolved low-confidence scenarios for post-release improvement where privacy and governance rules permit.
- The feature shall state quantitatively what performance it claims and what it does when that claim can no longer be met.

### 14.12 Final Engineering Takeaways

- Functional safety and SOTIF are complementary: one addresses faults, the other addresses intended-function insufficiency and uncertainty.
- A requirement set is mature only when nominal behaviour, degraded behaviour, and user communication are all explicitly defined.
- ADAS requirements must always connect perception validity to control authority and HMI state.
- Traceability is not paperwork overhead; it is the mechanism that keeps safety intent intact through architecture, implementation, testing, and change management.
- Well-written requirements are measurable, scenario-based, and aligned with both the safety case and the operational design domain.

---

End of document.
