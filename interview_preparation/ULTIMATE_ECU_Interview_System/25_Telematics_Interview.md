# Telematics Interview Questions
## Senior Automotive Embedded Engineer — TCU / Telematics Specialist

---

## TOPIC OVERVIEW

Telematics is the fusion of **telecommunications, vehicle data, and embedded software**. TCU (Telematics Control Unit) roles are highly sought at Harman, Continental Telematics, Aptiv, Visteon, Qualcomm Automotive, and OEM R&D centres. This is YOUR strongest topic area — answer with production-level depth.

**Key areas probed:**
- TCU hardware architecture and cellular modem integration
- MQTT, AMQP, HTTPS — cloud protocol selection for vehicle telematics
- Vehicle data collection (CAN signals → cloud)
- OTA (Over-The-Air) update orchestration
- eCall (TS 26.267), V2X (DSRC, C-V2X)
- GPS/GNSS integration and positioning
- Telematics Security (mTLS, certificate management)
- Power management (always-on telematics vs ignition-on)
- 4G LTE / 5G NR modem integration (AT commands, QMI, MBIM)

---

## BEGINNER QUESTIONS

---

### Q1. What is a Telematics Control Unit (TCU) and what are its core functions?

**Short Answer:** A TCU is an automotive ECU that provides cellular connectivity, GPS positioning, and vehicle data gateway services — enabling remote diagnostics, fleet management, eCall emergency services, and OTA updates.

**Detailed Expert Answer:**

```
┌──────────────────────────────────────────────────────────┐
│                  TCU Architecture                        │
│                                                          │
│  ┌──────────────┐    ┌────────────────────────────────┐  │
│  │  CAN/CAN-FD  │───▶│           MCU                  │  │
│  │  Interface   │    │  Application Processor          │  │
│  │  (SocketCAN) │    │  (ARM Cortex-A or A+M split)   │  │
│  └──────────────┘    │                                 │  │
│                      │  ┌────────────┐ ┌────────────┐  │  │
│  ┌──────────────┐    │  │  MQTT/TLS  │ │  OTA Agent │  │  │
│  │  GPS/GNSS    │───▶│  │  Client    │ │            │  │  │
│  │  (u-blox     │    │  └─────┬──────┘ └─────┬──────┘  │  │
│  │  Neo-M8N)    │    │        └─────────┬─────┘         │  │
│  └──────────────┘    │           ┌──────▼──────┐        │  │
│                      │           │  LTE Modem  │        │  │
│  ┌──────────────┐    │           │  Interface  │        │  │
│  │  SIM/eSIM    │───▶│           │  (AT cmd /  │        │  │
│  │  (UICC)      │    │           │   QMI/MBIM) │        │  │
│  └──────────────┘    └────────────────────────────────┘  │
│                                    │                      │
│  ┌──────────────┐                  │                      │
│  │  LTE Modem   │◀─────────────────┘                      │
│  │  (Quectel    │                                          │
│  │  EC25 /      │                                          │
│  │  Sierra MC7)  │─────────────────────────▶ Cloud Backend │
│  └──────────────┘                                          │
└──────────────────────────────────────────────────────────┘
```

**TCU core functions:**

| Function | Description | Standard/Protocol |
|----------|-------------|------------------|
| eCall | Emergency crash notification | ETSI TS 102 508, 3GPP TS 26.267 |
| Vehicle Tracking | GPS position every N seconds | NMEA 0183, GNSS |
| Remote Diagnostics | Read DTCs, live data over cellular | OBD-II, UDS over IP |
| OTA Update | Firmware/software update over cellular | HTTPS, MQTT, delta compression |
| V2I/V2X | Vehicle-to-infrastructure messaging | DSRC 802.11p, C-V2X PC5 |
| Fleet Management | Driver behaviour, fuel efficiency | MQTT to TSP backend |
| Stolen Vehicle Tracking | Low-power periodic ping | GPRS/LTE-M |

---

### Q2. Explain MQTT and why it's preferred for vehicle telematics over HTTP REST.

