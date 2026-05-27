# Module 18 — Interview Preparation

> 300 Q&A covering all domains | Level: All Levels

---

## Section 1: Fundamentals (Q1–Q40)

**Q1. What is the CIA Triad in automotive context? Give one example for each.**
> **Confidentiality**: VIN + location data must not be accessible to unauthorized parties (telematics).
> **Integrity**: AEB brake command CAN message must not be tampered with (SecOC protection).
> **Availability**: CAN bus must remain functional; a bus-off attack violates availability.

**Q2. What is the difference between Functional Safety (ISO 26262) and Cybersecurity (ISO 21434)?**
> ISO 26262 addresses **random hardware failures** and **systematic design errors** that cause unintended behavior. ISO 21434 addresses **intentional malicious attacks**. Both are needed: a safety system can be made unsafe by a cybersecurity attack.

**Q3. What is the automotive attack surface? Name 5 entry points.**
> OBD-II diagnostic port, Bluetooth (key fob, phone), Wi-Fi (infotainment), Cellular (telematics), USB (media, charging), V2X (DSRC/C-V2X), EV charging port (ISO 15118), TPMS sensors.

**Q4. What does UNECE R155 mandate?**
> Mandatory Cybersecurity Management System (CSMS) for all new vehicles sold in EU, Japan, and Korea from 2024. Requires TARA, security controls, incident management, OTA capability, and supplier CS requirements. Non-compliance = type approval denial.

**Q5. Define TARA (Threat Analysis and Risk Assessment).**
> TARA is the ISO 21434 §15 process of identifying assets, determining threats, rating impact (S/F/O/P) and feasibility, computing risk level, and selecting risk treatment (reduce/avoid/transfer/accept).

**Q6. What is a cybersecurity goal in ISO 21434?**
> A high-level security objective derived from TARA. Example: "The AEB brake command shall be authenticated and protected against replay attacks" (CAL 4, linked to TARA threat T-001).

**Q7. What are the 4 impact categories in ISO 21434?**
> **Safety** (S0–S3), **Financial** (F0–F3), **Operational** (O0–O3), **Privacy** (P0–P3).

**Q8. What is Cybersecurity Assurance Level (CAL)?**
> CAL 1–4 indicates the rigor required for cybersecurity activities. Derived from ISO 21434 risk matrix (impact × feasibility). CAL 4 = highest risk = most rigorous validation needed.

**Q9. What is the difference between vulnerability and threat in automotive context?**
> A **vulnerability** is a weakness (e.g., UDS security access without lockout). A **threat** is a potential event exploiting that weakness (e.g., attacker brute-forces seed-key to gain programming access).

**Q10. Name 3 automotive cybersecurity standards.**
> ISO/SAE 21434, UNECE R155, SAE J3061, ISO 15118, ETSI EN 303 645, IEC 62443.

**Q11. What is the E/E architecture evolution: Domain → Zonal → SDV?**
> **Domain**: one ECU per domain (powertrain, chassis, body). Multiple ECUs, complex wiring.
> **Zonal**: ECUs by vehicle zone (front-left, rear), fewer compute nodes with domain software.
> **SDV (Software-Defined Vehicle)**: central high-performance compute, virtualized domains, OTA all features.

**Q12. What is Secure Boot?**
> Hardware-rooted chain of trust: Boot ROM verifies bootloader signature → bootloader verifies OS/app → no unsigned code executes. Anti-rollback prevents downgrade to older vulnerable versions.

**Q13. What is an HSM in automotive context?**
> Hardware Security Module — dedicated secure processor on ECU (e.g., EVITA Light/Medium/Full) that stores keys, performs crypto operations (AES-CMAC, ECDSA), and provides a TRNG. Keys never leave the HSM.

**Q14. What is the STRIDE threat model?**
> Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege. Each category maps to a violated security property (Authentication, Integrity, Non-repudiation, Confidentiality, Availability, Authorization).

---

## Section 2: CAN Security (Q41–Q90)

**Q41. Describe a CAN replay attack.**
> Attacker records a valid CAN message (e.g., unlock command) and retransmits it later. No authentication on standard CAN allows any ECU to accept it. SecOC with freshness counter prevents replay.

