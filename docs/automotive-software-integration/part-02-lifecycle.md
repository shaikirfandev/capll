# Part 2 — ECU Integration Lifecycle

The ECU integration lifecycle covers the end-to-end journey from a customer requirement to a validated, deployed software release on a production vehicle.

---

## Overview: 20-Phase Lifecycle

```
1  Requirement Analysis
2  System Architecture
3  Software Architecture
4  Interface Definition
5  Development
6  Configuration
7  Build
8  Static Analysis
9  Unit Testing
10 Software Integration
11 ECU Integration
12 Network Integration
13 HIL Integration
14 Vehicle Integration
15 Validation
16 Diagnostics
17 Release
18 OTA Deployment
19 Field Monitoring
20 Maintenance
```

---

## Phase 1 — Requirement Analysis

**Purpose:** Understand what the ECU/feature must do.

| Item | Detail |
|---|---|
| **Inputs** | Customer spec, OEM requirements, SRS, system spec |
| **Activities** | Parse, clarify, decompose requirements; identify interfaces |
| **Outputs** | Software Requirements Specification (SRS), Requirement IDs |
| **Responsibilities** | Integration Engineer, Systems Engineer |
| **Tools** | DOORS, Polarion, Jira, Excel |
| **Artifacts** | SRS document, requirement traceability matrix (RTM) |
| **Common Failures** | Ambiguous requirements, missing interface definitions |
| **Entry Criteria** | System-level requirements available |
| **Exit Criteria** | All requirements reviewed, baselined, and assigned IDs |

---

## Phase 2 — System Architecture

**Purpose:** Define the overall system structure: ECUs, networks, interfaces.

| Item | Detail |
|---|---|
| **Inputs** | SRS, vehicle network topology, hardware specs |
| **Activities** | Define ECU topology, communication matrix, network design |
| **Outputs** | System architecture document, network topology diagram |
| **Responsibilities** | System Architect, Integration Lead |
| **Tools** | Enterprise Architect, Visio, MATLAB/Simulink |
| **Artifacts** | System architecture doc, communication matrix |
| **Common Failures** | Interface overlaps, bandwidth underestimation |
| **Entry Criteria** | Requirements baselined |
| **Exit Criteria** | Architecture reviewed and approved |

---

## Phase 3 — Software Architecture

**Purpose:** Define software components, their interactions, and allocation to ECUs.

| Item | Detail |
|---|---|
| **Inputs** | System architecture, SRS, AUTOSAR methodology |
| **Activities** | Define SWCs, ports, interfaces, runnable entities |
| **Outputs** | Software architecture document, ARXML skeleton |
| **Responsibilities** | Software Architect |
| **Tools** | Vector DaVinci Developer, EB tresos, PREEvision |
| **Artifacts** | ARXML, SWC descriptions, port interface definitions |
| **Common Failures** | Circular dependencies, missing runnable activation |
| **Entry Criteria** | System architecture approved |
| **Exit Criteria** | All SWCs defined, interfaces agreed |

---

## Phase 4 — Interface Definition

**Purpose:** Precisely define all external and internal interfaces.

| Item | Detail |
|---|---|
| **Inputs** | Software architecture, system architecture |
| **Activities** | Define ICD (Interface Control Document), CAN DBC files, ARXML ports |
| **Outputs** | ICD, DBC files, signal matrices, SOME/IP service definitions |
| **Responsibilities** | Integration Engineer, Software Architect |
| **Tools** | CANdb++, Vector DaVinci Developer, Excel |
| **Artifacts** | ICD, DBC, CAN matrix, Ethernet service definition |
| **Common Failures** | Signal value range mismatch, endianness errors, missing signals |
| **Entry Criteria** | Software architecture baselined |
| **Exit Criteria** | All interfaces documented and reviewed by all stakeholders |

---

## Phase 5 — Development

**Purpose:** Implement software components.

| Item | Detail |
|---|---|
| **Inputs** | SRS, SWC definitions, interface definitions |
| **Activities** | Coding, unit testing locally, code review |
| **Outputs** | Source code, unit test results |
| **Responsibilities** | Software Developer |
| **Tools** | IDE (Eclipse, VS Code), Git, compiler (GCC, Green Hills) |
| **Artifacts** | Source code, doxygen documentation |
| **Common Failures** | Missing requirement coverage, unhandled error cases |
| **Entry Criteria** | Requirements and design approved |
| **Exit Criteria** | Code review passed, unit tests green |

