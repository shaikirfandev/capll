# Automotive Engineering Knowledge Base

> A complete learning ecosystem for automotive embedded, ADAS, testing, and validation engineers — from junior test engineer to senior architect.

**300+ documents · 85+ modules · CAPL, C, C++, Python · Production-grade projects**

---

## Where to Start

**Not sure where to begin? Use this decision table:**

| Your Background | Your Goal | Start Here |
|-----------------|-----------|-----------|
| Complete beginner | Learn automotive testing | [ROADMAP.md](ROADMAP.md) → Phase 1 |
| Know software testing | Learn CAN/ECU specifics | [protocol_study_material/](protocol_study_material/) |
| Know CAN basics | Learn CANoe/CAPL | [MG_HECTOR_INFOTAINMENT_VALIDATION/](MG_HECTOR_INFOTAINMENT_VALIDATION/) `START_HERE` folder |
| Know CANoe | Learn DBC file creation | [dbc_canoe_training/](dbc_canoe_training/) |
| Know C | Build an ADAS ECU | [adas_ecu_c/](adas_ecu_c/) |
| Know C++ | Build production ADAS software | [adas_ecu_cpp/](adas_ecu_cpp/) |
| Know Python | Automate CAN/UDS testing | [python_automotive_automation_testing/](python_automotive_automation_testing/) |
| Preparing for interviews | Any automotive role | [interview_preparation/](interview_preparation/) |
| Experienced engineer | ADAS AI / Autonomy | [adas_ai_master/](adas_ai_master/) |

---

## Master Learning Roadmap

> See [ROADMAP.md](ROADMAP.md) for the full phase-by-phase plan with week estimates.

```
Phase 1 — Foundations (Weeks 1–4)
  CAN protocol → UDS basics → CANoe basics → First CAPL script

Phase 2 — Core Skills (Weeks 5–12)
  DBC creation → CAPL test modules → Python CAN → Signal validation

Phase 3 — Intermediate (Weeks 13–20)
  ADAS testing → Ethernet/SOME-IP → HIL concepts → ISO 26262

Phase 4 — Advanced (Weeks 21–28)
  Sensor fusion → Autonomous stack → Cybersecurity → AUTOSAR

Phase 5 — Interview Ready (Weeks 29–32)
  100 Q&A banks → STAR scenarios → Live coding practice
```

---

## Full Directory Reference

### CAPL & Vector Tools

| Folder | What it teaches | Level |
|--------|----------------|-------|
| [capl_scripts/](capl_scripts/) | 26 progressive CAPL scripts: Hello World → UDS → CAN FD → XCP | Beginner → Advanced |
| [capl_suites/](capl_suites/) | CANoe test suites for ADAS / Cluster / Infotainment / Telematics ECUs | Intermediate |
| [dbc_canoe_training/](dbc_canoe_training/) | **Complete DBC program**: 12 modules, DBC syntax, CANdb++, CANoe simulation, validation, 100 Q&A | Beginner → Advanced |
| [vector_tools/](vector_tools/) | CANoe and CANalyzer complete guide | Beginner |
| [vteststudio/](vteststudio/) | Vector vTESTstudio automated testing framework | Intermediate |
| [dbc_arxml_files/](dbc_arxml_files/) | Sample DBC / ARXML reference files | Reference |

**Quick start for CAPL:** `capl_scripts/script_01_hello_world.capl` → work through to `script_26_*`

---

### Protocols & Communication

| Folder | Coverage | Level |
|--------|----------|-------|
| [protocol_study_material/](protocol_study_material/) | CAN, CAN FD, ISO-TP, DoIP, SOME/IP, FlexRay, J1939, LIN, OBD2, SecOC, XCP — 13 guides | Beginner → Intermediate |
| [uds_diagnostics/](uds_diagnostics/) | ISO 14229 complete + STAR scenarios for 4 ECU domains | Intermediate |
| [obd2_diagnostics/](obd2_diagnostics/) | OBD2 full guide + STAR scenarios | Beginner |
| [j1939/](j1939/) | SAE J1939 heavy-duty vehicle protocol | Intermediate |
| [lin_testing/](lin_testing/) | LIN bus testing guide | Beginner |
| [ethernet_automotive/](ethernet_automotive/) | Automotive Ethernet guide | Intermediate |
| [automotive_ethernet_course/](automotive_ethernet_course/) | 15-module course: Ethernet → SOME/IP → DoIP → testing → 300 Q&A | Beginner → Advanced |
| [xcp_calibration/](xcp_calibration/) | XCP real-time calibration protocol | Intermediate |

