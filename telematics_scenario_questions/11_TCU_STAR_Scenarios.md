# TCU / Telematics — 50 STAR Interview Scenarios
## Situation · Task · Action · Result

> Format: Each scenario is written as a detailed STAR answer you can adapt for interviews.
> Topics span: OTA testing, cellular connectivity, remote diagnostics, GNSS, eCall,
> power management, CAN gateway, security, HIL bench work, defect investigation, and process.

---

## Index

| # | Topic | Title |
|---|-------|-------|
| 1 | OTA | Happy-path OTA campaign found a critical rollback bug |
| 2 | OTA | Power cut mid-flash — bricked ECU in field |
| 3 | OTA | Delta OTA stalled at 99% for 300 vehicles |
| 4 | OTA | Wrong VIN delivered production firmware |
| 5 | OTA | Anti-rollback triggered during regression — blocked release |
| 6 | OTA | Staged rollout caught memory leak before full fleet rollout |
| 7 | OTA | Campaign abort design: 2% error rate threshold |
| 8 | OTA | UN ECE R156 audit finding on RXSWIN update timing |
| 9 | OTA | TLS 1.2 fallback discovered in OTA client |
| 10 | OTA | OTA download stalling on 2G roaming markets |
| 11 | Cellular | LTE registration loss after 48-hour soak |
| 12 | Cellular | eSIM profile provisioning failed for 10% of vehicles |
| 13 | Cellular | Modem crash on specific PLMN selection sequence |
| 14 | Cellular | MQTT reconnect storm causing backend overload |
| 15 | Cellular | Signal quality map: identified dead zones for OTA campaigns |
| 16 | Cellular | Roaming data cost exploded due to wrong APN |
| 17 | Cellular | 5G NSA handover dropped TCP session mid-OTA |
| 18 | Remote Diagnostics | DoIP session timeout during factory programming |
| 19 | Remote Diagnostics | UDS gateway routing race condition found via CAPL |
| 20 | Remote Diagnostics | Remote DTC read returned stale data after ECU reset |
| 21 | Remote Diagnostics | P2* timer exhaustion on 4G with 200 ms latency |
| 22 | Remote Diagnostics | Security access seed-key lockout in production fleet |
| 23 | Remote Diagnostics | CAN gateway routing priority inversion during OTA |
| 24 | GNSS | GNSS fix lost after highway tunnel — 3-minute outage |
| 25 | GNSS | eCall transmitted wrong GPS coordinates |
| 26 | GNSS | Cold-start TTFF exceeded 60 s in winter conditions |
| 27 | GNSS | GNSS spoofing detected in fleet test in Dubai |
| 28 | GNSS | Galileo constellation disabled — position accuracy degraded |
| 29 | eCall | eCall audio silent — PSAP received no voice |
| 30 | eCall | Automatic eCall triggered falsely on speed bump |
| 31 | eCall | eCall MSD missing number of occupants field |
| 32 | eCall | ERA-GLONASS callback not answered by TCU |
| 33 | Power | Quiescent current exceeded 5 mA — battery drain complaint |
| 34 | Power | TCU did not wake on NM CAN frame — remote command failed |
| 35 | Power | Ignition OFF → OTA download consumed full vehicle battery |
| 36 | Power | TCU entered sleep during eCall hold |
| 37 | CAN Gateway | Message storm from TCU caused CAN bus overload |
| 38 | CAN Gateway | Gateway routed wrong logical address — flashed wrong ECU |
| 39 | CAN Gateway | SecOC freshness counter out of sync after TCU reset |
| 40 | CAN Gateway | CAN filter misconfiguration passed safety-critical IDs to public bus |
| 41 | Security | MITM intercept caught in HIL — cert pinning was disabled in test build |
| 42 | Security | Replay attack found in MQTT OTA command channel |
| 43 | Security | HSM key provisioning failed at start of production — line stopped |
| 44 | Security | Firmware signed with dev key shipped to production vehicles |
| 45 | Security | Downgrade attack possible via unprotected version field |
| 46 | Process | HIL bench environment drift caused false failures for 2 weeks |
| 47 | Process | Test coverage gap found by auditor: power-cut rollback never tested |
| 48 | Process | Wrote OTA test plan from scratch for new platform in 3 weeks |
| 49 | Process | Automated nightly OTA regression reduced cycle time 80% |
| 50 | Process | Mentored junior engineer to resolve cellular debug independently |

---

## STAR Scenarios

---

### 1. Happy-path OTA Campaign Found Critical Rollback Bug

**S — Situation:**
Our team was running final validation for the first over-the-air firmware update campaign on a new telematics platform. The OTA happy-path test (TC-OTA-001) had passed ten times. We were one week from the production launch date, and management had already communicated the release date to the OEM customer.

**T — Task:**
My responsibility was to execute the full OTA regression suite, including failure-injection tests, before signing off the test report for type approval submission.

**A — Action:**
I ran the power-interruption test (TC-OTA-F020): I connected a GPIO-controlled relay to the 12V bench supply and triggered a power cut exactly when UDS block 0x36 (TransferData) was mid-transmission, verified via CANoe timestamp. On power restore, I monitored the UART boot log. The bootloader printed `[BL] Partition B marked invalid — restoring partition A` as expected — but then the system hung indefinitely. It never booted. I captured the full UART log and analysed it. The root cause: the bootloader attempted to restore partition A, but the NVM flag write for "partition A is the valid partition" had also been corrupted by the power cut because both partition flags shared the same NVM page. Writing partition B invalid had invalidated the entire NVM page, taking partition A's validity flag with it. I raised a critical defect, documented the exact binary NVM layout showing the design flaw, and proposed moving partition validity flags to separate NVM pages with redundant copies. I wrote a targeted regression test to verify NVM flag resilience for all four power-cut injection points.

**R — Result:**
The launch was delayed by three weeks for firmware fix and re-validation. The field impact was zero — the bug was caught before any vehicle was updated. Post-fix, all four power-cut injection scenarios passed. The NVM redesign was also adopted in the next-generation platform. The OEM accepted our corrective action report and restarted the type-approval timeline.

---

### 2. Power Cut Mid-Flash — Bricked ECU in Field

**S — Situation:**
Three months after production launch of an OTA-enabled telematics system, the field support team reported three vehicles at dealerships with a "no communication" fault — the infotainment ECU was completely unresponsive and could not be accessed via the OBD port. All three had attempted an OTA update the previous night.

**T — Task:**
I was assigned as the lead test engineer to diagnose the root cause, determine whether it was a systematic risk across the wider fleet, and recommend a containment action within 48 hours.

**A — Action:**
I requested the OTA backend logs for all three VINs. Each showed: `campaign_state: INSTALLING`, followed by `campaign_state: FAILED` with error code `E_POWER_LOSS_DETECTED`, but no rollback state was ever recorded. This was the critical clue — rollback should always follow INSTALLING_FAILED. I reproduced the issue on a bench unit by cutting power 200 ms before the final UDS 0x37 RequestTransferExit. The ECU never booted again. I traced through the bootloader source code with the firmware team. The issue: rollback was only triggered if the bootloader read a specific NVM flag (`FLASH_PENDING=1`) on boot. But that flag was cleared by the OTA client before issuing the ECU reset — so the bootloader saw a clean NVM, assumed the new partition was complete, tried to boot it, found an incomplete CRC, and halted with no fallback. I identified the fix: `FLASH_PENDING` flag must be cleared only AFTER post-flash verification succeeds, not before reset. I also added a test in the suite: a NVM-flag-only corruption test (no actual power cut) to directly validate the flag clearing order.

**R — Result:**
A firmware hotfix was released within one week. The three affected vehicles were recovered by JTAG re-flash at dealerships at zero cost to owners. We issued a fleet advisory pausing OTA campaigns for 48 hours while 99.7% of in-flight campaigns completed safely. Post-fix, zero additional brick incidents in 18 months of production.

---

### 3. Delta OTA Stalled at 99% for 300 Vehicles

**S — Situation:**
During a delta OTA campaign for a minor feature update (patch size: 800 KB), campaign monitoring showed 300 vehicles (out of 5,000) stuck in `DOWNLOADING` state at 99% for over two hours. Other 4,700 vehicles completed normally.

**T — Task:**
I was tasked to investigate the root cause, determine if those 300 vehicles would self-recover or require intervention, and prevent recurrence.

**A — Action:**
I pulled the TCU logs for one affected VIN from the backend log aggregation system. The log showed repeated HTTP GET requests with the `Range: bytes=817152-819199` header — the final 2 KB chunk — returning HTTP 206 Partial Content responses, but the OTA client was never acknowledging completion. I set up a network capture in the HIL bench to reproduce: I served a test package and monitored the TCP session. I found an off-by-one error in the OTA download manager: the `bytes_received` counter used a `<` check against `total_size` rather than `<=`. When `bytes_received == total_size` the client re-requested the last chunk infinitely because the loop condition was never satisfied. The fix was a single character change. I also added a boundary-condition unit test to the OTA client CI pipeline and a watchdog timeout on the DOWNLOADING state (max 45 minutes) to prevent silent stalls in future.

**R — Result:**
The 300 stuck vehicles were recovered by a backend command forcing the TCU to re-evaluate its state machine (a `RESET_OTA_CLIENT` MQTT command). All 300 completed their OTA on retry within 30 minutes. The bug fix was merged and validated in two days. The watchdog was added to the test suite as a standard regression test.

---

### 4. Wrong VIN Delivered Production Firmware

**S — Situation:**
In an OTA staging test, a package intended only for test VIN `WTEST001` was delivered to a production vehicle `WPROD089` on the same test network. The production vehicle received and installed the firmware successfully before anyone noticed.

**T — Task:**
As the OTA test lead, I had to determine why the VIN scoping failed, assess the risk to the production vehicle, and close the gap before the production campaign.

**A — Action:**
I analysed the campaign configuration on the test OTA backend. The campaign JSON showed `"targets": [{"vin_pattern": "W*"}]` — someone had used a wildcard instead of the exact VIN `WTEST001`. The backend campaign engine had matched both vehicles. I checked the installed firmware on `WPROD089`: it was a test build, not production — it had JTAG debug interfaces open, logging verbosity at DEBUG level, and test certificates embedded. This was a security risk: if that vehicle reached end users, it would expose debug attack surfaces. I immediately flagged it to security and hardware teams. I then audited the backend VIN targeting logic and found that wildcard patterns were allowed without a confirmation step. I wrote a test case specifically for VIN scoping validation: create a campaign with an exact VIN, then verify that a vehicle with a similar-but-different VIN receives nothing. I also proposed and the team implemented a mandatory manual confirmation for any campaign targeting more than one VIN in staging.

