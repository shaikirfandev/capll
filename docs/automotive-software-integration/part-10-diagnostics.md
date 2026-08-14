# Part 10 — Diagnostics Integration

---

## 10.1 Overview

Automotive diagnostics allow external tools (testers, service tools, cloud backends) to:
- Read fault codes (DTCs)
- Read and write ECU parameters
- Execute routines (e.g., actuator tests)
- Flash new firmware
- Monitor live data

Key standards:
- **UDS (ISO 14229)** — Unified Diagnostic Services
- **OBD (ISO 15031 / SAE J1979)** — On-Board Diagnostics (emissions)
- **DoIP (ISO 13400)** — Diagnostics over IP

---

## 10.2 UDS — Unified Diagnostic Services (ISO 14229)

### Diagnostic Sessions

| Session | Value | Purpose |
|---|---|---|
| Default Session | 0x01 | Normal vehicle operation, limited services |
| Programming Session | 0x02 | ECU flashing |
| Extended Diagnostic Session | 0x03 | Full diagnostics, actuator tests |
| Safety System Diagnostic | 0x04 | Safety-related diagnostics |

### Key UDS Services

| Service | SID | Purpose |
|---|---|---|
| DiagnosticSessionControl | 0x10 | Switch session |
| ECUReset | 0x11 | Reset ECU (hard/soft/key off) |
| ClearDiagnosticInformation | 0x14 | Clear DTCs |
| ReadDTCInformation | 0x19 | Read DTCs (by status, type, etc.) |
| ReadDataByIdentifier | 0x22 | Read ECU data (DID) |
| ReadMemoryByAddress | 0x23 | Read raw memory |
| SecurityAccess | 0x27 | Seed/key authentication |
| CommunicationControl | 0x28 | Enable/disable network communication |
| WriteDataByIdentifier | 0x2E | Write ECU data (DID) |
| IOControlByIdentifier | 0x2F | Control ECU I/O (actuator test) |
| RoutineControl | 0x31 | Start/stop/request results of routines |
| RequestDownload | 0x34 | Start flash download |
| TransferData | 0x36 | Transfer data blocks |
| RequestTransferExit | 0x37 | End transfer |
| TesterPresent | 0x3E | Keep session alive |
| ControlDTCSetting | 0x85 | Enable/disable DTC setting |

---

## 10.3 DTC (Diagnostic Trouble Code)

A DTC is a fault code stored in an ECU's non-volatile memory when a fault is detected.

### DTC Structure

```
DTC = 3 bytes:
  Byte 1: High byte (system: P=powertrain, B=body, C=chassis, U=network)
  Byte 2: Middle byte
  Byte 3: Low byte (failure type)

Example: P0101 = Mass Air Flow Sensor Performance
```

### DTC Status Byte

```
Bit 7: warningIndicatorRequested
Bit 6: testFailedSinceLastClear
Bit 5: testNotCompletedSinceLastClear
Bit 4: confirmedDTC
Bit 3: pendingDTC
Bit 2: storedDTC (from previous drive cycle)
Bit 1: testFailed
Bit 0: testCompletedThisCycle
```

### DTC Management (Dem Module in AUTOSAR)

```
Application calls: Dem_ReportErrorStatus(DEM_EVENT_ID_SENSOR_FAILURE, DEM_EVENT_STATUS_FAILED)
↓
Dem module: increment failure counter
When counter ≥ threshold: set DTC status to "pending"
After confirmation cycle: set "confirmed"
Dem stores in NvM
DCM responds to ReadDTCInformation (0x19) with DTC list
```

---

## 10.4 Diagnostic Flow

```
+----------+    CAN TP (ISO 15765) or DoIP     +---------+
|  Tester  | ←────────────────────────────────→ |   ECU   |
| (CANoe,  |    Physical: CAN bus or Ethernet   | (DCM +  |
| INCA, PC)|                                    |  Dem)   |
+----------+                                    +---------+
```

### Transport Layer: CAN TP (ISO 15765-2)

UDS messages can be larger than 8 bytes (CAN frame limit), so ISO 15765-2 provides segmentation:
- **Single Frame (SF)** — ≤ 7 bytes
- **First Frame (FF)** + **Consecutive Frames (CF)** — for larger messages
- **Flow Control (FC)** — manages transfer speed

```
Tester sends 20-byte request:
  FF: [0x10, 0x14, 0x22, 0xF1, 0x90, 0x22, 0xF1, 0x91]  (First Frame, 20 bytes)
ECU responds:
  FC: [0x30, 0x00, 0x00, ...]  (Flow Control: ContinueToSend)
Tester sends remaining:
  CF: [0x21, 0x22, 0xF1, 0x92, 0x22, 0xF1, 0x93, 0x00]  (Consecutive Frame)
```

