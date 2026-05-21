# AUTOSAR Cybersecurity Full Stack — Complete Learning Guide
## Configure · Implement · Validate · Attack · Defend

> Covers: AUTOSAR SecOC · CSM · KeyM · FVM · HSM · Secure Boot · TARA · Pen Testing

---

## Table of Contents

1. [AUTOSAR Security Architecture Overview](#1-autosar-security-architecture-overview)
2. [Crypto Service Manager (CSM)](#2-crypto-service-manager-csm)
3. [Secure Onboard Communication (SecOC)](#3-secure-onboard-communication-secoc)
4. [Key Manager (KeyM)](#4-key-manager-keym)
5. [Freshness Value Manager (FVM)](#5-freshness-value-manager-fvm)
6. [HSM Integration](#6-hsm-integration)
7. [Secure Boot Implementation](#7-secure-boot-implementation)
8. [Secure Software Update (FOTA)](#8-secure-software-update-fota)
9. [Secure Diagnostic Access](#9-secure-diagnostic-access)
10. [TLS & Network Layer Security](#10-tls--network-layer-security)
11. [Risk Analysis (TARA Deep-Dive)](#11-risk-analysis-tara-deep-dive)
12. [Cybersecurity Documentation Templates](#12-cybersecurity-documentation-templates)
13. [Security & Penetration Testing](#13-security--penetration-testing)
14. [CAN Bus Attacks & CAPL Security Scripts](#14-can-bus-attacks--capl-security-scripts)
15. [Firmware Security Debugging](#15-firmware-security-debugging)

---

## 1. AUTOSAR Security Architecture Overview

### 1.1 Security Module Stack

```
┌────────────────────────────────────────────────────┐
│              Application Layer (SWCs)               │
├────────────────────────────────────────────────────┤
│  SecOC      │  Dcm (Sec. Diag)  │  TLS / SomeIP-TP │
├─────────────┼───────────────────┼──────────────────┤
│        CSM (Crypto Service Manager)                 │  ← API layer
├────────────────────────────────────────────────────┤
│        CryIf (Crypto Interface)                     │  ← abstraction
├────────────────────────────────────────────────────┤
│  Crypto SW Driver   │   Crypto HW Driver (HSM)      │  ← providers
├─────────────────────┼──────────────────────────────┤
│  KeyM (Key Manager) │  FVM (Freshness Value Mgr)   │
└────────────────────────────────────────────────────┘
         ↕ SHE / EVITA / TrustZone / HSM Hardware
```

### 1.2 Module Responsibilities

| Module | AUTOSAR SWS | Role |
|--------|-------------|------|
| **CSM** | SWS_Csm | Unified API for crypto operations (encrypt, sign, verify, MAC) |
| **CryIf** | SWS_CryIf | Routes CSM calls to correct crypto driver |
| **Crypto SW** | SWS_CryptoDriver | Software crypto (AES, SHA, RSA in MCU) |
| **Crypto HW** | SWS_CryptoDriver | Hardware crypto (HSM, SHE, EVITA) |
| **KeyM** | SWS_KeyM | Manages key lifecycle: generation, storage, update, deletion |
| **SecOC** | SWS_SecOC | Adds MAC + freshness to CAN/LIN/Ethernet PDUs |
| **FVM** | SWS_Freshness | Provides/verifies monotonic freshness counters |
| **Dcm** | SWS_Dcm | UDS diagnostic services with access control |

### 1.3 AUTOSAR Security Interfaces — Data Flow (SecOC example)

```
Transmit Path (Sender ECU):
  SWC writes PDU data
        │
  SecOC receives PDU
        │
  CSM_MacGenerate(keyId, data, &mac)  ←── CryIf ──→ HSM AES-CMAC
        │
  SecOC appends MAC + Freshness Counter to PDU
        │
  PduR → CanIf → CAN bus

Receive Path (Receiver ECU):
  CAN bus → CanIf → PduR → SecOC
        │
  SecOC extracts data, MAC, FC
        │
  CSM_MacVerify(keyId, data, mac)  ←── HSM verification
        │
  SecOC checks freshness (FVM)
        │
  If OK: PDU passed to SWC
  If FAIL: PDU dropped; DEM event logged
```

---

## 2. Crypto Service Manager (CSM)

### 2.1 Configuration (ARXML / DaVinci Configurator)

```xml
<!-- CsmJob: defines a specific crypto job -->
<ELEMENTS>
  <CSM-JOB>
    <SHORT-NAME>CsmJob_AesCmac_Generate</SHORT-NAME>
    <CSM-JOB-PRIMITIVES>
      <CSM-MAC-GENERATE-PRIMITIVE>
        <!-- Maps to a CryIf channel → Crypto HW driver -->
        <CRYPTO-KEY-REF DEST="CryptoKeyType">/Crypto/KeyTypes/AesCmac128Key</CRYPTO-KEY-REF>
        <PROCESSING-MODE>CSM_PROCESSING_SYNC</PROCESSING-MODE>
      </CSM-MAC-GENERATE-PRIMITIVE>
    </CSM-JOB-PRIMITIVES>
  </CSM-JOB>
</ELEMENTS>
```

### 2.2 CSM API Usage in C

```c
#include "Csm.h"

/* MAC Generation — used by SecOC internally, or directly by SWC */
Std_ReturnType result;
uint8  mac[16];           /* 128-bit MAC output */
uint32 macLength = 16u;

/* Set key material (typically done at startup via KeyM) */
Csm_KeySetValid(CSM_KEY_ID_SECOC_TX);  /* Activate loaded key */

/* Generate AES-128-CMAC over payload */
result = Csm_MacGenerate(
    CSM_JOB_ID_CMAC_GENERATE,   /* Job ID from configuration */
    CRYPTO_OPERATIONMODE_SINGLECALL,
    (const uint8*)payload,       /* Input data pointer */
    payloadLen,                  /* Input data length in bytes */
    mac,                         /* Output MAC buffer */
    &macLength                   /* Output MAC length */
);

if (result == E_OK) {
    /* MAC generated successfully */
} else if (result == CRYPTO_E_BUSY) {
    /* HSM is busy; retry or use async callback */
}

/* MAC Verification */
result = Csm_MacVerify(
    CSM_JOB_ID_CMAC_VERIFY,
    CRYPTO_OPERATIONMODE_SINGLECALL,
    (const uint8*)payload,
    payloadLen,
    received_mac,
    16u,
    &verifyResult          /* CRYPTO_E_VER_OK or CRYPTO_E_VER_NOT_OK */
);
```

### 2.3 Supported Operations

| CSM Function | Description | Algorithm Examples |
|---|---|---|
| `Csm_Encrypt` / `Csm_Decrypt` | Symmetric encryption | AES-128-CBC, AES-128-GCM |
| `Csm_MacGenerate` / `Csm_MacVerify` | Message authentication | AES-128-CMAC, HMAC-SHA256 |
| `Csm_SignatureGenerate` / `Verify` | Asymmetric signature | RSA-2048-PKCS1, ECDSA-P256 |
| `Csm_Hash` | Cryptographic hash | SHA-256, SHA-384 |
| `Csm_KeyGenerate` | Key pair generation | ECDH, RSA |
| `Csm_KeyDerive` | Key derivation | HKDF, PBKDF2 |
| `Csm_KeyExchange` | Key agreement | ECDH |
| `Csm_RandomGenerate` | TRNG / PRNG | AUTOSAR TRNG |

### 2.4 Asynchronous Callback Pattern

```c
/* Declare callback — registered in CSM config */
void CsmCallback_MacGenerate(uint32 jobId, Std_ReturnType result) {
    if (result == E_OK) {
        /* MAC is ready in output buffer */
        SecOC_TxMacReady(jobId);
    } else {
        /* Log error via DEM */
        Dem_ReportErrorStatus(DEM_EVENT_CSM_MAC_FAIL, DEM_EVENT_STATUS_FAILED);
    }
}

/* Trigger async job */
Csm_MacGenerate(
    CSM_JOB_ID_CMAC_GENERATE_ASYNC,
    CRYPTO_OPERATIONMODE_SINGLECALL,
    data, dataLen, macBuf, &macLen
);
/* Function returns immediately; CsmCallback_MacGenerate called when HSM finishes */
```

---

## 3. Secure Onboard Communication (SecOC)

### 3.1 SecOC PDU Format

```
Standard CAN payload (8 bytes max):
┌────────────────────────────────────────────────────┐
│  Data  (e.g., 4 bytes)  │  FC Bits │  MAC (truncated) │
│  [application payload]  │ [3 bits] │  [up to 24 bits] │
└────────────────────────────────────────────────────┘
         └─────── Secured PDU ────────────────────────┘

FC = Freshness Counter (replayed from FVM)
MAC = truncated AES-128-CMAC over (data + full FC)
```

### 3.2 ARXML Configuration

```xml
<!-- SecOCTxPduProcessing: one entry per secured TX PDU -->
<SECOCPDUPROCESSING>
  <SHORT-NAME>SecOC_Tx_BMS_Command</SHORT-NAME>

  <!-- Link to the authentic (plain) PDU -->
  <AUTHPDUREF DEST="IPdu">/Ecuc/PduR/BMS_Command_PDU</AUTHPDUREF>

  <!-- Algorithm job reference -->
  <DATA-ID>0x0042</DATA-ID>  <!-- Unique 16-bit Data ID per PDU -->

  <!-- Freshness configuration -->
  <FRESHNESS-COUNTER-SYNC-ATTEMPT-LIMIT>3</FRESHNESS-COUNTER-SYNC-ATTEMPT-LIMIT>
  <FRESHNESS-VALUE-ID>FV_BMS_Command</FRESHNESS-VALUE-ID>

  <!-- MAC configuration -->
  <MESSAGE-AUTHENTICATION-CODE>
    <CSM-MAC-GENERATE-JOB-REF>/Csm/Jobs/CsmJob_AesCmac_Generate</CSM-MAC-GENERATE-JOB-REF>
    <AUTHENTICATION-BUILD-ATTEMPTS>3</AUTHENTICATION-BUILD-ATTEMPTS>
    <SECURED-AREA-LENGTH>12</SECURED-AREA-LENGTH>  <!-- bytes of truncated MAC -->
  </MESSAGE-AUTHENTICATION-CODE>
</SECOCPDUPROCESSING>
```

### 3.3 SecOC Runtime Behaviour

```c
/* SecOC transmit processing (called periodically from BSW task) */

/* Step 1: Receive authentic PDU from PduR */
SecOC_TxAuthenticPduType authPdu = { .data = payload, .length = 4 };

/* Step 2: Get freshness value from FVM */
uint8  fv[8];
uint16 fvLength = 8u;
FVM_GetTxFreshnessValue(FV_ID_BMS_CMD, fv, &fvLength);

/* Step 3: Build MAC input = Data ID || Authentic PDU || Freshness Value */
uint8 macInput[2 + 4 + 8];
macInput[0] = (uint8)(DATA_ID_BMS_CMD >> 8);
macInput[1] = (uint8)(DATA_ID_BMS_CMD);
memcpy(&macInput[2], authPdu.data, 4);
memcpy(&macInput[6], fv, 8);

/* Step 4: Generate MAC via CSM */
uint8  mac[16];
uint32 macLen = 16u;
Csm_MacGenerate(CSM_JOB_ID_CMAC, CRYPTO_OPERATIONMODE_SINGLECALL,
    macInput, sizeof(macInput), mac, &macLen);

/* Step 5: Truncate MAC and append FC bits to secured PDU */
SecuredPdu secPdu;
memcpy(secPdu.data, authPdu.data, 4);
secPdu.data[4] = fv[0] & 0x07;    /* 3 LSBs of counter */
secPdu.data[5] = mac[0];          /* 24-bit truncated MAC */
secPdu.data[6] = mac[1];
secPdu.data[7] = mac[2];

/* Step 6: Pass secured PDU to PduR → CanIf */
PduR_SecOCTransmit(SECOC_TX_PDU_ID_BMS_CMD, &secPdu);
```

### 3.4 SecOC Verification (Receiver Side)

```c
/* On PDU reception from CAN */
SecOC_RxIndication(SECOC_RX_PDU_ID_BMS_CMD, &securedPdu);

/* Internal SecOC verification steps: */
/* 1. Extract data, FC bits, truncated MAC from secured PDU */
/* 2. FVM_GetRxFreshness(): reconstruct full freshness value from FC bits + stored counter */
/* 3. Re-compute expected MAC over (DataID || data || full FV) */
/* 4. Compare truncated MAC with received MAC */
/* 5. If match: pass authentic PDU to SWC via PduR */
/* 6. If mismatch: */
/*    - Increment failure counter */
/*    - Report DEM event: SECOC_E_FRESHNESS_FAILURE or SECOC_E_AUTHENTICATION_FAILURE */
/*    - Drop PDU (do NOT pass to SWC) */
```

---

## 4. Key Manager (KeyM)

### 4.1 Key Lifecycle

```
[Factory/HSM Provisioning]
        │
   Key Material loaded into HSM NVM during production
        │
[AUTOSAR Startup]
        │
   KeyM_Init() → load key metadata from NVM
        │
[Runtime Use]
        │
   Csm_KeySetValid(keyId)   — activate for crypto operations
   Csm_KeyElementGet(...)   — read non-secret key properties
        │
[Key Update (FOTA or OBD-II)]
        │
   KeyM_Update() → receive new encrypted key blob via DCM/UDS 0x2E
   → Verify signature on key blob
   → Decrypt with transport key (stored in HSM)
   → Store new key in HSM NVM
   → Deactivate old key; activate new key
        │
[Decommissioning]
        │
   KeyM_Delete() → HSM securely erases key material
```

### 4.2 Key Types and Usage

| Key Name | Algorithm | Bit Size | Usage |
|----------|-----------|---------|-------|
| SecOC session key | AES-CMAC | 128 | MAC for each secured PDU |
| Boot verification key | RSA / ECDSA | 2048 / 256 | Verify firmware signature at boot |
| TLS server certificate | RSA / ECDSA | 2048 / 256 | TLS handshake for Ethernet ECU |
| OTA transport key | AES-GCM | 128/256 | Encrypt/authenticate firmware update |
| Seed-key master | AES-ECB | 128 | Derive ECU-specific seed-key pairs |
| X.509 CA cert (trust anchor) | RSA-PSS | 4096 | Root of trust for PKI chain |

### 4.3 Key Provisioning in Production

```
Production line flow:
┌──────────────────────────────────────────────────────────────┐
│  Secure Key Provisioning Server (PKI backend)                │
│  - Generates ECU-unique key pair                             │
│  - Signs with CA private key                                 │
│  - Encrypts key blob with transport key                      │
└──────────────────────────────┬───────────────────────────────┘
                               │ JTAG / Programming Flash
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  ECU / HSM (during end-of-line programming)                  │
│  - HSM receives encrypted key blob                           │
│  - HSM decrypts with factory transport key (pre-injected)    │
│  - Stores keys in HSM secure NVM (not accessible via CPU)    │
│  - Verifies integrity; reports PASS/FAIL to production line  │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Freshness Value Manager (FVM)

### 5.1 Why Freshness Matters

Without a freshness value, an attacker can **replay** a captured valid SecOC frame. FVM prevents replay attacks by ensuring each frame has a unique, monotonically increasing counter.

### 5.2 FVM Architectures

```
Architecture 1: Counter-based (simplest)
  - Each secured PDU has a 64-bit monotonic counter
  - Incremented on every transmit
  - Only 3 LSBs sent in CAN payload (bandwidth constraint)
  - Receiver reconstructs full counter using sync frames
  - PRO: simple  CON: counter sync across ECUs needed

Architecture 2: Trip Counter + Message Counter (AUTOSAR FreshnessValueManager spec)
  - 40-bit FV = [TripCounter(15) | ResetCounter(5) | MessageCounter(20)]
  - TripCounter: incremented each ignition cycle (stored in NVM)
  - MessageCounter: incremented each transmit; reset on new trip
  - Only MessageCounter LSBs sent inline; TC sync via separate bus frame
```

### 5.3 FVM Configuration (Typical)

```c
/* FVM PDU Configuration (generated from ARXML) */
const FvmPduConfigType FvmPduConfig[] = {
    {
        .freshnessValueId    = FV_ID_BMS_CMD,
        .freshnessValueLength = 40u,         /* bits */
        .freshnessValueTxLength = 4u,        /* bits sent inline in CAN */
        .messageCounterLength = 20u,
        .tripCounterLength   = 15u,
        .maxCounterJump      = 15u,          /* allow receiver to skip N missed frames */
        .keySlotRef          = KEY_SLOT_BMS_CMD
    },
};
```

---

## 6. HSM Integration

### 6.1 HSM Types in Automotive

| HSM Type | Standard | Key Size | Features |
|---------|---------|---------|---------|
| **SHE (Secure Hardware Extension)** | SHE spec v1.1 | 128-bit | AES-128, CMAC, basic RNG, 10 key slots |
| **EVITA Full** | EVITA spec | 128/256-bit | AES, RSA-2048, ECC-256, hash, 16+ key slots |
| **EVITA Medium** | EVITA spec | 128-bit | AES only, fewer key slots |
| **TrustZone (ARM)** | ARM TrustZone | Any | Isolated Secure World; flexible |
| **TPM 2.0** | TCG TPM 2.0 | 128/256-bit | Platform integrity, PCR, endorsement keys |

### 6.2 SHE API (Example — ETAS or similar)

```c
#include "She.h"

/* AES-128-CMAC using SHE (key slot KEY_1) */
uint8 mac[16];
She_ReturnType ret = She_CmdGenerateMac(
    SHE_KEY_ID_KEY_1,     /* Key slot (not the actual key value!) */
    messageLength * 8u,   /* Message length in BITS */
    message,              /* Pointer to input data */
    mac                   /* Output MAC */
);

if (ret != SHE_ERC_NO_ERROR) {
    /* SHE error codes: SHE_ERC_KEY_INVALID, SHE_ERC_KEY_EMPTY, etc. */
}

/* Load a key into SHE (protected by M1..M5 protocol) */
/* This is typically done via KeyM — not called directly in application */
She_CmdLoadKey(M1, M2, M3, M4, M5);
```

### 6.3 HSM Security Properties

```
SHE Key Flags (per key slot):
┌─────────────────────────────────────────────────────┐
│ Flag           │ Meaning                            │
├────────────────┼────────────────────────────────────┤
│ WRITE_PROTECT  │ Key cannot be overwritten          │
│ BOOT_PROTECT   │ Key usable only during secure boot │
│ DEBUGGER_PROT  │ Key inaccessible when debugger     │
│                │ is connected                       │
│ KEY_USAGE      │ Restrict to ENCRYPT/MAC/BOOT use   │
│ WILDCARD       │ Challenge: any answer accepted     │
└─────────────────────────────────────────────────────┘

SHE Key Loading (M1..M5 Protocol):
  New key loading requires knowledge of Authorization Key (SECRET_KEY or a parent key)
  → Prevents unauthorized key injection
  → M1: KeyId, AuthKeyId
  → M2: AES-CBC(NewKey || KeyFlags) with derivation of AuthKey
  → M3: CMAC(M1||M2) — integrity proof
  → M4, M5: proof of correct key loading (for verification)
```

---

## 7. Secure Boot Implementation

### 7.1 Boot Chain

```
Power-On
    │
[ROM Boot (HW-verified)]
    │  Verifies: BL0 signature with OTP-burned public key hash
    ▼
[Bootloader Stage 0 (BL0) — Minimal, in ROM]
    │  Verifies: BL1 signature with certificate chain
    ▼
[Bootloader Stage 1 (BL1) — Flash, read-only]
    │  Verifies: AUTOSAR BSW image with RSA-2048 or ECDSA-P256
    ▼
[AUTOSAR BSW / OS]
    │  Verifies: SWC partitions (optional, per security concept)
    ▼
[Application SWCs]
```

### 7.2 Firmware Signature Verification in C

```c
/* Secure boot verification — BL1 verifying AUTOSAR image */
#include "Csm.h"
#include "NvM.h"

#define FIRMWARE_START_ADDR  0x00010000UL
#define FIRMWARE_LENGTH      0x00080000UL  /* 512 KB */
#define SIGNATURE_ADDR       0x0000FF00UL  /* RSA-2048 signature in flash */
#define SIGNATURE_LEN        256u          /* 2048 bits = 256 bytes */
#define PUBLIC_KEY_SLOT_ID   CSM_KEY_SLOT_BOOT_VERIFY

SecureBootStatus_t verifyFirmwareImage(void) {
    Crypto_VerifyResultType verifyResult;
    uint8  hashBuffer[32];    /* SHA-256 output */
    uint32 hashLen = 32u;
    Std_ReturnType ret;

    /* Step 1: Compute SHA-256 hash of firmware region */
    ret = Csm_Hash(
        CSM_JOB_ID_SHA256,
        CRYPTO_OPERATIONMODE_SINGLECALL,
        (const uint8*)FIRMWARE_START_ADDR,
        FIRMWARE_LENGTH,
        hashBuffer,
        &hashLen
    );
    if (ret != E_OK) return SECBOOT_HASH_FAIL;

    /* Step 2: Verify RSA-2048-PKCS1v15 signature over hash */
    ret = Csm_SignatureVerify(
        CSM_JOB_ID_RSA_VERIFY,
        CRYPTO_OPERATIONMODE_SINGLECALL,
        hashBuffer,
        hashLen,
        (const uint8*)SIGNATURE_ADDR,
        SIGNATURE_LEN,
        &verifyResult
    );
    if (ret != E_OK || verifyResult != CRYPTO_E_VER_OK) {
        /* CRITICAL: Signature invalid — do NOT boot application */
        handleBootFailure();     /* Fallback: stay in BL, request OTA update */
        return SECBOOT_SIG_FAIL;
    }

    return SECBOOT_OK;
}

static void handleBootFailure(void) {
    /* Options: */
    /* 1. Stay in BL and wait for valid firmware via OBD-II/FOTA */
    /* 2. Boot golden/fallback image if available */
    /* 3. Set DTC and enter degraded mode */
    /* NEVER: silently boot corrupted/unsigned firmware */
    DEM_ReportEvent(DEM_EVENT_SECBOOT_FAIL);
    /* Signal to VCM: security issue detected */
}
```

### 7.3 Memory Protection (MPU)

```c
/* AUTOSAR OS / ARM Cortex-M MPU setup for memory isolation */
#include "Os_Hal_Mpu.h"

/* Configure MPU regions at startup to enforce memory separation */
const Os_Hal_MpuRegionConfigType MpuConfig[] = {
    {
        /* Region 0: Application SWC partition — no execute from RAM */
        .BaseAddress  = 0x20000000U,
        .Size         = MPU_REGION_SIZE_128KB,
        .AccessPermission = MPU_PRIV_RW_USER_RW,
        .DisableExec  = TRUE,    /* No execute from RAM — prevents code injection */
        .SubRegions   = 0x00U
    },
    {
        /* Region 1: HSM shared memory — no direct CPU write */
        .BaseAddress  = 0x40060000U,   /* HSM mailbox address */
        .Size         = MPU_REGION_SIZE_4KB,
        .AccessPermission = MPU_PRIV_RO_USER_NO,  /* Read-only for CPU */
        .DisableExec  = TRUE,
        .SubRegions   = 0x00U
    },
    {
        /* Region 2: Bootloader region — locked after BL hands off to app */
        .BaseAddress  = 0x00000000U,
        .Size         = MPU_REGION_SIZE_64KB,
        .AccessPermission = MPU_PRIV_RO_USER_NO,  /* App cannot write BL */
        .DisableExec  = FALSE,
        .SubRegions   = 0x00U
    }
};
```

---

## 8. Secure Software Update (FOTA)

### 8.1 OTA Update Security Requirements

| Requirement | Mechanism |
|------------|-----------|
| Authenticity: only authorised updates | RSA/ECDSA signature on update package |
| Confidentiality: IP protection | AES-128-GCM encryption of firmware binary |
| Integrity: no bit-flip corruption | SHA-256 hash + signature covers full package |
| Anti-rollback: can't downgrade to old/vulnerable firmware | Monotonic version counter in OTP/HSM |
| Safe install: no partial update bricks ECU | A/B partition scheme |

### 8.2 Update Package Validation

```c
/* FOTA package validation before flash write */
typedef struct {
    uint8  signature[256];    /* RSA-2048 signature */
    uint8  aesGcmIv[12];      /* AES-GCM IV (12 bytes for NIST) */
    uint8  aesGcmTag[16];     /* AES-GCM authentication tag */
    uint32 targetEcuId;       /* Must match this ECU's hardware ID */
    uint32 softwareVersion;   /* New version number */
    uint32 encryptedLength;   /* Length of encrypted firmware blob */
    uint8  encryptedData[];   /* Variable-length encrypted firmware */
} OtaPackage_t;

FotaStatus_t validateOtaPackage(const OtaPackage_t* pkg) {
    /* 1. Verify ECU target matches */
    if (pkg->targetEcuId != getHardwareEcuId()) return FOTA_WRONG_TARGET;

    /* 2. Anti-rollback: new version must be > current */
    uint32 currentVersion = NvM_GetSoftwareVersion();
    if (pkg->softwareVersion <= currentVersion) return FOTA_ROLLBACK_DENIED;

    /* 3. Verify RSA signature over (IV || tag || targetEcuId || version || encData) */
    Crypto_VerifyResultType sigResult;
    Csm_SignatureVerify(
        CSM_JOB_ID_RSA_VERIFY_OTA,
        CRYPTO_OPERATIONMODE_SINGLECALL,
        (uint8*)&pkg->aesGcmIv,          /* signed data starts after signature field */
        sizeof(*pkg) - 256u + pkg->encryptedLength,
        pkg->signature, 256u,
        &sigResult
    );
    if (sigResult != CRYPTO_E_VER_OK) return FOTA_SIG_FAIL;

    /* 4. AES-GCM decrypt + verify tag (ensures confidentiality + integrity) */
    uint8* decrypted = allocateFotaBuffer(pkg->encryptedLength);
    uint32 decryptedLen = pkg->encryptedLength;
    Csm_AeadDecrypt(
        CSM_JOB_ID_AES_GCM_DECRYPT,
        CRYPTO_OPERATIONMODE_SINGLECALL,
        CSM_KEY_ID_OTA_TRANSPORT,
        pkg->aesGcmIv, 12u,
        pkg->encryptedData, pkg->encryptedLength,
        NULL, 0,                  /* no additional authenticated data */
        decrypted, &decryptedLen,
        pkg->aesGcmTag            /* verified by AES-GCM internally */
    );

    return FOTA_VALIDATION_OK;
}
```

---

## 9. Secure Diagnostic Access

### 9.1 UDS Security Access (Service 0x27)

The Seed-Key mechanism authenticates a tester before granting access to privileged functions (ECU programming, calibration, security log read).

```c
/* UDS 0x27 SecurityAccess handler */
#include "Dcm.h"

/* Access levels (configured in Dcm ARXML) */
#define SEC_LEVEL_SUPPLIER_01    0x01u   /* Basic: read DTC */
#define SEC_LEVEL_ENGINEER_03    0x03u   /* Advanced: parameter write */
#define SEC_LEVEL_EOL_05         0x05u   /* End-of-line: flash programming */

/* 0x27 SubFunction 0x01: RequestSeed */
Dcm_ReturnType Dcm_SecurityAccess_RequestSeed_Level01(
    Dcm_OpStatusType    opStatus,
    uint8*              seedBuffer,
    uint16*             seedLength,
    Dcm_NegativeResponseCodeType* errorCode)
{
    /* Generate 16-byte random seed using HSM TRNG */
    Std_ReturnType ret = Csm_RandomGenerate(
        CSM_JOB_ID_TRNG,
        seedBuffer,
        16u
    );
    if (ret != E_OK) {
        *errorCode = DCM_E_CONDITIONSNOTCORRECT;
        return DCM_E_NOT_OK;
    }

    /* Store seed for later comparison (ECU-internal, never sent again) */
    storeCurrentSeed(SEC_LEVEL_SUPPLIER_01, seedBuffer, 16u);

    *seedLength = 16u;
    return DCM_E_OK;
}

/* 0x27 SubFunction 0x02: SendKey */
Dcm_ReturnType Dcm_SecurityAccess_SendKey_Level01(
    Dcm_OpStatusType    opStatus,
    const uint8*        keyBuffer,
    uint16              keyLength,
    Dcm_NegativeResponseCodeType* errorCode)
{
    uint8  expectedKey[16];
    uint8  currentSeed[16];

    getCurrentSeed(SEC_LEVEL_SUPPLIER_01, currentSeed);

    /* Derive expected key: AES-128-ECB(MasterKey, Seed) */
    /* MasterKey is stored in HSM — CPU never sees it */
    Csm_Encrypt(
        CSM_JOB_ID_AES_ECB_ENCRYPT,
        CRYPTO_OPERATIONMODE_SINGLECALL,
        currentSeed, 16u,
        expectedKey, NULL
    );

    /* Constant-time comparison — prevents timing attacks */
    if (!constantTimeMemCmp(keyBuffer, expectedKey, 16u)) {
        incrementSecurityAccessFailCounter();   /* Lockout after 3 failures */
        *errorCode = DCM_E_INVALIDKEY;
        return DCM_E_NOT_OK;
    }

    /* Unlock ECU for this session */
    Dcm_SetSecurityLevel(SEC_LEVEL_SUPPLIER_01);
    return DCM_E_OK;
}

/* Constant-time comparison (CRITICAL for security — prevents timing side-channel) */
static bool constantTimeMemCmp(const uint8* a, const uint8* b, size_t len) {
    uint8 diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= a[i] ^ b[i];   /* XOR: 0 only if all bytes match */
    }
    return diff == 0;
}
```

### 9.2 Diagnostic Security Lockout

```c
/* Rate limiting to prevent brute-force of seed-key */
typedef struct {
    uint8  failCount;
    uint32 lockoutTimestamp_ms;
    bool   isLocked;
} SecurityLockout_t;

static SecurityLockout_t lockout[MAX_SECURITY_LEVELS];

void incrementSecurityAccessFailCounter(uint8 level) {
    lockout[level].failCount++;
    if (lockout[level].failCount >= 3u) {
        lockout[level].isLocked = TRUE;
        lockout[level].lockoutTimestamp_ms = Os_GetSystemTimer_ms();
        /* Report to DEM */
        Dem_ReportEvent(DEM_EVENT_SECACCESS_LOCKOUT, DEM_EVENT_STATUS_FAILED);
    }
}

bool isSecurityAccessAllowed(uint8 level) {
    if (!lockout[level].isLocked) return TRUE;

    /* 10-second lockout window */
    uint32 elapsed = Os_GetSystemTimer_ms() - lockout[level].lockoutTimestamp_ms;
    if (elapsed > 10000u) {
        lockout[level].isLocked   = FALSE;
        lockout[level].failCount  = 0u;
        return TRUE;
    }
    return FALSE;
}
```

---

## 10. TLS & Network Layer Security

### 10.1 TLS 1.3 on Automotive Ethernet ECUs

```c
/* Using wolfSSL (common automotive TLS stack) */
#include "wolfssl/ssl.h"

/* Server-side TLS 1.3 session setup */
WOLFSSL_CTX* ctx = wolfSSL_CTX_new(wolfTLSv1_3_server_method());

/* Load ECU certificate and private key (from HSM key slot) */
wolfSSL_CTX_use_certificate_file(ctx, "/certs/ecu_cert.pem",  SSL_FILETYPE_PEM);
wolfSSL_CTX_use_PrivateKey_file(ctx,   "/certs/ecu_key.pem",  SSL_FILETYPE_PEM);

/* Require client certificate verification (mutual TLS) */
wolfSSL_CTX_set_verify(ctx, SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, NULL);
wolfSSL_CTX_load_verify_locations(ctx, "/certs/ca_cert.pem", NULL);

/* Restrict to secure cipher suites only */
wolfSSL_CTX_set_cipher_list(ctx,
    "TLS13-AES256-GCM-SHA384:TLS13-CHACHA20-POLY1305-SHA256");

WOLFSSL* ssl = wolfSSL_new(ctx);
wolfSSL_set_fd(ssl, client_socket_fd);

if (wolfSSL_accept(ssl) != SSL_SUCCESS) {
    /* TLS handshake failed — log error, close socket */
    int err = wolfSSL_get_error(ssl, 0);
    /* Log err via DEM/Syslog */
}
```

### 10.2 TLS 1.3 Handshake (Reference)

```
Client (Tester/Backend)          ECU (Server)
        │                              │
        │───── ClientHello ────────────►│
        │      [supported ciphers,      │
        │       key share (ECDH)]       │
        │                              │
        │◄────  ServerHello ────────────│
        │◄────  Certificate ────────────│  ECU presents its X.509 cert
        │◄────  CertificateVerify ──────│  Proves possession of private key
        │◄────  Finished ───────────────│
        │                              │
        │─────  Certificate ───────────►│  Client cert (if mutual TLS)
        │─────  CertificateVerify ─────►│
        │─────  Finished ──────────────►│
        │                              │
        │════════ Encrypted App Data ══════│
```

### 10.3 SOME/IP Security

```
SOME/IP with TLS (SOME/IP-TP over TLS):
- Service discovery: UDP broadcast (no TLS — limit sensitive discovery)
- Service methods and events: TCP with TLS 1.3
- Access control: SOME/IP-SD Service Authentication (AuTh plugin)

Key SOME/IP attack surfaces:
1. Service Discovery: Spoofed OFFER messages → attacker injects fake services
2. Method calls: No authentication by default → anyone on Ethernet segment can call any service
3. Subscription events: Event injection if no MAC verification
```

---

## 11. Risk Analysis (TARA Deep-Dive)

### 11.1 Full TARA Process (ISO 21434 Clause 15)

```
Step 1: Asset Identification
    → What data / functions does the item have?
    → Which have cybersecurity properties (CIA)?

Step 2: Threat Scenarios (STRIDE per asset)
    → Who would attack, and how?
    → What is the damage scenario if attack succeeds?

Step 3: Impact Rating (SFOP — Safety, Financial, Operational, Privacy)
    → Rate each damage scenario: Negligible / Moderate / Major / Severe

Step 4: Attack Path Analysis
    → How does attacker reach the asset? (attack tree)
    → What vulnerabilities or weaknesses are exploited?

Step 5: Attack Feasibility Rating (ISO 21434 Annex B)
    → Elapsed time / Expertise / Knowledge / Equipment / Window of opportunity
    → Total = sum of lowest individual scores
    → Overall: High (0–3) / Medium (4–10) / Low (11–19) / Very Low (≥20)

Step 6: Risk Determination
    → Risk = Damage Impact × Attack Feasibility
    → Risk levels: Unreasonable / Reasonable (tolerability criteria)

Step 7: Cybersecurity Goals
    → For each unacceptable risk: define goal (e.g., "Authenticate all BMS CAN frames")

Step 8: Countermeasure Selection
    → Map each goal to a technical control
    → Assign CAL (Cybersecurity Assurance Level): CAL1–CAL4
```

### 11.2 Attack Tree Example — Remote Engine Disable

```
Goal: Attacker remotely disables engine via CAN injection

OR
├── Path A: TCU Exploit → CAN Gateway → ECU
│   AND
│   ├── Exploit TCU (remote code execution via CVE in HTTP server)
│   ├── Pivot to internal CAN bus (no firewall on gateway)
│   └── Inject UDS routine control 0x31 to TCM
│
├── Path B: OBD-II Port → Physical CAN Access
│   AND
│   ├── Physical access to OBD-II port
│   ├── Bypass UDS Security Access (brute-force seed-key or exploit weak algo)
│   └── Send CAN frame directly
│
└── Path C: V2X Message Injection
    AND
    ├── Forge V2X DSRC message (no PKI cert validation in target ECU)
    └── ECU accepts unsigned V2X command as trusted

Feasibility per path:
  Path A: Expertise=Expert, Equipment=Standard PC, Time=Weeks → Feasibility=Medium
  Path B: Expertise=Low, Equipment=ELM327, Time=Hours → Feasibility=High
  Path C: Expertise=Expert, Equipment=SDR, Time=Months → Feasibility=Low
```

### 11.3 CVSS v3.1 for Automotive Scoring

```
CVSS Base Score formula:
  AV:N/L/A/P  Attack Vector (Network/Local/Adjacent/Physical)
  AC:L/H      Attack Complexity
  PR:N/L/H    Privileges Required (None/Low/High)
  UI:N/R      User Interaction
  S:U/C       Scope (Unchanged/Changed — does exploit cross security boundary?)
  C:N/L/H     Confidentiality Impact
  I:N/L/H     Integrity Impact
  A:N/L/H     Availability Impact

Example — Remote TCU exploit allowing CAN injection:
  AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
  Base Score: 10.0 (Critical)

Example — OBD-II physical seed-key bypass:
  AV:P/AC:H/PR:N/UI:N/S:C/C:L/I:H/A:H
  Base Score: 7.3 (High)

Automotive supplement (CVSS-AutomotiveAnnex):
  Additional metric: Safety Impact (SI:N/L/H/C) — Critical addition for vehicles
```

### 11.4 HEAVENS Risk Model (Alternative to ISO 21434 rating)

```
HEAVENS (HEAling Vulnerabilities to ENhance Software Security) adds:
- Likelihood (instead of feasibility)
- Security Level (SL 0–4, analogous to ASIL in safety)

Risk Level (HEAVENS):
  SL0: No security requirements
  SL1: Low — protect against opportunistic attacks
  SL2: Medium — protect against scalable attacks
  SL3: High — protect against expert attacks with resources
  SL4: Critical — protect against nation-state level attacks
```

---

## 12. Cybersecurity Documentation Templates

### 12.1 Cybersecurity Plan — Required Sections (ISO 21434 Clause 9)

```
Document: Cybersecurity Plan — [Project Name] — [ECU Name]

1. SCOPE
   1.1 Item description (ECU, interfaces, use cases)
   1.2 Cybersecurity activities (what will be done)
   1.3 Relationship to safety plan (ISO 26262)

2. ROLES & RESPONSIBILITIES
   2.1 Cybersecurity Manager
   2.2 Cybersecurity Engineer
   2.3 Penetration Test Team
   2.4 Supplier responsibilities

3. CYBERSECURITY ACTIVITIES
   3.1 TARA (Threat Analysis & Risk Assessment)
   3.2 Cybersecurity requirements specification
   3.3 Design phase cybersecurity activities
   3.4 Implementation guidelines (MISRA, secure coding)
   3.5 Verification & validation plan (pen test, fuzz, code review)
   3.6 Cybersecurity case (evidence collection)

4. SCHEDULE
   4.1 Milestones aligned to system development phases
   4.2 Entry/exit criteria per phase

5. TOOLS & ENVIRONMENT
   5.1 Static analysis tools (Polyspace, Coverity, MISRA checker)
   5.2 Pen testing tools and lab setup
   5.3 Cryptographic library (wolfSSL, mbedTLS, HSM SDK)

6. EVIDENCE & TRACEABILITY
   6.1 Requirement traceability matrix (TARA goals → CS requirements → tests)
   6.2 Review records
   6.3 Test reports
```

### 12.2 Cybersecurity Requirement Example

```
[CS-REQ-001]
Title: SecOC Authentication for Safety-Critical CAN PDUs
Description: All CAN PDUs classified as safety-critical in the item definition
             SHALL be protected by SecOC using AES-128-CMAC with a minimum
             truncated MAC length of 24 bits and a 64-bit freshness value.
Rationale: TARA identified threat T-BMS-03 (CAN message spoofing, risk=Critical).
           AES-128-CMAC with freshness counters mitigates spoofing and replay.
CAL: CAL3 (high attack feasibility, major impact)
Allocated to: SecOC module, CSM, FVM, KeyM
Verification method: V&V test SecOC_TC_001 (MAC generation and verification)
                     + Penetration test PT-CAN-02 (replay attempt)
Status: [Approved / In Development / Verified]
```

---

## 13. Security & Penetration Testing

### 13.1 Penetration Testing Scope in Automotive

```
External Attack Surface:
├── Telematics (4G/5G, MQTT, REST API)
├── V2X / DSRC / C-V2X communications
├── BLE (remote key fob, app pairing)
├── Wi-Fi (hotspot, diagnostic access)
└── OBD-II / CAN via OBD dongle

Internal Attack Surface (after initial access):
├── CAN bus (Classic CAN, CAN-FD)
├── LIN bus
├── FlexRay
├── Automotive Ethernet (SOME/IP, DoIP)
└── JTAG / UART / SWD (physical debug access)
```

### 13.2 CAN Bus Fuzzing

```python
# Python + python-can: CAN bus fuzzer
import can
import random
import struct

bus = can.interface.Bus(channel='can0', bustype='socketcan')

def fuzz_can_id_space():
    """Send frames across the entire 11-bit CAN ID range"""
    for can_id in range(0x000, 0x800):
        # Random 8-byte payload
        payload = bytes([random.randint(0, 0xFF) for _ in range(8)])
        msg = can.Message(
            arbitration_id=can_id,
            data=payload,
            is_extended_id=False
        )
        try:
            bus.send(msg)
        except can.CanError:
            pass

def replay_attack(captured_frame, count=100):
    """Replay a captured valid frame to test for replay protection"""
    for _ in range(count):
        bus.send(captured_frame)
        # Check if ECU responds differently on later replays

def mutation_fuzzer(seed_frame, iterations=10000):
    """Bit-flip fuzzer on captured valid frame"""
    for _ in range(iterations):
        payload = bytearray(seed_frame.data)
        # Flip a random bit
        byte_idx = random.randint(0, len(payload)-1)
        bit_idx  = random.randint(0, 7)
        payload[byte_idx] ^= (1 << bit_idx)
        msg = can.Message(
            arbitration_id=seed_frame.arbitration_id,
            data=bytes(payload),
            is_extended_id=seed_frame.is_extended_id
        )
        bus.send(msg)
```

### 13.3 UDS / OBD-II Penetration Testing

```python
# python-udsoncan: systematic UDS security testing
import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.services import SecurityAccess, DiagnosticSessionControl

conn = IsoTPSocketConnection('can0', rxid=0x7E8, txid=0x7E0)
client = udsoncan.Client(conn, request_timeout=2.0)

with client:
    # Step 1: Enter extended diagnostic session
    client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)

    # Step 2: Request seed (Security Level 01)
    response = client.request_seed(0x01)
    seed = response.service_data.seed

    # Step 3: Attempt brute-force (if no lockout)
    for attempt in range(0xFFFF):
        key = struct.pack('>H', attempt) + b'\x00' * 14  # 16-byte key attempt
        try:
            client.send_key(0x02, key)
            print(f"KEY FOUND: {key.hex()}")
            break
        except udsoncan.exceptions.NegativeResponseException as e:
            if e.code == 0x35:  # InvalidKey
                continue
            elif e.code == 0x36:  # ExceededNumberOfAttempts
                print("Lockout triggered — waiting")
                break

    # Step 4: Read memory (if access granted)
    try:
        data = client.read_memory_by_address(0x00010000, 1024)
        # If ECU returns firmware bytes: missing access control!
    except Exception as e:
        print(f"ReadMemory blocked: {e}")

    # Step 5: Test for unprotected WriteDataByIdentifier
    try:
        # Without SecurityAccess — should return 0x33 (SecurityAccessDenied)
        client.write_data_by_id(0xF190, b'ATTACKER_ECU_ID_!!')
    except udsoncan.exceptions.NegativeResponseException as e:
        print(f"Expected rejection: {e.code:#x}")
```

### 13.4 BLE / Wi-Fi Attack Testing

```
BLE Attack Scenarios on Automotive ECUs:
1. Unauthenticated pairing (Just Works)
   → Tool: gatttool, BLEsuite
   → Test: Connect without PIN/OOB pairing; read/write GATT characteristics

2. BLE MITM (for Legacy Pairing)
   → Tool: GATTacker, Braktooth exploits
   → Test: Intercept pairing; clone ECU BLE identity

3. Replay of BLE command (no freshness)
   → Test: Capture door unlock; replay after legitimate session ends

Wi-Fi Attack Scenarios:
1. Hotspot default credentials
   → Scan ECU Wi-Fi SSID; attempt default passwords (ECU_OEM / 12345678)

2. DHCP/ARP spoofing → MITM on vehicle Wi-Fi
   → Intercept HTTPS traffic to backend (check for cert pinning)

3. WPA2 PMKID attack (modern, no handshake needed)
   → Tool: hcxdumptool + hashcat
   → Test: Crack hotspot WPA2 PSK offline
```

### 13.5 Physical Attacks (JTAG / UART)

```
Steps for ECU Physical Attack Assessment:

1. IDENTIFY DEBUG INTERFACES
   - Probe PCB for JTAG pins: TDI, TDO, TCK, TMS, TRST
   - Probe for UART: TX, RX, GND (usually 115200 baud)
   - Use JTAGulator or multimeter for pin identification

2. ATTEMPT JTAG ACCESS
   - Tool: OpenOCD + J-Link / SEGGER
   - Try: openocd -f interface/jlink.cfg -f target/stm32f4x.cfg
   - If locked: attempt fault injection to unlock (ChipWhisperer)
   - Test: Can we read/write flash without SecurityAccess?

3. UART CONSOLE
   - Connect UART adapter; try common baud rates: 115200, 57600, 9600
   - Look for: bootloader prompt, Linux shell, diagnostic menu
   - Test: Boot into recovery mode; boot from USB

4. FAULT INJECTION
   - Voltage glitching during secure boot signature check window
   - Target: the comparison instruction (branch after signature verify)
   - Tool: ChipWhisperer; Riscure Inspector
   - A successful glitch bypasses signature verification → arbitrary boot

5. SIDE-CHANNEL ANALYSIS
   - Power analysis (SPA/DPA) to extract AES keys from SW implementations
   - Protection: use hardware AES (SHE/HSM) which is side-channel resistant
```

### 13.6 Fuzz Testing with boofuzz

```python
# boofuzz: network/protocol fuzzer for SOME/IP or DoIP
from boofuzz import *

def open_session():
    """Connect to ECU Ethernet port"""
    session = Session(
        target=Target(connection=TCPSocketConnection("192.168.1.10", 13400)),
        sleep_time=0.1
    )
    return session

session = open_session()

# Define DoIP Activation Request fuzzing
s_initialize("DoIP_ActivationRequest")
s_static(b'\x02\xfd')           # Protocol version
s_static(b'\x00\x05')           # Payload type: Routing Activation Request
s_size("payload", length=4, endian='>')   # Length field
s_block_start("payload")
s_word(0x0E00, name="source_address", fuzzable=True)   # Logical address
s_static(b'\x00')               # Activation type
s_static(b'\x00\x00\x00\x00')  # Reserved
s_block_end("payload")

session.connect(s_get("DoIP_ActivationRequest"))
session.fuzz()
```

---

## 14. CAN Bus Attacks & CAPL Security Scripts

### 14.1 CAN Bus Attack Types

| Attack | Description | Defence |
|--------|-------------|---------|
| **Eavesdropping** | Passive sniffing of unencrypted CAN frames | Payload encryption (rare on CAN due to bandwidth) |
| **Spoofing** | Send CAN frame with forged ID | SecOC: MAC on all safety-critical PDUs |
| **Replay** | Re-transmit captured valid frame | Freshness counter in SecOC |
| **Fuzzing** | Random frames to find ECU crashes | Robust input validation, watchdog timers |
| **Bus-off attack** | Force ECU into bus-off by inducing 16 errors | Error counters; redundant ECU modes |
| **Flooding / DoS** | High-priority frames starve others | Frame rate limiting at gateway; IDPS |

### 14.2 CAPL: SecOC Replay Attack Test

```capl
/*
 * SecOC_ReplayTest.can
 * Tests that receiver ECU rejects replayed SecOC frames
 * (Freshness counter must reject older/same counter values)
 */

variables {
    message 0x123 captureBuf;    /* Captured SecOC-protected frame */
    int replayCount = 0;
    int maxReplays  = 10;
    int rejectCount = 0;
}

/* Capture the first valid SecOC frame on the bus */
on message 0x123 {
    if (replayCount == 0) {
        captureBuf = this;
        write("SecOC frame captured: ID=0x%X FC_bits=%d MAC[0]=0x%02X",
              this.id, this.byte(4) & 0x07, this.byte(5));
    }
}

/* After capture, replay the same frame multiple times */
on key 'r' {
    int i;
    write("Starting replay attack — sending %d identical frames", maxReplays);
    for (i = 0; i < maxReplays; i++) {
        output(captureBuf);
        testWaitForTimeout(20);   /* 20ms between replays */
    }
    write("Replay complete. Check ECU DEM for SECOC_E_FRESHNESS_FAILURE");
}

/* Monitor for ECU DTC that confirms replay was detected */
on diagRequest BMS.ReadDtcInformation {
    /* Check if DTC 0xD00001 (SecOC Freshness Failure) is active */
}

/* Monitor for any ECU response that shouldn't occur after replay */
on message 0x200 {
    /* 0x200 = BMS response — should NOT appear for replayed command */
    write("WARNING: ECU responded to frame %d — replay attack may have succeeded!", replayCount);
}
```

### 14.3 CAPL: CAN ID Scanner

```capl
/*
 * CAN_ID_Scanner.can
 * Sends frames across all CAN IDs and logs ECU responses
 * Use to map unknown ECU interface
 */

variables {
    int scanId         = 0;
    int scanComplete   = 0;
    int responseCount  = 0;
    message 0x000 scanMsg;
}

on start {
    scanId = 0x001;
    write("CAN ID scan starting from 0x001 to 0x7FF");
    setTimer(scanTimer, 5);   /* Send every 5ms */
}

on timer scanTimer {
    if (scanId > 0x7FF) {
        write("Scan complete. Responses received: %d", responseCount);
        scanComplete = 1;
        return;
    }

    scanMsg.id  = scanId;
    scanMsg.dlc = 8;
    /* Send standard diagnostic query: 0x02 0x10 0x01 (Start Session) */
    scanMsg.byte(0) = 0x02;
    scanMsg.byte(1) = 0x10;
    scanMsg.byte(2) = 0x01;
    output(scanMsg);

    scanId++;
    setTimer(scanTimer, 5);
}

/* Log any response from any ECU */
on message * {
    if (!scanComplete && this.id != scanMsg.id) {
        write("Response from ID 0x%03X to query on 0x%03X: %02X %02X %02X",
              this.id, scanId - 1,
              this.byte(0), this.byte(1), this.byte(2));
        responseCount++;
    }
}
```

### 14.4 CAPL: Bus-Off Attack Test

```capl
/*
 * BusOff_Attack_Test.can
 * Verifies ECU recovers from bus-off within required time
 * (ISO 11898: bus-off after 256 consecutive errors)
 */

variables {
    msTimer recoveryTimer;
    int busOffDetected = 0;
    int recoveryTime_ms;
    message 0x100 errorMsg;
}

on start {
    write("Bus-off recovery test: inducing bus errors");
    /* Vector CANoe / CANalyzer CAN error injection API */
    canSetBusOffSimulation(1);   /* Enable bus-off simulation on this channel */
}

/* CANoe callback when bus-off condition detected on channel */
on busOff {
    busOffDetected = 1;
    recoveryTimer  = 0;
    setTimer(recoveryTimer, 1000);   /* Start 1-second timeout */
    write("Bus-off detected at t=%f ms", timeNow() / 1e4);
}

/* ECU should re-integrate to bus within this window */
on timer recoveryTimer {
    if (busOffDetected) {
        write("FAIL: ECU did not recover from bus-off within 1000ms");
        testFailed("BusOff_Recovery_Timeout");
    }
}

/* Detect ECU bus-on (recovery) */
on busOn {
    if (busOffDetected) {
        write("PASS: ECU recovered from bus-off");
        testPassed("BusOff_Recovery");
        busOffDetected = 0;
    }
}
```

---

## 15. Firmware Security Debugging

### 15.1 Security-Relevant Debug Techniques

```
Debugging Checklist for Secure Firmware:

1. VERIFY HSM ISOLATION
   - Memory map: confirm HSM shared RAM is not CPU-writable
   - Test: attempt to write HSM mailbox from CPU application code → should fault

2. VERIFY MPU ENFORCEMENT
   - Inject deliberately wrong memory access (write to read-only region)
   - Expected: UsageFault / MemManage fault immediately
   - Log: MPU fault handler should capture PC of faulting instruction

3. VERIFY SECURE BOOT CHAIN
   - Replace firmware signature with corrupted bytes
   - Expected: boot halts at signature verification; enters recovery BL
   - Test tool: Flash programmer to modify last bytes of binary

4. VERIFY SECOC DROP BEHAVIOUR
   - Inject CAN frame with corrupted MAC (flip one MAC byte)
   - Expected: SecOC_RxIndication reports E_NOT_OK; DEM event raised
   - Verify: SWC does NOT receive the PDU

5. VERIFY DIAGNOSTIC LOCKOUT
   - Send 3 incorrect keys via UDS 0x27; 4th attempt should get 0x36 response
   - Verify: DEM stores security lockout event
```

### 15.2 Hardened Debug Build Configuration

```c
/* Compile-time security assertions */
#if defined(PRODUCTION_BUILD)
  /* Disable all debug output in production */
  #define SECDBG_PRINT(...)  ((void)0)
  /* Disable test backdoors */
  #define SECURITY_TEST_BACKDOOR_ENABLED  0
  /* Enforce production key usage */
  #define CSM_KEY_ID_SECOC_TX  CSM_KEY_ID_PRODUCTION_SECOC
#else
  #define SECDBG_PRINT(fmt, ...) printf("[SECDBG] " fmt "\n", ##__VA_ARGS__)
  #define CSM_KEY_ID_SECOC_TX  CSM_KEY_ID_DEV_SECOC   /* Test key, NOT for field */
#endif

/* Detect debug connector at runtime */
bool isDebuggerConnected(void) {
    /* ARM CoreDebug register */
    return (CoreDebug->DHCSR & CoreDebug_DHCSR_C_DEBUGEN_Msk) != 0;
}

void checkSecurityContext(void) {
    if (isDebuggerConnected()) {
        /* In production: disable keys with DEBUGGER_PROT flag */
        /* At minimum: log the event */
        Dem_ReportEvent(DEM_EVENT_DEBUGGER_DETECTED, DEM_EVENT_STATUS_FAILED);
        /* Optionally: wipe session secrets from RAM */
        secureClearBuffer(sessionKeys, sizeof(sessionKeys));
    }
}
```

### 15.3 Common Security Bugs Found in Code Review

| Bug | Example | Fix |
|-----|---------|-----|
| **Timing side-channel in key compare** | `memcmp(key1, key2, len)` short-circuits on first mismatch | Use constant-time comparison |
| **Seed entropy from predictable source** | `rand() % 0xFFFF` as seed | Use CSM TRNG: `Csm_RandomGenerate()` |
| **Hardcoded key in source** | `const uint8 aesKey[] = {0x00,...}` in .c file | Keys ONLY in HSM/KeyM; never in source |
| **Unprotected UDS memory read** | `ReadMemoryByAddress` with no security level check | Check `Dcm_GetSecurityLevel() >= LEVEL_ENGINEER` |
| **SecOC key same across all ECUs** | One key for entire vehicle fleet | ECU-unique keys derived from VIN + ECU-ID |
| **Stale freshness after ECU reset** | FC starts at 0 after power cycle → replay window | Store FC in NVM with wear-levelling; sync with FVM |
| **Unchecked return value from CSM** | Ignoring `E_NOT_OK` from `Csm_MacVerify` | Always check return AND `verifyResult` output parameter |
| **Debug build key in production flash** | Dev key in released firmware | CI/CD gate: scan binary for known test key patterns |

---

## Quick Reference: Automotive Cybersecurity Tool List

| Category | Tool | Use |
|----------|------|-----|
| CAN capture/analysis | Vector CANalyzer, Wireshark + SocketCAN | Traffic capture, protocol decode |
| CAN fuzzing | caringcaribou, CANSPY, python-can | Identify CAN-accessible functions |
| UDS testing | python-udsoncan, CANdela Studio | Diagnostic service testing |
| BLE testing | Wireshark (nRF Sniffer), GATTacker | BLE sniffing, GATT enumeration |
| Network fuzzing | boofuzz, Peach Fuzzer | SOME/IP, DoIP protocol fuzzing |
| Static analysis | Polyspace, Coverity, CodeChecker | MISRA, CWE-top25 detection |
| Binary analysis | Ghidra, IDA Pro | Firmware reverse engineering |
| Fault injection | ChipWhisperer, Riscure VCGlitcher | Bypass secure boot via voltage glitch |
| Penetration testing | Metasploit + automotive modules | Network-level attack simulation |
| TARA management | Ansys Medini Analyze, Polarion | TARA documentation, traceability |

---

*See also*: [01_iso21434_tara.md](01_iso21434_tara.md) for TARA fundamentals and ISO 21434 process overview.
