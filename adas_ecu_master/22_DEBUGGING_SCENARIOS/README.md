# 22 — Debugging Scenarios

> **Level:** Senior ADAS ECU Software Engineer  
> **10 Real Lab Scenarios with root cause and fix**

---

## Lab 01: LKA Not Activating Above 60 km/h

```
SYMPTOM: LKA state stays STANDBY even at 80 km/h with lane markers visible.
REPORT: Driver: "LKA light on dashboard but steering does not correct."

INVESTIGATION:
  Step 1: CANoe trace — check LKA state signal (ADAS_LKA_Cmd 0x300, LkaActiveFlag)
    Observed: LkaActiveFlag = 0 (STANDBY confirmed)
  Step 2: Check LKA inputs — LaneOffset signal from camera
    Observed: LaneOffset = 0.08m (within standby threshold of 0.15m)
    
ROOT CAUSE: Vehicle is centred in lane → LaneOffset < OFFSET_CORRECT_M (0.15m).
  LKA is correctly in STANDBY — no correction needed.
  Driver expected correction even when centred → feature misunderstanding.
  
LESSON: LKA STANDBY = feature armed, not applying torque.
  LKA CORRECTING = actively steering.
  Dashboard LED "on" = feature armed (STANDBY or CORRECTING).
```

---

## Lab 02: Intermittent CAN Bus-Off on ADAS ECU

```
SYMPTOM: ADAS ECU goes bus-off ~2-3 times per hour on long drive.
         All LKA/ACC functions go inactive for ~500ms, then recover.
REPORT: DTC stored: U0155 "Lost Communication with ADAS ECU"

INVESTIGATION:
  Step 1: CANalyzer — check TEC/REC counters on ADAS ECU
    Observed: TEC rising to 255 (ECU enters passive mode), then drops to 0 after recovery
  Step 2: Check error frames — which CAN ID is causing errors?
    Tool: error frame filter in CANalyzer
    Observed: Error frames correlate with transmission of ADAS_LKA_Cmd (0x300)
  Step 3: Check CAN wiring near firewall — found intermittent ground connection
  Step 4: Oscilloscope on CAN bus: dominant bit voltage drops to 0.5V (should be 1.5V)
    → Termination resistor 120Ω loose connection

ROOT CAUSE: Intermittent 120Ω termination resistor → impedance mismatch → signal reflections
  → bit errors → TEC accumulates → bus-off.

FIX: Replace CAN connector at firewall. Add DTC logging for TEC counter threshold (>100).

LESSON: Bus-off is almost always a hardware issue (termination, wiring, ground), not software.
```

---

## Lab 03: ACC Overshoot — Speed Goes 10 km/h Above Set Speed

```
SYMPTOM: ACC set to 100 km/h. After cut-out (lead vehicle changes lane),
  ego speed rises to 110 km/h for ~3 seconds before settling.
  
INVESTIGATION:
  Step 1: Log ACC state transitions
    Observed: FOLLOWING → SPEED_CONTROL transition at lead vehicle cut-out
    Integral term in speed PID at transition: +8.5 Nm·s (heavily wound up)
  Step 2: Review FOLLOWING → SPEED_CONTROL transition code
    Found: PID is NOT reset on FOLLOWING→SPEED_CONTROL transition
    Wound-up integral (from following slowly) immediately applies excess throttle

ROOT CAUSE: PID integrator windup during FOLLOWING state.
  When following at low gap PID demanded high throttle (to reduce gap),
  integral accumulated large positive value.
  On cut-out: speed PID takes over with pre-wound integral → overshoot.

FIX: Reset integrators on all state transitions.
  speedPid_.reset();
  gapPid_.reset();
  // Called in: FOLLOWING onExit()

LESSON: ALWAYS reset PID integrators on state transitions.
  Document in state transition table which PIDs are reset on each transition.
```

---

## Lab 04: Memory Corruption — LKA Torque Output Randomised

```
SYMPTOM: LKA outputs random torque values intermittently.
  Values outside ±3 Nm limit observed in CAN traces.
  
INVESTIGATION:
  Step 1: Check PID output — is it within limits?
    CAN trace: LkaTorqueRequest sometimes = 15.7 Nm, 0 Nm, -28.2 Nm
  Step 2: Add logging before/after LKA mainfunction → values corrupted BEFORE PID compute
  Step 3: Static analysis (Polyspace): no RED results in LKA SWC
  Step 4: Check stack size — LKA_10ms task stack = 1024 bytes
    Compiler .su file analysis: worst-case stack depth = 1120 bytes (OVERFLOW!)
  
ROOT CAUSE: Stack overflow in LKA_10ms task.
  Sensor fusion struct (256 bytes) added to LKA task — but stack not increased.
  Stack overflow corrupts adjacent task's stack or .bss variables.
  
FIX: Increase LKA_10ms STACK_SIZE from 1024 to 2048 in OIL file.
  Add stack watermark check in background task.
  Add MPU guard page below every task stack.

LESSON: Stack overflow is silent. Always size stacks with .su file analysis + 20% margin.
```

