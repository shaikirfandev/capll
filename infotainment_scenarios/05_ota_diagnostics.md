# Scenarios 21–25 — OTA Updates & Diagnostics
## Infotainment Test Validation — Scenario-Based Interview Prep

---

## Scenario 21 — Head Unit Enters Locked State After Failed OTA

> **Interviewer:** "An OTA update was pushed to head units in the field. 2% of units ended up in a state where the screen shows 'Update Failed — Contact Dealer'. The unit is completely unresponsive to user input. How do you approach the investigation and recovery?"

**Background:**
2% failure rate on a potentially millions-of-units OTA is a critical safety and reputation issue. The locked state could be a hardware failure, SW corruption, or a rollback failure.

**Investigation Path:**

**Step 1 — Characterise the 2%:**
- Are they the same hardware variant, SW version, or geographic market?
- Are they units with low storage? Specific Android version? Specific modem version?
- 2% random → likely environmental (low battery during flash)
- 2% correlated to variant → SW compatibility issue

**Step 2 — Recovery via OBD-II/Ethernet:**
```
Connect to IVI via:
  - OBD-II diagnostics port → UDS 0x10 03 (Extended Session) → UDS 0x27 (Security Access)
  - Engineering serial port (UART/USB-C engineering mode)
  - If IVI runs Android: check if ADB is still accepting connections
    adb devices → if listed, recovery is possible
```

**Step 3 — ADB recovery attempt:**
```bash
adb reboot recovery       # boot into Android recovery mode
# In recovery: apply update from SD card / sideload
adb sideload recovery_image.zip
# This bypasses the failed OTA partition
```

**Step 4 — A/B partition check:**
Modern IVI uses A/B partition scheme:
- Slot A: current running SW
- Slot B: new OTA image
- On failure: should automatically revert to Slot A
```bash
adb shell bootctl get-current-slot     # which slot is active
adb shell bootctl get-suffix 0         # slot A status
adb shell bootctl get-suffix 1         # slot B status
```
If rollback to Slot A failed → the boot loader failed to fallback → hardware or bootloader bug.

**Step 5 — Root cause via telemetry:**
The 2% units should have cloud telemetry logged before they locked.
```json
{
  "unit_id": "VIN-XXXXX",
  "ota_start_time": "2026-04-10T14:22:00Z",
  "battery_voltage_at_start": 11.8,
  "download_complete": true,
  "flash_start": true,
  "flash_percent_complete": 87,
  "error_code": "FLASH_WRITE_TIMEOUT",
  "battery_voltage_at_fail": 10.9
}
```
Low battery during flash → power interruption to NAND at 87% → partial write → neither Slot A nor Slot B bootable.

**Test Cases:**
```
TC_OTA_LOCK_001: OTA update with battery at 12V → must complete successfully
TC_OTA_LOCK_002: OTA update with battery at 11.5V → system must refuse to start flash (not risk partial write)
TC_OTA_LOCK_003: Power cut at 50% through OTA flash → system must boot from Slot A (rollback)
TC_OTA_LOCK_004: Power cut at 95% through OTA flash → system must boot from Slot A (never partial)
TC_OTA_LOCK_005: OTA failure recovery → unit must be recoverable via service tool within 15 min
TC_OTA_LOCK_006: OTA pre-check must validate: free storage ≥ 150%, battery ≥ 12.5V, engine running
```

**Root Cause Summary:**
OTA flash was permitted to begin at battery voltage 11.8V. Mid-flash, user turned on AC compressor which caused voltage dip to 10.9V → insufficient power for NAND write → partial block write → both A/B partitions corrupted. Fix: (1) Require engine running (charging at 13.8V) for OTA flash. (2) Add hardware write-protect at voltage < 11.0V.

---

## Scenario 22 — Multiple DTCs Appear After Factory Reset

> **Interviewer:** "A customer performs a factory reset on their IVI system (via Settings → System → Factory Reset). After the reset, the instrument cluster shows 5 new warning lights including an airbag warning. The vehicle was perfectly fault-free before the reset. What happened?"

**Investigation Path:**

**Step 1 — What does factory reset do?**
Factory reset on the IVI should only reset:
- User preferences (Bluetooth pairings, navigation history, account data)
- IVI application data (media libraries, app settings)

It should NOT reset:
- ECU calibration data
- Stored DTCs from other ECUs
- Vehicle configuration data (VIN, variant coding)

