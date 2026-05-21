# 15 — Unit Testing for Automotive ECU Code

> **Frameworks:** Google Test (GTest), CppUTest, VectorCAST, Cantata  
> **Standard:** ISO 26262 Part 6 (unit testing requirements by ASIL)

---

## 15.1 Testing Requirements by ASIL Level

| ASIL | Coverage Requirement | Recommended Method |
|------|---------------------|--------------------|
| QM   | Statement coverage (SC) | Any unit test framework |
| A    | Branch coverage (BC) | GTest + gcov |
| B    | MC/DC (Modified Condition/Decision Coverage) | VectorCAST or Cantata |
| C    | MC/DC | VectorCAST, formal review |
| D    | MC/DC + hardware-in-the-loop | VectorCAST + HIL test |

```
MC/DC = Modified Condition/Decision Coverage:
  Every decision (if/switch/ternary) must be tested with:
  - Each condition independently affecting the outcome
  - Example: if (speedOk && laneOk && !fault)
    MC/DC requires 4 test cases where each variable independently toggles outcome.
  
  Typically requires 2×(conditions) + 1 test cases per decision.
  NASA space software uses MC/DC as standard.
  Required for DO-178C Level A (avionics) and ISO 26262 ASIL D.
```

---

## 15.2 GTest Structure for ECU Code

```cpp
// Test fixture (setup/teardown):
class LkaTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Runs before each test
        lka = std::make_unique<LkaController>();
    }
    void TearDown() override {
        // Runs after each test
    }
    std::unique_ptr<LkaController> lka;
};

// Test case:
TEST_F(LkaTest, StartsInactive) {
    EXPECT_EQ(lka->getState(), LkaState::INACTIVE);
}

// Parameterised test (boundary value analysis):
class SpeedBoundaryTest : public ::testing::TestWithParam<float> {};

TEST_P(SpeedBoundaryTest, BelowMinSpeedRemainsInactive) {
    float speed = GetParam();
    LkaInputs in; in.vehicleSpeedKph = speed; in.lkaEnableSwitch = true;
    in.laneQuality = LaneQuality::GOOD;
    auto out = lka->process(in);
    EXPECT_EQ(out.state, LkaState::INACTIVE);
}

INSTANTIATE_TEST_SUITE_P(LowSpeedValues, SpeedBoundaryTest,
    ::testing::Values(0.0F, 30.0F, 59.0F, 59.9F));
```

---

## 15.3 Dependency Injection for CAN Mocking

```cpp
// Problem: SWC calls Rte_Read_VehicleSpeed() directly — hard to test
// Solution: inject CAN interface via abstract port (interface + mock)

class ICanInterface {
public:
    virtual ~ICanInterface() = default;
    virtual float readVehicleSpeed() = 0;
    virtual bool  writeLkaTorque(float torqueNm) = 0;
};

// Production implementation
class AutosarCanInterface : public ICanInterface {
    float readVehicleSpeed() override {
        float v; Rte_Read_Speed_VehicleSpeed(&v); return v;
    }
    bool writeLkaTorque(float t) override {
        Rte_Write_Lka_TorqueRequest(t); return true;
    }
};

// GTest mock implementation
class MockCanInterface : public ICanInterface {
public:
    float  vehicleSpeed = 80.0F;
    float  lastWrittenTorque = 0.0F;
    
    float readVehicleSpeed() override { return vehicleSpeed; }
    bool  writeLkaTorque(float t) override { lastWrittenTorque = t; return true; }
};

// Test with mock:
TEST(LkaWithMock, AppliesTorqueWhenOffset) {
    MockCanInterface mock;
    mock.vehicleSpeed = 80.0F;
    
    LkaController lka(&mock);  // Inject mock
    LkaInputs in{}; in.laneOffsetM = 0.4F; in.laneQuality = LaneQuality::GOOD;
    
    auto out = lka.process(in);
    EXPECT_NE(out.steeringTorqueNm, 0.0F);   // Torque must be applied
    EXPECT_GT(mock.lastWrittenTorque, -5.0F); // Must be within safe limits
    EXPECT_LT(mock.lastWrittenTorque,  5.0F);
}
```

---

## 15.4 Boundary Value Analysis

