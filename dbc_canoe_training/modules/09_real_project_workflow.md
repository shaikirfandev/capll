# Module 09 — Real-World Project Workflow

> **Level**: Advanced (Industry Practice)  
> **Duration**: ~3 hours  
> **Goal**: Understand how DBC creation and management fits into a real automotive project from requirements to release.

---

## 9.1 The DBC Lifecycle in an Automotive Project

```
Phase 1: System Definition
  OEM System Architect writes communication requirements
  → Signal list, network topology, cycle times, safety levels
  
Phase 2: Database Creation
  Supplier Network Architect creates draft DBC
  → From communication matrix, manual or CANdb++
  
Phase 3: Review & Approval
  Peer review by other architects → Manager review → OEM sign-off
  
Phase 4: Integration
  All ECU teams import approved DBC into their projects
  ECU software uses DBC as the "truth document"
  
Phase 5: Verification
  System test: verify ECUs communicate correctly per DBC
  HIL test: automated test suites against DBC
  
Phase 6: Maintenance
  ECR (Engineering Change Request) → update DBC → re-approve
  Release version tagged in source control
```

---

## 9.2 Team Roles and Responsibilities

| Role | DBC Responsibility |
|------|-------------------|
| OEM System Architect | Defines communication requirements, approves final DBC |
| OEM/Tier1 Network Architect | Creates and maintains the DBC, owns the communication matrix |
| ECU Software Engineer | Uses DBC for signal encoding/decoding in embedded code |
| Test/Validation Engineer | Uses DBC in CANoe for automated test creation |
| Integration Lead | Manages version control, coordinates change process |
| Functional Safety Engineer | Reviews ASIL assignments for signals, E2E requirements |

---

## 9.3 OEM Project Phases Mapped to DBC

### Phase 1: Concept → System Spec Matrix (Draft DBC)

```
Timeline: Concept Phase (12–18 months before SOP)
Owner: OEM System Architect + Supplier Network Architect

Activities:
  ✓ Define network topology (how many buses, what bitrate)
  ✓ Identify ECU list and communication partners
  ✓ Create system specification matrix (Excel)
  ✓ Generate draft DBC from matrix
  ✓ ID allocation: reserve ranges per functional domain

OEM ID Allocation Example:
  0x000–0x0FF  Reserved / Safety Management
  0x100–0x1FF  ADAS ECUs (Radar, Camera, Fusion)
  0x200–0x2FF  Powertrain (ABS, AEB, EPS)
  0x300–0x3FF  Body (ECM, TCM, ACM)
  0x400–0x4FF  Comfort (BCM, AC, Lights)
  0x500–0x5FF  Infotainment
  0x600–0x6FF  Diagnostics
  0x700–0x7FF  UDS / OBD2
  0x7DF        OBD2 Functional Request (fixed)
```

### Phase 2: Development → Baseline DBC

```
Timeline: Development Phase (9–14 months before SOP)
Owner: Network Architect

Activities:
  ✓ Create baseline DBC v1.0 in CANdb++
  ✓ Define all attributes (GenMsgCycleTime, E2E, SecOC)
  ✓ Internal review (peer review)
  ✓ Publish baseline to all ECU teams via SharePoint/Git
  
Deliverables:
  ADAS_HS1_v1.0_BASELINE.dbc
  ADAS_HS1_v1.0_Communication_Matrix.xlsx
  ADAS_HS1_v1.0_Review_Minutes.pdf
```

### Phase 3: Integration → Verified DBC

```
Timeline: Integration Phase (6–9 months before SOP)
Owner: Integration Lead

Activities:
  ✓ All ECU teams use DBC for ECU software generation
  ✓ AUTOSAR SWC configs generated from DBC/ARXML
  ✓ CAPL test suites written for each ECU's signals
  ✓ Regular integration builds: all ECUs on common bus
  ✓ Bug reports → ECR → DBC patch → new baseline
  
Typical ECRs in integration:
  ECR-001: AEB signal AEB_Decel_Req max changed to 30 m/s² (was 25.5)
  ECR-002: Add CRC protection to EPS_Status message
  ECR-003: WheelSpeed cycle time changed from 10ms to 5ms (safety change)
```

### Phase 4: Validation → Release DBC

```
Timeline: Validation Phase (3–6 months before SOP)
Owner: V&V Team + OEM

Activities:
  ✓ System test on complete vehicle
  ✓ All CANoe test suites pass
  ✓ OEM review and approval
  ✓ DBC locked (RELEASED status)
  ✓ Archive to release management system
  
Deliverables:
  ADAS_HS1_v3.2_RELEASE.dbc
  ADAS_HS1_v3.2_Test_Report.pdf
  ADAS_HS1_v3.2_OEM_Approval.pdf (signed)
```

