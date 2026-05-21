from __future__ import annotations

import re
from pathlib import Path


class AscLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines = path.read_text(errors="ignore").splitlines() if path.exists() else []

    def count_can_id(self, can_id: str) -> int:
        pattern = re.compile(rf"\b{re.escape(can_id)}\b", re.IGNORECASE)
        return sum(1 for line in self.lines if pattern.search(line))

    def first_timestamp_for_id(self, can_id: str) -> float | None:
        pattern = re.compile(rf"^\s*([0-9]+\.[0-9]+).*?\b{re.escape(can_id)}\b", re.IGNORECASE)
        for line in self.lines:
            match = pattern.search(line)
            if match:
                return float(match.group(1))
        return None

