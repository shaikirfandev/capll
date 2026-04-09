# CAPL Real Work Interview Scenarios
## Practical Interview Questions with Code Challenges

---

## 🎨 Color Coding Guide

All code blocks use **C syntax highlighting** for better readability:
- 🟦 **Blue**: Keywords (`int`, `for`, `if`, `while`, `return`, `on`, `message`)
- 🟥 **Red**: Strings and comments
- 🟩 **Green**: Built-in functions (`Write()`, `Send()`, `GetTime()`, `SetTimer()`)
- 🟨 **Yellow**: Numbers and constants (`0x100`, `1000`, `TRUE`)
- ⚪ **White**: Variables and user-defined functions

**Difficulty Indicators:**
| Badge | Color | Difficulty | Est. Time |
|-------|-------|-----------|-----------|
| 🔵 | Blue | Beginner (⭐⭐) | 15-20 min |
| 🟡 | Yellow | Intermediate (⭐⭐⭐) | 20-25 min |
| 🟢 | Green | Advanced (⭐⭐⭐⭐) | 25-30 min |
| 🔴 | Red | Expert (⭐⭐⭐⭐⭐) | 30-45 min |

---

## 🔵 **Interview Scenario 1: Message Reception & Data Extraction**

**Difficulty:** ⭐⭐ (Beginner) | **Category:** CAN Message Handling | **Time:** 15-20 min

