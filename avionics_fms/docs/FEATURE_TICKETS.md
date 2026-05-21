# Avionics FMS — Feature Tickets

> **Project:** Avionics FMS v3.2.1  
> **Standard:** DO-178C DAL-B  
> **Platform:** B737-800 (MTOW 78,016 kg, VMO 340 kt, MMO 0.82)  
> **Build:** CMake 4.2.1 / AppleClang 17 / C++17  
> **Status key:** ✅ Done | 🔄 In Progress | ❌ Not Started

---

## SUBSYSTEM 1 — Navigation Engine

### FMS-001 — Haversine Great-Circle Navigation
| Field | Value |
|-------|-------|
| **ID** | FMS-001 |
| **Subsystem** | Navigation |
| **SRS Refs** | SRS-NAV-001, SRS-NAV-002 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/NavigationEngine.cpp`, `src/fms/NavigationEngine.hpp` |
| **Interface** | `include/fms/INavigationEngine.hpp` |

**Description**  
Implements spherical earth great-circle computation using the Haversine formula.
Provides three core geometric primitives needed by LNAV and the flight plan manager.

**Acceptance Criteria**
- `compute_distance_nm(EGLL, KSFO)` returns value in range [4500, 5000] nm
- `compute_bearing_deg(EGLL, KSFO)` returns westbound bearing ~280–310°
- `compute_xte_nm(from, to, pos)` returns 0.0 ± 0.001 nm when `pos` lies on the great-circle track

**Key Constants**
```
Earth radius: 3440.065 nm
DEG2RAD: π / 180
```

---

### FMS-002 — GPS-Aided Position and ANP Computation
| Field | Value |
|-------|-------|
| **ID** | FMS-002 |
| **Subsystem** | Navigation |
| **SRS Refs** | SRS-NAV-003 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/NavigationEngine.cpp` |

**Description**  
Ingests GPS measurements (lat/lon/alt, velocities, satellite count, HDOP) and updates
navigation state. Computes Actual Navigation Performance (ANP) proportional to HDOP
and satellite count. Switches nav mode from `DEAD_RECK` to `GPS_AIDED` when ≥4 sats
with HDOP < 3.0.

**Acceptance Criteria**
- After GPS update with 9 sats / HDOP 0.9 → `NavMode::GPS_AIDED`
- ANP < RNP when sats ≥ 8 and HDOP ≤ 1.0
- Ground speed derived from `√(Vn² + Ve²)` → converted m/s to knots

---

### FMS-003 — RNP Monitoring
| Field | Value |
|-------|-------|
| **ID** | FMS-003 |
| **Subsystem** | Navigation |
| **SRS Refs** | SRS-NAV-004 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/NavigationEngine.cpp` |

**Description**  
Continuously compares Actual Navigation Performance (ANP) against Required Navigation
Performance (RNP) limit. Transitions system status to `WARNING` when ANP > RNP.
RNP default: 2.0 nm enroute.

**Acceptance Criteria**
- `is_rnp_satisfied()` returns `true` when ANP ≤ RNP
- `is_rnp_satisfied()` returns `false` when ANP > RNP
- Status set to `WARNING` on RNP exceedance

---

### FMS-004 — Air Data Integration
| Field | Value |
|-------|-------|
| **ID** | FMS-004 |
| **Subsystem** | Navigation |
| **SRS Refs** | SRS-NAV-005 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/NavigationEngine.cpp` |

**Description**  
Accepts ADC data (TAS, CAS, Mach number, pressure altitude, ISA deviation) and
stores in navigation state for use by the guidance computer and performance computer.

**Acceptance Criteria**
- After `update_adc(TAS=440, CAS=280, Mach=0.78, alt=35000, isa=0)` →
  `state_.tas_kt=440`, `state_.position.alt_ft=35000`

---

## SUBSYSTEM 2 — Flight Plan Manager

