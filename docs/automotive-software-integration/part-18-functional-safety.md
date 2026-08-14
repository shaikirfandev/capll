# Part 18 — Functional Safety Integration

---

## 18.1 Key Concepts

| Term | Definition |
|---|---|
| HARA | Hazard Analysis and Risk Assessment |
| ASIL | Automotive Safety Integrity Level (A/B/C/D, QM) |
| Safety Goal | Top-level safety requirement from HARA |
| FSC | Functional Safety Concept — how system achieves safety goals |
| TSC | Technical Safety Concept — technical mechanisms for safety goals |
| FTTI | Fault Tolerant Time Interval — max time from fault to safe state |
| Diagnostic Coverage | Fraction of faults detected by safety mechanism |
| Fail-Safe | System reaches safe state upon fault |
| Fail-Operational | System continues operating with degraded performance upon fault |

---

## 18.2 HARA Example — AEB System

| Hazard | Situation | ASIL | Safety Goal |
|---|---|---|---|
| Unintended AEB activation | Driving at 100 km/h | ASIL-D | AEB shall not activate without valid collision threat |
| Missing AEB when needed | Pedestrian crossing | ASIL-C | AEB shall activate within 150ms of confirmed threat |
| Wrong brake magnitude | Any | ASIL-C | Brake request shall not exceed safe limit |

---

## 18.3 Safety Mechanisms

Safety mechanisms detect faults and bring the system to a safe state:

| Mechanism | Fault Detected | ECU |
|---|---|---|
| Watchdog timer (WdgM) | Task overrun, CPU hang | All ECUs |
| CRC check | Data corruption in RAM/Flash | All ECUs |
| Plausibility check | Sensor value out of range | ADAS, Cluster |
| Redundant sensors | Sensor failure | ADAS |
| End-to-end protection (E2E) | CAN message corruption/loss | Safety ECUs |
| Voltage monitoring | Power supply failure | All ECUs |
| CPU self-test (BIST) | CPU register fault | Safety MCUs |

---

## 18.4 E2E (End-to-End) Protection

E2E protection (AUTOSAR E2E library) adds a CRC + counter + data ID to safety-critical messages to detect:
- Bit errors
- Loss of messages
- Out-of-order messages
- Insertion of old messages

```
Sender side:
  E2E_Protect(data, &header)  // add CRC, increment counter
  Transmit over CAN

Receiver side:
  E2E_Check(data, &header)    // verify CRC, check counter
  If check fails: report DEM event → enter degraded mode
```

---

## 18.5 Degraded Mode (Fail-Degraded)

When a fault is detected, the system should enter a safe degraded mode:

```
ADAS ECU: camera signal lost
  → Disable camera-dependent features (LKA, AEB-vision)
  → Enable radar-only fallback (ACC continues)
  → Warn driver via cluster warning
  → Set DTC

Cluster: rendering crash on main SoC
  → Safety MCU takes over → display minimum telltales only
  → Set DTC

TCU: cellular modem unresponsive
  → Disable remote diagnostics
  → Enable eCall via backup path (SMS/GPRS fallback)
```

---

## 18.6 Fault Injection Testing

To verify safety mechanisms, faults are intentionally injected:

| Fault Injected | Expected Reaction |
|---|---|
| Disconnect camera signal | AEB-vision disabled; DTC set within FTTI |
| Inject wrong E2E CRC on AEB message | Receiver detects, enters safe state |
| Trigger watchdog timeout | ECU resets; recovers; DTC set |
| Inject sensor value = 9999 (out of range) | Plausibility check triggers; signal ignored |

---

## 18.7 Safety Integration Checklist

```
[ ] ASIL level assigned to all safety-relevant requirements
[ ] Safety mechanisms implemented per TSC
[ ] E2E protection configured on ASIL-B+ CAN messages
[ ] WdgM configured with correct supervision deadlines
[ ] FTTI verified by fault injection test
[ ] ISO 26262 Part 4 (system) and Part 6 (software) work products complete
[ ] Safety case reviewed and signed
```

---

## Summary

| Concept | Integration Implication |
|---|---|
| ASIL-D | Maximum rigor, redundancy, no single point of failure |
| ASIL-B | Diagnostic coverage ≥ 90%, E2E on messages |
| QM | No safety constraints, standard good practices |
| FTTI | Safety mechanism must react before this time |
| Fail-safe | Safe state defined and tested |

---

*Next: [Part 19 — Debugging & Troubleshooting](part-19-debugging-troubleshooting.md)*