---

## Lab 05: Race Condition — Sporadic LKA State Flip

```
SYMPTOM: LKA randomly jumps from CORRECTING to STANDBY and back within 1 cycle.
  Visible as brief "flicker" in LKA active torque.
  Reproducible only on multi-core ECU (not in simulation).
  
INVESTIGATION:
  Step 1: Add cycle counter logging to state transitions
    Observed: at cycle N, state = CORRECTING. State variable = 0x02.
    At cycle N+1 (in same timestamp), state = STANDBY. Variable reads as 0x01.
  Step 2: Suspect multi-core access to shared state variable
    LKA state machine runs on Core1. Dashboard display function reads state on Core0.
    State variable: LkaState state_; (NOT protected by spinlock)
  Step 3: Core0 display task reads partial write of 16-bit state variable while Core1 writes it

ROOT CAUSE: Non-atomic read of state variable across cores.
  16-bit write on Core1 is NOT atomic on AURIX TriCore — two 8-bit bus cycles.
  Core0 reads between the two 8-bit writes → corrupted value.

FIX: Use std::atomic<LkaState> for cross-core state variables.
  Or: copy state to display buffer under spinlock at end of LKA cycle.

LESSON: Any variable read by multiple cores needs atomicity or explicit locking.
  Even enum types are not guaranteed to be atomically written on all architectures.
```

---

## Lab 06: CAN Signal Wrong Byte Order

```
SYMPTOM: SteeringAngle shows +3200 deg when EPS measures +2.5 deg.
  All other EPS signals are correct.

INVESTIGATION:
  Step 1: Raw CAN frame for EPS_Status (0x200) at known steering angle (+2.5 deg):
    Bytes 0-1: 0xFB 0x63 
  Step 2: Intel decode: raw = 0x63FB = 25595 → physical = (25595 × 0.1) - 3276.8 = 2282.7 deg (WRONG)
  Step 3: Motorola decode: raw = 0xFB63 → ...
    Wait — check DBC file for EPS_Status in current project
    DBC says: SteeringAngle @1 (Intel, little-endian)
    BUT: actual EPS ECU (from different supplier) generates Motorola (big-endian)!

ROOT CAUSE: DBC file and ECU have mismatched byte order.
  New EPS ECU supplier changed from Motorola to Intel encoding.
  DBC file was not updated.

FIX: Update DBC signal to @0 (Motorola) for SteeringAngle.
  Regenerate ARXML COM configuration from updated DBC.
  Rebuild and verify: raw = 0xFB63, Motorola decode: 
    MSB first = physical = +2.5 deg ✓.

LESSON: Always verify byte order (Intel vs Motorola) when integrating a new ECU supplier.
  Create an on-target "sanity value" test: command known steering angle, read CAN signal,
  verify decoded value matches.
```

---

## Lab 07: Watchdog Reset Every 100ms During Fast Braking

```
SYMPTOM: ECU resets exactly every 100ms when AEB fires (hard braking event).
  No reset during normal driving.

INVESTIGATION:
  Step 1: Reset reason register: 0x04 = watchdog reset
  Step 2: WdgM configuration: windowed watchdog, window 50-100ms
  Step 3: Check task timing during AEB:
    AEB function called from LKA_10ms task due to FAULT event (unexpected)
    AEB function: calls radar processing + CAN frame burst send: takes 85ms!
  Step 4: LKA_10ms task BLOCKS for 85ms → WdgM checkpoint not reached in time
    → Watchdog fires at 100ms

ROOT CAUSE: AEB function erroneously called from wrong task context.
  AEB is a heavy 50ms periodic function — incorrectly placed in 10ms task.
  
FIX: Move AEB processing to its own 50ms task.
  Add WCET annotation to every task function call.
  Add WdgM early checkpoint after AEB to split budget.

LESSON: Watchdog resets during high-load events indicate WCET budget violation.
  Always measure task execution time with on-target profiling (AURIX STM timer).
```

---

## Lab 08: Lane Offset Drifts During Curves

