# Part 6 — Infotainment Integration

---

## 6.1 IVI Architecture Overview

IVI (In-Vehicle Infotainment) systems provide entertainment, navigation, connectivity, and vehicle interface for driver and passengers.

```
+------------------------------------------------------+
|                    HMI / Display                     |
|          Touchscreen UI / Voice / Physical Controls  |
+------------------------------------------------------+
|                  APPLICATION LAYER                   |
|  Media | Navigation | Phone | Climate | CarSettings  |
+------------------------------------------------------+
|                  FRAMEWORK LAYER                     |
|  Android Framework / Car Service / Audio Service     |
+------------------------------------------------------+
|                  MIDDLEWARE LAYER                    |
|  Android HAL / Audio HAL / BT Stack / Wi-Fi Stack   |
+------------------------------------------------------+
|                  DRIVER LAYER                        |
|  Display Driver | Audio Codec | BT Chip | Wi-Fi HW  |
+------------------------------------------------------+
|                  HARDWARE                            |
|  SoC (Qualcomm SA8295, NXP i.MX8, Renesas R-Car H3)|
+------------------------------------------------------+
```

---

## 6.2 Android Automotive OS (AAOS)

Android Automotive OS is AOSP (Android Open Source Project) adapted for in-vehicle use:
- Runs natively on the head unit (not tethered to phone like Android Auto)
- Has direct access to vehicle signals via Vehicle HAL
- OEM apps + Google apps (Maps, Play Store, Assistant)

### AAOS Architecture

```
+----------------------------------------------------------+
|  OEM Apps   | Google Maps | Play Store | Voice Assistant |
+----------------------------------------------------------+
|             Android Framework (Java/Kotlin APIs)         |
|    CarService (ICarVehicleCallback, etc.)                |
+----------------------------------------------------------+
|             Android Binder IPC                           |
+----------------------------------------------------------+
|     CarService (car_service.cpp)                         |
|     VehicleHAL Client                                    |
+----------------------------------------------------------+
|     Vehicle HAL (hardware/interfaces/automotive)         |
|     AIDL or HIDL interface                               |
+----------------------------------------------------------+
|     CAN/Ethernet Vehicle Signal Gateway                  |
|     (vhal_canbus_service or custom implementation)       |
+----------------------------------------------------------+
|     CAN Bus / Ethernet (vehicle signals)                 |
+----------------------------------------------------------+
```

### Vehicle HAL (VHAL)

The Vehicle HAL abstracts vehicle signals from Android:
- Vehicle properties: `VEHICLE_SPEED`, `DOOR_LOCK`, `HVAC_TEMPERATURE`, `GEAR_SELECTION`
- Android reads/writes properties via VHAL
- VHAL backend maps to CAN signals or gateway service

```java
// Reading vehicle speed in Android app
CarPropertyManager carPropertyManager = 
    (CarPropertyManager) car.getCarManager(Car.PROPERTY_SERVICE);
float speed = carPropertyManager.getFloatProperty(
    VehiclePropertyIds.PERF_VEHICLE_SPEED, 0);
```

### Car Service
Car Service is an Android system service that:
- Provides APIs for vehicle properties (speed, gear, windows)
- Manages audio focus for in-car audio routing
- Handles voice assistant integration
- Manages multi-zone displays (front + rear)

### Binder IPC
Inter-process communication in Android using Binder mechanism:
- Apps communicate with Car Service via Binder
- Car Service communicates with VHAL via AIDL/HIDL
- Low-latency, secure IPC

---

## 6.3 Audio Integration

### Audio Architecture

```
App → AudioManager (Android) → AudioFlinger → AudioPolicyManager
    → Audio HAL → Audio Codec Driver → Hardware Amplifier → Speakers
```

### Audio HAL
The Audio HAL (defined by AIDL interface) bridges Android Audio to the hardware audio codec. OEM implements the HAL for their specific audio hardware (e.g., TI TAS5827, NXP TFA98xx).

### Automotive Audio Routing
Automotive audio has multiple zones:
- Front zone (driver + front passenger)
- Rear zone (rear passengers with screens)
- System sounds, navigation prompts, media, phone calls

Audio focus management ensures that a navigation prompt can interrupt music.

---

## 6.4 Bluetooth Integration

### BT Stack

```
Android App (BT Profile API)
     ↓
Bluetooth Framework (BluetoothManager, BluetoothAdapter)
     ↓
Bluetooth Stack (Fluoride / BlueDroid)
     ↓
HCI (Host Controller Interface)
     ↓
Bluetooth Chip Driver
     ↓
Bluetooth Chip (e.g., Qualcomm QCA6696, NXP IW612)
```

