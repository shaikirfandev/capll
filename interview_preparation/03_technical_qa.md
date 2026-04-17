# Technical Q&A — Domain-Wise Interview Preparation

> 80+ questions with concise, interview-ready answers.
> Organized by domain. Focus on the domain matching the JD.
> For every answer: keep it under 1 minute unless asked to elaborate.

---

## Section 1: CAN Protocol (Always Asked — Prepare All)

### Q1: What is CAN? Explain the CAN frame structure.
**Answer:**
"CAN — Controller Area Network — is a serial communication protocol used in vehicles for real-time ECU communication. It uses differential signaling on two wires — CAN_H and CAN_L — and supports speeds up to 1 Mbit/s.

A standard CAN frame has:
- **SOF** (1 bit): Start of Frame
- **Identifier** (11 bits standard / 29 bits extended): Message priority — lower ID = higher priority
- **RTR** (1 bit): Remote Transmission Request
- **Control** (6 bits): includes DLC — Data Length Code (0–8 bytes)
- **Data** (0–64 bits): payload (0–8 bytes in classic CAN)
- **CRC** (15 bits): error detection
- **ACK** (2 bits): receiver acknowledges
- **EOF** (7 bits): End of Frame"

### Q2: What is the difference between CAN and CAN FD?
**Answer:**
"CAN FD — Flexible Data Rate — extends classic CAN in two ways:
1. **Data field**: up to 64 bytes (vs 8 in classic CAN)
2. **Bit rate switching**: the data phase can run at a higher speed (up to 8 Mbit/s) while the arbitration phase stays at 500 kbit/s

CAN FD maintains backward compatibility in the arbitration phase — both classic and FD nodes can coexist on the same bus during arbitration. But only FD-capable nodes can decode FD data frames."

### Q3: How does CAN arbitration work?
**Answer:**
"CAN uses non-destructive bitwise arbitration. When two nodes transmit simultaneously, each monitors the bus. A dominant bit (0) overwrites a recessive bit (1). The node transmitting a higher ID (more recessive bits) detects that its recessive bit was overwritten and backs off. The node with the lowest ID wins arbitration without losing data. This is why lower ID = higher priority."

### Q4: What happens during a CAN bus-off condition?
**Answer:**
"Every CAN node has a Transmit Error Counter (TEC) and Receive Error Counter (REC). When TEC exceeds 255, the node enters Bus-Off state — it stops transmitting AND receiving. To recover, the node must detect 128 occurrences of 11 consecutive recessive bits (the 'bus-off recovery' sequence). After recovery, counters reset to zero.

In my testing at BYD, I would simulate bus-off using CANoe fault injection and verify that the ECU recovered within the specification timeout — typically ≤ 1 second — and that proper DTCs were logged."

### Q5: What are CAN error types?
**Answer:**
"Five error types:
1. **Bit Error**: Node transmits a bit but reads back a different value
2. **Stuff Error**: More than 5 consecutive identical bits without a stuff bit
3. **CRC Error**: Received CRC doesn't match computed CRC
4. **Form Error**: Fixed-format field (EOF, ACK delimiter) has wrong value
5. **ACK Error**: Transmitter doesn't see dominant bit in ACK slot — no receiver acknowledged"

### Q6: What is CAN message timeout? How do you test it?
**Answer:**
"CAN message timeout means an expected periodic message is not received within its cycle time + tolerance. For example, if VehicleSpeed is sent every 20ms with a 10ms tolerance, timeout occurs if not received within 30ms.

In my testing, I used CAPL to stop transmitting a specific message and then verified:
1. The receiving ECU sets the signal to its default/substitute value
2. A proper DTC is logged (e.g., timeout DTC)
3. The feature degrades gracefully — for example, ACC disables if RadarObject message times out"

---

## Section 2: UDS Diagnostics (Frequently Asked)

### Q7: What is UDS? Name the services you've used.
**Answer:**
"UDS — Unified Diagnostic Services — is defined in ISO 14229. It's the standard protocol for ECU diagnostics — reading/writing data, DTCs, flashing firmware, and security access.

