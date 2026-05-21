# Verification & Validation — Complete Activities Guide

## 1. V&V Fundamentals: The Core Distinction

```
VERIFICATION: "Are we building the product right?"
              ─ Confirms outputs meet specified requirements (design inputs)
              ─ Objective evidence: inspection, analysis, test, demonstration
              ─ Done by: design engineer + V&V engineer
              ─ Output: Verification report in DHF

VALIDATION:  "Are we building the right product?"
             ─ Confirms device meets user needs and intended use
             ─ Objective evidence: usability study, clinical trial, simulated use
             ─ Done by: intended users (or representative users) ideally
             ─ Output: Validation report in DHF
```

### Why Both Are Required (ISO 13485 §8.3.4)
A device can verify perfectly against requirements yet still fail validation if:
- Requirements were incomplete or incorrect
- Intended use was not fully captured
- Users interact with the device differently than expected

---

## 2. V&V Planning — Master Validation Plan (MVP)

### Structure of a Master Validation Plan

```
MASTER VALIDATION PLAN
├── 1. Purpose and Scope
│   ├─ Document purpose
│   ├─ Product/system under test
│   └─ Regulatory basis (ISO 13485 §8.3, 21 CFR §820.30)
│
├── 2. References
│   ├─ Design inputs document
│   ├─ Risk management file
│   ├─ Software architecture doc (if applicable)
│   └─ Applicable standards
│
├── 3. Definitions and Acronyms
│
├── 4. V&V Strategy
│   ├─ Verification activities (unit test, integration test, system test)
│   ├─ Validation activities (simulated use, bench, clinical)
│   └─ Test levels and responsible parties
│
├── 5. Resource Requirements
│   ├─ Test equipment (calibrated instruments)
│   ├─ Test environment (lab conditions, temperature, humidity)
│   └─ Personnel qualifications
│
├── 6. Test Coverage Requirements
│   ├─ Requirements traceability approach
│   └─ Coverage criteria (100% of safety-critical requirements)
│
├── 7. Risk-Based Test Prioritization
│   └─ Higher risk items → more test cases, wider tolerances
│
├── 8. Deviation Handling
│   ├─ How deviations are documented
│   ├─ Severity classification
│   └─ Disposition process (accept/reject/retest)
│
├── 9. Completion Criteria
│   └─ What constitutes "test passed" for release
│
└── 10. Roles and Responsibilities
    ├─ V&V engineer
    ├─ Test executor
    ├─ Reviewer
    └─ Approver
```

---

## 3. Design Verification Activities

### 3.1 Inspection
Physical examination without testing:
- Visual inspection against drawing dimensions
- Material certificate verification
- Label legibility and content check
- Component identification (part numbers, revision levels)

### 3.2 Analysis
Mathematical / computational confirmation:
- Stress analysis (FEA, hand calculations)
- Thermal analysis
- Biocompatibility assessment (ISO 10993)
- Software code review / static analysis
- FMEA / fault tree analysis

### 3.3 Demonstration
Operating the device to show a feature works:
- Device powers on and off
- Alarm sounds when threshold exceeded
- User interface navigates correctly

### 3.4 Test (Most Common)
Quantitative measurement against acceptance criteria:
- Electrical performance (output voltage, current, power)
- Mechanical performance (force, torque, fatigue life)
- Software functional test (input → expected output)
- Environmental testing (IEC 60068: temperature, humidity, vibration)
- EMC testing (IEC 60601-1-2)

---

## 4. Design Validation Activities

### 4.1 Simulated Use Testing
Most common validation method for non-implantable devices:
- Use **representative users** (nurses, physicians, patients — not engineers)
- Use **production-equivalent** devices (not prototypes)
- Use **simulated use environment** (clinical simulation lab, or actual clinical setting)
- Tasks reflect **intended use scenarios** from user needs document

### 4.2 Clinical Investigation (Highest Evidence Level)
Required for Class III devices and most Class IIb:
- Conducted under ISO 14155 (clinical investigation of medical devices)
- Protocol reviewed by Ethics Committee / IRB
- Informed consent required
- Primary and secondary endpoints defined
- Statistical power calculation

### 4.3 Bench-Top Validation
For performance characteristics not requiring human subjects:
- Fluid delivery accuracy (infusion pumps)
- Filter efficiency (breathing circuits)
- Battery life under simulated clinical load

### 4.4 Usability Validation (IEC 62366-1 §5.9)
- **Summative evaluation**: Final validation with representative users
- Test critical tasks (identified from use error and risk analysis)
- Observe and record use errors, close calls, difficulties
- Pass criteria: No task failure on safety-critical tasks (typically)

---

## 5. Traceability — Requirements to V&V

### Requirements Traceability Matrix (RTM)

```
RTM Structure:

| Req ID  | Requirement Text          | Design Output | Verification Test | Validation Test | Status |
|---------|---------------------------|---------------|-------------------|-----------------|--------|
| UR-001  | Device shall deliver ...  | SDS §3.2.1    | TC-VER-001        | TC-VAL-010      | PASS   |
| UR-002  | Alarm at >40°C            | SDS §4.1.3    | TC-VER-015        | —               | PASS   |
| HR-005  | Risk control: temp guard  | FMEA-R-12     | TC-VER-022        | TC-VAL-011      | PASS   |
```

### Traceability Chain (Forward and Backward)
```
User Needs
    ↓ (trace forward)
Design Inputs (SRS/URD)
    ↓
Design Outputs (SDS, drawings, code)
    ↓
Verification Tests (prove output meets input)
    ↓
Validation Tests (prove device meets user needs)

← Backward trace: from any test → trace back to user need
```

