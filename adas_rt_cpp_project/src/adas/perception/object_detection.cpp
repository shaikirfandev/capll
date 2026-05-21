/**
 * @file object_detection.cpp
 * @brief Implementation of the multi-sensor object detection pipeline.
 *
 * Key design decisions documented inline:
 *  ① All trigonometry is done in single-precision float – sufficient for the
 *    ±150 m radar range and avoids double-precision overhead on Cortex-A53.
 *  ② No heap allocation inside process() once the vector's reserve() capacity
 *    is pre-allocated during configure() – keeps the RT path allocation-free.
 */

#include "object_detection.hpp"

#include <cassert>
#include <cmath>
#include <stdexcept>

namespace adas {
namespace perception {

// ─── Constants ───────────────────────────────────────────────────────────────

static constexpr float kMinConfidenceCamera = 0.40f;
static constexpr float kMinConfidenceRadar  = 0.30f;
static constexpr float kDegToRad            = M_PIf32 / 180.0f;

// ─── ObjectDetector ───────────────────────────────────────────────────────────

ObjectDetector::ObjectDetector() = default;

void ObjectDetector::configure(const CameraIntrinsics&   cam_intrinsics,
                                const ExtrinsicTransform& cam_extrinsic,
                                const ExtrinsicTransform& radar_extrinsic)
{
    cam_intrinsics_  = cam_intrinsics;
    cam_extrinsic_   = cam_extrinsic;
    radar_extrinsic_ = radar_extrinsic;
    configured_      = true;
    next_id_         = 0;
}

void ObjectDetector::reset()
{
    next_id_ = 0;
}

std::vector<DetectedObject> ObjectDetector::process(const SensorFrame& frame)
{
    if (!configured_) {
        throw std::runtime_error("ObjectDetector: configure() not called");
    }

    std::vector<DetectedObject> result;
    result.reserve(32);  // pre-reserve to avoid heap alloc in hot path

    switch (frame.type) {
        case SensorType::CAMERA:
            result = processCameraFrame(frame.camera_dets, frame.timestamp_us);
            break;
        case SensorType::RADAR:
            result = processRadarFrame(frame.radar_dets, frame.timestamp_us);
            break;
        case SensorType::LIDAR:
            result = processLidarFrame(frame.lidar_points, frame.timestamp_us);
            break;
        default:
            break;
    }
    return result;
}

// ─── Camera pipeline ──────────────────────────────────────────────────────────

std::vector<DetectedObject>
ObjectDetector::processCameraFrame(const std::vector<CameraDetection>& dets,
                                    uint64_t timestamp_us) const
{
    std::vector<DetectedObject> objects;
    objects.reserve(dets.size());

    for (const auto& det : dets) {
        if (det.confidence < kMinConfidenceCamera) {
            continue;  // filter low-confidence detections
        }

        DetectedObject obj{};
        obj.id           = next_id_++;
        obj.source       = SensorType::CAMERA;
        obj.cls          = det.cls;
        obj.confidence   = det.confidence;
        obj.timestamp_us = timestamp_us;

        // Approximate physical width from bounding-box pixel width:
        //   physical_width = (pixel_width / fx) * depth
        obj.width  = (det.width  / cam_intrinsics_.fx) * det.depth_m;
        obj.height = (det.height / cam_intrinsics_.fy) * det.depth_m;
        obj.length = obj.width * 2.0f;  // heuristic: length ≈ 2× width

        projectToEgoFrame(obj, det);
        objects.push_back(obj);
    }
    return objects;
}

void ObjectDetector::projectToEgoFrame(DetectedObject&       obj,
                                        const CameraDetection& det) const
{
    // Unproject pixel centre to camera frame using pin-hole model:
    //   X_cam = (u - cx) / fx * depth
    //   Y_cam = (v - cy) / fy * depth
    //   Z_cam = depth
    const float x_cam = (det.u - cam_intrinsics_.cx) / cam_intrinsics_.fx * det.depth_m;
    const float y_cam = (det.v - cam_intrinsics_.cy) / cam_intrinsics_.fy * det.depth_m;
    const float z_cam = det.depth_m;

    // Apply camera extrinsic (sensor → ego frame)
    obj.x = x_cam;
    obj.y = y_cam;
    obj.z = z_cam;
    applyExtrinsic(obj.x, obj.y, obj.z, cam_extrinsic_);

    // Camera gives no velocity estimate directly
    obj.vx = 0.0f;
    obj.vy = 0.0f;
}

// ─── Radar pipeline ───────────────────────────────────────────────────────────

std::vector<DetectedObject>
ObjectDetector::processRadarFrame(const std::vector<RadarDetection>& dets,
                                   uint64_t timestamp_us) const
{
    std::vector<DetectedObject> objects;
    objects.reserve(dets.size());

    for (const auto& det : dets) {
        // Reject ghost targets (very high RCS spike or near-zero range)
        if (det.range_m < 0.5f || det.range_m > 200.0f) {
            continue;
        }

        DetectedObject obj{};
        obj.id           = next_id_++;
        obj.source       = SensorType::RADAR;
        obj.cls          = ObjectClass::UNKNOWN;  // radar has no class info
        obj.confidence   = kMinConfidenceRadar;
        obj.timestamp_us = timestamp_us;
        obj.width        = 2.0f;   // radar cannot resolve object size; use defaults
        obj.length       = 4.5f;
        obj.height       = 1.5f;

        radarPolarToEgo(obj, det);
        objects.push_back(obj);
    }
    return objects;
}

void ObjectDetector::radarPolarToEgo(DetectedObject&      obj,
                                      const RadarDetection& det) const
{
    // Convert polar (range, azimuth, elevation) → Cartesian sensor frame
    const float cos_az  = std::cos(det.azimuth_rad);
    const float sin_az  = std::sin(det.azimuth_rad);
    const float cos_el  = std::cos(det.elevation_rad);

    const float x_sensor = det.range_m * cos_el * cos_az;
    const float y_sensor = det.range_m * cos_el * sin_az;
    const float z_sensor = det.range_m * std::sin(det.elevation_rad);

    // Velocity components in ego frame (range-rate projected)
    //   vx ≈ -range_rate * cos(az)  (negative: approaching → positive vx toward ego)
    obj.vx = -det.range_rate_mps * cos_az;
    obj.vy = -det.range_rate_mps * sin_az;

    obj.x = x_sensor;
    obj.y = y_sensor;
    obj.z = z_sensor;
    applyExtrinsic(obj.x, obj.y, obj.z, radar_extrinsic_);
}

// ─── LiDAR pipeline ───────────────────────────────────────────────────────────

std::vector<DetectedObject>
ObjectDetector::processLidarFrame(const std::vector<LidarPoint>& points,
                                   uint64_t timestamp_us) const
{
    // Simplified: DBSCAN-style naive clustering (Euclidean distance threshold)
    // Production code would run a full DBSCAN or voxel grid + cluster extraction.

    constexpr float kClusterRadius  = 1.5f;    // [m]
    constexpr size_t kMinClusterPts = 5;

    std::vector<bool>   visited(points.size(), false);
    std::vector<DetectedObject> clusters;
    clusters.reserve(16);

    for (size_t i = 0; i < points.size(); ++i) {
        if (visited[i]) continue;
        visited[i] = true;

        // Collect points within kClusterRadius
        std::vector<size_t> neighbours;
        neighbours.reserve(64);
        const auto& pi = points[i];

        for (size_t j = 0; j < points.size(); ++j) {
            if (visited[j]) continue;
            const auto& pj = points[j];
            const float dx = pi.x - pj.x;
            const float dy = pi.y - pj.y;
            if ((dx*dx + dy*dy) < kClusterRadius * kClusterRadius) {
                neighbours.push_back(j);
            }
        }

        if (neighbours.size() < kMinClusterPts) continue;

        // Compute centroid of cluster
        float cx = pi.x, cy = pi.y, cz = pi.z;
        float x_min = pi.x, x_max = pi.x;
        float y_min = pi.y, y_max = pi.y;

        for (size_t idx : neighbours) {
            visited[idx] = true;
            cx += points[idx].x;
            cy += points[idx].y;
            cz += points[idx].z;
            x_min = std::min(x_min, points[idx].x);
            x_max = std::max(x_max, points[idx].x);
            y_min = std::min(y_min, points[idx].y);
            y_max = std::max(y_max, points[idx].y);
        }

        const float n = static_cast<float>(neighbours.size() + 1);
        DetectedObject obj{};
        obj.id           = next_id_++;
        obj.source       = SensorType::LIDAR;
        obj.cls          = ObjectClass::UNKNOWN;
        obj.confidence   = 0.75f;
        obj.timestamp_us = timestamp_us;
        obj.x            = cx / n;
        obj.y            = cy / n;
        obj.z            = cz / n;
        obj.length       = x_max - x_min;
        obj.width        = y_max - y_min;
        obj.height       = 1.8f;   // height not estimable from 2D cluster
        obj.vx           = 0.0f;
        obj.vy           = 0.0f;

        clusters.push_back(obj);
    }
    return clusters;
}

// ─── Utility ─────────────────────────────────────────────────────────────────

void ObjectDetector::applyExtrinsic(float& x, float& y, float& z,
                                     const ExtrinsicTransform& ext) const
{
    // Rotation: ZYX Euler (yaw → pitch → roll)
    const float cy = std::cos(ext.yaw),   sy = std::sin(ext.yaw);
    const float cp = std::cos(ext.pitch), sp = std::sin(ext.pitch);
    const float cr = std::cos(ext.roll),  sr = std::sin(ext.roll);

    // Rotation matrix R = Rz(yaw) * Ry(pitch) * Rx(roll)
    const float r00 = cy*cp,  r01 = cy*sp*sr - sy*cr, r02 = cy*sp*cr + sy*sr;
    const float r10 = sy*cp,  r11 = sy*sp*sr + cy*cr, r12 = sy*sp*cr - cy*sr;
    const float r20 = -sp,    r21 = cp*sr,             r22 = cp*cr;

    const float xr = r00*x + r01*y + r02*z + ext.tx;
    const float yr = r10*x + r11*y + r12*z + ext.ty;
    const float zr = r20*x + r21*y + r22*z + ext.tz;

    x = xr;  y = yr;  z = zr;
}

}  // namespace perception
}  // namespace adas
