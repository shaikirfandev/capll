# UDS Diagnostics — ADAS STAR Scenarios
## 100 Real Interview Cases | AEB · ACC · LDW · BSD · Park Assist · HWA | April 2026

**STAR Format:** S=Situation T=Task A=Action R=Result
**ECU:** ADAS ECU (0x7A0 → 0x7A8), also references radar (0x7A2), camera (0x7A4), ultrasonic (0x7A6)

---

### Case 1 — AEB DTC U0429 Lost Radar Communication (Expanded)

**S (Situation):** A brand-new production vehicle (Odometer: 12km) displays an "AEB System Disabled" warning on the instrument cluster. The customer reports the Autonomous Emergency Braking (AEB) feature is unavailable. A preliminary scan shows DTC U0429 is active in the ADAS control module.

**T (Task):** Perform a full root cause analysis to identify why the ADAS ECU has lost communication with the forward-looking radar. Diagnose the issue using UDS, propose a fix, verify the repair, and suggest a long-term prevention strategy.

---

#### **A (Action):**

**1. Initial DTC Confirmation & Freeze Frame Analysis**

*   **Action:** Send a `ReadDTCInformation` request to the ADAS ECU (address `0x7A0`) to confirm the fault and retrieve its status.
*   **UDS Command:**
    ```
    19 02 09
    ```
*   **Byte Breakdown:**
    *   `19`: Service ID for `ReadDTCInformation`.
    *   `02`: Sub-function `reportDTCByStatusMask`. This asks for DTCs that match a specific status.
    *   `09`: Status Mask. `0x09` (`0000 1001`) requests DTCs where `testFailed` (bit 0) is true AND `confirmedDTC` (bit 3) is true. This is the standard way to ask for currently active and confirmed faults.
*   **Result:** The ECU responds confirming `U0429` is active.

*   **Action:** Retrieve the freeze frame data associated with `U0429` to understand the conditions at the exact moment the fault was logged.
*   **UDS Command:**
    ```
    19 04 C0 00 01 01
    ```
*   **Byte Breakdown:**
    *   `19 04`: `ReadDTCInformation` with sub-function `reportDTCSnapshotRecordByDTCNumber`.
    *   `C0 00 01`: The DTC `U0429` encoded. Network DTCs often have a different encoding scheme.
    *   `01`: The snapshot record number. `0x01` is the first (and often only) record.
*   **Result:** Freeze frame shows: `Odometer=12km`, `VehicleSpeed=0`, `IgnitionCycles=3`, `ECU_Voltage=12.4V`. This tells us the fault occurred very early in the vehicle's life, while stationary, and the ADAS ECU itself had good voltage.

**2. Investigating the Radar Power Status**

*   **Hypothesis:** If the ADAS ECU has power but can't communicate with the radar, the radar itself might not have power.
*   **Action:** Read a custom DID (`Data Identifier`) from the ADAS ECU designed to report the status of its peripheral components, including the radar's power supply.
*   **UDS Command:**
    ```
    22 D0 80
    ```
*   **Byte Breakdown:**
    *   `22`: Service ID for `ReadDataByIdentifier`.
    *   `D0 80`: A custom DID for "Peripheral Power Status". This is OEM-specific.
*   **Result:** The ECU responds `62 D0 80 00`. The `0x00` in the response indicates `Radar_Power_Status = OFF`. This is the critical clue. The ADAS ECU is confirming it cannot detect a power signature from the radar module.

**3. Physical Inspection & Repair**

*   **Action:** Based on the UDS result, perform a physical inspection of the radar's power supply chain.
*   **Steps:**
    1.  Consult the vehicle's electrical schematic to locate the fuse for the radar module.
    2.  Locate and inspect fuse F27 in the engine bay fuse box.
    3.  **Finding:** The fuse is visibly blown.
    4.  Replace the blown fuse with a new one of the correct rating (e.g., 5A).
    5.  After replacement, the radar module's status LED turns on.

**4. Verification and Closure**

*   **Action:** Clear the DTCs and run a system self-test to confirm the fix.
*   **UDS Commands:**
    ```
    14 FF FF FF   // Clear All DTCs
    19 02 09      // Re-read DTCs by status mask
    31 01 E0 01   // Start AEB Self-Test Routine
    ```
*   **Byte Breakdown:**
    *   `14 FF FF FF`: Service `ClearDiagnosticInformation` with a group address of `0xFFFFFF` (all groups).
    *   `31 01 E0 01`: Service `RoutineControl` (`31`), sub-function `startRoutine` (`01`), with a routine ID of `E0 01` (OEM-specific ID for "AEB Full System Self-Test").
*   **Result:**
    *   The `14` service returns a positive response.
    *   The subsequent `19 02 09` read shows no active DTCs.
    *   The `31` service returns `71 01 E0 01 01`, where the final `01` means "Test Passed".
    *   The "AEB System Disabled" warning on the cluster is now off.

---

#### **R (Result) & Deeper Analysis:**

*   **Immediate Cause:** The radar module was unpowered due to a blown fuse (F27), causing the ADAS ECU to log a `U0429` communication loss DTC.
*   **Root Cause Theory:** A fuse blowing on a new vehicle suggests either a faulty fuse from the supplier (unlikely but possible) or, more likely, a momentary short circuit during the vehicle assembly/testing process that stressed the fuse. It could also indicate a wiring harness issue (e.g., chafing against the chassis), which would require a more in-depth physical inspection.
*   **DTC Deep Dive (U0429):**
    *   **Code:** `U0429 - Invalid Data Received From Steering Column Control Module`. *Wait, the description seems wrong!* This is a common interview trap. While the generic SAE definition for U0429 might point to the steering module, in the context of this specific OEM and ADAS system, this "U" code has been repurposed to mean "Lost Communication with Forward Radar". Always rely on the OEM's specific DTC tables, not generic online lists.
    *   **Related DTCs:** `U0121` (Lost Comm with ABS), `U0155` (Lost Comm with Cluster), `B2A77` (ECU Internal Humidity). If multiple "U" codes are present, it points towards a broader network or power issue rather than a single component.
*   **Prevention & Design-Level Fix:**
    1.  **EOL Test Improvement:** The End-of-Line (EOL) testing procedure at the factory should be updated. After the final software flash, a UDS script should run that queries the status of all ADAS peripherals (like `22 D0 80`). This would have caught the unpowered radar before the vehicle ever left the plant.
    2.  **Fuse Analysis:** The blown fuse should be sent for failure analysis to rule out a manufacturing defect in the fuse itself.
    3.  **Harness Review:** If this issue repeats across other vehicles, a full design review of the radar wiring harness routing is necessary to check for potential chafing or pinch points that could cause intermittent shorts.
*   **Interview Tips & What the Interviewer is Looking For:**
    *   **Systematic Approach:** They want to see you move logically from DTC -> Freeze Frame -> Hypothesis -> Targeted Test -> Physical Inspection -> Verification. Don't just jump to replacing parts.
    *   **UDS Knowledge:** Mentioning specific services (`19`, `14`, `22`, `31`) and sub-functions (`02`, `04`) shows you know the tools. Explaining the byte codes is a bonus.
    *   **OEM Specificity:** Acknowledging that DIDs (`D080`) and Routine IDs (`E001`) are OEM-specific shows real-world experience. Pointing out the `U0429` description ambiguity is a sign of a senior-level engineer.
    *   **Thinking Beyond the Fix:** The best candidates don't just fix the problem; they think about how to prevent it from happening again (EOL test improvement, design review). This shows a "quality mindset".

---

### Case 2 — ACC DTC C1042 Radar Sensor Misalignment
**S:** ACC disengages randomly on highway. DTC C1042 active: Radar Horizontal Misalignment.
**T:** Verify radar alignment via UDS diagnostic and corrective calibration.
**A:**
```
10 03 → Enter Extended Session
22 [OEM DID radar alignment] → Read current alignment angle: +3.2° (spec: ±0.5°)
31 01 [Radar Alignment RID] → Start radar alignment routine
  → Position vehicle on flat ground, 25m to flat reflector
71 01 [RID] 01 → Result: new angle computed −0.1° (within spec)
2E [OEM DID] [−0.1° encoded] → Write new alignment value
11 03 → Soft reset
19 02 09 → C1042 not present
31 01 E0 02 → Run alignment verification routine → PASS
```
**R:** C1042 cleared. Alignment corrected via UDS routine. Root cause: vehicle body damage moved radar bracket 3.2° off axis. Alignment re-done and verified.

---

### Case 3 — Emergency AEB Does Not Activate in Test
**S:** NCAP-style AEB test at 50 km/h against stationary target. AEB does not activate. No DTCs present.
**T:** Use UDS to read AEB activation thresholds and mode status.
**A:**
```
10 03
22 [AEB_Config DID] → Read: AEB_Enable=0x00 (disabled!)
19 02 FF → Scan all DTCs → none
22 [AEB_Mode DID] → AEB_Mode=0x04 (workshop mode = AEB suppressed)
31 01 [ExitWorkshop RID] → Exit workshop mode → 71 01 [RID] 01 PASS
2E [AEB_Enable DID] 01 → Re-enable AEB
11 01 → Hard reset
22 [AEB_Config DID] → AEB_Enable=0x01 confirmed
```
**R:** AEB was left in workshop mode from a previous repair. Workshop mode suppresses AEB to prevent false activation during service. Root cause: workshop mode not cleared after repair. EOL check now includes AEB mode verification.

