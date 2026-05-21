b# Avionics FMS — Feature Development Mart
## Ticket × Implementation × Test Traceability Matrix

> **Version:** FMS v3.2.1  
> **Standard:** DO-178C DAL-B  
> **Total Tests:** 47 (47/47 passing)  
> **Coverage key:** ✅ Covered | ⚠️ Partial | ❌ Not Covered

---

## 1. Full Traceability Matrix

| Ticket | Feature Name | SRS Ref | Impl File(s) | Interface | Unit Tests | Integration Tests | Status |
|--------|-------------|---------|-------------|-----------|-----------|------------------|--------|
| FMS-001 | Haversine Distance / Bearing / XTE | SRS-NAV-001/002 | `src/fms/NavigationEngine.cpp` | `INavigationEngine.hpp` | #2 BearingEgllKsfo, #3 DistanceEgllKsfo, #4 XteZeroOnTrack | #39 NavModeGpsAided | ✅ |
| FMS-002 | GPS-Aided Position + ANP | SRS-NAV-003 | `src/fms/NavigationEngine.cpp` | `INavigationEngine.hpp` | #5 GpsModeSwitch, #6 RnpSatisfied, #7 RnpExceeded | #40 AnpConvergesAfterGpsUpdates, #41 RnpSatisfiedAfterConvergence | ✅ |
| FMS-003 | RNP Monitoring | SRS-NAV-004 | `src/fms/NavigationEngine.cpp` | `INavigationEngine.hpp` | #6 RnpSatisfied, #7 RnpExceeded | #41 RnpSatisfiedAfterConvergence | ✅ |
| FMS-004 | ADC Integration | SRS-NAV-005 | `src/fms/NavigationEngine.cpp` | `INavigationEngine.hpp` | #8 AdcUpdate | — | ✅ |
| FMS-005 | Embedded Nav Database | SRS-FPM-001 | `src/fms/FlightPlanManager.cpp` | `IFlightPlanManager.hpp` | #24 FindWaypointNotFound, #25 FindWaypointFound | — | ✅ |
| FMS-006 | Waypoint Insert / Delete | SRS-FPM-002/003 | `src/fms/FlightPlanManager.cpp` | `IFlightPlanManager.hpp` | #23 ActivateSucceedsWith2Wpts, #26 DeleteReducesCount | #37 FlightPlanStaysActive | ✅ |
| FMS-007 | Flight Plan Activation | SRS-FPM-004 | `src/fms/FlightPlanManager.cpp` | `IFlightPlanManager.hpp` | #22 ActivateFailsLessThan2Wpts, #23 ActivateSucceedsWith2Wpts | #36 ThirtyCyclesNoFault, #37 FlightPlanStaysActive | ✅ |
| FMS-008 | Waypoint Sequencing | SRS-FPM-005 | `src/fms/FlightPlanManager.cpp` | `IFlightPlanManager.hpp` | #28 SequenceAdvancesIndex | — | ✅ |
| FMS-009 | Direct-To Intercept | SRS-FPM-006 | `src/fms/FlightPlanManager.cpp` | `IFlightPlanManager.hpp` | #27 DirectTo | — | ✅ |
| FMS-010 | LNAV Roll Command (XTE→Bank) | SRS-GUID-001/002 | `src/fms/GuidanceComputer.cpp` | `IGuidanceComputer.hpp` | #31 LnavRollWithinLimit | #36 ThirtyCyclesNoFault | ✅ |
| FMS-011 | VNAV VS Command (Alt Target) | SRS-GUID-003 | `src/fms/GuidanceComputer.cpp` | `IGuidanceComputer.hpp` | #32 VnavDescentBelowTargetAlt, #33 VnavClimbAboveTargetAlt | #36 ThirtyCyclesNoFault | ✅ |
| FMS-012 | Missed Approach Procedure | SRS-GUID-004 | `src/fms/GuidanceComputer.cpp` | `IGuidanceComputer.hpp` | #34 MissedApproachEngagesHdgSel | — | ✅ |
| FMS-013 | Direct-To Guidance Mode | SRS-GUID-005 | `src/fms/GuidanceComputer.cpp` | `IGuidanceComputer.hpp` | #30 SetLnavMode | — | ✅ |
| FMS-014 | Fuel Burn Tracking | SRS-FUEL-001 | `src/fms/FuelManagement.cpp` | `IFuelManagement.hpp` | — | #38 FuelDecreases | ✅ |
| FMS-015 | Fuel Imbalance / Low-Fuel Warnings | SRS-FUEL-002 | `src/fms/FuelManagement.cpp` | `IFuelManagement.hpp` | — | — | ⚠️ No dedicated unit test |
| FMS-016 | Optimum Cruise Altitude | SRS-PERF-001 | `src/fms/PerformanceComputer.cpp` | `IPerformanceComputer.hpp` | — | #36 ThirtyCyclesNoFault, #38 FuelDecreases | ✅ |
| FMS-017 | Cruise / Climb Fuel Flow Model | SRS-PERF-002 | `src/fms/PerformanceComputer.cpp` | `IPerformanceComputer.hpp` | — | #38 FuelDecreases | ✅ |
| FMS-018 | GPS Receiver + RAIM | SRS-SENS-001 | `src/sensors/GpsReceiver.cpp` | `IGpsReceiver.hpp` | — | #39 NavModeGpsAided, #40 AnpConverges | ✅ |
| FMS-019 | INS + Schuler Drift | SRS-SENS-002 | `src/sensors/InertialNavSystem.cpp` | `IInertialNavSystem.hpp` | — | #42 SensorFusionProducesValidPosition | ✅ |
| FMS-020 | Air Data Computer | SRS-SENS-003 | `src/sensors/AirDataSystem.cpp` | `IAirDataSystem.hpp` | — | #36 ThirtyCyclesNoFault | ✅ |
| FMS-021 | 10-State EKF Sensor Fusion | SRS-SENS-004 | `src/sensors/SensorFusion.cpp` | — | — | #40 AnpConverges, #41 RnpSatisfied, #42 SensorFusionProducesValidPosition | ✅ |
| FMS-022 | Fault Report / Escalation / Callback | SRS-SAFE-001 | `src/safety/FaultManager.cpp` | `IFaultManager.hpp` | #16 ReportWarningFaultActive, #20 CallbackFires, #21 OccurrenceCountIncrements | #36 ThirtyCyclesNoFault | ✅ |
| FMS-023 | Fault Clear + Latch Protection | SRS-SAFE-002 | `src/safety/FaultManager.cpp` | `IFaultManager.hpp` | #17 CriticalFaultLatched, #18 WarningFaultClearable, #19 WorstStatusReflectsSeverity | — | ✅ |
| FMS-024 | BITE + Health Monitor | SRS-SAFE-003 | `src/safety/HealthMonitor.cpp` | `IHealthMonitor.hpp` | — | — | ⚠️ No dedicated test |
| FMS-025 | Software Watchdog | SRS-SAFE-004 | `src/safety/Watchdog.cpp` | `IWatchdog.hpp` | — | — | ⚠️ No dedicated test |
| FMS-026 | ARINC 429 BNR Encode/Decode | SRS-COMM-001 | `src/comms/Arinc429Driver.cpp` | `IArinc429.hpp` | #9 BnrRoundtripAlt35000, #10 BnrRoundtripNegAlt, #11 BnrRoundtripAirspeed | #43 Arinc429Loopback | ✅ |
| FMS-027 | ARINC 429 RX Callback Loopback | SRS-COMM-002 | `src/comms/Arinc429Driver.cpp` | `IArinc429.hpp` | #12 RxCallbackFires, #13 SsmNormalOp, #14 StatusNormalAfterInit | #43 Arinc429Loopback, #47 Arinc429StatusNormal | ✅ |
| FMS-028 | AFDX Dual-Network Transmit | SRS-COMM-003 | `src/comms/Arinc664Driver.cpp` | `IArinc664.hpp` | — | #44 AfdxTransmit | ✅ |
| FMS-029 | CANaerospace Driver | SRS-COMM-004 | `src/comms/CanAerospaceDriver.cpp` | `ICanAerospace.hpp` | — | #45 CanAeroTransmit, #46 CanAeroLoopback | ✅ |
| FMS-030 | Data Bus Health Monitor | SRS-COMM-005 | `src/comms/DataBusMonitor.cpp` | — | — | — | ⚠️ No dedicated test |
| FMS-031 | RTOS Task Abstraction | SRS-RTOS-001 | `src/rtos/FreeRtosTask.cpp` | `IRtosTask.hpp` | — | — | ⚠️ No test |
| FMS-032 | RTOS Mutex | SRS-RTOS-002 | `src/rtos/FreeRtosMutex.cpp` | — | — | — | ⚠️ No test |
| FMS-033 | RTOS Queue | SRS-RTOS-003 | `src/rtos/FreeRtosQueue.cpp` | — | — | — | ⚠️ No test |
| FMS-034 | RTOS Timer | SRS-RTOS-004 | `src/rtos/FreeRtosTimer.cpp` | — | — | — | ⚠️ No test |
| FMS-035 | Logger | — | `src/common/Logger.cpp` | `Logger.hpp` | — | — | ⚠️ No test |
| FMS-036 | Ring Buffer | — | `src/common/RingBuffer.cpp` | `RingBuffer.hpp` | — | — | ⚠️ No test |
| FMS-037 | Fixed-Point Arithmetic | — | `src/common/FixedPoint.cpp` | `FixedPoint.hpp` | — | — | ⚠️ No test |

