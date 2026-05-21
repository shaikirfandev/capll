# Safety Mechanisms
## Avionics FMS v3.2.1 — DO-178C DAL-B

## 1. Fault Detection and Isolation Recovery (FDIR)

### 1.1 Three-Tier Fault Model
```
INACTIVE  ->  ACTIVE   ->  LATCHED
              (report)      (CRITICAL auto-latch, or manual latch)
                |
              clear() [WARNING/CAUTION only]
```

### 1.2 Fault Severity to System Status Mapping
| FaultSeverity | SystemStatus | Effect |
|---------------|-------------|--------|
| INFO | NORMAL | Log only |
| WARNING | WARNING | Crew advisory |
| CAUTION | CAUTION | Non-normal checklist |
| CRITICAL | FAILED | Immediate action required |

### 1.3 Fault Sources in This FMS
| Fault ID | Source | Recovery |
|----------|--------|---------|
| GPS_SIGNAL_LOST | GpsReceiver | INS-only navigation |
| GPS_RAIM_FAIL | GpsReceiver | Conventional nav reversion |
| INS_ALIGN_FAIL | InertialNavSystem | GPS-only |
| INS_DRIFT_EXCEED | InertialNavSystem | EKF GPS correction |
| ADC_PRESSURE_FAIL | AirDataSystem | Backup ADC |
| ADC_AIRSPEED_FAIL | AirDataSystem | INS-computed airspeed |
| NAV_RNP_EXCEEDED | NavigationEngine | Crew alert, conventional nav |
| BUS_ARINC429_TIMEOUT | DataBusMonitor | Stale data flag |

## 2. Watchdog Timer (DAL-A)

- Period: 500 ms kick interval
- Implementation: `std::chrono::steady_clock` elapsed check
- If `is_expired()` returns true: FMS reports WATCHDOG_TIMEOUT fault (CRITICAL)
- Hardware watchdog (production): triggers CPU reset on expiry
- Main loop responsibility: call `watchdog.kick()` every 50 ms cycle

## 3. Built-In Test Equipment (BITE)

- Power-on: `HealthMonitor::run_bite()` tests RAM, CPU timers, bus interfaces
- Continuous: `HealthMonitor::update()` polls CPU load, RAM usage, uptime
- Reports: `HealthReport` struct with `cpu_load_pct`, `ram_usage_pct`, `uptime_ms`, `status`

## 4. Redundancy

| System | Redundancy | Failover |
|--------|-----------|---------|
| GPS | Dual (primary + backup) | Automatic on RAIM fail |
| AFDX | Dual network (A+B) | Automatic on single-network fail |
| ADC | Triple (captain/FO/standby) | FMS uses captain, auto-switch |
| INS | Dual IRS | Cross-check, worst-case ANP |

## 5. Memory Protection

- No dynamic allocation in flight-critical paths
- Stack usage bounded and analyzed (MISRA Rule 18-4-1)
- Global arrays with compile-time bounds
- No recursive functions in safety paths
