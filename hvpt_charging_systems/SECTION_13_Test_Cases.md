# SECTION 13 — TEST CASE LIBRARY
## Complete Test Case Suite for EV Powertrain Systems

---

## 13.1 TEST CASE FORMAT

All test cases follow this professional structure:

```
TC-[SYSTEM]-[NUMBER]: [Test Name]
Requirement: [SysRS or FSR ID]
Test Level:  [Bench / HIL / Vehicle]
ASIL:        [QM / A / B / C / D]
Priority:    [Critical / High / Medium / Low]

Preconditions:
  - [Hardware state]
  - [Software state]
  - [Tool setup]

Test Steps:
  Step N: [Action + expected immediate result]

Expected Results:
  - [Signal value / behavior / DTC state]
  - [Timing requirement]

Pass Criteria:
  PASS: [Quantified acceptance]
  FAIL: [Failure condition]

Traceability: [Requirement → Test Case → Test Result]
```

---

## 13.2 CAN NETWORK TEST CASES

```
TC-CAN-001: CAN Bus Idle Load
Priority: High | Level: Bench | ASIL: QM

Preconditions: All ECUs powered, vehicle in ignition ON (key-on)

Steps:
  1. Enable CANoe bus statistics window for all CAN channels
  2. Operate vehicle in stationary state (engine off, 12V on) for 30s
  3. Record bus utilization percentage

Expected:
  Powertrain CAN: 25–45% bus load
  Body CAN:       15–30% bus load

PASS: All bus loads within specification
FAIL: Any bus > 70% — risk of message delay

──────────────────────────────────────────────────────────────────

TC-CAN-002: Message Arbitration Priority
Priority: Critical | Level: Bench | ASIL: B

Purpose: Verify high-priority messages are not starved by low-priority messages

Preconditions: High bus load (>80%) test scenario active

Steps:
  1. Inject 60% bus load with low-priority test messages (ID > 0x600)
  2. Send BMS_Status (0x310) at configured 10ms cycle
  3. Measure actual delivery period of BMS_Status vs. configured

Expected:
  BMS_Status (ID 0x310) has priority over test messages (ID 0x700+)
  BMS_Status max period increase: ≤ 1ms when bus load = 80%

PASS: BMS_Status period ≤ 11ms even at 80% bus load
FAIL: BMS_Status delayed > 2ms due to bus load

──────────────────────────────────────────────────────────────────

TC-CAN-003: Error Frame Handling — Bus Off Recovery
Priority: Critical | Level: Bench | ASIL: C

Steps:
  1. Force dominant bit stuffing error by injecting hardware fault
     (short CAN_H to CAN_L momentarily via relay)
  2. Observe TEC/REC counters increment
  3. After Bus-Off state (TEC > 255), remove fault
  4. Measure ECU recovery time to Normal state

Expected:
  ECU enters Bus-Off after persistent error
  ECU attempts Bus-Off recovery after 128 × 11 consecutive recessive bits
  Recovery time: ≤ 1400ms (128 × 11 × 8µs at 500kbps + processing)
  
PASS: ECU recovers to Normal state, resumes CAN messages within 1.5s
FAIL: ECU stays in Bus-Off, requires power cycle

──────────────────────────────────────────────────────────────────

TC-CAN-004: CAN FD Signal Integrity
Priority: High | Level: Bench | ASIL: B

Preconditions: CAN FD bus with matched 120Ω termination at each end

Steps:
  1. Measure differential voltage on CAN FD bus with oscilloscope
  2. Measure rise/fall times at data phase bit boundary
  3. Verify eye diagram at 2 Mbit/s data phase rate

Expected:
  CAN_H – CAN_L differential voltage (recessive): 0V ± 0.2V
  CAN_H – CAN_L differential voltage (dominant): ≥ 1.5V
  Rise/fall time ≤ (0.3 × bit time) = 150ns at 2 Mbit/s

PASS: All eye diagram parameters within CAN FD specification (ISO 11898-2)
FAIL: Eye closure, ringing > 1.5× amplitude, setup/hold violations
```

---

## 13.3 BATTERY MANAGEMENT SYSTEM TEST CASES

