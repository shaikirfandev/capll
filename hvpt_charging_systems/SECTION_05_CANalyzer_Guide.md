# SECTION 5 — CANalyzer COMPLETE LEARNING GUIDE
## Bus Analysis, Signal Monitoring, Network Debugging

---

## 5.1 CANalyzer OVERVIEW

### 5.1.1 CANalyzer vs CANoe

| Feature | CANalyzer | CANoe |
|---------|-----------|-------|
| Bus Monitoring | ✓ Full | ✓ Full |
| Signal Decoding | ✓ Full | ✓ Full |
| Logging & Replay | ✓ Full | ✓ Full |
| ECU Simulation | Limited | ✓ Full |
| CAPL Scripting | Limited | ✓ Full |
| Test Modules | ✗ | ✓ Full |
| Panel Design | Limited | ✓ Full |
| UDS Diagnostics | ✓ Basic | ✓ Advanced |
| Cost | Lower | Higher |
| Primary Use | Analysis | Simulation + Test |

**Rule:** Use CANalyzer for monitoring and analysis. Use CANoe when you need simulation, automation, or test execution.

---

## 5.2 TRACE WINDOW ANALYSIS

### 5.2.1 Trace Window Features

```
TRACE WINDOW — KEY FEATURES:
──────────────────────────────────────────────────────────────
DISPLAY OPTIONS:
  ├── Message view: One row per CAN frame
  ├── Signal view: Decoded signal values per message
  ├── Error frame highlighting (shown in red)
  ├── BusOff/WakeUp event markers
  └── Timestamp formats: absolute/relative/delta

COLUMN CONFIGURATION:
  ✓ Time             — timestamp (use relative for timing analysis)
  ✓ Channel          — which CAN channel (1, 2, 3...)
  ✓ ID               — message ID (hex or decimal)
  ✓ Name             — message name from DBC
  ✓ Direction        — Rx (received) or Tx (transmitted)
  ✓ DLC              — data length
  ✓ Data             — payload bytes in hex
  ✓ Decoded Signals  — show signal values inline
  ✓ Counter          — how many times this message received
  ✓ Cycle Time       — measured cycle time (vs expected)

FILTERING:
  Highlight Filter: Color messages by ID/name for visual grouping
  Display Filter:   Show ONLY specific messages
  Storage Filter:   Only log specific messages (saves disk space)
```

### 5.2.2 Reading Raw CAN Traces — Expert Level

```
TRACE ANALYSIS EXERCISE:
──────────────────────────────────────────────────────────────
Time       Chan  ID    D  Data
0.000000   1     0310  8  00 E8 00 C8 00 7A 00 00
0.010012   1     0310  8  00 E8 00 C8 01 7A 00 00  ← change in byte 4!
0.020009   1     0310  8  00 E8 00 C8 01 7B 00 00  ← change in byte 5!
0.000000   1     0100  8  01 00 00 00 00 00 00 00
0.010000   1     0100  8  01 00 00 00 00 00 00 00

ANALYSIS:
  Message 0x310 = BMS_Status
  Bytes 0–1: 0x00E8 = 232 decimal → BMS_SoC: 232 × 0.5 = 116% ??? WRONG!
  Check DBC: BMS_SoC is bits 0–15, Intel, factor = 0.5
  Raw = 0x00E8 little endian: byte0=0x00, byte1=0xE8
  Raw value = byte0 + byte1×256 = 0 + 232×256 = 59392
  Physical = 59392 × 0.5 = 29696% ← CLEARLY WRONG

  RE-CHECK: Maybe signal is 8-bit, not 16-bit?
  BMS_SoC = bits 0–7 = byte0 = 0x00 = 0 → 0 × 0.5 = 0% ← wrong
  
  Check correct DBC: BMS_SoC bits 8–15 = byte1 = 0xE8 = 232
  Physical = 232 × 0.5 = 116% ← STILL WRONG, DBC issue confirmed
  
  With correct factor 0.1: 232 × 0.1 = 23.2% ← Makes sense!
  → DBC has wrong factor, correct is 0.1 not 0.5

LESSON: Always verify DBC against ECU software specification!
```

---

## 5.3 SIGNAL MONITORING

### 5.3.1 Signal Monitor Window

```
SIGNAL MONITOR SETUP:
──────────────────────────────────────────────────────────────
1. Open Signal Monitor: Measurement → Signal Monitor
2. Add signals:
   Double-click signal in DBC tree OR drag from Symbols window
   
3. Configure display:
   ├── Numerical: Shows current value with units
   ├── Bar graph: Progress bar for percentage signals
   ├── LED: On/Off for boolean signals
   └── Analog: Gauge display

4. Set min/max alarm:
   Right click signal → Properties → Alarm
   ├── Low warning:  BMS_PackVoltage < 300V
   ├── High warning: BMS_PackVoltage > 420V
   └── Alarm color: Yellow (warning), Red (critical)

5. Color coding:
   Green = within normal range
   Yellow = warning level
   Red = fault level
```

