# Regulatory Standards — Complete Reference Guide

## 1. ISO 13485:2016 — Quality Management Systems for Medical Devices

### What It Is
ISO 13485 is the **international standard for a Quality Management System (QMS)** specific to organisations involved in the design, production, installation, and servicing of medical devices and related services. It is the prerequisite for CE marking and strongly aligned with FDA 21 CFR Part 820.

### Key Differences from ISO 9001
| Aspect | ISO 9001:2015 | ISO 13485:2016 |
|--------|--------------|----------------|
| Focus | Customer satisfaction | Regulatory compliance + safety |
| Risk-based thinking | Implicit | Explicit, structured per ISO 14971 |
| Change control | Flexible | Formal documented procedure required |
| Customer feedback | General | Post-Market Surveillance mandatory |
| Validation | Not mandated | Mandatory for software, processes |

### Key Clauses You Must Know

**Clause 4 — Context of the Organisation**
- 4.1: Understand organisation and its context (regulatory requirements)
- 4.2: Scope of QMS including applicable regulatory requirements
- 4.2.3: Medical Device File (technical file) — must be maintained

**Clause 7 — Support**
- 7.5: Documented information (records and documents control)
  - Document control: approval, review, version control, distribution
  - Record control: retention periods, accessibility, legibility

**Clause 8 — Operation (Most Tested)**
- 8.1: Operational planning and control
  - Risk management per ISO 14971 integrated at every stage
- 8.2: Requirements for products and services
  - 8.2.1: Customer communication
  - 8.2.2: Determine requirements (regulatory, intended use, safety)
  - 8.2.3: Review requirements before commitment
- 8.3: **Design and Development** (core for V&V engineers)
  - 8.3.2: Planning — stages, reviews, responsibilities, DHF
  - 8.3.3: Design inputs — functional, performance, regulatory, usability
  - 8.3.4: Design controls — reviews, verification, validation
  - 8.3.5: Design outputs — specifications, drawings, labelling
  - 8.3.6: Design review — systematic examination at defined stages
  - 8.3.7: Design verification — confirms output meets input
  - 8.3.8: Design validation — confirms device meets intended use
  - 8.3.9: Design transfer — from development to manufacturing
  - 8.3.10: Design changes — change control, re-verification/re-validation
  - 8.3.11: Design history file — complete development record
- 8.4: Control of externally provided processes
- 8.5: Production and service provision
  - 8.5.3: Identification and traceability (UDI)
  - 8.5.4: Preservation
- 8.6: Release of products — inspection and test
- 8.7: Control of nonconforming outputs (NCR process)

**Clause 9 — Performance Evaluation**
- 9.1: Monitoring, measurement, analysis (complaint handling, PMS)
- 9.2: Internal audit (audit programme, competency of auditors)
- 9.3: Management review (inputs: audit results, complaints, CAPA status)

**Clause 10 — Improvement**
- 10.2: Nonconformity and corrective action (CAPA)
- 10.3: Continual improvement

### Design History File (DHF) — What It Contains
The DHF is the regulatory record proving your design controls were followed:

```
DHF Contents:
├── Design and Development Plan
├── Design Inputs (User Needs → Design Requirements)
├── Design Outputs (drawings, specs, software)
├── Design Review Records (meeting minutes, action items)
├── Design Verification Records (test reports, analysis)
├── Design Validation Records (clinical, usability studies)
├── Risk Management File (ISO 14971)
├── Design Transfer Records
├── Design Change Records
└── Regulatory Submission Documents
```

### Device Master Record (DMR) — What It Contains
The DMR is the recipe for manufacturing a device:

```
DMR Contents:
├── Device Specifications (drawings, dimensions, materials)
├── Production Process Specifications (work instructions, SOPs)
├── Quality Assurance Procedures (inspection criteria, test methods)
├── Packaging and Labelling Specifications
├── Installation, Maintenance and Servicing Procedures
└── Software Version Baseline
```

