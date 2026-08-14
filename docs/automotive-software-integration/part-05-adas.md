# Part 5 — ADAS Integration

ADAS (Advanced Driver Assistance Systems) integration involves combining sensors, ECUs, and actuators to implement safety and convenience features.

---

## 5.1 ADAS Architecture

```
+-----------------------------------------------------------+
|                  ADAS DOMAIN CONTROLLER                   |
|                                                           |
|  +----------+  +----------+  +----------+  +-----------+ |
|  |Perception|  |  Sensor  |  | Planning |  |  Control  | |
|  | Module   |  |  Fusion  |  | Module   |  |  Module   | |
|  +----------+  +----------+  +----------+  +-----------+ |
|                                                           |
|  Interfaces: CSI-2 (camera), Ethernet, CAN FD, PCIe      |
+-----------------------------------------------------------+
         |              |              |              |
    Camera ECU    Radar ECU      LiDAR ECU       GNSS/IMU
```

### ADAS ECU Types

| ECU | Function |
|---|---|
| ADAS Domain Controller | Centralized perception, fusion, planning, control |
| Camera ECU (front/rear/surround) | Image capture, ISP, optional pre-processing |
| Radar ECU (front/corner) | Object detection, velocity measurement |
| LiDAR ECU | 3D point cloud, precise distance |
| Ultrasonic ECU | Close-range parking assistance |
| GNSS/IMU ECU | Position, heading, acceleration |

---

## 5.2 Sensors

### Camera
- Types: Monocular, stereo, fisheye, surround-view
- Interface: MIPI CSI-2 (short range), Automotive Ethernet (FPD-Link, GMSL2)
- Data: Raw Bayer frames, YUV, compressed H.264/H.265
- Integration: Camera driver → Image Signal Processor (ISP) → perception app

### Radar
- Types: Short-range (SRR), Medium-range (MRR), Long-range (LRR)
- Interface: CAN FD or Ethernet
- Data: Object list (distance, velocity, azimuth, RCS)
- Integration: Radar driver → radar middleware → fusion layer

### LiDAR
- Interface: Ethernet (UDP)
- Data: 3D point cloud, range, intensity
- Integration: LiDAR driver → point cloud processing → fusion

### Ultrasonic
- Interface: LIN or DSI3 bus
- Data: Distance in cm
- Integration: Ultrasonic driver → parking logic

### GNSS (GPS/GLONASS/Galileo/BeiDou)
- Interface: UART/SPI, or Ethernet (NMEA or binary protocol)
- Data: Latitude, longitude, altitude, speed, heading, accuracy
- Integration: GNSS driver → localization module

### IMU (Inertial Measurement Unit)
- Interface: SPI or CAN FD
- Data: Accelerations (3-axis), angular rates (3-axis)
- Integration: IMU driver → dead reckoning, sensor fusion

### Wheel Speed Sensors
- Interface: CAN (ABS ECU provides wheel speed signals)
- Data: Wheel speed per wheel (rpm or km/h)
- Integration: Read CAN signal from ABS ECU → odometry

---

## 5.3 ADAS Features

| Feature | Acronym | Description |
|---|---|---|
| Adaptive Cruise Control | ACC | Maintains safe distance to vehicle ahead |
| Automatic Emergency Braking | AEB | Applies brakes to avoid collision |
| Forward Collision Warning | FCW | Warns driver of impending collision |
| Lane Keeping Assist | LKA | Steers vehicle to keep within lane |
| Lane Centering Assist | LCA | Centers vehicle in lane |
| Lane Departure Warning | LDW | Warns when vehicle drifts from lane |
| Traffic Sign Recognition | TSR | Reads speed limit, stop signs |
| Blind Spot Detection | BSD | Monitors adjacent lanes |
| Parking Assist | PA | Guides parking maneuver |
| Highway Assist | HWA | Combined ACC + LCA for highway |
| Driver Monitoring System | DMS | Monitors driver attention/drowsiness |
| Surround View Monitor | SVM | 360° camera view for parking |
| Automated Parking | APS | Fully automated parking |