**Quick start for protocols:** `protocol_study_material/01_can_protocol.md` first, then pick your domain.

---

### ADAS & Autonomous Driving

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [adas_ecu_c/](adas_ecu_c/) | ADAS ECU firmware in C11 (AUTOSAR BSW, MCAL, state machines) | Intermediate |
| [adas_ecu_cpp/](adas_ecu_cpp/) | ADAS ECU in C++17 (HAL, CAN, sensor fusion, LKA/ACC/AEB) | Intermediate |
| [adas_ecu_master/](adas_ecu_master/) | 29-module complete ADAS ECU course (beginner to production) | Beginner → Advanced |
| [adas_l4_project/](adas_l4_project/) | SAE Level 4 autonomous stack (perception, path planning, collision avoidance) | Advanced |
| [adas_framework/](adas_framework/) | Enterprise ADAS test framework (ISO 26262, CI/CD, radar/camera/fusion) | Advanced |
| [adas_ai_master/](adas_ai_master/) | 45-module ADAS AI program: Math → PyTorch → SLAM → ROS2 → CARLA | Advanced |
| [adas_release_test_suite_python/](adas_release_test_suite_python/) | 250 automated ADAS test cases (AEB, FCW, ACC, LKA, BSD, DMS) | Intermediate |
| [adas_rt_cpp_project/](adas_rt_cpp_project/) | Real-time ADAS system with Bazel build | Advanced |
| [adas_scenario_questions/](adas_scenario_questions/) | 10 ADAS feature scenario Q&As with STAR answers | Interview Prep |
| [adas_infotainment_validation/](adas_infotainment_validation/) | ADAS + Infotainment full validation lifecycle (6 guides) | Intermediate |
| [sensor_fusion/](sensor_fusion/) | Sensor fusion theory + STAR scenarios + CAPL examples | Intermediate |
| [advanced_automotive_learning/](advanced_automotive_learning/) | Ethernet, SOME/IP, DoIP, ADAS basics, Radar/LiDAR, CarMaker/dSPACE | Intermediate |
| [ADAS_Algorithm_Integration_Learning_Plan.md](ADAS_Algorithm_Integration_Learning_Plan.md) | Algorithm integration learning plan (root file) | Intermediate |
| [Detailed_ADAS_Integration_Learning_Guide.md](Detailed_ADAS_Integration_Learning_Guide.md) | Detailed integration guide (root file) | Intermediate |

---

### Embedded C / C++ & ECU Development

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [C_CPP_Learning/](C_CPP_Learning/) | Structured C/C++ master course: fundamentals → modern C++17 → concurrency | Beginner → Advanced |
| [c_cpp_adas/](c_cpp_adas/) | C/C++ specifically for ADAS (Kalman, path planning, FreeRTOS, ISO 26262) | Intermediate |
| [c_cpp_bms/](c_cpp_bms/) | C/C++ for Battery Management Systems (SoC/SoH, contactor FSM, UDS) | Intermediate |
| [cpp_automotive/](cpp_automotive/) | C++ automotive software: MISRA, AUTOSAR, design patterns, templates, RTOS | Intermediate |
| [silicon_validation_embedded_c/](silicon_validation_embedded_c/) | Pre/post-silicon validation, IP test engineering, bring-up, embedded C | Advanced |
| [ecu_can_uds_project/](ecu_can_uds_project/) | Production ECU project: CAN + UDS + ISO-TP + DTC + CAPL scripts | Intermediate |
| [ecu_embedded_testing_automotive/](ecu_embedded_testing_automotive/) | ECU embedded testing guide (MIL/SIL/PIL/HIL, UDS, Python, 50+ Q&A) | Intermediate |
| [autosar_basics/](autosar_basics/) | AUTOSAR architecture fundamentals | Beginner |
| [misra_coding_standards/](misra_coding_standards/) | MISRA C 2012 rules reference | Reference |

---

### Python & Test Automation

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [python_scripts/](python_scripts/) | 16 standalone scripts: CAN, UDS, LIN, BMS, OBD2, HIL, ADAS, OTA | Beginner |
| [python_suites/](python_suites/) | Domain suites: ADAS / Cluster / Infotainment / Telematics | Intermediate |
| [python_automotive_automation_testing/](python_automotive_automation_testing/) | Full automation: signal validation, diagnostics, HIL, OTA, CI reports | Intermediate |
| [python_testing_framework/](python_testing_framework/) | Enterprise PyTest + Robot Framework ADAS framework (ASIL A–D, 25 features) | Advanced |
| [python_robot_framework_powertools/](python_robot_framework_powertools/) | Python + Robot Framework for embedded/BLE testing + CI/CD | Intermediate |