### Automotive BT Profiles

| Profile | Use |
|---|---|
| HFP (Hands-Free Profile) | Phone calls |
| A2DP (Advanced Audio Distribution) | Music streaming |
| AVRCP (Audio/Video Remote Control) | Media controls |
| PBAP (Phone Book Access) | Contacts sync |
| MAP (Message Access Profile) | SMS on head unit |
| BLE (Bluetooth Low Energy) | Digital key, UWB pairing |

### BT Integration Issues
- Codec negotiation: ensure both phone and HU support same codecs (AAC, aptX, LDAC)
- HFP call audio routing: ensure audio focus correctly routes to phone call
- Pairing on cold boot: verify BT adapter initializes within 3 seconds

---

## 6.5 Wi-Fi Integration

### Wi-Fi Stack

```
App → WifiManager (Android) → WifiService → wpa_supplicant → Wi-Fi Driver → Wi-Fi Chip
```

### Automotive Wi-Fi Use Cases
- Smartphone projection (Android Auto over Wi-Fi, Apple CarPlay wireless)
- Hotspot for passengers
- OTA updates (via TCU Wi-Fi or direct access point)

### Wi-Fi Integration
- Wi-Fi chip firmware loaded by driver at boot
- wpa_supplicant configuration for automotive (enterprise, PSK modes)
- Antenna design critical for automotive EMC

---

## 6.6 USB Integration

### USB Stack

```
App → USB Manager → USB HAL → USB Controller Driver → USB Hardware
```

### Automotive USB Use Cases
- Wired Android Auto / Apple CarPlay
- Media playback from USB flash drive
- Software update via USB flash
- Charging (USB-C Power Delivery)

---

## 6.7 Navigation Integration

### Navigation Stack
- Offline map data stored on eMMC or SD card
- Online routing via embedded modem (TCU)
- OEM navigation (TomTom, HERE) or Google Maps
- Route instructions → text-to-speech engine → audio system
- Map display → GPU → display pipeline

---

## 6.8 Voice Assistant Integration

- Wake word detection (on-device low-power core)
- Audio capture → noise cancellation → beamforming → VAD (Voice Activity Detection)
- Local NLU or cloud-based (Google Assistant, Alexa Auto)
- Response via TTS engine → Audio HAL → speakers
- Vehicle control actions via Car Service VHAL API

---

## 6.9 Yocto-Based Linux IVI

For non-Android IVI systems (e.g., QNX-based or Automotive Linux AGL):
- Yocto Project builds custom Linux image
- BSP layer for SoC (e.g., meta-renesas, meta-nxp)
- Middleware layers (wayland/weston compositor, GStreamer media)
- HMI framework: Qt Automotive Suite, Flutter, React Native

---

## 6.10 IVI Integration Practical Example

**Scenario: Add vehicle speed display to IVI home screen**

```
1. Vehicle speed published on CAN bus by ABS ECU (0x0C9)
2. Gateway ECU bridges CAN to Automotive Ethernet
3. SOME/IP service "VehicleSpeedService" offered by gateway
4. VHAL backend subscribes to VehicleSpeedService
5. VHAL updates VEHICLE_PROPERTY: PERF_VEHICLE_SPEED
6. Car Service notifies registered listeners
7. IVI App: carPropertyManager registers listener for PERF_VEHICLE_SPEED
8. IVI App updates speedometer widget on UI
9. Verify: send CAN message in CANoe → observe speed in IVI UI
```

**Common Integration Issues:**

| Issue | Cause | Fix |
|---|---|---|
| VHAL property not updating | CAN signal not reaching VHAL backend | Verify SOME/IP subscription active |
| Bluetooth audio drops | BT firmware crash | Update BT firmware, check antenna |
| Android booting slowly | Too many autostart services | Profile with systrace, optimize |
| Navigation app crashes | Missing map license | Verify license key in VHAL properties |
| USB Android Auto not working | Missing AOA protocol support | Verify USB gadget mode configuration |

---

## Summary

| Component | Key Integration |
|---|---|
| AAOS / Linux / QNX | OS bring-up, BSP, Yocto |
| VHAL | CAN/Ethernet → Android vehicle properties |
| Audio HAL | Codec driver, routing, focus |
| Bluetooth | Profile support, firmware, pairing |
| Wi-Fi | wpa_supplicant, antenna, EMC |
| Navigation | Map data, connectivity, TTS |
| Voice assistant | Wake word, NLU, car control API |

---

*Next: [Part 7 — Instrument Cluster Integration](part-07-instrument-cluster.md)*
