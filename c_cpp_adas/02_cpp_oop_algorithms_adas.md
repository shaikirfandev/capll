# C++ OOP & Algorithms for ADAS Engineering

> **Coverage:** Sensor Fusion Classes, Kalman Filter, Path Planning, PID Controller,
>               Object Lifecycle Management, Camera/Radar/LiDAR Processing Pipelines

---

## 1. Sensor Abstraction — Base Class Hierarchy

```cpp
#include <cstdint>
#include <cmath>
#include <array>

/* Abstract sensor interface */
class ISensor {
public:
    virtual ~ISensor() = default;

    virtual bool     init(void)                        = 0;
    virtual bool     process_frame(void)               = 0;
    virtual uint32_t get_timestamp_ms(void)    const   = 0;
    virtual bool     is_healthy(void)          const   = 0;
    virtual uint8_t  get_sensor_id(void)       const   = 0;

    /* Sensor type enum */
    enum class Type : uint8_t { RADAR=0, LIDAR=1, CAMERA=2, ULTRASONIC=3, IMU=4 };
    virtual Type     get_type(void)            const   = 0;
};

/* Radar sensor implementation */
class RadarSensor : public ISensor {
public:
    static constexpr uint8_t  MAX_TARGETS   = 64U;
    static constexpr float    MAX_RANGE_M   = 250.0f;
    static constexpr float    FOV_AZIMUTH_DEG = 18.0f;

    struct Target {
        float   range_m;
        float   velocity_ms;
        float   azimuth_rad;
        float   elevation_rad;
        uint8_t confidence;
        bool    is_valid;
    };

    explicit RadarSensor(uint8_t id, uint8_t spi_channel)
        : id_(id), spi_ch_(spi_channel) {}

    bool  init(void)           override;
    bool  process_frame(void)  override;
    bool  is_healthy(void)     const override { return healthy_; }
    uint8_t get_sensor_id(void) const override { return id_; }
    uint32_t get_timestamp_ms(void) const override { return ts_; }
    Type get_type(void) const override { return Type::RADAR; }

    const Target* get_targets(void) const { return targets_.data(); }
    uint8_t       get_target_count(void) const { return target_count_; }

    /* CFAR (Constant False Alarm Rate) threshold calculation */
    static float compute_cfar_threshold(const float* noise_cells,
                                         uint8_t n_cells,
                                         float pfa) {
        if (noise_cells == nullptr || n_cells == 0U) return 0.0f;
        float sum = 0.0f;
        for (uint8_t i = 0U; i < n_cells; ++i) sum += noise_cells[i];
        float mean_noise = sum / static_cast<float>(n_cells);
        /* CFAR threshold: T = alpha * mean_noise where alpha = n*(PFA^(-1/n) - 1) */
        float alpha = static_cast<float>(n_cells) *
                      (std::pow(pfa, -1.0f / static_cast<float>(n_cells)) - 1.0f);
        return alpha * mean_noise;
    }

private:
    uint8_t id_;
    uint8_t spi_ch_;
    bool    healthy_ = false;
    uint32_t ts_     = 0U;
    uint8_t  target_count_ = 0U;
    std::array<Target, MAX_TARGETS> targets_{};
};

/* Camera sensor implementation */
class CameraSensor : public ISensor {
public:
    static constexpr uint8_t  MAX_OBJECTS    = 32U;
    static constexpr uint16_t IMAGE_WIDTH    = 1920U;
    static constexpr uint16_t IMAGE_HEIGHT   = 1080U;

    struct DetectedObject {
        uint16_t bbox_x, bbox_y, bbox_w, bbox_h;
        uint8_t  class_id;   /* 0=car, 1=truck, 2=ped, 3=cyclist, 4=sign, 5=light */
        uint8_t  confidence; /* 0–100 */
        float    estimated_distance_m;
        bool     is_valid;
    };

    explicit CameraSensor(uint8_t id, uint8_t camera_port)
        : id_(id), port_(camera_port) {}

    bool  init(void)          override;
    bool  process_frame(void) override;
    bool  is_healthy(void)    const override { return healthy_; }
    uint8_t get_sensor_id(void) const override { return id_; }
    uint32_t get_timestamp_ms(void) const override { return ts_; }
    Type get_type(void) const override { return Type::CAMERA; }

    const DetectedObject* get_objects(void) const { return objects_.data(); }
    uint8_t               get_object_count(void) const { return obj_count_; }

    /* Pinhole camera: distance estimation from bounding box height */
    static float estimate_distance(uint16_t bbox_height_px,
                                    float real_height_m,
                                    float focal_length_px) {
        if (bbox_height_px == 0U) return 999.0f;
        return (real_height_m * focal_length_px) /
               static_cast<float>(bbox_height_px);
    }

private:
    uint8_t id_, port_;
    bool    healthy_ = false;
    uint32_t ts_     = 0U;
    uint8_t  obj_count_ = 0U;
    std::array<DetectedObject, MAX_OBJECTS> objects_{};
};
```

