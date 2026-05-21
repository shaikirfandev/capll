# Resume Points — Avionics FMS Project
## Targeting: Boeing, Collins Aerospace, Honeywell Aerospace, Thales, GE Aerospace, Safran, Raytheon

---

## ATS-Optimized Bullet Points

### For "Software Engineer / Embedded Software Engineer" roles:

- Designed and implemented a **production-grade Flight Management System (FMS) in C++17** targeting B737-800 operations, compliant with **DO-178C DAL-B** standards
- Developed **ARINC 429 BNR encode/decode driver** with odd parity, SSM field, and label reversal; validated via 40+ unit tests using GoogleTest/GMock
- Implemented **dual-redundant AFDX driver** per ARINC 664 Part 7 with Virtual Link routing and Network A/B failover for 100 Mbps avionics Ethernet
- Built **10-state Extended Kalman Filter** fusing GPS and INS sensor data, achieving ANP convergence < 0.1 nm after 20 update cycles
- Designed **RAIM integrity monitoring** per DO-229F: ≥5 satellites + HDOP ≤ 2.0, raising `GPS_RAIM_FAIL` fault on integrity breach
- Implemented **FaultManager with static 64-slot fault table** (no heap allocation), INACTIVE→ACTIVE→LATCHED lifecycle, CRITICAL auto-latch, and fault callbacks
- Developed **LNAV proportional XTE controller** (±25° bank limit, Kp=3 °/nm) and **VNAV FPA-based vertical speed command** (±3000 fpm) with missed-approach sequencing
- Implemented **haversine great-circle navigation**: bearing, distance (EGLL→KSFO ~4900 nm), cross-track error computation
- Designed **hardware watchdog simulation** (DAL-A) with `steady_clock` kick tracking and 500 ms expiry detection
- Built **6-layer avionics software architecture** (Application / Sensor / Communications / Safety / RTOS / Common) with pure virtual interfaces for dependency injection
- Configured **multi-platform CMake build system** (C++17, FetchContent: GoogleTest, spdlog, nlohmann_json) with ASAN/UBSAN/coverage flags
- Established **GitHub Actions CI/CD pipeline** on Ubuntu 22.04 + macOS 13 with build, test, coverage (gcovr), and cppcheck/clang-tidy static analysis stages
- Wrote **30+ unit tests** across 5 test suites (NavigationEngine, ARINC 429, FaultManager, FlightPlanManager, GuidanceComputer) with `@req` traceability annotations
- Implemented **FreeRTOS task abstraction** using `std::thread` simulation (host) with task lifecycle: create → start → stop → suspend → resume

### For "Test Automation / Validation Engineer" roles:

- Authored **unit + integration test suite (40+ tests)** using GoogleTest/GMock with `@req SRS-*` traceability to Software Requirements Specification
- Implemented **ARINC 429 loopback test**: encode altitude 35,000 ft → transmit → RX callback → decode; verified round-trip accuracy ≤ 1 ft
- Built **CANaerospace loopback integration test**: transmit float payload via CAN 2.0B → receive callback → memcpy decode; validated bit-exact round-trip
- Designed **sensor fusion convergence tests**: GPS/INS EKF update × 20 → verify NavMode::GPS_AIDED, ANP < 0.1 nm, RNP satisfied
- Created **fault lifecycle integration tests**: WARNING→ACTIVE, CRITICAL→LATCHED (non-clearable), callback fire, worst-status aggregate
- Configured **gcovr HTML coverage report generation** for DO-178C DAL-B coverage artifacts
- Implemented **Docker multi-stage build** (builder + tester + runtime) for reproducible CI test execution

---

## LinkedIn / Profile Summary (100 words)

> Embedded software engineer with 5+ years automotive (CAN/UDS/Vector tools/ECU) transitioning into safety-critical avionics. Built full Flight Management System in C++17: ARINC 429/664/CANaerospace drivers, GPS/INS EKF sensor fusion, RAIM, LNAV/VNAV guidance, DO-178C DAL-B fault management. Proven ability to deliver production-quality embedded C++ with no dynamic allocation, static analysis (cppcheck/clang-tidy), and 40+ unit tests with requirements traceability. Seeking avionics embedded role at Boeing / Collins Aerospace / Honeywell.

---

## HR Interview Answers

**"Why aerospace after automotive?"**  
> "In automotive I mastered real-time embedded systems, CAN protocol stack, UDS diagnostics, and HIL validation. The engineering disciplines are identical — deterministic scheduling, bus protocols, fault management — but aerospace applies stricter formal standards (DO-178C vs ISO 26262) and longer system lifetimes. I built this FMS to demonstrate I can apply those standards to ARINC 429/664, GPS/INS fusion, and LNAV/VNAV guidance computation."

**"What DO-178C experience do you have?"**  
> "I self-studied DO-178C and implemented DAL-B compliance in this FMS: requirements traceability via @req annotations linking SRS to tests, coverage targets met via gcovr, static analysis via cppcheck, fault management with INACTIVE/ACTIVE/LATCHED lifecycle, no dynamic allocation in safety paths, and watchdog at DAL-A. I understand the difference between verification (tests against LLD) and validation (scenario tests against SRS)."

**"Describe a complex algorithm you implemented."**  
> "The 10-state EKF in SensorFusion: state vector [lat, lon, alt, Vn, Ve, Vd, roll, pitch, yaw, accel_bias]. Process model propagates INS state. Measurement update uses GPS lat/lon/alt as observations. Kalman gain per axis as K = P × H^T × (H × P × H^T + R)^-1. After 20 GPS updates, ANP converges below 0.1 nm. All state operations use static arrays to avoid heap allocation."

---

## Skills Keywords (ATS-optimized)

DO-178C, DO-254, RTCA DO-229, ARINC 429, ARINC 664, AFDX, CANaerospace, CAN 2.0B, J1939, UDS, ISO 26262, MISRA C++, C++17, C11, CMake, GoogleTest, GMock, Extended Kalman Filter, RAIM, RNP/ANP, LNAV, VNAV, FMS, GPS, INS, Sensor Fusion, FreeRTOS, VxWorks, Watchdog, HIL, BITE, FMEA, RTM, Safety-Critical, Embedded Systems, Real-Time, Static Analysis, cppcheck, clang-tidy, GitHub Actions, Docker, Python, Vector CANalyzer, CAPL, spdlog, nlohmann_json, gcovr
