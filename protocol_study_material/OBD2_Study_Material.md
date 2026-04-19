# OBD-II (On-Board Diagnostics) Study Material
## SAE J1979 / ISO 15031 – Emission Diagnostic Protocol

---

## 1. Overview

**OBD-II** is a standardized vehicle self-diagnostic system mandatory in:
- USA since **1996** (EPA requirement)
- EU since **2001** (petrol) / **2004** (diesel) — known as EOBD

OBD-II communicates via the **16-pin OBD-II diagnostic connector** (SAE J1962).

**Transport protocols supported:**
- **ISO 15765-4** (CAN) — most common in modern vehicles
- SAE J1850 PWM / VPW
- ISO 9141-2 / ISO 14230 (K-Line)

---

## 2. OBD-II Communication on CAN (ISO 15765-4)

| Parameter | Value |
|-----------|-------|
| Request CAN ID | **0x7DF** (functional/broadcast) or 0x7E0–0x7E7 (physical) |
| Response CAN ID | **0x7E8–0x7EF** (ECU response, +8 from request) |
| Baud rate | 500 kbit/s (modern) or 250 kbit/s |
| Frame format | ISO 15765-2 (CAN-TP) |

### OBD-II CAN Frame Structure
```
Byte 0:   Number of additional data bytes (length)
Byte 1:   Mode (Service ID)
Byte 2:   PID (Parameter ID)
Byte 3-7: Response data
```

---

## 3. OBD-II Modes (Services)

| Mode | Hex | Name | Description |
|------|-----|------|-------------|
| 01 | 0x01 | Show current data | Live sensor data (PIDs) |
| 02 | 0x02 | Freeze frame data | Data captured when DTC set |
| 03 | 0x03 | Stored DTCs | Emission-related fault codes |
| 04 | 0x04 | Clear DTCs | Erase DTCs and freeze frame |
| 05 | 0x05 | O2 sensor monitoring | Oxygen sensor test results |
| 06 | 0x06 | On-board monitoring | Test results for non-continuous monitors |
| 07 | 0x07 | Pending DTCs | DTCs not yet confirmed |
| 08 | 0x08 | Control operation | Request control of system |
| 09 | 0x09 | Vehicle information | VIN, calibration IDs |
| 0A | 0x0A | Permanent DTCs | Cannot be cleared until monitor runs |

---

## 4. Mode 01 PIDs (Live Data)

| PID | Hex | Name | Formula | Unit |
|-----|-----|------|---------|------|
| 00 | 0x00 | Supported PIDs 01-20 | Bit-encoded | — |
| 04 | 0x04 | Engine Load | A × 100 / 255 | % |
| 05 | 0x05 | Coolant Temperature | A − 40 | °C |
| 0A | 0x0A | Fuel Pressure | A × 3 | kPa |
| 0B | 0x0B | Intake MAP | A | kPa |
| 0C | 0x0C | Engine Speed | (A×256+B) / 4 | RPM |
| 0D | 0x0D | Vehicle Speed | A | km/h |
| 0E | 0x0E | Timing Advance | A/2 − 64 | ° |
| 0F | 0x0F | Intake Air Temp | A − 40 | °C |
| 10 | 0x10 | MAF Air Flow | (A×256+B) / 100 | g/s |
| 11 | 0x11 | Throttle Position | A × 100/255 | % |
| 1C | 0x1C | OBD Standard (ISO/SAE) | A | — |
| 2F | 0x2F | Fuel Tank Level | A × 100/255 | % |
| 33 | 0x33 | Barometric Pressure | A | kPa |
| 46 | 0x46 | Ambient Air Temp | A − 40 | °C |
| 5A | 0x5A | Accelerator Position | A × 100/255 | % |

---

## 5. DTC Format (Mode 03 / 07)

DTCs are 2 bytes each, encoded as:
```
Byte 1 bits 7-6: System
  00 = Powertrain (P)     (e.g., P0300)
  01 = Chassis    (C)
  10 = Body       (B)
  11 = Network    (U)

Byte 1 bits 5-4: OEM vs Standard
  0 = SAE/ISO defined
  1 = OEM manufacturer-specific

Remaining 12 bits: 3-digit fault code

Example: 0x01 0x00
  Bits 7-6 = 00 → P
  Bits 5-4 = 01 → OEM
  Bits 3-0 of byte1 + byte2 = 0x0100 → code 100
  → P0100 (Mass Air Flow sensor circuit)
```

---

## 6. Mode 09 – Vehicle Information

| IOCTLID | Name | Description |
|---------|------|-------------|
| 0x02 | VIN | 17-char Vehicle Identification Number |
| 0x04 | Calibration ID | Software calibration identifier |
| 0x06 | Calibration Verification Number (CVN) | CRC/hash of calibration |
| 0x0A | ECU Name | ASCII ECU identifier |

