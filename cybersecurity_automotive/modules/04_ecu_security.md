# Module 04 — ECU Security & Hardening

> Level: Intermediate → Advanced | Est. study time: 10 hours

---

## 4.1 ECU Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ECU INTERNALS                           │
│                                                                 │
│  ┌────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │ MCU/SoC    │    │  HSM / TPM       │    │ External Flash │  │
│  │            │    │                  │    │                │  │
│  │ Application│    │ Crypto Engine    │    │ Firmware       │  │
│  │ RTOS       │    │ Key Store        │    │ Calibration    │  │
│  │ AUTOSAR    │◄──►│ Random Number Gen│    │ NVM config     │  │
│  │ BSW        │    │ Secure Boot ROM  │    │                │  │
│  │ MCAL       │    │ Monotonic Counter│    └────────────────┘  │
│  └──────┬─────┘    └──────────────────┘                        │
│         │                                                       │
│  ┌──────▼─────────────────────────────────────────────────┐    │
│  │ I/O: CAN, LIN, Eth, SPI, UART, ADC, PWM, JTAG/SWD    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

Key MCU families in automotive:
  Infineon AURIX TC3xx (ASIL D, ISO 26262)
  NXP S32K / S32G
  Renesas RH850 / R-Car  
  STM32 (non-safety, body ECUs)
  Texas Instruments TMS570 (ASIL D)
```

---

## 4.2 Secure Boot

Secure Boot ensures only authenticated firmware runs on the ECU.

### Chain of Trust

```
Power ON
   │
   ▼
┌────────────────────────────────────┐
│  Boot ROM (immutable, in silicon)  │
│  Contains: Root Public Key Hash    │
│  Action: Verify Bootloader sig     │
└─────────────────┬──────────────────┘
                  │ ✓ Signature valid
                  ▼
┌────────────────────────────────────┐
│  Bootloader Stage 1 (BL1)         │
│  Signed with OEM Root Key          │
│  Action: Verify BL2 signature      │
└─────────────────┬──────────────────┘
                  │ ✓ Signature valid
                  ▼
┌────────────────────────────────────┐
│  Bootloader Stage 2 (BL2)         │
│  Verifies Application firmware     │
│  Action: Verify App signature      │
└─────────────────┬──────────────────┘
                  │ ✓ Signature valid
                  ▼
┌────────────────────────────────────┐
│  Application Firmware              │
│  AUTOSAR OS + BSW + SWC            │
│  Executes only if all checks pass  │
└────────────────────────────────────┘

Each stage:
  1. Computes hash (SHA-256/SHA-384) of next stage
  2. Verifies ECDSA or RSA signature using stored public key
  3. If verification fails → HALT or FALLBACK (never run untrusted code)
