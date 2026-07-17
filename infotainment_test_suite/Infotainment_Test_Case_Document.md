# Infotainment ECU — Test Case Document with Traceability
**Project:** Infotainment ECU Validation Test Suite  
**Document ID:** TCD-INFO-001  
**Version:** 1.0  
**Date:** 2026-07-08  
**Author:** Automotive Test Validation Team  
**Status:** Active  

---

## 1. Scope

This document defines the formal test cases for the Infotainment Head Unit (HU) ECU validation
suite. Coverage spans UDS diagnostic services, all HU feature areas (Bluetooth, USB/Media,
Radio/Tuner, Navigation, Voice Recognition, Display/HMI, Audio Amplifier, CarPlay/Android Auto,
OTA, and Network Connectivity), DTC management, and negative/error handling.

Implemented in `infotainment_test_suite/tests/`.

---

## 2. Reference Documents

| Ref | Document |
|-----|----------|
| [ISO-14229] | ISO 14229-1:2020 — Unified Diagnostic Services (UDS) |
| [ISO-26262] | ISO 26262-1:2018 — Road vehicles Functional Safety |
| [AUTOSAR] | AUTOSAR DCM R22-11 |
| [ISO-15765] | ISO 15765-2:2016 — UDS on CAN (ISO-TP) |
| [SRS-HU] | Head Unit ECU Software Requirements Specification (supplier) |
| [DTC-HU] | Infotainment ECU DTC Catalogue v3.1 |
| [DID-HU] | Infotainment ECU DID Register v2.5 |

---

## 3. Requirements Summary

### 3.1 System Requirements

| Req ID | Description | Source | ASIL |
|--------|-------------|--------|------|
| SYS_REQ_INFO_001 | Infotainment ECU shall support UDS diagnostic access over CAN | SRS-HU §3.1 | A |
| SYS_REQ_INFO_002 | ECU shall implement DSC (default, extended, programming sessions) | SRS-HU §3.2 | A |
| SYS_REQ_INFO_003 | ECU shall implement security access with seed/key at levels 1 and 3 | SRS-HU §3.3 | A |
| SYS_REQ_INFO_004 | ECU shall expose all feature status DIDs | DID-HU §2 | QM |
| SYS_REQ_INFO_005 | ECU shall generate and store DTCs for all monitored hardware faults | DTC-HU §1 | A |
| SYS_REQ_INFO_006 | ECU shall support routine control for all self-test and reset routines | SRS-HU §4.1 | QM |
| SYS_REQ_INFO_007 | ECU shall respond with correct NRCs for all invalid requests | SRS-HU §3.5 | A |
| SYS_REQ_INFO_008 | ECU shall support IOControlByIdentifier for HMI output overrides | SRS-HU §4.2 | QM |

### 3.2 Functional Requirements

| Req ID | Description | Source |
|--------|-------------|--------|
| FUNC_REQ_INFO_001 | Bluetooth module status shall be readable and writable via DID 0x3001 | DID-HU §2.2.1 |
| FUNC_REQ_INFO_002 | BT pairing count DID shall reflect the number of stored pairings (0–8) | DID-HU §2.2.2 |
| FUNC_REQ_INFO_003 | A2DP and HFP states shall be exposed via diagnostic DIDs | DID-HU §2.2.3 |
| FUNC_REQ_INFO_004 | USB port status DIDs shall reflect device connection state | DID-HU §2.5.1 |
| FUNC_REQ_INFO_005 | Media playback state DID shall reflect current player state | DID-HU §2.5.2 |
| FUNC_REQ_INFO_006 | Wi-Fi module status and SSID shall be readable via DIDs | DID-HU §2.3.1 |
| FUNC_REQ_INFO_007 | Tuner band and FM frequency DIDs shall be writable for band switching | DID-HU §2.4.1 |
| FUNC_REQ_INFO_008 | GPS fix status and map DB version shall be readable | DID-HU §2.6.1 |
| FUNC_REQ_INFO_009 | Voice recognition and microphone status DIDs shall be readable | DID-HU §2.7.1 |
| FUNC_REQ_INFO_010 | Display brightness DID shall support read and write in extended session | DID-HU §2.8.1 |
| FUNC_REQ_INFO_011 | CarPlay and Android Auto status DIDs shall reflect projection state | DID-HU §2.9.1 |
| FUNC_REQ_INFO_012 | OTA update status DID shall reflect firmware update progression | DID-HU §2.10.1 |
| FUNC_REQ_INFO_013 | Factory reset routine shall restore all HMI settings to defaults | SRS-HU §4.1.3 |
| FUNC_REQ_INFO_014 | Audio volume DID shall support read and write | DID-HU §2.5.4 |
| FUNC_REQ_INFO_015 | IOControl shall force display backlight and audio mute outputs | SRS-HU §4.2.1 |

### 3.3 DTC Requirements

| Req ID | Description | Source |
|--------|-------------|--------|
| DTC_REQ_INFO_001 | DTC 0xB11001 shall be generated on display panel comm failure | DTC-HU §3.1 |
| DTC_REQ_INFO_002 | DTC 0xB13001 shall be generated on BT module not detected | DTC-HU §3.3 |
| DTC_REQ_INFO_003 | DTC 0xB15001 shall be generated on USB port 1 overcurrent | DTC-HU §3.5 |
| DTC_REQ_INFO_004 | DTC 0xB16001 shall be generated on GPS antenna open circuit | DTC-HU §3.6 |
| DTC_REQ_INFO_005 | DTC 0xB12001 shall be generated on audio amp over-temperature | DTC-HU §3.2 |

---

## 4. Test Cases

---

### TC_INFO_001: Enter Default Diagnostic Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_001 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_001, SYS_REQ_INFO_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_enter_default_session` |

**Preconditions:** ECU powered; CAN at 500 kbps; TX=0x730, RX=0x738

**Test Steps:**
1. `DiagnosticSessionControl(0x01 — defaultSession)`
2. Capture response

**Expected Result:** Positive response `0x50 0x01`; `service_id == 0x10`

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_002: Enter Extended Diagnostic Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_002 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_001, SYS_REQ_INFO_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_enter_extended_diagnostic_session` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `DSC(0x03 — extendedDiagnosticSession)`

**Expected Result:** Positive response `0x50 0x03`

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_003: Enter Programming Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_003 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_enter_programming_session_from_extended` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `DSC(0x02 — programmingSession)`