**Quick start for Python:** `python_scripts/` → `python_automotive_automation_testing/` → `python_testing_framework/`

---

### Testing, HIL & Validation Frameworks

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [hil_testing/](hil_testing/) | HIL architecture, bench setup, ADAS HIL, regression testing, Robot Framework | Intermediate |
| [carmaker_dspace_learning/](carmaker_dspace_learning/) | IPG CarMaker + dSPACE SCALEXIO: 10 modules, HIL debugging, ADAS validation | Intermediate |
| [model_based_testing/](model_based_testing/) | MIL / SIL / HIL testing levels guide | Beginner |
| [hw_test_framework/](hw_test_framework/) | Hardware validation framework (C++17 + Python, CI/CD, observability) | Advanced |
| [tcu_validation_framework/](tcu_validation_framework/) | Enterprise TCU validation (CAN, UDS, OTA, fault injection, reports) | Advanced |
| [functional_safety/](functional_safety/) | ISO 26262 fundamentals | Beginner |
| [automotive_tools_learning/](automotive_tools_learning/) | LDRA (static analysis), VectorCAST (unit test/coverage), GTest/GMock | Intermediate |

---

### Domain-Specific Systems

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [MG_HECTOR_INFOTAINMENT_VALIDATION/](MG_HECTOR_INFOTAINMENT_VALIDATION/) | **50-module** production infotainment lab: CANoe, CAPL, Android Auto, CarPlay, Bluetooth, USB, OTA, UDS | Beginner → Advanced |
| [bms_validation/](bms_validation/) | BMS CAPL scripts + Python + technical reference | Intermediate |
| [hvpt_charging_systems/](hvpt_charging_systems/) | EV high-voltage powertrain + charging systems (16 sections) | Advanced |
| [cluster_scenarios/](cluster_scenarios/) | Instrument cluster validation: speed, RPM, warnings, ADAS display, stress | Intermediate |
| [infotainment_scenarios/](infotainment_scenarios/) | Infotainment scenario Q&As: BT, USB, CarPlay, navigation, HMI, OTA | Intermediate |
| [telematics_scenario_questions/](telematics_scenario_questions/) | Telematics/TCU validation: V2X, OTA, eCall, cellular, cybersecurity | Intermediate |
| [byd_sealion7/](byd_sealion7/) | Deep-dive: BYD Sealion 7 EV architecture, E/E, ADAS, software, OTA | Reference |
| [bluetooth_firmware/](bluetooth_firmware/) | Bluetooth firmware development and testing | Intermediate |

---

### Cybersecurity

| Folder | What it contains | Level |
|--------|-----------------|-------|
| [cybersecurity_automotive/](cybersecurity_automotive/) | ISO/SAE 21434, TARA, AUTOSAR Security, ECU hardening, OTA security, pen testing | Advanced |

---

### Functional Safety & Standards

| Folder | What it contains |
|--------|-----------------|
| [functional_safety/](functional_safety/) | ISO 26262 Part 1–10 fundamentals |
| [autosar_basics/](autosar_basics/) | AUTOSAR Classic/Adaptive architecture |
| [misra_coding_standards/](misra_coding_standards/) | MISRA C 2012 rules (required/advisory) |
| [requirement_engineering/](requirement_engineering/) | EARS patterns, DOORS, ASPICE, traceability |
| [automotive_homologation/](automotive_homologation/) | Type approval, UN ECE regulations, certification |
| [bug_management_automotive/](bug_management_automotive/) | Bug lifecycle, Jira, RCA across ECU domains |

---

### Interview Preparation

| Folder | What it contains |
|--------|-----------------|
| [interview_preparation/](interview_preparation/) | **20+ files**: intro scripts, 80+ technical Q&A, STAR answers, salary negotiation, live CAPL coding |
| [senior_automotive_testing_lead/](senior_automotive_testing_lead/) | Senior Lead / Manager prep (strategy, leadership, team, stakeholders) |
| [adas_scenario_questions/](adas_scenario_questions/) | FCW, AEB, LDW, BSD, TSR, parking — STAR format |
| [sensor_fusion/](sensor_fusion/) | 10 STAR interview scenarios for sensor fusion roles |
| [uds_diagnostics/](uds_diagnostics/) | STAR scenarios for ADAS, telematics, cluster, infotainment |
| [advanced_debugging_rca/](advanced_debugging_rca/) | RCA deep dives, JIRA management, log analysis |
| [marelli_cluster_lead/](marelli_cluster_lead/) | Role-specific prep for Instrument Cluster Lead position |
| [CAPL_Interview_100_QA.md](CAPL_Interview_100_QA.md) | 100 CAPL interview questions and answers (root file) |
| [Automotive_Test_Validation_250_Detailed_Answers.md](Automotive_Test_Validation_250_Detailed_Answers.md) | 250 automotive test validation Q&A (root file) |

