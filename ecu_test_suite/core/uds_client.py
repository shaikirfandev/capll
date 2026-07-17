"""
UDS Diagnostic Client (ISO 14229-1).

This module exposes a hardware-agnostic ``UDSClientBase`` abstract class
and two concrete implementations:

``MockUDSClient``
    Fully in-process.  Returns plausible positive UDS responses for every
    service call.  Supports per-call response stubbing for negative-response
    tests.  All log lines carry the **[MOCK]** prefix.

``RealUDSClient``
    Wraps the *udsoncan* library over any :class:`~core.isotp_transport.IsoTpConnectionBase`
    connection.  Requires ``pip install udsoncan``.

Factory
-------
::

    client = build_uds_client(connection=conn, mock=False)
    client.connect()
    response = client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    assert response.positive
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
# UDS constants
# ---------------------------------------------------------------------------
class ServiceID(IntEnum):
    """UDS service identifier bytes (ISO 14229-1 Table 3)."""
    DIAGNOSTIC_SESSION_CONTROL          = 0x10
    ECU_RESET                           = 0x11
    SECURITY_ACCESS                     = 0x27
    COMMUNICATION_CONTROL               = 0x28
    TESTER_PRESENT                      = 0x3E
    READ_DTC_INFORMATION                = 0x19
    CLEAR_DTC_INFORMATION               = 0x14
    READ_DATA_BY_IDENTIFIER             = 0x22
    WRITE_DATA_BY_IDENTIFIER            = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER  = 0x2F
    ROUTINE_CONTROL                     = 0x31


class SessionType(IntEnum):
    """Diagnostic session sub-types (0x10 sub-function)."""
    DEFAULT             = 0x01
    PROGRAMMING         = 0x02
    EXTENDED_DIAGNOSTIC = 0x03


class ResetType(IntEnum):
    """ECU reset types (0x11 sub-function)."""
    HARD_RESET     = 0x01
    KEY_OFF_ON     = 0x02
    SOFT_RESET     = 0x03


class RoutineControlType(IntEnum):
    """Routine Control request types (0x31 sub-function)."""
    START  = 0x01
    STOP   = 0x02
    RESULT = 0x03


class CommControlType(IntEnum):
    """Communication Control types (0x28 sub-function)."""
    ENABLE_RX_AND_TX   = 0x00
    ENABLE_RX_DISABLE_TX = 0x01
    DISABLE_RX_ENABLE_TX = 0x02
    DISABLE_RX_AND_TX  = 0x03


class NRC(IntEnum):
    """Negative Response Codes (ISO 14229-1, Annex A)."""
    GENERAL_REJECT                                  = 0x10
    SERVICE_NOT_SUPPORTED                           = 0x11
    SUB_FUNCTION_NOT_SUPPORTED                      = 0x12
    INCORRECT_MESSAGE_LENGTH                        = 0x13
    RESPONSE_TOO_LONG                               = 0x14
    BUSY_REPEAT_REQUEST                             = 0x21
    CONDITIONS_NOT_CORRECT                          = 0x22
    REQUEST_SEQUENCE_ERROR                          = 0x24
    FAILURE_PREVENTS_EXECUTION                      = 0x26
    REQUEST_OUT_OF_RANGE                            = 0x31
    SECURITY_ACCESS_DENIED                          = 0x33
    INVALID_KEY                                     = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS                     = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED                 = 0x37
    GENERAL_PROGRAMMING_FAILURE                     = 0x72
    RESPONSE_PENDING                                = 0x78
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION         = 0x7F


# ---------------------------------------------------------------------------
# Response / exception types
# ---------------------------------------------------------------------------
@dataclass
class UDSResponse:
    """Decoded result of a single UDS service exchange."""

    service_id: int
    positive:   bool
    data:       bytes = b""
    nrc:        Optional[int] = None
    raw_bytes:  bytes = b""
    timestamp:  float = field(default_factory=time.time)

    @property
    def nrc_name(self) -> str:
        """Human-readable NRC name, or hex string if unknown."""
        if self.nrc is None:
            return ""
        try:
            return NRC(self.nrc).name
        except ValueError:
            return f"0x{self.nrc:02X}"

    def __repr__(self) -> str:
        if self.positive:
            return (
                f"<UDSResponse SID=0x{self.service_id:02X} POSITIVE "
                f"data={self.data.hex().upper()!r}>"
            )
        return (
            f"<UDSResponse SID=0x{self.service_id:02X} NEGATIVE "
            f"NRC={self.nrc_name}>"
        )


class UDSException(Exception):
    """Raised when a UDS service returns a negative response or times out."""

    def __init__(
        self,
        service_id: int,
        nrc: Optional[int] = None,
        message: str = "",
    ) -> None:
        self.service_id = service_id
        self.nrc = nrc
        nrc_str = f" NRC=0x{nrc:02X}" if nrc is not None else ""
        super().__init__(
            f"UDS SID=0x{service_id:02X}{nrc_str} — {message}"
        )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class UDSClientBase(ABC):
    """Common interface for real and mock UDS clients."""

    @abstractmethod
    def connect(self) -> None:
        """Initialise the underlying transport connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Tear down the transport connection."""

    @abstractmethod
    def diagnostic_session_control(self, session: int) -> UDSResponse:
        """Service 0x10 — change the active diagnostic session."""

    @abstractmethod
    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        """Service 0x11 — request an ECU reset."""

    @abstractmethod
    def security_access_request_seed(self, level: int) -> UDSResponse:
        """Service 0x27 — send the *requestSeed* sub-function."""

    @abstractmethod
    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse:
        """Service 0x27 — send the *sendKey* sub-function."""

    @abstractmethod
    def read_data_by_identifier(self, did: int) -> UDSResponse:
        """Service 0x22 — read a single DID."""

    @abstractmethod
    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse:
        """Service 0x2E — write a single DID."""

    @abstractmethod
    def routine_control(
        self,
        control_type: int,
        routine_id: int,
        data: bytes = b"",
    ) -> UDSResponse:
        """Service 0x31 — start/stop/request-results for a routine."""

    @abstractmethod
    def read_dtc_by_status_mask(self, status_mask: int = 0xFF) -> UDSResponse:
        """Service 0x19 sub-function 0x02 — read DTCs by status mask."""

    @abstractmethod
    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse:
        """Service 0x14 — clear DTC information for a group."""

    @abstractmethod
    def tester_present(self, suppress_response: bool = True) -> UDSResponse:
        """Service 0x3E — keep the current session alive."""

    @abstractmethod
    def communication_control(
        self, control_type: int, comm_type: int
    ) -> UDSResponse:
        """Service 0x28 — enable or disable specific message categories."""

    @abstractmethod
    def io_control_by_identifier(
        self, did: int, control_option: bytes
    ) -> UDSResponse:
        """Service 0x2F — override ECU output / input signals."""

    # Context manager support
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
    Self-contained mock UDS client.

    Returns plausible positive UDS responses without any hardware or library
    dependency.  Individual responses can be pre-stubbed via
    :meth:`stub_response` so that negative-response paths can be tested.

    All log messages carry the **[MOCK]** prefix.
    """

    def __init__(self) -> None:
        self._session: int = SessionType.DEFAULT
        self._security_unlocked: bool = False
        self._connected: bool = False
        # Map: service_id → UDSResponse to return on next matching call
        self._response_stubs: dict[int, UDSResponse] = {}

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------
    def stub_response(self, service_id: int, response: UDSResponse) -> None:
        """
        Pre-load a specific response for a service.

        The stub is consumed on the *next* call to that service and then
        removed.  Useful for testing negative-response paths::

            client.stub_response(
                ServiceID.READ_DATA_BY_IDENTIFIER,
                UDSResponse(ServiceID.READ_DATA_BY_IDENTIFIER, positive=False, nrc=NRC.REQUEST_OUT_OF_RANGE),
            )
        """
        self._response_stubs[service_id] = response

    def _resolve(self, service_id: int, default_data: bytes = b"") -> UDSResponse:
        """Return a stubbed response if available, otherwise a generic positive one."""
        if service_id in self._response_stubs:
            resp = self._response_stubs.pop(service_id)
            logger.debug("[MOCK] Returning stubbed response for SID=0x{:02X}", service_id)
            return resp
        return UDSResponse(
            service_id = service_id,
            positive   = True,
            data       = default_data,
            raw_bytes  = bytes([service_id + 0x40]) + default_data,
        )

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
    # Service implementations
    # ------------------------------------------------------------------
    def diagnostic_session_control(self, session: int) -> UDSResponse:
        logger.info("[MOCK] DiagnosticSessionControl  session=0x{:02X}", session)
        self._session = session
        # Response payload: session_type + P2=0x0019 + P2*=0x01F4
        return self._resolve(
            ServiceID.DIAGNOSTIC_SESSION_CONTROL,
            bytes([session, 0x00, 0x19, 0x01, 0xF4]),
        )

    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        logger.info("[MOCK] ECUReset  type=0x{:02X}", reset_type)
        self._session = SessionType.DEFAULT
        self._security_unlocked = False
        return self._resolve(
            ServiceID.ECU_RESET,
            bytes([reset_type]),
        )

    def security_access_request_seed(self, level: int) -> UDSResponse:
        logger.info("[MOCK] SecurityAccess RequestSeed  level=0x{:02X}", level)
        mock_seed = bytes([0xDE, 0xAD, 0xBE, 0xEF])
        return self._resolve(
            ServiceID.SECURITY_ACCESS,
            bytes([level]) + mock_seed,
        )

    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse:
        logger.info("[MOCK] SecurityAccess SendKey  level=0x{:02X}  key={}", level, key.hex())
        self._security_unlocked = True
        return self._resolve(
            ServiceID.SECURITY_ACCESS,
            bytes([level + 1]),
        )

    def read_data_by_identifier(self, did: int) -> UDSResponse:
        logger.info("[MOCK] RDBI  DID=0x{:04X}", did)
        did_bytes  = did.to_bytes(2, "big")
        mock_value = bytes([0x01, 0x23, 0x45, 0x67])
        return self._resolve(
            ServiceID.READ_DATA_BY_IDENTIFIER,
            did_bytes + mock_value,
        )

    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse:
        logger.info("[MOCK] WDBI  DID=0x{:04X}  value={}", did, value.hex())
        return self._resolve(
            ServiceID.WRITE_DATA_BY_IDENTIFIER,
            did.to_bytes(2, "big"),
        )

    def routine_control(
        self,
        control_type: int,
        routine_id: int,
        data: bytes = b"",
    ) -> UDSResponse:
        logger.info(
            "[MOCK] RoutineControl  ctrl=0x{:02X}  routine=0x{:04X}",
            control_type, routine_id,
        )
        return self._resolve(
            ServiceID.ROUTINE_CONTROL,
            bytes([control_type]) + routine_id.to_bytes(2, "big") + b"\x00",
        )

    def read_dtc_by_status_mask(self, status_mask: int = 0xFF) -> UDSResponse:
        logger.info("[MOCK] ReadDTCInformation  mask=0x{:02X}", status_mask)
        # sub_fn=0x02, availability_mask=0xFF, no DTC records (clean ECU)
        return self._resolve(
            ServiceID.READ_DTC_INFORMATION,
            bytes([0x02, 0xFF]),
        )

    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse:
        logger.info("[MOCK] ClearDTC  group=0x{:06X}", group)
        return self._resolve(ServiceID.CLEAR_DTC_INFORMATION, b"")

    def tester_present(self, suppress_response: bool = True) -> UDSResponse:
        logger.debug("[MOCK] TesterPresent  suppress={}", suppress_response)
        return self._resolve(
            ServiceID.TESTER_PRESENT,
            bytes([0x80 if suppress_response else 0x00]),
        )

    def communication_control(
        self, control_type: int, comm_type: int
    ) -> UDSResponse:
        logger.info(
            "[MOCK] CommunicationControl  ctrl=0x{:02X}  comm=0x{:02X}",
            control_type, comm_type,
        )
        return self._resolve(
            ServiceID.COMMUNICATION_CONTROL,
            bytes([control_type]),
        )

    def io_control_by_identifier(
        self, did: int, control_option: bytes
    ) -> UDSResponse:
        logger.info(
            "[MOCK] IOControlByIdentifier  DID=0x{:04X}  option={}",
            did, control_option.hex(),
        )
        return self._resolve(
            ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER,
            did.to_bytes(2, "big") + control_option,
        )


