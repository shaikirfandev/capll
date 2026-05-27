# Module 04 — Manual DBC Creation from Communication Matrix

> **Level**: Intermediate  
> **Duration**: ~4 hours  
> **Goal**: Build a complete production-level DBC file from scratch by hand, step by step.

---

## 4.1 Overview — The Manual DBC Creation Process

```
STEP 1:  Analyze communication matrix
STEP 2:  Set up DBC file header
STEP 3:  Define bus units (ECU nodes)
STEP 4:  Create CAN messages (BO_ blocks)
STEP 5:  Define signals (SG_ lines)
STEP 6:  Calculate and verify bit positions
STEP 7:  Add value tables (VAL_)
STEP 8:  Add attributes (BA_DEF_ / BA_)
STEP 9:  Add comments (CM_)
STEP 10: Validate DBC
```

---

## 4.2 Working Example — ADAS Safety Bus

### Input: Communication Matrix Extract

We will build a DBC for the ADAS Safety CAN bus with the following ECUs and messages:

| ECU | Role |
|-----|------|
| AEB_ECU | Radar-based emergency braking |
| ABS_ECU | Anti-lock braking system |
| ECM | Engine control module |
| EPS_ECU | Electric power steering |
| BCM | Body control module |
| IPC | Instrument panel cluster |
| CGW | Central gateway |

**Messages:**

| # | Message | ID | DLC | Cycle | Tx ECU |
|---|---------|----|----|-------|--------|
| 1 | WheelSpeed | 0x200 | 8 | 10ms | ABS_ECU |
| 2 | AEB_Req | 0x244 | 8 | 20ms | AEB_ECU |
| 3 | VehicleStatus | 0x300 | 8 | 10ms | ECM |
| 4 | EPS_Status | 0x380 | 4 | 20ms | EPS_ECU |
| 5 | IPC_Display | 0x350 | 8 | 100ms | IPC |
| 6 | BCM_Status | 0x420 | 6 | 100ms | BCM |

---

## 4.3 STEP 1 — Analyze Communication Matrix

Before writing a single line of DBC, complete these checks:

### Checklist

```
□ List all message IDs — check for duplicates
□ Verify all Tx ECU names are consistent (spelling, underscore vs dash)
□ For each signal: confirm start_bit + length never exceeds DLC×8
□ Identify all signed signals (temperature, acceleration, current)
□ Note all enum signals (need VAL_ entries)
□ Identify safety-critical messages (need cycle time attributes)
□ Note event-triggered messages (cycle = 0 in attributes)
□ Check for multiplexed messages
```

### Signal Bit Range Validation Table

| Message | Signal | Start | Length | End Bit | OK? |
|---------|--------|-------|--------|---------|-----|
| AEB_Req (DLC=8, max=63) | AEB_Active | 0 | 1 | 0 | ✅ |
| | AEB_State | 1 | 3 | 3 | ✅ |
| | AEB_Decel_Req | 4 | 8 | 11 | ✅ |
| | AEB_Obj_Distance | 12 | 16 | 27 | ✅ |
| | AEB_TTC | 28 | 8 | 35 | ✅ |
| | Alive_Counter | 36 | 4 | 39 | ✅ |
| | CRC_AEB | 40 | 8 | 47 | ✅ |
| | Reserved | 48 | 16 | 63 | ✅ |
| **Total** | | | **64 bits** | ≤64 | ✅ |

---

## 4.4 STEP 2 — DBC File Header

Start every DBC with:

```
VERSION ""

NS_ :
  NS_DESC_
  CM_
  BA_DEF_
  BA_DEF_DEF_
  BA_
  BA_DEF_SGTYPE_
  BA_SGTYPE_
  SIG_TYPE_REF_
  VAL_DEF_
  VAL_
  CAT_DEF_
  CAT_
  FILTER
  BA_DEF_DEF_REL_
  BA_DEF_REL_
  BA_REL_
  BU_SG_REL_
  BU_EV_REL_
  BU_BO_REL_
  SG_MUL_VAL_

BS_:
```

