# C/C++ for BMS Engineering — Study Guide

> Complete learning path for C and C++ in Battery Management Systems
> Covers cell monitoring, SoC/SoH estimation (Coulomb counting + EKF), contactor FSM, UDS,
> FreeRTOS, ISO 26262, IEC 62619, and interview preparation

---

## File Structure

| File | Topic | Level |
|---|---|---|
| [01_c_fundamentals_bms.md](01_c_fundamentals_bms.md) | C for BMS — cell types, CAN encoding, OV/UV FSM, Coulomb counting, UDS in C | Beginner–Intermediate |
| [02_cpp_oop_algorithms_bms.md](02_cpp_oop_algorithms_bms.md) | C++ OOP — EKF SoC, BmsMonitor, ContactorFsm, CellBalancer, FaultManager | Intermediate–Advanced |
| [03_rtos_safety_bms.md](03_rtos_safety_bms.md) | FreeRTOS tasks, ISO 26262 ASIL, IEC 62619, Watchdog, MPU, WCET | Advanced |
| [04_star_interview_bms.md](04_star_interview_bms.md) | STAR scenarios — SoC drift, OV2 response, NVM corruption, UDS timeout, MISRA | Interview Prep |

---

## Recommended Study Path

```
Week 1   → 01_c_fundamentals_bms.md
            Focus: CellData_t, pack structs, CAN bit ops, coulomb counting in C,
                   contactor FSM, UDS 0x22 handler

Week 2   → 02_cpp_oop_algorithms_bms.md
            Focus: IBmsAlgorithm Strategy pattern, CoulombCountingSoC class

Week 3   → 02 continued — EkfSoC full implementation (predict + update + covariance)

Week 4   → 02 continued + 03_rtos_safety_bms.md
            Focus: BmsMonitor Observer pattern, FaultManager, FreeRTOS task setup

Week 5   → 03 continued — OV2 ASIL B, IEC 62619, weld detection, WWDG, NvM integration

Week 6   → 04_star_interview_bms.md
            Practise all 5 STAR scenarios aloud, revise Q&A table
```

---

## Quick Reference

### BMS Key Algorithms

| Algorithm | Formula | Where |
|---|---|---|
| Coulomb counting | SoC[k] = SoC[k-1] - (η·I·dt)/Q_nom | 01, 02 |
| EKF predict | x̂⁻ = F·x̂, P⁻ = F·P·Fᵀ + Q | 02 |
| EKF update | K = P⁻·Hᵀ / (H·P⁻·Hᵀ + R), x̂ = x̂⁻ + K·(y - Hx̂⁻) | 02 |
| Precharge complete | V_dclink ≥ 0.95 × V_battery | 01, 02 |
| IMD isolation | R_insulation ≥ 500 Ω/V × V_pack | 03 |
| Cell delta | ΔV = V_max − V_min | 01 |
| Balance trigger | V_cell > V_min + 10 mV AND V_cell > 3300 mV | 02 |

### ASIL Assignment (BMS)

| Function | ASIL |
|---|---|
| OV2 detection & contactor open | ASIL B |
| UV2 detection & contactor open | ASIL B |
| Isolation monitoring (IMD) | ASIL B |
| Contactor weld detection | ASIL B |
| SoC estimation | QM |
| Cell balancing | QM |
| UDS diagnostics | QM |

### CAN Message Map

| ID | Name | Period | Key Signals |
|---|---|---|---|
| 0x3A0 | BMS Pack Status | 10ms | SoC, SoH, BMS State, Fault Level |
| 0x3A2 | Pack Voltage/Current | 10ms | V_pack [V×10], I_pack [A×10] |
| 0x3A4 | Temperature | 100ms | T_max, T_min, T_avg |
| 0x3A6 | Cell Extremes | 100ms | V_max_cell, V_min_cell, ΔV |
| 0x7E4/0x7EC | UDS Request/Response | On-demand | ISO 14229 frames |

### UDS DIDs (BMS)

| DID | Name | Length | Scaling |
|---|---|---|---|
| 0xF190 | SoC | 1 byte | × 0.5 = % |
| 0xF191 | SoH | 1 byte | 1 = 1% |
| 0xF192 | Pack Voltage | 2 bytes | × 0.1 = V |
| 0xF193 | Pack Current | 2 bytes | signed, × 0.1 = A |
| 0xF194 | Max Cell Voltage | 2 bytes | 1 = 1 mV |
| 0xF195 | Min Cell Voltage | 2 bytes | 1 = 1 mV |
| 0xE001 | Active DTC Count | 1 byte | raw count |

---

## Related Folders

- [../c_cpp_adas/](../c_cpp_adas/) — ADAS equivalent guide
- [../bms_validation/](../bms_validation/) — CAPL + Python BMS test scripts
- [../cpp_automotive/](../cpp_automotive/) — General C++ for automotive
- [../uds_diagnostics/](../uds_diagnostics/) — UDS protocol deep dive

---

*Part of the CAPL & Automotive Engineering learning repository*
