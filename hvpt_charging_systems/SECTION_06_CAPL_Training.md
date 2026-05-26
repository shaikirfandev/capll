# SECTION 6 — CAPL PROGRAMMING COMPLETE TRAINING
## Beginner to Advanced — Real OEM Automation Examples

---

## 6.1 CAPL FUNDAMENTALS

### 6.1.1 What is CAPL?

CAPL (CAN Access Programming Language) is a C-like event-driven programming language embedded in Vector CANoe and CANalyzer. It allows:
- Simulating ECU behavior (restbus simulation)
- Automating test scenarios
- Implementing custom protocol handling
- Injecting faults and stimuli
- Creating diagnostic sequences
- Processing received CAN messages

### 6.1.2 CAPL Architecture

```
CAPL PROGRAM STRUCTURE:
──────────────────────────────────────────────────────────────
                   ┌─────────────────────────┐
                   │      CAPL PROGRAM        │
                   │                         │
    CANoe          │  ┌─────────────────┐    │
    Events ───────▶│  │   Event handlers│    │
    (messages,     │  │  on start()     │    │
     timers,       │  │  on message X() │    │
     key presses,  │  │  on timer T()   │    │
     signals,      │  │  on envVar V()  │    │
     key states)   │  └─────────────────┘    │
                   │                         │
                   │  ┌─────────────────┐    │
                   │  │    Functions    │    │──▶ CAN output
                   │  │  (user-defined) │    │   Signal set
                   │  └─────────────────┘    │   Write output
                   │                         │   Test result
                   │  ┌─────────────────┐    │
                   │  │    Variables    │    │
                   │  │  (local, global)│    │
                   │  └─────────────────┘    │
                   └─────────────────────────┘
```

### 6.1.3 CAPL File Structure

```capl
// ═══════════════════════════════════════════════════════════
// FILE: BMS_Simulation.can
// PURPOSE: Simulate BMS ECU for bench testing VCU
// ═══════════════════════════════════════════════════════════

includes
{
  // Include other CAPL files (libraries)
  #include "Common_Utilities.cin"
  #include "UDS_Library.cin"
}

variables
{
  // Global variables declared here
  message BMS_Status gBMS_Status;         // CAN message object
  msTimer gBMS_Timer;                     // 10ms cyclic timer
  
  float gSoC = 80.0;                      // State of Charge (%)
  float gPackVoltage = 380.0;             // Pack voltage (V)
  float gPackCurrent = 0.0;              // Pack current (A)
  float gMaxCellTemp = 25.0;             // Max cell temperature
  int gContactorState = 0;               // 0=OPEN, 2=CLOSED
  int gFaultCode = 0;                    // Fault bitmap
  
  // Constants
  const float kSOC_MIN = 5.0;
  const float kSOC_MAX = 100.0;
  const int kMSG_PERIOD_MS = 10;
}

// ═══════════════════════════════════════════════════════════
// EVENT: on start — called when CANoe measurement starts
// ═══════════════════════════════════════════════════════════
on start
{
  write("BMS Simulation started");
  setTimer(gBMS_Timer, kMSG_PERIOD_MS);   // Start 10ms cyclic timer
}

// ═══════════════════════════════════════════════════════════
// EVENT: on timer — cyclic message transmission
// ═══════════════════════════════════════════════════════════
on timer gBMS_Timer
{
  SendBMSStatus();                         // Send BMS status
  setTimer(gBMS_Timer, kMSG_PERIOD_MS);   // Restart timer
}

// ═══════════════════════════════════════════════════════════
// EVENT: on message — process received CAN messages
// ═══════════════════════════════════════════════════════════
on message VCU_Command
{
  int hv_enable;
  hv_enable = this.VCU_HV_Enable;
  
  if (hv_enable == 1)   // VCU requests HV ON
  {
    write("VCU requests HV ON — starting precharge");
    StartPrecharge();
  }
  else if (hv_enable == 0)  // VCU requests HV OFF
  {
    OpenContactors();
  }
}

// ═══════════════════════════════════════════════════════════
// FUNCTION: Send BMS status message
// ═══════════════════════════════════════════════════════════
void SendBMSStatus()
{
  gBMS_Status.BMS_SoC = gSoC;
  gBMS_Status.BMS_PackVoltage = gPackVoltage;
  gBMS_Status.BMS_PackCurrent = gPackCurrent;
  gBMS_Status.BMS_MaxCellTemp = gMaxCellTemp;
  gBMS_Status.BMS_ContactorState = gContactorState;
  gBMS_Status.BMS_FaultCode = gFaultCode;
  
  output(gBMS_Status);
}
```

---

## 6.2 CAPL VARIABLES