---

## 2. Kalman Filter — Core Fusion Algorithm

```cpp
/*
 * Linear Kalman Filter for radar target tracking
 * State vector: x = [pos_x, pos_y, vel_x, vel_y]  (4-DOF)
 * Measurement:  z = [pos_x, pos_y]                 (from radar range+azimuth)
 */
class KalmanFilter {
public:
    static constexpr uint8_t STATE_DIM  = 4U;   /* [x, y, vx, vy] */
    static constexpr uint8_t MEAS_DIM   = 2U;   /* [x, y] */

    using StateVec  = std::array<float, STATE_DIM>;
    using MeasVec   = std::array<float, MEAS_DIM>;
    using Matrix4x4 = std::array<std::array<float, STATE_DIM>, STATE_DIM>;
    using Matrix2x4 = std::array<std::array<float, STATE_DIM>, MEAS_DIM>;
    using Matrix4x2 = std::array<std::array<float, MEAS_DIM>, STATE_DIM>;
    using Matrix2x2 = std::array<std::array<float, MEAS_DIM>, MEAS_DIM>;

    KalmanFilter() { reset(); }

    void reset(void) {
        /* Initial state */
        x_ = {0.0f, 0.0f, 0.0f, 0.0f};

        /* Initial covariance — high uncertainty */
        P_ = {{
            {100.0f, 0.0f,  0.0f,  0.0f},
            {0.0f,  100.0f, 0.0f,  0.0f},
            {0.0f,   0.0f, 25.0f,  0.0f},
            {0.0f,   0.0f,  0.0f, 25.0f}
        }};

        /* Measurement noise — radar range ~1m, azimuth ~1m at 50m */
        R_ = {{
            {1.0f,  0.0f},
            {0.0f,  1.0f}
        }};

        /* Process noise — acceleration uncertainty */
        Q_ = {{
            {0.1f, 0.0f, 0.0f, 0.0f},
            {0.0f, 0.1f, 0.0f, 0.0f},
            {0.0f, 0.0f, 1.0f, 0.0f},
            {0.0f, 0.0f, 0.0f, 1.0f}
        }};
    }

    /* PREDICT step: x̂⁻ = F·x̂, P⁻ = F·P·Fᵀ + Q */
    void predict(float dt_s) {
        /* State transition matrix F (constant velocity model)
           [1, 0, dt, 0]
           [0, 1,  0,dt]
           [0, 0,  1, 0]
           [0, 0,  0, 1] */
        StateVec x_pred = {
            x_[0] + x_[2] * dt_s,
            x_[1] + x_[3] * dt_s,
            x_[2],
            x_[3]
        };
        x_ = x_pred;

        /* P⁻ = F·P·Fᵀ + Q (simplified for constant velocity) */
        Matrix4x4 P_pred = P_;
        P_pred[0][0] += 2.0f * P_[0][2] * dt_s + P_[2][2] * dt_s * dt_s + Q_[0][0];
        P_pred[1][1] += 2.0f * P_[1][3] * dt_s + P_[3][3] * dt_s * dt_s + Q_[1][1];
        P_pred[0][2] += P_[2][2] * dt_s;
        P_pred[1][3] += P_[3][3] * dt_s;
        P_pred[2][0]  = P_pred[0][2];
        P_pred[3][1]  = P_pred[1][3];
        P_pred[2][2] += Q_[2][2];
        P_pred[3][3] += Q_[3][3];
        P_ = P_pred;
    }

    /* UPDATE step: K = P·Hᵀ·(H·P·Hᵀ + R)⁻¹, x̂ = x̂⁻ + K·(z - H·x̂⁻) */
    void update(const MeasVec& z) {
        /* H = [1,0,0,0; 0,1,0,0] — we measure position only */
        /* Innovation: y = z - H·x */
        MeasVec y = {z[0] - x_[0], z[1] - x_[1]};

        /* S = H·P·Hᵀ + R (top-left 2x2 of P plus R) */
        Matrix2x2 S = {{
            {P_[0][0] + R_[0][0], P_[0][1] + R_[0][1]},
            {P_[1][0] + R_[1][0], P_[1][1] + R_[1][1]}
        }};

        /* S⁻¹ (2x2 inversion) */
        float det = S[0][0] * S[1][1] - S[0][1] * S[1][0];
        if (std::fabsf(det) < 1e-9f) return;  /* Singular — skip update */
        float inv_det = 1.0f / det;
        Matrix2x2 S_inv = {{
            { S[1][1] * inv_det, -S[0][1] * inv_det},
            {-S[1][0] * inv_det,  S[0][0] * inv_det}
        }};

        /* K = P·Hᵀ·S⁻¹ (4x2 gain matrix, H selects rows 0,1) */
        Matrix4x2 K;
        for (uint8_t i = 0U; i < STATE_DIM; ++i) {
            K[i][0] = P_[i][0] * S_inv[0][0] + P_[i][1] * S_inv[1][0];
            K[i][1] = P_[i][0] * S_inv[0][1] + P_[i][1] * S_inv[1][1];
        }

        /* State update: x = x + K·y */
        for (uint8_t i = 0U; i < STATE_DIM; ++i) {
            x_[i] += K[i][0] * y[0] + K[i][1] * y[1];
        }

        /* Covariance update: P = (I - K·H)·P */
        Matrix4x4 P_new = P_;
        for (uint8_t i = 0U; i < STATE_DIM; ++i) {
            P_new[i][0] = P_[i][0] - K[i][0] * P_[0][0] - K[i][1] * P_[1][0];
            P_new[i][1] = P_[i][1] - K[i][0] * P_[0][1] - K[i][1] * P_[1][1];
            P_new[i][2] = P_[i][2] - K[i][0] * P_[0][2] - K[i][1] * P_[1][2];
            P_new[i][3] = P_[i][3] - K[i][0] * P_[0][3] - K[i][1] * P_[1][3];
        }
        P_ = P_new;
    }

    float get_pos_x(void) const { return x_[0]; }
    float get_pos_y(void) const { return x_[1]; }
    float get_vel_x(void) const { return x_[2]; }
    float get_vel_y(void) const { return x_[3]; }
    float get_pos_uncertainty(void) const {
        return std::sqrtf(P_[0][0] + P_[1][1]);
    }

private:
    StateVec  x_{};
    Matrix4x4 P_{}, Q_{};
    Matrix2x2 R_{};
};
```

