from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time


@dataclass
class EvidenceRecord:
    test_id: str
    artifact_type: str
    path: str
    timestamp: str
    notes: str = ""


class EvidenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.records: list[EvidenceRecord] = []

    def add_text(self, test_id: str, name: str, content: str, artifact_type: str = "text") -> Path:
        path = self.root / test_id / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.records.append(
            EvidenceRecord(test_id, artifact_type, str(path), time.strftime("%Y-%m-%d %H:%M:%S"))
        )
        return path

    def write_manifest(self) -> Path:
        path = self.root / "evidence_manifest.json"
        path.write_text(json.dumps([asdict(r) for r in self.records], indent=2), encoding="utf-8")
        return path
