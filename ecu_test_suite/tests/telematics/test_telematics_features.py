"""
Telematics ECU (TCU / TBOX) — domain-specific validation tests.

Covers:
  - DIDs: SIM/eSIM status, GPS fix status, modem firmware version
  - DTC checks: antenna faults, network registration failure, eCall module
  - Routine control: connectivity self-test, GPS cold start
  - Security access for remote command simulation

Markers: ``telematics``, ``smoke``, ``regression``, ``dtc``, ``security``, ``functional``
"""
from __future__ import annotations

import pytest

from core.uds_client import (
    NRC,
    ServiceID,
    SessionType,
    ResetType,
    RoutineControlType,
    UDSResponse,
    UDSClientBase,
    MockUDSClient,
)
from core.security_access import get_algorithm, perform_security_access
from core.dtc_manager import DTCManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_did(ecu_config: dict, name: str) -> int:
    did_str = ecu_config.get("dids", {}).get(name, {}).get("id", "0x0000")
    return int(did_str, 16) if isinstance(did_str, str) else int(did_str)


def _get_routine(ecu_config: dict, name: str) -> int:
    rid_str = ecu_config.get("routines", {}).get(name, {}).get("id", "0x0000")
    return int(rid_str, 16) if isinstance(rid_str, str) else int(rid_str)


# ===========================================================================
# 1. Read SIM ICCID DID
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.smoke
@pytest.mark.functional
def test_read_sim_iccid_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the SIM card ICCID DID and verify a payload is returned.

    Arrange: ECU in extended diagnostic session.
    Act:     RDBI sim_iccid DID.
    Assert:  Positive response; data ≥ 2 bytes (DID echo).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "sim_iccid")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"SIM ICCID DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "SIM ICCID response too short"


# ===========================================================================
# 2. Read eSIM status DID
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.smoke
@pytest.mark.functional
def test_read_esim_status_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the eSIM provisioning status DID.

    Arrange: ECU in extended session.
    Act:     RDBI esim_status DID.
    Assert:  Positive response; payload ≥ 2 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "esim_status")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"eSIM status DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "eSIM status response too short"


# ===========================================================================
# 3. Read GPS fix status DID
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.smoke
@pytest.mark.functional
def test_read_gps_fix_status_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the GPS fix status DID and verify the value is in range 0–3.

    Arrange: ECU in extended session.
    Act:     RDBI gps_fix_status DID.
    Assert:  Positive response; fix byte ∈ {0x00, 0x01, 0x02, 0x03}.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "gps_fix_status")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"GPS fix status DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    if len(response.data) >= 3:
        fix_byte = response.data[2]
        assert fix_byte in (0x00, 0x01, 0x02, 0x03), (
            f"GPS fix status 0x{fix_byte:02X} outside valid range [0x00, 0x03]"
        )


# ===========================================================================
# 4. Read modem firmware version DID
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.regression
@pytest.mark.functional
def test_read_modem_firmware_version_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the cellular modem firmware version DID.

    Arrange: ECU in extended session.
    Act:     RDBI modem_firmware_version DID.
    Assert:  Positive response; payload non-empty.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "modem_firmware_version")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Modem FW version DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "Modem FW version response too short"


# ===========================================================================
# 5. DTC check — GPS antenna fault absent on healthy TCU
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.dtc
@pytest.mark.smoke
def test_no_gps_antenna_fault_on_healthy_tcu(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify no GPS antenna open-circuit DTC on a healthy TCU.

    Arrange: Clear DTC memory.
    Act:     Read DTC snapshot.
    Assert:  DTC 0xB30001 (GPS antenna open circuit) is not confirmed.
    """
    GPS_ANTENNA_DTC = 0xB30001

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    antenna_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == GPS_ANTENNA_DTC]
    assert len(antenna_faults) == 0, (
        f"GPS antenna DTC 0x{GPS_ANTENNA_DTC:06X} unexpectedly confirmed"
    )


# ===========================================================================
# 6. Connectivity self-test routine
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.smoke
@pytest.mark.functional
def test_connectivity_self_test_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Execute the connectivity self-test routine (SIM + modem + network).

    Arrange: ECU in extended session, security unlocked.
    Act:     RoutineControl(startRoutine) connectivity_self_test.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "connectivity_self_test")
    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"Connectivity self-test routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 7. Security access for remote command simulation
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.security
@pytest.mark.regression
def test_security_access_remote_command_level(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Verify security access at the remote-command level succeeds.

    Arrange: ECU in extended session.
    Act:     perform_security_access at remote_command_level.
    Assert:  Security access granted.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    algo_name = ecu_config["security_access"].get(
        "remote_command_algorithm", "xor_placeholder"
    )
    level = int(ecu_config["security_access"].get("remote_command_level", 0x05))
    algo  = get_algorithm(algo_name)

    granted = perform_security_access(uds_client, level, algo)

    assert granted, (
        f"Remote command security access should be granted at level 0x{level:02X}"
    )


# ===========================================================================
# 8. eCall module fault DTC absent on healthy TCU
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.dtc
@pytest.mark.regression
def test_no_ecall_module_fault_dtc(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify eCall module self-test failure DTC is not confirmed.

    Arrange: Clear DTCs.
    Act:     Read DTC snapshot.
    Assert:  DTC 0xB34001 is not confirmed.
    """
    ECALL_DTC = 0xB34001

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    ecall_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == ECALL_DTC]
    assert len(ecall_faults) == 0, (
        f"eCall module DTC 0x{ECALL_DTC:06X} unexpectedly confirmed"
    )


# ===========================================================================
# 9. Network registration failure DTC absent
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.dtc
@pytest.mark.regression
def test_no_network_registration_failure_dtc(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify LTE network registration timeout DTC is not confirmed.

    Arrange: Clear DTCs.
    Act:     Read DTC snapshot.
    Assert:  DTC 0xB33001 (network registration timeout) is not confirmed.
    """
    NET_REG_DTC = 0xB33001

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    net_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == NET_REG_DTC]
    assert len(net_faults) == 0, (
        f"Network registration DTC 0x{NET_REG_DTC:06X} unexpectedly confirmed"
    )


# ===========================================================================
# 10. GPS cold start routine
# ===========================================================================
@pytest.mark.telematics
@pytest.mark.regression
@pytest.mark.functional
def test_gps_cold_start_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Trigger the GNSS module cold start routine.

    Arrange: ECU in extended session, security access granted.
    Act:     RoutineControl(startRoutine) gps_cold_start.
    Assert:  Positive response.

    .. note::
        On real hardware this clears the almanac and ephemeris data.
        Allow 60–120 s for the first GNSS fix after this routine.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "gps_cold_start")
    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"GPS cold start routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )
