# CAPL Data Structures Guide
## Complete Reference for Arrays, Structs, Associative Arrays & More

---

## Overview

CAPL supports the following data structures:

| Structure | Support | Notes |
|---|---|---|
| **Arrays (1D / 2D)** | ✅ Native | Fixed size, 0-indexed |
| **Structs** | ✅ CANoe 10+ | `struct` keyword |
| **Associative Arrays** | ✅ CAPL-unique | Key-value map, dynamic size |
| **Strings** | ✅ char arrays | Null-terminated |
| **Enumerations** | ⚠️ Simulated | Use `const int` constants |
| **Pointers** | ❌ Not supported | No dynamic memory |
| **Linked Lists / Trees** | ❌ Not supported | No heap allocation |
| **Classes / Objects** | ❌ Not supported | No OOP |

---

## 1. Arrays

### 1D Arrays
```capl
byte   gRawBytes[8]     = {0x10, 0x03, 0x00, 0x00, 0xCC, 0xCC, 0xCC, 0xCC};
int    gSensorValues[5] = {100, 200, 300, 400, 500};
float  gTemps[4]        = {25.5, 37.0, -10.0, 100.0};
char   gLabel[32]       = "EngineECU";
```

### 2D Arrays
```capl
byte gMatrix[3][4];   // 3 rows, 4 columns (row-major)

// Fill
int r, c;
for (r = 0; r < 3; r++)
  for (c = 0; c < 4; c++)
    gMatrix[r][c] = (r * 4) + c;
```

### Key Array Functions

| Function | Description |
|---|---|
| `elCount(arr)` | Returns compile-time array length |
| Manual loop | No built-in `memcpy` / `memset` in basic CAPL |

### Common Array Operations
```capl
// Safe iteration using elCount()
for (i = 0; i < elCount(buf); i++)
  write("buf[%d] = 0x%02X", i, buf[i]);

// Copy
void CopyByteArray(byte src[], byte dst[], int len)
{
  int i;
  for (i = 0; i < len; i++)
    dst[i] = src[i];
}

// Linear search
int FindValue(int arr[], int len, int target)
{
  int i;
  for (i = 0; i < len; i++)
    if (arr[i] == target) return i;
  return -1;
}

// Bubble sort (ascending)
void SortIntArray(int arr[], int len)
{
  int i, j, tmp;
  for (i = 0; i < len - 1; i++)
    for (j = 0; j < len - i - 1; j++)
      if (arr[j] > arr[j+1])
      {
        tmp      = arr[j];
        arr[j]   = arr[j+1];
        arr[j+1] = tmp;
      }
}

// Average
float ArrayAverage(int arr[], int len)
{
  int i;
  float sum = 0.0;
  for (i = 0; i < len; i++)
    sum += arr[i];
  return (len > 0) ? (sum / len) : 0.0;
}
```

---

## 2. Structs

Requires **CANoe 10+**. Use `struct` keyword to group related data.

### Declaration
```capl
struct DTCRecord
{
  long  dtcCode;
  byte  statusByte;
  float odometerKm;
  char  description[64];
};

struct CANFrame
{
  long id;
  byte dlc;
  byte data[8];
};
```

### Usage
```capl
// Single instance
struct DTCRecord gLastDTC;

// Array of structs
struct DTCRecord gDTCList[10];
int              gDTCListCount = 0;

// Access members
gLastDTC.dtcCode    = 0xC0200;
gLastDTC.statusByte = 0x09;
gLastDTC.odometerKm = 12345.0;
strncpy(gLastDTC.description, "Engine Speed Sensor", 63);
```

### Struct Functions Example
```capl
// Add DTC to list
int AddDTC(long code, byte status, float odo, char desc[])
{
  if (gDTCListCount >= 10)
  {
    write("!! DTC list full");
    return -1;
  }
  gDTCList[gDTCListCount].dtcCode    = code;
  gDTCList[gDTCListCount].statusByte = status;
  gDTCList[gDTCListCount].odometerKm = odo;
  strncpy(gDTCList[gDTCListCount].description, desc, 63);
  gDTCListCount++;
  return gDTCListCount - 1;
}

// Print all DTCs
void PrintAllDTCs()
{
  int i;
  for (i = 0; i < gDTCListCount; i++)
    write("DTC: 0x%06X | Status: 0x%02X | Odo: %.1f km | %s",
          gDTCList[i].dtcCode,
          gDTCList[i].statusByte,
          gDTCList[i].odometerKm,
          gDTCList[i].description);
}
```

---

## 3. Associative Arrays (CAPL-Unique)

CAPL's most powerful data structure — a **dynamic key-value map** with no fixed size limit.

### Declaration Syntax
```capl
type  name[key_type];
```

| Key Type | Example | Use Case |
|---|---|---|
| `long` | `int count[long]` | DTC code → count |
| `int` | `float value[int]` | Message ID → float |
| `char` | `float sig[char]` | Signal name → value |

### Basic Operations
```capl
// Declare
int   gDTCCount[long];    // key = DTC code
float gSignal[char];      // key = signal name string

// Write
gDTCCount[0xC0200] = 3;
gSignal["VehicleSpeed"]  = 120.5;
gSignal["EngineRPM"]     = 3200.0;

// Read
write("Speed: %.1f", gSignal["VehicleSpeed"]);

// Increment existing
gDTCCount[0xC0200]++;

// Check if key exists
if (isvalid(gDTCCount[0xC0200]))
  write("Key exists");

// Delete a key
del(gSignal["VehicleSpeed"]);

// Count entries
write("Total entries: %d", elCount(gSignal));
```

