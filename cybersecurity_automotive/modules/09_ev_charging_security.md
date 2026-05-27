# Module 09 — EV & Charging Security

> Level: Intermediate → Advanced | Est. study time: 7 hours

---

## 9.1 EV Architecture & Security-Relevant Components

```
EV ELECTRICAL & ELECTRONIC ARCHITECTURE:

  ┌────────────────────────────────────────────────────────────┐
  │               HIGH VOLTAGE SYSTEM                          │
  │  ┌──────────┐  HV CAN  ┌──────────┐  HV CAN  ┌─────────┐ │
  │  │  BMS     │◄─────────►│  VCU     │◄─────────►│  OBC    │ │
  │  │ (Battery │          │(Vehicle  │          │(On-Board│ │
  │  │ Mgmt Sys)│          │Control   │          │Charger) │ │
  │  └──────────┘          │Unit)     │          └─────────┘ │
  │                        └────┬─────┘                       │
  │                             │                             │
  │                    ┌────────▼────────┐                    │
  │                    │    Inverter /   │                    │
  │                    │  Motor Control  │                    │
  │                    └─────────────────┘                    │
  └────────────────────────────────────────────────────────────┘
  
  ┌────────────────────────────────────────────────────────────┐
  │               CHARGING INTERFACE                           │
  │                                                            │
  │  AC Charging (Level 1/2):    DC Fast Charging (Level 3):  │
  │  ┌─────────────────────┐     ┌─────────────────────────┐  │
  │  │  Type 2 / J1772     │     │  CCS (Combined Charging │  │
  │  │  Pilot signal (PWM) │     │  System) / CHAdeMO      │  │
  │  │  IEC 61851-1        │     │  ISO 15118 / DIN SPEC   │  │
  │  │  Basic control      │     │  70121                  │  │
  │  └─────────────────────┘     └─────────────────────────┘  │
  └────────────────────────────────────────────────────────────┘
```

---

## 9.2 BMS (Battery Management System) Security

The BMS is critical: it controls charge/discharge, cell balancing, and thermal management.
A compromised BMS can cause battery thermal runaway (fire).

### BMS Attack Scenarios

```
Attack 1: BMS CAN Signal Manipulation
  Target: BMS ↔ VCU communication on HV CAN bus
  Signal: State_of_Charge (SoC) — sent from BMS to VCU
  
  Attack:
    1. Physical access to HV CAN bus (usually requires disassembly)
    2. Inject CAN frame with ID: 0x0CF (BMS status, typical J1939)
    3. Set SoC_Reported = 10%  (actual SoC = 85%)
    4. VCU restricts performance, activates charge warnings
    5. Driver panics, pulls over → vehicle disabled (availability attack)
  
  OR:
    Set SoC_Reported = 100%  (actual SoC = 5%)
    VCU does not restrict drive → battery depleted beyond limits → damage
  
  Mitigation: SecOC on HV CAN bus BMS messages

Attack 2: Overcharge via BMS Manipulation
  Target: OBC (On-Board Charger) charge control signal
  
  Attack:
    1. Manipulate "Charge_Current_Limit" signal (BMS → OBC)
    2. Override OBC to charge beyond cell voltage limit
    3. Cells overcharged → thermal runaway → fire
  
  DANGER LEVEL: CATASTROPHIC — this is a life-safety issue
  Mitigation: Hardware OVP (Over Voltage Protection) in BMS independent of software

Attack 3: Temperature Sensor Spoofing
  Target: Cell temperature reporting
  
  Attack:
    1. Spoof temperature sensors to report low values
    2. BMS allows fast charging in what it thinks is cool battery
    3. Actual temperature too high → thermal runaway
    
  Mitigation: Redundant temperature sensors + hardware thermal fuse
```

---

## 9.3 ISO 15118 — Charging Communication Security

ISO 15118 defines the communication protocol between EV and EVSE (charger):

```
COMMUNICATION LAYERS:

  EV (Vehicle)                    EVSE (Charger)
  ──────────────                  ──────────────────
  V2G Application                 V2G Application
  ISO 15118-2 (AC/DC)    ←TLS→    ISO 15118-2
  EXI (Efficient XML)             EXI encoding
  TCP/UDP                         TCP/UDP
  IPv6                            IPv6
  HomePlug Green PHY              HomePlug Green PHY
  CCS Connector                   CCS Connector
```

### ISO 15118 Security Features

```
1. TLS Mutual Authentication:
   EV has: Contract Certificate (signed by OEM CA or Mobility Operator CA)
   EVSE has: Server certificate
   → Both parties verify each other's identity before charging starts

2. Plug & Charge (PnC):
   - EV presents certificate to EVSE automatically (no app, no card)
   - EVSE validates certificate chain against V2G root CA
   - Billing identity is the certificate (EV's contract ID)

3. V2G PKI (Vehicle to Grid Public Key Infrastructure):
   Root CA (V2G Root CA — trust anchor for all participants)
     ├── OEM Provisioning CA (issues Vehicle contracts)
     │     └── Vehicle Contract Certificate (per vehicle)
     └── CPO (Charge Point Operator) CA
           └── EVSE Certificate
```

### ISO 15118 Attack Scenarios