**Q42. What is a CAN bus-off attack?**
> Attacker injects dominant bits at precise timing to cause error frames. ECU error counter (TEC) reaches 255 → enters bus-off state → stops transmitting → denial of service for that ECU.

**Q43. What is SecOC?**
> AUTOSAR Secure Onboard Communication. Adds CMAC-AES-128 authentication and freshness counter to CAN messages. Prevents spoofing, tampering, and replay attacks on CAN.

**Q44. What information is included in the SecOC PDU?**
> Authentic I-PDU (payload) + truncated freshness value (counter, typically 24 bits) + truncated MAC (typically 32 bits). Total overhead: ~7 bytes added to original payload.

**Q45. What is the maximum data length of a CAN 2.0 frame?**
> 8 bytes (64 bits). CAN FD extends this to 64 bytes.

**Q46. How does SecOC prevent replay attacks?**
> The freshness value (monotonic counter) is included in MAC computation. Receiver maintains last accepted counter; rejects any message with counter ≤ last accepted. Replayed frame has old counter → rejected.

**Q47. What is a DBC file?**
> CAN Database Container. Defines message IDs, signal names, bit positions, scaling factors, units, and value tables. Used by tools (CANalyzer, SavvyCAN, Python cantools) to decode raw CAN frames.

**Q48. What is SavvyCAN and when do you use it?**
> Open-source CAN analyzer GUI (cross-platform). Used for: live CAN capture, frame filtering, differential analysis (comparing before/after action), DBC import, fuzzing, replay. Connects via ELM327 or SocketCAN.

**Q49. What is the CAN error frame format?**
> Error frames: 6 dominant bits (active error flag) followed by 8 recessive bits (passive error flag + delimiter). Any ECU detecting an error transmits an error frame, destroying the current message.

**Q50. How would you identify a CAN injection attack on a live vehicle?**
> Look for: messages with unexpected IDs (not in DBC whitelist), messages at wrong cycle time, counter anomalies, CAN error frame rate increase, bus load spike. Use IDS rules in gateway ECU.

**Q51. What is J1939?**
> Heavy-duty vehicle CAN protocol (trucks, buses, off-highway). Uses 29-bit extended CAN IDs. PGN (Parameter Group Number) encodes message type. Priority field in bits 28-26. Source address in bits 7-0.

**Q52. What Python library do you use for CAN communication?**
> `python-can`. Supports SocketCAN (Linux), PCAN, Vector, Kvaser, ELM327 interfaces. Example: `can.interface.Bus("vcan0", bustype="socketcan")`.

**Q53. How does CAN arbitration work?**
> Lower arbitration ID wins. When multiple nodes transmit simultaneously, the one with more dominant (0) bits in the ID wins. Bitwise AND on the bus: any 0 bit makes the bit 0 on the bus.

**Q54. What is the difference between CAN 2.0A and 2.0B?**
> 2.0A: 11-bit identifier (SID). 2.0B: 29-bit identifier (EID). Automotive vehicles use both. J1939 uses 29-bit IDs.

---

## Section 3: UDS Diagnostics Security (Q91–Q130)

**Q91. What UDS service is used for security access?**
> Service 0x27 (Security Access). Request seed (sub-function 0x01) → compute key → send key (sub-function 0x02) → if key correct, access granted.

**Q92. What are the UDS NRCs for Security Access failures?**
> 0x35 = invalidKey, 0x36 = exceededNumberOfAttempts, 0x37 = requiredTimeDelayNotExpired, 0x24 = requestSequenceError (wrong session first).

**Q93. What is the UDS programming session sequence for ECU flash?**
> Default Session (0x01) → Extended Diagnostic Session (0x03) → Security Access level 3 (0x27 0x03/0x04) → Programming Session (0x02) → Security Access level 1 (0x27 0x01/0x02) → RequestDownload (0x34) → TransferData (0x36) → TransferExit (0x37) → Verify (0x31) → Reset (0x11).