---

## 4.5 STEP 3 — Define Bus Units

List every ECU and the special `Vector__XXX` placeholder:

```
BU_: AEB_ECU ABS_ECU ECM EPS_ECU IPC BCM CGW Vector__XXX
```

---

## 4.6 STEP 4 & 5 — Create Messages and Signals

### Message 1: WheelSpeed (ID=0x200=512)

Signal packing (Intel, DLC=8):
```
Bits 0–15:  WheelSpeed_FL  (16 bits)
Bits 16–31: WheelSpeed_FR  (16 bits)
Bits 32–47: WheelSpeed_RL  (16 bits)
Bits 48–63: WheelSpeed_RR  (16 bits)
```

```
BO_ 512 WheelSpeed: 8 ABS_ECU
 SG_ WheelSpeed_FL : 0|16@1+  (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM,EPS_ECU
 SG_ WheelSpeed_FR : 16|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM,EPS_ECU
 SG_ WheelSpeed_RL : 32|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM
 SG_ WheelSpeed_RR : 48|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM
```

**Manual Calculation Check:**
```
WheelSpeed_FL:
  Start bit = 0, Length = 16
  Occupies bits 0–15 → Bytes 0–1 ✅

WheelSpeed_FR:
  Start bit = 16, Length = 16
  Occupies bits 16–31 → Bytes 2–3 ✅

Max bit = 63 = DLC × 8 - 1 = 63 ✅ Exactly fits!
```

---

### Message 2: AEB_Req (ID=0x244=580)

Signal layout visualization:
```
Byte:   |    B0    |    B1    |    B2    |    B3    |    B4    |    B5    |    B6    |    B7    |
Bit:    |76543210  |76543210  |76543210  |76543210  |76543210  |76543210  |76543210  |76543210  |
         ↑↑↑                                          ↑↑↑↑     ↑↑↑↑↑↑↑↑
         |||AEB_Decel (bits 4-11)                    Alive    CRC_AEB (40-47)
         ||AEB_State (bits 1-3)
         |AEB_Active (bit 0)

         [          AEB_Obj_Distance (bits 12-27)         ][AEB_TTC (bits 28-35)]
```

```
BO_ 580 AEB_Req: 8 AEB_ECU
 SG_ AEB_Active       : 0|1@1+  (1,0)    [0|1]       ""      CGW,IPC,BCM
 SG_ AEB_State        : 1|3@1+  (1,0)    [0|7]       ""      CGW,IPC,BCM
 SG_ AEB_Decel_Req    : 4|8@1+  (0.1,0)  [0|25.5]    "m/s2"  CGW,IPC,ECM
 SG_ AEB_Obj_Distance : 12|16@1+ (0.01,0) [0|655.35]  "m"     CGW,IPC
 SG_ AEB_TTC          : 28|8@1+  (0.01,0) [0|2.55]    "s"     CGW,IPC
 SG_ Alive_Ctr_AEB    : 36|4@1+  (1,0)    [0|14]      ""      CGW,IPC
 SG_ CRC_AEB          : 40|8@1+  (1,0)    [0|255]     ""      CGW,IPC
 SG_ Reserved_AEB     : 48|16@1+ (1,0)    [0|65535]   ""      Vector__XXX
```

---

### Message 3: VehicleStatus (ID=0x300=768)

Signal layout (mixed signal types — note signed EngineTemp):
```
Bits  0–15: EngineSpeed     (16-bit unsigned, 0.25 rpm/bit)
Bits 16–23: ThrottlePos     (8-bit unsigned, 0.4 %/bit)
Bits 24–31: EngineTemp      (8-bit SIGNED, 0.5°C/bit, offset -40)
Bits 32–34: EngineState     (3-bit unsigned, enum)
Bits 35–37: TransmMode      (3-bit unsigned, enum)
Bits 38–47: FuelPress       (10-bit unsigned, 0.1 bar/bit)
Bits 48–51: Alive_Ctr_VS   (4-bit unsigned)
Bits 52–59: CRC_VS          (8-bit unsigned)
Bits 60–63: Reserved
```

