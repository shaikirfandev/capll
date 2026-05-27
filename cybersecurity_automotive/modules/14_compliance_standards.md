# Module 14 — Compliance & Standards

> Level: Intermediate–Advanced | Est. study time: 8 hours

---

## 14.1 Standards Landscape Overview

```
AUTOMOTIVE CYBERSECURITY STANDARDS ECOSYSTEM:

  ┌────────────────────────────────────────────────────────────────┐
  │                 REGULATORY (MANDATORY)                        │
  │                                                               │
  │  UNECE R155 ──────────── Cybersecurity Management System      │
  │  (Vehicle Type Approval)   Required for EU/Japan/Korea       │
  │                                                               │
  │  UNECE R156 ──────────── Software Update Management System    │
  │  (Vehicle Type Approval)   OTA update process regulation     │
  └───────────────────────────┬────────────────────────────────────┘
                              │ fulfilled by →
  ┌───────────────────────────▼────────────────────────────────────┐
  │                 TECHNICAL STANDARDS                           │
  │                                                               │
  │  ISO/SAE 21434 ─────────── Cybersecurity Engineering Process  │
  │  (Primary automotive CS)   TARA, cybersec goals, V-model     │
  │                                                               │
  │  SAE J3061 ────────────── Cybersecurity Guidebook            │
  │  (US-focused predecessor)  Less prescriptive than 21434      │
  │                                                               │
  │  ISO 15118 ────────────── EV–Charger Communication Security   │
  │  ISO 26262 ────────────── Functional Safety (complementary)  │
  └───────────────────────────┬────────────────────────────────────┘
                              │ implemented via →
  ┌───────────────────────────▼────────────────────────────────────┐
  │                 IMPLEMENTATION STANDARDS                      │
  │                                                               │
  │  AUTOSAR SecOC / Crypto   ECU-level security implementation   │
  │  IEC 62443                Industrial/infrastructure security  │
  │  NIST CSF                 Risk management framework (US)      │
  │  ETSI EN 303 645          Connected consumer devices (IoT)   │
  └───────────────────────────────────────────────────────────────┘
```

---

## 14.2 ISO/SAE 21434 Deep-Dive

```
ISO/SAE 21434:2021 STRUCTURE:

  Clause  │ Title                          │ Key Deliverables
  ────────┼────────────────────────────────┼──────────────────────────────
  §5      │ Organization Management        │ Cybersecurity Policy
          │                                │ Cybersecurity culture evidence
  §6      │ Project Management             │ Cybersecurity Plan
          │                                │ Cybersecurity Case
  §7      │ Distributed development        │ SOW with supplier CS requirements
          │                                │ Supplier audit evidence
  §8      │ Continual cybersecurity        │ Incident management process
          │                                │ Vulnerability monitoring
  §9      │ Concept phase                  │ Item Definition
          │                                │ Cybersecurity Goals
          │                                │ Cybersecurity Claims
  §10     │ Product development (design)   │ Cybersecurity Requirements
          │                                │ TARA
          │                                │ Cybersecurity Architecture
  §11     │ Product development (impl.)    │ Cybersecurity Design Specs
          │                                │ Source code analysis
  §12     │ Post-development               │ Cybersecurity Validation
          │                                │ Penetration testing
  §13     │ Production                     │ Production security controls
  §14     │ Operations & maintenance       │ Incident response
          │                                │ Vulnerability management
  §15     │ End of cybersecurity support   │ EOL planning
  §A–F    │ Annexes                        │ Informative guidance
```

### ISO 21434 TARA Process (§15)

