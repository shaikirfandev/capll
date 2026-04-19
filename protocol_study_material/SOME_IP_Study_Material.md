# SOME/IP (Scalable service-Oriented MiddlewarE over IP) Study Material
## AUTOSAR Standard for Service-Oriented Communication

---

## 1. What is SOME/IP?

**SOME/IP** (Scalable service-Oriented MiddlewarE over IP) is a **middleware protocol** developed by AUTOSAR for **service-oriented communication** in automotive Ethernet networks.

- Defines how automotive software components expose and consume **services** over Ethernet
- Enables **service discovery**, **method calls**, **event subscriptions**, and **field access**
- Used in modern vehicles for ADAS, infotainment, telematics, and domain/zone architectures
- Replaces signal-based CAN communication with flexible, scalable service interfaces

**Key documents:**
- AUTOSAR SOME/IP Protocol Spec (AUTOSAR_PRS_SOMEIPProtocol)
- AUTOSAR SOME/IP Service Discovery Spec (AUTOSAR_PRS_SOMEIPServiceDiscovery)

---

## 2. SOME/IP vs. Classic Signal-Based Communication

| Aspect | CAN Signal-Based | SOME/IP |
|---|---|---|
| Paradigm | Periodic signal broadcast | Service-oriented (publish/subscribe + RPC) |
| Network | CAN, LIN | Ethernet (100BASE-T1, 1000BASE-T1) |
| Bandwidth | 500 kbps – 8 Mbps | 100 Mbps – 10 Gbps |
| Discoverability | Static DBC configuration | Dynamic service discovery (SOME/IP-SD) |
| Data types | Fixed-length signals | Flexible serialized data structures |
| Interface | Consumer reads bus | Client calls service / subscribes to events |
| Coupling | Tight (all ECUs see all signals) | Loose (client subscribes to specific services) |

---

## 3. SOME/IP Architecture

```
     [Service Provider ECU]                [Service Consumer ECU]
     +----------------------+              +----------------------+
     | Service Interface    |              | Client Proxy         |
     | - Methods            |              | - Method Calls       |
     | - Events             |◄─── Eth ───►| - Event Subscriptions|
     | - Fields             |              | - Field Access       |
     +----------------------+              +----------------------+
             |                                        |
     +-------+--------+                    +----------+--------+
     | SOME/IP Runtime|                    | SOME/IP Runtime   |
     | SOME/IP-SD     |                    | SOME/IP-SD        |
     +----------------+                    +-------------------+
             |                                        |
     +-------+--------+                    +----------+--------+
     |   UDP / TCP     |                    |   UDP / TCP       |
     |   IP            |                    |   IP              |
     |   Ethernet      |                    |   Ethernet        |
     +-----------------+                    +-------------------+
```

---

## 4. SOME/IP Communication Patterns

### 4.1 Request/Response (Remote Procedure Call)
Client sends a request → Server processes → Server sends response.
- Synchronous or asynchronous
- Uses **Method ID** to identify the called method

### 4.2 Fire & Forget
Client sends a request, no response expected.
- One-way method call
- Lower overhead

### 4.3 Event Notification (Publish/Subscribe)
Server sends event data to subscribed clients when data changes or periodically.
- Clients subscribe via **SOME/IP-SD**
- Events have an **Event ID**

### 4.4 Field (Getter / Setter / Notifier)
A **field** combines:
- **Getter**: Client requests current field value
- **Setter**: Client updates field value
- **Notifier**: Server sends update when field changes (like event)

---