---

### Case 4 — DTC B2A41 Camera Sensor Dirty/Blocked
**S:** Customer reports LDW and LKA not working. DTC B2A41: Forward Camera Blocked.
**T:** Distinguish between a real obstruction and a faulty camera self-clean sensor.
**A:**
```
19 02 09 on 0x7A4 (camera ECU) → B2A41 confirmed
22 [Camera_Status DID] → BlockageStatus=0x01 (obscured)
22 [Wiper_Status DID] → WindshieldWiper_Cycles=0 (camera area not cleaned by wiper)
2F [Wiper_Control DID] 03 01 → Force single wiper cycle → camera area cleared
Wait 2s...
22 [Camera_Status DID] → BlockageStatus=0x00 (clear)
14 FF FF FF
19 02 09 → No active DTCs
```
**R:** B2A41 was genuine blockage (insect debris on camera). Wiper cleared it. Added to customer advisory: keep camera area clean. Camera self-diagnostic confirmed working correctly.

---

### Case 5 — Security Access Lockout on ADAS ECU During Calibration
**S:** Calibration station sends wrong security key 3 times. ADAS ECU now reporting 0x36 (exceededNumberOfAttempts). Entire calibration line stopped.
**T:** Recover ECU from security lockout.
**A:**
```
27 01 → 7F 27 37 (requiredTimeDelayNotExpired) ← lockout active
Wait 90 seconds (manufacturer lockout period)
27 01 → 67 01 [seed bytes]  ← seed now available
Compute key with correct algorithm
27 02 [correct key] → 67 02 ← security unlocked
Continue calibration sequence
31 01 [Cal RID] → calibration proceeds normally
```
**R:** ECU recovered after waiting the lockout timer (90s defined in ECU spec). Root cause: wrong security key version loaded at station. Updated station with correct key algorithm. Lockout timer value documented in station runbook.

---

### Case 6 — AEB Permanent DTC Environmental Damage
**S:** AEB system has permanent DTC P0A1F that cannot be cleared with 14 FF FF FF.
**T:** Understand permanent DTC and either clear properly or replace ECU.
**A:**
```
19 18 → reportDTCWithPermanentStatus → P0A1F present
14 FF FF FF → 54 positive, but P0A1F still in 19 18
19 02 09 → P0A1F not in confirmed memory (correctly cleared)
Explanation: Permanent DTC can only be cleared by completing OBD drive cycle
  → System must run self-monitoring → if monitor passes → permanent DTC cleared automatically
Drive cycle completed:
  - Highway at 80+ km/h for 5 min
  - ACC function actively tracking target
19 18 → P0A1F no longer present
```
**R:** Permanent DTC cleared after completed drive cycle. Root cause: previous water ingress into ADAS ECU connectors caused intermittent fault. Connector repaired and sealed. Monitor passed → permanent DTC cleared.

---

### Case 7 — Radar Object List Empty — Firmware Mismatch
**S:** After radar ECU software update at dealer, ADAS fusion ECU shows no radar objects. No DTCs except U0429 (no communication).
**T:** Verify software versions match between radar and fusion ECU expectations.
**A:**
```
22 F1 89 on 0x7A2 (radar) → SW Version: 3.2.0
22 F1 89 on 0x7A0 (ADAS fusion) → expected radar version: 3.1.x
→ Version mismatch detected
31 01 FF 01 on 0x7A0 → Check Programming Dependencies → Result: 0x02 FAIL (radar version incompatible)
Load correct radar firmware version 3.1.5:
10 02 → 27 11/12 → 28 03 01 → 31 01 FF 00 → 34 → 36 → 37 → 31 01 FF 01 → PASS
11 01 → Reset
19 02 09 → No DTCs. Radar objects present.
```
**R:** Root cause: dealer loaded wrong firmware version (3.2.0 not compatible with this ADAS ECU). Programming dependency check failure is the key diagnostic. Correct version 3.1.5 restored. Lessons: always run 31 01 FF 01 after any ECU flash.

---

### Case 8 — BSD (Blind Spot Detection) DTC Asymmetric
**S:** DTC C0A45 active on left rear radar only. Right radar fine. BSD indicator only works on right side.
**T:** Isolate fault to sensor vs harness vs ECU.
**A:**
```
19 02 09 on 0x7A6 → C0A45: Left Rear Radar Fault
22 [LRRD_Status DID] → Voltage=11.2V (spec: >11.5V), Comms_Errors=47
22 [RRRD_Status DID] → Voltage=12.1V, Comms_Errors=0
CAN trace: Left radar CAN bus has intermittent errors (bit error count rising)
Physically inspect: Left rear radar connector corroded
Clean and re-pin connector → left radar comms restored
14 FF FF FF
19 02 09 → No active DTCs
Test: both BSD indicators function correctly
```
**R:** Corroded connector on left rear radar. High contact resistance caused voltage drop and CAN errors. Re-pinned connector. Post-fix: run 100 CAN error count check as pass criterion.

---

### Case 9 — Park Assist: One Ultrasonic Sensor Fails at Hot Temperature
**S:** Intermittent P1A23 DTC (Ultrasonic Sensor 3 Signal Invalid). Only occurs when ambient temperature > 35°C. Works fine in morning.
**T:** Capture freeze frame and characterise thermal dependency.
**A:**
```
19 04 [P1A23 bytes] 01 → Read freeze frame
Freeze frame: AmbientTemp=38°C, Odometer=15420km, Speed=0
22 [UltraTemp DID] on sensor 3 → SensorTemp=71°C (near design limit)
22 [UltraTemp DID] on sensors 1,2,4 → 52°C, 53°C, 54°C (normal)
Root cause hypothesis: Sensor 3 located near exhaust → thermal soak
Confirm: 19 17 → DTC Fault Detection Counter for P1A23 = 89/127 (near confirmed threshold)
Thermal protection cover added to sensor 3 bracket
Re-test at 40°C ambient → SensorTemp=58°C → no fault
```
**R:** Sensor 3 directly above exhaust heat zone. Thermal soak caused circuit instability above 65°C. Metal heat shield added. Freeze frame data was essential to correlate temperature. Design change propagated to all vehicles with rear sensor in that position.

---

### Case 10 — Lane Keeping Assist Pulls Incorrectly to Left
**S:** LKA (Lane Keep Assist) applies steering correction pulling left when it should pull right. DTC B3A88 active: Lane Detection Camera Angle Offset Out of Range.
**T:** Read and correct camera extrinsic calibration via UDS.
**A:**
```
10 03 → Extended session
22 [Camera_Pitch DID] → −1.8° (spec: −0.5° to +0.5°)
22 [Camera_Yaw DID] → +2.1° (spec: ±0.5°)
31 01 [Camera_Cal_RID] → Start camera calibration routine
  → Vehicle on calibration rig with targets
71 01 [RID] 01 → Calibration complete
22 [Camera_Yaw DID] → +0.1° (within spec)
22 [Camera_Pitch DID] → −0.2° (within spec)
14 FF FF FF → Clear DTCs
19 02 09 → B3A88 not present
Test drive: LKA corrects correctly to right when drifting left
```
**R:** Camera misalignment (pitch + yaw) caused incorrect lane position estimate. LKA responded to wrong reference. Calibration via UDS corrected both axes. Likely cause: windscreen replacement without recalibration.

---

### Case 11 — ACC Following Distance Shorter Than Set
**S:** Customer sets ACC following distance to level 3 (furthest). ACC follows at level 1 distance. No DTC.
**T:** Read and verify following distance configuration via UDS.
**A:**
```
22 [ACC_Gap DID] → Current_Gap_Setting=0x01 (level 1 — closest)
22 [ACC_GapRequest DID] → Driver_Requested=0x03 (level 3 — correct)
→ Gap setting not propagating from driver request to ACC setting
22 [HMI_ACC DID] → Gap_Override_Active=0x01 (override active!)
22 [Gap_Override_DID] → Override_Source=0x02 (EOL configuration)
EOL accidentally set gap to override level 1
2E [Gap_Override DID] 00 → Disable override
11 03 → Soft reset
22 [ACC_Gap DID] → Now follows driver request correctly
```
**R:** EOL station had erroneously written gap override = level 1. Driver's selection was ignored. EOL configuration write verified corrected. Regression test added: verify no gap override written at EOL unless intentionally specified.

---

### Case 12 — Highway Driving Assist Unavailable: Speed Sign Reader Fault
**S:** HDA (Highway Drive Assist) shows unavailable. System reads road speed limit as 0 km/h from camera. DTC C3B12: Speed Sign Recognition Error.
**T:** Diagnose whether camera classifier or DID configuration is the fault.
**A:**
```
22 [SpeedLimit DID] → Detected_Limit=0x00 km/h (incorrect)
22 [Camera_Mode DID] → Camera_Region=0x00 (unknown region!)
→ Camera speed sign model requires market region to be configured
2E [Camera_Region DID] 0x01 → Set region to Europe
11 03 → Soft reset
22 [SpeedLimit DID] → Detected_Limit read correctly on test drive
14 FF FF FF
19 02 09 → C3B12 cleared, no active DTCs
```
**R:** Camera region not configured — sign classifier could not select the correct sign model for European speed signs. EOL did not write market region configuration. Added to EOL sequence: write camera region DID.