### FMS-005 — Embedded Navigation Database
| Field | Value |
|-------|-------|
| **ID** | FMS-005 |
| **Subsystem** | Flight Plan |
| **SRS Refs** | SRS-FPM-001 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FlightPlanManager.cpp` |

**Description**  
Hard-coded nav-DB of 12 entries: 4 airports (EGLL, KSFO, KLAX, EDDF), 2 VORs (LAM,
OCK, SFO), and 4 North Atlantic Track intersection waypoints (WOBUN, MALOT, SUNOT,
MIMKU). `find_waypoint()` performs linear search and populates a `Waypoint` struct.

**Acceptance Criteria**
- `find_waypoint("EGLL", wpt)` returns `true`, lat=51.4775, lon=-0.4614
- `find_waypoint("XXXXX", wpt)` returns `false`

---

### FMS-006 — Waypoint Insert / Delete
| Field | Value |
|-------|-------|
| **ID** | FMS-006 |
| **Subsystem** | Flight Plan |
| **SRS Refs** | SRS-FPM-002, SRS-FPM-003 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FlightPlanManager.cpp` |

**Description**  
`insert_waypoint(idx, wpt)` inserts at any position with array shift-right.
`delete_waypoint(idx)` removes with shift-left and zero-fill of vacated slot.
Maximum capacity: `MAX_WAYPOINTS` (64). Returns `ERR_BUFFER_OVERFLOW` when full.

**Acceptance Criteria**
- Insert at index 0 shifts existing wpt to index 1
- `wpt_count` increments on insert, decrements on delete
- Delete on invalid index returns `ERR_INVALID_PARAM`

---

### FMS-007 — Flight Plan Activation
| Field | Value |
|-------|-------|
| **ID** | FMS-007 |
| **Subsystem** | Flight Plan |
| **SRS Refs** | SRS-FPM-004 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FlightPlanManager.cpp` |

**Description**  
`activate()` transitions the flight plan state from `PREFLIGHT` to `ACTIVE` and
sets `active_wpt_idx = 1`. Rejects activation with fewer than 2 waypoints.

**Acceptance Criteria**
- `activate()` with < 2 wpts → returns `ERR_FP_INVALID`
- `activate()` with ≥ 2 wpts → returns `OK`, `fp_.state == ACTIVE`

---

### FMS-008 — Waypoint Sequencing
| Field | Value |
|-------|-------|
| **ID** | FMS-008 |
| **Subsystem** | Flight Plan |
| **SRS Refs** | SRS-FPM-005 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FlightPlanManager.cpp` |

**Description**  
`sequence_next_waypoint()` increments `active_wpt_idx` by 1 if not already at the
last waypoint, implementing automatic leg sequencing.

**Acceptance Criteria**
- `active_wpt_idx` increments from 1 → 2 after call
- Does not advance past `wpt_count - 1`

---

### FMS-009 — Direct-To Function
| Field | Value |
|-------|-------|
| **ID** | FMS-009 |
| **Subsystem** | Flight Plan |
| **SRS Refs** | SRS-FPM-006 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FlightPlanManager.cpp` |

**Description**  
`direct_to(ident)` scans the active flight plan for the waypoint; if found, sets
`active_wpt_idx` directly. If not in flight plan but found in nav-DB, inserts at
the end and sequences to it. Returns `ERR_PROCEDURE_NOT_FOUND` for unknown identifiers.

**Acceptance Criteria**
- `direct_to("KSFO")` on a plan containing KSFO → `active_wpt_idx` points to KSFO
- `direct_to("ZZZZ")` → returns `ERR_PROCEDURE_NOT_FOUND`

---

## SUBSYSTEM 3 — Guidance Computer

### FMS-010 — LNAV Lateral Guidance (XTE → Roll Command)
| Field | Value |
|-------|-------|
| **ID** | FMS-010 |
| **Subsystem** | Guidance |
| **SRS Refs** | SRS-GUID-001, SRS-GUID-002 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/GuidanceComputer.cpp`, `src/fms/GuidanceComputer.hpp` |
| **Interface** | `include/fms/IGuidanceComputer.hpp` |

**Description**  
Computes Cross-Track Error (XTE) from the current nav position against the active
leg (prev wpt → active wpt). Applies proportional controller (Kp = 3.0 deg/nm)
to generate roll command. Saturates at ±25° (B737 bank limit).

**Acceptance Criteria**
- Aircraft on track (XTE = 0) → `roll_cmd_deg = 0`
- XTE = 5 nm → `|roll_cmd_deg| = 15°`
- Roll command never exceeds ±25°

---

