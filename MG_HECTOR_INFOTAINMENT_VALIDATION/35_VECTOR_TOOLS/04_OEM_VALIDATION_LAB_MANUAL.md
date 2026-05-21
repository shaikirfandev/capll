# OEM Validation Lab Manual: Vector Tools

## Lab Objective

Validate vector tools on an MG Hector-style IVI bench using CANoe, CAPL, Python, adb/logcat and UDS diagnostics.

## Equipment

- IVI head unit or software bench equivalent.
- Programmable 12 V DC supply with current limit.
- Vector VN interface and CANoe.
- Bench harness with KL30, KL15, ACC, GND, CAN-H, CAN-L and required peripherals.
- Android reference phone, iPhone reference device, USB media, camera simulator or media converter when relevant.
- Automation PC with Python, pytest and adb.

## Pre-Execution Checklist

1. Confirm bench ID, harness revision and power supply current limit.
2. Start CANoe and load the representative or project DBC.
3. Verify no critical DTC is present before stimulus.
4. Capture software version DID and build fingerprint.
5. Start synchronized CANoe logging and Android/Linux logging.

## Execution Flow

1. Set bench to a known state: KL30 on, KL15 off, CANoe measurement stopped.
2. Start CANoe measurement and rest bus simulation.
3. Apply KL15/IGN and wait for IVI ready.
4. Execute the nominal test path for vector tools.
5. Execute at least three fault injections from `06_FAILURE_INJECTION_MATRIX.csv`.
6. Execute one recovery path: sleep/wakeup, reconnect, reset or ignition cycle.
7. Read DTCs and capture post-test software/service state.
8. Fill report and traceability artifacts.

## Pass Criteria

- Functional result matches requirement.
- No critical crash, boot loop, stale state, blocked UI or unexpected DTC.
- Performance KPI is measured or explicitly marked not applicable.
- Evidence is sufficient for a third-party reviewer to reproduce and understand the result.

## Common Bench Mistakes

- Running a feature test before IVI boot readiness is stable.
- Trusting CANoe physical output without checking channel mapping.
- Filing a software defect before proving the simulated ECU signal is correct.
- Missing pre-fault and post-fault DTC snapshots.
- Capturing logs without build ID, bench ID or timestamp.
