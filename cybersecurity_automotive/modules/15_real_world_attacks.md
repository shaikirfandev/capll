# Module 15 — Real-World Attacks: Automotive Cybersecurity Case Studies

> Level: All Levels | Est. study time: 6 hours

---

## 15.1 Jeep Cherokee Remote Exploit (2015) — Miller & Valasek

```
THE MOST SIGNIFICANT AUTOMOTIVE CYBERSECURITY INCIDENT

RESEARCHERS: Charlie Miller & Chris Valasek
PUBLISHED:   Black Hat USA 2015 + WIRED article
IMPACT:      1.4 million vehicle recall (Fiat Chrysler)

ATTACK CHAIN:

  [1] SPRINT 4G NETWORK
      ↓ Attackers on Sprint network found Uconnect IPs via Sprint API
      ↓ Scanned cellular network for Chrysler Uconnect head units
      ↓ Found ~470,000 Uconnect units exposed on cellular network
      
  [2] UCONNECT HEAD UNIT (IVI) — INITIAL COMPROMISE
      ↓ Vulnerable D-Bus service exposed to cellular network
      ↓ QNX-based head unit had poor network isolation
      ↓ Exploit: heap overflow in web browser component
      ↓ Gained code execution on head unit
      
  [3] UCONNECT → V850 CHIP
      ↓ Head unit connected to V850 microcontroller (handles
        radio, HVAC, infotainment controls)
      ↓ Custom protocol from QNX to V850 over internal bus
      ↓ Flashed custom firmware to V850 via diagnostic interface
      
  [4] V850 → CAN BUS
      ↓ V850 chip has access to CAN bus
      ↓ Injected CAN messages to vehicle buses
      ↓ Achieved: AC control, radio, wipers, display
      
  [5] HIGH-SPEED CAN: BRAKES AND STEERING
      ↓ On highway: controlled brakes (SlowDown command)
      ↓ Deactivated transmission (PRND control)
      ↓ Limited to: slow-speed steering only (steering ECU rejected
        commands above ~5 mph for safety)

ROOT CAUSES:
  1. Cellular-exposed management interface (no firewall)
  2. No network segmentation between IVI and vehicle CAN
  3. V850 firmware update without authentication (no signature check)
  4. IVI to CAN bridge without message filtering/whitelist

FIXES APPLIED:
  1. Sprint blocked port-scanning on their network
  2. Fiat Chrysler released patch (USB stick distribution — pre-OTA era)
  3. Uconnect network isolation improved
  4. V850 firmware update now requires authentication

LESSONS:
  → IVI must be isolated from chassis CAN (firewall gateway required)
  → Cellular attack surface requires firewall + VPN or NAT
  → No ECU should accept arbitrary firmware without cryptographic validation
  → Pentest must cover remote attack paths, not just physical OBD attacks
```

---

## 15.2 Tesla Model S Remote Exploit (2016) — Keen Security Lab

```
RESEARCHERS: Keen Security Lab (Tencent), China
PUBLISHED:   September 2016

ATTACK CHAIN:

  [1] WIFI + BROWSER EXPLOIT
      ↓ Connected to rogue Wi-Fi hotspot (attacker-controlled)
      ↓ Exploited Chromium-based browser in infotainment
      ↓ WebKit vulnerability → code execution in browser renderer
      
  [2] BROWSER SANDBOX ESCAPE
      ↓ Escaped browser sandbox via kernel vulnerability
      ↓ Gained root access to Linux-based IVI system (Ubuntu)
      
  [3] IVI → CAN BUS
      ↓ IVI connected to internal CAN bus (same architecture flaw)
      ↓ Injected CAN frames directly from compromised IVI
      
  [4] DEMONSTRATED IMPACT (while car moving at 12 mph):
      ↓ Sunroof opened/closed remotely
      ↓ Seat position changed
      ↓ Instrument cluster manipulated
      ↓ Brakes applied (rear brakes only, limited test)
      ↓ Door locks opened/closed

DISCLOSURE: Responsible disclosure to Tesla → patched in 10 days
TESLA RESPONSE: Very fast OTA patch ("best response time of any OEM")

SUBSEQUENT RESEARCH (2017, 2018):
  Keen found: ECU log file path traversal, Ethernet bus exploitation
  Tesla fixed: isolated IVI from CAN via gateway with filtering
```

