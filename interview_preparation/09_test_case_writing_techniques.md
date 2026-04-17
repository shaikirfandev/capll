# 09 — Test Case Writing Techniques
## Automotive Test Validation Engineer — Interview Preparation

---

## 1. What is a Test Case?

A **test case** is a documented set of conditions, inputs, and expected results used to verify that a system behaves as specified.

### Core Attributes of a Good Test Case

| Attribute | Description |
|-----------|-------------|
| **Test Case ID** | Unique identifier (e.g., TC_PA_RR_001) |
| **Title** | Short, action-oriented summary |
| **Objective** | What requirement is being verified |
| **Preconditions** | System state before execution |
| **Test Steps** | Exact sequential actions |
| **Input Data** | Specific values used |
| **Expected Result** | Measurable, observable outcome |
| **Actual Result** | Filled during execution |
| **Pass/Fail** | Based on expected vs actual |
| **Linked Requirement** | Traceability to spec (SRS/SDS) |
| **Priority** | Critical / High / Medium / Low |

---

## 2. Test Case Writing Techniques

### 2.1 Equivalence Partitioning (EP)

**Concept:** Divide input data into partitions where all values in a partition are expected to behave the same way. Test one value from each partition instead of every value.

**When to use:** Large input ranges — signal values, voltage ranges, speed ranges.

**Example — Vehicle Speed Signal (spec: 0–250 km/h):**

| Partition | Range | Test Value | Expected |
|-----------|-------|------------|----------|
| Invalid Below | < 0 | -1 | Rejected / DTC set |
| Valid | 0–250 | 120 | Accepted, processed |
| Invalid Above | > 250 | 260 | Rejected / DTC set |

```
TC_EP_001: Vehicle speed = -1 km/h → System rejects invalid signal
TC_EP_002: Vehicle speed = 120 km/h → System processes normally
TC_EP_003: Vehicle speed = 260 km/h → System rejects, sets DTC C1001
```

---

### 2.2 Boundary Value Analysis (BVA)

**Concept:** Test at the exact edges of valid/invalid boundaries — the most common location for bugs.

**Rule:** For each boundary, test: `(min-1)`, `min`, `(min+1)`, `(max-1)`, `max`, `(max+1)`

**When to use:** Any signal with a defined min/max specification.

**Example — Fuel Level Warning (spec: warning activates at ≤ 10L):**

| Test Value | Position | Expected |
|------------|----------|----------|
| 9L | Below threshold | Warning ON |
| 10L | At threshold (boundary) | Warning ON |
| 11L | Just above threshold | Warning OFF |
| 0L | Minimum | Warning ON |
| 80L | Maximum | Warning OFF |
| 81L | Above maximum | DTC / invalid |

```
TC_BVA_001: Fuel = 9L   → FuelLow_Warning = 1 (ACTIVE)
TC_BVA_002: Fuel = 10L  → FuelLow_Warning = 1 (ACTIVE — exact boundary)
TC_BVA_003: Fuel = 11L  → FuelLow_Warning = 0 (INACTIVE)
TC_BVA_004: Fuel = 0L   → FuelLow_Warning = 1 (tank empty)
TC_BVA_005: Fuel = 80L  → FuelLow_Warning = 0 (full tank)
```

**Real project use:** In BMW Cluster project, I discovered a bug where the fuel telltale activated at 11L instead of 10L — found only because BVA forced testing at 10L and 11L separately.

---

### 2.3 Decision Table Testing

**Concept:** Model all combinations of conditions and their corresponding actions in a table. Best for logic with multiple input conditions.

**When to use:** Warning priority logic, DTC trigger conditions, state machine transitions.

**Example — Seatbelt Warning Logic:**

| | TC1 | TC2 | TC3 | TC4 |
|--|-----|-----|-----|-----|
| **Speed > 20 km/h** | N | Y | Y | Y |
| **Seatbelt buckled** | N | Y | N | N |
| **Door open** | N | N | N | Y |
| — | — | — | — | — |
| **Seatbelt warning** | OFF | OFF | ON | ON |
| **DTC set** | No | No | No | Yes (Door) |

