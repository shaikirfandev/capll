# ASPICE Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Automotive SPICE (Software Process Improvement and Capability dEtermination) is the **mandatory process framework** for automotive software development. Every Tier-1 (Bosch, Continental, ZF, Aptiv) and OEM requires ASPICE compliance. Senior engineers are expected to understand ASPICE levels (0–5), key process areas (SWE.1–6, MAN.3, SUP.8–10), and how they apply daily work. Questions are common at **KPIT, Tata Elxsi, LTTS, Continental, and ASPICE assessments**.

**Key areas:**
- ASPICE process model overview (VDA scope, INTACS)
- Process capability levels (0=incomplete to 5=optimising)
- Software Engineering processes: SWE.1–6
- System Engineering processes: SYS.1–5
- Quality and Support processes: SUP.1 (Documentation), SUP.8 (CM), SUP.9 (Problem Resolution), SUP.10 (Change Request)
- Management processes: MAN.3 (Project Management), MAN.5 (Risk Management)
- Work Products: trace from requirement to code to test result
- Typical ASPICE Level 2 vs Level 3 differences
- Gap analysis: how to improve from Level 2 to Level 3
- Daily application: review checklists, traceability matrices

---

## ASPICE OVERVIEW

---

### Q1. What is ASPICE? Explain the capability levels and why they matter.

**Short Answer:** Automotive SPICE is a process assessment framework derived from ISO 15504. It defines how well a company's software development processes are defined, managed, and continuously improved. Capability level 2 (Managed) is the minimum most OEMs require; Level 3 (Established) is preferred for complex ECU programs.

**Detailed Expert Answer:**

```
ASPICE Capability Levels:

Level 0 — INCOMPLETE
  Process: Not implemented, or doesn't achieve its purpose
  Evidence: No documented requirements, no test cases, ad hoc coding
  OEM view: Unacceptable — won't certify supplier

Level 1 — PERFORMED
  Process: Achieves its purpose (informally)
  Evidence: Software works, but process is individual-dependent
  Key attributes: PA 1.1 — Process performance
  Typical company: startup, small team, "hero-driven"
  OEM view: Better, but risky — depends on key persons

Level 2 — MANAGED
  Process: Planned, monitored, and adjusted
  Evidence: Plans (project plan, test plan), status tracking, reviews
  Key attributes:
    PA 2.1 — Performance management (goals, status, corrective actions)
    PA 2.2 — Work product management (baselines, configurations, reviews)
  Typical company: Established Tier-2 supplier
  OEM view: MINIMUM for most automotive programs
  Requires: Requirements documented, traced to tests, reviewed, baselined

Level 3 — ESTABLISHED
  Process: Tailored from a standard process
  Evidence: Organisational standard process + project tailoring guidelines
  Key attributes:
    PA 3.1 — Process definition (standard process defined for org)
    PA 3.2 — Process deployment (projects follow the standard process)
  Typical company: Bosch, Continental, Tier-1 suppliers
  OEM view: PREFERRED for complex ECUs (ADAS, powertrain)
  Requires: Defined process library, templates, entry/exit criteria

Level 4 — PREDICTABLE
  Process performance measured quantitatively
  Statistical process control — KPIs tracked, variation understood
  Key attributes:
    PA 4.1 — Process measurement
    PA 4.2 — Process control

Level 5 — OPTIMISING
  Continuous process improvement using data
  Root cause analysis of defects, experimentation
  Only top-tier OEMs and suppliers at full-vehicle system level
```

---

### Q2. Describe the Software Engineering processes SWE.1 through SWE.6.

**Expert Answer:**

