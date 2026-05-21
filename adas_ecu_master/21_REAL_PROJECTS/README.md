# 21 — Real Projects: Mini ADAS ECU

> **Project:** Integrated ADAS ECU — LKA + LDA + ACC + CAN + Diagnostics  
> **Build:** `g++ -std=c++17` (host) or `arm-none-eabi-g++ -std=c++14` (ECU target)

---

## Project Overview

This mini project integrates all ADAS ECU modules into a single executable:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mini ADAS ECU — main.cpp                     │
├─────────────────────────────────────────────────────────────────┤
│  CanSimulator      ← simulates CAN bus (BCM, EPS, Camera, Radar)│
│  LkaController     ← 07_LKA_MODULE/lka_ecu.cpp (adapted)        │
│  LdaStateMachine   ← 08_LDA_MODULE/lda_ecu.cpp (adapted)        │
│  AccController     ← 09_ACC_MODULE/acc_ecu.cpp (adapted)        │
│  DiagnosticsManager← handles DTC log + UDS read simulation      │
│  AdasHsm           ← 10_STATE_MACHINES/ (system-level HSM)      │
│  MainLoop          ← 10ms periodic task, 50ms slow task         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Build Instructions

```bash
# From adas_ecu_master/ directory:
g++ -std=c++17 -Wall -Wextra -O2 \
    21_REAL_PROJECTS/main.cpp \
    -o 21_REAL_PROJECTS/adas_ecu_demo

./21_REAL_PROJECTS/adas_ecu_demo
```

---

## Project Structure

```
21_REAL_PROJECTS/
├── README.md               ← This file
├── main.cpp                ← Integrated mini ECU entry point
├── requirements.md         ← 10 functional + 5 safety requirements
└── test_plan.md            ← Unit + integration + HIL test plan
```
