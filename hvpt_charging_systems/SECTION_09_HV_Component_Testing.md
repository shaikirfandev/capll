# SECTION 9 — HV COMPONENT TESTING
## Battery Pack, Inverter, Motor, OBC — Bench to Vehicle Validation

---

## 9.1 TESTING STRATEGY OVERVIEW

```
HV COMPONENT TEST PYRAMID:
══════════════════════════════════════════════════════════════
                    ▲
                   /│\
                  / │ \
                 /  │  \    VEHICLE VALIDATION
                /   │   \   (full vehicle, real roads, charging)
               /    │    \
              /─────────────\
             /               \  SYSTEM INTEGRATION (HIL)
            /                 \  (hardware-in-loop, all ECUs)
           /───────────────────\
          /                     \  COMPONENT INTEGRATION BENCH
         /                       \  (2+ ECUs on test bench)
        /─────────────────────────\
       /                           \  COMPONENT BENCH TEST
      /                             \  (single ECU, stimuli)
     /───────────────────────────────\
    /                                 \  SIL / Model Testing
   /                                   \  (software in loop)
  /─────────────────────────────────────\

TEST LEVEL COVERAGE:
Level               │ Tools              │ Typical coverage
────────────────────┼────────────────────┼─────────────────
SIL                 │ MATLAB/Simulink    │ Algorithm/model validation
Component Bench     │ CANoe, bench rig   │ ECU functional testing
Integration Bench   │ CANoe + HIL        │ Interface testing
HIL                 │ dSPACE, ETAS LABCAR│ Real-time testing
Vehicle Validation  │ CANalyzer, loggers │ End-to-end, ADAS, charging
```

---

## 9.2 BATTERY MANAGEMENT SYSTEM (BMS) TESTING

### 9.2.1 BMS Test Categories

```
BMS VALIDATION TEST MATRIX:
────────────────────────────────────────────────────────────────────
Category                │ Tests
────────────────────────┼───────────────────────────────────────────
CAN Communication       │ Period, data integrity, encoding, MUX
State Machine           │ Power state transitions, fault handling
SoC Estimation          │ Accuracy vs reference, Coulomb counting
SoH Monitoring          │ Capacity fade tracking
Cell Balancing          │ Passive balancing operation
Fault Detection         │ OV/UV/OT/UT/isolation/interlock detection
Thermal Management      │ Cooling request behavior
Charging Interface      │ VCU handshake, OBC coordination
Recovery Behavior       │ Post-fault recovery, wakeup
Environmental           │ -40°C / +85°C operation
────────────────────────────────────────────────────────────────────
```

### 9.2.2 Complete BMS Test Cases

