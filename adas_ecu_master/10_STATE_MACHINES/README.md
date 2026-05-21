# 10 — State Machines in Automotive ECU Software

> **Pattern:** Hierarchical State Machine (HSM) — used in every production ADAS ECU  
> **AUTOSAR:** Maps to SWC mode management, BswM (Basic Software Mode Manager)

---

## 10.1 Why State Machines?

```
Automotive ECU requirements:
  - Deterministic behaviour (no undefined states)
  - Explicit fault handling paths
  - Safe default on entry/exit of every state
  - Auditable transitions (requirements traceability)
  - ISO 26262: state machines must be verified via FMEA

State machine benefits:
  - Every state and transition is DOCUMENTED (→ requirements traceability)
  - No "if/else" spaghetti — impossible transitions are structurally impossible
  - On entry/exit actions ensure actuators are always in safe state
  - Hierarchical (HSM): parent states handle common events (e.g., IGNITION_OFF
    in any active sub-state → SLEEP). Reduces code duplication.
```

---

## 10.2 Flat vs Hierarchical State Machine

```
FLAT SM:
  Every state handles every event.
  For N states × M events = N×M transition rules.
  Problem: IGNITION_OFF must be handled in all 10 states → 10 duplicate transitions.

HIERARCHICAL SM (HSM) — Miro Samek "Practical UML State Charts in C/C++":
  Parent states handle common events.
  Child states inherit parent transitions.
  
  Example:
    OPERATIONAL state (parent) handles IGNITION_OFF → SLEEP (once)
    LKA, ACC, OVERRIDE (children) only handle their specific events
    IGNITION_OFF propagates UP to parent if not handled by child

  Reduction: 10 states × 8 events = 80 rules → ~25 rules with HSM
```

---

## 10.3 AUTOSAR Mode Manager (BswM)

```
In AUTOSAR Classic, state management uses BswM:

  BswM_ModeNotification:
    Applications and BSW modules notify BswM of mode changes.
    BswM evaluates rules and triggers actions.

  Example: LKA SWC signals mode:
    Rte_Switch_SwcModeSwitchPort_LKAMODE(LKAMODE_ACTIVE)
    
    BswM rule: IF LKA_MODE == ACTIVE AND EPS_FAULT == FALSE
               THEN enable LKA COM signals

  AUTOSAR Adaptive (R21-11):
    ara::exec::ExecutionClient — report application state
    ara::com SOME/IP event notifications replace BswM rules

OSEK/AUTOSAR OS Application Modes:
  OSEK modes: OSDEFAULTAPPMODE + custom modes
  Tasks can be activated only in specific app modes
  Example: LKA task (10ms) only active in NORMAL_DRIVE mode
```

---

## 10.4 Common ADAS State Machine Patterns

```
Pattern 1: "FAULT is latching"
  Safety requirement: once a safety-critical fault is detected, do NOT auto-recover.
  Require: ignition cycle (power cycle) or explicit diagnostic reset (UDS 0x11 service).
  Reason: if EPS fault caused LKA to output wrong torque, auto-recovery is dangerous.

Pattern 2: "Override Hold Timer"
  After driver override, hold override state for N seconds (e.g., 3s) before re-engaging.
  Prevents "ping-pong" oscillation between ACTIVE and OVERRIDE states.
  Implementation: uint32_t overrideTimerMs; increment in override state; transition when
  timer expires AND driver torque has been below threshold.

Pattern 3: "Safe Entry/Exit Actions"
  onEntry(ACTIVE):  verify actuator is healthy before applying torque
  onExit(ACTIVE):   zero torque request, signal EPS to release control
  onEntry(FAULT):   zero all outputs, log DTC to DEM, set warning lamp

Pattern 4: "Graceful Degradation"
  Camera fails: LANE_LOST event → LKA disables, ACC continues (radar only)
  Radar fails:  ACC disables, LKA continues (camera only)
  Both fail: → system degraded → warning lamp only
  Defined in HARA/FMEA documents as planned degradation paths
```

---

## 10.5 Interview Questions

```
L1:
  Q: Why use a state machine instead of if/else in an ADAS feature?
  A: State machines provide deterministic behaviour: every input in every state
     produces exactly one defined output + next state. There are no undefined paths.
     In safety-critical code, undefined behaviour is unacceptable (ISO 26262).
     Also: state machines map directly to requirements (UML state diagrams) →
     automated requirements traceability tools can generate/verify test cases from them.

  Q: What is an entry action and an exit action?
  A: onEntry(): executes ONCE when entering a state.
       Example: when entering LKA_ACTIVE → enable EPS LKA torque channel, start timeout timer
     onExit(): executes ONCE when leaving a state.
       Example: when leaving LKA_ACTIVE → set EPS torque request = 0, cancel timeout timer
     These ensure actuators are always in a safe state regardless of which transition fires.

L2:
  Q: How do you test a state machine?
  A: 1. State transition matrix: create N×M matrix of all states × events.
        Verify every cell is explicitly HANDLED or IGNORED (not undefined).
     2. All-transitions coverage: test suite must exercise every valid transition.
     3. Invalid transition test: send invalid events, verify state does not change
        and no undefined behaviour occurs.
     4. Guard condition test: verify transitions only fire when guard conditions are met.
     5. For ISO 26262 ASIL C/D: formal verification (model checking with tools like
        Simulink State Flow + Polyspace, or SCADE).

L3:
  Q: How does AUTOSAR BswM interact with SWC state machines?
  A: BswM is the central mode arbiter in AUTOSAR Classic:
     1. SWC signals its mode via Rte_Switch() → BswM receives mode notification
     2. BswM evaluates action table (configured in ARXML):
        IF SWC1_mode == ACTIVE AND Voltage > 9V THEN enable COM TX for LKA signals
     3. BswM executes actions: starts/stops ComM channels, activates OS Alarms,
        switches BSW modules to required state
     
     This means: SWC state machine controls SWC behaviour,
     BswM controls system-level resource management (communication, power, scheduling).
     Clear separation of concerns: feature logic vs system configuration.
```
