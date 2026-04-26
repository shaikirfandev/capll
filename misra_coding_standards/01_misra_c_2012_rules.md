# MISRA C:2012 — Comprehensive Guide for Automotive Engineers

---

## Table of Contents
1. [What Is MISRA C?](#what-is-misra-c)
2. [History and Editions](#history-and-editions)
3. [Rule Categories](#rule-categories)
4. [Essential Type Model](#essential-type-model)
5. [Top 30 MISRA C:2012 Rules](#top-30-misra-c2012-rules)
6. [MISRA C++ 2008 Key Rules](#misra-c-2008-key-rules)
7. [Deviations — How to Document Formally](#deviations)
8. [Static Analysis Tools](#static-analysis-tools)
9. [STAR Scenarios](#star-scenarios)
10. [Interview Q&A](#interview-qa)

---

## 1. What Is MISRA C?

**MISRA** = Motor Industry Software Reliability Association.

MISRA C is a set of software development guidelines for the C programming language developed by the MISRA consortium. Its primary purpose is to facilitate **code safety, security, portability, and reliability** in the context of embedded systems — particularly safety-critical automotive ECUs (Electronic Control Units).

### Why MISRA C Exists
The C language is powerful but was designed for system programming, not safety-critical embedded systems. It has:
- Undefined behaviours (hundreds of them per the ISO C standard)
- Implementation-defined behaviours that vary between compilers
- Unspecified behaviours that lead to non-portable code
- Language features that are error-prone (implicit type conversions, pointer arithmetic abuse)

MISRA C restricts or bans these dangerous features. The goal is NOT to make C "nicer" — it is to make C **predictable and auditable** for safety-critical applications such as:
- Braking systems (ABS, ESC)
- Airbag deployment
- ADAS (Advanced Driver Assistance Systems)
- Powertrain ECUs
- Battery Management Systems (BMS) in EVs

---

## 2. History and Editions

### MISRA C:1998 (First Edition)
- Published in 1998 by the MISRA consortium (originally formed by UK automotive companies: Jaguar, Ford, Lucas, Rover, Visteon, etc.)
- Targeted the C90 standard (ISO/IEC 9899:1990)
- 127 rules — all phrased as "shall" (required) or "should" (advisory)
- Widely adopted but had gaps and ambiguities
- Did not have the concept of "Mandatory" rules

### MISRA C:2004 (Second Edition)
- Published in 2004
- 141 rules (122 Required, 19 Advisory)
- Better organized into categories: Environment, Language Extensions, Documentation, Character sets, Identifiers, Types, Constants, Declarations, Initialization, Arithmetic, Pointer/Array, Structures, Functions, Memory, Input/Output, Control Flow, Switch, Preprocessor, Standard Libraries, Runtime
- Still targeted C90
- Became the dominant standard in production automotive code for a decade

### MISRA C:2012 (Third Edition — Current)
- Published in March 2012; Amendment 1 (Appendix D) added in 2016 covering C99 and C11 new rules; Amendment 2 added in 2020
- Adds support for C99 (ISO/IEC 9899:1999) and C11
- Introduces three-tier rule classification: **Mandatory**, **Required**, **Advisory**
- Introduces the **Essential Type Model** — a formal type model that replaces ad-hoc integer conversion rules
- 143 rules + 16 directives
- Rules are now numbered by section (e.g., Rule 10.3 = section 10, rule 3)
- Adds concept of **decidability** — static analysis tools can formally prove compliance
- Required in ISO 26262 ASIL B/C/D projects

### MISRA C++ :2008
- Parallel standard for C++03
- 228 rules
- Used for projects in C++ (infotainment, AUTOSAR adaptive platform)
- A new MISRA C++:2023 edition was published to cover C++14/17

### MISRA Compliance in Context
| Standard     | Applicable C Standard | Rules  | Used In                            |
|-------------|----------------------|--------|------------------------------------|
| MISRA C:1998 | C90                  | 127    | Legacy systems (1990s–2005)         |
| MISRA C:2004 | C90                  | 141    | Legacy automotive ECUs             |
| MISRA C:2012 | C90, C99, C11        | 143+16 | Current ASIL projects, ISO 26262   |
| MISRA C++:2008 | C++03              | 228    | Infotainment, AUTOSAR AP           |
| MISRA C++:2023 | C++14/17/20        | TBD    | Next-gen AUTOSAR AP, OTA, etc.     |

---

## 3. Rule Categories

MISRA C:2012 classifies every rule and directive into one of three categories:

### 3.1 Mandatory
- **Definition**: The rule **must** be followed. There is NO mechanism to deviate from it. Violations cannot be suppressed or justified under any circumstance.
- **Enforcement**: If a Mandatory rule is violated, the software is deemed **non-compliant with MISRA C:2012**, period.
- **Number of Mandatory rules in MISRA C:2012**: Very few (~10) — they cover absolute undefined behaviour
- **Example**: Rule 13.6 — the `sizeof` operator shall not be used on an expression that contains a side effect.

### 3.2 Required
- **Definition**: The rule **must** be followed **unless a formal documented deviation exists**.
- **Enforcement**: A deviation record must explain the rationale, safety justification, and compensating measures.
- **Most rules are Required** — about 107 of the 143 rules
- **Example**: Rule 14.4 — the controlling expression of an `if` statement shall be essentially Boolean.

### 3.3 Advisory
- **Definition**: The rule represents **best practice**. Non-compliance is noted but does not require a formal deviation.
- **Enforcement**: Should be followed where possible. Deviations are recommended to be documented informally.
- **Example**: Rule 2.7 — there should be no unused parameters in a function.

### Category Summary Table
| Category  | Must Follow?    | Deviation Allowed? | Typical Impact   |
|-----------|----------------|-------------------|-----------------|
| Mandatory | Always          | Never             | Safety-critical  |
| Required  | Yes             | Yes (formal)      | High importance  |
| Advisory  | Recommended     | Yes (informal)    | Best practice    |

### Decidability
Rules are also classified as:
- **Decidable**: A static analysis tool can determine compliance definitively
- **Undecidable**: Requires human judgment (e.g., evaluating whether a comment sufficiently documents a deviation)

---

## 4. Essential Type Model

The Essential Type Model (ETM) is one of the most important additions in MISRA C:2012. It defines a simplified type system that maps C types to a small set of "essential categories," then constrains how values of different categories interact.

### Essential Type Categories

| Category              | Description                                  | Example Types                     |
|-----------------------|----------------------------------------------|-----------------------------------|
| Essentially Boolean   | Only values 0 and 1 (TRUE/FALSE)             | `_Bool`, `bool` (stdbool.h)       |
| Essentially character | Character representation                     | `char`, `unsigned char`           |
| Essentially signed    | Signed integer arithmetic                    | `int8_t`, `int16_t`, `int32_t`    |
| Essentially unsigned  | Unsigned integer arithmetic                  | `uint8_t`, `uint16_t`, `uint32_t` |
| Essentially enum      | Named enumeration                            | Any `enum` type                   |
| Essentially floating  | Floating-point                               | `float`, `double`, `long double`  |

### Why the ETM Matters
C's implicit integer conversion rules (integer promotion, arithmetic conversion) can silently change the meaning of expressions. The ETM forces engineers to be explicit about type interactions:

```c
/* MISRA violation: mixing essentially signed and essentially unsigned */
int16_t  speed    = -50;
uint16_t distance = 100U;
int32_t  result   = speed + distance;  /* Rule 10.4 violation */

/* Compliant: explicit cast to make intention clear */
int32_t  result   = (int32_t)speed + (int32_t)distance;
```

### ETM-Related Rules (10.x series)
- Rule 10.1 — operands of certain operators shall be essentially Boolean
- Rule 10.2 — essentially character values shall not be used in the wrong context
- Rule 10.3 — the value of an expression shall not be assigned to a variable of a narrower essential type
- Rule 10.4 — both operands of an operator shall have the same essential type
- Rule 10.5 — the value of an expression should not be cast to an inappropriate essential type
- Rule 10.6 — the value of composite expression shall not be assigned to a wider essential type
- Rule 10.7 — if a composite expression is used as one operand of an operator, the other operand shall not be of a wider essential type
- Rule 10.8 — the value of a composite expression shall not be cast to a different essential type or a wider essential type

---

## 5. Top 30 MISRA C:2012 Rules

---

### Rule 1.3 — Undefined Behaviour
**Category**: Mandatory  
**Description**: There shall be no occurrence of undefined or critical unspecified behaviour.

```c
/* NON-COMPLIANT — signed integer overflow (undefined behaviour in C) */
int32_t sensor_value = INT32_MAX;
sensor_value = sensor_value + 1;  /* UB: signed overflow */

/* NON-COMPLIANT — null pointer dereference */
uint8_t *ptr = NULL;
*ptr = 0xFFU;  /* UB: dereference of null pointer */

/* COMPLIANT */
int32_t sensor_value = INT32_MAX;
if (sensor_value < INT32_MAX) {
    sensor_value = sensor_value + 1;
}
```
**Automotive Impact**: Undefined behaviour in ABS or airbag code can cause non-deterministic behaviour — the ECU might behave correctly during testing but fail unpredictably in the field.

---

### Rule 2.1 — Unreachable Code
**Category**: Required  
**Description**: A project shall not contain unreachable code.

```c
/* NON-COMPLIANT */
uint8_t get_fault_code(void)
{
    return 0x00U;
    (void)fault_check();  /* unreachable — never executes */
}

/* COMPLIANT */
uint8_t get_fault_code(void)
{
    uint8_t code = 0x00U;
    (void)fault_check();
    return code;
}
```
**Automotive Impact**: Dead branches after `return` statements can indicate logic errors. In safety-critical systems, code coverage requirements (MC/DC for ISO 26262 ASIL D) make unreachable code fail structural coverage targets.

---

### Rule 2.2 — Dead Code
**Category**: Required  
**Description**: There shall be no dead code (code that cannot affect the program's output).

```c
/* NON-COMPLIANT */
uint8_t speed_limit = 130U;
speed_limit = 130U;  /* dead assignment — immediately overwritten */
speed_limit = 120U;

/* NON-COMPLIANT */
uint8_t flag = 1U;
flag = flag | 0x00U;  /* dead operation — OR with 0 changes nothing */

/* COMPLIANT */
uint8_t speed_limit = 120U;
```

---

### Rule 2.4 — Unused Tags
**Category**: Advisory  
**Description**: A project should not contain unused tag declarations.

```c
/* NON-COMPLIANT */
struct unused_sensor_data {
    uint16_t velocity;
    uint16_t heading;
};
/* This struct is defined but never used anywhere */

/* COMPLIANT: either use it or remove it */
typedef struct {
    uint16_t velocity;
    uint16_t heading;
} SensorData_t;

static SensorData_t sensor = {0U, 0U};
```

---

### Rule 2.6 — Unused Labels
**Category**: Advisory  
**Description**: A function should not contain unused labels.

```c
/* NON-COMPLIANT */
void process_signal(void)
{
error_label:          /* label defined but never used with goto */
    signal_reset();
    return;
}

/* COMPLIANT: remove the unused label */
void process_signal(void)
{
    signal_reset();
    return;
}
```

---

### Rule 2.7 — Unused Parameters
**Category**: Advisory  
**Description**: There should be no unused parameters in a function.

```c
/* NON-COMPLIANT */
void set_throttle(uint8_t throttle_pct, uint8_t reserved_param)
{
    throttle_register = throttle_pct;
    /* reserved_param is never used */
}

/* COMPLIANT — explicitly cast to void to document intentional non-use */
void set_throttle(uint8_t throttle_pct, uint8_t reserved_param)
{
    (void)reserved_param;  /* intentionally unused — reserved for future use */
    throttle_register = throttle_pct;
}
```

---

### Rule 4.1 — Octal and Hex Escape Sequences
**Category**: Required  
**Description**: Octal and hexadecimal escape sequences shall be terminated.

```c
/* NON-COMPLIANT — escape sequence not terminated, ambiguous */
const char *msg = "\x41BC";  /* is 'B' part of the hex escape? */

/* COMPLIANT — use string concatenation to terminate escape */
const char *msg = "\x41" "BC";  /* clearly: hex 0x41 followed by "BC" */
```

---

### Rule 5.1 — External Identifiers Shall Be Distinct
**Category**: Required  
**Description**: External identifiers shall be distinct from other identifiers within the first 31 characters.

```c
/* NON-COMPLIANT */
extern uint16_t vehicle_speed_sensor_front_left_value;
extern uint16_t vehicle_speed_sensor_front_right_value;
/* Both are identical within first 31 characters! */

/* COMPLIANT */
extern uint16_t vss_front_left_kph;
extern uint16_t vss_front_right_kph;
```

---

### Rule 5.2 — Identifiers in the Same Scope
**Category**: Required  
**Description**: Identifiers declared within the same scope and namespace shall be distinct.

```c
/* NON-COMPLIANT */
void calc_speed(void)
{
    uint16_t speed  = 0U;
    uint16_t speedd = 0U;  /* similar to 'speed' — visual confusion */
}

/* COMPLIANT */
void calc_speed(void)
{
    uint16_t current_speed = 0U;
    uint16_t target_speed  = 0U;
}
```

---

### Rule 5.3 — Identifier Hiding
**Category**: Required  
**Description**: An identifier declared in an inner scope shall not hide an identifier declared in an outer scope.

```c
/* NON-COMPLIANT */
static uint16_t g_speed = 0U;  /* global */

void update_speed(void)
{
    uint16_t g_speed = 100U;  /* hides global! */
    process(g_speed);
}

/* COMPLIANT */
static uint16_t g_speed = 0U;

void update_speed(void)
{
    uint16_t local_speed = 100U;
    g_speed = local_speed;
}
```

---

### Rule 5.4 — Macro Identifiers
**Category**: Required  
**Description**: Macro identifiers shall be distinct.

```c
/* NON-COMPLIANT */
#define CAN_TIMEOUT_MS     100U
#define CAN_TIMEOUT_MS_MAX 200U  /* first 15 chars identical: CAN_TIMEOUT_MS */

/* COMPLIANT */
#define CAN_TX_TIMEOUT_MS  100U
#define CAN_RX_TIMEOUT_MS  200U
```

---

### Rule 7.1 — Octal Constants Shall Not Be Used
**Category**: Required  
**Description**: Octal constants shall not be used (except 0).

```c
/* NON-COMPLIANT */
uint8_t fault_code = 010U;  /* This is 8 in decimal, NOT 10! */
uint8_t mask       = 077U;  /* This is 63 in decimal */

/* COMPLIANT */
uint8_t fault_code = 8U;
uint8_t mask       = 0x3FU;  /* Use hex, which is unambiguous */
```
**Automotive Impact**: Octal 010 looks like decimal 10 to most readers. In a CAN ID mask calculation this would produce a catastrophic filtering error that is nearly invisible during code review.

---

### Rule 7.2 — Suffixes on Integer Literals
**Category**: Required  
**Description**: A "u" or "U" suffix shall be applied to all integer constants that are not negative.

```c
/* NON-COMPLIANT */
#define MAX_SPEED   250
#define CAN_TIMEOUT 100
uint32_t count = 0;

/* COMPLIANT */
#define MAX_SPEED   250U
#define CAN_TIMEOUT 100U
uint32_t count = 0U;
```
**Automotive Impact**: Without `U` suffix, the constant has a signed type. In comparisons with unsigned variables, the signed constant undergoes implicit conversion — potentially a source of wrap-around bugs.

---

### Rule 7.3 — Lowercase 'l' Suffix Prohibited
**Category**: Required  
**Description**: The lowercase letter "l" shall not be used as the suffix for integer constants (visually identical to '1').

```c
/* NON-COMPLIANT */
long timeout = 1000l;  /* Is that a lowercase 'l' or the number '1'? */

/* COMPLIANT */
long timeout = 1000L;
```

---

### Rule 7.4 — String Literal Assignment
**Category**: Required  
**Description**: A string literal shall not be assigned to an object unless the object's type is "pointer to const char."

```c
/* NON-COMPLIANT */
char *ecu_name = "ABS_CONTROLLER";  /* Modifying this pointer = UB */

/* COMPLIANT */
const char *ecu_name = "ABS_CONTROLLER";
```

---

### Rule 8.1 — Types Shall Be Explicitly Specified
**Category**: Required  
**Description**: Types shall be explicitly specified (implicit int is not allowed in C99/C11).

```c
/* NON-COMPLIANT (C90 implicit int) */
extern read_sensor();       /* return type implicitly int */
static g_fault_counter;     /* type implicitly int */

/* COMPLIANT */
extern int32_t read_sensor(void);
static int32_t g_fault_counter = 0;
```

---

### Rule 8.4 — Compatible Declarations
**Category**: Required  
**Description**: A compatible declaration shall be visible when an object or function with external linkage is defined.

```c
/* NON-COMPLIANT — definition without visible declaration */
/* sensor.c */
uint16_t g_wheel_speed = 0U;  /* no header declaration visible */

/* COMPLIANT */
/* sensor.h */
extern uint16_t g_wheel_speed;
/* sensor.c */
#include "sensor.h"
uint16_t g_wheel_speed = 0U;
```

---

### Rule 10.1 — Operands: Essential Boolean Context
**Category**: Required  
**Description**: Operands shall not be of an inappropriate essential type.

```c
/* NON-COMPLIANT — using arithmetic result where Boolean expected */
uint8_t speed = 60U;
if (speed & 0x01U) {   /* essentially unsigned in Boolean context */
    engage_odd_logic();
}

/* COMPLIANT */
uint8_t speed = 60U;
if ((speed & 0x01U) != 0U) {
    engage_odd_logic();
}
```

---

### Rule 10.3 — No Narrowing Assignments
**Category**: Required  
**Description**: The value of an expression shall not be assigned to an object with a narrower essential type or of a different essential type category.

```c
/* NON-COMPLIANT — 16-bit value assigned to 8-bit variable (narrowing) */
uint16_t raw_adc = 1023U;
uint8_t  scaled  = raw_adc;  /* truncation — top byte lost silently */

/* COMPLIANT */
uint16_t raw_adc = 1023U;
uint8_t  scaled  = (uint8_t)(raw_adc / 4U);  /* explicit scale and cast */
```
**Automotive Impact**: Silent truncation of an ADC sensor reading could make a 100% throttle reading appear as 75% — a dangerous fault in drive-by-wire systems.

---

### Rule 10.4 — Mixed Essential Types in Expressions
**Category**: Required  
**Description**: Both operands of an operator in which the usual arithmetic conversions are performed shall have the same essential type category.

```c
/* NON-COMPLIANT — signed + unsigned mix */
int16_t  temperature = -20;
uint16_t threshold   = 100U;
int32_t  delta       = temperature + threshold;  /* Rule 10.4 violation */

/* COMPLIANT */
int32_t  delta = (int32_t)temperature + (int32_t)threshold;
```

---

### Rule 10.8 — No Composite Expression Cast to Wider Type
**Category**: Required  
**Description**: The value of a composite expression shall not be cast to a different essential type or a wider essential type.

```c
/* NON-COMPLIANT */
uint8_t a = 200U;
uint8_t b = 100U;
uint32_t result = (uint32_t)(a + b);  /* addition overflows BEFORE cast */

/* COMPLIANT */
uint32_t result = (uint32_t)a + (uint32_t)b;  /* cast before operation */
```
**Automotive Impact**: In odometer or trip distance calculations, this pattern can silently truncate accumulated values leading to incorrect odometer readings.

---

### Rule 11.1 — Function Pointer Conversions
**Category**: Mandatory  
**Description**: Conversions shall not be performed between a pointer to a function and any other type.

```c
/* NON-COMPLIANT */
typedef void (*isr_handler_t)(void);
uint32_t *raw_ptr = (uint32_t*)can_rx_isr;  /* casting function pointer */

/* COMPLIANT */
isr_handler_t handler = can_rx_isr;
handler();
```

---

### Rule 11.3 — No Casting Between Pointer Types
**Category**: Required  
**Description**: A cast shall not be performed between a pointer to object type and a pointer to a different object type.

```c
/* NON-COMPLIANT */
uint32_t raw_register = 0xDEADBEEFU;
uint8_t *byte_ptr = (uint8_t*)&raw_register;  /* violates strict aliasing */

/* COMPLIANT — use a union or memcpy */
typedef union {
    uint32_t word;
    uint8_t  bytes[4];
} register_view_t;

register_view_t reg_view;
reg_view.word = 0xDEADBEEFU;
uint8_t first_byte = reg_view.bytes[0];
```

---

### Rule 11.5 — No void* to Object Pointer Conversion
**Category**: Advisory  
**Description**: A conversion should not be performed from pointer to void into pointer to object.

```c
/* NON-COMPLIANT */
void *generic_handle = get_sensor_handle();
SensorData_t *sensor = (SensorData_t*)generic_handle;

/* COMPLIANT — use typed interface */
SensorData_t *sensor = get_typed_sensor_handle();
```

---

### Rule 12.1 — Operator Precedence
**Category**: Advisory  
**Description**: The precedence of operators within expressions should be made explicit.

```c
/* NON-COMPLIANT — relies on precedence knowledge */
uint8_t result = a | b & c;   /* & binds tighter than | — confusing */
uint8_t flag   = x + y << 2; /* << has lower precedence than + */

/* COMPLIANT */
uint8_t result = a | (b & c);
uint8_t flag   = (x + y) << 2U;
```

---

### Rule 12.2 — Shift Operator Ranges
**Category**: Required  
**Description**: The right-hand operand of a shift operator shall lie in the range zero to one less than the width in bits of the essential type of the left-hand operand.

```c
/* NON-COMPLIANT */
uint8_t mask = 0x01U;
uint8_t shifted = mask << 8U;  /* shift by 8 on an 8-bit type = UB */

/* COMPLIANT */
uint16_t mask    = 0x0001U;
uint16_t shifted = mask << 8U;  /* shift range valid for 16-bit type */
```

---

### Rule 13.2 — Sequence Points and Side Effects
**Category**: Required  
**Description**: The value of an expression and its persistent side effects shall be the same under all permitted evaluation orders.

```c
/* NON-COMPLIANT — order of evaluation of function arguments is unspecified */
uint8_t buf[10];
uint8_t idx = 0U;
write_byte(buf, idx++, get_data(idx));  /* idx modified and read: UB */

/* COMPLIANT */
uint8_t data = get_data(idx);
write_byte(buf, idx, data);
idx++;
```

---

### Rule 13.5 — Logical AND/OR Short-Circuit Side Effects
**Category**: Required  
**Description**: The right-hand operand of a logical && or || shall not contain persistent side effects.

```c
/* NON-COMPLIANT */
if ((fault_count > 0U) && (fault_count-- != 0U)) {  /* side effect in RHS */
    handle_fault();
}

/* COMPLIANT */
if (fault_count > 0U) {
    fault_count--;
    handle_fault();
}
```

---

### Rule 14.4 — Controlling Expression Shall Be Essentially Boolean
**Category**: Required  
**Description**: The controlling expression of an `if` or iteration statement shall be essentially Boolean.

```c
/* NON-COMPLIANT */
uint8_t fault_flag = get_fault();
if (fault_flag) {        /* essentially unsigned used as Boolean */
    trigger_safe_state();
}
if (can_receive()) {     /* function returning int, not bool */
    process_frame();
}

/* COMPLIANT */
bool fault_active = (get_fault() != 0U);
if (fault_active) {
    trigger_safe_state();
}
if (can_receive() != 0) {
    process_frame();
}
```

---

### Rule 15.5 — Single Exit Point for Functions
**Category**: Advisory  
**Description**: A function should have a single point of exit at the end.

```c
/* NON-COMPLIANT */
uint8_t validate_speed(uint16_t speed_kph)
{
    if (speed_kph > MAX_SPEED) {
        return FAULT_OVERSPEED;   /* early return */
    }
    if (speed_kph == 0U) {
        return FAULT_ZERO_SPEED;  /* early return */
    }
    return NO_FAULT;
}

/* COMPLIANT */
uint8_t validate_speed(uint16_t speed_kph)
{
    uint8_t result;
    if (speed_kph > MAX_SPEED) {
        result = FAULT_OVERSPEED;
    } else if (speed_kph == 0U) {
        result = FAULT_ZERO_SPEED;
    } else {
        result = NO_FAULT;
    }
    return result;
}
```

---

### Rule 15.6 — Mandatory Braces for Loop/if Bodies
**Category**: Required  
**Description**: The body of an iteration/selection statement shall be a compound statement.

```c
/* NON-COMPLIANT */
if (fault_detected)
    trigger_safe_state();

for (i = 0U; i < 10U; i++)
    buffer[i] = 0U;

/* COMPLIANT */
if (fault_detected) {
    trigger_safe_state();
}

for (i = 0U; i < 10U; i++) {
    buffer[i] = 0U;
}
```
**Automotive Impact**: The Apple SSL "goto fail" security bug (2014) was caused by a violation of this exact rule — a duplicate goto statement was silently added because there were no braces.

---

### Rule 17.7 — Return Value Must Be Used
**Category**: Required  
**Description**: The value returned by a function having non-void return type shall be used.

```c
/* NON-COMPLIANT */
memcpy(dest, src, sizeof(dest));   /* return value ignored */
can_transmit(frame);                /* error code ignored */

/* COMPLIANT */
(void)memcpy(dest, src, sizeof(dest));  /* explicitly discard */
eStatus_t tx_status = can_transmit(frame);
if (tx_status != E_OK) {
    handle_tx_error();
}
```

---

### Rule 18.1 — Valid Pointer Arithmetic Range
**Category**: Required  
**Description**: A pointer resulting from arithmetic on a pointer operand shall address an element of the same array as that pointer operand.

```c
/* NON-COMPLIANT */
uint8_t buffer[8];
uint8_t *ptr = &buffer[0];
ptr = ptr + 10U;  /* pointer now out of bounds */
*ptr = 0xFFU;     /* UB: out-of-bounds write */

/* COMPLIANT */
uint8_t buffer[8];
uint8_t idx = 5U;
if (idx < sizeof(buffer)) {
    buffer[idx] = 0xFFU;
}
```

---

### Rule 21.3 — malloc/calloc/realloc/free Are Banned
**Category**: Required  
**Description**: The memory allocation and deallocation functions of <stdlib.h> shall not be used.

```c
/* NON-COMPLIANT — BANNED in MISRA */
SensorData_t *sensor = (SensorData_t*)malloc(sizeof(SensorData_t));
if (sensor != NULL) {
    process_sensor(sensor);
    free(sensor);  /* also banned */
}

/* COMPLIANT — use static allocation */
static SensorData_t sensor_pool[MAX_SENSORS];
static uint8_t      sensor_pool_index = 0U;

SensorData_t *allocate_sensor(void) {
    SensorData_t *ptr = NULL;
    if (sensor_pool_index < MAX_SENSORS) {
        ptr = &sensor_pool[sensor_pool_index];
        sensor_pool_index++;
    }
    return ptr;
}
```
**Why Banned**: Dynamic memory in embedded systems causes fragmentation and non-deterministic timing. In a real-time ABS controller, `malloc` taking 2ms extra due to heap fragmentation could mean the difference between stopping in time and a crash.

---

### Rule 22.1 — Dynamic Memory — No Allocation
**Category**: Required  
**Description**: All resources obtained dynamically shall be explicitly released. (In MISRA context: reinforces the ban on dynamic allocation; no dynamic memory means this rule is trivially satisfied.)

---

## 6. MISRA C++ :2008 Key Rules

MISRA C++:2008 applies to C++03. Key differences from MISRA C:2012:

| Rule             | Description                                          | Category  |
|------------------|------------------------------------------------------|-----------|
| Rule 0-1-1        | A project shall not contain unreachable code         | Required  |
| Rule 2-13-2       | Octal constants shall not be used                   | Required  |
| Rule 3-9-1        | Types shall be explicitly specified                  | Required  |
| Rule 5-0-5        | Signed/unsigned conversions explicit                 | Required  |
| Rule 6-4-1        | if/else shall use compound statements                | Required  |
| Rule 7-5-4        | Functions with no return type issues                 | Required  |
| Rule 8-4-4        | Function identifiers shall be used properly          | Required  |
| Rule 15-0-1       | Exceptions only for error handling (not flow control)| Document  |
| Rule 15-3-3       | Catch handlers shall be ordered from derived to base | Required  |
| Rule 17-0-5       | `setjmp`, `longjmp` shall not be used               | Required  |
| Rule 18-4-1       | Dynamic heap memory allocation shall not be used     | Required  |

**Additional MISRA C++ concerns not in MISRA C:**
- Templates with side effects in non-type parameters
- Virtual function calls in constructors/destructors
- Exception specifications (`throw()`)
- RTTI (`dynamic_cast`, `typeid`) usage in safety-critical paths

---

## 7. Deviations

A **deviation** is a documented, justified, and approved non-compliance to a Required rule. Mandatory rules cannot be deviated from.

### When a Deviation Is Needed
- Third-party library code that violates MISRA rules
- Hardware register access requiring pointer-type casts (Rule 11.3)
- Protocol implementations requiring specific integer behaviour
- Legacy code with justified non-compliance

### Deviation Permit vs. Deviation Record
- **Deviation Permit**: Pre-approved category of deviation (e.g., "All casts to hardware register addresses in the HAL layer are permitted under Rule 11.3")
- **Deviation Record**: Specific deviation for a specific piece of code

### Deviation Record Template

```
MISRA DEVIATION RECORD
======================
Project:          ABS_Controller_v3.2
ECU/Component:    Wheel Speed Sensor HAL
File:             hal_wss.c
Line(s):          143-147
Date:             2026-04-26
Author:           J. Smith
Approved by:      Safety Manager (countersignature required)

Rule Violated:    MISRA C:2012 Rule 11.3
Category:         Required
Description:      A cast shall not be performed between a pointer to
                  object type and a pointer to a different object type.

Violation Code:
  uint32_t *reg = (uint32_t*)WSS_BASE_ADDRESS;

Justification:
  Hardware register access requires casting an integer address constant
  to a typed pointer. This is the only way to access the WSS peripheral
  registers on the MCU (STM32G4). Alternative approaches (e.g., union
  overlays) are not possible as the registers are memory-mapped I/O, not
  RAM. The address WSS_BASE_ADDRESS is fixed by the MCU hardware design
  and documented in the hardware reference manual (REF-HW-001, sec 14.3).

Safety Argument:
  The address is a compile-time constant, verified against the MCU
  linker script. The cast is isolated to the HAL layer with no pointer
  arithmetic. The pointed-to type matches the register width (32-bit).
  This pattern is reviewed and used consistently across the HAL.

Compensating Measures:
  1. Static analysis (Polyspace) configured to suppress this suppression
     only for files matching hal_*.c
  2. Code review checklist item for HAL layer casts
  3. Unit tests cover register read/write paths (coverage: 100% statement)

References:
  - MCU HW Reference Manual: REF-HW-001, Section 14.3
  - AUTOSAR Memory Mapping Spec: AUTOSAR_SWS_MemoryMapping.pdf
  - ISO 26262-6:2018, Table 1 — code coverage at ASIL B
```

### Inline Suppression (Tool-specific)
Tools allow inline suppression comments for deviations. Examples:

```c
/* Helix QAC */
/* PRQA S 0306 1 */ /* Rule 11.3: Hardware register cast — see DR-2026-001 */
uint32_t *reg = (uint32_t*)WSS_BASE_ADDRESS;

/* Polyspace */
/* polyspace<MISRA-C3:11.3:Not a defect:Justified> Hardware reg access */
uint32_t *reg = (uint32_t*)WSS_BASE_ADDRESS;

/* PC-lint */
/*lint -e(923) Rule 11.3: Hardware register cast */
uint32_t *reg = (uint32_t*)WSS_BASE_ADDRESS;
```

---

## 8. Static Analysis Tools

### 8.1 Helix QAC (Formerly PRQA, now Perforce)
- **Industry standard** for MISRA compliance in automotive
- Deep dataflow analysis, rule traceability to MISRA text
- Generates compliance reports accepted by TÜV, Bureau Veritas, SGS
- Supports MISRA C:2012, MISRA C++:2008, CERT C, AUTOSAR C++14
- Integration: Jenkins CI/CD, Polarion, DOORS
- **Used by**: Bosch, Continental, ZF, Valeo, most Tier 1 suppliers
- Cost: Enterprise license (~€50k+/year)

### 8.2 Polyspace (MathWorks)
- Combines MISRA checking with **formal verification** (abstract interpretation)
- Can prove the **absence** of runtime errors (not just detect them)
- Tight integration with MATLAB/Simulink (model-based development)
- Code Prover (formal) + Bug Finder (fast heuristic)
- **Used by**: OEMs (BMW, Daimler) with Simulink-based development
- Cost: Part of MATLAB toolchain (~€15k–30k/year per seat)

### 8.3 LDRA (LDRA Ltd.)
- Long history in safety-critical industries (aerospace, automotive, medical)
- Covers MISRA + structural/MC/DC code coverage in one tool
- TBvision for static analysis, TBrun for unit test harness
- **Strengths**: Combined coverage + MISRA compliance
- **Used by**: Airbus, BAE Systems, automotive Tier 1s
- Cost: Mid-range enterprise

### 8.4 Klocwork (Perforce)
- Developer-focused: real-time analysis in IDE (Eclipse, VS Code plugins)
- Good for large codebases (millions of lines)
- MISRA C:2012 + security (CERT, CWE) analysis
- **Strengths**: Fast, CI/CD integration, security focus
- **Used by**: Large automotive OEMs, embedded Linux projects

### 8.5 PC-lint / PC-lint Plus (Gimpel Software)
- The oldest and most widely known C/C++ static analyser
- Command-line tool, very configurable
- MISRA C:2004, MISRA C:2012 rule sets available
- Cost: Much lower than enterprise tools (~$1k–2k)
- **Strengths**: Low cost, scriptable, fast
- **Limitation**: Less formal than QAC/Polyspace for certification reports

### Tool Selection Guide
| Scenario                              | Recommended Tool       |
|---------------------------------------|------------------------|
| ISO 26262 ASIL D formal compliance    | Helix QAC or Polyspace |
| MathWorks/Simulink-based code gen     | Polyspace              |
| Combined coverage + MISRA             | LDRA                   |
| Developer-integrated quick checks     | Klocwork               |
| Budget-constrained projects           | PC-lint Plus           |
| Open source projects                  | cppcheck (limited)     |

---

## 9. STAR Scenarios

### STAR 1: Critical Safety Bug Caused by a MISRA Violation

**Situation**: You are a software validation engineer at a Tier 1 supplier. Two weeks before Job 1 (start of production), a field test vehicle reports an intermittent ABS activation failure — the brakes are not modulating correctly at highway speed.

**Task**: Root-cause the ABS modulation failure and implement a fix within 72 hours without introducing regressions.

**Action**:
- Ran Helix QAC on the ABS wheel speed processing module — identified Rule 10.3 violation (narrowing conversion) in the slip ratio calculation
- Root cause: `uint32_t slip_ratio_scaled` was being assigned to `uint8_t slip_percent` without a range check. At highway speed, the slip ratio exceeded 255 — the uint8_t wrapped to a near-zero value, making the ABS controller think there was no slip, so it did not modulate
- The violation was flagged by QAC but had been marked as "advisory" in a previous review and not actioned
- Fix: Added explicit range check before the cast: `slip_percent = (slip_ratio_scaled > 100U) ? 100U : (uint8_t)slip_ratio_scaled`
- Added unit test covering the > 255 boundary condition
- Fast-tracked through MISRA compliance re-check and safety review

**Result**: Fix validated in HIL within 24 hours. No regressions. Delivered to vehicle test team on day 2. Root cause report submitted to safety manager. Rule 10.3 elevated from "advisory deviation" to "required — no deviation" in project MISRA compliance plan. Team training session on the ETM conducted the following week.

---

### STAR 2: MISRA Audit on a Legacy Codebase

**Situation**: Your company acquires a Tier 2 sensor fusion supplier. Their radar signal processing code (150,000 lines of C) must be integrated into your ASIL B project and pass MISRA C:2012 compliance audit in 3 months.

**Task**: Plan and execute a MISRA compliance uplift for the acquired codebase to reach a defined compliance level for ASIL B integration.

**Action**:
1. **Baseline scan**: Ran Helix QAC on the full codebase. Result: 14,327 violations. Breakdown: 23 Mandatory, 8,412 Required, 5,892 Advisory.
2. **Triage**: Focused on Mandatory violations first (23) — all fixed within week 1.
3. **Categorized Required violations** by rule:
   - Rule 10.x (ETM): 3,200 violations — assigned to 3 engineers, bulk of work
   - Rule 14.4 (non-Boolean controlling expressions): 1,800 violations — partially automated with script
   - Rule 15.6 (missing braces): 620 violations — auto-fixed by clang-format customization
   - Rule 17.7 (ignored return values): 440 violations — fixed by adding `(void)` casts or adding error handling
   - Rule 21.3 (malloc/free): 48 violations — redesigned memory management with static pools
4. **Formal deviations** created for 127 Rule 11.3 violations (hardware register casts) — all justified as peripheral access patterns
5. Re-ran QAC after 8 weeks: 312 Required violations remaining, 0 Mandatory
6. Remaining 312 violations either fixed or received formal deviation records before final audit

**Result**: Codebase achieved MISRA C:2012 compliance for ASIL B integration (0 unjustified Required violations, all Mandatory resolved). Audit passed by independent assessor (SGS-TÜV Saar). Integration completed on schedule.

---

### STAR 3: Justifying a Deviation for a Tier 1 Customer

**Situation**: You are the software technical lead at a Tier 2 supplier. A Tier 1 customer (Continental) raises a finding during a supplier audit: your CAN driver accesses FIFO registers using pointer arithmetic (Rule 18.1 potential violation), and they request either a code change or a formal deviation within 2 weeks.

**Task**: Evaluate the finding, decide whether to fix or deviate, and present the outcome to the customer's safety team.

**Action**:
- Reviewed the flagged code: the pointer arithmetic was bounded by the FIFO size (always accessed within `[0, FIFO_DEPTH-1]`), but QAC could not statically determine the bound
- Two options evaluated:
  1. **Refactor** to index-based access (no pointer arithmetic) — estimated 3 days + regression testing
  2. **Formal deviation** with proof of boundedness
- Chose refactoring as it was cleaner, removed the violation permanently, and avoided maintaining a deviation
- Rewrote 4 functions in the CAN FIFO driver to use array indexing instead of pointer arithmetic
- Added assert-style range checks (disabled in production via `NDEBUG`) and static analysis annotations
- Re-ran QAC: zero Rule 18.1 violations in the module
- Presented to Continental safety team: code change, Helix QAC report, unit test coverage report (100% branch)

**Result**: Customer audit finding closed. Continental's safety assessor approved the module without any open deviation records — a stronger compliance position than a deviation would have provided.

---

### STAR 4: MISRA in ISO 26262 Context

**Situation**: Your team is developing an ASIL C electric power steering (EPS) controller. The QMS (Quality Management System) requires demonstration of MISRA C:2012 compliance as a coding guideline per ISO 26262-6 Table 1.

**Task**: Define the MISRA compliance strategy for the project and integrate it into the development process (V-model).

**Action**:
1. **Defined compliance levels** per software component:
   - ASIL C software: Full MISRA C:2012 compliance — 0 unjustified Required violations, 0 Mandatory violations
   - QM (non-safety) software: MISRA C:2012 Required compliance, deviation count tracked
2. **Integrated QAC into CI/CD**: New violations introduced in a PR break the build. Legacy violations tracked in a declining metric
3. **Training**: All embedded C engineers completed MISRA C:2012 training (8 hours)
4. **Deviation process**: Defined in the Software Development Plan (SDP) — deviation requires safety manager + software lead sign-off, stored in DOORS
5. **Work Products created**:
   - MISRA Compliance Matrix (maps each rule to compliance status)
   - Deviation Permit Catalog (pre-approved deviation categories for hardware access)
   - Coding Guideline Document referencing MISRA C:2012 + project-specific additions
6. **Audit evidence**: QAC reports exported at each software release, stored in the project archive per ISO 26262-8 (supporting processes)

**Result**: ISO 26262 ASIL C certification audit by SGS-TÜV Saar passed with zero major findings related to MISRA compliance. The coding guideline and MISRA strategy were cited as best practices in the audit report.

---

### STAR 5: Code Review MISRA Checklist

**Situation**: Your team's code reviews are inconsistent — different reviewers catch different MISRA issues, and the QAC tool run only happens at the end of a sprint, making fixes expensive.

**Task**: Create a shift-left MISRA checklist to be used during code reviews so common violations are caught before the QAC gate.

**Action**: Developed and rolled out the following code review checklist:

```
MISRA C:2012 — Code Review Checklist (Automotive ECU)
======================================================

MANDATORY (zero tolerance):
[ ] No undefined behaviour (null deref, signed overflow, out-of-bounds)
[ ] sizeof not used on expressions with side effects (Rule 13.6)
[ ] No conversions between function pointers and other types (Rule 11.1)

TYPE SAFETY (ETM):
[ ] Integer literals have U/L suffixes (Rule 7.2, 7.3)
[ ] No octal constants except 0 (Rule 7.1)
[ ] All if/while/for conditions are explicitly Boolean (Rule 14.4)
[ ] No mixed signed/unsigned in expressions without cast (Rule 10.4)
[ ] No narrowing assignments without explicit cast (Rule 10.3)

CONTROL FLOW:
[ ] All if/for/while/do bodies use braces (Rule 15.6)
[ ] No unreachable code after return/break (Rule 2.1)
[ ] No unused variables, labels, parameters (Rules 2.2, 2.6, 2.7)
[ ] Switch: each case ends in break or /* fallthrough */ comment (Rule 16.3)
[ ] switch has a default case (Rule 16.4)

FUNCTIONS:
[ ] Return values of non-void functions are used or explicitly cast to (void) (Rule 17.7)
[ ] Functions have a prototype visible at definition (Rule 8.4)
[ ] No implicit function declarations (Rule 8.1)

POINTERS AND ARRAYS:
[ ] No pointer arithmetic that could go out of bounds (Rule 18.1)
[ ] No casts between pointer types (Rule 11.3) — or deviation record exists
[ ] No malloc/calloc/realloc/free (Rule 21.3)

PREPROCESSOR:
[ ] Macro arguments parenthesized (Rule 20.7)
[ ] No #undef (Rule 20.5)
[ ] #include only contains file names, not expressions (Rule 20.3)

GENERAL:
[ ] All identifiers distinct in first 31 chars (Rule 5.1)
[ ] No identifier hiding outer scope (Rule 5.3)
[ ] Operator precedence made explicit with parentheses (Rule 12.1)
```

**Result**: Within one sprint cycle, QAC violation count in new code dropped by 68%. Defect escape rate to the QAC gate fell from an average of 12 violations per PR to under 2. Engineers reported faster code reviews with clearer feedback.

---

## 10. Interview Q&A

**Q1: What is the difference between Mandatory, Required, and Advisory rules in MISRA C:2012?**

**A**: Mandatory rules must always be followed — there is no mechanism for deviation regardless of justification. Violations of Mandatory rules make the software non-compliant with MISRA C:2012. Required rules must also be followed but allow formal documented deviations when technically justified. Advisory rules represent best practice; non-compliance should be noted but does not require formal deviation documentation.

---

**Q2: Why is `malloc` banned in MISRA C?**

**A**: Dynamic memory allocation (`malloc`, `calloc`, `realloc`, `free`) is banned under Rule 21.3 for several reasons: (1) heap fragmentation can cause non-deterministic memory allocation timing, violating real-time constraints; (2) allocation failure (NULL return) introduces complex error paths that are easy to miss; (3) dangling pointers and use-after-free are common causes of undefined behaviour; (4) embedded ECUs typically have no memory protection unit (MPU) separating heap regions. Static allocation provides deterministic memory usage that can be analysed at compile time.

---

**Q3: Explain the Essential Type Model and why it was introduced in MISRA C:2012.**

**A**: The Essential Type Model (ETM) provides a simplified taxonomy of C types — essentially Boolean, character, signed integer, unsigned integer, enum, and floating — and rules for how values of these categories can interact. It was introduced because C's implicit arithmetic conversions (integer promotion, usual arithmetic conversion) silently change types in ways that cause bugs. For example, comparing an `int16_t` and a `uint16_t` may yield unexpected results due to sign extension or value wrapping. The ETM forces engineers to be explicit: mixing essentially signed and essentially unsigned values in an expression is a Rule 10.4 violation and must be resolved with an explicit cast that documents intent.

---

**Q4: What is a MISRA deviation and what must a deviation record contain?**

**A**: A deviation is a documented, justified, and approved non-compliance to a Required rule. It cannot be applied to Mandatory rules. A deviation record must contain: the specific rule number violated, the exact code or pattern causing the violation, a technical justification for why compliance is not feasible or would introduce greater risk, compensating measures that reduce the risk of the violation, references to supporting evidence (hardware manuals, standards), and approval signatures (typically software lead + safety manager).

---

**Q5: Can MISRA C:2012 rules be applied to auto-generated code (e.g., from MATLAB Simulink or AUTOSAR tooling)?**

**A**: Yes, and this is a common challenge. Code generators like Embedded Coder produce MISRA-compliant output when the correct configuration is applied (MISRA compliance mode in Embedded Coder). However, generated code often has specific patterns (fixed naming conventions, use of global variables) that trigger advisory violations. The standard approach is to apply a bulk deviation permit for the generated code layer (e.g., "All files matching *_data.c are generated — Rule X.Y violations are permitted under DP-GEN-001") and focus manual MISRA compliance on hand-written integration and calibration layers.

---

**Q6: Rule 15.5 advises a single point of exit from functions. Is this always practical?**

**A**: Rule 15.5 is Advisory, not Required. The single-exit principle improves readability and makes it easier to ensure cleanup code (e.g., releasing mutex locks, resetting state) always runs. However, in complex validation functions with many early-exit conditions, forcing a single return can lead to deeply nested `if`/`else` chains that are harder to read. The practical MISRA approach is to prefer single-exit where it does not significantly harm readability, and to document deviations (informally, since it is Advisory) where multiple returns genuinely improve clarity.

---

**Q7: What is Rule 13.2 about? Give an automotive example of the bug it prevents.**

**A**: Rule 13.2 addresses expressions whose value depends on the order of evaluation of side effects. C's standard does not define the order in which function arguments are evaluated or side effects within an expression take effect (between sequence points). A real example: `write_can_buffer(tx_buf, byte_index++, encode_byte(byte_index))` — the pre-increment of `byte_index` and its use as an argument to `encode_byte` have unspecified evaluation order. If `encode_byte` is called first (with the old index) the result is different than if `byte_index++` executes first. This could corrupt a CAN frame being transmitted, causing an incorrectly assembled UDS diagnostic response — a real bug class in CAN driver implementations.

---

**Q8: How does MISRA C:2012 relate to ISO 26262?**

**A**: ISO 26262-6:2018, Table 1 (Design and coding guidelines) lists the use of a language subset (such as MISRA C) as a **highly recommended** practice for ASIL B and **recommended** for ASIL C/D. In practice, most automotive safety assessors expect full MISRA C:2012 compliance for ASIL C/D software. MISRA C compliance is part of the "coding guidelines" work product required by ISO 26262-6. It does not replace other requirements (functional correctness, coverage testing, architectural design) but contributes to the software's structural correctness argument in the Safety Case.

---

**Q9: What is the difference between Rule 2.1 (unreachable code) and Rule 2.2 (dead code)?**

**A**: Unreachable code (Rule 2.1) is code that can never be executed because of the control flow — e.g., statements after an unconditional `return` or `break`, or an `else` branch that is mathematically impossible. Dead code (Rule 2.2) is code that can be executed but has no effect on the program's outputs — e.g., a variable assignment whose value is then immediately overwritten without being read, or `x | 0` (ORing with zero). Both represent wasted code that obscures intent, inflates binary size, and interferes with code coverage targets.

---

**Q10: Why are octal constants specifically banned (Rule 7.1)?**

**A**: Octal constants in C are written with a leading zero: `0177` is decimal 127, not 177. This notation is extremely easy to misread — `0100` is decimal 64, not 100. In embedded C code, constants for register masks, CAN IDs, and bitmaps are common. A developer writing `uint8_t mask = 011;` intending to write 11 decimal will actually assign the value 9. This bug is nearly invisible in code review and does not cause a compiler warning. The only safe constants with leading zero are `0` itself and hex constants (`0x...`).

---

**Q11: How would you handle a third-party CAN stack that has many MISRA violations?**

**A**: The standard approach is: (1) quantify the violations using a static analysis tool; (2) assess the safety relevance of each violation — violations in code paths that affect safety-relevant signals need more scrutiny; (3) contact the vendor to request a MISRA-compliant version or ask for their deviation records; (4) if vendor compliance is not possible, create a Deviation Permit covering the third-party module with the rationale that the library is externally supplied, its behaviour is validated by system-level tests, and it is isolated by a defined interface; (5) document this in the Safety Case. The key is that the deviation must be approved, documented, and architecturally isolated.

---

**Q12: What does Rule 17.7 (return value must be used) impose on C standard library calls?**

**A**: Many C standard library functions return error codes or output values that programmers commonly ignore: `fclose()`, `fwrite()`, `memcpy()` (returns destination pointer), `strtol()` (sets errno), etc. Rule 17.7 requires that the return value is either used (checked for errors) or the developer explicitly documents the discard with `(void)funcname(...)`. In automotive ECU code, ignoring `NvM_WriteBlock()` return codes could mean a critical calibration value was not persisted to non-volatile memory — a serious data integrity failure.

---

**Q13: What is the "safe integer" challenge that the MISRA ETM addresses?**

**A**: C's integer promotion rules mean that operations on small integer types (`uint8_t`, `int16_t`) are first promoted to `int` (typically 32-bit signed). This can silently change the essential type of a value mid-expression. For example, `uint8_t a = 200U; uint8_t b = 100U; int result = a - b;` — the subtraction is performed on promoted `int` values, so result is +100, not -12 (which would occur if the subtraction wrapped in uint8_t). The ETM rules (10.1–10.8) force the programmer to be explicit about type widening and mixing, making the intended arithmetic clear.

---

**Q14: What MISRA rules are specifically relevant to switch statements?**

**A**: Section 16 of MISRA C:2012 covers switch statements. Key rules: Rule 16.1 (switch shall not be poorly formed), Rule 16.2 (only switch labels at top level of switch), Rule 16.3 (an unconditional break shall terminate every non-empty switch clause — prevents unintentional fallthrough), Rule 16.4 (every switch statement shall have a default label), Rule 16.5 (default label shall appear as the last case label), Rule 16.6 (every switch shall have at least 2 switch-clauses), Rule 16.7 (if a switch condition can only be one value, use if-else instead). In CAN protocol parsers and UDS service dispatchers, switch statements are ubiquitous — these rules are very commonly violated and very commonly checked.

---

**Q15: How do you demonstrate MISRA compliance to a customer or assessor?**

**A**: Demonstration of MISRA compliance typically includes: (1) a **MISRA Compliance Matrix** mapping each of the 143 rules + 16 directives to its status (Compliant / Deviated / Not Applicable) for the project; (2) **Static analysis tool reports** (e.g., Helix QAC HTML/PDF report) showing violation counts by rule, with evidence of zero unjustified Required violations and zero Mandatory violations; (3) **Deviation Records** for all approved deviations, with safety manager signatures; (4) the **Coding Guideline Document** that references MISRA C:2012 and defines project-specific rule interpretations; (5) evidence of **engineer training** on MISRA C:2012; (6) integration of MISRA checking in the **CI/CD pipeline** (gate check before merge). Together these form the MISRA compliance argument in the Safety Case per ISO 26262-6.

---

*End of File — MISRA C:2012 Comprehensive Guide*  
*Total coverage: Rules 1.x through 22.x, ETM, Deviations, Tools, STAR Scenarios, 15 Interview Q&A*
