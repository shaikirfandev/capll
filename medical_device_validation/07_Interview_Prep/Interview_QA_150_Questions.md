# Medical Device Validation Engineer — 150 Interview Q&A

## SECTION 1: Regulatory Standards (40 Questions)

### ISO 13485

**Q1: What are the key differences between ISO 9001 and ISO 13485?**
> ISO 13485 is specifically tailored for medical devices and incorporates regulatory requirements as a primary driver rather than customer satisfaction. Key differences: ISO 13485 explicitly requires risk management integration throughout (aligned with ISO 14971), mandates process validation, requires documented procedures for complaint handling and post-market surveillance, has stricter document and record control requirements, and requires infrastructure to maintain the working environment. ISO 9001 uses a risk-based thinking concept more broadly, while ISO 13485 treats risk management as a specific documented process.

**Q2: Walk me through a Design History File — what does it contain and why?**
> The DHF is the regulatory record proving that the design control process was followed. It contains: Design and Development Plan (scope, stages, responsibilities), Design Inputs (user needs translated to measurable requirements), Design Outputs (drawings, specs, software), Design Review Records (systematic examinations at defined stages), Verification Records (tests proving outputs meet inputs), Validation Records (evidence device meets user needs in intended use), Risk Management File (ISO 14971 hazard analysis and risk controls), Design Transfer Records (production scale-up evidence), and Change Records (all design changes with impact assessments). The DHF is critical because without it, an FDA audit would find design controls not followed, which is a Major 483 observation or Warning Letter.

**Q3: What is the difference between a DHF and a DMR?**
> The DHF (Design History File) documents the history of designing and developing the device — it's the "how we designed it" record. The DMR (Device Master Record) documents how to manufacture the device — it's the "recipe" or blueprint. A DHF entry might be "Verification Test Report showing pump delivers within ±5%" while a DMR entry is "Manufacturing SOP for pump assembly, Rev 3." The DHF is a regulatory requirement under 21 CFR 820.30(j), and the DMR under 820.181.

**Q4: What triggers a design change review under ISO 13485 §8.3.10?**
> Any modification to a device's design or manufacturing process, regardless of how minor it appears, requires formal change control. This includes: changes to materials, dimensions, software code, manufacturing processes, suppliers (for critical components), sterilisation methods, labelling, or packaging. The impact assessment must evaluate: does the change affect safety or performance? Does it require re-verification or re-validation? Does it affect regulatory submissions? The change must be reviewed, verified/validated as appropriate, and approved before implementation.

**Q5: How do you handle a design input that cannot be verified by test?**
> Some design inputs are verified by analysis rather than testing. For example, biocompatibility (ISO 10993 risk-based assessment), software architecture adequacy (design review and walkthrough), or theoretical calculations for structural loads. The verification method must be documented in the verification plan, and the chosen method (test, analysis, demonstration, or inspection) must be technically justified. The acceptance criteria must still be objective and measurable.

---

### ISO 14971

**Q6: Explain the two probability components in ISO 14971 risk estimation.**
> ISO 14971 defines the probability of harm as P1 × P2, where P1 is the probability of the hazardous situation occurring given the failure mode exists (e.g., probability that a pump malfunction causes unexpected dose delivery), and P2 is the probability that the hazardous situation leads to harm given it occurs (e.g., probability that unexpected dose delivery causes patient injury). Separating these allows more precise risk estimation — a hazardous situation might occur frequently (high P1) but rarely cause harm if protective measures exist (low P2).

**Q7: What is the hierarchy of risk control options and why does it matter?**
> Per ISO 14971 §6.2, risk controls must be applied in priority order: (1) Inherently safe design — eliminate the hazard or reduce risk through design choices; (2) Protective measures — guards, interlocks, alarms, automatic shut-off; (3) Information for safety — warnings in labelling, IFU instructions, training requirements. This hierarchy matters because information-only risk controls are the weakest — they rely on the user correctly reading and following instructions every time, which is statistically unreliable. A well-designed device controls risk at the design level before relying on labelling.

**Q8: How do you determine residual risk acceptability?**
> After applying risk controls, evaluate residual risk against the risk acceptance criteria defined in the Risk Management Plan. If residual risk is below the acceptable threshold — done. If above the threshold but the benefits of the device outweigh the residual risk, a benefit-risk determination may support acceptability. If neither applies, additional risk controls must be implemented. Additionally, the overall residual risk (all residual risks combined) must be evaluated — a device with many small residual risks may have unacceptably high overall risk even if each individual risk seems acceptable.

