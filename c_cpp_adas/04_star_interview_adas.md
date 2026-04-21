# ADAS C/C++ — STAR Format Interview Scenarios

> **Roles:** ADAS Software Engineer, Sensor Fusion Developer, Safety Software Engineer,
>             Embedded C++ Developer (ADAS domain), Autonomous Driving Software Lead

---

## STAR Scenario 1 — Kalman Filter Divergence Under High-Speed Manoeuvres

**Question:** *"Tell me about a time you debugged a tracking algorithm failure in a real vehicle scenario."*

**SITUATION:**
During high-speed motorway validation testing at 130 km/h, the radar object tracker was losing track of lead vehicles during lane changes — the Kalman filter would diverge and assign a new track ID instead of maintaining continuity. This caused the ACC system to briefly "forget" the lead car and accelerate before reacquiring, which was both unsafe and a SOTIF violation.

**TASK:**
Root-cause the tracker divergence and fix it within the sprint to meet the motorway validation milestone.

**ACTION:**
- Replayed the validation drive log in the SIL (Software-in-the-Loop) environment using MathWorks Simulink Sensor Fusion Toolbox
- Observed that during lane changes, the radar target's lateral measurement (Y position) would jump 1.5–2.0 m in one 10 ms cycle — exceeding the Mahalanobis distance gate of the tracker
- The gate was set using a fixed Euclidean distance (3 m) — not accounting for uncertainty:
  ```c
  /* BEFORE — Euclidean gate: misses fast-moving targets */
  float dist = sqrtf(dx*dx + dy*dy);
  if (dist < ASSOC_GATE_M) { /* associate */ }
  ```
- Replaced with **Mahalanobis distance gating**, which normalises by the innovation covariance (accounts for Kalman uncertainty):
  ```c
  /* AFTER — Mahalanobis gate: robust to uncertainty */
  float S[2][2] = { /* innovation covariance */ };
  float y[2]    = {dx, dy};
  float det_S   = S[0][0]*S[1][1] - S[0][1]*S[1][0];
  float inv_S[2][2] = { /* 2x2 inverse */ };
  float mahal = y[0]*(inv_S[0][0]*y[0] + inv_S[0][1]*y[1]) +
                y[1]*(inv_S[1][0]*y[0] + inv_S[1][1]*y[1]);
  if (mahal < 9.21f) { /* Chi-squared gate, 99% confidence */ }
  ```
- The 9.21 threshold comes from the chi-squared distribution with 2 DOF at 99% confidence
- Additionally found the process noise matrix Q was under-tuned (too low lateral uncertainty), causing the filter to reject legitimate lateral measurements. Increased `Q[1][1]` from 0.1 to 0.5 m²/s²
- Re-validated over 200+ km of motorway log replay — zero track loss events

**RESULT:**
- Track continuity during lane changes improved from **78% → 99.6%** in log replay
- ACC "forget and accelerate" incidents eliminated from validation log
- Fix documented in the tracker algorithm design document and reviewed in ISO 26262 SWE.4 review
- Process noise tuning methodology now included in the project tracking component guidelines

---

## STAR Scenario 2 — AEB False Activation on Overhead Motorway Gantries

**Question:** *"Describe a situation where your ADAS system behaved unexpectedly and how you solved it."*

**SITUATION:**
During motorway validation, the AEB system triggered hard braking (0.6g deceleration) three times on overhead motorway gantries — metal structures across all lanes. At 110 km/h, this was a safety incident. The system had passed all test-track validation but failed on real-world infrastructure.

**TASK:**
Identify the root cause, prevent recurrence, and update the SOTIF analysis — classified as priority 1 (vehicle must be quarantined from motorway use until resolved).

**ACTION:**
- Extracted the black-box sensor data log from the incident ECU — analysed in MATLAB
- Radar was detecting the gantry overhead beam as a stationary object with:
  - Range: 45 m, Azimuth: 0°, Elevation: **+6°** (overhead)
  - Radial velocity: 0 m/s (stationary)
  - Confidence: 87%
