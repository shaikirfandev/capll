# CAPL Script Interview Questions & Answers - 100 Questions

## Quick Navigation
- [1-10: Basics](#basics-questions-1-10)
- [11-20: Data Types & Variables](#data-types--variables-questions-11-20)
- [21-30: Operators & Expressions](#operators--expressions-questions-21-30)
- [31-40: Control Flow](#control-flow-questions-31-40)
- [41-50: Functions & Scope](#functions--scope-questions-41-50)
- [51-60: Arrays & Strings](#arrays--strings-questions-51-60)
- [61-70: Events & Timers](#events--timers-questions-61-70)
- [71-80: Message Handling](#message-handling-questions-71-80)
- [81-90: Error Handling & Validation](#error-handling--validation-questions-81-90)
- [91-100: Advanced Topics](#advanced-topics-questions-91-100)

---

## BASICS - Questions 1-10

### Q1: What is CAPL and what does it stand for?
**A:** CAPL stands for Computer Aided Production Language. It's an event-driven scripting language designed for automotive CAN bus testing, simulation, and analysis. CAPL is used primarily in Vector CANoe and CANalyzer tools for creating test scripts, gateways, and simulations.

### Q2: What is the main difference between CAPL and C language?
**A:** While CAPL is based on C syntax, key differences include:
- **Event-driven**: CAPL uses event handlers (on message, on timer, on key)
- **Message-oriented**: Built-in CAN message handling
- **No main function**: Program flow driven by events, not a main() entry point
- **Simplified**: No pointers or complex memory management
- **Integrated**: Direct access to CAN bus, timers, and CANoe features

### Q3: What is an event in CAPL?
**A:** An event is something that happens in the system that triggers code execution. CAPL is event-driven, meaning code only runs when specific events occur:
```capl
on start             // Event: measurement starts
on message 0x100     // Event: specific message received
on timer MyTimer     // Event: timer expires
on key 'A'          // Event: key pressed
```

### Q4: What does "event-driven" mean?
**A:** Event-driven means the program doesn't run continuously. Instead:
- Program waits for events to occur
- When an event happens, the corresponding handler executes
- After handler finishes, program waits for next event
- More efficient than polling or busy-waiting

Example:
```capl
on message 0x100 {
  // Code runs ONLY when message 0x100 arrives
  // Not continuously checking for it
}
```

### Q5: What is the execution order in CAPL?
**A:** CAPL execution follows this order:
1. `on start` - Runs once at measurement start (initialization)
2. Event-driven handlers execute in order of events
3. `on message *` - Catches all messages
4. `on message ID` - Specific message handlers
5. `on timer` - Timer events
6. `on key` - Keyboard events
7. `on stop` - Runs once at measurement end (cleanup)

### Q6: What is the difference between local and global variables in CAPL?
**A:**
```capl
// GLOBAL - visible everywhere in script
int gGlobalCounter = 0;

void MyFunction() {
  // LOCAL - only visible in this function
  int localCounter = 0;
  
  {
    // BLOCK-LOCAL - only visible in this block
    int blockVar = 0;
  }
  // blockVar not accessible here
}
```

**Scope Rules:**
- Global: Declared outside functions
- Local: Declared inside functions
- Block: Declared inside curly braces

### Q7: What are the basic data types in CAPL?
**A:**
| Type | Size | Range | Example |
|------|------|-------|---------|
| byte | 8 bits | 0-255 | `byte val = 100;` |
| word | 16 bits | 0-65535 | `word val = 1000;` |
| dword | 32 bits | 0-4.2B | `dword val = 50000;` |
| int | 32 bits | -2.1B to 2.1B | `int val = -100;` |
| float | 32 bits | ±3.4E±38 | `float val = 3.14;` |
| double | 64 bits | ±1.7E±308 | `double val = 3.14159;` |
| char | 8 bits | -128 to 127 | `char c = 'A';` |

### Q8: How do you declare and initialize an array in CAPL?
**A:**
```capl
// Single dimension
byte data[8];                           // Uninitialized
byte data[8] = {0x00};                 // Initialize to 0
byte data[8] = {0x01, 0x02, 0x03};    // Explicit values

// Two dimension
int matrix[3][3];                       // 3x3 matrix
int matrix[3][3] = {                   // With values
  {1, 2, 3},
  {4, 5, 6},
  {7, 8, 9}
};

// Strings (char arrays)
char str[50] = "Hello";
```

### Q9: What is the purpose of `Write()` function?
**A:** The `Write()` function outputs text to the CANoe Trace window:
```capl
Write("Simple message");                      // Basic text
Write("Value: %d", 42);                      // With variable
Write("Float: %.2f", 3.14159);               // Formatted output
Write("Hex: 0x%X", 255);                     // Hexadecimal

// Format specifiers:
// %d - integer
// %f - float
// %.2f - float with 2 decimals
// %X or %x - hexadecimal
// %s - string
// %c - character
```

### Q10: What are the main include files used in CAPL?
**A:**
```capl
#include "stdlib.h"      // Standard library (common functions)
#include "math.h"        // Math functions (sin, cos, sqrt, etc.)
#include "string.h"      // String functions
#include "time.h"        // Time functions
#include "database.dbc"  // CAN database (defines messages)
```

These provide access to built-in functions. The database include is most common for accessing message definitions.

---

## DATA TYPES & VARIABLES - Questions 11-20

### Q11: What is the difference between int and dword?
**A:**
```capl
int value;    // Signed 32-bit (-2,147,483,648 to 2,147,483,647)
dword value;  // Unsigned 32-bit (0 to 4,294,967,295)
```
- **int**: Can represent negative numbers
- **dword**: Always positive (useful for large unsigned values)
- **byte**: 0-255 (smaller, more memory efficient)

Example:
```capl
int temp = -40;      // Valid: negative temperature
dword timestamp = GetTime();  // Valid: timestamps are positive
```

### Q12: How do you declare a constant in CAPL?
**A:**
```capl
const int MAX_VALUE = 100;
const float PI = 3.14159;
const byte STATUS_READY = 0x01;
const dword TIMEOUT_MS = 5000;
```

Constants are:
- Immutable: Can't change after initialization
- Memory efficient: Compiled into code
- Named constants: More readable than magic numbers

### Q13: What is the difference between const and #define?
**A:**
```capl
// CONST - Typed constant
const int MAX = 100;
int arr[MAX];  // Valid

// #DEFINE - Preprocessor macro
#define MAX 100
#define MAX_SIZE 100
#define CONCAT(a,b) a##b  // Can be complex

// Differences:
// const: Type-safe, scoped
// #define: Simple text replacement, no type checking
```

### Q14: How do you convert between data types?
**A:**
```capl
// Type casting (explicit)
int intVal = 42;
float floatVal = (float)intVal;     // int to float
byte byteVal = (byte)intVal;        // int to byte

// String conversions
int numFromStr = atoi("123");       // String to int
float floatFromStr = atof("3.14");  // String to float

// Number to string
char buffer[20];
sprintf(buffer, "%d", 42);          // 42 -> "42"
sprintf(buffer, "0x%X", 255);       // 255 -> "0xFF"
```

### Q15: What is the sizeof operator?
**A:**
```capl
int size_byte = sizeof(byte);       // 1
int size_word = sizeof(word);       // 2
int size_dword = sizeof(dword);     // 4
int size_float = sizeof(float);     // 4
int size_double = sizeof(double);   // 8

// Array size calculation
byte arr[10];
int elementCount = sizeof(arr) / sizeof(arr[0]);  // 10
```

### Q16: How do you handle floating point precision?
**A:**
```capl
float f = 3.14159265;
double d = 3.14159265358979;

// Display with specific decimals
Write("Float: %.2f", f);        // 3.14
Write("Float: %.4f", f);        // 3.1416
Write("Double: %.8f", d);       // 3.14159265

// Comparison with tolerance
float val1 = 3.14;
float val2 = 3.15;
float tolerance = 0.1;

if (abs(val1 - val2) < tolerance) {
  Write("Values are close enough");
}
```

### Q17: What is the difference between initialization and assignment?
**A:**
```capl
// INITIALIZATION - Setting value at declaration
int x = 100;          // Initialize x to 100
byte arr[5] = {1,2,3,4,5};  // Initialize array

// ASSIGNMENT - Setting value after declaration
int y;                // Declare (default 0)
y = 100;             // Assign later

// In function
void MyFunc() {
  int local = 50;    // Initialize local variable
  local = 75;        // Assign new value
}

// All global variables auto-initialized to 0
int gCounter;        // Starts as 0
dword gTime;         // Starts as 0
```

### Q18: How do you work with character arrays and strings?
**A:**
```capl
// Declare string
char str1[50] = "Hello";

// String functions
int len = strlen(str1);              // Get length
strcpy(str1, "World");              // Copy
strcat(str1, " C");                 // Concatenate
int cmp = strcmp(str1, "World");    // Compare (0=equal)

// Format string
char formatted[100];
sprintf(formatted, "Value: %d", 42); // Create formatted string

// Character access
char first = str1[0];               // 'H'
char last = str1[strlen(str1)-1];   // Last character
```

### Q19: What happens if you don't initialize a variable?
**A:**
```capl
// GLOBAL variables auto-initialize to 0
int gValue;         // Value = 0
byte gByte;         // Value = 0
float gFloat;       // Value = 0.0
char gStr[50];      // Value = "" (empty)

// LOCAL variables are NOT automatically initialized
void MyFunc() {
  int local;        // Value is UNKNOWN (garbage)
  Write("%d", local);  // Unpredictable output!
  
  // Best practice: Always initialize
  int localSafe = 0;  // Safe: initialized to 0
}
```

### Q20: How do global variables interact with event handlers?
**A:**
```capl
int gCounter = 0;        // Global, shared across all handlers

on start {
  gCounter = 0;          // Initialize
}

on message 0x100 {
  gCounter++;            // Increment (persistent across messages)
  Write("Count: %d", gCounter);
}

on timer MyTimer {
  if (gCounter > 100) {  // Check value from message handler
    Write("Threshold reached!");
    gCounter = 0;        // Reset
  }
}
```

Global variables **persist** across event handlers until script stops.

---

## OPERATORS & EXPRESSIONS - Questions 21-30

### Q21: What are the arithmetic operators in CAPL?
**A:**
```capl
int a = 15, b = 4;

int sum = a + b;           // Addition: 19
int diff = a - b;          // Subtraction: 11
int prod = a * b;          // Multiplication: 60
int quot = a / b;          // Division: 3
int rem = a % b;           // Modulus: 3

// Unary operators
int neg = -a;              // Negation: -15
int pos = +a;              // Positive: 15
```

### Q22: What are the comparison operators?
**A:**
```capl
int a = 10, b = 20;

if (a == b) { }            // Equal (false)
if (a != b) { }            // Not equal (true)
if (a > b)  { }            // Greater than (false)
if (a < b)  { }            // Less than (true)
if (a >= b) { }            // Greater or equal (false)
if (a <= b) { }            // Less or equal (true)

// Results: 0 = false, 1 = true
int result = (a < b);      // result = 1
```

### Q23: What are the logical operators?
**A:**
```capl
int x = 1, y = 1, z = 0;

// AND (&&) - both must be true
if (x && y) { }            // true (1 && 1)
if (x && z) { }            // false (1 && 0)

// OR (||) - at least one true
if (x || z) { }            // true (1 || 0)
if (z || z) { }            // false (0 || 0)

// NOT (!) - negates condition
if (!x) { }                // false (!1)
if (!z) { }                // true (!0)

// Complex conditions
if (x && (y || !z)) { }    // true: 1 && (1 || 1)
```

### Q24: What are the bitwise operators?
**A:**
```capl
byte a = 0x0F;  // 00001111
byte b = 0xF0;  // 11110000

byte and = a & b;           // AND: 00000000 (0x00)
byte or = a | b;            // OR:  11111111 (0xFF)
byte xor = a ^ b;           // XOR: 11111111 (0xFF)
byte not = ~a;              // NOT: 11110000 (0xF0)

byte lshift = a << 2;       // Left shift by 2: 00111100 (0x3C)
byte rshift = b >> 2;       // Right shift by 2: 00111100 (0x3C)
```

### Q25: What are the increment and decrement operators?
**A:**
```capl
int counter = 5;

// Pre-increment (++var)
int val1 = ++counter;       // counter=6, val1=6

// Post-increment (var++)
int val2 = counter++;       // val2=6, counter=7

// Pre-decrement (--var)
int val3 = --counter;       // counter=6, val3=6

// Post-decrement (var--)
int val4 = counter--;       // val4=6, counter=5

// Difference:
int x = 0;
Write("%d", x++);           // Prints 0, then x becomes 1
Write("%d", ++x);           // x becomes 2, prints 2

// In loops
for (int i = 0; i < 10; i++) { }  // Either works
for (int j = 0; j < 10; ++j) { }  // Slightly more efficient
```

### Q26: What are the assignment operators?
**A:**
```capl
int x = 10;

x += 5;                     // x = x + 5 = 15
x -= 3;                     // x = x - 3 = 12
x *= 2;                     // x = x * 2 = 24
x /= 4;                     // x = x / 4 = 6
x %= 5;                     // x = x % 5 = 1

// Bitwise assignment
byte flags = 0xFF;
flags &= 0x0F;              // flags = 0x0F
flags |= 0xF0;              // flags = 0xFF
flags ^= 0x55;              // flags = 0xAA
```

### Q27: What is the ternary operator?
**A:**
```capl
// Syntax: condition ? true_value : false_value

int age = 25;
char *status = (age >= 18) ? "Adult" : "Minor";

int max = (a > b) ? a : b;

// Nested ternary
int score = 85;
char *grade = (score >= 90) ? "A" :
              (score >= 80) ? "B" :
              (score >= 70) ? "C" : "F";

// Example in code
int speed = 50;
int speedLimit = speed < 30 ? 10 : (speed < 60 ? 20 : 30);
```

### Q28: What is operator precedence?
**A:**
```capl
// Precedence (high to low):
// 1. () [] . ->  (parentheses, brackets, member access)
// 2. ! ~ ++ --  (unary operators)
// 3. * / %      (multiplication, division, modulus)
// 4. + -        (addition, subtraction)
// 5. << >>      (bit shifts)
// 6. < <= > >=  (comparison)
// 7. == !=      (equality)
// 8. &          (bitwise AND)
// 9. ^          (bitwise XOR)
// 10. |         (bitwise OR)
// 11. &&        (logical AND)
// 12. ||        (logical OR)
// 13. ? :       (ternary)
// 14. = += -= (* assignment operators)

// Examples:
int a = 2 + 3 * 4;          // 14 (not 20) - * before +
int b = (2 + 3) * 4;        // 20 - parentheses first
int c = 16 >> 2 + 1;        // 4 - + before >>
int d = 16 >> (2 + 1);      // 2 - parentheses first
```

### Q29: How do you handle division by zero?
**A:**
```capl
int a = 10, b = 0;

// CHECK before dividing
if (b != 0) {
  int result = a / b;
  Write("Result: %d", result);
} else {
  Write("Error: Division by zero!");
}

// Function to safely divide
int SafeDivide(int numerator, int denominator) {
  if (denominator == 0) {
    Write("Error: Cannot divide by zero");
    return 0;  // Or return error code
  }
  return numerator / denominator;
}

// Usage
int result = SafeDivide(10, 0);  // Handled safely
```

### Q30: What is the difference between = and ==?
**A:**
```capl
int x = 10;        // = is ASSIGNMENT (sets value)
int y;

y = x;             // y gets value 10

// Common mistake
if (x = 5) {       // WRONG: assigns 5 to x, evaluates true
  Write("x is 5");  // Always executes
}

if (x == 5) {      // CORRECT: compares x with 5
  Write("x equals 5");  // Only if true
}

// In comparisons, ALWAYS use ==
if (x == 10) { }
if (x == 20) { }
if (x != 30) { }
```

---

## CONTROL FLOW - Questions 31-40

### Q31: What is the if statement syntax?
**A:**
```capl
// Simple if
if (condition) {
  // Execute if condition is true
}

// if-else
if (condition) {
  // Execute if true
} else {
  // Execute if false
}

// if-else if-else
if (age < 13) {
  Write("Child");
} else if (age < 18) {
  Write("Teenager");
} else if (age < 65) {
  Write("Adult");
} else {
  Write("Senior");
}

// Single statement (no braces)
if (x > 0) Write("Positive");
else Write("Not positive");
```

### Q32: What is the switch statement?
**A:**
```capl
switch (status) {
  case 0:
    Write("Idle");
    break;          // Exit switch
  case 1:
    Write("Running");
    break;
  case 2:
  case 3:          // Fall-through (handle multiple values)
    Write("Warning");
    break;
  default:         // Default case
    Write("Unknown");
    break;
}

// Important: Always use break to exit case
// Without break, execution "falls through" to next case
```

### Q33: When should you use switch vs if-else?
**A:**
```capl
// Use SWITCH when:
// - Comparing single integer/char against many values
// - Multiple cases have same action

int mode = 2;
switch (mode) {
  case 0: DoInit(); break;
  case 1: DoRun(); break;
  case 2: DoPause(); break;
}

// Use IF-ELSE when:
// - Complex conditions with ranges
// - Logical operations (&&, ||)

int temp = 25;
if (temp < 0) {
  Write("Freezing");
} else if (temp < 15) {
  Write("Cold");
} else if (temp < 25) {
  Write("Cool");
} else {
  Write("Warm");
}
```

### Q34: What is the while loop?
**A:**
```capl
int counter = 0;

while (counter < 10) {
  Write("Counter: %d", counter);
  counter++;
}

// Do-while (executes at least once)
int x = 10;
do {
  Write("This runs even though x > 5");
} while (x < 5);

// Infinite loop (use break to exit)
while (1) {  // Always true
  if (someCondition) break;
}

// Loop with condition check
int attempts = 0;
while (attempts < 3 && !success) {
  attempts++;
  TryAgain();
}
```

### Q35: What is the for loop?
**A:**
```capl
// Standard for loop
for (int i = 0; i < 10; i++) {
  Write("i = %d", i);
}

// No initialization
int j = 0;
for (; j < 10; j++) {
  // starts with j already set
}

// No increment
for (int k = 0; k < 10;) {
  k += 2;
}

// Multiple variables
for (int x = 0, y = 10; x <= y; x++, y--) {
  Write("x=%d, y=%d", x, y);
}

// Infinite loop in for
for (;;) {
  if (condition) break;
}

// Backwards
for (int i = 10; i >= 0; i--) {
  Write("%d", i);
}
```

### Q36: What is the break statement?
**A:**
```capl
// Exit a loop
for (int i = 0; i < 100; i++) {
  if (i == 5) {
    Write("Found 5, breaking");
    break;  // Exit for loop
  }
}

// Exit a switch
switch (value) {
  case 1:
    Write("One");
    break;  // Exit switch, not loop
  case 2:
    Write("Two");
    break;
}

// Nested loops - break only exits inner loop
for (int i = 0; i < 10; i++) {
  for (int j = 0; j < 10; j++) {
    if (j == 5) break;  // Breaks inner loop only
  }
}
```

### Q37: What is the continue statement?
**A:**
```capl
// Skip to next iteration
for (int i = 0; i < 10; i++) {
  if (i % 2 == 0) continue;  // Skip even numbers
  Write("%d", i);             // Only odd: 1,3,5,7,9
}

// Useful for filtering
while (true) {
  if (!isValid()) continue;  // Skip invalid
  processData();
}

// In nested loops - only affects innermost
for (int i = 0; i < 3; i++) {
  for (int j = 0; j < 3; j++) {
    if (j == 1) continue;  // Continues inner loop
    Write("%d,%d ", i, j);
  }
}
// Output: 0,0 0,2 1,0 1,2 2,0 2,2
```

### Q38: What are nested loops?
**A:**
```capl
// Nested for loops
for (int row = 1; row <= 3; row++) {
  for (int col = 1; col <= 3; col++) {
    Write("%d*%d=%d ", row, col, row*col);
  }
  Write("\n");
}

// Nested with break
for (int i = 0; i < 10; i++) {
  for (int j = 0; j < 10; j++) {
    if (j == 5) {
      break;  // Breaks inner loop only
    }
  }
}

// Search in 2D array
int found = 0;
for (int i = 0; i < 3; i++) {
  for (int j = 0; j < 3; j++) {
    if (matrix[i][j] == target) {
      found = 1;
      break;  // Break inner
    }
  }
  if (found) break;  // Break outer
}
```

### Q39: What is the difference between while and do-while?
**A:**
```capl
// WHILE - checks condition FIRST
int x = 10;
while (x < 5) {
  Write("This never runs");  // x is 10, not < 5
}

// DO-WHILE - executes THEN checks condition
int y = 10;
do {
  Write("This runs once");    // Executes even though y > 5
} while (y < 5);

// Practical example: User input loop
char input[10];
int valid = 0;
do {
  // Get user input
  // Validate input
  if (isValid) valid = 1;
} while (!valid);  // Keep asking until valid
```

### Q40: How do you create nested conditionals?
**A:**
```capl
int age = 25;
int hasLicense = 1;

if (age >= 18) {
  if (hasLicense) {
    Write("Can drive");
  } else {
    Write("Need license");
  }
} else {
  Write("Too young");
}

// Better with && operator
if (age >= 18 && hasLicense) {
  Write("Can drive");
}

// Complex nesting
int temp = 25;
int humidity = 60;

if (temp > 30) {
  if (humidity > 70) {
    Write("Hot and humid");
  } else {
    Write("Hot and dry");
  }
} else if (temp > 15) {
  if (humidity > 70) {
    Write("Warm and humid");
  } else {
    Write("Warm and dry");
  }
} else {
  Write("Cold");
}

// Cleaner version
if ((temp > 30) && (humidity > 70)) {
  Write("Hot and humid");
} else if ((temp > 30) && (humidity <= 70)) {
  Write("Hot and dry");
}
// ... etc
```

---

## FUNCTIONS & SCOPE - Questions 41-50

### Q41: How do you define a function?
**A:**
```capl
// Function without parameters or return value
void PrintHello() {
  Write("Hello!");
}

// Function with parameters
void Greet(char *name) {
  Write("Hello, %s", name);
}

// Function with return value
int Add(int a, int b) {
  return a + b;
}

// Function with multiple parameters and return
float CalculateAverage(int val1, int val2, int val3) {
  int sum = val1 + val2 + val3;
  return (float)sum / 3;
}

// Calling functions
PrintHello();
Greet("Alice");
int result = Add(5, 3);
float avg = CalculateAverage(10, 20, 30);
```

### Q42: What is a function prototype?
**A:**
```capl
// FUNCTION PROTOTYPE (declaration)
// Tells compiler function exists, will be defined later
int Add(int a, int b);          // Prototype
void PrintStats();

// FUNCTION DEFINITIONS
int Add(int a, int b) {
  return a + b;
}

void PrintStats() {
  Write("Running stats");
}

// Usage: Can call functions before they're defined
on start {
  int sum = Add(5, 3);           // Works (prototype declared)
  PrintStats();
}

// Why use prototypes?
// - Allows calling function before definition
// - Better code organization
// - Required for forward references

// Good practice - put all prototypes at top
int Add(int a, int b);
int Subtract(int a, int b);
int Multiply(int a, int b);

// Then function definitions below
```

### Q43: How do parameters work in functions?
**A:**
```capl
// PASS BY VALUE - function gets copy
void ModifyByValue(int value) {
  value = 100;  // Changes local copy only
}

int x = 10;
ModifyByValue(x);
Write("%d", x);  // Still 10 (unchanged)

// PASS BY REFERENCE - using arrays
void FillArray(int arr[], int size) {
  for (int i = 0; i < size; i++) {
    arr[i] = i;  // Modifies original array
  }
}

int data[5];
FillArray(data, 5);
Write("%d", data[0]);  // Changed! Value is 0

// Arrays always pass by reference
// Other types pass by value

// Multiple parameters
int Max(int a, int b, int c) {
  int max = a;
  if (b > max) max = b;
  if (c > max) max = c;
  return max;
}

int highest = Max(10, 30, 20);  // 30
```

### Q44: What is function return value?
**A:**
```capl
// Function MUST return correct type
int GetPositive() {
  return 5;        // Returns int
}

float GetPI() {
  return 3.14159;  // Returns float
}

void PrintMessage() {
  Write("Hello");
  return;          // No value (or just return;)
}

// Early return
int ValidateAge(int age) {
  if (age < 0) return 0;      // Invalid
  if (age > 150) return 0;    // Invalid
  return 1;                    // Valid
}

// Using return values
int status = ValidateAge(25);
if (status) {
  Write("Age is valid");
} else {
  Write("Age is invalid");
}

// Multiple returns
int AbsoluteValue(int x) {
  if (x < 0) return -x;
  return x;
}
```

### Q45: What is variable scope?
**A:**
```capl
// GLOBAL SCOPE
int gGlobalVar = 100;

void Function1() {
  // gGlobalVar accessible here
  Write("%d", gGlobalVar);
  
  // LOCAL SCOPE
  int localVar = 50;
  // localVar only in Function1
}

void Function2() {
  // gGlobalVar accessible here
  Write("%d", gGlobalVar);
  
  // localVar NOT accessible here
  // Write("%d", localVar);  // COMPILE ERROR
}

// BLOCK SCOPE
void Function3() {
  int x = 10;
  
  {
    int y = 20;
    // x and y both accessible here
  }
  
  // y NOT accessible here (block ended)
  // x still accessible
}

// PARAMETER SCOPE
void MyFunc(int param) {
  // param only accessible in MyFunc
  Write("%d", param);
}
```

### Q46: How do you handle variable naming to avoid confusion?
**A:**
```capl
// Good naming convention
int gGlobalCounter;        // Global: g prefix
dword gStartTime;

void ProcessData() {
  int localCounter;        // Local: no prefix
  float tempValue;
  
  const int MAX_SIZE = 100;  // Constant: UPPERCASE
  const int MIN_SIZE = 10;
}

// Avoid shadowing
int gValue = 100;  // Global

void MyFunc() {
  int gValue = 50;  // LOCAL shadows global
  Write("%d", gValue);  // 50 (local)
  // How to access global? Not easily - bad design
}

// Better practice - don't shadow
int gValue = 100;
int gValueLocal = 50;

// Name by type/purpose
int gMessageCount;     // What it is
int gChecksum;         // What it does
int gIsActive;         // Boolean (Is___ pattern)
int gHasError;
```

### Q47: What is recursion?
**A:**
```capl
// RECURSIVE FUNCTION - calls itself
int Factorial(int n) {
  if (n <= 1) {
    return 1;        // Base case (stops recursion)
  } else {
    return n * Factorial(n - 1);  // Recursive call
  }
}

// Example execution: Factorial(4)
// 4 * Factorial(3)
// 4 * 3 * Factorial(2)
// 4 * 3 * 2 * Factorial(1)
// 4 * 3 * 2 * 1
// = 24

// Another example: Fibonacci
int Fibonacci(int n) {
  if (n <= 1) return n;  // Base case
  return Fibonacci(n-1) + Fibonacci(n-2);  // Recursive
}

// Usage
Write("Factorial(5) = %d", Factorial(5));  // 120
Write("Fibonacci(7) = %d", Fibonacci(7));  // 13

// Common issue - infinite recursion
void BadRecursion() {
  BadRecursion();  // NEVER ENDS - stack overflow!
}
```

### Q48: What is the difference between void and returning a value?
**A:**
```capl
// VOID - no return value
void PrintMessage() {
  Write("Message");
  // return;  // Optional, no value
}

// Function returns value
int GetNumber() {
  return 42;
}

// Usage
PrintMessage();        // Call, ignore any return
int val = GetNumber(); // Call, capture return

// WRONG: Can't assign void
// int x = PrintMessage();  // COMPILE ERROR

// Can return early from void
void ProcessData() {
  if (!isValid()) return;    // Early exit
  // Process valid data
}

// Must return value from non-void
int Divide(int a, int b) {
  if (b == 0) {
    Write("Error!");
    return -1;  // MUST return something
  }
  return a / b;
}
```

### Q49: How do you pass arrays to functions?
**A:**
```capl
// Arrays ALWAYS pass by reference
void PrintArray(byte arr[], int size) {
  for (int i = 0; i < size; i++) {
    Write("%d", arr[i]);  // Access function parameter
  }
}

void FillArray(int arr[], int size, int value) {
  for (int i = 0; i < size; i++) {
    arr[i] = value;  // MODIFIES original array
  }
}

void SortArray(int arr[], int size) {
  // Sorting code here
  // Changes are reflected in original array
}

// Usage
byte data[8] = {10, 20, 30, 40, 50, 60, 70, 80};
PrintArray(data, 8);

int numbers[5];
FillArray(numbers, 5, 100);  // All elements become 100

// 2D array (note syntax)
void Process2D(int matrix[3][3]) {
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      matrix[i][j] = i * j;
    }
  }
}
```

### Q50: What is the stack and heap? (Understanding memory)
**A:**
```capl
// Most CAPL variables use STACK (automatic)
void MyFunction() {
  int localVar = 10;      // Stack - automatic cleanup
  char arr[100];          // Stack
  float f = 3.14;         // Stack
}
// All local variables destroyed when function ends

// GLOBAL variables
int gGlobal = 100;        // Exists entire program

// Stack considerations
void RecursiveFunc(int depth) {
  int local[1000];        // Stack grows
  if (depth > 1000) {
    // Stack overflow! Too many recursions
  }
  RecursiveFunc(depth + 1);
}

// Best practice: Avoid deep recursion
// Use iteration instead when possible

// CAPL doesn't have dynamic allocation (new/delete)
// All memory management is automatic
```

---

## ARRAYS & STRINGS - Questions 51-60

### Q51: How do you declare and access array elements?
**A:**
```capl
// Single dimension array
byte data[8];                           // 8 elements
int values[100];                        // 100 elements

// Access elements (0-based indexing)
data[0] = 0x11;                         // First element
data[7] = 0x88;                         // Last element
int val = data[3];                      // Read element

// Multi-dimension array
int matrix[3][3];                       // 3x3
float table[10][10];                    // 10x10

// Access 2D elements
matrix[0][0] = 1;                       // First
matrix[2][2] = 9;                       // Last (0,0 to 2,2)

// Array bounds
byte arr[5];   // Valid indices: 0,1,2,3,4
// arr[5] is OUT OF BOUNDS (undefined behavior)
```

### Q52: How do you iterate through an array?
**A:**
```capl
byte data[8] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};

// FOR loop (most common)
for (int i = 0; i < 8; i++) {
  Write("%02X", data[i]);
}

// WHILE loop
int i = 0;
while (i < 8) {
  Write("%02X", data[i]);
  i++;
}

// Process with condition
for (int i = 0; i < 8; i++) {
  if (data[i] == 0xFF) {
    Write("Found 0xFF at index %d", i);
    break;
  }
}

// Reverse iteration
for (int i = 7; i >= 0; i--) {
  Write("%02X", data[i]);
}

// Multi-dimension
int matrix[3][3];
for (int r = 0; r < 3; r++) {
  for (int c = 0; c < 3; c++) {
    Write("%d ", matrix[r][c]);
  }
}
```

### Q53: How do you find the size of an array?
**A:**
```capl
byte data[8];

// Method 1: sizeof
int elementSize = sizeof(data[0]);  // 1 for byte
int totalSize = sizeof(data);       // 8 for byte[8]
int count = totalSize / elementSize; // 8

// Method 2: Known size (most reliable)
#define ARRAY_SIZE 8
byte data[ARRAY_SIZE];

for (int i = 0; i < ARRAY_SIZE; i++) {
  // Use ARRAY_SIZE
}

// Method 3: Store size
void ProcessArray(byte arr[], int size) {
  for (int i = 0; i < size; i++) {
    // Use size parameter
  }
}

// Practical example
byte values[5];
int len = sizeof(values) / sizeof(values[0]);  // 5
for (int i = 0; i < len; i++) {
  values[i] = i * 10;
}
```

### Q54: How do you search for values in an array?
**A:**
```capl
// LINEAR SEARCH
int Find(int arr[], int size, int target) {
  for (int i = 0; i < size; i++) {
    if (arr[i] == target) {
      return i;        // Found at index i
    }
  }
  return -1;           // Not found
}

// Usage
int numbers[5] = {10, 20, 30, 40, 50};
int index = Find(numbers, 5, 30);  // Returns 2
if (index >= 0) {
  Write("Found at index %d", index);
} else {
  Write("Not found");
}

// Search with condition
int FindGreater(int arr[], int size, int threshold) {
  for (int i = 0; i < size; i++) {
    if (arr[i] > threshold) {
      return i;
    }
  }
  return -1;
}

// Count occurrences
int CountValue(byte arr[], int size, byte target) {
  int count = 0;
  for (int i = 0; i < size; i++) {
    if (arr[i] == target) {
      count++;
    }
  }
  return count;
}
```

### Q55: How do you sort an array?
**A:**
```capl
// BUBBLE SORT (simple, inefficient)
void BubbleSort(int arr[], int size) {
  for (int i = 0; i < size - 1; i++) {
    for (int j = 0; j < size - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        // Swap
        int temp = arr[j];
        arr[j] = arr[j + 1];
        arr[j + 1] = temp;
      }
    }
  }
}

// Usage
int unsorted[5] = {50, 20, 80, 10, 60};
BubbleSort(unsorted, 5);
// Result: 10, 20, 50, 60, 80

// Reverse sort (descending)
void BubbleSortDesc(int arr[], int size) {
  for (int i = 0; i < size - 1; i++) {
    for (int j = 0; j < size - i - 1; j++) {
      if (arr[j] < arr[j + 1]) {  // Note: < instead of >
        int temp = arr[j];
        arr[j] = arr[j + 1];
        arr[j + 1] = temp;
      }
    }
  }
}

// Different data types
void SortBytes(byte arr[], int size) {
  // Same algorithm, different type
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

### Q56: How do you work with strings in CAPL?
**A:**
```capl
// Declare string
char str1[50] = "Hello";
char str2[50];

// String length
int len = strlen(str1);           // 5

// Copy string
strcpy(str2, str1);               // str2 = "Hello"

// Concatenate
strcat(str2, " World");           // str2 = "Hello World"

// Compare
int cmp = strcmp(str1, "Hello");  // 0 if equal
if (cmp == 0) {
  Write("Strings match");
}

// Character access
char first = str1[0];             // 'H'
char last = str1[strlen(str1)-1]; // 'o'

// String modification
for (int i = 0; i < strlen(str1); i++) {
  str1[i] = str1[i] - 32;  // Convert to uppercase (ASCII)
}
```

### Q57: How do you convert between strings and numbers?
**A:**
```capl
// STRING TO NUMBER
int number = atoi("12345");           // "12345" -> 12345
float decimal = atof("3.14159");      // "3.14" -> 3.14159
int hex = atoi("FF");                 // Not hex! Use custom

// NUMBER TO STRING
char buffer[50];
sprintf(buffer, "%d", 42);            // 42 -> "42"
sprintf(buffer, "%X", 255);           // 255 -> "FF"
sprintf(buffer, "%.2f", 3.14159);     // -> "3.14"

// Format examples
sprintf(buffer, "Value: %d", 100);    // "Value: 100"
sprintf(buffer, "Hex: 0x%X", 255);    // "Hex: 0xFF"
sprintf(buffer, "Float: %.2f", 19.99); // "Float: 19.99"

// Validate number string
if (atoi("abc") == 0) {
  Write("Not a valid number");
}

// Multi-value formatting
int a = 10, b = 20;
sprintf(buffer, "Values: a=%d, b=%d", a, b);
```

### Q58: How do you handle string buffers safely?
**A:**
```capl
// Always allocate enough space
char small[10];
strcpy(small, "Hello");           // OK - 5 + null = 6 bytes
// strcpy(small, "This is way too long");  // OVERFLOW!

// Check string length before copy
char dest[20];
char src[] = "Source string";

if (strlen(src) < sizeof(dest)) {
  strcpy(dest, src);              // Safe
} else {
  Write("String too long!");
}

// Safe concatenation
char result[100];
strcpy(result, "Part1");

if (strlen(result) + strlen("Part2") < sizeof(result)) {
  strcat(result, "Part2");        // Safe
}

// Initialize strings
char buffer[50] = "";              // Start empty
char name[50] = {0};               // All zeros

// Be careful with format strings
char format[100];
sprintf(format, "Value: %d", 42);  // Use format string directly
// Don't use user input as format: sprintf(buffer, userInput);
```

### Q59: What are string functions available?
**A:**
```capl
char str1[50] = "Hello";
char str2[50] = "World";
char result[100];

// strlen - length
int len = strlen(str1);                    // 5

// strcpy - copy
strcpy(result, str1);                      // result = "Hello"

// strcat - concatenate
strcat(result, " ");
strcat(result, str2);                      // result = "Hello World"

// strcmp - compare
int cmp = strcmp(str1, "Hello");           // 0 = equal

// sprintf - format to string
sprintf(result, "%d + %d = %d", 2, 3, 5); // "2 + 3 = 5"

// atoi - string to int
int num = atoi("12345");                   // 12345

// atof - string to float
float fnum = atof("3.14");                 // 3.14

// Character checking
char c = 'A';
if (c >= 'A' && c <= 'Z') Write("Uppercase");
if (c >= 'a' && c <= 'z') Write("Lowercase");
if (c >= '0' && c <= '9') Write("Digit");
```

### Q60: How do you create a simple string buffer for data?
**A:**
```capl
// Byte buffer (CAN message data)
byte messageData[8];

// Copy from message
Message msg;
for (int i = 0; i < msg.DLC; i++) {
  messageData[i] = msg.Data[i];
}

// Extract values from buffer
byte status = messageData[0];
int value16 = (messageData[1] << 8) | messageData[2];
float temp = (float)messageData[3];

// Pack data into buffer
byte output[8];
output[0] = 0x42;
output[1] = (value16 >> 8) & 0xFF;
output[2] = value16 & 0xFF;
output[3] = (int)temp;

// String buffer with formatting
char dataStr[100];
sprintf(dataStr, "Status: 0x%02X, Value: %d, Temp: %.1f",
        status, value16, temp);

// Hex string from buffer
char hexStr[50];
hexStr[0] = 0;
for (int i = 0; i < 8; i++) {
  char hexByte[10];
  sprintf(hexByte, "%02X ", messageData[i]);
  strcat(hexStr, hexByte);
}
```

---

## EVENTS & TIMERS - Questions 61-70

### Q61: What are the main event types in CAPL?
**A:**
```capl
// SYSTEM EVENTS
on start {
  // Triggered once when measurement starts
}

on stop {
  // Triggered once when measurement stops
}

// MESSAGE EVENTS
on message * {
  // Every message
}

on message 0x100 {
  // Specific message ID
}

on message error {
  // CAN error frame
}

// TIMER EVENTS
timer myTimer;
on timer myTimer {
  // When timer expires
}

// KEYBOARD EVENTS
on key 'A' {
  // When 'A' key pressed
}

// ENVIRONMENT VARIABLE EVENTS
on SimVar SimulationSpeed {
  // When environment variable changes
}
```

### Q62: What is the on start event?
**A:**
```capl
int gMessageCount = 0;
timer gMonitorTimer;

on start {
  Write("========== Script Started ==========");
  
  // Initialize variables
  gMessageCount = 0;
  
  // Start timers
  SetTimer(gMonitorTimer, 1000);
  
  // Log startup
  Write("Monitoring started at %d ms", GetTime());
}

// Characteristics:
// - Executes ONCE at measurement start
// - Guaranteed to run before any other events
// - Best place for initialization
// - All globals already initialized to 0
// - Timers must be started here with SetTimer()

// Return: void
// Cannot return a value
```

### Q63: What is the on stop event?
**A:**
```capl
int gMessageCount = 0;
timer gMonitorTimer;

on stop {
  Write("========== Script Stopped ==========");
  
  // Cancel timers
  CancelTimer(gMonitorTimer);
  
  // Log statistics
  Write("Total messages: %d", gMessageCount);
  Write("Runtime: %d ms", GetTime());
  
  // Cleanup
  gMessageCount = 0;
}

// Characteristics:
// - Executes ONCE at measurement end
// - Last chance to save data
// - Should cancel all timers
// - Always use for cleanup
// - Variables remain in memory until stop
```

### Q64: How do you create and use timers?
**A:**
```capl
// Declare timer at global scope
timer gRecurringTimer;
timer gOneTimeTimer;

on start {
  // Start recurring timer (fires every X milliseconds)
  SetTimer(gRecurringTimer, 1000);      // Every 1000ms
  
  // Start one-time timer (fires once after X milliseconds)
  SetTimer(gOneTimeTimer, 5000);        // After 5000ms
}

// Handle recurring timer
on timer gRecurringTimer {
  Write("Recurring timer fired");
  // Continues to fire every 1000ms
}

// Handle one-time timer
on timer gOneTimeTimer {
  Write("One-time timer fired");
  // Stops automatically after firing once
}

// Stop a timer
on key 'S' {
  CancelTimer(gRecurringTimer);
  Write("Timer stopped");
}

// Restart timer
on key 'R' {
  CancelTimer(gRecurringTimer);
  SetTimer(gRecurringTimer, 1000);
  Write("Timer restarted");
}
```

### Q65: How do you measure elapsed time?
**A:**
```capl
dword gStartTime;

on start {
  gStartTime = GetTime();
  Write("Start time: %d ms", gStartTime);
}

// In event handler
on message 0x100 {
  dword elapsed = GetTime() - gStartTime;
  Write("Elapsed time: %d ms", elapsed);
  Write("Elapsed time: %.2f seconds", (float)elapsed / 1000);
}

// Periodic reporting
timer gReportTimer;
on timer gReportTimer {
  dword now = GetTime();
  dword elapsed = now - gStartTime;
  
  int minutes = elapsed / 60000;
  int seconds = (elapsed % 60000) / 1000;
  int milliseconds = elapsed % 1000;
  
  Write("Time: %d:%02d.%03d", minutes, seconds, milliseconds);
}

// Timeout detection
dword gLastMessageTime;

on message 0x100 {
  gLastMessageTime = GetTime();
}

on timer gMonitorTimer {
  dword now = GetTime();
  if ((now - gLastMessageTime) > 5000) {  // 5 second timeout
    Write("Message timeout!");
  }
}
```

### Q66: How do you pause execution?
**A:**
```capl
// Wait() pauses script execution
on key 'P' {
  Write("Waiting for 3 seconds...");
  Wait(3000);                    // Pause 3000ms
  Write("Resume!");
}

// Don't use Wait in frequently-called handlers
// Bad: Wait in timer
on timer gFastTimer {
  Wait(100);                    // BLOCKS other events!
}

// Good: Use separate timer for delayed action
timer gDelayedTimer;

on message 0x100 {
  SetTimer(gDelayedTimer, 100); // Delay, don't block
}

on timer gDelayedTimer {
  // Execute after delay
}

// Wait is useful for:
// - Startup sequences
// - Keyboard-triggered delays
// - One-time initialization
// NOT for frequent operations (causes lag)
```

### Q67: What is on key event?
**A:**
```capl
// Single character
on key 'A' {
  Write("Key 'A' pressed");
}

on key 'S' {
  Write("Key 'S' pressed");
}

// Numbers
on key '0' {
  Write("Number 0 pressed");
}

// Special keys
on key ' ' {
  Write("Spacebar pressed");
}

on key 'F1' {
  Write("F1 pressed");
}

on key 'Enter' {
  Write("Enter pressed");
}

// Common pattern - help menu
on key 'H' {
  Write("");
  Write("===== HELP =====");
  Write("P - Process");
  Write("S - Statistics");
  Write("R - Reset");
  Write("Q - Quit");
  Write("");
}

// Interactive script
int gMode = 0;

on key '1' {
  gMode = 1;
  Write("Mode 1");
}

on key '2' {
  gMode = 2;
  Write("Mode 2");
}

on key '3' {
  gMode = 3;
  Write("Mode 3");
}
```

### Q68: How do you handle multiple concurrent timers?
**A:**
```capl
timer gMonitorTimer;
timer gHeartbeatTimer;
timer gCleanupTimer;

on start {
  SetTimer(gMonitorTimer, 1000);    // Every 1 second
  SetTimer(gHeartbeatTimer, 5000);  // Every 5 seconds
  SetTimer(gCleanupTimer, 10000);   // Every 10 seconds
}

// Each timer has its own handler
on timer gMonitorTimer {
  Write("Monitor check");
  // Runs every 1 second
}

on timer gHeartbeatTimer {
  Write("♥ Heartbeat");
  // Runs every 5 seconds
}

on timer gCleanupTimer {
  Write("Cleanup");
  // Runs every 10 seconds
}

// Timeline:
// 0ms: All three start
// 1sec: Monitor fires
// 2sec: Monitor fires
// 3sec: Monitor fires
// 4sec: Monitor fires
// 5sec: Monitor + Heartbeat + ... ALL concurrent!
// 6sec: Monitor
// ...
// 10sec: Monitor + Heartbeat + Cleanup ALL together

// Stopping individual timers
on key 'M' {
  CancelTimer(gMonitorTimer);
  Write("Monitor stopped");
}

on key 'H' {
  CancelTimer(gHeartbeatTimer);
  Write("Heartbeat stopped");
}
```

### Q69: What are environment variable events (on SimVar)?
**A:**
```capl
// Declared in CANoe environment
int gEngineRPM;
float gTemperature;

// React to variable changes
on SimVar gEngineRPM {
  Write("Engine RPM changed: %d", gEngineRPM);
}

on SimVar gTemperature {
  Write("Temperature changed: %.1f", gTemperature);
}

// Usage: Connect to CANoe measurement setup
// CANoe updates these variables
// on SimVar handler executes whenever value changes

// Reading environment variables
on start {
  int initialRPM = GetEnvVarInt("EngineRPM");
  float initialTemp = GetEnvVarFloat("Temperature");
}

// Setting environment variables
void SetEngineParameters() {
  SetEnvVarInt("EngineRPM", 3000);
  SetEnvVarFloat("EngineTemperature", 95.5);
}

// Powerful for simulation integration
// Example: Hardware simulator controls variables
// CAPL script reacts to changes
```

### Q70: How do you combine multiple events?
**A:**
```capl
int gIsActive = 0;
timer gProcessTimer;

on start {
  gIsActive = 1;
  SetTimer(gProcessTimer, 1000);
}

// Message handler
on message 0x100 {
  if (!gIsActive) return;  // check state
  ProcessMessage();
}

// Timer handler
on timer gProcessTimer {
  if (!gIsActive) return;  // check state
  PeriodicWork();
}

// Keyboard to enable/disable
on key 'E' {
  gIsActive = 1;
  Write("Enabled");
}

on key 'D' {
  gIsActive = 0;
  Write("Disabled");
}

// Cascading events
Message triggerMsg;

on key 'T' {
  // Keyboard triggers message sending
  triggerMsg.ID = 0x100;
  triggerMsg.DLC = 2;
  triggerMsg.Data[0] = 0x01;
  Send(triggerMsg);
  // This also triggers on message * and on message 0x100!
}

on message * {
  // Also runs for messages sent by keyboard handler
}
```

---

## MESSAGE HANDLING - Questions 71-80

### Q71: What is the Message object in CAPL?
**A:**
```capl
on message 0x100 {
  // Message object 'this' contains:
  
  int id = this.ID;             // CAN ID (0x000-0x7FF)
  int dlc = this.DLC;           // Data length (0-8)
  dword time = this.Time;       // Timestamp in ms
  byte data[8];
  
  // Access data bytes
  for (int i = 0; i < dlc; i++) {
    data[i] = this.Data[i];
  }
  
  // Example values
  Write("ID: 0x%03X", this.ID);
  Write("DLC: %d bytes", this.DLC);
  Write("Data: %02X %02X %02X %02X", 
        this.Data[0], this.Data[1], 
        this.Data[2], this.Data[3]);
  Write("Received: %d ms", this.Time);
}
```

### Q72: How do you send a message?
**A:**
```capl
// Create message manually
Message msg;
msg.ID = 0x123;
msg.DLC = 3;
msg.Data[0] = 0x01;
msg.Data[1] = 0x02;
msg.Data[2] = 0x03;

Send(msg);              // Send the message

// Send zeros
Message zeroMsg;
zeroMsg.ID = 0x200;
zeroMsg.DLC = 8;
// All Data[i] = 0 by default

Send(zeroMsg);

// Send with pattern
Message patternMsg;
patternMsg.ID = 0x300;
patternMsg.DLC = 8;

for (int i = 0; i < 8; i++) {
  patternMsg.Data[i] = i;
}

Send(patternMsg);        // Sends 0,1,2,3,4,5,6,7

// Send periodically
timer gSendTimer;

on start {
  SetTimer(gSendTimer, 500);
}

on timer gSendTimer {
  Message msg;
  msg.ID = 0x100;
  msg.DLC = 2;
  msg.Data[0] = 0xAA;
  msg.Data[1] = 0xBB;
  Send(msg);
}
```

### Q73: How do you extract data bytes from a message?
**A:**
```capl
on message 0x100 {
  // Extract individual bytes
  byte byte0 = this.Data[0];
  byte byte1 = this.Data[1];
  
  // Extract 16-bit value (Big-endian)
  int value16 = (this.Data[0] << 8) | this.Data[1];
  
  // Extract 16-bit value (Little-endian)
  int value16_LE = this.Data[0] | (this.Data[1] << 8);
  
  // Extract 32-bit value (Big-endian)
  dword value32 = (this.Data[0] << 24) | 
                  (this.Data[1] << 16) |
                  (this.Data[2] << 8) | 
                  this.Data[3];
  
  // Extract with scaling
  int temperature = this.Data[2] - 40;      // Offset
  int pressure = this.Data[3] * 32;         // Scale
  
  // Extract bit fields
  byte status = this.Data[0] & 0x0F;       // Lower 4 bits
  byte flags = this.Data[0] >> 4;          // Upper 4 bits
  
  // Check specific bits
  if (this.Data[0] & 0x01) {
    Write("Bit 0 is set");
  }
}
```

### Q74: How do you pack data into a message?
**A:**
```capl
// Pack individual bytes
byte temperature = 85;
byte pressure = 45;

Message msg;
msg.ID = 0x150;
msg.DLC = 2;
msg.Data[0] = temperature;
msg.Data[1] = pressure;

Send(msg);

// Pack 16-bit value (Big-endian)
int value = 1000;
msg.ID = 0x200;
msg.DLC = 2;
msg.Data[0] = (value >> 8) & 0xFF;    // High byte
msg.Data[1] = value & 0xFF;           // Low byte

Send(msg);

// Pack 32-bit value (Big-endian)
dword largeValue = 0x12345678;
msg.ID = 0x300;
msg.DLC = 4;
msg.Data[0] = (largeValue >> 24) & 0xFF;
msg.Data[1] = (largeValue >> 16) & 0xFF;
msg.Data[2] = (largeValue >> 8) & 0xFF;
msg.Data[3] = largeValue & 0xFF;

Send(msg);

// Pack with bits
byte flags = 0;
flags |= 0x01;      // Set bit 0
flags |= 0x04;      // Set bit 2

msg.Data[0] = flags;
```

### Q75: What is on message error?
**A:**
```capl
int gErrorCount = 0;

on message error {
  gErrorCount++;
  Write("!!! CAN Error #%d !!!", gErrorCount);
  
  // Take action on error
  if (gErrorCount > 10) {
    Write("Too many errors - stopping");
    // Could stop measurement or take recovery action
  }
}

// Error types detected:
// - Bus off
// - Error frames
// - Protocol violations
// - Transmission errors
// - Receive errors

// Recovery strategy
on message error {
  Write("Error detected at %d ms", GetTime());
  Write("Error count: %d", ++gErrorCount);
  
  // Reset counter after timeout
  if (gErrorCount > 100) {
    gErrorCount = 0;
    Write("Error counter reset");
  }
}
```

### Q76: How do you handle on message * (all messages)?
**A:**
```capl
int gTotalMessages = 0;

on message * {
  // Runs for EVERY message on bus
  gTotalMessages++;
  
  // Count by ID
  if (this.ID == 0x100) {
    gCount0x100++;
  } else if (this.ID == 0x200) {
    gCount0x200++;
  }
}

on message 0x100 {
  // THIS ALSO RUNS (in addition to on message *)
  // on message * runs first, then on message 0x100
}

// Conditional processing
on message * {
  // Filter by DLC
  if (this.DLC != 8) {
    return;  // Skip non-8-byte messages
  }
  
  // Filter by ID range
  if (this.ID < 0x100 || this.ID > 0x2FF) {
    return;  // Only process 0x100-0x2FF
  }
  
  // Process filtered messages
  ProcessMessage();
}

// Common pattern: Count all, process specific
on message * {
  gAllMessageCount++;  // Global counter
}

on message 0x100 {
  gEngineCount++;      // Specific counter
  ProcessEngine();
}

on message 0x200 {
  gTransmissionCount++;
  ProcessTransmission();
}
```

### Q77: How do you filter messages by ID?
**A:**
```capl
// Specific IDs
on message 0x100 {
  Write("Engine status");
}

on message 0x200 {
  Write("Transmission status");
}

on message 0x300 {
  Write("Chassis data");
}

// Filter in generic handler
on message * {
  // Only process certain IDs
  switch (this.ID) {
    case 0x100:
      Write("Engine");
      break;
    case 0x200:
      Write("Transmission");
      break;
    default:
      return;  // Ignore others
  }
}

// Range filtering
on message * {
  if (this.ID >= 0x100 && this.ID <= 0x1FF) {
    Write("Engine range: 0x%X", this.ID);
  } else if (this.ID >= 0x200 && this.ID <= 0x2FF) {
    Write("Transmission range: 0x%X", this.ID);
  }
}
```

### Q78: How do you handle message timeouts?
**A:**
```capl
dword gLastEngineMessageTime = 0;
#define ENGINE_TIMEOUT 1000  // 1 second

on message 0x100 {
  gLastEngineMessageTime = GetTime();
  // Process message
}

// Check timeout in timer
timer gTimeoutCheck;

on start {
  SetTimer(gTimeoutCheck, 500);  // Check every 500ms
}

on timer gTimeoutCheck {
  dword now = GetTime();
  dword elapsed = now - gLastEngineMessageTime;
  
  if (elapsed > ENGINE_TIMEOUT) {
    Write("!!! Engine message timeout!");
    Write("Last message: %d ms ago", elapsed);
    
    // Take action
    // - Log error
    // - Stop processes
    // - Send alternate message
  }
}

// Multi-message timeout tracking
struct MessageStatus {
  dword lastTime;
  int timeout;
  char name[20];
};

// Better: Use separate timers for different messages
timer gEngineTimeoutTimer;
timer gTransTimeoutTimer;

on message 0x100 {
  CancelTimer(gEngineTimeoutTimer);
  SetTimer(gEngineTimeoutTimer, 1000);
}

on timer gEngineTimeoutTimer {
  Write("Engine message timeout!");
}
```

### Q79: How do you work with extended CAN IDs?
**A:**
```capl
// Standard CAN: 11-bit ID (0x000 - 0x7FF)
on message 0x100 {
  Write("Standard CAN ID");
}

// Extended CAN: 29-bit ID (0x00000000 - 0x1FFFFFFF)
on message 0x18FF1234 {
  Write("Extended CAN ID");
}

// Send extended format
Message extMsg;
extMsg.ID = 0x18FF1234;      // Large ID = extended
extMsg.DLC = 8;
extMsg.Data[0] = 0x01;
// ...

Send(extMsg);

// Detect format
on message * {
  if (this.ID > 0x7FF) {
    Write("Extended format: 0x%X", this.ID);
  } else {
    Write("Standard format: 0x%X", this.ID);
  }
}
```

### Q80: How do you implement a message gateway?
**A:**
```capl
// Gateway: Receive from Channel 1, transmit on Channel 2
on message Channel1.EngineData {
  // Receive from Channel 1
  Message msg;
  msg = EngineData;
  
  // Optionally modify
  msg.Data[0] = msg.Data[0] + 1;  // Example modification
  
  // Send on Channel 2
  output(Channel2, msg);
}

// Simple pass-through
on message * {
  // Forward all messages from input to output
  Message passMsg;
  passMsg = this;
  output(Channel2, passMsg);  // Send to Channel 2
}

// Selective gateway
on message 0x100 {
  // Only forward message 0x100
  output(Channel2, this);
}

on message 0x200 {
  // Transform before forwarding
  Message transformed;
  transformed.ID = this.ID;
  transformed.DLC = this.DLC;
  
  for (int i = 0; i < this.DLC; i++) {
    transformed.Data[i] = this.Data[i] ^ 0xFF;  // Invert
  }
  
  output(Channel2, transformed);
}
```

---

## ERROR HANDLING & VALIDATION - Questions 81-90

### Q81: How do you validate message DLC?
**A:**
```capl
on message 0x100 {
  // Check minimum DLC
  if (this.DLC < 4) {
    Write("Error: Invalid DLC %d (minimum 4)", this.DLC);
    return;
  }
  
  // Check exact DLC
  if (this.DLC != 8) {
    Write("Error: Expected DLC 8, got %d", this.DLC);
    return;
  }
  
  // Check maximum DLC (always <= 8)
  if (this.DLC > 8) {
    Write("Error: Invalid DLC %d", this.DLC);
    return;
  }
  
  // Valid - process
  ProcessMessage();
}

// Generic validation function
int ValidateDLC(Message msg, int expectedDLC) {
  if (msg.DLC != expectedDLC) {
    Write("Error: DLC mismatch");
    return 0;  // Invalid
  }
  return 1;    // Valid
}

// Usage
on message 0x100 {
  if (!ValidateDLC(this, 8)) {
    return;
  }
  ProcessMessage();
}
```

### Q82: How do you validate value ranges?
**A:**
```capl
// Range checking
int ValidateRange(int value, int min, int max) {
  if (value < min || value > max) {
    return 0;  // Invalid
  }
  return 1;    // Valid
}

on message 0x100 {
  int rpm = (this.Data[0] << 8) | this.Data[1];
  
  if (!ValidateRange(rpm, 0, 10000)) {
    Write("Error: RPM out of range: %d", rpm);
    gErrorCount++;
    return;
  }
  
  // Valid RPM - process
}

// Multiple field validation
on message 0x150 {
  if (this.DLC < 4) {
    Write("Invalid DLC");
    return;
  }
  
  int temp = this.Data[0];
  int pressure = this.Data[1];
  int speed = (this.Data[2] << 8) | this.Data[3];
  
  // Validate each field
  if (temp < -40 || temp > 125) {
    Write("Error: Temperature out of range");
    return;
  }
  
  if (pressure < 0 || pressure > 100) {
    Write("Error: Pressure out of range");
    return;
  }
  
  if (speed > 350) {
    Write("Error: Speed too high");
    return;
  }
  
  // All valid - process
  ProcessSensorData(temp, pressure, speed);
}
```

### Q83: How do you verify checksums?
**A:**
```capl
// Calculate simple checksum
byte CalculateChecksum(byte data[], int length) {
  byte checksum = 0;
  
  for (int i = 0; i < length; i++) {
    checksum += data[i];
  }
  
  // Return two's complement
  return (~checksum) + 1;
}

// Verify checksum
int VerifyChecksum(byte data[], int length) {
  byte calculated = CalculateChecksum(data, length - 1);
  byte received = data[length - 1];
  
  if (calculated == received) {
    return 1;  // Valid
  }
  return 0;    // Invalid
}

// Usage
on message 0x200 {
  byte msgData[8];
  
  // Copy message data
  for (int i = 0; i < this.DLC; i++) {
    msgData[i] = this.Data[i];
  }
  
  // Verify
  if (!VerifyChecksum(msgData, this.DLC)) {
    Write("Error: Checksum mismatch!");
    gErrorCount++;
    return;
  }
  
  // Valid - process
  ProcessMessage(msgData);
}

// CRC checksum (more complex)
word CalculateCRC(byte data[], int length) {
  word crc = 0xFFFF;
  
  for (int i = 0; i < length; i++) {
    crc ^= data[i];
    for (int j = 0; j < 8; j++) {
      if (crc & 0x0001) {
        crc = (crc >> 1) ^ 0xA001;
      } else {
        crc >>= 1;
      }
    }
  }
  
  return crc;
}
```

### Q84: How do you handle data consistency checks?
**A:**
```capl
// Consistency between multiple values
on message 0x300 {
  int speed = (this.Data[0] << 8) | this.Data[1];
  int acceleration = this.Data[2];
  int distance = (this.Data[3] << 8) | this.Data[4];
  
  // Check consistency: acceleration should match speed change
  dword now = GetTime();
  static dword lastTime = 0;
  static int lastSpeed = 0;
  
  if (lastTime > 0) {
    int timeDelta = now - lastTime;
    int speedDelta = speed - lastSpeed;
    
    // Calculate expected acceleration
    int expectedAccel = speedDelta / timeDelta;
    int tolerance = 2;
    
    if (abs(acceleration - expectedAccel) > tolerance) {
      Write("Warning: Acceleration inconsistent");
    }
  }
  
  lastTime = now;
  lastSpeed = speed;
}

// Track before/after state
int gLastStatus = 0;

on message 0x100 {
  int currentStatus = this.Data[0];
  
  // Check for impossible transitions
  if (gLastStatus == 1 && currentStatus == 3) {
    // Jumped from 1 to 3, missing 2
    Write("Warning: Skipped state");
  }
  
  gLastStatus = currentStatus;
}
```

### Q85: How do you implement error recovery?
**A:**
```capl
int gErrorCount = 0;
int gMaxErrors = 10;
int gIsRecovering = 0;

on message error {
  gErrorCount++;
  
  if (gErrorCount > gMaxErrors) {
    if (!gIsRecovering) {
      gIsRecovering = 1;
      Write("Starting error recovery...");
      // Attempt recovery
      ResetSystem();
    }
  }
}

void ResetSystem() {
  Write("Resetting system");
  
  // Stop operations
  CancelTimer(gProcessTimer);
  
  // Wait for system to stabilize
  Wait(1000);
  
  // Restart
  Message resetMsg;
  resetMsg.ID = 0x100;
  resetMsg.DLC = 2;
  resetMsg.Data[0] = 0x00;  // Reset command
  resetMsg.Data[1] = 0x01;
  
  Send(resetMsg);
  
  // Restart monitoring
  SetTimer(gProcessTimer, 1000);
  
  // Reset counters
  gErrorCount = 0;
  gIsRecovering = 0;
  
  Write("System recovered");
}

// Gradual degradation
on message error {
  gErrorCount++;
  
  if (gErrorCount > 5) {
    ReducedMode();    // Scale back operations
  }
  
  if (gErrorCount > 10) {
    SafeMode();       // Minimal operations only
  }
  
  if (gErrorCount > 20) {
    EmergencyStop();  // Stop everything
  }
}
```

### Q86: How do you log errors?
**A:**
```capl
// Simple logging
void LogError(char *message) {
  Write("ERROR: %s", message);
}

void LogWarning(char *message) {
  Write("WARNING: %s", message);
}

void LogInfo(char *message) {
  Write("INFO: %s", message);
}

// Usage
on message 0x100 {
  if (this.DLC < 4) {
    LogError("Message 0x100: Invalid DLC");
    return;
  }
  
  int value = (this.Data[0] << 8) | this.Data[1];
  
  if (value > 5000) {
    LogWarning("Value exceeds threshold");
  } else {
    LogInfo("Normal operation");
  }
}

// Timestamped logging
void LogWithTime(char *level, char *message) {
  Write("[%d ms] %s: %s", GetTime(), level, message);
}

// Structured logging
void LogMessageError(int id, int dlc, int expected) {
  Write("Message 0x%X: DLC error", id);
  Write("  Expected: %d bytes", expected);
  Write("  Got: %d bytes", dlc);
  Write("  Time: %d ms", GetTime());
}

// File-like logging
char gLogBuffer[1000];
int gLogIndex = 0;

void AddToLog(char *entry) {
  if (gLogIndex + strlen(entry) < sizeof(gLogBuffer)) {
    strcat(gLogBuffer, entry);
    strcat(gLogBuffer, "\n");
    gLogIndex = strlen(gLogBuffer);
  }
}
```

### Q87: How do you use asserts for validation?
**A:**
```capl
// Custom assert macro
#define ASSERT(condition, message) \
  if (!(condition)) { \
    Write("ASSERTION FAILED: %s", message); \
    return; \
  }

on message 0x100 {
  ASSERT(this.DLC == 8, "DLC must be 8");
  ASSERT(this.Data[0] != 0xFF, "Data[0] cannot be 0xFF");
  
  // If conditions fail, function returns early
  ProcessMessage();
}

// Assert with value
#define ASSERT_RANGE(value, min, max, message) \
  if ((value) < (min) || (value) > (max)) { \
    Write("ASSERT RANGE FAILED: %s (value=%d)", message, value); \
    return; \
  }

on message 0x200 {
  int speed = this.Data[0];
  ASSERT_RANGE(speed, 0, 200, "Speed out of range");
  
  // Only reached if speed in range
  ProcessSpeed(speed);
}
```

### Q88: How do you implement a state validation machine?
**A:**
```capl
#define STATE_INIT  0
#define STATE_IDLE  1
#define STATE_RUN   2
#define STATE_ERROR 3

int gCurrentState = STATE_INIT;
int gIsValidTransition = 1;

void TransitionToState(int newState) {
  // Check if transition is valid
  int valid = 0;
  
  switch (gCurrentState) {
    case STATE_INIT:
      if (newState == STATE_IDLE) valid = 1;
      break;
    case STATE_IDLE:
      if (newState == STATE_RUN || newState == STATE_ERROR) valid = 1;
      break;
    case STATE_RUN:
      if (newState == STATE_IDLE || newState == STATE_ERROR) valid = 1;
      break;
    case STATE_ERROR:
      if (newState == STATE_IDLE) valid = 1;
      break;
  }
  
  if (!valid) {
    Write("Invalid transition: %d -> %d", gCurrentState, newState);
    return;
  }
  
  gCurrentState = newState;
  Write("State changed to %d", newState);
}

on message 0x100 {
  if (gCurrentState != STATE_RUN) {
    Write("Message in wrong state");
    return;
  }
  ProcessMessage();
}
```

### Q89: How do you validate before sending?
**A:**
```capl
// Validate message before sending
int ValidateBeforeSend(Message msg) {
  // Check ID
  if (msg.ID < 0x100 || msg.ID > 0x7FF) {
    Write("Invalid message ID: 0x%X", msg.ID);
    return 0;
  }
  
  // Check DLC
  if (msg.DLC < 1 || msg.DLC > 8) {
    Write("Invalid DLC: %d", msg.DLC);
    return 0;
  }
  
  // Check data (optional)
  for (int i = 0; i < msg.DLC; i++) {
    if (msg.Data[i] == 0xFF) {  // Example: reject 0xFF
      Write("Invalid data at byte %d", i);
      return 0;
    }
  }
  
  return 1;  // Valid
}

// Usage
on key 'S' {
  Message msg;
  msg.ID = 0x100;
  msg.DLC = 2;
  msg.Data[0] = 0x42;
  msg.Data[1] = 0x43;
  
  if (ValidateBeforeSend(msg)) {
    Send(msg);
    Write("Message sent");
  } else {
    Write("Send failed validation");
  }
}
```

### Q90: How do you handle rare or edge cases?
**A:**
```capl
// Zero values
on message 0x100 {
  int value = this.Data[0];
  
  if (value == 0) {
    Write("Zero value - handle specially");
    // Could be invalid or special case
  }
}

// Maximum values
on message 0x200 {
  byte val = this.Data[0];
  
  if (val == 0xFF) {
    Write("Maximum value reached");
    // Could indicate overflow or special condition
  }
}

// Negative numbers (signed bytes)
byte signedByte = this.Data[0];
int signedInt = (int)signedByte;
if (signedByte > 127) {
  // Negative value
  signedInt = signedByte - 256;
}

// Division by zero
if (divisor != 0) {
  result = dividend / divisor;
} else {
  Write("Division by zero!");
  result = 0;
}

// Array boundary
int index = some_value;
if (index < 0 || index >= ARRAY_SIZE) {
  Write("Index out of bounds: %d", index);
  return;
}
value = array[index];

// Floating point issues
float f = 3.14;
float compare = 3.14000001;
if (abs(f - compare) < 0.0001) {
  Write("Values approximately equal");
}
```

---

## ADVANCED TOPICS - Questions 91-100

### Q91: What is the difference between Send() and output()?
**A:**
```capl
// Send() - transmits on current channel
Message msg;
msg.ID = 0x100;
msg.DLC = 2;
Send(msg);  // Uses current channel

// output() - transmits on specified channel
// Used in gateway/multi-channel scenarios
on message 0x100 {
  output(Channel2, this);  // Forward to Channel 2
}

// Practical example: Two-channel gateway
on message Channel1.Message0x100 {
  // Receive from Channel 1
  output(Channel2, this);   // Send to Channel 2
}

on message Channel2.Message0x200 {
  // Receive from Channel 2
  output(Channel1, this);   // Send to Channel 1
}
```

### Q92: How do you create a circular buffer?
**A:**
```capl
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
  return 0xFF;  // Error: empty
}

int BufferCount() {
  return gCount;
}

// Usage
on message 0x100 {
  for (int i = 0; i < this.DLC; i++) {
    BufferWrite(this.Data[i]);
  }
}

on timer gProcessTimer {
  while (BufferCount() > 0) {
    byte value = BufferRead();
    ProcessByte(value);
  }
}
```

### Q93: How do you implement a state machine with timeouts?
**A:**
```capl
#define STATE_WAIT  0
#define STATE_RUN   1
#define STATE_ERR   2
#define TIMEOUT_MS  5000

int gState = STATE_WAIT;
dword gStateStartTime = 0;
timer gTimeoutTimer;

void EnterState(int newState) {
  gState = newState;
  gStateStartTime = GetTime();
  
  switch (newState) {
    case STATE_WAIT:
      Write("Waiting for command...");
      SetTimer(gTimeoutTimer, TIMEOUT_MS);
      break;
    case STATE_RUN:
      Write("Running");
      SetTimer(gTimeoutTimer, TIMEOUT_MS);
      break;
    case STATE_ERR:
      Write("Error state");
      CancelTimer(gTimeoutTimer);
      break;
  }
}

on timer gTimeoutTimer {
  dword elapsed = GetTime() - gStateStartTime;
  Write("State timeout after %d ms", elapsed);
  
  switch (gState) {
    case STATE_WAIT:
      EnterState(STATE_ERR);
      break;
    case STATE_RUN:
      EnterState(STATE_ERR);
      break;
  }
}

on key 'S' {
  if (gState == STATE_WAIT) {
    EnterState(STATE_RUN);
  }
}
```

### Q94: How do you handle message acknowledgment?
**A:**
```capl
int gWaitingForAck = 0;
int gAckTimeout = 1000;
timer gAckTimer;

void SendWithAck(Message msg) {
  if (gWaitingForAck) {
    Write("Still waiting for ACK");
    return;
  }
  
  Write("Sending message with ACK wait...");
  gWaitingForAck = 1;
  Send(msg);
  
  SetTimer(gAckTimer, gAckTimeout);
}

on message 0x500 {  // ACK message
  if (gWaitingForAck) {
    CancelTimer(gAckTimer);
    gWaitingForAck = 0;
    Write("ACK received");
  }
}

on timer gAckTimer {
  if (gWaitingForAck) {
    Write("ACK timeout!");
    gWaitingForAck = 0;
    // Retry or error handling
  }
}

// Usage
on key 'S' {
  Message msg;
  msg.ID = 0x100;
  msg.DLC = 2;
  msg.Data[0] = 0x01;
  
  SendWithAck(msg);
}
```

### Q95: How do you implement a request-response pattern?
**A:**
```capl
int gWaitingForResponse = 0;
byte gExpectedResponseID = 0;
timer gResponseTimer;
#define RESPONSE_TIMEOUT 2000

void SendRequest(byte requestID) {
  if (gWaitingForResponse) {
    Write("Already waiting for response");
    return;
  }
  
  Message req;
  req.ID = 0x600;
  req.DLC = 1;
  req.Data[0] = requestID;
  
  Send(req);
  
  gWaitingForResponse = 1;
  gExpectedResponseID = requestID;
  SetTimer(gResponseTimer, RESPONSE_TIMEOUT);
  
  Write("Request sent (ID=%d), waiting for response...", requestID);
}

on message 0x700 {  // Response message
  if (gWaitingForResponse && this.Data[0] == gExpectedResponseID) {
    CancelTimer(gResponseTimer);
    gWaitingForResponse = 0;
    
    Write("Response received!");
    Write("Data: %02X %02X %02X %02X", 
          this.Data[1], this.Data[2], 
          this.Data[3], this.Data[4]);
  }
}

on timer gResponseTimer {
  if (gWaitingForResponse) {
    Write("Response timeout for request ID %d", gExpectedResponseID);
    gWaitingForResponse = 0;
    // Retry or error handling
  }
}
```

### Q96: How do you implement a queue-based system?
**A:**
```capl
#define QUEUE_SIZE 10

struct QueueItem {
  byte commandID;
  byte param1;
  byte param2;
};

QueueItem gQueue[QUEUE_SIZE];
int gQueueIn = 0;
int gQueueOut = 0;
int gQueueCount = 0;
int gProcessing = 0;
timer gQueueTimer;

void EnqueueCommand(byte cmd, byte p1, byte p2) {
  if (gQueueCount >= QUEUE_SIZE) {
    Write("Queue full!");
    return;
  }
  
  gQueue[gQueueIn].commandID = cmd;
  gQueue[gQueueIn].param1 = p1;
  gQueue[gQueueIn].param2 = p2;
  
  gQueueIn = (gQueueIn + 1) % QUEUE_SIZE;
  gQueueCount++;
  
  if (!gProcessing) {
    SetTimer(gQueueTimer, 100);  // Start processing
  }
}

on timer gQueueTimer {
  if (gQueueCount > 0 && !gProcessing) {
    gProcessing = 1;
    
    QueueItem item = gQueue[gQueueOut];
    gQueueOut = (gQueueOut + 1) % QUEUE_SIZE;
    gQueueCount--;
    
    ProcessCommand(item.commandID, item.param1, item.param2);
    
    gProcessing = 0;
    
    if (gQueueCount > 0) {
      SetTimer(gQueueTimer, 100);  // Process next
    }
  }
}

void ProcessCommand(byte cmd, byte p1, byte p2) {
  Write("Processing: cmd=0x%X, p1=0x%X, p2=0x%X", cmd, p1, p2);
}
```

### Q97: How do you work with bitmasks?
**A:**
```capl
// Define masks
#define FLAG_ACTIVE     0x01    // Bit 0
#define FLAG_ERROR      0x02    // Bit 1
#define FLAG_BUSY       0x04    // Bit 2
#define FLAG_WARNING    0x08    // Bit 3
#define MASK_STATUS     0x0F    // All status bits

byte gFlags = 0;

void SetFlag(byte mask) {
  gFlags |= mask;
}

void ClearFlag(byte mask) {
  gFlags &= ~mask;
}

int IsFlagSet(byte mask) {
  return (gFlags & mask) != 0;
}

void ToggleFlag(byte mask) {
  gFlags ^= mask;
}

// Usage
on message 0x100 {
  byte statusByte = this.Data[0];
  
  if (statusByte & FLAG_ACTIVE) {
    Write("Device is active");
  }
  
  if (statusByte & FLAG_ERROR) {
    Write("Error detected");
  }
  
  byte statusOnly = statusByte & MASK_STATUS;
  Write("Status field: 0x%X", statusOnly);
}

on key 'A' {
  SetFlag(FLAG_ACTIVE);
}

on key 'E' {
  SetFlag(FLAG_ERROR);
}

on key 'C' {
  ClearFlag(FLAG_ACTIVE);
  ClearFlag(FLAG_ERROR);
}
```

### Q98: How do you implement data aggregation?
**A:**
```capl
struct DataPoint {
  dword timestamp;
  int value;
};

#define SAMPLE_SIZE 100
DataPoint gSamples[SAMPLE_SIZE];
int gSampleIndex = 0;
int gSampleCount = 0;

void RecordSample(int value) {
  gSamples[gSampleIndex].timestamp = GetTime();
  gSamples[gSampleIndex].value = value;
  
  gSampleIndex = (gSampleIndex + 1) % SAMPLE_SIZE;
  if (gSampleCount < SAMPLE_SIZE) {
    gSampleCount++;
  }
}

int CalculateAverage() {
  if (gSampleCount == 0) return 0;
  
  int sum = 0;
  for (int i = 0; i < gSampleCount; i++) {
    sum += gSamples[i].value;
  }
  
  return sum / gSampleCount;
}

int FindMax() {
  if (gSampleCount == 0) return 0;
  
  int max = gSamples[0].value;
  for (int i = 1; i < gSampleCount; i++) {
    if (gSamples[i].value > max) {
      max = gSamples[i].value;
    }
  }
  return max;
}

int FindMin() {
  if (gSampleCount == 0) return 0;
  
  int min = gSamples[0].value;
  for (int i = 1; i < gSampleCount; i++) {
    if (gSamples[i].value < min) {
      min = gSamples[i].value;
    }
  }
  return min;
}

// Usage
on message 0x100 {
  int value = (this.Data[0] << 8) | this.Data[1];
  RecordSample(value);
}

on key 'S' {
  Write("Average: %d", CalculateAverage());
  Write("Max: %d", FindMax());
  Write("Min: %d", FindMin());
}
```

### Q99: How do you implement a simple state logger?
**A:**
```capl
#define LOG_SIZE 100

struct LogEntry {
  dword timestamp;
  char message[50];
  int value;
};

LogEntry gLog[LOG_SIZE];
int gLogIndex = 0;

void LogEvent(char *message, int value) {
  if (gLogIndex >= LOG_SIZE) {
    // Rotate or clear
    gLogIndex = 0;
  }
  
  gLog[gLogIndex].timestamp = GetTime();
  strcpy(gLog[gLogIndex].message, message);
  gLog[gLogIndex].value = value;
  
  gLogIndex++;
  
  // Also print immediately
  Write("[%d] %s: %d", gLog[gLogIndex-1].timestamp, message, value);
}

void DisplayLog() {
  Write("========== Event Log ==========");
  
  for (int i = 0; i < gLogIndex; i++) {
    Write("%d ms: %s (value=%d)", 
          gLog[i].timestamp,
          gLog[i].message,
          gLog[i].value);
  }
}

// Usage
on message 0x100 {
  LogEvent("Message 0x100 received", this.Data[0]);
}

on start {
  LogEvent("Script started", 0);
}

on key 'L' {
  DisplayLog();
}
```

### Q100: What tips improve CAPL script quality?
**A:**
```capl
// 1. USE MEANINGFUL NAMES
int gMessageCount;        // Good
int count;                // Bad
int gMsgCnt;             // Abbreviation ok

// 2. INITIALIZE VARIABLES
int gValue = 0;          // Good: initialized
int gValue;              // Bad: unclear initial state

// 3. VALIDATE EARLY
on message 0x100 {
  if (this.DLC < 4) return;      // Validate first
  // Process with confidence
}

// 4. USE CONSTANTS
const int TIMEOUT_MS = 5000;
SetTimer(gTimer, TIMEOUT_MS);    // Good

SetTimer(gTimer, 5000);          // Bad: magic number

// 5. DOCUMENT COMPLEX LOGIC
// Check if speed exceeds RPM threshold to prevent engine damage
if (speed > 200 && rpm > 7000) {
  // Take corrective action
}

// 6. SEPARATE CONCERNS
on message 0x100 {
  ProcessEngineMessage();           // Call function
}

void ProcessEngineMessage() {
  // Complex logic here
}

// 7. HANDLE ERRORS
if (divisor != 0) {
  result = numerator / divisor;
} else {
  err = 1;
}

// 8. USE FUNCTIONS FOR REPEATED CODE
int GetEngineRPM() {
  return (msg.Data[0] << 8) | msg.Data[1];
}

// 9. AVOID DEEPLY NESTED CONDITIONS
if (a) {
  if (b) {
    if (c) {  // Too deep
      doSomething();
    }
  }
}

// Better:
if (!a || !b || !c) return;
doSomething();

// 10. TEST EDGE CASES
// Zero values, min/max values, boundary conditions
```

---

## Final Tips

**Interview Successfully:**
1. Understand CAPL fundamentals deeply
2. Be able to write working code examples
3. Explain your code clearly
4. Ask clarifying questions
5. Show problem-solving approach
6. Mention best practices and error handling

**Master These Topics First:**
- Event handlers (on start, on message, on timer)
- Message structure (ID, DLC, Data[])
- Data types and operators
- String and array operations
- Error handling and validation
- State machines

**Practice Patterns:**
- Message sending/receiving
- Timer management
- Data extraction
- Validation
- Error handling
- Logging

Good luck with your CAPL interview!