```
ASPICE Software Engineering Processes:

SWE.1 — Software Requirements Analysis
  Purpose: Define software requirements derived from system requirements
  Key activities:
    - Derive SW requirements from SYS requirements
    - Classify requirements (functional, non-functional, safety, interface)
    - Analyse feasibility (can we implement this?)
    - Define SW requirements attributes (priority, status, source)
  Work products:
    - Software Requirements Specification (SRS)
    - Requirements traceability (SYS → SWE.1)
  Example: System says "ECU must recover from bus-off within 1s"
    SWE.1: "CAN driver shall attempt recovery every 200ms for max 5 attempts"
           "CanSM module shall increment bus-off counter and enter limp-home"

SWE.2 — Software Architecture Design
  Purpose: Define SW architecture and interfaces
  Key activities:
    - Define SW components (modules, layers)
    - Define interfaces between components (APIs, data flows)
    - Verify architecture against requirements
    - Identify safety-relevant components (ASIL decomposition)
  Work products:
    - Software Architecture Document (SAD)
    - Interface specifications (ARXML in AUTOSAR)
  Example: AUTOSAR BSW + application component diagram, port connections

SWE.3 — Software Detailed Design
  Purpose: Define internal design for each module
  Key activities:
    - Define algorithms, data structures, state machines
    - Design error handling, defensive coding patterns
    - Create pseudo-code / flowcharts for complex logic
  Work products:
    - Detailed Design Document (DDD)
    - Flowcharts, state machine diagrams

SWE.4 — Software Unit Verification
  Purpose: Verify software units (functions, modules) through reviews and tests
  Key activities:
    - Code reviews (against MISRA C, coding guidelines)
    - Unit tests (GoogleTest, Unity, CAPL unit testing)
    - Static analysis (cppcheck, PC-lint, Polyspace)
    - Coverage measurement (MC/DC coverage for ASIL-B+)
  Work products:
    - Code review records
    - Unit test specifications and results
    - Coverage reports (branch, MC/DC)

SWE.5 — Software Integration and Integration Testing
  Purpose: Integrate SW modules and verify integration
  Key activities:
    - Build complete firmware from components
    - Run integration tests (module-to-module API tests)
    - Verify interface compatibility
  Work products:
    - Integration test plan and results
    - Integration build reports

SWE.6 — Software Qualification Testing
  Purpose: Confirm SW meets all software requirements (SWE.1)
  Key activities:
    - Run qualification test suite against all SRS requirements
    - Produce traceability: SWE.1 requirement → test case → test result
    - On HIL bench (real ECU, real-time stimulation)
  Work products:
    - Software Qualification Test specification
    - Test execution results (PASS/FAIL per requirement)
    - Full traceability matrix

Mnemonic: SWE.1 = What? SWE.2 = How (architecture)?
           SWE.3 = How (detail)?  SWE.4 = Verify each piece
           SWE.5 = Integrate + test  SWE.6 = Prove the whole works
```

---

## TRACEABILITY

---

### Q3. What is bi-directional traceability? Show an example.

**Expert Answer:**

```
Bi-directional traceability means every requirement can be traced FORWARD
to its implementation and tests, AND every test can be traced BACKWARD
to a requirement.

Forward trace: Requirement → Design → Code → Test
Backward trace: Test → Code → Design → Requirement

Why it matters:
  Impact analysis: if requirement changes, find affected code + tests
  Completeness check: every requirement has a test (no gaps)
  Regression scope: identify which tests to run for a given code change

Example: CAN Bus-Off Recovery Requirement

Level     Item                    Reference
──────────────────────────────────────────────────────────────────
SYS.3     "ECU shall remain       SYS-REQ-0042
          functional after CAN
          bus-off within 1s"

SWE.1     "CanSM shall attempt    SW-REQ-0112
          bus-off recovery
          every 200ms, max 5
          attempts before
          limp-home mode"

SWE.2     CanSM component        ARCH-DOC-003 §4.2
          state machine:         Figure 4-7
          BUSOFF → RECOVERY
          → NORMAL or LIMPHOME

SWE.3     ComM_BusOff_Handler()  DDD-CAN-007
          state machine with
          200ms timer and
          retry counter

SWE.4     Unit test:             UT-CAN-0034
          test_busoff_recovery_  (GoogleTest, PASS)
          within_1s()

SWE.5     Integration test:      IT-COM-0087
          CAN controller + CanSM (HIL, PASS)
          bus-off injected

SWE.6     Qualification test:    QT-CAN-0019
          TC_BusOff_1s_Recovery  (CANoe, PASS)

Traceability Matrix (partial):
  SW-REQ-0112 → UT-CAN-0034 (PASS) → IT-COM-0087 (PASS) → QT-CAN-0019 (PASS)
  SYS-REQ-0042 → SW-REQ-0112 → QT-CAN-0019 → VERIFIED

Tools used:
  IBM DOORS / Polarion: requirements management, traceability links
  Jira + Xray: test management, requirements linked to test cases
  Excel (small projects): manual traceability matrix
  AUTOSAR toolchain: requirement → component → code auto-linking
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q4. Your project receives an ASPICE Level 1 assessment. Improvement plan to Level 2?

**Expert Answer:**

"Level 1 → Level 2 is the most common improvement journey. Here's the practical plan:

**Gap Analysis (what Level 2 needs that Level 1 lacks):**
```
PA 2.1 — Performance Management:
  ✗ No formal project plan (effort, schedule, milestones)
  ✗ No status tracking meetings (progress vs plan not measured)
  ✗ No corrective actions documented when behind plan
  Fix: Create project plan template, weekly status reports,
       issue tracker for deviations

