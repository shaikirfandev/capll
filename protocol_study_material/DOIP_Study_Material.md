# DoIP (Diagnostics over Internet Protocol) Study Material
## ISO 13400 | Automotive Ethernet Diagnostics

---

## 1. What is DoIP?

**DoIP** (Diagnostics over Internet Protocol) is a communication protocol defined in **ISO 13400** that enables diagnostic communication over **Ethernet-based vehicle networks**.

- Replaces or supplements classic CAN-based diagnostics (e.g., ISO 15765 CAN TP)
- Works on top of **TCP/IP** and **UDP/IP**
- Enables **remote diagnostics**, **over-the-air (OTA) updates**, and **high-bandwidth ECU flashing**
- Standardized entry point: **DoIP Edge Node** (typically the vehicle's Ethernet gateway)

---

## 2. Why DoIP? (vs. CAN UDS)

| Feature                  | CAN UDS (ISO 15765)         | DoIP (ISO 13400)               |
|--------------------------|-----------------------------|--------------------------------|
| Bandwidth                | 500 kbps (CAN), 8 Mbps (CAN FD) | 100 Mbps / 1 Gbps (Ethernet) |
| Flash speed              | Slow (minutes)              | Fast (seconds)                 |
| Remote diagnostics       | Not native                  | Native (TCP/IP)                |
| Physical media           | CAN bus                     | Ethernet (DoIP over TCP/UDP)   |
| Transport layer          | ISO 15765-2 (CAN TP)        | TCP/UDP (standard IP stack)    |
| Addressing               | CAN IDs                     | Logical Address + IP Address   |
| OTA updates              | Not suitable                | Designed for OTA               |

---

## 3. DoIP Architecture

```
[Tester / Diagnostic Tool]
         |
    [Ethernet Switch]
         |
   [DoIP Edge Node / Gateway]  <-- Vehicle Entry Point
         |
    [Internal Bus (CAN/LIN/FlexRay)]
         |
    [ECUs / Nodes]
```

**Key components:**
- **DoIP Entity**: Any ECU that implements DoIP (Edge nodes, internal ECUs)
- **DoIP Tester**: External diagnostic device (PC, off-board tester)
- **DoIP Gateway / Edge Node**: Bridges Ethernet and internal vehicle buses
- **Activation Line**: Physical wire used for vehicle wake-up during diagnostics

---

## 4. DoIP Protocol Stack

```
+----------------------------+
|   UDS (ISO 14229)          |  ← Diagnostic application layer
+----------------------------+
|   DoIP (ISO 13400)         |  ← Diagnostic routing layer
+----------------------------+
|   TCP / UDP                |  ← Transport (TCP for reliable, UDP for discovery)
+----------------------------+
|   IP (IPv4 / IPv6)         |
+----------------------------+
|   Ethernet (IEEE 802.3)    |
+----------------------------+
```

- **UDP port 13400**: Vehicle discovery and announcement
- **TCP port 13400**: Diagnostic message routing

---

## 5. DoIP Message Types

### 5.1 Vehicle Discovery (UDP)
| Message Type | Value  | Description |
|---|---|---|
| Vehicle Identification Request | 0x0001 | Tester broadcasts to discover vehicles |
| Vehicle Identification Response | 0x0004 | Vehicle responds with VIN + logical address |
| Vehicle Announcement | 0x0004 | Vehicle announces itself on network join |

### 5.2 Connection Handling (TCP)
| Message Type | Value  | Description |
|---|---|---|
| Routing Activation Request | 0x0005 | Tester establishes a diagnostic channel |
| Routing Activation Response | 0x0006 | Vehicle confirms routing activation |
| Alive Check Request | 0x0007 | Keep-alive ping |
| Alive Check Response | 0x0008 | Keep-alive response |

### 5.3 Diagnostic Messaging (TCP)
| Message Type | Value  | Description |
|---|---|---|
| Diagnostic Message | 0x8001 | UDS payload forwarded to ECU |
| Diagnostic Message Positive ACK | 0x8002 | ECU received and processing |
| Diagnostic Message Negative ACK | 0x8003 | Routing error (invalid address, etc.) |

---

## 6. DoIP Frame Structure

### Generic DoIP Header (8 bytes)
```
+--------+--------+--------+--------+--------+--------+--------+--------+
|Version | ~Ver   |   Payload Type  |        Payload Length             |
| 1 byte | 1 byte |    2 bytes      |            4 bytes                |
+--------+--------+-----------------+------------------------------------+
                                    |   Payload (variable length)       |
```

- **Version**: DoIP protocol version (0x02 for ISO 13400-2:2012, 0x03 for 2019)
- **~Version**: Bitwise inverse of version (checksum)
- **Payload Type**: Message type identifier
- **Payload Length**: Length of data following the header

### Diagnostic Message Payload
```
+------------------+------------------+------------------------+
| Source Address   | Target Address   | User Data (UDS)        |
|   2 bytes        |   2 bytes        |   variable             |
+------------------+------------------+------------------------+
```

---

## 7. DoIP Connection Flow (Step-by-Step)

```
Tester                                  DoIP Gateway/ECU
  |                                          |
  |--- UDP Broadcast (VehicleIdReq) -------> |
  |<-- UDP (VehicleIdResponse + VIN) --------|
  |                                          |
  |--- TCP Connect (port 13400) -----------> |
  |--- RoutingActivationRequest -----------> |
  |<-- RoutingActivationResponse ------------|
  |                                          |
  |--- DiagnosticMessage (UDS 0x10 03) ----> |
  |<-- DiagnosticMessage PositiveACK --------|
  |<-- DiagnosticMessage (UDS 0x50 03) ------|
  |                                          |
  |--- (more UDS requests) ----------------> |
  |                                          |
  |--- TCP Close -------------------------> |
```

---

## 8. Routing Activation

Routing activation establishes a **logical channel** between tester and target ECU.

**Request payload:**
```
Source Address (2 bytes) | Activation Type (1 byte) | Reserved (4 bytes)
```

**Activation Types:**
- `0x00` = Default
- `0x01` = WWH-OBD
- `0xE0–0xFE` = OEM-specific

**Response codes:**
| Code | Meaning |
|------|---------|
| 0x00 | Denied – unknown source address |
| 0x06 | Routing activated (success) |
| 0x07 | Routing activated, confirmation required |
| 0x10 | Denied – already registered |

---

## 9. Logical Addressing

| Address Range | Usage |
|---|---|
| 0x0001–0x0DFF | Individual ECU logical addresses |
| 0x0E00–0x0EFF | Functional group addresses |
| 0x0EFF | All DoIP entities (broadcast) |
| 0xE000–0xE3FF | Tester addresses |
| 0xF000–0xFFFF | OEM/Supplier reserved |

---

## 10. DoIP in CANoe / CAPL

### CAPL Example: Send UDS via DoIP
```c
// Using CANoe DoIP access (via CAPL IL / Diagnostic Layer)
diagnosticsRequest req;

on start
{
  DiagSetTarget("Gateway"); // target ECU name in CANoe config
  
  req = DiagCreateRequest(0x10);  // DiagnosticSessionControl
  DiagSetPrimitive(req, "Id", 0x03); // extendedSession
  DiagSendRequest(req);
}

on diagResponse req
{
  if (DiagGetLastError() == 0)
    write("Session control positive response received");
  else
    write("Negative response: 0x%02X", DiagGetLastError());
}
```

---

## 11. Vehicle Identification Response Fields

| Field | Size | Description |
|---|---|---|
| VIN | 17 bytes | Vehicle Identification Number (ASCII) |
| Logical Address | 2 bytes | DoIP entity logical address |
| EID | 6 bytes | Entity Identification (MAC address) |
| GID | 6 bytes | Group Identification |
| Further Action | 1 byte | 0x00=no further action, 0x10=central security |

---

## 12. Common Interview Questions

**Q1: What transport protocols does DoIP use and why?**
> UDP for discovery (connectionless, broadcast-friendly) and TCP for diagnostic message routing (reliable, ordered delivery ensures UDS integrity).

**Q2: What is the role of the DoIP Edge Node?**
> It is the vehicle's Ethernet gateway that translates DoIP messages from the external tester into the vehicle's internal bus protocol (CAN/LIN/FlexRay) and routes UDS requests to the correct ECU.

**Q3: What is Routing Activation and why is it needed?**
> Routing activation authenticates the tester, assigns a source address, and opens a logical channel before any diagnostic messages flow. Without it, the gateway rejects all diagnostic requests.

**Q4: How does DoIP handle network discovery?**
> The tester broadcasts a Vehicle Identification Request on UDP port 13400. Each DoIP-capable entity on the network responds with its VIN, logical address, and EID.

**Q5: What is the difference between DoIP and UDS?**
> UDS (ISO 14229) is the *application-layer* diagnostic protocol (defines services like 0x22, 0x27). DoIP (ISO 13400) is the *transport/routing* mechanism that carries UDS payloads over Ethernet. DoIP is the "how to deliver" and UDS is the "what to request."

**Q6: What port does DoIP use?**
> Both UDP and TCP use port **13400**.

**Q7: Describe the typical DoIP diagnostics sequence.**
> 1. Tester sends UDP Vehicle Id Request (broadcast)
> 2. Vehicle responds with VIN + logical address
> 3. Tester opens TCP connection to vehicle on port 13400
> 4. Tester sends Routing Activation Request
> 5. Vehicle confirms Routing Activation
> 6. DoIP Diagnostic Messages (carrying UDS) flow over TCP
> 7. TCP connection closed after session ends

---

## 13. Test Scenarios for DoIP

### Scenario 1: Vehicle Discovery Failure
**Setup**: Tester on same subnet, vehicle powered.
**Test**: Send Vehicle Identification Request, expect response within 500ms.
**Pass criteria**: Response contains valid VIN and logical address.

### Scenario 2: Routing Activation Rejection
**Test**: Use invalid source address in Routing Activation Request.
**Pass criteria**: Gateway returns response code 0x00 (denied).

### Scenario 3: High-bandwidth ECU Flash
**Test**: Flash a large firmware image (e.g., 50MB) via DoIP UDS 0x34/0x36/0x37.
**Measure**: Flash time, compare to CAN-based baseline.
**Pass criteria**: Flash completes without errors, Ethernet utilization < 80%.

### Scenario 4: Alive Check Handling
**Test**: Establish TCP connection, wait without sending for 5 seconds.
**Expected**: Gateway sends Alive Check Request; tester must respond or connection closes.

---

## 14. Key Standards References

| Standard | Description |
|---|---|
| ISO 13400-1 | DoIP – General information and use case definition |
| ISO 13400-2 | DoIP – Transport protocol and network layer services |
| ISO 13400-3 | DoIP – Wired vehicle interface based on IEEE 802.3 |
| ISO 13400-4 | DoIP – Ethernet-based high-speed data link connector |
| ISO 14229 | UDS – Unified Diagnostic Services |
| IEEE 802.3 | Ethernet standard |
