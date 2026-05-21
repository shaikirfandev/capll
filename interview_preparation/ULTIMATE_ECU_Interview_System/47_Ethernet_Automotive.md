# Automotive Ethernet Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Automotive Ethernet is replacing legacy bus systems (CAN/LIN/MOST) for high-bandwidth applications (ADAS cameras, infotainment, central gateway). Knowledge is essential for **Harman, Qualcomm Automotive, Continental, Aptiv, Visteon, and any domain controller or ADAS ECU role**. You must understand the physical layer differences (100BASE-T1, 1000BASE-T1), SOME/IP service-oriented communication, and AUTOSAR Adaptive Platform integration.

**Key areas:**
- Automotive Ethernet physical layer: 100BASE-T1 (BroadR-Reach), 1000BASE-T1
- OSI model applied to automotive Ethernet
- SOME/IP (Scalable service-Oriented MiddlewarE over IP)
- SOME/IP-SD (Service Discovery)
- IP addressing in vehicle networks (static vs DHCP, VLAN)
- DoIP (Diagnostics over IP) — ISO 13400
- Time synchronisation: gPTP (IEEE 802.1AS) for AVB/TSN
- AVB/TSN for real-time streaming (camera feeds, audio)
- Automotive Ethernet switch architecture (central gateway)
- AUTOSAR Adaptive Platform (ara::com, ara::diag)

---

## PHYSICAL LAYER

---

### Q1. How does automotive 100BASE-T1 differ from standard 100BASE-TX?

**Expert Answer:**

```
Comparison: Automotive vs Standard Ethernet Physical Layer

Feature              100BASE-TX (Standard)      100BASE-T1 (Automotive)
─────────────────────────────────────────────────────────────────────────
Standard             IEEE 802.3u                IEEE 802.3bw
Also known as        Fast Ethernet              BroadR-Reach
Introduced           1995                       2016

Physical cable       2 pairs of UTP cable       1 PAIR of twisted cable
Connectors           RJ-45 (large)              Smaller, automotive-grade
Cable weight         Heavy                      Lighter (critical for EV range)

Duplex               Half or Full duplex        Full duplex only
                                                (simultaneous TX + RX on 1 pair)

Speed                100 Mbps                   100 Mbps
Pair utilisation     2 pairs (1 TX, 1 RX)       1 pair (both TX and RX)

ESD protection       Standard                   Automotive-grade (±2 kV surge)
Operating temp       0°C to 70°C                -40°C to +125°C
EMC                  FCC Class B                CISPR 25 (automotive EMC)
Noise tolerance      Standard                   Higher (engine bay environment)
Maximum cable length 100 m                      15 m (standard), 40 m possible

Why 1 pair?
  Weight reduction: in a modern vehicle, ~50% of wiring harness weight
  With 100+ Ethernet links: 2-pair would add ~20 kg
  1-pair technology: echo cancellation DSP allows full duplex on single pair

1000BASE-T1 (Automotive Gigabit):
  IEEE 802.3bp
  1 Gbps over single pair
  Typical use: backbone links, ADAS sensor fusion, central gateway
  Cable: up to 40m for chassis, 15m for engine bay
  
2500BASE-T1 / 10GBASE-T1:
  Emerging for Level 3+ ADAS (LiDAR, multi-camera fusion)
  Standardised in IEEE 802.3ch (Multi-Gig)
```

---

## SOME/IP

---

### Q2. What is SOME/IP? Explain service discovery, method calls, and events.

**Expert Answer:**

```
SOME/IP — Scalable service-Oriented MiddlewarE over IP

SOME/IP is the application-layer protocol used in AUTOSAR Adaptive and
automotive Ethernet networks for service-oriented communication.
Defined by: AUTOSAR Foundation and PRS_SOMEIPProtocol

SOME/IP message format:
Byte 0-3:   Service ID (16 bit) + Method/Event ID (16 bit)
Byte 4-7:   Length (payload length in bytes, not including header)
Byte 8-11:  Client ID (16 bit) + Session ID (16 bit)
Byte 12:    Protocol Version (should be 0x01)
Byte 13:    Interface Version (service version)
Byte 14:    Message Type
            0x00 = REQUEST (client → server, expects response)
            0x01 = REQUEST_NO_RETURN (fire and forget)
            0x02 = NOTIFICATION (server → client, event)
            0x80 = RESPONSE (server → client, reply to REQUEST)
            0x81 = ERROR (server → client, error response)
Byte 15:    Return Code
            0x00 = E_OK
            0x01 = E_NOT_OK
            0x02 = E_UNKNOWN_SERVICE
            0x03 = E_UNKNOWN_METHOD

Communication patterns:

1. REQUEST / RESPONSE (like RPC / function call):
   Client sends:   REQUEST (ServiceID + MethodID + args)
   Server replies: RESPONSE (same SessionID + return values)
   Example: Client requests current speed → Server returns 58.8 km/h
   
2. FIRE AND FORGET (Request No Return):
   Client sends: REQUEST_NO_RETURN (command, no reply needed)
   Example: "Turn on AC compressor" command to HVAC ECU
   
3. EVENTS (Subscribe / Notify):
   Server sends NOTIFICATION to all subscribed clients (push model)
   Example: Speed sensor ECU notifies all subscribers every 100ms
   
4. FIELDS (Getter / Setter + Notifier):
   Combination: initial value via GET, updates via NOTIFICATION
   Example: Engine temperature field (read initial, receive updates)
```