```
Step 1: ASSET IDENTIFICATION
  Asset = anything with cybersecurity value (data, function, property)
  
  Template entry:
  Asset ID: A-001
  Asset Name: AEB Brake Command (CAN message 0x244)
  Asset Type: Function
  Cybersecurity Property: Integrity, Authenticity
  
Step 2: THREAT SCENARIO ANALYSIS
  For each asset × attack vector × threat agent:
  
  Threat ID: T-001
  Threat: Spoofed AEB command triggers unnecessary braking
  Threat Agent: Remote attacker (via compromised infotainment)
  Attack Path: Infotainment → Gateway → Chassis CAN → AEB ECU
  Violated Property: Integrity, Authenticity
  
Step 3: IMPACT RATING
  Impact Categories: Safety (S), Financial (F), Operational (O), Privacy (P)
  
  Severity levels (S0–S3):
  S0: No injuries
  S1: Light injuries
  S2: Severe injuries
  S3: Life-threatening / fatal injuries
  
  T-001 Impact: S3 (false braking at highway speed → rear collision)
  
Step 4: ATTACK FEASIBILITY
  Factors: Elapsed Time, Specialist Expertise, Knowledge of Item, 
           Window of Opportunity, Equipment
  
  Feasibility: 1 (LOW) to 4 (HIGH) — higher = more feasible = higher risk
  
  T-001 Feasibility: 3 (attacker needs CAN expertise but tool exists)
  
Step 5: RISK DETERMINATION
  Risk = f(Impact, Feasibility)
  
  Risk matrix (ISO 21434 Table A.8):
  
       │ F1  │ F2  │ F3  │ F4
  ─────┼─────┼─────┼─────┼─────
  S3   │  5  │  6  │  7  │  7   ← T-001: S3×F3 = Risk Level 7
  S2   │  4  │  5  │  6  │  7
  S1   │  2  │  3  │  4  │  5
  S0   │  1  │  1  │  2  │  3
  
  Risk Levels: 1-2 = Tolerable, 3-4 = ALARP, 5-7 = Intolerable
  
Step 6: RISK TREATMENT
  For each intolerable risk:
  Option A: Reduce (add security control)
  Option B: Avoid (remove feature)
  Option C: Transfer (contract clause with supplier)
  Option D: Accept (document + management approval, only for low risks)
  
  T-001 Treatment: Reduce → Deploy SecOC on AEB CAN message
  
Step 7: CYBERSECURITY GOAL
  Derived from intolerable risk:
  
  CS Goal ID: CG-001
  Statement: "The AEB brake command shall be authenticated and 
              protected against replay attacks"
  Cat: CAL 4 (highest, due to S3 impact)
  Derived from: T-001, T-002
```

---

## 14.3 UNECE R155 Compliance Requirements

```
WHAT VEHICLE TYPES REQUIRE R155 COMPLIANCE?
  - New type approvals in EU: July 2022 onwards
  - All new passenger vehicles sold in EU: July 2024 onwards
  - Commercial vehicles: phased in per category

R155 REQUIRES OEM TO DEMONSTRATE:

  1. CSMS (Cybersecurity Management System) in place
     → Documented policy, roles, risk process, incident management
     → Third-party audit by Technical Service required
     → CSMS Certificate issued (valid 3 years)
     
  2. Per-vehicle-type risk assessment
     → TARA performed per ISO 21434 §15
     → Risk treatments implemented for all intolerable risks
     → Residual risk accepted and documented
     
  3. Cybersecurity test documentation
     → Pentest evidence for each vehicle type
     → V&V test reports
     
  4. Post-production cybersecurity management
     → OTA capability for security patches
     → Incident monitoring (VSOC or equivalent)
     → Vulnerability disclosure process
     
  5. Supply chain cybersecurity
     → Tier-1 suppliers must meet CS requirements (SOW/contractual)
     → Evidence of supplier CS capability assessments

R155 ATTACK SURFACES (Annex 5 — vehicle attack list):
  - Backend servers
  - Communication channels (V2X, OTA, diagnostic)
  - Vehicle software update (SUMS)
  - Third-party software
  - External interfaces (OBD, TPMS, V2G, infotainment apps)
  - Sensors (GPS spoofing, sensor manipulation)
  - Humans (social engineering, insider threats)
```

---

## 14.4 ASPICE in Cybersecurity Context

```
ASPICE (Automotive SPICE) — Process Assessment Model:

  ASPICE Capability Level (CL):
  CL0: Incomplete — process not performed
  CL1: Performed — outputs exist but not managed
  CL2: Managed — planned, monitored, controlled
  CL3: Established — standard process, tailored consistently
  
  Industry minimum for new programs: CL2 for safety, CL2+ for cybersecurity
  Premium OEMs (BMW, Mercedes): require CL3 from Tier-1 suppliers
  
  Cybersecurity-relevant ASPICE processes:
  ┌─────────────┬──────────────────────────────────────────────┐
  │ Process ID  │ Name                                         │
  ├─────────────┼──────────────────────────────────────────────┤
  │ ENG.1       │ Requirements Elicitation (CS requirements)   │
  │ ENG.2       │ System Requirements Analysis                 │
  │ ENG.3       │ System Architectural Design (secure arch)    │
  │ ENG.4       │ Software Requirements Analysis               │
  │ ENG.5       │ Software Design (secure design patterns)     │
  │ ENG.6       │ Software Construction (secure coding)        │
  │ ENG.7       │ Software Integration Testing (CS test cases) │
  │ ENG.8       │ Software Testing (penetration testing)       │
  │ SUP.1       │ Quality Assurance (CS audit)                 │
  │ SUP.8       │ Configuration Management (firmware versioning│
  │ SUP.9       │ Problem Resolution Management (CVE handling) │
  └─────────────┴──────────────────────────────────────────────┘
```

