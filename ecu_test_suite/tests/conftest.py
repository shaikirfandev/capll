"""
pytest conftest.py — session, transport, UDS, DTC, and reporting fixtures.

Fixture hierarchy
-----------------
Session-scoped (created once per pytest session):
    ecu_config          — parsed YAML config for the active domain
    vector_interface    — open Vector (or mock) CAN channel
    isotp_connection    — open ISO-TP transport over the vector interface
    uds_client          — connected UDS client (mock or real)
    dtc_manager         — DTCManager bound to uds_client
    report_collector    — accumulates TestCaseRecord objects
    generate_final_report (autouse) — writes HTML + JSON report after all tests

Function-scoped (created per test):
    dtc_snapshot (autouse)      — captures DTC state before/after each test
    record_test_result (autouse)— appends a TestCaseRecord to report_collector

Environment variables (consumed by these fixtures)
----------------------------------------------------
    ECU_DOMAIN      — "ADAS" | "Infotainment" | "Cluster" | "Telematics"
    VECTOR_CHANNEL  — 1-based channel number string
    CAN_BITRATE     — bitrate in bps string
    MOCK_HARDWARE   — "1" / "true" to activate mock mode (default: "1")
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
import yaml

# Make the project root importable without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Default to mock mode so the suite can run in CI without hardware
os.environ.setdefault("MOCK_HARDWARE", "1")

from core.vector_interface import VectorChannelConfig, build_vector_interface
from core.isotp_transport import IsoTpConfig, build_isotp_connection
from core.uds_client import UDSClientBase, build_uds_client
from core.dtc_manager import DTCManager, DTCSnapshot
from core.security_access import get_algorithm
from core.report_generator import (
    ReportCollector,
    ReportGenerator,
    RunSummary,
    TestCaseRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_mock() -> bool:
    """Return True when mock hardware mode is active."""
    return os.environ.get("MOCK_HARDWARE", "1").lower() in ("1", "true", "yes")


def _hex_to_int(value: object, default: int = 0) -> int:
    """Convert a YAML hex string (e.g. '0x7DF') or int to int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16)
    return default


# ---------------------------------------------------------------------------
# ECU configuration
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def ecu_config() -> dict:
    """
    Load and return the YAML config for the active ECU domain.

    The domain is read from the ``ECU_DOMAIN`` environment variable
    (default: ``"ADAS"``).  Configs live in ``ecu_test_suite/config/``.
    """
    domain = os.environ.get("ECU_DOMAIN", "ADAS")
    config_map = {
        "ADAS":          "adas_ecu.yaml",
        "Infotainment":  "infotainment_ecu.yaml",
        "Cluster":       "cluster_ecu.yaml",
        "Telematics":    "telematics_ecu.yaml",
    }
    config_file = PROJECT_ROOT / "config" / config_map.get(domain, "adas_ecu.yaml")
    if not config_file.exists():
        pytest.fail(f"Config file not found: {config_file}")
    with open(config_file) as fh:
        cfg = yaml.safe_load(fh) or {}
    return cfg


# ---------------------------------------------------------------------------
# Hardware / transport / UDS stack  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def vector_interface(ecu_config: dict):
    """
    Open (and at teardown close) a Vector CAN interface.

    When ``MOCK_HARDWARE=1`` (default) a :class:`~core.vector_interface.MockVectorInterface`
    is returned — no real Vector hardware is required.
    """
    can_cfg = ecu_config.get("can", {})
    vec_config = VectorChannelConfig(
        channel  = int(os.environ.get("VECTOR_CHANNEL", can_cfg.get("channel", 1))),
        bitrate  = int(os.environ.get("CAN_BITRATE", can_cfg.get("bitrate", 500_000))),
        can_fd   = can_cfg.get("can_fd", False),
        fd_bitrate = can_cfg.get("fd_bitrate", 2_000_000),
    )
    iface = build_vector_interface(vec_config, mock=_is_mock())
    iface.connect()
    yield iface
    iface.disconnect()


@pytest.fixture(scope="session")
def isotp_connection(ecu_config: dict, vector_interface):
    """
    Open (and at teardown close) an ISO-TP transport connection.

    In mock mode the connection is purely in-process.  In real mode the
    underlying ``can.BusABC`` from ``vector_interface._bus`` is used.
    """
    can_cfg = ecu_config.get("can", {})
    isotp_cfg = IsoTpConfig(
        tx_id   = _hex_to_int(can_cfg.get("tx_id",  "0x7DF")),
        rx_id   = _hex_to_int(can_cfg.get("rx_id",  "0x7E8")),
        func_id = _hex_to_int(can_cfg.get("func_id","0x7DF")),
    )
    bus  = getattr(vector_interface, "_bus", None)
    conn = build_isotp_connection(isotp_cfg, bus=bus, mock=_is_mock())
    conn.open()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def uds_client(isotp_connection) -> Generator[UDSClientBase, None, None]:
    """
    Create and connect a UDS client (mock or real) for the session.

    Yields the client and disconnects it on teardown.
    """
    client = build_uds_client(connection=isotp_connection, mock=_is_mock())
    client.connect()
    yield client
    client.disconnect()


