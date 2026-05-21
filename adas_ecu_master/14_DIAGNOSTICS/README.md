# 14 — Diagnostics (OBD-II, UDS, DEM)

> **Standards:** ISO 14229 (UDS), SAE J1979 (OBD-II), ISO 15765-2 (ISO-TP over CAN)  
> **AUTOSAR:** DEM (Diagnostic Event Manager), DCM (Diagnostic Communication Manager)

---

## 14.1 OBD-II Overview

```
On-Board Diagnostics II (OBD-II): US regulation (CARB 1996), worldwide mandatory.
Purpose: Emissions-related fault monitoring, workshop diagnosis.

Physical layer: CAN (ISO 15765-4) at 500 kbit/s
Diagnostic tool: External scan tool → sends request → ECU responds

OBD-II PID request/response (functional addressing):
  Request: CAN ID 0x7DF  data: [02, 01, 0D, 00, ...]   (Mode 01, PID 0x0D = VehicleSpeed)
  Response: CAN ID 0x7E8  data: [03, 41, 0D, 50, ...]   (41 = response to 01, 50 hex = 80 km/h)

Common OBD-II Modes:
  Mode 01: Show current data (live PIDs)
  Mode 02: Freeze frame data (snapshot at time of fault)
  Mode 03: Read stored DTCs
  Mode 04: Clear DTCs (clears MIL lamp)
  Mode 06: On-board monitor test results
  Mode 09: Vehicle information (VIN, calibration ID)
```

---

## 14.2 UDS (ISO 14229) — Production Diagnostics

```
UDS extends OBD-II for full ECU diagnostics (beyond emissions):
  ECU programming, calibration, fault memory, security access

UDS uses CAN ID addressing:
  Physical: tool → one specific ECU  (0x7E0 for ECU 0, 0x7E1 for ECU 1, ...)
  Functional: tool → all ECUs        (0x7DF)
  Response: ECU → tool               (0x7E8 for ECU 0)

Key UDS Services:
  Service | Code | Description
  --------|------|------------------------------------------------
  DiagnosticSessionControl | 0x10 | Switch to extended/programming session
  ECUReset                 | 0x11 | Soft/hard reset
  SecurityAccess           | 0x27 | Unlock protected services (seed/key)
  CommunicationControl     | 0x28 | Enable/disable Tx/Rx
  ReadDataByIdentifier     | 0x22 | Read ECU data (VIN, SW version, sensor values)
  WriteDataByIdentifier    | 0x2E | Write calibration data
  RoutineControl           | 0x31 | Execute ECU routine (end-of-line tests)
  RequestDownload          | 0x34 | Begin software download
  TransferData             | 0x36 | Transfer flash data blocks
  TransferExit             | 0x37 | Complete flash transfer
  ReadDTCInformation       | 0x19 | Read stored DTCs
  ClearDiagnosticInfo      | 0x14 | Clear DTC memory
  InputOutputControlByID   | 0x2F | Override actuator for test (e.g., force EPS to 1 Nm)

SecurityAccess flow:
  1. Tool sends 0x27 01 (Request Seed)
  2. ECU responds with random seed: 0x67 01 <seed_bytes>
  3. Tool computes key: key = f(seed, secret_constant)  [OEM-defined algorithm]
  4. Tool sends 0x27 02 <key>
  5. ECU validates → if correct: unlocks programming/calibration services
```

---

## 14.3 DTC Format (SAE J2012)

```
DTC = 5 characters: [System][Subtype][Code][Code][Code]
Example: P0300 = Powertrain, Generic, 300 = Random/Multiple Misfire

System codes:
  P = Powertrain
  C = Chassis
  B = Body
  U = Network/Communication

Subtype:
  0 = SAE standard (OBD-II)
  1-3 = OEM-specific
  
ADAS examples (OEM-specific):
  U0155 = Lost Communication with Instrument Panel Cluster
  U0126 = Lost Communication with Steering Angle Sensor
  C1201 = ABS ECU malfunction (chassis, OEM)
  C1260 = EPS Assist Fault (chassis, OEM)

AUTOSAR DEM DTC lifecycle:
  PREFAILED → FAILED → CONFIRMED → AGED → CLEARED
  
  CONFIRMED: fault occurred N times (configurable debounce)
  AGED: fault not seen for M ignition cycles → auto-cleared
  FREEZE FRAME: snapshot of signals at first occurrence
    (e.g., VehicleSpeed=72 km/h, SteeringAngle=5.3deg, OilTemp=85°C)
```

---

## 14.4 AUTOSAR DEM Usage in SWC

