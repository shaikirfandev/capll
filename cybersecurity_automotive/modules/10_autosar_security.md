# Module 10 — AUTOSAR Security

> Level: Advanced | Est. study time: 8 hours

---

## 10.1 AUTOSAR Overview

AUTOSAR (AUTomotive Open System ARchitecture) is the dominant ECU software platform:

```
AUTOSAR CLASSIC (CP):          AUTOSAR ADAPTIVE (AP):
───────────────────────        ──────────────────────────
Target: MCU (AURIX, S32K)      Target: SoC (R-Car, S32G)
OS: AUTOSAR OS (OSEK-based)    OS: POSIX (QNX, Linux)
Com: CAN / LIN / FlexRay      Com: SOME/IP, DDS, Ethernet
Sched: Static (config-time)   Sched: Dynamic (runtime)
Update: Limited (UDS flash)   Update: Full OTA runtime
Memory: KB–MB                  Memory: GB-range
Security: HSM, SecOC, DCM     Security: TLS, mTLS, SROS2

Security Modules:
  Classic:          Adaptive:
  ├── SecOC         ├── ara::com (SOME/IP security)
  ├── Crypto Stack  ├── ara::crypto (Crypto API)
  ├── DCM (UDS)     ├── ara::iam (Identity & Access)
  ├── NvM (storage) ├── TLS (transport security)
  └── HSM Driver    └── Certificate management
```

---

## 10.2 SecOC (Secure Onboard Communication)

SecOC is the AUTOSAR module that adds message authentication to CAN:

```
SecOC PDU STRUCTURE:

  ┌─────────────────────────────┬──────────────────┬──────────────┐
  │    Authentic I-PDU          │  Freshness Value │     MAC      │
  │  (Original payload data)   │  (truncated)     │  (truncated) │
  │                             │                  │              │
  │  e.g., AEB_BrakeRequest    │  24-bit counter  │  32-bit CMAC │
  │  = 3 bytes                 │  = 3 bytes       │  = 4 bytes   │
  └─────────────────────────────┴──────────────────┴──────────────┘
  Total: 10 bytes (fits in 8-byte CAN frame with some compression)

MAC COMPUTATION:
  MAC = Truncate_32bit(
      CMAC-AES-128(
          SecOCKey,                    // 128-bit symmetric key, HSM-stored
          FreshnessValue ||            // prevents replay
          DataID ||                    // prevents cross-message attacks  
          AuthenticIPDU                // actual payload
      )
  )

Where SecOCKey is:
  - Provisioned per ECU-pair at end-of-line
  - Stored in HSM (never in readable flash)
  - Unique per message type (different keys for different critical signals)
```

### SecOC Configuration (AUTOSAR Classic)

```xml
<!-- SecOC module configuration (simplified) -->
<SecOCRxPduProcessing>
  <SecOCDataId>0x0244</SecOCDataId>          <!-- AEB control message -->
  <SecOCFreshnessValueLength>24</SecOCFreshnessValueLength>
  <SecOCAuthInfoTxLength>32</SecOCAuthInfoTxLength>  <!-- 32-bit MAC -->
  <SecOCFreshnessValueId>1</SecOCFreshnessValueId>
  <SecOCCsmJobReference>CsmJob_CMAC_AES128_Verify</SecOCCsmJobReference>
  <SecOCReceptionOverflowStrategy>REPLACE</SecOCReceptionOverflowStrategy>
  <SecOCVerificationStatusCalloutList>
    <SecOCVerificationStatusCallout>
      <SecOCFuncNameRef>/SecOCCallouts/AEB_Auth_Failed_Callout</SecOCFuncNameRef>
    </SecOCVerificationStatusCallout>
  </SecOCVerificationStatusCalloutList>
</SecOCRxPduProcessing>
```

### SecOC Freshness Value Management

