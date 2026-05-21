# Avionics FMS Interview Q&A
## Boeing / Collins Aerospace / Honeywell / Thales / GE Aerospace

---

## DO-178C & Safety Standards

**Q1. What are the DO-178C Design Assurance Levels (DAL)?**  
A: DAL A–E based on failure condition severity:
- **DAL-A** — Catastrophic (e.g., loss of aircraft). Requires MC/DC coverage.
- **DAL-B** — Hazardous (e.g., large navigation error). Requires DC/MC coverage.
- **DAL-C** — Major (e.g., crew workload increase). Decision coverage.
- **DAL-D** — Minor. Statement coverage.
- **DAL-E** — No safety effect. No coverage required.
This FMS is **DAL-B** for navigation/guidance; **DAL-A** for watchdog/memory.

**Q2. What is MC/DC coverage and why does DAL-A require it?**  
A: Modified Condition/Decision Coverage. Every condition in every boolean decision must independently affect the outcome. For `if (a && b)`, must test: (T,T)→T, (T,F)→F, (F,T)→F. DAL-A requires it because catastrophic failures must have no unexercised safety logic.

**Q3. What is a Software Requirements Standard (SRS) and how does it trace to tests?**  
A: SRS defines what the software must do. Each requirement gets an ID (e.g., `SRS-NAV-001`). Tests annotate `@req SRS-NAV-001`. A Requirements Traceability Matrix (RTM) links SRS → HLD → LLD → test. This FMS uses `@req` Doxygen annotations in all test cases.

**Q4. What is the difference between verification and validation in DO-178C?**  
A: Verification — "Did we build it right?" (reviews, tests against LLD/HLD). Validation — "Did we build the right thing?" (tests against SRS, end-to-end scenarios). This FMS validates via integration tests (EGLL→KSFO scenario) and verifies via unit tests per LLD.

---

## ARINC 429

