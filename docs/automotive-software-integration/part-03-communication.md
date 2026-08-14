# Part 3 — Communication Integration

Communication is the backbone of automotive systems. Every feature requires at least one communication protocol. This part covers CAN, CAN FD, LIN, FlexRay, and Automotive Ethernet in depth.

---

## 3.1 CAN (Controller Area Network)

### What is CAN?
CAN (ISO 11898) is a broadcast serial communication protocol designed for harsh automotive environments. Every node on the bus can send/receive; the highest-priority message wins.

### CAN 2.0A (Standard Frame) vs 2.0B (Extended Frame)

| Feature | CAN 2.0A | CAN 2.0B |
|---|---|---|
| Identifier | 11-bit (0–2047) | 29-bit (0–536,870,911) |
| Use | Legacy ECUs, simple signals | Diagnostics (CAN ID + 29-bit), J1939 |

### CAN Frame Structure

```
+--------+----+----+----+----+----+-----+----+-------+
| SOF(1) | ID | RTR| IDE| r0 |DLC |Data |CRC | ACK  |
|        |11b | 1b | 1b | 1b | 4b |0-8B |15b |  2b  |
+--------+----+----+----+----+----+-----+----+-------+
```

- **SOF** — Start of Frame (dominant bit)
- **ID** — Message identifier (determines priority; lower = higher priority)
- **RTR** — Remote Transmission Request
- **DLC** — Data Length Code (0–8 bytes)
- **Data** — Payload (up to 8 bytes)
- **CRC** — 15-bit cyclic redundancy check
- **ACK** — Acknowledgement (any receiver pulls this dominant)

### Arbitration
When two nodes transmit simultaneously, bitwise AND arbitration occurs. The node with the lower ID (more dominant bits) wins and continues. The losing node waits and retransmits.

### CAN Bit Timing
```
Bit time = Sync Segment + Propagation Segment + Phase Segment 1 + Phase Segment 2

Example at 500 kbps:
  Bit time = 2 µs (1/500,000)
  Sync Seg = 1 TQ
  Prop Seg = 3 TQ
  Phase1   = 4 TQ
  Phase2   = 4 TQ
  TQ       = 250 ns
```

### Bus-Off and Error Handling

CAN nodes maintain error counters:
- **Transmit Error Counter (TEC)** and **Receive Error Counter (REC)**
- **Error Active** — Normal operation (TEC/REC < 96)
- **Error Passive** — TEC/REC ≥ 96 (still transmits but more restricted)
- **Bus-Off** — TEC ≥ 256 — node stops transmitting, can recover after 128 × 11 recessive bits

### DBC Files
DBC (Database CAN) files define:
- Message IDs and names
- Signal definitions: start bit, length, byte order, scaling, offset, min/max, unit
- Node assignments

```
// Example DBC snippet
BO_ 0x100 EngineControl: 8 Engine_ECU
 SG_ EngineSpeed : 0|16@1+ (0.25,0) [0|16383.75] "rpm" Cluster, TCU
 SG_ EngineTemp  : 16|8@1+ (1,-40) [-40|215] "degC" Cluster
```

### Integration Practical Example
```
Integration task: Add new signal "BrakePedalActive" to CAN
1. Update DBC file: add SG_ entry to braking message 0x240
2. Update AUTOSAR ARXML: add signal to COM configuration
3. Regenerate COM module code
4. Rebuild and flash ECU
5. Verify in CANoe: send trigger, observe signal in trace
```

---

## 3.2 CAN FD (CAN with Flexible Data Rate)

### What is CAN FD?
CAN FD (ISO 11898-1:2015) extends Classical CAN with:
- Up to **64 bytes** payload (vs 8 bytes CAN 2.0)
- **Bit-rate switching**: slow arbitration phase (e.g., 500 kbps), fast data phase (e.g., 2–8 Mbps)

### CAN FD Frame Structure

```
+-----+----+----+----+----+----+------+-----+----+
| SOF | ID |BRS |ESI |DLC |DATA|Stuff |CRC  |ACK |
|     |11b | 1b | 1b | 4b |0-64B     |17/21b    |
+-----+----+----+----+----+----+------+-----+----+
```

- **BRS** — Bit Rate Switch (marks start of faster data phase)
- **ESI** — Error State Indicator
- **DLC** — Extended DLC table (9→12 bytes, 10→16 bytes, ... 15→64 bytes)

### CAN FD vs Classical CAN

| Feature | Classical CAN | CAN FD |
|---|---|---|
| Max payload | 8 bytes | 64 bytes |
| Data bit rate | Up to 1 Mbps | Up to 8 Mbps |
| Identifier | 11 or 29 bits | 11 or 29 bits |
| Backward compatible | — | Partially (FD-capable nodes needed) |
| Use case | Body, powertrain | ADAS, gateway, large data transfer |

