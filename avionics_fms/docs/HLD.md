# High-Level Design (HLD)
## Avionics FMS v3.2.1 — DO-178C DAL-B

## 1. System Architecture Overview

The FMS is structured as a six-layer stack with strict downward dependency:

```
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  NavigationEngine  GuidanceComputer  FlightPlanManager        │
│  FuelManagement    PerformanceComputer                        │
├──────────────────────────────────────────────────────────────┤
│                      Sensor Layer                             │
│  AirDataSystem  InertialNavSystem  GpsReceiver  SensorFusion  │
├──────────────────────────────────────────────────────────────┤
│                   Communications Layer                        │
│  Arinc429Driver  Arinc664Driver  CanAerospaceDriver           │
│  DataBusMonitor                                               │
├──────────────────────────────────────────────────────────────┤
│                      Safety Layer                             │
│  FaultManager  Watchdog  HealthMonitor                        │
├──────────────────────────────────────────────────────────────┤
│                   RTOS Abstraction Layer                      │
│  FreeRtosTask  FreeRtosMutex  FreeRtosQueue  FreeRtosTimer    │
├──────────────────────────────────────────────────────────────┤
│                    Common Utilities                           │
│  Logger  FixedPoint  RingBuffer  ErrorCodes                   │
└──────────────────────────────────────────────────────────────┘
```

### Design Principle: Interface Segregation
Each layer exposes a pure abstract interface (`INavigationEngine`, `IArinc429`, etc.). Concrete implementations depend only on interfaces, enabling:
- Unit testing with GMock
- Target/host portability (FreeRTOS vs. std::thread)
- Dependency injection at initialization

---

## 2. Component Descriptions

### 2.1 NavigationEngine (HLD-3.1 through HLD-3.3)

**Responsibility:** Maintains the aircraft's estimated position, velocity, and navigation accuracy estimate (ANP).

**Algorithms:**
- Great-circle navigation: haversine formula for distance/bearing
- Cross-track error: spherical law of cosines
- RNP monitoring: compare ANP against required navigation performance

**Interfaces consumed:** `IAirDataSystem`, `IGpsReceiver`, `IInertialNavSystem`, `IFaultManager`
**Outputs:** `NavState` struct (position, velocity, ANP, RNP, mode, status)

### 2.2 GuidanceComputer (HLD-7.1 through HLD-7.4)

**Responsibility:** Translates desired flight plan trajectory into roll and VS commands.

**LNAV logic:** Proportional controller on cross-track error. Roll limit ±25°.
**VNAV logic:** Proportional controller on altitude deviation. VS limit ±6000 fpm.
**Missed approach:** Set `LnavMode::HDG_SEL`, clear VS command.

**Interfaces consumed:** `INavigationEngine`, `IFlightPlanManager`, `IFaultManager`

### 2.3 FlightPlanManager (HLD-6.1 through HLD-6.2)

**Responsibility:** Stores, edits, and sequences the active route.

**Storage:** `FlightPlan` struct with static `Waypoint[128]` array (no heap).
**Operations:** add_waypoint, delete_waypoint, direct_to, sequence_to_next_waypoint, find_waypoint.

### 2.4 SensorFusion (HLD-8.2)

**Responsibility:** Fuses GPS and INS data using an Extended Kalman Filter to produce best-estimate position.

**State vector:** [lat, lon, alt, vel_n, vel_e, vel_d] (6 DOF)
**Predict:** INS propagation with process noise
**Update:** GPS measurement with measurement noise (R = 50 m² diag)

### 2.5 FaultManager (HLD-5.1 through HLD-5.4)

**Responsibility:** Central fault repository with ACTIVE/LATCHED lifecycle.

**Storage:** Static `FaultRecord[64]` table (no heap).
**CRITICAL** faults auto-latch and cannot be cleared.
**WARNING/CAUTION** faults can be cleared by crew.

### 2.6 Arinc429Driver (HLD-4.1 through HLD-4.2)

**Responsibility:** Encode/decode ARINC 429 words; call registered RX callbacks.

**BNR encoding:** 18-bit two's complement in bits 11–29 of 32-bit word.
**Label dispatch:** Map from label octet to callback function.

### 2.7 DataBusMonitor (HLD-8.3)

**Responsibility:** Monitors all bus interfaces for stale data and reports `BUS_*_TIMEOUT` faults.

---

## 3. Data Flow

```
GpsReceiver ─────────────────┐
InertialNavSystem ────────────┼──> SensorFusion ──> NavigationEngine ──> GuidanceComputer
AirDataSystem ────────────────┘                              │
                                                        FlightPlanManager
                                                             │
                                                    PerformanceComputer
                                                    FuelManagement
                                                             │
                                              Arinc429Driver/Arinc664Driver (TX to displays)
```

---

## 4. Thread Model

| Thread | Period | Priority | Responsibility |
|--------|--------|----------|----------------|
| FMS Main | 50 ms | HIGH | Nav + guidance update cycle |
| Sensor Task | 10 ms | VERY HIGH | GPS/INS raw data acquisition |
| Bus RX Task | Interrupt | CRITICAL | ARINC 429 RX callback dispatch |
| Watchdog Task | 500 ms | HIGHEST | CPU hang detection |
| Health Monitor | 1000 ms | LOW | BITE and resource monitoring |

---

## 5. Memory Budget (Embedded Target)

| Region | Size |
|--------|------|
| Code (Flash) | ~512 KB |
| Read-only data | ~64 KB |
| BSS (zero-init) | ~32 KB |
| Stack (all tasks) | ~128 KB |
| Heap | 0 (disabled) |