---

## 15.3 Key Fob Relay Attack (Ongoing — All Manufacturers)

```
ATTACK TYPE: Relay Attack (not a code replay — a signal relay)
IMPACT: Billions of dollars in vehicle theft annually (UK: #1 method since 2021)

HOW PASSIVE ENTRY WORKS (legitimate):
  Car → emits low-frequency (LF 125 kHz) challenge to nearby key fob
  Key fob → receives challenge, computes response using secret key
  Key fob → transmits response at UHF (315/433 MHz)
  Car → verifies response → unlocks doors + authorizes ignition

HOW RELAY ATTACK WORKS:
  
  ┌─────────────────────────────────────────────────────────┐
  │  Attacker 1          Attacker 2             Victim Car  │
  │  (near house/         (in car park          (locked)    │
  │   pocket, office)     or street)                        │
  │                                                         │
  │  Attacker 1's       Attacker 2's                        │
  │  relay device  ─────► relay device ──────────────────► │
  │  (picks up          (re-emits LF         Car thinks     │
  │   LF from car)       near key fob)        key is nearby │
  │                                                         │
  │                       Key fob responds                  │
  │                       Attacker 2 relay ─────────────────│
  │                       re-emits UHF                      │
  │                                                         │
  │                                         Car: UNLOCKED   │
  └─────────────────────────────────────────────────────────┘

RELAY ATTACK DETAILS:
  - LF relay device: EM field amplifier + transmitter
  - UHF relay: SDR or custom RF board
  - Range: attacker 1 within 2-3m of building/room, attacker 2 at car
  - Total relay distance: up to 100m possible
  - Cost of equipment: £30–£200 (available on eBay)
  - Attack duration: 5–30 seconds

DEFENSES:
  1. Ultra-Wideband (UWB) ranging: precise distance measurement
     → Key must be within 1-2 meters (relay fails: 50-100m gap detected)
     → Implemented in: Apple AirTag, BMW Digital Key Plus, Volvo UWB
     
  2. Motion sensor in key fob (Bosch/Continental):
     → Fob detects zero motion → disables LF response
     → Defeats relay (fob won't respond when stationary at home)
     
  3. Faraday pouches: blocks all RF (consumer protection)
  
  4. PIN-to-drive: require PIN code in addition to key fob
```

---

## 15.4 CAN Bus Injection to Defeat Speed Limiters

```
ATTACK: CAN message injection to disable Intelligent Speed Assistance (ISA)
RELEVANCE: EU mandated ISA in all new cars from July 2024 (EU 2019/2144)

HOW ISA WORKS:
  Camera/GPS reads speed sign → sends CAN message to powertrain ECU
  Powertrain ECU → limits throttle if speed exceeds limit
  
ATTACK METHOD:
  Physical access to OBD-II port required
  Connect CAN USB adapter (PCAN, PEAK, Vector)
  Inject CAN message spoofing GPS/camera signal
  Signal says: "no speed limit sign detected" or "speed limit = 255 km/h"
  Powertrain ECU accepts spoofed signal → ISA effectively disabled
  
REAL CASE: Multiple YouTube videos demonstrating this on VAG group vehicles
           Security researchers at IOActive demonstrated on BMW (2023)
  
MITIGATIONS:
  - SecOC on ISA CAN messages (camera/GPS to PCM)
  - Multi-source confirmation: GPS + camera must agree
  - OBD port lockdown (PATS-like diagnostic authentication)
  - Geo-fencing: cross-reference GPS vs speed limit database independently
```

---

## 15.5 OBD-II Port Dongle Attack (Progressive Insurance Case)

