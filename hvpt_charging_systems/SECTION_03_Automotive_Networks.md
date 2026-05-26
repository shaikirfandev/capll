# SECTION 3 — AUTOMOTIVE COMMUNICATION NETWORKS
## CAN, CAN FD, LIN, Automotive Ethernet — Complete Reference

---

## 3.1 CAN PROTOCOL

### 3.1.1 CAN Overview

Controller Area Network (CAN) is the dominant automotive communication protocol, defined by ISO 11898. Developed by Bosch in 1986, it provides:
- Multi-master bus topology
- Priority-based arbitration
- Error detection and error handling
- Differential signaling for noise immunity

### 3.1.2 CAN Physical Layer

```
CAN BUS PHYSICAL LAYER:
──────────────────────────────────────────────────────────────
ECU1 ──────────────────────────────────── ECU2
       │  CAN_H (+2.5V nominal)   │
       │  ────────────────────    │
       │  CAN_L (+2.5V nominal)   │
       │  ────────────────────    │
 120Ω │                          │  120Ω
 term │                          │  term

DOMINANT state (logic 0):  CAN_H = 3.5V, CAN_L = 1.5V (diff = 2V)
RECESSIVE state (logic 1): CAN_H = 2.5V, CAN_L = 2.5V (diff = 0V)

Bus arbitration uses DOMINANT = 0 wins:
  Multiple ECUs transmit simultaneously
  First bit that differs → higher priority (lower ID) wins
  Other ECUs back off and retry
```

### 3.1.3 CAN Frame Format (Standard — 11-bit ID)

```
START OF FRAME (1 bit) — always dominant
│
├── ARBITRATION FIELD
│   ├── Identifier (11 bits) — message priority (lower = higher priority)
│   └── RTR bit (1 bit) — 0=data frame, 1=remote frame
│
├── CONTROL FIELD
│   ├── IDE bit — 0=standard (11-bit), 1=extended (29-bit)
│   ├── r0 — reserved (always recessive)
│   └── DLC (4 bits) — data length code (0–8 bytes)
│
├── DATA FIELD (0–8 bytes)
│
├── CRC FIELD
│   ├── CRC sequence (15 bits)
│   └── CRC delimiter (1 bit)
│
├── ACK FIELD
│   ├── ACK slot (1 bit) — receiver writes dominant
│   └── ACK delimiter (1 bit)
│
└── END OF FRAME (7 recessive bits)
```

### 3.1.4 CAN Arbitration

```
ARBITRATION EXAMPLE:
─────────────────────────────────────────────────────────────
ECU A wants to send:  ID = 0x100 (binary: 0001 0000 0000)
ECU B wants to send:  ID = 0x200 (binary: 0010 0000 0000)

Both start transmitting simultaneously...
Bit 1: Both send 0 → OK (both recessive fields match)
Bit 2: ECU A sends 0, ECU B sends 1
       → ECU B reads back 0 (bus dominant)
       → ECU B detects collision → backs off
ECU A wins and continues transmitting ID 0x100

RESULT: Lower ID = Higher priority = wins arbitration
This is why:
  ID 0x000 has HIGHEST priority
  ID 0x7FF has LOWEST priority
```

### 3.1.5 CAN Baud Rates in Automotive

| Application | Baud Rate |
|-------------|-----------|
| Powertrain (Drivetrain) | 500 kbit/s |
| Chassis / ADAS | 500 kbit/s |
| Body / Comfort | 125 kbit/s |
| OBD-II Diagnostics | 500 kbit/s |
| Safety Critical (ASIL) | 1 Mbit/s (CAN FD) |

### 3.1.6 CAN Error Handling

```
ERROR TYPES:
1. Bit Error:    Node reads back different bit than it sent
2. Stuff Error:  6+ consecutive bits of same polarity (violates bit stuffing)
3. CRC Error:    CRC mismatch between sender and receiver
4. Form Error:   Fixed-format field has incorrect value
5. Acknowledgment Error: No dominant bit in ACK slot

ERROR CONFINEMENT:
─────────────────────────────────────────────────────────
State         │ TEC      │ REC      │ Behavior
──────────────────────────────────────────────────────────
Error Active  │ 0–127    │ 0–127   │ Normal, sends Active Error Frame
Error Passive │ 128–255  │ 128–255 │ Sends Passive Error Frame
Bus Off       │ > 255    │ N/A     │ ECU disconnects from bus
──────────────────────────────────────────────────────────
TEC = Transmit Error Counter, REC = Receive Error Counter
TEC +8 per transmit error, −1 per successful frame
REC +1 per receive error, −1 per successful frame
```

