# Telematics ECU & OTA Testing — Complete Validation Guide
## Test Plans · HIL Setup · Test Cases · CAPL Scripts · Defect Patterns

---

## Table of Contents

1. [Telematics Test Scope & Architecture](#1-telematics-test-scope--architecture)
2. [Test Environment Setup](#2-test-environment-setup)
3. [TCU Functional Test Plan](#3-tcu-functional-test-plan)
4. [Cellular Connectivity Testing](#4-cellular-connectivity-testing)
5. [Remote Diagnostics Testing (DoIP/UDS)](#5-remote-diagnostics-testing-doipuds)
6. [OTA Update Test Plan](#6-ota-update-test-plan)
7. [OTA Negative / Failure Injection Tests](#7-ota-negative--failure-injection-tests)
8. [OTA Security Testing](#8-ota-security-testing)
9. [GNSS & eCall Testing](#9-gnss--ecall-testing)
10. [Power Mode & Wake-Up Testing](#10-power-mode--wake-up-testing)
11. [CAPL Scripts for Telematics Testing](#11-capl-scripts-for-telematics-testing)
12. [Python Test Automation Scripts](#12-python-test-automation-scripts)
13. [KPIs, Acceptance Criteria & Metrics](#13-kpis-acceptance-criteria--metrics)
14. [Common Defects & RCA Patterns](#14-common-defects--rca-patterns)

---

## 1. Telematics Test Scope & Architecture

### 1.1 What Telematics Testing Covers

```
┌────────────────────────────────────────────────────────────────────┐
│                      TELEMATICS TEST SCOPE                         │
│                                                                    │
│  ┌─────────────────┐   ┌──────────────────┐   ┌────────────────┐  │
│  │ Hardware/HW     │   │ Software/SW       │   │ Integration    │  │
│  │ Layer           │   │ Layer             │   │ Layer          │  │
│  ├─────────────────┤   ├──────────────────┤   ├────────────────┤  │
│  │ - RF conducted  │   │ - AT command API  │   │ - CAN gateway  │  │
│  │   performance   │   │ - MQTT protocol   │   │   routing      │  │
│  │ - Antenna VSWR  │   │ - OTA client      │   │ - DoIP end-to- │  │
│  │ - Power rail    │   │ - eCall stack     │   │   end chain    │  │
│  │   verification  │   │ - GNSS parser     │   │ - V2X message  │  │
│  │ - EMC limits    │   │ - SecOC on CAN    │   │   passing      │  │
│  │ - Temp cycling  │   │ - Key provisioning│   │ - Backend API  │  │
│  └─────────────────┘   └──────────────────┘   └────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 TCU Interface Map (Test Points)

```
EXTERNAL (test stimuli injected here):
  [Cellular RF]   ← RF attenuator / channel emulator (CMW500 / R&S CMW500)
  [GNSS RF]       ← GNSS signal simulator (Spirent GSS9790 / u-blox)
  [Power supply]  ← Keysight bench PSU (simulate battery / ignition line)
  [CAN bus]       ← Vector CANoe interface (VN1640 / VN7600)
  [LIN bus]       ← Vector VN1630 LIN interface
  [Vehicle Ethernet (100BASE-T1)] ← Vector VN5610 Ethernet interface
  [JTAG/UART debug] ← J-Link / FTDI for firmware debug

INTERNAL (observability):
  [UART log]      → TCU application log (timestamp, severity, module)
  [ETH: Wireshark]→ SOME/IP, DoIP, MQTT traffic capture
  [CAN trace]     → CANalyzer / CANoe trace for all CAN messages
  [HSM debug API] → Crypto operation results / error codes
```

---

## 2. Test Environment Setup

### 2.1 HIL (Hardware-in-the-Loop) Bench Layout

```
┌────────────────────────────────────────────────────────────────────────┐
│                    TELEMATICS HIL BENCH                                │
│                                                                        │
│  ┌──────────────┐    ┌──────────────────────┐    ┌─────────────────┐  │
│  │  Test PC     │    │    REAL TCU (DUT)     │    │ RF Equipment    │  │
│  │              │    │                      │    │                 │  │
│  │ CANoe        │◄──►│  CAN-FD bus (2×)      │    │ RF Attenuator   │  │
│  │ vTESTstudio  │    │  100BASE-T1 ETH       │◄──►│ (30 dB pad)     │  │
│  │ Python suite │    │  LIN bus              │    │ CMW500 / R&S    │  │
│  │ Wireshark    │    │  Debug UART           │    │ LTE simulator   │  │
│  └──────────────┘    │  GNSS SMA port        │◄──►│                 │  │
│         │            │  Power: 12V ± 2V      │    │ Spirent GNSS    │  │
│         │            └──────────────────────┘    │ simulator       │  │
│  ┌──────▼───────┐                                └─────────────────┘  │
│  │  OTA Backend │                                                      │
│  │  (local      │    ┌──────────────────────┐                         │
│  │   server or  │    │  Network Impairment  │                         │
│  │   staging    │    │  Box (Spirent        │                         │
│  │   cloud env) │    │  Avalanche / tc netem│                         │
│  └──────────────┘    │  packet loss / delay │                         │
│                      └──────────────────────┘                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Software Stack on Test PC

| Tool | Version / Config | Purpose |
|------|-----------------|---------|
| Vector CANoe | 16.x | CAN/LIN simulation, CAPL test modules |
| vTESTstudio | 6.x | Test case management, test report generation |
| Wireshark | 4.x | SOME/IP, DoIP, MQTT, TLS traffic analysis |
| Python 3.11+ | pytest + python-udsoncan + paho-mqtt | OTA & diagnostic test automation |
| openssl CLI | 3.x | Certificate inspection, TLS handshake debug |
| CMW500 test suite | Rohde & Schwarz CMWrun | LTE/5G protocol conformance tests |
| Spirent iTest | — | GNSS scenario playback |
| Git + CI | Jenkins / GitLab CI | Automated nightly regression |

### 2.3 Network Topology for OTA Testing

```
[OTA Test Server]──[TLS 1.3]──[Firewall/Proxy]──[LTE Network Emulator]
                                                         │
                                              [TCU modem RF port]
                                                         │
                                              [TCU Application]
                                                         │
                                              [DoIP/CAN GW]
                                                         │
                                    ┌────────────────────┘
                                    │
                               [Target ECUs on CAN bus]
```

---

## 3. TCU Functional Test Plan

### 3.1 Test Suite Structure

```
TCU_FunctionalTests/
├── TC-TCU-001 to 020  Boot & Initialisation
├── TC-TCU-021 to 040  Cellular Registration
├── TC-TCU-041 to 060  GNSS & Positioning
├── TC-TCU-061 to 080  CAN Gateway Routing
├── TC-TCU-081 to 100  Remote Diagnostics (DoIP/UDS)
├── TC-TCU-101 to 130  OTA Update (Normal path)
├── TC-TCU-131 to 160  OTA Failure & Rollback
├── TC-TCU-161 to 180  OTA Security
├── TC-TCU-181 to 200  Power Management
└── TC-TCU-201 to 220  eCall / ERA-GLONASS
```

### 3.2 Boot & Initialisation Tests

| TC-ID | Test Name | Precondition | Steps | Expected Result | Priority |
|-------|-----------|-------------|-------|-----------------|---------|
| TC-TCU-001 | Cold Boot Timing | Power off state | Apply 12V; measure time to first MQTT heartbeat | MQTT connect ≤ 15 s from power-on | High |
| TC-TCU-002 | Warm Restart Recovery | TCU running, trigger SW reset | Software reboot via AT command; measure restart time | Reconnect + MQTT ≤ 8 s | High |
| TC-TCU-003 | Secure Boot PASS | Valid signed firmware | Normal power-on | Boot completes; no DTC for SecBoot failure | High |
| TC-TCU-004 | Secure Boot FAIL — corrupted image | Modify 1 byte in firmware CRC area via flash tool | Apply power | Boot halts; enters BL recovery mode; DTC set; no application code executes | Critical |
| TC-TCU-005 | WDT recovery from application hang | Inject infinite loop via debug port | — | HW watchdog fires in ≤ WDT timeout; system restarts; DTC logged | High |
| TC-TCU-006 | EEPROM / NVM integrity check | Pre-corrupt NVM header checksum | Power-on | NVM reports corruption; defaults loaded; DEM event raised | Medium |
| TC-TCU-007 | Voltage undervoltage (8V) | Set PSU to 8V | Apply power | TCU does not boot; no irreversible state change | High |
| TC-TCU-008 | Voltage over-voltage (16V) | Set PSU to 16V | Apply power | TCU enters protection; no damage; resumes at 14.4V | High |

### 3.3 Sample Detailed Test Case

```
TEST CASE: TC-TCU-004
Title:    Secure Boot FAIL — corrupted firmware image
Version:  2.1
Author:   Telematics Test Team
Reviewed: [Name / Date]

OBJECTIVE:
  Verify that the TCU bootloader rejects a firmware image whose signature
  does not match, preventing execution of potentially malicious or corrupted SW.

PRECONDITIONS:
  1. TCU on bench with JTAG access (test-only; JTAG disabled in production)
  2. Baseline: known-good signed firmware flashed; TCU boots normally
  3. Debug UART connected; log capture running

TEST STEPS:
  1. Using flash tool (SEGGER J-Flash), modify byte at offset 0x8FF00
     (within signature region, last 256 bytes of firmware): flip 0xAB → 0xAC
  2. Verify flash modification via read-back
  3. Disconnect JTAG; power-cycle TCU
  4. Monitor UART log for 30 seconds
  5. Monitor CAN bus for any TCU messages
  6. Connect via UDS (SID 0x19) to read DTCs

EXPECTED RESULTS:
  Step 3: Boot log shows: "[SECBOOT] Firmware signature INVALID — halting"
  Step 4: Application-layer messages do NOT appear on UART
  Step 5: No MQTT or CAN application frames transmitted by TCU
  Step 6: DTC P1800 (Secure Boot Failure) present as confirmed active

ACCEPTANCE CRITERIA:
  PASS: Boot halted within 2 s of power-on; DTC set; no application execution
  FAIL: Any application message observed after signature failure is logged

CLEANUP:
  Reflash valid firmware; verify TC-TCU-001 (normal boot) passes before next test
```

---

## 4. Cellular Connectivity Testing

### 4.1 LTE Registration Test Cases

| TC-ID | Test Name | Method | Accept Criteria |
|-------|-----------|--------|----------------|
| TC-TCU-021 | LTE cold registration | Power-on; measure time to IP assignment | ≤ 10 s |
| TC-TCU-022 | LTE re-registration after signal loss | RF attenuator: 0 dB → 90 dB → 0 dB | Re-register ≤ 5 s after signal restored |
| TC-TCU-023 | Fallback PLMN selection | Block preferred PLMN in CMW500 config | TCU connects to fallback PLMN within 30 s |
| TC-TCU-024 | Roaming activation | Set CMW500 to foreign PLMN; enable roaming on eSIM | TCU registers; data active; billing tagged as roaming |
| TC-TCU-025 | RSRP threshold handover | Sweep signal −80 dBm → −115 dBm | No data loss > 500 ms during cell reselection |
| TC-TCU-026 | 5G NSA handover (if modem supports) | CMW500: LTE anchor + 5G NR secondary | Throughput boost; fallback to LTE when 5G unavailable |
| TC-TCU-027 | eSIM profile switch (test→production) | Trigger RSP (Remote SIM Provisioning) | Profile switch completes; cellular active on production APN |
| TC-TCU-028 | SIM profile lock after 10 attach failures | Block APN on CMW500; wait for retry exhaustion | SIM does not lock; alert sent to OEM backend |

### 4.2 RF Signal Quality Characterisation

```
Test procedure — conducted RF sensitivity sweep:

Equipment:
  - Rohde & Schwarz CMW500 LTE tester
  - RF attenuator (variable, 0–100 dB)
  - Power meter

Steps:
  1. Connect CMW500 TX output → attenuator → TCU RF port (LTE antenna)
  2. Set CMW500 to LTE Band 3 (1800 MHz) — most common European band
  3. Set attenuation = 0 dB; verify LTE registered; start iperf3 TCP session
  4. Increase attenuation in 5 dB steps; record at each step:
     a. RSRP (dBm) — reported by TCU via AT+CEREG / AT+CESQ
     b. RSRQ (dB)
     c. SINR (dB)
     d. TCP throughput (iperf3, 10 s average)
     e. Packet loss (%)
  5. Find: minimum RSRP at which TCP session remains active (sensitivity floor)
  6. Repeat for LTE Band 20 (800 MHz) and LTE Band 1 (2100 MHz)

Acceptance Criteria:
  - TCP data active for RSRP ≥ −110 dBm
  - Throughput ≥ 100 kbps at RSRP = −100 dBm (adequate for OTA delta packages)
  - Data reconnect within 5 s after RSRP recovers from < −115 dBm

Key AT Commands for Signal Query:
  AT+CESQ          → RSSI, BER
  AT+QCSQ          → RSRP, RSRQ, RSSNR (Quectel modems)
  AT+CREG?         → Registration status
  AT+CGDCONT?      → PDP context / APN
  AT+CIMI          → IMSI
  AT+CGSN          → IMEI
  AT+CGACT?        → PDP context activation status
```

---

## 5. Remote Diagnostics Testing (DoIP/UDS)

### 5.1 DoIP Protocol Test Cases

| TC-ID | Test Name | Steps | Expected |
|-------|-----------|-------|---------|
| TC-TCU-061 | DoIP routing activation | Send DoIP Routing Activation Request (0x0005) | Response 0x0006 with status=0x10 (success) |
| TC-TCU-062 | UDS DTC read via DoIP | SID 0x10 0x03 → SID 0x19 0x02 0xFF | DTC list in ISO format returned within 5 s |
| TC-TCU-063 | DoIP response timeout | Send partial DoIP message; stop; wait | TCU closes TCP connection after 2 s idle (T_TCP_General_Inactivity) |
| TC-TCU-064 | DoIP invalid source address | Send request with unknown logical address | NACK code 0x00 (incorrect pattern) or 0x04 (unknown source address) |
| TC-TCU-065 | Concurrent DoIP + OTA session | Start OTA download; then open DoIP session | DoIP returns NRC 0x22 (ConditionsNotCorrect); OTA continues |
| TC-TCU-066 | DoIP over cellular (latency) | Route diagnostic request via 4G; add 150 ms latency via netem | UDS response received; P2 timer extended correctly via 0x78 NRC |
| TC-TCU-067 | CAN gateway routing: remote ECU | Request DTC from Engine ECU via DoIP → TCU gateway → CAN | Engine ECU DTC data returned correctly |

### 5.2 Remote UDS Session Script (Python)

```python
"""
tcu_remote_diag_test.py
Tests remote diagnostic access via TCU DoIP gateway.
Requires: python-udsoncan, python-doip-client
"""

import doipclient
import udsoncan
import logging
import pytest

TCU_IP   = "192.168.10.50"   # TCU Ethernet IP (or cellular IP in HIL)
TCU_PORT = 13400              # DoIP standard port

# Logical addresses — from vehicle network topology document
GATEWAY_LOGICAL_ADDR  = 0x0E00
ENGINE_ECU_LOGICAL    = 0x0720
TESTER_LOGICAL_ADDR   = 0x0E01


class TestRemoteDiagnostics:

    @pytest.fixture(autouse=True)
    def setup_doip(self):
        """Establish DoIP TCP connection to TCU."""
        self.doip_conn = doipclient.DoIPClient(TCU_IP, TCU_PORT,
                                               tester_logical_address=TESTER_LOGICAL_ADDR)
        self.doip_conn.request_activation()
        yield
        self.doip_conn.close()

    def test_routing_activation(self):
        """TC-TCU-061: DoIP routing activation must succeed."""
        result = self.doip_conn.request_activation()
        assert result.response_code == 0x10, \
            f"Routing activation failed: code={result.response_code:#04x}"

    def test_engine_ecu_dtc_read(self):
        """TC-TCU-062: Read confirmed DTCs from Engine ECU via CAN gateway."""
        # Open extended diagnostic session
        req = udsoncan.services.DiagnosticSessionControl.make_request(0x03)
        resp = self.doip_conn.send_doip(req.data, ENGINE_ECU_LOGICAL)
        assert resp[0] == 0x50, "Session open failed"

        # Request DTC (SID 0x19 sub 0x02, all confirmed)
        req_dtc = bytes([0x19, 0x02, 0xFF])
        resp_dtc = self.doip_conn.send_doip(req_dtc, ENGINE_ECU_LOGICAL)

        assert resp_dtc[0] == 0x59, f"DTC read NRC: {resp_dtc[1]:#04x}"

        # Parse DTC list
        dtc_records = []
        idx = 3
        while idx + 3 < len(resp_dtc):
            dtc_bytes = resp_dtc[idx:idx+3]
            status    = resp_dtc[idx+3]
            dtc_id    = (dtc_bytes[0] << 16) | (dtc_bytes[1] << 8) | dtc_bytes[2]
            dtc_records.append({'dtc': f"{dtc_id:#08x}", 'status': f"{status:#04x}"})
            idx += 4

        logging.info(f"DTCs found: {dtc_records}")
        # Test does not assert specific DTC count — logs for analysis
        return dtc_records

    def test_concurrent_doip_ota_rejected(self):
        """TC-TCU-065: DoIP session rejected while OTA update in progress."""
        # Trigger OTA update start on TCU (via MQTT command)
        import paho.mqtt.client as mqtt
        mq = mqtt.Client()
        mq.connect("localhost", 1883)
        mq.publish("tcu/cmd/ota", '{"action":"start_update","pkg_id":"PKG_001"}')

        import time
        time.sleep(2)  # Allow OTA state machine to enter DOWNLOADING state

        # Attempt to open DoIP diagnostic session — should be rejected
        req = bytes([0x10, 0x03])
        resp = self.doip_conn.send_doip(req, ENGINE_ECU_LOGICAL)

        # Expect NRC 0x22 (ConditionsNotCorrect)
        assert resp[0] == 0x7F, "Expected negative response"
        assert resp[2] == 0x22, f"Expected NRC 0x22, got {resp[2]:#04x}"
        mq.disconnect()
```

---

## 6. OTA Update Test Plan

### 6.1 OTA Update State Machine

```
                 [IDLE]
                   │
         OTA notification received (MQTT)
                   │
            [CHECKING_UPDATE]
                   │ Compatibility check PASS
                   │ (VIN, HW rev, SW version match)
                   │
           [CONSENT_PENDING]
                   │ Driver / OEM consent granted
                   │
          [DOWNLOADING]
                   │ Package download complete
                   │
          [VALIDATING]       ← SHA-256 + RSA signature check
                   │ Validation PASS
                   │
    ┌──────────────▼──────────────┐
    │     Pre-conditions check:    │
    │  - Ignition OFF              │
    │  - Battery SOC > 30%         │
    │  - Parking brake engaged     │
    └──────────────┬──────────────┘
                   │ All conditions met
                   │
            [INSTALLING]       ← Flash write via UDS 0x34/0x36/0x37
                   │ Flash complete + CRC check PASS
                   │
            [VERIFYING]        ← Post-flash signature + hash
                   │ PASS
                   │
           [ACTIVATING]        ← ECU reset; boot new image
                   │ Secure boot PASS; new version confirmed
                   │
             [COMPLETE]        ← RXSWIN updated; report to backend

   [FAILED at any step] ──────────────────────────►  [ROLLBACK]
                                                          │
                                                   Restore previous partition
                                                          │
                                                   [IDLE with previous SW]
```

### 6.2 OTA Normal Path Test Cases

| TC-ID | Test Name | Precondition | Steps | Expected | Priority |
|-------|-----------|-------------|-------|---------|---------|
| TC-OTA-001 | Full OTA happy path | Valid pkg on server; vehicle parked | Backend pushes OTA notification; verify each state | Version N+1 active after reboot; RXSWIN updated | Critical |
| TC-OTA-002 | Delta OTA update | Only changed binary sections in package | Push delta package | Only changed ECU partitions reflashed; unchanged partitions skipped | High |
| TC-OTA-003 | Multi-ECU campaign | Package targets 3 ECUs simultaneously | Push campaign | All 3 ECUs updated in dependency order; campaign completes; versions confirmed | High |
| TC-OTA-004 | OTA during charging | Vehicle plugged in; SOC 15% | Push OTA notification | OTA deferred until SOC > 30% (or user accepts at low SOC) | High |
| TC-OTA-005 | Staged rollout — wave 1 | 100 VINs in test fleet | Deploy to 1% cohort | Only 1% VINs receive notification; others ignored | Medium |
| TC-OTA-006 | RXSWIN update verification | Baseline RXSWIN known | Complete OTA cycle | Read RXSWIN via UDS 0x22 0xF1A2; value matches new version RXSWIN | High |
| TC-OTA-007 | Consent timeout | OTA pending consent; no driver action | Wait 7 days | OEM backend re-sends notification; consent prompt renewed | Medium |
| TC-OTA-008 | Campaign abort by OEM | 2% error rate exceeded in wave 1 | Backend aborts campaign | Vehicles not yet updating stop; vehicles mid-download: graceful stop or complete | High |

### 6.3 Detailed OTA Test Case — Happy Path

```
TEST CASE: TC-OTA-001
Title:    Complete OTA Update — Normal Path (Happy Path)
Version:  3.0

OBJECTIVE:
  Verify that a standard OTA update completes successfully: notification delivery,
  download, validation, pre-condition check, flash, post-flash verify, activation,
  RXSWIN update, and backend status report.

PRECONDITIONS:
  1. TCU running firmware version N (baseline)
  2. OTA test server running; firmware version N+1 package available (signed, correct VIN)
  3. LTE signal strength: RSRP > −95 dBm (good signal)
  4. Vehicle state: ignition OFF, parking brake ON, battery SOC 85%
  5. Test bench CAN simulation: CANoe simulates all required vehicle signals

TEST DATA:
  Package ID:       PKG_TEST_N1_001
  Package size:     12.4 MB (compressed)
  Package hash:     SHA-256 known value (stored in test reference)
  Target ECU:       TCU application firmware
  New version:      2.5.3
  New RXSWIN:       RXSWIN_EU_2025_0042

PROCEDURE:
  Step 1: Confirm baseline
    1a. Via UDS 0x22 0xF189: read current SW version → confirm "2.5.2"
    1b. Via MQTT: confirm TCU sends heartbeat with version "2.5.2"

  Step 2: Trigger OTA campaign on test server
    2a. Login to OTA backend test console
    2b. Create campaign targeting this vehicle's VIN
    2c. Associate PKG_TEST_N1_001; trigger immediate push

  Step 3: Observe notification delivery
    3a. Monitor MQTT topic: "vehicles/{VIN}/ota/notification"
    3b. TCU should publish acknowledgement within 30 s
    Checkpoint: notification_received timestamp recorded

  Step 4: Download phase monitoring
    4a. Monitor MQTT: "vehicles/{VIN}/ota/progress" — should report % progress
    4b. Monitor Wireshark: TCP stream to OTA server; confirm HTTPS + TLS 1.3
    4c. Record total download time; calculate throughput
    Checkpoint: download_complete message on MQTT

  Step 5: Validation
    5a. TCU internally validates signature and hash (no explicit test stimulus)
    5b. Monitor UART log for: "[OTA] Package signature OK — SHA256 match"
    Checkpoint: validation_complete log entry within 60 s of download complete

  Step 6: Pre-condition check
    6a. Verify CANoe is simulating: IgnStatus=OFF, ParkBrake=ON, BatterySoc=85
    6b. Monitor MQTT: "vehicles/{VIN}/ota/status" → "READY_TO_INSTALL"
    Checkpoint: READY_TO_INSTALL state reached

  Step 7: Flash installation
    7a. Monitor Wireshark: TCU → ECU CAN traffic (UDS SID 0x34 RequestDownload)
    7b. Monitor UART for flash write progress logs
    7c. Power supply: confirm power draw increases during flash (expected spike)
    Checkpoint: flash_complete log entry; UDS 0x37 (RequestTransferExit) seen on CAN

  Step 8: Post-flash verification
    8a. Monitor UART: "[OTA] Post-flash verification: SHA256 PASS, Signature PASS"
    Checkpoint: verification_pass log

  Step 9: ECU reset and activation
    9a. Monitor CAN for ECU reset frame (UDS 0x11 0x01 EcuReset)
    9b. Monitor CANoe: ECU reappears on CAN within 5 s
    9c. Check UART: "[SECBOOT] Firmware valid — booting version 2.5.3"

  Step 10: Campaign completion reporting
    10a. TCU publishes to MQTT: "vehicles/{VIN}/ota/result" → "SUCCESS"
    10b. OTA backend receives and marks campaign complete for this VIN
    10c. Read RXSWIN via UDS 0x22 0xF1A2 → must equal "RXSWIN_EU_2025_0042"
    10d. Read SW version via UDS 0x22 0xF189 → must equal "2.5.3"

EXPECTED RESULTS:
  - All 10 steps pass their checkpoints
  - Total OTA cycle time ≤ 30 minutes (for 12.4 MB package on 4G)
  - No DTCs set during or after OTA
  - TCU remains reachable via MQTT after activation
  - RXSWIN correctly updated in both ECU NVM and OTA backend DB

ROLLBACK: If step fails → see TC-OTA-R001 (rollback test suite)
```

---

## 7. OTA Negative / Failure Injection Tests

### 7.1 Network Interruption Tests

| TC-ID | Test Name | Injection | Expected Handling |
|-------|-----------|-----------|-----------------|
| TC-OTA-F001 | Download interrupted at 50% | RF attenuator: cut signal mid-download | Download resumes from byte offset when signal restored (HTTP Range request) |
| TC-OTA-F002 | Download interrupted at 99% | Cut signal 1 second before completion | Resume; not restart; completes from 99% position |
| TC-OTA-F003 | Network loss during flash write | Cut cellular during UDS 0x36 transfer | Flash paused; package re-validated on reconnect; flash resumes or clean rollback |
| TC-OTA-F004 | Server unavailable (404) | OTA server returns HTTP 404 | TCU logs error; retries after backoff (30 min); DEM event; campaign marked failed |
| TC-OTA-F005 | Slow network (2G speed: 50 kbps) | tc netem rate 50kbit on server interface | Download completes (slow); no timeout; throughput KPI flagged as LOW in report |
| TC-OTA-F006 | TLS certificate expired (injected) | Replace server TLS cert with expired cert | TCU rejects TLS handshake; download does not start; security DEM event |
| TC-OTA-F007 | DNS failure | Block DNS resolution on bench network | TCU uses hardcoded OTA server IP fallback (if configured) OR reports DNS_FAILURE |

### 7.2 Package Integrity Tests

| TC-ID | Test Name | Injection | Expected Handling |
|-------|-----------|-----------|-----------------|
| TC-OTA-F011 | Corrupted package (1 bit flip) | Flip bit at offset 0x10000 in .bin before serving | Hash check FAILS; package rejected; no flash; DEM event set |
| TC-OTA-F012 | Invalid signature (wrong key) | Sign package with a non-production private key | Signature verify FAILS; package rejected; "invalid signature" logged |
| TC-OTA-F013 | Replay of old package | Serve version N-1 package (previously applied) | Anti-rollback check FAILS; NRC 0x22 on version compare; rejected |
| TC-OTA-F014 | Wrong target ECU (different VIN) | Package signed for VIN XYZ; DUT is VIN ABC | VIN check FAILS; package rejected; no flash |
| TC-OTA-F015 | Package truncated (50% of expected size) | Serve incomplete package file | Download size mismatch; SHA-256 FAILS; rejected cleanly |

### 7.3 Power Interruption Tests (Most Critical)

```
TEST CASE: TC-OTA-F020
Title:    Power cut during flash write — must rollback cleanly

OBJECTIVE:
  Verify ECU does NOT become permanently bricked when power is cut
  during the active flash write operation. Rollback must be automatic.

SETUP:
  - Power supply connected to relay (controlled by test PC GPIO)
  - Oscilloscope probe on TCU power rail to timestamp the cut precisely
  - UDS monitor: log every 0x36 (TransferData) block received

INJECTION POINTS (run as separate test instances):
  Point A: Power cut after 10% of firmware written (0x36 block 10 of 100)
  Point B: Power cut after 50% written
  Point C: Power cut after 90% written
  Point D: Power cut during final 0x37 RequestTransferExit

PROCEDURE:
  1. Start OTA update normally via TC-OTA-001 steps 1–6
  2. Once UDS 0x36 observed on CAN: trigger relay open at injection point
  3. Restore power after 5 seconds
  4. Monitor boot sequence on UART

EXPECTED RESULTS at each injection point:
  - UART shows: "[BL] Incomplete flash detected — partition B marked invalid"
  - UART shows: "[BL] Restoring partition A (previous firmware)"
  - Application boots to PREVIOUS firmware version (N, not N+1)
  - No DTC for: SecBoot fail, NVM corruption, watchdog (except expected power-fail DTC)
  - UDS 0x22 0xF189 returns version N (not N+1, not garbage)
  - OTA backend receives: "INSTALL_FAILED — POWER_INTERRUPT" for that VIN
  - Backend schedules retry campaign automatically

ACCEPTANCE CRITERIA:
  PASS at ALL 4 injection points: no brick, correct version after recovery
```

### 7.4 Pre-condition Violation Tests

| TC-ID | Test Name | Condition Violated | Expected |
|-------|-----------|-------------------|---------|
| TC-OTA-F030 | Ignition ON during install attempt | Simulate IgnStatus=ON in CANoe | Installation deferred; MQTT status = WAITING_FOR_CONDITIONS |
| TC-OTA-F031 | Low battery (SOC < 30%) | Simulate BatterySoc = 25 in CANoe | OTA postponed; user notification sent; retry when SOC > 30% |
| TC-OTA-F032 | Vehicle moving | Simulate VehicleSpeed = 50 km/h | OTA download may continue; install step deferred until speed = 0 |
| TC-OTA-F033 | Parking brake not engaged | Simulate ParkBrake = OFF | Installation deferred for safety-critical ECU targets |

---

## 8. OTA Security Testing

### 8.1 Security Attack Test Cases

| TC-ID | Attack | Method | Expected Defence |
|-------|--------|--------|-----------------|
| TC-OTA-S001 | Man-in-the-Middle (MITM) | ARP spoof on test LAN; intercept HTTPS | TLS cert pinning rejects; download aborted |
| TC-OTA-S002 | Package substitution | Replace valid package with custom binary on server | Signature validation FAILS; flash blocked |
| TC-OTA-S003 | Downgrade attack | Push older version with valid old signature | Anti-rollback version check FAILS; NRC 0x26 |
| TC-OTA-S004 | Replay of valid campaign | Re-trigger an already-applied campaign | TCU compares installed version; "already up to date"; no re-flash |
| TC-OTA-S005 | Forged MQTT OTA command | Publish crafted MQTT message to ota/cmd topic | TCU validates command source (mutual TLS / token); ignores unauthenticated cmd |
| TC-OTA-S006 | DoS: flood OTA server requests | Send 1000 requests/s from test client | Server rate-limits by VIN; TCU not affected; legitimate requests still served |
| TC-OTA-S007 | Certificate pinning bypass | Present self-signed cert with correct CN | TCU validates against pinned CA fingerprint; rejects self-signed |

### 8.2 TLS Validation Script

```python
"""
ota_tls_validation.py
Verify TCU OTA client enforces TLS correctly.
"""

import ssl
import socket
import subprocess
import pytest

OTA_SERVER_HOST = "ota-test.oem-staging.com"
OTA_SERVER_PORT = 443


def test_tls13_only():
    """TCU must reject TLS 1.2 — only TLS 1.3 allowed."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2   # Force TLS 1.2
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE

    with pytest.raises(ssl.SSLError):
        with socket.create_connection((OTA_SERVER_HOST, OTA_SERVER_PORT)) as sock:
            with ctx.wrap_socket(sock, server_hostname=OTA_SERVER_HOST):
                pass  # Should not reach here


def test_expired_cert_rejected():
    """TCU must reject expired server certificate."""
    # openssl s_client with expired cert test:
    result = subprocess.run([
        "openssl", "s_client",
        "-connect", f"{OTA_SERVER_HOST}:{OTA_SERVER_PORT}",
        "-cert", "certs/expired_client.pem",
        "-key",  "certs/expired_client.key",
        "-verify_return_error"
    ], capture_output=True, text=True, timeout=10)

    # Expect verification error
    assert "Verify return code: 0 (ok)" not in result.stdout, \
        "Expired cert was accepted — cert validation broken!"


def test_cipher_suite_restriction():
    """Only AEAD cipher suites should be accepted (no CBC)."""
    result = subprocess.run([
        "openssl", "s_client",
        "-connect", f"{OTA_SERVER_HOST}:{OTA_SERVER_PORT}",
        "-cipher", "AES128-SHA"   # CBC cipher — should be rejected
    ], capture_output=True, text=True, timeout=10)

    assert "handshake failure" in result.stderr.lower() or \
           "no cipher" in result.stderr.lower(), \
        "Server accepted insecure CBC cipher suite"
```

---

## 9. GNSS & eCall Testing

### 9.1 GNSS Test Cases

| TC-ID | Test Name | Method | Criteria |
|-------|-----------|--------|---------|
| TC-GPS-001 | Cold start TTFF | Clear almanac; power-on; measure fix time | TTFF ≤ 60 s (outdoor, open sky) |
| TC-GPS-002 | Hot start TTFF | Valid almanac cached; power-cycle | TTFF ≤ 5 s |
| TC-GPS-003 | Position accuracy | Spirent GNSS sim: place vehicle at known coordinates | CEP50 ≤ 3 m; CEP95 ≤ 10 m |
| TC-GPS-004 | Urban canyon simulation | Spirent: dense building multipath scenario | Position fix maintained; accuracy degrades gracefully (CEP95 ≤ 50 m) |
| TC-GPS-005 | GNSS jamming response | Inject jamming signal at −40 dBm | TCU detects jamming; sends alert to backend; switches to DR (dead reckoning) |
| TC-GPS-006 | GNSS spoofing detection | Inject spoofed GPS at wrong coordinates | TCU detects position jump > plausibility threshold; reports spoof suspicion |
| TC-GPS-007 | Galileo + GPS fusion | Spirent: GPS + Galileo constellation | Position fix uses both; check NMEA GNGGA (not GPGGA only) |

### 9.2 eCall Testing

```
eCall Test Requirements (EU Directive 2015/758/EC):

Mandatory Test Cases:
  1. Automatic eCall trigger
     - Stimulus: Simulate airbag deployment signal on CAN (DID 0x2010 = deployed)
     - Expected: eCall initiated within 10 s; MSD (Minimum Set of Data) transmitted
     - MSD contains: GPS position, VIN, time of incident, number of occupants

  2. Manual eCall trigger
     - Stimulus: Hold eCall button for 3 seconds (CAN signal simulation)
     - Expected: eCall initiated; voice session established with PSAP

  3. eCall GPS position accuracy
     - Expected: Transmitted latitude/longitude within 150 m of actual position

  4. Callback test
     - PSAP operator calls back within 10 minutes; TCU auto-answers

  5. Low signal (indoor parking) eCall
     - Set RF attenuation to −100 dBm (indoor loss)
     - Expected: TCU retries call every 30 s for 20 minutes (per EN 16072)

  6. Automatic vs. manual eCall flag
     - Check bit 7 (manual/auto) in MSD record correct for each trigger type

eCall AT Commands (GSMA TS.31 compatible):
  AT+CECALL=1          → Trigger test eCall
  AT+CECALL=0          → End eCall session
  AT+CCMSD?            → Read last transmitted MSD
  AT+CLVL=5            → Set eCall audio volume
```

---

## 10. Power Mode & Wake-Up Testing

### 10.1 Power State Test Cases

```
TCU Power States:
  ACTIVE  → Full operation: cellular, GNSS, CAN all running
  PARTIAL → CAN/LIN wake monitoring only; modem in low-power
  SLEEP   → Only wake source monitoring; modem off; < 5 mA total
  OFF     → Ignition off > 30 min; complete shutdown; < 1 mA quiescent
```

| TC-ID | Test Name | Stimulus | Expected |
|-------|-----------|---------|---------|
| TC-PWR-001 | Quiescent current (OFF state) | Ignition off 30+ min | Total current draw ≤ 1 mA (battery protection) |
| TC-PWR-002 | Wake by ignition | Assert IGN signal HIGH | TCU boots within 5 s; cellular registers within 15 s |
| TC-PWR-003 | Wake by CAN frame (remote wake) | Send NM wake frame on CAN | TCU wakes from SLEEP within 200 ms |
| TC-PWR-004 | Wake by SMS/push notification | OEM backend pushes wake SMS to eSIM | TCU wakes; opens MQTT session; processes remote command |
| TC-PWR-005 | OTA download in SLEEP (pre-download) | Push OTA notification when vehicle parked | TCU wakes briefly to download; returns to SLEEP after download if install not yet allowed |
| TC-PWR-006 | Battery disconnect recovery | Disconnect 12V for 10 s; reconnect | TCU recovers NVM; re-registers cellular; no NVM corruption DTC |

### 10.2 Wake-Up Timing Test (CAPL)

```capl
/*
 * TCU_WakeUp_Timing.can
 * Measures precise time from NM wake frame to TCU CAN activity
 * Validates TCU wake-up latency ≤ 200 ms
 */

variables {
    msTimer   wakeTimer;
    long      wakeStart_us;
    long      tcuFirstFrame_us;
    int       wakeDetected = 0;
    message 0x400 nmWakeFrame;   /* NM wake frame — configured per vehicle NM spec */
}

on start {
    write("TCU wake-up latency test initialised");
    write("Sending NM wake frame in 2 seconds...");
    setTimer(wakeTimer, 2000);
}

on timer wakeTimer {
    /* Send CAN NM partial network wake-up request */
    nmWakeFrame.id  = 0x400;
    nmWakeFrame.dlc = 8;
    nmWakeFrame.byte(0) = 0x01;   /* NM CBV: partial networking wake request */
    nmWakeFrame.byte(1) = 0x28;   /* NM CBV flags */

    wakeStart_us = timeNow();
    output(nmWakeFrame);
    wakeDetected = 0;
    write("NM wake frame sent at t=%.3f ms", wakeStart_us / 1000.0);
}

/* Monitor for any CAN frame from TCU (0x700–0x7FF = TCU ID range) */
on message 0x700-0x7FF {
    if (!wakeDetected) {
        tcuFirstFrame_us = timeNow();
        long latency_ms = (tcuFirstFrame_us - wakeStart_us) / 1000;

        wakeDetected = 1;
        write("TCU first CAN frame at t=%.3f ms", tcuFirstFrame_us / 1000.0);
        write("Wake-up latency: %d ms", latency_ms);

        if (latency_ms <= 200) {
            write("RESULT: PASS — latency %d ms ≤ 200 ms", latency_ms);
            testPassed("TCU_WakeUp_Latency");
        } else {
            write("RESULT: FAIL — latency %d ms > 200 ms", latency_ms);
            testFailed("TCU_WakeUp_Latency");
        }
    }
}

/* Timeout: TCU did not wake within 500 ms */
on timer wakeWatchdog {
    if (!wakeDetected) {
        write("RESULT: FAIL — TCU did not wake within 500 ms");
        testFailed("TCU_WakeUp_NoResponse");
    }
}
```

---

## 11. CAPL Scripts for Telematics Testing

### 11.1 OTA State Machine Monitor

```capl
/*
 * OTA_StateMachine_Monitor.can
 * Monitors TCU diagnostic PIDs to track OTA state machine progression
 * Validates state transitions and timing requirements per TC-OTA-001
 */

variables {
    msTimer stateTimer;
    int     currentState = 0;
    long    stateEntryTime_ms;

    /* OTA state codes (from TCU diagnostic DID 0xFD00) */
    const int OTA_STATE_IDLE          = 0x00;
    const int OTA_STATE_DOWNLOADING   = 0x01;
    const int OTA_STATE_VALIDATING    = 0x02;
    const int OTA_STATE_READY         = 0x03;
    const int OTA_STATE_INSTALLING    = 0x04;
    const int OTA_STATE_VERIFYING     = 0x05;
    const int OTA_STATE_COMPLETE      = 0x06;
    const int OTA_STATE_ROLLBACK      = 0xFF;

    /* Maximum allowed time in each state (ms) */
    const long MAX_DOWNLOAD_MS   = 1800000;  /* 30 minutes */
    const long MAX_VALIDATE_MS   =   60000;  /* 60 seconds */
    const long MAX_INSTALL_MS    =  300000;  /* 5 minutes */
    const long MAX_VERIFY_MS     =   30000;  /* 30 seconds */
}

on start {
    setTimer(stateTimer, 1000);   /* Poll every 1 second */
    write("OTA state machine monitoring started");
}

on timer stateTimer {
    /* Read OTA status DID via UDS 0x22 0xFD00 */
    diagRequest TCU.ReadDataByIdentifier_OTA_Status req;
    req.SendRequest();
    setTimer(stateTimer, 1000);
}

on diagResponse TCU.ReadDataByIdentifier_OTA_Status {
    int newState = this.OTA_StateCode;
    long now_ms  = timeNow() / 1000;

    if (newState != currentState) {
        long timeInPrev = now_ms - stateEntryTime_ms;
        write("OTA state change: %02X → %02X after %d ms",
              currentState, newState, timeInPrev);

        /* Validate time spent in previous state */
        checkStateTimeout(currentState, timeInPrev);

        currentState    = newState;
        stateEntryTime_ms = now_ms;

        /* Signal test result on final states */
        if (newState == OTA_STATE_COMPLETE) {
            write("OTA UPDATE COMPLETE — verifying version");
            verifyFinalVersion();
        } else if (newState == OTA_STATE_ROLLBACK) {
            write("OTA ROLLBACK DETECTED — checking rollback integrity");
            testFailed("OTA_UnexpectedRollback");
        }
    }
}

void checkStateTimeout(int state, long duration_ms) {
    if (state == OTA_STATE_DOWNLOADING && duration_ms > MAX_DOWNLOAD_MS) {
        write("WARN: Download took %d ms — exceeded %d ms limit", duration_ms, MAX_DOWNLOAD_MS);
    } else if (state == OTA_STATE_VALIDATING && duration_ms > MAX_VALIDATE_MS) {
        write("FAIL: Validation timeout — %d ms > %d ms", duration_ms, MAX_VALIDATE_MS);
        testFailed("OTA_ValidationTimeout");
    } else if (state == OTA_STATE_INSTALLING && duration_ms > MAX_INSTALL_MS) {
        write("FAIL: Install timeout — %d ms > %d ms", duration_ms, MAX_INSTALL_MS);
        testFailed("OTA_InstallTimeout");
    }
}

void verifyFinalVersion() {
    diagRequest TCU.ReadDataByIdentifier_SWVersion req;
    req.SendRequest();
}

on diagResponse TCU.ReadDataByIdentifier_SWVersion {
    char version[16];
    this.SoftwareVersion.GetString(version, 16);
    write("Post-OTA software version: %s", version);

    if (strncmp(version, "2.5.3", 5) == 0) {
        write("PASS: Expected version 2.5.3 confirmed");
        testPassed("OTA_VersionConfirmed");
    } else {
        write("FAIL: Expected 2.5.3, got %s", version);
        testFailed("OTA_VersionMismatch");
    }
}
```

### 11.2 TCU CAN Gateway Routing Validator

```capl
/*
 * TCU_Gateway_Routing.can
 * Sends diagnostic requests to multiple ECUs via TCU gateway
 * Validates correct routing and response mapping
 */

variables {
    /* ECU logical addresses mapped to CAN IDs (from network topology doc) */
    const int ECU_ENGINE   = 0x0720;    /* CAN Tx ID 0x7E0 */
    const int ECU_RADAR    = 0x0750;    /* CAN Tx ID 0x7E3 */
    const int ECU_GATEWAY  = 0x0E00;    /* TCU gateway logical address */

    int routingTestsPassed = 0;
    int routingTestsTotal  = 0;
}

/* Test: read ECU software version from Engine ECU via gateway */
testcase TCU_Routes_To_EngineECU() {
    diagRequest Engine.ReadDataByIdentifier_SWVersion req;

    routingTestsTotal++;
    req.SendRequest();

    if (testWaitForDiagResponse(req, 5000) == 1) {
        char sw[16];
        req.response.SoftwareVersion.GetString(sw, 16);
        write("Engine ECU SW: %s — routed via TCU gateway", sw);
        routingTestsPassed++;
        testPassed("Gateway_Route_Engine_OK");
    } else {
        write("FAIL: No response from Engine ECU via gateway");
        testFailed("Gateway_Route_Engine_TIMEOUT");
    }
}

/* Test: Radar ECU accessible via gateway */
testcase TCU_Routes_To_RadarECU() {
    diagRequest Radar.ReadDataByIdentifier_SWVersion req;

    routingTestsTotal++;
    req.SendRequest();

    if (testWaitForDiagResponse(req, 5000) == 1) {
        write("Radar ECU reachable via TCU gateway");
        routingTestsPassed++;
        testPassed("Gateway_Route_Radar_OK");
    } else {
        testFailed("Gateway_Route_Radar_TIMEOUT");
    }
}

on start {
    write("TCU Gateway routing validation — %d ECUs in scope", 2);
    TCU_Routes_To_EngineECU();
    TCU_Routes_To_RadarECU();
    write("Gateway routing: %d/%d PASS", routingTestsPassed, routingTestsTotal);
}
```

---

## 12. Python Test Automation Scripts

### 12.1 OTA Campaign Trigger & Monitor

```python
"""
ota_campaign_runner.py
Automates OTA campaign creation, monitoring, and result validation.
"""

import requests
import paho.mqtt.client as mqtt
import time
import pytest
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("OTA_Test")

# Test configuration
OTA_BACKEND_URL  = "https://ota-test-server.local:8443"
MQTT_BROKER      = "mqtt-test.local"
MQTT_PORT        = 8883
TEST_VIN         = "WDB1234567890TEST"
PKG_ID           = "PKG_TEST_N1_001"
EXPECTED_VERSION = "2.5.3"
EXPECTED_RXSWIN  = "RXSWIN_EU_2025_0042"
API_TOKEN        = "Bearer test_api_token_123"


class OTACampaignTest:

    def __init__(self):
        self.ota_result    = None
        self.state_history = []
        self.mq            = mqtt.Client(client_id="ota_test_runner")
        self.mq.tls_set("certs/ca.pem", "certs/client.pem", "certs/client.key")
        self.mq.on_message = self._on_mqtt_message
        self.mq.connect(MQTT_BROKER, MQTT_PORT)
        self.mq.loop_start()
        self.mq.subscribe(f"vehicles/{TEST_VIN}/ota/#")

    def _on_mqtt_message(self, client, userdata, msg):
        topic   = msg.topic
        payload = json.loads(msg.payload)
        log.info(f"MQTT [{topic}]: {payload}")

        if "status" in topic:
            state = payload.get("state", "")
            self.state_history.append({
                "state": state,
                "timestamp": time.time()
            })
            if state in ("COMPLETE", "FAILED", "ROLLBACK"):
                self.ota_result = state

    def trigger_campaign(self) -> str:
        """Create and start OTA campaign; return campaign ID."""
        resp = requests.post(
            f"{OTA_BACKEND_URL}/api/v2/campaigns",
            headers={"Authorization": API_TOKEN},
            json={
                "name":       "TestCampaign_N_to_N1",
                "package_id": PKG_ID,
                "targets":    [{"vin": TEST_VIN}],
                "rollout":    {"strategy": "immediate"}
            },
            verify="certs/ca.pem",
            timeout=10
        )
        resp.raise_for_status()
        campaign_id = resp.json()["campaign_id"]
        log.info(f"Campaign created: {campaign_id}")
        return campaign_id

    def wait_for_result(self, timeout_s: int = 1800) -> str:
        """Block until OTA result received or timeout."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self.ota_result:
                return self.ota_result
            time.sleep(5)
        raise TimeoutError(f"OTA did not complete within {timeout_s} s")

    def verify_post_ota(self) -> dict:
        """Query OTA backend for post-update status."""
        resp = requests.get(
            f"{OTA_BACKEND_URL}/api/v2/vehicles/{TEST_VIN}/software",
            headers={"Authorization": API_TOKEN},
            verify="certs/ca.pem", timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def cleanup(self):
        self.mq.loop_stop()
        self.mq.disconnect()


@pytest.fixture
def ota():
    runner = OTACampaignTest()
    yield runner
    runner.cleanup()


def test_happy_path_ota(ota):
    """TC-OTA-001: Full OTA happy path."""
    campaign_id = ota.trigger_campaign()
    log.info(f"Waiting for OTA completion (max 30 min)...")

    result = ota.wait_for_result(timeout_s=1800)
    assert result == "COMPLETE", f"OTA result was '{result}', expected COMPLETE"

    # Verify state machine traversed all expected states in correct order
    expected_states = ["DOWNLOADING", "VALIDATING", "READY_TO_INSTALL",
                       "INSTALLING", "VERIFYING", "COMPLETE"]
    actual_states = [s["state"] for s in ota.state_history]

    for expected in expected_states:
        assert expected in actual_states, \
            f"Expected state '{expected}' not observed. Actual: {actual_states}"

    # Verify version on backend
    post_ota = ota.verify_post_ota()
    assert post_ota["software_version"] == EXPECTED_VERSION, \
        f"Version mismatch: {post_ota['software_version']} != {EXPECTED_VERSION}"
    assert post_ota["rxswin"] == EXPECTED_RXSWIN, \
        f"RXSWIN mismatch: {post_ota['rxswin']} != {EXPECTED_RXSWIN}"

    log.info("TC-OTA-001 PASSED")


def test_rollback_on_power_cut(ota):
    """TC-OTA-F020: Power cut mid-flash triggers rollback."""
    import subprocess

    campaign_id = ota.trigger_campaign()

    # Wait until INSTALLING state observed
    deadline = time.time() + 600
    while time.time() < deadline:
        if any(s["state"] == "INSTALLING" for s in ota.state_history):
            break
        time.sleep(1)
    else:
        pytest.fail("INSTALLING state not observed within 600 s")

    # Trigger power cut via GPIO relay control script
    log.info("Cutting power mid-flash...")
    subprocess.run(["python3", "relay_control.py", "--cut", "--duration_s", "5"],
                   check=True)

    # Wait for result after power restore
    result = ota.wait_for_result(timeout_s=300)
    assert result == "ROLLBACK", f"Expected ROLLBACK after power cut, got '{result}'"

    # Verify previous version still active
    post_ota = ota.verify_post_ota()
    assert post_ota["software_version"] != EXPECTED_VERSION, \
        "Version should be old version after rollback — not N+1!"
    log.info(f"TC-OTA-F020 PASSED — version after rollback: {post_ota['software_version']}")
```

---

## 13. KPIs, Acceptance Criteria & Metrics

### 13.1 TCU Performance KPIs

| KPI | Target | Measurement Method |
|-----|--------|--------------------|
| Boot-to-MQTT time | ≤ 15 s | Timestamp: 12V applied → first MQTT PUBLISH |
| LTE cold registration | ≤ 10 s | AT+CREG poll from AT command logger |
| LTE reconnection after drop | ≤ 5 s | RF attenuator cut → restore; measure reconnect |
| GNSS cold start TTFF | ≤ 60 s | Spirent GNSS sim; measure first fix flag |
| DoIP response latency | ≤ 500 ms | Wireshark: UDS request → response timestamp |
| CAN gateway routing latency | ≤ 100 ms | CANoe timestamp: TX from test PC → response |
| Quiescent current (off state) | ≤ 1 mA | Bench ammeter; 30 min after ign off |
| MQTT heartbeat interval | 60 s ± 5 s | MQTT subscription; timestamp consecutive heartbeats |

### 13.2 OTA Quality Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| OTA success rate (fleet) | ≥ 99.5% | Monitored across all VINs in campaign |
| Rollback success rate | 100% | Zero tolerance for bricked ECUs |
| Average download time (12 MB) | ≤ 20 min (4G) | At RSRP = −95 dBm |
| Package validation time | ≤ 60 s | SHA-256 + RSA on 12 MB package |
| Flash write time | ≤ 5 min | For 512 KB ECU firmware |
| RXSWIN update propagation | ≤ 10 min after completion | Backend DB + ECU NVM both updated |
| Error rate abort threshold | > 2% → halt campaign | Automatic campaign abort policy |

### 13.3 Test Coverage Checklist (UN ECE R156 Compliance)

```
Required Evidence for R156 Type Approval:
  ✓ Software Update Management System (SUMS) documentation
  ✓ Test evidence: cryptographic verification of package authenticity
  ✓ Test evidence: compatibility check (VIN/HW revision matching)
  ✓ Test evidence: rollback functionality (power interruption tests)
  ✓ Test evidence: RXSWIN lifecycle (baseline → update → verification)
  ✓ Test evidence: driver notification and consent mechanism
  ✓ Test evidence: no safety-critical update applied while driving
  ✓ Test evidence: update history accessible via OBD-II (SID 0x22 0xF1A2)
  ✓ Process evidence: SUMS audit trail for each campaign (who, when, which VINs)
```

---

## 14. Common Defects & RCA Patterns

### 14.1 Top Telematics ECU Defects

| Defect | Symptom | Root Cause | Fix |
|--------|---------|-----------|-----|
| LTE re-registration failure | TCU goes offline permanently after signal drop | Missing CEREG unsolicited result code handler; modem not polled for re-attach | Add AT+CEREG=2 URC; watchdog to force modem reset if offline > 5 min |
| GNSS fix lost after tunnel | Position freeze for 3 min after tunnel exit | Cold-start algorithm triggered by excessive signal gap; A-GPS aiding not refreshed | Reduce max-gap timer; configure Dead Reckoning as fallback |
| MQTT reconnect loop | High backend log volume; TCU reconnects every 30 s | Client-ID conflict: two ECUs with same MQTT client ID | Generate unique client ID from VIN + ECU serial; enforce uniqueness at backend |
| OTA download stalls at 99% | Campaign never completes for some vehicles | HTTP range-request off-by-one bug in OTA client; last chunk not fetched | Fix chunk calculation: `remaining = total_size - bytes_received` |
| Power-cut brick after flash | ECU boots to blank flash; no rollback | A/B partition flag write done AFTER flash (not before); power cut corrupts flag | Write partition B flag BEFORE starting flash; rollback checks flag first |
| Seed-key lockout in field | Garage cannot access ECU; locked out permanently | NVM lockout counter survives ignition cycle; no reset mechanism | Add lockout reset via authenticated FOTA or OEM backend command |
| SecOC freshness sync lost | SecOC drops all frames after ECU reset | Trip counter not persisted to NVM before shutdown | Write FV NVM in shutdown hook; verify NVM write complete before power-down |
| eCall MSD wrong position | Emergency services get wrong GPS coordinates | GNSS fix used from cache (15 min stale); not refreshed on eCall trigger | Force GNSS fix refresh on eCall trigger; use position timestamp to reject stale |

### 14.2 OTA Defect RCA Checklist

```
When OTA fails — systematic investigation:

1. CHECK STATE AT FAILURE
   → Which state did the OTA state machine reach before failure?
   → DOWNLOADING, VALIDATING, INSTALLING, or VERIFYING?

2. NETWORK ISSUES (if failed during DOWNLOADING)
   → Check RSRP at time of failure (TCU logs)
   → Check server HTTP response codes (416 Range Not Satisfiable?)
   → Check TCP keepalive; was session dropped?
   → Check OTA server availability log

3. VALIDATION FAILURE
   → Log shows "signature FAIL" or "hash FAIL"?
   → If hash: package corrupted during transit or on server?
   → If signature: key mismatch — dev key on production binary?
   → If version check: anti-rollback triggered? Backend sent wrong package?

4. INSTALLATION FAILURE
   → Was vehicle state correct? (IGN off, SOC > 30%?)
   → UDS error code returned during 0x34/0x36 transfer?
   → Flash write error? NVM fault? Bad flash sector?
   → Was flash partition B erased before write?

5. POST-FLASH VERIFICATION FAILURE
   → CRC over new partition fails? Indicates write error
   → Signature of new partition fails? Indicates partially incomplete write
   → Action: rollback to partition A; report VERIFY_FAIL to backend

6. NO ROLLBACK AFTER FAILURE (critical defect!)
   → Partition flag corrupted? Check NVM integrity
   → Bootloader has correct rollback decision logic?
   → Trace boot log byte by byte if needed
```

---

*See also*:
- [02_ota_updates.md](02_ota_updates.md) — OTA architecture scenarios
- [07_tcu_architecture.md](07_tcu_architecture.md) — TCU hardware/software architecture
- [04_remote_diagnostics.md](04_remote_diagnostics.md) — Remote diagnostic protocol chains
- [cybersecurity_automotive/02_AUTOSAR_Cybersecurity_Full_Stack.md](../cybersecurity_automotive/02_AUTOSAR_Cybersecurity_Full_Stack.md) — SecOC, OTA security, TLS