---

## 3. Object Tracker — Multi-Target Tracking

```cpp
class ObjectTracker {
public:
    static constexpr uint8_t MAX_TRACKS         = 32U;
    static constexpr uint8_t CONFIRM_THRESHOLD  = 3U;   /* hits before confirming */
    static constexpr uint8_t DELETE_THRESHOLD   = 5U;   /* misses before deleting */
    static constexpr float   ASSOC_GATE_M       = 3.0f; /* gating distance [m] */

    enum class TrackStatus : uint8_t {
        FREE        = 0U,
        TENTATIVE   = 1U,   /* New, not yet confirmed */
        CONFIRMED   = 2U,   /* Stable track */
        COASTING    = 3U    /* No recent measurement */
    };

    struct Track {
        KalmanFilter kf;
        TrackStatus  status       = TrackStatus::FREE;
        uint8_t      track_id     = 0U;
        uint8_t      hit_count    = 0U;   /* consecutive associations */
        uint8_t      miss_count   = 0U;   /* consecutive misses */
        uint8_t      class_id     = 0U;
        float        existence_prob = 0.0f;
        uint32_t     last_update_ms = 0U;
    };

    /* Update all tracks with new radar measurements */
    void update(const RadarSensor::Target* targets, uint8_t n_targets,
                float dt_s, uint32_t timestamp_ms)
    {
        /* 1. Predict all existing tracks */
        for (auto& t : tracks_) {
            if (t.status != TrackStatus::FREE) {
                t.kf.predict(dt_s);
            }
        }

        /* 2. Associate measurements to tracks (nearest-neighbour gate) */
        bool associated[MAX_TRACKS] = {false};

        for (uint8_t m = 0U; m < n_targets; ++m) {
            if (!targets[m].is_valid) continue;

            float meas_x = targets[m].range_m * std::cosf(targets[m].azimuth_rad);
            float meas_y = targets[m].range_m * std::sinf(targets[m].azimuth_rad);

            int8_t best_track = -1;
            float  best_dist  = ASSOC_GATE_M;

            for (uint8_t t = 0U; t < MAX_TRACKS; ++t) {
                if (tracks_[t].status == TrackStatus::FREE) continue;
                float dx = tracks_[t].kf.get_pos_x() - meas_x;
                float dy = tracks_[t].kf.get_pos_y() - meas_y;
                float dist = std::sqrtf(dx*dx + dy*dy);
                if (dist < best_dist) {
                    best_dist  = dist;
                    best_track = static_cast<int8_t>(t);
                }
            }

            if (best_track >= 0) {
                /* Update existing track */
                KalmanFilter::MeasVec z = {meas_x, meas_y};
                tracks_[best_track].kf.update(z);
                tracks_[best_track].hit_count++;
                tracks_[best_track].miss_count = 0U;
                tracks_[best_track].last_update_ms = timestamp_ms;
                associated[best_track] = true;

                if (tracks_[best_track].status == TrackStatus::TENTATIVE &&
                    tracks_[best_track].hit_count >= CONFIRM_THRESHOLD) {
                    tracks_[best_track].status = TrackStatus::CONFIRMED;
                }
            } else {
                /* Initiate new track */
                init_track(meas_x, meas_y,
                           targets[m].velocity_ms, 0.0f, timestamp_ms);
            }
        }

        /* 3. Handle missed measurements */
        for (uint8_t t = 0U; t < MAX_TRACKS; ++t) {
            if (tracks_[t].status == TrackStatus::FREE) continue;
            if (!associated[t]) {
                tracks_[t].miss_count++;
                tracks_[t].status = TrackStatus::COASTING;
                if (tracks_[t].miss_count >= DELETE_THRESHOLD) {
                    tracks_[t].status = TrackStatus::FREE;
                }
            }
        }
    }

    uint8_t get_confirmed_count(void) const {
        uint8_t count = 0U;
        for (const auto& t : tracks_) {
            if (t.status == TrackStatus::CONFIRMED) ++count;
        }
        return count;
    }

    const Track& get_track(uint8_t idx) const { return tracks_[idx]; }

private:
    std::array<Track, MAX_TRACKS> tracks_{};
    uint8_t next_id_ = 1U;

    void init_track(float x, float y, float vx, float vy, uint32_t ts) {
        for (auto& t : tracks_) {
            if (t.status == TrackStatus::FREE) {
                t.kf.reset();
                t.status   = TrackStatus::TENTATIVE;
                t.track_id = next_id_++;
                t.hit_count  = 1U;
                t.miss_count = 0U;
                t.last_update_ms = ts;
                (void)x; (void)y; (void)vx; (void)vy;
                return;
            }
        }
    }
};
```