---

## 3.2 CAN FD (CAN with Flexible Data Rate)

### 3.2.1 CAN FD Advantages

| Feature | Classic CAN | CAN FD |
|---------|-------------|--------|
| Max data payload | 8 bytes | 64 bytes |
| Nominal baud rate | Up to 1 Mbit/s | Up to 1 Mbit/s |
| Data phase baud rate | Same | Up to 8 Mbit/s (typ. 2 Mbit/s) |
| FD bit | No | Yes (BRS bit switches speed) |
| CRC | 15-bit | 17-bit or 21-bit (improved) |
| Standard | ISO 11898-1:2015 | ISO 11898-1:2015 |

### 3.2.2 CAN FD Frame Format

```
CAN FD FRAME (Extended):
SOF │ 11/29-bit ID │ FDF=1 │ BRS=1 │ ESI │ DLC │
─────────────────────────────────────────────────
                ↑ FDF=1 → FD frame
                         ↑ BRS=1 → switch to higher data rate here
                                    (data phase at 2 Mbit/s)
│ DATA (0, 1, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64 bytes) │
────────────────────────────────────────────────────────────
                                    ↓ back to nominal rate here
│ CRC (17 or 21-bit) │ ACK │ EOF │
```

### 3.2.3 CAN FD vs Classic CAN — Real Example

```
BMS_CellData message in Classic CAN (max 8 bytes):
  → Can only send 4 cell voltages per message (2 bytes each)
  → Need multiple messages to cover 100 cells: ~25 messages

BMS_CellData message in CAN FD (up to 64 bytes):
  → Can send 32 cell voltages in ONE message (2 bytes each)
  → Entire 64-cell module in 2 messages
  → Massively reduced bus load
```

---

## 3.3 DBC FILE FORMAT

### 3.3.1 DBC File Structure

```
// Example DBC file: EV_Powertrain.dbc

VERSION ""

NS_ : (namespace block)
BS_: (bitrate, often empty)

BU_: VCU BMS MCU OBC DCDC PDU GW  (Network nodes)

// ─────────────────────────────────────────────────
// MESSAGE DEFINITION
// ─────────────────────────────────────────────────
BO_ 784 BMS_Status: 8 BMS
 // BO_ <ID_decimal> <MsgName>: <DLC> <Sender>
 
 SG_ BMS_SoC : 0|16@1+ (0.5,0) [0|100] "%" VCU,GW
 // SG_ <SignalName> : <StartBit>|<Length>@<ByteOrder><ValueType> 
 //     (<Factor>,<Offset>) [<Min>|<Max>] "<Unit>" <Receivers>
 // ByteOrder: 1=Intel (little endian), 0=Motorola (big endian)
 // ValueType: + = unsigned, - = signed
 
 SG_ BMS_SoH : 16|16@1+ (0.5,0) [0|100] "%" VCU,GW
 SG_ BMS_PackVoltage : 32|16@1+ (0.1,0) [0|1000] "V" VCU,MCU,GW
 SG_ BMS_PackCurrent : 48|16@1- (0.1,0) [-600|600] "A" VCU,MCU,GW

BO_ 256 VCU_Command: 8 VCU
 SG_ VCU_HV_Enable : 0|2@1+ (1,0) [0|3] "" BMS,PDU
 SG_ VCU_ChargeEnable : 2|1@1+ (1,0) [0|1] "" OBC,BMS
 SG_ VCU_MaxChargeCurrent : 16|16@1+ (0.1,0) [0|600] "A" OBC,BMS
 SG_ VCU_TargetVoltage : 32|16@1+ (0.1,0) [0|1000] "V" OBC
 SG_ VCU_DriveMode : 36|3@1+ (1,0) [0|7] "" MCU

// ─────────────────────────────────────────────────
// VALUE TABLES (for enum signals)
// ─────────────────────────────────────────────────
VAL_ 784 BMS_ContactorState 
  0 "OPEN" 
  1 "PRECHARGE" 
  2 "CLOSED" 
  3 "FAULT";

VAL_ 256 VCU_HV_Enable 
  0 "OFF" 
  1 "ON" 
  2 "PRECHARGE" 
  3 "FAULT_REQUEST";

// ─────────────────────────────────────────────────
// COMMENTS
// ─────────────────────────────────────────────────
CM_ SG_ 784 BMS_SoC "Battery State of Charge. Physical value = raw × 0.5 %";
CM_ SG_ 784 BMS_PackCurrent "Positive = discharge, Negative = charge";
```

