# Automotive Homologation — 20 STAR Scenarios
## Situation | Task | Action | Result — Interview Preparation

---

> **Instructions for use:** Each scenario follows the STAR format.
> - **S (Situation):** Set the scene with context
> - **T (Task):** Your specific responsibility
> - **A (Action):** What you specifically did
> - **R (Result):** Measurable outcomes

---

## Scenario 1 — First R112 Headlamp Type Approval Submission

**Question:** Tell me about a time you managed a full Type Approval submission from scratch.

**S:** I joined a tier-1 automotive lighting supplier as the homologation lead for a new LED headlamp programme. The product was a first-ever LED headlamp for that platform, and no one on the team had managed an ECE R112 Type Approval submission before. The deadline was the OEM's SOP in 16 weeks.

**T:** My task was to own the entire R112 Type Approval process — from reading the regulation and extracting requirements to receiving the Type Approval Certificate (TAC) from the Approval Authority.

**A:**
- Studied UN R112 Amendment 02 in full — created an internal requirements matrix mapping each regulation clause to a required test method and acceptance criterion
- Identified our Technical Service (TÜV Rheinland) and booked testing 10 weeks before submission
- Built the Technical File: Information Document (Annex I), engineering drawings section, COP plan, and manufacturer declarations
- Managed pre-test photometric evaluation at our internal goniometer to predict pass/fail before TS witness test
- Internal pre-test at HV showed 9.8 cd against R112's 12 cd minimum — raised alert to optics team; they adjusted the LED drive current, bringing HV to 14.2 cd
- Attended all TS type tests as applicant representative
- Compiled and submitted Technical File to KBA (Germany, E1 authority)

**R:** TAC received from KBA within 6 weeks of submission — meeting the OEM SOP requirement. Zero re-test required. The Internal pre-test system I established became standard practice for all future R112 projects at the company, reducing TS re-test incidents by 70%.

---

## Scenario 2 — B50L Glare Failure Root Cause Investigation

**Question:** Describe a time a critical photometric failure occurred and how you led the investigation.

**S:** During a Technical Service type test for a new LED projector headlamp under R112, the B50L measurement came back at 22 cd — exceeding the maximum of 17 cd. This was a hard regulatory failure with no second chance on B50L under the certificate application. The TS would halt the test program if not resolved within 3 days.

**T:** As validation engineer, I was responsible for leading the root cause analysis and proposing a corrective action that could be implemented before the extended test window closed.

**A:**
- Immediately measured our reference sample on the internal goniometer — confirmed 22 cd at B50L (not a TS calibration error)
- Reviewed the optical simulation model — found a secondary reflection path from the projector lens rim creating stray light above the cut-off
- Used near-field luminance camera: identified a bright luminance arc at the lens edge (not masked by the shield)
- Root cause confirmed: Shield height was 0.3 mm below design drawing specification — manufacturing tolerance had accumulated
- Solution: Collaborated with tooling team — new shield insert tooled within 48 hours (retained in-house capacity) bringing B50L to 13.5 cd in verification measurement
- Presented root cause and in-process control update to TS project manager

**R:** Corrected samples tested at TS — B50L: 13.5 cd (pass vs 17 cd maximum). Full certification achieved on extended test window without re-application fee. New drawing tolerance for shield height tightened from ±0.5 mm to ±0.15 mm across all projector designs.

---

## Scenario 3 — COP Audit Failure and Corrective Action

**Question:** Have you ever experienced a COP audit finding? How did you respond?

**S:** During a routine annual COP audit by the Dutch RDW (E4 authority) on our R7 stop lamp product, the auditor selected 3 production samples and requested witness testing. One sample measured 52 cd at the HV test point — below the COP acceptance minimum of 48 cd (80% of the 60 cd regulation minimum). The auditor issued a major finding and threatened TA suspension within 30 days if no corrective action was provided.

**T:** As certification manager, I had to lead a structured corrective action response within a tight deadline, coordinating cross-functionally with production, quality, and engineering.

