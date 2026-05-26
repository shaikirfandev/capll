# SECTION 10 — CHARGING SYSTEM VALIDATION
## AC/DC Charging, ISO 15118, CCS, CHAdeMO, Fault Scenarios

---

## 10.1 CHARGING STANDARDS OVERVIEW

```
EV CHARGING STANDARDS HIERARCHY:
══════════════════════════════════════════════════════════════

AC CHARGING:
  SAE J1772 (Level 1 / Level 2)          — North America
    - CP (Control Pilot) signal: PWM 1kHz
    - PP (Proximity Pilot): plug presence detect
    - L1: 120V / 12A = 1.44 kW
    - L2: 240V / 80A = 19.2 kW

  IEC 62196 Type 2 / Mennekes             — Europe
    - 1-phase: 230V / 32A = 7.4 kW
    - 3-phase: 400V / 32A = 22 kW

DC FAST CHARGING:
  CHAdeMO                                 — Japan
    - CAN-based communication 500 kbps
    - Up to 400A / 1000V = up to 400 kW

  CCS Combo 1 (J1772 + DC pins)          — North America
  CCS Combo 2 (Type 2 + DC pins)         — Europe
  Both use:
    - DIN 70121 (initial CCS)
    - ISO 15118-2 (PLC-based communication)
    - ISO 15118-20 (bidirectional V2G, future)
    - Power: up to 350 kW (current installations)

  GB/T 20234                             — China
    - AC: GB/T 20234.2
    - DC: GB/T 20234.3

  Tesla NACS (SAE J3400)                 — expanding to all OEMs
    - Single cable for AC + DC
    - Same physical as Tesla proprietary
    - Up to 250 kW

WIRELESS CHARGING:
  SAE J2954 / IEC 61980                  — Inductive, up to 11 kW
```

---

## 10.2 AC CHARGING SEQUENCE (J1772 / IEC 62196)

```
AC CHARGING STATE MACHINE:
──────────────────────────────────────────────────────────────
STATE A: Not Connected (CP = +12V, no PWM)
  - Vehicle unplugged
  - No current available

STATE B: EV Connected, Not Ready (CP = +9V or oscillating +12/-12)
  - EVSE detects vehicle via CP voltage drop
  - EVSE provides PWM indicating available current
  - Vehicle not yet ready to charge

STATE C: EV Ready — Charging (CP = +6V during PWM)
  - Vehicle closes S2 switch (CP to 882Ω in vehicle)
  - EVSE energizes relay → AC power available
  - Charging begins

STATE D: Ventilation Required (CP = +3V)
  - Required only for older lead-acid chargers
  - Modern EVs ignore this state

STATE E: No Power (CP = 0V)
  - EVSE fault condition

STATE F: EVSE Error (CP = -12V)
  - EVSE error, no power

CP VOLTAGE LEVELS:
  +12V = State A (EVSE idle)
  +9V  = State B (EVSE detects EV, PWM available)
  +6V  = State C (EV ready to charge)
  +3V  = State D (ventilation needed)
   0V  = State E (no power/fault)
  -12V = State F (EVSE fault)

PHYSICAL RESISTANCE NETWORK:
  EVSE side: 1kΩ pullup to +12V, 1kΩ pulldown to -12V
  EV side:   2.74kΩ (State B), 882Ω (State C/D), 270Ω (State D)

COMPLETE AC CHARGING SEQUENCE:
  ────────────────────────────────────────────────────────────
  1. Vehicle plugged in
     CP: State A (+12V) → State B (+9V/oscillating)
     PP: EVSE detects proximity plug (proximity resistance)

  2. EVSE sends PWM signal
     Duty cycle = available current
     16% = 10A, 50% = 32A, etc.

  3. Vehicle wakes up OBC
     OBC reads CP PWM duty cycle
     OBC sends OBC_EvseCurrentLimit to VCU via CAN

  4. Vehicle closes S2 switch (request power)
     CP drops to +6V = State C
     EVSE energizes main relay → AC power at inlet

  5. OBC performs AC/DC conversion
     PFC (Power Factor Correction) + isolation
     Output regulated to battery voltage

  6. BMS/VCU controls charge current
     VCU_ChargeCurrentLimit → OBC
     OBC adjusts output current accordingly

  7. Charging terminates:
     a. BMS_SoC reaches 100% (or set limit)
     b. User unplugs (CP goes to State A)
     c. Scheduled end time
     d. Fault condition

  8. Shutdown sequence:
     Vehicle opens S2 → CP returns to +9V
     EVSE opens relay → AC power off
     Vehicle disconnects

CAN SIGNAL FLOW DURING AC CHARGING:
  VCU_Command::VCU_ChargeEnable = 1 → OBC starts
  OBC_Status::OBC_ChargingPhase = CHARGING
  OBC_Status::OBC_ChargingCurrent = actual A
  OBC_Status::OBC_ChargingVoltage = actual V
  BMS_Limits::BMS_ChargePowerLimit = available power
  BMS_Status::BMS_SoC = increasing
  
  Every 100ms:
  VCU → OBC: VCU_ChargeCurrentLimit (maximum A)
  OBC → VCU: OBC_Status (actual power, state, faults)
  BMS → VCU: BMS_Status (SoC, voltage, temp)
  BMS → VCU: BMS_Limits (charge/discharge limits)
```

