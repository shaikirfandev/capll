# ADAS ECU — Test Case Document with Traceability
**Project:** ADAS ECU Validation Test Suite  
**Document ID:** TCD-ADAS-001  
**Version:** 1.0  
**Date:** 2026-07-08  
**Author:** Automotive Test Validation Team  
**Status:** Active  

---

## 1. Scope

This document defines the formal test cases for the ADAS (Advanced Driver Assistance Systems)
ECU validation suite. Coverage spans UDS diagnostic services, sensor calibration routines, DTC
management, functional signal validation, and negative/error handling.

All test cases are linked to requirements and implemented in `ecu_test_suite/tests/adas/` and
`ecu_test_suite/tests/common/`.

---

## 2. Reference Documents

| Ref | Document |
|-----|----------|
| [ISO-14229] | ISO 14229-1:2020 — Unified Diagnostic Services (UDS) |
| [ISO-26262] | ISO 26262-1:2018 — Road vehicles Functional Safety |
| [AUTOSAR] | AUTOSAR DCM R22-11 — Diagnostic Communication Manager |
| [ISO-15765] | ISO 15765-2:2016 — Road vehicles, UDS on CAN (ISO-TP) |
| [SRS-ADAS] | ADAS ECU Software Requirements Specification (supplier document) |
| [DTC-CAT] | ADAS ECU DTC Catalogue v2.3 |

---

## 3. Requirements Summary

### 3.1 System Requirements

| Req ID | Description | Source | ASIL |
|--------|-------------|--------|------|
| SYS_REQ_ADAS_001 | ADAS ECU shall support UDS diagnostic access over CAN | SRS-ADAS §3.1 | B |
| SYS_REQ_ADAS_002 | ECU shall transition between default, extended, and programming sessions | SRS-ADAS §3.2 | B |
| SYS_REQ_ADAS_003 | ECU shall implement security access with seed/key mechanism | SRS-ADAS §3.3 | B |
| SYS_REQ_ADAS_004 | ECU shall expose all sensor calibration status via diagnostic DIDs | SRS-ADAS §4.1 | B |
| SYS_REQ_ADAS_005 | ECU shall generate and store DTCs for all monitored sensor faults | SRS-ADAS §5.1 | B |
| SYS_REQ_ADAS_006 | ECU shall support routine control for sensor calibration triggers | SRS-ADAS §4.2 | A |
| SYS_REQ_ADAS_007 | ECU shall expose functional signal states via DIDs | SRS-ADAS §4.3 | A |
| SYS_REQ_ADAS_008 | ECU shall return correct NRCs for all invalid requests | SRS-ADAS §3.5 | A |

### 3.2 Functional Requirements

| Req ID | Description | Source |
|--------|-------------|--------|
| FUNC_REQ_ADAS_001 | Camera calibration status shall be readable via DID 0x2001 | SRS-ADAS §4.1.1 |
| FUNC_REQ_ADAS_002 | Radar calibration status shall be readable via DID 0x2002 | SRS-ADAS §4.1.2 |
| FUNC_REQ_ADAS_003 | ACC state signal shall be readable via DID 0x2011 | SRS-ADAS §4.3.1 |
| FUNC_REQ_ADAS_004 | AEB state signal shall be readable via DID 0x2012 | SRS-ADAS §4.3.2 |
| FUNC_REQ_ADAS_005 | Object detection flag shall be a valid boolean DID | SRS-ADAS §4.3.3 |
| FUNC_REQ_ADAS_006 | Camera calibration shall be triggerable via routine 0x0201 | SRS-ADAS §4.2.1 |
| FUNC_REQ_ADAS_007 | Radar calibration shall be triggerable via routine 0x0202 | SRS-ADAS §4.2.2 |
| FUNC_REQ_ADAS_008 | Sensor blockage DTC 0xC11003 shall be generated on blockage | DTC-CAT §2.1 |
| FUNC_REQ_ADAS_009 | Radar misalignment DTC 0xC12002 shall be generated on misalignment | DTC-CAT §2.2 |
| FUNC_REQ_ADAS_010 | VIN shall be readable via standard DID 0xF190 | ISO-14229 §D.1 |

### 3.3 Safety Requirements

| Req ID | Description | ISO 26262 Ref | ASIL |
|--------|-------------|---------------|------|
| SAFE_REQ_ADAS_001 | Sensor calibration status shall be verifiable without entering programming session | ISO 26262-6 §7.4 | B |
| SAFE_REQ_ADAS_002 | Security lockout shall be enforced after 3 consecutive wrong keys | ISO 26262-4 §6.5 | B |
| SAFE_REQ_ADAS_003 | DTC for sensor communication loss shall be confirmed within one drive cycle | ISO 26262-5 §8.3 | B |
| SAFE_REQ_ADAS_004 | ECU reset shall not clear confirmed DTCs without explicit ClearDTC service | ISO 26262-5 §8.4 | A |

---

## 4. Test Cases

---