## 5. SOME/IP Header Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Service ID          |           Method ID           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Length                                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Client ID           |           Session ID          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Protocol Ver  | Interface Ver |  Msg Type     |  Return Code  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Payload                               |
|                         ...                                   |
```

**Total header size: 16 bytes**

| Field | Size | Description |
|---|---|---|
| Service ID | 2 bytes | Unique identifier for the service |
| Method ID | 2 bytes | Identifies the method/event/field (0x8000+ = events) |
| Length | 4 bytes | Length of remaining bytes (from Client ID onwards) |
| Client ID | 2 bytes | Unique identifier of the requesting client instance |
| Session ID | 2 bytes | Used to correlate requests and responses |
| Protocol Version | 1 byte | Currently 0x01 |
| Interface Version | 1 byte | Major version of service interface |
| Message Type | 1 byte | Type of message (see below) |
| Return Code | 1 byte | 0x00=OK, error codes otherwise |

### Message Types
| Value | Type | Description |
|---|---|---|
| 0x00 | REQUEST | Client method call expecting response |
| 0x01 | REQUEST_NO_RETURN | Fire & forget |
| 0x02 | NOTIFICATION | Event or field notifier |
| 0x80 | RESPONSE | Server response to REQUEST |
| 0x81 | ERROR | Error response |

### Return Codes
| Value | Meaning |
|---|---|
| 0x00 | E_OK |
| 0x01 | E_NOT_OK |
| 0x02 | E_UNKNOWN_SERVICE |
| 0x03 | E_UNKNOWN_METHOD |
| 0x04 | E_NOT_READY |
| 0x05 | E_NOT_REACHABLE |
| 0x06 | E_TIMEOUT |
| 0x07 | E_WRONG_PROTOCOL_VERSION |
| 0x08 | E_WRONG_INTERFACE_VERSION |
| 0x09 | E_MALFORMED_MESSAGE |

---

## 6. SOME/IP-SD (Service Discovery)

**SOME/IP-SD** is the mechanism by which services **announce their availability** and clients **find and subscribe to services**.

- Runs over **UDP multicast** (typically 239.x.x.x) or unicast
- Default port: **30490 (UDP)**

### SD Message Entry Types
| Type | Description |
|---|---|
| **FindService** | Consumer searching for a provider |
| **OfferService** | Provider announcing service availability |
| **StopOfferService** | Provider stopping service |
| **SubscribeEventgroup** | Consumer subscribing to an event group |
| **SubscribeEventgroupAck** | Provider acknowledging the subscription |
| **SubscribeEventgroupNAck** | Provider rejecting the subscription |
| **StopSubscribeEventgroup** | Consumer unsubscribing |

### Service Discovery Flow
```
Consumer                             Provider
    |                                    |
    |-- FindService (multicast) -------> |
    |                                    |
    |<-- OfferService ------------------|
    |                                    |
    |-- SubscribeEventgroup -----------> |
    |<-- SubscribeEventgroupAck --------|
    |                                    |
    |<== Event Notifications ============|  (periodic or on change)
    |                                    |
    |-- StopSubscribeEventgroup -------> |
```

### SD Phases
1. **Initial Wait Phase**: Random delay before first offer/find
2. **Repetition Phase**: Multiple retransmissions, increasing intervals
3. **Main Phase**: Steady-state periodic announcements

---

## 7. SOME/IP Serialization

Data is **serialized** (marshalled) before being placed in the payload:

| Type | Serialization |
|---|---|
| `uint8` | 1 byte, big-endian |
| `uint16` | 2 bytes, big-endian |
| `uint32` | 4 bytes, big-endian |
| `float32` | 4 bytes, IEEE 754 |
| `string` | Length-prefixed UTF-8 |
| `struct` | Members in order, no padding (unless configured) |
| `array` | Length-prefixed sequence of elements |
| `optional` | Tag-Length-Value (TLV) encoding (SOME/IP 2.0+) |

---

## 8. SOME/IP Transport Binding

| Scenario | Protocol |
|---|---|
| Events, fire-and-forget | **UDP** (low latency, no guaranteed delivery) |
| Request/Response, critical | **TCP** (reliable, ordered) |
| Large payloads (> 1400 bytes) | **TCP** (avoids IP fragmentation) |
| Multicast events | **UDP multicast** |

---

## 9. SOME/IP vs. DDS vs. MQTT

| Feature | SOME/IP | DDS | MQTT |
|---|---|---|---|
| Origin | Automotive (AUTOSAR) | Defense / Industrial | IoT |
| Discovery | SOME/IP-SD | RTPS | Broker-based |
| QoS | Basic | Rich QoS policies | Basic (0,1,2) |
| Middleware | None (direct IP) | RTPS | Broker required |
| Serialization | Custom / AUTOSAR | CDR | Flexible (JSON etc.) |
| In-vehicle use | Very common (AUTOSAR) | Growing (SOAFEE) | Rare |

---

## 10. SOME/IP in AUTOSAR Adaptive Platform

In **AUTOSAR Adaptive** (AP), SOME/IP is the primary inter-ECU communication mechanism:

```
Application Layer
      |
