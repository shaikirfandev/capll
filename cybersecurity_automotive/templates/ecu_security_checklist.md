# ECU Security Hardening Checklist

> Document No: [PROJ-ECU-SEC-001]  |  Version: [1.0]  |  Date: [YYYY-MM-DD]
> ECU Name: [e.g., AEB ECU / TCU / Gateway]  |  HW Rev: [X.Y]  |  SW Ver: [X.Y.Z]

---

## Section 1: Secure Boot

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| SB-01 | Boot ROM verifies Stage 1 Bootloader signature (ECDSA P-256 minimum) | □ | □ | □ | |
| SB-02 | Stage 1 Bootloader verifies Stage 2 Bootloader signature | □ | □ | □ | |
| SB-03 | Final bootloader verifies application firmware signature before execution | □ | □ | □ | |
| SB-04 | Anti-rollback counter stored in OTP/monotonic counter (not in NvM only) | □ | □ | □ | |
| SB-05 | Firmware with version < anti-rollback counter is rejected | □ | □ | □ | Test: try flashing v1 after v2 installed |
| SB-06 | Secure Boot failure: ECU enters safe state (does not execute unsigned code) | □ | □ | □ | |
| SB-07 | Secure Boot failure logged as DTC | □ | □ | □ | |
| SB-08 | Hash algorithm: SHA-256 minimum (SHA-384 for CAL 4) | □ | □ | □ | |
| SB-09 | Root public key hash burned to OTP at End-of-Line | □ | □ | □ | |
| SB-10 | No bypass mechanism exists (no "skip verification" bootloader command) | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 2: Hardware Security Module (HSM)

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| HSM-01 | ECU uses hardware HSM (not software-only crypto) for key operations | □ | □ | □ | |
| HSM-02 | Key provisioning performed at EoL programming station (not in source code) | □ | □ | □ | |
| HSM-03 | No raw key material accessible via debug interface (JTAG/SWD) | □ | □ | □ | |
| HSM-04 | AES keys never exported from HSM in plaintext | □ | □ | □ | |
| HSM-05 | TRNG used for seed generation (not software PRNG) | □ | □ | □ | |
| HSM-06 | HSM initialized status checked at startup (alert if not initialized) | □ | □ | □ | |
| HSM-07 | Key attestation supported (HSM can prove key was generated internally) | □ | □ | □ | N/A if not required by design |
| HSM-08 | HSM firmware version documented and CVE monitoring in place | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 3: Debug Interface Security (JTAG/SWD)

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| DBG-01 | JTAG/SWD fused (OTP) in production units | □ | □ | □ | OTP fusing script documented |
| DBG-02 | Debug access requires challenge-response authentication (if JTAG not fused) | □ | □ | □ | |
| DBG-03 | UART console disabled or requires authentication in production build | □ | □ | □ | |
| DBG-04 | Debug macros/preprocessor defines disabled in production build | □ | □ | □ | Build flag: NDEBUG or equivalent |
| DBG-05 | Memory dump via debug interface blocked for key material regions | □ | □ | □ | |
| DBG-06 | Production build differs from development build (separate build target) | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 4: UDS Diagnostic Security (DCM)

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| UDS-01 | Programming Session requires prior Extended Diagnostic Session | □ | □ | □ | |
| UDS-02 | Programming Session requires Security Access level 2 (0x27 0x01/0x02) | □ | □ | □ | |
| UDS-03 | Security Access lockout: maximum 3 failed attempts | □ | □ | □ | Test: 4 wrong keys → NRC 0x36 |
| UDS-04 | Security Access lockout duration: ≥ 10 seconds (or OEM requirement) | □ | □ | □ | Test: measure lockout time |
| UDS-05 | Security Access lockout persists across ECU soft reset | □ | □ | □ | Test: lockout → reset → verify still locked |
| UDS-06 | Security Access seed: hardware TRNG, ≥ 4 bytes, non-predictable | □ | □ | □ | Test: collect 100 seeds, verify entropy |
| UDS-07 | Security Access key algorithm: HMAC or equivalent (not XOR/rotate) | □ | □ | □ | Source code review |
| UDS-08 | WDBI for calibration DIDs requires Security Access level 1+ | □ | □ | □ | |
| UDS-09 | IO Control (0x2F) for safety-relevant signals requires Security Access | □ | □ | □ | |
| UDS-10 | DTC clear (0x14) requires Extended session at minimum | □ | □ | □ | |
| UDS-11 | Default session only exposes non-sensitive RDBI (VIN, ECU info) | □ | □ | □ | Verify DID permission matrix |
| UDS-12 | Firmware download accepted only with valid OEM signature | □ | □ | □ | Test: unsigned file rejected |
| UDS-13 | Diagnostic session log available (UDS service, NRC, timestamp) | □ | □ | □ | |
| UDS-14 | NRC 0x31 (requestOutOfRange) returned for unknown/unsupported DIDs | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 5: SecOC (Secure Onboard Communication)

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| SOC-01 | SecOC deployed on all safety-critical CAN messages (CAL 3/4) | □ | □ | □ | List: [AEB 0x244, EPS 0x300, ...] |
| SOC-02 | MAC algorithm: CMAC-AES-128 minimum | □ | □ | □ | |
| SOC-03 | Freshness value: ≥ 24 bits, monotonically increasing | □ | □ | □ | |
| SOC-04 | Freshness counter stored in NvM (persists across ECU reset) | □ | □ | □ | |
| SOC-05 | Replay attack detected (replayed frame rejected): Test pass | □ | □ | □ | |
| SOC-06 | Tampered MAC detected (modified payload rejected): Test pass | □ | □ | □ | |
| SOC-07 | SecOC failure causes safe state (not silent acceptance of unprotected msg) | □ | □ | □ | |
| SOC-08 | SecOC keys provisioned via HSM (not hardcoded in source) | □ | □ | □ | |
| SOC-09 | Counter rollover handling: resync procedure defined and tested | □ | □ | □ | |
| SOC-10 | E2E protection also deployed (separate from SecOC) on safety signals | □ | □ | □ | E2E = random error; SecOC = malicious |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 6: Memory Protection

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| MEM-01 | MPU enabled and configured (not bypassed in production) | □ | □ | □ | |
| MEM-02 | Code region: Execute + Read only (no Write) | □ | □ | □ | MPU config review |
| MEM-03 | Data region: Read + Write only (no Execute — NX bit) | □ | □ | □ | |
| MEM-04 | AUTOSAR OS partitions cannot access each other's memory | □ | □ | □ | |
| MEM-05 | Stack overflow detection: stack canaries or MPU guard regions | □ | □ | □ | |
| MEM-06 | No dangerous functions: strcpy, gets, sprintf without bounds check | □ | □ | □ | Static analysis report |
| MEM-07 | All external input lengths validated before buffer operations | □ | □ | □ | Code review |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 7: Cryptographic Strength

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| CRY-01 | No hardcoded keys or passwords in source code or binary | □ | □ | □ | Static analysis + binwalk strings |
| CRY-02 | Symmetric: AES-128 minimum (AES-256 for high-sensitivity) | □ | □ | □ | |
| CRY-03 | Asymmetric: ECDSA P-256 minimum (P-384 for CAL 4) | □ | □ | □ | |
| CRY-04 | Hash: SHA-256 minimum | □ | □ | □ | |
| CRY-05 | No deprecated algorithms: MD5, SHA-1, DES, 3DES, RC4 | □ | □ | □ | |
| CRY-06 | MAC: CMAC or HMAC (not homemade hash-based) | □ | □ | □ | |
| CRY-07 | Constant-time comparison used for secret comparison (no early exit) | □ | □ | □ | |
| CRY-08 | Nonces/IVs: unique per session, from TRNG | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 8: OTA Update Security

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| OTA-01 | OTA package signed with OEM root CA (ECDSA P-256+) | □ | □ | □ | |
| OTA-02 | Signature verified before any flash write operation | □ | □ | □ | Test: unsigned package rejected |
| OTA-03 | Anti-rollback: older version rejected | □ | □ | □ | Test: install v2, try v1 |
| OTA-04 | Transport: TLS 1.3 with certificate validation | □ | □ | □ | |
| OTA-05 | Certificate pinning implemented (reject non-pinned backend cert) | □ | □ | □ | |
| OTA-06 | Pre-conditions checked: vehicle speed = 0, ignition off | □ | □ | □ | R156 requirement |
| OTA-07 | Atomic update: fallback to old firmware on verification failure | □ | □ | □ | Test: power cut during flash |
| OTA-08 | OTA manifest includes: version, hash, ECU ID, timestamp | □ | □ | □ | |
| OTA-09 | OTA events logged with timestamp and result | □ | □ | □ | R156 requirement |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Section 9: Network Isolation (Gateway)