```

### Secure Boot Implementation (Pseudo-code)

```c
/* Boot ROM — runs first, immutable */
bool secure_boot_verify(const uint8_t *firmware, size_t len,
                        const uint8_t *signature) {
    /* Public key hash is fused into OTP (One-Time Programmable) memory */
    uint8_t otp_key_hash[32];
    OTP_Read(OTP_ROOT_KEY_HASH_ADDR, otp_key_hash, 32);
    
    /* Load public key from firmware header */
    const uint8_t *pub_key = firmware_header_get_pubkey(firmware);
    
    /* Verify public key matches OTP-stored hash */
    uint8_t computed_hash[32];
    SHA256(pub_key, PUBLIC_KEY_SIZE, computed_hash);
    if (memcmp(computed_hash, otp_key_hash, 32) != 0) {
        security_halt(); /* PUBLIC KEY NOT TRUSTED */
    }
    
    /* Verify firmware signature */
    if (ECDSA_Verify(pub_key, firmware, len, signature) != SUCCESS) {
        security_halt(); /* FIRMWARE SIGNATURE INVALID */
    }
    
    /* Verify anti-rollback: version must be >= minimum version */
    uint32_t fw_version = firmware_header_get_version(firmware);
    uint32_t min_version = OTP_Read_Word(OTP_MIN_FW_VERSION_ADDR);
    if (fw_version < min_version) {
        security_halt(); /* ROLLBACK ATTACK DETECTED */
    }
    
    return true; /* All checks passed — boot continues */
}
```

### Secure Boot Failure Modes

| Failure | Cause | Mitigation |
|---------|-------|-----------|
| Root key compromise | Physical extraction from OTP | Use HSM key, not raw OTP; key ceremony |
| Bootloader bypass | Jump to app via JTAG | Fuse JTAG permanently in production |
| Rollback attack | Flash old vulnerable firmware | Monotonic counter in OTP (increment on each flash) |
| Flash corruption | Power cut during flash | Redundant flash regions, A/B swap |
| Glitch attack | Voltage/clock glitch skips verify | Multi-redundant check, delay randomization |
| Debug mode left on | JTAG not disabled | Production fusing mandatory before shipping |

---

## 4.3 Hardware Security Module (HSM)

The HSM is a dedicated security co-processor within the MCU.

```
┌─────────────────────────────────────────────────────────────────┐
│                      HSM (Hardware Security Module)             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Crypto Engine│  │  Key Store   │  │  Secure RAM           │ │
│  │ AES-128/256  │  │  (isolated)  │  │  (not accessible      │ │
│  │ ECDSA/RSA    │  │  Root key    │  │   from main CPU)      │ │
│  │ SHA-2/3      │  │  Session key │  └───────────────────────┘ │
│  │ CMAC/HMAC    │  │  OTA key     │                            │
│  └──────────────┘  └──────────────┘  ┌───────────────────────┐ │
│                                       │ True Random Number Gen │ │
│  ┌──────────────────────────────────┐ │ (hardware entropy)    │ │
│  │   Monotonic Counter (OTP-backed) │ └───────────────────────┘ │
│  │   (prevents firmware rollback)   │                           │
│  └──────────────────────────────────┘                           │
│                                                                 │
│  HSM-to-CPU interface: SHE (Secure Hardware Extension)         │
│  or SHE+ / EVITA (European Vehicle IT Architecture)            │
└─────────────────────────────────────────────────────────────────┘

EVITA Levels:
  EVITA Light:  Symmetric crypto only (AES, CMAC)
  EVITA Medium: + Asymmetric (RSA-2048, ECDSA-256)
  EVITA Full:   + TPM-like, high-speed, all algorithms
```

**Why keys must live in HSM:**
```
Without HSM: Keys in regular flash → attacker reads flash via JTAG → steals key
With HSM:    Keys in HSM key store → physically isolated → key never leaves HSM
             HSM performs crypto on behalf of CPU (never exposes raw key)
```

---

## 4.4 TPM (Trusted Platform Module)

TPM is a standardized secure element used in SDV (Linux-based HPC):

```
TPM 2.0 Functions in Automotive:
  Platform Configuration Registers (PCR):
    → Store measurements of boot chain (BIOS + bootloader + kernel + initrd)
    → Any change to measured components changes PCR values
    → Keys sealed to PCR values → won't decrypt if boot chain tampered

  Attestation:
    → ECU can prove to cloud that its software is in a known-good state
    → V2C: Vehicle reports PCR values + TPM signature → Cloud verifies
    
  Key storage:
    → TPM stores TLS client certificate key
    → Used for mutual TLS in OTA/telematics

  Sealed storage:
    → Encryption key sealed to PCR[0-7]
    → Boot-time measured values must match for key to be released
```

---

## 4.5 Secure Flashing (Firmware Update via UDS)

```
SECURE FLASH SEQUENCE:

  Tester/Tool                              ECU
      │                                    │
      │── 0x10 0x02 (ExtendedDiag Sess) ──►│
      │◄─ 0x50 0x02 (Positive Response) ───│
      │                                    │
      │── 0x27 0x01 (RequestSeed) ─────────►│
      │◄─ 0x67 0x01 <seed_4bytes> ──────────│
      │                                    │
      │   [Compute key = f(seed, secret)]  │
      │                                    │
      │── 0x27 0x02 <computed_key_4B> ─────►│
      │◄─ 0x67 0x02 (Access Granted) ──────│
      │                                    │
      │── 0x10 0x03 (Programming Sess) ────►│
      │◄─ 0x50 0x03 ────────────────────────│
      │                                    │
      │── 0x34 [Download Request + algo] ──►│  ← Specify encryption algo
      │◄─ 0x74 [Max block size] ────────────│
      │                                    │
      │── 0x36 [Block 1 encrypted data] ───►│  ← Encrypted + signed blocks
      │── 0x36 [Block 2 encrypted data] ───►│
      │── 0x36 [Block N ...] ──────────────►│
      │                                    │
      │── 0x37 (Transfer Exit) ────────────►│
      │◄─ 0x77 ─────────────────────────────│
      │                                    │
      │── 0x31 [Verify Signature routine] ─►│  ← ECU verifies ECDSA sig
      │◄─ 0x71 [Result = 0x00 OK] ──────────│
      │                                    │
      │── 0x11 0x01 (Hard Reset) ──────────►│  ← Secure Boot validates on restart
      │                                    │
