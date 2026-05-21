# Sample Release Sign-Off Report

| Field | Value |
| --- | --- |
| Build | MGH_IVI_RC_01 |
| Bench | MGH_BENCH_01 |
| CANoe Config | MGH_IVI_Bench.cfg |
| DBC | MG_Hector_IVI_Training.dbc |
| Execution Window | 5 days |

## Result Summary

| Category | Total | Pass | Fail | Blocked |
| --- | ---: | ---: | ---: | ---: |
| Smoke | 8 | 8 | 0 | 0 |
| IVI Features | 25 | 23 | 2 | 0 |
| Connectivity | 20 | 18 | 1 | 1 |
| Camera/Cluster/SWC | 18 | 17 | 1 | 0 |
| Diagnostics/OTA | 15 | 13 | 1 | 1 |
| Power/Stress | 12 | 11 | 1 | 0 |

## Open Release Risks

- Bluetooth reconnect intermittent after sleep: workaround available, regression needed after stack fix.
- Reverse camera latency P95 exceeds KPI during low-voltage profile: release blocker if KPI is contractual.

## Recommendation

Conditional no-go until reverse camera low-voltage behavior is fixed or formally waived by the release board.
