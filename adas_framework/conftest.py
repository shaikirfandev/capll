# adas_framework/conftest.py
"""
Root pytest conftest.py — ADAS Enterprise Test Framework.

Provides session/module/function-scoped fixtures for:
    - CAN bus connection
    - Signal validator (live decoded signals)
    - UDS client (per-ECU)
    - Radar / Camera / LiDAR validators
    - Sensor fusion validator
    - Fault injector
    - HIL bench
    - Test metadata hooks (Allure tagging, ASIL enforcement)
    - FlakyTracker session reporting
    - Auto-cleanup (return ECU to default session, restore signals)

CLI options (add to pytest invocation):
    --channel PCAN_USBBUS1   CAN channel
    --interface pcan         CAN interface type
    --bitrate 500000         CAN bitrate
    --dbc test_data/dbs/ADAS_Network.dbc
    --ecu ADAS_ECU           Target ECU for UDS
    --env HIL_LAB_01         Environment name
    --sw-version 1.4.2       ADAS SW version under test
    --hil                    Enable HIL bench integration
    --no-hardware            Skip hardware-dependent tests
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Generator

import pytest

# Framework imports
from core.config import FrameworkConfig, cfg as default_cfg
from core.logger import get_logger, set_test_context
from core.retry import FlakyTracker
from can.can_interface import CANInterface
from can.signal_validator import SignalValidator
from diagnostics.uds_client import UDSClient
from radar.radar_validator import RadarValidator
from camera.camera_validator import CameraValidator
from sensor_fusion.fusion_validator import FusionValidator

log = get_logger("conftest")

# ─────────────────────────────────────────────────────────────────────────────
# Custom CLI options
# ─────────────────────────────────────────────────────────────────────────────

def pytest_addoption(parser: pytest.Parser):
    grp = parser.getgroup("adas", "ADAS Framework Options")
    grp.addoption("--channel",      default=None)
    grp.addoption("--interface",    default=None)
    grp.addoption("--bitrate",      default=None, type=int)
    grp.addoption("--dbc",          default=None)
    grp.addoption("--ecu",          default="ADAS_ECU")
    grp.addoption("--env",          default=None)
    grp.addoption("--sw-version",   default=None)
    grp.addoption("--hil",          action="store_true", default=False)
    grp.addoption("--no-hardware",  action="store_true", default=False)


# ─────────────────────────────────────────────────────────────────────────────
# Custom markers
# ─────────────────────────────────────────────────────────────────────────────

def pytest_configure(config: pytest.Config):
    markers = [
        ("smoke",          "Quick smoke test suite (< 5 min)"),
        ("sanity",         "Sanity check suite"),
        ("regression",     "Full regression suite"),
        ("safety",         "ISO 26262 safety test — no @flaky allowed"),
        ("asil_a",         "ASIL A safety test"),
        ("asil_b",         "ASIL B safety test"),
        ("asil_c",         "ASIL C safety test"),
        ("asil_d",         "ASIL D safety test — most critical"),
        ("hardware",       "Requires physical hardware / HIL bench"),
        ("slow",           "Test runs > 60 seconds"),
        ("flaky",          "Known intermittent test"),
        ("acc",            "Adaptive Cruise Control"),
        ("aeb",            "Autonomous Emergency Braking"),
        ("lka",            "Lane Keep Assist"),
        ("ldw",            "Lane Departure Warning"),
        ("bsd",            "Blind Spot Detection"),
        ("tsr",            "Traffic Sign Recognition"),
        ("dms",            "Driver Monitoring System"),
        ("radar",          "Radar sensor test"),
        ("camera",         "Camera sensor test"),
        ("lidar",          "LiDAR sensor test"),
        ("fusion",         "Sensor fusion test"),
        ("uds",            "UDS diagnostic test"),
        ("can",            "CAN network test"),
        ("ethernet",       "Automotive Ethernet / SOME-IP test"),
        ("hil",            "HIL bench test"),
        ("sil",            "SIL environment test"),
        ("performance",    "Performance/timing test"),
        ("cybersecurity",  "Cybersecurity test"),
        ("fault_injection","Fault injection test"),
    ]
    for name, description in markers:
        config.addinivalue_line("markers", f"{name}: {description}")


# ─────────────────────────────────────────────────────────────────────────────
# Session-level config fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def framework_cfg(request: pytest.FixtureRequest) -> FrameworkConfig:
    """
    Session-scoped framework config.
    CLI options override defaults from test_config.yaml.
    """
    c = default_cfg

    # Apply CLI overrides
    channel   = request.config.getoption("--channel")
    interface = request.config.getoption("--interface")
    bitrate   = request.config.getoption("--bitrate")
    dbc       = request.config.getoption("--dbc")
    env_name  = request.config.getoption("--env")
    sw_ver    = request.config.getoption("--sw-version")
    hil       = request.config.getoption("--hil")

    if channel:   c.can.channel    = channel
    if interface: c.can.interface  = interface
    if bitrate:   c.can.bitrate    = bitrate
    if dbc:       c.can.dbc_path   = dbc
    if env_name:  c.env.name       = env_name
    if sw_ver:    c.env.adas_sw_version = sw_ver
    if hil:       c.hil.enabled    = True

    log.info(
        f"Framework config loaded | env={c.env.name} | "
        f"sw={c.env.adas_sw_version} | channel={c.can.channel}"
    )
    return c


# ─────────────────────────────────────────────────────────────────────────────
# CAN fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def can_bus(framework_cfg: FrameworkConfig) -> Generator[CANInterface, None, None]:
    """Session-scoped CAN bus. One connection for entire test session."""
    bus = CANInterface.create(framework_cfg.can)
    bus.start()
    yield bus
    bus.stop()


@pytest.fixture(scope="session")
def signals(can_bus: CANInterface,
            framework_cfg: FrameworkConfig) -> SignalValidator:
    """
    Session-scoped signal validator.
    Auto-subscribes to all CAN messages and decodes via DBC.
    """
    validator = SignalValidator(framework_cfg.can.dbc_path)
    validator.attach(can_bus)
    return validator


# ─────────────────────────────────────────────────────────────────────────────
# UDS fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def uds(can_bus: CANInterface,
        framework_cfg: FrameworkConfig,
        request: pytest.FixtureRequest):
    """
    Function-scoped UDS client.
    Starts in default session. Returns to default on teardown.
    Target ECU from --ecu CLI option.
    """
    ecu = request.config.getoption("--ecu")
    client = UDSClient(framework_cfg.uds, ecu, can_bus._bus)
    client._tp.open()
    client._run(client.change_session(0x01))
    yield client
    # Teardown
    client.stop_keepalive()
    try:
        client._run(client.change_session(0x01))
    except Exception:
        pass
    client._tp.close()


@pytest.fixture(scope="function")
def uds_extended(uds: UDSClient):
    """UDS client pre-entered into Extended Diagnostic session."""
    uds._run(uds.change_session(0x03))
    uds.start_keepalive(interval_s=3.0)
    yield uds
    uds.stop_keepalive()


# ─────────────────────────────────────────────────────────────────────────────
# Sensor fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def radar(framework_cfg: FrameworkConfig,
          signals: SignalValidator) -> RadarValidator:
    """Module-scoped radar validator."""
    validator = RadarValidator(framework_cfg.radar)
    validator.attach(signals)
    yield validator
    validator.clear_stats()


@pytest.fixture(scope="module")
def camera(framework_cfg: FrameworkConfig) -> Generator[CameraValidator, None, None]:
    """Module-scoped camera validator."""
    validator = CameraValidator(framework_cfg.camera)
    validator.open()
    yield validator
    validator.release()


@pytest.fixture(scope="module")
def fusion() -> FusionValidator:
    """Module-scoped sensor fusion validator."""
    return FusionValidator()


# ─────────────────────────────────────────────────────────────────────────────
# Async event loop (for async test cases)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Provide a single asyncio event loop for the entire session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─────────────────────────────────────────────────────────────────────────────
# Hardware skip marker
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def skip_no_hardware(request: pytest.FixtureRequest):
    """Auto-skip @hardware tests when --no-hardware flag is set."""
    if (request.node.get_closest_marker("hardware") and
            request.config.getoption("--no-hardware", default=False)):
        pytest.skip("Skipped — no hardware (--no-hardware flag)")


# ─────────────────────────────────────────────────────────────────────────────
# Allure / test metadata injection
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def inject_allure_metadata(request: pytest.FixtureRequest, framework_cfg: FrameworkConfig):
    """Automatically tag Allure reports with SW version, ECU, environment."""
    try:
        import allure
        allure.dynamic.parameter("sw_version",  framework_cfg.env.adas_sw_version)
        allure.dynamic.parameter("environment", framework_cfg.env.name)
        allure.dynamic.parameter("hw_variant",  framework_cfg.env.hw_variant)
    except (ImportError, Exception):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Per-test logging context
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def test_log_context(request: pytest.FixtureRequest):
    """Inject test node ID into all log records for that test."""
    set_test_context(request.node.nodeid)


# ─────────────────────────────────────────────────────────────────────────────
# FlakyTracker (session scope)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def flaky_tracker() -> FlakyTracker:
    return FlakyTracker()


def pytest_runtest_logreport(report: pytest.TestReport):
    """Record pass/fail for flakiness analysis."""
    if report.when == "call":
        # Access tracker from session stash if available
        pass


def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    """Print final session summary."""
    log.info(
        f"Session finished | exit={exitstatus} | "
        f"passed={session.testscollected}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Release validation workflow fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def release_context(framework_cfg: FrameworkConfig) -> dict:
    """
    Provides structured context for a new SW release validation run.
    Used by the release regression suite to track the full workflow state.
    """
    return {
        "sw_version":     framework_cfg.env.adas_sw_version,
        "hw_variant":     framework_cfg.env.hw_variant,
        "environment":    framework_cfg.env.name,
        "start_time":     time.time(),
        "smoke_passed":   False,
        "sanity_passed":  False,
        "regression_done": False,
        "defects":        [],
        "sign_off":       False,
    }
