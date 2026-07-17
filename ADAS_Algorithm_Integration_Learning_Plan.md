# Learning Plan: Senior ADAS Algorithm Integration Engineer

This document outlines a structured learning path to acquire the skills necessary for the "Senior SW Engineer – Algorithm Integration ARXML Integration" role. It focuses on the key competencies mentioned in the job description, including AUTOSAR, ADAS algorithms, embedded systems, and automotive processes.

---

## 1. Foundational AUTOSAR & Tooling

This is the most critical area. Your goal is to become proficient in AUTOSAR Classic Platform architecture and the Vector DaVinci toolchain.

### Key Topics:
- **AUTOSAR Classic Architecture:**
  - Understand the layered architecture: Application Layer, RTE (Runtime Environment), BSW (Basic Software).
  - Study key BSW modules: COM (Communication), DCM (Diagnostic Communication Manager), DEM (Diagnostic Event Manager), OS (Operating System).
  - Learn about Software Components (SWCs) and their interaction.
- **ARXML (AUTOSAR XML):**
  - Understand the purpose and structure of ARXML files.
  - Learn how ARXML is used to describe system configuration, SWCs, and ECU parameters.
  - Practice reading and interpreting ARXML files for system understanding.
- **Vector DaVinci Toolchain:**
  - **DaVinci Configurator Pro:** Gain hands-on experience in configuring BSW modules. Learn to generate a complete ECU configuration.
  - **DaVinci Developer:** Learn to design SWCs and define their interfaces.
- **Integration Workflow:**
  - Understand the end-to-end process: receiving Application ARXML, integrating it with the existing system, configuring the BSW, and generating the final ECU software.

### Learning Resources & Actions:
- **Review Existing Material:** Your workspace has `dbc_arxml_files/` and `autosar_basics/`. Start there.
- **Hands-on Practice:**
    1.  Obtain a sample ARXML file (or use one from `dbc_arxml_files/`).
    2.  Use a trial version of DaVinci tools (if available) to import and analyze the file.
    3.  Attempt to create a simple project, define a Software Component, and configure the CAN communication stack.

---

## 2. ADAS Domain Knowledge

You need to understand what you are integrating. This involves learning about ADAS features, sensor data, and the algorithms that process it.

### Key Topics:
- **ADAS Features:**
  - Study common ADAS features like Adaptive Cruise Control (ACC), Lane Keeping Assist (LKA), Automated Emergency Braking (AEB).
- **Sensor Fundamentals:**
  - **Camera:** Image processing basics, object detection.
  - **Radar:** Principles of operation, point clouds, object tracking.
  - **LiDAR:** How it works, data representation.
- **Perception & Planning Pipelines:**
  - **Perception:** How raw sensor data is processed to detect objects, lanes, and free space.
  - **Sensor Fusion:** How data from multiple sensors is combined for a more robust understanding of the environment.
  - **Planning:** How the vehicle decides its path and actions based on perception output.
- **Testing & Validation:**
  - **SIL (Software-in-the-Loop):** Testing algorithms on a PC.
  - **HIL (Hardware-in-the-Loop):** Testing the actual ECU with simulated inputs.
  - **Vehicle Testing:** On-road validation.

### Learning Resources & Actions:
- **Explore Workspace:** The `adas_scenario_questions/` and `sensor_fusion/` directories are highly relevant.
- **Online Courses:** Look for courses on platforms like Coursera or Udacity related to Self-Driving Cars or Robotics. They provide excellent introductions to perception and planning.

---

## 3. Embedded C & Microcontrollers

This role requires strong, hands-on embedded development skills.

### Key Topics:
- **32-bit Microcontroller Architectures:**
  - Focus on **Infineon Aurix (TriCore)** and **ARM Cortex-M/R**. These are very common in automotive.
  - Understand memory maps, peripherals (CAN, SPI, Ethernet), and interrupt handling.
- **Embedded C Programming:**
  - **Pointers and Memory:** Master pointer arithmetic, memory-mapped I/O, and memory management.
  - **Bitwise Operations:** Essential for manipulating hardware registers.
  - **Real-time Concepts:** Understand interrupts, task scheduling, and determinism.
- **Debugging:**
  - Learn to use a hardware debugger (e.g., Lauterbach TRACE32, iSystem) to step through code, inspect memory, and analyze system state on a real ECU.

### Learning Resources & Actions:
- **Review Scripts:** The `c_cpp_adas/` and `script_12_bitwise.capl` files can provide practical examples.
- **Get a Dev Board:** Purchase a low-cost development board (e.g., an STM32 Nucleo or an Infineon Aurix board) and practice writing drivers for its peripherals from scratch.

---

## 4. Automotive Processes & Standards

Professional automotive development is highly process-driven.

### Key Topics:
- **Automotive SPICE (ASPICE):**
  - Understand the purpose of ASPICE and its Process Areas (e.g., SWE.1 to SWE.6).
  - Learn about the importance of traceability, documentation, and process compliance.
- **ISO 26262 (Functional Safety):**
  - Learn the basics of ASILs (Automotive Safety Integrity Levels).
  - Understand concepts like safety goals, functional safety requirements, and fault analysis (FMEA).
- **Agile/Scrum:**
  - Familiarize yourself with Agile ceremonies (sprint planning, daily stand-ups, retrospectives) and artifacts (product backlog, sprint backlog).

### Learning Resources & Actions:
- **Read Up:** The `functional_safety/` and `automotive_project_manager/` folders are good starting points.
- **Online Research:** Search for whitepapers and articles from companies like Vector, ETAS, and MathWorks on these topics.

---

## 5. Study & Application Roadmap

Follow this sequence for a structured approach.

1.  **Month 1: AUTOSAR Deep Dive.** Focus entirely on Section 1. This is your highest priority. Your goal is to be able to explain the AUTOSAR integration workflow confidently.
2.  **Month 2: ADAS & Embedded C.** Split your time between Section 2 and Section 3. Apply your embedded C knowledge by trying to write a simple program that mimics processing sensor data (e.g., parsing a CAN message).
3.  **Month 3: Processes & Project Work.** Cover Section 4 and start a personal project. A good project would be to create a simple "Lane Warning" system on your development board using a simulated CAN input. Document your process as if you were following ASPICE, creating requirements and design documents.

By following this plan, you will build a strong and relevant skill set for the ADAS Algorithm Integration role.




