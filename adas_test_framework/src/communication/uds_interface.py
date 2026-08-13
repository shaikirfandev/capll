from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from diagnostics.dtc import DTCManager


@dataclass(slots=True)
class MockECUState:
    session: int = 0x01
    unlocked_levels: set[int] = field(default_factory=set)
    did_store: Dict[int, bytes] = field(default_factory=lambda: {
        0xF190: b"TESTVIN1234567890",
        0xF187: b"ADAS-ECU-01",
    })
    pending_seed: Dict[int, bytes] = field(default_factory=dict)
    alive_counter: int = 0


class MockUDSServer:
    """In-memory UDS responder used by diagnostics and safety tests."""

    def __init__(self, dtc_manager: Optional[DTCManager] = None) -> None:
        self.state = MockECUState()
        self.dtc_manager = dtc_manager or DTCManager()

    def handle_request(self, request: bytes) -> bytes:
        service = request[0]
        if service == 0x10:
            self.state.session = request[1]
            return bytes([0x50, request[1], 0x00, 0x32, 0x01, 0xF4])
        if service == 0x14:
            self.dtc_manager.clear()
            return bytes([0x54]) + request[1:4]
        if service == 0x19:
            subfunction = request[1]
            records = self.dtc_manager.read_active(status_mask=request[2] if len(request) > 2 else 0xFF)
            payload = bytearray([0x59, subfunction, 0xFF])
            for record in records:
                payload.extend(record.code.to_bytes(3, "big"))
                payload.append(record.status)
            return bytes(payload)
        if service == 0x22:
            did = int.from_bytes(request[1:3], "big")
            data = self.state.did_store.get(did)
            if data is None:
                return bytes([0x7F, 0x22, 0x31])
            return bytes([0x62, request[1], request[2]]) + data
        if service == 0x27:
            level = request[1]
            if level % 2 == 1:
                seed = bytes([level, level ^ 0x5A, 0x12, 0x34])
                self.state.pending_seed[level + 1] = self._derive_key(seed)
                return bytes([0x67, level]) + seed
            expected = self.state.pending_seed.get(level)
            if expected is None or expected != request[2:]:
                return bytes([0x7F, 0x27, 0x35])
            self.state.unlocked_levels.add(level)
            return bytes([0x67, level])
        if service == 0x2E:
            did = int.from_bytes(request[1:3], "big")
            self.state.did_store[did] = request[3:]
            return bytes([0x6E, request[1], request[2]])
        if service == 0x3E:
            self.state.alive_counter += 1
            return bytes([0x7E, request[1] if len(request) > 1 else 0x00])
        if service == 0x11:
            self.state.session = 0x01
            return bytes([0x51, request[1]])
        return bytes([0x7F, service, 0x11])

    @staticmethod
    def _derive_key(seed: bytes) -> bytes:
        return bytes((byte ^ 0xA5) for byte in seed)
