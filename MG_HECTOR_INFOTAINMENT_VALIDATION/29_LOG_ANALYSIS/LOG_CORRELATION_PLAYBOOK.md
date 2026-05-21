# Log Correlation Playbook

## Evidence Sources

- CANoe BLF/ASC: vehicle stimulus and ECU messages.
- Android logcat: framework, app and service logs.
- Kernel logs: driver, USB, audio, camera and filesystem events.
- Ethernet pcap: DoIP, SOME/IP, OTA and service discovery.
- CANoe diagnostic log: UDS request/response timing.

## Method

Normalize timestamps, mark T0 stimulus, identify first incorrect state, then walk backward to the earliest abnormal dependency.
