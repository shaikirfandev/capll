# Part 16 — Automotive Standards

---

## 16.1 ISO 26262 — Functional Safety

**What:** Road vehicle functional safety standard.
**Why:** Ensures systematic development process to prevent safety hazards.
**How it affects integration:**
- Every ECU assigned an ASIL level (A/B/C/D or QM)
- Integration engineer must trace safety requirements to test cases
- Safety mechanisms (watchdog, redundancy, plausibility checks) must be verified
- Safety analysis (FMEA, FTA) must cover integration interfaces

**Key ASIL levels for common ECUs:**

| ECU | Typical ASIL |
|---|---|
| AEB brake actuator | ASIL-D |
| Steering angle input | ASIL-C |
| Cluster telltale display | ASIL-B |
| Infotainment | QM |
| TCU | QM / ASIL-A |

---

## 16.2 Automotive SPICE (ASPICE)

**What:** Software process assessment model (based on ISO/IEC 15504).
**Why:** OEMs require suppliers to demonstrate process maturity (typically CL2 or CL3).
**How it affects integration:**
- Integration process must produce defined work products
- Evidence of integration tests, reviews, traceability required
- Common ASPICE processes for integration engineers:
  - SWE.4 Software Unit Verification
  - SWE.5 Software Integration and Integration Test
  - SWE.6 Software Qualification Test

---

## 16.3 ISO/SAE 21434 — Cybersecurity

**What:** Automotive cybersecurity engineering standard.
**Why:** Defines TARA (Threat Analysis and Risk Assessment) methodology.
**How it affects integration:**
- Integration must implement security controls (secure boot, encryption, HSM)
- CAN/Ethernet interfaces must be assessed for attack surfaces
- OTA update pipeline must be secured end-to-end
- Penetration testing required for connected ECUs (TCU, IVI)

---

## 16.4 UNECE R155 / R156

**R155:** Vehicle cybersecurity regulation (mandates ISO/SAE 21434-aligned CSMS).
**R156:** Software update regulation (mandates SUMS — Software Update Management System).

Required for type approval in EU, Japan, South Korea (since 2022 for new types).

**Integration impact:** Every software update process must comply with R156:
- Version control, rollback, activation validation
- OTA process must be documented and audited

---

## 16.5 ISO 14229 — UDS (Unified Diagnostic Services)

**What:** Defines all UDS diagnostic services.
**Integration impact:** Every diagnostic service implemented in DCM must match the spec.

---

## 16.6 ISO 13400 — DoIP

**What:** Diagnostics over Ethernet (IP-based transport for UDS).
**Integration impact:** Gateway and ECUs must support DoIP for Ethernet-based diagnostics and flashing.

---

## 16.7 ISO 11898 — CAN

**What:** CAN physical and data link layer.
**Integration impact:** Bit timing, transceiver selection, error handling must comply.

---

## 16.8 AUTOSAR Standard

**What:** Software architecture standard (Classic and Adaptive).
**Integration impact:** BSW module configuration, API compliance, ARXML must follow AUTOSAR spec.

---

## 16.9 MISRA C/C++

**What:** Coding guidelines for safety-critical C/C++ (MISRA C:2012, MISRA C++:2023).
**Integration impact:**
- Static analysis must report MISRA compliance
- All mandatory rules must be addressed; deviations documented
- Key rules: no dynamic memory allocation in Classic AUTOSAR, no implicit conversions

---

## Summary Table

| Standard | Affects Integration How |
|---|---|
| ISO 26262 | ASIL assignment, safety mechanism verification, traceability |
| ASPICE | Process maturity, work products, evidence |
| ISO/SAE 21434 | Security controls, TARA, penetration testing |
| UNECE R155/156 | OTA and cybersecurity compliance for type approval |
| ISO 14229 | UDS service implementation and verification |
| ISO 13400 | DoIP integration and testing |
| AUTOSAR | BSW configuration, ARXML compliance |
| MISRA C/C++ | Static analysis compliance |

---

*Next: [Part 17 — Cybersecurity Integration](part-17-cybersecurity.md)*
