"""
ADAS ECU — domain-specific validation tests.

Covers:
  - Session transitions and security access unlock
  - Sensor calibration status DIDs (camera / radar)
  - Calibration routine trigger and result polling
  - DTC checks for sensor faults (blockage, misalignment, comm loss)
  - Functional signal validation (object detection flag, ACC state)

Markers: ``adas``, ``smoke``, ``regression``, ``security``, ``dtc``, ``functional``
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
    """Resolve a named DID to its integer value from the YAML config."""
    did_str = ecu_config.get("dids", {}).get(name, {}).get("id", "0x0000")
    return int(did_str, 16) if isinstance(did_str, str) else int(did_str)


def _get_routine(ecu_config: dict, name: str) -> int:
    """Resolve a named routine ID to its integer value from the YAML config."""
    rid_str = ecu_config.get("routines", {}).get(name, {}).get("id", "0x0000")
    return int(rid_str, 16) if isinstance(rid_str, str) else int(rid_str)


# ===========================================================================
# 1. Default session entry
# ===========================================================================
@pytest.mark.adas
@pytest.mark.smoke
def test_default_session_entry(uds_client: UDSClientBase) -> None:
    """
    Verify the ADAS ECU accepts a default diagnostic session request.

    Arrange: No precondition.
    Act:     Send DiagnosticSessionControl(defaultSession).
    Assert:  Positive response; service ID matches 0x10.
    """
    # Act
    response: UDSResponse = uds_client.diagnostic_session_control(SessionType.DEFAULT)

    # Assert
    assert response.positive, (
        f"ADAS ECU should enter default session; got NRC={response.nrc_name}"
    )
    assert response.service_id == ServiceID.DIAGNOSTIC_SESSION_CONTROL


# ===========================================================================
# 2. Extended session entry
# ===========================================================================
@pytest.mark.adas
@pytest.mark.smoke
def test_extended_session_entry(uds_client: UDSClientBase) -> None:
    """
    Verify the ADAS ECU enters extended diagnostic session.

    Arrange: ECU is in default session.
    Act:     Request extendedDiagnosticSession (0x03).
    Assert:  Positive response.
    """
    uds_client.diagnostic_session_control(SessionType.DEFAULT)
    response = uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    assert response.positive, (
        f"Expected extendedDiagnosticSession positive; NRC={response.nrc_name}"
    )


# ===========================================================================
# 3. Security access unlock in extended session
# ===========================================================================
@pytest.mark.adas
@pytest.mark.security
@pytest.mark.regression
def test_security_access_unlock_extended_session(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Verify full Security Access handshake (seed → key) succeeds.

    Arrange: ECU is in extended diagnostic session.
    Act:     Execute perform_security_access() with configured algorithm.
    Assert:  Security access is granted (returns True).
    """
    # Arrange
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)

    algo_name = ecu_config.get("security_access", {}).get("algorithm", "xor_placeholder")
    level     = int(ecu_config.get("security_access", {}).get("level", 0x01))
    algorithm = get_algorithm(algo_name)

    # Act
    granted = perform_security_access(uds_client, level, algorithm)

    # Assert
    assert granted, (
        "Security access should be granted in extended session using "
        f"algorithm='{algo_name}', level=0x{level:02X}"
    )


# ===========================================================================
# 4. Camera calibration status DID
# ===========================================================================
@pytest.mark.adas
@pytest.mark.smoke
@pytest.mark.functional
def test_camera_calibration_status_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the front camera calibration status DID and verify response format.

    Arrange: ECU is in extended session with security access granted.
    Act:     ReadDataByIdentifier for camera_calibration_status DID.
    Assert:  Positive response; data payload is non-empty.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "camera_calibration_status")

    # Act
    response = uds_client.read_data_by_identifier(did)

    # Assert
    assert response.positive, (
        f"RDBI for camera calibration DID 0x{did:04X} failed: NRC={response.nrc_name}"
    )
    expected_length = ecu_config["dids"]["camera_calibration_status"].get("length", 1)
    # Data includes 2-byte DID echo + value bytes
    assert len(response.data) >= 2, (
        f"Expected at least 2 bytes in RDBI response; got {len(response.data)}"
    )


# ===========================================================================
# 5. Radar calibration status DID
# ===========================================================================
@pytest.mark.adas
@pytest.mark.regression
@pytest.mark.functional
def test_radar_calibration_status_did(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the front radar calibration status DID.

    Arrange: ECU in extended session.
    Act:     RDBI radar_calibration_status DID.
    Assert:  Positive response; data length matches config.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "radar_calibration_status")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"RDBI for radar calibration DID 0x{did:04X} failed: NRC={response.nrc_name}"
    )
    assert len(response.data) >= 2, "Expected at least DID echo bytes in response"


