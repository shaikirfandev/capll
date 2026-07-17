"""
UDS Diagnostic Client (ISO 14229-1) — Infotainment Edition.

Key additions over the generic UDS client:
  - ``UDSTransaction`` dataclass captures every request/response pair for the
    frame logger fixture.
  - ``MockUDSClient.transaction_log`` is populated on every service call.
  - ``MockUDSClient.inject_nrc()`` helper makes negative-response tests clean.

Services implemented:
  0x10 DiagnosticSessionControl
  0x11 ECUReset
  0x14 ClearDiagnosticInformation
  0x19 ReadDTCInformation (sub-fn 0x02 by status mask)
  0x22 ReadDataByIdentifier
  0x27 SecurityAccess (requestSeed + sendKey)
  0x28 CommunicationControl
  0x2E WriteDataByIdentifier
  0x2F InputOutputControlByIdentifier
  0x31 RoutineControl
  0x3E TesterPresent
"""
from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class ServiceID(IntEnum):
    DIAGNOSTIC_SESSION_CONTROL          = 0x10
    ECU_RESET                           = 0x11
    CLEAR_DTC_INFORMATION               = 0x14
    READ_DTC_INFORMATION                = 0x19
    READ_DATA_BY_IDENTIFIER             = 0x22
    WRITE_DATA_BY_IDENTIFIER            = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER  = 0x2F
    SECURITY_ACCESS                     = 0x27
    COMMUNICATION_CONTROL               = 0x28
    ROUTINE_CONTROL                     = 0x31
    TESTER_PRESENT                      = 0x3E


class SessionType(IntEnum):
    DEFAULT             = 0x01
    PROGRAMMING         = 0x02
    EXTENDED_DIAGNOSTIC = 0x03


class ResetType(IntEnum):
    HARD_RESET    = 0x01
    KEY_OFF_ON    = 0x02
    SOFT_RESET    = 0x03


class RoutineControlType(IntEnum):
    START          = 0x01
    STOP           = 0x02
    REQUEST_RESULT = 0x03


class CommControlType(IntEnum):
    ENABLE_RX_AND_TX    = 0x00
    ENABLE_RX_DISABLE_TX = 0x01
    DISABLE_RX_ENABLE_TX = 0x02
    DISABLE_RX_AND_TX   = 0x03


class NRC(IntEnum):
    """Negative Response Codes — ISO 14229-1, Annex A."""
    GENERAL_REJECT                              = 0x10
    SERVICE_NOT_SUPPORTED                       = 0x11
    SUB_FUNCTION_NOT_SUPPORTED                  = 0x12
    INCORRECT_MESSAGE_LENGTH                    = 0x13
    RESPONSE_TOO_LONG                           = 0x14
    BUSY_REPEAT_REQUEST                         = 0x21
    CONDITIONS_NOT_CORRECT                      = 0x22
    REQUEST_SEQUENCE_ERROR                      = 0x24
    FAILURE_PREVENTS_EXECUTION                  = 0x26
    REQUEST_OUT_OF_RANGE                        = 0x31
    SECURITY_ACCESS_DENIED                      = 0x33
    INVALID_KEY                                 = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS                 = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED             = 0x37
    GENERAL_PROGRAMMING_FAILURE                 = 0x72
    RESPONSE_PENDING                            = 0x78
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION     = 0x7F


# ---------------------------------------------------------------------------
# Response and transaction types
# ---------------------------------------------------------------------------
@dataclass
class UDSResponse:
    """Decoded result of a single UDS exchange."""
    service_id: int
    positive:   bool
    data:       bytes = b""
    nrc:        Optional[int] = None
    raw_bytes:  bytes = b""
    timestamp:  float = field(default_factory=time.time)

    @property
    def nrc_name(self) -> str:
        if self.nrc is None:
            return ""
        try:
            return NRC(self.nrc).name
        except ValueError:
            return f"0x{self.nrc:02X}"

    def __repr__(self) -> str:
        if self.positive:
            return f"<UDS SID=0x{self.service_id:02X} POSITIVE data={self.data.hex().upper()!r}>"
        return f"<UDS SID=0x{self.service_id:02X} NEGATIVE NRC={self.nrc_name}>"


