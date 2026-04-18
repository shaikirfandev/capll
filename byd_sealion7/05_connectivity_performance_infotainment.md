# BYD Sealion 7 — Connectivity, Performance & Infotainment
## Smart Features | Powertrain Specs | Thermal | HMI | UX

---

## 1. Connectivity Architecture

### Telematics Stack

```
Vehicle (TCU)
     │ 4G LTE Category 4 (20 Mbps DL / 50 Mbps UL)
     │ Fallback: 3G / 2G
     │ TLS 1.3 over cellular
     ↓
BYD Cloud (DiLink Cloud Platform)
     ├── Remote monitoring API
     ├── OTA server
     ├── Fleet data aggregation
     ├── Map tile server (HERE/Baidu)
     └── Voice assistant backend (NLU/NLP)
     ↓
BYD App (iOS / Android)
```

### Wireless Interfaces in Vehicle

| Interface | Standard | Use |
|-----------|----------|-----|
| 4G LTE | 3GPP Cat-4 | Cloud services, OTA, remote control |
| Wi-Fi | IEEE 802.11ac (5GHz + 2.4GHz) | In-cabin hotspot, large OTA downloads |
| Bluetooth | BLE 5.0 + Classic BT | Phone-as-key, audio streaming, HandsFreeProfile |
| NFC | ISO 14443 | Digital key (phone tap to unlock) |
| USB | USB 3.0 × 2, USB-C | CarPlay/Android Auto wired, device charging |
| GPS | GPS + BeiDou + GLONASS + Galileo | Multi-constellation GNSS |

---

## 2. BYD App — Remote Functions

| Function | Description | Latency |
|----------|-------------|---------|
| Remote lock/unlock | Door lock via app | < 3s (cloud round-trip) |
| Climate pre-conditioning | Start HVAC before entering | < 5s |
| Charging schedule | Set departure time, off-peak charging | Immediate |
| Battery status | SOC, remaining range, charging ETA | Real-time push |
| Remote parking (RPA) | Move car in/out of tight space via app | Low-latency BT needed |
| Locate vehicle | GPS position on map | Real-time |
| Trip history | Energy consumption per trip | Cloud stored |
| Fault alerts | DTC notification to owner | Push notification |
| OTA consent | Approve/schedule software updates | Interactive |

---

## 3. V2X Capabilities

| Market | V2X Technology | Notes |
|--------|---------------|-------|
| China | **C-V2X (LTE-V, PC5 sidelink)** | Mandatory in new models from 2025 per MIIT |
| Europe | **ITS-G5 (802.11p) / C-V2X 5G NR** | Optional, available via Qualcomm 9150 C-V2X chip in TCU |

**V2X use cases on Sealion 7:**
- V2I: Traffic signal phase + timing (SPAT/MAP) → ACC pre-deceleration at red lights
- V2V: Emergency vehicle approaching alert
- V2I: Road hazard warning (slippery road ahead, accident)
- V2N: Cloud-based hazard sharing

---

## 4. Voice Assistant & AI Features

### DiLink Voice Assistant (DiPilot AI)

```
Wake word: "Hi BYD" (customizable)

NLU pipeline:
  Microphone array (6-mic beamforming) → AEC (echo cancellation)
  → Wake word detection (on-device, TFLite model)
  → ASR (speech-to-text): On-device hybrid + cloud
  → NLU intent parsing
  → Vehicle API / InfoCard response

Examples:
  "Hi BYD, set temperature to 22 degrees" → HVAC setpoint command
  "Hi BYD, navigate to the nearest charging station" → Maps + Routing
  "Hi BYD, turn on seat heating" → BCM LIN seat module
  "Hi BYD, what's my battery level?" → BMS SOC query
```

---

## 5. Performance Specifications

### RWD Version

| Parameter | Value |
|-----------|-------|
| Motor | Rear PMSM, 230 kW, 360 Nm |
| 0–100 km/h | 6.7 seconds |
| Top speed | 215 km/h |
| WLTP range | 482 km (82.56 kWh) |
| Battery | 82.56 kWh (Blade Battery, LFP) |
| DC fast charge | 150 kW CCS2, 10–80% in ~28 min |
| AC charging | 11 kW 3-phase |