---

### Case 13 — UDS Communication Timeout During ADAS Calibration
**S:** Calibration routine (31 01 RID) times out after 25 seconds. ECU does not respond.
**T:** Diagnose why ECU stops responding mid-calibration.
**A:**
```
31 01 [Cal_RID] → Response pending (7F 31 78) ← responseCorrectlyReceivedResponsePending
Wait... → second 7F 31 78 received at t=10s
Wait... → third 7F 31 78 at t=20s
Wait... → no response at t=25s → timeout
Re-enter session: 10 03 → positive response (ECU still alive)
22 [Cal_Status DID] → Calibration_State=0x03 (in-progress but waiting for sensor condition)
22 [Cal_Condition DID] → Waiting for zero motion (vehicle moving slightly on lift)
Stabilise vehicle on lift → re-run 31 01
71 01 [Cal_RID] 01 → PASS in 8 seconds
```
**R:** Calibration routine was waiting for vehicle motion < 0.01 m/s (required for static calibration). Small movement from technician leaning on car was causing it. Vehicle stabilised → routine completed. 0x78 responses correctly indicate processing — tester must continue waiting up to P2* (5s between 0x78s is conformant).

---

### Case 14 — DTC Fault Detection Counter Used to Predict Imminent Failure
**S:** Pre-delivery quality check. No confirmed DTCs but validation engineer wants to check early warning state.
**T:** Use sub-function 0x17 to check pending DTC counters.
**A:**
```
19 17 → reportDTCFaultDetectionCounter
Response includes:
  C0 A4 11 → FDC=45/127 (radar temperature — rising, not yet confirmed)
  C0 B2 22 → FDC=12/127 (camera voltage margin — low but stable)
  C0 A4 45 → FDC=3/127  (ultrasonic — just started showing)
C0 A4 11 FDC=45 is concerning — radar ECU temperature cycles near threshold
Check radar mounting: found partially blocked ventilation slot
Clear obstruction → re-test → FDC drops to 8/127 after 30min soak
Document: FDC monitoring is an excellent pre-confirm fault detection tool
```
**R:** Pre-delivery, caught a radar thermal pre-fault before it became a customer complaint. Sub-function 0x17 is available in default session — no security needed. Incorporated into pre-delivery inspection checklist.

---

### Case 15 — AEB Software Rollback After Customer Complaint
**S:** New AEB SW version 3.5 causes false braking events. Need to roll back to 3.4. ADAS ECU is in field vehicles.
**T:** Re-flash ADAS ECU with older software using full UDS programming sequence.
**A:**
```
22 F1 89 → Current SW: 3.5.0
Enter programming:
  10 01 → 27 01/02 → 10 02 → 27 11/12
  28 03 01 → Disable comms
  31 01 FF 00 → Erase memory → 71 01 FF 00 01 PASS
  34 00 44 [start addr] [size] → 74 20 [max block] ← max block 256 bytes
  36 01...36 nn → Transfer all blocks
  37 → Transfer exit
  31 01 FF 01 → Check dependencies → PASS
  28 00 01 → Re-enable comms
  11 01 → Hard reset
22 F1 89 → SW: 3.4.2 confirmed
31 01 E0 01 → AEB self-test → PASS
```
**R:** SW 3.5 successfully replaced with 3.4.2. Post-flash: dependency check always run. Root cause under investigation: 3.5 had modified TTC calculation threshold causing false triggers. 3.5 removed from field update.

---

### Case 16 — ACC Cruise Speed Incorrect by 10 km/h
**S:** ACC set speed = 100 km/h. Actual maintaining speed = 110 km/h. No DTCs.
**T:** Investigate set speed signal vs actual control.
**A:**
```
22 [ACC_SetSpeed DID] → SetSpeed=100 km/h (correct)
22 [Ego_Speed DID] → EgoSpeed_kph=89.1 km/h (incorrect — too low)
22 [WheelSpeed DID] → LF=100, LR=100, RF=101, RR=100 (correct)
→ ACC's EgoSpeed is under-reading by ~10%
22 [WheelCircumference DID] → 1.98m (spec for this tyre: 2.19m)
→ Wrong tyre circumference! ECU configured for 16" tyre, vehicle has 18"
2E [WheelCircumference DID] 2.19 encoded → Write correct value
11 03 → Soft reset
22 [Ego_Speed DID] → Correct at 100 km/h
```
**R:** Wrong tyre (wheel) circumference calibration caused ~10% speed error. ACC compensated by maintaining 110 km/h while thinking it was driving at 100. Root cause: vehicle built with non-standard tyre without updating ECU configuration. Added tyre size check to EOL test.

---

### Case 17 — Emergency Call Trigger During ADAS Test (Unexpected)
**S:** During ADAS bench test with simulated crash signal, eCall system activates unexpectedly. ADAS ECU is flooding CAN with crash signal.
**T:** Suppress eCall during ADAS testing using UDS.
**A:**
```
85 02 on eCall ECU → turnOffDTCSetting (prevent eCall DTC from triggering comms cascade)
28 01 01 on ADAS ECU → enableRxDisableTx (suppress crash signal broadcast)
Run ADAS test
28 00 01 → Re-enable comms
85 01 → Re-enable DTC setting
Note: Could also use 2F [CrashSignal DID] 02 (freeze current state = no crash) during test
```
**R:** Communication control and DTC suppression used together to isolate ADAS test from safety systems. Always restore both services after test. Safety: confirm 28 00 01 and 85 01 sent before vehicle leaves test bench.

---

### Case 18 — Park Pilot Calibration via UDS Fails: NRC 0x22
**S:** New Park Pilot feature requires post-production calibration. UDS command 31 01 [Park_Cal] returns 0x22 conditionsNotCorrect.
**T:** Determine and satisfy the conditions required for calibration.
**A:**
```
31 01 [Park_Cal RID] → 7F 31 22
22 [Park_Cal_Conditions DID] → Conditions byte: 0x03
  Bit 0=1: requires engine running
  Bit 1=1: requires gear = Reverse
  Bit 2=0: OK (speed = 0 met)
  Bit 3=0: OK (vehicle on flat ground met)
Start engine → shift to Reverse → re-attempt
31 01 [Park_Cal RID] → 71 01 [RID] 01 PASS
```
**R:** 0x22 NRC is often misread as a permanent error. It means conditions are not met. Always read the conditions DID to understand what the ECU is waiting for. Calibration required: engine on + reverse gear.

---

### Case 19 — Ghost DTC After ADAS ECU Replacement
**S:** ADAS ECU replaced. New ECU now shows aged DTCs from previous unit history (configuration mismatch).
**T:** Clear ECU NVM configuration to factory state.
**A:**
```
19 02 FF → Many old DTCs with confirmed status (from previous ECU history — impossible on fresh ECU)
→ Replacement ECU was actually a refurbished unit with old data
31 01 [FactoryReset RID] → Factory reset routine
71 01 [RID] 01 → PASS (reset confirmed)
11 01 → Hard reset
19 02 FF → No DTCs (clean state)
22 F1 8C → Serial number now correct (new ECU serial)
Perform full EOL sequence to re-write configuration
```
**R:** Refurbished ECU retained previous vehicle data. Factory reset via routine control cleared NVM. Always run factory reset + full EOL configuration sequence on any replacement ECU.

---

### Case 20 — ADAS ECU 0x78 Response Pending Loop
**S:** Service 0x19 to read DTCs returns 0x78 response pending 15 times then finally responds. Total wait: 8 seconds. Is this a problem?
**T:** Determine if this is a conformance issue or normal behaviour.
**A:**
```
P2 Server = 50ms (max time before first response or 0x78)
P2* Server = 5000ms (max time between each 0x78 and final response)
Session P2* Client = 5000ms (tester waits up to 5s for each part)

15 × 0x78 = 15 × some interval...
Total 8s: each 0x78 arrived < 5s apart? YES (about every 500ms per 0x78)
→ Conformant behaviour but unusual for a simple DTC read
Check: ECU was busy running self-monitoring routines at start-up
After ECU warm (60s after key on): same 19 02 09 returns in < 200ms
→ Behaviour is start-up artefact, not a conformance violation
```
**R:** Conformant but sub-optimal. ECU was prioritising start-up monitoring over diagnostic response. Timing documented. Tool configured to wait full P2* × count. No issue if each 0x78 arrives within P2* = 5 seconds of the previous response or request.

---

### Case 21 — AEB DTC C0501 Wrong Vehicle Speed Signal Source
**S:** DTC C0501: Invalid Vehicle Speed from ABS active. AEB disabled. ABS is working correctly (vehicle speed on cluster is correct).
**T:** Identify signal routing mismatch.
**A:**
```
22 [ADAS_EgoSpeed_Source DID] → Source=0x02 (reading from body CAN)
22 [ABS_Speed DID] on body CAN → Signal present, correct value
22 [ADAS_ABS_Comms DID] → Last_ABS_msg_age=2400ms (2.4 seconds stale!)
→ ADAS is on powertrain CAN; ABS speed message is on body CAN
→ Gateway should bridge speed from body to powertrain, but gateway routing not configured
2E [Gateway_Route DID] [enable ABS speed bridge] → configure gateway
11 01 → Reset both gateway and ADAS
19 02 09 → C0501 cleared
```
**R:** Signal routing was missing at gateway. After a gateway software update, the ABS speed routing rule was dropped. ABS message on body CAN not forwarded to powertrain CAN where ADAS ECU lives. Gateway routing table restored.