# ADAS, Infotainment, Cluster, and Telematics: A Learning Guide to Writing Test Cases from System Specification Documents

> Audience: new automotive software/hardware test engineers. Goal: by the end of this document you can pick up any System Requirements Specification (SyRS) or Feature Specification Document (FSD) for an ADAS, Infotainment, Cluster or Telematics project and translate every functional requirement into structured, traceable test cases.

---

## Executive Summary

- **Spec-Anatomy First**: Every automotive test case is born from a requirement row that lives inside a SyRS / FSD / IRS (Interface Requirements Specification). The first job of a test engineer is not to design tests - it is to **find** the requirement row and read its verification method. Good test cases are therefore indistinguishable from good requirement reads.
- **Coverage Across 4 Domains Demands Different Test Grammars**: ADAS test cases use a Sense -> Warn -> Intervene grammar anchored in sensor stimuli; Infotainment test cases use a Use-Case / State grammar anchored in HMI actions; Cluster test cases use a Signal-Driven grammar anchored on the CAN/LIN signal list in the spec; Telematics test cases use a Call-Flow grammar anchored in network and protocol standards.
- **Standards Bind It All Together**: IEEE 829 supplies the test-document template; ISO/IEC/IEEE 29119 extends it; Automotive SPICE PAM 3.1 demands bidirectional traceability in SWE.6 and SYS.4; ISO 26262 assigns ASILs that constrain test rigor on safety-relevant features; ISO 14229 (UDS) and ISO 2575 (telltale symbols) define protocol- and symbol-level regressions that test cases must cover.
- **Three Test Types Per Requirement**: For every accepted requirement, write at least three test cases - one **positive (happy path)**, one **negative (invalid input / fault injection)**, one **boundary (min/max/timeout)**. The spec tells you the nominal range; your job is to probe just outside it.

---

## 1. Anatomy of a System Specification Document (cross-domain foundation)

Every automotive project - ADAS, IVI, Cluster, Telematics - consumes the same family of specification artefacts. Knowing which page to flip to is half the war.

| Spec artefact | Lives in it | What a test engineer reads there | Source |
|---|---|---|---|
| System Requirements Specification (SyRS) | High-level feature behaviour | "REQ-CL-0042: Speedometer range is 0-260 km/h, resolution 1 km/h, update rate >= 50 Hz" - the verification column flags V&V method | [1_anatomy_of_a_system_specification_document_cross_domain_foundation[0]] [47] |
| Software Requirements Specification (SRS) | Component-level behaviour | Module APIs, state-machine variables, timing budgets, fault handling | ASPICE SWE.1 base practice |
| Interface Requirements Specification (IRS) | Signal-level contracts | CAN DBC / LIN LDF signals, UDS services, Ethernet SOME/IP messages, pin-out, voltage levels | System engineering best practice |
| Feature Specification Document (FSD) | Marketing-vs-engineering view | User-visible behaviour, V model left side | OEM practice |
| Test Specification (TST) | You write this | Traceable to SyRS, deterministic steps | ASPICE SWE.6 outputs (08-50, 13-50) |
| Diagnostics Specification (DDS) | UDS on CAN / UDS on IP / DoIP | $22/$2E/$31 DIDs, SecurityAccess algorithm, DTC list | [1_anatomy_of_a_system_specification_document_cross_domain_foundation[1]] [33] |
| Safety Manual (ISO 26262) | ASILs, FSRs, TSRs | Fault-injection tests, diagnostic coverage tests | ISO 26262-4/-5 |

Source: [1_anatomy_of_a_system_specification_document_cross_domain_foundation[2]] [2], [1_anatomy_of_a_system_specification_document_cross_domain_foundation[3]] [45].

**Mechanism -> Implication -> Recommendation.** The spec is often the only contractual artefact tying the OEM, Tier-1 and silicon vendor together on what "done" means. A test case that is not anchored to a requirement row is therefore not auditable and will be rejected by ASPICE assessors. **Recommendation:** before you write a single test step, build a Requirement -> Test-Case traceability matrix in a tool such as Jama, Polarion, DOORS, or even a shared spreadsheet. The matrix forces you to read the spec carefully and exposes early whether you have too many tests per requirement (over-tested) or none (uncovered).

### 1.1 The IEEE 829 / ISO 29119 Test-Document Template

The IEEE 829 Standard (and its successor ISO/IEC/IEEE 29119) defines the eight documents a serious test process must produce. Every test case you write lives inside one of these.

| 829 artefact | What it contains | 29119 equivalent |
|---|---|---|
| Master Test Plan (MTP) | Scope, items-under-test, approach, tools, risks, exit criteria | Test Plan |
| Level Test Plan (LTP) | Plan for one test level (e.g. system test vs SW qualification) | Test Plan |
| Test Design Specification (TDS) | Identifies test cases, gives techniques (equivalence partitioning, boundary, decision table) | Test Design |
| Test Case Specification (TCS) | The case: ID, purpose, preconditions, inputs, procedure, expected results, pass/fail criteria | Test Case |
| Test Procedure Specification (TPS) | The script: ordered steps, executable code or manual keystrokes | Test Procedure |
| Test Log | Chronological record of execution outcomes | Test Log |
| Test Incident Report | One per anomaly found (bug -> ticket) | Test Incident |
| Test Summary Report | Aggregate metrics: cases run, pass/fail, coverage, residual risk | Test Summary |

Source: [1_anatomy_of_a_system_specification_document_cross_domain_foundation[4]] [1].

**Mechanism -> Recommendation.** A common failure mode we see on real ADAS projects is conflating TCS and TPS - engineers write procedural steps inside the case, leaving the design intent invisible. Keep them separate: *what* (TCS) drives *how* (TPS). You can then re-use a TCS across manual, automation, and HIL benches with only the TPS rewritten.

---

## 2. ADAS - Feature Taxonomy and Test Cases from Spec

### 2.1 The Feature Map (Sense -> Warn -> Intervene)

The four automotive ADAS levels (L0-L2) all run on the same three-stage logic: sensor fusion detects an event, driver is warned, and if the driver does not act, the system intervenes. Every ADAS feature spec is organised around these three columns [2_adas_feature_taxonomy_and_test_cases_from_spec[0]] [12].