**Q94. What attack can be performed if Security Access lockout is not implemented?**
> Brute force seed-key attack. Attacker requests seed, tries all possible keys, eventually finds the correct key. For a 4-byte key: 2^32 = ~4 billion attempts. With a weak algorithm (linear, XOR): pattern analysis may reduce this dramatically.

**Q95. What is seed-key key expansion?**
> The OEM-specific algorithm that derives the key from the seed. Commonly: XOR with constant, rotate, multiply. If algorithm is weak, attacker can reverse-engineer from firmware or test samples.

**Q96. What is a diagnostic DTC (Diagnostic Trouble Code)?**
> Fault code stored by an ECU when it detects an abnormal condition. Format: X (system) + digit + letter + 2 hex digits. Service 0x19 reads DTCs, 0x14 clears them. Clearing DTCs maliciously = destroying evidence.

**Q97. What is UDS testerPresent (0x3E) used for?**
> Keeps the diagnostic session alive. If ECU doesn't receive any message for the S3 timeout (default: 5 seconds), it returns to Default Session, losing Security Access. TesterPresent prevents timeout.

**Q98. What services are restricted to Programming Session?**
> RequestDownload (0x34), TransferData (0x36), RequestTransferExit (0x37), and specific RoutineControl (0x31) routines (erase flash, check programming dependencies).

**Q99. How do you detect unauthorized UDS access?**
> Monitor for: Programming Session activation outside service windows, Security Access after multiple failures, RDBI/WDBI for sensitive DIDs, IO Control activation, DTC clear without authorization.

**Q100. What is ISO-TP (ISO 15765-2)?**
> Transport protocol for UDS over CAN. Handles segmentation of messages > 8 bytes. Frame types: Single Frame (SF), First Frame (FF), Consecutive Frame (CF), Flow Control (FC).

---

## Section 4: ECU Security (Q131–Q170)

**Q131. What is JTAG and why is it a security risk?**
> JTAG (Joint Test Action Group) is a hardware debug interface (4-wire: TCK, TMS, TDI, TDO). Allows full memory read/write, breakpoints, and register access. An attacker with physical access can extract firmware and keys. Mitigated by OTP fusing to disable JTAG in production.

**Q132. What is EVITA?**
> E-safety Vehicle Intrusion Protected Applications. Defines three HSM profiles: Light (low-cost, AES-128, CMAC), Medium (AES + asymmetric, ECDSA), Full (full PKI, secure boot, key management).

**Q133. What is a side-channel attack?**
> Attacks that exploit physical information leakage rather than algorithmic weakness. Types: Simple Power Analysis (SPA), Differential Power Analysis (DPA), Timing attacks, Electromagnetic (EM) analysis, Fault injection (voltage/laser). Mitigated by: constant-time algorithms, power noise injection, shielding.

**Q134. How does Secure Boot prevent downgrade attacks?**
> Anti-rollback counter: each firmware version has a version number. HSM/OTP counter stores minimum accepted version. Bootloader rejects any firmware with version < stored counter. After successful boot of V2: counter set to 2, V1 is rejected forever.

**Q135. What is the purpose of MPU in an AUTOSAR ECU?**
> Memory Protection Unit enforces OS partition isolation. Each partition (application) gets its own memory region with specific permissions (read/write/execute). Prevents one partition from reading or corrupting another's data — isolation from compromised components.

**Q136. Explain the HSM key hierarchy.**
> Root Key (in OTP) → wraps Master Key (in HSM NvM) → derives Session Keys (per-session). Hierarchical derivation: keys at higher level protect lower-level keys. Root key never exported; all operations performed inside HSM.

**Q137. What is SecureFlash?**
> ECU flash update requires valid OEM signature + anti-rollback check before applying. Implemented via UDS programming sequence with cryptographic verification in the bootloader before activating new firmware.

**Q138. What is constant-time comparison and why is it needed?**
> Comparing secrets byte-by-byte and returning early on mismatch leaks timing information (attacker knows how many bytes matched). Constant-time comparison (e.g., CRYPTO_memcmp) always takes the same time regardless of match position.