**Code — SOME/IP client using raw socket (simplified):**
```c
/* Simplified SOME/IP REQUEST implementation */
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define SOMEIP_HEADER_SIZE  16U

typedef struct {
    uint16_t service_id;
    uint16_t method_id;
    uint32_t length;          /* Payload length (excluding header) */
    uint16_t client_id;
    uint16_t session_id;
    uint8_t  protocol_ver;    /* 0x01 */
    uint8_t  iface_ver;
    uint8_t  msg_type;
    uint8_t  return_code;
    uint8_t  payload[];
} __attribute__((packed)) SOMEIP_Header_t;

int someip_send_request(int sock, struct sockaddr_in *server,
                         uint16_t svc_id, uint16_t method_id,
                         const uint8_t *payload, uint16_t pay_len) {
    uint8_t buf[1500];
    SOMEIP_Header_t *hdr = (SOMEIP_Header_t *)buf;
    static uint16_t s_session_id = 1U;
    
    hdr->service_id   = htons(svc_id);
    hdr->method_id    = htons(method_id);
    hdr->length       = htonl((uint32_t)pay_len + 8U);  /* +8 for header bytes 8-15 */
    hdr->client_id    = htons(0x0001U);
    hdr->session_id   = htons(s_session_id++);
    hdr->protocol_ver = 0x01U;
    hdr->iface_ver    = 0x01U;
    hdr->msg_type     = 0x00U;  /* REQUEST */
    hdr->return_code  = 0x00U;  /* E_OK */
    
    if (payload && pay_len > 0U) {
        memcpy(buf + SOMEIP_HEADER_SIZE, payload, pay_len);
    }
    
    ssize_t sent = sendto(sock, buf, SOMEIP_HEADER_SIZE + pay_len, 0,
                          (struct sockaddr *)server, sizeof(*server));
    return (sent > 0) ? 0 : -1;
}
```

---

## DoIP (DIAGNOSTICS OVER IP)

---

### Q3. How does DoIP work? Compare it to CAN-based UDS.

**Expert Expert Answer:**

```
DoIP — Diagnostics over IP (ISO 13400)

WHY DoIP?
  CAN: 8 bytes/frame, 500kbps → firmware download = hours
  DoIP over 100BASE-T1: 1500 bytes/frame, 100Mbps → firmware download = minutes
  ADAS ECUs: large firmware (>100MB) → CAN would take 24+ hours
  DoIP: 15 minutes for 100MB firmware

DoIP Transport:
  Physical: 100BASE-T1 (automotive Ethernet)
  Network:  IPv4 (static addressing in vehicle)
  Transport: TCP (for UDS) or UDP (for VehicleIdentification)
  Port:      13400 (both TCP and UDP)

DoIP Entity types:
  DoIP Gateway: entry point (usually Central GW ECU, accessible via OBD-II LAN port)
  DoIP Node: ECU behind the gateway (ADAS ECU, IVI, etc.)

DoIP Session (TCP):
  1. Tester connects TCP to DoIP Gateway port 13400
  2. Send: Routing Activation Request (logical address = 0x0001)
  3. Receive: Routing Activation Response (success = 0x10)
  4. Now send UDS payloads inside DoIP headers
  5. DoIP gateway routes to target ECU (e.g., ADAS ECU at 0x0014)

DoIP header (8 bytes):
  Byte 0-1: Protocol version (0x02 0xFD = current version + ~version)
  Byte 2-3: Payload Type:
    0x0001 = Vehicle Identification Request
    0x0002 = Vehicle Identification Response
    0x0005 = Routing Activation Request
    0x0006 = Routing Activation Response
    0x8001 = Diagnostic Message (UDS payload)
    0x8002 = Diagnostic Message Positive ACK
    0x8003 = Diagnostic Message Negative ACK
  Byte 4-7: Payload Length

DoIP Diagnostic Message structure:
  DoIP Header (8 bytes)
  Source Address: 2 bytes (e.g., 0x0001 = tester)
  Target Address: 2 bytes (e.g., 0x0014 = ADAS ECU logical address)
  User Data: UDS request (e.g., 10 02 = enter programming session)

CAN UDS vs DoIP UDS:
  Feature          CAN (ISO-TP + UDS)    DoIP + UDS
  Max payload      4KB (CF limit)        64KB per message
  Speed            500kbps               100Mbps
  Flash 50MB       ~13 hours             ~5 minutes
  Setup            Physical CAN only     Network config required
  Tool support     CANoe, PEAK           CANoe, Wireshark, custom
  
Production setup (ADAS ECU flashing via DoIP):
  OBD-II connector has Ethernet port (some OEMs: Toyota, BMW)
  tester PC ← Ethernet → OBD-II port ← DoIP gateway → ADAS ECU
  Flash ADAS camera ECU in 8 minutes vs 20+ hours via CAN
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q4. SOME/IP service not discovered in vehicle. Debug steps.

**Expert Answer:**

"SOME/IP-SD (Service Discovery) failure is a common integration issue. Systematic debug:

**Step 1 — Network reachability:**
```bash
# From engineering PC on vehicle network (OBD-II LAN port):
ping 192.168.1.14  # Target ECU IP
# If ping fails: IP config, VLAN, or physical layer issue

