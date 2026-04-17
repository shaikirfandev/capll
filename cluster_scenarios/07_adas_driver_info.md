# Scenarios 16–20 — ADAS Alerts & Driver Information
## Instrument Cluster Validation — Scenario-Based Interview Prep

---

## Scenario 16 — Lane Departure Warning Activates on Straight Motorway With No Lane Change

> **Interviewer:** "The Lane Departure Warning (LDW) icon and chime activate repeatedly while driving in the centre of a clear motorway lane. There is no actual lane departure. What is causing false activation?"

**Background:**
LDW uses a camera to track lane markings. False activations occur when the camera detects something it interprets as a lane boundary that isn't one, or when the camera is miscalibrated.

**Investigation Path:**

**Step 1 — Identify camera data vs cluster display:**
```capl
on message ADAS::LDW_Status_BC {
  write("LDW: LeftLine=%d  RightLine=%d  Warn=%d  Reason=%d  LatDeviation=%.2fm",
        this.LDW_LeftLaneDetected,
        this.LDW_RightLaneDetected,
        this.LDW_WarningActive,
        this.LDW_WarningReason,
        this.LDW_LateralDeviation_m);
}
```
- Is the LDW_WarningActive from ADAS camera = 1 (camera genuinely reports warning)?
- Or is the cluster showing LDW without the ADAS confirming?

**Step 2 — Camera calibration check:**
LDW camera requires calibration after:
- Windscreen replacement
- Camera bracket adjustment
- Significant accident (even minor)
If the camera's pitch angle is off by 1–2 degrees, the lane detection confidence reduces, causing false positives.

**Step 3 — Road condition factors:**
- Road repair markings, shadows from trees, worn lane markings
- If `LDW_LeftLaneDetected = 0` (camera cannot see left line) → system may default to a virtual lane boundary → false warning when near road edge

**Step 4 — Speed threshold check:**
LDW should only activate above 60 km/h (EN ISO 11270 standard).
If activating below 60 km/h: threshold incorrectly configured.

**Step 5 — Sensitivity setting:**
LDW sensitivity: Low / Medium / High
At "High", the warning triggers even for minor drift within the lane.
Test: set to "Low" sensitivity → do false activations stop? → confirms sensitivity configuration.

**CAPL False Activation Monitor:**
```capl
variables {
  int   gFalseActivations = 0;
  int   gTrueActivations  = 0;
  float gLatDev_threshold = 0.30;   // 30cm from lane centre = genuine departure
}

on message ADAS::LDW_Status_BC {
  if (this.LDW_WarningActive == 1) {
    float latDev = this.LDW_LateralDeviation_m;
    float speed  = getValue(ABS::VehicleSpeed_kmh);

    if (speed < 60.0) {
      write("FALSE ACTIVATION — Speed %.1f km/h below LDW threshold (60 km/h)", speed);
      gFalseActivations++;
    } else if (latDev < gLatDev_threshold) {
      write("FALSE ACTIVATION — Lateral deviation %.2fm < %.2fm threshold at %.1f km/h",
            latDev, gLatDev_threshold, speed);
      gFalseActivations++;
    } else {
      write("TRUE activation — deviation %.2fm at %.1f km/h", latDev, speed);
      gTrueActivations++;
    }
  }
}

on stopMeasurement {
  write("LDW: True=%d  False=%d  False Rate=%.1f%%",
        gTrueActivations, gFalseActivations,
        (float)gFalseActivations / (gTrueActivations + gFalseActivations + 0.001) * 100.0);
}
```

**Test Cases:**
```
TC_LDW_001: Drive straight in lane centre at 80 km/h → 0 LDW activations over 10 km
TC_LDW_002: Drift 35cm to left without signal → LDW left warning within 0.5s
TC_LDW_003: Indicate left, cross left line → no LDW warning (indicator suppresses)
TC_LDW_004: Speed = 50 km/h → no LDW activity regardless of lane position
TC_LDW_005: Drive over road repair markings (known test route) → LDW false activation rate < 5%
TC_LDW_006: Camera blocked (tape) → cluster shows LDW unavailable icon (not silent failure)
```

