"""
Data-driven NRC coverage tests.

One test per entry in ``config/<ecu>/nrc_expected_matrix.yaml`` — generated
automatically via ``pytest_generate_tests``.

Each scenario:
1. Sets up the required session and security state.
2. Sends the triggering request.
3. Asserts that the received NRC matches ``expected_nrc`` from the YAML.
4. Records the result for baseline regression comparison.

Adding a new NRC scenario requires only a YAML change — no test code.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import get_algorithm, perform_security_access
from core.uds_client import UDSClient, ServiceID, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.regression]

# Map session name → SessionType int
_SESSION_MAP = {
    "default":     SessionType.DEFAULT,
    "extended":    SessionType.EXTENDED,
    "programming": SessionType.PROGRAMMING,
}

# -------------------------------------------------------------------
# NRC scenario trigger dispatcher
# -------------------------------------------------------------------

def _trigger_nrc_scenario(
    client: UDSClient,
    scenario: Dict[str, Any],
) -> "core.uds_client.UDSResponse":  # type: ignore[name-defined]
    """
    Execute the triggering action for a given NRC scenario.

    Returns the UDS response (expected to be a negative response).
    """
    action = scenario["trigger_action"]

    # ── Service Not Supported ──────────────────────────────────────────
    if action == "send_raw_service_0xBA":
        return client._send(bytes([0xBA, 0x00]))

    # ── SubFunction Not Supported ──────────────────────────────────────
    if action == "diagnostic_session_control_subfunction_0xAA":
        return client._send(bytes([int(ServiceID.DIAGNOSTIC_SESSION_CONTROL), 0xAA]))

    if action == "ecu_reset_type_0x05":
        return client._send(bytes([int(ServiceID.ECU_RESET), 0x05]))

    if action == "read_dtc_subfunction_0x99":
        return client._send(bytes([int(ServiceID.READ_DTC_INFORMATION), 0x99]))

    if action == "tester_present_subfunction_0x01":
        return client._send(bytes([int(ServiceID.TESTER_PRESENT), 0x01]))

    # ── Incorrect Message Length ───────────────────────────────────────
    if action == "send_0x22_with_only_1_byte":
        return client._send(bytes([int(ServiceID.READ_DATA_BY_IDENTIFIER)]))

    if action == "send_0x2E_with_wrong_data_length":
        # Write to 0xD003/0xE001 (length 1) but send wrong length (0 bytes data)
        did_byte1, did_byte2 = 0xD0, 0x03
        return client._send(bytes([int(ServiceID.WRITE_DATA_BY_IDENTIFIER), did_byte1, did_byte2]))

    if action == "send_0x31_with_only_2_bytes":
        return client._send(bytes([int(ServiceID.ROUTINE_CONTROL), 0x01]))

    # ── Request Out Of Range ───────────────────────────────────────────
    if action == "read_did_0xFFFF":
        return client.read_did(0xFFFF)

    if action == "write_did_0xF190_vin":
        return client.write_did(0xF190, bytes(17))

    if action == "start_routine_0xDEAD":
        return client.start_routine(0xDEAD)

    # ── Security Access Denied ─────────────────────────────────────────
    if action in (
        "read_did_0xD003_no_security",
        "read_did_0xE001_no_security",
    ):
        did = 0xD003 if "D003" in action else 0xE001
        return client.read_did(did)

    if action in (
        "write_did_0xD003_no_security",
        "write_did_0xE001_no_security",
    ):
        did = 0xD003 if "D003" in action else 0xE001
        return client.write_did(did, bytes(1))

    if action in (
        "start_routine_0x0202_no_security",
        "start_routine_0x0301_no_security",
    ):
        rid = 0x0202 if "0202" in action else 0x0301
        return client.start_routine(rid)

    # ── Security Key / Lockout ─────────────────────────────────────────
    if action == "send_wrong_key_after_valid_seed":
        seed_resp = client.request_seed(1)
        if not seed_resp.positive:
            return seed_resp  # propagate NRC
        return client.send_key(1, bytes([0x00, 0x00]))

    if action in ("send_wrong_key_3_times", "send_wrong_key_after_valid_seed_3_times"):
        # The mock engine keeps attempt count, so send the seed+key 3 times
        resp = None
        for _ in range(3):
            seed_resp = client.request_seed(1)
            if not seed_resp.positive:
                resp = seed_resp
                break
            resp = client.send_key(1, bytes([0x00, 0x00]))
            if resp.nrc in (0x36, 0x37):
                break
        return resp  # type: ignore[return-value]

    if action in (
        "attempt_seed_request_during_lockout",
        "attempt_seed_during_lockout",
    ):
        # First trigger a lockout, then attempt seed
        for _ in range(3):
            seed_resp = client.request_seed(1)
            if not seed_resp.positive:
                break
            client.send_key(1, bytes([0x00, 0x00]))
        return client.request_seed(1)

    # ── Session-restricted services ────────────────────────────────────
    if action in ("clear_dtc_in_default_session", "clear_dtc_default_session"):
        return client.clear_dtc(0xFF_FF_FF)

    if action in (
        "communication_control_in_default_session",
        "communication_control_default_session",
    ):
        return client.communication_control(0x00, 0x01)

    raise ValueError(f"Unknown trigger_action: '{action}'")


# -------------------------------------------------------------------
# Main parametrised test
# -------------------------------------------------------------------

def test_nrc_scenario(
    uds_client: UDSClient,
    result_collector: RunResult,
    nrc_scenario: Dict[str, Any],
) -> None:
    """
    NRC coverage — one test per scenario in ``nrc_expected_matrix.yaml``.

    Verifies that the ECU responds with exactly the expected NRC for
    each documented negative-response scenario.
    """
    scenario_name = nrc_scenario["scenario"]
    expected_nrc  = int(nrc_scenario["expected_nrc"], 16)
    setup_session = nrc_scenario.get("setup_session", "default")
    setup_security = int(nrc_scenario.get("setup_security", 0))

    record = TestRecord(
        test_id=f"nrc/{scenario_name}",
        category="nrc",
        service_id=nrc_scenario.get("service_id"),
        session=setup_session,
        nrc_code=nrc_scenario["expected_nrc"],
        extra={"expected_nrc": nrc_scenario["expected_nrc"]},
    )

    try:
        # -- Session setup ---------------------------------------------------
        r = uds_client.change_session(_SESSION_MAP.get(setup_session, SessionType.DEFAULT))
        assert r.positive, f"Could not enter {setup_session} session: {r.nrc_name}"

        # -- Security setup (only if explicitly required, and NOT for security-error tests) --
        is_security_test = "security" in scenario_name.lower() or "key" in scenario_name.lower()
        if setup_security > 0 and not is_security_test:
            algo = get_algorithm("xor_placeholder")
            perform_security_access(uds_client, level=setup_security, algorithm=algo)

        # -- Trigger & capture -----------------------------------------------
        resp = _trigger_nrc_scenario(uds_client, nrc_scenario)

        record.actual_nrc   = f"0x{resp.nrc:02X}" if resp.nrc else None
        record.actual_value = resp.data.hex().upper() if (resp.positive and resp.data) else None
        record.elapsed_ms   = resp.elapsed_ms

        assert not resp.positive, (
            f"Scenario '{scenario_name}': expected NRC 0x{expected_nrc:02X} "
            f"but got a POSITIVE response"
        )
        assert resp.nrc == expected_nrc, (
            f"Scenario '{scenario_name}': "
            f"expected NRC 0x{expected_nrc:02X} ({nrc_scenario.get('description', '')}), "
            f"got 0x{resp.nrc:02X} ({resp.nrc_name})"
        )
        record.status = "pass"

    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)
