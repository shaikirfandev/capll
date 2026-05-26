# SECTION 14 — JIRA & ISSUE MANAGEMENT
## Defect Lifecycle, RCA, Sprint Planning for Automotive Projects

---

## 14.1 JIRA IN AUTOMOTIVE DEVELOPMENT

### 14.1.1 Project Structure

```
JIRA PROJECT HIERARCHY FOR EV POWERTRAIN:
══════════════════════════════════════════════════════════════

Jira Project: EVPT (EV Powertrain)
  │
  ├── Epics (major features / system areas):
  │     EVPT-E001: BMS Core Functionality
  │     EVPT-E002: Charging System
  │     EVPT-E003: Inverter / Motor Control
  │     EVPT-E004: Diagnostic Framework (UDS)
  │     EVPT-E005: Functional Safety Compliance
  │     EVPT-E006: Software Integration Testing
  │
  ├── Stories (user/system stories per epic):
  │     EVPT-S001: BMS sends SoC on CAN bus at 10ms
  │     EVPT-S002: BMS detects cell overvoltage within 100ms
  │     EVPT-S003: OBC controls charge current from VCU command
  │
  ├── Tasks (technical implementation tasks):
  │     EVPT-T001: Implement BMS CAN driver
  │     EVPT-T002: Write BMS overvoltage detection function
  │     EVPT-T003: Create CAPL BMS simulation test node
  │
  └── Bugs (defects found during testing):
        EVPT-B001: BMS_SoC value incorrect at -10°C
        EVPT-B002: OBC does not respond to VCU_ChargeEnable on first try
        EVPT-B003: P0A80 DTC incorrectly set at high SoC during regen
```

### 14.1.2 Custom Fields for Automotive Bug Reports

```
AUTOMOTIVE-SPECIFIC JIRA FIELDS:
──────────────────────────────────────────────────────────────
Field               │ Type    │ Description
────────────────────┼─────────┼───────────────────────────────
Affected ECU        │ Select  │ BMS / VCU / MCU / OBC / DCDC / PDU
Vehicle Build Level │ Text    │ e.g., SOP-2, EP1, FP1, PTR
SW Version          │ Text    │ e.g., BMS_SW_1.2.3
HW Version          │ Text    │ e.g., BMS_HW_B2
Test Level          │ Select  │ SWUnit / SIT / HIL / Vehicle
CAN Signal          │ Text    │ Affected signal (e.g., BMS_SoC)
DTC Code            │ Text    │ ISO DTC (e.g., P0A80)
Reproducibility     │ Select  │ Always / Intermittent / Once
Temperature         │ Number  │ Ambient temperature at fault
Odometer            │ Number  │ Vehicle km at fault time
ASIL Impact         │ Select  │ QM / A / B / C / D (safety impact)
RCA Category        │ Select  │ SW Design / HW Design / Spec / Test Gap
Supplier Bug?       │ Boolean │ Tracked separately if supplier issue
```

---

## 14.2 DEFECT LIFECYCLE

```
DEFECT STATUS WORKFLOW:
══════════════════════════════════════════════════════════════

[OPEN]
  ↓ Triage (lead engineer reviews)
[ASSIGNED]
  ↓ Engineer picks up
[IN PROGRESS]  
  ↓ Fix developed
[IN REVIEW]
  ↓ Code review + peer check
[FIXED]
  ↓ Fix deployed to test environment
[IN TEST]
  ↓ Test engineer re-runs test case
  │
  ├── Test PASS → [CLOSED] ✓
  └── Test FAIL → [REOPEN] → back to [IN PROGRESS]

SPECIAL STATES:
[DUPLICATE]    — Same bug as existing JIRA
[WONT FIX]     — Accepted limitation, business decision
[CANNOT REPRO] — Cannot reproduce after investigation
[DEFERRED]     — Not blocking, pushed to next release

RESOLUTION TYPES:
  Fixed          — Code/config change made
  Won't Fix      — Known limitation, risk accepted
  Duplicate      — Merged with another JIRA
  By Design      — Behavior is correct per spec
  Cannot Repro   — Cannot reproduce after investigation
  Data Required  — Need more debug data from field
```

---

