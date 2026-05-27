# Module 03 — DBC File Fundamentals

> **Level**: Beginner–Intermediate  
> **Duration**: ~3 hours  
> **Goal**: Master DBC file syntax — every keyword, section, and attribute explained with real examples.

---

## 3.1 What Is a DBC File?

A **DBC file** (Database CAN) is a text-format database that describes:
- All CAN messages on a network
- All signals inside each message
- Signal encoding (bit position, length, scaling)
- Node (ECU) definitions
- Value tables (enumerations)
- Attributes (metadata)
- Comments

DBC files are the primary input for:
- Vector CANoe / CANalyzer (signal decoding and simulation)
- Kvaser software
- Peak PCAN software
- Python `cantools` library
- Automotive HIL test systems

```
File extension:   .dbc
Text encoding:    ASCII (UTF-8 not standard — avoid special chars)
Line endings:     Windows (CRLF) recommended for CANoe compatibility
Version:          No strict versioning — tool-dependent
```

---

## 3.2 DBC File Structure Overview

```
VERSION ""                            ← Always first line

NS_ :                                 ← Namespace section (symbol definitions)
  NS_DESC_
  CM_
  BA_DEF_
  ...

BS_ :                                 ← Bit timing (usually empty in practice)

BU_: ECU1 ECU2 ECU3                   ← Bus Units (node names)

BO_ 0x244 AEB_Req: 8 AEB_ECU          ← Message definition
 SG_ AEB_Active : 0|1@1+ (1,0) [0|1] "" CGW,IPC
 SG_ AEB_Decel_Req : 4|8@1+ (0.1,0) [0|25.5] "m/s2" CGW,IPC

BO_ 0x300 VehicleStatus: 8 ECM
 SG_ EngineSpeed : 0|16@1+ (0.25,0) [0|16383.75] "rpm" AEB_ECU,IPC

VAL_ 0x244 AEB_Active  0 "Inactive" 1 "Active" ;
VAL_ 0x300 EngineState 0 "OFF" 1 "CRANKING" 2 "IDLE" 3 "RUNNING" ;

BA_DEF_ BO_ "GenMsgCycleTime" INT 0 10000;
BA_DEF_ SG_ "GenSigStartValue" FLOAT 0 100;

BA_ "GenMsgCycleTime" BO_ 0x244 20;
BA_ "GenSigStartValue" SG_ 0x244 AEB_Active 0;

CM_ BO_ 0x244 "AEB active deceleration request from AEB ECU to powertrain";
CM_ SG_ 0x244 AEB_Active "1=AEB deceleration request active";
```

---

## 3.3 VERSION Section

```
VERSION ""
```

Always present as the first line. The version string is typically empty or contains a
CANdb++ version tag. **Do not modify** — CANoe requires this line.

---

## 3.4 NS_ — New Symbols Section

```
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
```

This section lists all symbol names used later in the file. CANoe generates this automatically.
**Leave this section as-is** — do not manually edit symbol names.

---

## 3.5 BU_ — Bus Units (ECU Node Definitions)

```
BU_: AEB_ECU ECM ABS_ECU BCM IPC CGW HMI_ECU TCU
```

Lists all ECU node names. Rules:
- Names must be alphanumeric + underscore
- No spaces allowed
- Case-sensitive
- Each ECU in `Tx Node` column of BO_ must be listed here
- Special node `Vector__XXX` = "don't care" / external node

```
BU_: AEB_ECU ECM ABS_ECU BCM IPC CGW HMI_ECU TCU Vector__XXX
                                                              ↑
                                              Placeholder for undefined sender
```

---

## 3.6 BO_ — Message Definition

### Syntax
```
BO_ <decimal_id> <message_name>: <dlc> <tx_node>
```

### Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `decimal_id` | Integer | CAN ID in **decimal**. For extended IDs: add 0x80000000 |
| `message_name` | String | Alphanumeric + underscore, no spaces |
| `dlc` | Integer | Data length 0–8 (CAN) or 0–64 (CAN FD) |
| `tx_node` | String | Must match a BU_ entry; use `Vector__XXX` if unknown |

### Examples

```
Standard CAN ID (11-bit):
BO_ 580 AEB_Req: 8 AEB_ECU
                              ↑ 0x244 = 580 decimal

BO_ 768 VehicleStatus: 8 ECM
                              ↑ 0x300 = 768 decimal

Extended CAN ID (29-bit):
BO_ 2566844416 J1939_EEC1: 8 ECM
     ↑
     0x98F00300 + 0x80000000 = 2566844416
     (CANdb++ automatically converts with "+" suffix in some versions)

Diagnostic message:
BO_ 2016 DiagReq: 8 Tester
                              ↑ 0x7E0 = 2016 decimal
```

