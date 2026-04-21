# CAN Log Analysis, Root-Cause Investigation & Defect Management

> **Role:** Cluster Lead — Marelli / LTTS Bangalore
> **Focus:** Trace analysis workflows, root-cause methodology, defect lifecycle,
>            tools (CANoe, Jira/Mantis/ALM), OEM reporting standards

---

## 1. CAN Log Analysis Workflow

### 1.1 Log File Types in CANoe/CANalyzer

| Format | Extension | Notes |
|---|---|---|
| Vector Binary Log | `.blf` | Timestamped binary — primary format. Very fast read/write. |
| ASCII Log | `.asc` | Human-readable, larger file size. Useful for grep/Python parsing. |
| MF4 (ASAM) | `.mf4` | Modern measurement format — supports all channels |
| Trace database | `.csv` | Exported from trace for Excel/Python analysis |
| Vector vMeas | `.vmes` | Measurement data with variable groups |

### 1.2 Systematic Trace Analysis Approach

```
STEP 1 — SCOPE
  Define the time window:
  - Note test start (KL15 ON) and test end timestamps
  - Narrow to ±2 seconds around the failure event

STEP 2 — FILTER
  Filter to relevant messages only:
  - E.g., Filter = 0x3B3 (Speed) + 0x316 (Engine) + 0x3A5 (ABS)
  - Remove heartbeat/keep-alive messages that clutter trace

STEP 3 — SIGNAL PLOT
  Use CANoe/CANalyzer Graphics window:
  - Plot VehicleSpeed, ABS_Fault, FuelLevel vs time
  - Look for: signal drop, unexpected spikes, missing cycles

STEP 4 — TIMING CHECK
  - Measure message cycle time: should be 10ms for speed, 100ms for fuel
  - A 200ms gap in a 10ms message = timeout (ECU or bus fault)
  - Use Bus Statistics panel: check load%, error rate, CRC errors

STEP 5 — CORRELATION
  - Correlate multiple signals: does ABS_Fault = 1 match ABS_Active = 0 at same time?
  - Cross-reference BCM ignition state with cluster behaviour
  - Timeline: when did signal arrive vs when did display change? Measure delta.

STEP 6 — ISOLATE
  - Does fault occur at the sender (source ECU not transmitting)?
  - Or at the receiver (cluster not processing signal correctly)?
  - Swap DBC signal decode — is the bit position correct?

STEP 7 — DOCUMENT
  - Capture screenshot with annotations in CANoe
  - Export filtered log as .asc for defect attachment
  - Note: timestamp, signal value, expected vs actual
```

---

## 2. Root-Cause Investigation — Framework

### 2.1 The 5-Why Method for Cluster Defects

```
DEFECT: Fuel gauge needle stuck at 'E' even when fuel level signal shows 80%

Why 1: Needle is not moving despite correct signal?
  → Cluster is not updating gauge from the received signal.

Why 2: Why is the cluster not updating?
  → Signal value 80 (raw) decoded with wrong factor.

Why 3: Why wrong factor?
  → DBC file used in CANoe has FuelLevel scaling: factor=1, offset=0
    Cluster firmware uses: factor=0.5, offset=0 (old version loaded in ECU)

Why 4: Why was old DBC loaded in ECU?
  → Software delivery received from ECU team was not tagged correctly.
    CI/CD release included an older .hex that was not rebuilt after DBC update.

Why 5: Why not caught in review?
  → DBC version not tracked in release checklist. No automated check.

ROOT CAUSE: Configuration management gap — DBC version not validated in CI/CD.
CORRECTIVE ACTION: Add DBC SHA-256 hash comparison step in build pipeline.
```

### 2.2 Fishbone (Ishikawa) for Cluster Defects

```
                   DEFECT: MIL does not extinguish after fault cleared
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
      SOFTWARE             SIGNAL/CAN           HARDWARE
    ─────────            ──────────           ──────────
  Latch logic bug      Signal not cleared    Backlight circuit
  Wrong DTC clear      DTC active in ECU     Fuse blown
  State machine fault  DBC decode error      Display damage
         │                    │                    │
      PROCESS              CONFIG               TOOLING
    ─────────            ──────────           ──────────
  Missing test case    Wrong variant loaded  Stale CANoe DBC
  Incomplete SRS       EOL not complete      Logger time drift
```

