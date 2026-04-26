# Cluster CAPL Automation Suite
## Instrument Panel Cluster – Gauge, Warning Lamps, Indicators, HMI Testing

---

## Overview

30 CAPL scripts for validating the Instrument Panel Cluster (IPC) / Digital Cluster ECU via CAN bus in Vector CANoe. Covers speedometer, RPM, warning lamps, gear indicator, EV displays, ADAS icon cluster, regression testing, and UDS diagnostics.

---

## Suite Structure

```
cluster_capl_suite/
├── README.md
├── 01_speedometer_accuracy.capl        – Speed signal vs cluster display validation
├── 02_rpm_gauge.capl                   – RPM sweep, redline, idle validation
├── 03_fuel_gauge.capl                  – Fuel level steps, low fuel warning
├── 04_coolant_temp_gauge.capl          – Coolant temp ramp, overheat warning
├── 05_mil_check_engine.capl            – MIL on/off, DTC correlation
├── 06_warning_lamps.capl               – All warning lamp activation/deactivation
├── 07_odometer_tripmeter.capl          – ODO count, trip reset, display rollover
├── 08_trip_computer.capl               – Avg speed, fuel consumption, range display
├── 09_turn_signal_indicator.capl       – Left/right indicator flash rate, hazard
├── 10_park_brake_indicator.capl        – Park brake ON/OFF signal and lamp
├── 11_oil_pressure_warning.capl        – Oil pressure low detection and warning
├── 12_seatbelt_reminder.capl           – Belt unfastened warning, chime logic
├── 13_cluster_brightness.capl          – Dimmer control, AUTO/MANUAL modes
├── 14_cluster_dtc.capl                 – UDS DTC read/clear for Cluster ECU
├── 15_cluster_power_mode.capl          – Power ON/OFF, wake, sleep, retain mode
├── 16_cluster_can_monitor.capl         – Signal cycle time, range, timeout monitor
├── 17_gear_indicator.capl              – P/R/N/D/M gear display, paddle shift
├── 18_range_display.capl               – Fuel range and EV range calculation
├── 19_speed_limit_display.capl         – ISA speed limit shown on cluster
├── 20_adas_icons_cluster.capl          – LKA, ACC, AEB, BSD icons on cluster
├── 21_door_ajar_display.capl           – Door open animation per door
├── 22_tpms_display.capl                – Tyre pressure per wheel, alert threshold
├── 23_instrument_self_test.capl        – Cluster self-test sequence at ignition on
├── 24_cluster_language.capl            – Language/unit change (km/mi, °C/°F)
├── 25_cluster_animation.capl           – Welcome/goodbye animation timing
├── 26_ev_battery_display.capl          – EV SOC%, charging status, power flow bar
├── 27_service_interval_display.capl    – Service due in km/days, reset
├── 28_night_mode_cluster.capl          – Night mode auto switch, ambient sensor
├── 29_cluster_regression.capl          – Full regression runner for all lamp/signals
└── 30_cluster_e2e_test.capl            – IGN ON→self-test→drive sim→warn→IGN OFF
```

---

## Signal Reference

| Signal | Message ID | Description |
|--------|-----------|-------------|
| VehicleSpeed | 0x100 | Speed km/h (from ESP) |
| EngineRPM | 0x101 | Engine RPM |
| FuelLevel | 0x500 | Fuel level 0–255 = 0–100% |
| CoolantTemp | 0x501 | Coolant temp (raw, offset −40) |
| GearPosition | 0x502 | P=0 R=1 N=2 D=3 M=4 |
| OilPressure | 0x503 | Oil pressure kPa |
| ClusterPower | 0x504 | 0=Sleep 1=Standby 2=On |
| WarningLamps | 0x505 | Bitmask of all warning lamps |
| TPMS_Status | 0x506 | Per-wheel pressure + alert |
| EV_SOC | 0x507 | State of charge 0–100% |
| Cluster_DTC | 0x508 | DTC byte high/low |
| Brightness | 0x509 | Dimmer level 0–255 |
