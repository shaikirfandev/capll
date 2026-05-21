# Test Case Design — Happy Path, Alternate Path, Negative Path

## 1. The Three Test Paths

Every feature in a medical device must be tested across all three paths:

```
HAPPY PATH (Normal / Positive)
  ─ System behaves correctly when used as intended
  ─ Valid inputs, expected sequence, normal conditions
  ─ Goal: Confirm the primary function works

ALTERNATE PATH (Edge / Boundary)
  ─ System behaves correctly at the boundaries of its specification
  ─ Valid but non-typical inputs, unexpected but valid sequences
  ─ Goal: Confirm system handles all valid scenarios

NEGATIVE PATH (Error / Exception)
  ─ System handles invalid inputs gracefully and safely
  ─ Invalid inputs, out-of-sequence operations, hardware faults
  ─ Goal: Confirm system does NOT fail dangerously
```

---

## 2. Systematic Test Coverage Framework

### Step 1 — Identify Requirement Categories
For each requirement, identify:
1. What is the normal operating scenario?
2. What are the boundary conditions?
3. What are the failure/misuse scenarios?
4. Are there risk controls that must be tested?

### Step 2 — Apply Boundary Value Analysis (BVA)

For any requirement with a numeric range:

```
Example: "Device shall maintain temperature between 36.0°C and 42.0°C"

Boundary Value Test Points:
├─ Below lower boundary:     35.9°C → Expected: alarm/shutdown
├─ At lower boundary:        36.0°C → Expected: normal operation
├─ Just above lower:         36.1°C → Expected: normal operation
├─ Midpoint (nominal):       39.0°C → Expected: normal operation
├─ Just below upper:         41.9°C → Expected: normal operation
├─ At upper boundary:        42.0°C → Expected: normal operation
└─ Above upper boundary:     42.1°C → Expected: alarm/shutdown
```

### Step 3 — Apply Equivalence Partitioning

Divide inputs into partitions where the system behaves equivalently:

```
Example: User enters patient weight (valid: 1-300 kg)

Partition 1 (invalid low):   0 kg, -1 kg, -100 kg → Error message
Partition 2 (valid):         1-300 kg → Accept, use in calculation
Partition 3 (invalid high):  301 kg, 500 kg, 9999 kg → Error message
Partition 4 (non-numeric):   "abc", null, empty → Error message
```

---

## 3. Test Case Template

```
Test Case ID:   TC-[MODULE]-[NNN]
Title:          [Descriptive name — what is being tested]
Path Type:      [Happy / Alternate / Negative]
Requirement:    [REQ-ID: Requirement text being verified]
Risk Ref:       [Risk ID if testing a risk control]
Priority:       [Critical / High / Medium / Low]
Preconditions:  [System state before test begins]

Test Steps:
Step | Action                          | Expected Result
-----|----------------------------------|------------------
 1   | [User/system action]            | [Observable result]
 2   | [User/system action]            | [Observable result]
 ...

Acceptance Criteria: [Precise pass/fail definition]
Test Data:           [Input data used]
Post-conditions:     [System state after test]
Notes:               [Any special instructions]
```

---

## 4. Complete Example — Infusion Pump Rate Setting

**Requirement**: "The pump shall deliver fluid at rates between 0.1 mL/hr and 999.9 mL/hr in 0.1 mL/hr increments. Entry outside this range shall be rejected with an error message."

### Happy Path Tests

```
TC-PUMP-001 | HAPPY PATH
Title: Normal flow rate entry — midrange value
Preconditions: Pump powered on, in rate entry mode
Steps:
  1. Press rate entry button → Display shows rate entry field
  2. Enter "125.0" → Display shows "125.0 mL/hr"
  3. Press CONFIRM → Pump starts, delivers at 125.0 mL/hr
Acceptance: Pump running, rate displayed = 125.0 mL/hr, delivery confirmed

TC-PUMP-002 | HAPPY PATH
Title: Rate change during infusion
Preconditions: Pump running at 50.0 mL/hr
Steps:
  1. Press CHANGE RATE → Display shows current rate
  2. Enter "75.0" → Display shows "75.0 mL/hr"
  3. Press CONFIRM → Rate changes to 75.0 mL/hr
Acceptance: Volume/rate display updates, no interruption to delivery
```

### Alternate Path Tests

```
TC-PUMP-003 | ALTERNATE PATH — Lower Boundary
Title: Minimum valid flow rate entry
Preconditions: Pump in rate entry mode
Steps:
  1. Enter "0.1" → Display shows "0.1 mL/hr"
  2. Press CONFIRM → Pump starts
Acceptance: Pump runs, rate = 0.1 mL/hr, no error

TC-PUMP-004 | ALTERNATE PATH — Upper Boundary
Title: Maximum valid flow rate entry
Preconditions: Pump in rate entry mode
Steps:
  1. Enter "999.9" → Display shows "999.9 mL/hr"
  2. Press CONFIRM → Pump starts
Acceptance: Pump runs, rate = 999.9 mL/hr, no error

TC-PUMP-005 | ALTERNATE PATH — Maximum Resolution
Title: Entry at 0.1 mL/hr resolution
Preconditions: Pump in rate entry mode
Steps:
  1. Enter "5.7" → Display shows "5.7 mL/hr"
  2. Press CONFIRM → Pump starts
Acceptance: Rate = 5.7 mL/hr (not 5 or 6), delivery verified

TC-PUMP-006 | ALTERNATE PATH — Power interruption recovery
Title: Rate retained after power cycle
Preconditions: Pump running at 75.0 mL/hr
Steps:
  1. Power off pump
  2. Power on pump
  3. Observe display
Acceptance: Pump prompts user to resume at 75.0 mL/hr (previous rate retained in NVM)
```

