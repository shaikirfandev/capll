# 18 — Functional Safety (ISO 26262)

> **Standard:** ISO 26262:2018 (2nd edition) — Road vehicles — Functional safety  
> **Scope:** E/E systems (electrical/electronic) in passenger cars, trucks, motorcycles

---

## 18.1 ISO 26262 Structure

```
ISO 26262 (12 parts):
  Part 1:  Vocabulary
  Part 2:  Management of functional safety
  Part 3:  Concept phase (HARA, Safety Goals)
  Part 4:  Product development: System level
  Part 5:  Product development: Hardware
  Part 6:  Product development: Software ← ADAS ECU developers live here
  Part 7:  Production, operation, service, decommissioning
  Part 8:  Supporting processes (tool qualification, proven in use)
  Part 9:  ASIL-oriented and safety-oriented analyses
  Part 10: Guidelines on ISO 26262
  Part 11: Guidelines on application of ISO 26262 to semiconductors
  Part 12: Adaptation for motorcycles

Software development lifecycle (Part 6):
  Requirements → Design → Unit Impl → Unit Test → Integration Test → Verification
  Each step: work products (documents), methods, reviews
```

---

## 18.2 ASIL Levels

```
ASIL = Automotive Safety Integrity Level

Determination: HARA (Hazard Analysis and Risk Assessment)
  Risk = Severity × Exposure × Controllability

Severity (S):
  S0: no injuries
  S1: light injuries
  S2: severe/life-threatening injuries (survival probable)
  S3: life-threatening injuries (survival uncertain) or fatalities

Exposure (E):
  E0: impossible
  E1: very low probability
  E2: low probability
  E3: medium probability (some drives)
  E4: high probability (almost every drive)

Controllability (C):
  C0: controllable in general
  C1: simply controllable
  C2: normally controllable (most drivers can handle it)
  C3: difficult to control or uncontrollable

ASIL matrix (simplified):
  S3 + E4 + C3 = ASIL D (highest, most stringent)
  S3 + E4 + C2 = ASIL D
  S2 + E3 + C2 = ASIL B
  S1 + E2 + C2 = ASIL A (lowest)
  QM = not safety relevant (but still quality-managed)
```

---

## 18.3 HARA Example — LKA Steering Torque

```
Hazardous Event: "Unintended high steering torque applied by LKA on highway at 130 km/h"

Severity: S3 (potential fatal crash at highway speed)
Exposure: E4 (LKA is active on almost every highway drive)
Controllability: C2 (most drivers CAN recover, but not all)
→ ASIL = C (or D depending on OEM analysis)

Safety Goal derived from Hazard:
  "LKA shall not apply steering torque exceeding 5 Nm without confirmed driver intent"
  
  Safety requirements derived from goal:
  SR-1: LKA torque request must be limited to ±3 Nm in software (LKA SWC)
  SR-2: EPS ECU must independently limit accepted LKA torque to ±5 Nm (hardware guard)
  SR-3: LKA must detect driver override (torque > 2.5 Nm) and release within 100ms
  SR-4: EPS must timeout LKA command if no frame received for 50ms
  SR-5: LKA must deactivate if camera signal timeout > 100ms (SR-4 in AUTOSAR DEM)

ASIL decomposition:
  ASIL C requirement → LKA SWC (ASIL A) + EPS monitor (ASIL A(C))
  Both elements are independent → combined integrity = ASIL C
```

---

## 18.4 Software Safety Requirements (Part 6)

```
ISO 26262-6: Software development process requirements by ASIL:

               | QM | A  | B  | C  | D
Informal spec  | ++  | ++ | o  | o  | -
Formal notations| -  | o  | o  | +  | ++
Design patterns: Restricted data flow, limited control flow | - | o | + | ++ | ++
Dynamic allocation: NOT ALLOWED above ASIL QM              |   |   | Forbidden | Forbidden | Forbidden
Recursion: NOT ALLOWED above QM (call depth unknown)       |   |   | Forbidden | Forbidden | Forbidden
Unit testing required: | recommended | required | required | required | required
Coverage: SC | SC | BC | MC/DC | MC/DC
Code inspection: informal | informal | peer review | independent | independent

++ = highly recommended, + = recommended, o = neutral, - = not recommended
```

---

## 18.5 FMEA for LKA Steering Torque Function

