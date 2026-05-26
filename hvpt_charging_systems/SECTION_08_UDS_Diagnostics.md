# SECTION 8 — UDS DIAGNOSTICS COMPLETE TRAINING
## ISO 14229 — Full Diagnostic Protocol Reference

---

## 8.1 UDS OVERVIEW

### 8.1.1 What is UDS?

Unified Diagnostic Services (UDS) is defined by ISO 14229. It is the standard diagnostic protocol used across ALL automotive ECUs for:
- Reading fault codes (DTCs)
- Reading/writing ECU data
- ECU programming (flash)
- Security access (seed/key)
- ECU configuration
- Routine control (test functions)

### 8.1.2 UDS Communication Stack

```
DIAGNOSTIC TOOL (PC / CANoe / Tester)
         │
         │  Application layer: UDS (ISO 14229)
         │
         │  Transport layer: ISO-TP / ISO 15765 (CAN transport)
         │  (handles segmentation of long messages)
         │
         │  Network layer: CAN / CAN FD / Ethernet (DoIP)
         │
ECU DIAGNOSTIC MODULE
         │
         │  Processes UDS requests
         │  Returns positive or negative responses
```

### 8.1.3 ISO-TP (ISO 15765-2) Transport Protocol

```
ISO-TP FRAME TYPES:
──────────────────────────────────────────────────────────────
SINGLE FRAME (SF): Complete message in 1 CAN frame
  Byte 0: [0][N_PCI_type=0000] [DL = length]
  Example: Single frame, 3 bytes: 0x03 10 01 AA BB CC 00 00

FIRST FRAME (FF): First frame of multi-frame message
  Byte 0–1: [0001][FF_DL high 4 bits][FF_DL low 8 bits]
  Followed by up to 6 bytes of data

CONSECUTIVE FRAME (CF): Continuation frames
  Byte 0: [0010][SN = sequence number 0–15]
  
FLOW CONTROL (FC): Receiver controls flow
  Byte 0: [0011][FS = 00=ContinueSend, 01=Wait, 02=Overflow]
  Byte 1: Block size (0 = unlimited)
  Byte 2: Separation time (milliseconds)

EXAMPLE: Reading 20-byte response
  Tester → ECU: [Single Frame] 02 22 F1 90 (ReadDID VIN)
  ECU → Tester: [First Frame]   10 15 62 F1 90 V I N ...
  Tester → ECU: [Flow Control]  30 00 00 (continue, block size=0)
  ECU → Tester: [Consec Frame]  21 N N N N N N N
  ECU → Tester: [Consec Frame]  22 N N N N N N N
  (3 frames to deliver 20 bytes)
```

---

## 8.2 UDS SERVICES REFERENCE

### 8.2.1 Service Overview

| SID | Name | Description |
|-----|------|-------------|
| 0x10 | DiagnosticSessionControl | Switch diagnostic session |
| 0x11 | ECUReset | Reset the ECU |
| 0x14 | ClearDiagnosticInformation | Clear DTCs |
| 0x19 | ReadDTCInformation | Read fault codes |
| 0x22 | ReadDataByIdentifier | Read ECU data by DID |
| 0x23 | ReadMemoryByAddress | Read memory directly |
| 0x27 | SecurityAccess | Seed/key security unlock |
| 0x28 | CommunicationControl | Control Tx/Rx |
| 0x2E | WriteDataByIdentifier | Write ECU data by DID |
| 0x2F | InputOutputControlByIdentifier | Control I/O |
| 0x31 | RoutineControl | Start/stop/request routines |
| 0x34 | RequestDownload | Start ECU programming |
| 0x36 | TransferData | Transfer programming data |
| 0x37 | RequestTransferExit | End programming |
| 0x3D | WriteMemoryByAddress | Write memory directly |
| 0x3E | TesterPresent | Keep session alive |
| 0x85 | ControlDTCSettings | Enable/disable DTC storage |

---

## 8.3 DIAGNOSTIC SESSIONS (SID 0x10)