### 6.2.1 Data Types

```capl
variables
{
  // INTEGER TYPES
  byte   b1 = 0;           // 8-bit unsigned (0–255)
  word   w1 = 0;           // 16-bit unsigned (0–65535)
  dword  dw1 = 0;          // 32-bit unsigned (0–4294967295)
  int    i1 = 0;           // 32-bit signed (-2147483648 to +2147483647)
  long   l1 = 0L;          // 32-bit signed (same as int in CAPL)
  int64  i64 = 0;          // 64-bit signed
  
  // FLOATING POINT
  float  f1 = 0.0;         // 32-bit float
  double d1 = 0.0;         // 64-bit double
  
  // CHARACTER
  char   c1 = 'A';
  char   str1[100] = "Hello CAN";   // String (char array)
  
  // MESSAGE OBJECTS (reference DBC messages)
  message BMS_Status        gBMSMsg;      // message by name
  message 0x310             gBMSMsg2;     // message by ID
  
  // TIMER OBJECTS
  msTimer  gTimer1;        // millisecond timer
  timer    gTimer2;        // second timer
  
  // SIGNAL ALIASES
  // Access via: $SignalName (environment)
  
  // ARRAYS
  float    gCellVoltages[96];            // array of 96 floats
  byte     gCANData[8];                  // 8-byte array
  
  // CONSTANTS (const keyword)
  const float kBATTERY_MAX_VOLTAGE = 420.0;
  const int   kMAX_CELLS = 96;
}
```

### 6.2.2 System Variables and Environment Variables

```capl
// ENVIRONMENT VARIABLES (panel controls):
// Defined in CANoe → Environment → Environment Variables

on envVar Env_ChargeEnable   // triggered when panel button pressed
{
  int value;
  value = getValue(this);    // get panel value
  
  if (value == 1)
  {
    write("Charge enable requested from panel");
    $VCU_ChargeEnable = 1;   // set CAN signal
  }
}

// SYSTEM VARIABLES (predefined CANoe variables):
// Access with @sysvar:: namespace
// Example: @sysvar::VehicleSpeed::Speed_kmh
on sysvar_update sysvar::BMS::SoC
{
  write("SoC updated to: %.1f%%", @sysvar::BMS::SoC);
}
```

---

## 6.3 CAPL TIMERS

```capl
variables
{
  msTimer gCyclicTimer;           // For cyclic tasks
  msTimer gTimeoutTimer;          // For timeout monitoring  
  msTimer gDelayTimer;            // For one-shot delays
  int gTimeoutExpired = 0;
}

// CYCLIC TIMER EXAMPLE:
on timer gCyclicTimer
{
  // This code executes every 10ms
  TransmitHeartbeat();
  setTimer(gCyclicTimer, 10);    // restart
}

// TIMEOUT TIMER EXAMPLE:
on timer gTimeoutTimer
{
  gTimeoutExpired = 1;
  write("ERROR: Timeout expired! No response from BMS.");
}

void WaitForContactorClosed()
{
  gTimeoutExpired = 0;
  setTimer(gTimeoutTimer, 3000);   // 3 second timeout
  
  while ($BMS_ContactorState != 2 && gTimeoutExpired == 0)
  {
    // Wait in loop (handled by event system)
    testWaitForTimeout(10);        // yield for 10ms
  }
  
  cancelTimer(gTimeoutTimer);
  
  if ($BMS_ContactorState == 2)
    write("Contactor CLOSED ✓");
  else
    write("ERROR: Contactor did not close within timeout!");
}

// ONE-SHOT DELAY:
void DelayedAction()
{
  setTimer(gDelayTimer, 500);    // 500ms delay
}

on timer gDelayTimer
{
  // Called once after 500ms — do NOT restart
  write("Delayed action executed");
}
```

---

## 6.4 CAPL MESSAGE HANDLING

### 6.4.1 Receiving Messages

```capl
// ─────────────────────────────────────────────────
// Receive by message NAME (requires DBC loaded)
// ─────────────────────────────────────────────────
on message BMS_Status
{
  float soc, voltage, current;
  
  soc     = this.BMS_SoC;           // access signal by name
  voltage = this.BMS_PackVoltage;
  current = this.BMS_PackCurrent;
  
  write("BMS: SoC=%.1f%% Voltage=%.1fV Current=%.1fA",
        soc, voltage, current);
  
  // Check for fault
  if (this.BMS_FaultCode != 0)
  {
    write("BMS FAULT: 0x%04X", this.BMS_FaultCode);
  }
}

// ─────────────────────────────────────────────────
// Receive by message ID (hex)
// ─────────────────────────────────────────────────
on message 0x310
{
  byte byte0, byte1;
  int raw_soc;
  float physical_soc;
  
  byte0 = this.byte(0);             // access raw bytes
  byte1 = this.byte(1);
  
  raw_soc = byte0 | (byte1 << 8);  // Intel byte order
  physical_soc = raw_soc * 0.5;    // apply factor
  
  write("Raw SoC: %d → Physical: %.1f%%", raw_soc, physical_soc);
}

// ─────────────────────────────────────────────────
// Receive with message direction filter
// ─────────────────────────────────────────────────
on message *   // catch ALL messages
{
  if (this.dir == RX)   // only process received messages
  {
    // Log all received messages
  }
}
```