**Step 2 — Check which ECU the DTCs are on:**
```
The airbag warning is owned by the Airbag ECU (SRS) — NOT the IVI.
How is the IVI factory reset affecting the SRS ECU?
```
Check: are these new DTCs on the IVI ECU itself, or on other ECUs (SRS, BCM, ABS)?

**Step 3 — CAN bus disruption during reset:**
Factory reset involves full IVI reboot — during reboot, the IVI stops sending CAN messages.
Other ECUs may have CAN timeout DTC logic:
- SRS ECU expects a message from IVI every 100ms
- If IVI is silent for 5s during reset → SRS logs U0100 (lost communication with IVI)
- U0100 triggers SRS warning light

**Step 4 — Reset scope creep:**
Using UDS, check if the factory reset command on IVI inadvertently sends a 0x14 (ClearAllDTCs) or 0x2E (WriteDataByID) to other ECUs.
Some factory reset implementations incorrectly clear VIN or variant coding on the SRS/BCM.

**Step 5 — Variant coding loss:**
If the IVI stores the vehicle variant code (5-door vs 3-door, diesel vs petrol) and factory reset wipes this:
- Variant code transmitted to SRS ECU on boot is now "default" (blank)
- SRS ECU receives different variant than it was configured with → configuration mismatch DTC

**Required Test:**
```
Pre-condition: Vehicle with 0 DTCs, all ECU configurations verified
Action: Perform IVI factory reset
Post-check:
  UDS 0x19 02 FF on: IVI, SRS, BCM, ABS, ADAS → must show 0 new DTCs after reset
  UDS 0x22 VIN DID on each ECU → VIN must match before and after reset
  All warning lights on cluster must remain OFF after reset + 60 second key cycle
```

**Test Cases:**
```
TC_FRESET_001: IVI factory reset → 0 new DTCs on any ECU
TC_FRESET_002: IVI factory reset → cluster shows 0 new warning icons after restart
TC_FRESET_003: IVI factory reset → VIN, variant coding, calibration data identical before/after
TC_FRESET_004: IVI factory reset → Bluetooth pairings cleared, navigation history cleared
TC_FRESET_005: IVI factory reset during active phone call → call ends gracefully, no DTC
TC_FRESET_006: IVI factory reset → vehicle speed, odometer, trip computer unaffected
```

**Root Cause Summary:**
IVI reboot during factory reset caused a 12-second CAN bus silence. SRS ECU has a 5-second timeout threshold for the IVI heartbeat message — after 5 seconds with no heartbeat, SRS logs U0100 and activates airbag warning. Fix: IVI should send a "shutdown notification" CAN message before entering reset to suppress timeout-based DTCs on other ECUs.

---

## Scenario 23 — UDS 0x22 Returns Wrong Software Version After OTA Update

> **Interviewer:** "After an OTA update to IVI SW version 3.2, a UDS 0x22 request for the SW version DID returns v3.1 (the old version). The vehicle clearly has new features from v3.2 running. What could cause this?"

**Investigation Path:**

**Step 1 — What stores the SW version?**
SW version information can be stored in:
- The application binary itself (hardcoded string)
- NVM / flash calibration area (programmable during flashing)
- A dedicated version management ECU function

**Step 2 — NVM not updated by OTA:**
The OTA process may have updated the application code (new features work) but failed to write the version string to the NVM version DID.
This is a defect in the OTA flashing sequence.

**Step 3 — DID read source:**
```
IVI SW version DID 0xF189:
  Source could be:
  a) Hardcoded in compile-time constant → updated automatically with new binary ✓
  b) Read from NVM at address 0x00A0 → must be explicitly written during OTA ← possible bug
  c) Read from bootloader version area → bootloader unchanged by OTA ← common issue
```
If the DID reads from the bootloader area and the bootloader was not updated by the OTA, it still returns the old version.

**Step 4 — Verify via ADB:**
```bash
adb shell getprop ro.build.version.release          # Android OS version
adb shell getprop ro.build.display.id               # Build ID (contains SW version)
adb shell cat /etc/build.prop | grep version        # More detailed version info
```
If ADB shows v3.2 but UDS returns v3.1 → UDS DID handler is reading from wrong source.

