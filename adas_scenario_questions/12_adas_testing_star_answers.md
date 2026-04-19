# ADAS Testing — STAR Format Interview Answers

> STAR = **S**ituation → **T**ask → **A**ction → **R**esult
> Use these for behavioural and competency-based questions.
> Adapt the ECU/project names to your actual experience.

---

## 1. ACC — Adaptive Cruise Control

### "Tell me about a time you tested ACC and found a critical bug."

**S — Situation**
> During ADAS integration testing on a BYD Sealion 7 project, ACC was in its final
> validation phase before SOP. The feature had passed all component-level tests on HIL,
> but full vehicle testing was still pending. I was responsible for CAN-level signal
> validation using CANoe.

**T — Task**
> My task was to verify that ACC correctly deactivates and raises a fault when the forward
> radar signal is lost — a safety-critical requirement under ISO 26262 ASIL-B. The
> requirement stated: "ACC shall deactivate within 100ms of radar message timeout and
> log a U0401 DTC."

**A — Action**
> I wrote a CAPL script that sent normal radar target frames (0x300) at 20ms cycle for
> 5 seconds, then abruptly stopped, simulating a radar communication failure. I monitored
> the ACC status output message (0x502) for the fault bit and used the CANoe Diagnostic
> Console to check for U0401 after each run. On the third test run, I noticed the ACC
> fault bit was set correctly but the DTC was not logged — the ECU transition to
> session-less state was clearing the DTC automatically before it could be read.

**CAPL Script used in the Action:**

```capl
/*
 * ACC STAR-1: Radar timeout + DTC persistence check
 * Sends radar frames for 5s, then stops.
 * Monitors: ACC fault flag (0x502) AND reads DTC via UDS after timeout.
 */
variables {
  message 0x300 msg_Radar;
  message 0x7E0 udsReq;          // DTC read request (raw UDS)
  msTimer tRadarCycle;
  msTimer tStopRadar;
  msTimer tReadDTC;
  int     radarActive = 1;
  dword   tFaultSet   = 0;       // timestamp when fault flag seen
}

on start {
  msg_Radar.dlc = 8;
  msg_Radar.byte(0) = 0x0F; msg_Radar.byte(1) = 0xA0;  // 40m target
  msg_Radar.byte(2) = 0x00; msg_Radar.byte(3) = 0x00;  // RelSpeed = 0
  setTimer(tRadarCycle, 20);
  setTimer(tStopRadar,  5000);   // kill radar at 5 s
  write("[ACC-STAR1] Phase 1: Normal radar @ 20ms cycle");
}

on timer tRadarCycle {
  if (radarActive) output(msg_Radar);
  setTimer(tRadarCycle, 20);
}

on timer tStopRadar {
  radarActive = 0;
  write("[ACC-STAR1] Phase 2: RADAR STOPPED — timeout injected @ t=%d ms", timeNow()/100000);
  setTimer(tReadDTC, 200);       // read DTC 200ms after timeout
}

on timer tReadDTC {
  // UDS: ReadDTCInformation — reportDTCByStatusMask 0x08 (confirmed)
  udsReq.dlc = 8;
  udsReq.byte(0) = 0x03;
  udsReq.byte(1) = 0x19;
  udsReq.byte(2) = 0x02;
  udsReq.byte(3) = 0x08;
  output(udsReq);
  write("[ACC-STAR1] UDS DTC read sent — checking U0401 persistence...");
}

on message 0x502 {    // ACC status
  if ((this.byte(0) & 0x04) && tFaultSet == 0) {
    tFaultSet = timeNow() / 100000;   // ms
    write("[ACC-STAR1] ACC fault flag SET at t=%d ms", tFaultSet);
  }
}

on message 0x7E8 {    // UDS response
  if (this.byte(1) == 0x59) {         // positive ReadDTC response
    int numDTCs = (this.dlc - 4) / 4;
    if (numDTCs > 0) {
      write("[ACC-STAR1] PASS: %d DTC(s) found — U0401 persisted ✓", numDTCs);
    } else {
      write("[ACC-STAR1] FAIL: 0 DTCs — DTC was cleared before NvM write! (BUG)");
    }
  }
}
```

**R — Result**
> I raised a P2 defect in JIRA with full CAN log, CAPL script, and timestamp analysis
> showing the DTC was being cleared within 80ms of being set. The root cause was a
> missing NvM write call in the diagnostic session transition handler. The SW team
> patched it in the next sprint. The fix was re-verified using the same CAPL script — DTC
> now persists correctly across sessions. This prevented a potential recall issue post-SOP.

---

## 2. LKA — Lane Keep Assist

### "Describe a situation where you had to validate a safety requirement for LKA."