# ---------------------------------------------------------------------------
# DTC manager  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def dtc_manager(uds_client: UDSClientBase, ecu_config: dict) -> DTCManager:
    """
    Build a :class:`~core.dtc_manager.DTCManager` pre-populated with the
    DTC description map from the YAML config.
    """
    raw_map: dict = ecu_config.get("dtc_map", {}) or {}
    # Normalise keys — YAML may store them as strings like "0xC11001"
    dtc_map: dict[int, str] = {}
    for k, v in raw_map.items():
        try:
            int_key = int(str(k), 16) if isinstance(k, str) else int(k)
            dtc_map[int_key] = v
        except (ValueError, TypeError):
            pass
    return DTCManager(uds_client, dtc_map=dtc_map)


# ---------------------------------------------------------------------------
# Per-test DTC snapshot  (autouse, function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def dtc_snapshot(dtc_manager: DTCManager, request: pytest.FixtureRequest):
    """
    Capture DTC state **before** and **after** every test function.

    Snapshots are stored on the test node so that ``record_test_result``
    can include them in the report.  A warning is emitted if the test
    introduced new DTCs.
    """
    before: DTCSnapshot = dtc_manager.read_all()
    request.node._dtc_before = before  # type: ignore[attr-defined]
    yield
    after: DTCSnapshot = dtc_manager.read_all()
    request.node._dtc_after = after  # type: ignore[attr-defined]
    new_dtcs = dtc_manager.diff(before, after)
    request.node._new_dtcs = new_dtcs  # type: ignore[attr-defined]
    if new_dtcs:
        pytest.warns(
            UserWarning,
            match="NEW DTCs",
        ) if False else None  # already logged by DTCManager


# ---------------------------------------------------------------------------
# pytest hook — capture outcome & timing per test
# ---------------------------------------------------------------------------
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
) -> Generator:
    """Attach outcome, duration, and error text to the test item node."""
    outcome = yield
    report  = outcome.get_result()
    if call.when == "call":
        item._test_outcome  = report.outcome  # type: ignore[attr-defined]
        item._test_duration = (call.stop - call.start) if (call.stop and call.start) else 0.0  # type: ignore[attr-defined]
        item._test_error    = str(report.longrepr) if report.failed else ""  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Report collector  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def report_collector() -> ReportCollector:
    """Single-instance collector for all test case records in the session."""
    return ReportCollector()


# ---------------------------------------------------------------------------
# Per-test result recording  (autouse, function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def record_test_result(
    request: pytest.FixtureRequest,
    report_collector: ReportCollector,
) -> Generator[None, None, None]:
    """
    Append a :class:`~core.report_generator.TestCaseRecord` to the collector
    after each test finishes.
    """
    yield  # test runs here

    outcome  = getattr(request.node, "_test_outcome",  "unknown")
    duration = getattr(request.node, "_test_duration", 0.0)
    error    = getattr(request.node, "_test_error",    "")

    dtc_before = getattr(request.node, "_dtc_before", None)
    dtc_after  = getattr(request.node, "_dtc_after",  None)
    new_dtcs   = getattr(request.node, "_new_dtcs",   [])

    record = TestCaseRecord(
        name         = request.node.name,
        domain       = os.environ.get("ECU_DOMAIN", "unknown"),
        outcome      = outcome,
        duration_s   = duration,
        dtcs_before  = [d.code_str for d in (dtc_before.records if dtc_before else [])],
        dtcs_after   = [d.code_str for d in (dtc_after.records  if dtc_after  else [])],
        new_dtcs     = [d.code_str for d in new_dtcs],
        error_message= error,
    )
    report_collector.add(record)


# ---------------------------------------------------------------------------
# Session-level report generation  (autouse, session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def generate_final_report(
    report_collector: ReportCollector,
    ecu_config: dict,  # noqa: ARG001 — unused but forces config load before report
) -> Generator[None, None, None]:
    """
    After all tests complete, build and write the consolidated HTML + JSON report.

    Report files land in ``ecu_test_suite/reports/`` with a timestamp suffix.
    """
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    yield  # all tests run here

    domain  = os.environ.get("ECU_DOMAIN", "ADAS")
    records = report_collector.get_all()

    summary = RunSummary(
        domain     = domain,
        run_id     = session_start,
        start_time = session_start,
        end_time   = datetime.now().strftime("%Y%m%d_%H%M%S"),
        total      = len(records),
        passed     = sum(1 for r in records if r.outcome == "passed"),
        failed     = sum(1 for r in records if r.outcome == "failed"),
        errors     = sum(1 for r in records if r.outcome == "error"),
        skipped    = sum(1 for r in records if r.outcome == "skipped"),
        test_cases = records,
    )

    reports_dir = PROJECT_ROOT / "reports"
    generator   = ReportGenerator(reports_dir)
    try:
        generator.generate(summary)
        generator.generate_json(summary)
    except Exception as exc:  # noqa: BLE001
        # Report generation must never fail the test session
        print(f"\n[WARNING] Report generation failed: {exc}", file=sys.stderr)