---

## 3.7 SG_ — Signal Definition

### Syntax
```
 SG_ <signal_name> : <start_bit>|<length>@<byte_order><value_type> (<factor>,<offset>) [<min>|<max>] "<unit>" <receivers>
```

### Parameter Breakdown

| Parameter | Values | Meaning |
|-----------|--------|---------|
| `start_bit` | Integer | Bit position (LSB for Intel, MSB for Motorola) |
| `length` | Integer | Signal width in bits |
| `byte_order` | `1` or `0` | `1` = Intel/little-endian, `0` = Motorola/big-endian |
| `value_type` | `+` or `-` | `+` = unsigned, `-` = signed (two's complement) |
| `factor` | Float | Multiplier for physical value calculation |
| `offset` | Float | Offset for physical value calculation |
| `min` | Float | Minimum physical value |
| `max` | Float | Maximum physical value |
| `unit` | String | Physical unit (in quotes) |
| `receivers` | CSV | Comma-separated list of receiving nodes |

### Full Example with Annotations

```
BO_ 580 AEB_Req: 8 AEB_ECU
 SG_ AEB_Active      : 0|1@1+   (1,0)     [0|1]       ""       CGW,IPC,BCM
     ───────────────   ─ ─ ──    ─ ─        ─ ─         ──       ───────────
     signal name       │ │ ↑↑    │ │        │ │         unit     receivers
                       │ │ byte_order+type  min|max
                       │ │ @1=Intel, +=unsigned
                       │ length=1 bit
                       start_bit=0

 SG_ AEB_Decel_Req   : 4|8@1+   (0.1,0)   [0|25.5]    "m/s2"   CGW,IPC
 SG_ AEB_Obj_Distance : 12|16@1+ (0.01,0)  [0|655.35]  "m"      CGW,IPC
 SG_ AEB_TTC          : 28|8@1+  (0.01,0)  [0|2.55]    "s"      CGW,IPC
 SG_ AEB_State        : 36|3@1+  (1,0)     [0|7]       ""       CGW,IPC,BCM
 SG_ Alive_Counter    : 39|4@1+  (1,0)     [0|14]      ""       CGW,IPC
 SG_ CRC_AEB          : 43|8@1+  (1,0)     [0|255]     ""       CGW,IPC
```

---

## 3.8 Signed Signal Example

```
Signal: EngineTemp, 8-bit signed, factor=0.5, offset=-40

DBC:
 SG_ EngineTemp : 24|8@1- (0.5,-40) [-40|87.5] "degC" AEB_ECU,IPC
                              ↑  signed (two's complement)

Bit pattern 0x50 = 80 decimal
Physical = 80 × 0.5 + (-40) = 40 - 40 = 0°C  ✓

Bit pattern 0xFF (-1 in two's complement)
Physical = -1 × 0.5 + (-40) = -40.5°C  (just below minimum — treat as error)
```

---

## 3.9 Multiplexed Signals — MUX

Multiplexing allows multiple signal sets to share the same byte positions, selected by a
multiplexer signal.

### DBC Syntax

```
BO_ 400 SensorData: 8 SensorECU
 SG_ Mux_Selector  M  : 0|4@1+ (1,0) [0|15] "" Vector__XXX
                   ↑ M = this signal IS the multiplexer
 SG_ Temp_Sensor   m0 : 8|16@1+ (0.1,-40) [-40|200] "degC" IPC
                   ↑ m0 = this signal is active when Mux_Selector=0
 SG_ Press_Sensor  m1 : 8|16@1+ (0.01,0) [0|655.35] "bar" IPC
                   ↑ m1 = this signal is active when Mux_Selector=1
 SG_ VoltSensor    m2 : 8|16@1+ (0.001,0) [0|65.535] "V" IPC
 SG_ CurrSensor    m3 : 8|16@1+ (0.01,-327.68) [-327.68|327.67] "A" IPC
```

### How It Works

```
Frame 0x190 with Mux_Selector=0:
  Byte 0 low nibble = 0 → decode Temp_Sensor from bytes 1–2

Frame 0x190 with Mux_Selector=1:
  Byte 0 low nibble = 1 → decode Press_Sensor from bytes 1–2

All variants share bits 8–23, but only one is valid per frame
```

---

## 3.10 VAL_ — Value/Enumeration Tables

### Syntax
```
VAL_ <message_id> <signal_name>  <raw_value> "<description>"  ... ;
```

### Example

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

VAL_ 1056 BCM_Status DoorFL_Status
  0 "CLOSED"
  1 "OPEN"
  2 "AJAR"
  3 "NOT_AVAILABLE" ;

VAL_ 1056 BCM_Status IgnitionState
  0 "OFF"
  1 "ACC"
  2 "ON"
  3 "START"
  4 "NOT_AVAILABLE" ;
```

Note: Message ID in `VAL_` must be the **decimal** ID, same as in `BO_`.

---

## 3.11 VAL_TABLE_ — Reusable Value Tables

When the same enum appears in multiple signals, define a named table once:

```
VAL_TABLE_ NotAvailableState
  0 "NOT_AVAILABLE" ;

VAL_TABLE_ OnOff
  0 "OFF"
  1 "ON" ;

VAL_TABLE_ DoorState
  0 "CLOSED"
  1 "OPEN"
  2 "AJAR"
  3 "NOT_AVAILABLE" ;
```

Reference in signal with `SIG_VALTYPE_` or use CANdb++ UI to assign.

---

## 3.12 CM_ — Comment Definitions

### Syntax Variants

```
CM_ "database comment";                    ← Overall database comment

CM_ BU_ AEB_ECU "Advanced Emergency Braking ECU, Tier1: Bosch";  ← Node comment

CM_ BO_ 580 "AEB deceleration request — transmitted at 20ms, safety-critical (ASIL-B)";  ← Message comment

CM_ SG_ 580 AEB_Active "1=AEB system requesting deceleration from powertrain";  ← Signal comment
```

### Good Practice

```
/* Always add comments for: */
1. Non-obvious signal purpose
2. Safety classification (ASIL level)
3. Known limitations (e.g., "invalid above 250 km/h")
4. Related signals or dependency notes
```

---

## 3.13 BA_DEF_ — Attribute Definitions

Attributes add metadata to messages, signals, nodes, and the database.

### Syntax
```
BA_DEF_ <object_type> "<attr_name>" <attr_type> <range_or_values>;
BA_DEF_DEF_ "<attr_name>" <default_value>;
```

### Object Types

| Type | Applies To |
|------|-----------|
| (none) | Database |
| `BO_` | Messages |
| `SG_` | Signals |
| `BU_` | Nodes |
| `EV_` | Environment variables |

### Attribute Types

| Type | Example |
|------|---------|
| `INT` | Integer with range |
| `FLOAT` | Float with range |
| `STRING` | Free text |
| `ENUM` | List of choices |
| `HEX` | Hexadecimal value |

### Standard Attributes Used by CANoe

```
/* Message attributes */
BA_DEF_ BO_ "GenMsgCycleTime"         INT    0 10000;   ← Cycle time in ms
BA_DEF_ BO_ "GenMsgStartDelayTime"    INT    0 1000;    ← Startup delay
BA_DEF_ BO_ "GenMsgSendType"          ENUM   "NoMsgSendType","cyclic","event","notUsed";
BA_DEF_ BO_ "GenMsgILSupport"         ENUM   "No","Yes";  ← IL (Interaction Layer) support
BA_DEF_ BO_ "NmMessage"               ENUM   "No","Yes";  ← Network Management message

/* Signal attributes */
BA_DEF_ SG_ "GenSigStartValue"        FLOAT  0 100;    ← Initial raw value
BA_DEF_ SG_ "GenSigSendType"          ENUM   "Cyclic","Event","NoSigSendType";
BA_DEF_ SG_ "SystemSignalLongSymbol"  STRING ;         ← Long signal names

/* Node attributes */
BA_DEF_ BU_ "NodeLayerModules"        STRING ;         ← CAPL module assignment
BA_DEF_ BU_ "ILUsed"                  ENUM   "No","Yes";

/* Defaults */
BA_DEF_DEF_ "GenMsgCycleTime"         0;
BA_DEF_DEF_ "GenMsgSendType"          "NoMsgSendType";
BA_DEF_DEF_ "GenSigStartValue"        0;
BA_DEF_DEF_ "ILUsed"                  "No";
```

---

## 3.14 BA_ — Attribute Values

After defining attribute types (BA_DEF_), assign specific values:

### Syntax
```
BA_ "<attr_name>" <object_type> <id_or_name> <value>;
```

### Examples

```
/* Message: AEB_Req — 20ms cyclic, IL-supported */
BA_ "GenMsgCycleTime"     BO_ 580   20;
BA_ "GenMsgSendType"      BO_ 580   "cyclic";
BA_ "GenMsgILSupport"     BO_ 580   "Yes";
BA_ "GenMsgStartDelayTime" BO_ 580  0;

/* Message: HMI_AudioCmd — event triggered */
BA_ "GenMsgCycleTime"     BO_ 1296  0;
BA_ "GenMsgSendType"      BO_ 1296  "event";

/* Signal: AEB_Active — initial value = 0 */
BA_ "GenSigStartValue"    SG_ 580 AEB_Active  0;
BA_ "GenSigStartValue"    SG_ 580 AEB_Decel_Req 0;

/* Node: AEB_ECU uses IL */
BA_ "ILUsed"              BU_ AEB_ECU  "Yes";
BA_ "NodeLayerModules"    BU_ AEB_ECU  "CAPL::AEB_Simulation";
```

---

## 3.15 Extended CAN ID in DBC

```
Standard 11-bit: Write ID in decimal directly
  BO_ 580 AEB_Req: 8 AEB_ECU
  (0x244 = 580)

Extended 29-bit: Add 0x80000000 (2147483648) to the ID
  0x18DA00F1 = 417100017 decimal
  + 2147483648 = 2564583665
  BO_ 2564583665 DiagReq_UDS: 8 Tester
```

In CANdb++, you can toggle "Extended" checkbox instead of manual calculation.

---

## 3.16 CAN FD DBC Structure

CAN FD DBC files are almost identical to CAN, with additional attributes:

```
/* CAN FD message (DLC up to 64) */
BO_ 580 AEB_Req_FD: 64 AEB_ECU

/* Attributes for CAN FD */
BA_DEF_ BO_ "CANFD_BRS"  ENUM "0","1";    ← Bit Rate Switch
BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","StandardCAN_FD","ExtendedCAN_FD";

BA_ "VFrameFormat"   BO_ 580  "StandardCAN_FD";
BA_ "CANFD_BRS"      BO_ 580  "1";        ← Enable fast data phase
```

---

## 3.17 Complete DBC File Annotated Example

```
VERSION ""

NS_ :
  NS_DESC_
  CM_
  BA_DEF_
  BA_DEF_DEF_
  BA_
  VAL_

BS_:

BU_: AEB_ECU ECM ABS_ECU BCM IPC CGW

/* ─── MESSAGES ──────────────────────────────────────────────────── */

BO_ 580 AEB_Req: 8 AEB_ECU
 SG_ AEB_Active      : 0|1@1+  (1,0)    [0|1]       ""      CGW,IPC,BCM
 SG_ AEB_State        : 1|3@1+  (1,0)    [0|7]       ""      CGW,IPC,BCM
 SG_ AEB_Decel_Req    : 4|8@1+  (0.1,0)  [0|25.5]    "m/s2"  CGW,IPC
 SG_ AEB_Obj_Distance : 12|16@1+ (0.01,0) [0|655.35]  "m"     CGW,IPC
 SG_ AEB_TTC          : 28|8@1+  (0.01,0) [0|2.55]    "s"     CGW,IPC
 SG_ Alive_Ctr_AEB    : 36|4@1+  (1,0)    [0|14]      ""      CGW,IPC
 SG_ CRC_AEB          : 40|8@1+  (1,0)    [0|255]     ""      CGW,IPC

BO_ 768 VehicleStatus: 8 ECM
 SG_ EngineSpeed   : 0|16@1+  (0.25,0)  [0|16383.75]  "rpm"  AEB_ECU,IPC,ABS_ECU
 SG_ ThrottlePos   : 16|8@1+  (0.4,0)   [0|100]       "%"    AEB_ECU,IPC
 SG_ EngineTemp    : 24|8@1-  (0.5,-40) [-40|87.5]    "degC" IPC
 SG_ EngineState   : 32|3@1+  (1,0)     [0|6]         ""     AEB_ECU,IPC,BCM
 SG_ TransmMode    : 35|3@1+  (1,0)     [0|5]         ""     IPC,BCM
 SG_ FuelPress     : 38|10@1+ (0.1,0)   [0|102.3]     "bar"  IPC
 SG_ Alive_Ctr_VS  : 48|4@1+  (1,0)     [0|14]        ""     AEB_ECU,IPC
 SG_ CRC_VS        : 52|8@1+  (1,0)     [0|255]       ""     AEB_ECU,IPC

BO_ 512 WheelSpeed: 8 ABS_ECU
 SG_ WheelSpeed_FL : 0|16@1+  (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM
 SG_ WheelSpeed_FR : 16|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM
 SG_ WheelSpeed_RL : 32|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM
 SG_ WheelSpeed_RR : 48|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,ECM

BO_ 1056 BCM_Status: 6 BCM
 SG_ DoorFL_Status  : 0|2@1+  (1,0) [0|3] "" CGW,IPC
 SG_ DoorFR_Status  : 2|2@1+  (1,0) [0|3] "" CGW,IPC
 SG_ DoorRL_Status  : 4|2@1+  (1,0) [0|3] "" CGW,IPC
 SG_ DoorRR_Status  : 6|2@1+  (1,0) [0|3] "" CGW,IPC
 SG_ Hood_Status    : 8|1@1+  (1,0) [0|1] "" CGW,IPC
 SG_ Trunk_Status   : 9|1@1+  (1,0) [0|1] "" CGW,IPC
 SG_ IgnitionState  : 10|3@1+ (1,0) [0|4] "" CGW,IPC,AEB_ECU
 SG_ HazardActive   : 13|1@1+ (1,0) [0|1] "" CGW,IPC
 SG_ LowBeam        : 14|1@1+ (1,0) [0|1] "" CGW,IPC
 SG_ HighBeam       : 15|1@1+ (1,0) [0|1] "" CGW,IPC
 SG_ WiperState     : 16|3@1+ (1,0) [0|4] "" CGW,IPC
 SG_ Alive_Ctr_BCM  : 40|4@1+ (1,0) [0|14] "" CGW,IPC
 SG_ CRC_BCM        : 44|8@1+ (1,0) [0|255] "" CGW,IPC

/* ─── VALUE TABLES ──────────────────────────────────────────────── */

VAL_ 580 AEB_State
  0 "OFF" 1 "STANDBY" 2 "WARNING" 3 "ACTIVE"
  4 "FAULT" 5 "DEGRADED" 6 "OVERRIDE" 7 "NOT_AVAILABLE" ;

VAL_ 768 EngineState
  0 "OFF" 1 "CRANKING" 2 "IDLE" 3 "RUNNING"
  4 "OVERHEATING" 5 "SHUTDOWN" 6 "FAULT" ;

VAL_ 1056 BCM_Status DoorFL_Status
  0 "CLOSED" 1 "OPEN" 2 "AJAR" 3 "NOT_AVAILABLE" ;

VAL_ 1056 BCM_Status IgnitionState
  0 "OFF" 1 "ACC" 2 "ON" 3 "START" 4 "NOT_AVAILABLE" ;

/* ─── ATTRIBUTES ─────────────────────────────────────────────────── */

BA_DEF_ BO_ "GenMsgCycleTime"     INT 0 10000;
BA_DEF_ BO_ "GenMsgSendType"      ENUM "NoMsgSendType","cyclic","event";
BA_DEF_ SG_ "GenSigStartValue"    FLOAT 0 100;

BA_DEF_DEF_ "GenMsgCycleTime"     0;
BA_DEF_DEF_ "GenMsgSendType"      "NoMsgSendType";
BA_DEF_DEF_ "GenSigStartValue"    0;

BA_ "GenMsgCycleTime"  BO_ 580   20;
BA_ "GenMsgCycleTime"  BO_ 768   10;
BA_ "GenMsgCycleTime"  BO_ 512   10;
BA_ "GenMsgCycleTime"  BO_ 1056  100;
BA_ "GenMsgSendType"   BO_ 580   "cyclic";
BA_ "GenMsgSendType"   BO_ 768   "cyclic";
BA_ "GenMsgSendType"   BO_ 1056  "cyclic";

/* ─── COMMENTS ───────────────────────────────────────────────────── */

CM_ BU_ AEB_ECU "Advanced Emergency Braking ECU — Bosch Gen5";
CM_ BU_ ECM     "Engine Control Module";
CM_ BU_ ABS_ECU "Anti-lock Braking System ECU";
CM_ BU_ BCM     "Body Control Module";
CM_ BU_ IPC     "Instrument Panel Cluster";
CM_ BU_ CGW     "Central Gateway";

CM_ BO_ 580  "AEB braking request — ASIL-B — 20ms cyclic";
CM_ BO_ 768  "Engine and powertrain status — 10ms cyclic";
CM_ BO_ 512  "Wheel speed data from ABS — 10ms cyclic";
CM_ BO_ 1056 "Body/door/ignition status from BCM — 100ms cyclic";

CM_ SG_ 580 AEB_Active      "1=AEB deceleration request is active";
CM_ SG_ 580 AEB_Decel_Req   "Requested deceleration in m/s². 0xFF = not available";
CM_ SG_ 580 AEB_Obj_Distance "Distance to detected obstacle in meters";
CM_ SG_ 580 AEB_TTC         "Time-to-Collision estimate in seconds";
CM_ SG_ 768 EngineTemp      "Engine coolant temperature. Signed: -40 to +87.5 degC";
```

---

## 3.18 DBC Syntax Quick Reference

```
┌─────────────────────────────────────────────────────────┐
│             DBC SYNTAX CHEAT SHEET                       │
├─────────────┬───────────────────────────────────────────┤
│ VERSION     │ VERSION ""                                 │
├─────────────┼───────────────────────────────────────────┤
│ BU_         │ BU_: Node1 Node2 Node3                     │
├─────────────┼───────────────────────────────────────────┤
│ BO_         │ BO_ <dec_id> <name>: <dlc> <tx_node>       │
├─────────────┼───────────────────────────────────────────┤
│ SG_         │  SG_ <name> : <sbit>|<len>@<end><sgn>      │
│             │    (<factor>,<offset>) [<min>|<max>]        │
│             │    "<unit>" <rx_nodes>                      │
├─────────────┼───────────────────────────────────────────┤
│ Endianness  │ @1 = Intel (little-endian)                 │
│             │ @0 = Motorola (big-endian)                  │
├─────────────┼───────────────────────────────────────────┤
│ Sign        │ + = unsigned,  - = signed                   │
├─────────────┼───────────────────────────────────────────┤
│ Mux         │ M = multiplexer,  m<n> = muxed signal       │
├─────────────┼───────────────────────────────────────────┤
│ VAL_        │ VAL_ <msg_id> <sig_name> n "text" ... ;    │
├─────────────┼───────────────────────────────────────────┤
│ CM_         │ CM_ SG_ <id> <name> "comment";              │
├─────────────┼───────────────────────────────────────────┤
│ BA_DEF_     │ BA_DEF_ BO_ "AttrName" INT 0 1000;          │
├─────────────┼───────────────────────────────────────────┤
│ BA_         │ BA_ "AttrName" BO_ <id> <value>;            │
└─────────────┴───────────────────────────────────────────┘
```

---

## 3.19 Common DBC Errors

| Error | Symptom | Fix |
|-------|---------|-----|
| Duplicate message ID | CANoe shows duplicate warning | Check all BO_ IDs are unique |
| Signal overlap | Wrong decoded values | Recalculate bit ranges |
| Node not in BU_ | Import error | Add to BU_ line |
| Missing `VAL_` semicolon | Parse error | End every VAL_ with `;` |
| Wrong endianness | Swapped bytes | Verify @0/@1 per signal |
| Signed signal with positive offset | Unexpected negative values | Verify factor/offset math |
| DLC mismatch | Signals exceed byte count | Ensure (max_bit + 1) ≤ DLC × 8 |

---

## Module 03 — Knowledge Check

1. What is the decimal value of CAN ID `0x300` for use in a DBC `BO_` statement?
2. Write the DBC signal definition for: `BrakePress`, Start=16, Len=10, Intel, Unsigned, Factor=0.1, Offset=0, Range 0–102.3 bar, receivers: ABS_ECU, ECM
3. What does `m2` mean in a multiplexed signal definition?
4. How do you represent a signed 8-bit signal with Factor=0.5 and Offset=-40?
5. Write the `VAL_` entry for signal `GearPos` with values: 0=Park, 1=Reverse, 2=Neutral, 3=Drive, message ID 0x300
6. What is the purpose of `BA_DEF_DEF_`?

**Answers:**
1. `768`
2. `SG_ BrakePress : 16|10@1+ (0.1,0) [0|102.3] "bar" ABS_ECU,ECM`
3. The signal is active when the multiplexer signal equals 2
4. `SG_ EngineTemp : 24|8@1- (0.5,-40) [-40|87.5] "degC" ...`
5. `VAL_ 768 GearPos 0 "Park" 1 "Reverse" 2 "Neutral" 3 "Drive" ;`
6. Sets the default value for an attribute when no specific value is assigned to an object