**Q5. Describe the ARINC 429 word format.**  
A: 32-bit serial word, LSB first transmitted:
- Bits 1–8: Label (octal, e.g., 0203 = pressure alt). **Bit-reversed** on bus.
- Bits 9–10: SDI (Source/Destination Identifier)
- Bits 11–28: Data (BNR = 2's complement binary, BCD = packed decimal)
- Bits 29–30: SSM (Sign/Status Matrix): 00=Failure, 01=No Computed, 10=Functional, 11=Normal Operation
- Bit 31: Parity (odd)

**Q6. How does BNR encoding work in ARINC 429?**  
A: Binary Number Representation. The MSB is the sign bit. Resolution = (range / 2^(N-1)). For altitude label 0203 with range ±131072 ft and 18 data bits: resolution = 1 ft. Value in counts = value / LSB. Encoded as 2's complement 18-bit integer in bits 11–28.

**Q7. What is the label reversal in ARINC 429?**  
A: ARINC 429 transmits the label byte LSB-first, so the label appears bit-reversed. Label 0203 octal = 0x83 = 10000011b. Reversed = 11000001b = 0xC1 = 0301 octal. Software must reverse the label byte when placing in the word.

**Q8. How do you detect a stale ARINC 429 word?**  
A: Each word has a timestamp on receipt. If no new word arrives within 2× the expected refresh rate (e.g., label 0203 at 25 Hz → timeout = 80 ms), declare the source failed. DataBusMonitor tracks `last_rx_time` per label.

---

## ARINC 664 / AFDX

**Q9. What is AFDX and how does it differ from ARINC 429?**  
A: AFDX (Avionics Full-Duplex Switched Ethernet) per ARINC 664 Part 7. Differences:
- ARINC 429: Unidirectional, 12.5/100 kbps, broadcast, one wire pair per source.
- AFDX: Bidirectional, 100 Mbps full-duplex, switched, deterministic via Virtual Links (VL) with Bandwidth Allocation Gap (BAG) 1–128 ms.
- AFDX uses dual-redundant networks (A + B) for fault tolerance.

**Q10. What is a Virtual Link in AFDX?**  
A: A VL is a logical unidirectional connection from one end-system to one or more end-systems. Each VL has a guaranteed bandwidth (BAG) and max frame size (MFS). The switch forwards frames based on VL ID. This FMS uses VL IDs for routing altitude, nav, and fuel data.

---

## CANaerospace

**Q11. What is CANaerospace?**  
A: CANaerospace v1.7 is a protocol layered on top of CAN 2.0B. 11-bit CAN IDs encode message type + node. Data frames carry: node_id, data_type, service_code, message_code, 4-byte data payload. Used for lower-criticality avionics interconnect. This FMS uses it for engine FADEC data (baro altitude, fuel flow).

---

## Navigation — RNP/ANP

**Q12. What is RNP and ANP?**  
A: 
- **RNP** (Required Navigation Performance) — regulatory requirement for containment. RNP 2.0 means 95% of time position error < 2 nm, 99.999% < 4 nm (2×RNP).
- **ANP** (Actual Navigation Performance) — FMS estimate of current position uncertainty (1-sigma). If ANP > RNP, crew gets alert and must revert to conventional navigation.

**Q13. How does this FMS compute ANP?**  
A: `ANP = 0.01 × hdop × sat_factor` in GPS_AIDED mode, where `sat_factor = 8.0 / num_sats`. In INS_ONLY, ANP grows with `rlg_drift_nm_hr × elapsed_hr`. SensorFusion EKF-based ANP = `2 × √(P[0][0] + P[1][1])` in nm.

**Q14. What is the haversine formula used for in this FMS?**  
A: Computes great-circle distance and bearing between two lat/lon positions on a sphere. Used by `NavigationEngine::compute_distance_nm()` and `compute_bearing_deg()`. XTE uses the cross-track formula: `xte = asin(sin(d12/R) × sin(θ12 − θ13))`.

---

## Sensor Fusion / EKF

**Q15. Why use an EKF for GPS/INS fusion?**  
A: INS gives high-rate (50 Hz+) position with growing error. GPS gives absolute position (1 Hz) with bounded error. EKF propagates INS state via process model, then corrects with GPS measurement. 10-state vector: [lat, lon, alt, Vn, Ve, Vd, roll, pitch, yaw, bias]. Reduces ANP vs using either alone.

**Q16. What are the EKF tuning parameters?**  
A: Process noise Q (models INS dynamics uncertainty) and measurement noise R (models GPS noise). Higher Q = trust GPS more (responsive). Lower Q = trust INS more (smooth). This FMS uses diagonal Q with position noise 1e-8°² and R with GPS noise σ=1.5e-5°.

---

## RAIM

**Q17. What is RAIM and when does it fail?**  
A: Receiver Autonomous Integrity Monitoring. GPS receiver cross-checks satellite ranges to detect faulty satellites. RAIM requires ≥5 satellites for fault detection (FD) and ≥6 for fault detection and exclusion (FDE). Fails when: HDOP > 2.0, <5 satellites visible, or satellite range residuals exceed threshold. On RAIM fail, FMS raises `GPS_RAIM_FAIL` fault.

---

## LNAV/VNAV

**Q18. Describe the LNAV guidance algorithm in this FMS.**  
A: Proportional XTE controller. `bank_cmd = Kp × XTE_nm` clamped to ±25°. Kp = 3.0 °/nm. At XTE = 8 nm → bank = 24° (near limit). Uses haversine XTE from current position to active leg. After waypoint passage (within 0.5 nm), sequences to next waypoint.

**Q19. Describe the VNAV guidance algorithm.**  
A: FPA (Flight Path Angle) tracking. Target altitude from flight plan altitude constraint. `FPA = atan2(target_alt − current_alt, dist_to_wpt_nm × 6076)`. `VS_cmd = GS × tan(FPA)` clamped to ±3000 fpm. If no constraint, tracks optimal cruise alt from PerformanceComputer.

**Q20. What triggers a missed approach in this FMS?**  
A: `execute_missed_approach()` transitions LNAV from APPROACH to HDG_SEL mode. Triggered by: runway not in sight at DH/MDA, GPWS/TAWS alert, crew input, or FMS auto-detect (descent below MDA without visual). GuidanceComputer reverts guidance to heading hold.

---

## Software Architecture

**Q21. Why use a static fault table (no dynamic allocation)?**  
A: DO-178C and IEC 61508 recommend no heap allocation in safety-critical paths. Dynamic allocation can lead to fragmentation, non-deterministic timing, and memory leaks. This FMS uses a 64-slot `FaultRecord fault_table_[64]` fixed array in FaultManager.

**Q22. What is a watchdog and why is it DAL-A in this FMS?**  
A: A hardware/software timer that must be kicked regularly. If main loop hangs (stack overflow, deadlock, infinite loop), watchdog expires and triggers reset. DAL-A because undetected loss of FMS function = catastrophic. This FMS watchdog uses `steady_clock` with 500 ms timeout.

**Q23. Explain the 6-layer architecture.**  
A: Bottom-up: (1) Common Utilities — Logger, FixedPoint, RingBuffer; (2) RTOS Abstraction — FreeRTOS HAL; (3) Communications — ARINC 429/664, CANaerospace drivers; (4) Safety — FaultManager, Watchdog, HealthMonitor; (5) Sensor Layer — ADC, INS, GPS, SensorFusion; (6) Application — Navigation, Guidance, FlightPlan, Fuel, Performance. Upper layers depend only on interfaces of lower layers.

**Q24. Why does GuidanceComputer only use interfaces (INavigationEngine, IFlightPlanManager)?**  
A: Dependency inversion principle. Guidance is tested in isolation by injecting mocks. In production, real implementations are injected. Follows DO-178C testability requirement. Prevents coupling between subsystems.

---

## Automotive → Aerospace Transition

**Q25. How does CAN relate to CANaerospace?**  
A: CAN 2.0B is the physical layer. CANaerospace adds a defined application-layer protocol: standard message IDs for avionics parameters (pressure altitude, fuel flow, etc.), node addressing, data type codes, and sequence numbering. Similar to CANopen or J1939 in automotive.

**Q26. How does UDS/OBD-II relate to DO-178C testing?**  
A: Both involve structured test requirements, fault codes, and protocol-level testing. In automotive you have ECU flashing, DTC management, and HIL simulation. In aerospace, equivalent is onboard BITE (Built-In Test Equipment), fault reporting via ARINC 429 maintenance words, and HIL with iron-bird rigs.

**Q27. How does CAPL scripting relate to avionics test automation?**  
A: CAPL (in Vector CANalyzer) scripts test ECU behavior on CAN bus — stimulate, observe, assert. In aerospace, equivalent tools include: LDRA/Polyspace for coverage, Simulink Test for model-based testing, and Python test harnesses with ARINC 429 interface boards. The test philosophy is identical: stimulus → DUT → assertion.

**Q28. What is HIL testing and how does it apply to FMS?**  
A: Hardware-In-the-Loop. Real FMS computer receives simulated sensor data (GPS, INS, ADC) via actual ARINC 429/664 buses. The simulation runs on a separate host. Validates real-time performance, bus timing, fault injection. Boeing uses Honeywell HMI iron-bird rigs for B737 FMS HIL.

---

## Protocols and Standards

**Q29. What is ARINC 424 and how does this FMS use it?**  
A: ARINC 424 defines the navigation database format: airports, runways, SIDs/STARs, airways, waypoints, NAT tracks. This FMS nav_database.json mimics ARINC 424 structure for EGLL, KSFO, and NAT Track A waypoints.

**Q30. What is RTCA DO-229F (now DO-229G)?**  
A: Minimum Operational Performance Standards for GPS SBAS airborne equipment. Defines RAIM algorithms, WAAS signal processing, protection levels. This FMS implements a simplified RAIM check (≥5 sats, HDOP ≤ 2.0) per DO-229F basic requirement.

**Q31. What is DO-254 and how does it differ from DO-178C?**  
A: DO-254 is Design Assurance Guidance for Airborne Electronic Hardware (FPGAs, ASICs, PLDs). DO-178C is for software. This FMS targets DO-178C. If the FMS ARINC 429 ASIC were in scope, DO-254 DAL-B applies.

**Q32. What is a FMEA in aerospace?**  
A: Failure Mode and Effects Analysis. For each hardware/software function, identifies: failure mode, effect on aircraft, severity, probability, and mitigation. This FMS FMEA (docs/FMEA.md) analyzes GPS failure → INS only → ANP growth → RNP exceed → crew alert → revert to conventional nav.

---

## Coding Standards

**Q33. What is MISRA C++:2008 and why is it used?**  
A: Motor Industry Software Reliability Association coding guidelines for C++. Restricts: no dynamic cast, no multiple inheritance (except interfaces), no implicit conversions, no undefined behavior constructs. Aerospace adopts it for safety-critical C++ to prevent subtle bugs in embedded systems.

**Q34. What is a FixedPoint type and why use it instead of float?**  
A: Fixed-point arithmetic uses integer with implicit scale factor. `FixedQ16` here = Q15.16 format (16 fractional bits). Advantages for safety-critical: deterministic bit pattern, no NaN/Inf, integer ALU (no FPU required on some MCUs), easier to verify. Used in this FMS for altitude deltas and fuel calculations.

---