### 3.3.2 Signal Encoding Calculation

```
Physical Value = (Raw Value × Factor) + Offset

Example: BMS_PackVoltage
  Factor = 0.1, Offset = 0
  Raw = 3700 → Physical = 3700 × 0.1 + 0 = 370.0 V

Example: BMS_PackCurrent (signed)
  Factor = 0.1, Offset = 0
  Raw = -1500 (two's complement) → Physical = -150.0 A (charging)
  Raw = +2000 → Physical = 200.0 A (discharging)

Example: Temperature with offset
  Factor = 1, Offset = -40
  Raw = 65 → Physical = 65 - 40 = 25°C
  Raw = 0  → Physical = -40°C
  Raw = 255 → Physical = 215°C
```

---

## 3.4 CAN SIGNAL MULTIPLEXING (MUX)

### 3.4.1 Multiplexed Messages

Used when many signals share one message ID. A multiplexer (MUX) indicator selects which signal set is active:

```
DBC Multiplexing Example:
BO_ 800 BMS_CellVoltage: 8 BMS
 SG_ CellMuxID M : 0|8@1+ (1,0) [0|255] "" VCU
 // M = multiplexer indicator signal
 
 SG_ CellVolt_01 m0 : 8|16@1+ (1,0) [0|5000] "mV" VCU
 SG_ CellVolt_02 m0 : 24|16@1+ (1,0) [0|5000] "mV" VCU
 SG_ CellVolt_03 m0 : 40|16@1+ (1,0) [0|5000] "mV" VCU
 // m0 = active when CellMuxID = 0
 
 SG_ CellVolt_04 m1 : 8|16@1+ (1,0) [0|5000] "mV" VCU
 SG_ CellVolt_05 m1 : 24|16@1+ (1,0) [0|5000] "mV" VCU
 SG_ CellVolt_06 m1 : 40|16@1+ (1,0) [0|5000] "mV" VCU
 // m1 = active when CellMuxID = 1

CAN frame content when CellMuxID=0: [0x00, V1_L, V1_H, V2_L, V2_H, V3_L, V3_H, 0x00]
CAN frame content when CellMuxID=1: [0x01, V4_L, V4_H, V5_L, V5_H, V6_L, V6_H, 0x00]
```

---

## 3.5 LIN PROTOCOL

### 3.5.1 LIN Overview

Local Interconnect Network (LIN) is a low-cost, single-wire serial protocol for low-bandwidth body functions.

| Feature | LIN |
|---------|-----|
| Topology | Single master, multiple slaves |
| Max speed | 20 kbit/s |
| Max nodes | 16 (1 master + 15 slaves) |
| Wire | Single wire + ground |
| Standard | ISO 17987, SAE J2602 |
| Applications | Windows, mirrors, seats, sensors |

### 3.5.2 LIN Frame Structure

```
LIN FRAME:
─────────────────────────────────────────────────────────────
BREAK FIELD  │ SYNC FIELD │ PID FIELD  │ DATA (1–8 bytes) │ CHECKSUM
(≥13 bits    │  0x55      │ 6-bit ID   │                  │
 dominant)   │            │ + 2 parity │                  │
─────────────────────────────────────────────────────────────
BREAK: Signals start of frame (violation of bit stuffing)
SYNC:  0x55 for baud rate synchronization
PID:   Protected ID = Frame ID + 2 parity bits (P0, P1)
P0 = ID0 XOR ID1 XOR ID2 XOR ID4
P1 = NOT(ID1 XOR ID3 XOR ID4 XOR ID5)
```

### 3.5.3 LIN Schedule Table