---

## 9.4 Version Control for DBC Files

### Git Strategy for DBC

```bash
# Repository structure
/network_databases/
  /ADAS_HS1/
    ADAS_HS1_v3.2_RELEASE.dbc
    ADAS_HS1_Communication_Matrix_v3.2.xlsx
    CHANGELOG.md
    
  /Body_HS2/
    Body_HS2_v2.1_RELEASE.dbc
    ...

# .gitattributes — enforce CRLF for DBC on Windows
*.dbc text eol=crlf
*.can text eol=crlf

# Branch strategy
main          → always RELEASED version
develop       → integration work
feature/ECR-xxx → individual change branch

# Change workflow
git checkout -b feature/ECR-1234-aeb-decel-range
# Make changes to ADAS_HS1_v3.2_RELEASE.dbc
git add ADAS_HS1_v3.2_RELEASE.dbc
git commit -m "ECR-1234: Increase AEB_Decel_Req max to 30 m/s2

- Changed AEB_Decel_Req max_phys from 25.5 to 30.0
- DLC unchanged: raw max 255 × 0.1 = 25.5, need factor change
- New factor: 0.12, max 255 × 0.12 = 30.6 (rounded to 30.0 in spec)
- Updated communication matrix row AEB_Decel_Req
- Reviewed by: Shaik Irfan (Network Architect), ECR approved by OEM

Refs: ECR-1234, JIRA: ADAS-4521"

git push origin feature/ECR-1234-aeb-decel-range
# Open Pull Request → peer review → merge to develop
```

### DBC Diff Analysis

```bash
# View what changed in a DBC update:
git diff HEAD~1 -- ADAS_HS1.dbc

# Filter to just message and signal changes:
git diff HEAD~1 -- ADAS_HS1.dbc | grep "^[+-][BO_| SG_]"

# Compare two release versions:
git show v2.3:ADAS_HS1.dbc > /tmp/old.dbc
git show v3.2:ADAS_HS1.dbc > /tmp/new.dbc
diff /tmp/old.dbc /tmp/new.dbc
```

---

## 9.5 Jira Integration for DBC Changes

### Ticket Types

```
ECR (Engineering Change Request):
  TYPE: Task or Story
  Priority: Critical (safety) / Major (function) / Minor (cleanup)
  Labels: DBC, CAN, NETWORK_ARCH
  
  Template:
  ┌────────────────────────────────────────────┐
  │ ADAS-4521: ECR-1234 AEB Decel Range Change │
  │                                             │
  │ Type: Engineering Change Request           │
  │ Priority: Major                            │
  │ Component: ADAS_HS1 DBC                    │
  │                                             │
  │ Current: AEB_Decel_Req max = 25.5 m/s²     │
  │ Requested: AEB_Decel_Req max = 30.0 m/s²   │
  │ Reason: Updated AEB algorithm requirement   │
  │                                             │
  │ Impact: AEB_ECU firmware, CANoe test suite  │
  │ Review: Network Arch + Functional Safety   │
  └────────────────────────────────────────────┘

DBC Review:
  TYPE: Review
  DBC file version attached as comment
  Reviewers: Network Architect, Integration Lead, OEM Rep

DBC Release:
  TYPE: Release
  All ECRs since last release attached
  Test report link in description
  "Release Criteria" checklist in description
```

---

## 9.6 ASPICE Compliance for DBC Work Products

### Relevant ASPICE Processes

| Process | DBC Relevance |
|---------|--------------|
| SYS.3 — System Architecture Design | Network topology decision, bus selection |
| SWE.1 — Software Requirements | Signal ranges, cycle times, ASIL assignments |
| SWE.2 — Software Architecture | AUTOSAR COM mapping to DBC signals |
| SWE.3 — Software Detailed Design | ECU signal encoding logic |
| SWE.4 — Software Unit Verification | Signal decode unit test |
| SWE.5 — Software Integration Test | Multi-ECU bus test with DBC |
| SWE.6 — Software Qualification Test | System test against DBC |

### Required DBC Work Products at ASPICE CL2

```
SYS.3:
  ✓ Network architecture diagram (bus topology)
  ✓ Communication matrix (Excel) ← source of DBC

SWE.1:
  ✓ Signal description with ranges, ASIL, E2E requirements

SWE.2:
  ✓ DBC file (v-controlled, reviewed, approved)
  ✓ AUTOSAR ARXML if AUTOSAR-based project

SWE.5:
  ✓ DBC test plan (which signals, which test cases)
  ✓ CANoe test module with all test cases

SWE.6:
  ✓ System test report (CANoe test run results)
  ✓ Bug tracking: all DBC-related defects logged in Jira
```

---

