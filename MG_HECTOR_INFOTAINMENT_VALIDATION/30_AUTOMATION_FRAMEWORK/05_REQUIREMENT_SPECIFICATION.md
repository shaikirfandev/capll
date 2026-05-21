# Requirement Specification: Automation Framework

## Functional Requirements

| Req ID | Requirement | Verification Method | Priority |
| --- | --- | --- | --- |
| MGH-30-FUNC-001 | The IVI shall support the defined automation framework behavior in IGN mode. | Bench functional test | P0 |
| MGH-30-FUNC-002 | The IVI shall preserve a valid user-visible state after sleep/wakeup where applicable. | Recovery test | P1 |
| MGH-30-FUNC-003 | The IVI shall handle unavailable dependency inputs without crash or undefined UI. | Fault injection | P0 |

## Diagnostic Requirements

| Req ID | Requirement | Verification Method | Priority |
| --- | --- | --- | --- |
| MGH-30-DIAG-001 | The IVI shall expose software identification through approved DIDs. | UDS DID read | P0 |
| MGH-30-DIAG-002 | The IVI shall set or suppress DTCs according to the diagnostic specification during automation framework faults. | DTC test | P1 |

## Performance Requirements

| Req ID | Requirement | Verification Method | Priority |
| --- | --- | --- | --- |
| MGH-30-PERF-001 | User-visible response latency shall meet the feature KPI or documented target. | Timed measurement | P1 |
| MGH-30-PERF-002 | The feature shall not cause memory, CPU, thread or file descriptor growth during stress execution. | Stress monitoring | P1 |

## Evidence Requirements

Every passed or failed result must include CAN trace, test report, relevant IVI logs and diagnostic snapshot unless marked not applicable with reviewer approval.