**Expected Result:** Positive response; `0x50 0x02`

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_004: Session Timing Parameters P2 and P2*

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_004 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_session_response_contains_timing_parameters` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `DSC(extendedDiagnosticSession)`
2. Parse: `P2 = (data[1]<<8)|data[2]`; `P2* = ((data[3]<<8)|data[4]) × 10`

**Expected Result:** `P2_ms > 0`; `P2*_ms >= P2_ms`

**Pass Criteria:** Both timing values valid per ISO 14229

---

### TC_INFO_005: Full Session Cycle

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_005 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_002 |
| **UDS Service** | 0x10 DiagnosticSessionControl |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_full_session_cycle` |

**Preconditions:** None

**Test Steps:**
1. `DSC(default)` → positive
2. `DSC(extended)` → positive
3. `DSC(programming)` → positive
4. `DSC(default)` → positive

**Expected Result:** All four transitions succeed

**Pass Criteria:** All `response.positive == True`

---

### TC_INFO_006: Hard Reset Returns to Default Session

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_006 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_001 |
| **UDS Service** | 0x11 ECUReset |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_session_control.py::test_hard_reset_returns_to_default_session` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `ECUReset(0x01 — hardReset)`
2. Wait 2 s (boot time)
3. `DSC(defaultSession)`

**Expected Result:** Both calls positive; ECU operational after reset

**Pass Criteria:** `reset_resp.positive == True`; `default_resp.positive == True`

---

### TC_INFO_007: Security Access — Seed Request (Level 0x01)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_007 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.security` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_security_access.py::test_request_seed_in_extended_session` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `SecurityAccess(requestSeed, 0x01)`
2. Verify seed bytes non-zero

**Expected Result:** Positive response `0x67 0x01 <seed>`; seed ≠ 0x00000000

**Pass Criteria:** `response.positive == True`; at least one non-zero seed byte

---

### TC_INFO_008: Security Access — Correct Key Grants Access

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_008 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.security` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_security_access.py::test_correct_key_grants_access` |

**Preconditions:** Extended session; seed obtained

**Test Steps:**
1. `SecurityAccess(requestSeed, 0x01)` → get seed
2. Compute key via algorithm
3. `SecurityAccess(sendKey, 0x02, <key>)`

**Expected Result:** `0x67 0x02`; access granted

**Pass Criteria:** `perform_security_access()` returns `True`

---

### TC_INFO_009: Security Access — Wrong Key Returns NRC 0x35

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_009 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.security` `@pytest.mark.negative` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_security_access.py::test_wrong_key_returns_nrc_invalid_key` |

**Preconditions:** Extended session; seed obtained

**Test Steps:**
1. `SecurityAccess(sendKey, 0x02, 0x00000000)` — wrong key

**Expected Result:** NRC `0x7F 0x27 0x35` (InvalidKey)

**Pass Criteria:** `response.nrc == 0x35`

---

### TC_INFO_010: Security Lockout After 3 Failed Attempts (NRC 0x36)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_010 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_003 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.security` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_security_access.py::test_lockout_after_exceeded_attempts` |

**Preconditions:** Extended session

**Test Steps:**
1–3. Send wrong key 3 times (each time after fresh seed request)

**Expected Result:** After 3rd attempt: NRC 0x36 (ExceededNumberOfAttempts)

**Pass Criteria:** `final_resp.nrc == 0x36`

---

### TC_INFO_011: SecurityAccess in Default Session Returns NRC 0x7F

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_011 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_003, SYS_REQ_INFO_007 |
| **UDS Service** | 0x27 SecurityAccess |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.security` `@pytest.mark.negative` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_security_access.py::test_seed_request_in_default_session_denied` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `SecurityAccess(requestSeed, 0x01)` without entering extended session

**Expected Result:** NRC `0x7F 0x27 0x7F`

**Pass Criteria:** `response.nrc == 0x7F`

---

### TC_INFO_012: TesterPresent — Keep Session Alive

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_012 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_tester_present.py::test_multiple_tester_present_keep_session_alive` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. Send 5 × `TesterPresent(suppress=True)` at 1 s intervals

**Expected Result:** All 5 calls positive; session maintained

**Pass Criteria:** All 5 `response.positive == True`

---

### TC_INFO_013: TesterPresent — Suppress Response Flag

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_013 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_INFO_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_tester_present.py::test_tester_present_suppress_response` |

**Preconditions:** ECU in extended session

**Test Steps:**
1. `TesterPresent(suppress=True)` — sub-function 0x80

**Expected Result:** No response frame; session kept alive

**Pass Criteria:** No NRC returned

---

### TC_INFO_014: Frame Logger Captures TesterPresent Transaction

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_014 |
| **Priority** | P3 — Medium |
| **Requirement IDs** | SYS_REQ_INFO_001 |
| **UDS Service** | 0x3E TesterPresent |
| **DID / DTC** | N/A |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Framework |
| **Automation File** | `tests/uds/test_tester_present.py::test_frame_logger_captures_tester_present_transaction` |

**Preconditions:** Mock mode; `frame_logger` fixture declared

**Test Steps:**
1. `TesterPresent(suppress=False)` with frame_logger active
2. Check `frame_logger[-1]["service"] == "TesterPresent"`

**Expected Result:** Transaction log entry for TesterPresent exists

**Pass Criteria:** `len(frame_logger) > 0`

---

### TC_INFO_015: Read Software Version DID (0xF189)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_015 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF189 |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_read_write_did.py::test_read_software_version_did` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `RDBI(0xF189 — software_version)`

**Expected Result:** Positive response; data ≥ 4 bytes; ASCII string

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 4`

---

### TC_INFO_016: Read VIN DID (0xF190)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_016 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xF190 |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_read_write_did.py::test_read_vin_did` |

**Preconditions:** VIN programmed; ECU in default session

**Test Steps:**
1. `RDBI(0xF190 — vin)`

**Expected Result:** Positive response; 19-byte payload (2 DID + 17 VIN)

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 4`

---

### TC_INFO_017: Write Display Brightness DID (0x3020)

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_017 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_010 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | DID 0x3020 |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_read_write_did.py::test_write_display_brightness_did` |

**Preconditions:** Extended session (no security needed for brightness)

**Test Steps:**
1. `WDBI(0x3020, data=0x80)` — set brightness to ≈50 %