```
TC_DT_001: Speed=10, Buckled=Y, Door=Closed → Warning=OFF
TC_DT_002: Speed=30, Buckled=Y, Door=Closed → Warning=OFF
TC_DT_003: Speed=30, Buckled=N, Door=Closed → Warning=ON
TC_DT_004: Speed=30, Buckled=N, Door=Open   → Warning=ON + Door DTC
```

---

### 2.4 State Transition Testing

**Concept:** Test that a system moves correctly between states when specific events occur. Also test invalid transitions (system should NOT change state).

**When to use:** State machines — gear shifting, vehicle modes, DTC lifecycle, boot sequence.

**Example — Park Assist System State Machine:**

```
STATES:
  IDLE → ACTIVE → WARNING → EMERGENCY_BRAKE

TRANSITIONS:
  IDLE     → ACTIVE     : Reverse gear engaged
  ACTIVE   → WARNING    : Obstacle detected < 1.0m
  WARNING  → EMERGENCY_BRAKE : Obstacle < 0.3m
  WARNING  → ACTIVE     : Obstacle moves away > 1.0m
  Any      → IDLE       : Forward gear / speed > 10 km/h
```

| TC ID | From State | Event | Expected Next State |
|-------|-----------|-------|---------------------|
| TC_ST_001 | IDLE | Reverse gear | ACTIVE |
| TC_ST_002 | ACTIVE | Obstacle @ 0.8m | WARNING |
| TC_ST_003 | WARNING | Obstacle @ 0.25m | EMERGENCY_BRAKE |
| TC_ST_004 | WARNING | Obstacle moves to 1.5m | ACTIVE |
| TC_ST_005 | ACTIVE | Forward gear | IDLE |
| TC_ST_006 | IDLE | Obstacle detected (invalid) | IDLE (no change) |

**CAPL Script for State Transition Test:**
```capl
// State Transition Test — Park Assist
variables {
  message GearStatus_BC     msgGear;
  message UltrasonicEcho_BC msgEcho;
  int gPass = 0, gFail = 0;
}

on start {
  // TC_ST_001: IDLE → ACTIVE
  msgGear.GearPosition = 4;   // Reverse
  output(msgGear);
  delay(300);
  checkState("IDLE→ACTIVE", getValue(ParkAssist::PA_SystemState), 1);

  // TC_ST_002: ACTIVE → WARNING (obstacle at 0.8m)
  msgEcho.PA_Rear_Distance = 80;   // 80cm
  output(msgEcho);
  delay(300);
  checkState("ACTIVE→WARNING", getValue(ParkAssist::PA_SystemState), 2);

  // TC_ST_003: WARNING → EMERGENCY_BRAKE
  msgEcho.PA_Rear_Distance = 25;
  output(msgEcho);
  delay(300);
  checkState("WARNING→EMERGENCY", getValue(ParkAssist::PA_SystemState), 3);

  // TC_ST_005: Any → IDLE (forward gear)
  msgGear.GearPosition = 1;
  output(msgGear);
  delay(300);
  checkState("Any→IDLE", getValue(ParkAssist::PA_SystemState), 0);

  write("=== State Test: PASS=%d FAIL=%d ===", gPass, gFail);
}

void checkState(char label[], int actual, int expected) {
  if (actual == expected) {
    write("PASS [%s] State=%d", label, actual); gPass++;
  } else {
    write("FAIL [%s] State=%d (expected %d)", label, actual, expected); gFail++;
  }
}
```

---

### 2.5 Pairwise / Combinatorial Testing

**Concept:** Instead of testing all possible combinations (which grows exponentially), test all **pairs** of input values. Statistically, most bugs are triggered by interactions between 2 variables.

**When to use:** Multiple configuration options — ECU variants, vehicle configurations, sensor combinations.

**Example — ADAS Config Matrix:**
- Vehicle type: Sedan / SUV / Truck
- Sensor type: Ultrasonic / Radar / Camera
- Speed mode: City / Highway

Full combinations: 3×3×3 = **27 test cases**
Pairwise (all 2-way pairs covered): **9 test cases**