### 6.4.2 Transmitting Messages

```capl
// ─────────────────────────────────────────────────
// Method 1: Immediate output
// ─────────────────────────────────────────────────
void SendVCUCommand(int hv_enable, int charge_enable)
{
  message VCU_Command msg;
  
  msg.VCU_HV_Enable    = hv_enable;
  msg.VCU_ChargeEnable = charge_enable;
  msg.VCU_DriveMode    = 1;    // NORMAL
  
  output(msg);   // immediate transmission
}

// ─────────────────────────────────────────────────
// Method 2: Set signal via $ shorthand
// ─────────────────────────────────────────────────
void SetDriveMode(int mode)
{
  $VCU_Command::VCU_DriveMode = mode;   // sets signal in restbus simulation
}

// ─────────────────────────────────────────────────
// Method 3: Raw byte construction
// ─────────────────────────────────────────────────
void SendRawMessage()
{
  message 0x100 raw_msg;
  
  raw_msg.dlc = 8;
  raw_msg.byte(0) = 0x01;    // byte 0
  raw_msg.byte(1) = 0x00;    // byte 1
  raw_msg.byte(2) = 0xF4;    // byte 2 (100.0A charge current = 1000 × 0.1)
  raw_msg.byte(3) = 0x03;    // byte 3 (upper byte of 1000)
  raw_msg.byte(4) = 0x70;    // byte 4
  raw_msg.byte(5) = 0x17;    // byte 5
  raw_msg.byte(6) = 0x00;
  raw_msg.byte(7) = 0x00;
  
  output(raw_msg);
}
```

---

## 6.5 CAPL SIGNAL HANDLING

```capl
// ─────────────────────────────────────────────────
// on signal — triggered when signal CHANGES value
// ─────────────────────────────────────────────────
on signal BMS_Status::BMS_SoC
{
  float new_soc = this.phys;    // physical value
  write("SoC changed to: %.1f%%", new_soc);
  
  // Update panel display
  putValue(Env_SoCDisplay, new_soc);
}

// ─────────────────────────────────────────────────
// on signal_update — triggered on EVERY message (even no change)
// ─────────────────────────────────────────────────
on signal_update BMS_Status::BMS_PackVoltage
{
  float voltage = this.phys;
  
  // Check limit
  if (voltage > 420.0)
  {
    write("WARNING: Pack voltage too high: %.1fV", voltage);
  }
}

// ─────────────────────────────────────────────────
// Reading signal value imperatively
// ─────────────────────────────────────────────────
void CheckBatteryHealth()
{
  float soc = $BMS_SoC;             // read current value
  float voltage = $BMS_PackVoltage;
  float temp = $BMS_MaxCellTemp;
  
  write("Battery: SoC=%.1f%% V=%.1fV T=%.1f°C", soc, voltage, temp);
}
```

---

## 6.6 COMPLETE CAPL PROJECTS

### 6.6.1 Project 1: Battery ECU Simulation

