# Design Control — ISO 13485 §8.3 Complete Guide

## 1. Design and Development Process Overview

ISO 13485 §8.3 mandates a formal design control process for all medical devices. The process is structured as a series of documented stages with gate reviews at each transition.

```
DESIGN AND DEVELOPMENT STAGES (ISO 13485 §8.3)

[User Needs / Intended Use]
         ↓
[§8.3.2] Design and Development Planning
  ─ Stages defined
  ─ Reviews, verification, validation responsibilities
  ─ Interfaces between teams
         ↓
[§8.3.3] Design Inputs
  ─ Functional requirements
  ─ Performance requirements
  ─ Safety requirements
  ─ Regulatory requirements
  ─ Risk controls
         ↓
[§8.3.4] Design Outputs
  ─ Drawings and specifications
  ─ Software architecture and code
  ─ BOM
  ─ Manufacturing instructions
  ─ Labelling requirements
         ↓
[§8.3.5] Design Review
  ─ Systematic examination at defined stages
  ─ Independent reviewer required
  ─ Action items tracked to closure
         ↓
[§8.3.6] Design Verification
  ─ Outputs meet inputs
  ─ Test reports, analyses, inspections
         ↓
[§8.3.7] Design Validation
  ─ Device meets user needs
  ─ Clinical evaluation, simulated use, usability
         ↓
[§8.3.8] Design Transfer
  ─ Specifications transferred to manufacturing
  ─ Production capability verified
         ↓
[§8.3.9] Design and Development Files (DHF)
  ─ Maintained throughout
  ─ All records above compiled
         ↓
[§8.3.10] Design Changes
  ─ Formal change control
  ─ Re-verification / re-validation as needed
```

---

## 2. Design and Development Planning (§8.3.2)

### What the Plan Must Cover
- **Stages** of design and development with start/end criteria
- **Review, verification, and validation** activities at each stage
- **Responsibilities** for each activity
- **Interfaces** between different teams (e.g., hardware-software)
- **Resource requirements** (people, equipment, budget)
- **Risk management** integration points
- **Regulatory requirements** applicable to the device

### Stage-Gate Structure
```
Stage 0: Feasibility
  ├─ Input: Concept and business case
  ├─ Activities: Market research, regulatory strategy, initial risk assessment
  └─ Exit: Feasibility report approved

Stage 1: Concept / Design Inputs
  ├─ Input: User needs, intended use
  ├─ Activities: User research, requirements definition, risk analysis (PHA)
  └─ Exit: Design Input Specification approved (Design Review 1)

Stage 2: System Design
  ├─ Input: Approved design inputs
  ├─ Activities: Architecture definition, subsystem specs, FMEA update
  └─ Exit: System Design Specification approved (Design Review 2)

Stage 3: Detailed Design
  ├─ Input: System design
  ├─ Activities: Detailed drawings, software detailed design, SOUP assessment
  └─ Exit: Detailed design approved, V&V plan approved (Design Review 3)

Stage 4: Verification & Validation
  ├─ Input: Approved detailed design
  ├─ Activities: Build prototypes, execute V&V, resolve defects, risk file complete
  └─ Exit: All V&V passed, DHF complete (Design Review 4 / Design Transfer Review)

Stage 5: Design Transfer
  ├─ Input: Verified and validated design
  ├─ Activities: Transfer to manufacturing, process validation, training
  └─ Exit: DMR approved, manufacturing ready
```

---

## 3. Design Inputs (§8.3.3)