```
The Master controls ALL communication on LIN bus.
Master sends headers; slaves respond with data (if their ID matches).

SCHEDULE TABLE EXAMPLE (10ms frame):
Slot  │ Frame ID │ Period │ Publisher │ Purpose
──────────────────────────────────────────────────
  0   │  0x10    │  10ms  │  Slave1   │ Window position status
  1   │  0x11    │  10ms  │  Slave2   │ Mirror status
  2   │  0x20    │  20ms  │  Master   │ Window command
  3   │  0x21    │  20ms  │  Master   │ Mirror command
  4   │  0x3C    │  100ms │  Slave1   │ Temperature sensor
  5   │  0x3D    │  N/A   │  Master   │ Diagnostic request (on demand)
```

### 3.5.4 LIN Sleep/Wakeup

```
SLEEP:
  Master sends Sleep Frame (ID=0x3C, Data=0x00 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF)
  All slaves enter low-power mode
  Bus held recessive by all nodes

WAKEUP:
  Any node (master or slave) can wake the bus
  Sends Wake-Up pulse (≥250µs dominant)
  All nodes detect wakeup → return to normal operation
  Master resumes schedule table
```

---

## 3.6 AUTOMOTIVE ETHERNET

### 3.6.1 Automotive Ethernet Overview

| Technology | Speed | Physical Layer | Application |
|-----------|-------|----------------|-------------|
| 100BASE-T1 | 100 Mbit/s | Single UTP pair | ADAS, cameras |
| 1000BASE-T1 | 1 Gbit/s | Single UTP pair | Backbone, AVB |
| 10BASE-T1S | 10 Mbit/s | Single UTP, multi-drop | Sensor networks |
| 10BASE-T1L | 10 Mbit/s | Long reach (>15m) | Heavy vehicles |

### 3.6.2 SOME/IP (Scalable service-Oriented MiddlewarE over IP)

```
SOME/IP CONCEPTS:
─────────────────────────────────────────────────────────────
SERVICE: A collection of related events, methods, and fields
  Example: BatteryService
    Methods: GetSoC(), RequestCharging(), SetChargingLimit()
    Events: SoCChanged, FaultDetected
    Fields: CurrentSoC (getter/setter)

SOME/IP MESSAGE TYPES:
  0x00 = Request         (client → server, method call)
  0x01 = Request No Return (fire and forget)
  0x02 = Notification    (server → client, event)
  0x80 = Response        (server → client, method return)
  0x81 = Error           (server → client, error return)

SOME/IP MESSAGE FORMAT:
  ┌─────────────────────────────────────────────────────────┐
  │  Service ID  (16-bit)  │  Method/Event ID   (16-bit)   │
  ├─────────────────────────────────────────────────────────┤
  │  Length     (32-bit)   │  Client ID          (16-bit)  │
  ├─────────────────────────────────────────────────────────┤
  │  Session ID (16-bit)   │  Protocol Ver (8)  Iface Ver  │
  ├─────────────────────────────────────────────────────────┤
  │  Message Type (8-bit)  │  Return Code        (8-bit)   │
  ├─────────────────────────────────────────────────────────┤
  │  PAYLOAD (variable)                                     │
  └─────────────────────────────────────────────────────────┘
```

### 3.6.3 SOME/IP Service Discovery (SOME/IP-SD)

```
SERVICE DISCOVERY FLOW:
ECU_A (Provider) ──────────────────── ECU_B (Consumer)
       │                                    │
       │  ← ← ← ← Find Service (multicast) ←│
       │  (ECU_B looks for BatteryService)  │
       │                                    │
       │─ Offer Service (multicast) ──────► │
       │  (ECU_A announces BatteryService)  │
       │                                    │
       │  ← ← ← ← Subscribe Event ─────── ←│
       │  (ECU_B subscribes to SoCChanged)  │
       │                                    │
       │─ Subscribe Acknowledge ──────────► │
       │                                    │
       │─ SOME/IP Event (SoCChanged) ─────► │  (every time SoC changes)
       │                                    │
```

### 3.6.4 DoIP (Diagnostics over IP) — ISO 13400