### Interview Q: "How do you ensure DHF integrity?"
> "I establish a document matrix at project kickoff mapping each DHF element to its owner, revision, and approval status. I use the PLM system (e.g., Windchill or Teamcenter) to enforce version control and approval workflows. At each design gate review, I run a DHF completeness checklist — verifying that design inputs trace to verification results, risk controls trace to V&V evidence, and all reviews are signed. Before product release, I conduct a final DHF audit against the clause 8.3.11 checklist and FDA Design Controls guidance."

---

## 2. ISO 14971:2019 — Risk Management for Medical Devices

### The Risk Management Process (5-Step Framework)

```
Step 1: RISK MANAGEMENT PLANNING
        └─ Define scope, responsibilities, risk criteria, acceptable risk levels

Step 2: RISK ANALYSIS
        ├─ Hazard Identification (FMEA, FTA, PHA, HAZOP)
        ├─ Estimate Probability of Harm (P1 × P2)
        └─ Estimate Severity of Harm

Step 3: RISK EVALUATION
        ├─ Compare estimated risk vs acceptance criteria
        └─ Determine if risk reduction is required

Step 4: RISK CONTROL
        ├─ Option 1: Inherently safe design
        ├─ Option 2: Protective measures (guards, alarms)
        └─ Option 3: Information for safety (labelling, IFU)

Step 5: RESIDUAL RISK EVALUATION
        ├─ Residual risk of individual measures
        ├─ Overall residual risk
        └─ Benefit-risk analysis if residual risk is not ALARP
```

### Risk Acceptability Matrix (Example)
```
Severity →   Negligible  Minor  Serious  Critical  Catastrophic
Probability ↓
Frequent        Low      Medium  High     High       High
Probable        Low      Medium  Medium   High       High
Occasional      Low       Low    Medium   High       High
Remote         Acceptable Low    Low     Medium      High
Improbable     Acceptable Acc.   Low      Low       Medium
```

### Key Terminology Changes (2007 → 2019)
| ISO 14971:2007 | ISO 14971:2019 |
|----------------|----------------|
| Reasonably foreseeable misuse | Reasonably foreseeable misuse (same) |
| ALARP | Overall residual risk acceptable |
| Risk-benefit analysis | Benefit-risk determination |
| Harm probability = P1 × P2 | Probability of harm = P1 × P2 (clarified) |

### FMEA vs FTA
| Aspect | FMEA (Bottom-up) | FTA (Top-down) |
|--------|-----------------|----------------|
| Starting point | Component failure | Undesired top event |
| Direction | Effects propagate up | Causes traced down |
| Best for | Identifying failure modes | Proving safety case |
| Output | Risk priority number (RPN) | Cut sets, probability |
| Standard | IEC 60812 | IEC 61025 |

### Risk File Structure
```
Risk Management File:
├── Risk Management Plan (scope, criteria, team)
├── Risk Analysis Report (FMEA, FTA, PHA results)
├── Risk Evaluation Report (risks vs acceptance criteria)
├── Risk Control Measures (design changes, labelling)
├── Residual Risk Report
├── Benefit-Risk Analysis (if needed)
└── Risk Management Report (summary, declaration of acceptability)
```

---

## 3. 21 CFR Part 11 — Electronic Records and Electronic Signatures

### Applicability
FDA regulation requiring that electronic records and signatures used in **FDA-regulated industries** (medical devices, pharma, biotech) are **trustworthy, reliable, and equivalent to paper records**.

### Two Main Categories

**3.1 Closed Systems** (org controls access)
- Access controls: unique user IDs + passwords
- Audit trails: computer-generated, time-stamped, operator-linked
- Record protection: archiving, backup, disaster recovery
- Audit trail review: part of regulated operations

**3.2 Open Systems** (external network transmission)
- All closed system requirements PLUS
- Document encryption
- Digital signatures with PKI

### Key Requirements for System Validation

```
Part 11 Validation Checklist:
□ System validation (IQ/OQ/PQ completed)
□ Audit trail enabled and cannot be disabled by users
□ Audit trail captures: who, what, when (timestamp), original & new value
□ Unique user IDs — no shared accounts
□ Password policies enforced (complexity, expiry, lockout)
□ Electronic signatures are permanently linked to their records
□ System-generated date/time stamps (not user-modifiable)
□ Authority checks — users can only perform authorised actions
□ Operational system checks — enforce proper sequence of steps
□ SOPs for system use, training records maintained
```