**Real-World Context:**
You're developing a CAPL script for an automotive test harness. Your test stand receives engine status messages (ID: 0x100) with 8 bytes:
- **Byte 0-1**: Engine RPM (16-bit, Big-endian, range 0-8000)
- **Byte 2**: Engine Temperature (range -40°C to +125°C, stored as offset value)
- **Byte 3**: Throttle Position (0-100%, stored as 0-255)
- **Byte 7**: Checksum (simple sum of bytes 0-6, two's complement)

**Requirements:**
1. Receive message 0x100
2. Extract all 4 values with correct byte ordering and scaling
3. Validate the checksum
4. Log results if valid, error message if invalid
5. Maintain running counter of valid/invalid messages

**Your Code:**
```capl
// Global counters
int gValidMessages = 0;
int gInvalidMessages = 0;

// Constants
#define ENGINE_MSG_ID 0x100
#define ENGINE_MSG_DLC 8
#define TEMP_OFFSET (-40)

// Extract RPM from bytes 0-1 (Big-endian)
int ExtractRPM(byte data[]) {
  return (data[0] << 8) | data[1];
}

// Extract Temperature (offset -40°C)
int ExtractTemperature(byte value) {
  return (int)value + TEMP_OFFSET;
}

// Extract Throttle Position (0-100%)
int ExtractThrottle(byte value) {
  return (value * 100) / 255;  // Convert 0-255 to 0-100%
}

// Calculate checksum (sum of bytes 0-6, two's complement)
byte CalculateChecksum(byte data[], int dlc) {
  byte sum = 0;
  for (int i = 0; i < dlc - 1; i++) {  // All bytes except last (checksum byte)
    sum += data[i];
  }
  return (~sum) + 1;  // Two's complement
}

// Validate message checksum
int ValidateChecksum(byte data[], int dlc) {
  if (dlc < 8) {
    Write("Error: Invalid DLC %d (expected 8)", dlc);
    return 0;
  }
  
  byte calculated = CalculateChecksum(data, dlc);
  byte received = data[dlc - 1];
  
  if (calculated != received) {
    Write("Error: Checksum mismatch. Calculated: 0x%02X, Received: 0x%02X", 
          calculated, received);
    return 0;
  }
  return 1;
}

// Main message handler
on message ENGINE_MSG_ID {
  // Validate DLC first
  if (this.DLC != ENGINE_MSG_DLC) {
    Write("Error: Message 0x100 invalid DLC: %d (expected 8)", this.DLC);
    gInvalidMessages++;
    return;
  }
  
  // Copy message data
  byte msgData[8];
  for (int i = 0; i < 8; i++) {
    msgData[i] = this.Data[i];
  }
  
  // Validate checksum
  if (!ValidateChecksum(msgData, 8)) {
    gInvalidMessages++;
    return;
  }
  
  // Checksum valid - extract all values
  int rpm = ExtractRPM(msgData);
  int temp = ExtractTemperature(msgData[2]);
  int throttle = ExtractThrottle(msgData[3]);
  
  // Validate extracted values are in valid range
  if (rpm < 0 || rpm > 8000) {
    Write("Error: RPM out of range: %d", rpm);
    gInvalidMessages++;
    return;
  }
  
  if (temp < -40 || temp > 125) {
    Write("Error: Temperature out of range: %d°C", temp);
    gInvalidMessages++;
    return;
  }
  
  if (throttle < 0 || throttle > 100) {
    Write("Error: Throttle out of range: %d%%", throttle);
    gInvalidMessages++;
    return;
  }
  
  // All validations passed - log results
  gValidMessages++;
  Write("Valid Message [%d] - RPM: %d, Temp: %d°C, Throttle: %d%%", 
        gValidMessages, rpm, temp, throttle);
}

// Display statistics on demand
on key 'S' {
  Write("===== Engine Message Statistics =====");
  Write("Valid messages: %d", gValidMessages);
  Write("Invalid messages: %d", gInvalidMessages);
  if ((gValidMessages + gInvalidMessages) > 0) {
    int total = gValidMessages + gInvalidMessages;
    int percentage = (gValidMessages * 100) / total;
    Write("Success rate: %d%%", percentage);
  }
  Write("====================================");
}
```

**Evaluation Criteria:**
- ✅ Correct data extraction (byte ordering, scaling, offset handling)
- ✅ Proper checksum validation
- ✅ Error handling for invalid DLC
- ✅ Meaningful variable names
- ✅ Code comments explaining logic
- ✅ Use of helper functions

**Common Mistakes to Avoid:**
- Wrong byte order (Little-endian instead of Big-endian)
- Incorrect offset handling for temperature
- Not validating message length before accessing bytes
- Not handling checksum correctly

---

## 🟢 **Interview Scenario 2: Message Transmission with Validation**

**Difficulty:** ⭐⭐⭐ (Intermediate) | **Category:** Send & Validate | **Time:** 20-25 min

**Real-World Context:**
You need to send control commands to a vehicle module (ID: 0x200). The message transmission must:
- Pack 4 bytes of data into message payload
- Calculate checksum before sending
- Validate parameters before transmission
- Track transmission success/failure
- Implement retry logic on failure

Message format:
- **Byte 0**: Command Type (1-10)
- **Byte 1-2**: Parameter Value (16-bit signed, Big-endian)
- **Byte 3**: Priority (0-7)
- **Byte 4-6**: Reserved (0x00)
- **Byte 7**: Checksum

**Requirements:**
1. Create function `SendCommand(int cmdType, int paramValue, int priority)`
2. Validate all parameters are in range
3. Calculate and attach checksum
4. Send message on CAN bus
5. Implement retry if first transmission fails
6. Log all transmissions (success/failure)

**Your Code:**
```capl
// Constants
#define CONTROL_MSG_ID 0x200
#define CONTROL_MSG_DLC 8
#define MAX_RETRIES 3
#define RETRY_DELAY 100  // ms
#define MIN_CMD_TYPE 1
#define MAX_CMD_TYPE 10
#define MIN_PRIORITY 0
#define MAX_PRIORITY 7

// Global counters
int gSentCommands = 0;
int gFailedCommands = 0;
int gRetryCount = 0;

// Calculate checksum for control message
byte CalculateControlChecksum(byte data[]) {
  byte sum = 0;
  for (int i = 0; i < 7; i++) {  // Bytes 0-6
    sum += data[i];
  }
  return (~sum) + 1;  // Two's complement
}

// Validate command parameters
int ValidateParameters(int cmdType, int paramValue, int priority) {
  if (cmdType < MIN_CMD_TYPE || cmdType > MAX_CMD_TYPE) {
    Write("Error: Invalid command type %d (range %d-%d)", 
          cmdType, MIN_CMD_TYPE, MAX_CMD_TYPE);
    return 0;
  }
  
  if (paramValue < -32768 || paramValue > 32767) {
    Write("Error: Parameter value out of 16-bit range: %d", paramValue);
    return 0;
  }
  
  if (priority < MIN_PRIORITY || priority > MAX_PRIORITY) {
    Write("Error: Invalid priority %d (range %d-%d)", 
          priority, MIN_PRIORITY, MAX_PRIORITY);
    return 0;
  }
  
  return 1;  // Valid
}

// Send command with retry logic
int SendCommand(int cmdType, int paramValue, int priority) {
  // Validate parameters first
  if (!ValidateParameters(cmdType, paramValue, priority)) {
    gFailedCommands++;
    return 0;
  }
  
  gRetryCount = 0;
  int success = 0;
  
  while (gRetryCount < MAX_RETRIES && !success) {
    Message msg;
    msg.ID = CONTROL_MSG_ID;
    msg.DLC = CONTROL_MSG_DLC;
    
    // Pack command data
    msg.Data[0] = (byte)cmdType;
    
    // Pack 16-bit parameter (Big-endian)
    msg.Data[1] = (byte)((paramValue >> 8) & 0xFF);
    msg.Data[2] = (byte)(paramValue & 0xFF);
    
    msg.Data[3] = (byte)priority;
    msg.Data[4] = 0x00;  // Reserved
    msg.Data[5] = 0x00;  // Reserved
    msg.Data[6] = 0x00;  // Reserved
    
    // Calculate and attach checksum
    msg.Data[7] = CalculateControlChecksum(msg.Data);
    
    // Send message
    Send(msg);
    gSentCommands++;
    success = 1;
    
    Write("Command sent [Attempt %d/%d] - Type: %d, Param: %d, Priority: %d",
          gRetryCount + 1, MAX_RETRIES, cmdType, paramValue, priority);
    
    gRetryCount++;
  }
  
  if (!success) {
    Write("Error: Command failed after %d retries", MAX_RETRIES);
    gFailedCommands++;
    return 0;
  }
  
  return 1;  // Success
}

// BONUS: Rate limiting - ensure commands at least 100ms apart
dword gLastCommandTime = 0;
#define MIN_COMMAND_INTERVAL 100  // ms

int SendCommandWithRateLimit(int cmdType, int paramValue, int priority) {
  dword now = GetTime();
  dword timeSinceLastCmd = now - gLastCommandTime;
  
  if (timeSinceLastCmd < MIN_COMMAND_INTERVAL) {
    Write("Rate limit: Wait %d ms before next command", 
          MIN_COMMAND_INTERVAL - timeSinceLastCmd);
    return 0;  // Command rejected
  }
  
  int result = SendCommand(cmdType, paramValue, priority);
  if (result) {
    gLastCommandTime = now;
  }
  
  return result;
}

// Test the command sender
on key 'C' {
  // Send valid command
  SendCommand(1, 1000, 5);
}

on key 'T' {
  // Send command with rate limiting
  SendCommandWithRateLimit(2, 2000, 3);
}

on key 'R' {
  // Test invalid parameters
  SendCommand(15, 1000, 5);    // Invalid command type
  SendCommand(1, 100000, 5);   // Invalid parameter
  SendCommand(1, 1000, 10);    // Invalid priority
}

on key 'S' {
  Write("===== Command Statistics =====");
  Write("Commands sent: %d", gSentCommands);
  Write("Commands failed: %d", gFailedCommands);
  Write("Success rate: %d%%", 
        (gSentCommands > 0) ? (100 * (gSentCommands - gFailedCommands) / gSentCommands) : 0);
  Write("==============================");
}
```

**Evaluation Criteria:**
- ✅ Parameter validation before packing
- ✅ Correct byte packing with proper byte order
- ✅ Checksum calculation accuracy
- ✅ Retry mechanism (max 3 attempts)
- ✅ Comprehensive logging
- ✅ Return status (success/failure)

**Challenge (Bonus):**
Add timing: Ensure commands are sent at least 100ms apart. How would you implement this?

---

## 🟣 **Interview Scenario 3: Timer-Based Monitoring & Timeout Detection**

**Difficulty:** ⭐⭐⭐ (Intermediate) | **Category:** Timers & Monitoring | **Time:** 20-25 min

**Real-World Context:**
You're creating a watchdog system that monitors multiple vehicle modules. Each module sends a heartbeat message every 100ms. You must:
- Detect if heartbeat stops (timeout after 200ms)
- Log timeout events
- Trigger recovery action on timeout
- Count total timeouts per module
- Maintain statistics (uptime, availability percentage)

Module messages:
- **Engine Module**: Message ID 0x100, expected every 100ms
- **Transmission Module**: Message ID 0x200, expected every 100ms
- **Chassis Module**: Message ID 0x300, expected every 100ms

**Requirements:**
1. Create timeout detection for all 3 modules
2. Log when timeout is detected
3. Calculate availability percentage (uptime / total time)
4. Display statistics on demand (press 'S' key)
5. Reset statistics (press 'R' key)

**Your Code:**
```capl
// Module heartbeat monitoring
#define ENGINE_TIMEOUT 200    // ms
#define TRANS_TIMEOUT 200     // ms
#define CHASSIS_TIMEOUT 200   // ms

// Message IDs
#define ENGINE_MSG 0x100
#define TRANS_MSG 0x200
#define CHASSIS_MSG 0x300

// Module structure
struct ModuleStatus {
  dword lastMessageTime;
  int messageCount;
  int timeoutCount;
  int timeout_ms;
  char name[20];
};

ModuleStatus gEngine, gTrans, gChassis;
dword gStartTime = 0;
timer gTimeoutCheckTimer;

// Initialize module
void InitModule(ModuleStatus &mod, char *name, int timeout) {
  strcpy(mod.name, name);
  mod.lastMessageTime = GetTime();
  mod.messageCount = 0;
  mod.timeoutCount = 0;
  mod.timeout_ms = timeout;
}

// Check if module has timed out
int CheckTimeout(ModuleStatus &mod) {
  dword now = GetTime();
  dword elapsed = now - mod.lastMessageTime;
  
  return (elapsed > mod.timeout_ms) ? 1 : 0;
}

// Calculate availability percentage
int CalculateAvailability(ModuleStatus &mod) {
  int total = mod.messageCount + mod.timeoutCount;
  if (total == 0) return 0;
  
  return (mod.messageCount * 100) / total;
}

// Display statistics for a module
void DisplayModuleStats(ModuleStatus &mod) {
  dword uptime = GetTime() - gStartTime;
  
  Write("  Name: %s", mod.name);
  Write("  Messages: %d", mod.messageCount);
  Write("  Timeouts: %d", mod.timeoutCount);
  Write("  Availability: %d%%", CalculateAvailability(mod));
  Write("  Expected timeout: %d ms", mod.timeout_ms);
  Write("");
}

// Recovery action on timeout
void RecoveryAction(ModuleStatus &mod) {
  Write("[%d ms] TIMEOUT: %s (no message for > %d ms)", 
        GetTime(), mod.name, mod.timeout_ms);
  
  mod.timeoutCount++;
  // Could send recovery command here
}

// Engine message handler
on message ENGINE_MSG {
  gEngine.lastMessageTime = GetTime();
  gEngine.messageCount++;
}

// Transmission message handler
on message TRANS_MSG {
  gTrans.lastMessageTime = GetTime();
  gTrans.messageCount++;
}

// Chassis message handler
on message CHASSIS_MSG {
  gChassis.lastMessageTime = GetTime();
  gChassis.messageCount++;
}

// Timeout check timer (runs every 100ms)
on timer gTimeoutCheckTimer {
  if (CheckTimeout(gEngine)) {
    RecoveryAction(gEngine);
  }
  
  if (CheckTimeout(gTrans)) {
    RecoveryAction(gTrans);
  }
  
  if (CheckTimeout(gChassis)) {
    RecoveryAction(gChassis);
  }
}

on start {
  gStartTime = GetTime();
  
  // Initialize all modules
  InitModule(gEngine, "Engine", ENGINE_TIMEOUT);
  InitModule(gTrans, "Transmission", TRANS_TIMEOUT);
  InitModule(gChassis, "Chassis", CHASSIS_TIMEOUT);
  
  // Start timeout check timer
  SetTimer(gTimeoutCheckTimer, 100);
  
  Write("Heartbeat monitor started");
}

on stop {
  CancelTimer(gTimeoutCheckTimer);
  Write("Heartbeat monitor stopped");
}

// Display statistics (press 'S')
on key 'S' {
  dword runtime = GetTime() - gStartTime;
  
  Write("");
  Write("========== Heartbeat Monitor Statistics ==========");
  Write("Runtime: %d ms (%.2f seconds)", runtime, runtime / 1000.0);
  Write("");
  
  DisplayModuleStats(gEngine);
  DisplayModuleStats(gTrans);
  DisplayModuleStats(gChassis);
  
  int totalMessages = gEngine.messageCount + gTrans.messageCount + gChassis.messageCount;
  int totalTimeouts = gEngine.timeoutCount + gTrans.timeoutCount + gChassis.timeoutCount;
  int overallAvailability = (totalMessages + totalTimeouts > 0) ? 
    (totalMessages * 100) / (totalMessages + totalTimeouts) : 0;
  
  Write("Overall statistics:");
  Write("  Total messages: %d", totalMessages);
  Write("  Total timeouts: %d", totalTimeouts);
  Write("  Overall availability: %d%%", overallAvailability);
  Write("=================================================");
  Write("");
}

// Reset statistics (press 'R')
on key 'R' {
  gStartTime = GetTime();
  
  gEngine.messageCount = 0;
  gEngine.timeoutCount = 0;
  gEngine.lastMessageTime = GetTime();
  
  gTrans.messageCount = 0;
  gTrans.timeoutCount = 0;
  gTrans.lastMessageTime = GetTime();
  
  gChassis.messageCount = 0;
  gChassis.timeoutCount = 0;
  gChassis.lastMessageTime = GetTime();
  
  Write("Statistics reset");
}
```

**Evaluation Criteria:**
- ✅ Accurate timeout detection (using timers, not just elapsed time)
- ✅ Proper timer management (start/cancel/restart)
- ✅ Statistics calculation
- ✅ Clean periodic reporting (no spam to trace)
- ✅ Recovery action on timeout
- ✅ Memory efficiency

---

## 🔴 **Interview Scenario 4: State Machine with Protocol Implementation**

**Difficulty:** ⭐⭐⭐⭐ (Advanced) | **Category:** State Machines | **Time:** 25-30 min

**Real-World Context:**
You're implementing a diagnostic session manager for ECU communication. The protocol has these states:

```
IDLE → WAIT_RESPONSE → PROCESS → IDLE
        ↓ (timeout)
      TIMEOUT_RECOVER
```

**Protocol Flow:**
1. **IDLE**: Waiting for start command (keyboard: 'S')
2. **WAIT_RESPONSE**: Sends diagnostic request, waits for response (0x600)
3. **PROCESS**: Processes received response, validates data
4. **TIMEOUT_RECOVER**: If no response after 2 seconds, retry up to 3 times
5. Back to IDLE after success or 3 failures

**Requirements:**
1. Implement state machine with 4 states
2. Send request message on entering WAIT_RESPONSE: `{0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, checksum}`
3. Validate response message (ID: 0x600, first byte must equal 0x41)
4. Implement 2-second timeout
5. Retry mechanism (max 3 attempts)
6. Transition to IDLE after success or failure
7. Log all state transitions with timestamps

**Your Code:**
```capl
// State definitions
#define STATE_IDLE 0
#define STATE_WAIT_RESPONSE 1
#define STATE_PROCESS 2
#define STATE_TIMEOUT_RECOVER 3

// Message IDs
#define REQUEST_MSG_ID 0x500
#define RESPONSE_MSG_ID 0x600

// Timing
#define RESPONSE_TIMEOUT 2000  // ms
#define MAX_RETRIES 3

// Global state
int gCurrentState = STATE_IDLE;
int gRetryAttempt = 0;
int gRequestID = 0;
dword gStateStartTime = 0;
timer gTimeoutTimer;

// Statistics
int gTotalRequests = 0;
int gSuccessfulResponses = 0;
int gFailedRequests = 0;
int gTimeoutCount = 0;

byte gReceivedResponseData[8];
int gReceivedResponseDLC = 0;

// Log state transition
void LogStateTransition(int oldState, int newState) {
  char *stateNames[] = {"IDLE", "WAIT_RESPONSE", "PROCESS", "TIMEOUT_RECOVER"};
  Write("[%d ms] State transition: %s -> %s", 
        GetTime(), stateNames[oldState], stateNames[newState]);
}

// Transition to new state
void TransitionToState(int newState) {
  // Validate state machine transitions
  int validTransition = 0;
  
  switch (gCurrentState) {
    case STATE_IDLE:
      if (newState == STATE_WAIT_RESPONSE) validTransition = 1;
      break;
    case STATE_WAIT_RESPONSE:
      if (newState == STATE_PROCESS || newState == STATE_TIMEOUT_RECOVER) validTransition = 1;
      break;
    case STATE_PROCESS:
      if (newState == STATE_IDLE) validTransition = 1;
      break;
    case STATE_TIMEOUT_RECOVER:
      if (newState == STATE_WAIT_RESPONSE || newState == STATE_IDLE) validTransition = 1;
      break;
  }
  
  if (!validTransition) {
    Write("Error: Invalid state transition attempted");
    return;
  }
  
  LogStateTransition(gCurrentState, newState);
  gCurrentState = newState;
  gStateStartTime = GetTime();
  
  // Execute state-specific setup
  switch (newState) {
    case STATE_IDLE:
      CancelTimer(gTimeoutTimer);
      Write("Ready for next request");
      break;
      
    case STATE_WAIT_RESPONSE:
      gRequestID++;
      gTotalRequests++;
      SendDiagnosticRequest();
      SetTimer(gTimeoutTimer, RESPONSE_TIMEOUT);
      Write("Waiting for response (Request ID: %d)", gRequestID);
      break;
      
    case STATE_PROCESS:
      CancelTimer(gTimeoutTimer);
      ProcessResponse();
      break;
      
    case STATE_TIMEOUT_RECOVER:
      Write("Recovering from timeout (Attempt %d/%d)", gRetryAttempt, MAX_RETRIES);
      SetTimer(gTimeoutTimer, 1000);  // Wait 1 second before retry
      break;
  }
}

// Send diagnostic request
void SendDiagnosticRequest() {
  Message msg;
  msg.ID = REQUEST_MSG_ID;
  msg.DLC = 8;
  
  // Pack request: {0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, checksum}
  msg.Data[0] = 0x01;
  msg.Data[1] = 0x02;
  msg.Data[2] = 0x03;
  msg.Data[3] = 0x00;
  msg.Data[4] = 0x00;
  msg.Data[5] = 0x00;
  msg.Data[6] = 0x00;
  
  // Calculate simple checksum
  byte checksum = 0;
  for (int i = 0; i < 7; i++) {
    checksum += msg.Data[i];
  }
  msg.Data[7] = (~checksum) + 1;
  
  Send(msg);
  Write("Diagnostic request sent");
}

// Process received response
void ProcessResponse() {
  // Validate response
  if (gReceivedResponseDLC < 2) {
    Write("Error: Response DLC invalid");
    TransitionToState(STATE_IDLE);
    gFailedRequests++;
    return;
  }
  
  // First byte must be 0x41 (0x01 + 0x40)
  if (gReceivedResponseData[0] != 0x41) {
    Write("Error: Invalid response format (byte 0 = 0x%02X)", gReceivedResponseData[0]);
    TransitionToState(STATE_IDLE);
    gFailedRequests++;
    return;
  }
  
  Write("Valid response received!");
  Write("Response data:");
  for (int i = 0; i < gReceivedResponseDLC; i++) {
    Write("  Data[%d] = 0x%02X", i, gReceivedResponseData[i]);
  }
  
  gSuccessfulResponses++;
  TransitionToState(STATE_IDLE);
}

// Timeout handler
on timer gTimeoutTimer {
  switch (gCurrentState) {
    case STATE_WAIT_RESPONSE:
      gTimeoutCount++;
      Write("Timeout waiting for response");
      
      if (gRetryAttempt < MAX_RETRIES) {
        gRetryAttempt++;
        TransitionToState(STATE_TIMEOUT_RECOVER);
      } else {
        Write("Max retries exceeded");
        gFailedRequests++;
        TransitionToState(STATE_IDLE);
      }
      break;
      
    case STATE_TIMEOUT_RECOVER:
      // Ready to retry
      gRetryAttempt++;
      if (gRetryAttempt <= MAX_RETRIES) {
        TransitionToState(STATE_WAIT_RESPONSE);
      } else {
        Write("Aborting: Max retries exceeded");
        gFailedRequests++;
        TransitionToState(STATE_IDLE);
      }
      break;
  }
}

// Response message handler
on message RESPONSE_MSG_ID {
  if (gCurrentState != STATE_WAIT_RESPONSE) {
    Write("Response received in wrong state: %d", gCurrentState);
    return;
  }
  
  // Copy response data
  gReceivedResponseDLC = this.DLC;
  for (int i = 0; i < this.DLC && i < 8; i++) {
    gReceivedResponseData[i] = this.Data[i];
  }
  
  gRetryAttempt = 0;  // Reset retry count on success
  TransitionToState(STATE_PROCESS);
}

// Start diagnostic session (press 'S')
on key 'S' {
  if (gCurrentState == STATE_IDLE) {
    Write("\n===== Starting Diagnostic Session =====");
    TransitionToState(STATE_WAIT_RESPONSE);
  } else {
    Write("Already in diagnostic session (state: %d)", gCurrentState);
  }
}

// Display statistics (press 'T')
on key 'T' {
  Write("");
  Write("===== Diagnostic Session Statistics =====");
  Write("Total requests: %d", gTotalRequests);
  Write("Successful responses: %d", gSuccessfulResponses);
  Write("Failed requests: %d", gFailedRequests);
  Write("Timeout events: %d", gTimeoutCount);
  Write("Success rate: %d%%", 
        gTotalRequests > 0 ? (gSuccessfulResponses * 100) / gTotalRequests : 0);
  Write("Current state: %d", gCurrentState);
  Write("========================================");
}

on start {
  TransitionToState(STATE_IDLE);
}

on stop {
  CancelTimer(gTimeoutTimer);
}
```

**Evaluation Criteria:**
- ✅ Proper state machine design
- ✅ Valid state transitions only
- ✅ Timeout implementation
- ✅ Retry logic with attempt counter
- ✅ Message validation
- ✅ Comprehensive error handling
- ✅ Clear state logging

---

## 🟡 **Interview Scenario 5: Data Validation & Error Recovery**

**Difficulty:** ⭐⭐⭐ (Intermediate) | **Category:** Validation & Error Handling | **Time:** 20-25 min

**Real-World Context:**
You're developing a sensor data aggregator that collects readings from multiple sensors:
- **Temperature sensor (0x150)**: Valid range -40°C to 125°C
- **Pressure sensor (0x160)**: Valid range 0-100 PSI
- **Speed sensor (0x170)**: Valid range 0-300 km/h

Data consistency rules:
- Temperature cannot change more than 5°C between messages
- Pressure cannot change more than 10 PSI between messages
- Speed cannot exceed acceleration limit (max 5 km/h per 100ms)

**Requirements:**
1. Validate message format (DLC, byte ranges)
2. Check value ranges for each sensor
3. Detect impossible transitions
4. Quarantine bad data (don't process)
5. Log validation failures with details
6. Recover after N errors by resetting sensor readings

**Your Code:**
```capl
// Constants
#define TEMP_SENSOR_ID 0x150
#define PRES_SENSOR_ID 0x160
#define SPEED_SENSOR_ID 0x170

// Validation ranges
#define TEMP_MIN (-40)
#define TEMP_MAX 125
#define PRES_MIN 0
#define PRES_MAX 100
#define SPEED_MIN 0
#define SPEED_MAX 300

// Rate of change limits
#define MAX_TEMP_CHANGE 5      // °C per message
#define MAX_PRES_CHANGE 10     // PSI per message
#define MAX_SPEED_CHANGE 5     // km/h per 100ms

// Previous sensor values
int gLastTemp = 20;      // Start at room temp
int gLastPres = 50;      // Mid-range
int gLastSpeed = 0;      // Stationary
dword gLastSpeedTime = 0;

// Error counters
int gTempErrors = 0;
int gPresErrors = 0;
int gSpeedErrors = 0;
int gConsistencyErrors = 0;

// Validate temperature
int ValidateTemperature(byte rawValue) {
  int temp = (int)rawValue - 40;  // Offset conversion
  
  // Check range
  if (temp < TEMP_MIN || temp > TEMP_MAX) {
    Write("Temp validation failed: %d°C out of range [%d, %d]", 
          temp, TEMP_MIN, TEMP_MAX);
    gTempErrors++;
    return 0;
  }
  
  // Check rate of change
  int tempDelta = abs(temp - gLastTemp);
  if (tempDelta > MAX_TEMP_CHANGE) {
    Write("Temp validation failed: Change %d°C exceeds max %d°C (from %d to %d)", 
          tempDelta, MAX_TEMP_CHANGE, gLastTemp, temp);
    gTempErrors++;
    return 0;
  }
  
  gLastTemp = temp;
  return 1;  // Valid
}

// Validate pressure
int ValidatePressure(byte rawValue) {
  int pres = rawValue;  // Direct mapping 0-100 PSI
  
  // Check range
  if (pres < PRES_MIN || pres > PRES_MAX) {
    Write("Pres validation failed: %d PSI out of range [%d, %d]", 
          pres, PRES_MIN, PRES_MAX);
    gPresErrors++;
    return 0;
  }
  
  // Check rate of change
  int presDelta = abs(pres - gLastPres);
  if (presDelta > MAX_PRES_CHANGE) {
    Write("Pres validation failed: Change %d PSI exceeds max %d PSI (from %d to %d)", 
          presDelta, MAX_PRES_CHANGE, gLastPres, pres);
    gPresErrors++;
    return 0;
  }
  
  gLastPres = pres;
  return 1;  // Valid
}

// Validate speed
int ValidateSpeed(int rawValue) {
  int speed = rawValue;  // Direct mapping
  
  // Check range
  if (speed < SPEED_MIN || speed > SPEED_MAX) {
    Write("Speed validation failed: %d km/h out of range [%d, %d]", 
          speed, SPEED_MIN, SPEED_MAX);
    gSpeedErrors++;
    return 0;
  }
  
  // Check acceleration limit
  dword now = GetTime();
  if (gLastSpeedTime > 0) {
    int timeDelta = now - gLastSpeedTime;
    if (timeDelta >= 100) {  // Only check every 100ms
      int speedDelta = abs(speed - gLastSpeed);
      int maxChangeAllowed = (speedDelta * timeDelta) / 100;  // Scale to time
      
      if (speedDelta > MAX_SPEED_CHANGE) {
        Write("Speed validation failed: Acceleration too high");
        Write("  Speed change: %d km/h in %d ms", speedDelta, timeDelta);
        gSpeedErrors++;
        return 0;
      }
    }
  }
  
  gLastSpeed = speed;
  gLastSpeedTime = now;
  return 1;  // Valid
}

// Check data consistency between sensors
int CheckConsistency() {
  // Example: At high speed, temperature should be increasing (engine load)
  // At low speed, temperature should be stable or decreasing
  // This is a simple example - real logic would be more sophisticated
  
  if (gLastSpeed > 200 && gLastTemp > 110) {
    // High speed AND high temp - normal
    return 1;
  }
  if (gLastSpeed < 20 && gLastTemp < 40) {
    // Low speed AND low temp - normal
    return 1;
  }
  if (gLastSpeed > 100 && gLastTemp < 30) {
    // High speed but very low temp - INCONSISTENT
    Write("Consistency check failed: High speed (%d) but low temp (%d)", 
          gLastSpeed, gLastTemp);
    gConsistencyErrors++;
    return 0;
  }
  
  return 1;  // Consistent
}

// Log validation error with context
void LogValidationError(char *sensorName, char *reason) {
  Write("[%d ms] Validation Error - %s: %s", GetTime(), sensorName, reason);
}

// Temperature sensor handler
on message TEMP_SENSOR_ID {
  if (this.DLC < 1) {
    LogValidationError("Temperature", "Invalid DLC");
    return;
  }
  
  if (ValidateTemperature(this.Data[0])) {
    Write("[Valid] Temperature: %d°C", gLastTemp);
  }
}

// Pressure sensor handler
on message PRES_SENSOR_ID {
  if (this.DLC < 1) {
    LogValidationError("Pressure", "Invalid DLC");
    return;
  }
  
  if (ValidatePressure(this.Data[0])) {
    Write("[Valid] Pressure: %d PSI", gLastPres);
  }
}

// Speed sensor handler
on message SPEED_SENSOR_ID {
  if (this.DLC < 2) {
    LogValidationError("Speed", "Invalid DLC");
    return;
  }
  
  int speed = (this.Data[0] << 8) | this.Data[1];
  
  if (ValidateSpeed(speed) && CheckConsistency()) {
    Write("[Valid] Speed: %d km/h", gLastSpeed);
  }
}

// Display statistics (press 'S')
on key 'S' {
  Write("");
  Write("===== Sensor Data Validation Statistics =====");
  Write("Temperature errors: %d", gTempErrors);
  Write("Pressure errors: %d", gPresErrors);
  Write("Speed errors: %d", gSpeedErrors);
  Write("Consistency errors: %d", gConsistencyErrors);
  Write("===========================================");
  Write("Current values:");
  Write("  Temperature: %d°C", gLastTemp);
  Write("  Pressure: %d PSI", gLastPres);
  Write("  Speed: %d km/h", gLastSpeed);
  Write("");
}

// Reset statistics (press 'R')
on key 'R' {
  gTempErrors = 0;
  gPresErrors = 0;
  gSpeedErrors = 0;
  gConsistencyErrors = 0;
  Write("Validation statistics reset");
}
```

**Evaluation Criteria:**
- ✅ Comprehensive validation checks
- ✅ Proper error messages with context
- ✅ Range checking
- ✅ Rate-of-change validation
- ✅ Track previous values correctly
- ✅ Graceful error recovery
- ✅ Detailed logging

---

## 🟠 **Interview Scenario 6: Message Gateway & Forwarding**

**Difficulty:** ⭐⭐⭐⭐ (Advanced) | **Category:** Gateway & Rate Limiting | **Time:** 25-30 min

**Real-World Context:**
You're building a CAN gateway that:
- Receives diagnostic messages on Channel 1 (IDs: 0x100-0x1FF)
- Forwards them to Channel 2
- Modifies certain bytes before forwarding (encryption/masking)
- Filters out invalid messages
- Throttles forwarding rate (max 10 messages/second)
- Maintains statistics

**Message IDs to forward:**
- 0x100-0x10F: Engine diagnostics
- 0x150-0x15F: Transmission diagnostics
- 0x180-0x18F: Chassis diagnostics

**Modifications required:**
- Byte 0: XOR with 0xAA (encryption pattern)
- Add timestamp in Byte 4-5 (milliseconds since start, Big-endian)

**Requirements:**
1. Monitor specified message IDs
2. Validate before forwarding
3. Apply modifications (XOR, timestamp)
4. Implement rate limiting
5. Track forwarded vs dropped messages
6. Display gateway statistics

**Your Code:**
```capl
// Gateway configuration
#define MIN_FORWARD_ID 0x100
#define MAX_FORWARD_ID 0x1FF
#define XOR_KEY 0xAA              // Encryption pattern
#define MAX_FORWARD_RATE 10       // messages/second
#define TIME_WINDOW 1000          // ms

// Statistics
int gMessagesReceived = 0;
int gMessagesForwarded = 0;
int gMessagesDropped = 0;
dword gLastForwardTime = 0;
int gForwardCountInWindow = 0;
dword gWindowStartTime = 0;

// Check if message should be forwarded
int ShouldForward(int ID) {
  // Only forward diagnostic messages in range
  if (ID >= MIN_FORWARD_ID && ID <= MAX_FORWARD_ID) {
    return 1;
  }
  return 0;
}

// Apply XOR encryption to first data byte
void ApplyXOREncryption(Message &msg) {
  msg.Data[0] ^= XOR_KEY;
}

// Add timestamp to message (bytes 4-5)
void AddTimestamp(Message &msg) {
  dword timestamp = GetTime();
  
  // Store timestamp in Big-endian format
  msg.Data[4] = (byte)((timestamp >> 8) & 0xFF);
  msg.Data[5] = (byte)(timestamp & 0xFF);
}

// Check and apply rate limiting
int ApplyRateLimit() {
  dword now = GetTime();
  
  // Check if we're still in the current time window
  if ((now - gWindowStartTime) >= TIME_WINDOW) {
    // New window started
    gWindowStartTime = now;
    gForwardCountInWindow = 0;
  }
  
  gForwardCountInWindow++;
  
  // Calculate max messages allowed in this window
  int maxInWindow = (MAX_FORWARD_RATE * TIME_WINDOW) / 1000;
  
  if (gForwardCountInWindow > maxInWindow) {
    Write("[%d ms] Rate limit exceeded: %d messages in %d ms", 
          now, gForwardCountInWindow, TIME_WINDOW);
    gMessagesDropped++;
    return 0;  // Rate limit exceeded
  }
  
  return 1;  // Rate limit OK
}

// Modify message before forwarding
void ModifyMessage(Message &msg) {
  // Ensure DLC is valid
  if (msg.DLC < 6) {
    // Pad to at least 6 bytes for timestamp
    msg.DLC = 6;
  }
  
  // Apply encryption to byte 0
  ApplyXOREncryption(msg);
  
  // Add timestamp to bytes 4-5
  AddTimestamp(msg);
}

// Forward message handler for each message ID range
on message 0x100 {
  gMessagesReceived++;
  
  if (ShouldForward(this.ID) && ApplyRateLimit()) {
    Message fwdMsg = this;
    ModifyMessage(fwdMsg);
    
    // Send on Channel 2 (output command)
    Write("Forwarding 0x%03X: Original byte0=0x%02X -> Encrypted=0x%02X",
          fwdMsg.ID, this.Data[0], fwdMsg.Data[0]);
    
    // Note: output() is for multi-channel; Send() for single channel
    // For single channel testing, use Send()
    Send(fwdMsg);
    gMessagesForwarded++;
    gLastForwardTime = GetTime();
  }
}

on message 0x101 {
  gMessagesReceived++;
  if (ShouldForward(this.ID) && ApplyRateLimit()) {
    Message fwdMsg = this;
    ModifyMessage(fwdMsg);
    Send(fwdMsg);
    gMessagesForwarded++;
  }
}

on message 0x150 {
  gMessagesReceived++;
  if (ShouldForward(this.ID) && ApplyRateLimit()) {
    Message fwdMsg = this;
    ModifyMessage(fwdMsg);
    Send(fwdMsg);
    gMessagesForwarded++;
  }
}

on message 0x180 {
  gMessagesReceived++;
  if (ShouldForward(this.ID) && ApplyRateLimit()) {
    Message fwdMsg = this;
    ModifyMessage(fwdMsg);
    Send(fwdMsg);
    gMessagesForwarded++;
  }
}

// Generic handler for other diagnostic messages
on message * {
  if (this.ID >= MIN_FORWARD_ID && this.ID <= MAX_FORWARD_ID) {
    gMessagesReceived++;
    
    if (ApplyRateLimit()) {
      Message fwdMsg = this;
      ModifyMessage(fwdMsg);
      Send(fwdMsg);
      gMessagesForwarded++;
    }
  }
}

// Display gateway statistics (press 'S')
on key 'S' {
  dword runtime = GetTime();
  
  Write("");
  Write("===== CAN Gateway Statistics =====");
  Write("Runtime: %d ms", runtime);
  Write("Messages received: %d", gMessagesReceived);
  Write("Messages forwarded: %d", gMessagesForwarded);
  Write("Messages dropped: %d", gMessagesDropped);
  
  if (gMessagesReceived > 0) {
    int forwardRate = (gMessagesForwarded * 100) / gMessagesReceived;
    Write("Forward rate: %d%%", forwardRate);
  }
  
  if (runtime > 0) {
    int messagesPerSecond = (gMessagesForwarded * 1000) / runtime;
    Write("Throughput: %d msg/sec", messagesPerSecond);
  }
  
  Write("Max forward rate: %d msg/sec", MAX_FORWARD_RATE);
  Write("Current window: %d/%d messages", gForwardCountInWindow, 
        (MAX_FORWARD_RATE * TIME_WINDOW) / 1000);
  Write("==================================");
}

on start {
  gWindowStartTime = GetTime();
  Write("CAN Gateway started");
  Write("Forwarding: 0x%03X-0x%03X", MIN_FORWARD_ID, MAX_FORWARD_ID);
  Write("Encryption: XOR with 0x%02X", XOR_KEY);
  Write("Rate limit: %d messages/sec", MAX_FORWARD_RATE);
}
```

**Evaluation Criteria:**
- ✅ Correct message filtering
- ✅ Proper data modification (XOR, endianness)
- ✅ Rate limiting algorithm
- ✅ Statistics tracking
- ✅ Multi-channel handling
- ✅ Error handling for invalid data

---

## 🔵 **Interview Scenario 7: Circular Buffer & Data Logging**

**Difficulty:** ⭐⭐⭐ (Intermediate) | **Category:** Data Structures | **Time:** 20-25 min

**Real-World Context:**
You need to implement a high-speed data logger that captures CAN messages in a circular buffer for later analysis. The logger must:
- Store last 1000 messages (memory efficient)
- Record: timestamp, message ID, all 8 data bytes
- Handle buffer wraparound
- Export logged data on demand
- Calculate statistics (message frequency, data patterns)

**Requirements:**
1. Create circular buffer for 1000 messages
2. Log every message on bus (on message *)
3. Use keyboard commands:
   - 'E': Export buffer to trace
   - 'S': Show statistics (message count, IDs received, frequency)
   - 'C': Clear buffer
4. Calculate average message arrival time
5. Find most common message ID

**Your Code:**
```capl
// Circular buffer constants
#define BUFFER_SIZE 1000

// Log entry structure
struct LogEntry {
  dword timestamp;
  int ID;
  byte DLC;
  byte Data[8];
};

// Circular buffer
LogEntry gBuffer[BUFFER_SIZE];
int gWriteIndex = 0;
int gReadIndex = 0;
int gBufferCount = 0;

// Statistics
int gIDFrequency[256];      // Frequency counter per message ID
dword gFirstMessageTime = 0;
dword gLastMessageTime = 0;
int gTotalMessagesLogged = 0;

// Log a message to circular buffer
void LogMessage(Message msg) {
  gBuffer[gWriteIndex].timestamp = GetTime();
  gBuffer[gWriteIndex].ID = msg.ID;
  gBuffer[gWriteIndex].DLC = msg.DLC;
  
  // Copy data bytes
  for (int i = 0; i < msg.DLC && i < 8; i++) {
    gBuffer[gWriteIndex].Data[i] = msg.Data[i];
  }
  
  // Track first and last message time
  if (gTotalMessagesLogged == 0) {
    gFirstMessageTime = GetTime();
  }
  gLastMessageTime = GetTime();
  
  // Update frequency counter
  if (msg.ID < 256) {
    gIDFrequency[msg.ID]++;
  }
  
  gTotalMessagesLogged++;
  
  // Move write index with wraparound
  gWriteIndex = (gWriteIndex + 1) % BUFFER_SIZE;
  
  if (gBufferCount < BUFFER_SIZE) {
    gBufferCount++;
  } else {
    // Buffer full, advance read index
    gReadIndex = (gReadIndex + 1) % BUFFER_SIZE;
  }
}

// Export buffer contents to trace
void ExportBuffer() {
  Write("");
  Write("===== Circular Buffer Export =====");
  Write("Total entries: %d (max %d)", gBufferCount, BUFFER_SIZE);
  Write("Write pointer: %d", gWriteIndex);
  Write("Read pointer: %d", gReadIndex);
  Write("");
  
  int currentIndex = gReadIndex;
  int count = 0;
  
  Write("Timestamp   | ID    | DLC | Data");
  Write("----|---|---------|-----|---|--------");
  
  while (count < gBufferCount && count < 100) {  // Limit export to 100 messages
    LogEntry *entry = &gBuffer[currentIndex];
    
    Write("%10d  | 0x%03X | %d   |", entry->timestamp, entry->ID, entry->DLC);
    
    for (int i = 0; i < entry->DLC; i++) {
      Write(" %02X", entry->Data[i]);
    }
    
    currentIndex = (currentIndex + 1) % BUFFER_SIZE;
    count++;
  }
  
  Write("=====================================");
}

// Calculate statistics
void CalculateStatistics() {
  if (gBufferCount == 0) {
    Write("No data to analyze");
    return;
  }
  
  dword timespan = gLastMessageTime - gFirstMessageTime;
  int averageInterval = (timespan > 0) ? (timespan / gBufferCount) : 0;
  
  Write("");
  Write("===== Buffer Statistics =====");
  Write("Total messages logged: %d", gTotalMessagesLogged);
  Write("Buffer capacity: %d messages", BUFFER_SIZE);
  Write("Current buffer fill: %d%%", (gBufferCount * 100) / BUFFER_SIZE);
  Write("");
  
  Write("Time analysis:");
  Write("  First message: %d ms", gFirstMessageTime);
  Write("  Last message: %d ms", gLastMessageTime);
  Write("  Timespan: %d ms", timespan);
  Write("  Average interval: %d ms/msg", averageInterval);
  
  if (timespan > 0) {
    int msgPerSec = (gBufferCount * 1000) / timespan;
    Write("  Message rate: %d msg/sec", msgPerSec);
  }
  
  Write("============================");
}

// Get most frequent message ID
int GetMostFrequentID() {
  int maxID = 0;
  int maxFreq = 0;
  
  for (int i = 0; i < 256; i++) {
    if (gIDFrequency[i] > maxFreq) {
      maxFreq = gIDFrequency[i];
      maxID = i;
    }
  }
  
  return maxID;
}

// Find least frequent message ID
int GetLeastFrequentID() {
  int minID = 0;
  int minFreq = 999999;
  
  for (int i = 0; i < 256; i++) {
    if (gIDFrequency[i] > 0 && gIDFrequency[i] < minFreq) {
      minFreq = gIDFrequency[i];
      minID = i;
    }
  }
  
  return minID;
}

// Log all messages on bus
on message * {
  LogMessage(this);
}

// Export buffer (press 'E')
on key 'E' {
  ExportBuffer();
}

// Show statistics (press 'S')
on key 'S' {
  CalculateStatistics();
  
  int mostFreq = GetMostFrequentID();
  Write("");
  Write("Message ID analysis:");
  Write("Most frequent ID: 0x%03X (%d occurrences)", 
        mostFreq, gIDFrequency[mostFreq]);
  
  // Find all unique IDs logged
  int uniqueIDCount = 0;
  for (int i = 0; i < 256; i++) {
    if (gIDFrequency[i] > 0) {
      uniqueIDCount++;
    }
  }
  Write("Unique message IDs: %d", uniqueIDCount);
  Write("");
}

// Clear buffer (press 'C')
on key 'C' {
  gWriteIndex = 0;
  gReadIndex = 0;
  gBufferCount = 0;
  gTotalMessagesLogged = 0;
  
  // Clear frequency counters
  for (int i = 0; i < 256; i++) {
    gIDFrequency[i] = 0;
  }
  
  Write("Circular buffer cleared");
}

on start {
  Write("Data logger started");
  Write("Buffer capacity: %d messages", BUFFER_SIZE);
  Write("Commands: E=Export, S=Stats, C=Clear");
}
```

**Evaluation Criteria:**
- ✅ Efficient circular buffer implementation
- ✅ Correct wraparound handling
- ✅ Statistics calculation
- ✅ Clean data export
- ✅ Memory efficient
- ✅ No data loss

---

## 🟢 **Interview Scenario 8: Complex Message Filtering & Aggregation**

**Difficulty:** ⭐⭐⭐⭐ (Advanced) | **Category:** Pattern Detection | **Time:** 25-30 min

**Real-World Context:**
You're creating an automated test scenario analyzer that:
- Monitors multiple message streams (Engine, Transmission, Chassis)
- Detects specific patterns (startup sequence, shutdown sequence, fault)
- Counts pattern occurrences
- Logs pattern timing
- Triggers alerts on pattern detection

**Patterns to detect:**

**Startup Sequence:**
1. Message 0x100 received with Data[0] = 0x00
2. Within 200ms, Message 0x100 with Data[0] = 0x01
3. Within next 300ms, Message 0x200 with Data[0] = 0x01

**Shutdown Sequence:**
1. Message 0x100 with Data[0] = 0x00
2. Message 0x200 with Data[0] = 0x00
3. Both received within 100ms of each other

**Fault Pattern:**
- Message 0x100 with Data[1] = 0xFF (error byte)
- Message 0x300 with Data[0] (fault code) not received within 500ms

**Requirements:**
1. Track state for each pattern
2. Detect complete patterns with timing
3. Log pattern detections with timestamps
4. Count each pattern type
5. High-performance detection (no missed patterns)

**Your Code:**
```capl
// Pattern detection states
#define PATTERN_IDLE 0
#define PATTERN_STEP1 1
#define PATTERN_STEP2 2
#define PATTERN_STEP3 3

// Startup sequence pattern detection
int gStartupState = PATTERN_IDLE;
dword gStartupStartTime = 0;
int gStartupCount = 0;

// Shutdown sequence pattern detection
int gShutdownState = PATTERN_IDLE;
dword gShutdownStartTime = 0;
int gShutdownCount = 0;
dword gLastMsg0x100Time = 0;
dword gLastMsg0x200Time = 0;

// Fault pattern detection
int gFaultPatternActive = 0;
dword gFaultDetectedTime = 0;
int gFaultCount = 0;

// Process startup pattern
void ProcessStartupPattern() {
  // Pattern: 0x100 Data[0]=0x00 -> 0x100 Data[0]=0x01 -> 0x200 Data[0]=0x01
  // Timing: Step 2 within 200ms, Step 3 within next 300ms (500ms total)
}

// Process shutdown pattern
void ProcessShutdownPattern() {
  // Pattern: 0x100 Data[0]=0x00 AND 0x200 Data[0]=0x00
  // Timing: Both within 100ms of each other
}

// Check for fault pattern
void CheckFaultPattern(byte faultCode) {
  // Pattern: 0x100 Data[1]=0xFF (error) but 0x300 not received within 500ms
  gFaultPatternActive = 1;
  gFaultDetectedTime = GetTime();
  gFaultCount++;
}

// Timeout for startup pattern
timer gStartupTimeoutTimer;

on timer gStartupTimeoutTimer {
  if (gStartupState != PATTERN_IDLE) {
    Write("Startup pattern timeout at step %d", gStartupState);
    gStartupState = PATTERN_IDLE;
  }
}

// Message 0x100 handler
on message 0x100 {
  byte commandByte = this.Data[0];
  dword now = GetTime();
  
  gLastMsg0x100Time = now;
  
  // STARTUP PATTERN DETECTION
  if (commandByte == 0x00 && gStartupState == PATTERN_IDLE) {
    gStartupState = PATTERN_STEP1;
    gStartupStartTime = now;
    Write("[Startup] Step 1: Message 0x100 Data[0]=0x00 detected at %d ms", now);
    SetTimer(gStartupTimeoutTimer, 500);  // 500ms total timeout
  } 
  else if (commandByte == 0x01 && gStartupState == PATTERN_STEP1) {
    dword elapsed = now - gStartupStartTime;
    if (elapsed <= 200) {
      gStartupState = PATTERN_STEP2;
      Write("[Startup] Step 2: Message 0x100 Data[0]=0x01 detected at %d ms (elapsed: %d ms)", 
            now, elapsed);
    } else {
      Write("[Startup] Pattern failed: Step 2 timeout (elapsed: %d ms, max: 200 ms)", elapsed);
      gStartupState = PATTERN_IDLE;
    }
  }
  
  // SHUTDOWN PATTERN DETECTION
  if (commandByte == 0x00) {
    gShutdownStartTime = now;
    gShutdownState = PATTERN_STEP1;
    Write("[Shutdown] Detected 0x100 Data[0]=0x00 at %d ms", now);
  }
  
  // FAULT PATTERN DETECTION
  if (this.DLC > 1 && this.Data[1] == 0xFF) {
    CheckFaultPattern(this.Data[1]);
    Write("[Fault] Error detected in 0x100 Data[1]=0xFF at %d ms", now);
  }
}

// Message 0x200 handler
on message 0x200 {
  byte commandByte = this.Data[0];
  dword now = GetTime();
  
  gLastMsg0x200Time = now;
  
  // STARTUP PATTERN DETECTION - Step 3
  if (commandByte == 0x01 && gStartupState == PATTERN_STEP2) {
    dword elapsed = now - gStartupStartTime;
    if (elapsed <= 500) {
      gStartupState = PATTERN_STEP3;
      gStartupCount++;
      CancelTimer(gStartupTimeoutTimer);
      
      Write("[Startup] PATTERN COMPLETE at %d ms (total elapsed: %d ms)", now, elapsed);
      Write("[Startup] Pattern #%d detected", gStartupCount);
    } else {
      Write("[Startup] Pattern failed: Step 3 timeout (elapsed: %d ms, max: 500 ms)", elapsed);
      gStartupState = PATTERN_IDLE;
    }
  }
  
  // SHUTDOWN PATTERN DETECTION
  if (commandByte == 0x00 && gShutdownState == PATTERN_STEP1) {
    dword elapsed = now - gShutdownStartTime;
    if (elapsed <= 100) {
      gShutdownCount++;
      
      Write("[Shutdown] PATTERN COMPLETE at %d ms", now);
      Write("[Shutdown] 0x100 and 0x200 both zero within %d ms", elapsed);
      Write("[Shutdown] Pattern #%d detected", gShutdownCount);
      
      gShutdownState = PATTERN_IDLE;
    }
  }
}

// Message 0x300 handler
on message 0x300 {
  dword now = GetTime();
  byte faultCode = this.Data[0];
  
  // FAULT PATTERN RECOVERY
  if (gFaultPatternActive) {
    dword elapsed = now - gFaultDetectedTime;
    
    if (elapsed <= 500) {
      Write("[Fault] Response received at %d ms (elapsed: %d ms) with fault code: 0x%02X", 
            now, elapsed, faultCode);
      gFaultPatternActive = 0;  // Pattern resolved
    }
  }
}

// Timeout check for fault pattern (press 'F')
timer gFaultCheckTimer;

on timer gFaultCheckTimer {
  if (gFaultPatternActive) {
    dword now = GetTime();
    dword elapsed = now - gFaultDetectedTime;
    
    if (elapsed > 500) {
      gFaultCount++;
      Write("[Fault] PATTERN COMPLETE at %d ms (no response within 500ms)", now);
      Write("[Fault] Pattern #%d detected", gFaultCount);
      
      gFaultPatternActive = 0;
    }
  }
}

on start {
  SetTimer(gFaultCheckTimer, 100);  // Check fault pattern every 100ms
  Write("Pattern detector started");
  Write("Monitoring: Startup, Shutdown, Fault patterns");
}

on stop {
  CancelTimer(gStartupTimeoutTimer);
  CancelTimer(gFaultCheckTimer);
}

// Display pattern statistics (press 'P')
on key 'P' {
  Write("");
  Write("===== Pattern Detection Statistics =====");
  Write("Startup patterns detected: %d", gStartupCount);
  Write("Shutdown patterns detected: %d", gShutdownCount);
  Write("Fault patterns detected: %d", gFaultCount);
  Write("");
  Write("Current active patterns:");
  Write("  Startup state: %d", gStartupState);
  Write("  Shutdown state: %d", gShutdownState);
  Write("  Fault pattern active: %d", gFaultPatternActive);
  Write("=========================================");
}
```

**Evaluation Criteria:**
- ✅ Accurate pattern detection
- ✅ Correct timing validation
- ✅ State management
- ✅ No false positives
- ✅ Efficient implementation
- ✅ Comprehensive logging

---

## 🟣 **Interview Scenario 9: Dynamic Message Configuration & Control**

**Difficulty:** ⭐⭐⭐⭐ (Advanced) | **Category:** Dynamic Configuration | **Time:** 25-30 min

**Real-World Context:**
You're building a flexible CAN test tool where users can:
- Define message expectations dynamically
- Set upper/lower limits for each data byte
- Configure timeout expectations
- Monitor multiple messages simultaneously
- Alert when messages exceed limits

**Runtime Configuration (via keyboard):**
- 'A`: Add message to monitor: `AddMonitor(ID, timeout, byte0_min, byte0_max, ...)`
- 'R': Remove message from monitor: `RemoveMonitor(ID)`
- 'S': Show all monitored messages and limits
- 'C': Clear all monitors

**Example:**
- Monitor 0x100 with timeout 100ms, byte0 range 0-200, byte1 range 0-100
- Monitor 0x200 with timeout 150ms, byte0 range 0-255, byte1 range 10-50

**Requirements:**
1. Create dynamic monitoring list
2. For each monitored message:
   - Validate against configured limits
   - Check timeout
   - Alert on violations
3. Support adding/removing monitors at runtime
4. Track violations per message
5. Display comprehensive status

**Your Code:**
```capl
// Monitor configuration structure
struct MonitorConfig {
  int ID;
  int timeout_ms;
  byte minValues[8];
  byte maxValues[8];
  int isActive;
  dword lastMessageTime;
  int messageCount;
  int violationCount;
};

#define MAX_MONITORS 20
MonitorConfig gMonitors[MAX_MONITORS];
int gMonitorCount = 0;

// Find monitor by ID
int FindMonitorByID(int ID) {
  for (int i = 0; i < gMonitorCount; i++) {
    if (gMonitors[i].ID == ID && gMonitors[i].isActive) {
      return i;
    }
  }
  return -1;  // Not found
}

// Add message to monitor list
int AddMonitor(int ID, int timeout, byte mins[], byte maxs[]) {
  if (gMonitorCount >= MAX_MONITORS) {
    Write("Error: Monitor list full (max %d)", MAX_MONITORS);
    return 0;
  }
  
  // Check if already monitoring this ID
  if (FindMonitorByID(ID) >= 0) {
    Write("Error: Already monitoring message 0x%03X", ID);
    return 0;
  }
  
  // Create new monitor entry
  MonitorConfig *monitor = &gMonitors[gMonitorCount];
  monitor->ID = ID;
  monitor->timeout_ms = timeout;
  monitor->isActive = 1;
  monitor->lastMessageTime = GetTime();
  monitor->messageCount = 0;
  monitor->violationCount = 0;
  
  // Copy limit values
  for (int i = 0; i < 8; i++) {
    monitor->minValues[i] = mins[i];
    monitor->maxValues[i] = maxs[i];
  }
  
  gMonitorCount++;
  
  Write("Added monitor for 0x%03X (timeout: %d ms)", ID, timeout);
  return 1;  // Success
}

// Remove message from monitor list
int RemoveMonitor(int ID) {
  int index = FindMonitorByID(ID);
  
  if (index < 0) {
    Write("Error: Not monitoring message 0x%03X", ID);
    return 0;
  }
  
  // Mark as inactive (don't remove. to avoid reindexing)
  gMonitors[index].isActive = 0;
  
  Write("Removed monitor for 0x%03X", ID);
  return 1;  // Success
}

// Validate message against monitor limits
int ValidateMessage(Message msg) {
  int monitorIndex = FindMonitorByID(msg.ID);
  
  if (monitorIndex < 0) {
    return 1;  // Not being monitored (valid by default)
  }
  
  MonitorConfig *monitor = &gMonitors[monitorIndex];
  
  // Update message tracking
  monitor->lastMessageTime = GetTime();
  monitor->messageCount++;
  
  // Check DLC
  if (msg.DLC < 1) {
    Write("[0x%03X] Violation: Invalid DLC %d", msg.ID, msg.DLC);
    monitor->violationCount++;
    return 0;
  }
  
  // Check value ranges
  for (int i = 0; i < msg.DLC && i < 8; i++) {
    byte value = msg.Data[i];
    byte minVal = monitor->minValues[i];
    byte maxVal = monitor->maxValues[i];
    
    if (value < minVal || value > maxVal) {
      Write("[0x%03X] Violation: Data[%d]=0x%02X out of range [0x%02X-0x%02X]",
            msg.ID, i, value, minVal, maxVal);
      monitor->violationCount++;
      return 0;  // Violation
    }
  }
  
  return 1;  // Valid
}

// Generic message handler for all monitored IDs
on message * {
  // Only validate if we're monitoring something
  if (gMonitorCount > 0) {
    ValidateMessage(this);
  }
}

// Show monitor status (press 'S')
on key 'S' {
  Write("");
  Write("===== Active Monitors =====");
  
  if (gMonitorCount == 0) {
    Write("No monitors configured");
  } else {
    Write("ID    | Timeout | Messages | Violations | Limits");
    Write("----|---------|----------|------------|--------");
    
    for (int i = 0; i < gMonitorCount; i++) {
      if (gMonitors[i].isActive) {
        MonitorConfig *mon = &gMonitors[i];
        Write("0x%03X | %d ms    | %d       | %d         | [0x%02X-0x%02X]",
              mon->ID, mon->timeout_ms, mon->messageCount, mon->violationCount,
              mon->minValues[0], mon->maxValues[0]);
      }
    }
  }
  
  Write("=========================");
}

// Configure monitors via keyboard
int gConfigMode = 0;
int gTempID = 0;
int gTempTimeout = 0;

// Add monitor interactively (press 'A')
on key 'A' {
  // Example: Monitor 0x100 with timeout 100ms, byte limits
  byte mins[8] = {0, 0, 0, 0, 0, 0, 0, 0};
  byte maxs[8] = {255, 255, 255, 255, 255, 255, 255, 255};
  
  AddMonitor(0x100, 100, mins, maxs);
}

// Add second monitor (press 'B')
on key 'B' {
  byte mins[8] = {0, 0, 0, 0, 0, 0, 0, 0};
  byte maxs[8] = {100, 50, 255, 100, 255, 255, 255, 255};
  
  AddMonitor(0x200, 150, mins, maxs);
}

// Remove monitor (press 'R')
on key 'R' {
  RemoveMonitor(0x100);
}

// Clear all monitors (press 'C')
on key 'C' {
  for (int i = 0; i < gMonitorCount; i++) {
    if (gMonitors[i].isActive) {
      gMonitors[i].isActive = 0;
    }
  }
  gMonitorCount = 0;
  Write("All monitors cleared");
}

// Show help (press 'H')
on key 'H' {
  Write("");
  Write("===== Monitor Commands =====");
  Write("A - Add monitor for 0x100");
  Write("B - Add monitor for 0x200");
  Write("R - Remove 0x100 monitor");
  Write("C - Clear all monitors");
  Write("S - Show monitor status");
  Write("H - Show this help");
  Write("===========================");
}

on start {
  Write("Dynamic message monitor started");
  Write("Use keyboard to configure monitors");
  Write("Press 'H' for help");
}
```

**Evaluation Criteria:**
- ✅ Dynamic data structure management
- ✅ Runtime configuration
- ✅ Proper limit checking
- ✅ Timeout validation
- ✅ No memory leaks
- ✅ Clear user interface via keyboard

---

## 🔴 **Interview Scenario 10: Multi-Module Test Coordinator**

**Difficulty:** ⭐⭐⭐⭐⭐ (Expert) | **Category:** Complex Systems | **Time:** 30-45 min

**Real-World Context:**
You're developing a comprehensive test coordinator that manages testing of 3 modules simultaneously:
- **Module A (Engine)**: Message 0x100, expects response within 500ms
- **Module B (Transmission)**: Message 0x200, expects response within 400ms
- **Module C (Chassis)**: Message 0x300, expects response within 600ms

Test sequence:
1. Send test command to all 3 modules simultaneously
2. Wait for all responses
3. Validate all responses received within timeout
4. If one fails, mark as failed and continue
5. After 5 failed modules total, STOP test
6. Report overall test result (PASS/FAIL)
7. Collect statistics: response times, failure types, success rate

**Requirements:**
1. Send synchronized commands to 3 modules
2. Track response status for each module
3. Implement module-specific timeouts
4. Failure counting and stop condition
5. Response time measurement
6. Comprehensive statistics and logging
7. Keyboard controls:
   - 'S': Start test sequence
   - 'R': Reset statistics
   - 'P': Print report

**Your Code:**
```capl
// Test sequence states
#define TEST_IDLE 0
#define TEST_SENDING 1
#define TEST_WAITING 2
#define TEST_DONE 3

// Module IDs and timeouts
#define ENGINE_ID 0x100
#define TRANS_ID 0x200
#define CHASSIS_ID 0x300
#define ENGINE_TIMEOUT 500
#define TRANS_TIMEOUT 400
#define CHASSIS_TIMEOUT 600

// Module response tracking
struct ModuleTest {
  int ID;
  int timeout;
  int responseReceived;
  dword sendTime;
  int responseTime;  // Response time in ms
  int status;        // 0=pending, 1=pass, -1=fail
};

ModuleTest gModules[3];
int gCurrentTestState = TEST_IDLE;
int gTestNumber = 0;
int gTotalTests = 0;
int gPassedTests = 0;
int gFailedTests = 0;
int gFailedModuleCount = 0;  // Count failures to stop at threshold

timer gTestTimeoutTimer;

// Initialize modules
void InitializeModules() {
  gModules[0].ID = ENGINE_ID;
  gModules[0].timeout = ENGINE_TIMEOUT;
  gModules[1].ID = TRANS_ID;
  gModules[1].timeout = TRANS_TIMEOUT;
  gModules[2].ID = CHASSIS_ID;
  gModules[2].timeout = CHASSIS_TIMEOUT;
}

// Send test command to all modules synchronously
void SendTestCommands() {
  dword now = GetTime();
  
  for (int i = 0; i < 3; i++) {
    Message msg;
    msg.ID = gModules[i].ID;
    msg.DLC = 8;
    msg.Data[0] = 0x01;  // Test command
    msg.Data[1] = (gTestNumber >> 8) & 0xFF;
    msg.Data[2] = gTestNumber & 0xFF;
    msg.Data[3] = 0x00;
    msg.Data[4] = 0x00;
    msg.Data[5] = 0x00;
    msg.Data[6] = 0x00;
    
    // Calculate checksum
    byte sum = 0;
    for (int j = 0; j < 7; j++) sum += msg.Data[j];
    msg.Data[7] = (~sum) + 1;
    
    Send(msg);
    gModules[i].responseReceived = 0;
    gModules[i].status = 0;  // Pending
    gModules[i].sendTime = now;
    
    Write("[Test %d] Sent to module 0x%03X", gTestNumber, gModules[i].ID);
  }
  
  // Set maximum timeout (longest module timeout)
  SetTimer(gTestTimeoutTimer, 700);
}

// Wait for responses from all modules
int WaitForAllResponses() {
  int allReceived = 1;
  
  for (int i = 0; i < 3; i++) {
    if (!gModules[i].responseReceived) {
      allReceived = 0;
      break;
    }
  }
  
  return allReceived;
}

// Validate responses
int ValidateResponses() {
  int testPass = 1;
  dword now = GetTime();
  
  for (int i = 0; i < 3; i++) {
    gModules[i].responseTime = now - gModules[i].sendTime;
    
    if (gModules[i].responseReceived) {
      // Check if response within timeout
      if (gModules[i].responseTime <= gModules[i].timeout) {
        gModules[i].status = 1;  // Pass
        Write("  Module 0x%03X: PASS (%d ms)", gModules[i].ID, gModules[i].responseTime);
      } else {
        gModules[i].status = -1;  // Fail - timeout
        testPass = 0;
        gFailedModuleCount++;
        Write("  Module 0x%03X: FAIL - Response time %d ms exceeds timeout %d ms",
              gModules[i].ID, gModules[i].responseTime, gModules[i].timeout);
      }
    } else {
      gModules[i].status = -1;  // Fail - no response
      testPass = 0;
      gFailedModuleCount++;
      Write("  Module 0x%03X: FAIL - No response", gModules[i].ID);
    }
  }
  
  return testPass;
}

// Generate test report
void GenerateReport() {
  Write("");
  Write("===== Test Report =====");
  Write("Total tests: %d", gTotalTests);
  Write("Passed: %d", gPassedTests);
  Write("Failed: %d", gFailedTests);
  Write("Success rate: %d%%", gTotalTests > 0 ? (gPassedTests * 100) / gTotalTests : 0);
  Write("Failed modules total: %d", gFailedModuleCount);
  
  Write("");
  Write("Module statistics:");
  for (int i = 0; i < 3; i++) {
    Write("  0x%03X: Response time avg (last test: %d ms)", 
          gModules[i].ID, gModules[i].responseTime);
  }
  Write("=======================");
}

// Recovery action when module fails
void RecoveryAction(int moduleIndex) {
  Write("[Recovery] Attempting recovery for module 0x%03X", gModules[moduleIndex].ID);
  
  // Send recovery/reset command
  Message recMsg;
  recMsg.ID = gModules[moduleIndex].ID;
  recMsg.DLC = 8;
  recMsg.Data[0] = 0xFF;  // Reset command
  
  Send(recMsg);
  
  Write("[Recovery] Reset command sent to module 0x%03X", gModules[moduleIndex].ID);
}

// Timeout handler
on timer gTestTimeoutTimer {
  if (gCurrentTestState == TEST_WAITING) {
    gCurrentTestState = TEST_DONE;
    ValidateResponses();
    
    // Check if we exceeded failure threshold (5 total failures)
    if (gFailedModuleCount >= 5) {
      Write("\n!!! STOPPING TEST: Too many failures (%d/5) !!!", gFailedModuleCount);
      gCurrentTestState = TEST_IDLE;
    } else {
      Write("Ready for next test (Press 'R' to continue)");
    }
  }
}

// Engine response
on message Engine.Response {
  if (gCurrentTestState == TEST_WAITING) {
    int index = 0;  // Engine is index 0
    gModules[index].responseReceived = 1;
    
    Write("Response from engine 0x%03X received", this.ID);
  }
}

// Transmission response
on message Transmission.Response {
  if (gCurrentTestState == TEST_WAITING) {
    int index = 1;  // Transmission is index 1
    gModules[index].responseReceived = 1;
    
    Write("Response from transmission 0x%03X received", this.ID);
  }
}

// Chassis response
on message Chassis.Response {
  if (gCurrentTestState == TEST_WAITING) {
    int index = 2;  // Chassis is index 2
    gModules[index].responseReceived = 1;
    
    Write("Response from chassis 0x%03X received", this.ID);
  }
}

// Generic response handlers
on message 0x101 {  // Engine response
  if (gCurrentTestState == TEST_WAITING) {
    gModules[0].responseReceived = 1;
    Write("Response from engine received");
  }
}

on message 0x201 {  // Transmission response
  if (gCurrentTestState == TEST_WAITING) {
    gModules[1].responseReceived = 1;
    Write("Response from transmission received");
  }
}

on message 0x301 {  // Chassis response
  if (gCurrentTestState == TEST_WAITING) {
    gModules[2].responseReceived = 1;
    Write("Response from chassis received");
  }
}

// Start test sequence (press 'S')
on key 'S' {
  if (gCurrentTestState != TEST_IDLE) {
    Write("Test already in progress");
    return;
  }
  
  gTestNumber++;
  gCurrentTestState = TEST_SENDING;
  gTotalTests++;
  
  Write("\n===== Starting Test %d =====", gTestNumber);
  SendTestCommands();
  
  gCurrentTestState = TEST_WAITING;
}

// Next test (press 'N' or 'R')
on key 'N' {
  if (gCurrentTestState == TEST_DONE || gCurrentTestState == TEST_IDLE) {
    // Check failure threshold
    if (gFailedModuleCount >= 5) {
      Write("Test stopped: Failure threshold exceeded");
      return;
    }
    
    // Get test result from last test
    if (ValidateResponses()) {
      gPassedTests++;
    } else {
      gFailedTests++;
    }
    
    gCurrentTestState = TEST_IDLE;
    Write("Press 'S' to start next test");
  }
}

// Print report (press 'P')
on key 'P' {
  GenerateReport();
}

on start {
  InitializeModules();
  Write("Test Coordinator started");
  Write("Commands: S=Start test, N=Next test, P=Print report");
}

on stop {
  CancelTimer(gTestTimeoutTimer);
}
```

**Advanced Requirements:**
- Handle case where responses arrive in wrong order
- Implement pipelined testing (test 2 starts before test 1 completes)
- Track response time statistics (min, max, average)
- Detect partial failures (1-2 modules fail per test)

**Evaluation Criteria:**
- ✅ Complex state coordination
- ✅ Multiple concurrent operations
- ✅ Module-specific timeout handling
- ✅ Statistics tracking and reporting
- ✅ Error recovery mechanism
- ✅ Robust failure detection
- ✅ Clean architecture despite complexity
- ✅ Comprehensive logging

---

## 🟡 **Interview Scenario 11: Protocol Implementation - Request/Response/ACK**

**Difficulty:** ⭐⭐⭐⭐ (Advanced) | **Category:** Protocol Design | **Time:** 25-30 min

**Real-World Context:**
You're implementing a three-tier communication protocol:
1. **Request** (Master → Slave): ID 0x700, expects immediate ACK
2. **ACK** (Slave → Master): ID 0x701, response to request
3. **Response** (Slave → Master): ID 0x702, actual data (up to 100ms after request)

Timeout strategy:
- ACK must arrive within 50ms of request
- Response must arrive within 100ms of request
- If ACK not received, no need to wait for response (error)
- If Response not received (but ACK was), log as timeout

Retry strategy:
- If ACK timeout: retry up to 3 times with 200ms between retries
- If Response timeout: don't retry, move to next command
- If 3 consecutive ACK failures: stop communication

**Message formats:**
- **Request (0x700)**: {0x01, RequestID, Param1, Param2, ...}
- **ACK (0x701)**: {RequestID, 0x00, ...}
- **Response (0x702)**: {RequestID, 0x01, ResponseData...}

**Requirements:**
1. Send commands with proper request format
2. Wait for ACK with 50ms timeout
3. If ACK received, wait for response with 100ms timeout
4. Implement retry mechanism
5. Track consecutive failures
6. Stop communication after 3 consecutive failures
7. Log all protocol events (request, ACK, response, timeouts, retries)

**Your Code:**
```capl
// Protocol states
#define STATE_IDLE 0
#define STATE_WAIT_ACK 1
#define STATE_WAIT_RESPONSE 2
#define STATE_RETRY 3
#define STATE_ERROR 4

// Message IDs
#define REQUEST_ID 0x700
#define ACK_ID 0x701
#define RESPONSE_ID 0x702

// Timing
#define ACK_TIMEOUT 50      // ms
#define RESPONSE_TIMEOUT 100  // ms
#define RETRY_DELAY 200     // ms
#define MAX_CONSECUTIVE_FAILURES 3

// Protocol state
int gProtocolState = STATE_IDLE;
int gCurrentRequestID = 0;
int gRetryCount = 0;
int gConsecutiveFailures = 0;
dword gRequestStartTime = 0;

// Statistics
int gTotalRequests = 0;
int gSuccessfulRequests = 0;
int gFailedRequests = 0;
int gACKTimeouts = 0;
int gResponseTimeouts = 0;
int gRetries = 0;

// Timers
timer gACKTimer;
timer gResponseTimer;
timer gRetryTimer;

// Log protocol event
void LogProtocolEvent(char *description) {
  dword elapsed = GetTime() - gRequestStartTime;
  Write("[%d ms] %s", elapsed, description);
}

// Send request
void SendRequest(byte requestID, byte param1, byte param2) {
  if (gProtocolState != STATE_IDLE) {
    Write("Error: Protocol not idle (state: %d)", gProtocolState);
    return;
  }
  
  Message req;
  req.ID = REQUEST_ID;
  req.DLC = 3;
  req.Data[0] = requestID;
  req.Data[1] = param1;
  req.Data[2] = param2;
  
  Send(req);
  
  gCurrentRequestID = requestID;
  gProtocolState = STATE_WAIT_ACK;
  gRequestStartTime = GetTime();
  gTotalRequests++;
  gRetryCount = 0;
  
  LogProtocolEvent("Sent request, waiting for ACK...");
  
  // Start ACK timeout timer
  SetTimer(gACKTimer, ACK_TIMEOUT);
}

// Handle ACK timeout
void HandleACKTimeout() {
  CancelTimer(gACKTimer);
  gACKTimeouts++;
  gRetryCount++;
  
  LogProtocolEvent("ACK timeout!");
  
  if (gRetryCount >= MAX_CONSECUTIVE_FAILURES) {
    // Too many failures - stop
    Write("Fatal: %d consecutive ACK timeouts - stopping communication", 
          MAX_CONSECUTIVE_FAILURES);
    gProtocolState = STATE_ERROR;
    gConsecutiveFailures++;
    gFailedRequests++;
    
    if (gConsecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      Write("\nCritical: Halting protocol after %d failures", MAX_CONSECUTIVE_FAILURES);
      return;
    }
  } else {
    // Retry
    gProtocolState = STATE_RETRY;
    gRetries++;
    LogProtocolEvent("Retrying request...");
    SetTimer(gRetryTimer, RETRY_DELAY);
  }
}

// Handle response timeout
void HandleResponseTimeout() {
  CancelTimer(gResponseTimer);
  gResponseTimeouts++;
  
  LogProtocolEvent("Response timeout!");
  
  // No retry for response timeout (ACK was received)
  gProtocolState = STATE_IDLE;
  gFailedRequests++;
  gConsecutiveFailures++;
  
  Write("Request failed: Response not received");
}

// Recover from failure
void RecoverFromFailure() {
  LogProtocolEvent("Recovering...");
  
  // Send reset command
  Message resetMsg;
  resetMsg.ID = REQUEST_ID;
  resetMsg.DLC = 1;
  resetMsg.Data[0] = 0x00;  // Reset command
  
  Send(resetMsg);
  
  gProtocolState = STATE_IDLE;
  Write("Protocol reset sent");
}

// ACK timeout handler
on timer gACKTimer {
  HandleACKTimeout();
}

// Response timeout handler
on timer gResponseTimer {
  HandleResponseTimeout();
}

// Retry timer handler
on timer gRetryTimer {
  if (gProtocolState == STATE_RETRY) {
    LogProtocolEvent("Resending request (attempt %d)", gRetryCount);
    
    Message req;
    req.ID = REQUEST_ID;
    req.DLC = 3;
    req.Data[0] = gCurrentRequestID;
    req.Data[1] = 0x00;
    req.Data[2] = 0x00;
    
    Send(req);
    
    gProtocolState = STATE_WAIT_ACK;
    SetTimer(gACKTimer, ACK_TIMEOUT);
  }
}

// ACK message handler
on message ACK_ID {
  if (gProtocolState != STATE_WAIT_ACK) {
    Write("Warning: Unexpected ACK in state %d", gProtocolState);
    return;
  }
  
  // Validate ACK
  if (this.DLC < 2 || this.Data[0] != gCurrentRequestID) {
    Write("Error: Invalid ACK");
    HandleACKTimeout();
    return;
  }
  
  // ACK received successfully
  CancelTimer(gACKTimer);
  gConsecutiveFailures = 0;  // Reset failure counter
  
  dword ackTime = GetTime() - gRequestStartTime;
  LogProtocolEvent("ACK received (%d ms)", ackTime);
  
  gProtocolState = STATE_WAIT_RESPONSE;
  SetTimer(gResponseTimer, RESPONSE_TIMEOUT);
}

// Response message handler
on message RESPONSE_ID {
  if (gProtocolState != STATE_WAIT_RESPONSE) {
    Write("Warning: Unexpected response in state %d", gProtocolState);
    return;
  }
  
  // Validate response
  if (this.DLC < 2 || this.Data[0] != gCurrentRequestID) {
    Write("Error: Invalid response");
    HandleResponseTimeout();
    return;
  }
  
  // Response received successfully
  CancelTimer(gResponseTimer);
  
  dword responseTime = GetTime() - gRequestStartTime;
  LogProtocolEvent("Response received (%d ms)", responseTime);
  
  // Extract response data
  byte responseData = this.Data[1];
  Write("Response data: 0x%02X", responseData);
  
  gProtocolState = STATE_IDLE;
  gSuccessfulRequests++;
  gConsecutiveFailures = 0;  // Reset failure counter
  
  Write("Request complete - Ready for next request");
}

// Test protocol (press 'T')
on key 'T' {
  if (gProtocolState == STATE_IDLE) {
    Write("\n===== Sending Test Request =====");
    SendRequest(0x01, 0x10, 0x20);
  } else {
    Write("Protocol busy (state: %d)", gProtocolState);
  }
}

// Show statistics (press 'S')
on key 'S' {
  Write("");
  Write("===== Protocol Statistics =====");
  Write("Total requests: %d", gTotalRequests);
  Write("Successful: %d", gSuccessfulRequests);
  Write("Failed: %d", gFailedRequests);
  Write("ACK timeouts: %d", gACKTimeouts);
  Write("Response timeouts: %d", gResponseTimeouts);
  Write("Retries: %d", gRetries);
  Write("Consecutive failures: %d", gConsecutiveFailures);
  Write("Current state: %d", gProtocolState);
  
  if (gTotalRequests > 0) {
    int successRate = (gSuccessfulRequests * 100) / gTotalRequests;
    Write("Success rate: %d%%", successRate);
  }
  Write("==============================");
}

on start {
  Write("Protocol handler started");
  Write("Protocol: Request -> ACK -> Response");
  Write("Press 'T' to test, 'S' for stats");
}

on stop {
  CancelTimer(gACKTimer);
  CancelTimer(gResponseTimer);
  CancelTimer(gRetryTimer);
}
```

**Evaluation Criteria:**
- ✅ Proper timeout implementation (separate for ACK and Response)
- ✅ Correct retry logic
- ✅ Failure tracking
- ✅ Appropriate stop conditions
- ✅ Detailed protocol logging
- ✅ Robust message validation

---

## 🟠 **Interview Scenario 12: Performance Optimization Challenge**

**Difficulty:** ⭐⭐⭐⭐⭐ (Expert) | **Category:** Performance & Analysis | **Time:** 30-45 min

**Real-World Context:**
You have a baseline CAPL script that monitors 100 CAN messages and performs validation on each. However, the script is running slowly and causing CANoe to lag. You need to optimize it.

**Current Issues:**
- Processing every message in on message *
- Running validation on all 100 possible IDs
- Performing string formatting in every message handler
- Excessive logging (prints trace for every message)
- Memory inefficiency (storing redundant data)

**Requirements:**
1. Profile and identify bottlenecks
2. Implement filtering (only process relevant messages)
3. Optimize validation logic
4. Reduce logging overhead
5. Improve memory usage
6. Maintain all error detection

**Challenge Questions:**
- How would you filter messages before processing?
- What validation checks could be moved to less-critical code paths?
- How would you reduce logging without losing visibility?
- What data structures are most memory efficient?
- How would you measure performance improvement?

**Your Analysis & Code:**
```capl
// ========== BOTTLENECK ANALYSIS ==========
// 
// ISSUES IN BASELINE:
// 1. Processing every message in on message * (100 IDs, most irrelevant)
// 2. Running full validation on all 100 IDs every time
// 3. String formatting in every handler (sprintf is slow)
// 4. Excessive trace output (kills CANoe performance)
// 5. No filtering - processes messages that don't matter
// 
// OPTIMIZATION STRATEGY:
// 1. Filter by ID before processing (skip irrelevant messages)
// 2. Use static lookup table for ID validation
// 3. Defer detailed logging (batch or on-demand)
// 4. Minimize string operations
// 5. Use bitwise operations instead of string checks

// ========== OPTIMIZED CODE ==========

// Configuration: Which message IDs to monitor (use array for fast lookup)
int gMonitoredIDs[] = { 0x100, 0x200, 0x300, 0x400, 0x500 };  // Only 5 important IDs
#define MONITORED_COUNT 5

// Fast ID lookup using binary search optimization
int IsMonitoredID(int ID) {
  for (int i = 0; i < MONITORED_COUNT; i++) {
    if (gMonitoredIDs[i] == ID) {
      return 1;
    }
  }
  return 0;
}

// Additional helper for syntax highlighting

// Validation ranges (stored, not computed)
struct IDConfig {
  int id;
  byte minVal;
  byte maxVal;
  int enabled;
};

IDConfig gValidationRules[] = {
  {0x100, 0, 255, 1},
  {0x200, 0, 100, 1},
  {0x300, -40, 125, 1},
  {0x400, 0, 255, 1},
  {0x500, 0, 255, 1}
};

// Message counters (avoid repeated counting)
int gValidMessages = 0;
int gInvalidMessages = 0;

// OPTIMIZATION 1: Filter at entry point (only process relevant messages)
on message * {
  // FAST: Single check before any processing
  if (!IsMonitoredID(this.ID)) {
    return;  // Exit immediately for non-monitored messages
  }
  
  // OPTIMIZATION 2: Direct validation without heavy operations
  ValidateMessageOptimized(this);
}

// OPTIMIZATION 3: Inline validation without string formatting
void ValidateMessageOptimized(Message msg) {
  // Check DLC first (cheapest check)
  if (msg.DLC < 1) {
    gInvalidMessages++;
    // Don't format string here - use error counters instead
    return;
  }
  
  // Quick byte range check
  byte val = msg.Data[0];
  if (val < 0 || val > 255) {
    gInvalidMessages++;
    return;
  }
  
  gValidMessages++;
  // Increment counter instead of formatting
}

// OPTIMIZATION 4: Deferred detailed logging (only on demand)
int gDetailedLoggingEnabled = 0;  // Control via keyboard

void ConditionalLog(char *message) {
  // Skip expensive Trace() when not needed
  if (gDetailedLoggingEnabled) {
    Write("%s", message);
  }
}

// OPTIMIZATION 5: Batch statistics instead of per-message output
timer gStatisticsTimer;

on timer gStatisticsTimer {
  // Report statistics periodically (every 1 second)
  // Instead of per-message output
  int total = gValidMessages + gInvalidMessages;
  
  if (total > 0) {
    int percentage = (gValidMessages * 100) / total;
    Write("Valid: %d, Invalid: %d, Rate: %d%%", 
          gValidMessages, gInvalidMessages, percentage);
  }
}

// OPTIMIZATION 6: Use bitwise operations instead of arithmetic
int FastCalculateChecksum(byte data[], int DLC) {
  // Bitwise XOR is faster than arithmetic sum
  byte checksum = 0;
  for (int i = 0; i < DLC - 1; i++) {
    checksum ^= data[i];  // XOR instead of ADD
  }
  return checksum;
}

// OPTIMIZATION 7: Static data - avoid dynamic allocation
// Already done: gMonitoredIDs[], gValidationRules[] are static

// OPTIMIZATION 8: Reduce array lookups
int FindValidationRule(int ID) {
  // Cache common IDs (most used first)
  if (ID == 0x100) return 0;
  if (ID == 0x200) return 1;
  if (ID == 0x300) return 2;
  
  // Fallback to search
  for (int i = 0; i < 5; i++) {
    if (gValidationRules[i].id == ID) {
      return i;
    }
  }
  return -1;
}

// OPTIMIZATION 9: Avoid repeated condition checks
void ProcessWithMinimalChecks(Message msg) {
  // Single validation path
  if (msg.DLC >= 1 && msg.Data[0] >= 0 && msg.Data[0] <= 255) {
    gValidMessages++;
  } else {
    gInvalidMessages++;
  }
}

// OPTIMIZATION 10: Enable/disable detailed logging
void ToggleDetailedLogging() {
  gDetailedLoggingEnabled = !gDetailedLoggingEnabled;
  
  if (gDetailedLoggingEnabled) {
    Write("Detailed logging ENABLED (impacts performance)");
    CancelTimer(gStatisticsTimer);
  } else {
    Write("Detailed logging DISABLED (optimized)");
    SetTimer(gStatisticsTimer, 1000);  // Batch every 1 sec
  }
}

on key 'D' {
  ToggleDetailedLogging();
}

// Display optimization status
on key 'O' {
  Write("");
  Write("===== Performance Optimization Status =====");
  Write("Monitored IDs: %d (out of 100s possible)", MONITORED_COUNT);
  Write("Filtering: ENABLED (fast ID check)");
  Write("String formatting: MINIMIZED (batch mode)");
  Write("Detailed logging: %s", gDetailedLoggingEnabled ? "ON" : "OFF");
  Write("Statistics reporting: Every 1 second");
  Write("==== Improvements ====");
  Write("1. ID filtering (eliminates 95%+ of processing)");
  Write("2. No expensive sprintf() per message");
  Write("3. Batch statistics (1 output/sec vs many)");
  Write("4. Early exit for non-monitored IDs");
  Write("5. Inline validation (no function call overhead)");
  Write("================================================")
}

on start {
  // Start batch statistics timer
  SetTimer(gStatisticsTimer, 1000);
  Write("Optimized message processor started");
}

on stop {
  CancelTimer(gStatisticsTimer);
}

// ========== BENCHMARKING METHODOLOGY ==========
//
// MEASUREMENT APPROACH:
// 1. CPU Load: Use CANoe's built-in CPU profiler
//    - Baseline: Record CPU% with original code
//    - Optimized: Record CPU% with optimized code
//    - Target: 50%+ reduction
//
// 2. Message Latency: Measure time from CAN RX to processing
//    dword startTime = GetTime();
//    ProcessMessage();
//    gLatency = GetTime() - startTime;
//
// 3. Trace Output: Count lines per second
//    - Baseline: Many per message
//    - Optimized: Few (batch)
//
// 4. Real test: Send 100 msg/sec of relevant + 1000 msg/sec noise
//    - Baseline will struggle/lag
//    - Optimized will handle smoothly
//
// 5. CANoe Responsiveness:
//    - Can you interact with CANoe GUI without lag?
//    - Before optimization: Likely slow
//    - After optimization: Smooth
```

**Evaluation Criteria:**
- ✅ Correct identification of bottlenecks
- ✅ Practical optimization techniques
- ✅ Maintained functionality
- ✅ Measurable performance gains
- ✅ Code clarity (optimization shouldn't reduce readability significantly)
- ✅ Memory efficiency
- ✅ Professional approach to profiling

---

## **Answer Submission Format**

For each scenario, provide:

### **Scenario [Number]: [Name]**

**Your Code:**
```capl
// Paste complete working code here
```

**Explanation:**
- Key design decisions
- Error handling approach
- Validation strategy
- Performance considerations

**Testing:**
- How would you test this code?
- What edge cases would you check?
- What could go wrong?

**Improvements:**
- Any limitations?
- How could it be enhanced?
- Production-ready? Why/why not?

---

## **Evaluation Rubric**

| Criterion | Poor | Good | Excellent |
|-----------|------|------|-----------|
| **Correctness** | Code doesn't work | Works for basic cases | Handles all cases & edge cases |
| **Error Handling** | No error checking | Basic validation | Comprehensive validation with recovery |
| **Code Quality** | Messy, unreadable | Readable, organized | Clean, self-documenting |
| **Performance** | Inefficient, causes lag | Acceptable | Optimized, resource efficient |
| **Comments** | None or insufficient | Adequate explanations | Clear intent, reasoning documented |
| **Completeness** | Missing requirements | All requirements met | Exceeds requirements |

---

## **Interview Tips**

1. **Ask Questions**: Clarify ambiguous requirements
2. **Show Your Work**: Explain your reasoning
3. **Handle Edge Cases**: Think about boundary conditions
4. **Test Thoughtfully**: Consider how you'd verify your solution
5. **Code Professionally**: Use meaningful names, organize logically
6. **Document Decisions**: Comment why, not just what
7. **Consider Performance**: Think about resource usage
8. **Validate Early**: Check inputs before processing

---

## **Pro Tips for Success**

✅ Always validate message DLC before accessing bytes
✅ Use meaningful variable names (gMessageCount not cnt)
✅ Initialize global variables to known values
✅ Cancel timers in cleanup (on stop)
✅ Use constants for magic numbers (#define TIMEOUT 5000)
✅ Log failures with context (not just "Error!")
✅ Test with boundary values (0, max, negative if applicable)
✅ Comment complex logic explaining the "why"
✅ Use state machines for complex flows
✅ Implement rate limiting for high-frequency operations
✅ Track metrics for debugging (counters, statistics)
✅ Handle the "off by one" errors in arrays/loops

---

**Good luck with your interview! 🚀**

Start with Scenario 1 and work your way up in difficulty. Each scenario tests different CAPL competencies you'd encounter in real automotive testing work.
