# Module 01 — Automotive Communication Basics

> **Level**: Beginner  
> **Duration**: ~3 hours  
> **Goal**: Understand every automotive bus protocol, signal concept, and bit-level parameter before touching a DBC file.

---

## 1.1 Why Automotive Networks Exist

Modern vehicles contain 70–100+ ECUs (Electronic Control Units). Without a shared communication
network, each ECU would need a dedicated wire to every other ECU — making the harness heavier
than the engine.

```
WITHOUT NETWORK (point-to-point wiring):
Engine ECU ──────────────────────── Cluster
Engine ECU ──────────────────────── ABS ECU
Engine ECU ──────────────────────── TCM
Engine ECU ──────────────────────── BCM
Result: Hundreds of wires, impossible to maintain

WITH CAN NETWORK:
Engine ECU ─┐
Cluster    ─┤──── CAN BUS (2 wires) ───── All ECUs share one bus
ABS ECU    ─┤
TCM        ─┘
Result: One pair of wires, all ECUs communicate
```

---

## 1.2 CAN — Controller Area Network (ISO 11898)

### Overview
- Developed by Bosch in 1986
- Two-wire differential bus: CAN-H and CAN-L
- Multi-master, broadcast protocol
- Speeds: Low-Speed CAN (125 Kbps), High-Speed CAN (500 Kbps – 1 Mbps)

### CAN Frame Structure

```
 ┌─────┬────────┬───┬───┬───┬──────┬──────────────────┬───────┬───┬──────┬──────┐
 │ SOF │ ARB ID │RTR│IDE│r0 │ DLC  │   DATA (0–8 B)   │  CRC  │ACK│ EOF  │ IFS  │
 │  1b │  11b   │1b │1b │1b │  4b  │    0–64 bits     │ 15b+1b│2b │  7b  │  3b  │
 └─────┴────────┴───┴───┴───┴──────┴──────────────────┴───────┴───┴──────┴──────┘
 Total: ~111 bits for 8-byte frame @ 500Kbps = ~222µs per frame
```

### Key CAN Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Arbitration ID** | 11-bit (Standard) or 29-bit (Extended) frame identifier | `0x244` = AEB request |
| **DLC** | Data Length Code — number of data bytes (0–8) | DLC=8 → 8 bytes |
| **SOF** | Start of Frame — dominant bit starts transmission | Bit = 0 |
| **EOF** | End of Frame — 7 recessive bits | Bits = 1111111 |
| **ACK** | Any receiver drives ACK dominant if received OK | Bus-level acknowledgment |
| **CRC** | 15-bit CRC for error detection | Polynomial: x¹⁵+x¹⁴+... |
| **RTR** | Remote Transmission Request — request data from another node | RTR=1 |

### CAN Bus Arbitration (CSMA/CA)

```
Node A sends:  1  1  0  1  0  0  1  (ID = 0x69)
Node B sends:  1  1  0  0  1  1  0  (ID = 0x61)
Bus result:    1  1  0  0  1  1  0  ← Node B wins (lower ID = higher priority)
                          ↑
                    Node A sees 0, was sending 1 → lost, backs off
```

**Rule**: Lower Arbitration ID = Higher Priority

### CAN Bit Timing

```
One CAN Bit:
┌──────────┬──────────────┬──────────┐
│  SYNC_SEG│  PROP + PH1  │   PH2    │
│    1 Tq  │   n × Tq     │  m × Tq  │
└──────────┴──────────────┴──────────┘
         ↑ Sample point (~80% for 500Kbps CAN-HS)
```

### Error Handling

| Error Type | Cause | Detection |
|------------|-------|-----------|
| Bit Error | Node reads back different bit than sent | Self-monitoring |
| Stuff Error | >5 consecutive same bits | Bit stuffing rule violated |
| Form Error | Fixed-format field has wrong value | EOF, ACK delimiter |
| CRC Error | Received CRC ≠ calculated CRC | CRC field |
| ACK Error | No ACK received (no other node on bus) | ACK field |