## 14.3 COMPLETE BUG REPORT EXAMPLES

### Example 1 — High Severity Field Bug

```
JIRA ID:     EVPT-B0847
TITLE:       BMS_Status CAN message has 65ms period spike causing VCU timeout DTC
PROJECT:     EV Powertrain (EVPT)
SEVERITY:    CRITICAL (S1)
PRIORITY:    P1 — Fix within current sprint
ASSIGNED TO: Rajan Kumar (BMS SW Lead)
STATUS:      IN PROGRESS

SUMMARY:
  During highway driving at 120 km/h, VCU generates DTC P1A00 
  (BMS Communication Timeout) intermittently. Frequency: ~1 per 6 seconds.
  Affects 3 pilot production vehicles (VINs: WDB001, WDB003, WDB007).

AFFECTED COMPONENTS:
  ECU:       BMS (Battery Management System)
  SW Version: BMS_SW_1.2.0
  HW Version: BMS_HW_B2
  Signal:    BMS_Status (CAN ID 0x310)

ENVIRONMENT:
  Vehicle:     EP1 pre-production, all 50 vehicles affected
  Temperature: 15-25°C
  Reproducibility: Always (every 6 seconds, precisely)

STEPS TO REPRODUCE:
  1. Power up vehicle, KL15 on
  2. Enter READY state
  3. Monitor BMS_Status (0x310) in CANoe trace
  4. Observe period spike to 65ms every 6 seconds

ACTUAL RESULT:
  BMS_Status period: normally 10ms ± 1ms
  Every ~6 seconds: one message period = 65ms
  VCU timeout threshold: 50ms → DTC P1A00 triggered

EXPECTED RESULT:
  BMS_Status period must be 10ms ± 2ms continuously
  No period spikes > 15ms under any conditions

ROOT CAUSE ANALYSIS:
  BMS performs NVM write every 6 seconds (SoC persistence)
  NVM write on external EEPROM takes 50ms (blocking I2C write)
  NVM write runs in same RTOS task as CAN transmission
  → CAN TX delayed by 50ms during NVM write
  
  Evidence: Added debug log to BMS. Log shows:
    "NVM_Write_Start" at 00:01.020
    "NVM_Write_End"   at 00:01.070 (+50ms)
    "CAN_TX_BMS_Status" at 00:01.070 (delayed by 50ms from scheduled 00:01.020)

PROPOSED FIX:
  Option A: Move NVM write to dedicated low-priority background task (RTOS)
  Option B: Split NVM write into 5×10ms segments to avoid blocking

RISK ASSESSMENT:
  ASIL impact: ASIL-B (VCU loses BMS visibility → potential wrong commands)
  Safety mitigation: VCU currently commands 0 torque on BMS timeout → SAFE
  Customer impact: Warning light in cluster, requires restart
  
  Fix complexity: MEDIUM (2-3 days including testing)
  Fix risk: LOW (well-understood RTOS mechanism)

VERIFICATION PLAN:
  1. Unit test: NVM write timing on BMS standalone
  2. Integration test: CANoe timing measurement, 30-minute soak
  3. Verify max period spike < 12ms after fix
  4. Re-run on all 50 EP1 vehicles

ATTACHMENTS:
  [CANoe_trace_BMS_period_spike.blf]
  [BMS_debug_log_20231115.txt]

JIRA LINKS:
  Blocks: EVPT-T1050 (Release Gate EP1 Testing)
  
HISTORY:
  2023-11-15: Bug filed by Test Lead (Priya Sharma)
  2023-11-16: Root cause identified — BMS team
  2023-11-17: Assigned to Rajan Kumar
  Target close: 2023-11-20
```

### Example 2 — Medium Severity Intermittent Bug