```
TC-BMS-010: BMS State Transition — OFF to STANDBY
Priority: Critical | Level: Bench | ASIL: C

Preconditions:
  - BMS powered (12V logic supply)
  - HV battery connected
  - CAN bus active
  - Previous state: BMS_ContactorState = OFF (0)

Steps:
  1. Assert VCU_KL15 signal (ignition key-on)
  2. Monitor BMS_Status via CAN for state change
  3. Measure time from KL15 to BMS_State = STANDBY (1)

Expected:
  BMS_State transitions: OFF(0) → INIT(1) → STANDBY(2)
  Transition time (KL15 asserted → STANDBY): ≤ 500ms
  No DTC generated during normal startup

PASS: Correct state sequence, timing ≤ 500ms, no DTC
FAIL: Wrong sequence, timeout > 500ms, unexpected DTC

──────────────────────────────────────────────────────────────────

TC-BMS-011: BMS State Transition — STANDBY to ACTIVE (Precharge)
Priority: Critical | Level: Bench | ASIL: D

Preconditions: BMS in STANDBY, DC link voltage < 10V

Steps:
  1. Send VCU_Command::VCU_HV_Request = 1
  2. Monitor BMS_ContactorState via CAN
  3. Measure DC link voltage (from INV_DCLinkVoltage on CAN)
  4. Record time from request to CLOSED state

Expected:
  State sequence: STANDBY → PRECHARGE_POS → PRECHARGE → ACTIVE
  Precharge condition: V_dclink ≥ 0.95 × V_battery before CLOSE
  Maximum precharge time: 3 seconds
  
  Transition NOT allowed if V_dclink < 0.95 × V_battery at timeout
  → BMS should abort and set DTC "Precharge_Timeout"

PASS: Correct sequence, DC link ≥ 95% before main contactor closes
FAIL: Skip precharge, main contactor closes before voltage threshold

──────────────────────────────────────────────────────────────────

TC-BMS-012: Cell Overvoltage Fault Response
Priority: Critical | Level: HIL | ASIL: C

Preconditions: BMS ACTIVE state, clean fault state, HIL thermal model active

Steps:
  1. Clear DTCs: send UDS 14 FF FF FF
  2. Via HIL: inject cell voltage signal +4.28V (threshold = 4.20V + hysteresis)
  3. Monitor BMS_FaultCode bit 0 (CellOV) via CAN
  4. Monitor BMS_ContactorState
  5. Monitor DTC via: 19 02 FF

Expected:
  Fault detection within 50ms (debounce time)
  BMS_FaultCode bit 0 = 1
  BMS_ContactorState → FAULT (3) within 200ms
  DTC 0x0A0001 confirmed (bit 3 status set)
  INV_ActualTorque → 0 within 200ms (VCU commands 0 on BMS fault)

PASS: All above within timing specs
FAIL: Fault not detected, wrong DTC, contactor remains closed

──────────────────────────────────────────────────────────────────

TC-BMS-013: BMS Isolation Fault Detection
Priority: Critical | Level: HIL | ASIL: D

Steps:
  1. Set HV bus active (contactors closed)
  2. Via HIL: reduce isolation resistance to 30 kΩ (threshold = 100 Ω/V × 400V = 40 kΩ)
  3. Monitor BMS_IsolationStatus signal
  4. Monitor response time and actions

Expected:
  IMD detection time: ≤ 1 second (per spec)
  BMS_IsolationStatus = FAULT within 1.5 seconds
  BMS opens contactors within 100ms of IMD fault
  DTC 0x0D0001 (HV_Isolation_Fault) confirmed

PASS: Isolation fault detected, contactors opened within spec
FAIL: Fault undetected at 30 kΩ, contactors not opened

──────────────────────────────────────────────────────────────────

TC-BMS-014: Temperature-Based Power Derating
Priority: High | Level: HIL | ASIL: B

Preconditions: Cell temperature simulation via HIL

Steps:
  1. Set cell temperature to 25°C, record BMS_ChargePowerLimit
  2. Ramp temperature to 40°C, record power limit
  3. Ramp temperature to 50°C, record power limit
  4. Ramp temperature to 55°C, record power limit
  5. Ramp temperature to 60°C, record power limit

Expected Power Derating Table:
  T ≤ 45°C: 100% of max charge power
  T = 50°C: ≤ 80% of max
  T = 55°C: ≤ 50% of max
  T ≥ 60°C: BMS_ChargingAllowed = 0 (charging disabled)

PASS: Derating matches specification table within ±5%
FAIL: No derating observed, or derating different from specification

──────────────────────────────────────────────────────────────────

TC-BMS-015: BMS Recovery After Fault Clear
Priority: Medium | Level: Bench | ASIL: B

Steps:
  1. Inject and confirm overvoltage fault (TC-BMS-012)
  2. Remove fault condition (reduce cell voltage to nominal)
  3. Clear DTC via UDS: 14 FF FF FF
  4. Send VCU_HV_Request = 1
  5. Verify BMS can re-enter ACTIVE state

Expected:
  BMS resumes normal operation after fault clear
  Precharge sequence repeatable after fault recovery
  No DTC in fresh state

PASS: BMS fully recovers, system operational
FAIL: BMS stuck in fault state, cannot clear without power cycle
```