**S — Situation**
> On a passenger vehicle project, the LKA feature had a safety requirement that it must
> NOT apply steering torque when the driver activates the turn signal. This was a known
> driver-override requirement from ISO 22178 and defined in the DOORS trace as
> REQ-LKA-007. During regression testing after a SW update, I was assigned to re-verify
> this requirement.

**T — Task**
> Re-verify that LKA steering torque output drops to zero within one control cycle
> (20ms) whenever TurnSignal is active — for both left and right signals, both during
> active correction and idle monitoring.

**A — Action**
> I created four test cases in CANoe using CAPL signal injection:
> 1. LKA actively correcting left drift → left turn signal injected → torque monitored
> 2. LKA actively correcting right drift → right turn signal injected → torque monitored
> 3. LKA idle (centered) → turn signal → ensure no latent torque spike
> 4. Turn signal removed mid-drift → torque resumes correctly
>
> For each, I captured the exact timestamp of TurnSignal rising edge vs
> LKA_TorqueRequest falling edge in the CANoe Graphics window and measured the delta.
> On test case 2, I found a 60ms delay — three control cycles — before torque dropped.

**CAPL Script used in the Action:**

```capl
/*
 * LKA STAR-2: Turn signal suppression timing test
 * Injects lane drift then activates turn signal.
 * Measures latency between TurnSignal rising edge and LKA_TorqueRequest = 0.
 * REQ-LKA-007: torque must drop within 20ms (1 control cycle).
 */
variables {
  message 0x320 msg_Lane;
  message 0x220 msg_TurnSig;
  msTimer tCycle;
  msTimer tActivateTurn;
  dword   tTurnActivated = 0;
  int     torqueWasActive = 0;
}

on start {
  // Simulate active left drift — LKA should be correcting
  msg_Lane.dlc = 8;
  msg_Lane.byte(0) = 0xFF; msg_Lane.byte(1) = 0x38;  // offset = -200mm (signed)
  msg_Lane.byte(2) = 0xFF; msg_Lane.byte(3) = 0x9C;  // angle = -100
  msg_Lane.byte(4) = 2;                               // LaneQuality = high

  msg_TurnSig.dlc = 8;
  msg_TurnSig.byte(0) = 0x00;   // no turn signal yet

  setTimer(tCycle, 20);
  setTimer(tActivateTurn, 3000);   // activate turn signal at 3s
  write("[LKA-STAR2] Phase 1: Left drift active — monitoring torque...");
}

on timer tCycle {
  output(msg_Lane);
  output(msg_TurnSig);
  setTimer(tCycle, 20);
}

on timer tActivateTurn {
  msg_TurnSig.byte(0) = 0x02;   // RIGHT turn signal (test case 2)
  tTurnActivated = timeNow() / 100000;   // ms
  write("[LKA-STAR2] Phase 2: RIGHT turn signal activated @ t=%d ms", tTurnActivated);
}

on message 0x510 {   // LKA torque output
  int torque = (this.byte(0) << 8) | this.byte(1);

  if (torque > 0) {
    torqueWasActive = 1;    // confirm LKA was correcting before test
  }

  // Check torque drop after turn signal
  if (torqueWasActive && torque == 0 && tTurnActivated > 0) {
    dword latency = (timeNow() / 100000) - tTurnActivated;
    if (latency <= 20) {
      write("[LKA-STAR2] PASS: Torque = 0 in %d ms (≤ 20ms) ✓", latency);
    } else {
      write("[LKA-STAR2] FAIL: Torque = 0 after %d ms — EXCEEDS 20ms! (BUG)", latency);
    }
    tTurnActivated = 0;   // reset to avoid repeated logging
    torqueWasActive = 0;
  }
}
```

**R — Result**
> Filed a P1 defect (safety-critical regression) with timestamp analysis, CAN trace,
> and CAPL script attached. The delay was traced to a signal debounce filter that had
> been incorrectly applied to TurnSignal in the new SW build. The filter was removed,
> re-tested — torque now drops within 5ms (< 1 cycle). Test case closed as PASS.
> Requirement REQ-LKA-007 re-verified and signed off in DOORS.

---

## 3. BSD — Blind Spot Detection

### "Give me an example of a time you tested a warning system that involved multiple ECU interactions."

**S — Situation**
> BSD warning on a mid-range SUV project required coordination between three ECUs:
> the rear-corner radar ECU (sends target data), the ADAS ECU (processes and decides),
> and the cluster ECU (displays mirror warning and plays chime). During system integration
> testing, it was reported that the chime was playing even when no target was actually
> present in the blind spot — a false positive that could erode driver trust.

**T — Task**
> Isolate which ECU was responsible for the false chime — was it incorrect target
> detection by the radar ECU, incorrect processing by the ADAS ECU, or incorrect
> triggering logic in the cluster ECU?

