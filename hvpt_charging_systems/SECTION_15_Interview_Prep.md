# SECTION 15 — INTERVIEW PREPARATION
## 200+ Q&A for EV Powertrain Systems Engineer Roles

---

## 15.1 SYSTEMS ENGINEERING QUESTIONS (Q1–Q40)

```
Q1: What is the V-Model in automotive development?
A: The V-Model is the standard systems engineering lifecycle:
   Left side = decomposition (System → Subsystem → Component design)
   Right side = integration and verification (Unit test → Integration → System test → Validation)
   Each level on the right verifies the corresponding level on the left.
   Used in ISO 26262, ASPICE, and OEM development processes.

────────────────────────────────────────────────────────────────

Q2: What is the difference between Verification and Validation?
A: Verification = "Did we build it right?" — checks against specifications
   ("Does the BMS send CAN at 10ms as specified?")
   Validation = "Did we build the right thing?" — checks against customer needs
   ("Does the vehicle actually charge correctly in real-world conditions?")

────────────────────────────────────────────────────────────────

Q3: What is an ICD (Interface Control Document) in EV context?
A: ICD defines all communication interfaces between ECUs.
   For EV powertrain:
   - CAN messages: ID, DLC, signal names, encoding, period
   - Signal definitions: scaling, offset, range, units
   - Timing requirements: max cycle time, timeout
   - Physical connections: connector, pin, wire gauge
   Example: VCU ↔ BMS ICD defines BMS_Status message (0x310, 10ms) and
   VCU_Command message (0x100, 10ms), with all signal details.

────────────────────────────────────────────────────────────────

Q4: What is RTM (Requirements Traceability Matrix)?
A: RTM maps:
   Customer requirements → System requirements → Component requirements → Test cases
   Shows:
   - Every requirement has at least one test case (100% coverage)
   - Every test case traces to a requirement (no orphan tests)
   In practice: matrix with rows = requirements, columns = test cases
   Used during release gate reviews to confirm completeness.

────────────────────────────────────────────────────────────────

Q5: What is ASPICE and why does it matter?
A: ASPICE (Automotive SPICE) is a process assessment model for automotive SW development.
   Level 0 = incomplete, Level 1 = performed, ..., Level 3 = established (OEM minimum)
   Covers: requirements management, software design, verification, supplier management.
   OEMs require suppliers to be ASPICE Level 2 or 3.
   You will do ASPICE audits and provide evidence (reviews, tests, documents) to achieve levels.

────────────────────────────────────────────────────────────────

Q6: What happens when BMS and VCU disagree on SoC?
A: BMS is the authoritative source for SoC. VCU receives it via CAN.
   If BMS SoC via CAN ≠ VCU internal calculation (if VCU has one):
   - VCU uses BMS value (BMS has direct cell voltage measurement)
   - VCU logs diagnostic information
   - If disagreement > threshold, DTC may be set
   In practice: only BMS calculates SoC; VCU uses it from CAN.

────────────────────────────────────────────────────────────────

Q7: What is ASIL decomposition?
A: When one ASIL-D function is split into two independent redundant parts,
   each part only needs to be ASIL-B (because independent dual ASIL-B = ASIL-D).
   Example: BMS contactor command (ASIL-D) split into:
   - Primary contactor driver (ASIL-B) + independent HW watchdog (ASIL-B)
   Requires: independence (no common cause failures), diversity.
   Documented in TSC (Technical Safety Concept).

────────────────────────────────────────────────────────────────

Q8: What is a Safety Goal?
A: A Safety Goal is the top-level safety objective derived from HARA (Hazard Analysis).
   Example: SG-01 — "The BMS shall open main contactors within 500ms of thermal runaway detection"
   Safety Goals are ASIL-qualified and must never be violated.
   From Safety Goals, Functional Safety Requirements are derived.
   Safety Goals are in the FSC (Functional Safety Concept) document.

────────────────────────────────────────────────────────────────

Q9: How do you handle a requirement that is ambiguous or missing?
A: Steps:
   1. Identify the gap: write it up in the RFI (Request For Information) log
   2. Raise in next requirements review meeting
   3. If blocking: TBD (To Be Determined) flag in JAMA/DOORS
   4. Work with systems engineer/customer to clarify
   5. Update requirement after agreement
   Never implement based on guesses — always get written agreement.

────────────────────────────────────────────────────────────────

Q10: What is the difference between a DBC file and an ARXML file?
A: DBC (Database CAN): Vector-specific text format defining CAN messages and signals.
   Simple, widely used, supported by all tools.
   
   ARXML: AUTOSAR XML format defining the entire software architecture.
   Includes CAN signals but also: composition, ports, runnables, OS configuration.
   More complex, used in AUTOSAR-compliant ECU development.
   
   In practice: DBC for CAN signal definition; ARXML for full system architecture.

────────────────────────────────────────────────────────────────

Q11: How do you validate that CAN signal encoding is correct?
A: 1. Read raw CAN data in hex from CANoe trace
   2. Apply DBC formula: physical = raw × scale + offset
   3. Compare to expected physical value
   4. Cross-check with independent measurement (multimeter, reference sensor)
   Example: BMS_SoC raw = 0xAC = 172, scale = 0.5, offset = 0
   Physical = 172 × 0.5 = 86.0% SoC
   Confirm with charging equipment display showing 86% SoC

────────────────────────────────────────────────────────────────

Q12: What are EARS requirement patterns?
A: EARS (Easy Approach to Requirements Syntax) provides template sentences:
   - Ubiquitous: "The [system] shall [do something]"
   - Event-driven: "When [event], the [system] shall [do something]"
   - Optional: "Where [feature], the [system] shall [do something]"
   - Unwanted behavior: "If [condition], the [system] shall [respond]"
   Example: "When BMS_CellTemp > 80°C, the BMS shall open main contactors within 500ms."
   Makes requirements unambiguous and testable.

────────────────────────────────────────────────────────────────

Q13: What is a safe state in automotive safety context?
A: A safe state is a system state where risk is tolerable even after a safety-relevant fault.
   For BMS: safe state = contactors open, HV bus de-energized, vehicle propulsion disabled.
   Safe state must be:
   - Achievable from any fault condition
   - Maintained until system is inspected/repaired
   - Not causing additional hazards
   Safe states are defined in the FSC and verified in FMEA/FTA.

────────────────────────────────────────────────────────────────

Q14: What documentation do you maintain as a systems engineer?
A: Key documents:
   - ICD (Interface Control Document) — all ECU interfaces
   - SysRS (System Requirements Specification)
   - HARA (Hazard Analysis and Risk Assessment) — safety
   - FSC (Functional Safety Concept)
   - TSC (Technical Safety Concept)
   - RTM (Requirements Traceability Matrix)
   - System Test Plan + Test Report
   - Release notes

────────────────────────────────────────────────────────────────

Q15: How do you manage a DBC file in a team?
A: DBC files must be version-controlled (Git or equivalent).
   Change process:
   1. Engineer requests change via JIRA/ECR (Engineering Change Request)
   2. Systems engineer reviews impact on all receivers
   3. Change approved by all affected teams
   4. DBC updated, version number incremented
   5. All tools (CANoe, Python, embedded SW) updated with new DBC
   6. Integration test to confirm no regression
   Never change DBC without impact analysis — it breaks all CAN decoders.
```