```
SESSION TYPES:
──────────────────────────────────────────────────────────────
0x01 = Default Session (DS)
  - Always accessible
  - Read-only operations allowed
  - DTC reading allowed

0x02 = Programming Session (PROG)
  - Flash reprogramming
  - Requires security access first
  - Requires vehicle conditions (engine off, KL15 on)

0x03 = Extended Diagnostic Session (EXTDS)
  - Read/Write parameter access
  - Routine control
  - Fault injection capability
  - Requires security access for sensitive operations

OEM-specific sessions:
0x40 = Safety System Diagnostic Session
0x60 = Development Session

SESSION REQUEST/RESPONSE:
Request:  10 03           (enter Extended Session)
Response: 50 03 00 19 01  (positive response: 
                           session=0x03, P2max=25ms, P2ext*10=100ms)

SESSION TIMEOUT (S3 timer):
  If no communication for 5 seconds → ECU returns to Default Session
  Tester must send: 3E 00 (TesterPresent, suppressPositiveResponse bit=0)
  to keep extended/programming session alive
```

---

## 8.4 SECURITY ACCESS (SID 0x27)

```
SECURITY ACCESS FLOW:
──────────────────────────────────────────────────────────────
Tester → ECU:  27 01  (RequestSeed, level 01)
ECU → Tester:  67 01  [SEED_BYTE_1] [SEED_BYTE_2] [SEED_BYTE_3] [SEED_BYTE_4]

Example seed: 67 01 12 34 56 78
  Seed = 0x12345678

Tester calculates key (algorithm is OEM-specific, typically SECRET):
  Algorithm example (simplified): 
  key = (seed XOR 0xCAFEBABE) ROL 3

  key = 0x12345678 XOR 0xCAFEBABE = 0xD8CAECC6
  ROL 3 of 0xD8CAECC6 = ... (calculated)

Tester → ECU:  27 02  [KEY_BYTE_1] [KEY_BYTE_2] [KEY_BYTE_3] [KEY_BYTE_4]
ECU → Tester:  67 02  (positive response → access granted)

On failure:
ECU → Tester:  7F 27 35  (negative response: SID=0x27, NRC=0x35=InvalidKey)

FAILED ATTEMPTS:
  After 3 failed attempts → ECU locks for delay time
  NRC 0x36 = ExceededNumberOfAttempts
  NRC 0x37 = RequiredTimeDelayNotExpired (must wait before retry)
```

---

## 8.5 READ DATA BY IDENTIFIER (SID 0x22)

```
REQUEST FORMAT:
  22 [DID_High] [DID_Low]

RESPONSE FORMAT (positive):
  62 [DID_High] [DID_Low] [DATA...]

COMMON DIDs IN EV POWERTRAIN:
──────────────────────────────────────────────────────────────
DID     │ Name                     │ Length │ Format
──────────────────────────────────────────────────────────────
0xF190  │ VIN                      │ 17 B   │ ASCII string
0xF18C  │ ECU Serial Number        │ 20 B   │ ASCII
0xF188  │ ECU SW Version           │ 4 B    │ XX.XX.XX.XX
0xF186  │ Active Diagnostic Session│ 1 B    │ 0x01/0x02/0x03
0xF101  │ Battery SoC              │ 2 B    │ 0.5%/bit
0xF102  │ Battery Voltage          │ 2 B    │ 0.1V/bit
0xF103  │ Battery Current          │ 2 B    │ 0.1A/bit, signed
0xF104  │ Battery Max Cell Temp    │ 1 B    │ 1°C/bit, −40 offset
0xF105  │ BMS Fault Code           │ 2 B    │ bitmap
0xF110  │ Motor Speed              │ 2 B    │ 1 RPM/bit, signed
0xF111  │ Motor Torque             │ 2 B    │ 0.1Nm/bit, signed
0xF120  │ Charging Status          │ 1 B    │ enum
0xF121  │ Charge Power             │ 2 B    │ 10W/bit
0xF130  │ DC Link Voltage          │ 2 B    │ 0.1V/bit
0xFD01  │ Isolation Resistance     │ 2 B    │ 100Ω/bit

EXAMPLE — READ BATTERY SoC:
Request:  22 F1 01
Response: 62 F1 01 A8 00
  Data = 0x00A8 = 168 decimal
  Physical = 168 × 0.5 = 84.0%
  → BMS_SoC = 84.0%
```

