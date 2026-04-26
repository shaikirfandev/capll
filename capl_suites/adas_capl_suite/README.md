# ADAS CAPL Automation Suite
## Advanced Driver Assistance Systems – CANoe/CANalyzer Test Automation

---

## Overview

This suite contains **30 CAPL automation scripts** for validating ADAS (Advanced Driver Assistance Systems) ECUs using Vector CANoe/CANalyzer. Scripts cover sensor fusion, object detection, safety functions, mode management, diagnostics, and regression testing aligned with ISO 26262, NCAP, and OEM requirements.

---

## Suite Structure

```
adas_capl_suite/
├── README.md
├── 01_fcw_validation.capl              – Forward Collision Warning
├── 02_aeb_test.capl                    – Autonomous Emergency Braking
├── 03_acc_state_machine.capl           – Adaptive Cruise Control
├── 04_lka_validation.capl              – Lane Keep Assist
├── 05_ldw_test.capl                    – Lane Departure Warning
├── 06_bsd_validation.capl              – Blind Spot Detection
├── 07_rcta_test.capl                   – Rear Cross Traffic Alert
├── 08_parking_sensor.capl              – Parking Sensor Array Test
├── 09_radar_target_sim.capl            – Radar Target Simulation
├── 10_camera_fusion.capl               – Camera-Radar Sensor Fusion
├── 11_adas_can_monitor.capl            – ADAS CAN Signal Monitor
├── 12_speed_limit_recognition.capl     – Speed Limit Recognition (SLI)
├── 13_pedestrian_detection.capl        – Pedestrian Detection Validation
├── 14_dms_validation.capl              – Driver Monitoring System
├── 15_highway_pilot.capl               – Highway Pilot Mode
├── 16_adas_dtc_management.capl         – DTC Lifecycle Management
├── 17_sensor_calibration_check.capl    – Sensor Calibration Verification
├── 18_adas_power_mode.capl             – Power Mode Transitions
├── 19_adas_fault_injection.capl        – Fault Injection & Recovery
├── 20_object_distance_monitor.capl     – Object Distance Monitoring
├── 21_adas_gateway_routing.capl        – ADAS Gateway CAN Routing
├── 22_ncap_automation.capl             – NCAP Test Sequence Automation
├── 23_adas_logging.capl                – Test Logging & Reporting
├── 24_adas_wake_sleep.capl             – Wake/Sleep Cycle Validation
├── 25_sensor_health_monitor.capl       – Sensor Health & Timeout Check
├── 26_adas_regression_suite.capl       – Full Regression Test Runner
├── 27_adas_uds_diagnostics.capl        – UDS Diagnostics for ADAS ECU
├── 28_emergency_brake_light.capl       – Emergency Brake Light (EBL)
├── 29_tsr_validation.capl              – Traffic Sign Recognition
└── 30_adas_e2e_test.capl               – End-to-End ADAS Integration Test
```

---

## Test Environment

| Parameter | Value |
|-----------|-------|
| Tool | Vector CANoe 16+ / CANalyzer |
| Bus | CAN FD (Powertrain: 500/2000 kbps), CAN C (500 kbps) |
| DBC | ADAS_System.dbc + ADAS_FD.dbc |
| ECUs Under Test | ADAS Domain Controller, Radar ECU, Camera ECU, Sensor Fusion ECU |
| Standards | ISO 26262 ASIL-B/D, Euro NCAP 2025, ISO 21448 (SOTIF) |

---

## Signal Reference

| Signal | Message ID | Description |
|--------|-----------|-------------|
| FCW_Warning | 0x300 | Forward collision warning level (0–3) |
| AEB_Active | 0x301 | AEB activation status |
| ACC_SetSpeed | 0x302 | ACC target speed (km/h) |
| LKA_Active | 0x303 | Lane keep assist active |
| LDW_LeftAlert | 0x304 | Left lane departure alert |
| LDW_RightAlert | 0x304 | Right lane departure alert |
| BSD_Left | 0x305 | Blind spot left detection |
| BSD_Right | 0x305 | Blind spot right detection |
| RCTA_Alert | 0x306 | Rear cross traffic alert |
| ParkSensor_Front | 0x307 | Front parking distance (cm) |
| RadarObj_Distance | 0x308 | Lead object distance (m) |
| RadarObj_Speed | 0x308 | Lead object relative speed (km/h) |
| CameraLane_Valid | 0x309 | Camera lane detection valid |
| ADAS_Mode | 0x310 | System mode (0=Off, 1=Standby, 2=Active, 3=Override) |
| Driver_TorqueInput | 0x311 | Driver steering torque |
| VehicleSpeed | 0x100 | Vehicle speed km/h (from ESP) |
| YawRate | 0x101 | Yaw rate deg/s |
| SteeringAngle | 0x102 | Steering wheel angle |

---

## How to Run

1. Open CANoe project and load `ADAS_System.cfg`
2. Load the desired `.capl` script into a CAPL node
3. Assign relevant DBC databases
4. Start measurement → scripts auto-execute on `on start`
5. Key shortcuts are documented in each script header

---

## Pass/Fail Criteria Reference

| Test | Pass Condition |
|------|---------------|
| FCW | Warning level ≥ 2 when TTC ≤ 2.5s |
| AEB | Brake applied within 600ms of TTC ≤ 1.5s |
| ACC | Speed maintained ±5 km/h of set speed |
| LKA | Correction active when offset ≥ 0.3m |
| LDW | Alert within 200ms of lane line crossing |
| AEB Deactivation | Deactivates when speed < 10 km/h |
| DMS | Alert within 3s of eye closure |

---

## Script Categories

| Category | Scripts |
|----------|---------|
| Warning Systems | 01, 05, 06, 07, 08, 12 |
| Active Safety | 02, 03, 04, 15 |
| Sensor Validation | 09, 10, 17, 25 |
| Diagnostics | 16, 27 |
| System Management | 18, 19, 21, 24 |
| Automation / Regression | 22, 23, 26, 30 |
| Perception | 13, 14, 29 |
| Monitoring | 11, 20, 28 |
