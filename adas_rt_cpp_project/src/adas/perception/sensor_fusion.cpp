/**
 * @file sensor_fusion.cpp
 * @brief EKF multi-object tracker implementation.
 *
 * PREDICT STEP  (constant-velocity model)
 * ─────────────────────────────────────────
 *   x_k|k-1 = F * x_k-1|k-1
 *   P_k|k-1 = F * P_k-1|k-1 * Fᵀ + Q
 *
 *   F = | 1 0 dt  0 |    Q ≈ σ_a² * G * Gᵀ  where G = [dt²/2, dt²/2, dt, dt]ᵀ
 *       | 0 1  0 dt |
 *       | 0 0  1  0 |
 *       | 0 0  0  1 |
 *
 * CAMERA UPDATE (linear)
 * ────────────────────────
 *   H_cam = | 1 0 0 0 |    z = [px, py]ᵀ
 *           | 0 1 0 0 |
 *   y = z - H_cam * x_pred
 *   S = H_cam * P * H_camᵀ + R_cam
 *   K = P * H_camᵀ * S⁻¹
 *   x = x_pred + K * y
 *   P = (I - K * H_cam) * P_pred
 *
 * RADAR UPDATE (non-linear → EKF linearisation)
 * ────────────────────────────────────────────────
 *   h(x) = [ sqrt(px²+py²),
 *             atan2(py, px),
 *            (px*vx+py*vy)/sqrt(px²+py²) ]ᵀ
 *
 *   Jacobian H_j = dh/dx  (3×4, computed analytically)
 */

#include "sensor_fusion.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>

