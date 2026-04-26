# CAN vs CAN FD vs CAN TP — When to Use & Why
### Detailed Technical Guide with STAR Scenarios

---

## 1. Protocol Overview

| Feature | CAN (Classical) | CAN FD | CAN TP (ISO 15765-2) |
|---------|----------------|--------|----------------------|
| Standard | ISO 11898-1 (2003) | ISO 11898-1 (2015) | ISO 15765-2 |
| Max Data | 8 bytes/frame | 64 bytes/frame | Up to 4095 bytes (segmented) |
| Nominal Bit Rate | Up to 1 Mbit/s | Up to 1 Mbit/s | Same as underlying CAN/CAN FD |
| Data Phase Rate | N/A (single rate) | Up to 8 Mbit/s | N/A (transport layer) |
| Arbitration | CSMA/CA | CSMA/CA | Same as underlying bus |
| Real-Time | Yes | Yes (better) | Not real-time (connection overhead) |
| Layer | Data Link Layer (L2) | Data Link Layer (L2) | Transport Layer (L4) |
| Use Case | Periodic signals, control | High-bandwidth signals, calibration | Diagnostics, UDS, large data transfer |
| Error Detection | CRC-15 | CRC-17 or CRC-21 | Uses underlying CAN CRC |

---

## 2. Classical CAN — When to Use

### 2.1 Technical Characteristics
- **Frame formats:** Base Frame (11-bit ID) and Extended Frame (29-bit ID)
- **Max payload:** 8 bytes per frame
- **Bit rate:** Up to 1 Mbit/s (typical: 125 kbit/s, 250 kbit/s, 500 kbit/s)
- **Arbitration:** Non-destructive bitwise CSMA/CA (dominant bit wins)
- **Error detection:** Bit stuffing, CRC-15, Frame check, ACK check
- **Bus topology:** Multi-master, differential two-wire (CAN_H / CAN_L)

### 2.2 When to Use Classical CAN

**Use Classical CAN when:**

| Condition | Reason |
|-----------|--------|
| Data fits in ≤8 bytes | No segmentation needed, low overhead |
| Real-time, periodic signals (≤50ms cycle) | Deterministic latency |
| Safety-critical control signals | Well-proven, ISO 26262 certified implementations widespread |
| Low-cost ECU budget | CAN controllers are cheap, widely available |
| Network data rate ≤500 kbit/s | No bandwidth bottleneck |
| Legacy systems integration | Full backward compatibility |
| Body control, lighting, HVAC | Low data volume, simple I/O |

### 2.3 Typical Signals on Classical CAN

```
Engine RPM           → 2 bytes  (16-bit integer)
Vehicle Speed        → 2 bytes  (uint16 × 0.01 km/h)
Throttle Position    → 1 byte   (0–100%)
Door Status          → 1 byte   (bitmask)
Warning Lamps        → 1 byte   (bitmask)
Gear Position        → 1 byte   (enum)
Fuel Level           → 1 byte   (0–255 = 0–100%)
Coolant Temperature  → 1 byte   (offset +40°C)
```

All fit comfortably in 8-byte frames — no transport protocol required.

### 2.4 Frame Structure

```
┌──────────┬─────┬──────┬───────────────┬───────┬─────┬─────┐
│  SOF (1) │ ID  │ DLC  │  Data (0-8 B) │ CRC15 │ ACK │ EOF │
│          │11/29│ (4b) │               │       │(2b) │(7b) │
└──────────┴─────┴──────┴───────────────┴───────┴─────┴─────┘
```

---

## 3. CAN FD (Flexible Data-Rate) — When to Use

### 3.1 Technical Characteristics
- **Introduced:** Bosch, 2012; standardized ISO 11898-1:2015
- **Two bit-rate phases:**
  - **Nominal phase** (arbitration): Same as Classical CAN, up to 1 Mbit/s
  - **Data phase**: Up to 8 Mbit/s (typically 2–5 Mbit/s in production)
