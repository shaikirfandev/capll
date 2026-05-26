# SECTION 12 — OEM CASE STUDIES
## 10 Real-World EV Powertrain Debugging Scenarios

---

## CASE STUDY 1 — Battery Communication Failure

### 1.1 Problem Statement
**Symptom:** Vehicle on test bench with all ECUs powered. OBD scanner shows VCU-generated DTC P1A00 — "BMS Communication Lost." Customer complaint from pilot production vehicles: vehicle enters limp mode randomly during highway driving.

### 1.2 Initial Investigation

```
CAN Bus Trace Analysis in CANoe:
──────────────────────────────────────────────────────────────
Time      │ ID    │ D0  D1  D2  D3  D4  D5  D6  D7 │ Period
──────────┼───────┼──────────────────────────────────┼────────
00:01.000 │ 0x310 │ 42 01 0C 1A 00 00 00 00 │  10ms
00:01.010 │ 0x310 │ 42 01 0C 1A 00 00 00 00 │  10ms
00:01.020 │ 0x310 │ 42 01 0C 1A 00 00 00 00 │  10ms
00:01.085 │ 0x310 │ 42 01 0C 1A 00 00 00 00 │  65ms ← !!SPIKE!!
00:01.095 │ 0x310 │ 42 01 0C 1A 00 00 00 00 │  10ms
```

**Observation:** BMS_Status (0x310) has a 65ms period spike at 00:01.085 instead of normal 10ms.

### 1.3 Root Cause Analysis

```
INVESTIGATION STEPS:
1. Filter trace to BMS messages only → confirmed intermittent 60-80ms spikes
2. Checked BMS firmware version → 1.2.0 (matches spec)
3. Checked CAN bus load → 35% (acceptable)
4. Reviewed BMS software architecture → found issue:

ROOT CAUSE:
  BMS runs all tasks in a single RTOS task at 10ms priority.
  Every 6 seconds, the BMS performs EEPROM (NVM) write for SoC storage.
  NVM write takes ~50ms blocking time.
  → RTOS task blocked during NVM write
  → CAN transmission delayed by 50ms

TIMELINE:
  t=0ms:    CAN message sent
  t=10ms:   Next CAN message due
  t=10ms:   BMS starts NVM write (every 6s event)
  t=10-60ms: NVM write in progress (CPU blocked)
  t=65ms:   CAN message finally sent (55ms late)
  t=75ms:   Next message sent (10ms after recovery)

WHY VCU TRIGGERS FAULT:
  VCU timeout threshold = 50ms (5 missed messages)
  65ms spike = 5.5 × 10ms = 5.5 messages missed
  → VCU confirms BMS timeout DTC
```

### 1.4 Fix and Verification

```
FIX:
  BMS firmware refactoring:
  1. Move NVM write to dedicated low-priority background task
  2. Use DMA (Direct Memory Access) for NVM write (non-blocking)
  3. Split NVM write into 5ms chunks if DMA not available

VERIFICATION (CANoe trace after fix):
  Maximum BMS_Status period spike: 12ms (2ms jitter, acceptable)
  VCU DTC P1A00 no longer triggered in 24-hour soak test
  JIRA bug: BMS-2023-0847 CLOSED

LESSONS LEARNED:
  - Never perform blocking operations (NVM, flash, I2C) in cyclic CAN tasks
  - Always test edge cases with CAN timing analysis in CANoe
  - Trace window statistics view is key: sort by "Max Period"
```

---

## CASE STUDY 2 — Inverter CAN Timeout

### 2.1 Problem Statement
**Symptom:** Vehicle at -10°C cold start. Vehicle starts, but 3-5 seconds after key-on, inverter reports CAN timeout DTC. Fault clears after warm-up (15 minutes). Only occurs at temperatures below -5°C.

### 2.2 Investigation