### TC_ADAS_001: Enter Default Diagnostic Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_001 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_001, SYS_REQ_ADAS_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_default_session_entry` |

**Preconditions:**
- ECU powered; CAN bus at 500 kbps
- Vector interface connected and initialised

**Test Steps:**
1. Send `DiagnosticSessionControl(0x01 — defaultSession)`
2. Capture the response frame

**Expected Result:**
- ECU responds with positive response `0x50 0x01`
- `response.positive == True`
- `response.service_id == 0x10`

**Pass Criteria:** Response is positive within P2 timeout (50 ms)

---

### TC_ADAS_002: Enter Extended Diagnostic Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_002 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_001, SYS_REQ_ADAS_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_extended_session_entry` |

**Preconditions:** ECU in default session

**Test Steps:**
1. Send `DiagnosticSessionControl(0x03 — extendedDiagnosticSession)`
2. Capture response

**Expected Result:**
- Positive response `0x50 0x03`
- Response data bytes 1–4 carry valid P2/P2* timing

**Pass Criteria:** Positive response; P2_ms > 0

---

### TC_ADAS_003: Full Session Cycle (Default → Extended → Programming → Default)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_003 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_session_transitions_full_cycle` |

**Preconditions:** ECU in any session

**Test Steps:**
1. `DSC(defaultSession)` → verify positive
2. `DSC(extendedDiagnosticSession)` → verify positive
3. `DSC(programmingSession)` → verify positive
4. `DSC(defaultSession)` → verify positive

**Expected Result:** All four steps return positive response

**Pass Criteria:** All four `response.positive == True`

---

### TC_ADAS_004: Session Timing Parameters Verification (P2 / P2*)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_004 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_extended_session_entry` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. Parse response bytes: `P2 = (data[1]<<8)|data[2]`; `P2* = ((data[3]<<8)|data[4]) * 10`

**Expected Result:** `P2_ms > 0`; `P2*_ms >= P2_ms`

**Pass Criteria:** Both timing values are non-zero and consistent with ISO 14229

---

### TC_ADAS_005: Hard ECU Reset

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_005 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x11 ECUReset |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_hard_reset_returns_to_default_session` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `ECUReset(0x01 — hardReset)`
2. Wait 2 s for ECU boot
3. `DSC(defaultSession)`

**Expected Result:** Hard reset accepted; ECU returns to default session after boot

**Pass Criteria:** Both calls return positive response

---

### TC_ADAS_006: Soft ECU Reset in Extended Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_006 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x11 ECUReset |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_soft_reset_in_extended_session` |

**Preconditions:** ECU in extended diagnostic session

**Test Steps:**
1. `ECUReset(0x03 — softReset)`
2. Capture response

**Expected Result:** Positive response `0x51 0x03`

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_007: Security Access — Request Seed (Level 0x01)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_007 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.security` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_security_access_unlock_extended_session` |

**Preconditions:** ECU in extended diagnostic session

**Test Steps:**
1. `SecurityAccess(0x01 — requestSeed)`
2. Parse response: seed bytes at data[1:]

**Expected Result:** Positive response `0x67 0x01 <seed_bytes>`; seed is non-zero

**Pass Criteria:** `response.positive == True`; at least one non-zero seed byte

---

### TC_ADAS_008: Security Access — Correct Key Grants Access

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_008 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.security` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_security_access_unlock_extended_session` |

**Preconditions:** ECU in extended session; seed obtained via TC_ADAS_007

**Test Steps:**
1. `SecurityAccess(0x01)` → obtain seed
2. Compute key using configured algorithm
3. `SecurityAccess(0x02 — sendKey, <key>)`

**Expected Result:** ECU responds `0x67 0x02`; access granted

**Pass Criteria:** `perform_security_access()` returns `True`

---

### TC_ADAS_009: Security Access — Wrong Key Returns NRC 0x35

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_009 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.security` `@pytest.mark.negative` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` (negative stub) |

**Preconditions:** ECU in extended session; seed obtained

**Test Steps:**
1. `SecurityAccess(0x01)` → obtain seed
2. Send deliberately wrong key `0x00000000`
3. `SecurityAccess(0x02 — sendKey, 0x00000000)`

**Expected Result:** NRC `0x7F 0x27 0x35` (InvalidKey)

**Pass Criteria:** `response.nrc == 0x35`

---

### TC_ADAS_010: Security Lockout After 3 Failed Key Attempts (NRC 0x36)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_010 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SAFE_REQ_ADAS_002, SYS_REQ_ADAS_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.security` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `SA(0x01)` → seed; send wrong key 1 → NRC 0x35
2. `SA(0x01)` → seed; send wrong key 2 → NRC 0x35
3. `SA(0x01)` → seed; send wrong key 3

**Expected Result:** After 3rd wrong key: NRC `0x7F 0x27 0x36` (ExceededNumberOfAttempts)

**Pass Criteria:** `response.nrc == 0x36` on final attempt

---