```
TC-BMS-001: CAN Message Transmission — BMS_Status
Requirement: SysRS-BMS-CAN-001
Precondition: 
  - BMS powered (12V logic power)
  - HV battery connected
  - CAN bus loaded, CANoe connected

Step 1: Configure CANoe trace with BMS_Status (0x310) filter
Step 2: Power on BMS (key-on sequence)
Step 3: Measure message period using trace window Statistics

Expected Results:
  - BMS_Status appears within 2 seconds of power-on
  - Cyclic period: 10ms ± 1ms
  - No message loss > 5ms gap
  - BMS_SoC: 0–100%, resolution 0.5%
  - BMS_PackVoltage: 280–420V range

Pass/Fail Criteria:
  PASS: Period mean = 10ms ±1ms, no gaps >15ms, values in range
  FAIL: Missing messages, wrong period, values out of range

──────────────────────────────────────────────────────────────────

TC-BMS-002: SoC Estimation Accuracy
Requirement: SysRS-BMS-SOC-001 (SoC accuracy ±3% over lifecycle)
Precondition:
  - Reference Coulomb counter calibrated
  - Battery fully charged (SoC=100% reference)

Step 1: Record BMS_SoC at SoC=100%
Step 2: Apply 50A discharge load for 30 minutes
Step 3: Calculate reference SoC: SoC_ref = 100% - (I×t / Capacity)
Step 4: Compare BMS_SoC to SoC_ref at t=30min

Expected Results:
  - |BMS_SoC - SoC_ref| ≤ 3.0%
  
Pass/Fail Criteria:
  PASS: BMS SoC within ±3% of reference Coulomb-counted SoC
  FAIL: Deviation > 3%

──────────────────────────────────────────────────────────────────

TC-BMS-003: Overvoltage Fault Detection
Requirement: SysRS-BMS-FAULT-001
Precondition:
  - Extended session, clean fault state
  - Fault injection capability available

Step 1: Clear DTCs: 14 FF FF FF
Step 2: Inject cell overvoltage > 4.25V (threshold per spec = 4.20V)
Step 3: Wait 100ms (fault debounce)
Step 4: Read BMS_FaultCode from CAN: 22 F1 05
Step 5: Read DTC: 19 02 08

Expected Results:
  - BMS_FaultCode bit 0 (CellOvervoltage) = 1
  - DTC 0x0A0001 present with confirmed bit set
  - BMS transitions to FAULT state (BMS_ContactorState = 3)
  - Main contactors open within 200ms

Pass/Fail Criteria:
  PASS: All above conditions met within 200ms of fault injection
  FAIL: Fault not detected, wrong DTC, contactors remain closed

──────────────────────────────────────────────────────────────────

TC-BMS-004: Precharge Sequence
Requirement: SysRS-BMS-PRECHG-001
Precondition:
  - HV battery charged (SoC > 20%)
  - DC link capacitors discharged (V_dclink < 10V)

Step 1: Send VCU_HV_Request = 1 (request HV bus)
Step 2: Monitor BMS_ContactorState via CAN
Step 3: Monitor DC link voltage (can be read via Inverter CAN signal)
Step 4: Measure precharge duration (time PRECHARGE → CLOSED)

Expected Results:
  Sequence observed:
    BMS_ContactorState: 0 (OPEN) → 1 (PRECHARGE) → 2 (CLOSED)
  Precharge criteria:
    DC link voltage reaches ≥ 95% of battery voltage
    OR timeout = 3 seconds (whichever first)
  Transition PRECHARGE → CLOSED only when V_dclink ≥ 0.95 × V_battery

Pass/Fail Criteria:
  PASS: Correct state sequence, DC link ≥ 95% before main positive closes
  FAIL: Skip precharge, wrong sequence, close before voltage reaches 95%

──────────────────────────────────────────────────────────────────

TC-BMS-005: Temperature Derating
Requirement: SysRS-BMS-THERM-002
Precondition: Temperature conditioning equipment available

Step 1: Condition battery to 55°C
Step 2: Monitor BMS_ChargePowerLimit and BMS_DischargePowerLimit
Step 3: Compare to 25°C baseline values

Expected Results at 55°C:
  - ChargePowerLimit reduced to ≤ 50% of 25°C value
  - DischargePowerLimit reduced to ≤ 70% of 25°C value
  - BMS_ChargingAllowed may be 0 (charging disabled) above 50°C

Pass/Fail Criteria:
  PASS: Power limits derate as per temperature derating table
  FAIL: No derating, limits exceed specification at high temp
```

---

## 9.3 INVERTER / MOTOR CONTROLLER TESTING

### 9.3.1 Inverter Test Categories

```
INVERTER VALIDATION TEST MATRIX:
────────────────────────────────────────────────────────────────────
Category                │ Tests
────────────────────────┼───────────────────────────────────────────
CAN Communication       │ INV_Status period, signal encoding
Torque Control          │ Torque accuracy, response time
Speed Feedback          │ Speed measurement accuracy
Regenerative Braking    │ Regen torque, HV regeneration
Fault Handling          │ Gate driver fault, IGBT OT, desaturation
HV Enable Sequence      │ HV enable, ready state
FOC Algorithm           │ Id/Iq control, efficiency
Thermal Protection      │ Inverter derating, OT shutdown
────────────────────────────────────────────────────────────────────
```

### 9.3.2 Inverter Test Cases

