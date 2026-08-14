# Part 14 — Tools Reference

---

## 14.1 Tool Matrix Overview

| Category | Tool | Vendor |
|---|---|---|
| Network analysis | CANoe, CANalyzer | Vector |
| Calibration | CANape, INCA | Vector, ETAS |
| Test automation | vTESTstudio, CAPL | Vector |
| Unit testing | VectorCAST | Vector |
| ECU debug | Lauterbach Trace32 | Lauterbach |
| HIL | dSPACE ControlDesk/AutomationDesk | dSPACE |
| BSW config | EB tresos, DaVinci | Elektrobit, Vector |
| Requirements | DOORS, Polarion | IBM, Siemens |
| Issue tracking | Jira | Atlassian |
| CI/CD | Jenkins, GitHub Actions | Various |
| Build | CMake, Yocto | Open source |
| Python | python-can, pytest | Open source |
| Packet analysis | Wireshark | Open source |
| Android debug | adb, Fastboot | Google |
| Modeling | MATLAB/Simulink | MathWorks |

---

## 14.2 CANoe

**Purpose:** The primary tool for CAN/CAN FD/LIN/Ethernet automotive network simulation, analysis, and testing.

**When used:** CAN/CAN FD/LIN/Ethernet integration testing, HIL, diagnostics, protocol analysis.

**Inputs:** DBC files, ARXML, LDF files, ODX, CAPL scripts

**Outputs:** Message traces, logs, test reports

**Example workflow:**
1. Load DBC file → CANoe parses all signals
2. Start measurement → capture live CAN traffic
3. Create CAPL test script for automated signal verification
4. Run test → export XML test report

**Features:**
- Symbolic signal display (speed, RPM vs raw hex)
- Signal generators (simulate missing ECUs)
- Diagnostic window (UDS via DiagVIEW)
- Python scripting
- CANoe .NET API for automation

**Typical interview questions:**
- How do you simulate a missing ECU in CANoe?
- What is CAPL and how do you write a test case?
- How do you capture and analyze a bus-off event in CANoe?

---

## 14.3 CANalyzer

**Purpose:** Lightweight version of CANoe — primarily for bus analysis without simulation.

**Use:** Quick CAN/LIN bus monitoring and logging.

---

## 14.4 CANape

**Purpose:** ECU calibration and measurement tool.

**When used:** Calibrating ECU parameters (maps, thresholds), measuring live variables, EOL flash.

**Inputs:** A2L files, HEX files, ECU connected via CAN/XCP/Ethernet

**Outputs:** Calibration data files (DAT, HEX), measurement logs

**Key features:**
- Online calibration: change parameter values while ECU is running
- Measurement: log ECU internal variables at high speed (via XCP over Ethernet)
- Flash programming: download new calibration data

---

## 14.5 vTESTstudio

**Purpose:** Create automated test cases for CANoe with graphical test sequence editor.

**When used:** Automated integration testing, regression testing, HIL test execution.

**Features:** Visual state machine editor, requirement traceability, test report generation.

---

## 14.6 CAPL (Communication Access Programming Language)

CAPL is Vector's C-like scripting language embedded in CANoe/CANalyzer.

**Typical use cases:**
- Simulate ECU behavior (respond to CAN messages)
- Write automated test cases (send/receive, timing checks)
- Diagnostic scripting
- Signal manipulation

```c
// CAPL example: automated test with pass/fail
testcase TC_001_SpeedSignalPresent() {
  float speed;
  testWaitForSignalInRange("VehicleSpeed", 0.0, 300.0, 200);
  speed = $VehicleSpeed;
  
  if (speed >= 0.0 && speed <= 300.0) {
    testStepPass("SpeedRange", "Speed: %.1f", speed);
  } else {
    testStepFail("SpeedRange", "Out of range: %.1f", speed);
  }
}
```

---

## 14.7 VectorCAST

**Purpose:** Unit and integration testing for C/C++ embedded code.

**When used:** Safety-critical code unit testing, MC/DC coverage measurement.

**Outputs:** Test report, coverage report (MC/DC, branch, statement).

---

## 14.8 dSPACE ControlDesk / AutomationDesk