---

### Case 22 — Multi-DID Read for ADAS Health Check
**S:** Daily build verification requires checking 5 ADAS configuration DIDs quickly (< 2 seconds total).
**T:** Use multi-DID read to efficiently read all in one transaction.
**A:**
```
Request: 22 F1 89 F1 90 D0 10 D0 11 D0 12
Response: 62
  F1 89 [SW Version bytes]
  F1 90 [VIN bytes]
  D0 10 [AEB Enable flag]
  D0 11 [ACC Enable flag]
  D0 12 [LKA Enable flag]

Single request → all 5 values in one response
Verify:
  SW Version = expected build
  VIN = test vehicle VIN
  AEB/ACC/LKA all = 0x01 (enabled)
```
**R:** Multi-DID read confirmed all 5 values in 140ms. More efficient than 5 individual reads (would take ~500ms at P2 spacing). Incorporate into build verification script.

---

### Case 23 — ADAS Cooldown: Security Access After 0x36 Lockout Recovery
**S:** ADAS ECU locked out (0x36). Development spec says lockout = 10 attempts per vehicle lifetime. Current vehicle at attempt 9. Must proceed carefully.
**T:** Plan single careful attempt with correct key.
**A:**
```
Check: 19 17 → DTC P1F34 (SecurityAccessAttemptExceeded) FDC=115/127 (nearly to permanent DTC)
Wait: 27 01 → 7F 27 37 (delay not expired: must wait 240 seconds per spec)
Wait 240s...
27 01 → 67 01 [seed: DE AD BE EF]
Apply correct algorithm: Key = (Seed × 0x3141) XOR 0xA5A5A5A5 → Key = [correct bytes]
27 02 [key] → 67 02 ← success! Security level 1 unlocked
Print in work order: "Attempt 10/10 used — ECU must not need further security access or replacement required"
```
**R:** Final attempt used carefully. Correct key computed accurately. If this had failed: ECU permanently locked, replacement mandatory. Documentation updated: always verify key algorithm version before any security access attempt.

---

### Case 24 — Read DTC Extended Data: Failure Counter and Healing
**S:** DTC P2A09 (Radar Return Rate Too Low) appears intermittently. Need to understand if it is healing (self-recovering) or getting worse.
**T:** Use extended data record to read occurrence count and healing counter.
**A:**
```
19 06 [P2A09 bytes] 01 → Read extended data record 0x01
Response includes:
  ExtRecord 0x01:
    FailureCounter=14 (set 14 times since last clear)
    HealingCounter=11 (healed 11 of 14 times — 79% heal rate)
    LastFailOdometer=14620km
    LastHealOdometer=14631km
→ Most failures heal quickly → intermittent condition, not permanent hardware fault
Pattern: failures at cold start (radar warm-up), heals after 2-3 minutes
Root cause: Radar heater not coming on at cold start (related DTC P2B11 heater fault)
Fix heater circuit → P2A09 failure counter stops incrementing
```
**R:** Extended data records reveal failure history patterns not visible from confirmed DTC alone. Healing counter showed intermittent nature. Led to correct root cause (heater fault) rather than replacing the radar.

---

### Case 25 — LDW Incorrectly Active at Low Speed (Below Threshold)
**S:** LDW activating at parking lot speeds (< 15 km/h). Should only activate above 60 km/h. No DTC.
**T:** Check LDW activation speed threshold configuration.
**A:**
```
22 [LDW_LowSpeed_Threshold DID] → 0x0F = 15 km/h (should be 0x3C = 60 km/h)
→ Low speed threshold incorrectly programmed
2E [LDW_LowSpeed_Threshold DID] 0x3C → Write 60 km/h
11 03 → Soft reset
22 [LDW_LowSpeed_Threshold DID] → 0x3C = 60 km/h confirmed
Test: LDW not active below 60 km/h → pass
Test: LDW active above 60 km/h with lane drift → pass
```
**R:** EOL configuration error: threshold DID scaled by 4 (0x3C = 60, not 60 directly). Encoding error in EOL station tool parameter file. Fixed in parameter file; all affected vehicles recalled for configuration update. 84 vehicles affected.

---

### Case 26 — Traffic Sign Recognition: Region Coded Incorrectly
**S:** TSR (Traffic Sign Recognition) reads 30 mph signs as 48 km/h. Vehicle is in UK (mph market).
**T:** Verify and correct market/unit configuration.
**A:**
```
22 [TSR_Region DID] → Region=0x01 (Europe km/h)
Vehicle is UK market → should be 0x02 (UK mph)
2E [TSR_Region DID] 0x02 → Set UK mph
22 [TSR_Unit DID] → Now mph
Test: TSR correctly reads UK road signs in mph
Cluster display matches TSR reading
```
**R:** Region coded incorrectly at production (vehicle diverted from EU order to UK without ECU re-coding). Market code is a single write via 2E. Added to divert/remarket procedure.

---

### Case 27 — Cross-Traffic Alert False Alarm Suppression via UDS
**S:** RCTA (Rear Cross Traffic Alert) triggers every time reversing from home garage due to reflections off metal garage door.
**T:** Check if there is a sensitivity calibration option.
**A:**
```
10 03 → Extended session
22 [RCTA_Threshold DID] → Threshold=0x14 (20 — in raw ECU units, most sensitive)
Spec range: 0x14 (most sensitive, 20) to 0x28 (least sensitive, 40)
Adjust: 2E [RCTA_Threshold DID] 0x1E → 30 (medium sensitivity)
Test in garage → RCTA no longer false-triggers on metal door
Test on road crossing → RCTA still triggers correctly on approaching vehicles
Document adjustment in work order
```
**R:** Sensitivity reduced to eliminate garage reflection false alarm while maintaining proper cross-traffic detection. Customer-specific calibration possible via authorised workshop UDS session.

---

### Case 28 — AEB Inhibition During Trailer Tow Via UDS
**S:** Customer attaches trailer. AEB rear radar output causes false frontal AEB events (trailer detected as object). Need to configure trailer tow mode.
**T:** Enable trailer tow mode to suppress rear radar input to ADAS fusion.
**A:**
```
22 [TrailerTow_Mode DID] → 0x00 (disabled)
2E [TrailerTow_Mode DID] 0x01 → Enable trailer tow mode
Effect: Rear radar excluded from ADAS fusion
Effect: BSD and RCTA disabled automatically (documented in owner manual)
Effect: AEB still functional for front radar/camera combination
Test: No false AEB events with trailer attached
Test: AEB still activates on forward stationary target
11 03 → Soft reset
22 [TrailerTow_Mode DID] → 0x01 confirmed
```
**R:** Trailer tow mode configured via UDS. Mode must be manually disabled when trailer detached. Some OEMs auto-detect trailer via 7-pin socket supply voltage. Documented customer procedure.

---

### Case 29 — ADAS ECU: Programming Fails at Erase Memory Routine
**S:** During ECU flash, 31 01 FF 00 (erase memory) returns 7F 31 22 conditionsNotCorrect.
**T:** Satisfy erase conditions.
**A:**
```
31 01 FF 00 → 7F 31 22
22 [Flash_Precondition DID] → Bits:
  Bit0=0: OK (programming session active ✓)
  Bit1=1: FAIL — DTC setting not disabled
  Bit2=1: FAIL — Comms not disabled
  Bit3=0: OK (security unlocked ✓)

85 02 → Turn off DTC setting
28 03 01 → Disable Rx/Tx
31 01 FF 00 → 71 01 FF 00 01 PASS
```
**R:** Erase prerequisite check requires both DTC setting disabled and communication control disabled before allowing flash erase. Missed steps in flash sequence. Tool script updated to always include 85 02 and 28 03 01 before erase.

---

### Case 30 — ADAS: Mirror Memory DTC Investigation
**S:** Customer reports ADAS warning light in history (not current). Service DTC read shows nothing in standard memory. Customer insisting fault happened.
**T:** Check mirror memory for historical DTCs.
**A:**
```
19 02 09 → No confirmed DTCs
19 0F 09 → reportMirrorMemoryDTCByStatusMask
Response: C0 A1 12 [status byte]   ← C0A112: ADAS Processor Overtemperature
  Status: bit3=1 confirmed, bit5=1 failed since clear → was a real fault, now healed
19 04 C0 A1 12 01 → Mirror memory freeze frame:
  Odometer=8420km, AmbientTemp=42°C, CPUTemp=105°C (spec max=90°C)
Root cause: Severe ambient temperature + long sun exposure
Check: cooling solution, ventilation path, ADAS ECU placement near A/C vent
```
**R:** Mirror memory reveals what standard DTC read misses. DTC was real, confirmed, and healed. Useful for investigating customer complaints where the fault has cleared. CPU temperature at 105°C → design review of thermal management initiated for high-ambient markets.

---

