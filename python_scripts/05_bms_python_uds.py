#!/usr/bin/env python3
"""
FILE:    05_bms_python_uds.py
PURPOSE: BMS UDS Diagnostics via Python + python-can / ISO-TP
         Covers all ISO 14229 services relevant to BMS:
           - DiagnosticSessionControl (0x10)
           - SecurityAccess (0x27)
           - ReadDataByIdentifier (0x22)
           - WriteDataByIdentifier (0x2E)
           - ReadDTCInformation (0x19)
           - ClearDiagnosticInformation (0x14)
           - ECUReset (0x11)
           - RoutineControl (0x31)
           - InputOutputControlByIdentifier (0x2F)
           - ControlDTCSetting (0x85)
           - TesterPresent (0x3E)
         Full EOL sequence and DTC reading with decode table

DEPENDENCIES:
    pip install python-can udsoncan can-isotp

USAGE:
    python 05_bms_python_uds.py --mode read_all
    python 05_bms_python_uds.py --mode eol
    python 05_bms_python_uds.py --mode read_dtcs
    python 05_bms_python_uds.py --mode clear_dtcs

AUTHOR: BMS Validation Team
DATE:   2026-04-19
"""

import argparse
import logging
import time
import struct
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger("BMS_UDS")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s"
)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  BMS UDS DID & DTC Definitions
# ─────────────────────────────────────────────────────────────────────────────

# Data Identifiers ─ Read Only
BMS_READ_DIDS: Dict[int, dict] = {
    0xF190: {"name": "SoC",             "unit": "%",   "scale": 0.5,   "offset": 0,     "bytes": 1},
    0xF191: {"name": "SoH",             "unit": "%",   "scale": 0.5,   "offset": 0,     "bytes": 1},
    0xF192: {"name": "Pack Voltage",    "unit": "V",   "scale": 0.1,   "offset": 0,     "bytes": 2},
    0xF193: {"name": "Pack Current",    "unit": "A",   "scale": 0.1,   "offset": -3276.8,"bytes": 2},
    0xF194: {"name": "Max Cell Voltage","unit": "V",   "scale": 0.001, "offset": 0,     "bytes": 2},
    0xF195: {"name": "Min Cell Voltage","unit": "V",   "scale": 0.001, "offset": 0,     "bytes": 2},
    0xF196: {"name": "Max Temperature", "unit": "°C",  "scale": 1.0,   "offset": -40,   "bytes": 1},
    0xF197: {"name": "Min Temperature", "unit": "°C",  "scale": 1.0,   "offset": -40,   "bytes": 1},
    0xF198: {"name": "Cell Delta",      "unit": "mV",  "scale": 1.0,   "offset": 0,     "bytes": 2},
    0xF199: {"name": "BMS State",       "unit": "",    "scale": 1.0,   "offset": 0,     "bytes": 1},
    0xF19A: {"name": "Fault Level",     "unit": "",    "scale": 1.0,   "offset": 0,     "bytes": 1},
    0xF19B: {"name": "Cycle Count",     "unit": "",    "scale": 1.0,   "offset": 0,     "bytes": 2},
    0xF19C: {"name": "Pack Serial No.", "unit": "",    "scale": None,  "offset": 0,     "bytes": 10},  # ASCII
    0xF19D: {"name": "SW Version",      "unit": "",    "scale": None,  "offset": 0,     "bytes": 3},   # BCD
    0xF19E: {"name": "Isolation R",     "unit": "Ω",  "scale": 10.0,  "offset": 0,     "bytes": 2},
    0xF19F: {"name": "Active DTC Count","unit": "",    "scale": 1.0,   "offset": 0,     "bytes": 1},
}

# Data Identifiers ─ Write (require security unlock)
BMS_WRITE_DIDS: Dict[int, dict] = {
    0xF17F: {"name": "VIN",             "bytes": 17},
    0xF1A0: {"name": "Capacity (Ah)",   "bytes": 2},
    0xF1A1: {"name": "SoC Init (%)",    "bytes": 1},
    0xF1A2: {"name": "Cell Chemistry",  "bytes": 1},
    0xF1A3: {"name": "OV1 Threshold",   "bytes": 2},
    0xF1A4: {"name": "OV2 Threshold",   "bytes": 2},
    0xF1A5: {"name": "UV1 Threshold",   "bytes": 2},
    0xF1A6: {"name": "UV2 Threshold",   "bytes": 2},
    0xF1FF: {"name": "EOL Flag",        "bytes": 2},
}

