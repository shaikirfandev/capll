# Functional Safety – ISO 26262 Study Material
## Road Vehicles – Functional Safety Standard

---

## 1. What is ISO 26262?

**ISO 26262** is the functional safety standard for **electrical and electronic (E/E) systems in road vehicles**. It addresses the safety risks from systematic failures and random hardware failures.

- Based on **IEC 61508** (general functional safety standard)
- Covers passenger cars, trucks, motorcycles, and buses
- Applies to all phases: concept, development, production, operation, decommissioning
- Released 2011, revised **2018 (2nd edition)** + ISO/PAS 8926 for AI/ML

### What is Functional Safety?
> Absence of **unreasonable risk** due to hazards from malfunctioning behavior of E/E systems.

**Key terms:**
- **Hazard**: Potential source of harm (e.g., unintended acceleration)
- **Risk**: Probability × Severity of hazard
- **Safety Goal**: Top-level safety requirement derived from HARA
- **Safe State**: Operating mode in which no harm occurs

---

## 2. ASIL – Automotive Safety Integrity Levels

ASIL defines the **rigor required** to mitigate a risk. Determined by HARA.

| ASIL | Risk Level | Examples |
|---|---|---|
| **QM** (Quality Managed) | No safety risk; standard quality process | Infotainment display |
| **ASIL A** | Low | Seat occupancy detection |
| **ASIL B** | Moderate | ABS (some features) |
| **ASIL C** | High | Electronic Power Steering |
| **ASIL D** | Highest | Airbag deployment, EPS, autonomous braking |

### ASIL Decomposition
A single ASIL D requirement can be split into two independent ASIL B requirements:
```
ASIL D ──────► ASIL B (Channel 1) + ASIL B (Channel 2)
ASIL C ──────► ASIL A (Channel 1) + ASIL B (Channel 2)
```
Independent channels must have no common cause failures.

---

## 3. Hazard Analysis and Risk Assessment (HARA)

HARA identifies **hazards** and assigns **ASILs** based on three factors:

### 3.1 ASIL Determination

```
ASIL = f(Severity, Exposure, Controllability)
```

### 3.2 Severity (S)
| Level | Description | Example |
|---|---|---|
| S0 | No injuries | Cosmetic issue |
| S1 | Light to moderate injuries | Minor collision |
| S2 | Severe life-threatening injuries | High-speed event |
| S3 | Life-threatening / fatal | Unintended full throttle |

### 3.3 Exposure (E) – How often is the hazardous situation encountered?
| Level | Probability | Description |
|---|---|---|
| E0 | Incredible | Virtually never |
| E1 | Very low | Few times in lifetime |
| E2 | Low | Once per year |
| E3 | Medium | Once per month |
| E4 | High | Almost daily |

### 3.4 Controllability (C) – Can a typical driver control the situation?
| Level | Description |
|---|---|
| C0 | Controllable in general |
| C1 | Simply controllable |
| C2 | Normally controllable |
| C3 | Difficult to control / uncontrollable |

### 3.5 ASIL Lookup Table

|   | S1 | S2 | S3 |
|---|---|---|---|
| **E1, C3** | QM | QM | A |
| **E2, C3** | QM | A | B |
| **E3, C3** | A | B | C |
| **E4, C3** | B | C | D |
| **E4, C2** | A | B | C |
| **E4, C1** | QM | A | B |

---

## 4. Safety Lifecycle Phases (ISO 26262 V-Model)

```
Concept Phase
├── Item Definition
├── HARA → Safety Goals
└── Functional Safety Concept (FSC)
        ↓
System Level
├── Technical Safety Concept (TSC)
├── System Architecture Design
└── System Integration Tests
        ↓
Hardware Level              Software Level
├── HW Design               ├── SW Architecture
├── HW FMEA/FTA             ├── SW Unit Design
├── HW Analysis             ├── SW Unit Tests
└── HW Tests                └── SW Integration Tests
        ↓                           ↓
              System Integration
              Vehicle Integration
              Production, Operation, Service
```

---

## 5. Key ISO 26262 Work Products

| Work Product | Description |
|---|---|
| **Item Definition** | Scope and boundaries of the safety-relevant item |
| **HARA** | Hazard identification, ASIL assignment |
| **Safety Goals** | Top-level, ASIL-rated safety requirements |
| **FSC** | Functional safety concept – how goals are achieved |
| **TSC** | Technical safety concept – system-level requirements |
| **FMEA** | Failure Mode and Effects Analysis |
| **FTA** | Fault Tree Analysis |
| **DFMEA** | Design FMEA at hardware level |
| **Safety Plan** | Project-level safety management plan |
| **DIA** | Dependent Failure Analysis |
| **Safety Case** | Final evidence package that safety goals are met |

---