@dataclass
class UDSTransaction:
    """A single UDS request/response pair — used by the frame logger."""
    service_name: str
    service_id:   int
    request_args: dict
    response:     UDSResponse
    timestamp:    float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "service":   self.service_name,
            "sid":       f"0x{self.service_id:02X}",
            "request":   self.request_args,
            "response":  repr(self.response),
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class UDSClientBase(ABC):
    """Interface shared by mock and real UDS clients."""

    def __init__(self) -> None:
        # Frame-logger hook: populated by concrete implementations
        self.transaction_log: list[UDSTransaction] = []

    def _record(self, name: str, sid: int, args: dict, resp: UDSResponse) -> None:
        self.transaction_log.append(UDSTransaction(name, sid, args, resp))

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def diagnostic_session_control(self, session: int) -> UDSResponse: ...

    @abstractmethod
    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse: ...

    @abstractmethod
    def security_access_request_seed(self, level: int) -> UDSResponse: ...

    @abstractmethod
    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse: ...

    @abstractmethod
    def read_data_by_identifier(self, did: int) -> UDSResponse: ...

    @abstractmethod
    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse: ...

    @abstractmethod
    def routine_control(self, ctrl: int, rid: int, data: bytes = b"") -> UDSResponse: ...

    @abstractmethod
    def read_dtc_by_status_mask(self, mask: int = 0xFF) -> UDSResponse: ...

    @abstractmethod
    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse: ...

    @abstractmethod
    def tester_present(self, suppress: bool = True) -> UDSResponse: ...

    @abstractmethod
    def communication_control(self, ctrl: int, comm_type: int) -> UDSResponse: ...

    @abstractmethod
    def io_control_by_identifier(self, did: int, option: bytes) -> UDSResponse: ...

    def __enter__(self) -> "UDSClientBase":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()