```
BO_ 768 VehicleStatus: 8 ECM
 SG_ EngineSpeed   : 0|16@1+  (0.25,0)   [0|16383.75]   "rpm"  AEB_ECU,IPC,ABS_ECU,CGW
 SG_ ThrottlePos   : 16|8@1+  (0.4,0)    [0|100]        "%"    AEB_ECU,IPC
 SG_ EngineTemp    : 24|8@1-  (0.5,-40)  [-40|87.5]     "degC" IPC,BCM
 SG_ EngineState   : 32|3@1+  (1,0)      [0|6]          ""     AEB_ECU,IPC,BCM,CGW
 SG_ TransmMode    : 35|3@1+  (1,0)      [0|5]          ""     IPC,BCM
 SG_ FuelPress     : 38|10@1+ (0.1,0)    [0|102.3]      "bar"  IPC
 SG_ Alive_Ctr_VS  : 48|4@1+  (1,0)      [0|14]         ""     AEB_ECU,IPC,CGW
 SG_ CRC_VS        : 52|8@1+  (1,0)      [0|255]        ""     AEB_ECU,IPC,CGW
```

---

### Message 4: EPS_Status (ID=0x380=896, DLC=4)

```
BO_ 896 EPS_Status: 4 EPS_ECU
 SG_ SteeringAngle : 0|16@1-  (0.1,-3276.8) [-3276.8|3276.7] "deg"    AEB_ECU,IPC,CGW
 SG_ SteeringTorque: 16|10@1- (0.01,-5.12)  [-5.12|5.11]     "Nm"     IPC
 SG_ EPS_State     : 26|3@1+  (1,0)          [0|7]            ""       IPC,CGW,BCM
 SG_ EPS_Warning   : 29|1@1+  (1,0)          [0|1]            ""       IPC,BCM
 SG_ Alive_Ctr_EPS : 30|2@1+  (1,0)          [0|3]            ""       AEB_ECU
```

**Signed signal verification:**
```
SteeringAngle — 16-bit signed, Factor=0.1, Offset=-3276.8
  Physical_min = -32768 × 0.1 + (-3276.8) = -3276.8 - 3276.8 = -6553.6 (exceeds spec!)
  
Wait — re-check:
  Correct interpretation: Factor=0.1 applies first, then offset
  Physical = raw × factor + offset
  raw=-32768: physical = -32768 × 0.1 + (-3276.8) = -3276.8 + (-3276.8) = -6553.6
  
  That doesn't match range -3276.8 to 3276.7
  
Correct approach: to get range -3276.8 to 3276.7 with 16-bit signed:
  At raw=0: physical = 0 × 0.1 + 0 = 0 (centered at 0)
  At raw=-32768: physical = -32768 × 0.1 = -3276.8 ✓
  At raw=32767: physical = 32767 × 0.1 = 3276.7 ✓
  So: Factor=0.1, Offset=0
  
CORRECTED:
 SG_ SteeringAngle : 0|16@1- (0.1,0) [-3276.8|3276.7] "deg" AEB_ECU,IPC,CGW
```

---

### Message 5: IPC_Display (ID=0x350=848, DLC=8)

```
BO_ 848 IPC_Display: 8 IPC
 SG_ Display_Speed    : 0|12@1+  (0.1,0)   [0|409.5]  "km/h" CGW
 SG_ Display_RPM      : 12|14@1+ (0.5,0)   [0|8191.5] "rpm"  CGW
 SG_ Display_Fuel_Pct : 26|8@1+  (0.5,0)   [0|127.5]  "%"    CGW
 SG_ Display_Gear     : 34|4@1+  (1,0)     [0|9]       ""     CGW
 SG_ MIL_On           : 38|1@1+  (1,0)     [0|1]       ""     CGW
 SG_ ABS_Warning      : 39|1@1+  (1,0)     [0|1]       ""     CGW
 SG_ EPS_Warning_Disp : 40|1@1+  (1,0)     [0|1]       ""     CGW
 SG_ Door_Ajar_Any    : 41|1@1+  (1,0)     [0|1]       ""     CGW
 SG_ Alive_Ctr_IPC    : 48|4@1+  (1,0)     [0|14]      ""     CGW
 SG_ CRC_IPC          : 52|8@1+  (1,0)     [0|255]     ""     CGW
```

