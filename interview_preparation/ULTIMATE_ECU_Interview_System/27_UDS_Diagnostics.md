# UDS Diagnostics Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

UDS (Unified Diagnostic Services, ISO 14229) is the **universal diagnostic protocol** for all modern automotive ECUs. If you work on ECU testing, validation, telematics, or ADAS, you will be tested on UDS. Senior engineers are expected to know the full service hierarchy, error response codes, and implementation details.

**Key areas probed:**
- UDS service IDs, request/response format
- Session management (default, programming, extended)
- Security Access (seed/key, algorithm)
- DTC management (Dem, freeze frames, status bits)
- Data reading (0x22) and writing (0x2E)
- Firmware download via UDS (0x34/0x36/0x37/0x31)
- ISO-TP transport layer
- Negative Response Codes (NRC) and their meanings
- Implementation in AUTOSAR DCM

---

## BEGINNER QUESTIONS

---

### Q1. What is UDS and how is it structured? Explain the request/response format.

**Short Answer:** UDS (ISO 14229-1) defines a set of diagnostic services used by test tools to communicate with ECUs. Each service has a request SID (Service Identifier) and a positive response SID = request SID + 0x40. Negative responses use SID 0x7F.

**Detailed Expert Answer:**

```
UDS Request/Response Format (over ISO-TP):

Request:  [SID] [Sub-function or Data] ...
Response: [SID+0x40] [Sub-function or Data] ...  (positive)
          [0x7F] [SID] [NRC]                      (negative)

Example 1: Read VIN (0x22 ReadDataByIdentifier)
  Request:  [0x22][0xF1][0x90]
                         ↑ DID 0xF190 = VIN
  Positive: [0x62][0xF1][0x90][W1][W2]...[W17]
             ↑0x22+0x40=0x62
  Negative: [0x7F][0x22][0x31]
                          ↑ NRC 0x31 = requestOutOfRange

Example 2: Diagnostic Session Control (0x10)
  Request:  [0x10][0x01]  → Default Session
  Request:  [0x10][0x02]  → Programming Session
  Request:  [0x10][0x03]  → Extended Diagnostic Session
  Positive: [0x50][0x0X][P2_high][P2_low][P2star_high][P2star_low]
              ↑0x10+0x40    ↑session  ↑P2=25ms default  ↑P2*=5000ms

P2 and P2* timing:
  P2: maximum time between request and start of response = 50ms (default)
  P2*: extended timing (long operations) = 5 seconds
  If ECU needs more time: send [0x7F][SID][0x78] (NRC 0x78 = requestCorrectlyReceivedResponsePending)
```

**UDS service overview:**

| SID | Service | Typical Usage |
|-----|---------|--------------|
| 0x10 | DiagnosticSessionControl | Switch to programming/extended session |
| 0x11 | ECUReset | Soft/hard/keyOffOnReset |
| 0x14 | ClearDiagnosticInformation | Clear all DTCs |
| 0x19 | ReadDTCInformation | Read DTCs by status mask |
| 0x22 | ReadDataByIdentifier | Read VIN, software version, live data |
| 0x27 | SecurityAccess | Unlock ECU for reprogramming |
| 0x28 | CommunicationControl | Disable/enable normal communication |
| 0x2E | WriteDataByIdentifier | Write VIN, calibration data |
| 0x31 | RoutineControl | Start/stop/request routine (erase flash) |
| 0x34 | RequestDownload | Initiate firmware download |
| 0x36 | TransferData | Transfer data blocks |
| 0x37 | RequestTransferExit | Complete download, verify |
| 0x3D | WriteMemoryByAddress | Write to specific memory address |
| 0x3E | TesterPresent | Keep ECU in non-default session |
| 0x85 | ControlDTCSetting | Enable/disable DTC storage |

---

### Q2. Explain Security Access (0x27) — how does seed/key work?

**Short Answer:** Security Access is a challenge-response mechanism. ECU sends a 4-byte seed; the tester applies a secret algorithm and returns the key. If key matches, ECU unlocks. Prevents unauthorised programming.