```
TC-INV-001: Torque Response Time
Requirement: SysRS-INV-TORQ-001 (torque command → response ≤ 10ms)

Precondition: Motor spinning at 1000 RPM, 0 Nm torque command

Step 1: Set up CANoe Graphics window: 
        X-axis: time (10ms scale)
        Y-axis 1: VCU_TorqueRequest (green)
        Y-axis 2: INV_ActualTorque (red)
Step 2: Issue torque step from 0 Nm → 100 Nm via VCU_Command
Step 3: Measure Δt from VCU_TorqueRequest change to INV_ActualTorque = 100 Nm
Step 4: Repeat at 5 different speed points: 500, 1000, 2000, 4000, 6000 RPM

Expected Results:
  - Torque response time ≤ 10ms at all speed points
  - Torque ripple ≤ ±5 Nm during steady state
  - No torque overshoot > 110% of commanded value

──────────────────────────────────────────────────────────────────

TC-INV-002: Regenerative Braking Validation
Requirement: SysRS-INV-REGEN-001

Precondition: Motor spinning forward at 3000 RPM (driven by power source)

Step 1: Command negative torque (e.g., -80 Nm) via VCU_TorqueRequest
Step 2: Monitor:
        INV_ActualTorque (should show negative = braking)
        INV_DCLinkVoltage (should increase slightly as energy returned)
        BMS_PackCurrent (should show charging current)

Expected Results:
  - INV_ActualTorque → -80 Nm within 10ms
  - BMS_PackCurrent shows negative current (charging)
  - BMS_PackCurrent within BMS_ChargePowerLimit
  - No DTC set during regen operation

──────────────────────────────────────────────────────────────────

TC-INV-003: IGBT Overtemperature Protection
Requirement: SysRS-INV-THERM-001

Precondition: Thermal simulation capability OR temperature conditioning

Step 1: Force IGBT junction temperature > 150°C (threshold per spec)
Step 2: Monitor INV_Status::INV_FaultCode
Step 3: Monitor torque derating behavior
Step 4: Verify DTC set

Expected Results:
  - Torque limit progressively derated starting at 120°C
  - Full torque disable at 150°C
  - DTC 0x0C0001 (IGBT_OT) confirmed
  - Torque = 0 within 100ms of 150°C threshold

──────────────────────────────────────────────────────────────────

TC-INV-004: HV Enable Sequence
Requirement: SysRS-INV-HV-001

Precondition: BMS ready, DC link voltage = battery voltage (precharge complete)

Step 1: Send VCU_Command::VCU_HV_Enable = 1
Step 2: Monitor INV_Status::INV_ReadyState
Step 3: Measure time from VCU_HV_Enable → INV_ReadyState = READY

Expected Results:
  - Inverter transitions: INIT → PREOP → READY within 500ms
  - INV_DCLinkVoltage stabilizes to battery voltage
  - No error codes during normal enable sequence
```

---

## 9.4 ONBOARD CHARGER (OBC) TESTING

### 9.4.1 OBC Test Categories

```
OBC VALIDATION TEST MATRIX:
────────────────────────────────────────────────────────────────────
Category                  │ Tests
──────────────────────────┼─────────────────────────────────────────
AC Input Recognition      │ Pilot signal detection, EVSE handshake
CP Signal Validation      │ J1772 pilot duty cycle / voltage levels
Charging Mode Selection   │ Mode 1/2/3 recognition
AC/DC Conversion          │ Power factor, efficiency, THD
CC/CV Algorithm           │ Constant current phase, CV phase
Thermal Management        │ OBC temperature monitoring, derating
Fault Handling            │ OV, OC, OT, insulation, EVSE error
CAN Integration           │ OBC_Status message, VCU command interface
────────────────────────────────────────────────────────────────────
```

### 9.4.2 OBC Test Cases

```
TC-OBC-001: AC Pilot Signal Detection (J1772 / IEC 62196)
Requirement: SysRS-OBC-CP-001

Precondition: EVSE simulator connected to OBC AC inlet

Step 1: Configure EVSE simulator with:
        - CP PWM frequency: 1 kHz
        - Duty cycle: 16% (= 10A available per J1772)
        - Pilot voltage: +12V/-12V
Step 2: Monitor OBC_Status::OBC_EVSECurrentLimit via CAN
Step 3: Verify OBC decoded EVSE available current correctly

Expected Results:
  - OBC detects pilot signal within 500ms of EVSE connection
  - OBC_EVSECurrentLimit = 10A (decoded from 16% duty cycle)
  - CP duty cycle formula: Duty% = (Available Amps / 0.6) for 6–51A range
  
CP DUTY CYCLE TABLE:
  10% = not available
  16% = 10A
  25% = 16A
  50% = 32A
  80% = 48A
  96% = 80A (maximum)

──────────────────────────────────────────────────────────────────

TC-OBC-002: CC/CV Charging Algorithm Verification
Requirement: SysRS-OBC-CHARGE-001

Precondition: Battery SoC = 20%, EVSE providing 32A / 230VAC

Step 1: Start charging
Step 2: Monitor:
        OBC_ChargingCurrent (should be at maximum = EVSE limit)
        OBC_ChargingVoltage (cell voltage × series cells)
        BMS_SoC (should increase)
        BMS_PackCurrent (charging current into battery)
Step 3: Monitor transition from CC → CV phase
        (occurs when cell voltage reaches upper voltage limit)
Step 4: Measure total time to reach 80% SoC

Expected Results CC Phase:
  - OBC_ChargingCurrent = min(OBC_MaxCurrent, BMS_ChargePowerLimit / Vbatt)
  - Charging power ≈ constant
  - BMS_SoC increases linearly in CC phase

Expected Results CV Phase:
  - OBC_ChargingVoltage = 4.15V × cells (float voltage)
  - OBC_ChargingCurrent decreases as SoC increases
  - Taper current terminates when I < 0.05C rate

──────────────────────────────────────────────────────────────────

TC-OBC-003: OBC Safety — Loss of Pilot Signal
Requirement: SysRS-OBC-SAFE-001

Precondition: Active charging session at 7.2 kW

Step 1: Monitor OBC_Status::OBC_ChargingPhase = CHARGING
Step 2: Remove EVSE pilot signal (disconnect CP line)
Step 3: Monitor time to OBC_ChargingPhase = FAULT or STOPPED

Expected Results:
  - OBC detects loss of pilot within 200ms
  - OBC terminates charging within 500ms
  - DTC set: 0x0B0003 (CP_Signal_Lost)
  - No HV voltage on vehicle inlet after OBC stop

──────────────────────────────────────────────────────────────────

TC-OBC-004: OBC CAN Communication Period
Requirement: SysRS-OBC-CAN-001

Precondition: OBC powered, CAN bus active

Step 1: Capture OBC_Status (0x620) on CAN trace
Step 2: Measure period statistics over 30 seconds

Expected Results:
  - OBC_Status period: 100ms ± 5ms (nominal charging state)
  - OBC_Status period: 1000ms ± 50ms (standby/idle state)
  - No message loss > 500ms in charging state
```

