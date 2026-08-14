# Part 17 — Cybersecurity Integration

---

## 17.1 Secure Boot

**What:** Verify firmware integrity before execution on ECU startup.

**How it works:**
```
ECU Power-On
    ↓
Bootloader starts (ROM or read-protected flash)
    ↓
Compute SHA-256 of application firmware
    ↓
Verify ECDSA signature using OEM public key (stored in OTP/HSM)
    ↓
Match? → Execute application
No match? → Stay in safe state, set DTC, wait for re-flash
```

**Integration:**
- Public key provisioned to ECU at manufacturing (OTP)
- Build system signs firmware with OEM private key
- Bootloader verification code reviewed and tested

---

## 17.2 HSM (Hardware Security Module)

An HSM is a hardware block inside modern MCUs (e.g., NXP S32G HSE, Renesas RH850 HSM) that:
- Stores keys securely (never leave hardware)
- Performs cryptographic operations (AES, RSA, ECDSA, SHA)
- Provides true random number generator

**Integration:**
- Key provisioning at production
- Application uses HSM driver API for crypto operations
- TLS certificates and OTA signing keys stored in HSM

---

## 17.3 Secure Diagnostics

**Challenges:**
- UDS Security Access (0x27) protects programming and extended sessions
- Diagnostic interface can be used as attack vector

**Controls:**
- Seed/key authentication with ECDSA-based algorithm (AES-CMAC minimum)
- Rate limiting on failed security access attempts
- Diagnostic interface disabled during vehicle driving (speed > 5 km/h)
- Separate CAN channel for diagnostics (not shared with safety-critical signals)

---

## 17.4 Secure OTA

OTA is a major attack surface. Security measures:

| Measure | Description |
|---|---|
| Package signature | ECDSA-P256 signed by OEM |
| TLS 1.3 | All downloads encrypted |
| Certificate pinning | TCU only accepts OEM server cert |
| Mutual TLS | TCU authenticates to server |
| Anti-rollback | Version counter checked; older versions rejected |
| Secure storage | Downloaded packages stored in encrypted flash partition |

---

## 17.5 Network Security

**CAN bus:** No authentication natively. Mitigations:
- Message Authentication Code (MAC) via SecOC (AUTOSAR Security on-board Communication)
- SecOC appends a truncated MAC to each CAN message using a session key from HSM

**Ethernet:** TLS for external connections; VLAN segregation for internal.

**Firewall:** TCU/IVI have Linux netfilter/iptables rules:
```bash
# Allow only MQTT on port 8883 outbound
iptables -A OUTPUT -p tcp --dport 8883 -j ACCEPT
iptables -A OUTPUT -p tcp -j DROP  # block all other outbound TCP
```

---

## 17.6 IDS (Intrusion Detection System)

In-vehicle IDS monitors CAN/Ethernet traffic for anomalies:
- Unexpected message IDs
- Messages outside expected period
- Signal value outside plausible range
- Unusually high bus load

Example: IDS detects CAN injection attack (rapid identical frames) → logs event → alerts cloud backend → OEM investigates.

---

## 17.7 Integration of Security in ADAS / IVI / Cluster / TCU

| ECU | Security Measures |
|---|---|
| ADAS ECU | Secure boot, HSM, signed sensor calibration data |
| IVI (AAOS) | Android verified boot, TLS for cloud, app permissions |
| Cluster | Secure boot, no external interfaces (isolated) |
| TCU | All above + mutual TLS, certificate lifecycle, IDS |

---

## Summary

| Control | Purpose |
|---|---|
| Secure Boot | Prevent unauthorized firmware |
| HSM | Protect cryptographic keys |
| SecOC | CAN message authentication |
| TLS / mTLS | Secure network communication |
| OTA signing | Prevent malicious updates |
| IDS | Detect anomalous behavior |

---

*Next: [Part 18 — Functional Safety Integration](part-18-functional-safety.md)*