### TC_ADAS_011: Read Software Version DID (0xF189)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_011 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_001, FUNC_REQ_ADAS_010 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF189 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `ReadDataByIdentifier(0xF189)`
2. Capture response data

**Expected Result:** Positive response; data ≥ 4 bytes; software version string

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 4`

---

### TC_ADAS_012: Read Hardware Version DID (0xF191)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_012 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF191 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `ReadDataByIdentifier(0xF191)`

**Expected Result:** Positive response; HW part number string

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_013: Read VIN DID (0xF190)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_013 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_010 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF190 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session; VIN programmed at EOL

**Test Steps:**
1. `ReadDataByIdentifier(0xF190)`
2. Verify response length (2 DID echo + 17 VIN chars)

**Expected Result:** 19-byte response; valid ASCII VIN string

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 4`

---

### TC_ADAS_014: Read Camera Calibration Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_014 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_001, SAFE_REQ_ADAS_001 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_camera_calibration_status_did` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. `ReadDataByIdentifier(0x2001 — camera_calibration_status)`
3. Parse status byte: `0x00 = uncalibrated`, `0x01 = calibrated`

**Expected Result:** Positive response; status byte in `{0x00, 0x01}`

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 2`

---

### TC_ADAS_015: Read Radar Calibration Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_015 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_002, SAFE_REQ_ADAS_001 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2002 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_radar_calibration_status_did` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. `ReadDataByIdentifier(0x2002 — radar_calibration_status)`

**Expected Result:** Positive response; status byte in `{0x00, 0x01}`

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_016: Read ACC State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_016 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_003, SYS_REQ_ADAS_007 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2011 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_acc_state_signal_read` |

**Preconditions:** ECU in extended session; CAN signals active

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. `ReadDataByIdentifier(0x2011 — acc_state)`
3. Parse: `0x00 = off`, `0x01 = active`, `0x02 = override`

**Expected Result:** State byte ∈ `{0x00, 0x01, 0x02}`

**Pass Criteria:** `response.positive == True`; state in valid range

---

### TC_ADAS_017: Read AEB State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_017 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2012 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `RDBI(0x2012 — aeb_state)`
2. Verify state byte is valid

**Expected Result:** Positive response; state byte ∈ `{0x00, 0x01, 0x02}`

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_018: Read Object Detection Flag DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_018 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_005 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2010 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_object_detection_flag_read` |

**Preconditions:** ECU in extended session; no obstruction in sensor field

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. `RDBI(0x2010 — object_detection_flag)`
3. Verify: `0x00 = clear`, `0x01 = detected`

**Expected Result:** Flag byte ∈ `{0x00, 0x01}`

**Pass Criteria:** `response.positive == True`; boolean value confirmed

---

### TC_ADAS_019: Read Invalid DID Returns NRC 0x31

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_019 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x0000 (undefined) |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/common/test_uds_common.py::test_negative_response_for_invalid_did` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `RDBI(0x0000)` — unallocated DID

**Expected Result:** NRC `0x7F 0x22 0x31` (RequestOutOfRange)

**Pass Criteria:** `response.positive == False`; `response.nrc == 0x31`

---

### TC_ADAS_020: Write Read-Only DID Returns Negative Response

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_020 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | DID 0xF189 (software_version — read-only) |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session with security access

**Test Steps:**
1. `WDBI(0xF189, data=b"\x01\x02\x03")`

**Expected Result:** NRC `0x7F 0x2E 0x31` or `0x22`

**Pass Criteria:** `response.positive == False`

---

### TC_ADAS_021: Camera Calibration Routine Start

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_021 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_006, SYS_REQ_ADAS_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0201 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_camera_calibration_routine_start` |

**Preconditions:** ECU in extended session; security access granted; calibration target in field

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. `SecurityAccess(level=0x01)` — unlock
3. `RoutineControl(startRoutine=0x01, routineId=0x0201)`
4. Verify response status byte = 0x00

**Expected Result:** Positive response; routine status = 0x00 (started/OK)

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_022: Camera Calibration Routine Result Request

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_022 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0201 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Camera calibration routine started (TC_ADAS_021)

**Test Steps:**
1. `RoutineControl(requestRoutineResults=0x03, routineId=0x0201)`
2. Parse result: status byte at data[3]

**Expected Result:** Positive response; result status = 0x00 (pass)

**Pass Criteria:** `response.positive == True`; status byte = 0x00

---

### TC_ADAS_023: Radar Calibration Routine Start

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_023 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_007 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0202 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` `@pytest.mark.functional` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session; security access granted

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0202)`

**Expected Result:** Positive response; routine started

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_024: Routine Without Security Access Returns NRC 0x33

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_024 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_003, SYS_REQ_ADAS_008 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0201 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.security` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session; security access NOT granted

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0201)` without prior security unlock

**Expected Result:** NRC `0x7F 0x31 0x33` (SecurityAccessDenied)

**Pass Criteria:** `response.nrc == 0x33`

---

