# Automotive Cybersecurity Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Automotive cybersecurity is now a regulatory requirement under **UNECE WP.29 (R155/R156)** and standardised in **ISO/SAE 21434**. Every connected ECU (TCU, IVI, gateway, OBD2 port) must be secured. Questions are increasingly common at **Aptiv, Harman, Qualcomm Automotive, Continental, and any OTA/telematics role**. You need to know the threat landscape, cryptographic primitives, secure boot, secure communication, and TARA methodology.

**Key areas:**
- ISO/SAE 21434 structure and TARA
- UNECE WP.29 R155/R156 requirements
- Threat categories: CAN injection, OBD2 attacks, OTA tampering, network intrusion
- Cryptographic fundamentals: AES, RSA, ECDSA, SHA-256, HMAC
- Secure Boot (ROM → bootloader → application chain of trust)
- Secure Communication: TLS 1.3, mTLS, DTLS for UDP
- Key management: HSM (Hardware Security Module), key provisioning
- SecOC (Secure On-Board Communication) in AUTOSAR
- Intrusion Detection Systems (IDPS) for automotive
- Vulnerability assessment and penetration testing basics

---

## THREAT LANDSCAPE

---

### Q1. What are the main cybersecurity threats to a connected vehicle?

**Expert Answer:**

```
Attack Surface Categories:

1. WIRELESS INTERFACES
   Bluetooth (pairing attacks, BT stack vulnerabilities)
   Wi-Fi (rogue AP, MITM on car hotspot)
   LTE/5G (IMSI catcher, SMS command injection)
   V2X (fake infrastructure messages, GPS spoofing)
   TPMS (wireless tyre pressure sensor — weak 315/433MHz)
   
2. PHYSICAL INTERFACES
   OBD-II port (most accessible — direct CAN access)
     → CAN injection, UDS session attacks, key learning
   JTAG/SWD debug port (read flash, bypass security)
   USB ports (IVI, media injection, exploit parsing)
   Charging port (ISO 15118 attack surface)
   
3. EXTERNAL COMMUNICATION
   OTA updates (tampered package, MITM, replay attack)
   Backend APIs (credential theft, insecure API endpoints)
   MQTT broker (unauthorised publish → fake commands)
   
4. IN-VEHICLE NETWORKS
   CAN bus (no authentication — any node can spoof any message)
     → Ghost messages: inject brake release, engine shutdown
   Automotive Ethernet (DoS, ARP spoofing, VLAN jumping)
   LIN (less critical but firmware updates via LIN)
   
5. SUPPLY CHAIN
   Compromised toolchain (malicious compiler, infected SDK)
   Third-party libraries with vulnerabilities (OpenSSL CVEs)
   Hardware trojans in components

Attack impact classification:
  Safety-critical: brake/steering/engine spoofing → human injury
  Privacy: location tracking, driver biometric data theft
  Financial: insurance fraud, remote theft, mileage tampering
  Operational: vehicle immobilisation, ransom
```

---

## CRYPTOGRAPHIC FUNDAMENTALS

---

### Q2. Explain the cryptographic algorithms used in automotive security. When to use each?

**Expert Answer:**