---

## 8.6 READ DTC INFORMATION (SID 0x19)

```
SUB-FUNCTIONS:
──────────────────────────────────────────────────────────────
0x01 = reportNumberOfDTCByStatusMask
  Request:  19 01 08           (report count, status=confirmedDTC)
  Response: 59 01 FF 00 03     (3 DTCs found, formatID=0xFF)

0x02 = reportDTCByStatusMask
  Request:  19 02 08           (read all confirmed DTCs)
  Response: 59 02 08           (header)
              0A 80 00 2F      (DTC 0x0A8000, status=0x2F)
              0A 00 02 28      (DTC 0x0A0002, status=0x28)
              0C 00 01 2B      (DTC 0x0C0001, status=0x2B)

0x06 = reportDTCExtDataRecordByDTCNumber
  Request:  19 06 0A 80 00 FF  (read extended data for DTC 0x0A8000)
  Response: 59 06 0A 80 00 2F  (DTC + status)
              01               (extended data record number 0x01)
              0F               (occurrence counter = 15 times)
              05               (age = 5 operation cycles)

DTC STATUS BYTE BREAKDOWN:
  Bit 7: warningIndicatorRequested   (MIL lamp on)
  Bit 6: testNotCompletedThisOpCycle
  Bit 5: testFailedSinceLastClear
  Bit 4: testNotCompletedSinceLastClear
  Bit 3: confirmedDTC                ← most important!
  Bit 2: pendingDTC
  Bit 1: testFailedThisOpCycle
  Bit 0: testFailed                  ← currently failing

Example 0x2F = 0010 1111:
  Bits 0,1,2,3,5 set = testFailed + testFailedThisOp + pending + confirmed + failedSinceLastClear
  → This DTC is currently ACTIVE and CONFIRMED
```

---

## 8.7 ROUTINE CONTROL (SID 0x31)

```
ROUTINE TYPES:
  0x01 = startRoutine
  0x02 = stopRoutine
  0x03 = requestRoutineResults

COMMON EV ROUTINES:
──────────────────────────────────────────────────────────────
Routine ID │ Name                  │ Description
──────────────────────────────────────────────────────────────
0x0200     │ BMS Self Test         │ Run internal BMS diagnostic
0x0201     │ Cell Balancing        │ Force cell balancing
0x0202     │ Isolation Test        │ Run isolation resistance test
0x0300     │ Inverter Self Test    │ Check gate driver integrity
0x0400     │ Charging Self Test    │ OBC pre-test before charging
0xFF00     │ Check Programming     │ Validate flash after programming
0xE101     │ Learn BMS Capacity    │ Recalibrate SoH

EXAMPLE — Isolation Test Routine:
Request (start):  31 01 02 02   (startRoutine 0x0202)
Response:         71 01 02 02   (routine started)

Request (results): 31 03 02 02  (requestRoutineResults 0x0202)
Response:          71 03 02 02 01 [R_pos_H][R_pos_L][R_neg_H][R_neg_L]
  01 = routine completed
  R_pos = positive isolation resistance (kΩ)
  R_neg = negative isolation resistance (kΩ)
  
Example: 71 03 02 02 01 01 F4 01 F4
  R_pos = 0x01F4 = 500 kΩ (500 × 100Ω/bit = 50 MΩ → way above limit → OK)
  R_neg = 0x01F4 = 500 kΩ → OK
```

---

## 8.8 COMMUNICATION CONTROL (SID 0x28)