| TC | Vehicle | Sensor | Mode |
|----|---------|--------|------|
| 1 | Sedan | Ultrasonic | City |
| 2 | Sedan | Radar | Highway |
| 3 | Sedan | Camera | City |
| 4 | SUV | Ultrasonic | Highway |
| 5 | SUV | Radar | City |
| 6 | SUV | Camera | Highway |
| 7 | Truck | Ultrasonic | City |
| 8 | Truck | Radar | City |
| 9 | Truck | Camera | Highway |

---

### 2.6 Error Guessing

**Concept:** Use experience and intuition to guess where bugs are likely to hide. Not formalized — based on domain knowledge.

**Common automotive error guess points:**

| Area | Likely Bug Location |
|------|-------------------|
| CAN timing | Signal at exactly the timeout threshold (e.g., 499ms vs 500ms) |
| UDS services | NRC 0x22 (conditions not correct) — often missed in cold start |
| Multiplexed signals | Mux ID = 0 (default) vs Mux ID = 1 (active) — confusion |
| DTC status byte | Bit 3 (confirmed) vs Bit 0 (testFailed) — often swapped |
| Signal default values | After bus-off, default should be 0 or last valid? — spec ambiguity |
| Boot sequence | ECU sends first message before NVM is loaded — race condition |
| Gateway routing | Message forwarded on wrong CAN network at startup |

**Example test cases from error guessing:**
```
TC_EG_001: Send CAN message at exactly T=499ms (1ms before timeout) → no DTC
TC_EG_002: Send CAN message at exactly T=501ms (1ms after timeout)  → DTC set
TC_EG_003: Mux message with MuxID=0 carrying default values → ECU must not process as valid data
TC_EG_004: Power cycle ECU → verify UDS session reverts to 0x01 (default session)
TC_EG_005: Send 0x19 immediately after KL15 ON (within 100ms) → ECU must respond, not return NRC
```

---

### 2.7 Use Case / Scenario-Based Testing

**Concept:** Write test cases from a real-world user scenario end-to-end, not just individual signals.

**When to use:** System-level tests, SIL/HIL integration testing, acceptance testing.

**Example — Parking Assist Full Scenario:**

```
Scenario: Driver reverses into a parking space with a metal pole on the right side

Steps:
  1. Engine ON, gear in Park → PA system = IDLE
  2. Shift to Reverse → PA system = ACTIVE, rear sensors enabled
  3. Vehicle moves back at 5 km/h
  4. Right sensor detects obstacle at 1.5m → first audio beep (1Hz)
  5. Obstacle at 0.8m → audio beep 3Hz, telltale yellow
  6. Obstacle at 0.3m → audio beep 10Hz (continuous), telltale red
  7. Obstacle at 0.2m → Emergency brake assist activates
  8. Driver stops → audio OFF after 2s, telltale remains
  9. Driver shifts to Drive → PA system = IDLE, all signals cleared

Expected results at each step — checked via CAN signals and UDS 0x22
```

---

### 2.8 Regression Testing Strategy

**Concept:** Re-run a defined set of test cases after every SW change to ensure no previously working functionality broke.

**Automotive regression test selection criteria:**

| Priority | Include in Regression |
|----------|-----------------------|
| P0 — Safety critical | Always (seatbelt, brake, airbag warnings) |
| P1 — High | Always (DTC lifecycle, CAN timeout behavior) |
| P2 — Medium | On related module change |
| P3 — Low | On full regression cycle only |

**Example regression matrix for ADAS ECU:**
```
Smoke Regression (15 min):
  - Power cycle boot check
  - CAN bus communication check
  - UDS 0x10 session change
  - 3 P0 safety signal checks

Full Regression (4 hours):
  + All boundary value test cases
  + All state transition tests
  + DTC lifecycle (inject/confirm/clear)
  + 50-cycle timing measurements
  + All UDS service checks
```

---

## 3. Test Case Template (Automotive Standard)