### Integration Note
When integrating CAN FD, ensure:
- All nodes on the same bus support CAN FD
- Transceivers support FD (e.g., TJA1044, MCP2558FD)
- Bit timing is configured for both nominal and data phases
- DBC or FIBEX updated with FD frames

---

## 3.3 LIN (Local Interconnect Network)

### What is LIN?
LIN (ISO 17987) is a low-cost, single-wire serial protocol for simple sensor/actuator communication where CAN bandwidth is not needed.

- **Speed**: 1–20 kbps (typically 9.6 or 19.2 kbps)
- **Master/slave**: One master schedules all communication
- **Up to 16 slaves** on one cluster

### LIN Frame

```
+-------+-------+-------+-------+
| Break | Sync  |  PID  |  Data  | Checksum |
| 13bit | 0x55  |  8bit | 1-8 B  |   8bit   |
+-------+-------+-------+-------+----------+
```

- **Break** — Signals start of frame
- **Sync** — 0x55 for slave baud rate sync
- **PID** — Protected Identifier (6-bit ID + 2-bit parity)
- **Data** — 1–8 bytes

### LIN Schedule Table
The LIN master sends frames according to a fixed schedule table defining:
- Frame IDs
- Timing (period per frame)
- Direction (master-to-slave or slave response)

```
// Example schedule
0ms   Frame 0x10 (Window position request)
5ms   Frame 0x11 (Window position response)
10ms  Frame 0x12 (Mirror control)
```

### LIN Integration Example
```
Use case: Driver seat position control over LIN

1. Body ECU (LIN master) sends frame 0x20 "SeatAdjustCmd"
2. Seat ECU (LIN slave) receives and adjusts motor
3. Seat ECU responds with frame 0x21 "SeatPositionStatus"
4. Body ECU reads position feedback
5. Verify with CANoe LIN analysis or LIN analyzer
```

### LIN Diagnostics
LIN supports diagnostics via Master Request Frame (0x3C) and Slave Response Frame (0x3D), following ISO 14229 (UDS over LIN).

---

## 3.4 FlexRay

### What is FlexRay?
FlexRay (ISO 17458) is a deterministic, fault-tolerant high-speed communication protocol used in safety-critical systems (e.g., X-by-wire, active suspension).

- **Speed**: Up to 10 Mbps per channel (channels A and B for redundancy)
- **Deterministic**: Time-triggered, no arbitration needed
- **Two channels (A/B)**: Independent, can be used for redundancy or higher bandwidth

### FlexRay Architecture

```
+-------+     +-------+     +-------+
| ECU A |-----| Bus   |-----| ECU B |
+-------+     | Guard |     +-------+
              +-------+
              (Optional Star/Bus topology)
```

### Static and Dynamic Segments

```
FlexRay Cycle:
+-------------------+----------+------+
|  Static Segment   | Dynamic  | Sym  |
| (TDMA-scheduled)  | Segment  | Wndw |
+-------------------+----------+------+
  Deterministic timing  Event-driven  Sync
```

- **Static Segment**: Fixed TDMA slots; each slot always carries the same data
- **Dynamic Segment (FIFO)**: On-demand transmission, like CAN mini-slot

### FlexRay Integration
FlexRay was common in advanced chassis systems (BMW active suspension, Mercedes-Benz) but is being replaced by Automotive Ethernet in new platforms.

**Integration tasks**: Configure static slot assignments, verify cycle time, check synchronization, validate with FlexRay analyzer.

---

## 3.5 Automotive Ethernet

### Why Automotive Ethernet?
Traditional CAN/LIN bandwidth is insufficient for camera data (raw: ~2 Gbps), radar, LiDAR, OTA updates, and centralized architectures.

### Physical Layer Standards

| Standard | Speed | Cable | Use |
|---|---|---|---|
| 100BASE-T1 (BroadR-Reach) | 100 Mbps | 1 pair UTP | Cameras, sensors, ECUs |
| 1000BASE-T1 | 1 Gbps | 1 pair UTP | Gateway, ADAS, IVI |
| 10GBASE-T1 | 10 Gbps | 1 pair | Central compute backbone |
| 10BASE-T1S | 10 Mbps | Single wire, multi-drop | Low-cost sensors |

### VLAN (Virtual LAN)
Automotive Ethernet uses VLANs (IEEE 802.1Q) to separate traffic domains:
- VLAN 100: ADAS camera traffic
- VLAN 200: Diagnostics (DoIP)
- VLAN 300: Infotainment

### SOME/IP (Scalable service-Oriented MiddlewarE over IP)

SOME/IP is the standard middleware for service-oriented automotive Ethernet communication.

**Core concepts:**
- **Service**: A named functionality provided by one ECU (e.g., "SpeedService")
- **Method call**: Request/Response (like RPC)
- **Event**: Periodic or on-change notification
- **Field**: Getter/Setter with notification