**Expected Result:** Positive response `0x6E 0x30 0x20`

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_018: Write Read-Only DID Returns NRC

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_018 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_007 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | DID 0xF189 (software_version — read-only) |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_read_write_did.py::test_write_read_only_did_returns_nrc` |

**Preconditions:** Extended session

**Test Steps:**
1. `WDBI(0xF189, data=b"\x01\x02\x03")`

**Expected Result:** NRC 0x31 (RequestOutOfRange) or 0x22

**Pass Criteria:** `response.positive == False`

---

### TC_INFO_019: Write DID in Default Session Returns NRC 0x7F

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_019 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_007 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | DID 0x3031 (audio_volume — extended-session write) |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_read_write_did.py::test_write_did_in_default_session_denied` |

**Preconditions:** ECU in default session

**Test Steps:**
1. `WDBI(0x3031, data=0x50)` in default session

**Expected Result:** NRC 0x7F or 0x22

**Pass Criteria:** `response.positive == False`

---

### TC_INFO_020: Parametrized Read — All DIDs in YAML Catalogue

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_020 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | All 36 DIDs from infotainment_dids.yaml |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.parametrize` `@pytest.mark.regression` |
| **Test Type** | Parametrized Coverage |
| **Automation File** | `tests/uds/test_read_write_did.py::test_read_all_dids[<did_name>]` |

**Preconditions:** Required session entered per DID config

**Test Steps:**
1. For each DID in `infotainment_dids.yaml`:
   a. Enter required session
   b. `RDBI(<did_id>)`
   c. Verify positive response and `len(data) >= 2`

**Expected Result:** All 36 DIDs return positive responses

**Pass Criteria:** 100 % positive response rate across all DIDs

---

### TC_INFO_021: Bluetooth Module Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_021 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_001 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3001 |
| **pytest Marker** | `@pytest.mark.bluetooth` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_bluetooth.py::test_read_bluetooth_module_status_did` |

**Preconditions:** Extended session; BT module powered

**Test Steps:**
1. `RDBI(0x3001 — bluetooth_module_status)`
2. Verify value ∈ `{0x00=off, 0x01=initialising, 0x02=ready, 0x03=fault}`

**Expected Result:** Valid enum state returned

**Pass Criteria:** `response.positive == True`; `data[2] in (0x00..0x03)`

---

### TC_INFO_022: Bluetooth Pairing Count DID — Range Validation

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_022 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_002 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3002 |
| **pytest Marker** | `@pytest.mark.bluetooth` `@pytest.mark.smoke` |
| **Test Type** | Boundary Value |
| **Automation File** | `tests/features/test_bluetooth.py::test_read_bluetooth_pairing_count_did` |

**Preconditions:** Extended session; 0–8 devices paired

**Test Steps:**
1. `RDBI(0x3002 — bluetooth_pairing_count)`
2. Verify: `0 <= count <= 8`

**Expected Result:** Pairing count within spec range

**Pass Criteria:** `data[2] <= 8`

---

### TC_INFO_023: Bluetooth A2DP Streaming State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_023 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_003 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3003 |
| **pytest Marker** | `@pytest.mark.bluetooth` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_bluetooth.py::test_read_bluetooth_a2dp_state_did` |

**Preconditions:** Extended session; BT module ready

**Test Steps:**
1. `RDBI(0x3003 — bluetooth_a2dp_state)`
2. Verify state ∈ `{0x00=disconnected, 0x01=connected, 0x02=streaming}`

**Expected Result:** Valid A2DP state

**Pass Criteria:** `data[2] in (0x00, 0x01, 0x02)`

---

### TC_INFO_024: Bluetooth HFP Call State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_024 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_003 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3004 |
| **pytest Marker** | `@pytest.mark.bluetooth` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_bluetooth.py::test_read_bluetooth_hfp_state_did` |

**Preconditions:** Extended session; HFP device connected or idle

**Test Steps:**
1. `RDBI(0x3004 — bluetooth_hfp_state)`

**Expected Result:** Valid state: `{idle=0x00, incoming=0x01, active=0x02, outgoing=0x03}`

**Pass Criteria:** `data[2] in (0x00, 0x01, 0x02, 0x03)`

---

### TC_INFO_025: Bluetooth Module Not-Detected DTC Absent on Healthy ECU

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_025 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | DTC_REQ_INFO_002, SYS_REQ_INFO_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB13001 |
| **pytest Marker** | `@pytest.mark.bluetooth` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_bluetooth.py::test_no_bluetooth_module_dtc_on_healthy_ecu` |

**Preconditions:** BT module connected; DTCs cleared

**Test Steps:**
1. `ClearDTC(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0x08 — confirmed)`
3. Check DTC 0xB13001 absent

**Expected Result:** DTC 0xB13001 NOT in confirmed list

**Pass Criteria:** No BT module DTC confirmed

---

### TC_INFO_026: USB Port 1 Status DID — Valid Enum State

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_026 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3040 |
| **pytest Marker** | `@pytest.mark.usb_media` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_usb_media.py::test_read_usb_port1_status_did` |

**Preconditions:** Extended session; USB port 1 in known state

**Test Steps:**
1. `RDBI(0x3040 — usb_port1_status)`
2. Verify: `{0x00=no_device, 0x01=connected, 0x02=enumerated, 0x03=overcurrent, 0x04=fault}`

**Expected Result:** Valid state byte

**Pass Criteria:** `data[2] in (0x00..0x04)`

---

### TC_INFO_027: USB Port 2 Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_027 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_004 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3041 |
| **pytest Marker** | `@pytest.mark.usb_media` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_usb_media.py::test_read_usb_port2_status_did` |

**Preconditions:** Extended session

**Test Steps:**
1. `RDBI(0x3041 — usb_port2_status)`

**Expected Result:** Positive response; valid state

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_028: Media Playback State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_028 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_005 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3042 |
| **pytest Marker** | `@pytest.mark.usb_media` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_usb_media.py::test_read_media_playback_state_did` |

**Preconditions:** Extended session; USB media connected

**Test Steps:**
1. `RDBI(0x3042 — media_playback_state)`
2. Verify: `{0x00=idle, 0x01=playing, 0x02=paused, 0x03=stopped, 0x04=error}`

**Expected Result:** Valid playback state

**Pass Criteria:** `data[2] in (0x00..0x04)`

---

