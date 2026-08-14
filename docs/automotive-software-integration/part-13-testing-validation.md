# Part 13 — Testing & Validation

---

## 13.1 Test Levels Overview

```
Vehicle Testing (VEHIL)
    ↑
System / Vehicle Integration Testing
    ↑
HIL (Hardware-in-the-Loop)
    ↑
ECU Integration Testing
    ↑
Software Integration Testing
    ↑
SIL (Software-in-the-Loop)
    ↑
MIL (Model-in-the-Loop)
    ↑
Unit Testing
    ↑
Component Testing
```

---

## 13.2 Test Level Definitions

| Level | Environment | Purpose |
|---|---|---|
| Unit Test | Host PC | Test individual functions/modules |
| Component Test | Host PC or target | Test a software component |
| MIL | MATLAB/Simulink | Test models against requirements |
| SIL | PC with target software | Test software with simulated hardware |
| HIL | ECU + hardware simulator | Test ECU with simulated vehicle |
| ECU Integration | Bench with real ECUs | Test ECU with other real ECUs |
| System Test | HIL or vehicle | Test complete system |
| Vehicle Test | Real vehicle | Final validation |

---

## 13.3 Unit Testing

**Objective:** Verify each function/module works in isolation.

**Framework example: VectorCAST (for C/C++ embedded):**
```c
// Test case: verify speed_to_rpm_conversion returns correct value
TEST(SpeedConversionTest, NormalSpeed) {
    float rpm = speed_to_rpm(80.0f);  // 80 km/h
    EXPECT_NEAR(rpm, 2400.0f, 1.0f);  // expect 2400 RPM within 1 RPM
}

TEST(SpeedConversionTest, ZeroSpeed) {
    float rpm = speed_to_rpm(0.0f);
    EXPECT_EQ(rpm, 0.0f);
}
```

**Code coverage requirements:**
- Safety-critical (ASIL-D): 100% MC/DC (Modified Condition/Decision Coverage)
- Safety-relevant (ASIL-B): 100% branch coverage
- QM (non-safety): statement coverage ≥ 80%

---

## 13.4 HIL (Hardware-in-the-Loop) Testing

HIL replaces real vehicle sensors and actuators with a simulator:

```
+-------------------+       +-------------------+
|   HIL Simulator   |       |   ECU under test  |
| (dSPACE/NI/ETAS)  |       |                   |
|                   |←CAN→  |  Application      |
| Vehicle dynamics  |←ETH→  |  AUTOSAR BSW      |
| sensor simulation |←GPIO→ |  MCAL drivers     |
| fault injection   |       |                   |
+-------------------+       +-------------------+
         ↑
    +----------------+
    | Automation PC  |
    | dSPACE Auto-   |
    | mationDesk or  |
    | CANoe          |
    +----------------+
```

### HIL Test Types

| Test Type | Purpose |
|---|---|
| Functional | Verify feature behavior (ACC maintains distance) |
| Regression | Re-run all tests after software change |
| Stress | Run at maximum load/temperature |
| Fault injection | Inject sensor faults, verify ECU reaction |
| Boundary | Test at min/max signal values |
| Endurance | Run for 100+ hours continuously |

---

## 13.5 CANoe Test Automation (CAPL)

```c
// CANoe CAPL: automated test of ACC speed following
variables {
  float targetSpeed = 80.0; // km/h
  float followingVehicleSpeed = 60.0;
}

testcase TC_ACC_01_SpeedFollowing() {
  // Set up: ego vehicle at 80 km/h, lead vehicle at 60 km/h
  $BrakeCtrl::TargetSpeed = targetSpeed;
  $RadarSim::LeadVehicleSpeed = followingVehicleSpeed;
  
  // Wait for ACC to reduce speed
  testWaitForTimeout(5000); // 5 seconds
  
  // Verify: ego speed should decrease toward 60 km/h
  float egoSpeed = $Cluster::VehicleSpeed;
  if (egoSpeed < 65.0) {
    testStepPass("ACC_SpeedReduced", "Ego reduced to: %.1f km/h", egoSpeed);
  } else {
    testStepFail("ACC_SpeedReduced", "Ego speed still: %.1f km/h", egoSpeed);
  }
}
```