### Case 31 — AEB not available after windscreen replacement
**S:** Customer had windscreen replaced at a third-party shop. AEB warning light on. Camera shows B2A50: Camera Calibration Required.
**T:** Perform post-windscreen camera calibration via UDS.
**A:**
```
19 02 09 → B2A50 pending/confirmed
22 [Camera_CalStatus DID] → CalStatus=0x02 (calibration required)
Drive to calibration bay with static target board
10 03 → Extended session
27 01/02 → Security access (calibration level)
31 01 [Camera_Static_Cal RID] → Start static calibration
  → Park 3m from target board (positioning per workshop manual)
71 01 [RID] 01 → PASS
14 FF FF FF → Clear DTCs
19 02 09 → B2A50 not present
22 [Camera_CalStatus DID] → 0x01 (calibrated)
```
**R:** Camera calibration mandatory after windscreen replacement. Third-party shop missed this step. Calibration via UDS routine with static target board completed in ~5 minutes. Added to third-party windscreen replacement instruction sheet.

---

### Case 32 — ADAS Fault: NRC 0x25 (noResponseFromSubnetComponent)
**S:** Sending UDS request to ADAS gateway address 0x7A0. Response 7F XX 25 received from gateway.
**T:** Understand and resolve sub-network no-response.
**A:**
```
7F 27 25 = noResponseFromSubnetComponent
→ Gateway received request and forwarded to ADAS ECU on sub-bus
→ ADAS ECU did not respond within gateway timeout
Check: is ADAS ECU initialised? (may be in sleep mode)
Send 3E 00 to ADAS ECU OBD address → 7E 00 response? No.
Attempt to wake ECU via NM (Network Management) frame
After NM wake-up: 22 F1 89 response in 50ms
Root cause: ADAS ECU in low-power sleep mode. Gateway timed out before ECU woke.
Fix: Adjust gateway forwarding timeout from 50ms to 300ms for ADAS sub-network
```
**R:** NRC 0x25 is a gateway error — the ECU didn't reply to the gateway's forwarded request. Not a direct ECU error. Sleep mode wakeup time was 200ms; gateway timeout was 50ms. Timeout extended.

---

### Case 33 — ACC DTC: Speed Sensor Improbable Signal
**S:** DTC C1021 (Speed Signal Improbable) on ACC. Triggered during highway driving. Intermittent.
**T:** Correlate with environmental conditions.
**A:**
```
19 06 [C1021 bytes] 01 → Extended data:
  FailureCount=8, Odometer at last fail=22145km
  Freeze: Speed=142 km/h, SteeringAngle=2°, AccY=0.1g
Pattern: Only occurs above 130 km/h
22 [SpeedHistory DID] → Speed samples: 138, 139, 141, 41, 143, 144
  → Single sample = 41 km/h (clearly an error spike)
22 [SpeedSource DID] → Source=ABS LF wheel speed
Investigate: wheel speed sensor gap (air gap) measured → LF sensor gap 2.1mm (spec: 0.4-0.9mm)
Replace wheel speed sensor
19 17 → C1021 FDC drops to 0 after fix
```
**R:** Air gap on LF wheel speed sensor too large → at high speed (high rotation frequency), sensor occasionally misses pulses → speed spike. Extended data pointing to LF sensor source was key. Replaced sensor; no further occurrences.

---

### Case 34 — ADAS ECU Variant Coding for Different Markets
**S:** Same ADAS ECU hardware used in 5 market variants. Need to configure market-specific features.
**T:** Write correct variant code for each market.
**A:**
```
Market Variant Coding DID: 0xD010
Encoding:
  0x01 = Germany (ISA speed limit enforcement not mandatory)
  0x02 = France (ISA mandatory, curfew features)
  0x03 = Japan (pedestrian proximity alert required)
  0x04 = US-California (AEB to FMVSS 127 required)
  0x05 = China GB standard

For vehicle destined Germany:
  10 03 → 27 01/02 →
  2E D0 10 01 → Write 0x01
  2E D0 11 [Germany feature flags] → additional features
  11 03 → Soft reset
  22 D0 10 → 0x01 confirmed
```
**R:** Variant coding enables one hardware design to serve multiple markets. Critical: coding must be completed at EOL before vehicle leaves plant. Wrong variant code in wrong market = regulatory non-compliance. Added variant code verification to EOL boundary check.

---

### Case 35 — Park Assist Grid Drawing Error Investigation
**S:** Parking assist camera shows distorted gridlines. No DTCs. Customer complaint: gridlines don't align with vehicle path.
**T:** Check camera distortion/projection calibration parameters.
**A:**
```
22 [Camera_Projection DID] → K1=−0.28, K2=0.08, P1=0.001, P2=0.002
Reference spec: K1=−0.25±0.05, K2=0.07±0.03
Values within spec but:
22 [Camera_Mount_Height DID] → 0.28m
Spec for RVC camera: 0.29m–0.32m
Camera bracket mounting height 0.28m (too low by 0.01m–0.04m)
→ Projection grid assumes different camera height → gridlines shifted up
Adjust bracket: camera height now 0.30m
2E [Camera_Mount_Height DID] 0.30 encoded
11 03 → Soft reset
Recheck grid: lines align with rear bumper correctly
```
**R:** Camera mount height parameter did not match physical installation. Grid overlay projection uses mount height to compute parking space edges. After bracket correction and DID update: gridlines aligned correctly.

---

### Case 36 — Multi-ECU DTC Scan via Functional Addressing
**S:** After a rear collision repair, need to scan all ADAS ECUs simultaneously for new DTCs.
**T:** Use functional addressing for efficient multi-ECU DTC read.
**A:**
```
Physical address: must query each ECU individually (slow)
Functional address: 7DF#03 19 02 09

Single broadcast request 7DF#03 19 02 09 →
Responses (each ECU responds independently):
  7A8#xx 59 02 09 ... (ADAS ECU — 2 DTCs)
  7A2#xx 59 02 09 ... (Radar — 0 DTCs)
  7A4#xx 59 02 09 ... (Camera — 1 DTC B2A50)
  7A6#xx 59 02 09 ... (Ultrasonic — 0 DTCs)

All responses collected in < 200ms total
Focus on B2A50: camera calibration required after repair
```
**R:** Functional addressing collects all ECU DTCs in one short window. B2A50 found — rear camera needs recalibration after collision repair. Calibration performed. Final re-scan confirms clear.

---

### Case 37 — ADAS Firmware Fingerprint Read for Audit
**S:** Warranty claim investigation. Customer says ADAS SW was modified by tuning garage. Need to verify original manufacturer SW.
**T:** Read programming fingerprint to identify last programming event.
**A:**
```
22 F1 98 → Read ApplicationSoftwareFingerprint
Response: [Tester ID: "0x1234 CARVANA-TUNING"] [Date: 2025-11-14] [Tool: "AutoFlash Pro"]
→ SW was re-programmed on 14 Nov 2025 by third party
Reference: OEM fingerprint should be [OEM Production ID + Manufacturing Date]
22 F1 99 → Read ApplicationDataFingerprint → Same third-party ID

Conclusion: ECU was re-programmed with non-OEM software by tuning shop
Warranty voided for ADAS system
```
**R:** Fingerprint DIDs (0xF198, 0xF199) are written by the flash tool and identify who last programmed the ECU. This is inadmissible evidence in some jurisdictions but very useful for warranty fraud detection. OEM programming always writes OEM tester ID.

---

### Case 38 — AEB DTC After OTA Update Fails Midway
**S:** OTA update for ADAS ECU fails at 60% completion (vehicle reset during transfer). Now ADAS reports P0A99 (ECU Programming Error) and is non-functional.
**T:** Recover ECU from partial flash state.
**A:**
```
22 F1 89 → SW version: "CORRUPT_VER_0000" (known corrupt state indicator)
22 [Boot_Status DID] → In bootloader mode: 0x01 (bootloader active, no application SW)
Enter programming via bootloader:
  10 02 direct → 27 11/12
  31 01 FF 00 → Full erase
  34/36/37 → Transfer complete correct SW image
  31 01 FF 01 → Check dependencies → PASS
  11 01 → Hard reset
22 F1 89 → Correct SW version restored
19 02 09 → P0A99 cleared
```
**R:** Partial flash left ECU in bootloader. Bootloader allows recovery programming without security unlocking the application (bootloader has separate security or none for recovery). Always ensure stable power during OTA update. Added OTA pre-condition: battery SOC > 70%.

---

### Case 39 — Read All Supported DTCs on New ADAS ECU
**S:** New ADAS ECU platform. Need to understand all DTCs it can report for test coverage planning.
**T:** Read complete supported DTC list.
**A:**
```
19 0A → reportSupportedDTC
Response: 59 0A [all DTC bytes with availability status byte]
Result: 142 DTCs reported as supported
Export to spreadsheet:
  DTC group C0xxx: 34 DTCs (radar related)
  DTC group C1xxx: 28 DTCs (camera related)
  DTC group B2xxx: 18 DTCs (sensor bus communication)
  DTC group U0xxx: 41 DTCs (network/communication)
  DTC group P1xxx: 21 DTCs (output/control)

Use list to build test case coverage matrix
Goal: test coverage > 80% of supported DTCs
```
**R:** 0x19 0A is extremely useful at start of test development. Lists all DTCs the ECU knows about regardless of whether any have been configured. Full coverage matrix built. 142 DTCs → 117 covered (82%) in test cases.

---