### TC_INFO_029: USB Port 1 Overcurrent DTC Absent on Clean ECU

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_029 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | DTC_REQ_INFO_003 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB15001 |
| **pytest Marker** | `@pytest.mark.usb_media` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_usb_media.py::test_no_usb_overcurrent_dtc_on_clean_ecu` |

**Preconditions:** No overcurrent; DTCs cleared

**Test Steps:**
1. `ClearDTC(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0x08)`
3. Verify 0xB15001 absent

**Expected Result:** No USB overcurrent DTC confirmed

**Pass Criteria:** `0xB15001 not in snapshot.confirmed_dtcs codes`

---

### TC_INFO_030: Wi-Fi Module Status DID — Valid State

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_030 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_006 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3010 |
| **pytest Marker** | `@pytest.mark.network` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_network_connectivity.py::test_read_wifi_module_status_did` |

**Preconditions:** Extended session; Wi-Fi module powered

**Test Steps:**
1. `RDBI(0x3010 — wifi_module_status)`
2. Verify: `{0x00=off, 0x01=enabled_disconnected, 0x02=connected, 0x03=hotspot, 0x04=fault}`

**Expected Result:** Valid Wi-Fi state

**Pass Criteria:** `data[2] in (0x00..0x04)`

---

### TC_INFO_031: Wi-Fi SSID DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_031 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_006 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3011 |
| **pytest Marker** | `@pytest.mark.network` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_network_connectivity.py::test_read_wifi_ssid_did` |

**Preconditions:** Extended session; Wi-Fi connected or module active

**Test Steps:**
1. `RDBI(0x3011 — wifi_ssid)`

**Expected Result:** Positive response; up to 32 bytes SSID

**Pass Criteria:** `response.positive == True`; `len(response.data) >= 2`

---

### TC_INFO_032: Hotspot Status DID — Boolean Value

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_032 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_006 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3012 |
| **pytest Marker** | `@pytest.mark.network` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_network_connectivity.py::test_read_hotspot_status_did` |

**Preconditions:** Extended session

**Test Steps:**
1. `RDBI(0x3012 — hotspot_status)`
2. Verify: `0x00 = disabled`, `0x01 = enabled`

**Expected Result:** Boolean state

**Pass Criteria:** `data[2] in (0x00, 0x01)`

---

### TC_INFO_033: Connectivity Self-Test Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_033 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_006, FUNC_REQ_INFO_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0330 |
| **pytest Marker** | `@pytest.mark.network` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_network_connectivity.py::test_connectivity_self_test_routine` |

**Preconditions:** Extended session

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0330 — connectivity_self_test)`

**Expected Result:** Positive response; Wi-Fi RF loop-back passes

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_034: Active Tuner Band DID — Enum Validation

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_034 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_007 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3050 |
| **pytest Marker** | `@pytest.mark.radio` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_radio_tuner.py::test_read_tuner_band_did` |

**Preconditions:** Extended session; tuner active

**Test Steps:**
1. `RDBI(0x3050 — tuner_band)`
2. Verify: `{0x00=AM, 0x01=FM, 0x02=DAB}`

**Expected Result:** Valid band value

**Pass Criteria:** `data[2] in (0x00, 0x01, 0x02)`

---

### TC_INFO_035: FM Frequency DID — Write Band Switch

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_035 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_007 |
| **UDS Service** | 0x2E WriteDataByIdentifier |
| **DID / DTC** | DID 0x3050 |
| **pytest Marker** | `@pytest.mark.radio` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_radio_tuner.py::test_write_tuner_band_switch_fm` |

**Preconditions:** Extended session

**Test Steps:**
1. `WDBI(0x3050, data=0x01)` — switch to FM

**Expected Result:** Positive response; tuner switches to FM

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_036: DAB Service Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_036 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_007 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3052 |
| **pytest Marker** | `@pytest.mark.radio` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_radio_tuner.py::test_read_dab_service_status_did` |

**Preconditions:** Extended session; DAB antenna connected

**Test Steps:**
1. `RDBI(0x3052 — dab_service_status)`

**Expected Result:** Valid state: `{0x00=no_signal, 0x01=signal_acquired, 0x02=playing}`

**Pass Criteria:** `data[2] in (0x00, 0x01, 0x02)`

---

### TC_INFO_037: GPS Fix Status DID — Range 0–3

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_037 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_008 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3060 |
| **pytest Marker** | `@pytest.mark.navigation` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_navigation.py::test_read_gps_fix_status_did` |

**Preconditions:** Extended session; GPS antenna connected

**Test Steps:**
1. `RDBI(0x3060 — gps_fix_status)`
2. Verify: `{0x00=no_fix, 0x01=2D, 0x02=3D, 0x03=DGPS}`

**Expected Result:** Valid fix type

**Pass Criteria:** `data[2] in (0x00..0x03)`

---

### TC_INFO_038: Map DB Version DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_038 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_008 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3063 |
| **pytest Marker** | `@pytest.mark.navigation` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_navigation.py::test_read_map_db_version_did` |

**Preconditions:** Default session; navigation module active

**Test Steps:**
1. `RDBI(0x3063 — map_db_version)`

**Expected Result:** Non-empty version string

**Pass Criteria:** `response.positive == True`; `len(data) >= 4`

---

### TC_INFO_039: GPS Self-Test Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_039 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_006, FUNC_REQ_INFO_008 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0340 |
| **pytest Marker** | `@pytest.mark.navigation` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_navigation.py::test_gps_self_test_routine` |

**Preconditions:** Extended session; GPS antenna connected

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0340 — gps_self_test)`

**Expected Result:** Positive response; GNSS module cold-start initiated

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_040: GPS Antenna Open-Circuit DTC Absent

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_040 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | DTC_REQ_INFO_004, SYS_REQ_INFO_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB16001 |
| **pytest Marker** | `@pytest.mark.navigation` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_navigation.py::test_no_gps_antenna_open_circuit_dtc` |

**Preconditions:** GPS antenna connected; DTCs cleared

**Test Steps:**
1. `ClearDTC(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0x08)`
3. Verify 0xB16001 absent

**Expected Result:** GPS antenna DTC NOT confirmed

**Pass Criteria:** `0xB16001 not in snapshot.confirmed_dtcs`

---

