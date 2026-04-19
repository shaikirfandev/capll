# Automotive Testing Learning Roadmap
## From Beginner to Senior Automotive Test Engineer

---

## How to Use This Roadmap

Work through each phase sequentially. Each phase builds on the previous.
Estimated duration assumes 1–2 hours of daily study.

---

## Phase 1 – Foundations (4–6 weeks)

**Goal**: Understand automotive networks and basic testing concepts.

### Week 1–2: CAN Bus Fundamentals
- [ ] What is CAN? (ISO 11898, bit timing, arbitration)
- [ ] CAN frame structure (SOF, ID, DLC, DATA, CRC, ACK, EOF)
- [ ] CAN error handling (error frames, passive/bus-off)
- [ ] Practice: [CAPL_Learning_Guide.md](CAPL_Learning_Guide.md)
- [ ] Study: [protocol_study_material/CAN_FD_Study_Material.md](protocol_study_material/CAN_FD_Study_Material.md)

### Week 3: LIN and Other Protocols
- [ ] LIN bus basics (scheduling, frames, master/slave)
- [ ] When to use LIN vs. CAN
- [ ] Study: [protocol_study_material/LIN_Study_Material.md](protocol_study_material/LIN_Study_Material.md)

### Week 4: CAPL Basics
- [ ] Variables, data types, operators
- [ ] `on start`, `on message`, `on timer`, `on key`
- [ ] Practice: [script_01_hello_world.capl](script_01_hello_world.capl) → [script_08_timers.capl](script_08_timers.capl)

### Week 5–6: DBC Files and CANoe
- [ ] DBC file structure, signals, encoding
- [ ] Open DBC in CANdb++, create signals
- [ ] Set up a basic CANoe project
- [ ] Study: [vector_tools/01_canoe_canalyzer_guide.md](vector_tools/01_canoe_canalyzer_guide.md)
- [ ] Practice: [dbc_arxml_files/powertrain_sample.dbc](dbc_arxml_files/powertrain_sample.dbc)

---

## Phase 2 – Core Skills (6–8 weeks)

**Goal**: Write real test scripts and validate ECU behavior.

### Week 7–8: Advanced CAPL
- [ ] Message sending and receiving
- [ ] State machines
- [ ] Bitwise operations and signal decoding
- [ ] Practice: [script_09_receive_messages.capl](script_09_receive_messages.capl) → [script_16_events_comprehensive.capl](script_16_events_comprehensive.capl)

### Week 9–10: UDS Diagnostics
- [ ] UDS service overview (0x10, 0x22, 0x27, 0x2E, 0x19, 0x14)
- [ ] ISO 15765 CAN TP (Single/First/Consecutive/Flow Control frames)
- [ ] Study: [protocol_study_material/ISO15765_CAN_TP.md](protocol_study_material/ISO15765_CAN_TP.md)
- [ ] Study: [uds_diagnostics/](uds_diagnostics/)
- [ ] Practice: [script_17_diagnostics_uds.capl](script_17_diagnostics_uds.capl)

### Week 11–12: Test Automation
- [ ] vTESTstudio test module structure
- [ ] Writing testcase/testgroup in CAPL
- [ ] Test reports (HTML, XML)
- [ ] Practice: CANoe test automation with `testWaitForSignal()`
- [ ] Study: [interview_preparation/12_capl_live_coding.md](interview_preparation/12_capl_live_coding.md)

### Week 13–14: Python for Automotive
- [ ] python-can library (monitoring, logging)
- [ ] cantools (DBC signal decoding)
- [ ] pytest for test automation
- [ ] Study: [python_automotive_automation_testing/](python_automotive_automation_testing/)
- [ ] Practice: [python_automotive_automation_testing/scripts/python_can_bus_monitor.py](python_automotive_automation_testing/scripts/python_can_bus_monitor.py)

---

## Phase 3 – Intermediate (6–8 weeks)

**Goal**: Understand ECU architecture, HIL testing, and modern protocols.

### Week 15–16: AUTOSAR Fundamentals
- [ ] Classic Platform layers (MCAL, ECU Abstraction, BSW, RTE, SWC)
- [ ] S/R and C/S ports
- [ ] DEM, DCM, COM stack
- [ ] Study: [autosar_basics/01_autosar_architecture_overview.md](autosar_basics/01_autosar_architecture_overview.md)

### Week 17–18: HIL Testing
- [ ] HIL architecture (real-time simulator, plant model, I/O boards)
- [ ] Test types (functional, fault injection, regression)
- [ ] dSPACE SCALEXIO overview
- [ ] Study: [hil_testing/01_hil_concepts_and_architecture.md](hil_testing/01_hil_concepts_and_architecture.md)

