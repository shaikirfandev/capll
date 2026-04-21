# Automotive Homologation — 20 Interview Q&A
## Detailed Questions with Expert-Level Answers

---

## Q1. What is automotive homologation and why is it important?

**Answer:**
Automotive homologation is the official process of obtaining regulatory approval — from a recognised government authority — confirming that a vehicle, system, or component meets defined technical standards before it can be legally placed on the market.

The importance is threefold:
1. **Safety:** Ensures lighting systems (headlamps, indicators etc.) provide adequate visibility and don't dazzle other road users.
2. **Market access:** Without type approval, the product cannot be legally sold in that country.
3. **Consumer confidence and trade:** Mutual recognition under the 1958 UNECE Agreement means a single approval covers 60+ countries, enabling efficient global distribution.

Without homologation, a manufacturer risks product liability, regulatory fines, forced market withdrawal, and reputational damage.

---

## Q2. What is the difference between UN R112, UN R7, and UN R6? When does each apply?

**Answer:**

| Regulation | Subject | Applies To |
|---|---|---|
| **UN R112** | Headlamps producing an asymmetric low/high beam | Main headlamps (projector, reflector, LED, HID) |
| **UN R7** | Position, stop, end-outline lamps | Sidelights, tail lights, brake lights, DRL |
| **UN R6** | Direction indicators | Turn signals, front/rear/side, hazard lamps |

**UN R112** focuses on the asymmetric beam pattern — the characteristic cut-off line that limits glare while providing maximum road illumination.

**UN R7** covers lamps that signal the vehicle's position and braking status — requires specific intensity ranges and colour coordinates for white (front) and red (rear) lamps.

**UN R6** regulates how turn signals operate — critically the flash frequency (60–120 flashes/minute) and ON-time ratio (40–60%), as well as minimum luminous intensity at specified angles.

---

## Q3. What is the B50L test point and why is it critical in R112?

**Answer:**
**B50L** stands for: **B** = beam, **50** = 50 cm above the horizontal reference line, **L** = to the left of the vertical reference line (by 75 cm at 25 m distance).

It represents the position of an oncoming driver's eyes — the glare zone. A passing car's driver sits at approximately this height and position relative to your headlamp's projection.

In UN R112, B50L has a **maximum limit of 17 cd**. This means your headlamp must NOT exceed 17 candela in the direction of the approaching driver — to prevent blinding oncoming traffic.

B50L is the single most critical pass/fail point in R112:
- If B50L > 17 cd → **automatic failure** regardless of all other test points
- There is no tolerance or averaging allowed on B50L
- Common causes of B50L failure: stray light above the cut-off line, incorrect shield position, lens scatter

---

## Q4. Explain the E-mark format with an example.

**Answer:**
The E-mark is applied to components approved under the UNECE (1958 Agreement) Type Approval system.

**Format:** `E[country code] R[regulation] [approval number] [function code]`

**Example:** `E4 R112 00521 A/B`

Decoded:
- **E4** → Approved by Netherlands (RDW) — country code 4
- **R112** → Under UN Regulation No. 112
- **00521** → Approval number assigned by RDW
- **A/B** → Function A (low beam) and B (high beam) both included

The mark is physically embossed or moulded onto the lamp. Every production unit must bear this mark — it is the proof of compliance visible to market surveillance authorities.

**Common country codes:**
- E1 = Germany (KBA)
- E2 = France
- E4 = Netherlands (RDW)
- E11 = United Kingdom (VCA — pre-Brexit)
- E43 = Japan

---

## Q5. What is Conformity of Production (COP) and what happens if COP fails?

**Answer:**
**COP (Conformity of Production)** is the ongoing obligation of the manufacturer to ensure that every unit produced continues to meet the requirements of the type approval. It is not just a one-time test — it must be maintained throughout the life of the product in production.

**COP process:**
- Production samples randomly selected at defined frequency (typically 3 per year)
- Samples tested against photometric and other requirements
- Acceptance band: ±20% of photometric limits (e.g., if minimum is 60 cd, COP pass is ≥ 48 cd)

**If COP fails:**
1. **Immediate containment:** Affected production lots are placed on hold
2. **Notification to Approval Authority:** Mandatory within a specified period (typically 30 days)
3. **Root cause analysis:** Identify cause — LED batch variation, tooling change, material change
4. **Corrective action plan:** Submitted to AA
5. **Consequences if not resolved:**
   - AA may **suspend** the type approval
   - If suspension is sustained: **withdrawal** of approval
   - Manufacturer must withdraw product from market
   - **Recall** of affected vehicles/components may be mandated