```
Technique: test at exact boundary + just below + just above

LKA speed boundary (MIN_SPEED_KPH = 60.0):
  Test 59.9 → INACTIVE (below threshold)
  Test 60.0 → STANDBY  (exactly at threshold)
  Test 60.1 → STANDBY  (just above)
  Test 180.1→ INACTIVE (above max speed)

PID output clamping:
  Test error = 0.0    → output = 0.0
  Test error = 100.0  → output = outMax (clamped)
  Test error = -100.0 → output = outMin (clamped)
  Test dt = 0.0       → output = 0.0 (division guard)
  Test dt = -1.0      → output = 0.0 (negative time guard)

Ring buffer:
  Test push to N-1 items: success
  Test push to N items:   success (full)
  Test push to N+1 items: FAIL (buffer full, no push)
  Test pop from empty:    FAIL (returns false, no corruption)
```

---

## 15.5 Code Coverage Measurement

```bash
# GCC coverage flags:
g++ -std=c++17 --coverage -O0 test_adas_ecu.cpp -lgtest -lgtest_main -o test_cov
./test_cov

# Generate coverage report:
gcov test_adas_ecu.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html/
# Open coverage_html/index.html in browser

# Check MC/DC: use gcov branch coverage
gcov --branch-probabilities test_adas_ecu.cpp
# Shows each branch hit/not-hit for every if statement

# For ASIL-D: use VectorCAST or Cantata — they report MC/DC natively
# and generate compliance-ready coverage reports (ISO 26262 Annex B)
```

---

## 15.6 Interview Questions

```
L1:
  Q: What is the difference between statement coverage and branch coverage?
  A: Statement coverage (SC): every line of code executed at least once.
     100% SC does NOT mean all branches tested.
     
     Example: if (x > 0) { foo(); }
     SC 100%: one test with x=1 (foo() executes).
     But: branch with x=-1 (foo() not called) never tested.
     
     Branch coverage (BC): every branch (true/false) of every decision executed.
     Requires test with x=1 AND x=-1.
     BC ⊇ SC: 100% BC implies 100% SC (but not vice versa).
     
     MC/DC: stricter than BC. Each condition independently shown to affect outcome.
     Required for ISO 26262 ASIL D.

  Q: What should you test in a PID controller unit test?
  A: Key test cases:
     1. Zero error → zero output (no false intervention)
     2. Positive error → positive output (correct direction)
     3. Negative error → negative output (correct direction)
     4. Output clamping at outMin and outMax (safety limit)
     5. Anti-windup: integral stays within clamp even for sustained large error
     6. Reset: after reset(), integral and derivative term = 0
     7. Zero dt_s: no division by zero, returns 0
     8. Step response: error goes from 0 → 1 → check proportional response

L2:
  Q: How do you test a state machine with unit tests?
  A: 1. Test every valid transition:
        send correct event in correct state → verify correct next state
     2. Test every guard condition:
        event with guard NOT met → state must not change
     3. Test invalid events:
        send event not defined for current state → no state change, no crash
     4. Test entry/exit actions:
        verify side effects (mock actuator calls) occur on expected transitions
     5. Sequence tests:
        INACTIVE → STANDBY → CORRECTING → OVERRIDE → STANDBY (full scenario)
     
     Tool: GTest parametrised tests generate all combinations:
       INSTANTIATE_TEST_SUITE_P(AllTransitions, StateTransitionTest, 
           testing::Values(transition1, transition2, ...));

L3:
  Q: How do you achieve ISO 26262 ASIL-D unit testing compliance?
  A: Requirements from ISO 26262-6:
     1. Unit tests derived from unit requirements (not just code coverage)
        → Each test case references a requirement ID (JIRA/DOORS traceability)
     2. MC/DC coverage: use qualified tool (VectorCAST or Cantata rated for ASIL-D)
        → Tool qualification: ISO 26262-8 Annex B TQL-4 or TQL-5
     3. Independence: tester different from developer (reviewer sign-off)
     4. Automated regression: tests run in CI on every commit
     5. Coverage measurement: qualified coverage tool (not gcov for ASIL-D)
     6. Equivalence class + boundary value analysis documented per test
     7. Robustness tests: null pointers, max values, min values, invalid inputs
     
     Typical ASIL-D test evidence package:
       - Unit test specification (test cases from requirements)
       - Test execution report (pass/fail for each test case)
       - Coverage report (MC/DC ≥ 100% for safety functions)
       - Code review checklist (MISRA compliance, no undefined behaviour)
```
