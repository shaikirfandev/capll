# XCP Protocol Study Material
## Universal Measurement and Calibration Protocol (ASAM MCD-1 XCP)

---

## 1. What is XCP?

**XCP** (Universal Measurement and Calibration Protocol) is an automotive communication standard defined by **ASAM** (Association for Standardisation of Automation and Measuring Systems) in the **MCD-1 XCP** specification.

It enables:
- **Measurement**: Reading ECU internal variables at runtime (DAQ — Data Acquisition)
- **Calibration**: Writing new parameter values to ECU memory (offline or online)
- **Flash Programming**: Downloading firmware to ECU

**XCP transports supported:** CAN / CAN FD / Ethernet (TCP/UDP) / FlexRay / USB / SPI

---

## 2. Key Concepts

| Concept | Description |
|---------|-------------|
| **A2L file** | ASAM MCD-2 MC description file — maps variable names to ECU memory addresses, data types, conversion rules |
| **MTA** | Memory Transfer Address — pointer set before upload/download |
| **DAQ** | Data Acquisition — ECU pushes measurement data periodically |
| **STIM** | Stimulation — tester sends data to ECU (bypass/stimulation testing) |
| **Seed & Key** | Security authentication before calibration access |
| **Cal Page** | Memory page for calibration data (ROM = default, RAM = active) |
| **CTO** | Command Transfer Object — command frames (tester → ECU) |
| **DTO** | Data Transfer Object — response/event frames (ECU → tester) |

---

## 3. XCP Frame Structure (CAN)

### CTO (Command) Frame
```
Byte 0:  Command Code (0xFF=CONNECT, 0xF0=DOWNLOAD, 0xF5=UPLOAD, ...)
Byte 1:  Command-specific parameter
...
Byte 7:  Command-specific parameter
```

### DTO (Response) Frame
```
Byte 0:  0xFF = Positive Response | 0xFE = Error | 0xFD = Event
Byte 1:  Response-specific data (or error code)
...
Byte 7:  Response-specific data
```

---

## 4. XCP Commands Reference

### Connection Management
| Command | Code | Direction | Description |
|---------|------|-----------|-------------|
| CONNECT | 0xFF | M→S | Establish XCP session |
| DISCONNECT | 0xFE | M→S | End XCP session |
| GET_STATUS | 0xFD | M→S | Read session status |
| SYNCH | 0xFC | M→S | Synchronize after error |
| GET_COMM_MODE_INFO | 0xFB | M→S | Get communication parameters |

### Memory Transfer
| Command | Code | Direction | Description |
|---------|------|-----------|-------------|
| SET_MTA | 0xF6 | M→S | Set Memory Transfer Address |
| UPLOAD | 0xF5 | M→S | Read N bytes from MTA |
| SHORT_UPLOAD | 0xF4 | M→S | Read N bytes from explicit address |
| DOWNLOAD | 0xF0 | M→S | Write N bytes to MTA |
| SHORT_DOWNLOAD | 0xED | M→S | Write N bytes to explicit address |
| DOWNLOAD_NEXT | 0xEF | M→S | Continue multi-frame download |
| MODIFY_BITS | 0xEC | M→S | Bit-level modification |

### Calibration Page Management
| Command | Code | Description |
|---------|------|-------------|
| GET_CAL_PAGE | 0xEA | Read active calibration page |
| SET_CAL_PAGE | 0xEB | Switch active calibration page |
| COPY_CAL_PAGE | 0xE4 | Copy ROM → RAM |
| CLEAR_DAQ_LIST | 0xE3 | Clear DAQ list |

### DAQ (Measurement)
| Command | Code | Description |
|---------|------|-------------|
| GET_DAQ_PROCESSOR_INFO | 0xDA | DAQ capabilities |
| GET_DAQ_RESOLUTION_INFO | 0xD9 | Timestamp resolution |
| SET_DAQ_PTR | 0xE2 | Set DAQ pointer |
| WRITE_DAQ | 0xE1 | Write DAQ entry |
| SET_DAQ_LIST_MODE | 0xE0 | Configure DAQ mode |
| START_STOP_DAQ_LIST | 0xDE | Start/stop DAQ |
| START_STOP_SYNCH | 0xDD | Synchronized start/stop |

### Security
| Command | Code | Description |
|---------|------|-------------|
| GET_SEED | 0xF7 | Request seed for seed-key auth |
| UNLOCK | 0xF6 | Send computed key to unlock |

---

## 5. XCP Session Flow

```
Tester                              ECU (XCP Slave)
  │                                     │
  │─── CONNECT (0xFF, mode=0x00) ──────►│
  │◄── CONNECT_RESPONSE (0xFF, ...) ────│
  │    [MaxDTO, MaxCTO, ProtVer]         │
  │                                     │
  │─── GET_STATUS (0xFD) ──────────────►│
  │◄── STATUS_RESPONSE ─────────────────│
  │                                     │
  │─── GET_SEED (resource=CAL) ────────►│  (if protected)
  │◄── SEED bytes ──────────────────────│
  │─── UNLOCK (computed key) ──────────►│
  │◄── UNLOCK_RESPONSE ─────────────────│
  │                                     │
  │─── SET_MTA (addr=0x20001000) ──────►│  (point to IdleRPM)
  │◄── SET_MTA_RESPONSE ────────────────│
  │                                     │
  │─── UPLOAD (4 bytes) ───────────────►│  (read IdleRPM)
  │◄── 00 00 02 EE (= 750 RPM) ────────│
  │                                     │
  │─── SET_MTA (addr=0x20001000) ──────►│  (before write)
  │─── DOWNLOAD (4 bytes, new=800) ────►│
  │◄── DOWNLOAD_RESPONSE ───────────────│
  │                                     │
  │─── DISCONNECT (0xFE) ──────────────►│
  │◄── DISCONNECT_RESPONSE ─────────────│
```

