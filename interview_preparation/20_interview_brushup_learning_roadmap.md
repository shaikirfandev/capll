# Interview Brush-Up Learning Roadmap
## Automotive ECU Test Engineer — Complete Skill Refresh Guide

> **How to use this document:** You are already in interviews. This is not a beginner guide — it is a targeted brush-up plan. Each section tells you what to review, what depth is needed for interviews, what questions you will be asked, and which files in this repo contain the material.

---

## Phase 0 — Mindset Before You Open Any Book

**The most common mistake candidates make:** Trying to re-learn everything from scratch instead of refreshing what they already know.

**What interviewers actually test:**
1. Can you explain what you did clearly with STAR structure?
2. Do you know the why behind your tools and decisions?
3. Can you debug a problem live under pressure?
4. Do you understand the protocols you claim to have worked with?

**Time budget if you have 1 week:**
- Day 1–2: Your own project experience (STAR stories) + protocols you used
- Day 2–3: Tools (CANoe, CANalyzer, CAPL, Python-CAN, UDS)
- Day 3–4: Domain knowledge (ADAS / Cluster / Infotainment / Telematics)
- Day 4–5: Live coding practice (CAPL + Python)
- Day 5–6: Behavioral + salary + questions to ask
- Day 7: Mock full interview (time yourself)

**Time budget if you have 2 weeks:**
- Add: ISO standards depth (26262, 14229, 15765)
- Add: AUTOSAR basics, ASPICE awareness
- Add: CI/CD, HIL bench architecture
- Add: One extra domain (BMS or Powertrain)

---

## Phase 1 — Your Own CV and Project Stories (Day 1, 2 hours)

**This is the highest ROI activity. Do it first.**

### What to prepare
For EVERY project on your CV, write down:
```
Project:         ___________________________
Duration:        ___________________________
Vehicle/ECU:     ___________________________
Bus protocol:    CAN / CAN FD / LIN / Ethernet
Tools used:      CANoe / CAPL / Python / HIL / UDS
My specific role: ___________________________
Biggest problem I solved: __________________
Result/metric:   ___________________________
```

### Self-introduction (2 minutes — memorise this)
Structure:
```
"I have X years of experience in automotive ECU testing, focused on [domain].
I've worked on [specific ECU/system] at [company/project type].
My core expertise is [CAN/CAPL/UDS/ADAS/etc].
Most recently I [specific achievement].
I'm looking for [specific next step]."
```

→ File: `interview_preparation/01_self_introduction.md`
→ File: `interview_preparation/02_project_walkthroughs.md`

---

## Phase 2 — CAN Protocol (Day 1, 2 hours)

### What interviewers ask — ranked by frequency

**Level 1 (Asked in every interview):**
- What is CAN? How does arbitration work?
- What is the difference between CAN and CAN FD?
- What are CAN error frames? What are the 5 error types?
- What is TEC and REC? What is Bus Off?
- What is a DLC? What does it mean?
- What is the difference between 11-bit and 29-bit CAN ID?

**Level 2 (Asked in technical rounds):**
- What is bit stuffing? When does a stuff error occur?
- How does CAN FD switch bit rates? What are BRS and FDF bits?
- What is CAN TP (ISO 15765-2)? What are SF, FF, CF, FC?
- Why can you NOT use CAN TP for real-time signals?
- What is STmin? What is BlockSize in Flow Control?

**Level 3 (Asked for senior roles):**
- How do you detect intermittent CAN faults on a live bus?
- What is E2E protection? AUTOSAR E2E Profile 2 vs Profile 4?
- How do you calculate bus load? What is the maximum safe bus load?

### Key numbers to remember
```
CAN max data payload:      8 bytes
CAN FD max data payload:   64 bytes
CAN TP max PDU:            4095 bytes (classical), 4095+ (CAN FD extended)
Classical CAN max bit rate: 1 Mbit/s
CAN FD data phase max:     8 Mbit/s
CAN error active TEC/REC:  < 128
CAN error passive TEC/REC: 128–255
CAN bus off TEC:           > 255
Bit stuffing rule:         After 5 identical bits, insert 1 opposite bit
```