## 6. Hardware Safety Analysis

### 6.1 FMEA (Failure Mode and Effects Analysis)
Bottom-up analysis:
- List all hardware components
- Identify failure modes for each
- Trace effect on system behavior
- Assess ASIL and mitigation

### 6.2 FTA (Fault Tree Analysis)
Top-down analysis:
- Start from the hazardous event (top event)
- Decompose into contributing causes using AND/OR gates
- Quantify probability (λ = failure rate in FIT)

### 6.3 Diagnostic Coverage (DC)
Percentage of failure modes detected by safety mechanisms:

| DC Classification | DC Range |
|---|---|
| Low | < 60% |
| Medium | 60% to < 90% |
| High | ≥ 90% |

### 6.4 PMHF (Probabilistic Metric for random Hardware Failures)
Maximum allowed random HW failure rate (probability):

| ASIL | PMHF Target |
|---|---|
| ASIL D | < 10 FIT (10^-8 /h) |
| ASIL C | < 100 FIT (10^-7 /h) |
| ASIL B | < 100 FIT |

**FIT** = Failures In Time = number of failures per 10^9 operating hours

---

## 7. Software Safety Requirements

### ASIL SW Development Requirements
| ASIL | Coding Guidelines | SW Testing |
|---|---|---|
| ASIL A | Recommended | Statement coverage |
| ASIL B | Required | Branch coverage |
| ASIL C | Required + tools | MC/DC coverage |
| ASIL D | Required + formal methods | MC/DC, formal verification |

### SW Safety Mechanisms
- **Range checks** on input/output signals
- **Plausibility checks** against redundant signals
- **Cyclic Redundancy Check (CRC)** on safety data
- **Alive counter** on safety-critical messages
- **Watchdog** timer to detect task overrun
- **Memory protection** (MPU) to prevent corruption
- **Redundant calculations** with comparison

---

## 8. Functional Safety Concepts for ADAS

### Safe States for ADAS Functions
| Function | Safe State |
|---|---|
| AEB (Autonomous Emergency Braking) | Deactivate AEB, alert driver, apply partial braking only |
| LKA (Lane Keep Assist) | Fade out steering assistance, alert driver |
| ACC (Adaptive Cruise Control) | Disengage, maintain last driver-set speed |
| EPS (Electric Power Steering) | Maintain last torque, alert, reduce assist gradually |

### FTTI (Fault-Tolerant Time Interval)
Time from fault occurrence to potential harm:
```
FTTI = FHTI + FSR
FHTI = Fault Handling Time Interval (detection + reaction)
FSR  = Fault Safety Reaction (reaching safe state)
```

---

## 9. ISO 26262 and SOTIF (ISO 21448)

| Standard | Covers |
|---|---|
| **ISO 26262** | Failures and malfunctions of E/E systems |
| **ISO 21448 (SOTIF)** | Intended function insufficiency – system works as designed but causes harm (e.g., ADAS in edge cases) |

SOTIF is critical for ADAS – even a correctly-functioning camera that fails to detect a child in fog is a SOTIF issue, not an ISO 26262 failure.

---

## 10. Common Interview Questions

**Q1: What is ASIL and how is it determined?**
> ASIL is the Automotive Safety Integrity Level ranging from A to D (D = highest). It's determined by HARA using three factors: Severity (S) of potential harm, Exposure (E) to the hazardous situation, and Controllability (C) by the driver.

**Q2: What is HARA?**
> Hazard Analysis and Risk Assessment – the systematic process of identifying operational situations and hazards, assessing risk per S/E/C parameters, and assigning ASILs to define safety goals.

**Q3: What is a Safety Goal?**
> A top-level safety requirement derived from HARA to prevent or mitigate a specific hazard. Safety goals state what must not happen (e.g., "The EPS shall not apply unintended steering torque above 3 Nm").

**Q4: What is ASIL decomposition?**
> Splitting one high-ASIL requirement into two independent lower-ASIL requirements. ASIL D → ASIL B + ASIL B, allowing implementation in two independent channels to reduce design burden while maintaining integrity.

**Q5: What is FIT?**
> Failures In Time – a unit for hardware failure rate: one failure per 10^9 operating hours. ASIL D systems must achieve < 10 FIT random hardware failure targets.

**Q6: What is the difference between ISO 26262 and SOTIF?**
> ISO 26262 addresses random hardware failures and systematic faults in E/E systems. SOTIF (ISO 21448) addresses situations where the intended function itself is insufficient to ensure safety — no malfunction, but the system fails due to limitations (e.g., sensor perception gaps in ADAS).

**Q7: What are common software safety mechanisms?**
> Range checks, plausibility checks, CRC on safety-critical data, alive counters on messages, watchdog timers, MPU-based memory protection, and redundant calculations with cross-comparison.
