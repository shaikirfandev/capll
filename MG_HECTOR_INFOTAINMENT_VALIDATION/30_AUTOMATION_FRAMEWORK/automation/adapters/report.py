from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    test_id: str
    result: str
    feature: str
    evidence: str
    defect: str = ""


def write_markdown_report(path: Path, results: list[TestResult]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Automated Validation Report",
        "",
        "| Test ID | Feature | Result | Evidence | Defect |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(f"| {item.test_id} | {item.feature} | {item.result} | {item.evidence} | {item.defect} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
