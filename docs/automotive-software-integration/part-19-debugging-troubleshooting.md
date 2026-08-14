# Part 19 — Debugging & Troubleshooting

---

## Format for Each Scenario

**Symptom → Possible Causes → Investigation → Tools → Logs → Root Cause → Fix → Prevention**

---

## 19.1 ECU Does Not Boot

**Symptom:** ECU powers on but no CAN activity, no response to diagnostic requests.

**Possible Causes:**
- Clock configuration incorrect
- Bootloader flash corrupt
- Application CRC check fails → stays in bootloader
- Power supply issue (under-voltage)
- Pin not connected (reset pin held low)

**Investigation:**
1. Measure supply voltage at ECU connector
2. Attach Trace32 via JTAG → check if CPU is executing
3. Check reset pin state
4. Check bootloader log via UART debug port

**Tools:** Oscilloscope, Trace32, UART terminal, multimeter

**Logs:**
```
UART debug output:
  [BOOT] Initializing clocks... OK
  [BOOT] Checking application CRC...
  [BOOT] CRC MISMATCH! Staying in programming mode.
```

**Root Cause:** Wrong firmware binary flashed (wrong HW variant)

**Fix:** Flash correct firmware binary

**Prevention:** Add HW variant check in build system; label binaries clearly

---

## 19.2 ECU Does Not Communicate on CAN

**Symptom:** ECU present but no CAN messages visible in CANoe.

**Possible Causes:**
- CAN bit timing mismatch
- Wrong CAN channel selected in software
- CAN transceiver fault
- ECU in bus-off state
- CanIf/CanSM misconfigured

**Investigation:**
1. CANoe: check if bus has any activity at all
2. Oscilloscope on CAN-H/CAN-L: check physical signal levels
3. Check CAN bit timing configuration in ECUC
4. Read DTC: check if CAN bus-off DTC is set

**Tools:** CANoe, oscilloscope, Trace32

**Root Cause:** Bit timing mismatch (ECU configured for 250 kbps, bus runs at 500 kbps)

**Fix:** Correct CanDrv bit timing parameters; regenerate BSW configuration

**Prevention:** CI check: compare bit timing config against network requirements doc

---

## 19.3 CAN/Ethernet Communication Failure

**Symptom:** Expected signals missing or intermittent.

**Possible Causes:**
- Missing DBC signal configuration
- PDU routing misconfigured in PduR
- VLAN misconfigured (Ethernet)
- Network cable fault

**Investigation:**
1. CANoe: load DBC, check if message arrives at all
2. Check PduR routing table in ECUC
3. Wireshark: verify Ethernet packets and VLAN tags

**Root Cause (example):** PduR routing path missing for new signal

**Fix:** Add missing routing path in PduR configuration; regenerate

---

## 19.4 SOME/IP Service Unavailable

**Symptom:** Client cannot find/use a SOME/IP service.

**Investigation:**
1. Wireshark filter: `udp.port == 30490` → check for OfferService messages
2. Verify server ECU is running and service is offered
3. Check VLAN assignment: server and client on same VLAN?
4. Check firewall rules on Linux IVI/ADAS

**Root Cause (example):** Server ECU on VLAN 100, client on VLAN 200; no routing between

**Fix:** Add VLAN routing rule on central gateway

---

## 19.5 ECU Flashing Failure

**Symptom:** UDS flashing fails with negative response code.

**Common NRC (Negative Response Codes):**

| NRC | Code | Meaning |
|---|---|---|
| conditionsNotCorrect | 0x22 | Pre-conditions not met (speed > 0) |
| requestSequenceError | 0x24 | Services called out of order |
| securityAccessDenied | 0x33 | Security access failed |
| requestOutOfRange | 0x31 | Address/size out of valid range |
| generalProgrammingFailure | 0x72 | Flash write error |

**Investigation:**
1. CANoe DiagVIEW: observe exact NRC
2. Verify flashing sequence: session → security → erase → download
3. Check security seed/key algorithm

**Root Cause (example):** Security key derivation mismatch between tester and ECU

**Fix:** Align key algorithm in tester script and ECU firmware

---

## 19.6 UDS Diagnostic Failure

**Symptom:** DID read returns wrong value or NRC.

**Investigation:**
1. Send 0x22 DID request in CANoe DiagVIEW
2. Check response: NRC 0x31 (out of range) = DID not configured
3. Verify Dcm configuration: DID handler registered?

**Root Cause (example):** New DID added to spec but not configured in Dcm ECUC

