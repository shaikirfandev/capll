#pragma once

// ============================================================
// adas/sensor_fusion.hpp — Extended Kalman Filter ego-state estimator
//
// State vector x ∈ ℝ⁵: [x_m, y_m, ψ_rad, v_mps, ψ̇_radps]
//
// Prediction model: constant-turn-rate + speed (CTRS) with
// additive process noise on acceleration and yaw acceleration.
//
// Measurement sources:
//   1. Wheel-speed sensor  → speed (scalar)
//   2. IMU lateral accel   → centripetal: v·ψ̇ (scalar)
//   3. IMU yaw rate        → ψ̇ (scalar)
//
// All update steps are scalar (sequential), so no matrix inverse is needed.
//
// Production extensions:
//   - GNSS position update (NovAtel, u-blox) with HDOP gating.
//   - Camera visual odometry update.
//   - Lidar-based map matching.
//   - Covariance inflation for graceful degradation.
//   - GNSS spoofing / anomaly detection.
// ============================================================

#include "adas/types.hpp"

#include <array>

namespace adas {

class EgoStateEkf {
public:
    // ──────────────────────────────────────────────────────────────────
    // Lifecycle
    // ──────────────────────────────────────────────────────────────────

    /// @brief Initialize state and covariance from first sensor data.
    void reset(double speed_mps, double yaw_rate_radps) noexcept;

    // ──────────────────────────────────────────────────────────────────
    // Prediction step: run every control cycle (20 ms typical).
    // ──────────────────────────────────────────────────────────────────

    /// @param dt_s  Elapsed time since last prediction (s). Must be in (0, 0.2].
    void predict(double dt_s) noexcept;

    // ──────────────────────────────────────────────────────────────────
    // Measurement updates: call whichever sensors are available after predict().
    // ──────────────────────────────────────────────────────────────────

    /// @brief Update from wheel-speed sensor.
    bool update_wheel_speed(double measured_speed_mps) noexcept;

    /// @brief Update from IMU yaw rate.
    bool update_yaw_rate(double measured_yaw_rate_radps) noexcept;

    /// @brief Update from IMU lateral acceleration (used as v·ψ̇ observation).
    bool update_lateral_accel(double measured_ay_mps2) noexcept;

    // ──────────────────────────────────────────────────────────────────
    // State accessors
    // ──────────────────────────────────────────────────────────────────
    [[nodiscard]] EgoStateEstimate state() const noexcept;
    [[nodiscard]] bool initialized() const noexcept { return initialized_; }

private:
    // State: [x, y, psi, v, psi_dot]
    std::array<double, 5> x_{};
    // Covariance P (5×5, upper triangle stored row-major)
    std::array<std::array<double, 5>, 5> p_{};

    // Process noise diagonal [q_pos, q_pos, q_psi, q_v, q_psi_dot]
    static constexpr std::array<double, 5> kQ{0.04, 0.04, 0.001, 0.25, 0.09};

    // Measurement noise for each scalar sensor
    static constexpr double kR_speed{0.25};
    static constexpr double kR_yaw_rate{0.01};
    static constexpr double kR_lat_accel{0.36};

    bool initialized_{};
    TimePoint last_prediction_time_{};

    /// Scalar measurement update (Joseph form for numerical stability).
    /// @param z    Scalar measurement.
    /// @param h    Measurement Jacobian row (1×5).
    /// @param r    Measurement noise variance.
    /// @return false if innovation variance is non-positive (measurement rejected).
    bool scalar_update(double z, const std::array<double, 5>& h, double r) noexcept;
};

}  // namespace adas