```
DoIP is used for vehicle diagnostics over Ethernet (replacing K-Line/CAN).
Used for:
  - Flash programming (over OTA)
  - UDS diagnostics over Ethernet
  - End-of-line testing (EOL)

DoIP ARCHITECTURE:
  Diagnostic Tool (PC) ─ TCP/UDP ─ DoIP Gateway ─ CAN/LIN ─ Target ECU

DoIP PORT: UDP 13400 (vehicle announcement), TCP 13400 (diagnostic data)

DoIP FLOW:
  1. Tool sends UDP Broadcast: "Vehicle Announcement Request"
  2. DoIP Gateway responds: VIN, logical address
  3. Tool opens TCP connection to port 13400
  4. Tool sends: Routing Activation Request
  5. Gateway responds: Routing Activation Response (success)
  6. Tool sends UDS requests wrapped in DoIP messages
  7. Gateway forwards to target ECU via internal bus
  8. Response comes back in reverse
```

---

## 3.7 NETWORK ARCHITECTURE

### 3.7.1 Typical EV Network Topology

```
EV NETWORK ARCHITECTURE:
═════════════════════════════════════════════════════════════════════
                    ┌─────────────────────┐
                    │   CENTRAL GATEWAY   │
                    │       (GW)          │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                       │
┌───────▼────────┐   ┌────────▼────────┐   ┌─────────▼─────────┐
│ POWERTRAIN CAN │   │  CHASSIS CAN    │   │ BODY/COMFORT CAN  │
│ (500 kbit/s)   │   │ (500 kbit/s)   │   │ (125 kbit/s)      │
├────────────────┤   ├─────────────────┤   ├───────────────────┤
│  VCU           │   │  ABS/ESC        │   │  BCM              │
│  BMS           │   │  EPS            │   │  IVI              │
│  MCU/Inverter  │   │  ADAS ECU       │   │  Climate          │
│  OBC           │   │  Radar/Camera   │   │  Lighting         │
│  DC-DC         │   │  (Ethernet      │   │  Door modules     │
│  PDU           │   │   for ADAS)     │   │  (LIN slaves)     │
└────────────────┘   └─────────────────┘   └───────────────────┘
                              │
                    ┌─────────▼───────────┐
                    │  DIAGNOSTIC CAN     │
                    │  (OBD-II port,      │
                    │  UDS diagnostics)   │
                    └─────────────────────┘
                              │
                    ┌─────────▼───────────┐
                    │  ETHERNET BACKBONE  │
                    │  (1000BASE-T1)      │
                    ├─────────────────────┤
                    │  ADAS Domain Ctrl   │
                    │  Cameras (LVDS/Eth) │
                    │  Lidar              │
                    │  OTA Update ECU     │
                    └─────────────────────┘
```

### 3.7.2 Gateway Routing Tables

```
GATEWAY ROUTING EXAMPLE:
─────────────────────────────────────────────────────────────
Message            │ Source Network  │ Destination Network  │ Action
───────────────────────────────────────────────────────────────────────
BMS_Status(0x310)  │ Powertrain CAN  │ Chassis CAN          │ Forward
VCU_Command(0x100) │ Powertrain CAN  │ Powertrain CAN       │ Local only
INV_Status(0x410)  │ Powertrain CAN  │ Diagnostic CAN       │ Forward
OBC_Status(0x620)  │ Powertrain CAN  │ Body CAN             │ Forward
UDS_Request        │ Diagnostic CAN  │ Powertrain CAN       │ Route to ECU
SOME/IP events     │ Ethernet        │ Powertrain CAN       │ Transform+route
```

---

## 3.8 NETWORK TIMING ANALYSIS

### 3.8.1 Bus Load Calculation

```
BUS LOAD FORMULA:
Bus Load (%) = (Sum of all frame bit times) / (Available bit time per second) × 100

Frame bit time = (11 + DLC×8 + 25 overhead) bits × (1/baud_rate)

Example: Powertrain CAN at 500 kbit/s with 20 cyclic messages:
  Message period average: 10 ms
  Average frame bits: ~100 bits
  Frames per second: 20 messages / 10ms = 2000 frames/s
  Bits per second: 2000 × 100 = 200,000 bits/s
  Bus load = 200,000 / 500,000 = 40%
  
  Rule of thumb: Keep bus load < 30% normal, < 50% peak
```

### 3.8.2 Timing Analysis — Message Latency

