// ============================================================
// adas/sensor_fusion.cpp — EKF ego-state estimator
// ============================================================

#include "adas/sensor_fusion.hpp"

#include <algorithm>
#include <cmath>

namespace adas {

// ──────────────────────────────────────────────────────────────────────────────
// Reset: initialise state and a diagonal covariance.
// ──────────────────────────────────────────────────────────────────────────────
void EgoStateEkf::reset(double speed_mps, double yaw_rate_radps) noexcept {
    x_.fill(0.0);
    x_[3] = speed_mps;
    x_[4] = yaw_rate_radps;
    // Diagonal initial covariance: position uncertain (10 m), heading 0.1 rad,
    // speed 2 m/s, yaw rate 0.2 rad/s.
    for (auto& row : p_) row.fill(0.0);
    p_[0][0] = 100.0;
    p_[1][1] = 100.0;
    p_[2][2] = 0.01;
    p_[3][3] = 4.0;
    p_[4][4] = 0.04;
    initialized_ = true;
}

// ──────────────────────────────────────────────────────────────────────────────
// Predict: CTRS model (constant turn-rate and speed).
//
// x = [x, y, ψ, v, ψ̇]
// ψ̇ ≠ 0:  x += (v/ψ̇)(sin(ψ+ψ̇·dt) − sin(ψ))
//         y += (v/ψ̇)(cos(ψ) − cos(ψ+ψ̇·dt))
// ψ̇ ≈ 0:  x += v·cos(ψ)·dt,  y += v·sin(ψ)·dt   (nearly straight)
// ψ  += ψ̇·dt
// v,ψ̇ unchanged (constant model; corrected by sensor updates).
//
// Jacobian F is the Tylor-series linearisation of f about the current state.
// Process noise added as Q on diagonal after covariance propagation.
// ──────────────────────────────────────────────────────────────────────────────
void EgoStateEkf::predict(double dt_s) noexcept {
    if (!initialized_ || dt_s <= 0.0 || dt_s > 0.2) return;

    const double psi  = x_[2];
    const double v    = x_[3];
    const double dpsi = x_[4];
    const double cos_psi = std::cos(psi);
    const double sin_psi = std::sin(psi);

    if (std::abs(dpsi) > 1e-4) {
        const double new_psi = psi + dpsi * dt_s;
        const double cos_new = std::cos(new_psi);
        const double sin_new = std::sin(new_psi);
        x_[0] += (v / dpsi) * (sin_new - sin_psi);
        x_[1] += (v / dpsi) * (cos_psi - cos_new);
        x_[2]  = new_psi;
    } else {
        x_[0] += v * cos_psi * dt_s;
        x_[1] += v * sin_psi * dt_s;
        x_[2] += dpsi * dt_s;
    }
    // v and dpsi unchanged (corrected by measurement updates).

    // Jacobian of f w.r.t. x (5×5). Derived by differentiating the CTRS equations.
    std::array<std::array<double, 5>, 5> F{};
    for (auto& row : F) row.fill(0.0);
    // Identity base
    for (int i = 0; i < 5; ++i) F[i][i] = 1.0;
    const double new_psi = x_[2];
    const double cos_new = std::cos(new_psi);
    const double sin_new = std::sin(new_psi);
    if (std::abs(dpsi) > 1e-4) {
        F[0][2] = (v / dpsi) * (cos_new - cos_psi);
        F[0][3] = (1.0 / dpsi) * (sin_new - sin_psi);
        F[0][4] = (v / (dpsi * dpsi)) * (cos_new - cos_psi) + (v / dpsi) * cos_new * dt_s;
        F[1][2] = (v / dpsi) * (sin_new - sin_psi);
        F[1][3] = (1.0 / dpsi) * (cos_psi - cos_new);
        F[1][4] = (v / (dpsi * dpsi)) * (sin_new - sin_psi) + (v / dpsi) * (-sin_new) * dt_s;
    } else {
        F[0][2] = -v * sin_psi * dt_s;
        F[0][3] =  cos_psi * dt_s;
        F[1][2] =  v * cos_psi * dt_s;
        F[1][3] =  sin_psi * dt_s;
    }

    // P = F*P*F' + Q
    std::array<std::array<double, 5>, 5> FP{};
    for (int i = 0; i < 5; ++i)
        for (int j = 0; j < 5; ++j) {
            FP[i][j] = 0.0;
            for (int k = 0; k < 5; ++k) FP[i][j] += F[i][k] * p_[k][j];
        }
    for (int i = 0; i < 5; ++i)
        for (int j = 0; j < 5; ++j) {
            p_[i][j] = 0.0;
            for (int k = 0; k < 5; ++k) p_[i][j] += FP[i][k] * F[j][k];
        }
    // Additive process noise (diagonal Q)
    for (int i = 0; i < 5; ++i) p_[i][i] += kQ[static_cast<std::size_t>(i)] * dt_s;
}

// ──────────────────────────────────────────────────────────────────────────────
// Scalar update (shared by all measurement types)
// h is the 1×5 measurement Jacobian row. Innovates state and covariance.
// ──────────────────────────────────────────────────────────────────────────────
bool EgoStateEkf::scalar_update(double z, const std::array<double, 5>& h, double r) noexcept {
    // Predicted measurement
    double h_x = 0.0;
    for (int i = 0; i < 5; ++i) h_x += h[static_cast<std::size_t>(i)] * x_[static_cast<std::size_t>(i)];
    const double innovation = z - h_x;

    // S = H*P*H' + R
    std::array<double, 5> ph{};
    for (int i = 0; i < 5; ++i) {
        ph[static_cast<std::size_t>(i)] = 0.0;
        for (int j = 0; j < 5; ++j)
            ph[static_cast<std::size_t>(i)] += p_[i][j] * h[static_cast<std::size_t>(j)];
    }
    double S = r;
    for (int i = 0; i < 5; ++i) S += h[static_cast<std::size_t>(i)] * ph[static_cast<std::size_t>(i)];
    if (!std::isfinite(S) || S <= 1e-9) return false;

    // Kalman gain K = P*H'/S
    std::array<double, 5> K{};
    for (int i = 0; i < 5; ++i) K[static_cast<std::size_t>(i)] = ph[static_cast<std::size_t>(i)] / S;

    // State update
    for (int i = 0; i < 5; ++i) x_[static_cast<std::size_t>(i)] += K[static_cast<std::size_t>(i)] * innovation;

    // Covariance update: Joseph form P = (I-KH)P(I-KH)' + K*R*K'
    std::array<std::array<double, 5>, 5> ImKH{};
    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < 5; ++j) ImKH[i][j] = (i == j ? 1.0 : 0.0) - K[static_cast<std::size_t>(i)] * h[static_cast<std::size_t>(j)];
    }
    std::array<std::array<double, 5>, 5> tmp{};
    for (int i = 0; i < 5; ++i)
        for (int j = 0; j < 5; ++j) {
            tmp[i][j] = 0.0;
            for (int k = 0; k < 5; ++k) tmp[i][j] += ImKH[i][k] * p_[k][j];
        }
    for (int i = 0; i < 5; ++i)
        for (int j = 0; j < 5; ++j) {
            p_[i][j] = 0.0;
            for (int k = 0; k < 5; ++k) p_[i][j] += tmp[i][k] * ImKH[j][k];
            p_[i][j] += K[static_cast<std::size_t>(i)] * r * K[static_cast<std::size_t>(j)];
        }
    return std::isfinite(x_[3]) && std::isfinite(x_[4]);
}

