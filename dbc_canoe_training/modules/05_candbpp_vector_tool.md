# Module 05 — DBC Creation Using Vector CANdb++

> **Level**: Intermediate  
> **Duration**: ~3 hours  
> **Goal**: Use Vector CANdb++ to create, edit, and validate DBC files through a GUI workflow.

---

## 5.1 What Is CANdb++?

**CANdb++** (CAN Database Editor) is Vector's graphical tool for creating and editing DBC/LDF/ARXML
database files. It is the industry-standard tool for signal database management in automotive
projects.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CANdb++ Interface                            │
├────────────────┬────────────────────────────────────────────────────┤
│  Network Tree  │                  Properties Panel                   │
│  ─ Network     │  Message:  AEB_Req                                  │
│    ├ AEB_ECU   │  ID:       0x244 (580 decimal)                      │
│    ├ Messages  │  DLC:      8                                         │
│    │  ├ AEB_Req│  Cycle:    20 ms                                     │
│    │  │ ├ AEB_Active │  Tx Node:  AEB_ECU                            │
│    │  │ ├ AEB_State  ├────────────────────────────────────────────── │
│    │  │ └ ...        │  Signal Layout (Bit View)                      │
│    └ Environment     │  Byte: B0 B1 B2 B3 B4 B5 B6 B7               │
│      Variables       │  [  0][  1][  2][  3][  4][  5][  6][  7]    │
└────────────────┴────────────────────────────────────────────────────┘
```

### Installation

CANdb++ is bundled with CANoe/CANalyzer (Vector Informatik).

```
License required: CANoe (any edition) includes CANdb++
Standalone:       CANdb++ Editor (free download from Vector website)
Version check:    Help → About CANdb++
Minimum version:  10.0 for full CAN FD support
```

---

## 5.2 CANdb++ Workspace Setup

### Creating a New Database

```
1. Open CANdb++
2. File → New
3. Select "CAN Database (.dbc)"
4. Set target: "CAN" or "CAN FD"
5. Click OK
6. File → Save As → [ProjectName]_[BusName]_[Version].dbc
   Example: ADAS_HS1_v1.0.dbc
```

### Database Properties

```
File → Database Properties:
  Network type:   CAN (or CAN FD)
  Default bit rate: 500000 (or 1000000/2000000/5000000/8000000 for FD)
  Comment:        "ADAS Safety Bus — CAN-HS1 — Project: SUV2026"
```

### File Naming Convention (OEM Standard)

```
[Project]_[BusName]_[ECU or ALL]_[Version]_[Status].dbc

Examples:
  SUV26_CAN_HS1_ALL_v2.3_RELEASE.dbc
  SUV26_CAN_HS2_BCM_v1.0_DRAFT.dbc
  SUV26_CAN_FD1_ADAS_v0.5_REVIEW.dbc
```

---

## 5.3 Adding ECU Nodes (BU_)

### In CANdb++

```
1. Right-click on "Nodes" in tree → Add Node
2. Node Name: AEB_ECU (use exact names from communication matrix)
3. Comment: "Advanced Emergency Braking ECU — Continental"
4. Attributes tab → set ILUsed = Yes (for safety-critical nodes)

Repeat for each ECU:
  AEB_ECU, ABS_ECU, ECM, EPS_ECU, IPC, BCM, CGW, Vector__XXX
```

### Naming Rules in CANdb++

```
✅ Valid names:    AEB_ECU, EngineSpeed, WheelSpeed_FL
✅ Numbers OK:     AEB2_Request, Temp_1
❌ Spaces:         "AEB ECU" (not allowed)
❌ Special chars:  AEB-ECU, Speed@Wheel
❌ Leading digit:  1_AEB_ECU
❌ Hyphen:         AEB-Request
❌ German umlauts: AEB_Drücken
```

---

## 5.4 Creating CAN Messages

### Step-by-Step: Adding a New Message

```
1. Right-click "Messages" → Add Message
2. Fill Message Properties:
   
   ┌─────────────────────────────────────────────┐
   │ Message Properties                           │
   │                                             │
   │ Name:        AEB_Req                        │
   │ ID:          0x244  [  ] Extended Frame     │
   │ Type:        CAN    [○] CAN FD              │
   │ DLC:         8                              │
   │ Transmitter: AEB_ECU     ▼                  │
   │ Comment:     AEB deceleration request       │
   └─────────────────────────────────────────────┘