### 5.3.2 Statistics Window

```
BUS STATISTICS (CANalyzer):
──────────────────────────────────────────────────────────────
1. Measurement → Bus Statistics
   
2. Shows per-message statistics:
   Message      │ Count │ Avg Period │ Min Period │ Max Period │ Last Rx
   ─────────────────────────────────────────────────────────────────────
   BMS_Status   │ 10243 │ 10.02 ms  │ 9.85 ms   │ 11.24 ms  │ 0.002s
   VCU_Command  │ 10241 │ 10.01 ms  │ 9.90 ms   │ 10.95 ms  │ 0.002s
   OBC_Status   │ 1024  │ 100.2 ms  │ 98.5 ms   │ 103.1 ms  │ 0.015s
   
3. CAN Bus statistics:
   Total frames: 52,841
   Error frames: 0 ← should always be 0 in healthy network
   Bus load: 38.2%
   TX frames: 12,450
   RX frames: 40,391

4. Error statistics:
   Bit errors: 0
   Stuff errors: 0
   CRC errors: 0
   ACK errors: 0
   BusOff events: 0
```

---

## 5.4 PRACTICAL DEBUGGING EXERCISES

### 5.4.1 Exercise 1 — Missing CAN Message

```
SCENARIO: BMS_Status message (0x310) is missing from CAN bus

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Open Trace Window
  → Search for 0x310 in trace
  → No messages found → confirmed missing

STEP 2: Check Bus Health
  → Statistics window → Error frames = 0 → Bus itself is healthy
  → Other messages present → Bus is functional
  → BMS is NOT transmitting at all

STEP 3: Check BMS Power
  → Measure BMS power pin with multimeter (separate from CANalyzer)
  → Voltage OK → ECU powered

STEP 4: Check BMS CAN Bus connectivity
  → Is BMS even on this CAN channel?
  → Check ICD: BMS is on Powertrain_CAN, Channel 1 → correct

STEP 5: Check BMS State
  → Can we communicate with BMS via diagnostics?
  → Send UDS: 10 01 (Default Session) → No response
  → BMS not responding at all → might be in BusOff, or in sleep, or crashed

STEP 6: Force BMS wakeup
  → Send NM (Network Management) wakeup frame if applicable
  → Key cycle: power off → wait 5s → power on
  → BMS_Status appears in trace → Problem was BMS in shutdown state

ROOT CAUSE: VCU was not sending wakeup/ignition signal to BMS.
            BMS remained in sleep state.
FIX: Verify VCU_IgnitionStatus signal is transmitted before expecting BMS.
```

### 5.4.2 Exercise 2 — Wrong Signal Value

```
SCENARIO: BMS_SoC always shows 0% in CANalyzer

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Verify message is present
  → BMS_Status (0x310) IS in trace ✓

STEP 2: Raw data check
  Trace shows: 0x310: 00 00 00 C8 00 7A 00 00
  BMS_SoC decoded: 0%
  
STEP 3: Manual decode
  BMS_SoC defined as: bits 0–15, Intel byte order, factor=0.5
  Bytes 0–1 (little endian): byte0=0x00, byte1=0x00
  Raw value = 0x0000 = 0
  Physical = 0 × 0.5 = 0% ← BUT battery should be at 50%!

STEP 4: Check DBC vs ECU SW notes
  ECU SW version 3.1 release note:
  "BMS_SoC signal moved from bytes 0–1 to bytes 1–2 (new start bit = 8)"
  
STEP 5: Verify with updated start bit
  Bytes 1–2 (Intel): byte1=0x00, byte2=0x00 = 0 → still 0%?
  
  Wait — raw data is: 00 00 00 C8 ...
  Let's try bytes 2–3: byte2=0x00, byte3=0xC8 = 0x00C8 = 200
  Physical = 200 × 0.5 = 100% ← too high
  With factor 0.1: 200 × 0.1 = 20% ← plausible
  
STEP 6: Get correct DBC from ECU team
  New DBC: BMS_SoC = bits 16–23, factor=0.1
  After updating DBC → BMS_SoC shows 20% ← matches real SoC

ROOT CAUSE: DBC file was outdated (old SW version)
FIX: Always use DBC that matches ECU SW version in release notes.
LESSON: Keep DBC files version-controlled, linked to SW releases.
```