# Check VLAN assignment:
ip link show
# Expected: eth0.10 (VLAN 10 for ADAS network)

# Check ARP:
arp -n | grep 192.168.1.14
# If no entry: ECU not responding to ARP → ECU not booted or IP mismatch
```

**Step 2 — Capture SOME/IP-SD multicast:**
```bash
# SOME/IP-SD uses multicast address 239.192.255.251 port 30490
tcpdump -i eth0 -n "udp port 30490" -w someip_sd.pcap

# Open in Wireshark → filter: someip-sd
# Should see:
#   OfferService (server advertising its services)
#   FindService (client looking for service)
#   SubscribeEventgroup (client subscribing to events)
#   SubscribeEventgroupAck (server acknowledging)
```

**Step 3 — Common root causes:**
```
Issue A: Server not sending OfferService
  Cause: Server ECU not yet in "service ready" state
  Check: ECU startup log — is SOME/IP stack initialised?
  Fix: Increase wait time for initial service discovery

Issue B: VLAN mismatch
  Server on VLAN 10, client on VLAN 20 → multicast doesn't cross VLAN boundary
  Fix: Central gateway must relay SOME/IP-SD between VLANs
  OR: Move both to same VLAN

Issue C: IP TTL too low
  Multicast TTL=1 doesn't cross routers
  UDP socket option: setsockopt(sock, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof(ttl))
  Automotive: TTL=64 for unicast, TTL=1 for in-vehicle multicast (expected)
  But if switch is routing between VLANs: TTL decremented → 0 → dropped

Issue D: Firewall / iptables blocking multicast
  Linux-based ECU: check iptables -L -n | grep MULTICAST
  Fix: iptables -A INPUT -p udp --dport 30490 -j ACCEPT

Issue E: SOME/IP config mismatch
  Service instance ID in server ≠ client configuration
  Check ARXML: ServiceInterface InstanceIdentifier must match
  Fix: Re-generate SOME/IP binding from same ARXML in both ECU builds
```

---

## CHEAT SHEET — Automotive Ethernet

```
Physical layer:
  100BASE-T1: 100 Mbps, 1 pair, BroadR-Reach, IEEE 802.3bw
  1000BASE-T1: 1 Gbps, 1 pair, IEEE 802.3bp
  RJ45 vs automotive connector: smaller, IP67, vibration-resistant

SOME/IP message types:
  0x00 = REQUEST (expects response)
  0x01 = REQUEST_NO_RETURN (fire and forget)
  0x02 = NOTIFICATION (event push)
  0x80 = RESPONSE
  0x81 = ERROR

SOME/IP-SD multicast:
  IP: 239.192.255.251
  Port: 30490
  Messages: OfferService, FindService, SubscribeEventgroup, ...Ack

DoIP:
  Standard: ISO 13400
  Port: 13400 (TCP + UDP)
  UDS wrapped in DoIP: logical addressing (source + target addr)
  Benefit: 100× faster than CAN for large firmware downloads

gPTP (Generalised PTP, IEEE 802.1AS):
  Time synchronisation across vehicle network
  Required for: AVB audio/video streaming, sensor fusion timestamps
  Accuracy: ±1 microsecond (grandmaster → slave synchronisation)
  AUTOSAR: StbM (Synchronised Time-Base Manager) interfaces gPTP

TSN (Time-Sensitive Networking):
  802.1Qbv: Time-Aware Shaper (deterministic latency for safety signals)
  802.1Qav: Credit-Based Shaper (AVB for audio/video)
  Purpose: guarantee < 2ms latency for ADAS sensor data

IP addressing typical:
  Vehicle subnet: 192.168.x.x or 169.254.x.x (link-local)
  DoIP gateway: 192.168.0.10
  ADAS domain: 192.168.1.0/24
  Infotainment: 192.168.2.0/24
  Diagnostic tester: 192.168.0.1 (OBD-II laptop)
```