```
Algorithm   Type              Key size    Use case in automotive
──────────────────────────────────────────────────────────────────────
AES-128     Symmetric         128-bit     Encrypt flash, secure storage, ECU-ECU
AES-256     Symmetric         256-bit     High-value data (keys, calibration)
AES-GCM     Auth + Encrypt    128/256-bit TLS, secure CAN (authenticated + encrypted)
HMAC-SHA256 Message auth      Variable    CAN message authentication (SecOC)
SHA-256     Hash (integrity)  N/A         OTA firmware hash, certificate digest
SHA-384     Hash (integrity)  N/A         High-security certificates
RSA-2048    Asymmetric sig    2048-bit    Legacy, certificate signing (avoid new)
ECDSA-P256  Asymmetric sig    256-bit     OTA signature, secure boot (preferred)
ECDH-P256   Key exchange      256-bit     TLS handshake, session key derivation
X.509       Certificate       Variable    TLS certificates, device identity
──────────────────────────────────────────────────────────────────────

Why ECDSA over RSA in automotive?
  RSA-2048 signature: 256 bytes, slow (Cortex-M0: 3-5 seconds)
  ECDSA-P256 signature: 64 bytes, fast (Cortex-M0: 200-400ms)
  Automotive constraint: boot verification must complete quickly
  ECDSA is 10× faster verification with 4× smaller key/signature

Why not SHA-1 or MD5?
  SHA-1 broken (2017 collision attack — SHAttered)
  MD5 broken (1996 — trivially collide)
  Automotive standard: minimum SHA-256
  ISO 21434 Annex: SHA-256 or better mandatory for new designs

Secure key storage — why HSM?
  Software key storage: key in RAM or flash → vulnerable to memory attack
  HSM (Hardware Security Module):
    - Dedicated crypto co-processor (e.g., SHE, SHE+, EVITA Medium)
    - Keys never leave HSM — compute happens inside HSM
    - Physical tamper detection: erase keys on tamper
    - Example: Infineon TC397 has HSM with EVITA Full
    - Example: NXP S32G has CSE (Cryptographic Services Engine)
```

---

## SECURE BOOT

---

### Q3. Implement secure boot verification for an automotive ECU.

**Expert Answer:**

