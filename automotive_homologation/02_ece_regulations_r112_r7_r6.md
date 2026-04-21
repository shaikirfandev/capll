# ECE Regulations — R112, R7, R6, R48, R10 & R123
## Deep-Dive Technical Study Guide for Lighting Homologation Engineers

---

## 1. UN Regulation No. 112 — Headlamps with Asymmetric Low Beam (and High Beam)

### 1.1 Scope
UN R112 covers **motor vehicle headlamps** that produce:
- An **asymmetric low beam** (passing beam) with a distinct cut-off line
- An optional **high beam** (driving beam)

Light sources covered:
- Filament (halogen) lamps
- Gas discharge (HID/Xenon) lamps
- **LED** light sources (non-replaceable modules)
- Laser light source
- Combination/multi-function lamps

> Key distinction: R112 applies to **Category A** headlamps (asymmetric) as opposed to R98 (symmetric fog) or R123 (AFS).

---

### 1.2 Photometric Test Setup

**Standard test distance:** 25 m (far-field measurement)

**Screen layout at 25 m:**
```
                  ←  B50L  →  HV →  50R, 75R, 25R
                              │
  ─────────────────────────── │ ─────────────── (h–h line, horizontal cut-off reference)
                              │
           50L → │            │
  25L ←         │            │ (cut-off line — drops ≥15° on left side)
                              │
```

**Key test points for R112 low beam:**

| Zone | Test Point | Min Intensity (cd) | Max Intensity (cd) |
|---|---|---|---|
| Glare zone | B50L | — | **17 cd** |
| Hot zone | HV | 12 | — |
| Hot zone | 50R | 12 | — |
| Hot zone | 75R | 12 | — |
| Hot zone | 25R | 6 (halogen) / 6 (LED) | — |
| Left side | 50L | — | 15 cd |
| Elbow region | 25L | — | depends |
| Upper zone | 15U | — | restricted |

> B50L is the critical **glare point** — if the measurement here exceeds 17 cd, the headlamp fails regardless of all other results.

---

### 1.3 Cut-Off Line Requirements

The cut-off line is what makes asymmetric beams distinct:
- **Left side (traffic approach side):** Horizontal or slightly downwards cut-off
- **Right side (kerb side):** Inclined upward at 15° (right-hand traffic)
- **Kink point:** The transition point between horizontal and inclined part

**Gradient measurement:** The sharpness of the cut-off is assessed by measuring intensity change over a narrow angle band (typically 0.1°).

---

### 1.4 Aim Verification
Headlamps must be aimed correctly for photometric measurement. The reference mounting angle is specified in the product information document. Deviation during test must be within ±0.1°.

---

### 1.5 Installation Angles and Aim
- Headlamps are aimed downward by a specified percentage (e.g., 1.0% or 1.5% slope)
- Aiming adjustment mechanism must allow ±0.17° adjustment (minimum)
- AFS systems (R123) allow dynamic vertical aim correction for load

---

### 1.6 LED Specific Requirements under R112
- LED modules are **non-replaceable** — if the LED fails, the whole module is serviced
- Thermal stabilisation required: headlamp must be in stabilised thermal state before measurement
- **Thermal stabilisation test:** Run lamp until light output stabilises (typically 30-minute warm-up minimum)
- LED headlamps must pass photometric test at both min and max supply voltage (9V and 13V for 12V systems, 18V and 28V for 24V)
- Colour: White — chromaticity coordinates within CIE white boundary

---

### 1.7 Marking Required on R112 Approved Lamps

Example marking on lens or body:
```
e4 ★ R112 ★ 00001 A/B
   │         │      └── Function codes (A=low beam only, A/B=low+high)
   │         └────────── Approval number
   └──────────────────── Country code (e4 = Netherlands)
```

---

### 1.8 High Beam (Driving Beam) in R112

