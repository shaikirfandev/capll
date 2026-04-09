# CAPL Events and Event Handlers - Complete Guide

## Table of Contents
1. [Introduction to Events](#introduction-to-events)
2. [Event-Driven Architecture](#event-driven-architecture)
3. [System Events](#system-events)
4. [Message Events](#message-events)
5. [Timer Events](#timer-events)
6. [Keyboard Events](#keyboard-events)
7. [Environment Variable Events](#environment-variable-events)
8. [Control Events](#control-events)
9. [Advanced Event Patterns](#advanced-event-patterns)
10. [Event Best Practices](#event-best-practices)

---

## Introduction to Events

### What is an Event?

An **event** is something that happens in your CAPL script or the CANoe system that triggers code execution. Instead of writing a continuous loop, CAPL programs are **event-driven** - they respond when specific things occur.

### Event-Driven vs. Traditional Programming

**Traditional Loop:**
```c
while (true) {
  // Check for things continuously
  if (message_received) process_message();
  if (timer_expired) handle_timer();
  // etc.
}
```

**Event-Driven (CAPL):**
```capl
on message MessageID {
  // This runs only when MessageID is received
}

on timer MyTimer {
  // This runs only when MyTimer expires
}
// Rest of code runs when events occur
```

### Benefits of Event-Driven Architecture

- **Efficient** - CPU only works when something happens
- **Responsive** - Immediate reaction to events
- **Clean** - Separates different concerns
- **Scalable** - Easy to add new event handlers

---

## Event-Driven Architecture

### The Event Loop

CANoe manages an internal event loop:

```
Event Queue → Event Dispatcher → Event Handler → Continue
    ↑                                              ↓
    └──────────────────────────────────────────────┘
```

1. **Events occur** (message received, timer expires, key pressed)
2. **Events are queued** in order
3. **Event dispatcher** processes each event
4. **Event handler** (your code) executes
5. **Loop continues** to next event

### Event Execution Order

Events are processed in the order they occur:

```capl
on start {
  Write("Event 1: Script starts");
}

on message 0x100 {
  Write("Event 2: Message received");
}

on timer MyTimer {
  Write("Event 3: Timer expires");
}

// Events execute in order as they happen, not top-to-bottom
```

---

## System Events

### on start - Script Initialization

**Triggers:** When the measurement/simulation starts

**Typical Use:** Initialize variables, start timers, load resources

```capl
on start {
  Write("========== Script Started ==========");
  
  // Initialize global variables
  gMessageCount = 0;
  gErrorCount = 0;
  gStartTime = GetTime();
  
  // Start timers
  SetTimer(gMonitorTimer, 1000);
  
  // Log initialization
  Write("Initialization complete at %dms", GetTime());
}
```

**Key Points:**
- Executes exactly **once** at measurement start
- Guaranteed to run before any other events
- Good place for setup operations
- All global variables initialized to 0 before on start

### on stop - Script Cleanup

**Triggers:** When the measurement/simulation stops

**Typical Use:** Cleanup, logging final statistics, cancel timers

```capl
on stop {
  Write("========== Script Stopped ==========");
  
  // Cancel running timers
  CancelTimer(gMonitorTimer);
  CancelTimer(gHeartbeatTimer);
  
  // Log final statistics
  Write("Final Statistics:");
  Write("  Total messages: %d", gMessageCount);
  Write("  Total errors: %d", gErrorCount);
  Write("  Runtime: %dms", GetTime() - gStartTime);
  
  // Cleanup
  gIsActive = 0;
}
```

**Key Points:**
- Executes exactly **once** at measurement stop
- Last chance to save data
- All timers should be canceled
- Good place for final logging

### on preStart - Pre-Initialization (Advanced)

**Triggers:** Before measurement starts (if present)

```capl
on preStart {
  Write("Preparing to start...");
  // Prepare resources before measurement begins
}
```

---

## Message Events

### on message * - Catch All Messages

**Triggers:** Every message on the bus

**Typical Use:** Monitor all traffic, collect statistics

```capl
on message * {
  // 'this' represents the current message
  Write("Message ID: 0x%03X, DLC: %d", this.ID, this.DLC);
  gTotalMessageCount++;
}
```

**Message Object Properties:**
```capl
on message * {
  int id = this.ID;              // Message ID (CAN identifier)
  int dlc = this.DLC;            // Data Length Code (0-8)
  dword timestamp = this.Time;   // Timestamp in milliseconds
  byte data[8];
  
  // Copy data
  for (int i = 0; i < dlc; i++) {
    data[i] = this.Data[i];
  }
}
```

### on message ID - Specific Message Handler

**Triggers:** Only when message with specific ID arrives

**Typical Use:** Process specific CAN message

```capl
on message 0x100 {
  Write("Engine status message received");
  int rpm = (this.Data[0] << 8) | this.Data[1];
  Write("  RPM: %d", rpm);
}

on message 0x200 {
  Write("Transmission status message received");
  int torque = this.Data[0];
  Write("  Torque: %d", torque);
}

on message 0x300 {
  Write("Chassis status message received");
  int speed = (this.Data[0] << 8) | this.Data[1];
  Write("  Speed: %d", speed);
}
```

**Key Points:**
- More efficient than filtering in `on message *`
- Use **hexadecimal** for message IDs: `0x123`
- `this` variable contains the message object
- Executes immediately when message arrives

### on message error - Error Frames

**Triggers:** When a CAN error frame is detected

**Typical Use:** Error handling, diagnostics

```capl
on message error {
  Write("!!! CAN Error Frame Detected !!!");
  gErrorCount++;
  
  // Take action - maybe stop measurement
  if (gErrorCount > 10) {
    Write("Too many errors, stopping...");
    // Stop measurement
  }
}
```

### Multiple Message Handlers

You can have both generic and specific handlers:

```capl
on message * {
  // This runs for EVERY message
  gAllMessageCount++;
}

on message 0x100 {
  // This ALSO runs when message 0x100 arrives
  // (in addition to the on message * handler)
  gEngine0x100Count++;
}
```

**Execution Order:** `on message *` runs first, then `on message 0x100`

---

## Timer Events

### Timer Declaration

```capl
// Declare timers at global scope
timer gRecurringTimer;
timer gOneTimeTimer;
timer gMonitorTimer;
```

### Starting Timers

```capl
on start {
  // Recurring timer (fires repeatedly every 1000ms)
  SetTimer(gRecurringTimer, 1000);
  
  // One-time timer (fires once after 5000ms)
  SetTimer(gOneTimeTimer, 5000);
}
```

### Timer Event Handler

```capl
on timer gRecurringTimer {
  Write("Timer fired at %dms", GetTime());
  gTimerCount++;
}

on timer gOneTimeTimer {
  Write("One-time timer fired!");
  // This executes once, then timer is done
}
```

**Key Points:**
- Timer fires at specified interval (in milliseconds)
- `on timer` handler called each time timer expires
- Recurring timer continues until `CancelTimer()` is called
- One-time timers automatically stop after firing once

### Timer Control

```capl
// Start a timer
SetTimer(gMyTimer, 2000);  // Fire every 2 seconds

// Stop a timer
CancelTimer(gMyTimer);

// Restart a timer (cancels and restarts)
CancelTimer(gMyTimer);
SetTimer(gMyTimer, 2000);

// Get current time
dword now = GetTime();

// Wait (pause execution)
Wait(1000);  // Pause for 1000ms
```

### Practical Timer Pattern

```capl
timer gStatusTimer;
int gStatusInterval = 1000;  // milliseconds

on start {
  SetTimer(gStatusTimer, gStatusInterval);
}

on timer gStatusTimer {
  // Do periodic work here
  PrintSystemStatus();
  
  // Can dynamically change interval
  if (someCondition) {
    CancelTimer(gStatusTimer);
    SetTimer(gStatusTimer, 500);  // Speed up monitoring
  }
}

void PrintSystemStatus() {
  Write("Status check at %d", GetTime());
}
```

---

## Keyboard Events

### on key - Single Key Press

**Triggers:** When a specific key is pressed

**Typical Use:** User interaction, testing, debugging

```capl
on key 'A' {
  Write("Key 'A' pressed");
}

on key 'S' {
  Write("Key 'S' pressed");
}

on key ' ' {
  Write("Spacebar pressed");
}
```

### Common Keys

```capl
on key 'M' {
  // Regular letter
}

on key '0' {
  // Number key
}

on key ' ' {
  // Spacebar
}

on key 'F1' {
  // Function keys: F1-F12
}

on key 'Enter' {
  // Special keys
}

on key 'Escape' {
  // Escape key
}
```

### Key Combinations

Some systems support modifiers:

```capl
on key 'Ctrl+A' {
  Write("Ctrl+A pressed");
}

on key 'Shift+S' {
  Write("Shift+S pressed");
}
```

### Interactive Script Pattern

```capl
on key 'H' {
  DisplayHelp();
}

on key 'S' {
  DisplayStats();
}

on key 'R' {
  ResetCounters();
}

void DisplayHelp() {
  Write("");
  Write("========== Help ==========");
  Write("H - Show help");
  Write("S - Show statistics");
  Write("R - Reset counters");
  Write("");
}

void DisplayStats() {
  Write("");
  Write("========== Statistics ==========");
  Write("Messages: %d", gMessageCount);
  Write("Errors: %d", gErrorCount);
  Write("");
}

void ResetCounters() {
  gMessageCount = 0;
  gErrorCount = 0;
  Write("Counters reset");
}
```

---

## Environment Variable Events

### on SimVar - Simulation Variable Change

**Triggers:** When an environment variable (SimVar) changes

**Typical Use:** React to external simulation changes

```capl
on SimVar gEngineSpeed {
  Write("Engine speed changed to: %d", gEngineSpeed);
}

on SimVar gTemperature {
  Write("Temperature changed to: %.1f", gTemperature);
}
```

**Key Points:**
- SimVar must be declared in environment
- Runs whenever variable changes
- Can be used to synchronize with CANoe simulation
- Powerful for integration with CANoe's measurement setup

### Using Environment Variables

```capl
on start {
  // Get initial environment variable value
  int value = GetEnvVarInt("SimulationSpeed");
  float temp = GetEnvVarFloat("Temperature");
}

void SetEnvironmentVariable() {
  // Modify environment variables
  SetEnvVarInt("Status", 1);
  SetEnvVarFloat("OutputValue", 3.14);
}
```

---

## Control Events

### on busType - Bus Type Detection

**Triggers:** At startup to detect bus type

```capl
on busType {
  Write("Bus type detected");
  // Bus-specific initialization
}
```

### on busState - Bus State Change

**Triggers:** When bus state changes (rarely used)

```capl
on busState {
  Write("Bus state changed");
}
```

---

## Advanced Event Patterns

### Nested Event Handlers

One event handler can trigger actions that cause other event handlers to run:

```capl
on message 0x100 {
  // Process incoming message
  ProcessEngineData();
  
  // This might trigger other handlers indirectly
}

void ProcessEngineData() {
  // This function runs in context of on message 0x100
  // If it sends a message, on message * also runs
  Message response;
  response.ID = 0x200;
  response.DLC = 2;
  response.Data[0] = 0x01;
  response.Data[1] = 0x02;
  Send(response);
  
  // Now on message * handler also executes for this message!
}

on message * {
  // This also runs for the message sent above
  gAllMessagesCount++;
}
```

### Event Handler Execution Flow

```
on message 0x100 {
  ProcessEngineData();  // ← Function call
}

void ProcessEngineData() {
  Send(msg);  // ← Sends message
}

on message * {
  // ← This handler also runs!
  gCount++;
}
```

### Conditional Event Handling

```capl
on message 0x100 {
  // Only process if we're in active state
  if (!gIsActive) {
    return;
  }
  
  ProcessData();
}

on timer gMonitor {
  // Only monitor if enabled
  if (!gMonitoringEnabled) {
    return;
  }
  
  CheckStatus();
}

on key 'S' {
  // Only accept input in certain states
  if (gCurrentState != STATE_IDLE) {
    Write("Command not allowed in current state");
    return;
  }
  
  SendMessage();
}
```

### Event Filtering

```capl
on message * {
  // Only process CAN IDs in range 0x100-0x200
  if (this.ID < 0x100 || this.ID > 0x200) {
    return;
  }
  
  ProcessMessage();
}

on message * {
  // Only process messages with DLC == 8
  if (this.DLC != 8) {
    return;
  }
  
  ProcessStandardMessage();
}
```

### Sequential Event Handling

```capl
// Event 1: Message triggers action
on message 0x100 {
  gEventTriggered = 1;
  SetTimer(gProcessTimer, 100);
}

// Event 2: Timer processes the result
on timer gProcessTimer {
  if (gEventTriggered) {
    ProcessResult();
    gEventTriggered = 0;
  }
}
```

---

## Event Best Practices

### 1. Keep Event Handlers Short

```capl
// GOOD: Event handler is simple
on message 0x100 {
  ProcessEngineMessage();
}

void ProcessEngineMessage() {
  // Complex logic here in separate function
  int rpm = (this.Data[0] << 8) | this.Data[1];
  ValidateRPM(rpm);
  UpdateDashboard(rpm);
}

// AVOID: Complex logic directly in handler
on message 0x100 {
  int rpm = (this.Data[0] << 8) | this.Data[1];
  if (rpm > 0 && rpm < 10000) {
    // ... lots of logic directly here
  }
}
```

### 2. Organize Events Logically

```capl
// === System Events ===
on start { /* ... */ }
on stop { /* ... */ }

// === Message Events ===
on message 0x100 { /* ... */ }
on message 0x200 { /* ... */ }

// === Timer Events ===
on timer gMonitor { /* ... */ }
on timer gUpdate { /* ... */ }

// === User Input ===
on key 'S' { /* ... */ }
on key 'H' { /* ... */ }

// === Helper Functions ===
void ProcessEngine() { /* ... */ }
void DisplayStats() { /* ... */ }
```

### 3. Validate Data in Event Handlers

```capl
on message 0x100 {
  // Validate before processing
  if (this.DLC < 4) {
    Write("Error: Invalid message length");
    return;
  }
  
  int value = (this.Data[0] << 8) | this.Data[1];
  
  if (value < 0 || value > 5000) {
    Write("Error: Value out of range: %d", value);
    return;
  }
  
  ProcessValue(value);
}
```

### 4. Avoid Long Operations in Event Handlers

```capl
// AVOID: Long loop in event handler
on message 0x100 {
  for (int i = 0; i < 1000000; i++) {
    // Long computation - blocks other events!
    result += ComplexCalculation(i);
  }
}

// GOOD: Schedule work for timer
on message 0x100 {
  gWorkNeeded = 1;
  SetTimer(gWorkTimer, 10);  // Do work after short delay
}

on timer gWorkTimer {
  DoWork();
  gWorkNeeded = 0;
}
```

### 5. Use Descriptive Naming

```capl
// GOOD
timer gEngineMonitorTimer;
int gEngineRPMValue;
void ProcessEngineData() { }

on message 0x100 {  // Engine status
  ProcessEngineData();
}

// AVOID
timer t1;
int val;
void Process() { }

on message 0x100 {
  Process();
}
```

### 6. Document Event Handlers

```capl
/**
 * on message 0x100 - Engine Status
 * 
 * Triggered when engine status message is received
 * Extracts RPM, temperature, and pressure
 * Updates dashboard and checks for warnings
 */
on message 0x100 {
  // Extract engine data
  int rpm = (this.Data[0] << 8) | this.Data[1];
  int temp = this.Data[2];
  int pressure = this.Data[3];
  
  // Process data
  ProcessEngineParameters(rpm, temp, pressure);
}
```

### 7. Handle Errors Gracefully

```capl
on message 0x100 {
  // Check message validity
  if (gMessageCount++ > MAX_SAFE_COUNT) {
    Write("Warning: Message rate too high");
    gMessageCount = 0;  // Reset counter
    return;
  }
  
  // Try to process
  int result = ProcessMessage();
  
  if (result < 0) {
    Write("Error processing message");
    gErrorCount++;
    
    // Take recovery action
    if (gErrorCount > MAX_ERRORS) {
      Write("Too many errors - stopping");
      CancelTimer(gMonitorTimer);
    }
  }
}
```

### 8. Testing Event Handlers

```capl
#define TEST_MODE 1

on key 'T' {
  #if TEST_MODE
  RunTests();
  #endif
}

void RunTests() {
  Write("========== Running Tests ==========");
  TestMessageProcessing();
  TestTimerHandling();
  TestDataValidation();
  Write("========== Tests Complete ==========");
}
```

---

## Event Handler Complete Example

```capl
// Global declarations
timer gMonitorTimer;
int gMessageCount = 0;
int gErrorCount = 0;
int gIsActive = 0;

// === SYSTEM EVENTS ===

on start {
  Write("========== Script Started ==========");
  gMessageCount = 0;
  gErrorCount = 0;
  gIsActive = 1;
  SetTimer(gMonitorTimer, 1000);
}

on stop {
  Write("========== Script Stopped ==========");
  CancelTimer(gMonitorTimer);
  Write("Final: %d messages, %d errors", gMessageCount, gErrorCount);
}

// === MESSAGE EVENTS ===

on message * {
  if (gIsActive) {
    gMessageCount++;
  }
}

on message 0x100 {
  Write("[0x100] Engine status");
}

on message error {
  gErrorCount++;
  Write("! CAN Error #%d", gErrorCount);
}

// === TIMER EVENTS ===

on timer gMonitorTimer {
  Write("Monitor: %d messages, %d errors", gMessageCount, gErrorCount);
}

// === KEYBOARD EVENTS ===

on key 'S' {
  Write("Stats: Messages=%d, Errors=%d", gMessageCount, gErrorCount);
}

on key 'R' {
  gMessageCount = 0;
  gErrorCount = 0;
  Write("Counters reset");
}

on key 'H' {
  Write("Help: Press S=stats, R=reset, Q=quit");
}
```

---

## Summary

CAPL's event-driven architecture means:

1. **No busy loops** - Code runs when events occur
2. **Responsive** - Immediate reaction to changes
3. **Organized** - Different handlers for different concerns
4. **Efficient** - CPU only works when needed

Master event handling and you'll write efficient, responsive CAPL scripts!