---

## Phase 6 — Configuration

**Purpose:** Configure BSW, OS, communication stack, diagnostics for the target ECU.

| Item | Detail |
|---|---|
| **Inputs** | ARXML, ECUC, DBC files, memory map |
| **Activities** | Configure AUTOSAR BSW modules (CanIf, Com, PduR, Dcm, Dem, NvM, Os, EcuM) |
| **Outputs** | Generated configuration code, ECUC parameter sets |
| **Responsibilities** | Integration Engineer |
| **Tools** | Vector DaVinci Configurator, EB tresos, ETAS |
| **Artifacts** | ECUC container files, generated C code |
| **Common Failures** | Wrong buffer sizes, missing DTC configuration, wrong task priorities |
| **Entry Criteria** | Interface definitions finalized |
| **Exit Criteria** | Configuration reviewed, compiler errors resolved |

---

## Phase 7 — Build

**Purpose:** Compile all software components into a flashable binary.

| Item | Detail |
|---|---|
| **Inputs** | Source code, configuration, linker script, compiler flags |
| **Activities** | Compile, link, generate HEX/SREC/BIN, run static analysis pre-checks |
| **Outputs** | Binary image (HEX/SREC/BIN/ELF), build report |
| **Responsibilities** | Build Engineer, Integration Engineer |
| **Tools** | CMake, Make, Green Hills MULTI, GCC, Jenkins |
| **Artifacts** | Build artifacts, build log, version manifest |
| **Common Failures** | Linker errors, stack overflow in linker map, missing libraries |
| **Entry Criteria** | Configuration complete |
| **Exit Criteria** | Clean build, no errors, binary size within flash limits |

---

## Phase 8 — Static Analysis

**Purpose:** Detect code issues without running the code.

| Item | Detail |
|---|---|
| **Inputs** | Source code |
| **Activities** | Run MISRA C/C++ checks, data-flow analysis, rule violations |
| **Outputs** | Static analysis report, violation list |
| **Responsibilities** | Developer, Integration Engineer |
| **Tools** | Polyspace, PC-lint, LDRA, Klocwork, Coverity |
| **Artifacts** | Static analysis report with deviations |
| **Common Failures** | Uninitialized variables, null pointer dereference, array out-of-bounds |
| **Entry Criteria** | Code complete |
| **Exit Criteria** | All mandatory MISRA violations resolved or justified |

---

## Phase 9 — Unit Testing

**Purpose:** Verify individual software units in isolation.

| Item | Detail |
|---|---|
| **Inputs** | Source code, test specification |
| **Activities** | Write and run unit tests, measure code coverage |
| **Outputs** | Unit test report, code coverage report |
| **Responsibilities** | Developer, Test Engineer |
| **Tools** | VectorCAST, GoogleTest, Cantata, pytest |
| **Artifacts** | Test cases, test report, coverage metrics |
| **Common Failures** | Incomplete coverage, untested error paths |
| **Entry Criteria** | Code implementation complete |
| **Exit Criteria** | ≥90% MC/DC coverage (safety-critical), all test cases pass |

---

## Phase 10 — Software Integration

**Purpose:** Integrate software components on a PC/virtual environment first.

| Item | Detail |
|---|---|
| **Inputs** | Compiled SWCs, BSW, OS, stubs for hardware |
| **Activities** | Integrate SWCs with BSW on SIL (Software-in-the-Loop) or emulator |
| **Outputs** | Integration test results, logs |
| **Responsibilities** | Integration Engineer |
| **Tools** | CANoe (virtual), MATLAB/Simulink (MIL/SIL), custom test harness |
| **Artifacts** | SIL test report |
| **Common Failures** | RTE port mismatch, initialization order issues |
| **Entry Criteria** | Unit tests passed, build successful |
| **Exit Criteria** | SWC communication verified in SIL |

---

## Phase 11 — ECU Integration

**Purpose:** Flash binary to target ECU hardware and verify operation.