**A — Action**
> I took a three-layer approach using CANoe:
> 1. **Radar ECU isolation**: Captured BSD_Left_Target signal (0x330) in Trace — confirmed
>    it was correctly showing 0 (no target) during the false chime events.
> 2. **ADAS ECU isolation**: Monitored BSD_WarnLeft output (0x520). Found it was pulsing
>    0→1→0 briefly every ~2 seconds even with no target — this was the source.
> 3. **Root cause**: Used CANoe Statistics to check message timing. BSD_Left_Target
>    message from radar ECU had a 200ms gap (timeout) under high bus load. The ADAS ECU
>    treated a missing message as "unknown" and momentarily set the warning flag while
>    re-querying — the spec said it should hold last-known state, not trigger warning.

**R — Result**
> Root cause confirmed: missing timeout handling in ADAS ECU — it should hold the last
> valid target state for 500ms before flagging "no data." Raised P2 defect with CAN
> bus load analysis, timing screenshots, and a CAPL script that reproduced the issue
> by injecting a 200ms gap in BSD radar messages. Fix implemented and verified — chime
> now requires 3 consecutive valid target frames before activating, which eliminated
> the false positive completely.

**CAPL Script used in the Action:**

```capl
/*
 * BSD STAR-3: 200ms message gap injection — false chime reproduction
 * Sends BSD_Left_Target = 0 (no target) normally, but introduces
 * a 200ms dropout to simulate high bus load gap.
 * Expected: BSD_WarnLeft should NOT pulse during the gap (bug = it does).
 */
variables {
  message 0x330 msg_BSD;
  msTimer tBSDCycle;
  msTimer tInjectGap;
  msTimer tResumeAfterGap;
  int     bsdSending = 1;
  int     gapInjected = 0;
}

on start {
  msg_BSD.dlc = 8;
  msg_BSD.byte(0) = 0x00;   // BSD_Left_Target = 0 (no target)
  msg_BSD.byte(1) = 0x00;
  msg_BSD.byte(2) = 0x00;
  msg_BSD.byte(3) = 0x00;
  setTimer(tBSDCycle, 20);
  setTimer(tInjectGap, 3000);   // inject gap at 3s
  write("[BSD-STAR3] Phase 1: Normal BSD frames — no target present");
}

on timer tBSDCycle {
  if (bsdSending) output(msg_BSD);
  setTimer(tBSDCycle, 20);
}

on timer tInjectGap {
  bsdSending = 0;   // STOP sending — simulates 200ms bus dropout
  gapInjected = 1;
  write("[BSD-STAR3] Phase 2: GAP INJECTED — 200ms silence on 0x330");
  setTimer(tResumeAfterGap, 200);
}

on timer tResumeAfterGap {
  bsdSending = 1;
  write("[BSD-STAR3] Phase 3: 0x330 resumed — monitoring for spurious warning...");
}

on message 0x520 {   // BSD warning output
  byte warnLeft = this.byte(0) & 0x01;
  if (warnLeft && gapInjected) {
    write("[BSD-STAR3] BUG REPRODUCED: BSD_WarnLeft = 1 during/after gap — no target! (P2 defect)");
  }
}

on message 0x521 {   // Chime
  if (this.byte(0) & 0x01 && gapInjected) {
    write("[BSD-STAR3] BUG REPRODUCED: FALSE CHIME triggered — no target present! ✓");
  }
}
```

---

## 4. DMS — Driver Monitoring System

### "Tell me about a time you had to test a feature where the test environment was difficult to set up."

**S — Situation**
> DMS relies on infrared camera data to detect drowsiness. On a real vehicle, you need
> a human driver with controlled eye closure — impossible to repeat precisely. On HIL,
> the camera data would need a real IR camera pointed at a face, which was not available
> in our lab. The test needed to be repeatable, automated, and independent of human
> subjects for regression testing.

**T — Task**
> Design an automated DMS test that could be run in CANoe without a camera, without a
> human driver, and produce consistent, repeatable results — covering the full warning
> escalation from Level 1 (visual) to Level 3 (haptic + brake).

**A — Action**
> I worked with the DMS ECU team to understand the CAN interface: the camera processes
> the IR image internally and sends pre-processed parameters (EyeClosure%, GazeDirection,
> HeadPose_Yaw) over CAN (0x340). I wrote a CAPL script that simulated these parameters
> directly — bypassing the camera hardware entirely. The script ramped `DMS_EyeClosure`
> from 10% to 95% over 10 seconds in 5% steps every 500ms, while keeping FaceDetected=1
> and GazeDirection=0 (forward head, eyes closing). I added assertion handlers on
> DMS_Warning_Level (0x530) to auto-log the exact eye closure percentage at which each
> warning level was triggered. I ran this 10 times per SW build for regression.

