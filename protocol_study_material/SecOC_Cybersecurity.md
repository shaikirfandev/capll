# SecOC & Automotive Cybersecurity Study Material
## AUTOSAR SecOC | ISO 21434 | UN R155 | Cryptographic Protection

---

## 1. Why Automotive Cybersecurity?

Modern vehicles have **100+ ECUs** communicating over internal buses. Without protection:
- CAN bus is unauthenticated — any ECU can spoof any message
- Remote attacks via OBD-II, telematics, V2X
- Safety consequences: spoofed brake commands, engine shutoff

**Key standards:**
- **AUTOSAR SecOC** (Secure Onboard Communication) — message authentication
- **ISO 21434** — automotive cybersecurity engineering process
- **UN Regulation No. 155** — mandatory cybersecurity management system (CSMS)
- **UN Regulation No. 156** — software update management (SUMS)

---

## 2. AUTOSAR SecOC Architecture

SecOC is an AUTOSAR module that adds a **Message Authentication Code (MAC)** to PDUs.

### Transmission (Sender ECU)
```
[Application PDU]
       ↓
[SecOC Module - Add Freshness + Compute MAC]
       ↓
[IPDU with Authenticator appended]
       ↓
[COM / PduR → CAN/LIN/Ethernet]
```

### Reception (Receiver ECU)
```
[Received IPDU]
       ↓
[SecOC Module - Extract Authenticator + Verify MAC]
       ↓  (Pass / Fail)
[If Pass → Deliver to Application]
[If Fail → Report Security Event, optionally discard]
```

---

## 3. SecOC PDU Structure

```
|<---------- Authentic PDU ----------->|<-- Authenticator --|
+------------------+-------------------+--------------------+
| Authentic I-PDU  | Freshness Value   |    Truncated MAC   |
| (payload)        | (partial/full)    |    (e.g., 24 bit)  |
+------------------+-------------------+--------------------+
```

| Field | Description |
|-------|-------------|
| **Authentic I-PDU** | Original data payload |
| **Freshness Value (FV)** | Counter/timestamp to prevent replay attacks |
| **Truncated MAC** | Cryptographic MAC, truncated to save bus bandwidth |

---

## 4. MAC Computation

### Algorithm (typically AES-128-CMAC)
```
MAC = CMAC_AES128(Key, DataToAuth)

DataToAuth = Authentic_IPDU || Full_Freshness_Value || DataID
```

The **Key** is stored in HSM (Hardware Security Module) — never accessible to application software.

### Truncation
Full CMAC = 128 bits. Typically truncated to **24–32 bits** for CAN bus (8-byte limit).

Trade-off: Shorter MAC = less security (birthday attack probability increases).

---

## 5. Freshness Value (Anti-Replay)

**Purpose:** Prevent replay attacks where attacker captures and retransmits valid frames.

### FV Schemes

| Scheme | Description |
|--------|-------------|
| **Trip Counter** | Resets at ignition-on, increments per message |
| **Monotonic Counter** | Never resets, stored in NVM |
| **Timestamp** | Time-based, requires synchronized clock |

### FV Synchronization
Since the full FV may be too large for CAN (bandwidth), only **truncated FV** is sent in PDU. Receiver reconstructs full FV using its local counter + received truncated bits. FV Manager runs as separate AUTOSAR module.

---

## 6. SecOC Configuration (AUTOSAR)

```xml
<!-- SecOC PDU configuration example -->
<SECURED-I-PDU>
  <SHORT-NAME>SecuredPdu_EngineCtrl</SHORT-NAME>
  <AUTHENTIC-PDU-REF>EngineCtrl_IPDU</AUTHENTIC-PDU-REF>
  <AUTH-INFO-TX-LENGTH>4</AUTH-INFO-TX-LENGTH>  <!-- 4 bytes = FV(8bit) + MAC(24bit) -->
  <DATA-ID>0x0042</DATA-ID>
  <FRESHNESS-VALUE-LENGTH>32</FRESHNESS-VALUE-LENGTH>
  <FRESHNESS-VALUE-TX-BIT-LENGTH>8</FRESHNESS-VALUE-TX-BIT-LENGTH>  <!-- Truncated TX -->
  <MESSAGE-LINK-METHOD>SECURED-AREA</MESSAGE-LINK-METHOD>
</SECURED-I-PDU>
```

---

## 7. ISO 21434 – Automotive Cybersecurity Engineering

### Process Overview
ISO 21434 ("Road vehicles — Cybersecurity engineering") published **2021-08**.

```
Item Definition
      ↓
TARA (Threat Analysis & Risk Assessment)
      ↓
Cybersecurity Goals
      ↓
Cybersecurity Concept (Countermeasures)
      ↓
Product Development (Design, Implementation, Test)
      ↓
Post-Development (Production, Operations, Incident Response, Decommission)
```

