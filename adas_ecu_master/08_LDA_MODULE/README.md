# 08 — Lane Departure Assist (LDA) Module

> **Feature:** LDA — Alerts driver when vehicle drifts from lane **without** steering intervention  
> **ASIL:** B (alerts only) — compare LKA ASIL C/D (active steering)  
> **Standard:** ISO 17361 (LDWS — Lane Departure Warning Systems)

---

## 08.1 LDA vs LKA — Feature Comparison

| Attribute          | LDA (Lane Departure Assist)      | LKA (Lane Keeping Assist)         |
|--------------------|----------------------------------|-----------------------------------|
| Intervention type  | Warnings only                    | Steering torque correction        |
| ASIL               | ASIL B                           | ASIL C/D                          |
| Min speed          | 60 km/h (typical)                | 60 km/h (typical)                 |
| Alert types        | Visual + haptic + audible        | Steering torque (+ alerts)        |
| Driver override    | Indicator active suppresses alert| Torque override detected          |
| ISO standard       | ISO 17361 LDWS                   | ISO 11270 LKAS                    |
| ASIL decomp.       | Not required                     | Required (ASIL D decomposed)      |

---

## 08.2 LDA Algorithm — Time to Line Crossing (TLC)

```
Time-To-Line-Crossing (TLC):

  TLC = lateral_gap_to_lane_marking / |lateral_velocity|

  Where:
    lateral_gap_to_lane_marking = distance between vehicle edge and lane marking (metres)
    lateral_velocity = vehicle lateral velocity (m/s) computed from:
                       lateral_velocity = vehicle_speed × sin(heading_angle)
                       (or directly from IMU lateral acceleration integral)

  Example:
    Lane offset = 0.35m (vehicle drifting right, 0.70m wide vehicle, 0.40m to line)
    Lateral velocity = 0.05 m/s
    TLC = 0.40 / 0.05 = 8.0 seconds → No warning

  Warning threshold:
    TLC < 3.0s → Visual warning (LED flicker on departing side)
    TLC < 1.5s → Haptic warning (seat vibration or steering wheel vibration)
    TLC < 0.8s → Audible warning (beep) + visual

  Suppression conditions:
    - Turn indicator active (intentional lane change)
    - LKA active (LKA already correcting → no need for LDA warning)
    - Speed < 60 km/h
    - Lane quality poor (camera confidence < 60%)
    - AEB active
```

---

## 08.3 LDA State Machine

```
                  ┌─────────────────────────────────────┐
                  │            POWER_OFF                 │
                  └─────────────────┬───────────────────┘
                                    │ Ignition ON
                  ┌─────────────────▼───────────────────┐
                  │            INITIALISING              │
                  └─────────────────┬───────────────────┘
                                    │ Camera ready + speed > 60
         ┌──────────────────────────▼──────────────────────────────┐
         │                     MONITORING                          │
         │   Camera tracking. TLC computed. No warning active.     │
         └──────┬───────────────────┬──────────────────────────────┘
                │ TLC < 3.0s        │ Indicator ON / Speed < 60
  ┌─────────────▼──────────┐        │
  │        WARNING         │        ▼
  │ Visual alert on dash   │   ┌──────────────┐
  │ LED flickers on side   │   │  SUPPRESSED  │
  └─────────────┬──────────┘   └──────────────┘
                │ TLC < 1.5s
  ┌─────────────▼──────────┐
  │      HAPTIC_ALERT      │
  │  Seat vibration        │
  └─────────────┬──────────┘
                │ TLC < 0.8s
  ┌─────────────▼──────────┐
  │    CRITICAL_ALERT      │
  │  Audible + haptic      │
  └────────────────────────┘
    All states → MONITORING when TLC > 4.0s (hysteresis)
```

---

## 08.4 Camera Signal Interface

```cpp
// Camera outputs (received from Camera ECU via CAN)
struct LdaCameraInputs {
    float   laneOffsetM;         // Lateral offset from lane centre [m]
    float   headingAngleDeg;     // Vehicle heading relative to lane [deg]
    float   laneWidthM;          // Detected lane width [m]
    uint8_t laneQuality;         // 0=LOST, 1=LOW, 2=MEDIUM, 3=HIGH
    bool    leftMarkerDetected;
    bool    rightMarkerDetected;
};
```

---

## 08.5 MISRA Considerations

| Rule | Category | LDA Relevance |
|------|----------|---------------|
| M0-1-1 | Unreachable code | Every TLC branch must be reachable in unit test |
| M5-0-6 | Implicit conversion | TLC division: ensure float cast, not integer division |
| M6-4-5 | No switch fall-through | State switch must have explicit break; |
| M7-5-2 | Reference to automatic variable | Ensure LDA inputs not stack-copied in ISR |

---

## 08.6 Interview Questions

**L1 (Junior):**
1. What is the difference between LDA and LKA?
2. What is TLC and how is it calculated?
3. Why is LDA ASIL B while LKA is ASIL C/D?
4. What conditions suppress LDA warnings?

**L2 (Senior):**
5. How do you handle the hysteresis between TLC thresholds to prevent alert flickering?
6. A driver complains of false LDA warnings during intentional lane merges with no indicator. How do you improve the system?
7. How would you validate TLC computation in HIL?
8. What is the latency budget for LDA from lane departure to visual alert?

**L3 (Principal):**
9. Design the full requirements traceability for LDA from ISO 17361 down to software test.
10. How does LDA interact with ACC during a slow drift on motorway?
11. LDA false alert rate must be < 0.1 per 100km. How do you measure and verify this?
12. Propose a safety mechanism to handle camera dropout during active LDA warning.
