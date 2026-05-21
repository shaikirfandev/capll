# Avionics Flight Management System (FMS) v3.2.1

Production-grade avionics FMS in C++17 targeting B737-800 operations.  
Standards: **DO-178C DAL-B** | **ARINC 702A** | **RTCA DO-229F** | **ARINC 424**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                                │
│   NavigationEngine │ GuidanceComputer │ FlightPlanManager           │
│   FuelManagement   │ PerformanceComputer                            │
├─────────────────────────────────────────────────────────────────────┤
│                     SENSOR LAYER                                    │
│   AirDataSystem │ InertialNavSystem │ GpsReceiver │ SensorFusion     │
├─────────────────────────────────────────────────────────────────────┤
│                  COMMUNICATIONS LAYER                               │
│   Arinc429Driver │ Arinc664Driver │ CanAerospaceDriver              │
│   DataBusMonitor                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                    SAFETY LAYER                                     │
│   FaultManager │ Watchdog (DAL-A) │ HealthMonitor                  │
├─────────────────────────────────────────────────────────────────────┤
│                  RTOS ABSTRACTION                                   │
│   FreeRtosTask │ FreeRtosMutex │ FreeRtosQueue │ FreeRtosTimer      │
├─────────────────────────────────────────────────────────────────────┤
│                  COMMON UTILITIES                                   │
│   Logger │ FixedPoint (Q15.16) │ RingBuffer (SPSC lock-free)       │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- CMake ≥ 3.20
- C++17 compiler (GCC 12+ / Clang 14+)
- Ninja (recommended)
- Internet access (FetchContent downloads spdlog, nlohmann_json, GoogleTest)

### Build & Run
```bash
./scripts/build.sh Release
./build/fms_app
```

### Run Tests
```bash
./scripts/build.sh Debug
./scripts/run_tests.sh
```

### Coverage Report
```bash
./scripts/generate_coverage.sh
open build_cov/coverage/index.html
```

### Static Analysis
```bash
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
./scripts/static_analysis.sh
```

### Docker
```bash
docker build --target tester -t fms-test .
docker build --target runtime -t fms-app .
docker run --rm fms-app
```

## Demo Output
```
=== Avionics FMS v3.2.1 — EGLL→KSFO ===
[BITE] FMS HealthMonitor self-test: RAM OK, CPU OK, timers OK
[CYCLE   0] ALT=2000 ft | GS=250 kt | ANP=0.012 nm | CPU=15.2% | RX_ALT=2000
[CYCLE  10] ALT=8500 ft | GS=350 kt | ANP=0.008 nm | CPU=14.8% | RX_ALT=8500
[CYCLE  20] ALT=23000 ft | GS=450 kt | ANP=0.006 nm | CPU=15.1% | RX_ALT=23000
[CYCLE  30] ALT=33000 ft | GS=460 kt | ANP=0.005 nm | CPU=14.9% | RX_ALT=33000
[CYCLE  40] ALT=35000 ft | GS=462 kt | ANP=0.005 nm | CPU=15.0% | RX_ALT=35000
=== FMS shutdown ===
```

## Project Structure
```
avionics_fms/
├── CMakeLists.txt              # Top-level build (C++17, FetchContent)
├── include/                    # Public interface headers
│   ├── common/                 # Logger, ErrorCodes, FixedPoint, RingBuffer
│   ├── comms/                  # IArinc429, IArinc664, ICanAerospace
│   ├── fms/                    # FmsTypes, INavigationEngine, IGuidance...
│   ├── rtos/                   # IRtosTask, IRtosMutex, IRtosQueue...
│   ├── safety/                 # IFaultManager, IWatchdog, SafetyTypes
│   └── sensors/                # IAirDataSystem, IGpsReceiver, SensorTypes
├── src/                        # Implementations
│   ├── comms/                  # Arinc429Driver, Arinc664Driver, CanAerospace
│   ├── fms/                    # NavigationEngine, GuidanceComputer...
│   ├── rtos/                   # FreeRTOS task/mutex/queue/timer simulation
│   ├── safety/                 # FaultManager, Watchdog, HealthMonitor
│   ├── sensors/                # ADS, INS, GPS, SensorFusion (EKF)
│   └── main.cpp                # FMS bootstrap — EGLL→KSFO scenario
├── tests/
│   ├── unit/                   # 40+ GoogleTest unit tests
│   └── integration/            # 3 integration test suites
├── config/
│   ├── fms_config.json         # Runtime configuration
│   ├── nav_database.json       # ARINC 424 nav-db (EGLL, KSFO, NAT Track A)
│   └── aircraft_config.hpp     # Compile-time B737-800 constants
├── docs/
│   ├── InterviewQA.md          # 34 Q&As for aerospace interviews
│   ├── ResumePoints.md         # ATS resume bullets for Boeing/Collins/Honeywell
│   └── ...                     # SRS, HLD, LLD, DO178C, FMEA, RTM, Architecture
├── scripts/                    # build.sh, run_tests.sh, coverage, static_analysis
├── .github/workflows/ci.yml    # GitHub Actions CI (Ubuntu + macOS)
└── Dockerfile                  # Multi-stage: builder → tester → runtime
```

## Standards Compliance
| Standard    | Level | Scope |
|-------------|-------|-------|
| DO-178C     | DAL-B | All FMS software |
| DO-178C     | DAL-A | Watchdog, memory management |
| DO-229F     | —     | RAIM, GPS integrity |
| ARINC 424   | —     | Navigation database format |
| ARINC 429   | —     | BNR encode/decode, labels |
| ARINC 664   | —     | AFDX dual-network VL |
| ARINC 702A  | —     | FMS functional requirements |
| CANaerospace v1.7 | — | CAN application layer |
| MISRA C++:2008 | — | Coding guidelines |

## Key Algorithms
- **Haversine** great-circle distance + bearing + cross-track error
- **10-state EKF** GPS/INS sensor fusion (position, velocity, attitude, bias)
- **RAIM** satellite integrity monitoring (≥5 sats, HDOP ≤ 2.0)
- **LNAV** proportional XTE controller (Kp=3 °/nm, ±25° bank)
- **VNAV** FPA-based VS command (±3000 fpm)
- **ISA atmosphere** pitot-static CAS/TAS/Mach computation
- **Strapdown INS** with Schuler 84.38-min oscillation and RLG 0.8 nm/hr drift
- **ARINC 429 BNR** with label reversal, odd parity, SSM encoding
