# Automation Plan: Python Automation

## Automatable Checks

- Start/stop CANoe measurement.
- Set power mode, gear, speed and feature-specific system variables.
- Collect CAN traces and adb logs.
- Read software DID and DTC status.
- Parse result evidence and generate markdown/JUnit reports.

## Suggested pytest Names

- `test_python_automation_smoke`
- `test_python_automation_negative_missing_signal`
- `test_python_automation_sleep_wakeup_recovery`
- `test_python_automation_stress_cycles`

## Manual Review Remains Needed For

- Visual UI correctness.
- Audio quality.
- Camera image quality.
- User experience wording.
- Any safety or legal warning behavior.