### Electronic Signatures Requirements (§11.50, §11.70, §11.100)
- Must contain: printed name, date/time, meaning of signature
- Must be linked to their electronic record — cannot be excised or transferred
- First use requires two components (e.g., username + password)
- Subsequent uses can use one component IF within a continuous working session
- Non-biometric signatures must be **certified to FDA** (§11.100(c))

### Common Part 11 Audit Findings
1. Audit trails disabled or not reviewed
2. Shared user accounts (no individual accountability)
3. System time not synchronised to a trusted source
4. Insufficient backup/recovery testing
5. User access not removed promptly on termination
6. No SOP for system administration

---

## 4. EU MDR 2017/745 — Medical Device Regulation

### Classification Rules (MDR Annex VIII)
```
Class I    → Low risk (e.g., bandages, crutches, non-sterile scalpels)
Class IIa  → Medium risk (e.g., hearing aids, dental fillings)
Class IIb  → Medium-high risk (e.g., ventilators, bone screws)
Class III  → High risk (e.g., pacemakers, coronary stents, implantable)

Rule 11:   Software — standalone software that diagnoses/monitors → IIa or higher
Rule 22:   Active therapeutic devices using ionising radiation → IIb/III
```

### Key Changes from MDD to MDR
| Area | MDD 93/42/EEC | MDR 2017/745 |
|------|--------------|--------------|
| Clinical evidence | Clinical data acceptable | Clinical investigations often required |
| PMCF | Not mandatory | Mandatory for all classes |
| UDI | Not required | Mandatory (Eudamed) |
| Software classification | Less clear | Rule 11 clarified — most diagnostic SaMD = IIa+ |
| Notified body oversight | Lighter | Annual unannounced audits for IIb/III |
| Implant card | Not required | Mandatory for implantable devices |
| SSCP | Not required | Summary of Safety and Clinical Performance (Class IIb/III) |

### Technical Documentation (Annex II & III)
```
Technical Documentation (Annex II):
├── Device description and specification (variants, accessories)
├── Information supplied by manufacturer (labelling, IFU)
├── Design and manufacturing information
│   ├── Design stages (drawings, process flows)
│   └── Manufacturing sites, subcontractors
├── General safety and performance requirements (Annex I GSPR)
│   └── Each GSPR → applicable standard → verification/validation evidence
├── Benefit-risk analysis and risk management
├── Product verification and validation
│   ├── Pre-clinical tests
│   ├── Clinical evaluation (Annex XIV)
│   └── Usability (IEC 62366)
└── Post-market surveillance system (Annex III)
```

### General Safety and Performance Requirements (GSPR — Annex I)
Engineers must create an **GSPR checklist** — for each requirement:
1. Is it applicable? If not, justify why
2. What standard was applied (harmonised standard preferred)
3. What test/verification evidence demonstrates conformity
4. Where is the evidence in the technical file?

---

## 5. IEC 60601-1 — Medical Electrical Equipment Safety

### Structure: 1 Collateral + Many Particular Standards
```
IEC 60601-1:2005+AMD1:2012+AMD2:2020 (General requirements)
│
├── IEC 60601-1-2: EMC (electromagnetic compatibility)
├── IEC 60601-1-3: Radiation protection (X-ray)
├── IEC 60601-1-6: Usability (references IEC 62366)
├── IEC 60601-1-8: Alarm systems
├── IEC 60601-1-9: Environmentally conscious design
├── IEC 60601-1-10: Physiological closed-loop controllers
├── IEC 60601-1-11: Home healthcare environment
└── IEC 60601-1-12: Emergency medical services

Particular standards (Part 2-xx):
├── IEC 60601-2-1: Particle accelerators
├── IEC 60601-2-27: ECG monitoring
├── IEC 60601-2-30: Blood pressure monitors
├── IEC 60601-2-49: Multifunction patient monitoring
└── ...many more device-specific parts
```

### Key Safety Concepts

**Essential Performance vs Basic Safety**
- **Basic Safety**: Freedom from unacceptable physical risk (electric shock, fire, mechanical hazard)
- **Essential Performance**: Performance necessary to avoid unacceptable risk — defined by manufacturer and FMEA

