# 25 — DoIP and UDS over Ethernet

> **Standard:** ISO 13400 (DoIP), ISO 14229 (UDS)  
> **Use case:** Workshop diagnostics, end-of-line programming, OTA, remote diagnostics

---

## 25.1 DoIP vs CAN-based UDS

| Attribute         | UDS over CAN (ISO-TP)         | UDS over DoIP (ISO 13400)     |
|-------------------|-------------------------------|-------------------------------|
| Transport         | ISO-TP (ISO 15765-2)          | TCP/UDP over Ethernet         |
| Bandwidth         | ~7 bytes/frame @ 500kbps      | 1400 bytes/packet @ 100Mbps   |
| Max message size  | 4095 bytes (ISO-TP SF/FC)     | 64KB+ (TCP stream)            |
| Use case          | ECU diagnostics, OBD-II       | OTA flash, domain controller  |
| Port              | CAN ID (physical addressing)  | TCP port 13400                |
| Authentication    | Seed/key (SecurityAccess)     | TLS 1.3 + seed/key            |
| OTA speed         | ~1 KB/s (CAN-limited)         | ~10 MB/s (Ethernet)           |

---

## 25.2 DoIP Protocol Details

### Network Discovery — UDP

```
DoIP UDP Announcement (multicast on 224.0.0.2:13400):
  VehicleIdentificationRequest → broadcast by tester
  VehicleIdentificationResponse ← from each DoIP-capable ECU:
    VIN (17 chars), Logical Address (16-bit), GID (Group ID)

Ports:
  UDP 13400 → vehicle announcement, entity identification
  TCP 13400 → diagnostic session (data exchange)
```

### DoIP Header

```
DoIP Generic Header (8 bytes):
  Byte 0-1: Protocol Version (0x0002 = ISO 13400-2:2019)
  Byte 2-3: Payload Type
  Byte 4-7: Payload Length (32-bit)

Payload Types:
  0x0001  VehicleIdentificationRequest
  0x0004  VehicleIdentificationResponse
  0x0005  RoutingActivationRequest
  0x0006  RoutingActivationResponse
  0x8001  DiagnosticMessage (UDS)
  0x8002  DiagnosticMessagePositiveAck
  0x8003  DiagnosticMessageNegativeAck
```

### Routing Activation (TCP Session Setup)

```
Tester                        Gateway ECU
  |--RoutingActivationRequest -->|
  |   SourceAddress=0x0E00       |
  |   ActivationType=0x00        |
  |<-RoutingActivationResponse---|
  |   Code=0x10 (success)        |
  |                              |
  |--DiagnosticMessage---------->| 
  |   TargetAddress=0x0015 (ECU) |
  |   UDS: 10 03 (ExtendedSession)|
  |<-DiagnosticMessage-----------|
  |   UDS: 50 03 00 19 01 F4     |
```

---

## 25.3 UDS over DoIP — SecurityAccess

```
Tester                        ECU (target)
  |--10 02 (ProgrammingSession)->|
  |<-50 02 ----------------------|
  |--27 01 (RequestSeed)-------->|
  |<-67 01 [seed4bytes]----------|
  |                              |
  Compute: key = F(seed, secretKey)
  |--27 02 [key4bytes]---------->|
  |<-67 02 (access granted)------|
  |--34 ... (RequestDownload)--->|
  |<-74 ... (download ok)--------|
  |--36 [data block]------------>| repeated for all blocks
  |<-76 ... (ack)----------------|
  |--37 (RequestTransferExit)--->|
  |<-77 -------------------------|
  |--31 01 FF 01 (validateApp)-->|
  |<-71 01 FF 01 01 -------------|
  |--11 01 (ECUReset)----------->|
```

---

## 25.4 AUTOSAR DCM DoIP Configuration (ARXML sketch)

```xml
<DCM-CONFIG>
  <TRANSPORT-PROTOCOL-CONFIGURATION>
    <TRANSPORT-PROTOCOL>DOIP</TRANSPORT-PROTOCOL>
    <DOIP-CONFIG>
      <IP-ADDRESS>192.168.0.10</IP-ADDRESS>
      <UDP-PORT>13400</UDP-PORT>
      <TCP-PORT>13400</TCP-PORT>
      <LOGICAL-ADDRESS>0x0015</LOGICAL-ADDRESS>
    </DOIP-CONFIG>
  </TRANSPORT-PROTOCOL-CONFIGURATION>
  
  <SESSION-CONTROL>
    <DCM-DSP-SESSION id="DEFAULT_SESSION">0x01</DCM-DSP-SESSION>
    <DCM-DSP-SESSION id="EXTENDED_SESSION">0x03</DCM-DSP-SESSION>
    <DCM-DSP-SESSION id="PROGRAMMING_SESSION">0x02</DCM-DSP-SESSION>
  </SESSION-CONTROL>

  <SECURITY-ACCESS>
    <DCM-DSP-SECURITY-ROW>
      <ACCESS-LEVEL>0x01</ACCESS-LEVEL>  <!-- Request seed -->
      <SEED-SIZE>4</SEED-SIZE>
      <KEY-SIZE>4</KEY-SIZE>
      <GET-SEED-FNC>Dcm_GetSeedForLevel1</GET-SEED-FNC>
      <COMPARE-KEY-FNC>Dcm_CompareKeyForLevel1</COMPARE-KEY-FNC>
    </DCM-DSP-SECURITY-ROW>
  </SECURITY-ACCESS>
</DCM-CONFIG>
```

---

## 25.5 TLS for DoIP Security

```
ISO 13400-3 (DoIP over TLS):
  - TLS 1.3 mandatory for OEM over-the-air diagnostics
  - Certificate-based authentication (OEM Root CA → vehicle certificate)
  - Forward secrecy (TLS 1.3 ephemeral keys)
  
TLS handshake adds ~50ms to session setup (acceptable for OTA, not for workshop)
Workshop use: TLS optional (trusted physical connection assumed)

Common implementation: openssl in AUTOSAR Adaptive crypto stack
  ara::crypto TLS provider wraps openssl or mbedTLS
```

---

## 25.6 Interview Questions

**L1:**
1. What is DoIP and what problem does it solve vs CAN-based UDS?
2. What port does DoIP use?
3. What is the purpose of routing activation in DoIP?

**L2:**
4. Walk me through the DoIP session setup sequence.
5. How does SecurityAccess work in UDS, and what is the seed/key algorithm?
6. What is the difference between physical and functional addressing in UDS?

**L3:**
7. Design the DoIP architecture for a domain controller that has 5 downstream ECUs.
8. How would you implement TLS mutual authentication for OTA diagnostics in AUTOSAR Adaptive?
9. What is the DoIP gateway's role when a workshop tester connects to a zonal ECU via a domain controller?
10. How would you test DoIP connectivity in a HIL simulation environment?