# ---------------------------------------------------------------------------
# Mock client
# ---------------------------------------------------------------------------
class MockUDSClient(UDSClientBase):
    """
    Fully self-contained mock UDS client.

    Behaviour
    ---------
    * Returns positive responses for every service by default.
    * ``inject_nrc(service_id, nrc)`` makes the *next* call to that service
      return the specified NRC, then reverts to default behaviour.
    * ``transaction_log`` records every call for the frame logger fixture.
    * All log lines carry **[MOCK]**.
    """

    def __init__(self) -> None:
        super().__init__()
        self._session   = SessionType.DEFAULT
        self._unlocked  = False
        self._connected = False
        # pending NRC stubs: {service_id: nrc_int}
        self._nrc_stubs: dict[int, int] = {}
        # pending full-response stubs: {service_id: UDSResponse}
        self._resp_stubs: dict[int, UDSResponse] = {}

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def inject_nrc(self, service_id: int, nrc: int) -> None:
        """Make the next call to *service_id* return a negative response."""
        self._nrc_stubs[service_id] = nrc

    def stub_response(self, service_id: int, response: UDSResponse) -> None:
        """Make the next call to *service_id* return *response* exactly."""
        self._resp_stubs[service_id] = response

    def _resolve(self, sid: int, default_data: bytes = b"") -> UDSResponse:
        """Return stub / NRC / default positive response and record it."""
        if sid in self._resp_stubs:
            resp = self._resp_stubs.pop(sid)
        elif sid in self._nrc_stubs:
            nrc = self._nrc_stubs.pop(sid)
            resp = UDSResponse(sid, positive=False, nrc=nrc)
        else:
            resp = UDSResponse(
                sid, positive=True, data=default_data,
                raw_bytes=bytes([sid + 0x40]) + default_data,
            )
        return resp

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def connect(self) -> None:
        self._connected = True
        logger.info("[MOCK] UDS client connected")

    def disconnect(self) -> None:
        self._connected = False
        logger.info("[MOCK] UDS client disconnected")

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    def diagnostic_session_control(self, session: int) -> UDSResponse:
        logger.info("[MOCK] DSC session=0x{:02X}", session)
        self._session = session
        resp = self._resolve(
            ServiceID.DIAGNOSTIC_SESSION_CONTROL,
            bytes([session, 0x00, 0x19, 0x01, 0xF4]),
        )
        self._record("DSC", ServiceID.DIAGNOSTIC_SESSION_CONTROL, {"session": session}, resp)
        return resp

    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        logger.info("[MOCK] ECUReset type=0x{:02X}", reset_type)
        self._session  = SessionType.DEFAULT
        self._unlocked = False
        resp = self._resolve(ServiceID.ECU_RESET, bytes([reset_type]))
        self._record("ECUReset", ServiceID.ECU_RESET, {"reset_type": reset_type}, resp)
        return resp

    def security_access_request_seed(self, level: int) -> UDSResponse:
        logger.info("[MOCK] SA RequestSeed level=0x{:02X}", level)
        resp = self._resolve(
            ServiceID.SECURITY_ACCESS,
            bytes([level, 0xDE, 0xAD, 0xBE, 0xEF]),
        )
        self._record("SA_RequestSeed", ServiceID.SECURITY_ACCESS, {"level": level}, resp)
        return resp

    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse:
        logger.info("[MOCK] SA SendKey level=0x{:02X} key={}", level, key.hex())
        self._unlocked = True
        resp = self._resolve(ServiceID.SECURITY_ACCESS, bytes([level + 1]))
        self._record("SA_SendKey", ServiceID.SECURITY_ACCESS, {"level": level, "key": key.hex()}, resp)
        return resp

    def read_data_by_identifier(self, did: int) -> UDSResponse:
        logger.info("[MOCK] RDBI DID=0x{:04X}", did)
        resp = self._resolve(
            ServiceID.READ_DATA_BY_IDENTIFIER,
            did.to_bytes(2, "big") + bytes([0x01, 0x23, 0x45, 0x67]),
        )
        self._record("RDBI", ServiceID.READ_DATA_BY_IDENTIFIER, {"did": f"0x{did:04X}"}, resp)
        return resp

    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse:
        logger.info("[MOCK] WDBI DID=0x{:04X} value={}", did, value.hex())
        resp = self._resolve(ServiceID.WRITE_DATA_BY_IDENTIFIER, did.to_bytes(2, "big"))
        self._record("WDBI", ServiceID.WRITE_DATA_BY_IDENTIFIER, {"did": f"0x{did:04X}", "value": value.hex()}, resp)
        return resp

    def routine_control(self, ctrl: int, rid: int, data: bytes = b"") -> UDSResponse:
        logger.info("[MOCK] RC ctrl=0x{:02X} routine=0x{:04X}", ctrl, rid)
        resp = self._resolve(
            ServiceID.ROUTINE_CONTROL,
            bytes([ctrl]) + rid.to_bytes(2, "big") + b"\x00",
        )
        self._record("RC", ServiceID.ROUTINE_CONTROL, {"ctrl": ctrl, "rid": f"0x{rid:04X}"}, resp)
        return resp

    def read_dtc_by_status_mask(self, mask: int = 0xFF) -> UDSResponse:
        logger.info("[MOCK] ReadDTC mask=0x{:02X}", mask)
        resp = self._resolve(ServiceID.READ_DTC_INFORMATION, bytes([0x02, 0xFF]))
        self._record("ReadDTC", ServiceID.READ_DTC_INFORMATION, {"mask": mask}, resp)
        return resp

    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse:
        logger.info("[MOCK] ClearDTC group=0x{:06X}", group)
        resp = self._resolve(ServiceID.CLEAR_DTC_INFORMATION, b"")
        self._record("ClearDTC", ServiceID.CLEAR_DTC_INFORMATION, {"group": f"0x{group:06X}"}, resp)
        return resp

    def tester_present(self, suppress: bool = True) -> UDSResponse:
        logger.debug("[MOCK] TesterPresent suppress={}", suppress)
        resp = self._resolve(ServiceID.TESTER_PRESENT, bytes([0x80 if suppress else 0x00]))
        self._record("TesterPresent", ServiceID.TESTER_PRESENT, {"suppress": suppress}, resp)
        return resp

    def communication_control(self, ctrl: int, comm_type: int) -> UDSResponse:
        logger.info("[MOCK] CommCtrl ctrl=0x{:02X} comm=0x{:02X}", ctrl, comm_type)
        resp = self._resolve(ServiceID.COMMUNICATION_CONTROL, bytes([ctrl]))
        self._record("CommCtrl", ServiceID.COMMUNICATION_CONTROL, {"ctrl": ctrl, "comm_type": comm_type}, resp)
        return resp

    def io_control_by_identifier(self, did: int, option: bytes) -> UDSResponse:
        logger.info("[MOCK] IOCtrl DID=0x{:04X} option={}", did, option.hex())
        resp = self._resolve(
            ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER,
            did.to_bytes(2, "big") + option,
        )
        self._record("IOCtrl", ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER, {"did": f"0x{did:04X}", "option": option.hex()}, resp)
        return resp


