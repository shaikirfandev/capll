# UDS (ISO 14229) — Complete Study Guide
## All Services, Frame Formats, Sessions, Error Codes | April 2026

---

## Chapter 1 — What is UDS?

**Unified Diagnostic Services (UDS)** is the automotive ECU diagnostic protocol defined in **ISO 14229**. It operates over CAN, LIN, Ethernet (DoIP), FlexRay, and K-Line transport layers. UDS defines how a diagnostic tester (workshop tool, EOL station, or test bench) communicates with an ECU to:

- Read fault codes (DTCs)
- Read live data (sensor values, calibration)
- Write data (configuration, VIN, variant coding)
- Flash new software (ECU programming)
- Perform actuator tests (routine control)
- Control communication and security

### Transport Layer Stack

```
ISO 14229 (UDS Application Layer — services 0x10 to 0xBA)
        ↕
ISO 15765-2 (CAN Transport Protocol — TP / ISO-TP)
        ↕
ISO 11898 (CAN Physical Layer)

For Ethernet:
ISO 14229 UDS
        ↕
ISO 13400 (DoIP — Diagnostics over Internet Protocol)
        ↕
TCP/IP + Ethernet
```

### ISO-TP Frame Types

| Frame Type | ID | Description |
|------------|----|-------------|
| Single Frame (SF) | 0x0_ | Payload ≤ 7 bytes. PCI: nibble=0, length nibble |
| First Frame (FF) | 0x1_ | First frame of multi-frame message. PCI: nibble=1, 12-bit length |
| Consecutive Frame (CF) | 0x2_ | Follow-on data. PCI: nibble=2, sequence counter |
| Flow Control (FC) | 0x3_ | Receiver controls transmission. PCI: nibble=3 |

**Flow Control flags:** 0x30 = ContinueToSend, 0x31 = Wait, 0x32 = Overflow

**Example — Reading DTC (single frame):**
```
Request:  7A0#03 19 02 09      (3 bytes: SID=19, subFunc=02, statusMask=09)
Response: 7A8#09 59 02 09 C0 00 01 03   (first 9 bytes — multi-frame if more DTCs)
```

---

## Chapter 2 — Diagnostic Sessions (Service 0x10)

### 2.1 Session Types

| Sub-function | Name | Hex | Purpose |
|-------------|------|-----|---------|
| 0x01 | defaultSession | `10 01` | Normal operation. Basic read, clear |
| 0x02 | programmingSession | `10 02` | ECU flashing. Full access with security |
| 0x03 | extendedDiagnosticSession | `10 03` | Advanced diagnostics, write data, routine |
| 0x04 | safetySystemDiagnosticSession | `10 04` | Safety-critical ECUs (rare) |
| 0x40–0x5F | vehicleManufacturerSpecific | varies | OEM-defined sessions |
| 0x60–0x7E | systemSupplierSpecific | varies | Tier-1 defined sessions |

### 2.2 Session Transitions

```
Default → Extended: 10 03 → positive response 50 03 → now in extended
Default → Programming: 10 01 → Security Access 27 01/02 → 10 02
Extended → Default: 10 01 (or timeout — P3 client timer)
```

### 2.3 Timing Parameters (ISO 14229)

| Parameter | Typical Value | Description |
|-----------|--------------|-------------|
| P2 Client | 50ms | Timeout waiting for ECU response |
| P2* Client | 5000ms | Timeout for slow response (after 0x78 NRC) |
| P2 Server | 50ms | ECU must respond within this time |
| P3 Client | 5000ms | Tester Present interval (session keepalive) |
| S3 Client | 5000ms | Session timeout (ECU falls back to default) |

### 2.4 Negative Response for Session Change

```
NRC 0x22 (conditionsNotCorrect): ECU in wrong state for requested session
NRC 0x25 (requestOutOfRange is wrong here — actually 0x25 = invalidKey)
NRC 0x7E (subFunctionNotSupportedInActiveSession): session doesn't support this sub-function
NRC 0x7F (serviceNotSupportedInActiveSession): service not available in this session
```

---

## Chapter 3 — Security Access (Service 0x27)

### 3.1 Purpose

Protect sensitive operations (write calibration, flash ECU, activate actuators) from unauthorised access.

### 3.2 Flow

```
1. Tester → ECU:  27 01         (requestSeed, level 1)
2. ECU → Tester:  67 01 [seed4 bytes]   (sendSeed)
3. Tester computes key: Key = f(Seed, Algorithm, SecretConst)
4. Tester → ECU:  27 02 [key4 bytes]    (sendKey)
5. ECU validates:  67 02 (positive) OR 7F 27 35 (invalidKey)
```

### 3.3 Security Levels (typical OEM)

| Level | Access Code | Usage |
|-------|-------------|-------|
| 0x01/0x02 | Extended diag key | Routine control, actuator tests |
| 0x03/0x04 | EOL/calibration key | Write calibration data, variant coding |
| 0x05/0x06 | Engineering key | Full read/write, bypass limits |
| 0x11/0x12 | Programming key | ECU flash (reprogramming) |

### 3.4 Key Calculation (Common Algorithms)

**Algorithm A (XOR):** `Key = Seed XOR SecretConst`
**Algorithm B (Shift-XOR):** `Key = (Seed << 1) XOR Mask`
**Algorithm C (CRC32):** `Key = CRC32(Seed + Salt)`

### 3.5 NRC Codes for Security Access

| NRC | Code | Meaning |
|-----|------|---------|
| requestSequenceError | 0x24 | Sent key without requesting seed first |
| invalidKey | 0x35 | Key computation mismatch |
| exceededNumberOfAttempts | 0x36 | Too many failed key attempts (lockout) |
| requiredTimeDelayNotExpired | 0x37 | Must wait before retry after lockout |

---

## Chapter 4 — DTC Services (0x14 and 0x19)

### 4.1 Clear DTC — Service 0x14

```
Request:  14 FF FF FF     (clear all DTCs)
Request:  14 00 42 67     (clear specific group)
Response: 54              (positive — ClearDiagnosticInformation)
NRC 0x22: conditions not correct (engine running, vehicle moving)
```

### 4.2 Read DTC — Service 0x19 Sub-functions