```
SOME/IP Message Structure:
+----------+--------+--------+---------+----------+
| Service  | Method | Length | Request | Protocol |
|  ID (2B) | ID (2B)| (4B)   | ID (4B) | Version  |
+----------+--------+--------+---------+----------+
| Interface | Message | Return  | Payload  ...     |
|  Version  |  Type   |  Code   |                  |
+----------+--------+--------+---------------------|
```

### SOME/IP-SD (Service Discovery)

SOME/IP-SD allows services to be found dynamically at runtime:
1. **OfferService** — Server announces availability
2. **FindService** — Client searches for a service
3. **Subscribe/SubscribeAck** — Client subscribes to events

```
Flow:
Server ECU --[OfferService "SpeedService"]--> Multicast 224.0.0.1
Client ECU --[FindService "SpeedService"]--> Multicast
Server ECU --[OfferService Response]--> Client ECU
Client ECU --[SubscribeEventgroup]--> Server ECU
Server ECU --[SubscribeAck]--> Client ECU
Server ECU --[Speed event: 80 km/h]--> Client ECU (periodic)
```

### DoIP (Diagnostics over Internet Protocol) — ISO 13400

DoIP carries UDS diagnostic messages over Ethernet/IP.

```
Tester ←→ DoIP Entity (Gateway ECU) ←→ Target ECU
   TCP port 13400 (default)

DoIP PDU:
+----------+--------+---------+--------+---------+
| Protocol | Payload| Payload | Source | Target  |
| Version  |  Type  | Length  | Addr   | Addr    |
|  (2B)    |  (2B)  |  (4B)   | (2B)   | (2B)    |
+----------+--------+---------+--------+---------+
| UDS data ...                                    |
+-------------------------------------------------+
```

### TCP/IP and UDP in Automotive

- **TCP**: Used for reliable communication (UDS over DoIP, OTA downloads)
- **UDP**: Used for SOME/IP events (low-latency, fire-and-forget)
- **TLS**: Used over TCP for secure communication (OTA, remote diagnostics)

### TSN (Time-Sensitive Networking)

TSN (IEEE 802.1 standards) adds determinism to Ethernet:
- **IEEE 802.1AS**: Time synchronization (gPTP)
- **IEEE 802.1Qbv**: Time-Aware Shaper (scheduled traffic)
- **IEEE 802.1Qbu/802.3br**: Frame preemption
- Use case: ADAS sensor fusion (timestamps must align across sensors)

### Automotive Ethernet Integration Example

```
ADAS Camera Integration:
1. Camera sends raw video via 100BASE-T1 Ethernet
2. Integrate with camera HAL driver in Linux
3. Configure VLAN 100 for camera traffic
4. SOME/IP-SD: camera announces "CameraService"
5. ADAS ECU subscribes to "CameraService"
6. Verify bandwidth (raw 1080p30 ≈ 100 Mbps → use MJPEG/H.264 compression)
7. TSN: synchronize camera timestamp with GNSS PPS signal (IEEE 802.1AS)
8. Use Wireshark + Automotive Ethernet adapter to capture and analyze
```

---

## 3.6 Communication Matrix

A Communication Matrix (often called CAN Matrix or Network Database) is a spreadsheet or database listing all signals exchanged on all networks.

| Signal Name | ECU Source | ECU Consumer | Protocol | Message ID | Period | Signal Range |
|---|---|---|---|---|---|---|
| VehicleSpeed | ABS_ECU | Cluster, ADAS | CAN | 0x0C9 | 10ms | 0–511 km/h |
| EngineRPM | Engine_ECU | Cluster, TCU | CAN | 0x0C8 | 10ms | 0–16383 rpm |
| CameraData | Camera_ECU | ADAS_DC | ETH/SOME/IP | — | On event | Video stream |
| WheelAngle | EPS_ECU | ADAS_DC | CAN FD | 0x3A0 | 5ms | -540 to +540 deg |

---

## Summary

| Protocol | Speed | Payload | Use Case |
|---|---|---|---|
| CAN 2.0 | ≤1 Mbps | 8 bytes | Body, powertrain, chassis |
| CAN FD | ≤8 Mbps | 64 bytes | ADAS, gateway |
| LIN | ≤20 kbps | 8 bytes | Mirrors, seats, simple actuators |
| FlexRay | 10 Mbps | 254 bytes | X-by-wire (legacy) |
| Eth 100BASE-T1 | 100 Mbps | MTU 1500B | Cameras, sensors, ECUs |
| Eth 1000BASE-T1 | 1 Gbps | MTU 1500B | ADAS domain, gateway, IVI |
| SOME/IP | — (over Eth) | Variable | Service-oriented communication |
| DoIP | — (over Eth) | Variable | Diagnostics over Ethernet |

---

*Next: [Part 4 — AUTOSAR Integration](part-04-autosar.md)*
