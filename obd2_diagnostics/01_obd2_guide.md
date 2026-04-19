# OBD-II Diagnostics Guide
## Emission Diagnostics | SAE J1979 | ISO 15031 | ELM327

---

## 1. OBD-II System Overview

OBD-II (On-Board Diagnostics II) is a standardized system that:
- Monitors emission-related vehicle systems
- Stores Diagnostic Trouble Codes (DTCs) when faults detected
- Exposes live sensor data via standardized PIDs
- Is accessible via the 16-pin OBD-II port (SAE J1962)

### Connector Pinout (SAE J1962 Type A)
```
  ┌───────────────────────────┐
  │ 1  2  3  4  5  6  7  8  │
  │ 9 10 11 12 13 14 15 16  │
  └───────────────────────────┘

Pin 4:  Chassis Ground
Pin 5:  Signal Ground  
Pin 6:  CAN High (ISO 15765-4)
Pin 14: CAN Low (ISO 15765-4)
Pin 16: Battery Voltage (+12V)
```

---

## 2. OBD-II Diagnostic Flow

```
Engine/Sensor Fault
        ↓
ECU detects out-of-range reading
        ↓
Runs readiness monitor (2 consecutive trips for confirmation DTCs)
        ↓
DTC stored (pending → confirmed)
        ↓
MIL (Check Engine Light) illuminated
        ↓
Technician connects scan tool to OBD-II port
        ↓
Uses Mode 03 to read DTCs
        ↓
Diagnoses and repairs fault
        ↓
Mode 04 to clear DTCs / MIL
        ↓
Drive cycle completes → readiness monitor passes
```

---

## 3. Mode Reference with Examples

### Mode 01 — Current Data
Request: `02 01 0C` (Length=2, Mode=01, PID=0C)
Response: `04 41 0C 1A F8` (Length=4, Mode+40=41, PID=0C, A=0x1A, B=0xF8)
RPM = (0x1A × 256 + 0xF8) / 4 = (26×256+248)/4 = 6904/4 = **1726 RPM**

### Mode 03 — Read DTCs
Request: `01 03` (no PID needed)
Response: `06 43 02 01 00 01 13 00`
- 0x43 = Mode 03 response (03+40)
- 0x02 = 2 DTCs
- DTC1: `01 00` → P0100 (MAF sensor)
- DTC2: `01 13` → P0113 (IAT sensor high)

### Mode 04 — Clear DTCs
Request: `01 04`
Response: `01 44` (positive, MIL cleared)

### Mode 09 — Vehicle Info
Request: `02 09 02` (VIN)
Response: Multi-frame ISO-TP message, 17 ASCII bytes

---

## 4. Important PIDs Quick Reference

```
Mode 01 PID → Decoding:

0x00 → Supported PIDs bitmap (PIDs 01–20)
0x01 → Monitor status (ready/incomplete flags)
0x04 → Engine Load      = A × 100/255         [%]
0x05 → Coolant Temp     = A − 40              [°C]
0x0B → Intake MAP       = A                   [kPa]
0x0C → Engine Speed     = (A×256+B) / 4       [RPM]
0x0D → Vehicle Speed    = A                   [km/h]
0x0E → Timing Advance   = A/2 − 64            [°BTDC]
0x0F → Intake Air Temp  = A − 40              [°C]
0x10 → MAF Rate         = (A×256+B) / 100     [g/s]
0x11 → Throttle Pos     = A × 100/255         [%]
0x1F → Run Since Start  = A×256+B             [sec]
0x21 → Distance w/MIL   = A×256+B             [km]
0x2F → Fuel Level       = A × 100/255         [%]
0x33 → Barometric Pres  = A                   [kPa]
0x45 → Relative Throttle= A × 100/255         [%]
0x46 → Ambient Temp     = A − 40              [°C]
0x5C → Oil Temperature  = A − 40              [°C]
```

---

## 5. ELM327 Interface — AT Commands

ELM327 is the most widely used OBD-II adapter chip (USB/Bluetooth/WiFi).

