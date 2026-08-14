# Part 21 — Senior / Lead / Architect Level

---

## 21.1 Role Comparison

| Role | Scope | Responsibilities |
|---|---|---|
| Integration Engineer | ECU / feature level | Hands-on integration, test execution, defect investigation |
| Senior Integration Engineer | Domain level | Design integration strategy, guide team, complex defect analysis |
| Integration Lead | Project level | Plan and coordinate all integration activities, interface with other leads |
| Software Architect | Architecture | Define software architecture, interface standards, technology choices |
| System Architect | System | End-to-end system architecture, cross-domain decisions |
| Validation Lead | Validation | Lead validation strategy, sign-off on releases |

---

## 21.2 System Integration Strategy

A senior engineer or lead defines the integration strategy before any integration work begins:

**Key decisions:**
1. **Integration order:** Bottom-up (verify ECUs individually first) vs Top-down (start with system view)
2. **Stub strategy:** Which ECUs will be simulated in CANoe and when real hardware joins
3. **Integration environments:** SIL → ECU bench → network bench → HIL → vehicle
4. **Entry/exit criteria:** Defined for each phase transition
5. **Integration baseline:** Fixed SW baseline for each integration sprint

---

## 21.3 ECU Dependency Management

Dependencies between ECUs must be mapped:

```
ADAS DC depends on:
  - Camera ECU (perception input)
  - Radar ECU (object list)
  - GNSS ECU (position)
  - Brake ECU (actuation)
  
When Radar ECU SW changes: re-test ADAS DC integration
When Brake ECU changes: re-test AEB end-to-end
```

**Integration dependency matrix:** maintained in a spreadsheet or tool (DOORS, Jira), showing which ECU changes trigger which re-integration.

---

## 21.4 Interface Governance

As integration lead, you own the interface definition process:
- All interface changes must go through Interface Change Request (ICR) process
- Impact analysis required before approving ICR
- All stakeholder ECU owners must approve interface changes
- ICD (Interface Control Document) is baselined and change-controlled

---

## 21.5 Version Compatibility and Integration Baselines

**Baseline:** A fixed set of SW versions for all ECUs that are tested together.

```
Integration Baseline B_2025_W10:
  ADAS ECU:  v1.3.2
  Cluster:   v2.1.0
  IVI:       v3.0.1
  Gateway:   v4.2.0
  TCU:       v1.5.0
  Body ECU:  v2.0.1
```

All HIL and vehicle tests use only baselined software. No untested mix-and-match.

---

## 21.6 Branch and Release Strategy

```
develop ←── feature branches (daily integration)
    ↓
integration/sprint-23 ←── stabilization baseline
    ↓
release/v2.5 ←── OEM acceptance tests
    ↓
main ←── production release tagged
```

---

## 21.7 Defect Triage

Integration lead runs weekly defect triage:
1. Review all open defects (Jira)
2. Classify: blocking / critical / major / minor
3. Assign owners and fix deadlines
4. Identify recurring defect patterns (systemic issues)
5. Escalate blocking issues to management

**KPI tracking:**
- Open P1 defects count
- Defect injection rate (new defects per week)
- Defect closure rate
- Regression rate (defects re-opened after fix)

---

## 21.8 Technical Debt Management

As senior/architect:
- Document known workarounds and temporary fixes with a debt ticket in Jira
- Prioritize debt items against features in sprint planning
- Prevent debt accumulation in safety-critical areas

---

## 21.9 Supplier Integration Management

When ECU software is developed by a Tier-1 or external supplier:
1. Define acceptance criteria (functional, timing, diagnostic requirements)
2. Provide integration test environment (HIL, test scripts)
3. Run incoming integration test on every supplier SW delivery
4. Track defects in joint defect tracker (Jira, Polarion)
5. Conduct regular integration status meetings

---

## 21.10 Integration Metrics

| KPI | Target | Measurement |
|---|---|---|
| HIL test pass rate | > 98% | Weekly HIL run |
| Build success rate | > 99% | CI dashboard |
| Integration defect density | < 0.5 per KLOC | Jira |
| Mean time to resolve P1 | < 2 days | Jira |
| First-time flash success rate | > 95% | Flash log |
| Integration baseline delivery on schedule | 100% | Project plan |

---

## 21.11 Production Release Management

Before a software release to OEM production:

```
Release Gate Checklist:
[ ] All P1/P2 defects closed or accepted risk
[ ] HIL test pass rate ≥ 98%
[ ] Vehicle test sign-off from validation lead
[ ] Static analysis compliant (no mandatory MISRA violations open)
[ ] Safety review sign-off
[ ] Cybersecurity review sign-off
[ ] Release notes complete and reviewed
[ ] Software binary matches flash report (CRC match)
[ ] Artifact uploaded to OEM artifact repository
[ ] Release communication sent to all stakeholders
```

---

## Summary

| Senior Skill | Outcome |
|---|---|
| Integration strategy | Clear plan, no surprises |
| Dependency management | Know what to re-test on every change |
| Interface governance | Stable interfaces, no late surprises |
| Baselines | Reproducible, traceable test results |
| Defect triage | Blocking issues resolved quickly |
| Release management | On-time, quality releases |

---

*Next: [Part 22 — Production-Ready Artifacts](part-22-production-artifacts.md)*