---

## 14.5 NIST Cybersecurity Framework for Automotive

```
NIST CSF CORE FUNCTIONS — AUTOMOTIVE MAPPING:

IDENTIFY (Know your assets):
  ├── Asset inventory: all ECUs, communication interfaces, external connections
  ├── TARA per ISO 21434 (risk assessment)
  └── Supply chain risk: tier-1/tier-2 suppliers

PROTECT (Implement controls):
  ├── Access Control: UDS session management, SecOC, ECU security access
  ├── Protective Technology: HSM, Secure Boot, MPU
  └── Training: cybersecurity training for all engineers

DETECT (Monitor for incidents):
  ├── IDS in gateway ECU
  ├── VSOC telemetry monitoring
  └── SIEM correlation rules

RESPOND (React to incidents):
  ├── Incident response playbooks (per IRP-001, IRP-002)
  ├── Communication plan (UNECE R155 notification)
  └── Forensic evidence collection from vehicles

RECOVER (Restore normal operations):
  ├── OTA patch deployment
  ├── Certificate rotation procedures
  └── Post-incident review and TARA update
```

---

## 14.6 IEC 62443 for Automotive (Charging Infrastructure)

```
IEC 62443 is the industrial cybersecurity standard — relevant for:
  - EV charging stations (EVSE) as industrial control systems
  - Smart factory (vehicle manufacturing)
  - V2G grid interfaces

SECURITY LEVELS (SL) — IEC 62443:
  SL1: Protection against casual/unintentional violations
  SL2: Protection against intentional violation with simple means
  SL3: Protection against intentional violation with sophisticated means
  SL4: Protection against state-sponsored attacks with unlimited resources

For EV charging (OCPP 2.0.1 backend):
  Target SL2 minimum for typical CSMS
  Target SL3 for high-profile charging networks (target of attacks)

Key IEC 62443 requirements for EV charging:
  ├── Authentication before any configuration change (OCPP SetVariables)
  ├── Encrypted transport (TLS 1.2 minimum, 1.3 recommended)
  ├── Security event logging (all actions logged with user identity)
  ├── Software integrity validation on update
  └── Network segmentation (EVSE on separate VLAN from office/corporate)
```

---

## 14.7 Compliance Audit Preparation Checklist

```
PRE-AUDIT PREPARATION:

DOCUMENTATION:
  [ ] Cybersecurity Policy signed by C-level
  [ ] Cybersecurity Plan for each vehicle program
  [ ] TARA worksheet (ISO 21434 §15 format) per vehicle type
  [ ] Cybersecurity Goals list with impact/feasibility rationale
  [ ] Cybersecurity Requirements derived from goals
  [ ] Architecture design with security controls marked
  [ ] Pentest reports (for programs in product development phase)
  [ ] Incident log (even if empty = "no incidents this period")
  [ ] Vulnerability monitoring evidence (CVE feed subscriptions, responses)
  [ ] OTA update management procedure document

SUPPLIER EVIDENCE:
  [ ] Tier-1 supplier CS requirement SOW
  [ ] Supplier CS questionnaires or audit results
  [ ] Evidence of supplier CS capability (ASPICE assessment, certifications)

TECHNICAL EVIDENCE:
  [ ] Secure Boot configuration files per ECU
  [ ] HSM key management procedure
  [ ] SecOC deployment list (which messages are protected)
  [ ] Pentest scope, methodology, and findings for each target
  [ ] Patch deployment procedure and SLA

COMMON AUDIT FINDINGS:
  ├── TARA not updated after engineering changes
  ├── No evidence of supplier CS assessments  
  ├── Cybersecurity goals not traceable to requirements
  ├── Penetration testing done too late (not fixing findings)
  └── No formal process for monitoring CVEs in used components
```

---

## 14.8 Summary — Module 14

```
KEY TAKEAWAYS:

✓ UNECE R155 = mandatory regulation (EU/Japan/Korea) for new vehicles from 2024
✓ ISO/SAE 21434 = how to implement R155 requirements technically
✓ TARA (§15 of 21434): Assets → Threats → Impact → Feasibility → Risk → Treatment
✓ Risk levels 5–7 in ISO 21434 matrix = intolerable = must be treated
✓ ASPICE CL2 = minimum for automotive, CL3 expected by premium OEMs
✓ NIST CSF maps naturally to VSOC (Identify, Protect, Detect, Respond, Recover)
✓ IEC 62443 SL2 required for EV charging infrastructure
✓ Audit prep: document everything — undocumented controls = non-compliant
```

**Next Module**: [15 — Real-World Attacks](15_real_world_attacks.md)
