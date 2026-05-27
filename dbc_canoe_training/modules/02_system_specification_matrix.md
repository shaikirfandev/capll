# Module 02 — Understanding the System Specification Matrix

> **Level**: Beginner–Intermediate  
> **Duration**: ~2 hours  
> **Goal**: Learn how to read OEM communication matrices and extract signal requirements for DBC creation.

---

## 2.1 What Is a System Specification Matrix?

A **System Specification Matrix** (also called **Communication Matrix**, **Signal Matrix**, or
**Network Design Specification**) is the authoritative engineering document that defines:

- Which ECU sends which message
- What signals are inside each message
- How signals are encoded (bit position, length, endianness)
- Signal scaling and physical units
- Timing requirements (cycle time, timeout)

```
Real-world document names:
  ├── "CAN Communication Matrix" (.xlsx, .csv)
  ├── "Network Design Specification" (.pdf)
  ├── "ECU Communication Specification" (.docx)
  ├── "Signal Database" (exported from CANdb++ or ARXML)
  └── "AUTOSAR System Description" (.arxml)
```

### Who Creates the Communication Matrix?

```
System Architect (OEM)
      │ defines top-level signals & IDs
      ▼
E/E Architect
      │ assigns bus topology, message IDs
      ▼
ECU Integration Engineer
      │ populates signal bit positions & timing
      ▼
Software Engineer (each ECU supplier)
      │ implements signals in code
      ▼
Validation Engineer
      │ uses matrix to create DBC and test
```

---

## 2.2 System Specification Matrix — Column Structure

A standard OEM communication matrix has these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Message Name** | Unique name for the CAN message | `AEB_Req` |
| **Message ID** | Arbitration ID (hex or decimal) | `0x244` / `580` |
| **DLC** | Number of data bytes | `8` |
| **Cycle Time** | Transmission interval (ms) | `20` |
| **Timeout** | Receiver timeout (ms) | `60` |
| **Tx ECU** | Transmitter ECU name | `AEB_ECU` |
| **Rx ECU** | Receiver ECU(s) | `CGW, IPC, BCM` |
| **Bus** | CAN bus identifier | `CAN_HS1` |
| **Signal Name** | Unique signal name | `AEB_Active` |
| **Start Bit** | LSB bit position (or MSB for Motorola) | `0` |
| **Length** | Signal width in bits | `1` |
| **Byte Order** | Intel or Motorola | `Intel` |
| **Data Type** | Signed or Unsigned | `Unsigned` |
| **Factor** | Scaling multiplier | `0.01` |
| **Offset** | Scaling offset | `0` |
| **Min** | Minimum physical value | `0` |
| **Max** | Maximum physical value | `655.35` |
| **Unit** | Physical unit | `m` |
| **Initial Value** | Default value (raw) | `0x00` |
| **Invalid Value** | Value indicating "not available" | `0xFFFF` |
| **Description** | Signal purpose | `AEB activation flag` |

---

## 2.3 Sample OEM Communication Matrix

### Vehicle: Compact SUV — CAN-HS Bus (500 Kbps)

#### Message Table

| Msg Name | ID (hex) | DLC | Cycle (ms) | Timeout (ms) | Tx ECU | Rx ECU |
|----------|----------|-----|-----------|--------------|--------|--------|
| AEB_Req | 0x244 | 8 | 20 | 60 | AEB_ECU | CGW, IPC, BCM |
| VehicleStatus | 0x300 | 8 | 10 | 30 | ECM | ABS, AEB, IPC |
| WheelSpeed | 0x200 | 8 | 10 | 30 | ABS_ECU | ECM, AEB, ESC |
| IPC_Display | 0x350 | 8 | 100 | 300 | IPC | CGW |
| BCM_Status | 0x420 | 6 | 100 | 300 | BCM | CGW, IPC |
| HMI_AudioCmd | 0x510 | 4 | Event | — | HMI_ECU | HU |
| GW_Status | 0x640 | 2 | 1000 | 3000 | CGW | All |
| Diag_Req | 0x7E0 | 8 | Event | 25 | Tester | All ECUs |

