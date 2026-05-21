# 02 — ADAS Domain

## Overview

This module covers the **Advanced Driver Assistance Systems (ADAS)** domain concepts implemented in `adas_rt_cpp_project`: sensor types, coordinate systems, object detection, Extended Kalman Filter sensor fusion, trajectory planning, and vehicle control.

---

## 1. ADAS System Functional Hierarchy

```
ISO 26262 Functional Chain
────────────────────────────────────────────────────────────────────
Environment Sensing
    │
    ▼
Object Detection & Classification
    │
    ▼
World Model (Sensor Fusion / EKF Tracker)
    │
    ▼
Situation Assessment (TTC, gap, lane geometry)
    │
    ▼
Behavior Decision (CRUISE / FOLLOW / AEB / LANE_CHANGE)
    │
    ▼
Trajectory Planning (JMT polynomial)
    │
    ▼
Vehicle Control (PID + Stanley)
    │
    ▼
Actuators (throttle, brake, steering)
────────────────────────────────────────────────────────────────────
```

---

## 2. Coordinate System (ISO 8855)

All ADAS calculations use the **ISO 8855 vehicle-fixed frame**:

```
        X (forward)
        ▲
        │
        │
Y ◄─────┼─────── (left is positive)
        │
        │ Z points up (right-hand rule)
```

| Axis | Direction | Unit |
|------|-----------|------|
| X | Vehicle forward | metres |
| Y | Vehicle left | metres |
| Z | Up | metres |
| Yaw (ψ) | Counter-clockwise from X | radians |

### Extrinsic Sensor Transform

Each sensor has a mounting pose `(tx, ty, tz, roll, pitch, yaw)` relative to the vehicle body. The `ObjectDetector` applies a ZYX Euler rotation matrix to transform sensor-frame detections into the ego vehicle frame:

```
R_body_from_sensor = Rz(yaw) * Ry(pitch) * Rx(roll)

p_body = R_body_from_sensor * p_sensor + t_body_from_sensor
```

---

## 3. Sensor Types

### 3.1 Camera

| Property | Value |
|----------|-------|
| Output | 2D bounding boxes (u, v, width, height) + class label |
| Range | ~0–150 m (varies by resolution) |
| Update rate | 30–60 Hz |
| Strengths | Rich semantic data (pedestrian, sign, lane marking) |
| Weaknesses | Depth ambiguity; degrades in poor lighting / fog |

**Unproject to 3D** (pin-hole model):
```
Given bounding box bottom-centre: (u_c, v_bot)

x_cam = (u_c - cx) / fx           # normalized horizontal
z_cam = camera_height / (1 - (v_bot - cy) / fy)  # height assumption
y_cam = x_cam * z_cam
```

### 3.2 Radar

| Property | Value |
|----------|-------|
| Output | Range (ρ), azimuth (φ), Doppler range-rate (ρ̇) |
| Range | ~1–200 m |
| Update rate | 20–50 Hz |
| Strengths | All-weather; direct velocity measurement |
| Weaknesses | Low angular resolution; ghost targets possible |

**Polar to Cartesian**:
```
px = ρ * cos(φ)
py = ρ * sin(φ)
vx = ρ̇ * cos(φ)
vy = ρ̇ * sin(φ)
```

### 3.3 LiDAR

| Property | Value |
|----------|-------|
| Output | Point cloud (x, y, z, intensity) |
| Range | ~1–200 m |
| Update rate | 10–20 Hz |
| Strengths | High angular/depth precision; 3D shape information |
| Weaknesses | Expensive; affected by rain/snow scattering |

**Clustering (Simplified DBSCAN)**:
```
For each point p:
  For each unvisited neighbour q within ε=1.5m:
    Add to current cluster
  If cluster size >= minPts=3: output as detected object
```

---

## 4. Extended Kalman Filter (EKF) Sensor Fusion

### 4.1 Why EKF?