```c
/*
 * Secure Boot Implementation (simplified)
 * ROM → Bootloader → Application
 * Each stage verifies signature of next stage
 */

#include <stdint.h>
#include <stdbool.h>

/* ===== ECDSA-P256 signature structure ===== */
typedef struct {
    uint8_t r[32];  /* ECDSA r component */
    uint8_t s[32];  /* ECDSA s component */
} ECDSA_Signature_t;

/* ===== Firmware image header ===== */
#define FW_MAGIC    0xDEADBEEFUL
#define HEADER_SIZE 256U

typedef struct {
    uint32_t          magic;             /* FW_MAGIC: 0xDEADBEEF */
    uint8_t           version[4];        /* Major.Minor.Patch.Build */
    uint32_t          image_size;        /* Size of firmware (excluding header) */
    uint32_t          load_address;      /* Flash address of firmware start */
    uint8_t           sha256[32];        /* SHA-256 hash of firmware payload */
    ECDSA_Signature_t signature;         /* ECDSA-P256 signature over sha256 */
    uint8_t           reserved[HEADER_SIZE - 4 - 4 - 4 - 4 - 32 - 64];
} __attribute__((packed)) FW_Header_t;

/* ===== OEM Root of Trust public key (burned in OTP/ROM at manufacturing) ===== */
/* This is an EXAMPLE public key — real key is OEM-specific */
static const uint8_t s_oem_ecdsa_pubkey[64] = {
    /* x coordinate (32 bytes) */
    0xC9, 0x7B, 0x7A, 0xAE, 0x29, 0x79, 0x47, 0x3B,
    0xB3, 0x35, 0x68, 0x58, 0x41, 0x81, 0xAB, 0x08,
    0x82, 0x9D, 0x3B, 0xEA, 0x34, 0x6A, 0x1E, 0x1C,
    0xE5, 0x52, 0xD5, 0xCC, 0xE9, 0x5E, 0x7D, 0xC1,
    /* y coordinate (32 bytes) */
    0x49, 0x3B, 0x2C, 0x5E, 0xD8, 0x44, 0x29, 0xB9,
    0xF5, 0x4D, 0xD2, 0x46, 0xD0, 0x38, 0x8A, 0x30,
    0x15, 0x81, 0xAB, 0xCE, 0xF7, 0x24, 0xD5, 0x35,
    0xE5, 0xB1, 0x95, 0xED, 0xA6, 0x9C, 0xB1, 0x52
};

typedef enum {
    SECURE_BOOT_OK = 0,
    SECURE_BOOT_INVALID_MAGIC,
    SECURE_BOOT_HASH_MISMATCH,
    SECURE_BOOT_SIGNATURE_INVALID,
    SECURE_BOOT_VERSION_ROLLBACK,
} SecureBootResult_t;

SecureBootResult_t secure_boot_verify(const FW_Header_t *header,
                                       const uint8_t *fw_payload) {
    uint8_t computed_hash[32];
    
    /* Step 1: Check magic number */
    if (header->magic != FW_MAGIC) {
        return SECURE_BOOT_INVALID_MAGIC;
    }
    
    /* Step 2: Compute SHA-256 of firmware payload */
    sha256_compute(fw_payload, header->image_size, computed_hash);
    
    /* Step 3: Compare with header's claimed hash */
    if (memcmp(computed_hash, header->sha256, 32U) != 0) {
        /* Hash mismatch: firmware corrupted during OTA or flash */
        return SECURE_BOOT_HASH_MISMATCH;
    }
    
    /* Step 4: Verify ECDSA-P256 signature */
    /* Signature is over SHA-256 hash (prevents length-extension attacks) */
    int sig_rc = ecdsa_p256_verify(
        computed_hash,           /* 32-byte hash to verify */
        &header->signature,      /* ECDSA r+s (64 bytes) */
        s_oem_ecdsa_pubkey       /* OEM public key (ROM) */
    );
    if (sig_rc != 0) {
        /* Invalid signature: unauthorized firmware, abort */
        return SECURE_BOOT_SIGNATURE_INVALID;
    }
    
    /* Step 5: Anti-rollback check */
    /* Read minimum allowed version from OTP (incremented after each security fix) */
    uint32_t min_version = otp_read_minimum_fw_version();
    uint32_t fw_version  = *(uint32_t *)header->version;  /* Packed uint32 */
    if (fw_version < min_version) {
        /* Rollback attack: trying to install older (vulnerable) firmware */
        return SECURE_BOOT_VERSION_ROLLBACK;
    }
    
    return SECURE_BOOT_OK;
}

/* Called from ROM bootloader or primary bootloader */
void __attribute__((noreturn)) bootloader_main(void) {
    const FW_Header_t *app_header  = (const FW_Header_t *)APP_FLASH_BASE;
    const uint8_t     *app_payload = (const uint8_t *)(APP_FLASH_BASE + HEADER_SIZE);
    
    SecureBootResult_t result = secure_boot_verify(app_header, app_payload);
    
    if (result != SECURE_BOOT_OK) {
        /* Log failure to secure log (tamper-resistant NvM) */
        secure_log_write(LOG_SECURE_BOOT_FAIL, (uint32_t)result);
        
        /* Enter recovery mode — wait for new firmware via UDS */
        recovery_mode_enter();  /* Never returns */
    }
    
    /* Secure boot passed — jump to application */
    typedef void (*AppEntry_t)(void);
    AppEntry_t app_entry = (AppEntry_t)(*(uint32_t *)(APP_FLASH_BASE + HEADER_SIZE + 4U));
    
    /* Clean up: zero out any sensitive data in bootloader RAM before jumping */
    secure_memzero(bootloader_stack, sizeof(bootloader_stack));
    
    app_entry();  /* Jump to application */
    __builtin_unreachable();
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q4. A researcher reports a remote code execution vulnerability via OTA. What's your response process?

**Expert Answer:**

"This is a critical security incident requiring a coordinated response under **ISO 21434 §14 (Vulnerability Management)** and **UNECE R155 (CSMS)**:

**Immediate Response (0–4 hours):**
```
1. Severity assessment:
   - Remote code execution? Critical severity (CVSS 9.0+)
   - Can it be triggered without physical access? Yes → HIGH URGENCY
   - Can it affect safety functions? If yes → invoke ISO 26262 + 21434 joint process
   
2. Containment options:
   - Can we disable OTA campaigns immediately? YES → do it now
   - Contact cloud team: disable OTA endpoint for affected ECU type
   - Check if any vehicles are currently in OTA update → abort campaigns
   
3. Responsible disclosure:
   - Acknowledge researcher within 24h
   - Bug bounty program (if exists): trigger payment process
   - Do NOT disclose publicly until fix is ready (coordinated disclosure)
