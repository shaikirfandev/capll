# vTESTstudio Guide
## Vector vTESTstudio | Test Modules | CAPL | Python | CI Integration

---

## 1. What is vTESTstudio?

**vTESTstudio** is Vector's integrated test development environment for automated ECU and network testing. It works together with **CANoe** (test execution runtime).

**Key capabilities:**
- Structured test authoring (CAPL, Python, XML, Simulink)
- Test case management and verdict reporting
- Parameterized test execution
- XML-based test reporting (JUnit-compatible for CI)
- Signal-level and service-level testing

---

## 2. vTESTstudio Architecture

```
vTESTstudio (development)          CANoe (execution)
┌────────────────────────┐         ┌──────────────────────┐
│ Test Suite             │ ──────> │ Test Execution        │
│  ├─ Test Group 1       │  .vtx   │  ├─ Real/simulated    │
│  │   ├─ Test Case 1.1  │  file   │  │   ECU on CAN/LIN   │
│  │   └─ Test Case 1.2  │         │  └─ Results collected │
│  └─ Test Group 2       │         └──────────────────────┘
│      └─ Test Case 2.1  │
│                        │
│ CAPL Functions / Python│
│ Test Libraries         │
└────────────────────────┘
```

---

## 3. Test Structure Hierarchy

```
Test Suite (.vtsuite)
 └─ Test Group
     └─ Test Case
         └─ Test Step (pass/fail with verdict)
```

All levels can have:
- Pre-conditions (setup)
- Post-conditions (teardown)
- Parameters (data-driven testing)

---

## 4. CAPL Test Functions

```capl
/* vTESTstudio test module */
testmodule StartTest "Engine Control Tests" {

  /* Global setup */
  void StartUp() {
    write("=== Engine Control Test Suite Starting ===");
  }

  /* Global teardown */
  void TearDown() {
    write("=== Engine Control Test Suite Complete ===");
  }
}

/* Test Group */
testgroup EngineSpeedGroup() {
  
  /* Test Case 1 */
  testcase TC_EngineSpeed_IdleValid() {
    long timeout_ms = 2000;
    float expected_min = 700;
    float expected_max = 900;
    float actual;

    testStep("Precondition", "Set ignition ON and engine running");
    $IgnitionSwitch = 1;
    testWaitForTimeout(500);

    testStep("Wait for stable engine speed");
    if (testWaitForSignalInRange(Engine::Speed, expected_min, expected_max, timeout_ms)) {
      actual = getValue(Engine::Speed, float);
      testStepPass("TC_EngineSpeed_IdleValid",
                   "Engine speed %.1f RPM within range [%.0f..%.0f]",
                   actual, expected_min, expected_max);
    } else {
      actual = getValue(Engine::Speed, float);
      testStepFail("TC_EngineSpeed_IdleValid",
                   "Engine speed %.1f RPM outside range [%.0f..%.0f]",
                   actual, expected_min, expected_max);
    }
  }

  /* Test Case 2 — Parameterized */
  testcase TC_EngineSpeed_Ramp(float targetRPM, long holdTime) {
    /* Ramp to target RPM and verify */
    $AcceleratorPedal = (targetRPM - 700) / 60.0;  // Simplified mapping
    if (testWaitForSignalInRange(Engine::Speed, targetRPM*0.95, targetRPM*1.05, 3000)) {
      testStepPass("TC_EngineSpeed_Ramp",
                   "Achieved target RPM: %.0f", targetRPM);
    } else {
      testStepFail("TC_EngineSpeed_Ramp",
                   "Failed to reach target RPM: %.0f", targetRPM);
    }
    testWaitForTimeout(holdTime);
  }
}

/* Entry point — run all groups */
void MainTest() {
  EngineSpeedGroup();
}
```

---

## 5. Key CAPL Test API Functions

| Function | Description |
|----------|-------------|
| `testWaitForTimeout(ms)` | Wait for N milliseconds |
| `testWaitForMessage(id, ms)` | Wait for CAN message |
| `testWaitForSignalInRange(sig, min, max, ms)` | Wait for signal in range |
| `testWaitForSignalMatch(sig, value, tol, ms)` | Wait for exact signal value |
| `testWaitForEnvVar(var, value, ms)` | Wait for environment variable |
| `testWaitForCondition(expr, ms)` | Wait for boolean condition |
| `testStepPass(id, fmt, ...)` | Mark test step passed |
| `testStepFail(id, fmt, ...)` | Mark test step failed |
| `testCaseFail(id, fmt, ...)` | Immediately fail test case |
| `getValue(signal, type)` | Read signal value |
| `testReportAddMiscInfoBlock(title)` | Add section to report |
| `testReportAddMiscInfo(label, value)` | Add key-value to report |

---

## 6. Test Verdicts

| Verdict | Meaning |
|---------|---------|
| **Passed** | All test steps passed |
| **Failed** | At least one step failed |
| **Inconclusive** | Cannot determine (missing precondition) |
| **Error** | Test execution error (not a functional failure) |
| **Not executed** | Skipped by filter/condition |

---

## 7. Data-Driven Testing (Parameters)

```xml
<!-- vTESTstudio parameter table -->
<ParameterTable name="SpeedTestParams">
  <Row>
    <Param name="targetRPM">1500</Param>
    <Param name="holdTime">2000</Param>
  </Row>
  <Row>
    <Param name="targetRPM">3000</Param>
    <Param name="holdTime">3000</Param>
  </Row>
  <Row>
    <Param name="targetRPM">5000</Param>
    <Param name="holdTime">2000</Param>
  </Row>
</ParameterTable>
```

The test case `TC_EngineSpeed_Ramp(targetRPM, holdTime)` runs once per row automatically.

---

## 8. CI/CD Integration

vTESTstudio test results export as **JUnit XML** for use with Jenkins/GitLab CI.

### Jenkins Pipeline Example
```groovy
pipeline {
  agent any
  stages {
    stage('Run CANoe Tests') {
      steps {
        bat 'CANoe.exe /batch ECU_Tests.cfg /outputdir TestResults'
      }
    }
    stage('Publish Results') {
      steps {
        junit 'TestResults/**/*.xml'
      }
    }
  }
  post {
    always {
      archiveArtifacts 'TestResults/**'
    }
  }
}
```

### CANoe command line
```bash
CANoe.exe /batch MyTest.cfg /testcfg TestSuite.vtsuite /outputdir C:\Results
```

---

## 9. Interview Q&A

**Q: What is the difference between a Test Step and a Test Case in vTESTstudio?**
> A **Test Case** is a complete test scenario with a single verdict. A **Test Step** is one atomic check within a test case. Multiple test steps can fail but the test case continues (collecting evidence). The overall test case verdict is derived from all step verdicts.

**Q: How do you handle test dependencies in vTESTstudio?**
> Using pre-conditions in the test group setup (`StartUp`) and post-conditions in teardown (`TearDown`). If a precondition cannot be met, the test is marked Inconclusive rather than Failed. For sequential dependencies, use test group order and shared variables.

**Q: How do you integrate vTESTstudio tests into a CI pipeline?**
> CANoe runs in batch mode (`/batch` flag) executing the .vtsuite. Results are exported to JUnit XML. A CI tool (Jenkins/GitLab) ingests the XML via `junit` publisher step, tracking pass/fail trends across builds.