| Acronym | Full name | Sense | Warn | Intervene | Typical spec row (example) |
|---|---|---|---|---|---|
| ACC | Adaptive Cruise Control | Front radar + camera | Head-up distance bars | Throttle / brake modulation | "REQ-ACC-007: Set-speed range 30-180 km/h, time-gap selection 1.0/1.5/2.0 s" |
| AEB | Autonomous Emergency Braking | Front radar | Audible + haptic brake pulse | Full ABS-based braking | "REQ-AEB-014: Braking deceleration >= 6 m/s^2 when TTC < 1.4 s" |
| FCW | Forward Collision Warning | Front radar + camera | Red icon + chime | None (warning only) | "REQ-FCW-003: TTC threshold 2.5 s, warning latency < 200 ms" |
| LDW | Lane Departure Warning | Front camera | Steering-wheel vibration + icon | None | "REQ-LDW-005: Activation above 60 km/h, departure angle > 0.1 rad" |
| LKA | Lane Keep Assist | Front camera | Same as LDW | Corrective steering torque | "REQ-LKA-009: Steering torque ramp 0.5-3 Nm/s, max 8 Nm" |
| LCA | Lane Change Assist | Side radar | Mirror LED + chime | None / lane abort | "REQ-LCA-002: Activation between 60-140 km/h, blind-spot lane coverage 4 m x 18 m" |
| BSD | Blind Spot Detection | Side radar | Mirror LED | None | "REQ-BSD-001: Detection range 4-18 m, lateral +/- 4 m" |
| APA | Automatic Parking Assist | Ultrasonic + camera | Visual + audible | Steer, shift, brake | "REQ-APA-017: Supported slot length [vehicle + 0.8 m], angle +-15 deg" |
| DMS | Driver Monitoring System | Driver-facing IR camera | Audio prompt + cluster icon | None | "REQ-DMS-004: Drowsiness alert at PERCLOS > 0.4 for 4 s" |
| TSR | Traffic Sign Recognition | Front camera | Cluster overlay | None / speed-limit suggestion | "REQ-TSR-002: Recognised classes: speed limit, no-overtake, stop, yield" |
| NOA | Navigate on Autopilot | HD map + sensor fusion | Acoustic + cluster state | Longitudinal + lateral control | "REQ-NOA-011: Route adherence +/- 0.3 m, lane-change policy 3 taps" |

**Mechanism -> why it matters.** ADAS features all degrade gracefully - they declare an "avail-state" on the CAN bus (ASIL QM/B). A spec row that says "feature shall show 'unavailable' symbol" is just as testable as one that says "feature shall brake to 0 m/s". Treating availability-state as a first-class requirement is what separates a junior tester from an experienced one.

### 2.2 Anatomy of a Typical ADAS System Spec

Most OEMs divide the ADAS SyRS into:
1. **General** - feature scope, system variants, operating modes (Active, Standby, Degraded, Off).
2. **Sensor Inputs** - radar / camera / lidar / ultrasonic interfaces, signal ranges, alignment tolerances.
3. **Functional Requirements** - the FRs, each with ID and Verification Method (typically Analysis / HIL / Vehicle).
4. **Performance Requirements** - timing budgets, accuracy tolerances.
5. **Interface Requirements** - CAN messages (DBC reference), debug/UDS.
6. **State / Fault Handling** - degraded modes, DTC behaviour, fall-back strategy.
7. **Safety** - ASIL allocation per ISO 26262, fault injection requirements, diagnostic coverage.
8. **Environmental** - temperature, vibration, EMC.
9. **Cybersecurity** - UN R155, secure onboard communication.

### 2.3 Worked Example - Three Test Cases for ACC from an FSD

Assume the spec row reads: **"REQ-ACC-021: The ACC shall maintain a time-gap of 1.5 s ±20% to a preceding vehicle within a speed range of 30-180 km/h. When the gap exceeds the upper tolerance for >3 s, the system shall smoothly close to the set-gap with a closing rate <= 0.5 g."**

| TC ID | Type | Preconditions | Steps | Expected Result | Pass criteria | Trace link |
|---|---|---|---|---|---|---|
| TC-ACC-021-P01 | Positive / Happy path | ACC active, set-speed 100 km/h, time-gap 1.5 s, lead vehicle moving at 90 km/h | 1. Engage ACC. 2. Maintain steady state for 60 s. | Time-gap remains in [1.2 s, 1.8 s] for the entire 60 s | All samples inside band | REQ-ACC-021 |
| TC-ACC-021-N01 | Negative - lead decelerates sharply | Lead at 100 km/h, ego at 100 km/h, gap 1.5 s | 1. Lead vehicle brakes at 0.4 g. | Ego applies brake acceleration > 0.4 g and re-establishes 1.5 s gap with no overshoot below 1.0 s | TC-time never below 1.0 s; no AEB escalation | REQ-ACC-021, REQ-AEB-014 |
| TC-ACC-021-B01 | Boundary - upper gap trigger | Lead at 80 km/h, ego at 120 km/h, gap drifts to 2.4 s | 1. Hold steady for 5 s. 2. Observe ego closing rate. | Closing rate <= 0.5 g (4.9 m/s^2) for entire closure from 2.4 s -> 1.8 s | Peak measured deceleration <= 0.5 g; smooth transition | REQ-ACC-021 |
| TC-ACC-021-N02 | Negative - sensor mis-alignment | Front radar yaw offset +0.8 deg injected in HIL | 1. Drive steady 90 km/h. | ACC either disengages with audible warning or auto-realigns within 2 s | No uncontrolled acceleration; cluster warning ON | REQ-SAF-009 (fault injection) |

**Mechanism -> implementation tip.** Notice row TC-ACC-021-P01 vs N01 - one drives positive behaviour, one drives a fault path. A common mistake is to stop after the positive case. ASPICE SWE.6 BP1 requires a documented **regression test strategy** that includes negative cases [2_adas_feature_taxonomy_and_test_cases_from_spec[1]] [45]. Negative test cases are how you prove the system fails safely.

---

## 3. Infotainment - Feature Taxonomy and Test Cases from Spec

### 3.1 Feature Map

Modern automotive infotainment (also referred to as In-Vehicle Infotainment, IVI) is a heterogeneous stack: head-unit, connectivity module, display, audio amplifier, telematics control unit. Each layer has its own feature list and spec.

