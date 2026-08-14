# Part 25 — STAR Scenarios

STAR format: **S**ituation → **T**ask → **A**ction → **R**esult

---

## Scenario 1 — AEB False Trigger in Vehicle Test

**Situation:** During highway integration testing at 100 km/h, the AEB system triggered a hard brake with no object present, causing a near-accident.

**Task:** Identify root cause immediately; prevent recurrence before further vehicle tests.

**Action:**
- Immediately stopped all vehicle tests for safety
- Captured all relevant data: CAN trace, ADAS log, radar object list, camera recording
- Analyzed ADAS log: found radar object list showed a ghost object at 15m for 80ms
- Traced to radar firmware bug: multipath reflection from overhead bridge counted as object
- Worked with radar supplier to reproduce on HIL with bridge simulation model
- Verified fix in HIL before allowing vehicle tests to resume

**Result:** Root cause confirmed in 2 days; radar firmware updated; HIL regression passed; vehicle tests resumed safely with no recurrence.

**How to tell this in an interview:**
Emphasize: immediate stop for safety, systematic data-driven analysis, cross-functional collaboration (you + radar supplier + safety team), structured root cause approach, prevention through HIL regression.

---

## Scenario 2 — CAN Bus-Off Causing Cluster Blackout

**Situation:** During cold-weather testing (-25°C), the instrument cluster went blank intermittently. Occurred 3 times in 2 days; could not reproduce at room temperature.

**Task:** Identify root cause and fix before winter testing window closed (1 week).

**Action:**
- Reviewed DTC log from cluster: DTC for CAN bus-off event
- Checked CAN bit timing configuration vs actual CAN transceiver spec at -25°C
- Found: CAN transceiver propagation delay increased at low temperature, pushing bit timing out of spec
- Adjusted CAN bit timing parameters (increased propagation segment) to accommodate cold temperature
- Regression tested in climatic chamber: -40°C to +85°C sweep

**Result:** Fixed in 3 days; no further bus-off events across temperature range; delivered to winter test program on time.

---

## Scenario 3 — Supplier ECU Software Delivered Late

**Situation:** Radar ECU SW v1.3.0 was 3 weeks late from supplier. HIL integration milestone was at risk.

**Task:** Maintain HIL milestone delivery while waiting for supplier SW.

**Action:**
- Created CANoe simulation of Radar ECU (simulated object list on CAN FD) using last available DBC
- Integrated all other ECUs (ADAS DC, Brake ECU, Cluster) on HIL with simulated radar
- Ran 80% of planned HIL test cases (those not dependent on real radar behavior)
- Set up integration test environment ready for real radar SW on day of delivery
- When v1.3.0 arrived: ran in 2 days instead of 2 weeks

**Result:** Delivered HIL baseline 1 week late instead of 3 weeks late; parallel work plan recovered most of the delay.

---

## Scenario 4 — Critical Defect 2 Days Before Release

**Situation:** 2 days before the software release deadline, a critical defect was found: UDS ReadDTCInformation returned corrupted data when 50+ DTCs were active simultaneously.

**Task:** Assess risk, fix if possible, or define mitigation before release.

**Action:**
- Immediate triage: reproduced with 55 DTCs active in HIL
- Root cause in 4 hours: Dcm buffer size too small for large DTC list → buffer overflow → response truncated
- Fix: increase Dcm response buffer in ECUC; regenerate BSW; rebuild; flash
- Regression: re-run full diagnostics test suite (2 hours)
- Verified: no buffer overflow with 100 active DTCs

**Result:** Fixed and verified within 18 hours; release delivered on schedule. Documented buffer size calculation in integration checklist for future projects.

---

## Scenario 5 — OTA Update Bricked 50 Vehicles

**Situation:** An OTA campaign for IVI SW v3.1.0 was deployed to a test fleet. 50 of 500 vehicles became unresponsive (black screen, no boot) after the update.

**Task:** Recover affected vehicles; identify root cause; prevent future occurrence.

**Action:**
- Immediate: pause OTA campaign to prevent more affected vehicles
- Recovery: dispatched technicians to dealer; reflashed via USB fallback (standard OBD port)
- Root cause analysis: new IVI firmware had wrong partition table size — overwrote bootloader in 10% of vehicles with different HW revision
- Found: HW revision check missing in OTA manifest
- Fix: add HW variant check in OTA deployment validation; update packaging script
- Verified fix on all 5 HW variants in lab before resuming campaign

**Result:** All 50 vehicles recovered within 3 days; campaign resumed with 0 further failures; process improvement added to OTA checklist.

---

## Scenario 6 — Ethernet Gateway VLAN Misconfiguration

**Situation:** After upgrading the central gateway ECU to a new SW baseline, ADAS radar objects no longer appeared in the instrument cluster ADAS visualization.

**Task:** Identify and fix the cross-ECU communication break.

**Action:**
- Wireshark capture on Ethernet: OfferService multicast visible but cluster not receiving events
- Traced: radar object SOME/IP events on VLAN 100; cluster on VLAN 200; no routing between
- Confirmed gateway SW upgrade had changed default VLAN routing table
- Updated gateway VLAN routing configuration: added VLAN 100→200 route for ObjectListService
- Verified in integration bench: cluster ADAS display restored

**Result:** Fixed in 4 hours; identified missing VLAN routing test in integration test suite; added test case to prevent future recurrence.

---

## Scenario 7 — Requirements Changed 2 Weeks Before Freeze

**Situation:** OEM changed the requirement for cluster boot-to-telltale time from 2 seconds to 500ms — 2 weeks before requirements freeze.

**Task:** Assess technical feasibility, propose solution, implement without breaking other features.