**Purpose:** HIL test execution platform.

**ControlDesk:** Real-time monitoring and control of HIL setup (inject signals, monitor ECU outputs).

**AutomationDesk:** Automated test execution with test sequences, fault injection.

**Typical workflow:**
1. Configure HIL model (Simulink plant model on dSPACE hardware)
2. Create test sequence in AutomationDesk
3. Run: inject signals → observe ECU reaction → compare to expected
4. Export test report

---

## 14.9 ETAS INCA

**Purpose:** ECU calibration and measurement (alternative to CANape).

Used by many OEMs and Tier-1s, especially for powertrain ECUs.

---

## 14.10 Lauterbach Trace32

**Purpose:** JTAG/SWD hardware debugger and trace tool.

**When used:** ECU bring-up, crash investigation, task timing analysis, memory analysis.

**Features:**
- Breakpoints, watchpoints on target hardware
- Memory read/write
- ETM trace (instruction-level tracing)
- SMP debugging (multi-core ECUs)
- RTOS-aware debugging (task state, stack)

**Common use case:**
```
ECU crashes → attach Trace32 via JTAG → halt → examine stack trace → identify crash address
→ set breakpoint before crash → step through code → find root cause
```

---

## 14.11 Jenkins

**Purpose:** Open-source CI/CD automation server.

**When used:** Building automotive firmware on every commit, running automated tests, packaging releases.

---

## 14.12 Jira

**Purpose:** Issue tracking and project management.

**When used:** Defect tracking, feature management, sprint planning, release tracking.

**Automotive use:**
- Defect: "ECU bus-off after CAN timeout" → Assigned to integration engineer
- Link: defect → requirement → test case → fix commit

---

## 14.13 IBM DOORS / Siemens Polarion

**Purpose:** Requirements management and traceability.

**DOORS:** Industry standard, long history in automotive OEMs.
**Polarion:** Modern web-based alternative.

**Use:** Store requirements, link to design, code, test cases. Mandatory for ISO 26262.

---

## 14.14 MATLAB / Simulink

**Purpose:** Model-based design for control algorithms.

**When used:** ADAS algorithm development, powertrain control modeling, MIL/SIL testing, auto-code generation.

**Embedded Coder:** Generates production C code from Simulink model directly.

---

## 14.15 Python (python-can, pytest)

See Part 13 for examples.

**python-can:** Library to interface with CAN buses from Python (SocketCAN, PCAN, Vector).
**pytest:** Python test framework — used for automated CAN/Ethernet integration tests, log analysis.

---

## 14.16 Wireshark

**Purpose:** Network packet analyzer.

**When used:** Ethernet/SOME/IP analysis, DoIP diagnostics analysis, TCP/IP troubleshooting.

**Automotive Ethernet setup:**
```
1. Connect automotive Ethernet TAP to capture port
2. Open Wireshark → select Ethernet adapter
3. Filter: udp.port == 30490  (SOME/IP-SD)
4. Filter: tcp.port == 13400  (DoIP)
5. Decode SOME/IP with Vector SOME/IP plugin
```

---

## 14.17 adb / Fastboot (Android Debug Bridge)

**Purpose:** Debug and interact with Android Automotive IVI systems.

```bash
# Check connected device
adb devices

# Get system logs
adb logcat -v time | grep "CarService"

# Pull log file from device
adb pull /data/misc/logd/logcat.log .

# Reboot to bootloader
adb reboot bootloader

# Flash new system image
fastboot flash system system.img
fastboot reboot
```

---

## Summary

| Tool | Primary Use |
|---|---|
| CANoe | CAN/ETH simulation, analysis, test |
| CANape | ECU calibration, measurement |
| CAPL | CANoe scripting for automation |
| VectorCAST | Unit testing, coverage |
| Trace32 | JTAG debug, trace |
| dSPACE | HIL test automation |
| DOORS/Polarion | Requirements traceability |
| Jenkins | CI/CD pipeline |
| python-can | Python CAN test automation |
| Wireshark | Ethernet packet analysis |
| adb | Android IVI debug |

---

*Next: [Part 15 — Requirements & Traceability](part-15-requirements-traceability.md)*