### TC_ADAS_025: Read All DTCs — Status Mask 0xFF

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_025 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | All DTCs |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_no_active_sensor_dtcs_on_clean_ecu` |

**Preconditions:** ECU on clean bench; DTCs cleared

**Test Steps:**
1. `ClearDiagnosticInformation(0xFFFFFF)`
2. `ReadDTCInformation(subFn=0x02, statusMask=0xFF)`
3. Parse DTC records

**Expected Result:** Zero confirmed DTCs on clean bench ECU

**Pass Criteria:** `len(snapshot.confirmed_dtcs) == 0`

---

### TC_ADAS_026: Read Confirmed DTCs Only (Mask 0x08)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_026 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | Confirmed DTCs |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Clean ECU; DTCs cleared

**Test Steps:**
1. `ReadDTCInformation(subFn=0x02, statusMask=0x08)`

**Expected Result:** Empty DTC list; no confirmed DTCs

**Pass Criteria:** DTC list empty

---

### TC_ADAS_027: Camera Sensor Blockage DTC (0xC11003) Verification

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_027 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_008, SAFE_REQ_ADAS_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC11003 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection Positive |
| **Automation File** | `tests/adas/test_adas_features.py::test_camera_blockage_dtc_injection_and_read` |

**Preconditions:** Mock mode; synthetic DTC injected OR physical blockage on real HW

**Test Steps:**
1. Inject / simulate camera blockage condition
2. `ReadDTCInformation(statusMask=0xFF)`
3. Check for DTC 0xC11003 in response

**Expected Result:** DTC 0xC11003 present; status = confirmed

**Pass Criteria:** `0xC11003 in snapshot.codes()`; `is_confirmed == True`

---

### TC_ADAS_028: Radar Misalignment DTC (0xC12002) Verification

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_028 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_009, SAFE_REQ_ADAS_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC12002 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Radar misalignment condition simulated

**Test Steps:**
1. Simulate misalignment (rotate radar target / stub DTC)
2. `ReadDTCInformation(statusMask=0xFF)`

**Expected Result:** DTC 0xC12002 present; `confirmedDTC` bit set

**Pass Criteria:** `0xC12002 in snapshot.codes()`

---

### TC_ADAS_029: Camera Communication Loss DTC (0xC11001)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_029 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_008, SAFE_REQ_ADAS_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC11001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Camera harness disconnected or CAN signal loss simulated

**Test Steps:**
1. Disconnect camera harness / inject fault
2. `ReadDTCInformation(statusMask=0x08)`

**Expected Result:** DTC 0xC11001 confirmed

**Pass Criteria:** `0xC11001 in snapshot.confirmed_dtcs codes`

---

### TC_ADAS_030: Clear All DTCs (0xFFFFFF)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_030 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_004 |
| **UDS Service** | 0x14 ClearDiagnosticInformation |
| **DID / DTC** | Group 0xFFFFFF |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_clear_dtc_with_no_active_faults` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `ClearDiagnosticInformation(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0xFF)`

**Expected Result:** Clear returns positive; subsequent read shows 0 confirmed DTCs

**Pass Criteria:** `clear_resp.positive == True`; `len(snapshot.confirmed_dtcs) == 0`

---

### TC_ADAS_031: DTC Diff — New DTC After Sensor Fault

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_031 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC11003 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Clean DTC snapshot taken before stimulus

**Test Steps:**
1. Take `snapshot_before = dtc_manager.read_all()`
2. Inject camera blockage fault
3. Take `snapshot_after = dtc_manager.read_all()`
4. `diff = dtc_manager.diff(snapshot_before, snapshot_after)`

**Expected Result:** diff list contains exactly 1 new DTC (0xC11003)

**Pass Criteria:** `len(diff) == 1`; `diff[0].dtc_code == 0xC11003`

---

### TC_ADAS_032: TesterPresent Keep-Alive in Extended Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_032 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_tester_present_default_session` |

**Preconditions:** ECU in extended diagnostic session

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. Send 5 × `TesterPresent(suppress=True)` at 1 s intervals

**Expected Result:** All 5 responses positive; session not dropped

**Pass Criteria:** All `response.positive == True`

---

### TC_ADAS_033: Communication Control — Disable TX Messages

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_033 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x28 CommunicationControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_communication_control_disable_and_restore` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `CommunicationControl(0x02 — disableRxEnableTx, commType=0x01)`
2. Verify positive response

**Expected Result:** `response.positive == True`

**Pass Criteria:** `response.positive == True`

---

### TC_ADAS_034: Communication Control — Re-Enable All Messages

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_034 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x28 CommunicationControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py::test_communication_control_disable_and_restore` |

**Preconditions:** TX messages disabled (TC_ADAS_033)

**Test Steps:**
1. `CommunicationControl(0x00 — enableRxAndTx, commType=0x01)`

**Expected Result:** `response.positive == True`

**Pass Criteria:** `response.positive == True`; normal CAN TX restored

---