**Action:**
- Profiled current boot sequence: Linux init took 1.8 seconds alone
- Identified quick wins: disabled unnecessary init services (BT, Wi-Fi) from early boot path
- Split boot into two phases: minimal boot (telltales only) in 450ms; full boot in 2s
- Used systemd targets: emergency.target for telltales, default.target for full UI
- Implemented Qt Safe Renderer for telltale display independent of Qt full app

**Result:** 500ms telltale display achieved; full cluster functional at 1.9s; OEM accepted solution; no regression on other features.

---

## Scenario 8 — Production Issue: DTC Storm After Software Update

**Situation:** After a field SW update (OTA v2.3.1) was deployed to 8,000 vehicles, the service center received calls about warning lights. DTC analysis showed 15 new DTCs set on every affected vehicle.

**Task:** Identify root cause; issue fix; prevent customer impact.

**Action:**
- Reproduced in lab with the exact OTA package
- Found: new SW version changed NvM block format without migration path — NvM data invalid after update → all NvM-dependent DEM events initialized to "failed"
- Developed SW v2.3.2: NvM migration code to convert old format to new
- Tested migration path: update from v2.3.0 → v2.3.1 → v2.3.2 in lab; verified no DTC storm
- Released v2.3.2 OTA; included migration; DTC storm eliminated

**Result:** All 8,000 vehicles updated with fix within 1 week; service calls dropped to zero; NvM migration testing added to OTA regression suite.

---

## Scenario 9 — Cross-Team Conflict on Interface Definition

**Situation:** ADAS team and Brake ECU team disagreed on the latency requirement for the AEB brake request CAN FD message. ADAS expected 5ms; Brake ECU team claimed they needed 20ms for processing.

**Task:** Resolve the conflict and reach an agreed specification.

**Action:**
- Organized a joint technical meeting with both teams + system engineer + safety manager
- Asked each team to present their latency requirement with technical justification
- ADAS: AEB end-to-end latency budget allows max 5ms for actuator message delay
- Brake ECU: 20ms needed for internal processing pipeline
- Facilitated compromise: ADAS sends AEB pre-request (predictive) at T-0ms for ADAS decision, hard brake request at T+5ms for actual braking
- Brake ECU: processes pre-request to prepare; executes on hard brake request
- Both teams signed off; updated ICD and CAN matrix; tested in HIL

**Result:** Both teams' constraints met; system latency requirement achieved; no delay to project schedule.

---

## Scenario 10 — Memory Leak Causing ECU Reset Every 48 Hours

**Situation:** Field report from 200 vehicles: ADAS ECU resets every 48–72 hours. Customers reported brief loss of ADAS features.

**Task:** Reproduce and fix the memory leak without access to production vehicles.

**Action:**
- Reproduced in HIL: ran for 60 hours continuously; observed increasing memory usage
- Used Trace32 to monitor heap usage: growing at ~0.5 KB/hour
- Added memory allocation tracking to heap allocator
- Found: object detection module allocated temporary buffers for each video frame but did not free one buffer per 10th frame (off-by-one in cleanup loop)
- Fixed: corrected loop bounds in cleanup function
- Verified: 100-hour HIL soak with stable memory usage

**Result:** Fix deployed via OTA; field resets eliminated; added 100-hour soak test to HIL regression suite.

---

## Scenario 11 — Integration Metric Showing Regression Trend

**Situation:** Weekly integration metrics showed P2 defect injection rate increasing for 3 consecutive weeks (from 2/week to 8/week).

**Task:** As Integration Lead, identify systemic cause and reverse the trend.

**Action:**
- Analyzed defect types: 60% were CAN signal configuration errors (wrong endianness, wrong bit position)
- Root cause: new engineers added to project had limited CAN DBC knowledge; no formal review process for DBC changes
- Actions taken:
  1. Added DBC change review step to PRs (required CAN expert sign-off)
  2. Created automated DBC validation script in CI pipeline
  3. Ran 2-hour CAN signal configuration training for team
- Results visible after 2 sprints

**Result:** Defect injection rate dropped back to 2/week within 3 weeks; DBC validation script prevented 4 further defects in CI.

---

## Scenario 12 — ADAS Sensor Timestamp Synchronization Issue

**Situation:** ADAS fusion showed occasional ghost objects (objects appearing/disappearing with no physical cause) under specific highway driving conditions.

**Task:** Identify cause of ghost objects; fix and validate.

**Action:**
- Captured ADAS log: ghost objects appeared at 200ms intervals
- Checked sensor timestamps: camera timestamps had a 200ms jitter spike every 5 seconds
- Traced to: camera gPTP sync daemon restarting every 5 seconds due to a systemd watchdog misconfiguration
- Fixed: corrected systemd watchdog timeout for gPTP daemon; synchronized camera trigger hardware
- Verified: ghost objects eliminated in 8-hour highway drive test

**Result:** Fusion accuracy improved; no ghost objects in 500km validation drive; gPTP daemon monitoring added to system health checks.

---

## How a Senior Engineer Communicates STAR Scenarios

**Key principles for senior-level STAR responses:**
1. **Show initiative:** You identified the problem proactively or took ownership beyond your role
2. **Show technical depth:** Explain the root cause with specifics, not just "I fixed a bug"
3. **Show leadership:** You organized a meeting, facilitated resolution, trained the team
4. **Show process improvement:** What did you change so it won't happen again?
5. **Quantify the result:** "Reduced defect rate by 75%" > "improved quality"
6. **Show cross-functional collaboration:** Mention other teams, roles, suppliers

**Template for interview delivery:**
- 30 seconds: Situation context
- 30 seconds: Your specific task/responsibility
- 2–3 minutes: Action — be specific, technical, first-person ("I analyzed...", "I proposed...")
- 30 seconds: Result — quantified, business impact

---

*Next: [Part 26 — Capstone Project](part-26-capstone-project.md)*
