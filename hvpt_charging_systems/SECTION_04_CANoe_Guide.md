# SECTION 4 — CANoe COMPLETE LEARNING GUIDE
## Beginner to Advanced — Real OEM Projects

---

## 4.1 CANoe INTRODUCTION

### 4.1.1 What is CANoe?

CANoe (CAN open environment) by Vector Informatik is the industry-standard tool for:
- **Bus Simulation**: Simulate ECUs and entire vehicle networks
- **Network Testing**: Automated test execution with test modules
- **Diagnostics**: UDS/OBD diagnostics console
- **Logging & Replay**: Record and replay bus traffic
- **CAPL Scripting**: Automate simulation and testing behavior
- **Panel Design**: Create virtual dashboards/HMI panels

### 4.1.2 CANoe Variants

| Variant | Use Case |
|---------|---------|
| CANoe/CAN | Classic CAN testing and simulation |
| CANoe/CAN FD | CAN FD networks |
| CANoe/LIN | LIN bus simulation |
| CANoe/Ethernet | SOME/IP, DoIP, Ethernet testing |
| CANoe/AUTOSAR | AUTOSAR middleware testing |
| CANoe.DiVA | Automated test generation |

---

## 4.2 CANoe WORKSPACE SETUP

### 4.2.1 Creating a New Configuration

```
STEP-BY-STEP WORKSPACE CREATION:
──────────────────────────────────────────────────────────────
1. Launch CANoe
2. File → New Configuration
3. Select "New Configuration from Wizard"
4. Choose network type: CAN
5. Set baud rate: 500 kbit/s
6. Add CAN channel: Hardware → Vector VN1630, Channel 1

RESULT: Empty configuration with one CAN channel
```

### 4.2.2 DBC File Integration

```
ADDING DBC FILES:
──────────────────────────────────────────────────────────────
Method 1: Via Configuration Editor
  1. Extras → Configuration Editor
  2. Networks section → Right click → Add Database
  3. Browse to EV_Powertrain.dbc
  4. Assign to Network "Powertrain_CAN"

Method 2: Drag and Drop
  1. Open Windows Explorer
  2. Drag .dbc file onto CANoe workspace
  3. CANoe prompts: assign to network → select CAN1

VERIFY: After adding DBC:
  - Trace window shows message names (not raw hex IDs)
  - Signal window can show decoded signal values
  - Write/test CAPL can reference signals by name
```

### 4.2.3 Multi-Bus Configuration

```
MULTI-NETWORK SETUP (EV powertrain example):
──────────────────────────────────────────────────────────────
Network 1: Powertrain_CAN (CAN FD, 500k/2M)
  DBC: EV_Powertrain.dbc
  Hardware: VN1640, Channel 1
  ECUs: VCU, BMS, MCU, OBC, DCDC, PDU

Network 2: Body_CAN (CAN, 125k)
  DBC: Body_LV.dbc
  Hardware: VN1640, Channel 2
  ECUs: BCM, IVI, Climate

Network 3: Diagnostics_CAN (CAN, 500k)
  DBC: Diagnostics.dbc
  Hardware: VN1640, Channel 3
  
Network 4: LIN1 (LIN, 19.2k)
  LDF: Door_LIN.ldf
  Hardware: VN1640, Channel 4 (LIN-capable)
```

---

## 4.3 SIMULATION SETUP

### 4.3.1 Restbus Simulation

Restbus simulation simulates all ECUs that are NOT connected to the bench. This allows testing one real ECU while simulating all others.

```
RESTBUS SIMULATION CONCEPT:
──────────────────────────────────────────────────────────────
Physical bench has: Real BMS ECU
Simulated via CANoe: VCU, MCU, OBC, DCDC, PDU (all others)

CANoe restbus simulator:
  → Sends VCU_Command at correct timing/rate
  → Responds to BMS requests if any
  → Allows test engineer to modify simulated signals
  → Real BMS ECU sees a "complete vehicle" environment

SETTING UP RESTBUS SIMULATION:
1. Load DBC file
2. Simulation → Restbus Simulation
3. CANoe auto-generates simulation nodes from DBC
4. For each message: set Tx = YES for messages NOT from real ECU
5. Set cycle times from DBC SEND_TYPE attributes
6. Start simulation → all messages transmitting at correct rates
```