PA 2.2 — Work Product Management:
  ✗ Requirements not baselined (anyone can change them)
  ✗ No review records (code reviews done verbally, no trace)
  ✗ No CM: code in shared folder, no version control, no baselines
  Fix: Implement Git (version control), requirements in DOORS/Jira,
       mandatory review checklist for every work product
```

**Concrete 90-Day Plan:**
```
Month 1 — Foundation:
  Week 1-2: Training for entire team on ASPICE L2 requirements
  Week 3:   Set up Git repository, branching policy, PR reviews
  Week 4:   Migrate requirements to DOORS or Jira (all must have ID, owner, status)

Month 2 — Process:
  Week 5-6: Create project plan template: WBS, milestones, effort
  Week 7:   Define review checklist: entry criteria, review questions, exit criteria
  Week 8:   Baseline current requirements in DOORS (version 1.0)

Month 3 — Evidence:
  Week 9-10:  Run first sprint with new process, collect review records
  Week 11:    First configuration audit: all WPs baselined, reviews recorded
  Week 12:    Internal mock ASPICE assessment — gaps identified and addressed
  
Target: ASPICE Level 2 assessment by end of month 4
```

**Key metrics to track (for PA 2.1):**
```python
# Example: Sprint velocity tracking for PA 2.1 evidence
metrics = {
    "sprint": 3,
    "planned_story_points": 40,
    "completed_story_points": 35,
    "deviation_pct": 12.5,
    "corrective_action": "2 requirements under-specified, re-estimated",
    "open_issues": 3,
    "closed_issues": 12
}
# These records are the ASPICE Level 2 evidence for PA 2.1
```

**Production Insight (KPIT, TATA Motors project):** Project scored Level 1 in assessment due to no configuration management and ad-hoc requirements. In 4 months: GitLab implemented, requirements moved to Jira with mandatory IDs, review records generated by GitLab MR approvals. Re-assessment: Level 2 achieved for SWE.1, SWE.4, SWE.6. SWE.2 and SWE.3 reached Level 2 by month 7 after architecture documents were reviewed and baselined."

---

## CHEAT SHEET — ASPICE

```
Capability Levels:
  0 = Incomplete (don't achieve purpose)
  1 = Performed (achieve purpose, ad-hoc)
  2 = Managed (planned + evidence + baselines)
  3 = Established (standardised process, org-wide)
  4 = Predictable (quantitative measurement)
  5 = Optimising (continuous improvement)

OEM minimum: Level 2 for most programs
OEM preferred: Level 3 for complex ECUs (ADAS, powertrain, gateway)

SWE process chain:
  SWE.1 → SW Requirements
  SWE.2 → SW Architecture
  SWE.3 → SW Detailed Design
  SWE.4 → Unit Verification (code review + unit test)
  SWE.5 → Integration + Integration Testing
  SWE.6 → SW Qualification Testing

Level 2 evidence requirements:
  PA 2.1 (Performance Management):
    - Project plan with goals, schedule, milestones
    - Status tracking records
    - Corrective action records
  PA 2.2 (Work Product Management):
    - All WPs under version control (Git)
    - Review records for every WP
    - Baselines at milestones

Key support processes:
  SUP.8 — Configuration Management: CM plan, version control, baselines
  SUP.9 — Problem Resolution Management: defect tracking (Jira)
  SUP.10 — Change Request Management: formal CR process
  MAN.3 — Project Management: plans, estimates, monitoring

Traceability chain (must be complete):
  SYS requirement → SW requirement → architecture → code → unit test → 
  integration test → qualification test → test result
  
  Forward: trace from requirement to test result
  Backward: trace from test result to originating requirement
  
Tools:
  Requirements: IBM DOORS, Polarion, Jira + Xray
  Code: Git (GitLab/GitHub/Bitbucket), AUTOSAR toolchain
  Tests: vTESTstudio, Jenkins (automated), Jira Xray (results)
```
