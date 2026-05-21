#pragma once
/**
 * @file sensor_fusion.hpp
 * @brief Extended Kalman Filter (EKF) for multi-sensor object tracking.
 *
 * STATE VECTOR  x = [ px, py, vx, vy ]ᵀ   (4D, constant-velocity model)
 *
 * SENSOR MODELS
 * ─────────────
 *   Camera  →  z_cam  = [px, py]ᵀ              (linear H)
 *   Radar   →  z_rad  = [ρ, φ, ρ̇]ᵀ             (non-linear h, needs Jacobian)
 *
 * ARCHITECTURE
 * ────────────
 * • SensorFusion owns a map<TrackID, KalmanTrack>.
 * • Each call to update() associates incoming detections with existing tracks
 *   (nearest-neighbour gating), creates new tracks, and deletes stale ones.
 * • Designed for single-thread RT use at up to 50 Hz fusion rate.
 *
 * NUMERICAL NOTES
 * ───────────────
 * • All matrices are 4×4 or smaller – no dynamic allocation in hot path.
 * • Uses a simple fixed-size Matrix<N,M> to avoid Eigen dependency while
 *   remaining readable and numerically explicit.
 */

#include "object_detection.hpp"

#include <array>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace adas {
namespace perception {

// ─── Tiny fixed-size matrix (row-major) ──────────────────────────────────────

template<int ROWS, int COLS>
struct Matrix {
    std::array<float, ROWS * COLS> data{};

    float& operator()(int r, int c)       { return data[r * COLS + c]; }
    float  operator()(int r, int c) const { return data[r * COLS + c]; }

    static Matrix<ROWS, COLS> zero() { Matrix<ROWS, COLS> m; m.data.fill(0.0f); return m; }
    static Matrix<ROWS, ROWS> identity() requires (ROWS == COLS) {
        auto m = zero();
        for (int i = 0; i < ROWS; ++i) m(i, i) = 1.0f;
        return m;
    }
};

/// Matrix addition
template<int R, int C>
Matrix<R,C> operator+(const Matrix<R,C>& A, const Matrix<R,C>& B) {
    Matrix<R,C> out;
    for (int i = 0; i < R*C; ++i) out.data[i] = A.data[i] + B.data[i];
    return out;
}

/// Matrix subtraction
template<int R, int C>
Matrix<R,C> operator-(const Matrix<R,C>& A, const Matrix<R,C>& B) {
    Matrix<R,C> out;
    for (int i = 0; i < R*C; ++i) out.data[i] = A.data[i] - B.data[i];
    return out;
}

/// Matrix multiplication A(R×K) * B(K×C)
template<int R, int K, int C>
Matrix<R,C> matmul(const Matrix<R,K>& A, const Matrix<K,C>& B) {
    auto out = Matrix<R,C>::zero();
    for (int r = 0; r < R; ++r)
        for (int k = 0; k < K; ++k)
            for (int c = 0; c < C; ++c)
                out(r,c) += A(r,k) * B(k,c);
    return out;
}

/// Matrix transpose
template<int R, int C>
Matrix<C,R> transpose(const Matrix<R,C>& A) {
    Matrix<C,R> out;
    for (int r = 0; r < R; ++r)
        for (int c = 0; c < C; ++c)
            out(c,r) = A(r,c);
    return out;
}

/// Scalar multiply
template<int R, int C>
Matrix<R,C> operator*(float s, const Matrix<R,C>& A) {
    Matrix<R,C> out;
    for (int i = 0; i < R*C; ++i) out.data[i] = s * A.data[i];
    return out;
}

// ─── 2×2 matrix inversion (closed form) ──────────────────────────────────────
Matrix<2,2> inv2x2(const Matrix<2,2>& M);

// ─── 3×3 matrix inversion (closed form) ──────────────────────────────────────
Matrix<3,3> inv3x3(const Matrix<3,3>& M);

// ─── State / track types ──────────────────────────────────────────────────────

using Vec4 = Matrix<4,1>;
using Mat4 = Matrix<4,4>;

struct KalmanTrack {
    uint32_t  track_id;
    Vec4      x;           ///< state [px, py, vx, vy]
    Mat4      P;           ///< error covariance
    uint32_t  hits;        ///< consecutive frames with associated measurement
    uint32_t  misses;      ///< consecutive frames without associated measurement
    uint64_t  last_update_us;
    ObjectClass cls;
    float     cls_confidence;
};

/// Fused, tracked object ready for consumption by the planning module
struct TrackedObject {
    uint32_t    track_id;
    ObjectClass cls;
    float       confidence;
    float       px, py;          ///< ego-frame position [m]
    float       vx, vy;          ///< ego-frame velocity [m/s]
    float       cov_px, cov_py;  ///< 1-σ position uncertainty [m]
    uint64_t    timestamp_us;
    bool        is_confirmed;     ///< true once hits >= kConfirmThreshold
};

// ─── SensorFusion class ───────────────────────────────────────────────────────

/**
 * @class SensorFusion
 * @brief EKF-based multi-object tracker consuming DetectedObject lists.
 *
 * Example:
 * @code
 *   SensorFusion fusion;
 *   fusion.setNoiseParams(0.5f, 0.1f, 0.3f);
 *
 *   auto objects = detector.process(cam_frame);
 *   auto tracked = fusion.update(objects, timestamp_us);
 * @endcode
 */
class SensorFusion {
public:
    SensorFusion();
    ~SensorFusion() = default;