---

## 15.2 CAN PROTOCOL & CANoe QUESTIONS (Q41–Q80)

```
Q41: What is CAN bus arbitration?
A: Non-destructive bit-wise arbitration (CSMA/CR — Carrier Sense Multiple Access
   with Collision Resolution):
   1. Multiple nodes start transmitting simultaneously
   2. Each node monitors the bus while transmitting
   3. When a node transmits recessive (1) but detects dominant (0): it loses arbitration
   4. Winner = node with lowest CAN ID (most dominant bits at start)
   5. Loser stops and retries after current frame
   Result: highest priority message always wins. No information lost.
   This is why lower CAN ID = higher priority.

────────────────────────────────────────────────────────────────

Q42: What are the 5 CAN error types?
A: 1. Bit Error — transmitted bit ≠ monitored bit
   2. Stuff Error — more than 5 consecutive identical bits without stuffing
   3. CRC Error — received CRC ≠ calculated CRC
   4. Form Error — fixed-form field has wrong bit value (EOF, IFS)
   5. Acknowledgment Error — no ACK from any receiver
   Each increments TEC (Transmit) or REC (Receive) error counter.
   TEC/REC > 127 = Error Passive, TEC > 255 = Bus Off.

────────────────────────────────────────────────────────────────

Q43: What is the difference between CAN and CAN FD?
A: CAN (ISO 11898-1 classic):
   - Max payload: 8 bytes
   - Max speed: 1 Mbit/s
   
   CAN FD (ISO 11898-1:2015):
   - Max payload: 64 bytes
   - Nominal speed: 1 Mbit/s (arbitration phase)
   - Data phase speed: up to 8 Mbit/s (with BRS bit set)
   - BRS (Bit Rate Switch): signal to switch to higher speed
   - ESI (Error Status Indicator): passive/active status
   CAN FD nodes on same bus as classic nodes? Only if no BRS frames are sent.

────────────────────────────────────────────────────────────────

Q44: What is ISO-TP and why is it needed?
A: ISO-TP (ISO 15765-2) is a transport protocol on top of CAN.
   Reason: CAN frames hold max 8 bytes, but UDS messages can be larger (e.g., VIN=17 bytes).
   ISO-TP handles segmentation/reassembly:
   - Single Frame (SF): ≤ 7 bytes
   - First Frame (FF) + Consecutive Frames (CF): > 7 bytes
   - Flow Control (FC): receiver controls sending pace
   Every UDS diagnostic message uses ISO-TP.

────────────────────────────────────────────────────────────────

Q45: How do you debug a missing CAN message?
A: Step-by-step:
   1. Check if ECU is powered on (12V supply, CAN transceiver Vcc)
   2. Check if ECU is in correct state (some messages only in ACTIVE mode)
   3. Measure CAN bus voltage: should be 2.5V idle, 3.5V/1.5V during frame
   4. Check termination: measure 60Ω across CAN_H/CAN_L (2×120Ω in parallel)
   5. In CANoe: check "Unknown Frame" — ECU may be using different CAN ID
   6. Check DBC version: old DBC may have wrong ID for updated ECU
   7. Check bus load: if >80%, messages may be delayed
   8. Review ECU software: is message send enabled in current power mode?

────────────────────────────────────────────────────────────────

Q46: What is restbus simulation in CANoe?
A: Restbus simulation = simulating ECUs that are NOT physically connected to the test bench.
   Instead of real BMS: CANoe runs a CAPL simulation node that sends BMS_Status, BMS_Limits, etc.
   This allows testing one ECU (e.g., VCU) in isolation without needing all other ECUs.
   Configuration: in CANoe network designer, add simulation node, assign messages from DBC.
   Critical for early integration testing before all hardware is available.

────────────────────────────────────────────────────────────────

Q47: What is the significance of byte order (endianness) in CAN signals?
A: CAN signals can be encoded in two byte orders:
   Intel (Little-Endian): LSB first. Signal starts at LSB position in first byte.
   Motorola (Big-Endian): MSB first. Signal starts at MSB position in first byte.
   
   Wrong byte order = completely wrong decoded value.
   Example: 2-byte value 0x0310 in Intel = 0x1003 in Motorola
   
   Always check DBC signal byte order when integrating a new ECU.
   Debug: compare raw bytes in trace to expected physical value manually.

────────────────────────────────────────────────────────────────

Q48: How do you set up a filter in CANoe trace window?
A: Right-click trace window → Filter settings → Add filter:
   By message name (if DBC loaded): e.g., "BMS_*" for all BMS messages
   By CAN ID range: e.g., 0x310-0x320
   By time window: show only events between T=0s and T=10s
   By error frames: show only error frames
   Also: highlight specific messages with colors for easier analysis.
   Tip: use "Inverse filter" to show everything EXCEPT a specific message.

────────────────────────────────────────────────────────────────

Q49: What is CAPL used for in testing?
A: CAPL (Communication Access Programming Language) is Vector's event-driven scripting language for CANoe/CANalyzer.
   Key uses:
   - ECU simulation (restbus nodes)
   - Test automation (sending stimuli, checking responses)
   - Signal monitoring with alarms
   - Fault injection
   - Test reports generation
   - Custom panels and HMI
   CAPL integrates directly with CANoe simulation environment.

────────────────────────────────────────────────────────────────

Q50: What is the maximum CANoe test report you have generated?
A: Good answer for an interview:
   "I automated a complete BMS validation suite of 47 test cases in CAPL.
   The test module ran overnight on our HIL setup. CANoe generated an HTML report
   with pass/fail per test case, timing graphs, and CAN trace snippets for failures.
   The report was automatically emailed to the team each morning and linked to JIRA."
   
   Mention: CAPL test module, TC_Main, testResult(), write() for report details.
```

