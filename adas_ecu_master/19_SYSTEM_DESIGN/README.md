# 19 — System Design for ADAS ECU

> **Level:** Principal Engineer interview questions  
> **Format:** Design interviews at Bosch, Continental, NVIDIA Automotive, Mobileye

---

## 19.1 How to Approach System Design Interviews

```
Framework (5 minutes of structured thinking):
  1. Requirements clarification (functional + non-functional)
  2. Constraints and assumptions (latency, ASIL, memory, protocols)
  3. High-level architecture (block diagram — layers, interfaces)
  4. Component deep-dive (pick 2-3 critical components)
  5. Trade-off discussion (alternative architectures and why you chose yours)
  6. Safety and failure modes
```

---

## 19.2 Design: LKA ECU From Scratch

### Requirements

```
Functional:
  FR1: LKA shall maintain vehicle within detected lane markings
  FR2: LKA shall activate at speed ≥ 60 km/h with lane quality ≥ MEDIUM
  FR3: LKA shall deactivate if driver applies > 2.5 Nm torque for > 0.2s
  FR4: LKA shall limit correction torque to ± 3.0 Nm
  FR5: LKA shall send CAN torque request to EPS at 10ms period

Non-functional:
  NFR1: ASIL C (torque output), ASIL B (state monitoring), ASIL A (display)
  NFR2: Latency: camera → LKA torque output ≤ 50ms
  NFR3: Safe state: LkaTorqueRequest = 0 Nm on any fault
  NFR4: Memory: ≤ 16 KB RAM, ≤ 64 KB flash
  NFR5: CPU: ≤ 5% of 10ms task on AURIX TC277
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   LKA ECU Block Diagram                         │
├────────────────────────────────────────────────────────────────┤
│ Camera ECU                                                      │
│  (CAN 0x230)  ──────┐                                           │
│                     ▼                                           │
│               ┌─────────────┐    ┌──────────────────────────┐  │
│               │ LKA Input   │    │  LKA State Machine        │  │
│               │ Validator   │───▶│  (STANDBY/CORRECTING/     │  │
│               │ (ASIL B)    │    │   OVERRIDE/FAULT)         │  │
│               └─────────────┘    └───────────┬──────────────┘  │
│ BCM (speed)                                  │                  │
│  (CAN 0x100) ──────┐                         ▼                  │
│                    │               ┌──────────────────────┐     │
│ EPS (torque sens.) │               │   PID Controller     │     │
│  (CAN 0x200) ──────┤               │   (ASIL C)           │     │
│                    │               │   Kp=0.8 Ki=0.15     │     │
│                    ▼               │   Kd=0.05 ±3Nm       │     │
│              ┌──────────┐          └───────────┬──────────┘     │
│              │ Override │                       │                │
│              │ Detector │◀──── EPS torque ──────┘                │
│              └──────────┘                       │                │
│                                                 ▼                │
│                                     ┌──────────────────────┐    │
│                                     │  Output Limiter      │    │
│                                     │  + E2E Encoder       │    │
│                                     │  + CAN TX (0x300)    │    │
│                                     └──────────────────────┘    │
│                                                 │                │
│                                                 ▼                │
│                                          EPS ECU                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

```
Decision 1: Separate ASIL C PID from ASIL B state machine
  Rationale: ASIL decomposition — C = C (no decomposition needed)
  But isolating them allows independent review of safety-critical torque computation

Decision 2: Hardware torque limiter in EPS (not only in LKA software)
  Rationale: Defense in depth. If LKA sends wrong value due to RAM corruption,
  EPS hardware clamps the torque. Single-point fault protection.

Decision 3: E2E CRC on LKA command frame
  Rationale: ASIL C signal. E2E Profile 2 (16-bit CRC + 8-bit counter).
  Counter ensures stale frame detection (EPS detects old LKA command reuse).
```

---

## 19.3 Design: ACC with AEB Integration

```
Functional Requirements:
  ACC: maintain set speed (up to 200 km/h) and following gap (min 5m, 1.5s TTC)
  AEB: intervene when TTC < 1.0s, full stop from 80 km/h in < 3.0s