→ File: `protocol_study_material/CAN_Arbitration_and_Error_Handling.md`
→ File: `protocol_study_material/CAN_CANFD_CANTP_When_To_Use_STAR.md`
→ File: `protocol_study_material/CAN_FD_Study_Material.md`
→ File: `protocol_study_material/ISO15765_CAN_TP.md`

---

## Phase 3 — UDS Diagnostics (Day 1, 2 hours)

**UDS questions appear in 95% of automotive test engineer interviews.**

### What interviewers ask

**Always asked:**
- What is UDS? What standard?
- What is the difference between OBD and UDS?
- What is DiagnosticSessionControl (0x10)? What sessions exist?
- What is ECUReset (0x11)? Types of reset?
- What is ReadDataByIdentifier (0x22)? How do you find DID values?
- What is a NRC? Give examples of NRC codes.
- What is SecurityAccess (0x27)? How does seed-key work?

**Technical depth:**
- Walk me through a complete UDS sequence to read software version.
- How does ECU flashing work step by step? (0x10→0x27→0x34→0x36→0x37)
- What is TESTER_PRESENT (0x3E)? Why is it needed?
- What is the difference between physical and functional addressing?
- Explain ReadDTCInformation (0x19) subfunction 0x02 vs 0x0F.

### UDS Flash Sequence — memorise this
```
1. 0x10 03  → ExtendedDiagnosticSession
2. 0x27 01  → SecurityAccess requestSeed
3. 0x27 02  → SecurityAccess sendKey (calculated key)
4. 0x34 00 44 [address] [size] → RequestDownload
5. 0x36 01 [block data]  → TransferData (repeat for each block)
6. 0x37     → RequestTransferExit
7. 0x31 01 FF 01 → Routine: checksum verification
8. 0x11 01  → ECUReset hardReset
```

### NRC Codes — must know
```
0x10 - generalReject
0x11 - serviceNotSupported
0x12 - subFunctionNotSupported
0x13 - incorrectMessageLengthOrInvalidFormat
0x22 - conditionsNotCorrect
0x24 - requestSequenceError
0x25 - noResponseFromSubnetComponent
0x31 - requestOutOfRange
0x33 - securityAccessDenied
0x35 - invalidKey
0x36 - exceededNumberOfAttempts
0x37 - requiredTimeDelayNotExpired
0x7E - subFunctionNotSupportedInActiveSession
0x7F - serviceNotSupportedInActiveSession
```

→ File: `uds_diagnostics/01_uds_complete_guide.md`
→ File: `interview_preparation/11_eol_uds_diagnostics_guide.md`
→ File: `obd2_diagnostics/OBD_Complete_Learning_Guide_STAR.md`

---

## Phase 4 — CAPL Scripting (Day 2, 3 hours)

**Every CANoe role tests CAPL. Live coding is common.**

### What interviewers test

**Written on whiteboard / shared screen:**
- Write a CAPL script to send a CAN message every 100ms
- Write a CAPL script to receive a message and validate a byte value
- Write an on message handler that checks if speed > 120 km/h and logs a warning
- Write a timer that counts down 5 seconds then sends a command
- Write a function that decodes a uint16 from two bytes

### Core CAPL constructs — review these
```capl
// Message send
message 0x100 speedMsg;
on start {
  speedMsg.byte(0) = 0x01;
  speedMsg.byte(1) = 0xF4;  // 500 = 50.0 km/h
  output(speedMsg);
}

// Timer
msTimer myTimer;
on timer myTimer {
  output(speedMsg);
  setTimer(myTimer, 100);
}

// Receive and validate
on message 0x200 {
  int status = this.byte(0);
  if (status == 0x02) {
    write("AEB Triggered");
  }
}

// Variables
variables {
  msTimer stepTimer;
  int testStep = 0;
  int passCount = 0;
  int failCount = 0;
}

// Check function pattern
void check(char name[], int condition) {
  if (condition) { write("[PASS] %s", name); passCount++; }
  else            { write("[FAIL] %s", name); failCount++; }
}
```