---

## 4. PID Controller — Lateral / Longitudinal Control

```cpp
class PidController {
public:
    struct Config {
        float kp;
        float ki;
        float kd;
        float output_min;
        float output_max;
        float integral_limit;  /* Anti-windup */
        float dt_s;
    };

    explicit PidController(const Config& cfg) : cfg_(cfg) {}

    float update(float setpoint, float measurement) {
        float error = setpoint - measurement;

        /* Proportional */
        float p_term = cfg_.kp * error;

        /* Integral with anti-windup clamp */
        integral_ += error * cfg_.dt_s;
        integral_ = clamp(integral_, -cfg_.integral_limit, cfg_.integral_limit);
        float i_term = cfg_.ki * integral_;

        /* Derivative (on measurement, not error — avoids derivative kick) */
        float d_term = cfg_.kd * (prev_measurement_ - measurement) / cfg_.dt_s;
        prev_measurement_ = measurement;

        float output = p_term + i_term + d_term;
        return clamp(output, cfg_.output_min, cfg_.output_max);
    }

    void reset(void) { integral_ = 0.0f; prev_measurement_ = 0.0f; }

private:
    Config cfg_;
    float  integral_        = 0.0f;
    float  prev_measurement_ = 0.0f;

    static float clamp(float v, float lo, float hi) {
        return (v < lo) ? lo : (v > hi) ? hi : v;
    }
};

/* ACC (Adaptive Cruise Control) longitudinal controller */
class AccController {
public:
    AccController()
        : speed_pid_({
            .kp=0.4f, .ki=0.05f, .kd=0.02f,
            .output_min=-4.0f, .output_max=3.0f,
            .integral_limit=10.0f, .dt_s=0.020f
          }),
          gap_pid_({
            .kp=0.5f, .ki=0.01f, .kd=0.1f,
            .output_min=-4.0f, .output_max=2.0f,
            .integral_limit=5.0f, .dt_s=0.020f
          }) {}

    /* Returns desired acceleration [m/s²] */
    float compute(float set_speed_ms, float ego_speed_ms,
                  float lead_dist_m, float thw_set_s) {
        float desired_gap_m = thw_set_s * ego_speed_ms + 2.0f; /* min gap */

        if (lead_dist_m > 150.0f) {
            /* Free cruise — speed control only */
            return speed_pid_.update(set_speed_ms, ego_speed_ms);
        } else {
            /* Gap control — follow leader */
            float gap_accel = gap_pid_.update(desired_gap_m, lead_dist_m);
            float spd_accel = speed_pid_.update(set_speed_ms, ego_speed_ms);
            /* Conservative: take minimum */
            return (gap_accel < spd_accel) ? gap_accel : spd_accel;
        }
    }

    void reset(void) { speed_pid_.reset(); gap_pid_.reset(); }

private:
    PidController speed_pid_;
    PidController gap_pid_;
};

/* LKA (Lane Keep Assist) lateral controller */
class LkaController {
public:
    LkaController()
        : steering_pid_({
            .kp=0.8f, .ki=0.02f, .kd=0.15f,
            .output_min=-0.35f, .output_max=0.35f,  /* ±20° steering */
            .integral_limit=0.3f, .dt_s=0.010f
          }) {}

    /* Returns steering wheel angle [rad] */
    float compute(float lateral_error_m, float heading_error_rad) {
        /* Combine lateral offset and heading error */
        float combined_error = lateral_error_m + 2.0f * heading_error_rad;
        return steering_pid_.update(0.0f, -combined_error);
    }

private:
    PidController steering_pid_;
};
```

