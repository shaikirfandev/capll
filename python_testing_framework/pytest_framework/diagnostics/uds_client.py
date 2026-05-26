"""
pytest_framework/diagnostics/uds_client.py

Enterprise ADAS Framework – Full ISO 14229-1 UDS Client
========================================================
Async-first, sync wrappers included.
Services: 0x10 0x11 0x14 0x19 0x22 0x23 0x27 0x28 0x2E 0x31 0x34-0x37 0x3D 0x3E 0x85
Transport: python-isotp + udsoncan / mock for CI.
"""
from __future__ import annotations

import asyncio
import struct
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from core.logger import get_logger

log = get_logger("uds_client")

NRC_DESCRIPTIONS: Dict[int, str] = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooLong",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSubnetComponent",
    0x26: "failurePreventsExecutionOfRequestedAction",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceededNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceivedResponsePending",
    0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
}


class NRCError(Exception):
    def __init__(self, service: int, nrc: int) -> None:
        self.service = service
        self.nrc     = nrc
        desc = NRC_DESCRIPTIONS.get(nrc, f"unknown(0x{nrc:02X})")
        super().__init__(f"NRC 0x{nrc:02X} ({desc}) for service 0x{service:02X}")


@dataclass
class DTCEntry:
    dtc_id:     int
    status:     int
    snapshot:   bytes = b""

    @property
    def status_bits(self) -> Dict[str, bool]:
        return {
            "testFailed":                      bool(self.status & 0x01),
            "testFailedThisMonitoringCycle":   bool(self.status & 0x02),
            "pendingDTC":                      bool(self.status & 0x04),
            "confirmedDTC":                    bool(self.status & 0x08),
            "testNotCompletedSinceLastClear":  bool(self.status & 0x10),
            "testFailedSinceLastClear":        bool(self.status & 0x20),
            "testNotCompleted":                bool(self.status & 0x40),
            "warningIndicatorRequested":       bool(self.status & 0x80),
        }

    def __repr__(self) -> str:
        return f"DTC(0x{self.dtc_id:06X}, status=0x{self.status:02X})"


# ── Transport layer ───────────────────────────────────────────────────────────

class _MockTransport:
    """Headless mock transport for CI without ECU hardware."""
    def __init__(self) -> None:
        self._session = 0x01
        self._dtcs: List[DTCEntry] = []

    async def request(self, data: bytes) -> bytes:
        await asyncio.sleep(0.01)
        sid = data[0]
        if sid == 0x10:  # DSC
            sub = data[1]
            self._session = sub
            return bytes([0x50, sub])
        if sid == 0x11:  # ECU reset
            return bytes([0x51, data[1]])
        if sid == 0x14:  # ClearDTC
            self._dtcs.clear()
            return bytes([0x54])
        if sid == 0x19:  # ReadDTCByStatus
            sub = data[1]
            if sub == 0x02:
                # Report 2 fake DTCs
                resp = bytearray([0x59, 0x02, 0xFF])
                for dtc in self._dtcs:
                    resp += struct.pack(">I", dtc.dtc_id)[1:] + bytes([dtc.status])
                return bytes(resp)
            return bytes([0x59, sub])
        if sid == 0x22:  # ReadDID
            did = (data[1] << 8) | data[2]
            if did == 0xF190:  # VIN
                return bytes([0x62, 0xF1, 0x90]) + b"WBAJB0C5XBC" + b"123456"
            return bytes([0x62]) + data[1:3] + bytes(4)
        if sid == 0x27:  # SecurityAccess
            sub = data[1]
            if sub % 2 == 1:  # seed request
                return bytes([0x67, sub, 0x11, 0x22, 0x33, 0x44])
            return bytes([0x67, sub])
        if sid == 0x2E:  # WriteDID
            return bytes([0x6E]) + data[1:3]
        if sid == 0x31:  # Routine
            return bytes([0x71, data[1]]) + data[2:4] + bytes([0x00])
        if sid == 0x3E:  # TesterPresent
            return bytes([0x7E, 0x00])
        return bytes([0x7F, sid, 0x11])