**R — Result:**
`WPROD089` was re-flashed with the correct production firmware via bench JTAG. The wildcard pattern was removed from the backend campaign API (only exact VINs or explicit VIN lists allowed). The scoping test was added to the regression suite and has run on every release since.

---

### 5. Anti-Rollback Triggered During Regression — Blocked Release

**S — Situation:**
During regression testing of a new firmware build (v2.6.0), the OTA client refused to install the package and returned `NRC 0x26 (requestOutOfRange)`. The package was valid, correctly signed, and the test had passed with the previous firmware (v2.5.3). Release was scheduled for the following morning.

**T — Task:**
I had to diagnose why anti-rollback was firing on a legitimate upgrade and determine whether it was a test environment issue or a genuine firmware defect.

**A — Action:**
I checked the version comparison logic in the OTA client source. The version was stored as a BCD-encoded byte: `0x25` for v2.5.x, `0x26` for v2.6.x. The anti-rollback check was `if (new_version <= installed_version) → reject`. I then checked the test environment: the HIL bench TCU had been flashed with v2.5.3 for the previous test run. The issue was that v2.5.3 had a version byte of `0x253`, but stored in a single byte field it was truncated to `0x53`. v2.6.0 had version byte `0x260` truncated to `0x60`. `0x60 > 0x53` — so this should pass. I dug further and found the real cause: a test script had flashed the TCU with a pre-production v2.6.1 debug build for an earlier test, and that build had version `0x261`. When the official v2.6.0 (`0x260`) package was pushed, `0x260 < 0x261` — anti-rollback correctly blocked it. The debug build had been installed without updating the baseline register. I created a strict test setup procedure: always flash a known baseline at the start of each OTA test session, and read back the version before beginning any OTA test.

**R — Result:**
The fix was a process change, not a firmware bug. The baseline was restored, and v2.6.0 installed successfully. The test setup procedure was added to the test plan as a mandatory pre-condition step. The release proceeded on schedule after a 4-hour delay.

---

### 6. Staged Rollout Caught Memory Leak Before Full Fleet Rollout

**S — Situation:**
We deployed a new telematics firmware (v3.1.0) with a 1% staged rollout (Wave 1: 500 vehicles) targeting an LTE connectivity improvement. After 72 hours, backend telemetry showed those 500 vehicles had an average MQTT session uptime of only 6 hours before disconnection, versus the 30-day average for all other vehicles.

**T — Task:**
I was responsible for analysing wave-1 telemetry, diagnosing the anomaly, and making the go/no-go decision for wave-2 (10% rollout) scheduled for the next day.

**A — Action:**
I requested a heap dump from one affected vehicle via the remote debug MQTT command (`CMD_HEAP_SNAPSHOT`). The heap showed 98% utilisation — the application was running out of memory. I compared heap snapshots at 1 hour, 3 hours, and 5 hours post-boot: heap free memory decreased by ~200 KB every hour. I identified the leak: the MQTT reconnect handler was allocating a new TLS context object on each reconnection but only freeing it when the session was cleanly closed. In poor signal areas, sessions dropped abruptly — the clean-close path was never reached — leaving orphaned TLS objects. I confirmed this by simulating signal drops in HIL: 10 signal cut-restore cycles produced a measurable heap reduction of ~2 MB. I gave a clear no-go recommendation for wave 2, documented with heap data graphs. I also proposed a test case: soak test with 50 simulated signal interruptions, measuring heap free memory before and after.

**R — Result:**
Wave 2 was halted. Wave 1 vehicles were remotely triggered to restart the TCU application (graceful restart via MQTT, not a hard reset — important for vehicles that were driving). The firmware team fixed the memory leak in 3 days. A 50-reconnection soak test was added to the release gating criteria. v3.1.1 released two weeks later with zero memory leak in a 7-day soak.

---

### 7. Campaign Abort Design: 2% Error Rate Threshold

**S — Situation:**
The OTA backend system had no automatic abort mechanism. A previous campaign had silently failed for 15% of vehicles before a human noticed — those vehicles remained on outdated firmware for weeks, creating a compliance gap.

**T — Task:**
I was asked to design and validate the automatic campaign abort feature: if the rolling error rate across a wave exceeds a configurable threshold, the campaign should automatically halt and alert the operations team.

**A — Action:**
I wrote the test specification for the abort feature, defining three scenarios: (a) error rate never reaches threshold — campaign continues, (b) error rate exceeds threshold mid-wave — campaign halts cleanly, (c) error rate spikes then recovers below threshold — no false abort. I created a mock OTA backend in the HIL environment using a Python Flask server. I injected failure responses for a configurable percentage of vehicle simulations using CANoe's simulated vehicle panel. For scenario (b): I configured 10 simulated vehicles in wave 1; after vehicle #6 reported failure, the error rate hit 60% — well above the 2% threshold I'd set for the test — and the backend halted the campaign. I verified that: no new OTA notifications were sent to remaining vehicles; in-progress downloads were not interrupted (graceful stop after current chunk); an alert email was generated with VIN list and failure codes. I also wrote a negative test: set threshold to 0% (zero tolerance) and verified that even one failure triggered abort.

**R — Result:**
The feature was validated and released with the backend v4.2 update. In production, it has triggered twice: once caught a TLS misconfiguration (7% failure rate in wave 1, campaign halted after 35 vehicles), preventing a potentially 50,000-vehicle failed campaign. The feature is now a mandatory requirement in our OTA backend specifications.

---

### 8. UN ECE R156 Audit Finding on RXSWIN Update Timing

**S — Situation:**
During a third-party UN ECE R156 type approval audit, the auditor identified a finding: the RXSWIN (Regulatory Extended Software Version Identification Number) was not updated in the OTA backend database immediately upon campaign completion. Instead, the backend updated the RXSWIN 24 hours later via a nightly batch job, creating a window where the vehicle's physical RXSWIN (in ECU NVM) did not match the backend record.

**T — Task:**
I was assigned to design and execute the test evidence required to demonstrate that after the fix, RXSWIN is updated synchronously (within 60 seconds of OTA completion) in both the ECU and the backend.

**A — Action:**
I wrote a dedicated RXSWIN synchronisation test. After completing a full OTA cycle, I immediately read the RXSWIN from three places: (1) ECU NVM via UDS 0x22 0xF1A2, (2) OTA backend database via REST API, (3) the `ota/result` MQTT message payload. I timestamped each read. In the initial (unfixed) state: ECU RXSWIN was updated immediately, but the backend showed the old RXSWIN for 23+ hours. I documented this as test evidence for the baseline defect. After the firmware and backend fix (backend now processes RXSWIN update synchronously on receiving the `COMPLETE` MQTT message), I re-ran: all three sources showed the same RXSWIN value within 8 seconds of OTA completion. I produced a timestamped test report with screenshots of each read, attached to the corrective action response for the auditor.

**R — Result:**
The auditor accepted the corrective action and test evidence. Type approval was granted 6 weeks later. The RXSWIN synchronisation test was added to the standard OTA regression suite and is now part of the release gating criteria.

---

### 9. TLS 1.2 Fallback Discovered in OTA Client

**S — Situation:**
During a security review of the OTA client implementation, I was asked to verify that the TCU enforced TLS 1.3 only and did not fall back to older protocol versions. The firmware specification required TLS 1.3 minimum, but this had never been explicitly tested.

**T — Task:**
Design and execute a TLS version enforcement test and report findings.

**A — Action:**
I set up a test OTA server using nginx configured to accept only TLS 1.2 (rejecting 1.3). I pointed the TCU at this server and triggered an OTA download. The TCU successfully downloaded the package. This confirmed that the TCU was negotiating TLS 1.2 when TLS 1.3 was unavailable — a violation of the security specification. I captured the TLS handshake in Wireshark to confirm: `Client Hello` offered TLS 1.2 as the minimum version. I then set up a second server accepting TLS 1.3 only; the TCU also connected successfully, confirming TLS 1.3 worked but wasn't enforced. Root cause: the `ssl_minimum_version` parameter in the TLS library configuration was left at the library default (`TLSv1.0`), not explicitly set to `TLSv1.3`. I raised a security defect with CVSS scoring, provided the one-line configuration fix, and wrote two test cases: one verifying TLS 1.2 is rejected (PASS = no connection), one verifying TLS 1.3 succeeds (PASS = connection established and OTA completes).

**R — Result:**
The fix was applied in the next firmware build and verified. The TLS version enforcement tests were added to the security regression suite. A follow-up audit of all network-connected components in the vehicle found one additional component (the remote logging agent) with the same misconfiguration, which was also corrected.

---

### 10. OTA Download Stalling on 2G Roaming Markets

**S — Situation:**
The product was launched in a market where 4G coverage was limited in rural areas and vehicles frequently roamed on 2G GPRS (40–80 kbps throughput). The OTA campaign in that market showed a 35% incomplete rate — campaigns timed out before the package finished downloading.

**T — Task:**
Investigate whether the OTA client had a hard timeout incompatible with slow networks and propose a solution that balanced user experience with network cost.

**A — Action:**
I reproduced the issue by configuring the network impairment box (Spirent Avalanche) to simulate 60 kbps downstream with 3% packet loss. A 12 MB OTA package took approximately 35 minutes to download in these conditions. The OTA client had a hardcoded `DOWNLOAD_TIMEOUT = 1800 s` (30 min) — just under the 35-minute requirement. The download timed out and the partial file was discarded. I proposed three changes: (1) increase the configurable timeout to 90 minutes for markets with slow networks (backend-configurable per campaign), (2) implement HTTP resumable download — never restart from zero on reconnect, only re-request remaining bytes, (3) use delta packages for slow-network campaigns (delta was 800 KB vs 12 MB full package). I wrote tests for all three: timeout configuration test, resume-from-partial test (50% downloaded, kill TCP, reconnect, verify it resumes from 50%), and delta package test in 60 kbps conditions.

**R — Result:**
After implementing all three changes, the 2G market OTA success rate improved from 65% to 97.2% over the next campaign cycle. Campaign timeout became a campaign-level parameter rather than a firmware constant. The test for resume-from-partial was added to the standard regression suite.