```capl
// ═══════════════════════════════════════════════════════════════
// FILE: battery_ecu_simulation.can
// PURPOSE: Complete BMS simulation for HIL/bench testing
// ═══════════════════════════════════════════════════════════════

includes
{
}

variables
{
  // BMS state
  message BMS_Status  gBMS_Status;
  message BMS_Limits  gBMS_Limits;
  msTimer gBMS_Status_Timer;
  msTimer gBMS_Limits_Timer;
  msTimer gPrecharge_Timer;
  
  // Battery model
  float gSoC = 80.0;             // %
  float gSoH = 96.0;             // %
  float gPackVoltage = 380.0;    // V
  float gPackCurrent = 0.0;      // A
  float gMaxCellTemp = 25.0;     // °C
  float gMinCellTemp = 22.0;     // °C
  float gMaxCellVolt = 3950;     // mV
  float gMinCellVolt = 3900;     // mV
  
  // Battery limits
  float gMaxChargePower = 150.0; // kW
  float gMaxDischargePower = 200.0; // kW
  float gMaxChargeVolt = 420.0;  // V
  float gMaxChargeCurrent = 100.0; // A
  
  // State
  int gContactorState = 0;   // 0=OPEN, 1=PRECHARGE, 2=CLOSED
  int gIsolationOK = 1;
  int gFaultCode = 0;
  int gPrechargeStep = 0;
  
  // Simulation parameters
  float gCapacity_Ah = 100.0;    // Battery capacity
  const int kSTATUS_PERIOD = 10;  // ms
  const int kLIMITS_PERIOD = 100; // ms
}

// ─────────────────────────────────────
// STARTUP
// ─────────────────────────────────────
on start
{
  write("=== BMS Simulation Starting ===");
  write("Initial SoC: %.1f%%", gSoC);
  setTimer(gBMS_Status_Timer, kSTATUS_PERIOD);
  setTimer(gBMS_Limits_Timer, kLIMITS_PERIOD);
}

// ─────────────────────────────────────
// CYCLIC TIMERS
// ─────────────────────────────────────
on timer gBMS_Status_Timer
{
  UpdateBatteryModel();
  SendBMS_Status();
  setTimer(gBMS_Status_Timer, kSTATUS_PERIOD);
}

on timer gBMS_Limits_Timer
{
  SendBMS_Limits();
  setTimer(gBMS_Limits_Timer, kLIMITS_PERIOD);
}

// ─────────────────────────────────────
// BATTERY MODEL UPDATE
// ─────────────────────────────────────
void UpdateBatteryModel()
{
  float dSoC;
  float dt_h = kSTATUS_PERIOD / 3600000.0; // convert ms to hours
  
  // Update SoC: SoC change = current × time / capacity
  // Positive current = discharge, negative = charge
  dSoC = (gPackCurrent * dt_h / gCapacity_Ah) * 100.0;
  gSoC -= dSoC;   // discharge reduces SoC
  
  // Clamp SoC to valid range
  if (gSoC > 100.0) gSoC = 100.0;
  if (gSoC < 0.0)   gSoC = 0.0;
  
  // Update pack voltage (simplified OCV model)
  gPackVoltage = 3.0 * 96 + (gSoC / 100.0) * 1.2 * 96;
  // Simplified: V = 288 + SoC_fraction × 115.2 V
  // At 0% SoC: 288V, At 100% SoC: 403.2V
  
  // Cell voltages
  gMaxCellVolt = (gPackVoltage / 96.0 + 0.05) * 1000;  // mV
  gMinCellVolt = (gPackVoltage / 96.0 - 0.02) * 1000;  // mV
  
  // Update power limits based on SoC and temperature
  UpdatePowerLimits();
  
  // Fault checking
  CheckFaults();
}

void UpdatePowerLimits()
{
  // Reduce charge power when SoC > 80%
  if (gSoC > 80.0)
  {
    gMaxChargePower = 150.0 * (100.0 - gSoC) / 20.0;
    if (gMaxChargePower < 5.0) gMaxChargePower = 5.0;
  }
  else
  {
    gMaxChargePower = 150.0;
  }
  
  // Reduce charge power at high temperature
  if (gMaxCellTemp > 40.0)
  {
    gMaxChargePower = gMaxChargePower * 0.5;
    gMaxDischargePower = gMaxDischargePower * 0.7;
  }
  
  // Inhibit charging below 5°C
  if (gMinCellTemp < 5.0)
  {
    gMaxChargePower = 0.0;
    write("BMS: Charge inhibited — cell temp too low (%.1f°C)", gMinCellTemp);
  }
}

void CheckFaults()
{
  gFaultCode = 0;   // clear all faults
  
  // Overvoltage check (cell voltage > 4250 mV)
  if (gMaxCellVolt > 4250)
  {
    gFaultCode |= 0x0001;  // bit 0 = overvoltage
    write("BMS FAULT: Cell overvoltage! %.0fmV", gMaxCellVolt);
  }
  
  // Undervoltage check (cell voltage < 2800 mV)  
  if (gMinCellVolt < 2800)
  {
    gFaultCode |= 0x0002;  // bit 1 = undervoltage
    write("BMS FAULT: Cell undervoltage! %.0fmV", gMinCellVolt);
  }
  
  // Overtemperature check
  if (gMaxCellTemp > 55.0)
  {
    gFaultCode |= 0x0004;  // bit 2 = overtemperature
    write("BMS FAULT: Overtemperature! %.1f°C", gMaxCellTemp);
  }
  
  // If any fault → open contactors
  if (gFaultCode != 0 && gContactorState == 2)
  {
    OpenContactors();
  }
}

// ─────────────────────────────────────
// CONTACTOR CONTROL
// ─────────────────────────────────────
void StartPrecharge()
{
  write("BMS: Starting precharge sequence...");
  gContactorState = 1;  // PRECHARGE
  gPrechargeStep = 0;
  setTimer(gPrecharge_Timer, 100);  // check every 100ms
}

on timer gPrecharge_Timer
{
  float dclink_voltage;
  
  gPrechargeStep++;
  
  // Simulate DC link voltage rising during precharge
  dclink_voltage = gPackVoltage * (1.0 - 0.95 * exp_approx(-gPrechargeStep * 0.3));
  
  write("Precharge: Step %d, DCLink = %.1fV (target: %.1fV)",
        gPrechargeStep, dclink_voltage, gPackVoltage * 0.95);
  
  if (dclink_voltage >= gPackVoltage * 0.95 || gPrechargeStep >= 20)
  {
    // Precharge complete — close main contactors
    gContactorState = 2;  // CLOSED
    write("BMS: Contactor CLOSED! Precharge complete.");
  }
  else
  {
    setTimer(gPrecharge_Timer, 100);  // continue monitoring
  }
}

void OpenContactors()
{
  gContactorState = 0;  // OPEN
  gPackCurrent = 0.0;
  write("BMS: Contactors OPENED");
}

// ─────────────────────────────────────
// MESSAGE TRANSMISSION
// ─────────────────────────────────────
void SendBMS_Status()
{
  gBMS_Status.BMS_SoC = gSoC;
  gBMS_Status.BMS_SoH = gSoH;
  gBMS_Status.BMS_PackVoltage = gPackVoltage;
  gBMS_Status.BMS_PackCurrent = gPackCurrent;
  gBMS_Status.BMS_MaxCellTemp = gMaxCellTemp;
  gBMS_Status.BMS_MinCellTemp = gMinCellTemp;
  gBMS_Status.BMS_MaxCellVolt = gMaxCellVolt;
  gBMS_Status.BMS_MinCellVolt = gMinCellVolt;
  gBMS_Status.BMS_ContactorState = gContactorState;
  gBMS_Status.BMS_IsolationStatus = gIsolationOK;
  gBMS_Status.BMS_FaultCode = gFaultCode;
  
  output(gBMS_Status);
}

void SendBMS_Limits()
{
  gBMS_Limits.BMS_MaxChargePower    = gMaxChargePower;
  gBMS_Limits.BMS_MaxDischargePower = gMaxDischargePower;
  gBMS_Limits.BMS_MaxChargeVoltage  = gMaxChargeVolt;
  gBMS_Limits.BMS_MaxChargeCurrent  = gMaxChargeCurrent;
  
  output(gBMS_Limits);
}

// ─────────────────────────────────────
// INCOMING MESSAGE PROCESSING
// ─────────────────────────────────────
on message VCU_Command
{
  int hv_enable;
  hv_enable = this.VCU_HV_Enable;
  
  switch (hv_enable)
  {
    case 0:  // HV OFF
      if (gContactorState != 0)
        OpenContactors();
      break;
      
    case 1:  // HV ON
      if (gContactorState == 0 && gFaultCode == 0)
        StartPrecharge();
      break;
      
    case 3:  // Fault request / emergency
      OpenContactors();
      break;
  }
}

// ─────────────────────────────────────
// KEY PRESS EVENTS (for manual testing)
// ─────────────────────────────────────
on key 'h'   // Press 'h' to toggle HV
{
  if (gContactorState == 0)
  {
    write("Key: Requesting HV ON");
    StartPrecharge();
  }
  else
  {
    write("Key: Requesting HV OFF");
    OpenContactors();
  }
}

on key 'f'   // Press 'f' to inject isolation fault
{
  write("FAULT INJECTION: Isolation fault");
  gIsolationOK = 0;
  gFaultCode |= 0x0010;
  OpenContactors();
}

on key 'c'   // Press 'c' to clear faults
{
  write("Clearing all BMS faults");
  gFaultCode = 0;
  gIsolationOK = 1;
}

on key 't'   // Press 't' to increase temperature
{
  gMaxCellTemp += 5.0;
  write("Temperature increased to %.1f°C", gMaxCellTemp);
}

// ─────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────
float exp_approx(float x)
{
  // Simple exponential approximation using Taylor series
  // Only accurate for small x — for simulation purposes
  if (x > 5.0) return 150.0;
  if (x < -5.0) return 0.0;
  return 1.0 + x + x*x/2 + x*x*x/6 + x*x*x*x/24;
}
```

