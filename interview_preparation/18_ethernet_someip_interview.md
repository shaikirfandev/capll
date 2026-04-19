# Automotive Ethernet & SOME/IP Interview Q&A — 40 Questions
## DoIP | SOME/IP | PTP | TSN | Automotive Ethernet Testing

---

## Section 1: Automotive Ethernet Basics

**Q1: How does automotive Ethernet differ from standard Ethernet?**
| Feature | Standard Ethernet | Automotive Ethernet |
|---------|------------------|---------------------|
| Physical | RJ45, 2-4 pairs | Single UTP pair (100BASE-T1) |
| Standard | IEEE 802.3 | OPEN Alliance BroadR-Reach |
| Speed | 10M/100M/1G+ | 100Mbit/s (100BASE-T1), 1G (1000BASE-T1) |
| EMC | Office environment | Automotive grade |
| Connector | RJ45 | HSD/MATE-AX |
| Power | PoE optional | No PoE |

**Q2: What speeds are used in automotive Ethernet?**
- **100BASE-T1** (OPEN Alliance BroadR-Reach) — 100 Mbit/s over single pair, most common
- **1000BASE-T1** — 1 Gbit/s over single pair, used for cameras/radar data
- **10BASE-T1S** — 10 Mbit/s multi-drop (replaces CAN in some applications)
- **2.5GBASE-T1, 5GBASE-T1** — emerging for autonomous driving backbone

**Q3: What is the typical automotive Ethernet topology?**
```
[Cameras] ──→ ┐
[Radar]   ──→ ├─ [Zone ECU / Domain Controller] ──→ [Central Gateway]
[Lidar]   ──→ ┘         (1000BASE-T1)                     │
                                                   (switched Ethernet)
[Infotainment] ──→ [IVI ECU] ──→ [Central Gateway]
[Cluster]      ──→ [Cluster ECU]  │
                                  ↓
                         [OBD-II / DoIP diagnostic access]
```

---

## Section 2: DoIP (Diagnostics over IP)

**Q4: What is DoIP (ISO 13400)?**
> DoIP enables UDS (ISO 14229) diagnostic communication over Ethernet (UDP/TCP). Replaces K-Line and CAN-based diagnostics for modern vehicles with Ethernet backbone. Allows remote diagnostics, faster firmware updates, and simultaneous access to multiple ECUs.

**Q5: Describe the DoIP connection sequence.**
```
1. Tester discovery:
   Tester → UDP broadcast (port 13400): Vehicle Announcement Request
   Vehicle → UDP: Vehicle Announcement (VIN, EID, GID, logical address)

2. TCP connection:
   Tester → TCP connect to port 13400
   Tester → Routing Activation Request (source address, activation type)
   Gateway → Routing Activation Response (confirm)

3. UDS over DoIP:
   Tester → DiagnosticMessage(source=0x0E00, target=0x0010, UDS_request)
   ECU → DiagnosticMessageAck
   ECU → DiagnosticMessage(source=0x0010, target=0x0E00, UDS_response)
```

**Q6: What is the DoIP payload type field?**
| Payload Type | Hex | Description |
|--------------|-----|-------------|
| Generic DoIP header NACK | 0x0000 | Negative acknowledgment |
| Vehicle ID request | 0x0001 | Discovery request (UDP) |
| Vehicle announcement | 0x0004 | Vehicle response with VIN, addresses |
| Routing activation request | 0x0005 | Tester opens diagnostic channel |
| Routing activation response | 0x0006 | Gateway confirms channel |
| Alive check request | 0x0007 | Keep-alive ping |
| Alive check response | 0x0008 | Keep-alive pong |
| Diagnostic message | 0x8001 | UDS payload |
| Diagnostic message ACK | 0x8002 | Positive acknowledgment |
| Diagnostic message NACK | 0x8003 | Negative acknowledgment |

**Q7: How do you implement a DoIP client in Python?**
```python
import socket, struct

DOIP_PORT = 13400
DOIP_VERSION = 0x02
DOIP_ROUTING_ACTIVATION_REQ = 0x0005
DOIP_DIAG_MSG = 0x8001

def doip_header(payload_type: int, payload: bytes) -> bytes:
    return struct.pack('>BBHI', DOIP_VERSION, ~DOIP_VERSION & 0xFF,
                       payload_type, len(payload)) + payload

class DoIPClient:
    def __init__(self, host: str, source_addr: int = 0x0E00):
        self.sock = socket.create_connection((host, DOIP_PORT), timeout=5)
        self.source_addr = source_addr
        self._activate_routing()

    def _activate_routing(self):
        payload = struct.pack('>HHB', self.source_addr, 0x0000, 0x00)
        self.sock.send(doip_header(DOIP_ROUTING_ACTIVATION_REQ, payload))
        self.sock.recv(1024)  # Routing activation response

    def send_uds(self, target_addr: int, uds_data: bytes) -> bytes:
        payload = struct.pack('>HH', self.source_addr, target_addr) + uds_data
        self.sock.send(doip_header(DOIP_DIAG_MSG, payload))
        self.sock.recv(1024)  # ACK
        resp = self.sock.recv(4096)  # Actual response
        _, header_len = 8, 8
        return resp[header_len + 4:]  # Skip header + source/target addr

    def close(self):
        self.sock.close()

# Usage:
client = DoIPClient('192.168.1.10')
vin_response = client.send_uds(0x0010, bytes([0x22, 0xF1, 0x90]))
print(f"VIN: {vin_response[3:].decode()}")
client.close()
```