**Means of Protection (MOP)**
- **MOOP** — Means of Operator Protection: 2× MOOP = reinforced insulation from operator
- **MOPP** — Means of Patient Protection: 2× MOPP = reinforced insulation from patient (tighter limits)

**Applied Parts**
- Type B: Not electrically connected to patient (least protective)
- Type BF: Floating applied part (isolated from earth)
- Type CF: Cardiac floating (strictest — direct cardiac contact)

**Leakage Current Limits (Type CF, normal condition)**
- Earth leakage: ≤500 µA
- Enclosure leakage: ≤100 µA
- Patient leakage (AC): ≤10 µA
- Patient auxiliary current: ≤10 µA

### V&V Test Planning for 60601-1
```
Test Protocol Structure:
1. Scope and applicable standards
2. Equipment under test (EUT) description
3. Test configuration / setup
4. Pre-test checks (visual inspection, functional check)
5. Individual test procedures (step-by-step)
6. Acceptance criteria (pass/fail per standard)
7. Deviation handling
8. Post-test functional check
```

---

## 6. IEC 62304:2006+AMD1:2015 — Medical Device Software Lifecycle

### Software Safety Classification

| Class | Definition | Examples |
|-------|-----------|---------|
| Class A | No injury or damage possible | Scheduling software, billing |
| Class B | Non-serious injury possible | Diagnostic support (non-critical) |
| Class C | Death or serious injury possible | Infusion pump controller, ventilator software |

**Conservative Rule:** Classify based on **worst case** if SOUP (Software of Unknown Provenance) is used.

### SOUP (Software of Unknown Provenance)
Any pre-existing software component not developed under IEC 62304 lifecycle (e.g., COTS OS, open-source libraries, legacy code):
- Must be documented (name, version, manufacturer)
- Functional and performance requirements must be documented
- Known anomalies must be evaluated for impact
- For Class C: regression testing required when SOUP is updated

### Required Activities by Class

| Activity | Class A | Class B | Class C |
|----------|---------|---------|---------|
| Software development planning | Required | Required | Required |
| Software requirements analysis | Required | Required | Required |
| Software architectural design | — | Required | Required |
| Software detailed design | — | — | Required |
| Software unit implementation | Required | Required | Required |
| Software unit verification | — | Required | Required |
| Software integration testing | — | Required | Required |
| Software system testing | Required | Required | Required |
| Software release | Required | Required | Required |

### Software Development Plan Contents
```
1. Processes to be used (SDLC model: waterfall, V-model, agile)
2. Deliverables at each lifecycle stage
3. Traceability approach (requirements ↔ design ↔ tests)
4. Configuration management plan
5. Problem resolution process (defect tracking)
6. Change management
7. Maintenance plan
8. Risk management integration (ISO 14971 reference)
```

### Problem Resolution Process (§9)
All software anomalies/defects must be:
1. Evaluated for safety impact (does it affect Essential Performance?)
2. Documented with severity classification
3. Investigated to root cause
4. Resolved with regression testing
5. Recorded in problem resolution log

### Software as a Medical Device (SaMD) — IEC/TR 24971 + IMDRF
- SaMD is defined as software intended to be used for medical purposes **without** being part of a hardware device
- Subject to all standard regulations + additional IMDRF guidance
- Must include clinical evaluation component
- Post-market performance monitoring required

---

## Standards Cross-Reference Matrix

| Standard | Scope | Applies To |
|----------|-------|-----------|
| ISO 13485 | QMS | Manufacturer, distributor, supplier |
| ISO 14971 | Risk management | All medical devices |
| IEC 62304 | Software lifecycle | Devices with software |
| IEC 60601-1 | Electrical safety | Active electrical devices |
| IEC 62366-1 | Usability engineering | All devices with UI |
| 21 CFR Part 11 | E-records/signatures | US market, electronic systems |
| 21 CFR Part 820/QMSR | QSR | US market manufacturers |
| EU MDR 2017/745 | Device regulation | EU market |
| ISO 10993-1 | Biological safety | Devices with patient contact |
| ASTM F2132 | Sterilisation | Sterile devices |