**Step 5 — Version DID write in OTA script:**
Review OTA update script (typically a shell script or update-binary):
```bash
# Should include this line after flashing:
busybox echo -n "SW_V3.2.0" > /dev/block/by-name/version_info
# Or via UDS write during EOL re-programming:
# 0x2E 0xF189 [version bytes]
```
If this line is missing → version NVM not updated → UDS reads old value.

**Test Cases:**
```
TC_VER_001: After OTA v3.2 → UDS 0x22 0xF189 returns "3.2.0" (exact match to deployed version)
TC_VER_002: Multiple OTA updates in sequence → version DID always matches last installed version
TC_VER_003: Factory reset after OTA → version DID still returns post-OTA version (not factory version)
TC_VER_004: UDS 0x22 0xF180 (bootloader version) → correct bootloader version returned
TC_VER_005: UDS 0x22 0xF18C (ECU serial) → unchanged before and after OTA
TC_VER_006: Version DID readable in all UDS sessions (Default, Extended, Programming)
```

**Root Cause Summary:**
The OTA update script updates the application partition but does not write to the NVM version DID area. The UDS 0x22 handler reads version from NVM (a historical decision from the EOL programming process) rather than from the binary itself. Fix: add a post-flash step in the OTA script to write the version string to the NVM version DID, mirroring the EOL programming sequence.

---

## Scenario 24 — DTC Cleared But Warning Light Does Not Extinguish for 2 Drive Cycles

> **Interviewer:** "A technician clears all DTCs with a scan tool (UDS 0x14). The DTC disappears from the DTC list, but the warning light on the cluster remains ON. The light only goes off after 2 complete drive cycles. Is this a bug?"

**Strong Answer:**

**This is NOT a bug — this is correct ISO 14229 / OBD-II behaviour. But it's important to be able to explain it clearly.**

**The concept: Readiness Monitors and Healing Cycles**

When a DTC is cleared via 0x14:
1. The DTC is removed from the confirmed DTC list ✓
2. The test monitor status is set to "not completed" (bit 4 = 1)
3. The warning lamp must remain ON until the monitor runs and passes

The warning lamp turns off ONLY when:
- The diagnostic monitor for that fault runs successfully (enabling conditions met)
- Monitor result = PASS (no fault detected)
- This typically requires 1–2 complete drive cycles

**The drive cycle requirement:**
```
Monitor enabling conditions (example: O2 sensor monitor):
  - Engine warm (coolant temp > 70°C) ✓
  - Engine run time > 5 minutes ✓
  - Vehicle speed between 40–100 km/h for > 2 min ✓
  - Engine load > 30% ✓
All conditions met in one drive cycle = "readiness complete"
Warning lamp extinguishes
```

**When it IS a bug:**
- DTC cleared → warning lamp stays on after 5 complete drive cycles (monitor never runs to completion)
- DTC cleared → monitor reports PASS but lamp still on → lamp persistence logic bug
- DTC cleared → lamp off immediately with no monitor run → OBD-II compliance failure

**CAPL Readiness Monitor Test:**
```capl
// Monitor DTC status byte changes through healing cycle
on signal ADAS_ECU::DTC_ReadinessStatus {
  write("Readiness Monitor Status: 0x%02X", this.value);
  // Bit 0 = testFailed (currently failed)
  // Bit 4 = testNotCompletedSinceLastClear
  // Bit 5 = testFailedSinceLastClear
  // When bit 0 = 0 AND bit 4 = 0 → monitor passed → lamp should clear

  if ((this.value & 0x11) == 0x00) {
    write("PASS — Monitor complete, no fault → warning lamp should extinguish");
  }
}
```

**Test Cases:**
```
TC_DTC_HEAL_001: Clear DTC → drive cycle 1 complete → DTC monitor completes → warning lamp OFF
TC_DTC_HEAL_002: Clear DTC → immediately check DTC list → DTC not present (cleared correctly)
TC_DTC_HEAL_003: Clear DTC → no drive cycle → warning lamp remains ON (correct per OBD-II)
TC_DTC_HEAL_004: Clear DTC → fault reoccurs in same drive cycle → DTC re-sets, lamp stays ON
TC_DTC_HEAL_005: 5 drive cycles after clear → if lamp still ON → flag as monitor never completing
TC_DTC_HEAL_006: Verify specific DTC healing cycle count matches OEM spec (1 cycle or 2 cycles)
```