### Events you must know
```
on start            - measurement starts
on stopMeasurement  - measurement ends
on message 0xXXX    - CAN message received
on timer myTimer    - timer fires
on key 'a'          - keyboard key pressed
on errorFrame       - CAN error frame received
on busOff           - bus off detected
on envVar myVar     - environment variable changes
```

→ File: `interview_preparation/12_capl_live_coding.md`
→ File: `interview_preparation/15_capl_advanced_interview.md`
→ File: `CAPL_Language_Overview.md`
→ Files: `capl_scripts/` (30 example scripts)

---

## Phase 5 — Python for Automotive Testing (Day 2, 2 hours)

### What interviewers ask
- How do you send a CAN message using Python?
- How do you decode a CAN message using a DBC file in Python?
- How do you write a pytest test for an ECU response?
- How do you log CAN data to CSV?
- How do you calculate a rolling average of signal values?

### Core patterns to repeat from memory

```python
import can
import cantools

# Send message
bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
msg = can.Message(arbitration_id=0x100, data=[0x00, 0xF4], is_extended_id=False)
bus.send(msg)

# Receive with timeout
response = bus.recv(timeout=2.0)
if response and response.arbitration_id == 0x250:
    result = response.data[1]

# Decode using DBC
db = cantools.database.load_file('powertrain.dbc')
message = db.get_message_by_name('VehicleSpeed')
decoded = message.decode(bytes([0x01, 0xF4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

# pytest structure
def test_aeb_trigger():
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
    msg = can.Message(arbitration_id=0x208, data=[0x00, 0x50, 0x05, 0x64])
    bus.send(msg)
    resp = bus.recv(timeout=2.0)
    assert resp is not None
    assert resp.data[0] == 0x02, "AEB should be Triggered"
    bus.shutdown()
```

→ File: `interview_preparation/16_python_automotive_interview.md`
→ Files: `python_suites/` (120 example scripts)

---

## Phase 6 — Domain Knowledge Review (Day 3, 3 hours)

### Pick your strongest domain first — then prepare a second one

#### A. ADAS (Most in-demand)
**Questions:**
- What is TTC (Time to Collision)? Formula?
- What is the difference between FCW and AEB?
- What sensors does a modern ADAS use? Radar vs camera vs LiDAR trade-offs?
- What is sensor fusion? Why can't you rely on a single sensor?
- How do you test AEB at a specific TTC threshold?
- What is NCAP? How does it relate to ADAS testing?
- What is the ADAS ECU network topology? Which signals on which bus?

**Key ADAS formulas:**
```
TTC = Distance / Relative_Velocity
Braking_Distance = v² / (2 × μ × g)      (μ = friction coefficient, g = 9.81)
FCW_Threshold typically: TTC < 2.5s
AEB_Threshold typically: TTC < 1.4s
```

→ File: `adas_scenario_questions/`  
→ File: `interview_preparation/17_adas_interview_deep_dive.md`

#### B. Instrument Cluster
**Questions:**
- How is vehicle speed encoded in a CAN message?
- What is the difference between the speedometer signal and GPS speed?
- How does the cluster self-test work on ignition ON?
- What is TPMS? How does the cluster display tyre pressure?
- How do you test the MIL lamp?

→ File: `uds_diagnostics/04_instrument_cluster_star_scenarios.md`  
→ File: `cluster_scenarios/`

#### C. Infotainment
- How does CarPlay/Android Auto work at the protocol level?
- What is the difference between CAN-sourced data and private bus data in IVI?
- How do you test audio latency?
- What is MOST bus? When is it used?

→ File: `uds_diagnostics/05_infotainment_star_scenarios.md`  
→ File: `interview_preparation/10_infotainment_scenario_questions.md`

#### D. Telematics (TCU)
- What is the role of the TCU in a connected car?
- How does remote door lock work end to end?
- What is eCall? What is the regulatory requirement?
- How does OTA firmware update flow from cloud to ECU?

→ File: `uds_diagnostics/03_telematics_star_scenarios.md`

---

