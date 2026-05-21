# Software Architecture Document
## Avionics FMS v3.2.1

### 1. Architecture Overview

The FMS uses a **layered architecture** with strict unidirectional dependencies (upper layers depend on lower layer interfaces, never concrete classes).

```
┌────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                         │
│  NavigationEngine | GuidanceComputer | FlightPlanManager   │
│  FuelManagement   | PerformanceComputer                    │
│  Depends on: INavigationEngine, IFlightPlanManager, etc.   │
├────────────────────────────────────???────────────────────────────────────???────?       │
│  AirDataSystem | InertialNavSystem | GpsReceiver           │
│  SensorFusion (EKF)                                        │
│  Implements: IAirDataSystem, IGpsReceiver, IInertialNavSys │
├────────────────────────────────────────────────────────────┤
│  COMMUNICATIONS LAYER                                      │
│  Arinc429Driver | Arinc664Driver | CanAerospaceDriver      │
│  DataBusMonitor                                            │
│  Implements: IArinc429, IArinc664, ICanAerospace           │
├────────────────────────────────────────────────────────────┤
│  SAFETY LAYER                                              │
│  FaultManager | Watchdog | HealthMonitor                   │
│  Implements: IFaultManager, IWatchdog, IHealthMonitor      │
├────────────────────────────────────────────────────────────┤
│  RTOS ABSTRACTION LAYER                                    │
│  FreeRtosTask | FreeRtosMutex | FreeRtosQueue              │
│  FreeRtosTimer                                             │
│  Implements: IRtosTask, IRtosMutex, IRtosQueue, IRtosTimer │
├────────────────────────────────────────────────────────────┤
│  COMMON UTILITIES                                          │
│  Logger | FixedPoint (Q15.16) | RingBuffer (SPSC)          │
│  ErrorCodes (Result<T,E>)                                  │
└────────────────────────────────────────────────────────────┘
```

### 2. Key Design Decisions

#### 2.1 Pure Virtual Interfaces
Every subsystem exposes a pure virtual interface (`INavigationEngine`, `IFaultManager`, etc.). Concrete classes depend only on interfaces of lower layers. Enables unit testing via GMock injection.

#### 2.2 No Dynamic Allocation in Safety Paths
All safety-critical data structures use static arrays:
- FaultRecord fault_table_[64]
- Waypoint waypoints[128]  
- float EKF state_[10], P_[10][10]

#### 2.3 Thread Safety
The RTOS simulation uses `std::atomic` for `running_` and `suspended_` flags. FaultManager uses `std::mutex` protecting `fault_table_` but invokes callbacks outside the lock to prevent priority inversion.

#### 2.4 Fault Management Lifecycle
```
INACTIVE → ACTIVE (on report) → LATCHED (on CRITICAL or explicit latch)
                ↑ clear() allowed for WARNING/CAUTION
```

### 3. Data Flow — Navigation Update Cycle (50 ms)

```
GPS.update() → GpsRaw
INS.update() → InsRaw  
ADC.update() → AdcRaw
                ↓
SensorFusion.update(GPS, INS, ADC) → fused_position
                ↓
NavigationEngine.update_gps() / update_adc()
NavigationEngine → NavState {position, velocity, ANP, RNP, mode}
                ↓
GuidanceComputer.update(NavState, FlightPlan, PerfData)
  → roll_cmd_deg (LNAV)
  → vs_cmd_fpm   (VNAV)
                ↓
Arinc429Driver.transmit(altitude_word)
                ↓
FaultManager.report_fault(NAV_RNP_EXCEEDED) if ANP > RNP
```
