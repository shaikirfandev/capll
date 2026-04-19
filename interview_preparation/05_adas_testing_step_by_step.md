# ADAS Testing — Step-by-Step Signal Injection Guide (CANoe)

> How to test each ADAS feature by injecting signals via CANoe CAPL scripts and the
> Interaction Generator (IG). Each section follows the same structure:
> **Feature overview → CAN signals involved → Preconditions → Injection steps → Pass/Fail criteria → CAPL script**

---

## Table of Contents

1. [ACC — Adaptive Cruise Control](#1-acc--adaptive-cruise-control)
2. [LKA — Lane Keep Assist](#2-lka--lane-keep-assist)
3. [BSD — Blind Spot Detection](#3-bsd--blind-spot-detection)
4. [DMS — Driver Monitoring System](#4-dms--driver-monitoring-system)
5. [APS — Automatic Parking System](#5-aps--automatic-parking-system)
6. [PCW — Pedestrian Collision Warning](#6-pcw--pedestrian-collision-warning)
7. [Cross-Feature Fault Injection Checklist](#7-cross-feature-fault-injection-checklist)
8. [CANoe Setup Checklist (All Features)](#8-canoe-setup-checklist-all-features)

---

## 1. ACC — Adaptive Cruise Control

### What it does
ACC maintains a set speed and a safe following distance to the vehicle ahead by controlling
throttle and braking automatically. Input comes from forward-facing radar + wheel speed sensors.

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `RadarTarget_Distance` | 0x300 | B0-B1 | Distance to lead vehicle (cm) |
| `RadarTarget_RelSpeed` | 0x300 | B2-B3 | Relative speed (signed, km/h × 10) |
| `VehicleSpeed` | 0x200 | B0-B1 | Ego vehicle speed (km/h × 100) |
| `ACC_SetSpeed` | 0x410 | B0-B1 | Driver-set target speed |
| `ACC_Enable` | 0x410 | B2 bit0 | 1 = ACC active |
| `ThrottleRequest` | 0x500 | B0 | ECU output: 0–100% |
| `BrakeRequest_mbar` | 0x501 | B0-B1 | ECU output: brake pressure |

### Preconditions

```
1. CANoe loaded with ADAS ECU DBC + ODX files
2. Simulation setup: ADAS ECU connected (hardware or simulated node)
3. Measurement started
4. Vehicle in Drive (GearPosition = D)
5. VehicleSpeed = 80 km/h (steady state)
```

### Test Cases & Injection Steps

---

#### TC-ACC-01: Normal following — maintain safe distance

```
Step 1: Set ego speed = 80 km/h
  → Write VehicleSpeed signal: 8000 (= 80.00 km/h, factor 0.01)

Step 2: Enable ACC with set speed = 80 km/h
  → Write ACC_Enable = 1
  → Write ACC_SetSpeed = 8000

Step 3: Inject lead vehicle at 50m
  → Write RadarTarget_Distance = 5000 (cm)
  → Write RadarTarget_RelSpeed = 0

Step 4: Slowly decrease distance to 20m (simulate cut-in)
  → Ramp RadarTarget_Distance from 5000 → 2000 over 3 seconds

Expected:
  ✓ ThrottleRequest decreases
  ✓ BrakeRequest_mbar increases (soft deceleration)
  ✓ No DTC logged
  ✓ ACC remains active (no deactivation flag)
```

#### TC-ACC-02: Lead vehicle cut-out (distance jumps to maximum)

```
Step 1: ACC active, lead vehicle at 30m

Step 2: Simulate lead vehicle turning off (no target)
  → Write RadarTarget_Distance = 0xFFFF (invalid / no target)
  → Write RadarTarget_RelSpeed = 0

Expected:
  ✓ ACC accelerates back to set speed
  ✓ ThrottleRequest increases
  ✓ No false braking
```

#### TC-ACC-03: Emergency stop injection — AEB trigger boundary

```
Step 1: ACC active at 80 km/h

Step 2: Inject sudden obstacle at 5m
  → Write RadarTarget_Distance = 500 (cm = 5m)
  → Write RadarTarget_RelSpeed = -3000 (= -30 km/h, approaching fast)

Expected:
  ✓ BrakeRequest rises to maximum within 500ms
  ✓ AEB_Active flag = 1 on CAN ID 0x502
  ✓ DTC NOT logged (this is normal AEB, not a fault)
  ✓ ACC deactivates after stop
```

#### TC-ACC-04: Radar signal timeout (fault injection)

```
Step 1: ACC active, following a lead vehicle

Step 2: STOP sending 0x300 (RadarTarget) — simulate radar failure
  → In CAPL: set sending flag to 0, stop outputting 0x300

Step 3: Wait > 100ms (typical timeout threshold)

Expected:
  ✓ ACC deactivates
  ✓ Warning lamp on cluster (ACCFaultWarning = 1)
  ✓ DTC logged: U0401 or similar radar communication fault
```

### CAPL Script — TC-ACC-04 Radar Timeout Injection

```capl
variables {
  message 0x300 msg_RadarTarget;
  msTimer tRadarCycle;
  msTimer tStopRadar;
  int radarActive = 1;
}

on start {
  // Normal radar target: 40m ahead, same speed
  msg_RadarTarget.dlc = 8;
  msg_RadarTarget.byte(0) = 0x0F;   // Distance high = 4000cm = 40m
  msg_RadarTarget.byte(1) = 0xA0;
  msg_RadarTarget.byte(2) = 0x00;   // RelSpeed = 0
  msg_RadarTarget.byte(3) = 0x00;
  setTimer(tRadarCycle, 20);        // 20ms cycle (50 Hz radar)
  setTimer(tStopRadar, 5000);       // Kill radar after 5 seconds
  write("[ACC-TC04] Phase 1: Radar sending normally...");
}

on timer tRadarCycle {
  if (radarActive) output(msg_RadarTarget);
  setTimer(tRadarCycle, 20);
}

on timer tStopRadar {
  radarActive = 0;
  write("[ACC-TC04] Phase 2: RADAR TIMEOUT — stopped @ t=5s. Monitoring ACC reaction...");
}

on message 0x502 {    // ADAS status message
  if (this.byte(0) & 0x04) {        // ACC fault bit
    write("[ACC-TC04] PASS: ACC fault flag set after radar timeout ✓");
  }
}
```

---

## 2. LKA — Lane Keep Assist

### What it does
LKA detects lane markings via camera and applies steering corrections to keep the
vehicle within its lane. It uses lateral offset and lane departure angle as inputs.

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `LaneDeparture_Offset` | 0x320 | B0-B1 | Lateral offset from lane center (mm, signed) |
| `LaneDeparture_Angle` | 0x320 | B2-B3 | Angle relative to lane (0.01° per bit, signed) |
| `LaneQuality` | 0x320 | B4 | 0=invalid, 1=low, 2=high |
| `VehicleSpeed` | 0x200 | B0-B1 | Must be > 60 km/h for LKA to activate |
| `SteeringAngle` | 0x210 | B0-B1 | Current steering angle (0.1° per bit) |
| `TurnSignal` | 0x220 | B0 | 1=left, 2=right — suppresses LKA during lane change |
| `LKA_TorqueRequest` | 0x510 | B0-B1 | ECU output: steering torque (Nm × 10) |
| `LKA_Warning` | 0x511 | B0 bit0 | 1 = haptic/visual warning active |

### Test Cases & Injection Steps

---

#### TC-LKA-01: Lane departure left — correction torque

```
Step 1: Set vehicle speed to 80 km/h
  → VehicleSpeed = 8000

Step 2: LKA enabled, LaneQuality = 2 (high confidence)
  → Write LaneQuality = 2

Step 3: Simulate slow drift left
  → Ramp LaneDeparture_Offset from 0 → -300mm over 2 seconds
  → Ramp LaneDeparture_Angle from 0 → -150 over 2 seconds

Expected:
  ✓ LKA_TorqueRequest > 0 (right corrective torque)
  ✓ LKA_Warning = 1 (haptic steering wheel vibration)
  ✓ No DTC
```

#### TC-LKA-02: Lane departure suppressed by turn signal

```
Step 1: LKA active, vehicle drifting left (Offset = -200mm)

Step 2: Driver activates LEFT turn signal
  → Write TurnSignal = 1

Expected:
  ✓ LKA_TorqueRequest = 0 (LKA suppressed)
  ✓ LKA_Warning = 0
  ✓ No steering correction applied
```

#### TC-LKA-03: Low lane quality — LKA deactivation

```
Step 1: LKA active with good marking detection

Step 2: Simulate lane markings fade (tunnel, wet road)
  → Write LaneQuality = 0 (invalid)

Expected:
  ✓ LKA deactivates within 200ms
  ✓ LKA_Status on CAN = unavailable
  ✓ Cluster warning lamp ON
  ✓ No DTC (this is a sensor coverage limitation, not a fault)
```

#### TC-LKA-04: Camera signal timeout

```
Step 1: LKA active and correcting

Step 2: STOP sending 0x320 (camera lane data)

Expected:
  ✓ LKA deactivates after timeout (≤ 100ms)
  ✓ DTC logged: camera communication fault
  ✓ LKA_Status = fault
```

### CAPL Script — TC-LKA-01 Lane Drift Injection

```capl
variables {
  message 0x320 msg_Lane;
  msTimer tLaneCycle;
  msTimer tStartDrift;
  int offset = 0;     // mm, signed
  int angle  = 0;     // 0.01°, signed
}

on start {
  // Initial: vehicle centered in lane, good quality
  msg_Lane.dlc = 8;
  msg_Lane.byte(4) = 2;       // LaneQuality = high
  setTimer(tLaneCycle, 20);
  setTimer(tStartDrift, 3000);  // Begin drift after 3s
  write("[LKA-TC01] Phase 1: Centered in lane...");
}

on timer tLaneCycle {
  int rawOffset, rawAngle;
  // Encode signed 16-bit (big endian)
  rawOffset = offset & 0xFFFF;
  rawAngle  = angle  & 0xFFFF;

  msg_Lane.byte(0) = (rawOffset >> 8) & 0xFF;
  msg_Lane.byte(1) =  rawOffset       & 0xFF;
  msg_Lane.byte(2) = (rawAngle  >> 8) & 0xFF;
  msg_Lane.byte(3) =  rawAngle        & 0xFF;
  output(msg_Lane);
  setTimer(tLaneCycle, 20);
}

on timer tStartDrift {
  write("[LKA-TC01] Phase 2: Left drift starting...");
  // Ramp offset from 0 → -300mm (step -3mm per 20ms = 2s to reach -300)
  if (offset > -300) {
    offset -= 3;
    angle  -= 2;      // slight angle change
    setTimer(tStartDrift, 20);
  } else {
    write("[LKA-TC01] Max drift reached: %d mm — check LKA_TorqueRequest", offset);
  }
}

on message 0x510 {   // LKA torque response
  int torque = (this.byte(0) << 8) | this.byte(1);
  if (torque > 0) {
    write("[LKA-TC01] PASS: LKA correction torque = %d (×0.1 Nm) ✓", torque);
  }
}
```

---

## 3. BSD — Blind Spot Detection

### What it does
BSD uses rear-corner radar sensors (left and right) to detect vehicles in the blind spot
zones and warns the driver with a mirror indicator when a lane change would be unsafe.

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `BSD_Left_Target` | 0x330 | B0 | 0=no target, 1=target in left blind spot |
| `BSD_Left_Distance` | 0x330 | B1 | Distance (m) |
| `BSD_Left_Speed` | 0x330 | B2-B3 | Relative speed (km/h × 10) |
| `BSD_Right_Target` | 0x331 | B0 | 0=no target, 1=target in right blind spot |
| `BSD_Right_Distance` | 0x331 | B1 | Distance (m) |
| `BSD_Right_Speed` | 0x331 | B2-B3 | Relative speed (km/h × 10) |
| `TurnSignal` | 0x220 | B0 | 1=left, 2=right |
| `BSD_WarnLeft` | 0x520 | B0 bit0 | 1 = left mirror warning active |
| `BSD_WarnRight` | 0x520 | B0 bit1 | 1 = right mirror warning active |
| `BSD_Chime` | 0x521 | B0 bit0 | 1 = audible chime triggered |

### Test Cases & Injection Steps

---

#### TC-BSD-01: Target in left blind spot — indicator warning

```
Step 1: Vehicle moving > 30 km/h, no turn signal

Step 2: Inject vehicle in left blind spot
  → BSD_Left_Target = 1
  → BSD_Left_Distance = 3 (m)
  → BSD_Left_Speed = 50 (5 km/h faster than ego)

Expected:
  ✓ BSD_WarnLeft bit = 1 (mirror indicator ON)
  ✓ No chime (chime only on turn signal + target)
```

#### TC-BSD-02: Target present + driver signals left turn — active warning

```
Step 1: BSD_Left_Target = 1 (target in blind spot)

Step 2: Driver activates left turn signal
  → TurnSignal = 1

Expected:
  ✓ BSD_WarnLeft = 1 (escalated flashing)
  ✓ BSD_Chime = 1 (audible warning)
  ✓ Both warnings cancel when TurnSignal = 0 and target clears
```

#### TC-BSD-03: High-speed approaching vehicle — RCTW (Rear Cross Traffic)

```
Step 1: Vehicle reversing (Gear = R), speed < 10 km/h

Step 2: Inject fast-approaching vehicle from right rear
  → BSD_Right_Target = 1
  → BSD_Right_Distance = 10 (m)
  → BSD_Right_Speed = -500 (= -50 km/h, approaching fast)

Expected:
  ✓ BSD_WarnRight = 1
  ✓ BSD_Chime = 1
  ✓ AEB rear activation flag (if RCTW + AEB integrated)
```

### CAPL Script — TC-BSD-02 Blind Spot + Turn Signal Escalation

```capl
variables {
  message 0x330 msg_BSD_Left;
  message 0x220 msg_TurnSig;
  msTimer tBSDCycle;
  msTimer tActivateTurn;
}

on start {
  // Inject target in left blind spot
  msg_BSD_Left.dlc = 8;
  msg_BSD_Left.byte(0) = 0x01;   // Target present
  msg_BSD_Left.byte(1) = 0x03;   // 3m distance
  msg_BSD_Left.byte(2) = 0x00;
  msg_BSD_Left.byte(3) = 0x32;   // 50 = 5 km/h faster

  msg_TurnSig.dlc = 8;
  msg_TurnSig.byte(0) = 0x00;    // No signal initially

  setTimer(tBSDCycle, 20);
  setTimer(tActivateTurn, 3000); // Turn signal at t=3s
  write("[BSD-TC02] Phase 1: Target in blind spot, no turn signal");
}

on timer tBSDCycle {
  output(msg_BSD_Left);
  output(msg_TurnSig);
  setTimer(tBSDCycle, 20);
}

on timer tActivateTurn {
  msg_TurnSig.byte(0) = 0x01;   // Left turn signal ON
  write("[BSD-TC02] Phase 2: LEFT turn signal activated — chime expected");
}

on message 0x521 {   // Chime message
  if (this.byte(0) & 0x01) {
    write("[BSD-TC02] PASS: BSD chime activated ✓");
  }
}
```

---

## 4. DMS — Driver Monitoring System

### What it does
DMS uses an infrared cabin camera to track driver gaze, head pose, and eye closure.
It detects drowsiness, distraction, and hands-off-wheel events and escalates warnings.

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `DMS_GazeDirection` | 0x340 | B0 | 0=forward, 1=left, 2=right, 3=down, 4=up |
| `DMS_HeadPose_Yaw` | 0x340 | B1 | Head yaw angle (°, signed, 0=forward) |
| `DMS_EyeClosure` | 0x340 | B2 | 0–100% closed (PERCLOS value) |
| `DMS_FaceDetected` | 0x340 | B3 | 0=no face, 1=face detected |
| `DMS_HandsOnWheel` | 0x341 | B0 | 0=hands off, 1=hands on |
| `VehicleSpeed` | 0x200 | B0-B1 | DMS only active when speed > 20 km/h |
| `DMS_Warning_Level` | 0x530 | B0 | 0=none, 1=visual, 2=audible, 3=haptic+brake |
| `DMS_DrowsinessScore` | 0x531 | B0 | 0–10 (KSS scale) |

### Test Cases & Injection Steps

---

#### TC-DMS-01: Drowsiness detection — eye closure escalation

```
Step 1: Vehicle at 80 km/h, face detected, eyes open
  → DMS_FaceDetected = 1
  → DMS_EyeClosure = 10 (10% = eyes open)
  → DMS_GazeDirection = 0 (forward)

Step 2: Simulate progressive eye closure (microsleep)
  → Ramp DMS_EyeClosure: 10 → 40 → 70 → 90% over 5 seconds

Expected:
  ✓ At 40%: DMS_Warning_Level = 1 (visual icon on cluster)
  ✓ At 70%: DMS_Warning_Level = 2 (audible chime)
  ✓ At 90%: DMS_Warning_Level = 3 (haptic seat + light braking)
  ✓ DMS_DrowsinessScore increases proportionally
```

#### TC-DMS-02: Distraction — gaze away from road

```
Step 1: DMS active, driver looking forward

Step 2: Inject gaze direction = down (phone use)
  → DMS_GazeDirection = 3 (down)
  → DMS_HeadPose_Yaw = 0 (head still forward but gaze down)

Step 3: Hold for > 3 seconds

Expected:
  ✓ After 3s: DMS_Warning_Level ≥ 1
  ✓ ACC/LKA handover request if integrated
```

#### TC-DMS-03: Face not detected (occlusion / no driver)

```
Step 1: DMS active, normal state

Step 2: Simulate face occlusion (sunglasses, bright sun)
  → DMS_FaceDetected = 0

Step 3: Hold for > 5 seconds

Expected:
  ✓ DMS enters "face not detected" mode
  ✓ Warning level escalates if speed > 60 km/h
  ✓ DTC NOT logged (sensor limitation, not fault)
  ✓ If held > 10s: request driver to confirm attention (hands on wheel check)
```

### CAPL Script — TC-DMS-01 Drowsiness Ramp

```capl
variables {
  message 0x340 msg_DMS;
  msTimer tDMSCycle;
  msTimer tRampTimer;
  int eyeClosure = 10;
}

on start {
  msg_DMS.dlc = 8;
  msg_DMS.byte(0) = 0x00;   // GazeDirection = forward
  msg_DMS.byte(1) = 0x00;   // HeadPose_Yaw  = 0°
  msg_DMS.byte(2) = eyeClosure;
  msg_DMS.byte(3) = 0x01;   // Face detected

  setTimer(tDMSCycle, 20);
  setTimer(tRampTimer, 1000); // Ramp eye closure every 1s
  write("[DMS-TC01] Drowsiness ramp test started...");
}

on timer tDMSCycle {
  msg_DMS.byte(2) = eyeClosure;
  output(msg_DMS);
  setTimer(tDMSCycle, 20);
}

on timer tRampTimer {
  eyeClosure += 10;
  if (eyeClosure > 95) eyeClosure = 95;
  write("[DMS-TC01] EyeClosure = %d%%", eyeClosure);
  setTimer(tRampTimer, 1000);
}

on message 0x530 {   // DMS warning level
  byte warnLevel = this.byte(0);
  if (warnLevel > 0) {
    write("[DMS-TC01] Warning Level = %d at EyeClosure = %d%%", warnLevel, eyeClosure);
  }
}
```

---

## 5. APS — Automatic Parking System

### What it does
APS uses ultrasonic sensors (front + rear + side) and sometimes cameras to steer
the vehicle automatically into a parking space while the driver controls throttle/brake.

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `USS_Front_L` | 0x350 | B0 | Ultrasonic front-left distance (cm) |
| `USS_Front_R` | 0x350 | B1 | Ultrasonic front-right distance (cm) |
| `USS_Rear_L` | 0x350 | B2 | Ultrasonic rear-left distance (cm) |
| `USS_Rear_R` | 0x350 | B3 | Ultrasonic rear-right distance (cm) |
| `USS_Side_L` | 0x351 | B0-B1 | Side-left scan distance array (cm) |
| `USS_Side_R` | 0x351 | B2-B3 | Side-right scan distance array (cm) |
| `GearPosition` | 0x230 | B0 | 0=P, 1=R, 2=N, 3=D |
| `VehicleSpeed` | 0x200 | B0-B1 | Must be < 10 km/h for APS |
| `APS_Enable` | 0x430 | B0 bit0 | 1 = APS mode requested |
| `APS_SteerRequest` | 0x540 | B0-B1 | ECU output: steering angle target (0.1°) |
| `APS_Status` | 0x541 | B0 | 0=idle, 1=scanning, 2=maneuvering, 3=complete, 4=aborted |
| `APS_GuidanceMsg` | 0x542 | B0 | 0=stop, 1=move forward, 2=reverse, 3=complete |

### Test Cases & Injection Steps

---

#### TC-APS-01: Space detection scan — valid parallel space

```
Step 1: Vehicle moving at 5 km/h (scan speed), GearPosition = D
  → VehicleSpeed = 500
  → GearPosition = 3 (D)

Step 2: Enable APS scanning
  → APS_Enable = 1

Step 3: Inject side sensor sweep showing a valid gap (6m space between parked cars)
  → USS_Side_R sequence over 60 frames:
     Frames 1–10:  B2-B3 = 0x001E (30cm — car present)
     Frames 11–50: B2-B3 = 0x0190 (400cm — open space)
     Frames 51–60: B2-B3 = 0x001E (30cm — car present again)

Expected:
  ✓ APS_Status transitions: idle → scanning → space found
  ✓ APS offers parking slot to driver
  ✓ Space dimensions logged correctly
```

#### TC-APS-02: Obstacle detection during maneuver — abort

```
Step 1: APS in maneuvering state (reversing into space)
  → APS_Status = 2
  → GearPosition = 1 (R)
  → VehicleSpeed = 200 (2 km/h)

Step 2: Inject sudden obstacle behind vehicle
  → USS_Rear_L = 0x14 (20 cm — critical threshold)
  → USS_Rear_R = 0x14

Expected:
  ✓ APS_Status = 4 (aborted)
  ✓ APS_GuidanceMsg = 0 (stop command)
  ✓ APS_SteerRequest = 0 (steering released)
  ✓ Cluster warning: "Parking aborted — obstacle detected"
```

#### TC-APS-03: USS sensor failure during scan

```
Step 1: APS scanning active

Step 2: Stop sending USS_Front_L (0x350 byte 0 stays at previous value)
  OR inject value 0xFF (sensor invalid code)
  → USS_Front_L = 0xFF

Expected:
  ✓ APS aborts or suspends
  ✓ DTC logged: USS sensor fault (e.g., B1234)
  ✓ APS_Status = 4 (aborted)
```

### CAPL Script — TC-APS-01 Space Detection Scan

```capl
variables {
  message 0x351 msg_USS_Side;
  msTimer tUSS_Cycle;
  int frameCount = 0;
}

on start {
  msg_USS_Side.dlc = 8;
  setTimer(tUSS_Cycle, 20);
  write("[APS-TC01] Side sensor sweep starting (60 frames)...");
}

on timer tUSS_Cycle {
  frameCount++;

  if (frameCount <= 10) {
    // Car present: ~30cm
    msg_USS_Side.byte(2) = 0x00;
    msg_USS_Side.byte(3) = 0x1E;
  } else if (frameCount <= 50) {
    // Open space: 400cm
    msg_USS_Side.byte(2) = 0x01;
    msg_USS_Side.byte(3) = 0x90;
    if (frameCount == 11)
      write("[APS-TC01] Gap start detected at frame %d", frameCount);
  } else if (frameCount <= 60) {
    // Second car: ~30cm
    msg_USS_Side.byte(2) = 0x00;
    msg_USS_Side.byte(3) = 0x1E;
    if (frameCount == 51)
      write("[APS-TC01] Gap end detected at frame %d — checking APS space offer...", frameCount);
  } else {
    write("[APS-TC01] Sweep complete — %d frames sent", frameCount);
    return;
  }

  output(msg_USS_Side);
  setTimer(tUSS_Cycle, 20);
}

on message 0x541 {   // APS Status
  write("[APS-TC01] APS_Status = %d", this.byte(0));
}
```

---

## 6. PCW — Pedestrian Collision Warning

### What it does
PCW detects pedestrians and cyclists in the vehicle path using camera and radar fusion.
It warns the driver and can trigger automatic emergency braking (AEB-P).

### Key CAN Signals

| Signal | CAN ID | Bytes | Description |
|--------|--------|-------|-------------|
| `Ped_ClassID` | 0x360 | B0 | 0=no object, 1=pedestrian, 2=cyclist, 3=large object |
| `Ped_Distance` | 0x360 | B1-B2 | Distance to object (cm) |
| `Ped_LateralOffset` | 0x360 | B3-B4 | Lateral offset from vehicle path (cm, signed) |
| `Ped_RelSpeed` | 0x360 | B5-B6 | Relative speed (cm/s, signed — negative = approaching) |
| `VehicleSpeed` | 0x200 | B0-B1 | PCW active: 5–80 km/h |
| `PCW_Warning` | 0x550 | B0 bit0 | 1 = visual/audible warning |
| `AEB_P_Active` | 0x551 | B0 bit0 | 1 = AEB for pedestrian triggered |
| `AEB_P_Decel` | 0x552 | B0-B1 | Deceleration applied (m/s² × 10) |

### Test Cases & Injection Steps

---

#### TC-PCW-01: Pedestrian in path at 30m — warning only

```
Step 1: Vehicle at 40 km/h, no pedestrian
Step 2: Inject pedestrian in path
  → Ped_ClassID = 1 (pedestrian)
  → Ped_Distance = 3000 (30m)
  → Ped_LateralOffset = 0 (directly ahead)
  → Ped_RelSpeed = -1111 (≈ -40 km/h closing speed)

Expected:
  ✓ PCW_Warning = 1 (audible + visual)
  ✓ AEB_P_Active = 0 (distance too far for AEB, warning only)
  ✓ Warning escalates as distance decreases
```

#### TC-PCW-02: Pedestrian close — AEB-P trigger

```
Step 1: Vehicle at 40 km/h

Step 2: Inject pedestrian suddenly appearing at 6m
  → Ped_ClassID = 1
  → Ped_Distance = 600 (6m)
  → Ped_LateralOffset = 0
  → Ped_RelSpeed = -1111

Expected:
  ✓ AEB_P_Active = 1 within 150ms
  ✓ AEB_P_Decel > 60 (≥ 6 m/s² braking)
  ✓ Full stop before impact
  ✓ DTC NOT logged (normal AEB-P operation)
```

#### TC-PCW-03: Cyclist detection at high lateral offset (edge case)

```
Step 1: Vehicle at 50 km/h

Step 2: Inject cyclist far to the right — NOT in vehicle path
  → Ped_ClassID = 2 (cyclist)
  → Ped_Distance = 1500 (15m)
  → Ped_LateralOffset = 200 (2m to the right of vehicle path)

Expected:
  ✓ PCW_Warning = 0 (object not in path)
  ✓ AEB_P_Active = 0
  ✓ Object tracked but no intervention
```

#### TC-PCW-04: Object misclassification — large static object injected

```
Step 1: Vehicle at 30 km/h

Step 2: Inject large static object (trash can, bollard)
  → Ped_ClassID = 3 (large object)
  → Ped_Distance = 800 (8m)
  → Ped_RelSpeed = 0 (stationary — relative speed = -ego_speed)

Expected:
  ✓ PCW_Warning = 1 (warning for stationary obstacle)
  ✓ AEB_P_Active: depends on implementation
     - If AEB for static objects enabled: AEB_P_Active = 1
     - If pedestrian-only: AEB_P_Active = 0
  ✓ This tests the classification boundary
```

### CAPL Script — TC-PCW-02 AEB-P Trigger

```capl
variables {
  message 0x360 msg_Ped;
  message 0x200 msg_Speed;
  msTimer tCycle;
  msTimer tInjectPed;
}

on start {
  // Set vehicle speed: 40 km/h = 4000 (factor 0.01)
  msg_Speed.dlc = 8;
  msg_Speed.byte(0) = 0x0F;
  msg_Speed.byte(1) = 0xA0;

  // No pedestrian initially
  msg_Ped.dlc = 8;
  msg_Ped.byte(0) = 0x00;   // ClassID = no object

  setTimer(tCycle, 20);
  setTimer(tInjectPed, 3000);  // Inject pedestrian at 3s
  write("[PCW-TC02] Phase 1: Cruising at 40 km/h, no pedestrian...");
}

on timer tCycle {
  output(msg_Speed);
  output(msg_Ped);
  setTimer(tCycle, 20);
}

on timer tInjectPed {
  // Suddenly inject pedestrian at 6m, directly in path, closing fast
  msg_Ped.byte(0) = 0x01;         // ClassID = PEDESTRIAN
  msg_Ped.byte(1) = 0x02;         // Distance high = 0x0258 = 600cm = 6m
  msg_Ped.byte(2) = 0x58;
  msg_Ped.byte(3) = 0x00;         // LateralOffset high
  msg_Ped.byte(4) = 0x00;         // LateralOffset = 0 (directly ahead)
  msg_Ped.byte(5) = 0xFB;         // RelSpeed = -1111cm/s ≈ -40 km/h
  msg_Ped.byte(6) = 0xA9;
  write("[PCW-TC02] Phase 2: PEDESTRIAN injected at 6m — AEB-P expected!");
}

on message 0x551 {   // AEB-P status
  if (this.byte(0) & 0x01) {
    write("[PCW-TC02] PASS: AEB-P ACTIVATED ✓");
  }
}

on message 0x552 {   // Deceleration applied
  int decel = (this.byte(0) << 8) | this.byte(1);
  write("[PCW-TC02] AEB-P deceleration = %.1f m/s²", decel * 0.1);
}
```

---

## 7. Cross-Feature Fault Injection Checklist

Use this checklist in any ADAS test session to systematically cover all failure modes:

### Signal Timeout Faults

| Signal Killed | Expected ECU Reaction | DTC Family |
|--------------|----------------------|-----------|
| Radar 0x300 | ACC/AEB disables | U0401 (radar comm lost) |
| Camera 0x320 | LKA/PCW disables | U0422 (camera comm lost) |
| USS 0x350 | APS aborts | B1xxx (USS sensor fault) |
| DMS 0x340 | DMS warning, LKA hands-off check | U0480 (DMS comm lost) |
| VehicleSpeed 0x200 | ALL ADAS features disable | U0126 (wheel speed lost) |

### Signal Range Violations (Send out-of-range values)

| Signal | Valid Range | Inject Value | Expected Reaction |
|--------|-------------|-------------|-------------------|
| VehicleSpeed | 0–300 km/h | 0xFFFF | ADAS disable + DTC |
| RadarTarget_Distance | 0–250m | 0x0000 (0cm) | AEB trigger OR fault, check spec |
| DMS_EyeClosure | 0–100% | 200% (0xC8) | Clamp to 100% or flag invalid |
| USS_Front_L | 0–255 cm | 0xFF | Sensor invalid → APS abort |

### Communication Error Injection

```
CANoe: Simulation Setup → Right-click CAN channel → Add Disturbance
- Error type: Bit error on specific message ID
- Inject 5 consecutive error frames on 0x300
- Expected: error counter increment, eventually DTC
```

---

## 8. CANoe Setup Checklist (All Features)

Before running ANY ADAS injection test in CANoe:

```
□ 1. Load DBC file
     File → Database → Add (select .dbc)
     Verify signals decode in Trace window

□ 2. Load ODX/PDX diagnostic file (for DTC checks)
     Diagnostics → Configuration → Add ECU description (select .pdx)
     Node name: match exactly with CAPL diagResponse handlers

□ 3. Simulation Setup
     Open Simulation Setup (F8)
     Add simulation nodes for signals you will inject
     Connect to correct CAN channel (e.g., CAN 1 = body bus, CAN 2 = ADAS bus)

□ 4. Configure Graphics window
     Drag key output signals to Graphics: ThrottleRequest, BrakeRequest,
     LKA_TorqueRequest, AEB_P_Active, DMS_Warning_Level, APS_Status

□ 5. Open Diagnostic Console (for DTC readout)
     Diagnostics → Diagnostic Console
     After each test: ReadDTCInformation (0x19 02 0F) to read all active DTCs

□ 6. Start logging
     Measurement → Logging → Configure (.blf file, all channels)
     Always log before pressing Start — never lose a test run

□ 7. Run CAPL script
     Simulation Setup → Add CAPL node → Assign .can file
     Or: open CAPL browser → compile → assign to Environment

□ 8. Post-test DTCs
     In Diagnostic Console: send 0x19 02 0F → verify expected DTCs present
     Clear DTCs: 0x14 FF FF FF → re-run → verify DTCs set again (reproducible)

□ 9. Save .blf log + screenshots
     Name format: ADAS_<Feature>_<TC_ID>_<PassFail>_<Date>.blf
```

---

> **Interview talking point:**
> "For ADAS testing, I always start with signal-level injection in CANoe before moving to
> HIL or vehicle level. This lets me verify ECU logic in isolation — I know exactly which
> inputs I sent and what response I expect. Once the logic is confirmed, I move to HIL
> where I add sensor noise, timing variation, and multi-ECU interactions. The final vehicle
> test then becomes a confidence check, not a discovery exercise."