**Q139. What does OTP fusing do to JTAG?**
> One-Time Programmable bits in the MCU permanently disable the JTAG interface. Once fused, JTAG commands are ignored by the hardware. Cannot be undone — irreversible production step.

**Q140. What is TPM and how does it differ from an automotive HSM?**
> TPM 2.0 is a standardized security chip (PC/server origin, now in some automotive). Provides PCR (Platform Configuration Registers) for integrity measurement, sealed storage, attestation. HSM in automotive is integrated into the main MCU die (more performance-optimized) while TPM is a separate chip.

---

## Section 5: Ethernet/SOME/IP Security (Q171–Q210)

**Q171. What is SOME/IP?**
> Scalable service-Oriented MiddlEwarE over IP. AUTOSAR's service communication protocol for Automotive Ethernet. Supports: request/response, fire-and-forget, and event notification. Service Discovery (SOME/IP-SD) broadcasts service availability.

**Q172. How can SOME/IP be attacked?**
> Service enumeration (discover all available services), method spoofing (forge service calls), subscription flooding (subscribe to all events → DoS), SD amplification attack, payload fuzzing.

**Q173. What is VLAN segmentation and why is it used in automotive Ethernet?**
> Virtual LAN separates traffic on same physical Ethernet. ADAS sensors on VLAN 10, infotainment on VLAN 20, gateway bridge. Prevents compromised infotainment from directly accessing ADAS services.

**Q174. What is DoIP (Diagnostics over IP)?**
> ISO 13400. UDS transport over Ethernet/UDP. Allows remote diagnostics (not just OBD-II). Activation type 0x01 allows routing without authentication → potential attack vector if not firewalled.

**Q175. What ports does SOME/IP typically use?**
> Service ports: defined per service in AUTOSAR configuration, typically >30000. SOME/IP-SD: UDP port 30490. DoIP: TCP/UDP port 13400.

**Q176. What is TSN and what security risks does it introduce?**
> Time-Sensitive Networking (IEEE 802.1Qbv/Qbu). Deterministic Ethernet for safety-critical ADAS. Risks: gPTP time synchronization spoofing (attacker manipulates time → affects TSN schedules), VLAN hopping (bypass stream reservation), traffic shaping abuse.

**Q177. What is DTLS and when is it used in automotive?**
> Datagram TLS — TLS adapted for UDP. Used when SOME/IP over UDP needs encryption. Provides same guarantees as TLS but handles UDP's unreliable delivery.

**Q178. What is the SOME/IP message format? Name the fields.**
> Service ID (2B), Method ID (2B), Length (4B), Client ID (2B), Session ID (2B), Protocol Version (1B), Interface Version (1B), Message Type (1B), Return Code (1B), Payload.

---

## Section 6: OTA & Cloud Security (Q211–Q240)

**Q211. What are the security requirements for automotive OTA?**
> Package integrity (hash), authentication (OEM signature), anti-rollback (version counter), encrypted transport (TLS 1.3), pre-condition checks (speed = 0), atomic update (all-or-nothing), incident logging.

**Q212. What is UNECE R156?**
> Software Update Management System (SUMS) regulation. Mandates OEM have documented OTA process, risk assessment for each update, pre-condition checks, ability to roll back, and update history log.

**Q213. How does an OTA rollback attack work?**
> Attacker intercepts OTA channel and delivers older (vulnerable) firmware version. Victim ECU downgrades to version with known CVE. Prevented by anti-rollback counter in bootloader.

**Q214. What is certificate pinning in vehicles?**
> Vehicle stores hash of OTA backend's TLS certificate (or CA public key). Only connects to server with matching certificate. Prevents MITM even with a rogue CA certificate.

**Q215. What is the attack against interrupted OTA updates?**
> Power loss during OTA leaves ECU in half-updated state → may not boot. Good OTA design: keep old firmware active until new firmware verified → only switch on successful verification.

**Q216. What OWASP categories apply to vehicle API security?**
> API1 (Broken Object Level Authorization), API2 (Broken Authentication), API3 (Broken Object Property Level Authorization). Vehicle APIs must require authentication + authorization for every request.

---

## Section 7: Pentest & Tools (Q241–Q270)