3. Click "Attributes" tab:
   GenMsgCycleTime:      20
   GenMsgSendType:       cyclic
   GenMsgILSupport:      Yes
   GenMsgStartDelayTime: 0
```

### Setting Message ID — Standard vs Extended

```
Standard (11-bit):
  Enter 0x244 in ID field, leave "Extended" unchecked
  CANdb++ stores as 580 decimal internally

Extended (29-bit):
  Enter 0x18DA00F1, CHECK "Extended Frame"
  CANdb++ adds 0x80000000 automatically in DBC file

J1939 style:
  Check "J1939 Message" (if J1939 license present)
  PGN, Priority, Source Address fields appear
```

---

## 5.5 Creating Signals

### Step-by-Step: Adding a Signal to a Message

```
1. Select message AEB_Req in tree
2. Right-click → Add Signal (or Ctrl+Shift+S)
3. Fill Signal Properties Dialog:

┌────────────────────────────────────────────────────────┐
│  Signal Properties: AEB_Active                          │
├─────────────────────┬──────────────────────────────────┤
│ Name:               │ AEB_Active                        │
│ Start bit:          │ 0                                 │
│ Length:             │ 1                                 │
│ Byte order:         │ ○ Intel  ● Motorola               │
│ Value type:         │ ● Unsigned  ○ Signed  ○ Float     │
│ Factor:             │ 1                                 │
│ Offset:             │ 0                                 │
│ Minimum value:      │ 0                                 │
│ Maximum value:      │ 1                                 │
│ Unit:               │ (empty)                           │
│ Initial value:      │ 0                                 │
│ Comment:            │ 1=AEB deceleration active         │
└─────────────────────┴──────────────────────────────────┘
```

### Signal Properties for Each Signal in AEB_Req

| Signal | Start Bit | Length | Order | Type | Factor | Offset | Min | Max | Unit |
|--------|-----------|--------|-------|------|--------|--------|-----|-----|------|
| AEB_Active | 0 | 1 | Intel | UNS | 1 | 0 | 0 | 1 | — |
| AEB_State | 1 | 3 | Intel | UNS | 1 | 0 | 0 | 7 | — |
| AEB_Decel_Req | 4 | 8 | Intel | UNS | 0.1 | 0 | 0 | 25.5 | m/s2 |
| AEB_Obj_Distance | 12 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | m |
| AEB_TTC | 28 | 8 | Intel | UNS | 0.01 | 0 | 0 | 2.55 | s |
| Alive_Ctr_AEB | 36 | 4 | Intel | UNS | 1 | 0 | 0 | 14 | — |
| CRC_AEB | 40 | 8 | Intel | UNS | 1 | 0 | 0 | 255 | — |
| Reserved_AEB | 48 | 16 | Intel | UNS | 1 | 0 | 0 | 65535 | — |

---

## 5.6 Bit View — Visual Signal Layout

CANdb++ shows a bit layout grid — the most important visual for validating signal packing:

```
CANdb++ Bit View for AEB_Req (DLC=8):

     Bit: 7  6  5  4  3  2  1  0  | 15 14 13 12 11 10  9  8  | ...
Byte 0: [Rsv][Rsv][Rsv][Rsv][Decel][Decel][St][St][St][Actv]
Byte 1: [Dist][Dist][Dist][Dist][Dist][Dist][Dist][Dist][Decel][Decel][Decel][Decel]
...

Each signal shown in different color — easy to spot overlaps
```

### How to Use Bit View
```
1. Select message → click "Bit View" button
2. Signals shown as colored blocks
3. Red = overlap (error!)
4. Gray = unused bits
5. Click any colored block to select signal
6. Right-click in gray → Add Signal at this position
```

---

## 5.7 Motorola (Big-Endian) Signal Entry in CANdb++

Motorola signals require careful start bit entry:

```
Example: EngineRPM, Motorola, 16-bit, Start bit = MSB position

