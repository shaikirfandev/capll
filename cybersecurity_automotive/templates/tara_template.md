# TARA Worksheet Template — ISO/SAE 21434 §15

> Document No: [PROJ-TARA-001]  |  Version: [1.0]  |  Date: [YYYY-MM-DD]
> Author: [Name]  |  Reviewer: [Name]  |  Approved by: [Name]

---

## 1. Item Definition

| Field | Value |
|-------|-------|
| Item Name | [e.g., Gateway ECU, AEB System, TCU] |
| Vehicle Program | [Program name and model year] |
| Hardware Version | [HW Rev X.Y] |
| Software Version | [SW V X.Y.Z] |
| TARA Scope | [In-scope ECUs, interfaces, functions] |
| Related Standards | ISO/SAE 21434, ISO 26262 (ASIL: [X]), UNECE R155 |
| Document References | [System spec, architecture doc, DBC files] |

### 1.1 Item Boundary Diagram

```
[Insert ASCII or attached diagram showing:]
- External interfaces (CAN buses, Ethernet VLANs, OBD, Bluetooth, cellular)
- Connected ECUs and systems
- Data flows
- Trust boundaries (solid line = trusted, dashed = untrusted)
```

---

## 2. Asset Identification

> Assets are anything with cybersecurity value: sensitive data, safety-critical functions, or security properties.

| Asset ID | Asset Name | Asset Type | Cybersecurity Property | Justification |
|----------|-----------|------------|----------------------|---------------|
| A-001 | [e.g., AEB Brake Command (CAN 0x244)] | Function | Integrity, Authenticity | Tampered AEB command could cause unintended braking |
| A-002 | [e.g., ECU Flash Memory] | Resource | Integrity, Authenticity | Unauthorized firmware could replace safety code |
| A-003 | [e.g., Vehicle VIN (DID 0xF190)] | Data | Confidentiality | Links to owner identity + vehicle history |
| A-004 | [e.g., Diagnostic Session (UDS)] | Function | Authorization | Unauthorized access enables flash/ECU takeover |
| A-005 | [Add more assets] | | | |

**Asset Types**: Data, Function, Resource, External Entity
**Cybersecurity Properties**: Confidentiality (C), Integrity (I), Authenticity (A), Availability (Av), Authorization (Az)

---

## 3. Threat Scenario Analysis

> For each asset × attack path combination, define one threat scenario.

| Threat ID | Asset ID | Threat Description | Attack Path | Attacker Profile | STRIDE Category | Violated Property |
|-----------|----------|-------------------|-------------|------------------|-----------------|------------------|
| T-001 | A-001 | Attacker injects spoofed AEB command to trigger false braking | Remote → Infotainment → Gateway → Chassis CAN → AEB ECU | Remote, motivated, CAN expertise | S (Spoofing) | Integrity, Authenticity |
| T-002 | A-002 | Attacker flashes malicious firmware via unauthorized programming session | Physical → OBD-II → UDS → ECU Flash | Physical access (30 min), UDS tool | T (Tampering) | Integrity |
| T-003 | A-003 | Telematics backend breach exposes VIN + GPS history | Remote → OTA Backend → Database | Remote (cloud attacker) | ID (Info Disclosure) | Confidentiality |
| T-004 | A-004 | Brute force UDS Security Access to bypass authentication | Physical → OBD-II → UDS 0x27 | Physical, low skill (script kiddie) | E (Elevation of Privilege) | Authorization |
| T-005 | [Add] | | | | | |

---

## 4. Impact Rating

> Rate impact in 4 categories: Safety (S), Financial (F), Operational (O), Privacy (P).

| Threat ID | Safety Impact | S Rating | Financial Impact | F Rating | Operational Impact | O Rating | Privacy Impact | P Rating | Overall Worst Case |
|-----------|--------------|----------|-----------------|----------|--------------------|----------|----------------|----------|-------------------|
| T-001 | Unintended braking at highway speed → rear collision → fatalities | **S3** | Product recall, legal liability | F3 | Vehicle immobilization | O2 | None | P0 | **S3** |
| T-002 | Modified AEB/ADAS logic → incorrect responses → S3 potential | **S3** | Recall + criminal liability | F3 | Multiple functions lost | O3 | None | P0 | **S3** |
| T-003 | No direct safety impact | S0 | GDPR fine up to 4% revenue | F2 | None | O0 | VIN + location exposed | **P3** | **P3** |
| T-004 | Depends on what attacker does after access | S2 | Recall if widespread | F2 | ECU reflash downtime | O2 | None | P0 | S2 |

**Safety Severity Scale**:
- S0: No injuries
- S1: Light and moderate injuries
- S2: Severe and life-threatening injuries
- S3: Life-threatening injuries, fatalities

---

## 5. Attack Feasibility Rating

> Rate how easily each threat can be exploited. Consider: Elapsed Time, Expertise, Knowledge, Equipment, Window.