**Detailed Expert Answer:**

```
Security Access Flow:

Tester → ECU: [0x27][0x01]  (RequestSeed, level 1 = programming unlock)
ECU → Tester: [0x67][0x01][S1][S2][S3][S4]  (seed = 4 bytes)
              If seed = 0x00000000 → ECU already unlocked (no key needed)

Tester applies algorithm to seed → calculates key
Key example (simple XOR): key = seed ^ 0xDEADBEEF

Tester → ECU: [0x27][0x02][K1][K2][K3][K4]  (SendKey)
ECU verifies: if (received_key == expected_key) → unlock ✓
ECU → Tester: [0x67][0x02]  (positive response — unlocked!)
              Or: [0x7F][0x27][0x35]  (NRC 0x35 = invalidKey)
```

**Failure handling:**
```
After 3 consecutive invalid keys → NRC 0x36 (exceededNumberOfAttempts)
ECU locks for a delay period (e.g., 10 seconds) → NRC 0x37 (requiredTimeDelayNotExpired)
```

**Real algorithm types (from automotive specs):**
```c
/* Simple: NOT the seed (early prototype ECUs, not secure!) */
uint32_t calc_key_simple(uint32_t seed) {
    return ~seed;
}

/* XOR with constant (better, but still breakable) */
uint32_t calc_key_xor(uint32_t seed, uint32_t secret) {
    return seed ^ secret;  /* secret = 0xA5B6C7D8 (OEM-specific) */
}

/* AUTOSAR SecOC style — HMAC-based (production-grade) */
void calc_key_hmac(const uint8_t *seed, uint8_t seed_len,
                   const uint8_t *oem_secret, uint8_t secret_len,
                   uint8_t *key_out, uint8_t key_len) {
    /* HMAC-SHA256 truncated to key_len bytes */
    hmac_sha256(oem_secret, secret_len, seed, seed_len, key_out);
    /* OEM secret stored in HSM — never in plain flash */
}
```

**Access levels:**
```
Level 0x01/0x02: Programming session unlock (write firmware, calibration)
Level 0x03/0x04: Extended session unlock (advanced parameters)
Level 0x11/0x12: ECU-specific (e.g., VIN write, feature coding)
Odd = RequestSeed, Even = SendKey (always seed SID + 1 = key SID)
```

---

### Q3. Explain 0x19 ReadDTCInformation — DTC format, status byte, and sub-functions.

**Short Answer:** 0x19 reads diagnostic trouble codes. DTCs have a 3-byte code and a 1-byte status byte. Status bits indicate if the fault is current, confirmed, pending, permanent, etc.

**Detailed Expert Answer:**

```
DTC Status Byte (8 bits):

Bit 7: warningIndicatorRequested  (MIL lamp on for emissions)
Bit 6: testNotCompletedSinceLastClear (monitor not yet run)
Bit 5: testFailedSinceLastClear   (fault occurred since clear)
Bit 4: testNotCompletedThisMonitoringCycle
Bit 3: confirmedDTC               (fault confirmed = above threshold)
Bit 2: pendingDTC                 (fault detected but not yet confirmed)
Bit 1: testFailed                 (current fault — active right now)
Bit 0: testFailedSinceLastClear   (historical — fault ever occurred)

Example: DTC status = 0x2F = 0010 1111
  bit7=0: no MIL
  bit6=0: monitor has run
  bit5=1: failed since last clear ← fault occurred before
  bit4=0: monitor ran this cycle
  bit3=1: CONFIRMED DTC ← needs attention
  bit2=1: PENDING ← currently failing
  bit1=1: TEST FAILED ← currently active
  bit0=1: failed since last clear ← historical too
  → This is an ACTIVE, CONFIRMED DTC
```

