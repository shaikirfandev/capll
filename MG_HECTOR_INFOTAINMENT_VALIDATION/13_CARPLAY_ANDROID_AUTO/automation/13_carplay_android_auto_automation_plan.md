# Automation Plan: CarPlay Android Auto

## Automatable Checks

- Start/stop CANoe measurement.
- Set power mode, gear, speed and feature-specific system variables.
- Collect CAN traces and adb logs.
- Read software DID and DTC status.
- Parse result evidence and generate markdown/JUnit reports.

## Suggested pytest Names

- `test_carplay_android_auto_smoke`
- `test_carplay_android_auto_negative_missing_signal`
- `test_carplay_android_auto_sleep_wakeup_recovery`
- `test_carplay_android_auto_stress_cycles`

## Manual Review Remains Needed For

- Visual UI correctness.
- Audio quality.
- Camera image quality.
- User experience wording.
- Any safety or legal warning behavior.