- The AEB algorithm was processing targets without checking **elevation angle** — treating the gantry exactly like a stationary car:
  ```c
  /* BEFORE — no elevation filter */
  if (target->range_m < 50.0f &&
      target->radial_vel_ms >= 0.0f &&   /* stationary or approaching */
      target->confidence > 70U) {
      compute_aeb_intervention(target);
  }
  ```
- Added a **stationary target elevation filter** — overhead stationary objects with elevation > +4° are classified as infrastructure:
  ```c
  /* AFTER — elevation and height plausibility */
  float obj_height_m = target->range_m * sinf(target->elevation_rad);

  #define AEB_MAX_RELEVANT_HEIGHT_M  2.5f   /* Max relevant object top: car roof ~1.5m */
  #define AEB_ELEVATION_GANTRY_RAD   0.07f  /* ~4 degrees */

  bool is_gantry = (target->elevation_rad > AEB_ELEVATION_GANTRY_RAD &&
                    obj_height_m > AEB_MAX_RELEVANT_HEIGHT_M &&
                    fabsf(target->radial_vel_ms) < 0.5f);

  if (!is_gantry) {
      compute_aeb_intervention(target);
  }
  ```
- Cross-checked fix against a database of 50 known gantry sites in the test fleet's coverage area
- Updated SOTIF hazardous event analysis — "Overhead stationary infrastructure" added as known triggering condition with coverage measure

**RESULT:**
- Zero AEB false activations in 15,000 km post-fix validation (including 200+ motorway gantry crossings)
- SOTIF analysis updated; gantry scenario added to the standard regression test suite
- Change reported to the OEM as a safety-relevant software update (SSCM: Software Configuration Management change)
- Presented root cause analysis to the cross-programme ADAS safety board — fix adopted across two other vehicle platforms sharing the same radar processing library

---

## STAR Scenario 3 — Race Condition in Fusion-to-FCW Data Handoff

**Question:** *"Tell me about a concurrency bug you encountered in a safety-critical embedded system."*

**SITUATION:**
An intermittent FCW false alarm was occurring once every 4–6 hours during continuous vehicle operation. The alarm showed TTC = 0.8 s with no visible obstacle — drivers were alarmed and filing complaints. Reproducing the bug was extremely difficult.

**TASK:**
Root-cause the intermittent FCW false alarm. The bug had to be found and fixed before the OEM customer's fleet trial in two weeks.

**ACTION:**
- Enabled RTOS event tracing using Percepio Tracealyzer with the production ECU
- After 18 hours of instrumented driving, captured the race condition:
  - Fusion task was writing `FusedObjectList_t` (64 bytes, partial write) while the FCW task was simultaneously reading it — the FCW task read a **half-written structure** where `object[0].ttc_s` was overwritten with a new TTC of 0.8 s but `object[0].is_in_path` was still `0` from the previous cycle
  - Without the in-path flag, the FCW logic still triggered on TTC alone:
    ```c
    /* BUGGY — reading ttc without atomic access guarantee */
    if (g_fused_list.objects[0].ttc_s < FCW_TTC_ALERT_S) {
        trigger_fcw();  /* Fired on corrupted partial write */
    }
    ```
- Root cause: `xQueueOverwrite()` was being called correctly for the queue, but a **second direct pointer** `g_fused_list` was also being used as a shortcut and was NOT protected by a mutex
- Fix 1: Removed the direct pointer entirely — all access via `xQueuePeek()` which uses a copy
- Fix 2: Added double-buffer pattern (ping-pong) for the fused object list, with an atomic index:
  ```c
  static FusedObjectList_t s_fused_ping_pong[2U];
  static volatile uint8_t  s_active_buffer = 0U;

  /* Writer (fusion task): always writes to inactive buffer */
  void fusion_publish(const FusedObjectList_t* data) {
      uint8_t write_buf = 1U - s_active_buffer;
      memcpy(&s_fused_ping_pong[write_buf], data, sizeof(FusedObjectList_t));
      s_active_buffer = write_buf;  /* Atomic pointer swap */
  }

  /* Reader (FCW task): reads from active buffer (snapshot) */
  void fcw_get_objects(FusedObjectList_t* out) {
      memcpy(out, &s_fused_ping_pong[s_active_buffer], sizeof(FusedObjectList_t));
  }
  ```