---

## 15.3 CAPL PROGRAMMING QUESTIONS (Q81–Q110)

```
Q81: What is an on message event in CAPL?
A: Event handler triggered when a specific CAN message is received.
   Syntax:
     on message 0x310 { ... }          // by ID
     on message BMS_Status { ... }     // by name (requires DBC)
     on message * { ... }              // any message
   The 'this' keyword inside provides access to the received frame.
   Example: float soc = this.BMS_SoC * 0.5; // decode with scale

────────────────────────────────────────────────────────────────

Q82: How do you implement a watchdog timer in CAPL?
A: Using msTimer with on timer reset pattern:
   variables { msTimer tmrWatchdog; int msgReceived = 0; }
   
   on message BMS_Status { msgReceived = 1; setTimer(tmrWatchdog, 100); }
   
   on timer tmrWatchdog {
     if (!msgReceived) {
       write("BMS timeout detected!");
       setTimer(tmrWatchdog, 100);  // Keep monitoring
     }
     msgReceived = 0;  // Reset flag
   }
   
   on start { setTimer(tmrWatchdog, 100); }  // Start monitoring

────────────────────────────────────────────────────────────────

Q83: What is the difference between output() and putValue() in CAPL?
A: output(msg): Sends a complete CAN message (message object)
   putValue(signal, value): Sets a signal value and sends the message
   
   output() example:
     message VCU_Command cmd;
     cmd.VCU_HV_Enable = 1;
     output(cmd);
   
   putValue() example (simpler for signals):
     putValue(VCU_Command::VCU_HV_Enable, 1);  // Sends message automatically
   
   output() gives more control; putValue() is simpler for single signal changes.

────────────────────────────────────────────────────────────────

Q84: How do you read a signal value in CAPL?
A: Three ways:
   1. From received message:
      on message BMS_Status { float soc = this.BMS_SoC; }
      
   2. Imperative read (current value in simulation):
      float soc = getValue(BMS_Status::BMS_SoC);
      
   3. On signal change event:
      on signal BMS_Status::BMS_SoC { float soc = this.rawValue * 0.5; }

────────────────────────────────────────────────────────────────

Q85: How do you write a CAPL test case?
A: CAPL test cases use testcase keyword:
   
   testcase TC_BMS_SoC_Range() {
     float soc = getValue(BMS_Status::BMS_SoC);
     
     if (soc >= 0.0 && soc <= 100.0) {
       testStepPass("SoC range", "SoC=%.1f%% within [0-100%%]", soc);
     } else {
       testStepFail("SoC range", "SoC=%.1f%% OUTSIDE RANGE!", soc);
     }
   }
   
   void MainTest() {
     TC_BMS_SoC_Range();
   }

────────────────────────────────────────────────────────────────

Q86: What are global variables vs. environment variables in CAPL?
A: Global variables: CAPL variables, exist only within CAPL program.
   Can be shared between CAPL nodes via 'export' declaration.
   
   Environment variables (sysvar/envvar): CANoe-level variables.
   Created in environment → accessible from ALL CAPL nodes and panels.
   Used for: panel controls, inter-node communication, system state.
   
   Example: envvar EV_ChargeMode { int; 0 }
   Access: sysSetVariable(sysvar::EV_ChargeMode, 1);
   
   In Panels: button binds to environment variable → all CAPL nodes react.

────────────────────────────────────────────────────────────────

Q87: How do you implement fault injection in CAPL?
A: Example structure:
   void InjectFault(int faultType) {
     switch(faultType) {
       case FAULT_OV: {
         // Override BMS cell voltage signal
         message BMS_CellData faultMsg;
         faultMsg.BMS_MaxCellVoltage = 430; // 4.30V × 100 = 430 raw
         output(faultMsg);
         write("[FAULT] Overvoltage injected");
         break;
       }
       case FAULT_TIMEOUT: {
         // Stop sending BMS message
         cancelTimer(tmrBMSCycle);
         write("[FAULT] BMS timeout injected");
         break;
       }
     }
   }

────────────────────────────────────────────────────────────────

Q88: What is the difference between on preStart and on start in CAPL?
A: on preStart: called before simulation starts. Used for initialization.
   Variables can be set, but CAN messages cannot be sent (bus not active yet).
   
   on start: called when simulation starts. CAN bus is active.
   Timers can be started, messages can be sent.
   
   on stopMeasurement: called when simulation stops. Used for cleanup.
   
   Correct order: preStart → start → (simulation running) → stopMeasurement

────────────────────────────────────────────────────────────────

Q89: How do you access raw bytes of a CAN message in CAPL?
A: Using .byte(n) accessor:
   on message 0x310 {
     byte b0 = this.byte(0);  // First byte
     byte b1 = this.byte(1);  // Second byte
     // Manually decode multi-byte signal:
     word raw16 = (word)b0 | ((word)b1 << 8);  // Intel byte order
     float soc = raw16 * 0.5;
   }

────────────────────────────────────────────────────────────────

Q90: Can CAPL access UDS diagnostic services?
A: Yes, using DiagSendRequest() or DiagSetTarget():
   diag request BMS_ECU.DefaultSession {}
   DiagSendRequest(BMS_ECU.DefaultSession);
   
   Wait for response:
   on diagResponse BMS_ECU.DefaultSession {
     if (DiagGetLastResponseCode() == 0x50) {
       write("Default session entered");
     }
   }
   
   CAPL also has direct UDS service access via:
   DiagDoJob(BMS_ECU.ReadDataById_F190);  // Read VIN
```