---

## 13.4 CHARGING TEST CASES

```
TC-CHRG-010: AC Charging — State Machine Compliance
Priority: Critical | Level: Vehicle | ASIL: B

Equipment: EVSE simulator, CP/PP measurement equipment

Steps:
  1. Set EVSE simulator: 32A available, 230VAC
  2. Plug in charging cable
  3. Measure CP voltage transitions with oscilloscope
  4. Time each state transition

Expected State Transitions:
  A (cable disconnected): CP = +12V
  B (connected, EV not ready): CP = +9V ± 1V (within 500ms of plug)
  C (EV ready to charge): CP = +6V ± 1V (within 2s of user request)
  
PASS: All CP voltage levels correct, transitions within 500ms each
FAIL: Wrong CP voltage, transitions > 2s, stuck in wrong state

──────────────────────────────────────────────────────────────────

TC-CHRG-011: DC Fast Charging — ISO 15118 Handshake
Priority: Critical | Level: Vehicle | ASIL: B

Equipment: DCFC simulator with ISO 15118-2 support, PLC protocol analyzer

Steps:
  1. Connect CCS Combo 2 cable
  2. Monitor PLC traffic with protocol analyzer
  3. Verify complete ISO 15118 message sequence
  4. Time overall connection-to-charging-start duration

Expected Sequence Completion Times:
  SLAC complete: ≤ 2 seconds
  SessionSetup: ≤ 2 seconds  
  Authorization: ≤ 5 seconds
  ChargeParameterDiscovery: ≤ 2 seconds
  CableCheck: ≤ 20 seconds (isolation check)
  PreCharge: ≤ 20 seconds (voltage matching)
  PowerDelivery (start): ≤ 1 second
  
  Total: ≤ 90 seconds from cable connection to charging

PASS: All phases complete in sequence within time limits
FAIL: Any phase failure, missing message, timeout

──────────────────────────────────────────────────────────────────

TC-CHRG-012: Charging Safety — Emergency Stop
Priority: Critical | Level: Vehicle | ASIL: D

Steps:
  1. Start active DC fast charging session (50 kW)
  2. Simulate emergency: press emergency stop at DCFC station
     (or send EmergencyShutdown message in 15118)
  3. Measure time from emergency signal to HV power off at inlet
  4. Verify contactors open

Expected:
  Power off at vehicle inlet: ≤ 500ms from emergency signal
  Vehicle DC contactors open: ≤ 200ms from DCFC power off
  No HV voltage at connector after 1 second

PASS: Power off within timing, contactors open, safe state achieved
FAIL: Charging continues after emergency, HV present at connector

──────────────────────────────────────────────────────────────────

TC-CHRG-013: Charging Interoperability — Multiple EVSE Types
Priority: High | Level: Vehicle | ASIL: QM

Precondition: Access to various EVSE types for interoperability testing

Steps (for each EVSE type):
  1. AC Level 1 (120V/12A): Connect and verify charging starts
  2. AC Level 2 (240V/32A): Connect and verify charging starts
  3. DCFC Type A — Brand 1: Connect and verify 15118 handshake
  4. DCFC Type B — Brand 2: Connect and verify 15118 handshake
  5. Measure charging power for each

Expected:
  All connection types result in successful charging
  No communication errors in 15118 log
  Power levels match EVSE capability

PASS: Successful charging on all tested EVSE types
FAIL: Any EVSE type fails to charge

──────────────────────────────────────────────────────────────────

TC-CHRG-014: Cold Weather Charging at -20°C
Priority: High | Level: Vehicle | ASIL: B

Equipment: Environmental chamber (-20°C), EVSE

Steps:
  1. Cold soak vehicle to -20°C (at least 4 hours)
  2. Attempt AC Level 2 charging
  3. Monitor BMS_HeatingActive signal
  4. Monitor initial charge current vs. full-temp charge current
  5. Record time to reach full charge current

Expected:
  BMS activates battery heater before starting charge
  Initial charge current ≤ 0.1C = ~5A for 50 kWh battery
  Battery heater active until T ≥ 10°C
  Once T ≥ 10°C: charge current increases to full available
  DTC should NOT be set during this normal cold-weather operation

PASS: Correct cold-weather charging behavior per specification
FAIL: No heating, overcharge at cold temp, unexpected DTC
```

---

## 13.5 UDS DIAGNOSTICS TEST CASES