### 2.3 Root Cause Categories for Cluster

| Category | Example Root Cause |
|---|---|
| Signal issue | Signal scaling mismatch between DBC and cluster SW |
| Timing issue | Cluster debounce too long — doesn't react to 50ms fault pulse |
| DBC mismatch | Signal bit position wrong in DBC — adjacent signal decoded instead |
| SW bug | Cluster firmware state machine has stuck state |
| Configuration | Wrong software variant loaded for this vehicle region |
| Test environment | CAN interface not terminating bus correctly — 60Ω instead of 60Ω each end |
| NVM issue | Factory EOL not run — factory defaults persisted |

---

## 3. CAN Log Analysis with Python

```python
"""
can_log_analyzer.py
Parse a .asc log file and detect CAN timeout for VehicleSpeed 0x3B3
"""

import re
from collections import defaultdict

LOG_FILE     = "cluster_test_run.asc"
TARGET_ID    = 0x3B3           # VehicleSpeed message
TIMEOUT_MS   = 200.0           # Expected max cycle: 200ms before timeout alarm
CYCLE_EXPECT = 10.0            # Expected cycle: 10ms

def parse_asc_log(filepath: str) -> list:
    """Parse Vector .asc file and return message list"""
    messages = []
    pattern  = re.compile(
        r"(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]+)\s+[RT]\s+d\s+\d+\s+([\w\s]+)"
    )
    with open(filepath, "r") as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                messages.append({
                    "ts_ms"    : float(m.group(1)) * 1000.0,
                    "channel"  : int(m.group(2)),
                    "msg_id"   : int(m.group(3), 16),
                    "data_hex" : m.group(4).split()
                })
    return messages

def check_cycle_time_and_timeouts(messages: list, target_id: int,
                                  timeout_ms: float) -> dict:
    """Find gaps in message cycle time and report timeouts"""
    results = {"gaps": [], "min_cycle": float("inf"), "max_cycle": 0.0}
    last_ts  = None

    for msg in messages:
        if msg["msg_id"] != target_id:
            continue
        if last_ts is not None:
            delta = msg["ts_ms"] - last_ts
            results["min_cycle"] = min(results["min_cycle"], delta)
            results["max_cycle"] = max(results["max_cycle"], delta)
            if delta > timeout_ms:
                results["gaps"].append({
                    "start_ms" : last_ts,
                    "end_ms"   : msg["ts_ms"],
                    "gap_ms"   : delta
                })
        last_ts = msg["ts_ms"]
    return results

def decode_vehicle_speed(data_hex: list) -> float:
    """Decode VehicleSpeed: bytes [0:2], factor 0.01 km/h"""
    raw = (int(data_hex[1], 16) << 8) | int(data_hex[0], 16)
    return raw * 0.01

def analyze_speed_signal(messages: list):
    """Extract speed values and detect anomalies"""
    print(f"\n{'Timestamp_ms':>14} | {'Speed_kmh':>10} | {'Flag':>10}")
    print("-" * 40)
    for msg in messages:
        if msg["msg_id"] != TARGET_ID:
            continue
        speed = decode_vehicle_speed(msg["data_hex"])
        flag  = "SPIKE" if speed > 300.0 else ""
        print(f"{msg['ts_ms']:>14.1f} | {speed:>10.2f} | {flag:>10}")

def main():
    messages = parse_asc_log(LOG_FILE)
    print(f"Total messages parsed: {len(messages)}")

    results = check_cycle_time_and_timeouts(messages, TARGET_ID, TIMEOUT_MS)
    print(f"\n=== Cycle Analysis: 0x{TARGET_ID:X} (VehicleSpeed) ===")
    print(f"  Min cycle: {results['min_cycle']:.1f} ms")
    print(f"  Max cycle: {results['max_cycle']:.1f} ms")
    print(f"  Timeouts (>{TIMEOUT_MS}ms): {len(results['gaps'])}")
    for gap in results["gaps"]:
        print(f"    GAP: {gap['start_ms']:.1f} → {gap['end_ms']:.1f} ms "
              f"= {gap['gap_ms']:.1f} ms")

    analyze_speed_signal(messages)

if __name__ == "__main__":
    main()
```