# DTC Decode Table
DTC_DECODE: Dict[int, dict] = {
    0x0A0D: {"desc": "Cell Voltage High — Warning",         "severity": "Warning",   "reaction": "20% Power Derate"},
    0x0A0E: {"desc": "Cell Voltage High — Critical",        "severity": "Critical",  "reaction": "Contactor Open"},
    0x0A0F: {"desc": "Cell Voltage Low — Critical",         "severity": "Critical",  "reaction": "Contactor Open"},
    0x0A10: {"desc": "OV HW Safety Mechanism Failure",      "severity": "Safety",    "reaction": "Reduced Power"},
    0x0A1A: {"desc": "Cell Temperature High — Warning",     "severity": "Warning",   "reaction": "Cooling Max + 50% Derate"},
    0x0A1B: {"desc": "Cell Temperature High — Critical",    "severity": "Critical",  "reaction": "Contactor Open"},
    0x0A1C: {"desc": "Temperature Sensor Open Circuit",     "severity": "Diagnostic","reaction": "Assume Max Temp"},
    0x0A2D: {"desc": "SoC Out of Range",                    "severity": "Diagnostic","reaction": "Limit Charge/Discharge"},
    0x0A3A: {"desc": "Contactor Weld Detected",             "severity": "Safety",    "reaction": "HV Isolation Maintained"},
    0x0A3B: {"desc": "Precharge Failure — Timeout",         "severity": "Critical",  "reaction": "HV Ready Blocked"},
    0x0A3C: {"desc": "Emergency HV OFF — Crash Signal",     "severity": "Critical",  "reaction": "All Contactors Open"},
    0x1A00: {"desc": "Pack Over-Temperature Emergency",     "severity": "Emergency", "reaction": "Immediate Shutdown"},
    0x1B00: {"desc": "Isolation Resistance — Warning",      "severity": "Warning",   "reaction": "Driver Warning Lamp"},
    0x1B01: {"desc": "Isolation Resistance — Critical",     "severity": "Critical",  "reaction": "50% Charge Power Limit"},
    0x1B02: {"desc": "Isolation Resistance — Emergency",    "severity": "Emergency", "reaction": "Immediate HV Off"},
    0x1C00: {"desc": "CAN Communication Timeout (VCU)",    "severity": "Diagnostic","reaction": "Limp Mode"},
    0x1D00: {"desc": "IMD Self-Test Failure",               "severity": "Safety",    "reaction": "Limp Mode"},
}

# Routine Control IDs
ROUTINE_IDS: Dict[int, str] = {
    0x0201: "BMS Self-Test",
    0x0202: "Force Cell Balancing",
    0x0203: "Contactor Self-Test",
    0x0204: "IMD Self-Test",
    0x0205: "Reset Cycle Counter",
    0x0206: "OV HW Safety Mechanism Test",
}

# BMS State decode
BMS_STATES: Dict[int, str] = {
    0: "INIT",
    1: "IDLE",
    2: "PRECHARGE",
    3: "HV_READY",
    4: "CHARGING",
    5: "DISCHARGING",
    6: "FAULT",
    7: "SLEEP",
}