```
TEMPERATURE ANALYSIS:
  -10°C cold start trace:
    BMS_Status present immediately ✓
    MCU_Status (0x410) absent for first 4 seconds ✗
    INV_Status appears at T+4.0s → too late for VCU timeout (2s)
    
  +20°C ambient start trace:
    MCU_Status appears at T+0.3s ✓

CAN BUS VOLTAGE ANALYSIS at -10°C:
  Measured using oscilloscope on CAN lines:
  CAN_H idle: 2.5V (correct)
  CAN_L idle: 2.5V (correct)
  CAN_H dominant: 2.1V (should be 3.5V!)
  
  → CAN transceiver not driving to full dominant voltage
```

### 2.3 Root Cause Analysis

```
ROOT CAUSE: CAN transceiver (TJA1044GT) supply voltage issue

POWER SEQUENCE:
  12V LV battery → DC-DC converter → 5V rail → CAN transceiver Vcc
  
  At -10°C, DC-DC converter output: 4.65V (spec minimum = 4.75V)
  CAN transceiver TJA1044 requires Vcc ≥ 4.5V for normal operation
  → At edge case -10°C, transceiver marginal but functional
  
  ACTUAL ROOT CAUSE: Wrong capacitor value on DC-DC converter output
    Specified: 47µF, 25V, X5R ceramic
    Installed: 47µF, 25V, Y5V ceramic
    
    Y5V has severe capacitance derating at low temperature and voltage:
    At -10°C, 47µF Y5V → actual capacitance = ~8µF
    
    Reduced capacitance → DC-DC converter has poor transient response
    → Voltage dips below 4.75V during MCU boot current demand
    → CAN transceiver brownout → MCU can't transmit CAN for 4 seconds

VERIFICATION:
  Replace Y5V with X5R capacitors → DC-DC output stable at 4.92V at -10°C
  MCU CAN appears at T+0.25s consistently
  Cold start validation passed -40°C to +85°C
  
LESSONS LEARNED:
  - Always specify capacitor dielectric type in BOM (never just µF + voltage)
  - X5R or X7R for automotive temperature range
  - Y5V is unacceptable for automotive
  - Test ECUs across full temperature range (-40°C to +125°C)
```

---

## CASE STUDY 3 — Charging Failure Investigation

### 3.1 Problem Statement
**Symptom:** Vehicle with Level 2 AC charging (7.2 kW). 3 out of 50 pilot vehicles reported charging fails at approximately 60-70% SoC and restarts from beginning. Charging cycle can take 8 hours instead of expected 4 hours for full charge.

### 3.2 Investigation

```
CANoe Log Analysis (.blf playback):

Timeline of event:
  T=1:30:00 │ OBC_ChargingPhase = CC (charging at 30A)
  T=1:30:00 │ BMS_SoC = 65.4%
  T=1:30:01 │ BMS_SoC = 65.6%
  T=1:30:02 │ OBC_ChargingPhase = CV (transition to CV — EARLY!)
  T=1:30:05 │ OBC_ChargingCurrent = 28A → 0A (stops suddenly)
  T=1:30:10 │ OBC_FaultCode = 0x04 (Overvoltage fault)
  T=1:30:10 │ VCU_Command::VCU_ChargeEnable = 0 (VCU disables OBC)
  T=1:30:15 │ VCU_Command::VCU_ChargeEnable = 1 (VCU retries)
  T=1:30:20 │ OBC_ChargingPhase = CC (restart from CC)
  T=1:30:20 │ BMS_SoC = 65.6% (SoC same, charging restarted from 0)

ISSUE: OBC triggered self-overvoltage protection
  OBC_ChargingVoltage at fault time: 415.2V
  BMS_MaxChargeVoltage DID: 410.0V
  OBC overvoltage threshold: 415.0V

CLOSE ANALYSIS: Why did OBC reach 415.2V?
  Normal CC operation: VCU sets OBC voltage limit = BMS_MaxChargeVoltage + 5V margin
  Expected: 410.0 + 5 = 415.0V limit in OBC
  
  Signal encoding error found in VCU software:
    VCU_ChargeVoltageLimit is sent in BMS_Limits message
    Signal definition in DBC: scale = 0.5V/bit, offset = 0
    BMS software was sending: physical = 410.0V / 0.5 = 820 raw
    But OBC was decoding: scale = 1V/bit → reading 820V as limit!
    
  WAIT — this would make OBC accept 820V limit, not 415V...
  
  Second look: OBC has a HARD maximum of 415V regardless of VCU command
  OBC_VoltageLimit = min(VCU_commanded, 415V internal limit)
  
  Battery pack voltage at 65% SoC was calculated at 409V
  But actual pack voltage measurement was wrong!

ROOT CAUSE:
  OBC uses BMS_PackVoltage to set its output voltage target.
  BMS_PackVoltage signal has a +2V measurement offset (production calibration issue).
  
  True voltage: 406V
  BMS reports: 408V
  OBC targets: 408V + headroom = 415.5V
  OBC self-protection triggers at 415.0V
  
  The measurement offset exists only on 3 specific BMS hardware variants
  (different precision voltage measurement ICs — incoming inspection missed this)
```

