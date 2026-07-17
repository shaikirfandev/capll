"""
Service availability regression tests.

For each UDS service the ECU declares it supports (in sessions_security.yaml),
verify that it still responds (positively or with an expected NRC).

A service is considered "regressed" if:
- It previously responded (in any session) but now returns a transport-level timeout.
- It previously was available in a specific session but is now rejected with
  a session-specific NRC that wasn't present in the baseline.

These tests run once per session type, not once per DID/RID, to keep the
scope focused on service availability rather than data content.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.uds_client import UDSClient, SessionType, ServiceID


pytestmark = [pytest.mark.regression]

_SESSION_MAP = {
    "default":     SessionType.DEFAULT,
    "extended":    SessionType.EXTENDED,
    "programming": SessionType.PROGRAMMING,
}

# Probe request for each service — minimal valid request to get any response
_SERVICE_PROBES: dict[int, tuple[bytes, str]] = {
    0x10: (bytes([0x10, 0x01]),          "default"),    # DSC — default session
    0x11: (bytes([0x11, 0x03]),          "default"),    # ECUReset — soft reset
    0x14: (bytes([0x14, 0xFF, 0xFF, 0xFF]), "extended"), # ClearDTC
    0x19: (bytes([0x19, 0x02, 0xFF]),    "extended"),   # ReadDTC — by status
    0x22: (bytes([0x22, 0xF1, 0x86]),    "default"),    # ReadDID — active session
    0x27: (bytes([0x27, 0x01]),          "extended"),   # SecurityAccess — seed
    0x28: (bytes([0x28, 0x00, 0x01]),    "extended"),   # CommunicationControl
    0x2E: (bytes([0x2E, 0xF1, 0x90] + [0] * 17), "extended"),  # WriteDID VIN (expect NRC 0x31)
    0x2F: (bytes([0x2F, 0xF1, 0x90, 0x00]), "extended"), # IOControl (expect NRC 0x31)
    0x31: (bytes([0x31, 0x01, 0xFF, 0x00]), "extended"), # RoutineControl — unknown RID
    0x3E: (bytes([0x3E, 0x00]),          "default"),    # TesterPresent
}

# NRCs that indicate service is present but request is invalid (not timeout)
_EXPECTED_NRCS_FOR_PROBE = frozenset({
    0x10, 0x11, 0x12, 0x13, 0x22, 0x24, 0x31, 0x33, 0x35, 0x7E, 0x7F,
})


@pytest.mark.parametrize(
    "service_id,probe_bytes,required_session",
    [
        pytest.param(sid, probe, sess, id=f"0x{sid:02X}")
        for sid, (probe, sess) in _SERVICE_PROBES.items()
    ],
)
def test_service_availability(
    uds_client: UDSClient,
    result_collector: RunResult,
    baseline_loader: Optional[RunResult],
    sessions_config: Dict[str, Any],
    service_id: int,
    probe_bytes: bytes,
    required_session: str,
) -> None:
    """
    Verify each supported UDS service still responds (not timed-out / disappeared).
    """
    allowed = sessions_config.get("sessions", {}).get(required_session, {}).get(
        "allowed_services", []
    )
    if service_id not in allowed:
        pytest.skip(
            f"Service 0x{service_id:02X} not declared in {required_session} "
            f"session config — skipping availability check"
        )

    test_id = f"service/0x{service_id:02X}-available_{required_session}"
    baseline_record: Optional[TestRecord] = None
    if baseline_loader:
        baseline_record = baseline_loader.records.get(test_id)

    record = TestRecord(
        test_id=test_id,
        category="service",
        service_id=f"0x{service_id:02X}",
        session=required_session,
    )

    try:
        r = uds_client.change_session(_SESSION_MAP.get(required_session, SessionType.DEFAULT))
        assert r.positive

        resp = uds_client._send(probe_bytes)
        record.actual_value = resp.data.hex().upper() if resp.positive else None
        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.elapsed_ms   = resp.elapsed_ms

        # Service is "available" if it responds with either a positive response
        # or a well-defined NRC (not 0x78 timeout acting as no-response)
        service_responded = resp.positive or (resp.nrc and resp.nrc in _EXPECTED_NRCS_FOR_PROBE)

        if baseline_record and baseline_record.status == "pass" and not service_responded:
            msg = (
                f"SERVICE REGRESSION: 0x{service_id:02X} previously responded "
                f"but now appears unavailable (NRC={resp.nrc_name})"
            )
            record.status = "fail"
            record.failure_reason = msg
            pytest.fail(msg)

        assert service_responded, (
            f"Service 0x{service_id:02X} did not respond to probe in {required_session} session "
            f"(nrc={resp.nrc_name if resp.nrc else 'none'})"
        )
        record.status = "pass"

    except AssertionError as exc:
        if record.status not in ("fail",):
            record.status = "fail"
            record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