---

### Message 6: BCM_Status (ID=0x420=1056, DLC=6)

```
BO_ 1056 BCM_Status: 6 BCM
 SG_ DoorFL_Status  : 0|2@1+  (1,0) [0|3]  "" CGW,IPC,AEB_ECU
 SG_ DoorFR_Status  : 2|2@1+  (1,0) [0|3]  "" CGW,IPC
 SG_ DoorRL_Status  : 4|2@1+  (1,0) [0|3]  "" CGW,IPC
 SG_ DoorRR_Status  : 6|2@1+  (1,0) [0|3]  "" CGW,IPC
 SG_ Hood_Status    : 8|1@1+  (1,0) [0|1]  "" CGW,IPC
 SG_ Trunk_Status   : 9|1@1+  (1,0) [0|1]  "" CGW,IPC
 SG_ IgnitionState  : 10|3@1+ (1,0) [0|4]  "" CGW,IPC,AEB_ECU
 SG_ HazardActive   : 13|1@1+ (1,0) [0|1]  "" CGW,IPC
 SG_ LowBeam        : 14|1@1+ (1,0) [0|1]  "" CGW,IPC
 SG_ HighBeam       : 15|1@1+ (1,0) [0|1]  "" CGW,IPC
 SG_ WiperState     : 16|3@1+ (1,0) [0|4]  "" CGW,IPC
 SG_ Alive_Ctr_BCM  : 40|4@1+ (1,0) [0|14] "" CGW,IPC
 SG_ CRC_BCM        : 44|8@1+ (1,0) [0|255] "" CGW,IPC
```

---

## 4.7 STEP 6 — Calculate and Verify Bit Positions

### Bit-Level Visualization Tool

Use this formula to verify no signal overlap:

```
For each signal: occupied_bits = {start_bit, start_bit+1, ..., start_bit+length-1}
Signal overlap check: no two signals share any bit number

Verification for BCM_Status (DLC=6, bits 0–47):
Signal          Start  Len   Bits Used
DoorFL_Status   0      2     {0,1}
DoorFR_Status   2      2     {2,3}
DoorRL_Status   4      2     {4,5}
DoorRR_Status   6      2     {6,7}
Hood_Status     8      1     {8}
Trunk_Status    9      1     {9}
IgnitionState   10     3     {10,11,12}
HazardActive    13     1     {13}
LowBeam         14     1     {14}
HighBeam        15     1     {15}
WiperState      16     3     {16,17,18}
                            [Bits 19–39 unused]
Alive_Ctr_BCM   40     4     {40,41,42,43}
CRC_BCM         44     8     {44,45,46,47}

Total used: 2+2+2+2+1+1+3+1+1+1+3+4+8 = 31 bits out of 48 max ✅
No overlaps ✅
```

---

## 4.8 STEP 7 — Add Value Tables