**Interview Answer Summary:**
"This is expected behaviour. ISO 14229 defines that after a DTC clear, the warning lamp remains on until the diagnostic monitor that detected the fault completes successfully — which requires specific driving conditions to be met. If the lamp stays on beyond the expected number of healing cycles, then it becomes a bug. I would check the monitor enabling conditions and verify that they are achievable in the test drive cycle."

---

## Scenario 25 — IVI ECU Responds to UDS Requests from Unauthorised Tool

> **Interviewer:** "During security audit, it was found that an off-the-shelf OBD-II scan tool can read private data DIDs from the IVI using UDS 0x22 — including location history, paired phone numbers, and user account tokens. This should be restricted. How do you fix and test this?"

**Background:**
This is a security vulnerability. UDS security is controlled by:
- Session requirements (which session allows which service)
- Security Access levels (0x27 seed/key challenge)
- Access Control (which DIDs are readable in which session)

**Root Cause Analysis:**

**Issue 1 — Private DIDs readable in Default Session:**
Private data DIDs (location history, phone numbers) should only be readable in:
- Extended Diagnostic Session (0x10 03) with Security Access Level ≥ 0x03
A standard scan tool operates in Default Session (0x10 01) → these DIDs should return NRC 0x31 (Request Out of Range) or NRC 0x33 (Security Access Denied).

**Issue 2 — Security Access too weak:**
If Security Access uses a simple XOR seed/key algorithm:
```
Seed: 0x1234ABCD
Key:  Seed XOR 0xDEADBEEF = 0xCC99153C
```
A reverse engineer can determine the XOR mask in minutes → security access bypassed.

**Fix:**

1. **Implement DID session control matrix:**
```
DID 0xF100-0xF1FF (Standard DIDs): readable in any session (compliant)
DID 0x0200-0x02FF (User data DIDs): Extended Session + Security Level 3 required
DID 0x0300-0x03FF (Private/OEM DIDs): Programming Session + Security Level 5 required
```

2. **Strengthen Security Access:**
- Replace XOR algorithm with HMAC-SHA256 challenge-response
- Rotate seed on every request
- Lock ECU after 3 failed attempts (add delay: 10s, 60s, 1000s)

3. **Firewall at OBD-II port:**
- Only allow UDS on functional address (0x7DF) for standard OBD-II PIDs
- Route private UDS to secured CAN segment not accessible from OBD-II port

**Test Cases:**
```
TC_SEC_001: Default session → read private DID 0x0201 → must return NRC 0x31 or 0x33
TC_SEC_002: Extended session without security access → read private DID → must return NRC 0x33
TC_SEC_003: Extended session + correct security access → read private DID → returns data
TC_SEC_004: 3 wrong security key attempts → ECU locks for 10 seconds (NRC 0x37 = requiredTimeDelayNotExpired)
TC_SEC_005: Security seed must be different on every request (no static seeds)
TC_SEC_006: Penetration test with standard OBD-II tools → no private data accessible without security access
TC_SEC_007: Programming session (0x10 02) required for write DIDs — must fail in default session
```

**CAPL Security Test:**
```capl
// Security access test — verify brute force protection
variables {
  int gAttempts = 0;
  msTimer tmrRetry;
}

on start {
  // Attempt 3 wrong keys
  sendSecurityAccess(0x27, 0x03, 0xDEADBEEF);  // wrong key
}

on diagResponse IVI_ECU.SecurityAccess {
  gAttempts++;
  if (diagGetRespPrimitiveByte(this, 0) == 0x7F &&
      diagGetRespPrimitiveByte(this, 2) == 0x36) {
    write("PASS [Attempt %d] — Wrong key rejected (NRC 0x36 ExceededNumberOfAttempts)", gAttempts);
  }
  if (gAttempts < 3) {
    sendSecurityAccess(0x27, 0x03, 0xBADC0FFE);  // another wrong key
  } else {
    // 4th attempt should get NRC 0x37 (time delay not expired)
    setTimer(tmrRetry, 100);
  }
}

on timer tmrRetry {
  sendSecurityAccess(0x27, 0x03, 0x00000001);
  // expect NRC 0x37 — ECU locked, delay not expired
}
```

**Root Cause Summary:**
Private DIDs were not included in the DID access control matrix during SW development — all DIDs were initially implemented as readable in any session for development convenience and the access restrictions were never applied before production release. This is a development lifecycle failure: security requirements were not tracked as test cases and were not part of the pre-production validation gate.

---
*File: 05_ota_diagnostics.md | Scenarios 21–25 | April 2026*
