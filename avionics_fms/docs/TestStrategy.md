# Test Strategy Document
## Avionics FMS v3.2.1 — DO-178C DAL-B

## 1. Test Objectives

- Verify all SRS requirements are met (requirements coverage)
- Achieve DO-178C DAL-B coverage: statement + decision + MC/DC for DAL-A paths
- Demonstrate correct LNAV/VNAV guidance behavior
- Validate ARINC 429/664/CANaerospace driver correctness
- Verify fault detection and FDIR behavior
- Validate sensor fusion EKF convergence

## 2. Test Levels

### 2.1 Unit Tests (tests/unit/)
**Purpose:** Test individual classes in isolation with mocked dependencies.

| Test Suite | Class Under Test | Key Tests |
|------------|-----------------|-----------|
| test_navigation_engine.cpp | NavigationEngine | Init, haversine bearing/distance, XTE, GPS mode, RNP |
| test_arinc429.cpp | Arinc429Driver | BNR roundtrip, loopback, SSM, parity |
| test_fault_manager.cpp | FaultManager | Lifecycle, LATCHED, callback, worst_status |
| test_flight_plan_manager.cpp | FlightPlanManager | CRUD, activate, direct_to, sequence |
| test_guidance_computer.cpp | GuidanceComputer | Modes, LNAV roll limit, VNAV VS, missed approach |

### 2.2 Integration Tests (tests/integration/)
**Purpose:** Test multi-subsystem interactions.

| Test Suite | Scenario | Key Assertions |
|------------|----------|----------------|
| test_fms_integration.cpp | 30-cycle EGLL->KSFO | No faults, FP active, fuel decreases |
| test_navigation_integration.cpp | GPS/INS convergence | GPS_AIDED after 20 updates, ANP < 0.1 nm |
| test_comms_integration.cpp | Bus loopbacks | ARINC 429/AFDX/CAN roundtrips |

## 3. Coverage Requirements

| Level | Target | Tool |
|-------|--------|------|
| Statement | 100% DAL-B | gcovr |
| Decision | 100% DAL-B | gcovr --branch |
| MC/DC | 100% DAL-A (Watchdog) | Manual analysis |

## 4. Test Environment

- Host: Ubuntu 22.04 / macOS 13
- Compiler: GCC 12+ / AppleClang 17+
- Framework: GoogleTest v1.14.0 + GMock
- Coverage: gcovr 7+
- Static analysis: cppcheck 2+ / clang-tidy 15+
- CI: GitHub Actions

## 5. Requirements Traceability

Every test function has a `@req SRS-XXX-NNN` annotation. The RTM (docs/RTM.md) maps each SRS requirement to at least one test. Untested requirements fail the CI coverage gate.