**For interview prep:** Start at [interview_preparation/](interview_preparation/) → add domain STAR scenarios → practice live coding in `capl_scripts/`.

---

### Career Transition Guides

| Folder | Target Role |
|--------|------------|
| [forward_deployment_engineer/](forward_deployment_engineer/) | Site Reliability / Forward Deployment Engineer (full-stack + cloud + DevOps) |
| [senior_data_engineer/](senior_data_engineer/) | Senior Data Engineer (SQL → Spark → cloud → AI data pipelines) |
| [product_manager/](product_manager/) | Product Manager (frameworks, roadmap, 200 Q&A bank) |
| [automotive_project_manager/](automotive_project_manager/) | Automotive Project Manager (Agile, ASPICE, 200 Q&A) |
| [silicon_validation_career_transition/](silicon_validation_career_transition/) | Silicon Validation Engineer |
| [medical_device_validation/](medical_device_validation/) | Medical Device Validation (ISO 13485, FDA 21 CFR Part 11) |
| [f1_career_roadmap/](f1_career_roadmap/) | F1 Motorsport Engineering |
| [mckinsey_auto_firm_strategy/](mckinsey_auto_firm_strategy/) | Automotive Consulting / Firm Strategy |

---

### Root-Level Reference Files

| File | What it is |
|------|-----------|
| [ROADMAP.md](ROADMAP.md) | Master 30-week learning plan with tool priority matrix |
| [GLOSSARY.md](GLOSSARY.md) | 100+ automotive/embedded terms A–Z |
| [README_Scripts.md](README_Scripts.md) | Guide to all 26 CAPL scripts |
| [CAPL_Language_Overview.md](CAPL_Language_Overview.md) | CAPL language quick overview |
| [CAPL_Learning_Guide.md](CAPL_Learning_Guide.md) | Structured CAPL learning guide |
| [CAPL_Data_Structures_Guide.md](CAPL_Data_Structures_Guide.md) | CAPL data types and structures |
| [CAPL_Events_Guide.md](CAPL_Events_Guide.md) | CAPL event handlers reference |
| [CAPL_Real_Work_Interview_Scenarios.md](CAPL_Real_Work_Interview_Scenarios.md) | CAPL real-work and interview scenarios |
| [CAPL_Interview_100_QA.md](CAPL_Interview_100_QA.md) | 100 CAPL interview Q&A |
| [Automotive_Test_Validation_250_Detailed_Answers.md](Automotive_Test_Validation_250_Detailed_Answers.md) | 250 automotive test Q&A |
| [Automotive_Test_Validation_250_Detailed_Answers_With_Scenarios.md](Automotive_Test_Validation_250_Detailed_Answers_With_Scenarios.md) | Same Q&A with real-world scenarios |

---

## Learning Paths by Role

### Path A — Automotive Test Engineer (Fresh Graduate)
```
Week 1–2:  GLOSSARY.md + protocol_study_material/01_can_protocol.md
Week 3–4:  capl_scripts/ (01–10) + vector_tools/
Week 5–6:  dbc_canoe_training/ (Modules 01–04)
Week 7–8:  uds_diagnostics/ + obd2_diagnostics/
Week 9–10: python_scripts/ + python_automotive_automation_testing/
Week 11–12: interview_preparation/ + Automotive_Test_Validation_250_Detailed_Answers.md
```

### Path B — ADAS Validation Engineer
```
Week 1–2:  protocol_study_material/ + functional_safety/01_iso26262_fundamentals.md
Week 3–4:  adas_ecu_master/ (01–10)
Week 5–6:  sensor_fusion/ + adas_scenario_questions/
Week 7–8:  adas_framework/ + hil_testing/
Week 9–10: python_testing_framework/ + carmaker_dspace_learning/
Week 11–12: cybersecurity_automotive/ + interview_preparation/
```

