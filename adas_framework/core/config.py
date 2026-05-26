# adas_framework/core/config.py
"""
Centralized configuration management for the ADAS test framework.

Loads from:
    1. configs/test_config.yaml  (defaults)
    2. Environment variables     (override)
    3. pytest command-line       (override via conftest)

Usage:
    from core.config import cfg
    cfg.can.bitrate           # 500000
    cfg.uds.bms_tx            # 0x741
    cfg.env.name              # "HIL_LAB_01"
"""
from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Sub-config dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CANConfig:
    channel: str           = "PCAN_USBBUS1"
    interface: str         = "pcan"
    bitrate: int           = 500_000
    fd_bitrate: int        = 2_000_000
    fd_enabled: bool       = False
    dbc_path: str          = "test_data/dbs/ADAS_Network.dbc"
    timeout_s: float       = 0.05
    bus_load_limit_pct: float = 60.0


@dataclass
class UDSConfig:
    ecu_name: str          = "ADAS_ECU"
    tx_id: int             = 0x740
    rx_id: int             = 0x748
    # Extended addresses per ECU
    ecu_map: dict          = field(default_factory=lambda: {
        "ADAS_ECU": {"tx": 0x740, "rx": 0x748},
        "BMS":      {"tx": 0x741, "rx": 0x749},
        "VCU":      {"tx": 0x742, "rx": 0x74A},
        "RADAR_F":  {"tx": 0x744, "rx": 0x74C},
        "CAMERA":   {"tx": 0x745, "rx": 0x74D},
    })
    p2_timeout_s: float    = 2.0
    p2_star_timeout_s: float = 25.0
    s3_timeout_s: float    = 5.0


@dataclass
class RadarConfig:
    target_range_min_m: float     = 0.5
    target_range_max_m: float     = 200.0
    velocity_min_mps: float       = -60.0
    velocity_max_mps: float       = 60.0
    azimuth_fov_deg: float        = 120.0
    update_rate_hz: float         = 20.0
    snr_threshold_db: float       = 10.0
    ghost_object_tolerance: int   = 0
    can_id_object_list: int       = 0x600
    can_id_status: int            = 0x601


@dataclass
class CameraConfig:
    resolution_w: int             = 1920
    resolution_h: int             = 1080
    fps: float                    = 30.0
    lane_detection_confidence: float = 0.85
    sign_detection_confidence: float = 0.80
    object_detection_confidence: float = 0.75
    rtsp_url: str                 = "rtsp://localhost:8554/camera_front"
    calibration_file: str        = "test_data/calibration/camera_front.yaml"


@dataclass
class LiDARConfig:
    point_cloud_min_points: int   = 1000
    max_range_m: float            = 120.0
    vertical_fov_deg: float       = 30.0
    horizontal_fov_deg: float     = 360.0
    update_rate_hz: float         = 10.0
    host: str                     = "192.168.1.100"
    port: int                     = 2368


@dataclass
class EthernetConfig:
    interface: str                = "eth0"
    someip_host: str              = "192.168.1.50"
    someip_port: int              = 30490
    doip_host: str                = "192.168.1.50"
    doip_port: int                = 13400
    target_address: int           = 0x0001
    tester_address: int           = 0x0E00


@dataclass
class HILConfig:
    enabled: bool                 = False
    type: str                     = "dspace"   # dspace | ni_pxi | etas
    host: str                     = "192.168.1.200"
    port: int                     = 8080
    model_path: str               = ""
    startup_timeout_s: float      = 30.0


@dataclass
class ReportConfig:
    output_dir: str               = "reports/"
    allure_dir: str               = "reports/allure-results/"
    html_dir: str                 = "reports/html/"
    log_dir: str                  = "logs/"
    capture_screenshots: bool     = True
    capture_can_logs: bool        = True
    capture_pcap: bool            = False


@dataclass
class EnvironmentConfig:
    name: str                     = "DEV"
    site: str                     = "LOCAL"
    adas_sw_version: str          = "UNKNOWN"
    hw_variant: str               = "EVT"
    vehicle_model: str            = "GENERIC_EV"
    parallel_workers: int         = 4
    retry_count: int              = 2
    retry_delay_s: float          = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Master config
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FrameworkConfig:
    can:      CANConfig      = field(default_factory=CANConfig)
    uds:      UDSConfig      = field(default_factory=UDSConfig)
    radar:    RadarConfig    = field(default_factory=RadarConfig)
    camera:   CameraConfig   = field(default_factory=CameraConfig)
    lidar:    LiDARConfig    = field(default_factory=LiDARConfig)
    ethernet: EthernetConfig = field(default_factory=EthernetConfig)
    hil:      HILConfig      = field(default_factory=HILConfig)
    report:   ReportConfig   = field(default_factory=ReportConfig)
    env:      EnvironmentConfig = field(default_factory=EnvironmentConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "FrameworkConfig":
        """Load config from YAML, apply environment variable overrides."""
        instance = cls()
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            instance._apply_dict(data)
        instance._apply_env_overrides()
        return instance

    def _apply_dict(self, data: dict):
        """Recursively apply YAML dict to dataclass fields."""
        section_map = {
            "can": self.can, "uds": self.uds, "radar": self.radar,
            "camera": self.camera, "lidar": self.lidar, "ethernet": self.ethernet,
            "hil": self.hil, "report": self.report, "env": self.env,
        }
        for section, obj in section_map.items():
            if section in data:
                for k, v in data[section].items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)

    def _apply_env_overrides(self):
        """Allow ENV vars to override config (CI/CD friendly)."""
        overrides = {
            "ADAS_CAN_CHANNEL":       ("can",     "channel"),
            "ADAS_CAN_INTERFACE":     ("can",     "interface"),
            "ADAS_CAN_BITRATE":       ("can",     "bitrate"),
            "ADAS_ENV_NAME":          ("env",     "name"),
            "ADAS_SW_VERSION":        ("env",     "adas_sw_version"),
            "ADAS_HIL_ENABLED":       ("hil",     "enabled"),
            "ADAS_PARALLEL_WORKERS":  ("env",     "parallel_workers"),
            "ADAS_REPORT_DIR":        ("report",  "output_dir"),
        }
        section_map = {
            "can": self.can, "uds": self.uds, "radar": self.radar,
            "camera": self.camera, "lidar": self.lidar, "ethernet": self.ethernet,
            "hil": self.hil, "report": self.report, "env": self.env,
        }
        for env_key, (section, attr) in overrides.items():
            val = os.environ.get(env_key)
            if val is not None:
                obj = section_map[section]
                current = getattr(obj, attr)
                if isinstance(current, bool):
                    setattr(obj, attr, val.lower() in ("1", "true", "yes"))
                elif isinstance(current, int):
                    setattr(obj, attr, int(val))
                elif isinstance(current, float):
                    setattr(obj, attr, float(val))
                else:
                    setattr(obj, attr, val)

    def get(self, path: str, default: Any = None) -> Any:
        """Dot-path access: cfg.get('can.bitrate', 500000)"""
        parts = path.split(".")
        obj = self
        for p in parts:
            obj = getattr(obj, p, None)
            if obj is None:
                return default
        return obj


# Singleton — import and use directly
_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "test_config.yaml"
cfg: FrameworkConfig = FrameworkConfig.from_yaml(_CONFIG_PATH)