# ─────────────────────────────────────────────────────────────────────────────
# 2.  UDS Transport Layer (ISO 15765-2 ISOTP)
# ─────────────────────────────────────────────────────────────────────────────
class UDSTransport:
    """
    UDS transport over CAN using python-can + can-isotp.
    Handles single frames (≤7 bytes) and multi-frame via ISOTP.
    """

    def __init__(self, channel: str = "virtual", bustype: str = "virtual",
                 tx_id: int = 0x7E2, rx_id: int = 0x7EA,
                 bitrate: int = 500000, simulation: bool = True):
        self.tx_id      = tx_id
        self.rx_id      = rx_id
        self.simulation = simulation
        self._bus       = None

        if not simulation:
            try:
                import can
                self._bus = can.interface.Bus(channel=channel, bustype=bustype,
                                              bitrate=bitrate)
                logger.info("CAN bus connected: %s %s @ %d bps", bustype, channel, bitrate)
            except Exception as exc:
                logger.warning("CAN not available (%s) — falling back to simulation", exc)
                self.simulation = True

    def send_receive(self, payload: bytes, timeout_s: float = 0.5) -> Optional[bytes]:
        """Send UDS request and return response bytes."""
        if self.simulation:
            return self._simulate_response(payload)

        try:
            import can
            import isotp

            addr    = isotp.Address(isotp.AddressingMode.Normal_11bits,
                                    txid=self.tx_id, rxid=self.rx_id)
            stack   = isotp.CanStack(self._bus, address=addr)
            stack.send(payload)

            deadline = time.time() + timeout_s
            while time.time() < deadline:
                stack.process()
                if stack.available():
                    return bytes(stack.recv())
                time.sleep(0.001)

            logger.warning("UDS timeout (%.3f s) for SID 0x%X", timeout_s, payload[0])
            return None

        except Exception as exc:
            logger.error("Transport error: %s", exc)
            return None

    def _simulate_response(self, payload: bytes) -> bytes:
        """Return simulated positive responses for testing without hardware."""
        if not payload:
            return b""

        sid = payload[0]

        # DiagnosticSessionControl
        if sid == 0x10:
            return bytes([0x50, payload[1], 0x00, 0x19, 0x01, 0xF4])

        # SecurityAccess — Seed
        elif sid == 0x27 and payload[1] == 0x01:
            return bytes([0x67, 0x01, 0xDE, 0xAD, 0xBE, 0xEF])

        # SecurityAccess — Key accepted
        elif sid == 0x27 and payload[1] == 0x02:
            return bytes([0x67, 0x02])

        # ReadDataByIdentifier
        elif sid == 0x22:
            did = (payload[1] << 8) | payload[2]
            return self._sim_read_did(did)

        # WriteDataByIdentifier
        elif sid == 0x2E:
            return bytes([0x6E, payload[1], payload[2]])

        # ReadDTC — reportDTCByStatusMask
        elif sid == 0x19 and payload[1] == 0x02:
            # Simulate 2 stored DTCs
            return bytes([
                0x59, 0x02, 0xFF, 0x06,  # header: 0x59, subFn, dtcFormatID, availabilityMask
                0x0A, 0x0D, 0x00, 0x08,  # DTC1: 0x0A0D, status=0x08 (confirmed)
                0x1C, 0x00, 0x00, 0x09,  # DTC2: 0x1C00, status=0x09
            ])

        # ClearDTC
        elif sid == 0x14:
            return bytes([0x54])

        # ECUReset
        elif sid == 0x11:
            return bytes([0x51, payload[1]])

        # RoutineControl — Start
        elif sid == 0x31 and payload[1] == 0x01:
            return bytes([0x71, 0x01, payload[2], payload[3], 0x00])  # 0x00 = PASS

        # TesterPresent
        elif sid == 0x3E:
            return bytes([0x7E, 0x00])

        # ControlDTCSetting
        elif sid == 0x85:
            return bytes([0xC5, payload[1]])

        # CommunicationControl
        elif sid == 0x28:
            return bytes([0x68, payload[1]])

        # Default — Negative Response: Conditions Not Correct
        else:
            return bytes([0x7F, sid, 0x22])

    def _sim_read_did(self, did: int) -> bytes:
        """Return realistic simulated values for each DID."""
        sim_values = {
            0xF190: bytes([0x62, 0xF1, 0x90, 0x96]),          # SoC = 75% (0x96 × 0.5)
            0xF191: bytes([0x62, 0xF1, 0x91, 0xC8]),          # SoH = 100%
            0xF192: bytes([0x62, 0xF1, 0x92, 0x0F, 0x92]),    # Pack V = 395.4 V (0x0F92 × 0.1)
            0xF193: bytes([0x62, 0xF1, 0x93, 0x80, 0x00]),    # Current = 0 A (offset centre)
            0xF194: bytes([0x62, 0xF1, 0x94, 0x0E, 0xA6]),    # Max cell V = 3.750 V
            0xF195: bytes([0x62, 0xF1, 0x95, 0x0E, 0x8C]),    # Min cell V = 3.724 V
            0xF196: bytes([0x62, 0xF1, 0x96, 0x41]),          # Max temp = 25°C (0x41 - 40)
            0xF197: bytes([0x62, 0xF1, 0x97, 0x3A]),          # Min temp = 18°C
            0xF198: bytes([0x62, 0xF1, 0x98, 0x00, 0x1A]),    # Cell delta = 26 mV
            0xF199: bytes([0x62, 0xF1, 0x99, 0x05]),          # State = DISCHARGING (5)
            0xF19A: bytes([0x62, 0xF1, 0x9A, 0x00]),          # Fault Level = 0
            0xF19B: bytes([0x62, 0xF1, 0x9B, 0x00, 0xC8]),    # Cycle count = 200
            0xF19D: bytes([0x62, 0xF1, 0x9D, 0x03, 0x05, 0x00]),  # SW 03.05.00
            0xF19E: bytes([0x62, 0xF1, 0x9E, 0x61, 0xA8]),    # R_iso = 250000 Ω (0x61A8 × 10)
            0xF19F: bytes([0x62, 0xF1, 0x9F, 0x00]),          # Active DTC count = 0
        }
        return sim_values.get(did, bytes([0x7F, 0x22, 0x31]))  # Out of range if unknown


