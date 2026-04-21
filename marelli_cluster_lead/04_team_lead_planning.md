# Team Leadership, Planning & Customer Communication — Cluster Lead

> **Role:** Cluster Lead — Marelli / LTTS Bangalore
> **Scope:** Task allocation, progress monitoring, team mentoring, OEM stakeholder management

---

## 1. Role of a Cluster Lead — Responsibilities Breakdown

```
Cluster Lead
├── Technical Authority
│   ├── Review test cases for correctness and coverage
│   ├── Define test strategy for each feature
│   ├── Resolve technical blockers (DBC issues, tool setup)
│   └── Own test architecture — reusable CAPL libraries, naming conventions
│
├── Team Management
│   ├── Assign tasks by skill and capacity
│   ├── Daily/weekly review of team outputs
│   ├── Identify risks early — blocked tasks, skill gaps
│   └── Mentor juniors on CAN, CAPL, cluster domain
│
├── Process & Quality
│   ├── Ensure test case review before execution
│   ├── Enforce defect reporting standards
│   ├── Maintain traceability: Requirement → Test Case → Execution → Defect
│   └── Own test closure sign-off before OEM delivery
│
└── Customer Interface
    ├── Weekly status to OEM/customer team
    ├── Defect triage calls with ECU owners
    ├── Manage customer expectations on open issues
    └── Present test results in OEM review gates
```

---

## 2. Task Allocation Framework

### 2.1 Skill Matrix — Map Engineers to Test Areas

```
SKILL MATRIX TEMPLATE (Rate: 1=Beginner, 2=Working, 3=Expert)

Engineer    | CAN/DBC | CAPL | UDS/Diag | Cluster HW | Python | Test Mgmt
------------|---------|------|----------|------------|--------|----------
Ravi K      |    3    |  3   |    2     |     3      |   2    |    2
Priya M     |    2    |  2   |    1     |     2      |   3    |    2
Suresh L    |    3    |  2   |    3     |     2      |   1    |    1
Anjali R    |    1    |  1   |    1     |     1      |   2    |    1  (fresher)
You (Lead)  |    3    |  3   |    3     |     3      |   3    |    3

ASSIGNMENT STRATEGY:
  Senior testers (Ravi, Suresh) → Safety telltales, NVM, ABS/SRS validation (ASIL B)
  Mid testers (Priya) → Gauge sweep tests, Python automation scripts
  Freshers (Anjali) → DIS/trip meter tests with senior pairing first 2 weeks
  Lead (You) → Test strategy, OEM communication, critical defect RCA, review
```

### 2.2 Sprint Planning — Weekly / Bi-Weekly

```
SPRINT PLANNING WORKSHEET — IC Validation Sprint 3 (WK17–WK18)

Team Capacity:
  - 4 engineers × 5 days × 6 effective hours = 120 person-hours
  - Lead: 2 days test execution + 3 days review/reporting

Sprint Goal:
  - Complete Telltale validation (TC_TEL_001 to TC_TEL_030)
  - Retest all P1 defects from Sprint 2
  - Start CAN Timeout tests (TC_CTO_001 to TC_CTO_010)

BACKLOG ITEM           | Owner  | Est(hrs) | Dependency
-----------------------|--------|----------|-------------------
TC_TEL_001-010 Execute | Ravi   |   12     | Bench SLA (Sprint 2)
TC_TEL_011-020 Execute | Suresh |   12     | ABS signal coverage done
TC_TEL_021-030 Execute | Priya  |    8     | None
Retest CLU-1024        | Ravi   |    3     | SW build v1.5.1 available
Retest CLU-1031        | Suresh |    3     | SW build v1.5.1 available
Python timeout script  | Priya  |    8     | None
TC_CTO_001-010 Review  | Lead   |    4     | Priya completes script
Daily defect triage    | Lead   |    5     | Daily 30min × 5 days = 2.5h each WK
Weekly OEM report      | Lead   |    4     | WK17 + WK18 = 2 reports
Total Est              |        |   59h    | Buffer: 61h remaining (45% buffer)
```

---

## 3. Test Case Review — Lead's Checklist