**R — Result**
> The automated script replaced 3 hours of manual testing per build cycle with a
> 12-minute automated run. It caught two regressions: one where the Level 2 threshold
> shifted from 70% to 55% eye closure (too sensitive — false alarms while blinking),
> and one where Level 3 never triggered due to a timer reset bug. Both were caught
> before vehicle testing. The script was adopted by the team as the standard DMS
> regression suite.

**CAPL Script used in the Action:**

```capl
/*
 * DMS STAR-4: Automated drowsiness regression script
 * Ramps DMS_EyeClosure from 10% → 95% in 5% steps every 500ms.
 * Logs the exact closure % at which each warning level triggers.
 * Run 10× per build for regression — no human subject needed.
 */
variables {
  message 0x340 msg_DMS;
  msTimer tDMSCycle;
  msTimer tRamp;
  int eyeClosure = 10;
  int lastWarnLevel = 0;
  int runCount = 0;
  int warnL1_closure = -1;
  int warnL2_closure = -1;
  int warnL3_closure = -1;
}

void resetTest() {
  eyeClosure   = 10;
  lastWarnLevel = 0;
  warnL1_closure = -1;
  warnL2_closure = -1;
  warnL3_closure = -1;
  runCount++;
  write("[DMS-STAR4] === Run %d started ===", runCount);
}

on start {
  msg_DMS.dlc = 8;
  msg_DMS.byte(0) = 0x00;   // GazeDirection = forward
  msg_DMS.byte(1) = 0x00;   // HeadPose_Yaw  = 0
  msg_DMS.byte(2) = eyeClosure;
  msg_DMS.byte(3) = 0x01;   // FaceDetected = 1
  setTimer(tDMSCycle, 20);
  resetTest();
  setTimer(tRamp, 500);
}

on timer tDMSCycle {
  msg_DMS.byte(2) = eyeClosure;
  output(msg_DMS);
  setTimer(tDMSCycle, 20);
}

on timer tRamp {
  eyeClosure += 5;
  if (eyeClosure > 95) eyeClosure = 95;
  write("[DMS-STAR4] EyeClosure ramp → %d%%", eyeClosure);
  if (eyeClosure < 95) setTimer(tRamp, 500);
  else write("[DMS-STAR4] Max closure reached — check warning thresholds above");
}

on message 0x530 {   // DMS warning level
  byte warnLevel = this.byte(0);
  if (warnLevel != lastWarnLevel) {
    write("[DMS-STAR4] Warning LEVEL CHANGE: %d → %d at EyeClosure = %d%%",
          lastWarnLevel, warnLevel, eyeClosure);

    if (warnLevel == 1 && warnL1_closure < 0) {
      warnL1_closure = eyeClosure;
      // REQ: Level 1 at 40% — check
      write("[DMS-STAR4] L1 threshold = %d%%  Expected ≈ 40%%  → %s",
            warnL1_closure, (warnL1_closure <= 45) ? "PASS ✓" : "FAIL — too early/late!");
    }
    if (warnLevel == 2 && warnL2_closure < 0) {
      warnL2_closure = eyeClosure;
      write("[DMS-STAR4] L2 threshold = %d%%  Expected ≈ 70%%  → %s",
            warnL2_closure, (warnL2_closure <= 75) ? "PASS ✓" : "FAIL!");
    }
    if (warnLevel == 3 && warnL3_closure < 0) {
      warnL3_closure = eyeClosure;
      write("[DMS-STAR4] L3 threshold = %d%%  Expected ≈ 90%%  → %s",
            warnL3_closure, (warnL3_closure <= 95) ? "PASS ✓" : "FAIL!");
    }
    lastWarnLevel = warnLevel;
  }
}
```

---

## 5. APS — Automatic Parking System

### "Describe a time you found a bug during parking system testing that was hard to reproduce."

**S — Situation**
> During APS validation on a BYD crossover project, the test team occasionally reported
> that APS aborted mid-maneuver with no obstacle present and no DTC logged. It happened
> roughly 1 in 20 test runs and only during reverse parallel parking — never during
> perpendicular parking. No one had been able to reliably reproduce it.

**T — Task**
> Reproduce the intermittent APS abort, identify the root cause, and provide a reliable
> reproduction script so the SW team could debug it.

**A — Action**
> I started by analysing .blf logs from the failed runs. Using CANoe's post-processing
> tools, I filtered for APS_Status transitions and searched for the 60 seconds before
> each abort. I noticed a pattern: the abort always coincided with a brief 40ms dropout
> on the USS_Side_R message (0x351) during the final steering correction phase. The
> dropout was caused by CAN bus overload from a concurrent OBD2 diagnostic poll that
> the test team ran in parallel.
> I wrote a CAPL script to reproduce it precisely: start APS maneuver, at the 8-second
> mark (matching the typical timing of the final correction) inject a 50ms gap in 0x351
> by suspending its output for one timer cycle. This reproduced the abort 100% of the time.