### FMS-011 — VNAV Vertical Guidance (Altitude Target → VS Command)
| Field | Value |
|-------|-------|
| **ID** | FMS-011 |
| **Subsystem** | Guidance |
| **SRS Refs** | SRS-GUID-003 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/GuidanceComputer.cpp` |

**Description**  
When mode is `VNAV_PTH` or `VNAV_SPD`, computes altitude error against:
1. Waypoint altitude constraint (if non-zero), or
2. `perf.opt_cruise_alt_ft` as the fallback target.

VS command = altitude_error × 0.5, saturated at ±3000 fpm. Sets `in_descent` flag
when VS < 0.

**Acceptance Criteria**
- Aircraft at 5000 ft, target at 35000 ft → VS > 0 (climb)
- Aircraft at 40000 ft, target at 35000 ft → VS < 0, `in_descent = true`
- VS never exceeds ±3000 fpm

---

### FMS-012 — Missed Approach Procedure
| Field | Value |
|-------|-------|
| **ID** | FMS-012 |
| **Subsystem** | Guidance |
| **SRS Refs** | SRS-GUID-004 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/GuidanceComputer.cpp` |

**Description**  
`execute_missed_approach()` immediately engages `HDG_SEL` (LNAV) and `ALT_HOLD`
(VNAV), disabling path-following modes and passing aircraft control to the flight crew
for heading and altitude selection.

**Acceptance Criteria**
- After call: `lnav_mode == HDG_SEL`
- After call: `vnav_mode == ALT_HOLD`

---

### FMS-013 — Direct-To Guidance Mode
| Field | Value |
|-------|-------|
| **ID** | FMS-013 |
| **Subsystem** | Guidance |
| **SRS Refs** | SRS-GUID-005 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/GuidanceComputer.cpp` |

**Description**  
`direct_to(ident)` stores the target waypoint identifier and re-engages `LNAV` mode
so the guidance computer immediately steers toward the specified fix.

**Acceptance Criteria**
- After call: `lnav_mode == LNAV`
- `direct_to_ident_` contains the requested identifier

---

## SUBSYSTEM 4 — Fuel Management

### FMS-014 — Fuel Burn Tracking
| Field | Value |
|-------|-------|
| **ID** | FMS-014 |
| **Subsystem** | Fuel |
| **SRS Refs** | SRS-FUEL-001 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FuelManagement.cpp`, `src/fms/FuelManagement.hpp` |
| **Interface** | `include/fms/IFuelManagement.hpp` |

**Description**  
Tracks fuel in left wing tank, right wing tank, and total. On each update cycle,
burns `fuel_flow_cruise_kghr × DT_HR` split equally between tanks. Accumulates
`fuel_used_kg`. Initial load: configurable (`INITIAL_FUEL_KG`).

**Acceptance Criteria**
- After N update cycles, `total_fuel_kg < INITIAL_FUEL_KG`
- `fuel_used_kg` increases monotonically
- Neither tank goes below 0 kg

---

### FMS-015 — Fuel Imbalance and Low-Fuel Warnings
| Field | Value |
|-------|-------|
| **ID** | FMS-015 |
| **Subsystem** | Fuel |
| **SRS Refs** | SRS-FUEL-002 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/FuelManagement.cpp` |

**Description**  
Sets `imbalance_warn` when `|left - right| > IMBALANCE_WARN` kg. Sets `low_fuel_warn`
when `total < LOW_FUEL_WARN` kg and transitions system status to `WARNING`.

**Acceptance Criteria**
- Artificial imbalance > threshold → `imbalance_warn == true`
- Total fuel < low fuel threshold → `low_fuel_warn == true`, `status == WARNING`

---

## SUBSYSTEM 5 — Performance Computer

### FMS-016 — Optimum Cruise Altitude Computation
| Field | Value |
|-------|-------|
| **ID** | FMS-016 |
| **Subsystem** | Performance |
| **SRS Refs** | SRS-PERF-001 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/PerformanceComputer.cpp`, `src/fms/PerformanceComputer.hpp` |
| **Interface** | `include/fms/IPerformanceComputer.hpp` |

**Description**  
Updates Takeoff Weight (TOW) as fuel burns. Computes optimum cruise altitude using
`35000 + (70000 - TOW) × 0.2 ft`, capped at 41000 ft (B737 certified ceiling).
As the aircraft gets lighter, optimal altitude rises (step-climb logic basis).

**Acceptance Criteria**
- At TOW = 70000 kg → `opt_cruise_alt = 35000 ft`
- At TOW = 65000 kg → `opt_cruise_alt = 36000 ft`
- Never exceeds 41000 ft regardless of weight reduction