**Q9: How do you ensure risk management is integrated throughout the product lifecycle?**
> Risk management is not a one-time activity. I integrate it at every stage: during design inputs, perform initial hazard analysis (PHA) to identify potential hazards from intended use and foreseeable misuse; during design, update the FMEA as the design evolves and risk controls are implemented; during verification and validation, test every risk control measure; post-market, monitor for new hazards through complaint analysis, PMS data, literature surveillance, and incident reporting. The Risk Management File is a living document updated throughout the device lifecycle.

**Q10: Describe how you would set up an FMEA for a new medical device.**
> I start by forming a cross-functional team (design, manufacturing, software, clinical, regulatory). We create the FMEA table with columns for: component/function, potential failure mode, potential effect, severity (1-5), potential cause, current controls, occurrence (1-5), detection method, detection (1-5), RPN = S×O×D, and recommended actions. I populate it systematically by working through every component and function. For medical devices, I weight severity most heavily — a severity-5 item gets priority regardless of low occurrence. Risk controls for high-severity items are linked back to design inputs and must be verified in the test plan. The FMEA is reviewed at each design review gate.

---

### 21 CFR Part 11

**Q11: A new employee asks why we can't share login credentials in our eQMS. How do you explain it?**
> 21 CFR Part 11 §11.300 requires that "persons who use electronic signatures based on use of identification codes in combination with passwords shall employ controls to ensure their security and integrity." Sharing credentials means an electronic signature no longer uniquely identifies an individual — we cannot establish who actually made a change or approved a record. In a regulatory audit, shared credentials are a direct Part 11 violation and would call into question the integrity of all electronic records. Individual accountability is non-negotiable in regulated environments.

**Q12: What is the minimum audit trail information required under Part 11?**
> An audit trail must capture: the user ID (who), the action taken (what — create, modify, delete, approve), the date and time stamp (when — system-generated, not user-modifiable), and for modifications, the previous value and new value. The audit trail must be computer-generated (not manually editable), retained for the same period as the associated record, and available for FDA inspection.

**Q13: How does Part 11 differ for an open system versus a closed system?**
> A closed system is one where access is controlled by the organisation that owns the records (e.g., internal QMS system behind a firewall). An open system involves records transmitted across public networks. In addition to all closed system requirements, open systems must use document encryption and digital signatures with PKI to protect record integrity during transmission. The practical implication is that any system where regulated records are sent via email or accessed over the internet needs the additional encryption and digital signature requirements.

---

### EU MDR

**Q14: What is a GSPR checklist and how do you create one?**
> GSPR stands for General Safety and Performance Requirements (Annex I of MDR 2017/745). Creating a GSPR checklist involves: listing every applicable GSPR requirement (there are ~23 general requirements and many specific ones for particular device types), for each requirement determining if it applies to your device, identifying the harmonised standard or common specification that addresses it, documenting how conformity was demonstrated (test, analysis, clinical data), and referencing the evidence in the technical documentation. Non-applicable requirements must be justified. This checklist is a core element of the technical documentation and is reviewed by the notified body.

**Q15: How has EU MDR changed post-market obligations compared to MDD?**
> Under MDR, Post-Market Surveillance is significantly more rigorous. Manufacturers must have a proactive PMS plan (not just reactive complaint handling), conduct Post-Market Clinical Follow-up (PMCF) for all device classes with a systematic literature review and structured data collection, submit Periodic Safety Update Reports (PSURs) or Summary of Safety and Clinical Performance (SSCP) documents annually or every two/three years depending on class, and report to EUDAMED (the EU device database). The SSCP for Class IIb and III devices must be written in language understandable to patients and healthcare professionals and made publicly available.

---

### IEC 62304

**Q16: How do you classify SOUP in your project?**
> I review each SOUP item (third-party library, OS component, open-source package) against the worst-case impact on patient safety if it fails. I look at: does this component contribute to Essential Performance? Can its failure lead to patient harm? If failure of the SOUP could contribute to Class B or C harm, the overall software may need to be classified at B or C. I document each SOUP: name, version, manufacturer, functional requirements it must meet, known anomalies from bug databases, and my impact assessment. For Class C software using Class B-rated SOUP, I typically add regression tests when the SOUP is updated.

