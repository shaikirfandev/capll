# Flashing & Bootloader Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Bootloader and flashing knowledge is **critical** for every ECU firmware engineer and validation engineer. Interviewers at Bosch, Continental, KPIT, and Tata Elxsi probe deeply: "How does your ECU update its firmware?" You must explain UDS-based flashing (ISO 14229-1), dual-bank flash for fail-safe OTA, security (key derivation, symmetric auth), and common flashing failures (locked security access, incomplete programming, power cycle issues).

**Key areas:**
- Bootloader architecture (primary vs application bootloader)
- ROM bootloader vs flash bootloader (second-stage)
- Dual-bank flash (active/inactive swap, fallback)
- UDS flash programming sequence (0x34/0x36/0x37/0x31)
- Security during flashing (0x27 SecurityAccess, checksum)
- Programming preconditions (speed=0, KL15 stable)
- CRC / hash integrity verification
- Programming error recovery (incomplete flash, power loss)
- JTAG vs UDS flashing (production vs development)
- AUTOSAR BSW: FBL (Flash Bootloader) module

---

## BOOTLOADER FUNDAMENTALS

---

### Q1. Explain the dual-stage bootloader architecture. How does an automotive ECU boot?

**Expert Answer:**

```
Dual-Stage Boot Sequence (e.g., NXP S32K344 or Infineon TC397):

┌─────────────────────────────────────────────────────────────────┐
│ BOOT ROM (Read-Only, factory programmed)                         │
│  • Loaded at reset: PC → 0x00000000 (ROM start)                 │
│  • Checks pin/SFR: JTAG enabled? → drop to debug                │
│  • Checks flash: valid magic number at 0x08000000?              │
│  • If valid: jump to Primary Bootloader                          │
│  • If invalid: stay in ROM recovery mode (can receive firmware) │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼ (if primary bootloader valid)
┌─────────────────────────────────────────────────────────────────┐
│ PRIMARY BOOTLOADER (in flash, small, ~16KB)                      │
│  Flash region: 0x08000000 – 0x08003FFF                          │
│                                                                  │
│  1. Initialise minimal hardware: clock, UART debug, CAN-FD      │
│  2. Check "flash request" flag in NvM (set by App before reset) │
│  3. If flag set: stay in bootloader, wait for UDS 0x34 request  │
│  4. If no flag: verify Application FW header (CRC-32, version)  │
│  5. If Application FW valid: jump to application                │
│  6. If Application FW invalid: enter fail-safe bootloader mode  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼ (normal boot)
┌─────────────────────────────────────────────────────────────────┐
│ APPLICATION (in flash, production firmware, ~512KB–4MB)         │
│  Flash region: 0x08010000 – ...                                 │
│                                                                  │
│  On OTA request received (MQTT/Bluetooth/cellular):             │
│  1. Verify OTA package signature (RSA-2048 or ECDSA-256)        │
│  2. Write new firmware to INACTIVE bank                         │
│  3. Verify written data (SHA-256 hash)                          │
│  4. Set "flash request" flag in NvM                             │
│  5. Write "swap to inactive bank" command                       │
│  6. Reset ECU → Primary Bootloader activates new bank           │
└─────────────────────────────────────────────────────────────────┘

Flash Layout (Dual-Bank):
  0x08000000 │ Primary Bootloader (16KB)      │ Never erased via OTA
  0x08004000 │ NvM / Config area (64KB)       │ Persistent across flashes
  0x08014000 │ BANK A — Active Firmware       │ Current running version
  0x08214000 │ BANK B — Inactive/Staging      │ Next firmware written here
  0x08414000 │ Signature storage (4KB)        │ RSA/ECDSA signatures
  End of flash
```

---

### Q2. Describe the complete UDS firmware flashing sequence. Write the code.

**Expert Answer:**