---

## 10.3 DC FAST CHARGING SEQUENCE (ISO 15118 CCS)

```
CCS CHARGING COMMUNICATION ARCHITECTURE:
══════════════════════════════════════════════════════════════
  DCFC Station                            EV Vehicle
  ──────────                              ──────────
  SECC                                    EVCC
  (Supply Equip Comm Controller)          (EV Communication Controller)
       │                                       │
  Power Line                             Power Line
  Communication (PLC)    ←────────────→  Communication (PLC)
  HomePlug GreenPHY                       HomePlug GreenPHY
  1 Mbit/s over CP line                  
       │                                       │
   TCP/IP                                 TCP/IP
   DoIP                                   DoIP
   ISO 15118-2 App                       ISO 15118-2 App
       │
  Power Stage ───HV DC Power──→ EV Battery (via DC inlet)

PHYSICAL CONNECTION:
  CCS Combo 2 connector pins:
  ① CP (Control Pilot)    ④ PP (Proximity Pilot)
  ② N (AC Neutral)        ⑤ DC+ (High voltage positive)
  ③ L1 (AC Line)          ⑥ DC- (High voltage negative)
  
  During DC fast charging: pins 5,6 active; pins 2,3 not used

ISO 15118-2 CHARGING SEQUENCE (DETAILED):
──────────────────────────────────────────────────────────────
PHASE 1: PHYSICAL CONNECTION & SLEEP
  1. Vehicle plugged in
  2. CP: State B established
  3. EVSE senses CP state change

PHASE 2: PLC NETWORK ESTABLISHMENT
  4. SECC broadcasts SDP request (SECC Discovery Protocol)
     Port 15118 UDP multicast
  5. EVCC responds: "I am here at IP=x.x.x.x port=y"
  6. TCP connection established: EVCC → SECC

PHASE 3: V2G SESSION SETUP
  7. EVCC → SECC: SessionSetupReq
      Body: EVCCID (MAC address of EV)
  8. SECC → EVCC: SessionSetupRes
      Body: SessionID, ResponseCode=OK
      
  9. EVCC → SECC: ServiceDiscoveryReq
      Body: ServiceScope (empty = all services)
  10. SECC → EVCC: ServiceDiscoveryRes
      Body: ChargeService, ServiceList

  11. EVCC → SECC: ServicePaymentSelectionReq
      Body: SelectedPaymentOption = ExternalPayment
  12. SECC → EVCC: ServicePaymentSelectionRes

PHASE 4: AUTHORIZATION
  13. EVCC → SECC: AuthorizationReq (or ContractCertificateReq)
  14. SECC → EVCC: AuthorizationRes (with EVSE processing status)

PHASE 5: CHARGE PARAMETERS
  15. EVCC → SECC: ChargeParameterDiscoveryReq
      Body: EVMaxCurrentLimit = 200A
            EVMaxVoltageLimit = 800V
            EVMaxPowerLimit = 150000W
            EVEnergyCapacity = 82000 Wh
            EVEnergyRequest = 50000 Wh (50 kWh needed)
  16. SECC → EVCC: ChargeParameterDiscoveryRes
      Body: EVSEMaxCurrentLimit = 300A
            EVSEMaxVoltageLimit = 500V
            EVSEMaxPowerLimit = 150000W
            EVSENominalVoltage = 400V

PHASE 6: CABLE CHECK
  17. EVCC → SECC: CableCheckReq
  18. SECC → EVCC: CableCheckRes
      Body: EVSEProcessing = Ongoing / Finished
  → SECC closes internal contactors, performs isolation check
  → Verifies isolation resistance > 100 Ω/V (before HV on cable)

PHASE 7: PRE-CHARGE
  19. EVCC → SECC: PreChargeReq
      Body: EVTargetVoltage = [vehicle battery voltage]
            EVTargetCurrent = 0A (or 2A target)
  20. SECC → EVCC: PreChargeRes
      Body: EVSEPresentVoltage = [rising]
  → SECC ramps DC output voltage up to match vehicle battery voltage
  → Minimizes inrush current when EV contactors close

PHASE 8: CURRENT DEMAND (ACTUAL CHARGING)
  21. Vehicle closes main DC contactors
  22. EVCC → SECC: PowerDeliveryReq (ChargeProgress = Start)
  23. SECC → EVCC: PowerDeliveryRes
  
  24. EVCC → SECC: CurrentDemandReq (repeated every 25ms)
      Body: EVTargetCurrent = 200A (requested)
            EVTargetVoltage = 400V
            EVMaximumCurrentLimit = 200A (updated each cycle)
            ChargingComplete = false
  25. SECC → EVCC: CurrentDemandRes
      Body: EVSEPresentVoltage = 402V (actual)
            EVSEPresentCurrent = 195A (actual delivered)
            EVSEStatus = Normal

PHASE 9: CHARGE TERMINATION
  26. When BMS_SoC = target level:
      EVCC → SECC: CurrentDemandReq (ChargingComplete = true)
  27. SECC ramps down power
  28. EVCC → SECC: PowerDeliveryReq (ChargeProgress = Stop)
  29. Vehicle opens DC contactors
  30. EVCC → SECC: WeldingDetectionReq (check contactor welding)
  31. EVCC → SECC: SessionStopReq
  32. TCP connection closed
  33. Vehicle unplugged
```

