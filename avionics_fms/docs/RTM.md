# Requirements Traceability Matrix (RTM)
## Avionics FMS v3.2.1

| Req ID | Description | HLD Ref | LLD Ref | Test |
|--------|-------------|---------|---------|------|
| SRS-NAV-001 | Init at given lat/lon | HLD-3.1 | LLD-NAV-1 | test_navigation_engine:InitSuccess |
| SRS-NAV-002 | Bearing computation | HLD-3.1 | LLD-NAV-2 | test_navigation_engine:BearingEgllKsfo |
| SRS-NAV-003 | Distance computation | HLD-3.1 | LLD-NAV-3 | test_navigation_engine:DistanceEgllKsfo |
| SRS-NAV-004 | XTE zero on track | HLD-3.1 | LLD-NAV-4 | test_navigation_engine:XteZeroOnTrack |
| SRS-NAV-005 | GPS mode switch | HLD-3.2 | LLD-NAV-5 | test_navigation_engine:GpsModeSwitch |
| SRS-NAV-006 | RNP satisfied | HLD-3.3 | LLD-NAV-6 | test_navigation_engine:RnpSatisfied |
| SRS-NAV-007 | RNP exceeded | HLD-3.3 | LLD-NAV-7 | test_navigation_engine:RnpExceeded |
| SRS-NAV-008 | ADC update | HLD-3.2 | LLD-NAV-8 | test_navigation_engine:AdcUpdate |
| SRS-COM-001 | BNR roundtrip alt 35000 | HLD-4.1 | LLD-COM-1 | test_arinc429:BnrRoundtripAlt35000 |
| SRS-COM-002 | BNR negative alt | HLD-4.1 | LLD-COM-2 | test_arinc429:BnrRoundtripNegAlt |
| SRS-COM-003 | BNR airspeed 280 kt | HLD-4.1 | LLD-COM-3 | test_arinc429:BnrRoundtripAirspeed |
| SRS-COM-004 | RX callback fires | HLD-4.2 | LLD-COM-4 | test_arinc429:RxCallbackFires |
| SRS-COM-005 | SSM NORMAL_OP | HLD-4.1 | LLD-COM-5 | test_arinc429:SsmNormalOp |
| SRS-SAF-001 | No faults after init | HLD-5.1 | LLD-SAF-1 | test_fault_manager:NoFaultsAfterInit |
| SRS-SAF-002 | WARNING fault ACTIVE | HLD-5.1 | LLD-SAF-2 | test_fault_manager:ReportWarningFaultActive |
| SRS-SAF-003 | CRITICAL fault LATCHED | HLD-5.2 | LLD-SAF-3 | test_fault_manager:CriticalFaultLatched |
| SRS-SAF-004 | WARNING clearable | HLD-5.2 | LLD-SAF-4 | test_fault_manager:WarningFaultClearable |
| SRS-SAF-005 | Worst status | HLD-5.3 | LLD-SAF-5 | test_fault_manager:WorstStatusReflectsSeverity |
| SRS-SAF-006 | Fault callback | HLD-5.4 | LLD-SAF-6 | test_fault_manager:CallbackFires |
| SRS-FP-001 | Activate < 2 wpts fails | HLD-6.1 | LLD-FP-1 | test_flight_plan_manager:ActivateFailsLessThan2Wpts |
| SRS-FP-002 | Activate >= 2 wpts ok | HLD-6.1 | LLD-FP-2 | test_flight_plan_manager:ActivateSucceedsWith2Wpts |
| SRS-FP-003 | find_waypoint not found | HLD-6.2 | LLD-FP-3 | test_flight_plan_manager:FindWaypointNotFound |
| SRS-FP-004 | find_waypoint found | HLD-6.2 | LLD-FP-4 | test_flight_plan_manager:FindWaypointFound |
| SRS-GNC-001 | Init modes STANDBY | HLD-7.1 | LLD-GNC-1 | test_guidance_computer:InitModesStandby |
| SRS-GNC-002 | Set LNAV mode | HLD-7.2 | LLD-GNC-2 | test_guidance_computer:SetLnavMode |
| SRS-GNC-003 | LNAV roll <= 25 deg | HLD-7.2 | LLD-GNC-3 | test_guidance_computer:LnavRollWithinLimit |
| SRS-GNC-004 | VNAV descend above alt | HLD-7.3 | LLD-GNC-4 | test_guidance_computer:VnavDescentBelowTargetAlt |
| SRS-GNC-005 | VNAV climb below alt | HLD-7.3 | LLD-GNC-5 | test_guidance_computer:VnavClimbAboveTargetAlt |
| SRS-GNC-006 | Missed approach HDG_SEL | HLD-7.4 | LLD-GNC-6 | test_guidance_computer:MissedApproachEngagesHdgSel |
| SRS-INT-001 | 30-cycle no fault | HLD-8.1 | LLD-INT-1 | test_fms_integration:ThirtyCyclesNoFault |
| SRS-INT-010 | GPS_AIDED after updates | HLD-8.2 | LLD-INT-2 | test_navigation_integration:NavModeGpsAided |
| SRS-INT-011 | ANP < 0.1 nm | HLD-8.2 | LLD-INT-3 | test_navigation_integration:AnpConvergesAfterGpsUpdates |
| SRS-INT-020 | ARINC 429 loopback | HLD-8.3 | LLD-INT-4 | test_comms_integration:Arinc429Loopback |
| SRS-INT-022 | CAN loopback | HLD-8.3 | LLD-INT-5 | test_comms_integration:CanAeroLoopback |