```c
/*
 * UDS Firmware Download — Complete 9-step sequence
 * Standard: ISO 14229-1
 * ECU: TCU with 512KB firmware, CAN UDS channel
 */

#include <stdint.h>
#include <stddef.h>

/* UDS Service IDs */
#define UDS_SID_SESSION_CTRL      0x10U
#define UDS_SID_SECURITY_ACCESS   0x27U
#define UDS_SID_ROUTINE_CTRL      0x31U
#define UDS_SID_REQUEST_DOWNLOAD  0x34U
#define UDS_SID_TRANSFER_DATA     0x36U
#define UDS_SID_REQUEST_EXIT      0x37U
#define UDS_SID_ECU_RESET         0x11U

/* NRCs */
#define UDS_NRC_REQUEST_OUT_SEQ   0x24U
#define UDS_NRC_INVALID_KEY       0x35U
#define UDS_NRC_EXCEEDED_NUM      0x36U
#define UDS_NRC_PROG_FAIL         0x72U
#define UDS_NRC_WRONG_BLOCK_SEQ   0x73U
#define UDS_NRC_REQ_CORRECT_RCVD  0x78U  /* Response pending */

/* ===== Complete UDS Flash Download ===== */

typedef struct {
    uint8_t  buf[8];
    uint8_t  len;
    uint8_t  resp[256];
    uint16_t resp_len;
} UDS_Context_t;

static UDS_Context_t uds;

/* Returns 0 on success, negative on error */
int uds_flash_firmware(const uint8_t *fw_data, uint32_t fw_len, uint32_t target_addr) {
    int rc;
    
    /* ── STEP 1: Enter Programming Session ─────────────────── */
    uds.buf[0] = UDS_SID_SESSION_CTRL;
    uds.buf[1] = 0x02U;  /* Programming Session */
    rc = uds_send_and_receive(uds.buf, 2, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x50U || uds.resp[1] != 0x02U) {
        return -1;  /* Session rejected */
    }
    /* Response: 50 02 00 19 01 F4 (OK, P2=25ms, P2*=5000ms) */
    
    /* ── STEP 2: Security Access — Request Seed ─────────────── */
    uds.buf[0] = UDS_SID_SECURITY_ACCESS;
    uds.buf[1] = 0x11U;  /* AccessLevel 0x11 for programming */
    rc = uds_send_and_receive(uds.buf, 2, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x67U) {
        return -2;
    }
    
    uint32_t seed = ((uint32_t)uds.resp[2] << 24) | ((uint32_t)uds.resp[3] << 16) |
                    ((uint32_t)uds.resp[4] << 8)  | (uint32_t)uds.resp[5];
    
    /* ── STEP 3: Security Access — Send Key ─────────────────── */
    uint32_t key = compute_security_key(seed);  /* Project-specific */
    
    uds.buf[0] = UDS_SID_SECURITY_ACCESS;
    uds.buf[1] = 0x12U;  /* SendKey for level 0x11 */
    uds.buf[2] = (uint8_t)(key >> 24);
    uds.buf[3] = (uint8_t)(key >> 16);
    uds.buf[4] = (uint8_t)(key >> 8);
    uds.buf[5] = (uint8_t)(key);
    rc = uds_send_and_receive(uds.buf, 6, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x67U || uds.resp[1] != 0x12U) {
        return -3;  /* NRC 0x35 = wrong key */
    }
    
    /* ── STEP 4: Check Programming Preconditions ─────────────── */
    uds.buf[0] = UDS_SID_ROUTINE_CTRL;
    uds.buf[1] = 0x01U;  /* Start routine */
    uds.buf[2] = 0xFF;
    uds.buf[3] = 0x01;   /* RoutineID = 0xFF01: Check Programming Conditions */
    rc = uds_send_and_receive(uds.buf, 4, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x71U) {
        return -4;  /* Conditions not met (speed ≠ 0, voltage low, etc.) */
    }
    
    /* ── STEP 5: Erase Memory ────────────────────────────────── */
    uds.buf[0] = UDS_SID_ROUTINE_CTRL;
    uds.buf[1] = 0x01U;
    uds.buf[2] = 0xFF;
    uds.buf[3] = 0x00;   /* RoutineID = 0xFF00: Erase Memory */
    /* Memory range to erase: start address + length */
    uds.buf[4] = (uint8_t)(target_addr >> 24);
    uds.buf[5] = (uint8_t)(target_addr >> 16);
    uds.buf[6] = (uint8_t)(target_addr >> 8);
    uds.buf[7] = (uint8_t)(target_addr);
    uds.buf[8] = (uint8_t)(fw_len >> 24);
    uds.buf[9] = (uint8_t)(fw_len >> 16);
    uds.buf[10] = (uint8_t)(fw_len >> 8);
    uds.buf[11] = (uint8_t)(fw_len);
    uds.len = 12;
    rc = uds_send_and_receive(uds.buf, 12, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x71U) {
        return -5;  /* Erase failed */
    }
    
    /* ── STEP 6: Request Download ────────────────────────────── */
    uds.buf[0] = UDS_SID_REQUEST_DOWNLOAD;
    uds.buf[1] = 0x00U;  /* dataFormatIdentifier: no compression, no encryption */
    uds.buf[2] = 0x44U;  /* addressAndLengthFormatIdentifier: 4 addr + 4 len bytes */
    /* Memory address */
    uds.buf[3] = (uint8_t)(target_addr >> 24);
    uds.buf[4] = (uint8_t)(target_addr >> 16);
    uds.buf[5] = (uint8_t)(target_addr >> 8);
    uds.buf[6] = (uint8_t)(target_addr);
    /* Memory size */
    uds.buf[7] = (uint8_t)(fw_len >> 24);
    uds.buf[8] = (uint8_t)(fw_len >> 16);
    uds.buf[9] = (uint8_t)(fw_len >> 8);
    uds.buf[10] = (uint8_t)(fw_len);
    rc = uds_send_and_receive(uds.buf, 11, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x74U) {
        return -6;
    }
    /* Response: 74 20 02 00 → maxBlockLen = (0x02 << 8) | 0x00 = 512 bytes */
    uint16_t max_block_len = ((uint16_t)uds.resp[2] << 8) | uds.resp[3];
    if (max_block_len < 2) max_block_len = 256U;  /* Safety default */
    
    /* ── STEP 7: Transfer Data ───────────────────────────────── */
    uint32_t offset   = 0U;
    uint8_t  block_seq = 1U;  /* Block sequence counter: 1..0xFF, then wraps to 0 */
    
    while (offset < fw_len) {
        uint32_t chunk = fw_len - offset;
        if (chunk > (uint32_t)(max_block_len - 2U)) {
            chunk = (uint32_t)(max_block_len - 2U);  /* -2 for SID + seq */
        }
        
        uds.buf[0] = UDS_SID_TRANSFER_DATA;   /* 0x36 */
        uds.buf[1] = block_seq;
        memcpy(&uds.buf[2], &fw_data[offset], chunk);
        
        rc = uds_send_and_receive(uds.buf, (uint16_t)(2U + chunk),
                                  uds.resp, &uds.resp_len);
        if (rc != 0 || uds.resp[0] != 0x76U || uds.resp[1] != block_seq) {
            return -7;  /* Transfer data rejected */
        }
        
        offset += chunk;
        block_seq = (block_seq == 0xFFU) ? 0x00U : (block_seq + 1U);
    }
    
    /* ── STEP 8: Request Transfer Exit ──────────────────────── */
    uds.buf[0] = UDS_SID_REQUEST_EXIT;  /* 0x37 */
    rc = uds_send_and_receive(uds.buf, 1, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x77U) {
        return -8;
    }
    
    /* ── STEP 9: Verify Checksum ─────────────────────────────── */
    /* Routine 0xFF02: Verify Programming Checksum */
    uint32_t crc = calculate_crc32(fw_data, fw_len);
    uds.buf[0] = UDS_SID_ROUTINE_CTRL;
    uds.buf[1] = 0x01U;
    uds.buf[2] = 0xFF;
    uds.buf[3] = 0x02;  /* RoutineID = 0xFF02: Verify Checksum */
    uds.buf[4] = (uint8_t)(crc >> 24);
    uds.buf[5] = (uint8_t)(crc >> 16);
    uds.buf[6] = (uint8_t)(crc >> 8);
    uds.buf[7] = (uint8_t)(crc);
    rc = uds_send_and_receive(uds.buf, 8, uds.resp, &uds.resp_len);
    if (rc != 0 || uds.resp[0] != 0x71U) {
        return -9;  /* Checksum mismatch — programming corrupted */
    }
    
    /* ── STEP 10: ECU Reset ─────────────────────────────────── */
    uds.buf[0] = UDS_SID_ECU_RESET;
    uds.buf[1] = 0x01U;  /* Hard reset */
    uds_send_and_receive(uds.buf, 2, uds.resp, &uds.resp_len);
    /* No response check — ECU resets immediately */
    
    return 0;  /* Success */
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q3. An ECU becomes unresponsive after a failed firmware flash. How do you recover it?

**Expert Answer:**

"This is one of the most critical automotive scenarios — a bricked ECU in production or in the field.

**Scenario analysis:**
```
Failed during:        Most likely root cause:        Recovery path:
─────────────────────────────────────────────────────────────────
Step 5 (Erase)        Flash erased, no valid FW      Bootloader still intact?
Step 7 (Transfer)     Partial write, bad CRC          Re-flash via bootloader
Step 9 (Checksum)     Flash complete but corrupted   Re-flash via bootloader
Power loss during 7   Partial/corrupted flash         ROM bootloader recovery
─────────────────────────────────────────────────────────────────
```

**Recovery Procedure:**

```
CASE 1: Primary Bootloader intact, Application corrupted
  → ECU boots to bootloader (detects bad app CRC)
  → ECU stays in bootloader, awaiting UDS commands
  → No announcement — must send 0x10 0x02 to enter programming session
  
  Solution:
  1. Apply KL15 (ignition ON)
  2. Wait 200ms for bootloader CAN init
  3. Send: 10 02 (DiagnosticSessionControl, Programming)
  4. If response: 50 02 → bootloader is alive
  5. Run full flash sequence from Step 3 onwards
  6. ECU recovers

