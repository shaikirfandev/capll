# 05 — ADAS Basics

> **Level:** L0 Foundation — Read this before any feature module  
> **Purpose:** Understand the full ADAS system context your ECU code lives in

---

## 5.1 SAE Automation Levels

| Level | Name              | Who drives?      | Feature examples           | Market availability |
|-------|-------------------|-----------------|----------------------------|---------------------|
| L0    | No Automation     | Human always    | Forward collision warning   | Standard 2010+      |
| L1    | Driver Assist     | Human + 1 axis  | ACC (longitudinal) or LKA  | Standard 2015+      |
| L2    | Partial Automation| Human supervises| ACC + LKA combined (HWA)   | Tesla Autopilot 2016|
| L2+   | Supervised L2     | Human watching  | ProPilot, Super Cruise      | 2020+               |
| L3    | Conditional Auto  | System drives, human standby | Traffic Jam Chauffeur | Audi A8 2018 |
| L4    | High Automation   | System drives in ODD | Robotaxi (Waymo)      | 2022+ limited       |
| L5    | Full Automation   | No human needed | All roads, all conditions   | Research only       |

```
Key distinction:
  L2: driver always monitors (hands-on or eyes-on)
  L3: driver can look away, must re-engage within N seconds when requested
  L4: system handles ALL scenarios within defined ODD (Operational Design Domain)
```

---

## 5.2 ADAS Sensor Types

### Camera (Visible Light)
```
Usage: Lane detection (LKA/LDA), traffic sign recognition, pedestrian detection
Resolution: 1–8 Megapixel (mono or stereo)
FPS: 30–60 Hz (ADAS), up to 120 Hz (high-speed scenarios)
FOV: Forward (52°, 60°, 120°), surround (190°)
Strengths: colour, texture, fine detail, classification
Weaknesses: rain/fog/night, no direct depth measurement

ECU interface: MIPI CSI-2, LVDS, or Ethernet (GMSL2)
Processing: Image signal processor (ISP) + CNN inference on dedicated chip (TDA4VM)
```

### Radar (77 GHz)
```
Usage: ACC, AEB, blind spot detection
Frequency: 76–77 GHz (long-range), 77–81 GHz (short-range)
Range: Short-range 0–30m, Long-range 30–250m
Velocity: ±70 m/s (FMCW Doppler)
Azimuth resolution: 1–2° (modern MIMO radar)
Strengths: direct range AND velocity measurement, works in all weather
Weaknesses: limited lateral resolution, ghost targets, cannot classify

ECU interface: CAN FD or Ethernet (SOME/IP) for processed object list
```

### LiDAR (905nm / 1550nm)
```
Usage: L3+ mapping, precise 3D point cloud, pedestrian shape detection
Range: 0–200m (typical production LiDAR)
Points per second: 1–4 million
Strengths: precise 3D, long range, shape recognition
Weaknesses: expensive (~$500–5000), snow/fog scatter, no velocity (without Doppler)

Typical: Velodyne VLP-32, Luminar Iris (1550nm), Valeo SCALA
ECU interface: Ethernet UDP (raw point cloud), or processed object list
```

### Ultrasonic (40–70 kHz)
```
Usage: Parking sensors, low-speed object detection (< 5 m/s)
Range: 0.1–5m
Strengths: very cheap, omnidirectional, works in any weather
Weaknesses: short range, no velocity measurement, cross-talk between sensors

ECU interface: LIN bus (SAE J2602), direct GPIO on parking PDC ECU
```

---

## 5.3 ADAS Perception Pipeline

```
┌──────────────┐   Raw data    ┌─────────────────┐  Object list  ┌─────────────────────┐
│   Sensors    │──────────────►│  Pre-processing  │──────────────►│  Sensor Fusion &    │
│ Camera/Radar │               │  (ISP, FFT,      │               │  Object Tracking    │
│ LiDAR/Ultra  │               │   filtering)     │               │  (Kalman Filter)    │
└──────────────┘               └─────────────────┘               └──────────┬──────────┘
                                                                              │ Fused World Model
                                                                              ▼
                                                               ┌─────────────────────────┐
                                                               │   Path Planning /        │
                                                               │   Situation Analysis     │
                                                               │   (prediction 3–5s)      │
                                                               └──────────┬──────────────┘
                                                                          │ Decision
                                                                          ▼
                                                          ┌───────────────────────────────┐
                                                          │   Motion Control              │
                                                          │   (ACC PID, LKA PID,         │
                                                          │    AEB deceleration profile) │
                                                          └───────────────────────────────┘
```

