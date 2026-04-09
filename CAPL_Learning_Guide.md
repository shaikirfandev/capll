# CAPL Script - Complete Learning Guide

## Table of Contents
1. [Introduction](#introduction)
2. [CAPL Basics](#capl-basics)
3. [Data Types and Variables](#data-types-and-variables)
4. [Operators](#operators)
5. [Control Flow](#control-flow)
6. [Functions](#functions)
7. [Messages and Signals](#messages-and-signals)
8. [Event Handling](#event-handling)
9. [Built-in Functions](#built-in-functions)
10. [Advanced Topics](#advanced-topics)
11. [Best Practices](#best-practices)
12. [Practical Examples](#practical-examples)

---

## Introduction

### What is CAPL?

CAPL (Computer Aided Production Language) is an event-driven scripting language designed for automotive CAN bus testing, simulation, and analysis. It's primarily used in **Vector CANalyzer** and **CANoe** tools.

### Key Characteristics

- **Event-Driven**: CAPL scripts respond to events like message reception, timer expiration, or keyboard input
- **Based on C**: Syntax similar to C language, making it accessible to programmers
- **Message-Oriented**: Designed specifically for handling CAN messages and signals
- **Real-Time**: Suitable for real-time vehicle simulation and testing
- **Integration**: Works seamlessly with CANoe's measurement capabilities

### Applications

- CAN bus network simulation
- ECU behavior testing
- Diagnostic testing
- Network gateways and bridges
- Vehicle bus simulation
- Automated test script generation

---

## CAPL Basics

### File Structure

A basic CAPL script file has this structure:

```capl
// Includes
#include "filename.h"

// Variable declarations
dword globalVariable;

// Function declarations (optional)
void MyFunction();

// Event handlers and function implementations
on start {
  // Initialization code
}

on stop {
  // Cleanup code
}

void MyFunction() {
  // Function body
}
```

### Case Sensitivity

CAPL is **case-sensitive**. `MyVariable` and `myvariable` are different.

### Comments

```capl
// Single line comment

/* Multi-line
   comment */
```

### Code Blocks

Code blocks use curly braces:

```capl
{
  // Code inside block
}
```

---

## Data Types and Variables

### Primitive Data Types

| Type | Size | Range | Example |
|------|------|-------|---------|
| `byte` | 8 bits | 0-255 | `byte value = 100;` |
| `word` | 16 bits | 0-65535 | `word count = 1000;` |
| `dword` | 32 bits | 0-4294967295 | `dword timestamp = 50000;` |
| `int` | 32 bits | -2147483648 to 2147483647 | `int temperature = -5;` |
| `float` | 32 bits | ±3.4E±38 | `float voltage = 12.5;` |
| `double` | 64 bits | ±1.7E±308 | `double precise = 3.14159;` |
| `char` | 8 bits | -128 to 127 | `char letter = 'A';` |

### String Type

```capl
char message[50];  // Character array (string)
message = "Hello, CAPL!";

// String operations
strlen(message);     // Get length
strcpy();           // Copy string
strcat();           // Concatenate strings
```

### Variable Declaration and Initialization

```capl
// Global variable (visible in entire program)
int globalCounter;

// Local variable (visible only in current scope)
void MyFunction() {
  int localCounter = 0;  // Initialized to 0
  float value = 3.14;
}

// Multiple declarations
int a, b, c;
int x = 1, y = 2, z = 3;

// Arrays
byte buffer[8];        // Array of 8 bytes
int matrix[10][10];    // 2D array

// Constants
const int MAX_VALUE = 100;
const float PI = 3.14159;
```

### Variable Scopes

```capl
// Global scope - accessible everywhere
int globalVar;

void Function1() {
  int localVar1;  // Local to Function1
  
  {
    int blockVar;  // Local to this block
  }
  // blockVar not accessible here
}

void Function2() {
  // localVar1 not accessible here
}
```

---

## Operators

### Arithmetic Operators

```capl
int a = 10, b = 3;

int sum = a + b;        // Addition: 13
int diff = a - b;       // Subtraction: 7
int product = a * b;    // Multiplication: 30
int quotient = a / b;   // Division: 3
int remainder = a % b;  // Modulus: 1

// Unary operators
int neg = -a;           // Negation: -10
int inc = ++a;          // Pre-increment
int post = a++;         // Post-increment
```

### Comparison Operators

```capl
if (a == b)  // Equal to
if (a != b)  // Not equal to
if (a > b)   // Greater than
if (a < b)   // Less than
if (a >= b)  // Greater than or equal
if (a <= b)  // Less than or equal
```

### Logical Operators

```capl
if (a > 5 && b < 10)   // AND: both conditions true
if (a > 5 || b > 10)   // OR: at least one true
if (!(a == b))         // NOT: negates condition
```

### Bitwise Operators

```capl
byte a = 0x0F, b = 0xF0;

byte andResult = a & b;    // AND: 0x00
byte orResult = a | b;     // OR:  0xFF
byte xorResult = a ^ b;    // XOR: 0xFF
byte notResult = ~a;       // NOT: 0xF0
byte leftShift = a << 2;   // Left shift by 2
byte rightShift = a >> 2;  // Right shift by 2
```

### Assignment Operators

```capl
int x = 10;
x += 5;   // x = x + 5;   → 15
x -= 3;   // x = x - 3;   → 12
x *= 2;   // x = x * 2;   → 24
x /= 4;   // x = x / 4;   → 6
x %= 5;   // x = x % 5;   → 1
x &= 0xFF; // x = x & 0xFF;
```

### Ternary Operator

```capl
int max = (a > b) ? a : b;  // If a > b, max = a, else max = b
```

---

## Control Flow

### If-Else Statements

```capl
int age = 25;

if (age < 13) {
  Write("Child");
} else if (age < 18) {
  Write("Teenager");
} else if (age < 65) {
  Write("Adult");
} else {
  Write("Senior");
}
```

### Switch Statement

```capl
int status = 2;

switch (status) {
  case 0:
    Write("Idle");
    break;
  case 1:
    Write("Running");
    break;
  case 2:
    Write("Error");
    break;
  default:
    Write("Unknown");
    break;
}
```

### While Loop

```capl
int counter = 0;

while (counter < 10) {
  Write("Counter: %d", counter);
  counter++;
}

// Do-while loop (executes at least once)
do {
  Write("This executes at least once");
} while (counter < 0);
```

### For Loop

```capl
// Standard for loop
for (int i = 0; i < 10; i++) {
  Write("Iteration: %d", i);
}

// Multiple increments
for (int i = 0, j = 10; i < 10; i++, j--) {
  Write("i=%d, j=%d", i, j);
}

// Infinite loop (use break to exit)
for (;;) {
  if (someCondition) break;
}
```

### Loop Control

```capl
for (int i = 0; i < 10; i++) {
  if (i == 3) continue;  // Skip to next iteration
  if (i == 7) break;     // Exit loop
  Write("%d", i);
}
```

---

## Functions

### Function Basics

```capl
// Function declaration/definition
return_type FunctionName(parameter_type param1, parameter_type param2) {
  // Function body
  return value;  // If return type is not void
}

// Function with no parameters and no return
void GreetUser() {
  Write("Hello, User!");
}

// Function with return value
int Add(int a, int b) {
  return a + b;
}

// Calling functions
GreetUser();
int result = Add(5, 3);  // result = 8
```

### Function Parameters

```capl
// Pass by value - copy of value is passed
void ModifyByValue(int value) {
  value = 100;  // Original not affected
}

// Arrays are always passed by reference
void FillArray(byte array[], int size) {
  for (int i = 0; i < size; i++) {
    array[i] = i;  // Modifies original array
  }
}

// Usage
byte data[10];
FillArray(data, 10);
```

### Function Prototypes

```capl
// Declare before use (optional but recommended)
int CalculateValue(int input);

// Later in code
int main() {
  int result = CalculateValue(42);
}

// Function definition
int CalculateValue(int input) {
  return input * 2;
}
```

### Recursive Functions

```capl
// Calculate factorial
int Factorial(int n) {
  if (n <= 1)
    return 1;
  else
    return n * Factorial(n - 1);
}

// Calculate Fibonacci
int Fibonacci(int n) {
  if (n <= 1)
    return n;
  else
    return Fibonacci(n - 1) + Fibonacci(n - 2);
}
```

---

## Messages and Signals

### Working with CAN Messages

#### Sending Messages

```capl
// Send a message
void SendMessage() {
  // Method 1: Using specific message object
  Message msg;
  msg.DLC = 8;
  msg.Data[0] = 0x12;
  msg.Data[1] = 0x34;
  // ... set other data bytes
  Send(msg);
}

// Method 2: Sending immediately
void OnButtonClick() {
  byte data[8] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  SendMessage(0x123, 8, data);  // ID, DLC, Data
}
```

#### Receiving Messages

```capl
// Handle all messages
on message * {
  Write("Received ID: 0x%X, DLC: %d", this.ID, this.DLC);
}

// Handle specific message by ID
on message 0x123 {
  Write("Speed message received");
  byte speed = this.Data[0];
  Write("Speed: %d", speed);
}

// Handle message by name (if defined in database)
on message EngineStatus {
  if (EngineStatus.EngineRPM > 5000) {
    Write("Engine overspeed!");
  }
}
```

### Working with Signals

```capl
// Accessing signals in received messages
on message EngineData {
  // Access signal directly by name
  int rpm = EngineData.RPM;
  float temp = EngineData.Temperature;
  
  // Access signal with signal() function
  int speed = signal(EngineData, Speed);
}

// Setting signal values in message
Message msg;
msg.DLC = 8;
msg.RPM = 3000;
msg.Temperature = 85.5;
Send(msg);

// Individual signal writes
void SendEngineStatus() {
  byte msgData[8] = {};
  msgData[0] = 125;  // RPM MSB
  msgData[1] = 200;  // RPM LSB
  msgData[2] = 85;   // Temperature
  
  SendMessage(0x100, 8, msgData);
}
```

### Message Structure

```capl
// Message attributes
on message SystemStatus {
  int id = this.ID;           // Message CAN ID
  int dlc = this.DLC;         // Data Length Code
  dword timestamp = this.Time; // Timestamp
  byte data[8];
  
  // Copy message data
  for (int i = 0; i < dlc; i++) {
    data[i] = this.Data[i];
  }
}
```

---

## Event Handling

### System Events

#### Start Event
```capl
on start {
  Write("Script started");
  // Initialize variables
  // Start timers
  // Send initial messages
}
```

#### Stop Event
```capl
on stop {
  Write("Script stopped");
  // Cleanup code
  // Disable timers
  // Log final values
}
```

#### Key Events
```capl
// Handle keyboard input
on key 'a' {
  Write("Key 'a' pressed");
  SendMessage();
}

on key ' ' {
  Write("Space bar pressed");
}
```

### Timer Events

```capl
// Declare timer
timer MyTimer;
timer StatusCheck;

on start {
  // Start a recurring timer (every 1000ms)
  SetTimer(MyTimer, 1000);
}

// Timer event
on timer MyTimer {
  Write("Timer fired!");
  int count++;
  
  if (count > 10) {
    CancelTimer(MyTimer);  // Stop the timer
  }
}

// One-time timer
SetTimer(StatusCheck, 5000);

on timer StatusCheck {
  Write("Status check");
  // Timer automatically stops after firing once
}
```

### Environment Variable Events

```capl
// React to SimVar (simulation variable) change
on start {
  // Enable monitoring of variable
}

on SimVar SimulationSpeed {
  float speed = SimulationSpeed;
  Write("Speed changed to: %f", speed);
}
```

### Error Handling Events

```capl
// Handle CAN errors
on message error {
  Write("CAN Error");
}

// Handle other system events
on busType {
  // Bus type detection
}
```

---

## Built-in Functions

### Output Functions

```capl
// Write to output/trace window
Write("Simple message");
Write("Value: %d", 42);
Write("Float: %f, Int: %d", 3.14, 100);

// Format specifiers
// %d - integer
// %u - unsigned integer
// %x or %X - hexadecimal
// %f - float
// %c - character
// %s - string
```

### Timing Functions

```capl
// Get current time in milliseconds since start
dword currentTime = GetTime();
Write("Time: %d ms", currentTime);

// Delay execution
Wait(1000);  // Wait 1000 ms (1 second)

// Check elapsed time
dword startTime = GetTime();
// Do something...
dword elapsed = GetTime() - startTime;
```

### String Functions

```capl
char str1[50] = "Hello";
char str2[50] = " World";
char result[100];

int length = strlen(str1);           // Get length: 5
strcpy(result, str1);                // Copy string
strcat(result, str2);                // Concatenate: "Hello World"

// String comparison
if (strcmp(str1, "Hello") == 0) {
  Write("Strings match");
}

// Convert between types
int value = atoi("123");             // String to integer
float fValue = atof("3.14");         // String to float
```

### Math Functions

```capl
#include "math.h"  // Required for math functions

int absValue = abs(-10);             // Absolute value: 10
double sqrtValue = sqrt(16);         // Square root: 4.0
double sinValue = sin(0.5);          // Sine
double cosValue = cos(0.5);          // Cosine
double tanValue = tan(0.5);          // Tangent
double power = pow(2, 8);            // 2^8 = 256
```

### Array Functions

```capl
// Find maximum
byte values[5] = {10, 25, 15, 30, 20};
byte maxVal = values[0];
for (int i = 1; i < 5; i++) {
  if (values[i] > maxVal)
    maxVal = values[i];
}

// Sum array
int sum = 0;
for (int i = 0; i < 5; i++) {
  sum += values[i];
}

// Sort array (bubble sort example)
void SortArray(byte arr[], int size) {
  for (int i = 0; i < size - 1; i++) {
    for (int j = 0; j < size - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        byte temp = arr[j];
        arr[j] = arr[j + 1];
        arr[j + 1] = temp;
      }
    }
  }
}
```

### Type Conversion

```capl
int intVal = 42;
float floatVal = (float)intVal;      // Cast to float
byte byteVal = (byte)intVal;         // Cast to byte
int backToInt = (int)floatVal;       // Cast back to int

// String conversion
char buffer[20];
sprintf(buffer, "Value: %d", 123);   // Format string
```

---

## Advanced Topics

### Working with Databases

```capl
// Include database file
#include "myDatabase.dbc"

// Use predefined messages
void SendPredefinedMessage() {
  EngineStatus msg;
  msg.RPM = 3000;
  msg.Temperature = 85;
  msg.FuelLevel = 50;
  Send(msg);
}

// Predefined message characteristics are available
on message EngineStatus {
  // Auto-completion and type-checking available
}
```

### Environment Variables (SimVar)

```capl
// Declare environment variables
dword gEngineRPM;
float gEngineTemp;

// Read from environment
on start {
  gEngineRPM = GetEnvVarInt("EngineRPM");
  gEngineTemp = GetEnvVarFloat("EngineTemperature");
}

// Write to environment
void SetEngineValues() {
  SetEnvVarInt("EngineRPM", 3000);
  SetEnvVarFloat("EngineTemperature", 95.5);
}
```

### Gateway Functions

```capl
// In a gateway-type CAPL script
on message Channel1.MessageA {
  // Receive from Channel 1
  Message msg;
  msg = MessageA;  // Copy message
  
  // Modify if needed
  msg.Data[0] = msg.Data[0] + 1;
  
  // Forward to Channel 2
  output(Channel2, msg);
}

// output() sends to specific channel
void ForwardMessage(Message inMsg, int targetChannel) {
  output(targetChannel, inMsg);
}
```

### Struct-like Structures

```capl
// Data structure using byte arrays
void ProcessComplexData() {
  byte packet[16];
  
  // Pack data
  packet[0] = 0xAA;  // Header
  packet[1] = 0xBB;  // Source
  packet[2] = 0xCC;  // Destination
  // ... more data
  
  // Extract data
  byte header = packet[0];
  byte source = packet[1];
  // Extract and process
}
```

### Bit Manipulation Helpers

```capl
// Macro-like functions for bit operations
void SetBit(byte *data, int bitIndex) {
  int byteIndex = bitIndex / 8;
  int bitPosition = bitIndex % 8;
  data[byteIndex] |= (1 << bitPosition);
}

void ClearBit(byte *data, int bitIndex) {
  int byteIndex = bitIndex / 8;
  int bitPosition = bitIndex % 8;
  data[byteIndex] &= ~(1 << bitPosition);
}

int CheckBit(byte data[], int bitIndex) {
  int byteIndex = bitIndex / 8;
  int bitPosition = bitIndex % 8;
  return (data[byteIndex] >> bitPosition) & 1;
}
```

---

## Best Practices

### 1. Script Organization

```capl
// === INCLUDES ===
#include "myDatabase.dbc"

// === CONSTANTS ===
const int MAX_RETRY = 3;
const dword TIMEOUT_MS = 5000;

// === GLOBAL VARIABLES ===
int gRetryCount = 0;
dword gLastMessageTime = 0;

// === TIMERS ===
timer gRetryTimer;

// === FUNCTION PROTOTYPES ===
void Retry();
void HandleTimeout();

// === EVENT HANDLERS ===
on start { /* ... */ }
on stop { /* ... */ }

// === FUNCTION IMPLEMENTATIONS ===
void Retry() { /* ... */ }
void HandleTimeout() { /* ... */ }
```

### 2. Naming Conventions

```capl
// Global variables with prefix 'g'
int gGlobalCounter;
dword gTimestamp;

// Constants in UPPERCASE
const int MAX_VALUE = 100;
const float PI = 3.14159;

// Functions with descriptive names
void ValidateData();
int CalculateChecksum();
void SendHeartbeat();

// Local variables in camelCase
void MyFunction() {
  int localCounter;
  float tempValue;
  byte buffer[8];
}
```

### 3. Error Handling

```capl
// Validate input range
void ProcessSpeed(int speed) {
  if (speed < 0 || speed > 200) {
    Write("Error: Invalid speed %d", speed);
    return;
  }
  // Process valid speed
}

// Check array bounds
void AccessArray(int index, int arraySize) {
  if (index < 0 || index >= arraySize) {
    Write("Error: Array index out of bounds");
    return;
  }
  // Safe access
}

// Verify message reception
on message EngineData {
  dword currentTime = GetTime();
  if (currentTime - gLastMessageTime > TIMEOUT_MS) {
    Write("Warning: Message timeout detected");
  }
  gLastMessageTime = currentTime;
}
```

### 4. Performance Optimization

```capl
// Avoid unnecessary operations in loops
int sum = 0;
for (int i = 0; i < 1000; i++) {
  sum += i;  // Simple operation
}

// Don't call expensive functions in tight loops
void OptimizedLoop() {
  // Pre-calculate outside loop
  int arraySize = sizeof(gArray) / sizeof(gArray[0]);
  
  for (int i = 0; i < arraySize; i++) {
    // Use index
  }
}

// Use appropriate data types
byte smallValue = 50;      // 0-255
int largeValue = 50000;    // Larger range
float precise = 3.14159;   // Decimal values
```

### 5. Code Documentation

```capl
/**
 * Validates CAN message data structure
 * @param msg - Pointer to message data
 * @param dlc - Data length code
 * @return 1 if valid, 0 if invalid
 */
int ValidateMessage(byte msg[], int dlc) {
  if (dlc < 1 || dlc > 8) {
    return 0;
  }
  // Validation logic
  return 1;
}

// Inline comments for complex logic
on message EngineStatus {
  // Check if RPM exceeds safe threshold
  if (EngineStatus.RPM > 7000) {
    Write("Warning: High RPM");
  }
}
```

---

## Practical Examples

### Example 1: Basic Message Sender

```capl
// Simple message sender with timing

timer SendTimer;
int messageCounter = 0;

on start {
  Write("Message Sender Started");
  SetTimer(SendTimer, 1000);  // Send every 1 second
}

on timer SendTimer {
  Message msg;
  msg.ID = 0x123;
  msg.DLC = 3;
  msg.Data[0] = messageCounter & 0xFF;
  msg.Data[1] = (messageCounter >> 8) & 0xFF;
  msg.Data[2] = 0xFF;
  
  Send(msg);
  
  Write("Message %d sent", messageCounter);
  messageCounter++;
  
  if (messageCounter > 100) {
    CancelTimer(SendTimer);
    Write("Sender completed");
  }
}
```

### Example 2: Message Receiver with Validation

```capl
// Receive and validate messages

on message 0x100 {
  // Basic validation
  if (this.DLC < 6) {
    Write("Error: Invalid message length %d", this.DLC);
    return;
  }
  
  // Extract fields
  byte status = this.Data[0];
  int temperature = (this.Data[1] << 8) | this.Data[2];
  int pressure = (this.Data[3] << 8) | this.Data[4];
  
  // Validate ranges
  if (temperature < -40 || temperature > 125) {
    Write("Warning: Abnormal temperature: %d", temperature);
  }
  
  if (pressure < 0 || pressure > 100) {
    Write("Warning: Abnormal pressure: %d", pressure);
  }
  
  Write("Status: %d, Temp: %d, Press: %d", status, temperature, pressure);
}
```

### Example 3: State Machine Implementation

```capl
// Simple state machine

#define STATE_IDLE 0
#define STATE_ACTIVE 1
#define STATE_ERROR 2

int gCurrentState = STATE_IDLE;
timer gStateTimer;

void SetState(int newState) {
  Write("State transition: %d -> %d", gCurrentState, newState);
  gCurrentState = newState;
}

on key 'S' {
  SetState(STATE_ACTIVE);
  SetTimer(gStateTimer, 5000);
}

on timer gStateTimer {
  if (gCurrentState == STATE_ACTIVE) {
    SetState(STATE_IDLE);
  }
}

on message ErrorCode {
  if (ErrorCode.Code != 0) {
    SetState(STATE_ERROR);
  }
}
```

### Example 4: Checksum Calculation

```capl
// Calculate and verify checksums

byte CalculateChecksum(byte data[], int length) {
  byte checksum = 0;
  for (int i = 0; i < length; i++) {
    checksum += data[i];
  }
  // Return two's complement
  return (~checksum) + 1;
}

int VerifyChecksum(byte data[], int length, byte checksum) {
  byte calculated = CalculateChecksum(data, length - 1);
  if (calculated == data[length - 1]) {
    return 1;  // Valid
  }
  return 0;    // Invalid
}

on message DataPacket {
  byte msgData[8];
  for (int i = 0; i < this.DLC; i++) {
    msgData[i] = this.Data[i];
  }
  
  if (VerifyChecksum(msgData, this.DLC, msgData[this.DLC - 1])) {
    Write("Checksum valid");
  } else {
    Write("Checksum error");
  }
}
```

### Example 5: Circular Buffer Implementation

```capl
// Simple circular buffer for data storage

#define BUFFER_SIZE 100
byte gBuffer[BUFFER_SIZE];
int gWriteIndex = 0;
int gReadIndex = 0;
int gCount = 0;

void BufferWrite(byte value) {
  gBuffer[gWriteIndex] = value;
  gWriteIndex = (gWriteIndex + 1) % BUFFER_SIZE;
  
  if (gCount < BUFFER_SIZE) {
    gCount++;
  } else {
    // Buffer full, overwrite oldest
    gReadIndex = (gReadIndex + 1) % BUFFER_SIZE;
  }
}

byte BufferRead() {
  if (gCount > 0) {
    byte value = gBuffer[gReadIndex];
    gReadIndex = (gReadIndex + 1) % BUFFER_SIZE;
    gCount--;
    return value;
  }
  return 0xFF;  // Error: empty buffer
}

int BufferCount() {
  return gCount;
}
```

### Example 6: Signal Multiplexing Example

```capl
// Handle multiplexed CAN messages

#define MUX_SIGNAL_ID 0
#define MUX_ENGINE 1
#define MUX_TRANSMISSION 2

on message MultiplexedData {
  byte muxValue = this.Data[MUX_SIGNAL_ID];
  
  switch (muxValue) {
    case MUX_ENGINE:
      {
        int rpm = (this.Data[1] << 8) | this.Data[2];
        float temp = (float)this.Data[3];
        Write("Engine: RPM=%d, Temp=%.1f", rpm, temp);
      }
      break;
      
    case MUX_TRANSMISSION:
      {
        int gear = this.Data[1];
        int torque = (this.Data[2] << 8) | this.Data[3];
        Write("Trans: Gear=%d, Torque=%d", gear, torque);
      }
      break;
      
    default:
      Write("Unknown multiplex identifier: %d", muxValue);
      break;
  }
}
```

---

## Troubleshooting Common Issues

### Variables Not Updating

**Problem**: Global variable changes don't persist.

**Solution**: Ensure variables are declared at global scope and not being reset in event handlers:

```capl
int gCounter;  // Global - persists

on start {
  gCounter = 0;  // Initialize once
}

on message SomeMessage {
  gCounter++;    // Increment - value persists
}
```

### Timer Not Firing

**Problem**: Timer event handler never executes.

**Solution**: Verify timer is started and event handler has correct name:

```capl
timer MyTimer;

on start {
  SetTimer(MyTimer, 1000);  // Must call SetTimer
}

on timer MyTimer {  // Must match timer name
  Write("Timer fired");
}
```

### Message Not Sending

**Problem**: Messages appear not to transmit.

**Solution**: Verify message structure and use SendMessage correctly:

```capl
// Correct way
Message msg;
msg.ID = 0x123;
msg.DLC = 8;
msg.Data[0] = 0x01;
Send(msg);

// Common mistake - forgetting DLC
Message badMsg;
badMsg.ID = 0x123;
// badMsg.DLC not set - defaults to 0!
Send(badMsg);  // Won't send data
```

### Data Type Overflow

**Problem**: Calculations produce unexpected results.

**Solution**: Use appropriate data types for value ranges:

```capl
byte val1 = 200;
byte val2 = 100;
int sum = val1 + val2;  // Use int result, not byte
Write("Sum: %d", sum);  // 300, not 44 (overflow)
```

---

## Quick Reference

### Common Message Operations

| Operation | Syntax |
|-----------|--------|
| Send message | `Send(msg);` |
| Get message ID | `this.ID` |
| Get message DLC | `this.DLC` |
| Access data byte | `this.Data[index]` |
| Get timestamp | `this.Time` |

### Common Timer Operations

| Operation | Syntax |
|-----------|--------|
| Start timer | `SetTimer(timerName, milliseconds);` |
| Stop timer | `CancelTimer(timerName);` |
| Timer event | `on timer timerName { }` |

### Common Output Operations

| Operation | Syntax |
|-----------|--------|
| Write text | `Write("message");` |
| Format output | `Write("Value: %d", variable);` |
| Get current time | `dword t = GetTime();` |
| Pause execution | `Wait(milliseconds);` |

---

## Resources and Further Learning

### Official Documentation
- Vector CANoe Help System (integrated in CANoe)
- Vector CAPL Documentation manual
- CANoe Online Help (Help > CANoe Help)

### Tips for Success

1. **Start Simple**: Begin with basic message send/receive before complex logic
2. **Use Debugger**: Utilize CANoe's built-in debugger for troubleshooting
3. **Monitor Output**: Use Write() statements liberally during development
4. **Test Gradually**: Incrementally test functionality rather than entire script at once
5. **Database Integration**: Leverage .dbc file imports for message definitions
6. **Version Control**: Keep backups of working scripts
7. **Performance**: Monitor CPU load in CANoe's Measurement setup

### Common Libraries to Include

```capl
#include "stdlib.h"      // Standard library functions
#include "math.h"        // Math functions
#include "string.h"      // String functions
#include "time.h"        // Time functions
#include "database.dbc"  // CAN database definitions
```

---

## Conclusion

CAPL scripting is a powerful tool for CAN bus testing and simulation. This guide covers the fundamental concepts and practical examples to help you build effective CAPL scripts. Practice with the examples provided and gradually build more complex solutions. Remember that CAPL is event-driven, so think about what events your script needs to handle and write event handlers accordingly.

Key takeaways:
- CAPL is based on C syntax with extensions for CAN messaging
- Scripts are event-driven (message reception, timers, keyboard, etc.)
- Use appropriate data types and validate inputs
- Organize code with clear naming conventions
- Leverage CANoe's database integration for message definitions
- Test incrementally and use debugging tools effectively

Happy scripting!