---

### 11. LTE Registration Loss After 48-Hour Soak

**S — Situation:**
In a 72-hour system soak test (TCU running continuously with LTE active), the TCU lost LTE registration at the 48-hour mark and never recovered without a manual reboot. The issue was intermittent — it did not reproduce in short tests.

**T — Task:**
Identify the root cause of the long-duration LTE registration failure and provide a fix that could be validated in a reasonable test duration.

**A — Action:**
I extended the soak test to 72 hours with full modem AT command logging enabled (`AT+QURCCFG=1` for Quectel modem URC logging). At the 48-hour mark in the second soak, the logs showed the modem sent an unexpected `+CEREG: 0` (deregistered) URC, followed by a normal re-registration attempt — but the attempt never completed. The AT log then went silent: the modem had stopped responding to AT commands entirely. The modem's UART interface was frozen. I escalated to the modem vendor. Their analysis: after approximately 47 hours of continuous operation at elevated temperature (bench was 40°C ambient), a memory leak in the modem firmware's AT command parser caused the parser task to crash. I added a modem health watchdog to the TCU application: every 5 minutes, send `AT` and expect `OK` within 2 seconds; if no response after 3 consecutive attempts, trigger a modem hardware reset via the RESET_N GPIO. I also wrote the test: inject modem non-responsiveness (hold UART high) and verify the watchdog detects it and triggers a reset within 15 minutes.

**R — Result:**
The modem vendor released a firmware patch fixing the AT parser crash. Our watchdog was retained as a defence-in-depth measure. The 72-hour soak test was added to the release gating criteria. No further LTE loss events were reported in 6 months of production monitoring.

---

### 12. eSIM Profile Provisioning Failed for 10% of Vehicles

**S — Situation:**
At end-of-line production, 10% of vehicles failed the eSIM (eUICC) profile download step. Each failure meant the vehicle left the factory without a cellular subscription — it could not connect to the OTA backend or emergency services. The failure had started appearing after a production line software update.

**T — Task:**
Diagnose the root cause of the eSIM provisioning failure and unblock production within 24 hours.

**A — Action:**
I obtained the RSP (Remote SIM Provisioning) server logs for the failing vehicles. Each failure showed: `ES9+ HTTPS request timeout after 30000 ms`. The RSP server was reachable — other vehicles on the same production line succeeded. I compared the successful and failing vehicles' TCU firmware versions: all failures were on TCU SW v1.4.2, all successes on v1.4.1. I diffed the v1.4.2 release notes: a TLS library update from mbedTLS 2.28 to 3.1. In mbedTLS 3.1, the default TLS handshake timeout was reduced from 60 s to 10 s. The RSP server's ES9+ endpoint had a certificate chain of depth 4, which required multiple round trips. With production line Wi-Fi latency (~80 ms per round trip), the handshake took 12–15 s — just over the new 10 s default. I proposed a targeted fix: increase the mbedTLS handshake timeout to 30 s in the eSIM provisioning module. I validated this on a bench unit: with the fix, provisioning completed in 13.4 s; without, it timed out at 10 s.

**R — Result:**
A hotfix was built, validated in 2 hours, and deployed to production within the same shift. The 10% failure rate dropped to 0.02% (within acceptable rework tolerance). The eSIM provisioning step was added to the HIL automated pre-production checklist with a timeout validation test.

---

### 13. Modem Crash on Specific PLMN Selection Sequence

**S — Situation:**
During LTE conformance testing on a new modem module, the test bench found that the modem crashed (reset spontaneously) when a specific PLMN selection sequence was executed: manual selection of PLMN A, then immediate AT+COPS=0 (return to automatic) while the modem was mid-registration.

**T — Task:**
Characterise the crash (reproducibility, conditions, impact), report to the modem vendor, and determine the test mitigation strategy.

**A — Action:**
I ran 50 iterations of the sequence with varying timing intervals between the two AT commands. The crash reproduced 100% when the interval was 50–200 ms, and 0% when it was < 30 ms or > 500 ms. This pointed to a race condition in the modem's PLMN selection state machine: if AT+COPS=0 arrived while the modem was transitioning from `SEARCHING` to `REGISTERING`, an internal state pointer was dereferenced before initialisation. I wrote a reproducible test script with exact timing and generated a modem crash report with AT log capture for every crash. I sent it to the modem vendor with a severity 1 rating. While waiting for a modem firmware fix, I proposed a workaround: always wait 500 ms after any manual PLMN selection before issuing AT+COPS=0. This was added to the TCU modem driver abstraction layer.

**R — Result:**
The modem vendor confirmed the defect and released a patch in their next quarterly firmware update. Our workaround was retained until all field units could receive the modem firmware update. The race condition test sequence was added to our modem qualification test suite for all future modem evaluations.

---

### 14. MQTT Reconnect Storm Causing Backend Overload

**S — Situation:**
During a large-scale OTA campaign (50,000 vehicles simultaneously notified), the OTA backend's MQTT broker became unresponsive for 8 minutes. Investigation showed that all 50,000 vehicles had received the OTA notification, lost their MQTT session simultaneously (due to a broker restart), and immediately attempted to reconnect — a synchronised reconnect storm.

**T — Task:**
Design and validate a reconnect backoff mechanism on the TCU to prevent synchronised reconnect storms.

**A — Action:**
I designed a test for the reconnect backoff behaviour: using a test MQTT broker (Mosquitto) I could kill and restart programmatically. In a bench of 5 simulated TCUs (running as Python MQTT clients simulating the TCU behaviour), I killed the broker and measured reconnect attempts. Without backoff: all 5 reconnected within 1 second of broker restart — a mini-storm. I specified exponential backoff with jitter: initial retry after `random(1, 5)` seconds, doubling each attempt to a maximum of 5 minutes. I wrote a test validating that: (a) all TCUs reconnect within 10 minutes of broker restart, (b) no two simulated TCUs reconnect within the same 100 ms window more than once. I also added a test that the backoff timer resets after a successful 24-hour connected session (to ensure long-term reconnection speed was not penalised).

**R — Result:**
The backoff implementation was validated and deployed. In a subsequent OTA campaign, a planned broker maintenance restart at midnight (10,000 vehicles affected) showed reconnection spread over 7 minutes with no performance impact on the broker. The MQTT reconnect storm test was added to the OTA scale testing suite.

---

### 15. Signal Quality Map: Identified Dead Zones for OTA Campaigns

**S — Situation:**
OTA campaigns were failing consistently for vehicles registered in one geographic region. Failure pattern: stuck in `DOWNLOADING` state, then timeout. The region had been approved by the carrier as having 4G coverage, but real-world OTA success rate was only 40%.

**T — Task:**
Determine whether the poor OTA success rate was due to signal quality and provide actionable data to operations.

**A — Action:**
I extracted the RSRP data from TCU telemetry logs for affected VINs and correlated them with GPS coordinates at the time of each OTA failure. Plotting the data on a map showed a clear spatial pattern: the failures clustered in three valley areas where terrain blocked cell tower line-of-sight. RSRP at those locations averaged −112 dBm — below the −110 dBm threshold I had established in the RF sensitivity test. I also found that the carrier's coverage map used a prediction model that overestimated coverage in terrain-shadowed areas by 8–12 dB. I proposed three recommendations: (1) schedule OTA campaigns for those vehicles only when the vehicle is detected in a coverage area (geofencing on the backend), (2) use smaller delta packages for low-signal vehicles, (3) extend download timeout to 120 minutes for those VINs. I validated all three changes in HIL by running OTA at −112 dBm with the delta package + extended timeout configuration.

**R — Result:**
OTA success rate in the affected region improved from 40% to 88% after deploying delta packages and geofence-aware campaign scheduling. The geofencing logic became a standard feature in the campaign engine for all mountainous market regions.

---

### 16. Roaming Data Cost Exploded Due to Wrong APN

**S — Situation:**
In a new market deployment, the vehicle fleet's monthly cellular data cost was 8× higher than projected. Finance escalated after the first billing cycle.

**T — Task:**
Identify the source of excess data consumption and prevent recurrence in future market launches.

**A — Action:**
I pulled the data usage logs from the carrier for a sample of 20 vehicles. All showed data usage on a public APN (`internet`) rather than the OEM's private APN (`oem.m2m.private`). The private APN had no roaming charges; the public APN incurred full roaming rates. I checked the eSIM profile for those vehicles — the production profile had been provisioned correctly with the private APN. I then checked the modem APN selection logic in the TCU firmware: the modem stored two APN profiles and selected based on the MCC/MNC (country/network code). The mapping table for the new country's MCC/MNC was missing — the modem was falling through to the public APN as a default. I verified this in HIL by setting the CMW500 to the new country's PLMN and confirming the modem selected the wrong APN. The fix: add the new MCC/MNC to the APN mapping table. I also wrote a test for every supported market's MCC/MNC — 28 entries — verifying each selects the correct private APN.

**R — Result:**
The APN fix was deployed via a small OTA parameter update within one week. The billing anomaly stopped immediately. The APN mapping test for all supported markets was added to the eSIM/APN validation suite and is required before any new market launch.

---

### 17. 5G NSA Handover Dropped TCP Session Mid-OTA

**S — Situation:**
On a vehicle with a 5G NSA-capable modem, an OTA download was in progress on an LTE anchor when the vehicle entered 5G NR coverage. The modem performed a 5G NSA secondary cell addition (EN-DC) — a handover event. The TCP session carrying the OTA download was dropped and the download restarted from zero.

**T — Task:**
Determine whether the TCP drop was a network event or an application-level handling failure, and validate the fix.

**A — Action:**
I captured a Wireshark trace during the EN-DC event in the HIL bench (CMW500 simulating EN-DC handover). The TCP session showed a 1.2-second gap in data flow during the handover, followed by the server sending a TCP RST — the server had timed out the session. The OTA client received the RST and treated it as a fatal connection error, starting the download from byte 0. The real fix needed two parts: (1) server-side: increase the TCP idle timeout for OTA connections from 1 s to 10 s, (2) client-side: on TCP RST or connection close, attempt to resume the download using HTTP Range header from the last acknowledged byte, not restart. I tested both fixes: with timeout increased, EN-DC handover (1.2 s gap) no longer caused a session drop. With the resume logic, even if the session did drop, the download resumed without byte 0 restart. I measured download resumption after EN-DC: 2.1 seconds additional delay versus zero bytes lost.