### TC_INFO_041: Voice Recognition State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_041 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_009 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3070 |
| **pytest Marker** | `@pytest.mark.voice` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_voice_recognition.py::test_read_voice_recognition_state_did` |

**Preconditions:** Extended session; VR module initialised

**Test Steps:**
1. `RDBI(0x3070 — voice_recognition_state)`
2. Verify: `{0x00=inactive, 0x01=listening, 0x02=processing, 0x03=fault}`

**Expected Result:** Valid VR state

**Pass Criteria:** `data[2] in (0x00..0x03)`

---

### TC_INFO_042: Microphone Status DID — Hardware Check

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_042 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_009 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3071 |
| **pytest Marker** | `@pytest.mark.voice` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_voice_recognition.py::test_read_microphone_status_did` |

**Preconditions:** Extended session; microphone connected

**Test Steps:**
1. `RDBI(0x3071 — microphone_status)`
2. Verify: `{0x00=not_ready, 0x01=ready, 0x02=open_circuit, 0x03=short}`

**Expected Result:** Microphone hardware status; should be 0x01 (ready) on bench

**Pass Criteria:** `data[2] in (0x00, 0x01, 0x02, 0x03)`

---

### TC_INFO_043: HMI Sleep State DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_043 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_010 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3023 |
| **pytest Marker** | `@pytest.mark.display` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_display_hmi.py::test_read_hmi_sleep_state_did` |

**Preconditions:** Default session; HMI active

**Test Steps:**
1. `RDBI(0x3023 — hmi_sleep_state)`
2. Verify: `{0x00=active, 0x01=dim, 0x02=sleep, 0x03=deep_sleep}`

**Expected Result:** Valid HMI state; should be 0x00 on active bench

**Pass Criteria:** `data[2] in (0x00..0x03)`

---

### TC_INFO_044: Display Brightness DID Read Then Write

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_044 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_010 |
| **UDS Service** | 0x22 RDBI + 0x2E WDBI |
| **DID / DTC** | DID 0x3020 |
| **pytest Marker** | `@pytest.mark.display` `@pytest.mark.regression` |
| **Test Type** | Read-Modify Positive |
| **Automation File** | `tests/features/test_display_hmi.py::test_write_display_brightness_50_percent` |

**Preconditions:** Extended session; no security needed for brightness

**Test Steps:**
1. `RDBI(0x3020)` → record original brightness
2. `WDBI(0x3020, data=0x80)` — set 50 %
3. `RDBI(0x3020)` → verify updated value

**Expected Result:** Read-back value matches written value (0x80)

**Pass Criteria:** Post-write RDBI returns 0x80

---

### TC_INFO_045: Touch Screen Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_045 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_010 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3022 |
| **pytest Marker** | `@pytest.mark.display` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_display_hmi.py::test_read_touch_screen_status_did` |

**Preconditions:** Extended session; touch controller active

**Test Steps:**
1. `RDBI(0x3022 — touch_screen_status)`
2. Verify: `{0x00=not_ready, 0x01=ready, 0x02=degraded, 0x03=fault}`

**Expected Result:** Touch controller ready (0x01) on bench

**Pass Criteria:** `data[2] in (0x00..0x03)`

---

### TC_INFO_046: Display Self-Test Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_046 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0301 |
| **pytest Marker** | `@pytest.mark.display` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_display_hmi.py::test_display_self_test_routine` |

**Preconditions:** Extended session; security unlock

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0301 — display_self_test)`

**Expected Result:** Positive response; display pixel test activated

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_047: Force Display Backlight via IOControl

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_047 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_015, SYS_REQ_INFO_008 |
| **UDS Service** | 0x2F IOControlByIdentifier |
| **DID / DTC** | DID 0x3020 |
| **pytest Marker** | `@pytest.mark.display` `@pytest.mark.io_control` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_io_control.py::test_force_display_backlight_on` |

**Preconditions:** Extended session; security unlock

**Test Steps:**
1. `IOControl(0x3020, shortTermAdjustment → 0xFF)` — max brightness

**Expected Result:** Positive response; display at max brightness

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_048: Audio Amplifier Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_048 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_014 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3030 |
| **pytest Marker** | `@pytest.mark.audio` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_audio_amplifier.py::test_read_audio_amp_status_did` |

**Preconditions:** Extended session; audio amp powered

**Test Steps:**
1. `RDBI(0x3030 — audio_amp_status)`
2. Verify: `{0x00=off, 0x01=standby, 0x02=active, 0x03=fault}`

**Expected Result:** Amplifier active or standby on bench

**Pass Criteria:** `data[2] in (0x00..0x03)`

---

### TC_INFO_049: Audio Volume Level DID — Read and Write

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_049 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_014 |
| **UDS Service** | 0x22 RDBI + 0x2E WDBI |
| **DID / DTC** | DID 0x3031 |
| **pytest Marker** | `@pytest.mark.audio` `@pytest.mark.smoke` |
| **Test Type** | Read-Modify Positive |
| **Automation File** | `tests/features/test_audio_amplifier.py::test_write_audio_volume_level` |

**Preconditions:** Extended session; volume in 0–100 range

**Test Steps:**
1. `WDBI(0x3031, data=0x32)` — write 50 %
2. `RDBI(0x3031)` → verify 0x32

**Expected Result:** Write positive; read-back = 0x32

**Pass Criteria:** `response.positive == True`; post-write RDBI returns 0x32

---

### TC_INFO_050: Audio Amp Over-Temperature DTC Absent on Healthy ECU

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_050 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | DTC_REQ_INFO_005, SYS_REQ_INFO_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB12001 |
| **pytest Marker** | `@pytest.mark.audio` `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_audio_amplifier.py::test_no_audio_amp_over_temp_dtc` |

**Preconditions:** Ambient temperature normal; DTCs cleared

**Test Steps:**
1. `ClearDTC(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0x08)`
3. Verify 0xB12001 absent

**Expected Result:** Audio amp DTC NOT confirmed

**Pass Criteria:** DTC 0xB12001 absent

---

### TC_INFO_051: CarPlay Session Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_051 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_011 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3080 |
| **pytest Marker** | `@pytest.mark.projection` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_carplay_androidauto.py::test_read_carplay_status_did` |

**Preconditions:** Extended session; USB connected

**Test Steps:**
1. `RDBI(0x3080 — carplay_status)`
2. Verify: `{0x00=disconnected, 0x01=connecting, 0x02=active_wired, 0x03=active_wireless, 0x04=fault}`

**Expected Result:** Valid projection state

**Pass Criteria:** `data[2] in (0x00..0x04)`

---

### TC_INFO_052: Android Auto Session Status DID

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_052 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_011 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3081 |
| **pytest Marker** | `@pytest.mark.projection` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_carplay_androidauto.py::test_read_android_auto_status_did` |

