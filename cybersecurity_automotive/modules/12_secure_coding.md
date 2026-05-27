# Module 12 — Secure Coding for Automotive

> Level: All Levels | Est. study time: 8 hours | Standards: MISRA C, CERT C, AUTOSAR C++14

---

## 12.1 MISRA C in a Security Context

MISRA C was designed for safety (ISO 26262), but its rules also prevent many security vulnerabilities:

| MISRA Rule | Security Relevance | What It Prevents |
|------------|-------------------|-----------------|
| Rule 17.7 | Return value checks | Ignore crypto errors → silent failure |
| Rule 14.3 | No always-true/false | Dead code hiding backdoors |
| Rule 22.1 | Resources released | Memory leaks → DoS |
| Rule 21.6 | No scanf | Format string attacks |
| Rule 11.3 | No ptr casting | Type confusion exploits |
| Rule 15.5 | Single exit | Bypass of security checks via multiple returns |
| Advisory 1.3 | Undefined behavior | Buffer overflows, signed overflow |

---

## 12.2 Buffer Overflow — Vulnerable vs Secure

```c
/* ─────────────── VULNERABLE CODE ─────────────── */

/* CWE-121: Stack-based buffer overflow */
void process_vin_VULNERABLE(char *received_vin) {
    char local_buffer[17];         /* VIN is exactly 17 chars */
    strcpy(local_buffer, received_vin);  /* DANGEROUS: no bounds check! */
    /* Attacker sends 100 bytes → overflows stack → RIP/LR overwrite */
    validate_vin(local_buffer);
}

/* UDS ReadDataByIdentifier response handler — VULNERABLE */
void handle_rdbi_VULNERABLE(uint8_t *response, uint16_t len) {
    uint8_t data[64];
    memcpy(data, response + 3, len);  /* DANGEROUS: len unvalidated! */
    /* Attacker sends len=255 in UDS response → 191 bytes overflow */
}


/* ─────────────── SECURE CODE ─────────────── */

/* CWE-121 Fixed: Bounds checking */
#define VIN_LENGTH 17

void process_vin_SECURE(const char *received_vin, size_t input_len) {
    if (received_vin == NULL) {
        return;
    }
    if (input_len != VIN_LENGTH) {
        log_security_event(SEC_EVENT_INVALID_VIN_LENGTH, input_len);
        return;
    }
    
    char local_buffer[VIN_LENGTH + 1];  /* +1 for null terminator */
    /* Safe copy with explicit length limit */
    (void)memcpy(local_buffer, received_vin, VIN_LENGTH);
    local_buffer[VIN_LENGTH] = '\0';    /* Explicit null termination */
    
    validate_vin(local_buffer);
}

/* UDS handler — SECURE */
#define MAX_DID_DATA_LEN 100

void handle_rdbi_SECURE(const uint8_t *response, uint16_t len) {
    /* Input validation at system boundary */
    if (response == NULL || len < 3u || (len - 3u) > MAX_DID_DATA_LEN) {
        log_security_event(SEC_EVENT_INVALID_UDS_LEN, len);
        return;
    }
    
    uint8_t data[MAX_DID_DATA_LEN];
    uint16_t data_len = len - 3u;
    (void)memcpy(data, response + 3u, data_len);
    process_did_data(data, data_len);
}
```

---

## 12.3 Integer Overflow

