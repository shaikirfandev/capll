"""
pytest conftest — Infotainment ECU Test Suite.

Fixture overview
----------------
Session-scoped
    ecu_config          combined dict (sessions + io_control sections)
    dids_config         infotainment_dids.yaml
    dtcs_config         infotainment_dtcs.yaml
    routines_config     infotainment_routines.yaml
    sessions_config     sessions section of ecu_sessions.yaml
    vector_session      open Vector (or mock) CAN interface
    isotp_conn          open ISO-TP transport
    uds_client          connected UDS client  ← session-scoped for efficiency
    dtc_manager         DTCManager bound to uds_client
    did                 callable: name→int DID resolver
    routine             callable: name→int routine ID resolver
    report_collector    accumulates TestCaseRecord objects
    generate_report (autouse) write HTML+JSON at session end

Function-scoped
    ecu_default_session (autouse)   reset ECU to default session before/after test
    dtc_snapshot (autouse)          capture DTC state before/after test
    frame_logger                    per-test UDS transaction list
    record_test_result (autouse)    append TestCaseRecord after each test

Environment variables
    MOCK_HARDWARE   "1" (default) = mock, "0" = real hardware
    VECTOR_CHANNEL  1-based channel (default: from YAML)
    CAN_BITRATE     bps (default: from YAML)
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("MOCK_HARDWARE", "1")

from core.vector_interface import VectorChannelConfig, build_vector_interface
from core.isotp_transport  import IsoTpConfig, build_isotp_connection
from core.uds_client       import (
    UDSClientBase, SessionType, build_uds_client,
)
from core.dtc_manager      import DTCManager, DTCSnapshot
from core.security_access  import get_algorithm
from core.report_generator import (
    DTCSummaryEntry, ReportCollector, ReportGenerator,
    RunSummary, TestCaseRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_mock() -> bool:
    return os.environ.get("MOCK_HARDWARE", "1").lower() in ("1", "true", "yes")


def _to_int(val: object, default: int = 0) -> int:
    if isinstance(val, int):
        return val
    try:
        return int(str(val), 16) if str(val).startswith("0x") else int(str(val))
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def ecu_config() -> dict:
    """Load ecu_sessions.yaml."""
    p = PROJECT_ROOT / "config" / "ecu_sessions.yaml"
    with open(p) as f:
        return yaml.safe_load(f) or {}


@pytest.fixture(scope="session")
def dids_config() -> dict:
    """Load infotainment_dids.yaml — keyed by DID name."""
    p = PROJECT_ROOT / "config" / "infotainment_dids.yaml"
    with open(p) as f:
        return yaml.safe_load(f) or {}


@pytest.fixture(scope="session")
def dtcs_config() -> dict:
    """Load infotainment_dtcs.yaml — keyed by DTC name."""
    p = PROJECT_ROOT / "config" / "infotainment_dtcs.yaml"
    with open(p) as f:
        return yaml.safe_load(f) or {}


@pytest.fixture(scope="session")
def routines_config() -> dict:
    """Load infotainment_routines.yaml — keyed by routine name."""
    p = PROJECT_ROOT / "config" / "infotainment_routines.yaml"
    with open(p) as f:
        return yaml.safe_load(f) or {}


@pytest.fixture(scope="session")
def sessions_config(ecu_config: dict) -> dict:
    """Extract 'sessions' section from ecu_sessions.yaml."""
    return ecu_config.get("sessions", {})


# ---------------------------------------------------------------------------
# DID / Routine resolver fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def did(dids_config: dict) -> Callable[[str], int]:
    """
    Return a callable that resolves a DID name → integer.

    Usage in tests::

        def test_foo(uds_client, did):
            resp = uds_client.read_data_by_identifier(did("bluetooth_module_status"))
    """
    def _resolve(name: str) -> int:
        entry = dids_config.get(name)
        if entry is None:
            raise KeyError(f"DID '{name}' not found in infotainment_dids.yaml")
        return _to_int(entry.get("id", "0x0000"))
    return _resolve


@pytest.fixture(scope="session")
def routine(routines_config: dict) -> Callable[[str], int]:
    """Return a callable that resolves a routine name → integer."""
    def _resolve(name: str) -> int:
        entry = routines_config.get(name)
        if entry is None:
            raise KeyError(f"Routine '{name}' not found in infotainment_routines.yaml")
        return _to_int(entry.get("id", "0x0000"))
    return _resolve


@pytest.fixture(scope="session")
def dtc_code(dtcs_config: dict) -> Callable[[str], int]:
    """Return a callable that resolves a DTC catalogue name → integer DTC code."""
    def _resolve(name: str) -> int:
        entry = dtcs_config.get(name)
        if entry is None:
            raise KeyError(f"DTC '{name}' not found in infotainment_dtcs.yaml")
        return _to_int(entry.get("code", "0x000000"))
    return _resolve


# ---------------------------------------------------------------------------
# Hardware / transport stack  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def vector_session(ecu_config: dict):
    """Open (and at teardown close) a Vector CAN interface."""
    can_cfg = ecu_config.get("can", {})
    cfg = VectorChannelConfig(
        channel    = int(os.environ.get("VECTOR_CHANNEL", can_cfg.get("channel", 1))),
        bitrate    = int(os.environ.get("CAN_BITRATE",    can_cfg.get("bitrate", 500_000))),
        can_fd     = can_cfg.get("can_fd", False),
        fd_bitrate = can_cfg.get("fd_bitrate", 2_000_000),
        app_name   = can_cfg.get("app_name", "InfotainmentTestSuite"),
    )
    iface = build_vector_interface(cfg, mock=_is_mock())
    iface.connect()
    yield iface
    iface.disconnect()


@pytest.fixture(scope="session")
def isotp_conn(ecu_config: dict, vector_session):
    """Open ISO-TP connection over the vector session."""
    can_cfg = ecu_config.get("can", {})
    iso_cfg = ecu_config.get("isotp", {})
    cfg = IsoTpConfig(
        tx_id      = _to_int(can_cfg.get("tx_id",  "0x730")),
        rx_id      = _to_int(can_cfg.get("rx_id",  "0x738")),
        func_id    = _to_int(can_cfg.get("func_id","0x7DF")),
        tx_padding = iso_cfg.get("tx_padding", 0xAA),
        stmin      = iso_cfg.get("stmin",      0),
        blocksize  = iso_cfg.get("blocksize",  0),
    )
    bus  = getattr(vector_session, "_bus", None)
    conn = build_isotp_connection(cfg, bus=bus, mock=_is_mock())
    conn.open()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def uds_client(isotp_conn) -> Generator[UDSClientBase, None, None]:
    """Connected UDS client — session-scoped for efficiency."""
    client = build_uds_client(connection=isotp_conn, mock=_is_mock())
    client.connect()
    yield client
    client.disconnect()


# ---------------------------------------------------------------------------
# DTC manager  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def dtc_manager(uds_client: UDSClientBase, dtcs_config: dict) -> DTCManager:
    """DTCManager pre-loaded with the DTC catalogue."""
    catalogue: dict[str, dict] = {
        entry.get("code", ""): entry
        for entry in dtcs_config.values()
        if isinstance(entry, dict)
    }
    return DTCManager(uds_client, dtc_catalogue=catalogue)


# ---------------------------------------------------------------------------
# Per-test: reset session  (autouse)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def ecu_default_session(uds_client: UDSClientBase) -> Generator[None, None, None]:
    """
    Return ECU to default session **before** and **after** each test.

    This fixture is autouse so every test starts from a known baseline
    and cannot accidentally leave the ECU in an elevated session that
    breaks the next test.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    yield
    uds_client.diagnostic_session_control(SessionType.DEFAULT)