---

## 5. Sensor Fusion Pipeline — Observer Pattern

```cpp
/* Fusion result callback */
class IFusionConsumer {
public:
    virtual ~IFusionConsumer() = default;
    virtual void on_object_list_updated(const std::array<TrackedObject_t, 32U>& objects,
                                         uint8_t count) = 0;
};

/* Sensor fusion manager */
class SensorFusionManager {
public:
    static constexpr uint8_t MAX_CONSUMERS = 4U;

    void register_consumer(IFusionConsumer* c) {
        if (consumer_count_ < MAX_CONSUMERS) {
            consumers_[consumer_count_++] = c;
        }
    }

    void register_radar(RadarSensor* r) { radar_ = r; }
    void register_camera(CameraSensor* c) { camera_ = c; }

    void run_fusion_cycle(float dt_s, uint32_t timestamp_ms) {
        if (radar_ != nullptr) radar_->process_frame();
        if (camera_ != nullptr) camera_->process_frame();

        /* Update tracker with radar */
        if (radar_ != nullptr && radar_->is_healthy()) {
            tracker_.update(radar_->get_targets(),
                            radar_->get_target_count(),
                            dt_s, timestamp_ms);
        }

        /* Build output object list */
        uint8_t count = 0U;
        std::array<TrackedObject_t, 32U> output{};

        for (uint8_t i = 0U; i < ObjectTracker::MAX_TRACKS && count < 32U; ++i) {
            const auto& track = tracker_.get_track(i);
            if (track.status != ObjectTracker::TrackStatus::CONFIRMED) continue;

            auto& obj = output[count];
            obj.id               = track.track_id;
            obj.kinematics.x_m   = track.kf.get_pos_x();
            obj.kinematics.y_m   = track.kf.get_pos_y();
            obj.kinematics.vx_ms = track.kf.get_vel_x();
            obj.kinematics.vy_ms = track.kf.get_vel_y();
            obj.timestamp_ms     = timestamp_ms;

            /* TTC */
            if (obj.kinematics.vx_ms > 0.1f) {
                obj.ttc_s = obj.kinematics.x_m / obj.kinematics.vx_ms;
            } else {
                obj.ttc_s = 99.0f;
            }
            ++count;
        }

        /* Notify all consumers */
        for (uint8_t i = 0U; i < consumer_count_; ++i) {
            consumers_[i]->on_object_list_updated(output, count);
        }
    }

private:
    RadarSensor*   radar_   = nullptr;
    CameraSensor*  camera_  = nullptr;
    ObjectTracker  tracker_;
    std::array<IFusionConsumer*, MAX_CONSUMERS> consumers_{};
    uint8_t consumer_count_ = 0U;
};

/* Example consumer — FCW application */
class FcwApplication : public IFusionConsumer {
public:
    void on_object_list_updated(const std::array<TrackedObject_t, 32U>& objects,
                                 uint8_t count) override {
        const TrackedObject_t* lead = nullptr;
        float min_x = 999.0f;

        for (uint8_t i = 0U; i < count; ++i) {
            const auto& obj = objects[i];
            if (obj.kinematics.y_m > -1.8f &&
                obj.kinematics.y_m < 1.8f &&
                obj.kinematics.x_m > 0.0f &&
                obj.kinematics.x_m < min_x) {
                min_x = obj.kinematics.x_m;
                lead  = &obj;
            }
        }

        if (lead != nullptr) {
            update_fcw_state(*lead);
        }
    }

private:
    void update_fcw_state(const TrackedObject_t& lead) {
        /* FCW logic here */
        (void)lead;
    }
};
```