---

## 9.5 DC-DC CONVERTER TESTING

```
DC-DC CONVERTER TEST CASES:
────────────────────────────────────────────────────────────────────

TC-DCDC-001: 12V Regulation Accuracy
Requirement: SysRS-DCDC-REG-001

Precondition: HV bus active, 12V load = variable (0–100A)

Step 1: Measure 12V output voltage at 0A load
Step 2: Measure 12V output voltage at 50A load  
Step 3: Measure 12V output voltage at 100A load (full load)
Step 4: Read DCDC_Status::DCDC_LVOutputVoltage from CAN

Expected Results:
  - 12V output: 13.5V ± 0.3V (14.5V with battery conditioning)
  - Voltage regulation: ±2% from no-load to full-load
  - CAN signal matches measured voltage ± 0.2V

TC-DCDC-002: HV-to-LV Efficiency
Requirement: SysRS-DCDC-EFF-001

Step 1: Measure HV input power: P_HV = V_HV × I_HV
Step 2: Measure 12V output power: P_12V = V_12V × I_12V
Step 3: Calculate efficiency: η = P_12V / P_HV × 100%

Expected Results:
  - η ≥ 90% at full load (100A, 13.5V = 1350W)
  - η ≥ 85% at 50% load

TC-DCDC-003: CAN Period and Signal Integrity
Precondition: DCDC powered, CAN monitoring active

Expected: DCDC_Status (0x630) at 100ms ± 5ms, all signals in valid range
```

---

## 9.6 POWER DISTRIBUTION UNIT (PDU) TESTING

```
PDU TEST CASES:
────────────────────────────────────────────────────────────────────

TC-PDU-001: HV Interlock Loop Integrity
Requirement: SysRS-PDU-SAFETY-001

PDU INTERLOCK ARCHITECTURE:
  VCU ──HVIL─→ BMS ──HVIL─→ Inverter ──HVIL─→ OBC ──HVIL─→ Battery Pack
  Each connector break opens the interlock loop → HV shutdown

Step 1: Verify HVIL loop intact: PDU_Status::PDU_InterlockStatus = OK
Step 2: Disconnect one HV connector (simulate fault)
Step 3: Monitor PDU_Status::PDU_InterlockStatus
Step 4: Verify HV shutdown response

Expected Results:
  - HVIL break detected within 50ms
  - HV contactors open within 100ms of HVIL break
  - DTC 0x0D0001 (HV_Interlock_Break) set with confirmed status

TC-PDU-002: HV Connector Status Monitoring
Precondition: All HV connectors properly seated

Step 1: Monitor PDU_Status::PDU_HighSideCurrent and PDU_LowSideCurrent
Step 2: Verify currents match within 2% (plausibility check)
Step 3: Force 5% current mismatch via current source
Step 4: Verify fault detection

Expected: Current mismatch fault detected, DTC set within 200ms
```

