# C/C++ for ADAS Engineering — Study Guide

> Complete learning path for C and C++ in Advanced Driver Assistance Systems
> Covers sensor data types, Kalman filtering, path planning, RTOS, ISO 26262, and interview preparation

---

## File Structure

| File | Topic | Level |
|---|---|---|
| [01_c_fundamentals_adas.md](01_c_fundamentals_adas.md) | C for ADAS — structs, pointers, bit ops, sensor data, FCW FSM, MISRA | Beginner–Intermediate |
| [02_cpp_oop_algorithms_adas.md](02_cpp_oop_algorithms_adas.md) | C++ OOP — ISensor, Kalman Filter, ObjectTracker, PID, SensorFusion | Intermediate–Advanced |
| [03_rtos_safety_adas.md](03_rtos_safety_adas.md) | FreeRTOS tasks, ISO 26262 ASIL, SOTIF, MPU, WCET | Advanced |
| [04_star_interview_adas.md](04_star_interview_adas.md) | STAR scenarios — Kalman drift, AEB gantry, race condition, SOTIF | Interview Prep |

---

## Recommended Study Path

```
Week 1   → 01_c_fundamentals_adas.md
            Focus: RadarTarget_t, ring buffers, FCW FSM, TTC math, bit manipulation

Week 2   → 02_cpp_oop_algorithms_adas.md
            Focus: ISensor hierarchy, KalmanFilter predict/update, ObjectTracker

Week 3–4 → 02 continued + 03_rtos_safety_adas.md
            Focus: PID, fusion pipeline, FreeRTOS task setup, ASIL table

Week 5   → 03 continued — SOTIF, safety mechanisms, MPU, WCET analysis

Week 6   → 04_star_interview_adas.md
            Practise all 5 STAR scenarios aloud
```

---

## Quick Reference

### Key ADAS Algorithms

| Algorithm | Purpose | Where Covered |
|---|---|---|
| TTC = range / relative_velocity | Forward collision time budget | 01 |
| CFAR threshold | Radar clutter suppression | 02 |
| Kalman predict: x̂ = F·x + B·u | State extrapolation (constant velocity) | 02 |
| Kalman update: x̂ = x̂ + K·(z-H·x̂) | Measurement fusion | 02 |
| Mahalanobis distance | Track-to-detection gating | 02, 04 |
| Quintic polynomial | Lane change path planning | 02 |
| PID: u = Kp·e + Ki·∫e + Kd·ė | Longitudinal/lateral control | 02 |

### ASIL Assignment (ADAS)

| Function | ASIL |
|---|---|
| AEB brake command | ASIL D |
| LKA steering torque | ASIL D |
| FCW audio alert | ASIL B |
| ACC speed control | ASIL B |
| Parking aid beep | QM |

### MISRA C:2012 Top Rules (ADAS context)

| Rule | Summary |
|---|---|
| 10.1 | No implicit integer conversions |
| 11.3 | No cast between pointer types |
| 13.5 | No side-effects in logical operators |
| 14.3 | Controlling expression not invariant |
| 15.5 | Single exit point per function |
| 17.7 | Use all non-void return values |

---

## Related Folders

- [../c_cpp_bms/](../c_cpp_bms/) — BMS equivalent guide
- [../cpp_automotive/](../cpp_automotive/) — General C++ for automotive
- [../adas_scenario_questions/](../adas_scenario_questions/) — Domain scenario Q&A
- [../hil_testing/](../hil_testing/) — HIL test framework

---

*Part of the CAPL & Automotive Engineering learning repository*