| Sub-system | Features | Spec-anchored test angle |
|---|---|---|
| HMI / Display | Touch response, gesture, multi-window, day/night theme, font scaling | Latency, contrast, render correctness |
| Radio | AM/FM, RDS, DAB+, SiriusXM, HD Radio | Frequency lock, RDS-TA flag, blend time |
| Media | USB, Bluetooth audio (A2DP/AVRCP), Apple CarPlay, Android Auto, iPod mode | Codec negotiation, artwork, track forward/back |
| Navigation | GPS, dead-reckoning, map update, route guidance, traffic, POI | Re-route latency, GPS-denied behaviour |
| Connectivity | Wi-Fi (station/AP), Bluetooth (profiles HFP/A2DP/AVRCP/PBAP/MAP), LTE/5G, NFC | Profile handshake, throughput |
| Voice | Speech recognition, TTS, barge-in, voice prompts | WER thresholds, language variants |
| Phone | Hands-free, phonebook sync, SMS read-out | PBAP sync time, HFP audio |
| Apps / Projection | CarPlay, Android Auto, vendor app store | App launch time, projection dropouts |
| RSE | Rear-seat entertainment, HDMI/USB-C, screen control | Independent control, parental lock |
| HVAC integration | Seat heater, climate control surfaces on head-unit | Status sync, refresh rate |
| Vehicle data | Energy info, tyre pressure, door status | Refresh, accuracy vs. CAN source |

Sources: [3_infotainment_feature_taxonomy_and_test_cases_from_spec[0]] [7], [3_infotainment_feature_taxonomy_and_test_cases_from_spec[1]] [9].

### 3.2 Anatomy of an Infotainment System Spec

A practical IVI SyRS / FSD will include:
1. **Use cases** (diagrammed as UML state machines or activity diagrams).
2. **Screen flows** (wireframes + state transitions).
3. **Signal list** (CAN signals consumed/produced - parking, vehicle speed, ignition state, light status, GPS-coordinates from telematics module, etc.).
4. **Performance budgets** (boot time, source-switch latency, audio-video sync skew).
5. **UX / Accessibility** (font scaling, colour-blind mode, voice prompts, button sizes per ISO 15005 / ISO 9241).
6. **Cybersecurity** (signed updates per UN R155, sandboxed apps).
7. **Diagnostics** (UDS on CAN, $22 to read head-unit part number, $31 to run radio self-test).

### 3.3 Worked Example - Bluetooth Pairing from Spec

Spec row: **"REQ-IVI-BT-014: When a new Bluetooth device is in pairing range and no device is currently connected, the HMI shall show a pairing prompt within 5 s; if the user accepts within 30 s, the HFP and A2DP profiles shall be established within 8 s."**

| TC ID | Type | Preconditions | Steps | Expected Result | Pass / Fail signal |
|---|---|---|---|---|---|
| TC-BT-014-P01 | Positive | Head-unit in IDLE BT state, no paired devices. New phone "PX9" discoverable. | 1. Bring PX9 into cabin. 2. Wait 5 s. 3. Accept on HMI. | Prompt shown in <= 5 s; HFP+A2DP up in <= 8 s after accept | Pass if timer reading < 8 s |
| TC-BT-014-N01 | Negative - already connected | One phone connected. New phone "PB5" enters range. | 1. Park near PX9 already connected. 2. Bring PB5 close. | HMI does NOT show new-pair prompt while PX9 is in active call | Pass if no auto-prompt; option to switch exists in settings |
| TC-BT-014-B01 | Boundary - timeout | HMI prompts but user does nothing. | 1. Trigger prompt. 2. Wait 35 s idle. | Prompt times out and is dismissed | Pass if prompt gone after 30-32 s |
| TC-BT-014-N02 | Negative - 2 paired phones | Two phones in paired list: PX9 (HFP only) and PB5 (A2DP only). | 1. Both in range. 2. Power-cycle head-unit. | Head-unit auto-connects PX9 HFP and PB5 A2DP concurrently | Pass if both profiles live |

**Mechanism -> Implication.** Pairing prompt vs *connection state* are two different signals; the spec above only mentions the prompt timer. An experienced tester will write a separate TC-BT-014-P02 that measures the connection establishment latency in isolation, because in some lab settings the prompt is fast (5 s) but the SDP / RFCOMM handshake takes 12 s - the system is plausible-looking but does not meet the contract.

---

## 4. Cluster (Instrument Cluster) - Feature Taxonomy and Test Cases from Spec

### 4.1 Feature Map

A digital instrument cluster is the driver-facing display that replaces the mechanical gauges. Spec rows cluster around three families:

| Family | Examples | Spec source |
|---|---|---|
| Gauges & indicators | Speedometer, tachometer, fuel gauge, coolant temp, e-Power/SoC, ADAS state bar | OEM SyRS |
| Telltales & warning indicators | Brake, airbag, ABS, ESP, EPS, engine check, oil pressure, battery, tyre pressure, seat-belt, door ajar, high-beam, low-beam, fog lamp, turn signal | **ISO 2575** dictates symbol and colour, **FMVSS/ECE Reg. 121** dictates mandatory telltales |
| Driver information / message centre | Trip meter (A/B), average consumption, range, DTE, navigation turn-by-turn popup, ADAS banner, gear indicator, odometer | OEM FSD |
| Modes | Day / night / auto, ECO / Sport / Off-road, theme variants | OEM HMI spec |
| HUD projection | Speed, navigation arrow, ADAS state | OEM HMI opt-in |
| Diagnostics | Self-test at KL15 ON, lamp sweep, DTC display, mileage tamper detection | [4_cluster_instrument_cluster_feature_taxonomy_and_test_cases_from_spec[0]] [33] |

Sources: [4_cluster_instrument_cluster_feature_taxonomy_and_test_cases_from_spec[1]] [36], [4_cluster_instrument_cluster_feature_taxonomy_and_test_cases_from_spec[2]] [21].

### 4.2 The Colour Code from ISO 2575

ISO 2575 binds the colour of every telltale. This is the single most-skipped rule by junior testers, and the most-flagged compliance audit item.

| Colour | Meaning (from spec) | Example telltales |
|---|---|---|
| Red | Serious, immediate danger; stop safely | Engine oil pressure, brake system warning, airbag, coolant temperature |
| Yellow / Amber | Caution; non-immediate malfunction | Check engine, ABS, ESP, tyre pressure low, low fuel |
| Green | Safe, normal operating | Turn signal, high beam, cruise set |
| Blue | High-beam indicator on some markets | High beam |