```

**Security checks during flashing:**
1. Programming session requires Security Access (seed-key)
2. Each data block encrypted with OEM key (AES-256-GCM)
3. Full firmware has ECDSA signature verified BEFORE execution
4. Anti-rollback: firmware version > monotonic counter
5. Post-flash: Secure Boot re-validates on reset

---

## 4.6 Key Management

```
KEY HIERARCHY:

  OEM Root CA (offline, air-gapped HSM)
       │
       ├── ECU Signing Key (online, signing service)
       │       └── Signs firmware images for each ECU type
       │
       ├── OTA Signing Key
       │       └── Signs OTA packages
       │
       ├── TLS Intermediate CA
       │       └── Issues per-vehicle TLS certificates
       │
       └── SecOC Keys (provisioned per ECU)
               └── CMAC keys for CAN message authentication

KEY PROVISIONING (at end-of-line):
  Factory → Secure flashing station → HSM provisions:
    - Production firmware (signed)
    - Vehicle-unique SecOC keys
    - TLS client certificate
    - UDS seed-key secret
  
  All provisioning over encrypted channel (TLS 1.3 mutual auth)
  Keys NEVER exported after provisioning
  Provision audit log retained for 15 years
```

---

## 4.7 Debug Port Attacks (JTAG/SWD)

JTAG and SWD are hardware debug interfaces. If left enabled in production, they are the
most powerful attack vector:

```
JTAG Attack Capability:
  - Read ALL memory (flash, RAM, registers)
  - Extract private keys, calibration, proprietary algorithms
  - Set breakpoints, step through code
  - Write to memory (bypass software checks)
  - Inject code directly
  - Bypass Secure Boot by jumping past verification

Production Hardening (mandatory):
  MCU OTP fusing:
    JTAG_DISABLE_BIT = 1   (fused, irreversible)
    DEBUG_DISABLE_BIT = 1  
    
  For Infineon AURIX TC3xx:
    UCB[CPUDBIVEC] configuration bit → disable JTAG
    
  For NXP S32K:
    Flash Configuration Field (FCF) FDPROT byte → disable flash debug
    
  For STM32:
    FLASH_OPTCR RDP Level 2 (permanent, irreversible)

Partial Debug Lock (development only):
  Debug authentication: JTAG requires 256-bit password (challenge-response)
  Used by: NVIDIA Drive, Tesla, Qualcomm Snapdragon Ride
```

---

## 4.8 Side-Channel Attacks

Side-channel attacks extract secrets by observing physical characteristics:

### Power Analysis Attack

```
Simple Power Analysis (SPA):
  - Attacker measures MCU power consumption during crypto operation
  - AES key operations have different power signature per bit
  - Oscilloscope traces → identify key bits

Differential Power Analysis (DPA):
  - Statistical analysis of many traces
  - Extract full AES-128 key with ~1000 encryption traces
  
Countermeasures:
  - Constant-time crypto implementation (no data-dependent branches)
  - Power noise injection (randomized dummy operations)
  - Masking (split secret shares, XOR with random mask)
  - Hardware crypto engine (HSM) with built-in DPA resistance
```

### Timing Attack

```c
/* VULNERABLE — timing attack on seed-key comparison */
bool verify_key_bad(uint8_t *received, uint8_t *expected, int len) {
    for (int i = 0; i < len; i++) {
        if (received[i] != expected[i]) return false;  // Early exit!
        // Attacker measures response time → learns how many bytes matched
    }
    return true;
}