```
BEFORE EXECUTING ANY TEST CASE, LEAD CONFIRMS:

✓ COVERAGE
  - Does the TC trace to a requirement in the SRS? (requirement ID linked)
  - Are boundary conditions covered? (min/max/default/timeout)
  - Is negative test included? (invalid signal, wrong value)

✓ CLARITY
  - Steps are unambiguous — a different engineer can run without asking
  - Expected Result is specific and measurable (not "check fuel gauge moves")

✓ PREREQUISITE
  - Correct SW baseline stated
  - Bench configuration is defined (channel assignments, termination)
  - DBC version referenced

✓ CAPL SCRIPT
  - Script reviewed for CAPL correctness
  - Signal names match current DBC
  - Output message IDs are correct for current bus
  - No hardcoded timestamps that might fail on different builds

✓ TRACEABILITY
  - TC ID exists in test management tool (Jira/ALM)
  - TC linked to defect if retesting

REJECTION CRITERIA (send back for rework):
  ✗ No requirement trace
  ✗ Expected result says "as per SRS" without quoting the specific value
  ✗ Wrong DBC signal name used in CAPL
  ✗ Missing preconditions (e.g., doesn't state ignition must be ON)
```

---

## 4. Progress Monitoring — KPIs for Cluster Lead

### 4.1 Daily Tracking

```
DAILY STANDUP STRUCTURE (15 minutes):

Each engineer answers:
  1. "Yesterday I completed: [TC IDs or tasks]"
  2. "Today I plan: [TC IDs or tasks]"
  3. "My blocker is: [tool, bench, SW build, DBC, knowledge]"

Lead notes:
  - Update execution tracker immediately
  - If blocker: assign action with due time (not "sometime today" → "by 3pm")
  - Re-prioritise if any P1 defect needs retest by EOD
```

### 4.2 Execution Tracker (Spreadsheet / Jira Board)

```
IC_Validation_Tracker_WK17.xlsx

Column: TC_ID | Feature | Engineer | Status | Date Executed | Result | Defect_ID
---------------------------------------------------------------------------
TC_SPD_001 | Speed 60kph  | Ravi    | Done   | 2026-04-20   | Pass   | -
TC_SPD_002 | Speed 100kph | Ravi    | Done   | 2026-04-20   | Pass   | -
TC_SPD_003 | Speed 200kph | Priya   | Done   | 2026-04-21   | Fail   | CLU-1044
TC_TEL_001 | ABS Telltale | Suresh  | WIP    | 2026-04-21   | -      | -
TC_TEL_002 | SRS Telltale | Suresh  | TODO   | -            | -      | -

Metrics (auto-calculated):
  Executed: 37/320 (11.5%)
  Passed: 35 | Failed: 2 | Blocked: 0
  Execution rate: 12 TC/day → On track for WK20 completion
```

### 4.3 Key Metrics Tracked Weekly

| Metric | Target | How to Measure |
|---|---|---|
| Test Execution Rate | > 85% of planned TCs per sprint | Tracker sheet |
| First-Pass Yield | > 85% tests pass on first run | (Pass / Total Executed) × 100 |
| Defect Leakage | < 5% defects found by OEM not by team | Escaped defects / Total defects |
| P1 Defect Age | < 7 days average open time | Jira: Created → Fixed date |
| Retest Cycle Time | < 2 days from build delivery to retest | Jira timestamps |

---

## 5. Mentoring Junior Engineers — Training Plan

### 5.1 4-Week Onboarding Plan (New Cluster Engineer)

```
WEEK 1 — Domain Foundation
  Mon: Vehicle CAN architecture + DBC reading with CANalyzer
  Tue: Instrument cluster tour (physical bench walkthrough)
  Wed: Understand OEM SRS — read telltale requirements
  Thu: Observe senior engineer run 5 TCs — shadow session
  Fri: Run 3 simple TCs independently (gauge sweep) + review with lead

WEEK 2 — CAPL Fundamentals
  Mon: CAPL syntax: variables, timers, on message handlers
  Tue: Write first CAPL script: send message, observe in trace
  Wed: CAPL telltale injection script workshop
  Thu: Set up full CANoe environment with DBC + panel
  Fri: Mini-project: automate 3 telltale TCs with CAPL, demo to lead

WEEK 3 — Defect Management
  Mon: Defect lifecycle in Jira (create, update, close)
  Tue: Trace analysis technique — read through 2 real defect logs
  Wed: Root-cause 3 pre-canned lab exercises (prepared by lead)
  Thu: Write defect report for a seeded fault the lead injected
  Fri: Peer review session — each engineer reviews another's defect report

WEEK 4 — Execution Independence
  Mon–Fri: Execute 20 TCs independently from the backlog
           Lead reviews all outputs but does not assist unless blocked > 30 minutes
  Review: Lead gives structured feedback session Friday
```

---

## 6. Customer Stakeholder Management

### 6.1 Types of Stakeholders in a Cluster Project