**Q17: What is the difference between software verification and software system testing under IEC 62304?**
> Software verification under IEC 62304 covers multiple activities: unit verification (testing individual units in isolation), software integration testing (testing units working together), and software system testing (testing the complete software in its target environment). Software system testing (§5.6) verifies that the software satisfies the software requirements specification as a whole. Verification at each level provides evidence that the software was built correctly at that level before moving to the next. This creates a hierarchy of evidence aligned with the V-model.

---

## SECTION 2: V&V Activities (30 Questions)

**Q18: How do you differentiate verification from validation in a real project example?**
> I'll use an infusion pump example. Verification: "The pump shall deliver fluid within ±5% of set rate at 100 mL/hr." I run a bench test measuring actual delivery against set rate — this verifies the design output meets the design input. Validation: "The pump shall be operable by ICU nurses with minimal training." I conduct a simulated use study with ICU nurses in a lab environment, observing task completion, use errors, and time-on-task — this validates the device against the user need. Verification asks "did we build it right?" Validation asks "did we build the right thing?"

**Q19: Walk me through how you would write a V&V plan for a new medical device.**
> I start by reviewing the design inputs document to identify all testable requirements. I categorise them: safety-critical, performance, usability, labelling, sterilisation, biocompatibility, EMC, electrical safety. For each category I determine: verification method (test, analysis, inspection, demonstration), test level (unit, integration, system), responsible party, applicable standard, and risk priority. I write the V&V plan documenting all this along with resources, equipment, environment, completion criteria, and how deviations will be handled. The plan is reviewed by the design team and QA, then approved before testing begins. Every test case traces to a requirement.

**Q20: How do you ensure your test equipment is appropriate for use?**
> All test equipment must be calibrated against national/international standards. I verify: the instrument's accuracy is at least 4× better than the tolerance being measured (4:1 test accuracy ratio), the calibration certificate is current and not expired, the calibration sticker matches the certificate, and the instrument is within its operating specification for the test conditions. In the test protocol, I record the instrument model, serial number, calibration certificate number, and calibration due date. If equipment is found out of calibration after testing, I perform an impact assessment on all results obtained with that equipment.

**Q21: How do you handle a situation where 3 out of 30 test units fail acceptance criteria?**
> First, I stop and document the failures — I do not discard them or retest without investigation. I evaluate: is this a safety issue? Do the failures indicate a systemic design problem or random manufacturing variation? I conduct a root cause analysis. If it's a systematic design issue, the design must be corrected and all 30 units retested. If it's a manufacturing/process issue, the process must be improved. If it's a statistical outlier with analysis supporting it, I document the disposition with engineering justification. I would not "accept" failures unless there's rigorous analysis showing they represent acceptable risk — and that analysis goes in the DHF. I would never simply accept failures to meet a schedule.

**Q22: Describe your approach to testing software-hardware integration.**
> I start with a system-level integration test plan that covers all interfaces between software and hardware: sensor inputs (normal values, boundary values, out-of-range values), actuator commands (valid commands, boundary conditions, invalid commands), communication buses (normal traffic, timeout, bus errors), power states (startup, normal operation, shutdown, unexpected power loss), and error handling (hardware fault injection). I use real hardware where possible, and hardware simulators for conditions that are dangerous or difficult to create (e.g., sensor failure). For Class C software, I include fault injection tests to verify software responds correctly to hardware faults.

**Q23: What is a use error analysis and how does it inform test cases?**
> A use error analysis (per IEC 62366-1 §5.4) systematically identifies ways users might make errors with the device. I analyse: what tasks must users perform? What knowledge and skills are required? Where can users confuse controls? What happens if they do the task in the wrong sequence? Which errors lead to harm? This analysis produces a list of use errors — some critical (leading to harm) and some minor. For critical use errors, I write test cases to verify that either the device prevents the error (e.g., confirmation dialog), detects and warns about the error (alarm), or the error cannot occur at all (foolproofing). The test cases are run during summative usability evaluation.

---

## SECTION 3: PLM Systems (25 Questions)

**Q24: Explain the concept of document lifecycle management in a PLM system.**
> Every document in a PLM system progresses through lifecycle states: typically In Work → Under Review → Released → Obsolete. In Work means it's being authored and can be modified. Under Review means it's in an approval workflow — changes are restricted. Released means it's an approved, controlled version — the "official" version. Obsolete means it has been superseded by a newer revision or withdrawn. The PLM system enforces these states through access control — for example, only the document owner can check out a Released document to create a new revision. This ensures we always know which version is current and approved.

