from __future__ import annotations

from dataclasses import dataclass

from communication.uds_interface import MockUDSServer
from diagnostics.dtc import DTCRecord


class UDSNegativeResponse(Exception):
    pass


@dataclass(slots=True)
class UDSResponse:
    service_id: int
    payload: bytes


class UDSClient:
    """Synchronous mock UDS client supporting common diagnostic services."""

    def __init__(self, server: MockUDSServer) -> None:
        self.server = server

    def request(self, service_id: int, payload: bytes = b"") -> UDSResponse:
        raw = self.server.handle_request(bytes([service_id]) + payload)
        if raw[0] == 0x7F:
            raise UDSNegativeResponse(f"Negative response for 0x{service_id:02X}: NRC=0x{raw[2]:02X}")
        return UDSResponse(service_id=raw[0], payload=raw[1:])

    def diagnostic_session_control(self, session_type: int) -> int:
        return self.request(0x10, bytes([session_type])).payload[0]

    def clear_diagnostic_information(self, group: int = 0xFFFFFF) -> bool:
        self.request(0x14, group.to_bytes(3, "big"))
        return True

    def read_dtc_information(self, subfunction: int = 0x02, status_mask: int = 0xFF) -> list[DTCRecord]:
        response = self.request(0x19, bytes([subfunction, status_mask])).payload
        records: list[DTCRecord] = []
        for index in range(2, len(response), 4):
            chunk = response[index:index + 4]
            if len(chunk) < 4:
                continue
            code = int.from_bytes(chunk[:3], "big")
            status = chunk[3]
            record = self.server.dtc_manager.records.get(code)
            if record is not None:
                records.append(record)
            else:
                records.append(DTCRecord(code=code, status=status, description="unknown", freeze_frame={}))
        return records

    def read_data_by_identifier(self, did: int) -> bytes:
        return self.request(0x22, did.to_bytes(2, "big")).payload[2:]

    def security_access_request_seed(self, level: int) -> bytes:
        return self.request(0x27, bytes([level])).payload[1:]

    def security_access_send_key(self, level: int, key: bytes) -> bool:
        self.request(0x27, bytes([level]) + key)
        return True

    def write_data_by_identifier(self, did: int, data: bytes) -> bool:
        self.request(0x2E, did.to_bytes(2, "big") + data)
        return True

    def tester_present(self, suppress_response: bool = False) -> bool:
        self.request(0x3E, bytes([0x80 if suppress_response else 0x00]))
        return True

    def derive_key(self, seed: bytes) -> bytes:
        return bytes((byte ^ 0xA5) for byte in seed)