### TC_ADAS_035: NRC 0x22 — Conditions Not Correct

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_035 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session (calibration not allowed)

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0201)` in default session

**Expected Result:** NRC `0x7F 0x31 0x22` (ConditionsNotCorrect)

**Pass Criteria:** `response.nrc == 0x22`

---

### TC_ADAS_036: NRC 0x7F — Service Not Supported in Active Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_036 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `SecurityAccess(requestSeed, level=0x01)` in default session

**Expected Result:** NRC `0x7F 0x27 0x7F` (ServiceNotSupportedInActiveSession)

**Pass Criteria:** `response.nrc == 0x7F`

---

### TC_ADAS_037: EOL Self-Test Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_037 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0210 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Extended session; security unlock; all sensors connected

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0210 — eol_self_test)`
2. Poll results via `requestRoutineResults`

**Expected Result:** Status = 0x00 (all sensors pass)

**Pass Criteria:** `response.positive == True`; result status = 0x00

---

### TC_ADAS_038: DTC Status Bit Decoding — confirmedDTC Bit

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_038 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC11001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** DTC with status 0x09 injected

**Test Steps:**
1. `ReadDTCInformation(statusMask=0xFF)` with injected DTC status=0x09
2. Check `dtc_record.is_confirmed` and `dtc_record.is_test_failed`

**Expected Result:** Both `is_confirmed == True` and `testFailed` in `active_bits()`

**Pass Criteria:** Bit 3 (confirmedDTC) and Bit 0 (testFailed) both set

---

### TC_ADAS_039: Multiple Active DTCs — 3 Simultaneous Faults

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_039 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTCs 0xC11001, 0xC12001, 0xU01001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Three simultaneous faults injected

**Test Steps:**
1. Inject 3 DTCs in one synthetic response
2. `ReadDTCInformation(statusMask=0xFF)`

**Expected Result:** Snapshot contains exactly 3 DTC records

**Pass Criteria:** `len(snapshot.records) == 3`

---

### TC_ADAS_040: Key-Off-On Reset

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_040 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x11 ECUReset |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `ECUReset(0x02 — keyOffOnReset)`
2. Wait for power cycle simulation
3. `DSC(defaultSession)`

**Expected Result:** Both calls positive; ECU resumes operation

**Pass Criteria:** `reset_resp.positive == True`

---

### TC_ADAS_041: Programming Session — Security Access Level 3

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_041 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_002, SYS_REQ_ADAS_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.security` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in programming session

**Test Steps:**
1. `DSC(programmingSession)`
2. `SecurityAccess(requestSeed, level=0x11)` (level 3)
3. Compute key; `SecurityAccess(sendKey)`

**Expected Result:** Access granted at level 3

**Pass Criteria:** Key response positive

---

### TC_ADAS_042: TesterPresent with Suppress Response

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_042 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/common/test_uds_common.py` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `TesterPresent(suppressResponse=True)` — sub-fn 0x80

**Expected Result:** No response frame transmitted; session maintained

**Pass Criteria:** No NRC received; session alive confirmed by next RDBI

---

### TC_ADAS_043: Side Radar Communication Loss DTC (0xC13001)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_043 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC13001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Left side radar harness disconnected / fault injected

**Test Steps:**
1. Inject fault for DTC 0xC13001
2. `ReadDTCInformation(statusMask=0x08 — confirmed only)`

**Expected Result:** DTC 0xC13001 confirmed

**Pass Criteria:** `0xC13001 in snapshot.confirmed_dtcs codes`

---

### TC_ADAS_044: CAN Bus-Off DTC (0xU01001) After Network Fault

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_044 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xU01001 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** CAN bus-off condition injected via hardware or stub

**Test Steps:**
1. Inject CAN bus-off scenario
2. `ReadDTCInformation(statusMask=0xFF)`

**Expected Result:** DTC 0xU01001 present

**Pass Criteria:** DTC code in snapshot

---

### TC_ADAS_045: DTC Not Cleared by Soft Reset

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_045 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SAFE_REQ_ADAS_004 |
| **UDS Service** | 0x11 ECUReset, 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC11003 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** DTC 0xC11003 confirmed before reset

**Test Steps:**
1. Verify DTC 0xC11003 present: `ReadDTCInformation`
2. `ECUReset(softReset)`
3. `ReadDTCInformation(statusMask=0x08)` — confirmed only

**Expected Result:** DTC 0xC11003 still confirmed after soft reset

**Pass Criteria:** DTC persists in post-reset snapshot

---

### TC_ADAS_046: NRC 0x13 — Incorrect Message Length

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_046 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in extended session with security access

**Test Steps:**
1. `WDBI(0x3020, data=b"")` — zero-length data (invalid)

**Expected Result:** NRC `0x7F 0x2E 0x13` (IncorrectMessageLength)

**Pass Criteria:** `response.nrc == 0x13`

---

### TC_ADAS_047: NRC 0x12 — Sub-Function Not Supported

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_047 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `DSC(0x99)` — undefined session sub-function

**Expected Result:** NRC `0x7F 0x10 0x12` (SubFunctionNotSupported)