| Item | Detail |
|---|---|
| **Inputs** | Flashable binary, ECU hardware, test bench |
| **Activities** | Flash ECU, verify boot, run functional tests on real hardware |
| **Outputs** | ECU test results, DTC logs |
| **Responsibilities** | Integration Engineer |
| **Tools** | CANoe, CANape, Trace32, UDS tester |
| **Artifacts** | ECU test report, DTC list |
| **Common Failures** | Bootloader failure, clock misconfiguration, peripheral initialization error |
| **Entry Criteria** | Software integration passed |
| **Exit Criteria** | ECU boots, no unexpected DTCs, basic signals verified |

---

## Phase 12 — Network Integration

**Purpose:** Verify ECU communication on the vehicle network with other ECUs.

| Item | Detail |
|---|---|
| **Inputs** | ECU hardware, CAN/Ethernet test bench, DBC files |
| **Activities** | Connect ECU to network, verify CAN signals, Ethernet services, bus timing |
| **Outputs** | Network test report, bus load measurements |
| **Responsibilities** | Integration Engineer |
| **Tools** | CANoe, CANalyzer, Wireshark, network analyzer |
| **Artifacts** | CAN/Ethernet trace logs, network test report |
| **Common Failures** | Missing CAN IDs, wrong arbitration, SOME/IP service not found |
| **Entry Criteria** | ECU integration passed |
| **Exit Criteria** | All required signals present, timing within spec |

---

## Phase 13 — HIL Integration

**Purpose:** Test ECU in a Hardware-in-the-Loop environment simulating the full vehicle.

| Item | Detail |
|---|---|
| **Inputs** | ECU, HIL simulator (dSPACE, NI, ETAS), test scripts |
| **Activities** | Run automated test cases, inject faults, validate safety mechanisms |
| **Outputs** | HIL test report, regression test results |
| **Responsibilities** | HIL Engineer, Integration Engineer |
| **Tools** | dSPACE ControlDesk/AutomationDesk, CANoe, NI VeriStand |
| **Artifacts** | HIL test report, coverage metrics |
| **Common Failures** | Signal timing mismatch in simulation, missing fault reactions |
| **Entry Criteria** | Network integration passed |
| **Exit Criteria** | All HIL test cases pass, safety mechanisms verified |

---

## Phase 14 — Vehicle Integration

**Purpose:** Validate ECU in the actual vehicle with all other real ECUs.

| Item | Detail |
|---|---|
| **Inputs** | Vehicle with all ECUs installed, test plan |
| **Activities** | Functional tests on vehicle, vehicle communication validation, drive tests |
| **Outputs** | Vehicle test report |
| **Responsibilities** | Vehicle Integration Engineer, Test Driver |
| **Tools** | CANoe, data loggers, oscilloscopes, ADAS validation tools |
| **Artifacts** | Vehicle test report, defect list |
| **Common Failures** | EMC interference, thermal failures, real-world timing issues |
| **Entry Criteria** | HIL testing passed |
| **Exit Criteria** | All vehicle-level test cases pass |

---

## Phase 15 — Validation

**Purpose:** Confirm the system meets all requirements.

| Item | Detail |
|---|---|
| **Inputs** | Requirements, test cases, vehicle test results |
| **Activities** | Requirements-based validation, traceability review, sign-off |
| **Outputs** | Validation report, requirements sign-off |
| **Responsibilities** | Validation Engineer, System Engineer |
| **Tools** | DOORS, Polarion, test management tools |
| **Artifacts** | Validation report, RTM closure |
| **Common Failures** | Missing test coverage for requirements, incomplete traceability |
| **Entry Criteria** | Vehicle testing complete |
| **Exit Criteria** | 100% requirements validated, no critical open defects |

---

## Phase 16 — Diagnostics

**Purpose:** Verify UDS diagnostics, DTC behavior, and OBD compliance.

| Item | Detail |
|---|---|
| **Inputs** | Diagnostic specification, DTC list |
| **Activities** | Test all UDS services, verify DTC set/clear/readout, security access |
| **Outputs** | Diagnostic test report |
| **Responsibilities** | Diagnostics Engineer, Integration Engineer |
| **Tools** | CANoe DiagVIEW, INCA, ODX/ODXA tester, Python UDS scripts |
| **Artifacts** | Diagnostic test report |
| **Common Failures** | Wrong DTC configuration, security seed/key algorithm mismatch |
| **Entry Criteria** | ECU integration validated |
| **Exit Criteria** | All diagnostic test cases pass |

---

## Phase 17 — Release

**Purpose:** Package and release the validated software to OEM / production.