### 6.6.2 Project 2: Charging System Simulation

```capl
// ═══════════════════════════════════════════════════════════════
// FILE: charging_system_simulation.can
// PURPOSE: Simulate complete AC/DC charging session
// ═══════════════════════════════════════════════════════════════

variables
{
  // OBC messages
  message OBC_Status   gOBC_Status;
  msTimer gOBC_Timer;
  msTimer gChargeTimer;
  
  // Charging state
  int gChargingState = 0;  // 0=IDLE, 1=INIT, 2=PRECHARGE, 3=CHARGING, 4=DONE, 5=FAULT
  float gOutputVoltage = 0.0;   // V
  float gOutputCurrent = 0.0;   // A
  float gOutputPower   = 0.0;   // W
  float gOBC_Temp = 30.0;       // °C
  
  // Target from VCU
  float gTargetVoltage = 0.0;
  float gMaxCurrent = 0.0;
  
  const int kOBC_PERIOD = 100;  // ms
}

on start
{
  write("=== OBC / Charging Simulation Started ===");
  setTimer(gOBC_Timer, kOBC_PERIOD);
}

on timer gOBC_Timer
{
  UpdateChargingModel();
  SendOBC_Status();
  setTimer(gOBC_Timer, kOBC_PERIOD);
}

void UpdateChargingModel()
{
  switch (gChargingState)
  {
    case 0:  // IDLE
      gOutputVoltage = 0.0;
      gOutputCurrent = 0.0;
      gOutputPower = 0.0;
      break;
      
    case 1:  // INIT
      write("OBC: Initializing...");
      gChargingState = 2;  // → PRECHARGE
      break;
      
    case 2:  // PRECHARGE (ramping up voltage)
      gOutputVoltage += 5.0;  // ramp up 5V per 100ms
      if (gOutputVoltage >= gTargetVoltage - 5.0)
      {
        write("OBC: Voltage reached target, starting current");
        gChargingState = 3;  // → CHARGING
      }
      break;
      
    case 3:  // CHARGING (constant current / constant voltage)
      // CC phase
      if (gOutputVoltage < gTargetVoltage)
      {
        gOutputCurrent = gMaxCurrent;  // constant current
        gOutputVoltage += 0.5;         // voltage rises slowly
      }
      else
      {
        // CV phase (voltage reached, current tapers)
        gOutputCurrent = gMaxCurrent * 0.5;
        if (gOutputCurrent < 2.0)
        {
          write("OBC: Charging COMPLETE (current tapered to %.1fA)", gOutputCurrent);
          gChargingState = 4;  // DONE
        }
      }
      gOutputPower = gOutputVoltage * gOutputCurrent;
      
      // Temperature rise model
      gOBC_Temp += (gOutputPower / 100000.0);  // simplified thermal model
      if (gOBC_Temp > 80.0)
      {
        write("OBC FAULT: Overtemperature! %.1f°C", gOBC_Temp);
        gChargingState = 5;  // FAULT
      }
      break;
      
    case 4:  // DONE
      gOutputCurrent = 0.0;
      gOutputPower = 0.0;
      // Keep voltage maintained briefly then ramp down
      break;
      
    case 5:  // FAULT
      gOutputVoltage = 0.0;
      gOutputCurrent = 0.0;
      gOutputPower = 0.0;
      break;
  }
}

void SendOBC_Status()
{
  gOBC_Status.OBC_State = gChargingState;
  gOBC_Status.OBC_OutputVoltage = gOutputVoltage;
  gOBC_Status.OBC_OutputCurrent = gOutputCurrent;
  gOBC_Status.OBC_OutputPower = gOutputPower;
  gOBC_Status.OBC_Temperature = gOBC_Temp;
  
  output(gOBC_Status);
}

on message VCU_ChargingControl
{
  int charge_enable = this.VCU_ChargeEnable;
  
  if (charge_enable == 1 && gChargingState == 0)
  {
    gTargetVoltage = this.VCU_TargetVoltage;
    gMaxCurrent = this.VCU_MaxCurrent;
    write("OBC: Charge request received. Target=%.1fV, MaxI=%.1fA",
          gTargetVoltage, gMaxCurrent);
    gChargingState = 1;  // → INIT
  }
  else if (charge_enable == 0 && gChargingState != 0)
  {
    write("OBC: Charge stop requested");
    gChargingState = 4;  // → DONE
  }
}
```