# ---------------------------------------------------------------------------
# Real client backed by udsoncan
# ---------------------------------------------------------------------------
class RealUDSClient(UDSClientBase):
    """
    UDS client backed by the *udsoncan* library.

    Args:
        connection: An open :class:`~core.isotp_transport.IsoTpConnectionBase` instance.
        timeout:    Default P2 timeout in seconds.
    """

    def __init__(self, connection: object, timeout: float = 2.0) -> None:
        self._connection = connection
        self._timeout    = timeout
        self._client     = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def connect(self) -> None:
        try:
            from udsoncan.client import Client  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "udsoncan not installed.  Run: pip install udsoncan"
            ) from exc

        cfg = {
            "exception_on_negative_response":   False,
            "exception_on_invalid_response":    False,
            "exception_on_unexpected_response": False,
            "p2_timeout":      self._timeout,
            "p2_star_timeout": self._timeout * 5,
            "security_algo":   None,
        }
        self._client = Client(self._connection, config=cfg)
        self._client.open()
        logger.info("UDS client connected (udsoncan)")

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        logger.info("UDS client disconnected")

    # ------------------------------------------------------------------
    # Response conversion helper
    # ------------------------------------------------------------------
    def _wrap(self, response: object, service_id: int) -> UDSResponse:
        """Convert a *udsoncan* response object to :class:`UDSResponse`."""
        positive = bool(getattr(response, "positive", False))
        nrc_code = None
        raw      = b""
        data     = b""

        if not positive:
            nrc_code = getattr(response, "code", None)
        else:
            svc_data = getattr(response, "service_data", None)
            if svc_data is not None:
                try:
                    data = bytes(svc_data)
                except TypeError:
                    data = b""

        orig = getattr(response, "original_payload", None)
        if orig is not None:
            try:
                raw = bytes(orig)
            except TypeError:
                raw = b""

        return UDSResponse(
            service_id = service_id,
            positive   = positive,
            data       = data,
            nrc        = nrc_code,
            raw_bytes  = raw,
        )

    # ------------------------------------------------------------------
    # Service methods
    # ------------------------------------------------------------------
    def diagnostic_session_control(self, session: int) -> UDSResponse:
        resp = self._client.change_session(session)
        logger.info("DSC  session=0x{:02X}  positive={}", session, resp.positive)
        return self._wrap(resp, ServiceID.DIAGNOSTIC_SESSION_CONTROL)

    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        resp = self._client.ecu_reset(reset_type)
        logger.info("ECUReset  type=0x{:02X}  positive={}", reset_type, resp.positive)
        return self._wrap(resp, ServiceID.ECU_RESET)

    def security_access_request_seed(self, level: int) -> UDSResponse:
        resp = self._client.request_seed(level)
        logger.info("SA RequestSeed  level=0x{:02X}  positive={}", level, resp.positive)
        return self._wrap(resp, ServiceID.SECURITY_ACCESS)

    def security_access_send_key(self, level: int, key: bytes) -> UDSResponse:
        resp = self._client.send_key(level + 1, key)
        logger.info("SA SendKey  level=0x{:02X}  positive={}", level + 1, resp.positive)
        return self._wrap(resp, ServiceID.SECURITY_ACCESS)

    def read_data_by_identifier(self, did: int) -> UDSResponse:
        resp = self._client.read_data_by_identifier(did)
        logger.info("RDBI  DID=0x{:04X}  positive={}", did, resp.positive)
        return self._wrap(resp, ServiceID.READ_DATA_BY_IDENTIFIER)

    def write_data_by_identifier(self, did: int, value: bytes) -> UDSResponse:
        resp = self._client.write_data_by_identifier(did, value)
        logger.info("WDBI  DID=0x{:04X}  positive={}", did, resp.positive)
        return self._wrap(resp, ServiceID.WRITE_DATA_BY_IDENTIFIER)

    def routine_control(
        self, control_type: int, routine_id: int, data: bytes = b""
    ) -> UDSResponse:
        resp = self._client.routine_control(control_type, routine_id, data)
        logger.info("RC  routine=0x{:04X}  positive={}", routine_id, resp.positive)
        return self._wrap(resp, ServiceID.ROUTINE_CONTROL)

    def read_dtc_by_status_mask(self, status_mask: int = 0xFF) -> UDSResponse:
        resp = self._client.get_dtc_by_status_mask(status_mask)
        logger.info("ReadDTC  mask=0x{:02X}  positive={}", status_mask, resp.positive)
        return self._wrap(resp, ServiceID.READ_DTC_INFORMATION)

    def clear_dtc(self, group: int = 0xFFFFFF) -> UDSResponse:
        resp = self._client.clear_dtc(group)
        logger.info("ClearDTC  group=0x{:06X}  positive={}", group, resp.positive)
        return self._wrap(resp, ServiceID.CLEAR_DTC_INFORMATION)

    def tester_present(self, suppress_response: bool = True) -> UDSResponse:
        resp = self._client.tester_present(suppress_response)
        logger.debug("TesterPresent  positive={}", resp.positive)
        return self._wrap(resp, ServiceID.TESTER_PRESENT)

    def communication_control(
        self, control_type: int, comm_type: int
    ) -> UDSResponse:
        resp = self._client.communication_control(control_type, comm_type)
        logger.info("CommCtrl  type=0x{:02X}  positive={}", control_type, resp.positive)
        return self._wrap(resp, ServiceID.COMMUNICATION_CONTROL)

    def io_control_by_identifier(
        self, did: int, control_option: bytes
    ) -> UDSResponse:
        resp = self._client.input_output_control_by_identifier(did, control_option)
        logger.info("IOCtrl  DID=0x{:04X}  positive={}", did, resp.positive)
        return self._wrap(resp, ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def build_uds_client(
    connection: Optional[object] = None,
    mock: bool = False,
) -> UDSClientBase:
    """
    Return a :class:`MockUDSClient` or :class:`RealUDSClient`.

    Mock mode is forced when ``MOCK_HARDWARE`` env var is truthy.
    """
    env_mock = os.environ.get("MOCK_HARDWARE", "0").lower() in ("1", "true", "yes")
    if mock or env_mock:
        logger.warning("[MOCK] UDS client operating in mock/simulation mode")
        return MockUDSClient()
    if connection is None:
        raise ValueError(
            "An open IsoTpConnectionBase instance is required for RealUDSClient"
        )
    return RealUDSClient(connection)