### 3.3 Fix

```
IMMEDIATE FIX: BMS software calibration correction for affected units
  - New BMS calibration to correct +2V offset
  - OTA update deployed to affected vehicles
  
LONG-TERM FIX:
  - Tighten incoming inspection for BMS voltage measurement accuracy
  - Add OBC tolerance to handle ±3V pack voltage offset
  - OBC soft limit: 412V (not 415V) for more margin

JIRA: OBC-2023-1122 RESOLVED
AFFECTED: 3 units → hardware calibration applied at dealer
```

---

## CASE STUDY 4 — Vehicle Not Waking Up

### 4.1 Problem Statement
**Symptom:** After a fleet vehicle was parked for 7 days (normal operation), it could not be unlocked via key fob. Jump-starting via 12V external power restored function. DTC read: "LV Battery Undervoltage" stored in BCM and BMS.

### 4.2 Investigation

```
12V BATTERY DRAIN ANALYSIS:

Expected 12V quiescent current: < 5mA (sleep state)
Measured quiescent current: 45mA

45mA × 24h × 7 days = 7.56 Ah consumed
Battery capacity: 40 Ah → starting from 100% → 81% remaining
At 81%, 12V should still work... 

But measured: only 10.2V on 12V bus after 7 days
→ Higher drain than expected + battery may be degraded

CAN BUS SLEEP ANALYSIS:
  Using CANalyzer trace recorded over 2 hours after key-off:
  
  T+0s:   Key-off, VCU sends Sleep command on CAN
  T+2s:   All ECUs should enter sleep
  T+2s:   CAN traffic drops to 0 (expected)
  T+2s:   ...
  T+2s:   Wait...
  T+15s:  Single CAN frame appears! 0x1FF (unknown ID in DBC)
  T+25s:  0x1FF appears again
  T+35s:  0x1FF appears again  
  → CAN frame 0x1FF every 10 seconds — this is keeping CAN bus active!
  → All ECUs in network detection mode (CAN receivers active)
  → Collective quiescent current elevated

MYSTERIOUS ID 0x1FF:
  DBC lookup: not defined in current vehicle DBC
  Compare to older project DBC: 0x1FF = TestBench_Heartbeat
  → This was a development test message
  → Still present in production firmware of... (checking ECU ID)
  → VIN-decoding service response: INFOTAINMENT_ECU, firmware v2.0.1
  
ROOT CAUSE:
  Infotainment ECU v2.0.1 has a development artifact:
  "CAN keep-alive heartbeat" feature was enabled for bench testing
  Feature was not removed before production release
  Infotainment ECU sends 0x1FF every 10 seconds indefinitely after key-off
  This prevents other ECUs from entering deep sleep
  
POWER CONSUMPTION CALCULATION:
  Normal CAN receiver: ~2mA per ECU
  12 ECUs in network detection mode instead of sleep: ~24mA extra
  + Infotainment ECU fully awake: +15mA
  = ~39mA excess → matches measured 45mA (±5mA measurement error)
```