### 4.3.2 Simulation Node (CANoe Network Node)

```
ADDING A SIMULATION NODE:
──────────────────────────────────────────────────────────────
1. In Simulation Setup window:
   Right click → Insert Network Node
   
2. Name: "VCU_Simulation"
3. Associated network: Powertrain_CAN
4. Assign CAPL program: VCU_Sim.can

5. The CAPL program defines:
   - What messages VCU sends
   - How VCU responds to received messages
   - State machine logic
```

---

## 4.4 MEASUREMENT SETUP

### 4.4.1 Trace Window Configuration

```
TRACE WINDOW SETUP:
──────────────────────────────────────────────────────────────
1. Open Trace Window: Measurement → Add Trace Window

2. Configure columns (right-click header):
   ✓ Time (relative/absolute)
   ✓ Channel
   ✓ ID (decimal/hex)
   ✓ Name (from DBC)
   ✓ DLC
   ✓ Data (hex)
   ✓ Decoded signals
   ✓ Direction (Tx/Rx)

3. Filtering:
   Add Filter → By message ID or name
   Example: Show only BMS_Status (0x310) and VCU_Command (0x100)

4. Highlighting:
   Right click message → Highlight → Select color
   Makes specific messages visually distinct

5. Stop on Error Frame:
   Options → Trigger on error frame
   → CANoe pauses trace when error frame detected
```

### 4.4.2 Signal Window (Signal Viewer)

```
SIGNAL WINDOW:
──────────────────────────────────────────────────────────────
1. Measurement → Add Signal Window (tabular view)

2. Add signals to monitor:
   Right click → Add Signal
   Browse DBC tree: BMS_Status → BMS_SoC → Add

3. Common EV signals to monitor:
   BMS_SoC, BMS_SoH, BMS_PackVoltage, BMS_PackCurrent
   BMS_MaxCellTemp, BMS_MinCellVolt
   VCU_State, VCU_TorqueRequest
   INV_ActualTorque, INV_ActualSpeed
   OBC_OutputPower, OBC_State

4. Signal value display:
   - Numerical value with unit
   - Physical value (after factor/offset applied)
   - Raw hex value (optional)
```

### 4.4.3 Graphics Window (Signal Plots)

```
GRAPHICS/SCOPE WINDOW:
──────────────────────────────────────────────────────────────
1. Measurement → Add Graphics Window

2. Drag signals from Signal window into Graphics window
3. Each signal gets its own Y-axis scale (auto or manual)

4. Useful combinations for EV testing:
   Plot 1: BMS_SoC over time (charging test)
   Plot 2: BMS_PackVoltage + BMS_PackCurrent (power analysis)
   Plot 3: INV_ActualTorque + INV_ActualSpeed (drive test)
   Plot 4: OBC_OutputPower + BMS_MaxCellTemp (charging health)

5. Cursor tools:
   - Measure time between events
   - Calculate rate of change (dV/dt for voltage rise)
```

---

## 4.5 PANEL DESIGN

### 4.5.1 Creating a Virtual Dashboard

Panels allow creating interactive HMI screens for test control and monitoring.

```
PANEL DESIGN — EV POWERTRAIN PANEL:
──────────────────────────────────────────────────────────────
1. Panel Editor: Extras → Panel Editor

2. CONTROLS available:
   ├── Display elements:
   │   ├── Label (static text)
   │   ├── Digital Display (signal value, decimal/hex)
   │   ├── Analog Gauge (like speedometer)
   │   ├── Bar Meter (SoC bar like fuel gauge)
   │   ├── LED indicator (fault state, on/off)
   │   └── Picture/Image
   │
   └── Input elements:
       ├── Button (trigger CAPL event)
       ├── Switch (toggle signal value)
       ├── Slider (set signal value with range)
       ├── Input Box (enter value manually)
       └── Dropdown (enum signal selection)

3. SIGNAL BINDING:
   Right click element → Properties → Signal
   Select: BMS_SoC → element shows live BMS_SoC value
   
4. CONTROL ACTION:
   Button "Send HV_ON command":
     On Click → Set signal VCU_HV_Enable = 1
              → OR call CAPL function HV_ON_Request()
```

