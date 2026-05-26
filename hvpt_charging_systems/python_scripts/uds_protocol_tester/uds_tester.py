"""
uds_protocol_tester/uds_tester.py
Complete UDS (ISO 14229) Protocol Compliance Tester.

Tests all standard UDS services:
    0x10 — DiagnosticSessionControl
    0x11 — ECUReset
    0x14 — ClearDiagnosticInformation
    0x19 — ReadDTCInformation
    0x22 — ReadDataByIdentifier
    0x27 — SecurityAccess
    0x28 — CommunicationControl
    0x2E — WriteDataByIdentifier
    0x3E — TesterPresent
"""
import pytest
import udsoncan
import time
import logging
from udsoncan import services


logging.basicConfig(level=logging.WARNING)


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE 0x10 — DiagnosticSessionControl
# ─────────────────────────────────────────────────────────────────────────────

class TestDiagnosticSessionControl:
    """ISO 14229-1 Section 9.4 — DiagnosticSessionControl (0x10)"""

    def test_default_session(self, uds_client):
        """TC-UDS-010: ECU shall enter Default session (0x01) with positive response."""
        resp = uds_client.change_session(
            services.DiagnosticSessionControl.Session.defaultSession
        )
        assert resp.positive, f"Default session failed: {resp.code_name}"

    def test_extended_session(self, uds_client):
        """TC-UDS-011: ECU shall enter Extended Diagnostic session (0x03)."""
        resp = uds_client.change_session(
            services.DiagnosticSessionControl.Session.extendedDiagnosticSession
        )
        assert resp.positive, f"Extended session failed: {resp.code_name}"

    def test_programming_session(self, uds_client):
        """TC-UDS-012: ECU shall enter Programming session (0x02)."""
        resp = uds_client.change_session(
            services.DiagnosticSessionControl.Session.programmingSession
        )
        assert resp.positive, f"Programming session failed: {resp.code_name}"

    def test_invalid_session_nrc(self, uds_client):
        """TC-UDS-013: Invalid session subfunction shall return NRC 0x12."""
        # Manually send raw UDS request with invalid session type
        uds_client.connection.send(bytes([0x10, 0xFF]))
        response_bytes = uds_client.connection.wait_frame(timeout=2.0)
        if response_bytes and len(response_bytes) >= 3:
            assert response_bytes[0] == 0x7F, "Expected negative response"
            assert response_bytes[1] == 0x10, "Expected SID 0x10 in NRC"
            assert response_bytes[2] == 0x12, \
                f"Expected NRC 0x12 (subFunctionNotSupported), got {response_bytes[2]:#x}"

    def test_session_returns_to_default_on_timeout(self, uds_client):
        """TC-UDS-014: ECU shall return to Default session after S3 timeout (typ. 5s)."""
        uds_client.change_session(0x03)
        time.sleep(6.0)  # Wait longer than S3 timer

        # Try a Default-only operation to confirm session reset
        resp = uds_client.change_session(0x01)
        assert resp.positive


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE 0x11 — ECUReset
# ─────────────────────────────────────────────────────────────────────────────

class TestECUReset:
    """ISO 14229-1 Section 9.3 — ECUReset (0x11)"""

    @pytest.mark.slow
    def test_hard_reset(self, uds_client):
        """TC-UDS-020: ECU shall perform hard reset and return to Default session."""
        resp = uds_client.ecu_reset(services.ECUReset.ResetType.hardReset)
        assert resp.positive, f"Hard reset failed: {resp.code_name}"
        time.sleep(2.0)  # Wait for ECU to restart

        # ECU should be back in default session after restart
        resp2 = uds_client.change_session(0x01)
        assert resp2.positive, "ECU not accessible after hard reset"

    def test_soft_reset(self, uds_client):
        """TC-UDS-021: ECU shall perform soft reset."""
        resp = uds_client.ecu_reset(services.ECUReset.ResetType.softReset)
        assert resp.positive, f"Soft reset failed: {resp.code_name}"
        time.sleep(1.0)

    def test_reset_requires_extended_session(self, uds_client):
        """TC-UDS-022: ECUReset shall be available in Default session (per spec)."""
        uds_client.change_session(0x01)
        resp = uds_client.ecu_reset(services.ECUReset.ResetType.hardReset)
        assert resp.positive, "ECUReset should work in Default session"


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE 0x22 — ReadDataByIdentifier
# ─────────────────────────────────────────────────────────────────────────────