#### Signal Table for `AEB_Req` (ID=0x244, DLC=8)

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init | Invalid |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|---------|
| AEB_Active | 0 | 1 | Intel | UNS | 1 | 0 | 0 | 1 | — | 0 | — |
| AEB_State | 1 | 3 | Intel | UNS | 1 | 0 | 0 | 7 | — | 0 | 7 |
| AEB_Decel_Req | 4 | 8 | Intel | UNS | 0.1 | 0 | 0 | 25.5 | m/s² | 0 | 0xFF |
| AEB_Obj_Distance | 12 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | m | 0 | 0xFFFF |
| AEB_TTC | 28 | 8 | Intel | UNS | 0.01 | 0 | 0 | 2.55 | s | 0 | 0xFF |
| Alive_Counter | 36 | 4 | Intel | UNS | 1 | 0 | 0 | 14 | — | 0 | 15 |
| CRC_AEB | 40 | 8 | Intel | UNS | 1 | 0 | 0 | 255 | — | 0 | — |
| Reserved | 48 | 16 | Intel | UNS | 1 | 0 | — | — | — | 0 | — |

#### Signal Table for `VehicleStatus` (ID=0x300, DLC=8)

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|
| EngineSpeed | 0 | 16 | Intel | UNS | 0.25 | 0 | 0 | 16383.75 | rpm | 0 |
| ThrottlePos | 16 | 8 | Intel | UNS | 0.4 | 0 | 0 | 100 | % | 0 |
| EngineTemp | 24 | 8 | Intel | SGN | 0.5 | -40 | -40 | 87.5 | °C | 40 |
| EngineState | 32 | 3 | Intel | UNS | 1 | 0 | 0 | 6 | — | 0 |
| TransmMode | 35 | 3 | Intel | UNS | 1 | 0 | 0 | 5 | — | 0 |
| FuelPress | 38 | 10 | Intel | UNS | 0.1 | 0 | 0 | 102.3 | bar | 0 |
| Alive_Counter | 48 | 4 | Intel | UNS | 1 | 0 | 0 | 14 | — | 0 |
| CRC_VS | 52 | 8 | Intel | UNS | 1 | 0 | 0 | 255 | — | 0 |

#### Signal Table for `WheelSpeed` (ID=0x200, DLC=8)

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|
| WheelSpeed_FL | 0 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | km/h |
| WheelSpeed_FR | 16 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | km/h |
| WheelSpeed_RL | 32 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | km/h |
| WheelSpeed_RR | 48 | 16 | Intel | UNS | 0.01 | 0 | 0 | 655.35 | km/h |

#### Signal Table for `BCM_Status` (ID=0x420, DLC=6)

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Unit | Values |
|-------------|-----------|--------|------------|------|--------|--------|------|--------|
| DoorFL_Status | 0 | 2 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open,2=Ajar,3=NA |
| DoorFR_Status | 2 | 2 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open,2=Ajar,3=NA |
| DoorRL_Status | 4 | 2 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open,2=Ajar,3=NA |
| DoorRR_Status | 6 | 2 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open,2=Ajar,3=NA |
| Hood_Status | 8 | 1 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open |
| Trunk_Status | 9 | 1 | Intel | UNS | 1 | 0 | — | 0=Closed,1=Open |
| IgnitionState | 10 | 3 | Intel | UNS | 1 | 0 | — | 0=OFF,1=ACC,2=ON,3=START,4=NA |
| HazardActive | 13 | 1 | Intel | UNS | 1 | 0 | — | 0=OFF,1=ON |
| LowBeam | 14 | 1 | Intel | UNS | 1 | 0 | — | 0=OFF,1=ON |
| HighBeam | 15 | 1 | Intel | UNS | 1 | 0 | — | 0=OFF,1=ON |
| WiperState | 16 | 3 | Intel | UNS | 1 | 0 | — | 0=OFF,1=INT,2=LOW,3=HIGH,4=WASH |
| Alive_Counter | 40 | 4 | Intel | UNS | 1 | 0 | — | 0–14, 15=Invalid |
| CRC_BCM | 44 | 8 | Intel | UNS | 1 | 0 | — | — |

