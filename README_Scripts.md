# 15 CAPL Scripts - Learning Collection

This collection contains 15 carefully designed CAPL scripts that progressively teach different aspects of CAPL programming, from basic concepts to advanced real-world patterns.

## Quick Reference Guide

### Script 01: Hello World (Basics)
**File:** `script_01_hello_world.capl`

The simplest CAPL script. Demonstrates:
- Basic output using `Write()` function
- `on start` event handler
- `on stop` event handler
- Script lifecycle

**Learn:** How to output text and understand script execution flow

---

### Script 02: Data Types and Variables (Fundamentals)
**File:** `script_02_data_types.capl`

Complete overview of all data types in CAPL:
- Primitive types: `byte`, `word`, `dword`, `int`, `float`, `double`, `char`
- String handling with character arrays
- Variable declaration and initialization
- Type conversion and casting
- Format specifiers in `Write()` (%d, %f, %x, etc.)

**Learn:** What data types are available and how to use them correctly

---

### Script 03: Operators (Arithmetic & Logic)
**File:** `script_03_operators.capl`

All operator categories:
- Arithmetic operators: +, -, *, /, %
- Comparison operators: ==, !=, <, >, <=, >=
- Logical operators: &&, ||, !
- Bitwise operators: &, |, ^, ~, <<, >>
- Assignment operators: +=, -=, *=, /=, etc.
- Increment/decrement: ++, --
- Ternary operator: ? :

**Learn:** How to use operators for calculations and decision-making

---

### Script 04: Control Flow (If-Else & Switch)
**File:** `script_04_control_flow.capl`

Conditional statement patterns:
- Simple `if` statements
- `if-else` chains
- Nested conditional logic
- `switch` statements with cases
- Default case handling
- Break statement in switch

**Learn:** How to make decisions in code based on conditions

---

### Script 05: Loops (For, While, Do-While)
**File:** `script_05_loops.capl`

All loop types and techniques:
- Standard `for` loops with initialization, condition, increment
- Backwards looping
- Multi-variable for loops
- `while` loops
- `do-while` loops (executes at least once)
- `break` statement to exit loops
- `continue` statement to skip iterations
- Nested loops
- Array iteration

**Learn:** How to repeat code blocks and iterate over data

---

### Script 06: Functions (Definition & Parameters)
**File:** `script_06_functions.capl`

Function programming concepts:
- Function declaration and definition
- Parameters and return values
- Pass by value
- Pass by reference (arrays)
- Function prototypes
- Recursive functions (Factorial, Fibonacci)
- Helper functions

**Learn:** How to write reusable code with functions

---

### Script 07: Arrays and Strings (Data Structures)
**File:** `script_07_arrays.capl`

Working with collections:
- One-dimensional arrays
- Two-dimensional arrays
- Array initialization
- Array access and modification
- Array searching
- Array sorting (bubble sort example)
- String functions: `strlen()`, `strcpy()`, `strcat()`, `strcmp()`
- String manipulation

**Learn:** How to store and work with multiple values

---

### Script 08: Timers and Timing (Time Management)
**File:** `script_08_timers.capl`

Timer-based programming:
- `SetTimer()` to start timers
- `on timer` event handlers
- `CancelTimer()` to stop timers
- `GetTime()` for timestamps
- `Wait()` for delays
- Recurring timers vs one-time timers
- Timer monitoring and control

**Learn:** How to create time-based events and measure elapsed time

---

### Script 09: Receiving CAN Messages (Message Input)
**File:** `script_09_receive_messages.capl`

Message reception techniques:
- `on message *` to catch all messages
- `on message ID` for specific IDs
- Message structure: `ID`, `DLC` (Data Length Code), `Data[]`, `Time`
- Message filtering and validation
- Data extraction from message bytes
- Bit field analysis
- Message statistics and counting
- Error frame handling

**Learn:** How to receive and process CAN messages

---

### Script 10: Sending CAN Messages (Message Output)
**File:** `script_10_send_messages.capl`

Message transmission patterns:
- Message structure setup
- Setting ID, DLC, and data bytes
- `Send()` function
- Periodic message sending with timers
- Data formatting and byte packing
- Multi-byte value transmission
- Sensor data encoding
- Test pattern generation
- Keyboard-triggered sending

**Learn:** How to create and send CAN messages

---

### Script 11: String Operations (Text Manipulation)
**File:** `script_11_string_operations.capl`

String handling in depth:
- Basic string functions: `strlen()`, `strcpy()`, `strcat()`, `strcmp()`
- `sprintf()` for string formatting
- Number to string conversion
- String to number conversion: `atoi()`, `atof()`
- Character manipulation
- Case conversion (uppercase/lowercase)
- String building and concatenation
- String validation

**Learn:** How to work with text and format data

---

### Script 12: Bitwise Operations (Binary Manipulation)
**File:** `script_12_bitwise.capl`

Bit-level programming:
- Bitwise operators: AND (&), OR (|), XOR (^), NOT (~)
- Bit shifting: << (left), >> (right)
- Setting individual bits
- Clearing individual bits
- Checking individual bits
- Bit masking techniques
- Multi-byte bit operations
- Bit flags and status bytes
- Visual binary representation

**Learn:** How to manipulate individual bits and flags

---

### Script 13: Data Validation (Error Checking)
**File:** `script_13_validation.capl`

