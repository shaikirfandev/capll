# 20 — Interview Preparation — ADAS ECU Software Engineer (500+ Q&A)

> **Level:** Senior Engineer (L5/L6 equivalent) — Bosch, Continental, Aptiv, NVIDIA, Mobileye  
> **Topics:** Embedded C++, AUTOSAR, CAN, ADAS Algorithms, Safety, System Design

---

## Section A — Embedded C++ for ECU (Q1–Q80)

```
Q1: Why are exceptions forbidden in automotive ECU C++?
A: Stack unwinding is non-deterministic — variable execution time.
   Extra ROM (exception tables) and RAM (stack frames) overhead.
   OSEK/AUTOSAR OS does not support C++ exception unwinding.
   MISRA C++ Rule 15-0-1 prohibits exceptions.
   Compile with: -fno-exceptions -fno-unwind-tables

Q2: What is the volatile keyword used for in ECU code?
A: Two legitimate uses (AUTOSAR A2-11-1):
   1. Memory-mapped hardware registers: volatile uint32_t* const reg = (uint32_t*)0x4000;
   2. ISR-shared variables: volatile bool rxFlag;
   Volatile prevents compiler from caching value in register or reordering accesses.
   NOT a substitute for atomic or mutex in multi-threaded code.

Q3: What is the difference between const and constexpr?
A: const: value is immutable at runtime, but initialised at runtime if not constexpr.
   constexpr: evaluated at compile time. Uses ROM (flash) not RAM.
   constexpr float KP = 0.8F;  → placed in .rodata, zero RAM cost
   For ECUs: prefer constexpr for all calibration constants, lookup table sizes.

Q4: When would you use std::array vs raw array on an ECU?
A: std::array<float, 8U>: same memory layout as float[8], but:
   - .size() method (avoids manual sizeof division)
   - Bounds-checked at() access in debug builds
   - Copyable/assignable as a value type
   - Range-for compatible
   - AUTOSAR A18-1-1: prefer std::array over C-style arrays
   Raw array: only use for MCAL/BSW driver code interfacing with legacy C APIs.

Q5: Explain RAII with an example relevant to ECU.
A: Resource Acquisition Is Initialisation: acquire resource in constructor, 
   release in destructor. Destructor called even if function exits early.
   
   Example: CanMailboxLock guard:
   class CanMailboxLock {
   public:
     explicit CanMailboxLock(uint32_t mailboxId) : id_(mailboxId) {
       Can_LockMailbox(id_);         // Acquire
     }
     ~CanMailboxLock() { Can_UnlockMailbox(id_); }  // Release (always)
   private:
     uint32_t id_;
   };
   
   void sendFrame(uint32_t mbId, const CanFrame& f) {
     CanMailboxLock lock(mbId);  // Released at end of scope — no risk of forgetting
     Can_WriteMailbox(mbId, &f);
   }

Q6: What is a memory pool and why is it used on ECUs?
A: Fixed-block heap allocator: N pre-allocated blocks of equal size.
   Alloc: O(1), determ. (no fragmentation). Free: O(1), mark block as available.
   Use: when you need "dynamic-like" allocation for a known max number of objects.
   Example: radar object tracker — up to 32 tracked objects, pre-allocate all 32 slots.

Q7: What is the difference between a semaphore and a mutex in RTOS?
A: Mutex: binary lock. Owner = task that acquired it. Only owner can release.
   Prevents priority inversion via priority inheritance or priority ceiling.
   Use: protect shared data structures.
   
   Semaphore: signalling. Any task/ISR can signal (give), any can wait (take).
   ISR-to-task: ISR gives semaphore → task wakes up.
   Counting semaphore: counts pending events (up to N).
   Mutex != binary semaphore: mutex has ownership semantics, semaphore does not.

Q8: Explain move semantics and when they are safe to use on an ECU.
A: Move semantics: transfer ownership of resource from one object to another.
   Avoids expensive copy (especially for large buffers).
   
   ECU safety: move semantics are safe only for objects that:
   1. Do not hold hardware resources (ISR handles, register locks)
   2. Leave moved-from object in a valid state (AUTOSAR A12-8-3)
   3. Are used in non-safety-critical paths
   
   Common use: AUTOSAR Adaptive — ara::core::Vector<T> move instead of copy.
   In Classic (ASIL-D code): avoid move semantics — prefer static allocation entirely.

Q9: What is a template specialisation and when would you use it on an ECU?
A: Partial or full specialisation of a template for specific types.
   ECU use: StaticRingBuffer<bool, N> can use bitwise storage for compactness.
   Signal decoder: DecodeSignal<SignedType> vs <UnsignedType> different sign extension.
   
   MISRA caution: complex template specialisations are hard to review.
   Prefer simple, readable templates over clever meta-programming.

Q10: What is undefined behaviour (UB) and give 3 examples.
A: Code that the C++ standard does not define — compiler may generate anything.
   
   1. Signed integer overflow: int a = INT_MAX; int b = a + 1; // UB
      Fix: use uint32_t, or check before increment
   2. Null pointer dereference: int* p = nullptr; *p = 5; // UB
      Fix: assert(p != nullptr) at function entry
   3. Out-of-bounds array access: float arr[8]; float x = arr[10]; // UB
      Fix: always bounds-check, use std::array::at() in debug

Q11–Q20: More C++ topics
Q11: What are the rules for operator overloading in MISRA?
Q12: How do you implement a type-safe state machine without dynamic_cast?
Q13: What is placement new and when is it allowed in ECU code?
Q14: Explain constexpr functions vs templates for compile-time computation.
Q15: What is the strict aliasing rule and why does it matter for register access?
Q16: When is std::atomic sufficient vs when do you need a mutex?
Q17: What is a lambda in C++14? Are lambdas allowed in MISRA/AUTOSAR?
Q18: Explain the rule of three/five/zero for ECU classes.
Q19: What is copy elision (RVO/NRVO) and when can you rely on it?
Q20: How do you handle fixed-point arithmetic on ECUs without FPU?
```

