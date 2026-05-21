# OEM Validation Workflow: IVI Features

## Entry Criteria

- Released build installed or flashed.
- Bench ID, harness revision, power supply model and CAN interface logged.
- DBC, diagnostic spec and test procedure versions frozen.
- Known issues reviewed before execution.

## Execution

1. Bench health check: power, CAN, Ethernet, adb, audio, camera and USB.
2. Baseline capture: boot, heartbeat, DIDs, DTC snapshot and software version.
3. Feature execution: nominal, negative, boundary, stress and recovery.
4. Log package: CANoe BLF/ASC, logcat, kernel log, report XML/PDF, screenshots/video.
5. Defect triage: isolate stimulus, reproduction rate and suspected layer.

## Exit Criteria

- All P0/P1 cases pass or have approved deviations.
- No open critical defects for release candidate.
- Regression cases executed after every fix.
- Traceability matrix updated with evidence path.
