"""
Infotainment ECU — domain-specific validation tests.

Covers:
  - HMI wake-up / sleep diagnostic session behaviour
  - Software version, Bluetooth / Wi-Fi module status DIDs
  - Routine control for factory reset and display self-test
  - DTC checks for display, audio, and USB faults

Markers: ``infotainment``, ``smoke``, ``regression``, ``dtc``, ``functional``
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
# 1. HMI wake-up via diagnostic session control
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.smoke
def test_hmi_wakeup_via_default_session(uds_client: UDSClientBase) -> None:
    """
    Verify the Infotainment ECU wakes and responds in default session.

    Arrange: No precondition (ECU may be in sleep/low-power state).
    Act:     Send DiagnosticSessionControl(defaultSession).
    Assert:  Positive response within P2 timeout.
    """
    response: UDSResponse = uds_client.diagnostic_session_control(SessionType.DEFAULT)

    assert response.positive, (
        f"Infotainment ECU should respond to default session; NRC={response.nrc_name}"
    )
    assert response.service_id == ServiceID.DIAGNOSTIC_SESSION_CONTROL


# ===========================================================================
# 2. Extended session for diagnostic access
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.smoke
def test_extended_session_entry(uds_client: UDSClientBase) -> None:
    """
    Verify the ECU enters extended diagnostic session.

    Arrange: ECU is in default session.
    Act:     Request extendedDiagnosticSession.
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    response = uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    assert response.positive, (
        f"extendedDiagnosticSession request failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 3. Read software version DID
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.smoke
@pytest.mark.functional
def test_read_software_version_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the Infotainment software version DID (0xF189) and validate length.

    Arrange: ECU in extended session.
    Act:     RDBI software_version DID.
    Assert:  Positive response; at least 2 bytes returned (DID echo + data).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "software_version")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Software version DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, (
        f"Software version response too short: {len(response.data)} bytes"
    )


# ===========================================================================
# 4. Read Bluetooth module status DID
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.regression
@pytest.mark.functional
def test_read_bluetooth_module_status(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the Bluetooth module status DID and verify response is positive.

    Arrange: ECU in extended session.
    Act:     RDBI bluetooth_status DID.
    Assert:  Positive response; data non-empty.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "bluetooth_status")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"BT status DID 0x{did:04X} failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "BT status response too short"


# ===========================================================================
# 5. Write Bluetooth module config DID
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.regression
@pytest.mark.functional
def test_write_bluetooth_module_config(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Write to the Bluetooth module DID to enable the BT module.

    Arrange: ECU in extended session with security access.
    Act:     WDBI bluetooth_status with enable value.
    Assert:  Positive response.
    """
    # Arrange
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    did = _get_did(ecu_config, "bluetooth_status")
    write_value_str = ecu_config["dids"]["bluetooth_status"].get("write_value", "0x0100")
    write_value = bytes.fromhex(write_value_str.replace("0x", "").zfill(4))

    # Act
    response = uds_client.write_data_by_identifier(did, write_value)

    # Assert
    assert response.positive, (
        f"WDBI BT status DID 0x{did:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 6. DTC check — display communication fault
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.dtc
@pytest.mark.regression
def test_no_display_communication_dtcs(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify no display-related DTCs are confirmed on a healthy ECU.

    Arrange: Clear DTC memory.
    Act:     Read all DTCs.
    Assert:  No confirmed DTCs with display communication codes.
    """
    DISPLAY_COMM_DTC = 0xB11001   # from infotainment_ecu.yaml dtc_map

    # Arrange
    uds_client.clear_dtc(group=0xFFFFFF)

    # Act
    snapshot = dtc_manager.read_all()

    # Assert
    display_faults = [
        r for r in snapshot.confirmed_dtcs
        if r.dtc_code == DISPLAY_COMM_DTC
    ]
    assert len(display_faults) == 0, (
        f"Unexpected display communication DTC confirmed: {display_faults}"
    )


# ===========================================================================
# 7. Factory reset routine
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.regression
@pytest.mark.functional
def test_factory_reset_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Trigger the factory reset routine and verify positive response.

    Arrange: ECU in programming session with security access (factory
             reset typically requires elevated privileges).
    Act:     RoutineControl(startRoutine) for factory_reset routine.
    Assert:  Positive response.

    .. warning::
        On real hardware this will RESET all HMI settings.
        Run only in a controlled test environment / bench.
    """
    uds_client.diagnostic_session_control(SessionType.PROGRAMMING)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "factory_reset")

    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"Factory reset routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 8. Display self-test routine
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.smoke
@pytest.mark.functional
def test_display_self_test_routine(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Activate the display pixel self-test routine.

    Arrange: ECU in extended session with security access.
    Act:     RoutineControl(startRoutine) for display_self_test.
    Assert:  Positive response with status byte 0x00.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo  = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "display_self_test")

    response = uds_client.routine_control(RoutineControlType.START, rid)

    assert response.positive, (
        f"Display self-test routine 0x{rid:04X} failed: NRC={response.nrc_name}"
    )


# ===========================================================================
# 9. HMI sleep state DID
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.functional
@pytest.mark.smoke
def test_hmi_sleep_state_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the HMI power/sleep state DID and verify it is within valid range.

    Arrange: ECU in default session (low-power check).
    Act:     RDBI hmi_sleep_state.
    Assert:  Positive response; state byte ∈ {0x00, 0x01, 0x02}.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    did = _get_did(ecu_config, "hmi_sleep_state")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"HMI sleep state DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    if len(response.data) >= 3:
        state = response.data[2]
        assert state in (0x00, 0x01, 0x02), (
            f"HMI sleep state 0x{state:02X} is outside valid range {{0x00, 0x01, 0x02}}"
        )


# ===========================================================================
# 10. USB/media fault DTC — clean ECU has no USB DTC
# ===========================================================================
@pytest.mark.infotainment
@pytest.mark.dtc
@pytest.mark.regression
def test_no_usb_media_dtcs_on_clean_ecu(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify no USB/media-related DTCs are present after DTC clear.

    Arrange: Clear DTC memory.
    Act:     Read all DTCs.
    Assert:  DTC 0xB14001 (USB port overcurrent) is not confirmed.
    """
    USB_OVERCURRENT_DTC = 0xB14001

    uds_client.clear_dtc(group=0xFFFFFF)
    snapshot = dtc_manager.read_all()

    usb_faults = [r for r in snapshot.confirmed_dtcs if r.dtc_code == USB_OVERCURRENT_DTC]
    assert len(usb_faults) == 0, (
        f"USB overcurrent DTC 0x{USB_OVERCURRENT_DTC:06X} unexpectedly confirmed"
    )