### 5.4.3 Exercise 3 — Timeout Issue

```
SCENARIO: VCU reports "BMS_Timeout fault" but BMS seems to be transmitting

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Measure actual period
  Signal Statistics: BMS_Status average period = 10.02ms ✓
  BUT: Max period = 85.3ms ← SPIKE DETECTED!

STEP 2: Find the spike in trace
  Sort trace by: time gap between messages
  Found: At time 42.158s, gap between two BMS_Status = 85ms
  
STEP 3: What happened at t=42.158s?
  Search trace around that time:
  42.050s: BMS_CellVoltage_ALL (large CAN FD message, 64 bytes)
  42.051s: BMS_CellVoltage_ALL
  42.052s: BMS_CellVoltage_ALL (many in burst)
  ...
  42.158s: BMS_Status (gap = 85ms!)
  
STEP 4: Root cause hypothesis
  BMS transmits a burst of CellVoltage frames, which delays BMS_Status
  CAN FD 64-byte frame at 2Mbit/s = ~300µs per frame
  20 frames in burst = 6ms burst → shouldn't cause 85ms delay...
  
  But: BMS_CellVoltage is at 500kbit/s (NOT FD!)
  20 frames × 1.0ms/frame = 20ms burst
  Plus bus arbitration delays...
  
STEP 5: Check CAN task scheduling in BMS
  → BMS SW uses same OS task for both messages
  → Task overrun during cell data burst causes 10ms task delay
  → Multiple task delays compound → 85ms total gap

ROOT CAUSE: BMS OS task scheduling conflict. CellVoltage transmission
            delays BMS_Status transmission beyond VCU timeout threshold.
FIX: Separate CAN transmit tasks, or increase VCU timeout to 100ms.
     BMS SW team: split BMS_Status to higher-priority OS task.
```

### 5.4.4 Exercise 4 — ECU No Response

```
SCENARIO: OBC doesn't respond to UDS diagnostics during charging

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Check OBC is transmitting
  → OBC_Status (0x620) IS present in trace ✓ → OBC is alive

STEP 2: Check UDS session
  → Send: 10 01 (Default Session Request)
  → No response after 50ms ← UDS not responding

STEP 3: Check OBC diagnostics address
  → CAN ID for OBC diag request: 0x741 (physical address)
  → CAN ID for OBC response: 0x749
  → Search trace for 0x749: NOT FOUND ← no response from 0x749

STEP 4: Verify diagnostic addresses
  → Check ICD: OBC Phys Request = 0x741, Response = 0x749 ✓
  → But trace shows request sent to 0x741 with no reply
  
STEP 5: OBC CommunicationControl state
  → OBC may have disabled diagnostic communication (UDS 0x28)
  → Check OBC status signal: OBC_DiagEnabled = 0 ← DISABLED!

STEP 6: Why is DiagEnabled = 0?
  → Read OBC_Status: OBC_State = CHARGING
  → During active charging, OBC disables diagnostics (by design)
  → This is documented in OBC specification: "Diagnostics inhibited during charge"

ROOT CAUSE: Expected behavior — diagnostics disabled during active charging.
FIX: Stop charging session first, then perform diagnostics.
LESSON: Always check ECU specification for diagnostic access conditions.
```

### 5.4.5 Exercise 5 — Bus Off Condition

```
SCENARIO: Entire Powertrain CAN bus stops working for 1 second, then recovers

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Examine error frames in trace
  Time 15.230s: Error frame #1
  Time 15.230s: Error frame #2
  Time 15.230s: Error frame #3 ... (burst of 100+ error frames)
  Time 15.231s: BusOff event detected on Channel 1
  Time 16.250s: Bus normal (ECU recovered)
  
STEP 2: What triggered the error frames?
  Just before error burst at 15.229s:
  15.229s: 0x410 INV_Status (normal)
  15.230s: 0x410 INV_Status — DATA CHANGED: byte7 from 0x00 to 0xFF
  15.230s: ← ERROR FRAMES START

STEP 3: What changed in INV_Status byte7?
  0xFF in byte7 → All status bits = 1 → FAULT STATE
  Check DBC: Byte 7 = INV_FaultCode (bitmap)
  0xFF = all fault bits set simultaneously
  → INV_FaultCode = overvoltage + overcurrent + overtemp + all faults at once
  → This is NOT a real inverter fault — all bits at once = HW glitch

STEP 4: What causes HW glitch?
  Review event log: At t=15.229s: Thermal chamber reached -40°C test point
  → Cold temperature caused CAN transceiver supply voltage to drop momentarily
  → Inverter CAN transceiver misbehaved → sent invalid frame
  → Error burst → TEC overflow → BusOff

ROOT CAUSE: INV CAN transceiver undervoltage at extreme cold temperature.
            Supply voltage (3.3V for transceiver) dipped below minimum (3.0V).
FIX: Hardware fix — add decoupling capacitor on inverter CAN transceiver supply.
     SW workaround — increase ECU BusOff recovery timeout.
```