### AWD Version

| Parameter | Value |
|-----------|-------|
| Front motor | PMSM, 160 kW, 310 Nm |
| Rear motor | PMSM, 230 kW, 360 Nm |
| Combined power | 390 kW (523 hp) |
| Combined torque | 670 Nm |
| 0–100 km/h | **4.5 seconds** |
| Top speed | 230 km/h |
| WLTP range (AWD) | ~456 km |

---

## 6. Regenerative Braking Strategy

```
Regen strategy (driver selectable + automatic):

Level 0 (OFF):  Creep enabled, no regen — normal ICE feel
Level 1 (LOW):  Regen starts 0.05g on lift-off
Level 2 (MED):  0.10g on lift-off (default)
Level 3 (HIGH): 0.15g on lift-off — strong single-pedal tendency
Auto (iBooster): 
  AEB: max regen first (0.3g), then friction brake (up to 1.0g)
  blend is transparent to driver — no pedal pulsation

Hardware:
  MCU reports regen capability to VCU (current battery SOC, temp limits)
  If SOC > 98% or battery temp < 5°C → regen limited by BMS
  iBooster compensates with friction braking to match requested deceleration

Regeneration efficiency:
  Typical real-world: 15–22% energy recovery on city driving cycle
  Highway: 8–12% (less braking)
```

---

## 7. Infotainment & HMI

### Display Configuration

```
Instrument cluster (10.25" TFT):
  ├── Speed (digital, large format)
  ├── Power gauge (kW output / regen bar)
  ├── Battery SOC + estimated range
  ├── ADAS status icons (ACC following, LKA active)
  ├── Navigation mini-map (from head unit via Ethernet)
  ├── DMS status indicator
  └── Warning / tell-tale icons

Central touchscreen (12.3" standard, 15.6" in Performance trim):
  ├── Android Automotive launcher (BYD DiLink skin)
  ├── Climate control (persistent bottom bar)
  ├── Media (Spotify, Tidal, built-in apps)
  ├── Navigation (Baidu/HERE)
  ├── Vehicle settings (suspension, lights, ADAS thresholds)
  ├── Energy flow animation (live power flow diagram)
  └── Charging screen (SOC curve, cost estimate)
```

### HMI Design Principles

1. **Safety-critical info always visible:** Speed, ADAS state, battery on cluster — never hidden by infotainment
2. **One-touch HVAC access:** Temperature bar persistent on central screen bottom
3. **Glanceability:** Key functions reachable in ≤ 2 taps
4. **Night mode:** Auto-dimming with ambient light sensor, warm tones for night driving

### Android Auto / Apple CarPlay

| Feature | Details |
|---------|---------|
| Wired | USB-C (USB 2.0 protocol) |
| Wireless | Wi-Fi Direct + Bluetooth handshake (2.4 GHz) |
| Screen mirroring | Full central screen |
| Voice integration | Siri / Google Assistant active |
| Availability | Standard on all Sealion 7 markets except CN (China uses DiLink native) |

---

## 8. Audio System

| Specification | Standard | Optional |
|---------------|----------|---------|
| Speakers | 8-speaker system | Dynaudio Premium 12-speaker |
| Subwoofer | Yes (rear shelf) | Yes |
| Amplifier | Digital Class-D | Dynaudio DSP amplifier |
| Audio quality | Dolby Atmos support | Dynaudio concert mode |
| ANC | Active Noise Cancellation (cabin microphones) | Standard |

---

## 9. Energy Management Strategy

### Range Optimization Logic (VCU)

```
Driver inputs:
  Eco mode: 
    Max motor torque limited → 60%
    Climate power limited → 2 kW
    Regen level forced to Level 2
    Speed soft limit: 110 km/h

  Sport mode:
    No torque limit
    Traction control thresholds loosened
    Regen Level 1 (sporty feel)
    Immediate AWD torque vectoring engagement

Energy consumption display:
  Realtime kWh/100km gauge on cluster
  Regeneration meter (green bar below speed)
  Rolling 5km average energy displayed
  Route-based range prediction (GPS + elevation data)
```
