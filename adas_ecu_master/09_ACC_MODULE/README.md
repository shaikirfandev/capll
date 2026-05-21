# 09 — Adaptive Cruise Control (ACC) Module

> **Standard:** SAE J3016 (Automation Level 1–2), ISO 22179 (ACC full-speed range)  
> **Hardware:** Bosch LRR5 / Continental ARS540 radar + ADAS ECU

---

## 9.1 ACC System Architecture

```
SENSORS:
  - Front radar (77 GHz): distance, relative speed, azimuth angle
    Range: 0–250m, accuracy: ±0.1m distance, ±0.1 m/s speed
  - Optional: camera fusion for target classification

PROCESSING (ADAS ECU, 20ms cycle):
  - Radar object tracking (up to 32 objects)
  - In-path target selection (azimuth filter ±5°)
  - Safe following distance calculation (time-gap model)
  - Dual PID: speed controller + gap controller
  - State machine: INACTIVE → SPEED_CONTROL → FOLLOWING → BRAKING → OVERRIDE

OUTPUTS:
  - Throttle request → Engine ECU / Motor controller (EV)
  - Brake request    → ESC/ABS (Electronic Stability Control)
  - Dashboard display: set speed, actual gap, ACC status icon
```

---

## 9.2 Target Selection Algorithm

```
Radar returns up to 32 detected objects.
ACC selects "Most Relevant Object (MRO)":

1. In-path filter: |azimuth| < 5.0° (forward-facing cone)
2. Closest distance in front (distance > 0)
3. Rejection criteria:
   - Oncoming vehicles (relative speed > +5 m/s = moving away fast)
   - Stationary objects below threshold (traffic signs, guard rails)
     → requires camera fusion or map data to distinguish

Cut-in scenario (most dangerous):
  New vehicle appears at < 30m from adjacent lane
  ACC must react within 200ms (sensor fusion cycle: 50ms + 3 radar cycles)
  Response: immediate gap PID activation, smooth deceleration

Cut-out scenario:
  Lead vehicle leaves path → ACC transitions to SPEED_CONTROL
  Acceleration: comfort limit 1.5 m/s² (avoids passenger discomfort)
```

---

## 9.3 Time-Gap Model (Following Distance)

```
Desired gap = v_ego × time_gap_setting

  time_gap_setting = 1.0s, 1.5s, 2.0s, 2.5s, 3.0s (driver selectable)
  Default: 2.0s (recommended by EURO NCAP)

Example at 120 km/h (33.3 m/s):
  time_gap = 2.0s → desired gap = 33.3 × 2.0 = 66.6m

Gap error term:
  error = (current_gap - desired_gap) + (relative_speed × 0.5)
  
  The relative_speed term (closing term) provides early reaction:
  If lead is braking hard (-5 m/s relative), error is reduced by 2.5m → ACC
  starts decelerating earlier than pure gap would indicate.

Emergency braking:
  If gap < 50% of desired gap → transition to BRAKING state
  Deceleration capped at -3.5 m/s² (comfort limit)
  AEB (Autonomous Emergency Braking) handles -8 m/s² to -9.8 m/s² — separate function
```

---

## 9.4 Dual PID Control Architecture

```
SPEED_CONTROL state:
  speedError = setSpeed - egoSpeed
  accel_cmd  = PID_speed(speedError)
  Gains: Kp=1.2, Ki=0.1, Kd=0.08
  Limits: [-3.5, +2.0] m/s²

FOLLOWING state:
  gapError   = (currentGap - desiredGap) + (relSpeed × 0.5)
  accel_cmd  = PID_gap(gapError)
  Gains: Kp=0.5, Ki=0.05, Kd=0.1
  Limits: [-4.0, +2.0] m/s²
  
  Set speed cap: accel_cmd = min(accel_cmd, speedPID_output)
  → ACC never exceeds set speed even when following gap is large

Actuator mapping:
  If accel_cmd > 0: throttle = accel_cmd / 2.0, brake = 0
  If accel_cmd < 0: brake = -accel_cmd / 4.0, throttle = 0
  (Maps normalized to 0..1 range for CAN output signals)
```