**A:**
- Launched immediate containment — placed 3 production lots (5,000 units) on hold pending investigation
- Led root cause analysis: discovered LED bin specification had expanded to include a lower-luminous-flux bin (B20) mixed with the standard (B30) bin — procurement had accepted a batch without checking photometric equivalence
- Calculated impact: B20 bin reduces flux by ~8% — enough to push COP samples below 48 cd
- Corrective action: Rejected B20 bin batch, re-specified LED procurement to B30+ only, added incoming inspection photometric check for LED bins
- Quantified risk: Retained sample 2 (58 cd) and sample 3 (63 cd) — only 1 of 3 failed, supporting that it was a specific LED batch issue not systemic
- Submitted corrective action plan to RDW within 10 days with 6-month effectiveness monitoring plan

**R:** RDW accepted the corrective action plan — TA suspension was avoided. All held stock re-tested: 23 units in the B20 bin range were quarantined and scrapped. No field returns or customer notification required. Incoming LED bin photometric check adopted globally across all lighting sites.

---

## Scenario 4 — R48 Installation Violation Found in Vehicle Integration

**Question:** Tell me about a time you identified a compliance risk during vehicle-level integration.

**S:** During a prototype vehicle homologation review for a new SUV, I was supporting the vehicle-level R48 lighting assessment. The design engineer had mounted the rear direction indicators 450 mm above the ground — below the R48 minimum of 500 mm when the vehicle was in full bump position.

**T:** My task was to assess the severity of the non-compliance, determine if it was measurable, and work with vehicle body engineers to propose a solution that could be implemented without a complete body-side rework.

**A:**
- Measured bump travel: In full compression, rear body drops 55 mm — bringing indicator from 505 mm (nominal) to 450 mm
- Mapped R48 clause: Height is to be measured at the reference (unladen) condition. In unladen position, 505 mm — technically compliant per R48 measurement definition
- However, OEM internal standard required compliance at all suspension positions — internal requirement stricter than R48
- Engaged with body engineering and suspension team: proposed raising the rear tail lamp cluster by 30 mm — feasible within styling intent
- Ran revised R48 geometry model — raised position gives 535 mm unladen and 480 mm in full bump
- Presented findings and options to chief engineer: Option A (regulatory risk accepted) vs Option B (30 mm raise — cost impact €2k in tooling change)

**R:** OEM approved Option B. Tooling change completed at prototype build 3. Vehicle passed R48 audit at vehicle type approval RI check. Finding documented in lessons-learned and added to platform checklist for future programmes.

---

## Scenario 5 — OEM Late Design Change Affecting R112 Approval

**Question:** How have you managed a late design change that threatened an existing homologation certificate?

**S:** Four weeks before the start of production, the OEM's styling team requested a colour change of the headlamp lens — from clear to a dark-tinted lens. This was driven by vehicle styling update. The headlamp already held an R112 Type Approval Certificate.

**T:** As homologation engineer, I had to rapidly assess whether the tinted lens change would require a new TA file, an extension, or was permissible within the existing approval.

**A:**
- Reviewed existing TAC and information document: lens colour was described as "clear polycarbonate"
- Reviewed R112 text: lens material colour changes require re-test if transmission reduction > 2% at any photometric test point
- Measured tinted lens transmission: 82% vs clear lens 97% — a significant drop of 15%
- Calculated impact on all R112 test points: HV would drop from 14 cd to 11.5 cd — below 12 cd minimum
- Presented findings to programme team: tinted lens not feasible without optic redesign
- Alternative proposed: Partial tint (gradient film on outer zone only — not over the projector aperture) — maintains photometric performance
- Measured partial-tint option: HV = 13.2 cd — within margin above 12 cd minimum

**R:** Styling accepted partial tint option. Re-tested at TS with partial tint assembly — passed all R112 test points. TA extension filed for lens description change (minor variant extension). No production delay incurred. Saved an estimated €180k re-tooling cost that a full optic redesign would have required.

---

## Scenario 6 — Emergency Response to Regulation Amendment

**Question:** Tell me about a time when a regulation changed and you had to act quickly.