```cpp
// Report error from LKA SWC when camera signal times out
#include "Dem.h"

#define DEM_EVENT_LKA_CAMERA_TIMEOUT  42U   // Event ID from ARXML

void LKA_MonitorCamera(void) {
    if (cameraSignalTimedOut) {
        // Report fault: PREPASSED/PREFAILED/PASSED/FAILED
        Dem_ReportErrorStatus(DEM_EVENT_LKA_CAMERA_TIMEOUT,
                              DEM_EVENT_STATUS_FAILED);
        
        // Transition to FAULT state in LKA state machine
        lkaSm.dispatch(Event{Events::FAULT_DETECTED});
    } else {
        Dem_ReportErrorStatus(DEM_EVENT_LKA_CAMERA_TIMEOUT,
                              DEM_EVENT_STATUS_PASSED);
    }
}

// Reading DTCs (UDS 0x19 handled by DCM → DEM):
// Tool: 19 02 08  = ReadDTCByStatusMask(confirmed DTCs)
// DEM: returns all confirmed DTCs
// DCM: formats and sends over CAN via ISO-TP

// Freeze frame data (developer configures in ARXML):
// DemFreezeFrameRecord:
//   DID 0x0001: VehicleSpeed
//   DID 0x0002: SteeringAngle  
//   DID 0x0003: LaneOffset
//   DID 0x0004: LKAState
// Captured at: first occurrence, confirmed occurrence, latest occurrence
```

---

## 14.5 DoIP (Diagnostics over IP) — Ethernet

```
ISO 13400: Diagnostics over Internet Protocol
Used in: AUTOSAR Adaptive, high-bandwidth ECUs, OTA-capable vehicles

Protocol stack:
  UDS (ISO 14229) ─── application
  DoIP (ISO 13400) ─── session layer
  TCP/UDP ─────────── transport
  100BASE-T1 ──────── physical (automotive Ethernet)

DoIP vs classic (CAN + ISO-TP):
  Bandwidth: 100 Mbit/s vs 0.5 Mbit/s → 200x faster flash programming
  Addressing: IP-based (192.168.x.x) vs CAN ID-based
  Network topology: star vs bus
  Security: TLS-encrypted DoIP sessions (ISO 13400-2:2019)

DoIP Entity Announcement:
  ECU boots → sends UDP announcement on port 13400
  Tool: discovers ECU, establishes TCP connection (port 13400)
  Then sends UDS requests over DoIP encapsulation
```

---

## 14.6 Interview Questions

```
L1:
  Q: What is the difference between OBD-II and UDS?
  A: OBD-II (SAE J1979): mandated by emissions regulation. Limited to emissions-related
     data, standardised PIDs for workshop scan tools, no write access.
     UDS (ISO 14229): full-featured production diagnostic protocol. Used by OEM engineers.
     Supports flash programming, calibration write, actuator override, custom data IDs.
     OBD-II is a subset of UDS + adds mode-specific protocols. UDS is the production
     interface; OBD-II is the emissions/workshop-facing interface.

  Q: What is a DTC freeze frame?
  A: A snapshot of selected ECU signals captured at the moment a DTC is set.
     Example: DTC C1201 (EPS fault) freeze frame stores:
     VehicleSpeed, SteeringAngle, IgnitionCycles, SupplyVoltage at time of fault.
     Purpose: allows engineers to reconstruct the conditions that caused the fault.
     Configured in AUTOSAR DEM ARXML per DTC.

L2:
  Q: Walk me through a UDS ReadDataByIdentifier (0x22) request.
  A: Tool: physical address to ECU (e.g., 0x7E0)
          Sends: [03, 22, F1, 90]  = length 3, service 0x22, DID 0xF190 (VIN)
     ISO-TP: if data > 7 bytes, uses multi-frame (FF+CF)
     DCM: receives request, calls Dcm_ReadDataByIdentifier callback
     SWC: provides VIN data (17 ASCII chars)
     DCM: formats response: [12, 62, F1, 90, 31 47 43 ...] (positive response 0x62)
     ECU sends back over ISO-TP with flow control frames if needed.

L3:
  Q: How do you protect sensitive UDS services (calibration write)?
  A: SecurityAccess (0x27) seed/key algorithm:
     1. ECU generates random 4-byte seed (from hardware RNG or time-based)
     2. Tool applies OEM secret algorithm: key = AES_encrypt(seed, secret_key)
        (Some OEMs use simpler XOR-based algorithms — weaker but common)
     3. ECU validates key independently → unlocks programming session
     
     Additional protections:
     - Programming session (0x10 02) only allowed at standstill (vehicle halted)
     - Write protected by NvM CRC: after writing calibration, verify CRC matches
     - Calibration data signed with ECDSA (modern OEMs) → ECU verifies signature
       before accepting new flash image (prevents malicious firmware injection)
     - Attempt counter: 3 failed SecurityAccess → lock out for 10 minutes (anti-brute-force)
     - AUTOSAR: SecurityAccess delay counter stored in NvM (survives power cycle)
```