```
This service enables/disables CAN message Tx/Rx.
Useful during EOL programming to prevent interference.

Request:  28 [controlType] [communicationType]
  controlType:
    0x00 = enableRxAndTx
    0x01 = enableRxAndDisableTx
    0x02 = disableRxAndEnableTx
    0x03 = disableRxAndTx

  communicationType: which messages to affect
    0x01 = application layer messages
    0x02 = network management messages
    0x03 = both

EXAMPLE — Disable all Tx during programming:
  Request:  28 03 01     (disable Rx and Tx of application messages)
  Response: 68 03

  → ECU stops sending periodic CAN messages
  → Only diagnostic (UDS) communication active
  → Required before ECU reprogramming to avoid bus overload
```

---

## 8.9 UDS TEST CASES

### 8.9.1 BMS UDS Validation Test Suite

```
TEST SUITE: BMS_UDS_Validation
Requirements: SysRS-BMS-DIAG-001 through -020

TC-BMS-UDS-001: Default Session Access
  Precondition: ECU powered, CAN bus active
  Step 1: Send 10 01 (DiagSession Default)
  Step 2: Verify response 50 01
  Step 3: Verify P2 timeout value in response
  Expected: Positive response within 50ms
  Pass criteria: Response = 50 01 [P2_H][P2_L][P2ext_H][P2ext_L]

TC-BMS-UDS-002: Extended Session Access  
  Precondition: Default session active
  Step 1: Send 10 03 (DiagSession Extended)
  Step 2: Verify response 50 03
  Expected: Positive response, session = 0x03
  Pass criteria: Response starts with 50 03

TC-BMS-UDS-003: VIN Readback
  Precondition: Default session active
  Step 1: Send 22 F1 90
  Step 2: Verify response starts with 62 F1 90
  Step 3: Verify 17 ASCII bytes follow
  Step 4: Verify VIN matches vehicle documentation
  Expected: VIN = "WDB123456XXXXXXX1"
  Pass criteria: Length=17, ASCII, matches expected

TC-BMS-UDS-004: BMS SoC DID Readback
  Precondition: Extended session active, HV on
  Step 1: Send 22 F1 01
  Step 2: Decode response: Physical = raw × 0.5
  Step 3: Compare to CAN bus BMS_Status::BMS_SoC
  Expected: DID SoC ± 1% of CAN SoC
  Pass criteria: |DID_SoC - CAN_SoC| ≤ 1.0%

TC-BMS-UDS-005: Security Access Level 1
  Precondition: Extended session active
  Step 1: Send 27 01 (RequestSeed)
  Step 2: Receive 67 01 [4-byte seed]
  Step 3: Calculate key: key = (seed XOR 0xBEEF1234) + 0x5A5A5A5A
  Step 4: Send 27 02 [key]
  Expected: Response 67 02 (access granted)
  Pass criteria: Response = 67 02

TC-BMS-UDS-006: DTC Reading — No Faults
  Precondition: Clean vehicle state (no injected faults)
  Step 1: Send 14 FF FF FF (ClearDTC)
  Step 2: Wait 2 seconds
  Step 3: Send 19 02 FF (ReadDTC all)
  Expected: No confirmed DTCs
  Pass criteria: DTC list empty OR only monitor-not-complete entries

TC-BMS-UDS-007: DTC Setting After Fault Injection
  Precondition: Extended session, clean DTC state
  Step 1: Clear DTCs: 14 FF FF FF
  Step 2: Inject BMS overvoltage condition via hardware fault simulator
  Step 3: Wait for BMS to confirm fault (typically 3 cycles × 10ms = 30ms)
  Step 4: Read DTC: 19 02 08 (read confirmed DTCs)
  Expected: DTC 0x0A0001 (cell overvoltage) present with status bit 3 set
  Pass criteria: DTC found with confirmedDTC bit = 1

TC-BMS-UDS-008: ECU Soft Reset
  Precondition: Extended session active
  Step 1: Record current SoC value
  Step 2: Send 11 03 (SoftReset)
  Step 3: Wait 2 seconds for ECU to restart
  Step 4: Send 10 01 (DefaultSession) to verify ECU alive
  Step 5: Read SoC DID: 22 F1 01
  Expected: ECU recovers, SoC retained (persistent memory)
  Pass criteria: SoC after reset ± 2% of pre-reset value

TC-BMS-UDS-009: TesterPresent Session Keep-Alive
  Precondition: Extended session active
  Step 1: Enter extended session: 10 03
  Step 2: Wait 4.5 seconds (near S3 timeout of 5s)
  Step 3: Send 3E 00 (TesterPresent)
  Step 4: Wait 4.5 seconds more
  Step 5: Send 3E 00 again
  Step 6: Verify still in extended session: read 22 F1 86 → should return 03
  Expected: Extended session maintained with TesterPresent
  Pass criteria: DID 0xF186 returns 0x03 throughout test

TC-BMS-UDS-010: Session Return After Timeout
  Precondition: Extended session active
  Step 1: Enter extended session: 10 03
  Step 2: Wait 6 seconds (past S3 timeout)
  Step 3: Attempt service only available in extended session
  Step 4: Verify service refused
  Expected: ECU returns to Default session after 5s without TesterPresent
  Pass criteria: NRC 0x22 (conditionsNotCorrect) returned for extended-only service
```