**R — Result**
> Root cause: APS ECU treated a single-cycle USS timeout as a sensor fault and aborted
> — per spec, it should tolerate up to 3 consecutive missing frames before aborting.
> I documented the reproduction CAPL script, the CAN log analysis, and the spec
> reference in JIRA. SW team patched the timeout tolerance from 1 to 3 frames. Verified
> with the same script — APS now tolerates the 50ms gap and completes the maneuver
> successfully. Issue closed as resolved.

**CAPL Script used in the Action:**

```capl
/*
 * APS STAR-5: USS_Side_R 50ms gap reproduction script
 * Simulates normal APS reverse maneuver, then injects a 50ms gap
 * in USS_Side_R (0x351) at the 8-second mark.
 * Bug: APS aborts on a single missed USS frame.
 * Expected after fix: APS continues through 3 missed frames.
 */
variables {
  message 0x351 msg_USS_Side;
  message 0x350 msg_USS_Front_Rear;
  msTimer tUSSCycle;
  msTimer tInjectGap;
  msTimer tResumeUSS;
  int     ussSideActive = 1;
  int     gapStart_ms   = 0;
}

on start {
  // USS all clear — parking space confirmed, maneuver ongoing
  msg_USS_Side.dlc = 8;
  msg_USS_Side.byte(2) = 0x01; msg_USS_Side.byte(3) = 0x90;  // 400cm clear
  msg_USS_Side.byte(0) = 0x01; msg_USS_Side.byte(1) = 0x90;

  msg_USS_Front_Rear.dlc = 8;
  msg_USS_Front_Rear.byte(0) = 0xC8;  // Front-L: 200cm
  msg_USS_Front_Rear.byte(1) = 0xC8;  // Front-R: 200cm
  msg_USS_Front_Rear.byte(2) = 0x64;  // Rear-L:  100cm
  msg_USS_Front_Rear.byte(3) = 0x64;  // Rear-R:  100cm

  setTimer(tUSSCycle,  20);
  setTimer(tInjectGap, 8000);   // gap at 8s — matches final correction phase
  write("[APS-STAR5] Phase 1: Normal APS maneuver in progress...");
}

on timer tUSSCycle {
  output(msg_USS_Front_Rear);
  if (ussSideActive) output(msg_USS_Side);
  setTimer(tUSSCycle, 20);
}

on timer tInjectGap {
  ussSideActive = 0;
  gapStart_ms   = timeNow() / 100000;
  write("[APS-STAR5] Phase 2: USS_Side_R GAP injected — 50ms silence");
  setTimer(tResumeUSS, 50);    // 50ms gap = 2.5 missed frames @ 20ms cycle
}

on timer tResumeUSS {
  ussSideActive = 1;
  write("[APS-STAR5] Phase 3: USS_Side_R resumed after %d ms gap",
        (timeNow() / 100000) - gapStart_ms);
}

on message 0x541 {   // APS status
  byte apsStatus = this.byte(0);
  if (apsStatus == 4) {
    write("[APS-STAR5] BUG REPRODUCED: APS ABORTED (status=4) after USS gap! (P2 defect)");
  } else if (apsStatus == 3) {
    write("[APS-STAR5] PASS: APS COMPLETED successfully despite USS gap ✓");
  }
}
```

---

## 6. PCW — Pedestrian Collision Warning / AEB-P

### "Tell me about your involvement in safety testing for an AEB feature."

**S — Situation**
> AEB for pedestrians (AEB-P) on a hatchback project was undergoing pre-SOP safety
> validation. The feature had an ISO 22737 reference and required AEB-P to activate
> within 150ms of a pedestrian entering the critical zone (< 8m, in-path). I was
> responsible for ECU-level signal validation — the HIL team handled the full-speed
> vehicle model testing.

**T — Task**
> Verify the AEB-P activation latency requirement (<150ms from pedestrian crossing the
> 8m threshold to AEB_P_Active = 1) for 5 speed setpoints: 20, 30, 40, 50, 60 km/h.

**A — Action**
> I developed a CAPL script that:
> 1. Set VehicleSpeed to the target setpoint
> 2. Injected a pedestrian at 10m (outside threshold) and held for 2 seconds
> 3. At t=2s, stepped distance to 750cm (7.5m — inside 8m threshold) in one frame
> 4. Recorded the timestamp of that step (tTrigger)
> 5. In the `on message 0x551` handler (AEB_P_Active), recorded tActivation
> 6. Calculated latency = tActivation - tTrigger and logged PASS/FAIL vs 150ms limit
>
> I ran 10 iterations per speed setpoint (50 runs total), logging min/max/average latency.
> At 60 km/h I found an average latency of 142ms — inside the limit but with a max spike
> of 178ms (FAIL). The spike correlated with a specific CAN bus load condition.