**Q241. What is the automotive pentest methodology?**
> Scope → Passive Recon → Active Recon → Vulnerability Analysis → Exploitation → Post-Exploitation → Reporting (7 phases, see Module 11).

**Q242. How do you extract firmware from an ECU?**
> Methods: OTA package (easiest), UART/serial console, JTAG (if not fused), flash chip desoldering (CH341A programmer), voltage glitch attack (last resort).

**Q243. What is binwalk used for?**
> Firmware analysis: identifies embedded file systems (SquashFS, JFFS2), compression (gzip, LZMA), and signatures. `binwalk -e firmware.bin` extracts all identified sections.

**Q244. How do you find hardcoded secrets in firmware?**
> `strings firmware.bin | grep -i "key\|pass\|secret"`. Look for high-entropy byte sequences (AES keys, private keys). Use YARA rules for pattern matching. Search for ASN.1/PEM certificate markers.

**Q245. What is the Jeep Cherokee vulnerability in simple terms?**
> Cellular-exposed web browser in IVI → exploited to gain IVI code execution → IVI had direct CAN bus access → arbitrary CAN injection from the internet. Root cause: no isolation between IVI and chassis CAN.

**Q246. What tools do you use for Bluetooth security testing?**
> hcitool (scan), gatttool (BLE GATT), Wireshark (BT HCI capture), Btlejuice (MITM proxy), Flipper Zero (sub-GHz + BT), HackRF (SDR), GATTacker.

**Q247. What is a CVSS score and how is it used in automotive?**
> Common Vulnerability Scoring System (0–10). Measures: Attack Vector, Complexity, Privileges, User Interaction, Scope, Confidentiality/Integrity/Availability Impact. In automotive: CVSS is supplemented with ISO 21434 safety impact rating (S0–S3).

**Q248. Name 3 CAN hacking tools.**
> SocketCAN (Linux kernel CAN stack), python-can (Python library), SavvyCAN (GUI), CANtact (hardware dongle), PCAN-USB (Peak PCAN adapter), Vector CANalyzer, Kvaser.

---

## Section 8: Standards & Compliance (Q271–Q290)

**Q271. What is the difference between ISO 21434 and ISO 26262?**
> 26262: Functional Safety, systematic errors + hardware failures, ASIL levels.
> 21434: Cybersecurity, intentional attacks, CAL levels.
> Both needed: complementary, not alternatives. Safety system can be compromised by security attack.

**Q272. What is ASPICE CL2 vs CL3?**
> CL2: Managed — work is planned and tracked, inputs/outputs defined.
> CL3: Established — standard processes defined at organization level, all projects tailored from standard.
> Automotive premium OEMs typically require CL3 from Tier-1.

**Q273. How does UNECE R155 relate to CSMS?**
> R155 mandates that OEM has a certified CSMS. ISO 21434 defines how to implement a CSMS. Technical service (TÜV, SGS, etc.) audits the CSMS and issues a certificate valid for 3 years.

**Q274. What is the 72-hour rule in R155?**
> Acute cybersecurity incidents with potential safety impact must be reported to the national authority within 72 hours. Similar to GDPR's 72-hour breach notification requirement.

**Q275. What is IEC 62443 used for in automotive?**
> Industrial security standard applied to EV charging infrastructure (EVSE), smart factory (vehicle manufacturing), V2G grid interfaces. Defines Security Levels SL1–SL4.

---

## Section 9: Career & Scenario Questions (Q291–Q300)

**Q291. You've joined a new automotive OEM as a cybersecurity engineer. What do you do in Week 1?**
> Understand the vehicle program portfolio and current phase (development vs production). Review existing TARA documents. Identify which ECUs have cybersecurity goals. Understand the toolchain (AUTOSAR configurator, CANalyzer, test bench setup). Meet the safety and quality teams (ISO 21434 + 26262 intersection).

**Q292. A penetration tester reports: "UDS Security Access does not implement lockout." What's your response?**
> Classify severity: HIGH (enables brute force of seed-key → unauthorized flash access). Immediate workaround: monitoring/alerting at VSOC level. Permanent fix: configure DCM with NumAttDelay=3 and DelayTime=10000ms. Root cause: DCM configuration not reviewed against security requirements. Add to TARA risk register.

