# OTA Updates Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Over-The-Air (OTA) update capability is now a **mandatory requirement** for connected vehicles (Tesla pioneered it; BMW, Mercedes, Volkswagen, and every major OEM now requires it). OTA involves the full stack: cloud backend, TCU telematics, firmware packaging, security (signing, verification), dual-bank flash, bootloader swap, and rollback. Questions appear at **Aptiv, Harman, Visteon, Qualcomm Automotive, and any connected ECU role**.

**Key areas:**
- OTA architecture (cloud → backend → SOTA/FOTA agents → ECU)
- SOTA (Software OTA) vs FOTA (Firmware OTA)
- Delta OTA (bsdiff/zstd) vs full OTA
- Package security: code signing (ECDSA-256), hash chain (SHA-256)
- Delivery: MQTT, HTTP range request, resumable download
- ECU-side: dual-bank flash, atomic swap, rollback
- Campaign management: staged rollout, fleet health monitoring
- Standards: OTA-related requirements in UNECE WP.29, ISO/SAE 21434
- Failure handling: interrupted download, failed self-test, fleet rollback

---

## OTA ARCHITECTURE

---

### Q1. Describe a complete automotive FOTA architecture from cloud to ECU flash.

**Expert Answer:**

```
Complete FOTA Architecture:

┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD BACKEND                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐ │
│  │  Campaign Mgmt  │   │  Package Store  │   │  Fleet Mgmt   │ │
│  │  (AWS IoT / OEM)│   │  (S3, CDN)      │   │  Dashboard    │ │
│  └────────┬────────┘   └────────┬────────┘   └───────────────┘ │
│           │                     │                               │
│           └──────────── Campaign Trigger (MQTT) ───────────────┘
└──────────────────────────────────────────────────────┬──────────┘
                                                       │ LTE/5G
                                                       │ TLS 1.3
┌──────────────────────────────────────────────────────▼──────────┐
│                    TCU (Telematics Control Unit)                 │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │ MQTT Client  │  │  OTA Manager   │  │  Package Validator   │ │
│  │ (AWS IoT SDK)│→ │  (State FSM)   │→ │  (ECDSA-256 verify)  │ │
│  └──────────────┘  └────────┬───────┘  └──────────┬───────────┘ │
│                             │                      │             │
│                    ┌────────▼──────────────────────▼──────────┐ │
│                    │  Download Manager (HTTP Range + resume)   │ │
│                    └────────────────────────────────────────── ┘ │
└────────────────────────────────────────────────────────┬─────────┘
                                                         │ CAN FD / Ethernet
┌────────────────────────────────────────────────────────▼─────────┐
│                    TARGET ECU (e.g., Gateway ECU)                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ AUTOSAR UDS FBL (Flash Bootloader)                          │ │
│  │  0x34 Request Download → 0x36 Transfer Data → 0x37 Exit    │ │
│  │  CRC-32 verify → Signature verify → Bank swap → Reset      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  Flash:   │ Bank A (Active, V1.2.3) │ Bank B (Staging, V1.3.0) │ │
└───────────────────────────────────────────────────────────────────┘
```

---

### Q2. Implement an OTA state machine with download, verify, and rollback logic.

**Expert Answer:**