### Categories of Design Inputs
| Category | Examples |
|----------|----------|
| Functional | "Shall measure ECG in 12 leads simultaneously" |
| Performance | "Shall measure heart rate 30–300 bpm, accuracy ±2 bpm" |
| Safety | "Shall not deliver patient leakage current >10 μA (BF applied part)" |
| Usability | "Shall complete defibrillation setup in < 60 seconds by trained responder" |
| Regulatory | "Shall comply with IEC 60601-1 Ed. 3.1 for electrical safety" |
| Interface | "Shall communicate via HL7 FHIR to hospital EHR" |
| Environmental | "Shall operate in ambient temperatures 5°C to 40°C, 30–85% RH non-condensing" |
| Sterilisation | "Shall withstand 50 sterilisation cycles using ethylene oxide per AAMI TIR28" |
| Labelling | "Shall bear CE marking per EU MDR Annex V if placed on EU market" |
| Risk controls | "Shall include air-in-line detection to prevent air embolism (RC-012)" |

### Writing Good vs Bad Design Inputs

**Bad (incomplete, non-verifiable):**
```
✗ "The device should be easy to use"
✗ "The device should have good battery life"
✗ "The device should be accurate"
✗ "The device should be safe"
```

**Good (specific, verifiable, measurable):**
```
✓ "Novice users (< 30 minutes training) shall complete routine startup in ≤ 3 minutes
    with ≤ 1 recoverable use error [usability evaluation, IEC 62366-1]"

✓ "Battery shall provide ≥ 8 hours continuous operation at 100 mL/hr infusion rate
    at 25°C [battery discharge test]"

✓ "Glucose concentration measurement accuracy shall be ±0.83 mmol/L for values
    < 5.5 mmol/L, or ±15% for values ≥ 5.5 mmol/L [ISO 15197:2013 §6.3]"

✓ "Patient leakage current shall not exceed 10 μA (AC) under single fault condition
    for BF applied parts [IEC 60601-1 §8.7.3, Table 2]"
```

### Criteria for Complete Design Inputs
- **SMART**: Specific, Measurable, Achievable, Relevant, Traceable
- No vague language ("adequate," "sufficient," "as required")
- Reference the test method or standard that will verify it
- Include applicable regulatory standard reference
- Every safety requirement cross-referenced to risk management file

---

## 4. Design Outputs (§8.3.4)

Design outputs are the deliverables that implement the design inputs.

### Types of Design Outputs
| Output Type | Examples |
|------------|---------|
| Mechanical drawings | Dimensional drawings (GD&T), assembly drawings |
| Electrical schematics | Circuit diagrams, PCB layouts |
| Software | Source code, compiled firmware, configuration files |
| Specifications | Material specs, component specs, tolerance specs |
| BOM | Full Bill of Materials with part numbers and revisions |
| Labelling | Device label, IFU, packaging label |
| Manufacturing specs | Assembly procedures, inspection criteria, test procedures |
| Software architecture | Detailed design specification, unit/module specs |

### Key Requirements for Design Outputs
1. Must **meet design inputs** (verified during verification phase)
2. Must be **adequate for production** (unambiguous instructions)
3. Must **reference acceptance criteria** (what is pass/fail for each spec)
4. Must identify **safety-critical characteristics** (for manufacturing attention)
5. Must be version-controlled in PLM

---

## 5. Design Reviews (§8.3.5)

### Purpose of Design Review
A design review is a **systematic and documented examination** of the design at a defined stage. It evaluates:
- Are design inputs complete and correct?
- Are design outputs meeting inputs?
- Are risks identified and controlled?
- Are the next stage activities appropriately planned?

### Who Must Attend
Per ISO 13485, design reviews must include **at minimum**:
- Representatives of all functions related to the stage under review
- **At least one person who is NOT directly responsible** for the design being reviewed (independent reviewer)

Typical attendees:
- Project Manager (facilitator)
- Design Engineer(s)
- Software Engineer(s)
- Quality / Regulatory Engineer
- Risk Management Representative
- Manufacturing Engineer (at later stages)
- Clinical / Usability Expert (at validation stage)

