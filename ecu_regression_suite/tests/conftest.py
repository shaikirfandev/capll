"""
Global pytest fixtures and configuration for the ECU Regression Suite.

CLI options
-----------
--ecu=adas|infotainment   Target ECU (default: adas)
--version=<str>           Software version under test (default: v0.0.0)
--mock / --no-mock        Hardware mode (default: mock)
--baseline-version=<str>  Specific baseline version to compare against
--channel=<str>           Vector CAN channel for hardware mode (default: VECTOR::0)
--bitrate=<int>           CAN bitrate in bps (default: 500000)

Data-driven parametrisation
----------------------------
Test functions that declare ``did_entry``, ``rid_entry``, or ``nrc_scenario``
as fixture arguments are automatically parametrised from the YAML matrices via
``pytest_generate_tests``.  Adding a new DID/RID/NRC requires only a config
change — no test code modifications.

Result collection
-----------------
Every test's :class:`~core.baseline_manager.TestRecord` is stored in the
session-scoped ``result_collector`` fixture.  At session end,
``pytest_sessionfinish`` runs the baseline diff and writes the HTML + JSON
regression report.
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
import yaml
from loguru import logger

# ── Make project root importable ───────────────────────────────────────────
_SUITE_ROOT = Path(__file__).parent.parent
if str(_SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SUITE_ROOT))

from core.baseline_manager import BaselineManager, RunResult, TestRecord
from core.isotp_transport import IsoTpConfig, build_isotp_connection
from core.report_generator import ReportGenerator
from core.security_access import perform_security_access, get_algorithm
from core.uds_client import UDSClientConfig, build_uds_client, SessionType, UDSClient
from core.vector_interface import VectorChannelConfig, build_vector_interface


# ── Path constants ──────────────────────────────────────────────────────────
_CONFIG_ROOT   = _SUITE_ROOT / "config"
_BASELINES_DIR = _SUITE_ROOT / "baselines"
_REPORTS_DIR   = _SUITE_ROOT / "reports"
_LOGS_DIR      = _SUITE_ROOT / "logs"


# ===========================================================================
# CLI option registration
# ===========================================================================

def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ECU regression suite CLI options."""
    group = parser.getgroup("ecu-regression", "ECU Regression Suite options")
    group.addoption(
        "--ecu",
        choices=["adas", "infotainment"],
        default="adas",
        help="Target ECU to test (default: adas)",
    )
    group.addoption(
        "--version",
        default="v0.0.0",
        help="ECU software version under test (e.g. v1.3.0)",
    )
    group.addoption(
        "--mock",
        action="store_true",
        default=True,
        help="Run in simulated mock mode — no hardware required (default: True)",
    )
    group.addoption(
        "--no-mock",
        action="store_false",
        dest="mock",
        help="Connect to real Vector hardware",
    )
    group.addoption(
        "--baseline-version",
        default=None,
        help="Specific baseline version to compare against (default: latest)",
    )
    group.addoption(
        "--channel",
        default="VECTOR::0",
        help="Vector CAN channel for hardware mode (default: VECTOR::0)",
    )
    group.addoption(
        "--bitrate",
        type=int,
        default=500_000,
        help="CAN bitrate in bps (default: 500000)",
    )


# ===========================================================================
# Data-driven parametrisation
# ===========================================================================

def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file or return empty dict if file is missing."""
    if not path.exists():
        logger.warning("YAML config not found: {}", path)
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Auto-parametrise data-driven tests from YAML matrices.

    Test functions that request the following fixture names will be
    parametrised automatically — one invocation per matrix entry.

    ``did_entry``     → every DID in ``config/<ecu>/did_matrix.yaml``
    ``rid_entry``     → every routine in ``config/<ecu>/rid_matrix.yaml``
    ``nrc_scenario``  → every scenario in ``config/<ecu>/nrc_expected_matrix.yaml``
    ``writable_did``  → writable-only subset of the DID matrix
    ``readable_did``  → readable-only subset of the DID matrix
    ``secured_did``   → DIDs requiring security_level > 0
    ``io_did``        → io_controllable DIDs
    """
    ecu = metafunc.config.getoption("--ecu", default="adas")
    ecu_cfg_dir = _CONFIG_ROOT / ecu

    if "did_entry" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = matrix.get("dids", [])
        metafunc.parametrize(
            "did_entry",
            dids,
            ids=[d.get("id", str(i)) for i, d in enumerate(dids)],
        )

    if "writable_did" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = [d for d in matrix.get("dids", []) if d.get("writable")]
        metafunc.parametrize(
            "writable_did",
            dids,
            ids=[d.get("id") for d in dids],
        )

    if "readable_did" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = [d for d in matrix.get("dids", []) if d.get("readable")]
        metafunc.parametrize(
            "readable_did",
            dids,
            ids=[d.get("id") for d in dids],
        )

    if "readonly_did" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = [d for d in matrix.get("dids", []) if d.get("readable") and not d.get("writable")]
        metafunc.parametrize(
            "readonly_did",
            dids,
            ids=[d.get("id") for d in dids],
        )

    if "secured_did" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = [d for d in matrix.get("dids", []) if d.get("security_level", 0) > 0]
        metafunc.parametrize(
            "secured_did",
            dids,
            ids=[d.get("id") for d in dids],
        )

    if "io_did" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "did_matrix.yaml")
        dids = [d for d in matrix.get("dids", []) if d.get("io_controllable")]
        metafunc.parametrize(
            "io_did",
            dids,
            ids=[d.get("id") for d in dids],
        )

    if "rid_entry" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "rid_matrix.yaml")
        routines = matrix.get("routines", [])
        metafunc.parametrize(
            "rid_entry",
            routines,
            ids=[r.get("id", str(i)) for i, r in enumerate(routines)],
        )

    if "nrc_scenario" in metafunc.fixturenames:
        matrix = _load_yaml(ecu_cfg_dir / "nrc_expected_matrix.yaml")
        scenarios = matrix.get("nrc_scenarios", [])
        metafunc.parametrize(
            "nrc_scenario",
            scenarios,
            ids=[s.get("scenario", str(i)) for i, s in enumerate(scenarios)],
        )


