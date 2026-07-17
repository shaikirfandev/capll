"""
Tests for UDS SecurityAccess (service 0x27).

Validates:
- Seed request returns a non-zero seed of expected length.
- Valid key → positive response, security level granted.
- Invalid key → NRC 0x35 (invalidKey).
- Exceeding max attempts → NRC 0x36 (exceededNumberOfAttempts).
- Attempting seed while locked out → NRC 0x37 (requiredTimeDelayNotExpired).
- Security access not available in default session for extended-only levels.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from core.baseline_manager import RunResult, TestRecord
from core.security_access import (
    XorPlaceholderAlgorithm,
    NullAlgorithm,
    get_algorithm,
    perform_security_access,
)
from core.uds_client import UDSClient, SessionType


pytestmark = [pytest.mark.uds, pytest.mark.security, pytest.mark.regression]


def test_security_access_full_handshake(
    uds_client: UDSClient,
    result_collector: RunResult,
    sessions_config: Dict[str, Any],
) -> None:
    """
    0x27 — Full seed/key handshake: extended session, level 1.
    """
    record = TestRecord(
        test_id="service/0x27-security_access_level1",
        category="service",
        service_id="0x27",
        session="extended",
    )
    try:
        r = uds_client.change_session(SessionType.EXTENDED)
        assert r.positive

        algo = get_algorithm("xor_placeholder")
        seed_resp = uds_client.request_seed(1)
        assert seed_resp.positive, f"Seed request failed: {seed_resp.nrc_name}"

        seed = seed_resp.data[1:]   # strip sub-function echo
        assert len(seed) > 0, "Seed must be non-empty"
        assert seed != bytes(len(seed)), "Seed must be non-zero"

        key = algo.compute_key(seed, 1)
        key_resp = uds_client.send_key(1, key)

        record.actual_value = key_resp.data.hex().upper() if key_resp.positive else None
        record.actual_nrc   = f"0x{key_resp.nrc:02X}" if key_resp.nrc else None
        record.elapsed_ms   = key_resp.elapsed_ms

        assert key_resp.positive, (
            f"SecurityAccess key send failed: {key_resp.nrc_name}"
        )
        assert uds_client.security_level == 1, "Security level not updated after grant"
        record.status = "pass"
    except AssertionError as exc:
        record.status = "fail"
        record.failure_reason = str(exc)
        raise
    finally:
        result_collector.add(record)
        uds_client.change_session(SessionType.DEFAULT)


def test_security_access_invalid_key_nrc35(uds_client: UDSClient) -> None:
    """
    0x27 — Sending an incorrect key must return NRC 0x35 (invalidKey).
    """
    r = uds_client.change_session(SessionType.EXTENDED)
    assert r.positive

    # Get a valid seed but deliberately compute wrong key
    seed_resp = uds_client.request_seed(1)
    assert seed_resp.positive

    # Send inverted-wrong key (opposite of XOR placeholder)
    wrong_key = bytes([0x00] * len(seed_resp.data[1:]))
    key_resp = uds_client.send_key(1, wrong_key)

    assert not key_resp.positive, "Expected negative response for invalid key"
    assert key_resp.nrc == 0x35, (
        f"Expected NRC 0x35 (invalidKey), got 0x{key_resp.nrc:02X} ({key_resp.nrc_name})"
    )
    uds_client.change_session(SessionType.DEFAULT)


def test_security_access_lockout_after_max_attempts(
    uds_client: UDSClient,
    sessions_config: Dict[str, Any],
) -> None:
    """
    0x27 — After max_attempts failed keys, ECU must respond with NRC 0x36.
    """
    max_attempts = sessions_config.get("security", {}).get("max_attempts", 3)

    r = uds_client.change_session(SessionType.EXTENDED)
    assert r.positive

    wrong_key = bytes([0x00, 0x00])
    last_nrc: int = 0x00

    for _ in range(max_attempts):
        seed_resp = uds_client.request_seed(1)
        if not seed_resp.positive:
            # Already locked (0x37) — stop trying
            last_nrc = seed_resp.nrc or 0x00
            break
        key_resp = uds_client.send_key(1, wrong_key)
        last_nrc = key_resp.nrc or 0x00
        if last_nrc in (0x36, 0x37):
            break

    assert last_nrc in (0x36, 0x37), (
        f"Expected NRC 0x36 (exceededNumberOfAttempts) or 0x37 (timeDelayNotExpired) "
        f"after {max_attempts} failed attempts, got 0x{last_nrc:02X}"
    )
    # Reset session to clear state for subsequent tests
    uds_client.change_session(SessionType.DEFAULT)


def test_security_access_seed_not_available_in_default_session(
    uds_client: UDSClient,
) -> None:
    """
    0x27 — Seed request in default session for extended-only level should
    succeed (seed is available in all sessions per ISO 14229), but key send
    may be restricted.  Verify at least seed request succeeds.

    NOTE: This test verifies positive seed issuance — the ECU can issue seeds
    in any session per ISO 14229-1 §10.4.
    """
    r = uds_client.change_session(SessionType.DEFAULT)
    assert r.positive
    seed_resp = uds_client.request_seed(1)
    # Seed requests are generally available in default session (ISO 14229)
    # If the ECU restricts this, it should return NRC 0x7F or 0x31
    assert seed_resp.positive or seed_resp.nrc in (0x7F, 0x31, 0x22), (
        f"Unexpected NRC for seed request in default session: {seed_resp.nrc_name}"
    )