**Root Cause Summary:**
Camera calibration pitch angle was 1.5° high after a windscreen replacement. This caused the camera to see the road surface 8m ahead instead of 20m, compressing the lane angle perspective. At 80 km/h, normal suspension pitch oscillation caused the camera's perspective-corrected lane tracking to oscillate by ±0.4m, exceeding the LDW threshold. Fix: recalibrate camera to OEM spec using the camera calibration target board.

---

## Scenario 17 — Blind Spot Warning Active on Both Sides Simultaneously

> **Interviewer:** "Both blind spot indicator lights (left mirror and right mirror) are illuminated simultaneously and continuously while driving — even on an empty motorway with no vehicles visible for 500m. How do you debug this?"

**Background:**
Blind spot detection uses rear-corner radar modules. Both active simultaneously while stationary/empty road suggests either: both radars have faults, the CAN signal is stuck, or the cluster is displaying a default/fault state.

**Investigation Path:**

**Step 1 — Sensor status check:**
```capl
on message RADAR::BlindSpot_Status_BC {
  write("BSD: Left=%d  Right=%d  LeftSensor=%d  RightSensor=%d  SystemFault=%d",
        this.BSD_Left_ObjectDetected,
        this.BSD_Right_ObjectDetected,
        this.BSD_LeftSensor_Status,   // 0=OK 1=Blocked 2=Fault
        this.BSD_RightSensor_Status,
        this.BSD_SystemFault);
}
```

**Step 2 — Sensor blockage:**
Radar sensors are behind the rear bumper. If the bumper has a metallic repair patch, sticker, or mud/ice covering the sensor area: the sensor detects the obstruction as a permanent object → warning stays on.
Test: clean the rear bumper radar zones → do warnings clear?

**Step 3 — Default state on sensor fault:**
Some BSD implementations default to "both sides warning ON" when the radar ECU detects an internal fault.
This is a fail-safe design: warn the driver that ADAS is unreliable (fail-on vs fail-off).
Check: is there a BSD fault DTC?
```
UDS 0x19 02 08 on RADAR ECU → any active DTCs?
```

**Step 4 — CAN signal stuck high:**
If the BSD CAN message is sending `BSD_Left = 1` and `BSD_Right = 1` consistently:
- Both radar sensors detecting something (obstruction, sensor degradation)
- Or: the CAN message has been stuck at a non-zero value (TX buffer issue in radar ECU)

**Step 5 — Power cycle test:**
Turn car off → wait 30s → restart.
If warnings clear on restart: transient fault in radar ECU → intermittent
If warnings return immediately: persistent hardware fault

**Test Cases:**
```
TC_BSD_001: No vehicles within 100m → both BSD lights OFF
TC_BSD_002: Vehicle in left blind spot → left light ON, right light OFF
TC_BSD_003: Both blind spots occupied → both lights ON (correct)
TC_BSD_004: Radar blocked (tape simulation) → cluster shows sensor blocked warning, not false object detection
TC_BSD_005: Indicate to change lane with object in blind spot → additional chime/alert
TC_BSD_006: Vehicle overtakes and leaves blind spot → warning clears within 1 second
```

**Root Cause Summary:**
The left radar sensor had a firmware crash loop — it rebooted every 45 seconds and on each reboot briefly transmitted `ObjectDetected = 1` on both outputs (the default TX register value cleared only after RTOS fully initialised). The right sensor was fine but the combined signal was permanently both-ON between reboot events. DTC: `U3001 Internal ECU fault — radar processor watchdog reset`. Fix: patch radar firmware default TX register to 0x00 before RTOS init, and add watchdog reset DTC suppression during first 500ms of startup.

---

## Scenario 18 — Forward Collision Warning Triggers at Parked Cars 200m Ahead

