# Project Walkthroughs — STAR Method Answers

> **STAR** = Situation → Task → Action → Result
> Interviewers evaluate: problem-solving, technical depth, ownership, and impact.
> Prepare 2 stories per project. Practice telling each in 2–3 minutes.

---

## Project 1: BYD — ADAS ECU Validation (Most Recent — Lead With This)

### Story 1A: Ultrasonic Sensor False Detection Bug

**Situation:**
"At BYD, I was responsible for end-to-end validation of the Parking Assist system using ultrasonic sensors. During HIL testing, we discovered that the parking sensors were falsely detecting obstacles when the vehicle approached metal bollards and guardrails at low speed — about 5–10 km/h. This was causing unnecessary parking warnings and automatic braking interventions, which was a P1 safety issue."

**Task:**
"I was tasked with reproducing the issue on the HIL bench, identifying the root cause, and ensuring it was fixed before the production release."

**Action:**
"First, I analyzed the CAN logs in CANoe and found that the ultrasonic echo signal patterns from metal surfaces had a similar reflection profile to real obstacles — specifically, the echo amplitude and time-of-flight values overlapped with valid obstacle ranges at 1m and 3m.

I designed new edge-case test scenarios covering different surface materials — metal, glass, wood, and plastic — at distances of 0.5m, 1m, 3m, and 5m. I wrote CAPL scripts to inject these echo patterns on the dSPACE HIL bench, so we could reproduce the issue without needing a physical test track every time.

I also performed UDS diagnostics — using service 0x22 to read the sensor calibration DIDs and 0x19 to check if any DTCs were logged during the false detections. The diagnostics showed no DTC, which meant the ECU considered the detection 'valid' — confirming the issue was in the algorithm, not the hardware.

I shared my analysis with the software team, who found that the material-type filter in the signal processing algorithm was not active below 15 km/h. They fixed the filter threshold, and I re-ran the complete test suite."

**Result:**
"The fix resolved the false detection issue across all material types. My CAPL-based HIL test scenarios were added to the regression suite permanently, which improved defect detection efficiency by 30%. The issue was caught and resolved before production release, avoiding a potential field recall."

---

### Story 1B: CAPL Automation for Regression Testing

**Situation:**
"At BYD, our ADAS regression test suite had about 200 test cases that were executed manually every sprint. This was taking 3 full days of manual effort per cycle and was prone to human error — sometimes signal boundary checks were missed."

**Task:**
"I was asked to automate the repetitive CAN-signal-level test cases to reduce execution time and improve reliability."

**Action:**
"I identified 120 out of 200 test cases that were purely CAN-signal-based — things like verifying signal ranges, timeout behavior, default values on bus-off, and DTC response to fault injection.

I wrote CAPL scripts in CANoe that:
- Simulated vehicle speed, gear position, and sensor signals on the CAN bus
- Injected faults like signal timeout, bus-off, and invalid signal values
- Automatically checked CAN responses against expected values from the test specification
- Generated pass/fail reports in XML format compatible with our test management tool

I also added UDS automation — scripts that automatically sent 0x19 (Read DTC), verified DTC status bytes, and validated freeze frame data after each fault injection."

**Result:**
"Automation reduced regression execution from 3 days to less than 1 day — a 35% improvement in execution efficiency. The automated suite caught 3 critical bugs that were previously missed in manual execution due to timing-sensitive signal checks. The framework was adopted by the team for all future test cycles."

---

### Story 1C: Camera System Validation (RVC/MVC)

**Situation:**
"I was also responsible for validating the Reverse View Camera and Multi View Camera systems. We found that the camera display had a 400ms delay when shifting to reverse gear — the specification required activation within 200ms."

**Task:**
"Measure the exact activation delay, identify the bottleneck, and validate the fix."

**Action:**
"I set up a test scenario in dSPACE VT Studio where I simulated the gear shift from Drive to Reverse on the CAN bus and measured the timestamp delta between the GearPosition CAN signal change and the camera video stream activation signal.

