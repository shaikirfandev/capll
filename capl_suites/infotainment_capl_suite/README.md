# Infotainment CAPL Automation Suite
## Head Unit | Audio | Navigation | Connectivity | HMI Testing

---

## Overview

30 CAPL scripts for validating in-vehicle infotainment (IVI) systems via CAN/CAN FD bus in Vector CANoe. Covers audio management, navigation, Bluetooth/CarPlay/Android Auto, HMI interactions, power modes, and regression testing.

---

## Suite Structure

```
infotainment_capl_suite/
├── README.md
├── 01_audio_volume_control.capl        – Volume step, mute, max limit validation
├── 02_media_source_switch.capl         – AM/FM→USB→BT→CarPlay source switching
├── 03_bluetooth_pairing.capl           – BT device pairing, connection, rejection
├── 04_carplay_session.capl             – Apple CarPlay session init/teardown
├── 05_android_auto_session.capl        – Android Auto connection validation
├── 06_navigation_route.capl            – Route set, guidance, recalculation
├── 07_phone_call_handling.capl         – Incoming/outgoing call, hold, mute, end
├── 08_radio_tuning.capl                – AM/FM seek, preset, RDS, signal quality
├── 09_hmi_touchscreen.capl             – Touch key validation, gesture recognition
├── 10_voice_recognition.capl           – VR wake word, command dispatch, timeout
├── 11_display_brightness.capl          – Ambient light adaptation, manual override
├── 12_screen_mirror.capl               – Rear camera / screen mirroring protocol
├── 13_usb_audio.capl                   – USB device connect/play/skip/eject
├── 14_steering_wheel_controls.capl     – SWC audio/call/voice shortcut validation
├── 15_equalizer_settings.capl          – EQ band persistence, reset, profile set
├── 16_infotainment_dtc.capl            – DTC read/clear for IVI ECU via UDS
├── 17_head_unit_boot.capl              – Boot time, SplashScreen, first-signal validation
├── 18_privacy_mode.capl                – Privacy mode on/off, mic/camera disable
├── 19_language_settings.capl           – Language change, HMI text signal update
├── 20_system_update_ota.capl           – OTA trigger, progress signal, completion
├── 21_power_mode_infotainment.capl     – IGN off→retain→sleep→wake cycle
├── 22_remote_hmi_access.capl           – Remote app connected HMI command routing
├── 23_do_not_disturb.capl              – DND activate, call suppression, calendar sync
├── 24_audio_fade_balance.capl          – Fade/balance range, speaker zones
├── 25_clock_sync.capl                  – GPS time sync, timezone, DST change
├── 26_rear_seat_entertainment.capl     – RSE screen, independent audio zone
├── 27_wifi_hotspot.capl                – Wi-Fi AP start/stop, client connect
├── 28_vehicle_status_display.capl      – Door/fuel/TPMS status on IVI screen
├── 29_ambient_lighting_control.capl    – RGB ambient light zone control, colour change
└── 30_infotainment_e2e_test.capl       – Full IVI sequence: boot→media→nav→call→off
```

---

## Signal Reference

| Signal | Message ID | Description |
|--------|-----------|-------------|
| Audio_Volume | 0x400 | Current volume 0–100 |
| Audio_Source | 0x401 | Active source (0=Radio 1=USB 2=BT 3=CarPlay 4=AA) |
| HU_PowerState | 0x402 | 0=Off 1=Standby 2=On 3=Retain |
| Nav_Guidance | 0x403 | Turn instruction code |
| BT_ConnStatus | 0x404 | BT connection state |
| Call_Status | 0x405 | Call state (0=Idle 1=Ringing 2=Active 3=Hold) |
| SWC_Key | 0x406 | Steering wheel control keycode |
| Display_Brightness | 0x407 | 0–255 brightness value |
| OTA_Progress | 0x408 | OTA download progress % |
| WiFi_ClientCount | 0x409 | Number of connected Wi-Fi clients |