### 4.5.2 Example Panel Layout — EV Battery Test Panel

```
╔═══════════════════════════════════════════════════════════╗
║        EV BATTERY MANAGEMENT SYSTEM — TEST PANEL         ║
╠═══════════════════════════════════════════════════════════╣
║  STATE OF CHARGE          STATE OF HEALTH                 ║
║  ████████████░░ 78%        ██████████████ 96%             ║
║  [BMS_SoC Bar Graph]       [BMS_SoH Bar Graph]            ║
╠═══════════════════════════════════════════════════════════╣
║  Pack Voltage: 387.4 V     Pack Current: -45.2 A          ║
║  Max Cell Temp: 32.5°C     Min Cell Volt: 3.842 V         ║
║  Contactor: [CLOSED] 🟢    Isolation: [OK] 🟢            ║
╠═══════════════════════════════════════════════════════════╣
║  COMMANDS:                 FAULT STATUS:                   ║
║  [HV ON]  [HV OFF]         [  ] Overvoltage               ║
║  [CHARGE START]            [  ] Overcurrent                ║
║  [CHARGE STOP]             [  ] Overtemp                   ║
║  [FAULT INJECT]            [  ] Isolation Fault            ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 4.6 DIAGNOSTICS CONSOLE

### 4.6.1 UDS Diagnostics in CANoe

```
DIAGNOSTICS CONSOLE SETUP:
──────────────────────────────────────────────────────────────
1. Open: Diagnostics → Diagnostics Console

2. Load ODX/PDX database (or use manual request builder):
   File → Import Diagnostic Description → Browse to ECU_BMS.odx

3. SEND DIAGNOSTIC REQUEST:
   Method A — ODX-based:
     Select ECU: BMS
     Select Service: ReadDataByIdentifier
     Select DID: 0xF190 (VIN)
     Click "Send" → response decoded automatically
     
   Method B — Manual hex:
     Request: 22 F1 90 (UDS ReadDID, VIN)
     Response decoded from raw bytes: 59 F1 90 [17 VIN bytes]

4. COMMON UDS SERVICES TO TEST (see Section 8 for full details):
   SID 0x10: Diagnostic Session Control
   SID 0x11: ECU Reset
   SID 0x14: Clear DTC
   SID 0x19: Read DTC Information
   SID 0x22: Read Data By Identifier
   SID 0x27: Security Access
   SID 0x2E: Write Data By Identifier
   SID 0x31: Routine Control
   SID 0x3E: Tester Present
```

### 4.6.2 Reading DTCs from BMS via CANoe

```
UDS READ DTC SEQUENCE IN CANoe:
──────────────────────────────────────────────────────────────
Request:  19 02 FF  (ReadDTCInformation, reportDTCByStatusMask, allDTC)
Response: 59 02 FF  (positive response)
           [DTC1_Byte0][DTC1_Byte1][DTC1_Byte2][StatusByte]
           [DTC2_Byte0][DTC2_Byte1][DTC2_Byte2][StatusByte]
           ...

DTC Status Byte:
  Bit 0: testFailed (current fault)
  Bit 3: confirmedDTC (confirmed by debounce)
  Bit 4: testNotCompletedSinceLastClear
  Bit 5: testFailedSinceLastClear
  Bit 6: testNotCompletedThisOperationCycle

Example response for BMS with one fault:
  59 02 FF  0A 80 00 2F
             └──────┘ └─ Status byte (0x2F = bits 0,1,2,3,5)
             DTC = 0x0A8000 → check DTC list
```

---

## 4.7 CANOE TEST MODULES

### 4.7.1 Test Module Overview

CANoe Test Modules provide a structured framework for automated testing with:
- CAPL-based test execution
- Test case results (PASS/FAIL/ERROR)
- Automatic test report generation (HTML/XML/PDF)
- Requirement traceability links

### 4.7.2 CAPL Test Module Structure

```capl
// File: BMS_TestModule.can
// CANoe Test Module for BMS validation

includes
{
  // include shared CAPL libraries
}

variables
{
  msTimer gTimeoutTimer;
  int gTestResult;
  long gExpectedSoC;
}