> **Interviewer:** "Forward Collision Warning (FCW) activates and shows a frontal collision icon on the cluster when passing a row of legally parked cars 200m to the right side of the road. The car being driven is nowhere near these parked cars. What is wrong?"

**Background:**
FCW uses a front radar and/or camera to detect objects in the vehicle's projected path. 200m range false positive from roadside parked cars suggests radar beam width or azimuth angle issue.

**Investigation Path:**

**Step 1 — Radar beamwidth and azimuth:**
Long-range radar (77 GHz): typically 200m range, ±10° horizontal beamwidth.
At 200m distance, ±10° beam covers: `2 × 200 × tan(10°) = 70m wide span`
If parked cars are 3m from road edge and road is 3.5m wide (total offset ~7m from lane centre), at 200m range: `angle = atan(7/200) = 2°` — well within the 10° beam.
So the radar IS receiving a return from a parked car — the issue is the path prediction, not the beam.

**Step 2 — Path prediction algorithm:**
FCW should only warn for objects in the predicted vehicle path.
Path prediction uses: steering angle, yaw rate, speed → projects an arc.
If yaw rate = 0 (straight line) but the parked cars are in an arc (road curves slightly), the straight-line projection may clip the parked cars incorrectly.

**Step 3 — Object classification:**
Modern FCW classifies objects as: moving vehicle, stationary vehicle, guard rail, parked car.
"Parked cars" should be filtered from FCW (too many false alarms on city roads).
If the classification is incorrect (parked car classified as stopped vehicle in path) → FCW triggers.

**Step 4 — Sensor fusion check:**
Camera + radar fusion: camera confirms if the detected radar object is in the driving lane.
If camera processing is delayed (high CPU load, or camera blocked by direct sunlight → camera unavailable) → radar fusion reverts to radar-only → less accurate path discrimination → more false positives.

**CAPL FCW False Positive Counter:**
```capl
variables {
  int gFCW_count    = 0;
  int gFCW_false    = 0;
  int gFCW_genuine  = 0;
}

on message ADAS::FCW_Alert_BC {
  if (this.FCW_AlertActive == 1) {
    gFCW_count++;
    float ttc = this.FCW_TimeToCollision_s;       // Time to collision
    float relVel = this.FCW_RelativeVelocity_ms;  // Relative velocity to object

    // Genuine FCW: object in path approaching, TTC < 2.5s
    if (ttc < 2.5 && relVel < -2.0) {
      write("GENUINE FCW [#%d] TTC=%.1fs  RelVel=%.1fm/s", gFCW_count, ttc, relVel);
      gFCW_genuine++;
    } else {
      write("FALSE FCW   [#%d] TTC=%.1fs  RelVel=%.1fm/s  ← probable false positive",
            gFCW_count, ttc, relVel);
      gFCW_false++;
    }
  }
}

on stopMeasurement {
  write("FCW Summary: Genuine=%d  False=%d  False Rate=%.1f%%",
        gFCW_genuine, gFCW_false,
        (float)gFCW_false / (gFCW_count + 0.001) * 100.0);
}
```

**Test Cases:**
```
TC_FCW_001: Empty straight road → drive 5 km at 80 km/h → 0 FCW activations
TC_FCW_002: Vehicle 50m ahead braking hard → FCW activates within 0.5s
TC_FCW_003: Parked cars at roadside → no FCW activation when not in projected path
TC_FCW_004: FCW false positive rate on standard test route < 1 per 50 km
TC_FCW_005: FCW deactivated (user setting) → cluster shows FCW off indicator, no alerts
TC_FCW_006: Camera unavailable (sun glare) → FCW degrades to radar-only mode with appropriate cluster indicator
```

**Root Cause Summary:**
Sensor fusion was not running during the test — the camera had a temporary calibration flag set (from a recent tool visit), disabling the camera's lane-placement input. Without camera lane validation, the radar-only FCW triggered on stationary objects with TTC calculations that didn't account for lateral offset. Fix: (1) cancel calibration flag correctly on completion, (2) radar-only FCW must apply a stricter lateral path tolerance (±1.5m vs ±4m for fused mode).