**R — Result**
> Reported the latency spike as a P1 defect with statistical data (10-run latency chart),
> CAN bus load correlation, and the reproduction script. The ADAS ECU team identified
> a priority inversion in the real-time task scheduler that delayed the AEB decision task
> under high bus load. Task priority was elevated in the next build — maximum latency
> dropped to 128ms across all 50 runs. Requirement verified and closed. This finding
> was also escalated to the HIL team to add bus load as a test parameter in their
> scenario matrix.

**CAPL Script used in the Action:**

```capl
/*
 * PCW STAR-6: AEB-P latency measurement — 10 iterations per speed
 * Injects pedestrian at 10m, steps to 7.5m (inside 8m threshold).
 * Measures exact latency: threshold crossing → AEB_P_Active.
 * REQ: latency < 150ms across all iterations.
 */
variables {
  message 0x360 msg_Ped;
  message 0x200 msg_Speed;
  msTimer tCycle;
  msTimer tStepDistance;   // step from 10m → 7.5m
  msTimer tNextRun;

  dword tTrigger    = 0;
  int   iteration   = 0;
  int   totalRuns   = 10;
  int   speedKmh    = 60;   // change per setpoint: 20/30/40/50/60
  int   passCount   = 0;
  int   failCount   = 0;
  int   maxLatency  = 0;
  int   minLatency  = 9999;
  int   pedInjected = 0;
}

void startRun() {
  iteration++;
  pedInjected = 0;
  tTrigger    = 0;

  // Speed: speedKmh * 100 (factor 0.01)
  msg_Speed.dlc = 8;
  msg_Speed.byte(0) = (speedKmh * 100) >> 8;
  msg_Speed.byte(1) = (speedKmh * 100) & 0xFF;

  // Pedestrian at 10m, in-path
  msg_Ped.dlc = 8;
  msg_Ped.byte(0) = 0x01;           // ClassID = pedestrian
  msg_Ped.byte(1) = 0x03; msg_Ped.byte(2) = 0xE8;  // 1000cm = 10m
  msg_Ped.byte(3) = 0x00; msg_Ped.byte(4) = 0x00;  // LateralOffset = 0
  msg_Ped.byte(5) = ((-speedKmh * 278) >> 8) & 0xFF;   // RelSpeed ≈ -ego speed in cm/s
  msg_Ped.byte(6) =  (-speedKmh * 278)       & 0xFF;

  setTimer(tStepDistance, 2000);    // step to 7.5m after 2s
  write("[PCW-STAR6] Run %d/%d @ %d km/h — pedestrian at 10m",
        iteration, totalRuns, speedKmh);
}

on start {
  setTimer(tCycle, 20);
  startRun();
}

on timer tCycle {
  output(msg_Speed);
  output(msg_Ped);
  setTimer(tCycle, 20);
}

on timer tStepDistance {
  // Step to 7.5m — crosses 8m AEB-P threshold
  msg_Ped.byte(1) = 0x02; msg_Ped.byte(2) = 0xEE;  // 750cm = 7.5m
  tTrigger    = timeNow() / 100000;  // ms
  pedInjected = 1;
  write("[PCW-STAR6] Run %d: distance stepped to 7.5m @ %d ms", iteration, tTrigger);
}

on message 0x551 {   // AEB-P active
  if ((this.byte(0) & 0x01) && pedInjected && tTrigger > 0) {
    dword latency = (timeNow() / 100000) - tTrigger;
    if (latency > maxLatency) maxLatency = latency;
    if (latency < minLatency) minLatency = latency;

    if (latency < 150) {
      passCount++;
      write("[PCW-STAR6] Run %d: PASS — latency = %d ms ✓", iteration, latency);
    } else {
      failCount++;
      write("[PCW-STAR6] Run %d: FAIL — latency = %d ms > 150ms! (BUG)", iteration, latency);
    }
    pedInjected = 0;
    tTrigger    = 0;
    if (iteration < totalRuns) setTimer(tNextRun, 1000);
    else write("[PCW-STAR6] === SUMMARY: PASS=%d FAIL=%d | Min=%dms Max=%dms ===",
               passCount, failCount, minLatency, maxLatency);
  }
}

on timer tNextRun { startRun(); }
```

---

## 7. General ADAS — Cross-Feature Scenarios

### "Tell me about a time you had to coordinate with multiple teams during ADAS testing."