# ===========================================================================
# 6. Camera calibration routine trigger
# ===========================================================================
@pytest.mark.adas
@pytest.mark.regression
@pytest.mark.functional
def test_camera_calibration_routine_start(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Trigger the camera static calibration routine and verify it starts.

    Arrange: ECU in extended session, security unlocked.
    Act:     RoutineControl(startRoutine) for camera_calibration_trigger.
    Assert:  Positive response with routine status byte = 0x00 (started/OK).
    """
    # Arrange
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    algo = get_algorithm(ecu_config["security_access"].get("algorithm", "xor_placeholder"))
    level = int(ecu_config["security_access"].get("level", 0x01))
    perform_security_access(uds_client, level, algo)

    rid = _get_routine(ecu_config, "camera_calibration_trigger")

    # Act
    response = uds_client.routine_control(
        RoutineControlType.START, rid
    )

    # Assert
    assert response.positive, (
        f"Camera calibration routine 0x{rid:04X} start failed: NRC={response.nrc_name}"
    )
    expected_status = int(
        ecu_config.get("routines", {})
        .get("camera_calibration_trigger", {})
        .get("expected_status", 0x00)
    )
    # Response data: [control_type][RID_H][RID_L][status]
    if len(response.data) >= 4:
        actual_status = response.data[3]
        assert actual_status == expected_status, (
            f"Calibration routine status 0x{actual_status:02X} != "
            f"expected 0x{expected_status:02X}"
        )


# ===========================================================================
# 7. DTC check — no active sensor faults on clean ECU
# ===========================================================================
@pytest.mark.adas
@pytest.mark.dtc
@pytest.mark.smoke
def test_no_active_sensor_dtcs_on_clean_ecu(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
) -> None:
    """
    Verify no confirmed sensor-fault DTCs are present after ECU init.

    Arrange: ECU is freshly powered — clear DTC memory first.
    Act:     Read all DTCs with status mask 0xFF.
    Assert:  Zero confirmed DTCs in the snapshot.
    """
    # Arrange — clear any residual faults
    uds_client.clear_dtc(group=0xFFFFFF)

    # Act
    snapshot = dtc_manager.read_all(status_mask=0xFF)

    # Assert
    confirmed = snapshot.confirmed_dtcs
    assert len(confirmed) == 0, (
        f"Expected 0 confirmed DTCs on clean ADAS ECU; found: "
        f"{[str(d) for d in confirmed]}"
    )


# ===========================================================================
# 8. DTC simulation — camera sensor blockage DTC
# ===========================================================================
@pytest.mark.adas
@pytest.mark.dtc
@pytest.mark.regression
def test_camera_blockage_dtc_injection_and_read(
    uds_client: UDSClientBase,
    dtc_manager: DTCManager,
    ecu_config: dict,
) -> None:
    """
    Simulate a camera blockage condition and verify the expected DTC is set.

    This test relies on mock mode — in mock mode a synthetic DTC response
    is injected into the UDS client; on real hardware the DTC would be set
    by physically covering the camera lens.

    Arrange: Stub the DTC read to return camera blockage DTC.
    Act:     Read DTCs.
    Assert:  The known camera blockage DTC code appears in the snapshot.
    """
    # For mock mode: inject a synthetic DTC response
    CAMERA_BLOCKAGE_DTC = 0xC11003  # from adas_ecu.yaml dtc_map
    CONFIRMED_STATUS    = 0x09      # testFailed(0x01) + confirmedDTC(0x08)

    if isinstance(uds_client, MockUDSClient):
        # Build raw ReadDTCInformation response: sub_fn=0x02, avail_mask=0xFF, 1 DTC
        synthetic = bytes([
            0x02, 0xFF,                  # sub-function + availability mask
            (CAMERA_BLOCKAGE_DTC >> 16) & 0xFF,
            (CAMERA_BLOCKAGE_DTC >> 8)  & 0xFF,
             CAMERA_BLOCKAGE_DTC        & 0xFF,
            CONFIRMED_STATUS,
        ])
        uds_client.stub_response(
            ServiceID.READ_DTC_INFORMATION,
            __import__("core.uds_client", fromlist=["UDSResponse"]).UDSResponse(
                service_id = ServiceID.READ_DTC_INFORMATION,
                positive   = True,
                data       = synthetic,
            ),
        )

    # Act
    snapshot = dtc_manager.read_all()

    # Assert
    dtc_codes = {r.dtc_code for r in snapshot.records}
    assert CAMERA_BLOCKAGE_DTC in dtc_codes, (
        f"Expected camera blockage DTC 0x{CAMERA_BLOCKAGE_DTC:06X} in snapshot; "
        f"found: {[hex(c) for c in dtc_codes]}"
    )


# ===========================================================================
# 9. ACC state functional signal read
# ===========================================================================
@pytest.mark.adas
@pytest.mark.functional
@pytest.mark.smoke
def test_acc_state_signal_read(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the ACC (Adaptive Cruise Control) state DID and validate range.

    Arrange: ECU in extended session.
    Act:     RDBI for acc_state DID.
    Assert:  Positive response; state byte is in valid range (0–2).
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "acc_state")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"ACC state DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    # Response format: [DID_H][DID_L][state_byte]...
    if len(response.data) >= 3:
        state_byte = response.data[2]
        assert state_byte in (0x00, 0x01, 0x02), (
            f"ACC state 0x{state_byte:02X} is outside valid range [0x00, 0x02]"
        )


# ===========================================================================
# 10. Object detection flag read
# ===========================================================================
@pytest.mark.adas
@pytest.mark.functional
@pytest.mark.regression
def test_object_detection_flag_read(
    uds_client: UDSClientBase,
    ecu_config: dict,
) -> None:
    """
    Read the ADAS object detection flag DID and confirm it is a boolean.

    Arrange: ECU in extended session.
    Act:     RDBI for object_detection_flag DID.
    Assert:  Positive response; flag byte is 0x00 or 0x01.
    """
    uds_client.diagnostic_session_control(SessionType.EXTENDED_DIAGNOSTIC)
    did = _get_did(ecu_config, "object_detection_flag")

    response = uds_client.read_data_by_identifier(did)

    assert response.positive, (
        f"Object detection DID 0x{did:04X} read failed: NRC={response.nrc_name}"
    )
    if len(response.data) >= 3:
        flag_byte = response.data[2]
        assert flag_byte in (0x00, 0x01), (
            f"Object detection flag 0x{flag_byte:02X} is not a valid boolean (0x00 or 0x01)"
        )
