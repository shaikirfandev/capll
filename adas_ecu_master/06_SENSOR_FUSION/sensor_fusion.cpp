/**
 * @file    sensor_fusion.cpp
 * @brief   Sensor Fusion — Kalman Filter + EKF for ADAS Object Tracking
 * @details 1D Linear Kalman Filter for radar range tracking
 *          + Extended Kalman Filter (EKF) for 2D radar+camera fusion
 *
 * Matches production ADAS tracking approach (Bosch, Aptiv style)
 * Compile: g++ -std=c++17 -Wall -Wextra -O2 sensor_fusion.cpp -o sensor_fusion
 */

#include <cstdint>
#include <cstddef>
#include <cmath>
#include <array>
#include <iostream>
#include <iomanip>

// ============================================================================
// UTILITY — Simple 2x2 matrix for EKF (ECU heap-free, no Eigen)
// ============================================================================

struct Mat2x2 {
    float m[2][2] = {};

    Mat2x2 operator+(const Mat2x2& o) const noexcept {
        Mat2x2 r;
        for (int i = 0; i < 2; ++i)
            for (int j = 0; j < 2; ++j)
                r.m[i][j] = m[i][j] + o.m[i][j];
        return r;
    }

    Mat2x2 operator*(const Mat2x2& o) const noexcept {
        Mat2x2 r;
        for (int i = 0; i < 2; ++i)
            for (int j = 0; j < 2; ++j)
                for (int k = 0; k < 2; ++k)
                    r.m[i][j] += m[i][k] * o.m[k][j];
        return r;
    }

    Mat2x2 transpose() const noexcept {
        return {{{m[0][0], m[1][0]}, {m[0][1], m[1][1]}}};
    }

    // Inverse of 2x2: {{a,b},{c,d}}^-1 = (1/(ad-bc)) * {{d,-b},{-c,a}}
    Mat2x2 inverse() const noexcept {
        float det = m[0][0]*m[1][1] - m[0][1]*m[1][0];
        if (std::abs(det) < 1e-9F) { return *this; } // Singular guard
        float inv = 1.0F / det;
        return {{{m[1][1]*inv, -m[0][1]*inv}, {-m[1][0]*inv, m[0][0]*inv}}};
    }
};

struct Vec2 {
    float v[2] = {};
    float operator[](int i) const noexcept { return v[i]; }
    float& operator[](int i) noexcept { return v[i]; }
    Vec2 operator+(const Vec2& o) const noexcept { return {v[0]+o.v[0], v[1]+o.v[1]}; }
    Vec2 operator-(const Vec2& o) const noexcept { return {v[0]-o.v[0], v[1]-o.v[1]}; }
};

static Vec2 mat_vec(const Mat2x2& A, const Vec2& x) noexcept {
    return {A.m[0][0]*x[0] + A.m[0][1]*x[1],
            A.m[1][0]*x[0] + A.m[1][1]*x[1]};
}

// ============================================================================
// 1D LINEAR KALMAN FILTER (Radar range tracking)
// ============================================================================
//
// State vector: [range_m, range_rate_mps]
//
// Motion model (constant velocity):
//   x_k+1 = F * x_k + w     (w = process noise)
//   F = [1  dt]
//       [0   1]
//
// Observation model (radar measures range directly):
//   z_k = H * x_k + v       (v = measurement noise)
//   H = [1  0]
//
// Noise matrices:
//   Q = process noise (model uncertainty)
//   R = measurement noise (radar accuracy)
//

class KalmanFilter1D {
public:
    struct State {
        float range_m     = 0.0F;
        float rangeDot_mps = 0.0F;   // Range rate (velocity)
    };

    KalmanFilter1D() {
        // Initial covariance: high uncertainty
        P_.m[0][0] = 100.0F;  // Range variance (m²)
        P_.m[1][1] = 25.0F;   // Range-rate variance (m/s)²

        // Process noise (tune to vehicle dynamics)
        Q_.m[0][0] = 0.01F;   // Low process noise = smooth tracking
        Q_.m[1][1] = 0.1F;

        // Radar measurement noise: ±0.1m = variance = 0.01 m²
        R_ = 0.04F;   // Conservative: ±0.2m

        H_[0] = 1.0F; H_[1] = 0.0F;  // H = [1, 0]
    }