CASE 2: Power lost during flash (most dangerous)
  → Flash sector partially written → all zeroes or random bytes
  → Primary bootloader can't jump anywhere valid
  → ECU appears completely dead on CAN

  Solution A: ROM bootloader recovery (if supported)
  1. Apply specific pin pattern (e.g., MODE pin pulled high)
  2. ROM bootloader activates, waits on UART or SWD
  3. Use vendor tool (NXP MCUXpresso, Infineon MemTool) to re-flash
  4. Flash full firmware image via UART/SWD
  
  Solution B: JTAG/SWD programming (development bench)
  1. Connect JTAG probe (Lauterbach, J-Link, OpenOCD)
  2. Use Lauterbach T32: Flash.ReProgram ALL (re-programs entire flash)
  3. Flash complete firmware image
  4. ECU fully recovered

CASE 3: Security lockout (too many failed seed/key attempts)
  → ECU NRC 0x36 (exceededNumberOfAttempts) → locked for 30 minutes
  
  Solution:
  1. Wait 30 minutes (security lockout timer in most ECUs)
  2. Power cycle to reset timer (if bootloader supports)
  3. Use special "unlock" UDS routine (OEM-specific, may require HSM key)
  4. If neither: JTAG to clear security lockout flag in NvM directly
```

**Production Insight (Bosch EDC17 project, customer portal complaint):** Fleet update for 8,000 vehicles. 23 ECUs bricked during OTA (power cut during transfer). Recovery required dealer visit, JTAG reflash via OBD2 port using special reprogramming tool (CANflash / vFlash). Fixed root cause: Added battery voltage check (must be >12.5V) before allowing OTA to proceed, and added resume capability (SHA-256 block tracking so partial downloads could resume without re-erasing)."

---

## CHEAT SHEET — Flashing & Bootloader

```
UDS Flash sequence (9 steps):
  1.  10 02      DiagnosticSessionControl → Programming Session
  2.  27 11      SecurityAccess → Request Seed (level 0x11)
  3.  27 12 KEY  SecurityAccess → Send Key
  4.  31 01 FF01 Routine → Check Programming Conditions
  5.  31 01 FF00 Routine → Erase Memory
  6.  34 00 44 ADDR LEN  Request Download
  7.  36 SEQ DATA         Transfer Data (loop, blockSeq 01→FF→00...)
  8.  37         Request Transfer Exit
  9.  31 01 FF02 CRC32   Routine → Verify Checksum
  10. 11 01      ECU Reset

