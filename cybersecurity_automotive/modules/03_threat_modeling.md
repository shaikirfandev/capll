# Module 03 — Threat Modeling & TARA

> Level: Intermediate | Est. study time: 8 hours | ISO/SAE 21434 §15

---

## 3.1 What is TARA?

**TARA** (Threat Analysis and Risk Assessment) is the ISO 21434-mandated process
for systematically identifying and evaluating cybersecurity risks in vehicle systems.

```
TARA Process Flow (ISO 21434 §15):

  Item Definition
       │
       ▼
  Asset Identification ────────────────────────────────────────────┐
       │                                                           │
       ▼                                                           │
  Threat Scenario Identification                                   │
       │                                                           │
       ▼                                                           │
  Impact Rating (Safety/Financial/Operational/Privacy)            │
       │                                                           │
       ▼                                                           ▼
  Attack Path Analysis ──────────────────────────────────► Attack Feasibility
       │
       ▼
  Risk Determination (Impact × Feasibility)
       │
       ▼
  Risk Treatment Decision
  (Avoid / Reduce / Transfer / Accept)
       │
       ▼
  Cybersecurity Goals & Controls
```

---

## 3.2 STRIDE Threat Model

STRIDE is a threat classification model from Microsoft, widely adopted in automotive:

| Letter | Category | Definition | Automotive Example |
|--------|----------|-----------|-------------------|
| **S** | Spoofing | Pretend to be someone/something else | Fake ADAS ECU sending AEB disable |
| **T** | Tampering | Modify data or code | Alter CAN signal value, firmware |
| **R** | Repudiation | Deny performing an action | ECU flashed, no audit log |
| **I** | Information Disclosure | Expose private data | VIN + GPS + PII from TCU |
| **D** | Denial of Service | Make system unavailable | CAN flood, bus-off attack |
| **E** | Elevation of Privilege | Gain unauthorized access | UDS default→programming session |

### STRIDE Applied to Gateway ECU

```
ITEM: Central Gateway ECU (CGW)
INTERFACES:
  - CAN_PT (Powertrain CAN)
  - CAN_ADAS (ADAS CAN)
  - CAN_IVI (Infotainment CAN)
  - Eth_TCU (Ethernet to Telematics)
  - OBD-II (Diagnostic access)

STRIDE Analysis:
┌───────────────┬────────────────────────────────────┬─────────┐
│ Threat        │ Scenario                           │ Control │
├───────────────┼────────────────────────────────────┼─────────┤
│ Spoofing      │ Attacker sends fake ECM CAN msgs   │ SecOC   │
│ Tampering     │ Modify routed message payload      │ E2E+MAC │
│ Repudiation   │ Diagnostic commands not logged     │ Audit log│
│ Info Disc.    │ Eavesdrop Eth_TCU link             │ TLS 1.3 │
│ DoS           │ Flood CAN_ADAS → AEB disabled      │ Rate limit│
│ EoP           │ OBD-II → programming session       │ Seed-key│
└───────────────┴────────────────────────────────────┴─────────┘
```

---

## 3.3 DREAD Risk Scoring

DREAD provides quantitative scores (1–3 each) for risk prioritization:

| Dimension | 1 (Low) | 2 (Medium) | 3 (High) |
|-----------|---------|-----------|---------|
| **D**amage | Minor annoyance | Financial loss | Injury/death |
| **R**eproducibility | Hard to repeat | Repeatable with effort | Always works |
| **E**xploitability | Requires expert, special HW | Moderate skill | Script kiddie |
| **A**ffected users | One vehicle, local | Multiple vehicles | Entire fleet |
| **D**iscoverability | Buried in code | Known to researchers | Published exploit |

**DREAD Score = (D+R+E+A+D) / 5**
- Score < 1.5 = Low
- 1.5–2.5 = Medium
- > 2.5 = High / Critical