### Error Counter States

```
Normal → Warning (TEC/REC > 96) → Error Passive (TEC/REC > 127) → Bus-Off (TEC > 255)
```

---

## 1.3 CAN FD — CAN with Flexible Data Rate (ISO 11898-1:2015)

### What Changed from Classical CAN

| Parameter | Classical CAN | CAN FD |
|-----------|--------------|--------|
| Max payload | 8 bytes | **64 bytes** |
| Data phase speed | Up to 1 Mbps | **Up to 8 Mbps** |
| Frame format | Standard | BRS + ESI bits added |
| DLC encoding | 0–8 linear | 0–15 (9→12, 10→16, …15→64) |
| CRC | 15-bit | **17-bit or 21-bit** |

### CAN FD Frame Structure

```
 ┌─────┬────────┬───┬─────┬──────┬──────────────────────┬─────────┬───┐
 │ SOF │ ARB ID │RRS│ FDF │ DLC  │   DATA (0–64 B)      │  CRC    │ACK│
 │  1b │  11b   │1b │  1b │  4b  │  0–512 bits max      │17 or 21b│2b │
 └─────┴────────┴───┴─────┴──────┴──────────────────────┴─────────┴───┘
                              ↑ BRS: Bit Rate Switch (triggers speed change)
```

### CAN FD DLC Table

| DLC Value | Bytes Transmitted |
|-----------|-------------------|
| 0–8 | 0–8 (same as CAN) |
| 9 | 12 |
| 10 | 16 |
| 11 | 20 |
| 12 | 24 |
| 13 | 32 |
| 14 | 48 |
| 15 | 64 |

### When to Use CAN FD

- ADAS ECUs (radar point cloud, camera metadata)
- OTA software download
- Calibration data transfer
- Any message > 8 bytes

---

## 1.4 LIN — Local Interconnect Network

### Overview
- Single-wire protocol
- Speed: 1–20 Kbps (typically 10.4 or 19.2 Kbps)
- Master-slave architecture (1 master, up to 16 slaves)
- Cost: ~$0.10/node vs ~$1.00/node for CAN
- ISO 17987, SAE J2602

### Architecture

```
BCM (LIN Master)
     │
     ├── Mirror Motor (LIN Slave)
     ├── Window Regulator (LIN Slave)
     ├── Seat Motor (LIN Slave)
     └── Rain Sensor (LIN Slave)
```

### LIN Frame Structure

```
Break field (13 bits) → Sync (0x55) → PID (6-bit ID + 2-bit parity) → Data (1–8B) → Checksum
```

### LIN vs CAN

| Feature | LIN | CAN |
|---------|-----|-----|
| Speed | 20 Kbps | 1 Mbps |
| Wires | 1 | 2 |
| Topology | Single master | Multi-master |
| Cost | Very low | Low |
| Use case | Comfort/body | Powertrain/chassis |

---

## 1.5 FlexRay (ISO 17458)