- **Max payload:** 64 bytes per frame (DLC 0–8 map same; DLC 9–15 map 12,16,20,24,32,48,64)
- **CRC:** CRC-17 for ≤16 bytes, CRC-21 for >16 bytes (stronger than CAN's CRC-15)
- **No remote frames:** CAN FD drops RTR (Remote Transmission Request)
- **Bit Rate Switch (BRS):** Control bit enables switching to faster data rate mid-frame
- **Error State Indicator (ESI):** Node indicates its error state in the frame

### 3.2 When to Use CAN FD

**Use CAN FD when:**

| Condition | Reason |
|-----------|--------|
| Data payload between 9–64 bytes per frame | Eliminates multi-frame workarounds |
| High sample rate sensor data (camera, radar, lidar) | More bytes per frame at higher speed |
| ADAS ECUs requiring <5ms cycle for large signals | Data phase up to 8 Mbit/s |
| OTA firmware download over CAN | 64-byte frames reduce frame count for large blocks |
| Calibration data (XCP over CAN FD) | Faster memory read/write |
| Modern powertrain (EV battery cell data, motor control) | BMS requires many cell voltages per cycle |
| Replacing CAN where bandwidth is a bottleneck | Same 2-wire physical layer, software upgrade |
| Reducing bus load on existing 500 kbit/s networks | Higher data rate = more data in same time window |

### 3.3 CAN FD vs Classical CAN — Bandwidth Comparison

Sending 64 bytes of sensor data every 10 ms:

**Classical CAN (500 kbit/s):**
- Need 8 frames (8 × 8 = 64 bytes)
- Each frame ~130 bits → 8 × 130 = 1040 bits
- At 500 kbit/s → 2.08 ms per batch
- Bus load contribution: ~20.8%

**CAN FD (500 kbit/s nominal / 2 Mbit/s data):**
- 1 frame (64 bytes)
- ~600 bits at mixed rate → ~0.4 ms per batch
- Bus load contribution: ~4%
- **Result: ~5× less bus load**

### 3.4 CAN FD Frame Structure

```
┌────┬────────┬─────┬─────┬─────┬──────────────────┬────────┬─────┬─────┐
│SOF │ ID     │ FDF │ BRS │ ESI │ Data (up to 64 B)│CRC17/21│ ACK │ EOF │
│    │ 11/29b │ =1  │     │     │                  │        │     │     │
└────┴────────┴─────┴─────┴─────┴──────────────────┴────────┴─────┴─────┘
     ←— Nominal bit rate ——→←————— Data bit rate (if BRS=1) ————→
```

- **FDF (FD Frame):** = 1 identifies CAN FD frame
- **BRS (Bit Rate Switch):** = 1 switches to higher data rate for payload
- **ESI (Error State Indicator):** = 0 Error Active, = 1 Error Passive

### 3.5 DLC to Byte Count Mapping (CAN FD)

| DLC | Bytes |
|-----|-------|
| 0–8 | 0–8 (same as CAN) |
| 9 | 12 |
| 10 | 16 |
| 11 | 20 |
| 12 | 24 |
| 13 | 32 |
| 14 | 48 |
| 15 | 64 |

---

## 4. CAN TP (ISO 15765-2) — When to Use

### 4.1 What is CAN TP?
CAN TP (Transport Protocol) is **not a physical protocol** — it is a **transport layer** built on top of Classical CAN or CAN FD. Defined in ISO 15765-2, it enables transmission of payloads **larger than 8 bytes** (CAN) or **64 bytes** (CAN FD) by segmenting data into multiple frames with flow control.

### 4.2 Why CAN TP is Needed
UDS (ISO 14229) diagnostic messages often carry:
- VIN numbers (17 bytes)
- ECU software versions (variable length)
- DTC records (multiple DTCs × multiple bytes each)
- Flash programming data blocks (kilobytes to megabytes)

None of these fit in a single classical CAN frame. CAN TP provides the segmentation, reassembly, and flow control to make this work reliably.

### 4.3 CAN TP Frame Types

| Frame Type | PCI Byte | Description |
|-----------|---------|-------------|
| **SF (Single Frame)** | byte0[7:4] = 0x0 | Entire PDU in one frame (≤7 bytes on CAN, ≤62 on CAN FD) |
| **FF (First Frame)** | byte0[7:4] = 0x1 | First segment of multi-frame message; includes total length |
| **CF (Consecutive Frame)** | byte0[7:4] = 0x2 | Subsequent segments; sequence number byte0[3:0] = 1–15 |
| **FC (Flow Control)** | byte0[7:4] = 0x3 | Receiver controls sender: ContinueToSend / Wait / Overflow |

### 4.4 Flow Control Parameters

```
FC Frame:
  byte0 = 0x30 (FS=0: ContinueToSend) / 0x31 (FS=1: Wait) / 0x32 (FS=2: Overflow)
  byte1 = BlockSize (BS): Number of CF frames before next FC (0 = send all)
  byte2 = STmin: Minimum separation time between CF frames
          0x00–0x7F = 0–127 ms
          0xF1–0xF9 = 100–900 µs
```

### 4.5 CAN TP Message Flow Example (UDS ReadDTCInfo)

```
Tester (0x744) → ECU (0x7E0)          ECU (0x7EC) → Tester (0x74C)

FF: [10 1A 19 02 09]  ← Send 26 bytes  FF: [10 2E 59 02 09 ...]  ← ECU responds with 46 bytes
                                         SF(sent by tester):
FC: [30 00 00]        ← ContinueToSend  CF: [21 xx xx xx xx xx xx]
                                         CF: [22 xx xx xx xx xx xx]
                                         CF: [23 xx xx xx xx xx xx]
                                         CF: [24 xx xx xx xx xx xx]
                                         CF: [25 xx xx xx xx xx xx]
                                         CF: [26 xx xx xx xx xx xx]
```

### 4.6 When to Use CAN TP

**Use CAN TP when:**

| Condition | Reason |
|-----------|--------|
| Single UDS service (0x22, 0x27, 0x2E, 0x31, 0x34, 0x36) | All UDS is mandatory over ISO 15765-2 |
| Reading DTC records (0x19) | Multiple DTCs → response > 8 bytes |
| ECU flash programming (0x34/0x36/0x37) | Block sizes from 256 bytes to multiple MB |
| Reading ECU VIN, software version (0x22 F190, F189) | Multiple bytes of ASCII data |
| OBD-II communication (SAE J1979 / ISO 15031) | Mandated by regulation |
| Key programming, coding, adaptation | Dealer tool sessions use UDS over CAN TP |
| End-of-line (EOL) flashing at factory | All ECU programming uses CAN TP |
| Telematics remote diagnostics | Off-board server uses UDS over CAN TP tunneled via IP |

**Do NOT use CAN TP for:**
- Real-time periodic signals (use raw CAN or CAN FD instead)
- Safety-critical control loops (CAN TP has variable latency)
- Signals that change faster than 20 ms (CAN TP overhead is too high)

---

## 5. Decision Framework — Which Protocol to Choose?

```
                    ┌─────────────────────────────────┐
                    │ What is the data size?           │
                    └────────────┬────────────────────┘
                                 │
               ┌─────────────────┼──────────────────┐
               ▼                 ▼                   ▼
          ≤ 8 bytes          9–64 bytes         > 64 bytes
               │                 │                   │
               ▼                 ▼                   ▼
    ┌──────────────────┐ ┌───────────────┐ ┌─────────────────────┐
    │ Is it real-time? │ │ Is bandwidth  │ │ Is it diagnostic?   │
    └────────┬─────────┘ │ critical?     │ └──────────┬──────────┘
             │           └───────┬───────┘            │
      Yes    │ No        Yes     │ No            Yes  │ No
      │      │           │       │               │    │
      ▼      ▼           ▼       ▼               ▼    ▼
  Classic  Classic    CAN FD  CAN FD +      CAN TP   Not a good
  CAN      CAN        Native  CAN TP        over CAN   fit for
  (raw     + CAN TP            (transport)  or CAN FD  CAN bus
  frame)   if needed                                  (use ETH)
```

---

## 6. STAR Scenarios

---

### STAR Scenario 1 — Using Classical CAN for Real-Time Powertrain Control

**Situation:**
You are an automotive test engineer at a Tier 1 supplier working on a 6-speed automatic transmission ECU (TCU) integration. The TCU must exchange gear position, engine torque request, and turbine speed data with the Engine Control Module (ECM) every 10ms. The vehicle network is a legacy 500 kbit/s CAN network used in a mid-range sedan project (2024 model year, no CAN FD requirement in the spec).

**Task:**
Select the correct CAN variant and frame strategy for TCU–ECM real-time communication. Justify the choice and design the message layout within the constraints of the existing network.

**Action:**
1. Reviewed the signal list:
   - `TCU_GearPosition` → 1 byte (enum: P/R/N/1–6)
   - `TCU_TorqueRequest` → 2 bytes (uint16, Nm × 4)
   - `TCU_TurbineSpeed` → 2 bytes (uint16, RPM × 1)
   - `ECM_EngineSpeed` → 2 bytes (already broadcast by ECM)
   - `ECM_AcceleratorPedal` → 1 byte (0–100%)
   - Total: 6 bytes of TCU data, fits in a single 8-byte CAN frame with 2 bytes spare

2. Chose **Classical CAN** at 500 kbit/s because:
   - All signals fit in 8 bytes (no segmentation needed)
   - 10ms cycle time is feasible — a single frame at 500 kbit/s takes ~0.22ms
   - Legacy network with classical CAN controllers in all ECUs
   - AUTOSAR COM layer configured for PDU with 10ms cyclic trigger

3. Designed CAN frame 0x320 (`TCU_PowertrainData`):
   ```
   Byte 0: GearPosition (enum 0=P,1=R,2=N,3=1,4=2,5=3,6=4,7=5,8=6)
   Byte 1-2: TorqueRequest (uint16 BE, Nm×4)
   Byte 3-4: TurbineSpeed (uint16 BE, RPM)
   Byte 5: ShiftStatus (0=idle,1=shifting,2=complete)
   Byte 6: TCC_Status (Torque Converter Clutch: 0=open,1=slip,2=locked)
   Byte 7: Checksum (XOR bytes 0-6)
   ```

4. Validated cycle timing with CANalyzer: confirmed 10ms ±2ms jitter within spec.

**Result:**
The TCU–ECM interface passed all HIL timing tests. Bus load contribution was 2.3% (well within the 30% target). No retransmissions were observed. Classical CAN proved entirely adequate — using CAN FD would have added unnecessary cost and complexity to a legacy system without measurable benefit.

**Key Lesson:** *Classical CAN is the right choice when data is ≤8 bytes, timing requirements are ≥5ms, and the network is within bandwidth limits. Avoid over-engineering with CAN FD purely because it exists.*

---

### STAR Scenario 2 — Using CAN FD for ADAS Radar Object List

**Situation:**
You are a validation engineer on an ADAS project for a front radar sensor (77 GHz, ISO 26262 ASIL-B). The radar ECU must transmit an object list containing up to 8 tracked objects every 50ms. Each object carries: object ID (1B), distance X/Y (2+2B), velocity X/Y (2+2B), RCS value (1B), confidence level (1B) — totalling 11 bytes per object. With 8 objects: 88 bytes per cycle. The existing powertrain CAN runs at 500 kbit/s classical CAN. The ADAS gateway connects to a dedicated ADAS CAN network.

**Task:**
Determine whether Classical CAN, CAN FD, or Automotive Ethernet is appropriate for the radar object list transmission, and define a protocol strategy that achieves the 50ms cycle constraint with acceptable bus load.

**Action:**
1. Calculated bandwidth requirements:
   - Classical CAN: 88 bytes = 11 frames × ~130 bits = 1430 bits every 50ms at 500 kbit/s → 1430/25000 = **5.72% bus load** (feasible but uses 11 CAN IDs)
   - CAN FD: 88 bytes fits in **2 CAN FD frames** (64+24 bytes) at 2 Mbit/s data phase → 2 × ~500 bits at mixed rate ≈ 0.1ms → **~0.2% bus load**

2. Chose **CAN FD** at 1 Mbit/s nominal / 2 Mbit/s data because:
   - 88 bytes in 2 frames vs 11 frames on classical CAN
   - Reduces message IDs — simpler DBC/ARXML management
   - ADAS gateway ECU (NXP S32G) supports CAN FD natively
   - ISO 26262 ASIL-B: CAN FD CRC-17/21 provides stronger error detection than CRC-15
   - Future-proof: lidar point-cloud data (next year's program) won't fit on classical CAN

3. Designed two CAN FD frames:
   - `0x300` (64 bytes): Objects 1–5 packed (11B each + 9B header with timestamp, object count)
   - `0x301` (36 bytes, DLC=32): Objects 6–8 packed + 8B CRC safety wrapper (AUTOSAR E2E Profile 4)

4. Added E2E protection (AUTOSAR E2E Profile 4) because the sensor data is ASIL-B — CRC32 + counter in header bytes.

5. Validated with CAPL test script: measured actual bus latency from radar sensor trigger to gateway reception = 1.2ms (well within 50ms requirement).

**Result:**
The CAN FD solution reduced the ADAS CAN bus load from a projected 34% (11 classical CAN frames × 3 sensors) to under 6% (2 CAN FD frames × 3 sensors). ASIL-B E2E protection requirements were met. The gateway routing latency of 1.2ms met the ADAS system requirement of ≤5ms. Architecture was approved and entered series production.

**Key Lesson:** *Use CAN FD when large payloads (>8 bytes) are sent at high frequency, especially in ADAS where multiple sensors broadcast object lists simultaneously. CAN FD is also mandatory when E2E Profile 4 (CRC-32 in header) is required for ASIL-B/C signals, as it needs more header space than 8 bytes allows.*

---

### STAR Scenario 3 — Using CAN TP for UDS ECU Diagnostics

**Situation:**
You are a diagnostic test engineer performing end-of-line (EOL) validation at a manufacturing plant for a new Body Control Module (BCM). The EOL tester must: (1) read the ECU VIN (17 bytes), (2) read the ECU software fingerprint (40 bytes), (3) run a self-test routine that returns a 120-byte result, and (4) clear all DTCs. All communication is over the vehicle's 500 kbit/s CAN network using UDS (ISO 14229). The BCM responds on CAN ID 0x7CC (physical), functional address 0x7DF.

**Task:**
Design the complete diagnostic communication strategy using the correct protocol layers. Explain why raw CAN or CAN FD alone cannot fulfil these requirements, and implement a working tester flow using CAN TP (ISO 15765-2).

**Action:**
1. Identified why raw CAN alone fails:
   - VIN = 17 bytes → exceeds 8-byte classical CAN limit. Cannot fit in single frame.
   - Software fingerprint = 40 bytes → requires 5+ classical CAN frames with no protocol to sequence them.
   - Self-test result = 120 bytes → 15 classical CAN frames with no flow control = data loss risk.
   - Without transport protocol: no acknowledgement, no segmentation, no receiver buffer management.

2. Confirmed CAN TP (ISO 15765-2) is mandatory:
   - UDS (ISO 14229) **requires** ISO 15765-2 as the transport layer on CAN
   - CAN TP provides: SF/FF/CF/FC frame types, flow control, sequence numbers, timeout handling (N_As, N_Bs, N_Cs, N_Ar, N_Br, N_Cr timers)

3. Designed the EOL tester flow:

   **Step 1 — Enter Extended Diagnostic Session:**
   ```
   TX (0x744 → 0x7CC): SF [02 10 03] (UDS 0x10, subfunction 0x03 = extendedDiagnosticSession)
   RX (0x7CC → 0x74C): SF [02 50 03] (positive response)
   ```

   **Step 2 — Read VIN (0x22 F190):**
   ```
   TX: SF [03 22 F1 90]
   RX: FF [00 14 62 F1 90 56 49 4E]  ← len=20, response SID=0x62, DID=F190, first 5 VIN bytes
       TX: FC [30 00 00]              ← ContinueToSend, BlockSize=0, STmin=0
       CF [21 xx xx xx xx xx xx xx]  ← VIN bytes 6–12
       CF [22 xx xx xx xx xx]        ← VIN bytes 13–17 + padding
   ```

   **Step 3 — Read Software Fingerprint (0x22 F18B):**
   ```
   TX: SF [03 22 F1 8B]
   RX: FF [00 2B 62 F1 8B xx xx xx]  ← len=43 (3 header + 40 data)
       TX: FC [30 00 00]
       CF [21..] CF [22..] CF [23..] CF [24..] CF [25..]  ← 5 consecutive frames
   ```

   **Step 4 — Execute Self-Test Routine (0x31 0101 + read result 0x31 0301):**
   ```
   TX: SF [04 31 01 01 01]           ← Start Routine 0x0101
   RX: SF [04 71 01 01 01]           ← Positive response
   (wait 500ms)
   TX: SF [04 31 03 01 01]           ← Request routine results
   RX: FF [00 7B 71 03 01 01 xx xx]  ← len=123, multi-frame response
       TX: FC [30 00 00]
       CF [21..] through CF [2F..]   ← 15 consecutive frames for 120-byte result
   ```

   **Step 5 — Clear DTCs (0x14 FF FF FF):**
   ```
   TX: SF [04 14 FF FF FF]           ← ClearDiagnosticInformation, all DTCs
   RX: SF [01 54]                    ← Positive response
   ```

4. Implemented in Python using `python-can` with manual ISO-TP:
   ```python
   def send_isotp_sf(bus, tx_id, data):
       """Send Single Frame UDS message via CAN TP"""
       pci = [len(data)]  # SF: N_PCI byte = length (0-7)
       frame = pci + list(data) + [0xCC] * (7 - len(data))  # pad to 8
       msg = can.Message(arbitration_id=tx_id, data=frame, is_extended_id=False)
       bus.send(msg)
   ```

5. Added N_Cr timeout (150ms) handling to abort and retry if consecutive frame is delayed.

**Result:**
All five EOL diagnostic steps completed reliably in under 3 seconds total. VIN readback matched the programmed value. Self-test result (120 bytes) was received correctly with zero frame drops across 500 test cycles. DTC clear confirmed at end of run. The CAN TP protocol provided the necessary segmentation and flow control that raw CAN could never provide, with zero modifications needed to the ECU — it already implemented ISO 15765-2 as part of its UDS stack.

**Key Lesson:** *CAN TP (ISO 15765-2) is not optional for UDS communication — it is the transport layer mandated by ISO 14229. Any diagnostic data larger than 7 bytes (classical CAN) or 62 bytes (CAN FD SF) automatically requires multi-frame CAN TP. Never attempt to bypass CAN TP for diagnostics — sequence numbers, flow control, and timeout handling are essential to reliable large-payload transfer.*

---

### STAR Scenario 4 — Choosing Between CAN FD and Classical CAN + CAN TP for OTA Flash

**Situation:**
You are a systems architect on a next-generation EV platform. The software team estimates the BMS ECU firmware is 512 KB and must be updatable Over-The-Air (OTA) without taking the vehicle to a dealer. The OTA manager ECU receives the firmware block from the telematics unit via internal Ethernet and must re-flash the BMS over CAN. The BMS ECU is connected on a dedicated battery CAN network. You must compare: (A) Classical CAN 500 kbit/s + CAN TP, vs (B) CAN FD 2 Mbit/s + CAN TP. Both use UDS flashing (0x34 RequestDownload, 0x36 TransferData, 0x37 RequestTransferExit).

**Task:**
Calculate the theoretical flash time for both options, identify the performance-limiting factors, and recommend the correct architecture with justification.

**Action:**
1. Calculated net data throughput for each option:

   **Option A — Classical CAN 500 kbit/s + CAN TP:**
   - TransferData (0x36) block: CAN TP max usable payload = 4095 bytes per ISO-TP PDU
   - Each classical CAN frame carries 7 bytes (1 byte PCI overhead): net 7 B/frame
   - Frame duration at 500 kbit/s: ~130 bits ≈ 0.26ms → 3846 frames/second
   - Net throughput: 7 × 3846 = **26.9 KB/s**
   - 512 KB ÷ 26.9 KB/s = **~19 seconds** (ideal, no STmin, BS=0)
   - With STmin=1ms (typical ECU requirement): 3846 → 1000 frames/s → 7 KB/s → **73 seconds**

   **Option B — CAN FD 2 Mbit/s data phase + CAN TP:**
   - TransferData: CAN FD TP (ISO 15765-2, extended addressing) max SF = 62 bytes
   - Each CAN FD CF carries 63 bytes (1 byte PCI): net 63 B/frame
   - Frame duration (64-byte CAN FD at 2 Mbit/s data, 500 kbit nominal): ~380 bits total ≈ **0.52ms** at nominal + ~0.25ms data phase → ~0.35ms per frame
   - At STmin=1ms: 1000 frames/s × 63 bytes = **63 KB/s**
   - 512 KB ÷ 63 KB/s = **~8.1 seconds**
   - 9× faster than classical CAN with same STmin

2. Identified limiting factors:
   - **ECU flash write speed**: BMS internal NVM typically 50–100 KB/s → real bottleneck
   - **STmin**: Set by BMS ECU to give time for flash write per block. CAN FD helps here because more bytes arrive per frame.
   - **P2 server timeout (UDS)**: Max response time for 0x36. Longer if ECU is erasing/writing.

3. Recommended **Option B (CAN FD + CAN TP)**:
   - Even if ECU NVM limits to 50 KB/s, CAN FD removes the *network* as the bottleneck
   - Fewer frames → less interrupt overhead on BMS microcontroller → faster write
   - Larger blocks (up to 4095 bytes per ISO-TP PDU, fitting in ~65 CAN FD frames) reduce protocol overhead
   - Future sensor data requirements (cell voltage every 10ms × 96 cells = 192 bytes) will need CAN FD anyway

4. Validated architecture in CAPL HIL simulation: CAN FD OTA flashed a 512 KB binary in **11.3 seconds** actual (vs 68 seconds on classical CAN in the same simulation), with flash NVM being the real bottleneck at ~45 KB/s.

**Result:**
The CAN FD OTA architecture was selected for the BMS network. Production flash time of 11–15 seconds enabled OTA to complete within the 30-second regulatory window for safety firmware updates (UNECE WP.29 regulation). The classical CAN option was rejected as it could not guarantee completion within the window under worst-case STmin and NVM conditions.

**Key Lesson:** *CAN TP is required for any firmware flash operation — no alternative. The choice between Classical CAN and CAN FD affects the speed and reliability of that flashing. For large payloads (>10 KB) or time-constrained OTA scenarios, CAN FD + CAN TP is architecturally superior. Classical CAN + CAN TP is sufficient for small ECUs with infrequent updates.*

---

### STAR Scenario 5 — Wrong Protocol Choice and Root Cause Analysis

**Situation:**
During system integration testing for a cluster ECU project, the test team reports that the instrument cluster intermittently misses speed updates, causing the speedometer to freeze for 200–500ms. The CAN network is 500 kbit/s Classical CAN. A previous engineer had implemented vehicle speed as part of a UDS-style multi-frame message (CAN TP) to bundle speed, RPM, fuel, and temperature together (total 32 bytes). The logic was "32 bytes doesn't fit in one frame, so let's use CAN TP."

**Task:**
Diagnose why this approach is technically incorrect, explain the root cause of the freezing, and redesign the interface using the appropriate protocol strategy.

**Action:**
1. Retrieved the CANalyzer trace and found:
   - Speed data was sent as CAN TP FF → CF sequence with STmin=5ms
   - Under normal conditions: FF + 4 CFs arrived fine → cluster updates
   - Under high bus load: FC (Flow Control) frame from cluster was delayed → sender waited up to N_Bs timeout (1000ms) before aborting → cluster received nothing for up to 1 second

2. Identified root cause: **CAN TP was used for real-time periodic data — a fundamental protocol misuse:**
   - CAN TP introduces flow control dependency (sender must wait for FC frame)
   - FC delays under bus load cause multi-second data gaps
   - Periodic real-time signals must never depend on request-response handshaking
   - FC timeout (N_Bs = 1000ms by default) caused 1-second blackouts of speed data

3. Redesigned the interface:
   - Split 32 bytes across **4 standard CAN frames** (8 bytes each), each broadcast independently:
     ```
     0x100: VehicleSpeed + EngineRPM (4 bytes)
     0x500: FuelLevel + CoolantTemp + GearPosition + OilPressure (5 bytes)
     0x505: WarningLamps + TPMS (2 bytes)
     0x507: EV_SOC + Brightness (2 bytes)
     ```
   - All frames broadcast at 10ms cycle, no flow control, no sequencing
   - Cluster receives each independently — partial loss of one frame doesn't block others

4. Retained CAN TP **only for UDS diagnostic communication** over separate IDs (0x744 / 0x74C).

**Result:**
The speedometer freeze was eliminated completely. Post-fix testing over 72 hours of continuous HIL simulation recorded zero occurrences of speed freeze events (vs 847 events in 72 hours pre-fix). Bus load actually decreased from 8.4% (CAN TP overhead) to 4.1% (4 direct frames) because CAN TP header bytes and FC frames were eliminated.

**Key Lesson:** *CAN TP is for diagnostic, configuration, and large one-shot transfers — NEVER for periodic real-time signals. If a real-time signal exceeds 8 bytes, the correct solution is to split it across multiple CAN frames (or upgrade to CAN FD), not to wrap it in CAN TP. Using CAN TP for real-time data creates latency, flow-control dependency, and system reliability risks.*

---

## 7. Quick Reference Summary

| Decision | Classical CAN | CAN FD | CAN TP |
|----------|--------------|--------|--------|
| Data size per message | ≤8 bytes | 9–64 bytes native | Any size (segmented) |
| Real-time periodic? | Yes | Yes | No — adds latency |
| Diagnostics (UDS)? | Only if payload ≤7 bytes | Only if payload ≤62 bytes | Yes — mandatory |
| ECU flashing (OTA)? | Only with CAN TP | Only with CAN TP | Required layer |
| Calibration (XCP)? | XCP over CAN (≤8B) | XCP over CAN FD (≤64B) | Not needed |
| Safety (E2E protection)? | Yes (E2E Profile 2) | Yes (E2E Profile 4) | Not applicable |
| Bit rate | Up to 1 Mbit/s | Up to 8 Mbit/s | Protocol layer |
| Legacy ECU compatibility | Universal | Requires FD-capable controller | Requires ISO-TP stack |
| Cost | Low | Medium (newer silicon) | Software only |

---

## 8. Common Mistakes to Avoid

| Mistake | Consequence | Correct Approach |
|---------|-------------|------------------|
| Using CAN TP for periodic speed/RPM signals | Flow control delays → data freeze | Use raw CAN frames at fixed cycle |
| Using Classical CAN for 50-byte ADAS object list | 6+ frame IDs, complex DBC, high bus load | Upgrade to CAN FD |
| Not implementing STmin correctly in CAN TP | ECU buffer overflow → data loss, frame drops | Always honour STmin from FC frame |
| Using CAN FD without E2E on ASIL-B signals | Safety violation — weaker protection than required | Add AUTOSAR E2E Profile 4 |
| Mixing CAN and CAN FD nodes without FD-tolerant transceivers | Bus errors — CAN FD frames corrupt classical CAN nodes | Use FD-passive transceivers or separate networks |
| Ignoring N_Cr timeout in CAN TP receiver | Silent failure if CF is lost mid-transmission | Implement N_Cr timer and abort/retry logic |

---

*Document: CAN_CANFD_CANTP_When_To_Use_STAR.md*
*Location: protocol_study_material/*
*Standards: ISO 11898-1, ISO 15765-2, ISO 14229, AUTOSAR E2E Library*
