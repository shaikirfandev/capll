from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DTCRecord:
    code: int
    status: int
    description: str
    freeze_frame: dict[str, float | int | str] = field(default_factory=dict)
    occurrence_count: int = 1


class DTCManager:
    def __init__(self) -> None:
        self.records: dict[int, DTCRecord] = {}

    def set_dtc(self, code: int, status: int = 0x0F, description: str = "", freeze_frame: dict[str, float | int | str] | None = None) -> DTCRecord:
        if code in self.records:
            record = self.records[code]
            record.status = status
            record.occurrence_count += 1
            if freeze_frame:
                record.freeze_frame = dict(freeze_frame)
            if description:
                record.description = description
            return record
        record = DTCRecord(code=code, status=status, description=description or f"DTC-{code:06X}", freeze_frame=dict(freeze_frame or {}))
        self.records[code] = record
        return record

    def read_active(self, status_mask: int = 0xFF) -> list[DTCRecord]:
        return [record for record in self.records.values() if record.status & status_mask]

    def read_all(self) -> list[DTCRecord]:
        return list(self.records.values())

    def clear(self, code: int | None = None) -> None:
        if code is None:
            self.records.clear()
        else:
            self.records.pop(code, None)

    def get_freeze_frame(self, code: int) -> dict[str, float | int | str]:
        return dict(self.records[code].freeze_frame)