### 4.3 Resolution

```
FIX:
  Infotainment firmware v2.0.2: remove CAN keepalive
  OTA update pushed to all affected vehicles
  
VERIFICATION:
  Post-update: quiescent current = 3.2mA (within spec < 5mA)
  7-day park test: 12V battery at 94% (expected ~97%, small degradation ok)

LESSONS LEARNED:
  - Always audit CAN network for undocumented message IDs before production
  - CANalyzer "Unknown Frame" alarm helps catch this during system testing
  - Quiescent current measurement is mandatory in release gate
  - Debug/development features must be feature-flagged and disabled in production
```

---

## CASE STUDY 5 — CAN Bus Overload

### 5.1 Problem Statement
**Symptom:** During ADAS feature development integration testing, adding 3 new ADAS ECUs (cameras, radar, lidar fusion) caused intermittent DTC errors across multiple existing ECUs. Pattern: errors appear only when all ADAS systems active simultaneously.

### 5.2 Investigation

```
BUS LOAD MEASUREMENT in CANoe:
  Normal EV operation: 35% bus load
  With ADAS active:    91% bus load ← CRITICAL!
  
  At 91% CAN bus load:
  - Message arbitration delays increase
  - High-priority messages still OK
  - Lower-priority messages experience 50-200ms delays
  - Some messages miss deadline → timeout DTCs
  
ADAS MESSAGE ANALYSIS:
  Camera fusion:    5ms cycle, 64 bytes CAN FD = 480 bits × 200Hz = 96 kbits/s
  Radar object:     10ms cycle, 48 bytes × 100Hz = 48 kbits/s  
  Lidar summary:    20ms cycle, 64 bytes × 50Hz = 32 kbits/s
  Total ADAS:       176 kbits/s on 1 Mbit/s bus = 17.6% bus load
  
  Wait — these are CAN FD messages on standard CAN 2.0B bus!
  
ROOT CAUSE:
  Network architect specified CAN FD for ADAS messages (fast data, 8 Mbit/s)
  BUT: ADAS ECUs were integrated on the Powertrain CAN bus (CAN 2.0B, 500 kbps!)
  
  CAN FD frames have:
  - Longer bit timing due to larger payloads
  - On a 500 kbps bus, 64-byte CAN FD frame: 
    Header: ~47 bits at 500 kbps = 94µs
    Data phase: 64 bytes × 8 bits = 512 bits at 500 kbps = 1024µs
    Total: ~1.1ms per frame
    
  ADAS ECUs sending at 200Hz × 1.1ms = 22% bus time per ECU
  All 3 ADAS ECUs: 66% of bus time
  
  Existing powertrain messages pushed out by ADAS → excessive delays
```

### 5.3 Resolution

```
FIX:
  ADAS ECUs moved to dedicated Ethernet backbone (1000BASE-T1, 1 Gbit/s)
  Gateway ECU bridges safety-critical ADAS data to Powertrain CAN (summarized)
  
NETWORK TOPOLOGY AFTER FIX:
  Powertrain CAN (500 kbps): BMS, VCU, MCU, OBC, DCDC
  ADAS Ethernet (1000BASE-T1): Camera, Radar, Lidar fusion, ADAS ECU
  Gateway ECU: translates critical ADAS alerts → CAN (1 message, 20ms)

LESSONS LEARNED:
  - Bus load analysis must include worst-case burst scenarios
  - Network architecture review required before adding new ECUs
  - CAN FD and classic CAN cannot share bus at different data rates
  - ADAS requires Automotive Ethernet (100BASE-T1 or 1000BASE-T1)
```

---

## CASE STUDY 6 — Thermal Protection Activation