```
TC-UDS-010: All Sessions Accessible
Priority: Critical | Level: Bench | ASIL: QM

Steps:
  For each session type:
  1. Send 10 01 (Default) → verify 50 01 response
  2. Send 10 02 (Programming) → verify 50 02 response or NRC with reason
  3. Send 10 03 (Extended) → verify 50 03 response
  4. Return to Default after each: send 10 01

Expected:
  Default (0x01): Always accessible
  Programming (0x02): Accessible with correct conditions (speed=0, KL15 on)
  Extended (0x03): Accessible after DTC cleared or at any time

PASS: Correct responses for all session types
FAIL: Session not accessible, wrong response, unexpected NRC

──────────────────────────────────────────────────────────────────

TC-UDS-011: DID Read Completeness
Priority: High | Level: Bench | ASIL: QM

Steps:
  For each specified DID in DID catalog:
  1. Enter appropriate session
  2. Send 22 [DID_H][DID_L]
  3. Verify response format and length
  4. Verify value is within physical range

DID List to Test (EV BMS):
  0xF190 — VIN (17 bytes ASCII)
  0xF18C — Serial Number
  0xF188 — SW Version  
  0xF186 — Active Session
  0xF101 — Battery SoC (0–100%)
  0xF102 — Pack Voltage (0–500V)
  0xF103 — Pack Current (-500–500A)
  0xF104 — Max Cell Temp (-40–125°C)
  0xF105 — Fault Code

PASS: All DIDs respond, correct format, values in range
FAIL: DID missing, wrong length, value out of range

──────────────────────────────────────────────────────────────────

TC-UDS-012: DTC Fault Memory Lifecycle
Priority: Critical | Level: HIL | ASIL: B

Steps:
  1. Clear DTCs: 14 FF FF FF, verify clean state
  2. Inject fault (e.g., cell overvoltage via HIL)
  3. Read DTC (19 02 FF) — verify pending DTC present
  4. Run through 2 more drive cycles with fault active
  5. Read DTC — verify confirmed DTC
  6. Remove fault condition
  7. Run drive cycle without fault
  8. Read DTC — verify testFailedThisOpCycle cleared
  9. After 3 clean drive cycles: DTC should age out (if OEM implements aging)

Expected DTC Status Progression:
  After 1st detection:  pendingDTC = 1, testFailed = 1
  After confirmation:   confirmedDTC = 1
  After fault removed:  testFailed = 0, confirmedDTC still = 1
  After aging:          DTC may be cleared automatically (OEM-specific)

PASS: DTC lifecycle matches ISO 14229 specification
FAIL: DTC not setting, wrong status byte, not confirming

──────────────────────────────────────────────────────────────────

TC-UDS-013: Security Access Lockout
Priority: Critical | Level: Bench | ASIL: B

Steps:
  1. Enter Extended session: 10 03
  2. Request seed: 27 01 → receive seed
  3. Send WRONG key: 27 02 FF FF FF FF
  4. Repeat step 3 three times total
  5. After 3rd wrong attempt: verify lockout

Expected:
  After 3rd wrong key: NRC 0x36 (ExceededNumberOfAttempts)
  Subsequent RequestSeed: NRC 0x37 (RequiredTimeDelayNotExpired)
  After lockout delay (typically 10 minutes): seed accessible again

PASS: Lockout triggers after 3 attempts, delay enforced
FAIL: Access granted with wrong key, no lockout after 3 attempts

──────────────────────────────────────────────────────────────────

TC-UDS-014: ECU Reset and Recovery
Priority: High | Level: Bench | ASIL: B

Steps:
  1. Read DID 0xF101 (SoC) and note value
  2. Send 11 01 (HardReset)
  3. Wait 5 seconds
  4. Attempt DiagnosticSessionControl: 10 01
  5. Read DID 0xF101 again

Expected:
  ECU restarts (no CAN messages for 2-3 seconds during reset)
  ECU recovers to Default session
  SoC value preserved (from NVM) ± 2%
  No unexpected DTC generated by reset itself

PASS: ECU recovers, session accessible, SoC retained
FAIL: ECU does not recover, session not accessible, SoC lost
```

---

## 13.6 VEHICLE STATE TEST CASES