---

## Scenario 19 — Driver Assistance Icons Appear in Wrong Cluster Zone

> **Interviewer:** "After a cluster display layout software update, the ADAS status icons (LDW, ACC, LKA) are appearing in the centre of the speedometer dial instead of the ADAS status bar at the bottom of the cluster. How do you diagnose a UI layout regression?"

**Background:**
Icon position is defined in the cluster HMI specification, implemented in the cluster's display skin/theme files. After a SW update, the positioning data may have been overwritten or incorrectly merged.

**Investigation Path:**

**Step 1 — Compare SW versions:**
- Previous SW (correct): cluster SW v2.4
- Current SW (wrong): cluster SW v2.5
- Check git diff / change log for any HMI layout file changes (XML, JSON, or proprietary format)

**Step 2 — Layout specification check:**
```
Cluster layout spec: CL_HMI_Layout_Spec_v3.1, Section 4.2
  ADAS status bar: x=0, y=210, width=800, height=50 pixels (bottom of display)
  Speedometer info zone: x=150, y=100, width=300, height=200 pixels (centre dial)
```
If the ADAS icon `y` coordinate was changed from 210 to 100 → icons move to speedometer zone.

**Step 3 — HMI validation CAPL script (signal → position test):**
```capl
// Verify icon appears in correct cluster zone by reading
// cluster pixel zone report (if cluster supports zone reporting via UDS)
variables {
  diagRequest Cluster.ReadDataByIdentifier_Zones reqZone;
}

testcase TC_ICON_POSITION_LDW() {
  // Step 1: Activate LDW icon
  message ADAS::LDW_Status_BC msgLDW;
  msgLDW.LDW_WarningActive = 1;
  output(msgLDW);
  testWaitForTimeout(500);

  // Step 2: Read cluster zone report
  diagSetParameter(reqZone, "dataIdentifier", 0xF300);   // Zone report DID
  diagSendRequest(reqZone);
  testWaitForResponse(reqZone, 1000);

  // Step 3: Verify icon zone
  int iconZone = diagGetRespPrimitiveByte(reqZone, "LDW_Icon_Zone");
  // Zone 5 = ADAS status bar, Zone 2 = speedometer centre (wrong)
  if (iconZone == 5) {
    testStepPass("TC_POS_LDW", "LDW icon in correct zone 5 (ADAS bar)");
  } else {
    testStepFail("TC_POS_LDW",
      "LDW icon in WRONG zone " + (string)iconZone + " (expected zone 5)");
  }

  // Clean up
  msgLDW.LDW_WarningActive = 0;
  output(msgLDW);
}
```

**Step 4 — Visual regression test:**
For clusters with screenshot capability (engineering mode):
```bash
# Capture cluster screenshot via UDS or ADB
adb shell screencap -p /sdcard/cluster_screenshot.png
adb pull /sdcard/cluster_screenshot.png

# Compare pixel coordinates of LDW icon (using Python + OpenCV template matching)
python3 validate_icon_position.py --image cluster_screenshot.png \
        --template LDW_icon_template.png \
        --expected_x 400 --expected_y 220 --tolerance 10
```

**Test Cases:**
```
TC_ICON_001: LDW icon appears in ADAS status bar zone (bottom of cluster) — not in dial area
TC_ICON_002: ACC icon appears in ADAS status bar zone alongside LDW
TC_ICON_003: All OEM-defined icon positions verified against layout spec table (30 icons)
TC_ICON_004: Icon positions identical in km/h and mph market variants
TC_ICON_005: Icon positions correct at all brightness levels (icon coordinates, not rendering)
TC_ICON_006: SW update: icon positions must not change unless layout spec is also updated
```

**Root Cause Summary:**
The HMI layout file underwent a merge conflict during the v2.5 SW branch. The merge resolution incorrectly applied the ADAS icon `y` coordinate from an older branch (y=100, speedometer zone) instead of the current spec (y=210, ADAS bar). The automated CI pipeline did not include a visual regression test for icon positions — only functional activation was tested. Fix: add pixel-coordinate validation to the CI pipeline using screenshot comparison.