- Note: On ARM Cortex-A with cache coherency, `std::atomic<uint8_t>` was used for the index

**RESULT:**
- False alarm eliminated — zero recurrences in 500+ hours post-fix soak test (representing ~8M FCW evaluation cycles)
- Pattern documented as a coding guideline: "Never use direct pointers to shared sensor data — always use queue or double-buffer"
- ASPICE SWE.3 code review checklist updated to flag direct shared-memory access in RTOS contexts
- Fleet trial proceeded on schedule with a clean safety record

---

## STAR Scenario 4 — SOTIF Gap: Pedestrian Detection Fails in Backlit Conditions

**Question:** *"Tell me about a time you improved an ADAS function's robustness against edge cases."*

**SITUATION:**
Post-SOP field data from a customer fleet showed elevated pedestrian detection miss rates in late-afternoon, low-sun-angle conditions. The camera-based pedestrian detector (CNN) performed normally in lab/test-track conditions but failed when pedestrians were backlit (silhouetted).

**TASK:**
Analyse field data, characterise the SOTIF known unsafe scenario, and implement a system-level mitigation that could be deployed via OTA update.

**ACTION:**
- Retrieved 200 near-miss event logs from the fleet's black-box data (stored when FCW did not activate but AEB did in fallback mode)
- Wrote a Python + C++ analysis pipeline to characterise the failure mode:
  ```cpp
  /* Camera exposure metric */
  float compute_contre_jour_index(const uint8_t* image, uint16_t w, uint16_t h) {
      float sky_luminance   = mean_luminance(image, 0, 0, w, h/3);     /* Top third */
      float ground_luminance = mean_luminance(image, 0, 2*h/3, w, h);  /* Bottom third */
      return sky_luminance / (ground_luminance + 1.0f); /* > 5 = backlit */
  }
  ```
- Found: when `contre_jour_index > 5.0`, pedestrian detection confidence dropped from 82% to 41%
- Implemented a **sensor confidence-based system adaptation**:
  - When backlit condition detected: reduce FCW pedestrian TTC threshold from 2.5 s to 3.5 s (earlier activation)
  - Increase radar contribution weight in fusion for pedestrian objects
  - Activate driver attention request (haptic steering wheel feedback)
  - Downgrade max vehicle speed from 80 km/h to 60 km/h in urban areas:
  ```c
  void adapt_to_backlit_conditions(float contre_jour_idx) {
      if (contre_jour_idx > 5.0f) {
          system_set_fcw_ttc_threshold(OBJ_CLASS_PEDESTRIAN, 3.5f);
          system_set_max_accel(0.5f);    /* Gentle only */
          set_radar_fusion_weight(0.7f); /* Increase radar vs camera */
          trigger_driver_attention_request();
          Dem_SetEventStatus(DEM_EVENT_CAMERA_BACKLIT, DEM_EVENT_STATUS_FAILED);
      } else {
          system_set_fcw_ttc_threshold(OBJ_CLASS_PEDESTRIAN, 2.5f);
          set_radar_fusion_weight(0.5f);
      }
  }
  ```
- Updated SOTIF analysis: "Low-angle sun backlit pedestrian" moved from "unknown unsafe scenario" to "known unsafe scenario with coverage"

**RESULT:**
- OTA update deployed to 2,400 vehicles in 6 weeks
- Fleet pedestrian near-miss event rate reduced by **68%** in backlit conditions
- SOTIF HARA updated; scenario accepted by safety assessor as adequately mitigated
- Paper on the field-data-driven SOTIF mitigation process submitted to the ADAS Safety conference

---

## STAR Scenario 5 — Refactoring Spaghetti C to Testable C++ ADAS Module

**Question:** *"Give an example of a major code improvement you drove in an embedded automotive project."*

**SITUATION:**
Inherited an FCW/AEB C codebase from a previous contractor — 8,000 lines in a single `fcw_aeb.c` file with over 200 global variables, no unit tests (unit test coverage: 0%), and ASPICE SWE.4 review failing due to absent traceability between requirements and code.