---

## 4. Defect Management — Full Lifecycle

### 4.1 Defect Attributes (LTTS / OEM Reporting)

| Field | Description | Example |
|---|---|---|
| Defect ID | Unique identifier | CLU-1024 |
| Title | Clear one-line summary | `[IC][Speed] Speedometer reads 5 km/h high at 60 km/h input` |
| Severity | Impact on functionality | Critical / Major / Minor / Cosmetic |
| Priority | Fix urgency | P1 / P2 / P3 |
| Component | Subsystem | Cluster SW / Cluster HW / CAN DBC / Test Env |
| Status | Current state | New → Open → In-Analysis → Fixed → Verify → Closed |
| Found in build | Software baseline | IC_SW_v1.4.2_Build234 |
| Fixed in build | Resolution baseline | IC_SW_v1.4.3_Build246 |
| Test case | Linked test | TC_SPD_001_Accuracy_60kph |
| Root cause | Technical cause | DBC signal offset wrong in cluster variant B |
| Attachments | Evidence | CAN log .blf, screenshot, trace screenshot |
| OEM visibility | Customer-facing? | Yes / No |

### 4.2 Defect Severity Definition (Cluster Context)

| Severity | Definition | Example |
|---|---|---|
| Critical (S1) | Safety hazard or vehicle cannot operate | Speedometer reads 0 at 120 km/h, MIL not showing active engine fault |
| Major (S2) | Feature completely broken, no workaround | Odometer not incrementing, ABS telltale never activates |
| Minor (S3) | Feature partially wrong, workaround exists | Fuel gauge 5% off at half tank, trip meter resets 1km late |
| Cosmetic (S4) | Visual/UX issue, no functional impact | Backlight flickers once at startup, icon misaligned 2px |

### 4.3 Writing a Good Defect Report

```
DEFECT REPORT TEMPLATE
======================
Title: [IC][Telltale][ABS] ABS Fault telltale does not activate on ABS_Fault=1

Environment:
  - HW: Cluster bench A3, SW baseline IC_SW_v1.5.0_Build312
  - CANoe version: 16.0 SP4
  - DBC: Powertrain_v2.3.dbc

Steps to Reproduce:
  1. Set KL15 ON — wait for bulb check to complete
  2. Inject CAN message 0x3A5 with ABS_Fault bit = 1 (byte 0, bit 3)
  3. Observe cluster telltale area (top row, 4th from left)

Expected Result:
  ABS telltale (amber, triangle with ABS text) illuminates within 200ms
  per SRS requirement IC_REQ_0042 Rev C.

Actual Result:
  ABS telltale remains OFF. No change observed after 5 seconds.
  CAN trace shows message 0x3A5 transmitted correctly with ABS_Fault = 1.

Attachments:
  - cluster_abs_fail_20260421.blf (CAN log 10 seconds)
  - screenshot_abs_not_active.png
  - abs_trace.asc (filtered)

Root Cause (Initial Hypothesis):
  Possible DBC mismatch — ABS_Fault bit position may differ between
  test DBC and cluster ECU SW.

Severity: Major (S2)
Priority: P1 — Blocking ASIL B validation gate
```

### 4.4 Defect State Transitions

```
New
 └→ Open (assigned to SW/HW team)
     ├→ In-Analysis (team actively investigating)
     │   ├→ Cannot Reproduce (needs more info → back to Open)
     │   ├→ Not-a-Bug (as-per-design → WAD/Closed)
     │   └→ Fixed (fix implemented in new build)
     │       └→ Verify (tester re-runs TC on fixed build)
     │           ├→ Verified-Pass → Closed
     │           └→ Reopen (fix incomplete → back to Open)
     └→ Deferred (post release, low severity)
```

---

## 5. Defect Tools — Quick Reference

### 5.1 Jira (most common at LTTS)

