# XCP Calibration Protocol — Complete Guide
## XCP on CAN/CAN FD | A2L Files | CANape Workflow

---

## 1. XCP Overview

**XCP (Universal Measurement and Calibration Protocol)** enables:
- **Measurement:** Reading ECU internal variables during runtime (online measurement)
- **Calibration:** Writing ECU parameters at runtime (online calibration)

XCP replaces the older CCP (CAN Calibration Protocol) and supports multiple transports:
- XCP on CAN
- XCP on CAN FD
- XCP on Ethernet (UDP/TCP)
- XCP on FlexRay

**Tool:** Vector CANape, ETAS INCA

---

## 2. Core Concepts

| Concept | Description |
|---------|-------------|
| **Slave** | ECU being calibrated/measured |
| **Master** | PC-based tool (CANape/INCA) |
| **CTO** | Command Transfer Object — master → slave commands |
| **DTO** | Data Transfer Object — slave → master responses & DAQ data |
| **A2L** | ASAM MDF database file describing ECU memory layout |
| **MTA** | Memory Transfer Address — pointer for READ/WRITE operations |
| **DAQ** | Data Acquisition — periodic measurement from ECU |
| **STIM** | Stimulation — periodic write to ECU (bypass) |

---

## 3. XCP CAN Frame Layout

### Command (Master → Slave): CTO
```
Byte 0:  Command Code (e.g., 0xFF = CONNECT)
Byte 1+: Command parameters
```

### Response (Slave → Master): CTO Response
```
Byte 0:  0xFF = Positive Response
         0xFE = Error Response
Byte 1:  Error code (if 0xFE)
Byte 2+: Response data
```

### DAQ (Slave → Master): DTO
```
Byte 0:  Identification (DAQ list number / timestamp)
Byte 1+: Measurement data
```

---

## 4. XCP Command Set

| Command | Hex | Description |
|---------|-----|-------------|
| CONNECT | 0xFF | Establish XCP session, get slave capabilities |
| DISCONNECT | 0xFE | End XCP session |
| GET_STATUS | 0xFD | Session status, protection status |
| SYNCH | 0xFC | Re-synchronize slave |
| GET_COMM_MODE_INFO | 0xFB | Block mode, interleaved mode info |
| GET_ID | 0xFA | Request identification (A2L filename) |
| SET_MTA | 0xF6 | Set Memory Transfer Address |
| UPLOAD | 0xF5 | Read n bytes from current MTA |
| SHORT_UPLOAD | 0xF4 | Read up to 6 bytes from address |
| DOWNLOAD | 0xF0 | Write n bytes to current MTA |
| SHORT_DOWNLOAD | 0xED | Write up to 6 bytes to address |
| MODIFY_BITS | 0xEC | Read-modify-write bit field |
| SET_CAL_PAGE | 0xEB | Select RAM or ROM cal page |
| GET_CAL_PAGE | 0xEA | Query active calibration page |
| CLEAR_DAQ_LIST | 0xE3 | Remove all entries from DAQ list |
| SET_DAQ_PTR | 0xE2 | Set pointer to DAQ list/ODT/entry |
| WRITE_DAQ | 0xE1 | Write DAQ entry (address, length) |
| SET_DAQ_LIST_MODE | 0xE0 | Configure DAQ list timing/mode |
| GET_DAQ_LIST_MODE | 0xDF | Query DAQ list configuration |
| START_STOP_DAQ_LIST | 0xDE | Start/stop individual DAQ list |
| START_STOP_SYNCH | 0xDD | Start/stop all DAQ lists together |
| TIME_CORRELATION | 0xC6 | Synchronize ECU and tool clocks |
| UNLOCK | 0xF1 | Provide seed response to unlock protection |
| GET_SEED | 0xF2 | Obtain seed for security unlock |

---

## 5. XCP Session Flow

```
Master                          Slave (ECU)
  |                                  |
  |-------- CONNECT(0xFF) ---------> |
  | <------- Response (caps) ------- |
  |                                  |
  |-------- GET_STATUS(0xFD) ------> |
  | <------- Status response ------- |
  |                                  |
  |--- SET_MTA(addr=0x20001000) ---> |
  | <------- Positive response ----- |
  |                                  |
  |--- SHORT_UPLOAD(len=4) --------> |  (Read 4 bytes from address)
  | <------- [0xFF, B0, B1, B2, B3] |
  |                                  |
  |--- SHORT_DOWNLOAD(val, addr) --> |  (Write new value)
  | <------- Positive response ----- |
  |                                  |
  |-------- DISCONNECT(0xFE) ------> |
```

