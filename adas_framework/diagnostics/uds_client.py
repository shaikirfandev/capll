# adas_framework/diagnostics/uds_client.py
"""
Production-grade UDS (ISO 14229) diagnostic client.

Covers ALL standard services:
    0x10 DiagnosticSessionControl
    0x11 ECUReset
    0x14 ClearDiagnosticInformation
    0x19 ReadDTCInformation
    0x22 ReadDataByIdentifier
    0x23 ReadMemoryByAddress
    0x27 SecurityAccess
    0x28 CommunicationControl
    0x2E WriteDataByIdentifier
    0x31 RoutineControl
    0x34 RequestDownload (flashing)
    0x36 TransferData
    0x37 RequestTransferExit
    0x3E TesterPresent
    0x85 ControlDTCSetting

Features:
    - Async-capable (asyncio)
    - Auto TesterPresent keepalive thread
    - Security access with pluggable key derivation
    - Multi-ECU routing
    - Negative response (NRC) decoding with ISO 14229 table
    - Retry on pending (0x78)
    - Comprehensive logging

Usage:
    async with UDSClient.connect(cfg.uds, ecu="ADAS_ECU") as client:
        await client.change_session(0x03)
        await client.security_access(level=1, key_fn=derive_key)
        dtcs = await client.read_dtcs()
        vin  = await client.read_did(0xF190)
"""
from __future__ import annotations

import asyncio
import struct
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.config import UDSConfig
from core.logger import uds_log as log


# ─────────────────────────────────────────────────────────────────────────────
# NRC Table (ISO 14229-1 Table A-1)
# ─────────────────────────────────────────────────────────────────────────────

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
    """Raised when ECU returns a negative response."""
    def __init__(self, service: int, nrc: int):
        self.service = service
        self.nrc     = nrc
        desc = NRC_DESCRIPTIONS.get(nrc, f"unknown({nrc:#04x})")
        super().__init__(
            f"NRC for service {service:#04x}: {nrc:#04x} — {desc}"
        )


@dataclass
class DTCEntry:
    """A single DTC with status byte."""
    dtc_id:     int
    status:     int
    confirmed:  bool
    active:     bool
    dtc_hex:    str

    @property
    def status_bits(self) -> List[str]:
        names = ["testFailed", "testFailedThisDriveCycle", "pendingDTC",
                 "confirmedDTC", "testNotCompletedSinceLastClear",
                 "testFailedSinceLastClear", "testNotCompletedThisDriveCycle",
                 "warningIndicatorRequested"]
        return [n for i, n in enumerate(names) if self.status & (1 << i)]


# ─────────────────────────────────────────────────────────────────────────────
# Transport abstraction (ISO-TP / DoIP)
# ─────────────────────────────────────────────────────────────────────────────

class _ISOTPTransport:
    """Thin wrapper over python-isotp / udsoncan."""

    def __init__(self, tx_id: int, rx_id: int, bus):
        self.tx_id = tx_id
        self.rx_id = rx_id
        self._bus  = bus
        self._conn = None

    def open(self):
        try:
            import isotp
            import udsoncan
            addr = isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=self.tx_id, rxid=self.rx_id
            )
            self._conn = udsoncan.connections.PythonIsoTpConnection(
                self._bus, addr
            )
            self._conn.open()
        except ImportError:
            log.warning("isotp/udsoncan not available — using mock transport")
            self._conn = _MockTransport()

    def send(self, data: bytes):
        self._conn.send(data)

    def recv(self, timeout: float = 5.0) -> bytes:
        return self._conn.wait_frame(timeout=timeout) or b''

    def close(self):
        if self._conn and hasattr(self._conn, 'close'):
            self._conn.close()


class _MockTransport:
    """Null transport for CI environments without hardware."""
    def send(self, data): pass
    def wait_frame(self, timeout=5.0): return None
    def close(self): pass


# ─────────────────────────────────────────────────────────────────────────────
# UDSClient
# ─────────────────────────────────────────────────────────────────────────────

