# CANoe Regression Suite

## Suites

- `SmokeSuite`: boot, heartbeat, software DID, no critical DTC.
- `PowerSuite`: KL15/KL30, ACC, crank, shutdown, sleep and wakeup.
- `FeatureSuite`: IVI, Bluetooth, USB, projection, camera, cluster and SWC.
- `DiagSuite`: DID, DTC, sessions, reset and negative responses.
- `StressSuite`: cycle and endurance tests.

## Report Rule

Every automated test shall output XML/JUnit plus a human-readable summary with trace file name, build ID and bench ID.
