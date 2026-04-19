# CAPL Live Coding Interview Guide
## Hands-On Tasks Commonly Asked in Automotive Testing Interviews

---

## Overview

Many automotive testing interviews include a **live CAPL coding challenge** in CANoe or on a whiteboard. This guide covers the most frequently asked tasks, patterns, and tips.

---

## 1. Task Types Asked in Interviews

| Category | Example Task |
|---|---|
| Message sending | Send a CAN message periodically at 10 Hz |
| Message receiving | Detect timeout when message stops arriving |
| Signal validation | Check signal is within defined range |
| State machine | Implement ignition key state transitions |
| Timer usage | Debounce an input signal over 200 ms |
| Error detection | Detect missing heartbeat message |
| UDS sequence | Send 0x10 03 and check positive response |
| Bitwise ops | Extract RPM from two bytes with factor/offset |

---

## 2. Task 1 – Send CAN Message at 10 Hz

**Question**: "Write a CAPL script that sends message 0x100 with 8 bytes every 100 ms."

```capl
variables
{
  msTimer sendTimer;
  message 0x100 txMsg;
  byte gCounter = 0;
}

on start
{
  txMsg.dlc = 8;
  setTimer(sendTimer, 100);
}

on timer sendTimer
{
  txMsg.byte(0) = gCounter++;
  txMsg.byte(1) = 0xAB;
  txMsg.byte(2) = 0xCD;
  txMsg.byte(3) = 0xEF;
  txMsg.byte(4) = 0x00;
  txMsg.byte(5) = 0x00;
  txMsg.byte(6) = 0x00;
  txMsg.byte(7) = 0x00;
  output(txMsg);
  setTimer(sendTimer, 100);
}
```

**Key points to mention:**
- `msTimer` for millisecond timers
- Always restart the timer at end of handler
- `output()` actually transmits the message
- Incrementing counter byte to verify sequence

---

## 3. Task 2 – Message Timeout Detection

**Question**: "Detect if message 0x200 stops arriving for more than 500 ms. Log an error if so."

```capl
variables
{
  msTimer timeoutTimer;
  int gTimeoutOccurred = 0;
}

on start
{
  write("Monitoring 0x200 with 500ms timeout...");
  setTimer(timeoutTimer, 500);
}

on message 0x200
{
  // Message received – reset watchdog timer
  cancelTimer(timeoutTimer);
  gTimeoutOccurred = 0;
  setTimer(timeoutTimer, 500);
}

on timer timeoutTimer
{
  gTimeoutOccurred = 1;
  write("!! ERROR: Message 0x200 not received for 500 ms!");
  // In a real test: testStepFail("Timeout on 0x200");
}
```

**Key points:**
- Pattern: reset timer on each receive, fire on timeout
- `cancelTimer` prevents false triggers
- Foundation for all network monitoring tests

---

## 4. Task 3 – Extract Signal from Raw Bytes

**Question**: "Message 0x100 has engine RPM in bytes 0-1, Intel byte order, factor 0.25, offset 0. Print the RPM."

```capl
on message 0x100
{
  word rawRPM;
  float rpm;

  // Intel (little-endian): byte 0 = low byte, byte 1 = high byte
  rawRPM = this.byte(0) | (this.byte(1) << 8);

  // Apply factor and offset
  rpm = rawRPM * 0.25;

  write("Engine RPM: %.2f (raw=0x%04X)", rpm, rawRPM);

  // Validation
  if (rpm < 0 || rpm > 8000)
    write("!! RPM out of range: %.2f", rpm);
}
```

**For Motorola (big-endian):**
```capl
rawRPM = (this.byte(0) << 8) | this.byte(1);
```

---

## 5. Task 4 – Simple State Machine

**Question**: "Implement a state machine for ignition: OFF → ACC → ON → START → ON → OFF."

```capl
variables
{
  int gIgnState = 0;
  // 0=OFF, 1=ACC, 2=ON, 3=START
}

on key 'n'  // next state
{
  transitionIgnition();
}

on key 'o'  // back to OFF
{
  gIgnState = 0;
  write("Ignition: OFF");
}

void transitionIgnition()
{
  switch(gIgnState)
  {
    case 0:
      gIgnState = 1;
      write("Ignition: OFF -> ACC");
      break;
    case 1:
      gIgnState = 2;
      write("Ignition: ACC -> ON");
      break;
    case 2:
      gIgnState = 3;
      write("Ignition: ON -> START");
      // Simulate crank for 500ms
      setTimer(crankTimer, 500);
      break;
    case 3:
      gIgnState = 2;
      write("Ignition: START -> ON (engine running)");
      break;
  }
}

on timer crankTimer
{
  gIgnState = 2;
  write("Engine started. State: ON");
}
```

---

## 6. Task 5 – UDS Request/Response

**Question**: "Send UDS DiagnosticSessionControl (0x10 0x03) to ECU address 0x7E0 and verify positive response."

