"""
pytest_framework/camera/camera_validator.py

Enterprise ADAS Framework – Camera Image / ADAS Validation
===========================================================
OpenCV-based lane detection, image quality metrics,
object detection result validation, and calibration checks.
Graceful fallback when cv2 not installed (CI headless).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.logger import get_logger

log = get_logger("camera_validator")

try:
    import cv2
    import numpy as np
    _HAS_CV = True
except ImportError:
    _HAS_CV = False
    log.warning("[Camera] OpenCV not installed — image analysis disabled")


@dataclass
class LaneDetectionResult:
    detected:    bool   = False
    left_line:   bool   = False
    right_line:  bool   = False
    center_line: bool   = False
    confidence:  float  = 0.0
    lateral_offset_m: float = 0.0


@dataclass
class ImageQualityMetrics:
    brightness:      float  = 0.0
    blur_score:      float  = 0.0   # Laplacian variance; higher = sharper
    fps:             float  = 0.0
    resolution:      Tuple[int, int] = (0, 0)
    is_dark:         bool   = False
    is_blurry:       bool   = False

    @property
    def is_acceptable(self) -> bool:
        return not self.is_dark and not self.is_blurry


@dataclass
class ObjectDetectionResult:
    label:       str
    confidence:  float
    bbox:        Tuple[int, int, int, int]  # x, y, w, h


class CameraValidator:
    """
    Validates camera frame quality and ADAS function outputs.

    Usage:
        with CameraValidator(source=0) as cam:
            frame  = cam.capture_frame()
            lanes  = cam.detect_lanes(frame)
            cam.assert_lane_detected(lanes)
    """

    def __init__(
        self,
        source:           Any = 0,
        calibration_file: str = "",
        cfg:              Optional[Any] = None,
    ) -> None:
        self._source      = source
        self._cal_file    = calibration_file
        self._cap:        Optional[Any] = None
        self._camera_mat: Optional[Any] = None
        self._dist_coeff: Optional[Any] = None
        self._cfg         = cfg
        self._frame_times: List[float] = []

        if cfg:
            self._target_w   = getattr(cfg, "width",   1920)
            self._target_h   = getattr(cfg, "height",  1080)
            self._target_fps = getattr(cfg, "fps",      30.0)
            self._min_conf   = getattr(cfg, "lane_conf_min", 0.85)
        else:
            self._target_w   = 1920
            self._target_h   = 1080
            self._target_fps = 30.0
            self._min_conf   = 0.85

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def open(self, source: Optional[Any] = None) -> "CameraValidator":
        if not _HAS_CV:
            return self
        src = source if source is not None else self._source
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera source: {src}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._target_w)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._target_h)
        self._cap.set(cv2.CAP_PROP_FPS, self._target_fps)
        if self._cal_file:
            self._load_calibration(self._cal_file)
        log.info(f"[Camera] opened source={src} ({self._target_w}x{self._target_h})")
        return self

    def release(self) -> None:
        if self._cap:
            self._cap.release()
        log.info("[Camera] released")

    def __enter__(self) -> "CameraValidator":
        return self.open()

    def __exit__(self, *_: Any) -> None:
        self.release()

    # ── Frame capture ─────────────────────────────────────────────────────────

    def capture_frame(self) -> Optional[Any]:
        if not _HAS_CV or self._cap is None:
            return None
        t0 = time.monotonic()
        ret, frame = self._cap.read()
        if ret:
            self._frame_times.append(t0)
            if len(self._frame_times) > 100:
                self._frame_times = self._frame_times[-100:]
        return frame if ret else None

    # ── Image quality ─────────────────────────────────────────────────────────

    def analyze_quality(self, frame: Any) -> ImageQualityMetrics:
        if not _HAS_CV or frame is None:
            return ImageQualityMetrics()
        gray        = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness  = float(np.mean(gray))
        blur_score  = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        h, w        = frame.shape[:2]
        fps         = self._compute_fps()
        return ImageQualityMetrics(
            brightness  = brightness,
            blur_score  = blur_score,
            fps         = fps,
            resolution  = (w, h),
            is_dark     = brightness < 30.0,
            is_blurry   = blur_score < 100.0,
        )

    # ── Lane detection ────────────────────────────────────────────────────────

    def detect_lanes(self, frame: Any) -> LaneDetectionResult:
        if not _HAS_CV or frame is None:
            return LaneDetectionResult()
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        # ROI mask — lower 40% of frame
        mask = np.zeros_like(edges)
        roi  = np.array([[
            (0, h), (w // 4, int(h * 0.6)),
            (3 * w // 4, int(h * 0.6)), (w, h)
        ]], dtype=np.int32)
        cv2.fillPoly(mask, roi, 255)
        masked = cv2.bitwise_and(edges, mask)
        lines = cv2.HoughLinesP(
            masked, 1, np.pi / 180,
            threshold=50, minLineLength=100, maxLineGap=50
        )
        if lines is None:
            return LaneDetectionResult(detected=False)
        left   = [l for l in lines if l[0][0] < w // 2]
        right  = [l for l in lines if l[0][0] >= w // 2]
        conf   = min(1.0, (len(left) + len(right)) / 10.0)
        return LaneDetectionResult(
            detected     = len(lines) >= 2,
            left_line    = len(left)  >= 1,
            right_line   = len(right) >= 1,
            center_line  = False,
            confidence   = conf,
        )

    # ── Undistortion ─────────────────────────────────────────────────────────

    def undistort(self, frame: Any) -> Any:
        if not _HAS_CV or self._camera_mat is None:
            return frame
        return cv2.undistort(frame, self._camera_mat, self._dist_coeff)

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_lane_detected(
        self, result: LaneDetectionResult, min_confidence: Optional[float] = None
    ) -> None:
        assert result.detected, "Camera: lane detection failed — no lane lines found"
        min_c = min_confidence or self._min_conf
        assert result.confidence >= min_c, (
            f"Camera: lane confidence {result.confidence:.2f} below minimum {min_c}"
        )

    def assert_image_quality(self, metrics: ImageQualityMetrics) -> None:
        assert not metrics.is_dark,   f"Camera: image too dark (brightness={metrics.brightness:.1f})"
        assert not metrics.is_blurry, f"Camera: image too blurry (blur_score={metrics.blur_score:.1f})"

    def assert_fps(self, min_fps: Optional[float] = None) -> None:
        fps   = self._compute_fps()
        limit = min_fps or (self._target_fps * 0.9)
        assert fps >= limit, (
            f"Camera: FPS {fps:.1f} below minimum {limit:.1f}"
        )

    def assert_resolution(self, frame: Any) -> None:
        if not _HAS_CV or frame is None:
            return
        h, w = frame.shape[:2]
        assert w == self._target_w and h == self._target_h, (
            f"Camera: resolution {w}x{h} != target {self._target_w}x{self._target_h}"
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _compute_fps(self) -> float:
        ts = self._frame_times
        if len(ts) < 2:
            return 0.0
        return (len(ts) - 1) / (ts[-1] - ts[0])

    def _load_calibration(self, path: str) -> None:
        if not _HAS_CV:
            return
        try:
            fs = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)
            self._camera_mat = fs.getNode("camera_matrix").mat()
            self._dist_coeff = fs.getNode("dist_coeffs").mat()
            fs.release()
            log.info(f"[Camera] calibration loaded: {path}")
        except Exception as exc:
            log.warning(f"[Camera] calibration load failed: {exc!r}")