---

## 9.5 CAN Interface

```
ACC READS:
  BCM_Status (0x100):     VehicleSpeed (ego speed)
  Radar_Objects (0x5xx):  TargetDistance, TargetRelSpeed, TargetAzimuth × N objects
  Driver_Input (0x110):   ACCEnableButton, SetSpeedButton, TimeGapButton, BrakePedal

ACC WRITES:
  ADAS_ACC_Cmd (0x310):   ThrottleRequest (0..100%), BrakeRequest (0..100%), 
                           AccActiveFlag, AccState, SetSpeedDisplay
  Cluster_ACC (0x410):    SetSpeedKph, ActualGapM, ACCIcon, WarningLamp
```

---

## 9.6 Interview Questions

```
L1:
  Q: What is the difference between Cruise Control (CC) and ACC?
  A: Classic CC: maintains fixed driver-set speed. No radar. Driver must brake manually
     when approaching traffic.
     ACC: adds radar/camera. Automatically adjusts speed to maintain safe gap to lead
     vehicle. Below ~30 km/h some ACC systems stop (full-speed range ACC = FSRA
     continues to standstill and can auto-resume).
     ACC is SAE Level 1 automation (longitudinal control only, driver monitors laterally).

  Q: What happens when the lead vehicle brakes suddenly?
  A: ACC detects increased closing rate (relative speed becomes more negative).
     Gap PID error grows rapidly → ACC requests deceleration.
     If gap drops below 50% of desired: ACC transitions to BRAKING state, requests
     maximum comfort deceleration (~-3.5 m/s²).
     If even harder braking needed → AEB (separate function) intervenes.
     If driver applies brake: OVERRIDE state, ACC releases throttle/brake control.

L2:
  Q: How do you handle radar ghost objects (false positives)?
  A: 1. Object persistence filter: object must be detected in N consecutive radar cycles
        (typically 3 cycles × 50ms = 150ms) before ACC acts on it.
     2. Confidence score threshold: radar returns object probability score.
        Only objects with probability > 80% are used.
     3. Camera fusion: cross-check radar objects with camera classification.
        If camera does not see a vehicle where radar detects one → reject.
     4. Azimuth consistency: object azimuth should not change > 2°/cycle for valid target.

  Q: How is ACC tested in HIL?
  A: Hardware-in-the-Loop: Real ADAS ECU connected to simulated radar (radar model
     in dSPACE SCALEXIO), simulated vehicle dynamics (CarMaker), simulated CAN bus.
     Test scenarios:
     - ACC07: Cut-in scenario at 5m gap
     - ACC08: Lead vehicle emergency brake from 120 km/h
     - ACC15: Stationary vehicle on highway
     Injected failure: radar timeout → verify ACC transitions to INACTIVE safely.

L3:
  Q: Describe the safety requirements for ACC at ASIL level.
  A: ACC controls longitudinal vehicle motion (acceleration + braking) on public roads.
     ISO 26262 HARA for ACC:
     Hazard 1: "Unintended acceleration when lead vehicle is stationary"
       Severity: S3, Exposure: E4, Controllability: C1 → ASIL D
       Safety goal: ACC shall not command positive throttle when object gap < 10m
       Safety mechanism: Independent monitoring in ESC ECU: if ESC detects ACC commands
       throttle while brake pressure > 5 bar → reject command

     Hazard 2: "Missed deceleration when closing on stationary obstacle"
       → AEB handles this (ASIL D), ACC is supplementary
     
     ASIL decomposition:
       ASIL D can be decomposed into ASIL B (D) + ASIL B (D)
       = ACC ECU (ASIL B) + ESC/AEB ECU (ASIL B) — independent channels
     
     Development requirements at ASIL D:
       - 100% MC/DC coverage for safety code
       - Independent safety analysis (FMEA + FTA)
       - Software unit tests with boundary value analysis
       - Independence of tester from developer
```