```
ATTACK VECTOR: Insurance/fleet telematics dongle plugged into OBD-II

BACKGROUND:
  Many insurance companies (Progressive Snapshot, etc.) provide OBD-II
  dongles for "good driver" discounts. Fleets use them for telematics.
  
VULNERABILITIES FOUND (2015, University of California San Diego):
  1. Dongle had Bluetooth with default PIN "0000"
  2. Paired attacker phone could send commands to dongle
  3. Dongle had full access to all CAN buses (no OBD-II isolation)
  4. Researcher (Charlie Miller) could drive by and send CAN messages
     via the dongle's Bluetooth interface
  5. Result: arbitrary CAN injection from Bluetooth range (~10 meters)
  
IMPACT:
  Full vehicle CAN bus access without any direct vehicle connection
  Persistent attack vector (dongle remains plugged in)
  
LESSONS:
  → OBD dongles should use secure Bluetooth (authentication + encryption)
  → OBD dongles should only expose OBD-II PIDs, not raw CAN
  → Insurers should certify dongle security before deployment
  → OEM should consider OBD port authentication (UDS-based gateway)
```

---

## 15.6 BMW ConnectedDrive (2015)

```
VULNERABILITY: SSL/TLS implementation error in BMW's connected services
DISCOVERED BY: ADAC (German automobile club), January 2015
AFFECTED: 2.2 million BMW, Mini, Rolls-Royce vehicles

ATTACK:
  BMW ConnectedDrive used HTTP → HTTPS redirect (not HTTPS-first)
  Attacker on same network (hotel Wi-Fi, mobile hotspot)
  Executed SSL stripping MITM attack
  Intercepted ConnectedDrive traffic
  
RESULT:
  Attacker could send fake "open door" commands to vehicle
  Vehicle accepted commands without re-authenticating the source
  Doors could be unlocked remotely by MITM attacker
  
ROOT CAUSE:
  No certificate pinning in ConnectedDrive client
  HTTP redirect allowed (HSTS not enforced)
  
FIX:
  BMW pushed update via cellular (one of earliest automotive OTA patches)
  Enforced HTTPS-only
  Added certificate pinning
  
LESSON:
  → API security = vehicle security: backend compromise = physical access
  → Certificate pinning is mandatory for vehicle connected services
  → HSTS preloading for all automotive backend domains
```

---

## 15.7 Tesla API Token Theft

```
ATTACK TYPE: Account takeover via API token theft
ONGOING RISK: Multiple incidents, most not publicly disclosed

METHOD:
  1. Phishing email to Tesla account owner
  2. Fake Tesla login page captures username + password
  3. Attacker logs into Tesla app with stolen credentials
  4. Tesla API returns OAuth bearer token
  5. Attacker uses token to:
     - Track vehicle location (GPS history)
     - Unlock doors remotely
     - Flash lights, honk horn (distraction/stalking)
     - Enable "Sentry Mode" to capture camera feeds
     - Disable charging remotely
     
  Advanced variant:
  Attacker also requests password reset during attack
  Changes account email → victim locked out → persistent access
  
MITIGATIONS:
  → MFA (Multi-factor authentication) for all vehicle API accounts
  → Token binding to device (tokens not portable to other devices)
  → Anomalous access detection (new device/location login alert)
  → Critical actions (door unlock) require re-authentication
  → Token lifetime limits (short-lived, auto-refresh)
```

---

## 15.8 Summary — Module 15

```
ATTACK PATTERNS ACROSS ALL CASE STUDIES:

1. IVI–CAN bridge: #1 root cause (Jeep, Tesla, key fob)
   Fix: Gateway with strict message filtering between IVI and chassis

2. Unencrypted or poorly authenticated network services
   Fix: TLS 1.3 everywhere, certificate pinning

3. Physical interfaces without authentication (OBD, JTAG, UART)
   Fix: Secure boot, JTAG fusing, OBD port authentication

4. Firmware update without cryptographic validation
   Fix: Signed OTA with rollback protection

5. No SecOC on safety-critical CAN messages
   Fix: Deploy SecOC (CMAC-AES128) on all safety-critical messages

DETECTION IMPROVEMENTS NEEDED:
  - Behavioral analytics: detect unusual CAN patterns
  - Network telemetry from IVI to cloud
  - UDS session logging with SIEM integration

INDUSTRY EVOLUTION:
  2015: No network segmentation, no encryption, no signing
  2024: Gateway required by R155, SecOC standardized, OTA mandatory
  2027: UWB for keyless, post-quantum cryptography exploration starting
```

**Next Module**: [16 — Hands-On Labs](16_hands_on_labs.md)