COP failure is a serious regulatory event — it can lead to significant financial penalties and reputational damage.

---

## Q6. What are the flash frequency requirements in UN R6 and how do you measure them?

**Answer:**
**Requirements:**
- Flash frequency: **60 to 120 flashes per minute** (no single reading outside this range during stabilised operation)
- ON-time ratio: **40% to 60%** of the total flash cycle (the lamp must be ON for no less than 40% and no more than 60% of each cycle)

**Measurement method:**
1. Connect oscilloscope or data logger to the lamp (measure voltage or current waveform)
2. Operate the direction indicator in its normal flash mode
3. Allow thermal stabilisation (no measurement during initial warm-up flash)
4. Measure at minimum 10 consecutive flash cycles in stabilised state
5. Calculate average frequency and ON-time ratio

**Example calculation:**
- If one full flash cycle lasts 600 ms: Frequency = 60,000 ms ÷ 600 ms = 100 flashes/min ✓
- ON-time within cycle: must be between 240 ms and 360 ms (40%–60% of 600 ms)

**Common failure causes:**
- Capacitor tolerance in flasher relay
- LED characteristic incompatible with older relay flasher
- BCM software timer drift with temperature

---

## Q7. What is the difference between luminous intensity (cd) and luminance (cd/m²)? When do you use each?

**Answer:**

| Quantity | Unit | Definition | Used For |
|---|---|---|---|
| **Luminous Intensity** | Candela (cd) | Light power per unit solid angle in a specific direction | Regulatory photometric requirements (R112, R7, R6 test points) |
| **Luminance** | cd/m² | Intensity per unit projected surface area (surface brightness) | Appearance quality, glare from surface, display brightness |

**Luminous intensity (cd)** answers: "How bright is the lamp when you look directly at it from that angle?" — used for all regulatory pass/fail in lighting regulations.

**Luminance (cd/m²)** answers: "How bright does the lamp surface appear?" — used for assessing whether a lamp is aesthetically uniform, verifying homogeneity of LEDs in a cluster, or measuring display visibility.

**Practical example:** A stop lamp specification in R7 says: minimum 60 cd at HV. This is measured on a goniophotometer as luminous intensity. The internal LEDs might show 50,000 cd/m² — visible with a luminance camera — but this is a quality metric, not the regulatory metric.

---

## Q8. What is UN R48 and what does it regulate?

**Answer:**
UN Regulation No. 48 is the **installation regulation** — it specifies where and how lighting devices must be installed on the complete vehicle. While individual lamp regulations (R112, R7, R6) govern the lamp as a component, R48 governs the system on the vehicle.

**Key areas covered by R48:**
1. **Mandatory lamps:** Which lamps must be present for each vehicle category (M1, N1, etc.)
2. **Height:** Minimum and maximum mounting height from the ground (e.g., headlamps: 500–1200 mm)
3. **Lateral position:** Lamps must be within 400 mm of the vehicle edge
4. **Separation:** Indicators must be at least 600 mm apart (inner edge to inner edge)
5. **Visibility angles:** Each lamp must be visible from the geometric angles specified
6. **Combined lamps:** Rules on combining multiple functions in one housing
7. **LED retrofit:** Restrictions on fitting LED lamps into non-LED-approved housings

**R48 assessment is done on the vehicle — it is a system-level check performed as part of the Whole Vehicle Type Approval (WVTA), not just component level.**

---

## Q9. What is the difference between Type Approval and Self-Certification? Give examples.

**Answer:**

| Aspect | Type Approval (ECE, WVTA) | Self-Certification (USA FMVSS) |
|---|---|---|
| Who tests | Accredited Technical Service (third party) | Manufacturer (no mandatory third party) |
| Who grants approval | Government Approval Authority | Manufacturer (self-declares compliance) |
| Pre-market check | Yes — product must pass before sale | No — product enters market immediately |
| Post-market | Market surveillance by authorities | NHTSA compliance testing, recall orders |
| Mark | E-mark on product | DOT mark on product |
| Example markets | EU, Russia, Japan, India, Australia | USA, Canada (partly) |

**Type Approval (ECE/WVTA):**
- Manufacturer applies to an AA (e.g., KBA Germany)
- Technical Service performs tests, issues report
- AA issues certificate
- Only then can the product be sold in that market

**Self-Certification (FMVSS 108 / USA):**
- Manufacturer designs and tests product internally (or hires private lab)
- Declares product meets FMVSS 108 standard
- Applies DOT mark to product
- No pre-market authority review
- NHTSA may test products from market and issue safety recall if non-compliant

