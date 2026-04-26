# Telematics CAPL Automation Suite
## TCU | GPS | Remote Services | OTA | V2X | Cloud Connectivity Testing

---

## Overview

30 CAPL scripts for validating Telematics Control Unit (TCU) functionality via CAN bus in Vector CANoe. Covers GPS positioning, remote services (lock/unlock/honk), OTA, eCall, geo-fencing, cellular connectivity, V2X, and fleet management.

---

## Suite Structure

```
telematics_capl_suite/
├── README.md
├── 01_tcu_connection_status.capl       – TCU startup, network registration, status
├── 02_gps_position_validation.capl     – GPS fix, position accuracy, HDOP check
├── 03_remote_door_lock.capl            – Remote lock/unlock command + ACK
├── 04_remote_honk_flash.capl           – Remote horn/flash command, timeout, ACK
├── 05_ota_trigger.capl                 – OTA download trigger, progress, install
├── 06_vehicle_tracking.capl            – Position log at intervals, track upload
├── 07_stolen_vehicle_alert.capl        – Intrusion detect, stolen flag, immobilise
├── 08_ecall_emergency.capl             – Manual/auto eCall trigger, MSD transmission
├── 09_roadside_assistance.capl         – RSA call request, location send, cancel
├── 10_cellular_connectivity.capl       – RSSI monitoring, hand-off, reconnect
├── 11_telematics_dtc.capl              – DTC read/clear for TCU via UDS
├── 12_tcu_power_mode.capl              – TCU sleep/wake/KL15/remote wake
├── 13_data_logging_tcu.capl            – Trip data record, buffer flush, upload
├── 14_can_to_cloud_routing.capl        – CAN signals → TCU → cloud forwarding check
├── 15_remote_diagnostics.capl          – Remote UDS session via TCU proxy
├── 16_geo_fencing.capl                 – Virtual boundary entry/exit alert
├── 17_valet_mode.capl                  – Valet mode on/off, speed limit 30 km/h
├── 18_over_speed_alert.capl            – Speed threshold, alert to cloud, clear
├── 19_trip_data_upload.capl            – Trip start/end, odometer, fuel upload
├── 20_tcu_wake_sleep.capl              – Scheduled wake, real-time wake, sleep timer
├── 21_v2x_communication.capl           – BSM broadcast, SPAT receive, RSU message
├── 22_sim_card_monitor.capl            – SIM present, ICCID read, data session
├── 23_tcu_fault_injection.capl         – GPS signal loss, cellular drop, CAN timeout
├── 24_remote_engine_start.capl         – Remote engine start command, safety guards
├── 25_telematics_regression.capl       – Full regression runner for all TCU services
├── 26_tcu_uds_diagnostics.capl         – UDS 0x10/0x22/0x27/0x19/0x14 for TCU
├── 27_fleet_management.capl            – Fleet ID, driver ID, vehicle group signal
├── 28_tcu_can_monitor.capl             – TCU CAN output signal surveillance
├── 29_remote_hvac_control.capl         – Remote A/C pre-condition command + confirm
└── 30_telematics_e2e_test.capl         – Boot→GPS→remote lock→eCall→OTA→sleep
```

---

## Signal Reference

| Signal | Message ID | Description |
|--------|-----------|-------------|
| TCU_Status | 0x600 | 0=Off 1=Initialising 2=Registered 3=Connected |
| GPS_Validity | 0x601 | 0=NoFix 1=2D 2=3D; HDOP byte1 |
| GPS_Lat | 0x602 | Latitude (scaled int32) |
| GPS_Lon | 0x603 | Longitude (scaled int32) |
| RemoteCmd | 0x604 | Remote command code + token |
| RemoteAck | 0x605 | ACK for remote command + status |
| OTA_Status | 0x606 | 0=Idle 1=Downloading 2=Installing 3=Done 4=Failed |
| Cellular_RSSI | 0x607 | Signal strength -113 to -51 dBm (encoded) |
| eCall_Status | 0x608 | 0=Idle 1=Triggered 2=Transmitting 3=Complete |
| TCU_PowerMode | 0x609 | 0=Sleep 1=Standby 2=Active |
| V2X_BSM | 0x610 | Basic Safety Message content |
| GeoFence_Event | 0x611 | 0=Inside 1=Exit 2=Entry alert |