---

### FMS-017 — Cruise / Climb Fuel Flow Model
| Field | Value |
|-------|-------|
| **ID** | FMS-017 |
| **Subsystem** | Performance |
| **SRS Refs** | SRS-PERF-002 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/fms/PerformanceComputer.cpp` |

**Description**  
Initialises performance data for B737-800: cruise Mach 0.78, long-range cruise
Mach 0.74, fuel flow cruise 2400 kg/hr, fuel flow climb 3200 kg/hr. These values
drive `FuelManagement.update()`.

---

## SUBSYSTEM 6 — Sensors

### FMS-018 — GPS Receiver with RAIM
| Field | Value |
|-------|-------|
| **ID** | FMS-018 |
| **Subsystem** | Sensors |
| **SRS Refs** | SRS-SENS-001 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/sensors/GpsReceiver.cpp`, `src/sensors/GpsReceiver.hpp` |
| **Interface** | `include/sensors/IGpsReceiver.hpp` |

**Description**  
Simulates EGLL→KSFO westbound GPS receiver. Advances longitude by 0.05°/cycle,
adds Gaussian noise (σ=0.0001°). Provides: lat/lon, WGS-84 altitude, velocity
(north/east/down), HDOP 0.9, VDOP 1.2, 9 satellites, fix quality 3D. RAIM OK when
≥5 sats and HDOP < 2.0.

---

### FMS-019 — Inertial Navigation System (Strapdown INS)
| Field | Value |
|-------|-------|
| **ID** | FMS-019 |
| **Subsystem** | Sensors |
| **SRS Refs** | SRS-SENS-002 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/sensors/InertialNavSystem.cpp`, `src/sensors/InertialNavSystem.hpp` |
| **Interface** | `include/sensors/IInertialNavSystem.hpp` |

**Description**  
Ring Laser Gyro (RLG) strapdown INS. Alignment time: 2 s simulation. Drift model:
0.8 nm/hr modulated by Schuler oscillation (84.38-minute period). Outputs attitude
(pitch 2.5°, heading 270° westbound), velocity (-10 m/s north, -220 m/s east).

---

### FMS-020 — Air Data Computer
| Field | Value |
|-------|-------|
| **ID** | FMS-020 |
| **Subsystem** | Sensors |
| **SRS Refs** | SRS-SENS-003 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/sensors/AirDataSystem.cpp`, `src/sensors/AirDataSystem.hpp` |
| **Interface** | `include/sensors/IAirDataSystem.hpp` |

**Description**  
Computes and provides: True Air Speed (TAS), Calibrated Air Speed (CAS), Mach
number, pressure altitude, and ISA deviation from pitot-static system data.

---

### FMS-021 — 10-State EKF Sensor Fusion (GPS/INS)
| Field | Value |
|-------|-------|
| **ID** | FMS-021 |
| **Subsystem** | Sensors |
| **SRS Refs** | SRS-SENS-004 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/sensors/SensorFusion.cpp`, `src/sensors/SensorFusion.hpp` |

**Description**  
Extended Kalman Filter fusing GPS, INS, and ADC data. States: lat, lon, alt,
Vn, Ve, Vd, 4× bias. Predict step propagates position from INS velocity (10 Hz,
dt=0.1 s). Update step applies GPS corrections with RAIM gate (≥5 sats, HDOP < 2.0).
ANP derived from 2σ of position covariance in nm. Outputs `FusedState` with valid flag.

**Acceptance Criteria**
- After N GPS updates, `anp_nm` converges below `rnp_nm`
- `valid = true` after INS alignment + at least one GPS update

---

## SUBSYSTEM 7 — Safety

### FMS-022 — Fault Manager — Report, Escalate, Callback
| Field | Value |
|-------|-------|
| **ID** | FMS-022 |
| **Subsystem** | Safety |
| **SRS Refs** | SRS-SAFE-001 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/safety/FaultManager.cpp`, `src/safety/FaultManager.hpp` |
| **Interface** | `include/safety/IFaultManager.hpp` |

**Description**  
Thread-safe (mutex-protected) fault table with 32 slots. `report_fault()` creates
a new record or increments `occurrence_count` on repeat. Severity can only escalate
(not de-escalate) on re-report. `CRITICAL` severity auto-transitions state to
`LATCHED`. Invokes registered callback outside the lock.