# ===========================================================================
# Session-scoped infrastructure fixtures
# ===========================================================================

@pytest.fixture(scope="session")
def ecu(request: pytest.FixtureRequest) -> str:
    """ECU name from --ecu CLI option."""
    return request.config.getoption("--ecu")


@pytest.fixture(scope="session")
def sw_version(request: pytest.FixtureRequest) -> str:
    """Software version string from --version CLI option."""
    return request.config.getoption("--version")


@pytest.fixture(scope="session")
def mock_mode(request: pytest.FixtureRequest) -> bool:
    """True when running in simulated mock mode."""
    return request.config.getoption("--mock")


@pytest.fixture(scope="session")
def did_matrix(ecu: str) -> Dict[str, Any]:
    """Parsed DID matrix YAML for the selected ECU."""
    return _load_yaml(_CONFIG_ROOT / ecu / "did_matrix.yaml")


@pytest.fixture(scope="session")
def rid_matrix(ecu: str) -> Dict[str, Any]:
    """Parsed RID matrix YAML for the selected ECU."""
    return _load_yaml(_CONFIG_ROOT / ecu / "rid_matrix.yaml")


@pytest.fixture(scope="session")
def nrc_matrix(ecu: str) -> Dict[str, Any]:
    """Parsed NRC expected-matrix YAML for the selected ECU."""
    return _load_yaml(_CONFIG_ROOT / ecu / "nrc_expected_matrix.yaml")


@pytest.fixture(scope="session")
def sessions_config(ecu: str) -> Dict[str, Any]:
    """Parsed sessions_security.yaml for the selected ECU."""
    return _load_yaml(_CONFIG_ROOT / ecu / "sessions_security.yaml")


@pytest.fixture(scope="session")
def vector_session(mock_mode: bool, request: pytest.FixtureRequest):
    """
    Open a Vector CAN interface once per test session.

    In mock mode, returns a :class:`~core.vector_interface.MockVectorInterface`.
    In hardware mode, connects to the real Vector device.
    """
    channel_str = request.config.getoption("--channel")
    # Parse channel number from e.g. "VECTOR::0" or "VECTOR::1"
    ch_num = 1
    m = re.search(r"(\d+)$", channel_str)
    if m:
        ch_num = int(m.group(1)) + 1  # Vector hardware config uses 1-based

    bitrate = request.config.getoption("--bitrate")
    cfg = VectorChannelConfig(
        channel=ch_num,
        bitrate=bitrate,
        mock=mock_mode,
    )
    iface = build_vector_interface(cfg)
    iface.connect()
    yield iface
    iface.disconnect()


@pytest.fixture(scope="session")
def uds_client(
    ecu: str,
    mock_mode: bool,
    did_matrix: Dict[str, Any],
    rid_matrix: Dict[str, Any],
    sessions_config: Dict[str, Any],
    vector_session,
) -> Generator[UDSClient, None, None]:
    """
    Session-scoped UDS client, built from ECU-specific YAML config.

    All tests share one connection per run to avoid repeated hardware connect/
    disconnect overhead and to preserve security state across the test session.
    """
    addr = sessions_config.get("addressing", {})
    isotp_cfg = IsoTpConfig(
        tx_id=addr.get("tx_id", 0x7E0),
        rx_id=addr.get("rx_id", 0x7E8),
    )
    conn = build_isotp_connection(isotp_cfg, vector_session, mock=mock_mode)

    uds_cfg = UDSClientConfig(
        ecu_name=ecu,
        mock=mock_mode,
        did_matrix=did_matrix,
        rid_matrix=rid_matrix,
        sessions_config=sessions_config,
    )
    client = build_uds_client(uds_cfg, connection=conn)
    client.connect()
    yield client
    client.disconnect()