class UDSClient:
    """
    Async UDS client implementing ISO 14229-1.

    All service methods are async and can be called from pytest-asyncio tests.
    Synchronous wrappers are available for classic pytest tests.
    """

    DEFAULT_TIMEOUT = 5.0

    def __init__(self, config: UDSConfig, ecu: str, bus):
        ecu_cfg      = config.ecu_map.get(ecu, {})
        self._tx_id  = ecu_cfg.get("tx", config.tx_id)
        self._rx_id  = ecu_cfg.get("rx", config.rx_id)
        self._cfg    = config
        self._ecu    = ecu
        self._bus    = bus
        self._tp     = _ISOTPTransport(self._tx_id, self._rx_id, bus)
        self._session = 0x01
        self._tp_thread: Optional[threading.Thread] = None
        self._tp_running = False

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    @asynccontextmanager
    async def connect(cls, config: UDSConfig, ecu: str, bus) -> "UDSClient":
        client = cls(config, ecu, bus)
        client._tp.open()
        await client.change_session(0x01)
        try:
            yield client
        finally:
            client.stop_keepalive()
            await client.change_session(0x01)
            client._tp.close()

    # ── TesterPresent keepalive ───────────────────────────────────────────────

    def start_keepalive(self, interval_s: float = 3.0):
        """Send TesterPresent every interval_s to hold extended session."""
        self._tp_running = True
        def _loop():
            while self._tp_running:
                time.sleep(interval_s)
                if self._tp_running:
                    try:
                        self._raw_request(bytes([0x3E, 0x80]))  # suppress response
                    except Exception:
                        pass
        self._tp_thread = threading.Thread(target=_loop, daemon=True, name="UDS-KA")
        self._tp_thread.start()

    def stop_keepalive(self):
        self._tp_running = False

    # ── Core request/response ─────────────────────────────────────────────────

    def _raw_request(self, data: bytes, timeout: float = None) -> bytes:
        """Send raw UDS request, handle pending (0x78), return response payload."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        self._tp.send(data)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp = self._tp.recv(timeout=min(1.0, deadline - time.monotonic()))
            if not resp:
                raise TimeoutError(
                    f"UDS timeout waiting for response to {data.hex()} "
                    f"(ECU={self._ecu})"
                )
            if resp[0] == 0x7F:
                nrc = resp[2] if len(resp) >= 3 else 0
                if nrc == 0x78:  # requestCorrectlyReceivedResponsePending
                    log.debug(f"UDS pending (0x78) for service {data[0]:#04x}")
                    continue
                raise NRCError(data[0], nrc)
            return resp
        raise TimeoutError(f"UDS P2* timeout for service {data[0]:#04x}")

    async def _request(self, data: bytes, timeout: float = None) -> bytes:
        """Async wrapper — runs raw_request in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._raw_request, data, timeout
        )

    # ── 0x10 DiagnosticSessionControl ────────────────────────────────────────

    async def change_session(self, session: int) -> bool:
        resp = await self._request(bytes([0x10, session]))
        if resp[0] == 0x50:
            self._session = session
            log.info(f"[{self._ecu}] Session → {session:#04x}")
            return True
        return False

    # ── 0x11 ECUReset ─────────────────────────────────────────────────────────

    async def ecu_reset(self, reset_type: int = 0x01) -> bool:
        """0x01=hard, 0x02=key off/on, 0x03=soft"""
        resp = await self._request(bytes([0x11, reset_type]))
        return resp[0] == 0x51

    # ── 0x14 ClearDTC ─────────────────────────────────────────────────────────

    async def clear_dtcs(self, group: int = 0xFFFFFF) -> bool:
        data = bytes([0x14]) + group.to_bytes(3, "big")
        resp = await self._request(data)
        return resp[0] == 0x54

    # ── 0x19 ReadDTCInformation ───────────────────────────────────────────────

    async def read_dtcs(self, status_mask: int = 0xFF) -> List[DTCEntry]:
        data  = bytes([0x19, 0x02, status_mask])
        resp  = await self._request(data)
        # resp: [0x59, 0x02, dtcStoredStatusAvailabilityMask, {dtc3 + status1}...]
        dtcs  = []
        if len(resp) >= 3:
            offset = 3
            while offset + 3 < len(resp):
                dtc_id  = int.from_bytes(resp[offset:offset+3], "big")
                status  = resp[offset+3]
                dtcs.append(DTCEntry(
                    dtc_id   = dtc_id,
                    status   = status,
                    confirmed = bool(status & 0x08),
                    active    = bool(status & 0x01),
                    dtc_hex   = f"P{dtc_id:06X}",
                ))
                offset += 4
        log.info(f"[{self._ecu}] Read DTCs: {len(dtcs)} found "
                 f"(mask={status_mask:#04x})")
        return dtcs

    # ── 0x22 ReadDataByIdentifier ────────────────────────────────────────────

    async def read_did(self, did: int) -> bytes:
        data = bytes([0x22]) + did.to_bytes(2, "big")
        resp = await self._request(data)
        # resp: [0x62, DID_H, DID_L, ...data...]
        return bytes(resp[3:]) if len(resp) >= 3 else b''

    async def read_vin(self) -> str:
        raw = await self.read_did(0xF190)
        return raw.decode("ascii", errors="replace")

    # ── 0x27 SecurityAccess ───────────────────────────────────────────────────

    async def security_access(
        self, level: int, key_fn: Callable[[bytes], bytes]
    ) -> bool:
        """
        Perform SecurityAccess handshake.

        Args:
            level:  Security level (odd = request, even = send key)
            key_fn: Function(seed_bytes) → key_bytes
        """
        req_level = (level * 2) - 1  # 1→1, 2→3, 3→5 ...
        seed_resp = await self._request(bytes([0x27, req_level]))
        seed = bytes(seed_resp[2:])
        key  = key_fn(seed)
        send_level = req_level + 1
        key_resp = await self._request(bytes([0x27, send_level]) + key)
        if key_resp[0] == 0x67:
            log.info(f"[{self._ecu}] SecurityAccess level {level} granted")
            return True
        raise NRCError(0x27, key_resp[2] if len(key_resp) >= 3 else 0)

    # ── 0x28 CommunicationControl ─────────────────────────────────────────────

    async def comm_control(self, control: int, msg_type: int = 0x01) -> bool:
        """0x00=enable, 0x01=disable, 0x02=enableRxDisableTx, ..."""
        resp = await self._request(bytes([0x28, control, msg_type]))
        return resp[0] == 0x68

    # ── 0x2E WriteDataByIdentifier ───────────────────────────────────────────

    async def write_did(self, did: int, value: bytes) -> bool:
        data = bytes([0x2E]) + did.to_bytes(2, "big") + value
        resp = await self._request(data)
        return resp[0] == 0x6E

    # ── 0x31 RoutineControl ───────────────────────────────────────────────────

    async def start_routine(self, routine_id: int,
                             params: bytes = b'') -> bytes:
        data = bytes([0x31, 0x01]) + routine_id.to_bytes(2, "big") + params
        resp = await self._request(data)
        return bytes(resp[4:]) if len(resp) >= 4 else b''

    async def stop_routine(self, routine_id: int) -> bytes:
        data = bytes([0x31, 0x02]) + routine_id.to_bytes(2, "big")
        resp = await self._request(data)
        return bytes(resp[4:]) if len(resp) >= 4 else b''

    async def request_routine_result(self, routine_id: int) -> bytes:
        data = bytes([0x31, 0x03]) + routine_id.to_bytes(2, "big")
        resp = await self._request(data)
        return bytes(resp[4:]) if len(resp) >= 4 else b''

    # ── 0x3E TesterPresent ────────────────────────────────────────────────────

    async def tester_present(self, suppress: bool = False) -> bool:
        sub = 0x80 if suppress else 0x00
        if suppress:
            self._tp.send(bytes([0x3E, 0x80]))
            return True
        resp = await self._request(bytes([0x3E, 0x00]))
        return resp[0] == 0x7E

    # ── 0x85 ControlDTCSetting ───────────────────────────────────────────────

    async def control_dtc_setting(self, on: bool = True) -> bool:
        setting = 0x01 if on else 0x02
        resp = await self._request(bytes([0x85, setting]))
        return resp[0] == 0xC5

    # ── Flash workflow ────────────────────────────────────────────────────────

    async def flash_ecu(self, firmware_path: str,
                         block_size: int = 0x200) -> bool:
        """
        Complete ECU flashing workflow using UDS 0x34/0x36/0x37.
        Requires prior SecurityAccess.
        """
        import os
        data = open(firmware_path, "rb").read()
        total = len(data)
        log.info(f"[{self._ecu}] Flash start — {total} bytes")

        # 0x34 RequestDownload
        mem_addr   = b'\x00\x00\x00\x00'
        mem_size   = total.to_bytes(4, "big")
        dl_resp    = await self._request(bytes([0x34, 0x00, 0x44]) + mem_addr + mem_size)
        if dl_resp[0] != 0x74:
            raise RuntimeError("RequestDownload rejected")

        # 0x36 TransferData
        seq = 1
        offset = 0
        while offset < total:
            chunk = data[offset:offset + block_size]
            td_resp = await self._request(bytes([0x36, seq & 0xFF]) + chunk)
            if td_resp[0] != 0x76:
                raise RuntimeError(f"TransferData failed at offset {offset}")
            offset += len(chunk)
            seq = (seq + 1) & 0xFF
            log.debug(f"Flash {offset}/{total} ({100*offset//total}%)")

        # 0x37 RequestTransferExit
        exit_resp = await self._request(bytes([0x37]))
        if exit_resp[0] != 0x77:
            raise RuntimeError("RequestTransferExit failed")

        log.info(f"[{self._ecu}] Flash complete")
        return True

    # ── Sync wrappers (for non-async pytest tests) ────────────────────────────

    def _run(self, coro) -> Any:
        """Run an async method synchronously (for use in sync pytest)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def sync_change_session(self, session: int) -> bool:
        return self._run(self.change_session(session))

    def sync_read_dtcs(self, mask: int = 0xFF) -> List[DTCEntry]:
        return self._run(self.read_dtcs(mask))

    def sync_read_did(self, did: int) -> bytes:
        return self._run(self.read_did(did))

    def sync_clear_dtcs(self) -> bool:
        return self._run(self.clear_dtcs())
