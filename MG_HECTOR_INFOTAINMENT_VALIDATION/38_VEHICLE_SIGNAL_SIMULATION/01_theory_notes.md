# Theory Notes: Vehicle Signal Simulation

## Engineering View

In production infotainment validation, vehicle signal simulation is never tested as an isolated feature only. It is validated as a chain of vehicle signals, middleware state, Android/Linux services, app behavior, persistence, user interaction and recovery behavior after power or connectivity disturbance.

Core focus: speed, gear, doors, power mode, lamps and network states.

## Automotive Use Case

A customer action such as selecting reverse gear, pressing a steering switch, pairing a phone or starting navigation becomes a validation problem across:

- Vehicle input source and signal timing.
- Network delivery and timeout handling.
- IVI service reaction time.
- UI/audio/video output correctness.
- Diagnostic state and DTC behavior.
- Logs and evidence needed for production triage.

## MG Hector-Style Feature Explanation

Use this as an MG Hector-style connected SUV infotainment bench. The representative head unit receives BCM, cluster, powertrain, HVAC, steering switch and camera gateway information over CAN and Ethernet. The IVI exposes user-facing features such as media, navigation, phone, projection, camera display, vehicle settings and connected services. Real program values must come from the released DBC, ARXML, diagnostic specification and system requirements.

## Bench Setup Workflow

1. Confirm power rails: KL30 permanent battery, KL15 ignition, ACC/accessory if available and ground reference.
2. Confirm communication: CAN termination, channel mapping, baud rate, database attachment and Ethernet link.
3. Start CANoe measurement with rest bus nodes active before IVI wakeup when the test requires realistic network availability.
4. Apply the vehicle state sequence and verify IVI response against KPI.
5. Capture logs from CANoe and Android/Linux at the same timestamp.

## CANoe Setup

- Assign network databases to physical or virtual CAN channels.
- Model unavailable ECUs as rest bus simulation nodes.
- Add panels for power mode, gear, speed, door, steering switch and DTC injection.
- Enable BLF/ASC logging with test name, build ID and bench ID in the filename.
- Use Test Setup or vTESTstudio for automated pass/fail verdicts.

## UDS Validation

Basic diagnostic checks for each feature:

- `0x10 0x03`: extended diagnostic session.
- `0x22 DID`: read software, hardware, calibration and feature-specific DIDs.
- `0x19 0x02`: read DTC by status mask after fault injection.
- `0x11 0x01`: ECU reset only when the test plan allows it.

## Production Debugging

Start with the evidence timeline. If the IVI output is wrong, verify input correctness first, then network timing, then service logs, then UI or app layer. A good RCA proves both the fault and the non-fault boundaries.

## OEM Validation Process

- Requirement review and ambiguity closure.
- Test design review with feature owner.
- Bench dry run and environment baseline.
- Formal execution with released build.
- Defect triage with attached logs and reproduction rate.
- Regression after fix and release sign-off.

## Interview Questions

1. How would you prove the issue is in the IVI and not the simulated ECU?
2. What evidence do you attach to a production defect?
3. How do you handle a requirement that does not specify timeout behavior?
4. What is the difference between functional, integration and system validation for this module?
5. How do CANoe, CAPL and adb complement each other during RCA?

## Failure Scenarios

- Missing or delayed CAN signal.
- Incorrect power mode transition.
- IVI service crash or ANR.
- Timeout threshold mismatch between spec and implementation.
- Persistence failure after sleep, wakeup or OTA.

## Performance Optimization

Measure before optimizing. Track signal-to-output latency, CPU, memory, binder load, app launch time, frame drops and boot readiness. Keep KPIs tied to user-visible behavior and release gates.
