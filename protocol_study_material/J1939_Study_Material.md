# SAE J1939 Protocol Study Material
## Heavy Vehicle Communication Standard

---

## 1. Overview

**SAE J1939** is the standard CAN-based communication protocol for heavy-duty vehicles: trucks, buses, agricultural machinery, and off-highway equipment.

- Based on **CAN 2.0B** (29-bit extended frame identifiers)
- Baud rate: **250 kbit/s** (standard), 500 kbit/s (J1939/22 HS)
- Message format: **PGN-based** (Parameter Group Numbers)
- Signal encoding: **SPNs** (Suspect Parameter Numbers)

---

## 2. J1939 CAN Frame ID (29-bit)

```
Bits 28-26:  Priority (0-7, lower=higher priority)
Bit 25:      Reserved (always 0)
Bit 24:      Data Page (DP) — extends PGN space
Bits 23-16:  PF (PDU Format) — determines PDU1 or PDU2
Bits 15-8:   PS (PDU Specific) — destination address (PDU1) or group extension (PDU2)
Bits 7-0:    SA (Source Address) — sending ECU
```

### PDU1 vs PDU2
| Format | PF Range | PS field | Type |
|--------|----------|----------|------|
| PDU1 | 0x00–0xEF | Destination Address | Peer-to-peer or broadcast |
| PDU2 | 0xF0–0xFF | Group Extension | Broadcast only |

**Example: Engine Speed PGN 0xF004 (61444)**
```
Priority = 3 (011)
DP = 0
PF = 0xF0 → PDU2 = broadcast
PS = 0x04 (group extension)
SA = ECU source address (e.g., 0x00 = Engine)

29-bit ID = 0x0CF00400
```

---

## 3. PGN (Parameter Group Number)

A PGN identifies a group of parameters (signals) transmitted together:

```
PGN = (DP << 17) | (PF << 8) | PS   (for PDU2)
PGN = (DP << 17) | (PF << 8)         (for PDU1, PS=destination)
```

### Common PGNs

| PGN | Decimal | Name | Typical Period |
|-----|---------|------|---------------|
| 0xF004 | 61444 | EEC1 – Electronic Engine Controller 1 | 10ms |
| 0xFEEF | 65263 | EFL/P1 – Engine Fluid Level / Pressure 1 | 500ms |
| 0xFEF1 | 65265 | CCVS – Cruise Control / Vehicle Speed | 100ms |
| 0xFECA | 65226 | DM1 – Active DTCs | On change |
| 0xFECB | 65227 | DM2 – Previously Active DTCs | On request |
| 0xFECC | 65228 | DM3 – Clear DTCs | On request |
| 0xFEDA | 65242 | SoftwareIdentification | On request |
| 0xFEEC | 65260 | VehicleIdentification (VIN) | On request |
| 0xEA00 | 59904 | Request PGN | — |
| 0xEB00 | 60160 | Transport Protocol – Data Transfer | — |
| 0xEC00 | 60416 | Transport Protocol – Connection Management | — |

---

## 4. SPN (Suspect Parameter Number)

SPNs are individual signals within a PGN, identified by an SPNID number:

| SPN | Name | PGN | Bits | Factor | Offset | Range |
|-----|------|-----|------|--------|--------|-------|
| 190 | Engine Speed | EEC1 | 16 | 0.125 rpm/bit | 0 | 0–8031.875 rpm |
| 84 | Wheel-Based Vehicle Speed | CCVS | 16 | 1/256 km/h | 0 | 0–250.996 km/h |
| 110 | Engine Coolant Temp | EFL/P1 | 8 | 1°C/bit | -40 | -40–210°C |
| 100 | Engine Oil Pressure | EFL/P1 | 8 | 4 kPa/bit | 0 | 0–1000 kPa |

---

## 5. J1939 Address Claiming

Each ECU must claim a unique **Source Address (SA)** using the **ACL (Address Claimed)** procedure:

```
1. Node broadcasts CLAIM address (PGN 0xEE00, SA=claimed_address)
2. If another node already has that SA, it sends CLAIM with its own name
3. Node with lower 64-bit NAME wins (has priority)
4. Loser must claim alternate address or go offline

NAME field (64-bit):
  Bits 63-56: Industry Group + Vehicle System
  Bits 55-49: Vehicle System Instance
  Bits 48-42: Function Code
  Bits 41-37: Function Instance
  ...
  Bits 20-0:  Manufacturer Code + Identity Number
```

---

## 6. Transport Protocol (J1939-21)

For PGNs with payload > 8 bytes, J1939 uses a multi-frame transport protocol:

