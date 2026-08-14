# Part 12 — Build & CI/CD Integration

---

## 12.1 Why CI/CD in Automotive?

Continuous Integration/Continuous Delivery (CI/CD) pipelines automate the build, test, and packaging of automotive software to:
- Detect integration failures early (within minutes of a commit)
- Ensure every build is reproducible and traceable
- Automate static analysis, unit tests, and packaging
- Enable rapid delivery to integration test environments

---

## 12.2 Source Control

### Git Branching Strategy (Automotive)

```
main ──────────────────────────────────────→ (release-ready code)
  └── develop ────────────────────────────→ (integration branch)
        ├── feature/ADAS-123-aeb-tuning
        ├── feature/CLUSTER-456-speed-display
        └── bugfix/TCU-789-mqtt-reconnect
```

- **main/master** — only release-tagged commits
- **develop** — integration of all features for current sprint
- **feature/* branches** — per-feature development, merged via Pull Request
- **release/* branches** — stabilization and regression before release

### Tagging for Releases

```
git tag -a v2.5.1 -m "Release v2.5.1: AEB improvement + cluster fix"
git push origin v2.5.1
```

---

## 12.3 Build Systems

| Tool | Use |
|---|---|
| CMake | Cross-platform build configuration; used for embedded and host builds |
| Make | Traditional Makefiles for simple builds |
| Ninja | Fast build executor, often used with CMake |
| Yocto / bitbake | Full embedded Linux image builds |
| Docker | Reproducible build environments |

### CMake Example (embedded cross-compile)

```cmake
cmake_minimum_required(VERSION 3.20)
project(adas_controller C CXX)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)

add_executable(adas_app
    src/main.c
    src/object_detection.c
    src/sensor_fusion.c
)
target_include_directories(adas_app PRIVATE include/)
target_compile_options(adas_app PRIVATE -O2 -Wall -Werror)
```

---

## 12.4 Yocto / OpenEmbedded

Yocto builds a complete embedded Linux image (including kernel, BSP, middleware, and application) for IVI, cluster, and ADAS systems.

### Yocto Recipe Example

```bitbake
# recipes-adas/adas-app/adas-app_1.0.bb
SUMMARY = "ADAS Application"
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://LICENSE;md5=abc123"

SRC_URI = "git://company-git.com/adas-app.git;branch=main"
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

inherit cmake

DEPENDS = "opencv tflite some-ip-stack"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${B}/adas_app ${D}${bindir}/
}
```

---

## 12.5 Docker for Reproducible Builds

```dockerfile
# Dockerfile for automotive embedded build environment
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    gcc-arm-none-eabi \
    cmake ninja-build python3 python3-pip \
    git curl wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install west pytest python-can

WORKDIR /workspace
CMD ["/bin/bash"]
```

---

## 12.6 CI/CD Pipeline Architecture

```
Developer pushes commit
       ↓
+------------------+
|   SCM (Git)      |  GitHub / GitLab / Azure DevOps
+------------------+
       ↓ webhook
+------------------+
|   CI Server      |  Jenkins / GitHub Actions / GitLab CI
+------------------+
       ↓
  ┌────┴────────────────────────┐
  │     Pipeline Stages:        │
  │  1. Checkout                │
  │  2. Static Analysis         │  MISRA, Polyspace, SonarQube
  │  3. Compile                 │  CMake + arm-none-eabi-gcc
  │  4. Unit Tests              │  VectorCAST / GoogleTest
  │  5. Code Coverage           │  gcov, lcov
  │  6. Package                 │  HEX + A2L + docs
  │  7. Integration Tests (SIL) │  CANoe virtual / pytest
  │  8. HIL Tests               │  dSPACE AutomationDesk
  │  9. Artifact Upload         │  Artifactory / Nexus
  │ 10. Release Notification    │  Email / Jira
  └─────────────────────────────┘
```

---

## 12.7 GitHub Actions YAML Example

```yaml
# .github/workflows/automotive-build.yml
name: Automotive ECU Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [develop]

jobs:
  build:
    runs-on: ubuntu-22.04
    container:
      image: automotive-build:latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Configure CMake
        run: |
          cmake -B build -S . \
            -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake \
            -DCMAKE_BUILD_TYPE=Release

      - name: Build
        run: cmake --build build --parallel 4

      - name: Static Analysis (MISRA)
        run: |
          cppcheck --enable=all --error-exitcode=1 \
            --addon=misra.py src/

      - name: Unit Tests
        run: |
          cmake -B build-test -S . -DBUILD_TESTS=ON
          cmake --build build-test
          cd build-test && ctest --output-on-failure

      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: adas-firmware
          path: |
            build/*.hex
            build/*.srec
            build/*.elf
```

---

## 12.8 Jenkins Pipeline Example

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker { image 'automotive-build:1.0' }
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build') {
            steps {
                sh 'cmake -B build -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake'
                sh 'cmake --build build --parallel'
            }
        }
        stage('Static Analysis') {
            steps {
                sh 'polyspace-bug-finder -sources src/ -results polyspace_results/'
                publishHTML([reportDir: 'polyspace_results/', reportFiles: 'report.html'])
            }
        }
        stage('Unit Test') {
            steps {
                sh 'cd build && ctest --output-junit test_results.xml'
                junit 'build/test_results.xml'
            }
        }
        stage('Package') {
            steps {
                sh 'python3 scripts/create_release_package.py --version ${BUILD_NUMBER}'
                archiveArtifacts artifacts: 'release/*.zip'
            }
        }
    }
    post {
        failure {
            emailext body: 'Build failed: ${BUILD_URL}', subject: 'CI Failure', to: 'team@oem.com'
        }
    }
}
```

---

## 12.9 Artifact Management

Release artifacts must be traceable:

| Artifact | Purpose | Storage |
|---|---|---|
| firmware.hex | Flashable firmware | Artifactory |
| firmware.elf | Debug-enabled binary | Artifactory |
| calibration.a2l | Calibration description | Artifactory |
| static_analysis_report.pdf | MISRA compliance | QMS |
| unit_test_report.xml | Test evidence | QMS / Artifactory |
| build_manifest.json | Version, dependencies | Artifactory |

### Build Manifest Example

```json
{
  "product": "ADAS_ECU",
  "hardware_variant": "v1A",
  "sw_version": "2.5.1",
  "build_number": "1453",
  "build_date": "2025-01-15T10:30:00Z",
  "git_commit": "a3f82d9",
  "git_branch": "release/2.5",
  "compiler": "arm-none-eabi-gcc 12.3",
  "autosar_version": "R23-11",
  "dependencies": [
    {"name": "CanStack", "version": "3.2.1"},
    {"name": "SOME/IP", "version": "1.5.0"},
    {"name": "Crypto", "version": "2.1.0"}
  ]
}
```

---

## 12.10 Automotive CI/CD Best Practices

1. **Fail fast**: static analysis and compile errors detected first
2. **Immutable artifacts**: same binary from build to release (no rebuild for release)
3. **Traceability**: every artifact linked to git commit, Jira ticket, test results
4. **Signed artifacts**: firmware signed in CI pipeline using HSM or signing service
5. **Parallel stages**: run static analysis + unit tests in parallel where possible
6. **Gate at merge**: PRs require CI green + code review before merge to develop
7. **Release gate**: release branch requires HIL test pass + QA sign-off

---

## Summary

| Area | Key Tools |
|---|---|
| Source control | Git, GitHub, GitLab |
| Build | CMake, Make, Yocto, Docker |
| CI server | Jenkins, GitHub Actions, GitLab CI |
| Static analysis | Polyspace, MISRA, SonarQube, cppcheck |
| Unit tests | VectorCAST, GoogleTest, ctest |
| Artifact repo | Artifactory, Nexus |
| Test management | Jira, DOORS, Polarion |

---

*Next: [Part 13 — Testing & Validation](part-13-testing-validation.md)*
