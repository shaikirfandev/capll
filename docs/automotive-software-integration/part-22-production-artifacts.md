# Part 22 — Production-Ready Artifacts & Templates

---

## 22.1 Software Integration Plan Template

```
PROJECT: [Project Name]
ECU: [ECU Name]
VERSION: [Plan Version]
DATE: [Date]
AUTHOR: [Author]

1. SCOPE
   - ECUs in scope: [list]
   - Networks in scope: [CAN, CAN FD, Ethernet]
   - Features in scope: [AEB, ACC, LKA...]

2. INTEGRATION ENVIRONMENTS
   - Phase 1: ECU bench (weeks 1-4)
   - Phase 2: Network bench / HIL (weeks 5-10)
   - Phase 3: Vehicle integration (weeks 11-16)

3. ENTRY/EXIT CRITERIA
   Phase 1 Entry: unit tests passed, build green
   Phase 1 Exit: ECU boots, basic CAN signals verified
   Phase 2 Entry: Phase 1 exit criteria met
   Phase 2 Exit: all HIL test cases pass (>98%), no P1 open
   Phase 3 Entry: Phase 2 exit criteria met
   Phase 3 Exit: all vehicle test cases pass, validation sign-off

4. RESOURCES
   - Integration engineers: [names, responsibilities]
   - HIL system: [identifier]
   - Vehicles: [vehicle IDs]

5. RISKS
   | Risk | Probability | Impact | Mitigation |
   |------|-------------|--------|------------|
   | Supplier delay | Medium | High | Early SW delivery milestones |

6. INTEGRATION BASELINE SCHEDULE
   | Baseline | Date | SW Versions |
   |----------|------|-------------|
   | B_W10 | 2025-03-07 | v1.0.0 all ECUs |
```

---

## 22.2 ECU Integration Checklist

```
ECU: _______________  SW Version: _______________  Date: _______________

HARDWARE
[ ] ECU hardware on bench, power supply verified
[ ] Debug interface (JTAG) connected
[ ] CAN/Ethernet connections verified

SOFTWARE BRING-UP
[ ] Firmware flashed successfully
[ ] ECU boots without reset loops
[ ] No unexpected DTCs at startup
[ ] Watchdog alive (no unexpected resets in 1 hour)

COMMUNICATION
[ ] All expected CAN messages transmitting at correct period
[ ] All received CAN signals decoded correctly
[ ] Ethernet SOME/IP services offered and subscribed
[ ] DoIP routing working

DIAGNOSTICS
[ ] All DIDs readable via 0x22
[ ] Security access (0x27) seed/key verified
[ ] Fault injection: DTC set and cleared correctly
[ ] Flashing via programming session verified

FUNCTIONAL
[ ] [Feature 1]: verified end-to-end
[ ] [Feature 2]: verified end-to-end
[ ] [Feature N]: verified end-to-end

SIGN-OFF
Integration Engineer: _______________  Date: _______________
```

---

## 22.3 CAN Signal Matrix (Communication Matrix)

| Signal Name | Source ECU | Consumer ECU | Message ID | Byte | Bit | Length | Factor | Offset | Unit | Period |
|---|---|---|---|---|---|---|---|---|---|---|
| VehicleSpeed | ABS_ECU | Cluster, TCU, ADAS | 0x0C9 | 0-1 | 0 | 16 | 0.25 | 0 | km/h | 10ms |
| EngineRPM | Engine_ECU | Cluster, TCU | 0x0C8 | 0-1 | 0 | 16 | 0.25 | 0 | rpm | 10ms |
| BrakePressure | Brake_ECU | ADAS | 0x0D0 | 0-1 | 0 | 12 | 0.1 | 0 | bar | 5ms |
| GearPosition | TCM_ECU | Cluster, IVI | 0x0DF | 0 | 0 | 4 | 1 | 0 | enum | 20ms |
| DoorStatus | Body_ECU | Cluster | 0x395 | 0 | 0 | 8 | 1 | 0 | bitmask | 100ms |

---

## 22.4 Diagnostic Matrix

| DTC | DTC ID | Trigger Condition | Debounce | Lamp | Priority |
|---|---|---|---|---|---|
| Sensor_Camera_Failure | P0A00 | CameraSignal absent > 150ms | 3 cycles | Amber | P1 |
| CAN_Timeout | U0100 | No CAN msg from Engine > 500ms | Immediate | Red | P0 |
| NvM_Write_Failure | B0001 | NvM write returns error | 1 cycle | None | P3 |

---

## 22.5 Release Checklist

```
RELEASE: [SW version]   DATE: [date]   ECU: [ECU name]

PRE-RELEASE
[ ] All P1/P2 defects closed
[ ] HIL regression: ___ / ___ test cases passed
[ ] Vehicle test sign-off: YES / NO
[ ] Static analysis: no mandatory violations open
[ ] Binary CRC verified: [CRC value]

RELEASE PACKAGE CONTENTS
[ ] firmware.hex (SHA256: _______________)
[ ] firmware.elf (SHA256: _______________)
[ ] calibration.a2l
[ ] release_notes.pdf
[ ] test_report.pdf
[ ] build_manifest.json

APPROVALS
Integration Lead:   _______________  Date: ___
Validation Lead:    _______________  Date: ___
Safety Manager:     _______________  Date: ___
Project Manager:    _______________  Date: ___
```

---

## 22.6 Root Cause Analysis Template

```
DEFECT ID: [Jira ID]
TITLE: [Short description]
DATE FOUND: / DATE CLOSED:

DEFECT DESCRIPTION:
[Symptom, environment, reproduction steps]

ROOT CAUSE:
[Technical root cause — be specific about the code/config/data issue]

CONTRIBUTING FACTORS:
[Process gaps, missing tests, ambiguous requirements]

FIX DESCRIPTION:
[What was changed, file/function, change description]

VERIFICATION:
[How fix was verified — test case, CANoe trace, logs]

PREVENTIVE ACTIONS:
[ ] Add regression test case TC-XXX to prevent recurrence
[ ] Update DBC review checklist to verify byte order
[ ] Update integration checklist: verify CAN timing before ECU integration

LESSONS LEARNED:
[What the team should remember]
```

---

## 22.7 Integration Status Report

```
INTEGRATION STATUS REPORT
Week: [W/X]   Project: [Name]   Date: [Date]

SUMMARY
  Current Phase: HIL Integration
  Baseline: B_2025_W10
  Overall Status: AMBER (1 P1 open)

METRICS
  HIL test cases: 487/500 passed (97.4%)
  Open P1 defects: 1
  Open P2 defects: 4
  New defects this week: 6
  Closed defects this week: 9

P1 DEFECTS
  JIRA-1234: AEB false trigger at highway speeds
  Owner: A. Kumar  ETA: 2025-03-12

RISKS
  Radar SW v1.3.2 delivery delayed 1 week — may impact HIL schedule

NEXT WEEK PLAN
  Complete P1 investigation and fix
  Run full HIL regression after fix
  Prepare vehicle for Phase 3 integration
```

---

*Next: [Part 23 — Code & Scripting](part-23-code-scripting.md)*