---

## 5.4 Key ADAS Features Map

| Feature | Abbr | Sensor(s)           | Actuator(s)       | ASIL | L-level |
|---------|------|---------------------|-------------------|------|---------|
| Lane Keep Assist | LKA | Camera | EPS | C | L1 |
| Lane Departure Alert | LDA | Camera | Haptic/Acoustic | A | L0 |
| Adaptive Cruise Control | ACC | Radar | Throttle + Brake | B | L1 |
| Autonomous Emergency Braking | AEB | Radar + Camera | Brake | D | L0-act |
| Traffic Sign Recognition | TSR | Camera | Display | QM | L0 |
| Blind Spot Monitor | BSM | Short-range Radar | Warning lamp | A | L0 |
| Rear Cross Traffic Alert | RCTA | Radar | Warning + Brake | B | L0 |
| Highway Assist | HWA | Camera + Radar | EPS + Throttle + Brake | C | L2 |
| Traffic Jam Assist | TJA | Camera + Radar | Full longitudinal + lateral | D | L3 |

---

## 5.5 ADAS ECU Hardware (Production Examples)

```
Bosch Gen5 ACC ECU:
  MCU: Infineon AURIX TC3xx (TriCore + lockstep safety cores)
  Radar: Integrated 77GHz MIMO (3 TX, 4 RX)
  CAN FD + Ethernet interfaces

TI TDA4VM (used in camera ECUs):
  CPU: ARM Cortex-A72 x2 + Cortex-R5F x6 (safety)
  GPU: Imagination PowerVR
  MMA: Matrix Multiply Accelerator (2 TOPS for CNN)
  RTOS: FreeRTOS (R5F) + Linux (A72)

NXP S32G2 (used in domain ECUs):
  CPU: ARM Cortex-A53 x4 + Cortex-M7 x3
  Network processor: 100BASE-T1 + CAN FD + LIN
  Used in: central domain controllers, gateway ECUs

Nvidia Orin (L4 robotaxi):
  CPU: ARM Cortex-A78AE x12
  GPU: Ampere GPU
  DLA: 254 TOPS
  Safety: ASIL-D certified cores
```

---

## 5.6 Interview Questions

```
L1:
  Q: What is the difference between AEB and ACC braking?
  A: ACC: comfort braking to maintain following gap. Max ~-3.5 m/s². 
     Driver expects smooth deceleration.
     AEB: emergency braking when collision is imminent. Up to -9 m/s² (0.9g).
     No warning required — immediate activation. Different algorithm and ASIL level.
     Both can run on same ECU hardware but are separate software functions.

  Q: What sensors are required for a basic LKA system?
  A: Minimum: single monocular camera + ADAS ECU with lane detection software.
     Camera detects lane markings → outputs lane offset + heading angle.
     ADAS ECU: PID controller → steering torque request → EPS via CAN.
     Optional improvements: stereo camera (depth), radar (environment awareness).

L2:
  Q: Why is sensor fusion needed — why not use just radar or just camera?
  A: Camera: excellent classification, lane detection, sign reading. Cannot measure
     range directly. Poor in fog/night.
     Radar: excellent range + velocity. Cannot classify well. Ghost targets possible.
     LiDAR: precise 3D. Expensive. No velocity without Doppler. Fog scatter issues.
     
     Fusion combines complementary strengths:
     - Camera provides classification (is it a car/pedestrian?)
     - Radar provides precise range + velocity (how far, how fast approaching?)
     - Fused object has: class label + position + velocity → safe for AEB decisions

L3:
  Q: How is the ADAS perception pipeline validated?
  A: Multiple levels:
     Unit test: algorithm unit tests (Kalman filter prediction accuracy)
     SIL (Software-in-the-Loop): recorded camera/radar data replayed against algorithm
     HIL (Hardware-in-the-Loop): sensor models inject data into real ECU hardware
     Closed-loop simulation: CarMaker / IPG scenarios (fog, rain, night driving)
     Open-loop road tests: German Autobahn, parking lots, specific EURO NCAP scenarios
     EURO NCAP scenarios:
       AEB City (CCRs), AEB Interurban (CCRb), Lane Support (LSS1/LSS3)
     Metrics: True Positive Rate, False Positive Rate, reaction time < 600ms
```
