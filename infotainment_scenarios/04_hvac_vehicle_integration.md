# Scenarios 16–20 — HVAC & Vehicle Integration
## Infotainment Test Validation — Scenario-Based Interview Prep

---

## Scenario 16 — Rear Parking Sensor Distance Bar Not Updating

> **Interviewer:** "The parking assist distance bar on the IVI screen freezes at 1.5m and does not update even as the vehicle continues reversing closer to an obstacle. The audio beeping continues to update correctly. How do you investigate?"

**Background:**
Audio beeping updates correctly — confirming PA ECU is functional and sending updated distance data over CAN. The display bar is frozen — so the issue is in the graphical update path, not the sensor itself.

**Investigation Path:**

**Step 1 — Separate audio from display paths:**
The PA ECU sends two things:
- `PA_Distance_m` CAN signal → used by both audio (correct) and display (frozen)
- If audio works but display freezes, the CAN signal is fine. The display render loop is the problem.

**Step 2 — Display update rate:**
```capl
// Monitor distance signal update rate
dword gLastUpdate = 0;
on signal ParkAssist::PA_Rear_Distance_cm {
  dword now = timeNow() / 10;
  write("PA Distance: %.0f cm  Delta time: %d ms", this.value, now - gLastUpdate);
  gLastUpdate = now;
}
```
- If signal updates every 100ms but display freezes at 1.5m → display rendering function is not called

**Step 3 — Rendering thread check:**
```bash
adb shell dumpsys window | grep -E "PA|parking|SurfaceView"
# If ParkingAssist SurfaceView shows 'paused' or 'stopped' → render thread suspended
adb logcat | grep -i "parking\|PA_view\|distance_bar"
```

**Step 4 — Scene transition conflict:**
The parking screen may have been launched before IVI was fully booted.
If a different app (reversing camera) claimed the display surface at boot, the PA bar surface may be rendered but hidden behind camera view.
Test: disable rearview camera → does PA bar now update?

**Step 5 — Data type overflow:**
If `PA_Distance_m` is a float and the display bar expects an integer, repeated float→int conversion in a loop may accumulate a rounding error causing the display to stick at the nearest integer (1.5m truncated to 1m stays at 1 visually).

**CAPL Automated BA Test:**
```capl
variables {
  message UltrasonicEcho_BC msgEcho;
  msTimer tmrSweep;
  float gDist = 200.0;   // start at 200cm
  int gPass = 0, gFail = 0;
}

on start {
  // Put car in reverse
  message GearStatus_BC msgGear;
  msgGear.GearPosition = 1;   // Reverse
  output(msgGear);
  delay(500);
  setTimer(tmrSweep, 200);
}

on timer tmrSweep {
  gDist -= 10.0;   // approach 10cm each step
  if (gDist < 10) { write("=== PA Bar Test: PASS=%d FAIL=%d ===", gPass, gFail); stop(); return; }

  msgEcho.PA_Rear_Distance_cm = (word)gDist;
  output(msgEcho);
  delay(150);

  // Read back what IVI display shows
  float displayed = getValue(IVI_ECU::PA_DisplayedDistance_cm);
  if (abs(displayed - gDist) <= 10.0) {
    gPass++;
  } else {
    write("FAIL — Sent=%.0f cm  Displayed=%.0f cm  (frozen?)", gDist, displayed);
    gFail++;
  }
  setTimer(tmrSweep, 200);
}
```

**Test Cases:**
```
TC_PA_BAR_001: Distance 200cm → 10cm in 10cm steps → display bar updates at each step within 200ms
TC_PA_BAR_002: Distance stationary at 50cm for 10s → bar remains at 50cm (no drift/freeze)
TC_PA_BAR_003: Shift from Reverse to Drive → PA bar disappears within 500ms
TC_PA_BAR_004: Shift back to Reverse → PA bar reappears and initialises correctly
TC_PA_BAR_005: All 4 sensors update simultaneously → display shows closest obstacle
TC_PA_BAR_006: PA ECU CAN timeout → bar shows '--' or dashed pattern (not frozen at last value)
```

**Root Cause Summary:**
SurfaceView rendering thread for the PA distance bar is not properly subscribed to the CAN signal update event post-reverse-camera activation. The camera view acquisition suspends the PA bar thread which only re-activates on the next full IVI restart. Fix: ensure PA bar view re-registers CAN listener after every camera view deactivation.

