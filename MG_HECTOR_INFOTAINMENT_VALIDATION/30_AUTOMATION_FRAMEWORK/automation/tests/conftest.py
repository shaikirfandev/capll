from __future__ import annotations

from pathlib import Path
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.adb import AdbAdapter
from adapters.canoe import CanoeAdapter, CanoeConfig
from adapters.diagnostics import DiagnosticsAdapter


@pytest.fixture(scope="session")
def bench_config() -> dict:
    return yaml.safe_load((ROOT / "config" / "bench.yaml").read_text())


@pytest.fixture()
def evidence_dir(bench_config: dict) -> Path:
    path = ROOT / bench_config.get("evidence_root", "evidence")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def canoe(bench_config: dict) -> CanoeAdapter:
    dry_run = bench_config.get("mode", "dry_run") == "dry_run"
    adapter = CanoeAdapter(CanoeConfig(bench_config["canoe"]["config_path"], dry_run=dry_run))
    adapter.open_configuration()
    adapter.start_measurement()
    yield adapter
    adapter.stop_measurement()


@pytest.fixture()
def adb(bench_config: dict) -> AdbAdapter:
    return AdbAdapter(bench_config.get("adb", {}).get("serial", ""))


@pytest.fixture()
def uds(bench_config: dict) -> DiagnosticsAdapter:
    return DiagnosticsAdapter(bench_config.get("diagnostics", {}).get("safe_mode", True))