```
JIRA ID:     EVPT-B0892
TITLE:       P0A80 DTC incorrectly set at 96% SoC during regen braking at -8°C
PROJECT:     EV Powertrain (EVPT)
SEVERITY:    HIGH (S2)
PRIORITY:    P2

SUMMARY:
  BMS sets P0A80 (SoH Degraded) DTC intermittently in cold weather.
  All occurrences at temperature < -5°C.
  0 occurrences at temperature > 10°C.
  DTC only pendingDTC — never confirmed.

AFFECTED COMPONENTS:
  ECU:       BMS
  SW Version: BMS_SW_1.2.0
  Signal:    BMS_SoH (DID 0xF121)

ENVIRONMENT:
  Temperature: -8°C ambient
  SoC: 60-70% range
  Driving: Regen braking events

DTC EXTENDED DATA:
  DTC 0x0A8000 (P0A80) occurrence counter: 47 times
  Last occurrence conditions: T=-8°C, SoC=65%

ANALYSIS:
  SoH calculation performs capacity measurement via controlled discharge
  At -8°C: cell internal resistance 3× higher than at 25°C
  Voltage sag causes BMS to think capacity is exhausted prematurely
  BMS calculates SoH = 76% (false low) instead of actual 96%
  
  Root cause: SoH measurement algorithm lacks temperature compensation
  Fix: Gate SoH measurement to T ≥ 15°C only

VERIFICATION:
  Temperature chamber test at -30°C to +25°C
  No P0A80 at cold temperatures after fix
  
STATUS: IN PROGRESS → Fix: BMS_SW_1.2.1
```

---

## 14.4 SPRINT PLANNING FOR EV TEST TEAM

```
SPRINT STRUCTURE FOR EV POWERTRAIN VALIDATION:

SPRINT 12 PLANNING (2 weeks):
════════════════════════════════════════════════════════════

Sprint Goal: Complete HIL validation of BMS fault handling (ASIL-C/D tests)

VELOCITY: Team capacity = 80 story points (5 engineers × 2 weeks)

USER STORIES:
──────────────────────────────────────────────────────────────
EVPT-S156 │ BMS fault detection tests    │ 8 pts  │ In Sprint
EVPT-S157 │ BMS recovery after fault     │ 5 pts  │ In Sprint
EVPT-S158 │ OBC CC/CV charging test      │ 13 pts │ In Sprint
EVPT-S159 │ UDS DTC validation suite     │ 13 pts │ In Sprint
EVPT-S160 │ ISO 15118 handshake test     │ 21 pts │ In Sprint
EVPT-S161 │ Charging cold weather -20°C  │ 8 pts  │ In Sprint
EVPT-S162 │ Regression: BMS CAN messages │ 5 pts  │ In Sprint
──────────────────────────────────────────────────────────────
TOTAL:     73 pts (within 80 pt capacity)

BUG FIXES IN SPRINT:
EVPT-B0847 │ BMS NVM blocking CAN          │ P1 │ Must fix
EVPT-B0892 │ P0A80 false DTC cold weather  │ P2 │ Should fix

SPRINT REVIEW CRITERIA:
  ✓ All S1/S2 bugs resolved
  ✓ BMS fault test suite: 100% executed, ≥ 95% pass
  ✓ ISO 15118 test: 100% executed
  ✓ Test report delivered to systems engineering
```

---

## 14.5 ROOT CAUSE ANALYSIS PROCESS

```
RCA TEMPLATE (5-WHY ANALYSIS):
══════════════════════════════════════════════════════════════

JIRA: EVPT-B0847 — BMS period spike

PROBLEM STATEMENT:
  BMS_Status CAN message has 65ms period spike causing VCU timeout DTC

5-WHY ANALYSIS:
  Why 1: Why did the VCU timeout DTC trigger?
          → BMS message missing for 65ms (threshold 50ms)

  Why 2: Why was BMS message delayed for 65ms?
          → BMS CAN task was blocked for 50ms

  Why 3: Why was BMS CAN task blocked?
          → NVM write (50ms blocking) runs in same task as CAN TX

  Why 4: Why does NVM write run in CAN task?
          → BMS SW architect put NVM write in 10ms cyclic task
             (triggered every 600 cycles = 6 seconds)

  Why 5: Why did the architect not use a background task?
          → BMS RTOS design did not specify separate priorities
             for CAN tasks vs. background storage tasks
             → PROCESS GAP: No architectural review for RTOS task priority

ROOT CAUSE: Process gap in RTOS task architecture review
  Immediate: Blocking NVM write in high-priority CAN task
  Systemic:  No review process for task timing impact

CORRECTIVE ACTIONS:
  Immediate (EVPT-B0847): Move NVM write to background task
  Systemic:  Add RTOS task timing review to architecture checklist
             Add CAN period verification to CI/CD test suite

VERIFICATION:
  EVPT-B0847 fix verified by 30-minute soak test in CANoe
  Checklist updated: EVP_SW_Architecture_Checklist_v1.3
```