---

## Section B — AUTOSAR (Q81–Q160)

```
Q81: What is the difference between AUTOSAR Classic and Adaptive?
A: Classic: static configuration, ARXML, OSEK OS, deterministic, ASIL-D, no heap.
   Adaptive: dynamic service discovery, C++17, Linux/QNX, SOME/IP, OTA, L3+.
   Classic = control-critical (brakes, steering). Adaptive = compute-intensive (ML, OTA).

Q82: What is an RPort and PPort in AUTOSAR SWC?
A: PPort = Provide Port: SWC provides a value/service to other SWCs.
   RPort = Require Port: SWC requires a value/service from other SWCs.
   Connection: PPort of SWC-A connected to RPort of SWC-B via Connector in Composition.
   
   Interface types: SenderReceiver (signal flow), ClientServer (function call), 
   ModeSwitch (operating modes), Parameter (calibration).

Q83: What is the COM stack's role in AUTOSAR?
A: COM (Communication): 
   - Packs multiple signals into one I-PDU (signal groups)
   - Applies AUTOSAR signal properties: timeout, initial value, update bit, invalid value
   - Signal filtering: on-change, periodic, mixed
   - IPDU Gateway mode: COM can route PDUs without SWC involvement

Q84: What is E2E protection in AUTOSAR and which ASIL requires it?
A: E2E = End-to-End protection. CRC + counter appended to safety PDUs.
   Detects: corrupted data (CRC fail), lost frames (counter gap), duplicate frames (same counter).
   Required: ASIL B and above for safety-relevant signals.
   Profile 1: 8-bit CRC, 4-bit counter. Profile 4: 32-bit CRC (FD/Ethernet).

Q85: Explain the DEM event lifecycle.
A: PREFAILED → FAILED → CONFIRMED → AGED → CLEARED
   CONFIRMED: after N occurrences (debounce, configurable).
   AGED: fault not seen for M cycles → auto-clears storage (aged out).
   CLEARED: UDS 0x14 command or diagnostic tool clears DTC memory.

Q86: What is the NvM module and how does it work?
A: Non-volatile Memory Manager. Manages persistent data in EEPROM/Flash:
   NvMBlock: logical block of data (e.g., odometer, calibration, DTC count).
   NvM_ReadAll(): called at startup, reads all blocks to RAM mirror.
   NvM_WriteAll(): called at shutdown, writes changed blocks to NvM.
   Wear leveling: distributes writes across EEPROM cells.
   CRC protection: each block has CRC, verified on read (detects corruption).

Q87–Q100: More AUTOSAR questions
Q87: What is BswM and how does it interact with SWCs?
Q88: How is a new ECU added to a CAN network in AUTOSAR?
Q89: What is the CanSM module?
Q90: What is the DcmDspData block in ARXML?
Q91: How are diagnostic sessions (0x10) configured in AUTOSAR?
Q92: What is WdgM and how does it detect software hang?
Q93: Explain the IoHwAb layer and its role.
Q94: How is a runnable's execution period configured in ARXML?
Q95: What is SOME/IP in AUTOSAR Adaptive?
Q96: How does ara::com work for a publisher-subscriber pattern?
Q97: What is the role of the ExecutionManager in Adaptive?
Q98: What is a Functional Cluster in Adaptive AUTOSAR?
Q99: How is OTA (Over-the-Air update) done in AUTOSAR Adaptive?
Q100: What is the difference between IPDU and PDU?
```