If the headlamp includes high beam, additional test points apply:
- **HV point:** Minimum 48 000 lux combined from all driven headlamps
- **Maximum:** No more than 350 000 lux at 7.5D (below cut-off) — glare limitation for high beam
- Colour: White

---

## 2. UN Regulation No. 7 — Position, Stop, End-Outline, and Daytime Running Lamps (CIE 2002)

### 2.1 Scope
R7 covers:
- **Front position lamps** (sidelights, parking lights)
- **Rear position lamps** (tail lights)
- **Stop lamps** (brake lights) — including central high-mounted stop lamp (CHMSL)
- **End-outline marker lamps** (trucks/buses > 1.8m wide)
- **Daytime Running Lamps (DRL)** under Revision 3 (alternative to R87)

---

### 2.2 Luminous Intensity Requirements

#### Front Position Lamps
| Parameter | Requirement |
|---|---|
| Minimum intensity | 4 cd at 0° H, 0° V |
| Maximum intensity | 60 cd at 0° H, 0° V |
| Colour | White (or amber for front indicators combined) |

#### Rear Position Lamps
| Parameter | Requirement |
|---|---|
| Minimum intensity | 4 cd at 0° H, 0° V |
| Maximum intensity | 12 cd at 0° H, 0° V |
| Colour | Red |

#### Stop Lamps (Standard — single stop lamp)
| Parameter | Requirement |
|---|---|
| Minimum intensity | 60 cd at 0° H, 0° V |
| Maximum intensity | 185 cd at 0° H, 0° V |
| Colour | Red |
| Ratio to rear position lamp | Minimum 5:1 (stop lamp must be substantially brighter) |

#### CHMSL (Central High-Mounted Stop Lamp)
| Parameter | Requirement |
|---|---|
| Minimum intensity | 22.5 cd (certain test points) |
| Maximum intensity | 100 cd |
| Colour | Red |

---

### 2.3 Geometric Visibility Angles for R7 Lamps

Lamps must emit light within specified minimum angular zones — the **geometric visibility** requirement ensures the lamp is visible from pedestrians and other road users at extreme angles.

**Rear position / stop lamp:**
- Horizontal: 45° inboard, 80° outboard
- Vertical: 15° above, 15° below (for height 750mm–1500mm mounting)

**Front position lamp:**
- Horizontal: 45° outboard, 10° inboard
- Vertical: 15° above, 10° below

---

### 2.4 Colour Requirements for R7 Lamps

All colour testing uses a **spectroradiometer** to determine chromaticity coordinates (x, y) in the CIE 1931 diagram.

**Red (rear position, stop):**
```
Boundary defined by:
y ≤ 0.335
z ≤ 0.008
Limit line: y ≥ 0.980 – x  (within red region)
```

**White (front position):**
```
x ≤ 0.500
y ≥ 0.150
y ≤ 0.500
y ≤ 0.382 (below yellow boundary)
y ≥ x – 0.120 (above purple boundary)
```

**Amber (direction indicators — also used in R6):**
```
0.310 ≤ x ≤ 0.500
y ≥ 0.390
y ≤ 0.790 – 0.670x
y ≤ x – 0.120 (NOT white region)
```

---

### 2.5 DRL Requirements under R7 Revision 3
- Luminous intensity at axis: min 400 cd, max 1200 cd (daytime only)
- When headlamps are active, DRL must dim to ≤ 300 cd (automatic dimming)
- Colour: White
- Position: Front, one each side, symmetric

---

## 3. UN Regulation No. 6 — Direction Indicators (Turn Signals)

### 3.1 Scope
R6 covers **direction indicator lamps** for:
- Motor vehicles (Category 1, 1a, 1b, 2, 2a, 2b — front/rear/side/trailer indicators)
- Includes emergency warning (hazard) lamps

---

### 3.2 Flash Frequency Requirements

**CRITICAL specification — most common R6 failure:**

