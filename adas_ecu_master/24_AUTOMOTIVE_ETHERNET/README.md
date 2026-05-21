# 24 — Automotive Ethernet

> **Standards:** 100BASE-T1 (OPEN Alliance), 1000BASE-T1, IEEE 802.1 TSN, SOME/IP

---

## 24.1 Automotive Ethernet vs. Traditional CAN

| Feature         | CAN Classic   | CAN FD        | Automotive Ethernet       |
|-----------------|---------------|---------------|---------------------------|
| Max bandwidth   | 1 Mbit/s      | 8 Mbit/s      | 100 Mbit/s – 10 Gbit/s   |
| Payload         | 8 bytes       | 64 bytes      | 1500 bytes (MTU)          |
| Cabling         | Twisted pair (2-wire) | Same  | Single pair (100BASE-T1)  |
| Topology        | Bus           | Bus           | Point-to-point + switched |
| Latency         | < 1ms         | < 1ms         | < 100µs (TSN)             |
| Use case        | Body, chassis | Sensor data   | Camera, radar, OTA, DoIP  |
| Diagnostics     | ISO-TP + UDS  | ISO-TP + UDS  | DoIP (ISO 13400)          |

---

## 24.2 100BASE-T1 Physical Layer

```
100BASE-T1 (IEEE 802.3bw):
  - Single unshielded twisted pair (UTP)
  - 100 Mbit/s full-duplex over 15m cable
  - 3-level PAM3 encoding (less EMI than 100BASE-TX)
  - No RJ45 — uses automotive-grade miniaturised connectors (HSD, FAKRA)
  - DC common mode voltage: 0-1V (automotive-grade, tolerates ground differences)

1000BASE-T1 (IEEE 802.3bp):
  - 1 Gbit/s on single pair, up to 15m
  - Used for: camera ECU → domain controller, radar data streams
  
10BASE-T1S (IEEE 802.3cg):
  - 10 Mbit/s, up to 25m, multi-drop (up to 8 nodes on one segment)
  - Replaces CAN in low-speed body/chassis networks (Ford, BMW evaluation)
```

---

## 24.3 TSN — Time-Sensitive Networking

```
TSN solves: latency + jitter guarantees in switched Ethernet (vs best-effort)

Key TSN standards for automotive:
  IEEE 802.1Qbv — Scheduled traffic (time gates for deterministic windows)
  IEEE 802.1Qbu — Frame preemption (high priority can interrupt low priority)
  IEEE 802.1Qav — Credit-based shaper (smooth bandwidth for audio/video streams)
  IEEE 802.1AS  — Time synchronisation (gPTP, < 1µs accuracy)

Use case: ADAS camera stream at 30fps needs guaranteed 8ms window per frame
  Without TSN: Ethernet switch may queue the frame behind a 1400-byte payload → jitter
  With TSN 802.1Qbv: time gate opens for camera stream every 33ms, no queue interference

TSN switch: NXP SJA1110 (used in Tier 1 domain controller designs)
```

---

## 24.4 SOME/IP — Scalable Service-Oriented Middleware over IP

```
Architecture: Service-based (vs signal-based CAN)
  Service: a named interface with methods, events, and fields
  Publisher: service provider (e.g., radar object list service)
  Subscriber: service consumer (e.g., ACC controller)
  
SOME/IP message types:
  REQUEST       → client → server (method call, expects response)
  RESPONSE      → server → client (result of method call)
  EVENT         → server → subscriber (no request needed, periodic or on-change)
  NOTIFICATION  → similar to event but for field changes

SOME/IP Service Discovery (SD):
  UDP multicast on port 30490
  OfferService: server announces availability
  FindService: client searches for service
  Subscribe EventGroup: client subscribes to events

Serialisation: 
  Big-endian by default (TLV or fixed layout)
  Length field: 32-bit message length (after header)
  
Header format (8 bytes):
  Service ID (16-bit) | Method ID (16-bit)
  Length (32-bit, incl. header)
  Client ID (16-bit) | Session ID (16-bit)
  Protocol version (8-bit) | Interface version (8-bit) | Msg type (8-bit) | Return code (8-bit)
```

---

## 24.5 Automotive Ethernet Switch (NXP SJA1110)

```
Features:
  - 5× 100BASE-T1 ports + 1× SGMII uplink to main SoC
  - IEEE 802.1Q VLANs (traffic isolation between domains)
  - IEEE 802.1Qbv TSN gating
  - IEEE 802.1AS gPTP hardware timestamping
  - 10BASE-T1S multi-drop port (for legacy low-speed devices)
  - SPI management interface (configure via Automotive BSP)

VLAN configuration example:
  VLAN 10: ADAS bus (camera, radar, domain controller)
  VLAN 20: Infotainment bus (HMI, connectivity module)
  VLAN 30: Diagnostics bus (OBD-II gateway, DoIP)
  
  Rules: ADAS → Infotainment: BLOCKED (security + isolation)
         OBD-II → ADAS: ALLOWED for diagnostics
```

---

## 24.6 Interview Questions

**L1:**
1. What is 100BASE-T1 and why is single-pair Ethernet used in automotive?
2. What is SOME/IP?
3. What is the purpose of TSN in automotive networks?

**L2:**
4. How does SOME/IP service discovery work?
5. What TSN mechanism guarantees latency for a camera stream?
6. Describe the difference between REQUEST and EVENT message types in SOME/IP.

**L3:**
7. Design the automotive Ethernet backbone for a Level 3 domain controller vehicle.
8. How would you configure TSN time gates for camera (30fps) and radar (20Hz) streams?
9. What are the security risks in automotive Ethernet and how does ISO/SAE 21434 address them?
10. Compare SOME/IP vs DDS for Adaptive AUTOSAR service communication.