### Week 19–20: Automotive Ethernet Protocols
- [ ] SOME/IP (service-oriented communication)
- [ ] DoIP (diagnostic over IP)
- [ ] Automotive Ethernet (100BASE-T1, 1000BASE-T1)
- [ ] Study: [protocol_study_material/SOME_IP_Study_Material.md](protocol_study_material/SOME_IP_Study_Material.md)
- [ ] Study: [protocol_study_material/DOIP_Study_Material.md](protocol_study_material/DOIP_Study_Material.md)

### Week 21–22: ADAS Testing
- [ ] Sensor types (radar, camera, LiDAR, ultrasonic)
- [ ] Sensor fusion concepts
- [ ] ADAS feature testing (FCW, AEB, LDW, ACC)
- [ ] Study: [adas_scenario_questions/](adas_scenario_questions/)
- [ ] Study: [sensor_fusion/](sensor_fusion/)

---

## Phase 4 – Advanced (8–10 weeks)

**Goal**: Master functional safety, CI/CD, and senior-level skills.

### Week 23–25: Functional Safety (ISO 26262)
- [ ] HARA, ASIL levels (A–D)
- [ ] Safety goals, FSC, TSC
- [ ] FMEA, FTA, PMHF, FTTI
- [ ] SW safety mechanisms
- [ ] Study: [functional_safety/01_iso26262_fundamentals.md](functional_safety/01_iso26262_fundamentals.md)

### Week 26–27: Bug Management
- [ ] Defect lifecycle, severity, priority
- [ ] Writing good bug reports
- [ ] Root cause analysis
- [ ] Study: [bug_management_automotive/](bug_management_automotive/)

### Week 28–29: CI/CD for Automotive
- [ ] Jenkins/GitLab CI pipelines
- [ ] CANoe headless execution
- [ ] Docker for reproducible builds
- [ ] Study: [ci_cd_automotive/01_cicd_pipeline_guide.md](ci_cd_automotive/01_cicd_pipeline_guide.md)

### Week 30–32: ASPICE and Project Management
- [ ] ASPICE processes (SWE.1–SWE.6, SYS.1–SYS.5)
- [ ] Test metrics and reporting
- [ ] Traceability tools (Jira, DOORS, Polarion)
- [ ] Study: [automotive_project_manager/](automotive_project_manager/)
- [ ] Study: [interview_preparation/14_test_metrics_and_reporting.md](interview_preparation/14_test_metrics_and_reporting.md)

---

## Phase 5 – Interview Readiness (2–3 weeks)

**Goal**: Prepare for senior automotive testing roles.

### Final Prep
- [ ] Study all interview Q&A guides
- [ ] Practice CAPL live coding (whiteboard style)
- [ ] Review STAR scenarios for behavioral questions
- [ ] Mock technical interview with a peer
- [ ] Study: [interview_preparation/](interview_preparation/)
- [ ] Study: [CAPL_Real_Work_Interview_Scenarios.md](CAPL_Real_Work_Interview_Scenarios.md)
- [ ] Study: [senior_automotive_testing_lead/](senior_automotive_testing_lead/)
- [ ] Study: [CAPL_Interview_100_QA.md](CAPL_Interview_100_QA.md)

---

## Key Tools to Learn (Priority Order)

| Priority | Tool | Time to Learn |
|---|---|---|
| 🔴 Essential | Vector CANoe | 2–3 weeks basic |
| 🔴 Essential | CAPL scripting | 3–4 weeks |
| 🔴 Essential | DBC editing (CANdb++) | 1 week |
| 🟡 Important | Python + python-can | 2 weeks |
| 🟡 Important | vTESTstudio | 1 week |
| 🟡 Important | UDS / CAN TP | 1–2 weeks |
| 🟢 Advanced | dSPACE (ControlDesk, SCALEXIO) | 3–4 weeks |
| 🟢 Advanced | AUTOSAR toolchain | 4+ weeks |
| 🟢 Advanced | Jenkins/GitLab CI | 1–2 weeks |

---

## Career Progression

```
Junior Tester (0-2 yrs)
  ↓ Master: CAN basics, CANoe, CAPL, DBC, UDS
  
Mid-Level Tester (2-4 yrs)  
  ↓ Master: HIL testing, test automation, ADAS, AUTOSAR basics

Senior Test Engineer (4-7 yrs)
  ↓ Master: ISO 26262, ASPICE, CI/CD, system validation, team leadership

Test Lead / Manager (7+ yrs)
    Master: Functional safety management, SOTIF, strategy, OTA, Adaptive AUTOSAR
```

---

## Recommended Certifications

| Certification | Relevance |
|---|---|
| **ISTQB Foundation** | Software testing fundamentals |
| **ISTQB Automotive** | Automotive-specific testing |
| **ISO 26262 Functional Safety** (TÜV) | Functional safety engineer certification |
| **ASPICE Assessment** | Process improvement |
| **Vector CANoe Training** | Official Vector training courses |
