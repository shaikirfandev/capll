# Test Metrics and Reporting in Automotive Testing
## KPIs, Dashboards, and Evidence for ASPICE/ISO 26262

---

## 1. Why Test Metrics Matter

In automotive testing, metrics serve three purposes:
1. **Quality visibility** – show product and process health to stakeholders
2. **Process compliance** – demonstrate ASPICE/ISO 26262 conformance
3. **Risk management** – identify problem areas early and prioritize testing effort

---

## 2. Key Test Metrics

### 2.1 Test Execution Metrics

| Metric | Formula | Target |
|---|---|---|
| Test case pass rate | (Passed / Total) × 100 | > 95% at release |
| Test execution rate | (Executed / Planned) × 100 | 100% at release |
| Blocked test rate | (Blocked / Total) × 100 | < 2% |
| Test automation rate | (Automated / Total) × 100 | > 70% regression |

### 2.2 Defect Metrics

| Metric | Formula | Description |
|---|---|---|
| Defect density | Defects / KLOC | Defects per 1000 code lines |
| Defect arrival rate | Defects per week | Trend over time |
| Defect removal efficiency | (Dev defects found) / (Dev + post-release) | Target > 95% |
| Mean time to close (MTTC) | Sum(close_time - open_time) / count | Target < 5 days |
| Defect escape rate | Post-release defects / Total defects | Target < 5% |

### 2.3 Coverage Metrics

| Metric | Target (ASIL D) |
|---|---|
| Requirements coverage | 100% |
| Statement coverage | 100% |
| Branch coverage | 100% |
| MC/DC coverage | 100% |
| DTC trigger coverage | 100% |
| Boundary value coverage | 100% critical signals |

---

## 3. Test Report Structure (Standard Format)

A professional automotive test report includes:

```
Test Report – Engine Control Module v2.4.1
─────────────────────────────────────────
1. Summary
   - Test Scope
   - Test Environment (CANoe version, ECU HW/SW version, DBC version)
   - Execution Date/Period
   - Overall Verdict: PASS / FAIL / CONDITIONAL PASS

2. Test Results Overview
   - Total test cases: 450
   - Passed: 445 (98.9%)
   - Failed: 3 (0.7%)
   - Blocked: 2 (0.4%)
   - Not Executed: 0

3. Failed Test Cases
   ┌─────────────────────────────────────────────────────────────┐
   │ TC_ID    │ Test Case Name        │ Verdict │ Defect ID       │
   ├─────────────────────────────────────────────────────────────┤
   │ TC_042   │ Overspeed DTC Set     │ FAIL    │ BUG-1234        │
   │ TC_117   │ Cold Start RPM Limit  │ FAIL    │ BUG-1235        │
   │ TC_289   │ LIN Sensor Timeout    │ FAIL    │ BUG-1236        │
   └─────────────────────────────────────────────────────────────┘

4. Coverage Report
   - Requirements tested: 234/234 (100%)
   - MC/DC coverage: 99.2% (target: 100%)

5. Defect Summary
   - Open: 3 | Closed: 47 | Total found this release: 50

6. Test Environment Details
7. Attachments (BLF logs, CANoe .cfg, screenshots)
```

---

## 4. Defect Lifecycle (Bug Workflow)

```
New → Assigned → In Analysis → Fix → Verify → Closed
                     ↓                  ↓
                  Rejected           Reopen (if fix fails)
```

**Defect severity classification:**

| Severity | Description | Example |
|---|---|---|
| **S1 – Critical** | Safety impact, system crash, data loss | AEB doesn't activate |
| **S2 – Major** | Feature non-functional | Wrong gear displayed in cluster |
| **S3 – Moderate** | Feature degraded | RPM gauge slightly off-scale |
| **S4 – Minor** | Cosmetic, low impact | Incorrect unit label |

**Defect priority:**

| Priority | Fix Timeline |
|---|---|
| P1 – Critical | Fix within 24 hours |
| P2 – High | Fix in current sprint |
| P3 – Medium | Fix before release |
| P4 – Low | Fix in next release |

---

## 5. Metrics Tracking – Sample Dashboard

```
WEEKLY TEST METRICS DASHBOARD (Week 12, 2026)
═══════════════════════════════════════════════

MODULE: Engine Control Unit v2.4.1

┌─────────────────────────────────────────────────┐
│  EXECUTION SUMMARY                               │
│  Total Planned   : 450                           │
│  Executed        : 448 (99.6%)  ✅               │
│  Passed          : 445 (99.3%)  ✅               │
│  Failed          : 3  (0.7%)   ⚠️               │
│  Blocked         : 2  (0.4%)   ⚠️               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  DEFECT SUMMARY                                  │
│  New This Week   : 3                             │
│  Closed This Week: 7                             │
│  Open Total      : 3                             │
│  Oldest Open     : BUG-1234 (5 days)  ⚠️        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  COVERAGE                                        │
│  Requirements    : 100%  ✅                      │
│  Branch          : 98.5% ⚠️ (target 100%)       │
│  MC/DC           : 99.2% ⚠️ (target 100%)       │
└─────────────────────────────────────────────────┘

TREND:
  Pass Rate: W10=96% → W11=97.5% → W12=99.3% ↑
  Open Defects: W10=12 → W11=8 → W12=3 ↓ (trending good)
```