Visual for Motorola bit numbering:
Byte 0: bit7  bit6  bit5  bit4  bit3  bit2  bit1  bit0
Byte 1: bit15 bit14 bit13 bit12 bit11 bit10 bit9  bit8

For 16-bit signal with MSB at byte 2 bit 7:
  Start bit (Motorola) = 23 (byte 2 bit 7 in Motorola numbering)

Enter in CANdb++:
  Start bit: 23
  Length: 16
  Byte order: Motorola
  CANdb++ automatically draws the bit range correctly
```

---

## 5.8 Value Tables (Enumerations)

### Creating Value Tables in CANdb++

```
Method 1 — Per-signal value table:
  1. Select signal AEB_State → Properties
  2. Click "Values" tab
  3. Click "New" to add each value:
     Raw: 0  Text: "OFF"
     Raw: 1  Text: "STANDBY"
     Raw: 2  Text: "WARNING"
     Raw: 3  Text: "ACTIVE"
     Raw: 7  Text: "NOT_AVAILABLE"

Method 2 — Global Value Table (reusable):
  1. Menu: Edit → Global Value Tables
  2. Create table "DoorStatus"
  3. Add: 0="CLOSED", 1="OPEN", 2="AJAR", 3="NOT_AVAILABLE"
  4. Assign to multiple signals: Signal → Properties → Values → Use Global Table
```

---

## 5.9 Signal Receivers (Rx Nodes)

```
1. Select signal → Properties
2. Click "Receivers" tab
3. Check the ECU nodes that receive this signal:
   ☑ CGW
   ☑ IPC
   ☑ BCM
   ☐ ECM
   ☐ ABS_ECU

Alternatively — assign from message level:
  Message → Properties → "Receivers" tab → adds all signals to selected node
```

---

## 5.10 Multiplexed Signals in CANdb++

### Setting Up Multiplexing

```
Step 1: Create the Multiplexer signal
  Signal name: Mux_Selector
  Start bit: 0
  Length: 4
  In "Multiplexer" tab: CHECK "Multiplexer signal"
  
Step 2: Create multiplexed signals
  Signal: Temp_Sensor
  In "Multiplexer" tab:
    Mux value: 0
    CHECK "Multiplexed signal"
    Multiplexer signal: Mux_Selector
    
  Signal: Press_Sensor
    Mux value: 1
    CHECK "Multiplexed signal"
    Multiplexer: Mux_Selector
```

---

## 5.11 Attributes in CANdb++

### Adding Custom Attributes

```
1. Edit → Attribute Definitions
2. Click "New"
3. Configure:
   Name: GenMsgCycleTime
   Object type: Message
   Value type: Integer
   Min: 0, Max: 10000
   Default: 0
   
4. Assign to messages:
   Select message → Attributes tab → GenMsgCycleTime = 20
```

### Commonly Needed Attributes

| Attribute | Type | Applies To | Notes |
|-----------|------|-----------|-------|
| GenMsgCycleTime | INT | Message | Cycle time ms — required for IL |
| GenMsgSendType | ENUM | Message | cyclic/event |
| GenMsgILSupport | ENUM | Message | Enables CANoe IL handling |
| GenSigStartValue | FLOAT | Signal | Init value for simulation |
| ILUsed | ENUM | Node | Enable Interaction Layer per ECU |
| NodeLayerModules | STRING | Node | CAPL simulation file |

---

## 5.12 Import and Export

### Import From Excel/CSV

```
CANdb++ → File → Import
Supported formats:
  - Excel Import via COM interface (CANdb++ add-in)
  - CSV via scripted import (CAPL or Python)
  
Manual approach for Excel matrix:
  1. Export matrix to CSV
  2. Write Python script using cantools library:
     import cantools
     db = cantools.database.Database()
     msg = cantools.database.can.Message(
         frame_id=0x244, name='AEB_Req', length=8,
         signals=[...])
     db.add_message(msg)
     cantools.database.dump_file(db, 'output.dbc')
```

### Export Options

```
File → Export:
  → Save as DBC (standard)
  → Save as ARXML (AUTOSAR exchange format)
  → Generate Symbol File (.sym) for CANalyzer
  → Export to HTML (documentation)
  → Print Network (PDF layout)
