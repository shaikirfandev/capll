# Part 15 — Requirements & Traceability

---

## 15.1 Requirement Types

| Type | Description | Tool |
|---|---|---|
| System Requirement | What the whole system must do | DOORS, Polarion |
| Software Requirement | What the software must do | DOORS, Polarion |
| Interface Requirement | How ECUs communicate | ICD, DBC, ARXML |
| Integration Requirement | How components work together | Integration spec |
| Diagnostic Requirement | UDS services, DTCs | Diagnostic spec |
| Safety Requirement | ISO 26262 derived safety goals | Safety plan |
| Cybersecurity Requirement | ISO/SAE 21434 derived | Cybersecurity spec |

---

## 15.2 Requirement Traceability Chain

```
Customer Need
    ↓
System Requirement (SRS)
    ↓
Software Requirement
    ↓
Software Design (SWC, architecture)
    ↓
Source Code (Implementation)
    ↓
Unit Test Case
    ↓
Integration Test Case
    ↓
System / Vehicle Test Case
    ↓
Validation Evidence
```

**Every step must be traceable in both directions (forward and backward).**

---

## 15.3 Requirements Traceability Matrix (RTM)

| Req ID | Requirement | Design Ref | Code Ref | Test Case | Test Status | Notes |
|---|---|---|---|---|---|---|
| SW-001 | Vehicle speed displayed within 200ms | SpeedSWC.c | speed_update() | TC-CLUS-001 | PASS | Verified in HIL |
| SW-002 | AEB shall trigger below 150ms latency | AEB_Control.c | aeb_trigger() | TC-AEB-001 | PASS | Vehicle test |
| SW-003 | UDS 0x22 0xF190 returns 17-byte VIN | DCM_Config | Dcm_ReadDid() | TC-DIAG-001 | PASS | CANoe verified |
| SW-004 | DTC 0x100501 set on sensor failure | DEM_Config | Dem_ReportError() | TC-DEM-001 | FAIL | Under investigation |

---

## 15.4 DOORS Workflow

IBM DOORS (Dynamic Object-Oriented Requirements System):

1. Create module for system requirements
2. Import OEM requirements document
3. Assign IDs automatically (SYS_001, SYS_002...)
4. Create child module for software requirements (link to system req)
5. Create child module for test cases (link to software req)
6. Generate RTM report: shows all links, gaps
7. Monitor: coverage = (linked requirements) / (total requirements) × 100%

---

## 15.5 Impact Analysis

When a requirement changes:
1. Identify all downstream linked artifacts (design, code, tests)
2. Assess impact on each artifact
3. Raise change request (CR) in change management system
4. Plan re-work and re-testing
5. Ensure traceability links updated for changed artifacts

---

## 15.6 Requirement Quality Rules

**SMART requirements:**
- **S**pecific — clearly defined, no ambiguity
- **M**easurable — has acceptance criteria (e.g., < 200ms, not "fast")
- **A**chievable — technically feasible
- **R**elevant — needed for the system
- **T**estable — can be verified with a test

**Bad:** "The cluster shall show speed quickly."
**Good:** "The cluster shall update the vehicle speed display within 200ms of receiving the CAN speed signal."

---

## Summary

| Tool | Use |
|---|---|
| DOORS | Requirements storage, links, RTM |
| Polarion | Modern alternative to DOORS |
| Jira | Defect tracking, linked to requirements |
| Excel/CSV | Simple RTM for small projects |
| Impact analysis | Change management, re-test scope |

---

*Next: [Part 16 — Automotive Standards](part-16-standards.md)*