---

## 9.7 HIL TEST ENVIRONMENT SETUP

```
HIL SETUP FOR EV POWERTRAIN TESTING:
══════════════════════════════════════════════════════════════

HIL TEST BENCH HARDWARE:
  ┌─────────────────────────────────────────────────────────┐
  │                   dSPACE HIL SYSTEM                      │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
  │  │ MicroAutoBox │  │  DS1007 CPU  │  │ DS4302 CAN   │  │
  │  │  (I/O)       │  │  (model)     │  │  Interface   │  │
  │  └──────────────┘  └──────────────┘  └──────────────┘  │
  └─────────────────────────────────────────────────────────┘
           │                                      │
     PWM outputs                          CAN channels
     Analog I/O                           (4× CAN buses)
     Digital I/O                          
           │                                      │
  ┌────────┴────────┐                    ┌────────┴──────────┐
  │  Real ECUs      │                    │  Vector Hardware  │
  │  BMS, VCU, MCU  │                    │  VN1640 CAN/FD    │
  │  OBC, DCDC      │                    │  CANoe on PC      │
  └─────────────────┘                    └───────────────────┘

MODELS RUNNING IN REAL-TIME:
  - Battery plant model (cell voltage, temperature, current)
  - Motor/mechanical load model (inertia, friction)
  - EVSE simulator model (pilot signal, power delivery)
  - Thermal model (ambient, coolant temperature)

SIGNAL INJECTION POINTS:
  Analog: Cell voltage simulation (ADC inputs to BMS)
  PWM:    Motor resolver/encoder simulation
  CAN:    Virtual ECU messages (restbus)
  Digital: Interlock, contactor feedback signals

HIL TEST EXECUTION FLOW:
  1. Load test case script (CAPL or Python)
  2. Initialize models to test preconditions
  3. Execute test steps (model stimuli + CAN signals)
  4. Monitor response via CAN trace + model outputs
  5. Evaluate pass/fail criteria
  6. Log results to database
  7. Generate automated test report
```

---

## 9.8 REGRESSION TEST FRAMEWORK

```python
# Run full regression suite
# Usage: python run_regression.py --target BMS --environment HIL

import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path

REGRESSION_SUITES = {
    'BMS': [
        'tests/battery/test_bms_communication.py',
        'tests/battery/test_bms_faults.py',
        'tests/battery/test_bms_soc.py',
    ],
    'INV': [
        'tests/inverter/test_inv_torque.py',
        'tests/inverter/test_inv_faults.py',
    ],
    'OBC': [
        'tests/charging/test_obc_ac.py',
        'tests/charging/test_obc_safety.py',
    ],
    'UDS': [
        'tests/uds/test_dtc_validation.py',
        'tests/uds/test_session_management.py',
    ]
}

def run_regression(target: str, environment: str):
    """Run regression suite and generate report."""
    test_files = REGRESSION_SUITES.get(target, [])
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"reports/regression_{target}_{timestamp}.html"
    
    cmd = [
        'python', '-m', 'pytest',
        *test_files,
        f'--html={report_path}',
        '--self-contained-html',
        f'--env={environment}',
        '-v',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Regression complete: {result.returncode}")
    print(f"Report: {report_path}")
    return result.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['BMS', 'INV', 'OBC', 'UDS', 'ALL'])
    parser.add_argument('--environment', choices=['bench', 'HIL', 'vehicle'])
    args = parser.parse_args()
    
    if args.target == 'ALL':
        for target in REGRESSION_SUITES:
            run_regression(target, args.environment)
    else:
        run_regression(args.target, args.environment)
```

---

## SECTION 9 SUMMARY

| Component | Key Validation Areas | Critical Tests |
|-----------|---------------------|----------------|
| BMS | CAN, SoC accuracy, fault detection, precharge | TC-BMS-003 (OV fault), TC-BMS-004 (precharge) |
| Inverter | Torque response, regen braking, thermal protection | TC-INV-001 (<10ms), TC-INV-002 (regen) |
| OBC | CP pilot, CC/CV algorithm, EVSE loss detection | TC-OBC-002 (CC/CV), TC-OBC-003 (safety) |
| DC-DC | Voltage regulation, efficiency, CAN reporting | TC-DCDC-001 (regulation) |
| PDU | HVIL integrity, current plausibility | TC-PDU-001 (interlock) |

Tools: CANoe (primary), dSPACE HIL, Python pytest, CANalyzer (debug)

---

*Next: Section 10 — Charging System Validation*
