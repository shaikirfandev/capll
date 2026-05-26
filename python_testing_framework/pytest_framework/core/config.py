"""
pytest_framework/core/config.py

Enterprise ADAS Framework – Master Configuration
=================================================
Singleton config loaded from configs/framework_config.yaml.
All values overridable via ADAS_* environment variables.
Thread-safe; supports multi-process test workers (pytest-xdist).
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_LOCK = threading.Lock()
_INSTANCE: Optional["FrameworkConfig"] = None

BASE_DIR = Path(__file__).resolve().parents[3]  # repo root
DEFAULT_CFG = BASE_DIR / "configs" / "framework_config.yaml"


@dataclass
class CANConfig:
    channel: str = "virtual"
    interface: str = "virtual"
    bitrate: int = 500_000
    fd_bitrate: int = 2_000_000
    fd_enabled: bool = False
    dbc_path: str = ""
    timeout_s: float = 0.5


@dataclass
class EthernetConfig:
    host: str = "127.0.0.1"
    someip_port: int = 30490
    doip_port: int = 13400
    pcap_iface: str = "lo"


@dataclass
class UDSConfig:
    ecu_map: Dict[str, Dict[str, int]] = field(default_factory=dict)
    default_ecu: str = "ADAS_ECU"
    p2_timeout_s: float = 2.0
    p2_ext_timeout_s: float = 5.0


@dataclass
class RadarConfig:
    range_min_m: float = 0.5
    range_max_m: float = 250.0
    velocity_min_mps: float = -80.0
    velocity_max_mps: float = 80.0
    update_rate_hz: float = 20.0
    snr_threshold_db: float = 5.0


@dataclass
class CameraConfig:
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    lane_conf_min: float = 0.85
    calibration_file: str = ""


@dataclass
class LiDARConfig:
    host: str = "127.0.0.1"
    port: int = 2368
    range_max_m: float = 100.0
    min_points: int = 1000
    update_rate_hz: float = 10.0


@dataclass
class HILConfig:
    enabled: bool = False
    canoe_project: str = ""
    dspace_host: str = ""
    carmaker_host: str = ""
    sync_timeout_s: float = 30.0


@dataclass
class ReportConfig:
    output_dir: str = "reports"
    allure_results: str = "allure-results"
    html_report: str = "reports/report.html"
    excel_report: str = "reports/report.xlsx"
    grafana_url: str = "http://localhost:3000"
    influx_url: str = "http://localhost:8086"
    influx_token: str = ""
    influx_bucket: str = "adas_tests"
    influx_org: str = "adas"


@dataclass
class FrameworkConfig:
    environment: str = "ci"
    sw_version: str = "0.0.0"
    hil_enabled: bool = False
    can: CANConfig = field(default_factory=CANConfig)
    ethernet: EthernetConfig = field(default_factory=EthernetConfig)
    uds: UDSConfig = field(default_factory=UDSConfig)
    radar: RadarConfig = field(default_factory=RadarConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    lidar: LiDARConfig = field(default_factory=LiDARConfig)
    hil: HILConfig = field(default_factory=HILConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    timing_limits: Dict[str, float] = field(default_factory=dict)
    dtc_map: Dict[str, str] = field(default_factory=dict)

    # ── ENV overrides ─────────────────────────────────────────────────────────
    def apply_env_overrides(self) -> None:
        _env = os.environ.get
        if v := _env("ADAS_ENVIRONMENT"):
            self.environment = v
        if v := _env("ADAS_SW_VERSION"):
            self.sw_version = v
        if v := _env("ADAS_CAN_CHANNEL"):
            self.can.channel = v
        if v := _env("ADAS_CAN_INTERFACE"):
            self.can.interface = v
        if v := _env("ADAS_CAN_BITRATE"):
            self.can.bitrate = int(v)
        if v := _env("ADAS_DBC_PATH"):
            self.can.dbc_path = v
        if v := _env("ADAS_HIL_ENABLED"):
            self.hil_enabled = v.lower() in ("1", "true", "yes")
        if v := _env("ADAS_INFLUX_TOKEN"):
            self.report.influx_token = v


def _parse_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _build(raw: Dict[str, Any]) -> FrameworkConfig:
    cfg = FrameworkConfig()
    if can := raw.get("can", {}):
        cfg.can = CANConfig(**{k: v for k, v in can.items()
                               if k in CANConfig.__dataclass_fields__})
    if eth := raw.get("ethernet", {}):
        cfg.ethernet = EthernetConfig(**{k: v for k, v in eth.items()
                                         if k in EthernetConfig.__dataclass_fields__})
    if uds := raw.get("uds", {}):
        ecu_map = uds.pop("ecu_map", {})
        cfg.uds = UDSConfig(**{k: v for k, v in uds.items()
                                if k in UDSConfig.__dataclass_fields__})
        cfg.uds.ecu_map = ecu_map
    if rad := raw.get("radar", {}):
        cfg.radar = RadarConfig(**{k: v for k, v in rad.items()
                                   if k in RadarConfig.__dataclass_fields__})
    if cam := raw.get("camera", {}):
        cfg.camera = CameraConfig(**{k: v for k, v in cam.items()
                                     if k in CameraConfig.__dataclass_fields__})
    if lid := raw.get("lidar", {}):
        cfg.lidar = LiDARConfig(**{k: v for k, v in lid.items()
                                   if k in LiDARConfig.__dataclass_fields__})
    if hil := raw.get("hil", {}):
        cfg.hil = HILConfig(**{k: v for k, v in hil.items()
                                if k in HILConfig.__dataclass_fields__})
    if rep := raw.get("report", {}):
        cfg.report = ReportConfig(**{k: v for k, v in rep.items()
                                     if k in ReportConfig.__dataclass_fields__})
    cfg.timing_limits = raw.get("timing_limits", {})
    cfg.dtc_map = raw.get("dtc_map", {})
    cfg.environment = raw.get("environment", "ci")
    return cfg


def get_config(config_file: Optional[Path] = None) -> FrameworkConfig:
    """Return singleton FrameworkConfig, thread-safe."""
    global _INSTANCE
    if _INSTANCE is None:
        with _LOCK:
            if _INSTANCE is None:
                path = config_file or DEFAULT_CFG
                raw = _parse_yaml(path)
                _INSTANCE = _build(raw)
                _INSTANCE.apply_env_overrides()
    return _INSTANCE


def reset_config() -> None:
    """Force reload (used in testing)."""
    global _INSTANCE
    with _LOCK:
        _INSTANCE = None