Input and data verification:
- Range validation (ensuring values are within acceptable bounds)
- Checksum calculation and verification
- Data consistency checks
- Message length validation
- Sequence validation
- Error reporting patterns
- Recovery strategies

**Learn:** How to validate data and detect errors

---

### Script 14: State Machine Implementation (Complex Logic)
**File:** `script_14_state_machine.capl`

State-based programming patterns:
- State definitions using constants
- Valid state transitions
- Transition validation
- Entry actions (executed on entering state)
- Exit actions (executed on leaving state)
- State-specific behavior
- Transition logging
- Keyboard-controlled state changes
- State machine diagram (in comments)

**Learn:** How to build systems that move between different states

---

### Script 15: Multiplexed Messages (Advanced protocols)
**File:** `script_15_multiplexed.capl`

Handling complex message protocols:
- Multiplexer-based message parsing
- Different data structures for same message ID
- Routing based on multiplexer value
- Multi-byte value extraction
- Sensor data decoding
- Complex message protocol handling
- Message statistics by type
- Test message generation

**Learn:** How to handle sophisticated CAN protocols with multiple message types

---

## Learning Path Recommendation

### Beginner Level
Start with scripts in this order to build fundamental understanding:
1. **script_01_hello_world.capl** - Get your first script running
2. **script_02_data_types.capl** - Understand available data types
3. **script_03_operators.capl** - Learn calculation and logic
4. **script_04_control_flow.capl** - Make decisions in code
5. **script_05_loops.capl** - Repeat operations

### Intermediate Level
Build practical programming skills:
6. **script_06_functions.capl** - Organize code with functions
7. **script_07_arrays.capl** - Work with collections
8. **script_08_timers.capl** - Master time-based events
9. **script_11_string_operations.capl** - Handle text data

### Intermediate+ Level
Apply knowledge to CAN messaging:
10. **script_09_receive_messages.capl** - Learn message reception
11. **script_10_send_messages.capl** - Learn message transmission
12. **script_12_bitwise.capl** - Master bit-level work (needed for CAN)

### Advanced Level
Tackle complex real-world patterns:
13. **script_13_validation.capl** - Add robustness with validation
14. **script_14_state_machine.capl** - Build sophisticated systems
15. **script_15_multiplexed.capl** - Handle advanced protocols

---

## How to Use These Scripts

### In CANoe/CANalyzer:

1. **Import a script:**
   - Right-click on "CAPL Programs" in the Configuration
   - Select "New Test" or "Add CAPL Program"
   - Browse and select one of the script files

2. **Run the script:**
   - Start the measurement/simulation
   - Watch the output in the "Trace" or "Output" window

3. **Interact with the script:**
   - Use keyboard commands (press various keys like 'S', 'M', 'P', etc.)
   - Check the script comments for available commands

4. **Study the code:**
   - Read the comments at the top of each script
   - Review the comments throughout the code
   - Observe the output to understand what's happening

### Tips for Learning:

- **Run one at a time** - Pick a script and run it to completion
- **Modify the code** - Change values, add print statements, experiment
- **Combine concepts** - Once you understand individual scripts, start combining techniques
- **Compare approaches** - Look at different scripts to see multiple ways to solve problems
- **Always check output** - Use `Write()` statements liberally to understand execution flow

---

## Common Keyboard Commands Across Scripts

Some scripts support keyboard interaction. Try these common keys:

| Key | Common Use |
|-----|-----------|
| 'S' | Statistics or Status |
| 'H' | Help |
| 'P' | Pause or Pressure |
| 'R' | Run or Resume |
| 'M' | Send Message |
| 'E' | Error or Engine |
| 'T' | Test or Temperature |
| 'C' | Clear counters or Current state |
| 'Q' | Quit |
| 'X' | Extended format |
| 'Z' | Test patterns |

Check individual script headers for specific keyboard bindings.

---

## Key Concepts Summary

### Data Organization
- Scripts 1-3: Basic concepts
- Scripts 6-7: Collections and functions
- Scripts 11-12: Text and binary data

### Control Flow
- Scripts 4-5: Conditional and repetitive logic
- Script 14: Complex state-based logic

### Real-Time Events
- Script 8: Timer-based events
- Scripts 9-10: Message-based events

### Data Processing
- Scripts 9-15: Receiving, validating, and transforming data

### Best Practices
- Use comments (see all scripts)
- Organize code logically (see script 14)
- Validate inputs (see script 13)
- Handle errors gracefully (see scripts 13-14)

---

## Next Steps After Learning These 15 Scripts

1. **Combine multiple scripts** - Create a script that sends and receives messages with timer events
2. **Use your vehicle data** - Replace example values with real CAN data from your system
3. **Database integration** - Use .dbc files to work with predefined message definitions
4. **Advanced features** - Explore environment variables, signal definitions, and advanced CANoe features
5. **Refer to the main guide** - Cross-reference these scripts with `CAPL_Learning_Guide.md` for detailed explanations

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Script won't load | Check syntax errors, ensure proper brackets |
| No output visible | Enable Trace window, check `Write()` output |
| Timer not firing | Call `SetTimer()` before `on timer` handler |
| Message not sending | Verify DLC is set and message structure is complete |
| Data looks wrong | Check byte order (big-endian vs little-endian) and scaling factors |

---

Good luck with your CAPL learning journey! Start with script 01 and work your way through the collection.