## Phase 7 — Tools and Bench Knowledge (Day 3, 2 hours)

### CANoe / CANalyzer

**Must-know:**
- What is the difference between CANoe and CANalyzer?
- How do you set up a measurement with a DBC file?
- How do you write a CAPL test module in CANoe?
- What is a Simulation Node vs Real Node in CANoe?
- How do you inject a fault (e.g., bus off, dominant bit stuck)?
- What is CANoe's Statistics window used for?
- What is the purpose of the Trace window vs the Graphics window?

**Hands-on questions:**
- How do you filter messages in CANalyzer by ID?
- How do you trigger a recording on a specific signal value?
- How do you set up a symbol comment for a DBC signal?

→ File: `vector_tools/01_canoe_canalyzer_guide.md`

### DBC Files
- What is a DBC file? What does it contain?
- What is a signal's start bit, length, byte order?
- What is the difference between Intel and Motorola byte order?
- How do you calculate the physical value from a raw CAN value?
  ```
  Physical = Raw × Factor + Offset
  Example: Speed raw = 500, Factor = 0.1, Offset = 0 → Physical = 50.0 km/h
  ```

→ File: `dbc_arxml_files/powertrain_sample.dbc`

### HIL Testing
- What is a HIL bench? What replaces real sensors/actuators?
- What does a test automation framework do on a HIL bench?
- What is the difference between MIL, SIL, and HIL?
- How do you inject a sensor fault on a HIL bench?

→ File: `hil_testing/HIL_ADAS_ECU_Testing_Guide.md`  
→ File: `model_based_testing/01_mil_sil_hil_guide.md`

---

## Phase 8 — Standards Awareness (Day 4, 2 hours)

**You don't need to memorise page numbers. You need to know what each standard is, why it exists, and how it affected your work.**

### ISO 26262 — Functional Safety
```
What: Road vehicle functional safety standard
Scope: Hardware + Software safety for E/E systems
Key concept: ASIL (A/B/C/D) — D is most safety-critical
Key activities: HARA, FMEA, safety goals, safety requirements
Your angle: "Our FCW had ASIL-B requirement — we had E2E protection
            on CAN signals and DTC monitoring for sensor faults."
```

### ISO 14229 — UDS
```
What: Unified Diagnostic Services standard
Scope: Defines all diagnostic service IDs and procedures
Key concept: Service IDs, session control, security access, DTCs
Your angle: "I used UDS daily for reading DTCs, ECU flashing,
            and reading calibration data identifiers."
```

### ISO 15765-2 — CAN TP
```
What: CAN Transport Protocol for on-board diagnostics
Scope: Segmentation/reassembly for diagnostic messages > 8 bytes
Key concept: SF/FF/CF/FC frame types, flow control
Your angle: "CAN TP was the transport layer under all our UDS
            communication — I traced ISO-TP frames in CANalyzer."
```

### ISO 11898 — CAN
```
What: CAN bus physical and data link layer standard
Scope: Bit timing, frame format, error handling
Your angle: "Used for all ECU-to-ECU communication on the
            vehicle CAN network."
```

### AUTOSAR
```
What: Standardised software architecture for automotive ECUs
Key layers: MCAL → ECU Abstraction → Services → RTE → Application
Key modules: COM (signal routing), DCM (diagnostics), DEM (DTCs),
             NM (network management), OS (OSEK-based)
Your angle: "The ECU software was AUTOSAR-based. Our test signals
            mapped to COM layer PDUs, and DTCs were managed by DEM."
```

### ASPICE
```
What: Automotive SPICE — process maturity model
Levels: 0 (incomplete) to 5 (optimising)
Key processes: SWE.1 (requirements) SWE.4 (unit test) SWE.6 (qualification)
Your angle: "Our project followed ASPICE Level 2 processes —
            requirements traceability, review records, test reports."
```

→ Files: `functional_safety/`, `autosar_basics/`, `cybersecurity_automotive/`

---

## Phase 9 — Behavioral Questions (Day 4, 1 hour)

**Prepare 6 STAR stories. One story can answer multiple questions.**