```

**Investigation (4–48 hours):**
```
Root cause analysis:
  - Reproduce in lab: validate the PoC
  - Identify vulnerable component: OTA parser? TLS implementation? bootloader?
  - Common OTA vulnerabilities:
    a) Integer overflow in size field → heap overflow
    b) Missing signature check on update notification message
    c) Outdated TLS library (e.g., OpenSSL CVE affecting device)
    d) Predictable nonce in ECDSA → key recovery

Fix development:
  - Input validation for all size fields
  - Enforce signature verification BEFORE any parsing
  - Update affected library (e.g., WolfSSL/mbedTLS patch)
  - Add input size caps (firmware image < 32MB, never allocate raw size)
```

**Fix Deployment (48h–2 weeks):**
```
- Fast-track OTA patch (security fix → skip full regression in non-safety modules)
- ISO 21434: security release requires TARA update, new risk assessment
- UNECE R155: notify OEM (type approval authority) of security incident + fix
- Staged rollout: 1% → 5% → 100% with anomaly monitoring

Code fix example:
```
```c
/* BEFORE (vulnerable) */
void ota_process_header(const uint8_t *data, size_t len) {
    uint32_t fw_size = *(uint32_t *)&data[4];  /* Attacker controls this */
    uint8_t *buf = malloc(fw_size);              /* No bounds check → heap overflow */
    memcpy(buf, &data[8], fw_size);
}

/* AFTER (secure) */
#define OTA_MAX_FIRMWARE_SIZE  (4U * 1024U * 1024U)  /* 4MB max */

int ota_process_header(const uint8_t *data, size_t len) {
    if (len < 8U) return -EINVAL;  /* Validate input length first */
    
    uint32_t fw_size;
    memcpy(&fw_size, &data[4], sizeof(fw_size));  /* Unaligned-safe copy */
    
    /* Validate size before any allocation */
    if (fw_size == 0U || fw_size > OTA_MAX_FIRMWARE_SIZE) {
        log_security("Invalid firmware size: %u", fw_size);
        return -ERANGE;
    }
    
    /* ALWAYS verify signature BEFORE allocating or parsing content */
    if (!ota_verify_notification_signature(data, len)) {
        return -EAUTH;
    }
    
    uint8_t *buf = secure_alloc(fw_size);  /* Fixed pool, not heap */
    if (!buf) return -ENOMEM;
    memcpy(buf, &data[8], fw_size);
    return 0;
}
```

---

## CHEAT SHEET — Automotive Cybersecurity

```
Key standards:
  ISO/SAE 21434: Cybersecurity engineering lifecycle (design to decommission)
  UNECE R155: Cyber Security Management System (CSMS) — type approval
  UNECE R156: Software Update Management System (SUMS) — OTA regulation
  ISO 15118: EV charging communication security
  AUTOSAR SecOC: Secure On-Board Communication (CAN message authentication)

Cryptographic choices:
  Signing:     ECDSA-P256 (fast on MCU, small key, preferred)
  Hashing:     SHA-256 minimum
  Symmetric:   AES-128-GCM (authenticated encryption)
  Auth codes:  HMAC-SHA256
  TLS:         TLS 1.3 minimum (TLS 1.2 with strong ciphers acceptable)

Secure boot chain:
  OTP public key (ROM) → verifies bootloader → verifies application
  Anti-rollback: OTP version counter (monotonically increasing)
  Each stage: SHA-256 hash → ECDSA signature verify

SecOC (AUTOSAR — CAN message authentication):
  Message = payload + MAC (Truncated CMAC/HMAC, 24–64 bits)
  Freshness counter: prevents replay attacks
  Example: steering angle on CAN — without SecOC, any node can spoof it

Common automotive attack patterns:
  CAN injection via OBD-II: plug in device, spoof messages
  Replay attack: record + replay CAN frames (without SecOC counter)
  OTA MITM: intercept + modify update (without ECDSA verification)
  API key leakage: hardcoded credentials in firmware → extract from flash
  Stack overflow via malformed Bluetooth pairing packet

Input validation rules:
  Always validate size before allocation (size > 0 && size < MAX)
  Always verify signature/MAC before parsing payload
  Never memcpy raw external length into stack buffers
  Never trust OBD-II or CAN bus input without authentication
```