```
TC-VST-001: Vehicle Power States
Priority: Critical | Level: Vehicle | ASIL: C

States:
  State 0: OFF — all ECUs powered down
  State 1: ACC — accessories only (radio, lights)
  State 2: IGNITION ON — all ECUs active, HV not enabled
  State 3: READY — HV enabled, ready to drive
  State 4: DRIVE — vehicle moving
  State 5: CHARGING — AC or DC charging active

Steps (state walk-through):
  1. Start from OFF, apply 12V power
  2. Key to ACC position, verify ACC devices power on
  3. Key to IGN ON, verify all ECUs start sending CAN messages
  4. Verify no HV bus (BMS_ContactorState = OPEN)
  5. Press READY (brake + power button), verify HV enables
  6. Verify READY state: VCU_State = READY
  7. Release brake slightly: verify propulsion available
  8. Apply brake + park: verify DRIVE → ACC state

Expected Transitions:
  Each state transition within 2 seconds
  Correct CAN signals per state (per state machine spec)
  No DTC during normal transitions

──────────────────────────────────────────────────────────────────

TC-VST-002: Emergency Stop — Drive
Priority: Critical | Level: Vehicle | ASIL: D

Steps:
  1. Vehicle moving at 60 km/h
  2. Simulate: BMS detects critical fault (thermal runaway trigger)
  3. Measure: time from fault trigger to torque = 0

Expected:
  Torque commanded to 0 within 200ms
  Vehicle decelerates (friction brakes available)
  Hazard lights activated
  Warning message displayed to driver
  HV contactors open within 500ms

PASS: Safe shutdown within specified timing
FAIL: Continued torque after critical fault
```

---

## 13.7 ENVIRONMENTAL TEST CASES

```
TC-ENV-001: Cold Start at -40°C
Priority: Critical | Level: Vehicle | ASIL: B

Preconditions: 
  - Vehicle soaked at -40°C for minimum 4 hours
  - 12V battery at full charge

Steps:
  1. Key-on at -40°C
  2. Monitor all ECU startup times
  3. Monitor BMS communication start
  4. Attempt READY state

Expected:
  All ECUs start within 5 seconds (longer allowed at extreme cold)
  BMS_SoC valid within 10 seconds
  No cold-start DTC (unless fault genuinely present)

TC-ENV-002: High Temperature at +85°C
Priority: High | Level: Vehicle/HIL | ASIL: B

Preconditions: Vehicle or component at 85°C (thermal chamber)

Steps:
  1. Verify all ECUs operational at 85°C
  2. Run charging session at 85°C
  3. Monitor all thermal protection behaviors

Expected:
  Charging derated at high ambient temperature
  No ECU failure at 85°C
  BMS_CoolingFan active
  All CAN signals within specification at 85°C
```

---

## 13.8 TEST CASE TRACEABILITY MATRIX

```
TRACEABILITY MATRIX OVERVIEW:
══════════════════════════════════════════════════════════════
Requirement ID      │ Test Cases          │ Coverage
────────────────────┼─────────────────────┼─────────────────
SysRS-BMS-CAN-001   │ TC-BMS-001          │ ✓ Full
SysRS-BMS-SOC-001   │ TC-BMS-002          │ ✓ Full
SysRS-BMS-FAULT-001 │ TC-BMS-003, 012     │ ✓ Full
SysRS-BMS-PRECHG-001│ TC-BMS-004, 011     │ ✓ Full
SysRS-BMS-THERM-002 │ TC-BMS-005, 014     │ ✓ Full
SysRS-INV-TORQ-001  │ TC-INV-001          │ ✓ Full
SysRS-INV-REGEN-001 │ TC-INV-002          │ ✓ Full
SysRS-OBC-CP-001    │ TC-OBC-001, CHRG-010│ ✓ Full
SysRS-OBC-CHARGE-001│ TC-OBC-002          │ ✓ Full
SysRS-OBC-SAFE-001  │ TC-OBC-003, CHRG-012│ ✓ Full
SysRS-CHARGE-DC-001 │ TC-CHRG-011         │ ✓ Full
FSR-BMS-001         │ TC-BMS-012 (ASIL-D) │ ✓ Full
FSR-BMS-002         │ TC-BMS-013 (ASIL-D) │ ✓ Full
SysRS-BMS-DIAG-001  │ TC-UDS-010 through  │ ✓ Full
                    │ TC-UDS-014          │
```

---

## SECTION 13 SUMMARY

Test library contains:

| Category | Count | Priority Level |
|----------|-------|---------------|
| CAN Network | 4 | Critical/High |
| BMS | 6 | Critical |
| Charging | 5 | Critical/High |
| UDS Diagnostics | 5 | Critical/High |
| Vehicle State | 2 | Critical |
| Environmental | 2 | High |
| **Total** | **24** | |

For production release, complete test set should include 300+ test cases covering all requirements with 100% RTM coverage.

---

*Next: Section 14 — JIRA & Issue Management*