```
Key operations for Cluster Lead:

1. Create defect:
   - Project: Cluster_IC
   - Issue Type: Bug
   - Priority: P1/P2/P3
   - Labels: [CAN] [CAPL] [Telltale] [Gauge] [NVM]
   - Link to Test Case in Xray/Zephyr plugin

2. Bulk triage:
   - Filter: Project=Cluster_IC AND Status=New AND Priority>=P2
   - Assign to engineers by component

3. Metrics dashboard:
   - Defect Open vs Closed chart
   - Severity distribution
   - Average resolution time per engineer
   - First-pass yield (defects found by team before OEM sees them)

4. Weekly status report from Jira:
   - Opened this week: X, Closed: Y, Open P1: Z
```

### 5.2 HP ALM / Micro Focus ALM (OEM-typical)

```
Used by OEMs like FCA, Renault (Marelli OEM partners):

Defect Module:
  - Created under test run → auto-linked to test case
  - Approval workflow: Engineer → Lead → OEM → Close

Test Execution Module:
  - Test sets map to test cycles (Sprint/Release)
  - Execution results: Passed / Failed / Blocked / N/A

Reports:
  - Test Execution Progress Report (auto from ALM)
  - Defect Aging Report (defects open > 14 days)
```

---

## 6. OEM Reporting & Communication

### 6.1 Weekly Status Report Template

```
PROJECT: Marelli IC Validation — Platform X
WEEK: WK17 2026 | Reporting Lead: [Your Name]

OVERALL STATUS: 🟡 AMBER (2 open P1 defects blocking ABS validation gate)

TEST EXECUTION:
  Total TCs: 320 | Executed: 280 (87.5%) | Passed: 261 | Failed: 15 | Blocked: 4

DEFECTS:
  Total Open: 19 | P1: 2 | P2: 9 | P3: 8
  New this week: 7 | Closed this week: 5
  Oldest open: CLU-1001 (18 days, awaiting SW fix from ECM team)

TOP RISKS:
  1. CLU-1024: ABS telltale not activating (P1, ASIL B gate) → SW fix ETA: WK18
  2. CLU-1031: Odometer NVM rollback on cold crank (P1) → Root cause in progress

COMPLETED THIS WEEK:
  ✓ Speedometer validation (TC_SPD_001 to TC_SPD_012): All Passed
  ✓ Fuel gauge sweep test: 11/12 Passed, 1 Minor defect (CLU-1041)
  ✓ Power mode sequence test: All 8 TCs Passed

PLAN NEXT WEEK:
  → Execute telltale matrix: TC_TEL_001 to TC_TEL_030
  → Retest CLU-1024 on new SW build v1.5.1
  → CAN timeout battery test (TC_CTO_001 to TC_CTO_015)
```

---

---

## 7. CAN Error Frame Analysis

### 7.1 Types of CAN Errors (ISO 11898)

| Error Type | Cause | How to See in CANoe |
|---|---|---|
| Bit Error | Node transmits a bit but reads back a different level | Error frame in Trace, red row |
| Stuff Error | 6+ consecutive same-polarity bits (stuffing violation) | Error frame, `StuffError` annotation |
| CRC Error | Receiver CRC mismatch | `CRCError` annotation in Trace |
| Form Error | Fixed-form field (EOF, ACK) has wrong bit level | `FormError` annotation |
| ACK Error | No node acknowledges the frame | `AckError` — only transmitter sees this |
| Bus-Off | Node error counter reaches 256 → taken off bus | No more TX from that node |
| Error Passive | Error counter 127 < n < 256 → node still active but passive | |

### 7.2 Reading Error Frames in CANoe Trace

```
In CANoe Trace window, error frames appear as red rows:

    09:14:22.3410  CAN 1  Error Frame  Bit Error, TxErrCnt=12, RxErrCnt=4
    09:14:22.3412  CAN 1  Error Frame  Stuff Error

Steps:
1. Filter trace to "CAN Errors" only (Filter → Error Frames)
2. Note timestamp — compare to last valid message before error
3. Note error counter values — rising TxErrCnt indicates transmitter fault
4. Check if errors are on one channel only (bus impedance problem)
   or both channels (ground fault or EMC event)
5. Correlate with signal plot — does speed signal disappear at exact error time?

Common cluster test causes:
  - CAN termination removed during test → reflection → Bit errors
  - Bench power supply voltage sag → ECU reboot → Bus-Off condition
  - Wrong baud rate in CANoe config → continuous error frames on all messages
```

### 7.3 Bus Load and Timing Analysis