**Pass Criteria:** `response.nrc == 0x12`

---

### TC_ADAS_048: Frame Logger Captures UDS Transactions

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_048 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | All |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Framework Validation |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Mock mode active; `frame_logger` fixture used

**Test Steps:**
1. Execute `DSC(extendedDiagnosticSession)` + `RDBI(0x2001)`
2. Check `frame_logger` list contains 2 entries

**Expected Result:** `len(frame_logger) == 2`; entries have `service` and `response` keys

**Pass Criteria:** Transaction log populated correctly

---

### TC_ADAS_049: DID Read in Wrong Session (Programming for Default-Only DID)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_049 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_ADAS_008 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF189 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Some DIDs readable only in extended session

**Test Steps:**
1. `DSC(defaultSession)` — ensure lowest session
2. `RDBI(extended-only DID)` — stub NRC 0x7F

**Expected Result:** NRC 0x7F (ServiceNotSupportedInActiveSession)

**Pass Criteria:** `response.nrc == 0x7F`

---

### TC_ADAS_050: Functional Addressing TesterPresent (0x7DF)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_050 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Functional TX ID 0x7DF configured

**Test Steps:**
1. Send `TesterPresent(suppressResponse=True)` via functional address 0x7DF

**Expected Result:** No NRC; all ECUs maintain session

**Pass Criteria:** Session maintained on next RDBI

---

### TC_ADAS_051: Radar Calibration Status After Successful Calibration

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_051 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_ADAS_002, SAFE_REQ_ADAS_001 |
| **UDS Service** | 0x31 RoutineControl + 0x22 RDBI |
| **DID / DTC** | Routine 0x0202; DID 0x2002 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.functional` `@pytest.mark.regression` |
| **Test Type** | End-to-End Positive |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Extended session; security unlock; calibration target in place

**Test Steps:**
1. `RDBI(0x2002)` → verify `0x00` (uncalibrated before routine)
2. `RC(startRoutine, 0x0202)` → start calibration
3. `RC(requestResults, 0x0202)` → wait for completion
4. `RDBI(0x2002)` → verify `0x01` (calibrated)

**Expected Result:** Status changes from 0x00 to 0x01 after routine

**Pass Criteria:** Post-calibration RDBI returns `0x01`

---

### TC_ADAS_052: Pending DTC After Single Fault Occurrence

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_052 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xC12001 (pending) |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Single fault event (not enough cycles for confirmed)

**Test Steps:**
1. Inject single-event radar comm fault
2. `ReadDTCInformation(statusMask=0x04 — pending only)`

**Expected Result:** DTC 0xC12001 in pending status; `is_pending == True`

**Pass Criteria:** `0xC12001` present with `pendingDTC` bit set

---

### TC_ADAS_053: ACC State DID — Value Range Under Different Drive States

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_053 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_ADAS_003 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x2011 |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.functional` `@pytest.mark.regression` |
| **Test Type** | Boundary Value |
| **Automation File** | `tests/adas/test_adas_features.py::test_acc_state_signal_read` |

**Preconditions:** Various ACC states simulated via CAN signal injection

**Test Steps:**
1. Simulate ACC OFF → `RDBI(0x2011)` → verify `0x00`
2. Simulate ACC ACTIVE → `RDBI(0x2011)` → verify `0x01`
3. Simulate ACC OVERRIDE → `RDBI(0x2011)` → verify `0x02`

**Expected Result:** DID reflects correct state for each simulated condition

**Pass Criteria:** All three state reads return expected values

---

### TC_ADAS_054: ECU Boot Time After Hard Reset ≤ 2 s

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_054 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_ADAS_001 |
| **UDS Service** | 0x11 ECUReset + 0x10 DSC |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Performance |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** ECU powered from bench supply

**Test Steps:**
1. `ECUReset(hardReset)` — record timestamp T1
2. Poll `DSC(defaultSession)` at 200 ms intervals until positive
3. Record timestamp T2; compute boot_time = T2 - T1

**Expected Result:** `boot_time <= 2.0 s`

**Pass Criteria:** Boot time within spec

---

### TC_ADAS_055: Concurrent DTC Read During Active Calibration

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_ADAS_055 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_ADAS_005, SYS_REQ_ADAS_006 |
| **UDS Service** | 0x31 RoutineControl + 0x19 ReadDTCInformation |
| **DID / DTC** | Routine 0x0201; All DTCs |
| **pytest Marker** | `@pytest.mark.adas` `@pytest.mark.regression` |
| **Test Type** | Concurrency |
| **Automation File** | `tests/adas/test_adas_features.py` |

**Preconditions:** Extended session; security unlock

**Test Steps:**
1. Start camera calibration routine
2. Immediately (< 500 ms) issue `ReadDTCInformation(statusMask=0xFF)`
3. Verify DTC read is not rejected with NRC 0x21 (BusyRepeatRequest)

**Expected Result:** DTC read returns valid snapshot during active routine

