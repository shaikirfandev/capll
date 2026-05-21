#pragma once
/**
 * @file object_detection.hpp
 * @brief Raw-sensor object detection pipeline (camera + radar + lidar)
 *
 * DESIGN INTENT
 * ─────────────
 * • Each sensor publishes a SensorFrame to the ObjectDetector.
 * • The detector converts raw measurements into a list of DetectedObjects in
 *   the ego-vehicle coordinate frame (ISO 8855: X forward, Y left, Z up).
 * • Outputs feed directly into SensorFusion (EKF tracker).
 *
 * THREADING MODEL
 * ───────────────
 * • process() is called from a dedicated RT thread at 50 Hz (camera) or
 *   20 Hz (radar). It is lock-free: consumers pull from a wait-free SPSC
 *   queue (see realtime/lock_free_queue.hpp).
 */

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace adas {
namespace perception {

// ─── Enumerations ────────────────────────────────────────────────────────────

enum class SensorType : uint8_t {
    CAMERA = 0,
    RADAR  = 1,
    LIDAR  = 2,
    FUSION = 3,  // already-fused estimate
};

enum class ObjectClass : uint8_t {
    UNKNOWN      = 0,
    VEHICLE      = 1,
    PEDESTRIAN   = 2,
    CYCLIST      = 3,
    STATIC_OBS   = 4,  // road furniture, barriers …
};

// ─── Raw sensor data frames ───────────────────────────────────────────────────

/// One raw detection from a camera (image-space bounding box + depth estimate)
struct CameraDetection {
    float u, v;           ///< bounding-box centre in pixel coordinates
    float width, height;  ///< bounding-box dimensions [px]
    float depth_m;        ///< depth estimate from stereo/mono-depth [m]
    float confidence;     ///< classifier score [0, 1]
    ObjectClass cls;
};

/// One raw detection from a radar (polar measurement)
struct RadarDetection {
    float range_m;        ///< radial distance [m]
    float azimuth_rad;    ///< azimuth angle [rad], +left
    float elevation_rad;  ///< elevation angle [rad]
    float range_rate_mps; ///< radial velocity (positive = approaching) [m/s]
    float rcs_dbsm;       ///< radar cross-section [dBsm]
};

/// One raw point from a LiDAR scan
struct LidarPoint {
    float x, y, z;        ///< Cartesian position in sensor frame [m]
    uint8_t intensity;    ///< return intensity [0-255]
};

/// Aggregated frame from a single sensor at one timestamp
struct SensorFrame {
    SensorType  type;
    uint64_t    timestamp_us;   ///< microseconds since epoch

    std::vector<CameraDetection> camera_dets;
    std::vector<RadarDetection>  radar_dets;
    std::vector<LidarPoint>      lidar_points;
};

// ─── Unified output type ──────────────────────────────────────────────────────

/// A detected object in the ego-vehicle Cartesian frame
struct DetectedObject {
    uint32_t    id;             ///< unique detection ID (per-frame, not tracked)
    SensorType  source;
    ObjectClass cls;
    float       confidence;

    // Position [m] and velocity [m/s] in ego frame
    float x, y, z;
    float vx, vy;

    // Bounding box [m] in ego frame
    float length, width, height;
    float heading_rad;          ///< heading relative to ego [rad]

    uint64_t timestamp_us;
};

// ─── Intrinsic / extrinsic calibration ───────────────────────────────────────

/// Pin-hole camera intrinsics + distortion (Brown-Conrady model)
struct CameraIntrinsics {
    float fx, fy;          ///< focal lengths [px]
    float cx, cy;          ///< principal point [px]
    std::array<float,5> dist_coeffs;  ///< k1,k2,p1,p2,k3
};

/// Rigid-body transform from sensor frame → ego frame
struct ExtrinsicTransform {
    float tx, ty, tz;      ///< translation [m]
    float roll, pitch, yaw;///< Euler angles [rad] (ZYX convention)
};

// ─── Object Detector class ────────────────────────────────────────────────────

/**
 * @class ObjectDetector
 * @brief Converts raw SensorFrames into a list of ego-frame DetectedObjects.
 *
 * Usage:
 * @code
 *   ObjectDetector detector;
 *   detector.configure(cam_intr, cam_ext, radar_ext);
 *   auto objects = detector.process(frame);
 * @endcode
 */
class ObjectDetector {
public:
    ObjectDetector();
    ~ObjectDetector() = default;

    // Non-copyable, movable
    ObjectDetector(const ObjectDetector&)            = delete;
    ObjectDetector& operator=(const ObjectDetector&) = delete;
    ObjectDetector(ObjectDetector&&)                 = default;

    /// Set calibration parameters (must be called before process())
    void configure(const CameraIntrinsics&  cam_intrinsics,
                   const ExtrinsicTransform& cam_extrinsic,
                   const ExtrinsicTransform& radar_extrinsic);

    /**
     * @brief Process a sensor frame and return detected objects.
     * @param frame  Raw sensor frame (may contain camera, radar, or lidar data)
     * @return       List of detected objects in the ego frame
     *
     * Real-time constraint: must complete in < 4 ms at 50 Hz camera rate.
     */
    std::vector<DetectedObject> process(const SensorFrame& frame);

    /// Reset internal ID counter (useful for SIL/HIL test reset)
    void reset();

private:
    // ── Camera pipeline ──────────────────────────────────────────────────────
    std::vector<DetectedObject> processCameraFrame(
        const std::vector<CameraDetection>& dets,
        uint64_t timestamp_us) const;

    void projectToEgoFrame(DetectedObject& obj,
                           const CameraDetection& det) const;

    // ── Radar pipeline ───────────────────────────────────────────────────────
    std::vector<DetectedObject> processRadarFrame(
        const std::vector<RadarDetection>& dets,
        uint64_t timestamp_us) const;

    // ── LiDAR pipeline ───────────────────────────────────────────────────────
    std::vector<DetectedObject> processLidarFrame(
        const std::vector<LidarPoint>& points,
        uint64_t timestamp_us) const;

    // ── Helpers ──────────────────────────────────────────────────────────────
    /// Convert polar radar measurement to Cartesian ego frame
    void radarPolarToEgo(DetectedObject& obj,
                         const RadarDetection& det) const;

    /// Apply rigid-body extrinsic transform to a position (in-place)
    void applyExtrinsic(float& x, float& y, float& z,
                        const ExtrinsicTransform& ext) const;

    // ── State ────────────────────────────────────────────────────────────────
    CameraIntrinsics   cam_intrinsics_{};
    ExtrinsicTransform cam_extrinsic_{};
    ExtrinsicTransform radar_extrinsic_{};
    bool               configured_{false};
    uint32_t           next_id_{0};
};

}  // namespace perception
}  // namespace adas
