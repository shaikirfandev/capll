# Module 08 — OTA & Connected Vehicle Security

> Level: Advanced | Est. study time: 8 hours | Aligned: UNECE R156

---

## 8.1 OTA Architecture

```
OTA SYSTEM ARCHITECTURE:

Cloud Backend                  Vehicle
─────────────────              ────────────────────────────────
  ┌──────────────┐             ┌──────────────────────────────┐
  │ OTA Backend  │             │ Telematics Control Unit (TCU)│
  │ Campaign Mgr │  TLS 1.3    │                              │
  │ Package Sign │◄───────────►│ MQTT/HTTPS client            │
  │ Distribution │  mTLS       │ Campaign receiver            │
  │ CDN          │             │ Download manager             │
  └──────┬───────┘             │ Package verifier             │
         │                     └──────────────┬───────────────┘
  ┌──────▼───────┐                            │  Automotive Ethernet
  │ PKI          │                     ┌──────▼───────────────┐
  │ Root CA      │                     │ Central Gateway ECU  │
  │ Code Signing │                     │ OTA routing          │
  │ Cert Issuing │                     │ Validates package    │
  └──────────────┘                     │ Distributes to ECUs  │
                                       └──────┬───┬───┬───────┘
                                              │   │   │
                                        ECU_1 ECU_2 ECU_3
                                              (CAN/Eth)
```

---

## 8.2 Secure OTA Update Workflow

```
SECURE OTA SEQUENCE DIAGRAM:

OTA Backend    CDN        TCU          Gateway       Target ECU
    │           │          │               │              │
    │─Campaign─►│          │               │              │
    │           │          │               │              │
    │           │──Notify──►               │              │
    │           │       (MQTT push)        │              │
    │           │          │               │              │
    │           │◄─Download─│               │              │
    │           │  Request  │               │              │
    │           │           │               │              │
    │           │─Signed────►               │              │
    │           │ Package   │               │              │
    │           │           │               │              │
    │           │        [Verify]           │              │
    │           │       TLS cert            │              │
    │           │       Pkg signature       │              │
    │           │       Version > min       │              │
    │           │       Hash integrity      │              │
    │           │          │               │              │
    │           │          │──Route pkg────►              │
    │           │          │   (Ethernet)  │              │
    │           │          │               │              │
    │           │          │               │─UDS 0x34 ───►│
    │           │          │               │  download    │
    │           │          │               │─UDS 0x36 ───►│ (blocks)
    │           │          │               │─UDS 0x37 ───►│
    │           │          │               │─UDS 0x31 ───►│ verify sig
    │           │          │               │◄ 0x71 OK ────│
    │           │          │               │─UDS 0x11 ───►│ reset
    │           │          │               │              │
    │           │          │               │           [Secure Boot]
    │           │          │               │           validates
    │           │          │               │           new firmware
```

---

## 8.3 OTA Package Structure

```
OTA Package (signed, encrypted):

┌───────────────────────────────────────────────────────────┐
│  Package Manifest (JSON, signed with OEM ECDSA key)       │
│  {                                                        │
│    "target_ecu": "ADAS_ECU_v2",                          │
│    "hw_compatibility": ["HW_REV_A", "HW_REV_B"],         │
│    "sw_version": "2.5.1",                                │
│    "min_allowed_version": "2.3.0",   ← anti-rollback     │
│    "sha256": "a1b2c3d4e5f6...",      ← firmware hash     │
│    "signature": "3045022100...",     ← ECDSA P-256        │
│    "encryption": "AES-256-GCM",                          │
│    "key_id": "OTA_KEY_20241001"                          │
│  }                                                        │
├───────────────────────────────────────────────────────────┤
│  Encrypted Firmware Payload                               │
│  (AES-256-GCM, key in HSM at vehicle side)               │
│  IV: random 96-bit                                        │
│  Auth tag: 128-bit (GCM integrity)                        │
└───────────────────────────────────────────────────────────┘
```

---

## 8.4 OTA Attack Vectors

### Attack 1: Rollback Attack

```
Vulnerability: OTA system accepts older firmware version
Attack:
  1. Attacker obtains older firmware (e.g., from leak or old vehicle)
  2. Packages with valid (but old) signature
  3. Vehicle accepts and installs older firmware
  4. Old firmware has known vulnerability → attacker exploits

Mitigation:
  - Monotonic counter in HSM/OTP (increments on every flash)
  - Manifest field: "min_allowed_version" enforced at ECU level
  - Counter stored in tamper-proof OTP — cannot be decremented
```