### Overview
- Deterministic, fault-tolerant protocol
- Speed: 10 Mbps per channel (dual channel = 20 Mbps)
- Used in safety-critical X-by-wire systems
- Common in BMW, Mercedes-Benz suspension, steering

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                  FlexRay Cluster                      │
│  Channel A: ────────────────────────────────────     │
│             ECU1    ECU2    ECU3    ECU4              │
│  Channel B: ────────────────────────────────────     │
│  (redundant identical channel for fault tolerance)   │
└──────────────────────────────────────────────────────┘
```

### FlexRay Cycle Structure

```
One Communication Cycle (e.g., 5ms):
┌──────────────┬──────────────┬───────────┬──────────┐
│  Static Seg  │  Dynamic Seg │  Symbol W │  NIT     │
│ (TDMA slots) │ (FTDMA flex) │ (wakeup)  │(idle)    │
└──────────────┴──────────────┴───────────┴──────────┘
```

### When to Use FlexRay
- Active suspension control
- Steer-by-wire
- Brake-by-wire
- Any X-by-wire requiring determinism < 1ms

---

## 1.6 Automotive Ethernet (OPEN Alliance, IEEE 802.3)

### Overview
- 100BASE-T1: 100 Mbps, single unshielded pair
- 1000BASE-T1: 1 Gbps (ADAS, backbone)
- SOME/IP: Service-Oriented Middleware over IP (AUTOSAR)
- AVB/TSN: Time-Sensitive Networking for real-time (IEEE 802.1AS)

### Automotive Ethernet Use Cases

```
Camera (1Gbps) ─────────────┐
Radar (100Mbps) ─────────────┤── Ethernet Switch ──── ADAS Domain Controller
LiDAR (1Gbps)  ─────────────┤                         (NVidia Orin / TDA4VM)
GPS/Map (100Mbps) ───────────┘
```

### SOME/IP Protocol Stack

```
Application Layer:  SOME/IP (Service-Oriented communication)
Transport Layer:    UDP (events) / TCP (reliable)
Network Layer:      IPv4/IPv6
Data Link:          Ethernet MAC
Physical:           100BASE-T1 / 1000BASE-T1
```

---

## 1.7 UDS Diagnostics (ISO 14229)

### Overview
UDS = Unified Diagnostic Services — diagnostic protocol running over CAN (ISO-TP), LIN, Ethernet (DoIP)

### Common UDS Services

| Service ID | Name | Purpose |
|------------|------|---------|
| 0x10 | DiagnosticSessionControl | Switch to Extended/Programming session |
| 0x22 | ReadDataByIdentifier (RDBI) | Read DID values (e.g., VIN, ECU info) |
| 0x2E | WriteDataByIdentifier (WDBI) | Write calibration data |
| 0x27 | SecurityAccess | Unlock ECU for sensitive operations |
| 0x31 | RoutineControl | Execute routines (checksum, learn) |
| 0x34/0x36/0x37 | Download/Transfer | Flash firmware |
| 0x14 | ClearDiagnosticInfo | Clear DTCs |
| 0x19 | ReadDTCInformation | Read fault codes |

### UDS on CAN (ISO 15765-2 Transport)

```
Request:  [0x7E0] 02 10 03       (Enter Extended Session)
Response: [0x7E8] 06 50 03 00 19 00 C8   (Positive response)
```

---

## 1.8 J1939 Basics (SAE J1939)

### Overview
- CAN-based protocol for heavy vehicles (trucks, buses, agriculture)
- 250 Kbps, uses **29-bit extended CAN IDs**
- PGN (Parameter Group Number) identifies the message type
- SPN (Suspect Parameter Number) identifies the signal

### J1939 ID Structure (29-bit)

```
Bits 28–26: Priority (3 bits, 0=highest, 7=lowest)
Bit 25:     Reserved
Bit 24:     Data Page
Bits 23–16: PF (PDU Format — determines PDU type)
Bits 15–8:  PS (PDU Specific — destination or group extension)
Bits 7–0:   Source Address (0x00–0xFE, 0xFF=broadcast)
```

### J1939 vs CAN DBC

| Feature | CAN DBC | J1939 DBC |
|---------|---------|-----------|
| ID format | 11-bit standard | 29-bit extended |
| Signal naming | Free | SPN-based |
| Tool support | Full CANdb++ | J1939 editor in CANdb++ |
| DBC keyword | `BO_ 0x244` | `BO_ 0x8CF00400` (extended) |

---

## 1.9 Signal vs Message — Core Concepts

### Message
A **CAN message** is a packet transmitted on the bus with:
- Fixed Arbitration ID (who sends it)
- Fixed DLC (how many bytes)
- Fixed cycle time (how often)

### Signal
A **CAN signal** is a specific piece of data packed inside the message bytes.

```
CAN Message 0x244 (AEB_Request), DLC=8:

Byte:  B0        B1        B2        B3        B4        B5        B6        B7
Bits: 76543210  76543210  76543210  76543210  76543210  76543210  76543210  76543210

Signal AEB_Req_Active:      Bits 0–0   (1 bit)
Signal AEB_Req_Decel:       Bits 1–8   (8 bits, little-endian)
Signal VehicleSpeed_Kmh:    Bits 9–20  (12 bits, little-endian)
Signal AEB_State:           Bits 21–23 (3 bits)
Signal Alive_Counter:       Bits 24–27 (4 bits)
Signal CRC_Value:           Bits 28–35 (8 bits)
```

---

## 1.10 Signal Properties — Detailed Explanation

### Arbitration ID (Message Identifier)

```
Standard (11-bit): Range 0x000–0x7FF
  0x000 = highest priority (dangerous — avoid for non-critical msgs)
  0x7FF = lowest priority

Extended (29-bit): Range 0x00000000–0x1FFFFFFF
  J1939 and CANopen use extended IDs
  DBC notation: BO_ 2566844416 Message_Name (the decimal form of 0x98F00300)
```

**Industry Convention for 11-bit IDs:**

| Range | Typical Use |
|-------|------------|
| 0x000–0x0FF | Powertrain critical (Engine, ABS, EPS) |
| 0x100–0x2FF | Chassis/Safety (AEB, ESC, Airbag) |
| 0x300–0x4FF | Body/Comfort (BCM, Climate, Windows) |
| 0x500–0x6FF | Infotainment / HMI |
| 0x600–0x6FF | Diagnostic (UDS physical + functional) |
| 0x700–0x7EF | Less critical / status messages |
| 0x7DF | UDS Functional Addressing |
| 0x7E0–0x7EF | UDS Physical Addressing per ECU |

---

### DLC — Data Length Code

```
DLC  Bytes  Typical Use
 0     0    Remote frame (RTR)
 1     1    Single binary flag
 2     2    Short sensor value
 4     4    Two 16-bit values
 8     8    Standard ECU message (most common)
```

**DLC is fixed per message** — do not confuse with variable-length.

---

### Endianness (Byte Order)

```
Value = 0x1234 (decimal 4660)

Big-Endian (Motorola / Intel MPC5xxx, Renesas):
  Memory address: LOW  → HIGH
  Byte storage:   0x12 → 0x34
  Bit numbering: MSB first in DBC (start_bit = MSB position)

Little-Endian (Intel / ARM Cortex-M):
  Memory address: LOW  → HIGH
  Byte storage:   0x34 → 0x12
  Bit numbering: LSB first in DBC (start_bit = LSB position)
```

**Critical**: Endianness mismatch causes completely wrong decoded values!

**DBC Notation:**
```
SG_ VehicleSpeed : 8|12@1+   ← @1 = little-endian (Intel), + = unsigned
SG_ EngineRPM   : 24|16@0+  ← @0 = big-endian (Motorola), + = unsigned
```

---

### Scaling Formula — Physical Value Calculation

```
Physical_Value = Raw_Value × Factor + Offset

Where:
  Raw_Value = integer bits extracted from CAN frame
  Factor    = scaling multiplier (resolution)
  Offset    = value added after scaling (can be negative)

Example: VehicleSpeed
  Factor = 0.01 km/h per bit
  Offset = 0
  Raw    = 10000 (0x2710)
  Physical = 10000 × 0.01 + 0 = 100.00 km/h

Example: Temperature
  Factor = 0.5 °C per bit
  Offset = -40 °C (because raw 0 = -40°C)
  Raw    = 160
  Physical = 160 × 0.5 + (-40) = 80 - 40 = 40°C

Example: Battery Current (can be negative)
  Factor = 0.1 A per bit
  Offset = -3276.8 A
  Raw    = 32768 (0x8000)
  Physical = 32768 × 0.1 + (-3276.8) = 3276.8 - 3276.8 = 0.0 A