Key UDS responses:
  74 20 02 00 → max block length = 0x0200 = 512 bytes
  NRC 0x24 = requestOutOfSequence (sent 0x36 before 0x34)
  NRC 0x35 = invalidKey (security access failed)
  NRC 0x36 = exceededNumberOfAttempts (too many wrong keys)
  NRC 0x72 = uploadDownloadNotAccepted (programming failed)
  NRC 0x73 = wrongBlockSequenceCounter (missed a 0x36 block)
  NRC 0x78 = requestCorrectlyReceivedResponsePending (slow erase)

Dual-bank flash advantages:
  1. Atomicity: new FW only activated after full verification
  2. Fallback: if new FW fails self-test, boot to previous bank
  3. No downtime: write to inactive bank while running from active
  4. Anti-bricking: valid bank always available

Bootloader recovery options (in order of preference):
  1. UDS programming session (bootloader intact, app corrupted)
  2. ROM bootloader via special pin/mode (vendor-specific)
  3. JTAG/SWD programming (bypasses all ECU software)
  OEM recovery: J2534 pass-through + dealer programming tool (ODX/FLASH)

Pre-conditions for programming (OEM-typical):
  ✓ Vehicle speed = 0 km/h
  ✓ Engine OFF (or in P/N gear)
  ✓ Battery voltage 12.5V–14.5V
  ✓ No active safety DTCs (ASIL functions locked)
  ✓ KL15 continuously ON for duration
  ✓ Communication stable (no CAN errors)
```
