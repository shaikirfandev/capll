# HIL Bench Testing Guide for ADAS ECU
## Using CANoe, vTestStudio, CAPL, and Python Scripts

**Document Version:** 1.0  
**Date:** 23 April 2026  
**Scope:** ACC · LKA · LDW · BSD · Parking Assistance · Hill Hold Assist  
**Tools:** Vector CANoe 17+ · vTestStudio 5+ · CAPL · Python 3.10+

---

## Table of Contents

1. [HIL Bench Architecture Overview](#1-hil-bench-architecture-overview)
2. [Hardware Setup and Wiring](#2-hardware-setup-and-wiring)
3. [CANoe Project Setup](#3-canoe-project-setup)
4. [CAN Signal Reference per Feature](#4-can-signal-reference-per-feature)
5. [vTestStudio Test Module Setup](#5-vteststudio-test-module-setup)
6. [CAPL Scripts — Feature by Feature](#6-capl-scripts--feature-by-feature)
7. [Python Scripts — Automation Layer](#7-python-scripts--automation-layer)
8. [Test Case Catalogue per Feature](#8-test-case-catalogue-per-feature)
9. [Fault Injection Procedures](#9-fault-injection-procedures)
10. [Measurement and Logging Strategy](#10-measurement-and-logging-strategy)
11. [Pass/Fail Criteria](#11-passfail-criteria)
12. [CI Integration](#12-ci-integration)
13. [Troubleshooting HIL Issues](#13-troubleshooting-hil-issues)

---

## 1. HIL Bench Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HIL TEST BENCH                               │
│                                                                     │
│  ┌──────────────┐    CAN/CAN-FD     ┌────────────────────────────┐ │
│  │  ADAS ECU    │◄──────────────────►│  Vector VN1640 / VN7572   │ │
│  │  (DUT)       │                   │  CAN Interface Hardware    │ │
│  │              │    LIN Bus        │                            │ │
│  │  - ACC ECU   │◄──────────────────►│  LIN Interface             │ │
│  │  - LKA/LDW   │                   └──────────┬─────────────────┘ │
│  │  - BSD ECU   │                              │ USB/PCIe           │
│  │  - Parking   │                   ┌──────────▼─────────────────┐ │
│  │  - HHA ECU   │◄──────────────────►│  HOST PC                   │ │
│  └──────┬───────┘   Power Supply    │  CANoe 17 + vTestStudio    │ │
│         │           (12V/Ignition)  │  CAPL + Python Scripts     │ │
│         │                           └──────────────────────────── ┘ │
│  ┌──────▼───────┐                                                   │
│  │  I/O Board   │   Analog/Digital signals                         │
│  │  (dSPACE /   │   - Vehicle speed sim                            │
│  │   NI CompactRIO│  - Steering angle sim                          │
│  │   / ETAS ES910│  - Wheel speed pulses                           │
│  └──────────────┘   - Brake pressure sim                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Bus Topology typical for ADAS ECU

| Bus | Baud Rate | ECUs on Bus |
|-----|-----------|-------------|
| Chassis CAN (HS) | 500 kbps | ADAS, ABS, EPS, TCU, BCM |
| Comfort CAN | 125 kbps | Cluster, HMI, HVAC |
| CAN-FD (Camera/Radar) | 2 Mbps | Front Radar, Camera ECU |
| LIN | 19.2 kbps | Parking Sensors, Mirror BSD |
| Ethernet (DoIP) | 100 Mbps | Diagnostics |

---

## 2. Hardware Setup and Wiring

### 2.1 Required Equipment

| Item | Part / Model | Purpose |
|------|-------------|---------|
| CAN Interface | Vector VN1640A or VN7572 | CAN/CAN-FD bus access |
| Power Supply | EA-PS 2384-05 B (0–32V, 20A) | Simulate 12V/ignition |
| ECU Harness Adapter | Custom break-out box | Probe/inject individual pins |
| I/O Simulation Board | dSPACE MicroLabBox or NI cDAQ | Wheel speed, brake, steering |
| LIN Interface | Vector VN1611 | Parking sensor LIN |
| Oscilloscope | Tektronix TDS3014 | Physical signal verification |
| Relay box | SSR relay card (DIN rail) | Fault injection (open/short) |

### 2.2 Power-Up Sequence

```
Step 1:  Connect ECU ground (GND) to bench GND
Step 2:  Connect CAN High / CAN Low to Vector interface
Step 3:  Apply KL30 (battery +12V) — power supply set to 12.5V
Step 4:  Verify current draw baseline (should be < 200 mA at KL30)
Step 5:  Apply KL15 (ignition on) via relay
Step 6:  Verify current draw rises and stabilises (ECU boot < 500 ms)
Step 7:  Check bus activity on CANoe — expect init messages within 1 s
Step 8:  Apply KL50 (crank signal 200 ms pulse) if engine start needed
```

### 2.3 CAN Bus Termination

- Each CAN bus segment requires **120 Ω** termination at both ends.
- Vector VN hardware provides built-in software-selectable termination.
- Enable via: **CANoe → Hardware → Channel → Termination → 120 Ω**

---

## 3. CANoe Project Setup

### 3.1 Creating New CANoe Project

1. Open **CANoe 17** → File → New Configuration
2. Select **Automotive** template → CAN (500 kbps) + CAN-FD (2 Mbps)
3. Add DBC/ARXML databases:
   - `Chassis_CAN.dbc` — vehicle dynamics signals
   - `ADAS_ECU.dbc` — ADAS feature signals
   - `Camera_RadarCAN.arxml` — sensor data (CAN-FD)
4. Assign databases per channel:
   - Channel 1: `Chassis_CAN.dbc`
   - Channel 2: `ADAS_ECU.dbc`
   - Channel 3: `Camera_RadarCAN.arxml`

### 3.2 Network Nodes Configuration

In **Simulation Setup** window, add the following simulation nodes:

| Node Name | CAPL Script | Purpose |
|-----------|-------------|---------|
| VehicleDynamicsSim | `vehicle_dynamics_sim.capl` | Simulate ABS, ESP, speed, steering |
| SensorSim | `sensor_sim.capl` | Radar targets, camera lane data |
| DriverInputSim | `driver_input_sim.capl` | Accelerator, brake pedal, gear |
| ClusterSim | `cluster_sim.capl` | Receive and ack HMI messages |
| TestController | `test_controller.capl` | Orchestrate test scenarios |

### 3.3 Panel Setup

Create panels for:
- **Speed Control Panel** — slider 0–200 km/h for vehicle speed
- **Target Object Panel** — leading vehicle distance, velocity, TTC
- **Lane Panel** — lane marking quality, lateral offset
- **Feature Status Panel** — display ACC, LKA, BSD, Park status LEDs

### 3.4 Environment Variables

Define these global environment variables in CANoe (Environment → Variables):

```
envVehicleSpeed        : float  [0..250]   km/h
envTargetDistance      : float  [0..200]   m
envTargetVelocity      : float  [0..200]   km/h
envLaneOffset          : float  [-2..2]    m
envSteeringAngle       : float  [-540..540] deg
envBrakeRequest        : float  [0..100]   %
envACCSetSpeed         : float  [30..180]  km/h
envParkingSensorZone   : int    [0..3]     zone ID
envHillGrade           : float  [-15..15]  %
```

---

## 4. CAN Signal Reference per Feature

### 4.1 Adaptive Cruise Control (ACC)

#### Input Signals (sent by simulation nodes to ECU)

| Message Name | Signal Name | Byte | Bit | Length | Unit | Range | Description |
|---|---|---|---|---|---|---|---|
| VehicleSpeed | VehSpd_kph | 0 | 0 | 16 | km/h | 0–250 | Current vehicle speed |
| WheelSpeeds | WhlSpd_FL | 0 | 0 | 16 | rpm | 0–3000 | Front left wheel speed |
| WheelSpeeds | WhlSpd_FR | 2 | 0 | 16 | rpm | 0–3000 | Front right wheel speed |
| AccelPedal | AccPdl_Pct | 0 | 0 | 8 | % | 0–100 | Accelerator pedal position |
| BrakePedal | BrkPdl_Pct | 0 | 0 | 8 | % | 0–100 | Brake pedal position |
| RadarObj | RadarObj_Dist | 0 | 0 | 12 | m | 0–200 | Leading object distance |
| RadarObj | RadarObj_RelVel | 2 | 0 | 12 | km/h | -100–100 | Relative velocity |
| GearPosition | GearPos | 0 | 0 | 4 | - | 0–8 | Gear selector position |
| AccSwitch | ACC_SetSpd | 0 | 0 | 8 | km/h | 30–180 | ACC set speed from driver |
| AccSwitch | ACC_ResumeBtn | 1 | 0 | 1 | bool | 0/1 | Resume button pressed |
| AccSwitch | ACC_CancelBtn | 1 | 1 | 1 | bool | 0/1 | Cancel button pressed |

#### Output Signals (received from ECU, verified by test)

| Message Name | Signal Name | Expected Value on Activate | Description |
|---|---|---|---|
| ACC_Status | ACC_Sts | 0x02 = ACTIVE | ACC system state |
| ACC_Control | ACC_TrqReq_Nm | 0–800 Nm | Torque request to TCU |
| ACC_Control | ACC_BrkReq_Pct | 0–100 % | Brake intervention request |
| ACC_HMI | ACC_SetSpd_Disp | matches driver set speed | Display set speed |
| ACC_HMI | ACC_TTC_s | > 0 | Time to collision |
| ACC_Decel | ACC_EmgcyBrk | 0 or 1 | Emergency brake flag |

### 4.2 Lane Keep Assist (LKA) / Lane Departure Warning (LDW)

#### Input Signals

| Message | Signal | Unit | Description |
|---|---|---|---|
| CameraLane | LnMrkng_QL_L | 0–3 | Left lane marking quality (3=high) |
| CameraLane | LnMrkng_QL_R | 0–3 | Right lane marking quality |
| CameraLane | LatOffset_L_m | m | Lateral offset to left lane |
| CameraLane | LatOffset_R_m | m | Lateral offset to right lane |
| CameraLane | LnCurvature | 1/m | Road curvature |
| VehicleSpeed | VehSpd_kph | km/h | Required > 60 km/h for LKA |
| SteeringAngle | StrgAng_deg | deg | EPS steering angle |
| TurnSignal | TurnSig_L | bool | Left indicator active |
| TurnSignal | TurnSig_R | bool | Right indicator active |
| YawRate | YawRt_dps | deg/s | Vehicle yaw rate |

#### Output Signals

| Message | Signal | Expected | Description |
|---|---|---|---|
| LKA_Status | LKA_Sts | 0x03 = INTERVENING | Active assist state |
| LKA_Output | LKA_TrqOvrd_Nm | ±5 Nm | Steering torque overlay |
| LDW_Status | LDW_Sts | 0x01 = WARNING | Departure warning active |
| LDW_HMI | LDW_AudioWarn | 1 | Audible warning flag |
| LDW_HMI | LDW_HapticWarn | 1 | Haptic (seat) warning flag |

### 4.3 Blind Spot Detection (BSD)

#### Input Signals

| Message | Signal | Unit | Description |
|---|---|---|---|
| RearRadarL | BSD_ObjDet_L | bool | Object in left blind zone |
| RearRadarL | BSD_ObjDist_L_m | m | Distance of left object |
| RearRadarL | BSD_ObjRelVel_L | km/h | Relative velocity left |
| RearRadarR | BSD_ObjDet_R | bool | Object in right blind zone |
| RearRadarR | BSD_ObjDist_R_m | m | Distance of right object |
| TurnSignal | TurnSig_L | bool | Driver activating left signal |
| TurnSignal | TurnSig_R | bool | Driver activating right signal |
| VehicleSpeed | VehSpd_kph | km/h | Must be > 10 km/h |

#### Output Signals

| Message | Signal | Expected | Description |
|---|---|---|---|
| BSD_Status | BSD_Warn_L | 1 | Left BSD warning active |
| BSD_Status | BSD_Warn_R | 1 | Right BSD warning active |
| BSD_HMI | BSD_LED_L | 0x02 = FLASHING | Left mirror LED state |
| BSD_HMI | BSD_LED_R | 0x02 = FLASHING | Right mirror LED state |
| BSD_Audio | BSD_Chime | 1 | Audible chime on indicator+object |

### 4.4 Parking Assistance

#### Input Signals

| Message | Signal | Unit | Description |
|---|---|---|---|
| ParkSensor_LIN | UltraSnd_FL_cm | cm | Front-left sensor distance |
| ParkSensor_LIN | UltraSnd_FR_cm | cm | Front-right sensor distance |
| ParkSensor_LIN | UltraSnd_RL_cm | cm | Rear-left sensor distance |
| ParkSensor_LIN | UltraSnd_RR_cm | cm | Rear-right sensor distance |
| GearPosition | GearPos | - | 0x07 = Reverse for rear PDC |
| VehicleSpeed | VehSpd_kph | km/h | Must be < 10 km/h |
| ParkButton | Park_Btn | bool | Driver enables park assist |

#### Output Signals

| Message | Signal | Expected | Description |
|---|---|---|---|
| Park_Status | Park_Sts | 0x01 = ACTIVE | Park assist state |
| Park_HMI | Park_Tone_Frq | 8 zones 0–7 | Tone frequency zone mapping |
| Park_HMI | Park_Display_Zone | 0–7 | Visual zone on cluster |
| Park_BrkCtrl | Park_BrkReq | 1 | Automatic brake before impact |
| Park_Steer | Park_StrgTrq_Nm | ±8 Nm | Steering guidance torque |

### 4.5 Hill Hold Assist (HHA)

#### Input Signals

| Message | Signal | Unit | Description |
|---|---|---|---|
| LongitudinalAccel | LongAccel_g | g | Longitudinal acceleration |
| InclineSensor | Slope_Pct | % | Road gradient |
| BrakePedal | BrkPdl_Pct | % | Driver brake pedal |
| GearPosition | GearPos | - | D or R for HHA |
| VehicleSpeed | VehSpd_kph | km/h | Must be = 0 for HHA |
| BrakeFluidPressure | BrkPressFl_bar | bar | Brake clamping pressure |

#### Output Signals

| Message | Signal | Expected | Description |
|---|---|---|---|
| HHA_Status | HHA_Sts | 0x02 = HOLDING | Hill hold active state |
| HHA_Output | HHA_BrkPressHold_bar | ≥ input pressure | Maintained brake clamping |
| HHA_Output | HHA_HoldDuration_ms | 0–3000 ms | Hold time post pedal release |
| HHA_HMI | HHA_Indicator | 1 | Cluster indicator on |

---

## 5. vTestStudio Test Module Setup

### 5.1 Project Structure in vTestStudio

```
vTestStudio Project: ADAS_HIL_Suite
│
├── Test Environment
│   ├── CANoe.cfg              ← CANoe configuration reference
│   ├── DBC_Files/
│   └── SystemVariables.vsysvar
│
├── Test Modules
│   ├── 01_ACC_TestModule.vtestunit
│   ├── 02_LKA_LDW_TestModule.vtestunit
│   ├── 03_BSD_TestModule.vtestunit
│   ├── 04_Parking_TestModule.vtestunit
│   └── 05_HHA_TestModule.vtestunit
│
├── CAPL Test Units
│   ├── acc_tests.can
│   ├── lka_ldw_tests.can
│   ├── bsd_tests.can
│   ├── parking_tests.can
│   └── hha_tests.can
│
├── Python Test Scripts
│   ├── acc_regression.py
│   ├── lka_ldw_regression.py
│   ├── bsd_regression.py
│   ├── parking_regression.py
│   └── hha_regression.py
│
└── Reports
    └── (auto-generated HTML/XML)
```

### 5.2 Creating a vTestStudio Test Module (Step by Step)

**Step 1 — New Test Unit**
- Open vTestStudio → File → New Test Unit
- Select **CAPL Test Unit** or **Python Test Unit**
- Link to CANoe configuration file

**Step 2 — Add Test Group**
- Right-click Test Unit → Add Test Group
- Name: `ACC_Functional_Tests`

**Step 3 — Add Test Case**
- Right-click Group → Add Test Case
- For CAPL: select CAPL Test Module, link function `tc_ACC_ActivationAtSetSpeed`
- For Python: select Python Test Module, link `test_acc_activation`

**Step 4 — Define Pre-conditions**
- At Test Setup level:
  - Call `precond_PowerOn()` to apply KL15
  - Call `precond_CANBusNominal()` to verify bus is healthy
  - Call `precond_SetVehicleSpeed(80)` to set initial speed

**Step 5 — Link Verdict**
- Set verdict using `testStepPass()` / `testStepFail()` in CAPL
- Or `teststep.verdict = Verdict.PASS` in Python

**Step 6 — vTestStudio Execution Settings**
- Right-click Test Unit → Properties
- Set: Stop on first failure = OFF
- Set: Repeat on failure = 0
- Set: Report format = HTML + JUnit XML

**Step 7 — Run and View Report**
- Start → Execute Selected Test Units
- Reports auto-generated in `Reports/` folder
- Open `TestReport.html` in browser

### 5.3 vTestStudio System Variables Mapping

Map CANoe environment variables to vTestStudio System Variables:

```xml
<!-- In SystemVariables.vsysvar -->
<SystemVariable name="VehicleSpeed_kph"   type="float"  init="0.0" />
<SystemVariable name="TargetDistance_m"   type="float"  init="100.0" />
<SystemVariable name="LaneOffset_m"       type="float"  init="0.0" />
<SystemVariable name="BSDObjectLeft"      type="int"    init="0" />
<SystemVariable name="HillGrade_pct"      type="float"  init="0.0" />
<SystemVariable name="IgnitionState"      type="int"    init="0" />
```

---

## 6. CAPL Scripts — Feature by Feature

### 6.1 Common Initialization and Utilities

```capl
/*
 * File: common_hil_utils.capl
 * Description: Shared utilities for all HIL ADAS tests
 */

includes
{
  // No external includes needed for standard CANoe
}

variables
{
  // Timing constants
  const int   POWER_ON_DELAY_MS      = 2000;   // ECU boot time
  const int   SIGNAL_SETTLE_MS       = 500;    // Signal stabilisation
  const int   CAN_TIMEOUT_MS         = 200;    // Max wait for CAN message
  const float KL30_VOLTAGE_V         = 12.5;
  const float KL15_VOLTAGE_V         = 12.0;

  // CAN message handles
  message VehicleSpeed           msg_VehSpd;
  message WheelSpeeds            msg_WhlSpd;
  message AccelPedal             msg_AccPdl;
  message BrakePedal             msg_BrkPdl;
  message RadarObj               msg_Radar;
  message CameraLane             msg_Camera;
  message GearPosition           msg_Gear;

  // Test state
  int    gTestStatus  = 0;  // 0=idle, 1=running, 2=pass, 3=fail
  float  gElapsedMs   = 0;
  timer  tWatchdog;
}

/*
 * Apply KL15 (ignition ON) and wait for ECU to boot
 */
void precond_PowerOn()
{
  @sysvar::IgnitionState = 1;
  testWaitForTimeout(POWER_ON_DELAY_MS);
  testStep("Power ON", "KL15 applied, waiting for ECU boot");
}

/*
 * Apply KL15 OFF
 */
void precond_PowerOff()
{
  @sysvar::IgnitionState = 0;
  testWaitForTimeout(500);
}

/*
 * Set vehicle speed by sending VehicleSpeed CAN message
 * param speed_kph : target speed in km/h
 */
void setVehicleSpeed(float speed_kph)
{
  msg_VehSpd.VehSpd_kph = speed_kph;
  output(msg_VehSpd);
  @sysvar::VehicleSpeed_kph = speed_kph;
  testWaitForTimeout(SIGNAL_SETTLE_MS);
}

/*
 * Set leading object distance and relative velocity
 * param dist_m    : distance in metres
 * param relVel_kph: relative velocity (-ve = approaching)
 */
void setLeadingObject(float dist_m, float relVel_kph)
{
  msg_Radar.RadarObj_Dist   = dist_m;
  msg_Radar.RadarObj_RelVel = relVel_kph;
  output(msg_Radar);
  @sysvar::TargetDistance_m = dist_m;
  testWaitForTimeout(SIGNAL_SETTLE_MS);
}

/*
 * Set lane offset (positive = drifting right)
 * param offset_m: lateral offset in metres
 */
void setLaneOffset(float offset_m)
{
  msg_Camera.LatOffset_L_m = -offset_m;
  msg_Camera.LatOffset_R_m =  offset_m;
  msg_Camera.LnMrkng_QL_L  = 3;  // High quality
  msg_Camera.LnMrkng_QL_R  = 3;
  output(msg_Camera);
  @sysvar::LaneOffset_m = offset_m;
  testWaitForTimeout(SIGNAL_SETTLE_MS);
}

/*
 * Apply brake pedal percentage
 * param brk_pct: 0–100%
 */
void applyBrake(float brk_pct)
{
  msg_BrkPdl.BrkPdl_Pct = brk_pct;
  output(msg_BrkPdl);
  testWaitForTimeout(100);
}

/*
 * Set gear position: 1=P, 2=R, 3=N, 4=D
 */
void setGear(int gear)
{
  msg_Gear.GearPos = gear;
  output(msg_Gear);
  testWaitForTimeout(200);
}

/*
 * Generic CAN signal read with timeout
 * Returns 1 if signal received within timeout, 0 otherwise
 */
int waitForSignalValue(char signalPath[], float expected, int timeout_ms)
{
  int      elapsed = 0;
  float    val;

  while (elapsed < timeout_ms) {
    val = @signalPath;
    if (abs(val - expected) < 0.5) return 1;
    testWaitForTimeout(50);
    elapsed += 50;
  }
  return 0;
}
```

---

### 6.2 ACC CAPL Test Script

```capl
/*
 * File: acc_tests.can
 * Description: ACC HIL test cases
 */

includes { "common_hil_utils.capl" }

variables
{
  message AccSwitch   msg_AccSw;
  message ACC_Status  msg_AccStatus;
  message ACC_Control msg_AccCtrl;
  message ACC_HMI     msg_AccHMI;

  const float ACC_ACTIVATION_SPEED_MIN_KPH = 30.0;
  const int   ACC_RESPONSE_TIMEOUT_MS      = 1000;
}

/*======================================================
 * TC-ACC-001: ACC activation at valid set speed
 *====================================================*/
testcase tc_ACC_ActivationAtSetSpeed()
{
  float accStatus;

  testCaseTitle("TC-ACC-001", "ACC Activation At Valid Set Speed");

  // Pre-conditions
  precond_PowerOn();
  setVehicleSpeed(80.0);
  setLeadingObject(50.0, 0.0);

  // Action: Press ACC set button at 80 km/h
  msg_AccSw.ACC_SetSpd  = 80;
  msg_AccSw.ACC_ResumeBtn = 0;
  msg_AccSw.ACC_CancelBtn = 0;
  output(msg_AccSw);

  testStep("Set ACC", "ACC set speed = 80 km/h, pressing set");

  // Verification: ACC_Sts should transition to ACTIVE (0x02) within 1s
  if (waitForSignalValue("ACC_Status::ACC_Sts", 0x02, ACC_RESPONSE_TIMEOUT_MS)) {
    testStepPass("ACC-001-V1", "ACC_Sts = ACTIVE received within 1000 ms");
  } else {
    testStepFail("ACC-001-V1", "ACC_Sts did not reach ACTIVE within timeout");
  }

  // Verify displayed set speed matches commanded speed
  accStatus = @ACC_HMI::ACC_SetSpd_Disp;
  if (abs(accStatus - 80.0) < 1.0) {
    testStepPass("ACC-001-V2", "ACC display set speed = 80 km/h confirmed");
  } else {
    testStepFail("ACC-001-V2", "ACC display set speed mismatch: " + (string)accStatus);
  }

  precond_PowerOff();
}

/*======================================================
 * TC-ACC-002: ACC deceleration when target approaches
 *====================================================*/
testcase tc_ACC_DecelerationOnTargetClose()
{
  float brkReq;

  testCaseTitle("TC-ACC-002", "ACC Brake Request When Target Approaches");

  precond_PowerOn();
  setVehicleSpeed(100.0);

  // Activate ACC first
  msg_AccSw.ACC_SetSpd = 100;
  output(msg_AccSw);
  testWaitForTimeout(1000);

  // Insert target at 15 m approaching at 30 km/h relative
  setLeadingObject(15.0, -30.0);

  testStep("Insert Close Target", "Target at 15m, -30 km/h relative velocity");

  testWaitForTimeout(500);

  // Verify brake request is > 0%
  brkReq = @ACC_Control::ACC_BrkReq_Pct;
  if (brkReq > 0.0) {
    testStepPass("ACC-002-V1", "Brake request active: " + (string)brkReq + " %");
  } else {
    testStepFail("ACC-002-V1", "No brake request despite close target");
  }

  precond_PowerOff();
}

/*======================================================
 * TC-ACC-003: ACC cancel on brake pedal press
 *====================================================*/
testcase tc_ACC_CancelOnBrakePedal()
{
  testCaseTitle("TC-ACC-003", "ACC Cancel When Driver Presses Brake");

  precond_PowerOn();
  setVehicleSpeed(80.0);
  setLeadingObject(60.0, 0.0);

  msg_AccSw.ACC_SetSpd = 80;
  output(msg_AccSw);
  testWaitForTimeout(1000);

  // Driver brakes
  applyBrake(30.0);
  testWaitForTimeout(300);

  // ACC should cancel (status = STANDBY = 0x01)
  if (waitForSignalValue("ACC_Status::ACC_Sts", 0x01, 500)) {
    testStepPass("ACC-003-V1", "ACC cancelled to STANDBY on brake press");
  } else {
    testStepFail("ACC-003-V1", "ACC did not cancel on brake press");
  }

  applyBrake(0.0);
  precond_PowerOff();
}

/*======================================================
 * TC-ACC-004: ACC emergency brake — TTC < 1.5s
 *====================================================*/
testcase tc_ACC_EmergencyBrakeOnLowTTC()
{
  testCaseTitle("TC-ACC-004", "Emergency Brake Triggered at TTC < 1.5s");

  precond_PowerOn();
  setVehicleSpeed(120.0);
  setLeadingObject(100.0, 0.0);

  msg_AccSw.ACC_SetSpd = 120;
  output(msg_AccSw);
  testWaitForTimeout(1000);

  // Rapidly reduce distance to simulate cut-in
  setLeadingObject(40.0, -80.0);
  testWaitForTimeout(300);

  if (waitForSignalValue("ACC_Decel::ACC_EmgcyBrk", 1.0, 800)) {
    testStepPass("ACC-004-V1", "Emergency brake flag raised on critical TTC");
  } else {
    testStepFail("ACC-004-V1", "Emergency brake NOT raised");
  }

  precond_PowerOff();
}
```

---

### 6.3 LKA / LDW CAPL Test Script

```capl
/*
 * File: lka_ldw_tests.can
 * Description: LKA and LDW HIL test cases
 */

includes { "common_hil_utils.capl" }

variables
{
  message LKA_Status  msg_LKASts;
  message LKA_Output  msg_LKAOut;
  message LDW_Status  msg_LDWSts;
  message TurnSignal  msg_TurnSig;

  const float LKA_MIN_SPEED_KPH   = 60.0;
  const float LDW_OFFSET_THRESH_M = 0.25;  // Lane departure threshold
  const int   LKA_RESPONSE_MS     = 800;
}

/*======================================================
 * TC-LKA-001: LKA steering torque on lane drift right
 *====================================================*/
testcase tc_LKA_SteeringTorqueOnRightDrift()
{
  float lkaTrq;

  testCaseTitle("TC-LKA-001", "LKA Steering Overlay on Right Lane Drift");

  precond_PowerOn();
  setVehicleSpeed(80.0);
  setLaneOffset(0.0);  // Start centred

  testWaitForTimeout(500);

  // Drift right by 0.35m (beyond LDW threshold)
  setLaneOffset(0.35);

  if (waitForSignalValue("LKA_Status::LKA_Sts", 0x03, LKA_RESPONSE_MS)) {
    testStepPass("LKA-001-V1", "LKA status = INTERVENING");
  } else {
    testStepFail("LKA-001-V1", "LKA not intervening on 0.35m drift");
  }

  lkaTrq = @LKA_Output::LKA_TrqOvrd_Nm;
  if (lkaTrq < 0.0) {
    // Negative torque = corrects rightward drift back left
    testStepPass("LKA-001-V2", "Corrective torque = " + (string)lkaTrq + " Nm (left correction)");
  } else {
    testStepFail("LKA-001-V2", "Torque direction incorrect: " + (string)lkaTrq + " Nm");
  }

  precond_PowerOff();
}

/*======================================================
 * TC-LKA-002: LKA suppressed when turn signal active
 *====================================================*/
testcase tc_LKA_SuppressedOnTurnSignal()
{
  testCaseTitle("TC-LKA-002", "LKA Suppressed When Right Turn Signal On");

  precond_PowerOn();
  setVehicleSpeed(80.0);

  // Activate right turn signal
  msg_TurnSig.TurnSig_R = 1;
  output(msg_TurnSig);
  testWaitForTimeout(200);

  // Drift right — LKA should NOT intervene
  setLaneOffset(0.40);
  testWaitForTimeout(LKA_RESPONSE_MS);

  float lkaSts = @LKA_Status::LKA_Sts;
  if (lkaSts != 0x03) {
    testStepPass("LKA-002-V1", "LKA correctly suppressed with turn signal active");
  } else {
    testStepFail("LKA-002-V1", "LKA intervened with turn signal — unexpected");
  }

  msg_TurnSig.TurnSig_R = 0;
  output(msg_TurnSig);
  precond_PowerOff();
}

/*======================================================
 * TC-LDW-001: LDW audio warning at lane departure
 *====================================================*/
testcase tc_LDW_AudioWarnOnDeparture()
{
  testCaseTitle("TC-LDW-001", "LDW Audio Warning on Lane Departure");

  precond_PowerOn();
  setVehicleSpeed(75.0);
  setLaneOffset(0.0);

  // Gradually move to lane marking
  setLaneOffset(0.28);
  testWaitForTimeout(300);

  if (waitForSignalValue("LDW_HMI::LDW_AudioWarn", 1.0, 600)) {
    testStepPass("LDW-001-V1", "LDW audio warning triggered at 0.28m offset");
  } else {
    testStepFail("LDW-001-V1", "LDW audio warning NOT triggered");
  }

  precond_PowerOff();
}

/*======================================================
 * TC-LKA-003: LKA inactive below minimum speed
 *====================================================*/
testcase tc_LKA_InactiveBelowMinSpeed()
{
  testCaseTitle("TC-LKA-003", "LKA Inactive Below 60 km/h");

  precond_PowerOn();
  setVehicleSpeed(45.0);  // Below LKA minimum
  setLaneOffset(0.40);
  testWaitForTimeout(800);

  float lkaSts = @LKA_Status::LKA_Sts;
  if (lkaSts == 0x00 || lkaSts == 0x01) {
    testStepPass("LKA-003-V1", "LKA inactive at 45 km/h as expected");
  } else {
    testStepFail("LKA-003-V1", "LKA active at 45 km/h — unexpected activation");
  }

  precond_PowerOff();
}
```

---

### 6.4 BSD CAPL Test Script

```capl
/*
 * File: bsd_tests.can
 * Description: Blind Spot Detection HIL tests
 */

includes { "common_hil_utils.capl" }

variables
{
  message RearRadarL  msg_RearRadL;
  message RearRadarR  msg_RearRadR;
  message BSD_Status  msg_BSDSts;
  message BSD_HMI     msg_BSDHMI;
  message TurnSignal  msg_TurnSig;

  const int BSD_RESPONSE_MS = 400;
}

/*======================================================
 * TC-BSD-001: BSD warning light on left object
 *====================================================*/
testcase tc_BSD_LeftObjectWarning()
{
  testCaseTitle("TC-BSD-001", "BSD Left Warning on Object Detection");

  precond_PowerOn();
  setVehicleSpeed(70.0);

  // Inject object in left blind zone
  msg_RearRadL.BSD_ObjDet_L     = 1;
  msg_RearRadL.BSD_ObjDist_L_m  = 3.5;
  msg_RearRadL.BSD_ObjRelVel_L  = -5.0;
  output(msg_RearRadL);

  if (waitForSignalValue("BSD_Status::BSD_Warn_L", 1.0, BSD_RESPONSE_MS)) {
    testStepPass("BSD-001-V1", "BSD left warning activated");
  } else {
    testStepFail("BSD-001-V1", "BSD left warning NOT activated");
  }

  // Check LED state = FLASHING (0x02)
  if (waitForSignalValue("BSD_HMI::BSD_LED_L", 0x02, BSD_RESPONSE_MS)) {
    testStepPass("BSD-001-V2", "Left mirror LED = FLASHING confirmed");
  } else {
    testStepFail("BSD-001-V2", "Left mirror LED not in FLASHING state");
  }

  // Clear object
  msg_RearRadL.BSD_ObjDet_L = 0;
  output(msg_RearRadL);
  precond_PowerOff();
}

/*======================================================
 * TC-BSD-002: BSD chime when signal + object
 *====================================================*/
testcase tc_BSD_ChimeOnSignalWithObject()
{
  testCaseTitle("TC-BSD-002", "BSD Chime When Turn Signal Active with Object");

  precond_PowerOn();
  setVehicleSpeed(70.0);

  // Object in right zone
  msg_RearRadR.BSD_ObjDet_R    = 1;
  msg_RearRadR.BSD_ObjDist_R_m = 2.8;
  output(msg_RearRadR);
  testWaitForTimeout(200);

  // Driver activates right signal
  msg_TurnSig.TurnSig_R = 1;
  output(msg_TurnSig);

  if (waitForSignalValue("BSD_Audio::BSD_Chime", 1.0, 600)) {
    testStepPass("BSD-002-V1", "BSD chime triggered on signal + object");
  } else {
    testStepFail("BSD-002-V1", "BSD chime NOT triggered");
  }

  msg_TurnSig.TurnSig_R = 0;
  output(msg_TurnSig);
  precond_PowerOff();
}

/*======================================================
 * TC-BSD-003: BSD inactive below 10 km/h
 *====================================================*/
testcase tc_BSD_InactiveBelowMinSpeed()
{
  testCaseTitle("TC-BSD-003", "BSD Inactive Below 10 km/h");

  precond_PowerOn();
  setVehicleSpeed(5.0);

  msg_RearRadL.BSD_ObjDet_L = 1;
  output(msg_RearRadL);
  testWaitForTimeout(BSD_RESPONSE_MS);

  float bsdWarn = @BSD_Status::BSD_Warn_L;
  if (bsdWarn == 0) {
    testStepPass("BSD-003-V1", "BSD correctly inactive at 5 km/h");
  } else {
    testStepFail("BSD-003-V1", "BSD unexpectedly active at 5 km/h");
  }

  precond_PowerOff();
}
```

---

### 6.5 Parking Assistance CAPL Test Script

```capl
/*
 * File: parking_tests.can
 * Description: Parking Assistance HIL tests
 */

includes { "common_hil_utils.capl" }

variables
{
  message ParkSensor_LIN  msg_ParkSensor;
  message Park_Status     msg_ParkSts;
  message Park_HMI        msg_ParkHMI;
  message Park_BrkCtrl    msg_ParkBrk;
  message ParkButton      msg_ParkBtn;

  const int PARK_RESPONSE_MS = 600;
}

/*======================================================
 * TC-PARK-001: Park assist activates in reverse gear
 *====================================================*/
testcase tc_Park_ActivationInReverse()
{
  testCaseTitle("TC-PARK-001", "Parking Assist Activates in Reverse Gear");

  precond_PowerOn();
  setVehicleSpeed(3.0);
  setGear(2);  // Reverse

  msg_ParkBtn.Park_Btn = 1;
  output(msg_ParkBtn);

  if (waitForSignalValue("Park_Status::Park_Sts", 0x01, PARK_RESPONSE_MS)) {
    testStepPass("PARK-001-V1", "Park assist ACTIVE in reverse gear");
  } else {
    testStepFail("PARK-001-V1", "Park assist did not activate in reverse");
  }

  setGear(4);
  precond_PowerOff();
}

/*======================================================
 * TC-PARK-002: Tone zone changes with distance
 *====================================================*/
testcase tc_Park_ToneZoneScaling()
{
  int zone;

  testCaseTitle("TC-PARK-002", "Park Tone Zone Scales With Distance");

  precond_PowerOn();
  setVehicleSpeed(3.0);
  setGear(2);

  msg_ParkBtn.Park_Btn = 1;
  output(msg_ParkBtn);
  testWaitForTimeout(PARK_RESPONSE_MS);

  // 150cm — expect zone 2 (far)
  msg_ParkSensor.UltraSnd_RR_cm = 150;
  output(msg_ParkSensor);
  testWaitForTimeout(300);
  zone = @Park_HMI::Park_Display_Zone;
  if (zone <= 3) {
    testStepPass("PARK-002-V1", "Zone at 150cm = " + (string)zone + " (far zone)");
  } else {
    testStepFail("PARK-002-V1", "Zone unexpected at 150cm: " + (string)zone);
  }

  // 30cm — expect zone 6+ (close)
  msg_ParkSensor.UltraSnd_RR_cm = 30;
  output(msg_ParkSensor);
  testWaitForTimeout(300);
  zone = @Park_HMI::Park_Display_Zone;
  if (zone >= 6) {
    testStepPass("PARK-002-V2", "Zone at 30cm = " + (string)zone + " (close zone)");
  } else {
    testStepFail("PARK-002-V2", "Zone not in close range at 30cm: " + (string)zone);
  }

  setGear(4);
  precond_PowerOff();
}

/*======================================================
 * TC-PARK-003: Automatic brake at critical distance
 *====================================================*/
testcase tc_Park_AutoBrakeAtCriticalDistance()
{
  testCaseTitle("TC-PARK-003", "Auto Brake at Critical Distance (< 20cm)");

  precond_PowerOn();
  setVehicleSpeed(3.0);
  setGear(2);

  msg_ParkBtn.Park_Btn = 1;
  output(msg_ParkBtn);
  testWaitForTimeout(PARK_RESPONSE_MS);

  // Critical distance
  msg_ParkSensor.UltraSnd_RR_cm = 15;
  output(msg_ParkSensor);

  if (waitForSignalValue("Park_BrkCtrl::Park_BrkReq", 1.0, 800)) {
    testStepPass("PARK-003-V1", "Auto brake request at 15cm confirmed");
  } else {
    testStepFail("PARK-003-V1", "Auto brake NOT triggered at 15cm");
  }

  setGear(4);
  precond_PowerOff();
}
```

---

### 6.6 Hill Hold Assist CAPL Test Script

```capl
/*
 * File: hha_tests.can
 * Description: Hill Hold Assist HIL tests
 */

includes { "common_hil_utils.capl" }

variables
{
  message LongitudinalAccel  msg_LongAccel;
  message InclineSensor      msg_Incline;
  message BrakeFluidPressure msg_BrkPress;
  message HHA_Status         msg_HHASts;
  message HHA_Output         msg_HHAOut;

  const int HHA_RESPONSE_MS = 500;
  const float HILL_GRADE_PCT = 8.0;   // 8% gradient
}

/*======================================================
 * TC-HHA-001: Hill hold activates on uphill stop
 *====================================================*/
testcase tc_HHA_ActivateOnUphillStop()
{
  testCaseTitle("TC-HHA-001", "HHA Activates on Uphill Stop");

  precond_PowerOn();

  // Simulate uphill gradient
  msg_Incline.Slope_Pct       = HILL_GRADE_PCT;
  msg_LongAccel.LongAccel_g   = 0.07;   // 8% slope ≈ 0.07g
  output(msg_Incline);
  output(msg_LongAccel);

  // Vehicle stopped on hill
  setVehicleSpeed(0.0);
  setGear(4);  // Drive

  // Driver presses brake fully
  applyBrake(100.0);
  testWaitForTimeout(300);

  // Release brake
  applyBrake(0.0);
  testWaitForTimeout(200);

  if (waitForSignalValue("HHA_Status::HHA_Sts", 0x02, HHA_RESPONSE_MS)) {
    testStepPass("HHA-001-V1", "HHA status = HOLDING on uphill stop");
  } else {
    testStepFail("HHA-001-V1", "HHA HOLDING state not reached");
  }

  // Verify indicator on cluster
  if (waitForSignalValue("HHA_HMI::HHA_Indicator", 1.0, 300)) {
    testStepPass("HHA-001-V2", "HHA cluster indicator active");
  } else {
    testStepFail("HHA-001-V2", "HHA cluster indicator NOT active");
  }

  precond_PowerOff();
}

/*======================================================
 * TC-HHA-002: HHA hold duration measurement
 *====================================================*/
testcase tc_HHA_HoldDurationMeasurement()
{
  float holdDuration;

  testCaseTitle("TC-HHA-002", "HHA Brake Hold Duration 0–3000 ms");

  precond_PowerOn();

  msg_Incline.Slope_Pct = HILL_GRADE_PCT;
  output(msg_Incline);
  setVehicleSpeed(0.0);
  setGear(4);

  applyBrake(100.0);
  testWaitForTimeout(300);
  applyBrake(0.0);
  testWaitForTimeout(500);

  holdDuration = @HHA_Output::HHA_HoldDuration_ms;

  if (holdDuration > 0 && holdDuration <= 3000) {
    testStepPass("HHA-002-V1", "HHA hold duration = " + (string)holdDuration + " ms (in range)");
  } else {
    testStepFail("HHA-002-V1", "HHA hold duration out of range: " + (string)holdDuration + " ms");
  }

  precond_PowerOff();
}

/*======================================================
 * TC-HHA-003: HHA not active on flat road (< 2% grade)
 *====================================================*/
testcase tc_HHA_NotActiveOnFlatRoad()
{
  testCaseTitle("TC-HHA-003", "HHA Not Active on Flat Road");

  precond_PowerOn();

  msg_Incline.Slope_Pct = 1.0;  // Flat
  output(msg_Incline);
  setVehicleSpeed(0.0);
  setGear(4);

  applyBrake(100.0);
  testWaitForTimeout(300);
  applyBrake(0.0);
  testWaitForTimeout(HHA_RESPONSE_MS);

  float hhaSts = @HHA_Status::HHA_Sts;
  if (hhaSts != 0x02) {
    testStepPass("HHA-003-V1", "HHA not holding on flat road as expected");
  } else {
    testStepFail("HHA-003-V1", "HHA activated on flat road — unexpected");
  }

  precond_PowerOff();
}
```

---

## 7. Python Scripts — Automation Layer

### 7.1 CANoe Python Automation via COM Interface

```python
# File: canoe_interface.py
# Description: CANoe COM interface wrapper for Python automation

import win32com.client
import time
import os
from pathlib import Path


class CANoeHILInterface:
    """
    Wrapper around Vector CANoe COM API for HIL test automation.
    Requires pywin32: pip install pywin32
    Must run on Windows with CANoe installed.
    """

    def __init__(self, config_path: str):
        self.app = win32com.client.Dispatch("CANoe.Application")
        self.config_path = Path(config_path)
        self._measurement = None
        self._environment = None

    def open_config(self):
        """Load CANoe configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        self.app.Open(str(self.config_path))
        time.sleep(2)
        self._measurement = self.app.Measurement
        self._environment = self.app.Environment
        print(f"[CANoe] Config loaded: {self.config_path.name}")

    def start_measurement(self):
        """Start CANoe measurement (simulation)."""
        self._measurement.Start()
        time.sleep(1)
        print("[CANoe] Measurement started")

    def stop_measurement(self):
        """Stop CANoe measurement."""
        self._measurement.Stop()
        time.sleep(0.5)
        print("[CANoe] Measurement stopped")

    def set_env_variable(self, name: str, value):
        """Write to a CANoe environment variable."""
        var = self._environment.GetVariable(name)
        var.Value = value

    def get_env_variable(self, name: str):
        """Read a CANoe environment variable."""
        var = self._environment.GetVariable(name)
        return var.Value

    def get_signal_value(self, channel: int, message: str, signal: str) -> float:
        """Read current value of a CAN signal from the bus."""
        sig = self.app.GetBus("CAN").GetSignal(channel, message, signal)
        return sig.Value

    def send_message(self, channel: int, msg_id: int, dlc: int, data: bytes):
        """Inject a raw CAN frame."""
        msg = self.app.GetBus("CAN").GetMessage(channel, msg_id)
        for i, byte in enumerate(data[:dlc]):
            msg.SetByteValue(i, byte)
        msg.Send()

    def close(self):
        """Release COM object."""
        self.app.Quit()
        print("[CANoe] Application closed")
```

---

### 7.2 ACC Python Regression Tests

```python
# File: acc_regression.py
# Description: ACC HIL regression test suite using CANoe COM interface

import pytest
import time
from canoe_interface import CANoeHILInterface

CONFIG_PATH = r"C:\HIL\ADAS_Tests\ADAS_HIL.cfg"


@pytest.fixture(scope="session")
def canoe():
    """Session-scoped CANoe interface fixture."""
    interface = CANoeHILInterface(CONFIG_PATH)
    interface.open_config()
    interface.start_measurement()
    yield interface
    interface.stop_measurement()
    interface.close()


def set_vehicle_speed(canoe: CANoeHILInterface, speed_kph: float):
    canoe.set_env_variable("VehicleSpeed_kph", speed_kph)
    time.sleep(0.5)


def set_target_object(canoe: CANoeHILInterface, dist_m: float, rel_vel_kph: float):
    canoe.set_env_variable("TargetDistance_m", dist_m)
    canoe.set_env_variable("TargetRelVelocity_kph", rel_vel_kph)
    time.sleep(0.5)


def activate_acc(canoe: CANoeHILInterface, set_speed_kph: float):
    canoe.set_env_variable("ACC_SetSpeed_kph", set_speed_kph)
    canoe.set_env_variable("ACC_SetButton", 1)
    time.sleep(0.1)
    canoe.set_env_variable("ACC_SetButton", 0)
    time.sleep(1.0)


def get_acc_status(canoe: CANoeHILInterface) -> int:
    return int(canoe.get_signal_value(1, "ACC_Status", "ACC_Sts"))


def get_acc_brake_request(canoe: CANoeHILInterface) -> float:
    return float(canoe.get_signal_value(1, "ACC_Control", "ACC_BrkReq_Pct"))


# ──────────────────────────────────────────────────────────────
# ACC Test Cases
# ──────────────────────────────────────────────────────────────

class TestACCActivation:

    def test_acc_activates_at_80kph(self, canoe):
        """TC-ACC-001: ACC activation at 80 km/h."""
        set_vehicle_speed(canoe, 80.0)
        set_target_object(canoe, 60.0, 0.0)
        activate_acc(canoe, 80.0)

        acc_status = get_acc_status(canoe)
        assert acc_status == 0x02, (
            f"Expected ACC_Sts=0x02 (ACTIVE), got 0x{acc_status:02X}"
        )

    def test_acc_displays_correct_set_speed(self, canoe):
        """TC-ACC-001b: Set speed displayed on HMI matches commanded."""
        set_vehicle_speed(canoe, 100.0)
        activate_acc(canoe, 100.0)

        disp_speed = canoe.get_signal_value(1, "ACC_HMI", "ACC_SetSpd_Disp")
        assert abs(disp_speed - 100.0) < 1.5, (
            f"Display speed {disp_speed} does not match commanded 100.0 km/h"
        )

    def test_acc_inactive_below_30kph(self, canoe):
        """TC-ACC-003: ACC should not activate below 30 km/h."""
        set_vehicle_speed(canoe, 20.0)
        activate_acc(canoe, 30.0)

        acc_status = get_acc_status(canoe)
        assert acc_status != 0x02, (
            "ACC activated at 20 km/h — should be blocked by min-speed gate"
        )


class TestACCBrakeControl:

    def test_brake_request_on_close_target(self, canoe):
        """TC-ACC-002: Brake request triggered when target approaches."""
        set_vehicle_speed(canoe, 100.0)
        set_target_object(canoe, 60.0, 0.0)
        activate_acc(canoe, 100.0)

        # Bring target close
        set_target_object(canoe, 12.0, -40.0)
        time.sleep(0.5)

        brk_req = get_acc_brake_request(canoe)
        assert brk_req > 0.0, (
            f"Expected brake request > 0%, got {brk_req}%"
        )

    def test_acc_cancel_on_brake_pedal(self, canoe):
        """TC-ACC-004: ACC cancels when driver applies brake."""
        set_vehicle_speed(canoe, 80.0)
        set_target_object(canoe, 50.0, 0.0)
        activate_acc(canoe, 80.0)
        time.sleep(0.5)

        # Driver brakes
        canoe.set_env_variable("BrakePedal_Pct", 40.0)
        time.sleep(0.4)

        acc_status = get_acc_status(canoe)
        assert acc_status in (0x00, 0x01), (
            f"ACC should be STANDBY/OFF after brake, got 0x{acc_status:02X}"
        )

        canoe.set_env_variable("BrakePedal_Pct", 0.0)


class TestACCEmergencyBrake:

    @pytest.mark.parametrize("dist_m,rel_vel_kph", [
        (8.0,  -60.0),
        (5.0,  -80.0),
        (10.0, -70.0),
    ])
    def test_emergency_brake_triggered(self, canoe, dist_m, rel_vel_kph):
        """TC-ACC-005: Emergency brake on critical TTC scenarios."""
        set_vehicle_speed(canoe, 120.0)
        set_target_object(canoe, 100.0, 0.0)
        activate_acc(canoe, 120.0)

        set_target_object(canoe, dist_m, rel_vel_kph)
        time.sleep(0.8)

        emg_brk = int(canoe.get_signal_value(1, "ACC_Decel", "ACC_EmgcyBrk"))
        assert emg_brk == 1, (
            f"Emergency brake not triggered at {dist_m}m / {rel_vel_kph} km/h rel"
        )
```

---

### 7.3 LKA/LDW Python Regression Tests

```python
# File: lka_ldw_regression.py
# Description: LKA and LDW regression tests

import pytest
import time
from canoe_interface import CANoeHILInterface

CONFIG_PATH = r"C:\HIL\ADAS_Tests\ADAS_HIL.cfg"


@pytest.fixture(scope="session")
def canoe():
    iface = CANoeHILInterface(CONFIG_PATH)
    iface.open_config()
    iface.start_measurement()
    yield iface
    iface.stop_measurement()
    iface.close()


def set_lane_scenario(canoe, speed_kph, offset_m, lane_quality=3):
    canoe.set_env_variable("VehicleSpeed_kph", speed_kph)
    canoe.set_env_variable("LaneOffset_m", offset_m)
    canoe.set_env_variable("LaneMarkingQuality", lane_quality)
    time.sleep(0.6)


class TestLKAIntervention:

    def test_lka_torque_on_right_drift(self, canoe):
        """TC-LKA-001: Corrective torque on 0.35m right lane drift."""
        set_lane_scenario(canoe, 80.0, 0.35)

        lka_sts = int(canoe.get_signal_value(1, "LKA_Status", "LKA_Sts"))
        lka_trq = float(canoe.get_signal_value(1, "LKA_Output", "LKA_TrqOvrd_Nm"))

        assert lka_sts == 0x03, f"LKA_Sts expected INTERVENING(3), got {lka_sts}"
        assert lka_trq < 0, f"Corrective torque should be negative, got {lka_trq} Nm"

    def test_lka_suppressed_with_right_indicator(self, canoe):
        """TC-LKA-002: LKA suppressed when right indicator is on."""
        canoe.set_env_variable("TurnSignalRight", 1)
        set_lane_scenario(canoe, 80.0, 0.40)

        lka_sts = int(canoe.get_signal_value(1, "LKA_Status", "LKA_Sts"))
        assert lka_sts != 0x03, "LKA must NOT intervene with turn indicator ON"
        canoe.set_env_variable("TurnSignalRight", 0)

    @pytest.mark.parametrize("speed_kph", [30, 45, 55, 59])
    def test_lka_inactive_below_60kph(self, canoe, speed_kph):
        """TC-LKA-003: LKA inactive below 60 km/h."""
        set_lane_scenario(canoe, speed_kph, 0.40)
        lka_sts = int(canoe.get_signal_value(1, "LKA_Status", "LKA_Sts"))
        assert lka_sts != 0x03, f"LKA should not intervene at {speed_kph} km/h"


class TestLDWWarnings:

    def test_ldw_audio_warning(self, canoe):
        """TC-LDW-001: Audio warning at lane departure."""
        set_lane_scenario(canoe, 75.0, 0.28)
        audio = int(canoe.get_signal_value(1, "LDW_HMI", "LDW_AudioWarn"))
        assert audio == 1, "LDW audio warning not triggered at 0.28m offset"

    def test_ldw_no_warning_with_good_lane_centering(self, canoe):
        """TC-LDW-002: No LDW warning when well centred."""
        set_lane_scenario(canoe, 80.0, 0.05)
        audio = int(canoe.get_signal_value(1, "LDW_HMI", "LDW_AudioWarn"))
        assert audio == 0, "Spurious LDW warning detected while well centred"

    @pytest.mark.parametrize("quality", [0, 1])
    def test_ldw_inactive_on_poor_lane_quality(self, canoe, quality):
        """TC-LDW-003: LDW inactive on poor lane marking quality."""
        set_lane_scenario(canoe, 80.0, 0.40, lane_quality=quality)
        ldw_sts = int(canoe.get_signal_value(1, "LDW_Status", "LDW_Sts"))
        assert ldw_sts == 0, f"LDW active on lane quality={quality} — unexpected"
```

---

### 7.4 Test Runner and Report Generator

```python
# File: run_hil_suite.py
# Description: Master HIL test runner with HTML report and JUnit XML output

import subprocess
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="ADAS HIL Test Runner")
    parser.add_argument("--feature", choices=["ALL","ACC","LKA","BSD","PARK","HHA"],
                        default="ALL")
    parser.add_argument("--build-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--min-pass-rate", type=float, default=95.0)
    return parser.parse_args()


FEATURE_MAP = {
    "ACC":  "acc_regression.py",
    "LKA":  "lka_ldw_regression.py",
    "BSD":  "bsd_regression.py",
    "PARK": "parking_regression.py",
    "HHA":  "hha_regression.py",
}


def run_feature(feature: str, build_id: str, output_dir: Path) -> dict:
    script = FEATURE_MAP[feature]
    report_html = output_dir / f"{build_id}_{feature}_report.html"
    report_xml  = output_dir / f"{build_id}_{feature}_junit.xml"

    cmd = [
        sys.executable, "-m", "pytest",
        script,
        "-v", "-q",
        f"--junitxml={report_xml}",
        f"--html={report_html}",
        "--self-contained-html",
    ]

    print(f"\n▶ Running {feature} tests...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    return {
        "feature":   feature,
        "returncode": result.returncode,
        "html_report": str(report_html),
        "xml_report":  str(report_xml),
        "stdout": result.stdout[-2000:],  # Last 2000 chars
    }


def main():
    args   = parse_args()
    outdir = Path(args.output_dir) / args.build_id
    outdir.mkdir(parents=True, exist_ok=True)

    features = list(FEATURE_MAP.keys()) if args.feature == "ALL" else [args.feature]
    results  = []

    for feat in features:
        res = run_feature(feat, args.build_id, outdir)
        results.append(res)

    all_pass = all(r["returncode"] == 0 for r in results)
    summary = {
        "build_id":   args.build_id,
        "generated":  datetime.now().isoformat(),
        "gate":       "PASSED" if all_pass else "FAILED",
        "features":   results,
    }

    summary_path = outdir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print("\n" + "="*60)
    print(f"  ADAS HIL Gate: {summary['gate']}")
    print(f"  Build:         {args.build_id}")
    print(f"  Reports:       {outdir}")
    print("="*60)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
```

---

## 8. Test Case Catalogue per Feature

### Summary Table

| Feature | TC ID | Test Name | Type | Priority |
|---------|-------|-----------|------|----------|
| ACC | TC-ACC-001 | Activation at valid set speed | Functional | P1 |
| ACC | TC-ACC-002 | Brake request on approaching target | Functional | P1 |
| ACC | TC-ACC-003 | Cancel on brake pedal press | Functional | P1 |
| ACC | TC-ACC-004 | Emergency brake at TTC < 1.5s | Safety | P0 |
| ACC | TC-ACC-005 | Speed reduction to set speed | Functional | P1 |
| ACC | TC-ACC-006 | Resume after standstill | Functional | P2 |
| ACC | TC-ACC-007 | Target lost — maintain set speed | Edge Case | P2 |
| ACC | TC-ACC-008 | Fault mode — radar failure | Fault | P1 |
| LKA | TC-LKA-001 | Steering torque on left drift | Functional | P1 |
| LKA | TC-LKA-002 | Steering torque on right drift | Functional | P1 |
| LKA | TC-LKA-003 | Suppressed on turn indicator | Functional | P1 |
| LKA | TC-LKA-004 | Inactive below 60 km/h | Boundary | P1 |
| LKA | TC-LKA-005 | Inactive on poor lane marking | Edge Case | P2 |
| LKA | TC-LKA-006 | No intervention on sharp curve | Edge Case | P2 |
| LDW | TC-LDW-001 | Audio warning on departure | Functional | P1 |
| LDW | TC-LDW-002 | No warning when centred | Negative | P1 |
| LDW | TC-LDW-003 | Haptic warning on departure | Functional | P2 |
| BSD | TC-BSD-001 | Left zone warning | Functional | P1 |
| BSD | TC-BSD-002 | Right zone warning | Functional | P1 |
| BSD | TC-BSD-003 | Chime on signal + object | Functional | P1 |
| BSD | TC-BSD-004 | Inactive below 10 km/h | Boundary | P1 |
| BSD | TC-BSD-005 | No warning when zone clear | Negative | P1 |
| PARK | TC-PARK-001 | Activation in reverse gear | Functional | P1 |
| PARK | TC-PARK-002 | Tone zone scaling | Functional | P1 |
| PARK | TC-PARK-003 | Auto brake at < 20cm | Safety | P0 |
| PARK | TC-PARK-004 | Deactivation above 10 km/h | Boundary | P1 |
| PARK | TC-PARK-005 | Sensor fault degradation | Fault | P1 |
| HHA | TC-HHA-001 | Hold on uphill stop | Functional | P1 |
| HHA | TC-HHA-002 | Hold duration measurement | Timing | P1 |
| HHA | TC-HHA-003 | Not active on flat road | Boundary | P1 |
| HHA | TC-HHA-004 | Release on acceleration request | Functional | P1 |
| HHA | TC-HHA-005 | Timeout after 3s without drive | Timing | P2 |

---

## 9. Fault Injection Procedures

### 9.1 CAN Bus Fault Injection via CANoe

```capl
/*
 * Inject CAN bus error to simulate sensor fault
 * Use CANoe's Error Frame Generator or programmatic approach
 */

variables
{
  msTimer tFaultTimer;
}

// Inject dominant error flag on Channel 1 for 200ms
on key 'f'
{
  // Enable error generation on CH1
  canSetErrorActive(1, 0);   // Set to error passive
  setTimer(tFaultTimer, 200);
}

on timer tFaultTimer
{
  canSetErrorActive(1, 1);   // Restore to error active
  testStep("FaultInjection", "Error passive restored after 200ms");
}
```

### 9.2 Relay-Based Fault Injection (Hardware)

| Fault Scenario | Method | Duration | Expected ECU Response |
|---|---|---|---|
| CAN bus open circuit | Open relay on CAN-H | 500ms | DTC U0001 logged, ADAS disable |
| Radar power loss | Open relay on radar +12V | 2s | ACC/AEB disabled, DTC stored |
| Steering angle sensor fault | Short CAN signal to GND | 100ms | LKA disabled, DTC B1234 |
| Ultrasonic sensor fault | Terminate LIN bus | Persistent | PARK disabled, warning lamp |
| Brake pressure sensor fault | Open wire | 200ms | HHA disabled |

### 9.3 DTC Verification after Fault

```python
# File: dtc_verify.py
# Verify expected DTCs are set after fault injection using DoIP

import socket
import struct

UDS_READ_DTC = bytes([0x03])  # Service 0x19 Sub-function 0x02

def read_active_dtcs(ecu_ip: str, port: int = 13400) -> list:
    """Read all active DTCs via UDS over DoIP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ecu_ip, port))

    # UDS ReadDTCInformation (Service 0x19, subfunction 0x02)
    payload = bytes([0x19, 0x02, 0xFF])
    header  = struct.pack(">HHI", 0x8001, 0x0001, len(payload))
    sock.send(header + payload)

    response = sock.recv(1024)
    sock.close()

    # Parse DTC bytes (3 bytes per DTC entry)
    dtc_list = []
    data = response[8:]  # Skip DoIP header (8 bytes)
    for i in range(1, len(data) - 3, 4):
        dtc = (data[i] << 16) | (data[i+1] << 8) | data[i+2]
        dtc_list.append(f"0x{dtc:06X}")

    return dtc_list


def test_radar_fault_dtc_present():
    """After radar power loss, U010000 or equivalent must be set."""
    dtcs = read_active_dtcs("192.168.1.100")
    assert any("U0100" in d for d in dtcs), (
        f"Expected radar comm DTC not found. Active DTCs: {dtcs}"
    )
```

---

## 10. Measurement and Logging Strategy

### 10.1 CANoe Logging Configuration

1. **Open** CANoe → Logging → New Logging Block
2. Set format: **MF4** (recommended) or **BLF**
3. Trigger: Start on Measurement Start, Stop on Measurement Stop
4. Add filters for relevant message IDs only (reduces file size):

| Feature | Message IDs to Log |
|---|---|
| ACC | 0x1A0, 0x1A1, 0x1B0, 0x2C0, 0x3F0 |
| LKA | 0x280, 0x281, 0x290, 0x291 |
| BSD | 0x310, 0x311, 0x312 |
| PARK | 0x350, 0x351, 0x352 |
| HHA | 0x370, 0x371 |

### 10.2 Key Measurement Variables to Track

```
VehicleSpeed_kph         — always log
TargetDistance_m         — for ACC/AEB
LateralOffset_m          — for LKA/LDW
ACCStatus (0x1A0)        — state machine transition timing
LKA_TorqueOverlay_Nm     — intervention magnitude
BSD_WarningLeft/Right    — detection latency
ParkBrakeRequest         — safety-critical brake command
HHA_HoldDuration_ms      — timing accuracy
```

### 10.3 Latency Measurement CAPL

```capl
/*
 * Measure latency between stimulus and ECU response
 */

variables
{
  dword  gStimulusTime_ms  = 0;
  dword  gResponseTime_ms  = 0;
  float  gLatency_ms       = 0;
}

on envVar VehicleSpeed_kph
{
  // Record time when scenario changes
  gStimulusTime_ms = timeNow() / 100000; // ns -> ms
}

on message ACC_Status
{
  if (this.ACC_Sts == 0x02 && gStimulusTime_ms > 0) {
    gResponseTime_ms = timeNow() / 100000;
    gLatency_ms      = gResponseTime_ms - gStimulusTime_ms;
    testStep("Latency", "ACC activation latency = " + (string)gLatency_ms + " ms");
    gStimulusTime_ms = 0;  // Reset for next measurement
  }
}
```

---

## 11. Pass/Fail Criteria

### 11.1 Feature-Level Acceptance Criteria

| Feature | Criterion | Limit | Measurement |
|---|---|---|---|
| ACC | Activation latency from set press | ≤ 1000 ms | CAN signal timestamp |
| ACC | Brake intervention latency at critical TTC | ≤ 400 ms | CAN timestamp |
| ACC | Set speed accuracy | ±2 km/h | Sustained speed vs. set speed |
| LKA | Torque response time | ≤ 800 ms | Drift onset to torque overlay |
| LKA | Max steering torque overlay | ≤ 5 Nm | LKA_TrqOvrd_Nm |
| LDW | Warning onset time | ≤ 500 ms | Offset crossing to audio flag |
| BSD | Object detection latency | ≤ 300 ms | Radar inject to LED flag |
| PARK | Tone zone update rate | ≤ 100 ms | Zone change responsiveness |
| PARK | Auto-brake latency at 15cm | ≤ 200 ms | Ultrasonic to brake request |
| HHA | Hold activation latency | ≤ 300 ms | Pedal release to hold state |
| HHA | Hold duration accuracy | 0–3000 ms ±50 ms | HHA_HoldDuration_ms |

### 11.2 Gate Thresholds for Release

| Metric | Minimum Acceptable |
|---|---|
| Overall pass rate | ≥ 95% |
| P0 (safety) test pass rate | 100% |
| P1 (functional) test pass rate | ≥ 98% |
| No open DTCs post-test | Required |
| All feature states return to nominal | Required |

---

## 12. CI Integration

### 12.1 GitHub Actions Workflow

```yaml
# .github/workflows/hil_adas_suite.yml
name: ADAS HIL Regression

on:
  workflow_dispatch:
    inputs:
      build_id:
        description: 'Build ID for this test run'
        required: true
        default: 'manual'
      feature:
        description: 'Feature to test (ALL/ACC/LKA/BSD/PARK/HHA)'
        default: 'ALL'

jobs:
  hil_test:
    runs-on: [self-hosted, hil-bench-windows]   # Must run on HIL-connected Windows PC
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest pytest-html pywin32 requests

      - name: Run HIL Gate
        run: |
          python run_hil_suite.py \
            --feature ${{ github.event.inputs.feature }} \
            --build-id ${{ github.event.inputs.build_id }} \
            --min-pass-rate 95.0

      - name: Upload Test Artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: hil-reports-${{ github.event.inputs.build_id }}
          path: reports/
          retention-days: 30
```

---

## 13. Troubleshooting HIL Issues

| Issue | Symptom | Root Cause | Resolution |
|---|---|---|---|
| No CAN traffic after KL15 | Zero messages in CANoe Trace | Bad termination / wrong channel assignment | Check 120Ω on both ends; verify DBC assignment |
| ECU not booting | No messages within 2s of KL15 | Insufficient KL30 current limit | Increase power supply current limit; check harness |
| CAN messages missing signals | Signal value always 0 | DBC mismatch (byte order / bit position) | Re-export DBC from OEM tool; verify with oscilloscope |
| LKA not intervening in test | LKA_Sts stays STANDBY | Lane quality signal not set | Set `LnMrkng_QL_L/R = 3` before drift scenario |
| ACC brake request = 0 always | No brake output | Radar object message format mismatch | Check signal scaling in DBC vs ECU spec |
| HHA always fires on flat road | Incorrect gradient simulation | Incline sensor not mapped correctly | Verify `Slope_Pct` signal byte position in DBC |
| vTestStudio tests fail to connect CANoe | COM error on start | CANoe not running before vTestStudio | Launch CANoe first; wait for config load before executing |
| Python COM interface error | `win32com` exception | 32-bit vs 64-bit mismatch | Use 32-bit Python for 32-bit CANoe COM |
| JUnit XML not generated | No XML file after run | pytest exit before write | Remove `--maxfail` limit for report generation runs |
| DTC not cleared between tests | Previous test DTC bleeds in | Missing ECU reset between test cases | Call UDS `0x11 01` (ECU reset) in teardown |

---

## Appendix A — Signal Quick Reference

```
ACC_Sts encoding:  0x00=OFF  0x01=STANDBY  0x02=ACTIVE  0x03=OVERRIDE  0xFF=FAULT
LKA_Sts encoding:  0x00=OFF  0x01=READY    0x02=ACTIVE  0x03=INTERVENING
BSD_LED encoding:  0x00=OFF  0x01=SOLID    0x02=FLASHING
Park_Sts encoding: 0x00=OFF  0x01=ACTIVE   0x02=PAUSED  0x03=FAULT
HHA_Sts encoding:  0x00=OFF  0x01=READY    0x02=HOLDING 0x03=RELEASING
```

## Appendix B — Useful CANoe Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Start Measurement | F9 |
| Stop Measurement | F10 |
| Open Trace Window | Ctrl+T |
| Open Data Window | Ctrl+D |
| Run CAPL Test Unit | Ctrl+Shift+R |
| Generate Report | Ctrl+Shift+G |

---

*End of Document — HIL ADAS ECU Testing Guide v1.0*