**Acceptance Criteria**
- No faults after `init()`
- `report_fault(WARNING)` → `is_fault_active() == true`, status = WARNING
- `report_fault(CRITICAL)` → fault state = `LATCHED`
- Callback fires with correct `FaultRecord` contents

---

### FMS-023 — Fault Manager — Clear and Latch Protection
| Field | Value |
|-------|-------|
| **ID** | FMS-023 |
| **Subsystem** | Safety |
| **SRS Refs** | SRS-SAFE-002 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/safety/FaultManager.cpp` |

**Description**  
`clear_fault()` removes WARNING/CAUTION faults. Returns `ERR_FAULT_LATCHED` if
fault is in `LATCHED` state (CRITICAL faults cannot be cleared programmatically
— require maintenance action). `get_worst_status()` returns highest severity
across all active faults.

**Acceptance Criteria**
- WARNING fault can be cleared → `is_fault_active() == false`
- CRITICAL/LATCHED fault → `clear_fault()` returns `ERR_FAULT_LATCHED`
- `get_worst_status()` reflects the highest active severity

---

### FMS-024 — Health Monitor (BITE + CPU/RAM)
| Field | Value |
|-------|-------|
| **ID** | FMS-024 |
| **Subsystem** | Safety |
| **SRS Refs** | SRS-SAFE-003 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/safety/HealthMonitor.cpp`, `src/safety/HealthMonitor.hpp` |
| **Interface** | `include/safety/IHealthMonitor.hpp` |

**Description**  
`run_bite()` executes Built-In Test Equipment (RAM check, ROM check, CPU test) and
sets `bite_passed_ = true`. `update()` simulates CPU load (35–45%) and RAM usage
(42%). Transitions to `WARNING` if CPU load > 80%. Provides uptime in ms.

---

### FMS-025 — Watchdog Timer
| Field | Value |
|-------|-------|
| **ID** | FMS-025 |
| **Subsystem** | Safety |
| **SRS Refs** | SRS-SAFE-004 |
| **Priority** | Critical |
| **Status** | ✅ Done |
| **Source Files** | `src/safety/Watchdog.cpp`, `src/safety/Watchdog.hpp` |
| **Interface** | `include/safety/IWatchdog.hpp` |

**Description**  
Software watchdog with configurable timeout (default 500 ms). `kick()` resets the
timer. `is_expired()` returns `true` if time since last kick exceeds the timeout.
`get_status()` maps expiry to `FAILED`.

---

## SUBSYSTEM 8 — Communications

### FMS-026 — ARINC 429 BNR Encoding / Decoding
| Field | Value |
|-------|-------|
| **ID** | FMS-026 |
| **Subsystem** | Comms |
| **SRS Refs** | SRS-COMM-001 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/comms/Arinc429Driver.cpp`, `src/comms/Arinc429Driver.hpp` |
| **Interface** | `include/comms/IArinc429.hpp` |

**Description**  
Full ARINC 429 word builder: 8-bit label (bit-reversed per spec), 2-bit SDI, up to
19-bit BNR data field starting at bit 10, 2-bit SSM, 1-bit odd parity (bit 31).
`decode_bnr()` performs 2's-complement sign extension for signed values. Supports
configurable resolution (LSB value) and bit width.

**Acceptance Criteria**
- `encode_bnr(label=0x20, 0, 35000.0, 1.0, 18)` → decoded back = 35000 ± 0.5
- Negative altitude roundtrip lossless within ±0.5 LSB
- Odd parity bit correct for every word

---

### FMS-027 — ARINC 429 Loopback RX Dispatch
| Field | Value |
|-------|-------|
| **ID** | FMS-027 |
| **Subsystem** | Comms |
| **SRS Refs** | SRS-COMM-002 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/comms/Arinc429Driver.cpp` |

**Description**  
`transmit_raw()` implements hardware-loopback simulation: extracts label from
transmitted word, looks up any registered callback for that label, and invokes
it with a populated `Arinc429Frame`. Enables RX path testing without physical bus.

**Acceptance Criteria**
- Register callback for label L → `transmit_raw()` invokes callback with correct frame
- `frame.ssm == NORMAL_OP` when SSM field set accordingly

---

