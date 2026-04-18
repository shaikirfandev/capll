# BYD Sealion 7 — ADAS & Autonomous Driving Features
## DiPilot | L2+ | Sensor Fusion | Edge Cases | Failure Handling

---

## 1. Autonomy Level

The BYD Sealion 7 with **DiPilot** delivers **SAE Level 2+** (L2 with hands-on/eyes-on required):
- Driver must remain attentive and keep hands on wheel
- System handles steering + acceleration + braking simultaneously in defined scenarios
- **Not L3** — driver cannot legally disengage attention even in traffic jam assist

Higher-tier **DiPilot+** (available in China, select markets) adds:
- Highway navigation assistance (lane change suggestions)
- Urban driving assist (city streets, lower speeds)
- Still classified L2+ per SAE (regulatory environment requires L2 designation)

---

## 2. ADAS Feature Matrix

| Feature | Acronym | Sensors Used | Speed Range | Notes |
|---------|---------|-------------|-------------|-------|
| Adaptive Cruise Control | ACC | Front radar + camera | 0–150 km/h | Stop-and-Go capable |
| Automatic Emergency Braking | AEB | Front radar + camera | 5–80 km/h (pedestrian) / up to 150 km/h (vehicle) | Euro NCAP 2023 tested |
| Autonomous Emergency Braking - Reverse | AEB-R | Rear radar + rear camera | Reverse < 10 km/h | Detect in reverse path |
| Forward Collision Warning | FCW | Front radar + camera | 5–200 km/h | Audio + visual alert |
| Lane Departure Warning | LDW | Front camera | > 60 km/h | No turn signal detected |
| Lane Keep Assist | LKA | Front camera + EPS | 60–150 km/h | Corrective steering torque |
| Lane Centering / Lane Following Assist | LCA/LFA | Front camera + radar | 60–150 km/h | Active centering in lane |
| Traffic Jam Assist | TJA | Radar + camera | 0–60 km/h | Stop-and-Go with steering |
| Highway Driving Assist | HDA/HWA | Radar + camera + HD map | 60–130 km/h | DiPilot+ only |
| Blind Spot Detection | BSD | Corner radars | > 30 km/h | Warning in mirror |
| Rear Cross Traffic Alert | RCTA | Corner radars | Reversing | Alert when reversing |
| Front Cross Traffic Alert | FCTA | Corner radars | < 10 km/h | Alert at intersections |
| Automatic Parking Assist | APA | Ultrasonic + cameras | < 10 km/h | Parallel + perpendicular |
| Remote Parking | RPA | Ultrasonic + cameras | < 5 km/h | Via smartphone app |
| Intelligent High Beam Control | IHBC | Front camera | Any | Auto high/low beam |
| Traffic Sign Recognition | TSR | Front camera | Any | Speed limit, no overtake |
| Driver Monitoring System | DMS | Interior IR camera | Any | Distraction / drowsiness |
| Door Open Warning | DOW | Corner radars | Any | Cyclist / vehicle approaching |

---

## 3. AEB System Deep Dive

### Decision Chain

```
Input: Front radar + front camera running in parallel

STEP 1 — Object Detection:
  Radar:  Returns (range, azimuth, range_rate, RCS) via Ethernet
  Camera: Returns (class=pedestrian/vehicle/cyclist, bounding_box, confidence)

STEP 2 — Object Fusion (in DCU):
  Associate radar tracks with camera detections using GNN (Global Nearest Neighbor)
  Fused object: position ± 0.3m, velocity ± 0.5 km/h, class confirmed

STEP 3 — Threat Assessment:
  TTC = relative_range / closing_speed
  FCW alarm:    TTC < 2.7s → Audio chime + Red HUD warning
  AEB partial:  TTC < 1.8s → 30% brake pressure
  AEB full:     TTC < 1.2s → Maximum autonomous braking (0.9g)

STEP 4 — Actuator command:
  DCU → iBooster (BBW ECU) via CAN FD: brake pressure request
  DCU → VCU: torque reduction to 0 Nm
  VCU → MCU: regen to maximum
```

### AEB Activation Conditions (AND logic)
```
[ Speed > 5 km/h ] AND
[ Vehicle not reversing ] AND
[ Hazard override not active ] AND
[ Radar + camera both confirm obstacle ] AND
[ Driver not already braking > 0.3g ] AND
[ TTC < threshold ]
→ ACTIVATE AEB
```

---

## 4. Lane Keep Assist — Control Architecture

```
Camera inputs:
  Left lane line: y_L(s) = polynomial fit (3rd order) in vehicle frame
  Right lane line: y_R(s) = polynomial fit
  Lane center: y_c = (y_L + y_R) / 2

Errors (at look-ahead distance d = 20m):
  Lateral error e_lat = vehicle_position - y_c(d)
  Heading error e_hdg = vehicle_heading - lane_heading

LKA controller (MPC / PID):
  δ_cmd = Kp × e_lat + Kd × (de_lat/dt) + K_hdg × e_hdg

EPS overlay:
  T_overlay = min(δ_cmd × K_steer, T_max = 3 Nm)
  → Applied as additive torque to driver steering torque

Safety interlock:
  IF driver_torque > 8 Nm (intent to override) → suppress LKA
  IF lane lines confidence < 60% → deactivate LKA
  IF speed < 60 km/h → deactivate LKA
```

