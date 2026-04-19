# J1939 Protocol Guide — Heavy Vehicle Networks
## SAE J1939 | PGN/SPN | Truck/Bus CAN Communication

---

## 1. Overview

**SAE J1939** is the standard CAN-based network for heavy-duty vehicles:
- Trucks, buses, agricultural/construction equipment
- Uses **29-bit extended CAN IDs** at **250 kbit/s**
- Layered on top of ISO 11898 (CAN physical/data link)

**Why J1939 instead of raw CAN?**
- Defines message addressing, PGN/SPN taxonomy
- Multi-packet transport protocol
- Standardized diagnostics (DM1–DM25)
- Network management (address claiming)

---

## 2. 29-Bit CAN ID Structure

```
Bit:  28  27  26  25  24  23  22-16  15-8   7-0
      [P  P   P ] [R] [DP] [PF byte] [PS byte] [SA byte]
      Priority        Page  PGN High  PGN Low   Source Addr
```

| Field | Bits | Description |
|-------|------|-------------|
| **Priority** | 3 | 0=highest, 7=lowest |
| **Reserved (R)** | 1 | Always 0 |
| **Data Page (DP)** | 1 | Extends PGN space (0 or 1) |
| **PF** | 8 | PDU Format (≥240 → broadcast PDU2) |
| **PS** | 8 | PDU Specific (destination addr for PDU1, group ext for PDU2) |
| **SA** | 8 | Source Address of transmitting ECU |

---

## 3. PDU1 vs PDU2

| Type | PF Range | PS Field | Destination |
|------|----------|----------|-------------|
| **PDU1** | 0–239 | Destination Address | Peer-to-peer (addressed) |
| **PDU2** | 240–255 | Group Extension | Broadcast to all nodes |

**PGN Extraction:**
- PDU1: PGN = DP×65536 + PF×256 + **0** (PS is address, not part of PGN)
- PDU2: PGN = DP×65536 + PF×256 + PS

---

## 4. Common PGNs

| PGN | Hex | Name | Typical Signals |
|-----|-----|------|-----------------|
| 61444 | 0xF004 | Electronic Engine Controller 1 (EEC1) | Engine Speed (SPN 190), Torque |
| 65265 | 0xFEF1 | Cruise Control / Vehicle Speed (CCVS) | Wheel Speed (SPN 84), Cruise ON/OFF |
| 65262 | 0xFEEE | Engine Temperature (ET1) | Coolant Temp (SPN 110) |
| 65263 | 0xFEEF | Engine Fluid Level/Pressure (EFL/P1) | Oil Pressure (SPN 100) |
| 65226 | 0xFECA | Diagnostic Message 1 (DM1) | Active DTCs + lamp status |
| 65227 | 0xFECB | DM2 — Previously Active DTC | Stored DTCs |
| 60160 | 0xEB00 | Transport Protocol Data Transfer (TP.DT) | Multi-packet data |
| 60416 | 0xEC00 | Transport Protocol Conn. Mgmt (TP.CM) | BAM/RTS/CTS/EndOfMsg |
| 59392 | 0xE800 | Acknowledgement (ACK/NACK) | Positive/Negative/Busy |
| 60928 | 0xEE00 | Address Claimed | NAME, address claiming |

---

## 5. SPN (Suspect Parameter Number)

SPNs are the individual signals within a PGN.

| SPN | Name | PGN | Resolution | Range | Unit |
|-----|------|-----|-----------|-------|------|
| 190 | Engine Speed | EEC1 | 0.125 rpm/bit | 0–8031.875 | rpm |
| 84 | Wheel-Based Speed | CCVS | 1/256 km/h/bit | 0–250.996 | km/h |
| 110 | Engine Coolant Temp | ET1 | 1°C/bit, offset -40 | -40→210 | °C |
| 100 | Engine Oil Pressure | EFL/P1 | 4 kPa/bit | 0–1000 | kPa |
| 51 | Throttle Position | EEC2 | 0.4%/bit | 0–100 | % |
| 91 | Accelerator Pedal Pos | EEC2 | 0.4%/bit | 0–100 | % |

### SPN Decoding (EEC1 — Engine Speed)
```python
# EEC1 PGN = 0xF004, 8 bytes
# SPN 190 = bytes 4-5 (1-indexed: byte 4 low, byte 5 high)
def decode_engine_speed(data_bytes):
    raw = (data_bytes[4] | (data_bytes[5] << 8))
    return raw * 0.125  # rpm
```

---

## 6. Address Claiming

Each ECU must claim its **Source Address (SA)** at startup.

```
1. ECU powers on
2. Broadcasts "Cannot Claim" (SA=254) if no address yet
   OR sends Address Claimed (PGN 0xEE00) with its NAME

NAME = 64-bit unique identifier:
  Bits 63-56: Identity Number (low)
  Bits 55-49: Manufacturer Code
  ...
  Bits 7-4:   Industry Group (5=Truck)
  Bits 3-0:   Reserved

3. If another ECU on bus has same SA:
   Higher-priority NAME (lower value) wins
   Loser must pick another SA or go offline (SA=254)
```