### FMS-028 — ARINC 664 (AFDX) Dual-Network Transmit
| Field | Value |
|-------|-------|
| **ID** | FMS-028 |
| **Subsystem** | Comms |
| **SRS Refs** | SRS-COMM-003 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/comms/Arinc664Driver.cpp`, `src/comms/Arinc664Driver.hpp` |
| **Interface** | `include/comms/IArinc664.hpp` |

**Description**  
AFDX driver simulating dual-network (Network A + Network B) redundancy per
ARINC 664 Part 7. Each `transmit()` increments `seq_counter_` and delivers to
the registered VL callback twice (A and B copies). Receiver would deduplicate
by sequence number.

**Acceptance Criteria**
- `transmit()` returns `true` on active network
- Callback receives frame with `seq_num` incremented from previous
- `net_a_ok` and `net_b_ok` both `true` after init

---

### FMS-029 — CANaerospace Message Bus
| Field | Value |
|-------|-------|
| **ID** | FMS-029 |
| **Subsystem** | Comms |
| **SRS Refs** | SRS-COMM-004 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/comms/CanAerospaceDriver.cpp`, `src/comms/CanAerospaceDriver.hpp` |
| **Interface** | `include/comms/ICanAerospace.hpp` |

**Description**  
CANaerospace v1.7 driver with node ID configuration, atomic bus-active flag, and
atomic error counter. `transmit()` delivers to registered message-ID callback in
loopback mode. Bus goes inactive via `deinit()`.

**Acceptance Criteria**
- `transmit()` on active bus → returns `true`, callback fires
- `deinit()` followed by `transmit()` → `error_count` increments, returns `false`

---

### FMS-030 — Data Bus Health Monitor
| Field | Value |
|-------|-------|
| **ID** | FMS-030 |
| **Subsystem** | Comms |
| **SRS Refs** | SRS-COMM-005 |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/comms/DataBusMonitor.cpp`, `src/comms/DataBusMonitor.hpp` |

**Description**  
Monitors activity on ARINC 429, AFDX, and CAN buses using `steady_clock` timestamps.
`mark_*_active()` stamps the current time. `is_*_healthy()` returns `true` if the
last activity was within `TIMEOUT_MS`. `update()` sets system status to `WARNING`
if ARINC 429 or AFDX has timed out.

---

## SUBSYSTEM 9 — RTOS Abstraction

### FMS-031 — FreeRTOS Task Wrapper
| Field | Value |
|-------|-------|
| **ID** | FMS-031 |
| **Subsystem** | RTOS |
| **SRS Refs** | SRS-RTOS-001 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/rtos/FreeRtosTask.cpp`, `src/rtos/FreeRtosTask.hpp` |
| **Interface** | `include/rtos/IRtosTask.hpp` |

**Description**  
Wraps `std::thread` as a portable FreeRTOS task abstraction for host-side testing.
Provides `create()`, `suspend()`, `resume()`, and `delete_task()`.

---

### FMS-032 — FreeRTOS Mutex
| Field | Value |
|-------|-------|
| **ID** | FMS-032 |
| **Subsystem** | RTOS |
| **SRS Refs** | SRS-RTOS-002 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/rtos/FreeRtosMutex.cpp`, `src/rtos/FreeRtosMutex.hpp` |

**Description**  
Wraps `std::mutex` and `std::timed_mutex`. Provides `lock(timeout_ms)` and `unlock()`.

---

### FMS-033 — FreeRTOS Queue
| Field | Value |
|-------|-------|
| **ID** | FMS-033 |
| **Subsystem** | RTOS |
| **SRS Refs** | SRS-RTOS-003 |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/rtos/FreeRtosQueue.cpp`, `src/rtos/FreeRtosQueue.hpp` |

**Description**  
Template ring-buffer-backed message queue. `send(item, timeout_ms)` and
`receive(item, timeout_ms)` with timeout semantics.

---

### FMS-034 — FreeRTOS Timer
| Field | Value |
|-------|-------|
| **ID** | FMS-034 |
| **Subsystem** | RTOS |
| **SRS Refs** | SRS-RTOS-004 |
| **Priority** | Low |
| **Status** | ✅ Done |
| **Source Files** | `src/rtos/FreeRtosTimer.cpp`, `src/rtos/FreeRtosTimer.hpp` |

**Description**  
Periodic software timer using `std::chrono`. Calls registered callback on expiry.

---

## SUBSYSTEM 10 — Common Infrastructure

