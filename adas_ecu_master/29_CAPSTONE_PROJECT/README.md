# 29 — Capstone Project: Full ADAS ECU

> **Project:** Complete ADAS ECU integrating LKA + LDA + ACC + AEB-lite + Diagnostics  
> **Goal:** Demonstrate production-grade embedded C++ design across all 29 modules

---

## 29.1 Requirements Document

### Functional Requirements

| ID   | Requirement                                                                 | Priority |
|------|-----------------------------------------------------------------------------|----------|
| FR01 | LKA shall activate at vehicle speed ≥ 60 km/h with lane quality ≥ MEDIUM   | Must     |
| FR02 | LKA shall apply lateral correction torque up to ±3.0 Nm to EPS             | Must     |
| FR03 | LKA shall deactivate if driver applies > 2.5 Nm for > 0.2s (override)      | Must     |
| FR04 | LDA shall issue visual alert when TLC < 3.0s                                | Must     |
| FR05 | LDA shall issue haptic alert when TLC < 1.5s                                | Must     |
| FR06 | ACC shall maintain target headway gap = v × 1.5s (min 5m)                  | Must     |
| FR07 | ACC shall limit deceleration to ≤ -3.5 m/s² (comfort braking)              | Must     |
| FR08 | AEB-lite shall apply emergency braking if TTC < 1.0s                       | Must     |
| FR09 | ADAS ECU shall log DTC for each fault condition (camera lost, sensor OOB)   | Must     |
| FR10 | ADAS ECU shall respond to UDS 0x22 requests for LKA state and ACC state     | Should   |

### Safety Requirements

| ID   | Safety Requirement                                                          | ASIL |
|------|-----------------------------------------------------------------------------|------|
| SR01 | LKA torque shall not exceed ±3.5 Nm under any software fault condition      | C    |
| SR02 | LKA shall deactivate within 200ms of any internal sensor fault              | C    |
| SR03 | AEB-lite shall be independent from ACC software path (separate ASIL chain)  | D    |
| SR04 | E2E CRC shall be applied to all safety-relevant CAN output signals          | B    |
| SR05 | Watchdog shall reset ECU if main loop does not complete within 15ms         | B    |

---

## 29.2 Architecture Diagram (AUTOSAR Layers)

```
┌───────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (SWC)                             │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────────┐ │
│  │ LKA        │  │ LDA        │  │ ACC + AEB  │  │ Diagnostics     │ │
│  │ Controller │  │ Controller │  │ Controller │  │ Manager (DEM)   │ │
│  │ ASIL C     │  │ ASIL B     │  │ ASIL B/D   │  │ ASIL A          │ │
│  └────────────┘  └────────────┘  └────────────┘  └─────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    System HSM (state manager)                    │ │
│  │         INIT → STANDBY → LKA_ACTIVE / ACC_ACTIVE / FAULT        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────┤
│                        RTE (auto-generated)                            │
├───────────────────────────────────────────────────────────────────────┤
│            BSW: COM | DEM | NvM | BswM | WdgM | DCM                  │
│            PduR | CanIf | CanSM                                        │
├───────────────────────────────────────────────────────────────────────┤
│            MCAL: CanDrv | WdgDrv | NvmDrv (SPI/EEP)                  │
├───────────────────────────────────────────────────────────────────────┤
│            Hardware: AURIX TC277 (or AURIX TC399 for ASIL-D)          │
│            CAN FD controller × 2, EEPROM (SPI), WDG                   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 29.3 Task Scheduling

```
OSEK Task Table:
  LKA_MAIN    — Priority 5, Period 10ms  — LKA state machine + PID + CAN TX
  LDA_MAIN    — Priority 4, Period 10ms  — LDA TLC + alert output
  ACC_MAIN    — Priority 4, Period 50ms  — ACC gap/speed control + CAN TX
  AEB_MONITOR — Priority 6, Period 20ms  — TTC computation, independent of ACC
  DIAG_MAIN   — Priority 2, Period 100ms — DEM processing, NvM write, DCM response
  BG_TASK     — Priority 1, Period 1000ms — Stack watermark, DTC cleanup

ISR:
  CAN_RX_ISR  — Priority 7 (highest) — signals RX semaphore to LKA/ACC tasks
