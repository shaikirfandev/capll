# Software Requirements Specification (SRS)
## Avionics FMS v3.2.1 — DO-178C DAL-B

## 1. Introduction

### 1.1 Purpose
This document defines software requirements for the Flight Management System (FMS) v3.2.1, targeting Boeing 737-800. It provides the basis for design, test, and DO-178C compliance evidence.

### 1.2 Scope
The FMS software implements navigation, guidance, flight plan management, fuel management, performance computation, sensor fusion, and bus communication functions.

### 1.3 Standards
| Standard | Applicability |
|----------|--------------|
| DO-178C DAL-B | Primary FMS software |
| DO-178C DAL-A | Watchdog, health monitor |
| RTCA DO-229F | GNSS sensor requirements |
| ARINC 702A | FMS functional requirements |
| ARINC 424-21 | Navigation database format |
| RTCA DO-236C | Minimum Aviation System Performance Standards for RNAV |

---

## 2. Navigation Engine Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-NAV-001 | The NavigationEngine shall initialize with a provided Position3D and return FmsError::OK. | Establishes initial fix |
| SRS-NAV-002 | The NavigationEngine shall compute great-circle bearing between two lat/lon pairs using the haversine formula, accurate to ±1.0°. | LNAV track following |
| SRS-NAV-003 | The NavigationEngine shall compute great-circle distance between two lat/lon pairs using the haversine formula, accurate to ±5 nm. | Waypoint sequencing |
| SRS-NAV-004 | The NavigationEngine shall compute cross-track error (XTE) ≤ 0.01 nm when aircraft is on the planned track. | LNAV deviation |
| SRS-NAV-005 | The NavigationEngine shall update NavMode to GPS_AIDED when a valid GPS Position3D is provided via update_gps(). | Navigation redundancy |
| SRS-NAV-006 | The NavigationEngine shall set NavState.status = NORMAL when ANP ≤ RNP. | RNP AR criteria |
| SRS-NAV-007 | The NavigationEngine shall set NavState.status = WARNING when ANP > RNP. | RNP AR criteria |
| SRS-NAV-008 | The NavigationEngine shall update NavState.position when update_adc() is called with valid AirDataState. | Sensor integration |
| SRS-NAV-009 | The NavigationEngine shall set NavState.mach from AirDataState.mach when update_adc() is called. | Performance input |
| SRS-NAV-010 | The NavigationEngine shall constrain NavState.anp_nm to ≥ 0.0 nm. | Data validity |

---

## 3. Communications Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-COM-001 | The Arinc429Driver.encode_bnr() shall encode altitude in the range [-131072, +131071] ft with 1.0 ft resolution into an ARINC 429 BNR word. | ARINC 702A §4.3 |
| SRS-COM-002 | The Arinc429Driver.decode_bnr() shall recover a value within ±1.0 ft of the encoded value when given a word from encode_bnr(). | BNR roundtrip |
| SRS-COM-003 | The Arinc429Driver shall support 100 kbps (high-speed) and 12.5 kbps (low-speed) operation. | ARINC 429 §2 |
| SRS-COM-004 | The Arinc429Driver shall call the registered RX callback within one bus cycle when a matching label is received. | Label dispatch |
| SRS-COM-005 | The Arinc429Driver shall set SSM = NORMAL_OP (0b11) in all transmit words unless overridden. | ARINC 429 §3 |
| SRS-COM-006 | The Arinc664Driver shall transmit an AFDX frame on the specified VL within 1 ms. | AFDX DO-160G §22 |
| SRS-COM-007 | The CanAerospaceDriver shall transmit a CANaerospace message with correct node_id and data_type. | CANaerospace §4 |
| SRS-COM-008 | The DataBusMonitor shall set a BUS_ARINC429_TIMEOUT fault when no message is received for > 500 ms. | Stale data detection |

---