**S — Situation**
> During system-level integration of ACC + AEB + LKA on a BYD Sealion 7 platform, a new
> bug was reported: when ACC was actively braking AND LKA was simultaneously applying
> steering correction, the vehicle responded with an unexpected CAN message flood that
> caused 200ms latency spikes across the ADAS bus. This was discovered during
> combined-feature testing, which had started only that week.

**T — Task**
> Identify which feature or ECU was causing the message flood, reproduce it reliably,
> and coordinate with the ACC, LKA, and gateway ECU teams to resolve it before
> the combined-feature integration milestone deadline (2 weeks away).

**A — Action**
> I set up a CANoe environment with three simultaneous signal injection streams:
> - ACC active: RadarTarget at 15m, ego speed 80 km/h (gentle braking scenario)
> - LKA active: Lane drift -200mm offset, torque correction active
> - Gateway monitoring: bus statistics window tracking message count per 100ms window
>
> I found the flood originated from the gateway ECU, which was re-routing ACC brake
> requests AND LKA torque requests to the chassis domain at the same instant, causing
> a retransmission storm due to a routing table conflict. I captured the exact message
> sequence in a .blf file and shared it with the gateway team with timestamps highlighted.
> I also created a simplified CAPL reproduction script (< 30 lines) so any team member
> could reproduce it without the full simulation setup.

**CAPL Script used in the Action:**

```capl
/*
 * CROSS-FEATURE STAR-7: ACC braking + LKA correction simultaneous injection
 * Reproduces the CAN message flood / gateway retransmission storm.
 * Monitors bus message count per 100ms window — spike > 50 msg/100ms = anomaly.
 */
variables {
  message 0x300 msg_Radar;      // ACC: radar target
  message 0x320 msg_Lane;       // LKA: lane offset
  message 0x200 msg_Speed;      // ego vehicle speed
  msTimer tCycle;
  msTimer tMonitorWindow;
  int msgCountWindow = 0;       // messages seen in last 100ms
  int maxMsgCount    = 0;
}

on start {
  // Speed: 80 km/h
  msg_Speed.dlc = 8;
  msg_Speed.byte(0) = 0x1F; msg_Speed.byte(1) = 0x40;  // 8000 = 80.00 km/h

  // ACC: lead vehicle at 15m — gentle braking zone
  msg_Radar.dlc = 8;
  msg_Radar.byte(0) = 0x05; msg_Radar.byte(1) = 0xDC;  // 1500cm = 15m
  msg_Radar.byte(2) = 0x00; msg_Radar.byte(3) = 0x00;

  // LKA: active left drift -200mm
  msg_Lane.dlc = 8;
  msg_Lane.byte(0) = 0xFF; msg_Lane.byte(1) = 0x38;    // -200mm
  msg_Lane.byte(2) = 0xFF; msg_Lane.byte(3) = 0x9C;
  msg_Lane.byte(4) = 2;                                 // LaneQuality high

  setTimer(tCycle, 20);
  setTimer(tMonitorWindow, 100);
  write("[CROSS-STAR7] ACC + LKA simultaneous injection started");
}

on timer tCycle {
  output(msg_Speed);
  output(msg_Radar);
  output(msg_Lane);
  setTimer(tCycle, 20);
}

// Count ALL CAN messages to detect the gateway retransmission storm
on message * {
  msgCountWindow++;
}

on timer tMonitorWindow {
  if (msgCountWindow > maxMsgCount) maxMsgCount = msgCountWindow;
  if (msgCountWindow > 50) {
    write("[CROSS-STAR7] BUS FLOOD DETECTED: %d messages in 100ms window! (norm ≈ 15)",
          msgCountWindow);
  } else {
    write("[CROSS-STAR7] Bus load normal: %d msg/100ms", msgCountWindow);
  }
  msgCountWindow = 0;
  setTimer(tMonitorWindow, 100);
}

on stopMeasurement {
  write("[CROSS-STAR7] Peak bus message count: %d/100ms", maxMsgCount);
}
```

**R — Result**
> Gateway team fixed the routing table conflict within 3 days using the reproduction
> script I provided. I re-ran the combined injection test — bus load returned to normal
> (<30% utilisation), latency spikes eliminated. The integration milestone was met on
> time. Post-incident, I proposed that combined-feature CAN bus load tests be added to
> the standard regression suite — this was approved and implemented for the next project.

---

### "Give an example of when you improved a testing process."

**S — Situation**
> On a previous project, ADAS regression testing was entirely manual. After each SW
> build, engineers would open CANoe, manually change signal values in the Graphics
> panel, observe the output, and write pass/fail in an Excel sheet. Each full regression
> cycle took 3 days for 6 features. With biweekly SW builds, the team was permanently
> behind.

**T — Task**
> Automate the ADAS regression test suite so that results could be generated within
> one working day per build, with consistent pass/fail criteria and no manual signal
> editing.

