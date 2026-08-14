# Part 9 — ECU Flashing & Deployment

---

## 9.1 What is ECU Flashing?

ECU flashing (also called ECU programming or reprogramming) is the process of writing new firmware to an ECU's flash memory.

This is done:
- During vehicle production (end-of-line programming)
- At the dealership (software updates, recall fixes)
- During development (daily builds, integration testing)
- Via OTA (vehicles in the field)

---

## 9.2 Memory Types

| Memory | Purpose | Volatile |
|---|---|---|
| Flash (NOR/NAND) | Application code, calibration data | No |
| EEPROM | Configuration, NvM parameters | No |
| RAM (SRAM, DRAM) | Runtime stack, heap, variables | Yes |
| OTP (One-Time Programmable) | Security keys, ECU identity | No |

### Flash Layout Example (AUTOSAR ECU)

```
Flash Memory Layout:
+-------------------------+ 0x00000000
|     Bootloader          |  (read-protected, signed)
+-------------------------+ 0x00008000
|     Startup Code        |
+-------------------------+ 0x00010000
|     Application Code    |
|     (BSW + SWCs)        |
+-------------------------+ 0x000F0000
|     Calibration Data    |  (A2L-referenced)
+-------------------------+ 0x000FC000
|     Configuration Data  |  (NvM data, checksums)
+-------------------------+ 0x000FFFFF
```

---

## 9.3 Flash File Formats

| Format | Description | Use |
|---|---|---|
| HEX (Intel HEX) | ASCII hex records with address and data | MCU flashing |
| SREC (Motorola S-record) | Similar to Intel HEX, Motorola format | MCU flashing |
| BIN | Raw binary, no address info | Linux/embedded flashing |
| ELF | Executable and Linkable Format, debug info included | Development/debug |
| A2L | ASAP2 description file (ETAS/CANape) | Calibration measurement |
| ODX/PDXA | Diagnostic data format (OEM/Tier-1) | UDS flashing scripts |

---

## 9.4 Bootloader Roles

### Primary Bootloader
- First code to execute on power-up
- Initializes clocks, memory, watchdog
- Checks application integrity (CRC/signature)
- Decides: jump to application OR enter programming mode

### Secondary Bootloader (for flashing)
- Entered when primary detects programming request
- Implements UDS services: RequestDownload (0x34), TransferData (0x36), RequestTransferExit (0x37)
- Receives new firmware via CAN/Ethernet
- Writes to flash
- Verifies checksum/signature after write

### Boot Decision Logic

```
Power ON
   ↓
Initialize hardware
   ↓
Check "programming mode" flag in NvM?
   YES → Start secondary bootloader
    ↓
Verify application CRC/signature
   VALID → Jump to application
   INVALID → Start secondary bootloader (recovery mode)
```

---

## 9.5 ECU Programming Session (UDS Flashing)

Flashing uses UDS (ISO 14229) services over CAN TP (ISO 15765-2) or DoIP.

### Standard UDS Flashing Sequence

```
Tester                    ECU
  |                         |
  |--DiagSessionControl(0x87 ProgrammingSession)-->|
  |<--Positive Response (0x50)---------------------|
  |                         |
  |--SecurityAccess(Seed Request 0x27 0x11)-------->|
  |<--Seed Response (0x67 0x11 + seed)-------------|
  |--SecurityAccess(Key 0x27 0x12 + key)----------->|
  |<--Positive Response (0x67 0x12)----------------|
  |                         |
  |--WriteDataByIdentifier(FingerprintData)-------->|
  |<--Positive Response--__________________________|
  |                         |
  |--EraseMemory(RoutineControl 0x31)-------------->|
  |<--Positive Response--__________________________|
  |                         |
  |--RequestDownload(0x34, addressLength, size)---->|
  |<--Positive Response (blockSize)----------------|
  |                         |
  | [loop: send 0xF0 block size chunks]            |
  |--TransferData(0x36, blockSeqNum, data)--------->|
  |<--Positive Response(0x76)----------------------|
  |                         |
  |--RequestTransferExit(0x37)--------------------->|
  |<--Positive Response (0x77)---------------------|
  |                         |
  |--CheckProgrammingDependencies(RoutineCtrl)----->|
  |<--Positive Response----------------------------|
  |                         |
  |--ECUReset(0x11 HardReset)---------------------->|
  |     (ECU reboots with new software)            |
```

