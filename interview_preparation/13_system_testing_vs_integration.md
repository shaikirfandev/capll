# System Testing vs. Integration Testing
## Automotive Test Strategy – Levels, Methods, and Interview Q&A

---

## 1. V-Model Test Levels in Automotive

```
Requirements ─────────────────────────────► System Test
    │                                           ▲
System Design ──────────────────► Integration Test
    │                                   ▲
SW Architecture ─────► SW Integration Test
    │                         ▲
SW Unit Design ──► SW Unit Test
    │                   ▲
    └─── Implement ──────┘
```

Each level on the left of the V has a corresponding test level on the right.

---

## 2. Unit Testing

### What is it?
Testing the smallest testable unit of software (function, module, class) in **isolation**.

### Characteristics
| Aspect | Detail |
|---|---|
| Scope | Single function or module |
| Environment | PC-based, mocked dependencies |
| Speed | Very fast (ms per test) |
| Tools | GoogleTest, Unity, CppUTest, VectorCAST |
| Coverage target | Branch / MC/DC (ASIL-dependent) |
| Performed by | Developer |

### Example (C ECU code – GoogleTest)
```cpp
// Function under test: engine_control.c
int CalculateThrottle(int rpm, int targetRpm)
{
    int delta = targetRpm - rpm;
    if (delta < 0) return 0;
    if (delta > 1000) return 100;
    return delta / 10;
}

// Unit test
TEST(EngineControlTest, ThrottleInRange) {
    EXPECT_EQ(CalculateThrottle(1000, 1500), 50);
    EXPECT_EQ(CalculateThrottle(2000, 1000), 0);   // below target → 0
    EXPECT_EQ(CalculateThrottle(1000, 3000), 100); // large delta → max
}
```

---

## 3. Integration Testing

### What is it?
Testing that **multiple software components or ECUs work correctly together**, focusing on interfaces, communication protocols, and data exchange.

### Types of Integration Testing in Automotive

| Type | Description |
|---|---|
| **SW Integration Test** | SWCs integrated within one ECU, test interfaces (RTE ports, AUTOSAR COM) |
| **HW/SW Integration Test** | SW running on real ECU hardware, test driver interactions |
| **ECU Integration Test** | Multiple ECUs on bench, test CAN/LIN/Ethernet communication |
| **Vehicle Integration** | All ECUs in vehicle, test system end-to-end |

### Characteristics
| Aspect | Detail |
|---|---|
| Scope | 2+ components/ECUs interacting |
| Environment | HIL bench, partial vehicle, full bench |
| Focus | Interfaces, signals, timing, protocol compliance |
| Tools | CANoe, dSPACE, Python + python-can |
| Performed by | System/integration test engineers |

### Integration Test Example (CAPL)
```capl
// Test: ECM sends EngineSpeed, TCM receives and acts
testcase TC_ECM_TCM_SpeedSignal()
{
  testStep("Stimulate ECM: set EngineSpeed to 3000 RPM");
  setValue(EngineData::EngineSpeed_Sim, 3000.0);

  // Wait for TCM to activate gear change
  testWaitForSignal(TransmissionData::GearChangeRequest, 1, 200);

  if (getValue(TransmissionData::GearChangeRequest) == 1)
    testStepPass("TCM responded to ECM speed signal correctly");
  else
    testStepFail("TCM did not respond within 200ms");
}
```

---

## 4. System Testing

### What is it?
Testing the **complete, integrated system** against high-level requirements and use cases. The system is treated as a black box.

### Characteristics
| Aspect | Detail |
|---|---|
| Scope | Entire system (all ECUs + vehicle) |
| Perspective | User/customer requirements |
| Environment | Vehicle, full HIL bench |
| Focus | End-to-end functionality, safety, performance |
| Tools | CANoe, HIL test automation, vehicle test equipment |
| Performed by | System test / validation engineers |

### System Test Example
**Requirement**: The vehicle shall activate Emergency Braking if an obstacle is detected within 3m at speeds > 20 km/h.

**Test Steps:**
1. Set vehicle speed to 60 km/h via HIL plant model
2. Inject radar sensor data: obstacle at 2.5 m, relative velocity = −20 km/h
3. Monitor AEB_Active signal from AEB ECU
4. Measure time from obstacle detection to brake application
5. Verify brake pressure > 80 bar within FTTI of 150 ms

---

## 5. Key Differences – Unit vs. Integration vs. System

| Factor | Unit Test | Integration Test | System Test |
|---|---|---|---|
| Scope | Single function | Multiple components | Full system |
| Isolation | Mocked dependencies | Partial mocks | No mocks – real system |
| Environment | PC/host | HIL / bench | Vehicle / full HIL |
| Feedback speed | Milliseconds | Minutes | Hours |
| Bug finding | Logic bugs | Interface bugs | Requirements bugs |
| ISO 26262 role | SW unit verification | SW/HW integration |Validation |
| ASPICE process | SWE.4 | SWE.5/SWE.6 | SYS.4 |

---

## 6. Regression Testing

**When to run:**
- After every SW build (CI pipeline)
- After ECU parameter/calibration changes
- After DBC/network changes

**Strategy:**
- Full regression suite nightly (CANoe headless, HIL)
- Smoke test subset on every commit (< 15 min run)
- Impact analysis: only run tests related to changed modules

---

## 7. Test Coverage Metrics

| Metric | Description | ASIL Requirement |
|---|---|---|
| **Statement coverage** | % of code statements executed | ASIL A |
| **Branch coverage** | % of decision branches executed | ASIL B |
| **MC/DC coverage** | Each condition independently affects outcome | ASIL C/D |
| **Requirements coverage** | % of requirements with at least one test | All ASILs |
| **DTC coverage** | % of specified DTCs triggered and verified | Safety-critical functions |

---

## 8. Defect Escape Rate

Measures quality of test process:
```
Defect Escape Rate = (Defects found post-release) / (Total defects found) × 100%

Target: < 5% for ASIL B/C, < 1% for ASIL D systems
```

---

## 9. Common Interview Questions

**Q1: What is the difference between integration and system testing?**
> Integration testing verifies that components *interface* correctly with each other (signals, protocols, AUTOSAR ports). System testing verifies the *complete system* against customer/safety requirements as a black box.

**Q2: At what test level would you catch a missing CAN signal? And a wrong torque algorithm?**
> Missing CAN signal → Integration Test (ECU communication test). Wrong torque algorithm → Unit Test (isolated function test).

**Q3: What does MC/DC coverage mean?**
> Modified Condition/Decision Coverage — each individual condition in a boolean expression must independently affect the overall decision outcome. Required for ASIL C and D software per ISO 26262.

**Q4: How do you ensure your tests cover all requirements?**
> By maintaining a **requirements-to-test traceability matrix** in a tool like Jira/DOORS/Polarion. Each requirement links to one or more test cases; coverage reports flag untested requirements.

**Q5: What is a smoke test in automotive context?**
> A fast subset of critical tests run on every build to quickly verify the system is not fundamentally broken before running the full regression suite. Typically 10-20 key test cases, < 15 min execution.