---

## Scenario 17 — Interior Lighting Does Not Change When Set via IVI

> **Interviewer:** "The ambient interior lighting settings on the IVI (colour, brightness) change on the screen but the actual interior lights do not respond. Other controls like seat heating work fine from the same Settings menu. What do you investigate?"

**Investigation Path:**

**Step 1 — Confirm physical lighting ECU is working:**
- Check if lighting responds to a different input: does automatic dimming (when door opens) work?
- If auto-dim works: the lighting ECU hardware is fine, the IVI → lighting ECU command path is broken.

**Step 2 — Network topology:**
- Ambient lighting is often on LIN bus (lower cost, simpler topology for lighting nodes)
- IVI sends RGB colour and brightness to the BCM or lighting master ECU via CAN
- BCM translates to LIN commands for individual lighting zones
- Where in this chain is the break?

**Step 3 — CAN command check:**
```capl
on message IVI::AmbientLight_Cmd {
  write("Lighting Cmd: Zone=%d  R=%d  G=%d  B=%d  Brightness=%d%%",
        this.AL_Zone,
        this.AL_Red,
        this.AL_Green,
        this.AL_Blue,
        this.AL_Brightness_Pct);
}
```
- Press colour change on IVI → is CAN message sent?
- If no CAN message: IVI SW bug in the settings→CAN output path (same layer as seat heating, but different message)

**Step 4 — BCM reception:**
UDS 0x22 on BCM: read ambient light colour DID → does BCM register the new colour?
If BCM shows correct new colour but LIN nodes don't respond: LIN bus issue between BCM and lighting nodes.

**Step 5 — LIN schedule:**
```
LIN schedule check:
  - BCM must include ambient light command frame in its LIN schedule
  - If frame is not scheduled → lights never receive update
  - After a BCM SW update, LIN schedule table may have been modified
```

**Step 6 — Colour gamut validation:**
Some lighting ECUs only accept sRGB values within a specific range. If the IVI sends `R=255, G=0, B=0` but the LED driver only supports 8-bit PWM values up to 240, the command may be silently rejected.

**Test Cases:**
```
TC_LIGHT_001: Set colour to Red (255,0,0) → all ambient zones turn red within 500ms
TC_LIGHT_002: Set brightness 0% → lights OFF → set 100% → lights at maximum
TC_LIGHT_003: Cycle through all 16 preset colours → each changes correctly within 300ms
TC_LIGHT_004: Change colour during driving at 100 km/h → no flicker, smooth transition
TC_LIGHT_005: Setting persists after ignition cycle (NVM save)
TC_LIGHT_006: Individual zone control (door, footwell, dashboard) → each zone responds independently
```

**Root Cause Summary:**
After an IVI SW update, the ambient lighting CAN message ID or signal byte order changed, but the BCM DBC was not updated to match. BCM receives the message but cannot decode it correctly → ignores it → no LIN command sent → lights unchanged. Classic DBC version mismatch after dual-SW-team release without joint integration test.

---

## Scenario 18 — Seat Memory Position Does Not Save From IVI

> **Interviewer:** "Pressing 'Save Position 1' on the IVI touchscreen does not store the current seat position. But pressing the physical button on the door panel saves it correctly. What is different?"

**Investigation Path:**

**Step 1 — Compare the two save paths:**
```
Physical door button path:
  Button press → Direct LIN signal to Seat ECU → Seat ECU saves NVM position

IVI touchscreen path:
  Touch event → IVI SW → CAN message to BCM → BCM LIN to Seat ECU → Seat ECU saves NVM
```
The physical button bypasses the IVI and BCM. The IVI path has more steps.

**Step 2 — Check if IVI sends the CAN command:**
```capl
on message IVI::SeatMemory_Cmd {
  write("Seat Memory Cmd: Position=%d  Action=%d (1=Save 2=Recall)",
        this.SeatMem_PositionSlot,
        this.SeatMem_Action);
}
```
- Tap 'Save Position 1' on IVI → does this CAN message appear?
- If not: IVI UI event not wired to CAN output — SW defect in touch event handler

**Step 3 — BCM relay:**
If CAN message is sent: does BCM forward the command to Seat ECU via LIN?
UDS 0x22 on Seat ECU: read saved position DID for slot 1 → has it updated?

