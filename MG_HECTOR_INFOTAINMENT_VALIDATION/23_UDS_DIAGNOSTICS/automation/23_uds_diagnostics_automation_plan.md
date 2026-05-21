# Automation Plan: UDS Diagnostics

## Automatable Checks

- Start/stop CANoe measurement.
- Set power mode, gear, speed and feature-specific system variables.
- Collect CAN traces and adb logs.
- Read software DID and DTC status.
- Parse result evidence and generate markdown/JUnit reports.

## Suggested pytest Names

- `test_uds_diagnostics_smoke`
- `test_uds_diagnostics_negative_missing_signal`
- `test_uds_diagnostics_sleep_wakeup_recovery`
- `test_uds_diagnostics_stress_cycles`

## Manual Review Remains Needed For

- Visual UI correctness.
- Audio quality.
- Camera image quality.
- User experience wording.
- Any safety or legal warning behavior.