# ---------------------------------------------------------------------------
# Per-test: DTC snapshot  (autouse)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def dtc_snapshot(
    dtc_manager: DTCManager,
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """
    Capture DTC state before and after each test, attach diff to node.
    """
    before: DTCSnapshot = dtc_manager.read_all()
    request.node._dtc_before = before  # type: ignore[attr-defined]
    yield
    after: DTCSnapshot = dtc_manager.read_all()
    request.node._dtc_after = after    # type: ignore[attr-defined]
    request.node._new_dtcs  = dtc_manager.diff(before, after)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Per-test: frame logger  (NOT autouse — explicitly requested by tests)
# ---------------------------------------------------------------------------
@pytest.fixture
def frame_logger(uds_client: UDSClientBase) -> Generator[list, None, None]:
    """
    Provide the per-test UDS transaction list.

    The list is cleared at fixture setup so it only contains transactions
    from the current test.  Tests that need to inspect raw request/response
    pairs should declare ``frame_logger`` in their signature.

    Example::

        def test_something(uds_client, frame_logger):
            uds_client.read_data_by_identifier(0x3001)
            assert len(frame_logger) == 1
            assert frame_logger[0]["service"] == "RDBI"
    """
    uds_client.transaction_log.clear()
    yield uds_client.transaction_log