```
OEM Customer (e.g., Renault, Honda, FCA):
  → Cares about: schedule, open P1 defects, whether product is ship-ready
  → Communication: Weekly status reports, gateway reviews
  → Tone: Professional, concise, factual

ECU Owners (ABS ECU team, BCM team, Engine ECU team):
  → Cares about: accurate defect description, reproduction steps, log files
  → Communication: Defect triage calls (bi-weekly or on-demand)
  → Tone: Technical, collaborative, not accusatory

Internal LTTS Management:
  → Cares about: Effort burn, risk flags, customer satisfaction score
  → Communication: Internal project updates, risk register
  → Tone: Metrics-driven, proactive on risks

System/Integration Lead:
  → Cares about: Interface completeness, DBC freeze dates, variant management
  → Communication: DBC review meetings, configuration change notifications
```

### 6.2 Escalation Matrix

```
LEVEL 1 — Team Level (< 2 days to resolve)
  Who: Cluster Lead ↔ ECU engineer
  How: Direct Teams/Slack message + defect comment
  When: Blocked task, environment issue, DBC query

LEVEL 2 — Project Manager (2–5 days unresolved)
  Who: LTTS Cluster Lead → LTTS PM → Customer-side PM
  How: Email + weekly status call agenda item
  When: P1 defect unresolved > 5 days, schedule risk

LEVEL 3 — Director / Customer Management (> 5 days or scope impact)
  Who: LTTS PM → LTTS Delivery Director → OEM Customer Lead
  How: Formal escalation note, risk register update
  When: Potential delivery miss, ASIL-related blocked gate
```

### 6.3 Defect Triage Call Agenda

```
OEM Defect Triage Call — Cluster IC | Duration: 45 min

1. New defects this week                          [10 min]
   - Walk through each new P1/P2: title, status, log evidence
   
2. P1 Status update                               [10 min]
   - CLU-1024: SW fix eta, build expected WK18 Mon
   - CLU-1031: Root cause confirmed, fix in progress

3. Defects pending OEM decision                   [10 min]
   - CLU-1002: "WAD or Defect?" — speedometer reads +3 km/h
                OEM to confirm if within their approved tolerance range

4. Closed defects                                  [5 min]
   - CLU-1018: Verified passed on build v1.5.0 → Closed

5. AOB / Risks                                    [10 min]
   - DBC freeze date: May 5 → request OEM confirms no more SRS changes
```

---

---

## 7. Test Strategy Document — Template for Cluster Lead

```
DOCUMENT: IC Validation Test Strategy
PROJECT:  Marelli Cluster — Platform X
VERSION:  1.0
AUTHOR:   [Your Name], Cluster Lead

1. SCOPE
   In scope:  Telltales, Gauges, NVM, Power Mode, CAN Timeout, DIS features
   Out scope: Radio, Navigation (handled by Infotainment team)

2. TEST APPROACH
   a) Functional testing: signal injection via CANoe CAPL
   b) Regression testing: automated CANoe test module run per build
   c) Exploratory testing: engineer-driven ad-hoc (planned 10% of effort)
   d) Defect-based retesting: full retest on fixed builds

3. ENTRY CRITERIA (to start execution)
   - Cluster SW build delivered with build note
   - DBC version frozen and verified against SW
   - Test bench operational (power supply, CANoe, CAN interface)
   - Test cases reviewed and approved by lead
   - Baseline regression: previous build's results available

4. EXIT CRITERIA (to sign off delivery)
   - All P1/P2 defects Closed/Verified
   - Test execution ≥ 95% (max 5% Blocked with documented reason)
   - First-pass yield within target (≥ 85%)
   - Traceability matrix complete: every SRS requirement has ≥ 1 TC
   - OEM sign-off on all open P3/P4 (accept as-is or deferral)

5. RISKS AND MITIGATIONS
   Risk 1: DBC freeze delayed → MITIGATION: Run with draft DBC, revalidate after freeze
   Risk 2: Bench availability → MITIGATION: Bench booking schedule, shared calendar
   Risk 3: Junior engineer CAPL skill gap → MITIGATION: Senior pairing for first 2 weeks

6. TEST ENVIRONMENT
   HW:    Cluster bench — 12V power supply, CANcaseXL, CAN HS 500kbps
   SW:    CANoe 17 SP3, DBC: Powertrain_v2.3.dbc, Body_v1.8.dbc
   Build: IC_SW_v1.5.x (updated per sprint)

7. TOOLS
   Test Management:   Jira + Zephyr plugin
   CAN interface:     Vector VN1630
   Bug Tracking:      Jira IC_CLUSTER project
   Reporting:         Python-generated Excel + CANoe XML HTML report
```

---

## 8. Test Case Review Checklist — Detailed