---

## 2. Test → Ticket Reverse Map

| CTest # | Test Name | Covers Ticket(s) |
|---------|-----------|-----------------|
| #1 | NavigationEngineTest.InitSuccess | FMS-001 |
| #2 | NavigationEngineTest.BearingEgllKsfo | FMS-001 |
| #3 | NavigationEngineTest.DistanceEgllKsfo | FMS-001 |
| #4 | NavigationEngineTest.XteZeroOnTrack | FMS-001 |
| #5 | NavigationEngineTest.GpsModeSwitch | FMS-002 |
| #6 | NavigationEngineTest.RnpSatisfied | FMS-002, FMS-003 |
| #7 | NavigationEngineTest.RnpExceeded | FMS-002, FMS-003 |
| #8 | NavigationEngineTest.AdcUpdate | FMS-004, FMS-020 |
| #9 | Arinc429Test.BnrRoundtripAlt35000 | FMS-026 |
| #10 | Arinc429Test.BnrRoundtripNegAlt | FMS-026 |
| #11 | Arinc429Test.BnrRoundtripAirspeed | FMS-026 |
| #12 | Arinc429Test.RxCallbackFires | FMS-027 |
| #13 | Arinc429Test.SsmNormalOp | FMS-027 |
| #14 | Arinc429Test.StatusNormalAfterInit | FMS-027 |
| #15 | FaultManagerTest.NoFaultsAfterInit | FMS-022 |
| #16 | FaultManagerTest.ReportWarningFaultActive | FMS-022 |
| #17 | FaultManagerTest.CriticalFaultLatched | FMS-023 |
| #18 | FaultManagerTest.WarningFaultClearable | FMS-023 |
| #19 | FaultManagerTest.WorstStatusReflectsSeverity | FMS-023 |
| #20 | FaultManagerTest.CallbackFires | FMS-022 |
| #21 | FaultManagerTest.OccurrenceCountIncrements | FMS-022 |
| #22 | FlightPlanTest.ActivateFailsLessThan2Wpts | FMS-007 |
| #23 | FlightPlanTest.ActivateSucceedsWith2Wpts | FMS-006, FMS-007 |
| #24 | FlightPlanTest.FindWaypointNotFound | FMS-005 |
| #25 | FlightPlanTest.FindWaypointFound | FMS-005 |
| #26 | FlightPlanTest.DeleteReducesCount | FMS-006 |
| #27 | FlightPlanTest.DirectTo | FMS-009 |
| #28 | FlightPlanTest.SequenceAdvancesIndex | FMS-008 |
| #29 | GuidanceTest.InitModesStandby | FMS-010, FMS-011 |
| #30 | GuidanceTest.SetLnavMode | FMS-013 |
| #31 | GuidanceTest.LnavRollWithinLimit | FMS-010 |
| #32 | GuidanceTest.VnavDescentBelowTargetAlt | FMS-011 |
| #33 | GuidanceTest.VnavClimbAboveTargetAlt | FMS-011 |
| #34 | GuidanceTest.MissedApproachEngagesHdgSel | FMS-012 |
| #35 | GuidanceTest.StandbyOutputsZero | FMS-010, FMS-011 |
| #36 | FmsIntegrationTest.ThirtyCyclesNoFault | FMS-007, FMS-010, FMS-011, FMS-016, FMS-020, FMS-022 |
| #37 | FmsIntegrationTest.FlightPlanStaysActive | FMS-006, FMS-007 |
| #38 | FmsIntegrationTest.FuelDecreases | FMS-014, FMS-016, FMS-017 |
| #39 | NavIntegrationTest.NavModeGpsAided | FMS-002, FMS-018 |
| #40 | NavIntegrationTest.AnpConvergesAfterGpsUpdates | FMS-002, FMS-018, FMS-021 |
| #41 | NavIntegrationTest.RnpSatisfiedAfterConvergence | FMS-003, FMS-021 |
| #42 | NavIntegrationTest.SensorFusionProducesValidPosition | FMS-019, FMS-021 |
| #43 | CommsIntegrationTest.Arinc429Loopback | FMS-026, FMS-027 |
| #44 | CommsIntegrationTest.AfdxTransmit | FMS-028 |
| #45 | CommsIntegrationTest.CanAeroTransmit | FMS-029 |
| #46 | CommsIntegrationTest.CanAeroLoopback | FMS-029 |
| #47 | CommsIntegrationTest.Arinc429StatusNormal | FMS-027 |

