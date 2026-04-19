# ADAS Interview Deep Dive — 50 Questions
## Sensor Fusion | AEB | LKA | ISO 26262 | SOTIF | Functional Safety

---

## Section 1: ADAS System Architecture

**Q1: What are the main sensors used in ADAS and their strengths?**
| Sensor | Range | FOV | Strengths | Weaknesses |
|--------|-------|-----|-----------|------------|
| Radar (77GHz) | 200m+ | 15–90° | All weather, velocity | Low resolution |
| Lidar | 100–200m | 360° | High resolution 3D | Cost, rain/fog |
| Camera | 30–150m | 50–180° | Color, lane lines, signs | Low light, glare |
| Ultrasonic | 30–500cm | Wide | Low cost, parking | Short range only |

**Q2: What is sensor fusion and why is it needed?**
> Sensor fusion combines data from multiple sensor modalities to produce a more accurate, robust, and complete perception of the environment than any single sensor alone. Each sensor has blind spots and failure modes; fusion provides redundancy and fills gaps.

**Q3: What is the difference between early, mid-level, and late fusion?**
> **Early (raw):** Combine raw sensor data before any feature extraction — most information preserved but computationally expensive. **Mid-level (feature):** Fuse extracted features (bounding boxes, clusters) from each sensor — balance of accuracy and compute. **Late (decision):** Each sensor makes independent decisions; results are combined at decision level — simplest but information loss.

---

## Section 2: ADAS Functions

**Q4: Describe the AEB (Automatic Emergency Braking) decision chain.**
```
Perception → Object Detection (pedestrian, vehicle)
           → Object Classification
           → Object Tracking (speed, heading)
           
Threat Assessment → TTC (Time to Collision) = Distance / Relative Speed
                 → TTC < threshold_1 → FCW alert
                 → TTC < threshold_2 → Partial brake
                 → TTC < threshold_3 → Full autonomous brake

Control → Brake command to ESP/ABS
        → Engine torque reduction request
```

**Q5: What is TTC and how is it calculated?**
> Time-To-Collision = Current distance / Closing speed
> `TTC = d / (v_ego - v_target)` (when v_ego > v_target — closing)
> AEB typically triggers FCW at TTC < 2.7s and autonomous braking at TTC < 1.5s.

**Q6: How does Lane Keep Assist (LKA) work?**
```
Camera detects lane markings → Fits polynomial curve to lanes
Lane center computed → Lateral error = vehicle_position - lane_center
                    → Heading error = vehicle_heading - lane_heading

PID/MPC controller → Steering torque request to EPS
                  → Torque proportional to lateral + heading error

Activation conditions: Speed > 60 km/h, lane lines visible,
                       driver not fighting system (torque override)
```

**Q7: What is the difference between LDW (warning) and LKA (assist)?**
> LDW (Lane Departure Warning) only alerts the driver (audio/haptic) when the vehicle crosses lane markings without a turn signal. LKA actively applies corrective steering torque to keep the vehicle in lane. LKA requires EPS (Electric Power Steering) with torque overlay capability.

---

## Section 3: ISO 26262 — Functional Safety

**Q8: What are the ASIL levels and what do they mean?**
| ASIL | Risk | Integrity Requirements | Example |
|------|------|------------------------|---------|
| A | Lowest | Basic | Seat belt reminder |
| B | Low | Moderate | Power windows |
| C | Medium | Significant | Electronic brake assistance |
| D | Highest | Stringent | AEB, EPS |
| QM | No risk | No special measures | Radio display |

**Q9: What is the HARA process?**
> Hazard Analysis and Risk Assessment:
> 1. **Item definition** — what does the function do?
> 2. **Situation analysis** — driving scenarios (highway, parking, tunnel)
> 3. **Hazard identification** — what can go wrong? (unintended braking, loss of steering)
> 4. **Risk assessment** — Severity × Exposure × Controllability = ASIL
> 5. **Safety goals** — top-level safety requirements

**Q10: What is Severity, Exposure, and Controllability in ISO 26262?**
| Parameter | Levels | Description |
|-----------|--------|-------------|
| Severity (S) | S0–S3 | S3=Life threatening injury |
| Exposure (E) | E0–E4 | E4=High probability driving scenario |
| Controllability (C) | C0–C3 | C3=Virtually uncontrollable |
> **ASIL = f(S, E, C)** — tables in ISO 26262-3 Annex B determine ASIL level.

