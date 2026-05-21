# 04 — CAN Protocol & Automotive Communication

> **Standards:** ISO 11898 (CAN), ISO 14229 (UDS), SAE J1939, ISO 15765 (ISO-TP)

---

## 4.1 CAN Frame Structure

```
Standard CAN Frame (11-bit ID):

 SOF  Arbitration  RTR  IDE  r0   DLC    Data (0-8 bytes)   CRC   ACK  EOF
 [1]    [11-bit]  [1]  [1]  [1]  [4]   [0-64 bits]        [15]  [2]  [7]

Fields:
  SOF:         Start of Frame (dominant bit)
  Arbitration: 11-bit (standard) or 29-bit (extended) message ID
  RTR:         Remote Transmission Request (0=data frame, 1=remote frame)
  IDE:         Identifier Extension (0=standard, 1=extended)
  DLC:         Data Length Code (0-8 bytes)
  Data:        Payload (up to 8 bytes for Classic CAN, 64 bytes for CAN FD)
  CRC:         15-bit CRC for error detection
  ACK:         Acknowledgement (any receiver pulls to dominant)
  EOF:         End of Frame (7 recessive bits)

Key property: CSMA/CA (Carrier Sense Multiple Access / Collision Avoidance)
  When two nodes transmit simultaneously → ARBITRATION
  Lower ID wins (dominant bits override recessive)
  Example: 0x100 wins over 0x200 → 0x100 has higher priority
```

---

## 4.2 DBC File — Decoding the Vehicle Network

```
DBC (Database CAN) file defines all messages and signals on a CAN bus.
Used in: Vector CANoe, CANdb++, Kvaser, MATLAB Vehicle Network Toolbox

Example DBC excerpt (Bosch-style):

VERSION ""

NS_:

BS_:

BU_: BCM ECM ADAS_ECU EPS

BO_ 256 BCM_Status: 8 BCM
 SG_ VehicleSpeed : 0|16@1+ (0.01,0) [0|327.67] "km/h" ADAS_ECU,ECM
 SG_ BrakeActive  : 16|1@1+  (1,0)   [0|1]       ""     ADAS_ECU
 SG_ AccelPedal   : 17|8@1+  (0.4,0) [0|100]     "%"    ADAS_ECU

BO_ 512 EPS_Status: 8 EPS
 SG_ SteeringAngle    : 0|16@1+   (0.1,-3276.8) [-3276.8|3276.7] "deg"  ADAS_ECU
 SG_ SteeringTorque   : 16|12@1+  (0.01,-20.48) [-20.48|20.47]  "Nm"   ADAS_ECU
 SG_ EpsFaultActive   : 28|1@1+   (1,0)         [0|1]           ""     ADAS_ECU

BO_ 768 ADAS_LKA_Cmd: 8 ADAS_ECU
 SG_ LkaTorqueRequest : 0|12@1+  (0.01,-20.48) [-5|5]    "Nm"  EPS
 SG_ LkaActiveFlag    : 12|1@1+  (1,0)          [0|1]    ""    EPS,BCM

Signal format: Name : StartBit|Length@ByteOrder+/- (Factor,Offset) [Min|Max] "Unit" Receivers

@1 = Intel byte order (little-endian)
@0 = Motorola byte order (big-endian)
+  = unsigned
-  = signed
```

---

## 4.3 CAN FD — Faster, Larger Payload

```
CAN FD (Flexible Data Rate) key improvements:
  - Data phase: up to 8 Mbps (vs 1 Mbps CAN Classic)
  - Payload: up to 64 bytes (vs 8 bytes CAN Classic)
  - Maintains backward compatibility with CAN Classic arbitration

When used:
  Camera data (raw image thumbnails): CAN FD 64-byte frames
  Radar object list: 10-20 objects × 8 bytes = 160 bytes → 3 CAN FD frames
  OTA firmware update chunks: 64-byte payload reduces frame count 8x

CAN FD Frame identifiable by: BRS bit (Bit Rate Switch) in frame
```

---

## 4.4 ISO-TP (ISO 15765-2) — Multi-Frame Transport

```
ISO-TP allows sending more than 8 bytes over CAN (used by UDS diagnostics)

Frame types:
  SF (Single Frame):   PCI byte[7:4]=0, Len=[3:0]   Payload: 1–7 bytes
  FF (First Frame):    PCI byte[7:4]=1, Len[11:0]   First 6 bytes of long message
  CF (Consecutive):    PCI byte[7:4]=2, SN=[3:0]    Next 7 bytes (SN=1,2,3...)
  FC (Flow Control):   PCI byte[7:4]=3, FS/BS/STmin  Receiver controls flow

Example: ECU sends 20-byte response to $22 F190 (VIN read) request
  FF: 20 00 49 4E 31 4A 43 35   (first 6 bytes of VIN)
  FC: 30 00 00 00 00 00 00 00   (tester sends flow control: continue, BS=0, STmin=0)
  CF1: 21 35 36 42 43 37 38 39  (next 7 bytes, SN=1)
  CF2: 22 30 31 32 00 00 00 00  (final 3 bytes, SN=2)
```