// ══════════════════════════════════════════════════════════
// TEST SETUP AND TEARDOWN
// ══════════════════════════════════════════════════════════

testcase TC_Setup()
{
  TestReportAddStep("Setup", "Initialize test environment");
  // Set VCU to Normal mode
  $VCU_DriveMode = 1;  // NORMAL
  // Wait for BMS to stabilize
  testWaitForTimeout(2000);
  TestReportAddStep("Setup Complete", "VCU in Normal mode, BMS stable");
}

// ══════════════════════════════════════════════════════════
// TEST CASE 1: BMS SoC Range Validation
// ══════════════════════════════════════════════════════════

testcase TC_BMS_SoC_Range()
{
  float soc;
  TestCaseTitle("TC_BMS_001", "BMS SoC Signal Range Validation");
  TestCaseDescription("Verify BMS_SoC is within valid range 0-100%");
  
  // Read current SoC
  soc = $BMS_SoC;
  
  // Check range
  if (soc >= 0.0 && soc <= 100.0)
  {
    TestStepPass("SoC Range", "BMS_SoC = %.1f%% — WITHIN RANGE [0–100%%]", soc);
  }
  else
  {
    TestStepFail("SoC Range", "BMS_SoC = %.1f%% — OUT OF RANGE!", soc);
  }
}

// ══════════════════════════════════════════════════════════
// TEST CASE 2: BMS Message Timing Validation
// ══════════════════════════════════════════════════════════

testcase TC_BMS_MessageTiming()
{
  long period_ms;
  
  TestCaseTitle("TC_BMS_002", "BMS_Status Message Timing");
  TestCaseDescription("Verify BMS_Status transmitted at 10ms ± 1ms");
  
  // Measure time between 100 consecutive messages
  period_ms = testMeasureMsgPeriod(BMS_Status, 100);
  
  if (period_ms >= 9 && period_ms <= 11)
  {
    TestStepPass("Timing", "BMS_Status period = %d ms — PASS (9–11ms)", period_ms);
  }
  else
  {
    TestStepFail("Timing", "BMS_Status period = %d ms — FAIL! Expected 9–11ms", period_ms);
  }
}

// ══════════════════════════════════════════════════════════
// MAIN TEST EXECUTION
// ══════════════════════════════════════════════════════════

void MainTest()
{
  TestModuleTitle("BMS Validation Suite");
  TestModuleDescription("Complete BMS CAN interface validation");
  
  TC_Setup();
  TC_BMS_SoC_Range();
  TC_BMS_MessageTiming();
  // ... more test cases
}
```

### 4.7.3 Test Report Configuration

```
REPORT SETTINGS:
──────────────────────────────────────────────────────────────
1. Right-click Test Module → Properties → Report
2. Enable: Generate HTML Report
3. Report path: C:\TestReports\BMS_Report_%DATE%.html
4. Include: Verdict, Steps, Traces, Error details
5. XML export for test management (JIRA, ALM) integration
```

---

## 4.8 LOGGING SETUP

### 4.8.1 Logging Configuration

```
CANOE LOGGING SETUP:
──────────────────────────────────────────────────────────────
1. Measurement → Add Logging
2. Configure:
   Format: .blf (Binary Logging Format — most efficient)
           .asc (ASCII — human readable, larger files)
           .mf4 (MDF4 — for data analysis tools)
   
3. Trigger:
   ├── Always: Record entire session
   ├── On Start/Stop: Manual control
   ├── Event-based: Start on specific message/signal
   │   Example: Start when OBC_State changes to CHARGING
   └── Pre/Post trigger: Record X seconds before and Y seconds after event

4. File split:
   Max file size: 500 MB (auto-creates new file when limit reached)
   Max duration: 60 minutes per file

5. Measurement log path:
   C:\Logs\[ProjectName]\[Date]\[TestName]_[Timestamp].blf
```

### 4.8.2 Log Analysis

```
ANALYZING .BLF LOGS IN CANOE:
──────────────────────────────────────────────────────────────
1. File → Open → Select .blf log file
2. CANoe opens in Analysis mode (no hardware required)
3. All windows work: Trace, Signal, Graphics, Statistics
4. Can search for specific messages, signal values, errors