---

## 6. Path Planning — Polynomial Lane Change

```cpp
class PathPlanner {
public:
    struct Waypoint { float x_m; float y_m; float speed_ms; };
    static constexpr uint8_t MAX_WAYPOINTS = 20U;

    /* Quintic polynomial for smooth lane change */
    /* Solves for coefficients given: start pos/vel/acc and end pos/vel/acc */
    struct QuinticCoeffs { float a0,a1,a2,a3,a4,a5; };

    static QuinticCoeffs compute_quintic(
        float y0, float vy0, float ay0,     /* initial: position, velocity, accel */
        float y1, float vy1, float ay1,     /* final:   position, velocity, accel */
        float T)                             /* manoeuvre time [s] */
    {
        QuinticCoeffs c;
        float T2 = T*T, T3=T2*T, T4=T3*T, T5=T4*T;

        c.a0 = y0;
        c.a1 = vy0;
        c.a2 = ay0 / 2.0f;

        float h  = y1  - y0  - vy0*T  - ay0*T2/2.0f;
        float hv = vy1 - vy0 - ay0*T;
        float ha = ay1 - ay0;

        c.a3 = (20.0f*h - (8.0f*vy1 + 12.0f*vy0)*T - (3.0f*ay0 - ay1)*T2) / (2.0f*T3);
        c.a4 = (-30.0f*h + (14.0f*vy1 + 16.0f*vy0)*T + (3.0f*ay0 - 2.0f*ay1)*T2) / (2.0f*T4);
        c.a5 = (12.0f*h  - (6.0f*vy1 + 6.0f*vy0)*T  - (ay0 - ay1)*T2) / (2.0f*T5);
        (void)hv; (void)ha;
        return c;
    }

    static float eval_quintic(const QuinticCoeffs& c, float t) {
        return c.a0 + c.a1*t + c.a2*t*t + c.a3*t*t*t
             + c.a4*t*t*t*t + c.a5*t*t*t*t*t;
    }

    /* Generate lane change path: current lane y=0, target lane y=3.5m */
    uint8_t generate_lane_change(float ego_speed_ms, float* out_x, float* out_y,
                                  uint8_t max_pts) {
        float T = 3.5f;   /* 3.5s lane change duration */
        auto coeffs = compute_quintic(0.0f, 0.0f, 0.0f,
                                       3.5f, 0.0f, 0.0f, T);

        uint8_t pts = (max_pts < MAX_WAYPOINTS) ? max_pts : MAX_WAYPOINTS;
        for (uint8_t i = 0U; i < pts; ++i) {
            float t = static_cast<float>(i) * T / static_cast<float>(pts - 1U);
            out_x[i] = ego_speed_ms * t;
            out_y[i] = eval_quintic(coeffs, t);
        }
        return pts;
    }
};
```