---

## 9.6 Secure Flashing

### Why Secure Flashing?
Prevents malicious or corrupted firmware from being flashed to vehicle ECUs.

### Security Mechanisms

| Mechanism | Description |
|---|---|
| Security Access | Seed/key challenge (UDS 0x27) — prevents unauthorized sessions |
| Digital Signature | Firmware signed with OEM private key; ECU verifies with public key |
| CRC/Checksum | Detects data corruption during transfer |
| Encryption | Firmware package encrypted for confidentiality |
| Rollback Protection | Prevents downgrading to vulnerable firmware version |
| Anti-replay | Timestamp or nonce in flashing protocol prevents replay attacks |

### Signature Verification Flow

```
OEM signs firmware:
  firmware_binary + SHA256 hash → RSA/ECDSA sign with OEM private key → .signature file

ECU verifies:
  Received firmware → SHA256 hash → RSA/ECDSA verify using OEM public key (stored in OTP)
  Match → proceed with flashing
  No match → reject, set DTC, stay in recovery
```

---

## 9.7 Tools for ECU Flashing

| Tool | Vendor | Use |
|---|---|---|
| CANoe with Diagnostic Feature Set | Vector | UDS flashing scripts, automation |
| CANape | Vector | Calibration flashing (A2L based) |
| Lauterbach Trace32 | Lauterbach | JTAG/SWD direct flash, debug |
| dSPACE | dSPACE | HIL-connected flashing |
| ETAS INCA | ETAS | Calibration and measurement |
| EB tresos | Elektrobit | AUTOSAR BSW flashing configuration |
| Vendor tools | MCU vendor (NXP, Renesas) | Direct flash via proprietary tool |
| python-uds | Open source | Python UDS flashing scripts |

---

## 9.8 A2L (Calibration Description File)

A2L files describe ECU calibration parameters:
- Parameter names, addresses in flash, data types
- Measurement variables (live data)
- Used by CANape/INCA for runtime calibration

```
/begin MEASUREMENT EngineSpeed
  LONG_IDENTIFIER "Engine speed in RPM"
  DATATYPE UWORD
  ECU_ADDRESS 0x40001234
  CONVERSION EngineSpeedConversion
/end MEASUREMENT
```

---

## 9.9 End-of-Line (EOL) Programming

At the vehicle production line:
1. Vehicle ECUs programmed via vehicle OBD port
2. Automated flasher connects to OBDII connector
3. Production test system uploads software packages to all ECUs
4. Automated test runs post-flash validation (CRC check, basic function test)
5. VIN coded to ECUs
6. ECU specific adaptations (wheel size, market variant) configured

---

## 9.10 Recovery and Rollback

If flashing fails or application is invalid:

```
Bootloader detects: CRC invalid after flash attempt
  → Keep recovery/bootloader active
  → Set DTC "ECU Software Invalid"
  → Wait for reflash attempt

OR with dual-bank flash:
  Bank A: current running firmware
  Bank B: new firmware (being written)
  After successful write to B:
    → Switch boot bank to B
    → First boot validates B
    → If validation fails → switch back to A (rollback)
```

---

## Summary

| Topic | Key Points |
|---|---|
| Flash memory | NOR Flash for code, EEPROM for NvM params |
| File formats | HEX, SREC for MCU; BIN for Linux |
| Bootloader | Integrity check, programming mode entry |
| UDS flashing | Session → Security → Erase → Download → Transfer → Exit |
| Secure flashing | Signature, encryption, CRC, rollback protection |
| Tools | CANoe, CANape, Trace32, python-uds |
| Calibration | A2L files, CANape/INCA |

---

*Next: [Part 10 — Diagnostics Integration](part-10-diagnostics.md)*