**Q293. An OEM asks you to review their CAN architecture for cybersecurity. What do you check?**
> SecOC deployment on safety-critical messages, gateway firewall rules, CAN bus segmentation, whitelist of expected message IDs and DLCs, cycle time monitoring (IDS rules), access to OBD port (authentication).

**Q294. How would you explain automotive cybersecurity to a non-technical executive?**
> "Modern cars are computers on wheels. Each ECU is like a server. If an attacker can access one (through Wi-Fi, Bluetooth, OTA), they could potentially control the car. We need to protect each layer — just like corporate IT security — but with the added requirement that failures cannot injure people."

**Q295. What's the hardest cybersecurity challenge in automotive today?**
> Post-quantum cryptography transition: current ECC (P-256, P-384) will be broken by quantum computers. Automotive ECU crypto must be replaced before ~2035 (estimated Q-Day). Constraint: ECUs designed today will be on roads until 2040+. Need hybrid classical+PQC algorithms on resource-constrained MCUs.

**Q296. How do you prioritize which CAN messages need SecOC?**
> Safety-critical first: AEB, EPS, brakes, throttle. Risk-based (TARA): messages where tampering leads to S3 safety impact = mandatory SecOC. Cost constraint: each SecOC message adds 7+ bytes overhead; assess if CAN utilization allows it. Result: protect highest-impact signals, tolerate risk on non-safety signals.

**Q297. You discover a critical vulnerability in production vehicles. What's the process?**
> 1) Confirm and classify severity. 2) Inform CISO + safety team. 3) Assess safety risk: do vehicles need to be recalled immediately? 4) Develop OTA patch. 5) Test patch. 6) Deploy to fleet in waves (5% → 25% → 100%). 7) Notify regulators per R155. 8) Conduct post-incident review. 9) Update TARA.

**Q298. What's the difference between penetration testing and vulnerability assessment?**
> Vulnerability assessment: identifies and lists known vulnerabilities (scanning tools, CVE databases). No active exploitation.
> Penetration testing: actively exploits vulnerabilities to demonstrate impact. Proves what an attacker can achieve. More invasive, more authoritative.

**Q299. Can you describe your experience with automotive security tools?**
> [Tailor to your own experience. Mention: CANalyzer/SavvyCAN for CAN analysis, PCAN/SocketCAN for hardware, Wireshark for Ethernet, Python with python-can/udsoncan/cantools for automation, Ghidra/binwalk for firmware analysis, CAPL for test automation in CANoe.]

**Q300. Where do you see automotive cybersecurity in 5 years?**
> Post-quantum cryptography adoption (NIST FIPS 204/205 algorithms). Zero-trust architecture in vehicle networks (every ECU authenticates every message). AI-based IDS (behavioral anomaly detection vs static rules). V2X security maturation (V2G, V2I, V2P with PKI). Regulatory expansion: US NHTSA cybersecurity rule expected. Software-Defined Vehicle security: securing hypervisors and containers in central compute.

---

## Quick Reference Card

```
MOST COMMON INTERVIEW TOPICS:

Fundamentals:    CIA, TARA, ISO 21434, STRIDE, CAL, UNECE R155
CAN Security:    SecOC, freshness, bus-off, injection, whitelist
UDS:             Security Access 0x27, sessions, NRCs, programming flow
ECU:             Secure Boot, HSM, JTAG, side-channel, MPU
Ethernet/SOME/IP: Service discovery, spoofing, VLAN, DoIP, TSN
OTA:             Signing, rollback, TLS, pre-conditions, R156
Pentest:         Methodology, firmware extraction, Ghidra, seed-key RE
Real Attacks:    Jeep Cherokee (IVI-CAN bridge), Tesla (browser→CAN)
Tools:           python-can, cantools, udsoncan, scapy, binwalk, Ghidra
AUTOSAR:         SecOC, CSM, DCM, ara::iam, E2E vs SecOC
```

**Next Module**: [19 — Career Roadmap](19_career_roadmap.md)