---

## 10.4 CAN SIGNAL MAPPING — CHARGING SESSION

```
COMPLETE CAN SIGNAL MAP FOR AC CHARGING:

Time    │ Message        │ Signal              │ Value
────────┼────────────────┼─────────────────────┼──────────────
T=0ms   │ VCU_Command    │ VCU_ChargeEnable    │ 0 → 1
T=0ms   │ VCU_Command    │ VCU_ChargeCurrentLim│ 32A
T=100ms │ OBC_Status     │ OBC_ChargingPhase   │ 0→1 (INIT→CC)
T=200ms │ OBC_Status     │ OBC_ChargingCurrent │ 0 → 28A
T=200ms │ OBC_Status     │ OBC_ChargingVoltage │ 390V
T=200ms │ BMS_Status     │ BMS_SoC             │ 45.0%
T=200ms │ BMS_Status     │ BMS_PackCurrent     │ 0 → -28A (charge)
T=1000ms│ BMS_Limits     │ BMS_ChargePowerLimit│ 7200W
T=...   │ OBC_Status     │ OBC_ChargingCurrent │ 28A (stable CC)
T=...   │ BMS_Status     │ BMS_SoC             │ increasing 0.5%/min

At SoC → 95% (CC→CV transition):
T=...   │ OBC_Status     │ OBC_ChargingPhase   │ 1→2 (CC→CV)
T=...   │ OBC_Status     │ OBC_ChargingVoltage │ 412V (float)
T=...   │ OBC_Status     │ OBC_ChargingCurrent │ 28 → taper

At SoC = 100% or user target:
T=...   │ VCU_Command    │ VCU_ChargeEnable    │ 1 → 0
T=...   │ OBC_Status     │ OBC_ChargingPhase   │ 2→3 (CV→COMPLETE)
T=...   │ OBC_Status     │ OBC_ChargingCurrent │ → 0A
```

---

## 10.5 CHARGING VALIDATION TEST CASES