---

## 15.4 PYTHON AUTOMATION QUESTIONS (Q111–Q140)

```
Q111: What is python-can and how do you use it?
A: python-can is a library for CAN bus communication in Python.
   Supports Vector, PCAN, Kvaser, SocketCAN interfaces.
   
   Basic usage:
     import can
     bus = can.interface.Bus('PCAN_USBBUS1', bustype='pcan', bitrate=500000)
     
     # Send
     msg = can.Message(arbitration_id=0x100, data=[0x01, 0x02])
     bus.send(msg)
     
     # Receive
     msg = bus.recv(timeout=1.0)
     print(f"ID={msg.arbitration_id:#x}, Data={msg.data.hex()}")

────────────────────────────────────────────────────────────────

Q112: How do you decode CAN signals with cantools?
A: cantools parses DBC files and decodes signals:
   
   import cantools
   db = cantools.database.load_file('EV_Powertrain.dbc')
   
   # Decode a received message
   msg_def = db.get_message_by_frame_id(0x310)
   decoded = msg_def.decode(bytes([0xAC, 0x01, 0x0C, 0x1A, 0x00, 0x00, 0x00, 0x00]))
   
   print(decoded)  # {'BMS_SoC': 86.0, 'BMS_PackVoltage': 391.2, ...}
   
   # Encode to send
   data = msg_def.encode({'BMS_SoC': 86.0, 'BMS_PackVoltage': 391.2})

────────────────────────────────────────────────────────────────

Q113: How do you implement thread-safe CAN reception in Python?
A: Use threading.Thread for background receive loop:
   
   import threading, can
   
   callbacks = {}
   
   def receive_loop(bus):
     while True:
       msg = bus.recv(timeout=0.1)
       if msg:
         for cb in callbacks.get(msg.arbitration_id, []):
           cb(msg)
   
   bus = can.interface.Bus(channel='can0', bustype='socketcan')
   thread = threading.Thread(target=receive_loop, args=(bus,), daemon=True)
   thread.start()
   
   # Register callback
   def on_bms(msg): print(f"BMS: {msg.data.hex()}")
   callbacks[0x310] = [on_bms]
   
   Thread is daemon=True so it stops when main thread exits.

────────────────────────────────────────────────────────────────

Q114: How do you perform UDS diagnostics in Python?
A: Using udsoncan library:
   
   import udsoncan, isotp, can
   
   bus = can.interface.Bus('PCAN_USBBUS1', bustype='pcan')
   addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x741, rxid=0x749)
   conn = udsoncan.connections.PythonIsoTpConnection(bus, addr)
   conn.open()
   
   with udsoncan.client.Client(conn) as client:
     client.change_session(0x03)  # Extended
     response = client.read_data_by_identifier(0xF190)
     vin = bytes(response.service_data.values[0xF190])
     print(f"VIN: {vin.decode()}")

────────────────────────────────────────────────────────────────

Q115: How do you structure automotive test scripts in pytest?
A: Structure:
   1. conftest.py: fixtures (CAN bus, UDS client, config loading)
   2. tests/ directory organized by ECU or system
   3. Parametrize for testing multiple ECUs/signals with one test function
   4. Fixtures with scope='module' for expensive setups (CAN connections)
   5. --html=report.html for automated HTML reports
   
   Example fixture:
   @pytest.fixture(scope='module')
   def can_bus():
     bus = CANInterface(channel='PCAN_USBBUS1', ...)
     bus.connect()
     yield bus
     bus.disconnect()

────────────────────────────────────────────────────────────────

Q116: How do you analyze CANoe .blf log files in Python?
A: Using cantools or python-can log reader:
   
   import can
   
   with can.LogReader('test_log.blf') as log:
     for msg in log:
       print(f"T={msg.timestamp:.3f} ID={msg.arbitration_id:#x}")
       # Decode with cantools
       decoded = db.decode_message(msg.arbitration_id, msg.data)
```