Architecture Layers:
  1. Radar signal processing (50ms cycle): object list (up to 32 objects, id/range/azimuth/speed)
  2. ACC target selection (50ms): MRO = Most Relevant Object (in-path azimuth filter)
  3. ACC gap control (50ms): dual PID (speed + gap), outputs: throttle%, brake%
  4. AEB monitor (20ms): INDEPENDENT from ACC (different ASIL chain)
     - TTC computation on highest-confidence in-path object
     - Trigger: TTC < 1.0s → request full braking
  5. ESC arbitration (10ms): max(ACC_brake, AEB_brake) → wheel braking commands
  6. Driver override: brake pedal > 30% → freeze ACC, cancel AEB

ASIL allocation:
  ACC control: ASIL B (speed + gap, not AEB)
  AEB decision: ASIL D (full deceleration to standstill)
  ESC arbitration: ASIL D (controls all braking)
  
Key safety mechanism: ESC independently validates AEB request via radar redundancy check
  (ESC has its own TTC estimate from wheel speed + ultrasonic)
```

---

## 19.4 Design: Domain Controller ECU (L3 Highway Assist)

```
Platform: NXP S32G2 (4× Cortex-A53 + 3× Cortex-M7) + TDA4VM (8-TOPS)

Processing partitioning:
  TDA4VM:        Camera perception (CNN), radar fusion, map matching
  S32G2 Cortex-A: Path planning, driver monitoring integration (AUTOSAR Adaptive)
  S32G2 Cortex-M: Safety monitor, actuator interface, watchdog (AUTOSAR Classic)

Communication:
  1000BASE-T1 backbone to domain controller
  Domain controller bridges to CAN FD subnets (EPS, ESC, BCM)
  SOME/IP between Adaptive services (camera, map, path planner)
  CAN FD for safety-critical actuation (EPS, ESC commands)

Latency budget (sensor → actuator):
  Camera frame capture:           0ms
  Neural network inference:      40ms (TDA4VM DLA)
  Sensor fusion:                  5ms
  Path planning:                  10ms
  Safety validation:              5ms
  CAN TX to EPS:                  2ms (10ms frame period)
  Total budget:                  62ms (must be < 100ms)

Safety architecture:
  ASIL D: safety monitor on Cortex-M7 (always running, independent clock)
  ASIL B: path planner on Cortex-A
  Decomposition: D = B+B (path planner) + D (safety monitor) with independence
```

---

## 19.5 Non-Functional Requirements Table

| Requirement      | LKA          | ACC          | Domain Controller (L3) |
|------------------|--------------|--------------|------------------------|
| ASIL             | C/D          | B            | D (AEB)               |
| Response latency | ≤ 50ms       | ≤ 100ms      | ≤ 100ms               |
| Cycle time       | 10ms         | 50ms         | 10ms (safety)         |
| RAM              | 16 KB        | 32 KB        | 512 MB (Adaptive)     |
| Flash            | 64 KB        | 128 KB       | 8 GB (NN model)       |
| Temp range       | -40 to 85°C  | -40 to 85°C  | -40 to 85°C           |
| Test coverage    | MC/DC (ASIL C)| Branch (ASIL B)| MC/DC + MC (safety) |

---

## 19.6 Interview Questions

**L1:**
1. What layers would you include in an LKA ECU?
2. What is the safe state of an LKA system?
3. Why is the torque limited in hardware AND software?

**L2:**
4. How would you separate AEB from ACC to achieve ASIL D for AEB?
5. Describe the communication interface between ACC (ASIL B) and ESC (ASIL D).
6. What would happen if the camera ECU crashes mid-drive? Design the graceful degradation.

**L3:**
7. Design the OTA architecture for a Level 3 highway assist ECU.
8. How would you partition a domain controller ECU for L3 to meet both ASIL D safety and Adaptive AUTOSAR flexibility?
9. Design the latency budget for a L3 camera-to-steering path.
10. How would you achieve functional safety evidence for an ML-based perception module in ISO 26262?