### FMS-035 — Logger
| Field | Value |
|-------|-------|
| **ID** | FMS-035 |
| **Subsystem** | Common |
| **Priority** | High |
| **Status** | ✅ Done |
| **Source Files** | `src/common/Logger.cpp`, `include/common/Logger.hpp` |

**Description**  
Singleton thread-safe logger with levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
Writes timestamped, levelled, module-tagged messages to file and stdout.
Macros: `FMS_LOG_INFO(module, msg)` etc.

---

### FMS-036 — Ring Buffer
| Field | Value |
|-------|-------|
| **ID** | FMS-036 |
| **Subsystem** | Common |
| **Priority** | Medium |
| **Status** | ✅ Done |
| **Source Files** | `src/common/RingBuffer.cpp`, `include/common/RingBuffer.hpp` |

**Description**  
Fixed-capacity lock-free ring buffer for inter-task data exchange (sensor data,
command queues). Template type, configurable capacity.

---

### FMS-037 — Fixed-Point Arithmetic
| Field | Value |
|-------|-------|
| **ID** | FMS-037 |
| **Subsystem** | Common |
| **Priority** | Low |
| **Status** | ✅ Done |
| **Source Files** | `src/common/FixedPoint.cpp`, `include/common/FixedPoint.hpp` |

**Description**  
Q-format fixed-point arithmetic library for deterministic math in avionics contexts.
Avoids floating-point non-determinism in RTOS-critical paths.

---

## Ticket Summary

| Ticket | Feature | Subsystem | Priority | Tests |
|--------|---------|-----------|----------|-------|
| FMS-001 | Haversine Navigation | Navigation | Critical | #2, #3, #4 |
| FMS-002 | GPS Position / ANP | Navigation | Critical | #5, #6, #7 |
| FMS-003 | RNP Monitoring | Navigation | Critical | #6, #7 |
| FMS-004 | Air Data Integration | Navigation | High | #8 |
| FMS-005 | Nav Database | Flight Plan | High | #24, #25 |
| FMS-006 | Wpt Insert / Delete | Flight Plan | High | #23, #26 |
| FMS-007 | Flight Plan Activate | Flight Plan | Critical | #22, #23 |
| FMS-008 | Wpt Sequencing | Flight Plan | High | #28 |
| FMS-009 | Direct-To | Flight Plan | High | #27 |
| FMS-010 | LNAV Roll Command | Guidance | Critical | #31 |
| FMS-011 | VNAV VS Command | Guidance | Critical | #32, #33 |
| FMS-012 | Missed Approach | Guidance | Critical | #34 |
| FMS-013 | Direct-To Guidance | Guidance | High | #30 |
| FMS-014 | Fuel Burn Tracking | Fuel | High | #38 |
| FMS-015 | Fuel Warnings | Fuel | High | — |
| FMS-016 | Optimum Altitude | Performance | High | #36, #37 |
| FMS-017 | Fuel Flow Model | Performance | Medium | #38 |
| FMS-018 | GPS Receiver / RAIM | Sensors | Critical | #39, #40 |
| FMS-019 | INS / Schuler Drift | Sensors | Critical | #42 |
| FMS-020 | Air Data Computer | Sensors | High | #8 |
| FMS-021 | EKF Sensor Fusion | Sensors | Critical | #40, #41, #42 |
| FMS-022 | Fault Report / CB | Safety | Critical | #16, #20, #21 |
| FMS-023 | Fault Clear / Latch | Safety | Critical | #17, #18, #19 |
| FMS-024 | BITE / Health Monitor | Safety | High | — |
| FMS-025 | Watchdog | Safety | Critical | — |
| FMS-026 | ARINC 429 BNR | Comms | High | #9, #10, #11 |
| FMS-027 | ARINC 429 RX Loop | Comms | High | #12, #13 |
| FMS-028 | AFDX Dual Network | Comms | Medium | #44 |
| FMS-029 | CANaerospace Driver | Comms | Medium | #45, #46 |
| FMS-030 | Data Bus Monitor | Comms | High | — |
| FMS-031 | RTOS Task | RTOS | Medium | — |
| FMS-032 | RTOS Mutex | RTOS | Medium | — |
| FMS-033 | RTOS Queue | RTOS | Medium | — |
| FMS-034 | RTOS Timer | RTOS | Low | — |
| FMS-035 | Logger | Common | High | — |
| FMS-036 | Ring Buffer | Common | Medium | — |
| FMS-037 | Fixed-Point Math | Common | Low | — |
