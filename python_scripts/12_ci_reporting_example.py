#!/usr/bin/env python3
"""Section 12: CI-style test reporting example (JUnit XML + Markdown)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List
import time
import xml.etree.ElementTree as ET


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_s: float
    message: str = ""


def run_case(name: str, fn: Callable[[], None]) -> TestResult:
    start = time.perf_counter()
    try:
        fn()
        passed = True
        message = ""
    except AssertionError as exc:
        passed = False
        message = str(exc)
    duration = time.perf_counter() - start
    return TestResult(name=name, passed=passed, duration_s=duration, message=message)


def write_junit(results: List[TestResult], output_file: Path) -> None:
    tests = len(results)
    failures = sum(1 for r in results if not r.passed)
    total_time = sum(r.duration_s for r in results)

    suite = ET.Element("testsuite", {
        "name": "automotive_automation_suite",
        "tests": str(tests),
        "failures": str(failures),
        "errors": "0",
        "time": f"{total_time:.6f}",
    })

    for result in results:
        case = ET.SubElement(suite, "testcase", {
            "classname": "automotive.samples",
            "name": result.name,
            "time": f"{result.duration_s:.6f}",
        })
        if not result.passed:
            failure = ET.SubElement(case, "failure", {"message": result.message or "Assertion failed"})
            failure.text = result.message or "Test failed"

    tree = ET.ElementTree(suite)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


def write_markdown_summary(results: List[TestResult], output_file: Path) -> None:
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    lines = [
        "# Automotive CI Test Summary",
        "",
        f"- Total: {total}",
        f"- Passed: {passed}",
        f"- Failed: {total - passed}",
        "",
        "| Test Case | Status | Duration (ms) | Message |",
        "|---|---|---:|---|",
    ]

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"| {r.name} | {status} | {r.duration_s * 1000:.2f} | {r.message} |")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    # Example test cases (replace with real test hooks in production).
    cases = [
        ("can_speed_plausibility", lambda: (_ for _ in ()).throw(AssertionError("speed out of range")) if 80 > 250 else None),
        ("uds_read_vin", lambda: (_ for _ in ()).throw(AssertionError("VIN missing")) if not "VIN_DEMO".startswith("VIN") else None),
        ("gateway_latency", lambda: (_ for _ in ()).throw(AssertionError("latency too high")) if 4 > 10 else None),
        ("ota_precheck_voltage", lambda: (_ for _ in ()).throw(AssertionError("voltage low")) if 12.6 < 12.0 else None),
    ]

    results = [run_case(name, fn) for name, fn in cases]

    junit_file = Path("python_automotive_automation_testing/reports/junit_automotive.xml")
    md_file = Path("python_automotive_automation_testing/reports/summary.md")

    write_junit(results, junit_file)
    write_markdown_summary(results, md_file)

    passed = sum(1 for r in results if r.passed)
    print("=== CI Reporting Example ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name} ({r.duration_s * 1000:.2f} ms) {r.message}")
    print(f"Summary: {passed}/{len(results)} passed")
    print(f"JUnit file: {junit_file}")
    print(f"Markdown summary: {md_file}")


if __name__ == "__main__":
    main()