```

---

## 29.4 Implementation Guide

### Step 1: Port LKA to Capstone

```cpp
// Adapt lka_ecu.cpp for capstone:
// 1. Remove standalone main()
// 2. Expose: LkaController::update(const VehicleState& v) → LkaResult
// 3. Add: E2E CRC encoder for LkaTorqueRequest output (simplified CRC8)
// 4. Add: DEM reporting on LKA internal fault
// 5. Integrate with SystemHsm — LKA requests state change via HSM
```

### Step 2: Integrate ACC with AEB-lite

```cpp
// AEB-lite is a separate, simpler class (not reusing ACC PID):
class AebMonitor {
    static constexpr float TTC_THRESHOLD_S = 1.0F;
    static constexpr float AEB_DECEL_MS2   = -8.5F;  // Full emergency stop
public:
    float update(float radarRangeM, float closingSpeedMps) noexcept {
        if (closingSpeedMps <= 0.0F || radarRangeM <= 0.0F) return 0.0F;
        const float ttc = radarRangeM / closingSpeedMps;
        return (ttc < TTC_THRESHOLD_S) ? AEB_DECEL_MS2 : 0.0F;
    }
};
// AEB deceleration takes priority over ACC braking in ESC arbitration
```

### Step 3: CAN Output with E2E CRC

```cpp
// Simple CRC8-SAE J1850 for E2E protection:
uint8_t computeE2eCrc8(const uint8_t* data, uint8_t len) noexcept {
    uint8_t crc = 0xFFU;
    for (uint8_t i = 0U; i < len; ++i) {
        crc ^= data[i];
        for (uint8_t b = 0U; b < 8U; ++b) {
            crc = (crc & 0x80U) ? ((crc << 1U) ^ 0x1DU) : (crc << 1U);
        }
    }
    return crc ^ 0xFFU;
}
```

---

## 29.5 Test Plan

### Unit Tests (GTest)

```
Test file: 15_UNIT_TESTING/test_adas_ecu.cpp (existing + extend)

New test groups for capstone:
  LdaController_Tests:
    TC_LDA_001: TLC > 3.0s → no alert
    TC_LDA_002: TLC < 1.5s → haptic alert
    TC_LDA_003: Indicator active → suppressed
    TC_LDA_004: LaneQuality LOST → suppressed

  AebMonitor_Tests:
    TC_AEB_001: TTC = 0.8s → AEB trigger
    TC_AEB_002: TTC = 2.0s → no AEB
    TC_AEB_003: Zero closing speed → no AEB

  E2E_Tests:
    TC_E2E_001: Known data → known CRC8 value
    TC_E2E_002: Single-bit flip in data → CRC8 mismatch detected
```

### Integration Tests (SIL/HIL)

```
Scenario 1: LKA + ACC active simultaneously, lead vehicle cut-out
  Expected: LKA continues, ACC switches from FOLLOWING to SPEED_CONTROL

Scenario 2: AEB trigger while LKA active
  Expected: LKA deactivates (AEB flag = true suppresses LKA), AEB brakes

Scenario 3: Camera lost during LKA CORRECTING
  Expected: LKA deactivates within 200ms, DTC C1101 logged

Scenario 4: Driver override during LKA
  Expected: OVERRIDE state, 3s hold, return to MONITORING
  Verify: no torque applied during OVERRIDE
```

---

## 29.6 Final Challenge

> Extend the capstone to add a **predictive ACC** (pACC) function:
>
> 1. Add map speed limit signal (new CAN frame: `MAP_Data 0x320`, `SpeedLimitKph`)
> 2. pACC shall slow down to speed limit 200m before a speed limit zone
> 3. Use linear deceleration ramp: `a = (v_current² - v_target²) / (2 × 200m)`
> 4. Add 3 GTest test cases for the deceleration ramp calculation
> 5. Document ASIL allocation: is map data trusted? (Hint: it is QM — requires redundancy from cameras)

---

## 29.7 90-Day Learning Completion Checklist

```
Week 1-4 (Foundation):
  □ 01_CPP_FOR_ECU — read + run ecu_cpp_patterns.cpp
  □ 02_EMBEDDED_CPP — understand volatile, ISR, watchdog
  □ 03_AUTOSAR — understand SWC, RTE, COM stack
  □ 04_CAN_PROTOCOL — run can_parser.cpp, decode a real DBC frame

Week 5-8 (ADAS Core):
  □ 05_ADAS_BASICS — SAE levels, sensor types
  □ 06_SENSOR_FUSION — run sensor_fusion.cpp, understand Kalman filter
  □ 07_LKA_MODULE — run lka_ecu.cpp, tune PID gains
  □ 08_LDA_MODULE — run lda_ecu.cpp, simulate slow drift
  □ 09_ACC_MODULE — run acc_ecu.cpp, simulate cut-in scenario
  □ 10_STATE_MACHINES — run automotive_state_machine.cpp

Week 9-12 (Production Skills):
  □ 11-15 — ECU architecture, RTOS, memory, diagnostics, unit testing
  □ 16 — Vector tools (CANoe/CANape workflow)
  □ 17-18 — MISRA + ISO 26262 (read + apply to capstone)
  □ 19-20 — System design + interview prep (Q&A all sections)
  □ 21-29 — Real project + capstone (integrate and build everything)
  □ 29 CAPSTONE — Complete mini ADAS ECU + all tests + final challenge
```