---

## 5. Adaptive Cruise Control (ACC with Stop-and-Go)

```
Modes:
  FOLLOWING:  Track lead vehicle, maintain time-gap T = 1.5–3.0s
                Speed_cmd = Lead_speed - Kp × (gap_actual - gap_desired)
  FREE:       No lead vehicle → maintain set speed
  STOPPING:   TTC < 2s AND speed < 15 km/h → decelerate to stop
  STANDING:   Speed = 0, held by iBooster
  GO:         Lead vehicle moves > 3m → automatic resume

Actuators:
  Accelerate:  VCU torque request → MCU
  Decelerate:  Regenerative (up to 0.3g) → iBooster (friction) up to 1.0g
  Standing:    iBooster maintains brake hold (no EPB needed)
```

---

## 6. Sensor Fusion Techniques

### Camera-Radar Fusion Algorithm

```
Object Association:
  - Radar: outputs object list (range, bearing, velocity) every 50ms
  - Camera: outputs object list (class, 2D bbox, monocular depth) every 33ms

Association gate (Mahalanobis distance):
  d² = (z - Hx)^T × S^-1 × (z - Hx)
  If d² < χ²(p=0.99) → associate; else → new track

Track types:
  Radar-only: position + velocity, no classification
  Camera-only: classification, poor depth
  Fused track: both → best attributes of each sensor
```

### IMM (Interacting Multiple Models) for motion prediction

```
Models running in parallel:
  M1: Constant Velocity (CV) — straight driving
  M2: Constant Turn Rate and Velocity (CTRV) — cornering
  M3: Constant Acceleration (CA) — braking/accelerating

At each step:
  weight_i = likelihood(measurement | model_i) × prior_weight_i
  Fused estimate = Σ(weight_i × state_i)
```

---

## 7. Edge Cases and Failure Handling

### Known Edge Cases

| Scenario | Problem | Mitigation |
|----------|---------|------------|
| Cut-in vehicle | Slow-moving vehicle cuts into lane at close range; radar/camera association lag | Increase monitoring frequency; reduce TTC threshold for lateral objects |
| Stationary object on highway | Radar CFAR may suppress stationary returns; camera detects | Camera-radar fusion required; camera primary for stationary AEB |
| Tunnel entry/exit | Camera overexposed/underexposed for ~200ms | Hysteresis on LKA deactivation; radar-only ACC until camera recovers |
| Sun glare | Front camera blinded by low sun angle | Degrade to radar-only; warn driver LKA unavailable |
| Heavy rain/snow | Radar range reduced; camera blurred | Speed-based threshold reduction; FCW range shortens to 60m |
| White truck against white sky | Camera misses detection; radar detects metal but RCS small | Fused track (camera class "unknown large") triggers AEB at lower TTC |
| Cyclist in parallel | Thin radar cross-section; camera classifies as cyclist | AEB activated based on camera classification alone with lower TTC threshold |

### Graceful Degradation Strategy

```
All sensors healthy: Full DiPilot feature set
│
├── Front radar fault → AEB deactivated, FCW camera-only
│     Driver alert: "AEB Unavailable"
│
├── Front camera fault → LKA/LDW deactivated, AEB radar-only (vehicle only)
│     Driver alert: "Lane Keeping Unavailable"
│
├── DCU power fault (single power rail) → Dual-rail architecture
│     Rail 1 failure → Fall back to Rail 2 (reduced processing)
│     ALL sensor faults → All ADAS deactivated, driver alerted
│
└── EPS fault during LKA → LKA immediately zero torque, driver takes over
      EPS maintains manual steering (no power loss, just no overlay)
```

---

## 8. Automatic Parking Assist (APA)

```
Phase 1 — Space detection (driving past):
  Ultrasonic side sensors + camera measure gap length/depth
  Space valid if: length > vehicle + 1.2m (parallel) or depth > vehicle + 0.6m (perpendicular)

Phase 2 — Path planning:
  Bezier curve or Dubins path from current position to target pose
  Constraints: max steering angle, clearance > 0.3m each side

Phase 3 — Execution:
  Speed: < 5 km/h
  Steering: Full authority (EPS, ±540° wheel)
  Braking: Ultrasonic proximity → automatic stop if < 0.3m to obstacle

Phase 4 — Completion:
  EPB engaged, driver selects Park, system disengages
```

---

## 9. DMS (Driver Monitoring System)

```
Sensor: Near-IR camera (850nm LED illumination) facing driver

Detection:
  - Eye closure rate (PERCLOS metric: > 80% closed over 1 min → drowsy)
  - Gaze direction (forward vs distracted)
  - Head pose estimation (looking away > 3s → alert)

Alerts:
  Level 1 (distracted 3s): Audible chime
  Level 2 (distracted 5s): Haptic seat warning
  Level 3 (drowsy pattern): "Rest Recommended" on cluster
  HDA/TJA: REQUIRED for hands-off tolerance (eyes-on enforcement)
```