Services I've used extensively:
- **0x10** DiagnosticSessionControl — switching to Extended or Programming session
- **0x22** ReadDataByIdentifier — reading SW version, VIN, sensor values
- **0x2E** WriteDataByIdentifier — writing calibration data
- **0x19** ReadDTCInformation — reading DTC list, status, freeze frames
- **0x14** ClearDiagnosticInformation — clearing DTCs
- **0x27** SecurityAccess — seed/key authentication for protected operations
- **0x31** RoutineControl — triggering routines like flash erase or self-test
- **0x34/0x36/0x37** — RequestDownload, TransferData, TransferExit for ECU flashing
- **0x3E** TesterPresent — keeping session alive"

### Q8: Explain the UDS session types.
**Answer:**
"Three standard sessions:
1. **Default Session (0x01)**: Basic operations — read DTCs, read data. No security needed.
2. **Extended Session (0x03)**: Full diagnostic access — write data, clear DTCs, IO control. Usually requires security access (0x27).
3. **Programming Session (0x02)**: For ECU flashing. Requires security access. Non-diagnostic CAN messages are typically suppressed (0x28).

If you don't send TesterPresent (0x3E) every ~5 seconds, the ECU falls back to Default session automatically."

### Q9: What is a DTC? Explain the DTC status byte.
**Answer:**
"DTC — Diagnostic Trouble Code — is a fault code stored by an ECU when a monitored condition fails.

The status byte has 8 bits:
- Bit 0 (0x01): testFailed — currently failing NOW
- Bit 2 (0x04): pendingDTC — failed in previous or current cycle, not yet confirmed
- Bit 3 (0x08): confirmedDTC — failed in 2+ consecutive cycles
- Bit 7 (0x80): warningIndicatorRequested — MIL/telltale requested ON

At BYD, I would inject faults using CAPL, then read DTCs with 0x19 02 09 (confirmed + active), verify the correct status byte, and check freeze frame data with 0x19 06."

### Q10: Explain the Security Access (0x27) seed/key mechanism.
**Answer:**
"Security Access prevents unauthorized write/flash operations. The flow is:
1. Tester sends 0x27 [odd level] — RequestSeed
2. ECU responds with a random seed (4–8 bytes)
3. Tester computes a key using the seed + OEM-secret algorithm
4. Tester sends 0x27 [even level] — SendKey
5. ECU verifies the key — if correct, access granted

If wrong key is sent 3 times, ECU locks (NRC 0x36) for typically 10 minutes.

At BMW, I used security access for writing calibration DIDs and performing ECU flashing."

### Q11: What is a Negative Response Code (NRC)?
**Answer:**
"When the ECU rejects a UDS request, it sends: 7F [SID] [NRC code]. Common NRCs I've encountered:
- **0x22** conditionsNotCorrect — wrong session or ECU not ready
- **0x33** securityAccessDenied — haven't done 0x27 yet
- **0x31** requestOutOfRange — invalid DID or parameter
- **0x78** responsePending — ECU is processing, wait for final response
- **0x7F** serviceNotSupportedInActiveSession — need to switch session first"

### Q12: How do you flash an ECU using UDS?
**Answer:**
"The full flash sequence:
1. Enter Programming Session (0x10 02)
2. Security Access (0x27)
3. Disable normal CAN communication (0x28 03 01)
4. Disable DTC storage (0x85 02)
5. Erase flash (routine 0x31 01 FF00)
6. Request Download (0x34) — specify address and size
7. Transfer Data (0x36) — send multiple blocks
8. Transfer Exit (0x37) — end data transfer
9. Verify CRC (routine 0x31 01 FF01)
10. ECU Reset (0x11 01)
11. Re-enable communication (0x28 00 01) and DTC storage (0x85 01)

At Lexus, I performed ECU flashing using USB and ADB tools, and at BYD I used UDS-based flashing through CANoe."