**Risk difference:** Self-certification pushes compliance risk onto the manufacturer — if NHTSA finds non-compliance after sale, the manufacturer bears full recall cost and legal liability.

---

## Q10. How do you manage a regulatory change (regulation amendment) that affects a product already in production?

**Answer:**
A structured approach is essential:

**Step 1 — Detection:** Monitor WP.29 working party publications, regulation amendment series. Subscribe to UNECE, national AA, and industry body (e.g., GTB — Global Technical Regulations forum) newsletters.

**Step 2 — Impact assessment:** Read the amended regulation text. Extract new/changed clauses. Create an impact matrix: which products are affected, which tests must be repeated.

**Step 3 — Grandfathering review:** Determine if existing approvals remain valid under the old series, or if the new series is mandatory within a transition period.

**Step 4 — Planning:**
- If re-test required: Schedule with Technical Service
- If documentation update only: Update Technical File and file extension
- If no impact: Document this conclusion for audit trail

**Step 5 — Certification update:** File TA extension or new application as needed.

**Step 6 — Communicate:** Notify OEM customers who use the product in their vehicle approvals — they need to update their vehicle TAC too.

**Step 7 — Go-forward design:** Update engineering design rules and test plans for all future new products to reflect the new amendment series from outset.

---

## Q11. What is an Adaptive Front-lighting System (AFS) and which regulation governs it?

**Answer:**
AFS (Adaptive Front-lighting System) is a headlamp system that **adjusts the beam pattern dynamically** based on driving conditions, using either mechanical swivelling of the projector optic or selective activation of LED matrix pixels.

**Governed by:** UN Regulation No. 123 (R123)

**AFS Beam Classes:**

| Class | Condition | Behaviour |
|---|---|---|
| Class C | Town/City | Wider horizontal spread, illuminates pavements and road signs |
| Class V | Rural | Standard asymmetric beam — baseline for comparison |
| Class E | Motorway/Highway | Extended range (higher right-side cut-off), more light further ahead |
| Class W | Wet road | Reduced upward light to minimise glare from wet surface reflection |
| Class T | Adverse weather | Low cut-off, wider spread — anti-dazzle in fog/rain/snow |

**Key AFS requirements:**
- Swivel up to ±15° from neutral based on steering angle
- Neutral position must produce an R112-compliant beam
- Vertical levelling compensation (auto-levelling for load changes)
- Fail-safe: AFS failure must return headlamp to fixed neutral position (at least R112 compliant)
- Matrix LED systems: Each pixel zone must be individually controllable and contribute correctly to each beam class pattern

---

## Q12. What are the colour requirements for automotive lamps and how are they verified?

**Answer:**
Each lamp function has a required colour defined by boundaries on the **CIE 1931 chromaticity diagram** (x, y coordinates):

| Function | Colour | Approx. x, y boundary |
|---|---|---|
| Headlamp / DRL / front position | White | Within white region (x < 0.500, y > 0.150) |
| Rear position / stop lamp | Red | y ≤ 0.335, toward high x |
| Direction indicator (ECE) | Amber | 0.540 ≤ x ≤ 0.610, y within amber triangle |

**Verification method:**
1. Use a **spectroradiometer** to measure the spectral power distribution (SPD) of the lamp at the axis (0°, 0° direction)
2. Software calculates CIE x, y coordinates from the SPD
3. Plot x, y on the CIE diagram
4. Confirm coordinates fall within the regulation boundary for the required colour
5. Repeat measurement at extreme geometric visibility angles (colour must remain valid at all angles, not just axis)

**Important:** Colour boundaries must be met at all supply voltages tested (min and max), not just nominal. LED colour can shift with current — especially amber LEDs using InGaN + phosphor.

---

## Q13. What is the difference between a Type Approval Extension and a new Type Approval?

**Answer:**

| Situation | Action Required | Why |
|---|---|---|
| New variant: Halogen replaced by LED same housing | Extension | Same basic type, different light source — need re-test |
| Different colour of non-optical housing | Extension or amendment | Minor change — may not need re-test, depends on authority |
| Completely new optical design (different reflector/lens) | New application | New type |
| Adding a new vehicle model as installation reference | Extension | Additional application context |
| Regulation amendment makes old approval invalid | New application under new amendment series | Cannot merely extend |

**Extension process:**
- Manufacturer applies to same Approval Authority that granted original TAC
- Submits: Description of change, test reports for changed elements, updated information document
- Authority issues an extended TAC (same number with /01 or subsequent suffix)
- Original approval number is maintained

**Key principle:** If the change is within the approved type's boundary (same fundamental optical design), extension is possible. If the fundamental optical prescription changes, a new application is the correct path.

---