**S:** UNECE WP.29 published an amendment to UN R7 (Amendment 7) that introduced a new maximum luminous intensity limit for rear position lamps when combined with DRL — requiring that when DRL is active, the rear position lamp brightness automatically adapts to ≤ 12 cd. Our existing product used a fixed rear position lamp at 10 cd but the DRL had no interaction with it — the new clause would require a software change in the BCM.

**T:** I was responsible for assessing the impact on our approved product portfolio and coordinating the software update programme to maintain compliance before the transition deadline (18 months from amendment publication).

**A:**
- Read Amendment 7 in full: extraction of the specific new clause — Annex 10 paragraph 6.2 (interaction between DRL and rear position lamps)
- Created impact matrix: mapped all vehicle programmes currently in production that have our R7-approved rear lamp + R87 DRL
- Identified 14 vehicle programmes across 4 OEM customers
- Briefed all 4 OEM vehicle homologation counterparts within 2 weeks
- Coordinated with BCM supplier for each programme to develop software change
- Arranged extended COP testing: updated BCM + lamp combination tested at Technical Service to confirm compliance with new clause
- Submitted TA extensions to include the new interaction requirement for each approved lamp family

**R:** All 14 programmes updated and re-certified within 12 months — 6 months ahead of the transition deadline. No production stop or market withdrawal required. Established a regulatory monitoring process (quarterly WP.29 Working Party minutes review) to prevent future late-notice situations.

---

## Scenario 7 — Technical Dispute with Approval Authority

**Question:** Describe a time you had to defend your technical position against an authority or auditor.

**S:** During an R6 type test at TÜV, the TS engineer declared a failure on flash frequency — measuring 122 flashes/min on 3 of 10 flash cycles, slightly above the 120/min maximum. Our own internal measurements consistently showed 115–118 flashes/min with the same sample.

**T:** I was the applicant representative and had to either accept the failure or professionally challenge the measurement, providing technical justification.

**A:**
- Requested all raw data from TS: oscilloscope traces of the flash voltage, timestamped
- Reviewed data: 3 cycles showed 122 flashes/min — but these cycles coincided with lamp turn-on (first 3 flashes of the session, before thermal stabilisation)
- Reviewed R6 clause 6.3: "measurement shall begin from the second flash onwards, from a thermally stabilised state"
- Presented regulation text to TS project manager: argued that the 3 borderline cycles were captured during warm-up, not in stabilised state
- Requested re-measurement with explicit stabilisation (lamp ON for 5 minutes, then measurement starts)
- TS discussed internally — agreed the warm-up argument was valid per R6 text

**R:** Re-measurement performed on the same sample — all 10 cycles in stabilised state: 114–118 flashes/min. Pass confirmed. TS issued test report with pass. Dispute resolved without escalation to AA. I documented the stabilisation protocol ambiguity and submitted a formal comment to the WP.29 GTB working group, which was incorporated as a clarification note in the next R6 amendment.

---

## Scenario 8 — Multi-Market Simultaneous Approval (EU + India + USA)

**Question:** How have you managed a complex multi-market certification programme?

**S:** A new rear lamp cluster needed to be certified for EU (R7/R6 ECE), India (AIS-014/AIS-012), and USA (FMVSS 108) simultaneously for a global platform launch. The design team had produced one physical design meant to serve all three markets.

**T:** As certification lead, I had to determine whether one optical design could satisfy all three regulatory frameworks and manage three parallel test campaigns at different test houses across three continents.

**A:**
- Extracted test point requirements for all three standards side-by-side — created a combined test matrix
- Key conflicts found: USA (FMVSS 108) allows red rear direction indicators; ECE requires amber. Resolution: separate amber lens insert for ECE markets, red for USA (same housing)
- Indian AIS-012 flash frequency: 60–120/min (identical to ECE R6) — no conflict
- FMVSS 108 stop lamp intensity: slightly different test grid but compatible with R7 60–185 cd range
- Assigned internal test owner per market; booked TÜV (EU), ARAI (India), SGS Automotive (USA)
- Developed a single master test matrix shared across all three labs — same sample, tested in sequence reducing lead time
- Organised global coordination call weekly with all three lab contacts and OEM homologation counterparts

