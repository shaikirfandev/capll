"""
HTML and JSON test report generator.

Reads :class:`RunSummary` data (populated by conftest.py fixtures during the
pytest run) and renders a self-contained HTML report via a Jinja2 template.
A JSON sidecar is also written for downstream machine consumption.

Usage from conftest.py::

    summary = RunSummary(domain="ADAS", ...)
    generator = ReportGenerator(output_dir=Path("reports/"))
    generator.generate(summary)
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

# Jinja2 template lives alongside this file
TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class FrameRecord:
    """A single CAN request/response pair captured during a test."""
    direction: str   # "TX" or "RX"
    can_id:    int
    data_hex:  str
    timestamp: float = 0.0

    def __str__(self) -> str:
        return f"{self.direction} ID=0x{self.can_id:X} DATA={self.data_hex}"


@dataclass
class TestCaseRecord:
    """Collected data for a single pytest test case execution."""
    name:        str
    domain:      str
    outcome:     str         # "passed" | "failed" | "error" | "skipped"
    duration_s:  float = 0.0
    uds_service: str   = ""  # e.g. "ReadDataByIdentifier (0x22)"
    expected:    str   = ""
    actual:      str   = ""
    dtcs_before: list[str] = field(default_factory=list)
    dtcs_after:  list[str] = field(default_factory=list)
    new_dtcs:    list[str] = field(default_factory=list)
    frames:      list[FrameRecord] = field(default_factory=list)
    error_message: str = ""
    timestamp:   str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def outcome_css(self) -> str:
        """Bootstrap contextual class for the outcome badge."""
        return {
            "passed":  "success",
            "failed":  "danger",
            "error":   "warning",
            "skipped": "secondary",
        }.get(self.outcome, "light")


@dataclass
class RunSummary:
    """Aggregated statistics and test records for one test session."""
    domain:      str
    run_id:      str
    start_time:  str
    end_time:    str
    total:       int = 0
    passed:      int = 0
    failed:      int = 0
    errors:      int = 0
    skipped:     int = 0
    test_cases:  list[TestCaseRecord] = field(default_factory=list)
    can_trace_path: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Pass rate as a percentage (0.0–100.0)."""
        if self.total == 0:
            return 0.0
        return round((self.passed / self.total) * 100, 1)


# ---------------------------------------------------------------------------
# Collector (populated by conftest.py during the pytest run)
# ---------------------------------------------------------------------------
class ReportCollector:
    """
    In-memory sink for test case records.

    A single session-scoped instance is created by the ``report_collector``
    fixture in *conftest.py*.  Each test's ``record_test_result`` fixture
    calls :meth:`add` at teardown.
    """

    def __init__(self) -> None:
        self._records: list[TestCaseRecord] = []

    def add(self, record: TestCaseRecord) -> None:
        """Append a completed test case record."""
        self._records.append(record)

    def get_all(self) -> list[TestCaseRecord]:
        """Return a snapshot of all collected records."""
        return list(self._records)

    def clear(self) -> None:
        """Reset the collector (useful between repeated session runs)."""
        self._records.clear()

    def build_summary(self, domain: str, run_id: str) -> RunSummary:
        """Derive a :class:`RunSummary` from all collected records."""
        records = self.get_all()
        return RunSummary(
            domain     = domain,
            run_id     = run_id,
            start_time = records[0].timestamp if records else datetime.now().isoformat(),
            end_time   = datetime.now().isoformat(),
            total      = len(records),
            passed     = sum(1 for r in records if r.outcome == "passed"),
            failed     = sum(1 for r in records if r.outcome == "failed"),
            errors     = sum(1 for r in records if r.outcome == "error"),
            skipped    = sum(1 for r in records if r.outcome == "skipped"),
            test_cases = records,
        )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------
class ReportGenerator:
    """
    Renders Jinja2 HTML and JSON reports from a :class:`RunSummary`.

    Args:
        output_dir: Directory where report files are written.
                    Created automatically if absent.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------
    def generate(self, summary: RunSummary) -> Path:
        """
        Render the Jinja2 HTML template and write the report file.

        Args:
            summary: Populated :class:`RunSummary`.

        Returns:
            Path of the generated HTML file.
        """
        try:
            from jinja2 import Environment, FileSystemLoader  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("Jinja2 not installed.  Run: pip install Jinja2") from exc

        env = Environment(
            loader    = FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape = True,
        )
        # Expose Python's built-in enumerate to the template
        env.globals["enumerate"] = enumerate
        template = env.get_template("report_template.html")
        html = template.render(
            summary      = summary,
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        out_path = self._output_dir / f"{summary.domain.lower()}_{summary.run_id}_report.html"
        out_path.write_text(html, encoding="utf-8")
        logger.info("HTML report → {}", out_path)
        return out_path

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    def generate_json(self, summary: RunSummary) -> Path:
        """
        Write a JSON sidecar file alongside the HTML report.

        Args:
            summary: Populated :class:`RunSummary`.

        Returns:
            Path of the generated JSON file.
        """
        def _default(obj: object) -> object:
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)  # type: ignore[arg-type]
            return str(obj)

        out_path = self._output_dir / f"{summary.domain.lower()}_{summary.run_id}_report.json"
        out_path.write_text(
            json.dumps(dataclasses.asdict(summary), default=_default, indent=2),
            encoding="utf-8",
        )
        logger.info("JSON report → {}", out_path)
        return out_path