| Threat ID | Elapsed Time | Expert Needed | Item Knowledge | Equipment | Window | **Feasibility Score** |
|-----------|-------------|---------------|----------------|-----------|--------|----------------------|
| T-001 | >1 week (low) | High expertise | Item knowledge needed | Standard (CAN USB) | Wide | **F3** |
| T-002 | <1 day (high) | Medium | Low (OBD tools available) | Standard (PCAN) | On access | **F4** |
| T-003 | >1 month | High | Low (cloud attack) | Standard (laptop) | Always open | **F2** |
| T-004 | <1 day | Low (script kiddie) | Low | Standard | On access | **F4** |

**Feasibility Scale (ISO 21434)**:
- F1: Very low feasibility (nation-state level effort)
- F2: Low feasibility (skilled researcher, weeks of work)
- F3: Medium feasibility (skilled attacker, days of work)
- F4: High feasibility (basic skills, available tools)

---

## 6. Risk Determination

> Risk Matrix (ISO 21434, Table A.8): Severity × Feasibility → Risk Level

```
RISK MATRIX:
         │  F1  │  F2  │  F3  │  F4
─────────┼──────┼──────┼──────┼──────
  S3     │  5   │  6   │  7   │  7
  S2     │  4   │  5   │  6   │  7
  S1     │  2   │  3   │  4   │  5
  S0     │  1   │  1   │  2   │  3
```

| Threat ID | Severity | Feasibility | **Risk Level** | **Risk Category** |
|-----------|----------|-------------|----------------|-------------------|
| T-001 | S3 | F3 | **7** | Intolerable — must treat |
| T-002 | S3 | F4 | **7** | Intolerable — must treat |
| T-003 | P3 | F2 | **6** | Intolerable — must treat |
| T-004 | S2 | F4 | **7** | Intolerable — must treat |

**Risk Categories**:
- 1–4: Tolerable (no action required, document)
- 5–6: ALARP (reduce if reasonably practicable)
- 7: Intolerable (must be reduced before release)

---

## 7. Risk Treatment

> For each intolerable/ALARP risk, define treatment option and cybersecurity control.

| Threat ID | Risk Level | Treatment Option | Cybersecurity Control | Residual Risk | Control Reference |
|-----------|-----------|------------------|-----------------------|---------------|------------------|
| T-001 | 7 | Reduce | Deploy SecOC (CMAC-AES-128 + 24-bit freshness) on AEB CAN message 0x244 | 3 (Tolerable) | CG-001 |
| T-001 | 7 | Reduce | Gateway firewall: block Chassis CAN messages from Infotainment domain | 3 | CG-001 |
| T-002 | 7 | Reduce | Signed firmware (ECDSA P-256) + anti-rollback counter in bootloader | 3 | CG-002 |
| T-002 | 7 | Reduce | UDS Security Access lockout: 3 attempts + 10s delay | 4 | CG-002 |
| T-003 | 6 | Reduce | Backend: encrypted at-rest + TLS 1.3 in transit + access control | 2 | CG-003 |
| T-004 | 7 | Reduce | UDS Security Access lockout (as T-002) + HMAC-based seed-key | 3 | CG-002 |

**Treatment Options** (ISO 21434 §15.8):
- **Reduce**: Implement security control to lower risk
- **Avoid**: Remove the feature/function entirely
- **Transfer**: Contractual obligation to supplier
- **Accept**: Document + management signature (only for Tolerable risks)

---

## 8. Cybersecurity Goals

> One cybersecurity goal per group of related threats. This is the top-level security requirement.

| Goal ID | Cybersecurity Goal Statement | CAL | Derived From | Notes |
|---------|------------------------------|-----|--------------|-------|
| CG-001 | The AEB brake command (CAN 0x244) shall be authenticated against spoofing and replay with a probability of detection > 99.99% | **CAL 4** | T-001 | SecOC required |
| CG-002 | ECU firmware shall only be updated with verified OEM-signed packages; unauthorized flashing shall be prevented | **CAL 4** | T-002 | Secure Boot + signed OTA |
| CG-003 | Vehicle identity and location data shall be protected against unauthorized disclosure | **CAL 2** | T-003 | Backend + transport security |
| CG-004 | Diagnostic session escalation shall require authenticated security access with lockout policy | **CAL 3** | T-004 | UDS DCM config |

**CAL Levels** (ISO 21434):
- CAL 1: Lowest rigor → Risk Level 1-3
- CAL 2: → Risk Level 3-4
- CAL 3: → Risk Level 5
- CAL 4: Highest rigor → Risk Level 6-7

---

## 9. TARA Summary Dashboard

| Metric | Value |
|--------|-------|
| Total Assets identified | [N] |
| Total Threat Scenarios | [N] |
| Intolerable Risks (Level 7) | [N] |
| ALARP Risks (Level 5-6) | [N] |
| Tolerable Risks (Level 1-4) | [N] |
| Cybersecurity Goals defined | [N] |
| Open (untreated) risks | **[Must be 0 before release]** |

---

## 10. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Lead Cybersecurity Engineer | | | |
| System Architect | | | |
| Safety Manager | | | |
| Project Manager | | | |

---

## Appendix A: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | YYYY-MM-DD | [Name] | Initial release |
| 1.1 | YYYY-MM-DD | [Name] | Added T-005 after architecture change |
