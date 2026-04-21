# Certification Documentation & Conformity of Production
## Technical File | E-Mark | COP | Approval Extensions | Multi-Market Strategy

---

## 1. The Technical File (Type Approval Dossier)

The **Technical File** is the complete documentation package submitted to an Approval Authority (AA) or Technical Service to obtain a Type Approval Certificate (TAC). It must comprehensively describe the product and prove compliance.

### 1.1 Structure of a Technical File

A typical Technical File for an automotive lamp (e.g., R112 headlamp) contains:

```
Technical File
├── Part A: Information Document (Annex I of Regulation)
│   ├── Manufacturer name and address
│   ├── Product description (lamp type, category, light source type)
│   ├── Reference to drawings (assembly, optical section, dimensions)
│   ├── Material declarations (lens, housing, reflector)
│   ├── Light source reference (bulb type or LED module part number)
│   ├── Supply voltage
│   └── Variants and versions list
│
├── Part B: Test Reports
│   ├── Photometric test report (goniometer results — R112 test points)
│   ├── Colour measurement report (CIE x,y coordinates)
│   ├── Filament/LED life test report (if required)
│   ├── Vibration test report
│   ├── Thermal test report
│   └── EMC test report (R10, if applicable)
│
├── Part C: Drawings and Specifications
│   ├── Engineering drawings (CAD cross-sections, dimensions)
│   ├── Illuminated area drawings (reference to E-mark position)
│   ├── Lens tooling drawings (if custom optics)
│   └── Wiring diagram (for AFS, LED driver)
│
├── Part D: Conformity of Production (COP) Plan
│   ├── Quality control procedure reference
│   ├── Sampling frequency and sample size
│   ├── COP test methods and acceptance criteria
│   └── Production process description
│
└── Part E: Manufacturer Declaration
    ├── Declaration that samples submitted are representative
    ├── Confirmation of COP plan implementation
    └── Authorised signatory
```

---

### 1.2 Information Document vs. Information Package

| Document | Contents | Purpose |
|---|---|---|
| **Information Document** | Published format (Annex I) — publicly accessible | Minimum disclosure to AA |
| **Information Package** | Full detailed Technical File | Submitted to TA authority — may be confidential |
| **Type Approval Certificate** | Issued by AA | Legal proof of approval |
| **Communication** | Standard format per regulation | Formal approval record |

---

## 2. E-Mark Format and Country Codes

### 2.1 E-Mark Marking Requirements

Every unit of an approved component must bear the **approval mark** physically on the product (engraved, embossed, or affixed as a durable label).

**Standard format:**

```
Circle containing:  E  4
                    ★
                   R112
                    ★
                  00001
                   A/B
```

Or in linear format:
```
⊕4★R112★00001A/B
```

**Decoding the mark:**
| Element | Meaning |
|---|---|
| Circle | Indicates type approval mark |
| E (capital) | ECE regulation (1958 Agreement) |
| 4 | Country code of Approval Authority that granted approval |
| ★ | Separator |
| R112 | Regulation number |
| ★ | Separator |
| 00001 | Approval number (assigned by AA) |
| A/B | Function code (A = low beam, B = high beam, A/B = both) |

### 2.2 Country Codes for E-Mark

| Code | Country | Authority |
|---|---|---|
| E1 | Germany | KBA (Kraftfahrt-Bundesamt) |
| E2 | France | UTAC / DREAL |
| E3 | Italy | UNRAE |
| E4 | Netherlands | RDW |
| E5 | Sweden | Transportstyrelsen |
| E6 | Belgium | DIV |
| E9 | Spain | DGMT |
| E11 | United Kingdom | VCA (pre-Brexit) |
| E13 | Luxembourg | SNCT |
| E22 | Russia | Rosstandart |
| E43 | Japan | MLIT |
| E45 | Australia | DIRD |

### 2.3 e-Mark vs E-Mark (Important Distinction)

| Mark | Agreement | Authority | Used On |
|---|---|---|---|
| **E-mark** (capital E in circle) | 1958 UNECE Agreement | National authority | Components approved under UN Regulations |
| **e-mark** (lowercase e in rectangle) | EU Directive/Regulation | EU member state authority | Components under EU type approval regulations |

> In practice, for most lighting components, the E-mark (capital) under UN Regulations is more commonly used globally. The e-mark (lowercase) is an EU-internal variant.

---

## 3. Type Approval Certificate (TAC)

### 3.1 What the TAC Contains

A Type Approval Certificate is a formal document issued by the Approval Authority that includes:

- Name and address of manufacturer
- Regulation number and amendment series (e.g., UN R112–02)
- Date of approval
- Approval number
- Description of approved type
- List of variants and versions (each variant is a configuration)
- Conditions of approval (if any)
- Reference to test report number
- Reference to information document
- Name and signature of approving authority officer