### 6.6.3 Project 3: Fault Injection Framework

```capl
// ═══════════════════════════════════════════════════════════════
// FILE: fault_injection_framework.can
// PURPOSE: Systematic fault injection for validation testing
// ═══════════════════════════════════════════════════════════════

variables
{
  msTimer gFaultTimer;
  int gFaultActive = 0;
  int gCurrentFaultType = 0;
  
  // Fault types
  const int FAULT_BMS_OVERVOLT    = 1;
  const int FAULT_BMS_UNDERTEMP   = 2;
  const int FAULT_INV_TIMEOUT     = 3;
  const int FAULT_ISOLATION       = 4;
  const int FAULT_INTERLOCK       = 5;
  const int FAULT_CAN_BUSOFF      = 6;
  const int FAULT_CHARGING_COMM   = 7;
}

// ─────────────────────────────────────
// FAULT INJECTION API
// ─────────────────────────────────────
void InjectFault(int faultType, int duration_ms)
{
  gCurrentFaultType = faultType;
  gFaultActive = 1;
  
  switch (faultType)
  {
    case FAULT_BMS_OVERVOLT:
      write("[FAULT INJECT] BMS Cell Overvoltage");
      $BMS_Status::BMS_MaxCellVolt = 4300;   // 4300mV > 4250mV limit
      $BMS_Status::BMS_FaultCode = 0x0001;
      break;
      
    case FAULT_BMS_UNDERTEMP:
      write("[FAULT INJECT] BMS Undertemperature");
      $BMS_Status::BMS_MinCellTemp = -15;    // Below -10°C charging limit
      break;
      
    case FAULT_INV_TIMEOUT:
      write("[FAULT INJECT] Inverter message timeout");
      // Stop inverter message transmission (remove from restbus)
      stopRestbusSimulation(INV_Status);
      break;
      
    case FAULT_ISOLATION:
      write("[FAULT INJECT] Isolation fault");
      $BMS_Status::BMS_IsolationStatus = 0;  // 0 = FAULT
      $BMS_Status::BMS_FaultCode = 0x0010;
      break;
      
    case FAULT_INTERLOCK:
      write("[FAULT INJECT] HV Interlock open");
      $PDU_Status::PDU_IsolationOK = 0;
      break;
      
    case FAULT_CHARGING_COMM:
      write("[FAULT INJECT] Charging communication failure");
      stopRestbusSimulation(OBC_Status);  // OBC stops responding
      break;
  }
  
  setTimer(gFaultTimer, duration_ms);
}

on timer gFaultTimer
{
  // Clear the injected fault
  ClearFault(gCurrentFaultType);
}

void ClearFault(int faultType)
{
  write("[FAULT INJECT] Clearing fault type %d", faultType);
  gFaultActive = 0;
  
  switch (faultType)
  {
    case FAULT_BMS_OVERVOLT:
      $BMS_Status::BMS_MaxCellVolt = 3950;
      $BMS_Status::BMS_FaultCode = 0;
      break;
      
    case FAULT_INV_TIMEOUT:
      startRestbusSimulation(INV_Status);
      break;
      
    case FAULT_ISOLATION:
      $BMS_Status::BMS_IsolationStatus = 1;
      $BMS_Status::BMS_FaultCode = 0;
      break;
      
    case FAULT_CHARGING_COMM:
      startRestbusSimulation(OBC_Status);
      break;
  }
}

// ─────────────────────────────────────
// TEST SCENARIO: BMS Overvoltage Fault Response
// ─────────────────────────────────────
testcase TC_BMS_Overvoltage_Response()
{
  TestCaseTitle("TC_FAULT_001", "BMS Overvoltage Fault Response");
  TestCaseDescription("Verify VCU opens contactors when BMS reports overvoltage");
  
  // Precondition: HV system is active
  if ($VCU_State != 3)  // 3 = READY
  {
    TestStepFail("Precondition", "Vehicle not in READY state");
    return;
  }
  
  TestStepPass("Precondition", "Vehicle in READY state, contactors closed");
  
  // Inject overvoltage fault
  InjectFault(FAULT_BMS_OVERVOLT, 5000);  // 5 second fault
  
  // Wait and check VCU reaction
  testWaitForTimeout(200);   // allow time for reaction
  
  // Check contactor state
  if ($BMS_ContactorState == 0)  // 0 = OPEN
  {
    TestStepPass("Contactor Response", "Contactors opened within 200ms ✓");
  }
  else
  {
    TestStepFail("Contactor Response", "Contactors NOT opened! State = %d",
                 $BMS_ContactorState);
  }
  
  // Check DTC set
  testWaitForTimeout(1000);
  // UDS check would go here...
}
```