---

## Section C — CAN and Protocols (Q161–Q240)

```
Q161: Explain CAN arbitration.
A: CAN uses bitwise arbitration — dominant bit (0) wins over recessive bit (1).
   Each node monitors bus while transmitting.
   If it transmits a '1' but sees a '0' → another node is transmitting → back off.
   Node with numerically lowest CAN ID wins (0 = dominant = highest priority).
   This is non-destructive: the losing node retries when bus is free.
   Collision vs Ethernet: CAN detects collision and loser backs off.
   Worst-case latency: sum of higher-priority message transmit times.

Q162: What is bit stuffing in CAN?
A: CAN adds a complementary stuffing bit after every 5 consecutive identical bits.
   This ensures sufficient clock transitions for synchronisation.
   Overhead: up to 20% extra bits.
   CAN FD: bit stuffing uses a fixed stuffing bit counter (not run-length) for better predictability.

Q163: What is ISO-TP and when is it used?
A: ISO 15765-2 Transport Protocol. Allows multi-byte messages over CAN (max 8 bytes/frame).
   Single Frame (SF): ≤7 bytes (most OBD-II requests)
   First Frame (FF): first 6 bytes + total length → triggers Flow Control
   Consecutive Frame (CF): subsequent 7-byte blocks (0..15 sequence number)
   Flow Control (FC): receiver tells sender: continue, wait, or abort
   Used for: UDS (ISO 14229), OBD-II, firmware download over CAN.

Q164: What is CAN FD and its advantages?
A: CAN Flexible Data-rate: same arbitration phase as CAN Classic, but faster data phase.
   Max data rate: 8 Mbit/s (vs 1 Mbit/s classic).
   Max payload: 64 bytes (vs 8 bytes classic).
   Use: sensor fusion PDUs (radar object lists), OTA transfer over CAN FD.
   Backward compatible: same CAN IDs, same bus topology.
   Note: ECU must support CAN FD transceiver and controller.

Q165–Q200: More protocol questions
Q165: How does J1939 differ from ISO 11898 CAN?
Q166: What is PGN in J1939?
Q167: Explain UDS SecurityAccess seed/key algorithm.
Q168: What is the difference between physical and functional addressing in UDS?
Q169: What is DoIP and how does it differ from CAN-based diagnostics?
Q170: How does SOME/IP service discovery work?
Q171: What is Ethernet TSN (Time-Sensitive Networking) for automotive?
Q172: What is XCP calibration protocol?
Q173: Describe the LIN protocol and its use cases.
Q174: What is FlexRay and why was it used?
Q175: What is SomeIP-SD (Service Discovery)?
Q176: How is a DBC file structured?
Q177: What is signal aliasing in CAN (when do two signals overlap bits)?
Q178: What is the difference between normal and extended CAN IDs?
Q179: What are the 4 CAN error frame types?
Q180: How does error confinement work in CAN? (TEC/REC counters)
```