### 3.2 Variants and Versions

| Term | Definition | Example |
|---|---|---|
| **Type** | Base product family | R112 headlamp for passenger car |
| **Variant** | Different configuration same approval | Variant 1: Halogen H7, Variant 2: LED module |
| **Version** | Different specification within variant | Version A: Black housing, Version B: Silver housing |

**Adding a variant:** Requires extension of existing TA (separate certificate but same approval base)
**New version (cosmetic only):** May be covered without re-test depending on regulation

---

## 4. Conformity of Production (COP)

COP is the mechanism ensuring that every unit coming off the production line continues to meet the requirements of the type approval. It is a **legal obligation** of the manufacturer.

### 4.1 COP Testing Requirements

**Sampling rate:** Typically agreed between AA and manufacturer. Common example:
- 3 production samples per year per approved type for photometric tests
- Samples must be from actual production (not special builds)

**Test scope for COP (R112 example):**
- Full photometric scan at R112 test points
- Colour measurement
- Marking check (E-mark present and correct)
- Visual inspection vs approved drawings

### 4.2 COP Tolerance Bands

Production samples are tested against relaxed tolerance limits (not the exact regulation minimum):

| Measurement | Design Limit | COP Acceptance Band |
|---|---|---|
| Photometric intensity (minimum) | ≥ minimum specified in regulation | ≥ 80% of regulation minimum (–20% tolerance) |
| Photometric intensity (maximum) | ≤ maximum specified | ≤ 120% of regulation maximum (+20% tolerance) |
| Colour coordinates | Within CIE boundary | Within CIE boundary (no relaxation) |
| Flash frequency | 60–120 /min | 60–120 /min (no relaxation on flash) |

> **Practical implication:** If R7 requires minimum 60 cd for stop lamp at HV, the COP acceptance is ≥ 48 cd. If a production sample measures 45 cd, it FAILS COP.

### 4.3 COP Failure Procedure

**Step 1 — Immediate investigation:**
- Root cause analysis (measurement error? production variance? tooling change?)
- Check if sample was representative (no pre-selection)

**Step 2 — Containment:**
- Put suspect production lots on hold
- Do not ship until investigation complete

**Step 3 — Response to Approval Authority:**
- Mandatory reporting within defined timeframe (varies by AA — typically 30 days)
- Submit corrective action plan

**Step 4 — Corrective action:**
- Process change, tooling correction, LED bin tightening
- Re-sample and re-test

**Step 5 — Escalation:**
- If COP cannot be restored: AA may suspend or withdraw type approval
- Product recall may be required if non-conforming units were delivered

### 4.4 COP Records Retention

All COP records must be retained for minimum 10 years (typical requirement):
- Sample selection records (serial numbers, production date, lot identification)
- Test results (raw data + processed results)
- Calibration certificates for test equipment
- Corrective action records

---

## 5. Type Approval Extensions

### 5.1 When an Extension is Needed

An extension to an existing type approval is required when:
- Adding a new variant (e.g., adding an LED version to a previously halogen-only approval)
- Changing the light source type (e.g., H7 to different base type)
- Modifying the optical design (reflector or lens changes affecting photometry)
- Changing housing material if it affects heat dissipation
- Adding a new vehicle application with different aim/installation

### 5.2 When an Extension is NOT Needed

Minor changes that do NOT require extension (check regulation Annex for specifics):
- Colour change of non-illuminated parts
- Supplier change for mechanical components (same drawing)
- Wire gauge change (same routing)

### 5.3 Extension vs New Approval

| Situation | Action |
|---|---|
| Minor variant within same type | Extension — same approval number, new letter suffix (e.g., 00001/01) |
| Significant design change — different optical design | New approval — new application and test |
| New regulation applicable (old not accepted) | New approval under new regulation |
| Product for new market (different TA authority) | New approval in that market's authority |

---

## 6. Multi-Market Type Approval Strategy

For global product launch, manufacturers typically need approvals in multiple regulatory zones:

### 6.1 Common Markets and Approval Types

| Market | Regulatory Framework | Authority | Mark |
|---|---|---|---|
| EU 27 member states | UN Regulations (R112, R7, etc.) | National AA (e.g., KBA, RDW) | E-mark |
| UK (post-Brexit) | UK Regulations (GB versions of UN Regs) | VCA | UK mark |
| Russia, CIS | UN Regulations | Russian FAA | E22 mark |
| Japan | TRIAS (Japan) | MLIT | Japan mark |
| Australia | ADRs (Australian Design Rules) | VASS | ADR mark |
| India | AIS standards (aligned to ECE) | ARAI/NATRIP | CMVR mark |
| USA | FMVSS 108 | NHTSA | Self-cert (DOT) |
| China | GB standards | CNCA | CCC mark |

### 6.2 Mutual Recognition Agreements