**Example — CAN Injection via OBD-II:**
```
Damage:         3 (AEB disable could cause accident)
Reproducibility:3 (Works every time with 10€ adapter)
Exploitability: 2 (Python script, basic CAN knowledge)
Affected users: 2 (Single vehicle per attack)
Discoverability:3 (Published research papers)
DREAD Score = (3+3+2+2+3)/5 = 2.6 → CRITICAL
```

---

## 3.4 Attack Trees

Attack trees decompose an attack goal into sub-goals:

```
GOAL: Disable AEB on target vehicle remotely
─────────────────────────────────────────────
ATTACK TREE:

[GOAL] Disable AEB Remotely
├── [OR] Compromise ADAS ECU
│   ├── [OR] Via CAN injection
│   │   ├── [AND] Physical OBD access
│   │   └── [AND] Reverse-engineer CAN signals
│   └── [OR] Via OTA malicious update
│       ├── [AND] Compromise OTA backend
│       └── [AND] Sign malicious firmware
│           └── Steal code signing key
├── [OR] Blind sensors (spoofing)
│   ├── Radar spoofing (hardware jammer)
│   └── Camera saturation (laser/flashlight)
└── [OR] Exhaust ADAS ECU (DoS)
    ├── CAN bus flood (high priority ID)
    └── Eth DoS (UDP flood if Eth-connected)

Likelihood ratings:
  Physical OBD + CAN reverse = 0.4 (moderate, requires physical access)
  OTA compromise              = 0.1 (hard, backend is hardened)
  Sensor spoofing            = 0.6 (radar jammers commercially available)
  CAN flood via OBD          = 0.7 (trivial, script available online)
```

---

## 3.5 ISO 21434 TARA Step-by-Step

### Step 1: Asset Identification

Identify what needs protecting (CIA properties per asset):

```
┌─────────────────────────────────┬──────────────────────────────────────┐
│ Asset                           │ Security Properties                  │
├─────────────────────────────────┼──────────────────────────────────────┤
│ Code signing key (HSM)          │ Confidentiality, Integrity           │
│ ECU firmware image              │ Integrity, Authenticity              │
│ UDS programming session         │ Integrity, Access Control            │
│ VIN + GPS telemetry             │ Confidentiality, Integrity           │
│ AEB activation signal (CAN)     │ Integrity, Availability              │
│ Vehicle unlock command (RKE)    │ Integrity, Authenticity              │
│ OTA update package              │ Integrity, Authenticity              │
│ Seed-key algorithm              │ Confidentiality                      │
│ SecOC key material              │ Confidentiality, Integrity           │
│ LiDAR/Radar raw data            │ Integrity, Availability              │
└─────────────────────────────────┴──────────────────────────────────────┘
```

### Step 2: Damage Scenario Identification

For each asset, define what damage its compromise causes:

```
Asset: AEB activation signal
Damage Scenarios:
  DS-01: AEB signal injected to trigger false emergency brake on highway
         → Rear-end collision from following vehicle
         → Impact: SAFETY (ASIL D equivalent)
         
  DS-02: AEB signal suppressed during genuine emergency
         → Vehicle fails to brake for obstacle
         → Impact: SAFETY (catastrophic)
         
  DS-03: AEB signal manipulated to report "always active" 
         → Driver overconfidence, reduced manual vigilance
         → Impact: SAFETY (indirect)
```

### Step 3: Impact Rating

ISO 21434 defines four impact categories:

| Category | S0 | S1 | S2 | S3 |
|----------|----|----|----|----|
| **Safety** | No injury | Light injury | Severe injury | Life-threatening/fatal |
| **Financial** | No loss | <€1M | €1M–€10M | >€10M |
| **Operational** | No degradation | Limited function | Core function affected | Mission critical |
| **Privacy** | No data | Anonymous data | Personal data | Sensitive personal data |