```c
/* ─────────────── VULNERABLE CODE ─────────────── */

/* CWE-190: Integer overflow in CAN DLC processing */
uint8_t* parse_can_frame_VULNERABLE(uint8_t *buf, uint8_t dlc) {
    uint16_t frame_size = dlc + HEADER_SIZE;  /* OVERFLOW if dlc=255, HEADER_SIZE=255 */
    uint8_t *frame = malloc(frame_size);
    if (frame == NULL) return NULL;
    memcpy(frame, buf, frame_size);           /* Heap overflow! */
    return frame;
}

/* Signal scaling overflow — VULNERABLE */
int32_t scale_speed_VULNERABLE(uint16_t raw_value) {
    return raw_value * 100;  /* OVERFLOW: 65535 * 100 = 6553500 > INT32_MAX? No in this case */
    /* But: raw_value * LARGE_SCALE could overflow silently */
}


/* ─────────────── SECURE CODE ─────────────── */

#define MAX_CAN_DLC     8u
#define HEADER_SIZE     4u
#define MAX_FRAME_SIZE  (MAX_CAN_DLC + HEADER_SIZE)  /* = 12 */

/* CWE-190 Fixed: Validate before arithmetic */
uint8_t* parse_can_frame_SECURE(const uint8_t *buf, uint8_t dlc) {
    if (buf == NULL || dlc > MAX_CAN_DLC) {
        return NULL;   /* Reject invalid DLC */
    }
    
    uint8_t frame[MAX_FRAME_SIZE];  /* Stack allocation, fixed size */
    uint16_t frame_size = (uint16_t)dlc + HEADER_SIZE;
    (void)memcpy(frame, buf, frame_size);
    process_frame_internal(frame, frame_size);
    return NULL;  /* No heap allocation needed */
}

/* Safe signal scaling */
#define SPEED_SCALE     100
#define SPEED_MAX_VALID 32767u  /* 327.67 km/h max possible */

int32_t scale_speed_SECURE(uint16_t raw_value) {
    if (raw_value > SPEED_MAX_VALID) {
        log_security_event(SEC_EVENT_SIGNAL_OVERFLOW, raw_value);
        return SPEED_INVALID_VALUE;
    }
    return (int32_t)raw_value * SPEED_SCALE;
}
```

---

## 12.4 Race Conditions in ECU Software

```c
/* ─────────────── VULNERABLE CODE ─────────────── */

/* CWE-362: TOCTOU (Time Of Check To Time Of Use) */
static uint8_t authenticated = 0;  /* Global auth state */
static uint8_t security_level = 0;

/* Task 1 (UDS handler — high priority) */
void UDS_SecurityAccess_Handler_VULNERABLE(void) {
    if (verify_seed_key()) {        /* CHECK */
        authenticated = 1;          /* Between CHECK and USE: Task 2 preempts! */
        security_level = 2;
    }
}

/* Task 2 (CAN handler — lower priority) */
void execute_programming_command_VULNERABLE(void) {
    if (authenticated == 1) {       /* USE — but auth was set by race! */
        start_firmware_download();  /* Unauthorized flash! */
    }
}


/* ─────────────── SECURE CODE ─────────────── */

/* Atomic state machine — no intermediate inconsistent state */
typedef enum {
    SEC_STATE_LOCKED     = 0,
    SEC_STATE_UNLOCKED_1 = 1,   /* Level 1: Extended session */
    SEC_STATE_UNLOCKED_2 = 2,   /* Level 2: Programming session */
} SecurityState_t;

static SecurityState_t g_securityState = SEC_STATE_LOCKED;

/* In AUTOSAR OS: mutual exclusion via GetResource/ReleaseResource */
void UDS_SecurityAccess_Handler_SECURE(void) {
    GetResource(RES_SECURITY_STATE);    /* AUTOSAR OS mutex */
    
    if (verify_seed_key_level2()) {
        g_securityState = SEC_STATE_UNLOCKED_2;
        /* State set atomically under lock */
    }
    
    ReleaseResource(RES_SECURITY_STATE);
}

void execute_programming_command_SECURE(void) {
    GetResource(RES_SECURITY_STATE);
    SecurityState_t state = g_securityState;  /* Read under lock */
    ReleaseResource(RES_SECURITY_STATE);
    
    if (state == SEC_STATE_UNLOCKED_2) {
        start_firmware_download();
    }
}
```

---

## 12.5 Secure Crypto Usage in C