| Parameter | Requirement |
|---|---|
| Flash frequency | **60 to 120 flashes per minute** |
| Tolerance on frequency | ±3 flashes per minute |
| ON-time ratio | Between **40% and 60%** of total flash cycle |
| Warm-up period | First flash may exceed timing limits — only from 2nd flash onwards |

**Example calculation:**
- At 85 flashes/min → cycle period = 60/85 = 0.706 seconds
- ON-time must be between 0.706 × 0.4 = 0.282s and 0.706 × 0.6 = 0.424s

**Measurement method:**
- Use oscilloscope or data logger measuring lamp voltage or current
- Record minimum 10 consecutive flash cycles after thermal stabilisation
- Average frequency and ON-time ratio must be within specification

---

### 3.3 Luminous Intensity Requirements for R6

#### Category 1 (Front direction indicator)
| Test point | Minimum (cd) | Maximum (cd) |
|---|---|---|
| 0° H, 0° V | 175 | 700 |
| ±20° H | 50% of axis value | — |
| ±10° V | 60% of axis value | — |

#### Category 2 (Rear direction indicator)
| Test point | Minimum (cd) | Maximum (cd) |
|---|---|---|
| 0° H, 0° V | 50 | 700 |
| ±20° H | 50% of axis value | — |

#### Category 5 (Front side repeater)
| Parameter | Minimum (cd) |
|---|---|
| At axis | 0.6 cd minimum (very low — side visibility) |
| Colour | Amber |

---

### 3.4 Colour Requirements for R6
- **Amber** is required for direction indicators in ECE markets
- **CIE chromaticity coordinates:** as specified in the Annexes (same amber boundary as R7 section 2.4 above)
- **USA (FMVSS 108):** Allows RED at rear direction indicators — a key difference from ECE

---

### 3.5 Hazard Warning Operation
When hazard warning is activated, all four indicators flash simultaneously.
- Flash frequency and timing requirements remain the same as normal operation
- System must resume single-side indication correctly after hazard deactivation
- Load fault detection (lamp-out warning) must also function correctly

---

### 3.6 Current Draw and Load Sensing
- Most vehicles use load-sensing circuits to detect bulb/LED failures
- When a lamp fails, flash rate increases (hyper-flashing) to alert driver
- For LED conversions: may need load resistor or smart flasher relay to maintain correct flash rate

---

## 4. UN Regulation No. 48 — Installation of Lighting Devices

### 4.1 Scope
R48 defines the **installation rules** for all lighting equipment on complete vehicles — it references which lamps are mandatory, optional, and prohibited, and specifies their mounting position.

R48 = System-level regulation. Individual lamp regulations (R112, R7, R6) = Component-level.

---

### 4.2 Mandatory Lamps by Vehicle Category

| Lamp | M1 (car) | N1 (van) | N2/N3 (truck) | L3 (motorcycle) |
|---|---|---|---|---|
| Front position | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Rear position | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Stop lamp | 2 × mandatory + CHMSL | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Front indicator | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Rear indicator | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Headlamp (low) | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Headlamp (high) | 2 × mandatory | 2 × mandatory | 2 × mandatory | 1 mandatory |
| Reversing lamp | 1 mandatory | 1 mandatory | 1 mandatory | — |
| Fog lamp (rear) | 1 mandatory | 1 mandatory | 1 mandatory | optional |
| DRL | mandatory (EU, since 2011) | mandatory (EU) | mandatory (EU) | — |

---

### 4.3 Height Requirements (Above Ground)

| Lamp | Minimum height | Maximum height |
|---|---|---|
| Front position | 350 mm | 1500 mm |
| Rear position | 350 mm | 1500 mm |
| Stop lamp | 350 mm | 1500 mm |
| CHMSL | — | 1500 mm (or max roof height) |
| Front indicator | 350 mm | 1500 mm |
| Rear indicator | 350 mm | 1500 mm |
| Headlamp (low) | 500 mm | 1200 mm |
| DRL | 250 mm | 1500 mm |
| Rear fog lamp | 250 mm | 1000 mm |
| Reversing lamp | 250 mm | 1200 mm |