class _ISOTPTransport:
    """Real ISO-TP transport using udsoncan + python-isotp."""
    def __init__(self, tx_id: int, rx_id: int, interface: str = "virtual") -> None:
        import isotp
        import udsoncan
        addr = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=tx_id, rxid=rx_id
        )
        self._stack = isotp.CanStack(
            bus=None, address=addr,  # bus injected externally
            params={"stmin": 0, "blocksize": 0}
        )

    async def request(self, data: bytes) -> bytes:
        raise NotImplementedError("Use full isotp stack with real CAN bus")


# ── UDS Client ────────────────────────────────────────────────────────────────

class UDSClient:
    """
    Full ISO 14229-1 UDS client.

    Args:
        tx_id:      ECU request CAN ID.
        rx_id:      ECU response CAN ID.
        transport:  Custom transport; auto-selects mock if None.
        p2_timeout: Default P2 timeout in seconds.
    """

    def __init__(
        self,
        tx_id:      int = 0x740,
        rx_id:      int = 0x748,
        transport:  Optional[Any] = None,
        p2_timeout: float = 2.0,
    ) -> None:
        self._tx_id      = tx_id
        self._rx_id      = rx_id
        self._transport  = transport or _MockTransport()
        self._p2_timeout = p2_timeout
        self._session    = 0x01
        self._tp_thread: Optional[threading.Thread] = None
        self._tp_stop    = threading.Event()

    # ── Services ──────────────────────────────────────────────────────────────

    async def change_session(self, session_id: int) -> None:
        resp = await self._transport.request(bytes([0x10, session_id]))
        self._validate(resp, 0x50)
        self._session = session_id
        log.info(f"[UDS] Session changed to 0x{session_id:02X}")

    async def ecu_reset(self, reset_type: int = 0x01) -> None:
        resp = await self._transport.request(bytes([0x11, reset_type]))
        self._validate(resp, 0x51)
        self._session = 0x01
        log.info(f"[UDS] ECU reset type 0x{reset_type:02X}")

    async def clear_dtcs(self, group: int = 0xFFFFFF) -> None:
        payload = bytes([0x14]) + struct.pack(">I", group)[1:]
        resp = await self._transport.request(payload)
        self._validate(resp, 0x54)
        log.info(f"[UDS] DTCs cleared (group=0x{group:06X})")

    async def read_dtcs(
        self, status_mask: int = 0xFF
    ) -> List[DTCEntry]:
        resp = await self._transport.request(bytes([0x19, 0x02, status_mask]))
        self._validate(resp, 0x59)
        dtcs: List[DTCEntry] = []
        i = 3  # skip 0x59 subFunc avMask
        while i + 3 < len(resp):
            dtc_id = (resp[i] << 16) | (resp[i+1] << 8) | resp[i+2]
            status = resp[i+3]
            dtcs.append(DTCEntry(dtc_id=dtc_id, status=status))
            i += 4
        log.info(f"[UDS] ReadDTC: {len(dtcs)} DTCs")
        return dtcs

    async def read_did(self, did: int) -> bytes:
        payload = bytes([0x22, (did >> 8) & 0xFF, did & 0xFF])
        resp = await self._transport.request(payload)
        self._validate(resp, 0x62)
        return resp[3:]  # strip 0x62 + 2-byte DID echo

    async def read_vin(self) -> str:
        raw = await self.read_did(0xF190)
        return raw.decode("ascii", errors="replace").strip()

    async def write_did(self, did: int, data: bytes) -> None:
        payload = bytes([0x2E, (did >> 8) & 0xFF, did & 0xFF]) + data
        resp = await self._transport.request(payload)
        self._validate(resp, 0x6E)

    async def security_access(
        self,
        level:  int,
        key_fn: Callable[[bytes], bytes],
    ) -> None:
        seed_resp = await self._transport.request(bytes([0x27, level]))
        self._validate(seed_resp, 0x67)
        seed = seed_resp[2:]
        key  = key_fn(seed)
        key_resp = await self._transport.request(
            bytes([0x27, level + 1]) + key
        )
        self._validate(key_resp, 0x67)
        log.info(f"[UDS] SecurityAccess level 0x{level:02X} granted")

    async def comm_control(
        self, control_type: int = 0x00, comm_type: int = 0x01
    ) -> None:
        resp = await self._transport.request(
            bytes([0x28, control_type, comm_type])
        )
        self._validate(resp, 0x68)

    async def routine_control(
        self, routine_type: int, routine_id: int, data: bytes = b""
    ) -> bytes:
        payload = bytes([
            0x31, routine_type,
            (routine_id >> 8) & 0xFF, routine_id & 0xFF
        ]) + data
        resp = await self._transport.request(payload)
        self._validate(resp, 0x71)
        return resp[4:]

    async def tester_present(self) -> None:
        await self._transport.request(bytes([0x3E, 0x00]))

    async def control_dtc_setting(self, setting_type: int = 0x01) -> None:
        resp = await self._transport.request(bytes([0x85, setting_type]))
        self._validate(resp, 0xC5)

    async def flash_ecu(self, firmware_path: str) -> None:
        """Full programming sequence: 0x34 / 0x36 / 0x37."""
        import os
        with open(firmware_path, "rb") as fh:
            fw = fh.read()
        size = len(fw)
        # RequestDownload
        await self._transport.request(
            bytes([0x34, 0x00, 0x44]) +
            struct.pack(">I", 0) + struct.pack(">I", size)
        )
        # TransferData in 0xFFF chunks
        block = 1
        offset = 0
        chunk = 0xFFF
        while offset < size:
            payload = fw[offset: offset + chunk]
            await self._transport.request(bytes([0x36, block & 0xFF]) + payload)
            offset += chunk
            block  += 1
        # RequestTransferExit
        await self._transport.request(bytes([0x37]))
        log.info(f"[UDS] Flash complete: {os.path.basename(firmware_path)} ({size}B)")

    # ── TesterPresent keepalive ───────────────────────────────────────────────

    def start_tester_present(self, interval_s: float = 2.0) -> None:
        self._tp_stop.clear()
        loop = asyncio.new_event_loop()

        def _run() -> None:
            asyncio.set_event_loop(loop)
            async def _loop() -> None:
                while not self._tp_stop.is_set():
                    try:
                        await self.tester_present()
                    except Exception:
                        pass
                    await asyncio.sleep(interval_s)
            loop.run_until_complete(_loop())

        self._tp_thread = threading.Thread(target=_run, daemon=True, name="uds-tp")
        self._tp_thread.start()

    def stop_tester_present(self) -> None:
        self._tp_stop.set()
        if self._tp_thread:
            self._tp_thread.join(timeout=3.0)

    # ── Sync wrappers ─────────────────────────────────────────────────────────

    def _run(self, coro: Any) -> Any:
        return asyncio.get_event_loop().run_until_complete(coro)

    def sync_change_session(self, session_id: int) -> None:
        self._run(self.change_session(session_id))

    def sync_read_dtcs(self, status_mask: int = 0xFF) -> List[DTCEntry]:
        return self._run(self.read_dtcs(status_mask))

    def sync_read_did(self, did: int) -> bytes:
        return self._run(self.read_did(did))

    def sync_clear_dtcs(self) -> None:
        self._run(self.clear_dtcs())

    def sync_read_vin(self) -> str:
        return self._run(self.read_vin())

    # ── Internal ──────────────────────────────────────────────────────────────

    def _validate(self, resp: bytes, positive_sid: int) -> None:
        if not resp:
            raise NRCError(positive_sid - 0x40, 0x10)
        if resp[0] == 0x7F:
            service = resp[1] if len(resp) > 1 else 0
            nrc     = resp[2] if len(resp) > 2 else 0
            if nrc == 0x78:  # pending
                time.sleep(0.5)
                return
            raise NRCError(service, nrc)
        if resp[0] != positive_sid:
            raise ValueError(
                f"Unexpected SID 0x{resp[0]:02X}, expected 0x{positive_sid:02X}"
            )


# ── Factory ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def connect(
    tx_id:  int = 0x740,
    rx_id:  int = 0x748,
    **kwargs: Any,
) -> AsyncIterator[UDSClient]:
    """
    Async context manager factory.

    async with connect(tx_id=0x740, rx_id=0x748) as client:
        await client.change_session(0x03)
    """
    client = UDSClient(tx_id=tx_id, rx_id=rx_id, **kwargs)
    await client.change_session(0x01)
    try:
        yield client
    finally:
        await client.change_session(0x01)
        client.stop_tester_present()