```
VAL_ 580 AEB_State
  0 "OFF"
  1 "STANDBY"
  2 "WARNING"
  3 "ACTIVE"
  4 "FAULT"
  5 "DEGRADED"
  6 "OVERRIDE"
  7 "NOT_AVAILABLE" ;

VAL_ 768 EngineState
  0 "OFF"
  1 "CRANKING"
  2 "IDLE"
  3 "RUNNING"
  4 "OVERHEATING"
  5 "SHUTDOWN"
  6 "FAULT" ;

VAL_ 768 TransmMode
  0 "PARK"
  1 "REVERSE"
  2 "NEUTRAL"
  3 "DRIVE"
  4 "SPORT"
  5 "MANUAL" ;

VAL_ 1056 BCM_Status DoorFL_Status  0 "CLOSED" 1 "OPEN" 2 "AJAR" 3 "NOT_AVAILABLE" ;
VAL_ 1056 BCM_Status DoorFR_Status  0 "CLOSED" 1 "OPEN" 2 "AJAR" 3 "NOT_AVAILABLE" ;
VAL_ 1056 BCM_Status DoorRL_Status  0 "CLOSED" 1 "OPEN" 2 "AJAR" 3 "NOT_AVAILABLE" ;
VAL_ 1056 BCM_Status DoorRR_Status  0 "CLOSED" 1 "OPEN" 2 "AJAR" 3 "NOT_AVAILABLE" ;
VAL_ 1056 BCM_Status IgnitionState  0 "OFF" 1 "ACC" 2 "ON" 3 "START" 4 "NOT_AVAILABLE" ;
VAL_ 1056 BCM_Status WiperState     0 "OFF" 1 "INTERMITTENT" 2 "LOW" 3 "HIGH" 4 "WASH" ;

VAL_ 848 IPC_Display Display_Gear
  0 "PARK" 1 "REVERSE" 2 "NEUTRAL" 3 "DRIVE"
  4 "1st" 5 "2nd" 6 "3rd" 7 "4th" 8 "5th" 9 "NOT_AVAILABLE" ;
```

---

## 4.9 STEP 8 — Add Attributes

```
/* ─── Attribute Definitions ──────────────────────────────────── */
BA_DEF_ BO_ "GenMsgCycleTime"          INT 0 10000;
BA_DEF_ BO_ "GenMsgStartDelayTime"     INT 0 1000;
BA_DEF_ BO_ "GenMsgSendType"           ENUM "NoMsgSendType","cyclic","event","noMsgSendType";
BA_DEF_ BO_ "GenMsgILSupport"          ENUM "No","Yes";
BA_DEF_ SG_ "GenSigStartValue"         FLOAT -1000000 1000000;
BA_DEF_ SG_ "GenSigSendType"           ENUM "Cyclic","Event","NoSigSendType";
BA_DEF_ BU_ "ILUsed"                   ENUM "No","Yes";
BA_DEF_ BU_ "NodeLayerModules"         STRING;

/* ─── Defaults ────────────────────────────────────────────────── */
BA_DEF_DEF_ "GenMsgCycleTime"          0;
BA_DEF_DEF_ "GenMsgStartDelayTime"     0;
BA_DEF_DEF_ "GenMsgSendType"           "NoMsgSendType";
BA_DEF_DEF_ "GenMsgILSupport"          "No";
BA_DEF_DEF_ "GenSigStartValue"         0;
BA_DEF_DEF_ "GenSigSendType"           "NoSigSendType";
BA_DEF_DEF_ "ILUsed"                   "No";
BA_DEF_DEF_ "NodeLayerModules"         "";

/* ─── Message Attribute Values ────────────────────────────────── */
BA_ "GenMsgCycleTime"     BO_ 512   10;
BA_ "GenMsgCycleTime"     BO_ 580   20;
BA_ "GenMsgCycleTime"     BO_ 768   10;
BA_ "GenMsgCycleTime"     BO_ 896   20;
BA_ "GenMsgCycleTime"     BO_ 848   100;
BA_ "GenMsgCycleTime"     BO_ 1056  100;

BA_ "GenMsgSendType"      BO_ 512   "cyclic";
BA_ "GenMsgSendType"      BO_ 580   "cyclic";
BA_ "GenMsgSendType"      BO_ 768   "cyclic";
BA_ "GenMsgSendType"      BO_ 896   "cyclic";
BA_ "GenMsgSendType"      BO_ 848   "cyclic";
BA_ "GenMsgSendType"      BO_ 1056  "cyclic";

BA_ "GenMsgILSupport"     BO_ 512   "Yes";
BA_ "GenMsgILSupport"     BO_ 580   "Yes";
BA_ "GenMsgILSupport"     BO_ 768   "Yes";

/* ─── Signal Initial Values ───────────────────────────────────── */
BA_ "GenSigStartValue" SG_ 580  AEB_Active       0;
BA_ "GenSigStartValue" SG_ 580  AEB_State        0;
BA_ "GenSigStartValue" SG_ 580  AEB_Decel_Req    0;
BA_ "GenSigStartValue" SG_ 768  EngineSpeed      0;
BA_ "GenSigStartValue" SG_ 768  EngineTemp       40;   ← raw 40 = (40×0.5)+(-40) = -20°C? No: 40×0.5-40=0°C ✓
BA_ "GenSigStartValue" SG_ 1056 IgnitionState    0;
```