---

## 8.10 NEGATIVE RESPONSE CODES (NRC)

```
NRC TABLE (ISO 14229):
──────────────────────────────────────────────────────────────
NRC  │ Hex │ Name                         │ Common Cause
──────────────────────────────────────────────────────────────
0x10 │     │ generalReject                │ Unknown error
0x11 │     │ serviceNotSupported          │ SID not implemented
0x12 │     │ subFunctionNotSupported      │ Invalid sub-function
0x13 │     │ incorrectMessageLengthOrFormat│ Wrong byte count
0x14 │     │ responseTooLong              │ Data > max transfer size
0x21 │     │ busyRepeatRequest            │ ECU busy, retry
0x22 │     │ conditionsNotCorrect         │ Wrong session, wrong state
0x24 │     │ requestSequenceError         │ Step out of order
0x25 │     │ noResponseFromSubnetComponent│ Sub-ECU timeout
0x26 │     │ failurePreventsExecOfReq     │ Fault prevents service
0x31 │     │ requestOutOfRange            │ Invalid DID/address
0x33 │     │ securityAccessDenied         │ Not unlocked
0x35 │     │ invalidKey                   │ Wrong seed/key
0x36 │     │ exceededNumberOfAttempts     │ Too many failed attempts
0x37 │     │ requiredTimeDelayNotExpired  │ Must wait for delay timer
0x70 │     │ uploadDownloadNotAccepted    │ Programming condition fail
0x71 │     │ transferDataSuspended        │ Flash write error
0x72 │     │ generalProgrammingFailure    │ Programming error
0x73 │     │ wrongBlockSequenceCounter   │ Block sequence error
0x78 │     │ requestCorrectlyReceivedResponsePending │ Still processing
0x7E │     │ subFunctionNotSupportedInActiveSession  │ Wrong session
0x7F │     │ serviceNotSupportedInActiveSession      │ Wrong session

COMMON SCENARIOS:
NRC 0x22 — Service called in wrong session
  → Enter Extended session first (10 03), then retry

NRC 0x33 — Security access required
  → Perform seed/key exchange (27 01/02) before sensitive writes

NRC 0x78 — Response pending (ECU still processing)
  → Send 3E 80 (keep alive, no response needed)
  → Wait and resend original request

NRC 0x35 — Invalid key
  → Verify seed/key algorithm matches ECU specification
  → Check endianness of seed bytes
```

---

## 8.11 PYTHON UDS EXAMPLE — COMPLETE DTC VALIDATION