```

---

### Signal Value Range

```
For unsigned signal, N bits:
  Raw range:      0 to (2^N - 1)
  Physical range: (0 × factor + offset) to ((2^N-1) × factor + offset)

For signed signal, N bits (two's complement):
  Raw range:      -2^(N-1) to 2^(N-1) - 1
  Physical range: (-2^(N-1) × factor + offset) to ((2^(N-1)-1) × factor + offset)

DBC signed notation: @1-  (minus sign = signed)
DBC unsigned notation: @1+ (plus sign = unsigned)
```

---

### Cycle Time and Timeout

```
Cycle Time: How often a message is transmitted (ms)
  Examples:
  Engine RPM:       10ms  (100Hz — fast control loop)
  Vehicle Speed:    20ms  (50Hz  — chassis control)
  Fuel Level:       500ms (2Hz   — slow sensor)
  Door Status:      Event-triggered (only on change)

Timeout:    How long before receiver considers message lost
  Rule:     Timeout ≥ 3 × Cycle Time (industry practice)
  Example:  Speed message at 20ms → timeout = 60ms

Alive Counter: 4-bit rolling counter in the message, increments each cycle
  Receiver verifies: counter always increments by 1
  If counter jumps or stays same → network fault detected
  Counter range: 0–14 (0x0–0xE), wraps 0xE → 0x0
  (0xF often reserved as "invalid/error" state)
```

---

### CRC (Cyclic Redundancy Check) in CAN Messages

**Note**: CAN hardware already has 15-bit CRC on every frame.  
Application-level CRC is an *additional* integrity check inside the data payload.

```
AUTOSAR E2E Profile 2:
  Byte 0: CRC (8-bit) over bytes 1–7 using CRC-8-SAE-J1850
  Byte 1: Alive Counter (4-bit) + other signals

Why application CRC?
  Protect against SW errors (not just transmission errors)
  Required for ISO 26262 ASIL-B and higher safety signals
```

---

## 1.11 Real ECU Communication Examples

### ADAS: AEB ECU Message

```
Message: AEB_Req   ID=0x244   DLC=8   Cycle=20ms
  Signal: AEB_Active        bits 0–0    (1-bit flag)
  Signal: AEB_Decel_Req     bits 1–8    (m/s², factor=0.1, range 0–25.5)
  Signal: AEB_Obj_Distance  bits 9–24   (meters, factor=0.01, range 0–655.35)
  Signal: AEB_TTC           bits 25–32  (seconds, factor=0.01, range 0–2.55)
  Signal: AEB_State         bits 33–35  (3-bit enum: 0=OFF, 1=WARN, 2=ACTIVE, 3=FAULT)
  Signal: AliveCounter      bits 36–39  (4-bit counter)
  Signal: CRC               bits 40–47  (8-bit CRC)
```

### Instrument Cluster Message

```
Message: IPC_Display   ID=0x350   DLC=8   Cycle=100ms
  Signal: VehicleSpeed_Kmh   bits 0–11   (km/h, factor=0.1, range 0–409.5)
  Signal: EngineRPM          bits 12–27  (rpm, factor=0.25, range 0–16383.75)
  Signal: FuelLevel_Pct      bits 28–35  (%, factor=0.5, range 0–127.5)
  Signal: Gear_Display       bits 36–39  (enum: 0=P, 1=R, 2=N, 3=D, 4–7=Manual)
  Signal: MIL_Indicator      bits 40–40  (1-bit: 0=OFF, 1=ON)
  Signal: AliveCounter       bits 41–44  (4-bit)
  Signal: CRC                bits 45–52  (8-bit)
```

### Infotainment: Audio Request from HMI

```
Message: HMI_AudioCmd   ID=0x510   DLC=4   Cycle=Event
  Signal: Volume_Level      bits 0–7   (0–100%, factor=1)
  Signal: Source_Select     bits 8–11  (enum: 0=FM, 1=AM, 2=BT, 3=USB, 4=AUX)
  Signal: Mute_Request      bits 12–12 (1-bit)
  Signal: Bass_Level        bits 13–17 (signed, factor=1, offset=-15, range -15 to +15)
  Signal: Treble_Level      bits 18–22 (signed, factor=1, offset=-15, range -15 to +15)
```

---

## 1.12 Architectural Overview: Vehicle CAN Network

```
                        OBD-II Port
                            │
┌───────────────────────────┼────────────────────────────────────────┐
│                    CENTRAL GATEWAY (CGW)                            │
│           Routes messages between bus domains                       │
└─────┬──────────────┬───────────────┬──────────────┬───────────────┘
      │              │               │              │
  Powertrain     Chassis/Safety   Body/Comfort  Infotainment
  CAN-HS         CAN-HS           CAN-HS        CAN-HS / ETH
  500Kbps        500Kbps          500Kbps       100Mbps
      │              │               │              │
  ┌───────┐      ┌───────┐       ┌───────┐     ┌───────┐
  │ ECM   │      │ ABS   │       │ BCM   │     │ HU/IVI│
  │ TCM   │      │ ESC   │       │ HVAC  │     │ ADAS  │
  │ EMS   │      │ AEB   │       │ PEPS  │     │ Cluster│
  └───────┘      └───────┘       └───────┘     └───────┘
      │
   LIN Bus
  (comfort)
  ┌──────────┐
  │ Mirrors  │
  │ Windows  │
  │ Seats    │
  └──────────┘
```

---

## 1.13 Summary Table — Protocol Comparison

| Feature | CAN | CAN FD | LIN | FlexRay | Automotive Eth |
|---------|-----|--------|-----|---------|---------------|
| Speed | 1 Mbps | 8 Mbps | 20 Kbps | 20 Mbps | 1 Gbps |
| Payload | 8 bytes | 64 bytes | 8 bytes | 254 bytes | Unlimited |
| Wires | 2 | 2 | 1 | 4 (2ch) | 1 (T1) |
| Topology | Bus | Bus | Bus | Bus/Star | Star |
| Deterministic | No | No | Yes | Yes | TSN: Yes |
| Cost | Low | Low | Very Low | High | Medium |
| Safety use | ASIL-B | ASIL-B | QM | ASIL-D | ASIL-B+ |
| DBC support | Full | Full | LDF | FIBEX | ARXML |

---

## 1.14 Common Beginner Mistakes

| Mistake | Explanation |
|---------|-------------|
| Confusing bit order with byte order | Endianness affects bit-level packing, not just byte order |
| Forgetting that lower CAN ID = higher priority | Critical for safety message design |
| Treating CAN CRC as application CRC | They are separate — hardware CRC doesn't protect against SW bugs |
| Confusing Cycle Time with Timeout | Cycle=10ms does NOT mean timeout=10ms |
| Mixing Standard and Extended IDs in same DBC | Causes confusion — always clarify in communication matrix |

---

## Module 01 — Knowledge Check

1. What is the maximum payload of a Classical CAN frame?
2. If Signal A has Factor=0.5, Offset=-40, and Raw=200, what is the physical value?
3. Why does a lower Arbitration ID have higher bus priority?
4. What happens to a CAN node when its TEC exceeds 255?
5. A message has Cycle=20ms. What is the minimum recommended Timeout value?
6. What does `@0+` mean in a DBC signal definition?
7. How many bytes can CAN FD carry in a single frame?
8. Which protocol is used for heavy vehicles with SPNs and PGNs?

**Answers:**
1. 8 bytes (DLC=8)
2. 200 × 0.5 + (−40) = 100 − 40 = **60°C**
3. During arbitration, dominant (0) beats recessive (1) — lower ID has more 0-bits at start
4. Bus-Off state — node is disconnected from bus until reset
5. Minimum 60ms (3× cycle time)
6. Big-endian (Motorola) byte order, unsigned value
7. 64 bytes (DLC=15)
8. SAE J1939