```
Attack 1: Certificate Replay
  Scenario: Steal EV's contract certificate → charge at victim's expense
  
  Attack:
    1. Passive eavesdrop on TLS 1.2 (vulnerable older charger)
    2. Capture certificate in ClientHello
    3. Use at different charger
  
  Mitigation: TLS 1.3 (forward secrecy) + certificate revocation (OCSP)

Attack 2: Fake EVSE (Rogue Charger)
  Scenario: Attacker deploys rogue charging station
  
  Attack:
    1. Deploy fake EVSE with self-signed certificate
    2. EV connects (driver unaware)
    3. Man-in-the-middle: TLS terminated at rogue EVSE
    4. Can read contract certificate, billing info
    5. Can manipulate charging commands
  
  Mitigation: Vehicle must verify EVSE certificate against trusted CA chain

Attack 3: V2G Protocol Fuzzing (DoS)
  Attack:
    1. Connect to EVSE charging port
    2. Send malformed ISO 15118 messages (EXI encoding attacks)
    3. Charger application crashes → charger unavailable
    
  Real-world: Researchers found buffer overflows in several EVSE implementations
  Mitigation: Input validation, memory-safe parsers, fuzzing in development

Attack 4: Energy Theft via Protocol Manipulation
  Vulnerability: EVSE trusts EV's reported charging state without backend validation
  
  Attack:
    1. Modify EV software to report "charging complete" prematurely
    2. EVSE stops billing but energy continues to flow
    3. OR: Report continuing after actual disconnection
    
  Mitigation: Backend validation, metering certificate (certified energy meter in EVSE)
```

---

## 9.4 OCPP (Open Charge Point Protocol) Security

OCPP is used between EVSE and charging backend (CSMS):

```
Architecture:
  EVSE (Charger) ──(WebSocket/OCPP 2.0.1)──► CSMS (Cloud Backend)

OCPP Security Profile 3 (mandatory for secure deployments):
  - TLS 1.2/1.3 + mutual authentication
  - Client certificate for each EVSE
  - CSMS validates EVSE certificate before accepting commands

OCPP Attack Scenarios:
┌──────────────────────────────────────────────────────────────────┐
│ Attack 1: Rogue CSMS                                             │
│   EVSE connects to attacker's CSMS (e.g., via DNS spoofing)      │
│   Attacker sends: RemoteStartTransaction to bill victims         │
│   OR:             FirmwareUpdate with malicious EVSE firmware    │
│   Mitigation: TLS cert pinning + EVSE cert verification          │
│                                                                  │
│ Attack 2: Replay Attack on OCPP Commands                         │
│   Record legitimate RemoteStartTransaction                       │
│   Replay at different time/EVSE                                  │
│   Mitigation: OCPP session IDs, timestamp in requests            │
│                                                                  │
│ Attack 3: Unauthorized Firmware Update                           │
│   Send FirmwareUpdate.req with malicious firmware URL            │
│   EVSE downloads and installs without signature check            │
│   Mitigation: EVSE must verify firmware signature (PKI)          │
│                                                                  │
│ Attack 4: Grid Destabilization (Fleet Scale)                     │
│   Compromise CSMS → send RemoteStartTransaction to 10,000 EVSEs │
│   All start charging simultaneously                              │
│   Grid frequency drops → cascading failure                       │
│   Mitigation: Backend rate limiting, demand response controls    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9.5 Smart Charging / V2G Security

```
Vehicle-to-Grid (V2G) enables EVs to feed energy back to the grid:

  Battery ──(OBC)──► Grid  (V2G mode: EV = prosumer)

Security Implications:
  - Bidirectional power flow = bidirectional attack surface
  - Grid stability depends on accurate V2G participation
  - Attacker compromising V2G protocol can:
    → Cause EV to discharge unexpectedly (availability/financial)
    → Manipulate energy pricing signals (financial)
    → Aggregate V2G EVs to create virtual power plant for DoS on grid

Smart Charging Attack:
  1. Compromise CSMS or charging management system
  2. Send SmartCharging profiles: charge all vehicles at peak hour
  3. Grid overloaded → brownout in target area

Countermeasures:
  - V2G commands cryptographically signed by certified authority
  - EV applies rate limits on grid power draw regardless of commands
  - Hardware power limits (cannot be overridden by software)
  - ISO 15118-20 (new): enhanced security for V2G bidirectional power
```

---

## 9.6 Summary — Module 09

```
KEY TAKEAWAYS:

✓ BMS attacks can cause battery thermal runaway — hardware OVP independent of SW
✓ ISO 15118 provides TLS mutual auth and Plug & Charge PKI for charging security
✓ OCPP deployments must use Security Profile 3 (TLS + mutual cert auth)
✓ Rogue charger attack: EV must verify EVSE certificate chain
✓ OCPP firmware update must require signed packages (same as vehicle OTA)
✓ Grid destabilization via fleet-scale CSMS compromise is a real critical infrastructure risk
✓ V2G commands must be signed — anonymous grid commands must be rejected
✓ Temperature sensor redundancy (hardware) is the last line of defense vs thermal attacks
```

**Next Module**: [10 — AUTOSAR Security](10_autosar_security.md)
