# Verification Strategy

## Test layers

| Layer | Objective | Example evidence |
|---|---|---|
| Unit | Boundary conditions and algorithm math | `adas_tests`, coverage report, static analysis |
| SIL | Closed-loop behavior with vehicle plant | scenario logs, KPIs, regression baseline |
| MIL | Model/controller equivalence where applicable | MATLAB/Simulink comparison report |
| HIL | Timing, I/O, diagnostics, fault injection | CANoe, restbus, ECU trace, test report |
| Vehicle | ODD behavior and driver interaction | approved proving-ground test cases |

## Required scenario families

- ACC: set-speed tracking, slow lead, cut-in/cut-out, stop-and-go, grade, sensor disagreement.
- AEB: stationary/moving targets, short TTC, degraded object confidence, false target, driver brake and accelerator override.
- LKA/Lane centring: straight/curved roads, lane change, lane loss, worn markings, camera timeout, driver steering torque override.
- Integration: CRC/counter failure, stale timestamp, missing CAN cycle, SOME/IP service loss, gateway reset, actuator unavailable, CPU overload.

## Release gates

1. Compile with warnings treated as errors and run static analysis appropriate to the target coding standard (MISRA C++ or AUTOSAR C++14 where mandated).
2. Demonstrate requirements-to-test traceability and branch/MC/DC goals required by the safety plan.
3. Establish WCET, end-to-end latency, CPU, stack, and memory budgets on target hardware.
4. Run fault injection and validate all safety mechanisms.
5. Obtain independent review and approval under the project functional-safety and cybersecurity processes.

The included tests are starter checks only; they are not a release qualification suite.