### Attack 2: Malicious Package Injection (MITM on OTA channel)

```
Vulnerability: OTA download over HTTP (no TLS) or TLS without cert pinning

Attack:
  1. Attacker on same 4G/WiFi network (or rogue AP)
  2. Intercepts OTA download traffic (MITM)
  3. Replaces legitimate firmware with malicious binary
  4. Vehicle installs attacker's firmware

Mitigation:
  - TLS 1.3 with mutual authentication (vehicle cert + backend cert)
  - Certificate pinning: vehicle only trusts OEM root CA certificate
  - Code signing: firmware ECDSA signature checked by ECU BEFORE install
  - Hash validation: SHA-256 of firmware matches manifest

Python: Verify OTA signature before trusting:
  from cryptography.hazmat.primitives.asymmetric import ec
  from cryptography.hazmat.primitives import hashes
  
  def verify_ota_signature(firmware: bytes, signature: bytes, 
                           public_key: ec.EllipticCurvePublicKey) -> bool:
      try:
          public_key.verify(signature, firmware, 
                           ec.ECDSA(hashes.SHA256()))
          return True
      except Exception:
          return False  # Invalid signature — reject firmware
```

### Attack 3: OTA Backend Compromise

```
Attack Surface: The OTA backend server
  - Compromise code signing key → forge valid firmware packages
  - Compromise campaign manager → push malicious packages to entire fleet
  - Compromise CDN → serve malicious firmware to all downloading vehicles
  
This is the most impactful attack: one compromise → millions of vehicles

Mitigations:
  OEM-level:
  - Code signing key in offline air-gapped HSM (never connected to backend)
  - Signing ceremony requires multiple authorized engineers (M-of-N)
  - All signing operations logged + timestamped
  - Firmware packages signed BEFORE uploading to CDN
  - CDN cannot modify packages (signature would break)
  
  Cloud security:
  - Backend API: OAuth 2.0 with short-lived tokens (15min expiry)
  - Campaign creation requires 2FA + role-based access
  - Immutable audit log for all signing operations
  - Anomaly detection: alert if >N packages signed per hour
```

### Attack 4: Interrupted OTA (Persistence Attack)

```
Attack: Intentionally interrupt OTA mid-flash to leave ECU in corrupt state
  - Power cut during flash → ECU in unprogrammed / half-flashed state
  - Some ECUs boot with default config after corruption
  - Default config may have debug interfaces enabled

Mitigation:
  - A/B partition scheme: 
    Slot A: Current firmware (running)
    Slot B: New firmware being written
    → If flash interrupted, Slot A still valid → automatic fallback
    → Only switch active slot AFTER successful Secure Boot validation of Slot B
```

---

## 8.5 TLS in Automotive

```
TLS 1.3 is mandatory for:
  - OTA download (vehicle ↔ CDN)
  - Vehicle ↔ cloud telemetry (TCU → MQTT broker)
  - DoIP over Ethernet (tester ↔ vehicle)
  - V2X PKI enrollment

TLS 1.3 Improvements over TLS 1.2:
  - 1-RTT handshake (vs 2-RTT in TLS 1.2) → faster
  - 0-RTT resumption for known connections
  - Forward Secrecy mandatory (ECDHE key exchange)
  - All cipher suites with AEAD (no CBC, RC4, etc.)
  - Removed: RSA static key exchange, SHA-1, MD5

Automotive TLS Configuration:
  Cipher suites (allowed):
    TLS_AES_256_GCM_SHA384
    TLS_AES_128_GCM_SHA256
    TLS_CHACHA20_POLY1305_SHA256
  
  Certificate requirements:
    - ECDSA P-256 or P-384 (RSA-2048 minimum if ECDSA unavailable)
    - Certificate lifetime: 3 years max
    - CN = VIN (vehicle identity)
    - Extended Key Usage: clientAuth (for vehicle → server mutual auth)
    
  Certificate pinning:
    - Vehicle firmware contains hash of OEM root CA certificate
    - TLS handshake: verify server cert chain against pinned root CA
    - Reject connection if chain doesn't trace back to pinned root
```

