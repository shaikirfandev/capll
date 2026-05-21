# 06 — Sensor Fusion

> **Core algorithm:** Kalman Filter (KF) + Extended Kalman Filter (EKF)  
> **Application:** Radar + camera object tracking, used in ACC, AEB, Highway Assist

---

## 6.1 Why Sensor Fusion?

```
Problem: No single sensor gives complete, accurate picture
  Camera: classification + lane detection, but noisy range, fails in fog/rain
  Radar: precise range + velocity, but no classification, ghost targets
  LiDAR: precise 3D, but expensive, fog scatter, no Doppler velocity

Solution: Sensor Fusion — combine multiple sensors to get best of all
  Output: Fused object list with: position (x,y), velocity (vx,vy), classification, confidence
  Algorithm: Kalman Filter family (linear KF, EKF, UKF)
```

---

## 6.2 Linear Kalman Filter Theory

```
State vector x = [range, range_rate]  (1D radar tracking)

PREDICT step (every cycle, even without measurement):
  x_k|k-1 = F * x_k-1|k-1          (state transition)
  P_k|k-1 = F * P_k-1|k-1 * F^T + Q  (covariance propagation)

  Where:
    F = [1  dt]  (constant velocity model)
        [0   1]
    Q = process noise matrix (model uncertainty)

UPDATE step (when measurement arrives):
  y = z - H * x_k|k-1               (innovation = measurement - predicted)
  S = H * P * H^T + R                (innovation covariance)
  K = P * H^T * S^-1                 (Kalman gain)
  x_k|k = x_k|k-1 + K * y           (updated state)
  P_k|k = (I - K*H) * P_k|k-1       (updated covariance)

  Where:
    H = [1  0]  (we observe range directly)
    R = measurement noise variance (radar accuracy)

Kalman Gain intuition:
  K = P * H^T / (H*P*H^T + R)
  
  If R is small (sensor is accurate) → K ≈ 1 → trust measurement
  If P is small (high confidence in model) → K ≈ 0 → trust prediction
  KF balances between model and measurement automatically
```

---

## 6.3 Extended Kalman Filter (EKF) for 2D Tracking

```
Problem: Radar measures in polar coordinates (range r, azimuth θ)
         State is in Cartesian coordinates (x, y, vx, vy)

Standard KF requires linear observation model — doesn't work here.
EKF solution: linearise using Jacobian (first-order Taylor expansion)

State: x = [px, py, vx, vy]  (Cartesian position + velocity)

Observation from radar:
  z = [r, θ] = [sqrt(px²+py²), atan2(py,px)]  ← non-linear

EKF linearisation:
  H_jacobian = dh/dx | at current x_hat
  
  H[0,0] = px/r,   H[0,1] = py/r,   H[0,2] = 0, H[0,3] = 0
  H[1,0] = -py/r², H[1,1] = px/r², H[1,2] = 0, H[1,3] = 0

EKF UPDATE:
  y = z - h(x_hat)              (use non-linear h, not H*x)
  S = H_j * P * H_j^T + R
  K = P * H_j^T * S^-1
  x = x + K * y
  P = (I - K*H_j) * P
```

---

## 6.4 Process Noise Tuning

```
Q matrix controls how fast the tracker responds to manoeuvres.
  Large Q → KF responds quickly to measurement changes (noisy output)
  Small Q → KF is smooth but slow to respond to sudden braking

Singer model (automotive standard):
  Q = σ_a² * [dt⁴/4  dt³/2]
              [dt³/2    dt²]
  
  σ_a = manoeuvre acceleration standard deviation
  Normal driving: σ_a = 2 m/s²
  Aggressive manoeuvre: σ_a = 4 m/s²

Practice: tune Q separately for longitudinal (range) and lateral (azimuth)
  Range rate changes fast (braking event) → higher Q_vx
  Lateral motion changes slowly → lower Q_vy
```

---

## 6.5 Camera + Radar Fusion Architecture