### 6.6.4 Project 4: Network Monitor Tool

```capl
// ═══════════════════════════════════════════════════════════════
// FILE: network_monitor_tool.can
// PURPOSE: Monitor CAN network health and report anomalies
// ═══════════════════════════════════════════════════════════════

variables
{
  msTimer gMonitorTimer;
  
  // Message reception tracking
  dword gBMS_LastRx = 0;
  dword gMCU_LastRx = 0;
  dword gOBC_LastRx = 0;
  dword gINV_LastRx = 0;
  
  // Timeout thresholds (ms)
  const int kBMS_TIMEOUT = 50;
  const int kMCU_TIMEOUT = 25;
  const int kOBC_TIMEOUT = 500;
  const int kINV_TIMEOUT = 25;
  
  // Error counters
  int gBMS_Timeout_Count = 0;
  int gMCU_Timeout_Count = 0;
  int gOBC_Timeout_Count = 0;
  int gINV_Timeout_Count = 0;
  int gTotalErrors = 0;
}

on start
{
  setTimer(gMonitorTimer, 10);  // Check every 10ms
  write("Network Health Monitor started");
}

on timer gMonitorTimer
{
  dword now = timeNow() / 100000;  // Convert to ms (timeNow returns 100ns units)
  
  CheckTimeout("BMS", gBMS_LastRx, now, kBMS_TIMEOUT, gBMS_Timeout_Count);
  CheckTimeout("MCU", gMCU_LastRx, now, kMCU_TIMEOUT, gMCU_Timeout_Count);
  CheckTimeout("OBC", gOBC_LastRx, now, kOBC_TIMEOUT, gOBC_Timeout_Count);
  CheckTimeout("INV", gINV_LastRx, now, kINV_TIMEOUT, gINV_Timeout_Count);
  
  setTimer(gMonitorTimer, 10);
}

void CheckTimeout(char node[], dword lastRx, dword now, int timeout, int errCnt)
{
  if ((now - lastRx) > timeout && lastRx > 0)
  {
    errCnt++;
    gTotalErrors++;
    write("NETWORK ALERT: %s message timeout! Last Rx: %dms ago (threshold: %dms)",
          node, (now - lastRx), timeout);
  }
}

// Update reception timestamps
on message BMS_Status  { gBMS_LastRx = timeNow() / 100000; }
on message MCU_Status  { gMCU_LastRx = timeNow() / 100000; }
on message OBC_Status  { gOBC_LastRx = timeNow() / 100000; }
on message INV_Status  { gINV_LastRx = timeNow() / 100000; }

// Error frame handler
on errorFrame
{
  gTotalErrors++;
  write("ERROR FRAME detected at time %.3fs! Total errors: %d",
        timeNow() / 1e7, gTotalErrors);
}

on key 's'  // Print status summary
{
  write("=== NETWORK HEALTH SUMMARY ===");
  write("BMS timeouts:     %d", gBMS_Timeout_Count);
  write("MCU timeouts:     %d", gMCU_Timeout_Count);
  write("OBC timeouts:     %d", gOBC_Timeout_Count);
  write("INV timeouts:     %d", gINV_Timeout_Count);
  write("Total errors:     %d", gTotalErrors);
  write("==============================");
}
```

