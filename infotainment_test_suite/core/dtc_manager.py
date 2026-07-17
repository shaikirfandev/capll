"""
DTC management — ISO 14229-1 services 0x19 / 0x14.

Identical API to the multi-domain suite's dtc_manager but tuned for
infotainment-specific severity classifications and freeze-frame parsing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

DTC_STATUS_BITS: dict[int, str] = {
    0: "testFailed",
    1: "testFailedThisMonitoringCycle",
    2: "pendingDTC",
    3: "confirmedDTC",
    4: "testNotCompletedSinceLastClear",
    5: "testFailedSinceLastClear",
    6: "testNotCompletedThisMonitoringCycle",
    7: "warningIndicatorRequested",
}


@dataclass
class DTCRecord:
    dtc_code:    int
    status_byte: int
    description: str   = ""
    severity:    str   = ""
    snapshot_data: bytes = b""

    @property
    def code_str(self) -> str:
        h = (self.dtc_code >> 16) & 0xFF
        m = (self.dtc_code >> 8)  & 0xFF
        l =  self.dtc_code        & 0xFF
        p = {0x00: "P", 0x40: "C", 0x80: "B", 0xC0: "U"}.get(h & 0xC0, "X")
        return f"{p}{h & 0x3F:01X}{m:02X}{l:02X}"

    @property
    def is_confirmed(self) -> bool:
        return bool(self.status_byte & 0x08)

    @property
    def is_pending(self) -> bool:
        return bool(self.status_byte & 0x04)

    @property
    def is_test_failed(self) -> bool:
        return bool(self.status_byte & 0x01)

    def active_bits(self) -> list[str]:
        return [n for b, n in DTC_STATUS_BITS.items() if self.status_byte & (1 << b)]


@dataclass
class DTCSnapshot:
    timestamp: float = field(default_factory=time.time)
    records:   list[DTCRecord] = field(default_factory=list)
    raw_response: bytes = b""

    @property
    def confirmed_dtcs(self) -> list[DTCRecord]:
        return [r for r in self.records if r.is_confirmed]

    @property
    def pending_dtcs(self) -> list[DTCRecord]:
        return [r for r in self.records if r.is_pending]

    def codes(self) -> set[int]:
        return {r.dtc_code for r in self.records}

    def __len__(self) -> int:
        return len(self.records)


@dataclass
class FreezeFrameRecord:
    """Snapshot data stored at the time a DTC was set."""
    dtc_code:   int
    record_num: int
    raw_data:   bytes

    @property
    def code_str(self) -> str:
        h = (self.dtc_code >> 16) & 0xFF
        m = (self.dtc_code >> 8)  & 0xFF
        l =  self.dtc_code        & 0xFF
        p = {0x00: "P", 0x40: "C", 0x80: "B", 0xC0: "U"}.get(h & 0xC0, "X")
        return f"{p}{h & 0x3F:01X}{m:02X}{l:02X}"


class DTCManager:
    """High-level DTC operations — read, clear, diff, freeze frames."""

    def __init__(
        self,
        uds_client: object,
        dtc_catalogue: Optional[dict] = None,
    ) -> None:
        self._client    = uds_client
        self._catalogue = dtc_catalogue or {}

    # ------------------------------------------------------------------
    def read_all(self, status_mask: int = 0xFF) -> DTCSnapshot:
        resp = self._client.read_dtc_by_status_mask(status_mask)  # type: ignore[attr-defined]
        snap = DTCSnapshot(raw_response=resp.raw_bytes)
        if not resp.positive:
            logger.warning("ReadDTCInformation negative: {}", resp)
            return snap
        snap.records = self._parse(resp.data)
        logger.info("DTC snapshot: total={} confirmed={} pending={}",
                    len(snap), len(snap.confirmed_dtcs), len(snap.pending_dtcs))
        return snap

    def read_confirmed(self) -> DTCSnapshot:
        return self.read_all(status_mask=0x08)

    def read_pending(self) -> DTCSnapshot:
        return self.read_all(status_mask=0x04)

    def clear_all(self, group: int = 0xFFFFFF) -> bool:
        resp = self._client.clear_dtc(group)  # type: ignore[attr-defined]
        if resp.positive:
            logger.info("DTCs cleared group=0x{:06X}", group)
        else:
            logger.warning("ClearDTC failed: {}", resp)
        return resp.positive

    def diff(self, before: DTCSnapshot, after: DTCSnapshot) -> list[DTCRecord]:
        before_codes = before.codes()
        new = [r for r in after.records if r.dtc_code not in before_codes]
        if new:
            logger.warning("NEW DTCs: {}", [str(r) for r in new])
        return new

    # ------------------------------------------------------------------
    def _parse(self, data: bytes) -> list[DTCRecord]:
        records: list[DTCRecord] = []
        if len(data) < 2:
            return records
        offset = 2  # skip sub-fn + availability mask
        while offset + 3 < len(data):
            code   = (data[offset] << 16) | (data[offset+1] << 8) | data[offset+2]
            status = data[offset + 3]
            offset += 4
            entry  = self._catalogue.get(f"0x{code:06X}", {})
            records.append(DTCRecord(
                dtc_code    = code,
                status_byte = status,
                description = entry.get("description", ""),
                severity    = entry.get("severity",    ""),
            ))
        return records