```
FMEA = Failure Mode and Effects Analysis

Component: LKA PID Controller (software function)

| Failure Mode              | Effect                         | Detection     | Mitigation |
|---------------------------|--------------------------------|---------------|------------|
| Stuck at max torque       | Vehicle veers off lane         | EPS timeout   | EPS hard limit |
| Integral windup           | Sudden large torque on engage  | N/A           | Anti-windup clamp |
| Wrong sign output         | Torque away from lane          | Lane quality  | Direction sanity check |
| dt=0 division             | CPU exception / NaN output     | SW test       | Guard dt > 0 |
| State machine stuck FAULT | LKA stays off permanently      | DTC to DEM    | Clear on ignition |
| PID gains corrupted (NvM) | Wrong response magnitude       | ROM CRC check | Protect gains in flash |

Safety mechanism: EPS ECU independent torque monitor (E2E protected CAN message)
  If ADAS_LKA_Cmd CRC fails OR message counter jumps → EPS sets torque = 0 immediately
  → Single-point fault (SPF) covered by EPS-side monitor
```

---

## 18.6 E2E Protection (AUTOSAR)

```
End-to-End (E2E) protection: detects transmission errors in safety-critical CAN messages

CRC + counter appended to safety-critical I-PDUs:
  Byte 0: CRC8 of payload (polynomial 0x1D — AUTOSAR E2E Profile 1)
  Byte 1: message counter (0..15, rolls over)
  Receiver checks:
    1. CRC matches → data not corrupted
    2. Counter incremented by 1 → no missed or duplicate messages

AUTOSAR E2E Profiles:
  Profile 1: 8-bit CRC, 4-bit counter (used in CAN Classic, small PDUs)
  Profile 2: 8-bit CRC, 8-bit counter
  Profile 4: 32-bit CRC (CAN FD, Ethernet PDUs)
  Profile 6: 32-bit CRC + sequence counter (SOME/IP)

In production: E2E protection on all ASIL-B+ messages:
  ADAS_LKA_Cmd (ASIL C): Profile 1 CRC + counter
  EPS_Status (ASIL C):    Profile 1 CRC + counter
  AEB_BrakeRequest (ASIL D): Profile 4 (32-bit CRC)
```

---

## 18.7 Interview Questions

```
L1:
  Q: What is ASIL and how is it determined?
  A: ASIL = Automotive Safety Integrity Level (QM, A, B, C, D).
     Higher ASIL = stricter development requirements.
     Determined by HARA using three factors:
     S (Severity): how badly could someone be hurt? (S0-S3)
     E (Exposure): how often is the vehicle in the hazardous situation? (E0-E4)
     C (Controllability): can the driver recover? (C0-C3)
     High S + high E + low C → high ASIL.
     Example: S3 + E4 + C3 = ASIL D (braking, steering)
              S2 + E3 + C2 = ASIL B (parking assist)

  Q: What is a Safety Goal?
  A: A Safety Goal is a high-level safety requirement derived from a Hazardous Event.
     It describes what the system must NOT do (or must do) to prevent the hazard.
     Example for LKA:
     Hazard: "Unintended LKA steering torque causes loss of vehicle control"
     Safety Goal: "The LKA system shall not apply steering torque > 5 Nm without 
     confirmed driver intent."
     Safety goals are assigned an ASIL level and drive all downstream requirements.

L2:
  Q: What is ASIL decomposition?
  A: ASIL decomposition: split one ASIL requirement into two lower ASIL requirements
     implemented by independent elements.
     Rule: ASIL B(D) × ASIL B(D) = ASIL D (both channels must be independent)
     
     Example: AEB braking at ASIL D
     → ASIL B(D) in ADAS ECU (radar-based deceleration request)
     → ASIL B(D) in ESC ECU (independent brake pressure monitoring)
     Independence requirement: different hardware, different developers, different tools.
     If not independent → decomposition is invalid → must implement full ASIL D in one element.

L3:
  Q: How does ISO 26262 affect day-to-day software engineering?
  A: Concrete engineering changes:
     Code review: peer review required for ASIL B, independent review for ASIL C/D
     Testing: MC/DC coverage measurement with qualified tool for ASIL C/D
     Static analysis: Polyspace/Axivion on every commit, 0 RED results required
     No dynamic allocation, no recursion, no exceptions
     Every function has: requirements reference, design description, test cases
     Change management: every code change requires safety impact assessment
     (Could this change introduce a hazard? Does it affect safety requirements?)
     Tool qualification: GCC, GTest, coverage tools must be qualified per ISO 26262-8
       (TQL-1 to TQL-5 based on how safety-critical their output is)
     Work products: every phase produces documented evidence (ASPICE SWE.1-SWE.6)
     
     Practical daily impact: slower, more documentation, but: zero ambiguity about
     what the code is supposed to do, very few production field bugs, strong regression safety.
```