---

## 4.10 STEP 9 — Add Comments

```
CM_ BU_ AEB_ECU  "Advanced Emergency Braking ECU — Continental Gen 4 Radar";
CM_ BU_ ABS_ECU  "Anti-lock Braking System ECU — Bosch ESP 9.3";
CM_ BU_ ECM      "Engine Control Module — Bosch ME17";
CM_ BU_ EPS_ECU  "Electric Power Steering ECU — Jtekt";
CM_ BU_ IPC      "Instrument Panel Cluster — Marelli";
CM_ BU_ BCM      "Body Control Module — Continental";
CM_ BU_ CGW      "Central Gateway ECU — Vector";

CM_ BO_ 512  "Wheel speed data — ASIL-B — 10ms cyclic from ABS_ECU";
CM_ BO_ 580  "AEB braking request — ASIL-B — 20ms cyclic — E2E protected";
CM_ BO_ 768  "Engine and transmission status — ASIL-A — 10ms cyclic";
CM_ BO_ 896  "EPS steering angle and status — ASIL-B — 20ms cyclic";
CM_ BO_ 848  "Instrument cluster display data — QM — 100ms cyclic";
CM_ BO_ 1056 "BCM body/door/ignition status — QM — 100ms cyclic";

CM_ SG_ 512  WheelSpeed_FL   "Front-left wheel speed. 0xFFFF=not available";
CM_ SG_ 580  AEB_Active      "1=AEB deceleration request currently active";
CM_ SG_ 580  AEB_Decel_Req   "Requested braking deceleration 0–25.5 m/s². 0xFF=NA";
CM_ SG_ 580  AEB_Obj_Distance "Distance to closest obstacle in path. 0xFFFF=NA";
CM_ SG_ 580  AEB_TTC         "Time-to-Collision with obstacle. 0xFF=NA";
CM_ SG_ 768  EngineTemp      "Engine coolant temperature. Signed 8-bit. -40 to +87.5 degC";
CM_ SG_ 896  SteeringAngle   "Steering wheel angle. Negative=left, Positive=right";
CM_ SG_ 1056 IgnitionState   "Current ignition/keystate. 4=NOT_AVAILABLE";
```

---

## 4.11 STEP 10 — DBC Validation Checklist

Before using DBC in CANoe, verify:

```
□ Version line present: VERSION ""
□ NS_ section present with standard symbols
□ BS_: line present (even if empty)
□ All Tx nodes listed in BU_
□ All BO_ IDs unique (no duplicates)
□ All BO_ IDs in decimal (not hex)
□ All signals within DLC byte range
□ No bit overlaps between signals in same message
□ All VAL_ entries end with semicolon
□ All CM_ entries end with semicolon
□ All BA_DEF_ entries have matching BA_DEF_DEF_
□ Signed signals use @1- or @0-
□ Factor and offset produce correct physical range
□ All receiver nodes listed in BU_
□ Special node Vector__XXX included in BU_
□ File saved as ASCII (not UTF-8 BOM)
□ Line endings: CRLF for Windows CANoe
```

---

## 4.12 Manual Calculation Examples