**R — Result:**
Both fixes were implemented. EN-DC handover OTA resilience test was added to the 5G test suite. In subsequent field testing in a live 5G NSA network, zero OTA failures were attributed to EN-DC handover events.

---

### 18. DoIP Session Timeout During Factory Programming

**S — Situation:**
At end-of-line factory programming, the production flash station reported intermittent DoIP session timeouts when programming the TCU simultaneously with 8 other ECUs in the vehicle. The failure rate was 3%, which meant 3 out of every 100 vehicles needed a manual rework step.

**T — Task:**
Identify why DoIP sessions were timing out in the multi-ECU simultaneous programming scenario and provide a fix that brought the failure rate below 0.1%.

**A — Action:**
I set up a bench reproducing the simultaneous 8-ECU programming scenario using CANoe. I captured DoIP and CAN traffic. I found that when all 8 ECUs were being flashed simultaneously, the CAN bus utilisation peaked at 94% — near saturation. During those peaks, DoIP routing packets from the flash station to the TCU experienced delays of up to 800 ms. The TCU's DoIP `T_TCP_General_Inactivity` timer was set to 500 ms — shorter than the observed delay. The TCU was closing the TCP session before the flash station's next message arrived. The fix: increase `T_TCP_General_Inactivity` from 500 ms to 2,000 ms for the factory programming use case. I also recommended staggering the start of ECU programming: start every 200 ms rather than simultaneously, reducing peak CAN load to 70%. I validated both changes: with staggering only, failure rate dropped to 0.5%. With both changes (staggering + timer increase), failure rate dropped to 0.0% over 200 bench iterations.

**R — Result:**
Both changes were implemented in the factory programming station software and TCU firmware. The production line DoIP timeout failure rate dropped from 3% to 0.02% (within rework tolerance). The simultaneous programming test with peak load monitoring was added to the factory validation test suite.

---

### 19. UDS Gateway Routing Race Condition Found via CAPL

**S — Situation:**
In integration testing, the TCU's CAN gateway was routing UDS diagnostic requests from the Ethernet tester to ECUs on the CAN bus. Occasionally (1 in 50 requests), the response was delivered to the wrong logical address on the return path — the tester received a response meant for a different request that had been pending.

**T — Task:**
Create a CAPL-based test that could reliably reproduce and characterise the race condition, then provide the data needed for the firmware team to fix it.

**A — Action:**
I wrote a CAPL test that sent two UDS requests in rapid succession to two different ECUs (Engine at 0x0720, Radar at 0x0750), with a 5 ms inter-request interval. I instrumented the test to record the exact source address of each response and compare it to the expected ECU. Running 1,000 iterations, I reproduced the mismatch at a rate of 1.8%. I then varied the inter-request interval from 1 ms to 100 ms: mismatches occurred only at intervals between 3 ms and 20 ms — a narrow race window. The CAPL trace showed the gateway was using a single global response buffer for all pending requests. When two responses arrived within that window, the second response overwrote the buffer before the first response had been forwarded. I provided the firmware team with: the exact timing window, Wireshark + CANoe trace showing the overwrite, and a proposed fix (per-request response buffers, keyed by UDS sequence number). I also wrote a regression test: 500 rapid-succession dual-ECU requests with a 10 ms interval — 0 mismatches required.

**R — Result:**
The firmware fix (per-request response buffers) was implemented and validated. The CAPL regression test was added to the gateway test suite. No response routing mismatches were observed in subsequent testing or in 12 months of production.

---

### 20. Remote DTC Read Returned Stale Data After ECU Reset

**S — Situation:**
During remote diagnostics testing, I observed that after an ECU was reset via UDS 0x11 (EcuReset) through the TCU gateway, the next remote DTC read (SID 0x19) returned the pre-reset DTC list — not the post-reset (cleared) DTC list. The DTC read was performed 30 seconds after the reset.

**T — Task:**
Determine why stale DTCs were returned and validate the fix.

**A — Action:**
I monitored the CAN traffic between the TCU gateway and the Engine ECU. After the ECU reset, the ECU correctly cleared its DTC memory and was broadcasting its post-reset status on CAN. However, the TCU gateway had a local DTC cache with a 5-minute TTL — it was serving cached pre-reset data to remote requests without querying the ECU again. I verified this by comparing: a local direct CAN query (fresh, showed empty DTC list) versus a remote DoIP query (served by cache, showed old DTCs). The root cause was a cache invalidation design gap: ECU reset events were not invalidating the gateway's DTC cache. Fix: on receiving a UDS 0x11 (EcuReset) request, the gateway must mark its cache for that ECU as invalid. The next read request then fetches live data. I wrote the test: reset ECU, immediately read DTCs via remote DoIP within 5 seconds — must return fresh empty list, not cached list.

**R — Result:**
The fix was implemented and validated. The stale cache test was added to the remote diagnostics regression suite. The finding was also shared with the platform team, who found the same caching bug in two other vehicle platforms.

---

### 21. P2* Timer Exhaustion on 4G with 200 ms Latency

**S — Situation:**
Remote UDS diagnostic sessions through the TCU gateway were failing intermittently in real-world conditions. Field engineers reported getting `NRC 0x78` (requestCorrectlyReceived-ResponsePending) responses that eventually timed out, making remote diagnostics unreliable.

**T — Task:**
Reproduce the issue in HIL, understand the timing interaction between UDS P2 timers and network latency, and verify the solution.

**A — Action:**
I configured the network impairment box to inject 200 ms one-way latency (400 ms round trip) — typical for 4G networks. I sent UDS requests to an ECU via the TCU gateway and monitored with Wireshark. The ECU sent NRC 0x78 (response pending) to extend the P2 timer, but the 0x78 response took 400 ms to reach the tester (round trip delay). The tester's P2 timer was 250 ms — shorter than the network round trip. By the time the 0x78 arrived, the tester had already timed out the session and sent a new request, confusing the gateway's session state. The fix had two components: (1) increase the remote diagnostic tester's P2 timer to 1,000 ms when connected via cellular (network-aware timer configuration), (2) the gateway should buffer and re-transmit NRC 0x78 locally to the tester if the network round trip exceeds a threshold. I tested both: with P2 = 1,000 ms and 400 ms latency, all UDS sessions completed without spurious timeouts.

**R — Result:**
The tester configuration and gateway buffering were both deployed. Remote diagnostic success rate on 4G improved from 87% to 99.6% in field trials. The P2 timer / latency interaction test was formalised as a required test in the remote diagnostics specification.

---

### 22. Security Access Seed-Key Lockout in Production Fleet

**S — Situation:**
Customer service reported that 120 vehicles in the field had ECUs that were no longer accessible via UDS security access (SID 0x27). Garage technicians could not perform reprogramming because the ECU returned NRC 0x36 (exceededNumberOfAttempts) indefinitely — even after ignition cycling.

**T — Task:**
Investigate why the lockout counter was not resetting, assess the scope of affected vehicles, and provide a recovery path.

**A — Action:**
I analysed the UDS seed-key implementation for the affected ECU. The lockout counter was stored in NVM and incremented on each failed security access attempt. The spec said "reset on next power cycle" — but the NVM was in a non-volatile partition that survived ignition off/on. The counter only reset after a complete ECU reset (hardware reset, not just ignition). In the field, an over-the-air diagnostic session had sent multiple malformed security access requests (a bug in the remote diagnostic tool that was generating wrong keys) before the session was closed. This had incremented the counter to the lockout threshold. Field recovery: I identified that a specific UDS routine control (0x31 0x01 0xFF10) could reset the lockout counter when called from the physical OBD port — this was a factory-only command that was undocumented in field literature. I documented this recovery procedure for dealerships. Long-term fix: the remote diagnostic tool bug was corrected, and a rate limiter was added on the TCU gateway to block more than 3 consecutive failed security access attempts per session.

**R — Result:**
120 vehicles were recovered using the documented OBD routine procedure. The remote tool bug was fixed. The gateway rate limiter was deployed in the next OTA cycle. The lockout scenario was added to the remote diagnostics test suite.

---

### 23. CAN Gateway Routing Priority Inversion During OTA

**S — Situation:**
During a combined test — an OTA install (flashing ECU via UDS 0x36 over CAN) and simultaneous remote diagnostics session — the OTA flash progress slowed from the expected 2 KB/block to 200 bytes/block. The OTA campaign timed out.

**T — Task:**
Determine whether the priority inversion was real and, if so, propose and validate a fix.

**A — Action:**
I set up the combined scenario in CANoe. I measured CAN bus utilisation: with both sessions active, CAN utilisation was 85%. I analysed the message scheduling in the gateway: the remote diagnostic messages (DoIP encapsulated UDS) were being sent with CAN priority ID 0x7E0 (higher priority, lower CAN ID value), while OTA flash data blocks (UDS 0x36) were being sent with CAN ID 0x700 (lower priority, higher CAN ID value). The gateway's scheduler was starving the OTA blocks because diagnostic messages had higher CAN arbitration priority and arrived more frequently. I proposed: (1) assign OTA flash data blocks higher CAN priority than diagnostic messages (swap the priority assignment), (2) implement time-division scheduling in the gateway: dedicate 70% of CAN bandwidth to OTA during active flash operations. I validated option (2) in CANoe: OTA throughput returned to 2 KB/block; diagnostic messages were delayed by at most 150 ms per message, which was within UDS P2 timer limits.

**R — Result:**
Time-division scheduling was implemented and validated. OTA campaign timeout issues under concurrent diagnostic load were eliminated. The combined OTA + diagnostics test became a standard scenario in the integration test suite.

---

### 24. GNSS Fix Lost After Highway Tunnel — 3-Minute Outage

**S — Situation:**
Fleet data showed that vehicles exiting highway tunnels (average tunnel length: 2 km, duration: 90 seconds) experienced a GNSS fix outage of 3–5 minutes after tunnel exit. During this period, the position was not updated in the OEM telematics backend — fleet management customers saw vehicles "disappear" on the map.

**T — Task:**
Diagnose why GNSS re-acquisition was taking 3–5 minutes after tunnel exit and validate improvements.

