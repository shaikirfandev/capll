from __future__ import annotations

import pytest


@pytest.mark.diagnostics
class TestUDSServices:
    def test_diagnostic_session_control_service(self, uds_client) -> None:
        """Test ID: UDS_001
Requirement: Diagnostics shall support service 0x10.
Objective: Verify session control."""
        assert uds_client.diagnostic_session_control(0x03) == 0x03

    def test_clear_diagnostic_information_service(self, uds_client) -> None:
        """Test ID: UDS_002
Requirement: Diagnostics shall support service 0x14.
Objective: Verify DTC clear command."""
        uds_client.server.dtc_manager.set_dtc(0x111111)
        assert uds_client.clear_diagnostic_information() is True
        assert uds_client.read_dtc_information() == []

    def test_read_dtc_information_service(self, uds_client) -> None:
        """Test ID: UDS_003
Requirement: Diagnostics shall support service 0x19.
Objective: Verify DTC reading."""
        uds_client.server.dtc_manager.set_dtc(0x222222, description="radar blocked")
        records = uds_client.read_dtc_information()
        assert records[0].code == 0x222222

    def test_read_data_by_identifier_service(self, uds_client) -> None:
        """Test ID: UDS_004
Requirement: Diagnostics shall support service 0x22.
Objective: Verify DID read."""
        assert uds_client.read_data_by_identifier(0xF190).startswith(b"TESTVIN")

    def test_security_access_service(self, uds_client) -> None:
        """Test ID: UDS_005
Requirement: Diagnostics shall support service 0x27.
Objective: Verify seed/key unlock."""
        seed = uds_client.security_access_request_seed(0x01)
        key = uds_client.derive_key(seed)
        assert uds_client.security_access_send_key(0x02, key) is True

    def test_write_data_by_identifier_service(self, uds_client) -> None:
        """Test ID: UDS_006
Requirement: Diagnostics shall support service 0x2E.
Objective: Verify DID write."""
        assert uds_client.write_data_by_identifier(0xF187, b"ADAS-ECU-02") is True
        assert uds_client.read_data_by_identifier(0xF187) == b"ADAS-ECU-02"

    def test_tester_present_service(self, uds_client) -> None:
        """Test ID: UDS_007
Requirement: Diagnostics shall support service 0x3E.
Objective: Verify tester present keepalive."""
        assert uds_client.tester_present() is True
        assert uds_client.server.state.alive_counter == 1