### The 6 most common behavioral questions in automotive interviews

1. **Tell me about a difficult bug you found and how you resolved it.**
   - Use a real CAN/UDS/ADAS bug story
   - Show: systematic approach, tool use, root cause analysis, resolution

2. **Tell me about a time you had to work under pressure or tight deadlines.**
   - Integration testing crunch / release deadline / blocking hardware issue

3. **Tell me about a time you disagreed with a colleague or requirement.**
   - Technical disagreement resolved professionally
   - Show: evidence-based approach, outcome-focused

4. **Give an example of a process you improved.**
   - Automated a manual test / introduced CAPL test module / reduced regression time

5. **Tell me about a time you worked with cross-functional teams.**
   - Working with hardware engineers, software developers, calibration engineers

6. **What is your biggest weakness?**
   - Pick something real but not disqualifying
   - Always pair with what you are doing to improve it

→ File: `interview_preparation/06_behavioral_qa.md`  
→ File: `interview_preparation/05_career_break_explanation.md`

---

## Phase 10 — Live Debugging Simulation (Day 5, 2 hours)

**Many companies give a live debugging exercise. Practice this format:**

### Scenario type 1 — Read a CANalyzer trace and find the bug
Practice asking yourself:
- Which message IDs are missing?
- Is any message outside its normal cycle time?
- Is there an unexpected error frame?
- Does the data value make sense for the signal?

### Scenario type 2 — Write a CAPL test live
Practice writing:
```capl
variables {
  msTimer t;
  message 0x100 speedMsg;
  int pass = 0, fail = 0;
}
on start {
  speedMsg.byte(0) = 0x01;
  speedMsg.byte(1) = 0xF4;
  output(speedMsg);
  setTimer(t, 200);
}
on timer t {
  // advance test step
}
on message 0x250 {
  if (this.byte(1) == 0x01) { write("[PASS] ECU acknowledged"); pass++; }
  else                       { write("[FAIL] wrong response");  fail++; }
}
on stopMeasurement {
  write("Result: %d PASS, %d FAIL", pass, fail);
}
```

### Scenario type 3 — Python + CAN live
Practice writing `send_and_verify()`, `wait_for_response()`, `pytest` test functions from memory.

→ Files: `capl_suites/` (4 suites × 30 scripts = 120 examples)  
→ Files: `python_suites/` (4 suites × 30 scripts = 120 examples)

---

## Phase 11 — Salary and Offer (Day 5, 30 min)

**Never be the first to say a number.**

1. When asked: *"I'm flexible and want to base the number on the full package including benefits, bonus, and RSUs. What is the budgeted range for this role?"*
2. If forced: State a range where the bottom of your range is already acceptable to you.
3. Counter-offer: Always negotiate. First offer is rarely the best offer.
4. Consider: base salary, annual bonus %, pension contribution %, remote flexibility, car allowance, health insurance, training budget, holiday allowance.

→ File: `interview_preparation/07_salary_negotiation.md`

---

## Phase 12 — Questions to Ask the Interviewer (Day 5, 30 min)

**Always ask 3–4 questions. Candidates who ask nothing appear disinterested.**

Best questions for automotive ECU test roles:
```
1. "What does the current test framework look like — CANoe simulation,
    HIL bench, or both? How much of testing is automated vs manual?"

2. "What is the CAN network topology of the ECU I'd be working on?
    Classical CAN, CAN FD, or Ethernet?"

3. "How close does the team follow ASPICE? Are test reports generated
    automatically from the framework or written manually?"

4. "What does a typical release cycle look like — sprint length,
    regression cadence, release frequency?"

5. "What is the biggest technical challenge the test team is facing
    right now?"

6. "Is there a mentoring structure for engineers joining the team?"
```

→ File: `interview_preparation/08_questions_to_ask.md`

---

## Master Revision Checklist

Use this daily. Tick when you can explain the topic without notes.