**Pass Criteria:** `dtc_read_resp.positive == True` or NRC 0x21 handled with retry

---

## 5. Traceability Matrix

### 5.1 Test Cases → Requirements

| TC ID | Req ID(s) | Priority | UDS Service | Marker |
|-------|-----------|----------|-------------|--------|
| TC_ADAS_001 | SYS_REQ_ADAS_001, SYS_REQ_ADAS_002 | P1 | 0x10 DSC | smoke |
| TC_ADAS_002 | SYS_REQ_ADAS_001, SYS_REQ_ADAS_002 | P1 | 0x10 DSC | smoke |
| TC_ADAS_003 | SYS_REQ_ADAS_002 | P1 | 0x10 DSC | regression |
| TC_ADAS_004 | SYS_REQ_ADAS_002 | P2 | 0x10 DSC | regression |
| TC_ADAS_005 | SYS_REQ_ADAS_001 | P1 | 0x11 ECUReset | smoke |
| TC_ADAS_006 | SYS_REQ_ADAS_001 | P2 | 0x11 ECUReset | regression |
| TC_ADAS_007 | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 | P1 | 0x27 SA | security, smoke |
| TC_ADAS_008 | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 | P1 | 0x27 SA | security, smoke |
| TC_ADAS_009 | SYS_REQ_ADAS_003, SAFE_REQ_ADAS_002 | P1 | 0x27 SA | security, negative |
| TC_ADAS_010 | SAFE_REQ_ADAS_002, SYS_REQ_ADAS_003 | P1 | 0x27 SA | security, regression |
| TC_ADAS_011 | SYS_REQ_ADAS_001, FUNC_REQ_ADAS_010 | P1 | 0x22 RDBI | smoke |
| TC_ADAS_012 | SYS_REQ_ADAS_001 | P2 | 0x22 RDBI | regression |
| TC_ADAS_013 | FUNC_REQ_ADAS_010 | P1 | 0x22 RDBI | smoke |
| TC_ADAS_014 | FUNC_REQ_ADAS_001, SAFE_REQ_ADAS_001 | P1 | 0x22 RDBI | smoke, functional |
| TC_ADAS_015 | FUNC_REQ_ADAS_002, SAFE_REQ_ADAS_001 | P1 | 0x22 RDBI | smoke, functional |
| TC_ADAS_016 | FUNC_REQ_ADAS_003, SYS_REQ_ADAS_007 | P1 | 0x22 RDBI | smoke, functional |
| TC_ADAS_017 | FUNC_REQ_ADAS_004 | P1 | 0x22 RDBI | regression, functional |
| TC_ADAS_018 | FUNC_REQ_ADAS_005 | P1 | 0x22 RDBI | smoke, functional |
| TC_ADAS_019 | SYS_REQ_ADAS_008 | P2 | 0x22 RDBI | negative |
| TC_ADAS_020 | SYS_REQ_ADAS_008 | P2 | 0x2E WDBI | negative |
| TC_ADAS_021 | FUNC_REQ_ADAS_006, SYS_REQ_ADAS_006 | P1 | 0x31 RC | regression, functional |
| TC_ADAS_022 | FUNC_REQ_ADAS_006 | P1 | 0x31 RC | regression |
| TC_ADAS_023 | FUNC_REQ_ADAS_007 | P1 | 0x31 RC | regression, functional |
| TC_ADAS_024 | SYS_REQ_ADAS_003, SYS_REQ_ADAS_008 | P1 | 0x31 RC | negative, security |
| TC_ADAS_025 | SYS_REQ_ADAS_005 | P1 | 0x19 ReadDTC | dtc, smoke |
| TC_ADAS_026 | SYS_REQ_ADAS_005 | P2 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_027 | FUNC_REQ_ADAS_008, SAFE_REQ_ADAS_003 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_028 | FUNC_REQ_ADAS_009, SAFE_REQ_ADAS_003 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_029 | FUNC_REQ_ADAS_008, SAFE_REQ_ADAS_003 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_030 | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_004 | P1 | 0x14 ClearDTC | dtc, smoke |
| TC_ADAS_031 | SYS_REQ_ADAS_005 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_032 | SYS_REQ_ADAS_001 | P2 | 0x3E TesterPresent | smoke |
| TC_ADAS_033 | SYS_REQ_ADAS_001 | P2 | 0x28 CommCtrl | regression |
| TC_ADAS_034 | SYS_REQ_ADAS_001 | P2 | 0x28 CommCtrl | regression |
| TC_ADAS_035 | SYS_REQ_ADAS_008 | P2 | 0x31 RC | negative, regression |
| TC_ADAS_036 | SYS_REQ_ADAS_008 | P2 | 0x27 SA | negative, regression |
| TC_ADAS_037 | SYS_REQ_ADAS_006 | P2 | 0x31 RC | regression |
| TC_ADAS_038 | SYS_REQ_ADAS_005 | P2 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_039 | SYS_REQ_ADAS_005 | P2 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_040 | SYS_REQ_ADAS_001 | P2 | 0x11 ECUReset | regression |
| TC_ADAS_041 | SYS_REQ_ADAS_002, SYS_REQ_ADAS_003 | P2 | 0x27 SA | security, regression |
| TC_ADAS_042 | SYS_REQ_ADAS_001 | P3 | 0x3E TesterPresent | smoke |
| TC_ADAS_043 | SYS_REQ_ADAS_005 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_044 | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_003 | P1 | 0x19 ReadDTC | dtc, regression |
| TC_ADAS_045 | SAFE_REQ_ADAS_004 | P1 | 0x11 + 0x19 | dtc, regression |
| TC_ADAS_046 | SYS_REQ_ADAS_008 | P2 | 0x2E WDBI | negative |
| TC_ADAS_047 | SYS_REQ_ADAS_008 | P2 | 0x10 DSC | negative |
| TC_ADAS_048 | SYS_REQ_ADAS_001 | P3 | All | regression |
| TC_ADAS_049 | SYS_REQ_ADAS_008 | P3 | 0x22 RDBI | negative |
| TC_ADAS_050 | SYS_REQ_ADAS_001 | P3 | 0x3E TesterPresent | smoke |
| TC_ADAS_051 | FUNC_REQ_ADAS_002, SAFE_REQ_ADAS_001 | P1 | 0x31 RC + 0x22 RDBI | functional |
| TC_ADAS_052 | SYS_REQ_ADAS_005, SAFE_REQ_ADAS_003 | P1 | 0x19 ReadDTC | dtc |
| TC_ADAS_053 | FUNC_REQ_ADAS_003 | P2 | 0x22 RDBI | functional |
| TC_ADAS_054 | SYS_REQ_ADAS_001 | P2 | 0x11 + 0x10 | regression |
| TC_ADAS_055 | SYS_REQ_ADAS_005, SYS_REQ_ADAS_006 | P3 | 0x31 + 0x19 | regression |