```
Level of fusion:
  RAW fusion (early): Fuse raw sensor data before object detection
    - Most accurate but computationally expensive
    - Used in premium L3+ systems (Nvidia Orin)
  
  OBJECT-level fusion (track-to-track):
    - Camera detects objects → camera object list (id, bbox, class, range_est)
    - Radar detects objects → radar object list (id, range, velocity, azimuth)
    - Fusion algorithm: associate camera + radar objects using Hungarian algorithm
    - Fused object: position from radar, classification from camera

Association step (data association):
  Gate: only associate if |radar_range - camera_range_est| < 5m AND |azimuth| < 3°
  Cost matrix: build N×M matrix of Mahalanobis distances
  Solve: Hungarian algorithm (O(n³)) or greedy assignment (O(n²) for small N)

In practice (AUTOSAR Adaptive + SOME/IP):
  Camera SWC publishes: CameraObjectList (SOME/IP service)
  Radar SWC publishes:  RadarObjectList (SOME/IP service)
  Fusion SWC subscribes to both → outputs FusedObjectList
```

---

## 6.6 Interview Questions

```
L1:
  Q: What is a Kalman Filter in simple terms?
  A: A Kalman Filter is an algorithm that maintains a probability distribution
     (a Gaussian: mean + variance) over a system state, and updates it
     optimally when new measurements arrive.
     It balances: "how much do I trust my physics model (prediction)?"
     vs "how much do I trust the sensor (update)?"
     
     In ADAS: tracks radar object. Prediction = constant velocity model.
     Update = new radar distance measurement. Output = smooth, low-noise estimate.

  Q: What is the difference between KF and EKF?
  A: KF: linear system + linear observations. Optimal (minimum variance) estimator.
     EKF: non-linear system or observations. Linearises using Jacobian.
     Not optimal (first-order approximation introduces errors).
     UKF (Unscented KF): better than EKF for highly non-linear systems — uses
     sigma points to propagate distribution. More compute-intensive.

L2:
  Q: What happens if your Kalman Filter diverges?
  A: Divergence = estimated state drifts far from truth. Covariance shrinks to near
     zero (filter "thinks" it knows exactly where the object is but is wrong).
     Causes:
     1. Wrong Q or R matrices (poor noise modeling)
     2. Sensor bias (radar range offset not calibrated)
     3. Wrong motion model (vehicle cornering but KF uses straight-line model)
     Detection: Monitor innovation y. If |y| >> sqrt(S) consistently → divergence.
     Fix: 
       Adaptive Q (increase if innovation is consistently large)
       Re-initialise filter when innovation exceeds 5σ threshold
       IMM filter (multiple models: straight, turning, braking)

  Q: How does the tracker handle an object that momentarily disappears?
  A: Coast prediction: KF continues predicting state using motion model even without
     measurement. Coast counter increments each missed detection cycle.
     If coast_count > max_coast_cycles (e.g., 5 cycles × 50ms = 250ms):
       → Mark track as LOST, deallocate object slot
     When object reappears: gate check — if predicted position is close to new
     measurement → re-associate with existing track (ghost track avoidance)

L3:
  Q: How do you validate the sensor fusion accuracy?
  A: Ground truth comparison using reference equipment:
     GNSS+IMU with centimetre accuracy (NovAtel SPAN, Applanix POS LV)
     LiDAR point cloud annotation as ground truth for camera/radar output
     
     Metrics:
       MOTA (Multi-Object Tracking Accuracy): accounts for false positives, misses, ID switches
       MOTP (Multi-Object Tracking Precision): position accuracy of matched tracks
       ID-switch rate: how often does the tracker lose object ID (bad for ACC)
     
     Validation scenarios:
       High-way following: accuracy vs GPS-truth of lead vehicle position
       Cut-in: time from object appearance to stable track (target: < 200ms)
       Static object: track stability for parked cars
       Night: camera confidence degradation + radar-only fallback
```
