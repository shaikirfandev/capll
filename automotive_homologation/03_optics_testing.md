# Optics Testing for Automotive Lighting
## Photometry | Goniophotometry | Colour Measurement | Lab Setup | Test Protocols

---

## 1. Fundamental Photometric Quantities

Understanding lighting regulations requires mastery of four core photometric quantities:

### 1.1 Luminous Flux — Lumen (lm)
**Definition:** Total light output from a source, integrated over all directions.
- Think of it as the "total power of light"
- Measured with an **integrating sphere**
- Used to characterise headlamp bulbs, LED modules
- Example: H7 halogen bulb ≈ 1500 lm; LED replacement ≈ 2000 lm

**Formula:** $\Phi = \int I(\omega) \, d\omega$ (integral of intensity over solid angle)

### 1.2 Luminous Intensity — Candela (cd)
**Definition:** Luminous flux per unit solid angle in a specific direction.
- The "brightness in a specific direction"
- Measured at each test point in a goniophotometer
- The primary measurement unit used in R112, R7, R6 requirements
- Example: Stop lamp must deliver ≥ 60 cd at the 0°, 0° test point

**Formula:** $I = \frac{d\Phi}{d\omega}$ [cd = lm/sr]

### 1.3 Illuminance — Lux (lx)
**Definition:** Luminous flux received per unit area at a surface.
- The "brightness at a target surface"
- Used for road surface illumination calculations and cornering lamp (R119) requirements
- Example: 1 lux = 1 lm/m²

**Formula:** $E = \frac{\Phi}{A} = \frac{I}{r^2}$ [lx = lm/m² = cd/m²]

**Inverse square law:** Illuminance decreases with square of distance: $E = I / r^2$

At 25 m distance, a 12 cd source gives:
$E = 12 / 25^2 = 12 / 625 = 0.0192$ lx

### 1.4 Luminance — Candela per square metre (cd/m²)
**Definition:** Luminous intensity emitted per unit projected area of a surface.
- The "perceived brightness of a surface as seen by the eye"
- Used for glare assessment, instrument cluster display brightness
- Measured with a **luminance camera** or **spot luminance meter**
- Example: Dashboard displays ≤ 15,000 cd/m² (not to blind driver)

**Formula:** $L = \frac{d^2\Phi}{dA \cdot d\omega}$ [cd/m²]

---

## 2. Photometric Test Points — R112 Low Beam Grid

The photometric test grid is defined on a screen at 25 m from the headlamp reference centre. All points are referenced from the H-H (horizontal) and V-V (vertical) reference lines.

### 2.1 Point Nomenclature
- **H-H line:** The horizontal reference line at headlamp mounting height
- **B50L:** Point 50 cm above H-H, 75 cm to the left (most critical glare point)
- **HV:** The intersection of H-H and V-V — the "hot vertical" point representing ahead-of-vehicle centre

### 2.2 Test Point Coordinates at 25 m Screen

| Point | Position on Screen (at 25m) | Description |
|---|---|---|
| B50L | 1.25m above H, 3.75m left of V | Glare zone — max 17 cd |
| HV | At H-H / V-V intersection | Ahead-centre |
| 50R | 12.5 cm below H, 37.5 cm right of V | Right-side hot zone |
| 75R | 12.5 cm below H, 56.25 cm right of V | Far right hot zone |
| 25R | 12.5 cm below H, 18.75 cm right of V | Near right hot zone |
| 50L | 12.5 cm below H, 37.5 cm left of V | Left boundary |
| 25L | 12.5 cm below H, 18.75 cm left of V | Left zone |
| 15D5L | 15 cm below H, at 5° left | Nadir check |

> The angular equivalents: at 25 m, 1° angle = 43.7 cm displacement on screen.
> B50L: 0.5°U = 21.8 cm up, 1.5°L = 65.5 cm left.

---

## 3. Goniophotometer — Far-Field Measurement

### 3.1 What is a Goniophotometer?
A goniophotometer measures the **luminous intensity distribution** of a lamp by recording candela values at many angular positions automatically.