## Q14. What are Technical Services? How are they accredited?

**Answer:**
**Technical Services (TS)** are accredited third-party organisations (laboratories or inspection bodies) authorised to perform the type tests under ECE regulations on behalf of the Approval Authority.

**Role:**
- Witness or perform all required tests specified in the regulation
- Issue signed test reports confirming pass/fail against each requirement
- Test reports are submitted by the manufacturer to the AA as part of the TA application

**Accreditation:**
- **ISO/IEC 17025:** Testing laboratory competence — required for all measurement activities
- **ISO/IEC 17020:** Inspection body — required for inspection activities
- The AA specifically designates each TS for each regulation they are authorised to cover (e.g., designated for R112 ≠ automatically designated for R7)
- Accreditation is assessed and renewed by national accreditation bodies (e.g., DAkkS in Germany, UKAS in UK, RvA in Netherlands)

**Examples of Technical Services:**
- TÜV Rheinland / TÜV SÜD (Germany, global)
- Applus IDIADA (Spain)
- UTAC (France)
- Millbrook (UK)
- TRL (Transport Research Laboratory, UK)
- ARAI (India — also acts as Approval Authority)

---

## Q15. What is the goniophotometer and how does it work?

**Answer:**
A **goniophotometer** is the primary instrument used to measure the **luminous intensity distribution** (candela values at defined angles) of a lamp.

**Principle:**
1. The lamp is mounted on a precision motorised turntable (or the detector moves around the lamp)
2. A calibrated photodetector is positioned at a fixed distance (25 m for R112 headlamps)
3. The lamp rotates through a defined angular range in both horizontal and vertical axes
4. At each angle position, the detector records luminous intensity (cd)
5. Software maps the full angular distribution and extracts values at regulation test points (HV, B50L, 50R, etc.)

**Key measurement parameters:**
- Test distance: 25 m (far-field, compliant with regulation)
- Angular resolution: 0.25°–1° steps (higher resolution for precise cut-off analysis)
- Supply voltage: Precisely regulated (13.2V ± 0.1V for 12V systems)
- Thermal stabilisation: 30–60 minutes before measurement (critical for LED)

**Output:**
- Table of intensity (cd) vs angle (H°, V°)
- Automatic comparison against R112 / R7 / R6 limits
- Pass/fail report

---

## Q16. What is the Technical File in automotive homologation? What must it contain?

**Answer:**
The **Technical File** (also called Type Approval Dossier or Information Package) is the complete documentation submitted to an Approval Authority to support a type approval application.

**Core contents for a lighting component (e.g., R112 headlamp):**

1. **Information Document (Annex I format):**
   - Manufacturer identity
   - Product description (lamp category, light source type, supply voltage)
   - Reference drawings
   - List of variants and versions

2. **Test Reports:**
   - Photometric test report (all R112 test points, signed by TS)
   - Colour measurement report (CIE chromaticity)
   - Environmental test reports (vibration, thermal, IP rating)
   - EMC report (if LED — under R10)

3. **Engineering Drawings:**
   - Assembly cross-section drawing
   - Illuminated area drawing showing reference axis
   - Wiring diagram (for LED/AFS)

4. **COP Plan:**
   - Sampling frequency, test methods, acceptance criteria
   - Quality management reference (IATF 16949)

5. **Manufacturer Declaration:**
   - Signed declaration that submitted samples are representative of production intent

The Technical File is the legal foundation of the type approval. **Any product change after approval that is not documented in the Technical File is a compliance violation.**

---

## Q17. Explain the key differences between ECE R112 and FMVSS 108 for headlamps.

**Answer:**

| Feature | ECE R112 | FMVSS 108 (USA) |
|---|---|---|
| Approval system | Type Approval — government issues certificate | Self-certification — manufacturer declares |
| Beam pattern | Asymmetric cut-off required (sharp horizontal cut-off line) | Not required to have sharp cut-off |
| Glare test point | B50L — maximum 17 cd | No direct B50L equivalent |
| Test distance | 25 m (far-field goniometer) | Specified test points at different distances |
| Colour indicator | Amber only (front and rear indicators) | Amber (front), red or amber (rear) |
| LED approval | Specific LED module approval under R112 | LED permitted with self-cert |
| DRL | Referenced in R87 / R7 | Not federally mandated |
| Mark | E-mark | DOT mark |

**Key practical difference:** R112's B50L glare limit is more restrictive — it forces headlamp designers to create a precise, sharp cut-off line. FMVSS 108 allows more flexibility in beam shaping but uses different test zones.

A product designed to pass R112 will generally NOT automatically pass FMVSS 108 at every test point — a dual compliance analysis is always needed.