```c
/* FreshnessValueManager (FVM) module handles anti-replay counters */

/* Freshness value storage in NvM (backed by HSM monotonic counter) */
typedef struct {
    uint32_t sendCounter;      /* Incremented on each transmission */
    uint32_t receiveCounter;   /* Highest received counter value */
    uint32_t acceptanceWindow; /* Max tolerated counter gap (e.g., 5) */
} FreshnessValue_t;

/* Sender side: Get freshness value for MAC computation */
Std_ReturnType FvM_GetTxFreshness(
    uint16_t freshnessValueId,
    uint8_t *freshnessValue,        /* Output: current counter value */
    uint32_t *freshnessValueLength  /* Output: length in bits */
) {
    FreshnessValue_t *fv = &freshnessDB[freshnessValueId];
    fv->sendCounter++;  /* Increment before each transmission */
    
    /* Write to NvM immediately (persist across reset) */
    NvM_WriteBlock(NVM_BLOCK_FRESHNESS, freshnessDB);
    
    /* Return counter as byte array */
    encode_counter(fv->sendCounter, freshnessValue, 3); /* 24-bit */
    *freshnessValueLength = 24;
    return E_OK;
}

/* Receiver side: Verify freshness (anti-replay check) */
Std_ReturnType FvM_GetRxFreshness(
    uint16_t freshnessValueId,
    const uint8_t *truncatedFreshness,   /* Received truncated counter */
    uint16_t truncatedFreshnessLength,
    uint16_t authVerifyAttempts,
    uint8_t *fullFreshnessValue,
    uint32_t *fullFreshnessValueLength
) {
    FreshnessValue_t *fv = &freshnessDB[freshnessValueId];
    uint32_t receivedCounter = decode_counter(truncatedFreshness, 3);
    
    /* Anti-replay: received must be > last accepted */
    if (receivedCounter <= fv->receiveCounter) {
        return SECOC_E_FRESHNESS_FAILURE;  /* Replay attack! */
    }
    
    /* Acceptance window: tolerate minor gaps (due to lost frames) */
    if (receivedCounter > fv->receiveCounter + fv->acceptanceWindow) {
        return SECOC_E_FRESHNESS_FAILURE;  /* Too large a jump */
    }
    
    fv->receiveCounter = receivedCounter;
    return E_OK;
}
```

---

## 10.3 AUTOSAR Crypto Stack

```
AUTOSAR CRYPTO STACK LAYERS:

  Application / SecOC / DCM
         │
  ┌──────▼──────────────────────────┐
  │  CSM (Crypto Service Manager)   │
  │  Unified API: AES, ECDSA, HASH  │
  │  Manages jobs, queuing          │
  └──────┬──────────────────────────┘
         │
  ┌──────▼──────────────────────────┐
  │  CryIf (Crypto Interface)       │
  │  Routes to correct driver       │
  └──────┬────────────────┬─────────┘
         │                │
  ┌──────▼──────┐  ┌───────▼──────┐
  │  Crypto SW  │  │  HSM Driver  │
  │  (software  │  │  (hardware   │
  │  fallback)  │  │  accelerated)│
  └─────────────┘  └─────────────┘

CSM API Usage:
  Csm_MacGenerate(jobId, CRYPTO_OPERATIONMODE_SINGLECALL,
                  data, dataLength,
                  macBuffer, &macLength)
                  
  Csm_MacVerify(jobId, CRYPTO_OPERATIONMODE_SINGLECALL,
                data, dataLength,
                mac, macLength,
                &verifyResult)
```

---

## 10.4 Secure Diagnostics (DCM Security)

```
AUTOSAR DCM (Diagnostic Communication Manager) security configuration:

DcmDsp_SecurityAccess_Level_Programming {
    SecurityLevel          = 0x11;    /* Level 0x11/0x12 for programming */
    SeedSize               = 8;       /* 8-byte seed (stronger) */
    KeySize                = 8;       /* 8-byte key */
    NumAttDelay            = 3;       /* Lockout after 3 wrong keys */
    DelayTime_ms           = 10000;   /* 10s lockout */
    SecurityDelayOnBoot_ms = 0;
    
    /* Security access function — calls into HSM */
    GetSecurityAttemptCounter_Fnc → Dcm_GetSecurityAttemptCounter();
    SetSecurityAttemptCounter_Fnc → Dcm_SetSecurityAttemptCounter();
    CompareKey_Fnc              → Dcm_CompareKey_HMAC();
    GetSeed_Fnc                 → Dcm_GetSeed_HW_RNG();
}

/* Session-service permission matrix */
DcmDspSession_Default_Allowed_Services = {
    0x10 (DSC), 0x11 (EcuReset), 0x19 (ReadDTC), 
    0x22 (RDBI: basic DIDs only), 0x3E (TesterPresent)
};

DcmDspSession_Extended_Allowed_Services = {
    Default services + 0x14 (ClearDTC), 0x2E (WDBI: restricted DIDs),
    0x2F (IOCBI: with additional checks), 0x31 (RC: non-flash routines)
};

DcmDspSession_Programming_Allowed_Services = {
    0x10, 0x11, 0x22, 0x27, 0x28, 0x3E,
    0x31 (RC: erase/check routines), 0x34, 0x36, 0x37
};
```

---

## 10.5 AUTOSAR Adaptive — ara::iam (Identity & Access Management)