USEFUL ANALYSIS FEATURES:
- Ctrl+F: Search within trace
- Filter by time range: Select start/end time
- Export signals to CSV: Right click signal → Export
- Calculate statistics: Min, Max, Mean, RMS on signals
- Find first occurrence of error frame
```

---

## 4.9 REPLAY CONFIGURATION

```
REPLAY (RESIMULATION) SETUP:
──────────────────────────────────────────────────────────────
1. Measurement → Add Replay Block
2. Load .blf/.asc log file
3. Configure:
   - Start time: begin of replay
   - Channels to replay (select specific CAN channels)
   - Replay speed: 1x, 0.5x, 2x, ...
   - Loop replay: yes/no
   - Network: assign replay to CAN channel

USE CASE: Replay production vehicle log to reproduce a field issue
  1. Get vehicle log from field (via telematics or service download)
  2. Load in CANoe replay
  3. Observe signals as if you were in the vehicle
  4. Analyze fault conditions without needing physical vehicle
```

---

## 4.10 CANOE — EV CHARGING SIMULATION PROJECT

### 4.10.1 Complete EV Charging Simulation Setup

```
PROJECT: EV Charging System Simulation
Goal: Simulate complete AC charging session using CANoe

NODES IN SIMULATION:
  1. EVSE_Simulation  — simulates the charge station
  2. VCU_Simulation   — simulates vehicle VCU
  3. BMS_Simulation   — simulates BMS (SoC starts at 30%)
  4. OBC_Monitor      — logs and validates OBC responses

PANEL: ChargingPanel
  - EVSE AC Voltage display
  - OBC State display
  - BMS_SoC progress bar
  - Charging power display
  - Start/Stop charging buttons
  - Fault injection buttons

TEST MODULE: ChargingValidation
  TC1: Normal charging session (30% → 80%)
  TC2: Charging timeout handling
  TC3: Charging communication fault injection
  TC4: Emergency stop during charging
  TC5: Cold battery charging (temp < 5°C)
```

---

## 4.11 HOW TO DEBUG SIGNALS IN CANoe

### 4.11.1 Signal Debugging Workflow

```
SIGNAL DEBUGGING CHECKLIST:
──────────────────────────────────────────────────────────────
STEP 1: Verify DBC
  ✓ Load correct DBC version (match ECU SW version)
  ✓ Check message ID in trace matches DBC
  ✓ Verify DLC (data length code)

STEP 2: Raw Hex Analysis
  Enable hex column in trace
  Manually decode bytes:
    Frame: 31 04 00 00 62 30 00 00
    BMS_SoC = bits 0–15, Intel byte order
    Byte 0 = 0x31 = 49, Byte 1 = 0x04 = 4
    Raw value (little endian) = 0x0431 = 1073
    Physical = 1073 × 0.5 = 536.5% ← ERROR!
    → Check DBC factor: should be 0.1, not 0.5
    Physical = 1073 × 0.1 = 107.3% ← still wrong
    → Check start bit: maybe signal is at bit 8, not 0
    
STEP 3: Statistics Check
  Signal window → right click → Statistics
  Min, Max, Mean values over time window
  Spike detection: Is value momentarily wrong or always wrong?
  
STEP 4: Compare to Reference
  If you have a known-good log, compare:
    Expected trace: signal = 72.5%
    Current trace: signal = wrong value
  → Difference confirms DBC change in new SW version
  → Request updated DBC from ECU owner

STEP 5: CAPL Trace Output
  Add CAPL debug output: write("BMS_SoC raw = %d", getRawValue(BMS_Status::BMS_SoC));
```

---

## SECTION 4 SUMMARY

CANoe is the complete tool for EV powertrain testing:

| Feature | Use in EV Testing |
|---------|-----------------|
| Restbus simulation | Simulate all ECUs for bench testing single ECU |
| DBC integration | Decode all CAN messages and signals |
| Test modules | Automated test execution with reports |
| Diagnostics console | UDS fault reading, session management |
| Panel design | Virtual dashboard for test control |
| Logging | Record all bus traffic for analysis |
| Replay | Re-run field issues without physical vehicle |
| CAPL scripting | Custom logic for complex test scenarios |

---

*Next: Section 5 — CANalyzer Complete Learning Guide*