---

## 14.6 RELEASE GATE CRITERIA

```
RELEASE GATE — EP1 (Engineering Pilot 1):
══════════════════════════════════════════════════════════════

GATE CRITERIA:
────────────────────────────────────────────────────────────────────
Category          │ Criteria                    │ Status
──────────────────┼─────────────────────────────┼────────────────
ASIL-D Tests      │ 100% executed, 100% PASS     │ ✓ / ✗
ASIL-C Tests      │ 100% executed, ≥ 99% PASS    │ ✓ / ✗
Critical S1 Bugs  │ 0 open S1 bugs              │ ✓ / ✗
High S2 Bugs      │ 0 open P1 S2 bugs           │ ✓ / ✗
DTC Coverage      │ All DTC codes verified       │ ✓ / ✗
Charging Tests    │ AC + DC charging validated   │ ✓ / ✗
Cold Start        │ -20°C start test passed      │ ✓ / ✗
Bus Load          │ All buses < 60% load         │ ✓ / ✗
Quiescent Current │ < 5mA (10-minute soak)       │ ✓ / ✗
ISO 26262 Review  │ Safety review signed off     │ ✓ / ✗
Cybersecurity     │ TARA reviewed, no CAL-4 open │ ✓ / ✗
OTA Test          │ OTA update verified          │ ✓ / ✗
────────────────────────────────────────────────────────────────────

GATE APPROVERS:
  SW Lead: ______  (signature)
  HW Lead: ______
  Systems Eng: ______
  Safety Manager: ______
  
  Gate opens when ALL criteria = ✓ AND all approvers signed.
```

---

## 14.7 SUPPLIER BUG TRACKING

```
SUPPLIER DEFECT REPORT TEMPLATE:
══════════════════════════════════════════════════════════════

SDR-2023-0156 — To: BMS_Supplier_Corp

VEHICLE/PROJECT: EV-Platform-1
DATE: 2023-11-20
SEVERITY: S1 (Safety Critical)
AFFECTED SW: BMS_SW_1.2.0

DEFECT DESCRIPTION:
  BMS_Status CAN message has 65ms period spike (expected ≤ 12ms)
  Root cause confirmed: blocking NVM write in CAN task

REQUIRED ACTION:
  Fix by: 2023-11-25 (5 business days)
  Fix verification method: CANoe 30-minute soak, max period < 12ms
  Deliverable: BMS_SW_1.2.1 + fix description document

EVIDENCE ATTACHED:
  - CANoe trace file showing period spike
  - Root cause analysis document (RCA_EVPT-B0847.pdf)

SUPPLIER RESPONSE DUE:
  Acknowledgment: Within 24 hours
  Root cause confirmation: Within 72 hours
  Fix delivery: Within 5 business days

ESCALATION PATH:
  Day 5 no fix: Escalate to Supplier Program Manager
  Day 10 no fix: Escalate to OEM Procurement + Engineering VP
```

---

## SECTION 14 SUMMARY

| Topic | Key Point |
|-------|-----------|
| Jira structure | Epics → Stories → Tasks → Bugs with automotive custom fields |
| Bug severity | S1=Critical/Safety, S2=High, S3=Medium, S4=Low |
| Defect lifecycle | OPEN → ASSIGNED → IN PROGRESS → FIXED → IN TEST → CLOSED |
| RCA | 5-Why analysis, immediate + systemic corrective actions |
| Sprint planning | Story points, velocity-based planning, P1 bugs in sprint |
| Release gates | 12 criteria checklist, multi-stakeholder sign-off |
| Supplier tracking | SDR (Supplier Defect Report) with formal response deadlines |

Tools: JIRA (defect tracking), Confluence (documentation), GitLab/GitHub (code reviews), TestRail or Jira Zephyr (test case management)

---

*Next: Section 15 — Interview Preparation Q&A*
