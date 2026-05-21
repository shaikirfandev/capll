# ADAS ECU Master — Complete Learning System

> **Role model:** Senior Automotive Embedded Software Architect (Bosch / Continental / Aptiv level)  
> **Target:** Beginner → Production-grade ADAS ECU Developer in 6 months  
> **Standards:** AUTOSAR, ISO 26262, MISRA C++:2008/2023, ASPICE

---

## Folder Structure

```
ADAS_ECU_MASTER/
│
├── 01_CPP_FOR_ECU/              Modern C++ for embedded ECU development
├── 02_EMBEDDED_CPP/             Embedded constraints, registers, ISRs, timers
├── 03_AUTOSAR/                  AUTOSAR Classic + Adaptive architecture
├── 04_CAN_PROTOCOL/             CAN, CAN FD, DBC, UDS, ISO-TP
├── 05_ADAS_BASICS/              ADAS fundamentals, sensors, perception
├── 06_SENSOR_FUSION/            Kalman filter, sensor integration
├── 07_LKA_MODULE/               Lane Keep Assist — full implementation
├── 08_LDA_MODULE/               Lane Departure Alert — full implementation
├── 09_ACC_MODULE/               Adaptive Cruise Control — full implementation
├── 10_STATE_MACHINES/           Automotive HSM, event-driven design
├── 11_ECU_ARCHITECTURE/         Layered software architecture, SOA
├── 12_RTOS/                     FreeRTOS, OSEK/VDX, scheduling
├── 13_MEMORY_MANAGEMENT/        Static allocation, memory pools, MPU
├── 14_DIAGNOSTICS/              DTC, DEM, DCM, OBD-II
├── 15_UNIT_TESTING/             Google Test, CppUTest, mock CAN, SIL
├── 16_VECTOR_TOOLS/             CANoe, CANalyzer, vTESTstudio
├── 17_MISRA_CPP/                MISRA C++:2008, static analysis, AUTOSAR C++14
├── 18_FUNCTIONAL_SAFETY/        ISO 26262, ASIL, FMEA, watchdogs
├── 19_SYSTEM_DESIGN/            Architecture diagrams, trade-off analysis
├── 20_INTERVIEW_PREPARATION/    Senior engineer Q&A bank (500+ questions)
├── 21_REAL_PROJECTS/            Mini ECU + LKA + ACC + CAN analyzer
├── 22_DEBUGGING_SCENARIOS/      Real-world RCA labs
├── 23_LINUX_FOR_AUTOMOTIVE/     Yocto, Qt, Linux ECU basics
├── 24_AUTOMOTIVE_ETHERNET/      SOME/IP, DDS, Ethernet AVB
├── 25_DOIP_UDS/                 DoIP, UDS services, flashing
├── 26_CMAKE_BUILD_SYSTEM/       CMake for automotive projects
├── 27_GIT_WORKFLOW/             Gerrit, branching, automotive git practices
├── 28_AI_IN_AUTOMOTIVE/         AI inference on ECU, ONNX, TensorRT
└── 29_CAPSTONE_PROJECT/         Full ADAS ECU — LKA + ACC + Diagnostics
```

---

## 90-Day Learning Roadmap

### Month 1: Foundations (Days 1–30)

| Week | Focus | Milestone |
|------|-------|-----------|
| 1 | C++ for ECU (01) | Smart pointers, RAII, templates in automotive context |
| 2 | Embedded C++ (02) + AUTOSAR basics (03) | Interrupts, volatile, AUTOSAR layer model |
| 3 | CAN Protocol (04) | Write CAN parser; decode DBC signals |
| 4 | ADAS Basics (05) + Sensor Fusion intro (06) | Camera/Radar/LiDAR models; Kalman filter |

### Month 2: ADAS Feature Implementation (Days 31–60)

| Week | Focus | Milestone |
|------|-------|-----------|
| 5 | LDA Module (08) | Lane departure detection + alert state machine |
| 6 | LKA Module (07) | PID lateral controller + steering correction |
| 7 | ACC Module (09) | Radar-based speed + distance control |
| 8 | State Machines (10) + ECU Architecture (11) | HSM pattern; layered architecture |

### Month 3: Production Engineering (Days 61–90)

| Week | Focus | Milestone |
|------|-------|-----------|
| 9  | Unit Testing (15) + MISRA (17) | 80% test coverage; MISRA-clean code |
| 10 | Functional Safety (18) + Diagnostics (14) | ASIL-B implementation, DTC logging |
| 11 | Debugging (22) + Vector Tools (16) | Solve 10 debug labs; CANoe scripting |
| 12 | Capstone Project (29) | Full ADAS ECU simulator: LKA + ACC + Diagnostics + CAN |

---

## Weekly Schedule Template

```
Monday:     Theory deep-dive (README + notes)
Tuesday:    Code implementation (follow the .cpp examples, modify them)
Wednesday:  Interview Q&A practice (10 questions from 20_INTERVIEW_PREPARATION)
Thursday:   Debug lab (pick one scenario from 22_DEBUGGING_SCENARIOS)
Friday:     Mini project work (21_REAL_PROJECTS milestone)
Saturday:   Architecture review + diagram drawing
Sunday:     Week summary; update learning log
```

---

## Skill Tier Assessment

```
TIER 0 — Pre-requisite (must have before starting):
  □ C++ basics (classes, functions, pointers)
  □ Git fundamentals
  □ Linux CLI basics

TIER 1 — Junior Automotive Embedded Engineer:
  □ AUTOSAR Classic layer model (MCAL/BSW/RTE/SWC)
  □ CAN frame structure + DBC file reading
  □ Basic state machine implementation
  □ Unit testing with Google Test
  □ MISRA Rule awareness (top 20 rules)

TIER 2 — Mid-Level ADAS Software Engineer:
  □ Full CAN stack implementation (parser, scheduler, DBC)
  □ LKA/LDA/ACC algorithm implementation
  □ ISO 26262 ASIL assessment
  □ Hierarchical state machines (HSM)
  □ ECU memory layout + static allocation patterns
  □ RTOS task design (FreeRTOS / OSEK)

TIER 3 — Senior ADAS ECU Architect:
  □ Full AUTOSAR Adaptive + Classic integration
  □ SOME/IP service design
  □ Sensor fusion algorithm (EKF)
  □ ISO 26262 FMEA + safety mechanism design
  □ ECU system architecture (hardware + software co-design)
  □ SIL/HIL validation strategy
  □ OBD-II + UDS diagnostics implementation
  □ ASPICE process compliance
```

---

## How This Compares to Real Industry

```
Bosch ADAS team workflow (simplified):
  Requirements (DOORS) → SW Architecture (Enterprise Architect)
  → Implementation (C++/AUTOSAR) → Unit Test (Google Test/TPT)
  → Integration Test (CANoe HIL) → Functional Safety Review
  → Release (ASPICE L2/L3 process)

This curriculum mirrors that workflow:
  Each module = one phase of the real engineering process
  Capstone = a simulated full sprint from requirements → test
```