**Short Answer:** MQTT is a lightweight publish-subscribe protocol designed for constrained environments. It uses 2-byte fixed headers (vs HTTP's hundreds of bytes), maintains persistent connections, and supports three QoS levels — making it ideal for intermittent cellular connectivity in vehicles.

**Detailed Expert Answer:**

**MQTT Frame overhead comparison:**
```
HTTP REST publish (POST /telemetry):
  HTTP header: ~500 bytes (Content-Type, Authorization, Host, etc.)
  Body: 100 bytes (JSON payload)
  Total: ~600 bytes per message
  Round-trip: request → TCP ACK → HTTP response → TCP ACK = 4 messages

MQTT publish:
  Fixed header: 2 bytes
  Topic: ~30 bytes ("/vehicle/VIN123456/telemetry")
  Payload: 100 bytes (binary or JSON)
  Total: ~132 bytes per message
  No response needed for QoS 0

→ MQTT is ~4.5× smaller per message
→ Critical on LTE-M/NB-IoT where data is expensive and latency is high
```

**MQTT QoS levels in automotive context:**
```c
/* QoS 0 — Fire and forget (GPS position, no acknowledgement) */
mqtt_publish(client, "/vehicle/VIN/gps", payload, QOS_0);
/* Use for: frequent, loss-tolerant: GPS every second, CAN signals */

/* QoS 1 — At least once (with PUBACK, may duplicate) */
mqtt_publish(client, "/vehicle/VIN/dtc", payload, QOS_1);
/* Use for: DTC events — better to send twice than miss once */

/* QoS 2 — Exactly once (PUBREC + PUBREL + PUBCOMP, 4-message handshake) */
mqtt_publish(client, "/vehicle/VIN/ota_confirm", payload, QOS_2);
/* Use for: OTA completion confirmation, payment events */
```

**MQTT Last Will for vehicle disconnect detection:**
```c
/* Set up Last Will before connecting — sent if TCU disconnects abnormally */
mqtt_connect_options opts = {
    .client_id  = "TCU_VIN_WBAJB9C58BC123456",
    .will_topic = "/vehicle/VIN123456/status",
    .will_payload = "{\"online\":false,\"reason\":\"unexpected_disconnect\"}",
    .will_qos   = MQTT_QOS_1,
    .will_retain = 1,
    .keepalive_sec = 60,  /* Server expects PING every 60 sec */
};
```

**When to use alternatives:**
```
HTTPS/REST: When security infrastructure requires stateless API calls,
            when integrating with existing web microservices,
            for large OTA package downloads (HTTP Range requests, resume support)

AMQP:       Enterprise telematics backends (Harman, Volkswagen Group cloud)
            when message routing, queues, and dead-letter handling needed

gRPC:       High-throughput vehicle-to-cloud streaming (ADAS data, V2X)
            when strongly-typed schemas are important
```

---

### Q3. How does a TCU handle OTA firmware updates? Walk through the complete flow.

**Short Answer:** TCU OTA involves: notification → package download → signature verification → staging → controlled flashing → rollback on failure — with network retry logic and watchdog protection throughout.

**Detailed Expert Answer:**

```
OTA Update State Machine:
                                                    
 [IDLE] → notification received                    
    ↓                                               
 [DOWNLOADING]                                      
    ├── MQTT: meta-message with package URL + size + SHA256
    ├── HTTPS GET with Range headers (resume support)
    ├── Streaming to staging partition (not active!)
    ├── Progress updates via MQTT every 1%           
    └── Retry on connection loss (exponential backoff)
    ↓                                               
 [VERIFYING]                                        
    ├── SHA-256 hash of downloaded file
    ├── RSA/ECDSA signature check (OEM public key)
    ├── Version compatibility check (target > current)
    └── Available space check before staging         
    ↓                                               
 [STAGING]                                          
    ├── Unpack delta/full firmware to staging area
    ├── Calculate destination CRC (pre-flash check)
    └── Set update flag in NvM                      
    ↓                                               
 [FLASHING] ← only enter if VERIFYING passed        
    ├── Disable all non-critical processes          
    ├── Write firmware to inactive partition         
    ├── Service watchdog every block                
    └── CRC verify written flash vs expected        
    ↓                                               
 [CONFIRMING]                                       
    ├── MCU reboot                                  
    ├── Bootloader verifies CRC of new firmware     
    ├── If OK: set boot vector to new firmware      
    └── If FAIL: boot original firmware (rollback)  
    ↓                                               
 [REPORTING]                                        
    └── MQTT publish result: success/fail/rollback  
```

**Production implementation considerations:**
```c
/* TCU OTA download with resume capability */
int ota_download(const char *url, const char *dest_path,
                 const uint8_t *expected_sha256) {
    /* Check if partial download exists */
    size_t resume_offset = ota_get_partial_size(dest_path);
    
    HttpRequest req = {
        .url     = url,
        .method  = HTTP_GET,
        .headers = {
            /* Range header enables HTTP resume */
            { "Range", "bytes=%zu-", resume_offset },
            { "Authorization", "Bearer %s", ota_get_token() },
        }
    };
    
    /* Stream to staging — never write to active partition during download */
    FILE *f = fopen(dest_path, resume_offset ? "ab" : "wb");
    
    /* Download in 4KB blocks with progress and watchdog service */
    uint8_t block[4096];
    size_t total = 0;
    while (http_read_block(&req, block, sizeof(block), &n) > 0) {
        fwrite(block, 1, n, f);
        total += n;
        Wdg_Trigger();  /* Keep watchdog alive during long download */
        
        if (total % (1024*1024) == 0) {
            /* Report progress every 1 MB */
            ota_report_progress(total, expected_total);
        }
    }
    fclose(f);
    
    /* Verify integrity */
    return sha256_verify_file(dest_path, expected_sha256);
}
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. Explain eCall — how does the TCU detect a crash and make the emergency call?

**Short Answer:** eCall (ETSI EN 15722) is a mandatory EU emergency call system. On crash detection (air bag deployment signal or g-sensor threshold), the TCU initiates an automatic cellular voice call to the PSAP (Public Safety Answering Point) and transmits MSD (Minimum Set of Data) via in-band modem.

**Detailed Expert Answer:**

**eCall trigger chain:**
```c
/* eCall can be triggered two ways */

/* 1. Automatic — crash signal from airbag ECU via CAN */
void CAN_RxCallback(uint32_t can_id, const uint8_t *data) {
    if (can_id == AIRBAG_STATUS_ID) {
        uint8_t airbag_deployed = (data[0] >> 4) & 0x0F;
        if (airbag_deployed && !g_ecall_active) {
            ECall_TriggerAutomatic();
        }
    }
}

/* 2. Manual — SOS button press in vehicle */
void SOS_Button_ISR(void) {
    ECall_TriggerManual();
}
```

**MSD (Minimum Set of Data) — what's sent to rescue services:**
```c
/* MSD structure (simplified from ETSI EN 15722) */
typedef struct {
    uint8_t  msd_version;           /* 1 = EN 15722:2015 */
    uint8_t  message_identifier;    /* Increments each transmission */
    struct {
        uint8_t test_call     :1;   /* 0 = real emergency */
        uint8_t auto_activated:1;   /* 1 = automatic, 0 = manual */
        uint8_t pos_can_be_trusted:1;
        uint8_t vehicle_type  :4;   /* Passenger car, HGV, etc. */
    } control;
    uint8_t  vehicle_id[17];        /* VIN */
    uint8_t  timestamp[4];          /* Unix timestamp of crash */
    int32_t  latitude;              /* × 10^-7 degrees */
    int32_t  longitude;             /* × 10^-7 degrees */
    uint8_t  direction;             /* 0-255 = 0-358 degrees */
    uint8_t  recent_vehicle_loc[3][6]; /* Last 3 GPS positions */
    uint8_t  num_passengers;        /* Estimated (from seat sensors) */
} MSD_t;
```

**eCall in-band modem transmission:**
```
eCall uses a special in-band modem to transmit MSD data over the voice call:
- Voice carrier: standard 3GPP voice call to 112 (EU) or 911 (US)
- MSD transmitted as audio-frequency modem signal (HLAP modem, 1200 bps)
- Transmitted 3 times automatically for reliability
- After MSD: call stays open for voice communication with PSAP operator
```

**Regulatory requirements:**
- EU: Mandatory for all new passenger cars since 2018 (eCall Regulation EU 2015/758)
- Russia: ERA-GLONASS (similar system using GLONASS instead of GPS)
- Brazil: CONTRAN (similar mandate)

---

### Q5. How does the TCU maintain connectivity with low power in parking/sleep mode?

**Short Answer:** The TCU uses a combination of wake-up sources (CAN wake, timer, cellular page, geo-fence) and power states (full-on, low-power, standby) to balance always-on connectivity with battery drain constraints.

**Detailed Expert Answer:**

```
TCU Power State Machine:
                                                    
 [FULL_ON] (ignition=ON)                           
    ├── All functions active (GPS, LTE, CAN active)
    ├── MQTT keepalive every 60 sec                
    ├── GPS update every 1 sec                     
    └── CAN monitoring active                      
           │                                        
           ▼ ignition off                          
 [TRANSITION_OFF]                                  
    ├── Send "ignition_off" event to cloud         
    ├── Stop non-essential CAN signal processing  
    └── Configure wake-up sources                 
           │                                        
           ▼ transition complete (15 sec)           
 [SLEEP_MODE] (ignition=OFF)                       
    ├── MCU in low-power mode (STM32 STOP mode)   
    ├── LTE modem: PSM (Power Saving Mode)        
    │     - Modem off, TAU timer for re-registration
    │     - Active Time Window: 2 min every 30 min
    ├── GPS: off (or periodic 5-min check)        
    └── Wake-up sources:                          
          ├── CAN wake-up frame (remote start)    
          ├── Timer (periodic ping, 30 min)       
          ├── eCall trigger (always on!)          
          └── Cellular page (remote command)      
           │                                        
           ▼ wake event received                    
 [WAKEUP]                                          
    ├── MCU exits STOP mode                       
    ├── LTE re-registers (if PSM timer expired)   
    ├── Performs function (position report, etc.) 
    └── Returns to SLEEP or FULL_ON               
```

**3GPP PSM (Power Saving Mode) for LTE-M/NB-IoT:**
```c
/* Configure LTE modem PSM via AT commands */
void tcm_configure_psm(void) {
    /* T3412 = periodic TAU timer (how often modem re-registers): 30 min */
    /* T3324 = active timer (how long modem stays awake after TAU): 2 min */
    uart_send("AT+CPSMS=1,,,\"01000011\",\"00100010\"\r\n");
    /*                              ↑T3412    ↑T3324
       "01000011" = 30 minutes TAU
       "00100010" = 2 minutes active time */
    
    /* With PSM: average current during sleep = ~10 μA (vs 100+ mA active) */
    /* Battery life improvement: 3-6 months on backup battery */
}
```

---

## ADVANCED QUESTIONS

---

### Q6. Explain mTLS (mutual TLS) for TCU-to-cloud communication. How are certificates managed at scale?

**Short Answer:** mTLS requires both client (TCU) and server (cloud) to present certificates. Each TCU has a unique X.509 certificate provisioned at manufacturing, stored in the HSM or secure flash. The cloud validates TCU identity; the TCU validates server authenticity.

**Detailed Expert Answer:**

```
mTLS Handshake (TCU ↔ Cloud Backend):
                                                    
  TCU                                    Cloud      
   │                                       │        
   │──── ClientHello ──────────────────────▶│        
   │     (TLS 1.3, cipher suites)          │        
   │                                       │        
   │◀─── ServerHello ──────────────────────│        
   │◀─── Certificate (server cert) ────────│        
   │◀─── CertificateRequest ───────────────│        
   │◀─── ServerHelloDone ──────────────────│        
   │                                       │        
   │ [TCU verifies server cert against     │        
   │  OEM CA certificate in TCU flash]     │        
   │                                       │        
   │──── Certificate (TCU cert) ───────────▶│        
   │     VIN: WBA1234567890ABCDE           │        
   │     Issued by: OEM Manufacturing CA  │        
   │──── CertificateVerify ────────────────▶│        
   │──── ClientFinished ───────────────────▶│        
   │                                       │        
   │◀─── ServerFinished ───────────────────│        
   │                                       │        
   │ [mTLS established — encrypted tunnel] │        
```

**Certificate provisioning at manufacturing:**
```c
/* During ECU manufacturing (end-of-line programming) */
void eol_provision_certificates(const char *vin) {
    /* 1. Generate private key in HSM (never leaves hardware) */
    hsm_generate_key(KEY_ID_TCU_IDENTITY, KEY_TYPE_ECC_P256);
    
    /* 2. Generate Certificate Signing Request (CSR) */
    uint8_t csr[512];
    hsm_generate_csr(KEY_ID_TCU_IDENTITY, vin, csr, sizeof(csr));
    
    /* 3. Send CSR to OEM PKI server over secure manufacturing line */
    uint8_t certificate[1024];
    pki_sign_csr(csr, certificate);  /* OEM CA signs the CSR */
    
    /* 4. Store signed certificate in secure flash */
    secure_flash_write(CERT_SLOT_TCU_IDENTITY, certificate, sizeof(certificate));
    
    /* 5. Store OEM CA certificate for server validation */
    secure_flash_write(CERT_SLOT_OEM_CA, oem_ca_cert, sizeof(oem_ca_cert));
}
```

**Certificate rotation (for field updates):**
```c
/* Certificate lifecycle: typically 5 years, rotated via OTA */
void rotate_certificate(const uint8_t *new_cert, size_t len,
                        const uint8_t *signature) {
    /* Verify new cert is signed by OEM CA */
    if (!verify_cert_chain(new_cert, len, oem_ca_cert)) return;
    
    /* Verify the rotation command is authenticated */
    if (!hsm_verify_signature(new_cert, len, signature,
                              OEM_ROTATION_SIGNING_KEY)) return;
    
    /* Atomic write — don't break connectivity if power fails */
    secure_flash_write_atomic(CERT_SLOT_TCU_IDENTITY, new_cert, len);
}
```

**Production Insight (Continental TCU project):**
Each TCU in a fleet of 2 million vehicles has a unique certificate. The certificate store at the OEM PKI is 2 million entries. Certificate revocation is handled via OCSP (Online Certificate Status Protocol) — the TCU checks OCSP before each new TLS session to confirm the server certificate isn't revoked. CRL (Certificate Revocation List) is too large to download to a TCU with limited flash.

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q7. Your TCU's MQTT connection drops every 15 minutes in the field, but not in lab testing. How do you debug this?

**Expert Answer:**

"This is a classic field vs lab gap — almost certainly a cellular network issue, not a software bug.

**Step 1 — Gather network telemetry:**
```c
/* Add logging for MQTT disconnect reason codes */
void mqtt_disconnect_callback(int rc, const char *reason) {
    log_warn("MQTT disconnect: rc=%d reason=%s "
             "signal_strength=%d network=%s timestamp=%lu",
             rc, reason,
             cellular_get_rssi(),
             cellular_get_network_type(),
             Os_GetTime());
    
    /* Common MQTT rc codes:
       0  = Normal disconnect (keepalive timeout — server side!)
       1  = Connection refused (server issue)
       128 = Network error (cellular dropped)
    */
}
```

**Step 2 — Check MQTT keepalive vs cellular idle timeout:**
```
Lab: Connected to corporate WiFi/Ethernet → no idle timeout on router
Field: Cellular carrier's NAT/firewall closes idle connections after X minutes!

Most carriers:
  AT&T, Verizon: 5-15 minutes idle timeout on UDP/TCP
  T-Mobile: ~10 minutes
  Vodafone EU: ~15 minutes

Our keepalive: 60 seconds → should ping every 60 sec to keep connection alive
BUT: The keepalive MQTT PINGREQ/PINGRESP adds data usage — some corporate
     fleets restrict this

Fix 1: Reduce keepalive to 45 sec (below 1-minute carrier timeout)
Fix 2: Use MQTT over TLS on port 443 (less likely to be firewalled)
Fix 3: Use LTE-M with eDRX (extended DRX) instead of PSM for always-on
```

**Step 3 — Check for TCP keep-alive at socket level:**
```c
/* Set TCP-level keepalive to detect dead connections faster */
int enable_tcp_keepalive(int sockfd) {
    int enable = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_KEEPALIVE, &enable, sizeof(enable));
    
    int idle_sec = 30;    /* Start keepalive after 30 sec idle */
    int interval_sec = 5; /* Probe every 5 sec */
    int probes = 3;       /* Give up after 3 failed probes */
    
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPIDLE,   &idle_sec,    sizeof(idle_sec));
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPINTVL,  &interval_sec, sizeof(interval_sec));
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPCNT,    &probes,       sizeof(probes));
    return 0;
}
```

**Step 4 — Implement robust reconnection:**
```c
void mqtt_reconnect_with_backoff(void) {
    static uint32_t retry_delay_ms = 1000;
    
    while (!mqtt_connected()) {
        log_info("MQTT reconnect attempt, delay=%u ms", retry_delay_ms);
        
        if (mqtt_connect() == MQTT_SUCCESS) {
            retry_delay_ms = 1000;  /* Reset backoff on success */
            mqtt_resubscribe_all();  /* Re-subscribe to all topics */
            return;
        }
        
        /* Exponential backoff: 1s, 2s, 4s, 8s... up to 5 minutes */
        Os_Delay(retry_delay_ms);
        retry_delay_ms = (retry_delay_ms < 300000) ? retry_delay_ms * 2 : 300000;
    }
}
```

**Production Insight:** This exact bug affected 50,000 Harman TCUs in Germany. The Telekom DE network has a 14-minute NAT timeout. MQTT keepalive was set to 60 seconds which should have worked, but the TLS handshake overhead was causing the first PINGREQ to arrive at 61 seconds (just over 60 sec), triggering a server-side keepalive timeout. Fix: reduce keepalive to 45 seconds, add jitter (-5 to +5 seconds) to prevent fleet-wide simultaneous reconnect storms."

---

## CHEAT SHEET — Telematics

```
TCU core: MCU + LTE modem + GPS + SIM + CAN gateway + security
Modem control: AT commands (basic) or QMI/MBIM (Linux, high performance)

MQTT:
  QoS 0 = fire-and-forget (GPS, frequent non-critical data)
  QoS 1 = at-least-once (DTC events, important alerts)
  QoS 2 = exactly-once (OTA confirmations, billing events)
  Last Will = auto-publish on unexpected disconnect
  Keepalive: set lower than carrier NAT timeout (~45s for EU carriers)

OTA Flow:
  Notification → Download (HTTPS with Range/resume) → SHA256 verify
  → Signature check → Stage to inactive partition
  → Flash → CRC verify → Reboot → Confirm → Report

eCall:
  Trigger: airbag CAN signal or manual SOS button
  MSD: VIN + timestamp + GPS + direction + passenger count
  Transmission: in-band modem (HLAP) over voice call to PSAP
  EU mandatory since 2018

Power modes:
  Full-on (ignition): all functions, MQTT keepalive active
  Sleep (ignition-off): PSM mode on modem, MCU STOP, 10μA average
  Wake sources: CAN wake / periodic timer / eCall / cellular page

mTLS:
  TCU cert: unique per VIN, provisioned at EOL, stored in HSM
  OEM CA cert: stored in secure flash for server validation
  Rotation: OTA-delivered new cert, verified before replacing old
```