**A — Action:**
I used the Spirent GNSS simulator to replay a tunnel scenario: signal present → 90-second blackout → signal restored. The TCU took 4 minutes 12 seconds to regain a fix. I analysed the GNSS receiver configuration: after 90 seconds of signal loss, the receiver had discarded its ephemeris data and was performing a cold start on signal restoration. The cold start TTFF with degraded almanac was 4+ minutes. I investigated the receiver's configuration register: `NMEA_WARM_START_TIMEOUT` was set to 60 seconds — any outage longer than 60 seconds triggered a cold start. I increased this to 180 seconds (3 minutes) to cover typical tunnel durations. I also enabled the A-GPS (Assisted GPS) feature, which provided a valid ephemeris from the cellular network within 2 seconds of signal restoration. With both changes, post-tunnel re-acquisition: 8 seconds. I validated with 10 Spirent tunnel scenario iterations.

**R — Result:**
The GNSS configuration change was deployed via OTA parameter update (no firmware change required). Post-tunnel GNSS re-acquisition improved from 4+ minutes to under 10 seconds in 95% of cases. Fleet management customer complaints about disappearing vehicles were eliminated.

---

### 25. eCall Transmitted Wrong GPS Coordinates

**S — Situation:**
In eCall type-approval testing, the PSAP test station reported that the MSD (Minimum Set of Data) transmitted by the TCU contained GPS coordinates that were 14 km from the vehicle's actual test location.

**T — Task:**
Identify why the eCall MSD contained wrong coordinates and fix it before the type-approval submission deadline.

**A — Action:**
I enabled full GNSS data logging on the TCU and triggered a test eCall. The MSD was generated using a cached GPS position from 22 minutes before the eCall event — the GNSS receiver had not been active, and the last cached fix was from when the vehicle was at the pre-test parking area 14 km away. The GNSS receiver was in a low-power scheduled mode: it woke every 30 minutes, obtained a fix, then slept. When the eCall triggered between GNSS wake cycles, the application used the stale cached position. The fix: on eCall trigger (airbag deployment signal or manual button press), the GNSS receiver must be woken immediately and a fresh fix must be obtained before the MSD is transmitted. If a fresh fix cannot be obtained within 10 seconds (e.g., vehicle is indoors), the MSD should be transmitted with the most recent cached fix AND a flag indicating the position may be stale (ISO 26262 recommended fallback). I validated this: eCall triggered, GNSS woke and obtained fix in 6 seconds, MSD transmitted with fresh coordinates within 8 seconds.

**R — Result:**
The fix was implemented and validated. eCall MSD position accuracy was within 3 m in open-sky conditions. The stale position use case was added to the eCall test suite as a dedicated test (indoor eCall scenario). Type approval passed.

---

### 26. Cold-Start TTFF Exceeded 60 s in Winter Conditions

**S — Situation:**
In cold weather testing at −30°C (cold chamber), the GNSS cold-start Time to First Fix (TTFF) consistently exceeded 180 seconds — three times the 60-second specification and far exceeding the EU eCall requirement of fix before MSD transmission.

**T — Task:**
Determine if the TTFF degradation was hardware-related (thermal), firmware-related (almanac not persisted), or both, and recommend a solution.

**A — Action:**
I ran TTFF tests at five temperatures: +25°C, 0°C, −10°C, −20°C, −30°C. TTFF was 22 s, 28 s, 45 s, 90 s, 182 s respectively — a clear thermal relationship. I investigated NVM almanac persistence: after a clean power cycle at −30°C, the receiver attempted a cold start — confirming almanac was NOT being persisted to NVM. At room temperature, the receiver completed a warm start in 5 s when almanac was available. I identified that the almanac write to NVM was gated behind a valid fix confirmation — at −30°C, the first fix sometimes failed, so almanac was never written. I also checked the TCXO (temperature-compensated oscillator) initial frequency accuracy at −30°C: the startup offset was 2.5 ppm versus the 1 ppm spec. This forced the receiver to search a wider Doppler window, explaining the extended acquisition time. I recommended: (1) persist almanac to NVM unconditionally every 4 hours during normal operation (not gated behind fix success), (2) enable A-GPS as the primary assistance mechanism, (3) flag the TCXO thermal performance to the hardware team for next hardware revision.

**R — Result:**
With A-GPS enabled and almanac persistence fixed, TTFF at −30°C improved from 182 s to 12 s. The TCXO was replaced in hardware rev B with a higher-spec unit. TTFF test at −30°C was added to the cold-chamber test campaign.

---

### 27. GNSS Spoofing Detected in Fleet Test in Dubai

**S — Situation:**
During fleet testing in Dubai (a known GNSS spoofing hotspot due to regional drone countermeasure systems), several test vehicles reported impossible position jumps: a vehicle stationary in a parking lot showed its position as being in the middle of the sea, 80 km offshore — a known spoofed location broadcast in that area.

**T — Task:**
Evaluate whether the TCU's GNSS spoofing detection was functioning and, if not, propose a detection mechanism.

**A — Action:**
I checked the TCU firmware's GNSS spoofing detection configuration: the receiver had spoofing detection enabled (`CFG-NAVSPG-SPOOFDETECTOR = 1` for u-blox receiver), but the detection result was not being read or acted upon by the TCU application. The u-blox receiver was correctly flagging the spoof in its NAV-STATUS message (`spoofDetState = 2: multiple spoofing indications`), but the TCU application was ignoring this field. I added logic to: (1) read `spoofDetState` from the GNSS receiver on every position fix, (2) if spoofing suspected: reject the position update, maintain last-known-good position, send a spoofing alert to the backend via MQTT (`vehicles/{VIN}/alerts/gnss_spoof`), set a DEM event. I tested this with the Spirent GNSS simulator's spoofing injection feature: injected a known-bad position, verified the TCU rejected it and transmitted the alert within 5 seconds.

**R — Result:**
The fix was deployed. In subsequent Dubai fleet testing, all spoofed positions were correctly rejected; the OEM backend received spoofing alerts for each affected vehicle. The test for spoofing detection was added to the GNSS test suite using Spirent's spoofing injection capability.

---

### 28. Galileo Constellation Disabled — Position Accuracy Degraded

**S — Situation:**
A position accuracy complaint from a fleet customer in northern Europe showed vehicles reporting positions with CEP95 of 25 m instead of the specified 10 m. The issue was geographically specific — Northern Europe, Nordic countries.

**T — Task:**
Investigate why position accuracy was degraded in that region and fix it.

**A — Action:**
I pulled the NMEA logs from affected vehicles. The GGA sentences showed `$GPGGA` — GPS only — instead of `$GNGGA` which would indicate multi-constellation (GPS + Galileo). The Galileo constellation provides significantly better geometry (GDOP) in northern Europe due to its orbital inclination. I checked the GNSS receiver configuration: the Galileo signal band E1 was disabled in the configuration — an entry `CFG-SIGNAL-GAL_ENA = 0`. I searched the codebase for where this was set: a GNSS initialisation script had an error where the constellation configuration was reset to GPS-only defaults on every boot, overwriting the production config. The fix: preserve the multi-constellation configuration in NVM and verify it on startup. I tested with Spirent: with GPS+Galileo enabled, CEP95 in Nordic geometry improved from 25 m to 4.8 m.

**R — Result:**
The configuration fix was deployed via OTA. Fleet accuracy complaints in northern Europe resolved. Multi-constellation configuration verification was added to the GNSS startup self-test. The fix also revealed the same bug in three other market configurations (GLONASS disabled in Russia, BeiDou disabled in China).

---

### 29. eCall Audio Silent — PSAP Received No Voice

**S — Situation:**
During eCall type-approval testing, the PSAP simulator received the MSD correctly but the voice channel was silent — no audio in either direction despite a connected call.

**T — Task:**
Diagnose the eCall audio path failure and fix it within the type-approval test window.

**A — Action:**
I connected an oscilloscope to the TCU audio codec lines (PCM interface between modem and audio codec). On eCall trigger, the modem established the voice call (visible in AT log: `CLCC` showing connected state), but the PCM clock lines showed no signal — the audio codec was not running its clock. I checked the TCU firmware's eCall state machine: the PCM clock was enabled by a GPIO that was supposed to be asserted when the eCall call was connected. In the code, the GPIO was asserted on `CECALL_STATE = CALL_SETUP` — but the PCM codec expected the clock to start after `CECALL_STATE = CALL_ACTIVE`. The clock was starting too early, the codec was not yet synchronised, and then the clock was not re-started when `CALL_ACTIVE` was reached. Fix: move the PCM clock enable GPIO assertion to the `CALL_ACTIVE` state transition. I validated: audio was present in both directions on the next eCall test; microphone input and speaker output both functional.

**R — Result:**
The fix was implemented and verified. eCall audio test was added to the test suite as a mandatory step. Type approval voice test passed. The state transition timing for audio peripherals was also reviewed for the manual call (non-eCall) audio path, which was found to have a similar but non-critical timing margin issue.

---

### 30. Automatic eCall Triggered Falsely on Speed Bump

**S — Situation:**
In field testing, the TCU triggered an automatic eCall when the vehicle drove over a sharp speed bump at 30 km/h. The PSAP simulator received a real eCall MSD — this was a false positive that would generate unnecessary emergency service calls in production.

**T — Task:**
Identify why the speed bump triggered the eCall algorithm and implement a discrimination mechanism with validated thresholds.

**A — Action:**
I analysed the eCall trigger logic: the automatic trigger read the crash detection signal from the Airbag Control Unit (ACU) via CAN. The trigger condition was `ACU_CrashDetected == 1`. I checked what the ACU was transmitting when the vehicle hit the speed bump: at 30 km/h over a sharp bump, the ACU's accelerometer registered a −8G deceleration spike lasting 15 ms. The ACU had a threshold of −7G for crash detection, so it briefly asserted `CrashDetected = 1`. The TCU triggered immediately on any assertion of this signal. The fix: require `CrashDetected == 1` for a minimum of 50 ms before triggering eCall — short mechanical shocks (speed bumps, potholes) last 10–30 ms; real crash decelerations sustain 50+ ms above threshold. I tested with the ACU simulation in CANoe: 15 ms spike → no eCall trigger; 55 ms spike → eCall triggered correctly. I also tested 100 simulated speed bump scenarios and 20 simulated crash scenarios with no false positives or false negatives.

**R — Result:**
The 50 ms debounce was implemented. False eCall triggers from road irregularities were eliminated. The speed bump discrimination test was added to the eCall test suite. The threshold was reviewed and accepted by the OEM safety team and the eCall test laboratory.