```c
/*
 * TCU OTA Firmware Update Manager
 * Handles: download → verify → flash → swap → rollback
 */

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* OTA state machine states */
typedef enum {
    OTA_STATE_IDLE       = 0,
    OTA_STATE_NOTIFIED,      /* New firmware version available */
    OTA_STATE_DOWNLOADING,   /* HTTP download in progress */
    OTA_STATE_VERIFYING,     /* SHA-256 + ECDSA signature check */
    OTA_STATE_FLASHING,      /* Writing to inactive bank via UDS */
    OTA_STATE_VERIFYING_FW,  /* Post-flash CRC verification */
    OTA_STATE_PENDING_REBOOT,/* Waiting for safe moment to reboot */
    OTA_STATE_REBOOTING,     /* Reset issued, bootloader will swap */
    OTA_STATE_VALIDATING,    /* Post-boot: is new FW working? */
    OTA_STATE_COMMITTED,     /* Confirmed — OTA complete */
    OTA_STATE_ROLLING_BACK,  /* Self-test failed → swap back */
    OTA_STATE_ERROR          /* Unrecoverable error */
} OTA_State_t;

typedef struct {
    OTA_State_t  state;
    char         package_url[256];
    char         version[32];
    uint8_t      expected_sha256[32];  /* From campaign notification */
    uint8_t      expected_sig[64];     /* ECDSA-256 signature */
    uint32_t     firmware_size;
    uint32_t     downloaded_bytes;     /* For resume */
    uint8_t     *staging_buffer;       /* Or: directly write to flash */
    uint8_t      retry_count;
    uint8_t      rollback_attempts;
    uint32_t     last_error;
} OTA_Context_t;

static OTA_Context_t s_ota;

/* ===== State transitions ===== */

OTA_State_t ota_process_notification(const char *url, const char *ver,
                                     const uint8_t *sha256, uint32_t size) {
    if (s_ota.state != OTA_STATE_IDLE) {
        log_warn("[OTA] Notification ignored — already in state %d", s_ota.state);
        return s_ota.state;
    }
    
    strncpy(s_ota.package_url, url, sizeof(s_ota.package_url) - 1U);
    strncpy(s_ota.version, ver, sizeof(s_ota.version) - 1U);
    memcpy(s_ota.expected_sha256, sha256, 32U);
    s_ota.firmware_size     = size;
    s_ota.downloaded_bytes  = 0U;
    s_ota.retry_count       = 0U;
    
    log_info("[OTA] New firmware available: v%s, %u bytes", ver, size);
    
    /* Check storage space before committing */
    if (flash_inactive_bank_size() < size) {
        log_error("[OTA] Insufficient flash space: need %u, have %u",
                  size, flash_inactive_bank_size());
        s_ota.state = OTA_STATE_ERROR;
        return s_ota.state;
    }
    
    s_ota.state = OTA_STATE_NOTIFIED;
    return s_ota.state;
}

int ota_download_firmware(void) {
    uint8_t  chunk[4096];
    uint32_t offset = s_ota.downloaded_bytes;  /* Resume from where we left off */
    int      rc;
    
    s_ota.state = OTA_STATE_DOWNLOADING;
    
    while (offset < s_ota.firmware_size) {
        uint32_t end = offset + sizeof(chunk) - 1U;
        if (end >= s_ota.firmware_size) end = s_ota.firmware_size - 1U;
        
        /* HTTP Range request: GET with Range: bytes=offset-end */
        rc = http_get_range(s_ota.package_url, offset, end, chunk);
        if (rc < 0) {
            if (++s_ota.retry_count >= 3U) {
                log_error("[OTA] Download failed after 3 retries at offset %u", offset);
                s_ota.state = OTA_STATE_ERROR;
                return -1;
            }
            /* Exponential backoff: 1s, 2s, 4s */
            ota_sleep_ms(1000U << (s_ota.retry_count - 1U));
            continue;  /* Retry same offset */
        }
        
        /* Write chunk to inactive flash bank */
        rc = flash_write_inactive(offset, chunk, (uint32_t)rc);
        if (rc != 0) {
            log_error("[OTA] Flash write failed at offset %u", offset);
            s_ota.state = OTA_STATE_ERROR;
            return -2;
        }
        
        offset += (uint32_t)rc;
        s_ota.downloaded_bytes = offset;  /* Persist for resume */
        nvm_save_ota_progress(&s_ota);    /* Write to NvM for power-loss resume */
        
        /* Report progress */
        uint8_t pct = (uint8_t)((offset * 100U) / s_ota.firmware_size);
        mqtt_publish_progress(pct);
    }
    
    s_ota.state = OTA_STATE_VERIFYING;
    return 0;
}

int ota_verify_firmware(void) {
    uint8_t computed_hash[32];
    
    /* Step 1: SHA-256 hash of downloaded firmware */
    sha256_compute_from_flash(FLASH_INACTIVE_BANK_ADDR, s_ota.firmware_size,
                              computed_hash);
    
    if (memcmp(computed_hash, s_ota.expected_sha256, 32U) != 0) {
        log_error("[OTA] SHA-256 mismatch — firmware corrupted");
        s_ota.state = OTA_STATE_ERROR;
        return -1;
    }
    
    /* Step 2: ECDSA-256 signature verification */
    /* Public key stored in ROM (burned during manufacturing) */
    int sig_rc = ecdsa_verify_p256(computed_hash, s_ota.expected_sig,
                                   ota_public_key_rom());
    if (sig_rc != 0) {
        log_error("[OTA] ECDSA signature invalid — reject firmware");
        s_ota.state = OTA_STATE_ERROR;
        return -2;
    }
    
    log_info("[OTA] Firmware verified: SHA-256 OK, ECDSA OK");
    s_ota.state = OTA_STATE_PENDING_REBOOT;
    return 0;
}

/* Called when conditions are safe to reboot (vehicle stopped, ignition cycle) */
int ota_trigger_swap_and_reboot(void) {
    /* Write swap request to NvM — bootloader reads this on next boot */
    nvm_write_bank_swap_request(BANK_B);  /* Activate inactive bank */
    
    /* Record that we're in OTA post-reboot validation phase */
    nvm_write_ota_validation_pending(true);
    nvm_write_ota_fallback_timer(OTA_VALIDATION_TIMEOUT_SEC);
    
    s_ota.state = OTA_STATE_REBOOTING;
    log_info("[OTA] Requesting reboot and bank swap to v%s", s_ota.version);
    
    /* Issue ECU reset via WDG timeout or NvM+reset */
    system_request_reset(RESET_OTA_SWAP);
    
    return 0;  /* Won't return */
}

/* Called on first boot after OTA (bootloader has swapped banks) */
void ota_post_reboot_validation(void) {
    if (!nvm_read_ota_validation_pending()) {
        return;  /* Not in OTA validation phase */
    }
    
    s_ota.state = OTA_STATE_VALIDATING;
    
    /* Self-test: verify basic functionality */
    int self_test_ok = run_boot_self_test();  /* CAN, sensors, basic logic */
    
    if (self_test_ok) {
        /* Commit: mark this bank as permanent active */
        nvm_write_bank_swap_request(BANK_NONE);   /* No more swap needed */
        nvm_write_ota_validation_pending(false);
        s_ota.state = OTA_STATE_COMMITTED;
        
        /* Report success to cloud */
        mqtt_publish_ota_result("SUCCESS", s_ota.version);
        log_info("[OTA] v%s committed — OTA complete", s_ota.version);
    } else {
        /* Rollback: reboot back to previous bank */
        log_error("[OTA] Self-test failed — rolling back from v%s", s_ota.version);
        s_ota.state = OTA_STATE_ROLLING_BACK;
        s_ota.rollback_attempts++;
        
        nvm_write_bank_swap_request(BANK_A);  /* Swap back to old bank */
        mqtt_publish_ota_result("ROLLBACK", s_ota.version);
        system_request_reset(RESET_OTA_ROLLBACK);
    }
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q3. 0.5% of a 100,000 vehicle fleet fails OTA. Cloud team reports download timeout. How do you debug?

**Expert Answer:**

```
Fleet scale failure (500 vehicles): likely not a single root cause