### Design Review Protocol
```
Pre-Review:
  ├─ Reviewer package distributed 5 business days in advance
  ├─ All attendees review materials before meeting
  └─ Independent reviewer confirms no conflict of interest

During Review:
  ├─ Each section reviewed against entry criteria checklist
  ├─ Questions and concerns raised and documented
  ├─ Action items assigned with owners and due dates
  └─ Pass / Conditional Pass / Fail decision recorded

Post-Review:
  ├─ Meeting minutes and action log distributed within 3 business days
  ├─ Action items tracked to closure
  └─ Stage exit criteria sign-off when all actions closed
```

---

## 6. Requirements Traceability Matrix (RTM)

### RTM Structure
```
RTM Columns:
ID | User Need | Design Input (SRS) | Design Output (DDS) | Test Case | Test Result | Risk Ref | Status
```

### RTM Example (partial)
| User Need | Design Input | Design Output | Test Case | Result | Risk |
|-----------|-------------|--------------|-----------|--------|------|
| UN-001: Clinician needs accurate temp reading | SRS-042: Temp accuracy ±0.3°C (35-42°C) | Sensor spec DS-T-01, Firmware SWR-189 | TC-TEMP-010, TC-TEMP-011 | PASS | RC-007 |
| UN-002: Device must alarm on fever | SRS-043: Fever alarm at ≥38.5°C within 5s | Alarm logic SWR-195 | TC-ALRM-012 | PASS | RC-008 |

### RTM Maintenance Rules
- RTM updated at every design review
- Any new or changed requirement immediately added with "OPEN" status
- No test result recorded as PASS if deviation was noted (must resolve deviation first)
- RTM formally reviewed at Design Review 3 (V&V Plan) and Design Review 4 (Transfer)
- Backward traceability: every test case traces to at least one requirement
- Forward traceability: every requirement has at least one test case

---

## 7. Design Transfer (§8.3.8)

Design transfer ensures the design can be consistently reproduced in manufacturing.

### Design Transfer Checklist
```
□ All DMR documents approved and released in PLM:
  ├─ Assembly drawings and instructions
  ├─ Component specifications and Approved Manufacturers List
  ├─ BOM at production revision
  ├─ Test specifications and acceptance criteria
  ├─ Labelling specifications and approved artwork
  └─ Packaging and shelf-life requirements

□ Manufacturing process capability verified:
  ├─ Process validation (IQ/OQ/PQ) completed for critical processes
  ├─ Equipment calibration records current
  └─ Operator training records complete

□ First article inspection completed:
  ├─ Dimensional inspection of all critical features
  └─ Functional test using production test procedures

□ Design transfer review completed and approved

□ Production authorisation granted by QA
```

---

## 8. Design Changes (§8.3.10)

### Change Control Process
```
Change Request (CR) raised
  ↓
Impact Assessment:
  ├─ Which requirements does this change affect?
  ├─ Which V&V tests are invalidated?
  ├─ Does this affect the risk management file?
  ├─ Does this affect regulatory approvals (510(k), CE mark)?
  └─ Does this affect the DHF, DMR, or labelling?
  ↓
Risk Assessment of the change itself:
  ├─ Does the change introduce new hazards?
  └─ Does the change affect residual risk acceptability?
  ↓
V&V Plan for the Change:
  ├─ Which tests must be re-executed?
  ├─ Are new tests required?
  └─ Is re-validation required?
  ↓
Implementation:
  ├─ Update affected documents
  ├─ Execute required V&V
  └─ Update risk file
  ↓
Change Order approved and closed in PLM
  ↓
DHF updated
```

### When Does a Design Change Require Re-Validation?
| Change Type | Typically Requires |
|-------------|-------------------|
| Change to intended use | Full re-validation |
| Change to user interface (controls, display) | Usability re-evaluation |
| Change to safety-critical function | Re-verification + risk file update |
| Material change (body contact) | Biocompatibility assessment |
| Software algorithm change | Software system re-test + risk review |
| Supplier change for critical component | Re-verification of affected performance |
| Manufacturing process change | Process re-validation |