**Working principle:**
1. Lamp fixed on turntable at centre of rotation
2. Detector (photocell) at fixed distance (25 m for headlamps per R112)
3. Lamp rotates in horizontal and vertical axes
4. At each angular position, detector reads intensity
5. Software records intensity (cd) vs angle (θ_H, θ_V) data table

### 3.2 Types of Goniophotometers

| Type | Description | Usage |
|---|---|---|
| **Type A** | Lamp rotates in azimuth, tilt changes elevation | Small sources |
| **Type B** | Lamp rotates in elevation, photocell moves in azimuth | Large lamps, headlamps |
| **Type C** | Lamp vertical axis, photocell sweeps | General lighting |
| **Moving detector** | Lamp fixed, detector on arm rotates | Short-range automotive |

**For automotive headlamps:** Type B goniophotometer is most common. The headlamp is mounted at a fixed elevation and rotated through azimuth angles. This simulates viewing the lamp from all horizontal directions.

### 3.3 Far-Field vs Near-Field Measurement

| Aspect | Far-Field (Goniophotometer) | Near-Field (Luminance camera) |
|---|---|---|
| Distance | 25 m (R112) or 10 m | Focused on lamp surface |
| Measurement | Luminous intensity (cd) | Luminance (cd/m²) |
| What it gives | Candela vs angle distribution | Surface brightness map |
| Usage | Regulatory compliance (R112, R7, R6) | Appearance, glare from lamp surface |
| Equipment | Detector + turntable | Imaging luminance camera |

### 3.4 Test Procedure on Goniophotometer

**Step 1 — Lamp preparation:**
- Mount lamp on standard fixture (or vehicle front end for full-car measurement)
- Zero-set the H-H and V-V reference lines using spirit level and laser alignment
- Connect correct supply voltage (13.2V ± 0.1V for 12V systems)

**Step 2 — Thermal stabilisation:**
- Switch lamp ON
- Monitor luminous flux output — wait until change is < 3% over 5 minutes
- **LED headlamps:** Typically 30–60 minutes warm-up. Do NOT start measurement before stabilisation.
- **Halogen:** Typically 15 minutes

**Step 3 — Zero reference measurement:**
- Record detector reading at HV with known calibration source
- Apply correction factor if needed for ambient temperature

**Step 4 — Angular scan:**
- Programme goniometer to sweep test points (automated)
- Resolution for R112: Typically 0.25° steps from –20° to +20° V, –10° to +80° H
- Scan speed limited by lamp response time (LED can scan faster)

**Step 5 — Result extraction:**
- Software maps intensity (cd) to each test point (B50L, HV, 50R, etc.)
- Compare against regulation limits
- Generate report with pass/fail for each test point

---

## 4. Integrating Sphere — Total Luminous Flux (lm)

### 4.1 Principle
An integrating sphere is a hollow sphere with **highly reflective white interior coating** (barium sulphate or PTFE). Light bounces around and integrates uniformly — the detector measures a sample of the uniform flux independent of lamp direction.

**Usage in automotive lighting:**
- Measure total lumen output of LED module or bulb
- Characterise light source for design purposes
- Measure efficacy (lm/W)
- NOT used directly for R112/R7 compliance (those require goniophotometer)

### 4.2 LED Module Measurement
1. Place LED module at sphere port
2. Power module at rated voltage and current
3. Wait for thermal stabilisation on heat sink
4. Read detector output → convert to lumens using calibration factor
5. Record: Total flux, colour coordinates, colour rendering index (CRI)

---

## 5. Spectroradiometer — Colour Measurement

### 5.1 What it Measures
A spectroradiometer measures the **spectral power distribution (SPD)** of light — how much energy is emitted at each wavelength across the visible spectrum (380–780 nm).

From the SPD, the following are calculated:
- **x, y chromaticity coordinates** (CIE 1931 colour space)
- **Correlated Colour Temperature (CCT)** in Kelvin
- **Colour Rendering Index (CRI)**
- **Peak wavelength** (dominant colour for indicator lamps)
- **Purity** (how saturated the colour is)