---

## Section D — ADAS Algorithms (Q241–Q320)

```
Q241: How does a PID controller work in lane keeping?
A: Error = desired_lane_offset (0) - actual_lane_offset
   P: proportional to current offset → immediate response
   I: integral of offset over time → corrects steady-state error (e.g., road camber)
   D: derivative of offset → damps oscillations, responds to heading angle change
   
   LKA output = Kp*error + Ki*∫error + Kd*(d/dt error)
   Output = steering torque request to EPS.
   Anti-windup: clamp integral ±5 to prevent windup when LKA is in STANDBY/OVERRIDE.

Q242: What is the Kalman Filter used for in radar tracking?
A: Estimates true object state from noisy measurements.
   State: [range, range_rate]. Measurement: radar range (noisy ±0.2m).
   Predict: uses constant velocity model to propagate state forward in time.
   Update: incorporates new radar measurement, weighing it against model uncertainty.
   Output: smooth, low-noise estimate of range and range rate.
   Used in ACC for stable following distance control.

Q243: How do you detect lane markings in a camera image?
A: Pre-processing: Canny edge detection or Sobel gradient
   Line detection: Hough transform detects lines in edge image
   Lane fitting: fit polynomial curve (2nd order) to detected lines
   Lane quality: confidence from line length, contrast, curvature consistency
   ECU output: lane offset (lateral distance from centre), heading angle, lane quality

Q244: Explain the time-to-collision (TTC) calculation.
A: TTC = current_range / closing_speed
   Where: closing_speed = |relative_velocity| (if closing; positive = approaching)
   
   TTC < 2s → AEB warning
   TTC < 1s → AEB intervention (braking)
   
   Limitation: assumes constant relative velocity. In reality, both vehicles may brake.
   Advanced: TTC with deceleration model (two-dimensional safe distance envelope).

Q245–Q280: More algorithm questions
Q245: What is the difference between LKA and LCA (Lane Change Assist)?
Q246: How does blind spot detection work (radar)?
Q247: What is the Hungarian algorithm used for in sensor fusion?
Q248: What is an EKF and when is it needed vs linear KF?
Q249: Explain Mahalanobis distance in track-to-measurement association.
Q250: What is the IMM (Interacting Multiple Model) filter?
Q251: How does pedestrian detection differ from vehicle detection?
Q252: What is the ego motion compensation for radar objects?
Q253: What is optical flow and how is it used in ADAS cameras?
Q254: How is free-space detection done in automotive cameras?
Q255: Explain how ACC handles the cut-in scenario.
Q256: What is headway time and how is it different from headway distance?
Q257: Explain the Responsible Sensitive Safety (RSS) model.
Q258: What is Occupancy Grid Mapping?
Q259: How is map-assisted lane keeping different from camera-only LKA?
Q260: What is SLAM and is it used in automotive production?
```

---

## Section E — Functional Safety & MISRA (Q321–Q400)

