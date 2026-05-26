"""
pytest_framework/conftest.py

Enterprise ADAS Hybrid Framework – Root pytest Configuration
=============================================================
Session-scoped:   framework_cfg, can_bus, signals, event_loop,
                  radar, camera, lidar, fusion, uds, dtc_monitor,
                  fault_injector, vehicle_sim, radar_sim
Function-scoped:  uds_extended
Autouse:          skip_no_hardware, inject_allure_metadata,
                  test_log_context
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Generator

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from core.config       import FrameworkConfig, get_config
from core.logger       import get_logger
from core.retry        import FlakyTracker
from can.can_interface import CANInterface
from can.signal_validator import SignalValidator
from diagnostics.uds_client import UDSClient
from diagnostics.dtc_handler import DTCMonitor
from radar.radar_validator   import RadarValidator
from camera.camera_validator import CameraValidator
from lidar.lidar_validator   import LiDARValidator
from sensor_fusion.fusion_validator import FusionValidator
from simulators.vehicle_simulator   import (
    VehicleSimulator, RadarSimulator, LiDARSimulator, GPSSimulator
)
from utilities.fault_injector import FaultInjector

log = get_logger("conftest")


# ── CLI Options ───────────────────────────────────────────────────────────────

def pytest_addoption(parser: pytest.Parser) -> None:
    grp = parser.getgroup("adas", "ADAS Framework options")
    grp.addoption("--channel",       default="virtual",       help="CAN channel")
    grp.addoption("--interface",     default="virtual",       help="CAN interface")
    grp.addoption("--bitrate",       default=500000, type=int,help="CAN bitrate")
    grp.addoption("--dbc",           default="",              help="Path to DBC file")
    grp.addoption("--ecu",           default="ADAS_ECU",      help="Target ECU name")
    grp.addoption("--env",           default="ci",            help="Environment (ci|hil|sil)")
    grp.addoption("--sw-version",    default="",              help="SW version under test")
    grp.addoption("--hil",           action="store_true",     help="Enable HIL bench")
    grp.addoption("--no-hardware",   action="store_true",     help="Run headless/CI")
    grp.addoption("--config-file",   default="",              help="Custom YAML config path")


# ── Markers ───────────────────────────────────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    markers = [
        # Feature markers
        ("acc",          "Adaptive Cruise Control tests"),
        ("aeb",          "Autonomous Emergency Braking tests"),
        ("lka",          "Lane Keep Assist tests"),
        ("ldw",          "Lane Departure Warning tests"),
        ("bsd",          "Blind Spot Detection tests"),
        ("tsr",          "Traffic Sign Recognition tests"),
        ("dms",          "Driver Monitoring System tests"),
        ("parking",      "Parking Assist / Auto Park tests"),
        ("surround_view","Surround View Camera tests"),
        ("rcta",         "Rear Cross Traffic Alert tests"),
        ("fcw",          "Forward Collision Warning tests"),
        ("pedestrian",   "Pedestrian Detection tests"),
        ("sensor_fusion","Sensor Fusion tests"),
        ("highway_pilot","Highway Pilot / TJA tests"),
        ("esa",          "Emergency Steering Assist tests"),
        ("night_vision",  "Night Vision tests"),
        ("isa",          "Intelligent Speed Assist tests"),
        # Test type markers
        ("smoke",        "Quick sanity smoke tests"),
        ("sanity",       "Sanity suite"),
        ("regression",   "Full regression suite"),
        ("performance",  "Performance / timing tests"),
        ("cybersecurity","Cybersecurity validation"),
        ("uds",          "UDS diagnostic tests"),
        ("can",          "CAN bus level tests"),
        ("ethernet",     "Automotive Ethernet tests"),
        ("hil",          "HIL bench required"),
        ("sil",          "SIL environment tests"),
        # ASIL markers
        ("asil_a",       "ASIL A tests"),
        ("asil_b",       "ASIL B tests"),
        ("asil_c",       "ASIL C tests"),
        ("asil_d",       "ASIL D tests"),
        ("safety",       "Functional safety tests (ASIL A-D)"),
        ("e2e",          "End-to-end scenario tests"),
        ("fault_injection","Fault injection / FMEA tests"),
    ]
    for name, desc in markers:
        config.addinivalue_line("markers", f"{name}: {desc}")


# ── Session fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def framework_cfg(request: pytest.FixtureRequest) -> FrameworkConfig:
    cfg_file = request.config.getoption("--config-file", default="")
    cfg = get_config(Path(cfg_file) if cfg_file else None)
    # CLI overrides
    if ch := request.config.getoption("--channel", default=""):
        cfg.can.channel   = ch
    if iface := request.config.getoption("--interface", default=""):
        cfg.can.interface = iface
    if br := request.config.getoption("--bitrate", default=0):
        if br:
            cfg.can.bitrate = int(br)
    if dbc := request.config.getoption("--dbc", default=""):
        cfg.can.dbc_path = dbc
    if env := request.config.getoption("--env", default=""):
        cfg.environment = env
    if ver := request.config.getoption("--sw-version", default=""):
        cfg.sw_version = ver
    if request.config.getoption("--hil", default=False):
        cfg.hil_enabled = True
    return cfg


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Shared asyncio event loop for async UDS and Ethernet fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def can_bus(framework_cfg: FrameworkConfig) -> Generator[CANInterface, None, None]:
    bus = CANInterface(
        channel    = framework_cfg.can.channel,
        interface  = framework_cfg.can.interface,
        bitrate    = framework_cfg.can.bitrate,
        fd_bitrate = framework_cfg.can.fd_bitrate,
        fd_enabled = framework_cfg.can.fd_enabled,
        dbc_path   = framework_cfg.can.dbc_path,
    )
    bus.connect()
    yield bus
    bus.disconnect()


@pytest.fixture(scope="session")
def signals(can_bus: CANInterface) -> Generator[SignalValidator, None, None]:
    sv = SignalValidator(can_bus)
    sv.start()
    yield sv
    sv.stop()


@pytest.fixture(scope="session")
def vehicle_sim(signals: SignalValidator) -> Generator[VehicleSimulator, None, None]:
    sim = VehicleSimulator(signals)
    sim.start()
    yield sim
    sim.stop()


@pytest.fixture(scope="session")
def radar(framework_cfg: FrameworkConfig) -> RadarValidator:
    return RadarValidator(framework_cfg.radar)


@pytest.fixture(scope="session")
def radar_sim(radar: RadarValidator) -> Generator[RadarSimulator, None, None]:
    sim = RadarSimulator(radar)
    yield sim
    sim.stop()


@pytest.fixture(scope="session")
def camera(framework_cfg: FrameworkConfig) -> Generator[CameraValidator, None, None]:
    cam = CameraValidator(source=0, cfg=framework_cfg.camera)
    # Open only on real hardware; in CI we just yield the validator instance
    yield cam
    cam.release()


@pytest.fixture(scope="session")
def lidar(framework_cfg: FrameworkConfig) -> Generator[LiDARValidator, None, None]:
    lv = LiDARValidator(
        host = framework_cfg.lidar.host,
        port = framework_cfg.lidar.port,
        cfg  = framework_cfg.lidar,
    )
    lv.connect()
    yield lv
    lv.disconnect()


@pytest.fixture(scope="session")
def fusion(framework_cfg: FrameworkConfig) -> FusionValidator:
    return FusionValidator(
        expected_sources = ["radar", "camera", "lidar"]
    )


@pytest.fixture(scope="session")
def uds(framework_cfg: FrameworkConfig) -> Generator[UDSClient, None, None]:
    ecu_name  = "ADAS_ECU"
    ecu_cfg   = framework_cfg.uds.ecu_map.get(ecu_name, {})
    tx_id     = ecu_cfg.get("tx_id", 0x740)
    rx_id     = ecu_cfg.get("rx_id", 0x748)
    client    = UDSClient(tx_id=tx_id, rx_id=rx_id,
                          p2_timeout=framework_cfg.uds.p2_timeout_s)
    client.sync_change_session(0x01)
    yield client
    client.sync_change_session(0x01)
    client.stop_tester_present()


@pytest.fixture(scope="function")
def uds_extended(uds: UDSClient) -> Generator[UDSClient, None, None]:
    """Function-scoped UDS in extended diagnostic session (0x03)."""
    uds.sync_change_session(0x03)
    yield uds
    uds.sync_change_session(0x01)


@pytest.fixture(scope="session")
def dtc_monitor(uds: UDSClient) -> Generator[DTCMonitor, None, None]:
    monitor = DTCMonitor(uds, poll_interval_s=0.5)
    monitor.start()
    yield monitor
    monitor.stop()


@pytest.fixture(scope="session")
def fault_injector(can_bus: CANInterface) -> FaultInjector:
    return FaultInjector(can_bus)


@pytest.fixture(scope="session")
def flaky_tracker() -> FlakyTracker:
    return FlakyTracker()


# ── Autouse fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def skip_no_hardware(request: pytest.FixtureRequest) -> None:
    """Skip @pytest.mark.hil tests when --hil flag absent."""
    if request.node.get_closest_marker("hil"):
        if not request.config.getoption("--hil", default=False):
            pytest.skip("HIL bench not available (use --hil flag)")


@pytest.fixture(autouse=True)
def inject_allure_metadata(
    request: pytest.FixtureRequest,
    framework_cfg: FrameworkConfig,
) -> None:
    """Attach SW version / environment to every test via Allure."""
    try:
        import allure
        allure.dynamic.parameter("sw_version",  framework_cfg.sw_version)
        allure.dynamic.parameter("environment", framework_cfg.environment)
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def test_log_context(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    log.info(f"▶ TEST START: {request.node.nodeid}")
    yield
    log.info(f"◀ TEST END:   {request.node.nodeid}")


# ── Hooks ─────────────────────────────────────────────────────────────────────

def pytest_runtest_logreport(
    report: pytest.TestReport,
) -> None:
    if report.when == "call":
        status = "PASS" if report.passed else ("FAIL" if report.failed else "SKIP")
        log.info(f"[{status}] {report.nodeid}")


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    log.info(
        f"SESSION FINISHED — exit={exitstatus} "
        f"items={session.testscollected}"
    )
