# OEM Issue RCA Catalog

| Issue | First Evidence | Likely Layers | RCA Direction |
| --- | --- | --- | --- |
| Bluetooth disconnects | BT snoop, logcat, phone matrix | profile, RF, state machine | reconnect state and profile conflict |
| Audio lag | audio timestamp, CPU, focus logs | audio HAL, DSP, app | buffer and focus chain |
| CAN timeout | CAN trace, DTC | network, gateway, IVI timeout | missing cyclic frame or debounce mismatch |
| Black screen | boot logs, display service | graphics, power, app | display init and compositor |
| Reverse camera freeze | video capture, gear trace | camera ECU, driver, UI | stale frame and stream reset |
| Navigation crash | tombstone, route steps | app, map, GNSS | reproduction route and memory |
| Touchscreen lag | screen video, CPU | UI thread, input driver | frame timing and main thread block |
| Boot loop | kernel, recovery logs | OTA, filesystem, service crash | rollback and boot reason |
| Sleep current issue | current trace, wake locks | app, kernel, CAN wake | wakelock and wake source |
| OTA corruption | update logs, hash | package, storage, rollback | verification and A/B state |
| Memory leak | meminfo trend | app, native, graphics | heap and cycle correlation |
| Voice assistant failure | mic/audio logs | network, ASR, audio focus | capture path and service state |
