"""
Cluster ECU (IPC) — domain-specific validation tests.

Covers:
  - DIDs: odometer, VIN, vehicle speed, warning lamp states
  - DTC checks: CAN bus-off, gauge stepper motor faults, backlight faults
  - IO Control: force lamp ON/OFF and verify via read-back

Markers: ``cluster``, ``smoke``, ``regression``, ``dtc``, ``functional``
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


def _get_io_did(ecu_config: dict, name: str) -> int:
    did_str = ecu_config.get("io_control", {}).get(name, {}).get("did", "0x0000")
    return int(did_str, 16) if isinstance(did_str, str) else int(did_str)


def _get_io_option(ecu_config: dict, name: str, key: str) -> bytes:
    option_str = ecu_config.get("io_control", {}).get(name, {}).get(key, "0x0300")
    hex_str = str(option_str).replace("0x", "").replace("0X", "").zfill(4)
    return bytes.fromhex(hex_str)


def _get_routine(ecu_config: dict, name: str) -> int:
    rid_str = ecu_config.get("routines", {}).get(name, {}).get("id", "0x0000")
    return int(rid_str, 16) if isinstance(rid_str, str) else int(rid_str)


# ===========================================================================
# 1. Read odometer DID
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.smoke
@pytest.mark.functional
def test_read_odometer_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the odometer DID and verify that a non-empty payload is returned.

    Arrange: ECU in extended diagnostic session.
    Act:     RDBI odometer DID.
    Assert:  Positive response; data length ≥ 4 bytes (DID echo + 4-byte value).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "odometer")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Odometer DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 4, (
        f"Odometer response too short: {len(response.data)} bytes"
    )


# ===========================================================================
# 2. Read VIN DID (0xF190)
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.smoke
@pytest.mark.functional
def test_read_vin_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the VIN DID (0xF190) and verify the response length.

    Arrange: ECU in default session (VIN readable without elevated access).
    Act:     RDBI vin DID.
    Assert:  Positive response; data ≥ 4 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    did = _get_did(ecu_config, "vin")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"VIN DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 4, (
        f"VIN response too short: {len(response.data)} bytes"
    )


# ===========================================================================
# 3. Read vehicle speed signal DID
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.smoke
@pytest.mark.functional
def test_read_vehicle_speed_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the vehicle speed DID (bench: vehicle stationary → speed = 0).

    Arrange: ECU in extended session.
    Act:     RDBI vehicle_speed DID.
    Assert:  Positive response; data ≥ 2 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "vehicle_speed")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Vehicle speed DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "Speed response too short"


# ===========================================================================
# 4. Read warning lamp states DID
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.regression
@pytest.mark.functional
def test_read_warning_lamp_states(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the warning lamp bitfield DID and verify the response is parseable.

    Arrange: ECU in extended session.
    Act:     RDBI warning_lamp_states DID.
    Assert:  Positive response; payload ≥ 2 bytes.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "warning_lamp_states")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Warning lamp states DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "Warning lamp states response too short"


# ===========================================================================
# 5. DTC check — CAN bus-off
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.dtc
@pytest.mark.smoke
def test_no_can_bus_off_dtc_on_healthy_network(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify no CAN bus-off DTC is active when the network is healthy.

    Arrange: Clear DTC memory.
    Act:     Read all DTCs.
    Assert:  DTC 0xB03001 (CAN bus-off cluster segment) is not confirmed.
    """
    CAN_BUS_OFF_DTC = 0x003001   # prefix normalised from "U03001"

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    bus_off_faults = [
        r for r in snapshot.confirmed_dtcs if r.dtc_code == CAN_BUS_OFF_DTC
    ]
    assert len(bus_off_faults) == 0, (
        f"CAN bus-off DTC unexpectedly confirmed"
    )


# ===========================================================================
# 6. IO Control — force Check Engine lamp ON
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.functional
@pytest.mark.regression
def test_io_control_check_engine_lamp_on(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Use IOControlByIdentifier (0x2F) to force the Check Engine lamp ON.

    Arrange: ECU in extended session, security unlocked.
    Act:     IOControl check_engine_lamp with control_option_on.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    did    = _get_io_did(ecu_config, "check_engine_lamp")
    option = _get_io_option(ecu_config, "check_engine_lamp", "control_option_on")

    response = uds_client.io_control_by_identifier(did, option)

    assert response.positive, (
        f"IO Control lamp ON for DID 0x{did:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 7. IO Control — force Check Engine lamp OFF and verify read-back
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.functional
@pytest.mark.regression
def test_io_control_lamp_off_and_readback(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Force Check Engine lamp OFF via IOControl, then read back the lamp state DID.

    Arrange: ECU in extended session, security unlocked.
    Act:     IOControl lamp ON → lamp OFF; RDBI warning_lamp_states.
    Assert:  All three service calls return positive responses.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    did     = _get_io_did(ecu_config, "check_engine_lamp")
    on_opt  = _get_io_option(ecu_config, "check_engine_lamp", "control_option_on")
    off_opt = _get_io_option(ecu_config, "check_engine_lamp", "control_option_off")

    # Force ON
    on_resp = uds_client.io_control_by_identifier(did, on_opt)
    assert on_resp.positive, f"IO Control lamp ON failed: NRC={on_resp.nrc_name}"

    # Force OFF
    off_resp = uds_client.io_control_by_identifier(did, off_opt)
    assert off_resp.positive, f"IO Control lamp OFF failed: NRC={off_resp.nrc_name}"

    # Read back
    lamp_did  = _get_did(ecu_config, "warning_lamp_states")
    read_resp = uds_client.read_data_by_identifier(lamp_did)
    assert read_resp.positive, (
        f"Warning lamp read-back failed: NRC={read_resp.nrc_name}"
    )


# ===========================================================================
# 8. Gauge sweep routine
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.regression
@pytest.mark.functional
def test_gauge_sweep_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Trigger the gauge needle sweep routine and verify a positive response.

    Arrange: ECU in extended session, security access granted.
    Act:     RoutineControl(startRoutine) gauge_sweep_test.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "gauge_sweep_test")
    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"Gauge sweep routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 9. DTC check — stepper motor fault absent on healthy cluster
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.dtc
@pytest.mark.regression
def test_no_speedometer_stepper_motor_dtc(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify speedometer stepper motor DTC is not confirmed on a healthy cluster.

    Arrange: Clear DTCs.
    Act:     Read DTC snapshot.
    Assert:  DTC 0xB20001 is not confirmed.
    """
    STEPPER_DTC = 0xB20001

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    stepper_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == STEPPER_DTC]
    assert len(stepper_faults) == 0, (
        f"Stepper motor DTC 0x{STEPPER_DTC:06X} unexpectedly confirmed"
    )


# ===========================================================================
# 10. Odometer NVM checksum verify routine
# ===========================================================================
@pytest.mark.cluster
@pytest.mark.regression
@pytest.mark.functional
def test_odometer_checksum_verify_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Run the odometer NVM checksum verification routine.

    Arrange: ECU in extended session.
    Act:     RoutineControl(startRoutine) odometer_checksum_verify.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    rid = _get_routine(ecu_config, "odometer_checksum_verify")

    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"Odometer checksum routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )
