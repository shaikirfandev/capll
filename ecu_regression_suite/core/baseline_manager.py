"""
Baseline manager — save, load, and diff per-release test results.

Workflow
--------
1. After a test run, :meth:`BaselineManager.save_run` persists the
   :class:`RunResult` to ``baselines/<ecu>/<version>_baseline.json``.
2. On the next run, :meth:`BaselineManager.load_baseline` reads the stored
   baseline for the *previous* release.
3. :meth:`BaselineManager.diff` compares current vs baseline and classifies
   every test result as ``regression``, ``improvement``, ``unchanged``,
   ``new``, or ``removed``.
4. The resulting :class:`BaselineDiff` is consumed by the report generator.

Result key format
-----------------
``"<category>/<test_id>"`` e.g. ``"did/0xF190-read"`` or ``"rid/0x0201-start"``.
Category values: ``did``, ``rid``, ``nrc``, ``service``.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TestRecord:
    """Stored result for a single test case."""

    test_id: str                        # unique key e.g. "did/0xF190-read"
    category: str                       # "did" | "rid" | "nrc" | "service"
    status: str                         # "pass" | "fail" | "error" | "skip"
    service_id: Optional[str] = None    # hex string e.g. "0x22"
    did_id: Optional[str] = None        # hex string e.g. "0xF190"
    rid_id: Optional[str] = None
    nrc_code: Optional[str] = None
    actual_value: Optional[str] = None  # hex string of response data
    actual_nrc: Optional[str] = None    # hex NRC code if negative response received
    elapsed_ms: float = 0.0
    session: Optional[str] = None
    failure_reason: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """All test records from a single regression run."""

    ecu: str
    version: str
    timestamp: str
    run_id: str
    mock_mode: bool
    records: Dict[str, TestRecord] = field(default_factory=dict)

    def add(self, record: TestRecord) -> None:
        """Add or overwrite a test record."""
        self.records[record.test_id] = record

    def pass_count(self) -> int:
        return sum(1 for r in self.records.values() if r.status == "pass")

    def fail_count(self) -> int:
        return sum(1 for r in self.records.values() if r.status == "fail")

    def error_count(self) -> int:
        return sum(1 for r in self.records.values() if r.status == "error")


# ---------------------------------------------------------------------------
# Diff result
# ---------------------------------------------------------------------------

@dataclass
class DiffEntry:
    """One entry in the baseline diff."""

    test_id: str
    classification: str   # "regression" | "improvement" | "unchanged" | "new" | "removed"
    baseline_record: Optional[TestRecord]
    current_record: Optional[TestRecord]
    changed_fields: List[str] = field(default_factory=list)

    @property
    def is_blocking(self) -> bool:
        """Regressions and removals are blocking; others are informational."""
        return self.classification in ("regression", "removed")


@dataclass
class BaselineDiff:
    """Full comparison result between a baseline run and the current run."""

    ecu: str
    baseline_version: str
    current_version: str
    timestamp: str

    regressions:  List[DiffEntry] = field(default_factory=list)
    improvements: List[DiffEntry] = field(default_factory=list)
    unchanged:    List[DiffEntry] = field(default_factory=list)
    new_items:    List[DiffEntry] = field(default_factory=list)
    removed:      List[DiffEntry] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        return len(self.regressions) > 0 or len(self.removed) > 0

    @property
    def sign_off_recommendation(self) -> str:
        if self.has_regressions:
            return "NO-GO — regressions detected (review required before release)"
        if self.improvements or self.new_items:
            return "GO (with review) — improvements / new items detected"
        return "GO — no regressions detected"

    def summary(self) -> dict:
        return {
            "regressions":  len(self.regressions),
            "improvements": len(self.improvements),
            "unchanged":    len(self.unchanged),
            "new_items":    len(self.new_items),
            "removed":      len(self.removed),
            "has_regressions": self.has_regressions,
            "sign_off": self.sign_off_recommendation,
        }


# ---------------------------------------------------------------------------
# Baseline manager
# ---------------------------------------------------------------------------

class BaselineManager:
    """
    Manages per-ECU per-version baseline JSON files.

    Directory layout::

        baselines/
          adas/
            v1.2.0_baseline.json
            v1.3.0_baseline.json
          infotainment/
            v2.0.4_baseline.json
    """

    def __init__(self, baselines_root: Path) -> None:
        self._root = baselines_root
        self._root.mkdir(parents=True, exist_ok=True)

    # -- Save ----------------------------------------------------------------

    def save_run(self, run: RunResult) -> Path:
        """
        Persist a :class:`RunResult` as a baseline candidate.

        The file is named ``<version>_baseline.json``.  Call this at the end
        of every successful run to register it as the new known-good baseline.

        Returns:
            Path to the written file.
        """
        ecu_dir = self._root / run.ecu
        ecu_dir.mkdir(parents=True, exist_ok=True)
        out_path = ecu_dir / f"{run.version}_baseline.json"
        payload = {
            "ecu": run.ecu,
            "version": run.version,
            "timestamp": run.timestamp,
            "run_id": run.run_id,
            "mock_mode": run.mock_mode,
            "records": {k: asdict(v) for k, v in run.records.items()},
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("Baseline saved: {}", out_path)
        return out_path

    # -- Load ----------------------------------------------------------------

    def load_baseline(self, ecu: str, version: Optional[str] = None) -> Optional[RunResult]:
        """
        Load a baseline for the given ECU.

        Args:
            ecu:     ECU name ("adas" or "infotainment").
            version: Specific version string to load.  If None, loads the
                     *most recent* baseline by filename lexicographic order.

        Returns:
            :class:`RunResult` if found, else None.
        """
        ecu_dir = self._root / ecu
        if not ecu_dir.exists():
            logger.warning("No baselines directory for ECU '{}'", ecu)
            return None

        if version:
            candidate = ecu_dir / f"{version}_baseline.json"
            if not candidate.exists():
                logger.warning("Baseline not found: {}", candidate)
                return None
            return self._parse(candidate)

        # Auto-select most recent baseline (lexicographic — assumes vX.Y.Z naming)
        files = sorted(ecu_dir.glob("*_baseline.json"))
        if not files:
            logger.info("No baselines found for ECU '{}'", ecu)
            return None
        chosen = files[-1]
        logger.info("Auto-selected baseline: {}", chosen.name)
        return self._parse(chosen)

    def list_baselines(self, ecu: str) -> List[str]:
        """Return a sorted list of baseline version strings for the given ECU."""
        ecu_dir = self._root / ecu
        if not ecu_dir.exists():
            return []
        return [
            re.sub(r"_baseline\.json$", "", f.name)
            for f in sorted(ecu_dir.glob("*_baseline.json"))
        ]

    # -- Diff ----------------------------------------------------------------

    def diff(self, baseline: RunResult, current: RunResult) -> BaselineDiff:
        """
        Compare *current* run against *baseline*.

        Classification rules:
        - ``regression``  : test was ``pass`` in baseline, now ``fail``/``error``
                            OR test passed both but ``actual_value`` or ``elapsed_ms``
                            changed beyond tolerance.
        - ``improvement`` : test was ``fail``/``error`` in baseline, now ``pass``.
        - ``unchanged``   : status and values identical.
        - ``new``         : test exists in current but not in baseline (new DID/RID added).
        - ``removed``     : test exists in baseline but not in current run.
        """
        result = BaselineDiff(
            ecu=current.ecu,
            baseline_version=baseline.version,
            current_version=current.version,
            timestamp=datetime.utcnow().isoformat(),
        )

        all_keys = set(baseline.records.keys()) | set(current.records.keys())

        for key in sorted(all_keys):
            base_rec = baseline.records.get(key)
            curr_rec = current.records.get(key)

            if base_rec is None and curr_rec is not None:
                result.new_items.append(DiffEntry(
                    test_id=key,
                    classification="new",
                    baseline_record=None,
                    current_record=curr_rec,
                ))
            elif curr_rec is None and base_rec is not None:
                result.removed.append(DiffEntry(
                    test_id=key,
                    classification="removed",
                    baseline_record=base_rec,
                    current_record=None,
                ))
            else:
                assert base_rec is not None and curr_rec is not None
                changed = self._changed_fields(base_rec, curr_rec)

                base_pass = base_rec.status == "pass"
                curr_pass = curr_rec.status == "pass"

                if base_pass and not curr_pass:
                    result.regressions.append(DiffEntry(
                        test_id=key,
                        classification="regression",
                        baseline_record=base_rec,
                        current_record=curr_rec,
                        changed_fields=changed,
                    ))
                elif not base_pass and curr_pass:
                    result.improvements.append(DiffEntry(
                        test_id=key,
                        classification="improvement",
                        baseline_record=base_rec,
                        current_record=curr_rec,
                        changed_fields=changed,
                    ))
                elif changed:
                    # Both pass but something changed (value/timing) — still a regression
                    result.regressions.append(DiffEntry(
                        test_id=key,
                        classification="regression",
                        baseline_record=base_rec,
                        current_record=curr_rec,
                        changed_fields=changed,
                    ))
                else:
                    result.unchanged.append(DiffEntry(
                        test_id=key,
                        classification="unchanged",
                        baseline_record=base_rec,
                        current_record=curr_rec,
                    ))

        logger.info(
            "Baseline diff complete: {} regressions, {} improvements, "
            "{} unchanged, {} new, {} removed",
            len(result.regressions),
            len(result.improvements),
            len(result.unchanged),
            len(result.new_items),
            len(result.removed),
        )
        return result

    # -- Private helpers -----------------------------------------------------

    @staticmethod
    def _parse(path: Path) -> RunResult:
        raw = json.loads(path.read_text(encoding="utf-8"))
        run = RunResult(
            ecu=raw["ecu"],
            version=raw["version"],
            timestamp=raw.get("timestamp", ""),
            run_id=raw.get("run_id", ""),
            mock_mode=raw.get("mock_mode", True),
        )
        for key, rec_dict in raw.get("records", {}).items():
            run.records[key] = TestRecord(**rec_dict)
        return run

    @staticmethod
    def _changed_fields(base: TestRecord, curr: TestRecord) -> List[str]:
        """Return names of fields that differ between two records."""
        changed: List[str] = []
        for fname in ("status", "actual_value", "actual_nrc"):
            b_val = getattr(base, fname)
            c_val = getattr(curr, fname)
            if b_val != c_val:
                changed.append(fname)

        # Timing drift: flag if elapsed_ms changes by >50 ms or >100%
        if base.elapsed_ms and curr.elapsed_ms:
            drift_abs = abs(curr.elapsed_ms - base.elapsed_ms)
            drift_pct = drift_abs / max(base.elapsed_ms, 1.0) * 100
            if drift_abs > 50 or drift_pct > 100:
                changed.append("elapsed_ms")

        return changed
