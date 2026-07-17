"""
HTML + JSON report generator with an Infotainment-specific DTC Summary section.

The DTC summary table shows every DTC that was set or cleared during the run,
cross-referenced with the ``infotainment_dtcs.yaml`` catalogue.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass
class TestCaseRecord:
    name:          str
    module:        str   = ""   # e.g. "uds", "dtc", "features.bluetooth"
    feature:       str   = ""   # e.g. "Bluetooth"
    outcome:       str   = "unknown"
    duration_s:    float = 0.0
    uds_service:   str   = ""
    expected:      str   = ""
    actual:        str   = ""
    dtcs_before:   list[str] = field(default_factory=list)
    dtcs_after:    list[str] = field(default_factory=list)
    new_dtcs:      list[str] = field(default_factory=list)
    cleared_dtcs:  list[str] = field(default_factory=list)
    transactions:  list[dict] = field(default_factory=list)  # UDSTransaction.to_dict()
    error_message: str   = ""
    timestamp:     str   = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def outcome_css(self) -> str:
        return {"passed": "success", "failed": "danger",
                "error": "warning", "skipped": "secondary"}.get(self.outcome, "light")


@dataclass
class DTCSummaryEntry:
    code_str:    str
    dtc_code:    int
    description: str
    severity:    str
    status:      str   # "set_during_run" | "cleared_during_run" | "present_at_end"
    test_name:   str   # which test triggered it


@dataclass
class RunSummary:
    run_id:        str
    start_time:    str
    end_time:      str
    total:         int = 0
    passed:        int = 0
    failed:        int = 0
    errors:        int = 0
    skipped:       int = 0
    test_cases:    list[TestCaseRecord] = field(default_factory=list)
    dtc_summary:   list[DTCSummaryEntry] = field(default_factory=list)
    can_trace_path: Optional[str] = None
    mock_mode:     bool = True

    @property
    def pass_rate(self) -> float:
        return round((self.passed / self.total) * 100, 1) if self.total else 0.0


class ReportCollector:
    def __init__(self) -> None:
        self._records: list[TestCaseRecord]    = []
        self._dtc_entries: list[DTCSummaryEntry] = []

    def add(self, record: TestCaseRecord) -> None:
        self._records.append(record)

    def add_dtc_event(self, entry: DTCSummaryEntry) -> None:
        self._dtc_entries.append(entry)

    def get_all(self) -> list[TestCaseRecord]:
        return list(self._records)

    def get_dtc_summary(self) -> list[DTCSummaryEntry]:
        return list(self._dtc_entries)

    def build_summary(self, run_id: str, mock_mode: bool = True) -> RunSummary:
        records = self.get_all()
        return RunSummary(
            run_id      = run_id,
            start_time  = records[0].timestamp if records else datetime.now().isoformat(),
            end_time    = datetime.now().isoformat(),
            total       = len(records),
            passed      = sum(1 for r in records if r.outcome == "passed"),
            failed      = sum(1 for r in records if r.outcome == "failed"),
            errors      = sum(1 for r in records if r.outcome == "error"),
            skipped     = sum(1 for r in records if r.outcome == "skipped"),
            test_cases  = records,
            dtc_summary = self.get_dtc_summary(),
            mock_mode   = mock_mode,
        )


class ReportGenerator:
    def __init__(self, output_dir: Path) -> None:
        self._out = output_dir
        self._out.mkdir(parents=True, exist_ok=True)

    def generate(self, summary: RunSummary) -> Path:
        try:
            from jinja2 import Environment, FileSystemLoader  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("pip install Jinja2") from exc

        env = Environment(
            loader     = FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape = True,
        )
        env.globals["enumerate"] = enumerate
        tmpl = env.get_template("report_template.html")
        html = tmpl.render(summary=summary, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        out = self._out / f"infotainment_{summary.run_id}_report.html"
        out.write_text(html, encoding="utf-8")
        logger.info("HTML report → {}", out)
        return out

    def generate_json(self, summary: RunSummary) -> Path:
        def _default(o: object) -> object:
            return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else str(o)  # type: ignore[arg-type]

        out = self._out / f"infotainment_{summary.run_id}_report.json"
        out.write_text(json.dumps(dataclasses.asdict(summary), default=_default, indent=2))
        logger.info("JSON report → {}", out)
        return out
