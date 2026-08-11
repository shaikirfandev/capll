from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass(slots=True)
class Scenario:
    id: str
    name: str
    data: dict[str, Any]


class ScenarioLoader:
    def __init__(self, base_path: Optional[Path] = None) -> None:
        self.base_path = Path(base_path) if base_path else None

    def load(self, filename: str | Path) -> list[Scenario]:
        path = Path(filename)
        if not path.is_absolute():
            if self.base_path is None:
                raise ValueError("Relative scenario path requires base_path")
            path = self.base_path / path
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        scenarios = []
        for item in payload.get("scenarios", []):
            scenarios.append(Scenario(id=item["id"], name=item["name"], data=item))
        return scenarios