A test case for a telltale MUST include the colour check, the symbol conformity per ISO 2575, and the illumination state in self-test at KL15 ON. OEMs commonly use this **3-check** pattern: `symbol == spec AND colour == spec AND self-test == spec`.

### 4.3 Worked Example - Low-Fuel Telltale from Spec

Spec rows typically look like:
- **REQ-CL-FUEL-001**: When fuel level < 7% ± 0.5%, the low-fuel telltale shall illuminate in amber (per ISO 2575 symbol "low fuel").
- **REQ-CL-FUEL-002**: When fuel level < 5%, an audible chime shall sound once.
- **REQ-CL-TEST-005**: At KL15 ON, every warning telltale shall illuminate for 2 s during lamp self-test.

| TC ID | Type | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-FUEL-001-P01 | Positive - threshold | Fuel level set to 6.5% via test mode | 1. KL15 ON. 2. Wait 3 s. | Telltale ON continuously; amber; ISO-2575 symbol |
| TC-FUEL-001-B01 | Boundary - just above threshold | Fuel level = 7.5% | 1. KL15 ON. | Telltale OFF |
| TC-FUEL-001-B02 | Boundary - audio cue | Fuel level = 4.5% | 1. KL15 ON. | Telltale ON + chime ONCE for 300-700 ms |
| TC-FUEL-001-N01 | Negative - sensor loss | CAN signal FuelLevel invalid (DTC P0463 active) | 1. KL15 ON. | Telltale remains OFF (no false low-fuel); DTC visible via UDS $19 |
| TC-FUEL-TEST-005-P01 | Positive - lamp sweep | Fresh ECU after flash | 1. KL15 ON. | All amber/red telltales lit for 2 s +- 200 ms |

**Mechanism -> Implication.** Telltale-symbol regressions are a recurring NC (non-conformity) in ASPICE audits because teams test functionality through the HMI but forget to test the *symbol bitmaps* themselves. Always include a reference-image comparison for the SWS (software specification) symbols against ISO 2575 reference art.

---

## 5. Telematics - Feature Taxonomy and Test Cases from Spec

### 5.1 Feature Map

Telematics sits at the boundary between vehicle-internal networks and the carrier cloud. Its feature catalogue is broader than at first glance.

| Domain | Feature | Source / standard |
|---|---|---|
| Emergency | eCall (EU), ERA-GLONASS (Russia), bCall | UN R144, EU 2015/758, GOST-R |
| OTA | FOTA (firmware), SOTA (software), delta updates, signed bundles | UN R156, OEM-specific |
| V2X | C-V2X (PC5 / Uu), DSRC, V2V, V2I, V2P, V2N | ETSI EN 302 637, IEEE 802.11p, 3GPP Rel. 14 |
| Remote | Lock/unlock, climate pre-conditioning, charge control, honk-and-find, send-to-car (POI), valet mode | OEM proprietary, e.g. Tesla, BMW Connected |
| Concierge / Voice | Operator call button, AI voice | Connected services |
| Fleet / UBI | Driver behaviour scoring, geofencing, mileage reports | UBI programmes |
| Stolen Vehicle Tracking (SVT) | Silent alarm, GPS pinging, immobiliser | Insurance / police |
| Diagnostics over cellular | Remote DTC read, predictive maintenance | OEM backend |
| Insurance SOS | Crash data dispatch | OEM / insurer |
| Wi-Fi hotspot | In-cabin Wi-Fi AP | Carrier plans |

Sources: [5_telematics_feature_taxonomy_and_test_cases_from_spec[0]] [18], [5_telematics_feature_taxonomy_and_test_cases_from_spec[1]] [17].

### 5.2 Anatomy of a Telematics SyRS

Telematics specs are remarkably protocol-heavy. A typical table of contents:
1. **Regulatory scope** - jurisdictional applicability (EU, RU, NAFTA, China, India, Japan).
2. **Hardware** - TCU (Telematics Control Unit), SIM (eUICC), GNSS antenna, backup battery requirements (e.g. eCall needs 5+ minutes of voice + 1+ hour of MSD retention after main battery cut).
3. **Cellular stack** - LTE Cat-4 minimum, 5G NR optional, fallback to 2G/3G.
4. **GNSS** - multi-constellation (GPS / GLONASS / Galileo / BeiDou / IRNSS), cold-start TTFF, position accuracy.
5. **Voice / Audio** - hands-free audio, speakerphone, microphone routing.
6. **Back-end protocol** - MQTT, HTTP/REST, gRPC over TLS 1.2+, certificate handling.
7. **Security** - TLS, PKI, signed OTA bundles, secure boot, attestation.
8. **eCall trigger / MSD** - exact byte-level definition of MSD per EN 15722.
9. **OTA flow** - campaign definition, download to TCU, integrity check, install schedule, rollback.
10. **Privacy / Data retention** - GDPR-style data classes, opt-in/opt-out.

### 5.3 Worked Example - eCall MSD Transmission

Spec excerpt ("REQ-TCU-eCall-001"): **"On automatic or manual trigger, the TCU shall encode the Minimum Set of Data (MSD) per EN 15722 within 1 s, dial the 112 emergency number over the in-vehicle cellular modem, transmit the MSD after voice line is established, and retry transmission up to 3 times if ACK is not received."** Required MSD fields include: messageIdentifier (latest version), timeStamp (UTC milliseconds), position (lat/lon), positionConfidence (semi-major/minor axes), vehicleType, vehicleIdentificationNumber (VIN), propulsionType (gasoline/diesel/electric/hybrid), and trigger (automatic/manual).

Source: [5_telematics_feature_taxonomy_and_test_cases_from_spec[2]] [28].

| TC ID | Type | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-eCall-001-P01 | Positive - manual trigger | TCU on cellular network, GPS fix valid | 1. Press eCall button. 2. Wait 3 s. | Voice line established; MSD sent; ACK received from PSAP within 30 s |
| TC-eCall-001-P02 | Positive - automatic trigger | Crash event injected via CAN (AB deployed + delta-v > 5 km/h) | 1. Inject crash. | TCU auto-establishes voice + MSD without driver input; lamp ON for 3 s + audible warning |
| TC-eCall-001-N01 | Negative - no cellular | Cellular modem in "no service" | 1. Press eCall. | TCU retries 3 times; then logs DTC; lamp ON; does NOT drain backup battery |
| TC-eCall-001-N02 | Negative - GPS denied | No fix for > 60 s | 1. Press eCall. | MSD transmitted with last-known position and confidence flag set to "less-than" |
| TC-eCall-001-B01 | Boundary - MSD timeStamp | Inject MSD at UTC midnight | 1. Trigger eCall. | timeStamp field encodes full ms precision, validated by PSAP tester parser |