Under the **1958 Agreement** (UN ECE), contracting parties mutually recognise each other's type approvals. A lamp approved by KBA (Germany) under R112 is automatically valid in all 60+ contracting party countries **without re-testing**.

This is the major advantage of UN Regulation approval over country-specific standards.

### 6.3 Managing Dual Certification (ECE + FMVSS 108)

Challenges:
- FMVSS 108 test points differ from R112 (no B50L concept in FMVSS)
- FMVSS allows different beam patterns (sealed beam, etc.)
- Colour standards differ: USA allows red rear indicators, ECE requires amber

Strategy:
- Design optical prescription to meet BOTH photometric targets simultaneously
- If not possible: separate optical variants for ECE and FMVSS markets
- Run ECE goniophotometer test AND FMVSS photometric test from same sample
- Document both test results — maintain separate Technical Files for each market

---

## 7. COP Audit — What to Expect

### 7.1 COP Audit Types

| Type | Trigger | Who Conducts |
|---|---|---|
| **Initial COP assessment** | Part of first type approval | Approval Authority or Technical Service |
| **Routine COP audit** | Annual or biennial | Approval Authority or TS |
| **Reactive COP audit** | Customer complaint, market complaint, COP test failure | Approval Authority |
| **Extended COP** | COP failure — intensified program | Manufacturer required to test more samples |

### 7.2 Typical COP Audit Agenda

**Day 1: Documentation review**
- Quality management system review (IATF 16949 / ISO 9001)
- COP plan review (sampling method, test frequency, equipment calibration)
- Previous COP records (3–5 years)
- Product change log (ECOs / PCNs — Product Change Notifications)
- Traceability records

**Day 2: Production floor audit**
- Raw material incoming inspection records
- LED bin incoming check records
- assembly process control
- End-of-line test records (100% functional test, photometric sampling)
- Non-conforming product handling (quarantine, MRB process)
- COP sample storage

**Day 3: Witness testing**
- Auditor witnesses selection and testing of 2–3 production samples
- Test performed at manufacturer's lab or Technical Service
- Results reviewed against COP acceptance criteria

### 7.3 Common COP Audit Findings

| Finding | Severity |
|---|---|
| COP test records incomplete or missing | Major |
| Test equipment not calibrated | Major |
| Production samples pre-selected (cherry picking) | Critical — approval suspension |
| COP test results at limit with no process control | Minor |
| Product change made without TA extension | Critical |
| COP plan not matching actual practice | Minor |

---

## 8. ARAI Type Approval Process (India Specific)

### 8.1 Steps for AIS Approval at ARAI

1. **Application:** Submit online application with product details, fee payment
2. **Document submission:** Technical file, drawings, information document (AIS format)
3. **Test booking:** Agree test schedule with ARAI testing department
4. **Sample submission:** Submit 3 samples (1 for testing, 1 for confirmation, 1 retained)
5. **Type test:** ARAI performs all tests per AIS standard (photometric, colour, vibration, etc.)
6. **Test report:** ARAI approves and issues test report
7. **Certificate:** AIS Type Approval Certificate issued if tests pass
8. **Quarterly report:** COP quarterly report submitted to ARAI

**Timeline:** Typically 3–6 months from application to certificate

**Key difference from ECE:** ARAI is both Technical Service AND Approval Authority — no separation of roles.

---

## 9. Technical Service Accreditation

Technical Services that witness type tests must be accredited:

| Standard | Scope |
|---|---|
| **ISO/IEC 17025** | Testing laboratories — competence for specific tests |
| **ISO/IEC 17020** | Inspection bodies — for field inspection activities |
| **ILAC MRA** | Mutual Recognition Arrangement — international acceptance of accreditation |

### Regulation-Specific Designation
A laboratory must specifically be designated (by the AA) for each regulation it covers:
- Designated for R112 ≠ automatically designated for R7
- Manufacturer must use a TS designated for the specific regulation being applied for

---

## 10. Documentation Checklist for Submission

Use this checklist before submitting to an Approval Authority:

| # | Document | Status |
|---|---|---|
| 1 | Completed Information Document (Annex I format) | ☐ |
| 2 | Photometric test report (signed, calibration cert attached) | ☐ |
| 3 | Colour measurement report | ☐ |
| 4 | Beam pattern photograph (for R112) | ☐ |
| 5 | Environmental test reports (vibration, thermal, IP) | ☐ |
| 6 | EMC test report (if LED) | ☐ |
| 7 | COP plan | ☐ |
| 8 | Engineering drawings (stamped/approved) | ☐ |
| 9 | Manufacturer declaration | ☐ |
| 10 | Application fee payment confirmation | ☐ |
| 11 | Previous approval certificate (if extension) | ☐ |
| 12 | Cover letter referencing regulation and amendment series | ☐ |

---

*File: 04_certification_documentation.md | automotive_homologation series*