### Case 40 — Negative Test: Service Not Supported in Default Session
**S:** Test engineer verifies that sensitive ADAS write functions are NOT accessible in default session (security validation test).
**T:** Confirm 0x2E is rejected in default session.
**A:**
```
10 01 → Default session
2E D0 10 01 → 7F 2E 7F (serviceNotSupportedInActiveSession)
2E F1 90 [VIN] → 7F 2E 7F
31 01 [Cal RID] → 7F 31 7F
27 01 → 7F 27 7F (security access not available in default session per this ECU)

Now in extended:
10 03 → Extended session
27 01 → 67 01 [seed] ← security unlock available
27 02 [key] → 67 02
2E D0 10 01 → 6E D0 10 ← write now permitted

PASS: Confirmed write services gated by session + security
```
**R:** Session and security gating working correctly. Write services inaccessible without proper session + security unlock. This is a mandated security validation test for any ADAS ECU before homologation.

---

### Cases 41–50 — AEB/ACC Quick-Fire Scenarios

**Case 41 — DTC B2B31 (ACC Target Lost): Windscreen Contamination**
```
19 04 → Freeze: Rainy conditions, wiper active=0 (washer fluid empty)
Fix: Top up washer fluid, clean camera lens area
Result: B2B31 healed, ACC re-enabled
Lesson: Camera-based ACC relies on clean windscreen
```

**Case 42 — ACC Sudden Brake from Stationary (Low-Speed False AEB)**
```
19 06 → Extended data: Speed=0, Sensor=Ultrasonic3, Confidence=0.55
Ultrasonic sensor 3 confidence < threshold → should not trigger AEB
SW bug: AEB threshold check uses OR instead of AND for confidence
Fixed in SW patch 2.4.1
```

**Case 43 — DTC U0155 Lost Comm with Instrument Cluster (ADAS)**
```
Cluster not sending ACC set speed confirmation back to ADAS ECU
Gateway log: Cluster in sleep mode (power save)
Wake-up message added to Network Management sequence
U0155 cleared
```

**Case 44 — AEB Dual-Horn Test via Routine Control**
```
Workshop test: 31 01 [AEB_Horn_Test RID] → Two short horn blasts confirm AEB warning device
71 01 [RID] 01 PASS
Used to verify horn functional without driving scenario
```

**Case 45 — Read ACC History Data (Activation Log)**
```
22 [ACC_Activation_Log DID] → Last 10 ACC engagements logged with speed and distance
Odometer: 14221km, Speed=97km/h, Gap=2.8s (normal operation)
Odometer: 14231km, Speed=0, Gap=0.0s, EmergencyBrake=1 (AEB event)
Log shows one AEB event → same customer complaint corresponds to real AEB activation
```

**Case 46 — Suppress AEB DTC During Chassis Roller Test**
```
On chassis rollers: rear wheels spinning, front wheels stationary
AEB detects imminent collision (front camera sees static wall)
85 02 → DTC setting off prevents accumulation of false DTCs
28 01 01 → Suppress AEB output
After test: 85 01, 28 00 01 → restore normal operation
Run 14 FF FF FF → clear any test accumulation
```

**Case 47 — ADAS NVM Corruption: SW Checksum Fault**
```
DTC P0B15: ADAS Configuration Checksum Error
22 [Checksum_DID] → Stored=0x4A2F, Calculated=0x4A1F (mismatch)
NVM corruption after voltage spike (customer modified battery)
Re-write configuration via EOL sequence
P0B15 clears after correct config written and checksum verified
```

**Case 48 — Cross-Platform Feature Toggle (ADAS Feature Flags)**
```
Europe requires ISA (Intelligent Speed Assistance) from July 2024
22 [ISA_Enable DID] → 0x00 (disabled on this vehicle)
Verify build date: July 2024 production → must be enabled
2E [ISA_Enable DID] 0x01
Regulatory requirement documented
```

**Case 49 — ADAS ECU Response Time Measurement**
```
Measure diagnostic response latency (P2 Server compliance test):
10 × 22 F1 89 requests, measure request-to-response time
Results: Min=12ms, Max=48ms, Avg=23ms (all < 50ms P2 Server spec)
PASS: ECU meets ISO 14229 P2 timing
```

**Case 50 — AEB First/Last DTC Tracking**
```
19 0B → reportFirstTestFailedDTC: C0A11 (radar temp fault — first ever fault)
19 0C → reportFirstConfirmedDTC: C0A11  
19 0D → reportMostRecentTestFailedDTC: U0429 (most recent)
19 0E → reportMostRecentConfirmedDTC: U0429
Pattern: Chronological fault investigation using first/last DTC services
```

---

### Cases 51–70 — LDW / LKA / HWA / TSR / ISA Scenarios

**Case 51 — LKA Torque Calibration After Steering Column Replacement**
```
Steering column replaced → LKA apply torque reference lost
31 01 [Steering_Cal RID] → Calibrate steering centre
Drives straight line at 80 km/h → confirms zero-torque centre
71 01 [RID] 01 PASS → LKA re-enabled
```

**Case 52 — ISA Override Counter Exceeded**
```
ISA (Intelligent Speed Assist) spec: max 3 overrides per trip
DTC C3B21: ISA Override Limit Exceeded
22 [ISA_Override_Count DID] → 7 overrides in 45 mins
ISA function disabled for remainder of trip per regulation
Resets on next key cycle
14 FF FF FF → Not effective on ISA override count (resets only on ign cycle)
```

**Case 53 — HWA (Highway Assist) Not Available: Missing MAP Data**
```
DTC C4A12: Map Data Not Available for HWA
22 [MAP_Version DID] → 0x00000000 (no map loaded)
HWA requires HD map for lane-level positioning
Map provisioning via OTA needed
After map update (via TCU OTA): C4A12 cleared, HWA available
```

**Case 54 — TSR: Country-Specific Sign Not Recognised**
```
French 110 km/h autoroute sign not recognised after model update
22 [TSR_Model_Version DID] → 2.1.0
Known issue: Model 2.1.0 missing FR autoroute signs
Update model to 2.1.1 via OTA
Post-update: FR 110 km/h signs correctly read
```

**Case 55 — LDW Sensitivity Customer Complaint: Too Sensitive**
```
LDW alerts even for minor lane position changes (lane centering)
22 [LDW_Sensitivity DID] → 0x01 (most sensitive — Level 1)
Customer preference: Level 3 (less sensitive)
2E [LDW_Sensitivity DID] 0x03
11 03 → Soft reset
Test: LDW only alerts at clear lane departure, not random centering
```

**Case 56 — Speed Limit DID Verification (22 F4 10)**
```
22 F4 10 → Read current road speed limit (from TSR + map blend)
Response: 62 F4 10 50 00 = 80 km/h (correct for UK 50 mph zone)
Verify cluster display shows 50 mph
Test: limit changes correctly at sign transitions
```

**Case 57 — LKA Steering Actuation Test via 0x2F**
```
2F [LKA_Steer DID] 03 01 → Force small left steer (1° command, short-term adjustment)
Verify: steering wheel moves 1° left
2F [LKA_Steer DID] 00 → returnControlToECU
Important: Only use in stationary vehicle — live road use is dangerous!
```

**Case 58 — ADAS DTC for CAN Bus Off Condition**
```
DTC U0001: CAN Bus Off (High Speed CAN)
CANalyzer log: 1200 bit errors in 3 seconds → bus went off
Root cause: Incorrect termination (120Ω missing on ADAS sub-bus)
2 × 120Ω terminators required; one missing after ECU swap
Install terminator → bus off clears → U0001 heals
```

**Case 59 — HWA Lateral Positioning Error**
```
HWA holds vehicle 0.3m right of lane centre
22 [HWA_LateralOffset DID] → +0.30m (offset from camera lane centre)
22 [Camera_CalStatus DID] → CalRequired
Camera not calibrated after windscreen replacement (same hospital as Case 31)
Calibration → HWA centred correctly
```

**Case 60 — DTC P1F50: ADAS Memory Limit Reached**
```
DTC P1F50: Object List Memory Full
22 [Object_Count DID] → MaxObjects=40, CurrentObjects=40 (at limit)
22 [Object_Overflow_Count DID] → 7 (7 objects dropped since last clear)
Root cause: Roundabout scenario — 40+ vehicles simultaneously detected
SW update increases max object list to 64
Post-update: P1F50 no longer triggered in roundabout test
```

**Case 61 — AEB Night Mode Configuration**
```
22 [AEB_NightMode DID] → NightMode_Active=0x00 (disabled)
Night mode: lower confidence threshold for pedestrian detection
Customer in dark rural area wants this enabled
2E [AEB_NightMode DID] 0x01 → Enable
Retest AEB pedestrian night scenario → detection rate improved
Note: Increases false positive risk — customer informed
```

**Case 62 — Mass Configuration Rollout via UDS Script**
```
60 vehicles need same configuration update (AEB threshold change after NCAP fail)
Automated UDS script:
  For each vehicle:
    10 03 → 27 01/02 → 2E [AEB_Thresh DID] [new value] → 14 FF FF FF → 11 03
  Log: Pass/Fail per vehicle → 58 PASS, 2 FAIL (security timeout on 2 vehicles)
  Retry 2 failures → both pass on retry
  Configuration update complete: 60/60
```

