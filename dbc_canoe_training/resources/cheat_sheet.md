# DBC / CANoe / CANdb++ Cheat Sheet

> Quick reference card for Automotive Network Engineers  
> Based on: SUV2026 ADAS Safety Bus (CAN-HS1) training program

---

## 1. DBC File Structure — Syntax Card

```
VERSION ""

NS_ :
  CM_  BA_DEF_  BA_DEF_DEF_  BA_  VAL_  SG_MUL_VAL_

BS_:

BU_: Node1 Node2 Node3

BO_ <decimal_id> <MsgName>: <dlc> <TxNode>
 SG_ <SignalName> : <StartBit>|<Length>@<ByteOrder><Sign> (<Factor>,<Offset>) [<Min>|<Max>] "<Unit>" <Receivers>

VAL_ <decimal_id> <SignalName> <RawVal> "Description" ... ;

CM_ BO_  <id>  "Message comment";
CM_ SG_  <id>  <SignalName>  "Signal comment";

BA_DEF_ BO_  "AttrName"  INT  0  10000;
BA_DEF_DEF_  "AttrName"  0;
BA_ "AttrName"  BO_  <id>  <value>;
```

### Key Rules

| Rule | Correct | Wrong |
|------|---------|-------|
| Message IDs | Decimal only in `BO_` | Never hex `0x200` in `BO_` |
| Signal spacing | One space before `SG_` | `SG_` at column 0 |
| VAL_ terminator | `... "Desc" ;` (space+semicolon) | `...;` without space |
| Extended frame IDs | `BO_ 2147483648` (add 0x80000000) | Cannot use `BO_ 0x1XXXXXXX` |

---

## 2. Signal Notation Decoder

```
SG_ SteeringAngle : 0|16@1- (0.1,0) [-3276.8|3276.7] "deg" AEB_ECU,IPC

                      │  │ │ │  │ │    │         │      │    └─ Receivers
                      │  │ │ │  │ │    └─────────┘      └─ Unit
                      │  │ │ │  │ │    Physical range
                      │  │ │ │  │ └─ Sign: + = unsigned, - = signed
                      │  │ │ │  └─ Byte order: 1 = Intel (LE), 0 = Motorola (BE)
                      │  │ └─┘
                      │  │ Factor, Offset
                      │  └─ Length in bits
                      └─ Start bit (LSB for Intel, MSB for Motorola)
```

### Signal Type Quick Table

| Notation | Byte Order | Sign | Description |
|----------|-----------|------|-------------|
| `@1+` | Intel (little-endian) | Unsigned | Most common — speed, distance |
| `@1-` | Intel (little-endian) | Signed | Signed values — temperature, angle |
| `@0+` | Motorola (big-endian) | Unsigned | Used in J1939, some OEM |
| `@0-` | Motorola (big-endian) | Signed | Motorola signed — rare |

---

## 3. Physical ↔ Raw Formula

$$
\text{Physical} = \text{Raw} \times \text{Factor} + \text{Offset}
$$

$$
\text{Raw} = \frac{\text{Physical} - \text{Offset}}{\text{Factor}}
$$

### Example: SteeringAngle

```
Signal: 0|16@1- (0.1, 0)  →  Raw is a 16-bit SIGNED integer

Physical = Raw × 0.1 + 0
  +300° → Raw = +3000 → 0x0BB8
  -300° → Raw = -3000 → 0xF448  (two's complement)
  Max raw signed 16-bit: +32767 → Physical = 3276.7°
  Min raw signed 16-bit: -32768 → Physical = -3276.8°

⚠  Offset = 0, NOT -3276.8. The negative range comes from signed representation.
```

### Example: EngineTemp

```
Signal: 24|8@1+ (0.5, -40)  →  Raw is UNSIGNED 8-bit

Physical = Raw × 0.5 + (-40) = Raw × 0.5 - 40
  Raw 0   → -40°C
  Raw 80  →   0°C
  Raw 160 →  40°C
  Raw 255 →  87.5°C

To transmit 25°C:  Raw = (25 - (-40)) / 0.5 = 65 / 0.5 = 130
```

---

## 4. Bit Numbering Quick Reference

### Intel (Little-Endian) — Start bit = LSB position

```
Byte:  | Byte 0  | Byte 1  | Byte 2  |
Bits:  |7 ... 0  |15 ... 8 |23 ... 16|

Signal WheelSpeed_FL : 0|16@1+
  Bit 0  = LSB  (Byte 0, bit 0)
  Bit 15 = MSB  (Byte 1, bit 7)
  Occupies: bits 0–15
```