---

## Section 3: ADAS Questions

### Q13: What ADAS features have you tested?
**Answer:**
"I've tested:
- **Parking Assist** (ultrasonic sensors — 1m, 3m, 5m range validation)
- **Blind Spot Detection (BSD)** — radar-based, tested detection zones and alert thresholds
- **Reverse View Camera (RVC)** and **Multi View Camera (MVC)** — activation timing, overlay accuracy
- **Adaptive Cruise Control (ACC)** — target following, cut-in/cut-out scenarios
- **Lane Keep Assist (LKA)** — lane marking detection, steering torque override
- **Forward Collision Warning (FCW)** — alert timing and threshold validation"

### Q14: How do you test ultrasonic sensor accuracy?
**Answer:**
"I validate detection at multiple ranges using the HIL bench:
1. Inject simulated echo signals at known distances: 0.5m, 1m, 3m, 5m
2. Verify detected distance on CAN matches the injected value within ±10cm
3. Test edge cases: moving obstacles, different materials (metal/glass/fabric)
4. Test boundary: just inside and just outside detection range
5. Test timeout: what happens when no echo returns (sensor blocked by mud/ice)

I used CAPL scripts to automate the sweep across distances and log pass/fail for each data point."

### Q15: What is sensor fusion and why is it important?
**Answer:**
"Sensor fusion combines data from multiple sensors — radar, camera, ultrasonic, LiDAR — to create a more reliable understanding of the environment.

For example, radar detects distance and velocity well but can't classify objects. Camera can classify (car/pedestrian/sign) but is affected by lighting. Fusion combines both: radar confirms an object at 40m, camera classifies it as a pedestrian → AEB decides to brake.

At BYD, I tested scenarios where radar detected an object but camera did not (false positive case) — this was my ultrasonic false detection bug where fusion logic was the key to root cause."

### Q16: How do you test ACC cut-in and cut-out scenarios?
**Answer:**
"Cut-in: a vehicle from an adjacent lane moves into my lane ahead. The ACC must detect the new target and reduce speed.
Cut-out: the vehicle ahead moves out of my lane. ACC must identify the next target or accelerate to set speed.

On HIL, I simulate these using dSPACE by:
1. Creating a radar target in the adjacent lane
2. Moving it laterally into my lane at a defined TTC (time-to-collision)
3. Verifying ACC braking response time and deceleration profile
4. For cut-out: removing the primary target and verifying smooth acceleration

I check CAN signals: ACC_TargetID, ACC_RequestedDecel, ACC_State, and verify no false braking or collision alerts."

---

## Section 4: Infotainment Questions

### Q17: What Bluetooth profiles have you tested?
**Answer:**
"I tested four main profiles at Lexus:
- **HFP** (Hands-Free Profile): phone call audio routing, dialing, contact sync
- **A2DP** (Advanced Audio Distribution Profile): music streaming quality, codec negotiation
- **PBAP** (Phone Book Access Profile): phone book download to head unit
- **MAP** (Message Access Profile): SMS notification display

For each profile, I tested: connection setup time, reconnection after power cycle, concurrent usage (streaming + call), and disconnection handling."

### Q18: How do you test Apple CarPlay / Android Auto?
**Answer:**
"I validate across multiple phone models and OS versions:
1. **Connection**: USB plug-in → CarPlay/AA projection within 10s
2. **Navigation**: route displayed on HU matches phone, voice guidance routed to car speakers
3. **Media**: audio controls (play/pause/skip) work from both phone and HU
4. **Phone calls**: incoming call → audio switches from media to call and back
5. **Disconnect/reconnect**: unplug USB → plug back → session resumes
6. **Multi-device**: switch between CarPlay and Android Auto without HU restart

At Lexus, I found critical USB reconnection bugs on Pixel 6 where AA would not re-project after brief disconnect."