---

## 7. Transport Protocol (Multi-Packet)

J1939 TP handles messages >8 bytes (up to 1785 bytes).

### Broadcast Announce Message (BAM) — One-to-all

```
TP.CM (PGN 0xEC00, PS=255 broadcast):
  Byte 0: 0x20 = BAM control byte
  Byte 1-2: Total message size (bytes)
  Byte 3:   Number of packets
  Byte 4:   0xFF (reserved)
  Byte 5-7: PGN of packaged message

→ Sender transmits TP.DT packets (PGN 0xEB00):
  Byte 0:   Sequence number (1, 2, 3...)
  Byte 1-7: 7 bytes of data per packet
```

### Request-to-Send / Clear-to-Send (RTS/CTS) — Peer-to-peer

```
Sender → RTS (TP.CM, ctrl=0x10): "I have N bytes for you"
Receiver → CTS (TP.CM, ctrl=0x11): "Send me packets 1..M"
Sender → TP.DT × M packets
Receiver → CTS again if more needed
Receiver → End of Message Acknowledgement (ctrl=0x13)
```

---

## 8. DM1 — Active Diagnostic Trouble Codes

DM1 (PGN 0xFECA) is broadcast each second when DTCs are active.

```
DM1 Structure:
Byte 0:   Lamp status (MIL, RSL, AWL, PL — 2 bits each)
Byte 1:   Reserved lamp status
Bytes 2+: DTC records (4 bytes each):
  Bits 31-19: SPN (19 bits)
  Bits 18-16: FMI (Failure Mode Identifier, 5 bits)
  Bit  15:    SPN MSB (part of SPN)
  Bits 14-11: Occurrence Count (4 bits)
  Bit  10:    SPN conversion method
```

**FMI Values:**
| FMI | Description |
|-----|-------------|
| 0 | Data valid but above normal range |
| 1 | Data valid but below normal range |
| 2 | Data erratic, intermittent, incorrect |
| 3 | Voltage above normal (short to high) |
| 4 | Voltage below normal (short to low) |
| 5 | Current below normal (open circuit) |
| 6 | Current above normal (short to ground) |
| 7 | Mechanical system not responding |
| 12 | Bad intelligent device or component |

---

## 9. Python J1939 Decoding Example

```python
import can

bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=250000)

def parse_j1939_id(arbitration_id):
    sa  = arbitration_id & 0xFF
    ps  = (arbitration_id >> 8) & 0xFF
    pf  = (arbitration_id >> 16) & 0xFF
    dp  = (arbitration_id >> 24) & 0x01
    pri = (arbitration_id >> 26) & 0x07
    if pf < 240:    # PDU1
        pgn = (dp << 16) | (pf << 8)
        dest = ps
    else:           # PDU2
        pgn = (dp << 16) | (pf << 8) | ps
        dest = 0xFF
    return pri, pgn, dest, sa

EEC1_PGN = 0xF004

for msg in bus:
    if not msg.is_extended_id:
        continue
    pri, pgn, dest, sa = parse_j1939_id(msg.arbitration_id)
    if pgn == EEC1_PGN:
        speed = ((msg.data[4] | (msg.data[5] << 8)) * 0.125)
        print(f"SA=0x{sa:02X} Engine Speed: {speed:.2f} RPM")
```

---

## 10. Interview Q&A

**Q: What is the difference between PGN and SPN?**
> PGN (Parameter Group Number) identifies a J1939 message (like a CAN message ID, but protocol-level). SPN (Suspect Parameter Number) identifies an individual signal within that message — the specific byte/bit position and scaling formula.

**Q: Why does J1939 use 29-bit CAN IDs instead of 11-bit?**
> The 29-bit extended CAN ID gives J1939 space for Priority (3 bits), Data Page (1 bit), PF (8 bits), PS (8 bits), and Source Address (8 bits). This allows 254 node addresses, peer-to-peer addressing (PDU1) and broadcast (PDU2) in a single ID field — impossible with 11-bit IDs.

**Q: What happens when two J1939 nodes have the same source address?**
> Both nodes broadcast "Address Claimed" (PGN 0xEE00). The node with the lower NAME value (higher priority) wins and keeps the address. The losing node must select a different address or go offline with SA=254 (null address).

**Q: How does J1939 transport protocol handle data > 8 bytes?**
> TP.CM and TP.DT PGNs. For broadcast: BAM (Broadcast Announce Message) followed by TP.DT packets of 7 bytes each. For peer-to-peer: RTS/CTS handshake. Maximum payload is 1785 bytes (255 packets × 7 bytes).
