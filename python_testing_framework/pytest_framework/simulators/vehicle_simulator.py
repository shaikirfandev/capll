"""
pytest_framework/simulators/vehicle_simulator.py

Enterprise ADAS Framework – Vehicle + Sensor Simulator
=======================================================
Generates synthetic CAN signals, radar objects, camera frames,
and LiDAR point clouds for SIL / CI headless testing.
All simulators are thread-safe and injectable into fixtures.
"""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from can.signal_validator import SignalValidator
from core.logger import get_logger
from radar.radar_validator import RadarObject
from sensor_fusion.fusion_validator import FusedObject
from lidar.lidar_validator import LiDARPoint, PointCloud

log = get_logger("vehicle_simulator")


# ── Vehicle State Simulator ───────────────────────────────────────────────────

@dataclass
class VehicleState:
    speed_kmh:      float = 100.0
    heading_deg:    float = 0.0
    lateral_offset_m: float = 0.0
    gear:           int   = 4
    engine_rpm:     float = 2000.0
    brake_pressure_bar: float = 0.0
    driver_torque_nm:   float = 0.0
    turn_signal:    int   = 0   # 0=off 1=left 2=right
    acc_active:     bool  = False
    aeb_active:     bool  = False
    lka_active:     bool  = False


class VehicleSimulator:
    """
    Publishes synthetic vehicle signals to a SignalValidator.

    Usage:
        sim = VehicleSimulator(signals)
        sim.set_speed(120.0)
        sim.start(interval_s=0.02)
        ...
        sim.stop()
    """

    def __init__(self, signals: SignalValidator) -> None:
        self._sv    = signals
        self._state = VehicleState()
        self._lock  = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop  = threading.Event()

    def set_speed(self, kmh: float) -> None:
        with self._lock:
            self._state.speed_kmh = kmh

    def set_brake(self, bar: float) -> None:
        with self._lock:
            self._state.brake_pressure_bar = bar

    def set_turn_signal(self, direction: int) -> None:
        with self._lock:
            self._state.turn_signal = direction

    def set_lateral_offset(self, m: float) -> None:
        with self._lock:
            self._state.lateral_offset_m = m

    def activate_acc(self, active: bool = True) -> None:
        with self._lock:
            self._state.acc_active = active

    def activate_aeb(self, active: bool = True) -> None:
        with self._lock:
            self._state.aeb_active = active

    def start(self, interval_s: float = 0.02) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._publish_loop,
            args=(interval_s,),
            daemon=True,
            name="vehicle-sim",
        )
        self._thread.start()
        log.info("[VehicleSim] started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("[VehicleSim] stopped")

    def _publish_loop(self, interval_s: float) -> None:
        while not self._stop.is_set():
            with self._lock:
                state = VehicleState(**self._state.__dict__)
            self._sv.update("VehicleSpeed_kmh",        state.speed_kmh)
            self._sv.update("VehicleHeading_deg",      state.heading_deg)
            self._sv.update("LKA_LateralOffset_m",     state.lateral_offset_m)
            self._sv.update("DriverBrakePressure_bar", state.brake_pressure_bar)
            self._sv.update("SteeringDriverTorque_Nm", state.driver_torque_nm)
            self._sv.update("TurnSignalActive",        state.turn_signal)
            self._sv.update("ACC_Status",              2 if state.acc_active else 0)
            self._sv.update("AEB_Status",              3 if state.aeb_active else 0)
            self._sv.update("EngineRPM",               state.engine_rpm)
            time.sleep(interval_s)


# ── Radar Simulator ───────────────────────────────────────────────────────────

class RadarSimulator:
    """
    Generates synthetic radar objects and feeds them to a RadarValidator.

    Usage:
        sim = RadarSimulator(radar_validator)
        sim.add_target(range_m=50, velocity_mps=-5, azimuth_deg=0)
        sim.start()
    """

    def __init__(self, validator: Any) -> None:
        self._validator = validator
        self._targets: List[Dict[str, Any]] = []
        self._lock    = threading.Lock()
        self._stop    = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._obj_id_counter = 0

    def add_target(
        self,
        range_m:      float,
        velocity_mps: float = 0.0,
        azimuth_deg:  float = 0.0,
        rcs_dbm:      float = 15.0,
        confidence:   float = 0.95,
    ) -> int:
        with self._lock:
            self._obj_id_counter += 1
            oid = self._obj_id_counter
            self._targets.append({
                "obj_id":       oid,
                "range_m":      range_m,
                "velocity_mps": velocity_mps,
                "azimuth_deg":  azimuth_deg,
                "rcs_dbm":      rcs_dbm,
                "confidence":   confidence,
            })
            return oid

    def remove_target(self, obj_id: int) -> None:
        with self._lock:
            self._targets = [t for t in self._targets if t["obj_id"] != obj_id]

    def start(self, rate_hz: float = 20.0) -> None:
        self._stop.clear()
        interval = 1.0 / rate_hz
        self._thread = threading.Thread(
            target=self._emit_loop,
            args=(interval,),
            daemon=True,
            name="radar-sim",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _emit_loop(self, interval: float) -> None:
        while not self._stop.is_set():
            with self._lock:
                targets = list(self._targets)
            for t in targets:
                obj = RadarObject(
                    obj_id       = t["obj_id"],
                    range_m      = t["range_m"] + random.gauss(0, 0.05),
                    velocity_mps = t["velocity_mps"],
                    azimuth_deg  = t["azimuth_deg"],
                    rcs_dbm      = t["rcs_dbm"],
                    confidence   = t["confidence"],
                )
                self._validator.ingest_object(obj)
            time.sleep(interval)


# ── LiDAR Simulator ───────────────────────────────────────────────────────────

class LiDARSimulator:
    """
    Generates synthetic point clouds from simple obstacle primitives.
    """

    def __init__(self, validator: Any) -> None:
        self._validator = validator
        self._obstacles: List[Dict[str, float]] = []
        self._stop  = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def add_obstacle(self, x_m: float, y_m: float, z_m: float = 0.0,
                     radius_m: float = 1.0) -> None:
        self._obstacles.append({"x": x_m, "y": y_m, "z": z_m, "r": radius_m})

    def start(self, rate_hz: float = 10.0) -> None:
        self._stop.clear()
        interval = 1.0 / rate_hz
        self._thread = threading.Thread(
            target=self._emit_loop,
            args=(interval,),
            daemon=True,
            name="lidar-sim",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _emit_loop(self, interval: float) -> None:
        while not self._stop.is_set():
            points: List[LiDARPoint] = []
            # Ground plane
            for i in range(100):
                angle = i * (2 * math.pi / 100)
                for d in [10, 20, 30, 50]:
                    x = d * math.cos(angle)
                    y = d * math.sin(angle)
                    points.append(LiDARPoint(x=x, y=y, z=-1.5,
                                             intensity=float(random.randint(20, 60))))
            # Obstacles
            for obs in self._obstacles:
                r = obs["r"]
                for _ in range(50):
                    theta = random.uniform(0, 2 * math.pi)
                    px = obs["x"] + r * math.cos(theta)
                    py = obs["y"] + r * math.sin(theta)
                    pz = obs["z"] + random.uniform(0, 2)
                    points.append(LiDARPoint(x=px, y=py, z=pz, intensity=80.0))
            self._validator.ingest_cloud(PointCloud(points=points))
            time.sleep(interval)


# ── GPS / GNSS Simulator ──────────────────────────────────────────────────────

class GPSSimulator:
    """Simulates GNSS signal for map-matching and localization tests."""

    def __init__(self, signals: SignalValidator) -> None:
        self._sv   = signals
        self._lat  = 48.8566
        self._lon  = 2.3522
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def set_position(self, lat: float, lon: float) -> None:
        self._lat, self._lon = lat, lon

    def start(self, rate_hz: float = 1.0) -> None:
        self._stop.clear()
        interval = 1.0 / rate_hz
        self._thread = threading.Thread(
            target=self._emit_loop, args=(interval,),
            daemon=True, name="gps-sim"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _emit_loop(self, interval: float) -> None:
        while not self._stop.is_set():
            self._sv.update("GPS_Latitude",  self._lat + random.gauss(0, 0.00001))
            self._sv.update("GPS_Longitude", self._lon + random.gauss(0, 0.00001))
            self._sv.update("GPS_Accuracy_m", 2.5)
            self._sv.update("GPS_Fix",       1)
            time.sleep(interval)