**Q11: What is the difference between safety goal and safety requirement?**
> A **safety goal** is a top-level objective derived from HARA (e.g., "The vehicle shall not apply autonomous emergency braking unintended"). A **safety requirement** is a derived, verifiable requirement that achieves the safety goal (e.g., "The AEB function shall verify object detection with 2-of-3 sensor agreement before braking").

**Q12: What is FMEA (Failure Mode and Effect Analysis)?**
> Systematic method to identify failure modes of each component, their effects, and severity. In ISO 26262: Diagnostic Coverage (DC) measures what percentage of failures are detected. FMEA feeds safety mechanism design (e.g., dual-channel, watchdog timers).

---

## Section 4: SOTIF (ISO 21448)

**Q13: What is SOTIF and how does it differ from ISO 26262?**
> ISO 26262 handles **safety of the intended function** — random hardware failures and systematic software errors. **SOTIF** (Safety Of The Intended Function, ISO 21448) handles situations where the **intended function itself is insufficient** for safe operation — e.g., camera fails to detect a pedestrian in rain (no hardware fault, but unsafe output). SOTIF focuses on **functional insufficiency and misuse**.

**Q14: Give an example of a SOTIF issue vs an ISO 26262 issue.**
> **ISO 26262:** AEB radar sensor loses power due to a hardware fault → Random HW failure → needs fault tolerance.
> **SOTIF:** AEB camera fails to detect a pedestrian wearing unusual clothing in direct sunlight → No hardware fault, algorithm is insufficient for this edge case → SOTIF issue.

---

## Section 5: Sensor Fusion Algorithms

**Q15: What is a Kalman Filter and why is it used in ADAS?**
> Kalman Filter is an optimal linear estimator that combines noisy sensor measurements with a dynamic model to produce the best estimate of state (position, velocity). Used for object tracking: predicts next position using vehicle model, corrects with sensor measurement.
```
Predict: x_k|k-1 = F × x_k-1|k-1 + B × u
         P_k|k-1 = F × P_k-1|k-1 × F^T + Q

Update:  K = P_k|k-1 × H^T × (H × P_k|k-1 × H^T + R)^-1
         x_k|k = x_k|k-1 + K × (z_k - H × x_k|k-1)
         P_k|k = (I - K × H) × P_k|k-1
```

**Q16: What is an Extended Kalman Filter (EKF)?**
> Extension of Kalman Filter for **nonlinear** systems. Linearizes the nonlinear functions at each timestep using Jacobians. Used in ADAS when the motion model or sensor model is nonlinear (e.g., radar measuring range and angle, converting to Cartesian coordinates).

**Q17: What is the difference between occupancy grid and object list representation?**
> **Occupancy grid:** 2D/3D grid where each cell stores probability of being occupied — good for free-space detection, path planning. **Object list:** List of detected objects with attributes (class, position, velocity, size) — good for tracking, prediction. Most ADAS systems use object lists for high-level functions.

---

## Section 6: Testing & Validation

**Q18: How do you test AEB in HIL (Hardware in the Loop)?**
```
1. Build vehicle dynamics model + target vehicle model in dSPACE
2. Connect real AEB ECU
3. Inject radar/camera measurements via sensor model
4. Define test scenarios: pedestrian crossing at TTC=2s, 1.5s, 1.0s
5. Verify: FCW alert timing, brake command magnitude, deceleration rate
6. Vary: speed (20/40/60 km/h), target type (pedestrian/vehicle), lighting
```

**Q19: What is the difference between a false positive and false negative in AEB?**
> **False positive (phantom braking):** AEB triggers without a real obstacle — nuisance activation, can cause rear-end collision from following vehicle. **False negative (miss):** AEB fails to activate when an obstacle is present — impact occurs. Both are safety concerns: false positives reduce driver trust; false negatives cause accidents.

**Q20: What is a test scenario database for ADAS?**
> A structured collection of driving scenarios for ADAS testing, including: scene parameters (road type, weather, lighting), object positions/velocities, ego vehicle state. Frameworks: OpenSCENARIO (format standard), ASAM OSC, Carla simulator, IPG CarMaker, AVL VSM. Used for coverage-based SOTIF validation.