```
ara::iam provides role-based access control for Adaptive AUTOSAR:

  Application A ──► ara::iam ──► Allowed to: subscribe /radar/objects
                                               publish /adas/commands
  Application B ──► ara::iam ──► NOT allowed to: publish /adas/commands
                                                  (access denied)
  
  Policy definition (JSON):
  {
    "subject": "ADAS_Fusion_App",
    "grant": [
      {"resource": "/radar/objects",  "action": "subscribe"},
      {"resource": "/camera/frames",  "action": "subscribe"},
      {"resource": "/adas/fusion",    "action": "publish"}
    ],
    "deny": [
      {"resource": "/adas/commands",  "action": "publish"},
      {"resource": "/diagnostics",    "action": "*"}
    ]
  }
  
  App identity verified by: certificate + hash of application binary (TPM-attested)
```

---

## 10.6 Memory Partitioning in AUTOSAR Classic

```c
/* MemMap.h — AUTOSAR memory map macros */

/* Code region — RX only (protected by MPU) */
#define ADAS_AEB_START_CODE
#define ADAS_AEB_STOP_CODE

/* Data region — RW, Non-Executable */
#define ADAS_AEB_START_VAR_INIT
#define ADAS_AEB_STOP_VAR_INIT

/* Shared memory between OS partitions */
#define ADAS_AEB_START_SHARED_VAR
#define ADAS_AEB_STOP_SHARED_VAR

/* MPU configuration (AUTOSAR OS Partition) */
OsMemoryProtectionRegion_AEB = {
    StartAddress     = ADAS_AEB_CODE_START;
    EndAddress       = ADAS_AEB_CODE_END;
    AccessPermission = EXECUTE | READ;    /* No write to code region */
}

OsMemoryProtectionRegion_AEB_Data = {
    StartAddress     = ADAS_AEB_DATA_START;
    EndAddress       = ADAS_AEB_DATA_END;
    AccessPermission = READ | WRITE;      /* No execute from data */
}
```

---

## 10.7 E2E Protection (End-to-End)

E2E protection is AUTOSAR's ISO 26262 mechanism for detecting transmission errors.
It provides data-level integrity (different from SecOC's security goal):

```
E2E PROFILE COMPARISON:

Profile  │ Checksum  │ Counter │ Use Case
─────────┼───────────┼─────────┼──────────────────────────
P01      │ CRC-8     │ 4-bit   │ Legacy CAN signals
P02      │ CRC-8     │ 4-bit   │ CAN, simple signals
P04      │ CRC-32    │ 16-bit  │ Ethernet, large PDUs
P07      │ CRC-64    │ 16-bit  │ Safety-critical large PDUs
PXF      │ CRC-32P4  │ 8-bit   │ AUTOSAR Flexible

E2E vs SecOC:
  E2E   = Detects transmission ERRORS (random faults, ISO 26262 concern)
          CRC computed without secret key → attacker can re-compute valid CRC
          
  SecOC = Detects MALICIOUS manipulation (cybersecurity concern)
          CMAC computed with secret key → attacker cannot forge without key
          
Both needed for safety-critical + security-critical messages:
  Payload → E2E wrapper → SecOC wrapper → CAN PDU
```

---

## 10.8 AUTOSAR Security Checklist

```
AUTOSAR CLASSIC:
  [ ] SecOC enabled on all safety-critical CAN messages
  [ ] Freshness value management uses NvM-backed counters
  [ ] CSM routes crypto operations to HSM driver (not SW fallback in production)
  [ ] DCM security access levels correctly defined per session
  [ ] Lockout after 3 failed Security Access attempts
  [ ] Programming session not reachable from default session without Security Access
  [ ] MPU configured for all OS partitions
  [ ] No partition can write to another partition's memory
  [ ] Debug macros disabled in production build
  [ ] JTAG fusing step in production flash script

AUTOSAR ADAPTIVE:
  [ ] ara::iam policies defined for all applications
  [ ] TLS 1.3 configured for all SOME/IP services
  [ ] Certificate rotation mechanism implemented
  [ ] ara::crypto uses platform HSM/TPM backend
  [ ] Container isolation verified (no shared namespaces between untrusted apps)
  [ ] SELinux/AppArmor policy active
  [ ] Hypervisor isolation between safety and infotainment VMs
```

---

## 10.9 Summary — Module 10

```
KEY TAKEAWAYS:

✓ SecOC = AUTOSAR's message authentication via CMAC-AES-128 + freshness value
✓ Freshness value (monotonic counter) prevents replay attacks on CAN
✓ E2E ≠ SecOC: E2E detects random errors; SecOC detects malicious attacks
✓ CSM abstracts crypto → all apps use same API regardless of HW or SW crypto
✓ DCM session/service permission matrix must be reviewed in every project
✓ ara::iam enforces least-privilege access in Adaptive AUTOSAR
✓ Memory partitioning (MPU) ensures OS partitions cannot access each other's memory
✓ HSM must be used for all key operations — no raw keys in application code
```

**Next Module**: [11 — Vehicle Penetration Testing](11_penetration_testing.md)