```
DS-01 (False AEB trigger on highway):
  Safety:     S3 (fatal rear-end collision)
  Financial:  S2 (liability, recall)
  Operational:S2 (feature disabled)
  Privacy:    S0 (no privacy impact)
  → Overall Impact = SEVERE (max category = S3)
```

### Step 4: Attack Feasibility

ISO 21434 uses five factors to rate feasibility:

| Factor | Values | Weight |
|--------|--------|--------|
| **Elapsed time** | <1 day / 1 wk / 1 mo / 3 mo / >6 mo | - |
| **Expertise** | Layman / Proficient / Expert / Multiple experts | - |
| **Knowledge** | Public / Restricted / Confidential / Secret | - |
| **Window of opportunity** | Unlimited / Easy / Moderate / Difficult | - |
| **Equipment** | Standard / Specialized / Bespoke / Multiple bespoke | - |

```
Attack: CAN injection via OBD-II to suppress AEB signal

Elapsed time:     <1 week (public scripts available)     → 0
Expertise:        Proficient (CAN tools knowledge)       → 3
Knowledge:        Public (DBC leaked / reverse-engineered)→ 0
Window of opport: Unlimited (OBD-II always accessible)   → 0
Equipment:        Standard (PCAN-USB = €50)              → 0

Attack Feasibility = LOW (easy attack) → HIGH RISK
```

### Step 5: Risk Determination Matrix

```
                    Attack Feasibility
                    High    Medium   Low    Very Low
                 ┌────────┬────────┬──────┬──────────┐
  Impact  S3/F3  │Critical│Critical│High  │Medium    │
          S2/F2  │Critical│High    │Medium│Low       │
          S1/F1  │High    │Medium  │Low   │Negligible│
          S0/F0  │Medium  │Low     │Neglg │Negligible│
                 └────────┴────────┴──────┴──────────┘
```

### Step 6: Risk Treatment

| Treatment | When to Apply | Example |
|-----------|---------------|---------|
| **Avoid** | Risk too high, cannot reduce | Remove OBD-II port write access entirely |
| **Reduce** | Apply controls to lower residual risk | Add SecOC to AEB signal |
| **Transfer** | Insurance, supplier liability | Tier-1 bears risk via contract |
| **Accept** | Residual risk after controls is negligible | Accept 0.001% bypass chance |

---

## 3.6 OEM-Level TARA Example: Gateway ECU

```
ITEM: Central Gateway ECU
HW: NXP S32G / Renesas R-Car
SW: AUTOSAR Classic 4.3
INTERFACES:
  - CAN HS x3 (Powertrain, Chassis, Body)
  - CAN FD x1 (ADAS)
  - 100BASE-T1 (TCU/OBD-over-Ethernet)
  - OBD-II (K-Line + CAN)

THREAT ID  ASSET              THREAT SCENARIO              IMPACT  FEASIBILITY  RISK
TS-GW-001  AEB CAN signal     Injection via OBD-II         S3      HIGH         CRITICAL
TS-GW-002  UDS prog session   Unlock without valid key     S2      MEDIUM       HIGH
TS-GW-003  Gateway firmware   Malicious reflash via OBD    S3      LOW          HIGH
TS-GW-004  CAN arbitration    Bus-off attack on AEB ECU    S3      HIGH         CRITICAL
TS-GW-005  Routing table      Modify routing to bypass FW  S2      LOW          MEDIUM
TS-GW-006  Telemetry data     Eavesdrop Eth link to TCU    P2      HIGH         HIGH
TS-GW-007  Crypto keys (HSM)  Extract via debug port       C3      VERY LOW     MEDIUM

CONTROLS:
TS-GW-001 → SecOC (CMAC) on AEB signal + source address filtering
TS-GW-002 → Seed-key Level 2, lockout after 3 failures, session timeout
TS-GW-003 → Secure Boot + signed firmware, programming session restricted
TS-GW-004 → Bus-off recovery + anomaly detection, rate limiting per ID
TS-GW-005 → Routing table in read-only flash region, integrity check on boot
TS-GW-006 → TLS 1.3 mutual auth on Ethernet link, VLAN isolation
TS-GW-007 → JTAG permanently fused, HSM key not exportable
```