### 5.2 Requirements → Test Cases (Reverse Traceability)

| Requirement ID | Covered By Test Cases | Coverage |
|----------------|----------------------|----------|
| SYS_REQ_ADAS_001 | TC_ADAS_001–006, 032–034, 040–042, 048, 050, 054 | ✅ Full |
| SYS_REQ_ADAS_002 | TC_ADAS_001–004, 041 | ✅ Full |
| SYS_REQ_ADAS_003 | TC_ADAS_007–010, 024, 041 | ✅ Full |
| SYS_REQ_ADAS_004 | TC_ADAS_014, 015 | ✅ Full |
| SYS_REQ_ADAS_005 | TC_ADAS_025–031, 038, 039, 043–045, 052 | ✅ Full |
| SYS_REQ_ADAS_006 | TC_ADAS_021–023, 037, 055 | ✅ Full |
| SYS_REQ_ADAS_007 | TC_ADAS_016–018 | ✅ Full |
| SYS_REQ_ADAS_008 | TC_ADAS_019, 020, 024, 035, 036, 046, 047, 049 | ✅ Full |
| FUNC_REQ_ADAS_001 | TC_ADAS_014 | ✅ Full |
| FUNC_REQ_ADAS_002 | TC_ADAS_015, 051 | ✅ Full |
| FUNC_REQ_ADAS_003 | TC_ADAS_016, 053 | ✅ Full |
| FUNC_REQ_ADAS_004 | TC_ADAS_017 | ✅ Full |
| FUNC_REQ_ADAS_005 | TC_ADAS_018 | ✅ Full |
| FUNC_REQ_ADAS_006 | TC_ADAS_021, 022 | ✅ Full |
| FUNC_REQ_ADAS_007 | TC_ADAS_023 | ✅ Full |
| FUNC_REQ_ADAS_008 | TC_ADAS_027, 029 | ✅ Full |
| FUNC_REQ_ADAS_009 | TC_ADAS_028 | ✅ Full |
| FUNC_REQ_ADAS_010 | TC_ADAS_011, 013 | ✅ Full |
| SAFE_REQ_ADAS_001 | TC_ADAS_014, 015, 051 | ✅ Full |
| SAFE_REQ_ADAS_002 | TC_ADAS_007–010 | ✅ Full |
| SAFE_REQ_ADAS_003 | TC_ADAS_027–029, 043, 044, 052 | ✅ Full |
| SAFE_REQ_ADAS_004 | TC_ADAS_030, 045 | ✅ Full |

### 5.3 Test Execution Summary

| Category | Count |
|----------|-------|
| Total test cases | 55 |
| P1 — Critical | 24 |
| P2 — High | 22 |
| P3 — Medium | 9 |
| Positive tests | 38 |
| Negative tests | 12 |
| Fault injection | 5 |
| Smoke tests | 16 |
| Regression tests | 33 |
| DTC-related | 15 |
| Security-related | 7 |
| Functional validation | 10 |

---

*Document end — TCD-ADAS-001 v1.0*