**Case 63 — ADAS: Mirror Memory Freeze Frame Under Water Ingress**
```
19 0F 09 → B2A77 (Internal ECU Humidity Detected) in mirror memory
19 14 → Mirror memory freeze frame: HumidityLevel=87% (spec < 50%)
Condition healed (ECU dried out) but mirror memory captures the peak
Physical inspection: cracked ECU housing seal
Replace ECU, seal housing, apply conformal coating
No further humidity DTCs
```

**Case 64 — ACC Headway Time Setting Via DID**
```
22 [ACC_Headway DID] → Default=0x03 (2.5 seconds — level 3)
Range: 0x01=1.5s Level1, 0x02=2.0s L2, 0x03=2.5s L3, 0x04=3.0s L4, 0x05=3.5s L5
Customer wants Level 4 default on vehicle delivery
2E [ACC_Headway DID] 0x04 → Customer preference written
Verified: ACC maintains 3.0s headway on road test
```

**Case 65 — Negative: Attempting 0x2E in Default Session**
```
Security validation test (TCF-ADAS-2065):
Default session → 2E D0 10 01 → 7F 2E 7F ← serviceNotSupportedInActiveSession
Expected NRC: 7F 2E 7F ← PASS
Also: 2E F1 90 [invalid VIN] → 7F 2E 7F ← also PASS
Confirms: write protection working in default session
```

**Case 66 — ACC: Diagnosis of Sporadic Hard Braking on Highway**
```
22 [ACC_Log DID] → Event at odometer 49,210km: TTC=0.8s, Decel=8.3 m/s²
Normal: TTC threshold 1.5s for max braking
TTC=0.8s → object appeared very late (occluded by spray behind lorry)
AEB response was correct (genuine emergency)
Radar range limited by water spray → documentation updated to note range reduction in heavy rain
No SW change needed
```

**Case 67 — TSR Speed Limit Fusion: Camera vs Map Conflict**
```
22 [TSR_Camera_Limit DID] → 70 km/h (from sign)
22 [TSR_Map_Limit DID] → 50 km/h (map database — outdated)
22 [TSR_Final_Limit DID] → 70 km/h (camera takes precedence — correct behaviour)
22 [TSR_Fusion_Mode DID] → 0x02 (camera-priority mode)
Verify: Map database update resolves conflict
After map OTA update: both sources agree at 70 km/h
```

**Case 68 — ADAS Remote Diagnosis via Telematics**
```
Remote UDS session via TCU DoIP gateway:
Vehicle on public road → TCU provides DoIP tunnel
10 03 → 22 F1 89 → Read SW version remotely
19 02 09 → Read DTCs remotely → C0A55 radar temperature (intermittent)
Send: 14 FF FF FF → Clear remotely
Confirm: 19 02 09 → clean
All performed without vehicle visit — first-time fix rate improved
```

**Case 69 — AEB Sensor Fusion Weight Modification**
```
After NCAP pedestrian night test fail:
22 [Fusion_Weights DID] → Radar=0.70, Camera=0.30
Change: Camera weight increase for pedestrian classification
2E [Fusion_Weights DID] → Radar=0.50, Camera=0.50
Retest NCAP: pedestrian detection rate 94% → PASS
Note: Fusion weights are safety-critical — ASIL D validation required before change
```

**Case 70 — Routine Control: AEB Full Self-Test Sequence**
```
31 01 [AEB_Full_Test RID] → Start full self-test
7F 31 78 × 3 (responsesPending — test running ~3 seconds)
71 01 [RID] 01 [TestResult: 8 bytes]
Result breakdown:
  Byte 1: Radar comms = 01 (PASS)
  Byte 2: Camera comms = 01 (PASS)
  Byte 3: CAN output = 01 (PASS)
  Byte 4: Brake interface = 01 (PASS)
  Byte 5: Reaction time = 01 (< 150ms PASS)
  Byte 6: Sensor alignment = 01 (PASS)
  Byte 7: Confidence calibration = 01 (PASS)
  Byte 8: Overall = 01 (PASS)
Use at EOL and post-service for full AEB system verification
```

---

### Cases 71–85 — BSD / Ultrasonic / Park Assist / Parking Pilot

**Case 71 — BSD DTC: Azimuth Association Fault After Rear Bumper Repaint**
```
19 02 09 → C1B44 (BSD Sensor Physical Disruption)
22 [BSD_Signal_Quality DID] → LR=0.31, RR=0.89 (LR signal quality poor)
Physical: Rear bumper repainted with metallic paint 3× thickness over LR sensor
Paint thickness attenuates radar signal
Recommendation: Radar-transparent bump zone (no metallic paint over sensor)
ECU replacement not needed — paint refinished correctly
```

**Case 72 — Park Assist Camera 360° Individual Camera Calibration**
```
After one side camera replaced:
31 01 [Cam3_Stitch_Cal RID] → Calibrate left side camera stitching
Park vehicle over calibration mat
71 01 [RID] 01 PASS
22 [Stitch_Quality DID] → All seams < 0.5cm misalignment PASS
SVM (Surround View Monitor) top-down view restored correctly
```

**Case 73 — Ultrasonic Self-Test: Crosstalk between Sensors**
```
31 01 [Ultrasonic_Crosstalk RID] → Fire sensors sequentially, measure crosstalk
71 01 [RID] [8 bytes: crosstalk matrix]
Sensor 3 triggering Sensor 4 response = crosstalk level 0x2A (spec < 0x20)
Adjust sensor 3 firing delay +2ms → reduces overlap → crosstalk 0x18 (PASS)
2E [S3_Fire_Delay DID] [2ms encoded] → Write adjustment
```

**Case 74 — Park Assist: Distance Calibration for Non-Standard Vehicle Length**
```
Tow bar attached adds 0.52m to vehicle length
Park assist distance reading incorrect (shows 0.52m shorter than actual)
2E [Vehicle_Length_Ext DID] 0x34 = 52cm → Write trailer/tow bar extension
22 [Rear_Stop_Distance DID] → Now accounts for tow bar
Park assist shows correct distance including tow bar
```

**Case 75 — Cross-Traffic: Pedestrian vs Cyclist Classification**
```
22 [RCTA_Class_DID] → Classification data: Object at 8m, Class=Pedestrian, Speed=4 m/s
4 m/s is fast for pedestrian → could be cyclist
22 [RCTA_Classify_Thresh DID] → Cyclist threshold = 5 m/s (only class as cyclist above 5 m/s)
4 m/s < 5 m/s → correctly classified as pedestrian (fast walking, running)
Verify: cyclist at 6 m/s classified as cyclist → correct
No configuration change needed → algorithm working correctly
```

**Case 76 — Park Assist: Sensor Blocked by Mud Flag**
```
DTC P2A19: Front Sensor 2 Response Rate < 50%
22 [F2_Response_Rate DID] → 23% (spec > 80%)
Physical: Mud packed in sensor 2 aperture
Clean sensor → response rate 94% → P2A19 heals
Self-diagnostic correctly identified blocked sensor
```

**Case 77 — RPA (Remote Parking Assist) Enable via UDS Feature Flag**
```
RPA feature not enabled on delivery vehicle
22 [RPA_Feature DID] → 0x00 (not enabled)
Customer purchases RPA via OTA feature unlock
2E [RPA_Feature DID] 0x01 (after payment verification)
11 03 → Remote parking becomes available on HMI
Note: feature monetisation via UDS 2E write after OTA key provisioning
```

**Case 78 — Trailer Hitch Sensor Calibration**
```
New trailer hitch installed → trailer angle sensor requires zeroing
31 01 [TrailerAngle_Cal RID] → with trailer straight
71 01 [RID] 01 PASS → Zero angle = current position
Test: turn trailer 30° left → 22 [Trailer_Angle DID] = −30° (correct)
Test: 30° right → +30° (correct)
Manoeuvre assist now correctly models trailer geometry
```

**Case 79 — Park Assist: DTC After Vehicle Wash (Pressure Washer Damage)**
```
P2A44: Front Sensor 4 Internal Fault
22 [F4_Internal_Status DID] → Water ingress detected (0x01)
High-pressure wash directly onto sensor
Sensors rated for IPX4 (splash) not IPX6 (jet water)
Replace sensor → clear DTC
Customer advisory: avoid direct jet spray on ultrasonic sensors
```

**Case 80 — APA (Automatic Parking Assist) Abort Investigation**
```
APA aborted mid-manoeuvre. DTC B3A99: Parking Manoeuvre Aborted.
19 04 [B3A99] 01 → Freeze frame:
  AbortReason=0x04 (obstacle appeared during manoeuvre)
  SteeringAngle=−220° (mid reverse)
  Speed=0.8 km/h
Obstacle: child on bicycle entered parking space
APA safety function correctly aborted
No fault — correct behaviour
Inform customer: APA detects close obstacles and aborts if path unsafe
```

**Case 81 — Park Assist Activation Gate: Gear + Speed**
```
Customer: park assist activates at 15 km/h (seems too fast)
22 [PA_Activate_Speed DID] → Max activation speed = 20 km/h
Spec: activates below 20 km/h in R or D-low
Customer wants 10 km/h limit for safety
2E [PA_Activate_Speed DID] 0x0A (10 km/h)
Note: Requires engineering session + security access (safety parameter)
```