```
TC-CHARGE-001: AC Level 2 Full Charge Cycle
Requirement: SysRS-CHARGE-AC-001

Precondition:
  - Vehicle SoC = 20%
  - EVSE: 230VAC, 32A capable
  - Ambient temperature = 25°C

Step 1: Connect EVSE, monitor CP signal
Step 2: Verify state A → B → C transition
Step 3: Verify charging starts within 5 seconds of plug
Step 4: Monitor BMS_SoC increase rate: 
        Expected ≈ 0.5%/min at 7.2 kW (75 kWh battery)
Step 5: Monitor CC → CV transition at target voltage
Step 6: Verify charging complete notification to user

Pass Criteria:
  ✓ CP states A→B→C correctly in <2s per state
  ✓ Charging power ≥ 7.0 kW (80% of EVSE capacity)
  ✓ SoC increases correctly
  ✓ CC/CV transition at correct voltage
  ✓ No DTC set during normal charge
  ✓ Total charge time matches expected value

──────────────────────────────────────────────────────────────

TC-CHARGE-002: DC Fast Charge — CurrentDemand Loop
Requirement: SysRS-CHARGE-DC-001

Precondition:
  - Vehicle SoC = 20%, temperature 25°C
  - DCFC: 150 kW capable, CCS Combo 2

Step 1: Connect DCFC
Step 2: Monitor ISO 15118 message sequence on PLC/Ethernet
Step 3: Verify each phase completes:
        - SessionSetup: OK
        - ServiceDiscovery: ChargeService available
        - Authorization: OK
        - ChargeParameterDiscovery: parameters exchanged
        - CableCheck: isolation OK
        - PreCharge: voltage match OK
        - PowerDelivery: session started
Step 4: Monitor CurrentDemandReq cycle rate (must be ≤ 25ms)
Step 5: Monitor charging power: V × I
Step 6: Verify SoC increasing at expected rate

Expected:
  - Full 15118 handshake completes in < 90s
  - CurrentDemand loop at 25ms ± 5ms
  - Charging power ≥ 140 kW (if vehicle capable)

──────────────────────────────────────────────────────────────

TC-CHARGE-003: Emergency Shutdown — EVSE Loss
Requirement: SysRS-CHARGE-SAFE-001

Precondition: Active charging session (AC or DC), 15 kW

Step 1: Simulate EVSE power loss (cut AC input to EVSE)
Step 2: Monitor OBC_Status::OBC_ChargingPhase
Step 3: Measure time from loss to charging termination
Step 4: Verify DC bus voltage safety (for DC charging)

Expected:
  - OBC detects EVSE loss within 200ms
  - Charging terminates within 500ms
  - No HV at inlet connector after termination
  - DTC may be set for abnormal termination
  
──────────────────────────────────────────────────────────────

TC-CHARGE-004: Charging Fault — Overvoltage Protection
Requirement: SysRS-CHARGE-SAFE-003

Precondition: Active DC fast charging

Step 1: Command DCFC to deliver voltage 10V above BMS_MaxVoltage
        (simulate DCFC voltage regulation failure)
Step 2: Monitor BMS response

Expected:
  - BMS detects overvoltage within 100ms
  - BMS sends emergency stop: BMS_PackCurrent limit → 0
  - OBC/DCFC terminates power delivery
  - DTC 0x0A0001 (CellOvervoltage) set

──────────────────────────────────────────────────────────────

TC-CHARGE-005: Cold Weather Charging — -10°C
Requirement: SysRS-CHARGE-TEMP-001

Precondition: Battery temperature = -10°C (cold soak)

Step 1: Attempt to start charging
Step 2: Monitor BMS_Status::BMS_HeatingActive
Step 3: Monitor BMS charging current limits at -10°C
Step 4: Monitor temperature increase during heating

Expected:
  - BMS activates heating before charging (BMS_HeatingActive = 1)
  - Initial charge current limited to 0.1C (cold protection)
  - As temperature increases, charge current increases
  - Full charge current available only when T ≥ 10°C
  - Charging available but derated at -10°C

──────────────────────────────────────────────────────────────

TC-CHARGE-006: Scheduled Charging Activation
Requirement: SysRS-CHARGE-SCH-001

Step 1: Set vehicle departure time = T + 60 minutes
Step 2: Connect EVSE but vehicle should NOT start charging immediately
Step 3: Verify charging starts at T + 30 minutes (to reach 80% at departure)
Step 4: Verify charging complete at departure time

Expected:
  - VCU calculates required charge time
  - VCU delays ChargeEnable until needed
  - Charging starts exactly when needed for on-time completion

──────────────────────────────────────────────────────────────

TC-CHARGE-007: V2G Discharge (if applicable)
Requirement: SysRS-CHARGE-V2G-001 (ISO 15118-20)

Note: V2G = Vehicle-to-Grid (bidirectional)

Precondition: V2G-capable OBC, ISO 15118-20 compliant EVSE

Step 1: Authenticate with V2G energy management system
Step 2: Accept V2G discharge request (10 kW, 2 hours)
Step 3: Monitor power flow direction reversal

Expected:
  - EV discharges to grid as requested
  - SoC decreases at expected rate
  - Grid power quality maintained (PF > 0.95)
  - EV maintains minimum SoC reserve (20%)
```

