# Reverse Camera Latency Workflow

## KPI Measurement

- T0: CANoe transmits `GearPosition = R`.
- T1: IVI publishes camera active state or screen capture detects camera frame.
- Latency: `T1 - T0`.
- Repeat: 30 cold, 30 warm, 30 after sleep/wakeup.

## Fault Injection

- Reverse signal missing.
- Camera video absent.
- Camera gateway reports fault.
- Gear toggles R-D-R quickly.
- Low voltage during camera activation.

## Pass Criteria

Camera view activates within KPI, no stale frame after gear out of reverse, dynamic guidelines follow steering input if supported, and DTC behavior matches diagnostic specification.