| Item | Detail |
|---|---|
| **Inputs** | Validated software binary, test reports, release notes |
| **Activities** | Create release package, sign binary, generate release notes, upload to artifact repo |
| **Outputs** | Release package (HEX + A2L + docs), release notes |
| **Responsibilities** | Release Manager, Integration Lead |
| **Tools** | Jenkins, Artifactory, GitHub/GitLab releases |
| **Artifacts** | Release package, release notes, build manifest |
| **Common Failures** | Wrong binary version, missing signature, incomplete test evidence |
| **Entry Criteria** | All validation phases passed, no critical defects open |
| **Exit Criteria** | Release approved, package uploaded, notifications sent |

---

## Phase 18 — OTA Deployment

**Purpose:** Deploy software update to vehicles in the field via OTA.

| Item | Detail |
|---|---|
| **Inputs** | Release package, OTA campaign configuration |
| **Activities** | Create OTA campaign, staged rollout, monitor update success rate |
| **Outputs** | OTA deployment report |
| **Responsibilities** | OTA Engineer, Release Manager |
| **Tools** | OTA platform (CARIAD, Airbiquity, Harman), TCU software |
| **Artifacts** | OTA campaign report |
| **Common Failures** | Update failure in field, rollback triggered, network connectivity issues |
| **Entry Criteria** | Release approved, OTA package signed |
| **Exit Criteria** | Target vehicle fleet updated, success rate meets KPI |

---

## Phase 19 — Field Monitoring

**Purpose:** Monitor deployed software in the field for issues.

| Item | Detail |
|---|---|
| **Inputs** | Vehicle telemetry, DTC logs, OTA analytics |
| **Activities** | Monitor DTC trends, crash reports, performance metrics |
| **Outputs** | Field issue report, monitoring dashboard |
| **Responsibilities** | Field Support Engineer, Integration Lead |
| **Tools** | Cloud telemetry platform, log analysis tools |
| **Artifacts** | Field monitoring report |
| **Common Failures** | Unexpected DTC surge, memory leaks in long-running systems |
| **Entry Criteria** | OTA deployment complete |
| **Exit Criteria** | Continuous — ongoing monitoring active |

---

## Phase 20 — Maintenance

**Purpose:** Fix field issues, apply patches, manage software lifecycle.

| Item | Detail |
|---|---|
| **Inputs** | Field issue reports, customer complaints, DTC data |
| **Activities** | Defect analysis, root cause investigation, patch development and regression testing |
| **Outputs** | Patch release, updated documentation |
| **Responsibilities** | Maintenance Engineer, Integration Lead |
| **Tools** | Jira, Git, CANoe, debugger |
| **Artifacts** | Patch release notes, updated RTM |
| **Common Failures** | Regression introduced by patch, incomplete field replication |
| **Entry Criteria** | Field issue confirmed and reproducible |
| **Exit Criteria** | Patch validated and deployed; field KPIs normalize |

---

## Lifecycle Summary Table

| Phase | Key Deliverable | Critical Risk |
|---|---|---|
| 1 Requirement Analysis | SRS | Ambiguous requirements |
| 2 System Architecture | Architecture doc | Interface conflicts |
| 3 Software Architecture | ARXML, SWC design | Circular dependencies |
| 4 Interface Definition | ICD, DBC, matrices | Signal mismatch |
| 5 Development | Source code | Requirement gaps |
| 6 Configuration | Generated BSW config | Wrong buffer sizes |
| 7 Build | HEX/BIN binary | Linker errors |
| 8 Static Analysis | Analysis report | MISRA violations |
| 9 Unit Testing | Test report | Low coverage |
| 10 Software Integration | SIL results | RTE port mismatch |
| 11 ECU Integration | ECU test report | Boot failure |
| 12 Network Integration | CAN/ETH logs | Missing signals |
| 13 HIL Integration | HIL test report | Simulation mismatch |
| 14 Vehicle Integration | Vehicle test report | EMC issues |
| 15 Validation | Validation report | Missing requirements |
| 16 Diagnostics | Diagnostic test report | DTC misconfiguration |
| 17 Release | Release package | Wrong binary version |
| 18 OTA Deployment | OTA campaign report | Update failure |
| 19 Field Monitoring | Monitoring report | Unexpected DTCs |
| 20 Maintenance | Patch release | Regression |

---

*Next: [Part 3 — Communication Integration](part-03-communication.md)*