---

## 5.4 Full ADAS Pipeline

```
Sensor Data Input
     |
     v
+------------+     +------------+     +------------+
|  Sensor    |     |  Sensor    |     |  Sensor    |
|  Drivers   |     |  Drivers   |     |  Drivers   |
| (Camera,   |     | (Radar,    |     | (LiDAR,    |
|  ISP)      |     |  Fusion)   |     |  Point Cld)|
+------------+     +------------+     +------------+
     |                   |                   |
     v                   v                   v
+---------------------------------------------------+
|              PERCEPTION MODULE                    |
|  Object Detection (CNN) | Lane Detection          |
|  Pedestrian Detection   | Traffic Sign Reading    |
+---------------------------------------------------+
                           |
                           v
+---------------------------------------------------+
|              SENSOR FUSION MODULE                 |
|  Fuse camera + radar + LiDAR object lists         |
|  Common coordinate frame (vehicle coordinates)   |
|  Object tracking (Kalman filter, EKF)             |
+---------------------------------------------------+
                           |
                           v
+---------------------------------------------------+
|              ENVIRONMENT MODEL                    |
|  Object List: ID, type, position, velocity       |
|  Lane model, map fusion, occupancy grid           |
+---------------------------------------------------+
                           |
                           v
+---------------------------------------------------+
|              PLANNING MODULE                      |
|  Collision risk assessment | trajectory planning  |
|  ACC setpoint | AEB trigger | LKA steering angle  |
+---------------------------------------------------+
                           |
                           v
+---------------------------------------------------+
|              CONTROL / ACTUATOR INTERFACE         |
|  Brake request → CAN FD → Brake ECU (ESC)        |
|  Steering angle → CAN FD → EPS ECU               |
|  Throttle request → CAN → Engine ECU             |
+---------------------------------------------------+
```

---

## 5.5 Sensor-to-ECU-to-Actuator Integration

### Camera Integration Example

```
Hardware path:
  Camera sensor (ISX031C) → FPD-Link III serializer → Automotive Ethernet PHY
                          → ADAS ECU deserializer → CSI-2 receiver → ISP

Software path:
  Camera Driver (V4L2 in Linux) → frame buffer → Camera HAL
                                → Perception application (OpenCV, TensorRT)
```

### Timestamp Synchronization

All sensors must be timestamped in a common time domain for sensor fusion:
- Use **IEEE 802.1AS (gPTP)** for Ethernet-connected sensors
- Trigger cameras via hardware sync signal (GPIO)
- IMU data associated with trigger timestamps
- GNSS PPS (pulse-per-second) used as grandmaster clock

```
GNSS PPS signal → gPTP grandmaster → all Ethernet nodes synchronized
Camera hardware trigger → all cameras capture same frame timestamp
Radar CAN message timestamp → aligned to gPTP time domain
```

### Coordinate Systems

All sensors report data in their local coordinate frames. Fusion requires transformation to **vehicle coordinate frame** (ISO 8855):
- X: forward
- Y: left
- Z: up

Transformation uses **sensor mounting position and orientation** (calibration data):

```
Object in camera frame → rotation matrix × translation → vehicle frame
Object in radar frame → rotation matrix × translation → vehicle frame
Fused object: average or weighted position in vehicle frame
```

---

## 5.6 Ethernet / SOME/IP / CAN FD Integration for ADAS

### Typical ADAS Network

```
ADAS Domain Controller
  |-- 1000BASE-T1 Ethernet → Central Gateway
  |-- CSI-2 → Front Camera
  |-- 100BASE-T1 Ethernet → Radar (corner radar × 4)
  |-- PCIe / Ethernet → LiDAR
  |-- CAN FD → Brake ECU (AEB actuator)
  |-- CAN FD → EPS ECU (LKA actuator)
```

### Bandwidth Calculation Example

