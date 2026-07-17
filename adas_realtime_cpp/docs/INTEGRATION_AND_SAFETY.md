# Integration and Safety Guide

## Interface control document (ICD)

Before connecting the core to an ECU, create an ICD for each `SensorFrame` source and `ActuatorCommand` sink. It must identify producer, consumer, unit, resolution, valid range, update period, maximum age, timeout value, counter, CRC/E2E profile, default value, ASIL/QM classification, and diagnostic response.

| Signal group | Nominal update | Maximum accepted age | Minimum validation |
|---|---:|---:|---|
| Ego state (speed/yaw/steering) | 10–20 ms | 100 ms | Range, counter, CRC, timestamp |
| Object track | 50 ms | 100 ms | Track validity, confidence, coordinate frame, timestamp |
| Lane model | 50 ms | 100 ms | Confidence, geometry plausibility, timestamp |
| Actuator command | 20 ms | Target-specific | Counter, CRC/E2E, enable state, rate/limit check |

The values are starting assumptions. The system specification owns final timing values.

## Gateway responsibilities

The gateway is a safety boundary. It shall:

1. Validate input transport integrity before constructing a frame.
2. Convert all units and coordinate conventions once, at the boundary.
3. Capture a monotonic receive timestamp and reject stale or future-dated information.
4. Publish coherent snapshots; never combine fields from different message cycles without defined synchronization.
5. Apply final command plausibility, actuator state checks, sequence protection, and reporting.
6. Report timeout and integrity faults to diagnostics/health monitoring without blocking the controller.

## Scheduling budget

Use a measured end-to-end budget such as:

$$T_\mathrm{e2e}=T_\mathrm{sensor}+T_\mathrm{transport}+T_\mathrm{queue}+T_\mathrm{compute}+T_\mathrm{actuator}$$

Allocate each term and show measurement evidence on the actual SoC/ECU. NVIDIA and Qualcomm platforms require an explicit deployment design: CPU affinity, thread priorities, cache/memory-bandwidth contention controls, GPU/accelerator hand-off behavior, thermal derating strategy, and start-up/shutdown timing. The provided control core stays CPU-only to make its timing predictable; perception acceleration belongs upstream.

## Security and update posture

Authenticate diagnostic/update access, use secure boot and signed artifacts where supported, restrict debug ports in production, maintain SBOM and vulnerability management, and define key/credential ownership. SOME/IP service discovery and Ethernet ingress must be segmented and filtered per the vehicle cybersecurity architecture. Perform threat analysis and risk assessment under the organization’s applicable process (for example ISO/SAE 21434).

## Safety case checklist

- Item definition, HARA, functional and technical safety concepts approved.
- Safety goals mapped to independent detection/mitigation mechanisms.
- Freedom from interference established for shared SoC resources.
- Software architecture, coding standard, tool qualification, and verification plan approved.
- Calibration and data sets controlled.
- SIL/HIL/vehicle evidence covers the approved ODD and fault model.
- Production diagnostics, logging, traceability, and field-monitoring plan accepted.

## Bilingual collaboration note

For globally distributed teams, maintain the normative ICD, requirements, safety artifacts, and test verdicts in a controlled English baseline. Provide reviewed Chinese translations for operational clarity where required, preserving signal names, units, identifiers, and requirement IDs exactly. Never use a translation as an uncontrolled substitute for the approved baseline.