### 6.1 Problem Statement
**Symptom:** Vehicle during performance testing (0-100 km/h acceleration runs) reports thermal protection DTC after 4th consecutive launch. Drive torque limited to 20% after 4th run. System clears after 30-minute rest.

### 6.2 Investigation

```
DATA ANALYSIS FROM TEST LOG:
  Run 1: Max INV_IGBTTemperature = 118°C, Motor = 85°C, Power = 165 kW
  Run 2: Max INV_IGBTTemperature = 131°C, Motor = 90°C, Power = 165 kW
  Run 3: Max INV_IGBTTemperature = 142°C, Motor = 93°C, Power = 165 kW
  Run 4: At T+3s, INV_IGBTTemperature = 151°C → Derating to 20%
  
  Rest period: IGBT temperature recovers to 60°C in 30 minutes
  
  CAN signals during derating:
    VCU_MaxTorqueLimit decreases from 400Nm to 80Nm (20%)
    INV_ActualTorque follows VCU limit
    VCU_PowertrainMode = DERATING (mode 3)

THERMAL MODEL ANALYSIS:
  IGBT thermal impedance: Rth(j-c) = 0.15°C/W (junction-to-case)
  Heatsink thermal impedance: Rth(c-h) = 0.05°C/W
  Cooling thermal resistance to coolant: Rth(h-coolant) = 0.10°C/W
  
  At 165 kW with 2% IGBT losses: P_IGBT = 3300W
  Thermal rise = 3300W × (0.15+0.05+0.10) = 3300 × 0.30 = 990°C above coolant
  
  Wait — that can't be right (coolant at 50°C → junction at 1040°C?)
  
  Re-check: 165 kW total power, 3-phase inverter:
  Switch losses per device (6 IGBTs): 165 kW × 2% / 6 = 550W per IGBT
  
  Thermal rise = 550W × 0.30 = 165°C above coolant
  
  If coolant at 50°C: junction = 50 + 165 = 215°C
  Maximum IGBT rating: 175°C junction
  
  Thermal protection at 150°C makes sense — it triggers before damage.

ROOT CAUSE:
  Coolant temperature during consecutive runs was not recovering fast enough.
  Coolant pump nominal flow: 12 L/min
  Measured flow during test: 8 L/min (pump degraded, impeller cracked)
  
  At 8 L/min instead of 12 L/min: 33% reduced cooling capacity
  → Coolant temperature rising from 50°C to 78°C over 4 runs
  → Higher coolant = higher IGBT junction temperature = earlier protection trigger
  
  SECONDARY ISSUE: Coolant pump health monitoring not implemented
```

### 6.3 Resolution

```
IMMEDIATE: Replace cracked coolant pump impeller
LONG-TERM: 
  - Add coolant flow sensor to validate pump operation
  - Add coolant pump health DTC if flow < 10 L/min during operation
  - Thermal model in VCU to predict derating early → smoother driver experience

VERIFICATION:
  4 consecutive runs after fix: Max IGBT temp = 138°C (no derating, within spec)
  Coolant flow measured: 11.8 L/min (within ±2% of spec)
```

---

## CASE STUDY 7 — Regen Braking Malfunction

### 7.1 Problem Statement
**Symptom:** Fleet vehicle reported: "Vehicle not decelerating as expected when lifting throttle." Customer complaint from high-SOC scenario. CANoe data requested from fleet data logger.

### 7.2 Investigation