### 5.4.6 Exercise 6 — CAN FD Issues

```
SCENARIO: CAN FD messages corrupted intermittently

DEBUGGING APPROACH:
──────────────────────────────────────────────────────────────
STEP 1: Identify CAN FD errors
  Filter trace: Show only error frames
  Found: 3 CRC errors on CAN FD messages in 1-hour test

STEP 2: When do errors occur?
  All 3 errors at cable length > 5m in test harness
  
STEP 3: CAN FD signal integrity analysis
  CAN FD data phase at 2 Mbit/s is very sensitive to:
  - Cable length (max ~4m for 2 Mbit/s)
  - Stub lengths (no stubs allowed in data phase)
  - Termination mismatch
  
STEP 4: Measure termination
  Expected: 120Ω at each end
  Measured: 120Ω at node 1, 56Ω at node 2 ← WRONG!
  
ROOT CAUSE: Incorrect termination resistor (56Ω instead of 120Ω)
            at one end. Combined with 6m cable → signal reflections
            → CRC errors in data phase.
FIX: Replace 56Ω terminator with 120Ω. Reduce cable length to < 4m for 2Mbit/s.
     Or reduce data phase to 1 Mbit/s (allows longer cables).
```

---

## 5.5 BUS STATISTICS AND TIMING ANALYSIS

### 5.5.1 Bus Load Measurement

```
MEASURING BUS LOAD IN CANalyzer:
──────────────────────────────────────────────────────────────
1. Statistics window → Bus Load section:
   Current bus load:    35.7%
   Peak bus load:       68.2% ← spike during CAN FD burst
   Average bus load:    38.1%
   
2. High bus load troubleshooting:
   > 70% bus load → risk of message loss, timeouts
   
   Identify heavy senders:
   Sort message statistics by bit rate:
   BMS_CellData_ALL  → 64 bytes × 25Hz = 12,800 bytes/s (most)
   INV_Status        → 8 bytes × 200Hz = 1,600 bytes/s
   VCU_TorqueRequest → 8 bytes × 200Hz = 1,600 bytes/s
   
   Solution: Reduce BMS_CellData_ALL to 10Hz (only needed 10Hz)
   → Bus load drops from 68% to 42% ✓
```

### 5.5.2 Timing Jitter Analysis

```
TIMING JITTER ANALYSIS:
──────────────────────────────────────────────────────────────
Normal timing: BMS_Status should be 10ms ± 1ms

Analysis: Export timestamp data to CSV:
  File → Export → Timestamp of message 0x310

Python analysis:
  import pandas as pd
  import numpy as np
  
  df = pd.read_csv('bms_timestamps.csv')
  periods = df['Timestamp'].diff().dropna() * 1000  # convert to ms
  
  print(f"Mean period: {periods.mean():.3f} ms")
  print(f"Std deviation: {periods.std():.3f} ms")
  print(f"Max period: {periods.max():.3f} ms")
  print(f"Min period: {periods.min():.3f} ms")
  print(f"Jitter > 2ms: {(abs(periods - 10) > 2).sum()} occurrences")

Result:
  Mean period: 10.012 ms ✓
  Std deviation: 0.287 ms ✓
  Max period: 85.3 ms ← FAIL (> 11ms threshold)
  Min period: 9.1 ms ✓
  Jitter > 2ms: 3 occurrences in 10000 messages
```

---

## SECTION 5 SUMMARY

CANalyzer is the essential tool for automotive network analysis. Master these skills:

| Skill | Application |
|-------|-------------|
| Trace window analysis | Find missing messages, wrong signals, error frames |
| Signal monitoring | Live signal values with alarms |
| Bus statistics | Bus load, message timing, error counts |
| Log analysis | Investigate field issues, reproduce bugs |
| Error frame debugging | Identify hardware/transceiver issues |
| Timing analysis | Verify cyclic rates, detect jitter |

**The 6 most common CAN issues an engineer will debug:**
1. Missing message → ECU sleep, no power, BusOff
2. Wrong signal value → Wrong DBC version, byte order error
3. Timeout → Jitter, OS task conflict, bus overload
4. No UDS response → Wrong address, condition blocked, BusOff
5. Bus Off → Hardware glitch, excessive errors, transceiver failure
6. CAN FD corruption → Impedance, termination, cable length issues

---

*Next: Section 6 — CAPL Programming Complete Training*