**R:** All three approvals achieved within 2 weeks of each other — all ahead of the platform SOP. One optical design served ECE and AIS markets with only the indicator lens colour changed for ECE vs USA. Production cost saving vs 3 separate optical designs: €430k. Became template for global lamp approval strategy at the company.

---

## Scenario 9 — Supplier Direction Indicator Fails R6 Flash Frequency

**Question:** Tell me about a supplier quality issue you resolved related to a regulatory compliance failure.

**S:** A tier-2 supplier delivered a batch of 8,000 direction indicator lamps to our production line. During our incoming inspection photometric sample check, 3 of 5 samples showed flash frequency at 128–135 flashes/min — well above the R6 maximum of 120/min. Lamps were already in the production area and assembly had begun on some vehicle sets.

**T:** As validation engineer, I was responsible for determining root cause, segregating non-compliant stock, and managing the supplier corrective action to meet production schedule.

**A:**
- Placed all 8,000 units on HOLD immediately; notified production manager and quality team
- Root cause investigation with supplier: Flasher relay timing circuit used a capacitor with ±20% tolerance — worst-case high capacitance value reduced the cycle period, increasing flash rate
- Verified: With nominal capacitor, flash rate = 112/min. With C+20% part = 134/min = failure
- Supplier had not performed statistical tolerance analysis — no production process control for timing
- Quantified at-risk population: Tested 30 additional units — 18 of 30 exceeded 120/min → batch rejection required
- Rejected entire 8,000-unit batch and returned to supplier
- Agreed corrective action plan with supplier: Reduce capacitor tolerance to ±5%, add 100% production flash frequency test before shipment

**R:** New batch delivered in 3 weeks with tightened tolerance — all units tested 108–116 flashes/min. No production shutdown occurred; line maintained with stock already in assembly. Supplier agreement updated to include incoming photometric compliance certificate with each delivery. Corrective action effectiveness verified 3 months later with zero subsequent flash frequency issues.

---

## Scenario 10 — LED Headlamp Thermal Drift Causing Photometric Failure at High Temperature

**Question:** Describe a time thermal management impacted your lamp' compliance.

**S:** During R112 type testing at our Technical Service, photometric tests were performed after 1-hour burn-in (TS standard stabilisation procedure). Results passed. However, during our own extended validation, we discovered that when the lamp was run for 3–4 hours (as would happen in real use), the LED junction temperature rose further and luminous output dropped — HV measured at 10.8 cd (below 12 cd minimum) at 4-hour mark.

**T:** My task was to characterise the thermal drift behaviour, understand if the R112 test protocol was representative, and determine whether the lamp needed a thermal redesign before start of production.

**A:**
- Set up extended photometric measurement: goniometer configured to measure HV every 30 minutes over 4 hours
- Plotted HV intensity vs time: initial 14.2 cd, drops to 10.8 cd by hour 4 — 24% degradation
- Thermal imaging: LED junction temperature at 1 hour = 105°C, at 4 hours = 138°C (above LED manufacturer's 130°C continuous rating)
- Root cause: Heat sink design had insufficient fin area — thermal resistance higher than simulation predicted due to manufacturing variation in contact layer
- Presented risk to OEM: R112 test protocol (1-hour stabilisation) does not capture this failure mode — but real-world use does
- Recommendation: Redesign heat sink (add 4 fins, increase thickness by 2 mm)
- Validated redesign: Junction at 4 hours = 115°C, HV = 13.1 cd — within specification throughout

**R:** Thermal redesign approved and incorporated before tooling freeze. OEM agreed to extended validation protocol (4-hour) becoming standard procedure for LED headlamps based on this finding. Avoided a potential field recall — cost avoidance estimated at €2.4M based on production volume.

---

## Scenario 11 — Team Managing Three Simultaneous TA Applications Under Deadline

**Question:** Tell me about a time you had to manage multiple priorities and lead a team under pressure.

**S:** I was homologation team lead with 3 engineers reporting to me. Three separate R112 Type Approval applications were all due for TS type testing within the same 4-week window — driven by platform programme SOP dates that could not slip. Each programme had its own Technical Service, drawing set, and OEM stakeholder.

**T:** My task was to manage the team capacity, ensure each Technical File was complete, and coordinate three simultaneous test campaigns without quality issues.

**A:**
- Created a master programme schedule across all three projects — tracked Technical File completion status, test booking confirmation, and sample readiness per programme week by week
- Held daily 15-minute team stand-ups to surface blockers early — resolved within 24 hours by re-prioritising tasks
- Allocated each engineer as lead for one programme, with me as reviewer and escalation point for all three
- Identified conflict: Programme 3's Technical File drawing section was incomplete (supplier hadn't delivered final drawings) — raised to programme manager 3 weeks early; drawing received with 1 week margin
- Implemented Technical File review checklist — each file peer-reviewed by another engineer before submission
- Coordinated sample logistics: 3 sets of test samples required customs clearance for TÜV Germany, UTAC France, and Millbrook UK simultaneously — managed via freight forwarder on joint shipment