**Common 0x19 sub-functions:**
```
0x19 0x01 [statusMask]:  Report DTCs by status
  Request: [0x19][0x01][0x08]  → mask=0x08 = confirmed DTCs only
  Response: [0x59][0x01][0x08][DTC1_HH][DTC1_HL][DTC1_LL][DTC1_status]
                                                           [DTC2...]

0x19 0x02 [statusMask]:  Report DTCs with count (efficient)
  Response: [0x59][0x02][0x08][count_high][count_low][DTC1]...[DTCn]

0x19 0x04 [DTC_HH][DTC_HL][DTC_LL] [recordNumber]: Freeze frame
  Request: [0x19][0x04][0xD0][0x00][0x11][0x01]
  Response: Freeze frame data at time of fault (speed, RPM, temperature, etc.)

0x19 0x06 [DTC_HH][DTC_HL][DTC_LL]: Extended data record
  Returns: fault occurrence counter, aging counter, healing counter
```

**DTC code format:**
```
ISO 15031-6 OBD DTC format (also used in UDS):
  Byte 1 high nibble: system (P=powertrain, C=chassis, B=body, U=network)
  Byte 1 low nibble: sub-system
  Byte 2-3: specific fault code

Examples:
  [0xD0][0x00][0x12] = 0xD00012 (manufacturer-specific)
  [0x01][0x01][0x00] = P0100 (Mass Airflow Circuit Malfunction — standard OBD)

AUTOSAR DTC internal format:
  DEM event ID → maps to DTC via configuration
  e.g., DEM_EVENT_CAN_BUS_OFF → DTC 0x900001
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. Walk through a complete UDS firmware download sequence (0x34/0x36/0x37).

**Detailed Expert Answer:**

```
Firmware Download Sequence:

STEP 1: Enter Programming Session
  Request:  [0x10][0x02]
  Response: [0x50][0x02][P2_ms_hi][P2_ms_lo][P2star_ms_hi][P2star_ms_lo]
  → P2* = 5000ms (ECU has 5s to respond during flash operations)

STEP 2: Security Access (required before programming)
  Request:  [0x27][0x01]  → RequestSeed
  Response: [0x67][0x01][S1][S2][S3][S4]
  
  Request:  [0x27][0x02][K1][K2][K3][K4]  → SendKey
  Response: [0x67][0x02]  ← Unlocked!

STEP 3: Stop Normal Communication (optional but common)
  Request:  [0x28][0x01][0x01]  → disableRxAndTx, all messages
  Response: [0x68][0x01]
  → ECU stops sending CAN messages (reduces bus load during flash)

STEP 4: Erase Flash Routine
  Request:  [0x31][0x01][0xFF][0x00][0x01][0x00][0x10][0x00][0x00][0x60][0x00]
             ↑start ↑routine  ↑FF00=OEM erase ↑memAddress       ↑memSize
  Response: Pending [0x7F][0x31][0x78] (may take 500ms-2s to erase)
            Final:  [0x71][0x01][0xFF][0x00]  ← Erase complete

STEP 5: RequestDownload
  Request:  [0x34][0x00][0x44][0x00][0x01][0x00][0x00][0x00][0x60][0x00]
             ↑svc ↑encrypt=0 ↑address=4B+size=4B ↑start_addr   ↑size
  Response: [0x74][0x20][0x04][0x00]
             ↑svc+0x40 ↑lengthFormat ↑maxBlockSize: 0x0400 = 1024 bytes

  maxBlockSize = 1024 bytes per TransferData block

STEP 6: TransferData (repeat for all blocks)
  Block 1: [0x36][0x01][data... up to 1024 bytes]
           Response: [0x76][0x01]  ← Block 1 accepted
  Block 2: [0x36][0x02][data...]
           Response: [0x76][0x02]
  ...
  Block N: [0x36][0xNN mod 0xFF][data...]
  
  Sequence counter wraps: 0x01..0xFE → 0xFF → 0x01 (not 0x00)

STEP 7: RequestTransferExit (verify download)
  Request:  [0x37][CRC1][CRC2][CRC3][CRC4]  (CRC-32 of downloaded firmware)
  Response: [0x77]  ← Firmware accepted and CRC verified
  NRC 0x31 if CRC mismatch or address/size invalid