### Negative Path Tests

```
TC-PUMP-007 | NEGATIVE PATH — Below minimum
Title: Entry below minimum rate rejected
Preconditions: Pump in rate entry mode
Steps:
  1. Enter "0.0" → 
  2. Press CONFIRM
Acceptance: Error message: "Rate must be 0.1–999.9 mL/hr", entry rejected, pump NOT started

TC-PUMP-008 | NEGATIVE PATH — Above maximum
Title: Entry above maximum rate rejected
Preconditions: Pump in rate entry mode
Steps:
  1. Enter "1000.0"
  2. Press CONFIRM
Acceptance: Error message displayed, entry rejected, pump NOT started

TC-PUMP-009 | NEGATIVE PATH — Non-numeric entry
Title: Alphabetic entry rejected
Preconditions: Pump in rate entry mode
Steps:
  1. Attempt to enter "abc" (if alpha keys available)
  2. Observe system behaviour
Acceptance: Non-numeric characters rejected at input level, not accepted

TC-PUMP-010 | NEGATIVE PATH — Empty entry
Title: Confirm without entering rate
Preconditions: Pump in rate entry mode, field empty
Steps:
  1. Press CONFIRM without entering any value
Acceptance: Error or prompt: "Please enter a rate", pump NOT started

TC-PUMP-011 | NEGATIVE PATH — Occlusion during infusion
Title: Pump alarm on downstream occlusion
Preconditions: Pump running at 100 mL/hr, tubing connected to flow phantom
Steps:
  1. Clamp the downstream tubing to simulate occlusion
  2. Wait ≤ T_DETECT (occlusion detection time per spec)
Acceptance: Audible alarm ≥ 55 dB, visual alarm, pump stops. RISK CTRL RC-007.

TC-PUMP-012 | NEGATIVE PATH — Air-in-line
Title: Pump detects air bubble
Preconditions: Pump running, air detector enabled
Steps:
  1. Inject 0.3 mL air bolus upstream of detector
  2. Observe
Acceptance: Pump stops within T_DETECT, alarm sounds. RISK CTRL RC-012.
```

---

## 5. Risk-Based Test Prioritisation

### Priority Assignment Matrix

| Risk Level (from FMEA) | Test Priority | Coverage Required |
|------------------------|---------------|------------------|
| High / Catastrophic | Critical | 100% — must pass, no exceptions |
| Medium / Serious | High | 100% — must pass |
| Low / Negligible | Medium | Representative sample sufficient |
| No risk impact | Low | Spot check |

### Risk Control Test Requirements
**Every risk control measure must have at least one test case that directly verifies it.**

```
FMEA Row:
Failure Mode: Air embolism from undetected air in line
Harm: Patient death
Risk Level: HIGH
Risk Control: RC-012 — Air-in-line detector shall stop pump
  └── Must verify: TC-PUMP-012 (air-in-line test)

Without TC-PUMP-012, RC-012 has no evidence of effectiveness.
Without evidence, the risk is NOT controlled for DHF purposes.
```

---

## 6. Systemic Test Review Checklist

Use this checklist when reviewing test cases written by others:

### Coverage Check
```
□ Does every safety-critical requirement have a test case?
□ Does every risk control have a verification test case?
□ Are all boundary values tested (lower, upper, just inside, just outside)?
□ Are negative/error cases tested for every input field?
□ Are time-dependent requirements tested (response time, timeout)?
□ Are power/communication interruption scenarios tested?
□ Are software fault injection tests included (if IEC 62304 Class C)?
```

### Test Case Quality Check
```
□ Acceptance criteria are objective (quantitative, not "appears correct")
□ Each step has a single clearly observable expected result
□ Preconditions are fully specified (leaves no ambiguity for executor)
□ Test data is specified (not left to executor discretion)
□ Test ID is unique and follows naming convention
□ Requirement traceability is correct and verified
□ Test case is repeatable (another person can execute and get same result)
```

### Medical Device-Specific Checks
```
□ Usability-critical tasks tested with representative users (not engineers)
□ Alarm tests include response time AND audibility
□ Software error handling tests include system logs / error codes
□ Sterility / cleanliness requirements tested with validated methods
□ Shelf-life tests are properly designed (accelerated aging per ASTM F1980)
□ Biocompatibility evidence linked (ISO 10993) — not tested in-house
```

---

## 7. Writing Acceptance Criteria — Good vs Bad

### Bad Acceptance Criteria
```
✗ "The device should work correctly"
✗ "The display looks OK"
✗ "The alarm sounds"
✗ "Temperature is within range"
✗ "The software does not crash"
```

### Good Acceptance Criteria
```
✓ "Device delivers fluid at 100.0 ± 0.5 mL/hr as measured by gravimetric scale over 60 minutes"
✓ "Display shows temperature value with format: 'XX.X °C', font size ≥ 5mm, readable at 60cm distance"
✓ "Audible alarm ≥ 65 dB(A) at 1m, confirmed with calibrated sound level meter"
✓ "Temperature measurement = reference ± 0.3°C across range 35.0°C to 42.0°C"
✓ "System continues operation and logs error code ERR-042; no data loss occurs; user notified within 500ms"
```

### The Three Properties of Good Acceptance Criteria
1. **Objective**: Can be evaluated to TRUE or FALSE without interpretation
2. **Measurable**: Specifies the measurement method and tolerance
3. **Traceable**: Links back to the specification value it verifies