```
SYMPTOM: On curved roads (R < 200m), LKA fights steering → driver feels resistance.
  Lane offset oscillates between +0.2m and -0.2m at 10 Hz.

INVESTIGATION:
  Step 1: Log LaneOffset from camera vs LKA torque output
    Observed: camera reports lane offset with 80ms latency on curves
    PID uses stale lane offset → derivative term oscillates due to step updates
  Step 2: Check camera filter configuration: temporal smoothing filter: 8-sample average
    At 60 km/h on curve: 8 × 20ms = 160ms of smoothing → ~4.8m of vehicle travel
    Lane offset measurement is "stale" by 4.8m in curve

ROOT CAUSE: Camera temporal filter causes excessive delay on curves.
  LKA PID with high Kd amplifies the delayed derivative → oscillation.

FIX option 1: Reduce camera temporal filter to 3-sample average (60ms latency).
FIX option 2: Add curve radius feed-forward to LKA — reduce Kd on curves.
  if (laneRadiusM < 300.0F) { kd *= 0.3F; }
FIX option 3: Use steering angle rate as proxy for lane change (faster signal).

LESSON: Control loop stability depends on sensor latency.
  Model the full loop delay: sensor delay + processing delay + actuator delay.
  Rule of thumb: total loop delay < 0.5 / (2π × bandwidth_Hz).
```

---

## Lab 09: UDS 0x22 Returns Empty Response

```
SYMPTOM: Workshop tool cannot read VIN (DID 0xF190) from ADAS ECU.
  Tool shows: negative response 0x31 (requestOutOfRange).
  All other DIDs work (SW version, serial number, etc.).

INVESTIGATION:
  Step 1: Check DCM configuration in ARXML for DID 0xF190
    DcmDspData: DID 0xF190, ReadFunction = "Dcm_ReadVin"
    Session: DIAGNOSTIC_SESSION_01 (default session)
  Step 2: Check if function Dcm_ReadVin is implemented in ECU
    Found: function stub only — returns E_NOT_OK immediately
  Step 3: VIN data source: should come from BCM_VIN_Block in NvM
    NvM_ReadAll() result: INIT (not yet read — NvM async read not completed at ECU start)
  Step 4: Timing: diagnostic tool connects immediately after ECU power-on
    NvM_ReadAll takes 300ms on this ECU → VIN not available in first 300ms

ROOT CAUSE: Race condition between NvM read completion and diagnostic tool request.
  Dcm_ReadVin returns E_NOT_OK because NvM block not yet read.
  DCM maps E_NOT_OK → negative response 0x31.

FIX: Check NvM read status before returning VIN:
  if (NvM_GetErrorStatus(VIN_BLOCK_ID) != NVM_REQ_OK) {
    return DCM_E_NOT_OK;  // Return 0x22 (conditionsNotCorrect) instead of 0x31
  }
  // Memcpy VIN data

LESSON: Always handle asynchronous NvM readback in diagnostic handlers.
  Use negative response code 0x22 (conditionsNotCorrect) not 0x31 (requestOutOfRange)
  when data is temporarily unavailable.
```

---

## Lab 10: Sensor Fusion — Ghost Object Causes False ACC Braking

```
SYMPTOM: ACC occasionally brakes hard on clear highway with no vehicle in front.
  Event lasts ~200ms, then ACC returns to normal.
  No DTC stored.

INVESTIGATION:
  Step 1: Extract ETK/XCP log of radar object list at time of event
    Observed: object ID 0x12 at 45m, azimuth 0.2°, confidence 75%
    Duration: 4 radar cycles (200ms) → passes persistence filter (3 cycles)
  Step 2: Cross-check camera object list
    Camera: no vehicle detected at 45m during same period
  Step 3: Scene reconstruction: bridge overpass was present at that location
    Radar reflected off bridge structure → ghost target at 45m
  Step 4: Camera had classified it correctly as "infrastructure" → rejected from camera list
    But fusion algorithm had bug: accept radar object if camera list is EMPTY (not just if no conflict)
    At that moment, camera pipeline was briefly unavailable (1 frame glitch)

ROOT CAUSE: Fusion logic flaw — radar-only object accepted without camera confirmation
  when camera is temporarily unavailable (should require camera confirmation or timeout).

FIX: Fusion logic change:
  Accept radar-only object ONLY if: camera is available AND has no conflicting detection.
  If camera unavailable > 2 cycles → degrade ACC (disable following, speed-only control).
  Increase radar confidence threshold to 90% for in-path objects < 60m.

LESSON: Fusion failure modes require explicit camera/radar availability state tracking.
  Never default to "accept" when one sensor is unavailable — default to "uncertain/degrade".
```