**Mechanism -> Implication.** The MSD is a binary blob - testers must validate the actual bytes with a hex dump or a regression-checked JSON. eCall certification labs (cetecom, Rohde & Schwarz) run a PSAP simulator that decodes MSD; if you don't gate against it, you can ship an MSD with the right field count but wrong byte order and pass HMI tests but fail regulatory certification [5_telematics_feature_taxonomy_and_test_cases_from_spec[3]] [29].

### 5.4 Worked Example - OTA Campaign

Spec row: **"REQ-OTA-014: The Telematics unit shall receive an OTA campaign metadata blob over cellular, verify its signature against the OEM root CA within 60 s, and proceed to download only if valid."**

| TC ID | Type | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-OTA-014-P01 | Positive | Campaign blob signed with valid OEM CA | 1. Publish campaign to backend. 2. Wait for TCU poll. | TCU verifies signature, downloads payload, initiates install |
| TC-OTA-014-N01 | Negative - bad sig | Campaign blob signed with test CA | 1. Publish rogue campaign. | TCU rejects, logs DTC, alerts backend, no install |
| TC-OTA-014-B01 | Boundary - large payload | 4 GB delta payload | 1. Publish. | Download completes within tolerance; system resumes after ignition off |
| TC-OTA-014-N02 | Negative - revoked cert | CA revoked in CRL | 1. Publish. | TCU rejects, fallback to previous firmware |

### 5.5 Worked Example - Remote Command Lock/Unlock

Spec row: **"REQ-RMT-007: A signed remote command 'UNLOCK' from the OEM mobile app shall, within 5 s, cause the Body Control Module to unlock doors. Maximum 3 retries if CAN ack not received."**

| TC ID | Type | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-RMT-007-P01 | Positive - normal | Car parked, app connected | 1. Send remote unlock from app. | Doors unlock + audible chirp + mobile confirmation in <= 5 s |
| TC-RMT-007-N01 | Negative - bad sig | Spoofed signature | 1. Send malicious unlock. | TCU rejects, no unlock, security log entry |
| TC-RMT-007-N02 | Negative - speed threshold | Vehicle moving > 5 km/h | 1. Send unlock. | TCU rejects - remote unlock disabled in motion |
| TC-RMT-007-B01 | Boundary - no cellular | Edge coverage hole | 1. Send unlock 5 times in 60 s. | App queues; retries when modem returns; success then within 10 s of regaining signal |

---

## 6. Universal Test-Case Authoring Template

Across all four domains, the test cases above obey one structure. Make this your team's standard.

```
TC-<DOMAIN>-<FEATURE>-<SEQ>  e.g. TC-CL-FUEL-001-B01
-------------------------------------------------------------------
Title               : <short imperative phrase>
Type                : Positive | Negative | Boundary | Performance | Security | Soak
Priority            : P1 / P2 / P3
ASIL (if relevant)  : QM | A | B | C | D
Spec trace          : <SyRS ID>  +  <IRS ID if interface-level>
Verification method : Test | Analysis | Inspection | Demonstration
Preconditions       : <test bench state, vehicle state, network state, signal injection>
Test data           : <explicit values, vectors>
Steps               : 1. <action>
                      2. <action> ...
                     N. <action>
Expected results    : <observable - cluster pixel / CAN signal / DTC / audio / network log>
Pass criteria       : <measurable threshold, including tolerance>
Fail criteria       : <observable that constitutes fail>
Environment         : Bench / HIL / Vehicle / Simulated
Tools required      : <CANoe, Wireshark, oscilloscope, GNSS simulator, audio analyser, etc.>
Author / Reviewer   : <name> @ <date>
Execution history   : <run id, build id, outcome>
```

### 6.1 Why this matters - traceability is the auditor's first question

ASPICE SWE.6 BP5 explicitly demands **bidirectional traceability** between (1) software requirements and (2) qualification test specification *including test cases*, and between (3) test cases and (4) test results [6_universal_test_case_authoring_template[0]] [45]. The `Spec trace` and `Execution history` fields above are what makes your test pack auditable. An assessor can click `TC-CL-FUEL-001-P01 -> REQ-CL-FUEL-001 -> TC-RUN-2024-11-17-04` and see coverage in both directions.

### 6.2 Test technique checklist - which technique when?

| Spec pattern | Recommended test technique | Example |
|---|---|---|
| Behaviour varies by value within a range | Equivalence partitioning + boundary | ACC time-gap 1.2 / 1.5 / 1.8 s |
| Output is a lookup of inputs | Decision table | Phone-projection vs encrypted connection |
| Inputs follow order | State transition testing | Cluster lamp sweep after KL15 ON |
| Fault response required | Fault injection (negative test) | Sensor mis-alignment, GNSS denied |
| Timing constrained | Timing/performance test | Pairing prompt in <= 5 s |
| Security-critical | Stroke / fuzz / signed-vs-unsigned | OTA signature validation |
| User-visible | UX / usability scoring | Touch latency, font legibility |
| Statutory | Standards regression | UN R144 eCall MSD, ISO 2575 telltales |

---

## 7. Standards Quick-Reference Map

| Standard | What it covers | Use in your test pack |
|---|---|---|
| **IEEE 829 / ISO/IEC/IEEE 29119** | Test documents (8 artefacts) | Template your TC structure |
| **Automotive SPICE (PAM 3.1)** | Process assessment for engineering | Process gate for ASPICE Level 2/3 |
| **ISO 26262** | Functional safety, ASIL allocation | Drives fault-injection & diagnostic coverage tests |
| **ISO 14229 (UDS)** | Diagnostic protocol on CAN/IP | Drives every $10/$11/$22/$27/$2E/$31/$36/$37/$85 test |
| **ISO 15765** | UDS on CAN (transport + network) | Multi-frame TP test cases |
| **ISO 11898** | CAN physical / data link | Bus-off / error-frame test cases |
| **ISO 2575** | Telltale symbols + colours | Cluster symbol regression |
| **UN R144** | eCall type approval | MSD byte-level certification |
| **UN R155** | Cybersecurity management | Signed bundle, secure OTA tests |
| **UN R156** | OTA software update | Rollback, version check tests |
| **UN R157** | Automated Lane Keeping (ALKS) | ODD tests for SAE L3 features |
| **EN 15722** | eCall MSD data format | Hex-dump regression in eCall tests |
| **ECE Reg. 121** | Telltale location/orientation | Cluster layout tests |
| **GM HIT / FMVSS 126** | ESC test rig | BSD / LKA tests |
| **ISO 15005 / ISO 9241** | In-vehicle HMI ergonomics | Touch latency, font scale tests |
| **3GPP Rel. 14** | C-V2X (PC5) | V2X message reception tests |
| **IEEE 802.11p / ETSI ITS-G5** | DSRC | V2X round-trip-time tests |