**Preconditions:** Extended session

**Test Steps:**
1. `RDBI(0x3081 — android_auto_status)`

**Expected Result:** Valid Android Auto state

**Pass Criteria:** `data[2] in (0x00..0x04)`

---

### TC_INFO_053: Projection Session Start Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_053 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_011, SYS_REQ_INFO_006 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0380 |
| **pytest Marker** | `@pytest.mark.projection` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_carplay_androidauto.py::test_projection_session_start_routine` |

**Preconditions:** Extended session; USB connected

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0380 — projection_session_start)`

**Expected Result:** Positive response; projection session initiated

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_054: OTA Update Status DID — Idle State on Fresh ECU

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_054 |
| **Priority** | P2 — High |
| **Requirement IDs** | FUNC_REQ_INFO_012 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x3090 |
| **pytest Marker** | `@pytest.mark.ota` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_software_update.py::test_read_ota_update_status_did` |

**Preconditions:** Extended session; no OTA in progress

**Test Steps:**
1. `RDBI(0x3090 — ota_update_status)`
2. Verify idle: `{0x00=idle, ..., 0x06=failed}`

**Expected Result:** Status = 0x00 (idle) on fresh bench ECU

**Pass Criteria:** `data[2] in (0x00..0x06)`

---

### TC_INFO_055: Software Checksum Verify Routine

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_055 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_006, FUNC_REQ_INFO_012 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0390 |
| **pytest Marker** | `@pytest.mark.ota` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/features/test_software_update.py::test_software_checksum_verify_routine` |

**Preconditions:** Programming session; security unlock level 3

**Test Steps:**
1. `DSC(programmingSession)`
2. Security unlock
3. `RoutineControl(startRoutine, 0x0390)`

**Expected Result:** Positive response; checksum verification passes

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_056: Read All DTCs — Clean ECU Returns Empty List

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_056 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | All |
| **pytest Marker** | `@pytest.mark.dtc` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/dtc/test_dtc_read.py::test_read_all_dtcs_status_mask_ff` |

**Preconditions:** Clean bench ECU; DTCs cleared

**Test Steps:**
1. `ClearDTC(0xFFFFFF)`
2. `ReadDTCInformation(statusMask=0xFF)`

**Expected Result:** Zero confirmed DTCs

**Pass Criteria:** `len(snapshot.confirmed_dtcs) == 0`

---

### TC_INFO_057: Clear All DTCs and Verify Empty List

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_057 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | SYS_REQ_INFO_005 |
| **UDS Service** | 0x14 ClearDiagnosticInformation |
| **DID / DTC** | Group 0xFFFFFF |
| **pytest Marker** | `@pytest.mark.dtc` `@pytest.mark.smoke` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/dtc/test_dtc_clear.py::test_clear_all_dtcs` |

**Preconditions:** Extended session

**Test Steps:**
1. `ClearDTC(0xFFFFFF)` → verify positive
2. `ReadDTCInformation(statusMask=0x08)`

**Expected Result:** Clear positive; 0 confirmed DTCs after clear

**Pass Criteria:** Both calls succeed; `len(confirmed) == 0`

---

### TC_INFO_058: DTC Diff — Detects Newly Set DTC

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_058 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_005 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB16001 |
| **pytest Marker** | `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/dtc/test_dtc_snapshot_freeze.py::test_dtc_diff_detects_new_dtc` |

**Preconditions:** Clean DTC snapshot before fault injection

**Test Steps:**
1. `snap_before = dtc_manager.read_all()`
2. Inject GPS antenna fault
3. `snap_after = dtc_manager.read_all()`
4. `new = dtc_manager.diff(snap_before, snap_after)`

**Expected Result:** diff = 1 DTC (0xB16001)

**Pass Criteria:** `len(new) == 1`; `new[0].dtc_code == 0xB16001`

---

### TC_INFO_059: NRC 0x11 — Service Not Supported

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_059 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_007 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0xFFFF (undefined) |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_negative_responses.py::test_nrc_service_not_supported` |

**Preconditions:** ECU in extended session; stub NRC 0x11

**Test Steps:**
1. `RDBI(0xFFFF)` — unallocated / unsupported DID

**Expected Result:** NRC 0x11 (ServiceNotSupported)

**Pass Criteria:** `response.nrc == 0x11`

---

### TC_INFO_060: NRC 0x31 — Request Out of Range

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_060 |
| **Priority** | P2 — High |
| **Requirement IDs** | SYS_REQ_INFO_007 |
| **UDS Service** | 0x22 ReadDataByIdentifier |
| **DID / DTC** | DID 0x0000 (invalid) |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.negative` `@pytest.mark.regression` |
| **Test Type** | Negative |
| **Automation File** | `tests/uds/test_negative_responses.py::test_nrc_request_out_of_range_invalid_did` |

**Preconditions:** Extended session; stub NRC 0x31

**Test Steps:**
1. `RDBI(0x0000)`

**Expected Result:** NRC 0x31 (RequestOutOfRange)

**Pass Criteria:** `response.nrc == 0x31`

---

### TC_INFO_061: Factory Reset Routine — Settings Restored

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_061 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | FUNC_REQ_INFO_013 |
| **UDS Service** | 0x31 RoutineControl |
| **DID / DTC** | Routine 0x0303 |
| **pytest Marker** | `@pytest.mark.uds` `@pytest.mark.regression` |
| **Test Type** | Functional Positive |
| **Automation File** | `tests/uds/test_routine_control.py::test_factory_reset_routine` |

> ⚠ **WARNING:** This resets all HMI settings. Run only on bench ECU.

**Preconditions:** Programming session; security unlock

**Test Steps:**
1. `RoutineControl(startRoutine, 0x0303 — factory_reset)`

**Expected Result:** Positive response; all settings reset

**Pass Criteria:** `response.positive == True`

---

### TC_INFO_062: Display Panel Comm Failure DTC — Fault Injection

| Attribute | Value |
|-----------|-------|
| **TC ID** | TC_INFO_062 |
| **Priority** | P1 — Critical |
| **Requirement IDs** | DTC_REQ_INFO_001 |
| **UDS Service** | 0x19 ReadDTCInformation |
| **DID / DTC** | DTC 0xB11001 |
| **pytest Marker** | `@pytest.mark.dtc` `@pytest.mark.regression` |
| **Test Type** | Fault Injection |
| **Automation File** | `tests/dtc/test_dtc_read.py::test_dtc_snapshot_after_injected_fault` |

