# vTESTstudio Test Module Blueprint

## Test Case Pattern

```text
TestCase ReverseCamera_Activation
  Precondition:
    PowerMode = IGN
    VehicleSpeed = 0
    IVI heartbeat valid
  Action:
    Set GearPosition = R
  Expected:
    IVI camera active state within 700 ms
    No camera DTC during nominal path
  Evidence:
    CANoe report, BLF trace, screen video, UDS readout
```

## Automated Signal Verification

- Use system variables or CAPL functions as stimulus hooks.
- Use wait conditions for IVI heartbeat, boot state and feature state.
- Keep all verdict thresholds in one parameter table.
- Export XML reports for CI dashboards and PDF reports for release boards.