### Key Associative Array Functions

| Function | Description |
|---|---|
| `isvalid(map[key])` | Returns 1 if key exists, 0 if not |
| `del(map[key])` | Removes the key-value pair |
| `elCount(map)` | Returns current number of entries |

### Real-World Example — Message Timeout Tracker
```capl
variables
{
  float  gLastRxTime[long];  // key=msg ID, value=last receive time
  int    gRxCount[long];     // key=msg ID, value=count
}

on message *
{
  gLastRxTime[this.id] = timeNow() / 100000.0;
  gRxCount[this.id]++;
}

on key 's'
{
  write("Received %d unique message IDs", elCount(gRxCount));
}
```

---

## 4. Enumerations (Simulated with const int)

CAPL has **no native `enum` keyword**. Use `const int` constants instead.

```capl
variables
{
  const int STATE_OFF     = 0;
  const int STATE_STANDBY = 1;
  const int STATE_ACTIVE  = 2;
  const int STATE_FAULT   = 3;

  int gECUState = 0;
}

// Helper
char* StateToString(int state)
{
  switch (state)
  {
    case 0: return "OFF";
    case 1: return "STANDBY";
    case 2: return "ACTIVE";
    case 3: return "FAULT";
    default: return "UNKNOWN";
  }
}

void TransitionState(int newState)
{
  write("State: %s --> %s",
        StateToString(gECUState),
        StateToString(newState));
  gECUState = newState;
}
```

---

## 5. Strings (char Arrays)

Strings in CAPL are **null-terminated character arrays**.

### Declaration
```capl
char gName[32]  = "Engine_ECU";
char gBuffer[128];
```

### String Functions

| Function | Description | Example |
|---|---|---|
| `strlen(s)` | Returns string length | `strlen("hello")` → 5 |
| `strcpy(dst, src)` | Copy string | `strcpy(dst, src)` |
| `strncpy(dst, src, n)` | Copy max n chars | `strncpy(dst, src, 31)` |
| `strcat(dst, src)` | Append string | `strcat(dst, " v2")` |
| `strcmp(a, b)` | Compare (0 = equal) | `if (strcmp(a,b)==0)` |
| `snprintf(dst, n, fmt, ...)` | Formatted string | `snprintf(buf, 64, "RPM=%d", rpm)` |
| `atoi(s)` | String to int | `atoi("42")` → 42 |
| `atof(s)` | String to float | `atof("3.14")` → 3.14 |

### Example
```capl
char src[32] = "Hello, Automotive!";
char dst[32];
char info[64];

// Copy
strcpy(dst, src);

// Append
strcat(dst, " v2");

// Compare
if (strcmp(src, dst) != 0)
  write("Strings differ");

// Format into string
snprintf(info, elCount(info),
         "Speed=%.1f RPM=%d", 120.5, 3200);
write("%s", info);
```

---

## 6. Quick Reference Summary

```
Type              Declaration Example             Key Notes
────────────────  ────────────────────────────   ─────────────────────────────
1D Array          byte buf[8];                   Fixed size, use elCount()
2D Array          byte m[3][4];                  Row-major indexing
String            char name[32] = "ECU_1";       Null-terminated char array
Struct            struct Rec { int x; char s[]; } CANoe 10+, member via .
Assoc Array       int map[long];                  CAPL-unique, dynamic, isvalid/del
Enum (simulated)  const int A=0, B=1;            No native enum keyword
```

### `elCount()` vs `sizeof()`

| | `elCount(arr)` | `sizeof(arr)` |
|---|---|---|
| Returns | **Number of elements** | Bytes occupied |
| Works on | Arrays & assoc arrays | Variables & arrays |
| At runtime for assoc | Current entry count | — |
| Recommended for loops | ✅ Yes | ❌ Can cause off-by-one |

---

## 7. Practical Patterns

### Pattern 1 — Lookup Table (const array)
```capl
// Map gear position number to string
char gGearNames[9][16] = {
  "Park", "1st", "2nd", "3rd", "4th",
  "5th",  "6th", "Reverse", "Neutral"
};

write("Current gear: %s", gGearNames[gGearPos]);
```

### Pattern 2 — Ring Buffer (circular array)
```capl
variables
{
  int  gLogBuf[16];
  int  gHead = 0;
  int  gCount = 0;
}

void LogPush(int val)
{
  gLogBuf[gHead % elCount(gLogBuf)] = val;
  gHead++;
  if (gCount < elCount(gLogBuf)) gCount++;
}

int LogPeekLatest()
{
  return gLogBuf[(gHead - 1) % elCount(gLogBuf)];
}
```

### Pattern 3 — Message Statistics (struct + assoc array)
```capl
struct MsgStat
{
  int   count;
  float minVal;
  float maxVal;
};

struct MsgStat gStats[long];  // key = message ID

on message *
{
  long id = this.id;
  gStats[id].count++;
}
```

---

*See also: [script_21_data_structures.capl](script_21_data_structures.capl) for runnable examples of all structures above.*