---

## 6. A2L File Structure

The A2L file describes ALL measurable / calibratable variables:

```
/begin PROJECT EngineController ""
  /begin MODULE ECM ""

    /begin MOD_PAR ""
      ADDR_EPK 0x20000000
    /end MOD_PAR

    /begin MEASUREMENT EngineSpeed
      "Engine speed in RPM"
      FLOAT32_IEEE                   /* data type */
      ConvRPM                        /* conversion method */
      1 0                            /* precision, resolution */
      0 8000                         /* min, max */
      ECU_ADDRESS 0x20002000
    /end MEASUREMENT

    /begin CHARACTERISTIC IdleRPM
      "Idle speed setpoint"
      VALUE                          /* type: single value */
      0x20001000                     /* address */
      /deposit ABSOLUTE
      ConvRPM
      700 900                        /* min, max */
    /end CHARACTERISTIC

    /begin COMPU_METHOD ConvRPM
      "RPM conversion"
      TAB_NOINTP ""
      "%6.1" "rpm"
      COEFFS 0 1 0 0 0 0.25         /* f(x) = 0.25 * x */
    /end COMPU_METHOD

  /end MODULE
/end PROJECT
```

---

## 7. DAQ-based Measurement Example (CAPL)

```capl
// DAQ: ECU continuously pushes EngineSpeed every 10ms
// Tester configures the DAQ list, then receives DTOs

void ConfigureDAQ()
{
  // 1. Clear existing DAQ list
  XCP_Send(0xE3, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);

  // 2. Set DAQ pointer (list=0, odt=0, entry=0)
  XCP_Send(0xE2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);

  // 3. Write DAQ entry (address of EngineSpeed=0x20002000, size=4)
  XCP_Send(0xE1, 0x04, 0x00, 0x00, 0x00, 0x20, 0x00, 0x20);

  // 4. Set DAQ list mode (event=0x01, prescaler=1)
  XCP_Send(0xE0, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00);

  // 5. Start DAQ list 0
  XCP_Send(0xDE, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
}

// Incoming DAQ DTO (~10ms period)
on message XCP_RX_ID
{
  if (this.byte(0) == 0xFF || this.byte(0) == 0x00)  // DAQ data packet
  {
    long rpm_raw = ((long)this.byte(1) << 24) | ((long)this.byte(2) << 16) |
                  ((long)this.byte(3) << 8) | this.byte(4);
    float rpm    = rpm_raw * 0.25;
    write("DAQ EngineSpeed: %.1f RPM", rpm);
  }
}
```

---

## 8. Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00 | ERR_CMD_SYNCH | Resynchronize needed |
| 0x10 | ERR_CMD_BUSY | Command processor busy |
| 0x11 | ERR_DAQ_ACTIVE | DAQ is running, cannot modify |
| 0x12 | ERR_PGM_ACTIVE | Programming active |
| 0x20 | ERR_CMD_UNKNOWN | Command not implemented |
| 0x21 | ERR_CMD_SYNTAX | Parameter out of range |
| 0x22 | ERR_OUT_OF_RANGE | Value out of allowed range |
| 0x23 | ERR_WRITE_PROTECTED | Memory is write-protected |
| 0x24 | ERR_ACCESS_DENIED | Resource protected, seed-key needed |
| 0x25 | ERR_ACCESS_LOCKED | Seed requested but not unlocked |
| 0x26 | ERR_PAGE_NOT_VALID | Page does not exist |
| 0x29 | ERR_SEQUENCE | Incorrect sequence of commands |
| 0x30 | ERR_DAQ_CONFIG | DAQ configuration invalid |

---

## 9. XCP Tools

| Tool | Vendor | Purpose |
|------|--------|---------|
| **CANape** | Vector | Primary XCP measurement+calibration tool (A2L-based) |
| **INCA** | ETAS | ECU development and calibration |
| **MDA** | Vector | Offline measurement data analysis |
| **vSignalyzer** | Vector | Signal analysis |
| **CANalyzer with XCP plugin** | Vector | Protocol analysis |
| **python-xcp** | Open source | Python XCP client |

---

## 10. XCP Interview Questions & Answers

**Q: What is the difference between UPLOAD and SHORT_UPLOAD?**
> UPLOAD reads N bytes from the current MTA (set by SET_MTA beforehand). SHORT_UPLOAD reads N bytes from an explicit address provided in the same command — no prior SET_MTA needed (if 6 address bytes fit in the CTO).

**Q: What is an A2L file and why is it needed?**
> A2L (ASAM MCD-2 MC) is a text file describing all measurable and calibratable ECU variables with their memory addresses, data types, conversion formulas, min/max ranges, and display units. Without it, XCP can only transfer raw bytes — the A2L maps those bytes to meaningful engineering values.

**Q: What is the difference between CAL page 0 (ROM) and page 1 (RAM)?**
> ROM page contains the original factory calibration (read-only). RAM page is a copy in volatile memory that can be modified during a session. Changes in RAM are lost on ECU reset unless explicitly saved to NVM with a PROGRAM command.

**Q: How does Seed & Key work in XCP?**
> If a resource (e.g., PGM or CAL) is protected: tester sends GET_SEED → ECU returns a random seed → tester computes the key using the OEM algorithm → tester sends UNLOCK with the key → ECU grants access if key matches.

**Q: What is DAQ mode vs. polling mode?**
> Polling: tester actively requests data with UPLOAD at its own rate — high bus load, slower. DAQ: ECU is configured to automatically push measurement data at ECU-controlled timestamps — lower latency, synchronized with ECU task scheduler, prefers for high-frequency signals.