**Preconditions:** Display panel I2C disconnected / synthetic DTC injected

**Test Steps:**
1. Inject display comm failure
2. `ReadDTCInformation(statusMask=0x08 — confirmed)`

**Expected Result:** DTC 0xB11001 confirmed

**Pass Criteria:** `0xB11001 in snapshot.confirmed_dtcs codes`

---

## 5. Traceability Matrix

### 5.1 Test Cases → Requirements

| TC ID | Requirement ID(s) | Priority | UDS Service | Marker |
|-------|-------------------|----------|-------------|--------|
| TC_INFO_001 | SYS_REQ_INFO_001, 002 | P1 | 0x10 DSC | smoke |
| TC_INFO_002 | SYS_REQ_INFO_001, 002 | P1 | 0x10 DSC | smoke |
| TC_INFO_003 | SYS_REQ_INFO_002 | P1 | 0x10 DSC | regression |
| TC_INFO_004 | SYS_REQ_INFO_002 | P2 | 0x10 DSC | regression |
| TC_INFO_005 | SYS_REQ_INFO_002 | P1 | 0x10 DSC | regression |
| TC_INFO_006 | SYS_REQ_INFO_001 | P1 | 0x11 ECUReset | smoke |
| TC_INFO_007 | SYS_REQ_INFO_003 | P1 | 0x27 SA | security, smoke |
| TC_INFO_008 | SYS_REQ_INFO_003 | P1 | 0x27 SA | security, smoke |
| TC_INFO_009 | SYS_REQ_INFO_003 | P1 | 0x27 SA | security, negative |
| TC_INFO_010 | SYS_REQ_INFO_003 | P1 | 0x27 SA | security, regression |
| TC_INFO_011 | SYS_REQ_INFO_003, 007 | P2 | 0x27 SA | security, negative |
| TC_INFO_012 | SYS_REQ_INFO_001 | P2 | 0x3E TP | smoke |
| TC_INFO_013 | SYS_REQ_INFO_001 | P3 | 0x3E TP | smoke |
| TC_INFO_014 | SYS_REQ_INFO_001 | P3 | 0x3E TP | regression |
| TC_INFO_015 | SYS_REQ_INFO_004 | P1 | 0x22 RDBI | smoke |
| TC_INFO_016 | SYS_REQ_INFO_004 | P1 | 0x22 RDBI | smoke |
| TC_INFO_017 | FUNC_REQ_INFO_010 | P2 | 0x2E WDBI | regression |
| TC_INFO_018 | SYS_REQ_INFO_007 | P2 | 0x2E WDBI | negative |
| TC_INFO_019 | SYS_REQ_INFO_007 | P2 | 0x2E WDBI | negative |
| TC_INFO_020 | SYS_REQ_INFO_004 | P2 | 0x22 RDBI | parametrize |
| TC_INFO_021 | FUNC_REQ_INFO_001 | P1 | 0x22 RDBI | bluetooth, smoke |
| TC_INFO_022 | FUNC_REQ_INFO_002 | P2 | 0x22 RDBI | bluetooth, smoke |
| TC_INFO_023 | FUNC_REQ_INFO_003 | P2 | 0x22 RDBI | bluetooth, regression |
| TC_INFO_024 | FUNC_REQ_INFO_003 | P2 | 0x22 RDBI | bluetooth, regression |
| TC_INFO_025 | DTC_REQ_INFO_002 | P1 | 0x19 ReadDTC | bluetooth, dtc |
| TC_INFO_026 | FUNC_REQ_INFO_004 | P1 | 0x22 RDBI | usb_media, smoke |
| TC_INFO_027 | FUNC_REQ_INFO_004 | P2 | 0x22 RDBI | usb_media, smoke |
| TC_INFO_028 | FUNC_REQ_INFO_005 | P2 | 0x22 RDBI | usb_media, regression |
| TC_INFO_029 | DTC_REQ_INFO_003 | P1 | 0x19 ReadDTC | usb_media, dtc |
| TC_INFO_030 | FUNC_REQ_INFO_006 | P1 | 0x22 RDBI | network, smoke |
| TC_INFO_031 | FUNC_REQ_INFO_006 | P2 | 0x22 RDBI | network, smoke |
| TC_INFO_032 | FUNC_REQ_INFO_006 | P2 | 0x22 RDBI | network, regression |
| TC_INFO_033 | SYS_REQ_INFO_006 | P2 | 0x31 RC | network, regression |
| TC_INFO_034 | FUNC_REQ_INFO_007 | P1 | 0x22 RDBI | radio, smoke |
| TC_INFO_035 | FUNC_REQ_INFO_007 | P2 | 0x2E WDBI | radio, regression |
| TC_INFO_036 | FUNC_REQ_INFO_007 | P2 | 0x22 RDBI | radio, regression |
| TC_INFO_037 | FUNC_REQ_INFO_008 | P1 | 0x22 RDBI | navigation, smoke |
| TC_INFO_038 | FUNC_REQ_INFO_008 | P2 | 0x22 RDBI | navigation, smoke |
| TC_INFO_039 | SYS_REQ_INFO_006, FUNC_REQ_INFO_008 | P2 | 0x31 RC | navigation, regression |
| TC_INFO_040 | DTC_REQ_INFO_004 | P1 | 0x19 ReadDTC | navigation, dtc |
| TC_INFO_041 | FUNC_REQ_INFO_009 | P2 | 0x22 RDBI | voice, smoke |
| TC_INFO_042 | FUNC_REQ_INFO_009 | P2 | 0x22 RDBI | voice, smoke |
| TC_INFO_043 | FUNC_REQ_INFO_010 | P2 | 0x22 RDBI | display, smoke |
| TC_INFO_044 | FUNC_REQ_INFO_010 | P2 | 0x22+0x2E | display, regression |
| TC_INFO_045 | FUNC_REQ_INFO_010 | P2 | 0x22 RDBI | display, regression |
| TC_INFO_046 | SYS_REQ_INFO_006 | P2 | 0x31 RC | display, regression |
| TC_INFO_047 | FUNC_REQ_INFO_015 | P2 | 0x2F IOCtrl | display, io_control |
| TC_INFO_048 | FUNC_REQ_INFO_014 | P1 | 0x22 RDBI | audio, smoke |
| TC_INFO_049 | FUNC_REQ_INFO_014 | P2 | 0x22+0x2E | audio, smoke |
| TC_INFO_050 | DTC_REQ_INFO_005 | P1 | 0x19 ReadDTC | audio, dtc |
| TC_INFO_051 | FUNC_REQ_INFO_011 | P2 | 0x22 RDBI | projection, smoke |
| TC_INFO_052 | FUNC_REQ_INFO_011 | P2 | 0x22 RDBI | projection, smoke |
| TC_INFO_053 | FUNC_REQ_INFO_011 | P2 | 0x31 RC | projection, regression |
| TC_INFO_054 | FUNC_REQ_INFO_012 | P2 | 0x22 RDBI | ota, smoke |
| TC_INFO_055 | SYS_REQ_INFO_006 | P2 | 0x31 RC | ota, regression |
| TC_INFO_056 | SYS_REQ_INFO_005 | P1 | 0x19 ReadDTC | dtc, smoke |
| TC_INFO_057 | SYS_REQ_INFO_005 | P1 | 0x14 ClearDTC | dtc, smoke |
| TC_INFO_058 | SYS_REQ_INFO_005 | P2 | 0x19 ReadDTC | dtc, regression |
| TC_INFO_059 | SYS_REQ_INFO_007 | P2 | 0x22 RDBI | negative |
| TC_INFO_060 | SYS_REQ_INFO_007 | P2 | 0x22 RDBI | negative |
| TC_INFO_061 | FUNC_REQ_INFO_013 | P1 | 0x31 RC | regression |
| TC_INFO_062 | DTC_REQ_INFO_001 | P1 | 0x19 ReadDTC | dtc, regression |

