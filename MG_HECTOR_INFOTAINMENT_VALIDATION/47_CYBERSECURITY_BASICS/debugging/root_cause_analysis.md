# Root Cause Analysis Template: Cybersecurity Basics

## Problem Statement

During cybersecurity basics validation, the IVI behavior deviated from requirement under a defined bench state.

## Evidence Timeline

| Time | Evidence | Observation |
| --- | --- | --- |
| T-10 s | CANoe trace | Rest bus active |
| T0 | Stimulus | Vehicle signal injected |
| T+X ms | IVI response | Missing, delayed or incorrect behavior |
| T+Y s | UDS/logcat | DTC or service log confirms layer |

## Five-Why Pattern

1. Why did the user-visible behavior fail?
2. Why did the IVI service not produce the expected output?
3. Why was the input, state or dependency invalid?
4. Why did validation not catch it earlier?
5. What prevention action closes the gap?

## Corrective Actions

- Software fix or calibration change.
- Test case update for regression.
- Bench simulation correction if the bench caused the fault.
- Requirement clarification when timing or state behavior is ambiguous.