The Kalman Filter (KF) is optimal for linear Gaussian systems. Radar range-rate gives a **non-linear** measurement (because `ρ̇ = (px*vx + py*vy) / ρ` depends on both position and velocity non-linearly). The EKF handles this by **linearising** the measurement model around the current state estimate.

### 4.2 State Representation

```
x = [px, py, vx, vy]ᵀ   (4D state per object)

px, py : position in ego frame [m]
vx, vy : velocity in ego frame [m/s]

P = 4×4 state covariance matrix
```

### 4.3 Predict Step (every cycle, 50 Hz)

Constant-velocity kinematic model:

```
dt = time since last predict

F = [1  0  dt  0 ]
    [0  1   0 dt ]
    [0  0   1  0 ]
    [0  0   0  1 ]

Process noise:
G = [dt²/2, dt²/2, dt, dt]ᵀ
Q = σ_a² * G * Gᵀ        (σ_a = 2.0 m/s² default)

Predict:
  x_pred = F * x
  P_pred = F * P * Fᵀ + Q
```

### 4.4 Update Step — Camera (linear)

Camera provides `(px, py)` directly (after unproject):

```
H_cam = [1  0  0  0]    (2×4 measurement matrix)
        [0  1  0  0]

R_cam = [σ_px²   0  ]   (measurement noise, σ=1.5m default)
        [  0   σ_py²]

Innovation:
  y = z_meas - H_cam * x_pred

Kalman gain:
  S = H * P * Hᵀ + R
  K = P * Hᵀ * S⁻¹

Update:
  x = x_pred + K * y
  P = (I - K * H) * P_pred
```

### 4.5 Update Step — Radar (non-linear EKF)

Radar provides `(ρ, φ, ρ̇)`:

```
h(x) = [√(px²+py²)           ]   (non-linear!)
       [atan2(py, px)          ]
       [(px*vx+py*vy)/√(px²+py²)]

Jacobian H_j (3×4):
  dh₁/dpx = px/ρ,    dh₁/dpy = py/ρ,    dh₁/dvx = 0, dh₁/dvy = 0
  dh₂/dpx = -py/ρ²,  dh₂/dpy = px/ρ²,  dh₂/dvx = 0, dh₂/dvy = 0
  dh₃/dpx = (vx*ρ² - px*(px*vx+py*vy)) / ρ³
  dh₃/dpy = (vy*ρ² - py*(px*vx+py*vy)) / ρ³
  dh₃/dvx = px/ρ
  dh₃/dvy = py/ρ

Azimuth innovation normalised to [-π, π] to handle angle wrap-around.
Proceed with same K formula using H_j instead of H.
```

### 4.6 Track Lifecycle

```
New detection → TENTATIVE track
    3 consecutive hits → CONFIRMED track (reported to planner)
    5 consecutive misses → track deleted

Gating:
  Mahalanobis distance: d = yᵀ * S⁻¹ * y
  Accept if d < threshold (default 9.21 = χ²(2, 0.99))
  Greedy nearest-neighbour assignment per frame
```

---

## 5. Path Planning

### 5.1 Behavior Decision

The planner reads `TrackedObject[]` and outputs a `BehaviorDecision` enum:

| Decision | Condition | Action |
|----------|-----------|--------|
| CRUISE | No object in corridor | Hold target speed |
| FOLLOW | Object at safe gap | ACC — maintain gap_target |
| EMERGENCY_BRAKE | TTC < 1.5 s | Full brake, AEB trajectory |
| LANE_CHANGE | Object slow + lane free | Lateral offset trajectory |
| STOP | Commanded or fault | Decelerate to 0 |

**TTC (Time-To-Collision)**:
```
TTC = distance / closing_speed
closing_speed = ego_v - object_vx  (relative, in ego X-axis)
AEB triggers if TTC < 1.5 s and closing_speed > 0
```

### 5.2 JMT (Jerk Minimising Trajectory)

Werling 2010 formulation. Minimises `∫₀ᵀ [d³s/dt³]² dt`.