---

## 8.6 Vehicle API & Mobile App Security

```
Connected Vehicle APIs (REST/HTTPS):
  - Remote start/stop
  - Climate preconditioning
  - Door lock/unlock
  - Locate vehicle
  - Trip history
  - OTA trigger

Common Attack Vectors:
┌──────────────────────────────────────────────────────────────────┐
│ 1. Broken Object Level Authorization (OWASP API #1)              │
│    GET /vehicles/VIN1234567/location                             │
│    → Change VIN to another vehicle → get their location too!    │
│    → Victim VIN is the car plate / easily guessable             │
│                                                                  │
│ 2. Broken Authentication (OWASP API #2)                         │
│    JWT without expiry → stolen token valid forever              │
│    Weak password policy → brute-forceable (no lockout)          │
│                                                                  │
│ 3. Excessive Data Exposure                                       │
│    GET /user/profile returns VIN + home/work addresses + trip   │
│    history → stalking, burglary planning                         │
│                                                                  │
│ 4. Mass Assignment                                               │
│    POST /vehicles/update with {"admin": true} → privilege esc.  │
│                                                                  │
│ 5. Token Theft from Mobile App                                   │
│    OAuth token stored in plaintext in SharedPreferences (Android)│
│    → Backup apps read it → replay to steal vehicle               │
└──────────────────────────────────────────────────────────────────┘

Secure API Implementation:
  - Authorization: JWT with VIN claim, verified server-side
  - Short token lifetime: 15-minute access token
  - Refresh token rotation: old refresh token invalidated on use
  - Rate limiting: max 10 remote commands per minute per vehicle
  - Command signing: critical commands (unlock, start) require 
    additional HMAC signature with per-vehicle shared secret
  - Audit log: every API call logged with timestamp, IP, user agent
```

---

## 8.7 Cloud-Connected Vehicle Security Architecture

```
SECURE ARCHITECTURE:

  Vehicle                 Cloud Backend               External
  ──────────────────      ──────────────────────      ──────────────
  TCU                     API Gateway                 OEM Mobile App
  ├─ TLS 1.3 mTLS ───────►├─ WAF (OWASP rules)       ├─ OAuth 2.0
  ├─ Certificate (VIN)    ├─ DDoS protection          ├─ Cert pinning
  ├─ JWT with VIN claim   ├─ Rate limiting            └─ Biometric auth
  └─ MQTT 5.0 TLS         ├─ RBAC authorization
                          │                           Third-party
                          ├─ Vehicle Service          ├─ OAuth scoped
                          │  (microservices)          │  access only
                          ├─ HSM (signing keys)       └─ No VIN access
                          ├─ SIEM (monitoring)
                          ├─ IDS/IPS
                          └─ Immutable audit logs
```

---

## 8.8 UNECE R156 OTA Compliance

UNECE R156 mandates a **Software Update Management System (SUMS)**:

| Requirement | What it means | Implementation |
|------------|---------------|---------------|
| Software ID | Each software component has unique ID | SBOM with hashes |
| Compatibility check | OTA checks HW/SW compatibility | Manifest validation |
| Driver notification | Driver informed before update | HMI notification flow |
| Consent | Driver can defer/accept (non-safety) | Campaign management |
| Integrity | Update packages verified | ECDSA signature + hash |
| Rollback | Can revert if update fails | A/B partition + monotonic counter |
| Audit | All updates logged | Immutable update history |

---

## 8.9 Summary — Module 08

```
KEY TAKEAWAYS:

✓ OTA backend is most impactful attack target — compromising it risks entire fleet
✓ Code signing key must NEVER be online — offline HSM + key ceremony
✓ TLS 1.3 mutual auth is mandatory for all vehicle ↔ cloud communication
✓ Certificate pinning prevents MITM even with rogue CA
✓ Anti-rollback requires OTP monotonic counter — not just manifest field
✓ A/B partition scheme prevents bricking from interrupted OTA
✓ Vehicle API authorization must check VIN ownership — OWASP API #1 is common
✓ UNECE R156 mandates SUMS — OTA update system must be type-approved
✓ Mobile apps: OAuth tokens must not be stored in plaintext storage
```

**Next Module**: [09 — EV & Charging Security](09_ev_charging_security.md)