STEP 1 — Segment the failures:
  Query fleet telemetry for failing vehicles:
    - LTE signal strength at time of attempt
    - Battery voltage during OTA
    - Firmware version being updated from
    - Geographic region
    - Time of day
    - Failure point: IDLE/DOWNLOAD/VERIFY/FLASH/REBOOT

  Common patterns found:
  A) 400/500 failures: RSSI < -110 dBm (poor LTE coverage, rural areas)
  B) 60/500 failures: battery < 12.0V at download start
  C) 40/500 failures: interrupted at 95% → specific CDN node issue

STEP 2 — Root cause for each cluster:

Cluster A — Poor LTE signal:
  HTTP download timeout at 30 seconds
  Fix: Increase timeout to 120s for low-RSSI (< -105 dBm)
  Fix: Reduce chunk size from 128KB to 16KB on low bandwidth
  Fix: Add CDN edge location to reduce round-trip latency

Cluster B — Low battery:
  ECU entered power-saving mode during download, TCP connection dropped
  Fix: Add battery voltage check before starting OTA (>12.0V required)
  Fix: Request user to charge if battery low (notification in instrument cluster)

Cluster C — CDN failure:
  CDN node returned partial 206 Partial Content with wrong content length
  Fix: Validate Content-Length header vs actual bytes received per chunk
  Fix: Add MD5/CRC per chunk in HTTP header (X-Chunk-Hash) for integrity
  
