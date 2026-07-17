"""
Release regression report generator — HTML + JSON output.

Produces a self-contained single-file HTML report with Bootstrap 5 styling
and a machine-readable JSON sidecar suitable for CI/CD pipeline gates.

Report structure (HTML sections)
---------------------------------
1. Executive Summary — pass/fail/error counts, regression counts, sign-off recommendation.
2. UDS Service Results — table of every service tested.
3. DID Matrix Results — per-DID status with baseline diff column.
4. RID Matrix Results — per-RID status with timing comparison.
5. NRC Matrix Results — per-NRC scenario status.
6. Baseline Comparison — detailed diff: regressions, improvements, new, removed.

Usage::

    from core.report_generator import ReportGenerator
    gen = ReportGenerator(reports_dir=Path("reports"))
    html_path, json_path = gen.generate(run_result, diff)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .baseline_manager import BaselineDiff, RunResult, TestRecord


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """Generates HTML and JSON regression reports."""

    def __init__(self, reports_dir: Path) -> None:
        self._dir = reports_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        run: RunResult,
        diff: Optional[BaselineDiff] = None,
    ) -> tuple[Path, Path]:
        """
        Write the HTML and JSON reports for a completed run.

        Args:
            run:  Current run results.
            diff: Baseline comparison result (None on first-ever run).

        Returns:
            Tuple of (html_path, json_path).
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stem = f"{run.ecu}_{run.version}_{ts}"
        html_path = self._dir / f"{stem}.html"
        json_path = self._dir / f"{stem}.json"

        html_path.write_text(self._render_html(run, diff), encoding="utf-8")
        json_path.write_text(self._render_json(run, diff), encoding="utf-8")

        return html_path, json_path

    # ------------------------------------------------------------------
    # JSON output
    # ------------------------------------------------------------------

    @staticmethod
    def _render_json(run: RunResult, diff: Optional[BaselineDiff]) -> str:
        payload: dict = {
            "report_type": "ecu_regression_suite",
            "ecu": run.ecu,
            "version": run.version,
            "timestamp": run.timestamp,
            "run_id": run.run_id,
            "mock_mode": run.mock_mode,
            "summary": {
                "total":  len(run.records),
                "pass":   run.pass_count(),
                "fail":   run.fail_count(),
                "error":  run.error_count(),
            },
        }
        if diff:
            payload["baseline_comparison"] = {
                "baseline_version": diff.baseline_version,
                "current_version":  diff.current_version,
                **diff.summary(),
                "regressions": [
                    {
                        "test_id": e.test_id,
                        "changed_fields": e.changed_fields,
                        "baseline_status": e.baseline_record.status if e.baseline_record else None,
                        "current_status":  e.current_record.status  if e.current_record  else None,
                        "baseline_value":  e.baseline_record.actual_value if e.baseline_record else None,
                        "current_value":   e.current_record.actual_value  if e.current_record  else None,
                    }
                    for e in diff.regressions
                ],
                "removed": [
                    {"test_id": e.test_id}
                    for e in diff.removed
                ],
                "new_items": [
                    {"test_id": e.test_id}
                    for e in diff.new_items
                ],
            }
        payload["records"] = [
            {
                "test_id":      r.test_id,
                "category":     r.category,
                "status":       r.status,
                "elapsed_ms":   round(r.elapsed_ms, 2),
                "actual_value": r.actual_value,
                "actual_nrc":   r.actual_nrc,
                "failure_reason": r.failure_reason,
            }
            for r in sorted(run.records.values(), key=lambda x: x.test_id)
        ]
        return json.dumps(payload, indent=2)

    # ------------------------------------------------------------------
    # HTML output
    # ------------------------------------------------------------------

    def _render_html(self, run: RunResult, diff: Optional[BaselineDiff]) -> str:
        total  = len(run.records)
        passed = run.pass_count()
        failed = run.fail_count()
        errors = run.error_count()
        pass_pct = (passed / total * 100) if total else 0

        sign_off = diff.sign_off_recommendation if diff else "N/A (first baseline run)"
        sign_off_cls = "danger" if diff and diff.has_regressions else "success"

        # ---- Section 1: Executive summary ----
        exec_summary = f"""
        <div class="row mb-4">
          <div class="col-md-3">
            <div class="card text-white bg-primary">
              <div class="card-body text-center">
                <h2 class="card-title">{total}</h2><p class="mb-0">Total Tests</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-white bg-success">
              <div class="card-body text-center">
                <h2 class="card-title">{passed}</h2><p class="mb-0">Passed</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-white bg-danger">
              <div class="card-body text-center">
                <h2 class="card-title">{failed + errors}</h2><p class="mb-0">Failed / Error</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-white bg-info">
              <div class="card-body text-center">
                <h2 class="card-title">{pass_pct:.1f}%</h2><p class="mb-0">Pass Rate</p>
              </div>
            </div>
          </div>
        </div>
        <div class="alert alert-{sign_off_cls}">
          <strong>Sign-off Recommendation:</strong> {sign_off}
        </div>
        """

        # ---- Section 2-5: Results tables by category ----
        categories = {
            "service": "UDS Service Results",
            "did":     "DID Matrix Results",
            "rid":     "RID Matrix Results",
            "nrc":     "NRC Matrix Results",
        }
        results_html = ""
        for cat, title in categories.items():
            records = [r for r in run.records.values() if r.category == cat]
            if not records:
                continue
            diff_map: dict[str, str] = {}
            if diff:
                for e in diff.regressions:
                    diff_map[e.test_id] = "regression"
                for e in diff.improvements:
                    diff_map[e.test_id] = "improvement"
                for e in diff.new_items:
                    diff_map[e.test_id] = "new"
                for e in diff.unchanged:
                    diff_map[e.test_id] = "unchanged"

            rows = ""
            for r in sorted(records, key=lambda x: x.test_id):
                sc = {"pass": "success", "fail": "danger", "error": "warning", "skip": "secondary"}.get(r.status, "secondary")
                dc = diff_map.get(r.test_id, "—")
                dc_badge = {
                    "regression":  '<span class="badge bg-danger">regression</span>',
                    "improvement": '<span class="badge bg-success">improvement</span>',
                    "new":         '<span class="badge bg-info">new</span>',
                    "unchanged":   '<span class="badge bg-light text-dark">unchanged</span>',
                }.get(dc, dc)
                timing_col = f"{r.elapsed_ms:.1f} ms" if cat == "rid" else ""
                rows += f"""
                <tr class="table-{sc}">
                  <td><code>{r.test_id}</code></td>
                  <td><span class="badge bg-{sc}">{r.status.upper()}</span></td>
                  <td><code>{r.actual_value or '—'}</code></td>
                  <td><code>{r.actual_nrc or '—'}</code></td>
                  {'<td>' + timing_col + '</td>' if cat == 'rid' else ''}
                  <td>{dc_badge}</td>
                  <td>{r.failure_reason or '—'}</td>
                </tr>"""

            timing_th = "<th>Elapsed</th>" if cat == "rid" else ""
            results_html += f"""
            <h3 class="mt-4">{title}</h3>
            <div class="table-responsive">
              <table class="table table-sm table-bordered table-hover">
                <thead class="table-dark">
                  <tr>
                    <th>Test ID</th><th>Status</th><th>Value</th>
                    <th>NRC</th>{timing_th}<th>Baseline Diff</th><th>Reason</th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

        # ---- Section 6: Baseline comparison ----
        diff_section = ""
        if diff:
            reg_rows = "".join(
                f"""<tr class="table-danger">
                  <td><code>{e.test_id}</code></td>
                  <td>{e.baseline_record.status if e.baseline_record else '—'}</td>
                  <td>{e.current_record.status  if e.current_record  else '—'}</td>
                  <td><code>{e.baseline_record.actual_value if e.baseline_record else '—'}</code></td>
                  <td><code>{e.current_record.actual_value  if e.current_record  else '—'}</code></td>
                  <td>{', '.join(e.changed_fields) or '—'}</td>
                </tr>"""
                for e in diff.regressions
            )
            removed_rows = "".join(
                f'<tr class="table-warning"><td colspan="6"><code>{e.test_id}</code> — removed from ECU response</td></tr>'
                for e in diff.removed
            )
            new_rows = "".join(
                f'<tr class="table-info"><td colspan="6"><code>{e.test_id}</code> — new in this release (review required)</td></tr>'
                for e in diff.new_items
            )
            diff_section = f"""
            <h3 class="mt-4">Baseline Comparison (vs {diff.baseline_version})</h3>
            <table class="table table-sm table-bordered">
              <thead class="table-dark">
                <tr><th>Test ID</th><th>Baseline Status</th><th>Current Status</th>
                    <th>Baseline Value</th><th>Current Value</th><th>Changed Fields</th></tr>
              </thead>
              <tbody>{reg_rows}{removed_rows}{new_rows}</tbody>
            </table>"""

        mock_badge = (
            '<span class="badge bg-warning text-dark ms-2">[MOCK/SIMULATED — no real hardware]</span>'
            if run.mock_mode else
            '<span class="badge bg-success ms-2">Hardware</span>'
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ECU Regression Report — {run.ecu.upper()} {run.version}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; }}
    h2, h3 {{ margin-top: 1.5rem; }}
    code {{ font-size: 0.85em; }}
  </style>
</head>
<body>
<div class="container-fluid p-4">
  <h1>ECU Regression Suite Report{mock_badge}</h1>
  <p class="text-muted">
    ECU: <strong>{run.ecu.upper()}</strong> &nbsp;|&nbsp;
    Version: <strong>{run.version}</strong> &nbsp;|&nbsp;
    Run ID: <code>{run.run_id}</code> &nbsp;|&nbsp;
    Timestamp: {run.timestamp}
  </p>
  <hr>
  <h2>1. Executive Summary</h2>
  {exec_summary}
  <h2>2–5. Test Results by Category</h2>
  {results_html}
  <h2>6. Baseline Comparison</h2>
  {diff_section if diff_section else '<p class="text-muted">No baseline available for comparison (first run).</p>'}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