---

## 2.4 Signal Extraction Workflow

```
STEP 1: RECEIVE COMMUNICATION MATRIX FROM OEM/SYSTEM TEAM
    └─ Format: Excel/CSV or PDF
    └─ Verify version and approval status

STEP 2: IDENTIFY BUS TOPOLOGY
    ├─ List all CAN buses (CAN_HS1, CAN_HS2, CAN_FD1, ...)
    ├─ List all ECUs per bus
    └─ Identify gateway routing

STEP 3: EXTRACT MESSAGES PER BUS
    ├─ Message Name, ID, DLC, Cycle Time
    └─ Tx/Rx node assignments

STEP 4: EXTRACT SIGNALS PER MESSAGE
    ├─ Signal Name, Start Bit, Length, Endianness
    ├─ Factor, Offset, Min, Max, Unit
    └─ Initial and Invalid values

STEP 5: VALIDATE SIGNAL PACKING
    ├─ Check for overlapping bits
    ├─ Verify total bits ≤ DLC × 8
    └─ Confirm endianness interpretation

STEP 6: CREATE DBC FILE (Module 04/05)
```

---

## 2.5 Understanding Bit Position (Start Bit)

This is the **most confusing part** for beginners. The start bit definition differs between
Intel (Little-Endian) and Motorola (Big-Endian).

### Intel (Little-Endian) — Start Bit = LSB Position

```
Byte: |  B0  |  B1  |  B2  |  B3  |
Bit:  |76543210|76543210|76543210|76543210|
                                    ↑
CAN bit numbering for Intel:
  Bit 0 = Byte 0, bit 0 (LSB of first byte)
  Bit 7 = Byte 0, bit 7
  Bit 8 = Byte 1, bit 0
  Bit 15= Byte 1, bit 7

Signal VehicleSpeed: Start=0, Length=12, Intel
  Bits used: 0,1,2,3,4,5,6,7 (Byte 0) + 8,9,10,11 (Byte 1 bits 0-3)
  Raw bytes in frame: [B0=0xF0] [B1=0x05]
  Raw value: 0x05F0 = 1520 decimal (after bit extraction)
  Physical: 1520 × 0.01 = 15.20 km/h  ✗ Wrong
  Wait — Intel: LSB=bit0=B0.0, value assembled LSB-first
  Raw = B1[3:0] << 8 | B0[7:0] = 0x5F0 = 1520 → 1520×0.01 = 15.20 km/h ✓
```

### Motorola (Big-Endian) — Start Bit = MSB Position

```
Motorola bit numbering within bytes:
  Byte 0 bits: 7,6,5,4,3,2,1,0 (MSB first)
  Byte 1 bits: 15,14,13,12,11,10,9,8

Signal EngineRPM: Start=24 (MSB), Length=16, Motorola
  MSB is bit 24 (Byte 3, bit 0 in Motorola numbering)
  Signal spans downward: bits 24,25,...,39
  ← Complex; CANdb++ handles this automatically
```

**Industry recommendation**: Prefer Intel (Little-Endian) for new designs — simpler bit math.

---

## 2.6 Value Definitions (Enumerations)

Many signals are discrete states with named values:

```
Signal: EngineState (3 bits, 0–7)
  Value table:
    0 = "OFF"
    1 = "CRANKING"
    2 = "IDLE"
    3 = "RUNNING"
    4 = "OVERHEATING"
    5 = "SHUTDOWN"
    6 = "FAULT"
    7 = "NOT_AVAILABLE"
```

These map directly to DBC `VAL_` entries (covered in Module 03).

---

## 2.7 Initial Value and Invalid Value

### Initial Value
The value the transmitter ECU sends at startup before valid data is available.

```
Example:
  VehicleSpeed — Initial = 0 (vehicle is stopped at startup)
  EngineTemp   — Initial = 0 raw (= -40°C with offset -40)
  AEB_State    — Initial = 0 (= OFF)
```