### 5.2 Requirements → Test Cases (Reverse Traceability)

| Requirement ID | Covered By | Coverage |
|----------------|-----------|----------|
| SYS_REQ_INFO_001 | TC_INFO_001, 002, 006, 012–014 | ✅ Full |
| SYS_REQ_INFO_002 | TC_INFO_001–005 | ✅ Full |
| SYS_REQ_INFO_003 | TC_INFO_007–011 | ✅ Full |
| SYS_REQ_INFO_004 | TC_INFO_015, 016, 020 | ✅ Full |
| SYS_REQ_INFO_005 | TC_INFO_025, 029, 040, 050, 056–058, 062 | ✅ Full |
| SYS_REQ_INFO_006 | TC_INFO_033, 039, 046, 053, 055, 061 | ✅ Full |
| SYS_REQ_INFO_007 | TC_INFO_018, 019, 059, 060 | ✅ Full |
| SYS_REQ_INFO_008 | TC_INFO_047 | ✅ Full |
| FUNC_REQ_INFO_001 | TC_INFO_021 | ✅ Full |
| FUNC_REQ_INFO_002 | TC_INFO_022 | ✅ Full |
| FUNC_REQ_INFO_003 | TC_INFO_023, 024 | ✅ Full |
| FUNC_REQ_INFO_004 | TC_INFO_026, 027 | ✅ Full |
| FUNC_REQ_INFO_005 | TC_INFO_028 | ✅ Full |
| FUNC_REQ_INFO_006 | TC_INFO_030, 031, 032 | ✅ Full |
| FUNC_REQ_INFO_007 | TC_INFO_034, 035, 036 | ✅ Full |
| FUNC_REQ_INFO_008 | TC_INFO_037, 038, 039 | ✅ Full |
| FUNC_REQ_INFO_009 | TC_INFO_041, 042 | ✅ Full |
| FUNC_REQ_INFO_010 | TC_INFO_017, 043–045 | ✅ Full |
| FUNC_REQ_INFO_011 | TC_INFO_051, 052, 053 | ✅ Full |
| FUNC_REQ_INFO_012 | TC_INFO_054, 055 | ✅ Full |
| FUNC_REQ_INFO_013 | TC_INFO_061 | ✅ Full |
| FUNC_REQ_INFO_014 | TC_INFO_048, 049 | ✅ Full |
| FUNC_REQ_INFO_015 | TC_INFO_047 | ✅ Full |
| DTC_REQ_INFO_001 | TC_INFO_062 | ✅ Full |
| DTC_REQ_INFO_002 | TC_INFO_025 | ✅ Full |
| DTC_REQ_INFO_003 | TC_INFO_029 | ✅ Full |
| DTC_REQ_INFO_004 | TC_INFO_040 | ✅ Full |
| DTC_REQ_INFO_005 | TC_INFO_050 | ✅ Full |

### 5.3 Test Execution Summary

| Category | Count |
|----------|-------|
| **Total test cases** | **62** |
| P1 — Critical | 24 |
| P2 — High | 33 |
| P3 — Medium | 5 |
| Positive tests | 47 |
| Negative tests | 8 |
| Fault injection / DTC | 7 |
| Smoke tests | 25 |
| Regression tests | 37 |
| Feature-level functional | 31 |
| UDS service layer | 20 |
| DTC management | 11 |

### 5.4 Feature Coverage Matrix

| Feature Area | TCs | Smoke | Regression | DTC |
|-------------|-----|-------|------------|-----|
| UDS Session Control | 6 | 3 | 3 | — |
| Security Access | 5 | 2 | 2 | — |
| TesterPresent | 3 | 2 | 1 | — |
| RDBI / WDBI | 6 | 2 | 4 | — |
| Routine Control | 1 | — | 1 | — |
| IO Control | 1 | — | 1 | — |
| Negative Responses | 4 | — | 4 | — |
| DTC Read/Clear | 4 | 2 | 2 | 4 |
| Bluetooth | 5 | 2 | 2 | 1 |
| USB / Media | 4 | 2 | 1 | 1 |
| Wi-Fi / Network | 4 | 2 | 1 | — |
| Radio / Tuner | 3 | 1 | 2 | — |
| Navigation / GPS | 4 | 2 | 1 | 1 |
| Voice Recognition | 2 | 2 | — | — |
| Display / HMI | 5 | 2 | 2 | 1 |
| Audio Amplifier | 3 | 2 | — | 1 |
| CarPlay / AA | 3 | 2 | 1 | — |
| OTA / Software | 2 | 1 | 1 | — |
| Factory Reset | 1 | — | 1 | — |
| Fault Injection | 1 | — | 1 | 1 |

---

*Document end — TCD-INFO-001 v1.0*