| ID | Requirement | Pass | Fail | N/A | Evidence |
|----|-------------|:----:|:----:|:---:|----------|
| NET-01 | IVI bus cannot directly inject messages to Chassis CAN bus | □ | □ | □ | Injection test |
| NET-02 | Gateway firewall rules: whitelist per CAN bus (ID + DLC) | □ | □ | □ | |
| NET-03 | OBD-II port CAN traffic does not route directly to Chassis ECUs | □ | □ | □ | |
| NET-04 | SOME/IP services: TLS/DTLS or VLAN isolation | □ | □ | □ | |
| NET-05 | Cellular interface firewalled (no inbound to vehicle internal network) | □ | □ | □ | |
| NET-06 | CAN flood protection: rate limiting per message ID | □ | □ | □ | |

**Section Pass/Fail**: PASS / FAIL / PARTIAL

---

## Summary Dashboard

| Section | Items | Pass | Fail | N/A | Result |
|---------|-------|:----:|:----:|:---:|--------|
| 1. Secure Boot | 10 | | | | |
| 2. HSM | 8 | | | | |
| 3. Debug Interfaces | 6 | | | | |
| 4. UDS Diagnostics | 14 | | | | |
| 5. SecOC | 10 | | | | |
| 6. Memory Protection | 7 | | | | |
| 7. Cryptographic Strength | 8 | | | | |
| 8. OTA Update | 9 | | | | |
| 9. Network Isolation | 6 | | | | |
| **TOTAL** | **78** | | | | |

**Release Recommendation**:
- All CRITICAL items (SB-01–SB-10, UDS-12, OTA-02): PASS required
- All HIGH items: PASS or documented risk acceptance
- MEDIUM items: PASS or ALARP justification

---

## Open Items / Findings

| ID | Section | Requirement | Severity | Owner | Target Date | Status |
|----|---------|-------------|----------|-------|-------------|--------|
| | | | | | | |

**Sign-off**:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| ECU Security Engineer | | | |
| Software Architect | | | |
| Safety Manager | | | |
| Quality Manager | | | |
