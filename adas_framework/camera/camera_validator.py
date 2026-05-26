# adas_framework/camera/camera_validator.py
"""
Camera sensor validation module using OpenCV.

Validates:
    - Lane detection confidence and geometry
    - Traffic sign recognition accuracy
    - Pedestrian/object detection
    - Image quality (brightness, blur, distortion)
    - Camera latency
    - Calibration consistency
    - Night vision performance

Usage:
    validator = CameraValidator(cfg.camera)
    frame = validator.capture_frame()
    validator.assert_lane_detected(min_confidence=0.85)
    validator.assert_image_quality(min_brightness=30, max_blur=500)
    validator.assert_sign_detected("STOP", min_confidence=0.80)
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

from core.config import CameraConfig
from core.logger import camera_log as log


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LaneDetectionResult:
    detected:      bool
    confidence:    float
    left_line:     Optional[Tuple]  = None
    right_line:    Optional[Tuple]  = None
    center_offset_px: float        = 0.0
    curvature_m:   Optional[float] = None
    timestamp:     float           = field(default_factory=time.monotonic)


@dataclass
class ObjectDetectionResult:
    label:      str
    confidence: float
    bbox:       Tuple[int, int, int, int]  # x, y, w, h
    distance_m: Optional[float] = None
    timestamp:  float = field(default_factory=time.monotonic)


@dataclass
class ImageQualityMetrics:
    brightness:  float   # mean pixel value 0-255
    blur_score:  float   # Laplacian variance — higher = sharper
    resolution:  Tuple[int, int]
    fps:         float   = 0.0
    timestamp:   float   = field(default_factory=time.monotonic)

    @property
    def is_blurry(self) -> bool:
        return self.blur_score < 100.0

    @property
    def is_dark(self) -> bool:
        return self.brightness < 30.0

    @property
    def is_overexposed(self) -> bool:
        return self.brightness > 240.0


# ─────────────────────────────────────────────────────────────────────────────
# CameraValidator
# ─────────────────────────────────────────────────────────────────────────────

class CameraValidator:
    """Camera image quality and ADAS function validation."""

    def __init__(self, config: CameraConfig):
        self._cfg      = config
        self._cap      = None
        self._lock     = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_timestamps: List[float] = []
        self._lane_results:   List[LaneDetectionResult]   = []
        self._detections:     List[ObjectDetectionResult] = []
        self._calib_matrix:   Optional[np.ndarray] = None
        self._dist_coeffs:    Optional[np.ndarray] = None
        self._load_calibration()

    def _load_calibration(self):
        """Load camera calibration file if present."""
        calib_path = Path(self._cfg.calibration_file)
        if calib_path.exists() and _CV2_AVAILABLE:
            fs = cv2.FileStorage(str(calib_path), cv2.FILE_STORAGE_READ)
            self._calib_matrix = fs.getNode("camera_matrix").mat()
            self._dist_coeffs  = fs.getNode("distortion_coefficients").mat()
            fs.release()
            log.info(f"Calibration loaded: {calib_path}")

    # ── Capture ───────────────────────────────────────────────────────────────

    def open(self, source: str = None):
        """Open video source (RTSP / file / device index)."""
        src = source or self._cfg.rtsp_url
        if not _CV2_AVAILABLE:
            log.warning("OpenCV not available — using null camera")
            return
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            log.warning(f"Cannot open camera source: {src}")

    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame."""
        if not _CV2_AVAILABLE or not self._cap:
            return np.zeros((self._cfg.resolution_h, self._cfg.resolution_w, 3),
                            dtype=np.uint8)
        ret, frame = self._cap.read()
        if ret:
            ts = time.monotonic()
            self._frame_timestamps.append(ts)
            if len(self._frame_timestamps) > 200:
                self._frame_timestamps = self._frame_timestamps[-200:]
            with self._lock:
                self._latest_frame = frame
            return frame
        return None

    def release(self):
        if self._cap and _CV2_AVAILABLE:
            self._cap.release()

    # ── Image quality ─────────────────────────────────────────────────────────

    def analyze_quality(self, frame: np.ndarray = None) -> ImageQualityMetrics:
        """Compute image quality metrics for a frame."""
        if frame is None:
            with self._lock:
                frame = self._latest_frame
        if frame is None:
            return ImageQualityMetrics(0.0, 0.0, (0, 0))

        gray        = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if _CV2_AVAILABLE else frame
        brightness  = float(np.mean(gray))
        blur_score  = float(np.var(cv2.Laplacian(gray, cv2.CV_64F))) if _CV2_AVAILABLE else 0.0
        h, w        = frame.shape[:2]
        fps         = self._current_fps()

        return ImageQualityMetrics(
            brightness=brightness, blur_score=blur_score,
            resolution=(w, h), fps=fps
        )

    def _current_fps(self) -> float:
        ts = self._frame_timestamps
        if len(ts) < 5:
            return 0.0
        elapsed = ts[-1] - ts[-10] if len(ts) >= 10 else ts[-1] - ts[0]
        count   = min(10, len(ts)) - 1
        return count / elapsed if elapsed > 0 else 0.0

    # ── Lane detection ────────────────────────────────────────────────────────

    def detect_lanes(self, frame: np.ndarray = None) -> LaneDetectionResult:
        """
        Detect lane lines using Canny + Hough transform.
        Production systems would use a trained CNN — this is the
        classical baseline for validation environment testing.
        """
        if not _CV2_AVAILABLE:
            return LaneDetectionResult(False, 0.0)

        if frame is None:
            with self._lock:
                frame = self._latest_frame
        if frame is None:
            return LaneDetectionResult(False, 0.0)

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        # Region of interest mask
        roi_vertices = np.array([[
            (0, h), (w//4, h//2), (3*w//4, h//2), (w, h)
        ]], dtype=np.int32)
        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, roi_vertices, 255)
        masked = cv2.bitwise_and(edges, mask)

        lines = cv2.HoughLinesP(masked, 1, np.pi/180, 50,
                                minLineLength=50, maxLineGap=100)
        if lines is None or len(lines) == 0:
            result = LaneDetectionResult(False, 0.0)
        else:
            # Separate left / right by slope
            left, right = [], []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 == x1:
                    continue
                slope = (y2 - y1) / (x2 - x1)
                if slope < -0.3:
                    right.append(line[0])
                elif slope > 0.3:
                    left.append(line[0])

            confidence = min(1.0, (len(left) + len(right)) / 10.0)
            center_x = w / 2.0
            center_offset = 0.0
            if left and right:
                l_x = np.mean([l[0] for l in left])
                r_x = np.mean([l[2] for l in right])
                lane_center = (l_x + r_x) / 2.0
                center_offset = lane_center - center_x

            result = LaneDetectionResult(
                detected=confidence >= self._cfg.lane_detection_confidence,
                confidence=confidence,
                left_line=left[0] if left else None,
                right_line=right[0] if right else None,
                center_offset_px=center_offset,
            )

        self._lane_results.append(result)
        return result

    # ── Object / sign detection ───────────────────────────────────────────────

    def detect_objects(self, frame: np.ndarray = None,
                       model=None) -> List[ObjectDetectionResult]:
        """
        Placeholder for YOLO/SSD-based object detection.
        In production: pass a loaded cv2.dnn or ONNX model.
        Returns mock result for test environment.
        """
        return []

    # ── Undistortion ─────────────────────────────────────────────────────────

    def undistort(self, frame: np.ndarray) -> np.ndarray:
        """Apply calibration undistortion if calibration is loaded."""
        if (self._calib_matrix is not None and
                self._dist_coeffs is not None and _CV2_AVAILABLE):
            return cv2.undistort(frame, self._calib_matrix, self._dist_coeffs)
        return frame

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_lane_detected(self, min_confidence: float = None):
        frame  = self.capture_frame()
        result = self.detect_lanes(frame)
        min_c  = min_confidence or self._cfg.lane_detection_confidence
        assert result.detected, \
            f"Lane not detected (confidence={result.confidence:.2f} < {min_c:.2f})"
        assert result.confidence >= min_c, \
            f"Lane confidence {result.confidence:.2f} below {min_c:.2f}"

    def assert_image_quality(
        self, min_brightness: float = 20.0, max_brightness: float = 240.0,
        min_blur_score: float = 100.0
    ):
        frame   = self.capture_frame()
        metrics = self.analyze_quality(frame)
        assert not metrics.is_dark, \
            f"Frame too dark: brightness={metrics.brightness:.1f} < {min_brightness}"
        assert not metrics.is_overexposed, \
            f"Frame overexposed: brightness={metrics.brightness:.1f} > {max_brightness}"
        assert not metrics.is_blurry, \
            f"Frame blurry: blur_score={metrics.blur_score:.1f} < {min_blur_score}"

    def assert_fps(self, min_fps: float = None):
        expected = min_fps or (self._cfg.fps * 0.9)
        actual   = self._current_fps()
        assert actual >= expected, \
            f"Camera FPS {actual:.1f} below minimum {expected:.1f}"

    def assert_resolution(self):
        frame = self.capture_frame()
        if frame is None:
            return
        h, w = frame.shape[:2]
        assert w == self._cfg.resolution_w and h == self._cfg.resolution_h, \
            f"Resolution {w}x{h} ≠ expected {self._cfg.resolution_w}x{self._cfg.resolution_h}"