---

## 7. Python OBD-II Testing

```python
import can
import time

bus = can.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)

OBD_REQUEST_ID  = 0x7DF
OBD_RESPONSE_ID = 0x7E8

def send_obd_request(mode: int, pid: int):
    """Send OBD-II request using ISO 15765-4 single frame."""
    data = [0x02, mode, pid, 0x00, 0x00, 0x00, 0x00, 0x00]
    msg = can.Message(arbitration_id=OBD_REQUEST_ID, data=data, is_extended_id=False)
    bus.send(msg)

def read_obd_response(timeout=1.0):
    """Read first matching OBD-II response."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg and (0x7E8 <= msg.arbitration_id <= 0x7EF):
            return msg
    return None

def decode_engine_speed(resp_data):
    """Mode 01, PID 0x0C: RPM = (A*256 + B) / 4"""
    A = resp_data[3]
    B = resp_data[4]
    return (A * 256 + B) / 4.0

def decode_vehicle_speed(resp_data):
    """Mode 01, PID 0x0D: Speed = A km/h"""
    return resp_data[3]

def decode_coolant_temp(resp_data):
    """Mode 01, PID 0x05: Temp = A - 40 °C"""
    return resp_data[3] - 40

def read_dtcs():
    """Mode 03: Read stored DTCs."""
    send_obd_request(0x03, 0x00)
    resp = read_obd_response()
    if resp is None:
        print("No DTC response")
        return []
    # Response: [len, 0x43, num_dtcs, DTC1_high, DTC1_low, ...]
    num_dtcs = resp.data[2]
    dtcs = []
    for i in range(num_dtcs):
        high = resp.data[3 + i*2]
        low  = resp.data[4 + i*2]
        system = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}[(high >> 6) & 0x03]
        code   = ((high & 0x3F) << 8) | low
        dtcs.append(f"{system}{code:04d}")
    return dtcs

def clear_dtcs():
    """Mode 04: Clear DTCs."""
    data = [0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    msg = can.Message(arbitration_id=OBD_REQUEST_ID, data=data, is_extended_id=False)
    bus.send(msg)
    resp = read_obd_response()
    return resp is not None

# Example: read RPM
send_obd_request(0x01, 0x0C)
resp = read_obd_response()
if resp:
    rpm = decode_engine_speed(resp.data)
    print(f"Engine Speed: {rpm:.1f} RPM")

# Example: read DTCs
dtcs = read_dtcs()
print(f"Stored DTCs: {dtcs}")

bus.shutdown()
```

---

## 8. OBD-II Readiness Monitors

Before emission testing, all readiness monitors must show "Complete":

| Monitor | Abbreviation | Description |
|---------|-------------|-------------|
| Catalyst | CAT | Catalytic converter efficiency |
| Heated Catalyst | HCAT | Heated cat warm-up |
| Evap System | EVAP | Fuel vapor leak detection |
| Secondary Air | AIR | Secondary air injection |
| A/C Refrigerant | ACRF | A/C system leak |
| Oxygen Sensor | O2S | O2 sensor response |
| O2 Sensor Heater | O2SH | Heater circuit |
| EGR System | EGR | Exhaust Gas Recirculation |
| Misfire | MIS | Continuous — engine misfire |
| Fuel System | FUEL | Continuous — fuel trim |
| Components | CCM | Continuous — component monitoring |

PID 0x01 (Mode 01) bit-encodes readiness monitor status.

---

## 9. Interview Q&A

**Q: What is the difference between Mode 03 and Mode 07?**
> Mode 03 returns **confirmed/stored DTCs** — codes that have triggered the MIL (Check Engine Light). Mode 07 returns **pending DTCs** — faults detected in the current or last drive cycle but not yet confirmed (MIL not yet illuminated).

**Q: What is Mode 0A (Permanent DTCs)?**
> Permanent DTCs are DTCs that cannot be erased by Mode 04 or by disconnecting the battery. They remain until the ECU itself verifies, through on-board monitoring, that the fault is no longer present. Introduced in OBD-II to prevent emission test fraud.

**Q: How is Engine Speed (PID 0x0C) decoded?**
> Two response bytes A and B: `RPM = (A × 256 + B) / 4`. Maximum: (255×256+255)/4 = 16,383.75 RPM.

**Q: What CAN ID does an OBD-II functional request use?**
> 0x7DF — this is the functional broadcast address. A physical request to a specific ECU uses 0x7E0–0x7E7. Responses come from 0x7E8–0x7EF (ECU address + 0x08).