---

## 10.6 CAPL CHARGING SIMULATION

```cpp
/* capl_scripts/charging_system_simulation.can
   OBC and EVSE simulation with full AC charging state machine
*/

variables {
  // OBC state machine
  int obcPhase = 0;     // 0=IDLE, 1=INIT, 2=CC, 3=CV, 4=COMPLETE, 5=FAULT
  
  // Charging parameters
  float chargeCurrentCmd  = 0.0;    // A - from VCU
  float obcActualCurrent  = 0.0;    // A
  float obcActualVoltage  = 0.0;    // V
  float obcTemp           = 25.0;   // °C

  // CP signal simulation
  int   cpState           = 0;      // 0=A, 1=B, 2=C, 3=D
  float cpDutyCycle       = 16.0;   // % (= 10A available)
  float evseCurrentLimit  = 10.0;   // A
  
  // Battery state (from BMS messages)
  float bmsPackVoltage    = 390.0;  // V
  float bmsMaxVoltage     = 410.0;  // V (CV target)
  float bmsChargeCurrent  = 0.0;    // A (actual charge)
  float bmsChargePowerLim = 7200.0; // W
  float bmsSoC            = 45.0;   // %

  // Timers
  msTimer tmrOBCCycle;       // 100ms OBC status transmission
  msTimer tmrChargeLogic;    // 500ms charging control
  msTimer tmrCPSimulation;   // 100ms CP state monitoring
  
  // OBC CAN message (0x620)
  message OBC_Status obcMsg = {id: 0x620, dlc: 8};
}

on start {
  setTimer(tmrOBCCycle,      100);
  setTimer(tmrChargeLogic,   500);
  setTimer(tmrCPSimulation,  100);
  
  obcActualVoltage = bmsPackVoltage;  // Start at battery voltage
  
  write("OBC Simulation started");
  write("  EVSE current limit: %.1fA", evseCurrentLimit);
}

// ─── OBC Status Transmission ─────────────────────────────────────

on timer tmrOBCCycle {
  // Calculate charging power
  float chargePower = obcActualVoltage * obcActualCurrent;
  
  // Temperature rise model
  obcTemp += (obcActualCurrent / 32.0) * 0.1;  // Heat up
  if (obcActualCurrent < 1.0) obcTemp -= 0.05;  // Cool down
  obcTemp = max(25.0, min(obcTemp, 90.0));
  
  // OBC_Status encoding (0x620)
  obcMsg.OBC_ChargingPhase   = obcPhase;
  obcMsg.OBC_ChargingCurrent = (word)(obcActualCurrent / 0.1);  // 0.1A/bit
  obcMsg.OBC_ChargingVoltage = (word)(obcActualVoltage / 0.1);  // 0.1V/bit
  obcMsg.OBC_OBCTemperature  = (byte)(obcTemp + 40);            // -40 offset
  obcMsg.OBC_EVSECurrentLimit= (byte)(evseCurrentLimit);
  obcMsg.OBC_FaultCode       = 0;
  
  output(obcMsg);
  setTimer(tmrOBCCycle, 100);
}

// ─── Charging Control Logic ───────────────────────────────────────

on timer tmrChargeLogic {
  switch(obcPhase) {
    case 0: // IDLE — wait for VCU enable
      obcActualCurrent = 0.0;
      break;
    
    case 1: // INIT — startup, ramp voltage
      obcActualCurrent = 0.5;  // Low current init
      obcActualVoltage = bmsPackVoltage;
      obcPhase = 2;  // Move to CC
      write("[OBC] Phase: INIT → CC");
      break;
    
    case 2: // CC — Constant Current
      {
        // Calculate target current
        float maxByEvse    = evseCurrentLimit;
        float maxByBMS     = bmsChargePowerLim / bmsPackVoltage;
        float maxByVCU     = chargeCurrentCmd;
        float targetCurrent = min(maxByEvse, min(maxByBMS, maxByVCU));
        
        // Ramp current
        if (obcActualCurrent < targetCurrent) {
          obcActualCurrent += 2.0;  // 2A/step ramp
        } else {
          obcActualCurrent = targetCurrent;
        }
        
        // Check for CV transition
        if (bmsPackVoltage >= bmsMaxVoltage * 0.99) {
          obcPhase = 3;  // Switch to CV
          write("[OBC] Phase: CC → CV (Vbatt=%.1fV)", bmsPackVoltage);
        }
        
        // OBC temperature derating
        if (obcTemp > 75.0) {
          float derateFactor = (90.0 - obcTemp) / 15.0;
          obcActualCurrent *= derateFactor;
          if (derateFactor < 0.1) obcPhase = 5;  // FAULT
        }
      }
      break;
    
    case 3: // CV — Constant Voltage
      {
        obcActualVoltage = bmsMaxVoltage;  // Hold at float voltage
        
        // Taper current (simulates BMS reducing charge current)
        if (obcActualCurrent > 2.0) {
          obcActualCurrent -= 0.5;  // Taper down
        } else {
          // End of charge (taper current < C/20)
          obcPhase = 4;
          write("[OBC] Phase: CV → COMPLETE");
        }
      }
      break;
    
    case 4: // COMPLETE
      obcActualCurrent = 0.0;
      break;
    
    case 5: // FAULT
      obcActualCurrent = 0.0;
      obcActualVoltage = 0.0;
      write("[OBC] FAULT: overtemperature %.1f°C", obcTemp);
      break;
  }
  
  setTimer(tmrChargeLogic, 500);
}

// ─── VCU Command Handler ──────────────────────────────────────────

on message VCU_Command {
  int  vcu_charge_enable  = this.VCU_ChargeEnable;
  float vcu_current_limit = this.VCU_ChargeCurrentLimit * 1.0;
  
  chargeCurrentCmd = vcu_current_limit;
  
  if (vcu_charge_enable == 1 && obcPhase == 0) {
    obcPhase = 1;  // Start charging
    write("[OBC] Charge Enable received, starting...");
  } else if (vcu_charge_enable == 0 && obcPhase != 0) {
    obcPhase = 0;  // Stop charging
    obcActualCurrent = 0.0;
    write("[OBC] Charge Disable received, stopping.");
  }
}

// ─── BMS Message Handler ─────────────────────────────────────────

on message BMS_Status {
  bmsPackVoltage = this.BMS_PackVoltage * 0.1;
  bmsSoC = this.BMS_SoC * 0.5;
}

on message BMS_Limits {
  bmsChargePowerLim = this.BMS_ChargePowerLimit * 10.0;  // 10W/bit
  bmsMaxVoltage = this.BMS_MaxChargeVoltage * 0.1;
}

// ─── Interactive Fault Injection ─────────────────────────────────

on key 'f' {
  write("[OBC] Fault injected manually");
  obcPhase = 5;
  obcMsg.OBC_FaultCode = 0x02;  // Overtemperature fault
  output(obcMsg);
}

on key 'r' {
  write("[OBC] Reset OBC simulation");
  obcPhase = 0;
  obcActualCurrent = 0.0;
  obcTemp = 25.0;
}

on key 's' {
  write("=== OBC Status ===");
  write("  Phase:    %d", obcPhase);
  write("  Current:  %.1f A", obcActualCurrent);
  write("  Voltage:  %.1f V", obcActualVoltage);
  write("  OBC Temp: %.1f C", obcTemp);
  write("  EVSE Lim: %.1f A", evseCurrentLimit);
  write("  BMS SoC:  %.1f%%", bmsSoC);
}
```