---

## Q18. What tests are included in a full R112 Type Approval?

**Answer:**
A complete R112 type test at a Technical Service includes:

| Test | Description |
|---|---|
| **Visual inspection** | Verify marking, construction, aim mechanism, lens material |
| **Dimensional check** | Verify dimensions against information document drawings |
| **Photometric test (low beam)** | Full test point scan: B50L (max), HV, 50R, 75R, 25R, 25L, 50L, etc. |
| **Photometric test (high beam)** | If combined headlamp includes high beam |
| **Colour measurement** | CIE x, y coordinates — confirm white boundary |
| **Cut-off line assessment** | Grade assessment - sharp cut-off on screen photograph |
| **Glare verification** | B50L cannot exceed 17 cd |
| **Thermal stabilisation** | LED warm-up protocol verified before measurement begins |
| **Min/max voltage** | Photometric at minimum and maximum supply voltage (9V and 16V for LED) |
| **Aim mechanism** | Verify aim adjustment range (±0.17° minimum) |
| **Replacement bulb test** | If replaceable light source: test with replacement bulb |
| **EMC (R10)** | LED headlamps — radiated and conducted emissions |

**Duration of type test at TS: Typically 2–4 days for a full headlamp TA including EMC.**

---

## Q19. What is COP tolerance and how does it affect lamp design?

**Answer:**
**COP tolerance** is the production variation band allowed for certified products — it recognises that mass production cannot achieve exactly the same value every time.

**Standard COP tolerance in lighting regulations:**
- Photometric minimum limits: Production samples must achieve ≥ **80% of the regulation minimum**
- Photometric maximum limits: Production samples must achieve ≤ **120% of the regulation maximum**
- Colour coordinates: **No relaxation** — must remain within regulation boundary
- Flash frequency: **No relaxation** — 60–120/min mandatory

**Design implication — Design-to-manufacture margin:**
If R7 requires stop lamp minimum 60 cd, the production COP minimum is 48 cd. However, if the lamp is designed to exactly 60 cd at nominal conditions, production variation (LED flux tolerance ±10%, lens transmission variation ±5%) could easily push production samples below 48 cd.

**Best practice: Design with margin:**
- Target value = Regulation minimum × (1 / COP factor) × (1 + manufacturing variation margin)
- For a 60 cd minimum: Target design value ≈ 60 ÷ 0.80 × 1.15 ≈ 86 cd at nominal

This means the lamp is designed to deliver ~86 cd so that in worst-case production, it delivers ≥ 48 cd (COP minimum).

Design margin is the key tool that prevents COP failures from reaching the market.

---

## Q20. Walk me through how you would approach a Type Approval for a new LED stop lamp under UN R7.

**Answer:**
A structured step-by-step process:

**Step 1 — Regulation extraction:**
Read UN R7 Amendment 7 in full. Create a requirements matrix: every clause mapped to: what it requires, how it is tested, pass criterion, responsible person.

**Step 2 — Design review:**
Verify design meets R7 requirements at nominal conditions (internal simulation and pre-test). Key checks: HV ≥ 60 cd, max ≤ 185 cd, stop:position ratio ≥ 5:1, colour within red boundary.

**Step 3 — Internal pre-test:**
Run the lamp on internal goniometer. Measure all R7 test points. Confirm pass with margin (target: ≥ 15% above minimum at all points).

**Step 4 — Technical File preparation:**
- Complete Annex I Information Document with all required fields
- Gather engineering drawings (assembly, illuminated surface, wiring)
- Write COP plan (sampling: 3 per year, test method: internal goniometer per regulated procedure)
- Prepare manufacturer declaration

**Step 5 — Technical Service booking:**
Select a TS designated for R7 (e.g., TÜV Rheinland). Book test window 10–12 weeks ahead. Ship samples with packing list and information document.

**Step 6 — Type test witness:**
Attend TS as applicant representative. Verify test setup is correct (distance, voltage, aim). Monitor all measured values in real time.

**Step 7 — Technical File submission:**
Compile complete Technical File with TS test report. Submit to chosen Approval Authority (e.g., KBA E1 or RDW E4). Pay application fee.

**Step 8 — TAC receipt and product marking:**
On receipt of certificate, confirm approval number. Arrange tooling change to incorporate correct E-mark into lamp housing mould.

**Step 9 — COP programme start:**
Register product in COP calendar. First COP test within 12 months of production start.

**Total timeline: Approximately 16–24 weeks from internal pre-test to TAC receipt.**

---

*File: 06_interview_qa.md | automotive_homologation series | 20 detailed interview Q&A*
