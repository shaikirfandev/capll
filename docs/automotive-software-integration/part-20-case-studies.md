# Part 20 — Real-World Case Studies

---

## Case Study 1 — ADAS ECU Integration

**Objective:** Integrate ADAS Domain Controller (ADC) into a mid-size sedan platform.

**Architecture:**
- ADC: Qualcomm Snapdragon Ride (SoC), Adaptive AUTOSAR + Linux
- 1× Front camera (100BASE-T1), 4× Corner radar (CAN FD), 1× Front radar (Ethernet)
- Brake ECU (CAN FD), EPS ECU (CAN FD)

**Integration Sequence:**
1. ADC Linux bring-up: Yocto build, camera/radar drivers
2. SOME/IP-SD: ADC offers ObjectListService
3. CAN FD integration: Brake and EPS actuator requests
4. HIL: 500 automated test cases
5. Vehicle: closed-course AEB tests at 30, 50, 80 km/h

**Key Defect Found:**
Object detection CNN running at 25Hz but fusion expected 30Hz → timestamp gaps → false AEB triggers

**Fix:** Align CNN output rate to 30Hz via frame rate configuration

---

## Case Study 2 — ACC Integration

**Objective:** Implement Adaptive Cruise Control on SUV.

**Architecture:** Radar ECU → CAN FD → ADAS DC → ACC algorithm → Throttle ECU + Brake ECU

**Integration challenge:** Speed oscillation — ACC overshot target speed by 8 km/h.

**Root Cause:** Radar object velocity estimate had 0.5m/s offset due to uncorrected Doppler bias.

**Fix:** Apply offset correction in radar driver; re-run ACC vehicle tests.

---

## Case Study 3 — AEB Integration

**Objective:** Validate AEB at system level per Euro NCAP AEB Car-to-Car protocol.

**Tests performed:**
- CCRs (Car-to-Car Rear stationary): 10, 20, 30, 40, 50 km/h
- CCRm (Car-to-Car Rear moving): various speed differentials
- CCRb (Car-to-Car Rear braking)

**Key finding:** AEB triggered 80ms late at 50 km/h.

**Root Cause:** CAN FD message routing delay through gateway — 50ms instead of 5ms.

**Fix:** Move AEB brake request to dedicated direct CAN FD link (no gateway); latency reduced to 3ms.

---

## Case Study 4 — Digital Cluster Integration

**Objective:** Integrate digital TFT cluster with ADAS visualization.

**Stack:** Linux on Renesas R-Car H3, Qt 5.15, Wayland, SOME/IP

**Integration challenge:** ADAS object overlay flickered when >3 objects displayed simultaneously.

**Root Cause:** SOME/IP event rate 30Hz, Qt rendering 60Hz — event bursts caused scene graph rebuild every other frame.

**Fix:** Implement object list interpolation in cluster app; smooth rendering at 60Hz.

---

## Case Study 5 — Android Automotive IVI Integration

**Objective:** Integrate AAOS head unit with vehicle CAN bus signals.

**VHAL integration:**
- CAN gateway → SOME/IP → VHAL backend → Android CarService → IVI apps

**Key defect:** Vehicle speed in IVI UI showed 0 after cold start for 3 seconds.

**Root Cause:** SOME/IP service discovery took 2.5 seconds; VHAL backend not subscribed yet.

**Fix:** Pre-configure static SOME/IP service endpoint; remove SD delay.

---

## Case Study 6 — TCU Integration

**Objective:** Integrate TCU with cloud fleet management backend.

**Integration challenge:** Vehicles lost MQTT connection when driving through tunnels (cellular loss for 30s).

**Root Cause:** MQTT client did not implement re-connection with exponential backoff; gave up after 3 retries.

**Fix:** Implement reconnection with jitter + exponential backoff; use MQTT QoS 1 for critical telemetry.

---

## Case Study 7 — CAN-to-Ethernet Gateway Integration

**Objective:** Integrate central gateway bridging CAN powertrain signals to Ethernet backbone.

**Challenge:** SOME/IP "VehicleSpeedService" showed stale data after engine restart.

**Root Cause:** CAN signal timeout detection not implemented in gateway — last received value held indefinitely.

**Fix:** Implement CAN signal timeout (150ms) in gateway; publish "invalid" flag when timed out.

---

## Case Study 8 — OTA Integration

**Objective:** Deploy SW update to ADAS ECU across 50,000 field vehicles.

**Staged rollout:**
- Stage 1: 500 vehicles (fleet test vehicles) — success rate 99.6%
- Stage 2: 5,000 vehicles — success rate 99.1%
- Stage 3: Full rollout

**Issue found at Stage 2:** 0.9% of vehicles stuck at "Installing" — caused by battery voltage dropping below threshold during installation.

**Fix:** Implement battery voltage monitoring during OTA; pause and retry if voltage drops.

---

## Case Study 9 — ECU Diagnostics Integration

**Objective:** Implement full UDS diagnostics on new Body ECU.

**Integration challenge:** DTC for window motor overload (0x200311) cleared successfully via 0x14 but reappeared immediately.

**Root Cause:** Application continuously called `Dem_ReportErrorStatus(FAILED)` in init code path.

**Fix:** Move Dem report to post-initialization; add debounce counter (3 occurrences before set).

---

## Case Study 10 — Multi-ECU Domain Controller Integration

**Objective:** Integrate ADAS domain controller with 7 sensor ECUs and 3 actuator ECUs simultaneously.

**Network:**
- 2× 100BASE-T1 Ethernet rings (sensor network + backbone)
- 3× CAN FD buses (actuators, body, diagnostics)

**Challenge:** Time-of-flight of GNSS timestamps inconsistent across 6 cameras.

**Root Cause:** 3 cameras upgraded to newer firmware with different gPTP delay offset.

**Fix:** Re-calibrate gPTP delay asymmetry for all cameras; document firmware-specific offset values.

---

*Next: [Part 21 — Senior/Lead/Architect Level](part-21-senior-lead-architect.md)*