```

---

## 5.13 Validation and Error Checking

### Built-in Validation

```
Tools → Check Database (F7):
Checks for:
  ✓ Duplicate message IDs
  ✓ Undefined transmitters (not in BU_)
  ✓ Signal bit overlaps
  ✓ DLC too small for signal positions
  ✓ Undefined attribute references
  ✓ Empty message names

Viewing errors:
  Error window shows → double-click error → jumps to offending item
```

### Manual Checks Not Caught by CANdb++

```
□ Signal physical range matches OEM specification
□ Initial values match startup state
□ Timeout values match 3× cycle time rule
□ Safety-critical signals have E2E protection (alive counter + CRC)
□ Naming convention matches OEM standard
□ No test signals left in production DBC
```

---

## 5.14 CANdb++ Keyboard Shortcuts

| Action | Shortcut |
|--------|---------|
| New Message | Ctrl+M |
| New Signal | Ctrl+Shift+S |
| New Node | Ctrl+N |
| Check Database | F7 |
| Find | Ctrl+F |
| Save | Ctrl+S |
| Properties | Alt+Enter |
| Bit View | Alt+B |
| Undo | Ctrl+Z |
| Copy Object | Ctrl+C |
| Paste Object | Ctrl+V |

---

## 5.15 OEM Naming Conventions

### Message Naming

```
Format: [ECU]_[Function]_[Direction]

Examples:
  AEB_BrakeRequest     ← AEB ECU, brake request signal
  ECM_EngineStatus     ← ECM, engine status data
  BCM_DoorLock         ← BCM, door lock command
  GW_NetworkStatus     ← Gateway, network status
  IPC_SpeedDisplay     ← Cluster, display data
```

### Signal Naming

```
Format: [Function]_[Property]_[Unit if ambiguous]

Examples:
  EngineSpeed          ← clear, no unit suffix needed
  ThrottlePos_Pct      ← percentage (ambiguous without unit suffix)
  SteeringAngle_Deg    ← degrees
  WheelSpeed_FL        ← FL=Front-Left direction suffix
  DoorStatus_FL        ← FL=Front-Left
  CRC_AEB              ← CRC suffix identifies E2E signals
  Alive_Ctr_AEB        ← AliveCounter prefix convention
```

### Version Tagging in DBC

```
Add to DBC comment (CM_ "..."):
  "Version: 2.3 | Date: 2026-05-27 | Author: J.Smith | Status: RELEASE"
  "Change: Added AEB_Decel_Req signal per ECR-1234"
  "Approved: E/E Architect, System Safety Manager"
```

---

## 5.16 Common CANdb++ Mistakes

| Mistake | How to Avoid |
|---------|-------------|
| Forgetting to add node to BU_ before assigning as Tx | Add all nodes first, then create messages |
| Entering hex ID in decimal field | Always enter hex with 0x prefix — CANdb++ converts |
| Not setting GenMsgCycleTime attribute | Required for CANoe IL to work correctly |
| Signal start bit off by 1 | Use bit view to verify visually |
| Wrong ILUsed attribute on node | Set ILUsed=Yes for all transmitting ECU nodes |
| Saving in wrong format | Always verify: File → Save As → .dbc (not .arxml) |

---

## Module 05 — Knowledge Check

1. What is the CANdb++ keyboard shortcut to check database validity?
2. How do you enter a 29-bit Extended CAN ID in CANdb++?
3. What attribute must be set for CANoe Interaction Layer to transmit messages automatically?
4. Where do you set the multiplexer indicator ("M") for a signal in CANdb++?
5. What does the red color in CANdb++ Bit View indicate?
6. Which export format does AUTOSAR use instead of DBC?

**Answers:**
1. F7 (Tools → Check Database)
2. Enter the 29-bit hex ID and check the "Extended Frame" checkbox
3. GenMsgCycleTime (and GenMsgSendType="cyclic" + GenMsgILSupport="Yes")
4. Signal Properties → Multiplexer tab → check "Multiplexer signal"
5. Signal bit overlap (error — two signals share the same bit position)
6. ARXML (.arxml)