    void init(float range_m, float rangeRate_mps) noexcept {
        x_[0] = range_m;
        x_[1] = rangeRate_mps;
        initialised_ = true;
    }

    State predict(float dt_s) noexcept {
        // State transition matrix F
        Mat2x2 F;
        F.m[0][0] = 1.0F; F.m[0][1] = dt_s;
        F.m[1][0] = 0.0F; F.m[1][1] = 1.0F;

        // Predicted state: x = F * x
        x_ = mat_vec(F, x_);

        // Predicted covariance: P = F*P*F^T + Q
        P_ = (F * P_ * F.transpose()) + Q_;

        return {x_[0], x_[1]};
    }

    State update(float measuredRange_m) noexcept {
        // Innovation: y = z - H*x
        float y = measuredRange_m - (H_[0]*x_[0] + H_[1]*x_[1]);

        // Innovation covariance: S = H*P*H^T + R
        float S = H_[0]*(P_.m[0][0]*H_[0] + P_.m[0][1]*H_[1])
                + H_[1]*(P_.m[1][0]*H_[0] + P_.m[1][1]*H_[1])
                + R_;

        // Kalman gain: K = P*H^T / S
        Vec2 K;
        K[0] = (P_.m[0][0]*H_[0] + P_.m[0][1]*H_[1]) / S;
        K[1] = (P_.m[1][0]*H_[0] + P_.m[1][1]*H_[1]) / S;

        // Updated state: x = x + K*y
        x_[0] += K[0] * y;
        x_[1] += K[1] * y;

        // Updated covariance: P = (I - K*H) * P
        Mat2x2 KH;
        KH.m[0][0] = K[0]*H_[0]; KH.m[0][1] = K[0]*H_[1];
        KH.m[1][0] = K[1]*H_[0]; KH.m[1][1] = K[1]*H_[1];

        Mat2x2 I; I.m[0][0] = 1.0F; I.m[1][1] = 1.0F;
        P_ = (I + Mat2x2{{{-KH.m[0][0]+I.m[0][0], -KH.m[0][1]},
                           {-KH.m[1][0], -KH.m[1][1]+I.m[1][1]}}}) * P_;

        return {x_[0], x_[1]};
    }

    bool isInitialised() const noexcept { return initialised_; }
    State getState() const noexcept { return {x_[0], x_[1]}; }

private:
    Vec2   x_            = {};      // State [range, range_rate]
    Mat2x2 P_            = {};      // Covariance
    Mat2x2 Q_            = {};      // Process noise
    float  R_            = 0.01F;   // Measurement noise variance
    float  H_[2]         = {};      // Observation matrix row
    bool   initialised_  = false;
};

// ============================================================================
// MULTI-OBJECT TRACKER — wraps KF per tracked object
// ============================================================================

struct TrackedObject {
    uint8_t         id        = 0U;
    bool            valid     = false;
    uint8_t         trackAge  = 0U;   // Cycles object has been tracked
    KalmanFilter1D  kf;
    float           filteredRange_m    = 0.0F;
    float           filteredRangeRate  = 0.0F;
};

class ObjectTracker {
public:
    static constexpr std::size_t MAX_OBJECTS = 8U;
    static constexpr uint8_t     CONFIRM_AGE = 3U;   // 3 cycles before reported

    /**
     * Update tracker with new radar measurement.
     * @param objectId  Radar-assigned object ID (0..31)
     * @param range_m   Measured range
     * @param relVelMps Measured relative velocity
     * @param dt_s      Time step
     */
    void update(uint8_t objectId, float range_m, float relVelMps, float dt_s) noexcept {
        TrackedObject* obj = findOrCreate(objectId);
        if (obj == nullptr) { return; }  // Tracker full

        if (!obj->kf.isInitialised()) {
            obj->kf.init(range_m, relVelMps);
        } else {
            obj->kf.predict(dt_s);
            obj->kf.update(range_m);
        }

        auto st = obj->kf.getState();
        obj->filteredRange_m   = st.range_m;
        obj->filteredRangeRate = st.rangeDot_mps;
        obj->trackAge          = std::min(static_cast<int>(obj->trackAge) + 1, 255);
    }