**Step 4 — Permission / session check:**
Some implementations require UDS Extended Session to modify seat position NVM:
- IVI must send `0x10 03` before the save command
- If IVI sends save command without entering extended session → Seat ECU returns NRC 0x22 (conditions not correct) → save silently ignored

**Step 5 — Race condition:**
IVI sends save command while seat is still moving (motor running).
Seat ECU may reject save commands during movement.
Test: save only after seat has been stationary for 2 seconds.

**CAPL Test:**
```capl
variables {
  message SeatMemory_Cmd_IVI msgSave;
  int gPass = 0, gFail = 0;
}

testcase TC_SEAT_SAVE_IVI() {
  // Step 1: move seat to specific position
  testStep("Move seat to position 40% forward, 30% up");
  // (manipulated via HIL)

  // Step 2: send save command from IVI
  msgSave.SeatMem_PositionSlot = 1;
  msgSave.SeatMem_Action       = 1;  // Save
  output(msgSave);
  testWaitForTimeout(500);

  // Step 3: move seat to a different position
  testStep("Move seat to extreme position");

  // Step 4: send recall command
  msgSave.SeatMem_Action = 2;  // Recall
  output(msgSave);

  // Step 5: verify seat returned to saved position
  float pos = testGetSignalValue("SeatECU::SeatPosition_Pct");
  if (abs(pos - 40.0) < 2.0) {
    write("PASS — Seat recalled to saved position: %.1f%%", pos);
    gPass++;
  } else {
    write("FAIL — Seat position: %.1f%% (expected ~40%%)", pos);
    gFail++;
  }
}
```

**Test Cases:**
```
TC_SEAT_001: Save position via IVI → move seat → recall via IVI → seat returns to saved position ±2%
TC_SEAT_002: Save position via IVI → ignition cycle → recall → position restored correctly
TC_SEAT_003: Save position via door button → recall via IVI → same position retrieved
TC_SEAT_004: Save position while seat is moving → command accepted only after seat stationary (2s)
TC_SEAT_005: Save all 3 memory slots via IVI → recall each → all return correct distinct positions
TC_SEAT_006: IVI save command sent without extended UDS session → command still processed (IVI handles session internally)
```

**Root Cause Summary:**
The IVI SW touch handler for 'Save Position' was implemented without triggering the CAN output function — the button only updates the IVI UI state (showing "Position 1 saved" toast) without actually sending the CAN command. This is a classic SW integration defect where UI component and CAN output component were developed by different teams without end-to-end integration testing.

---

## Scenario 19 — Door Ajar Warning Does Not Clear on IVI After Door is Closed

> **Interviewer:** "After closing all doors, the door ajar warning icon on the IVI stays on for 30 seconds before clearing. Expected behaviour is clearing within 1 second of door close. What do you investigate?"

**Investigation Path:**

**Step 1 — CAN signal timing:**
```capl
on signal BCM::DoorFrontLeft_Status {
  write("FL Door: %d (0=Closed 1=Open)  Time=%d ms", this.value, timeNow()/10);
}

on signal IVI_ECU::DoorAjar_Warning_Displayed {
  write("IVI Door Warning Display: %d  Time=%d ms", this.value, timeNow()/10);
}
```
- Log both signals: when does BCM send "door closed" vs when does IVI clear the warning?
- If BCM sends "closed" immediately but IVI waits 30s → IVI has a debounce/timer delay

**Step 2 — IVI debounce filter:**
IVI may apply a debounce filter to door status to prevent false closes (e.g., door not fully latched).
Spec check: what debounce time is required?
- 200ms debounce is acceptable
- 30 seconds is clearly a bug (10–30x too long)
- Check if the debounce timer value was changed in a recent SW update (e.g., accidentally set to 30000ms instead of 300ms — off by 100x)

**Step 3 — NVM/state persistence:**
Door state may be written to NVM each time status changes.
If NVM write operation takes 30s (corrupted NVM, slow flash) → state update delayed.
Test: does the 30s delay happen every time? Or only after specific conditions?

**Step 4 — Multi-door condition:**
If the warning only clears when ALL doors are confirmed "closed" simultaneously:
```
IVI logic: clear when door_FL=0 AND door_FR=0 AND door_RL=0 AND door_RR=0 AND door_Boot=0
```
If rear doors are sending CAN at a slower update rate (50ms vs 10ms for front doors), the AND condition takes longer to satisfy.