---

## 15.5 UDS DIAGNOSTICS QUESTIONS (Q141–Q170)

```
Q141: What is UDS and what standard defines it?
A: UDS = Unified Diagnostic Services, defined by ISO 14229.
   It is the standard automotive diagnostic protocol for:
   - Reading fault codes (DTCs)
   - Reading/writing ECU parameters (DIDs)
   - ECU programming (flashing)
   - Security access (seed/key)
   - Routine control
   Used across all OEMs and all ECUs in modern vehicles.
   Transport: ISO-TP over CAN (ISO 15765-2), or DoIP over Ethernet (ISO 13400).

────────────────────────────────────────────────────────────────

Q142: What is the format of a UDS request?
A: Request: [SID] [optional sub-function] [optional data]
   Response (positive): [SID + 0x40] [optional sub-function] [data]
   Response (negative): [0x7F] [SID] [NRC]
   
   Example:
   Request:  22 F1 90  (ReadDataByIdentifier, DID=0xF190)
   Positive: 62 F1 90  [17 bytes VIN]  (0x22 + 0x40 = 0x62)
   Negative: 7F 22 31  (NRC 0x31 = requestOutOfRange — DID not supported)

────────────────────────────────────────────────────────────────

Q143: What is Security Access and when is it required?
A: Security Access (SID 0x27) unlocks sensitive operations:
   - Writing calibration data (0x2E)
   - Flashing ECU firmware (0x34-0x37)
   - Controlling I/O (0x2F)
   
   Flow: RequestSeed (27 01) → receive seed → calculate key → SendKey (27 02)
   If key correct: 67 02 positive response = access granted
   If wrong key: 7F 27 35 (NRC 0x35 = invalid key)
   Required before programming session for safety.

────────────────────────────────────────────────────────────────

Q144: What does NRC 0x22 mean?
A: NRC 0x22 = conditionsNotCorrect
   Service requested in wrong state/session.
   Example: trying to write a DID (0x2E) in Default session → 7F 2E 22
   Fix: enter Extended session first (10 03), then retry the service.
   
   Most common NRCs:
   0x11 = serviceNotSupported (ECU doesn't implement this service)
   0x12 = subFunctionNotSupported
   0x22 = conditionsNotCorrect (wrong session/state)
   0x31 = requestOutOfRange (DID/address not valid)
   0x33 = securityAccessDenied (need security unlock first)
   0x78 = responsePending (still processing, wait)

────────────────────────────────────────────────────────────────

Q145: How do you read all DTCs from an ECU?
A: Service: 19 02 FF (ReadDTCInformation, reportDTCByStatusMask = 0xFF = all)
   Request: 19 02 FF
   Response: 59 02 [statusAvailabilityMask]
             [DTC3][DTC2][DTC1][StatusByte]  (each DTC = 4 bytes)
             ... repeat for each DTC ...
   
   Parse DTC: 3 bytes = DTC code, 1 byte = status
   Status bit 3 = confirmedDTC (persistent fault)
   Status bit 0 = testFailed (currently active fault)
   
   In Python: udsoncan.client.get_dtc_by_status_mask(0xFF)

────────────────────────────────────────────────────────────────

Q146: What is the difference between pending and confirmed DTC?
A: Pending DTC: fault detected in current drive cycle (bit 2 of status)
   Confirmed DTC: fault detected in multiple consecutive drive cycles (bit 3)
   
   Confirmation logic (OEM-specific, typically):
   - Fault present in 2 of 3 consecutive drive cycles → confirmed
   
   Why separate? Pending avoids false DTCs from transient issues.
   Workshop diagnosis: focus on confirmed DTCs.
   Field analysis: look at pending + confirmed for early warning.

────────────────────────────────────────────────────────────────

Q147: What is the TesterPresent service and why is it used?
A: SID 0x3E — TesterPresent keeps the diagnostic session alive.
   ECU has S3 timer (typically 5 seconds): if no communication received,
   ECU returns to Default session.
   
   TesterPresent (3E 00) resets S3 timer → maintains Extended/Programming session.
   
   Common usage:
   3E 80 = suppressPositiveResponse bit set (ECU doesn't respond, saves bus time)
   3E 00 = requires positive response (67 3E)
   
   In Python: client.tester_present() every 4 seconds to maintain session.
```