---

## 3.7 ADAS ECU Threat Model (Beginner-Friendly)

```
ITEM: Forward-facing ADAS ECU (Camera + Radar fusion)
DAMAGE SCENARIOS:
  1. False braking event → rear collision (S3)
  2. AEB suppressed → frontal collision (S3)  
  3. Lane keeping malfunction → road departure (S3)
  4. Speed sign misread → ISA speed violation (S1)
  5. Calibration data corrupted → systematic errors (S2)

ATTACK VECTORS:
  Physical: OBD-II → CAN → ADAS CAN bus
  Physical: Debug port (SWD) → firmware dump
  Physical: Camera connector → feed manipulated video
  Remote: OTA → malicious ADAS firmware
  Remote: Eth → SOME/IP call to ADAS service (no auth)

TOP 3 RISKS (after analysis):
  RISK-01: CAN injection via OBD-II → suppress AEB → CRITICAL
  RISK-02: Malicious OTA firmware → enable attacker code → CRITICAL  
  RISK-03: Camera feed manipulation → blind ADAS → HIGH
```

---

## 3.8 Cybersecurity Goals Format (ISO 21434)

```
FORMAT:
  CG-[ID]: [Asset] shall maintain [Property] against [Threat] to prevent [Damage]

EXAMPLES:
  CG-AEB-01: The AEB activation signal shall maintain INTEGRITY against 
             unauthorized CAN injection to prevent false braking events.
             ASIL: D equivalent | Risk without control: CRITICAL

  CG-OTA-01: The OTA firmware package shall maintain AUTHENTICITY against 
             malicious firmware injection to prevent unauthorized ECU modification.
             ASIL: B equivalent | Risk without control: CRITICAL

  CG-UDS-01: The UDS programming session shall maintain ACCESS CONTROL against
             unauthorized activation to prevent unauthorized firmware flashing.
             ASIL: B equivalent | Risk without control: HIGH

  CG-KEY-01: The HSM-stored code signing key shall maintain CONFIDENTIALITY against
             extraction via debug port to prevent forgeable firmware signatures.
             ASIL: QM (financial/IP risk) | Risk without control: HIGH
```

---

## 3.9 TARA vs Other Approaches

| Method | Standard | Best For | Limitation |
|--------|----------|---------|-----------|
| TARA | ISO 21434 | Full automotive lifecycle | Complex, resource-heavy |
| STRIDE | Microsoft SDL | Software threat ID | Not quantitative |
| DREAD | Microsoft | Risk scoring | Subjective scores |
| PASTA | Privacy | Privacy-by-design | Less automotive-specific |
| Attack Trees | General | Detailed attack path | Manual, time-consuming |
| HEAVENS | Industry consortium | Automotive-specific scoring | Less standardized |
| cvss | NVD | Vulnerability severity | Post-discovery only |

---

## 3.10 Summary — Module 03

```
KEY TAKEAWAYS:

✓ TARA = ISO 21434 mandatory risk assessment; defines security goals
✓ STRIDE classifies threats into 6 types; apply to each ECU interface
✓ DREAD provides 1–3 numeric scoring for risk prioritization
✓ Attack trees decompose complex attacks into manageable sub-goals
✓ Impact × Feasibility = Risk level → drives control decisions
✓ Cybersecurity goals become technical requirements for design
✓ TARA is a living document — update for every architecture change
✓ Gateway ECU and TCU always have the highest attack surfaces
```

**Templates**: [TARA Template](../templates/tara_template.md) | [Threat Model Template](../templates/threat_model_template.md)

**Next Module**: [04 — ECU Security & Hardening](04_ecu_security.md)
