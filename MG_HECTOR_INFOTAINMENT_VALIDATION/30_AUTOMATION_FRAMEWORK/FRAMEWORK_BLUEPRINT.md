# Full Infotainment Automation Framework

```text
automation/
  config/bench.yaml
  adapters/canoe.py
  adapters/adb.py
  adapters/diagnostics.py
  adapters/can_log.py
  tests/test_boot.py
  tests/test_reverse_camera.py
  tests/test_bluetooth.py
  reports/
  evidence/
```

## Design

- pytest controls test flow and verdicts.
- CANoe COM starts/stops measurement and drives environment variables.
- CAPL provides fast real-time vehicle signal simulation.
- adb collects logcat, dumpsys and screenshots.
- Diagnostic adapter reads DIDs and DTCs.
- Report generator links every verdict to evidence files.