**Case 82 — BSD: Night-time Sensitivity Increase**
```
BSD sensitivity lower at night (fewer false positives but misses fast motorcycles)
22 [BSD_Night_Sens DID] → NightAmplification=0x01 (Level 1 of 3)
Regulatory requirement for night sensitivity: Level 2
2E [BSD_Night_Sens DID] 0x02 → Level 2
Retest: motorcycle at 90 km/h from 30m → BSD correctly alerts at night
```

**Case 83 — Park Assist: Sensor Disable for Car Wash**
```
Car wash mode: disable PA sensors to prevent false activation during brushes
2F [PA_Mode DID] 02 → freeze current state (sensors off)
  OR
2E [PA_Carwash_Mode DID] 0x01 → CarWash mode on
Effect: PA sensors silent during wash
After wash: 2F [PA_Mode DID] 00 / 2E [PA_Carwash_Mode DID] 0x00 → normal
```

**Case 84 — Ultrasonic: Zero-Distance False Read**
```
DTC P2A31: Sensor 1 reports 0cm distance continuously
22 [Sensor1_Raw DID] → Distance=0x0000 (stuck at zero)
Physical: Sensor damaged/cracked
Compare: All other sensors read normally
Replace sensor 1 → P2A31 clears
Distance reading returns to normal
```

**Case 85 — HPA (Home Parking Assist) Location Write**
```
HPA learns preferred home parking position
After learning:
22 [HPA_HomePos DID] → Home_X=12.3m, Home_Y=−0.8m, Home_Angle=−3.2°
Written by learning routine via 31/2E combination
If position needs reset:
2E [HPA_HomePos DID] [zeros] → Clear learned position
Then re-learn from scratch: 31 01 [HPA_Learn RID]
```

---

### Cases 86–100 — ADAS Advanced Cases

**Case 86 — DTC U3001 (DoIP Routing Not Active) on ADAS**
```
DoIP diagnostic attempt fails with no response
Physical: Ethernet cable between gateway and ADAS ECU disconnected
UDS over CAN still works (backup path)
22 F1 89 via CAN → works
Ethernet reconnected → DoIP routing activation:
  DoIP header type 0x0005 with logical address → 0x0006 response code 0x10 (activated)
U3001 → heals after routing re-established
```

**Case 87 — Feature Enable: Hands-Free Highway Driving (Level 2 Upgrade)**
```
Software-enabled feature: L2 automation (hands-on required → hands-free on highway)
22 [L2_Feature DID] → 0x00 (disabled)
Customer purchases upgrade
2E [L2_Feature DID] 0x01 (after cryptographic token verified)
11 01 → Reset
Hands detection camera enabled
HDA+ (Highway Driving Assist+) now available on HMI
Monetisation: feature gated by UDS write behind crypto token
```

**Case 88 — Crash Recording Read (Event Data Recorder)**
```
After crash, police request EDR data:
10 03 → 27 01/02 → security level (high security — forensic access)
22 [EDR_Event_Count DID] → 3 events recorded
19 04 [Crash_DTC] 01 → Freeze frames:
  Event 1: Speed=127 km/h, Decel=12g, AEB_Active=0, Time-2s AEB_Alert=1
  → AEB alerted but not activated (speed too high for AEB intervention)
Data exported per EU EDR regulation
```

**Case 89 — Immobiliser Integration with ADAS (Anti-Theft)**
```
ADAS ECU requires VIN match with BCM immobiliser before enabling AEB
22 [ADAS_VIN DID] → VIN: W0L000011T1234567
22 F1 90 on BCM → VIN: W0L000011T1234567 (match)
If mismatch: ADAS locks down with DTC P0A88 (VIN Mismatch — Anti-Tampering)
Protect against stolen ADAS ECU swaps between vehicles
```

**Case 90 — CAN FD Bitrate Validation for ADAS Messages**
```
ADAS ECU upgraded to CAN FD (2 Mbit/s data phase)
22 [CANFD_Config DID] → Nominal=500kbit/s, Data=2000kbit/s
Link Control: 87 01 [2000kbit/s] → 87 03 → Switch to 2 Mbit/s data phase
Verify: ECU responds at new rate
Flash speed: 2MB file in 35 seconds (vs 4 minutes at 500kbit/s)
After flash: 87 01 [500] → 87 03 → return to nominal rate
```

**Case 91 — ADAS ECU Active Diagnostic Session Verification**
```
22 F1 86 → Read activeSession
In extended: Response = 62 F1 86 03 ← extendedDiagnosticSession
In default: Response = 62 F1 86 01 ← defaultSession
In programming: Response = 62 F1 86 02 ← programmingSession
Use this to verify test sequence is in correct session before critical steps
```

**Case 92 — ECU Hardware Version Verification**
```
22 F1 91 → ECU HW Number: ADAS-HW-V3.0
22 F1 93 → Supplier HW Version: 3.0.1
22 F1 95 → Supplier SW Version: 2.14.0
22 F1 8A → Supplier ID: 0x0042 (Bosch)
Cross-check against SOP (Start Of Production) BOM:
All match → correct hardware variant for this production order
```

**Case 93 — AEB Test Event Log Reset**
```
Before customer delivery, clear AEB test event log:
31 01 [AEB_Log_Clear RID] → Clear testing data
71 01 [RID] 01 PASS
22 [AEB_Activation_Count DID] → 0 (cleared)
22 [AEB_TestDrive_Distance DID] → 0 km (cleared)
Ensures delivery vehicle shows no pre-delivery test events to customer
```

**Case 94 — DTC Suppression List Configuration**
```
Some OEMs configure DTC suppression lists (DTCs that are set but not reported to customer)
22 [DTC_Suppress_List DID] → List of suppressed DTC codes
Compare with current regulation: OBD emission DTCs cannot be suppressed
Non-OBD safety DTCs can be temporarily suppressed in production test
EOL: clear suppression list before delivery
31 01 [DTC_Suppress_Clear RID] → Remove all suppressions
```

**Case 95 — ADAS ECU Date/Time Synchronisation**
```
ADAS ECU needs accurate timestamp for freeze frame and event log
22 [ECU_DateTime DID] → 2024-01-15 08:23:01 (wrong — vehicle was sleeping)
2E [ECU_DateTime DID] [current_time_encoded] → Sync to GPS time
11 03 → Soft reset
22 [ECU_DateTime DID] → Correct time
Freeze frames now have accurate timestamps for event investigation
```

**Case 96 — Progressive AEB Braking: Configuration Validation**
```
AEB implements 3-stage braking: warning → partial (0.3g) → full (1.0g)
22 [AEB_Stage1_Decel DID] → 0x03 = 0.3g (correct)
22 [AEB_Stage2_Decel DID] → 0x0A = 1.0g (correct)
22 [AEB_Stage1_TTC DID] → 2.5s trigger for warning
22 [AEB_Stage2_TTC DID] → 1.5s trigger for full brake
Verify all 4 DIDs match homologation document
All match → PASS
```

**Case 97 — Dual-CPU ADAS ECU: Both Core Diagnostics**
```
Modern ADAS ECU has Main CPU + Safety Monitor CPU
22 [Main_CPU_Status DID] → 0xA5 = healthy
22 [Safety_CPU_Status DID] → 0xA5 = safe state healthy
19 02 09 on Main: C0A00 radar temp
19 02 09 on Safety Monitor (separate UDS address 0x7A1) → No DTCs
Both CPU diagnostics independently confirm physical chain healthy
```

**Case 98 — ADAS Software Integrity Self-Check**
```
31 01 [SW_Integrity_RID] → Run SW CRC/hash self-check
7F 31 78 (responsesPending × 2) → ~2 second runtime
71 01 [RID] 01 [Hash: 8 bytes]
Compare returned hash against golden reference hash from build server:
Match → SW integrity confirmed
Mismatch → SW corruption detected → reflash required
Run at every service visit as security check
```

**Case 99 — ADAS ECU Sleep Current Measurement Support**
```
After key off, ADAS ECU should draw < 500μA (sleep current)
Enter sleep quiescent diagnostics:
10 01 → Default session
3E 80 → Suppress tester present (let ECU time out and sleep)
Wait S3 timeout (5s) → ECU drops to Default, then sleep
Measure current consumption externally: 380μA (within 500μA spec)
PASS: Sleep current within specification
```

**Case 100 — Full ADAS Build Verification: Automated 10-Step Check**
```
Automated EOL ADAS verification script:
Step 1:  22 F1 89 → SW version matches build target ✓
Step 2:  22 F1 90 → VIN matches vehicle build record ✓
Step 3:  22 F1 8C → ECU serial matches tray manifest ✓
Step 4:  19 02 09 → Zero confirmed DTCs ✓
Step 5:  22 [AEB_Enable DID] → 0x01 enabled ✓
Step 6:  22 [ACC_Enable DID] → 0x01 enabled ✓
Step 7:  22 [LKA_Enable DID] → 0x01 enabled ✓
Step 8:  22 [Market_Code DID] → correct market ✓
Step 9:  31 01 [AEB_Full_Test RID] → Self-test PASS ✓
Step 10: 22 F1 86 → Session = Default (01) at end ✓
All 10 steps PASS → ADAS Build Verified → Print QC label
Automated script runs in < 45 seconds per vehicle
```

---
*File: 02_adas_star_scenarios.md | 100 UDS ADAS Interview Scenarios | April 2026*
