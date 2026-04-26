# Automotive Ethernet — Complete Engineering Guide

> **Audience:** Automotive software/test engineers working on ADAS, IVI, body domains  
> **Scope:** Physical layer → OSI stack → TSN → DoIP → SOME/IP → Testing → Interview Q&A  
> **Last Updated:** 2026-04-26

---

## Table of Contents

1. [Why Automotive Ethernet?](#1-why-automotive-ethernet)
2. [100BASE-T1 (BroadR-Reach)](#2-100base-t1-broadr-reach)
3. [1000BASE-T1](#3-1000base-t1)
4. [10BASE-T1S — Multidrop](#4-10base-t1s--multidrop)
5. [Physical Layer Details](#5-physical-layer-details)
6. [Automotive Ethernet Topology](#6-automotive-ethernet-topology)
7. [OSI Model in Automotive Ethernet](#7-osi-model-in-automotive-ethernet)
8. [VLAN — IEEE 802.1Q](#8-vlan--ieee-8021q)
9. [AVB and TSN](#9-avb-and-tsn)
10. [DoIP — ISO 13400-2](#10-doip--iso-13400-2)
11. [SOME/IP Overview](#11-someip-overview)
12. [Ethernet Switch in Automotive](#12-ethernet-switch-in-automotive)
13. [Wireshark for Automotive Ethernet](#13-wireshark-for-automotive-ethernet)
14. [Testing Automotive Ethernet](#14-testing-automotive-ethernet)
15. [STAR Scenarios](#15-star-scenarios)
16. [Interview Q&A — 15 Questions](#16-interview-qa--15-questions)

---

## 1. Why Automotive Ethernet?

### 1.1 Bandwidth Demands of ADAS and Autonomous Driving

Modern vehicles are rolling sensor platforms:

| Sensor / System         | Raw Data Rate         |
|-------------------------|-----------------------|
| Front camera (1080p)    | ~400 Mbit/s raw       |
| Surround-view (4 cams)  | ~1.6 Gbit/s raw       |
| LiDAR (64-channel)      | ~700 Mbit/s           |
| Radar (4D imaging)      | ~100–300 Mbit/s       |
| Fusion ECU compute      | Several Gbit/s total  |
| OTA update package      | 1–4 GB per campaign   |

Even after compression, moving camera and LiDAR data from sensors to a central ADAS domain controller requires **gigabit-class** bandwidth. CAN FD and FlexRay cannot provide this.

### 1.2 Limitations of CAN FD and FlexRay

**CAN FD:**
- Maximum data phase bit rate: **8 Mbit/s** (practical: 5 Mbit/s)
- Maximum payload per frame: **64 bytes**
- Bus arbitration is inherently non-deterministic under load
- No native IP address space — each node sees every message on the bus
- Not suitable for streaming large blocks of data

**FlexRay:**
- Maximum bit rate: **10 Mbit/s** (dual channel: 20 Mbit/s)
- Static/dynamic segment scheduling is complex to configure
- Limited deployment (mainly high-end chassis control)
- Industry uptake declined in favour of Ethernet for high-bandwidth use cases

**Automotive Ethernet advantages:**
- 100 Mbit/s to 10 Gbit/s scalability on same cabling infrastructure
- IP-based — integrates with standard internet protocols (TCP, UDP, TLS)
- Supports VLAN, TSN, QoS — deterministic scheduling where needed
- Single Pair Ethernet (SPE) reduces wiring weight vs. TP cables
- Enables OTA, cloud-connected diagnostics, V2X gateways

### 1.3 Industry Adoption Timeline

- **2011** — OPEN Alliance SIG formed; BroadR-Reach 100BASE-T1 spec published
- **2016** — IEEE 802.3bw (100BASE-T1) ratified
- **2018** — IEEE 802.3bp (1000BASE-T1) ratified
- **2019** — IEEE 802.3cg (10BASE-T1S multidrop) ratified
- **2020+** — Tesla, BMW, Volkswagen MEB, Hyundai E-GMP adopt Ethernet backbone
- **2025** — Multi-gigabit (2.5G/10G) in ADAS compute nodes production-level

---

## 2. 100BASE-T1 (BroadR-Reach)

### 2.1 Key Specifications

| Parameter             | Value                              |
|-----------------------|------------------------------------|
| Standard              | IEEE 802.3bw-2015                  |
| Medium                | Single Unshielded Twisted Pair (UTP) |
| Data rate             | 100 Mbit/s full-duplex             |
| Modulation            | PAM3 (3-level pulse amplitude)     |
| Cable length          | Up to 15 m (automotive use case)   |
| Connector             | H-MTD, HSD, FAKRA variants         |
| Power over cable      | Possible (PoE variations)          |
| Impedance             | 100 Ω differential                 |

### 2.2 PAM3 Modulation

Unlike classic Ethernet (NRZ binary), 100BASE-T1 uses **PAM3** — three voltage levels (+1, 0, −1). This encodes 3 bits across 2 PAM3 symbols using a 4B3T-inspired code, achieving 100 Mbit/s on a single pair where binary NRZ would need 200 MHz signalling.

### 2.3 How 100BASE-T1 Differs from 1000BASE-T (Standard IT Ethernet)

| Feature               | 100BASE-T (IEEE 802.3u)       | 100BASE-T1 (IEEE 802.3bw)     |
|-----------------------|-------------------------------|-------------------------------|
| Cable pairs needed    | 2 pairs (4 wires)             | 1 pair (2 wires)              |
| Max cable length      | 100 m                         | 15 m                          |
| Connector             | RJ45                          | H-MTD / HSD / FAKRA           |
| Environment           | Office/IT                     | Automotive — vibration, temp  |
| Cost per node         | Higher (4-wire + RJ45)        | Lower (2-wire + compact conn) |
| EMC standard          | IEEE 802.3                    | OPEN Alliance TC8, ISO 17987  |

### 2.4 BroadR-Reach IP and OPEN Alliance

BroadR-Reach was originally a Broadcom technology licensed to the OPEN Alliance SIG, which opened it to the industry and drove IEEE standardisation as 100BASE-T1.

---

## 3. 1000BASE-T1

### 3.1 Key Specifications

| Parameter             | Value                                |
|-----------------------|--------------------------------------|
| Standard              | IEEE 802.3bp-2016                    |
| Medium                | Single shielded twisted pair (STP)   |
| Data rate             | 1000 Mbit/s (1 Gbit/s) full-duplex  |
| Modulation            | PAM3 at 750 Mbaud                    |
| Cable length          | Up to 15 m                           |
| Impedance             | 100 Ω differential                   |

### 3.2 ADAS Backbone Use Case

1000BASE-T1 is the workhorse of the ADAS sensor backbone:

```
[Front Camera] ──1000BASE-T1──┐
[Rear Camera]  ──1000BASE-T1──┤   [Central Domain    ]──10GbE──[Fusion ECU]
[LiDAR unit]   ──1000BASE-T1──┤   [Ethernet Switch   ]
[4D Radar]     ──1000BASE-T1──┘
```

- Camera ISP output → serialised over GMSL/FPD-Link → deserialised and bridged to 1000BASE-T1 into an automotive switch
- 4D imaging radar generates point clouds → 1000BASE-T1 can carry 10–20 Hz point cloud updates
- The central ADAS domain controller aggregates all streams and requires multi-gigabit uplinks

### 3.3 Shielding Requirement

1000BASE-T1 requires shielded twisted pair due to the higher Baud rate and correspondingly higher EMC emission risk. The shield must be properly terminated at both ends; floating shields cause common-mode noise amplification.

---

## 4. 10BASE-T1S — Multidrop

### 4.1 Key Specifications

| Parameter             | Value                                |
|-----------------------|--------------------------------------|
| Standard              | IEEE 802.3cg-2019                    |
| Medium                | Single Unshielded Twisted Pair       |
| Data rate             | 10 Mbit/s half-duplex                |
| Topology              | Multidrop bus — up to 25 nodes       |
| Cable length          | Up to 25 m (15 m per segment typical)|
| Access control        | PLCA (Physical Layer Collision Avoidance) |
| Impedance             | 100 Ω                                |

### 4.2 PLCA — Replacing CSMA/CD

10BASE-T1S uses **Physical Layer Collision Avoidance (PLCA)** instead of the legacy CSMA/CD. Each node is assigned a node ID (0–N). The cycle coordinator (node 0) transmits a BEACON frame; each node in order gets a transmit opportunity (TO). If a node has nothing to send it passes; the cycle restarts.

Benefits:
- Deterministic maximum latency: proportional to N × cycle time
- No collisions — nodes only transmit in their allocated slot
- Simple bus wiring — reduces star topology cost for zones with many low-bandwidth nodes

### 4.3 CAN Replacement Use Cases

10BASE-T1S targets the "last mile" of the in-vehicle network where CAN FD is currently deployed but bandwidth or IP connectivity is needed:

- Body domain: door modules, seat control, ambient lighting (each 10 Mbit/s is enough)
- Zone ECU fan-out: a zone ECU (running 1000BASE-T1 uplink) fans out to 8–16 body nodes on 10BASE-T1S
- Sensor fusion pre-processing units exchanging small status telegrams
- Replacement for LIN in medium-bandwidth sensors

---

## 5. Physical Layer Details

### 5.1 MDI Connector Types

| Connector Family | Usage                                 |
|------------------|---------------------------------------|
| H-MTD            | 100BASE-T1 and 1000BASE-T1, compact   |
| HSD (High Speed Data) | 100BASE-T1, robust IP67 options  |
| FAKRA            | RF-style, used for camera/antenna links|
| MATEnet          | TE Connectivity standard for SPE      |
| IEC 63171-6      | Industrial SPE, some automotive use   |

### 5.2 EMC Requirements

Automotive Ethernet must comply with:
- **CISPR 25** — radiated emissions from in-vehicle networks
- **ISO 11452** — vehicle EMC immunity (BCI, bulk current injection)
- **OPEN Alliance TC8 / TC12** — Ethernet PHY compliance test suites
- **ISO 17987** — local interconnect test methods adapted for SPE

Key design rules:
1. Keep stub length < 100 mm on multidrop 10BASE-T1S buses
2. Use differential routing — route both wires as tightly coupled pair
3. Termination: 100 Ω differential at each end of the segment (or built into PHY)
4. Shield termination: 360° connection to chassis at connector shell
5. Ferrite bead on power supply to PHY to reduce switching noise injection

### 5.3 Cable Types

| Type        | Impedance | Max Length | Notes                       |
|-------------|-----------|------------|-----------------------------|
| UTP Cat 5e  | 100 Ω     | 15 m       | 100BASE-T1 unshielded       |
| STP Cat 6   | 100 Ω     | 15 m       | 1000BASE-T1 shielded        |
| Automotive UTP | 100 Ω  | 15 m       | Thin, flexible, oil-resistant|
| Coax (hybrid)| 50/75 Ω  | N/A        | Camera SerDes, not SPE      |

---

## 6. Automotive Ethernet Topology

### 6.1 Star Topology

Classic switched-star: each node connects point-to-point to a central switch.

```
    [ECU A]──────┐
    [ECU B]──────┤
    [Camera]─────┤── [Central Switch] ──── [Domain Controller]
    [Radar]──────┤
    [ECU C]──────┘
```

**Pros:** Simple, no shared medium, full-duplex on all links  
**Cons:** Switch is a single point of failure; many cables converge at switch

### 6.2 Daisy-Chain / Line Topology

Nodes daisy-chained — each node has two Ethernet ports; frame forwarded hop-by-hop.

```
[Gateway] ── [Switch1] ── [Switch2] ── [Switch3]
                |              |              |
             [ECUs]         [ECUs]         [ECUs]
```

**Pros:** Reduced cabling harness weight  
**Cons:** Latency accumulates; failure of intermediate node severs downstream

### 6.3 Ring Topology

Loop-back added to line topology; IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER) provides redundancy.

### 6.4 Zone ECU / Domain Controller Architecture

Modern OEM architecture:

```
Sensor Zone (front)          Body Zone (left)         Body Zone (right)
 [Cam][Radar][LiDAR]          [Door][Seat][Light]       [Door][Seat][Light]
       │ 1000BASE-T1                │ 10BASE-T1S               │ 10BASE-T1S
  [Zone ECU A]                [Zone ECU B]              [Zone ECU C]
       │ 10GbE                      │ 1GbE                     │ 1GbE
       └──────────────[Backbone Switch]───────────────────────┘
                              │
                    [Central Computer / HPC]
                         │ DoIP │ SOME/IP
                    [OBD Port / OTA Gateway]
```

The **Zone ECU** aggregates local sensors and body nodes, converting heterogeneous buses (LIN, CAN, 10BASE-T1S) to backbone Ethernet.

---

## 7. OSI Model in Automotive Ethernet

```
┌─────────────────────────────────────────────────────────────────┐
│  L7  Application     │ SOME/IP, DoIP, HTTP/REST, MQTT           │
├─────────────────────────────────────────────────────────────────┤
│  L6  Presentation    │ Serialisation formats (SOME/IP, FIDL)    │
├─────────────────────────────────────────────────────────────────┤
│  L5  Session         │ TLS/DTLS, SOME/IP SD sessions            │
├─────────────────────────────────────────────────────────────────┤
│  L4  Transport       │ TCP (DoIP, SOME/IP reliable) / UDP       │
├─────────────────────────────────────────────────────────────────┤
│  L3  Network         │ IPv4 / IPv6   ICMP, ARP                  │
├─────────────────────────────────────────────────────────────────┤
│  L2  Data Link       │ IEEE 802.3 Ethernet frame, 802.1Q VLAN   │
│                      │ 802.1AS gPTP, 802.1Qbv TSN               │
├─────────────────────────────────────────────────────────────────┤
│  L1  Physical        │ 100BASE-T1 / 1000BASE-T1 / 10BASE-T1S   │
└─────────────────────────────────────────────────────────────────┘
```

### L2 Frame Structure (Automotive Ethernet with VLAN)

```
 ┌──────┬──────┬──────┬────────┬──────────┬──────────┬──────┐
 │ Dst  │ Src  │ 8100 │ TCI    │ EtherType│ Payload  │ FCS  │
 │ MAC  │ MAC  │ VLAN │ PCP+DEI│          │ (46-1500)│      │
 │ 6B   │ 6B   │ 2B   │ 2B     │ 2B       │          │ 4B   │
 └──────┴──────┴──────┴────────┴──────────┴──────────┴──────┘
```

- **PCP (Priority Code Point):** 3 bits → 8 traffic classes (0=best effort, 7=highest)
- **DEI (Drop Eligible Indicator):** 1 bit — mark frame as droppable under congestion
- **VLAN ID:** 12 bits → 4094 VLANs

---

## 8. VLAN — IEEE 802.1Q

### 8.1 What VLAN Provides

- **Traffic separation:** ADAS data on VLAN 10, diagnostics on VLAN 20, infotainment on VLAN 30
- **Security:** OBD tester cannot see ADAS camera stream (different VLAN)
- **QoS:** Priority bits ensure safety-critical frames are not delayed by entertainment data
- **Broadcast domain control:** ARP/GARP storms contained within VLAN

### 8.2 VLAN Assignment in Zonal Architecture

| VLAN ID | Domain                  | Traffic                         | Priority |
|---------|-------------------------|---------------------------------|----------|
| 10      | ADAS Sensor             | Camera, Radar, LiDAR streams    | 6–7      |
| 20      | Powertrain              | CAN gateway frames              | 5        |
| 30      | Body/Comfort            | Lighting, HVAC, seats           | 3        |
| 40      | InfotainmentIVI         | Audio, video, navigation        | 2        |
| 50      | Diagnostics             | DoIP UDS sessions               | 4        |
| 100     | Management              | Switch management, time sync    | 7        |

### 8.3 Port Modes

- **Access port:** Untagged ingress; switch assigns VLAN; egress untagged → for ECUs that don't understand VLAN tags
- **Trunk port:** Tagged ingress/egress; carries multiple VLANs → inter-switch links
- **Hybrid port:** Mix of tagged and untagged VLANs on same port → zone ECU uplinks

---

## 9. AVB and TSN

Time-Sensitive Networking is the suite of IEEE 802.1 standards that makes Ethernet deterministic enough for safety-critical and real-time automotive applications.

### 9.1 IEEE 802.1AS — gPTP (Generalized Precision Time Protocol)

**Purpose:** Synchronise all Ethernet nodes to a common time reference with sub-microsecond accuracy.

**How it works:**
1. A **Grand Master Clock (GMC)** is elected (typically the domain controller or a GNSS-disciplined node)
2. GMC sends **Sync** messages every 125 ms (configurable)
3. Each device calculates the **propagation delay** using Peer Delay mechanism (Pdelay_Req / Pdelay_Resp)
4. Local clock is adjusted to track the master — correction field carries residence time through switches
5. Each switch is a **transparent clock** (measures and adds its own residence time) or **boundary clock**

**Accuracy:** Typically ±100 ns end-to-end across an automotive network

**Why it matters for ADAS:**
- Sensor timestamps from camera, radar, and LiDAR must be correlated to the same timebase for sensor fusion
- Without gPTP synchronisation, a 100 µs clock offset at 30 m/s vehicle speed = 3 mm position error in fusion

### 9.2 IEEE 802.1Qbv — Time-Aware Shaper (TAS)

**Purpose:** Guarantee time slots for specific traffic classes using a **Gate Control List (GCL)**.

**Mechanism:**
- Each switch egress port has 8 queues (one per traffic class)
- A GCL defines a repeating schedule: e.g., every 1 ms cycle, queue 7 is open for 200 µs, queue 3 for 300 µs, etc.
- Non-scheduled traffic cannot preempt a scheduled window
- Schedule aligned across all switches using gPTP — same GCL offset from gPTP epoch

```
Time cycle: 1 ms
 ├── 0–200µs:  Q7 OPEN (ADAS sensor data)   Q0-Q6 CLOSED
 ├── 200–500µs:Q5 OPEN (powertrain CAN-Eth) Q7 CLOSED
 ├── 500–800µs:Q3 OPEN (body domain)        others CLOSED
 └── 800–1000µs: Q0 OPEN (best effort)
```

**Use case:** ADAS camera frame must arrive at fusion ECU within 5 ms; TAS reserves the first 200 µs of each millisecond for ADAS stream.

### 9.3 IEEE 802.1Qbu / 802.3br — Frame Preemption

**Purpose:** Allow high-priority "express" frames to interrupt the transmission of a lower-priority "preemptable" frame.

- A large video frame (1500 B) takes ~12 µs to transmit at 1 Gbit/s
- Without preemption, a 60-byte safety-critical alert could be delayed by that full 12 µs
- With frame preemption: express frame can interrupt mid-transmission of preemptable frame; preemptable frame is reassembled at receiver using mPacket mechanism

### 9.4 IEEE 802.1Qav — Credit-Based Shaper (CBS)

**Purpose:** Bandwidth reservation for audio/video streams — AVB (Audio/Video Bridging) use case.

- Two shaping classes: Class A (2 ms latency, 125 µs observation interval) and Class B (50 ms latency)
- A credit counter controls transmission: credit increases while idle, consumed when transmitting; when credit < 0, frame held back
- Prevents any single stream from monopolising bandwidth
- Used for IVI surround sound (Class B) and rear-seat entertainment video

### 9.5 Combined TSN Stack for Automotive

```
Application Layer (SOME/IP / RTP / custom)
        │
     [TAS Scheduler gated by GCL — 802.1Qbv]
        │
     [Frame Preemption — 802.1Qbu/802.3br]
        │
     [Credit-Based Shaper — 802.1Qav]
        │
     [gPTP Clock Sync — 802.1AS]
        │
     [1000BASE-T1 / 10GbE Physical Layer]
```

---

## 10. DoIP — ISO 13400-2

*(Brief overview here — see `02_doip_deep_dive.md` for full protocol details)*

### 10.1 What DoIP Is

**Diagnostics over Internet Protocol** — a transport protocol defined in ISO 13400 that tunnels UDS (ISO 14229) diagnostic messages over TCP/IP, replacing the physical OBD-II K-Line and CAN-based ISO 15765-2 (CAN TP) for Ethernet-connected vehicles.

### 10.2 Why DoIP?

- OBD-II physical access limits; workshop testers and OTA servers communicate over Wi-Fi/Ethernet
- Higher throughput: flashing a 4 GB software image over CAN TP at 8 Mbit/s → minutes; over DoIP on 100BASE-T1 → seconds
- Remote diagnostics: vehicle exposes DoIP endpoint over cellular/Wi-Fi to cloud backend

### 10.3 Key Ports and Roles

| Item                   | Value                   |
|------------------------|-------------------------|
| UDP port (discovery)   | 13400                   |
| TCP port (diagnostic)  | 13400                   |
| External test tool     | Connects to DoIP gateway|
| DoIP gateway           | Edge router for UDS     |
| DoIP node              | ECU reachable via gateway|

### 10.4 Session Flow (Summary)

```
Step 1:  Tester → UDP broadcast: Vehicle Identification Request
Step 2:  DoIP Gateway → UDP: Vehicle Announcement (VIN, EID, GID)
Step 3:  Tester → TCP SYN to port 13400
Step 4:  Tester → Routing Activation Request (source address, activation type)
Step 5:  Gateway → Routing Activation Response (0x10 = success)
Step 6:  Tester → Diagnostic Message (SA, TA, UDS payload)
Step 7:  Gateway → Diagnostic Message ACK + DoIP Node → UDS Response
Step 8:  Tester → TCP FIN
```

---

## 11. SOME/IP Overview

SOME/IP (Scalable service-Oriented MiddlewarE over IP) is the standard application-layer automotive middleware used in AUTOSAR Adaptive platforms.

| Feature          | Detail                                           |
|------------------|--------------------------------------------------|
| Transport        | UDP (events, fire-and-forget) / TCP (methods)    |
| Default port     | 30490 (SOME/IP-SD) / app-defined for services   |
| SOME/IP-SD       | Service Discovery — FindService, OfferService, Subscribe |
| Serialisation    | Little-endian binary; FIDL-defined data types    |
| Message types    | REQUEST, RESPONSE, NOTIFICATION, ERROR           |

**Wireshark filter:** `someip` or `udp.port == 30501` (example service port)

SOME/IP is used for: inter-ECU method calls (RPC), periodic signal publication (events), IVI media info, ADAS object lists subscribed by HMI.

---

## 12. Ethernet Switch in Automotive

### 12.1 L2 Managed Switch Features Required

| Feature              | Automotive Purpose                              |
|----------------------|-------------------------------------------------|
| VLAN (802.1Q)        | Domain separation, security, QoS               |
| RSTP / MSTP          | Redundancy in ring topologies                   |
| TSN (802.1AS/Qbv)    | Deterministic delivery for ADAS                 |
| Port mirroring (SPAN)| Debug traffic capture without disrupting flow   |
| ACL / Firewall rules | Block non-authorised traffic (zero-trust)       |
| SNMP/NETCONF agent   | Remote management and monitoring                |
| Cut-through switching| Reduce latency vs store-and-forward             |

### 12.2 Port Mirroring for Debug

```
switch(config)# monitor session 1 source interface gi0/1
switch(config)# monitor session 1 destination interface gi0/8
```
- Port gi0/8 connected to laptop running Wireshark
- All traffic (ingress + egress) from gi0/1 copied to gi0/8
- Does not affect live traffic on gi0/1

### 12.3 Security VLANs and Port Isolation

- **Private VLAN:** Ports within same VLAN cannot communicate with each other — only with promiscuous uplink port (domain controller)
- Use case: 4 camera nodes on same VLAN, but cameras must not be able to send traffic to each other (prevent lateral movement if one node is compromised)
- **Storm control:** Limit broadcast/multicast/unknown unicast rate per port to protect against DoS

---

## 13. Wireshark for Automotive Ethernet

### 13.1 Capture Setup

**Option A — Ethernet TAP (passive):**
- Insert a passive optical or copper TAP between two nodes on the link
- TAP copies all frames to monitor port; fully transparent, no impact on link timing
- For 100BASE-T1/1000BASE-T1: requires specialised automotive TAP (e.g., Technica Engineering Ethernet TAP)

**Option B — Port Mirror on managed switch:**
- Configure SPAN session (see Section 12.2)
- Connect standard Ethernet NIC laptop to mirror port
- Suitable for switched networks; may miss physical layer errors

**Capture command (Linux):**
```bash
sudo tcpdump -i eth0 -w capture_automotive.pcap
# Or in Wireshark: Capture → Interfaces → eth0 → Start
```

### 13.2 Essential Filter Expressions

```wireshark
# Filter by source MAC
eth.src == 00:1a:2b:3c:4d:5e

# Filter by destination IP
ip.dst == 192.168.1.100

# Filter SOME/IP on specific port
udp.port == 30501

# Filter all SOME/IP traffic (requires SOME/IP dissector plugin)
someip

# Filter DoIP diagnostic messages
udp.port == 13400 || tcp.port == 13400

# Filter by VLAN ID
vlan.id == 10

# Filter by EtherType (VLAN tagged frames)
eth.type == 0x8100

# Filter TSN PTP sync frames
ptp.v2.messagetype == 0x0

# Filter only TCP retransmissions (debugging packet loss)
tcp.analysis.retransmission

# Filter ARP (useful for diagnosing IP config issues)
arp

# Combine filters
ip.src == 192.168.10.5 && udp.port == 30501 && someip
```

### 13.3 Dissector Plugins

**SOME/IP plugin:**
- Available in Wireshark 2.4+ natively (built-in SOME/IP dissector)
- Configuration: Edit → Preferences → Protocols → SOMEIP → Define service/method IDs from ARXML/FIDL
- Wireshark reads `someip_service_id.csv` for human-readable service names

**DoIP plugin:**
- Built into Wireshark 3.4+
- Automatically decodes Vehicle Announcement, Routing Activation, Diagnostic Messages
- UDS layer dissected on top of DoIP payload

### 13.4 Analysing DoIP Diagnostic Flow in Wireshark

1. Apply filter: `tcp.port == 13400`
2. Look for **SYN/SYN-ACK** — confirms TCP connection to DoIP gateway
3. Next packet: DoIP header `0xFFFE` (Routing Activation Request) payload type `0x0005`
4. Response: payload type `0x0006` with response code `0x10` (success)
5. Diagnostic message: payload type `0x8001` — contains Source Address, Target Address, UDS bytes
6. ACK: payload type `0x8002`
7. UDS response: next `0x8001` from node direction — decode UDS layer (e.g., `0x50 0x03` = Positive Response to DiagnosticSessionControl ExtendedDiagnostic)

**Tip:** Right-click on DoIP frame → Follow TCP Stream to see complete session in readable hex+ASCII.

---

## 14. Testing Automotive Ethernet

### 14.1 Physical Layer Testing

**Impedance measurement:**
- Tool: Time Domain Reflectometer (TDR) or Vector Network Analyser (VNA)
- Expected: 100 Ω ± 15% differential impedance along entire link
- Discontinuities (stubs, bad connectors) show as impedance spikes in TDR trace
- Standard: OPEN Alliance TC8 System Channel test

**Insertion Loss (IL):**
- Maximum allowed: specified per standard (e.g., 100BASE-T1: ≤14 dB at 66 MHz)
- Measured using VNA S21 parameter at relevant frequency range
- High IL → signal amplitude too low at receiver → increased BER

**Return Loss (RL):**
- Minimum required: ≥ 16 dB across operating frequency
- Low RL = significant reflections → ISI (inter-symbol interference)
- Caused by impedance mismatches, sharp cable bends, bad connector contacts

**Differential-to-common mode conversion (CDNR, ALMC):**
- Measures how much differential signal is converted to common-mode noise
- Important for CISPR 25 compliance

### 14.2 Protocol Conformance Testing

**Tools:** Spirent TestCenter, Ixia (Keysight), Lauterbach Trace32 (PHY debug)

**Test categories:**
1. **100BASE-T1 / 1000BASE-T1 PHY compliance:** Master/slave configuration, auto-negotiation, link establishment time < 600 ms
2. **IEEE 802.1AS gPTP conformance:** Sync message interval, clock accuracy, announce message, BMCA (Best Master Clock Algorithm)
3. **802.1Qbv TAS conformance:** GCL accuracy, guard band timing, queue draining
4. **VLAN conformance:** Tag insertion/removal, PVID assignment, trunking
5. **SOME/IP SD conformance:** Service offer/find/subscribe/stop-subscribe state machine
6. **DoIP conformance:** ISO 13400-2 test suite — each message type, all error codes

### 14.3 Application / Performance Testing

| Test                      | Method                                          | Pass Criterion                        |
|---------------------------|-------------------------------------------------|---------------------------------------|
| Throughput                | RFC 2544 with Spirent; binary search for max rate | ≥ 95% of line rate                  |
| Latency (store-forward)   | Spirent one-way latency with HW timestamps      | ≤ 10 µs per switch hop               |
| Latency (TSN stream)      | Measure scheduled stream end-to-end             | Within TAS window, ≤ target budget   |
| Jitter                    | Packet Delay Variation (PDV) per RFC 3393       | ≤ 1 µs for ADAS class streams        |
| Packet Loss               | RFC 2544 PL test at 100% load                   | 0 loss for scheduled TSN streams     |
| Burst handling            | Inject bursts; measure tail drop vs queue depth | No drop on priority queues           |
| OTA throughput            | Upload 1 GB file via DoIP, measure time         | ≥ 50 Mbit/s sustained                |

### 14.4 Security Testing

| Test                      | Method                                    | Expected Result                     |
|---------------------------|-------------------------------------------|-------------------------------------|
| VLAN isolation            | Send frame with VLAN ID outside access port | Switch drops; no cross-VLAN leakage|
| ARP spoofing prevention   | Send gratuitous ARP to hijack gateway IP   | Dynamic ARP Inspection (DAI) drops |
| Port security             | Connect unauthorised MAC to access port   | Port disabled by port-security rule |
| DoS — broadcast storm     | Flood broadcast frames on port            | Storm control rate-limits; CPU ok  |
| DoIP authentication       | Connect without valid routing activation  | Gateway rejects; no UDS access     |
| SOME/IP access control    | Subscribe to secured service without auth | SD rejects subscription            |

---

## 15. STAR Scenarios

### Scenario 1: Diagnosing a DoIP Routing Activation Failure

**Situation:** During integration testing of a new HPC (High-Performance Computer), the diagnostic tester fails to activate routing. CANoe log shows Routing Activation Response with code `0x00` (Denied — unknown source address).

**Task:** Diagnose and fix the routing activation failure.

**Action:**
1. Captured Wireshark trace on diagnostic port — confirmed Routing Activation Request is reaching the DoIP gateway (TCP connection established, payload type `0x0005` received)
2. Examined the request: Source Address = `0x0E01` — this address was not in the gateway's whitelist
3. Reviewed AUTOSAR ARXML configuration for the DoIP gateway module — the `DoIPConnections` table listed only `0x0E00` as permitted tester address
4. The tester tool had been reconfigured to a new SA range `0x0E01` by the tools team without updating the ARXML
5. Added `0x0E01` to the `DoIPTesterLogicalAddress` list in ARXML, regenerated BSW code, deployed updated flash
6. Also discovered the gateway's `DoIPMaxTesterConnections` was set to 1 — two test benches were connected simultaneously occasionally causing lock-out; increased to 2

**Result:** Routing activation succeeded with response `0x10`. DoIP session stable. Root cause documented in bug tracker linking to ARXML and tools configuration change process.

---

### Scenario 2: Setting Up an AVB/TSN Test for ADAS Camera Data

**Situation:** System architect requests validation that a camera stream on VLAN 10 meets the 5 ms end-to-end latency budget through two automotive Ethernet switches.

**Task:** Design and execute a TSN performance test.

**Action:**
1. Verified gPTP sync across both switches and two endpoints using `ptp4l` status and Wireshark PTP sync frame analysis — offset < 50 ns ✓
2. Configured GCL on both switches: 8 ms cycle, 2 ms reserved for VLAN 10 priority-7 queue (TAS), 1 ms guard band, remaining for lower-priority traffic
3. Used Spirent TestCenter to generate synthetic camera stream (jumbo UDP frames, 1400 B, 500 Mbit/s) tagged VLAN 10 priority 7
4. Simultaneously injected background traffic at 100% on other VLANs to simulate worst-case congestion on lower-priority queues
5. Measured one-way latency using Spirent hardware timestamps — resulted in p99.9 = 380 µs; well within 5 ms budget
6. Injected deliberate schedule misalignment (offset GCL by 200 µs on switch 2) — latency jumped to 8.5 ms, exceeding budget, confirming gPTP alignment is critical
7. Corrected alignment, re-tested — 390 µs

**Result:** Test report confirmed TSN stream meets latency budget under worst-case congestion. Identified gPTP alignment tolerance requirement of ±100 µs for the GCL offset.

---

### Scenario 3: Analysing a SOME/IP Subscription Failure in Wireshark

**Situation:** An HMI ECU fails to display speed data from the body domain gateway. SOME/IP subscription is suspected.

**Task:** Use Wireshark to identify the root cause.

**Action:**
1. Applied filter: `someip` on the diagnostic port mirror — saw `SubscribeEventgroup` from HMI (service ID `0x1234`, instance `0x0001`, eventgroup `0x0001`)
2. Expected: `SubscribeEventgroupAck` from server — instead, received `SubscribeEventgroupNack` with return code `0x07` (Endpoint option not supported)
3. The HMI was offering a **UDP multicast endpoint option** (`239.1.1.100:30501`) in its subscription; the gateway was configured for **unicast-only** SOME/IP events
4. Checked the AUTOSAR service manifest of the gateway: `UdpMulticastEventgroupSdElement` not configured — only `UdpUnicastEventgroupSdElement`
5. Two options: (a) configure gateway to support multicast, or (b) change HMI subscription to request unicast endpoint
6. Chosen fix: Updated HMI SOME/IP configuration to subscribe with unicast endpoint option (HMI IP + ephemeral UDP port)

**Result:** `SubscribeEventgroupAck` received after fix; speed data flowing to HMI. Documented as configuration mismatch between SD manifest and runtime behaviour.

---

### Scenario 4: Configuring an Ethernet Switch VLAN for Zone Architecture

**Situation:** A new zone ECU integration requires isolating ADAS traffic on the trunk link between zone ECU and backbone switch.

**Task:** Configure VLANs on two Marvell 88Q5050 automotive switches.

**Action:**
1. Defined VLAN plan: VLAN 10 = ADAS, VLAN 30 = Body, VLAN 50 = Diagnostics
2. Zone ECU port on backbone switch: configured as trunk, allowed VLANs 10, 30, 50; native VLAN 1 unused
3. Sensor ports (camera, radar) on zone switch: access port VLAN 10, untagged ingress, priority 7
4. Body node ports: access port VLAN 30, priority 3
5. DoIP diagnostic port: access port VLAN 50, priority 4
6. Verified with Wireshark on backbone trunk link: camera frames carry `802.1Q VLAN ID=10 PCP=7` tag, body frames `VLAN ID=30 PCP=3`
7. Attempted to send ADAS-VLAN frame out of a body port (port security test) — switch dropped it ✓

**Result:** VLAN zone architecture operational. Traffic isolated per domain. Security test passed.

---

### Scenario 5: Debugging Packet Loss on a 1000BASE-T1 Link

**Situation:** In HIL test environment, a 1000BASE-T1 link between ADAS domain controller and LiDAR simulator shows intermittent packet loss measured at ~0.02% — acceptable for most traffic but causing occasional LiDAR point cloud corruption.

**Task:** Root-cause and fix the packet loss.

**Action:**
1. Ran `ethtool -S eth1` counters on domain controller — found `rx_errors: 142`, `rx_crc_errors: 139` after 10-minute run
2. CRC errors = electrical Signal Integrity issue, not software (if it were software, we'd see `rx_missed_errors`)
3. Measured insertion loss with VNA on the cable — found 16.8 dB at 375 MHz (limit: 14 dB); cable was 22 m, exceeding max 15 m spec
4. Also found the shielded cable shield was only connected at one end (by connector installer mistake) — floating shield = common-mode noise antenna
5. Shortened cable to 12 m, terminated shield at both connector shells to chassis
6. Re-ran test: `rx_crc_errors: 0` after 30-minute soak ✓

**Result:** Packet loss eliminated. Added cable length and shielding checks to lab setup checklist. Updated installation guide with double-termination requirement.

---

## 16. Interview Q&A — 15 Questions

---

**Q1. Why can't we use standard CAN FD for ADAS camera data?**

**A:** CAN FD maximum payload is 64 bytes per frame at up to 8 Mbit/s. A single 1080p camera frame at 30 fps uncompressed generates ~12.4 MB/s of data, which exceeds CAN FD's theoretical capacity by two orders of magnitude. Even compressed H.264 at 4 Mbit/s would consume 50% of the entire CAN FD bus, leaving no capacity for control messages. Automotive Ethernet (1000BASE-T1 at 1 Gbit/s) provides 125× more bandwidth and native IP routing, making it the only viable choice for multi-camera ADAS.

---

**Q2. What is the difference between 100BASE-T1 and 1000BASE-T1?**

**A:** Both use a single twisted pair, but 1000BASE-T1 (IEEE 802.3bp) delivers 1 Gbit/s vs 100 Mbit/s for 100BASE-T1 (IEEE 802.3bw). The higher baud rate of 1000BASE-T1 requires a shielded twisted pair and is used for sensor backbones (camera, LiDAR). 100BASE-T1 runs on unshielded pairs and suits lower-bandwidth nodes (gateway control, body ECUs). Both use PAM3 modulation and are limited to 15 m in automotive environments.

---

**Q3. What is 10BASE-T1S and when would you use it instead of CAN?**

**A:** 10BASE-T1S (IEEE 802.3cg) is a multidrop single-pair Ethernet standard supporting up to 25 nodes on a single bus at 10 Mbit/s. It uses PLCA (Physical Layer Collision Avoidance), giving deterministic access. You would use it when migrating body domain nodes from CAN to Ethernet for IP addressability (e.g., enable HTTPS OTA or SOME/IP service model on body ECUs) while reusing bus-style wiring harness. CAN remains preferred where 10BASE-T1S switch/PHY cost is not justified.

---

**Q4. Explain gPTP (IEEE 802.1AS) and why it is critical for ADAS.**

**A:** gPTP is the automotive profile of IEEE 1588 Precision Time Protocol. It synchronises all nodes to a Grand Master Clock with sub-microsecond accuracy. In ADAS, sensor fusion algorithms (Kalman filter, object tracking) require that camera, radar, and LiDAR timestamps refer to the same time base. A 100 µs clock misalignment at 100 km/h corresponds to ~2.8 mm position error, which can cause false object merges or missed fusions. gPTP also aligns TSN Gate Control Lists across switches, enabling deterministic latency guarantees.

---

**Q5. What is a Gate Control List in IEEE 802.1Qbv?**

**A:** A Gate Control List is a time-triggered table stored in a TSN switch's egress port. It specifies a repeating cycle of time windows in which each of the 8 traffic class queues is open (allowed to transmit) or closed (blocked). All queues are aligned to the gPTP clock. A GCL entry looks like: "at time offset T=0 µs, open queue 7 for 200 µs; at T=200 µs, open queue 5 for 300 µs". This ensures ADAS stream frames reserved in queue 7 always depart within a bounded time, regardless of congestion in lower-priority queues.

---

**Q6. What is DoIP and how does it differ from ISO 15765-2 (CAN TP)?**

**A:** DoIP (ISO 13400-2) tunnels UDS diagnostic messages over TCP/IP using port 13400. It provides vehicle discovery via UDP broadcast, routing activation to select the target ECU, and then UDS PDU exchange over a TCP session. ISO 15765-2 (CAN TP) achieves the same UDS tunnelling but over CAN, using segmentation (First Frame, Consecutive Frame, Flow Control). Key differences: DoIP supports gigabit throughput (critical for software flashing), works over IP networks (OTA, Wi-Fi workshop), and uses logical addressing to reach any ECU behind the gateway without physical OBD access.

---

**Q7. What are the DoIP routing activation response codes you should know?**

**A:**
| Code | Meaning |
|------|---------|
| 0x00 | Denied - Unknown source address |
| 0x01 | Denied - No socket |
| 0x02 | Denied - Different source address |
| 0x03 | Denied - Source already registered and active |
| 0x04 | Denied - Missing authentication |
| 0x05 | Denied - Rejected confirmation |
| 0x06 | Denied - Unsupported routing activation type |
| 0x10 | Routing activation successful |
| 0x11 | Routing activation successful with confirmation required |

---

**Q8. How does SOME/IP differ from raw UDP sockets?**

**A:** SOME/IP adds a service-oriented layer on top of UDP/TCP. It defines a fixed 16-byte header (Service ID, Method ID, Length, Client ID, Session ID, Protocol Version, Interface Version, Message Type, Return Code). SOME/IP-SD provides runtime service discovery — ECUs announce their services and clients subscribe, without hardcoded IP:port mappings. It supports RPC (request/response), periodic notifications (events), and field (getter/setter) patterns. Raw UDP sockets require application-level framing, service location, and error handling, which SOME/IP standardises for AUTOSAR Adaptive interoperability.

---

**Q9. How would you configure Wireshark to decode SOME/IP traffic on a custom service port?**

**A:** Go to Edit → Preferences → Protocols → SOMEIP. Add the service port (e.g., 30501) to the list of SOME/IP UDP/TCP ports. For human-readable service/method names, provide a `someip_service_id.csv` file in the same directory as the ARXML service model. To decode SOME/IP-SD, also configure port 30490. Verify by capturing with filter `udp.port == 30501` and confirming Wireshark shows the SOME/IP header fields in the Packet Details pane.

---

**Q10. What is PLCA and how does it differ from CSMA/CD?**

**A:** PLCA (Physical Layer Collision Avoidance, part of 10BASE-T1S) is a token-rotation mechanism at the PHY layer. Node 0 issues a BEACON; each node takes a deterministic transmit opportunity in sequence. No collisions can occur because only one node transmits at a time. CSMA/CD (traditional Ethernet) detects collisions after they occur and retransmits with random backoff, making latency bounded only probabilistically. PLCA's deterministic cycle makes maximum latency predictable: N nodes × cycle time, enabling 10BASE-T1S to be used in time-sensitive applications where CAN's TDMA or CSMA with priority was previously required.

---

**Q11. What physical layer tests would you run to qualify a new 1000BASE-T1 cable assembly?**

**A:** (1) Insertion loss vs frequency — must meet IEEE 802.3bp channel model up to 600 MHz. (2) Return loss — minimum 16 dB across operating band. (3) Differential-to-common mode conversion (ANEXT, ADEXT) — EMC qualification per OPEN Alliance TC8. (4) TDR scan for impedance uniformity — expect 100 Ω ± 15%, no discontinuities. (5) Connector mating cycles — verify impedance does not degrade after 30 mate/demate cycles (automotive connector spec). (6) Temperature cycling test — insertion loss at −40°C and +125°C must stay within limits.

---

**Q12. Explain VLAN trunking and when you would use it in a vehicle network.**

**A:** A trunk port carries frames belonging to multiple VLANs simultaneously, each frame tagged with an 802.1Q header containing the VLAN ID. In a vehicle, trunk links are used on inter-switch links and zone ECU uplinks to the backbone switch. For example, a zone ECU aggregating ADAS (VLAN 10), body (VLAN 30), and diagnostics (VLAN 50) nodes sends all three VLANs tagged on its single uplink to the backbone switch. The backbone switch then routes each VLAN to the appropriate domain controller. Access ports (VLAN-unaware ECUs) connect as untagged — the switch adds/removes the tag transparently.

---

**Q13. What is the purpose of IEEE 802.1CB FRER in automotive Ethernet?**

**A:** Frame Replication and Elimination for Reliability (FRER) provides seamless redundancy for safety-critical streams. The sender replicates each frame and sends it over two disjoint paths. The receiver's sequence recovery function eliminates duplicate frames (keeping the first to arrive) and detects lost frames. If one path fails, traffic continues uninterrupted on the other path with zero recovery time — unlike RSTP which has 30–50 ms convergence. Used for: ADAS object list distribution to brake actuator ECU (functional safety requirement for no data loss), redundant DoIP gateway uplinks.

---

**Q14. How would you troubleshoot intermittent CRC errors on an automotive Ethernet link?**

**A:** CRC errors always indicate a physical or electromagnetic issue. Approach: (1) Check `ethtool -S` or switch counters to characterise rate and pattern (burst vs random). (2) Run VNA insertion loss — if cable length exceeds 15 m or IL > limit, shorten cable. (3) Inspect shield termination — floating shields are common in prototype harnesses; verify 360° termination at both ends. (4) Check for stub branches — even a 200 mm unterminated stub causes reflections. (5) Measure radiated emissions from nearby switching regulators — if correlated to power events, add shielding or reroute cable away from power converters. (6) Swap the PHY or connector if all other checks pass.

---

**Q15. An ADAS camera stream shows jitter of 500 µs, but the TSN GCL was designed for 100 µs. What would you investigate?**

**A:** 500 µs jitter on a TSN-scheduled stream despite a 100 µs GCL window suggests one of: (1) **gPTP synchronisation drift** — if the two switch clocks are misaligned by > 100 µs, GCLs open at different times; verify with PTP offset metrics. (2) **GCL offset misconfiguration** — the GCL on switch 2 may have incorrect base time, causing it to open/close out of phase with switch 1. (3) **Frame preemption not enabled** — a large lower-priority frame (1500 B = 12 µs at 1 Gbit/s) at the end of a GCL window is not interrupted; add 802.1Qbu preemption. (4) **Guard band too short** — switch is cutting off stream fills before scheduled window closes. (5) **Background traffic exceeding CBS credit** — check if credit-based shaper on Class A queue has insufficient credit allocation for the camera stream data rate.

---

*End of 01_automotive_ethernet_guide.md*