```
CAN DATA ANALYSIS (fleet log playback):
  Condition: SoC = 96%, gentle throttle lift at 80 km/h
  
  Expected: BMS allows 0.2C regen (5 kW at SoC=96%)
  Actual: No regen braking at all

SIGNAL TRACE:
  VCU_RegenTorqueRequest = -80 Nm (driver intent = decelerate)
  BMS_ChargePowerLimit = 0.0 W ← BMS said no charging allowed!
  INV_RegenTorqueActual = 0 Nm (inverter following BMS limit)
  
  BMS_ChargePowerLimit = 0 only at SoC > 97% or cell overvoltage

  But BMS_SoC = 96%... so why is BMS limiting to 0W?

DETAILED CELL VOLTAGE ANALYSIS:
  BMS_MaxCellVoltage = 4.218V (from DID 0xF115)
  OV limit = 4.200V
  BMS_SoC = 96% (pack average)
  
  Max cell is at 4.218V = already OVER single-cell OV threshold!
  BMS correctly stopped charging to prevent further overvoltage.
  
ROOT CAUSE:
  Cell imbalance in battery pack.
  Pack average SoC = 96% (4.17V average)
  But highest cells already at 4.22V (0.05V above average = 2% SoC imbalance)
  
  Battery was not balanced during previous charge:
  - Balancing only runs during charging at TOP of charge (CV phase)
  - Previous charge was interrupted at 97% (user unplugged early)
  - Balancing never ran long enough to equalize high-voltage cells
  - Result: 2% SoC spread between best and worst cells
  
  When pack hits 96% average, some cells at 4.22V → BMS stops regen
```

### 7.3 Resolution

```
FIX:
  1. BMS software: increase balancing aggressiveness during charging
  2. BMS software: enable passive balancing during driving (not just charging)
     - When max-min cell voltage difference > 30mV → start balancing
     - During regen events: limit regen in affected modules only

DRIVER EXPERIENCE FIX:
  VCU: When BMS regen limit = 0 due to high SoC:
  - Apply friction brake blend to maintain expected deceleration feel
  - Display "High SoC — reduced regen" in cluster (not just silent failure)

LESSONS LEARNED:
  - Cell imbalance directly affects regen braking availability
  - SoC alone is insufficient to predict regen capability
  - Must check both pack average AND individual cell voltage limits
  - Fleet data logging is essential for field issue diagnosis
```

---

## CASE STUDY 8 — Intermittent DTC

### 8.1 Problem Statement
**Symptom:** BMS DTC "P0A80 — Battery System Degraded" appears intermittently. Cannot be reproduced in workshop. Occurs in cold weather. No permanent DTC recorded. Customer extremely dissatisfied.

### 8.2 Investigation

```
DTC ANALYSIS:
  P0A80 = BMS_SoH (State of Health) below threshold
  DTC status: pendingDTC (bit 2) only — never becomes confirmed
  
  This means: fault detected once in one drive cycle, but not in next
  → Intermittent / borderline condition

  DTC extended data record (0x19 06):
  Occurrence counter: 47 times
  Last occurrence: odometer 15,234 km
  Last temperature: -8°C (encoded in extended record)
  
FIELD DATA CORRELATION:
  Cross-reference DTC occurrence vs. temperature:
  All 47 occurrences recorded when battery temperature < -5°C
  Zero occurrences above +5°C
  
  Battery age: 15,234 km / expected capacity loss: ~2% (negligible)
  
  SoH calculation formula (from BMS specification):
    SoH = (Measured_Capacity / Rated_Capacity) × 100%
    SoH threshold for DTC: < 85%

COLD TEMPERATURE ANALYSIS:
  BMS SoH capacity measurement algorithm:
  Step 1: Discharge from 100% to 10% at C/10 rate
  Step 2: Measure total Ah discharged
  Step 3: Calculate SoH
  
  PROBLEM: At -8°C, battery internal resistance increases 3× vs 25°C
  At high discharge rates, voltage drops faster → BMS cuts off at 10% SoC
  But BMS reached the 10% cutoff FASTER due to voltage sag — not actual SoC
  BMS incorrectly interprets voltage cutoff as depleted capacity
  → BMS calculates SoH = 76% (at -8°C) vs actual SoH = 96% (at 25°C)
  → Temperature-induced false SoH reading
  
ROOT CAUSE:
  BMS SoH measurement algorithm lacks temperature compensation.
  Must compensate for internal resistance at different temperatures.
  BMS only measures SoH at reference temperature (25°C) in spec.
  But fleet vehicles ran SoH measurement in cold conditions.
```

