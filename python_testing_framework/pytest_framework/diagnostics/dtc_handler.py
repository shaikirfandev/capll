"""
pytest_framework/diagnostics/dtc_handler.py

Enterprise ADAS Framework – DTC Lifecycle Manager
===================================================
Provides:
  - DTCDatabase: static lookup of DTC id → name / description
  - DTCMonitor: watches UDSClient for DTC changes (background thread)
  - Assertion helpers for test cases
  - Full DTC lifecycle helper: clear → trigger → verify set → clear → verify gone
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from core.logger import get_logger
from diagnostics.uds_client import DTCEntry, UDSClient

log = get_logger("dtc_handler")


# ── DTC Database ──────────────────────────────────────────────────────────────

DTC_DB: Dict[int, Dict[str, str]] = {
    0xB0100: {"name": "Radar_SignalLoss",          "feature": "AEB/ACC"},
    0xB0101: {"name": "Radar_InternalFault",       "feature": "AEB/ACC"},
    0xB0200: {"name": "Camera_Blockage",           "feature": "LKA/DMS"},
    0xB0201: {"name": "Camera_CalibrationFault",   "feature": "LKA"},
    0xB0300: {"name": "LiDAR_PointCloudLoss",      "feature": "Fusion"},
    0xB0400: {"name": "FusionECU_Timeout",         "feature": "Fusion"},
    0xB0500: {"name": "DMS_CameraOcclusion",       "feature": "DMS"},
    0xB0600: {"name": "ACC_ControllerFault",       "feature": "ACC"},
    0xB0700: {"name": "AEB_BrakeActuatorFault",    "feature": "AEB"},
    0xB0800: {"name": "LKA_SteeringActuatorFault", "feature": "LKA"},
    0xC0100: {"name": "CAN_BusOff",                "feature": "Network"},
    0xC0200: {"name": "ETH_LinkLoss",              "feature": "Ethernet"},
    0xD0100: {"name": "BootloaderFault",           "feature": "Diagnostics"},
    0xD0200: {"name": "E2E_CRCError",              "feature": "Safety"},
}


@dataclass
class DTCDatabase:
    """Static DTC lookup table."""

    @staticmethod
    def lookup(dtc_id: int) -> Dict[str, str]:
        return DTC_DB.get(dtc_id, {
            "name":    f"UNKNOWN_0x{dtc_id:06X}",
            "feature": "Unknown"
        })

    @staticmethod
    def name(dtc_id: int) -> str:
        return DTCDatabase.lookup(dtc_id)["name"]

    @staticmethod
    def all_ids() -> List[int]:
        return list(DTC_DB.keys())


# ── DTC Monitor ───────────────────────────────────────────────────────────────

@dataclass
class DTCEvent:
    timestamp:  float
    dtc_id:     int
    status:     int
    event_type: str  # "SET" | "CLEARED"


class DTCMonitor:
    """
    Background poller that watches for DTC state changes via UDS 0x19.

    Usage:
        monitor = DTCMonitor(uds_client, poll_interval_s=1.0)
        monitor.start()
        # ... run test scenario ...
        assert monitor.was_set(0xB0100)
        monitor.stop()
    """

    def __init__(
        self,
        uds:             UDSClient,
        poll_interval_s: float = 1.0,
        status_mask:     int   = 0x08,   # confirmed DTCs
    ) -> None:
        self._uds          = uds
        self._interval     = poll_interval_s
        self._mask         = status_mask
        self._lock         = threading.Lock()
        self._events:      List[DTCEvent] = []
        self._active:      Set[int] = set()
        self._thread:      Optional[threading.Thread] = None
        self._stop_event   = threading.Event()
        self._callbacks:   Dict[int, List[Callable]] = {}

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="dtc-monitor"
        )
        self._thread.start()
        log.info("[DTCMonitor] started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        log.info("[DTCMonitor] stopped")

    def __enter__(self) -> "DTCMonitor":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    # ── Event access ─────────────────────────────────────────────────────────

    def was_set(self, dtc_id: int) -> bool:
        with self._lock:
            return any(
                e.event_type == "SET" and e.dtc_id == dtc_id
                for e in self._events
            )

    def was_cleared(self, dtc_id: int) -> bool:
        with self._lock:
            return any(
                e.event_type == "CLEARED" and e.dtc_id == dtc_id
                for e in self._events
            )

    def is_active(self, dtc_id: int) -> bool:
        with self._lock:
            return dtc_id in self._active

    def all_events(self) -> List[DTCEvent]:
        with self._lock:
            return list(self._events)

    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def clear_events(self) -> None:
        with self._lock:
            self._events.clear()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def on_dtc_set(self, dtc_id: int, cb: Callable[["DTCEvent"], None]) -> None:
        self._callbacks.setdefault(dtc_id, []).append(cb)

    # ── pytest assertions ─────────────────────────────────────────────────────

    def assert_dtc_set(
        self, dtc_id: int, timeout_s: float = 5.0
    ) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.was_set(dtc_id):
                log.info(f"[DTCMonitor] DTC 0x{dtc_id:06X} SET confirmed")
                return
            time.sleep(0.1)
        name = DTCDatabase.name(dtc_id)
        raise AssertionError(
            f"DTC 0x{dtc_id:06X} ({name}) was NOT set within {timeout_s}s"
        )

    def assert_dtc_cleared(
        self, dtc_id: int, timeout_s: float = 5.0
    ) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if not self.is_active(dtc_id):
                return
            time.sleep(0.1)
        name = DTCDatabase.name(dtc_id)
        raise AssertionError(
            f"DTC 0x{dtc_id:06X} ({name}) still ACTIVE after {timeout_s}s"
        )

    def assert_no_confirmed_dtcs(self) -> None:
        with self._lock:
            confirmed = [dtc for dtc in self._active]
        assert not confirmed, (
            f"Unexpected confirmed DTCs: "
            f"{[f'0x{d:06X}({DTCDatabase.name(d)})' for d in confirmed]}"
        )

    # ── Lifecycle test helper ─────────────────────────────────────────────────

    def run_lifecycle(
        self,
        dtc_id:      int,
        trigger_fn:  Callable[[], None],
        restore_fn:  Callable[[], None],
        set_timeout:  float = 5.0,
        clear_timeout: float = 5.0,
    ) -> None:
        """
        Full DTC lifecycle: clear → trigger → verify SET → restore → clear → verify GONE.
        Designed as a single reusable test helper.
        """
        # 1. Pre-clear
        self._uds.sync_clear_dtcs()
        self.clear_events()
        time.sleep(0.2)

        # 2. Trigger fault condition
        trigger_fn()

        # 3. Assert DTC was set
        self.assert_dtc_set(dtc_id, timeout_s=set_timeout)

        # 4. Restore normal condition
        restore_fn()

        # 5. Clear DTCs
        self._uds.sync_clear_dtcs()

        # 6. Assert DTC no longer active
        self.assert_dtc_cleared(dtc_id, timeout_s=clear_timeout)
        log.info(f"[DTCMonitor] lifecycle OK for DTC 0x{dtc_id:06X}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                dtcs = self._uds.sync_read_dtcs(status_mask=self._mask)
                current_ids = {d.dtc_id for d in dtcs}
                with self._lock:
                    new_set     = current_ids - self._active
                    new_cleared = self._active - current_ids
                    ts = time.monotonic()
                    for did in new_set:
                        entry = DTCEvent(ts, did, 0x08, "SET")
                        self._events.append(entry)
                        log.warning(f"[DTCMonitor] SET 0x{did:06X} ({DTCDatabase.name(did)})")
                        for cb in self._callbacks.get(did, []):
                            try:
                                cb(entry)
                            except Exception:
                                pass
                    for did in new_cleared:
                        self._events.append(DTCEvent(ts, did, 0x00, "CLEARED"))
                    self._active = current_ids
            except Exception as exc:
                log.debug(f"[DTCMonitor] poll error: {exc!r}")
            time.sleep(self._interval)