---

## Scenario 20 — Adaptive Cruise Control Active Speed Displays Wrong Target Speed

> **Interviewer:** "The driver sets ACC to 110 km/h. The ACC icon shows the correct 110 km/h set speed. But then a speed limit sign changes to 90 km/h and the system automatically adjusts to 90 km/h. The cluster now shows two speeds: 90 km/h (actual driving speed) and 110 km/h (set speed). The customer thinks the system is over-speeding. What is the display issue?"

**Background:**
This is a user information design issue — when ACC automatically adjusts for speed limits, the "set speed" display should update to reflect the active speed limit override, not retain the manually set speed.

**Investigation Path:**

**Step 1 — Two ACC speed signals:**
```capl
on message ACC::ACC_Status_BC {
  write("ACC: SetSpeed=%d km/h  ActiveSpeed=%d km/h  LimitOverride=%d km/h  Mode=%d",
        this.ACC_UserSetSpeed_kmh,      // what user pressed = 110
        this.ACC_CurrentTargetSpeed_kmh, // what system is actually doing = 90
        this.ACC_SpeedLimitActive_kmh,   // ISA speed limit = 90
        this.ACC_Mode);                  // 0=off 1=active 2=holding 3=speedlimit
}
```
The cluster is displaying `ACC_UserSetSpeed = 110 km/h` but should switch to displaying `ACC_CurrentTargetSpeed = 90 km/h` when speed limit is overriding.

**Step 2 — Cluster display logic for overrides:**
The cluster display should show `Current Target Speed` when `LimitOverride` is active, with a different symbol to indicate automatic override:
```
Normal ACC:          [110] (user set, bold)
Speed limit override: [90] (smaller, with speed limit sign icon)
```
If the cluster only ever shows `UserSetSpeed`, it will always show 110 when user set 110, regardless of ISA override.

**Step 3 — ISA (Intelligent Speed Assistance) integration:**
EU regulation (from July 2022) requires ISA in all new vehicles. ISA camera/map reads speed sign → sends to ACC → ACC adjusts.
The HMI must clearly distinguish between:
- User-set speed
- ISA-limited speed
Showing only user-set speed when ISA is active → EU regulation compliance failure.

**Step 4 — Signal source verification:**
```capl
// Monitor which speed the cluster is using for display
on signal Cluster::ACC_DisplayedTargetSpeed_kmh {
  write("Cluster ACC display: %.0f km/h", this.value);
}
on signal ACC::ACC_CurrentTargetSpeed_kmh {
  write("ACC actual target: %.0f km/h", this.value);
}
// These must match when ISA override active
```

**Test Cases:**
```
TC_ACC_001: User sets 110 km/h → no speed limit → cluster shows 110 km/h
TC_ACC_002: User sets 110 km/h → 90 km/h sign → ACC adjusts → cluster shows 90 km/h (not 110)
TC_ACC_003: Speed limit ends → ACC resumes user set speed → cluster shows 110 km/h
TC_ACC_004: ISA override active → cluster shows ISA speed limit icon + current target speed
TC_ACC_005: User overrides ISA (press accelerator) → cluster shows user speed + override indicator
TC_ACC_006: ACC off → cluster shows no ACC speed display (area clears within 1s)
```

**Root Cause Summary:**
Cluster display logic was written to always show `ACC_UserSetSpeed` as the primary speed. The `ACC_CurrentTargetSpeed` signal was added later (when ISA was integrated) but the cluster display logic was not updated to switch its display source when ISA override is active. This is an integration oversight between the ACC/ISA team and the cluster HMI team. Fix: cluster must display `ACC_CurrentTargetSpeed` when `ACC_SpeedLimitActive_kmh > 0`, with an ISA indicator icon.

---
*File: 07_adas_driver_info.md | Scenarios 16–20 | April 2026*
