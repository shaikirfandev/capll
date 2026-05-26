"""
robot_framework/libraries/UDSLibrary.py

Robot Framework keyword library for UDS (ISO 14229-1) diagnostic operations.
Wraps pytest_framework/diagnostics/uds_client.py and dtc_handler.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pytest_framework"))

from robot.api import logger
from robot.api.deco import keyword, library

from diagnostics.uds_client  import UDSClient
from diagnostics.dtc_handler import DTCMonitor, DTCDatabase

ROBOT_LIBRARY_SCOPE = "SUITE"


@library(scope="SUITE", auto_keywords=False)
class UDSLibrary:
    """
    Robot Framework library for UDS diagnostic services.

    Usage:
        Library    ../libraries/UDSLibrary.py    tx_id=0x740    rx_id=0x748
    """

    def __init__(self, tx_id: int = 0x740, rx_id: int = 0x748):
        self._tx_id     = int(tx_id)
        self._rx_id     = int(rx_id)
        self._client: UDSClient   | None = None
        self._monitor: DTCMonitor | None = None

    # ── Session management ────────────────────────────────────────────────────

    @keyword("Open UDS Session")
    def open_uds_session(self, session_type: str = "default") -> None:
        """
        Open a UDS diagnostic session.

        Arguments:
        - ``session_type``: ``default`` (0x01), ``programming`` (0x02),
          or ``extended`` (0x03). Default: ``default``.
        """
        session_map = {"default": 0x01, "programming": 0x02, "extended": 0x03}
        session_byte = session_map.get(session_type.lower(), int(session_type, 16))
        self._client = UDSClient(tx_id=self._tx_id, rx_id=self._rx_id)
        self._client.sync_change_session(session_byte)
        logger.info(f"UDS session {session_type} (0x{session_byte:02X}) opened")

    @keyword("Close UDS Session")
    def close_uds_session(self) -> None:
        """Return ECU to default session and stop TesterPresent."""
        if self._client:
            self._client.sync_change_session(0x01)
            self._client.stop_tester_present()
        logger.info("UDS session closed")

    @keyword("Switch To UDS Session")
    def switch_to_uds_session(self, session_type: str) -> None:
        """Change diagnostic session without re-connecting."""
        session_map = {"default": 0x01, "programming": 0x02, "extended": 0x03}
        session_byte = session_map.get(session_type.lower(), int(session_type, 16))
        self._client.sync_change_session(session_byte)
        logger.info(f"Switched to session 0x{session_byte:02X}")

    # ── DID read / write ──────────────────────────────────────────────────────

    @keyword("Read DID")
    def read_did(self, did: str) -> bytes:
        """
        Read a Data Identifier (DID) from ECU.

        Arguments:
        - ``did``: hex string e.g. ``0xF186``

        Returns raw bytes.

        Example:
            ${data}=    Read DID    0xF186
        """
        did_int = int(did, 16) if isinstance(did, str) and did.startswith("0x") else int(did)
        data = self._client.sync_read_did(did_int)
        logger.info(f"ReadDID 0x{did_int:04X} → {data.hex() if data else 'None'}")
        return data

    @keyword("DID Value Should Be")
    def did_value_should_be(self, did: str, expected_hex: str) -> None:
        """
        Assert DID response equals expected hex bytes.

        Example:
            DID Value Should Be    0xF186    03
        """
        data     = self.read_did(did)
        expected = bytes.fromhex(expected_hex.replace(" ", ""))
        assert data == expected, (
            f"DID {did}: got {data.hex()}, expected {expected.hex()}"
        )

    @keyword("DID Should Contain")
    def did_should_contain(self, did: str, substring_hex: str) -> None:
        """
        Assert DID response contains substring (hex).

        Example:
            DID Should Contain    0xF190    4142
        """
        data      = self.read_did(did)
        substring = bytes.fromhex(substring_hex.replace(" ", ""))
        assert substring in data, (
            f"DID {did} response {data.hex()} does not contain {substring.hex()}"
        )

    @keyword("Write DID")
    def write_did(self, did: str, data_hex: str) -> None:
        """
        Write to a Data Identifier.

        Example:
            Write DID    0xF19E    4142434445
        """
        did_int = int(did, 16) if isinstance(did, str) and did.startswith("0x") else int(did)
        payload = bytes.fromhex(data_hex.replace(" ", ""))
        self._client.sync_write_did(did_int, payload)
        logger.info(f"WriteDID 0x{did_int:04X} ← {payload.hex()}")

    # ── DTC management ────────────────────────────────────────────────────────

    @keyword("Read DTCs")
    def read_dtcs(self, status_mask: str = "0x08") -> list:
        """
        Read DTCs from ECU using ReadDTCInformation (0x19).

        Returns a list of DTCEntry objects.
        """
        mask = int(status_mask, 16) if isinstance(status_mask, str) else int(status_mask)
        dtcs = self._client.sync_read_dtcs(status_mask=mask)
        logger.info(f"Found {len(dtcs)} DTCs with mask {status_mask}")
        return dtcs

    @keyword("DTC Should Be Set")
    def dtc_should_be_set(self, dtc_code: str) -> None:
        """
        Assert that a specific DTC is set (confirmed).

        Example:
            DTC Should Be Set    B0100
        """
        code = int(dtc_code, 16) if dtc_code.startswith(("B", "C", "P", "U")) else int(dtc_code)
        dtcs = self._client.sync_read_dtcs(status_mask=0x08)
        dtc_codes = [d.dtc_code for d in dtcs]
        assert code in dtc_codes or dtc_code.upper() in [hex(c).upper() for c in dtc_codes], (
            f"DTC {dtc_code} not found in ECU DTC list: {[hex(c) for c in dtc_codes]}"
        )
        logger.info(f"DTC {dtc_code} confirmed as SET ✓")

    @keyword("No DTCs Should Be Present")
    def no_dtcs_should_be_present(self, status_mask: str = "0x08") -> None:
        """Assert ECU has no active DTCs."""
        dtcs = self.read_dtcs(status_mask)
        assert len(dtcs) == 0, (
            f"Found {len(dtcs)} unexpected DTCs: {[hex(d.dtc_code) for d in dtcs]}"
        )
        logger.info("No DTCs present ✓")

    @keyword("Clear DTCs")
    def clear_dtcs(self) -> None:
        """Clear all DTCs (service 0x14)."""
        self._client.sync_clear_dtcs()
        logger.info("All DTCs cleared")

    # ── ECU reset ─────────────────────────────────────────────────────────────

    @keyword("Reset ECU")
    def reset_ecu(self, reset_type: str = "hard") -> None:
        """
        Trigger ECU reset (service 0x11).

        Arguments:
        - ``reset_type``: ``hard`` (0x01), ``soft`` (0x03). Default: ``hard``.
        """
        reset_map = {"hard": 0x01, "soft": 0x03, "key_off_on": 0x02}
        reset_byte = reset_map.get(reset_type.lower(), int(reset_type, 16))
        self._client.sync_ecu_reset(reset_byte)
        logger.info(f"ECU reset: {reset_type} (0x{reset_byte:02X})")

    # ── Security access ───────────────────────────────────────────────────────

    @keyword("Unlock Security Access")
    def unlock_security_access(self, level: str = "0x01") -> bytes:
        """
        Perform seed-key security access unlock.

        Returns seed bytes (caller responsible for key derivation if needed).

        Example:
            ${seed}=    Unlock Security Access    0x01
        """
        level_byte = int(level, 16) if isinstance(level, str) else int(level)
        seed = self._client.sync_security_access(level_byte)
        logger.info(f"Security access seed: {seed.hex() if seed else 'None'}")
        return seed

    # ── VIN ───────────────────────────────────────────────────────────────────

    @keyword("Read VIN")
    def read_vin(self) -> str:
        """Read Vehicle Identification Number (DID 0xF190)."""
        vin = self._client.sync_read_vin()
        logger.info(f"VIN: {vin}")
        return vin

    @keyword("VIN Should Be")
    def vin_should_be(self, expected_vin: str) -> None:
        """Assert ECU VIN matches expected value."""
        actual_vin = self.read_vin()
        assert actual_vin == expected_vin, (
            f"VIN mismatch: got '{actual_vin}', expected '{expected_vin}'"
        )