**Fix:** Add DID entry in DaVinci Configurator → regenerate → rebuild → flash

---

## 19.7 Unexpected DTC

**Symptom:** DTC appears at startup or intermittently.

**Investigation:**
1. Read DTC via 0x19 in CANoe
2. Check DTC status: confirmed vs pending
3. Find Dem event for this DTC in ECUC
4. Find where `Dem_ReportErrorStatus()` is called in code
5. Add breakpoint in Trace32 at that call

**Root Cause (example):** DTC P0101 (MAF sensor) set because analog input not initialized before DEM check

**Fix:** Delay DEM check by 50ms after startup (adjust initialization sequence)

---

## 19.8 Wrong CAN Signal / Endianness Error

**Symptom:** Signal value appears wrong (e.g., speed shows 25,600 instead of 100).

**Investigation:**
1. CANoe: show raw hex bytes of message
2. Compare against DBC signal definition
3. Check Intel vs Motorola byte order in COM configuration

**Root Cause (example):** Signal configured as Intel (little-endian) in DBC but COM module configured as Motorola (big-endian)

**Fix:** Align byte order between DBC and COM ECUC configuration

---

## 19.9 Timing Mismatch / Timeout / Watchdog Reset

**Symptom:** ECU resets periodically; DTC for watchdog timeout.

**Investigation:**
1. Trace32: set breakpoint on WdgM_MainFunction
2. Profile task execution times
3. Check if any task exceeds its execution time budget

**Root Cause:** New algorithm added to 1ms task takes 3ms → task overrun → WdgM timeout → reset

**Fix:** Move heavy computation to lower-priority 10ms task

---

## 19.10 Memory Corruption / CPU Overload / Memory Leak

**Symptom:** ECU works initially then behaves erratically; eventually crashes.

**Investigation:**
1. Trace32: monitor stack usage over time
2. Trace32: watch heap pointer growth (if dynamic alloc used)
3. Check task stack sizes in AUTOSAR OS configuration

**Root Cause (example):** Stack overflow in CAPL event handler due to deeply nested function calls

**Fix:** Increase stack size for affected task; optimize call depth

---

## 19.11 OTA Update Failure

**Symptom:** OTA campaign shows vehicles stuck at "Downloading" or "Failed".

**Investigation:**
1. TCU logs: check download progress, TLS errors
2. Check cellular signal strength
3. Verify server certificate not expired
4. Check available storage on TCU flash

**Root Cause (example):** OTA server certificate expired → TLS handshake fails

**Fix:** Renew server certificate; update pinned certificate in TCU if certificate pinning used

---

## 19.12 Android Service Crash (IVI)

**Symptom:** Infotainment feature not working; Android keeps restarting a service.

**Investigation:**
```bash
adb logcat -v time | grep "FATAL\|crash\|AndroidRuntime"
adb bugreport  # collect full system log
```

**Root Cause (example):** CarService NPE (NullPointerException) when VHAL property not initialized

**Fix:** Add null check before accessing VHAL property; initialize property on startup

---

## 19.13 Cluster Display Freeze

**Symptom:** Cluster display stops updating; shows last state.

**Investigation:**
1. Check GPU load (Linux: `sudo radeontop` or `cat /sys/kernel/debug/dri/0/`)
2. Check Wayland compositor process status
3. Review display driver logs

**Root Cause (example):** GPU driver memory leak after 8 hours → OOM killer terminates compositor

**Fix:** Update GPU driver; add memory watchdog; auto-restart compositor on failure

---

## 19.14 ADAS Sensor Data Missing

**Symptom:** ADAS feature disabled; DTC for sensor communication failure.

**Investigation:**
1. CANoe: check if sensor CAN/Ethernet messages present
2. Verify sensor power supply
3. Check sensor fault codes via LIN/CAN diagnostics

**Root Cause (example):** Radar power relay not energized due to BCM relay control error

**Fix:** Fix BCM relay control logic; add DTC for relay failure

---

## Summary

| Problem | First Tool to Use |
|---|---|
| ECU won't boot | Trace32 JTAG + UART debug |
| No CAN traffic | Oscilloscope + CANoe |
| SOME/IP unavailable | Wireshark |
| Flashing fails | CANoe DiagVIEW NRC analysis |
| DTC unexpected | CANoe 0x19 + Trace32 breakpoint |
| Memory leak | Trace32 heap monitor |
| Android crash | adb logcat |
| OTA failure | TCU log analysis |

---

*Next: [Part 20 — Real-World Case Studies](part-20-case-studies.md)*