/* SECURE — constant-time comparison */
bool verify_key_good(uint8_t *received, uint8_t *expected, int len) {
    uint8_t diff = 0;
    for (int i = 0; i < len; i++) {
        diff |= (received[i] ^ expected[i]);  // XOR all bytes, no early exit
    }
    return (diff == 0);  // Only ONE comparison at the end
}
```

### Fault Injection Attacks

```
Voltage Glitching:
  - Briefly drop VCC below MCU operating voltage
  - Causes instruction skip (e.g., skip signature verification)
  - Tools: ChipWhisperer, custom FPGA glitcher
  
Clock Glitching:
  - Inject extra clock edge during critical instruction
  - Causes register corruption or instruction skip
  
Laser Fault Injection:
  - Focused laser beam on die → bit flip in register/memory
  - Used to flip security bit or skip comparison
  
Countermeasures:
  - Voltage and clock monitoring (out-of-range → security halt)
  - Redundant security checks (check twice, different path)
  - Delay randomization (unpredictable timing for glitcher)
  - Light sensors (detect laser attempts)
  - Metal shielding on security-critical die regions
```

---

## 4.9 Memory Protection

```
MPU (Memory Protection Unit) — prevents unauthorized access:

  AUTOSAR MemMap configuration:
  
  Region 0: Flash (RX only — no write from application)
  Region 1: RTOS kernel stack (no access from application tasks)
  Region 2: HSM shared buffer (no direct access — use HSM API only)
  Region 3: NVM calibration (R from app, W only from trusted service)
  Region 4: CAN RX buffer (R from CAN driver only)
  Region 5: Application RAM (RW for app tasks, NX — no execute)
  Region 6: Bootloader space (RX, accessible only during boot phase)
  
  Critical rule: Data regions must be NX (Non-Executable)
                 Code regions must be RX (no runtime writes)
```

---

## 4.10 ECU Security Hardening Checklist

```
PRODUCTION READINESS CHECKLIST:

Secure Boot:
  [ ] Secure Boot enabled and tested
  [ ] All boot stages signed (ECDSA P-256 or RSA-2048 min)
  [ ] Anti-rollback monotonic counter configured
  [ ] Fallback/recovery mode secured (not skippable)
  [ ] Boot failure → safe state (not arbitrary code)

Debug Interfaces:
  [ ] JTAG/SWD permanently fused OFF in production
  [ ] UART debug console disabled in production build
  [ ] Any debug-only functionality excluded (compiler flag)

Key Management:
  [ ] All keys stored in HSM (never in plain flash)
  [ ] Key provisioning over encrypted channel only
  [ ] Seed-key algorithm not hardcoded in code
  [ ] Default/demo keys not present in production

Memory:
  [ ] MPU configured (application cannot write code region)
  [ ] Stack overflow detection enabled (stack canaries)
  [ ] Heap overflow detection if heap used
  [ ] MISRA C compliant memory operations

Communication:
  [ ] SecOC enabled on safety-critical CAN messages
  [ ] UDS programming session requires Security Access Level 2
  [ ] Rate limiting on diagnostic services
  [ ] Lockout after 3 failed seed-key attempts

Runtime:
  [ ] Watchdog enabled (non-window + window watchdog)
  [ ] Voltage monitoring (EVDD/AVDD range check)
  [ ] Clock monitoring (ECU halts if clock out of spec)
  [ ] Temperature monitoring for extreme conditions

Software:
  [ ] No sprintf/gets/strcpy (replaced with safe variants)
  [ ] No unused code paths (dead code removed)
  [ ] MISRA C compliance verified with static analysis
  [ ] No debug print statements containing sensitive data
```

---

## 4.11 Summary — Module 04

```
KEY TAKEAWAYS:

✓ Secure Boot = Chain of Trust from silicon to application
✓ HSM = all crypto operations must use HSM, keys never exposed to CPU
✓ Anti-rollback via OTP monotonic counter is mandatory
✓ JTAG/SWD MUST be fused OFF before production — this is non-negotiable
✓ Timing attacks → always use constant-time comparison functions
✓ Voltage/clock glitching → multiple redundant security checks
✓ MPU enforces memory isolation — data regions must be NX
✓ Side-channel resistance requires constant-time code + power masking
```

**Next Module**: [05 — CAN Bus Hacking & Defense](05_can_hacking.md)
