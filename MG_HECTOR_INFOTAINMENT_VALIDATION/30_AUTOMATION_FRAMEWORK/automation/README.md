# Automation Skeleton

This is a bench-safe pytest framework skeleton for MG Hector-style IVI validation.

Default behavior is dry-run. Real bench control should be enabled only after reviewing `config/bench.yaml`, CANoe COM permissions, adb access and diagnostic safety rules.

## Flow

1. `pytest` loads bench configuration.
2. CANoe adapter starts measurement or prints dry-run actions.
3. CAPL/rest bus provides vehicle signals.
4. adb adapter collects logcat, build properties and dumpsys evidence.
5. Diagnostics adapter reads DIDs and DTCs through a replaceable transport.
6. Tests write structured evidence paths and assertions.

## Example

```bash
python3 -m pytest automation/tests -q
```