---

## 15.6 EV CHARGING & POWERTRAIN QUESTIONS (Q171–Q200)

```
Q171: What is the difference between OBC and DCDC in EV?
A: OBC (Onboard Charger): Converts AC grid power to DC for battery charging.
   DCDC Converter: Steps down HV DC (400V) to LV DC (13.5V) for 12V systems.
   
   OBC: AC inlet → PFC + Isolation transformer + rectifier → battery
   DCDC: HV bus → step-down converter → 12V bus (lights, sensors, ECUs)
   
   Both are galvanically isolated from HV to LV.

────────────────────────────────────────────────────────────────

Q172: What is the precharge sequence in a BMS?
A: Before connecting battery to DC link:
   1. Main negative contactor closes first (reference ground)
   2. Precharge contactor closes (in series with 100Ω precharge resistor)
   3. Current flows through resistor to charge DC link capacitors
   4. Wait until V_dclink ≥ 95% of V_battery (RC charging)
   5. Main positive contactor closes (now minimal inrush current)
   6. Precharge contactor opens
   
   Without precharge: closing main positive directly would cause
   massive inrush current (C_link × dV/dt = surge) → weld contactors.

────────────────────────────────────────────────────────────────

Q173: What is SoC and how is it calculated?
A: State of Charge = remaining capacity / total capacity × 100%
   
   Methods:
   1. Coulomb Counting: SoC = SoC_initial - ∫(I × dt) / Capacity
      + Simple, accurate for short periods
      - Cumulative error (drift over time)
   
   2. OCV (Open Circuit Voltage) lookup: map cell voltage to SoC
      + No drift
      - Only accurate at rest (not under load)
   
   3. Kalman Filter: combines Coulomb counting + model prediction + OCV correction
      + Most accurate for production BMS
      - Complex to implement

────────────────────────────────────────────────────────────────

Q174: What is the J1772 pilot signal?
A: J1772 Control Pilot (CP) = PWM signal on pin 3 of the J1772 connector.
   Generated by EVSE (charging station).
   Purpose: communicate between EVSE and vehicle.
   
   Signal properties:
   - Frequency: 1 kHz ± 5%
   - Voltage: ±12V (no load), ±9V (EV connected)
   - Duty cycle: encodes available current (per lookup table)
   
   Duty cycle table:
   16% = 10A, 25% = 16A, 50% = 32A, 80% = 48A, 96% = 80A
   Formula (6-51A): I = duty% × 0.6A

────────────────────────────────────────────────────────────────

Q175: What is CCS (Combined Charging System)?
A: CCS = DC fast charging standard combining J1772 (AC) and DC inlet in one connector.
   
   CCS Combo 1: J1772 (AC) + 2 DC pins (North America)
   CCS Combo 2: Type 2 (AC) + 2 DC pins (Europe, China emerging)
   
   Communication: ISO 15118-2 via PLC (HomePlug GreenPHY) on CP line
   Power: up to 350 kW with liquid-cooled cable
   
   Vehicle side: CCS inlet supports both AC Level 2 and DC fast charging.

────────────────────────────────────────────────────────────────

Q176: What is thermal runaway in a lithium battery?
A: Thermal runaway = self-accelerating, uncontrollable exothermic reaction.
   Trigger: overcharge, over-discharge, external short, physical damage.
   
   Progression:
   Stage 1: Separator breakdown (80–120°C)
   Stage 2: Electrolyte decomposition, gas generation (120–200°C)
   Stage 3: Cathode decomposition, oxygen release (200–300°C)
   Stage 4: Ignition, fire, propagation to adjacent cells
   
   Safety measures:
   - BMS: over-voltage, over-temperature protection
   - Thermal management: cooling, ventilation
   - Cell design: PTC (Positive Temperature Coefficient) fuse per cell
   - Pack design: fire barriers, thermal runaway propagation prevention
   - IMD: isolation monitoring

────────────────────────────────────────────────────────────────

Q177: What is regenerative braking?
A: Converting vehicle kinetic energy back to electrical energy during deceleration.
   Motor acts as generator: negative torque command → motor generates electricity.
   Electricity returned to HV battery (charging).
   
   BMS limits regen based on:
   - SoC (stop regen at 100% or near OV limit)
   - Temperature (reduce regen at low temp — battery can't absorb fast)
   - BMS_ChargePowerLimit signal
   
   If BMS allows 0W regen: friction brakes blend in automatically.
   Energy recovery efficiency: ~70-75% of kinetic energy recovered.

────────────────────────────────────────────────────────────────

Q178: What is FOC (Field Oriented Control) in an inverter?
A: FOC = Field Oriented Control = vector control of AC motor.
   
   Goal: independently control torque-producing current (Iq) and
         flux-producing current (Id) for optimal efficiency.
   
   Process:
   1. Measure 3-phase stator currents (ia, ib, ic)
   2. Transform to d-q rotating reference frame (Park transform)
   3. Control Id and Iq independently (two PI controllers)
   4. Inverse transform back to 3-phase duty cycles
   5. Apply to IGBT gate driver → PWM output
   
   Result: fast, efficient torque control with smooth operation.
   Used in all modern EV traction inverters.

────────────────────────────────────────────────────────────────

Q179: What is ASIL-D and what components in an EV require it?
A: ASIL-D = highest functional safety integrity level in ISO 26262.
   Requires: PMHF < 10 FIT, MC/DC code coverage, formal review, independent verification.
   
   ASIL-D items in EV powertrain:
   - HV isolation monitoring (IMD) — electric shock to occupant
   - Main contactor welding detection — unintended propulsion
   - Thermal runaway detection and response
   - Gate driver fault detection in inverter (IGBT desaturation)
   
   Not everything is ASIL-D: SoC display (ASIL-A), infotainment (QM).

────────────────────────────────────────────────────────────────

Q180: What experience do you have with HIL testing?
A: Strong answer:
   "I have set up and executed HIL test campaigns on [dSPACE/ETAS LABCAR].
   I configured the battery plant model to simulate cell voltages, temperatures,
   and current for BMS validation. I wrote CAPL test scripts to interface with
   the HIL for fault injection — for example, injecting cell overvoltage to
   validate BMS fault detection timing (ASIL-C requirement ≤ 100ms response).
   I also ran the ISO 15118 charging handshake test with a DCFC simulator
   model, validating the complete 15118 sequence within the 90-second budget."

────────────────────────────────────────────────────────────────

Q181: How do you validate that an isolation fault is detected correctly?
A: Steps:
   1. Vehicle in ACTIVE state (HV bus energized, contactors closed)
   2. Via HIL: inject isolation resistance drop to 30 kΩ (below threshold)
      or via laboratory: connect known resistance between HV+ and chassis ground
   3. Monitor IMD output signal (hardware signal to BMS)
   4. Monitor BMS_IsolationStatus on CAN
   5. Monitor DTC 0x0D0001 via UDS
   6. Measure response time from fault injection to contactors open
   
   Pass criteria:
   - Detection within 1 second
   - Contactors open within 100ms of detection
   - DTC confirmed
   - No HV on chassis after contactors open

────────────────────────────────────────────────────────────────

Q182: What would you do if a vehicle failed DC fast charging at a specific station?
A: Systematic approach:
   1. Check if issue is specific to that station or general
      → Try a different DCFC station
   2. Read DTCs with diagnostic tool
   3. Request CANoe/logger data from vehicle if available
   4. Analyze ISO 15118 sequence: which phase failed?
   5. If PLC issue: check PLC coupling circuit, CP signal quality
   6. If 15118 message issue: verify message content, check certificates
   7. If power issue: check DCFC station interoperability logs
   8. If power electronics issue: check OBC DTC, input/output voltages
   
   Reference Case Study 10 in this guide — PLC capacitor failure scenario.

────────────────────────────────────────────────────────────────

Q183: What is the role of the VCU in EV powertrain?
A: VCU (Vehicle Control Unit) is the central coordinator:
   - Reads accelerator/brake pedal position
   - Calculates torque request for inverter
   - Manages HV enable/disable sequence (commands BMS)
   - Controls charging (commands OBC)
   - Monitors all ECU health via CAN
   - Implements overall vehicle state machine
   - Generates top-level DTCs based on subsystem faults
   - Manages power modes (sleep/wake/active)
   
   VCU does NOT calculate SoC (BMS does) or control motor directly (inverter does).
   VCU is the "brain"; BMS/Inverter/OBC are the "muscles."

────────────────────────────────────────────────────────────────

Q184: Explain the ISO 15118 charging session in 60 seconds.
A: CCS DC fast charging communication:
   1. Vehicle plugs in
   2. HomePlug GreenPHY PLC pairing on CP line (SLAC)
   3. TCP/IP connection established between EV (EVCC) and station (SECC)
   4. SessionSetup: EV identifies itself by MAC address
   5. ServiceDiscovery: EV asks what services are available
   6. Authorization: EV proves identity (contract certificate or payment)
   7. ChargeParameterDiscovery: EV and station exchange max V/I/P
   8. CableCheck: station checks cable isolation (safety!)
   9. PreCharge: station ramps voltage to match battery voltage
   10. PowerDelivery: charging starts, EV sends CurrentDemandReq every 25ms
   11. Charging: EV controls current, station delivers
   12. SessionStop: EV done, contactors open, cable can be unplugged

────────────────────────────────────────────────────────────────

Q185: What ASIL level applies to the charging pilot signal (CP) function?
A: CP signal monitoring is typically ASIL-B because:
   Hazard: EVSE energizes AC without vehicle ready → shock risk
   S2 (life-threatening), E3 (medium probability), C2 (normally controllable)
   → ASIL B per ASIL determination table
   
   The CP state detection function (reading EVSE current limit from duty cycle)
   must be implemented with ASIL-B rigor:
   - Software validation
   - Plausibility check on CP duty cycle
   - Diagnostic coverage of CP measurement circuit

────────────────────────────────────────────────────────────────

Q186: What is the difference between SOC, SOH, and SOE?
A: SoC = State of Charge (remaining energy as percentage of current capacity)
   SoH = State of Health (current capacity vs. rated new capacity)
   SoE = State of Energy (actual energy available = SoC × SoH × Rated_Capacity)
   
   Example:
   New battery rated: 100 kWh at SoH=100%
   After 100k km: SoH = 80% (capacity degraded)
   Current SoC = 50%
   SoE = 50% × 80% × 100 kWh = 40 kWh available
   
   Range display should use SoE (actual) not just SoC.

────────────────────────────────────────────────────────────────

Q187: You see a DTC P0A80 (Battery System Degraded) in a production vehicle. What do you do?
A: Systematic investigation:
   1. Read DTC status byte: confirmed? pendingDTC? active?
   2. Read DTC extended data: occurrence counter, last conditions (temp, SoC)
   3. Read DID 0xF121 (BMS SoH): what does BMS report?
   4. Check correlation: does DTC always occur in cold weather?
   5. Check SoH algorithm: does it run at low temperature? (see Case Study 8)
   6. Compare BMS SoH to reference measurement (full charge/discharge test at 25°C)
   7. If SoH measurement incorrect: BMS firmware issue
   8. If SoH genuinely low: battery degradation issue
   
   Document findings → JIRA → RCA → fix BMS algorithm or replace battery per warranty.

────────────────────────────────────────────────────────────────

Q188: What is your approach when you find a test that fails intermittently?
A: 1. Increase sample size: run 100+ iterations, capture failure rate
   2. Correlate with conditions: temperature, SoC, time since start, specific sequences
   3. Add more logging: verbose CAN trace, extended DTC capture
   4. Analyze DTC extended data for context (temperature, odometer at failure)
   5. Check for timing dependencies: is there a race condition?
   6. Check for resource contention: NVM writes, ISR load, bus load spikes
   7. If hardware: check connector quality, voltage margins at temperature extremes
   8. Create automated regression test that runs continuously overnight
   9. Document in JIRA: reproduction rate, conditions, evidence

────────────────────────────────────────────────────────────────

Q189: What tools have you used for automotive testing?
A: Strong answer (adapt to your experience):
   - Vector CANoe: CAN simulation, CAPL scripting, restbus, diagnostics, testing
   - Vector CANalyzer: CAN bus analysis, debugging, protocol analysis
   - Python (python-can, cantools, udsoncan, pytest): automated test framework
   - dSPACE/ETAS LABCAR: HIL testing
   - Vector CANdb++/DBC editor: network database management
   - JAMA/IBM DOORS: requirements management
   - JIRA: defect and sprint management
   - Git: version control for CAPL scripts and Python tests

────────────────────────────────────────────────────────────────

Q190: How do you validate charging power matches specification?
A: Multi-point measurement approach:
   1. Set up EVSE simulator with known current capability (e.g., 32A)
   2. Monitor OBC_ChargingCurrent and OBC_ChargingVoltage on CAN
   3. Calculate CAN-reported power: P = V × I
   4. Measure actual AC input power with power analyzer (Yokogawa, Hioki)
   5. Measure DC output power at battery inlet
   6. Calculate efficiency: η = P_DC_out / P_AC_in
   7. Compare to spec: η ≥ 90% at full load
   8. Verify CAN-reported power matches measured power ± 2%
   9. Run at multiple EVSE current levels: 10A, 20A, 32A

────────────────────────────────────────────────────────────────

Q191: What is a BMS contactor welding check and why is it ASIL-D?
A: Contactor welding check verifies contactors actually opened when commanded.
   Method: check if voltage across contactor ≠ 0 after open command
   (if welded closed: V_across ≈ 0V; if open: V_across = V_battery)
   
   Why ASIL-D: If contactor is welded closed after crash:
   - HV remains active even with BMS commanding open
   - First responders could be electrocuted
   - Maintenance personnel at risk
   - HV remains even with battery disconnected service plug
   
   Must be ASIL-D (S3=fatal, E2, C2 = ASIL-C; but with additional factors → D)
   Hardware: contactor with auxiliary contacts for position feedback
   Software: check auxiliary contact state after open command

────────────────────────────────────────────────────────────────

Q192: What is AUTOSAR SecOC and why does it matter for EVs?
A: SecOC (Secure Onboard Communication) is an AUTOSAR module that adds
   Message Authentication Codes (MACs) to CAN frames.
   
   Problem it solves: CAN has no authentication — anyone with bus access
   can inject or replay messages. For EVs: attacker at OBD port could
   inject fake BMS messages, override torque limits, etc.
   
   SecOC:
   - Each safety-critical CAN message includes MAC + freshness counter
   - MAC = CMAC-AES-128(shared key, freshness || message_id || data)
   - Receiver verifies MAC — rejects any modified/replayed message
   
   For EV: Apply SecOC to BMS→VCU messages (SoC, limits) and
   VCU→MCU torque commands.
```

---

## SECTION 15 SUMMARY

This interview preparation section covers:

| Topic | Questions |
|-------|-----------|
| Systems Engineering | Q1–Q40 |
| CAN & CANoe | Q41–Q80 |
| CAPL Programming | Q81–Q110 |
| Python Automation | Q111–Q140 |
| UDS Diagnostics | Q141–Q170 |
| EV Charging & Powertrain | Q171–Q192 |

**Key interview tips:**
1. Always connect theory to a real example from your experience
2. For debugging questions: describe your systematic approach (not just the answer)
3. Quantify your work: "47 test cases," "30-minute soak test," "found 15 bugs"
4. Mention tools by name: CANoe, cantools, python-can, udsoncan, JIRA
5. Know your DTCs and UDS services by hex code, not just by name

---

*Next: Section 16 — Complete End-to-End Projects*
