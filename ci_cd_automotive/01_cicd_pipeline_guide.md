# CI/CD for Automotive Test Automation
## Jenkins, GitLab CI, and Docker for Embedded/Automotive Testing

---

## 1. Why CI/CD in Automotive?

Modern automotive software development involves:
- Multiple ECUs developed by distributed teams
- Nightly integration builds across hundreds of SWCs
- ISO 26262 requires **traceability** from requirements → tests → results
- Regression test suites run on HIL, SIL, or CAPL simulators

**CI/CD enables:**
- Automated builds triggered on every commit
- Automatic test execution (SIL/HIL/CAPL)
- Instant developer feedback on regressions
- Traceability for ASPICE and ISO 26262 audits
- Reproducible builds (Docker-based environments)

---

## 2. CI/CD Pipeline for Automotive Testing

```
Developer Push
      │
      ▼
┌─────────────────────────────────────────────────┐
│  CI Pipeline                                     │
│                                                  │
│  1. Code Checkout (Git)                          │
│  2. Static Analysis (PC-lint, MISRA, Polyspace)  │
│  3. Compile (cross-compiler for target ECU)      │
│  4. Unit Tests (GoogleTest / CAPL test modules)  │
│  5. SIL Tests (CANoe headless simulation)        │
│  6. Coverage Report (gcov / LDRA / VectorCAST)  │
│  7. HIL Test Trigger (dSPACE AutomationDesk)     │
│  8. Test Report Generation (HTML + XML)          │
│  9. Artifact Archive (BLF logs, reports)         │
│  10. Notification (Email / Slack / Teams)        │
└─────────────────────────────────────────────────┘
      │
      ▼ (if all pass)
 CD: Deploy firmware to test fleet / HIL systems
```

---

## 3. GitLab CI Example – Automotive C Build + CAPL Tests

### `.gitlab-ci.yml`
```yaml
stages:
  - static_analysis
  - build
  - unit_test
  - sil_test
  - report

variables:
  COMPILER: "arm-none-eabi-gcc"
  CANoe_PATH: "C:/Program Files/Vector CANoe 16/Exec64/CANoe64.exe"
  TEST_CFG: "tests/canoe/Engine_SIL_Test.cfg"

# ---- Stage 1: Static Analysis ----
misra_check:
  stage: static_analysis
  tags: [windows-build-agent]
  script:
    - echo "Running MISRA C check with PC-lint..."
    - lint-nt.exe +v engine_control.c > lint_report.txt
  artifacts:
    paths: [lint_report.txt]
    expire_in: 7 days

# ---- Stage 2: Build ----
compile_ecu:
  stage: build
  tags: [windows-build-agent]
  script:
    - echo "Cross-compiling ECU firmware..."
    - make -f Makefile.ecu TARGET=EngineECU all
  artifacts:
    paths: [build/EngineECU.elf, build/EngineECU.hex]
    expire_in: 30 days

# ---- Stage 3: Unit Tests ----
unit_tests:
  stage: unit_test
  tags: [linux-agent]
  script:
    - cd tests/unit
    - cmake . -B build && cmake --build build
    - ./build/engine_unit_tests --gtest_output="xml:unit_test_results.xml"
  artifacts:
    reports:
      junit: tests/unit/unit_test_results.xml

# ---- Stage 4: SIL Test via CANoe Headless ----
sil_canoe_test:
  stage: sil_test
  tags: [windows-canoe-agent]  # Agent with CANoe license
  script:
    - echo "Starting CANoe SIL test..."
    - |
      & "$env:CANoe_PATH" /run "$env:TEST_CFG" /outputpath "results/" /quit
  artifacts:
    paths:
      - results/*.xml
      - results/*.html
      - results/*.blf
    expire_in: 14 days

# ---- Stage 5: Publish Report ----
publish_report:
  stage: report
  tags: [linux-agent]
  script:
    - python3 scripts/generate_summary.py results/
  artifacts:
    paths: [results/summary_report.html]
    expose_as: "Test Summary Report"
```

---

## 4. Jenkins Pipeline Example

### `Jenkinsfile`
```groovy
pipeline {
    agent { label 'windows-canoe-agent' }

    environment {
        CANOE_EXE  = 'C:\\Program Files\\Vector CANoe 16\\Exec64\\CANoe64.exe'
        TEST_CFG   = 'tests\\Engine_HIL_Test.cfg'
        RESULTS    = 'results\\'
    }

    triggers {
        // Run every night at 11 PM
        cron('0 23 * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Analysis') {
            steps {
                bat '''
                    echo Running MISRA check...
                    polyspace-bug-finder-server.exe -sources src/ -results-dir polyspace_results/
                '''
            }
        }

        stage('Build') {
            steps {
                bat 'make -C build/ all'
            }
        }

        stage('CANoe SIL Test') {
            steps {
                bat """
                    "%CANOE_EXE%" /run "%TEST_CFG%" /outputpath "%RESULTS%" /quit
                    echo CANoe test completed with exit code: %ERRORLEVEL%
                """
            }
        }

        stage('Parse Results') {
            steps {
                junit 'results/*.xml'
                publishHTML(target: [
                    allowMissing: false,
                    reportDir: 'results',
                    reportFiles: 'TestReport.html',
                    reportName: 'CANoe Test Report'
                ])
            }
        }
    }

    post {
        failure {
            emailext(
                to: 'automotive-test-team@company.com',
                subject: "BUILD FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Check Jenkins: ${env.BUILD_URL}"
            )
        }
        success {
            slackSend(
                channel: '#automotive-ci',
                message: "✅ Build ${env.BUILD_NUMBER} PASSED - ${env.JOB_NAME}"
            )
        }
    }
}
```