| Sub-function | Name | Request Example | Description |
|-------------|------|-----------------|-------------|
| 0x01 | reportNumberOfDTCByStatusMask | `19 01 09` | Count of DTCs matching mask |
| 0x02 | reportDTCByStatusMask | `19 02 09` | List DTCs matching status mask |
| 0x03 | reportDTCSnapshotIdentification | `19 03` | List available freeze frames |
| 0x04 | reportDTCSnapshotRecordByDTCNumber | `19 04 C0 00 01 01` | Freeze frame for specific DTC |
| 0x06 | reportDTCExtendedDataRecordByDTCNumber | `19 06 C0 00 01 01` | Extended data for DTC |
| 0x07 | reportNumberOfDTCBySeverityMaskRecord | `19 07 08 09` | Count by severity + status |
| 0x08 | reportDTCBySeverityMaskRecord | `19 08 08 09` | DTCs by severity + status |
| 0x09 | reportSeverityInformationOfDTC | `19 09 C0 00 01` | Severity info for specific DTC |
| 0x0A | reportSupportedDTC | `19 0A` | All DTCs supported by ECU |
| 0x0B | reportFirstTestFailedDTC | `19 0B` | First DTC that failed since clear |
| 0x0C | reportFirstConfirmedDTC | `19 0C` | First confirmed DTC |
| 0x0D | reportMostRecentTestFailedDTC | `19 0D` | Most recent test-failed DTC |
| 0x0E | reportMostRecentConfirmedDTC | `19 0E` | Most recent confirmed DTC |
| 0x0F | reportMirrorMemoryDTCByStatusMask | `19 0F 09` | DTCs in mirror memory |
| 0x13 | reportUserDefMemoryDTCByStatusMask | `19 13 01 09` | User-defined memory DTCs |
| 0x14 | reportUserDefMemoryDTCSnapshotRecordByDTCNumber | `19 14` | User memory freeze frame |
| 0x15 | reportUserDefMemoryDTCExtDataRecordByDTCNumber | `19 15` | User memory extended data |
| 0x17 | reportDTCFaultDetectionCounter | `19 17` | Pre-confirmed DTCs (counter 1–127) |
| 0x18 | reportDTCWithPermanentStatus | `19 18` | Permanent DTCs (can't be cleared) |
| 0x19 | reportDTCExtDataRecordByRecordNumber | `19 19 01` | Extended data by record number |
| 0x42 | reportWWHOBDDTCByMaskRecord | `19 42 09` | WWH-OBD DTCs |

### 4.3 DTC Status Byte (ISO 14229)

```
Bit 7: warningIndicatorRequested
Bit 6: testNotCompletedThisMonitoringCycle
Bit 5: testFailedSinceLastClear
Bit 4: testNotCompletedSinceLastClear
Bit 3: confirmedDTC
Bit 2: pendingDTC
Bit 1: testFailedThisMonitoringCycle (since power cycle)
Bit 0: testFailed (current monitoring result)
```

Common status masks:
- `0x09` = testFailed (bit0) + confirmedDTC (bit3) → most common
- `0x0F` = all "failure" bits
- `0xFF` = all DTCs regardless of status
- `0x08` = confirmed only

### 4.4 DTC Severity Byte

```
0x20 = maintenanceOnly
0x40 = checkAtNextHalt
0x80 = checkImmediately
```

### 4.5 Freeze Frame Data (Snapshot)

Freeze frame captures ECU sensor values at the moment a DTC was set.
Common freeze frame data IDs:

| DID | Typical Content |
|-----|----------------|
| 0xF400 | Engine speed at DTC set |
| 0xF401 | Vehicle speed at DTC set |
| 0xF402 | Ambient temperature |
| 0xF403 | Odometer value |
| 0xF404 | Ignition cycles since DTC set |
| 0xF405 | Warm-up cycles since DTC clear |

---

## Chapter 5 — Read/Write Data By Identifier (0x22 / 0x2E)

### 5.1 Read Data By Identifier — Service 0x22

```
Request:  22 [DID high] [DID low]
Response: 62 [DID high] [DID low] [data bytes]

Example:  22 F1 10    → Read ECU Software Version
Response: 62 F1 10 "V2.14.01.00"
```

Multiple DIDs in one request (ISO 14229-1 allows multi-DID read):
```
Request:  22 F1 10 F1 89 F1 8C
Response: 62 F1 10 [data1] F1 89 [data2] F1 8C [data3]
```

### 5.2 Standardised DID Ranges (ISO 14229)

| Range | Owner | Description |
|-------|-------|-------------|
| 0x0000–0x00FF | OBD DIDs | Emissions, OBD-II |
| 0xF100–0xF1FF | Vehicle Manufacturer | VIN, ECU HW/SW versions |
| 0xF200–0xF2FF | OBD | System/test monitor data |
| 0xF300–0xF3FF | Vehicle Manufacturer | Stored data records |
| 0xF400–0xF4FF | ISO/SAE | Freeze frame data |
| 0xF500–0xF5FF | Vehicle Manufacturer | |
| 0xF600–0xFEFF | System Supplier | |
| 0xFF00–0xFFFF | ISOSAEReserved | |

### 5.3 Critical Standard DIDs

| DID | Name | Content |
|-----|------|---------|
| 0xF186 | activeSession | Current diagnostic session ID |
| 0xF187 | vehicleManufacturerSparePartNumber | Part number |
| 0xF188 | vehicleManufacturerECUSoftwareNumber | SW part number |
| 0xF189 | vehicleManufacturerECUSoftwareVersionNumber | SW version |
| 0xF18A | systemSupplierIdentifier | Tier-1 supplier code |
| 0xF18B | ECUManufacturingDate | Date of production |
| 0xF18C | ECUSerialNumber | Unique ECU serial |
| 0xF190 | VIN | 17-character Vehicle ID Number |
| 0xF191 | vehicleManufacturerECUHardwareNumber | HW part number |
| 0xF192 | systemSupplierECUHardwareNumber | Supplier HW number |
| 0xF193 | systemSupplierECUHardwareVersionNumber | Supplier HW version |
| 0xF194 | systemSupplierECUSoftwareNumber | Supplier SW number |
| 0xF195 | systemSupplierECUSoftwareVersionNumber | Supplier SW version |
| 0xF197 | vehicleManufacturerVehicleType | Vehicle type code |
| 0xF198 | applicationSoftwareFingerprint | Last programmed by |
| 0xF199 | applicationDataFingerprint | Last data programmed by |
| 0xF19D | programmedState | 0=not programmed, 1=programmed |
| 0xF19E | calDataODX | Calibration data ODX identifier |
| 0xF1A0 | unlockedStatus | Which security levels unlocked |

### 5.4 Write Data By Identifier — Service 0x2E

```
Request:  2E [DID high] [DID low] [data bytes]
Response: 6E [DID high] [DID low]
NRC 0x31: requestOutOfRange (DID not writable)
NRC 0x22: conditionsNotCorrect (wrong session, security not passed)
NRC 0x33: securityAccessDenied (security access required first)
```

Common write scenarios:
- Write VIN: `2E F1 90 [17 ASCII bytes]`
- Write variant code: `2E [OEM DID] [code byte]`
- Write customer configuration: `2E [DID] [config bytes]`

---

## Chapter 6 — ECU Reset (Service 0x11)

| Sub-function | Name | Hex | Description |
|-------------|------|-----|-------------|
| 0x01 | hardReset | `11 01` | Full power cycle simulation |
| 0x02 | keyOffOnReset | `11 02` | Ignition OFF → ON simulation |
| 0x03 | softReset | `11 03` | Software restart (no NVM clear) |
| 0x04–0x3F | ISO reserved | | |
| 0x40–0x5F | vehicleManufacturerSpecific | | |
| 0x60–0x7E | systemSupplierSpecific | | |

### Response Timing

After `11 01`: ECU must respond BEFORE resetting (positive response 0x51), then reset.
Reset completion time varies: 50ms (soft) to 5000ms (hard with NVM operations).

### NRC for Reset

- `0x22 conditionsNotCorrect`: vehicle moving, safety state prevents reset
- `0x25 requestSequenceError`: some ECUs require security access before hard reset

---

## Chapter 7 — Routine Control (Service 0x31)

### 7.1 Sub-functions

| Sub-function | Name | Description |
|-------------|------|-------------|
| 0x01 | startRoutine | Begin execution |
| 0x02 | stopRoutine | Halt execution |
| 0x03 | requestRoutineResults | Read outcome |

### 7.2 Format

```
Request:  31 01 [RID high] [RID low] [optional params]
Response: 71 01 [RID high] [RID low] [optional status/results]
```

### 7.3 Important Routine IDs (ISO and OEM)

| RID | Name | Usage |
|-----|------|-------|
| 0x0202 | vehicleSpeedSensorCalibration | Calibrate VSS |
| 0xF000 | deactivateLocalDiagnostic | Suppress internal monitoring |
| 0xFF00 | eraseMemory | Erase ECU flash (during programming) |
| 0xFF01 | checkProgrammingDependencies | Verify SW compatibility |
| 0xFF02 | eraseMirrorMemoryDTCs | Clear mirror memory |
| OEM defined | initiateReset | Trigger specific reset type |
| OEM defined | selfTest | Run ECU self-test, report result |
| OEM defined | actuatorTest | Drive relay/motor/valve |
| OEM defined | sensorCalibration | Calibrate offset/gain |
| OEM defined | nvmReadback | Verify written NVM data |

### 7.4 NRC for Routine Control

- `0x22`: Conditions not correct (engine must be off for erase)
- `0x24`: Request sequence error (start before checking earlier routine result)
- `0x31`: Request out of range (RID not supported)

---

## Chapter 8 — Communication Control (Service 0x28)

### 8.1 Purpose

Control which messages an ECU transmits/receives during diagnostic operations.
Used during programming to prevent communication interference.

### 8.2 Sub-functions

| Sub-function | Name | Hex | Description |
|-------------|------|-----|-------------|
| 0x00 | enableRxAndTx | `28 00 01` | Resume normal comms |
| 0x01 | enableRxDisableTx | `28 01 01` | Listen but don't transmit |
| 0x02 | disableRxEnableTx | `28 02 01` | Transmit but don't listen |
| 0x03 | disableRxAndTx | `28 03 01` | Full communication shutdown |
| 0x04 | enableRxAndDisableTxWithEnhancedAddressInfo | `28 04 01 [nodeID]` | Selective disable |
| 0x05 | enableRxAndTxWithEnhancedAddressInfo | `28 05 01 [nodeID]` | Selective enable |

### 8.3 Communication Type Byte

```
Bit 3-2: networkNumber (which CAN bus)
Bit 1-0: communicationType
  01 = normalCommunicationMessages
  02 = nmCommunicationMessages
  03 = networkManagementCommunicationMessages
```

---

## Chapter 9 — ECU Programming Sequence (Services 0x34/0x36/0x37)

### 9.1 Full Flash Sequence

```
Step 1:  10 03            → Enter Extended Session
Step 2:  27 01            → Request seed (programming unlock)
Step 3:  27 02 [key]      → Send key
Step 4:  10 02            → Enter Programming Session
Step 5:  27 11            → Request seed (programming level)
Step 6:  27 12 [key]      → Send key (programming level)
Step 7:  28 03 01         → Disable Rx/Tx (comms control)
Step 8:  31 01 FF 00      → Erase memory (routine)
Step 9:  34 00 44 [addr 4 bytes] [size 4 bytes] → RequestDownload
Step 10: 74 20 [maxBlockLen 2-4 bytes] → positive response with block size
Step 11: 36 01 [256 bytes data]  → TransferData block 1
Step 12: 36 02 [256 bytes data]  → TransferData block 2
 ... continue for all blocks ...
Step 13: 37               → RequestTransferExit
Step 14: 31 01 FF 01      → Check programming dependencies
Step 15: 28 00 01         → Enable Rx/Tx
Step 16: 11 01            → Hard Reset (activate new SW)
```

### 9.2 Service 0x34 — Request Download

```
Request:  34 [dataFormatIdentifier] [addressAndLengthFormatIdentifier]
              [memoryAddress N bytes] [memorySize N bytes]
Response: 74 [maxBlockLengthAndLengthFormatIdentifier] [maxBlockLength]

dataFormatIdentifier: 0x00=no compression, 0x11=OEM compress
addressAndLengthFormatIdentifier: 0x44 = 4-byte address + 4-byte size
```

### 9.3 Service 0x36 — Transfer Data

```
Request:  36 [blockSequenceCounter] [data bytes]
Response: 76 [blockSequenceCounter]
Counter: 01→02→...→FF→00→01 (wraps)
NRC 0x72: uploadDownloadNotAccepted
NRC 0x73: transferDataSuspended
```

### 9.4 Service 0x37 — Request Transfer Exit

```
Request:  37 [optional transfer parameter record]
Response: 77
```

---

## Chapter 10 — Input Output Control (Service 0x2F)

### 10.1 Purpose

Temporarily override sensor inputs or actuator outputs for testing without hardware setup.

### 10.2 Format

```
Request:  2F [DID high] [DID low] [controlOptionRecord] [controlEnableRecord]
Response: 6F [DID high] [DID low] [controlStatusRecord]

controlOptionRecord:
  0x00 = returnControlToECU
  0x01 = resetToDefault
  0x02 = freezeCurrentState
  0x03 = shortTermAdjustment (with control value)
```

### 10.3 Examples

```
Force coolant fan ON: 2F D0 01 03 01  (shortTermAdjustment, value=1=ON)
Force headlight ON:   2F D1 20 03 01
Return to ECU:        2F D0 01 00       (returnControlToECU)
Freeze output:        2F D0 01 02       (freeze at current state)
```

---

## Chapter 11 — All Negative Response Codes (0x7F)

### 11.1 Negative Response Format

```
Response:  7F [requested SID] [NRC byte]
Example:   7F 19 22 = Service 0x19 rejected with conditions not correct
```

### 11.2 Complete NRC Table

| NRC | Hex | Name | Meaning |
|-----|-----|------|---------|
| 0x10 | 10 | generalReject | Generic rejection |
| 0x11 | 11 | serviceNotSupported | SID not implemented |
| 0x12 | 12 | subFunctionNotSupported | Sub-function not implemented |
| 0x13 | 13 | incorrectMessageLengthOrInvalidFormat | Wrong byte count or format |
| 0x14 | 14 | responseTooLong | Response doesn't fit in buffer |
| 0x21 | 21 | busyRepeatRequest | ECU busy, resend |
| 0x22 | 22 | conditionsNotCorrect | Wrong vehicle state for request |
| 0x24 | 24 | requestSequenceError | Steps out of order |
| 0x25 | 25 | noResponseFromSubnetComponent | Gateway: downstream ECU not responding |
| 0x26 | 26 | failurePreventsExecutionOfRequestedAction | Hardware failure blocks execution |
| 0x31 | 31 | requestOutOfRange | DID/RID/address not supported |
| 0x33 | 33 | securityAccessDenied | Security not passed |
| 0x34 | 34 | authenticationRequired | ISO 14229-1:2020 new NRC |
| 0x35 | 35 | invalidKey | Wrong security key sent |
| 0x36 | 36 | exceededNumberOfAttempts | Too many failed security attempts |
| 0x37 | 37 | requiredTimeDelayNotExpired | Must wait (lockout period) |
| 0x38–0x4F | | reserved by extended addressing | |
| 0x50–0x5F | | reserved conditions | |
| 0x70 | 70 | uploadDownloadNotAccepted | Download rejected by ECU |
| 0x71 | 71 | transferDataSuspended | Data transfer aborted |
| 0x72 | 72 | generalProgrammingFailure | Flash write/erase failed |
| 0x73 | 73 | wrongBlockSequenceCounter | Transfer data block number wrong |
| 0x78 | 78 | requestCorrectlyReceivedResponsePending | ECU busy, more time needed (keep waiting) |
| 0x7E | 7E | subFunctionNotSupportedInActiveSession | Sub-function ok globally but not in this session |
| 0x7F | 7F | serviceNotSupportedInActiveSession | Service ok globally but not in this session |
| 0x81 | 81 | rpmTooHigh | Engine RPM prevents action |
| 0x82 | 82 | rpmTooLow | |
| 0x83 | 83 | engineIsRunning | |
| 0x84 | 84 | engineIsNotRunning | |
| 0x85 | 85 | engineRunTimeTooLow | |
| 0x86 | 86 | temperatureTooHigh | |
| 0x87 | 87 | temperatureTooLow | |
| 0x88 | 88 | vehicleSpeedTooHigh | |
| 0x89 | 89 | vehicleSpeedTooLow | |
| 0x8A | 8A | throttleOrPedalTooHigh | |
| 0x8B | 8B | throttleOrPedalTooLow | |
| 0x8C | 8C | transmissionRangeNotInNeutral | |
| 0x8D | 8D | transmissionRangeNotInGear | |
| 0x8F | 8F | brakeSwitch(es)NotClosed | |
| 0x90 | 90 | shifterLeverNotInPark | |
| 0x91 | 91 | torqueConverterClutchLocked | |
| 0x92 | 92 | voltageTooHigh | |
| 0x93 | 93 | voltageTooLow | |
| 0x94–0xFE | | vehicleManufacturerSpecific | OEM-defined conditions |

---

## Chapter 12 — Tester Present (Service 0x3E)

```
Request:  3E 00   → send and expect response 7E 00
Request:  3E 80   → suppress response (most common in automation)
Purpose:  Prevent ECU from timing out current session (must send every < P3 Client = 5s)
```

Used in CAPL test scripts to keep session alive during long test sequences.

---

## Chapter 13 — Control DTC Setting (Service 0x85)

```
Request:  85 01   → turnOnDTCSetting  (re-enable DTC logging)
Request:  85 02   → turnOffDTCSetting (disable DTC logging — for actuator tests)

When DTC setting off: ECU will not log DTCs even if fault conditions met.
Always re-enable with 85 01 at end of test! Otherwise DTCs missed in production.
```

---

## Chapter 14 — Link Control (Service 0x87)

```
Purpose: Change CAN/LIN/Ethernet baud rate for flash programming (higher speed)
Request:  87 01 [linkBaudRate byte]     → verifyBaudrateTransitionWithFixedBaudrate
Request:  87 02 [linkBaudRate byte]     → verifyBaudrateTransitionWithSpecificBaudrate
Request:  87 03                         → transitionBaudrate (actually switch now)
```

---

## Chapter 15 — DoIP (Diagnostics over IP / ISO 13400)

### 15.1 DoIP Overview

Used for high-bandwidth diagnostics (typically via OBD Ethernet port or internal vehicle Ethernet).

| Port | Purpose |
|------|---------|
| UDP 13400 | Vehicle announcement, routing activation |
| TCP 13400 | Diagnostic message transport |

### 15.2 DoIP Frame Header

```
[Protocol version 1 byte] [Inverse version 1 byte] [Payload type 2 bytes] [Payload length 4 bytes] [Payload]
Protocol version: 0x02 (ISO 13400-2:2012), 0x03 (ISO 13400-2:2019)
```

### 15.3 Key DoIP Payload Types

| Type | Hex | Description |
|------|-----|-------------|
| Vehicle Identification Request | 0x0001 | Discover ECUs on network |
| Vehicle Identification Response | 0x0004 | ECU VIN, EID, GID |
| Routing Activation Request | 0x0005 | Activate diagnostic channel |
| Routing Activation Response | 0x0006 | Confirm activation (0x10=success) |
| Diagnostic Message | 0x8001 | UDS request payload |
| Diagnostic Message Positive ACK | 0x8002 | UDS request received |
| Diagnostic Negative ACK | 0x8003 | UDS request rejected |

---

## Chapter 16 — EOL (End of Line) Programming Flow

### 16.1 Typical EOL Station Sequence

```
1. Vehicle on assembly line, power applied
2. EOL Tool connects (OBD port or direct ECU connection)
3. For each ECU:
   a. 22 F1 90 → Read VIN (verify correct VIN already programmed or needs writing)
   b. 22 F1 89 → Read SW version (verify correct SW loaded)
   c. 19 02 0F → Read all active DTCs (must be zero at EOL)
   d. If DTCs: investigate → clear → re-read
   e. 31 01 [EOL-RID] → Execute EOL routine (variant coding, customer config, calibration)
   f. 2E [DID] [value] → Write configuration / variant code
   g. 19 02 0F → Final DTC check
   h. PASS / FAIL stamp
4. Move to next station
```

### 16.2 Variant Coding

Writing vehicle-level configuration to ECUs:
```
Example: Infotainment market variant
2E D0 10 [variant byte]:
  0x01 = Europe left-hand drive
  0x02 = UK right-hand drive
  0x03 = North America
  0x04 = China
```

---

## Chapter 17 — UDS Over CAN vs Ethernet Comparison

| Feature | UDS over CAN (ISO-TP) | UDS over DoIP |
|---------|-----------------------|---------------|
| Max payload | 4095 bytes (ISO-TP) | Unlimited |
| Speed | 500 kbit/s–2 Mbit/s (CANFD) | 100 Mbit/s+ |
| Flash speed | ~5 min for 2MB | ~10 sec for 2MB |
| Addressing | 11-bit or 29-bit CAN ID | IP + Logical Address |
| Typical use | Body, Powertrain, Legacy ADAS | Modern ADAS, Domain ECUs, OTA |

---

## Chapter 18 — Functional vs Physical Addressing

| Type | CAN ID | Description |
|------|--------|-------------|
| Physical | 0x7A0 (e.g.) | One specific ECU |
| Functional | 0x7DF | Broadcast to all ECUs |

Use physical addressing for: security access, programming, write operations
Use functional addressing for: reading DTCs from multiple ECUs simultaneously, tester present broadcast

---

## Chapter 19 — Supplemental Services

### 0xBA — Authentication (ISO 14229-1:2020)

Enhanced security replacing 0x27, using PKI certificates:
```
BA 01 → deAuthenticate
BA 02 → verifyCertificateUnidirectional
BA 03 → verifyCertificateBidirectional
BA 04 → proofOfOwnership
BA 05 → transmitCertificate
BA 06 → requestChallengeForAuthentication
BA 07 → verifyProofOfOwnershipUnidirectional
BA 08 → verifyProofOfOwnershipBidirectional
BA 09 → authenticationConfiguration
```

### 0x84 — Secured Data Transmission

Wraps any other UDS service in cryptographic protection.

---

## Chapter 20 — Interview Quick Reference — Common UDS Questions

| Question | Key Answer Points |
|----------|------------------|
| What is 0x78 NRC? | ResponsePending — ECU needs more time. Tester must wait up to P2* (5s). Not an error. |
| Difference 0x7E vs 0x7F? | 0x7E = subfunction not supported in THIS session. 0x7F = service not supported in THIS session. Both implying service/sub-function works in another session. |
| How do DTCs get confirmed? | Must fail twice: first = pending (bit2), second consecutive = confirmed (bit3). |
| What resets permanent DTCs? | Only a completed OBD monitor drive cycle (not 14 FF FF FF). |
| Security access fails with 0x36? | Too many attempts. Must wait delay time (0x37 NRC) before retrying. |
| What is S3 Client timer? | Session timeout. If tester doesn't send 3E within S3 (5s), ECU falls back to Default session. |
| Maximum ISO-TP payload? | 4095 bytes (12-bit length field in First Frame). |
| Functional vs Physical? | Functional 0x7DF broadcasts to all ECUs. Physical targets one ECU directly. |
| When is 28 03 01 sent? | Before programming — disables ECU CAN Tx/Rx to prevent bus interference during flash. |
| What is CheckProgramDeps? | 31 01 FF 01 — after flash, checks compatibility between new SW and other ECUs. |

---

## Chapter 21 — STAR Format Interview Scenarios (UDS Diagnostics)

> **STAR = Situation → Task → Action → Result**
> Each scenario is a real-world automotive diagnostic situation answered in full STAR detail.

---

### Scenario 1 — ECU Not Responding to UDS Requests on the Test Bench

**Situation:**
During HIL (Hardware-in-the-Loop) validation of a newly integrated Body Control Module (BCM), the test engineer found that sending a `10 03` (Extended Diagnostic Session) request over CAN yielded no response. The test bench was newly configured for a new vehicle project, and the same CAPL test script had worked on the previous project's BCM variant. The CAN bus appeared active with network management frames, but all UDS requests went unanswered.

**Task:**
My responsibility was to root-cause why the ECU was unresponsive to UDS requests, restore diagnostic communication within the same working day (since regression tests were blocked), and document the findings to prevent the same issue on other ECUs being integrated the following week.

**Action:**
I took a structured diagnostic approach:

1. **Verified physical layer first** — Used CANalyzer to confirm the request frame was actually transmitted on the correct CAN channel (CAN1, 500kbit/s). Confirmed the frame `7A0#02 10 03 00 00 00 00 00` appeared on the bus.

2. **Checked the ECU's diagnostic CAN ID** — Consulted the ODX/PDXA network database file and found that the new BCM variant used a different request ID: `0x726` instead of `0x7A0` used in the old project. The CAPL script had the old IDs hardcoded.

3. **Checked for functional addressing** — Sent a broadcast request on `0x7DF` (`7DF#02 10 03 00 00 00 00 00`). The BCM responded with a positive session response on `0x72E`, confirming the ECU was alive and the issue was purely addressing.

4. **Updated the CAPL test script** — Changed `diagRequest` node address from `0x7A0` to `0x726` and updated the response ID from `0x7A8` to `0x72E` in the environment variable configuration. Re-ran the session change test.

5. **Validated all 5 UDS services** — Ran a smoke test: DiagSession `10 03`, ReadDID `22 F1 90` (VIN), ReadDTC `19 02 09`, TesterPresent `3E 00`, ECUReset `11 01`. All responded positively.

6. **Documented in the test log** — Raised a configuration item in JIRA to update the diagnostics address matrix for all new-project ECUs before test script creation.

**Result:**
Diagnostic communication was fully restored within 3 hours. The root cause was a CAN ID mismatch between the old and new BCM hardware variants — not an ECU fault. All 5 blocked regression test cases were executed and passed by end of day. The address matrix documentation was updated and reviewed by the team, preventing the same issue on 4 other ECUs integrated the following week. The incident was added to the onboarding checklist as a mandatory "verify ECU diagnostic addresses" step before any new ECU integration.

---

### Scenario 2 — Security Access Lockout During Calibration Writing

**Situation:**
On an EOL (End of Line) test station for a Powertrain Control Module (PCM), the automated EOL script intermittently failed at the security access step (Service `0x27`). The failure pattern was inconsistent: it passed on ~70% of vehicles but triggered NRC `0x36` (exceededNumberOfAttempts) on ~30%, causing the ECU to lock out for 10 minutes and blocking the production line. The issue had been occurring for 2 days with increasing frequency.

**Task:**
I was tasked with investigating the root cause of the intermittent security access lockout, proposing a fix that could be deployed to the production line without halting production, and ensuring zero lockout recurrence during a 24-hour production run validation.

**Action:**
I followed a methodical investigation approach:

1. **Collected failure logs** — Retrieved CAN traces from the EOL tool's data recorder for 5 failing vehicles. Analysed the raw frame timestamps in CANalyzer.

2. **Identified the pattern** — In all 5 failure traces, the `27 02` (sendKey) request was sent only **12ms** after the `67 01` (seedResponse) was received. The ECU datasheet specified a minimum key-send delay of **20ms** after receiving the seed, to allow internal key computation. At 12ms, the ECU had not yet finished computing the expected key and rejected the one sent — counting it as a failed attempt.

3. **Traced the timing issue to a threading problem** — The EOL tool's UDS stack ran seed-receipt callback and key-send in separate threads. A recent OS-level scheduler update on the EOL PC had reduced average thread switching latency, causing the key to be sent faster than designed.

4. **Implemented the fix** — Added an explicit `20ms` delay between receiving `67 01` and sending `27 02` in the UDS sequence in the EOL script. Also added a check: if NRC `0x35` (invalidKey) is received (not yet locked), wait 30ms and retry once before counting it as a failure.

5. **Added a guard for lockout recovery** — If NRC `0x36` is still received after the fix, the script now waits the mandatory delay (reads `requiredTimeDelayNotExpired` timer from ECU config — typically 10 minutes), retries automatically, and flags the vehicle for a quality audit rather than immediately failing it.

6. **Validated on the line** — Ran the updated script on 50 consecutive vehicles in a controlled production environment over 4 hours. Zero lockouts observed.

**Result:**
The root cause was a thread timing regression caused by an OS scheduler update, not an ECU or algorithm fault. After deploying the 20ms enforced delay, the EOL security access step ran at 100% pass rate across a 24-hour production run of 312 vehicles with zero lockout events. The fix was documented in the EOL script change log, and the 20ms minimum delay requirement was added to the ECU integration checklist for all future PCM variants.

---

### Scenario 3 — DTC False Positives After ECU Flash Update

**Situation:**
Following an OTA (Over-the-Air) software update to the ADAS domain controller ECU (software version V2.10 → V2.14), the vehicle diagnostic team received reports from the field that several DTC codes were present in vehicles post-update — specifically DTC `C0 42 00` (Radar Communication Fault) and `C1 19 03` (Camera Signal Timeout). These DTCs had never been reported with V2.10, and the radar and camera hardware had not changed. The issue affected approximately 15% of updated vehicles.

**Task:**
My task was to determine whether the DTCs represented genuine functional faults introduced by the new software, incorrect DTC threshold changes, or a diagnostic testing artifact. I was the lead diagnostics engineer in the investigation team working under a 72-hour resolution target before a customer escalation deadline.

**Action:**
I structured the investigation across three parallel workstreams:

1. **ECU software diff analysis** — Worked with the software team to compare DTC threshold parameters between V2.10 and V2.14 using the ODX calibration database. Found that the developers had adjusted the `CameraSignalTimeout_threshold` parameter from 150ms to **50ms** to improve fault detection latency. However, the normal camera startup time after a hard reset is between 80–120ms, meaning the first 50ms window after boot was now incorrectly triggering a timeout fault before the camera had a chance to initialise.

2. **DTC status byte analysis** — Read DTC status using `19 02 09` on affected vehicles. The DTC status byte showed `0x09` = `testFailed (bit0) + confirmedDTC (bit3)`, indicating the DTC was set and confirmed during the very first ignition ON cycle post-update — consistent with a race condition at startup, not an ongoing hardware fault.

3. **Freeze frame correlation** — Read freeze frame data using `19 04 C1 19 03 01`. The freeze frame showed `vehicleSpeed = 0`, `engineRunTime < 3 seconds`, and `ignitionCycles = 1`. This confirmed the fault occurred in the first 3 seconds of the very first ignition cycle — further confirming a startup race condition.

4. **Reproduced in lab** — Flashed V2.14 onto a lab ECU, connected a calibrated camera, and recorded the exact camera startup sequence. Camera signal became valid at T+95ms. ECU logged a DTC fault at T+52ms (before signal valid). Confirmed 100% reproduction.

5. **Proposed fix** — Increased the `CameraSignalTimeout_threshold` back to 120ms for post-reset startup scenarios, with a separate 50ms threshold for steady-state operation. Submitted calibration change request to software team.

6. **Interim field fix** — For already-affected vehicles, deployed a diagnostic procedure: `14 FF FF FF` (clear all DTCs), followed by a `11 02` (keyOffOnRestart) reset, then `19 02 09` re-read after 30 seconds. DTCs did not re-appear after the startup window passed, confirming they were historical artifacts.

**Result:**
Root cause was confirmed as a DTC threshold calibration error in V2.14 that set the camera signal timeout window shorter than the camera hardware startup time. A calibration patch (V2.14.1) was released within 72 hours with the corrected threshold values. The interim field procedure was deployed to all 15% affected vehicles via the service network, clearing the false DTCs with zero re-occurrence. The DTC threshold validation step was added to the SW release checklist to compare parameter changes against hardware startup timing specifications before any future release.

---

### Scenario 4 — ECU Flash Failure Mid-Programming (NRC 0x72)

**Situation:**
During a routine ECU software update campaign at a dealer workshop, the reprogramming procedure for a Transmission Control Unit (TCU) failed midway through the `0x36 TransferData` service sequence. The tool displayed NRC `0x72` (generalProgrammingFailure) at block number 73 of 156, leaving the ECU in a half-flashed state. The vehicle was immobilised (transmission would not engage). The dealer reported it as a critical escalation requiring same-day resolution.

**Task:**
I was the remote diagnostics support engineer assigned to guide the dealer technician through remote recovery of the ECU without physical ECU replacement, as a replacement TCU was not available for 3 days and the customer needed the vehicle urgently.

**Action:**
I took a step-by-step remote recovery approach:

1. **Assessed ECU state** — Instructed the technician to attempt `10 02` (programming session). The ECU responded positively (`50 02`) — confirming the bootloader was still functional and the ECU was not fully bricked.

2. **Checked NVM erase status** — Sent `31 01 FF 00` (EraseMemory routine). Received positive response `71 01 FF 00` — confirming the memory had been erased before programming started and the ECU was waiting for a complete, valid image.

3. **Identified the root cause** — Requested the programming tool logs from the dealer. Analysed the frame-level CAN trace. At block 73, the tester had sent the block but received no response for 500ms, then re-sent it. The ECU received it twice (duplicate block 73), incrementing the internal block counter incorrectly. This caused the next block (74) to be rejected with NRC `0x73` (wrongBlockSequenceCounter), which the tool misreported as NRC `0x72`.

4. **Root cause investigation** — The duplicate frame was caused by a CAN bus glitch (likely a momentary contact issue on the OBD port connector, which the technician confirmed was slightly loose).

5. **Recovery procedure** — Instructed to:
   - Securely seat the OBD connector and apply a retention clip
   - Re-enter programming session: `10 02`
   - Re-authenticate with security access `27 11` / `27 12`
   - Re-run erase: `31 01 FF 00`
   - Restart the full `0x34` + `0x36` + `0x37` programming sequence from block 1
   - Monitor the tool's block counter progress in real-time

6. **Monitored the reprogramming remotely** — Watched the technician's screen share. Programming completed all 156 blocks without error. `37` (RequestTransferExit) was acknowledged. `31 01 FF 01` (CheckProgramDeps) passed. `11 01` (HardReset) executed and TCU came up with new software version confirmed by `22 F1 89`.

**Result:**
The TCU was successfully reprogrammed on the second attempt within 45 minutes of remote support engagement. The vehicle was fully functional — transmission engaged normally and all DTCs clear. Root cause was a mechanical OBD connector contact issue causing a duplicate CAN frame, not an ECU or software fault. A field service bulletin was raised to mandate OBD connector inspection before any reprogramming procedure. NRC `0x72` vs `0x73` misreporting was flagged to the tool vendor as a software defect for their next tool update.

---

### Scenario 5 — ReadDTC Returning Unexpected DTC Count on Customer Vehicle

**Situation:**
During a pre-delivery inspection (PDI) at a dealership, the PDI diagnostic tool reported 0 DTCs when running Service `19 02 09`. However, the vehicle had an active MIL (Malfunction Indicator Lamp) illuminated on the instrument cluster. The PDI engineer marked the vehicle as "passed" (relying on the tool readout), and the vehicle was delivered to the customer. The customer returned within 2 days reporting the MIL was still on. This created a quality and customer satisfaction escalation.

**Task:**
I was assigned to investigate why the diagnostic tool returned 0 DTCs while the MIL was active, to determine if there was a tool deficiency, a protocol misuse, or an ECU reporting anomaly — and to define a corrective action for the PDI process.

**Action:**
I structured the investigation around DTC status mask analysis and tool protocol validation:

1. **Understood the status mask used** — Retrieved the PDI tool's diagnostic configuration. Found it was using `19 02 09` — status mask `0x09` = `testFailed (bit0) + confirmedDTC (bit3)`. This mask only returns DTCs where `bit0 AND bit3` are both set simultaneously.

2. **Read DTCs with an extended mask** — Connected a calibrated reference tool and sent `19 02 0F` (mask `0x0F` = all failure-related bits) and `19 02 FF` (all bits). Received 2 DTCs:
   - `P0420` (Catalyst Efficiency Below Threshold) — status byte `0x0A` = `testFailedSinceLastClear (bit1) + pendingDTC (bit2)`
   - `P0171` (System Too Lean) — status byte `0x06` = `testFailedThisMonitoringCycle (bit1) + pendingDTC (bit2)`

3. **Analysed the MIL illumination logic** — Consulted the ECU's diagnostic specification. Found that the MIL can illuminate when `testFailedSinceLastClear (bit5)` is set for emissions-relevant DTCs (OBD regulation), even before the DTC becomes `confirmedDTC (bit3)` (which requires two consecutive failures). The PDI tool's mask `0x09` missed both DTCs because neither had `bit3` (confirmedDTC) set yet — they were in the pending-but-not-yet-confirmed state.

4. **Root cause confirmation** — The PDI process tool was configured with an insufficient DTC status mask. Mask `0x09` is appropriate for workshop confirmed-fault checking but is incorrect for PDI where even pending/emissions DTCs must be detected to comply with emissions regulations.

5. **Proposed corrective action** — Updated the PDI tool's diagnostic step to use:
   - `19 02 0F` for all standard DTC checks
   - Separately `19 02 08` for confirmed-only check
   - A cross-reference check: if MIL is physically lit, at least one DTC with `warningIndicatorRequested (bit7)` set must be present. If not → tool misconfiguration, escalate.

6. **Updated the PDI checklist** — Added a mandatory MIL visual check vs DTC tool readout cross-validation step: if MIL is ON and tool shows 0 DTCs, treat as tool configuration error, not pass.

**Result:**
Root cause was PDI tool DTC status mask misconfiguration (`0x09` instead of `0x0F`). The two pending emissions-relevant DTCs were invisible to the tool but sufficient to illuminate the MIL per OBD regulation. The tool configuration was updated across all 47 dealerships using the same tool version. The PDI checklist was revised with the MIL cross-validation step. The customer vehicle was reworked (catalytic converter and fuel trim recalibration), and the vehicle was re-delivered with zero DTCs under the correct mask. No recurrence was reported in the 3-month monitoring period.

---

### Scenario 6 — Tester Present Timeout Dropping Session During Long Routine

**Situation:**
A CAPL-based automated test script for an ADAS domain ECU was executing a self-calibration routine (Service `31 01 [OEM-RID]`) that required approximately 45 seconds to complete. The test script sent the `31 01` request and then waited for the `71 01` positive response. During this wait, the ECU's session fell back to Default Session (Session timeout S3 = 5 seconds), causing the routine to abort and the response to come back as NRC `0x22` (conditionsNotCorrect). The script had been working in a previous software baseline but started failing after a 5-second S3 timeout parameter was enforced in the new ECU software version.

**Task:**
My task was to update the CAPL test framework to handle long-running routines correctly — keeping the session alive without disrupting the ongoing routine — and to make this a reusable, configurable mechanism for all long-running test sequences.

**Action:**
I redesigned the CAPL tester-present mechanism:

1. **Understood the protocol correctly** — Confirmed from ISO 14229 that:
   - Service `0x3E 80` (TesterPresent with suppressPositiveResponse bit set) keeps the session alive without requiring the ECU to send a response, reducing bus load.
   - The S3 timer resets on ANY valid UDS message received by the ECU, including `3E 80`.
   - Sending `3E 80` every 2 seconds provides a safe margin below the 5-second S3 timeout.

2. **Implemented a CAPL timer-based TesterPresent task:**

```capl
variables {
  msTimer testerPresentTimer;
  int testerPresentActive = 0;
}

on start {
  setTimer(testerPresentTimer, 2000);  // every 2 seconds
}

on timer testerPresentTimer {
  if (testerPresentActive == 1) {
    message 0x726 msg3E;
    msg3E.byte(0) = 0x02;   // length
    msg3E.byte(1) = 0x3E;   // SID TesterPresent
    msg3E.byte(2) = 0x80;   // suppressPositiveResponse
    output(msg3E);
  }
  setTimer(testerPresentTimer, 2000);  // re-arm
}
```

3. **Controlled the flag around long routines:**

```capl
// Before sending 31 01 routine
testerPresentActive = 1;
send_routine_start_request();

// Wait for routine completion (up to 60 seconds)
waitForResponse(71, 01, [RID], 60000);

// After routine completes
testerPresentActive = 0;
```

4. **Handled `0x78` NRC (ResponsePending) correctly** — During the 45-second routine, the ECU periodically sent `7F 31 78` to signal it was still processing. Updated the script to:
   - Recognise `0x78` as a valid "I'm busy" indicator, not an error
   - Reset the response wait timer each time `0x78` was received
   - Set the maximum total wait to 90 seconds (2× expected routine time)

5. **Made it reusable** — Wrapped the `testerPresentActive` flag management into a pair of test utility functions: `startSessionKeepAlive()` and `stopSessionKeepAlive()`, which any test case could call around any long-running operation.

6. **Regression tested** — Ran the calibration routine 20 times back-to-back on the test bench. All 20 passed within expected time, session remained alive, and the `31 01` received `71 01` positive response every time.

**Result:**
The session dropout issue was fully resolved. The root change was a background `3E 80` keepalive timer in CAPL firing every 2 seconds, combined with correct `0x78` NRC handling for extended ECU processing time. The reusable `startSessionKeepAlive()` / `stopSessionKeepAlive()` utility was adopted by the team and integrated into the shared CAPL test framework, immediately benefiting 6 other test scripts that had the same latent issue with other long-running routines. Test reliability improved from ~60% to 100% for all routines exceeding 5 seconds.

---

### Scenario 7 — Permanent DTC Not Being Cleared After Repair

**Situation:**
A quality audit of the OBD compliance test process revealed that after performing a repair (sensor replacement) and clearing DTCs using Service `14 FF FF FF`, the instrument cluster MIL was extinguishing — but when the vehicle was re-tested at the emissions inspection station, a Permanent DTC (PDTC) was still being reported. This was causing vehicles to fail emissions re-inspection despite the workshop clearing DTCs correctly. The issue affected approximately 8% of repaired vehicles and was escalating as a compliance risk.

**Task:**
I was asked to explain to the service teams why `14 FF FF FF` was not clearing the Permanent DTC, define the correct repair-and-clear procedure, and create a service bulletin with the proper diagnostic steps.

**Action:**
I provided a complete diagnostic and procedural explanation:

1. **Explained the Permanent DTC concept** — Permanent DTCs (PDTCs) are stored in a separate, non-volatile OBD memory partition. They are defined by OBD regulation (SAE J1979 / ISO 15031) and **cannot** be erased by a scan tool clear command (`14 FF FF FF`). This is intentional — it prevents "clear and inspect" fraud at emissions stations.

2. **Demonstrated the protocol difference:**

```
Standard DTC clear:
  Request:  14 FF FF FF
  Response: 54
  Effect:   Clears confirmed DTCs, pending DTCs, freeze frames from RAM/NVM
  Does NOT clear: Permanent DTCs (PDTC partition)

Permanent DTC read:
  Request:  19 18
  Response: 59 18 [DTC bytes with permanent status bit7 set]
  Key:      These DTCs remain until the ECU self-clears them after validation
```

3. **Explained the only valid PDTC clearing mechanism** — A PDTC clears itself automatically when:
   - The ECU runs the relevant OBD monitor to completion
   - The monitor passes (fault no longer present)
   - The ignition cycle is completed
   - This must happen at least once (some OBD modes require twice) without a new failure
   This is called an **OBD monitor drive cycle validation**.

4. **Created the correct post-repair procedure:**

```
Step 1: Verify repair is complete (sensor replaced, wiring checked)
Step 2: Clear DTCs: 14 FF FF FF
Step 3: Verify confirmed DTCs cleared: 19 02 09 → should be empty
Step 4: Check Permanent DTCs: 19 18 → note which PDTCs remain
Step 5: Perform OBD drive cycle:
        - Cold start (below 35°C ideally)
        - Drive at specified conditions (speed, duration, load) per OBD monitor spec
        - ECU runs and passes the relevant monitor
Step 6: After drive cycle, re-read: 19 18 → PDTC should now be absent
Step 7: Confirm MIL is OFF and 19 18 returns no PDTCsistian
Step 8: Vehicle cleared for emissions inspection
```

5. **Updated the diagnostic tool UI guidance** — Requested the tool vendor add a PDTC check step (`19 18`) to the post-clear validation screen, with a warning message if PDTCs are detected: *"Permanent DTCs present. Scan tool clear will not erase these. An OBD drive cycle is required."*

6. **Trained the service teams** — Delivered a 1-hour technical briefing to 12 service centres explaining the PDTC partition, why it exists, and the correct drive cycle validation process.

**Result:**
The emissions re-inspection failure rate for repaired vehicles dropped from 8% to 0.3% (residual cases where drive cycle was not performed correctly) within 6 weeks of deploying the updated procedure and tool UI change. The service bulletin was published to all dealerships in the network. The `19 18` Permanent DTC check was made a mandatory final step in the post-repair diagnostic workflow for all OBD-relevant fault repairs.

---

### Scenario 8 — Intermittent NRC 0x78 Loop During ECU Programming

**Situation:**
During a software update campaign for the Electric Vehicle Battery Management System (BMS) ECU, approximately 5% of vehicles were entering an infinite `0x78` (ResponsePending) loop during the `0x36 TransferData` phase. The programming tool would receive `7F 36 78` repeatedly and never receive the final `76 [blockCounter]` positive response. After 90 seconds, the tool timed out, leaving the BMS in a partially programmed state, which triggered a safety interlock that prevented the vehicle from being driven until BMS reprogramming was completed at a dealer.

**Task:**
I was the lead engineer for this escalation, responsible for identifying the root cause and providing both an immediate field recovery procedure and a permanent fix to prevent the issue from affecting more vehicles in the ongoing update campaign.

**Action:**
I led a cross-functional investigation with the ECU software team and the OTA platform team:

1. **Analysed the affected vehicle data** — Collected BMS ECU logs, CAN bus traces, and OTA session logs from 5 affected vehicles. All 5 showed the `7F 36 78` NRC loop starting at block 89 consistently (not random block numbers).

2. **Identified a common characteristic** — All 5 affected vehicles had BMS high-voltage battery State of Charge (SoC) between 18% and 23% at the time of the update. Vehicles with SoC above 30% were not affected.

3. **Correlated with BMS internal behaviour** — Reviewed the BMS software specification. Found that at SoC below 25%, the BMS executes a background cell balancing algorithm that activates at approximately 30-second intervals. This algorithm temporarily consumed 100% of the BMS microcontroller's CPU for ~200ms, causing the BMS to be unable to write the received flash block to NVM within the P2 Server timeout (50ms). The ECU responded with `0x78` to buy time, which resolved normally in most cases. However, if the balancing cycle occurred exactly during block 89 (which was the largest data block in the hex file — 512 bytes — requiring ~180ms of NVM write time), the combined CPU load exceeded available processing time and the ECU entered a `0x78` loop it could not exit from.

4. **Immediate field recovery procedure:**
   - Re-enter programming session: `10 02` (bootloader was still intact)
   - Re-authenticate: `27 11` + `27 12`
   - Re-erase: `31 01 FF 00`
   - Restart programming from block 1 with the tool's `maxBlockLength` reduced from 512 bytes to **256 bytes** (forcing block 89 to split into two smaller blocks)
   - All 5 vehicles recovered successfully with the smaller block size

5. **Permanent fix — dual approach:**
   - **Software team:** Added a BMS cell-balancing suppression flag during programming mode. When in programming session (`10 02`), cell balancing is suspended until session ends.
   - **OTA platform:** Added a SoC pre-check: if BMS SoC < 30%, prompt the user to charge to >30% before initiating the software update.

6. **Validated the fix** — Tested on 20 vehicles with SoC below 25%. All 20 programmed successfully with the updated BMS software containing the balancing suppression logic. Programming time average: 4 minutes 12 seconds (within specification).

**Result:**
Root cause was a CPU resource contention between BMS cell-balancing and NVM flash write operations during low-SoC conditions. The immediate fix (block size reduction) recovered all 5 stuck vehicles within 2 hours of field technician engagement. The permanent software fix was bundled into the next BMS patch release (V3.1.2). The SoC pre-check gate was deployed to the OTA platform within 48 hours, preventing any further occurrence in the ongoing campaign (remaining 40,000 vehicles). The fix was documented as a BMS diagnostic best practice: always check resource-intensive background tasks when investigating `0x78` NRC loops.

---

---

## Chapter 22 — DTC Bitmask Coding (Complete Reference)

> DTC status filtering is done entirely through bitmask operations applied to the **DTC Status Byte** returned in Service `0x19` responses. Mastering bitmasking is essential for writing correct diagnostic scripts, test tools, and ECU software.

---

### 22.1 DTC Status Byte — Full Bit Map (ISO 14229-1)

```
  Bit 7       Bit 6       Bit 5       Bit 4       Bit 3       Bit 2       Bit 1       Bit 0
┌───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│   WIR     │  TNCTMC   │  TFLC     │  TNCSLC   │  CDTC     │  PDTC     │  TFTMC    │  TF       │
└───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
  0x80        0x40        0x20        0x10        0x08        0x04        0x02        0x01

WIR   = warningIndicatorRequested        (MIL / telltale is ON)
TNCTMC= testNotCompletedThisMonitoringCycle
TFLC  = testFailedSinceLastClear         (failed at least once since last 14 FF FF FF)
TNCSLC= testNotCompletedSinceLastClear
CDTC  = confirmedDTC                     (failed in 2 consecutive drive cycles)
PDTC  = pendingDTC                       (failed once — not yet confirmed)
TFTMC = testFailedThisMonitoringCycle    (failed since last power cycle)
TF    = testFailed                       (current evaluation result — failed NOW)
```

---

### 22.2 Every Bitmask Value — Complete Table

| Mask (Hex) | Binary     | Bits Set | What is selected |
|------------|------------|----------|-----------------|
| `0x01`     | `00000001` | TF       | Currently failing DTCs only |
| `0x02`     | `00000010` | TFTMC    | Failed this power cycle |
| `0x04`     | `00000100` | PDTC     | Pending DTCs (not yet confirmed) |
| `0x08`     | `00001000` | CDTC     | Confirmed DTCs only |
| `0x09`     | `00001001` | TF+CDTC  | Currently failing AND confirmed (**most common workshop mask**) |
| `0x0A`     | `00001010` | TFTMC+CDTC | Failed this cycle + confirmed |
| `0x0C`     | `00001100` | PDTC+CDTC | Pending OR confirmed |
| `0x0F`     | `00001111` | TF+TFTMC+PDTC+CDTC | All failure-related bits |
| `0x10`     | `00010000` | TNCSLC   | Tests not completed since last clear |
| `0x20`     | `00100000` | TFLC     | Failed at any point since last clear |
| `0x28`     | `00101000` | TFLC+CDTC | Failed since clear AND confirmed |
| `0x2C`     | `00101100` | TFLC+PDTC+CDTC | Failed since clear OR pending OR confirmed |
| `0x2F`     | `00101111` | TFLC+all failure | Broad emissions-relevant search |
| `0x40`     | `01000000` | TNCTMC   | Incomplete monitors this cycle |
| `0x80`     | `10000000` | WIR      | MIL/telltale illuminated DTCs only |
| `0x88`     | `10001000` | WIR+CDTC | MIL ON + confirmed (strict PDI check) |
| `0xAF`     | `10101111` | WIR+TFLC+all failure | OBD regulatory check |
| `0xFF`     | `11111111` | All bits | Return every DTC the ECU knows about |

---

### 22.3 Bitmask Logic — How the ECU Filters

The ECU returns a DTC only if:

```
(DTC_StatusByte & RequestedStatusMask) != 0x00
```

**In words:** At least one bit set in the request mask must also be set in the DTC's stored status byte.

**Example:**
```
Request mask:    0x09  =  0000 1001  (TF + CDTC)
DTC status byte: 0x0A  =  0000 1010  (TFTMC + CDTC)

AND result:      0x08  =  0000 1000  → NOT zero → DTC IS returned

Request mask:    0x09  =  0000 1001
DTC status byte: 0x04  =  0000 0100  (PDTC only)

AND result:      0x00  =  0000 0000  → zero → DTC is NOT returned
```

---

### 22.4 CAPL Bitmask Code Examples

#### Read and parse status byte from a DTC response

```capl
variables {
  // DTC Status Byte bit positions
  const byte DTC_TF     = 0x01;  // testFailed
  const byte DTC_TFTMC  = 0x02;  // testFailedThisMonitoringCycle
  const byte DTC_PDTC   = 0x04;  // pendingDTC
  const byte DTC_CDTC   = 0x08;  // confirmedDTC
  const byte DTC_TNCSLC = 0x10;  // testNotCompletedSinceLastClear
  const byte DTC_TFLC   = 0x20;  // testFailedSinceLastClear
  const byte DTC_TNCTMC = 0x40;  // testNotCompletedThisMonitoringCycle
  const byte DTC_WIR    = 0x80;  // warningIndicatorRequested (MIL ON)
}

// Parse a single DTC status byte and print all active flags
void parseDTCStatus(byte statusByte, dword dtcCode) {
  write("DTC 0x%06X — Status: 0x%02X", dtcCode, statusByte);
  if (statusByte & DTC_TF)     write("  [bit0] testFailed — CURRENTLY FAILING");
  if (statusByte & DTC_TFTMC)  write("  [bit1] testFailedThisMonitoringCycle");
  if (statusByte & DTC_PDTC)   write("  [bit2] pendingDTC — NOT YET CONFIRMED");
  if (statusByte & DTC_CDTC)   write("  [bit3] confirmedDTC — CONFIRMED FAULT");
  if (statusByte & DTC_TNCSLC) write("  [bit4] testNotCompletedSinceLastClear");
  if (statusByte & DTC_TFLC)   write("  [bit5] testFailedSinceLastClear");
  if (statusByte & DTC_TNCTMC) write("  [bit6] testNotCompletedThisMonitoringCycle");
  if (statusByte & DTC_WIR)    write("  [bit7] warningIndicatorRequested — MIL ON");
}

// Check if a DTC is confirmed
int isDTCConfirmed(byte statusByte) {
  return (statusByte & DTC_CDTC) != 0;
}

// Check if MIL would be illuminated by this DTC
int isMILActive(byte statusByte) {
  return (statusByte & DTC_WIR) != 0;
}

// Check if DTC passes a given status mask (same logic ECU uses)
int dtcMatchesMask(byte statusByte, byte requestMask) {
  return (statusByte & requestMask) != 0;
}
```

#### Build a DTC status mask dynamically

```capl
byte buildStatusMask(int wantConfirmed, int wantPending, int wantCurrentlyFailing, int wantMIL) {
  byte mask = 0x00;
  if (wantConfirmed)        mask = mask | DTC_CDTC;   // 0x08
  if (wantPending)          mask = mask | DTC_PDTC;   // 0x04
  if (wantCurrentlyFailing) mask = mask | DTC_TF;     // 0x01
  if (wantMIL)              mask = mask | DTC_WIR;    // 0x80
  return mask;
}

// Usage:
// byte mask = buildStatusMask(1, 0, 1, 0);  →  mask = 0x09 (confirmed + currently failing)
// byte mask = buildStatusMask(1, 1, 0, 0);  →  mask = 0x0C (confirmed or pending)
// byte mask = buildStatusMask(1, 1, 1, 1);  →  mask = 0x8D (all of the above)
```

#### Parse all DTCs from a full 0x19 0x02 response buffer

```capl
// Assumes responseBuffer[] holds bytes from: 59 02 [statusOfDTCMask] [DTC1 3bytes][status1] [DTC2 3bytes][status2] ...
void parseReadDTCResponse(byte responseBuffer[], int responseLen) {
  int offset;
  dword dtcCode;
  byte dtcStatus;
  int dtcCount = 0;

  if (responseBuffer[0] != 0x59 || responseBuffer[1] != 0x02) {
    write("ERROR: Not a valid 19 02 response");
    return;
  }

  // Each DTC record = 4 bytes: 3 bytes DTC + 1 byte status
  // Response offset 3 onwards (byte[0]=0x59, byte[1]=0x02, byte[2]=statusMask)
  offset = 3;
  while (offset + 3 < responseLen) {
    dtcCode  = ((dword)responseBuffer[offset]   << 16)
             | ((dword)responseBuffer[offset+1] << 8)
             |  (dword)responseBuffer[offset+2];
    dtcStatus = responseBuffer[offset+3];

    dtcCount++;
    write("--- DTC #%d ---", dtcCount);
    parseDTCStatus(dtcStatus, dtcCode);

    offset += 4;
  }
  write("Total DTCs found: %d", dtcCount);
}
```

---

### 22.5 Python Bitmask Code Examples

```python
# DTC Status Byte bit masks (ISO 14229-1)
DTC_TF     = 0x01   # testFailed
DTC_TFTMC  = 0x02   # testFailedThisMonitoringCycle
DTC_PDTC   = 0x04   # pendingDTC
DTC_CDTC   = 0x08   # confirmedDTC
DTC_TNCSLC = 0x10   # testNotCompletedSinceLastClear
DTC_TFLC   = 0x20   # testFailedSinceLastClear
DTC_TNCTMC = 0x40   # testNotCompletedThisMonitoringCycle
DTC_WIR    = 0x80   # warningIndicatorRequested (MIL)

BIT_NAMES = {
    DTC_TF:     "testFailed",
    DTC_TFTMC:  "testFailedThisMonitoringCycle",
    DTC_PDTC:   "pendingDTC",
    DTC_CDTC:   "confirmedDTC",
    DTC_TNCSLC: "testNotCompletedSinceLastClear",
    DTC_TFLC:   "testFailedSinceLastClear",
    DTC_TNCTMC: "testNotCompletedThisMonitoringCycle",
    DTC_WIR:    "warningIndicatorRequested",
}


def parse_dtc_status(status_byte: int) -> list[str]:
    """Return list of active flag names for a DTC status byte."""
    return [name for mask, name in BIT_NAMES.items() if status_byte & mask]


def dtc_matches_mask(status_byte: int, request_mask: int) -> bool:
    """Return True if the DTC would be returned for the given request mask."""
    return bool(status_byte & request_mask)


def is_confirmed(status_byte: int) -> bool:
    return bool(status_byte & DTC_CDTC)


def is_pending_only(status_byte: int) -> bool:
    """Pending but not yet confirmed."""
    return bool(status_byte & DTC_PDTC) and not bool(status_byte & DTC_CDTC)


def is_mil_active(status_byte: int) -> bool:
    return bool(status_byte & DTC_WIR)


def encode_dtc(high: int, mid: int, low: int) -> int:
    """Combine 3 DTC bytes into a single integer."""
    return (high << 16) | (mid << 8) | low


def decode_dtc(dtc: int) -> tuple[int, int, int]:
    """Split a DTC integer back into 3 bytes."""
    return (dtc >> 16) & 0xFF, (dtc >> 8) & 0xFF, dtc & 0xFF


def parse_read_dtc_response(response: bytes, request_mask: int = 0x09) -> list[dict]:
    """
    Parse a full UDS 0x19 0x02 response payload.
    response: raw bytes starting from 0x59
    Returns list of dicts: {dtc_code, status_byte, flags, confirmed, mil}
    """
    assert response[0] == 0x59 and response[1] == 0x02, "Not a valid 59 02 response"
    results = []
    offset = 3  # skip 59 02 [statusMask]
    while offset + 3 <= len(response):
        dtc_code  = encode_dtc(response[offset], response[offset+1], response[offset+2])
        status    = response[offset + 3]
        results.append({
            "dtc_code":   f"0x{dtc_code:06X}",
            "status_byte": f"0x{status:02X}",
            "binary":     f"{status:08b}",
            "flags":      parse_dtc_status(status),
            "confirmed":  is_confirmed(status),
            "pending":    is_pending_only(status),
            "mil_active": is_mil_active(status),
            "matches_mask": dtc_matches_mask(status, request_mask),
        })
        offset += 4
    return results


# ── Usage Example ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulated response: 59 02 09 | C00001 0A | C11903 08 | B04200 04
    raw = bytes([0x59, 0x02, 0x09,
                 0xC0, 0x00, 0x01, 0x0A,
                 0xC1, 0x19, 0x03, 0x08,
                 0xB0, 0x42, 0x00, 0x04])

    dtcs = parse_read_dtc_response(raw, request_mask=0x09)
    for d in dtcs:
        print(f"\nDTC {d['dtc_code']}  Status: {d['status_byte']} ({d['binary']})")
        print(f"  Flags     : {', '.join(d['flags'])}")
        print(f"  Confirmed : {d['confirmed']}  |  Pending: {d['pending']}  |  MIL: {d['mil_active']}")
        print(f"  Matches 0x09 mask: {d['matches_mask']}")

# ── Output ───────────────────────────────────────────────────────────────────
# DTC 0xC00001  Status: 0x0A (00001010)
#   Flags     : testFailedThisMonitoringCycle, confirmedDTC
#   Confirmed : True  |  Pending: False  |  MIL: False
#   Matches 0x09 mask: True
#
# DTC 0xC11903  Status: 0x08 (00001000)
#   Flags     : confirmedDTC
#   Confirmed : True  |  Pending: False  |  MIL: False
#   Matches 0x09 mask: True
#
# DTC 0xB04200  Status: 0x04 (00000100)
#   Flags     : pendingDTC
#   Confirmed : False  |  Pending: True  |  MIL: False
#   Matches 0x09 mask: False    ← NOT returned for mask 0x09, only for 0x0C or 0x0F
```

---

### 22.6 C Code Examples (Embedded / ECU Side)

```c
#include <stdint.h>
#include <stdbool.h>

/* DTC Status Byte bit masks — ISO 14229-1 */
#define DTC_TF      (0x01u)   /* testFailed                          */
#define DTC_TFTMC   (0x02u)   /* testFailedThisMonitoringCycle       */
#define DTC_PDTC    (0x04u)   /* pendingDTC                          */
#define DTC_CDTC    (0x08u)   /* confirmedDTC                        */
#define DTC_TNCSLC  (0x10u)   /* testNotCompletedSinceLastClear      */
#define DTC_TFLC    (0x20u)   /* testFailedSinceLastClear            */
#define DTC_TNCTMC  (0x40u)   /* testNotCompletedThisMonitoringCycle */
#define DTC_WIR     (0x80u)   /* warningIndicatorRequested           */

/* Commonly used request masks */
#define MASK_CONFIRMED_ONLY        (DTC_CDTC)                    /* 0x08 */
#define MASK_CONFIRMED_FAILING     (DTC_CDTC | DTC_TF)           /* 0x09 */
#define MASK_ALL_ACTIVE            (DTC_TF | DTC_TFTMC | DTC_PDTC | DTC_CDTC) /* 0x0F */
#define MASK_EMISSIONS_OBD         (DTC_TFLC | DTC_PDTC | DTC_CDTC | DTC_WIR)/* 0xAC */
#define MASK_ALL                   (0xFFu)

typedef struct {
    uint8_t  high;      /* DTC byte 1 */
    uint8_t  mid;       /* DTC byte 2 */
    uint8_t  low;       /* DTC byte 3 */
    uint8_t  status;    /* DTC status byte */
} DTC_Record_t;


/* Returns true if DTC passes the requested status mask (ECU filter logic) */
bool DTC_MatchesMask(const DTC_Record_t *dtc, uint8_t requestMask) {
    return (dtc->status & requestMask) != 0u;
}

/* Set/clear individual bits on the status byte */
void DTC_SetBit(DTC_Record_t *dtc, uint8_t bitMask) {
    dtc->status |= bitMask;
}

void DTC_ClearBit(DTC_Record_t *dtc, uint8_t bitMask) {
    dtc->status &= (uint8_t)(~bitMask);
}

bool DTC_IsBitSet(const DTC_Record_t *dtc, uint8_t bitMask) {
    return (dtc->status & bitMask) != 0u;
}

/* Promote pending → confirmed (second consecutive failure) */
void DTC_ConfirmFault(DTC_Record_t *dtc) {
    DTC_SetBit(dtc, DTC_CDTC);    /* set confirmedDTC   */
    DTC_SetBit(dtc, DTC_TFLC);    /* set failedSinceClear */
    DTC_SetBit(dtc, DTC_WIR);     /* request MIL        */
    DTC_ClearBit(dtc, DTC_TNCSLC);/* test is now complete */
}

/* First failure — set pending, not yet confirmed */
void DTC_SetPending(DTC_Record_t *dtc) {
    DTC_SetBit(dtc, DTC_TF);      /* currently failing  */
    DTC_SetBit(dtc, DTC_TFTMC);   /* failed this cycle  */
    DTC_SetBit(dtc, DTC_PDTC);    /* pending            */
    DTC_SetBit(dtc, DTC_TFLC);    /* failed since clear */
}

/* Heal: fault no longer present */
void DTC_SetPassed(DTC_Record_t *dtc) {
    DTC_ClearBit(dtc, DTC_TF);    /* no longer failing  */
    /* PDTC and CDTC remain until cleared by Service 0x14 */
}

/* Clear all status bits — simulates Service 0x14 FF FF FF effect */
void DTC_ClearStatus(DTC_Record_t *dtc) {
    dtc->status = 0x00u;
    /* NOTE: permanent DTC partition is separate — not cleared here */
}

/* Count DTCs in array matching a mask — equivalent to 19 01 response */
uint16_t DTC_CountByMask(const DTC_Record_t *dtcArray, uint16_t count, uint8_t mask) {
    uint16_t result = 0u;
    for (uint16_t i = 0u; i < count; i++) {
        if (DTC_MatchesMask(&dtcArray[i], mask)) {
            result++;
        }
    }
    return result;
}

/* Build 19 02 response — write matching DTCs into output buffer */
uint16_t DTC_BuildReadDTCResponse(
    const DTC_Record_t *dtcArray, uint16_t count,
    uint8_t requestMask,
    uint8_t *outBuffer, uint16_t bufferSize)
{
    uint16_t offset = 0u;

    /* Response header: 59 02 [requestMask] */
    if (offset + 3u > bufferSize) return 0u;
    outBuffer[offset++] = 0x59u;
    outBuffer[offset++] = 0x02u;
    outBuffer[offset++] = requestMask;

    for (uint16_t i = 0u; i < count; i++) {
        if (!DTC_MatchesMask(&dtcArray[i], requestMask)) continue;
        if (offset + 4u > bufferSize) break;   /* buffer full */
        outBuffer[offset++] = dtcArray[i].high;
        outBuffer[offset++] = dtcArray[i].mid;
        outBuffer[offset++] = dtcArray[i].low;
        outBuffer[offset++] = dtcArray[i].status;
    }
    return offset;  /* total bytes written */
}
```

---

### 22.7 Bitmask Quick-Decision Table for Test Engineers

| I want to find… | Use mask | Hex |
|-----------------|----------|-----|
| All currently active faults | `TF` | `0x01` |
| All faults active this power cycle | `TF \| TFTMC` | `0x03` |
| All pending faults | `PDTC` | `0x04` |
| All confirmed faults | `CDTC` | `0x08` |
| Confirmed + currently failing | `CDTC \| TF` | `0x09` |
| Confirmed + pending (any stored fault) | `CDTC \| PDTC` | `0x0C` |
| Any failure-related bit | `TF \| TFTMC \| PDTC \| CDTC` | `0x0F` |
| Any fault ever since last clear | `TFLC` | `0x20` |
| Only faults triggering MIL | `WIR` | `0x80` |
| OBD emissions-relevant (PDI strict) | `WIR \| TFLC \| PDTC \| CDTC` | `0xAC` |
| Everything — full ECU DTC inventory | `all` | `0xFF` |

---

### 22.8 DTC Status Lifecycle — State Diagram

```
[No fault]
    │
    │  Fault detected for first time
    ▼
[TF=1, TFTMC=1, PDTC=1, TFLC=1]    ← PENDING DTC (first failure)
    │                    │
    │  Fault healed       │  Fault detected AGAIN
    │  (same cycle)       │  in next drive cycle
    ▼                    ▼
[TF=0, PDTC remains]   [CDTC=1, WIR=1]    ← CONFIRMED DTC (two consecutive failures)
    │                        │
    │                        │  Fault heals
    │                        ▼
    │               [TF=0, CDTC=1, WIR=1 remain]   ← Stored, MIL still ON
    │                        │
    │                        │  Service 14 FF FF FF
    │                        ▼
    └──────────────── [All bits cleared except PDTC/CDTC]
                             │
                             │  OBD monitor passes (for Permanent DTCs)
                             ▼
                       [PDTC=0, CDTC=0, WIR=0]    ← Fully healed
```

---

### 22.9 Common Bitmask Mistakes and Correct Usage

| Mistake | Wrong | Correct |
|---------|-------|---------|
| Using `0x09` at PDI and missing pending emissions faults | `19 02 09` | `19 02 0F` or `19 02 AC` |
| Assuming `14 FF FF FF` clears MIL immediately | It clears CDTC + WIR in NVM. MIL turns off after `19 18` returns empty. | Verify with `19 18` for permanent DTCs |
| Reading only confirmed DTCs during validation | `19 02 08` alone | Also run `19 02 04` for pending check |
| Not checking `TFLC (bit5)` after long test run | DTC may have appeared and healed — `0x09` would miss it | Use `19 02 20` or `19 02 2F` to catch historical faults |
| Treating `0x78` as a mask (it's an NRC, not a status bit) | Confusion between NRC `0x78` and status bit values | NRC `0x78` = ResponsePending; status `0x80` = WIR — completely separate |
| Sending `19 02 00` (mask = 0) | ECU will either return no DTCs or NRC `0x31` (request out of range) | Always use a non-zero mask |

---

---

## Chapter 23 — How to Execute UDS Testing on a Real Project

> **Key Principle:** UDS services are standardised by ISO 14229, but **every DID, RID, and DTC code is project-specific** and must be sourced from the project's **Diagnostic Requirement Matrix** (also called Diagnostic Specification, `.ODX` file, `.PDXA` database, or an Excel/Confluence requirement sheet). You never guess them — you read them from the document.

---

### 23.1 Where DIDs, RIDs, and DTCs Come From

```
┌─────────────────────────────────────────────────────────────────┐
│          Project Diagnostic Requirement Matrix                  │
│  (Supplied by ECU Supplier / System Architect / OEM Diagnostic  │
│   team — formats: ODX, MDF, Excel, Confluence, DOORS)           │
│                                                                 │
│  Contains:                                                      │
│  ┌──────────────────┬────────────────────────────────────────┐  │
│  │ DID Table        │ DID 0x2101 = "TurboBoostPressure"      │  │
│  │                  │ DID 0x2102 = "FuelRailPressure"        │  │
│  │                  │ DID 0xF190 = VIN (ISO standard)        │  │
│  ├──────────────────┼────────────────────────────────────────┤  │
│  │ RID Table        │ RID 0x0203 = "InjectorBalanceTest"     │  │
│  │                  │ RID 0x0301 = "EGRValveCalibration"     │  │
│  ├──────────────────┼────────────────────────────────────────┤  │
│  │ DTC Table        │ DTC P0087 = "FuelRailPressureLow"      │  │
│  │                  │ DTC P0234 = "TurboOverboostCondition"  │  │
│  ├──────────────────┼────────────────────────────────────────┤  │
│  │ Session/Security │ Extended session required for 0x2101   │  │
│  │ Requirements     │ Security level 0x03 for write DIDs     │  │
│  ├──────────────────┼────────────────────────────────────────┤  │
│  │ CAN IDs          │ Request ID: 0x7E0   Response ID: 0x7E8 │  │
│  └──────────────────┴────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Your job as a test engineer:**
1. Read the requirement matrix
2. Extract the DIDs, RIDs, DTCs, session requirements, and security levels
3. Build test cases that validate every entry in the matrix
4. Map test results back to requirements

---

### 23.2 Full Project Example — PCM (Powertrain Control Module)

Below is a complete worked example using a **fictional but realistic** PCM ECU with all values sourced from a sample requirement matrix. This single ECU covers every major UDS service.

#### Requirement Matrix Extract (PCM — Project OMEGA)

| ID | Type | Identifier | Name | Session | Security | Data Format | Access |
|----|------|-----------|------|---------|----------|-------------|--------|
| REQ-001 | DID | `0xF190` | VIN | Default | None | 17 ASCII bytes | Read |
| REQ-002 | DID | `0xF189` | SW Version | Default | None | ASCII string | Read |
| REQ-003 | DID | `0x2101` | TurboBoostPressure | Extended | None | UINT16, 0.01 kPa/bit | Read |
| REQ-004 | DID | `0x2102` | FuelRailPressure_bar | Extended | None | UINT16, 0.1 bar/bit | Read |
| REQ-005 | DID | `0x2103` | EngineOilTemp_degC | Extended | None | INT8, 1°C/bit, offset −40 | Read |
| REQ-006 | DID | `0x2104` | ThrottlePosition_pct | Extended | None | UINT8, 0.4%/bit | Read |
| REQ-007 | DID | `0xD001` | VariantCode | Extended | Level 0x03/0x04 | UINT8 | Read/Write |
| REQ-008 | DID | `0xD002` | ImmobilizerStatus | Extended | Level 0x03/0x04 | UINT8 (0=Off,1=On) | Read/Write |
| REQ-009 | DID | `0xD010` | InjectorTrimCyl1 | Extended | Level 0x05/0x06 | INT16, 0.01ms/bit | Read/Write |
| REQ-010 | RID | `0x0201` | EGRValveSweepTest | Extended | None | Param: UINT8 (cycles) | Start/Result |
| REQ-011 | RID | `0x0202` | InjectorBalanceTest | Extended | Level 0x03/0x04 | No params | Start/Stop/Result |
| REQ-012 | RID | `0xFF00` | EraseFlashMemory | Programming | Level 0x11/0x12 | None | Start |
| REQ-013 | RID | `0xFF01` | CheckProgramDependencies | Programming | Level 0x11/0x12 | None | Start/Result |
| REQ-014 | DTC | `P0087` `(0xC00087)` | FuelRailPressureTooLow | — | — | Status per ISO 14229 | Read/Clear |
| REQ-015 | DTC | `P0234` `(0xC00234)` | TurboOverboostCondition | — | — | Status per ISO 14229 | Read/Clear |
| REQ-016 | DTC | `P0300` `(0xC00300)` | RandomMultipleMisfire | — | — | Status per ISO 14229 | Read/Clear |
| REQ-017 | DTC | `U0100` `(0xC4A100)` | LostCommWithECM | — | — | Status per ISO 14229 | Read/Clear |
| REQ-018 | Session | `10 03` | ExtendedDiagSession | — | — | — | Enter from Default |
| REQ-019 | Session | `10 02` | ProgrammingSession | — | — | — | Enter after 27 01/02 |
| REQ-020 | Security | `27 01/02` | Level1 ExtDiag Key | Extended | Algo: XOR 0xA5B6C7D8 | — | Unlock write DIDs |

---

### 23.3 Complete UDS Test Sequence — Service by Service

> All frames below use: **Request CAN ID = `0x7E0`**, **Response CAN ID = `0x7E8`**

---

#### STEP 1 — Verify Default Session (Service 0x10)

```
Test: REQ-018 — ECU starts in Default Session
──────────────────────────────────────────────
Request:   7E0#02 10 01 00 00 00 00 00
           └─ len=2, SID=0x10, subFunc=0x01 (defaultSession)

Response:  7E8#06 50 01 00 19 01 F4 00
           └─ 0x50=positive, 0x01=defaultSession
              P2=0x0019 (25ms), P2*=0x01F4 (500×10ms=5000ms)

PASS criteria: Byte[0]=0x50, Byte[1]=0x01
```

---

#### STEP 2 — Read VIN (Service 0x22, DID 0xF190 — REQ-001)

```
Test: REQ-001 — Read VIN in Default Session
────────────────────────────────────────────
Request:   7E0#03 22 F1 90 00 00 00 00
           └─ len=3, SID=0x22, DID=0xF190

Response:  7E8#14 62 F1 90 W0M1A2B3C4D5E6F7G8H (multi-frame ISO-TP)
           First Frame:  7E8#10 14 62 F1 90 57 30 4D
           Flow Control: 7E0#30 00 0A 00 00 00 00 00
           Consec 1:     7E8#21 31 41 32 42 33 43 34
           Consec 2:     7E8#22 44 35 45 36 46 37 47
           └─ 0x62=positive, DID=0xF190, data=17 ASCII bytes = VIN

PASS criteria:
  - Byte[0]=0x62, Byte[1]=0xF1, Byte[2]=0x90
  - Bytes[3..19] = 17 printable ASCII chars (0x20–0x7E)
  - Length exactly 17 bytes
  - No NRC received

Expected decoded VIN: "W0M1A2B3C4D5E6F7G"
```

---

#### STEP 3 — Read SW Version (Service 0x22, DID 0xF189 — REQ-002)

```
Test: REQ-002 — Read ECU Software Version
──────────────────────────────────────────
Request:   7E0#03 22 F1 89 00 00 00 00

Response:  7E8#0D 62 F1 89 56 32 2E 31 34 2E 30 31 2E 30 30
           └─ decoded ASCII: "V2.14.01.00"

PASS criteria:
  - Byte[0]=0x62
  - ASCII string matches baseline version from project release document
  - Format matches "V[major].[minor].[patch].[build]" (REQ-002 format spec)
```

---

#### STEP 4 — Enter Extended Diagnostic Session (Service 0x10 — REQ-018)

```
Test: REQ-018 — Transition to Extended Session
───────────────────────────────────────────────
Request:   7E0#02 10 03 00 00 00 00 00

Response:  7E8#06 50 03 00 19 01 F4 00
           └─ 0x50=positive, 0x03=extendedSession

PASS criteria: Byte[0]=0x50, Byte[1]=0x03
FAIL criteria: 7F 10 22 (conditionsNotCorrect)
               7F 10 7F (serviceNotSupportedInActiveSession)
```

---

#### STEP 5 — Read Live Data DIDs (Service 0x22 — REQ-003 to REQ-006)

```
Test: REQ-003 — Read Turbo Boost Pressure
──────────────────────────────────────────
Precondition: Engine running, boost active
Request:   7E0#03 22 21 01 00 00 00 00

Response:  7E8#05 62 21 01 0A F0
           └─ data = 0x0AF0 = 2800 decimal
              Physical value = 2800 × 0.01 kPa = 28.00 kPa

PASS criteria:
  - Byte[0]=0x62, Byte[1..2]=0x2101
  - Value in range: 0 kPa to 300 kPa (physical limits from REQ-003)

──────────────────────────────────────────
Test: REQ-004 — Read Fuel Rail Pressure
──────────────────────────────────────────
Request:   7E0#03 22 21 02 00 00 00 00

Response:  7E8#05 62 21 02 01 9A
           └─ data = 0x019A = 410 decimal
              Physical value = 410 × 0.1 bar = 41.0 bar

PASS criteria: Value 20.0–180.0 bar (engine running range from REQ-004)

──────────────────────────────────────────
Test: REQ-005 — Read Engine Oil Temperature
──────────────────────────────────────────
Request:   7E0#03 22 21 03 00 00 00 00

Response:  7E8#04 62 21 03 62
           └─ data = 0x62 = 98 decimal
              Physical value = 98 − 40 = 58°C

PASS criteria: Value −40°C to +150°C (REQ-005 physical range)

──────────────────────────────────────────
Test: REQ-006 — Read Throttle Position
──────────────────────────────────────────
Request:   7E0#03 22 21 04 00 00 00 00

Response:  7E8#04 62 21 04 7D
           └─ data = 0x7D = 125 decimal
              Physical value = 125 × 0.4% = 50.0%

PASS criteria: Value 0%–100% (0x00–0xFA per REQ-006)

──────────────────────────────────────────
Multi-DID Read in one request (ISO 14229 allows this):
──────────────────────────────────────────
Request:   7E0#09 22 21 01 21 02 21 03 21 04   (multi-frame)
Response:  7E8#11 62 21 01 0A F0 21 02 01 9A 21 03 62 21 04 7D 00
           └─ All 4 DIDs returned in one response (reduces test cycle time)
```

---

#### STEP 6 — Security Access (Service 0x27 — REQ-020)

```
Test: REQ-020 — Unlock Security Level 0x03/0x04 (for write DIDs)
──────────────────────────────────────────────────────────────────
Step 6a — Request Seed:
  Request:   7E0#02 27 03 00 00 00 00 00
             └─ subFunc=0x03 = requestSeed level 3

  Response:  7E8#06 67 03 12 34 AB CD 00
             └─ 0x67=positive, seed = 0x1234ABCD

Step 6b — Compute Key:
  Algorithm from REQ-020: Key = Seed XOR 0xA5B6C7D8
  Key = 0x1234ABCD XOR 0xA5B6C7D8 = 0xB7826C15

Step 6c — Send Key:
  Request:   7E0#06 27 04 B7 82 6C 15 00
             └─ subFunc=0x04 = sendKey level 3

  Response:  7E8#02 67 04 00 00 00 00 00
             └─ 0x67=positive, security unlocked

FAIL scenarios:
  7F 27 35 = invalidKey         → wrong algorithm / wrong constant
  7F 27 36 = exceededAttempts   → too many failures, wait for 0x37 timer
  7F 27 24 = requestSeqError    → tried to send key without requesting seed first
```

---

#### STEP 7 — Write Data By Identifier (Service 0x2E — REQ-007, REQ-008)

```
Test: REQ-007 — Write Variant Code
────────────────────────────────────
Precondition: Extended Session + Security level 0x03/0x04 unlocked
Request:   7E0#04 2E D0 01 03 00 00 00
           └─ SID=0x2E, DID=0xD001, data=0x03 (Europe RHD)

Response:  7E8#03 6E D0 01 00 00 00 00
           └─ 0x6E=positive, DID=0xD001 echoed

Verify write: Read back with 22 D0 01
  Response: 7E8#04 62 D0 01 03 → data=0x03 ✓

PASS criteria:
  - 0x6E response received
  - Read-back value matches written value
  - Value within range 0x01–0x06 (REQ-007 variant range)

NRC scenarios:
  7F 2E 31 = requestOutOfRange  → DID 0xD001 not writable (check session)
  7F 2E 33 = securityAccessDenied → security not unlocked first
  7F 2E 22 = conditionsNotCorrect → wrong session (need Extended)

──────────────────────────────────────────
Test: REQ-008 — Write Immobilizer Status
──────────────────────────────────────────
Request:   7E0#04 2E D0 02 00 00 00 00
           └─ DID=0xD002, data=0x00 (disable immobilizer for test bench)

Response:  7E8#03 6E D0 02 00 00 00 00   → positive write
```

---

#### STEP 8 — Input Output Control (Service 0x2F)

```
Test: Actuator Test — EGR Valve Force Open
────────────────────────────────────────────
Precondition: Extended Session, engine off (physical safety req)
Request:   7E0#06 2F 21 10 03 64 00 00
           └─ SID=0x2F, DID=0x2110 (EGRValvePosition),
              controlOption=0x03 (shortTermAdjustment), value=0x64 (100%)

Response:  7E8#05 6F 21 10 03 64 00 00
           └─ 0x6F=positive, status echoed

Verify: Read DID 0x2110 → should return 0x64 (100%)

Return control to ECU:
  Request:   7E0#04 2F 21 10 00 00 00 00
             └─ controlOption=0x00 (returnControlToECU)
  Response:  7E8#04 6F 21 10 00 00 00 00
```

---

#### STEP 9 — Routine Control (Service 0x31 — REQ-010, REQ-011)

```
Test: REQ-010 — EGR Valve Sweep Test
──────────────────────────────────────
Request Start:   7E0#05 31 01 02 01 05 00 00
                 └─ SID=0x31, Start=0x01, RID=0x0201, param=0x05 (5 cycles)

Response:        7E8#04 71 01 02 01 00 00 00
                 └─ 0x71=positive, routine started

(Wait 10 seconds for 5 cycles to complete — send 3E 80 every 2s)
  3E keepalive: 7E0#02 3E 80 00 00 00 00 00 (no response expected, suppressBit=0x80)

Request Results: 7E0#04 31 03 02 01 00 00 00
                 └─ subFunc=0x03 (requestRoutineResults), RID=0x0201

Response:        7E8#06 71 03 02 01 00 01 00
                 └─ 0x71=positive, status byte=0x00 (PASS), completedCycles=0x01 byte=5

PASS criteria: Results byte[4] = 0x00 (no error code)

──────────────────────────────────────────
Test: REQ-011 — Injector Balance Test (Start/Stop/Result)
──────────────────────────────────────────
Start:    7E0#04 31 01 02 02 00 00 00    → 71 01 02 02 (started)
(run 5s)
Stop:     7E0#04 31 02 02 02 00 00 00    → 71 02 02 02 (stopped)
Result:   7E0#04 31 03 02 02 00 00 00
Response: 7E8#09 71 03 02 02 [Cyl1trim] [Cyl2trim] [Cyl3trim] [Cyl4trim] [status]
          └─ Each trim byte: INT8, 0.1ms/bit, range ±2.0ms (±20 raw)
             status=0x00 → all cylinders balanced
             status=0x01 → Cyl1 out of tolerance
```

---

#### STEP 10 — Read DTCs (Service 0x19 — REQ-014 to REQ-017)

```
Test: REQ-014/015/016/017 — Read All Active Confirmed DTCs
───────────────────────────────────────────────────────────
Request:   7E0#03 19 02 09 00 00 00 00
           └─ subFunc=0x02, statusMask=0x09 (TF+CDTC)

Response (example — 2 DTCs active):
  First Frame:  7E8#10 0B 59 02 09 C0 02 34 09 C0 03
  Flow Control: 7E0#30 00 00 00 00 00 00 00
  Consec 1:     7E8#21 00 08 00 00 00 00 00

  Decoded:
  59 02 09                   → positive response, subFunc=0x02, mask=0x09
  C0 02 34 09                → DTC P0234 (0xC00234), status=0x09 (TF+CDTC confirmed)
  C0 03 00 08                → DTC P0300 (0xC00300), status=0x08 (CDTC only, not currently failing)

PASS criteria for REQ-014..017:
  - All reported DTCs must be from the approved DTC list in the requirement matrix
  - No unlisted DTCs should appear (would indicate unspecified fault)
  - DTC TF/CDTC state must match injected fault conditions

──────────────────────────────────────────
Read Full DTC Count (19 01):
──────────────────────────────────────────
Request:   7E0#03 19 01 0F 00 00 00 00    → mask=0x0F (all failure bits)
Response:  7E8#05 59 01 0F FF 00 02 00
           └─ 0xFF = ISO DTC format, 0x00 = no severity, count = 0x0002 = 2 DTCs

──────────────────────────────────────────
Read Freeze Frame for P0234 (19 04):
──────────────────────────────────────────
Request:   7E0#06 19 04 C0 02 34 01 00
           └─ subFunc=0x04, DTC=0xC00234, record=0x01

Response:  7E8#10 12 59 04 C0 02 34 09 01 [DID 0xF401=speed] [DID 0xF400=RPM] ...
           └─ Freeze frame snapshot: speed=0 kph, RPM=3724, temp=92°C at fault time

──────────────────────────────────────────
Read Extended Data for P0234 (19 06):
──────────────────────────────────────────
Request:   7E0#06 19 06 C0 02 34 01 00

Response:  7E8#08 59 06 C0 02 34 09 01 [occurrence_count] [age_in_cycles]
           └─ occurrence_count=0x03 (failed 3 times), age=0x07 (7 ignition cycles ago)

──────────────────────────────────────────
Read Permanent DTCs (19 18) — REQ-015:
──────────────────────────────────────────
Request:   7E0#02 19 18 00 00 00 00 00

Response A (permanent DTC present):
  7E8#07 59 18 C0 02 34 0F [status]    → DTC P0234 is permanent — cannot be cleared by 14 FF FF FF

Response B (no permanent DTCs — vehicle ready for emissions):
  7E8#03 59 18 00 00 00 00 00           → empty, vehicle passes OBD
```

---

#### STEP 11 — Clear DTCs (Service 0x14 — REQ-014)

```
Test: REQ-014 — Clear All DTCs After Fault Injection Test
──────────────────────────────────────────────────────────
Precondition: Fault injection completed, vehicle not moving
Request:   7E0#04 14 FF FF FF 00 00 00
           └─ groupOfDTC=0xFFFFFF (clear all)

Response:  7E8#01 54 00 00 00 00 00 00
           └─ 0x54=positive — all DTCs cleared

Verify cleared: 19 02 09 → should return 59 02 09 (empty, no DTCs)

NRC scenarios:
  7F 14 22 = conditionsNotCorrect → vehicle moving (speed > 5 kph)
  7F 14 31 = requestOutOfRange    → group code 0xFFFFFF not supported (rare)

Clear specific DTC group only:
  14 C0 02 34    → clear only P0234 (DTC-specific group address)

Note: After clearing, run 19 18 to confirm Permanent DTCs also cleared
      (requires OBD drive cycle if permanent DTCs remain after 19 18)
```

---

#### STEP 12 — Tester Present Keepalive (Service 0x3E)

```
Test: Session maintenance during long test sequences
─────────────────────────────────────────────────────
During any test step > 5 seconds (S3 timer), send periodically:
  Request:   7E0#02 3E 80 00 00 00 00 00
             └─ subFunc=0x80 = suppressPositiveResponse (no echo needed)
             Send every 2000ms (safe margin below S3=5000ms)

If you need to monitor session is still alive:
  Request:   7E0#02 3E 00 00 00 00 00 00
             └─ subFunc=0x00 = normal (expects response)
  Response:  7E8#02 7E 00 00 00 00 00 00
             └─ 0x7E=positive, session confirmed active

CAPL automation:
  on timer tpTimer {
    output(tpMsg_3E80);      // send 3E 80
    setTimer(tpTimer, 2000); // re-arm every 2s
  }
```

---

#### STEP 13 — Control DTC Setting (Service 0x85)

```
Test: Disable DTC logging during actuator tests (prevents false DTCs)
──────────────────────────────────────────────────────────────────────
Turn OFF DTC logging:
  Request:   7E0#02 85 02 00 00 00 00 00
  Response:  7E8#02 C5 02 00 00 00 00 00   → 0xC5=positive

  Now run actuator tests / force inputs — no DTCs will be logged

Turn ON DTC logging:
  Request:   7E0#02 85 01 00 00 00 00 00
  Response:  7E8#02 C5 01 00 00 00 00 00   → 0xC5=positive

  ⚠ Always restore with 85 01 at end of test block!
```

---

#### STEP 14 — ECU Programming Sequence (Services 0x34/0x36/0x37 — REQ-012/013)

```
Test: REQ-012/013 — Full ECU Flash Sequence (SW Update)
─────────────────────────────────────────────────────────
Note: Uses Programming Session (10 02) + Security Level 0x11/0x12

Phase 1 — Unlock programming:
  10 03     → enter extended session
  27 01     → req seed (level 1)
  27 02 [key]  → unlock extended
  10 02     → enter programming session
  27 11     → req seed (programming level)
  27 12 [key]  → unlock programming level   (Key = Seed XOR 0xC3D4E5F6 per REQ-019)

Phase 2 — Prepare ECU:
  28 03 01  → disable Rx+Tx (stop normal CAN comms)
  85 02     → disable DTC setting
  31 01 FF 00 → REQ-012: Erase flash
  Wait for: 71 01 FF 00 or 7F 31 78 (response pending, keep waiting up to 15s)

Phase 3 — Download new software:
  34 00 44 00 08 00 00 00 04 00 00
  └─ SID=0x34, format=0x00, addrLen=0x44 (4+4 bytes)
     startAddress=0x00080000, dataLength=0x00040000 (256KB)

  Response: 74 20 02 00
  └─ 0x74=positive, maxBlockLength = 0x0200 = 512 bytes per block

  36 01 [512 bytes]   → block 1
  76 01               → ack
  36 02 [512 bytes]   → block 2
  76 02               → ack
  ... repeat for all 512 blocks (256KB / 512B = 512 blocks) ...
  36 FF [data]        → block 255
  76 FF               → ack
  36 00 [data]        → block 256 (counter wraps 0xFF→0x00)
  76 00               → ack
  ... continue until all data transferred ...

  37                  → RequestTransferExit
  77                  → positive exit

Phase 4 — Verify and activate:
  31 01 FF 01         → REQ-013: CheckProgrammingDependencies
  Response: 71 01 FF 01 00  → 0x00 = all dependencies OK

  28 00 01            → Re-enable Rx+Tx
  85 01               → Re-enable DTC setting
  11 01               → HardReset — activate new SW

Post-flash verify:
  10 01  → default session
  22 F1 89 → confirm SW version = new version "V2.15.00.00"
  19 02 09 → confirm no DTCs from programming
```

---

#### STEP 15 — Write Calibration Data (Service 0x2E — REQ-009)

```
Test: REQ-009 — Write Injector Trim Cylinder 1 (Engineering Key Required)
──────────────────────────────────────────────────────────────────────────
Precondition: Extended session + Security level 0x05/0x06 unlocked

  27 05 → req seed (level 5, engineering)
  27 06 [key]  → Key = CRC32(Seed || 0xDEADBEEF) per REQ-009 spec

Write trim value:
  Request:   7E0#05 2E D0 10 FF CE 00 00
             └─ DID=0xD010, data=0xFFCE = -50 decimal = -0.50ms trim

  Response:  7E8#03 6E D0 10 00 00 00 00   → positive write

Read back verify:
  Request:   7E0#03 22 D0 10 00 00 00 00
  Response:  7E8#05 62 D0 10 FF CE 00 00   → data matches ✓

Range check from REQ-009: value must be between -2.00ms (0xFF38) and +2.00ms (0x00C8)
  0xFF CE = -0.50ms → within range ✓
```

---

### 23.4 How to Build a Test Case from a Requirement Matrix Row

```
For every row in the Requirement Matrix, create a test case using this template:

┌─────────────────────────────────────────────────────────────┐
│ TEST CASE TEMPLATE                                          │
├─────────────────────────────────────────────────────────────┤
│ TestID:       TC-PCM-027                                    │
│ Requirement:  REQ-003                                       │
│ Service:      0x22 ReadDataByIdentifier                     │
│ Identifier:   DID 0x2101 (TurboBoostPressure)              │
│ Session:      Extended (must enter 10 03 first)             │
│ Security:     Not required (read only)                      │
│ Precondition: Engine running, turbo active (>2000 RPM)      │
├─────────────────────────────────────────────────────────────┤
│ POSITIVE TEST:                                              │
│   Send:     22 21 01                                        │
│   Expect:   62 21 01 [2 data bytes]                         │
│   Validate: (byte[3]<<8 | byte[4]) × 0.01 ∈ [0, 300] kPa  │
├─────────────────────────────────────────────────────────────┤
│ NEGATIVE TEST 1 — Wrong session:                            │
│   Precondition: Stay in Default Session (10 01)             │
│   Send:     22 21 01                                        │
│   Expect:   7F 22 7F (serviceNotSupportedInActiveSession)  │
│             OR 7F 22 7E (subFunctionNotSupportedInSess)    │
├─────────────────────────────────────────────────────────────┤
│ NEGATIVE TEST 2 — Invalid DID:                              │
│   Send:     22 21 FF (DID not in matrix)                    │
│   Expect:   7F 22 31 (requestOutOfRange)                    │
└─────────────────────────────────────────────────────────────┘
```

---

### 23.5 Complete UDS Test Execution Checklist

```
PRE-TEST SETUP
  ☐ Obtain Diagnostic Requirement Matrix (ODX / Excel / Confluence)
  ☐ Extract: all DIDs, RIDs, DTCs, session requirements, security levels
  ☐ Confirm CAN IDs (Request / Response / Functional)
  ☐ Confirm baud rate (typically 500kbit/s or 1Mbit/s for CAN-FD)
  ☐ Set up CANalyzer / CANoe / CAPL script with correct node addresses
  ☐ Confirm security key algorithm from matrix (ask supplier if NDA protected)

BASELINE READ (ALL ECUs)
  ☐ 10 01 → default session positive
  ☐ 22 F1 90 → VIN readable and correct
  ☐ 22 F1 89 → SW version matches expected baseline
  ☐ 22 F1 91 → HW version matches hardware under test
  ☐ 19 02 09 → Zero confirmed DTCs before test start

SESSION + SECURITY TESTS
  ☐ 10 03 → extended session reachable
  ☐ 27 01/02 → security unlock successful
  ☐ 10 01 → fallback to default session (test session timeout)
  ☐ 3E 00 → TesterPresent keepalive working

FUNCTIONAL DID TESTS (per matrix)
  ☐ Read each Read-only DID → verify response format and physical range
  ☐ Read each Read/Write DID → verify readable without security
  ☐ Write each Write DID → verify requires correct session + security
  ☐ Write boundary values → min, max, out-of-range (expect 0x31)
  ☐ Multi-DID read → verify all DIDs in one request respond correctly

ROUTINE CONTROL TESTS (per matrix)
  ☐ Start each RID → verify 71 positive or 7F with correct NRC
  ☐ For timed routines: verify 0x78 NRC during execution
  ☐ Request results → verify result format matches matrix
  ☐ Stop routine (if applicable) → verify stop acknowledged

DTC TESTS (per matrix)
  ☐ 19 02 09 → zero DTCs at start (clean state)
  ☐ Inject each fault → verify correct DTC appears with correct status
  ☐ 19 04 [dtc] 01 → freeze frame captured, values match fault conditions
  ☐ 19 06 [dtc] 01 → extended data: occurrence counter increments
  ☐ 14 FF FF FF → clear all DTCs
  ☐ 19 02 09 → verify cleared
  ☐ 19 18 → verify no permanent DTCs (or drive cycle if present)

ACTUATOR / IO CONTROL TESTS
  ☐ 2F shortTermAdjustment → actuator responds to forced value
  ☐ 2F returnControlToECU → actuator returns to ECU control
  ☐ 85 02 before test → no fault DTCs during forced operation
  ☐ 85 01 after test → DTC logging restored

POST-TEST CLEANUP
  ☐ 2F 00 → return all IO controls to ECU
  ☐ 85 01 → re-enable DTC setting
  ☐ 28 00 01 → re-enable all CAN communication
  ☐ 14 FF FF FF → clear any test-induced DTCs
  ☐ 10 01 → return to default session
  ☐ 22 F1 89 → confirm no SW changes unexpectedly
  ☐ 19 02 09 → final DTC check = 0
```

---

### 23.6 Requirement Traceability Map

```
Requirement Matrix Row → Test Case → Pass/Fail Result → Test Report

REQ-001 (VIN DID 0xF190)   → TC-PCM-001 → PASS  → Report line 1
REQ-002 (SW DID 0xF189)    → TC-PCM-002 → PASS  → Report line 2
REQ-003 (TurboBoost 0x2101)→ TC-PCM-003 → PASS  → Report line 3
REQ-004 (FuelRail 0x2102)  → TC-PCM-004 → PASS  → Report line 4
REQ-005 (OilTemp 0x2103)   → TC-PCM-005 → PASS  → Report line 5
REQ-006 (Throttle 0x2104)  → TC-PCM-006 → PASS  → Report line 6
REQ-007 (Variant 0xD001)   → TC-PCM-007 → PASS  → Report line 7
REQ-008 (Immob 0xD002)     → TC-PCM-008 → PASS  → Report line 8
REQ-009 (InjTrim 0xD010)   → TC-PCM-009 → PASS  → Report line 9
REQ-010 (EGR RID 0x0201)   → TC-PCM-010 → PASS  → Report line 10
REQ-011 (Injbal RID 0x0202)→ TC-PCM-011 → PASS  → Report line 11
REQ-012 (Erase RID 0xFF00) → TC-PCM-012 → PASS  → Report line 12
REQ-013 (ProgDep 0xFF01)   → TC-PCM-013 → PASS  → Report line 13
REQ-014 (DTC P0087)        → TC-PCM-014 → PASS  → Report line 14
REQ-015 (DTC P0234)        → TC-PCM-015 → PASS  → Report line 15
REQ-016 (DTC P0300)        → TC-PCM-016 → PASS  → Report line 16
REQ-017 (DTC U0100)        → TC-PCM-017 → PASS  → Report line 17
REQ-018 (Session 10 03)    → TC-PCM-018 → PASS  → Report line 18
REQ-019 (Session 10 02)    → TC-PCM-019 → PASS  → Report line 19
REQ-020 (Security 27 03/04)→ TC-PCM-020 → PASS  → Report line 20

Coverage: 20/20 requirements tested = 100% requirement coverage
```

---

*File: 01_uds_complete_guide.md | UDS ISO 14229 Complete Reference | April 2026*