---

## 3. Coverage Gaps (No Dedicated Tests)

| Ticket | Feature | Risk | Recommended Test |
|--------|---------|------|-----------------|
| FMS-015 | Fuel imbalance / low-fuel warnings | Medium | Unit test: set `left_wing_kg` artificially high/low |
| FMS-024 | BITE / Health Monitor | Medium | Unit test: verify `bite_passed=true`, `cpu_load` in range |
| FMS-025 | Watchdog timer | High | Unit test: init 100ms timeout → sleep 200ms → `is_expired()=true` |
| FMS-030 | Data Bus Monitor | Medium | Unit test: call `update()` without marking active → `WARNING` |
| FMS-031 | RTOS Task | Low | Unit test: create task, verify started |
| FMS-032 | RTOS Mutex | Low | Unit test: lock/unlock, verify no deadlock |
| FMS-033 | RTOS Queue | Low | Unit test: send → receive roundtrip |
| FMS-034 | RTOS Timer | Low | Unit test: register callback → wait period → verify fired |
| FMS-035 | Logger | Low | Smoke test: log message appears in output |
| FMS-036 | Ring Buffer | Medium | Unit test: push/pop, overflow behaviour |
| FMS-037 | Fixed-Point Math | Low | Unit test: addition, multiplication precision |