---

### 4.4 Lateral Position Requirements

**Reference edge lamps (outermost lamps):**
- Must be within **400 mm** of the outermost point of the vehicle
- Must be visible from the outermost point (not hidden by body panel)

**Separation distance between lamps:**
- Direction indicators must be at least **600 mm apart** (inner edge to inner edge, front and rear)
- Stop lamps must be at least **600 mm apart** (on M1 vehicles ≤ 1300 mm wide, this requirement relaxed)

**Combined lamp restrictions:**
- A single lamp unit can combine multiple functions (e.g., tail + stop + indicator) if each function meets its own regulations
- NOT permitted to combine: stop lamp + rear position lamp if they use the same illuminated surface area (unless intensity ratio maintained)

---

### 4.5 Visibility Angles from Vehicle

Every lamp must be visible from defined angles as seen from outside the vehicle:
- These are checked geometrically (no actual photometric measurement at extreme angles for installation check)
- Body panels, bumpers, tow hooks must not obscure lamp visibility angles

**Example:** Rear indicator must not be obscured at 80° outboard horizontal view — check with physical inspection.

---

### 4.6 LED Lamp Replacement Rules under R48

When replacing a conventional lamp with an LED retrofit:
- **NOT permitted in ECE markets** to install LED bulbs into halogen headlamp housings NOT designed for LED
- LED retrofit into a lamp not homologated for LED use = non-conforming installation
- LED lamp as complete assembly in an R48-compliant position = permitted if the Lamp unit itself is R112/R7 etc. approved

---

## 5. UN Regulation No. 10 — Electromagnetic Compatibility (EMC)

### 5.1 Scope
R10 applies to all **electrical/electronic systems** of motor vehicles and their components, including:
- LED lamp driver electronics (LED headlamps, DRLs, indicators)
- AFS control units
- Body control modules controlling lighting
- Any device that generates or may be affected by electromagnetic energy

---

### 5.2 Key EMC Tests under R10

#### Radiated Emissions (RE)
- Method: CISPR 12
- Limit: Depends on frequency band (typically 30 MHz to 1 GHz)
- Test setup: Vehicle or component on outdoor test site, antenna at 10m distance
- Headlamp LED driver generates conducted noise that radiates via wiring harness

#### Conducted Emissions (CE)
- Method: CISPR 25
- Limit: Band I to Band V (up to 1 GHz)
- Test: LISN (Line Impedance Stabilisation Network) in series with supply

#### Radiated Immunity (RI)
- Method: BCI (Bulk Current Injection) or TEM cell
- Ensures lamp continues to function correctly when vehicle is exposed to external RF fields
- Practical: LED headlamp must not flicker or turn off when mobile phone transmits

#### Electrical Transient Immunity
- ISO 7637 pulses: Load dump (Pulse 5), switching transients (Pulse 1, 2, 3)
- LED driver electronics must survive automotive voltage transients

---

### 5.3 Common EMC Failures in Lighting

| Failure | Cause | Fix |
|---|---|---|
| Radiated emissions at 150–450 MHz | LED switching frequency harmonics | EMI filter at driver input, ferrite bead |
| Radiated immunity failure (flicker) | Inductive coupling on power line | Improved grounding, bulk capacitor |
| Load dump failure (damaged LED driver) | No transient protection | TVS diode, varistor at input |
| AM radio interference | Power supply noise at AM frequencies | Better filtering, spread-spectrum switching |

---

## 6. UN Regulation No. 119 — Cornering Lamps

### 6.1 Scope
Cornering lamps provide **supplementary illumination** when turning, typically activated by steering angle or direction indicator signal above a speed threshold.