Source for ASPICE: [7_standards_quick_reference_map[0]] [2], [7_standards_quick_reference_map[1]] [3].

---

## 8. Domain Comparison - Same Spec, Different Test Grammar

The single largest insight for new engineers: the four domains are not just different *features*; they are different *genres of test*, with different state machines and different failure modes.

| Dimension | ADAS | Infotainment | Cluster | Telematics |
|---|---|---|---|---|
| **Primary spec driver** | OEM SyRS + ISO 26262 + UN R157 | OEM SyRS + UX standards + UN R155 | OEM SyRS + ISO 2575 + ECE R121 | OEM SyRS + UN R144/R155/R156 + carrier |
| **State machine granularity** | Module-level sub-state (Active / Standby / Degraded) often +20 states | Session-level (Idle / Connected / Streaming / Error) | KL15 / Lamp-sweep / Display ON | Network-level (Registered / Roamed / CSFB / No service) |
| **Time-critical?** | Yes - sub-second TTC windows | Latency-sensitive but tolerant of 100 ms+ | 50 Hz typical refresh; OEM-budgeted | Variable - 60 s verify, 30 s PSAP ACK, 5 s remote cmd |
| **ASIL ceiling for new code** | Often ASIL B/C/D for AEB, LKA, NOA | Typically QM (audio amplifiers may be ASIL B) | Mostly QM, dim-by-night may be ASIL B | Mixed - eCall path often ASIL B, OTA staging path QM |
| **Primary test bench** | HIL with sensor-fusion models + vehicle | HIL or HiL-class IVI rig + audio analyser + GNSS stim | HIL + display-capture cameras + CAN playback | Bench with cellular + GNSS sim + cloud simulator |
| **Test technique emphasis** | Fault injection + boundary + scenario | Use-case + state + UX | Symbol regression + signal-fidelity + timing | Protocol + signature + call-flow + failure-mode |
| **Automation rate (industry average)** | ~70% HIL, 30% vehicle | ~50% scriptable, ~50% manual UX | ~60% can be automated (image diff) | ~80% protocol-level automat-able |
| **Where bugs hurt** | Wrong brake / wrong path | Bad UX / crash car-play | Wrong telltale colour / dark display | Failed eCall / bricked ECU post-OTA |

---

## 9. Synthesis - The Repeatable Across the Domains

After working through all four domains, three principles stand out as the cross-cutting "how to write test cases from a spec" framework.

1. **Read the spec row, not the spec document.** A testable requirement contains 5 things: a verb ("shall"), an actor, an observable output, a quantitative threshold, and a verification method. If any of these are missing, return to the spec author. Do not invent values.
2. **Carry three test cases per requirement.** One positive, one negative (fault or invalid input), one boundary. ASPICE SWE.6 BP1 makes the negative and boundary cases part of your regression strategy [9_synthesis_the_repeatable_across_the_domains[0]] [45]. Without them, your pack is auditable but not robust.
3. **Pick the test technique to match the spec genre.** Sensor window -> boundary + fault injection; protocol state -> state transition; visible UI -> UX scoring; protocol message -> byte-level regression. The same "test case" template ships across all four domains, but the technique inside differs.

**Tension worth noting.** OEMs sometimes push for "test less, ship faster". A common failure is to drop negative cases on the basis that "the function works in positive case, we'll fix bugs later". This decision directly conflicts with ASPICE SWE.6 and ISO 26262 expectations. The right resolution is to keep negative cases but automate them at HIL level rather than vehicle level, which preserves coverage at lower cost.

**Counter-case.** A team that automates EVERYTHING runs into the inverse problem - their regression pack takes 8 h to run, engineers stop trusting it, false positives bury real bugs. Pick automation by spec genre: ADAS and Telematics benefit enormously (sensor stimuli deterministic); Cluster image-diff requires careful golden-image management; Infotainment UX is best validated by a small panel of human reviewers on top of scripted UI tests.

---

## References