| Command | Description |
|---------|-------------|
| `ATZ` | Reset ELM327 |
| `ATE0` | Echo OFF |
| `ATL0` | Linefeed OFF |
| `ATH1` | Show CAN headers ON |
| `ATSP6` | Set Protocol: ISO 15765-4 CAN 500kbps 11-bit |
| `ATSP0` | Auto-select protocol |
| `0100` | Read supported PIDs (Mode 01, PID 00) |
| `010C` | Read Engine Speed |
| `010D` | Read Vehicle Speed |
| `03` | Read stored DTCs (Mode 03) |
| `04` | Clear DTCs (Mode 04) |
| `0902` | Read VIN (Mode 09, IOCTLID 02) |
| `ATDP` | Describe current protocol |
| `ATRV` | Read battery voltage |

### ELM327 Python (pyserial)
```python
import serial, time

ser = serial.Serial('/dev/ttyUSB0', 38400, timeout=1)

def elm_cmd(cmd):
    ser.write((cmd + '\r').encode())
    time.sleep(0.1)
    return ser.read(200).decode(errors='ignore').strip()

# Initialize
print(elm_cmd('ATZ'))    # Reset
print(elm_cmd('ATE0'))   # Echo off
print(elm_cmd('ATSP0'))  # Auto protocol

# Read RPM
resp = elm_cmd('010C')
# Response example: "41 0C 1A F8"
parts = resp.split()
if '41' in parts and '0C' in parts:
    idx = parts.index('0C')
    A, B = int(parts[idx+1], 16), int(parts[idx+2], 16)
    rpm = (A * 256 + B) / 4
    print(f"RPM: {rpm}")

ser.close()
```

---

## 6. python-OBD Library

```python
import obd

# Auto-detect OBD-II port
connection = obd.OBD()    # or obd.OBD("/dev/ttyUSB0")

# Check connection
print(connection.status())

# Query RPM
cmd = obd.commands.RPM
response = connection.query(cmd)
print(f"RPM: {response.value}")

# Query speed
response = connection.query(obd.commands.SPEED)
print(f"Speed: {response.value}")

# Query DTCs
response = connection.query(obd.commands.GET_DTC)
for dtc in response.value:
    print(f"DTC: {dtc[0]} — {dtc[1]}")

# Clear DTCs
connection.query(obd.commands.CLEAR_DTC)

connection.close()
```

---

## 7. DTC Code Lookup

### Common DTCs

| DTC | System | Description |
|-----|--------|-------------|
| P0100 | MAF | Mass Air Flow Circuit |
| P0113 | IAT | Intake Air Temp Sensor High |
| P0128 | Thermostat | Coolant temp below thermostat range |
| P0171 | Fuel | Fuel system too lean (bank 1) |
| P0300 | Misfire | Random/multiple cylinder misfire |
| P0301 | Misfire | Cylinder 1 misfire |
| P0420 | Catalyst | Catalyst efficiency below threshold (bank 1) |
| P0440 | EVAP | EVAP system malfunction |
| P0500 | VSS | Vehicle Speed Sensor |

### Code Decoding
```
P 0 1 0 0
│ │ │ └─┴─ Fault code (00–99)  
│ │ └───── Subsystem:
│ │        0=Fuel/Air, 1=Fuel/Air injector
│ │        2=Fuel/Air injector
│ │        3=Ignition, 4=Aux emission
│ │        5=Speed/Idle, 6=PCM I/O
│ │        7=Transmission, 8=Transmission
│ └─────── 0=Generic(SAE), 1=OEM-specific
└───────── P=Powertrain, C=Chassis, B=Body, U=Network
```

---

## 8. Interview Q&A

**Q: What is the difference between a pending and stored DTC?**
> A **pending DTC** (Mode 07) is set when a fault is detected once but not yet confirmed. A **stored/confirmed DTC** (Mode 03) is set after the fault is detected on two consecutive drive cycles. Only confirmed DTCs illuminate the MIL.

**Q: What are OBD-II readiness monitors?**
> Software routines inside the ECU that test emission-related systems (catalyst, EVAP, O2 sensors, EGR, etc.). They run during specific drive cycle conditions. Emission inspection stations check that all monitors show "Complete." Clearing DTCs (Mode 04) resets them to "Incomplete," requiring a drive cycle to complete them again.

**Q: Why can't Mode 04 clear Permanent DTCs (Mode 0A)?**
> Permanent DTCs were introduced to prevent emission-test fraud. Previously, technicians could clear DTCs just before an inspection. Permanent DTCs can only be cleared by the ECU after it has successfully run the relevant monitor and verified the fault is gone — Mode 04 has no effect on them.
