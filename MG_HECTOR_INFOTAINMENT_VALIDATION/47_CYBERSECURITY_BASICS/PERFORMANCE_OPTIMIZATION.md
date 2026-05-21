# Performance Optimization: Cybersecurity Basics

## KPIs

- Signal-to-UI latency.
- Input-to-audio latency where audio is involved.
- Frame drop count for video or UI animation.
- CPU, memory, binder thread and IO pressure during stimulus.
- Recovery time after sleep, wakeup, USB reconnect or phone reconnect.

## Measurement Pattern

1. Timestamp stimulus in CANoe.
2. Timestamp IVI state change in CAN, logcat or screen capture.
3. Compute P50, P95 and worst-case latency over repeated runs.
4. Compare against KPI and build-to-build trend.
5. File performance defects with raw evidence and environment metadata.