STEP 8: Validate & Activate
  Request:  [0x31][0x01][0x02][0x02]  (check programming integrity routine)
  Response: [0x71][0x01][0x02][0x02][0x00]  ← Pass
  NRC 0x31 if validation fails

STEP 9: Reset ECU
  Request:  [0x11][0x01]  → hardReset
  Response: [0x51][0x01]
  → ECU reboots, bootloader verifies firmware, starts new application
```

**Common issues and NRC responses:**

| NRC | Code | Meaning | Fix |
|-----|------|---------|-----|
| 0x13 | incorrectMessageLengthOrInvalidFormat | Wrong data length | Check memoryAddressAndLengthFormatIdentifier byte |
| 0x22 | conditionsNotCorrect | Not in programming session | Do session change first |
| 0x24 | requestSequenceError | Steps out of order | Check sequence |
| 0x31 | requestOutOfRange | Invalid address/size | Check flash memory map |
| 0x33 | securityAccessDenied | Not unlocked | Do SecurityAccess first |
| 0x35 | invalidKey | Wrong key | Check seed-key algorithm |
| 0x70 | uploadDownloadNotAccepted | Flash busy/protected | Check bootloader state |
| 0x72 | generalProgrammingFailure | Flash write error | HW issue or supply voltage |
| 0x73 | wrongBlockSequenceCounter | Sequence mismatch | Restart download |

---

### Q5. What is AUTOSAR DCM and how does it process a UDS request internally?

**Detailed Expert Answer:**
```
AUTOSAR DCM (Diagnostic Communication Manager) request processing:

┌──────────────────────────────────────────────────────────────┐
│                    DCM Internal Flow                         │
│                                                              │
│ CAN → CanIf → PduR → ComM/CanTp ──────▶ Dcm_RxIndication() │
│                                              ↓               │
│                                   ┌─────────────────────┐   │
│                                   │  DCM Sub-module:    │   │
│                                   │  DSD (DSP Dispatch) │   │
│                                   │  Parses SID         │   │
│                                   │  Checks session     │   │
│                                   │  Checks security    │   │
│                                   └──────────┬──────────┘   │
│                                              ↓               │
│                              ┌───────────────────────────┐  │
│                              │  Service handler:          │  │
│                              │  Dcm_Dsp0x22() for 0x22   │  │
│                              │  Calls application         │  │
│                              │  callback to get data      │  │
│                              └───────────────────────────┘  │
│                                              ↓               │
│                              ┌───────────────────────────┐  │
│                              │  Response:                 │  │
│                              │  Dcm_ExternalSetNegResponse│  │
│                              │  or Dcm_ExternalSetPosDone │  │
│                              └───────────────────────────┘  │
│                                              ↓               │
│ Dcm_TxIndication() ◀─── PduR ◀── CanTp (ISO-TP) ◀── data  │
└──────────────────────────────────────────────────────────────┘
```

**DCM configuration (AUTOSAR arxml structure):**
```
DcmDspData:
  DcmDspDataId: 0xF190  (VIN)
  DcmDspDataReadFnc: App_ReadVIN  ← application provides this callback
  DcmDspDataSize: 17 bytes
  DcmDspDataConditionCheckReadFnc: App_CheckVINReadCondition

Application callback for 0x22 0xF190 (read VIN):
*/
Std_ReturnType App_ReadVIN(Dcm_OpStatusType opStatus,
                            uint8 *Data,
                            Dcm_NegativeResponseCodeType *ErrorCode) {
    if (NvM_GetErrorStatus(NVM_BLOCK_VIN) == NVM_REQ_OK) {
        NvM_ReadBlock(NVM_BLOCK_VIN, Data);
        return E_OK;
    }
    *ErrorCode = DCM_E_CONDITIONSNOTCORRECT;
    return E_NOT_OK;
}
```

---

## ADVANCED QUESTIONS

---

### Q6. Implement a UDS 0x19 0x02 DTC reader using SocketCAN ISO-TP in C.

**Detailed Expert Answer:**
```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <linux/can.h>
#include <linux/can/isotp.h>