### DoIP (Diagnostics over Internet Protocol) — ISO 13400

DoIP enables UDS over Ethernet (TCP port 13400):

```
Tester                    DoIP Entity (GW)          Target ECU
  |--TCP Connect (13400)-->|                              |
  |--VehicleIdentRequest-->|                              |
  |<--VehicleIdentResp-----|                              |
  |--RoutingActivation---->|                              |
  |<--RoutingActivationResp|                              |
  |--DoIP DiagMsgReq------>|--RouteToCAN/ForwardUDS------>|
  |                        |<--UDS Response--------------|
  |<--DoIP DiagMsgResp-----|                              |
```

---

## 10.5 ReadDataByIdentifier (0x22) Example

**Tester reads VIN:**
```
Request:  22 F1 90          (0x22 = ReadDataByIdentifier, DID 0xF190 = VehicleIdentificationNumber)
Response: 62 F1 90 31 47 31 4A 43 35 34 34 34 52 37 32 33 34 35 36 37
          (0x62 = positive response, DID 0xF190, followed by 17-byte VIN: "1G1JC5444R7234567")
```

---

## 10.6 CAPL Diagnostic Script Example

```c
// CANoe CAPL: Read DTC from ECU
variables {
  diagRequest ECU_1.ReadDTCInformation req;
}

on start {
  // Request all active DTCs
  req.SubFunction     = 0x01; // reportNumberOfDTCByStatusMask
  req.DTCStatusMask   = 0xFF; // all statuses
  diagSendRequest(req);
}

on diagResponse ECU_1.ReadDTCInformation {
  long dtcCount;
  dtcCount = this.DTC_count;
  write("Number of active DTCs: %d", dtcCount);
}
```

---

## 10.7 Python UDS Example

```python
import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.client import Client
import udsoncan.services as uds

# Connect via ISO-TP on CAN
conn = IsoTPSocketConnection('vcan0', rxid=0x7A8, txid=0x7A0)
conn.open()

config = {
    'data_identifiers': {
        0xF190: udsoncan.AsciiCodec(17)  # VIN = 17 ASCII chars
    }
}

with Client(conn, request_timeout=2, config=config) as client:
    # Switch to extended diagnostic session
    client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
    
    # Read VIN
    response = client.read_data_by_identifier(0xF190)
    print(f"VIN: {response.service_data.values[0xF190]}")
    
    # Read all DTCs
    response = client.get_dtc_by_status_mask(0xFF)
    for dtc in response.service_data.dtcs:
        print(f"DTC: {dtc.id:#08x} Status: {dtc.status.byte:#04x}")

conn.close()
```

---

## 10.8 OBD (On-Board Diagnostics)

OBD is a regulatory standard (EPA in USA, Euro OBD in Europe) for emissions-related diagnostics.

| Mode | Purpose |
|---|---|
| Mode 0x01 | Read current data (PID: speed, RPM, O2 sensor) |
| Mode 0x02 | Read freeze frame data |
| Mode 0x03 | Read stored DTCs |
| Mode 0x04 | Clear DTCs and MIL |
| Mode 0x09 | Read vehicle info (VIN, calibration ID) |

OBD is accessible via the standard OBD-II port (SAE J1962 connector) on any vehicle since 1996 (US) and 2001 (EU).

---

## 10.9 Diagnostic Integration Checklist

```
[ ] All DTCs defined in Dem configuration match DTC specification
[ ] All DIDs configured in Dcm respond correctly (value, length)
[ ] Security access seed/key algorithm matches tester expectation
[ ] ReadDTCInformation returns correct DTC status after fault injection
[ ] ClearDiagnosticInformation clears all DTCs
[ ] TesterPresent keeps session alive
[ ] Session timeout (S3) behaves correctly
[ ] ECUReset restores normal operation
[ ] Flashing via RequestDownload/TransferData verified
[ ] DoIP routing activation works over Ethernet
[ ] OBD Mode 03/04 verified (emissions-relevant ECUs)
```

---

## Summary

| Standard | Coverage | Transport |
|---|---|---|
| UDS (ISO 14229) | Full ECU diagnostics | CAN TP or DoIP |
| OBD (ISO 15031) | Emissions diagnostics | CAN |
| DoIP (ISO 13400) | UDS over Ethernet | Ethernet / TCP |
| CAN TP (ISO 15765) | Segmentation for UDS over CAN | CAN |

---

*Next: [Part 11 — OTA Integration](part-11-ota.md)*