```
Q321: What is HARA?
A: Hazard Analysis and Risk Assessment. Identifies hazardous events and assigns ASIL.
   Process: define vehicle situations → identify hazards → assess S/E/C → assign ASIL.
   Output: Safety Goals (top-level safety requirements for the system).

Q322: What is the difference between safety requirement and safety goal?
A: Safety Goal: top-level, technology-agnostic. "LKA shall not cause loss of control."
   Safety Requirement: derived, technology-specific. 
   "LKA SWC shall limit torque_request to ±3 Nm" (software requirement, ASIL C).
   "EPS shall reject LKA commands if torque > 5 Nm" (hardware safety mechanism).

Q323: What is a safety mechanism?
A: A measure that prevents, detects, or mitigates a fault or hazardous event.
   Examples:
   - Watchdog: detects software hang (coverage of CPU lock-up fault)
   - E2E CRC: detects data corruption on CAN bus
   - EPS torque limit: prevents excessive LKA torque
   - Plausibility check: camera range vs radar range — if diff > 30m → deactivate

Q324–Q360: More safety questions
Q324: What is FMEA and how is it done?
Q325: What is FTA (Fault Tree Analysis)?
Q326: What is the difference between systematic and random hardware failures?
Q327: What is safe state and how is it defined for LKA?
Q328: What is a single-point fault and a residual fault (ISO 26262-9)?
Q329: What are PMHF and SPFM metrics?
Q330: What is ASIL decomposition and its independence requirements?
Q331: What is freedom from interference in ISO 26262?
Q332: What is a development interface agreement (DIA)?
Q333: What is proven in use argument in ISO 26262?
Q334: What are the tool confidence levels (TCL) in ISO 26262-8?
Q335: What is the FTTI (Fault Tolerant Time Interval)?
Q336: What is a diagnostic coverage (DC) metric?
Q337: What is SOTIF (ISO 21448)?
Q338: What is the difference between ISO 26262 and SOTIF?
Q339: How does ASPICE relate to ISO 26262?
Q340: What is cybersecurity (ISO/SAE 21434) and how does it interact with safety?
```

---

## Section F — System Design Questions (Q401–Q450)

```
Q401: Design an LKA ECU from scratch. What components would you include?
A: Hardware: 
   - MCU: AURIX TC3xx (dual-core, ASIL-D capable)
   - CAN FD transceiver (TJA1057)
   - Power supply supervisor (voltage monitoring)
   - EEPROM (calibration + DTC storage)
   
   Software layers (AUTOSAR Classic):
   - MCAL: CanDrv, SpiDrv, WdgDrv, NvmDrv
   - BSW: COM, PduR, CanIf, DEM, NvM, WdgM, BswM, OS (AUTOSAR)
   - RTE: auto-generated
   - SWCs: LKA_Controller, CameraInput, DiagnosticsManager, CalibrationManager
   
   LKA SWC: state machine + PID controller + safety monitors
   Safety: E2E on LKA command, EPS timeout monitor, driver override detection

Q402: How would you design an ACC system to handle emergency braking?
A: Normal ACC: gap PID controls throttle and gentle braking (< -3.5 m/s²).
   Emergency: separate AEB function (different software module, ASIL D).
   
   Architecture:
   1. ACC (ASIL B): gap control → throttle/gentle brake request to ESC
   2. AEB (ASIL D): TTC < 1s threshold → hard brake request to ESC (highest priority)
   3. ESC (ASIL D): arbitrates between ACC and AEB — highest deceleration wins
   4. Driver override: driver brake pedal > 30% → ESC ignores ACC/AEB
   
   Timing: Radar cycle 50ms. AEB must activate within 200ms of TTC < 1s.
   E2E protected AEB message: 16-bit CRC + 8-bit counter.

Q403: Design a CAN gateway ECU for an ADAS domain.
A: Routes signals between multiple CAN buses and Ethernet backbone.
   Hardware: NXP S32G (network processor, 100BASE-T1, CAN FD × 4)
   
   Functions:
   1. Signal routing: BCM → ADAS_ECU (speed, gear, ignition state)
   2. Protocol translation: CAN FD → SOME/IP (for Adaptive ECUs)
   3. Filtering: ADAS_ECU not allowed to write to body BCM signals (security)
   4. Gating: safety signals only routed in NORMAL mode, blocked in FACTORY mode
   5. Diagnostics gateway: route UDS requests from OBD-II port to target ECU

Q404–Q420: More design questions
Q404: Design a watchdog strategy for a dual-core ADAS ECU.
Q405: How would you architect an OTA update mechanism for an ADAS ECU?
Q406: Design a sensor fusion pipeline for radar + camera in 50ms budget.
Q407: How would you test the ACC cut-in scenario in HIL?
Q408: Design the communication architecture for a Level 3 highway assist system.
Q409: How would you debug a CAN bus off condition in the field?
Q410: What tradeoffs exist between polling vs interrupt-driven CAN reception?
```