/* UDS request: 0x19 0x02 0x08 (read all confirmed DTCs) */
static const uint8_t READ_DTC_REQ[] = { 0x19, 0x02, 0x08 };

typedef struct {
    uint32_t dtc_code;    /* 3-byte DTC */
    uint8_t  status;      /* DTC status byte */
} DTC_Entry_t;

/* Parse 0x59 0x02 response */
int parse_dtc_response(const uint8_t *resp, size_t resp_len,
                       DTC_Entry_t *dtcs, int max_dtcs) {
    if (resp_len < 3) return -1;
    if (resp[0] != 0x59 || resp[1] != 0x02) return -1;
    
    /* resp[2] = status mask echo */
    const uint8_t *p = &resp[3];
    size_t remaining = resp_len - 3;
    int count = 0;
    
    /* Each DTC entry = 3 bytes DTC + 1 byte status */
    while (remaining >= 4 && count < max_dtcs) {
        dtcs[count].dtc_code = ((uint32_t)p[0] << 16) |
                               ((uint32_t)p[1] << 8)  |
                               ((uint32_t)p[2]);
        dtcs[count].status   = p[3];
        p         += 4;
        remaining -= 4;
        count++;
    }
    return count;
}

int read_all_dtcs(const char *iface, uint32_t tester_id, uint32_t ecu_id) {
    /* Open ISO-TP socket */
    int fd = socket(AF_CAN, SOCK_DGRAM, CAN_ISOTP);
    
    struct sockaddr_can addr = {
        .can_family           = AF_CAN,
        .can_addr.tp.tx_id    = tester_id,   /* 0x7DF (functional) or 0x7E0 (physical) */
        .can_addr.tp.rx_id    = ecu_id,      /* 0x7E8 (ECU response ID) */
    };
    struct ifreq ifr;
    strncpy(ifr.ifr_name, iface, IFNAMSIZ - 1);
    ioctl(fd, SIOCGIFINDEX, &ifr);
    addr.can_ifindex = ifr.ifr_ifindex;
    bind(fd, (struct sockaddr*)&addr, sizeof(addr));
    
    /* Send UDS request */
    write(fd, READ_DTC_REQ, sizeof(READ_DTC_REQ));
    
    /* Read response (ISO-TP reassembles multi-frame automatically) */
    uint8_t resp[4096];
    ssize_t n = read(fd, resp, sizeof(resp));
    close(fd);
    
    if (n < 0) {
        perror("read");
        return -1;
    }
    
    /* Check for negative response */
    if (n >= 3 && resp[0] == 0x7F) {
        printf("Negative response: SID=0x%02X NRC=0x%02X\n", resp[1], resp[2]);
        return -1;
    }
    
    /* Parse DTCs */
    DTC_Entry_t dtcs[100];
    int count = parse_dtc_response(resp, (size_t)n, dtcs, 100);
    
    printf("Found %d DTCs:\n", count);
    for (int i = 0; i < count; i++) {
        uint32_t code = dtcs[i].dtc_code;
        uint8_t  stat = dtcs[i].status;
        char prefix;
        switch((code >> 22) & 0x03) {
            case 0: prefix = 'P'; break;
            case 1: prefix = 'C'; break;
            case 2: prefix = 'B'; break;
            default: prefix = 'U'; break;
        }
        printf("  %c%04X status=0x%02X [%s%s%s]\n",
               prefix, code & 0x3FFF, stat,
               (stat & 0x01) ? "FAILED " : "",
               (stat & 0x04) ? "PENDING " : "",
               (stat & 0x08) ? "CONFIRMED" : "");
    }
    return count;
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q7. You are validating a TCU and it returns NRC 0x78 (Response Pending) repeatedly but never finishes. How do you debug?

**Expert Answer:**

"NRC 0x78 means 'requestCorrectlyReceivedResponsePending' — the ECU acknowledged the request but is still processing. It should keep sending 0x78 every P2* interval (5 seconds max by default), then eventually send the final response or a different NRC.

**Infinite 0x78 scenarios:**

1. **Deadlock in ECU application:**
   ```
   The application callback never returns.
   Classic cause: NvM_ReadBlock() called inside DCM handler
   → NvM is an asynchronous API — must use callback pattern, not block
   
   Bosch DCM guideline: callbacks must return E_PENDING if not done,
   then DCM calls them again on next OS cycle
   ```

2. **P2* timeout calculation issue:**
   ```
   P2* = 5000ms by default
   If the ECU sends 0x78 every 500ms, it can send 10 × 0x78 before P2* expires
   Check: is the tester's P2* timer set correctly?
   Some older CANoe scripts use P2=500ms and don't extend on 0x78
   ```

3. **Task priority inversion:**
   ```
   DCM runs in task priority 5, NvM runs in task priority 3
   Long NvM operation blocks the MCU → DCM timer not serviced
   Fix: use OS event mechanism, not polling
   ```

**Debug approach:**
```bash
# CANoe CAPL to track 0x78 count:
on message 0x7E8 {
    if (this.byte(0) == 0x7F && this.byte(2) == 0x78) {
        static int count = 0;
        write("0x78 count: %d at time %d ms", ++count, timeNow()/10);
    }
}

# Lauterbach TRACE32: break at the callback that issues 0x78
# Check: is the application task returning E_PENDING forever?
# Check: OS task trace — what is blocking the DCM callback task?
```

**Production Insight:** At a Valeo TCU project, this issue was traced to a UDS 0x31 routine (flash erase) that called `NvM_WriteBlock()` synchronously inside a while loop. The NvM operation was asynchronous — the result was never checked. The loop never exited. Fix: use NvM job result callback and set a flag for DCM to check on next call."

---

## CHEAT SHEET — UDS Diagnostics

```
Service IDs:
  0x10 DiagnosticSessionControl  (0x01=default, 0x02=programming, 0x03=extended)
  0x11 ECUReset                  (0x01=hard, 0x02=key-off-on, 0x03=soft)
  0x14 ClearDTCs                 (group 0xFFFFFF = all)
  0x19 ReadDTCInformation        (sub: 0x01=by_mask, 0x02=with_count, 0x04=freeze)
  0x22 ReadDataByIdentifier      (DID: 0xF190=VIN, 0xF186=active_session)
  0x27 SecurityAccess            (odd=RequestSeed, even=SendKey)
  0x2E WriteDataByIdentifier
  0x31 RoutineControl            (0x01=start, 0x02=stop, 0x03=result)
  0x34 RequestDownload
  0x36 TransferData
  0x37 RequestTransferExit
  0x3E TesterPresent             (send every 1-2 sec to stay in session)

Positive response = SID + 0x40
Negative response: [0x7F][SID][NRC]

Key NRC codes:
  0x10 generalReject
  0x11 serviceNotSupported
  0x12 subFunctionNotSupported
  0x13 incorrectMessageLength
  0x22 conditionsNotCorrect
  0x24 requestSequenceError
  0x31 requestOutOfRange
  0x33 securityAccessDenied
  0x35 invalidKey
  0x36 exceededNumberOfAttempts
  0x37 requiredTimeDelayNotExpired
  0x78 requestCorrectlyReceivedResponsePending (keep waiting)

DTC Status Byte:
  bit0: testFailedSinceLastClear
  bit1: testFailed (ACTIVE)
  bit2: pendingDTC
  bit3: confirmedDTC ← most important
  bit7: warningIndicatorRequested (MIL)

Flash download sequence:
  0x10 02 → 0x27 01/02 → 0x28 01 → 0x31 FF00 (erase) → 0x34 → 0x36×N → 0x37 → 0x11 01
```