### Motorola (Big-Endian) — Start bit = MSB position

```
Byte:  | Byte 0  | Byte 1  | Byte 2  |
Bits:  |7 ... 0  |15 ... 8 |23 ... 16|

Signal EngineSpeed : 7|16@0+   (Motorola)
  Bit 7  = MSB  (Byte 0, bit 7)
  Bit 8  = next (Byte 1, bit 7)  — wraps to next row, reading left-to-right
  Bit 23 = LSB
```

### Start Bit Rule Summary

| Byte Order | Start Bit Points To | Direction |
|-----------|-------------------|-----------|
| Intel `@1` | Least Significant Bit (LSB) | Count up |
| Motorola `@0` | Most Significant Bit (MSB) | Bit matrix snake |

---

## 5. CAN FD DLC Table

| DLC Value | Bytes in Payload |
|-----------|-----------------|
| 0 | 0 |
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | 7 |
| 8 | 8 |
| **9** | **12** |
| **10** | **16** |
| **11** | **20** |
| **12** | **24** |
| **13** | **32** |
| **14** | **48** |
| **15** | **64** |

DLC 0–8 are identical to classic CAN. DLC 9+ are CAN FD only.

---

## 6. Bus Load Formula

$$
\text{Bus Load (\%)} = \frac{\sum_i \frac{f_i \times b_i}{1000}}{f_{bus}} \times 100
$$

Where:
- $f_i$ = message frequency (messages/sec) = 1000 / CycleTime_ms
- $b_i$ = frame bit count = 47 + 8×DLC (for standard CAN 2.0B)
- $f_{bus}$ = bus bit rate (bits/sec)

### Example — CAN-HS1 (500 Kbps)

| Message | Cycle | DLC | Bits | f (msg/s) | Load |
|---------|-------|-----|------|-----------|------|
| WheelSpeed | 10ms | 8 | 111 | 100 | 2.22% |
| AEB_Req | 20ms | 8 | 111 | 50 | 1.11% |
| VehicleStatus | 10ms | 8 | 111 | 100 | 2.22% |
| EPS_Status | 20ms | 4 | 79 | 50 | 0.79% |
| IPC_Display | 100ms | 8 | 111 | 10 | 0.22% |
| BCM_Status | 100ms | 6 | 95 | 10 | 0.19% |
| **Total** | | | | | **~6.75%** |

---

## 7. Common CAN IDs Reference

| ID (Hex) | Decimal | Purpose |
|----------|---------|---------|
| 0x7DF | 2015 | OBD2 / UDS Functional Request (all ECUs) |
| 0x7E0 | 2016 | UDS Physical Request → ECM (default) |
| 0x7E1 | 2017 | UDS Physical Request → TCM |
| 0x7E8 | 2024 | UDS Response from ECM |
| 0x7EF | 2031 | UDS Physical Request → BCM |
| 0x18DB33F1 | 29-bit | SAE J1939 Global Request |
| 0x18FEF100 | 29-bit | SAE J1939 EEC1 (Engine Speed) |
| 0x18FF0000 | 29-bit | SAE J1939 Proprietary A2 range |

---

## 8. Alive Counter Convention

| Value | Meaning |
|-------|---------|
| 0–14 | Valid rolling counter (increments each cycle) |
| 15 (0xF) | INVALID — signal not available or fault |
| Wrap | After 14 → next is 0 (NOT 15) |

```
Sequence: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 0, 1, 2, ...
                                                                ^
                                                           wraps to 0
```

---

## 9. ASIL vs E2E Requirements Table

| ASIL | Safety Level | E2E Required | Alive Counter | CRC | Monitor Interval |
|------|-------------|--------------|---------------|-----|-----------------|
| QM | Not safety-relevant | Optional | Optional | Optional | ≤ 3× cycle |
| A | Low | Recommended | Yes (4-bit) | CRC8 | ≤ 3× cycle |
| B | Medium | Required | Yes (4-bit) | CRC8 | ≤ 3× cycle |
| C | High | Required | Yes (4-bit) | CRC16 | ≤ 2× cycle |
| D | Highest | Required | Yes (8-bit) | CRC16 | ≤ 1× cycle |

---

## 10. CANoe Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F5 | Start Measurement |
| F6 | Stop Measurement |
| F7 | Pause Measurement |
| F9 | Open Measurement Setup |
| Ctrl+T | Open Trace Window |
| Ctrl+G | Open Graphics Window |
| Ctrl+Shift+T | Open Test Module |
| Ctrl+Z | Undo |
| Alt+1..9 | Switch Layout Desk |
| Ctrl+S | Save Configuration |
| Ctrl+Shift+S | Save Configuration As |