# ---------------------------------------------------------------------------
# Real udsoncan-backed client
# ---------------------------------------------------------------------------
class RealUDSClient(UDSClientBase):
    """UDS client via udsoncan over an IsoTpConnectionBase connection."""

    def __init__(self, connection: object, timeout: float = 2.0) -> None:
        super().__init__()
        self._conn    = connection
        self._timeout = timeout
        self._client  = None

    def connect(self) -> None:
        try:
            from udsoncan.client import Client  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("pip install udsoncan") from exc

        self._client = Client(self._conn, config={
            "exception_on_negative_response":   False,
            "exception_on_invalid_response":    False,
            "exception_on_unexpected_response": False,
            "p2_timeout":      self._timeout,
            "p2_star_timeout": self._timeout * 5,
        })
        self._client.open()
        logger.info("UDS client connected (udsoncan)")

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        logger.info("UDS client disconnected")

    def _w(self, resp: object, sid: int, name: str, args: dict) -> UDSResponse:
        pos  = bool(getattr(resp, "positive", False))
        nrc  = getattr(resp, "code", None) if not pos else None
        data = b""
        if pos:
            sd = getattr(resp, "service_data", None)
            try:
                data = bytes(sd) if sd is not None else b""
            except TypeError:
                pass
        raw = b""
        orig = getattr(resp, "original_payload", None)
        try:
            raw = bytes(orig) if orig is not None else b""
        except TypeError:
            pass
        r = UDSResponse(sid, pos, data, nrc, raw)
        self._record(name, sid, args, r)
        return r

    def diagnostic_session_control(self, session: int) -> UDSResponse:
        return self._w(self._client.change_session(session), ServiceID.DIAGNOSTIC_SESSION_CONTROL, "DSC", {"session": session})

    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        return self._w(self._client.ecu_reset(reset_type), ServiceID.ECU_RESET, "ECUReset", {"type": reset_type})

    def security_access_request_seed(self, level: int) -> UDSResponse:
        return self._w(self._client.request_seed(level), ServiceID.SECURITY_ACCESS, "SA_RequestSeed", {"level": level})

    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse:
        return self._w(self._client.send_key(level + 1, key), ServiceID.SECURITY_ACCESS, "SA_SendKey", {"level": level})

    def read_data_by_identifier(self, did: int) -> UDSResponse:
        return self._w(self._client.read_data_by_identifier(did), ServiceID.READ_DATA_BY_IDENTIFIER, "RDBI", {"did": f"0x{did:04X}"})

    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse:
        return self._w(self._client.write_data_by_identifier(did, value), ServiceID.WRITE_DATA_BY_IDENTIFIER, "WDBI", {"did": f"0x{did:04X}"})

    def routine_control(self, ctrl: int, rid: int, data: bytes = b"") -> UDSResponse:
        return self._w(self._client.routine_control(ctrl, rid, data), ServiceID.ROUTINE_CONTROL, "RC", {"rid": f"0x{rid:04X}"})

    def read_dtc_by_status_mask(self, mask: int = 0xFF) -> UDSResponse:
        return self._w(self._client.get_dtc_by_status_mask(mask), ServiceID.READ_DTC_INFORMATION, "ReadDTC", {"mask": mask})

    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse:
        return self._w(self._client.clear_dtc(group), ServiceID.CLEAR_DTC_INFORMATION, "ClearDTC", {"group": group})

    def tester_present(self, suppress: bool = True) -> UDSResponse:
        return self._w(self._client.tester_present(suppress), ServiceID.TESTER_PRESENT, "TesterPresent", {"suppress": suppress})

    def communication_control(self, ctrl: int, comm_type: int) -> UDSResponse:
        return self._w(self._client.communication_control(ctrl, comm_type), ServiceID.COMMUNICATION_CONTROL, "CommCtrl", {"ctrl": ctrl})

    def io_control_by_identifier(self, did: int, option: bytes) -> UDSResponse:
        return self._w(self._client.input_output_control_by_identifier(did, option), ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER, "IOCtrl", {"did": f"0x{did:04X}"})


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def build_uds_client(
    connection: Optional[object] = None,
    mock: bool = False,
) -> UDSClientBase:
    env_mock = os.environ.get("MOCK_HARDWARE", "1").lower() in ("1", "true", "yes")
    if mock or env_mock:
        logger.warning("[MOCK] UDS client in simulation mode — responses are SIMULATED")
        return MockUDSClient()
    if connection is None:
        raise ValueError("IsoTpConnectionBase required for RealUDSClient")
    return RealUDSClient(connection)