### Invalid Value
A specific raw value meaning "data not available" or "sensor error".

```
Example:
  VehicleSpeed: 16-bit, Invalid = 0xFFFF (= 655.35 km/h — physically impossible)
  EngineTemp:   8-bit, Invalid = 0xFF (= 87.5°C or a reserved "not available" code)
  AEB_State:    3-bit, Invalid = 7 (= "NOT_AVAILABLE")

Rule: Invalid value must be OUTSIDE the physically meaningful range.
```

---

## 2.8 Functional Decomposition — Reading OEM Requirements

### OEM Requirement (High Level)
> "The AEB system shall request deceleration from the powertrain when a collision is imminent."

### System Decomposition

```
OEM Requirement
      │
      ▼
System Function: AEB_Request transmission
      │
      ▼
Interface Requirement:
  - AEB ECU → transmit CAN message with deceleration request
  - Message ID: TBD (assigned by E/E architect)
  - Cycle time: ≤20ms (safety requirement from FMEA)
      │
      ▼
Signal Requirements:
  - AEB_Active:       1 bit,  indicates request is active
  - AEB_Decel_Req:    8 bits, deceleration value 0–25.5 m/s²
  - AEB_Obj_Distance: 16 bits, detected obstacle distance 0–655m
  - AEB_TTC:          8 bits, Time-to-Collision 0–2.55 seconds
  - Alive_Counter:    4 bits, E2E protection
  - CRC:              8 bits, E2E protection
      │
      ▼
DBC Signal Definition (Module 04)
```

---

## 2.9 Common Matrix Reading Mistakes

| Mistake | Impact | Prevention |
|---------|--------|-----------|
| Reading start bit as byte index | Completely wrong bit packing | Always check if unit is "bit number" not "byte number" |
| Mixing Intel/Motorola within same signal | Garbage decoded value | Confirm endianness per signal row |
| Ignoring invalid value | Treating "not available" as real data | Always check invalid value before using signal |
| Using physical min/max as raw range | Scaling errors | Convert min/max to raw: raw = (phys - offset) / factor |
| Missing timeout column | No timeout detection in ECU | Always extract timeout; if missing, assume 3× cycle time |

---

## 2.10 Extracting DBC Parameters from Matrix

### Step-by-Step for Signal `AEB_Decel_Req`

| Matrix Column | Value | DBC Parameter |
|---------------|-------|---------------|
| Signal Name | AEB_Decel_Req | `SG_ AEB_Decel_Req` |
| Start Bit | 4 | `: 4\|` |
| Length | 8 | `8@` |
| Byte Order | Intel | `1` |
| Type | Unsigned | `+` |
| Factor | 0.1 | `(0.1,` |
| Offset | 0 | `0)` |
| Min | 0 | `[0\|` |
| Max | 25.5 | `25.5]` |
| Unit | m/s² | `"m/s²"` |
| Initial Value | 0 | Used in `BA_` attribute |

**Result in DBC:**
```
SG_ AEB_Decel_Req : 4|8@1+ (0.1,0) [0|25.5] "m/s2" Vector__XXX
```

---

## Module 02 — Knowledge Check

1. What is the difference between "Message ID" and "CAN ID"?
2. If Factor=0.5, Offset=-40, Min=-40°C, Max=87.5°C, what is the raw range (min and max)?
3. A signal has Start Bit=8, Length=16, Intel. Which bytes does it occupy?
4. What does an Invalid Value of 0xFF typically indicate?
5. Who is typically responsible for creating the OEM communication matrix?
6. A message has Cycle=10ms. The matrix doesn't specify a Timeout. What value would you use?

**Answers:**
1. They are the same — "Message ID" and "CAN ID" both refer to the Arbitration ID
2. Raw_min = (-40-(-40))/0.5 = 0; Raw_max = (87.5-(-40))/0.5 = 255 → Range: 0–255
3. Bytes 1 and 2 (bits 8–23)
4. Data not available / sensor fault / signal invalid
5. E/E Architect at the OEM, in coordination with system architect
6. 3× cycle time = 30ms