# ---------------------------------------------------------------------------
# pytest hook — capture outcome + timing
# ---------------------------------------------------------------------------
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator:
    outcome = yield
    report  = outcome.get_result()
    if call.when == "call":
        item._test_outcome  = report.outcome  # type: ignore[attr-defined]
        item._test_duration = (call.stop - call.start) if call.stop else 0.0  # type: ignore[attr-defined]
        item._test_error    = str(report.longrepr) if report.failed else ""  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Report collector  (session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def report_collector() -> ReportCollector:
    return ReportCollector()


# ---------------------------------------------------------------------------
# Per-test: record result  (autouse)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def record_test_result(
    request:          pytest.FixtureRequest,
    report_collector: ReportCollector,
    uds_client:       UDSClientBase,
    dtcs_config:      dict,
) -> Generator[None, None, None]:
    """Populate a TestCaseRecord after each test and add DTC events to collector."""
    yield

    outcome  = getattr(request.node, "_test_outcome",  "unknown")
    duration = getattr(request.node, "_test_duration", 0.0)
    error    = getattr(request.node, "_test_error",    "")

    dtc_before = getattr(request.node, "_dtc_before", None)
    dtc_after  = getattr(request.node, "_dtc_after",  None)
    new_dtcs   = getattr(request.node, "_new_dtcs",   [])

    # Feature label from the test's nodeid path
    parts  = request.node.nodeid.split("/")
    module = parts[-2] if len(parts) >= 2 else ""
    feature = module.replace("test_", "").replace("_", " ").title() if module else ""

    record = TestCaseRecord(
        name          = request.node.name,
        module        = module,
        feature       = feature,
        outcome       = outcome,
        duration_s    = duration,
        dtcs_before   = [d.code_str for d in (dtc_before.records if dtc_before else [])],
        dtcs_after    = [d.code_str for d in (dtc_after.records  if dtc_after  else [])],
        new_dtcs      = [d.code_str for d in new_dtcs],
        transactions  = [t.to_dict() for t in uds_client.transaction_log],
        error_message = error,
    )
    report_collector.add(record)

    # Register new DTC events in the DTC summary
    catalogue = dtcs_config
    for dtc_rec in new_dtcs:
        # Try to find this code in the catalogue
        cat_entry = next(
            (v for v in catalogue.values()
             if isinstance(v, dict) and v.get("code", "").upper() == f"0x{dtc_rec.dtc_code:06X}".upper()),
            {},
        )
        report_collector.add_dtc_event(DTCSummaryEntry(
            code_str    = dtc_rec.code_str,
            dtc_code    = dtc_rec.dtc_code,
            description = dtc_rec.description or cat_entry.get("description", ""),
            severity    = dtc_rec.severity    or cat_entry.get("severity",    "unknown"),
            status      = "set_during_run",
            test_name   = request.node.name,
        ))


# ---------------------------------------------------------------------------
# Session teardown — generate report  (autouse, session-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def generate_report(
    report_collector: ReportCollector,
    ecu_config:       dict,  # noqa: ARG001
) -> Generator[None, None, None]:
    """Write HTML + JSON report after all tests complete."""
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    yield

    summary = report_collector.build_summary(
        run_id    = session_start,
        mock_mode = _is_mock(),
    )
    out_dir = PROJECT_ROOT / "reports"
    gen     = ReportGenerator(out_dir)
    try:
        gen.generate(summary)
        gen.generate_json(summary)
    except Exception as exc:  # noqa: BLE001
        print(f"\n[WARNING] Report generation failed: {exc}", file=sys.stderr)