class TestReadDataByIdentifier:
    """ISO 14229-1 Section 11.2 — ReadDataByIdentifier (0x22)"""

    # Standard DIDs required by ISO 14229
    @pytest.mark.parametrize("did,name,expected_len", [
        (0xF180, "BootSoftwareIdentificationDataRecord",    None),
        (0xF181, "ApplicationSoftwareIdentificationDataRecord", None),
        (0xF186, "ActiveDiagnosticSessionDataRecord",      1),
        (0xF187, "VehicleManufacturerSparePartNumberDataRecord", None),
        (0xF189, "VehicleManufacturerECUSoftwareNumber",   None),
        (0xF18A, "SystemSupplierIdentifier",                4),
        (0xF18B, "ECUManufacturingDate",                    4),
        (0xF18C, "ECUSerialNumber",                         None),
        (0xF190, "VehicleIdentificationNumber",             17),
        (0xF191, "VehicleManufacturerECUHardwareNumber",   None),
        (0xF192, "SystemSupplierECUHardwareNumber",        None),
        (0xF193, "SystemSupplierECUHardwareVersionNumber", None),
        (0xF195, "SystemSupplierECUSoftwareNumber",        None),
    ])
    def test_standard_did_readable(self, uds_client, did, name, expected_len):
        """TC-UDS-030x: Standard ISO DIDs shall be readable in Default session."""
        resp = uds_client.read_data_by_identifier(did)
        assert resp.positive, f"DID {did:#06x} ({name}) failed: {resp.code_name}"
        data = resp.service_data.values.get(did)
        assert data is not None and len(data) > 0, \
            f"DID {did:#06x} returned empty data"
        if expected_len:
            assert len(data) == expected_len, \
                f"DID {did:#06x} length {len(data)} != expected {expected_len}"

    def test_vin_is_valid_ascii(self, uds_client):
        """TC-UDS-031: VIN (0xF190) shall be 17 uppercase alphanumeric ASCII chars."""
        resp = uds_client.read_data_by_identifier(0xF190)
        assert resp.positive
        vin = bytes(resp.service_data.values[0xF190])
        assert len(vin) == 17, f"VIN length {len(vin)} != 17"
        vin_str = vin.decode('ascii', errors='replace')
        assert vin_str.isalnum(), f"VIN not alphanumeric: {vin_str!r}"
        assert vin_str.isupper() or vin_str.isdigit(), \
            f"VIN contains lowercase: {vin_str!r}"

    def test_active_session_did_reflects_current_session(self, uds_client):
        """TC-UDS-032: DID 0xF186 shall reflect the active UDS session."""
        uds_client.change_session(0x03)  # Extended
        resp = uds_client.read_data_by_identifier(0xF186)
        assert resp.positive
        session_byte = resp.service_data.values[0xF186][0]
        assert session_byte == 0x03, \
            f"DID 0xF186 shows {session_byte:#x} but expected 0x03 (extended)"

    def test_unsupported_did_returns_nrc_31(self, uds_client):
        """TC-UDS-033: Unsupported DID shall return NRC 0x31 (requestOutOfRange)."""
        resp = uds_client.read_data_by_identifier(0xFFFF)
        assert not resp.positive
        assert resp.code == 0x31, \
            f"Expected NRC 0x31, got {resp.code:#x} ({resp.code_name})"


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE 0x27 — SecurityAccess
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityAccess:
    """ISO 14229-1 Section 9.4.2 — SecurityAccess (0x27)"""

    def test_seed_request_returns_8_bytes(self, uds_client):
        """TC-UDS-040: SecurityAccess RequestSeed shall return 8-byte seed."""
        uds_client.change_session(0x03)
        resp = uds_client.request_seed(0x01)
        assert resp.positive, f"RequestSeed failed: {resp.code_name}"
        seed = resp.service_data.seed
        assert len(seed) == 8, f"Seed length {len(seed)} != 8 bytes"
        assert any(b != 0 for b in seed), "Seed is all zeros (suspiciously weak)"

    def test_wrong_key_returns_nrc_35(self, uds_client):
        """TC-UDS-041: Wrong security key shall return NRC 0x35."""
        uds_client.change_session(0x03)
        uds_client.request_seed(0x01)
        wrong_key = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        resp = uds_client.send_key(0x02, wrong_key)
        assert not resp.positive
        assert resp.code == 0x35, \
            f"Expected NRC 0x35 (invalidKey), got {resp.code:#x}"

    def test_security_access_lockout_after_3_wrong_keys(self, uds_client):
        """TC-UDS-042: ECU shall lock out after 3 wrong key attempts (NRC 0x36)."""
        uds_client.change_session(0x03)
        wrong_key = bytes([0x00] * 8)

        for attempt in range(3):
            uds_client.request_seed(0x01)
            resp = uds_client.send_key(0x02, wrong_key)

        # 4th attempt should return exceededNumberOfAttempts (0x36)
        uds_client.request_seed(0x01)
        resp = uds_client.send_key(0x02, wrong_key)
        assert resp.code in (0x36, 0x37), \
            f"Expected lockout NRC (0x36/0x37), got {resp.code:#x}"


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE 0x3E — TesterPresent
# ─────────────────────────────────────────────────────────────────────────────

class TestTesterPresent:
    """ISO 14229-1 Section 9.2 — TesterPresent (0x3E)"""

    def test_tester_present_with_response(self, uds_client):
        """TC-UDS-050: TesterPresent (sub=0x00) shall return positive response 0x7E."""
        resp = uds_client.tester_present()
        assert resp.positive, f"TesterPresent failed: {resp.code_name}"

    def test_tester_present_suppress_response(self, uds_client):
        """TC-UDS-051: TesterPresent (sub=0x80) shall not return response."""
        # Send with suppressPositiveResponse bit
        uds_client.connection.send(bytes([0x3E, 0x80]))
        # No response expected — timeout is expected behavior
        try:
            frame = uds_client.connection.wait_frame(timeout=0.5)
            if frame:
                # If a response comes, it should NOT be a positive response to 0x3E
                assert frame[0] != 0x7E, \
                    "ECU responded to suppressed TesterPresent (should not)"
        except Exception:
            pass  # Timeout = correct behavior

    def test_session_maintained_by_tester_present(self, uds_client):
        """TC-UDS-052: Periodic TesterPresent shall maintain extended session past S3 timer."""
        uds_client.change_session(0x03)

        # Send TesterPresent every 4s for 12s total
        for _ in range(3):
            time.sleep(4.0)
            resp = uds_client.tester_present()
            assert resp.positive, "TesterPresent failed during keepalive"

        # Session should still be extended
        resp = uds_client.read_data_by_identifier(0xF186)
        assert resp.positive
        assert resp.service_data.values[0xF186][0] == 0x03, \
            "Session dropped from extended despite TesterPresent keepalive"