## 4. Guidance Computer Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-GNC-001 | The GuidanceComputer shall initialize with LnavMode::STANDBY and VnavMode::STANDBY. | Safe default state |
| SRS-GNC-002 | The GuidanceComputer shall accept set_lnav_mode(LNAV) and engage LNAV guidance. | LNAV operation |
| SRS-GNC-003 | The GuidanceComputer shall limit roll command output to ±25.0° in LNAV mode. | B737-800 bank limit |
| SRS-GNC-004 | The GuidanceComputer shall command negative vertical speed (descent) when aircraft altitude > target altitude in VNAV_PTH mode. | VNAV path following |
| SRS-GNC-005 | The GuidanceComputer shall command positive vertical speed (climb) when aircraft altitude < target altitude in VNAV_PTH mode. | VNAV path following |
| SRS-GNC-006 | The GuidanceComputer shall transition to LnavMode::HDG_SEL when execute_missed_approach() is called. | Missed approach procedure |
| SRS-GNC-007 | The GuidanceComputer shall output zero roll and VS commands in STANDBY mode. | Safe standby state |
| SRS-GNC-008 | The GuidanceComputer shall clamp VS command to ±6000 fpm. | Aircraft structural limit |
| SRS-GNC-009 | The GuidanceComputer shall return get_lnav_mode() reflecting the currently active LNAV mode. | Mode state visibility |
| SRS-GNC-010 | The GuidanceComputer shall return get_vnav_mode() reflecting the currently active VNAV mode. | Mode state visibility |

---

## 5. Safety Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-SAF-001 | The FaultManager shall return an empty fault table after initialization. | No false faults at power-on |
| SRS-SAF-002 | The FaultManager shall set FaultState::ACTIVE on a reported WARNING fault. | Fault lifecycle |
| SRS-SAF-003 | The FaultManager shall set FaultState::LATCHED on a reported CRITICAL fault (non-clearable). | Safety-critical non-reset |
| SRS-SAF-004 | The FaultManager shall allow clear() of WARNING and CAUTION faults. | Crew reset authority |
| SRS-SAF-005 | The FaultManager.get_worst_status() shall return the highest severity active fault. | System status rollup |
| SRS-SAF-006 | The FaultManager shall invoke registered FaultCb within the report_fault() call. | Real-time notification |
| SRS-SAF-007 | The FaultManager shall track occurrence_count per FaultId. | Maintenance data |
| SRS-SAF-008 | The Watchdog shall return is_expired()=true when more than period_ms has elapsed since last kick(). | CPU hang detection |
| SRS-SAF-009 | The Watchdog shall return is_expired()=false immediately after kick(). | Watchdog reset |
| SRS-SAF-010 | The HealthMonitor shall detect CPU load exceeding 90% and report CAUTION status. | Resource protection |

---

## 6. Flight Plan Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-FP-001 | The FlightPlanManager shall return ERR_FP_INVALID when activate() is called with fewer than 2 waypoints. | Minimum viable route |
| SRS-FP-002 | The FlightPlanManager shall return OK when activate() is called with ≥ 2 waypoints. | Normal activation |
| SRS-FP-003 | The FlightPlanManager shall return ERR_NOT_FOUND when find_waypoint() is called with an ICAO not in the plan. | Route query |
| SRS-FP-004 | The FlightPlanManager shall return the correct Waypoint when find_waypoint() is called with a valid ICAO. | Route query |
| SRS-FP-005 | The FlightPlanManager shall decrement the waypoint count after delete_waypoint() succeeds. | Route editing |
| SRS-FP-006 | The FlightPlanManager shall update active_wpt_idx to the direct_to waypoint after direct_to() succeeds. | Direct-to navigation |
| SRS-FP-007 | The FlightPlanManager shall increment active_wpt_idx after sequence_to_next_waypoint() when not at the last waypoint. | Route sequencing |
| SRS-FP-008 | The FlightPlanManager shall support up to 128 waypoints per flight plan. | ARINC 702A capacity |
| SRS-FP-009 | The FlightPlanManager shall store origin_icao and dest_icao for the active flight plan. | Route identification |
| SRS-FP-010 | The FlightPlanManager shall maintain FlightPlanState::ACTIVE while the route is in progress. | State machine |

---

## 7. Performance Requirements

| ID | Requirement | Rationale |
|----|------------|-----------|
| SRS-PERF-001 | The PerformanceComputer shall compute optimal cruise altitude ≥ FL350 at typical MTOW. | Fuel efficiency |
| SRS-PERF-002 | The PerformanceComputer shall compute TOD distance from current position. | VNAV descent planning |
| SRS-PERF-003 | The PerformanceComputer shall compute V-speeds (V1, VR, V2) within ±2 kt. | Departure performance |
| SRS-PERF-004 | The FuelManagement shall decrement fuel_on_board_kg per cycle based on fuel_flow_kgph. | Fuel accounting |
| SRS-PERF-005 | The FuelManagement shall trigger FUEL_LOW warning when fuel < min_fuel_reserve_kg. | Safety fuel reserve |
| SRS-PERF-006 | The FuelManagement shall compute time_to_dest_min from current fuel and flow rate. | ETA calculation |