```
Test Case ID  : TC_[MODULE]_[FEATURE]_[NUMBER]
Title         : [Short description of what is tested]
Requirement   : [SRS/SDS section number]
Test Type     : [Functional / Boundary / Negative / Performance / Regression]
Priority      : [Critical / High / Medium / Low]

Environment   :
  - Tool      : CANoe 12.0 / CANalyzer / dSPACE HIL
  - Network   : CAN FD 500kbps / LIN 19.2 kbps
  - ECU SW    : [SW version]
  - DBC       : [DBC file version]

Preconditions :
  1. ECU powered ON, KL15 active
  2. CAN bus active, no existing DTCs (0x14 cleared)
  3. Vehicle speed = 0 km/h
  4. All sensors in nominal state

Test Steps    :
  Step 1: [Action] → [Observable result]
  Step 2: [Action] → [Observable result]
  Step 3: [Action] → [Observable result]

Input Data    :
  - Signal: [signal name] = [value] [unit]
  - Message: [message name] @ [cycle time]

Expected Result:
  - [Signal name] = [expected value] within [time] ms
  - DTC [DTC code] = [present/not present]
  - [Telltale/warning] = [ON/OFF]

Pass Criteria : All expected results match actual results
Fail Criteria : Any deviation from expected result

Post-conditions:
  - Clear DTCs (UDS 0x14)
  - Reset signals to nominal
```

---

## 4. Real Interview Examples — Test Case Writing Questions

### Q: "Write test cases for a fuel low warning system."

**Answer approach — cover all techniques:**

```
Spec: Warning activates when fuel ≤ 10L. Deactivates when fuel ≥ 15L (hysteresis).

BVA Test Cases:
  TC_FUEL_001: Fuel = 9L  → Warning = ON  [below boundary]
  TC_FUEL_002: Fuel = 10L → Warning = ON  [at boundary — exact]
  TC_FUEL_003: Fuel = 11L → Warning = OFF [just above — no warning yet]
  TC_FUEL_004: Fuel = 14L → Warning = ON  [below deactivation threshold — hysteresis]
  TC_FUEL_005: Fuel = 15L → Warning = OFF [at deactivation boundary]
  TC_FUEL_006: Fuel = 16L → Warning = OFF [above deactivation threshold]

Negative / Error Guessing:
  TC_FUEL_007: Fuel = -1L → DTC B1001 set, warning OFF (invalid signal)
  TC_FUEL_008: Fuel signal timeout (no CAN message for 500ms) → DTC set, warning uses last valid

Scenario:
  TC_FUEL_009: Start at 50L → gradually decrease to 5L → confirm warning activates at 10L,
               then add fuel back to 16L → confirm warning deactivates at 15L
```

---

### Q: "How do you ensure test coverage for a CAN timeout?"

```
Test Cases:
  TC_TO_001: Stop sending message at T=0 → DTC set after 500ms (normal timeout)
  TC_TO_002: Stop at T=0, restart at T=499ms → DTC NOT set (just before timeout)
  TC_TO_003: Stop at T=0, restart at T=501ms → DTC set (just after timeout)
  TC_TO_004: Message resumes after DTC set → DTC status transitions to healed
  TC_TO_005: During timeout period, verify ECU uses default signal value (spec check)
  TC_TO_006: Multiple messages timeout simultaneously → verify all DTCs set
```

---

### Q: "Write test cases for UDS 0x19 ReadDTC service."

```
Positive Cases:
  TC_UDS_001: 0x19 01 FF → positive response 0x59, DTC count correct
  TC_UDS_002: 0x19 02 08 → confirmed DTCs returned after fault injection
  TC_UDS_003: 0x19 04 [DTC] → freeze frame data available after DTC set
  TC_UDS_004: After 0x14 clear → 0x19 02 returns 0 DTCs

Negative Cases:
  TC_UDS_005: 0x19 with wrong sub-function → NRC 0x12 (subFunctionNotSupported)
  TC_UDS_006: 0x19 in non-default session → NRC 0x7E or 0x22 per spec
  TC_UDS_007: 0x19 with missing byte → NRC 0x13 (incorrectMessageLength)
  TC_UDS_008: 0x19 during ECU initialization → NRC 0x78 (requestCorrectlyReceivedResponsePending)
```