**TASK:**
Refactor to a maintainable, testable, MISRA-compliant C++ architecture within one programme increment (8 weeks) without breaking system behaviour.

**ACTION:**
- Started by writing **characterisation tests** against the existing binary outputs (record and replay) using GoogleTest — established "golden" expected outputs before touching any code
- Decomposed the monolith into 6 classes: `ObjectListManager`, `TtcCalculator`, `FcwLogic`, `AebLogic`, `DriverNotifier`, `BrakeActuator`
- Key example — `TtcCalculator` extracted with full test coverage:
  ```cpp
  class TtcCalculator {
  public:
      static constexpr float NO_COLLISION = 99.0f;

      float compute(float distance_m, float closing_speed_ms) const {
          if (closing_speed_ms <= 0.0f) return NO_COLLISION;
          if (distance_m < 0.0f)       return 0.0f;
          return distance_m / closing_speed_ms;
      }

      float compute_with_ego_decel(float dist_m, float rel_v_ms,
                                    float ego_decel_ms2) const {
          /* Account for available decel: PRT (0.5s) + braking distance */
          float v = rel_v_ms;
          if (std::fabsf(ego_decel_ms2) < 0.1f) return compute(dist_m, rel_v_ms);
          /* Physical minimum stopping distance */
          float d_stop = v * 0.5f + (v * v) / (2.0f * ego_decel_ms2);
          return (d_stop <= dist_m) ? NO_COLLISION : dist_m / rel_v_ms;
      }
  };
  ```
- Each class had its own unit test file — total: 127 unit tests
- Enabled `clang-tidy` with MISRA subset checks in CI pipeline
- Added `[[nodiscard]]` to all safety output functions

**RESULT:**
- Unit test coverage: **0% → 84%** (branch coverage)
- ASPICE SWE.4 code review passed with zero major findings
- Build time reduced 40% (smaller, more cacheable translation units)
- Next feature (BSD integration) implemented in 3 days by new engineer — previously similar changes took 3 weeks in the monolith
- Recognised as "Best Engineering Practice" within the ADAS programme

---

## Quick Reference Table — ADAS C/C++ Technical Q&A

| Question | Answer |
|---|---|
| What is TTC and how do you compute it? | Time-To-Collision = relative distance / closing speed. Valid only when closing speed > 0 |
| What is sensor fusion? | Combining outputs of multiple sensors (radar + camera + LiDAR) to produce a more accurate, reliable object list |
| What is a Kalman filter? | Optimal linear estimator: predict state forward, update with measurement, minimise estimation error covariance |
| What is SOTIF (ISO 21448)? | Safety Of The Intended Functionality — addresses risks from performance limitations (not hardware faults) |
| What ASIL is AEB? | ASIL D (highest) — unintended/missed emergency braking at highway speed is life-threatening |
| What is CFAR? | Constant False Alarm Rate — adaptive radar thresholding based on local noise floor |
| What is Mahalanobis distance? | Distance normalised by covariance — accounts for measurement uncertainty in data association |
| What is a sensor gating strategy? | Reject sensor measurements outside a statistical bound (Mahalanobis gate) before Kalman update |
| Why double-buffering for sensor data? | Prevents race conditions between sensor writer task and consumer task without expensive mutex |
| What is THW (Time Headway)? | THW = distance / ego_speed — minimum safe following time (typically 1.5–2.5 s) |
| What is NCAP? | New Car Assessment Programme — defines standardised ADAS test scenarios (FCW, AEB, LKA) |
| What is V2X? | Vehicle-to-Everything — wireless communication between vehicles, infrastructure, and pedestrians |
| What is the difference between FCW and AEB? | FCW = warning only (driver acts). AEB = autonomous braking if driver does not respond |
| What is a bounding box in camera detection? | Rectangle [x, y, width, height] enclosing a detected object in the camera image |
| What is NMS (Non-Maximum Suppression)? | Post-processing step in object detection CNNs to remove duplicate overlapping bounding boxes |

---

*File: 04_star_interview_adas.md | c_cpp_adas learning series*