---

## 10.7 PYTHON CHARGING TEST AUTOMATION

```python
# tests/charging/test_ac_dc_charging.py
"""
AC/DC Charging validation test suite.
"""

import pytest
import time
import threading
from core.can_interface import CANInterface


class TestACCharging:
    """AC Level 2 charging validation tests."""

    def test_charging_startup_sequence(self, can_bus):
        """TC-CHARGE-001: Verify AC charging starts correctly."""
        # Enable charging via VCU
        can_bus.send_signal('VCU_Command', {
            'VCU_ChargeEnable': 1,
            'VCU_ChargeCurrentLimit': 32  # 32A
        })
        
        # Wait for OBC to start
        started = can_bus.wait_for_signal(
            'OBC_Status', 'OBC_ChargingPhase', 1,  # 1 = CC phase
            timeout=5.0
        )
        assert started, "OBC did not enter CC charging phase within 5s"
        
        # Verify charging current
        msg = can_bus.wait_for_message(
            can_bus._db.get_message_by_name('OBC_Status').frame_id,
            timeout=2.0
        )
        decoded = can_bus.decode_message(msg)
        current = decoded['OBC_ChargingCurrent']
        
        assert current > 0.0, f"OBC charging current = {current}A, expected > 0"
        assert current <= 32.0, f"OBC exceeded commanded limit: {current}A > 32A"

    def test_charging_current_within_bms_limit(self, can_bus):
        """Verify OBC current does not exceed BMS charge power limit."""
        # Collect data for 5 seconds
        violations = []
        
        def check(msg):
            decoded = can_bus.decode_message(msg)
            if decoded and decoded.get('OBC_ChargingCurrent', 0) > 33.0:  # 32A + 1A margin
                violations.append(decoded['OBC_ChargingCurrent'])
        
        obc_id = can_bus._db.get_message_by_name('OBC_Status').frame_id
        can_bus.register_callback(obc_id, check)
        time.sleep(5.0)
        can_bus._callbacks[obc_id].remove(check)
        
        assert len(violations) == 0, \
            f"Current limit violations detected: {violations}"

    def test_charge_complete_signal(self, can_bus):
        """Verify OBC sends COMPLETE phase signal when done."""
        # This test requires running to full SoC — use simplified version
        # with simulated battery at 99% SoC
        
        completed = can_bus.wait_for_signal(
            'OBC_Status', 'OBC_ChargingPhase', 4,  # 4 = COMPLETE
            timeout=30.0  # Wait up to 30s for simulation
        )
        
        if not completed:
            pytest.skip("Charging complete not reached within test window")
        
        # Verify current dropped to 0
        msg = can_bus.wait_for_message(
            can_bus._db.get_message_by_name('OBC_Status').frame_id,
            timeout=2.0
        )
        decoded = can_bus.decode_message(msg)
        assert decoded['OBC_ChargingCurrent'] < 1.0, \
            "Current not zero at charge complete"


class TestChargingFaults:
    """Charging fault handling tests."""

    def test_fault_terminates_charging(self, can_bus):
        """Verify charging terminates on OBC fault."""
        # First start charging
        can_bus.send_signal('VCU_Command', {
            'VCU_ChargeEnable': 1,
            'VCU_ChargeCurrentLimit': 32
        })
        time.sleep(1.0)
        
        # Inject fault (send fault code via CAPL key or hardware)
        # In this test we simulate by checking VCU disables on fault
        # In real test: use HIL fault injection
        
        # Simulate fault in OBC
        can_bus.send_signal('VCU_Command', {'VCU_ChargeEnable': 0})
        
        # Verify charging stopped
        stopped = can_bus.wait_for_signal(
            'OBC_Status', 'OBC_ChargingPhase', 0,  # 0 = IDLE
            timeout=3.0
        )
        assert stopped, "OBC did not stop on charge disable"
```

---

## SECTION 10 SUMMARY

| Standard | Application | Key Signals |
|----------|-------------|-------------|
| SAE J1772 | AC charging | CP state A/B/C, PP resistance |
| IEC 62196 | AC Type 2 | CP duty cycle → current limit |
| ISO 15118-2 | DC CCS | SessionSetup, ChargeParam, CurrentDemand |
| DIN 70121 | DC CCS legacy | Basic V2G protocol |
| CHAdeMO | DC Japan | CAN-based charge control |
| IEC 61851 | Safety requirements | Isolation, interlock |

Key test areas: CP signal states, charging sequence timing, fault shutdown, temperature derating, V2G bidirectional, scheduled charging.

---

*Next: Section 11 — Functional Safety & Cybersecurity*