---

## 6.7 CAPL CODING STANDARDS

```
CAPL CODING STANDARDS (OEM Grade):
──────────────────────────────────────────────────────────────
1. NAMING CONVENTIONS:
   Variables: camelCase with prefix
     g = global:    gPackVoltage, gSoC
     l = local:     lTemp, lCounter
     k = constant:  kMAX_VOLTAGE, kPERIOD_MS
   Functions: PascalCase: SendBMSStatus(), CheckFaults()
   Messages:  gMSG prefix: gBMS_Status, gVCU_Command
   Timers:    gXxx_Timer: gBMS_Timer, gPrecharge_Timer

2. FILE HEADER:
   Every .can file must have:
   - Author, date, purpose
   - Version history
   - Related documents (DBC version, ICD version)

3. COMMENTING:
   - Comment all functions with purpose, parameters, returns
   - Comment complex logic
   - Do NOT comment obvious code

4. ERROR HANDLING:
   - Every timed operation must have timeout
   - All write() calls must identify source module
   - Fault injections must always have cleanup

5. MAGIC NUMBERS:
   Never use magic numbers — always use named constants
   BAD:  if (soc > 80.0)
   GOOD: if (soc > kSOC_CHARGE_TAPER_THRESHOLD)

6. INCLUDES:
   Use .cin files (CAPL Include) for shared libraries
   Never duplicate code — create library functions
```

---

## SECTION 6 SUMMARY

CAPL is the automation language for professional EV testing. Master these:

| Skill | Application |
|-------|------------|
| Event handlers | React to messages, timers, keys, signals |
| Message Tx/Rx | Send/receive CAN frames with signal values |
| Timers | Cyclic simulation, timeout detection, sequencing |
| Test cases | Structured test execution with TestStep API |
| Fault injection | Systematic fault stimulation for validation |
| BMS simulation | Simulate complete battery ECU behavior |
| Network monitoring | Detect message loss, timing violations |

---

*Next: Section 7 — Python Automotive Test Automation*