---

### 31. eCall MSD Missing Number of Occupants Field

**S — Situation:**
During eCall MSD content verification, the PSAP simulator's MSD decoder reported the `numberOfPassengers` field as 0 in all test eMSDs — even when the test configuration specified 2 passengers. This field is required by the EN 15722 standard for emergency responders to know how many people to assist.

**T — Task:**
Diagnose why the passenger count was always 0 and validate the fix.

**A — Action:**
I reviewed the MSD encoding logic in the firmware. The `numberOfPassengers` field was supposed to be read from the Occupant Classification System (OCS) via a CAN DID. In the HIL bench, the OCS ECU was simulated by CANoe. I checked the CANoe simulation: the OCS DID was being transmitted on CAN ID 0x3A0 at 100 ms cycle. I then checked the TCU's CAN receive filter: the filter was configured to accept CAN IDs 0x100–0x380 only — ID 0x3A0 was being filtered out. The TCU was never receiving the passenger count. The fix: add 0x3A0 to the TCU CAN receive filter. I also added a diagnostic self-check: on startup, verify OCS signal is being received within 5 seconds; if not, set a DEM event and use a default safe value (maximum plausible occupants = 5) rather than 0.

**R — Result:**
CAN filter was updated. eCall MSD now correctly includes passenger count. The OCS signal reception check was added to the startup self-test. The MSD content validation test was extended to verify all 12 mandatory MSD fields are non-zero/non-default when the expected signals are present.

---

### 32. ERA-GLONASS Callback Not Answered by TCU

**S — Situation:**
In ERA-GLONASS type-approval testing (the Russian equivalent of eCall), the test required the PSAP to call back the vehicle within 10 minutes and have the TCU auto-answer. The TCU was not auto-answering — the callback rang indefinitely.

**T — Task:**
Diagnose the auto-answer failure specific to the ERA-GLONASS callback scenario.

**A — Action:**
I reviewed the ERA-GLONASS call handling configuration. The eCall auto-answer was implemented using AT+CCWA (call waiting) and AT+ATA (answer) triggered by the modem URC `+CRING` (incoming call ring indication). I checked the modem AT command log during a callback test: `+CRING: VOICE` was received, but the TCU application never issued `AT+ATA`. I traced the call handling code: `+CRING` was handled only if the TCU was in `CALL_ACTIVE` state (expecting a call extension). The callback arrived when the TCU was in `POST_CALL_MONITORING` state — a different state that had no `+CRING` handler. The ERA-GLONASS standard requires auto-answer for 20 minutes after the initial call ends; the state machine had not implemented this window correctly. Fix: add `+CRING` → `AT+ATA` handling in `POST_CALL_MONITORING` state with a 20-minute timeout. I validated: callback received 8 minutes after initial call, TCU auto-answered within 2 rings.

**R — Result:**
ERA-GLONASS type approval callback test passed. The state machine gap was documented and reviewed for the EU eCall path as well, where a similar but narrower (10 min) callback window exists. Both paths were validated. ERA-GLONASS certification was achieved.

---

### 33. Quiescent Current Exceeded 5 mA — Battery Drain Complaint

**S — Situation:**
A customer complaint: vehicle battery discharged within 3 weeks when the car was not driven (parked at airport). Normal quiescent current specification was ≤ 1 mA. An oscilloscope measurement at the dealer showed 6.2 mA average draw in the parked state.

**T — Task:**
Identify which component was drawing excess current and validate the fix.

**A — Action:**
I reproduced the condition on the bench: set TCU to OFF/sleep mode (ignition off, 30 minutes elapsed), measured total current with a precision ammeter. Confirmed 6.1 mA. I then measured individual power rails using current probes: 12V main: 0.9 mA (expected), 3.3V MCU domain: 0.2 mA (expected), 1.8V modem domain: 5.0 mA (unexpected — modem should be fully off). I queried the modem via UART: AT commands were still responded to, confirming the modem was not powered down. I reviewed the TCU shutdown sequence in firmware: on entering sleep mode, the firmware issued `AT+QPOWD=1` (Quectel power-down) and then de-asserted the modem's 1.8V power enable GPIO. However, the GPIO was on a port configured as INPUT after the sleep mode GPIO reconfiguration — a GPIO misconfiguration meant the modem power rail was never actually de-asserted, only floating. Fix: explicitly configure the modem power GPIO as OUTPUT LOW in the sleep entry sequence. I validated: quiescent current after fix: 0.7 mA.

**R — Result:**
The GPIO fix was deployed via OTA. Customer complaint resolved. Quiescent current test at 30-minute post-ignition-off was added to the power management test suite with a 1 mA threshold. The GPIO configuration for all power-enable signals was audited — two similar issues found in other peripherals.

---

### 34. TCU Did Not Wake on NM CAN Frame — Remote Command Failed

**S — Situation:**
A backend-triggered remote door unlock command (sent via MQTT → TCU → CAN) failed for 8% of vehicles. Investigation showed the vehicles were in sleep mode and not waking up in response to the NM (Network Management) CAN wake frame that the TCU should respond to.

**T — Task:**
Reproduce and diagnose the partial-network wake failure and validate the fix.

**A — Action:**
I put the bench TCU into sleep mode and sent the NM wake frame (CAN ID 0x400, partial network request) using CANoe. The TCU did not wake. I tried 20 times: wake worked 9 out of 20 times — confirming the 8% field failure rate was actually much higher in my test, likely because the bench had no RF interference masking borderline issues. I attached a logic analyser to the TCU's CAN Rx line and the MCU wake interrupt line. The CAN transceiver was correctly receiving the NM wake frame and pulling the WAKE pin high. But the MCU was not waking. I checked the MCU sleep mode configuration: the CAN wake interrupt was configured to wake the MCU from STOP1 mode only. After a software update, the sleep mode had been changed to STOP2 mode (for lower power consumption) without updating the wake interrupt configuration — STOP2 mode requires the EXTI line to be explicitly reconfigured. The CAN wake EXTI was not reconfigured for STOP2. Fix: add CAN wake EXTI reconfiguration to the STOP2 entry sequence.

**R — Result:**
After the fix, CAN NM wake was 100% reliable over 200 bench test iterations. The fix was deployed via OTA. Remote command delivery failure rate for sleeping vehicles dropped from 8% to below 0.1%. Sleep mode transition testing was added to the power management regression suite.

---

### 35. Ignition OFF → OTA Download Consumed Full Vehicle Battery

**S — Situation:**
A customer complaint: vehicle battery was completely flat in the morning after an OTA update notification was received overnight. Investigation showed the TCU had performed a 45-minute OTA download in full ACTIVE mode (cellular + CAN running) while the vehicle was parked.

**T — Task:**
Validate that the OTA pre-conditions correctly protect against battery depletion and test the low-SOC download interruption logic.

**A — Action:**
I reviewed the OTA pre-condition check for battery SOC: the specification required downloads to pause if SOC < 30%. I tested: set CANoe to simulate BatterySoc = 25%, triggered OTA download. The download proceeded without interruption — the pre-condition check was only applied to the INSTALLATION step, not the DOWNLOAD step. The design assumption was that download is a low-risk operation (no flash writes), but a 45-minute cellular session at full modem power consumes approximately 400 mAh — enough to flatten a weakened battery overnight. I proposed and validated two changes: (1) pause download if SOC < 20% (lower threshold for download vs. 30% for installation), (2) use the modem's low-power download mode (reduced transmit power, throttled throughput) when SOC is between 20–40%, (3) if vehicle is connected to a charger (charge current signal on CAN), no SOC restriction applies. I wrote test cases for each battery SOC boundary condition.

**R — Result:**
All three changes were implemented. The battery drain issue was reproduced in 0/20 subsequent overnight parking OTA simulations with corrected firmware. The SOC boundary test was added to the OTA pre-condition test suite. The OEM added a customer-facing notification: "Plugging in your car charges faster and enables overnight updates."

---

### 36. TCU Entered Sleep During eCall Hold

**S — Situation:**
In an eCall scenario where the call was put on hold by the PSAP for 12 minutes (PSAP coordinating with emergency services), the TCU entered sleep mode — the eCall session was lost and the call could not be resumed.

**T — Task:**
Ensure the TCU does not enter sleep mode during the full eCall window (including PSAP hold) and validate the fix.

**A — Action:**
I reviewed the power management state machine. The TCU entered sleep mode after 10 minutes of CAN bus inactivity — a standard sleep entry timer. During the eCall hold, the vehicle's CAN bus was quiet (ignition off, engine off), triggering the sleep entry. The eCall state machine had a flag `ECALL_ACTIVE = 1` but the power management module was not checking this flag before initiating sleep. Fix: add a check in the sleep entry condition: `if (ECALL_ACTIVE || ECALL_POST_CALL_MONITORING) → inhibit sleep`. The inhibit must remain until the eCall state machine returns to IDLE. I tested: triggered eCall, allowed PSAP hold for 15 minutes, verified TCU remained fully active throughout. I also tested the converse: after eCall completed and post-call monitoring ended (20 minutes), TCU correctly entered sleep.

**R — Result:**
Fix implemented and validated. eCall session held for 20 minutes without sleep interruption. eCall × sleep interaction test added to the test suite. The fix was also applied to the ERA-GLONASS path. No further eCall drops due to sleep mode in subsequent testing or production monitoring.

---

### 37. Message Storm from TCU Caused CAN Bus Overload

**S — Situation:**
During integration testing of a new TCU firmware, the CAN bus showed 98% utilisation within 5 seconds of TCU boot, causing other ECUs to miss their cyclic messages and generate communication DTCs.

**T — Task:**
Identify the source of the CAN message storm and restore normal bus utilisation.

**A — Action:**
I captured a CAN trace at boot using CANoe. The trace showed CAN ID 0x701 (TCU NM message) being transmitted at 1,000 frames/second — 20× its normal 50 ms cycle time. I checked the CAPL simulation environment's NM configuration: the new firmware had changed the NM active timeout from 2,000 ms to 20 ms — a typo (one zero missing). The TCU's NM module was transmitting its alive message at 50× the intended rate. I confirmed by checking the firmware diff: `NM_MSG_CYCLE_TIME_MS = 20` instead of `NM_MSG_CYCLE_TIME_MS = 2000`. The fix was a one-character correction. While the immediate cause was simple, I also added a CAN bus load monitor test: at TCU boot, measure CAN utilisation for the first 10 seconds and fail the test if utilisation exceeds 50% (normal expected load is ~30%).