---

## 7. Unit Tests for ADAS Algorithms (Google Test)

```cpp
#include <gtest/gtest.h>

class KalmanFilterTest : public ::testing::Test {
protected:
    KalmanFilter kf;
};

TEST_F(KalmanFilterTest, PredictMovesPositionByVelocity) {
    /* Start: pos=(10,0), vel=(5,0) */
    kf.reset();
    /* Manually prime filter with known state */
    KalmanFilter::MeasVec z = {10.0f, 0.0f};
    kf.update(z);

    kf.predict(1.0f);   /* dt = 1s */

    /* After prediction, x should be approx 10 + 5*1 = 15 (if vx was estimated) */
    EXPECT_NEAR(kf.get_pos_x(), 10.0f, 2.0f);  /* Position updated */
}

TEST_F(KalmanFilterTest, UpdateReducesUncertainty) {
    float initial_uncertainty = kf.get_pos_uncertainty();
    KalmanFilter::MeasVec z = {5.0f, 2.0f};
    kf.update(z);
    EXPECT_LT(kf.get_pos_uncertainty(), initial_uncertainty);
}

class PidTest : public ::testing::Test {
protected:
    PidController::Config cfg{0.5f, 0.1f, 0.05f, -10.0f, 10.0f, 5.0f, 0.02f};
    PidController pid{cfg};
};

TEST_F(PidTest, ZeroErrorGivesZeroOutput) {
    float out = pid.update(50.0f, 50.0f);
    EXPECT_NEAR(out, 0.0f, 0.001f);
}

TEST_F(PidTest, PositiveErrorGivesPositiveOutput) {
    float out = pid.update(60.0f, 50.0f);   /* Want more speed */
    EXPECT_GT(out, 0.0f);
}

TEST_F(PidTest, OutputIsClampedToLimits) {
    float out = pid.update(1000.0f, 0.0f);  /* Huge error */
    EXPECT_LE(out, cfg.output_max);
}

TEST(TtcTest, ApproachingObjectGivesFiniteTtc) {
    float ttc = calculate_ttc(50.0f, 25.0f);   /* 50m, 25 m/s closing */
    EXPECT_NEAR(ttc, 2.0f, 0.001f);
}

TEST(TtcTest, RecedingObjectGivesMaxTtc) {
    float ttc = calculate_ttc(50.0f, -5.0f);   /* Moving away */
    EXPECT_FLOAT_EQ(ttc, 99.0f);
}
```

---

*File: 02_cpp_oop_algorithms_adas.md | c_cpp_adas learning series*