```
CANoe Statistics Panel — key metrics:

Bus Load % = (frame_bits_per_second / 500000) × 100
  - Healthy: < 30% for HS-CAN 500kbps
  - Warning: 30–60%
  - Overloaded: > 60% → higher latency, more error frames

Cycle time analysis using CAPL:
```

```capl
/* Measure actual cycle time of VehicleSpeed message */
variables {
    double  last_ts_ms  = 0.0;
    double  cycle_time  = 0.0;
}

on message VehicleSpeed {
    double now = timeNow() / 1e5;  /* timeNow() returns 100ns units */
    if (last_ts_ms > 0.0) {
        cycle_time = now - last_ts_ms;
        if (cycle_time > 15.0 || cycle_time < 5.0) {
            write("TIMING VIOLATION: VehicleSpeed cycle %.2f ms (expected 10ms)", cycle_time);
        }
    }
    last_ts_ms = now;
}
```

---

## 8. Defect Writing — Deep Guide

### 8.1 Anatomy of a High-Quality Cluster Defect Report

```
DEFECT ID:   CLU-1024
TITLE:       [ABS] ABS fault telltale does NOT activate when ABS_Fault = 1

──────────────────────────────────────────────────────────────────
ENVIRONMENT:
  Cluster SW Build:   IC_SW_v1.4.2
  CANoe version:      17.0 SP3
  DBC version:        Powertrain_v2.3.dbc
  Test bench:         IC HIL Bench #3
  Date:               2026-04-20

──────────────────────────────────────────────────────────────────
PRECONDITION:
  1. Cluster powered on, KL15 = ON
  2. VehicleSpeed signal active at 0 km/h
  3. Bulb check completed — ABS telltale was visible during self-check

──────────────────────────────────────────────────────────────────
STEPS TO REPRODUCE:
  1. Open CANoe project IC_Validation_v2.3.cfg
  2. Start measurement
  3. In Panel, set KL15 = ON → confirm cluster wakes up
  4. Set ABS_Fault signal = 1 in message 0x3A5, Byte 0, Bit 0
  5. Wait 1000ms
  6. Observe cluster

──────────────────────────────────────────────────────────────────
EXPECTED RESULT:
  ABS telltale (amber, ISO 2575 symbol J.5.2) illuminates within 500ms
  of ABS_Fault = 1. Priority: P2 (ISO 2575).

ACTUAL RESULT:
  ABS telltale remains OFF. No change on cluster.
  VehicleSpeed display continues to update normally (CAN reception is OK).

──────────────────────────────────────────────────────────────────
ROOT CAUSE HYPOTHESIS:
  DBC signal ABS_Fault in Powertrain_v2.3.dbc is mapped to Byte 0 Bit 1.
  CAN log shows transmitted bit at Byte 0 Bit 0 (per test setup).
  Possible DBC mismatch — cluster firmware may expect Bit 1.

──────────────────────────────────────────────────────────────────
ATTACHMENTS:
  [ CLU-1024_trace.asc ]        — filtered CAN log showing 0x3A5 frames
  [ CLU-1024_panel_screenshot.png ] — cluster showing no ABS lamp
  [ CLU-1024_dbc_extract.txt ]  — ABS_Fault signal definition from DBC v2.2 vs v2.3

──────────────────────────────────────────────────────────────────
SEVERITY:     P1 — Safety / ASIL B gate blocker
ASSIGNED TO:  ABS ECU team (for DBC confirmation) + Cluster SW team
SRS REF:      IC_SRS_TEL_REQ_014 Rev C
```

### 8.2 Defect Severity Classification — Cluster-Specific

| Severity | Criteria | Cluster Examples |
|---|---|---|
| S1 / P1 | Safety-critical, ASIL gate blocker, OEM stop-ship | ABS telltale missing, SRS fault lamp absent, odometer rollback |
| S2 / P2 | Functional loss or OEM-visible quality issue | Speedometer error >5 km/h, MIL latches incorrectly, gear wrong |
| S3 / P3 | Cosmetic or minor functional deviation | Units wrong (L/100km vs MPG), DIS truncated text, backlight flicker |
| S4 / P4 | Suggestion / improvement | Font size slightly small, animation timing slightly off |