### 8.3 Resolution

```
FIX:
  BMS SoH algorithm: only run capacity measurement when T ≥ 15°C
  If temperature < 15°C: use last known SoH from NVM
  Add temperature condition check before SoH evaluation

VERIFICATION:
  Lab test: SoH measurement repeated at -10°C, 0°C, 15°C, 25°C
  After fix: SoH measurement suppressed below 15°C
  No false P0A80 DTC in cold test (-30°C to +15°C chamber)
  
LESSONS LEARNED:
  - Extended DTC data (occurrence counter, conditions) is CRITICAL for field bugs
  - Always correlate DTCs with environmental conditions (temp, altitude, speed)
  - Algorithm validation must include temperature extremes, not just 25°C
```

---

## CASE STUDY 9 — HV Interlock Failure

### 9.1 Problem Statement
**Symptom:** After a minor collision (small bump), vehicle cannot be restarted. All warning lights on. Fire brigade on scene reports no visible damage. DTC: "HV Interlock Open."

### 9.2 Investigation

```
HVIL CIRCUIT ANALYSIS:
  HV Interlock Loop (HVIL) traces through:
  1. VCU connector (12-pin HV interface)
  2. BMS HV connector (main battery)
  3. Inverter HV connector
  4. OBC HV connector  
  5. PDU internal wiring
  
  Any connector dislodging opens the loop → immediate HV shutdown

PHYSICAL INSPECTION:
  Technician checks all HV connectors → all properly seated
  
  But wait — HVIL still shows OPEN in DTC
  
  Check HVIL with multimeter:
  Junction 1 (VCU): continuity ✓
  Junction 2 (BMS): continuity ✓
  Junction 3 (Inverter): continuity ✓
  Junction 4 (OBC): OPEN CIRCUIT ✗
  
  OBC HV connector fully seated but HVIL pin open!
  
  Inspecting OBC connector more carefully:
  HVIL pin shows contact fretting (micro-movement wear)
  OBC was located directly in the vehicle's crumple zone
  
  Even though no visible damage, micro-vibrations during collision caused
  temporary contact separation → HVIL opened → HV shut down → 
  HVIL restored → but DTC already confirmed and requires workshop clear

ROOT CAUSE:
  Collision-triggered vibration (vehicle at ~15 km/h bump)
  OBC mounting position in crumple zone amplified vibration
  HVIL connector fretting → momentary open circuit
  This is actually CORRECT safety behavior — HV disabled on HVIL break
  
DESIGN ISSUE:
  OBC should not be mounted in primary crumple zone
  HV connectors should have anti-fretting contact material (gold plating)
```

### 9.3 Resolution

```
IMMEDIATE: 
  - Confirm no actual damage, clear DTC, restart vehicle
  - Inspect HVIL connector contacts for fretting damage
  - Replace OBC connector if contacts show wear marks

LONG-TERM DESIGN FIX (engineering change request):
  1. Relocate OBC to protected zone (behind firewall)
  2. Upgrade HVIL connector contacts to gold-plated (AuPdAg alloy)
  3. Add vibration analysis to OBC mounting design review

LESSON:
  HV shutdown on HVIL break is CORRECT safety behavior.
  Post-collision restart requires workshop inspection (by design).
  Vibration-sensitive safety systems must be mounted in protected areas.
```

---

## CASE STUDY 10 — Vehicle Cannot DC Fast Charge

### 10.1 Problem Statement
**Symptom:** Customer reports: vehicle charges fine on home AC Level 2 charger, but fails at multiple DC fast chargers. OBD shows DTC "ISO 15118 Communication Timeout."

### 10.2 Investigation