**Q25: How do you manage BOM (Bill of Materials) in a PLM system?**
> I create the BOM hierarchy in the PLM with each component as an Item with Part Number, Revision, and Description. I use effectivity dates for planned changes (item A superseded by item B from date X). I manage SBOM (software BOM) alongside hardware BOM — each software module with version number. I link the BOM to purchasing (approved manufacturers list per 21 CFR 820.50) and connect to the DMR. Critical suppliers are flagged, and any change to a critical component triggers a formal supplier change notification (SCN) review. The PLM enforces that BOMs can only be modified through the change control process.

**Q26: You've been asked to migrate from Agile PLM to Windchill. What are the key risks?**
> Key risks are: data completeness (some legacy records may have incomplete metadata), data integrity (relationships between documents and BOMs may not migrate correctly), signature validity (electronic signatures may not transfer with legal equivalence requiring re-approval), user access (roles and permissions must be remapped), training (users need time to learn the new system before go-live), downtime (period when neither system is fully operational), and regulatory validation (the new system must be validated before regulated data is created). I would mitigate these through a phased migration, parallel running period, a formal data verification step comparing 100% of migrated records to originals, and full IQ/OQ/PQ before production go-live.

**Q27: How would you validate a new Jama Connect instance for regulatory use?**
> I follow GAMP 5 guidance. Jama Connect is a Category 4 configured application. Validation steps: (1) URS — document business requirements (traceability, review workflows, test management); (2) Functional Specification — Jama's standard spec plus our configurations; (3) Risk Assessment — identify high-risk functions (traceability links, review records, electronic signatures); (4) IQ — verify installation, version, user accounts, SSO configuration; (5) OQ — test all standard functions and custom configurations against acceptance criteria; (6) PQ — run end-to-end scenarios simulating real project traceability, review, and test execution; (7) Validation Report — summarise results, note any deviations, conclude system fit for purpose. Maintain documentation for FDA inspection.

---

## SECTION 4: Design Control (20 Questions)

**Q28: What is the FDA's design control guidance and how do you apply it?**
> FDA's Design Controls Guidance (1997) implements 21 CFR 820.30. It describes a design control system using the "waterfall" concept: user needs → design inputs → design process → design outputs → design verification → design validation. At each stage, documented evidence must exist. Key principles: design inputs must be unambiguous and measurable; verification must prove outputs meet inputs; validation must prove device meets user needs; design reviews must be systematic and conducted by qualified reviewers who were not directly responsible for the design being reviewed; and the DHF must document all evidence.

**Q29: How do you manage design changes that occur late in development?**
> Late-stage design changes are common and carry more risk because verification/validation work may need to be repeated. My process: immediately assess the change scope using a formal change impact assessment; determine which requirements are affected; identify which previously executed tests are invalidated by the change; execute targeted re-verification on affected areas; if the change affects the intended use or user interface, consider whether validation must be repeated; update all affected documents (SRS, SDS, risk file, labelling) through change control; and document in the DHF. I track the change in a change log visible to the entire project team and QA.

**Q30: Describe traceability from user need to production verification.**
> The traceability chain: User Need (e.g., "Clinician needs to programme dose remotely") → Design Input/Requirement (e.g., "System shall support wireless dose programming via IEEE 802.11 at ≤10m") → Design Output (e.g., Wi-Fi module specification, software architecture diagram) → Verification Test (e.g., TC-COMM-045: wireless programming at 10m range with 0 errors in 100 attempts) → Result (pass, documented in test report) → DHF entry. In the RTM, I maintain this chain bidirectionally — I can start from any test and trace back to the user need, or start from any user need and find its test evidence. For risk controls, the chain also includes the FMEA hazard ID.

---

## SECTION 5: Scenario-Based Questions (35 Questions)

**Q31: You discover a critical test case was not executed before product release. What do you do?**
> Do not ignore it. Immediately notify QA and the project lead. Assess the criticality: does the missing test cover a safety requirement or risk control? If yes, this may require a field safety corrective action (FSCA) depending on whether the device is already distributed. I initiate a formal investigation: why was the test skipped? Was it documented? I file an NCR or CAPA. If the device is not yet distributed, we execute the test before any further distribution. If distributed, we perform a risk assessment: can we test on the same device (if not destructive)? Do we have analytical evidence from related testing? The conclusion must be documented and defensible. This scenario reflects why the test completion checklist exists.