---

## 4.5 UDS Services — Diagnostics Deep Dive

```
UDS (Unified Diagnostic Services) — ISO 14229
Used for: ECU flashing, fault reading, configuration, end-of-line testing

Key services (hex codes):

0x10 DiagnosticSessionControl
  0x10 01 → Enter Default Session
  0x10 02 → Enter Programming Session (for flashing)
  0x10 03 → Enter Extended Diagnostic Session

0x11 ECUReset
  0x11 01 → Hard Reset
  0x11 02 → Key Off On Reset
  0x11 03 → Soft Reset

0x14 ClearDiagnosticInformation
  0x14 FF FF FF → Clear all DTCs

0x19 ReadDTCInformation
  0x19 02 09 → Read all confirmed DTCs

0x22 ReadDataByIdentifier
  0x22 F1 90 → Read VIN (DataIdentifier 0xF190)
  0x22 F1 86 → Read Active Diagnostic Session
  0x22 F1 10 → Read ECU Manufacturing Date

0x2E WriteDataByIdentifier
  0x2E F1 90 [VIN bytes] → Write VIN (programming session only)

0x27 SecurityAccess (Seed/Key exchange)
  0x27 01 → Request seed
  Response: 0x67 01 [4 bytes seed]
  0x27 02 [4 bytes key] → Send key
  Response: 0x67 02 (positive) or 0x7F 27 35 (negative: invalidKey)

0x31 RoutineControl
  0x31 01 FF 00 → Start routine FF00 (e.g., "Erase flash memory")

0x34/0x36/0x37 RequestDownload / TransferData / RequestTransferExit
  Used for ECU flashing sequence
```

---

## 4.6 CAN Parser in C++ — Production Implementation

See: `can_parser.cpp` in this folder

---

## 4.7 Interview Questions

```
L1:
  Q: What is CAN bus arbitration?
  A: When two ECUs transmit simultaneously, CAN uses CSMA/CA (non-destructive
     bitwise arbitration). Each node monitors the bus while transmitting.
     If a node transmits a recessive bit (1) but reads a dominant bit (0), it
     lost arbitration and stops transmitting immediately. The frame with the
     lower ID (more dominant bits early) wins. No data is lost — the losing
     node retries after the winning frame completes.
     Example: 0x100 vs 0x200 — 0x100 wins (bit 8 is 0 in 0x100, 1 in 0x200).

  Q: What is a DBC file?
  A: Database CAN file. A text-based configuration file describing all CAN
     messages and signals in a vehicle network. Contains: message IDs, signal
     bit positions, bit lengths, byte order, scaling (factor + offset), value
     ranges, and which ECUs send/receive each message. Used in Vector CANoe
     for signal decoding and generation. Your software uses DBC data (or its
     equivalent in ARXML) to know how to encode/decode each signal.

  Q: What is the maximum payload of a CAN Classic frame?
  A: 8 bytes. CAN FD extends this to 64 bytes (with 8 Mbps data rate).

L2:
  Q: Explain ISO-TP and why it's needed for UDS.
  A: CAN Classic max payload = 8 bytes. UDS messages (especially firmware data
     during flashing, or long DTC read responses) can be 100s of bytes.
     ISO-TP (ISO 15765-2) provides a transport layer on top of CAN:
     First Frame announces total length, Consecutive Frames carry the data,
     Flow Control lets receiver throttle the sender.
     This allows UDS to send/receive arbitrary length messages over CAN.

  Q: What are the J1939 transport protocol differences from ISO-TP?
  A: J1939 (SAE J1939): heavy-vehicle protocol (trucks, buses).
     Uses 29-bit extended CAN IDs. PGN (Parameter Group Number) identifies messages.
     J1939 TP: BAM (Broadcast Announce Message) for broadcast multi-frame,
     CMDT (Connection Mode Data Transfer) for addressed multi-frame.
     ISO-TP: used in passenger car UDS diagnostics.
     Key difference: J1939 is a full application-layer protocol; ISO-TP is only transport layer.

L3:
  Q: How do you design a CAN signal scheduler in AUTOSAR?
  A: In AUTOSAR COM, each I-PDU has a configured transmission mode:
     - Periodic: sent every N ms regardless (e.g., VehicleSpeed every 10ms)
     - Event-triggered: sent on data change (e.g., gear position change)
     - Mixed: periodic with faster send on change
     The COM scheduler runs the configured PDU transmission timers.
     In the COM ARXML, you configure: ComTxModeMode, ComTxModePeriod, MinimumDelayTime.
     COM handles timeout supervision on Rx signals (ComRxDataTimeoutAction).
     If a signal is not received within timeout → signal goes to init value → DEM event.
```