### Golden Rule of Traceability
> Every test case must trace to at least one requirement.  
> Every requirement must have at least one test case.  
> No orphan requirements or orphan tests.

### Tools for Traceability
| Tool | Use |
|------|-----|
| Jama Connect | Requirements + traceability + reviews |
| IBM DNG (DOORS Next) | Requirements management + RTM |
| IBM RQM (Quality Manager) | Test case management + execution |
| PolarionALM | Full ALM: requirements → defects → tests |
| Excel RTM | Small projects / supplements |

---

## 6. DHF and DMR Integrity

### DHF Integrity Checklist
```
□ All design stages documented (plan → inputs → outputs → review → V&V → transfer)
□ Design inputs complete and approved before design outputs created
□ All design changes documented, reviewed, approved (§8.3.10)
□ Risk management file referenced and integrated
□ Verification results trace to design inputs
□ Validation results trace to user needs
□ All review records signed and dated
□ Software configuration baseline documented
□ Device transfer to manufacturing documented
□ Regulatory submission documents included
```

### DMR Integrity Checklist
```
□ All controlled documents at correct revision
□ Bill of Materials (BOM) complete and approved
□ All manufacturing procedures referenced
□ Acceptance criteria defined for each production step
□ Labelling master copy approved
□ Packaging and sterilisation specifications included
□ Software release version documented
□ Calibration requirements specified
```

### Change Control for DHF/DMR
```
Change Request → Impact Assessment → Risk Assessment →
Design Verification/Re-validation (if required) →
Document Update → Review/Approval → Release
```

**Key Question at Impact Assessment:**
- Does this change affect safety or performance?
- Does this require re-testing? (partial or full regression)
- Does this affect regulatory submission?
- Does this affect labelling / IFU?

---

## 7. Test Protocol Writing — Full Template

### Standard Medical Device Test Protocol Structure

```
DOCUMENT HEADER
================
Protocol Number:    [PROJECT]-VER-[NNN]-[REV]
Protocol Title:     [Test Description]
Device Under Test:  [Device Name, Model, SW Version]
Regulatory Basis:   ISO 13485 §8.3.7 / [applicable standard]
Author:             [Name, Title]
Reviewer:           [Name, Title]
Approver:           [Name, Title]
Date:               [YYYY-MM-DD]
Revision History:   [Table of revisions]

1. PURPOSE
==========
State what is being verified/validated and which requirements are addressed.
"This protocol verifies that [Device] delivers [performance metric] within
[tolerance] under [conditions] per requirement [REQ-XXX]."

2. SCOPE
========
What is included and excluded. Device configuration, software version, accessories.

3. APPLICABLE DOCUMENTS
========================
- Design Requirements Specification Rev X
- Risk Management File Rev X
- IEC/ISO standard reference
- Calibration procedures

4. DEFINITIONS
==============

5. RESOURCES
============
5.1 Equipment
    - Test equipment list with calibration status and due date
    - Device under test description
5.2 Consumables
5.3 Personnel
    - Qualifications required (training records)

6. SAFETY PRECAUTIONS
=====================
List any hazards: electrical, biological, chemical, mechanical

7. TEST CONDITIONS
==================
- Environmental: Temperature X°C ± Y°C, Humidity ≤ Z%
- Power supply: [nominal / worst case / edge]
- Software configuration

8. PROCEDURES
=============
For each test:

Test ID:    TC-[NNN]
Title:      [Descriptive test name]
Req Ref:    [Requirement ID(s) being verified]
Risk Ref:   [Risk ID if applicable]
Objective:  [What is being demonstrated]
Setup:      [Step-by-step setup instructions with diagrams/photos if needed]
Procedure:
    Step 1: [Action] → Expected result: [What should happen]
    Step 2: [Action] → Expected result: [What should happen]
    ...
Acceptance Criteria: [PASS if measured value is within X of Y]
Actual Result:       [To be filled during execution]
Pass/Fail:           [ ]

9. DEVIATION HANDLING
=====================
Document all deviations from protocol:
- Deviation number, date, description
- Impact assessment
- Disposition (accept/reject/retest with justification)

10. COMPLETION CRITERIA
========================
Protocol is complete when:
- All test cases executed
- All pass/fail entries recorded
- All deviations documented and dispositioned
- Protocol signed by executor and reviewer

11. RESULTS SUMMARY
====================
[To be completed after execution]
- Total tests: X
- Pass: Y
- Fail: Z
- Deviations: W

SIGNATURES
==========
Executed by: _________________ Date: ________
Reviewed by: _________________ Date: ________
Approved by: _________________ Date: ________
```

---

## 8. Handling Test Failures and Deviations

### Failure Classification

| Severity | Definition | Response |
|----------|-----------|---------|
| Critical | Failure puts patient at risk; safety requirement failed | Stop testing, NCR, design change required |
| Major | Performance requirement failed; not safety-related | Investigate root cause, may require design change |
| Minor | Cosmetic, documentation issue, no impact on function | Document, disposition, continue |

### Deviation vs Failure
- **Deviation**: Departure from the protocol procedure (e.g., wrong test sequence)
- **Failure**: Test results do not meet acceptance criteria
- Both must be documented; deviations don't automatically mean failure

### Root Cause Analysis (for failures)
```
5-Why Analysis Example:
Problem:  Battery life measured 4.2 hours vs requirement ≥5 hours

Why 1: Power consumption was higher than designed
Why 2: LCD backlight was not operating in low-power mode
Why 3: Low-power mode flag was not set in firmware initialization
Why 4: Power management requirement was not included in software SRS
Why 5: Software requirements review did not include power-related review criteria

Root Cause: Insufficient requirements review process for power management
Corrective Action: Add power management checklist to SRS review procedure
```