**R — Result:**
Firmware corrected and validated. CAN bus load test added to the integration test suite. The test caught a similar cycle time regression in a subsequent firmware build 3 months later, preventing it from reaching integration testing.

---

### 38. Gateway Routed Wrong Logical Address — Flashed Wrong ECU

**S — Situation:**
During a remote programming test, a firmware update intended for the Radar ECU (logical address 0x0750) was delivered to the ADAS Central ECU (logical address 0x0752). The ADAS ECU received and partially accepted the wrong firmware before returning an error.

**T — Task:**
Determine why the gateway routed to the wrong logical address and validate the fix.

**A — Action:**
I examined the routing table in the TCU gateway firmware. The routing table was a sorted array of logical addresses mapped to CAN IDs. The Radar ECU entry was `{0x0750, CAN_ID_0x758}` and the ADAS ECU entry was `{0x0752, CAN_ID_0x760}`. The lookup function used a binary search. I traced the binary search: with the table size at that point (127 entries), the binary search was performing a comparison at index 63 — which was the ADAS ECU entry, not the Radar entry. The bug: the routing table was not sorted by logical address — a merge from two feature branches had been done without re-sorting. The binary search returned a match for the closest entry, not an exact match. I added an exact-address comparison after the binary search: if the found entry's logical address doesn't exactly match the requested address, return "no route found" rather than routing to the wrong ECU. I also added a CI test: validate that the routing table is sorted by logical address before every build.

**R — Result:**
The ADAS ECU was recovered by re-flashing with the correct firmware. The gateway fix was implemented. The routing table sort validation was added to the CI pipeline. No subsequent routing mismatches were found in integration testing or production.

---

### 39. SecOC Freshness Counter Out of Sync After TCU Reset

**S — Situation:**
After a TCU software reset (triggered by the OTA activation step), all SecOC-protected CAN messages from the TCU were being rejected by receiving ECUs for approximately 30 minutes. During this window, safety-critical ADAS functions relying on SecOC-protected messages were degraded.

**T — Task:**
Diagnose the SecOC freshness counter synchronisation failure and minimise the recovery time.

**A — Action:**
I analysed the SecOC implementation. The TCU maintained a Trip Counter (TC) and a Reset Counter (RC) as its freshness value (FV). On reset, the RC should increment and be persisted to NVM. Receiving ECUs expected the RC to increment after a reset and would accept the new TC sequence. I measured: before reset, RC = 5, TC = 14,320. After reset, RC = 5 (unchanged) and TC = 0. The receiving ECUs saw TC go backwards from 14,320 to 0 with the same RC — this looked like a replay attack and they rejected all messages. Root cause: the RC NVM write was not completing before the reset was applied. The OTA reset command triggered an immediate `ECU_RESET` without waiting for the NVM write to flush. Fix: before issuing the ECU reset, the OTA client must invoke a shutdown hook that blocks until the NVM write is confirmed (NVM write-complete interrupt). I tested: post-fix, reset with NVM flush confirmation — RC correctly incremented to 6 after reset; receiving ECUs accepted new messages immediately.

**R — Result:**
SecOC re-synchronisation time after reset: reduced from 30 minutes to 0 seconds. The NVM flush-before-reset test was added to the OTA activation test suite. The finding was shared with the AUTOSAR BSW team to add a generic NVM flush step to the standard ECU reset sequence.

---

### 40. CAN Filter Misconfiguration Passed Safety-Critical IDs to Public Bus

**S — Situation:**
During a cybersecurity penetration test, the pen-test team demonstrated that by connecting to the OBD2 port (public CAN bus), they could receive CAN messages from the private ADAS bus that were being re-broadcast by the TCU gateway without filtering. These messages included airbag deployment commands and ADAS steering override commands.

**T — Task:**
Validate the severity of the finding, identify all leaking CAN IDs, and validate the remediation.

**A — Action:**
I set up a logging capture on both the public and private CAN buses simultaneously in CANoe. I ran the vehicle simulation for 30 minutes and compared all CAN IDs present on both buses. I found 23 CAN IDs that appeared on both buses — the gateway was re-broadcasting them without filtering. Of the 23, I classified: 6 as safety-critical (airbag, steering, braking commands), 9 as security-sensitive (diagnostic session status, key learning status), 8 as low-sensitivity (display messages, ambient temperature). I built a whitelist of CAN IDs that are permitted to be routed from private to public bus: only 4 IDs (vehicle speed, engine RPM, odometer, fuel level — all non-safety, non-security). I updated the gateway CAN filter to block all IDs not on the whitelist. I then validated: ran the full 30-minute simulation and confirmed 0 safety-critical or security-sensitive IDs appeared on the public bus. I also wrote a test that runs at every build: capture 60 seconds of traffic on both buses; assert that no ID outside the whitelist appears on the public bus.

**R — Result:**
The CAN filter was deployed as a security patch (priority OTA). The pen-test finding was closed with a corrective action. The CAN gateway security test became part of the mandatory pre-release security test suite. The finding was also reported to the OEM's TPSA (Third-Party Security Assessment) as required by ISO 21434.

---

### 41. MITM Intercept Caught — Cert Pinning Disabled in Test Build

**S — Situation:**
During a security validation test, I set up a man-in-the-middle proxy (mitmproxy) between the TCU and the OTA server on the HIL network. The proxy successfully intercepted the HTTPS OTA traffic — it could read and modify the firmware package in transit. This was only discovered during an ad-hoc security review.

**T — Task:**
Determine why cert pinning was not preventing the MITM, validate that the production build would not have the same issue, and add automated security tests.

**A — Action:**
I checked the build configuration for the test firmware: the cert pinning flag was `CERT_PINNING_ENABLED = 0` — it had been disabled to simplify HIL setup (the HIL bench used a self-signed certificate). This flag was set in a test-specific build configuration file. I then built the production firmware and verified `CERT_PINNING_ENABLED = 1`. Cert pinning in the production build rejected the MITM proxy correctly — the production build was safe. However, the risk was that the test build configuration could accidentally be used for production. I proposed: (1) add a CI gate that fails the release build if `CERT_PINNING_ENABLED = 0` is present in any production-build configuration, (2) replace the HIL self-signed cert with a test CA certificate that is explicitly trusted by the test firmware but different from the production CA, allowing cert pinning to remain enabled in test builds. I implemented and tested both changes.

**R — Result:**
Cert pinning is now enabled in all builds (test and production) using separate CA chains. The CI gate prevents any production build from accidentally including cert-pinning disabled configurations. The MITM test was formalised: set up MITM proxy, verify OTA download is rejected, verify TLS error is logged.

---

### 42. Replay Attack Found in MQTT OTA Command Channel

**S — Situation:**
During security testing of the OTA command channel, I captured a valid OTA trigger MQTT message (`{"action":"start_update","pkg_id":"PKG_001"}`) using Wireshark. I then replayed the same message 24 hours later. The TCU accepted the command and began an OTA update — even though the campaign had already completed.

**T — Task:**
Design and validate a replay prevention mechanism for the MQTT OTA command channel.

**A — Action:**
I reviewed the MQTT message format: no timestamp, no message ID, no sequence number — the message was stateless and had no replay protection. I proposed adding a `nonce` field (a UUID generated by the backend, valid for 5 minutes, stored in a backend-side used-nonce database) and a `timestamp` field (UTC ISO 8601). The TCU OTA client validates: (1) timestamp is within ±5 minutes of current time (requires TCU to have NTP synchronisation), (2) nonce has not been seen before (TCU stores last 20 nonces in RAM, backed by NVM). I also proposed signing each OTA command with the backend's private key (command signature over `{pkg_id + nonce + timestamp}`). I tested: replayed a captured command with a 6-minute-old timestamp — rejected. Replayed with a valid timestamp but known nonce — rejected. A fresh command with valid timestamp, new nonce, and valid signature — accepted.

**R — Result:**
All three mechanisms were implemented. Replay of captured OTA commands was no longer possible. The replay prevention test was added to the security test suite as a mandatory pre-release test. The same mechanism was also applied to the remote diagnostic session initiation command.

---

### 43. HSM Key Provisioning Failed at Start of Production — Line Stopped

**S — Situation:**
On day one of production launch, the HSM (Hardware Security Module) key injection step failed for 100% of vehicles in the first 2 hours. The production line was stopped. Each failure meant the vehicle left the HSM station with no crypto keys — no SecOC, no OTA signature verification, no TLS client certificate.

**T — Task:**
Diagnose the key provisioning failure and restore the production line as quickly as possible.

**A — Action:**
I was called to the production line with the firmware team. The key injection tool reported: `HSM_PROVISION: ERROR_TIMEOUT after 5000ms`. The provisioning station was connected to the TCU via a dedicated provisioning interface (SWP — Single Wire Protocol). I checked the interface: the SWP signal on the oscilloscope showed valid clock and data signals. I then checked the HSM state from the TCU side via the debug UART: `HSM state: LOCKED — awaiting factory unlock sequence`. The HSM had a two-step provisioning protocol: first send an unlock command with a factory password, then provision keys. The production tool had been updated overnight with a new version that changed the command sequence: it was sending keys before the unlock command. I rolled back the provisioning tool to the previous version and verified key injection succeeded on a bench unit. I then contacted the provisioning tool vendor to fix the command sequence in the new version.

**R — Result:**
Production line restored within 90 minutes using the rolled-back tool. The tool update process was changed to require a mandatory bench validation of 10 units before any production tool update is deployed. I wrote the bench validation test for provisioning tool changes.

---

### 44. Firmware Signed with Dev Key Shipped to Production Vehicles

**S — Situation:**
Twelve weeks after production launch, a security audit discovered that the firmware in 340 production vehicles had been signed with a development key (not the production key). The dev key was shared across all engineering laptops — it was not hardware-protected. Any engineer with access to the dev key could create and deploy signed firmware to those vehicles.

**T — Task:**
Assess the security impact, determine how the dev-signed firmware was shipped, and implement process and test controls to prevent recurrence.