### Path C — ADAS Embedded Developer
```
Week 1–4:  C_CPP_Learning/ + cpp_automotive/
Week 5–8:  adas_ecu_c/ → adas_ecu_cpp/ → adas_ecu_master/
Week 9–12: adas_l4_project/ + sensor_fusion/
Week 13–16: autosar_basics/ + misra_coding_standards/ + ecu_can_uds_project/
Week 17–20: adas_ai_master/ (01–20)
```

### Path D — Infotainment / HMI Test Engineer
```
Week 1–4:  MG_HECTOR_INFOTAINMENT_VALIDATION/ (START_HERE → CANoe → CAPL sections)
Week 5–6:  capl_suites/infotainment_capl_suite/
Week 7–8:  infotainment_scenarios/ + cluster_scenarios/
Week 9–10: uds_diagnostics/05_infotainment_star_scenarios.md
Week 11–12: advanced_automotive_learning/02_SOMEIP/ + automotive_ethernet_course/
```

### Path E — Interview Prep (2–4 weeks intensive)
```
Week 1: interview_preparation/ — read all 20+ files
Week 2: Pick your domain Q&A (adas_scenario_questions/ OR infotainment_scenarios/ OR telematics_scenario_questions/)
Week 3: CAPL_Interview_100_QA.md + dbc_canoe_training/modules/10_interview_preparation.md
Week 4: Mock practice — capl_scripts/ live coding + advanced_debugging_rca/
```

### Path F — Senior / Lead Engineer
```
Month 1: cybersecurity_automotive/ + functional_safety/ + requirement_engineering/
Month 2: adas_framework/ + python_testing_framework/ + hw_test_framework/
Month 3: adas_ai_master/ + adas_l4_project/ + silicon_validation_embedded_c/
Month 4: senior_automotive_testing_lead/ + automotive_project_manager/ + advanced_debugging_rca/
```

---

## Standards Coverage

| Standard | Coverage Location |
|----------|------------------|
| ISO 11898 (CAN) | `protocol_study_material/` · `dbc_canoe_training/modules/12_*` |
| ISO 14229 (UDS) | `uds_diagnostics/` · `ecu_can_uds_project/` |
| ISO 26262 (FuSa) | `functional_safety/` · `adas_framework/` · `dbc_canoe_training/modules/12_*` |
| ISO/SAE 21434 (Cyber) | `cybersecurity_automotive/` |
| AUTOSAR | `autosar_basics/` · `adas_ecu_cpp/` · `cpp_automotive/` |
| MISRA C:2012 | `misra_coding_standards/` · `adas_l4_project/` |
| ASPICE | `dbc_canoe_training/modules/09_*` · `interview_preparation/` |
| SAE J1939 | `j1939/` · `protocol_study_material/` |
| UNECE R155/R156 | `cybersecurity_automotive/` · `automotive_homologation/` |
| ISO 13485 (Medical) | `medical_device_validation/` |

---

## Tools & Languages

| Tool / Language | Where to Learn |
|-----------------|---------------|
| Vector CANoe | `vector_tools/` · `dbc_canoe_training/modules/06_*` · `MG_HECTOR_INFOTAINMENT_VALIDATION/` |
| CANdb++ | `dbc_canoe_training/modules/05_*` |
| CAPL | `capl_scripts/` · `CAPL_*.md` (root files) · `capl_suites/` |
| Python + cantools | `python_scripts/` · `dbc_canoe_training/resources/` |
| Python + pytest | `python_testing_framework/` · `adas_release_test_suite_python/` |
| Robot Framework | `python_robot_framework_powertools/` · `hil_testing/` |
| dSPACE SCALEXIO | `carmaker_dspace_learning/` |
| IPG CarMaker | `carmaker_dspace_learning/` |
| GTest / GMock | `automotive_tools_learning/` |
| VectorCAST | `automotive_tools_learning/` |
| LDRA | `automotive_tools_learning/` |
| C++17 (MISRA) | `C_CPP_Learning/` · `cpp_automotive/` · `adas_ecu_cpp/` |
| Bazel | `adas_rt_cpp_project/` |
| ROS2 | `adas_ai_master/` |

---

## Stats

- **85+ modules / domains**
- **300+ markdown documents**
- **29 CAPL scripts** (progressive)
- **16 Python automation scripts**
- **1,000+ interview Q&A** across all domains
- **Languages:** CAPL · C · C++17 · Python · Bash · SQL
- **OEM/Tier-1 context:** Bosch · Continental · Aptiv · Tesla · NVIDIA · BYD · Valeo · Marelli

---

*Start with [ROADMAP.md](ROADMAP.md) if you want a structured weekly plan. Use the tables above to jump directly to any domain.*