1. *IEEE 829 Test Documentation Guide | PDF | Software Testing ...*. https://www.scribd.com/document/612852040/Test-Documents-IEEE-829-Full-Template
2. *Automotive SPICE Guide: Reliability, Safety, Compliance*. https://www.srmtech.com/knowledge-base/blogs/automotive-aspice-compliance
3. *Traceability in ASPICE & ISO 26262: Automotive Compliance ...*. https://thetraceabilityhub.com/traceability-in-aspice-automotive-projects-iso-26262-compliance-best-practices
4. *IEEE 829: Software Test Documentation Standard | PDF Scribd https://www.scribd.com › IEE...*. https://www.scribd.com/document/840794125/IEEE-829
5. *Automotive SPICE and ISO 26262 in Engineering - Lemberg Solutions*. https://lembergsolutions.com/blog/impact-automotive-spice-and-iso-26262-your-engineering-process
6. *Infotainment system penetration testing with our test lab*. https://expleo.com/global/en/case-studies/infotainment-system-penetration-testing
7. *Infotainment Testing*. https://atesteo.com/en/engineering/infotainment-and-telematics-validation
8. *Infotainment testing products & solutions*. https://expo.digiteqautomotive.com/
9. *Infotainment Test System for automotive applications*. https://www.safran-group.com/products-services/infotainment-test-systems-automotive-applications
10. *Infotainment Test for Automotive Applications*. https://www.goepel.com/en/automotive-test-solutions/test-systems/infotainment-tester
11. *ADAS是向更高级自动驾驶（如L3、L4乃至L5）演进的基础*. https://www.sohu.com/a/888755299_121398040
12. *ADAS中的AEB、AES、ACC、FCW、LDW、LCA、BSD、APA、DMS、NOA、TSR*. https://zhuanlan.zhihu.com/p/49394124464
13. *ADAS（高级驾驶辅助系统）全解： DFM、FCW、LDW、BSD、AEB、AES、LKA....*. https://auto.jgvogel.cn/c1538405.shtml
14. *ADAS功能介绍 - ACC (一)_iso 22179-CSDN博客__财经头条__新浪财经*. https://cj.sina.com.cn/articles/view/7880068201/1d5b04c6901901zb0m
15. *Understanding ADAS*. https://www.korewireless.com/blog/understanding-adas-systems
16. *Telematics Testing and Design Solutions*. https://www.intertek.com/automotive/telematics-infotainment
17. *Telematics Testing*. https://www.tataelxsi.com/industries/automotive/system-testing-and-hils/telematics-testing
18. *Automotive Telematics & Connectivity | IC Navigator*. https://icnavigator.com/applications/automotive-electronics-assemblies/telematics-connectivity
19. *Vehicle Telematics: OTA, Teleoperations and Fleet Management ...*. https://www.rti.com/industries/automotive/vehicle-telematics
20. *Automotive Telematics: Architecture, Standards & Outlook*. https://www.kbvresearch.com/blog/automotive-telematics-architecture-standards
21. *Automotive instrument cluster*. https://www.infineon.com/application/automotive-instrument-cluster
22. *Nippon Seiki Ohio / New Sabina Industries, Inc. Information*. http://rocketreach.co/nippon-seiki-ohio-new-sabina-industries-inc-profile_b55c9853f60cb642
23. *An instrument cluster is the primary display panel located on the dashboard behind the steering wheel. It houses*. https://www.jegs.com/part-type/Instrument%2BCluster
24. *Cluster Dashboard - Test Bench - u-obd.com*. https://www.u-obd.com/product-category/test-bench/cluster
25. *Visteon supplies digital instrument cluster to new Kia Sonet ...*. https://autotechinsight.spglobal.com/news/5257526/visteon-supplies-digital-instrument-cluster-to-new-kia-sonet-compact-suv-in-indian-market
26. *eCall Systems Functional Specification*. https://www.scribd.com/document/487493516/heero2-wp2-del-d2-2-functional-specification-v1-0
27. *D2.2 - eCall systems functionalities’ specification - PDF4PRO*. https://pdf4pro.com/cdn/d2-2-ecall-systems-functionalities-specification-1c2f70.pdf
28. *eCall certification & testing - cetecom advanced*. https://cetecomadvanced.com/en/certification/ecall-certification
29. *Automotive eCall testing - Rohde & Schwarz*. https://www.rohde-schwarz.com/us/solutions/automotive-testing/automotive-connectivity-and-infotainment/automotive-ecall-testing/overview_231772.html
30. [[PDF] Four Considerations for Designing Emergency Call (eCall)](https://www.ti.com/lit/pdf/SPRT818)
31. *UDS Testing Guide - ISO 14229 Automation | TestBot*. https://www.etestbot.com/guides/uds-testing
32. *UDS - Unified Diagnostic Services - ISO 14229 | Vector*. https://www.vector.com/int/en/products/solutions/diagnostic-standards/uds-unified-diagnostic-services-iso14229
33. *UDS Protocol Deep Dive: Mastering ISO 14229 for Vehicle ...*. https://nexteraautomotive.com/blog/uds-protocol-deep-dive-iso-14229
34. *UDS Diagnostics & Secure ECU Reprogramming - beefed.ai*. https://beefed.ai/en/implement-uds-diagnostics-secure-reprogramming
35. *UDS Protocol | Unified Diagnostics Services | Vehicle Diagnostics*. https://automotivevehicletesting.com/vehicle-diagnostics/uds-protocol
36. *INTERNATIONAL ISO STANDARD 2575*. https://cdn.standards.iteh.ai/samples/68409/6480e873c14b4e56b7a0066b3ef65afc/ISO-2575-2021.pdf
37. *ISO 2575 - auto.gosstandart.info*. http://auto.gosstandart.info/data/documents/ISO-2575.pdf
38. *Iso 2575 2021 | PDF*. https://www.scribd.com/document/805218373/ISO-2575-2021
39. *ISO 2575:2004 - Symbols for controls, indicators and tell ...*. https://www.iso.org/standard/39704.html
40. *Symbols for controls, indicators and tell-tales (ISO 2575 ...*. https://www.sis.se/en/produkter/standardization/graphical-symbols/for-specific-equipment/ssiso25752010
41. *Automotive SPICE - MATLAB & Simulink*. https://www.mathworks.com/discovery/automotive-spice.html
42. *1. Automotive SPICE Overview*. https://reactive-systems.com/automotive-spice/aspice-overview.html
43. *Automotive SPICE®*. https://vda-qmc.de/wp-content/uploads/2023/02/Automotive_SPICE_PAM_31_EN.pdf
44. *Automotive SPICE Process Assessments UL Solutions https://www.ul.com › sis › services › automotive-spice-...*. https://www.ul.com/sis/services/automotive-spice-process-assessments
45. *Overview - SWE.6 Software Qualification Test*. https://alef1986.github.io/ASPICE-Archi/0c6fbcf4-57de-4e25-a1b4-d9a0fa460c16/views/39fd8768-cc1e-4b28-afb3-daf801742eff.html
46. [[DOC] System Requirements Specifications Template](https://dir.texas.gov/sites/default/files/System%20Requirements%20Specifications%20Template.doc)
47. [[PDF] IEEE Software Requirements Specification Template - ITE.org](https://www.ite.org/ITEORG/assets/File/Standards/Task3-2_1_CVPFS-System_Requirements_Specifications_Release_1_0.pdf)
48. [[PDF] D1.2.1 - System Requirements Specification - ITEA4](https://itea4.org/project/workpackage/document/download/4842/D1.2.1.%20INSIST%20-%20System%20Requirements%20Specification.pdf)
49. [[PDF] SYSTEM REQUIREMENTS SPECIFICATION FOR THE U.S. ...](https://pubs.usgs.gov/of/1991/0525/report.pdf)
50. *How to Write a System Requirements Specification (SRS) Document*. https://www.jamasoftware.com/requirements-management-guide/writing-requirements/system-requirements-specification

