# 27 — Git Workflow for Automotive Software

> **Standard:** ASPICE SWE.3/SWE.6, ISO 26262-6 (traceability requirements)  
> **Tools:** Git, Gerrit (code review), Jenkins CI, JIRA (requirement tracking)

---

## 27.1 Branching Strategy

```
main (protected)
  ├── develop
  │   ├── feature/JIRA-123_lka_antiwindup
  │   ├── feature/JIRA-456_acc_cut_in
  │   └── bugfix/JIRA-789_can_byte_order
  ├── release/v2.3
  │   └── hotfix/JIRA-999_aeb_timeout_fix
  └── tags/
      └── SWB_LKA_V2.3.1   ← Software Baseline Tag
```

### Branch Rules

```
main:
  - Protected: no direct push
  - Merge only from release/* after full test campaign
  - Requires 2 approvals (Technical Lead + Safety Engineer)
  - Tag format: SWB_<FEATURE>_V<major>.<minor>.<patch>

develop:
  - Integration branch — all features merge here
  - Requires 1 approval + CI pass (build + unit tests + static analysis)
  - Nightly build runs regression suite

feature/*:
  - Branch from develop
  - Naming: feature/JIRA-<ticket>_<short_description>
  - Example: feature/JIRA-1042_lka_min_speed_adjustment

release/*:
  - Branch from develop when feature freeze
  - Only bug fixes merged into release/*
  - Full regression test campaign (SIL/HIL)
  - Release notes generated from JIRA sprint

hotfix/*:
  - Branch from main (production issue)
  - Cherry-pick fix to both main and develop
```

---

## 27.2 Commit Message Format

```
Format (ASPICE traceability):
  [<JIRA-ID>] <type>: <short description>

  <optional body — what and why (not how)>

  Refs: <JIRA-ID>
  Safety-Impact: <ASIL-A|ASIL-B|ASIL-C|ASIL-D|QM>
  Reviewed-by: <name>

Examples:
  [LKA-042] feat: Add anti-windup integrator clamp to PID controller

  Integrator was winding up during OVERRIDE state, causing torque overshoot
  on re-entry to CORRECTING. Clamp integrator to ±5 Nm·s range.
  
  Refs: LKA-042
  Safety-Impact: ASIL-C
  Reviewed-by: Hans Müller

  [DIAG-101] fix: Correct negative response code for NvM-pending DID read

  Was returning 0x31 (requestOutOfRange), should return 0x22 (conditionsNotCorrect)
  per ISO 14229-1 Table 34.
  
  Refs: DIAG-101
  Safety-Impact: QM

Types:
  feat     → new feature or enhancement
  fix      → bug fix
  test     → add or modify tests
  refactor → code restructure, no functional change
  docs     → documentation only
  chore    → build system, CI, config changes
  safety   → safety mechanism or safety requirement change
```

---

## 27.3 Code Review Checklist

```
MANDATORY checks before approval:

□ MISRA C++:2008 compliance (no new deviations without justification)
□ AUTOSAR C++14 violations addressed
□ ASIL level matches requirement (ASIL-C code = MC/DC test coverage required)
□ Unit tests added/updated for all changed functions
□ Coverage not decreased from previous baseline
□ No new unhandled return values (MISRA M0-3-2)
□ Volatile used only for hardware registers and ISR-shared variables
□ No dynamic allocation (operator new, malloc, std::vector) in safety paths
□ All pointers null-checked at function entry
□ Commit message has JIRA-ID and Safety-Impact field
□ ARXML change consistent with C++ code change (if SWC interface changed)
□ No debug printf / TODO / FIXME left in production code
□ Stack usage analysed (compiler .su file) if new task function added

For ASIL-C/D changes (additional):
□ Safety Analysis updated (FMEA or FTA row added/modified)
□ Safety Requirement ID referenced in code comment
□ E2E protection correctly applied to all affected signals
□ Independent review by Safety Engineer sign-off
```

---

## 27.4 CI/CD Pipeline (Jenkins)

```groovy
// Jenkinsfile — ADAS ECU Build Pipeline
pipeline {
    agent { label 'ubuntu-22-04' }
    
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        
        stage('Build') {
            steps {
                sh 'cmake -S . -B build -DCMAKE_BUILD_TYPE=Coverage -DBUILD_TESTS=ON'
                sh 'cmake --build build -j4'
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'ctest --test-dir build --verbose --output-on-failure'
            }
            post {
                always {
                    junit 'build/**/*.xml'
                }
            }
        }
        
        stage('Coverage') {
            steps {
                sh 'cmake --build build --target coverage'
                publishHTML([
                    reportDir: 'build/coverage_html',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
        
        stage('Static Analysis') {
            steps {
                sh 'cmake --build build --target static_analysis'
            }
        }
        
        stage('SIL Tests') {
            when { branch 'develop' }
            steps {
                sh './scripts/run_sil_regression.sh'
            }
        }
    }
    
    post {
        failure {
            emailext(
                to: 'adas-team@company.com',
                subject: "ADAS ECU Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Check ${env.BUILD_URL}"
            )
        }
    }
}
```

---

## 27.5 Software Baseline Tagging

```bash
# Create a software baseline tag (SW release):
git tag -a SWB_LKA_V2.3.1 -m "Software Baseline: LKA V2.3.1
  - Anti-windup integrator clamp (LKA-042)
  - MISRA deviation justified for goto in state machine (MISRA-007)
  - Coverage: 94.2% branch coverage (LKA SWC)
  - ISO 26262 evidence package: docs/safety/LKA_V2.3.1_Safety_Evidence.pdf
  - Tested: HIL suite 100% pass, SIL suite 100% pass
  - Release date: 2024-01-15
  - Sign-off: Safety Engineer, Software Lead, Product Owner"

git push origin SWB_LKA_V2.3.1

# List all SW baselines:
git tag -l "SWB_*" | sort -V
```

---

## 27.6 Interview Questions

**L1:**
1. What is a software baseline in automotive projects?
2. Why do commit messages reference JIRA tickets?
3. What is a protected branch and why is main protected?

**L2:**
4. Describe the full flow from a bug ticket to a hotfix release.
5. What fields would you add to a commit message for ASPICE traceability?
6. How do you enforce commit message format and code review rules in Git?

**L3:**
7. Design the CI/CD pipeline for an ASIL-D automotive component.
8. How do you manage divergence between develop and release branches during a long release stabilisation phase?
9. What change management evidence is required by ISO 26262-6 for software modification?
10. How do you handle a MISRA deviation that is justified but requires sign-off from the Safety Manager?