**Q32: An FDA inspector is asking for your DHF for a product released 3 years ago. What happens?**
> I retrieve the DHF from our controlled archive (PLM or document control system). I present: the DHF index showing all included documents, design inputs approval records, design review meeting minutes, verification test reports, validation reports, risk management file, and design transfer records. I walk the inspector through the traceability — every design input has a corresponding test result, every risk control is tested. If any document is missing, I do not fabricate or reconstruct it — I acknowledge the gap and present compensating controls if available. Missing DHF elements are 21 CFR 820.30 violations and must be addressed through CAPA.

**Q33: A risk control in your FMEA references a software alarm, but the software was changed after validation. What do you do?**
> This is a critical situation. The software change must have gone through change control, and the impact assessment must have identified whether the alarm logic was affected. If it was affected, re-validation of the alarm (and any related risk controls) was required before the software was released. If the change control somehow missed this impact, we have a process failure. I would: (1) immediately evaluate whether the alarm is currently functional by testing against the original risk control acceptance criteria; (2) if the alarm is functional, document supplementary verification evidence and update the risk management file; (3) initiate a CAPA on the change control process; (4) if the alarm is not functional, initiate a field safety assessment.

**Q34: How do you prioritise when you have 200 test cases and 2 weeks before a product launch?**
> I never skip safety-critical tests — these are non-negotiable. I apply risk-based prioritisation: execute all tests covering safety requirements and risk control measures first; then functional requirements, boundary conditions, and performance specs; then cosmetic/minor tests last. I review the open defect list — do any open defects touch safety-critical areas? If yes, those must be resolved first. I communicate timeline risk to management early — not two days before launch. If the test plan cannot be fully executed within the timeline, the launch should be delayed or the scope formally reduced with QA approval, not silently truncated.

**Q35: How do you ensure traceability is maintained when requirements change during development?**
> I enforce a change notification process in the requirements management tool (Jama or DNG). When a requirement is modified, the tool automatically flags all downstream items (design outputs, test cases) as "suspect." I review each suspect item to determine: does the change invalidate this test case? Must the test be updated? Must the test be re-executed? I update the RTM to reflect the new traceability state. In agile development, I run a traceability review at the end of each sprint to ensure the matrix is current. At each design review gate, the RTM is formally reviewed and signed off — no gate can close with open traceability gaps.

---

## SECTION 6: Technical Writing Questions (20 Questions)

**Q36: What makes a good SRS (Software Requirements Specification)?**
> A good SRS is: Complete (every function specified), Unambiguous (one interpretation only), Verifiable (each requirement can be tested or analyzed), Consistent (no contradictions), Traceable (each requirement has a unique ID), Correct (reflects actual user needs), and Feasible (can be implemented). I avoid vague words: "fast," "user-friendly," "appropriate." Instead: "response time < 500ms," "novice user completes task in < 3 minutes," "maintains ±0.5°C accuracy." I write requirements in "shall" language: "The system SHALL..." vs "The system SHOULD..." (shall = mandatory, should = optional).

**Q37: Write a requirements statement for an infusion pump low battery alarm.**
> "The pump SHALL generate an audible alarm ≥ 65 dB(A) at 1 metre and display 'LOW BATTERY' on the display when the remaining battery capacity falls below 20% of rated capacity. The alarm SHALL activate within 5 seconds of battery threshold being reached. The alarm SHALL persist until the user acknowledges it or the battery is replaced. The remaining operation time at the current infusion rate SHALL be displayed in hours and minutes."

**Q38: How do you write a test procedure that a technician can follow without engineering guidance?**
> I assume zero background knowledge beyond the technician's role. I: write numbered steps with no step doing more than one action; specify exact button labels, menu paths, and field names as they appear on the device; include a diagram or photo of the test setup; specify exact measurement methods (e.g., "measure with Fluke 87V multimeter on the 200mA AC range, probes on TP1 and TP2"); give exact expected results with tolerances ("temperature shall be 37.0 ± 0.2°C"); include troubleshooting for common issues; and require the technician to initial each step. I pilot-test every new protocol with a technician who was not involved in writing it.