```capl
variables
{
  message 0x7E0 udsReq;
  msTimer responseTimer;
  int gWaitingForResponse = 0;
}

on start
{
  sendDiagSession(0x03);
}

void sendDiagSession(byte sessionType)
{
  udsReq.dlc = 8;
  udsReq.byte(0) = 0x02;        // length
  udsReq.byte(1) = 0x10;        // SID
  udsReq.byte(2) = sessionType; // subFunction
  udsReq.byte(3) = 0xCC;
  udsReq.byte(4) = 0xCC;
  udsReq.byte(5) = 0xCC;
  udsReq.byte(6) = 0xCC;
  udsReq.byte(7) = 0xCC;

  output(udsReq);
  gWaitingForResponse = 1;
  setTimer(responseTimer, 1000);
  write(">> DiagSession(0x%02X) sent", sessionType);
}

on message 0x7E8  // ECU response ID
{
  if (!gWaitingForResponse) return;

  cancelTimer(responseTimer);
  gWaitingForResponse = 0;

  byte sid = this.byte(1);

  if (sid == 0x50)
    write("<< PASS: Positive response 0x50 received");
  else if (sid == 0x7F)
    write("<< FAIL: Negative response, NRC=0x%02X", this.byte(3));
  else
    write("<< Unexpected SID: 0x%02X", sid);
}

on timer responseTimer
{
  gWaitingForResponse = 0;
  write("!! FAIL: No response within 1000ms");
}
```

---

## 7. Task 6 – Bus Load Calculation

**Question**: "Describe how to measure CAN bus load in CANoe."

```capl
variables
{
  msTimer busLoadTimer;
  long gMsgCount = 0;
  long gByteCount = 0;
  float gBusLoadPercent = 0.0;

  // CAN 500 kbps: approximate max frames/sec
  // A standard CAN frame with 8 bytes ≈ 130 bits
  // 500,000 bits/s / 130 bits = ~3846 frames/s
  const float MAX_FRAMES_PER_SEC = 3846.0;
}

on message *
{
  gMsgCount++;
  gByteCount += this.dlc;
}

on timer busLoadTimer
{
  // Approximate: frames per second vs theoretical max
  float framesPerSec = gMsgCount / 1.0; // per second

  gBusLoadPercent = (framesPerSec / MAX_FRAMES_PER_SEC) * 100.0;

  write("Bus Load: %.1f%% (%ld frames in last second)",
        gBusLoadPercent, gMsgCount);

  if (gBusLoadPercent > 70.0)
    write("!! WARNING: High bus load %.1f%%", gBusLoadPercent);

  gMsgCount = 0;
  gByteCount = 0;
  setTimer(busLoadTimer, 1000);
}

on start
{
  setTimer(busLoadTimer, 1000);
}
```

---

## 8. Task 7 – Count Specific Message Reception

**Question**: "Count how many times message 0x300 is received in 10 seconds and report."

```capl
variables
{
  msTimer measureTimer;
  int gMsgCount = 0;
}

on start
{
  gMsgCount = 0;
  setTimer(measureTimer, 10000);
  write("Counting 0x300 for 10 seconds...");
}

on message 0x300
{
  gMsgCount++;
}

on timer measureTimer
{
  write("Message 0x300 received %d times in 10 seconds", gMsgCount);
  write("Average cycle time: %.1f ms",
        gMsgCount > 0 ? 10000.0 / gMsgCount : 0.0);

  // For a 100ms cycle message, expect ~100 messages
  if (gMsgCount >= 95 && gMsgCount <= 105)
    write("PASS: Cycle time within spec (100ms ±5%)");
  else
    write("FAIL: Cycle time deviation (expected ~100, got %d)", gMsgCount);
}
```

---

## 9. Interview Tips for CAPL Live Coding

1. **Always declare variables first** in the `variables {}` block
2. **Restart timers explicitly** – CAPL timers do NOT auto-repeat
3. **Use `cancelTimer` before `setTimer`** to avoid double-firing
4. **Explain your logic** as you write – interviewers assess communication
5. **Address edge cases**: negative values, missing messages, out-of-range signals
6. **Use meaningful variable names**: `gEngineRPM` not `x`
7. **Test message direction**: distinguish TX vs. RX with `this.dir`
8. **Use `write()` for debugging** – show you think about observability
9. **Know `on message *`** for monitoring all messages
10. **Know the difference**: `output()` sends, `on message` receives

---

## 10. Common 5-Minute Whiteboard Tasks

| Task | Core Concept |
|---|---|
| Detect message 0x123 not received for 200ms | Timer + cancel on receive |
| Send 5 messages then stop | Counter in timer handler |
| Toggle a byte between 0x00 and 0xFF every second | XOR trick: `val ^= 0xFF` |
| Log all messages above ID 0x400 | `on message *` with ID check |
| Simulate key press to trigger test | `on key 'x'` handler |
| Validate signal is within [min, max] range | `if` condition + `write()` |