## 9.7 Real-World Project Scenario: AEB System Integration

### Scenario Description

```
Project: SUV2026 ADAS Development
Bus: CAN-HS1 (ADAS Safety Bus), 500 Kbps
ECUs: AEB_ECU (Continental) + ABS_ECU (Bosch) + CGW (Vector)
Problem: AEB braking not activating during test drives
```

### Root Cause Analysis via DBC

```
Step 1: Capture bus traffic with CANoe → log to .mf4
  → Filter: message 0x244 (AEB_Req)

Step 2: Replay in CANoe with ADAS_HS1_v3.2.dbc
  → Signal decode: AEB_Active shows 0 during expected braking
  → AEB_Decel_Req shows correct value (non-zero)

Step 3: Check DBC version installed in ECU
  → ABS_ECU firmware compiled with v3.1 DBC
  → v3.1: AEB_Active was bit 7 of byte 0
  → v3.2: AEB_Active moved to bit 0 of byte 0 (due to ECR-1198)

Root Cause: ABS_ECU firmware not updated to v3.2 DBC
  → ABS_ECU reading wrong bit position for AEB_Active
  → Braking activation signal never decoded as "1"

Fix: Rebuild ABS_ECU firmware with v3.2 DBC → resolved
Lesson: DBC version management in CI/CD pipeline prevents this
```

---

## 9.8 DBC in CI/CD Pipeline

### Automated DBC Validation in CI

```yaml
# .gitlab-ci.yml example for DBC validation
stages:
  - validate
  - test
  - release

dbc_syntax_check:
  stage: validate
  image: python:3.11
  script:
    - pip install cantools
    - python scripts/validate_dbc.py --dbc ADAS_HS1.dbc --matrix Communication_Matrix.csv
  only:
    changes:
      - "*.dbc"
      - "Communication_Matrix.csv"

dbc_version_check:
  stage: validate
  script:
    - grep -q "DatabaseVersion" ADAS_HS1.dbc || exit 1
    - grep -q "ApprovalStatus.*RELEASED" ADAS_HS1.dbc || echo "WARN: Not yet RELEASED"

dbc_regression_report:
  stage: test
  script:
    - diff baseline/ADAS_HS1_v3.1.dbc ADAS_HS1.dbc > diff_report.txt
    - cat diff_report.txt
  artifacts:
    paths:
      - diff_report.txt
```

---

## 9.9 Communication Matrix Template

### Sample Real-Project Matrix (Abbreviated)

| # | Message | ID | DLC | Cycle | Tx ECU | Rx ECU | Signal | Start | Len | Type | Factor | Offset | Min | Max | Unit | ASIL | E2E |
|---|---------|----|----|-------|--------|--------|--------|-------|-----|------|--------|--------|-----|-----|------|------|-----|
| 1 | WheelSpeed | 0x200 | 8 | 10ms | ABS_ECU | AEB_ECU,ECM | WheelSpeed_FL | 0 | 16 | U | 0.01 | 0 | 0 | 655.35 | km/h | B | CRC+AC |
| 1 | WheelSpeed | 0x200 | 8 | 10ms | ABS_ECU | AEB_ECU,ECM | WheelSpeed_FR | 16 | 16 | U | 0.01 | 0 | 0 | 655.35 | km/h | B | CRC+AC |
| 2 | AEB_Req | 0x244 | 8 | 20ms | AEB_ECU | CGW,IPC,ECM | AEB_Active | 0 | 1 | U | 1 | 0 | 0 | 1 | — | B | CRC+AC |
| 2 | AEB_Req | 0x244 | 8 | 20ms | AEB_ECU | CGW,IPC,ECM | AEB_Decel_Req | 4 | 8 | U | 0.1 | 0 | 0 | 25.5 | m/s² | B | — |

---

## Module 09 — Knowledge Check

1. What does "ECR" stand for in automotive project management?
2. At what project phase is the DBC typically "RELEASED" (locked)?
3. In Git, which branch typically holds the RELEASED DBC version?
4. What ASPICE process covers the DBC creation activity (network architecture)?
5. In the AEB root cause analysis scenario, what caused the braking system not to work?
6. What should be in a CI/CD pipeline to catch DBC regressions automatically?

**Answers:**
1. Engineering Change Request
2. Validation Phase (3–6 months before Start of Production)
3. `main` branch (development work on `develop`, features on `feature/ECR-xxx`)
4. SYS.3 (System Architecture Design) and SWE.2 (Software Architecture Design)
5. The ABS_ECU was compiled with an older DBC version (v3.1); the signal bit position had moved in v3.2 due to ECR-1198
6. Automated DBC syntax check (cantools parse), matrix compliance check (Python script), and diff report comparing to previous baseline