```
REVIEW CHECKLIST (Lead completes before approving each TC batch)

□ REQUIREMENT TRACEABILITY
  - Every TC has at least one SRS requirement reference
  - SRS reference is at correct revision (e.g. SRS Rev C, not Rev A)
  - No orphan tests (test with no requirement — adds effort without coverage value)

□ PRECONDITIONS
  - Preconditions are achievable on the test bench
  - Order of preconditions matches logical sequence (KL15 before signal injection)
  - Precondition does not assume test environment state from a previous TC

□ INPUTS AND EXPECTED VALUES
  - Input values are numeric, not vague ("send speed signal" → "set VehicleSpeed = 60.0 km/h")
  - Expected result quotes the SRS tolerance: "within ±3 km/h as per SRS_SPD_REQ_003"
  - Edge cases covered: 0 value, max value, boundary conditions

□ CAPL ALIGNMENT
  - CAPL script variable names match those in test case step
  - Timer values in CAPL match the wait times stated in TC steps
  - CAPL script compiles without error (run compile check before sprint start)

□ PASS/FAIL CRITERIA
  - Pass/fail is binary and measurable — not "looks correct"
  - Tolerance specified for analog checks
  - Binary telltale checks: ON or OFF — no "dimly lit" ambiguity

□ DEFECT LINKAGE
  - Failing TCs from previous builds have defect ID cross-reference
  - TC notes state "Blocked by CLU-XXXX" when not executable

Rejection trigger: Any TC with vague expected result or missing SRS ref is sent back.
```

---

## 9. Sprint Planning — Full Template

```
SPRINT:    Sprint 07
DURATION:  2 weeks (Mon 2026-04-20 → Fri 2026-05-01)
TEAM:      Ravi K, Priya M, Suresh L, Anjali R
GOAL:      Complete telltale matrix validation (TC_TEL_001–TC_TEL_060)
           Begin CAN timeout validation (TC_CTO_001–TC_CTO_015)

─────────────────────────────────────────────────────────────────────
CAPACITY CALCULATION:

Engineer     Days    Hours/day  Available  Planned Effort
──────────── ──────  ──────────  ─────────  ──────────────
Ravi K          10       6h       60h       55h  (5h meetings)
Priya M         10       6h       60h       55h
Suresh L         8       6h       48h       43h  (off 2 days)
Anjali R        10       4h       40h       35h  (fresher rate)
──────── ──────────────────────────────────────────────────
Total                            208h      188h usable

─────────────────────────────────────────────────────────────────────
BACKLOG SELECTION:

Story/Task                        Owner     Estimate  Priority
──────────────────────────────────────────────────────────────
TC_TEL_001–030 (safety telltales) Suresh L   20h       P1
TC_TEL_031–060 (info telltales)   Ravi K     20h       P2
TC_CTO_001–015 (CAN timeout)      Ravi K     15h       P1
Retest CLU-1024, CLU-1031         Suresh L    4h       P1
ABS CAPL script update            Priya M     8h       P2
DBC comparison run on v2.3        Priya M     3h       P2
Onboard Anjali: telltale TCs      Anjali R   30h       Normal
Sprint review prep + reporting    Lead        5h       Admin
──────────────────────────────────────────────────────────────
Total                                        105h  ← within 188h capacity

─────────────────────────────────────────────────────────────────────
DEPENDENCIES:
  - DBC v2.3 from ABS team — needed before TC_CTO start (ETA: Apr 22)
  - IC_SW_v1.5.1 build — needed for CLU-1024 retest (ETA: Apr 21)

RISKS:
  - If DBC delayed past Apr 24: TC_CTO pushed to Sprint 08 (notify PM)
```

---

## 10. Lead Behaviours — Do's and Don'ts in Day-to-Day

| Situation | DO | DON'T |
|---|---|---|
| Engineer raises a blocker in standup | "Thanks — I will take that action today. Who can unblock this?" | "Why didn't you raise this earlier?" (shaming) |
| OEM raises a defect dispute | Present evidence, quote SRS, ask for written OEM decision | Argue on the call without data |
| Fresher makes a mistake in defect report | Private correction, show example, have them redo it | Correct them publicly in a team meeting |
| Schedule is slipping | Inform PM with options and risk — do not hide | Wait until deadline to flag |
| Engineer's test case is rejected | Give written, specific feedback with a correct example | Reject without explanation |
| Two engineers disagree on expected result | Bring it to SRS — the requirement is the truth | Pick a side personally |
| P1 defect found 1 day before gateway | Escalate immediately, adjust test scope, inform OEM | Try to fix root cause yourself without escalating |

---

*File: 04_team_lead_planning.md | marelli_cluster_lead series*