---

## Section 3: SOME/IP (Scalable service-Oriented MiddlewarE over IP)

**Q8: What is SOME/IP?**
> SOME/IP is the standardized automotive middleware protocol for service-oriented communication over Ethernet (AUTOSAR standard). It defines: **service discovery**, **method calls** (request/response), **events** (publish/subscribe), and **fields** (get/set with notification).

**Q9: Describe the SOME/IP message format.**
```
SOME/IP Header (16 bytes):
┌──────────┬──────────┬──────────┬──────────┐
│ Service  │ Method   │ Length   │ Client   │
│ ID (2B)  │ ID (2B)  │ (4B)     │ ID (2B)  │
├──────────┼──────────┼──────────┼──────────┤
│ Session  │ Proto Ver│ If. Ver  │ Msg Type │
│ ID (2B)  │ (1B)     │ (1B)     │ (1B)     │
├──────────┴──────────┴──────────┴──────────┤
│ Return Code (1B)                          │
└───────────────────────────────────────────┘
│ Payload (variable)                        │
```

**Q10: What are SOME/IP message types?**
| Message Type | Hex | Description |
|--------------|-----|-------------|
| REQUEST | 0x00 | Method call expecting response |
| REQUEST_NO_RETURN | 0x01 | Fire-and-forget method call |
| NOTIFICATION | 0x02 | Event publication |
| REQUEST_ACK | 0x40 | Acknowledgment (not used in UDP) |
| RESPONSE | 0x80 | Method response (success) |
| ERROR | 0x81 | Method response (error) |

**Q11: What is SOME/IP-SD (Service Discovery)?**
> SOME/IP-SD enables dynamic service discovery — ECUs announce which services they offer (OfferService) and clients subscribe (FindService, Subscribe). Uses UDP multicast on port 30490.
```
Server ECU → Multicast: OfferService(Service ID=0x1234, Instance=0x0001)
Client ECU → Unicast server: Subscribe(Eventgroup ID=0x0001)
Server ECU → Unicast client: SubscribeAck
Server ECU → Events (periodic notifications via SOME/IP NOTIFICATION)
```

---

## Section 4: Time Synchronization & TSN

**Q12: What is PTP (IEEE 1588) and why is it needed in automotive?**
> PTP (Precision Time Protocol) synchronizes clocks across all ECUs on the Ethernet network to sub-microsecond accuracy. Required for:
> - **Sensor fusion:** Camera + Radar timestamps must be aligned < 1ms
> - **Time-triggered communication:** Scheduled transmissions (TSN)
> - **Data recording:** Synchronized logs across ECUs

**Q13: What is TSN (Time-Sensitive Networking)?**
> TSN is a set of IEEE 802.1 standard extensions to Ethernet providing:
> - **802.1AS:** Time synchronization (gPTP — automotive profile of PTP)
> - **802.1Qbv:** Time-Aware Shaper — scheduled traffic gates for deterministic latency
> - **802.1Qbu:** Frame preemption — high-priority frames interrupt low-priority
> - **802.1CB:** Frame Replication and Elimination for Reliability (FRER)
>
> TSN enables Ethernet to carry real-time safety-critical data alongside best-effort data.

---

## Section 5: Testing Automotive Ethernet

**Q14: How do you test SOME/IP services?**
```python
import socket, struct, time

# Listen for SOME/IP-SD OfferService
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 30490))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
               struct.pack('4sL', socket.inet_aton('239.192.255.251'),
                           socket.INADDR_ANY))
data, addr = sock.recvfrom(1024)
print(f"SOME/IP-SD from {addr}: {data.hex()}")
```

**Q15: What tools are used for automotive Ethernet testing?**
| Tool | Vendor | Use |
|------|--------|-----|
| Wireshark + SOME/IP plugin | Open source | Protocol analysis |
| CANoe.Ethernet | Vector | Test automation |
| ComProbe | Frontline | Hardware capture |
| Ixia/Spirent | Keysight | Load/performance testing |
| BUSMASTER | Open source | Basic Ethernet monitoring |
| Tcpdump | Open source | Command-line capture |

**Q16: How do you verify DoIP routing activation in testing?**
```python
# Step 1: Send routing activation request
# Step 2: Verify response contains activation type 0x10 (default)
# Step 3: Check logical address matches expected ECU
# Step 4: Send test UDS request (ReadDataByIdentifier 0xF189 = SW version)
# Step 5: Verify positive response received within timeout
```

---

## Section 6: Quick Reference

**Q17:** SOME/IP default port? → **UDP/TCP 30490** for SOME/IP-SD, application ports are service-specific.

**Q18:** DoIP port? → **UDP/TCP 13400** (assigned by IANA).

**Q19:** Maximum SOME/IP payload over UDP? → Limited by UDP payload size, typically **1400 bytes** (accounting for Ethernet, IP, UDP headers). Larger payloads use SOME/IP-TP (segmentation).

**Q20:** What is VLAN in automotive Ethernet?
> IEEE 802.1Q VLAN tagging separates traffic into virtual networks on the same physical Ethernet infrastructure. Automotive domains (powertrain, ADAS, infotainment) use different VLANs for isolation and QoS prioritization via VLAN priority field (0–7, maps to TSN traffic classes).