### Broadcast Announce Message (BAM) — no handshake
```
BAM (PGN 0xEC00, PS=0xFF broadcast):
  Byte 0: 0x20 (BAM control byte)
  Bytes 1-2: Total message size (bytes)
  Byte 3: Number of packets
  Byte 4: 0xFF (reserved)
  Bytes 5-7: PGN of the multi-frame message

Data Transfer (PGN 0xEB00):
  Byte 0: Sequence number (1..N)
  Bytes 1-7: Up to 7 bytes of data per packet
              (last packet padded with 0xFF)
```

### Connection Mode (RTS/CTS) — handshake with flow control
```
Sender → RTS (Request to Send)
Receiver → CTS (Clear to Send, N packets at a time)
Sender → Data packets (N packets)
Receiver → ACK (End of Message)
```

---

## 7. DM1 – Active Diagnostic Trouble Codes

DM1 is broadcast spontaneously when fault codes are active:

```
PGN: 0xFECA (65226)
Byte 0: Lamp status byte (MIL, RSL, AWL, PL — 2 bits each)
Bytes 1-2: SPN (bits 0-18, stored across bytes 1-2 + bits 7-5 of byte 3)
Byte 3: bits 7-5 = SPN[18:16], bits 4-0 = FMI
Byte 4: Occurrence Counter (0-126)
Byte 5: SPN Conversion Method (CM)
... repeating for each DTC
```

### DTC Status Lamp Byte
```
Bits 7-6: MIL (Malfunction Indicator Lamp): 00=off, 01=on, 10=fast, 11=slow
Bits 5-4: RSL (Red Stop Lamp)
Bits 3-2: AWL (Amber Warning Lamp)
Bits 1-0: PL (Protect Lamp)
```

---

## 8. J1939 in Python

```python
import can
import struct

bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=250000)

def parse_j1939_id(arb_id):
    priority  = (arb_id >> 26) & 0x07
    dp        = (arb_id >> 25) & 0x01
    pf        = (arb_id >> 16) & 0xFF
    ps        = (arb_id >>  8) & 0xFF
    sa        = (arb_id)       & 0xFF
    if pf >= 0xF0:
        pgn = (dp << 17) | (pf << 8) | ps
    else:
        pgn = (dp << 17) | (pf << 8)
    return priority, pgn, sa

def decode_engine_speed(data):
    """EEC1 PGN 0xF004: EngineSpeed at bytes 3-4 (SPN 190)"""
    raw   = struct.unpack_from('<H', data, 3)[0]   # little-endian 16-bit
    speed = raw * 0.125
    return speed

def decode_vehicle_speed(data):
    """CCVS PGN 0xFEF1: VehicleSpeed at bytes 1-2 (SPN 84)"""
    raw   = struct.unpack_from('<H', data, 1)[0]
    speed = raw / 256.0
    return speed

def monitor_j1939(duration=10):
    import time
    deadline = time.time() + duration
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg and msg.is_extended_id:
            priority, pgn, sa = parse_j1939_id(msg.arbitration_id)
            if pgn == 0xF004:   # EEC1
                rpm = decode_engine_speed(msg.data)
                print(f"EEC1 from SA=0x{sa:02X}: Engine Speed = {rpm:.2f} RPM")
            elif pgn == 0xFEF1: # CCVS
                spd = decode_vehicle_speed(msg.data)
                print(f"CCVS from SA=0x{sa:02X}: Vehicle Speed = {spd:.2f} km/h")

monitor_j1939()
bus.shutdown()
```

---

## 9. J1939 Source Addresses

| SA | ECU |
|----|-----|
| 0x00 | Engine #1 |
| 0x01 | Engine #2 |
| 0x03 | Transmission |
| 0x0B | Brakes (ABS) |
| 0x17 | Instrument Cluster |
| 0x28 | Body Controller |
| 0xFE | Anonymous (null address) |
| 0xFF | Global/Broadcast |

---

## 10. Interview Q&A

**Q: What is the difference between J1939 and standard CAN?**
> J1939 uses 29-bit extended CAN identifiers, 250 kbit/s baud rate, PGN-based message addressing, and defines a complete application layer including transport protocol for messages >8 bytes, address claiming, and diagnostic messages (DM1–DM31).

**Q: What is a PGN and how is it extracted from the 29-bit ID?**
> PGN (Parameter Group Number) identifies the message type. For PDU2 (PF≥0xF0), PGN = DP<<17 | PF<<8 | PS. For PDU1 (PF<0xF0), PGN = DP<<17 | PF<<8 (PS = destination address, not part of PGN).

**Q: How does address claiming work?**
> Each node starts with a desired SA and broadcasts an Address Claimed message. If another node has the same SA and a lower 64-bit NAME, the original node must either select another unused SA and re-claim, or give up and become address-less (SA=0xFE).

**Q: What is DM1 and when is it sent?**
> DM1 (Diagnostic Message 1) contains currently active DTCs. It is broadcast spontaneously whenever a fault is active, and retransmitted every 1 second. Each DTC includes a SPN (signal identifier), FMI (failure mode), and an occurrence counter.