```
ISO 15118 NETWORK TRACE ANALYSIS:
  PLC (Power Line Communication) network captured with specialized tool:
  
  EVCC sends: SLAC (Signal Level Attenuation Characterization) request
  → No response from SECC (DCFC station)
  
  SLAC is the physical layer pairing protocol for HomePlug GreenPHY
  SLAC failure → PLC session never established → 15118 never starts
  
SIGNAL ANALYSIS:
  CP line voltage waveform at vehicle inlet:
  CP high: +11.8V (spec: +12V ±0.5V — marginal but within tolerance)
  CP low:  -11.9V (spec: -12V ±0.5V — OK)
  PWM freq: 1001 Hz (spec: 1000Hz ±5% — OK)
  
  PLC signal on CP line:
  TX signal level: -15 dBV (spec minimum: -10 dBV)
  → PLC signal too weak!

VEHICLE PLC COUPLER ANALYSIS:
  PLC modem in vehicle: NXP FS32 chip
  PLC coupling circuit: capacitor + transformer coupling to CP line
  
  Measuring coupling impedance:
  Expected coupling capacitor: 100 nF, 630V
  Installed: 100 nF, 630V
  Measured capacitance: 12 nF
  
  CAP DEGRADED: 88% capacitance loss
  → PLC coupling amplitude reduced
  → PLC signal -15 dBV instead of -5 dBV
  
ROOT CAUSE:
  PLC coupling capacitor (100nF X2 class) degraded.
  Likely cause: repeated voltage stress from CP voltage spikes.
  
  CP line voltage spikes from EVSE connection/disconnection:
  Spec: < 1kV for 1µs transient
  Measured peak: 1.4kV (EVSE with poor transient suppression)
  
  Repeated overvoltage → capacitor dielectric stress → capacitance degraded

ADDITIONAL ROOT CAUSE:
  Capacitor specified was X2 class (440V RMS max for continuous operation)
  But CP has 1kV transients → should use X1 class (760V RMS) or higher rating
  This is a design deficiency in the coupling circuit
```

### 10.3 Resolution

```
IMMEDIATE: Replace PLC coupling capacitor (workshop fix)
  → Capacitor changed: 100nF X1 class, 1200V DC
  → DC fast charging works on all tested stations

PRODUCTION FIX: Change coupling capacitor to 100nF, 1200V DC, X1 class
  → ECN (Engineering Change Notice) issued
  → All vehicles in production updated
  → Service bulletin issued for field vehicles

TESTING ADDED:
  PLC coupling test added to OBC end-of-line test
  Measurement: PLC amplitude must be > -8 dBV on CP line
  
LESSONS LEARNED:
  - PLC coupling components must withstand CP line transients
  - Capacitor voltage rating must account for worst-case spikes
  - AC voltage rating ≠ transient spike rating
  - DC fast charging failures often trace to PLC/CP circuit issues
  - Add PLC signal level to diagnostic DID for field serviceability
```

---

## CASE STUDY SUMMARY

| Case | Component | Root Cause | Key Tool | Resolution |
|------|-----------|-----------|----------|------------|
| 1 | BMS CAN | NVM write blocking CAN task | CANoe timing | Async NVM write |
| 2 | Inverter startup | Y5V cap derating at -10°C | Oscilloscope + CAN trace | X5R cap replacement |
| 3 | OBC charging | Voltage offset calibration | CANoe log analysis | BMS recalibration |
| 4 | Vehicle wakeup | Debug CAN message in production | CANalyzer frame filter | Firmware fix, OTA |
| 5 | Bus overload | ADAS on wrong network | CANoe bus load | Network redesign |
| 6 | Thermal protection | Degraded coolant pump | Thermal data + flow sensor | Pump replacement |
| 7 | Regen braking | Cell imbalance | Fleet data + cell voltage | Balancing algorithm |
| 8 | Intermittent DTC | SoH algorithm not temp-compensated | DTC extended data | Temperature gate |
| 9 | HVIL fault | Connector fretting in collision | Physical inspection | Relocation + gold contacts |
| 10 | DC fast charge | PLC capacitor degraded | PLC signal analyzer | Capacitor upgrade |

---

*Next: Section 13 — Test Case Library*