@pytest.fixture(scope="session")
def baseline_loader(
    ecu: str,
    request: pytest.FixtureRequest,
) -> Optional[RunResult]:
    """
    Load the comparison baseline for this ECU.

    Returns the most recent available baseline, or the version explicitly
    specified via ``--baseline-version``.  Returns None on first-ever run.
    """
    baseline_version = request.config.getoption("--baseline-version")
    mgr = BaselineManager(_BASELINES_DIR)
    return mgr.load_baseline(ecu, version=baseline_version)


@pytest.fixture(scope="session")
def result_collector(
    ecu: str,
    sw_version: str,
    mock_mode: bool,
    request: pytest.FixtureRequest,
) -> Generator[RunResult, None, None]:
    """
    Session-scoped container for collecting all test records.

    Tests call ``result_collector.add(record)`` to register their results.
    On fixture teardown (after all tests), the suite:
    1. Loads the most recent baseline (or the version from --baseline-version).
    2. Diffs current results against the baseline.
    3. Saves current run as the new baseline candidate.
    4. Generates HTML + JSON release regression report.
    """
    ts = datetime.utcnow().isoformat()
    run_id = f"{ecu}_{sw_version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    run = RunResult(
        ecu=ecu,
        version=sw_version,
        timestamp=ts,
        run_id=run_id,
        mock_mode=mock_mode,
    )
    yield run

    # ── Post-session teardown: diff → report → save ────────────────────────
    if not run.records:
        logger.info("No test records collected — skipping report generation.")
        return

    baseline_version = request.config.getoption("--baseline-version")
    mgr = BaselineManager(_BASELINES_DIR)
    baseline = mgr.load_baseline(ecu, version=baseline_version)

    gen  = ReportGenerator(_REPORTS_DIR)
    diff = mgr.diff(baseline, run) if baseline else None
    html_path, json_path = gen.generate(run, diff)
    saved = mgr.save_run(run)

    print(f"\n{'='*70}")
    print(f"  ECU Regression Suite — Run Complete")
    print(f"  ECU: {run.ecu.upper()}   Version: {run.version}")
    print(f"  Results: {run.pass_count()} pass / {run.fail_count()} fail / {run.error_count()} error")
    if diff:
        print(f"  Baseline: {diff.baseline_version} \u2192 {diff.current_version}")
        print(f"  Regressions: {len(diff.regressions)}  |  Improvements: {len(diff.improvements)}")
        print(f"  Sign-off: {diff.sign_off_recommendation}")
    else:
        print(f"  First baseline run — no prior baseline to compare against.")
    print(f"  HTML Report: {html_path}")
    print(f"  JSON Report: {json_path}")
    print(f"  Baseline saved: {saved}")
    print(f"{'='*70}\n")


# ===========================================================================
# Function-scoped session management fixtures
# ===========================================================================

@pytest.fixture
def in_default_session(uds_client: UDSClient) -> Generator[UDSClient, None, None]:
    """Ensure the ECU is in the default session before the test."""
    resp = uds_client.change_session(SessionType.DEFAULT)
    assert resp.positive, f"Could not enter default session: NRC {resp.nrc_name}"
    uds_client._security_level = 0
    yield uds_client
    # Return to default after test (best-effort)
    uds_client.change_session(SessionType.DEFAULT)


@pytest.fixture
def in_extended_session(uds_client: UDSClient) -> Generator[UDSClient, None, None]:
    """Ensure the ECU is in the extended session before the test."""
    resp = uds_client.change_session(SessionType.EXTENDED)
    assert resp.positive, f"Could not enter extended session: NRC {resp.nrc_name}"
    yield uds_client
    uds_client.change_session(SessionType.DEFAULT)


@pytest.fixture
def in_extended_with_security(
    uds_client: UDSClient,
    sessions_config: Dict[str, Any],
) -> Generator[UDSClient, None, None]:
    """
    Ensure the ECU is in extended session with security level 1 unlocked.

    Uses the :func:`~core.security_access.perform_security_access` helper
    with the XOR placeholder algorithm (replace for real hardware).
    """
    resp = uds_client.change_session(SessionType.EXTENDED)
    assert resp.positive, f"Could not enter extended session: NRC {resp.nrc_name}"

    algo_name = (
        sessions_config
        .get("security", {})
        .get("levels", {})
        .get("1", {})
        .get("algorithm", "xor_placeholder")
    )
    algorithm = get_algorithm(algo_name)
    perform_security_access(uds_client, level=1, algorithm=algorithm)
    yield uds_client
    uds_client.change_session(SessionType.DEFAULT)


@pytest.fixture
def in_programming_session(uds_client: UDSClient) -> Generator[UDSClient, None, None]:
    """Ensure the ECU is in programming session before the test."""
    resp = uds_client.change_session(SessionType.PROGRAMMING)
    assert resp.positive, f"Could not enter programming session: NRC {resp.nrc_name}"
    yield uds_client
    uds_client.change_session(SessionType.DEFAULT)


# Report generation and baseline save are handled in result_collector fixture teardown.
