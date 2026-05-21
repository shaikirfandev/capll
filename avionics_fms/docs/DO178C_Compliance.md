# DO-178C Compliance Summary
## Avionics FMS v3.2.1 — DAL-B (Guidance), DAL-A (Watchdog/Memory)

| Activity                              | DAL-B | DAL-A | Status |
|---------------------------------------|-------|-------|--------|
| SW Requirements (SRS)                 | ✅    | ✅    | Documented in docs/SRS.md |
| HLD (Software Architecture)           | ✅    | ✅    | docs/HLD.md, docs/Architecture.md |
| LLD (Detailed Design)                 | ✅    | ✅    | docs/LLD.md |
| Source Code                           | ✅    | ✅    | src/ |
| Traceability (SRS→HLD→LLD→Test)       | ✅    | ✅    | @req annotations, | Traceability (SRS→HLD→LLD→Test)       | ✅    | ✅    | @req annotations, | Traceability (SRS→HLD→LLD→Test)       | ✅    | ✅    | @req annotations, | Traceability (SRS→HLD→LLD→Test)       | ✅    | ✅    | @req annotations, | Traceability (SRS→HLD→LLD→Test)    ✅    | ✅    | gcovr branch coverage |
| Coverage — MC/DC                      | N/A   | ✅    | Manual analysis for Watchdog |
| Static Analysis                       | ✅    | ✅    | cppcheck + clang-tidy |
| MISRA C++ compliance                  | ✅    | ✅    | No dynamic allocation, no RTTI |
| FMEA                                  | ✅    | ✅    | docs/FMEA.md |

### No Dynamic Allocation Policy
All safety-critical paths use static arrays only:
- `FaultManager`: `FaultRecord fault_table_[64]`
- `FlightPlanManager`: `FlightPlan active_fp_` (embedded `Waypoint[128]`)
- `SensorFusion`: `float P_[10][10]`, `float Q_[10][10]`, `float R_[3][3]`
- `Arinc429Driver`: `std::array<Arinc429RxCb, 256>` callbacks

### Watchdog DAL-A Justification
Loss of watchdog → undetected software hang → undetected navigation error → possible aircraft controlled flight into terrain. Catastrophic → DAL-A.