**R:** All three TA applications submitted on schedule. Two received TACs within 4 weeks. One required one re-test due to an EMC test point (not photometric) — resolved and certificate received 2 weeks after re-test. Team engagement scores improved during this period (quarterly survey) — team reported clarity of goals and effective daily stand-up as key positives.

---

## Scenario 12 — Engineering Change Impact on Existing Type Approval

**Question:** How do you manage engineering changes to approved products?

**S:** Production of a certified R7 rear lamp cluster was running at volume when the procurement team proposed substituting the LED supplier from Supplier A to Supplier B (lower cost, same LED package). This was driven by a cost reduction initiative targeting €0.80/unit saving.

**T:** As certification engineer, I had to assess whether the LED supplier change constituted a change to the approved type requiring re-test or TA extension, and provide a clear recommendation to the business.

**A:**
- Reviewed the R7 TAC information document: LED module described by part number (Supplier A's part number)
- Reviewed R7 regulation: change of light source requires re-test and TA extension
- However, if the LED change could be classified as an equivalent replacement (same photometric characteristics, same board layout), some authorities accept without full re-test
- Requested full photometric characterisation from Supplier B for their LED:
  - Luminous flux: Supplier B = 850 lm vs Supplier A = 900 lm (5.6% lower)
  - Colour coordinates: Both within white boundary — similar
  - Forward voltage: Supplier B 3.0V vs Supplier A 3.1V — minor
- Calculated impact: 5.6% flux reduction → stop lamp HV expected to drop from 95 cd to 89.7 cd — still above 60 cd minimum but margin reduced
- Performed photometric test on pre-production sample with Supplier B LED: measured 91 cd — pass confirmed
- Recommendation: TA extension required (LED part number changed in information document) — can be done as minor extension with photometric test data only (no full TS type test required — authority agreed)
- Filed TA extension with photometric test report as supporting evidence

**R:** TA extension granted in 3 weeks. LED supplier change approved without production disruption. Cost saving realised: €0.80/unit × 2.4M annual volume = €1.92M/year. No market compliance risk.

---

## Scenario 13 — First AFS (R123) Adaptive Headlamp Approval

**Question:** Tell me about a technically complex homologation experience.

**S:** Our company was tasked with designing and certifying the first AFS (Adaptive Front-lighting System) headlamp under UN R123 for a premium car OEM. The product used a 64-pixel matrix LED system — no one in our team had done an AFS type test before. The Technical Service was also not familiar with matrix LED AFS testing.

**T:** As senior homologation engineer, I was responsible for writing the first internal test protocol for AFS compliance and guiding both our team and the TS through the novel test procedure.

**A:**
- Read UN R123 cover-to-cover with annotations — extracted 47 individual requirements mapped to test methods
- Key challenge: Matrix LED AFS requires testing each "beam class" (C, V, E, W, T) as a separate photometric configuration — 5 sets of test points × multiple aim conditions
- No existing internal test procedure: wrote new internal AFS test procedure document (SOP-HOM-023) covering all R123 test point configurations and aim verification methods
- Reviewed with TS (Applus IDIADA) — incorporated their feedback on test fixture requirement for AFS swivel verification
- Designed AFS swivel test rig: stepper motor controlling steering input, encoder measuring swivel angle of headlamp optic
- Pre-tested all 5 beam classes internally: found Class E (motorway) had insufficient range extension (was 3% below R123 minimum at 1° above H-H test point)
- Worked with optics team: increased LED zone activation footprint for Class E — pre-test confirmed compliance
- Attended full R123 type test as applicant representative — 3-day test session

**R:** R123 type approval granted — first AFS product at our company certified under UN R123. Test procedure I wrote was adopted as company standard. OEM secured a competitive advantage with AFS as a first-in-class feature on the new platform. TAC received 4 weeks ahead of SOP.

---

## Scenario 14 — EMC Failure on LED Headlamp Driver (R10)

**Question:** Describe a time you solved an EMC compliance issue.

**S:** During R10 (EMC) radiated emissions testing, the LED headlamp driver was failing CISPR 12 limits at 144 MHz — 8 dB above the limit. This was identified 6 weeks before the planned TA submission date.

**T:** As test engineer, I had to diagnose the interference source, coordinate with the LED driver electronics designer, and validate a fix within the 6-week window.

**A:**
- Recorded radiated emissions spectrum — peak at 144 MHz, harmonic of the LED PWM switching frequency (48 MHz × 3rd harmonic = 144 MHz)
- Used near-field probe to trace emission source: wiring harness between LED driver and lamp head — acting as antenna for the 144 MHz noise
- Review of driver PCB: no ferrite bead or common-mode filter on output lines
- Proposed fix: Add common-mode choke (ferrite bead array, 1 µH at 100 MHz) on the harness at driver output connector
- Electronics designer implemented on breadboard within 1 week — tested in RF chamber: reduced emission at 144 MHz by 11 dB — 3 dB below limit
- Verified fix: No impact on lamp photometric performance (no lumen reduction from choke)
- Updated bill of materials and wiring harness drawing to include choke component

**R:** R10 type test passed all CISPR 12 limits with 3 dB minimum margin. TAC submission not delayed. EMC filter design guideline added to company LED driver design standard, preventing recurrence on future products.

---

## Scenario 15 — Colour Coordinate Boundary Failure (Amber Near White Boundary)

**Question:** Tell me about a colour compliance challenge you faced.

**S:** Our R6 direction indicator samples were measured at the Technical Service — colour coordinates x = 0.512, y = 0.480. The amber boundary requires x ≥ 0.540 (approximately). Our sample was inside the white region — an R6 failure. The amber lens we specified had been changed by the tooling team to increase transmission for higher intensity — the new lens had lower amber saturation.

**T:** I had to identify the root cause, determine if a compliant lens material existed with the required colour purity without reducing intensity below R6 minimum, and deliver corrected samples for TS re-test.

**A:**
- Measured 5 lens material options from our approved material database — plotted each on CIE diagram against R6 amber boundary
- Two materials met chromaticity (x ≥ 0.545): Material A and Material B
- Measured photometric performance with each material: Material A → 195 cd (above R6 175 cd minimum). Material B → 168 cd (below minimum).
- Material A selected — satisfies both colour and intensity
- Root cause confirmed: The original tooling team had swapped to a different material grade (higher transmission, lower amber purity) without homologation review
- Implemented mandatory Homologation Impact Assessment (HIA) for any material change — lens tooling, adhesive, or coating changes now require sign-off from homologation before production change

**R:** Material A validated samples tested at TS: x = 0.551, y = 0.477 — within amber boundary. Intensity 192 cd — comfortably above 175 cd minimum. R6 type approval granted without further issues. Material change control process (HIA form) implemented across all product lines.

---

## Scenario 16 — Technical File Incomplete at Submission, Authority Request for More Information

**Question:** How have you handled a situation where a submission was not accepted in first pass?

**S:** I submitted a Technical File for an R7 rear position lamp TA to the Netherlands RDW. Within 2 weeks, RDW issued a Request for Information (RFI) with 6 points — they were missing the vibration test report, wanted additional CIE colour plot with boundary lines visible, and needed clarification on three drawing dimensions.

**T:** My task was to respond comprehensively and quickly to avoid further delays — each week of RFI response time extended TAC receipt and risked delaying SOP.

**A:**
- Reviewed all 6 RFI points immediately — categorised: 2 missing documents, 3 drawing clarifications, 1 format issue (colour plot)
- Vibration test report: Had been completed 2 months earlier but not included in file — attached immediately
- CIE colour plot: Regenerated from test data with boundary lines per RDW's format requirement — reflected within 24 hours
- Drawing dimensions: Raised to design team — agreed to add dimensional notes to 3 drawing views — completed in 2 days
- Compiled complete RFI response package — reviewed by senior homologation engineer before sending
- Submitted comprehensive response within 5 working days of RFI receipt

**R:** RDW issued TAC within 3 weeks of receiving the RFI response — no further queries. Programme SOP date maintained. Established a Technical File pre-submission checklist specifically for RDW requirements based on this experience — reduced RFI rate from 40% to 8% on subsequent submissions to RDW over the following year.

---

## Scenario 17 — Production Tolerance Exceedance — Field Containment

**Question:** Tell me about a time you identified an in-market compliance risk and managed the containment.

**S:** A routine COP test on our R6 rear direction indicator revealed a production sample at 44 cd at the axis — below the 50 cd R6 minimum for Category 2 (rear). On investigation, we discovered the under-performing LED batch had been supplied for 3 months — potentially up to 180,000 vehicles in the field.

**T:** As certification manager, I had to determine the actual scale of the non-compliance, coordinate with the OEM customer, and propose a remediation plan compliant with regulatory obligations.

**A:**
- Traced all LED deliveries from the affected batch: 1.2M individual LED components delivered over 12 weeks; affected 185,000 vehicles already delivered to customers
- Measured retained samples from the batch: Confirmed 38 of 50 samples below 50 cd minimum; worst case: 41 cd
- Risk assessment: 41 cd vs 50 cd = 18% below minimum. In real use, intensity this low may not affect safety significantly (subjective judgement) — but regulatory non-compliance is a fact
- Notified Approval Authority (RDW) within 14 days as required under R6/UNECE obligations
- Engaged OEM legal and quality team — joint assessment of recall vs field monitoring approach
- OEM decision (with AA concurrence): Monitor field reports; if any visibility complaint in 6 months, initiate dealer inspection programme
- Redesigned LED procurement spec: minimum guaranteed flux on incoming inspection; new incoming test introduced

**R:** Field monitoring over 6 months: Zero visibility-related complaints attributed to the affected population. RDW accepted monitoring approach with enhanced COP requirements for 2 years (quarterly instead of annual COP sampling). Supplier penalised per supply agreement. Internal process change prevented recurrence.

---

## Scenario 18 — Cross-Functional Impact Assessment for Design Change

**Question:** Describe a time you had to coordinate across multiple functions to prevent a compliance risk.

**S:** The plastics engineering team proposed changing the headlamp lens material from polycarbonate (PC) to PMMA (acrylic) for a cost saving programme. This change had implications for UV ageing, thermal resistance, and light transmission — all of which had been tested and documented in the existing R112 type approval.

**T:** As homologation engineer, I needed to lead an impact assessment across optics, materials, thermal, legal/compliance, and the programme team to determine the full impact of this change on our R112 approval.

**A:**
- Assembled cross-functional impact assessment team: Materials engineer, thermal CAE, optics lead, programme manager, quality engineer, and myself
- Created impact matrix: Mapped each R112 test that referenced lens material properties (photometric, thermal, UV ageing, impact resistance)
- Key findings from each function:
  - Materials: PMMA yellows at 60°C ambient over 3 years (PC stable to 80°C) — thermal risk for underbonnet application
  - Optics: PMMA transmission 2% higher than PC — photometric improvement (minor positive)
  - Thermal: PMMA Tg (glass transition) 83°C vs PC 145°C — risk of lens deformation near LED heat
- Homologation impact: Lens material change = variant change requiring TA extension and fresh ageing test (12-week lead time for UV ageing)
- Programme impact: 12-week delay not acceptable for current programme phase
- Presented to programme manager: Options A (proceed with PMMA: 12-week delay, €650k re-test cost) and Option B (remain PC: no delay, no re-test cost, sacrifice cost saving)

**R:** Programme team chose Option B — PMMA change deferred to next generation platform where design timeline accommodated re-certification lead time. Next-gen programme was started with PMMA qualification from Day 1, making it timeline-neutral. Cross-functional impact assessment process formalised as a company procedure for all material changes.

---

## Scenario 19 — Competitive Benchmark Photometric Analysis

**Question:** Tell me about a time you used technical analysis to support a commercial or engineering decision.

**S:** Product management asked for a competitive benchmarking study of headlamp photometric performance — specifically comparing our current production headlamp against 3 competitor products for the same vehicle segment, all R112 certified.

**T:** As validation engineer, I was tasked with designing and executing the benchmark test, analysing results, and presenting findings with engineering recommendations.

**A:**
- Purchased 3 competitor headlamps from aftermarket (all bearing valid E-marks)
- Set up all 4 headlamps on the internal goniometer using identical test conditions: 25 m, 13.2V supply, 30-minute stabilisation
- Measured full photometric grid (R112 test points + 20° × 20° angular map) for all 4 units
- Created comparison data table: Our lamp at HV = 14.2 cd; Competitor A = 18.5 cd; Competitor B = 16.0 cd; Competitor C = 13.1 cd
- Generated beam pattern false-colour intensity maps for visual comparison
- Our lamp: good homogeneity but lower peak intensity than Competitors A and B
- Near-field luminance analysis: our lamp had 20% lower LED drive current than Competitor A — driving room available

**R:** Presented findings with recommendation: increase LED drive current by 15% — feasible within thermal budget. Engineering implemented increased drive current on next LED bin revision. Follow-up test: HV = 16.8 cd — now competitive with Competitor B. Product management used the benchmarking data to support a "class-leading visibility" marketing claim based on 75R test point (best in class after update). Study method adopted as standard product benchmarking protocol.

---

## Scenario 20 — New Market Entry — Harmonising R112 with FMVSS 108

**Question:** Describe a challenge you faced when entering a new market with an existing product.

**S:** Our European R112-approved LED headlamp was selected for a new US market variant. The product team assumed the R112 approval could be directly used for the USA with minimal change. My task was to assess the FMVSS 108 requirements and determine what, if any, changes were needed.

**T:** As homologation lead, I needed to execute a gap analysis between R112 and FMVSS 108 for our specific product and provide a clear recommendation with scope of work for US market compliance.

**A:**
- Extracted FMVSS 108 Table XIV photometric requirements for headlamps — created a side-by-side comparison with R112
- Key gaps identified:
  - FMVSS 108 does not recognise the B50L glare point (different safety philosophy)
  - FMVSS 108 low beam requires higher intensity at specific right-side points (0.6D25R zone — different from R112)
  - FMVSS 108 requires SAE J583 DRL compliance (different from R87/R7) if DRL is present
  - Self-certification in USA — no TA submission, but must maintain documentation for NHTSA audit
  - DOT marking required instead of E-mark
  
- Ran the R112-approved headlamp photometric data through FMVSS 108 test point map: 2 of 12 FMVSS test points failed (0.6D25R and 0.6U2L)
- Proposed optics adjustment: Add minor reflector zone modification to shift intensity toward failing points without degrading R112 compliance
- Modelled modification in optical simulation — confirmed dual compliance in simulation
- Physically validated on prototype — passed both R112 full measurement AND FMVSS 108 test matrix

**R:** US market variant qualified with minor optical modification. Dual-compliant product confirmed by documentation (FMVSS self-cert package) and retained sample store. US market launch achieved on schedule. Framework for dual R112 / FMVSS 108 assessment became reusable template for all future US market entries.

---

*File: 05_star_scenarios.md | automotive_homologation series | 20 STAR scenarios*
