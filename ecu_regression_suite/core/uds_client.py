"""
UDS (ISO 14229-1) diagnostic client — hardware-agnostic with full mock support.

Two implementations share :class:`UDSClientBase`:

``MockUDSEngine``
    Generates plausible ECU responses from the DID/RID/session YAML matrices
    without any CAN traffic.  All log lines carry **[MOCK]**.  Tests can
    exercise both positive-path and negative-response paths in full CI
    pipelines with no hardware.

    [MOCK/SIMULATED — clearly flagged throughout]

``UDSClient`` (real)
    Routes requests through the supplied :class:`~core.isotp_transport.IsoTpConnectionBase`.

Factory
-------
::

    cfg    = UDSClientConfig(ecu_name="adas", mock=True, ...)
    client = build_uds_client(cfg, connection=None)
    client.connect()
    resp   = client.read_did(0xF190)
    assert resp.positive
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from .nrc_catalog import NRC_NAMES

if TYPE_CHECKING:
    from .isotp_transport import IsoTpConnectionBase


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ServiceID(IntEnum):
    """UDS service identifier bytes (ISO 14229-1, Table 3)."""
    DIAGNOSTIC_SESSION_CONTROL         = 0x10
    ECU_RESET                          = 0x11
    CLEAR_DTC_INFORMATION              = 0x14
    READ_DTC_INFORMATION               = 0x19
    READ_DATA_BY_IDENTIFIER            = 0x22
    SECURITY_ACCESS                    = 0x27
    COMMUNICATION_CONTROL              = 0x28
    WRITE_DATA_BY_IDENTIFIER           = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F
    ROUTINE_CONTROL                    = 0x31
    TESTER_PRESENT                     = 0x3E


class SessionType(IntEnum):
    """Diagnostic session sub-types (service 0x10)."""
    DEFAULT     = 0x01
    PROGRAMMING = 0x02
    EXTENDED    = 0x03


class ResetType(IntEnum):
    """ECU reset sub-types (service 0x11)."""
    HARD_RESET  = 0x01
    KEY_OFF_ON  = 0x02
    SOFT_RESET  = 0x03


_SESSION_NAMES: dict[int, str] = {1: "default", 2: "programming", 3: "extended"}
_NRC_SID: int = 0x7F


# ---------------------------------------------------------------------------
# Response data class
# ---------------------------------------------------------------------------

@dataclass
class UDSResponse:
    """Encapsulates a single UDS service response."""

    service_id: int
    positive: bool
    data: bytes                         # positive: response data; negative: raw 3-byte NRC frame
    nrc: Optional[int] = None           # set when positive=False
    elapsed_ms: float  = 0.0
    raw_request: bytes = field(default_factory=bytes)
    raw_response: bytes = field(default_factory=bytes)
    timestamp: float   = field(default_factory=time.time)

    @property
    def nrc_name(self) -> str:
        """Human-readable NRC name, or 'N/A' for positive responses."""
        if self.nrc is None:
            return "N/A"
        return NRC_NAMES.get(self.nrc, f"Unknown(0x{self.nrc:02X})")

    def __repr__(self) -> str:
        sid = f"0x{self.service_id:02X}"
        if self.positive:
            return f"UDSResponse(sid={sid} POSITIVE data={self.data.hex().upper()} {self.elapsed_ms:.1f}ms)"
        return f"UDSResponse(sid={sid} NEGATIVE nrc=0x{self.nrc:02X}({self.nrc_name}) {self.elapsed_ms:.1f}ms)"


class UDSNegativeResponseError(Exception):
    """Raised when an unexpected NRC is received."""

    def __init__(self, service_id: int, nrc: int) -> None:
        self.service_id = service_id
        self.nrc = nrc
        super().__init__(
            f"Service 0x{service_id:02X} returned NRC 0x{nrc:02X} "
            f"({NRC_NAMES.get(nrc, 'unknown')})"
        )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class UDSClientConfig:
    """Unified configuration for both mock and real UDS client."""

    ecu_name: str           = "unknown"
    mock: bool              = True
    p2_timeout_ms: int      = 150
    p2_star_timeout_ms: int = 5_000
    # Matrices loaded from YAML by conftest.py
    did_matrix: Dict[str, Any]      = field(default_factory=dict)
    rid_matrix: Dict[str, Any]      = field(default_factory=dict)
    sessions_config: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# UDS Client
# ---------------------------------------------------------------------------

class UDSClient:
    """
    High-level UDS service client.

    In ``mock=True`` mode every request is answered by :class:`MockUDSEngine`
    without touching any real transport.  In ``mock=False`` mode every request
    is serialised and sent over the provided ``connection``.
    """

    def __init__(
        self,
        config: UDSClientConfig,
        connection: Optional["IsoTpConnectionBase"] = None,
    ) -> None:
        self._cfg = config
        self._conn = connection
        self._session: int = SessionType.DEFAULT
        self._security_level: int = 0
        self._mock_engine: Optional[MockUDSEngine] = None
        if config.mock:
            self._mock_engine = MockUDSEngine(config)

    # -- Lifecycle -----------------------------------------------------------

    def connect(self) -> None:
        """Open the underlying transport channel."""
        if self._cfg.mock:
            logger.info("[MOCK] UDSClient connected (ecu={})", self._cfg.ecu_name)
        else:
            if self._conn is None:
                raise RuntimeError("A real IsoTpConnection must be supplied in hardware mode.")
            self._conn.open()
            logger.info("UDSClient connected (ecu={})", self._cfg.ecu_name)

    def disconnect(self) -> None:
        """Close the underlying transport channel."""
        if not self._cfg.mock and self._conn is not None:
            self._conn.close()

    def reset_session_state(self) -> None:
        """Reset tracked session / security state (call after ECU reset)."""
        self._session = SessionType.DEFAULT
        self._security_level = 0

    @property
    def current_session(self) -> int:
        return self._session

    @property
    def security_level(self) -> int:
        return self._security_level

    # -- UDS Services --------------------------------------------------------

    def change_session(self, session_type: int) -> UDSResponse:
        """DiagnosticSessionControl (0x10)."""
        resp = self._send(bytes([ServiceID.DIAGNOSTIC_SESSION_CONTROL, session_type]))
        if resp.positive:
            self._session = session_type
        return resp

    def ecu_reset(self, reset_type: int = ResetType.HARD_RESET) -> UDSResponse:
        """ECUReset (0x11)."""
        resp = self._send(bytes([ServiceID.ECU_RESET, reset_type]))
        if resp.positive:
            self.reset_session_state()
        return resp

    def clear_dtc(self, group_of_dtc: int = 0xFF_FF_FF) -> UDSResponse:
        """ClearDiagnosticInformation (0x14)."""
        payload = bytes([
            ServiceID.CLEAR_DTC_INFORMATION,
            (group_of_dtc >> 16) & 0xFF,
            (group_of_dtc >> 8)  & 0xFF,
            group_of_dtc         & 0xFF,
        ])
        return self._send(payload)

    def read_dtc_by_status_mask(self, status_mask: int = 0xFF) -> UDSResponse:
        """ReadDTCInformation (0x19 sub-function 0x02)."""
        return self._send(bytes([ServiceID.READ_DTC_INFORMATION, 0x02, status_mask]))

    def read_dtc_snapshot(self, dtc: int, record: int = 0xFF) -> UDSResponse:
        """ReadDTCInformation (0x19 sub-function 0x04) — snapshot data."""
        return self._send(bytes([
            ServiceID.READ_DTC_INFORMATION, 0x04,
            (dtc >> 16) & 0xFF, (dtc >> 8) & 0xFF, dtc & 0xFF,
            record,
        ]))

    def read_dtc_extended_data(self, dtc: int, record: int = 0xFF) -> UDSResponse:
        """ReadDTCInformation (0x19 sub-function 0x06) — extended data."""
        return self._send(bytes([
            ServiceID.READ_DTC_INFORMATION, 0x06,
            (dtc >> 16) & 0xFF, (dtc >> 8) & 0xFF, dtc & 0xFF,
            record,
        ]))

    def read_dtc_supported_dtc(self, status_mask: int = 0xFF) -> UDSResponse:
        """ReadDTCInformation (0x19 sub-function 0x0A) — supported DTC by status mask."""
        return self._send(bytes([ServiceID.READ_DTC_INFORMATION, 0x0A, status_mask]))

    def read_did(self, did: int) -> UDSResponse:
        """ReadDataByIdentifier (0x22) — single DID."""
        return self._send(bytes([
            ServiceID.READ_DATA_BY_IDENTIFIER,
            (did >> 8) & 0xFF,
            did & 0xFF,
        ]))

    def write_did(self, did: int, data: bytes) -> UDSResponse:
        """WriteDataByIdentifier (0x2E)."""
        return self._send(
            bytes([ServiceID.WRITE_DATA_BY_IDENTIFIER, (did >> 8) & 0xFF, did & 0xFF])
            + data
        )

    def io_control(
        self,
        did: int,
        control_param: int,
        control_state: bytes = b"",
    ) -> UDSResponse:
        """InputOutputControlByIdentifier (0x2F)."""
        return self._send(
            bytes([ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER,
                   (did >> 8) & 0xFF, did & 0xFF, control_param])
            + control_state
        )

    def start_routine(self, rid: int, option: bytes = b"") -> UDSResponse:
        """RoutineControl start (0x31 0x01)."""
        return self._send(
            bytes([ServiceID.ROUTINE_CONTROL, 0x01, (rid >> 8) & 0xFF, rid & 0xFF]) + option
        )

    def stop_routine(self, rid: int, option: bytes = b"") -> UDSResponse:
        """RoutineControl stop (0x31 0x02)."""
        return self._send(
            bytes([ServiceID.ROUTINE_CONTROL, 0x02, (rid >> 8) & 0xFF, rid & 0xFF]) + option
        )

    def request_routine_results(self, rid: int) -> UDSResponse:
        """RoutineControl request results (0x31 0x03)."""
        return self._send(
            bytes([ServiceID.ROUTINE_CONTROL, 0x03, (rid >> 8) & 0xFF, rid & 0xFF])
        )

    def request_seed(self, level: int) -> UDSResponse:
        """SecurityAccess seed request (0x27 odd sub-function)."""
        return self._send(bytes([ServiceID.SECURITY_ACCESS, level]))

    def send_key(self, level: int, key: bytes) -> UDSResponse:
        """SecurityAccess key send (0x27 even sub-function = level + 1)."""
        resp = self._send(bytes([ServiceID.SECURITY_ACCESS, level + 1]) + key)
        if resp.positive:
            self._security_level = level
        return resp

    def communication_control(self, ctrl_type: int, comm_type: int) -> UDSResponse:
        """CommunicationControl (0x28)."""
        return self._send(bytes([ServiceID.COMMUNICATION_CONTROL, ctrl_type, comm_type]))

    def tester_present(self, suppress_response: bool = False) -> UDSResponse:
        """TesterPresent (0x3E)."""
        sub_fn = 0x80 if suppress_response else 0x00
        return self._send(bytes([ServiceID.TESTER_PRESENT, sub_fn]))

    # -- Internal routing ----------------------------------------------------

    def _send(self, payload: bytes) -> UDSResponse:
        """Route to mock engine or real transport."""
        if self._cfg.mock:
            return self._mock_engine.process(payload, self._session, self._security_level)
        return self._send_real(payload)

    def _send_real(self, payload: bytes) -> UDSResponse:
        """Send over real ISO-TP transport and parse raw response."""
        assert self._conn is not None
        t0 = time.monotonic()
        try:
            raw = self._conn.send_and_recv(payload)
        except TimeoutError:
            return UDSResponse(
                service_id=payload[0],
                positive=False,
                data=b"",
                nrc=0x78,
                elapsed_ms=(time.monotonic() - t0) * 1000,
                raw_request=payload,
            )
        elapsed = (time.monotonic() - t0) * 1000

        if not raw:
            return UDSResponse(service_id=payload[0], positive=False, data=b"",
                               nrc=0x00, elapsed_ms=elapsed, raw_request=payload)

        if raw[0] == _NRC_SID:
            return UDSResponse(
                service_id=payload[0],
                positive=False,
                data=raw,
                nrc=raw[2] if len(raw) >= 3 else 0x00,
                elapsed_ms=elapsed,
                raw_request=payload,
                raw_response=raw,
            )
        return UDSResponse(
            service_id=payload[0],
            positive=True,
            data=raw[1:],   # strip positive-response SID byte
            elapsed_ms=elapsed,
            raw_request=payload,
            raw_response=raw,
        )

    def __enter__(self) -> "UDSClient":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()


# ---------------------------------------------------------------------------
# Mock ECU engine
# ---------------------------------------------------------------------------

class MockUDSEngine:
    """
    Simulated ECU UDS response generator.

    Generates realistic positive and negative responses from the DID/RID/session
    matrices loaded from YAML.  Tracks session state, security level, and
    security lockout counters internally.

    [MOCK/SIMULATED — no real ECU hardware required]
    """

    def __init__(self, config: UDSClientConfig) -> None:
        self._cfg = config
        self._did_map: Dict[int, Any] = {}
        self._rid_map: Dict[int, Any] = {}
        # Mock storage: simulates NVM-persisted DID values
        self._did_storage: Dict[int, bytes] = {}
        # Security state
        self._seed_val: int = 0xAB
        self._attempts: Dict[int, int] = {}
        self._locked_until: Dict[int, float] = {}
        self._build_indexes()

    def _build_indexes(self) -> None:
        for entry in self._cfg.did_matrix.get("dids", []):
            try:
                key = int(entry["id"], 16)
                self._did_map[key] = entry
            except (ValueError, KeyError):
                pass
        for entry in self._cfg.rid_matrix.get("routines", []):
            try:
                key = int(entry["id"], 16)
                self._rid_map[key] = entry
            except (ValueError, KeyError):
                pass

    def process(self, payload: bytes, session: int, sec_level: int) -> UDSResponse:
        """Dispatch a request payload to the correct service handler."""
        if not payload:
            return self._nrc(0x00, 0x13)

        sid = payload[0]
        t0 = time.monotonic()

        _handlers = {
            int(ServiceID.DIAGNOSTIC_SESSION_CONTROL):         self._svc_session_control,
            int(ServiceID.ECU_RESET):                          self._svc_ecu_reset,
            int(ServiceID.CLEAR_DTC_INFORMATION):              self._svc_clear_dtc,
            int(ServiceID.READ_DTC_INFORMATION):               self._svc_read_dtc,
            int(ServiceID.READ_DATA_BY_IDENTIFIER):            self._svc_read_did,
            int(ServiceID.SECURITY_ACCESS):                    self._svc_security_access,
            int(ServiceID.COMMUNICATION_CONTROL):              self._svc_comm_control,
            int(ServiceID.WRITE_DATA_BY_IDENTIFIER):           self._svc_write_did,
            int(ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER): self._svc_io_control,
            int(ServiceID.ROUTINE_CONTROL):                    self._svc_routine_control,
            int(ServiceID.TESTER_PRESENT):                     self._svc_tester_present,
        }

        handler = _handlers.get(sid)
        resp = handler(payload, session, sec_level) if handler else self._nrc(sid, 0x11)
        resp.elapsed_ms = (time.monotonic() - t0) * 1000
        resp.raw_request = payload
        logger.debug("[MOCK] {} → {}", payload.hex().upper(), resp)
        return resp

    # ------------------------------------------------------------------
    # Service handlers
    # ------------------------------------------------------------------

    def _svc_session_control(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 2:
            return self._nrc(0x10, 0x13)
        new_sess = p[1]
        sess_cfg = self._cfg.sessions_config.get("sessions", {})
        name = _SESSION_NAMES.get(new_sess)
        if not name or name not in sess_cfg:
            return self._nrc(0x10, 0x12)  # subFunctionNotSupported
        cfg = sess_cfg[name]
        p2 = cfg.get("p2_ms", 50)
        p2s = cfg.get("p2_star_ms", 5000)
        data = bytes([new_sess]) + p2.to_bytes(2, "big") + (p2s // 10).to_bytes(2, "big")
        return UDSResponse(service_id=0x10, positive=True, data=data)

    def _svc_ecu_reset(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 2 or p[1] not in (0x01, 0x02, 0x03):
            return self._nrc(0x11, 0x12)
        time.sleep(0.02)   # simulate minimal reset latency
        return UDSResponse(service_id=0x11, positive=True, data=bytes([p[1]]))

    def _svc_clear_dtc(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if sess == SessionType.DEFAULT:
            return self._nrc(0x14, 0x7F)
        return UDSResponse(service_id=0x14, positive=True, data=b"")

    def _svc_read_dtc(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 2:
            return self._nrc(0x19, 0x13)
        sub = p[1]
        if sub not in (0x02, 0x04, 0x06, 0x0A):
            return self._nrc(0x19, 0x12)
        # Mock: no DTCs stored — return empty list
        return UDSResponse(service_id=0x19, positive=True, data=bytes([sub]))

    def _svc_read_did(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 3:
            return self._nrc(0x22, 0x13)
        did = (p[1] << 8) | p[2]
        entry = self._did_map.get(did)
        if entry is None:
            return self._nrc(0x22, 0x31)

        sess_name = _SESSION_NAMES.get(sess, "default")
        if sess_name not in entry.get("sessions", ["default"]):
            return self._nrc(0x22, 0x31)

        req_sec = entry.get("security_level", 0)
        if sec < req_sec:
            return self._nrc(0x22, 0x33)

        # Return stored value first (if previously written), then mock_value
        if did in self._did_storage:
            raw = self._did_storage[did]
        else:
            raw = self._mock_raw_value(entry)

        return UDSResponse(service_id=0x22, positive=True, data=bytes([p[1], p[2]]) + raw)

    def _svc_write_did(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 3:
            return self._nrc(0x2E, 0x13)
        did = (p[1] << 8) | p[2]
        entry = self._did_map.get(did)
        if entry is None:
            return self._nrc(0x2E, 0x31)
        if not entry.get("writable", False):
            return self._nrc(0x2E, 0x31)

        sess_name = _SESSION_NAMES.get(sess, "default")
        if sess_name not in entry.get("sessions", ["default"]):
            return self._nrc(0x2E, 0x7F)

        req_sec = entry.get("security_level", 0)
        if sec < req_sec:
            return self._nrc(0x2E, 0x33)

        write_data = p[3:]
        expected_len = entry.get("length", 1)
        if len(write_data) != expected_len:
            return self._nrc(0x2E, 0x13)

        self._did_storage[did] = write_data   # persist mock write
        return UDSResponse(service_id=0x2E, positive=True, data=bytes([p[1], p[2]]))

    def _svc_io_control(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 4:
            return self._nrc(0x2F, 0x13)
        did = (p[1] << 8) | p[2]
        ctrl = p[3]
        entry = self._did_map.get(did)
        if entry is None or not entry.get("io_controllable", False):
            return self._nrc(0x2F, 0x31)
        if ctrl not in (0x00, 0x01, 0x02, 0x03):
            return self._nrc(0x2F, 0x31)
        return UDSResponse(service_id=0x2F, positive=True, data=bytes([p[1], p[2], ctrl]))

    def _svc_routine_control(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 4:
            return self._nrc(0x31, 0x13)
        sub  = p[1]
        rid  = (p[2] << 8) | p[3]
        entry = self._rid_map.get(rid)
        if entry is None:
            return self._nrc(0x31, 0x31)

        sess_name = _SESSION_NAMES.get(sess, "default")
        if sess_name not in entry.get("sessions", ["extended"]):
            return self._nrc(0x31, 0x7F)

        req_sec = entry.get("security_level", 0)
        if sec < req_sec:
            return self._nrc(0x31, 0x33)

        if sub == 0x01:   # start
            if not entry.get("supports_start", True):
                return self._nrc(0x31, 0x12)
            dur_ms = entry.get("expected_duration_ms", 50)
            time.sleep(min(dur_ms / 1000.0, 0.05))   # cap mock sleep at 50 ms
            result = bytes.fromhex(entry.get("mock_result", "0100"))
            return UDSResponse(service_id=0x31, positive=True,
                               data=bytes([sub, p[2], p[3]]) + result)
        elif sub == 0x02:  # stop
            if not entry.get("supports_stop", False):
                return self._nrc(0x31, 0x12)
            return UDSResponse(service_id=0x31, positive=True, data=bytes([sub, p[2], p[3]]))
        elif sub == 0x03:  # requestResults
            if not entry.get("supports_results", True):
                return self._nrc(0x31, 0x12)
            result = bytes.fromhex(entry.get("mock_result", "0100"))
            return UDSResponse(service_id=0x31, positive=True,
                               data=bytes([sub, p[2], p[3]]) + result)
        return self._nrc(0x31, 0x12)

    def _svc_security_access(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if len(p) < 2:
            return self._nrc(0x27, 0x13)
        sub_fn = p[1]
        level  = sub_fn if sub_fn % 2 == 1 else sub_fn - 1

        # Check time-delay lockout
        locked_until = self._locked_until.get(level, 0.0)
        if time.time() < locked_until:
            return self._nrc(0x27, 0x37)

        if sub_fn % 2 == 1:   # Odd = seed request
            self._seed_val = (self._seed_val + 1) & 0xFF
            seed = bytes([self._seed_val, self._seed_val ^ 0xFF])
            return UDSResponse(service_id=0x27, positive=True, data=bytes([sub_fn]) + seed)

        # Even = key send
        if len(p) < 4:
            return self._nrc(0x27, 0x13)
        received_key = p[2:]
        expected_key = bytes([self._seed_val ^ 0xFF, self._seed_val])  # XOR placeholder
        attempts = self._attempts.get(level, 0) + 1
        self._attempts[level] = attempts
        max_att = (
            self._cfg.sessions_config.get("security", {}).get("max_attempts", 3)
        )
        if received_key != expected_key:
            if attempts >= max_att:
                delay = self._cfg.sessions_config.get("security", {}).get("lockout_delay_s", 10)
                self._locked_until[level] = time.time() + delay
                self._attempts[level] = 0
                return self._nrc(0x27, 0x36)
            return self._nrc(0x27, 0x35)
        self._attempts[level] = 0
        return UDSResponse(service_id=0x27, positive=True, data=bytes([sub_fn]))

    def _svc_comm_control(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        if sess == SessionType.DEFAULT:
            return self._nrc(0x28, 0x7F)
        if len(p) < 3 or p[1] not in (0x00, 0x01, 0x02, 0x03):
            return self._nrc(0x28, 0x12 if len(p) >= 3 else 0x13)
        return UDSResponse(service_id=0x28, positive=True, data=bytes([p[1]]))

    def _svc_tester_present(self, p: bytes, sess: int, sec: int) -> UDSResponse:
        sub = p[1] if len(p) > 1 else 0x00
        if sub not in (0x00, 0x80):
            return self._nrc(0x3E, 0x12)
        return UDSResponse(service_id=0x3E, positive=True, data=bytes([sub & 0x7F]))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _nrc(service_id: int, nrc_code: int) -> UDSResponse:
        return UDSResponse(
            service_id=service_id,
            positive=False,
            data=bytes([_NRC_SID, service_id, nrc_code]),
            nrc=nrc_code,
        )

    @staticmethod
    def _mock_raw_value(entry: dict) -> bytes:
        """Convert ``mock_value`` field to raw bytes."""
        mock_val = entry.get("mock_value", "00")
        data_type = entry.get("data_type", "hex")
        length = entry.get("length", 1)
        try:
            if data_type == "ascii":
                return str(mock_val).encode("ascii")[:length].ljust(length, b"\x00")
            if isinstance(mock_val, int):
                return mock_val.to_bytes(length, "big")
            if isinstance(mock_val, str):
                cleaned = mock_val.replace(" ", "").replace("0x", "")
                return bytes.fromhex(cleaned)[:length].ljust(length, b"\x00")
        except Exception:  # noqa: BLE001
            pass
        return bytes(length)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_uds_client(
    config: UDSClientConfig,
    connection: Optional["IsoTpConnectionBase"] = None,
) -> UDSClient:
    """
    Build a :class:`UDSClient` with mock or real transport.

    Args:
        config:     Client configuration (includes loaded DID/RID matrices).
        connection: ISO-TP connection; ignored when ``config.mock=True``.
    """
    return UDSClient(config, connection)