STEP 3 — Resume capability verification:
  Verify NvM save works correctly on power loss during download
  Test: Start download, pull ignition at 50% → re-ignite → should resume at 50%
  
STEP 4 — Staged rollout adjustment:
  Before: All 100,000 vehicles simultaneously
  After:  1% → 5% → 20% → 100% with health gate at each stage
  Gate: <0.1% failure rate to proceed to next stage
  Rollback: if failure > 1% at any stage, halt campaign

Production Insight (Harman, BMW ConnectedDrive):
  OTA download resume added a 4-byte NvM write on every 4KB chunk.
  NvM write frequency: too high → NvM wearing out.
  Fix: Write progress to NvM every 512KB, not every 4KB.
  Add SHA-256 per-chunk to resume correctly even if last chunk was partial.
```

---

## CHEAT SHEET — OTA Updates

```
OTA state machine:
  IDLE → NOTIFIED → DOWNLOADING → VERIFYING → FLASHING →
  VERIFYING_FW → PENDING_REBOOT → REBOOTING →
  VALIDATING → COMMITTED (success)
            └→ ROLLING_BACK (failure)

Security chain (defence in depth):
  Transport: TLS 1.3 (mTLS — both sides authenticate)
  Package:   ECDSA-256 signature on SHA-256 hash of firmware
  Storage:   Encrypted storage (AES-128 on flash inactive bank)
  Boot:      Secure Boot (ROM verifies bootloader signature)
  
Download resilience:
  HTTP Range requests (bytes=offset-end) for chunk downloads
  Progress saved to NvM every 512KB (not every chunk — NvM wear)
  3x retry with exponential backoff: 1s, 2s, 4s
  Resume on power cycle: read NvM offset, continue from there

Rollback mechanism:
  Dual-bank: write new FW to inactive, atomically swap on boot
  Self-test window: X seconds to validate new FW after boot
  If self-test fails → NvM swap request → reboot to old bank
  Fallback: watchdog timer — if new FW crashes before self-test → hardware reset → old bank

Fleet failure analysis:
  1. Segment by failure point (download/verify/flash/boot)
  2. Correlate with: LTE signal, battery voltage, FW version
  3. CDN health: check CDN logs for partial responses
  4. Implement staged rollout to limit blast radius

Common OTA failure causes:
  Power loss during download → resume needed
  LTE dropout → timeout too short, retry too few
  Battery sag → power check before starting
  Storage full → check available space before download
  Wrong signature → build system sign error (check CI pipeline)
  Hash mismatch → CDN or storage corruption
  Boot self-test fail → new FW bug → rollback
```