```c
/* ─────────────── VULNERABLE CRYPTO ─────────────── */

/* CWE-798: Hardcoded cryptographic key */
static const uint8_t AES_KEY[16] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF
};  /* In .rodata → extractable from firmware binary! */

/* CWE-330: Predictable random number */
uint32_t generate_seed_VULNERABLE(void) {
    srand((unsigned int)time(NULL));   /* Predictable: clock-based */
    return (uint32_t)rand();           /* Only 32768 possible values on some platforms */
}

/* CWE-327: Broken algorithm */
void encrypt_firmware_VULNERABLE(uint8_t *data, size_t len) {
    uint8_t key = 0x42;
    for (size_t i = 0; i < len; i++) {
        data[i] ^= key;  /* XOR cipher = trivially broken */
    }
}


/* ─────────────── SECURE CRYPTO ─────────────── */

/* Key stored in HSM — never in application code */
#define HSM_KEY_HANDLE_UDS  ((Csm_KeyIdType)0x01)  /* Handle, not raw key */

/* Secure seed generation using HSM TRNG */
Std_ReturnType generate_seed_SECURE(uint8_t *seed_buf, uint8_t seed_len) {
    Std_ReturnType ret;
    
    if (seed_buf == NULL || seed_len == 0u || seed_len > 32u) {
        return E_NOT_OK;
    }
    
    /* Hardware True Random Number Generator via HSM */
    ret = Csm_RandomGenerate(
        CSM_JOB_RNG,          /* Pre-configured TRNG job */
        seed_buf,             /* Output buffer */
        seed_len              /* Requested length */
    );
    
    return ret;
}

/* Secure CMAC verification using HSM */
Std_ReturnType verify_mac_SECURE(
    const uint8_t *data, uint32_t data_len,
    const uint8_t *mac,  uint32_t mac_len
) {
    Csm_VerifyResultType result = CSM_VERIFY_NOT_OK;
    Std_ReturnType ret;
    
    ret = Csm_MacVerify(
        CSM_JOB_CMAC_VERIFY,  /* Uses HSM_KEY_HANDLE_UDS internally */
        CRYPTO_OPERATIONMODE_SINGLECALL,
        data, data_len,
        mac, mac_len,
        &result
    );
    
    if (ret != E_OK || result != CSM_VERIFY_OK) {
        log_security_event(SEC_EVENT_MAC_VERIFY_FAIL, 0);
        return E_NOT_OK;
    }
    
    return E_OK;
}
```

---

## 12.6 Secure IPC (Inter-Process Communication)

```c
/* AUTOSAR OS — Secure inter-task communication */

/* Shared memory between OS partitions: define interface explicitly */
typedef struct {
    uint8_t  adas_aeb_request;    /* 0 = no brake, 1 = brake */
    uint8_t  adas_aeb_validity;   /* 0 = invalid, 1 = valid */
    uint32_t adas_timestamp_ms;
    uint8_t  mac[4];              /* SecOC-style MAC for IPC data */
} ADAS_IPC_Data_t;

/* Only defined access interface — no direct pointer sharing */
Std_ReturnType ADAS_IPC_ReadAEBRequest(uint8_t *brake_req, uint8_t *valid) {
    const ADAS_IPC_Data_t *ipc = IPC_GetReadPointer(IPC_BLOCK_ADAS);
    
    if (ipc == NULL) {
        return E_NOT_OK;
    }
    
    /* Verify MAC before trusting data (even in IPC!) */
    if (verify_ipc_mac(ipc) != E_OK) {
        log_security_event(SEC_EVENT_IPC_MAC_FAIL, 0);
        *valid = 0;
        return E_NOT_OK;
    }
    
    /* Age check: data must not be older than 50ms */
    uint32_t age = get_current_time_ms() - ipc->adas_timestamp_ms;
    if (age > 50u) {
        *valid = 0;  /* Stale data — safety measure */
        return E_NOT_OK;
    }
    
    *brake_req = ipc->adas_aeb_request;
    *valid     = ipc->adas_aeb_validity;
    return E_OK;
}
```

---

## 12.7 Python Secure Coding (Automotive Tools/Scripts)

```python
# ─────────────── VULNERABLE PYTHON ───────────────

import subprocess
import os

# CWE-78: Command injection
def run_can_analysis(interface: str):
    os.system(f"candump {interface}")  # DANGEROUS: if interface = "vcan0; rm -rf /"

# CWE-89: SQL injection in telemetry DB
def get_vehicle_data(vin: str):
    query = f"SELECT * FROM vehicles WHERE vin = '{vin}'"  # DANGEROUS
    cursor.execute(query)

# Hardcoded credentials
API_KEY = "secret_key_12345"  # In source code → exposed in Git


# ─────────────── SECURE PYTHON ───────────────

import subprocess
import shlex
import sqlite3
from pathlib import Path

# CWE-78 Fixed: Use subprocess with list arguments (no shell=True)
ALLOWED_INTERFACES = frozenset({"can0", "vcan0", "PCAN0"})

def run_can_analysis_secure(interface: str):
    if interface not in ALLOWED_INTERFACES:
        raise ValueError(f"Interface '{interface}' not in allowlist")
    
    # No shell=True, arguments as list (no injection possible)
    result = subprocess.run(
        ["candump", interface],  # Shell metacharacters are literal strings
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

# CWE-89 Fixed: Parameterized queries
def get_vehicle_data_secure(vin: str):
    if not vin.isalnum() or len(vin) != 17:
        raise ValueError("Invalid VIN format")
    
    cursor.execute("SELECT * FROM vehicles WHERE vin = ?", (vin,))
    return cursor.fetchone()

# Credentials from environment variables (never hardcoded)
import os
API_KEY = os.environ.get("OTA_API_KEY")
if not API_KEY:
    raise RuntimeError("OTA_API_KEY environment variable not set")
```