```
LATENCY CHAIN (Accelerator pedal → Torque):
VCU reads APP sensor ──► 1 ms
VCU calculates torque  ──► 2 ms
VCU sends CAN message  ──► + 0.2ms (transmission)
CAN network delay      ──► + 0.5ms (propagation + bus arbitration)
MCU receives message   ──► + 0.1ms
MCU control loop update──► + 1 ms (depends on control loop rate)
Inverter gate update   ──► + 0.1ms
────────────────────────────────
Total: ~5 ms latency

Requirement: ≤ 20 ms (typically)
```

---

## 3.9 NETWORK DEBUGGING WITH CANoe/CANalyzer

### 3.9.1 Common Network Issues and Debugging

```
ISSUE 1: ECU Not Transmitting
─────────────────────────────────────────────────────────
Symptom: Message missing in trace
Debug steps:
  1. Check ECU power supply (CAN trace: is ECU sending anything?)
  2. Check ECU wake-up condition (ECU might be in sleep)
  3. Check CAN bus termination (measure with multimeter: 60Ω at connector)
  4. Check DBC: is message defined? Correct ID?
  5. Check CANoe restbus simulation: is it blocking the message?
  6. Check ECU fault state: DTC P0600 (CAN communication fault)

ISSUE 2: Wrong Signal Value
─────────────────────────────────────────────────────────
Symptom: Signal value incorrect in CANoe panel
Debug steps:
  1. Verify DBC file matches ECU SW version
  2. Check byte order (Intel vs Motorola — very common error!)
  3. Check start bit (off-by-one errors are common)
  4. Check factor/offset in DBC
  5. Decode raw hex manually:
     Frame: [00 E6 00 00 00 00 00 00]
     Signal BMS_SoC: bits 0–15, Intel, factor=0.5
     Raw = 0x00E6 (little endian) = 0xE600 = 58880? NO.
     Intel byte order: byte0=0x00, byte1=0xE6
     Raw = 0xE600 reversed bits to bytes = 0x00E6 = 230 decimal
     Physical = 230 × 0.5 = 115.0% ← IMPOSSIBLE → DBC error?
     
ISSUE 3: Bus Off Condition
─────────────────────────────────────────────────────────
Symptom: ECU completely disappears from bus
Debug steps:
  1. Count error frames in CANalyzer trace
  2. Check TEC counter (via diagnostics if ECU can respond on other channel)
  3. Look for pattern: what event triggered error frames?
  4. Check for ground issues (different ECUs, different ground points)
  5. Check for CAN transceiver damage (short to GND or VBAT)
  6. Check for impedance mismatch (cable length, connector quality)
```

---

## 3.10 CAN TESTING SETUP

### 3.10.1 Vector Hardware Setup

```
PHYSICAL HARDWARE REQUIRED:
─────────────────────────────────────────────────────────────
1. Vector VN1630 / VN1640 (USB-CAN adapter)
   - Supports 4× CAN channels
   - Supports CAN FD
   - Connects to PC via USB

2. Connector configuration:
   - 9-pin DSUB (standard) or automotive connector (vehicle-specific)
   - CAN_H, CAN_L, GND
   - Termination: 120Ω at cable end if needed

3. Software:
   - CANoe or CANalyzer installed
   - Vector Driver Installed (VN16xx drivers)
   - DBC file loaded for message decoding

BENCH TEST SETUP:
PC ── USB ── VN1630 ── CAN_H/CAN_L ── Junction box
                                          │
                              ┌───────────┼───────────┐
                           ECU_1       ECU_2        ECU_3
                          (BMS HW)   (VCU HW)    (MCU HW)
                          120Ω term              120Ω term
```

---

## SECTION 3 SUMMARY

| Protocol | Speed | Topology | Main Use |
|---------|-------|----------|----------|
| CAN 2.0B | 1 Mbit/s max | Multi-master bus | Powertrain, chassis |
| CAN FD | 8 Mbit/s data | Multi-master bus | High data rate apps |
| LIN 2.x | 20 kbit/s | Master-slave | Low-cost body functions |
| 100BASE-T1 | 100 Mbit/s | Point-to-point | ADAS, cameras |
| 1000BASE-T1 | 1 Gbit/s | Point-to-point | Ethernet backbone |
| SOME/IP | over Ethernet | Service-oriented | Service communication |
| DoIP | over Ethernet | Client-server | Diagnostics, flashing |

---

*Next: Section 4 — CANoe Complete Learning Guide*