Using CANoe trace tools, I measured the end-to-end delay:
- CAN signal propagation: ~10ms (normal)
- ECU processing time: ~380ms (too slow — should be <150ms)
- Total: ~390ms (exceeds 200ms requirement)

I logged a detailed defect in JIRA with the CAN trace screenshots, exact timestamps, and the signal names involved. The SW team found that the video initialization was waiting for 3 consecutive valid camera frames instead of 1, adding unnecessary latency."

**Result:**
"After the fix, the camera activation time dropped to 120ms — well within the 200ms requirement. I created a dedicated CAPL timing measurement script that became a standard tool for all camera feature validation."

---

## Project 2: BMW — ADAS & Cluster Validation

### Story 2A: Adaptive Cruise Control Sensor Failure Handling

**Situation:**
"At BMW, I was validating Adaptive Cruise Control (ACC) behavior under sensor failure conditions. During testing, I discovered that when the front radar sensor was simulated as 'lost' (no signal for 300ms), the ACC did not gracefully degrade — instead of handing control back to the driver with an alert, the system maintained the last known speed for 2 additional seconds."

**Task:**
"Investigate the degradation behavior, document the safety gap, and validate the fix."

**Action:**
"I used dSPACE HIL to simulate radar signal loss at different speeds — 30, 60, 80, and 120 km/h. For each speed, I measured:
- Time from signal loss to ACC warning on cluster
- Time from signal loss to ACC deactivation
- Whether the driver was prompted to take over

Using CANoe, I traced the signal flow: RadarStatus → ADAS_ECU → ACC_State → Cluster_Alert. I found that the ADAS ECU was waiting for 5 consecutive missing radar frames before declaring sensor loss — this 5-frame wait at 10Hz cycle time = 500ms, plus the internal debounce added another 1.5s.

I created requirement-gap documentation with exact signal traces and shared it with the BMW system team. They adjusted the debounce from 5 frames to 2 frames and added an immediate cluster warning on the first missing frame."

**Result:**
"After the fix, ACC degradation time dropped from 2+ seconds to under 500ms, meeting the ISO 26262 ASIL-B timing requirement. My test scenarios covering sensor loss at multiple speeds were incorporated into the HIL regression suite, improving test coverage by 30%."

---

### Story 2B: Cluster Telltale Defect Leakage Reduction

**Situation:**
"The Cluster testing team was experiencing defect leakage — bugs were escaping to the integration testing phase because telltale validation was mostly manual and focused on happy-path scenarios."

**Task:**
"Improve telltale test coverage to reduce defect escape rate."

**Action:**
"I reviewed the existing test cases and found they only covered ON/OFF states for telltales. They missed:
- Boundary conditions (e.g., fuel level exactly at 10L threshold)
- CAN signal timeout behavior (what happens when the CAN message stops?)
- Priority conflicts (two warnings competing for the same display area)

I designed 40 additional test cases covering these gaps and wrote CAPL scripts to:
- Inject CAN signals at exact boundary values
- Simulate CAN message timeouts for each telltale source signal
- Verify telltale priority logic when multiple warnings are active simultaneously

I used UDS 0x19 to verify that proper DTCs were set when telltale-related CAN signals timed out."

**Result:**
"Defect leakage from Cluster testing reduced by 25% over the next 3 releases. Two critical defects were found in the new test cases — one where the low fuel warning did not activate at exactly 10L, and another where the seatbelt warning was overridden by a less critical door-ajar warning."

---

## Project 3: Lexus (Concentrix) — Infotainment & Cluster

### Story 3A: Bluetooth A2DP Connectivity Issue Across Devices

**Situation:**
"At Lexus, we received field complaints that Bluetooth music streaming (A2DP) was dropping on certain Samsung phones after 15–20 minutes of playback. The issue was not reproducible on iPhone or Pixel devices."

**Task:**
"Reproduce the issue in the lab, identify the root cause, and validate the fix across all supported devices."

**Action:**
"I set up a test matrix of 8 phone models across Android and iOS. I connected each phone via Bluetooth, started A2DP streaming, and monitored for 30 minutes.

