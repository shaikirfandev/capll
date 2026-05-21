# CANoe Project Blueprint

## Recommended Config

- `MGH_IVI_Bench.cfg`: main configuration.
- `Databases/`: BodyCAN, InfoCAN, DiagCAN DBC placeholders.
- `CAPL/`: rest bus simulation nodes and test helpers.
- `Panels/`: power, gear, speed, doors, SWC, diagnostics and fault injection.
- `TestModules/`: smoke, feature, diagnostics, stress and regression groups.
- `Logs/`: BLF formal logs and ASC training logs.

## Measurement Setup

Trace -> Graphics -> Data -> Diagnostics -> Write -> Logging.

## Test Setup Groups

- Smoke: boot, heartbeat, DID read and DTC no-fault baseline.
- Feature: IVI feature tests by module.
- Negative: missing messages, invalid ranges, bus off and peripheral disconnect.
- Stress: cycle, endurance and overload.
- Regression: P0/P1 release gate tests.