### 8.3 Defect Metrics — What a Cluster Lead Tracks

```
Weekly metrics dashboard (Jira filters):

1. Defect Discovery Rate (new per week):
   Healthy = < 5 new P1/P2 per week in late execution phase

2. Defect Closure Rate:
   Target: Closure rate ≥ Discovery rate (no growing backlog)

3. First-Pass Yield:
   FPY = (TCs passed on first execution) / (Total TCs executed)
   Target: > 85%

4. Defect Leakage:
   = Defects found by OEM AFTER LTTS sign-off / Total defects
   Target: < 5% leakage. Zero leakage for P1.

5. Mean Time To Close (MTTC) by severity:
   P1: < 7 days
   P2: < 14 days
   P3: < 30 days or deferred to next build

6. Age of Oldest Open P1:
   If > 7 days → escalate to PM with risk flag
```

---

## 9. Advanced Root-Cause Patterns

### 9.1 DBC Version Mismatch — The #1 Root Cause

```
Scenario: Signal suddenly decodes incorrectly after a new SW build

Detection:
  1. A signal that was working now shows wrong value
  2. Raw CAN data (hex bytes in trace) has not changed
  3. Conclusion: interpretation has changed → DBC mismatch

Investigation steps:
  Step 1: Export current DBC signal definition for suspect signal
  Step 2: Compare with previously used DBC (version in version control)
  Step 3: Key fields to compare:
          - Start bit position (most common change)
          - Factor and offset (scaling changes)
          - Signal length (bits)
          - Byte order (Intel vs Motorola)

  Example diff:
    v2.2: SG_ ABS_Fault : 0|1@1+ (1,0) — Bit 0 of Byte 0
    v2.3: SG_ ABS_Fault : 8|1@1+ (1,0) — Bit 0 of Byte 1
    → Signal moved from Byte 0 to Byte 1 → test setup injecting Byte 0 was wrong!

Prevention:
  - Always verify DBC version at test session start
  - Use DBC comparison script (see 05_python_automation.md section 4)
  - Freeze DBC at project milestone with git tag
```

### 9.2 Timing-Related Defects

```
Class: Signal present on bus but cluster display does not update in time

Examples:
  - Speedometer lags 1-2 seconds behind actual speed
  - Fuel gauge hesitates before updating
  - Gear indicator shows previous gear for 500ms after shift

Root cause investigation:
  1. Measure signal cycle time on bus (is ECU sending at correct rate?)
  2. Measure cluster response time (time between signal arrival and display change)
     In CANoe: use Measurement Setup → Graphics → overlay panel camera timestamp
  3. Check if cluster is applying a filter or averaging algorithm
     (Common: fuel gauge is filtered over 5s to avoid needle jitter)
  4. Check cluster SW requirement for display response time (typically < 200ms for speed)

Defect criteria:
  Response time > SRS requirement → valid defect
  Response time > SRS requirement but within OEM tolerance range → discuss with customer
```

---

## 10. Communication Templates

### 10.1 P1 Defect Escalation Email Template

```
Subject: [P1 URGENT] CLU-1024 ABS Telltale — Gateway Blocker — ACTION REQUIRED

Hi [ABS ECU Team Lead],

We have an S1 (P1) defect impacting the IC Gateway Review scheduled for [date].

DEFECT: CLU-1024 — ABS fault telltale not activating when ABS_Fault = 1
BUILD:  IC_SW_v1.4.2 + ABS_SW_v3.1.0
IMPACT: ASIL B gate blocker — cannot sign off cluster delivery with P1 open

ROOT CAUSE HYPOTHESIS:
ABS_Fault signal bit position mismatch between DBC v2.2 (test setup) and v2.3
(cluster ECU firmware). Awaiting ABS team confirmation on which DBC version governs.

ACTION NEEDED FROM YOUR TEAM:
  1. Confirm correct bit position for ABS_Fault in your current build
  2. Provide updated DBC if v2.3 is correct
  3. ETA for response: [required date] to meet build freeze

Log and DBC extract attached.

Regards,
[Your Name] | Cluster Validation Lead | LTTS Bangalore
```

---

*File: 03_can_log_analysis_defect_management.md | marelli_cluster_lead series*