**A — Action**
> I built a library of CAPL test scripts, one per feature (ACC, LKA, BSD, DMS, APS, PCW),
> each covering the 3–5 most critical test cases per feature. Each script:
> - Injected signals automatically from `on start`
> - Evaluated pass/fail using `on message` handlers with threshold comparisons
> - Wrote results to a structured log file (PASS/FAIL with signal values and timestamps)
> - Ran in sequence using CANoe's test module framework (vTESTstudio-compatible)
>
> I documented a standard header template so new scripts could be added in under 1 hour.

**CAPL Script used in the Action — Regression Framework Template:**

```capl
/*
 * ADAS REGRESSION FRAMEWORK — Standard script header template
 * Each feature script follows this structure.
 * Results auto-written to Write window (captured by CANoe logging).
 *
 * Usage: Copy this template, fill in the signals and thresholds.
 *        Add to CANoe test module → run in sequence after each SW build.
 */
variables {
  // ── Configuration (edit per feature) ──────────────────────────
  char   FEATURE_NAME[32] = "ACC";       // change: LKA / BSD / DMS / APS / PCW
  char   TC_ID[16]        = "TC-ACC-01";
  int    PASS_THRESHOLD   = 100;         // e.g. latency ms, torque Nm, etc.

  // ── Runtime tracking ──────────────────────────────────────────
  int    passCount  = 0;
  int    failCount  = 0;
  int    testActive = 0;

  // ── Inject messages (fill in per feature) ─────────────────────
  message 0x300 msg_Stimulus;   // <- change to relevant message ID
  msTimer tRunCycle;
  msTimer tEndTest;
}

/* ── Test start ─────────────────────────────────────────────── */
on start {
  write("=== [%s] %s STARTED ===", FEATURE_NAME, TC_ID);

  // Setup stimulus
  msg_Stimulus.dlc = 8;
  msg_Stimulus.byte(0) = 0x0F;   // <- fill in test values
  msg_Stimulus.byte(1) = 0xA0;

  testActive = 1;
  setTimer(tRunCycle, 20);
  setTimer(tEndTest, 10000);     // test duration: 10 seconds
}

/* ── Stimulus cycle ─────────────────────────────────────────── */
on timer tRunCycle {
  if (testActive) output(msg_Stimulus);
  setTimer(tRunCycle, 20);
}

/* ── Response evaluation (fill in per feature) ─────────────── */
on message 0x502 {   // <- change to ECU output message
  int value = this.byte(0);    // <- change to relevant byte/signal

  if (value <= PASS_THRESHOLD) {
    passCount++;
  } else {
    failCount++;
    write("[%s] FAIL at t=%d ms — value=%d > threshold=%d",
          TC_ID, timeNow()/100000, value, PASS_THRESHOLD);
  }
}

/* ── Test end ───────────────────────────────────────────────── */
on timer tEndTest {
  testActive = 0;
  write("=== [%s] %s RESULT: PASS=%d FAIL=%d → %s ===",
        FEATURE_NAME, TC_ID,
        passCount, failCount,
        (failCount == 0) ? "OVERALL PASS ✓" : "OVERALL FAIL ✗");
}

on stopMeasurement {
  write("[%s] Measurement stopped. Final: PASS=%d FAIL=%d",
        FEATURE_NAME, passCount, failCount);
}
```

**R — Result**
> Full regression run time reduced from 3 days to 4 hours. Once automated, a junior
> engineer could trigger the suite and collect results without ADAS domain expertise.
> Regression was run after every build instead of every two weeks — two regressions
> were caught that would have been missed under the old schedule. The script library
> was adopted as the project standard and used by two other teams on related platforms.

---

## Quick STAR Template (for adapting to any ADAS question)

```
S — SITUATION
  "On [project/feature], during [phase: integration/validation/HIL/vehicle testing],
   [context that creates the challenge]..."

T — TASK
  "My responsibility was to [specific action/requirement] —
   the key constraint was [time / safety level / spec requirement]."

A — ACTION
  "I [tool used: CANoe / CAPL / dSPACE / Python] to [what you did step by step].
   When I found [unexpected result], I [diagnostic step].
   The key insight was [technical finding]."

R — RESULT
  "[Quantified outcome: bug found / requirement verified / time saved].
   This was important because [impact on project / safety / team].
   As a follow-up, I also [improvement or lesson applied]."
```

> **Interview tips:**
> - Always name the tool (CANoe, CAPL, dSPACE) — interviewers want to know you can use it
> - Always include a number (150ms latency, P1 defect, 3-day reduction)
> - Always end with project impact — not just "I fixed it" but "this prevented X"
> - Keep each answer to 90–120 seconds when spoken aloud