namespace adas {
namespace perception {

// ─── Matrix helpers ───────────────────────────────────────────────────────────

Matrix<2,2> inv2x2(const Matrix<2,2>& M) {
    const float det = M(0,0)*M(1,1) - M(0,1)*M(1,0);
    assert(std::abs(det) > 1e-9f);
    const float inv_det = 1.0f / det;
    Matrix<2,2> out;
    out(0,0) =  M(1,1) * inv_det;
    out(0,1) = -M(0,1) * inv_det;
    out(1,0) = -M(1,0) * inv_det;
    out(1,1) =  M(0,0) * inv_det;
    return out;
}

Matrix<3,3> inv3x3(const Matrix<3,3>& M) {
    const float det = M(0,0)*(M(1,1)*M(2,2)-M(1,2)*M(2,1))
                    - M(0,1)*(M(1,0)*M(2,2)-M(1,2)*M(2,0))
                    + M(0,2)*(M(1,0)*M(2,1)-M(1,1)*M(2,0));
    assert(std::abs(det) > 1e-9f);
    const float inv = 1.0f / det;
    Matrix<3,3> out;
    out(0,0) = (M(1,1)*M(2,2)-M(1,2)*M(2,1))*inv;
    out(0,1) = (M(0,2)*M(2,1)-M(0,1)*M(2,2))*inv;
    out(0,2) = (M(0,1)*M(1,2)-M(0,2)*M(1,1))*inv;
    out(1,0) = (M(1,2)*M(2,0)-M(1,0)*M(2,2))*inv;
    out(1,1) = (M(0,0)*M(2,2)-M(0,2)*M(2,0))*inv;
    out(1,2) = (M(0,2)*M(1,0)-M(0,0)*M(1,2))*inv;
    out(2,0) = (M(1,0)*M(2,1)-M(1,1)*M(2,0))*inv;
    out(2,1) = (M(0,1)*M(2,0)-M(0,0)*M(2,1))*inv;
    out(2,2) = (M(0,0)*M(1,1)-M(0,1)*M(1,0))*inv;
    return out;
}

// ─── SensorFusion ─────────────────────────────────────────────────────────────

SensorFusion::SensorFusion() = default;

void SensorFusion::setNoiseParams(float sigma_a, float sigma_cam, float sigma_radar) {
    sigma_a_     = sigma_a;
    sigma_cam_   = sigma_cam;
    sigma_radar_ = sigma_radar;
}

void SensorFusion::reset() {
    tracks_.clear();
    next_track_id_ = 0;
    prev_timestamp_us_ = 0;
}

// ─── Predict step ─────────────────────────────────────────────────────────────

void SensorFusion::predictTrack(KalmanTrack& track, float dt_s) const {
    // ① Build F (state transition)
    auto F = Mat4::identity();
    F(0,2) = dt_s;
    F(1,3) = dt_s;

    // ② Build Q (process noise)
    const float dt2 = dt_s * dt_s;
    const float dt3 = dt2 * dt_s;
    const float dt4 = dt2 * dt2;
    const float sa2 = sigma_a_ * sigma_a_;
    auto Q = Mat4::zero();
    Q(0,0) = 0.25f * dt4 * sa2;
    Q(0,2) = 0.5f  * dt3 * sa2;
    Q(1,1) = 0.25f * dt4 * sa2;
    Q(1,3) = 0.5f  * dt3 * sa2;
    Q(2,0) = 0.5f  * dt3 * sa2;
    Q(2,2) = dt2   * sa2;
    Q(3,1) = 0.5f  * dt3 * sa2;
    Q(3,3) = dt2   * sa2;

    // ③ Predict: x' = F * x
    track.x = matmul(F, track.x);
    // ④ Predict: P' = F * P * Fᵀ + Q
    track.P = matmul(matmul(F, track.P), transpose(F)) + Q;
}

// ─── Camera update ────────────────────────────────────────────────────────────

void SensorFusion::updateTrackCamera(KalmanTrack&          track,
                                      const DetectedObject& det) const {
    // H_cam = [ 1 0 0 0 ; 0 1 0 0 ]
    Matrix<2,4> H;
    H(0,0)=1.f; H(0,1)=0.f; H(0,2)=0.f; H(0,3)=0.f;
    H(1,0)=0.f; H(1,1)=1.f; H(1,2)=0.f; H(1,3)=0.f;

    // R_cam
    Matrix<2,2> R;
    R(0,0) = sigma_cam_ * sigma_cam_;
    R(1,1) = sigma_cam_ * sigma_cam_;

    // Innovation
    Matrix<2,1> z;
    z(0,0) = det.x;
    z(1,0) = det.y;
    const Matrix<2,1> y = z - matmul(H, track.x);

    // S = H * P * Hᵀ + R
    const Matrix<2,2> S = matmul(matmul(H, track.P), transpose(H)) + R;
    const Matrix<2,2> S_inv = inv2x2(S);

    // K = P * Hᵀ * S⁻¹
    const Matrix<4,2> K = matmul(matmul(track.P, transpose(H)), S_inv);

    // Update
    track.x = track.x + matmul(K, y);
    const auto I = Mat4::identity();
    track.P = matmul(I - matmul(K, H), track.P);
}

// ─── Radar update (EKF) ───────────────────────────────────────────────────────

void SensorFusion::updateTrackRadar(KalmanTrack&          track,
                                     const DetectedObject& det) const {
    const float px = track.x(0,0);
    const float py = track.x(1,0);
    const float vx = track.x(2,0);
    const float vy = track.x(3,0);

    const float rho = std::sqrt(px*px + py*py);
    if (rho < 1e-4f) return;   // avoid division by zero in degenerate case

    // Non-linear measurement function h(x)
    Matrix<3,1> z_pred;
    z_pred(0,0) = rho;
    z_pred(1,0) = std::atan2(py, px);
    z_pred(2,0) = (px*vx + py*vy) / rho;

    // Measurement
    Matrix<3,1> z;
    z(0,0) = std::sqrt(det.x*det.x + det.y*det.y);       // range
    z(1,0) = std::atan2(det.y, det.x);                    // azimuth
    z(2,0) = (det.x*det.vx + det.y*det.vy) / (z(0,0) + 1e-6f); // range-rate

    Matrix<3,1> y = z - z_pred;
    // Normalise azimuth innovation to [-π, π]
    while (y(1,0) >  M_PIf32) y(1,0) -= 2.0f*M_PIf32;
    while (y(1,0) < -M_PIf32) y(1,0) += 2.0f*M_PIf32;

    // Jacobian H_j (3×4)
    Matrix<3,4> H_j;
    const float rho2 = rho * rho;
    H_j(0,0) =  px/rho;         H_j(0,1) =  py/rho;         H_j(0,2) = 0.f; H_j(0,3) = 0.f;
    H_j(1,0) = -py/rho2;        H_j(1,1) =  px/rho2;        H_j(1,2) = 0.f; H_j(1,3) = 0.f;
    H_j(2,0) = py*(vx*py-vy*px)/(rho2*rho);
    H_j(2,1) = px*(vy*px-vx*py)/(rho2*rho);
    H_j(2,2) = px/rho;
    H_j(2,3) = py/rho;

    // R_radar
    Matrix<3,3> R;
    R(0,0) = sigma_radar_ * sigma_radar_;
    R(1,1) = (0.03f * M_PIf32/180.f) * (0.03f * M_PIf32/180.f);  // ~0.03 deg azimuth noise
    R(2,2) = 0.1f * 0.1f;                                          // 0.1 m/s range-rate noise

    // S = H_j * P * H_jᵀ + R
    const Matrix<3,3> S = matmul(matmul(H_j, track.P), transpose(H_j)) + R;
    const Matrix<3,3> S_inv = inv3x3(S);

    // K = P * H_jᵀ * S⁻¹
    const Matrix<4,3> K = matmul(matmul(track.P, transpose(H_j)), S_inv);

    track.x = track.x + matmul(K, y);
    const auto I = Mat4::identity();
    track.P = matmul(I - matmul(K, H_j), track.P);
}

// ─── Mahalanobis distance ─────────────────────────────────────────────────────

float SensorFusion::mahalanobisDistance(const KalmanTrack&    track,
                                         const DetectedObject& det) const {
    // Use only position components (2D)
    const float dx = det.x - track.x(0,0);
    const float dy = det.y - track.x(1,0);

    // Extract 2×2 position sub-covariance
    Matrix<2,2> S;
    S(0,0) = track.P(0,0);  S(0,1) = track.P(0,1);
    S(1,0) = track.P(1,0);  S(1,1) = track.P(1,1);
    const Matrix<2,2> S_inv = inv2x2(S);

    return dx*dx*S_inv(0,0) + 2.0f*dx*dy*S_inv(0,1) + dy*dy*S_inv(1,1);
}

// ─── Main update loop ─────────────────────────────────────────────────────────

std::vector<TrackedObject>
SensorFusion::update(const std::vector<DetectedObject>& detections,
                      uint64_t timestamp_us) {
    // ① Compute dt
    float dt_s = 0.05f;  // default 50 Hz
    if (prev_timestamp_us_ > 0) {
        dt_s = static_cast<float>(timestamp_us - prev_timestamp_us_) * 1e-6f;
        dt_s = std::max(0.005f, std::min(dt_s, 0.5f));  // clamp to [5ms, 500ms]
    }
    prev_timestamp_us_ = timestamp_us;

    // ② Predict all existing tracks
    for (auto& [id, track] : tracks_) {
        predictTrack(track, dt_s);
        ++track.misses;
    }

    // ③ Greedy nearest-neighbour association
    std::vector<bool> det_assigned(detections.size(), false);

    for (auto& [id, track] : tracks_) {
        float   best_dist = kGateThreshold;
        int     best_idx  = -1;

        for (size_t i = 0; i < detections.size(); ++i) {
            if (det_assigned[i]) continue;
            const float d = mahalanobisDistance(track, detections[i]);
            if (d < best_dist) {
                best_dist = d;
                best_idx  = static_cast<int>(i);
            }
        }

        if (best_idx >= 0) {
            det_assigned[best_idx] = true;
            const auto& det = detections[best_idx];

            // ④ EKF update with appropriate sensor model
            if (det.source == SensorType::RADAR) {
                updateTrackRadar(track, det);
            } else {
                updateTrackCamera(track, det);
            }
            track.misses = 0;
            ++track.hits;
            track.last_update_us = timestamp_us;
            if (det.confidence > track.cls_confidence) {
                track.cls            = det.cls;
                track.cls_confidence = det.confidence;
            }
        }
    }

    // ⑤ Initialise new tracks for unassigned detections
    for (size_t i = 0; i < detections.size(); ++i) {
        if (!det_assigned[i]) {
            initTrack(detections[i], timestamp_us);
        }
    }

    // ⑥ Prune dead tracks
    pruneDeadTracks();

    // ⑦ Build output
    return getTracks();
}

void SensorFusion::initTrack(const DetectedObject& det, uint64_t timestamp_us) {
    KalmanTrack t{};
    t.track_id       = next_track_id_++;
    t.cls            = det.cls;
    t.cls_confidence = det.confidence;
    t.hits           = 1;
    t.misses         = 0;
    t.last_update_us = timestamp_us;

    t.x(0,0) = det.x;
    t.x(1,0) = det.y;
    t.x(2,0) = det.vx;
    t.x(3,0) = det.vy;

    // Initial covariance: low confidence on velocity
    t.P = Mat4::identity();
    t.P(0,0) = sigma_cam_ * sigma_cam_;
    t.P(1,1) = sigma_cam_ * sigma_cam_;
    t.P(2,2) = 25.0f;   // high velocity uncertainty [m²/s²]
    t.P(3,3) = 25.0f;

    tracks_[t.track_id] = t;
}

void SensorFusion::pruneDeadTracks() {
    for (auto it = tracks_.begin(); it != tracks_.end();) {
        if (it->second.misses >= kMaxMisses) {
            it = tracks_.erase(it);
        } else {
            ++it;
        }
    }
}

std::vector<TrackedObject> SensorFusion::getTracks() const {
    std::vector<TrackedObject> out;
    out.reserve(tracks_.size());
    for (const auto& [id, t] : tracks_) {
        out.push_back(trackToOutput(t));
    }
    return out;
}

TrackedObject SensorFusion::trackToOutput(const KalmanTrack& t) const {
    TrackedObject o{};
    o.track_id      = t.track_id;
    o.cls           = t.cls;
    o.confidence    = t.cls_confidence;
    o.px            = t.x(0,0);
    o.py            = t.x(1,0);
    o.vx            = t.x(2,0);
    o.vy            = t.x(3,0);
    o.cov_px        = std::sqrt(t.P(0,0));
    o.cov_py        = std::sqrt(t.P(1,1));
    o.timestamp_us  = t.last_update_us;
    o.is_confirmed  = (t.hits >= kConfirmThreshold);
    return o;
}

}  // namespace perception
}  // namespace adas