**A — Action:**
I traced the build pipeline for the affected firmware version. The CI/CD pipeline had two signing configurations: `dev_sign` (using a software key stored in CI secrets) and `prod_sign` (using a hardware HSM key requiring two-person authorisation). The affected build was triggered by a hotfix branch that had copied the build configuration from a development branch without updating the signing step. The CI pipeline ran `dev_sign` and the release manager approved the build without checking the signing key identity. I proposed three controls: (1) the firmware binary must embed a key identity byte (0x01 = dev, 0x02 = production); add a CI gate that blocks release packaging if key identity = dev, (2) add a UDS data identifier `0xF1B0` (Key Identity) readable by production test tools — end-of-line test must verify `0xF1B0 = 0x02`, (3) two-person review required on the signing step approval in CI. I implemented and tested the end-of-line UDS check and CI gate.

**R — Result:**
340 vehicles were recovered via a correctly signed OTA update. The three controls were implemented. No dev-signed firmware reached production in the subsequent 12 months. The end-of-line key identity check was adopted company-wide across all ECU types.

---

### 45. Downgrade Attack Possible via Unprotected Version Field

**S — Situation:**
Security review found that the OTA package manifest contained a plain-text `"target_version": "2.5.3"` field that was not included in the package signature. An attacker who could modify the manifest could set the version field to a high number, causing the anti-rollback check to pass, while actually delivering an old (vulnerable) firmware binary.

**T — Task:**
Validate the attack, assess the exploitability, and validate the fix.

**A — Action:**
I reproduced the attack: I took an old firmware package (v2.4.0), modified its manifest to set `"target_version": "9.9.9"`, and served it from the test OTA server. The TCU's anti-rollback check compared the manifest version field (9.9.9 > current 2.5.3) — passed. The firmware binary CRC was for v2.4.0 — the signature check was only over the binary, not the manifest. The TCU installed the downgraded firmware successfully. This confirmed a real attack vector. Fix: include the manifest contents (version field, VIN list, package hash) in the signed payload — the HSM signs `hash(firmware_binary || manifest_json)`. If the manifest is modified, the signature fails. I validated: modified manifest with correct binary → signature check FAILS, installation rejected. Unmodified manifest with correct binary → PASS.

**R — Result:**
The manifest was added to the signed payload in the next firmware release. The downgrade attack test was added to the OTA security test suite. The fix was also applied to parameter update packages (calibration files), which had the same vulnerability.

---

### 46. HIL Bench Environment Drift Caused False Failures for 2 Weeks

**S — Situation:**
Over a two-week period, the OTA regression test suite was reporting intermittent failures on tests that had been stable for months. The failures appeared random — different tests failing each night, no consistent pattern.

**T — Task:**
Determine whether the failures were genuine regressions in the firmware or environmental noise, and restore test suite stability.

**A — Action:**
I analysed the failure pattern: tests involving network operations (OTA download, MQTT connection) failed most often. Tests involving CAN and UDS were stable. I suspected the network stack. I checked the HIL bench network equipment log: the managed switch had rebooted 14 times in two weeks (indicated by SNMP log). Each reboot caused a 2–4 second network outage. I correlated the switch reboot timestamps with test failure timestamps: 11 out of 14 switch reboots coincided with a test failure within ±10 seconds. The switch was rebooting due to a firmware bug triggered by high multicast traffic from an unrelated PC on the same network segment. I isolated the HIL network: moved it to a dedicated VLAN with no external multicast traffic. I also added a pre-test health check: ping the OTA server and verify MQTT broker reachability before each test; if either fails, abort the test with `INFRA_ERROR` rather than `TEST_FAIL` — distinguishing infrastructure failures from genuine test failures.

**R — Result:**
After network isolation, the test suite returned to 100% stable runs. The `INFRA_ERROR` classification was adopted for all network-dependent tests. The switch was also updated with a firmware patch. The incident led to a bench environment health monitoring system being added to the CI dashboard.

---

### 47. Test Coverage Gap Found by Auditor: Power-Cut Rollback Never Tested

**S — Situation:**
A third-party type-approval auditor reviewing the OTA test evidence for UN ECE R156 noted that no test had been performed for the scenario of power loss during firmware installation. The test plan had a placeholder for this test (`TC-OTA-F020: TBD`) that had never been implemented.

**T — Task:**
Design, implement, and execute the power-cut rollback test within the auditor's corrective action window (3 weeks) and provide evidence for the type-approval file.

**A — Action:**
I designed the test from scratch. I needed a way to cut power at a precise, controllable moment during the flash write. I built a relay control circuit: a USB GPIO controller (Numato 2-channel relay) connected to the bench power supply's enable line. I wrote a Python script that triggered the relay at a configurable delay after observing the first UDS 0x36 (TransferData) message on CAN (detected via a CAN socket listener). I defined four injection points: 10%, 50%, 90%, and 99% of blocks transferred. I ran the test 3 times at each injection point (12 total runs). I captured UART boot logs, CAN traces, and post-recovery UDS version reads for each run. I documented: expected vs. actual state after recovery, boot time after power restore, and whether the previous version was correctly restored. I produced a formal test evidence report with all 12 run results attached.

**R — Result:**
All 12 runs passed (rollback successful, correct version after recovery). The test evidence was accepted by the auditor. TC-OTA-F020 was completed and the TBD status was closed. The test was added to the standard release gating suite. The relay control infrastructure I built was reused for subsequent power interrupt tests on other ECU types.

---

### 48. Wrote OTA Test Plan From Scratch for New Platform in 3 Weeks

**S — Situation:**
The company was launching a new telematics platform (new chipset, new RTOS, first OTA capability on this product line) with a type-approval deadline in 8 weeks. No OTA test plan existed, the firmware was not yet complete, and there was no test engineer assigned to the project.

**T — Task:**
I was assigned as the sole test engineer to create the OTA test plan, set up the HIL environment, and execute all tests within the 8-week window.

**A — Action:**
In week 1, I held a 3-hour kickoff with the firmware architect, OTA server team, and OEM test lab to capture requirements: UN ECE R156 requirements, OEM-specific requirements, and the OTA backend API specification. I produced a test scope document in 2 days. In week 2, I wrote 52 test cases covering: happy path, failure injection (7 scenarios), security (5 scenarios), pre-conditions (4 scenarios), and RXSWIN validation. I used a risk-based prioritisation: critical (run first, block release), high, medium, low. In week 3, I set up the HIL bench: ordered equipment, configured CANoe with vehicle simulation, set up the test OTA backend on a local VM, and wrote the CAPL monitoring scripts. I parallelised test execution with firmware development: I ran stable tests as firmware features were completed rather than waiting for a complete build. By week 6, all critical and high tests were complete. Week 7–8: medium/low tests and defect fix re-verification.

**R — Result:**
Test plan completed in week 2; HIL operational in week 3; all 52 test cases executed by week 8. 11 defects found (3 critical, 5 high, 3 medium). All critical defects resolved and re-validated before the type-approval submission. Type approval achieved in week 9 (one week ahead of original deadline).

---

### 49. Automated Nightly OTA Regression Reduced Cycle Time 80%

**S — Situation:**
The OTA regression test suite required 3 engineers running manual tests for 2 days to complete before each firmware release. This was causing release delays: any late firmware change triggered a full 2-day re-run.

**T — Task:**
Design and implement an automated nightly OTA regression suite that could run without human intervention and provide results by morning.

**A — Action:**
I audited the 52 test cases: 34 were fully automatable (no human judgment required), 12 needed semi-automation (automated execution + manual result review), 6 required purely manual execution (physical relay for power cuts, audio quality judgement for eCall). For the 34 fully automatable cases, I wrote pytest test scripts that: (a) controlled the test OTA backend via REST API to create and trigger campaigns, (b) monitored TCU state via MQTT subscription, (c) read post-OTA state via UDS (python-udsoncan), (d) generated a JUnit XML report consumed by Jenkins. I integrated the relay control into the power-cut tests, automating 3 of the 6 manual tests. I configured a Jenkins pipeline: every night at 23:00, (1) flash baseline firmware via automated JTAG script, (2) run automated test suite (3 hours), (3) publish results to Confluence. Failed tests triggered a Jira ticket automatically and emailed the firmware team.

**R — Result:**
Automated suite covered 37 of 52 tests (71%). Manual regression time dropped from 2 days to 4 hours. Total time from firmware cut to test results: overnight (8 hours) rather than 2 days. Six firmware regressions were caught by the nightly run before morning standup in the 6 months following deployment. Engineers spent the saved time on exploratory testing and new feature test design.

---

### 50. Mentored Junior Engineer to Resolve Cellular Debug Independently

**S — Situation:**
A junior test engineer was assigned to debug an LTE connectivity issue: the TCU was not registering on the network in a new market. After 3 days, they had no progress and escalated to me. They had limited experience with cellular protocols and AT command debugging.

**T — Task:**
Help the junior engineer resolve the issue while ensuring they built the skills to handle similar problems independently in future.

**A — Action:**
Instead of solving the problem for them, I structured a guided debugging session. First, I asked them to describe exactly what they had tried and what data they had collected. They had checked the SIM was provisioned but had not captured the AT command log. I explained the AT command logging setup and asked them to collect it. Together we analysed the log: the modem was sending `AT+COPS=?` (network scan), receiving a list of PLMNs, but `AT+CREG?` showed `+CREG: 0,3` (registration denied). I asked them: "What does +CREG status 3 mean?" They looked it up: registration denied. "What causes that?" — SIM not provisioned for that PLMN, or APN blocked. I walked them through checking the APN table: we found the new market's MCC/MNC was missing from the APN mapping (the same root cause as Scenario 16). They made the fix themselves. I then asked them to write the test case that would have caught this: check APN mapping for every supported market's MCC/MNC. They wrote the test independently. I reviewed and gave feedback on structure and edge cases.

**R — Result:**
The connectivity issue was resolved within 2 hours once we started structured debugging. The junior engineer documented their debugging process as a wiki page: "LTE registration failure — systematic debugging guide." That page is now referenced by 4 other engineers. Three months later, the same engineer resolved a different LTE issue (eSIM profile APN mismatch) independently in one day without escalation.

---

*See also*:
- [10_TCU_OTA_Testing_Guide.md](10_TCU_OTA_Testing_Guide.md) — Full test plan, CAPL scripts, KPIs
- [02_ota_updates.md](02_ota_updates.md) — OTA architecture and UN ECE R156
- [09_cellular_connectivity.md](09_cellular_connectivity.md) — Cellular connectivity scenarios
- [04_remote_diagnostics.md](04_remote_diagnostics.md) — Remote diagnostics protocol
