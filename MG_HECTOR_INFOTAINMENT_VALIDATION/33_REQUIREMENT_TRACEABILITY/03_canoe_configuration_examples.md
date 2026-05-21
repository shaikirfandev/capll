# CANoe Configuration Examples: Requirement Traceability

## Configuration Layout

- Networks: `BodyCAN`, `InfoCAN`, optional `DiagCAN`, optional `Ethernet`.
- Databases: representative DBC files for BCM, VCU, TCU, SWC, Cluster and IVI.
- Simulation Setup: rest bus nodes for BCM, VCU, TCU, SWC, Cluster and Camera Gateway.
- Measurement Setup: Trace, Graphics, Data, Diagnostics, Write and Logging blocks.
- Test Setup: smoke tests, functional tests, negative tests, stress tests and diagnostics tests.

## Recommended Logging

- Format: BLF for formal evidence, ASC for readable training examples.
- Naming: `BenchID_BuildID_Feature_TestCase_Timestamp`.
- Always log from 10 seconds before stimulus until 10 seconds after expected stable state.

## Rest Bus Simulation Signals

| Node | Message | Signals | Purpose |
| --- | --- | --- | --- |
| BCM | `BCM_PowerMode` | `PowerMode` | OFF/ACC/IGN/CRANK transitions |
| TCU | `TCU_GearStatus` | `GearPosition` | Reverse camera and cluster validation |
| VCU | `VCU_VehicleSpeed` | `VehicleSpeed_kph` | speed-dependent lockouts and navigation |
| SWC | `SWC_Buttons` | `SWC_KeyCode` | steering controls |
| IVI | `IVI_Status` | `IVI_BootState` | readiness and heartbeat verification |

## Automated Verdict Pattern

1. Set initial vehicle state.
2. Wait for stable IVI heartbeat.
3. Inject stimulus.
4. Measure response in CAN, diagnostics and Android logs.
5. Apply timeout and tolerance.
6. Save verdict with evidence references.