---

## Section G — Debugging and RCA (Q451–Q500)

```
Q451: How do you debug a CAN message that is received but processed with wrong values?
A: Step 1: Capture raw CAN frame with Vector CANalyzer or CANoe
   Step 2: Manually decode bytes vs DBC file → check if raw data is correct
   Step 3: If raw data wrong → sender side bug (check encoding in other ECU)
   Step 4: If raw data correct but decoded wrong → check DBC signal definition
           (byte order mismatch Intel/Motorola is most common source)
   Step 5: Check bit stuffing count — CAN FD vs Classic mismatch can corrupt timing
   Step 6: Check signal factor/offset/scaling in COM configuration (ARXML)

Q452: How do you diagnose an ECU that intermittently resets?
A: Suspect: watchdog reset, supply voltage glitch, stack overflow, exception.
   
   Step 1: Read ECU reset reason register (RSTSTAT in AURIX TC3xx)
           0x04 = watchdog reset, 0x08 = power-on reset, etc.
   Step 2: Check DTC log for DEM events before reset (if NvM write completes)
   Step 3: Stack watermark analysis: was stack near overflow before reset?
   Step 4: Voltage monitoring: log supply voltage during reset (NvM or CAN frame)
   Step 5: Watchdog: was a specific task not servicing its WdgM checkpoint?
           → task timing problem, blocking call, priority starvation

Q453: Camera signal sometimes shows LaneQuality=LOST at 120 km/h. How do you RCA?
A: Possible causes: motion blur (too fast), sun position (backlight), road surface (no contrast)
   
   Investigation:
   1. Correlate timestamps: when does LOST occur? Time of day? Road type?
   2. Check camera exposure time configuration (too long → motion blur at speed)
   3. Review image processing algorithm sensitivity parameter in camera calibration
   4. HIL test: inject synthetic camera images with reduced contrast → does quality drop?
   5. Check DEM: is camera timeout DTC set? If yes → COM Rx timeout (different root cause)
   
   Fix candidates:
   - Adjust exposure time schedule (speed-dependent)
   - Tune lane quality confidence threshold
   - Add heading angle plausibility (if camera lost but IMU heading stable → keep LKA active)

Q454–Q500: More debugging questions
Q454: How do you debug a LKA oscillation (hunting) issue?
Q455: Describe RCA for an ACC that overshoots target speed.
Q456: How do you diagnose a CAN bus-off condition?
Q457: What tools do you use to debug AUTOSAR BSW stack?
Q458: How do you find a memory corruption bug in ECU C++ code?
Q459: How do you debug a race condition between two OSEK tasks?
Q460: What is a core dump in automotive context and how do you use it?
Q461: How do you debug a signal that has wrong byte order?
Q462: Describe a systematic approach to timing analysis (WCET measurement).
Q463: How do you debug a diagnostic (UDS) request that gets no response?
Q464: How do you perform failure injection testing on an ECU?
Q465: What is ETK/XETK in calibration and debugging?
Q466: How do you verify a Kalman filter convergence on target hardware?
Q467: Describe your approach to debugging a function that returns NaN.
Q468: How do you debug a CRC failure on a safety-critical CAN message?
Q469: What is a scope probe used for in ECU debugging?
Q470: How do you debug a missing OSEK alarm (task not activating)?
```