Optimal solution is a **5th-order polynomial**:
```
s(t) = c₀ + c₁t + c₂t² + c₃t³ + c₄t⁴ + c₅t⁵

Boundary conditions:
  s(0) = s₀,   ṡ(0) = v₀,   s̈(0) = a₀
  s(T) = s₁,   ṡ(T) = v₁,   s̈(T) = a₁

c₀ = s₀,  c₁ = v₀,  c₂ = a₀/2

Solve 3×3 linear system for [c₃, c₄, c₅] using Cramer's rule.
```

**T (planning horizon)**: 2.0–4.0 seconds, selected to minimise total cost (jerk + time + deviation from target).

### 5.3 AEB Trajectory

Linear deceleration (no polynomial needed — time-critical):
```
a_brake = -v₀ / T_stop    where T_stop = v₀ / max_decel

Waypoints sampled every 0.1 s:
  v(t) = max(0, v₀ + a_brake * t)
  x(t) = v₀*t + ½*a_brake*t²
```

---

## 6. Vehicle Control

### 6.1 Longitudinal — PID Controller

Controls vehicle speed by commanding throttle (0–1) or brake (0–1):

```
e(t) = v_target - v_actual

u(t) = Kp * e + Ki * ∫e dt + Kd * de/dt

Anti-windup:
  integrator_sum = clamp(integrator_sum, -5.0, 5.0)

Output split:
  if u > 0: throttle = clamp(u, 0, 1), brake = 0
  if u < 0: brake = clamp(-u, 0, 1),  throttle = 0
```

Default gains: `Kp=0.5, Ki=0.1, Kd=0.05`

### 6.2 Lateral — Stanley Controller

Stanley method is widely used in autonomous vehicle research (DARPA Urban Challenge winner):

```
δ = ψ_e + atan(k * e_cte / max(v, v_min))

ψ_e    : heading error (vehicle heading vs nearest path tangent) [rad]
e_cte  : cross-track error (signed distance to nearest path point) [m]
k      : gain (default 0.5)
v      : vehicle speed [m/s]
v_min  : minimum speed for stability (default 1.0 m/s)

Output clamped to ±max_steer_rad (default ±0.5 rad = ±28.6°)
```

**Why Stanley vs Pure Pursuit?**
- Stanley converges faster at low speeds
- Naturally handles large heading errors
- Simple single-gain tuning

---

## 7. ADAS Features Summary

| Feature | Abbreviation | Implementation Location |
|---------|-------------|-------------------------|
| Automatic Emergency Braking | AEB | `PathPlanner::generateAEBTrajectory()` |
| Adaptive Cruise Control | ACC | `PathPlanner::computeFollowSpeed()` |
| Lane Keeping Assist | LKA | `VehicleController::computeLateral()` |
| Object Detection | OD | `ObjectDetector::process()` |
| Sensor Fusion | SF | `SensorFusion::update()` |
| Extended Kalman Filter | EKF | `SensorFusion` class |

---

## 8. Tuning Parameters

All tunable parameters are in `config/adas_params.yaml`:

```yaml
# EKF Noise
fusion:
  process_noise_accel: 2.0      # σ_a [m/s²]
  camera_pos_noise: 1.5         # σ_camera [m]
  radar_range_noise: 0.3        # σ_ρ [m]
  radar_azimuth_noise: 0.05     # σ_φ [rad]
  radar_doppler_noise: 0.3      # σ_ρ̇ [m/s]

# AEB
planning:
  aeb_ttc_threshold: 1.5        # [s]
  acc_target_gap: 15.0          # [m]
  max_decel: 8.0                # [m/s²]

# Control
control:
  pid_kp: 0.5
  pid_ki: 0.1
  pid_kd: 0.05
  stanley_k: 0.5
  max_steer_deg: 28.6
```

---

*See also*: [07_Multithreading_Realtime.md](07_Multithreading_Realtime.md) for timing constraints and task scheduling of the ADAS pipeline.
