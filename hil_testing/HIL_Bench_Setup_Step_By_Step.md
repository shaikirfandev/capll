# HIL Bench Setup & Testing — Complete Step-by-Step Guide
## Tools, Hardware, Wiring, Configuration, Execution, Reporting

**Document Version:** 1.0  
**Date:** 23 April 2026  
**Author:** ADAS Test Engineering  
**Scope:** Complete HIL bench setup from unboxing to first passing test

---

## Table of Contents

1. [What You Need — Hardware List](#1-what-you-need--hardware-list)
2. [What You Need — Software List](#2-what-you-need--software-list)
3. [Step 1 — Bench Physical Assembly](#step-1--bench-physical-assembly)
4. [Step 2 — Power Supply Configuration](#step-2--power-supply-configuration)
5. [Step 3 — CAN Bus Wiring and Termination](#step-3--can-bus-wiring-and-termination)
6. [Step 4 — LIN Bus Wiring](#step-4--lin-bus-wiring)
7. [Step 5 — dSPACE SCALEXIO Setup](#step-5--dspace-scalexio-setup)
8. [Step 6 — Vector Hardware Setup](#step-6--vector-hardware-setup)
9. [Step 7 — CANoe Project Setup](#step-7--canoe-project-setup)
10. [Step 8 — Load DBC / ARXML Databases](#step-8--load-dbc--arxml-databases)
11. [Step 9 — Add Simulation Nodes (CAPL)](#step-9--add-simulation-nodes-capl)
12. [Step 10 — Configure vTestStudio Project](#step-10--configure-vteststudio-project)
13. [Step 11 — ECU Power-On Verification](#step-11--ecu-power-on-verification)
14. [Step 12 — CAN Bus Health Check](#step-12--can-bus-health-check)
15. [Step 13 — Run First CAPL Test Case](#step-13--run-first-capl-test-case)
16. [Step 14 — Run Python Regression Suite](#step-14--run-python-regression-suite)
17. [Step 15 — Fault Injection Procedure](#step-15--fault-injection-procedure)
18. [Step 16 — Measurement and Logging](#step-16--measurement-and-logging)
19. [Step 17 — Report Generation](#step-17--report-generation)
20. [Step 18 — CI/CD Pipeline Setup](#step-18--cicd-pipeline-setup)
21. [Troubleshooting Reference](#troubleshooting-reference)
22. [Appendix — Quick Reference](#appendix--quick-reference)

---

## 1. What You Need — Hardware List

### 1.1 Core HIL Platform

| # | Item | Model / Part | Purpose | Qty |
|---|------|-------------|---------|-----|
| 1 | Real-Time Simulator | **dSPACE SCALEXIO** Processing Unit | Runs vehicle plant model in real-time | 1 |
| 2 | I/O Board | dSPACE **DS2655** Multi-I/O Board | Analog/digital I/O, PWM, encoder | 1–2 |
| 3 | CAN-FD Interface | dSPACE **DS6340** CAN-FD Board | Connect ECU CAN buses to simulator | 1 |
| 4 | LIN Interface Board | dSPACE **DS6230** | LIN bus for parking sensors, mirrors | 1 |
| 5 | Automotive Ethernet | dSPACE **DS6601** 100BASE-T1 | Camera/Radar ECU Ethernet | 1 |

> **Alternative if no dSPACE budget:** Use **NI PXIe chassis** + NI 6341 (analog) + NI 9853 (CAN) + NI VeriStand software.

---

### 1.2 Vector Bus Interface Hardware

| # | Item | Model | Purpose | Qty |
|---|------|-------|---------|-----|
| 6 | CAN/CAN-FD Interface | **Vector VN1640A** (4-ch CAN FD) | Direct ECU-to-PC CAN access | 1 |
| 7 | CAN/LIN Combined | **Vector VN7572** | CAN + LIN in one device | 1 (alt to above) |
| 8 | LIN standalone | **Vector VN1611** | Dedicated LIN bus analysis | 1 |
| 9 | Automotive Ethernet | **Vector VN5640** | 100BASE-T1 / DoIP diagnostics | 1 |

---

### 1.3 Power Supply & Ignition Simulation

| # | Item | Model | Spec | Purpose |
|---|------|-------|------|---------|
| 10 | Bench Power Supply | **EA-PS 2384-05 B** | 0–32V / 0–20A | Simulate KL30, KL15 |
| 11 | Secondary Supply | **Aim-TTi EX2020R** | 0–20V / 0–20A | KL15 separate line |
| 12 | SSR Relay Card | Crydom D2W202F (DIN rail) | 24V control, 2A/240V | Ignition switching |
| 13 | Relay Control Box | Custom (Arduino + SSR) | Digital control of KL15/KL30 | 1 |

---

### 1.4 Fault Injection Hardware

| # | Item | Model | Purpose |
|---|------|-------|---------|
| 14 | Relay Fault Injection Box | **dSPACE FIU-1** or custom SSR | Short/open circuit on any net |
| 15 | Resistor Decade Box | **MultiComp Pro MP730314** | Simulate sensor resistance changes |
| 16 | Signal Multiplexer | Pickering 40-725A | Route signals between ECU and sim |

---

### 1.5 Measurement & Probing

| # | Item | Model | Purpose |
|---|------|-------|---------|
| 17 | Oscilloscope | **Tektronix MDO3014** (4-ch, 100 MHz) | Physical CAN waveform verification |
| 18 | CAN/LIN Probe | Tektronix TAP1500 | Non-intrusive probing |
| 19 | Multimeter | Fluke 87V | Voltage/resistance at ECU pins |
| 20 | Break-out Box | Custom ECU BOB (Break-Out Board) | Access all ECU connector pins |
| 21 | DIN Rail Enclosure | Phoenix Contact ABS enclosure | Organise relay/resistors on bench |

---

### 1.6 Computing Hardware

| # | Item | Spec | Purpose |
|---|------|------|---------|
| 22 | HIL Host PC | Intel i9, 64 GB RAM, Win 11 Pro | Run CANoe, dSPACE ControlDesk, Python |
| 23 | CANoe License Dongle | Vector USB stick | CANoe/vTestStudio license |
| 24 | dSPACE License Server | dSPACE USB dongle | SCALEXIO license |
| 25 | Gigabit Switch | Netgear GS308 | Network between Host PC and SCALEXIO |
| 26 | USB Hub | 7-port USB 3.0 | Connect Vector hardware to PC |

---

### 1.7 ECU Under Test (DUT)

| # | Item | Notes |
|---|------|-------|
| 27 | ADAS ECU (DUT) | Production ECU (or pre-production sample) with all connectors |
| 28 | ECU Harness Adapter | Custom-built break-out cable matching ECU connector pin-out |
| 29 | ECU Mounting Plate | Aluminium plate or DIN rail bracket |

---

## 2. What You Need — Software List

| # | Software | Version | License | Purpose |
|---|---------|---------|---------|---------|
| 1 | **Vector CANoe** | 17.0 SP3+ | Commercial | CAN/LIN bus simulation, test execution |
| 2 | **vTestStudio** | 5.5+ | Included with CANoe | Test module editor and executor |
| 3 | **dSPACE ControlDesk** | 7.4+ | Commercial | SCALEXIO monitoring/control panel |
| 4 | **dSPACE AutomationDesk** | 5.7+ | Commercial | Graphical HIL test scripting |
| 5 | **MATLAB / Simulink** | R2024a | Commercial | Build and compile vehicle plant model |
| 6 | **dSPACE RTI** (Real-Time Interface) | Bundled | Commercial | Deploy Simulink model to SCALEXIO |
| 7 | **Python** | 3.11+ | Free | Test automation scripts |
| 8 | **pytest** | 8.x | Free | Python test runner |
| 9 | **pytest-html** | 4.x | Free | HTML test reports |
| 10 | **pywin32** | latest | Free | CANoe COM interface for Python |
| 11 | **Git** | 2.x | Free | Version control for test scripts |
| 12 | **Jenkins / GitHub Actions** | latest | Free / Cloud | CI/CD overnight regression |
| 13 | **Vector CANdb++** | Bundled | Commercial | DBC database editing |
| 14 | **PEAK PCAN Viewer** | Free | Free | Budget alternative CAN viewer |

---

## Step 1 — Bench Physical Assembly

### 1.1 Layout the Bench

```
[HOST PC] ──USB─── [Vector VN1640A] ──CAN H/L wires─── [ECU Harness BOB]
                                                              │
[dSPACE SCALEXIO] ──Gigabit Ethernet─── [HOST PC]           │ ECU Connector
      │                                                       │
      │ DS6340 CAN FD board                       [ADAS ECU (DUT)]
      └──────────────── CAN H/L ──────────────────────────────┘
      │ DS6230 LIN board ──────────── LIN wire ─── LIN Bus ───┘
      │ DS2655 Analog Out ──────────── 0–5V ──── Speed sensor sim
[POWER SUPPLY] ──12V/GND── [ECU KL30/GND pins]
[RELAY BOX] ──12V switched── [ECU KL15 pin]
```

### 1.2 Mount the ECU

1. Fix ECU on aluminium mounting plate with M6 bolts.
2. Attach Break-Out Box (BOB) cable to ECU connector — do not force pins.
3. Label each BOB terminal with pin number and signal name from ECU pin-out document.
4. Attach BOB to DIN rail for stability.

### 1.3 Ground All Equipment

- Connect Host PC chassis GND → bench GND bus bar.
- Connect SCALEXIO chassis GND → bench GND bus bar.
- Connect ECU GND (KL31) → bench GND bus bar.
- Connect power supply (-) terminal → bench GND bus bar.
- **Single-point grounding** — all equipment shares one common GND bar to avoid ground loops.

---

## Step 2 — Power Supply Configuration

### 2.1 Set KL30 Supply (Battery Positive)

```
Power Supply EA-PS 2384-05 B Settings:
  Voltage : 12.5 V
  Current limit : 15 A (ECU + actuators)
  OVP (overvoltage protection) : 14.5 V

Connection:
  (+) terminal → ECU KL30 pin (battery positive)
  (-) terminal → bench GND bus bar
```

### 2.2 Set KL15 Supply (Ignition)

```
Aim-TTi EX2020R Settings:
  Voltage : 12.0 V
  Current limit : 5 A
  Connected through SSR relay (OFF by default)

Relay Control:
  Arduino digital pin D3 → SSR control input
  SSR output → KL15 pin on ECU

Command to switch ignition ON:
  digitalWrite(3, HIGH);   // KL15 ON
  delay(200);               // Stabilise
```

### 2.3 Power-Up Sequence (Every Test Session)

```
STEP 1:  Set power supplies to correct voltages (do NOT turn on yet)
STEP 2:  Connect all CAN/LIN cables
STEP 3:  Open CANoe configuration on Host PC
STEP 4:  Open dSPACE ControlDesk on Host PC
STEP 5:  Turn ON KL30 supply (12.5V)
          → Observe current meter: baseline < 100 mA (ECU fully off)
STEP 6:  Turn ON KL15 via relay
          → Current rises to ~300–800 mA during ECU boot
          → Wait 2 seconds for ECU initialisation
STEP 7:  Verify CAN bus activity in CANoe Trace window
          → Should see periodic messages within 1 s of KL15
STEP 8:  Verify SCALEXIO is running (green LED on front panel)
STEP 9:  Ready for testing
```

---

## Step 3 — CAN Bus Wiring and Termination

### 3.1 CAN Wiring Rules

```
ECU CAN connector pin (CAN_H) ──────────────────── Vector VN1640A CH1 CAN_H
ECU CAN connector pin (CAN_L) ──────────────────── Vector VN1640A CH1 CAN_L
ECU CAN connector pin (CAN_GND) ─────────────────── bench GND bus bar

Wire type: Twisted pair, 22 AWG, max length 4 m on bench
Colour convention: CAN_H = Orange, CAN_L = Green (ISO 11898)
```

### 3.2 Termination

Each CAN bus segment needs **120 Ω at each end**:

| Location | Termination Method |
|---|---|
| Vector VN1640A | Enable via CANoe → Hardware → Channel → 120 Ω software termination |
| ECU end | Check ECU schematic — most production ECUs have internal 120 Ω |
| SCALEXIO DS6340 | Enable via dSPACE Experiment Manager bus configuration |

**Verification — Measure with Multimeter (KL30 OFF):**
- Multimeter on ECU CAN H–L pins: should read **60 Ω** (two parallel 120 Ω)
- If 120 Ω → only one terminator → add second terminator
- If 40 Ω → three terminators active → disable one

### 3.3 Multi-Bus Setup (Chassis + Camera CAN-FD)

```
Channel 1 (VN1640A):  Chassis HS-CAN   500 kbps   — ECU <-> ABS, EPS, BCM sim
Channel 2 (VN1640A):  OBD-II ISO-TP    500 kbps   — Diagnostics
Channel 3 (VN1640A):  Comfort CAN      125 kbps   — Cluster, HMI sim
Channel 4 (VN1640A):  Camera CAN-FD    2 Mbps     — Camera/Radar sensor data
```

---

## Step 4 — LIN Bus Wiring

### 4.1 LIN Wiring

```
ECU LIN master pin ──────────── Vector VN1611 LIN pin
ECU LIN GND (KL31)────────────  bench GND
ECU KL15 → LIN pullup ──────── 1 kΩ resistor to KL15 line

LIN wire type: Single wire, 22 AWG
LIN bus length: Max 40 m (bench: keep under 1 m)
LIN baud rate: 19,200 bps (automotive standard)
```

### 4.2 LIN Slave Simulation (Parking Sensors)

- In **CANoe**, add a LIN network node with the LDB (LIN database) file for your parking sensor.
- Assign the VN1611 to this LIN channel in Hardware Configuration.
- The CAPL simulation node will respond to master schedule frames automatically once measurement starts.

---

## Step 5 — dSPACE SCALEXIO Setup

### 5.1 First-Time SCALEXIO Configuration

```
STEP 1:  Connect SCALEXIO Processing Unit to Host PC via Gigabit Ethernet
          (use dedicated switch or direct cable)

STEP 2:  Open dSPACE Experiment Manager
          → Detect SCALEXIO on network
          → Assign static IP: 192.168.1.10 (SCALEXIO)
                                192.168.1.5  (Host PC NIC)

STEP 3:  Open MATLAB/Simulink + dSPACE RTI
          → Open vehicle plant model: VehicleModel_ADAS.slx
          → Target selection: SCALEXIO
          → Build and Download: Ctrl+B

STEP 4:  Open ControlDesk
          → New Experiment → Load .sdf model description file
          → Drag variables to instrument panel:
             - VehicleSpeed_kph → Numeric Display
             - TargetDistance_m → Gauge
             - LateralOffset_m  → Gauge
             - LongAccel_g      → Numeric Display

STEP 5:  Start Real-Time Application in ControlDesk
          → Click "Start Experiment" (green play button)
          → SCALEXIO LEDs: PWR (green), RUN (green), ERR (off) = OK

STEP 6:  Verify variable I/O
          → In ControlDesk, set VehicleSpeed_kph = 50
          → Check analog output on oscilloscope at DS2655 pin:
             should output 2.5V for 50 km/h (scaled: 0–5V = 0–100 km/h)
```

### 5.2 SCALEXIO I/O Channel Mapping (Example)

| Channel | Board | Signal | ECU Pin | Range | Scaling |
|---|---|---|---|---|---|
| AO_0 | DS2655 | Vehicle Speed | Speed sensor + | 0–5V | 0V=0 / 5V=250 km/h |
| AO_1 | DS2655 | Brake Pressure | BrkPress sensor | 0–5V | 0.5V=0 / 4.5V=200 bar |
| AO_2 | DS2655 | Steering Angle | EPS sensor | 0–5V | 2.5V=0° / 5V=540° |
| DIO_0 | DS2655 | Ignition KL15 | KL15 relay | 0/12V | digital |
| CAN_0 | DS6340 | Chassis CAN | ECU CAN H/L | 500 kbps | — |
| LIN_0 | DS6230 | Park Sensor LIN | ECU LIN pin | 19.2 kbps | — |

---

## Step 6 — Vector Hardware Setup

### 6.1 Install Vector Driver and Assign Channels

```
STEP 1:  Install Vector Driver Package (from Vector download portal)
         → VectorDriverSetup_v20.30.xx.exe → Run as Administrator

STEP 2:  Open Vector Hardware Config (Start → Vector Hardware Config)
         → Connected devices shown: VN1640A, VN1611
         → Assign application name "CANoe" to all channels

STEP 3:  Channel Assignment:
         VN1640A CH1 → Application: CANoe, Channel 1, Net: Chassis_CAN
         VN1640A CH2 → Application: CANoe, Channel 2, Net: OBD
         VN1640A CH3 → Application: CANoe, Channel 3, Net: Comfort
         VN1640A CH4 → Application: CANoe, Channel 4, Net: CAN_FD_Camera
         VN1611  CH1 → Application: CANoe, Channel 5, Net: LIN_Park

STEP 4:  Enable Termination:
         Right-click each channel → Termination → 120 Ω (for CAN channels)
         LIN channel: Termination = NOT applicable (LIN is single-wire)

STEP 5:  Test connection:
         Click "Test" button in Hardware Config
         → All channels should show green "OK"
```

---

## Step 7 — CANoe Project Setup

### 7.1 Create New Configuration

```
STEP 1:  Open CANoe 17
STEP 2:  File → New Configuration
STEP 3:  Template selection → "CAN/CANFD + LIN" → OK
STEP 4:  Hardware configuration dialog:
          → Channel 1: CAN, 500 kbps, VN1640A CH1
          → Channel 2: CAN, 500 kbps, VN1640A CH2
          → Channel 4: CAN-FD, 2 Mbps / 500 kbps arbitration, VN1640A CH4
          → Channel 5: LIN, 19.2 kbps, VN1611 CH1
STEP 5:  Save configuration: File → Save As → ADAS_HIL.cfg
```

### 7.2 Add Simulation Setup Nodes

```
STEP 1:  Open "Simulation Setup" window (Ctrl+Shift+S)
STEP 2:  Right-click in "Nodes" area → Add Node
STEP 3:  Add the following nodes:

  Node Name              | Script File              | Bus
  -----------------------|--------------------------|----------
  VehicleDynamicsSim     | vehicle_dynamics_sim.capl| Chassis CAN
  SensorSim              | sensor_sim.capl          | CAN-FD
  DriverInputSim         | driver_input_sim.capl    | Chassis CAN
  ClusterSim             | cluster_sim.capl         | Comfort CAN
  ParkingSensorSim       | parking_sensor_sim.capl  | LIN
  TestController         | test_controller.capl     | All buses

STEP 4:  For each node:
          → Right-click node → Properties → Assign script file
          → Set bus channel correctly
```

### 7.3 Global Environment Variables

```
STEP 1:  Environment → Variables manager
STEP 2:  Add the following variables (all namespace: ADAS):

  Name                  | Type  | Init  | Min    | Max
  ----------------------|-------|-------|--------|-------
  VehicleSpeed_kph      | float | 0.0   | 0      | 250
  TargetDistance_m      | float | 100.0 | 0      | 250
  TargetRelVelocity_kph | float | 0.0   | -100   | 100
  LaneOffset_m          | float | 0.0   | -2.0   | 2.0
  LaneMarkingQuality    | int   | 3     | 0      | 3
  BrakePedal_Pct        | float | 0.0   | 0      | 100
  AccelPedal_Pct        | float | 0.0   | 0      | 100
  SteeringAngle_deg     | float | 0.0   | -540   | 540
  GearPosition          | int   | 4     | 1      | 8
  IgnitionState         | int   | 0     | 0      | 1
  HillGrade_Pct         | float | 0.0   | -15    | 15
  TurnSignalLeft        | int   | 0     | 0      | 1
  TurnSignalRight       | int   | 0     | 0      | 1

STEP 3:  Save configuration
```

---

## Step 8 — Load DBC / ARXML Databases

### 8.1 Assign Databases to Channels

```
STEP 1:  In Simulation Setup window:
          → Right-click on Channel 1 → Assign Database
          → Browse to: Chassis_CAN.dbc → Open
          → Repeat for all channels:
             Channel 1: Chassis_CAN.dbc
             Channel 2: Diagnostics.dbc
             Channel 3: Comfort_CAN.dbc
             Channel 4: Camera_Radar.arxml
             Channel 5: ParkingSensor.ldb    (LIN database)

STEP 2:  Verify database load:
          → Open Trace window (Ctrl+T) → Start measurement
          → Decoded message names should appear (not raw hex)
          → If you see only hex IDs → database not assigned to correct channel
```

### 8.2 DBC Database Content Requirements

Your DBC files must contain:

| Feature | Required Messages in DBC |
|---|---|
| ACC | VehicleSpeed, RadarObj, AccSwitch, ACC_Status, ACC_Control, ACC_HMI |
| LKA/LDW | CameraLane, SteeringAngle, TurnSignal, LKA_Status, LKA_Output, LDW_HMI |
| BSD | RearRadarL, RearRadarR, BSD_Status, BSD_HMI, BSD_Audio |
| Parking | ParkButton, Park_Status, Park_HMI, Park_BrkCtrl |
| HHA | LongitudinalAccel, InclineSensor, BrakeFluidPressure, HHA_Status, HHA_Output |

---

## Step 9 — Add Simulation Nodes (CAPL)

### 9.1 Vehicle Dynamics Simulation Node

Save this file as `vehicle_dynamics_sim.capl`:

```capl
/*
 * vehicle_dynamics_sim.capl
 * Sends periodic vehicle dynamics messages to the ECU.
 * Values driven by CANoe environment variables.
 */

variables
{
  message VehicleSpeed  msg_VehSpd;
  message WheelSpeeds   msg_WhlSpd;
  message BrakePedal    msg_Brk;
  message AccelPedal    msg_Accel;
  message GearPosition  msg_Gear;
  message SteeringAngle msg_Steer;
  message TurnSignal    msg_Turn;
  message YawRate       msg_Yaw;

  msTimer tCyclicSend;
  const int CYCLE_MS = 10;  // 10 ms = 100 Hz
}

on start
{
  setTimer(tCyclicSend, CYCLE_MS);
}

on timer tCyclicSend
{
  float spd = @sysvar::ADAS::VehicleSpeed_kph;

  // VehicleSpeed message (10ms cycle)
  msg_VehSpd.VehSpd_kph = spd;
  output(msg_VehSpd);

  // Wheel speeds (derived from vehicle speed: assume no slip)
  float wheelRPM = (spd * 1000.0 / 3600.0) / (0.315 * 3.14159 * 2) * 60.0;
  msg_WhlSpd.WhlSpd_FL = wheelRPM;
  msg_WhlSpd.WhlSpd_FR = wheelRPM;
  msg_WhlSpd.WhlSpd_RL = wheelRPM;
  msg_WhlSpd.WhlSpd_RR = wheelRPM;
  output(msg_WhlSpd);

  // Brake and accel pedal
  msg_Brk.BrkPdl_Pct    = @sysvar::ADAS::BrakePedal_Pct;
  msg_Accel.AccPdl_Pct  = @sysvar::ADAS::AccelPedal_Pct;
  output(msg_Brk);
  output(msg_Accel);

  // Gear, steering, turn signal
  msg_Gear.GearPos       = @sysvar::ADAS::GearPosition;
  msg_Steer.StrgAng_deg  = @sysvar::ADAS::SteeringAngle_deg;
  msg_Turn.TurnSig_L     = @sysvar::ADAS::TurnSignalLeft;
  msg_Turn.TurnSig_R     = @sysvar::ADAS::TurnSignalRight;
  output(msg_Gear);
  output(msg_Steer);
  output(msg_Turn);

  setTimer(tCyclicSend, CYCLE_MS);
}
```

### 9.2 Sensor Simulation Node (Radar + Camera)

Save as `sensor_sim.capl`:

```capl
/*
 * sensor_sim.capl
 * Simulates radar and camera sensor signals for ADAS ECU.
 */

variables
{
  message RadarObj    msg_Radar;
  message CameraLane  msg_Camera;
  message RearRadarL  msg_RearL;
  message RearRadarR  msg_RearR;

  msTimer tSensorCycle;
  const int SENSOR_CYCLE_MS = 20;  // 50 Hz
}

on start
{
  setTimer(tSensorCycle, SENSOR_CYCLE_MS);
}

on timer tSensorCycle
{
  // Front radar (ACC / AEB)
  msg_Radar.RadarObj_Dist   = @sysvar::ADAS::TargetDistance_m;
  msg_Radar.RadarObj_RelVel = @sysvar::ADAS::TargetRelVelocity_kph;
  output(msg_Radar);

  // Camera lane keeping
  float offset = @sysvar::ADAS::LaneOffset_m;
  int   quality = @sysvar::ADAS::LaneMarkingQuality;
  msg_Camera.LatOffset_L_m  = 0.0 - offset;
  msg_Camera.LatOffset_R_m  = 0.0 + offset;
  msg_Camera.LnMrkng_QL_L   = quality;
  msg_Camera.LnMrkng_QL_R   = quality;
  msg_Camera.LnCurvature    = 0.0;  // Straight road
  output(msg_Camera);

  // Rear radar (BSD)
  msg_RearL.BSD_ObjDet_L    = 0;  // Default: no object
  msg_RearR.BSD_ObjDet_R    = 0;
  output(msg_RearL);
  output(msg_RearR);

  setTimer(tSensorCycle, SENSOR_CYCLE_MS);
}
```

---

## Step 10 — Configure vTestStudio Project

### 10.1 Create New vTestStudio Project

```
STEP 1:  Open vTestStudio 5.x
STEP 2:  File → New Project → Name: "ADAS_HIL_Tests"
STEP 3:  Tools → Options → CANoe → Browse to ADAS_HIL.cfg
          (Links vTestStudio to your CANoe configuration)
STEP 4:  File → New Test Unit → Select "CAPL Test Unit"
          → Name: "ACC_Tests"
          → Link CAPL file: acc_tests.can
STEP 5:  Repeat Step 4 for:
          LKA_LDW_Tests   → lka_ldw_tests.can
          BSD_Tests        → bsd_tests.can
          Parking_Tests    → parking_tests.can
          HHA_Tests        → hha_tests.can
```

### 10.2 Add Test Cases to Each Test Unit

```
STEP 1:  In vTestStudio project tree:
          → Expand ACC_Tests → Right-click → Add Test Group
          → Name: "ACC_Functional"

STEP 2:  Right-click ACC_Functional → Add Test Case
          → Set CAPL function: tc_ACC_ActivationAtSetSpeed
          → Title: "TC-ACC-001 — ACC activation at valid set speed"

STEP 3:  Repeat for all test cases:
          Group: ACC_Functional   → tc_ACC_ActivationAtSetSpeed
                                  → tc_ACC_DecelerationOnTargetClose
                                  → tc_ACC_CancelOnBrakePedal
          Group: ACC_Safety       → tc_ACC_EmergencyBrakeOnLowTTC
          Group: LKA_Functional   → tc_LKA_SteeringTorqueOnRightDrift
                                  → tc_LKA_SuppressedOnTurnSignal
          Group: LDW_Functional   → tc_LDW_AudioWarnOnDeparture
          Group: BSD_Functional   → tc_BSD_LeftObjectWarning
                                  → tc_BSD_ChimeOnSignalWithObject
          Group: PARK_Functional  → tc_Park_ActivationInReverse
                                  → tc_Park_ToneZoneScaling
                                  → tc_Park_AutoBrakeAtCriticalDistance
          Group: HHA_Functional   → tc_HHA_ActivateOnUphillStop
                                  → tc_HHA_HoldDurationMeasurement
```

### 10.3 Set Execution Settings

```
STEP 1:  Right-click each Test Unit → Properties:
          Stop on first failure : OFF
          Repeat on failure     : 0
          Pre-execution delay   : 2000 ms

STEP 2:  Report Settings:
          Format: HTML + JUnit XML
          Include: Screenshots on failure = ON (if using panels)
          Output path: C:\HIL\Reports\

STEP 3:  Click Apply → OK
```

---

## Step 11 — ECU Power-On Verification

### 11.1 Pre-Test Checklist (Run Before Every Test Session)

```
[ ] Bench GND bus bar connected to all equipment
[ ] KL30 supply set to 12.5V, current limit 15A, output OFF
[ ] KL15 relay control connected to Arduino or relay box
[ ] All CAN cables seated firmly (wiggle test)
[ ] CAN termination verified: 60Ω per bus (measured with multimeter)
[ ] Vector Hardware Config shows all channels: green OK
[ ] dSPACE SCALEXIO front panel: PWR green, ERR off
[ ] CANoe configuration loaded, databases assigned
[ ] vTestStudio project open and linked to CANoe config
```

### 11.2 Power-On and Boot Verification

```
STEP 1:  Turn ON KL30 (12.5V supply)
STEP 2:  Start CANoe measurement (F9)
STEP 3:  Turn ON KL15 relay
STEP 4:  Watch CANoe Trace window:
          → First message within 500 ms → PASS
          → No message within 2 s      → FAIL (check KL15, CAN termination)
STEP 5:  Check for DTC CAN messages:
          → Service 0x19 response should show 0 active DTCs on fresh boot
STEP 6:  Verify cyclic messages are present at correct intervals:
          VehicleSpeed:  10 ms ±2 ms
          ACC_Status:    20 ms ±3 ms
          LKA_Status:    20 ms ±3 ms
```

### 11.3 CAN Message Timing Verification (CANoe Statistics)

```
STEP 1:  Start measurement
STEP 2:  Open Statistics window: Analysis → Statistics
STEP 3:  Let run for 10 seconds
STEP 4:  Verify:
          Message: VehicleSpeed, Min/Max cycle time within spec
          Message: ACC_Status,   Min/Max cycle time within spec
STEP 5:  If cycle time deviates > 10%:
          → ECU may be overloaded or mis-configured
          → Check DBC scaling
```

---

## Step 12 — CAN Bus Health Check

### 12.1 Physical Layer Verification with Oscilloscope

```
STEP 1:  Probe CAN_H (orange wire) on oscilloscope CH1
         Probe CAN_L (green wire) on oscilloscope CH2
STEP 2:  Set time base: 1 µs/div
         Voltage scale: 2V/div
STEP 3:  Start CANoe measurement, run vehicle dynamics simulation
STEP 4:  Expected waveform:
          Recessive: CAN_H ≈ 2.5V, CAN_L ≈ 2.5V
          Dominant:  CAN_H ≈ 3.5V, CAN_L ≈ 1.5V
          Differential: CAN_H - CAN_L ≈ 2.0V in dominant bit
STEP 5:  Look for:
          [ ] Clean edges (rise/fall time < 200 ns at 500 kbps)
          [ ] No reflections or ringing on edges
          [ ] No DC offset between CAN_H and CAN_L at recessive
STEP 6:  If ringing observed: check termination resistance
         If asymmetric voltage: check for damaged transceiver
```

### 12.2 CANoe Error Frame Check

```
STEP 1:  Measurement running
STEP 2:  Open CANoe "Error Frames" window: Analysis → Error Frames
STEP 3:  Run for 60 seconds
STEP 4:  Accept threshold: 0 error frames per minute on nominal bench
         Any error frames → investigate wiring, termination, or ECU fault
```

---

## Step 13 — Run First CAPL Test Case

### 13.1 Running Manually from vTestStudio

```
STEP 1:  Ensure CANoe measurement is running (F9)
STEP 2:  In vTestStudio Test Unit ACC_Tests:
          → Right-click tc_ACC_ActivationAtSetSpeed
          → Click "Execute Test Case"
STEP 3:  Watch the test execution in vTestStudio:
          → Green steps = PASS
          → Red steps   = FAIL (click step for details)
STEP 4:  Test duration: ~5 seconds per test case
STEP 5:  After test completes:
          → vTestStudio shows PASSED / FAILED verdict
          → Right-click → View Report → opens HTML report
```

### 13.2 Running Full Test Suite from CANoe

```
STEP 1:  CANoe → Test → Test Modules → right-click suite → Start All
          OR press Ctrl+Shift+R

STEP 2:  All test units execute sequentially:
          ACC_Tests → LKA_LDW_Tests → BSD_Tests → Parking_Tests → HHA_Tests

STEP 3:  Estimated total duration for full suite: ~15–25 minutes

STEP 4:  Progress shown in vTestStudio progress bar
STEP 5:  On completion: Report auto-saved to Reports/ folder
```

---

## Step 14 — Run Python Regression Suite

### 14.1 Environment Setup

```bash
# On HIL Host PC (Windows)
cd C:\HIL\ADAS_Tests

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install pytest pytest-html pywin32 requests

# Verify CANoe COM is accessible
python -c "import win32com.client; app = win32com.client.Dispatch('CANoe.Application'); print('CANoe COM OK')"
```

### 14.2 Run Individual Feature

```bash
# Run ACC tests only
pytest acc_regression.py -v --html=reports/acc_report.html --self-contained-html

# Run LKA/LDW tests
pytest lka_ldw_regression.py -v --html=reports/lka_report.html --self-contained-html

# Run all features
pytest acc_regression.py lka_ldw_regression.py bsd_regression.py \
       parking_regression.py hha_regression.py \
       -v --html=reports/full_report.html --self-contained-html
```

### 14.3 Run Full Release Gate

```bash
# Single-command release gate with thresholds
python run_hil_suite.py \
    --feature ALL \
    --build-id BUILD_2026_04_23 \
    --min-pass-rate 95.0 \
    --output-dir reports

# Output:
# ============================================================
#   ADAS HIL Gate: PASSED
#   Build:         BUILD_2026_04_23
#   Reports:       reports/BUILD_2026_04_23/
# ============================================================
```

---

## Step 15 — Fault Injection Procedure

### 15.1 CAN Bus Open-Circuit Fault

```
Purpose: Verify ECU stores DTC on bus disconnection

STEP 1:  Start CANoe measurement (F9)
STEP 2:  Verify ECU in normal operating state (no DTCs)
STEP 3:  Open relay on CAN_H wire (break ECU CAN connection)
         → Relay box: switch relay K1 OFF (controls CAN_H line)
STEP 4:  Wait 500 ms
STEP 5:  Check CANoe Trace:
         → ECU should stop sending messages within 1 s
         → Error frames may appear briefly
STEP 6:  Close relay (restore CAN_H)
STEP 7:  Wait 2 s for ECU recovery
STEP 8:  Send UDS ReadDTC request (Service 0x19 0x02 0xFF):
         → Expected DTC: U0001 (CAN Bus Off)
         → Verify DTC is CONFIRMED (status byte = 0x29)
STEP 9:  Send UDS ClearDTC (Service 0x14 0xFF 0xFF 0xFF)
STEP 10: Verify no active DTCs remain
```

### 15.2 Radar Signal Out-of-Range Fault

```
STEP 1:  In sensor_sim.capl, inject physically impossible distance:
           msg_Radar.RadarObj_Dist = 999.9;  // > physical max 200m
           output(msg_Radar);

STEP 2:  Wait 1 s
STEP 3:  Verify ACC_Sts = FAULT (0xFF) or STANDBY (0x01)
STEP 4:  Verify DTC related to radar plausibility is set
STEP 5:  Restore: msg_Radar.RadarObj_Dist = 80.0; output(msg_Radar);
STEP 6:  Verify ECU recovers and ACC returns to STANDBY
```

### 15.3 LKA Steering Sensor Fault

```
STEP 1:  Force steering angle to maximum + jitter (sensor fault pattern):
           In CAPL: msg_Steer.StrgAng_deg = 999.0; output(msg_Steer);

STEP 2:  Wait 300 ms
STEP 3:  LKA_Sts should change to DISABLED or FAULT
STEP 4:  Warning lamp on cluster should illuminate (check ClusterSim node)
STEP 5:  DTC for EPS/Steering angle fault should be logged

STEP 6:  Restore: msg_Steer.StrgAng_deg = 0.0; output(msg_Steer);
STEP 7:  Cycle KL15 OFF → ON (ECU reset)
STEP 8:  Verify LKA recovers to READY state on clean KL15
```

---

## Step 16 — Measurement and Logging

### 16.1 Configure MF4 Logging in CANoe

```
STEP 1:  Logging → New Logging Block
STEP 2:  Settings:
          Format: MF4 (Vector proprietary, best performance)
          File name: ADAS_HIL_{BUILDID}_{DATETIME}.mf4
          Split file every: 100 MB
STEP 3:  Trigger: Start on Measurement Start
         Stop:    Stop on Measurement Stop
STEP 4:  Add filter (reduces file size):
          Include only message IDs relevant to test:
          0x1A0–0x1FF  (ACC messages)
          0x280–0x2FF  (LKA/LDW messages)
          0x310–0x35F  (BSD messages)
          0x350–0x380  (Parking messages)
          0x370–0x390  (HHA messages)
STEP 5:  Click OK → logging block active (orange icon = active)
```

### 16.2 Key Signals to Capture

```
Signal                         | Why Log It
-------------------------------|---------------------------------------------
VehicleSpeed_kph               | Baseline context for all tests
RadarObj_Dist, _RelVel         | Stimulus verification for ACC
ACC_Sts, ACC_BrkReq_Pct        | ECU response timing
LKA_Sts, LKA_TrqOvrd_Nm       | Torque onset timing
LatOffset_L_m, LatOffset_R_m   | Drift stimulus confirmation
BSD_Warn_L, BSD_Warn_R         | BSD response latency
Park_Display_Zone              | Zone update rate
HHA_Sts, HHA_HoldDuration_ms   | HHA timing compliance
All DTC messages (0x7DF resp)  | Fault coverage evidence
```

### 16.3 Open and Analyse MF4 Log in CANoe

```
STEP 1:  File → Open → select .mf4 file
STEP 2:  CANoe loads log in offline/playback mode
STEP 3:  Open Graphics window: Analysis → Graphics
STEP 4:  Drag signals from Signal Browser to Graphics window:
          → VehicleSpeed_kph vs Time
          → ACC_Sts vs Time
          → ACC_BrkReq_Pct vs Time
STEP 5:  Use cursor to measure:
          → T1: timestamp when TargetDistance reaches 15m
          → T2: timestamp when ACC_BrkReq_Pct > 0
          → Latency: T2 - T1
          → Compare to pass criteria: ≤ 400 ms
```

---

## Step 17 — Report Generation

### 17.1 vTestStudio HTML Report

The report is automatically generated after each test run.

```
Report location: C:\HIL\Reports\ADAS_HIL_<date>.html

Contents:
  - Configuration summary (build ID, date, CANoe version)
  - Test statistics: total, passed, failed, skipped
  - Per-test-case verdict with execution time
  - Signal waveform screenshots (if enabled)
  - CAPL testStep() log entries for each case
```

### 17.2 JUnit XML for CI Systems

```
STEP 1:  In vTestStudio → Test Unit Properties → Report → JUnit XML = ON
STEP 2:  Output: C:\HIL\Reports\junit_ACC_Tests.xml
STEP 3:  Feed to Jenkins or GitHub Actions:
          publish unit test results from junit_*.xml
```

### 17.3 Python pytest HTML Report

```bash
pytest acc_regression.py \
    -v \
    --junitxml=reports/ACC_junit.xml \
    --html=reports/ACC_report.html \
    --self-contained-html

# --self-contained-html embeds CSS/JS inside HTML
# → single portable file, no external dependencies
```

---

## Step 18 — CI/CD Pipeline Setup

### 18.1 GitHub Actions Workflow for HIL

```yaml
# .github/workflows/hil_regression.yml
name: ADAS HIL Nightly Regression

on:
  schedule:
    - cron: '0 22 * * 1-5'   # Every weekday at 22:00
  workflow_dispatch:
    inputs:
      build_id:
        default: 'nightly'

jobs:
  hil_regression:
    runs-on: [self-hosted, hil-bench]    # Self-hosted runner on HIL PC
    timeout-minutes: 120

    steps:
      - name: Checkout Test Scripts
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Install Python dependencies
        run: pip install pytest pytest-html pywin32 requests

      - name: Start CANoe Measurement
        run: python scripts/start_canoe.py --config ADAS_HIL.cfg

      - name: Power On ECU
        run: python scripts/power_control.py --action on

      - name: Run HIL Gate
        run: |
          python run_hil_suite.py \
            --feature ALL \
            --build-id ${{ github.event.inputs.build_id || 'nightly' }} \
            --min-pass-rate 95.0

      - name: Power Off ECU
        if: always()
        run: python scripts/power_control.py --action off

      - name: Stop CANoe
        if: always()
        run: python scripts/stop_canoe.py

      - name: Upload Reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: hil-reports-${{ github.run_number }}
          path: reports/
          retention-days: 30
```

### 18.2 Jenkins Pipeline (Alternative)

```groovy
// Jenkinsfile
pipeline {
    agent { label 'hil-bench-windows' }

    triggers {
        cron('H 22 * * 1-5')  // Weeknights at 22:00
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Install Deps') {
            steps {
                bat 'pip install pytest pytest-html pywin32 requests'
            }
        }

        stage('Run HIL Suite') {
            steps {
                bat """
                    python run_hil_suite.py ^
                        --feature ALL ^
                        --build-id %BUILD_NUMBER% ^
                        --min-pass-rate 95.0
                """
            }
        }
    }

    post {
        always {
            junit 'reports/**/*_junit.xml'
            publishHTML([
                target: [
                    allowMissing: false,
                    reportDir:    'reports',
                    reportFiles:  '**/full_report.html',
                    reportName:   'HIL Test Report'
                ]
            ])
        }
        failure {
            emailext subject: "HIL Regression FAILED — Build ${env.BUILD_NUMBER}",
                     body:    "See: ${env.BUILD_URL}",
                     to:      'adas-team@yourcompany.com'
        }
    }
}
```

---

## Troubleshooting Reference

| # | Problem | Symptom | Root Cause | Fix |
|---|---------|---------|------------|-----|
| 1 | No CAN messages in Trace | Empty trace after KL15 | CAN termination missing | Measure CAN_H-L resistance: should be 60 Ω |
| 2 | ECU not booting | Current stays < 50 mA at KL15 | KL15 relay not switching | Check relay control signal voltage (5V), check relay SSR |
| 3 | Decoded signal shows wrong value | Speed = 9999 km/h | DBC byte order wrong (Intel vs Motorola) | Compare DBC bit positions against ECU datasheet |
| 4 | vTestStudio can't connect to CANoe | "CANoe not running" error | CANoe started after vTestStudio | Start CANoe first, then launch vTestStudio |
| 5 | SCALEXIO ERR LED on | Red ERR LED front panel | Model crashed or timing overrun | Reduce model complexity; check cycle time setting |
| 6 | Python COM DispatchException | win32com error on CANoe.Application | 32-bit vs 64-bit mismatch | Use 32-bit Python if CANoe is 32-bit |
| 7 | Error frames on CAN bus | Error counter rising in CANoe | Incorrect baud rate or damaged transceiver | Probe physical layer; verify baud rate in HW Config |
| 8 | LKA never activates in test | LKA_Sts = READY but never INTERVENING | Lane marking quality signal = 0 | Set LnMrkng_QL_L/R = 3 in sensor_sim.capl |
| 9 | ACC brake request always 0 | ACC active but no braking output | Radar distance signal not sent | Verify RadarObj message is output by SensorSim node |
| 10 | HHA fires on flat road | HHA_Sts = HOLDING at 0% slope | Incline sensor wrong default | Check InclineSensor default value in DBC — set Slope_Pct = 0 |
| 11 | DTC never set after fault injection | 0 DTCs after open-circuit test | DTC debounce time > fault duration | Extend fault injection duration to > 500 ms |
| 12 | Test report not generated | No HTML/XML after run | Disk full or path not writable | Free disk space; check write permissions on reports/ |
| 13 | Oscilloscope shows ringing | CAN waveform has high-frequency oscillation | Mismatched termination or stub cable too long | Keep stubs < 0.3 m; verify single-point termination |
| 14 | SCALEXIO not found on network | Experiment Manager timeout | IP address conflict or wrong NIC | Set static IP on HIL NIC; disable other NICs |

---

## Appendix — Quick Reference

### A. Signal Encoding Reference

```
ACC_Sts:   0x00=OFF     0x01=STANDBY  0x02=ACTIVE   0x03=OVERRIDE  0xFF=FAULT
LKA_Sts:   0x00=OFF     0x01=READY    0x02=ACTIVE   0x03=INTERVENING
BSD_LED:   0x00=OFF     0x01=SOLID    0x02=FLASHING
Park_Sts:  0x00=OFF     0x01=ACTIVE   0x02=PAUSED   0x03=FAULT
HHA_Sts:   0x00=OFF     0x01=READY    0x02=HOLDING  0x03=RELEASING
GearPos:   0x01=P  0x02=R  0x03=N  0x04=D  0x05-0x08=M1-M4
```

### B. Useful CANoe Keyboard Shortcuts

| Action | Keys |
|---|---|
| Start Measurement | F9 |
| Stop Measurement | F10 |
| Open Trace Window | Ctrl + T |
| Open Data Window | Ctrl + D |
| Open Graphics Window | Ctrl + G |
| Start vTestStudio Suite | Ctrl + Shift + R |
| Open Statistics | Alt + S |
| Open Logging Config | Ctrl + L |

### C. Bench Quick Power Sequence

```
ON  order:  KL30 → wait 100ms → KL15 → wait 2s → start test
OFF order:  KL15 OFF → wait 500ms → KL30 OFF → stop measurement
```

### D. Pass Criteria Summary

| Feature | Metric | Limit |
|---|---|---|
| ACC | Activation latency | ≤ 1000 ms |
| ACC | Emergency brake latency | ≤ 400 ms |
| LKA | Torque response time | ≤ 800 ms |
| LDW | Warning onset | ≤ 500 ms |
| BSD | Detection to LED latency | ≤ 300 ms |
| Parking | Auto-brake at ≤ 20 cm | ≤ 200 ms |
| HHA | Hold activation | ≤ 300 ms |
| Overall suite | Pass rate | ≥ 95% |
| Safety (P0) | Pass rate | 100% |

---

*End of Document — HIL Bench Setup & Testing Step-by-Step Guide v1.0*