### Q19: How do you debug a Bluetooth connection failure?
**Answer:**
"My approach:
1. **Reproduce consistently**: same phone, same HU state, same steps
2. **Capture BT HCI logs**: from the head unit using ADB or debug tool
3. **Open in Wireshark**: filter by BT protocol; look for pairing failures, role switch issues, or L2CAP disconnects
4. **Check profiles**: is it failing on all profiles or just A2DP? (narrows root cause)
5. **Compare devices**: if only Samsung fails, check Samsung-specific BT behavior (like battery optimization)
6. **Log defect with**: HCI packet capture, timestamps, device info, exact failure point in protocol"

---

## Section 5: Telematics Questions

### Q20: What is eCall and how does it work?
**Answer:**
"eCall is an EU-mandated emergency system (regulation 2015/758). When a crash is detected (airbag deployment), the TCU automatically:
1. Initiates a cellular voice call to the nearest PSAP (Public Safety Answering Point — 112)
2. Transmits an MSD (Minimum Set of Data) containing: vehicle position (GPS), VIN, timestamp, direction of travel, vehicle type, and crash severity
3. Opens a voice channel so the PSAP can communicate with occupants

The critical rule: eCall MUST work even without GPS — it uses the last known position with a confidence flag."

### Q21: What is OTA update and how do you test it?
**Answer:**
"OTA — Over-The-Air — allows updating ECU software remotely without visiting the dealer.

I test:
1. **Download**: package downloads completely over LTE; interrupted download resumes correctly
2. **Validation**: TCU verifies package signature, version compatibility, and integrity before applying
3. **Installation**: flash process completes; ECU boots with new version
4. **Rollback**: if installation fails, ECU recovers to previous version
5. **Negative cases**: wrong package for this ECU → rejected; interrupted mid-flash → FBL recovery
6. **Post-update**: verify SW version via UDS 0x22 F195; verify no DTCs after update"

### Q22: How do you test TCU behavior under poor network conditions?
**Answer:**
"I test network degradation scenarios:
1. **Signal loss**: attenuate RF signal gradually; verify TCU reconnects within spec time
2. **Latency**: add 500ms–2s delay to network; verify data packets aren't lost
3. **Handover**: simulate cell tower transition; verify no data dropped
4. **Low bandwidth**: throttle to 50 kbps; verify OTA download pauses/resumes
5. **No coverage**: fully remove signal; verify TCU caches data and retransmits when signal returns

I verify DTC logging for each condition and check that eCall still works as fallback."

---

## Section 6: Cluster Questions

### Q23: What is a telltale and how do you validate it?
**Answer:**
"A telltale is a warning indicator lamp on the instrument cluster — like the Check Engine Light, ABS lamp, low fuel, seatbelt warning, etc.

I validate:
1. **Activation condition**: inject the correct CAN signal value → telltale turns ON within 500ms
2. **Deactivation**: remove condition → telltale turns OFF
3. **Boundary**: test at exact threshold (e.g., fuel = 10.0L) and just above/below
4. **Priority**: when 2 warnings compete for same area, higher priority displays
5. **CAN timeout**: if CAN message stops → telltale must go to fail-safe state (usually ON for safety telltales)
6. **DTC correlation**: if MIL is ON, verify DTC is stored with correct status"

### Q24: How do you test cluster boot time?
**Answer:**
"I measure the time from ignition ON (KL15 signal) to cluster fully operational (gauge sweep complete, all telltales visible).

Method:
1. Send KL15 ON via CAN on the HIL bench
2. Monitor cluster NM (Network Management) message — first NM frame = ECU awake
3. Monitor gauge sweep animation — last gauge reaches max position = sweep done
4. Acceptance: boot ≤ 4 seconds for typical cluster, ≤ 8s for graphic-heavy TFT cluster"

---

## Section 7: Testing Process & V-Model

### Q25: Explain the V-Model in automotive testing.
**Answer:**
"The V-Model maps development phases on the left side to corresponding test phases on the right:
- **Requirements** → System Testing (validates full system against requirements)
- **System Design** → Integration Testing (validates ECU interaction)
- **Component Design** → Component/Unit Testing (validates individual functions)