---

## 5. Test Techniques Quick Reference Card

| Technique | Best For | Automotive Example |
|-----------|----------|--------------------|
| Equivalence Partitioning | Large input ranges | Speed: <0 / 0-250 / >250 |
| Boundary Value Analysis | Signal thresholds | Fuel warning at exactly 10L |
| Decision Table | Multi-condition logic | Warning priority rules |
| State Transition | State machines | PA: IDLE→ACTIVE→WARNING |
| Pairwise/Combinatorial | Config combinations | ECU variant × sensor type |
| Error Guessing | Known bug-prone areas | Timeout at T-1ms vs T+1ms |
| Scenario-Based | End-to-end user flows | Full parking assist scenario |
| Regression | Post-change validation | Smoke + full regression suite |

---

## 6. Automotive-Specific Test Categories

### Functional Testing
- Verify each requirement behaves as specified
- Normal operating conditions
- Example: "Speed signal received → ADAS enables"

### Boundary / Limit Testing
- Min, max, and edge values of all parameters
- Example: "Sensor voltage at 4.80V (minimum spec)"

### Negative / Fault Injection Testing
- Test system behavior under invalid inputs or fault conditions
- Example: "Send out-of-range signal → DTC must set within 2 drive cycles"

### Timing / Performance Testing
- Verify system meets response time requirements
- Example: "Gear→Reverse to camera active: within 200ms"
- Example: "ECU boot to SafetyReady: within 500ms"

### Regression Testing
- Re-validate existing functionality after SW update
- Example: "After SW v2.3 patch — all P0 tests must pass"

### Compatibility Testing
- Verify correct behavior across ECU hardware variants and SW versions
- Example: "Behavior identical on variant A and variant B hardware"

### Stress / Soak Testing
- Long-duration stability — run overnight, measure for degradation
- Example: "Inject fault signals at 1kHz for 8 hours — no memory leak"

### Protocol Compliance Testing
- Verify CAN/LIN/UDS protocol behavior matches ISO specification
- Example: "UDS 0x10 01 → response within P2 server time (50ms)"

---

## 7. Defect Reporting — What Makes a Good Bug Report

When a test case fails, the defect report must include:

```
Title         : [ECU] [Module] — [Short bug description]
Severity      : Critical / Major / Minor / Cosmetic
Priority      : P1 / P2 / P3
Build/SW Ver  : [ECU SW version where bug found]

Steps to Reproduce:
  1. [Exact preconditions]
  2. [Exact actions taken]
  3. [Exact input values]

Expected Result: [What should happen per spec, with requirement reference]
Actual Result  : [What actually happened, with signal values, timestamps]

Evidence:
  - CANoe trace file (screenshot or .blf attachment)
  - Signal values at time of failure
  - DTC status byte value
  - UDS response raw bytes

Root Cause Hypothesis: [If known — helps SW team prioritize]
Workaround       : [If available]
```

---

## 8. Test Traceability Matrix (TTM)

Links requirements → test cases → test results. Ensures 100% requirement coverage.

| Requirement ID | Requirement Description | Test Case IDs | Status |
|----------------|------------------------|---------------|--------|
| SRS_PA_001 | PA system activates on Reverse gear | TC_ST_001, TC_SC_001 | PASS |
| SRS_PA_002 | Audio warning at 3 distance zones | TC_BVA_015–017 | PASS |
| SRS_PA_003 | Emergency brake at <0.3m | TC_ST_003 | FAIL |
| SRS_CL_001 | Fuel telltale at ≤ 10L | TC_BVA_001–006 | PASS |
| SRS_CL_002 | Seatbelt warning > 20 km/h | TC_DT_003–004 | PASS |
| SRS_UDS_001 | ECU responds to 0x19 in default session | TC_UDS_001–004 | PASS |

**Coverage formula:**
$$\text{Coverage \%} = \frac{\text{Requirements with at least 1 PASS test case}}{\text{Total Requirements}} \times 100$$

---

*File: 09_test_case_writing_techniques.md | Updated: April 2026*