```
Front camera (1920×1080 @ 30fps, raw Bayer 12-bit):
  1920 × 1080 × 30 × 12 bits = ~750 Mbps raw
  With H.264 compression (10:1): ~75 Mbps
  → Use 100BASE-T1 per camera

4 corner radars (object list, CAN FD, 1ms period):
  ~100 bytes × 1000/s = ~0.8 Mbps total → CAN FD sufficient
```

### SOME/IP Integration for ADAS

```
// ADAS Domain Controller offers ObjectListService
Service: ObjectListService
  Event: PublishObjectList (10ms periodic)
  Payload: [{id, type, x, y, vx, vy, confidence}...]

Cluster subscribes to ObjectListService → shows ADAS visualization
Brake ECU subscribes via gateway to AEB_BrakeRequest service
```

### Latency Budget

```
ADAS system latency budget (AEB example):
  Camera capture to frame available:   5ms
  Perception (object detection):      15ms
  Sensor fusion:                       5ms
  Planning (AEB decision):             3ms
  CAN FD message to Brake ECU:         2ms
  Brake ECU actuation:                 5ms
  ----------------------------------------
  Total end-to-end:                   35ms
  System requirement:                 <200ms  ✓
```

---

## 5.7 Calibration

Sensors must be calibrated after mounting to determine their exact position and orientation relative to the vehicle coordinate frame.

**Intrinsic calibration** — internal camera parameters (focal length, distortion)
**Extrinsic calibration** — sensor mounting position/angle relative to vehicle

Calibration data is stored in ECU non-volatile memory (NvM/EEPROM) and used by the fusion algorithm.

---

## 5.8 Failure Handling in ADAS

| Failure | Behavior |
|---|---|
| Camera signal lost | Disable camera-dependent features (LKA, AEB-visual); alert driver; set DTC |
| Radar signal lost | Disable radar-dependent features (ACC, BSD); alert driver |
| ADAS ECU crash | System falls back to driver control; set DTC; illuminate warning |
| Timestamp out of sync | Sensor data rejected by fusion; fallback to available sensors |
| Actuator unavailable (EPS) | LKA disabled; alert driver |

---

## 5.9 ADAS Integration Case Study — AEB

**Objective:** Integrate and validate AEB feature on test vehicle.

**Architecture:**
```
Front Camera → ADAS DC → AEB Decision → CAN FD → Brake ECU
Front Radar  → ADAS DC (sensor fusion)
```

**Integration Sequence:**
1. Hardware bring-up: verify camera/radar communication on bench
2. Software bring-up: load ADAS application on domain controller
3. SOME/IP-SD: verify ObjectListService offered and subscribed by Brake ECU
4. Network integration: verify CAN FD AEB_BrakeRequest signal
5. HIL simulation: inject pedestrian object at T-100ms, verify brake command
6. Vehicle test: closed-course test at 30 km/h toward static object
7. Verify: brake activated before impact, DTC clear, no false triggers

**Common Defects Found:**
- Camera timestamps not synchronized → fusion object jitter → false AEB
  Fix: Enable gPTP on camera Ethernet interface
- AEB triggered on parked vehicles at low speed
  Fix: Tune confidence threshold for stationary objects
- Brake ECU timeout on CAN FD
  Fix: Increase CAN FD watchdog timeout from 50ms to 100ms

---

## Summary

| Component | Interface | Key Integration Points |
|---|---|---|
| Front Camera | CSI-2 / Ethernet | Driver, ISP, timestamp sync |
| Radar | CAN FD / Ethernet | Object list parsing, coordinate transform |
| LiDAR | Ethernet UDP | Point cloud filtering, fusion |
| ADAS DC | CAN FD + Ethernet | Sensor fusion, planning, actuator interface |
| Brake ECU | CAN FD | AEB request signal, watchdog |
| EPS ECU | CAN FD | LKA steering angle request |

---

*Next: [Part 6 — Infotainment Integration](part-06-infotainment.md)*