Left side = planning/design. Right side = verification/validation.

As a validation engineer, I work primarily at the System Testing and Integration Testing levels — validating ECU behavior against requirements defined in DOORS."

### Q26: What is the difference between verification and validation?
**Answer:**
"Verification: Are we building the product RIGHT? (Does the implementation match the specification?)
Validation: Are we building the RIGHT product? (Does the product meet the user's actual needs?)

Example: Verification checks that ACC decelerates at exactly 3.5 m/s² as documented in the spec. Validation checks whether the passenger feels comfortable with that deceleration rate in real driving."

### Q27: How do you write test cases from requirements?
**Answer:**
"My process:
1. Read the requirement in DOORS (e.g., 'Low fuel warning shall activate when fuel level ≤ 10L')
2. Derive test cases:
   - **Positive**: Set fuel to 9L → verify telltale ON
   - **Boundary**: Set fuel to exactly 10.0L → verify ON; 10.1L → verify OFF
   - **Negative**: Invalid CAN signal value (0xFFFF) → verify fail-safe
   - **Timeout**: Stop CAN message → verify default behavior
3. Link each test case back to the requirement in DOORS (bidirectional traceability)
4. Add preconditions, expected results, and pass/fail criteria"

### Q28: What types of testing have you performed?
**Answer:**
"Functional, non-functional, regression, smoke, sanity, and HIL testing:
- **Functional**: Feature works as per specification (e.g., ACC follows target)
- **Non-functional**: Performance (boot time, response latency), endurance (24-hour soak)
- **Regression**: Re-run existing tests after code change to ensure no new bugs
- **Smoke**: Quick 10–15 critical checks after new build to confirm it's testable
- **Sanity**: Targeted checks on the specific area that was modified
- **HIL**: Hardware-in-the-Loop — ECU connected to dSPACE, simulating real vehicle conditions"

---

## Section 8: CAPL & Automation

### Q29: What is CAPL? How have you used it?
**Answer:**
"CAPL — Communication Access Programming Language — is CANoe's scripting language for CAN bus simulation and automation. It's event-driven.

I've used CAPL to:
1. Simulate CAN signals (vehicle speed, gear position, sensor data)
2. Inject faults (bus-off, signal timeout, invalid values)
3. Monitor and validate CAN responses automatically
4. Automate UDS diagnostic sequences (DTC read/clear/freeze frame)
5. Generate pass/fail reports

At BYD, my CAPL scripts automated 120 out of 200 regression test cases, reducing execution time by 35%."

### Q30: Explain CAPL event handlers you've used.
**Answer:**
"Key event handlers:
- `on start` / `on stop`: initialize/cleanup when measurement starts/stops
- `on message [ID]`: triggered when a specific CAN message is received
- `on timer [timerName]`: triggered when a timer expires — used for periodic checks
- `on key [char]`: triggered on keyboard input — used for manual test triggers
- `on signal [signalName]`: triggered when a specific signal value changes
- `on diagResponse`: triggered when UDS response is received
- `on envVar [name]`: triggered when a panel environment variable changes"

---

## Quick Revision: Top 10 Questions You WILL Be Asked

| # | Question | Preparation File |
|---|----------|-----------------|
| 1 | Tell me about yourself | 01_self_introduction.md (1-min version) |
| 2 | Explain CAN frame structure | Q1 above |
| 3 | What UDS services have you used? | Q7 above |
| 4 | Tell me about a challenging bug you found | 02_project_walkthroughs.md (Story 1A or 3A) |
| 5 | How do you write test cases? | Q27 above |
| 6 | What is DTC? Explain status byte | Q9 above |
| 7 | What ADAS features have you tested? | Q13 above |
| 8 | Describe your automation experience | Story 1B + Q29 |
| 9 | Why did you have a career break? | 05_career_break_explanation.md |
| 10 | Why should we hire you? | 06_behavioral_qa.md |