**Step 5 — CAN message cycle time:**
Door status message has a 10ms cycle time. If some doors are configured for 500ms event-driven (transmit on change only) rather than cyclic, the IVI may not receive the close event until next transmission.
Test: check DBC spec for each door's CAN message cycle time.

**Test Cases:**
```
TC_DOOR_001: Open door → close door → warning clears within 1.0 second
TC_DOOR_002: Open all 5 doors simultaneously → close all → warning clears within 1.0s of last door close
TC_DOOR_003: Door opened and closed rapidly (5 times in 2s) → no false positive warnings left displayed
TC_DOOR_004: Boot/trunk opens → closes → IVI boot icon clears within 1s
TC_DOOR_005: Door status CAN message absent for 500ms → IVI shows warning (fail-safe behaviour)
TC_DOOR_006: 100 door close cycles → mean clearance time < 500ms, max < 1000ms
```

**Root Cause Summary:**
Debounce timer value in IVI SW configuration was changed from `300` (ms) to `30000` (ms) — likely a unit change from milliseconds to deciseconds went wrong. After recent SW build. Fix: correct the debounce constant and add a unit test that validates debounce is always ≤ 500ms.

---

## Scenario 20 — IVI Shows "Engine On" Status After Engine is Switched Off

> **Interviewer:** "The IVI infotainment screen continues to show engine running indicators (RPM > 0, engine temperature climbing) for up to 10 seconds after the engine is unambiguously switched off. How do you investigate?"

**Investigation Path:**

**Step 1 — CAN signal vs physical reality:**
```capl
on signal ECM::Engine_Running_Status {
  write("ECM Engine Status: %d (0=OFF 1=RUN 2=CRANK)  RPM=%.0f",
        this.value,
        getValue(ECM::Engine_RPM));
}
```
- Does ECM send "Engine OFF" immediately after key off?
- If ECM still sends RPM > 0 for 10s after engine stop: ECM has a shutdown delay in its signal output

**Step 2 — Engine RPM after shutdown:**
When engine is switched off, the flywheel still rotates for 1–3 seconds (mechanical inertia).
During this time, RPM is real (dropping from 850 → 0).
The IVI showing RPM decreasing from 850 → 0 over 3 seconds is correct behaviour.
But showing RPM > 0 for 10 seconds is too long → check if ECM RPM signal includes a filter or delay.

**Step 3 — Engine temperature climbing after off:**
Engine temperature rises briefly after shutdown due to heat soak (no coolant flow).
If IVI shows temperature increasing for 10s after off: this may be physically correct.
Check spec: is there a maximum time the IVI should show running data after ECM reports engine off?

**Step 4 — IVI state machine for "engine running" mode:**
Some IVI systems remain in "engine on" display mode for a timeout period after engine off to allow driver to view trip data.
This is intentional but may be set too long.
UDS 0x22 on IVI: read engine mode display timeout DID.

**Step 5 — Ignition signal vs engine signal:**
IVI may use KL15 (ignition ON) as proxy for engine running.
If KL15 remains HIGH for 10s after engine off (due to accessory mode, relay delay) → IVI shows engine on.
Check KL15 signal timing with oscilloscope.

**Test Cases:**
```
TC_ENG_001: Start engine → stop engine → IVI clears RPM display within 5 seconds of engine OFF signal
TC_ENG_002: Start engine → stop engine → IVI displays "Engine Off" state within 3 seconds
TC_ENG_003: Engine stop → all engine-running indicators (oil pressure, RPM, tachometer) cleared within 5s
TC_ENG_004: KL15 OFF delay of up to 3s → IVI correctly uses ECM engine status, not KL15, for mode change
TC_ENG_005: After engine off, driver still viewing trip summary → data remains but engine indicators clear
TC_ENG_006: Engine hot-restart within 2s of stop → IVI does not show "engine off" state briefly
```

**Root Cause Summary:**
IVI uses KL15 signal as the engine-running indicator, not the ECM Engine_Running_Status signal. A relay hold circuit keeps KL15 active for 8–10 seconds after key removal to allow graceful IVI shutdown. During this window, IVI shows engine indicators. Fix: use ECM Engine_Running_Status (immediate) for gauge display updates, use KL15 only for IVI power management.

---
*File: 04_hvac_vehicle_integration.md | Scenarios 16–20 | April 2026*
