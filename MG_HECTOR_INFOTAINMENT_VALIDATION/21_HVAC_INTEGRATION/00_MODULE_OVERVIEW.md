# Module Overview: HVAC Integration

## Purpose

This module turns `HVAC Integration` into a production validation work package. The focus is climate signal display, controls and status synchronization. The expected learner output is not only theoretical understanding, but the ability to run a bench-level validation activity, collect evidence, explain failures, and defend the result in an OEM release review.

## Definition Of Complete

- You can explain the feature or domain architecture in IVI terms.
- You can identify the vehicle signals, diagnostics, Android/Linux services and user-facing outputs involved.
- You can configure CANoe monitoring or rest bus simulation for the relevant state.
- You can execute nominal, negative, boundary, recovery and stress tests.
- You can collect synchronized CANoe, diagnostic, Android/Linux and visual evidence.
- You can produce a release-quality defect report and RCA.
- You can answer senior interview questions using this module as a real project example.

## MG Hector-Style Context

Use this as a representative MG Hector connected-SUV infotainment bench. Replace the training DBC, DIDs, timing and topology with released program data on a real project. The workflow remains the same: requirement review, bench setup, CANoe/CAPL simulation, execution, evidence, RCA, regression and sign-off.

## Interfaces To Check

| Layer | What To Verify |
| --- | --- |
| Power | KL30, KL15, ACC, crank, sleep and wake behavior |
| CAN | cyclic message presence, signal scaling, timeout, alive counter |
| Diagnostics | software DID, DTC status, session behavior, negative response |
| Android/Linux | service state, logcat, kernel, process health, memory |
| User Output | UI, audio, video, warnings, responsiveness and persistence |
| Automation | repeatability, evidence naming, verdict traceability |