### 6.2 Key Requirements
- Illuminated surface: White light
- Activation condition: Speed < specified threshold (e.g., ≤ 40 km/h)
- Beam directed laterally (≥ 30° from vehicle centreline)
- Minimum illuminance: 1 lux measured at specified grid points
- Must not dazzle oncoming traffic (intensity limits apply)
- Deactivation: Must switch off when indicator is cancelled or speed exceeded

### 6.3 Installation under R48
- Optional equipment on M and N category vehicles
- Mounted within front quarter of vehicle
- Height: 250 mm to 900 mm from ground

---

## 7. UN Regulation No. 123 — Adaptive Front-Lighting Systems (AFS)

### 7.1 Scope
AFS headlamps can **adapt** beam pattern based on driving conditions using:
- Swivelling reflectors / projectors (mechanical)
- Matrix LED / pixel lighting (electronic, multiple lighting zones)

### 7.2 AFS Beam Classes

| Class | Condition | Key Difference vs Standard Low Beam |
|---|---|---|
| **Class C** | Town/city driving | Wider horizontal spread, illuminates footpaths |
| **Class V** | Rural | Standard asymmetric beam — reference class |
| **Class E** | Motorway/highway | Extended range, higher horizontal cut-off |
| **Class W** | Wet road | Reduced upward light to minimise reflection from wet surface |
| **Class T** | Adverse weather | Similar to fog lamp — wider spread, lower cut-off |

**Definition:** The **neutral position** (no swivel) must produce a beam compliant with R112 photometric requirements. AFS only activates deviation from neutral.

### 7.3 Swivel Angle Requirements
- Maximum lateral swivel: 15° inboard, 15° outboard (from neutral alignment)
- Swivel speed: Must track steering angle change at least at specified rate
- Return to neutral: Must return within specified time when no swivel input

### 7.4 Vertical Aim Control (Levelling)
AFS systems must include automatic headlamp levelling:
- Compensates for vehicle load changes (front rises when rear loaded)
- Sensor: vehicle height sensor at front and rear axle
- Maximum downward aim: Not less than –1.5% slope

---

## 8. Regulation Comparison — ECE vs FMVSS 108

| Feature | ECE (R112, R7, R6) | FMVSS 108 (USA) |
|---|---|---|
| Approval method | Type Approval (TA by authority) | Self-certification |
| Headlamp beam | Asymmetric cut-off (R112) | Sealed beam or replaceable bulb |
| Direction indicator colour | Amber only (front + rear) | Amber front, red OR amber rear |
| Stop lamp intensity | 60–185 cd | Photometric zones (different table) |
| DRL requirement | Mandatory in EU | Not federally required |
| Colour coordinates | CIE x,y specific boundaries | SAE/ANSI limits |
| Flash frequency | 60–120 /min | 60–120 /min (similar) |
| B50L glare limit | 17 cd max | No direct equivalent point |

> Managing dual ECE + FMVSS approval is common for global OEMs. The optical design must satisfy BOTH sets of test points — which sometimes requires separate reflectors/optics.

---

## 9. Quick Test Values Summary Table

| Regulation | Critical Limit | Value |
|---|---|---|
| R112 | Max glare at B50L | 17 cd |
| R112 | Min intensity at HV | 12 cd |
| R112 | Min intensity at 50R | 12 cd |
| R7 | Min front position | 4 cd |
| R7 | Max rear position | 12 cd |
| R7 | Min stop lamp | 60 cd |
| R7 | Max stop lamp | 185 cd |
| R7 | Stop:position ratio | ≥ 5:1 |
| R6 | Flash frequency | 60–120 /min |
| R6 | ON-time ratio | 40–60% |
| R6 | Min front indicator (axis) | 175 cd |
| R6 | Min rear indicator (axis) | 50 cd |
| R48 | Min headlamp height | 500 mm |
| R48 | Max headlamp height | 1200 mm |
| R48 | Indicator separation | 600 mm |

---

*File: 02_ece_regulations_r112_r7_r6.md | automotive_homologation series*