bool EgoStateEkf::update_wheel_speed(double measured_speed_mps) noexcept {
    if (!initialized_ || !std::isfinite(measured_speed_mps)) return false;
    // h = [0, 0, 0, 1, 0]
    return scalar_update(measured_speed_mps, {0.0, 0.0, 0.0, 1.0, 0.0}, kR_speed);
}

bool EgoStateEkf::update_yaw_rate(double measured_yaw_rate_radps) noexcept {
    if (!initialized_ || !std::isfinite(measured_yaw_rate_radps)) return false;
    // h = [0, 0, 0, 0, 1]
    return scalar_update(measured_yaw_rate_radps, {0.0, 0.0, 0.0, 0.0, 1.0}, kR_yaw_rate);
}

bool EgoStateEkf::update_lateral_accel(double measured_ay_mps2) noexcept {
    if (!initialized_ || !std::isfinite(measured_ay_mps2)) return false;
    // Centripetal acceleration: ay = v * psi_dot  → h = [0, 0, 0, psi_dot, v]
    const std::array<double, 5> h{0.0, 0.0, 0.0, x_[4], x_[3]};
    return scalar_update(measured_ay_mps2, h, kR_lat_accel);
}

EgoStateEstimate EgoStateEkf::state() const noexcept {
    EgoStateEstimate est;
    est.x_m         = x_[0];
    est.y_m         = x_[1];
    est.heading_rad = x_[2];
    est.speed_mps   = x_[3];
    est.yaw_rate_radps = x_[4];
    est.speed_variance        = p_[3][3];
    est.position_variance_m2  = 0.5 * (p_[0][0] + p_[1][1]);
    est.valid = initialized_;
    return est;
}

}  // namespace adas