---

## 6. DAQ Configuration Flow (Periodic Measurement)

```
1. CLEAR_DAQ_LIST(daq_num)          — Clear list
2. SET_DAQ_PTR(daq_num, odt=0, entry=0) — Point to first entry
3. WRITE_DAQ(addr, size)            — Write first variable address
4. SET_DAQ_PTR(daq_num, odt=0, entry=1)
5. WRITE_DAQ(addr2, size2)          — Write second variable address
6. SET_DAQ_LIST_MODE(mode, event, prescaler) — Set timing
7. START_STOP_SYNCH(START_ALL)      — Begin measurement
   → ECU sends DTO packets periodically
8. START_STOP_SYNCH(STOP_ALL)       — End measurement
```

---

## 7. A2L File Structure

The **A2L** (ASAM MDF 2-Link) file describes ECU internal variables:

```
/begin PROJECT MyECU ""
  /begin MODULE Engine_ECU ""

    /begin MEASUREMENT EngineSpeed
      "Engine speed in RPM"
      FLOAT32_IEEE ADDRESS_TYPE %6.1
      ECU_ADDRESS 0x20001000
      ECU_ADDRESS_EXTENSION 0x00
      LOWER_LIMIT 0
      UPPER_LIMIT 8000
      UNIT "rpm"
    /end MEASUREMENT

    /begin CHARACTERISTIC IdleRPM_Setpoint
      "Target idle RPM"
      VALUE 0x20002000 DEPOSIT_VALUE 0 "" NO_AXIS_PTS_X 1 0 0 6000 1
      LOWER_LIMIT 500
      UPPER_LIMIT 1500
      UNIT "rpm"
    /end CHARACTERISTIC

    /begin MAP FuelMap_Load_Speed
      "Fuel injection map vs load and speed"
      0x20003000 DEPOSIT_VALUE 0 "" 16 12 0 0 100 1
      LOWER_LIMIT 0
      UPPER_LIMIT 100
    /end MAP

  /end MODULE
/end PROJECT
```

---

## 8. CANape Workflow

1. **Open CANape** → New project → Configure CAN channel
2. **Load A2L file** → All measurements and characteristics auto-imported
3. **Connect to ECU** → CANape sends CONNECT command
4. **Online Measurement:**
   - Drag-drop signals from Symbol Browser to oscilloscope/table
   - CANape configures DAQ automatically
5. **Online Calibration:**
   - Open MAP/CURVE editor
   - Modify values → CANape issues SHORT_DOWNLOAD
   - Save to ECU RAM (volatile) or flash working page
6. **Page Switching (ROM ↔ RAM):**
   - ECU has ROM (default) and RAM (working) calibration page
   - SET_CAL_PAGE switches between them
   - "Flash" operation programs RAM to internal flash

---

## 9. XCP Security (SEED & KEY)

ECUs may protect calibration with seed-key mechanism:

```
Master                    Slave
  |--- GET_SEED(resource) -> |
  | <---- Seed [4 bytes] --- |
  |                          |
  | Apply key algorithm:     |
  | key = algo(seed, secret) |
  |                          |
  |--- UNLOCK(key) --------> |
  | <---- Access granted --- |
```

The `XCPsim.dll` or custom DLL provides the key computation algorithm.

---

## 10. Interview Q&A

**Q: What is the difference between XCP UPLOAD and SHORT_UPLOAD?**
> UPLOAD reads n bytes starting from the current MTA (requires a prior SET_MTA command). SHORT_UPLOAD includes the address directly in the command and reads up to 6 bytes — no need for a separate SET_MTA.

**Q: What is an ODT in XCP DAQ?**
> ODT (Object Descriptor Table) is a group of variables to be measured together in one DTO packet. Each DAQ list contains one or more ODTs. Each ODT fits in one CAN frame (up to 7 bytes of data on CAN 2.0, or more on CAN FD).

**Q: What is the purpose of cal page switching?**
> ECUs have a ROM calibration page (production data, read-only) and a RAM working page (modifiable). During calibration, engineers work on the RAM page. SET_CAL_PAGE switches between ROM and RAM. Once calibration is validated, the working page is flashed to production ROM.

**Q: How does XCP differ from UDS for ECU parameter access?**
> UDS (ISO 14229) is designed for diagnostics: reading/writing Data IDs (DIDs) through services like 0x22/0x2E — it's not optimized for high-speed real-time access. XCP is designed for **calibration and measurement** — direct memory access with minimal overhead, supporting high-rate periodic DAQ. XCP knows the ECU's internal memory addresses via the A2L file.