```python
# tests/uds/test_dtc_validation.py
"""
Complete UDS DTC validation test suite for BMS ECU.
"""

import pytest
import time
from core.uds_client import UDSClient


def calculate_security_key(seed: bytes) -> bytes:
    """
    BMS Level 1 security access key calculation.
    NOTE: Real algorithm is confidential — this is an example.
    """
    import struct
    seed_int = int.from_bytes(seed, byteorder='big')
    key_int = ((seed_int ^ 0xBEEF1234) + 0x5A5A5A5A) & 0xFFFFFFFF
    return key_int.to_bytes(4, byteorder='big')


class TestDTCValidation:
    """DTC validation test cases per ISO 14229."""
    
    def setup_method(self):
        """Setup before each test."""
        # Setup UDS connection (fixture would be better, simplified here)
        pass

    def test_clear_and_verify_empty(self, uds_bms):
        """TC-BMS-UDS-006: Verify no DTCs after clear."""
        # Clear all DTCs
        assert uds_bms.clear_dtc(0xFFFFFF), "ClearDTC failed"
        time.sleep(0.5)
        
        # Read confirmed DTCs
        dtcs = uds_bms.read_dtc_by_status(0x08)  # confirmeDTC bit only
        confirmed = [d for d in dtcs if d['confirmed']]
        
        assert len(confirmed) == 0, \
            f"DTCs present after clear: {[d['dtc_hex'] for d in confirmed]}"

    def test_security_access(self, uds_bms):
        """TC-BMS-UDS-005: Security access level 1."""
        # Enter extended session first
        assert uds_bms.change_session(0x03), "Extended session failed"
        
        # Perform security access
        result = uds_bms.security_access(
            level=0x01,
            seed_to_key_func=calculate_security_key
        )
        assert result, "Security access failed"
        
        # Return to default
        uds_bms.change_session(0x01)

    def test_vin_readback(self, uds_bms):
        """TC-BMS-UDS-003: VIN DID read and validate."""
        data = uds_bms.read_data_by_id(0xF190)
        
        assert data is not None, "ReadDID 0xF190 returned no data"
        assert len(data) == 17, f"VIN length = {len(data)}, expected 17"
        
        vin_str = data.decode('ascii', errors='replace')
        print(f"VIN: {vin_str}")
        
        # Basic VIN format check
        assert all(c.isalnum() for c in vin_str), f"VIN contains invalid chars: {vin_str}"

    def test_tester_present_keepalive(self, uds_bms):
        """TC-BMS-UDS-009: Session maintained with TesterPresent."""
        assert uds_bms.change_session(0x03), "Extended session failed"
        
        for _ in range(3):
            time.sleep(4.5)  # Wait near S3 timeout
            assert uds_bms.tester_present(), "TesterPresent failed"
        
        # Verify still in extended session
        data = uds_bms.read_data_by_id(0xF186)
        assert data is not None and data[0] == 0x03, \
            f"Session changed unexpectedly: {data}"
```

---

## SECTION 8 SUMMARY

| Service | SID | Primary Use in EV Testing |
|---------|-----|--------------------------|
| DiagnosticSessionControl | 0x10 | Enter extended/programming session |
| ECUReset | 0x11 | Reset ECU, verify recovery |
| ClearDTC | 0x14 | Clean fault state before testing |
| ReadDTCInformation | 0x19 | Read and validate fault codes |
| ReadDataByIdentifier | 0x22 | Read ECU parameter values |
| SecurityAccess | 0x27 | Unlock protected write access |
| CommunicationControl | 0x28 | Disable messages during programming |
| WriteDataByIdentifier | 0x2E | Write calibration parameters |
| RoutineControl | 0x31 | Run diagnostics routines |
| TesterPresent | 0x3E | Maintain extended session |

Key tool support:
- **CANoe**: Full UDS via Diagnostics Console or CAPL scripting
- **Python**: `udsoncan` library with `python-can` transport
- **Vector CANdela**: Advanced ODX-based diagnostics

---

*Next: Section 9 — Battery, Motor, Inverter, OBC Testing*