---

## 12.8 CAPL Secure Coding

```capl
/* Secure CAPL: Input validation and injection defense */

on message * {
    /* Validate DLC before accessing data bytes */
    if (this.dlc < 4) {
        write("WARN: Message 0x%X has unexpected DLC %d — skip", this.id, this.dlc);
        return;
    }
    
    /* Validate signal range before using */
    float speed = getSignalValue("VehicleSpeed");
    if (speed < 0 || speed > 350.0) {
        write("SECURITY ALERT: Out-of-range speed value: %.1f km/h", speed);
        testStepFail("Speed signal out of physical range");
        return;
    }
    
    /* Counter validation — detect replay or counter reset */
    static byte lastCounter = 255;  /* Init to impossible value */
    byte currentCounter = (this.byte(3) & 0x0F);
    
    if (lastCounter != 255 && ((currentCounter - lastCounter) & 0x0F) != 1) {
        write("SECURITY ALERT: Counter discontinuity! Expected %d, got %d",
              (lastCounter + 1) & 0x0F, currentCounter);
    }
    lastCounter = currentCounter;
}

/* Validate UDS response before processing */
on diagResponse * {
    if (this.ResponseCode != 0) {
        write("UDS NRC: 0x%X — do not process response data", this.ResponseCode);
        return;
    }
    
    /* Check response length matches expected */
    if (this.size < 5 || this.size > 260) {
        write("SECURITY: Unexpected UDS response size: %d", this.size);
        return;
    }
}
```

---

## 12.9 Secure Coding Cheat Sheet

```
MEMORY:
  ✓ Use memcpy_s/strncpy instead of strcpy/strcat
  ✓ Always validate length before buffer operations
  ✓ Stack canaries enabled in production builds
  ✓ No dynamic allocation in safety-critical code paths
  ✓ Initialize all variables (no uninitialized memory reads)

INTEGERS:
  ✓ Check for overflow before arithmetic operations
  ✓ Use unsigned types for sizes/lengths (prevents negative index)
  ✓ Signal values: clamp to physical range before use
  ✓ Cast explicitly, never implicitly downcast

CRYPTO:
  ✓ No hardcoded keys (HSM or env variable)
  ✓ Use TRNG (hardware) for seeds, nonces, IVs
  ✓ Constant-time comparison for secrets (no early exit)
  ✓ Never implement your own crypto algorithm
  ✓ AES-256-GCM or AES-128-GCM (authenticated encryption)
  ✓ ECDSA P-256 minimum for signatures

INPUT VALIDATION:
  ✓ Validate ALL external inputs at system boundary
  ✓ CAN: validate DLC before accessing data bytes
  ✓ UDS: validate response length, service ID
  ✓ SOME/IP: validate payload length vs declared length
  ✓ Never trust: VIN from network, CAN data, UDS response payload

CONCURRENCY:
  ✓ Protect shared state with OS primitives (GetResource/ReleaseResource)
  ✓ Avoid global mutable state where possible
  ✓ Atomic read-modify-write for security-sensitive flags

ERROR HANDLING:
  ✓ Check return values of ALL crypto and security functions
  ✓ Fail closed: on error, deny access (not grant access)
  ✓ Log security events without exposing sensitive data in logs
  ✓ Never leak key material or secrets in error messages
```

---

## 12.10 Summary — Module 12

```
KEY TAKEAWAYS:

✓ Buffer overflows in UDS handlers are the most common ECU vulnerability
✓ Integer overflow in DLC/length fields leads to heap/stack overflows
✓ Race conditions in security state → authentication bypass
✓ Hardcoded keys in binary → extractable with binwalk + strings
✓ MISRA C compliance prevents most CWE categories
✓ Use Csm_MacVerify, not manual HMAC — abstraction ensures HSM usage
✓ Python scripts: subprocess list (not shell=True), parameterized SQL
✓ Constant-time comparison is MANDATORY for any secret comparison
✓ All external data is untrusted: validate length, range, format
```

**Next Module**: [13 — Automotive SOC & Incident Response](13_soc_incident_response.md)
