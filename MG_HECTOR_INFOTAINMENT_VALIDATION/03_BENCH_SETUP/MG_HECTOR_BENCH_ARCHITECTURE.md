# MG Hector-Style Bench Architecture

## Representative ECU Topology

| Domain | ECU/Node | IVI Dependency |
| --- | --- | --- |
| Body | BCM | power mode, doors, lamps, vehicle lock state |
| Powertrain | VCU/ECM/TCU | speed, gear, engine state |
| Cockpit | Cluster | warnings, tell-tales, trip and alert sync |
| Controls | Steering switch module | media, phone, volume, voice button |
| Comfort | HVAC controller | climate display and control feedback |
| Vision | Reverse/360 camera ECU | video stream, camera state, diagnostic faults |
| Connectivity | TCU/telematics | OTA, connected services, emergency call status |
| Infotainment | IVI head unit | UI, audio, projection, navigation, vehicle settings |

## Bench Bring-Up Sequence

1. Connect power supply with current limit set low for first power-up.
2. Verify harness pinout, ground continuity and CAN termination.
3. Connect Vector interface and start CANoe in listen-only for sanity check.
4. Enable rest bus simulation and cyclic messages.
5. Apply KL30, then ACC/KL15 according to the test case.
6. Confirm IVI heartbeat, boot status and diagnostic response.
7. Capture software version DIDs and initial DTC snapshot.

## Troubleshooting Rules

- No power draw: check fuse, ground, KL30 and connector seating.
- High current: power down, inspect harness and current limit, isolate peripherals.
- No CAN traffic: check channel mapping, transceiver, termination and bus wakeup.
- IVI boots but feature absent: verify feature coding, region config, service logs and dependent ECU simulation.
