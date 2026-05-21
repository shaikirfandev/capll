# 07 — Lane Keep Assist (LKA) Module

> **Feature level:** Production ECU (Bosch LKA, Continental LK+)  
> **Regulation:** UNECE R79 (Lane-keeping, mandatory EU from 2022)

---

## 7.1 LKA System Overview

```
INPUTS:
  - Camera (lane marking detection) → lane offset + heading angle
  - Vehicle speed (from BCM via CAN)
  - Steering torque sensor (driver override detection, from EPS)
  - LKA enable switch (driver)

PROCESSING (ADAS ECU, 10ms cycle):
  - State machine: INACTIVE → STANDBY → CORRECTING → OVERRIDE → FAULT
  - PID lateral controller: computes steering torque correction
  - Safety monitors: driver override, sensor timeout, EPS fault

OUTPUTS:
  - Steering torque request → EPS (Electric Power Steering) via CAN
  - Warning indicator → Instrument cluster via CAN
  - DTC logging → DEM on fault
```

---

## 7.2 State Machine Transitions

```
                    LKA Switch ON
                    Speed >= 60 km/h
                    Lane markers visible
INACTIVE ──────────────────────────────► STANDBY
   ▲                                        │
   │ Switch OFF                             │ Offset > 15cm
   │ Speed < 60 km/h     CORRECTING ◄───────┘
   │ Lane lost               │
   │                         │ Offset < 7.5cm
   │                         ▼
   └──────────── STANDBY ◄────
                         │
                         │ Driver torque > 2.5 Nm
                         ▼
                     OVERRIDE (3s hold)
                         │
                         │ Torque < 1.25 Nm AND timer expires
                         ▼
                      STANDBY

Any State → FAULT: EPS fault, sensor error
```

---

## 7.3 PID Lateral Control

```
Error signal = desired_lane_offset (0) - actual_lane_offset
            + lane_heading_feedforward_term

Steering torque = Kp*error + Ki*∫error + Kd*(d/dt error)

Typical gains (varies by vehicle dynamics):
  Kp = 0.8 Nm/m
  Ki = 0.15 Nm/(m·s)
  Kd = 0.05 Nm·s/m
  
  Max output: ±3 Nm (EPS accepts up to ±5 Nm for LKA)

Anti-windup: integral clamped to ±5 Nm·s
  Prevents integrator windup during OVERRIDE/STANDBY states.
  Reset integrator whenever exiting CORRECTING state.
```

---

## 7.4 Camera Lane Detection (Signal Interface)

```
Camera SWC outputs (via RTE port):
  LaneOffset_m:    lateral distance from lane centre (negative = left of centre)
  LaneHeading_deg: heading angle vs lane (negative = pointing left)
  LaneQuality:     GOOD (0) / DEGRADED (1) / LOST (2)
  LeftMarkType:    SOLID / DASHED / NONE
  RightMarkType:   SOLID / DASHED / NONE
  LaneWidth_m:     detected lane width

LKA reacts to quality:
  GOOD:     full torque correction (100%)
  DEGRADED: reduced correction (60%) + warning
  LOST:     deactivate LKA + warning

Timeout monitoring (COM Rx timeout):
  Camera sends lane data every 20ms.
  If no frame received for 100ms → LKA transitions to FAULT.
```

---

## 7.5 Driver Override Detection

```
EPS torque sensor monitors driver hand torque.
Threshold: 2.5 Nm (configurable, EEPROM parameter)

Override logic:
  If driver_torque_abs > OVERRIDE_THRESHOLD:
    → LKA immediately releases steering (torque_request = 0)
    → Transition to OVERRIDE state
    → Hold for 3 seconds minimum (prevents oscillation)
    → Re-engage: driver torque < 1.25 Nm AND 3s elapsed

Haptic feedback option:
  Some OEMs configure EPS to vibrate steering wheel instead of torque correction
  This is LDA mode (Lane Departure ALERT) vs LKA mode (Lane Keep ASSIST)
```

---

## 7.6 Interview Questions

```
L1:
  Q: What is the difference between LKA and LDA?
  A: LDA (Lane Departure Alert): detection only. Warns driver when vehicle
     leaves lane without indicator. Warning: visual (dashboard), acoustic (beep),
     haptic (steering vibration). No steering intervention.
     
     LKA (Lane Keep Assist): active intervention. Applies steering torque to
     keep vehicle centred in lane. Driver can override with steering input.
     LKA is a higher ASIL level (B or C) than LDA because it actively controls steering.

  Q: What CAN messages does LKA read and write?
  A: READ:
       BCM_Status (0x100):  VehicleSpeed (enable/disable condition)
       Camera_Lane (0x3xx): LaneOffset, LaneHeading, LaneQuality (control input)
       EPS_Status (0x200):  DriverTorque (override detection), EpsFaultActive
     WRITE:
       ADAS_LKA_Cmd (0x300): LkaTorqueRequest, LkaActiveFlag (to EPS)
       BCM_Lamp_Cmd:         LKA warning indicator (to instrument cluster)

L2:
  Q: How do you handle sensor timeout in LKA?
  A: AUTOSAR COM layer monitors Rx signal timeout (configured in ARXML).
     If CameraLane PDU not received within ComRxDataTimeoutPeriod (e.g., 100ms),
     COM calls a timeout notification callback → SWC transitions to FAULT state.
     Safety reaction: zero torque request to EPS, log DTC to DEM,
     illuminate warning lamp. State is latching until ignition cycle or explicit reset.

  Q: What is anti-windup and why is it needed in LKA PID?
  A: Without anti-windup: when LKA is in STANDBY or OVERRIDE, the PID integral
     term keeps accumulating error (wind-up). When LKA re-engages, the large
     integral term causes a sudden large steering torque → dangerous step response.
     Anti-windup: clamp integral to ±5 Nm·s range. Also, reset integral when
     transitioning out of active states. This ensures smooth re-engagement.

L3:
  Q: What is the ASIL requirement for LKA and why?
  A: LKA controls vehicle steering → loss of control hazard → potentially lethal.
     ISO 26262 HARA (Hazard Analysis and Risk Assessment):
     Hazard: "Unintended steering torque at highway speed (80+ km/h)"
     Severity: S3 (life-threatening)
     Exposure:  E4 (high — LKA active on every highway drive)
     Controllability: C2 (driver can override but not always in time)
     ASIL = S3 + E4 + C2 → ASIL C or ASIL D
     
     Safety mechanisms required at ASIL C/D:
     1. EPS independent torque monitoring (cross-check with driver intent)
     2. Maximum torque limit enforced in EPS firmware (not just ADAS ECU)
     3. Timeout on LKA command: EPS stops torque if no ADAS frame for 50ms
     4. ISO 26262 FMEA on LKA SWC
     5. ADAS ECU and EPS ECU run independent safety monitors
```