---

## 13.6 Python Automated Testing with python-can

```python
import can
import time
import pytest

@pytest.fixture
def can_bus():
    bus = can.Bus(interface='socketcan', channel='vcan0', bitrate=500000)
    yield bus
    bus.shutdown()

def test_engine_speed_signal_presence(can_bus):
    """Verify EngineSpeed signal is broadcast every 10ms"""
    received = []
    start = time.time()
    
    while time.time() - start < 1.0:  # collect 1 second of messages
        msg = can_bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == 0x0C8:  # EngineSpeed message ID
            received.append(msg)
    
    # Should receive ~100 messages in 1 second (10ms period)
    assert 90 <= len(received) <= 110, \
        f"Expected ~100 EngineSpeed messages, got {len(received)}"

def test_vehicle_speed_encoding(can_bus):
    """Verify VehicleSpeed signal encoding: 80 km/h = raw 320"""
    msg = None
    for _ in range(100):
        m = can_bus.recv(timeout=0.05)
        if m and m.arbitration_id == 0x0C9:
            msg = m
            break
    
    assert msg is not None, "VehicleSpeed message not received"
    # Decode: bytes 0-1, Intel byte order, scaling 0.25
    raw = (msg.data[1] << 8) | msg.data[0]
    speed_kmh = raw * 0.25
    assert 75.0 <= speed_kmh <= 85.0, f"Speed out of range: {speed_kmh}"
```

---

## 13.7 Test Strategy

### V-Model Alignment

```
Requirements ─────────────────────────────→ System Test
  System Architecture ─────────────────→ Integration Test
    Software Architecture ─────────→ Software Integration Test
      Detailed Design ─────────→ Component / Unit Test
```

### Test Planning Artifacts

| Artifact | Content |
|---|---|
| Test Plan | Scope, resources, schedule, entry/exit criteria |
| Test Specification | Test cases with inputs, steps, expected results |
| Test Report | Pass/fail results, metrics, defect references |
| Traceability Matrix | Test case → requirement mapping |

---

## 13.8 Defect Lifecycle

```
New → Assigned → Open → Fixed → Verified → Closed
           ↓                       ↓
        Rejected               Rejected (reopened)
```

Defect fields:
- Title, description, steps to reproduce
- Severity (Critical / Major / Minor / Trivial)
- Priority (P1/P2/P3)
- Component, ECU, SW version
- Root cause, fix description

---

## 13.9 Regression Testing

After every software change, regression tests ensure no new failures were introduced:

```
Full regression: run all HIL test cases (~500 test cases, 4 hours on HIL)
Smoke regression: run subset of critical test cases (~50 cases, 30 minutes)
Sanity: run 5-10 most critical tests after flash, before starting full regression
```

---

## 13.10 Performance and Endurance Testing

| Test | Target | Method |
|---|---|---|
| CPU load | < 70% average | Profile with trace tools |
| Memory usage | < 80% RAM | Runtime memory monitoring |
| Task execution time | Within WCET budget | Trace32 timing measurement |
| Endurance | 500 hours continuous | HIL soak test |
| Temperature sweep | -40°C to +85°C | Climatic chamber + HIL |

---

## Summary

| Level | Tool | Metric |
|---|---|---|
| Unit Test | VectorCAST, GoogleTest | MC/DC coverage |
| MIL/SIL | Simulink, CANoe virtual | Functional coverage |
| HIL | dSPACE, CANoe | Test case pass rate |
| Vehicle | Data logger, CANoe | System-level requirements |
| Automation | Python + pytest, CAPL | Regression pass rate |

---

*Next: [Part 14 — Tools](part-14-tools.md)*
