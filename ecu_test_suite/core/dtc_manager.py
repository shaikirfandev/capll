"""
DTC (Diagnostic Trouble Code) management — ISO 14229-1 services 0x19 / 0x14.

Key types
---------
:class:`DTCRecord`   — decoded single DTC with status bit names.
:class:`DTCSnapshot` — set of DTCs captured at one point in time.
:class:`DTCManager`  — high-level helper: read, clear, diff snapshots.

Typical usage in a pytest fixture::

    dtc_mgr   = DTCManager(uds_client, dtc_map={0xC00100: "Front Camera Fault"})
    before    = dtc_mgr.read_all()
    # ... exercise ECU ...
    after     = dtc_mgr.read_all()
    new_faults = dtc_mgr.diff(before, after)
    assert new_faults == [], f"Unexpected DTCs: {new_faults}"
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


# ---------------------------------------------------------------------------
# DTC status bit definitions  (ISO 14229-1, Table D.1)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class DTCRecord:
    """A single DTC entry from a ReadDTCInformation response."""

    dtc_code:    int    # 3-byte DTC code (e.g. 0xC00100)
    status_byte: int    # Combined status bits
    description: str = ""   # Human-readable label from the config DTC map
    snapshot_data: bytes = b""

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def code_str(self) -> str:
        """
        ISO/SAE formatted DTC string (e.g. ``"P0300"``).

        Prefix mapping (high byte):
        * 0x00–0x3F → P (Powertrain)
        * 0x40–0x7F → C (Chassis)
        * 0x80–0xBF → B (Body)
        * 0xC0–0xFF → U (Network/Communication)
        """
        high = (self.dtc_code >> 16) & 0xFF
        mid  = (self.dtc_code >> 8)  & 0xFF
        low  =  self.dtc_code        & 0xFF
        prefix = {0x00: "P", 0x40: "C", 0x80: "B", 0xC0: "U"}.get(high & 0xC0, "X")
        return f"{prefix}{high & 0x3F:01X}{mid:02X}{low:02X}"

    @property
    def active_bits(self) -> list[str]:
        """Return names of all status bits that are currently set."""
        return [
            name
            for bit, name in DTC_STATUS_BITS.items()
            if self.status_byte & (1 << bit)
        ]

    @property
    def is_confirmed(self) -> bool:
        """``True`` when the *confirmedDTC* bit (bit 3) is set."""
        return bool(self.status_byte & 0x08)

    @property
    def is_pending(self) -> bool:
        """``True`` when the *pendingDTC* bit (bit 2) is set."""
        return bool(self.status_byte & 0x04)

    @property
    def is_warning_indicator(self) -> bool:
        """``True`` when the *warningIndicatorRequested* bit (bit 7) is set."""
        return bool(self.status_byte & 0x80)

    def __str__(self) -> str:
        desc = f" — {self.description}" if self.description else ""
        return f"{self.code_str}(0x{self.dtc_code:06X}) status=0x{self.status_byte:02X}{desc}"


@dataclass
class DTCSnapshot:
    """All DTC records captured at a single point in time."""

    timestamp: float = field(default_factory=time.time)
    records:   list[DTCRecord] = field(default_factory=list)
    raw_response: bytes = b""

    @property
    def confirmed_dtcs(self) -> list[DTCRecord]:
        """Subset of records with the *confirmedDTC* bit set."""
        return [r for r in self.records if r.is_confirmed]

    @property
    def pending_dtcs(self) -> list[DTCRecord]:
        """Subset of records with the *pendingDTC* bit set."""
        return [r for r in self.records if r.is_pending]

    def codes(self) -> set[int]:
        """Set of raw DTC codes in this snapshot."""
        return {r.dtc_code for r in self.records}

    def __len__(self) -> int:
        return len(self.records)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------
class DTCManager:
    """
    High-level DTC operations over a UDS client.

    Args:
        uds_client: Any :class:`~core.uds_client.UDSClientBase` instance.
        dtc_map:    Optional mapping of ``{dtc_code_int: "description"}``
                    loaded from the ECU YAML config.
    """

    def __init__(
        self,
        uds_client: object,
        dtc_map: Optional[dict[int, str]] = None,
    ) -> None:
        self._client  = uds_client
        self._dtc_map = dtc_map or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def read_all(self, status_mask: int = 0xFF) -> DTCSnapshot:
        """
        Read all DTCs matching *status_mask* via service 0x19 sub-fn 0x02.

        Args:
            status_mask: ISO 14229 DTC status mask (default 0xFF = all bits).

        Returns:
            :class:`DTCSnapshot` with decoded records.
        """
        response = self._client.read_dtc_by_status_mask(status_mask)  # type: ignore[attr-defined]
        snapshot = DTCSnapshot(raw_response=response.raw_bytes)

        if not response.positive:
            logger.warning("ReadDTCInformation negative response: {}", response)
            return snapshot

        snapshot.records = self._parse_dtc_payload(response.data)
        logger.info(
            "DTC snapshot: total={} confirmed={} pending={}",
            len(snapshot.records),
            len(snapshot.confirmed_dtcs),
            len(snapshot.pending_dtcs),
        )
        return snapshot

    def clear_all(self, group: int = 0xFFFFFF) -> bool:
        """
        Clear all DTCs in *group* via service 0x14.

        Args:
            group: DTC group identifier (0xFFFFFF = all DTCs).

        Returns:
            ``True`` on positive response, ``False`` otherwise.
        """
        response = self._client.clear_dtc(group)  # type: ignore[attr-defined]
        if response.positive:
            logger.info("DTCs cleared (group=0x{:06X})", group)
        else:
            logger.warning("ClearDTC failed: {}", response)
        return response.positive

    def diff(
        self,
        before: DTCSnapshot,
        after: DTCSnapshot,
    ) -> list[DTCRecord]:
        """
        Return DTC records that are present in *after* but not in *before*.

        Useful for verifying that a test stimulus did **not** trigger new faults.

        Args:
            before: Snapshot taken before the test stimulus.
            after:  Snapshot taken after the test stimulus.

        Returns:
            List of newly introduced :class:`DTCRecord` objects.
        """
        before_codes = before.codes()
        new_dtcs = [r for r in after.records if r.dtc_code not in before_codes]
        if new_dtcs:
            logger.warning(
                "NEW DTCs triggered: {}",
                [str(d) for d in new_dtcs],
            )
        return new_dtcs

    # ------------------------------------------------------------------
    # Internal parsing
    # ------------------------------------------------------------------
    def _parse_dtc_payload(self, data: bytes) -> list[DTCRecord]:
        """
        Parse ReadDTCInformation sub-function 0x02 response payload.

        Wire format (ISO 14229-1)::

            [sub_fn:1] [status_avail_mask:1] { [DTC_H:1][DTC_M:1][DTC_L:1][status:1] }*

        Args:
            data: Raw response data bytes (positive response, sans SID byte).

        Returns:
            List of :class:`DTCRecord` objects.
        """
        records: list[DTCRecord] = []
        if len(data) < 2:
            return records

        offset = 2  # skip sub-function + availability-mask
        while offset + 3 < len(data):
            dtc_code    = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2]
            status_byte = data[offset + 3]
            offset += 4
            records.append(
                DTCRecord(
                    dtc_code    = dtc_code,
                    status_byte = status_byte,
                    description = self._dtc_map.get(dtc_code, ""),
                )
            )
        return records