    // Non-copyable
    SensorFusion(const SensorFusion&)            = delete;
    SensorFusion& operator=(const SensorFusion&) = delete;

    /**
     * @brief Configure noise parameters.
     * @param sigma_a     Process noise (acceleration std-dev) [m/s²]
     * @param sigma_cam   Camera measurement noise (position std-dev) [m]
     * @param sigma_radar Radar measurement noise (range std-dev) [m]
     */
    void setNoiseParams(float sigma_a, float sigma_cam, float sigma_radar);

    /**
     * @brief Run one EKF predict+update cycle.
     * @param detections  Detections from ObjectDetector::process()
     * @param timestamp_us Current timestamp [µs]
     * @return All active tracks converted to TrackedObject
     */
    std::vector<TrackedObject> update(const std::vector<DetectedObject>& detections,
                                      uint64_t timestamp_us);

    /// Retrieve all currently active tracks (e.g. for visualisation)
    std::vector<TrackedObject> getTracks() const;

    /// Reset all tracks (useful for SIL scenario reset)
    void reset();

private:
    // ── EKF internals ────────────────────────────────────────────────────────
    void predictTrack(KalmanTrack& track, float dt_s) const;

    void updateTrackCamera(KalmanTrack& track,
                           const DetectedObject& det) const;

    void updateTrackRadar(KalmanTrack& track,
                          const DetectedObject& det) const;

    // ── Association ──────────────────────────────────────────────────────────
    /// Mahalanobis distance between track prediction and detection
    float mahalanobisDistance(const KalmanTrack& track,
                               const DetectedObject& det) const;

    // ── Track management ─────────────────────────────────────────────────────
    void initTrack(const DetectedObject& det, uint64_t timestamp_us);
    void pruneDeadTracks();
    TrackedObject trackToOutput(const KalmanTrack& t) const;

    // ── State ────────────────────────────────────────────────────────────────
    std::unordered_map<uint32_t, KalmanTrack> tracks_;
    uint32_t next_track_id_{0};
    uint64_t prev_timestamp_us_{0};

    // Noise parameters
    float sigma_a_{1.0f};       ///< process noise [m/s²]
    float sigma_cam_{0.5f};     ///< camera measurement noise [m]
    float sigma_radar_{1.0f};   ///< radar measurement noise [m]

    // Thresholds
    static constexpr float    kGateThreshold    = 9.0f;   ///< χ² at 99%
    static constexpr uint32_t kConfirmThreshold = 3u;
    static constexpr uint32_t kMaxMisses        = 5u;
};

}  // namespace perception
}  // namespace adas