---

## 11. CANdb++ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F7 | Validate Database |
| Ctrl+N | New Database |
| Ctrl+O | Open Database |
| Ctrl+S | Save Database |
| Ctrl+E | Export |
| Insert | Add new item (in lists) |
| Delete | Delete selected item |
| F2 | Rename selected item |
| Ctrl+F | Search (Find) |
| Ctrl+D | Duplicate selected |

---

## 12. DBC Attribute Quick Reference

| Attribute | Type | Applied To | Purpose |
|-----------|------|-----------|---------|
| `GenMsgCycleTime` | INT | BO_ | Cycle time in ms (used by IL) |
| `GenMsgSendType` | ENUM | BO_ | `cyclic`, `event`, `noMsgSendType` |
| `GenMsgILSupport` | ENUM | BO_ | Enable CANoe Interaction Layer |
| `GenSigStartValue` | FLOAT | SG_ | Initial/default signal value |
| `ASIL` | ENUM | BO_ | Safety integrity level |
| `VFrameFormat` | ENUM | BO_ | `StandardCAN`, `ExtendedCAN`, `StandardCAN_FD`, `ExtendedCAN_FD` |
| `E2EProfile` | ENUM | SG_ | `None`, `P01`, `P02`, `P04` |
| `ILUsed` | ENUM | BU_ | Node uses Interaction Layer |

---

## 13. Signal Range & DLC Bitfield Reference

### DLC → Maximum Number of Signals (Intel, non-overlapping)

| DLC | Bytes | Max bits | Max 1-bit signals | Max 8-bit signals | Max 16-bit signals |
|-----|-------|----------|------------------|------------------|--------------------|
| 1 | 1 | 8 | 8 | 1 | 0 |
| 2 | 2 | 16 | 16 | 2 | 1 |
| 4 | 4 | 32 | 32 | 4 | 2 |
| 8 | 8 | 64 | 64 | 8 | 4 |
| 64 | 64 | 512 | 512 | 64 | 32 |

---

## 14. Python cantools Quick Reference

```python
import cantools
import can

# Load DBC
db = cantools.database.load_file('vehicle_network.dbc')

# List messages
for msg in db.messages:
    print(f"0x{msg.frame_id:03X}  {msg.name}  DLC={msg.length}")

# Decode a raw frame
raw = bytes([0x01, 0x32, 0xE8, 0x03, 0x64, 0x05, 0xAB, 0x00])
decoded = db.decode_message('AEB_Req', raw)
print(decoded)
# {'AEB_Active': 1, 'AEB_State': 0, 'AEB_Decel_Req': 5.0, ...}

# Encode a message
data = db.encode_message('WheelSpeed', {
    'WheelSpeed_FL': 50.00,
    'WheelSpeed_FR': 50.00,
    'WheelSpeed_RL': 49.50,
    'WheelSpeed_RR': 49.50,
})
print(data.hex())

# Get signal object
sig = db.get_message_by_name('AEB_Req').get_signal_by_name('AEB_State')
print(f"Min={sig.minimum} Max={sig.maximum} Unit='{sig.unit}'")
```

---

## 15. Signal Overlap Detection (Python)

```python
def check_overlaps(message):
    bits = []
    for sig in message.signals:
        for i in range(sig.length):
            bit = sig.start + i
            if bit in bits:
                print(f"OVERLAP: {sig.name} at bit {bit}")
                return False
            bits.append(bit)
    return True
```

---

## 16. DBC ID Allocation Ranges (CAN 2.0B)

| Range (Hex) | Range (Dec) | Domain |
|------------|------------|--------|
| 0x000–0x07F | 0–127 | Network management, NM |
| 0x080–0x0FF | 128–255 | Engine / Powertrain |
| 0x100–0x1FF | 256–511 | Chassis safety (ABS, ESC) |
| 0x200–0x2FF | 512–767 | ADAS sensors |
| 0x300–0x3FF | 768–1023 | Powertrain / ECM |
| 0x400–0x4FF | 1024–1279 | Body electronics |
| 0x500–0x5FF | 1280–1535 | Infotainment / HMI |
| 0x600–0x67F | 1536–1663 | Diagnostics (UDS) |
| 0x7DF | 2015 | OBD2 functional |
| 0x7E0–0x7EF | 2016–2031 | UDS physical |

---

*Generated as part of the DBC/CANoe Complete Training Program — SUV2026 ADAS Safety Bus*