[ara::com API] ← Developer uses this
      |
[Communication Management (CM)]
      |
[SOME/IP Binding] ← Protocol binding
      |
[Network / Ethernet Driver]
```

- `ara::com` provides language-level service proxy/skeleton concepts
- CM handles SOME/IP serialization, SD, and transport automatically
- Developers work with typed interfaces, not raw bytes

---

## 11. SOME/IP Test Scenarios

### Scenario 1: Service Discovery Verification
**Test**: Start provider ECU. Check consumer receives `OfferService` within 1 second.
**Pass criteria**: OfferService captured on Wireshark, Service ID and Instance ID match spec.

### Scenario 2: Method Call Round-Trip Time
**Test**: Client sends REQUEST, measures time to RESPONSE.
**Pass criteria**: RTT < 5 ms for local Ethernet network.

### Scenario 3: Event Rate Verification
**Test**: Subscribe to a 100 Hz event. Measure actual event rate over 10 seconds.
**Pass criteria**: Rate between 95–105 Hz, no lost events.

### Scenario 4: Error Handling – Unknown Method
**Test**: Send REQUEST with invalid Method ID to a running service.
**Pass criteria**: ERROR response with return code `0x03` (E_UNKNOWN_METHOD).

### Scenario 5: TCP Session Recovery
**Test**: Drop TCP connection mid-session, re-establish.
**Pass criteria**: Service re-subscribes and communication resumes within 2 seconds.

---

## 12. Wireshark for SOME/IP

Wireshark natively decodes SOME/IP (plugin: `SOME/IP`):

1. Capture on Ethernet/DoIP gateway
2. Filter: `someip` or `udp.port == 30490` for SD
3. Verify:
   - Service ID, Method ID decode correctly
   - SD offer/subscribe messages present
   - Session IDs increment per client
   - Return codes = 0x00 (E_OK)

**Command-line capture:**
```bash
tshark -i eth0 -Y "someip" -T fields \
  -e someip.serviceid -e someip.methodid \
  -e someip.msgtype -e someip.returncode
```

---

## 13. Common Interview Questions

**Q1: What is SOME/IP and what problem does it solve?**
> SOME/IP is an AUTOSAR middleware protocol for service-oriented communication over Ethernet. It solves the scalability and flexibility limitations of CAN signal-based communication by providing dynamic service discovery, method calls, and event subscriptions.

**Q2: Explain SOME/IP-SD and its phases.**
> SOME/IP-SD enables services to announce themselves and clients to find/subscribe to them. It has three phases: Initial Wait (random delay to avoid storm), Repetition (multiple retries with growing intervals), and Main Phase (steady periodic announcements).

**Q3: What is the difference between a Method, Event, and Field in SOME/IP?**
> A Method is a callable function (request/response or fire-and-forget). An Event is data the server pushes to subscribed clients when triggered. A Field combines getter, setter, and notifier — it represents a persistent data element accessible and updatable by clients.

**Q4: When would you use TCP vs. UDP for SOME/IP?**
> UDP for low-latency events and fire-and-forget. TCP for Request/Response pairs requiring reliable delivery and for large payloads exceeding UDP's safe size (~1400 bytes) to avoid fragmentation.

**Q5: What are Event Groups in SOME/IP-SD?**
> Event Groups allow bundling multiple events into a single subscription unit. A client subscribes to an Event Group to receive all events within it, reducing subscription overhead.

**Q6: What is the SOME/IP default port?**
> SOME/IP-SD uses UDP port **30490**. Individual service ports are configured per service instance.

**Q7: How is SOME/IP used in AUTOSAR Adaptive?**
> In AUTOSAR Adaptive Platform, `ara::com` provides the application API. The Communication Management (CM) module underneath uses SOME/IP as the binding to serialize data, handle service discovery via SOME/IP-SD, and route messages over Ethernet — completely transparent to the application developer.
