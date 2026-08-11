# Infotainment Python Automation Suite

## Overview
30 Python automation scripts for validating In-Vehicle Infotainment (IVI) systems using `python-can`, `cantools`, and `pytest`. Covers audio volume, media source, Bluetooth, navigation, phone calls, OTA, HMI brightness, steering wheel controls, and full E2E regression.

## Environment Setup
```bash
pip install python-can cantools pytest pytest-html
```

## CAN Interface Configuration
```python
import can
bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
```

## Signal Reference

| CAN ID | Signal Name         | Encoding                                        |
|--------|---------------------|-------------------------------------------------|
| 0x400  | IVI_Volume          | byte0=volume(0-100); byte1=mute(0/1)            |
| 0x401  | IVI_MediaSource     | byte0=source(0=FM,1=AM,2=USB,3=BT,4=AUX,5=CarPlay,6=AndroidAuto) |
| 0x402  | IVI_PowerState      | byte0=state(0=Off,1=Standby,2=On,3=Booting)    |
| 0x403  | IVI_Navigation      | byte0=state(0=Idle,1=Routing,2=Active,3=Arrived); byte1=ETA_min |
| 0x404  | IVI_Bluetooth       | byte0=state(0=Off,1=Discoverable,2=Pairing,3=Connected); byte1=deviceCount |
| 0x405  | IVI_PhoneCall       | byte0=state(0=Idle,1=Ringing,2=Active,3=OnHold); byte1=signalStrength |
| 0x406  | IVI_SteeringCtrl    | byte0=button(0=VolUp,1=VolDown,2=Next,3=Prev,4=Mode,5=Call,6=End,7=Voice) |
| 0x407  | IVI_Brightness      | byte0=level(0-255); byte1=autoMode(0/1)         |
| 0x408  | IVI_OTA             | byte0=status(0=Idle,1=Downloading,2=Installing,3=Complete,4=Failed); byte1=progress |
| 0x409  | IVI_WiFi            | byte0=state(0=Off,1=Connecting,2=Connected); byte1=signalBars(0-5) |
| 0x40A  | IVI_EQ              | byte0=preset(0=Flat,1=Bass,2=Treble,3=Custom)  |
| 0x40B  | IVI_Language        | byte0=lang(0=EN,1=DE,2=FR,3=ZH,4=AR)           |
| 0x40C  | IVI_ClockSync       | byte0-3=unixTimestamp                           |
| 0x40D  | IVI_PrivacyMode     | byte0=mode(0=Off,1=On)                         |
| 0x40E  | IVI_DND             | byte0=enabled(0/1)                             |
| 0x450  | IVI_ECU_Response    | byte0=ackCmd; byte1=result(0=OK,1=Fail,2=Timeout); byte2=data |

## Suite Structure

| Script | Feature Under Test |
|--------|-------------------|
| 01_audio_volume_control.py | Volume 0→50→100, mute/unmute |
| 02_media_source_switch.py | FM/AM/USB/BT/CarPlay/AndroidAuto selection |
| 03_bluetooth_pairing.py | BT discovery, pairing, device count |
| 04_carplay_session.py | CarPlay connect/disconnect session |
| 05_android_auto_session.py | AndroidAuto connect/disconnect |
| 06_navigation_route.py | Route start, ETA update, arrival |
| 07_phone_call_handling.py | Incoming/answer/hold/end states |
| 08_radio_tuning.py | FM preset scan, AM band switch |
| 09_hmi_touchscreen.py | HMI state machine, screen transitions |
| 10_voice_recognition.py | Voice cmd trigger → action |
| 11_display_brightness.py | Dimmer 0→255, AUTO mode |
| 12_screen_mirror.py | Mirror start/stop latency |
| 13_usb_audio.py | USB connect → playback state |
| 14_steering_wheel_controls.py | All 8 SWC button presses |
| 15_equalizer_settings.py | EQ presets Flat/Bass/Treble/Custom |
| 16_infotainment_dtc.py | UDS DTC read/clear on IVI ECU |
| 17_head_unit_boot.py | Boot time measurement <10s |
| 18_privacy_mode.py | Privacy ON/OFF, nav disable verify |
| 19_language_settings.py | Language cycle EN/DE/FR/ZH |
| 20_system_update_ota.py | OTA 0→50→100%, failure rollback |
| 21_power_mode_infotainment.py | IGN off→sleep, IGN on→boot |
| 22_remote_hmi_access.py | Remote access enable/disable |
| 23_do_not_disturb.py | DND on/off, call blocking verify |
| 24_audio_fade_balance.py | Fade front/rear, balance left/right |
| 25_clock_sync.py | Unix timestamp set/verify |
| 26_rear_seat_entertainment.py | RSE zone enable, content routing |
| 27_wifi_hotspot.py | WiFi connect, signal bars 0→5 |
| 28_vehicle_status_display.py | Vehicle data displayed on IVI |
| 29_ambient_lighting_control.py | Ambient RGB, zone control |
| 30_infotainment_e2e_test.py | Boot→Audio→Call→Nav→BT→OTA→Sleep |

## Pass/Fail Criteria
- All timing checks report delta_ms vs threshold
- PASS: assertion passes without exception
- FAIL: `AssertionError` or `TimeoutError` caught and logged
- HTML report generated via `pytest --html=report.html`

## Running
```bash
pytest python_suites/infotainment_python_suite/ -v --html=ivi_report.html
```

`python_suites/infotainment_python_suite/pytest.ini` is configured with
`python_files = [0-9][0-9]_*.py` so two-digit numbered files
(`01_...py`, `02_...py`, etc.) are collected by pytest without collecting
non-test helpers.