### 5.2 CIE 1931 Chromaticity Diagram and Automotive Colour Zones

The CIE x,y diagram maps all visible colours on a 2D plane. ECE regulations define boundaries for each lamp colour:

```
     y
  0.8│       Green
     │    ╔════════╗
  0.6│    ║        ║  (amber zone)
     │White ║       ║
  0.4│ ╔══╗║        ║
     │ ║  ║╚════════╝
  0.2│ ╚══╝           (red zone)
     │
  0.0│────────────────
     0.2  0.3  0.4  0.5  0.6  0.7  x
```

**Colour Boundaries Table:**

| Colour | x range | y range | Usage |
|---|---|---|---|
| White | 0.270–0.500 | 0.150–0.440 | Front position, DRL, headlamp |
| Amber | 0.540–0.610 | calc. from boundaries | Front/rear indicators |
| Red | x ≥ 0.643 (approx) | y ≤ 0.335 | Rear position, stop lamp |
| Yellow-green | 0.320–0.420 | 0.480–0.600 | Emergency vehicles (not standard automotive) |

> Note: The exact boundaries are specified per regulation annex. Always refer to the published regulation text — these values are approximate.

### 5.3 Colour Test Procedure
1. Align spectroradiometer with lamp axis (0°, 0° direction)
2. Stabilise lamp thermally
3. Measure SPD at test axis
4. Software calculates x, y coordinates
5. Plot coordinates on CIE diagram — verify within regulation boundary
6. Measure at extreme geometric visibility angles (colour must remain within boundary at all angles)

---

## 6. Near-Field Luminance Camera System

### 6.1 Purpose
Near-field luminance cameras capture a **2D image of the lamp surface** where each pixel value represents luminance (cd/m²).

**Automotive applications:**
- Assessing lamp appearance quality
- Verifying uniform illuminated surface (no dark spots)
- Measuring luminance of individual LEDs within a cluster
- Evaluating glare potential from high-luminance zones
- Photometric simulation validation (compare measurement vs CAD simulation)

### 6.2 System Components
- Camera: High dynamic range CCD or CMOS (typically 14–16 bit)
- Lens: Telecentric or standard objectivetive
- Filter wheel: V(λ) photopic filter (matches human eye spectral sensitivity)
- Software: Maps pixel values to luminance (cd/m²)
- Calibration: Traceable calibration source (integrating sphere at known luminance)

### 6.3 Test Protocol for Near-Field Measurement
1. Set lamp at correct aim angle
2. Camera at set distance (e.g., 0.5 m to 2 m)
3. Stabilise lamp thermally
4. Capture high dynamic range image (HDR — multiple exposures)
5. Software applies calibration map → luminance image
6. Export luminance data:
   - Peak luminance (max cd/m²)
   - Average luminance across illuminated area
   - Luminance uniformity ratio (max/min)
   - Hot-spot coordinates

---

## 7. Test Environment Requirements

### 7.1 Dark Room Requirements
- **Background stray light:** < 0.1% of the lamp's flux at test distance
- Walls and ceiling: Matte black (non-reflective) to prevent stray reflections
- Room temperature: 20°C ± 5°C (default condition for ECE measurement)
- Vibration isolation: Goniometer and lamp must be on stable platform
- Air currents: Avoid drafts that could disturb lamp temperature

### 7.2 Photometer (Detector) Calibration
- Calibrated against national standard using traceability chain
- Calibration certificate must be current (typically annual recalibration)
- Correction factor for lamp colour (photometer spectral response should match V(λ) — human eye response)
- Temperature coefficient: Photometer reading corrects for ambient temp drift

### 7.3 Power Supply
- Regulated DC supply: ±0.1V stability for 12V lamps (13.2V ± 0.1V)
- LED drivers tested at min and max supply: 9V and 16V for 12V systems
- Current monitoring: Confirm lamp is drawing rated current
- For transient sensitivity: ISO 7637 generator connected during immunity tests

---

## 8. Environmental Tests in Homologation

Beyond pure photometric testing, lamps must pass environmental tests to prove durability:

### 8.1 Vibration Test (ISO 16750-3)
- Sinusoidal and random vibration profiles
- Purpose: Ensure filament or LED module survives road vibration
- After vibration: Photometric test must still pass (no bulb shift, lens crack)

### 8.2 Thermal Shock and Cycling (ISO 16750-4)
- Temperature range: –40°C to +85°C (or +105°C for underbonnet)
- Cycles: Typically 200–500 cycles
- After test: Visual inspection, photometric check

### 8.3 Dust and Water Ingress (IP Rating — IEC 60529)
- Most automotive lamps: IP55 (dust protected, water jets)
- Headlamps: IP67 or IP69K for sealed units
- After water test: No water ingress into light chamber, function retained

### 8.4 UV Ageing (SAE J2412 / ISO 4892)
- Lens material (polycarbonate) must resist UV yellowing
- Test: 1000+ hours UV exposure in xenon arc weatherometer
- After test: Transmittance must remain > 90% (lens must not yellow and reduce output)

### 8.5 Thermal Resistance of Lens and Housing
- Lamp on continuously: Housing surface temperature measured
- Must not exceed limits to prevent contact burns (especially for external access surfaces)
- LED junction temperature: Must remain within manufacturer's rating (typically Tj < 150°C)

---

## 9. Common Photometric Failures and Root Causes

| Failure | Test Point Failed | Root Cause | Corrective Action |
|---|---|---|---|
| Excessive glare | B50L > 17 cd | Stray light above cut-off line; reflector contamination | Shield adjustment; reflector re-design; lens diffusion |
| Low hot-zone intensity | HV, 50R below minimum | Under-driven LED; thermal derating; wrong aim | Increase LED drive current; improve thermal design; recalibrate aim |
| Colour outside amber zone | x,y outside boundary | LED bin shift; wrong phosphor | Change LED bin specification; add colour filter |
| Flash frequency out of range | R6 flash > 120/min | Timer circuit tolerance; LED driver pulse incompatibility | Tune flash timer; add load resistor |
| Production sample below minimum | Any R7/R6 point | Manufacturing variation; warped lens; LED batch variation | Tighten LED procurement spec; improve lens tooling |
| Luminance uniformity poor | Not regulatory but QA | LED pitch too wide; secondary optic gap | Redesign secondary optic; add mixing chamber |

---

## 10. Photometric Simulation Tools (Pre-Test Design)

Modern headlamp development uses optical simulation before physical prototyping:

### 10.1 Ray-Tracing Software
- **LucidShape (Synopsys), OptiCad, SPEOS (Ansys), TracePro, FRED**
- Simulates how light rays from LED source interact with reflector, lens, projection optics
- Output: Predicted far-field intensity distribution (same format as goniophotometer)
- Accuracy: Typically ±15–25% of measured values

### 10.2 Workflow:
1. Import LED source data (candela distribution from datasheet)
2. Model reflector geometry (freeform surface from CAD)
3. Assign material properties (reflectivity, transmission)
4. Run ray trace (typically 10–100 million rays)
5. Extract intensity at R112 test points
6. Iterate: Design — Simulate — Check test points — Modify
7. Prototype only when simulation shows margin above requirement

### 10.3 LED Source Modelling
- LED manufacturers provide TonkaTrunk or LDT source models
- Input to optical simulation: near-field goniometric data of LED die
- Critical for LED lamps: LED beam angle, emission area size affects optic focal distance

---

## 11. Photometric Records and Traceability

For a Type Approval submission, photometric records must demonstrate:

**Required documentation:**
- Calibration certificate for all measurement equipment (photometer, power supply, spectroradiometer)
- Traceability chain to national standard (e.g., PTB in Germany, NPL in UK)
- Stabilisation records (time-stamped luminous flux vs time plot showing stabilisation)
- Test point data table with all measured cd values vs requirements
- Cut-off line photograph (for R112 — screen photograph showing beam pattern)
- Colour coordinate plot on CIE diagram
- Signed test report by accredited technical service witness

---

*File: 03_optics_testing.md | automotive_homologation series*
