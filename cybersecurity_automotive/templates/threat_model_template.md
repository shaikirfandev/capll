# Threat Model Template — STRIDE + DREAD

> Document No: [PROJ-TM-001]  |  Version: [1.0]  |  Date: [YYYY-MM-DD]
> System: [e.g., Gateway ECU / OTA System / EV Charging Interface]

---

## 1. System Description

**System Name**: [e.g., Telematics Control Unit (TCU)]

**Purpose**: [One paragraph describing what the system does and why it's security-relevant]

**Technology Stack**:
- Hardware: [e.g., NXP S32K344 MCU + SIMCOM SIM7600 modem]
- OS/Platform: [e.g., AUTOSAR Classic + FreeRTOS]
- Communication: [e.g., CAN FD, LTE-M, MQTT over TLS 1.3]

---

## 2. Data Flow Diagram (DFD)

```
[Draw your DFD here using ASCII art or attach as image]

Example for TCU:

  ┌──────────────┐  MQTT/TLS   ┌──────────────────┐
  │  OEM Backend  │◄──────────►│   TCU             │
  │  (Cloud)      │            │                   │
  └──────────────┘            │  ┌──────────────┐ │
                               │  │  CAN Handler │ │
  ┌──────────────┐  CAN FD     │  └──────┬───────┘ │
  │  Gateway ECU  │◄──────────►│         │         │
  └──────────────┘            │  ┌──────▼───────┐ │
                               │  │  Flash/NvM   │ │
  ┌──────────────┐  AT cmds    └──└──────────────┘─┘
  │  Cellular NW  │◄────────────────────┘
  └──────────────┘

Trust Boundaries:
  ──────── Trusted (authenticated TLS)
  - - - -  Untrusted (CAN without SecOC)
```

---

## 3. Trust Boundaries

| Boundary ID | Boundary Description | Crossing Elements | Trust Level |
|-------------|---------------------|-------------------|-------------|
| TB-01 | External Internet → TCU | MQTT messages, OTA packages | **Untrusted** |
| TB-02 | TCU → Chassis CAN | CAN messages | **Semi-trusted** (add SecOC) |
| TB-03 | TCU internal memory | Flash reads/writes | **Trusted** |
| TB-04 | OBD-II port → ECUs | UDS messages | **Untrusted** |

---

## 4. STRIDE Threat Analysis

> For each system component and trust boundary crossing, analyze all 6 STRIDE categories.

### 4.1 Component: [e.g., MQTT Client (TCU ↔ Backend)]

| STRIDE Category | Threat Description | Example Attack | Relevant? |
|----------------|-------------------|----------------|-----------|
| **Spoofing** | Attacker impersonates legitimate OEM backend | Rogue MQTT broker with valid-looking domain | YES |
| **Tampering** | MITM modifies OTA commands in transit | Remove package signature check | YES |
| **Repudiation** | ECU denies receiving/executing OTA command | No audit log of OTA actions | YES |
| **Information Disclosure** | TLS misconfiguration exposes VIN/location | SSL stripping, weak cipher suite | YES |
| **Denial of Service** | Flood MQTT broker with messages | Cloud DDoS → no OTA possible | YES |
| **Elevation of Privilege** | Attacker sends "programming session" command without auth | Missing backend auth check | YES |

### 4.2 Component: [e.g., CAN Bus Interface]

| STRIDE Category | Threat Description | Example Attack | Relevant? |
|----------------|-------------------|----------------|-----------|
| **Spoofing** | Inject message with same ID as safety ECU | CAN injection via OBD-II | YES |
| **Tampering** | Modify signal values in existing message | Replay with modified data | YES |
| **Repudiation** | No record of who sent malicious CAN frame | Standard CAN has no source ID | YES |
| **Information Disclosure** | Sniff confidential diagnostic data | CAN sniffing (passive) | MEDIUM |
| **Denial of Service** | CAN flood → bus saturation → ECU overload | Flood with 0x000 ID (high priority) | YES |
| **Elevation of Privilege** | Use CAN to enter diagnostic session without UDS auth | Gateway bypass | YES |

### 4.3 Component: [e.g., UDS Diagnostic Interface]

| STRIDE Category | Threat Description | Example Attack | Relevant? |
|----------------|-------------------|----------------|-----------|
| **Spoofing** | — | N/A (point-to-point) | NO |
| **Tampering** | Modify DID write to change calibration data | WDBI with unauthorized DID | YES |
| **Repudiation** | No logging of diagnostic actions | No DTC shows what was changed | YES |
| **Information Disclosure** | Read secret DIDs (key material, certificates) | RDBI with internal DIDs | YES |
| **Denial of Service** | Repeatedly force ECU into diagnostic mode | TesterPresent flood | MEDIUM |
| **Elevation of Privilege** | Bypass Security Access to reach programming session | Brute force seed-key | YES |

---

## 5. DREAD Risk Scoring

> Score each threat 1–3 in 5 categories. Risk = (D+R+E+A+D) / 5

| ID | Threat (Short) | Damage (1-3) | Reproducibility (1-3) | Exploitability (1-3) | Affected Users (1-3) | Discoverability (1-3) | **DREAD Score** | **Priority** |
|----|---------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| TM-001 | Rogue MQTT broker MITM | 3 | 2 | 2 | 3 | 2 | **2.4** | HIGH |
| TM-002 | CAN injection via OBD | 3 | 3 | 3 | 3 | 3 | **3.0** | CRITICAL |
| TM-003 | UDS seed-key brute force | 3 | 2 | 2 | 2 | 2 | **2.2** | HIGH |
| TM-004 | TLS configuration exposing data | 2 | 1 | 2 | 2 | 2 | **1.8** | MEDIUM |
| TM-005 | [Add more] | | | | | | | |

**DREAD Scoring Guide**:

| Category | 1 (Low) | 2 (Medium) | 3 (High) |
|----------|---------|------------|---------|
| **Damage** | Minimal impact | Leaks data / minor disruption | Safety impact / full compromise |
| **Reproducibility** | Requires specific conditions | Works most of the time | Always reproducible |
| **Exploitability** | Requires expert + weeks | Some skill, hours | Script kiddie, minutes |
| **Affected Users** | 1 vehicle | Specific model | All vehicles |
| **Discoverability** | Hard to find | Known attack class | Obvious / CVE public |

---

## 6. Mitigations

| Threat ID | Threat | Mitigation | Implementation | Owner | Status |
|-----------|--------|------------|---------------|-------|--------|
| TM-001 | Rogue MQTT broker MITM | Certificate pinning + TLS 1.3 client auth | OTA client config | SW Team | [ ] Open |
| TM-002 | CAN injection via OBD | SecOC on safety messages + gateway whitelist | AUTOSAR SecOC config | ECU Team | [ ] Open |
| TM-003 | UDS seed-key brute force | DCM lockout: 3 attempts + 10s + HMAC seed-key | DCM config | SW Team | [ ] Open |
| TM-004 | TLS configuration exposure | Enforce TLS 1.3 only, disable weak ciphers | Crypto stack config | SW Team | [ ] Open |

---

## 7. Residual Risk Summary

| Threat ID | Original DREAD | Mitigation Applied | Residual DREAD | Accepted? |
|-----------|---------------|-------------------|----------------|-----------|
| TM-001 | 2.4 | Certificate pinning + mTLS | 1.2 | YES |
| TM-002 | 3.0 | SecOC + gateway filter | 1.4 | YES |
| TM-003 | 2.2 | DCM lockout + HMAC | 1.0 | YES |
| TM-004 | 1.8 | TLS 1.3 enforced | 0.8 | YES |

---

## 8. Threat Model Review Triggers

This threat model must be re-evaluated when:
- [ ] A new external interface is added
- [ ] Communication protocol is changed
- [ ] New supplier component is integrated
- [ ] A CVE is published for a used component
- [ ] A cybersecurity incident occurs related to this system
- [ ] Annual scheduled review

---

## Appendix: Attack Tree — [Key Threat]

```
Example: Attack Tree for "Unauthorized ECU Flash"

  Goal: Flash malicious firmware to ECU
  ├── Via Physical Access (OBD-II)
  │   ├── Bypass Security Access
  │   │   ├── Brute force seed-key [FEASIBLE if no lockout]
  │   │   └── Reverse-engineer seed-key algorithm from firmware [HIGH EFFORT]
  │   └── Exploit ECU during bootloader (glitch attack) [VERY HIGH EFFORT]
  └── Via Remote Access
      ├── Compromise OTA backend → deliver malicious package
      │   ├── Backend credential theft [MEDIUM EFFORT]
      │   └── HSM signing key compromise [VERY HIGH EFFORT]
      └── MITM OTA channel → inject package [MITIGATED by TLS + sig check]
```