### CAN Protocol
- [ ] How CAN arbitration works (wired-AND, CSMA/CA)
- [ ] 5 error types: Bit, Stuff, Form, ACK, CRC
- [ ] TEC/REC rules, Error Active/Passive/Bus Off
- [ ] CAN FD: BRS, FDF, ESI bits and DLC table
- [ ] CAN TP: SF/FF/CF/FC, flow control parameters
- [ ] When to use CAN vs CAN FD vs CAN TP

### UDS Diagnostics
- [ ] All major service IDs (0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x31, 0x34, 0x36, 0x37, 0x3E)
- [ ] All 3 sessions (default, programming, extended)
- [ ] NRC codes 0x10, 0x11, 0x13, 0x22, 0x24, 0x31, 0x33, 0x35, 0x7E, 0x7F
- [ ] Full ECU flash sequence (7 steps)
- [ ] Seed-key mechanism
- [ ] DTC status byte structure (confirmed, pending, test failed)

### CAPL
- [ ] All event handlers: on start, on message, on timer, on key, on errorFrame, on stopMeasurement
- [ ] message declaration and send with output()
- [ ] Timer: msTimer, setTimer(), cancelTimer()
- [ ] Writing a test step state machine
- [ ] Writing a check() function

### Python-CAN
- [ ] Creating a bus, sending, receiving with timeout
- [ ] Using cantools to decode from DBC
- [ ] Writing a pytest test function
- [ ] Handling bus shutdown cleanly

### Domain (pick 2)
- [ ] ADAS: FCW/AEB/ACC/LKA/BSD signal design and test criteria
- [ ] Cluster: speed encoding, warning bitmask, self-test sequence
- [ ] Infotainment: IVI power states, BT pairing, OTA flow
- [ ] Telematics: TCU online sequence, remote command ACK flow, eCall states

### Standards (awareness level)
- [ ] ISO 26262: what it is, ASIL levels, where it affects your testing
- [ ] ISO 14229: UDS service structure
- [ ] ISO 15765-2: CAN TP layer
- [ ] AUTOSAR: layer names, COM/DCM/DEM modules
- [ ] ASPICE: what it means, SWE process areas

---

## One-Page Quick Reference (Print/Study on commute)

```
CAN PAYLOAD:          8B (CAN) | 64B (CAN FD) | 4095B (CAN TP)
CAN BIT RATE:         1Mbit/s nominal | 8Mbit/s FD data
CAN FD BITS:          FDF (FD frame) | BRS (bit rate switch) | ESI (error state)
CAN ERROR STATES:     Active (TEC/REC<128) | Passive (128-255) | Bus Off (TEC>255)
STUFF RULE:           After 5 same bits → insert 1 opposite

UDS SESSIONS:         0x01 Default | 0x02 Programming | 0x03 Extended
UDS KEY SERVICES:     10(session) 11(reset) 14(clearDTC) 19(readDTC)
                      22(readDID) 27(secAccess) 2E(writeDID) 31(routine)
                      34(reqDownload) 36(transferData) 37(transferExit) 3E(testerPresent)
UDS NRC:              22=conditionsNotCorrect | 33=securityDenied | 35=invalidKey
                      7E=serviceNotInSession | 7F=serviceNotSupported

CAPL EVENTS:          on start | on message 0xXXX | on timer | on key
                      on errorFrame | on busOff | on stopMeasurement
CAPL SEND:            output(myMsg)
CAPL TIMER:           msTimer t; setTimer(t, 100); on timer t { }

PYTHON-CAN:           bus = can.interface.Bus(channel='...', bustype='pcan', bitrate=500000)
                      bus.send(can.Message(arbitration_id=0x100, data=[0x01,0xF4]))
                      msg = bus.recv(timeout=2.0)

ADAS TTC:             TTC = Distance / RelativeVelocity
                      FCW alert: TTC < 2.5s | AEB trigger: TTC < 1.4s

ISO 26262 ASIL:       A (lowest safety) → D (highest safety)
AUTOSAR LAYERS:       MCAL → ECU Abstraction → Services → RTE → Application
ASPICE LEVELS:        0(Incomplete) → 1(Performed) → 2(Managed) → 3(Established)
```

---

*File: interview_preparation/20_interview_brushup_learning_roadmap.md*