Key observations:
- Samsung S20, S21: disconnects at ~18 min (consistent)
- iPhone 12, 13: no disconnects
- Pixel 5: no disconnects

I captured BT HCI snoop logs from the head unit and analyzed them in Wireshark. I found that Samsung phones were sending an AVDTP SUSPEND command after 15 minutes of continuous streaming — this was triggered by Samsung's battery optimization feature that suspends background audio after 15 min.

The head unit was not handling the SUSPEND → RESUME transition correctly — instead of resuming, it was dropping the A2DP connection entirely.

I logged a detailed defect with HCI packet captures, timestamps, and device-specific behavior comparison. The SW team fixed the A2DP state machine to properly handle SUSPEND/RESUME."

**Result:**
"After the fix, all 8 devices streamed A2DP continuously for 2+ hours without disconnection. I created a standardized Bluetooth endurance test procedure (30-min soak test per device) that was adopted for all future Infotainment releases, reducing defect escape rate by 20%."

---

### Story 3B: Apple CarPlay / Android Auto Integration Testing

**Situation:**
"During Infotainment validation, we had to certify Apple CarPlay and Android Auto compatibility across 15+ phone models and multiple OS versions. The test matrix was large — about 300 test combinations — and we were behind schedule."

**Task:**
"Prioritize testing to cover maximum risk within the available time, and ensure core functionality was validated."

**Action:**
"I used a risk-based testing approach:
1. I categorized test combinations into High/Medium/Low risk based on:
   - Market share of phone model (top 5 phones = 80% of users)
   - OS version freshness (latest 2 versions = highest risk for compatibility)
   - Historical defect data (which phone models had most bugs in previous releases)

2. I created a priority matrix and got approval from the test lead to focus on the top 60 High-risk combinations first (covering 80% of real-world usage).

3. For each combination, I tested: connection setup, navigation projection, media playback, phone call handling, and disconnection/reconnection.

4. I documented all test results in DOORS with full traceability."

**Result:**
"We completed high-risk testing within the deadline. We found 5 critical bugs — 3 in Android Auto (USB reconnection issues on Pixel 6) and 2 in CarPlay (Siri voice routing to wrong speaker on iPhone 14). All were fixed before release. The prioritization approach was adopted as the standard strategy for future certification cycles, improving test coverage by 30% within the same time frame."

---

## How to Use These Stories in an Interview

### When Asked: "Tell me about a challenging bug you found"
→ Use **Story 1A** (ultrasonic false detection) or **Story 3A** (BT A2DP dropout)

### When Asked: "Tell me about your automation experience"
→ Use **Story 1B** (CAPL regression automation)

### When Asked: "How do you handle tight deadlines?"
→ Use **Story 3B** (CarPlay/Android Auto risk-based prioritization)

### When Asked: "Tell me about a safety-critical issue"
→ Use **Story 2A** (ACC sensor failure degradation)

### When Asked: "How did you improve test coverage?"
→ Use **Story 2B** (Cluster telltale defect leakage) or **Story 1B** (CAPL automation)

### When Asked: "Tell me about cross-team collaboration"
→ Use **Story 1A** (shared analysis with SW team) or **Story 2A** (worked with BMW system team)

---

## STAR Story Quick Reference Card

| # | Project | Story Title | Key Metric | Best For Question |
|---|---------|-------------|-----------|-------------------|
| 1A | BYD | Ultrasonic false detection | 30% defect detection improvement | Challenging bug, root cause analysis |
| 1B | BYD | CAPL regression automation | 35% execution efficiency | Automation experience |
| 1C | BYD | Camera activation delay | 390ms → 120ms | Timing/performance testing |
| 2A | BMW | ACC sensor failure handling | ISO 26262 compliance achieved | Safety-critical, sensor failure |
| 2B | BMW | Cluster telltale leakage | 25% defect leakage reduction | Test coverage improvement |
| 3A | Lexus | BT A2DP disconnection | 20% defect escape reduction | Device compatibility, debugging |
| 3B | Lexus | CarPlay/AA prioritization | 30% coverage in same time | Deadline pressure, prioritization |