---

## 6. CANoe Test Report Fields

When running tests in vTESTstudio + CANoe, each test case produces:

| Field | Description |
|---|---|
| Test Case Name | Descriptive name |
| Test Case ID | Unique identifier (links to requirement) |
| Verdict | PASS / FAIL / ERROR / NONE |
| Start Time | Absolute timestamp |
| Duration | Execution time (ms) |
| Test Steps | Pass/Fail per individual step |
| Log Reference | BLF file offset or timestamp |
| Description | What was tested |
| Deviation | Description of failure (if FAIL) |

---

## 7. Reporting for ASPICE Compliance

**ASPICE SWE.4 (SW Unit Verification):**
- Evidence: Unit test reports showing branch/MC/DC coverage
- Tool: VectorCAST / LDRA coverage reports

**ASPICE SWE.5 (SW Integration Test):**
- Evidence: Integration test reports, interface test results
- Tool: CANoe test reports + traceability to SW requirements

**ASPICE SWE.6 (SW Qualification Test):**
- Evidence: System test reports showing requirements coverage
- Traceability: Test case → requirement → pass/fail

**ASPICE SYS.4/SYS.5 (System Test):**
- Evidence: Vehicle/HIL test reports, safety requirement verification
- Tool: CANoe, HIL test system reports

---

## 8. Test Metrics Calculation Examples

### Calculating Defect Density
```
Project A:
  Total lines of code: 50,000
  Defects found in testing: 25

Defect Density = 25 / 50 = 0.5 defects/KLOC

Industry average: 0.5–1.0 defects/KLOC for embedded automotive
ASIL D target: < 0.1 defects/KLOC
```

### Calculating Test Efficiency
```
System test found 45 defects
Customer found 5 defects post-release

Defect Removal Efficiency = 45 / (45 + 5) × 100 = 90%
Target: > 95%
```

---

## 9. Python – Test Metrics Aggregator

```python
from dataclasses import dataclass, field
from typing import List
from enum import Enum

class Verdict(Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_RUN = "NOT_RUN"

@dataclass
class TestResult:
    tc_id:   str
    name:    str
    verdict: Verdict
    duration_ms: float = 0.0
    defect_id: str = ""

@dataclass
class TestMetrics:
    results: List[TestResult] = field(default_factory=list)

    @property
    def total(self): return len(self.results)

    @property
    def passed(self): return sum(1 for r in self.results if r.verdict == Verdict.PASS)

    @property
    def failed(self): return sum(1 for r in self.results if r.verdict == Verdict.FAIL)

    @property
    def blocked(self): return sum(1 for r in self.results if r.verdict == Verdict.BLOCKED)

    @property
    def pass_rate(self):
        return (self.passed / self.total * 100) if self.total > 0 else 0.0

    def print_summary(self):
        print(f"{'='*40}")
        print(f"  TEST METRICS SUMMARY")
        print(f"{'='*40}")
        print(f"  Total   : {self.total}")
        print(f"  Passed  : {self.passed}")
        print(f"  Failed  : {self.failed}")
        print(f"  Blocked : {self.blocked}")
        print(f"  Pass Rate: {self.pass_rate:.1f}%")
        print(f"{'='*40}")
        if self.failed > 0:
            print("  FAILED TEST CASES:")
            for r in self.results:
                if r.verdict == Verdict.FAIL:
                    print(f"    - {r.tc_id}: {r.name} [{r.defect_id}]")

# Usage
metrics = TestMetrics()
metrics.results = [
    TestResult("TC_001", "Engine Start Nominal", Verdict.PASS),
    TestResult("TC_002", "Overspeed DTC", Verdict.FAIL, defect_id="BUG-1234"),
    TestResult("TC_003", "Cold Start RPM", Verdict.PASS),
    TestResult("TC_004", "LIN Timeout", Verdict.BLOCKED),
]
metrics.print_summary()
```

---

## 10. Common Interview Questions

**Q1: What metrics do you track on a daily/weekly basis?**
> Pass rate, new defects opened, defects closed, blocked tests, and requirements/coverage progress. For CI, I monitor build pass rate and regression delta per build.

**Q2: How do you report to management on test progress?**
> Weekly dashboard with: test execution status (% executed, pass rate), defect trend (new vs. closed), risk items (blocked tests, overdue defects), and coverage status vs. release criteria.

**Q3: What is a release entry/exit criterion?**
> Entry criteria define when to start testing (e.g., build stability, requirements baselined). Exit criteria define when testing is "done" (e.g., 100% requirements covered, 0 S1 open defects, > 98% pass rate, MC/DC coverage met).

**Q4: If pass rate drops from 98% to 90% after a new build, what do you do?**
> Investigate the delta — identify which test cases newly failed, check if it's a code regression or test environment issue, assign defects, communicate to dev team, and decide if the build is releasable.

**Q5: What is defect removal efficiency and what does it tell you?**
> DRE = (defects found in testing) / (total defects). A low DRE means defects are escaping to customers. For ASIL D systems, DRE should be > 99%.