---

## 4. Subsystem Coverage Heatmap

```
Subsystem            Tickets    Tests     Coverage
─────────────────────────────────────────────────
Navigation           4          8 unit    ████████ HIGH
                                4 integ
Flight Plan          5          7 unit    ████████ HIGH
                                2 integ
Guidance             4          7 unit    ████████ HIGH
                                1 integ
Fuel Management      2          0 unit    ████░░░░ MEDIUM
                                1 integ
Performance          2          0 unit    ████░░░░ MEDIUM
                                2 integ
Sensors              4          0 unit    █████░░░ MEDIUM-HIGH
                                4 integ
Safety               4          7 unit    ██████░░ GOOD (watchdog gap)
                                1 integ
Communications       5          6 unit    █████████ HIGH
                                5 integ
RTOS                 4          0         ░░░░░░░░ NONE
Common               3          0         ░░░░░░░░ NONE
─────────────────────────────────────────────────
TOTAL               37         47         DO-178C DAL-B: supplement needed
```

---

## 5. Requirement → Implementation → Test Chain (DO-178C Format)

```
SRS-NAV-001 (Haversine bearing)
  └── impl: NavigationEngine::compute_bearing_deg()   [NavigationEngine.cpp:70]
        └── test: NavigationEngineTest.BearingEgllKsfo [test_navigation_engine.cpp]

SRS-NAV-002 (Haversine distance)
  └── impl: NavigationEngine::compute_distance_nm()   [NavigationEngine.cpp:82]
        └── test: NavigationEngineTest.DistanceEgllKsfo
              └── test: NavigationEngineTest.XteZeroOnTrack

SRS-NAV-003 (GPS-aided position)
  └── impl: NavigationEngine::update_gps()            [NavigationEngine.cpp:36]
        └── test: NavigationEngineTest.GpsModeSwitch
              └── integ: NavIntegrationTest.NavModeGpsAided

SRS-NAV-004 (RNP monitoring)
  └── impl: NavigationEngine::is_rnp_satisfied()      [NavigationEngine.cpp:60]
        └── test: NavigationEngineTest.RnpSatisfied
              └── test: NavigationEngineTest.RnpExceeded
                    └── integ: NavIntegrationTest.RnpSatisfiedAfterConvergence

SRS-COMM-001 (ARINC 429 BNR encoding)
  └── impl: Arinc429Driver::encode_bnr()              [Arinc429Driver.cpp:38]
        └── impl: Arinc429Driver::decode_bnr()        [Arinc429Driver.cpp:56]
              └── test: Arinc429Test.BnrRoundtripAlt35000
                    └── test: Arinc429Test.BnrRoundtripNegAlt
                          └── integ: CommsIntegrationTest.Arinc429Loopback

SRS-SAFE-001 (Fault reporting)
  └── impl: FaultManager::report_fault()              [FaultManager.cpp:37]
        └── impl: FaultManager::set_fault_callback()  [FaultManager.cpp:97]
              └── test: FaultManagerTest.ReportWarningFaultActive
                    └── test: FaultManagerTest.CallbackFires
                          └── integ: FmsIntegrationTest.ThirtyCyclesNoFault

SRS-GUID-001 (LNAV roll command)
  └── impl: GuidanceComputer::update_lnav()           [GuidanceComputer.cpp:32]
        └── impl: GuidanceComputer::bank_from_xte()   [GuidanceComputer.cpp:28]
              └── test: GuidanceTest.LnavRollWithinLimit
                    └── integ: FmsIntegrationTest.ThirtyCyclesNoFault

SRS-GUID-003 (VNAV VS command)
  └── impl: GuidanceComputer::update_vnav()           [GuidanceComputer.cpp:46]
        └── test: GuidanceTest.VnavDescentBelowTargetAlt
              └── test: GuidanceTest.VnavClimbAboveTargetAlt
                    └── integ: FmsIntegrationTest.ThirtyCyclesNoFault
```

---

## 6. Key Architectural Decisions (for Interview / Review)

| Decision | Rationale |
|----------|-----------|
| Interface-per-subsystem (`INavigationEngine`, `IFaultManager`, etc.) | Enables mock injection in unit tests; supports hardware abstraction layer swap |
| `noexcept` throughout | Avionics determinism — no exception overhead, stack unwinding banned in DO-178C |
| `std::mutex` in FaultManager | Thread-safe fault reporting from ISR-like callbacks |
| EKF fusion (not simple GPS passthrough) | Continuity during GPS outage; ANP estimation from covariance |
| Fixed-point library | Deterministic arithmetic for RTOS-critical timing paths |
| ARINC 429 loopback in driver | Hardware-independent test execution on dev machine |
| Watchdog `kick()` in main loop | Detects main-loop hang; mirrors real HW watchdog pattern |