---

## 8. TARA Process (Threat Analysis & Risk Assessment)

### Step 1: Asset Identification
Identify assets and their cybersecurity properties:
- **Confidentiality** — e.g., customer data, firmware
- **Integrity** — e.g., safety-critical commands
- **Availability** — e.g., braking, steering

### Step 2: Threat Scenario Identification (STRIDE)

| Threat | Example |
|--------|---------|
| **S**poofing | Fake brake command on CAN |
| **T**ampering | Modify firmware via OBD-II |
| **R**epudiation | Log manipulation |
| **I**nformation Disclosure | Extract calibration data via XCP |
| **D**enial of Service | Flood CAN bus |
| **E**levation of Privilege | Gain root access via infotainment |

### Step 3: Attack Path Analysis
Identify attack vectors, prerequisites, and attack feasibility.

**Attack Feasibility Rating (per ISO 21434 Annex B):**

| Factor | Rating |
|--------|--------|
| Elapsed time | < 1 day → High feasibility |
| Specialist expertise | Layman → High feasibility |
| Knowledge of item | Public → High feasibility |
| Window of opportunity | Easy access → High feasibility |
| Equipment | Standard → High feasibility |

**Overall Feasibility:** High / Medium / Low / Very Low

### Step 4: Impact Rating (SFOP)
- **S**afety impact
- **F**inancial impact
- **O**perational impact (vehicle service)
- **P**rivacy impact

| Level | Description |
|-------|-------------|
| Severe | Life-threatening / massive financial loss |
| Major | Serious injury / significant loss |
| Moderate | Light injury / limited loss |
| Negligible | No injury / no loss |

### Step 5: Risk Value
```
Risk = Impact × Feasibility
```
Risk levels: Critical / High / Medium / Low

---

## 9. Cybersecurity Controls

| Category | Example Controls |
|----------|-----------------|
| Secure Boot | Verify firmware MAC before boot |
| Secure Communication | SecOC, TLS 1.3, MACsec |
| Access Control | UDS security access, key management |
| Intrusion Detection | IDS/IPS monitoring CAN bus |
| Firmware Update | FOTA with signature verification |
| HSM | Hardware-protected key storage |
| Penetration Testing | Fuzzing, protocol attacks |

---

## 10. UN R155 – CSMS Requirements

Mandatory for vehicle type approval in **EU, Japan, Korea** (from July 2022 for new types, July 2024 for all new vehicles).

**OEM must demonstrate:**
1. Cybersecurity Management System (CSMS) certified by authority
2. Identification and management of cyber risks
3. Detection and response to cyber-attacks
4. Secure software updates (linked to UN R156)

---

## 11. HSM (Hardware Security Module)

Modern automotive MCUs (e.g., Infineon AURIX, NXP S32) include on-chip HSM:

| HSM Feature | Description |
|-------------|-------------|
| Key storage | Secret keys never leave HSM |
| AES-128/256 | Symmetric encryption/decryption |
| RSA/ECC | Asymmetric operations for boot verification |
| TRNG | True Random Number Generator |
| SHE | AUTOSAR Security Hardware Extension spec |

---

## 12. Interview Q&A

**Q: What is the purpose of a Freshness Value in SecOC?**
> The Freshness Value (FV) is a counter or timestamp included in the MAC computation to prevent **replay attacks**. If an attacker captures a valid authenticated message and retransmits it, the receiver will reject it because the expected FV has already advanced.

**Q: Why are MACs truncated in SecOC, and what is the risk?**
> CAN frames are limited to 8 bytes. After payload, only a few bytes remain for authentication. MACs are truncated (e.g., 24-bit). The risk is a higher probability of collision (birthday attack) — with a 24-bit MAC, there is a 1-in-16M chance of a random frame matching. This is acceptable given the difficulty of exploiting it within vehicle communication constraints.

**Q: What is TARA in ISO 21434?**
> Threat Analysis and Risk Assessment. It is the systematic process of identifying assets, threats (using STRIDE), attack paths, feasibility of attacks, and impact — resulting in a risk level per threat scenario. Risk levels drive selection of cybersecurity controls.

**Q: What is the difference between ISO 21434 and UN R155?**
> ISO 21434 is the **engineering standard** describing how to design and develop secure vehicles. UN R155 is a **regulatory requirement** by the United Nations that mandates OEMs have a certified CSMS (Cybersecurity Management System). ISO 21434 can be used to fulfill UN R155 technical requirements.

**Q: What is a Secure Boot and why is it important?**
> Secure Boot verifies the integrity and authenticity of firmware before allowing it to execute. On startup, the HSM verifies the bootloader signature (using a pre-provisioned root key), and each stage verifies the next. This prevents malicious firmware from running even if someone gains physical access and attempts to flash modified code.