### Example 1: Convert hex ID to decimal for BO_
```
Message ID: 0x244 (from OEM matrix)
Hex to decimal: 0x244 = 2×256 + 4×16 + 4 = 512 + 64 + 4 = 580
BO_ 580 AEB_Req: 8 AEB_ECU  ✓
```

### Example 2: Signal range calculation
```
Signal: EngineSpeed
  Length: 16 bits, Unsigned → Raw range: 0–65535
  Factor: 0.25, Offset: 0
  Physical min: 0 × 0.25 + 0 = 0.00 rpm
  Physical max: 65535 × 0.25 + 0 = 16383.75 rpm
  In DBC: [0|16383.75]  ✓
```

### Example 3: Signed temperature signal
```
Signal: EngineTemp
  Length: 8 bits, Signed → Raw range: -128 to +127
  Factor: 0.5, Offset: -40
  Physical at raw=-128: -128 × 0.5 + (-40) = -64 + (-40) = -104°C (invalid/error)
  Physical at raw=0:     0 × 0.5 + (-40)   =  0 + (-40)  = -40°C (sensor off)
  Physical at raw=127:   127 × 0.5 + (-40)  = 63.5 - 40  = +23.5°C (ambient)
  Physical at raw=255 (unsigned): not valid — this is signed!

  Actual valid range using raw 0–255 (8-bit UNSIGNED, signed=false):
  At raw=0: -40°C, at raw=255: 255×0.5-40 = 87.5°C
  
  In DBC: [-40|87.5] "degC"
  BUT sign depends on implementation — verify with matrix!
```

### Example 4: Verify CAN ID priority
```
Safety messages should have LOWER IDs (higher priority):
  WheelSpeed  0x200 = 512  ← lower ID = higher priority ✓
  AEB_Req     0x244 = 580  ← safety critical ✓
  VehicleStatus 0x300 = 768
  EPS_Status  0x380 = 896
  IPC_Display 0x350 = 848
  BCM_Status  0x420 = 1056 ← comfort, lower priority ✓
```

---

## 4.13 Common Manual Creation Mistakes

| Mistake | Example | Correct |
|---------|---------|---------|
| Using hex ID in BO_ | `BO_ 0x244` | `BO_ 580` |
| Off-by-one in end bit | Start=12, Len=16 → "bits 12–28" | Bits 12–27 (start+len-1) |
| Forgetting space before SG_ | `SG_ Signal :` at column 0 | ` SG_ Signal :` (1 space indent) |
| Wrong semicolon in VAL_ | `VAL_ ... "text"` | `VAL_ ... "text" ;` |
| Duplicate receiver node in SG_ | `ECM,ECM` | `ECM` |
| Wrong signed notation | `@1+` for negative value signal | `@1-` for signed |

---

## Module 04 — Knowledge Check

1. Convert 0x380 to decimal for use in a DBC BO_ statement.
2. A signal starts at bit 40 with length 8. What is the last bit it occupies?
3. If a 12-bit unsigned signal has Factor=0.1, Offset=0, what is its maximum physical value?
4. What is wrong with: `BO_ 0x244 AEB_Req: 8 AEB_ECU`?
5. Write the BCM signal `HighBeam` starting at bit 15, 1-bit, Intel, unsigned, no unit, receiver=IPC
6. A message with DLC=4 has signals using bits 0–7, 8–15, 16–31. How many unused bits remain?

**Answers:**
1. 0x380 = 3×256 + 8×16 + 0 = 768 + 128 = 896
2. Bit 47 (40 + 8 - 1)
3. (2¹²−1) × 0.1 + 0 = 4095 × 0.1 = 409.5
4. ID must be decimal, not hex: should be `BO_ 580 AEB_Req: 8 AEB_ECU`
5. `SG_ HighBeam : 15|1@1+ (1,0) [0|1] "" IPC`
6. DLC=4 → 32 bits total. Used: 8+8+16=32. Unused: 0 (fully packed)