---

## 5. CANoe Headless (Command-Line) Execution

CANoe supports headless execution for CI pipelines:

```batch
REM Run CANoe test headlessly and exit
"C:\Program Files\Vector CANoe 16\Exec64\CANoe64.exe" ^
  /run "Engine_Test.cfg" ^
  /outputpath "C:\CI_Results\" ^
  /quit

REM Check exit code
IF %ERRORLEVEL% NEQ 0 (
    echo CANoe test FAILED
    exit /b 1
) ELSE (
    echo CANoe test PASSED
)
```

**CANoe command-line switches:**
| Switch | Description |
|---|---|
| `/run <cfg>` | Open and start measurement |
| `/outputpath <dir>` | Directory for test results |
| `/quit` | Exit after measurement ends |
| `/nolicensehardwarecheck` | Skip hardware check (for SIL) |
| `/nobackupcreation` | Don't create cfg backups |

---

## 6. Docker for Reproducible Builds

Containerize the build environment to avoid "works on my machine" issues:

### `Dockerfile` (Linux cross-compile agent)
```dockerfile
FROM ubuntu:22.04

# Install ARM cross-compiler and build tools
RUN apt-get update && apt-get install -y \
    gcc-arm-none-eabi \
    binutils-arm-none-eabi \
    make \
    cmake \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python test dependencies
RUN pip3 install python-can pytest pytest-html

# Set working directory
WORKDIR /workspace

CMD ["/bin/bash"]
```

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  build-agent:
    build: .
    volumes:
      - .:/workspace
      - ./results:/workspace/results
    environment:
      - BUILD_TARGET=EngineECU
    command: make -C /workspace/build all

  unit-test-agent:
    build: .
    volumes:
      - .:/workspace
    command: bash -c "cd /workspace/tests && pytest -v --html=results/unit_test_report.html"
```

---

## 7. Python-Based Test Result Parser

```python
#!/usr/bin/env python3
"""
Parse CANoe XML test report and summarize results.
"""

import xml.etree.ElementTree as ET
import sys
import os

def parse_canoe_report(xml_path: str) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "test_cases": []
    }

    for testcase in root.findall(".//testcase"):
        name    = testcase.get("name", "Unknown")
        verdict = testcase.get("verdict", "unknown").lower()

        results["total"] += 1
        if verdict == "passed":
            results["passed"] += 1
        elif verdict == "failed":
            results["failed"] += 1
        else:
            results["errors"] += 1

        results["test_cases"].append({
            "name": name,
            "verdict": verdict
        })

    return results

def generate_summary(results_dir: str):
    all_results = {"total": 0, "passed": 0, "failed": 0, "errors": 0}

    for fname in os.listdir(results_dir):
        if fname.endswith(".xml"):
            r = parse_canoe_report(os.path.join(results_dir, fname))
            for k in all_results:
                all_results[k] += r[k]

    print("=" * 50)
    print("  AUTOMOTIVE CI/CD TEST SUMMARY")
    print("=" * 50)
    print(f"  Total   : {all_results['total']}")
    print(f"  Passed  : {all_results['passed']}")
    print(f"  Failed  : {all_results['failed']}")
    print(f"  Errors  : {all_results['errors']}")
    pass_rate = (all_results['passed'] / all_results['total'] * 100) if all_results['total'] > 0 else 0
    print(f"  Pass Rate: {pass_rate:.1f}%")
    print("=" * 50)

    # Exit non-zero if any failures (triggers CI failure)
    if all_results['failed'] > 0 or all_results['errors'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    generate_summary(results_dir)
```

---

## 8. ASPICE and Traceability

**ASPICE** (Automotive SPICE) Level 2 requires traceability matrices:

| Artifact | Tool |
|---|---|
| Requirements | DOORS / Polarion / Jira |
| Test Cases | Jira Xray / vTESTstudio |
| Test Results | CANoe XML reports |
| Code Coverage | LDRA / VectorCAST / gcov |
| CI Evidence | Jenkins artifacts / GitLab pipelines |

**Traceability chain:**
```
System Requirement → Software Requirement → Test Case → Test Result → Pass/Fail
```

All links stored in a requirements management tool; CI artifacts provide evidence.

---

## 9. Common Interview Questions

**Q1: How do you integrate CANoe tests into a CI pipeline?**
> CANoe supports headless execution via command line. In Jenkins/GitLab, we call CANoe.exe with `/run` and `/quit` flags on a licensed agent, capture the XML output, and parse it with JUnit reporter or custom scripts.

**Q2: Why use Docker in automotive CI?**
> To ensure reproducible build environments — same compiler version, same libraries, same OS — regardless of which build agent runs the job, eliminating "works on my machine" issues.

**Q3: What is the difference between SIL and HIL in a CI pipeline?**
> SIL runs automatically on any agent (no special hardware). HIL requires physical ECU hardware on a test bench, so HIL jobs use dedicated tagged agents. SIL runs on every commit; HIL typically runs nightly.

**Q4: How do you handle license management in CANoe CI?**
> Vector licenses are USB dongle or network-based. In CI, use a dedicated network license server (floating licenses) and assign specific Jenkins/GitLab agents to use CANoe — only those agents have license access.
