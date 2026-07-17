"""
Entry point for the ECU Test Suite CLI.

Workflow
--------
1. Discover available Vector channels (or use config defaults).
2. Prompt tester to confirm channel, baud rate, and ECU domain.
3. Export environment variables consumed by conftest.py.
4. Invoke pytest programmatically for the selected domain.

Usage::

    python -m cli.main
    # or
    python ecu_test_suite/cli/main.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import questionary
import yaml
from loguru import logger

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR  = PROJECT_ROOT / "reports"
LOGS_DIR     = PROJECT_ROOT / "logs"
CONFIG_DIR   = PROJECT_ROOT / "config"
TESTS_DIR    = PROJECT_ROOT / "tests"

# ---------------------------------------------------------------------------
# Domain registry
# ---------------------------------------------------------------------------
DOMAIN_MAP: dict[str, dict] = {
    "ADAS": {
        "config": CONFIG_DIR / "adas_ecu.yaml",
        "tests":  TESTS_DIR  / "adas",
        "marker": "adas",
        "description": "Camera, radar, ACC, AEB — sensor calibration & DTC checks",
    },
    "Infotainment": {
        "config": CONFIG_DIR / "infotainment_ecu.yaml",
        "tests":  TESTS_DIR  / "infotainment",
        "marker": "infotainment",
        "description": "HMI, audio, BT/Wi-Fi, display — wake/sleep, factory reset",
    },
    "Cluster": {
        "config": CONFIG_DIR / "cluster_ecu.yaml",
        "tests":  TESTS_DIR  / "cluster",
        "marker": "cluster",
        "description": "Odometer, VIN, speed, lamps — IO control & DTC checks",
    },
    "Telematics": {
        "config": CONFIG_DIR / "telematics_ecu.yaml",
        "tests":  TESTS_DIR  / "telematics",
        "marker": "telematics",
        "description": "SIM/eSIM, GPS, modem firmware — connectivity & eCall",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ensure_dirs() -> None:
    """Create output directories if they do not exist."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load_config(domain: str) -> dict:
    """Parse the ECU YAML config for *domain*."""
    config_path = DOMAIN_MAP[domain]["config"]
    if not config_path.exists():
        logger.error("Config not found: {}", config_path)
        sys.exit(1)
    with open(config_path) as fh:
        cfg = yaml.safe_load(fh)
    logger.info("Loaded config: {}", config_path)
    return cfg


def _select_domain() -> str:
    """Interactive domain selection."""
    choices = [
        questionary.Choice(
            title=f"{name:14s} — {meta['description']}",
            value=name,
        )
        for name, meta in DOMAIN_MAP.items()
    ]
    domain = questionary.select("Select ECU domain to validate:", choices=choices).ask()
    if domain is None:
        logger.warning("Selection cancelled.")
        sys.exit(0)
    return domain


def _confirm_hardware(cfg: dict) -> tuple[str, int]:
    """Confirm or override channel and baud rate from YAML config."""
    can_cfg = cfg.get("can", {})
    default_channel = str(can_cfg.get("channel", "1"))
    default_baud    = str(can_cfg.get("bitrate", 500_000))

    channel = questionary.text(
        f"Vector channel (default: {default_channel}):",
        default=default_channel,
    ).ask()

    baud = questionary.text(
        f"CAN bitrate in bps (default: {default_baud}):",
        default=default_baud,
    ).ask()

    return channel or default_channel, int(baud or default_baud)


def _select_run_mode() -> str:
    """Choose between smoke, regression, or full run."""
    mode = questionary.select(
        "Select test run mode:",
        choices=[
            questionary.Choice("smoke      — fast sanity checks only",  value="smoke"),
            questionary.Choice("regression — complete regression suite", value="regression"),
            questionary.Choice("all        — every collected test",      value="all"),
        ],
        default=None,
    ).ask()
    return mode or "smoke"


def _build_pytest_cmd(
    domain: str,
    marker_filter: str,
    report_html: Path,
    log_file: Path,
) -> list[str]:
    """Assemble the pytest command list."""
    domain_tests  = str(DOMAIN_MAP[domain]["tests"])
    common_tests  = str(TESTS_DIR / "common")

    cmd: list[str] = [
        sys.executable, "-m", "pytest",
        domain_tests,
        common_tests,
        f"--html={report_html}",
        "--self-contained-html",
        f"--log-file={log_file}",
        "--log-file-level=DEBUG",
        "-v",
    ]

    if marker_filter != "all":
        cmd += ["-m", marker_filter]

    return cmd


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point — orchestrates the entire test run."""
    _ensure_dirs()

    # Configure loguru to also write to a CLI-level log file
    logger.add(LOGS_DIR / "cli_{time}.log", rotation="10 MB", retention="7 days")
    logger.info("ECU Test Suite v1.0.0 — starting")

    domain           = _select_domain()
    cfg              = _load_config(domain)
    channel, bitrate = _confirm_hardware(cfg)
    run_mode         = _select_run_mode()

    # Export env vars — conftest.py reads these at session scope
    os.environ["ECU_DOMAIN"]     = domain
    os.environ["VECTOR_CHANNEL"] = channel
    os.environ["CAN_BITRATE"]    = str(bitrate)

    # Determine mock mode: default ON for safety; tester opts in to real HW
    mock_hw = os.environ.get("MOCK_HARDWARE", "1")
    if mock_hw not in ("0", "false", "no"):
        logger.warning(
            "[MOCK] Hardware mock mode is ACTIVE. "
            "Set MOCK_HARDWARE=0 to run against real Vector hardware."
        )

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_html = REPORTS_DIR / f"{domain.lower()}_{timestamp}.html"
    log_file    = LOGS_DIR    / f"{domain.lower()}_{timestamp}.log"

    cmd = _build_pytest_cmd(domain, run_mode, report_html, log_file)
    logger.info("Invoking: {}", " ".join(cmd))

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    logger.info("Run complete — exit code: {}", result.returncode)
    logger.info("HTML report: {}", report_html)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