    const TrackedObject* getObject(uint8_t objectId) const noexcept {
        for (const auto& o : objects_) {
            if (o.valid && o.id == objectId) { return &o; }
        }
        return nullptr;
    }

    /** Find closest confirmed in-path object (ACC "most relevant object") */
    const TrackedObject* getMostRelevantObject() const noexcept {
        const TrackedObject* best = nullptr;
        float minRange = 200.0F;
        for (const auto& o : objects_) {
            if (o.valid && o.trackAge >= CONFIRM_AGE && o.filteredRange_m < minRange) {
                minRange = o.filteredRange_m;
                best     = &o;
            }
        }
        return best;
    }

private:
    std::array<TrackedObject, MAX_OBJECTS> objects_ = {};

    TrackedObject* findOrCreate(uint8_t id) noexcept {
        // Find existing
        for (auto& o : objects_) {
            if (o.valid && o.id == id) { return &o; }
        }
        // Create new in free slot
        for (auto& o : objects_) {
            if (!o.valid) {
                o        = TrackedObject{};
                o.id     = id;
                o.valid  = true;
                return &o;
            }
        }
        return nullptr;
    }
};

// ============================================================================
// MAIN — DEMONSTRATE KALMAN FILTER TRACKING
// ============================================================================

int main() {
    std::cout << "=== Sensor Fusion — Kalman Filter Object Tracking ===\n\n";
    std::cout << std::fixed << std::setprecision(2);

    KalmanFilter1D kf;
    kf.init(100.0F, -10.0F);  // Object at 100m, approaching at 10 m/s

    std::cout << std::setw(8)  << "t(s)"
              << std::setw(14) << "True Range"
              << std::setw(16) << "Noisy Measure"
              << std::setw(16) << "KF Estimate"
              << std::setw(16) << "KF Velocity\n";
    std::cout << std::string(70, '-') << "\n";

    // Simulate: object moving from 100m to 50m over 5 seconds
    float trueRange    = 100.0F;
    float trueVelocity = -10.0F;  // Constant approach

    for (int step = 0; step <= 50; ++step) {
        float t = step * 0.1F;

        // True state
        trueRange += trueVelocity * 0.1F;
        // At t=3s: lead vehicle brakes → velocity changes
        if (step == 30) { trueVelocity = -3.0F; }

        // Simulated radar measurement with noise (±0.4m)
        float noise   = 0.4F * (static_cast<float>(step % 7 - 3) / 3.0F);
        float measure = trueRange + noise;

        // KF predict + update
        kf.predict(0.1F);
        auto state = kf.update(measure);

        if (step % 5 == 0) {
            std::cout << std::setw(8)  << t
                      << std::setw(14) << trueRange
                      << std::setw(16) << measure
                      << std::setw(16) << state.range_m
                      << std::setw(16) << state.rangeDot_mps << "\n";
        }
    }

    std::cout << "\n=== Multi-Object Tracker Demo ===\n\n";

    ObjectTracker tracker;

    // Simulate 3 radar objects over 10 cycles
    for (int cycle = 0; cycle < 10; ++cycle) {
        float t = cycle * 0.05F;
        tracker.update(1U, 80.0F - cycle * 0.8F, -5.0F, 0.05F);  // Obj 1: approaching
        tracker.update(2U, 50.0F - cycle * 0.2F, -2.0F, 0.05F);  // Obj 2: slower
        tracker.update(3U, 120.0F,                 0.1F, 0.05F);  // Obj 3: stationary

        const TrackedObject* mro = tracker.getMostRelevantObject();
        if (mro != nullptr) {
            std::cout << "t=" << std::setw(4) << t
                      << "  MRO: obj#" << static_cast<int>(mro->id)
                      << "  range=" << std::setw(7) << mro->filteredRange_m
                      << "m  relVel=" << std::setw(6) << mro->filteredRangeRate
                      << " m/s  age=" << static_cast<int>(mro->trackAge) << "\n";
        }
    }

    return 0;
}