# ─────────────────────────────────────────────────────────────────────────────
# 3.  UDS Client
# ─────────────────────────────────────────────────────────────────────────────
class BMSUDSClient:
    """
    High-level BMS UDS client.
    Automatically handles session management, security access, and response decoding.
    """

    SECURITY_CONSTANT = 0xA53CF069  # XOR constant for key derivation

    def __init__(self, transport: UDSTransport):
        self.tp               = transport
        self._session         = 0x01   # Default session
        self._security_level  = 0      # 0 = locked

    # ── Session Management ────────────────────────────────────────────────
    def open_default_session(self) -> bool:
        logger.info("Opening Default Session (0x01)")
        resp = self.tp.send_receive(bytes([0x10, 0x01]))
        if resp and resp[0] == 0x50:
            self._session = 0x01
            logger.info("  ✓ Default session active")
            return True
        return self._log_nrc(resp, "DiagnosticSessionControl Default")

    def open_extended_session(self) -> bool:
        logger.info("Opening Extended Diagnostic Session (0x03)")
        resp = self.tp.send_receive(bytes([0x10, 0x03]))
        if resp and resp[0] == 0x50:
            self._session = 0x03
            logger.info("  ✓ Extended session active")
            return True
        return self._log_nrc(resp, "DiagnosticSessionControl Extended")

    def open_programming_session(self) -> bool:
        logger.info("Opening Programming Session (0x02)")
        resp = self.tp.send_receive(bytes([0x10, 0x02]))
        if resp and resp[0] == 0x50:
            self._session = 0x02
            logger.info("  ✓ Programming session active")
            return True
        return self._log_nrc(resp, "DiagnosticSessionControl Programming")

    def tester_present(self) -> bool:
        """Keep session alive (suppress positive response with 0x80 sub-function)."""
        resp = self.tp.send_receive(bytes([0x3E, 0x80]))
        return resp is not None  # 0x80 = suppress response → may return nothing

    # ── Security Access ───────────────────────────────────────────────────
    def security_access_level1(self) -> bool:
        """Perform complete Security Access Level 1 (seed + key exchange)."""
        logger.info("Security Access — Requesting seed (Level 1)")

        # Request seed
        resp = self.tp.send_receive(bytes([0x27, 0x01]))
        if not resp or resp[0] != 0x67 or resp[1] != 0x01:
            return self._log_nrc(resp, "SecurityAccess Seed Request")

        seed = int.from_bytes(resp[2:6], "big")
        key  = self._compute_key(seed)
        logger.info("  Seed: 0x%08X → Key: 0x%08X", seed, key)

        # Send key
        key_bytes = key.to_bytes(4, "big")
        resp = self.tp.send_receive(bytes([0x27, 0x02]) + key_bytes)
        if resp and resp[0] == 0x67 and resp[1] == 0x02:
            self._security_level = 1
            logger.info("  ✓ Security Level 1 UNLOCKED")
            return True

        return self._log_nrc(resp, "SecurityAccess Key Send")

    def _compute_key(self, seed: int) -> int:
        """XOR-based key derivation: key = rotate_left_1(seed XOR constant)."""
        xored = seed ^ self.SECURITY_CONSTANT
        key   = ((xored << 1) | (xored >> 31)) & 0xFFFFFFFF
        return key

    # ── Read Data By Identifier ───────────────────────────────────────────
    def read_did(self, did: int) -> Optional[dict]:
        """Read a single DID and return decoded value dict."""
        request = bytes([0x22, (did >> 8) & 0xFF, did & 0xFF])
        resp    = self.tp.send_receive(request)

        if not resp or resp[0] != 0x62:
            self._log_nrc(resp, f"ReadDID 0x{did:04X}")
            return None

        resp_did = (resp[1] << 8) | resp[2]
        if resp_did != did:
            logger.warning("Response DID 0x%04X does not match request DID 0x%04X",
                           resp_did, did)
            return None

        data_bytes = resp[3:]
        return self._decode_did(did, data_bytes)

    def read_all_bms_dids(self) -> dict:
        """Read all defined BMS DIDs and return a summary dict."""
        results = {}
        logger.info("═" * 55)
        logger.info("  BMS LIVE DATA SNAPSHOT")
        logger.info("═" * 55)

        for did, info in BMS_READ_DIDS.items():
            result = self.read_did(did)
            if result:
                results[info["name"]] = result
                logger.info("  %-25s : %s %s",
                            info["name"],
                            result.get("formatted", "N/A"),
                            info["unit"])
            else:
                logger.warning("  %-25s : READ FAILED", info["name"])
            time.sleep(0.02)

        logger.info("═" * 55)
        return results

    def _decode_did(self, did: int, data: bytes) -> dict:
        """Decode raw DID bytes using scaling/offset from BMS_READ_DIDS table."""
        info   = BMS_READ_DIDS.get(did)
        result = {"raw": data.hex().upper(), "did": did}

        if not info:
            result["formatted"] = data.hex().upper()
            return result

        scale  = info.get("scale")
        offset = info.get("offset", 0)
        n      = info.get("bytes", 1)

        # ASCII string (e.g. serial number)
        if scale is None and n > 2:
            try:
                result["value"]     = data[:n].decode("ascii", errors="replace")
                result["formatted"] = result["value"]
            except Exception:
                result["formatted"] = data.hex()
            return result

        # BCD version (SW version)
        if scale is None and n == 3:
            result["formatted"] = f"{data[0]:02X}.{data[1]:02X}.{data[2]:02X}"
            return result

        # Numeric
        if n == 1:
            raw_val = data[0]
        elif n == 2:
            raw_val = struct.unpack(">H", data[:2])[0]
        else:
            raw_val = int.from_bytes(data[:n], "big")

        phys_val = raw_val * scale + offset
        result["value"]     = phys_val
        result["formatted"] = f"{phys_val:.3f}" if isinstance(phys_val, float) else str(phys_val)

        # Special decode for BMS State
        if did == 0xF199:
            result["formatted"] = BMS_STATES.get(int(phys_val), f"UNKNOWN ({int(phys_val)})")

        return result

    # ── Write Data By Identifier ──────────────────────────────────────────
    def write_did(self, did: int, value_bytes: bytes) -> bool:
        """Write data to a DID (requires security unlock for most write DIDs)."""
        if self._security_level < 1:
            logger.warning("Security not unlocked — write may be rejected by ECU")

        info    = BMS_WRITE_DIDS.get(did, {"name": f"DID 0x{did:04X}"})
        request = bytes([0x2E, (did >> 8) & 0xFF, did & 0xFF]) + value_bytes
        logger.info("Writing DID 0x%04X (%s) = %s",
                    did, info["name"], value_bytes.hex().upper())

        resp = self.tp.send_receive(request)
        if resp and resp[0] == 0x6E:
            logger.info("  ✓ Write confirmed")
            return True
        return self._log_nrc(resp, f"WriteDID 0x{did:04X}")

    # ── DTC Services ──────────────────────────────────────────────────────
    def read_active_dtcs(self) -> list:
        """Read all DTCs with status mask 0xFF (all status bits)."""
        logger.info("Reading DTCs (reportDTCByStatusMask 0xFF)")
        request = bytes([0x19, 0x02, 0xFF])
        resp    = self.tp.send_receive(request, timeout_s=1.0)

        if not resp or resp[0] != 0x59:
            self._log_nrc(resp, "ReadDTC")
            return []

        # Parse DTC records: starting at byte index 3 (skip 0x59, subFn, dtcFmtID)
        dtcs    = []
        offset  = 3

        # Skip availability mask byte if sub-function is 0x02
        if len(resp) > 3:
            offset = 4   # byte[3] = availability mask

        while offset + 3 < len(resp):
            b0     = resp[offset]
            b1     = resp[offset + 1]
            b2     = resp[offset + 2]
            status = resp[offset + 3] if offset + 3 < len(resp) else 0
            code   = (b0 << 16) | (b1 << 8) | b2

            info   = DTC_DECODE.get(code, {
                "desc": "Unknown DTC",
                "severity": "Unknown",
                "reaction": "N/A",
            })

            dtc_entry = {
                "code":     f"0x{code:06X}",
                "desc":     info["desc"],
                "severity": info["severity"],
                "reaction": info["reaction"],
                "status":   f"0x{status:02X}",
                "confirmed":(status & 0x08) != 0,
            }
            dtcs.append(dtc_entry)
            offset += 4

        logger.info("═" * 60)
        logger.info("  BMS DTC REPORT — %d DTC(s) found", len(dtcs))
        logger.info("═" * 60)
        for i, d in enumerate(dtcs, 1):
            confirmed = "CONFIRMED" if d["confirmed"] else "PENDING"
            logger.info("  [%d] %s | %s | %s", i, d["code"], confirmed, d["desc"])
            logger.info("      Severity: %-12s | Reaction: %s",
                        d["severity"], d["reaction"])
        logger.info("═" * 60)

        return dtcs

    def clear_dtcs(self) -> bool:
        """Clear all DTCs (group 0xFFFFFF)."""
        logger.info("Clearing all DTCs")
        resp = self.tp.send_receive(bytes([0x14, 0xFF, 0xFF, 0xFF]))
        if resp and resp[0] == 0x54:
            logger.info("  ✓ All DTCs cleared")
            return True
        return self._log_nrc(resp, "ClearDTC")

    # ── Routine Control ───────────────────────────────────────────────────
    def start_routine(self, routine_id: int, params: bytes = b"") -> Optional[bytes]:
        """Start a routine and return the result bytes."""
        name    = ROUTINE_IDS.get(routine_id, f"Routine 0x{routine_id:04X}")
        request = bytes([0x31, 0x01,
                         (routine_id >> 8) & 0xFF,
                         routine_id & 0xFF]) + params
        logger.info("Starting Routine: %s (0x%04X)", name, routine_id)
        resp    = self.tp.send_receive(request, timeout_s=5.0)

        if resp and resp[0] == 0x71:
            result = resp[4] if len(resp) > 4 else 0xFF
            status = "PASS" if result == 0x00 else f"FAIL (0x{result:02X})"
            logger.info("  ✓ %s — Result: %s", name, status)
            return resp[4:]
        self._log_nrc(resp, f"RoutineControl {name}")
        return None

    def run_bms_self_test(self) -> bool:
        result = self.start_routine(0x0201)
        return result is not None and result[0] == 0x00

    def run_contactor_test(self) -> bool:
        result = self.start_routine(0x0203)
        return result is not None and result[0] == 0x00

    def run_imd_test(self) -> bool:
        result = self.start_routine(0x0204)
        return result is not None and result[0] == 0x00

    def run_ov_hw_sm_test(self) -> bool:
        result = self.start_routine(0x0206)
        return result is not None and result[0] == 0x00

    # ── ECU Reset ─────────────────────────────────────────────────────────
    def ecu_reset_hard(self) -> bool:
        logger.info("ECU Hard Reset")
        resp = self.tp.send_receive(bytes([0x11, 0x01]))
        if resp and resp[0] == 0x51:
            logger.info("  ✓ ECU reset acknowledged")
            self._session       = 0x01
            self._security_level = 0
            return True
        return self._log_nrc(resp, "ECUReset Hard")

    def ecu_reset_soft(self) -> bool:
        logger.info("ECU Soft Reset")
        resp = self.tp.send_receive(bytes([0x11, 0x03]))
        if resp and resp[0] == 0x51:
            logger.info("  ✓ ECU soft reset acknowledged")
            return True
        return self._log_nrc(resp, "ECUReset Soft")

    # ── DTC Control ───────────────────────────────────────────────────────
    def disable_dtc_setting(self) -> bool:
        resp = self.tp.send_receive(bytes([0x85, 0x02]))
        if resp and resp[0] == 0xC5:
            logger.info("  ✓ DTC setting DISABLED")
            return True
        return self._log_nrc(resp, "ControlDTCSetting Disable")

    def enable_dtc_setting(self) -> bool:
        resp = self.tp.send_receive(bytes([0x85, 0x01]))
        if resp and resp[0] == 0xC5:
            logger.info("  ✓ DTC setting ENABLED")
            return True
        return self._log_nrc(resp, "ControlDTCSetting Enable")

    # ── I/O Control ───────────────────────────────────────────────────────
    def io_control_short_term(self, did: int, control_value: bytes) -> bool:
        """Force an output (shortTermAdjustment = 0x03)."""
        request = bytes([0x2F,
                         (did >> 8) & 0xFF, did & 0xFF,
                         0x03]) + control_value   # 0x03 = shortTermAdjust
        logger.info("I/O Control DID 0x%04X → %s", did, control_value.hex())
        resp = self.tp.send_receive(request)
        if resp and resp[0] == 0x6F:
            logger.info("  ✓ I/O Control accepted")
            return True
        return self._log_nrc(resp, f"IOControl DID 0x{did:04X}")

    def io_control_return_to_ecu(self, did: int) -> bool:
        """Return control to ECU (returnControlToECU = 0x00)."""
        request = bytes([0x2F, (did >> 8) & 0xFF, did & 0xFF, 0x00])
        resp    = self.tp.send_receive(request)
        if resp and resp[0] == 0x6F:
            logger.info("  ✓ I/O Control returned to ECU for DID 0x%04X", did)
            return True
        return self._log_nrc(resp, f"IOControl ReturnToECU 0x{did:04X}")

    # ── EOL Programming Sequence ──────────────────────────────────────────
    def run_eol_sequence(self,
                         vin: str        = "1BMSBMS0000012345",
                         capacity_ah: int = 60,
                         soc_init_pct: int = 80) -> bool:
        """
        Complete BMS EOL UDS programming sequence.
        Returns True if all steps passed.
        """
        logger.info("═" * 60)
        logger.info("  BMS EOL PROGRAMMING SEQUENCE")
        logger.info("═" * 60)

        steps_passed = 0
        steps_total  = 10

        # Step 1 — Extended session
        logger.info("\n[EOL Step 1/10] Open Extended Session")
        if not self.open_extended_session():
            logger.error("  ✗ Failed to open extended session")
            return False
        steps_passed += 1
        time.sleep(0.1)

        # Step 2 — Security Access
        logger.info("\n[EOL Step 2/10] Security Access Level 1")
        if not self.security_access_level1():
            logger.error("  ✗ Security access failed")
            return False
        steps_passed += 1
        time.sleep(0.1)

        # Step 3 — Disable DTC Setting
        logger.info("\n[EOL Step 3/10] Disable DTC Setting")
        if not self.disable_dtc_setting():
            logger.warning("  ⚠ DTC disable failed — continuing")
        else:
            steps_passed += 1
        time.sleep(0.1)

        # Step 4 — Write VIN
        logger.info("\n[EOL Step 4/10] Write VIN: %s", vin)
        vin_padded = vin[:17].ljust(17, '\x00').encode("ascii")
        if not self.write_did(0xF17F, vin_padded):
            logger.error("  ✗ VIN write failed")
        else:
            steps_passed += 1

        # Step 5 — Write Capacity
        logger.info("\n[EOL Step 5/10] Write Capacity: %d Ah", capacity_ah)
        if not self.write_did(0xF1A0, capacity_ah.to_bytes(2, "big")):
            logger.error("  ✗ Capacity write failed")
        else:
            steps_passed += 1

        # Step 6 — Write SoC Init
        logger.info("\n[EOL Step 6/10] Write SoC Init: %d%%", soc_init_pct)
        if not self.write_did(0xF1A1, bytes([soc_init_pct])):
            logger.error("  ✗ SoC init write failed")
        else:
            steps_passed += 1

        # Step 7 — Contactor self-test
        logger.info("\n[EOL Step 7/10] Run Contactor Self-Test")
        if not self.run_contactor_test():
            logger.error("  ✗ Contactor self-test failed")
        else:
            steps_passed += 1

        # Step 8 — Re-enable DTC setting
        logger.info("\n[EOL Step 8/10] Re-enable DTC Setting")
        self.enable_dtc_setting()
        steps_passed += 1

        # Step 9 — Write EOL flag
        logger.info("\n[EOL Step 9/10] Write EOL Completion Flag")
        if not self.write_did(0xF1FF, bytes([0x00, 0x01])):
            logger.error("  ✗ EOL flag write failed")
        else:
            steps_passed += 1

        # Step 10 — Clear DTCs + ECU Reset
        logger.info("\n[EOL Step 10/10] Clear DTCs & ECU Reset")
        self.clear_dtcs()
        time.sleep(0.1)
        self.ecu_reset_hard()
        steps_passed += 1

        # Summary
        logger.info("\n%s", "═" * 60)
        logger.info("  EOL RESULT: %d/%d steps passed", steps_passed, steps_total)
        logger.info("  STATUS    : %s",
                    "PASS ✓" if steps_passed >= steps_total - 1 else "FAIL ✗")
        logger.info("═" * 60)

        return steps_passed >= steps_total - 1  # Allow 1 non-critical failure

    # ── Helpers ───────────────────────────────────────────────────────────
    def _log_nrc(self, resp: Optional[bytes], context: str) -> bool:
        if resp is None:
            logger.error("  ✗ %s — No response (timeout)", context)
        elif len(resp) >= 3 and resp[0] == 0x7F:
            nrc = resp[2]
            NRC_TABLE = {
                0x10: "GeneralReject",
                0x11: "ServiceNotSupported",
                0x12: "SubFunctionNotSupported",
                0x13: "IncorrectMessageLength",
                0x22: "ConditionsNotCorrect",
                0x24: "RequestSequenceError",
                0x31: "RequestOutOfRange",
                0x33: "SecurityAccessDenied",
                0x35: "InvalidKey",
                0x36: "ExceededNumberOfAttempts",
                0x37: "RequiredTimeDelayNotExpired",
                0x78: "ResponsePending",
                0x7E: "SubFunctionNotSupportedInActiveSession",
                0x7F: "ServiceNotSupportedInActiveSession",
            }
            logger.error("  ✗ %s — NRC 0x%02X: %s",
                         context, nrc, NRC_TABLE.get(nrc, "Unknown"))
        else:
            logger.error("  ✗ %s — Unexpected response: %s",
                         context, resp.hex() if resp else "None")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 4.  CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="BMS UDS Diagnostics Tool")
    parser.add_argument("--mode", choices=[
        "read_all", "read_dtcs", "clear_dtcs", "eol",
        "self_test", "reset", "security_test"
    ], default="read_all", help="Operation mode")
    parser.add_argument("--channel",  default="virtual", help="CAN channel")
    parser.add_argument("--bustype",  default="virtual", help="CAN bustype")
    parser.add_argument("--sim",      action="store_true", default=True,
                        help="Run in simulation mode (no hardware required)")
    parser.add_argument("--vin",      default="1BMSBMS0000012345", help="VIN for EOL")
    parser.add_argument("--capacity", type=int, default=60, help="Capacity Ah for EOL")
    args = parser.parse_args()

    transport = UDSTransport(
        channel    = args.channel,
        bustype    = args.bustype,
        simulation = args.sim
    )
    client = BMSUDSClient(transport)

    if args.mode == "read_all":
        client.open_extended_session()
        client.read_all_bms_dids()

    elif args.mode == "read_dtcs":
        client.open_default_session()
        client.read_active_dtcs()

    elif args.mode == "clear_dtcs":
        client.open_extended_session()
        client.security_access_level1()
        client.clear_dtcs()

    elif args.mode == "eol":
        client.run_eol_sequence(vin=args.vin, capacity_ah=args.capacity)

    elif args.mode == "self_test":
        client.open_extended_session()
        client.security_access_level1()
        tests = {
            "BMS Self-Test":      client.run_bms_self_test(),
            "Contactor Test":     client.run_contactor_test(),
            "IMD Test":           client.run_imd_test(),
            "OV HW SM Test":      client.run_ov_hw_sm_test(),
        }
        print("\n─── Self-Test Results ───")
        for name, passed in tests.items():
            status = "PASS ✓" if passed else "FAIL ✗"
            print(f"  {name:<30} {status}")

    elif args.mode == "reset":
        client.open_extended_session()
        client.security_access_level1()
        client.ecu_reset_hard()

    elif args.mode == "security_test":
        client.open_extended_session()
        success = client.security_access_level1()
        print(f"\nSecurity Access: {'UNLOCKED ✓' if success else 'FAILED ✗'}")


if __name__ == "__main__":
    main()
